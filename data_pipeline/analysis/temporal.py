"""
Phase 6 — Temporal Dynamics & Time-Series Analysis.
Performs deterministic multi-scale temporal aggregation (daily, monthly, yearly, seasonal)
and cross-domain temporal comparison while strictly preserving timezone semantics.
"""

from collections import defaultdict
from datetime import datetime
import math
from typing import Any, Dict, List, Optional

from data_pipeline.analysis.models import (
    TemporalAnalysisResult,
    TemporalBucket,
)
from data_pipeline.fusion.models import DomainType, MarineObservation, UnifiedQueryParams
from data_pipeline.fusion.query_service import query_unified_observations
from data_pipeline.fusion.temporal import parse_marine_timestamp


SUPPORTED_TEMPORAL_PERIODS = {"daily", "monthly", "yearly", "seasonal"}

SEASONS: Dict[str, List[int]] = {
    "Pre-Monsoon": [3, 4, 5],
    "SW-Monsoon": [6, 7, 8, 9],
    "Post-Monsoon": [10, 11],
    "Winter": [12, 1, 2],
}


def _get_season_name(month: int) -> str:
    """Classifies month into the standard northern Indian Ocean seasonal regime."""
    for season, months in SEASONS.items():
        if month in months:
            return season
    return "Unknown"


def _format_period(dt: Optional[datetime], period_type: str) -> str:
    """Formats datetime according to aggregation scale."""
    if period_type not in SUPPORTED_TEMPORAL_PERIODS:
        raise ValueError(
            f"Unsupported period_type '{period_type}'. Supported: {sorted(SUPPORTED_TEMPORAL_PERIODS)}"
        )
    if not dt:
        return "unspecified_time"
    if period_type == "daily":
        return dt.strftime("%Y-%m-%d")
    elif period_type == "monthly":
        return dt.strftime("%Y-%m")
    elif period_type == "yearly":
        return dt.strftime("%Y")
    elif period_type == "seasonal":
        s_name = _get_season_name(dt.month)
        year = dt.year + 1 if dt.month == 12 else dt.year
        return f"{year}-{s_name}"
    return dt.strftime("%Y-%m")


def analyze_temporal_dynamics(
    observations: Optional[List[MarineObservation]] = None,
    period_type: str = "monthly",
    params: Optional[UnifiedQueryParams] = None,
) -> TemporalAnalysisResult:
    """
    Analyzes temporal patterns, domain frequency distributions, and variable means across time.

    Args:
        observations: Optional in-memory observations list.
        period_type: 'daily', 'monthly', 'yearly', or 'seasonal'.
        params: UnifiedQueryParams filter.
    """
    if period_type not in SUPPORTED_TEMPORAL_PERIODS:
        raise ValueError(
            f"Unsupported period_type '{period_type}'. Supported: {sorted(SUPPORTED_TEMPORAL_PERIODS)}"
        )

    warnings: List[str] = []

    # Step 1: Fetch observations if not supplied
    if observations is None:
        obs_pool = query_unified_observations(params or UnifiedQueryParams())
    else:
        obs_pool = observations

    # Step 2: Extract valid timestamps and group by bucket
    # Key: period_str -> List[MarineObservation]
    buckets: Dict[str, List[MarineObservation]] = defaultdict(list)
    dataset_ids = set()
    valid_datetimes: List[datetime] = []

    # Seasonal accumulator: season_name -> {count, domain_counts, vars}
    seasonal_buckets: Dict[str, Dict[str, Any]] = {
        "Pre-Monsoon": {"count": 0, "domain_counts": defaultdict(int), "vars": defaultdict(list)},
        "SW-Monsoon": {"count": 0, "domain_counts": defaultdict(int), "vars": defaultdict(list)},
        "Post-Monsoon": {"count": 0, "domain_counts": defaultdict(int), "vars": defaultdict(list)},
        "Winter": {"count": 0, "domain_counts": defaultdict(int), "vars": defaultdict(list)},
    }

    for obs in obs_pool:
        if not obs.observation_time:
            continue

        dt = parse_marine_timestamp(obs.observation_time)
        if dt is None:
            continue

        valid_datetimes.append(dt)
        period_key = _format_period(dt, period_type)
        buckets[period_key].append(obs)

        if obs.dataset_id:
            dataset_ids.add(obs.dataset_id)

        # Seasonal accumulation
        s_name = _get_season_name(dt.month)
        if s_name in seasonal_buckets:
            s_dict = seasonal_buckets[s_name]
            s_dict["count"] += 1
            s_dict["domain_counts"][obs.domain or "unknown"] += 1
            if obs.variable and obs.value is not None:
                try:
                    val_f = float(obs.value)
                    if math.isfinite(val_f):
                        s_dict["vars"][obs.variable.lower()].append(val_f)
                except (ValueError, TypeError):
                    pass

    if not buckets:
        return TemporalAnalysisResult(
            period_type=period_type,
            total_observations=0,
            warnings=["No observations with valid timestamps found."],
        )

    # Step 3: Compute aggregated statistics per temporal bucket
    time_series: List[TemporalBucket] = []
    for period in sorted(buckets.keys()):
        b_obs = buckets[period]
        b_doms: Dict[str, int] = defaultdict(int)
        b_species: Dict[str, int] = defaultdict(int)
        b_vars: Dict[str, List[float]] = defaultdict(list)

        for o in b_obs:
            b_doms[o.domain or "unknown"] += 1
            if o.species_name or o.species_id:
                b_species[o.species_name or o.species_id] += 1
            if o.variable and o.value is not None:
                try:
                    val_f = float(o.value)
                    if math.isfinite(val_f):
                        b_vars[o.variable.lower()].append(val_f)
                except (ValueError, TypeError):
                    pass

        var_means = {v: round(sum(vals) / len(vals), 4) for v, vals in b_vars.items() if vals}

        time_series.append(
            TemporalBucket(
                period=period,
                total_count=len(b_obs),
                domain_counts=dict(b_doms),
                species_counts=dict(b_species),
                variable_means=var_means,
            )
        )

    # Format seasonal summary
    seasonal_summary: Dict[str, Dict[str, Any]] = {}
    for s_name, s_data in seasonal_buckets.items():
        v_means = {v: round(sum(vals) / len(vals), 4) for v, vals in s_data["vars"].items() if vals}
        seasonal_summary[s_name] = {
            "observation_count": s_data["count"],
            "domain_counts": dict(s_data["domain_counts"]),
            "variable_means": v_means,
        }

    sorted_dts = sorted(valid_datetimes)
    time_min = sorted_dts[0].isoformat() if sorted_dts else None
    time_max = sorted_dts[-1].isoformat() if sorted_dts else None

    return TemporalAnalysisResult(
        period_type=period_type,
        total_observations=len(valid_datetimes),
        time_series=time_series,
        seasonal_summary=seasonal_summary,
        time_min=time_min,
        time_max=time_max,
        provenance={"datasets": sorted(dataset_ids)},
        warnings=warnings,
    )
