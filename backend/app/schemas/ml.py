"""
ML Model Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MLModelResponse(BaseModel):
    model_id: str
    name: str
    version: str
    task_type: str
    target_variable: Optional[str] = None
    input_features: List[str] = Field(default_factory=list)
    status: str = "ready"
    metrics: Optional[Dict[str, Any]] = None


class MLPredictRequest(BaseModel):
    model_id: str
    features: Dict[str, Any]


class MLPredictResponse(BaseModel):
    prediction_id: str
    model_id: str
    prediction: Any
    confidence_interval: Optional[List[float]] = None
    created_at: str
