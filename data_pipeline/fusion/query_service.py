"""
Unified Marine Query & Data Fusion Service for Phase 5.

Provides the service-level interface for Phase 6 Scientific Analysis,
FastAPI Backend endpoints, and Dashboard summary operations.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from data_pipeline.fusion.cross_domain import (
    find_associated_observations,
    batch_fuse_observations,
)
from data_pipeline.fusion.db import count_table, get_supabase_client, query_table
from data_pipeline.fusion.depth import is_within_depth_range
from data_pipeline.fusion.models import (
    CrossDomainAssociation,
    DomainType,
    MarineObservation,
    UnifiedQueryParams,
    UnifiedSummary,
)
from data_pipeline.fusion.spatial import (
    compute_bounding_box,
    is_within_bbox,
    is_within_spatial_proximity,
)
from data_pipeline.fusion.temporal import (
    is_within_date_range,
    parse_marine_timestamp,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Domain Record Adapters (Translate DB schemas -> MarineObservation)
# =============================================================================

def map_oceanographic_record(row: Dict[str, Any]) -> List[MarineObservation]:
    """
    Maps an oceanographic_observations DB record to canonical MarineObservation objects.
    Extracts individual physical/chemical measurements as separate variable observations.
    """
    obs_list: List[MarineObservation] = []
    base_id = str(row.get("id", ""))
    dataset_id = row.get("dataset_id")
    station_id = row.get("station_id")
    sample_id = row.get("sample_id")
    lat = float(row["latitude"]) if row.get("latitude") is not None else None
    lon = float(row["longitude"]) if row.get("longitude") is not None else None
    depth = float(row["depth_meters"]) if row.get("depth_meters") is not None else None
    time_str = str(row["timestamp"]) if row.get("timestamp") is not None else None
    quality = row.get("quality_status") or (f"score:{row.get('quality_score')}" if row.get("quality_score") is not None else None)

    # Measurement variables mapping: (column_name, variable_name, unit)
    measurements = [
        ("temperature_celsius", "temperature", "°C"),
        ("salinity_psu", "salinity", "PSU"),
        ("dissolved_oxygen_mgl", "dissolved_oxygen", "mg/L"),
        ("chlorophyll_mg_m3", "chlorophyll", "mg/m³"),
        ("ph", "ph", "pH"),
        ("pressure_dbar", "pressure", "dbar"),
        ("turbidity_ntu", "turbidity", "NTU"),
    ]

    has_any_var = False
    for col, var_name, unit in measurements:
        val = row.get(col)
        if val is not None:
            try:
                num_val = float(val)
                has_any_var = True
                obs = MarineObservation(
                    id=f"{base_id}_{var_name}",
                    dataset_id=dataset_id,
                    domain=DomainType.OCEANOGRAPHY.value,
                    observation_id=base_id,
                    station_id=station_id,
                    sample_id=sample_id,
                    latitude=lat,
                    longitude=lon,
                    observation_time=time_str,
                    depth=depth,
                    variable=var_name,
                    value=num_val,
                    unit=unit,
                    source_table="oceanographic_observations",
                    quality_status=quality,
                )
                obs_list.append(obs)
            except (ValueError, TypeError):
                continue

    # If record has no specific measurements but has coordinates, return a base observation
    if not has_any_var:
        obs_list.append(
            MarineObservation(
                id=base_id,
                dataset_id=dataset_id,
                domain=DomainType.OCEANOGRAPHY.value,
                observation_id=base_id,
                station_id=station_id,
                sample_id=sample_id,
                latitude=lat,
                longitude=lon,
                observation_time=time_str,
                depth=depth,
                variable="hydrographic_profile",
                value=1.0,
                unit="profile",
                source_table="oceanographic_observations",
                quality_status=quality,
            )
        )

    return obs_list


def map_fisheries_record(row: Dict[str, Any]) -> List[MarineObservation]:
    """
    Maps a fisheries_records DB record to canonical MarineObservation objects.
    """
    base_id = str(row.get("id", ""))
    dataset_id = row.get("dataset_id")
    sample_id = row.get("sample_id")
    species_id = row.get("species_id")
    lat = float(row["latitude"]) if row.get("latitude") is not None else None
    lon = float(row["longitude"]) if row.get("longitude") is not None else None
    depth = float(row["depth_meters"]) if row.get("depth_meters") is not None else None
    time_str = str(row["timestamp"]) if row.get("timestamp") is not None else None
    quality = row.get("quality_status")

    catch_weight = row.get("catch_weight_kg")
    weight_val = float(catch_weight) if catch_weight is not None else None

    obs = MarineObservation(
        id=base_id,
        dataset_id=dataset_id,
        domain=DomainType.FISHERIES.value,
        observation_id=base_id,
        sample_id=sample_id,
        species_id=species_id,
        species_name=row.get("vessel_name") or row.get("fishing_zone"),
        latitude=lat,
        longitude=lon,
        observation_time=time_str,
        depth=depth,
        variable="catch_weight",
        value=weight_val,
        unit="kg",
        source_table="fisheries_records",
        quality_status=quality,
    )
    return [obs]


def map_species_occurrence_record(row: Dict[str, Any]) -> List[MarineObservation]:
    """
    Maps a species_occurrences DB record to canonical MarineObservation objects.
    """
    base_id = str(row.get("id", ""))
    dataset_id = row.get("dataset_id")
    sample_id = row.get("sample_id")
    species_id = row.get("species_id")
    scientific_name = row.get("scientific_name") or row.get("common_name")
    lat = float(row["latitude"]) if row.get("latitude") is not None else None
    lon = float(row["longitude"]) if row.get("longitude") is not None else None
    depth = float(row["depth_meters"]) if row.get("depth_meters") is not None else None
    time_str = str(row["timestamp"]) if row.get("timestamp") is not None else None
    quality = row.get("quality_status")

    count_val = row.get("individual_count")
    count_num = float(count_val) if count_val is not None else 1.0

    obs = MarineObservation(
        id=base_id,
        dataset_id=dataset_id,
        domain=DomainType.BIODIVERSITY.value,
        observation_id=base_id,
        sample_id=sample_id,
        species_id=species_id,
        species_name=scientific_name,
        latitude=lat,
        longitude=lon,
        observation_time=time_str,
        depth=depth,
        variable="individual_count",
        value=count_num,
        unit="count",
        source_table="species_occurrences",
        quality_status=quality,
    )
    return [obs]


def map_edna_sample_record(row: Dict[str, Any]) -> List[MarineObservation]:
    """
    Maps an edna_samples DB record to canonical MarineObservation objects.
    """
    base_id = str(row.get("id", ""))
    dataset_id = row.get("dataset_id")
    sample_id = row.get("sample_id")
    station_id = row.get("station_id")
    lat = float(row["latitude"]) if row.get("latitude") is not None else None
    lon = float(row["longitude"]) if row.get("longitude") is not None else None
    depth = float(row["depth_meters"]) if row.get("depth_meters") is not None else None
    time_str = str(row["created_at"]) if row.get("created_at") is not None else None
    quality = row.get("quality_status")
    target_gene = row.get("target_gene", "eDNA")

    obs = MarineObservation(
        id=base_id,
        dataset_id=dataset_id,
        domain=DomainType.EDNA.value,
        observation_id=base_id,
        station_id=station_id,
        sample_id=sample_id,
        latitude=lat,
        longitude=lon,
        observation_time=time_str,
        depth=depth,
        variable="edna_sample",
        value=1.0,
        unit="detection",
        source_table="edna_samples",
        quality_status=quality,
    )
    return [obs]


# =============================================================================
# In-Memory Record Filter Application
# =============================================================================

def apply_filters(
    observations: List[MarineObservation],
    params: UnifiedQueryParams
) -> List[MarineObservation]:
    """
    Applies spatial, temporal, depth, species, domain, and variable filters
    to a list of MarineObservation objects.
    """
    filtered: List[MarineObservation] = []

    for obs in observations:
        # Domain filter
        if params.domain is not None and params.domain != "":
            if obs.domain is None or obs.domain.lower() != params.domain.lower():
                continue

        # Dataset ID filter
        if params.dataset_id is not None and params.dataset_id != "":
            if obs.dataset_id != params.dataset_id:
                continue

        # Species filter
        if params.species is not None and params.species != "":
            sp_query = params.species.lower().strip()
            obs_sp_name = (obs.species_name or "").lower()
            obs_sp_id = (obs.species_id or "").lower()
            if sp_query not in obs_sp_name and sp_query != obs_sp_id:
                continue

        # Variable filter
        if params.variable is not None and params.variable != "":
            if obs.variable is None or obs.variable.lower() != params.variable.lower():
                continue

        # Depth range filter
        if params.depth_min is not None or params.depth_max is not None:
            if not is_within_depth_range(obs.depth, params.depth_min, params.depth_max):
                continue

        # Temporal range filter
        if params.date_from is not None or params.date_to is not None:
            if not is_within_date_range(obs.observation_time, params.date_from, params.date_to):
                continue

        # Spatial filter — Bounding Box
        if params.bbox is not None and len(params.bbox) == 4:
            if not is_within_bbox(obs.latitude, obs.longitude, params.bbox):
                continue

        # Spatial filter — Point + Radius
        if params.latitude is not None and params.longitude is not None and params.radius_km is not None:
            if not is_within_spatial_proximity(
                params.latitude, params.longitude,
                obs.latitude, obs.longitude,
                params.radius_km
            ):
                continue

        filtered.append(obs)

    # Apply pagination
    start = params.offset
    end = start + params.limit
    return filtered[start:end]


# =============================================================================
# Main Unified Query Functions (Phase 5 -> Phase 6 / FastAPI Interface)
# =============================================================================

def query_unified_observations(
    params: Optional[UnifiedQueryParams] = None,
    records: Optional[List[MarineObservation]] = None,
    use_db: bool = True
) -> List[MarineObservation]:
    """
    Main unified query function for heterogeneous marine observations.

    Args:
        params: UnifiedQueryParams containing desired filters.
        records: Optional pre-loaded MarineObservation objects (for testing or fast in-memory query).
        use_db: If True and records is None, queries Supabase PostgreSQL tables.

    Returns:
        List of MarineObservation objects matching all filter criteria.
    """
    query_params = params or UnifiedQueryParams()

    if records is not None:
        return apply_filters(records, query_params)

    # Query from live database if requested
    pool: List[MarineObservation] = []
    if use_db:
        domains_to_fetch = [query_params.domain] if query_params.domain else [
            DomainType.OCEANOGRAPHY.value,
            DomainType.FISHERIES.value,
            DomainType.BIODIVERSITY.value,
            DomainType.EDNA.value,
        ]

        for d in domains_to_fetch:
            domain_obs = fetch_domain_from_db(d, query_params)
            pool.extend(domain_obs)

    return apply_filters(pool, query_params)


def fetch_domain_from_db(
    domain: str,
    params: UnifiedQueryParams
) -> List[MarineObservation]:
    """Fetches and maps records from the relevant database table."""
    obs_list: List[MarineObservation] = []
    dom_str = domain.lower() if domain else ""

    if dom_str == DomainType.OCEANOGRAPHY.value:
        raw_rows = query_table("oceanographic_observations", limit=params.limit)
        for r in raw_rows:
            obs_list.extend(map_oceanographic_record(r))
    elif dom_str == DomainType.FISHERIES.value:
        raw_rows = query_table("fisheries_records", limit=params.limit)
        for r in raw_rows:
            obs_list.extend(map_fisheries_record(r))
    elif dom_str == DomainType.BIODIVERSITY.value:
        raw_rows = query_table("species_occurrences", limit=params.limit)
        for r in raw_rows:
            obs_list.extend(map_species_occurrence_record(r))
    elif dom_str == DomainType.EDNA.value:
        raw_rows = query_table("edna_samples", limit=params.limit)
        for r in raw_rows:
            obs_list.extend(map_edna_sample_record(r))

    return obs_list


def get_domain_observations(
    domain: str,
    params: Optional[UnifiedQueryParams] = None,
    records: Optional[List[MarineObservation]] = None,
    use_db: bool = True
) -> List[MarineObservation]:
    """
    Retrieves observations restricted to a specific domain.
    """
    p = params or UnifiedQueryParams()
    p.domain = domain
    return query_unified_observations(params=p, records=records, use_db=use_db)


def get_unified_summary(
    records: Optional[List[MarineObservation]] = None,
    params: Optional[UnifiedQueryParams] = None,
    use_db: bool = True
) -> UnifiedSummary:
    """
    Generates summary statistics for the unified marine data layer (for dashboard).
    """
    obs_list = query_unified_observations(params=params, records=records, use_db=use_db)

    if not obs_list:
        return UnifiedSummary()

    datasets: Set[str] = set()
    domains: Set[str] = set()
    species: Set[str] = set()
    variables: Set[str] = set()
    domain_counts: Dict[str, int] = {}
    coords: List[Tuple[float, float]] = []
    timestamps: List[str] = []

    for o in obs_list:
        if o.dataset_id:
            datasets.add(o.dataset_id)
        if o.domain:
            domains.add(o.domain)
            domain_counts[o.domain] = domain_counts.get(o.domain, 0) + 1
        if o.species_name:
            species.add(o.species_name)
        if o.variable:
            variables.add(o.variable)
        if o.latitude is not None and o.longitude is not None:
            coords.append((o.latitude, o.longitude))
        if o.observation_time:
            timestamps.append(o.observation_time)

    # Compute bounding box
    bbox_dict = compute_bounding_box(coords)
    lat_min = bbox_dict["lat_min"] if bbox_dict else None
    lat_max = bbox_dict["lat_max"] if bbox_dict else None
    lon_min = bbox_dict["lon_min"] if bbox_dict else None
    lon_max = bbox_dict["lon_max"] if bbox_dict else None

    # Compute temporal range
    time_min = min(timestamps) if timestamps else None
    time_max = max(timestamps) if timestamps else None

    return UnifiedSummary(
        total_observations=len(obs_list),
        total_datasets=len(datasets),
        domains=sorted(list(domains)),
        species_count=len(species),
        species_names=sorted(list(species)),
        lat_min=lat_min,
        lat_max=lat_max,
        lon_min=lon_min,
        lon_max=lon_max,
        time_min=time_min,
        time_max=time_max,
        variables=sorted(list(variables)),
        domain_counts=domain_counts,
    )


def get_cross_domain_context(
    anchor: MarineObservation,
    candidate_pool: Optional[List[MarineObservation]] = None,
    spatial_radius_km: float = 50.0,
    temporal_window_hours: float = 72.0,
    depth_tolerance_m: Optional[float] = 50.0,
    use_db: bool = True
) -> CrossDomainAssociation:
    """
    Discovers associated observations across domains near a given anchor observation.
    """
    if candidate_pool is not None:
        candidates = candidate_pool
    else:
        # Query database around anchor's location/time
        qp = UnifiedQueryParams(
            latitude=anchor.latitude,
            longitude=anchor.longitude,
            radius_km=spatial_radius_km * 1.5,
            limit=500
        )
        candidates = query_unified_observations(params=qp, use_db=use_db)

    return find_associated_observations(
        anchor=anchor,
        candidate_observations=candidates,
        spatial_radius_km=spatial_radius_km,
        temporal_window_hours=temporal_window_hours,
        depth_tolerance_m=depth_tolerance_m,
    )
