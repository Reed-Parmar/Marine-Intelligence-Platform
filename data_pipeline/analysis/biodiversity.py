"""
Phase 6 — Biodiversity Indicators & Species Distribution Analysis.
Computes ecological community indices (Species Richness, Shannon H', Simpson D, Pielou J')
and geographic occurrence distribution maps for marine taxa.
"""

from collections import defaultdict
from datetime import datetime
import math
from typing import Any, Dict, List, Optional, Set, Tuple

from data_pipeline.analysis.models import (
    BiodiversityResult,
    SpeciesDistributionResult,
)
from data_pipeline.fusion.models import DomainType, MarineObservation, UnifiedQueryParams
from data_pipeline.fusion.query_service import query_unified_observations


def calculate_biodiversity_indicators(
    observations: Optional[List[MarineObservation]] = None,
    sample_definition: str = "regional_community",
    params: Optional[UnifiedQueryParams] = None,
) -> BiodiversityResult:
    """
    Computes mathematical biodiversity indices from marine occurrence observations.

    Formulas:
    - Species Richness (S): Count of distinct species.
    - Total Abundance (N): Sum of individual counts n_i.
    - Relative Abundance: p_i = n_i / N
    - Shannon-Wiener Index (H'): - sum(p_i * ln(p_i))
    - Gini-Simpson Index (1 - D): 1 - sum(p_i^2)
    - Pielou's Evenness (J'): H' / ln(S) (for S > 1)
    """
    warnings: List[str] = []

    # Step 1: Fetch observations if not supplied
    if observations is None:
        query_p = params or UnifiedQueryParams()
        if not query_p.domain:
            query_p.domain = DomainType.BIODIVERSITY.value
        obs_pool = query_unified_observations(query_p)
    else:
        obs_pool = observations

    # Step 2: Aggregate counts per species
    species_counts: Dict[str, float] = defaultdict(float)
    total_individuals = 0.0
    dataset_ids = set()

    for obs in obs_pool:
        # Check domain
        obs_dom = (obs.domain or "").lower()
        if obs_dom not in (DomainType.BIODIVERSITY.value, DomainType.EDNA.value, DomainType.FISHERIES.value):
            # If not explicitly marked biodiversity, accept if species name/id is present
            if not obs.species_name and not obs.species_id:
                continue

        sp_name = obs.species_name or obs.species_id or "unidentified_taxon"
        
        # Explicit finite abundance check, fallback to 1.0 (presence-only)
        count = 1.0
        if obs.value is not None:
            try:
                v_f = float(obs.value)
                if math.isfinite(v_f) and v_f > 0:
                    count = v_f
            except (ValueError, TypeError):
                count = 1.0

        species_counts[sp_name] += count
        total_individuals += count
        if obs.dataset_id:
            dataset_ids.add(obs.dataset_id)

    s_richness = len(species_counts)
    n_total = int(total_individuals) if isinstance(total_individuals, float) and total_individuals.is_integer() else total_individuals

    if s_richness == 0 or n_total == 0:
        return BiodiversityResult(
            species_richness=0,
            observation_count=0,
            shannon_index=None,
            simpson_index=None,
            pielou_evenness=None,
            species_abundances={},
            sample_definition=sample_definition,
            provenance={"datasets": sorted(dataset_ids), "source_domain": DomainType.BIODIVERSITY.value},
            warnings=["No species occurrences found to calculate biodiversity metrics."],
        )

    # Step 3: Compute Shannon, Simpson, and Pielou indices
    shannon_h = 0.0
    simpson_sum = 0.0
    abundances: Dict[str, float] = {}

    for sp, count in species_counts.items():
        p_i = count / total_individuals
        abundances[sp] = round(count, 2)
        if p_i > 0:
            shannon_h -= p_i * math.log(p_i)
            simpson_sum += p_i ** 2

    gini_simpson = 1.0 - simpson_sum

    # Pielou's Evenness J' = H' / ln(S)
    if s_richness > 1:
        pielou_j = shannon_h / math.log(s_richness)
    else:
        pielou_j = 1.0 # Single species is trivially maximally even with itself

    if s_richness < 3:
        warnings.append(f"Low species richness (S={s_richness}); biodiversity indices may have limited ecological meaning.")

    return BiodiversityResult(
        species_richness=s_richness,
        observation_count=n_total,
        shannon_index=round(shannon_h, 4),
        simpson_index=round(gini_simpson, 4),
        pielou_evenness=round(pielou_j, 4),
        species_abundances=abundances,
        sample_definition=sample_definition,
        provenance={"datasets": sorted(dataset_ids), "source_domain": DomainType.BIODIVERSITY.value},
        warnings=warnings,
    )


