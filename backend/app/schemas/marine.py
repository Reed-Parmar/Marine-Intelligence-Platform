"""
Unified Marine Cross-Domain Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MarineObservationItem(BaseModel):
    id: str
    domain: str  # oceanography, fisheries, biodiversity
    dataset_id: Optional[str] = None
    latitude: float
    longitude: float
    depth: Optional[float] = None
    time: Optional[str] = None
    species_id: Optional[str] = None
    species_name: Optional[str] = None
    measurements: Dict[str, Any] = Field(default_factory=dict)


class MarineSummaryResponse(BaseModel):
    total_datasets: int
    oceanography_count: int
    fisheries_count: int
    biodiversity_count: int
    total_species: int


class MarineQueryRequest(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None
    bbox: Optional[List[float]] = None  # [min_lon, min_lat, max_lon, max_lat]
    depth_min: Optional[float] = None
    depth_max: Optional[float] = None
    species_id: Optional[str] = None
    domain: Optional[str] = None
    dataset_id: Optional[str] = None
    variable: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
