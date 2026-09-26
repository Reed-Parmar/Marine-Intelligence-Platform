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


class EnvironmentalAnomalyDetectRequest(BaseModel):
    """Payload for on-demand Environmental Anomaly Detection V2."""
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    sst: Optional[float] = Field(None, description="Observed Sea Surface Temperature in Celsius")
    timestamp: Optional[str] = Field(None, description="ISO timestamp or date string (e.g. '2025-06-01')")


class AnomalyContributingFeature(BaseModel):
    feature: str
    value: Optional[float] = None
    importanceWeight: float = 0.5
    impactDirection: str = "positive"
    weight: Optional[float] = None
    impact: Optional[str] = None


class EnvironmentalAnomalyItem(BaseModel):
    """Output schema representing an evaluated environmental anomaly."""
    id: str
    region: str
    latitude: float
    longitude: float
    detectionDate: str
    timestamp: Optional[str] = None
    anomalyType: str
    anomaly_type: Optional[str] = None
    severity: str
    anomalyScore: float  # 0 to 100
    anomaly_score: Optional[float] = None
    is_anomaly: bool = True
    confidenceScore: float = 0.95
    baselineExpectedValue: str
    sst_baseline_celsius: Optional[float] = None
    observedCurrentValue: str
    sst_observed_celsius: Optional[float] = None
    sst_anomaly_celsius: Optional[float] = None
    sst_anomaly: Optional[float] = None
    warm_cold_direction: str = "neutral"
    in_arabian_sea: bool = True
    subbasin: str = "Arabian Sea (Strict IHO S-23)"
    contributingFeatures: List[AnomalyContributingFeature] = Field(default_factory=list)
    contributing_features: Optional[List[Dict[str, Any]]] = None
    mitigationAdvice: str = ""
    mitigation_advice: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EnvironmentalAnomalyModelInfo(BaseModel):
    """Metadata response for MEAD-V2 model."""
    model_name: str
    model_version: str
    algorithm: str
    dataset_name: str
    features_used: List[str]
    sample_size: Dict[str, Any]
    study_region: Dict[str, Any]
    test_results_2025: Dict[str, Any]
    unsupervised_note: str

