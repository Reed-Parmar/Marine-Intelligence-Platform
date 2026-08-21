"""
Phase 6 — Ecosystem Relationships Synthesis.
Combines physical, chemical, biological, and fisheries observations into
interpretable, multi-domain ecosystem synthesis reports for scientific decision-making.
"""

from typing import Any, Dict, List, Optional

from data_pipeline.analysis.biodiversity import calculate_biodiversity_indicators
from data_pipeline.analysis.correlation import calculate_cross_domain_correlation
from data_pipeline.analysis.models import (
    CorrelationResult,
    EcosystemRelationshipResult,
)
from data_pipeline.analysis.ocean import analyze_ocean_trends
from data_pipeline.fusion.models import DomainType, MarineObservation, UnifiedQueryParams
from data_pipeline.fusion.query_service import query_unified_observations


# Pre-defined supported scientific ecosystem synthesis themes
ECOSYSTEM_THEMES = {
    "temperature_species": {
        "theme": "Temperature ↔ Species Richness",
        "env_domain": DomainType.OCEANOGRAPHY.value,
        "env_var": "temperature",
        "bio_domain": DomainType.BIODIVERSITY.value,
        "bio_var": "individual_count",
        "description": "Evaluates the relationship between seawater temperature gradients and marine species occurrences.",
    },
    "oxygen_biodiversity": {
        "theme": "Dissolved Oxygen ↔ Biodiversity Diversity",
        "env_domain": DomainType.OCEANOGRAPHY.value,
        "env_var": "dissolved_oxygen",
        "bio_domain": DomainType.BIODIVERSITY.value,
        "bio_var": "individual_count",
        "description": "Investigates how dissolved oxygen availability relates to biological community richness and presence.",
    },
    "chlorophyll_habitat": {
        "theme": "Chlorophyll-a ↔ Occurrence Abundance",
        "env_domain": DomainType.OCEANOGRAPHY.value,
        "env_var": "chlorophyll",
        "bio_domain": DomainType.BIODIVERSITY.value,
        "bio_var": "individual_count",
        "description": "Examines whether surface primary productivity (chlorophyll-a) corresponds with higher marine organism densities.",
    },
    "fishing_diversity": {
        "theme": "Fishing Pressure ↔ Species Diversity",
        "env_domain": DomainType.FISHERIES.value,
        "env_var": "catch_weight_kg",
        "bio_domain": DomainType.BIODIVERSITY.value,
        "bio_var": "individual_count",
        "description": "Explores co-occurrence patterns between commercial fisheries landings and local species richness.",
    },
    "ocean_catch": {
        "theme": "Ocean Conditions ↔ Fisheries Catch",
        "env_domain": DomainType.OCEANOGRAPHY.value,
        "env_var": "temperature",
        "bio_domain": DomainType.FISHERIES.value,
        "bio_var": "catch_weight_kg",
        "description": "Analyzes how oceanographic thermal/saline conditions align with commercial fisheries catch variations.",
    },
}


def analyze_ecosystem_relationship(
    theme_key: str = "temperature_species",
    observations: Optional[List[MarineObservation]] = None,
    spatial_radius_km: float = 50.0,
    temporal_window_hours: float = 72.0,
    depth_tolerance_m: Optional[float] = 50.0,
    params: Optional[UnifiedQueryParams] = None,
) -> EcosystemRelationshipResult:
    """
    Synthesizes a multi-domain ecosystem relationship report.

    Args:
        theme_key: One of 'temperature_species', 'oxygen_biodiversity',
                   'chlorophyll_habitat', 'fishing_diversity', 'ocean_catch'.
        observations: Optional in-memory observations list.
        spatial_radius_km: Co-occurrence spatial radius.
        temporal_window_hours: Co-occurrence temporal window.
        depth_tolerance_m: Co-occurrence depth tolerance.
        params: Filter constraints.
    """
    theme_meta = ECOSYSTEM_THEMES.get(theme_key, ECOSYSTEM_THEMES["temperature_species"])
    theme_title = theme_meta["theme"]
    env_dom = theme_meta["env_domain"]
    env_var = theme_meta["env_var"]
    bio_dom = theme_meta["bio_domain"]
    bio_var = theme_meta["bio_var"]

    # Step 1: Fetch observations if not provided
    if observations is None:
        obs_pool = query_unified_observations(params or UnifiedQueryParams())
    else:
        obs_pool = observations

    # Step 2: Compute statistical correlation between the two domains
    corr_result = calculate_cross_domain_correlation(
        domain_x=env_dom,
        variable_x=env_var,
        domain_y=bio_dom,
        variable_y=bio_var,
        observations=obs_pool,
        spatial_radius_km=spatial_radius_km,
        temporal_window_hours=temporal_window_hours,
        depth_tolerance_m=depth_tolerance_m,
    )

    # Step 3: Compute domain-specific context summaries
    env_obs = [o for o in obs_pool if (o.domain or "").lower() == env_dom]
    bio_obs = [o for o in obs_pool if (o.domain or "").lower() == bio_dom]

    env_trend = analyze_ocean_trends(observations=env_obs, variable=env_var)
    bio_summary = calculate_biodiversity_indicators(observations=bio_obs)

    env_context = {
        "variable": env_var,
        "mean_value": env_trend.overall_mean,
        "min_value": env_trend.overall_min,
        "max_value": env_trend.overall_max,
        "data_points": env_trend.data_points_count,
        "unit": env_trend.unit,
    }

    bio_context = {
        "species_richness": bio_summary.species_richness,
        "total_observations": bio_summary.observation_count,
        "shannon_index": bio_summary.shannon_index,
        "simpson_index": bio_summary.simpson_index,
    }

    # Step 4: Build scientific narrative based strictly on empirical calculations
    co_findings = []
    if corr_result.sample_size >= 3 and corr_result.correlation_coefficient is not None:
        r_val = corr_result.correlation_coefficient
        interp = corr_result.interpretation
        narrative = (
            f"Observed {interp} (r = {r_val}, n = {corr_result.sample_size}) between "
            f"{env_dom} ({env_var}) and {bio_dom} ({bio_var}) within {spatial_radius_km}km "
            f"and {temporal_window_hours}h co-occurrence window."
        )
        co_findings.append(f"Empirical correlation coefficient: {r_val}")
        co_findings.append(f"Paired co-occurring observation clusters: {corr_result.sample_size}")
    else:
        narrative = (
            f"Insufficient co-occurring paired observations between {env_dom} ({env_var}) and "
            f"{bio_dom} ({bio_var}) in the current spatio-temporal selection."
        )
        co_findings.append("No statistically sufficient paired observations found.")

    if env_trend.overall_mean is not None:
        co_findings.append(f"Mean {env_var}: {env_trend.overall_mean} {env_trend.unit}")
    if bio_summary.species_richness > 0:
        co_findings.append(f"Observed regional species richness: {bio_summary.species_richness} taxa")

    return EcosystemRelationshipResult(
        theme=theme_title,
        summary_narrative=narrative,
        environmental_variable=env_var,
        biological_indicator=bio_var,
        correlation=corr_result,
        environmental_context=env_context,
        biological_context=bio_context,
        co_occurrence_findings=co_findings,
        provenance={"env_domain": env_dom, "bio_domain": bio_dom, "theme_key": theme_key},
    )
