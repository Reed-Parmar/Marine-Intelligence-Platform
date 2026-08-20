import os
import uuid
from typing import Dict, Any, Optional
from .format_detector import detect_format_and_preview
from .file_handler import upload_to_storage
from .dataset_registrar import register_dataset

DEFAULT_PROJECT_ID = "c1d2e3f4-0000-0000-0000-000000000001"

def process_upload(
    file_path: str, 
    dataset_name: Optional[str] = None, 
    project_id: Optional[str] = DEFAULT_PROJECT_ID,
    domain_type: Optional[str] = None,
    uploaded_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main orchestration function for the Data Ingestion Engine.
    1. Validates file existence and detects format, schema, row count, and domain.
    2. Uploads raw file to Supabase Storage at datasets/{dataset_id}/{filename}.
    3. Registers dataset metadata in Supabase PostgreSQL public.datasets table.
    """
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"File not found: {file_path}"}
    
    filename = os.path.basename(file_path)
    dataset_name = dataset_name or f"CMLRE: {filename}"
    dataset_id = str(uuid.uuid4())
    
    print(f"\n[Ingestion] Starting ingestion for: {filename} (ID: {dataset_id})")
    
    # 1. Format detection, schema extraction, and domain classification
    detection_result = detect_format_and_preview(file_path)
    if detection_result.get("error"):
        return {
            "status": "error", 
            "message": f"Format detection failed: {detection_result['error']}"
        }
        
    resolved_domain = domain_type or detection_result["domain_type"]
    row_count = detection_result["row_count"]
    file_size_bytes = detection_result["file_size_bytes"]
    columns = detection_result.get("columns", [])
    
    print(f" -> Format: {detection_result['format']} | Domain: {resolved_domain} | Rows: {row_count:,} | Size: {file_size_bytes:,} bytes")
    
    # 2. Upload to Supabase Storage
    try:
        storage_path = upload_to_storage(file_path, dataset_id=dataset_id)
        print(f" -> Uploaded to Supabase Storage: {storage_path}")
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Storage upload failed: {str(e)}"
        }
        
    # 3. Register Dataset in Supabase PostgreSQL
    try:
        provenance = {
            "source_filename": filename,
            "ingestion_method": "cmlre_data_pipeline",
            "column_count": len(columns),
            "columns": columns[:20]  # Store up to 20 column headers in provenance
        }
        
        record = register_dataset(
            name=dataset_name,
            storage_path=storage_path,
            schema=detection_result["schema"],
            format_type=detection_result["format"],
            domain_type=resolved_domain,
            file_size_bytes=file_size_bytes,
            row_count=row_count,
            dataset_id=dataset_id,
            project_id=project_id,
            uploaded_by=uploaded_by,
            status="uploaded",
            quality_status="pending",
            provenance_metadata=provenance
        )
        print(f" -> Registered in PostgreSQL (datasets.id: {dataset_id})")
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Database registration failed: {str(e)}"
        }
        
    return {
        "status": "success",
        "dataset_id": dataset_id,
        "name": dataset_name,
        "domain_type": resolved_domain,
        "storage_path": storage_path,
        "row_count": row_count,
        "file_size_bytes": file_size_bytes,
        "columns_count": len(columns),
        "dataset_record": record,
        "preview": detection_result["preview"]
    }
