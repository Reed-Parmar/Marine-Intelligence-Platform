"""
Analysis schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnalysisJobResponse(BaseModel):
    id: str
    job_type: str
    status: str
    parameters: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class CorrelationAnalysisRequest(BaseModel):
    variable_x: str
    variable_y: str
    domain_x: str = "oceanography"
    domain_y: str = "fisheries"
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class CorrelationAnalysisResponse(BaseModel):
    variable_x: str
    variable_y: str
    correlation_coefficient: Optional[float] = None
    sample_size: int = 0
    p_value: Optional[float] = None
    data_points: List[Dict[str, Any]] = Field(default_factory=list)
