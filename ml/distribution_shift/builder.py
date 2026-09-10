"""
Seasonal Species Distribution Shift Dataset Builder.

Constructs population-state transition records from CMLRE marine database observations
across the Arabian Sea Exclusive Economic Zone and adjacent oceanic sectors.
"""

from collections import defaultdict
from datetime import datetime, timezone
import json
import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.app.db.database import execute_query
from data_pipeline.fusion.spatial import (
    haversine_distance_km,
    is_valid_coordinate,
    is_within_bbox,
)
from data_pipeline.fusion.temporal import parse_marine_timestamp
from ml.distribution_shift.models import (
    PopulationStateObservation,
    SeasonalDistributionTransition,
)

logger = logging.getLogger(__name__)

# Standard Arabian Sea Bounding Box [West, South, East, North]
ARABIAN_SEA_BBOX: List[float] = [65.0, 6.0, 78.5, 24.0]

# Standard 3-Season Indian Oceanographic Calendar
# 1: Pre-Monsoon (Feb–May), 2: SW Monsoon (Jun–Sep), 3: Post-Monsoon / Winter (Oct–Jan)
MONTH_TO_SEASON: Dict[int, Tuple[int, str]] = {
    1: (3, "Post-Monsoon"),
    2: (1, "Pre-Monsoon"),
    3: (1, "Pre-Monsoon"),
    4: (1, "Pre-Monsoon"),
    5: (1, "Pre-Monsoon"),
    6: (2, "SW Monsoon"),
    7: (2, "SW Monsoon"),
    8: (2, "SW Monsoon"),
    9: (2, "SW Monsoon"),
    10: (3, "Post-Monsoon"),
    11: (3, "Post-Monsoon"),
    12: (3, "Post-Monsoon"),
}


def classify_arabian_sea_sector(lat: float, lon: float) -> str:
    """
    Classifies a coordinate into authoritative Arabian Sea ecological / administrative sectors.
    """
    if lat >= 20.0 and lon <= 73.5:
        return "North Arabian Sea / Gujarat Shelf"
    elif 14.0 <= lat < 20.0 and lon >= 71.0:
        return "Konkan Coast / Central West Coast"
    elif 8.0 <= lat < 14.0 and lon >= 74.0:
        return "Malabar Upwelling Shelf"
    elif 8.0 <= lat < 14.0 and 71.0 <= lon < 74.0:
        return "Lakshadweep Sea & Ridge"
    elif 6.0 <= lat < 8.0 and lon >= 76.0:
        return "Wadge Bank / Comorin Sector"
    elif lon < 71.0:
        return "Central Arabian Sea Offshore Basin"
    return "South-Eastern Arabian Sea EEZ"


def get_grid_cell_id(lat: float, lon: float, step: float = 1.0) -> Tuple[str, float, float, float, float]:
    """
    Assigns coordinate to standard 1° x 1° grid cell matching data_pipeline.analysis.spatial.
    """
    lat_idx = int(math.floor(lat / step))
    lon_idx = int(math.floor(lon / step))
    lat_min = round(lat_idx * step, 2)
    lat_max = round(lat_min + step, 2)
    lon_min = round(lon_idx * step, 2)
    lon_max = round(lon_min + step, 2)
    cell_id = f"CELL_{int(lat_min):02d}N_{int(lon_min):02d}E"
    return cell_id, lat_min, lat_max, lon_min, lon_max


def compute_geodesic_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[float]:
    """
    Calculates initial geodesic azimuth heading from (lat1, lon1) to (lat2, lon2) in degrees [0, 360).
    Returns None if points are identical.
    """
    if abs(lat1 - lat2) < 1e-6 and abs(lon1 - lon2) < 1e-6:
        return None

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    bearing = math.degrees(math.atan2(y, x))
    return round((bearing + 360.0) % 360.0, 2)


