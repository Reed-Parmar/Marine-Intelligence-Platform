"""
Phase 6 — Main Scientific Analysis Service Orchestrator.
Provides a unified, clean interface for generating oceanographic, fisheries,
biodiversity, spatial, temporal, correlation, and ecosystem relationship analyses.
"""

from typing import Any, Dict, List, Optional, Tuple

from data_pipeline.analysis.biodiversity import (
    analyze_species_distribution,
    calculate_biodiversity_indicators,
)
from data_pipeline.analysis.correlation import calculate_cross_domain_correlation
from data_pipeline.analysis.ecosystem import analyze_ecosystem_relationship
from data_pipeline.analysis.fisheries import analyze_fisheries_trends
from data_pipeline.analysis.models import (
    BiodiversityResult,
    CorrelationResult,
    EcosystemRelationshipResult,
    FisheriesTrendResult,
    OceanTrendResult,
    SpatialAnalysisResult,
    SpeciesDistributionResult,
    TemporalAnalysisResult,
)
from data_pipeline.analysis.ocean import analyze_ocean_trends
from data_pipeline.analysis.spatial import analyze_spatial_distribution
from data_pipeline.analysis.temporal import analyze_temporal_dynamics
from data_pipeline.fusion.models import MarineObservation, UnifiedQueryParams


class ScientificAnalysisService:
    """
    Main entrypoint for Phase 6 Scientific Analysis workflows.
    Consumes Phase 5 unified marine observations and produces deterministic scientific results.
    """

    @staticmethod
    def analyze_ocean_trends(
        observations: Optional[List[MarineObservation]] = None,
        variable: str = "temperature",
        time_aggregation: str = "monthly",
        params: Optional[UnifiedQueryParams] = None,
    ) -> OceanTrendResult:
        """Computes statistical time-series trends for an ocean physical/chemical variable."""
        return analyze_ocean_trends(
            observations=observations,
            variable=variable,
            time_aggregation=time_aggregation,
            params=params,
        )

    @staticmethod
    def analyze_fisheries_trends(
        observations: Optional[List[MarineObservation]] = None,
        time_aggregation: str = "monthly",
        params: Optional[UnifiedQueryParams] = None,
    ) -> FisheriesTrendResult:
        """Computes fisheries catch statistics, species allocations, and landing trends."""
        return analyze_fisheries_trends(
            observations=observations,
            time_aggregation=time_aggregation,
            params=params,
        )

    @staticmethod
    def analyze_species_distribution(
        observations: Optional[List[MarineObservation]] = None,
        params: Optional[UnifiedQueryParams] = None,
    ) -> SpeciesDistributionResult:
        """Computes spatial points, geographic centroids, and depth ranges for species."""
        return analyze_species_distribution(
            observations=observations,
            params=params,
        )

    @staticmethod
    def calculate_biodiversity(
        observations: Optional[List[MarineObservation]] = None,
        sample_definition: str = "regional_community",
        params: Optional[UnifiedQueryParams] = None,
    ) -> BiodiversityResult:
        """Computes ecological diversity metrics: Species Richness, Shannon H', Simpson D, Pielou J'."""
        return calculate_biodiversity_indicators(
            observations=observations,
            sample_definition=sample_definition,
            params=params,
        )

    @staticmethod
    def analyze_spatial(
        observations: Optional[List[MarineObservation]] = None,
        grid_size_deg: float = 1.0,
        bbox: Optional[List[float]] = None,
        center_coords: Optional[Tuple[float, float]] = None,
        radius_km: Optional[float] = None,
        params: Optional[UnifiedQueryParams] = None,
    ) -> SpatialAnalysisResult:
        """Performs spatial grid cell binning, bounding-box queries, and regional comparisons."""
        return analyze_spatial_distribution(
            observations=observations,
            grid_size_deg=grid_size_deg,
            bbox=bbox,
            center_coords=center_coords,
            radius_km=radius_km,
            params=params,
        )

    @staticmethod
    def analyze_temporal(
        observations: Optional[List[MarineObservation]] = None,
        period_type: str = "monthly",
        params: Optional[UnifiedQueryParams] = None,
    ) -> TemporalAnalysisResult:
        """Performs multi-scale temporal aggregation (daily, monthly, yearly, seasonal)."""
        return analyze_temporal_dynamics(
            observations=observations,
            period_type=period_type,
            params=params,
        )

    @staticmethod
    def calculate_correlation(
        domain_x: str,
        variable_x: str,
        domain_y: str,
        variable_y: str,
        observations: Optional[List[MarineObservation]] = None,
        method: str = "pearson",
        spatial_radius_km: float = 50.0,
        temporal_window_hours: float = 72.0,
        depth_tolerance_m: Optional[float] = 50.0,
        paired_data_override: Optional[List[Tuple[float, float]]] = None,
    ) -> CorrelationResult:
        """Calculates Pearson or Spearman correlation between paired cross-domain variables."""
        return calculate_cross_domain_correlation(
            domain_x=domain_x,
            variable_x=variable_x,
            domain_y=domain_y,
            variable_y=variable_y,
            observations=observations,
            method=method,
            spatial_radius_km=spatial_radius_km,
            temporal_window_hours=temporal_window_hours,
            depth_tolerance_m=depth_tolerance_m,
            paired_data_override=paired_data_override,
        )

    @staticmethod
    def analyze_ecosystem_relationship(
        theme_key: str = "temperature_species",
        observations: Optional[List[MarineObservation]] = None,
        spatial_radius_km: float = 50.0,
        temporal_window_hours: float = 72.0,
        depth_tolerance_m: Optional[float] = 50.0,
        params: Optional[UnifiedQueryParams] = None,
    ) -> EcosystemRelationshipResult:
        """Synthesizes an integrated multi-domain ecosystem relationship report."""
        return analyze_ecosystem_relationship(
            theme_key=theme_key,
            observations=observations,
            spatial_radius_km=spatial_radius_km,
            temporal_window_hours=temporal_window_hours,
            depth_tolerance_m=depth_tolerance_m,
            params=params,
        )
