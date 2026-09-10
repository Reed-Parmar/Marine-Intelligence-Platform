"""
Phase 4: Data Quality & Scientific Standardisation Layer.
Provides schema normalization, unit conversions, scientific validation rules,
quality scoring, provenance tracking, and pipeline boundaries.
"""

from data_pipeline.quality_standardisation.models import (
    DatasetQualityResult,
    DomainType,
    IssueSeverity,
    QualityScoreSummary,
    QualityStatus,
    TransformationRecord,
    ValidationIssue,
)
from data_pipeline.quality_standardisation.phase4_boundary import (
    integrate_with_phase4,
)
from data_pipeline.quality_standardisation.pipeline import QualityPipeline
from data_pipeline.quality_standardisation.quality_scorer import QualityScorer
from data_pipeline.quality_standardisation.schema_mapper import SchemaMapper
from data_pipeline.quality_standardisation.unit_converter import UnitConverter
from data_pipeline.quality_standardisation.validators import (
    CoordinateValidator,
    DuplicateValidator,
    MissingValueValidator,
    OutlierDetector,
    ScientificRangeValidator,
    TimestampValidator,
)

__all__ = [
    "QualityPipeline",
    "DatasetQualityResult",
    "ValidationIssue",
    "TransformationRecord",
    "QualityScoreSummary",
    "IssueSeverity",
    "QualityStatus",
    "DomainType",
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
]
