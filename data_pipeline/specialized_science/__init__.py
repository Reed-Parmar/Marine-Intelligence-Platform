"""
Phase 7 — Specialized Scientific Modules.
Provides domain-specific marine science capabilities:
- eDNA sequence validation, quality filtering, reference matching, and detection
- Otolith and marine image validation, morphological feature extraction, and ML-ready classification
- Taxonomy multi-rank hierarchy retrieval, synonym mapping, and taxon resolution
- Common evidence representation and storage persistence boundary
"""

# Common
from data_pipeline.specialized_science.common import (
    ConfidenceLevel,
    EvidenceType,
    IdentificationStatus,
    InMemoryStorageRepository,
    ScientificEvidence,
    SpecializedResult,
    StorageRepository,
    build_specialized_result,
    compute_confidence_level,
)

# eDNA
from data_pipeline.specialized_science.edna import (
    DEFAULT_EDNA_REFERENCE_DATABASE,
    EDNAService,
    EDNAValidationResult,
    ExactReferenceMatcher,
    FASTARecord,
    FASTQRecord,
    KmerSimilarityMatcher,
    PreprocessedSequence,
    ReferenceMatcher,
    SequenceMatch,
    SpeciesDetection,
    calculate_baseline_edna_confidence,
    calculate_gc_content,
    detect_species_from_matches,
    preprocess_fastq_records,
    preprocess_sequence,
    validate_fasta,
    validate_fastq,
    validate_sequence_string,
)

# Otolith
from data_pipeline.specialized_science.otolith import (
    BaselineMorphologicalFeatureExtractor,
    BaselineOtolithClassifier,
    ImageFeatureExtractor,
    ImageValidationResult,
    OtolithAnalysisService,
    OtolithClassificationResult,
    OtolithClassifier,
    OtolithFeatureVector,
    PreprocessedImage,
    preprocess_image,
    validate_image_input,
)

# Taxonomy
from data_pipeline.specialized_science.taxonomy import (
    DEFAULT_TAXONOMY_RECORDS,
    SynonymResolver,
    TaxonHierarchy,
    TaxonomicRank,
    TaxonRecord,
    TaxonResolutionResult,
    TaxonomySearchEngine,
    TaxonomyService,
)

__all__ = [
    # Common
    "EvidenceType",
    "IdentificationStatus",
    "ConfidenceLevel",
    "ScientificEvidence",
    "SpecializedResult",
    "StorageRepository",
    "InMemoryStorageRepository",
    "compute_confidence_level",
    "build_specialized_result",
    # eDNA
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
    # Otolith
    "validate_image_input",
    "preprocess_image",
    "ImageValidationResult",
    "PreprocessedImage",
    "ImageFeatureExtractor",
    "BaselineMorphologicalFeatureExtractor",
    "OtolithFeatureVector",
    "OtolithClassifier",
    "BaselineOtolithClassifier",
    "OtolithClassificationResult",
    "OtolithAnalysisService",
    # Taxonomy
    "TaxonomicRank",
    "TaxonHierarchy",
    "TaxonRecord",
    "TaxonomySearchEngine",
    "SynonymResolver",
    "TaxonomyService",
    "TaxonResolutionResult",
    "DEFAULT_TAXONOMY_RECORDS",
]
