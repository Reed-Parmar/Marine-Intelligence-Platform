import os
import uuid
from typing import Optional
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """
    Initializes and returns a Supabase Client using environment variables.
    Prefers SUPABASE_SERVICE_ROLE_KEY if available, falling back to SUPABASE_ANON_KEY.
    """
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables in environment.")
    return create_client(url, key)

def upload_to_storage(
    file_path: str, 
    bucket_name: str = "marine-files", 
    dataset_id: Optional[str] = None
) -> str:
    """
    Uploads a local file to a Supabase Storage bucket following the standard path convention:
    datasets/{dataset_id}/{filename} or datasets/uploads/{filename}.
    Returns the storage path upon success.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found for storage upload: {file_path}")
        
    supabase = get_supabase_client()
    
    file_name = os.path.basename(file_path)
    if dataset_id:
        storage_path = f"datasets/{dataset_id}/{file_name}"
    else:
        storage_path = f"datasets/uploads/{file_name}"
    
    with open(file_path, "rb") as f:
        supabase.storage.from_(bucket_name).upload(
            file=f,
            path=storage_path,
            file_options={"cache-control": "3600", "upsert": "true"}
        )
    
    return storage_path
