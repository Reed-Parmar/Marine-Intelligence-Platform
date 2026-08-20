"""
Phase 3 -> Phase 4 Integration Boundary.
Provides a clean, typed contract for passing canonical Phase 3 datasets to the Phase 4 Quality Pipeline.
Zero code duplication: uses data_pipeline.QualityPipeline when available.
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


def integrate_with_phase4(
    canonical_df: pd.DataFrame,
    dataset_metadata: Optional[Dict[str, Any]] = None,
    unit_hints: Optional[Dict[str, str]] = None,
    custom_column_mapping: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Integration boundary passing canonical Phase 3 tabular data to the Phase 4 Quality Pipeline.
    
    Inputs:
        canonical_df: Cleaned and column-normalized pandas DataFrame
        dataset_metadata: Ingestion metadata (domain_type, upload_id, filename, preambles)
        unit_hints: Optional explicit unit specifications
        custom_column_mapping: Optional custom column remappings
        
    Outputs:
        Dict containing:
            - df: Standardized pandas DataFrame (after Phase 4 standardisation/unit conversion)
            - quality_score: float [0.0 - 100.0] or None if pending
            - quality_status: 'passed' | 'flagged' | 'failed' | 'pending'
            - validation_notes: Detailed validation report
            - provenance: Comprehensive pipeline provenance dictionary
            - validation_issues: List of ValidationIssue objects
            - summary: QualityScoreSummary object
            - phase4_executed: bool
    """
    meta = dataset_metadata or {}
    
    # Prepare records for QualityPipeline
    clean_df = canonical_df.where(pd.notnull(canonical_df), None)
    records: List[Dict[str, Any]] = clean_df.to_dict(orient="records")

    try:
        from data_pipeline.pipeline import QualityPipeline
        pipeline = QualityPipeline(
            unit_hints=unit_hints,
            custom_column_mapping=custom_column_mapping
        )
        qc_result = pipeline.process(records, dataset_metadata=meta)
        
        # Convert standardized records back to DataFrame
        std_recs = getattr(qc_result, "standardized_records", None)
        if std_recs is None:
            std_recs = getattr(qc_result, "standardised_records", None)
        standardized_records = std_recs if std_recs is not None else records
        out_df = pd.DataFrame(standardized_records)
        
        status_val = qc_result.quality_status.value if hasattr(qc_result.quality_status, "value") else str(qc_result.quality_status)
        
        return {
            "df": out_df,
            "quality_score": qc_result.quality_score,
            "quality_status": status_val,
            "validation_notes": qc_result.validation_notes,
            "provenance": qc_result.provenance,
            "validation_issues": qc_result.validation_issues,
            "summary": qc_result.summary,
            "qc_result": qc_result,
            "phase4_executed": True
        }
    except ImportError:
        # Phase 4 module is not available; return canonical dataset cleanly
        provenance = {
            "source_records_count": len(canonical_df),
            "columns_count": len(canonical_df.columns),
            "columns": list(canonical_df.columns),
            "status": "ingested_pending_qc"
        }
        if meta:
            provenance.update({k: v for k, v in meta.items() if not str(k).startswith("_")})

        return {
            "df": canonical_df,
            "quality_score": None,
            "quality_status": "pending",
            "validation_notes": "Phase 4 Quality Pipeline pending merge/execution.",
            "provenance": provenance,
            "validation_issues": [],
            "summary": None,
            "qc_result": None,
            "phase4_executed": False
        }
