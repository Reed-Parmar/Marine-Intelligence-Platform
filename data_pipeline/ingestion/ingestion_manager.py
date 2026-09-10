"""
Main Ingestion Manager and Orchestrator for CMLRE Data Pipeline.
Coordinates format detection, metadata extraction, column normalization,
canonical export (CSV/XLSX), Phase 4 QC boundary, storage upload, and dataset registration.
"""

import os
import uuid
from typing import Any, Dict, Optional
import pandas as pd

from data_pipeline.ingestion.canonical_exporter import export_canonical_csv, export_canonical_xlsx
from data_pipeline.ingestion.format_detector import classify_domain, detect_format_and_preview
from data_pipeline.ingestion.schema_normalizer import normalize_dataframe_columns
from data_pipeline.ingestion.txt_parser import parse_cmlre_txt
from data_pipeline.quality_standardisation.phase4_boundary import integrate_with_phase4
from data_pipeline.storage.dataset_registrar import register_dataset
from data_pipeline.storage.file_handler import upload_to_storage

DEFAULT_PROJECT_ID = "c1d2e3f4-0000-0000-0000-000000000001"


def process_upload(
    file_path: str, 
    dataset_name: Optional[str] = None, 
    project_id: Optional[str] = DEFAULT_PROJECT_ID,
    domain_type: Optional[str] = None,
    uploaded_by: Optional[str] = None,
    export_canonical: bool = True,
    export_xlsx: bool = False,
    unit_hints: Optional[Dict[str, str]] = None,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main orchestration function for the Phase 3 Data Ingestion Engine.
    
    1. Validates file existence and detects format, schema, row count, and domain.
    2. Parses tabular rows and extracts all preamble / cruise / instrument metadata.
    3. Normalizes column names to CMLRE canonical schema without dropping unmapped columns.
    4. Generates canonical CSV (and optional XLSX) files.
    5. Passes canonical data to Phase 4 Quality Pipeline boundary.
    6. Uploads raw and canonical files to Supabase Storage at datasets/{dataset_id}/...
    7. Registers dataset metadata in Supabase PostgreSQL public.datasets table.
    """
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"File not found: {file_path}"}
    
    filename = os.path.basename(file_path)
    dataset_name = dataset_name or f"CMLRE: {filename}"
    dataset_id = str(uuid.uuid4())
    ext = os.path.splitext(file_path)[1].lower()
    
    print(f"\n[Ingestion] Processing dataset: {filename} (ID: {dataset_id})")
    
    # 1. Parse dataset and extract metadata
    try:
        if ext in [".txt", ".tsv", ".dat", ".csv", ""]:
            raw_df, extracted_meta, diagnostics = parse_cmlre_txt(file_path)
            format_name = "txt" if ext != ".csv" else "csv"
        elif ext in [".xls", ".xlsx"]:
            raw_df = pd.read_excel(file_path)
            extracted_meta = {}
            diagnostics = {"format": ext.lstrip(".")}
            format_name = ext.lstrip(".")
        elif ext == ".json":
            raw_df = pd.read_json(file_path)
            extracted_meta = {}
            diagnostics = {"format": "json"}
            format_name = "json"
        else:
            return {"status": "error", "message": f"Unsupported file format: {ext}"}
    except Exception as e:
        return {"status": "error", "message": f"Parsing failed: {str(e)}"}

    if raw_df is None or len(raw_df) == 0:
        return {"status": "error", "message": f"Dataset contains no valid data rows: {filename}"}

    # 2. Schema Normalization
    normalized_df, applied_mappings = normalize_dataframe_columns(raw_df)
    
    # 3. Domain Classification
    resolved_domain = domain_type or classify_domain(list(normalized_df.columns))
    
    row_count = len(normalized_df)
    file_size_bytes = os.path.getsize(file_path)
    columns = list(normalized_df.columns)
    
    print(f" -> Format: {format_name} | Domain: {resolved_domain} | Rows: {row_count:,} | Cols: {len(columns)}")

    # 4. Phase 4 Quality Pipeline Integration Boundary
    ds_metadata = {
        "dataset_id": dataset_id,
        "dataset_name": dataset_name,
        "domain_type": resolved_domain,
        "source_filename": filename,
        "preambles": extracted_meta
    }
    qc_res = integrate_with_phase4(
        canonical_df=normalized_df,
        dataset_metadata=ds_metadata,
        unit_hints=unit_hints
    )
    final_df = qc_res["df"]
    quality_score = qc_res["quality_score"]
    quality_status = qc_res["quality_status"]
    validation_notes = qc_res["validation_notes"]

    # 5. Canonical Export
    target_dir = output_dir or os.path.join(os.path.dirname(os.path.abspath(file_path)), "canonical_output")
    canonical_csv_path = None
    canonical_xlsx_path = None
    
    if export_canonical:
        canonical_csv_name = f"canonical_{os.path.splitext(filename)[0]}.csv"
        canonical_csv_path = os.path.join(target_dir, dataset_id, canonical_csv_name)
        export_canonical_csv(final_df, canonical_csv_path)
        
    if export_xlsx:
        canonical_xlsx_name = f"canonical_{os.path.splitext(filename)[0]}.xlsx"
        canonical_xlsx_path = os.path.join(target_dir, dataset_id, canonical_xlsx_name)
        export_canonical_xlsx(final_df, canonical_xlsx_path, metadata=extracted_meta)

    # 6. Upload to Supabase Storage
    try:
        storage_path = upload_to_storage(file_path, dataset_id=dataset_id)
        if canonical_csv_path and os.path.exists(canonical_csv_path):
            upload_to_storage(canonical_csv_path, dataset_id=dataset_id)
        print(f" -> Uploaded to Supabase Storage: {storage_path}")
    except Exception as e:
        return {"status": "error", "message": f"Storage upload failed: {str(e)}"}

    # 7. Register Dataset in Supabase PostgreSQL
    schema_metadata = {col: str(final_df[col].dtype) for col in final_df.columns}
    provenance = qc_res["provenance"]
    provenance.update({
        "original_filename": filename,
        "extracted_metadata": extracted_meta,
        "applied_column_mappings": applied_mappings,
        "canonical_csv_path": canonical_csv_path
    })

    try:
        record = register_dataset(
            name=dataset_name,
            storage_path=storage_path,
            schema=schema_metadata,
            format_type=format_name,
            domain_type=resolved_domain,
            file_size_bytes=file_size_bytes,
            row_count=row_count,
            dataset_id=dataset_id,
            project_id=project_id,
            uploaded_by=uploaded_by,
            status="standardized" if quality_status == "passed" else "uploaded",
            quality_status=quality_status,
            quality_score=quality_score,
            validation_notes=validation_notes,
            provenance_metadata=provenance
        )
        print(f" -> Registered in PostgreSQL (datasets.id: {dataset_id})")
    except Exception as e:
        return {"status": "error", "message": f"Database registration failed: {str(e)}"}

    # Prepare preview (top 5 rows)
    preview_df = final_df.head(5).copy()
    preview_df = preview_df.where(pd.notnull(preview_df), None)

    return {
        "status": "success",
        "dataset_id": dataset_id,
        "name": dataset_name,
        "domain_type": resolved_domain,
        "storage_path": storage_path,
        "canonical_csv_path": canonical_csv_path,
        "canonical_xlsx_path": canonical_xlsx_path,
        "row_count": row_count,
        "file_size_bytes": file_size_bytes,
        "columns_count": len(columns),
        "columns": columns,
        "applied_mappings": applied_mappings,
        "extracted_metadata": extracted_meta,
        "quality_score": quality_score,
        "quality_status": quality_status,
        "validation_notes": validation_notes,
        "dataset_record": record,
        "preview": preview_df.to_dict(orient="records")
    }
