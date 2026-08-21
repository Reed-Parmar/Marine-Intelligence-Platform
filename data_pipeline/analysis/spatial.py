"""
Phase 6 — Spatial Analysis & Multi-Domain Regional Distribution.
Utilizes Phase 5 geodesic Haversine distance and bounding-box geometry
to perform spatial grid binning, regional summaries, and cross-domain comparisons.
"""

from collections import defaultdict
import math
from typing import Any, Dict, List, Optional, Set, Tuple

from data_pipeline.analysis.models import (
    SpatialAnalysisResult,
    SpatialGridCell,
)
from data_pipeline.fusion.models import DomainType, MarineObservation, UnifiedQueryParams
from data_pipeline.fusion.query_service import query_unified_observations
from data_pipeline.fusion.spatial import (
    haversine_distance_km,
    is_valid_coordinate,
    is_within_bbox,
)


def analyze_spatial_distribution(
    observations: Optional[List[MarineObservation]] = None,
    grid_size_deg: float = 1.0,
    bbox: Optional[List[float]] = None,
    center_coords: Optional[Tuple[float, float]] = None,
    radius_km: Optional[float] = None,
    params: Optional[UnifiedQueryParams] = None,
) -> SpatialAnalysisResult:
    """
    Performs spatial aggregation, grid cell binning, and cross-domain regional comparison.

    Args:
        observations: Optional in-memory observations list.
        grid_size_deg: Spatial cell resolution in degrees (default 1.0° ~ 111 km at equator).
        bbox: Optional bounding box [west, south, east, north].
        center_coords: Optional (latitude, longitude) center.
        radius_km: Optional search radius in kilometers.
        params: UnifiedQueryParams filter.
    """
    warnings: List[str] = []

    # Step 1: Fetch observations if not supplied
    if observations is None:
        query_p = params or UnifiedQueryParams(
            bbox=bbox,
            latitude=center_coords[0] if center_coords else None,
            longitude=center_coords[1] if center_coords else None,
            radius_km=radius_km,
        )
        obs_pool = query_unified_observations(query_p)
    else:
        obs_pool = observations

    # Step 2: Spatial filtering (if explicit spatial constraints given on in-memory pool)
    filtered_obs: List[MarineObservation] = []
    dataset_ids = set()
    lats: List[float] = []
    lons: List[float] = []

    for obs in obs_pool:
        if obs.latitude is None or obs.longitude is None:
            continue
        if not is_valid_coordinate(obs.latitude, obs.longitude):
            continue

        lat = float(obs.latitude)
        lon = float(obs.longitude)

        # Apply bbox filter if specified
        if bbox is not None:
            if not is_within_bbox(lat, lon, bbox):
                continue

        # Apply point-radius filter if specified
        if center_coords is not None and radius_km is not None:
            dist = haversine_distance_km(center_coords[0], center_coords[1], lat, lon)
            if dist > radius_km:
                continue

        filtered_obs.append(obs)
        lats.append(lat)
        lons.append(lon)
        if obs.dataset_id:
            dataset_ids.add(obs.dataset_id)

    if not filtered_obs:
        return SpatialAnalysisResult(
            total_observations=0,
            warnings=["No observations found within the specified spatial boundaries."],
        )

    # Step 3: Domain & Species distribution
    domain_counts: Dict[str, int] = defaultdict(int)
    species_counts: Dict[str, int] = defaultdict(int)
    variable_vals: Dict[str, List[float]] = defaultdict(list)

    # Step 4: Grid Cell Binning
    # Key: (lat_bin_idx, lon_bin_idx)
    grid_buckets: Dict[Tuple[int, int], List[MarineObservation]] = defaultdict(list)

    step = max(0.01, grid_size_deg)

    for obs in filtered_obs:
        lat = float(obs.latitude)
        lon = float(obs.longitude)

        dom = obs.domain or DomainType.OCEANOGRAPHY.value
        domain_counts[dom] += 1

        if obs.species_name or obs.species_id:
            sp = obs.species_name or obs.species_id
            species_counts[sp] += 1

        if obs.variable and obs.value is not None:
            try:
                val_f = float(obs.value)
                if math.isfinite(val_f):
                    variable_vals[obs.variable.lower()].append(val_f)
            except (ValueError, TypeError):
                pass

        lat_idx = int(math.floor(lat / step))
        lon_idx = int(math.floor(lon / step))
        grid_buckets[(lat_idx, lon_idx)].append(obs)

    # Construct Grid Cells
    grid_cells: List[SpatialGridCell] = []
    for (lat_idx, lon_idx), cell_obs in grid_buckets.items():
        cell_lat_min = lat_idx * step
        cell_lat_max = cell_lat_min + step
        cell_lon_min = lon_idx * step
        cell_lon_max = cell_lon_min + step

        c_dom_counts: Dict[str, int] = defaultdict(int)
        c_species: Set[str] = set()
        c_vars: Dict[str, List[float]] = defaultdict(list)

        for o in cell_obs:
            c_dom = o.domain or DomainType.OCEANOGRAPHY.value
            c_dom_counts[c_dom] += 1
            if o.species_name or o.species_id:
                c_species.add(o.species_name or o.species_id)
            if o.variable and o.value is not None:
                try:
                    val_f = float(o.value)
                    if math.isfinite(val_f):
                        c_vars[o.variable.lower()].append(val_f)
                except (ValueError, TypeError):
                    pass

        mean_vals = {v: round(sum(vals) / len(vals), 4) for v, vals in c_vars.items() if vals}

        grid_cells.append(
            SpatialGridCell(
                lat_min=round(cell_lat_min, 4),
                lat_max=round(cell_lat_max, 4),
                lon_min=round(cell_lon_min, 4),
                lon_max=round(cell_lon_max, 4),
                center_lat=round((cell_lat_min + cell_lat_max) / 2.0, 4),
                center_lon=round((cell_lon_min + cell_lon_max) / 2.0, 4),
                observation_count=len(cell_obs),
                domain_counts=dict(c_dom_counts),
                species_count=len(c_species),
                species_richness=len(c_species),
                mean_values=mean_vals,
            )
        )

    # Deterministic sorting: descending by count, then by lat_min, lon_min
    grid_cells.sort(key=lambda c: (-c.observation_count, c.lat_min, c.lon_min))

    # Variable summary stats across the region
    var_stats: Dict[str, Dict[str, float]] = {}
    for var_name, vals in variable_vals.items():
        if vals:
            var_stats[var_name] = {
                "mean": round(sum(vals) / len(vals), 4),
                "min": round(min(vals), 4),
                "max": round(max(vals), 4),
                "count": len(vals),
            }

    bounds = {
        "south": round(min(lats), 6),
        "north": round(max(lats), 6),
        "west": round(min(lons), 6),
        "east": round(max(lons), 6),
    }

    return SpatialAnalysisResult(
        total_observations=len(filtered_obs),
        bounding_box=bounds,
        center_coords=center_coords,
        radius_km=radius_km,
        domain_distribution=dict(domain_counts),
        species_distribution=dict(species_counts),
        grid_cells=grid_cells,
        variable_spatial_stats=var_stats,
        provenance={"datasets": sorted(dataset_ids)},
        warnings=warnings,
    )
