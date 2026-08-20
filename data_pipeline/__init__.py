"""
CMLRE Marine Intelligence Platform — Data Pipeline Package.
Provides data ingestion, parsing, quality control, scientific standardisation,
unit conversion, and provenance tracking for heterogeneous marine datasets.
"""

from data_pipeline.models import (
    DatasetQualityResult,
    DomainType,
    IssueSeverity,
    QualityScoreSummary,
    QualityStatus,
    TransformationRecord,
    ValidationIssue,
)
from data_pipeline.pipeline import QualityPipeline
from data_pipeline.quality_scorer import QualityScorer
from data_pipeline.schema_mapper import SchemaMapper
from data_pipeline.unit_converter import UnitConverter
from data_pipeline.validators import (
    CoordinateValidator,
    DuplicateValidator,
    MissingValueValidator,
    OutlierDetector,
    ScientificRangeValidator,
    TimestampValidator,
)
from data_pipeline.phase4_boundary import integrate_with_phase4

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
