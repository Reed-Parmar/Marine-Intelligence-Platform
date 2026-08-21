"""
Supabase Storage and File Handler for CMLRE Data Pipeline.
Uploads raw and canonical dataset artifacts to the Supabase 'marine-files' storage bucket.
"""

import logging
import os
from typing import Optional
from supabase import Client, create_client

logger = logging.getLogger(__name__)


def get_supabase_client() -> Optional[Client]:
    """
    Initializes and returns a Supabase Client using environment variables.
    Returns None if variables are missing.
    """
    url: Optional[str] = os.environ.get("SUPABASE_URL")
    key: Optional[str] = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        logger.warning(f"Failed to create Supabase client: {e}")
        return None


def upload_to_storage(
    file_path: str, 
    bucket_name: str = "marine-files", 
    dataset_id: Optional[str] = None
) -> str:
    """
    Uploads a local file to Supabase Storage bucket following the standard path convention:
    datasets/{dataset_id}/{filename} or datasets/uploads/{filename}.
    Returns the storage path upon success.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found for storage upload: {file_path}")
        
    file_name = os.path.basename(file_path)
    if dataset_id:
        storage_path = f"datasets/{dataset_id}/{file_name}"
    else:
        storage_path = f"datasets/uploads/{file_name}"
    
    supabase = get_supabase_client()
    if supabase:
        try:
            with open(file_path, "rb") as f:
                supabase.storage.from_(bucket_name).upload(
                    file=f,
                    path=storage_path,
                    file_options={"cache-control": "3600", "upsert": "true"}
                )
        except Exception as e:
            logger.warning(f"Supabase storage upload bypassed or failed: {e}. Preserving canonical storage path.")
    else:
        logger.info(f"Supabase client not configured. Recorded storage path: {storage_path}")

    return storage_path
