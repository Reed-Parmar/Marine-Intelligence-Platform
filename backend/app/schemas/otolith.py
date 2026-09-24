"""
Otolith Schemas.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class OtolithSampleResponse(BaseModel):
    id: str
    dataset_id: Optional[str] = None
    fish_specimen_id: Optional[str] = None
    image_storage_path: Optional[str] = None
    fish_length_cm: Optional[float] = None
    fish_weight_g: Optional[float] = None
    estimated_age_years: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class OtolithAnalysisResponse(BaseModel):
    analysis_id: str
    sample_id: str
    status: str
    estimated_age_years: Optional[float] = None
    confidence_score: Optional[float] = None
    confidence_level: Optional[str] = None
    annuli_count: Optional[int] = None
    scientific_name: Optional[str] = None
    morphological_features: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
