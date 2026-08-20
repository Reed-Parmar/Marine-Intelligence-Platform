"""
Deterministic Quality Scorer for Phase 4.
Computes a transparent 0-100 dataset quality score and quality status flag.
"""

from typing import Any, Dict, List
from data_pipeline.models import (
    IssueSeverity,
    QualityScoreSummary,
    QualityStatus,
    ValidationIssue,
)


class QualityScorer:
    """
    Computes a deterministic, explainable data quality score (0 - 100).
    
    Rubric & Weighting:
    - Base Score: 100 points
    - Spatial Integrity (Coordinates): max deduction 25 points
    - Temporal Integrity (Timestamps): max deduction 20 points
    - Scientific Validity (Range checks): max deduction 15 points
    - Data Completeness (Missing values): max deduction 15 points
    - Uniqueness (Duplicate records): max deduction 10 points
    - Schema Compliance (Unmapped columns): max deduction 10 points
    - Statistical Consistency (Outliers): max deduction 5 points
    """

    def calculate_score(
        self,
        total_records: int,
        total_fields: int,
        missing_count: int,
        duplicate_count: int,
        invalid_coords_count: int,
        invalid_timestamps_count: int,
        range_violations_count: int,
        outliers_count: int,
        unmapped_columns: List[str],
        validation_issues: List[ValidationIssue]
    ) -> QualityScoreSummary:
        """Calculates score, deductions, issue breakdown, and quality status."""
        if total_records == 0:
            return QualityScoreSummary(
                overall_score=0.0,
                status=QualityStatus.FAILED,
                total_records=0,
                total_fields=0,
                missing_count=0,
                missing_percentage=0.0,
                duplicate_count=0,
                duplicate_percentage=0.0,
                invalid_coords_count=0,
                invalid_timestamps_count=0,
                range_violations_count=0,
                outliers_count=0,
                unmapped_columns=[],
                deductions={"empty_dataset": 100.0},
                issues_by_severity={"info": 0, "warning": 0, "error": 1}
            )

        total_cells = max(1, total_records * max(1, total_fields))
        missing_pct = round((missing_count / total_cells) * 100.0, 2)
        duplicate_pct = round((duplicate_count / total_records) * 100.0, 2)

        # 1. Spatial deduction (max 25)
        # Penalizes invalid or impossible coordinates proportionally to affected rows
        coord_error_ratio = min(1.0, invalid_coords_count / total_records)
        spatial_deduction = round(min(25.0, coord_error_ratio * 40.0), 2)

        # 2. Temporal deduction (max 20)
        # Penalizes unparseable or impossible timestamps proportionally
        time_error_ratio = min(1.0, invalid_timestamps_count / total_records)
        temporal_deduction = round(min(20.0, time_error_ratio * 35.0), 2)

        # 3. Scientific range violation deduction (max 15)
        range_error_ratio = min(1.0, range_violations_count / total_records)
        range_deduction = round(min(15.0, range_error_ratio * 30.0), 2)

        # 4. Missing values deduction (max 15)
        missing_deduction = round(min(15.0, (missing_pct / 40.0) * 15.0), 2)

        # 5. Duplicates deduction (max 10)
        duplicate_deduction = round(min(10.0, (duplicate_pct / 25.0) * 10.0), 2)

        # 6. Schema unmapped columns deduction (max 10)
        schema_deduction = min(10.0, len(unmapped_columns) * 2.0)

        # 7. Outliers deduction (max 5)
        outlier_ratio = min(1.0, outliers_count / max(1, total_records))
        outlier_deduction = round(outlier_ratio * 5.0, 2)

        deductions: Dict[str, float] = {
            "spatial_errors": spatial_deduction,
            "temporal_errors": temporal_deduction,
            "range_violations": range_deduction,
            "missing_values": missing_deduction,
            "duplicate_records": duplicate_deduction,
            "schema_non_standard": schema_deduction,
            "statistical_outliers": outlier_deduction
        }

        total_deductions = sum(deductions.values())
        raw_score = 100.0 - total_deductions
        final_score = max(0.0, min(100.0, round(raw_score, 2)))

        # Count issues by severity
        issues_by_severity = {
            IssueSeverity.INFO.value: 0,
            IssueSeverity.WARNING.value: 0,
            IssueSeverity.ERROR.value: 0
        }
        for issue in validation_issues:
            issues_by_severity[issue.severity.value] = issues_by_severity.get(issue.severity.value, 0) + 1

        error_count = issues_by_severity[IssueSeverity.ERROR.value]
        warning_count = issues_by_severity[IssueSeverity.WARNING.value]

        # Determine quality status
        if final_score >= 85.0 and error_count == 0:
            status = QualityStatus.PASSED
        elif final_score >= 60.0 and (coord_error_ratio < 0.25 and time_error_ratio < 0.25):
            status = QualityStatus.FLAGGED
        else:
            status = QualityStatus.FAILED

        return QualityScoreSummary(
            overall_score=final_score,
            status=status,
            total_records=total_records,
            total_fields=total_fields,
            missing_count=missing_count,
            missing_percentage=missing_pct,
            duplicate_count=duplicate_count,
            duplicate_percentage=duplicate_pct,
            invalid_coords_count=invalid_coords_count,
            invalid_timestamps_count=invalid_timestamps_count,
            range_violations_count=range_violations_count,
            outliers_count=outliers_count,
            unmapped_columns=unmapped_columns,
            deductions=deductions,
            issues_by_severity=issues_by_severity
        )
