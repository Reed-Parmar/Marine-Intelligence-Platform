"""
eDNA Schemas.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class EDNASampleResponse(BaseModel):
    id: str
    dataset_id: Optional[str] = None
    sample_code: Optional[str] = None
    latitude: float
    longitude: float
    depth: Optional[float] = None
    collected_at: Optional[str] = None
    sequencing_platform: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EDNADetectionResponse(BaseModel):
    id: str
    sample_id: str
    species_id: Optional[str] = None
    scientific_name: Optional[str] = None
    read_count: Optional[int] = None
    confidence_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
