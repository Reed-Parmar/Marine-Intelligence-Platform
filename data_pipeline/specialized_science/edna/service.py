"""
Phase 7 — eDNA Analysis Service.
Main orchestrator for environmental DNA pipelines: validation, preprocessing,
reference matching, species detection, and storage persistence.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from data_pipeline.specialized_science.common.models import (
    InMemoryStorageRepository,
    SpecializedResult,
    StorageRepository,
)
from data_pipeline.specialized_science.edna.detection import (
    SpeciesDetection,
    detect_species_from_matches,
)
from data_pipeline.specialized_science.edna.matching import (
    KmerSimilarityMatcher,
    ReferenceMatcher,
)
from data_pipeline.specialized_science.edna.preprocessing import (
    PreprocessedSequence,
    preprocess_fastq_records,
    preprocess_sequence,
)
from data_pipeline.specialized_science.edna.validation import (
    EDNAValidationResult,
    validate_fasta,
    validate_fastq,
)
from data_pipeline.specialized_science.taxonomy.service import TaxonomyService


class EDNAService:
    """
    Unified eDNA Analysis Orchestration Service.

    Connects validation, preprocessing, reference matching, and taxonomy resolution.
    Storage and Matcher components are pluggable via Protocols for seamless Phase 8 ML integration.
    """

    def __init__(
        self,
        matcher: Optional[ReferenceMatcher] = None,
        taxonomy_service: Optional[TaxonomyService] = None,
        storage_repo: Optional[StorageRepository] = None,
    ) -> None:
        self.matcher = matcher or KmerSimilarityMatcher()
        self.taxonomy_service = taxonomy_service or TaxonomyService()
        self.storage_repo = storage_repo or InMemoryStorageRepository()

    def validate_fasta(self, content_or_path: Union[str, Path]) -> EDNAValidationResult:
        """Validates FASTA format data."""
        return validate_fasta(content_or_path)

    def validate_fastq(self, content_or_path: Union[str, Path]) -> EDNAValidationResult:
        """Validates FASTQ format data."""
        return validate_fastq(content_or_path)

    def preprocess(
        self,
        raw_sequence: str,
        seq_id: str = "seq_01",
        min_length: int = 20,
    ) -> PreprocessedSequence:
        """Preprocesses a raw DNA sequence string."""
        return preprocess_sequence(raw_sequence, seq_id=seq_id, min_length=min_length)

    def analyze_sequence(
        self,
        raw_sequence: str,
        seq_id: str = "seq_01",
        target_gene: Optional[str] = "Cytochrome oxidase",
        confidence_threshold: float = 0.70,
        persist: bool = True,
    ) -> SpecializedResult:
        """
        Executes end-to-end eDNA sequence analysis pipeline for a single sequence:
        1. Preprocessing and quality filtering
        2. Reference library matching
        3. Species detection and baseline confidence derivation
        4. Taxonomy resolution
        5. Storage persistence (if enabled)
        """
        prep = self.preprocess(raw_sequence, seq_id=seq_id)
        if not prep.passed_filter:
            detection = SpeciesDetection(
                query_id=seq_id,
                is_detected=False,
                warnings=prep.filter_notes,
                provenance={"status": "failed_preprocessing_filter"},
            )
            result = detection.to_specialized_result()
            if persist and self.storage_repo:
                self.storage_repo.save_result(result)
            return result

        # Reference matching
        matches = self.matcher.match(prep.cleaned_sequence)

        # Species detection & taxonomy resolution
        detection = detect_species_from_matches(
            query_id=seq_id,
            sequence=prep.cleaned_sequence,
            matches=matches,
            confidence_threshold=confidence_threshold,
            taxonomy_service=self.taxonomy_service,
        )

        result = detection.to_specialized_result()
        result.metadata["gc_content"] = prep.gc_content
        result.metadata["sequence_length"] = prep.length

        if persist and self.storage_repo:
            if result.evidence:
                self.storage_repo.save_evidence(result.evidence)
            self.storage_repo.save_result(result)

        return result

    def analyze_fasta_file(
        self,
        file_path: Union[str, Path],
        confidence_threshold: float = 0.70,
        persist: bool = True,
    ) -> List[SpecializedResult]:
        """Validates and processes all sequence records within a FASTA file."""
        val = self.validate_fasta(file_path)
        if not val.is_valid:
            return []

        results: List[SpecializedResult] = []
        for rec in val.fasta_records:
            res = self.analyze_sequence(
                raw_sequence=rec.sequence,
                seq_id=rec.id or f"fasta_line_{rec.line_number}",
                confidence_threshold=confidence_threshold,
                persist=persist,
            )
            results.append(res)

        return results

    def analyze_cmlre_edna_record(
        self,
        record: Dict[str, Any],
        confidence_threshold: float = 0.70,
        persist: bool = True,
    ) -> SpecializedResult:
        """
        Processes a real CMLRE eDNA row (from dnaderiveddata1.txt or DB).
        Extracts DNA_sequence, target_gene, sample_id, PCR conditions.
        """
        seq = record.get("DNA_sequence") or record.get("sequence") or ""
        seq_id = str(record.get("id") or record.get("samp_name") or record.get("sample_id") or "cmlre_edna_sample")
        target_gene = record.get("target_gene") or "Cytochrome oxidase"

        result = self.analyze_sequence(
            raw_sequence=seq,
            seq_id=seq_id,
            target_gene=target_gene,
            confidence_threshold=confidence_threshold,
            persist=persist,
        )

        # Attach CMLRE domain-specific metadata
        result.provenance["cmlre_sample_id"] = record.get("samp_name")
        result.provenance["pcr_primer_forward"] = record.get("pcr_primer_forward")
        result.provenance["pcr_primer_reverse"] = record.get("pcr_primer_reverse")
        result.provenance["seq_meth"] = record.get("seq_meth")

        return result
