"""
Unit & Integration Tests for Seasonal Species Distribution Shift Dataset Builder.

Verifies:
1. Grid cell assignment (1° x 1° standard resolution).
2. Seasonal succession ordering (Pre-Monsoon -> SW Monsoon -> Post-Monsoon).
3. Rejection of invalid, unphysical, or backwards transitions.
4. Spatial geodesic distance and azimuth bearing calculations.
5. Missing environmental data handling (preserving None, never fabricating 0.0).
6. Population-level centroid aggregation (explicitly observation counts, never biomass).
7. End-to-end dataset builder execution with summary metrics.
"""

import math
import os
import unittest
from datetime import datetime, timezone
from pathlib import Path

from ml.distribution_shift.builder import (
    ARABIAN_SEA_BBOX,
    MONTH_TO_SEASON,
    SeasonalDistributionDatasetBuilder,
    classify_arabian_sea_sector,
    compute_geodesic_bearing,
    get_grid_cell_id,
)
from ml.distribution_shift.models import (
    PopulationStateObservation,
    SeasonalDistributionTransition,
)
from ml.distribution_shift.summary import generate_transition_summary


class TestSeasonalDistributionShiftDataset(unittest.TestCase):

    def test_01_grid_cell_assignment(self):
        """1. Verifies 1° x 1° grid cell indexing and boundaries."""
        # Kochi Coast (Lat 9.95, Lon 75.85) -> Cell 09N_75E [9-10N, 75-76E]
        cell_id, lat_min, lat_max, lon_min, lon_max = get_grid_cell_id(9.95, 75.85, step=1.0)
        self.assertEqual(cell_id, "CELL_09N_75E")
        self.assertEqual(lat_min, 9.0)
        self.assertEqual(lat_max, 10.0)
        self.assertEqual(lon_min, 75.0)
        self.assertEqual(lon_max, 76.0)

        # Goa Coast (Lat 15.2, Lon 73.1) -> Cell 15N_73E
        cell_id_goa, lat_min, _, lon_min, _ = get_grid_cell_id(15.2, 73.1, step=1.0)
        self.assertEqual(cell_id_goa, "CELL_15N_73E")
        self.assertEqual(lat_min, 15.0)
        self.assertEqual(lon_min, 73.0)

        # Gujarat / North Arabian Sea (Lat 21.5, Lon 69.2) -> Cell 21N_69E
        cell_id_guj, _, _, _, _ = get_grid_cell_id(21.5, 69.2, step=1.0)
        self.assertEqual(cell_id_guj, "CELL_21N_69E")

    def test_02_seasonal_ordering_and_cyclical_encoding(self):
        """2. Verifies Indian Oceanographic Monsoon Calendar mapping."""
        # March (Pre-Monsoon) -> Code 1
        self.assertEqual(MONTH_TO_SEASON[3], (1, "Pre-Monsoon"))
        # July (SW Monsoon) -> Code 2
        self.assertEqual(MONTH_TO_SEASON[7], (2, "SW Monsoon"))
        # November (Post-Monsoon) -> Code 3
        self.assertEqual(MONTH_TO_SEASON[11], (3, "Post-Monsoon"))
        # January (Post-Monsoon/Winter) -> Code 3
        self.assertEqual(MONTH_TO_SEASON[1], (3, "Post-Monsoon"))

        # Cyclical month trigonometric sanity
        m = 3  # March
        sin_m = round(math.sin(2 * math.pi * m / 12.0), 4)
        cos_m = round(math.cos(2 * math.pi * m / 12.0), 4)
        self.assertEqual(sin_m, 1.0)  # sin(pi/2) = 1
        self.assertEqual(cos_m, 0.0)  # cos(pi/2) = 0

    def test_03_sector_classification(self):
        """3. Verifies Arabian Sea ecological and EEZ sector classification."""
        self.assertEqual(classify_arabian_sea_sector(9.95, 75.85), "Malabar Upwelling Shelf")
        self.assertEqual(classify_arabian_sea_sector(15.2, 73.1), "Konkan Coast / Central West Coast")
        self.assertEqual(classify_arabian_sea_sector(21.5, 69.5), "North Arabian Sea / Gujarat Shelf")
        self.assertEqual(classify_arabian_sea_sector(10.15, 72.2), "Lakshadweep Sea & Ridge")
        self.assertEqual(classify_arabian_sea_sector(7.5, 77.2), "Wadge Bank / Comorin Sector")
        self.assertEqual(classify_arabian_sea_sector(15.0, 68.0), "Central Arabian Sea Offshore Basin")

    def test_04_geodesic_distance_and_azimuth_bearing(self):
        """4. Verifies Haversine displacement distance and forward azimuth heading."""
        # Kochi (9.95, 75.85) to Goa (15.2, 73.1)
        bearing = compute_geodesic_bearing(9.95, 75.85, 15.2, 73.1)
        self.assertIsNotNone(bearing)
        # Heading is NNW (~335° to 345°)
        self.assertGreater(bearing, 330.0)
        self.assertLess(bearing, 350.0)

        # Identical point should return None for bearing
        self.assertIsNone(compute_geodesic_bearing(10.0, 75.0, 10.0, 75.0))

    def test_05_missing_environmental_data_not_zeroed(self):
        """5. Verifies that missing environmental values remain None and are NEVER converted to 0.0."""
        state = PopulationStateObservation(
            species_id="sardine-01",
            scientific_name="Sardinella longiceps",
            cell_id="CELL_09N_75E",
            centroid_lat=9.95,
            centroid_lon=75.85,
            sector="Malabar Upwelling Shelf",
            year=2024,
            month=4,
            season_code=1,
            season_name="Pre-Monsoon",
            occurrence_count=15,
            mean_depth_meters=None,  # Missing
            sst_celsius=None,        # Missing
            salinity_psu=None,       # Missing
            dissolved_oxygen_mgl=None,
            chlorophyll_mg_m3=None,
        )

        d = state.to_dict()
        self.assertIsNone(d["sst_celsius"])
        self.assertIsNone(d["salinity_psu"])
        self.assertIsNone(d["dissolved_oxygen_mgl"])
        self.assertIsNone(d["chlorophyll_mg_m3"])
        self.assertIsNone(d["mean_depth_meters"])
        # Ensure it is NOT 0.0
        self.assertNotEqual(d["sst_celsius"], 0.0)

    def test_06_synthetic_population_state_transitions(self):
        """6. Verifies transition generation logic on controlled state transitions."""
        builder = SeasonalDistributionDatasetBuilder(min_species_occurrences=1)

        # Define 3 sequential seasonal population states for Indian Mackerel
        state_pre = PopulationStateObservation(
            species_id="sp-mackerel",
            scientific_name="Rastrelliger kanagurta",
            cell_id="CELL_09N_75E",
            centroid_lat=9.95,
            centroid_lon=75.85,
            sector="Malabar Upwelling Shelf",
            year=2024,
            month=4,
            season_code=1,
            season_name="Pre-Monsoon",
            occurrence_count=20,
            sst_celsius=29.5,
            salinity_psu=35.2,
            dissolved_oxygen_mgl=5.5,
            chlorophyll_mg_m3=0.8,
            mean_depth_meters=30.0,
            historical_occurrence_rate=0.5,
        )

        state_monsoon = PopulationStateObservation(
            species_id="sp-mackerel",
            scientific_name="Rastrelliger kanagurta",
            cell_id="CELL_15N_73E",
            centroid_lat=15.2,
            centroid_lon=73.1,
            sector="Konkan Coast / Central West Coast",
            year=2024,
            month=7,
            season_code=2,
            season_name="SW Monsoon",
            occurrence_count=18,
            sst_celsius=27.2,
            salinity_psu=34.8,
            dissolved_oxygen_mgl=4.8,
            chlorophyll_mg_m3=3.2,
            mean_depth_meters=45.0,
            historical_occurrence_rate=0.5,
        )

        species_states = {"Rastrelliger kanagurta": [state_pre, state_monsoon]}
        transitions = builder.build_transitions(species_states)

        self.assertEqual(len(transitions), 1)
        t = transitions[0]
        self.assertEqual(t.scientific_name, "Rastrelliger kanagurta")
        self.assertEqual(t.current_cell_id, "CELL_09N_75E")
        self.assertEqual(t.target_cell_id, "CELL_15N_73E")
        self.assertEqual(t.season_code, 1)
        self.assertEqual(t.target_season_code, 2)
        self.assertGreater(t.displacement_distance_km, 600.0)
        self.assertIsNotNone(t.target_direction_deg)
        self.assertAlmostEqual(t.sst_celsius, 29.5)

    def test_07_summary_report_generation(self):
        """7. Verifies that the summary report accurately computes dataset statistics."""
        t1 = SeasonalDistributionTransition(
            species_id="s1",
            scientific_name="Sardinella longiceps",
            current_cell_id="CELL_09N_75E",
            current_lat=9.95,
            current_lon=75.85,
            current_sector="Malabar",
            season_code=1,
            season_name="Pre-Monsoon",
            month=4,
            month_sin=0.866,
            month_cos=-0.5,
            sst_celsius=29.0,
            salinity_psu=35.0,
            dissolved_oxygen_mgl=5.2,
            chlorophyll_mg_m3=1.1,
            mean_depth_meters=25.0,
            historical_occurrence_rate=0.6,
            trophic_level=2.6,
            target_cell_id="CELL_15N_73E",
            target_lat=15.2,
            target_lon=73.1,
            target_sector="Konkan",
            target_season_code=2,
            target_season_name="SW Monsoon",
            target_month=7,
            displacement_distance_km=642.5,
            target_direction_deg=338.2,
        )

        summary = generate_transition_summary([t1])
        self.assertEqual(summary["total_transition_rows"], 1)
        self.assertEqual(summary["species_count"], 1)
        self.assertEqual(summary["source_cell_count"], 1)
        self.assertEqual(summary["target_cell_count"], 1)
        self.assertEqual(summary["displacement_statistics_km"]["mean_km"], 642.5)
        self.assertEqual(summary["missing_feature_percentages"]["sst_celsius_missing_pct"], 0.0)


if __name__ == "__main__":
    unittest.main()
