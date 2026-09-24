"""
Phase 6 — Oceanographic Trend Analysis.
Computes deterministic time-aggregated trends, descriptive statistics,
and linear rates of change for marine physical and chemical variables.
"""

from collections import defaultdict
from datetime import datetime
import math
from typing import Any, Dict, List, Optional, Tuple, Union

from data_pipeline.analysis.models import OceanTrendResult, TrendDataPoint
from data_pipeline.fusion.models import DomainType, MarineObservation, UnifiedQueryParams
from data_pipeline.fusion.query_service import query_unified_observations
from data_pipeline.fusion.temporal import parse_marine_timestamp


SUPPORTED_OCEAN_AGGREGATIONS = {"daily", "monthly", "yearly", "seasonal"}

# Standard scientific variable units
OCEAN_VARIABLE_UNITS: Dict[str, str] = {
    "temperature": "°C",
    "temperature_celsius": "°C",
    "salinity": "PSU",
    "salinity_psu": "PSU",
    "dissolved_oxygen": "mg/L",
    "dissolved_oxygen_mgl": "mg/L",
    "chlorophyll": "mg/m³",
    "chlorophyll_mg_m3": "mg/m³",
    "ph": "pH",
    "pressure": "dbar",
    "pressure_dbar": "dbar",
    "turbidity": "NTU",
    "turbidity_ntu": "NTU",
    "depth": "m",
    "depth_meters": "m",
}

VARIABLE_ALIASES: Dict[str, str] = {
    "temp": "temperature",
    "temperature": "temperature",
    "temperature_celsius": "temperature",
    "sal": "salinity",
    "salinity": "salinity",
    "salinity_psu": "salinity",
    "do": "dissolved_oxygen",
    "dissolved_oxygen": "dissolved_oxygen",
    "dissolved_oxygen_mgl": "dissolved_oxygen",
    "oxygen": "dissolved_oxygen",
    "chl": "chlorophyll",
    "chl_a": "chlorophyll",
    "chlorophyll": "chlorophyll",
    "chlorophyll_mg_m3": "chlorophyll",
    "ph": "ph",
    "pressure": "pressure",
    "pressure_dbar": "pressure",
    "turbidity": "turbidity",
    "turbidity_ntu": "turbidity",
    "depth": "depth",
    "depth_meters": "depth",
}


def _canonical_variable(var_name: Optional[str]) -> str:
    """Resolves variable name to canonical form."""
    if not var_name:
        return ""
    cleaned = str(var_name).lower().strip().replace(" ", "_").replace("-", "")
    return VARIABLE_ALIASES.get(cleaned, cleaned)


def _get_season_label(dt: datetime) -> str:
    """
    Returns the northern Indian Ocean / tropical marine season.
    December is grouped with January and February of the upcoming winter season.
    """
    m = dt.month
    if m in (3, 4, 5):
        return f"{dt.year}-Pre-Monsoon"
    elif m in (6, 7, 8, 9):
        return f"{dt.year}-SW-Monsoon"
    elif m in (10, 11):
        return f"{dt.year}-Post-Monsoon"
    else: # Dec, Jan, Feb
        year = dt.year + 1 if m == 12 else dt.year
        return f"{year}-Winter"


def _format_period(dt: Optional[datetime], aggregation: str) -> str:
    """Formats a datetime into the specified aggregation bucket key."""
    if aggregation not in SUPPORTED_OCEAN_AGGREGATIONS:
        raise ValueError(
            f"Unsupported time_aggregation '{aggregation}'. Supported: {sorted(SUPPORTED_OCEAN_AGGREGATIONS)}"
        )
    if not dt:
        return "unspecified_time"
    if aggregation == "daily":
        return dt.strftime("%Y-%m-%d")
    elif aggregation == "monthly":
        return dt.strftime("%Y-%m")
    elif aggregation == "yearly":
        return dt.strftime("%Y")
    elif aggregation == "seasonal":
        return _get_season_label(dt)
    return dt.strftime("%Y-%m")


def _calculate_linear_slope(x_vals: List[float], y_vals: List[float]) -> Tuple[Optional[float], str]:
    """
    Calculates linear regression slope (rate of change) and direction.
    Uses pure Python fallback to avoid hard dependency failures.
    """
    n = len(x_vals)
    if n < 2:
        return None, "insufficient_data"

    mean_x = sum(x_vals) / n
    mean_y = sum(y_vals) / n

    cov_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals))
    var_x = sum((x - mean_x) ** 2 for x in x_vals)

    if var_x == 0.0 or math.isnan(var_x) or math.isnan(cov_xy):
        return 0.0, "stable"

    slope = cov_xy / var_x
    if math.isnan(slope) or math.isinf(slope):
        return None, "insufficient_data"

    if slope > 1e-4:
        direction = "increasing"
    elif slope < -1e-4:
        direction = "decreasing"
    else:
        direction = "stable"

    return round(slope, 6), direction