def analyze_species_distribution(
    observations: Optional[List[MarineObservation]] = None,
    params: Optional[UnifiedQueryParams] = None,
) -> SpeciesDistributionResult:
    """
    Analyzes geographic and bathymetric distribution of species occurrences.

    Calculates species spatial centroids, depth extents, and location-aware points for maps.
    """
    warnings: List[str] = []

    # Step 1: Fetch observations if not supplied
    if observations is None:
        query_p = params or UnifiedQueryParams()
        if not query_p.domain:
            query_p.domain = DomainType.BIODIVERSITY.value
        obs_pool = query_unified_observations(query_p)
    else:
        obs_pool = observations

    species_locations: Dict[str, List[Tuple[float, float, Optional[float]]]] = defaultdict(list)
    species_occurrence_counts: Dict[str, int] = defaultdict(int)
    spatial_points: List[Dict[str, Any]] = []
    dataset_ids = set()

    lats: List[float] = []
    lons: List[float] = []

    for obs in obs_pool:
        sp_name = obs.species_name or obs.species_id or "unidentified_taxon"
        
        # Finite positive integer-valued count check, fallback to 1
        count = 1
        if obs.value is not None:
            try:
                v_f = float(obs.value)
                if math.isfinite(v_f) and v_f > 0 and v_f.is_integer():
                    count = int(v_f)
            except (ValueError, TypeError):
                count = 1

        species_occurrence_counts[sp_name] += count

        if obs.dataset_id:
            dataset_ids.add(obs.dataset_id)

        if obs.latitude is not None and obs.longitude is not None:
            lat = float(obs.latitude)
            lon = float(obs.longitude)
            lats.append(lat)
            lons.append(lon)
            species_locations[sp_name].append((lat, lon, obs.depth))

            spatial_points.append({
                "species_name": sp_name,
                "species_id": obs.species_id,
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "depth": round(obs.depth, 2) if obs.depth is not None else None,
                "count": count,
                "observation_time": obs.observation_time,
                "dataset_id": obs.dataset_id,
            })

    if not species_occurrence_counts:
        return SpeciesDistributionResult(
            total_occurrences=0,
            unique_species_count=0,
            warnings=["No species occurrences found matching criteria."],
        )

    # Step 2: Compute species summaries with centroids & depth bounds
    species_summary: List[Dict[str, Any]] = []
    for sp_name, locs in species_locations.items():
        n_pts = len(locs)
        lat_c = round(sum(p[0] for p in locs) / n_pts, 5) if n_pts > 0 else None
        lon_c = round(sum(p[1] for p in locs) / n_pts, 5) if n_pts > 0 else None
        depths = [p[2] for p in locs if p[2] is not None]
        d_min = round(min(depths), 2) if depths else None
        d_max = round(max(depths), 2) if depths else None

        species_summary.append({
            "species_name": sp_name,
            "total_count": species_occurrence_counts[sp_name],
            "observation_records": n_pts,
            "lat_centroid": lat_c,
            "lon_centroid": lon_c,
            "depth_min_m": d_min,
            "depth_max_m": d_max,
        })

    # Sort by abundance descending
    species_summary.sort(key=lambda x: x["total_count"], reverse=True)

    # Bounding box
    bbox = None
    if lats and lons:
        bbox = {
            "south": round(min(lats), 6),
            "north": round(max(lats), 6),
            "west": round(min(lons), 6),
            "east": round(max(lons), 6),
        }

    return SpeciesDistributionResult(
        total_occurrences=sum(species_occurrence_counts.values()),
        unique_species_count=len(species_occurrence_counts),
        species_summary=species_summary,
        spatial_points=spatial_points,
        bounding_box=bbox,
        provenance={"datasets": sorted(dataset_ids), "source_domain": DomainType.BIODIVERSITY.value},
        warnings=warnings,
    )