class SeasonalDistributionDatasetBuilder:
    """
    Builds structured, population-level seasonal distribution transition datasets.
    """

    def __init__(
        self,
        bbox: Optional[List[float]] = None,
        grid_size_deg: float = 1.0,
        env_fusion_radius_km: float = 100.0,
        env_fusion_window_days: float = 45.0,
        min_species_occurrences: int = 5,
    ):
        self.bbox = bbox or ARABIAN_SEA_BBOX
        self.grid_size_deg = grid_size_deg
        self.env_fusion_radius_km = env_fusion_radius_km
        self.env_fusion_window_days = env_fusion_window_days
        self.min_species_occurrences = min_species_occurrences

    def load_raw_observations(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Loads occurrence, catch, and CTD observation records within the Arabian Sea bounding box.
        """
        w, s, e, n = self.bbox[0], self.bbox[1], self.bbox[2], self.bbox[3]

        # 1. Biological Occurrences (Species Occurrences + Fisheries Records)
        occ_query = f"""
            SELECT 
                id::text as record_id,
                dataset_id::text as dataset_id,
                COALESCE(species_id::text, scientific_name) as species_key,
                scientific_name,
                common_name,
                timestamp,
                latitude,
                longitude,
                depth_meters,
                'biodiversity' as domain
            FROM public.species_occurrences
            WHERE latitude BETWEEN {s} AND {n}
              AND longitude BETWEEN {w} AND {e}
              AND timestamp IS NOT NULL
            UNION ALL
            SELECT 
                id::text as record_id,
                dataset_id::text as dataset_id,
                COALESCE(species_id::text, species_name_reported) as species_key,
                species_name_reported as scientific_name,
                species_name_reported as common_name,
                timestamp,
                latitude,
                longitude,
                depth_meters,
                'fisheries' as domain
            FROM public.fisheries_records
            WHERE latitude BETWEEN {s} AND {n}
              AND longitude BETWEEN {w} AND {e}
              AND timestamp IS NOT NULL;
        """
        bio_rows = execute_query(occ_query)

        # 2. Physical Oceanographic Sensor Measurements
        ocean_query = f"""
            SELECT 
                id::text as record_id,
                dataset_id::text as dataset_id,
                timestamp,
                latitude,
                longitude,
                depth_meters,
                temperature_celsius,
                salinity_psu,
                dissolved_oxygen_mgl,
                chlorophyll_mg_m3
            FROM public.oceanographic_observations
            WHERE latitude BETWEEN {s} AND {n}
              AND longitude BETWEEN {w} AND {e}
              AND (
                  temperature_celsius IS NOT NULL OR 
                  salinity_psu IS NOT NULL OR 
                  dissolved_oxygen_mgl IS NOT NULL OR 
                  chlorophyll_mg_m3 IS NOT NULL
              );
        """
        ocean_rows = execute_query(ocean_query)

        return bio_rows, ocean_rows

    def match_environmental_context(
        self,
        lat: float,
        lon: float,
        month: int,
        ocean_records: List[Dict[str, Any]],
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], Dict[str, Any]]:
        """
        Finds oceanographic sensor records within spatial-temporal fusion neighborhood.
        Never replaces missing data with zeroes; returns (sst, sal, do, chl, metadata).
        """
        matched_temps = []
        matched_sals = []
        matched_dos = []
        matched_chls = []
        distances = []

        for o in ocean_records:
            o_lat = o.get("latitude")
            o_lon = o.get("longitude")
            if not is_valid_coordinate(o_lat, o_lon):
                continue

            dist = haversine_distance_km(lat, lon, float(o_lat), float(o_lon))
            if dist > self.env_fusion_radius_km:
                continue

            # Check month proximity (within +/- 1 month cyclically)
            o_time = parse_marine_timestamp(o.get("timestamp"))
            if o_time is not None:
                o_month = o_time.month
                month_diff = min(abs(month - o_month), 12 - abs(month - o_month))
                if month_diff > 1:
                    continue

            distances.append(dist)
            if o.get("temperature_celsius") is not None:
                matched_temps.append(float(o["temperature_celsius"]))
            if o.get("salinity_psu") is not None:
                matched_sals.append(float(o["salinity_psu"]))
            if o.get("dissolved_oxygen_mgl") is not None:
                matched_dos.append(float(o["dissolved_oxygen_mgl"]))
            if o.get("chlorophyll_mg_m3") is not None:
                matched_chls.append(float(o["chlorophyll_mg_m3"]))

        sst = round(sum(matched_temps) / len(matched_temps), 2) if matched_temps else None
        sal = round(sum(matched_sals) / len(matched_sals), 2) if matched_sals else None
        do = round(sum(matched_dos) / len(matched_dos), 2) if matched_dos else None
        chl = round(sum(matched_chls) / len(matched_chls), 3) if matched_chls else None

        metadata = {
            "fusion_matched_records": len(distances),
            "avg_fusion_distance_km": round(sum(distances) / len(distances), 1) if distances else None,
            "fusion_radius_km": self.env_fusion_radius_km,
            "fusion_method": "spatial_temporal_cross_domain_neighborhood" if distances else "unobserved",
        }

        return sst, sal, do, chl, metadata

    def build_population_states(
        self,
        bio_rows: List[Dict[str, Any]],
        ocean_rows: List[Dict[str, Any]],
    ) -> Dict[str, List[PopulationStateObservation]]:
        """
        Groups biological observations by (species, grid_cell, season, month) and
        constructs population-state centroid observations.
        """
        # Step 1: Filter species with sufficient data
        species_counts: Dict[str, int] = defaultdict(int)
        for r in bio_rows:
            sp = (r.get("scientific_name") or r.get("species_key") or "").strip()
            if sp:
                species_counts[sp] += 1

        valid_species = {sp for sp, cnt in species_counts.items() if cnt >= self.min_species_occurrences}

        # Step 2: Bucket observations into (species, cell_id, season_code, month)
        buckets: Dict[Tuple[str, str, int, int], List[Dict[str, Any]]] = defaultdict(list)

        for r in bio_rows:
            sp = (r.get("scientific_name") or r.get("species_key") or "").strip()
            if sp not in valid_species:
                continue

            lat = r.get("latitude")
            lon = r.get("longitude")
            if not is_valid_coordinate(lat, lon):
                continue
            f_lat, f_lon = float(lat), float(lon)

            if not is_within_bbox(f_lat, f_lon, self.bbox):
                continue

            t = parse_marine_timestamp(r.get("timestamp"))
            if t is None:
                continue

            month = t.month
            season_code, _ = MONTH_TO_SEASON[month]
            cell_id, _, _, _, _ = get_grid_cell_id(f_lat, f_lon, self.grid_size_deg)

            buckets[(sp, cell_id, season_code, month)].append(r)

        # Step 3: Compute centroid population states
        species_states: Dict[str, List[PopulationStateObservation]] = defaultdict(list)

        for (sp, cell_id, season_code, month), obs_list in buckets.items():
            lats = [float(o["latitude"]) for o in obs_list]
            lons = [float(o["longitude"]) for o in obs_list]
            depths = [float(o["depth_meters"]) for o in obs_list if o.get("depth_meters") is not None]

            centroid_lat = round(sum(lats) / len(lats), 4)
            centroid_lon = round(sum(lons) / len(lons), 4)
            sector = classify_arabian_sea_sector(centroid_lat, centroid_lon)
            season_name = MONTH_TO_SEASON[month][1]

            mean_depth = round(sum(depths) / len(depths), 1) if depths else None

            # Environmental context via spatial-temporal fusion
            sst, sal, do, chl, env_meta = self.match_environmental_context(
                centroid_lat, centroid_lon, month, ocean_rows
            )

            total_species_occ = species_counts[sp]
            historical_rate = round(len(obs_list) / max(1, total_species_occ), 4)

            record_ids = [o["record_id"] for o in obs_list if o.get("record_id")]
            dataset_ids = list({o["dataset_id"] for o in obs_list if o.get("dataset_id")})

            sp_id = obs_list[0].get("species_key", sp)

            state = PopulationStateObservation(
                species_id=sp_id,
                scientific_name=sp,
                cell_id=cell_id,
                centroid_lat=centroid_lat,
                centroid_lon=centroid_lon,
                sector=sector,
                year=None,
                month=month,
                season_code=season_code,
                season_name=season_name,
                occurrence_count=len(obs_list),
                mean_depth_meters=mean_depth,
                sst_celsius=sst,
                salinity_psu=sal,
                dissolved_oxygen_mgl=do,
                chlorophyll_mg_m3=chl,
                trophic_level=None,
                historical_occurrence_rate=historical_rate,
                source_record_ids=record_ids,
                dataset_ids=dataset_ids,
                environmental_fusion_metadata=env_meta,
            )
            species_states[sp].append(state)

        return species_states

    def build_transitions(
        self,
        species_states: Dict[str, List[PopulationStateObservation]],
    ) -> List[SeasonalDistributionTransition]:
        """
        Generates consecutive seasonal and monthly population-state transitions.
        Ensures strict temporal ordering and scientific validity.
        """
        transitions: List[SeasonalDistributionTransition] = []

        for sp, states in species_states.items():
            if len(states) < 2:
                continue

            # Sort states by seasonal progression (Season 1 -> 2 -> 3) and month
            sorted_states = sorted(states, key=lambda s: (s.season_code, s.month, s.cell_id))

            for i in range(len(sorted_states)):
                src = sorted_states[i]

                # Find valid forward temporal targets (consecutive season or consecutive month)
                for j in range(len(sorted_states)):
                    if i == j:
                        continue
                    tgt = sorted_states[j]

                    # Valid transitions:
                    # Case A: Consecutive seasonal succession (1 -> 2, 2 -> 3, 3 -> 1)
                    is_consecutive_season = (
                        (src.season_code == 1 and tgt.season_code == 2) or
                        (src.season_code == 2 and tgt.season_code == 3) or
                        (src.season_code == 3 and tgt.season_code == 1)
                    )

                    # Case B: Sequential monthly step within same or adjacent season (1 <= month_diff <= 3)
                    month_diff = (tgt.month - src.month) % 12
                    is_sequential_month = 1 <= month_diff <= 3

                    if not (is_consecutive_season or is_sequential_month):
                        continue

                    # Calculate displacement distance and heading
                    dist_km = haversine_distance_km(
                        src.centroid_lat, src.centroid_lon,
                        tgt.centroid_lat, tgt.centroid_lon
                    )
                    bearing = compute_geodesic_bearing(
                        src.centroid_lat, src.centroid_lon,
                        tgt.centroid_lat, tgt.centroid_lon
                    )

                    # Periodic month encoding
                    month_sin = round(math.sin(2 * math.pi * src.month / 12.0), 4)
                    month_cos = round(math.cos(2 * math.pi * src.month / 12.0), 4)

                    trans = SeasonalDistributionTransition(
                        species_id=src.species_id,
                        scientific_name=src.scientific_name,
                        current_cell_id=src.cell_id,
                        current_lat=src.centroid_lat,
                        current_lon=src.centroid_lon,
                        current_sector=src.sector,
                        season_code=src.season_code,
                        season_name=src.season_name,
                        month=src.month,
                        month_sin=month_sin,
                        month_cos=month_cos,
                        sst_celsius=src.sst_celsius,
                        salinity_psu=src.salinity_psu,
                        dissolved_oxygen_mgl=src.dissolved_oxygen_mgl,
                        chlorophyll_mg_m3=src.chlorophyll_mg_m3,
                        mean_depth_meters=src.mean_depth_meters,
                        historical_occurrence_rate=src.historical_occurrence_rate,
                        trophic_level=src.trophic_level,
                        target_cell_id=tgt.cell_id,
                        target_lat=tgt.centroid_lat,
                        target_lon=tgt.centroid_lon,
                        target_sector=tgt.sector,
                        target_season_code=tgt.season_code,
                        target_season_name=tgt.season_name,
                        target_month=tgt.month,
                        displacement_distance_km=round(dist_km, 2),
                        target_direction_deg=bearing,
                        source_record_ids=src.source_record_ids,
                        dataset_ids=src.dataset_ids,
                        environmental_fusion_metadata=src.environmental_fusion_metadata,
                    )
                    transitions.append(trans)

        return transitions

    def build_and_save(
        self,
        output_filepath: Optional[str] = None,
    ) -> Tuple[List[SeasonalDistributionTransition], Dict[str, Any]]:
        """
        Executes complete pipeline: queries data, aggregates population states,
        constructs transitions, generates summary report, and exports JSON.
        """
        logger.info("Loading raw biological and oceanographic observations...")
        bio_rows, ocean_rows = self.load_raw_observations()

        logger.info(f"Loaded {len(bio_rows)} biological records and {len(ocean_rows)} CTD sensor profiles.")

        species_states = self.build_population_states(bio_rows, ocean_rows)
        total_states = sum(len(s) for s in species_states.values())
        logger.info(f"Aggregated {total_states} population-state centroids across {len(species_states)} species.")

        transitions = self.build_transitions(species_states)
        logger.info(f"Generated {len(transitions)} seasonal distribution transitions.")

        from ml.distribution_shift.summary import generate_transition_summary
        summary = generate_transition_summary(transitions)

        # Output persistence
        if output_filepath is None:
            output_dir = Path(__file__).resolve().parent.parent.parent / "data_pipeline" / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_filepath = str(output_dir / "species_seasonal_distribution_shifts.json")

        out_path = Path(output_filepath)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "geographic_domain": "Arabian Sea (Indian EEZ & Adjacent Oceanic Sector)",
                "spatial_resolution": f"{self.grid_size_deg} degree grid (~111 km)",
                "total_transitions": len(transitions),
                "scientific_disclaimer": "Represents Eulerian seasonal population distribution shifts; does not represent Lagrangian individual fish trajectories.",
            },
            "summary_report": summary,
            "transitions": [t.to_dict() for t in transitions],
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        logger.info(f"Saved transition dataset and report to {output_filepath}")
        return transitions, summary
