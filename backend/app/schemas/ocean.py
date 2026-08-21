"""
Oceanographic observation, summary, and trend schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OceanObservationResponse(BaseModel):
    id: str
    dataset_id: Optional[str] = None
    station_id: Optional[str] = None
    sample_id: Optional[str] = None
    latitude: float
    longitude: float
    depth: Optional[float] = None
    observed_at: Optional[str] = None
    temperature: Optional[float] = None
    salinity: Optional[float] = None
    dissolved_oxygen: Optional[float] = None
    chlorophyll: Optional[float] = None
    ph: Optional[float] = None
    pressure: Optional[float] = None
    turbidity: Optional[float] = None
    conductivity: Optional[float] = None
    quality_flag: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class OceanSummaryResponse(BaseModel):
    total_observations: int
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    avg_temperature: Optional[float] = None
    min_salinity: Optional[float] = None
    max_salinity: Optional[float] = None
    avg_salinity: Optional[float] = None
    min_dissolved_oxygen: Optional[float] = None
    max_dissolved_oxygen: Optional[float] = None
    avg_dissolved_oxygen: Optional[float] = None
    min_depth: Optional[float] = None
    max_depth: Optional[float] = None


class OceanTrendItem(BaseModel):
    time_bucket: str
    observation_count: int
    avg_temperature: Optional[float] = None
    avg_salinity: Optional[float] = None
    avg_dissolved_oxygen: Optional[float] = None
    avg_chlorophyll: Optional[float] = None


class OceanTrendResponse(BaseModel):
    variable: str
    trends: List[OceanTrendItem]
