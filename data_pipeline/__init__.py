"""
CMLRE Marine Intelligence Platform — Data Pipeline Package.
Modular, phase-oriented data pipeline containing:
- Phase 2: storage (Supabase file storage & dataset registration)
- Phase 3: ingestion (format detection, parsing, normalization, canonical export)
- Phase 4: quality_standardisation (QC validators, unit converter, quality scoring)
- Phase 5: fusion (spatial/temporal/depth alignment, unified query, cross-domain linking)
- Phase 6: analysis (ocean/fisheries trends, biodiversity, spatial/temporal, correlation, ecosystem)
- shared: common models and enumerations
"""

# Shared
from data_pipeline.shared import DomainType

# Phase 2: Storage & Database Integration
from data_pipeline.storage import (
    get_supabase_client,
    register_dataset,
    upload_to_storage,
)

# Phase 3: Ingestion & Raw Parsing
from data_pipeline.ingestion import (
    CANONICAL_COLUMN_MAPPINGS,
    classify_domain,
    detect_delimiter_and_header,
    detect_format_and_preview,
    export_canonical_csv,
    export_canonical_xlsx,
    extract_preamble_metadata,
    normalize_dataframe_columns,
    parse_cmlre_txt,
    process_all_datasets,
    process_upload,
)

# Phase 4: Quality & Scientific Standardisation
from data_pipeline.quality_standardisation import (
    CoordinateValidator,
    DatasetQualityResult,
    DuplicateValidator,
    IssueSeverity,
    MissingValueValidator,
    OutlierDetector,
    QualityPipeline,
    QualityScoreSummary,
    QualityScorer,
    QualityStatus,
    ScientificRangeValidator,
    SchemaMapper,
    TimestampValidator,
    TransformationRecord,
    UnitConverter,
    ValidationIssue,
    integrate_with_phase4,
)

# Phase 5: Data Fusion & Unified Marine Data
from data_pipeline.fusion import (
    CrossDomainAssociation,
    MarineObservation,
    UnifiedQueryParams,
    UnifiedSummary,
    get_cross_domain_context,
    get_domain_observations,
    get_unified_summary,
    query_unified_observations,
)

# Phase 6: Scientific Analysis
from data_pipeline.analysis import (
    BiodiversityResult,
    CorrelationResult,
    ECOSYSTEM_THEMES,
    EcosystemRelationshipResult,
    FisheriesTrendResult,
    OceanTrendResult,
    ScientificAnalysisService,
    SpatialAnalysisResult,
    SpatialGridCell,
    SpeciesDistributionResult,
    TemporalAnalysisResult,
    TemporalBucket,
    TrendDataPoint,
    analyze_ecosystem_relationship,
    analyze_fisheries_trends,
    analyze_ocean_trends,
    analyze_spatial_distribution,
    analyze_species_distribution,
    analyze_temporal_dynamics,
    calculate_biodiversity_indicators,
    calculate_cross_domain_correlation,
    pair_cross_domain_observations,
)

__all__ = [
    # Shared
    "DomainType",
    # Phase 2: Storage
    "get_supabase_client",
    "upload_to_storage",
    "register_dataset",
    # Phase 3: Ingestion
    "classify_domain",
    "detect_format_and_preview",
    "detect_delimiter_and_header",
    "extract_preamble_metadata",
    "parse_cmlre_txt",
    "normalize_dataframe_columns",
    "CANONICAL_COLUMN_MAPPINGS",
    "export_canonical_csv",
    "export_canonical_xlsx",
    "process_upload",
    "process_all_datasets",
    # Phase 4: Quality & Standardisation
    "QualityPipeline",
    "DatasetQualityResult",
    "ValidationIssue",
    "TransformationRecord",
    "QualityScoreSummary",
    "IssueSeverity",
    "QualityStatus",
    "SchemaMapper",
    "UnitConverter",
    "MissingValueValidator",
    "DuplicateValidator",
    "CoordinateValidator",
    "TimestampValidator",
    "ScientificRangeValidator",
    "OutlierDetector",
    "QualityScorer",
    "integrate_with_phase4",
    # Phase 5: Data Fusion
    "MarineObservation",
    "UnifiedQueryParams",
    "CrossDomainAssociation",
    "UnifiedSummary",
    "query_unified_observations",
    "get_domain_observations",
    "get_unified_summary",
    "get_cross_domain_context",
    # Phase 6: Scientific Analysis
    "ScientificAnalysisService",
    "analyze_ocean_trends",
    "analyze_fisheries_trends",
    "analyze_species_distribution",
    "calculate_biodiversity_indicators",
    "analyze_spatial_distribution",
    "analyze_temporal_dynamics",
    "calculate_cross_domain_correlation",
    "pair_cross_domain_observations",
    "analyze_ecosystem_relationship",
    "ECOSYSTEM_THEMES",
    "TrendDataPoint",
    "OceanTrendResult",
    "FisheriesTrendResult",
    "SpeciesDistributionResult",
    "BiodiversityResult",
    "SpatialGridCell",
    "SpatialAnalysisResult",
    "TemporalBucket",
    "TemporalAnalysisResult",
    "CorrelationResult",
    "EcosystemRelationshipResult",
]
