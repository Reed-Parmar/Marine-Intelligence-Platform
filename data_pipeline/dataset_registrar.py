import uuid
from typing import Dict, Any, Optional
from .file_handler import get_supabase_client

def register_dataset(
    name: str,
    storage_path: str,
    schema: Dict[str, str],
    format_type: str,
    project_id: Optional[str] = None,
    created_by: Optional[str] = None,
    status: str = "pending"
) -> Dict[str, Any]:
    """
    Registers a new dataset in the public.datasets table.
    """
    supabase = get_supabase_client()
    
    payload = {
        "title": name,  # Assuming 'title' or 'name' based on common conventions. Adjust if schema differs.
        "description": f"Uploaded {format_type} file",
        "storage_path": storage_path,
        "format": format_type,
        "processing_status": status,
        # "schema_metadata": schema, # Depending on if the table has a jsonb column for this
    }
    
    if project_id:
        payload["project_id"] = project_id
    if created_by:
        payload["created_by"] = created_by

    # Insert into database
    # Note: RLS might block this if not using service_role or authenticated user
    res = supabase.table("datasets").insert(payload).execute()
    
    return res.data[0] if res.data else None
