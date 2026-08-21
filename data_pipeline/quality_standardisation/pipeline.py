"""
Main Quality & Standardisation Pipeline for Phase 4.
Provides a clean, unified, zero-bloat interface for Phase 3 ingestion to consume.
"""

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Union
import json

from data_pipeline.quality_standardisation.models import (
    DatasetQualityResult,
    DomainType,
    IssueSeverity,
    QualityScoreSummary,
    QualityStatus,
    TransformationRecord,
    ValidationIssue,
)
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


class QualityPipeline:
    """
    Orchestrates end-to-end data quality checks, schema standardization,
    unit conversions, validation notes, and provenance tracking.
    """

    def __init__(
        self,
        custom_column_mapping: Optional[Dict[str, str]] = None,
        unit_hints: Optional[Dict[str, str]] = None,
        custom_missing_markers: Optional[Set[str]] = None,
        custom_range_rules: Optional[Dict[str, Dict[str, Any]]] = None,
        key_columns: Optional[List[str]] = None,
        iqr_multiplier: float = 1.5
    ):
        self.schema_mapper = SchemaMapper(custom_mapping=custom_column_mapping)
        self.unit_converter = UnitConverter(unit_hints=unit_hints)
        self.missing_validator = MissingValueValidator(custom_markers=custom_missing_markers)
        self.duplicate_validator = DuplicateValidator(key_columns=key_columns)
        self.coordinate_validator = CoordinateValidator()
        self.timestamp_validator = TimestampValidator()
        self.range_validator = ScientificRangeValidator(custom_rules=custom_range_rules)
        self.outlier_detector = OutlierDetector(iqr_multiplier=iqr_multiplier)
        self.scorer = QualityScorer()

    def process(
        self,
        data: List[Dict[str, Any]],
        dataset_metadata: Optional[Dict[str, Any]] = None
    ) -> DatasetQualityResult:
        """
        Processes incoming raw records through the complete quality pipeline.
        
        Args:
            data: List of raw record dictionaries.
            dataset_metadata: Optional metadata (e.g. dataset_id, domain_type, source).
            
        Returns:
            DatasetQualityResult with standardized records, quality score, issues, and provenance.
        """
        metadata = dataset_metadata or {}
        raw_records = deepcopy(data)
        all_issues: List[ValidationIssue] = []
        all_transformations: List[TransformationRecord] = []

        if not data:
            empty_summary = self.scorer.calculate_score(
                total_records=0,
                total_fields=0,
                missing_count=0,
                duplicate_count=0,
                invalid_coords_count=0,
                invalid_timestamps_count=0,
                range_violations_count=0,
                outliers_count=0,
                unmapped_columns=[],
                validation_issues=[]
            )
            return DatasetQualityResult(
                standardised_records=[],
                raw_records=[],
                quality_score=0.0,
                quality_status=QualityStatus.FAILED,
                validation_issues=[
                    ValidationIssue(
                        check="empty_dataset",
                        column="dataset",
                        severity=IssueSeverity.ERROR,
                        message="Dataset contains zero records to process"
                    )
                ],
                summary=empty_summary,
                provenance={
                    "pipeline_version": "phase-4-v1.0.0",
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "record_count": 0,
                    "applied_transformations": []
                },
                validation_notes="Dataset is empty. Quality check failed."
            )

        # 1. Schema Mapping & Column Normalization
        mapped_records, schema_issues, schema_transforms, unmapped_cols = self.schema_mapper.map_columns(raw_records)
        all_issues.extend(schema_issues)
        all_transformations.extend(schema_transforms)

        # 2. Unit Conversion & Non-Destructive Normalization
        std_unit_records: List[Dict[str, Any]] = []
        for idx, row in enumerate(mapped_records):
            conv_row, unit_issues, unit_transforms = self.unit_converter.standardize_record(row, idx)
            std_unit_records.append(conv_row)
            all_issues.extend(unit_issues)
            all_transformations.extend(unit_transforms)

        # 3. Missing Value Normalization & Analysis
        cleaned_records, missing_issues, missing_counts, total_missing = self.missing_validator.validate(std_unit_records)
        all_issues.extend(missing_issues)

        # 4. Duplicate Record Detection
        dup_issues, dup_count, dup_indices = self.duplicate_validator.validate(cleaned_records)
        all_issues.extend(dup_issues)

        # 5. Coordinate & Spatial Bounds Validation
        coord_records, coord_issues, coord_transforms, invalid_coords = self.coordinate_validator.validate(cleaned_records)
        all_issues.extend(coord_issues)
        all_transformations.extend(coord_transforms)

        # 6. Timestamp & Temporal Validation
        time_records, time_issues, time_transforms, invalid_times = self.timestamp_validator.validate(coord_records)
        all_issues.extend(time_issues)
        all_transformations.extend(time_transforms)

        # 7. Scientific Range Checks
        range_issues, range_violations = self.range_validator.validate(time_records)
        all_issues.extend(range_issues)

        # 8. Statistical Outlier Detection (IQR)
        outlier_issues, total_outliers = self.outlier_detector.detect(time_records)
        all_issues.extend(outlier_issues)

        # 9. Quality Scoring & Status Computation
        total_fields = max(len(r.keys()) for r in time_records) if time_records else 0
        summary = self.scorer.calculate_score(
            total_records=len(time_records),
            total_fields=total_fields,
            missing_count=total_missing,
            duplicate_count=dup_count,
            invalid_coords_count=invalid_coords,
            invalid_timestamps_count=invalid_times,
            range_violations_count=range_violations,
            outliers_count=total_outliers,
            unmapped_columns=unmapped_cols,
            validation_issues=all_issues
        )

        # 10. Generate Provenance Metadata & Human-Readable Validation Notes
        provenance = self._build_provenance(
            metadata=metadata,
            transformations=all_transformations,
            summary=summary,
            unmapped_columns=unmapped_cols
        )
        validation_notes = self._generate_validation_notes(summary, all_issues)

        return DatasetQualityResult(
            standardised_records=time_records,
            raw_records=raw_records,
            quality_score=summary.overall_score,
            quality_status=summary.status,
            validation_issues=all_issues,
            summary=summary,
            provenance=provenance,
            validation_notes=validation_notes
        )

    def _build_provenance(
        self,
        metadata: Dict[str, Any],
        transformations: List[TransformationRecord],
        summary: QualityScoreSummary,
        unmapped_columns: List[str]
    ) -> Dict[str, Any]:
        """Builds structured provenance and audit metadata."""
        return {
            "pipeline_name": "CMLRE Data Quality & Standardisation Engine",
            "pipeline_version": "phase-4-v1.0.0",
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "dataset_id": metadata.get("id") or metadata.get("dataset_id"),
            "domain_type": metadata.get("domain_type", DomainType.OCEANOGRAPHY.value),
            "input_record_count": summary.total_records,
            "quality_status": summary.status.value,
            "quality_score": summary.overall_score,
            "transformation_summary": {
                "total_transformations": len(transformations),
                "unmapped_columns": unmapped_columns,
                "sample_transformations": [t.to_dict() for t in transformations[:30]]
            }
        }

    def _generate_validation_notes(
        self,
        summary: QualityScoreSummary,
        issues: List[ValidationIssue]
    ) -> str:
        """Generates concise, human-readable summary notes suitable for database storage and researcher review."""
        lines = [
            f"Quality Score: {summary.overall_score}/100 based on the platform's predefined QC criteria ({summary.status.value.upper()})",
            f"Total Records: {summary.total_records} | Total Fields: {summary.total_fields}",
            f"Issues: {summary.issues_by_severity.get('error', 0)} Error(s), "
            f"{summary.issues_by_severity.get('warning', 0)} Warning(s), "
            f"{summary.issues_by_severity.get('info', 0)} Info"
        ]

        if summary.missing_count > 0:
            lines.append(f"• Missing data: {summary.missing_count} cell(s) ({summary.missing_percentage}%)")
        if summary.duplicate_count > 0:
            lines.append(f"• Duplicates: {summary.duplicate_count} record(s) ({summary.duplicate_percentage}%)")
        if summary.invalid_coords_count > 0:
            lines.append(f"• Invalid coordinates: {summary.invalid_coords_count} record(s)")
        if summary.invalid_timestamps_count > 0:
            lines.append(f"• Invalid timestamps: {summary.invalid_timestamps_count} record(s)")
        if summary.range_violations_count > 0:
            lines.append(f"• Scientific range violations: {summary.range_violations_count} record(s)")
        if summary.outliers_count > 0:
            lines.append(f"• Statistical outliers (IQR): {summary.outliers_count} value(s)")
        if summary.unmapped_columns:
            lines.append(f"• Unmapped domain fields: {', '.join(summary.unmapped_columns)}")

        # Deductions breakdown
        active_deductions = {k: v for k, v in summary.deductions.items() if v > 0}
        if active_deductions:
            lines.append("• Scoring deductions: " + ", ".join(f"{k}: -{v}pts" for k, v in active_deductions.items()))

        return "\n".join(lines)
