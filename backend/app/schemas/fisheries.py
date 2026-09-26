"""
Fisheries catch observations, summary, and trend schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FisheriesObservationResponse(BaseModel):
    id: str
    dataset_id: Optional[str] = None
    species_id: Optional[str] = None
    scientific_name: Optional[str] = None
    common_name: Optional[str] = None
    latitude: float
    longitude: float
    recorded_at: Optional[str] = None
    catch_weight_kg: Optional[float] = None
    effort_hours: Optional[float] = None
    gear_type: Optional[str] = None
    fishing_zone: Optional[str] = None
    vessel_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FisheriesSummaryResponse(BaseModel):
    total_records: int
    total_catch_kg: Optional[float] = None
    avg_catch_kg: Optional[float] = None
    total_effort_hours: Optional[float] = None
    distinct_species_count: int = 0
    distinct_zones_count: int = 0


class FisheriesTrendItem(BaseModel):
    time_bucket: str
    record_count: int
    total_catch_kg: Optional[float] = None
    avg_catch_kg: Optional[float] = None
    total_effort_hours: Optional[float] = None


class FisheriesTrendResponse(BaseModel):
    trends: List[FisheriesTrendItem]


class FisheriesCatchRequest(BaseModel):
    """
    Operational stratum parameters for predicting commercial marine fisheries catch (Phase 14.3 V1).
    Supports standard capitalized and lowercase parameter names.
    """
    Fleet: str = Field(..., description="Fishing vessel flag state (e.g. EUESP, EUFRA, SYC, MDV, JPN)", json_schema_extra={"example": "EUESP"})
    Gear: str = Field(..., description="Fishing gear code (e.g. PS, BB, LL)", json_schema_extra={"example": "PS"})
    Effort: float = Field(..., ge=0.0, description="Fishing effort expended (must be non-negative)", json_schema_extra={"example": 45.0})
    EffortUnits: str = Field(..., description="Unit of effort (e.g. FHOURS, FDAYS, SETS, TRIPS)", json_schema_extra={"example": "FHOURS"})
    Month: int = Field(..., ge=1, le=12, description="Month of fishing operation (1-12)", json_schema_extra={"example": 8})
    Year: int = Field(..., ge=1970, le=2035, description="Year of fishing operation", json_schema_extra={"example": 2024})
    Latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90 to +90)", json_schema_extra={"example": 2.5})
    Longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180 to +180)", json_schema_extra={"example": 55.5})
    SpatialResolution: Optional[float] = Field(1.0, description="Spatial grid resolution in degrees (default 1.0)", json_schema_extra={"example": 1.0})


class CatchPredictionResponse(BaseModel):
    """
    Standardized response for continuous fisheries catch prediction.
    """
    predicted_catch: float = Field(..., description="Predicted catch in Metric Tons (MT)", json_schema_extra={"example": 108.83})
    predicted_catch_mt: float = Field(..., description="Predicted catch in Metric Tons (MT)", json_schema_extra={"example": 108.83})
    unit: str = Field("Metric Tons (MT)", description="Measurement unit of catch")
    target_variable: str = Field("TotalCatchMT", description="Predicted ML target variable")
    model: str = Field(..., description="Model architecture", json_schema_extra={"example": "XGBoost Regressor (Tuned)"})
    model_version: str = Field(..., description="Model version", json_schema_extra={"example": "1.0.0"})
    disclaimer: str = Field(
        "Predicted catch is an estimated expectation based on historical IOTC surface fisheries operational strata and not a guaranteed actual harvest.",
        description="Scientific decision support disclaimer"
    )
    input_summary: Dict[str, Any] = Field(..., description="Normalized input operational stratum and derived features")


class BatchCatchRequest(BaseModel):
    items: List[FisheriesCatchRequest] = Field(..., description="List of fisheries catch prediction operational strata")


class BatchCatchResponse(BaseModel):
    total_records: int
    predictions: List[CatchPredictionResponse]


class FisheriesModelInfoResponse(BaseModel):
    metadata: Dict[str, Any]
    feature_schema: Dict[str, Any]

