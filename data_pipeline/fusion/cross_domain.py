"""
Cross-Domain Linking & Spatial-Temporal-Depth Fusion Engine for Phase 5.

Associates heterogeneous marine observations across domains (e.g. oceanography, fisheries,
biodiversity/species occurrences, and eDNA detections) sharing common spatial, temporal,
and depth contexts.

Scientific Trust & Ethics:
- All associations are explicitly labeled as 'associated observations/context'.
- Spatial, temporal, or depth proximity DOES NOT imply biological causation.
- Provenance (dataset_id, domain, source_table, observation_id, sample_id) is strictly preserved.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from data_pipeline.fusion.depth import is_within_depth_tolerance
from data_pipeline.fusion.models import (
    CrossDomainAssociation,
    DomainType,
    MarineObservation,
)
from data_pipeline.fusion.spatial import (
    haversine_distance_km,
    is_within_spatial_proximity,
)
from data_pipeline.fusion.temporal import (
    is_within_temporal_window,
    temporal_distance_hours,
)


def find_associated_observations(
    anchor: MarineObservation,
    candidate_observations: List[MarineObservation],
    spatial_radius_km: float = 50.0,
    temporal_window_hours: float = 72.0,
    depth_tolerance_m: Optional[float] = 50.0,
    target_domains: Optional[List[str]] = None,
    allow_missing_depth: bool = True,
) -> CrossDomainAssociation:
    """
    Finds and associates observations from other domains that occurred in the same
    spatial, temporal, and depth neighborhood as the anchor observation.

    Args:
        anchor: The reference MarineObservation.
        candidate_observations: Pool of candidate MarineObservation objects.
        spatial_radius_km: Maximum geographic distance in kilometers (Haversine).
        temporal_window_hours: Maximum time difference in hours.
        depth_tolerance_m: Maximum vertical distance in meters (None disables depth filtering).
        target_domains: Optional list of specific domain names to match against (e.g. ['oceanography']).
                        If None, searches across all domains different from the anchor's domain.
        allow_missing_depth: If True, matches when depth is None on either observation.

    Returns:
        CrossDomainAssociation object containing the anchor and all matched observations.
    """
    matched: List[MarineObservation] = []

    for candidate in candidate_observations:
        # Avoid self-matching or same record
        if candidate.id and anchor.id and candidate.id == anchor.id:
            continue
        if (
            candidate.observation_id
            and anchor.observation_id
            and candidate.observation_id == anchor.observation_id
            and candidate.domain == anchor.domain
        ):
            continue

        # Filter by domain if specified
        if target_domains is not None:
            if candidate.domain not in target_domains:
                continue
        else:
            # By default, match across OTHER domains (cross-domain fusion)
            if anchor.domain and candidate.domain and candidate.domain == anchor.domain:
                continue

        # 1. Spatial Check (geodesic distance)
        if not is_within_spatial_proximity(
            anchor.latitude, anchor.longitude,
            candidate.latitude, candidate.longitude,
            spatial_radius_km
        ):
            continue

        # 2. Temporal Check (time difference in hours)
        # If both have timestamps, verify window
        if anchor.observation_time and candidate.observation_time:
            if not is_within_temporal_window(
                anchor.observation_time,
                candidate.observation_time,
                temporal_window_hours
            ):
                continue
        elif not anchor.observation_time or not candidate.observation_time:
            # When one or both timestamps are missing, we check if spatial-only is permitted
            pass

        # 3. Depth Check (vertical water column)
        if depth_tolerance_m is not None:
            if not is_within_depth_tolerance(
                anchor.depth,
                candidate.depth,
                depth_tolerance_m,
                allow_missing=allow_missing_depth
            ):
                continue

        # Matched
        matched.append(candidate)

    return CrossDomainAssociation(
        anchor=anchor,
        associated=matched,
        spatial_radius_km=spatial_radius_km,
        temporal_window_hours=temporal_window_hours,
        depth_tolerance_m=depth_tolerance_m,
    )


def batch_fuse_observations(
    anchor_observations: List[MarineObservation],
    candidate_pool: List[MarineObservation],
    spatial_radius_km: float = 50.0,
    temporal_window_hours: float = 72.0,
    depth_tolerance_m: Optional[float] = 50.0,
    allow_missing_depth: bool = True,
) -> List[CrossDomainAssociation]:
    """
    Performs cross-domain fusion across a batch of anchor observations.
    """
    results: List[CrossDomainAssociation] = []
    for anchor in anchor_observations:
        assoc = find_associated_observations(
            anchor=anchor,
            candidate_observations=candidate_pool,
            spatial_radius_km=spatial_radius_km,
            temporal_window_hours=temporal_window_hours,
            depth_tolerance_m=depth_tolerance_m,
            allow_missing_depth=allow_missing_depth,
        )
        results.append(assoc)
    return results
