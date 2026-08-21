"""
Phase 6 — Fisheries Trend Analysis.
Analyzes catch volumes, target species distributions, gear allocations,
and temporal landing patterns from marine fisheries observations.
"""

from collections import defaultdict
from datetime import datetime
import math
from typing import Any, Dict, List, Optional, Tuple

from data_pipeline.analysis.models import FisheriesTrendResult, TrendDataPoint
from data_pipeline.fusion.models import DomainType, MarineObservation, UnifiedQueryParams
from data_pipeline.fusion.query_service import query_unified_observations
from data_pipeline.fusion.temporal import parse_marine_timestamp


def _format_period(dt: Optional[datetime], aggregation: str) -> str:
    """Formats a datetime into an aggregation key."""
    if not dt:
        return "unspecified_time"
    if aggregation == "daily":
        return dt.strftime("%Y-%m-%d")
    elif aggregation == "monthly":
        return dt.strftime("%Y-%m")
    elif aggregation == "yearly":
        return dt.strftime("%Y")
    return dt.strftime("%Y-%m")


def analyze_fisheries_trends(
    observations: Optional[List[MarineObservation]] = None,
    time_aggregation: str = "monthly",
    params: Optional[UnifiedQueryParams] = None,
) -> FisheriesTrendResult:
    """
    Computes comprehensive fisheries catch statistics and distributions.

    Args:
        observations: Optional in-memory list of MarineObservation objects.
        time_aggregation: 'daily', 'monthly', or 'yearly'.
        params: Filter constraints.
    """
    warnings: List[str] = []

    # Step 1: Fetch observations if not provided
    if observations is None:
        query_p = params or UnifiedQueryParams()
        if not query_p.domain:
            query_p.domain = DomainType.FISHERIES.value
        obs_pool = query_unified_observations(query_p)
    else:
        obs_pool = observations

    # Step 2: Filter and extract catch measurements
    catches: List[float] = []
    species_map: Dict[str, float] = defaultdict(float)
    zone_map: Dict[str, float] = defaultdict(float)
    gear_map: Dict[str, float] = defaultdict(float)
    time_buckets: Dict[str, List[float]] = defaultdict(list)
    dataset_ids = set()

    for obs in obs_pool:
        # Verify fisheries domain or catch variable
        obs_domain = (obs.domain or "").lower()
        obs_var = (obs.variable or "").lower()
        if obs_domain != DomainType.FISHERIES.value and "catch" not in obs_var:
            continue

        val = obs.value
        if val is None or math.isnan(val) or math.isinf(val) or val < 0:
            continue

        catches.append(float(val))
        if obs.dataset_id:
            dataset_ids.add(obs.dataset_id)

        # Species aggregation
        sp_name = obs.species_name or obs.species_id or "unspecified_species"
        species_map[sp_name] += float(val)

        # Time grouping
        dt = parse_marine_timestamp(obs.observation_time)
        period_key = _format_period(dt, time_aggregation)
        time_buckets[period_key].append(float(val))

    if not catches:
        return FisheriesTrendResult(
            total_catch_kg=0.0,
            avg_catch_kg=0.0,
            records_count=0,
            has_fishing_effort_data=False,
            effort_notes="No fisheries catch observations found matching the requested criteria.",
            warnings=["No valid fisheries records identified."],
        )

    # Step 3: Compute catch statistics
    n = len(catches)
    total_catch = round(sum(catches), 2)
    avg_catch = round(total_catch / n, 2)
    min_catch = round(min(catches), 2)
    max_catch = round(max(catches), 2)

    # Step 4: Time series aggregation
    time_series: List[TrendDataPoint] = []
    for period in sorted(time_buckets.keys()):
        p_vals = time_buckets[period]
        k = len(p_vals)
        p_mean = sum(p_vals) / k
        p_min = min(p_vals)
        p_max = max(p_vals)
        p_std = None
        if k >= 2:
            var_v = sum((x - p_mean) ** 2 for x in p_vals) / (k - 1)
            p_std = round(math.sqrt(var_v), 2)

        time_series.append(
            TrendDataPoint(
                period=period,
                mean=round(p_mean, 2),
                min=round(p_min, 2),
                max=round(p_max, 2),
                std=p_std,
                count=k,
            )
        )

    # Round breakdown dictionaries
    species_breakdown = {k: round(v, 2) for k, v in sorted(species_map.items(), key=lambda item: item[1], reverse=True)}
    zone_breakdown = {k: round(v, 2) for k, v in zone_map.items()}
    gear_breakdown = {k: round(v, 2) for k, v in gear_map.items()}

    return FisheriesTrendResult(
        total_catch_kg=total_catch,
        avg_catch_kg=avg_catch,
        min_catch_kg=min_catch,
        max_catch_kg=max_catch,
        records_count=n,
        species_breakdown=species_breakdown,
        zone_breakdown=zone_breakdown,
        gear_breakdown=gear_breakdown,
        time_series=time_series,
        has_fishing_effort_data=False,
        effort_notes="Commercial/research landing weights analyzed. Catch weight is distinct from fishing effort (trawling hours/vessel days).",
        provenance={"datasets": list(dataset_ids), "source_domain": DomainType.FISHERIES.value},
        warnings=warnings,
    )