def analyze_ocean_trends(
    observations: Optional[List[MarineObservation]] = None,
    variable: str = "temperature",
    time_aggregation: str = "monthly",
    params: Optional[UnifiedQueryParams] = None,
) -> OceanTrendResult:
    """
    Computes statistical trends for a specified oceanographic variable.

    Args:
        observations: Optional in-memory list of MarineObservation objects.
                      If None, queries Phase 5 unified data using `params`.
        variable: The oceanographic variable name to analyze (e.g., 'temperature', 'salinity').
        time_aggregation: 'daily', 'monthly', 'yearly', or 'seasonal'.
        params: Filter constraints (date range, depth range, bbox, radius, etc.).
    """
    if time_aggregation not in SUPPORTED_OCEAN_AGGREGATIONS:
        raise ValueError(
            f"Unsupported time_aggregation '{time_aggregation}'. Supported: {sorted(SUPPORTED_OCEAN_AGGREGATIONS)}"
        )

    warnings: List[str] = []
    canonical_req_var = _canonical_variable(variable)
    unit = OCEAN_VARIABLE_UNITS.get(canonical_req_var, "units")

    # Step 1: Fetch observations if not supplied
    if observations is None:
        query_p = params or UnifiedQueryParams()
        if not query_p.domain:
            query_p.domain = DomainType.OCEANOGRAPHY.value
        obs_pool = query_unified_observations(query_p)
    else:
        obs_pool = observations

    # Step 2: Filter and extract valid measurements with exact canonical variable matching
    filtered: List[Tuple[Optional[datetime], float, Optional[float]]] = []
    dataset_ids = set()

    for obs in obs_pool:
        if not obs.variable:
            continue
        if _canonical_variable(obs.variable) != canonical_req_var:
            continue

        if obs.value is None or math.isnan(obs.value) or math.isinf(obs.value):
            continue

        dt = parse_marine_timestamp(obs.observation_time)
        filtered.append((dt, float(obs.value), obs.depth))
        if obs.dataset_id:
            dataset_ids.add(obs.dataset_id)

    if not filtered:
        return OceanTrendResult(
            variable=variable,
            unit=unit,
            time_aggregation=time_aggregation,
            data_points_count=0,
            trend_direction="insufficient_data",
            warnings=["No valid oceanographic observations found matching the requested criteria."],
        )

    # Step 3: Bucket observations by period
    buckets: Dict[str, List[float]] = defaultdict(list)
    bucket_datetimes: Dict[str, List[datetime]] = defaultdict(list)
    all_values: List[float] = []
    all_depths: List[float] = []
    all_timestamps: List[datetime] = []

    for dt, val, depth in filtered:
        period_key = _format_period(dt, time_aggregation)
        buckets[period_key].append(val)
        all_values.append(val)
        if dt:
            bucket_datetimes[period_key].append(dt)
            all_timestamps.append(dt)
        if depth is not None and not math.isnan(depth):
            all_depths.append(depth)

    # Step 4: Compute aggregated stats per bucket
    time_series: List[TrendDataPoint] = []
    sorted_periods = sorted(buckets.keys())

    for period in sorted_periods:
        vals = buckets[period]
        k = len(vals)
        mean_v = sum(vals) / k
        min_v = min(vals)
        max_v = max(vals)
        std_v = None
        if k >= 2:
            var_v = sum((x - mean_v) ** 2 for x in vals) / (k - 1)
            std_v = round(math.sqrt(var_v), 4)

        time_series.append(
            TrendDataPoint(
                period=period,
                mean=round(mean_v, 4),
                min=round(min_v, 4),
                max=round(max_v, 4),
                std=std_v,
                count=k,
            )
        )

    # Step 5: Overall summary statistics
    n_total = len(all_values)
    overall_mean = round(sum(all_values) / n_total, 4)
    overall_min = round(min(all_values), 4)
    overall_max = round(max(all_values), 4)
    overall_std = None
    if n_total >= 2:
        ov_var = sum((x - overall_mean) ** 2 for x in all_values) / (n_total - 1)
        overall_std = round(math.sqrt(ov_var), 4)

    # Step 6: Trend slope across chronological periods using elapsed time from valid timestamps
    chronological_points = []
    for period in sorted_periods:
        if period == "unspecified_time":
            continue
        dts = bucket_datetimes.get(period)
        if not dts:
            continue
        rep_dt = dts[0] if len(dts) == 1 else min(dts) + (max(dts) - min(dts)) / 2
        p_mean = next(p.mean for p in time_series if p.period == period)
        chronological_points.append((rep_dt, p_mean))

    chronological_points.sort(key=lambda x: x[0])

    if len(chronological_points) >= 2:
        t0 = chronological_points[0][0]
        x_days = [(pt[0] - t0).total_seconds() / 86400.0 for pt in chronological_points]
        y_means = [pt[1] for pt in chronological_points]
        slope, direction = _calculate_linear_slope(x_days, y_means)
    else:
        slope, direction = None, "insufficient_data"

    date_range = None
    if all_timestamps:
        sorted_ts = sorted(all_timestamps)
        date_range = {
            "start": sorted_ts[0].isoformat(),
            "end": sorted_ts[-1].isoformat(),
        }

    depth_range = None
    if all_depths:
        depth_range = {
            "min_depth_m": round(min(all_depths), 2),
            "max_depth_m": round(max(all_depths), 2),
        }

    return OceanTrendResult(
        variable=variable,
        unit=unit,
        time_aggregation=time_aggregation,
        time_series=time_series,
        overall_mean=overall_mean,
        overall_min=overall_min,
        overall_max=overall_max,
        overall_std=overall_std,
        trend_slope=slope,
        trend_direction=direction,
        data_points_count=n_total,
        date_range=date_range,
        depth_range=depth_range,
        provenance={"datasets": sorted(dataset_ids), "source_domain": DomainType.OCEANOGRAPHY.value},
        warnings=warnings,
    )
