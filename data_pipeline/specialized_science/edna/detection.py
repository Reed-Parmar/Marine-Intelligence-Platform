"""
Phase 7 — eDNA Species Detection & Baseline Confidence Scoring.
Transforms sequence matches into structured species detections with transparent confidence derivations.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from data_pipeline.specialized_science.common.models import (
    ConfidenceLevel,
    EvidenceType,
    IdentificationStatus,
    ScientificEvidence,
    SpecializedResult,
    TaxonResolverProtocol,
)
from data_pipeline.specialized_science.common.result import (
    build_specialized_result,
    compute_confidence_level,
)
from data_pipeline.specialized_science.edna.matching import SequenceMatch


@dataclass
class SpeciesDetection:
    """Detection result for a single processed eDNA sequence."""
    query_id: str
    is_detected: bool
    species_name: Optional[str] = None
    common_name: Optional[str] = None
    status: IdentificationStatus = IdentificationStatus.UNRESOLVED
    confidence_score: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    match_score: float = 0.0
    target_gene: Optional[str] = None
    reference_id: Optional[str] = None
    reference_source: Optional[str] = None
    evidence: Optional[ScientificEvidence] = None
    alternative_candidates: List[Dict[str, Any]] = field(default_factory=list)
    taxonomic_hierarchy: Optional[Dict[str, Optional[str]]] = None
    warnings: List[str] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_specialized_result(self) -> SpecializedResult:
        """Converts detection into the platform's standardized SpecializedResult."""
        return build_specialized_result(
            result_id=f"edna-{self.query_id}",
            domain="edna",
            target_entity=self.species_name,
            common_name=self.common_name,
            status=self.status,
            confidence_score=self.confidence_score,
            confidence_method="deterministic_kmer_similarity",
            is_ml_prediction=False,
            evidence=self.evidence,
            alternative_candidates=self.alternative_candidates,
            taxonomic_hierarchy=self.taxonomic_hierarchy,
            provenance=self.provenance,
            warnings=self.warnings,
            metadata={"match_score": self.match_score, "target_gene": self.target_gene},
        )


def calculate_baseline_edna_confidence(
    top_match_score: float,
    query_length: int,
    second_match_score: Optional[float] = None,
    min_length_for_full_confidence: int = 120,
) -> float:
    """
    Computes transparent baseline confidence score [0.0, 1.0].
    
    Formula components:
    1. Base similarity score from sequence alignment / k-mer containment
    2. Sequence length penalty if query is shorter than standard barcode threshold
    3. Separation margin bonus/penalty relative to second closest candidate
    """
    if top_match_score is None or top_match_score <= 0 or not math.isfinite(top_match_score):
        return 0.0

    # Length scaling factor: short reads below barcode threshold receive proportionally reduced confidence
    length_factor = min(1.0, max(0.0, query_length / float(min_length_for_full_confidence)))

    # Base score
    base_conf = top_match_score * length_factor

    # Separation margin penalty if second candidate is nearly identical
    if second_match_score is not None and second_match_score > 0 and math.isfinite(second_match_score):
        margin = top_match_score - second_match_score
        if margin < 0.05:
            base_conf *= 0.90 # Slight ambiguity dampening

    return round(min(1.0, max(0.0, base_conf)), 4)


