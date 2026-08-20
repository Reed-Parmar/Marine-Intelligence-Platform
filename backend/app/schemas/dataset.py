"""
Dataset schemas for registration, metadata, quality scores, and provenance.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DatasetResponse(BaseModel):
    id: str
    project_id: Optional[str] = None
    data_source_id: Optional[str] = None
    name: str
    domain_type: str
    storage_file_path: Optional[str] = None
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    row_count: Optional[int] = None
    uploaded_by: Optional[str] = None
    status: str = "uploaded"
    quality_status: str = "pending"
    quality_score: Optional[float] = None
    validation_notes: Optional[str] = None
    provenance_metadata: Optional[Dict[str, Any]] = None
    project_name: Optional[str] = None
    source_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DatasetCreateRequest(BaseModel):
    name: str
    domain_type: str = "oceanography"
    project_id: Optional[str] = None
    data_source_id: Optional[str] = None
    storage_file_path: Optional[str] = None
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    row_count: Optional[int] = None
    provenance_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DatasetUpdateRequest(BaseModel):
    name: Optional[str] = None
    domain_type: Optional[str] = None
    quality_status: Optional[str] = None
    quality_score: Optional[float] = None
    validation_notes: Optional[str] = None
    provenance_metadata: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class DatasetQualityResponse(BaseModel):
    dataset_id: str
    quality_score: Optional[float] = None
    quality_status: str = "pending"
    validation_notes: Optional[str] = None
    issues_summary: Optional[Dict[str, Any]] = None
    deductions: Optional[Dict[str, Any]] = None


class DatasetProvenanceResponse(BaseModel):
    dataset_id: str
    provenance_metadata: Optional[Dict[str, Any]] = None
    storage_file_path: Optional[str] = None
    uploaded_by: Optional[str] = None
    created_at: Optional[str] = None
