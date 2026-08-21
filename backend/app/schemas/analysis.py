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
    variable_x: Optional[str] = None
    variable_y: Optional[str] = None
    independentVariable: Optional[str] = None
    dependentVariable: Optional[str] = None
    domain_x: Optional[str] = None
    domain_y: Optional[str] = None
    method: str = "pearson"
    spatial_radius_km: float = Field(50.0, ge=0.0)
    temporal_window_hours: float = Field(72.0, ge=0.0)
    depth_tolerance_m: Optional[float] = Field(50.0, ge=0.0)
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class CorrelationAnalysisResponse(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    variable_x: str
    variable_y: str
    domain_x: Optional[str] = None
    domain_y: Optional[str] = None
    method: str = "pearson"
    correlation_coefficient: Optional[float] = None
    sample_size: int = 0
    p_value: Optional[float] = None
    interpretation: Optional[str] = None
    is_statistically_significant: bool = False
    disclaimer: Optional[str] = None
    data_points: List[Dict[str, Any]] = Field(default_factory=list)
    scatterPoints: Optional[List[Dict[str, Any]]] = None
    statistics: Optional[Dict[str, Any]] = None
    regressionLine: Optional[Dict[str, Any]] = None
    ecologicalInterpretation: Optional[str] = None
    provenance: Optional[Dict[str, Any]] = None
    warnings: List[str] = Field(default_factory=list)
