"""
Data Models for Species Seasonal Distribution Shift & Population-State Transitions.

CRITICAL SCIENTIFIC DISTINCTION:
These models represent Eulerian population-level spatial distributions and seasonal
range shifts derived from scientific survey occurrences and fisheries catch logs.
They DO NOT represent Lagrangian individual fish tracking or telemetry trajectories.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PopulationStateObservation:
    """
    Represents an aggregated species population state within a discrete 1° x 1°
    geographic grid cell and temporal window (month/season).
    """
    species_id: str
    scientific_name: str
    cell_id: str
    centroid_lat: float
    centroid_lon: float
    sector: str
    year: Optional[int]
    month: int
    season_code: int  # 1: Pre-Monsoon, 2: SW Monsoon, 3: Post-Monsoon
    season_name: str  # 'Pre-Monsoon', 'SW Monsoon', 'Post-Monsoon'
    
    # Observation volume (Explicitly observation count, NOT biomass)
    occurrence_count: int
    
    # Physical / Environmental context (None if unobserved; never 0.0)
    mean_depth_meters: Optional[float] = None
    sst_celsius: Optional[float] = None
    salinity_psu: Optional[float] = None
    dissolved_oxygen_mgl: Optional[float] = None
    chlorophyll_mg_m3: Optional[float] = None
    
    # Biological traits
    trophic_level: Optional[float] = None
    historical_occurrence_rate: float = 0.0
    
    # Provenance & Cross-domain metadata
    source_record_ids: List[str] = field(default_factory=list)
    dataset_ids: List[str] = field(default_factory=list)
    environmental_fusion_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SeasonalDistributionTransition:
    """
    Represents a scientifically valid population-level distribution shift from state t to state t+1.
    """
    species_id: str
    scientific_name: str
    
    # Source Population State (Time t)
    current_cell_id: str
    current_lat: float
    current_lon: float
    current_sector: str
    season_code: int  # 1: Pre-Monsoon, 2: SW Monsoon, 3: Post-Monsoon
    season_name: str
    month: int
    month_sin: float
    month_cos: float
    
    # Fused Environmental Features at Source State (None if missing, never 0.0)
    sst_celsius: Optional[float]
    salinity_psu: Optional[float]
    dissolved_oxygen_mgl: Optional[float]
    chlorophyll_mg_m3: Optional[float]
    mean_depth_meters: Optional[float]
    
    # Ecological & Population Context
    historical_occurrence_rate: float
    trophic_level: Optional[float]
    
    # Destination Population State (Time t+1)
    target_cell_id: str
    target_lat: float
    target_lon: float
    target_sector: str
    target_season_code: int
    target_season_name: str
    target_month: int
    
    # Displacement Metrics
    displacement_distance_km: float
    target_direction_deg: Optional[float]  # Azimuth bearing 0°–360° (None if stationary displacement=0)
    
    # Provenance & Verification
    source_record_ids: List[str] = field(default_factory=list)
    dataset_ids: List[str] = field(default_factory=list)
    environmental_fusion_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
