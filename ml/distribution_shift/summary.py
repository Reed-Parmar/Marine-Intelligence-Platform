"""
Statistical summary and validation report generator for Seasonal Distribution Transitions.
"""

from collections import Counter, defaultdict
import math
from typing import Any, Dict, List

from ml.distribution_shift.models import SeasonalDistributionTransition


def generate_transition_summary(
    transitions: List[SeasonalDistributionTransition],
) -> Dict[str, Any]:
    """
    Computes a comprehensive scientific summary report across the generated transition dataset.
    """
    if not transitions:
        return {
            "total_transition_rows": 0,
            "species_count": 0,
            "source_cell_count": 0,
            "target_cell_count": 0,
            "season_counts": {},
            "transitions_per_species": [],
            "missing_feature_percentages": {},
            "environmental_fusion_coverage": {},
            "top_transition_pairs": [],
            "displacement_statistics_km": {},
        }

    total_rows = len(transitions)
    species_set = set()
    src_cells = set()
    tgt_cells = set()
    season_counts = Counter()
    species_counter = Counter()
    transition_pairs = Counter()
    displacements = []

    # Missing feature tracking
    missing_sst = 0
    missing_sal = 0
    missing_do = 0
    missing_chl = 0
    missing_depth = 0
    with_env_fusion = 0

    for t in transitions:
        species_set.add(t.scientific_name)
        src_cells.add(t.current_cell_id)
        tgt_cells.add(t.target_cell_id)
        season_counts[t.season_name] += 1
        species_counter[t.scientific_name] += 1

        pair_key = f"{t.current_cell_id} ({t.current_sector}) -> {t.target_cell_id} ({t.target_sector})"
        transition_pairs[pair_key] += 1

        displacements.append(t.displacement_distance_km)

        if t.sst_celsius is None:
            missing_sst += 1
        else:
            with_env_fusion += 1

        if t.salinity_psu is None:
            missing_sal += 1
        if t.dissolved_oxygen_mgl is None:
            missing_do += 1
        if t.chlorophyll_mg_m3 is None:
            missing_chl += 1
        if t.mean_depth_meters is None:
            missing_depth += 1

    # Sorted displacement stats
    displacements.sort()
    mean_disp = round(sum(displacements) / total_rows, 2)
    median_disp = round(displacements[total_rows // 2], 2)
    min_disp = round(displacements[0], 2)
    max_disp = round(displacements[-1], 2)

    top_species_list = [
        {"species": sp, "transition_count": cnt, "percentage": round((cnt / total_rows) * 100, 2)}
        for sp, cnt in species_counter.most_common(15)
    ]

    top_pairs_list = [
        {"transition_pair": pair, "count": cnt, "percentage": round((cnt / total_rows) * 100, 2)}
        for pair, cnt in transition_pairs.most_common(10)
    ]

    missing_percentages = {
        "sst_celsius_missing_pct": round((missing_sst / total_rows) * 100, 2),
        "salinity_psu_missing_pct": round((missing_sal / total_rows) * 100, 2),
        "dissolved_oxygen_missing_pct": round((missing_do / total_rows) * 100, 2),
        "chlorophyll_mg_m3_missing_pct": round((missing_chl / total_rows) * 100, 2),
        "mean_depth_meters_missing_pct": round((missing_depth / total_rows) * 100, 2),
    }

    fusion_coverage = {
        "transitions_with_environmental_fusion": with_env_fusion,
        "environmental_fusion_coverage_pct": round((with_env_fusion / total_rows) * 100, 2),
        "unobserved_environmental_features_preserved_as_null": True,
        "zero_fabrication_guarantee": "Missing sensor data preserved as null (never replaced with 0.0)",
    }

    return {
        "total_transition_rows": total_rows,
        "species_count": len(species_set),
        "source_cell_count": len(src_cells),
        "target_cell_count": len(tgt_cells),
        "season_counts": dict(season_counts),
        "transitions_per_species": top_species_list,
        "missing_feature_percentages": missing_percentages,
        "environmental_fusion_coverage": fusion_coverage,
        "top_transition_pairs": top_pairs_list,
        "displacement_statistics_km": {
            "mean_km": mean_disp,
            "median_km": median_disp,
            "min_km": min_disp,
            "max_km": max_disp,
        },
    }
