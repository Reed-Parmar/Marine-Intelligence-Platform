"""
Phase 2: Storage & Database Integration Layer.
Handles file uploads to Supabase Storage and dataset metadata registration.
"""

from data_pipeline.storage.dataset_registrar import register_dataset
from data_pipeline.storage.file_handler import (
    get_supabase_client,
    upload_to_storage,
)

__all__ = [
    "get_supabase_client",
    "upload_to_storage",
    "register_dataset",
]
