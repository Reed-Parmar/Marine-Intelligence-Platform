"""
Data models and type definitions for Phase 4: Data Quality and Standardisation.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import json
from datetime import datetime, timezone


class IssueSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class QualityStatus(str, Enum):
    PASSED = "passed"
    FLAGGED = "flagged"
    FAILED = "failed"


class DomainType(str, Enum):
    OCEANOGRAPHY = "oceanography"
    FISHERIES = "fisheries"
    BIODIVERSITY = "biodiversity"
    EDNA = "edna"
    OTOLITH = "otolith"
    GENERAL = "general"


@dataclass
class ValidationIssue:
    """Represents a specific validation finding, error, or warning."""
    check: str                          # e.g., 'missing_value', 'coordinate_bounds', 'range_check'
    column: str                         # affected column name or 'row'
    severity: IssueSeverity             # INFO, WARNING, ERROR
    message: str                        # Human-readable explanation
    row_index: Optional[int] = None     # 0-indexed row number where issue occurred
    value: Optional[Any] = None         # Offending or flagged value
    expected: Optional[str] = None      # Description of expected range/format
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


@dataclass
class TransformationRecord:
    """Records a single transformation applied to a field or record for provenance."""
    column: str
    row_index: int
    original_value: Any
    transformed_value: Any
    rule: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QualityScoreSummary:
    """Detailed summary of quality metrics and scoring deductions."""
    overall_score: float
    status: QualityStatus
    total_records: int
    total_fields: int
    missing_count: int
    missing_percentage: float
    duplicate_count: int
    duplicate_percentage: float
    invalid_coords_count: int
    invalid_timestamps_count: int
    range_violations_count: int
    outliers_count: int
    unmapped_columns: List[str]
    deductions: Dict[str, float]
    issues_by_severity: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class DatasetQualityResult:
    """Complete result of quality and standardisation processing for a dataset."""
    standardised_records: List[Dict[str, Any]]
    raw_records: List[Dict[str, Any]]
    quality_score: float
    quality_status: QualityStatus
    validation_issues: List[ValidationIssue]
    summary: QualityScoreSummary
    provenance: Dict[str, Any]
    validation_notes: str

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the result to a clean dictionary suitable for JSON APIs and database storage."""
        return {
            "quality_score": round(self.quality_score, 2),
            "quality_status": self.quality_status.value,
            "summary": self.summary.to_dict(),
            "validation_issues": [issue.to_dict() for issue in self.validation_issues],
            "validation_notes": self.validation_notes,
            "provenance": self.provenance,
            "record_count": len(self.standardised_records),
            "standardised_records": self.standardised_records,
            "raw_records": self.raw_records
        }

    def to_postgres_dataset_update(self) -> Dict[str, Any]:
        """Returns the dictionary payload matching the columns of the public.datasets table."""
        return {
            "quality_score": round(self.quality_score, 2),
            "quality_status": self.quality_status.value,
            "validation_notes": self.validation_notes,
            "provenance_metadata": self.provenance
        }
