"""
Pydantic Schemas for Seasonal Species Distribution Shift API.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import math


class DistributionShiftPredictionRequest(BaseModel):
    """Request payload for predicting seasonal species distribution shifts."""

    species_id: str = Field(
        ...,
        description="Scientific name or recognized common name of the marine species (e.g., 'Sardinella longiceps', 'Indian Oil Sardine').",
        examples=["Sardinella longiceps"],
    )
    current_sector: str = Field(
        ...,
        description="Source canonical ecological sector in the Arabian Sea.",
        examples=["Malabar Upwelling Shelf"],
    )
    latitude: float = Field(
        ...,
        ge=6.0,
        le=24.0,
        description="Current latitude coordinate within Arabian Sea bounds (6.0°N to 24.0°N).",
        examples=[10.5],
    )
    longitude: float = Field(
        ...,
        ge=65.0,
        le=78.5,
        description="Current longitude coordinate within Arabian Sea bounds (65.0°E to 78.5°E).",
        examples=[75.5],
    )
    month: int = Field(
        ...,
        ge=1,
        le=12,
        description="Current observation month (1 for Jan to 12 for Dec).",
        examples=[4],
    )
    forecast_horizon_months: int = Field(
        default=2,
        ge=1,
        le=11,
        description="Forecast forward horizon in months (1 to 11 months, default 2).",
        examples=[2],
    )
    mean_depth_meters: Optional[float] = Field(
        default=None,
        description="Local seafloor bathymetric depth in meters (optional, preserved as null if unobserved).",
        examples=[35.0],
    )
    sst_celsius: Optional[float] = Field(
        default=None,
        description="Sea Surface Temperature in °C (optional CTD sensor value).",
        examples=[29.5],
    )
    salinity_psu: Optional[float] = Field(
        default=None,
        description="Practical Salinity in PSU (optional CTD sensor value).",
        examples=[35.2],
    )
    dissolved_oxygen_mgl: Optional[float] = Field(
        default=None,
        description="Dissolved Oxygen concentration in mg/L (optional CTD sensor value).",
        examples=[4.8],
    )
    chlorophyll_mg_m3: Optional[float] = Field(
        default=None,
        description="Chlorophyll-a concentration in mg/m³ (optional CTD sensor value).",
        examples=[1.5],
    )

    @field_validator("latitude", "longitude", "mean_depth_meters", "sst_celsius", "salinity_psu", "dissolved_oxygen_mgl", "chlorophyll_mg_m3")
    @classmethod
    def validate_finite_numbers(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not math.isfinite(v):
            raise ValueError("Numeric inputs must be valid finite numbers.")
        return v


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class SeasonInfo(BaseModel):
    season_code: int = Field(..., description="1: Pre-Monsoon (Feb-May), 2: SW Monsoon (Jun-Sep), 3: Post-Monsoon (Oct-Jan)")
    season_name: str


class ForecastInfo(BaseModel):
    source_month: int
    target_month: int
    source_season: SeasonInfo
    target_season: SeasonInfo


class SectorPrediction(BaseModel):
    sector: str
    probability: float
    centroid: Optional[List[float]] = None


class EnvironmentalInputs(BaseModel):
    sst_celsius: Optional[float] = None
    salinity_psu: Optional[float] = None
    dissolved_oxygen_mgl: Optional[float] = None
    chlorophyll_mg_m3: Optional[float] = None
    mean_depth_meters: Optional[float] = None


class MarkovComparison(BaseModel):
    top_markov_sector: str
    markov_probability: float
    fallback_level: int
    fallback_description: str


class DistributionShiftPredictionResponse(BaseModel):
    """Response payload for seasonal species distribution shift prediction."""

    species: str
    prediction_type: str = "seasonal_distribution_shift"
    source_sector: str
    source_coordinates: Coordinates
    forecast_horizon_months: int
    forecast: ForecastInfo
    top_prediction: SectorPrediction
    top_3_predictions: List[SectorPrediction]
    probability_distribution: Dict[str, float]
    confidence_level: str = Field(..., description="'HIGH', 'MODERATE', or 'LOW'")
    confidence_tier: str = Field(..., description="Human-readable confidence description with calibration context")
    environmental_context_available: bool
    environmental_inputs: EnvironmentalInputs
    markov_baseline_comparison: MarkovComparison
    model_metadata: Dict[str, Any]
    limitations: List[str]
