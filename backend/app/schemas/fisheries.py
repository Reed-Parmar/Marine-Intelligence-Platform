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
