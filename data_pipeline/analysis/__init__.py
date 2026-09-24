"""
Phase 6 — Scientific Analysis Package.
Provides deterministic, reproducible scientific analysis services:
- Oceanographic trend analysis (temperature, salinity, oxygen, chlorophyll, pH, turbidity)
- Fisheries trend analysis (catch weights, species distributions, gear allocations)
- Species distribution analysis (spatial points, centroids, depth ranges)
- Biodiversity indicators (Species Richness S, Shannon H', Gini-Simpson D, Pielou Evenness J')
- Spatial analysis & regular grid cell binning
- Temporal multi-scale dynamics (daily, monthly, yearly, seasonal)
- Cross-domain statistical correlation (Pearson r, Spearman rho, p-values, paired co-occurrences)
- Integrated ecosystem relationship synthesis
"""

from data_pipeline.analysis.biodiversity import (
    analyze_species_distribution,
    calculate_biodiversity_indicators,
)
from data_pipeline.analysis.correlation import (
    calculate_cross_domain_correlation,
    pair_cross_domain_observations,
)
from data_pipeline.analysis.ecosystem import (
    ECOSYSTEM_THEMES,
    analyze_ecosystem_relationship,
)
from data_pipeline.analysis.fisheries import analyze_fisheries_trends
from data_pipeline.analysis.models import (
    BiodiversityResult,
    CorrelationResult,
    EcosystemRelationshipResult,
    FisheriesTrendResult,
    OceanTrendResult,
    SpatialAnalysisResult,
    SpatialGridCell,
    SpeciesDistributionResult,
    TemporalAnalysisResult,
    TemporalBucket,
    TrendDataPoint,
)
from data_pipeline.analysis.ocean import analyze_ocean_trends
from data_pipeline.analysis.service import ScientificAnalysisService
from data_pipeline.analysis.spatial import analyze_spatial_distribution
from data_pipeline.analysis.temporal import analyze_temporal_dynamics

__all__ = [
    # Main Service
    "ScientificAnalysisService",
    # Functions
    "analyze_ocean_trends",
    "analyze_fisheries_trends",
    "analyze_species_distribution",
    "calculate_biodiversity_indicators",
    "analyze_spatial_distribution",
    "analyze_temporal_dynamics",
    "calculate_cross_domain_correlation",
    "pair_cross_domain_observations",
    "analyze_ecosystem_relationship",
    # Constants
    "ECOSYSTEM_THEMES",
    # Models
    "TrendDataPoint",
    "OceanTrendResult",
    "FisheriesTrendResult",
    "SpeciesDistributionResult",
    "BiodiversityResult",
    "SpatialGridCell",
    "SpatialAnalysisResult",
    "TemporalBucket",
    "TemporalAnalysisResult",
    "CorrelationResult",
    "EcosystemRelationshipResult",
]