def detect_species_from_matches(
    query_id: str,
    sequence: str,
    matches: List[SequenceMatch],
    confidence_threshold: float = 0.70,
    taxonomy_service: Optional[TaxonResolverProtocol] = None,
) -> SpeciesDetection:
    """
    Evaluates sequence matches to generate a structured SpeciesDetection.
    Integrates with TaxonomyService to resolve canonical names and hierarchies.
    """
    warnings: List[str] = []
    q_len = len(sequence)

    if not matches:
        evidence = ScientificEvidence(
            evidence_id=f"ev-edna-{query_id}",
            evidence_type=EvidenceType.EDNA_SEQUENCE,
            source_identifier=query_id,
            features={"sequence_length_bp": q_len},
            metrics={"top_match_similarity": 0.0},
            provenance={"matcher": "deterministic_baseline", "status": "no_match"},
        )
        return SpeciesDetection(
            query_id=query_id,
            is_detected=False,
            status=IdentificationStatus.UNRESOLVED,
            confidence_score=0.0,
            confidence_level=ConfidenceLevel.UNKNOWN,
            evidence=evidence,
            warnings=["No reference sequence matches found above minimum alignment threshold."],
            provenance={"query_id": query_id, "evidence_type": EvidenceType.EDNA_SEQUENCE.value},
        )

    top_match = matches[0]
    second_match = matches[1] if len(matches) > 1 else None
    second_score = second_match.similarity_score if second_match else None

    # Calculate baseline confidence
    conf = calculate_baseline_edna_confidence(
        top_match_score=top_match.similarity_score,
        query_length=q_len,
        second_match_score=second_score,
    )

    # Format alternative candidates
    alt_candidates = [
        {
            "scientific_name": m.scientific_name,
            "similarity_score": m.similarity_score,
            "reference_id": m.reference_id,
            "match_type": m.match_type,
        }
        for m in matches[1:5]
    ]

    # Taxonomy integration
    resolved_sci_name = top_match.scientific_name
    common_name = None
    hierarchy_dict = None

    if taxonomy_service:
        tax_res = taxonomy_service.resolve_taxon(top_match.scientific_name)
        if tax_res.is_resolved:
            resolved_sci_name = tax_res.scientific_name or top_match.scientific_name
            common_name = tax_res.common_name
            if tax_res.hierarchy:
                hierarchy_dict = tax_res.hierarchy.to_dict()
            if tax_res.warnings:
                warnings.extend(tax_res.warnings)

    evidence = ScientificEvidence(
        evidence_id=f"ev-edna-{query_id}",
        evidence_type=EvidenceType.EDNA_SEQUENCE,
        source_identifier=query_id,
        features={"sequence_length_bp": q_len, "target_gene": top_match.target_gene},
        metrics={
            "similarity_score": top_match.similarity_score,
            "baseline_confidence": conf,
            "matched_kmers": top_match.matched_kmer_count,
        },
        raw_reference=top_match.reference_id,
        provenance={"reference_source": top_match.reference_source, "match_type": top_match.match_type},
    )

    # Status classification
    if conf >= 0.85:
        status = IdentificationStatus.CONFIRMED
    elif conf >= confidence_threshold:
        status = IdentificationStatus.PROVISIONAL
    else:
        status = IdentificationStatus.UNRESOLVED
        warnings.append(
            f"Top match '{top_match.scientific_name}' (score {top_match.similarity_score:.2f}, "
            f"conf {conf:.2f}) is below threshold ({confidence_threshold:.2f})."
        )
        return SpeciesDetection(
            query_id=query_id,
            is_detected=False,
            species_name=None,
            status=status,
            confidence_score=conf,
            confidence_level=compute_confidence_level(conf),
            match_score=top_match.similarity_score,
            target_gene=top_match.target_gene,
            reference_id=top_match.reference_id,
            reference_source=top_match.reference_source,
            evidence=evidence,
            alternative_candidates=alt_candidates,
            taxonomic_hierarchy=hierarchy_dict,
            warnings=warnings,
            provenance={"query_id": query_id, "evidence_type": EvidenceType.EDNA_SEQUENCE.value},
        )

    # Check ambiguity if top 2 candidates are tied
    if second_score is not None and abs(top_match.similarity_score - second_score) < 0.01:
        status = IdentificationStatus.FLAGGED
        warnings.append(
            f"Ambiguous top match: '{top_match.scientific_name}' and '{second_match.scientific_name}' "
            f"have nearly identical similarity scores."
        )

    return SpeciesDetection(
        query_id=query_id,
        is_detected=True,
        species_name=resolved_sci_name,
        common_name=common_name,
        status=status,
        confidence_score=conf,
        confidence_level=compute_confidence_level(conf),
        match_score=top_match.similarity_score,
        target_gene=top_match.target_gene,
        reference_id=top_match.reference_id,
        reference_source=top_match.reference_source,
        evidence=evidence,
        alternative_candidates=alt_candidates,
        taxonomic_hierarchy=hierarchy_dict,
        warnings=warnings,
        provenance={"query_id": query_id, "evidence_type": EvidenceType.EDNA_SEQUENCE.value},
    )
