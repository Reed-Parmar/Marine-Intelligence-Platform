"""
Data models for Phase 6 — Scientific Analysis.
Typed dataclasses representing deterministic scientific analysis outputs
suitable for API responses, dashboard charts, and Phase 8 AI/ML consumption.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class TrendDataPoint:
    """A single time-aggregated statistical bucket in a trend analysis."""
    period: str                         # e.g. '2026-03', '2026-W11', '2026-03-15'
    mean: float
    min: float
    max: float
    std: Optional[float] = None
    count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OceanTrendResult:
    """Scientific trend analysis result for an oceanographic variable."""
    variable: str                       # e.g. 'temperature', 'salinity', 'dissolved_oxygen'
    unit: str                           # e.g. '°C', 'PSU', 'mg/L'
    time_aggregation: str               # 'daily', 'monthly', 'yearly', 'seasonal'
    time_series: List[TrendDataPoint] = field(default_factory=list)
    overall_mean: Optional[float] = None
    overall_min: Optional[float] = None
    overall_max: Optional[float] = None
    overall_std: Optional[float] = None
    trend_slope: Optional[float] = None # Linear regression slope (units / period)
    trend_direction: str = "stable"      # 'increasing', 'decreasing', 'stable', 'insufficient_data'
    data_points_count: int = 0
    date_range: Optional[Dict[str, str]] = None
    depth_range: Optional[Dict[str, float]] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["time_series"] = [p.to_dict() if hasattr(p, "to_dict") else p for p in self.time_series]
        return d


@dataclass
class FisheriesTrendResult:
    """Scientific trend analysis result for fisheries catch and fishing dynamics."""
    total_catch_kg: float = 0.0
    avg_catch_kg: float = 0.0
    min_catch_kg: float = 0.0
    max_catch_kg: float = 0.0
    records_count: int = 0
    species_breakdown: Dict[str, float] = field(default_factory=dict) # species -> catch_kg
    zone_breakdown: Dict[str, float] = field(default_factory=dict)    # zone -> catch_kg
    gear_breakdown: Dict[str, float] = field(default_factory=dict)    # gear -> catch_kg
    time_series: List[TrendDataPoint] = field(default_factory=list)
    has_fishing_effort_data: bool = False
    effort_notes: str = "Catch observations analyzed; distinct from active fishing effort."
    provenance: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["time_series"] = [p.to_dict() if hasattr(p, "to_dict") else p for p in self.time_series]
        return d


@dataclass
class SpeciesDistributionResult:
    """Geographic and taxonomic distribution of species occurrences."""
    total_occurrences: int = 0
    unique_species_count: int = 0
    species_summary: List[Dict[str, Any]] = field(default_factory=list) # [{name, count, lat_centroid, lon_centroid, depth_min, depth_max}]
    spatial_points: List[Dict[str, Any]] = field(default_factory=list)   # [{latitude, longitude, species_name, count, depth, time}]
    bounding_box: Optional[Dict[str, float]] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BiodiversityResult:
    """Calculated ecological biodiversity indices and sample community structure."""
    species_richness: int = 0           # S: total number of distinct species
    observation_count: int = 0          # N: total number of individual observations / counts
    shannon_index: Optional[float] = None  # H': Shannon-Wiener diversity index
    simpson_index: Optional[float] = None  # 1 - D: Gini-Simpson diversity index
    pielou_evenness: Optional[float] = None # J': Pielou's equitability index (H' / ln(S))
    species_abundances: Dict[str, float] = field(default_factory=dict)
    sample_definition: str = "aggregated_dataset"
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SpatialGridCell:
    """A spatial grid cell binning observations for regional comparison."""
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    center_lat: float
    center_lon: float
    observation_count: int = 0
    domain_counts: Dict[str, int] = field(default_factory=dict)
    species_count: int = 0
    species_richness: int = 0
    mean_values: Dict[str, float] = field(default_factory=dict) # variable -> mean_val

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SpatialAnalysisResult:
    """Spatial distribution and grid binning analysis across marine domains."""
    total_observations: int = 0
    bounding_box: Optional[Dict[str, float]] = None
    center_coords: Optional[Tuple[float, float]] = None
    radius_km: Optional[float] = None
    domain_distribution: Dict[str, int] = field(default_factory=dict)
    species_distribution: Dict[str, int] = field(default_factory=dict)
    grid_cells: List[SpatialGridCell] = field(default_factory=list)
    variable_spatial_stats: Dict[str, Dict[str, float]] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["grid_cells"] = [c.to_dict() if hasattr(c, "to_dict") else c for c in self.grid_cells]
        return d


@dataclass
class TemporalBucket:
    """Temporal time bucket aggregating observations and domain frequencies."""
    period: str
    total_count: int = 0
    domain_counts: Dict[str, int] = field(default_factory=dict)
    species_counts: Dict[str, int] = field(default_factory=dict)
    variable_means: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TemporalAnalysisResult:
    """Temporal dynamics and time-series aggregation."""
    period_type: str                    # 'daily', 'monthly', 'yearly', 'seasonal'
    total_observations: int = 0
    time_series: List[TemporalBucket] = field(default_factory=list)
    seasonal_summary: Dict[str, Dict[str, Any]] = field(default_factory=dict) # season -> {count, domains, variable_means}
    time_min: Optional[str] = None
    time_max: Optional[str] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["time_series"] = [b.to_dict() if hasattr(b, "to_dict") else b for b in self.time_series]
        return d


@dataclass
class CorrelationResult:
    """Statistical correlation between two marine variables across or within domains."""
    variable_x: str
    variable_y: str
    domain_x: str
    domain_y: str
    method: str                         # 'pearson' or 'spearman'
    correlation_coefficient: Optional[float] = None # r or rho [-1.0, 1.0]
    p_value: Optional[float] = None
    sample_size: int = 0
    interpretation: str = "insufficient_data" # 'strong positive association', 'moderate negative association', etc.
    is_statistically_significant: bool = False
    disclaimer: str = (
        "Correlation represents empirical co-variation and does NOT imply biological or physical causation."
    )
    paired_data: List[Dict[str, Any]] = field(default_factory=list) # sample points [{x, y, lat, lon, time}]
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EcosystemRelationshipResult:
    """High-level multi-domain ecosystem synthesis combining environmental and biotic states."""
    theme: str                          # e.g. 'Temperature ↔ Species Richness'
    summary_narrative: str
    environmental_variable: str
    biological_indicator: str
    correlation: Optional[CorrelationResult] = None
    environmental_context: Dict[str, Any] = field(default_factory=dict)
    biological_context: Dict[str, Any] = field(default_factory=dict)
    co_occurrence_findings: List[str] = field(default_factory=list)
    limitation_note: str = (
        "Ecosystem relationships reflect observed spatial-temporal co-occurrences in the unified data layer. "
        "Further ecological modeling is required to infer functional mechanisms."
    )
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.correlation and hasattr(self.correlation, "to_dict"):
            d["correlation"] = self.correlation.to_dict()
        return d
