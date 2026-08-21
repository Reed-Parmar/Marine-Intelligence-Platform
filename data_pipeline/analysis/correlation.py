"""
Phase 6 — Cross-Domain Correlation Analysis.
Calculates deterministic Pearson and Spearman rank correlation coefficients
between paired marine physical, chemical, biological, and fisheries variables.

IMPORTANT: Correlation represents empirical co-variation and does NOT imply causation.
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union

from data_pipeline.analysis.models import CorrelationResult
from data_pipeline.fusion.models import DomainType, MarineObservation, UnifiedQueryParams
from data_pipeline.fusion.query_service import query_unified_observations
from data_pipeline.fusion.spatial import haversine_distance_km
from data_pipeline.fusion.temporal import parse_marine_timestamp, temporal_distance_hours


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
    "turbidity": "turbidity",
    "turbidity_ntu": "turbidity",
    "pressure": "pressure",
    "pressure_dbar": "pressure",
    "depth": "depth",
    "depth_meters": "depth",
    "catch": "catch_weight_kg",
    "catch_weight": "catch_weight_kg",
    "catch_weight_kg": "catch_weight_kg",
    "catch_kg": "catch_weight_kg",
    "count": "individual_count",
    "individual_count": "individual_count",
    "abundance": "individual_count",
    "richness": "species_richness",
    "species_richness": "species_richness",
}


def _canonical_variable(var_name: Optional[str]) -> str:
    """Normalizes variable name to canonical standard form."""
    if not var_name:
        return ""
    cleaned = str(var_name).lower().strip().replace(" ", "_").replace("-", "")
    return VARIABLE_ALIASES.get(cleaned, cleaned)


def _rank_data(values: List[float]) -> List[float]:
    """Computes fractional ranks for Spearman rank correlation."""
    n = len(values)
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * n
    
    i = 0
    while i < n:
        j = i
        while j < n - 1 and indexed[j][1] == indexed[j + 1][1]:
            j += 1
        avg_rank = sum(range(i + 1, j + 2)) / (j - i + 1)
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg_rank
        i = j + 1
    return ranks


def _compute_pearson(x_vals: List[float], y_vals: List[float]) -> Tuple[Optional[float], Optional[float]]:
    """
    Computes Pearson r and two-tailed p-value.
    Uses scipy when available, with pure-Python r computation fallback.
    """
    n = len(x_vals)
    if n < 3:
        return None, None

    # Check for zero variance
    mean_x = sum(x_vals) / n
    mean_y = sum(y_vals) / n
    var_x = sum((x - mean_x) ** 2 for x in x_vals)
    var_y = sum((y - mean_y) ** 2 for y in y_vals)

    if var_x == 0.0 or var_y == 0.0:
        return 0.0, 1.0

    try:
        from scipy import stats
        res = stats.pearsonr(x_vals, y_vals)
        return round(float(res.statistic), 4), round(float(res.pvalue), 4)
    except Exception:
        # Fallback pure-Python computation (p-value returned as None when scipy unavailable)
        cov_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals))
        denom = math.sqrt(var_x * var_y)
        if denom == 0.0 or math.isnan(denom):
            return 0.0, None
        r = max(-1.0, min(1.0, cov_xy / denom))
        return round(r, 4), None


def _compute_spearman(x_vals: List[float], y_vals: List[float]) -> Tuple[Optional[float], Optional[float]]:
    """Computes Spearman rank correlation coefficient rho and p-value."""
    n = len(x_vals)
    if n < 3:
        return None, None

    try:
        from scipy import stats
        res = stats.spearmanr(x_vals, y_vals)
        return round(float(res.statistic), 4), round(float(res.pvalue), 4)
    except Exception:
        ranked_x = _rank_data(x_vals)
        ranked_y = _rank_data(y_vals)
        return _compute_pearson(ranked_x, ranked_y)


def _interpret_correlation(r: Optional[float], p_val: Optional[float], n: int) -> Tuple[str, bool]:
    """Generates human-readable, non-causal interpretation and significance flag."""
    if r is None or n < 3:
        return "insufficient paired observations", False

    abs_r = abs(r)
    sign = "positive" if r > 0 else "negative"

    if abs_r >= 0.8:
        strength = "strong"
    elif abs_r >= 0.5:
        strength = "moderate"
    elif abs_r >= 0.25:
        strength = "weak"
    else:
        return "negligible or no linear association", False

    is_sig = (p_val is not None and p_val < 0.05) if n >= 5 else False
    sig_note = " (statistically significant at p < 0.05)" if is_sig else ""
    return f"{strength} {sign} association{sig_note}", is_sig


def pair_cross_domain_observations(
    obs_x_list: List[MarineObservation],
    obs_y_list: List[MarineObservation],
    spatial_radius_km: float = 50.0,
    temporal_window_hours: float = 72.0,
    depth_tolerance_m: Optional[float] = 50.0,
) -> List[Tuple[MarineObservation, MarineObservation]]:
    """
    Pairs observations from domain X and domain Y that co-occur in 3D space-time.
    Reuses Phase 5 spatial/temporal/depth matching criteria with pre-parsed timestamp caching.
    """
    pairs: List[Tuple[MarineObservation, MarineObservation]] = []
    used_y_indices = set()

    # Pre-parse candidate Y timestamps once for efficiency
    parsed_y_timestamps = [parse_marine_timestamp(oy.observation_time) for oy in obs_y_list]

    for ox in obs_x_list:
        if ox.latitude is None or ox.longitude is None:
            continue

        dt_x = parse_marine_timestamp(ox.observation_time)
        if temporal_window_hours is not None and dt_x is None:
            continue  # Reject unparseable / missing timestamps when temporal window is required

        best_y_idx = None
        best_dist = float("inf")

        for idx, oy in enumerate(obs_y_list):
            if idx in used_y_indices:
                continue
            if oy.latitude is None or oy.longitude is None:
                continue

            # 1. Spatial distance check
            dist_km = haversine_distance_km(ox.latitude, ox.longitude, oy.latitude, oy.longitude)
            if dist_km > spatial_radius_km:
                continue

            # 2. Temporal window check
            if temporal_window_hours is not None:
                dt_y = parsed_y_timestamps[idx]
                if dt_y is None:
                    continue
                t_diff = temporal_distance_hours(dt_x, dt_y)
                if t_diff > temporal_window_hours:
                    continue

            # 3. Depth tolerance check
            if depth_tolerance_m is not None and ox.depth is not None and oy.depth is not None:
                if abs(ox.depth - oy.depth) > depth_tolerance_m:
                    continue

            # Pick closest spatial match
            if dist_km < best_dist:
                best_dist = dist_km
                best_y_idx = idx

        if best_y_idx is not None:
            pairs.append((ox, obs_y_list[best_y_idx]))
            used_y_indices.add(best_y_idx)

    return pairs


def calculate_cross_domain_correlation(
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
    """
    Computes statistical correlation between two variables across marine domains.

    Args:
        domain_x: Source domain for variable X (e.g. 'oceanography').
        variable_x: Variable name for X (e.g. 'temperature').
        domain_y: Source domain for variable Y (e.g. 'biodiversity').
        variable_y: Variable name for Y (e.g. 'individual_count' or 'species_richness').
        observations: Optional combined list of MarineObservation objects.
        method: 'pearson' (linear) or 'spearman' (rank monotonic).
        spatial_radius_km: Maximum pairing distance in km.
        temporal_window_hours: Maximum pairing time window in hours.
        depth_tolerance_m: Maximum vertical depth tolerance in meters.
        paired_data_override: Direct list of (x, y) float pairs for testing/synthetic analysis.
    """
    warnings: List[str] = []

    # Case 1: Direct paired numbers supplied (joint filtering for finite pairs)
    if paired_data_override is not None:
        valid_pairs = [
            (float(p[0]), float(p[1])) for p in paired_data_override
            if p is not None and len(p) >= 2 and p[0] is not None and p[1] is not None
            and math.isfinite(float(p[0])) and math.isfinite(float(p[1]))
        ]
        x_vals = [p[0] for p in valid_pairs]
        y_vals = [p[1] for p in valid_pairs]
        paired_records = [{"x": p[0], "y": p[1]} for p in valid_pairs]
    else:
        # Case 2: Extract and pair observations with exact canonical variable matching
        target_var_x = _canonical_variable(variable_x)
        target_var_y = _canonical_variable(variable_y)

        if observations is None:
            obs_x_pool = query_unified_observations(UnifiedQueryParams(domain=domain_x, variable=variable_x))
            obs_y_pool = query_unified_observations(UnifiedQueryParams(domain=domain_y, variable=variable_y))
        else:
            obs_x_pool = [
                o for o in observations
                if (o.domain or "").lower() == domain_x.lower()
                and o.variable
                and _canonical_variable(o.variable) == target_var_x
            ]
            obs_y_pool = [
                o for o in observations
                if (o.domain or "").lower() == domain_y.lower()
                and o.variable
                and _canonical_variable(o.variable) == target_var_y
            ]

        pairs = pair_cross_domain_observations(
            obs_x_pool,
            obs_y_pool,
            spatial_radius_km=spatial_radius_km,
            temporal_window_hours=temporal_window_hours,
            depth_tolerance_m=depth_tolerance_m,
        )

        x_vals = []
        y_vals = []
        paired_records = []

        for ox, oy in pairs:
            if ox.value is not None and oy.value is not None:
                try:
                    vx = float(ox.value)
                    vy = float(oy.value)
                    if math.isfinite(vx) and math.isfinite(vy):
                        x_vals.append(vx)
                        y_vals.append(vy)
                        paired_records.append({
                            "x": vx,
                            "y": vy,
                            "latitude": ox.latitude,
                            "longitude": ox.longitude,
                            "time_x": ox.observation_time,
                            "time_y": oy.observation_time,
                        })
                except (ValueError, TypeError):
                    continue

    n = len(x_vals)
    if n < 3:
        return CorrelationResult(
            variable_x=variable_x,
            variable_y=variable_y,
            domain_x=domain_x,
            domain_y=domain_y,
            method=method,
            sample_size=n,
            interpretation="insufficient_paired_observations",
            warnings=[f"Insufficient paired observations ({n} found; minimum 3 required)."],
            paired_data=paired_records,
        )

    # Compute correlation based on selected method
    if method.lower() == "spearman":
        coeff, p_val = _compute_spearman(x_vals, y_vals)
    else:
        coeff, p_val = _compute_pearson(x_vals, y_vals)

    interpretation, is_sig = _interpret_correlation(coeff, p_val, n)

    return CorrelationResult(
        variable_x=variable_x,
        variable_y=variable_y,
        domain_x=domain_x,
        domain_y=domain_y,
        method=method.lower(),
        correlation_coefficient=coeff,
        p_value=p_val,
        sample_size=n,
        interpretation=interpretation,
        is_statistically_significant=is_sig,
        paired_data=paired_records[:100],  # Sample points capped for payload size
        warnings=warnings,
    )
