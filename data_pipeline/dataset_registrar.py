"""
Dataset Registrar for CMLRE Data Pipeline.
Registers dataset records and provenance into Supabase PostgreSQL public.datasets table.
"""

import logging
import uuid
from typing import Any, Dict, Optional
from .file_handler import get_supabase_client

logger = logging.getLogger(__name__)


def register_dataset(
    name: str,
    storage_path: str,
    schema: Dict[str, str],
    format_type: str,
    domain_type: str = "cross_domain",
    file_size_bytes: Optional[int] = None,
    row_count: Optional[int] = None,
    description: Optional[str] = None,
    dataset_id: Optional[str] = None,
    project_id: Optional[str] = None,
    data_source_id: Optional[str] = None,
    uploaded_by: Optional[str] = None,
    status: str = "uploaded",
    quality_status: str = "pending",
    quality_score: Optional[float] = None,
    validation_notes: Optional[str] = None,
    provenance_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Registers a new dataset record in Supabase PostgreSQL public.datasets table.
    """
    record_id = dataset_id or str(uuid.uuid4())
    
    payload = {
        "id": record_id,
        "name": name,
        "description": description or f"Canonical {format_type.upper()} dataset for {domain_type} domain",
        "domain_type": domain_type,
        "storage_file_path": storage_path,
        "file_type": format_type,
        "file_size_bytes": file_size_bytes or 0,
        "row_count": row_count or 0,
        "schema_metadata": schema or {},
        "status": status,
        "quality_status": quality_status,
        "provenance_metadata": provenance_metadata or {}
    }
    
    if project_id:
        payload["project_id"] = project_id
    if data_source_id:
        payload["data_source_id"] = data_source_id
    if uploaded_by:
        payload["uploaded_by"] = uploaded_by
    if quality_score is not None:
        payload["quality_score"] = quality_score
    if validation_notes:
        payload["validation_notes"] = validation_notes

    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.table("datasets").insert(payload).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.warning(f"Database registration bypassed or failed: {e}. Returning payload.")

    return payload
