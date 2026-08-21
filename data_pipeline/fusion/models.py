"""
Data models for Phase 5 — Data Fusion & Unified Marine Data.
Common representation for heterogeneous marine observations.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DomainType(str, Enum):
    """Marine science domains supported by the platform."""
    OCEANOGRAPHY = "oceanography"
    FISHERIES = "fisheries"
    BIODIVERSITY = "biodiversity"
    EDNA = "edna"


@dataclass
class MarineObservation:
    """
    Common representation for a single marine observation across any domain.

    This is NOT a replacement for domain-specific records — it is a unified
    query representation that allows heterogeneous observations to be compared
    and associated using common spatial, temporal, and domain dimensions.
    """
    # Identity
    id: Optional[str] = None
    dataset_id: Optional[str] = None
    domain: Optional[str] = None  # DomainType value

    # Observation reference
    observation_id: Optional[str] = None  # Source record ID
    station_id: Optional[str] = None
    sample_id: Optional[str] = None

    # Spatial
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Temporal
    observation_time: Optional[str] = None  # ISO-8601 string

    # Depth
    depth: Optional[float] = None

    # Species (where applicable)
    species_id: Optional[str] = None
    species_name: Optional[str] = None

    # Measurement
    variable: Optional[str] = None  # e.g. 'temperature', 'catch_weight_kg', 'individual_count'
    value: Optional[float] = None
    unit: Optional[str] = None

    # Provenance
    source_table: Optional[str] = None  # Original database table
    quality_status: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON/API response."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class UnifiedQueryParams:
    """
    Filter parameters for unified marine data queries.
    All filters are optional — omitting a filter means no constraint on that dimension.
    """
    # Domain filter
    dataset_id: Optional[str] = None
    domain: Optional[str] = None  # DomainType value or None for all domains

    # Species filter
    species: Optional[str] = None  # species name or ID

    # Temporal filter
    date_from: Optional[str] = None  # ISO-8601 date/datetime
    date_to: Optional[str] = None    # ISO-8601 date/datetime

    # Depth filter
    depth_min: Optional[float] = None
    depth_max: Optional[float] = None

    # Spatial filter — point + radius
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None  # Search radius in km

    # Spatial filter — bounding box [west, south, east, north]
    bbox: Optional[List[float]] = None

    # Variable filter
    variable: Optional[str] = None

    # Pagination
    limit: int = 1000
    offset: int = 0


@dataclass
class CrossDomainAssociation:
    """
    Represents associated observations across different domains.

    IMPORTANT: Spatial/temporal proximity does NOT imply causation.
    These are 'associated observations/context', not proof of relationships.
    """
    # The anchor observation
    anchor: MarineObservation = field(default_factory=MarineObservation)

    # Associated observations from other domains
    associated: List[MarineObservation] = field(default_factory=list)

    # Matching parameters (explicit, not hidden)
    spatial_radius_km: float = 50.0
    temporal_window_hours: float = 72.0
    depth_tolerance_m: Optional[float] = 50.0

    # Metadata
    association_note: str = (
        "Associated observations found within the specified spatial/temporal/depth window. "
        "Proximity does not imply causation or scientific correlation."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anchor": self.anchor.to_dict(),
            "associated": [obs.to_dict() for obs in self.associated],
            "matching_parameters": {
                "spatial_radius_km": self.spatial_radius_km,
                "temporal_window_hours": self.temporal_window_hours,
                "depth_tolerance_m": self.depth_tolerance_m,
            },
            "association_note": self.association_note,
            "associated_count": len(self.associated),
        }


@dataclass
class UnifiedSummary:
    """
    Summary statistics for the unified marine data layer.
    Used by the dashboard / command center.
    """
    total_observations: int = 0
    total_datasets: int = 0
    domains: List[str] = field(default_factory=list)
    species_count: int = 0
    species_names: List[str] = field(default_factory=list)

    # Geographic bounds
    lat_min: Optional[float] = None
    lat_max: Optional[float] = None
    lon_min: Optional[float] = None
    lon_max: Optional[float] = None

    # Temporal range
    time_min: Optional[str] = None
    time_max: Optional[str] = None

    # Available variables
    variables: List[str] = field(default_factory=list)

    # Per-domain counts
    domain_counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
