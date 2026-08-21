"""
eDNA analysis package exports.
"""

from data_pipeline.specialized_science.edna.detection import (
    SpeciesDetection,
    calculate_baseline_edna_confidence,
    detect_species_from_matches,
)
from data_pipeline.specialized_science.edna.matching import (
    DEFAULT_EDNA_REFERENCE_DATABASE,
    ExactReferenceMatcher,
    KmerSimilarityMatcher,
    ReferenceMatcher,
    SequenceMatch,
)
from data_pipeline.specialized_science.edna.preprocessing import (
    PreprocessedSequence,
    calculate_gc_content,
    preprocess_fastq_records,
    preprocess_sequence,
)
from data_pipeline.specialized_science.edna.service import EDNAService
from data_pipeline.specialized_science.edna.validation import (
    EDNAValidationResult,
    FASTARecord,
    FASTQRecord,
    validate_fasta,
    validate_fastq,
    validate_sequence_string,
)

__all__ = [
    "validate_fasta",
    "validate_fastq",
    "validate_sequence_string",
    "FASTARecord",
    "FASTQRecord",
    "EDNAValidationResult",
    "preprocess_sequence",
    "preprocess_fastq_records",
    "calculate_gc_content",
    "PreprocessedSequence",
    "ReferenceMatcher",
    "SequenceMatch",
    "ExactReferenceMatcher",
    "KmerSimilarityMatcher",
    "DEFAULT_EDNA_REFERENCE_DATABASE",
    "SpeciesDetection",
    "detect_species_from_matches",
    "calculate_baseline_edna_confidence",
    "EDNAService",
]
