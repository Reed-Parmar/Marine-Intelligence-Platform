"""
Upload schemas for dataset staging, preview, and Phase 3 processing.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    upload_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    storage_path: str
    status: str = "uploaded"  # uploaded, parsing, standardized, finalized, failed
    detected_format: Optional[str] = None
    created_at: str


class UploadPreviewResponse(BaseModel):
    upload_id: str
    filename: str
    detected_format: str
    total_preview_rows: int
    headers: List[str]
    sample_rows: List[Dict[str, Any]]


class UploadProcessRequest(BaseModel):
    dataset_name: Optional[str] = None
    domain_type: str = "oceanography"
    project_id: Optional[str] = None
    unit_hints: Optional[Dict[str, str]] = Field(default_factory=dict)
    column_mapping: Optional[Dict[str, str]] = Field(default_factory=dict)


class UploadProcessResponse(BaseModel):
    upload_id: str
    dataset_id: str
    status: str
    quality_score: Optional[float] = None
    quality_status: Optional[str] = None
    records_processed: int
    message: str
