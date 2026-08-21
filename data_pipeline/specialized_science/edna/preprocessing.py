"""
Phase 7 — eDNA Sequence Preprocessing.
Cleans nucleotide strings, calculates GC content, filters ambiguous base ratios,
and applies quality-score filtering for FASTQ reads.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from data_pipeline.specialized_science.edna.validation import FASTQRecord


@dataclass
class PreprocessedSequence:
    """Standard container for preprocessed eDNA sequence data."""
    id: str
    raw_sequence: str
    cleaned_sequence: str
    length: int
    gc_content: float
    ambiguous_bases_ratio: float
    avg_quality_score: Optional[float] = None
    passed_filter: bool = True
    filter_notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "length": self.length,
            "gc_content": round(self.gc_content, 4),
            "ambiguous_bases_ratio": round(self.ambiguous_bases_ratio, 4),
            "avg_quality_score": round(self.avg_quality_score, 2) if self.avg_quality_score is not None else None,
            "passed_filter": self.passed_filter,
            "filter_notes": self.filter_notes,
        }


def calculate_gc_content(sequence: str) -> float:
    """Calculates GC ratio (G + C) / total_length for DNA sequence."""
    if not sequence:
        return 0.0
    seq_u = sequence.upper()
    gc_count = seq_u.count("G") + seq_u.count("C")
    return gc_count / len(seq_u)


def preprocess_sequence(
    raw_seq: str,
    seq_id: str = "seq_01",
    min_length: int = 20,
    max_ambiguous_ratio: float = 0.10,
    to_upper: bool = True,
    strip_gaps: bool = True,
) -> PreprocessedSequence:
    """
    Standardizes and filters a raw DNA sequence string.

    Args:
        raw_seq: Raw input DNA sequence.
        seq_id: Unique identifier for the read.
        min_length: Minimum accepted sequence length in base pairs.
        max_ambiguous_ratio: Maximum allowed ratio of N or ambiguous IUPAC bases.
        to_upper: Uppercase all bases.
        strip_gaps: Remove gap '-' or '.' characters.
    """
    if not raw_seq:
        return PreprocessedSequence(
            id=seq_id,
            raw_sequence="",
            cleaned_sequence="",
            length=0,
            gc_content=0.0,
            ambiguous_bases_ratio=1.0,
            passed_filter=False,
            filter_notes=["Sequence is empty."],
        )

    cleaned = raw_seq.strip()
    if to_upper:
        cleaned = cleaned.upper()

    cleaned = cleaned.replace(" ", "").replace("\n", "").replace("\r", "")
    if strip_gaps:
        cleaned = cleaned.replace("-", "").replace(".", "")

    length = len(cleaned)
    notes: List[str] = []
    passed = True

    if length < min_length:
        passed = False
        notes.append(f"Sequence length ({length} bp) below minimum threshold ({min_length} bp).")

    # Count ambiguous bases (characters other than standard A, C, G, T, U)
    standard_bases = set("ACGTU")
    ambiguous_count = sum(1 for b in cleaned if b not in standard_bases)
    ambig_ratio = ambiguous_count / length if length > 0 else 1.0

    if ambig_ratio > max_ambiguous_ratio:
        passed = False
        notes.append(f"Ambiguous base ratio ({ambig_ratio:.2%}) exceeds maximum allowed ({max_ambiguous_ratio:.2%}).")

    gc_cont = calculate_gc_content(cleaned)

    return PreprocessedSequence(
        id=seq_id,
        raw_sequence=raw_seq,
        cleaned_sequence=cleaned,
        length=length,
        gc_content=gc_cont,
        ambiguous_bases_ratio=ambig_ratio,
        passed_filter=passed,
        filter_notes=notes,
    )


def preprocess_fastq_records(
    records: List[FASTQRecord],
    min_phred: int = 20,
    min_length: int = 30,
) -> List[PreprocessedSequence]:
    """
    Processes FASTQ records by calculating Phred quality and trimming low-quality ends.
    """
    results: List[PreprocessedSequence] = []

    for rec in records:
        seq = rec.sequence.strip().upper()
        qual = rec.quality.strip()

        # Convert ASCII to Phred+33 scores
        phred_scores = [ord(c) - 33 for c in qual]
        avg_q = sum(phred_scores) / len(phred_scores) if phred_scores else 0.0

        # Simple 3' end quality trimming: trim until base has >= min_phred
        trim_idx = len(seq)
        while trim_idx > 0 and phred_scores[trim_idx - 1] < min_phred:
            trim_idx -= 1

        trimmed_seq = seq[:trim_idx]
        trimmed_scores = phred_scores[:trim_idx]
        trimmed_avg_q = sum(trimmed_scores) / len(trimmed_scores) if trimmed_scores else avg_q

        prep = preprocess_sequence(trimmed_seq, seq_id=rec.id, min_length=min_length)
        prep.avg_quality_score = trimmed_avg_q

        if len(trimmed_seq) < len(seq):
            prep.metadata["bases_trimmed"] = len(seq) - len(trimmed_seq)

        results.append(prep)

    return results
