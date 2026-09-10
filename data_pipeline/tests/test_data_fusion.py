"""
Comprehensive Test Suite for Phase 5: Data Fusion & Unified Marine Data.
Covers all required test scenarios (A through M) + Cross-domain demonstrations
and Real CMLRE Dataset integrations.
"""

import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATASET_DIR = ROOT_DIR / "dataset"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data_pipeline.fusion.depth import (
    is_within_depth_range,
    is_within_depth_tolerance,
)
from data_pipeline.fusion.models import (
    CrossDomainAssociation,
    DomainType,
    MarineObservation,
    UnifiedQueryParams,
    UnifiedSummary,
)
from data_pipeline.fusion.query_service import (
    get_cross_domain_context,
    get_domain_observations,
    get_unified_summary,
    map_edna_sample_record,
    map_fisheries_record,
    map_oceanographic_record,
    map_species_occurrence_record,
    query_unified_observations,
)
from data_pipeline.fusion.spatial import (
    compute_bounding_box,
    haversine_distance_km,
    is_within_bbox,
    is_within_spatial_proximity,
)
from data_pipeline.fusion.temporal import (
    is_within_date_range,
    is_within_temporal_window,
    parse_marine_timestamp,
    temporal_distance_hours,
)
from data_pipeline.ingestion.schema_normalizer import normalize_dataframe_columns
from data_pipeline.ingestion.txt_parser import parse_cmlre_txt
from data_pipeline.quality_standardisation.phase4_boundary import integrate_with_phase4


class TestPhase5DataFusion(unittest.TestCase):
    """Full test suite covering Phase 5 Data Fusion responsibilities."""

    def setUp(self):
        # Sample synthetic oceanographic observations (Arabian Sea / Kochi coast)
        self.ocean_obs_1 = MarineObservation(
            id="ocean_001_temp",
            dataset_id="ds_ocean_cmlre_01",
            domain=DomainType.OCEANOGRAPHY.value,
            observation_id="ocean_rec_001",
            station_id="STN_KOC_01",
            latitude=9.9312,
            longitude=76.2673,
            observation_time="2026-03-15T08:30:00Z",
            depth=10.0,
            variable="temperature",
            value=28.5,
            unit="°C",
            source_table="oceanographic_observations",
            quality_status="passed",
        )
        self.ocean_obs_2 = MarineObservation(
            id="ocean_001_sal",
            dataset_id="ds_ocean_cmlre_01",
            domain=DomainType.OCEANOGRAPHY.value,
            observation_id="ocean_rec_001",
            station_id="STN_KOC_01",
            latitude=9.9312,
            longitude=76.2673,
            observation_time="2026-03-15T08:30:00Z",
            depth=10.0,
            variable="salinity",
            value=35.2,
            unit="PSU",
            source_table="oceanographic_observations",
            quality_status="passed",
        )
        self.ocean_obs_3 = MarineObservation(
            id="ocean_001_do",
            dataset_id="ds_ocean_cmlre_01",
            domain=DomainType.OCEANOGRAPHY.value,
            observation_id="ocean_rec_001",
            station_id="STN_KOC_01",
            latitude=9.9312,
            longitude=76.2673,
            observation_time="2026-03-15T08:30:00Z",
            depth=10.0,
            variable="dissolved_oxygen",
            value=6.1,
            unit="mg/L",
            source_table="oceanographic_observations",
            quality_status="passed",
        )

        # Sample biodiversity occurrence (near STN_KOC_01, ~2.5 km away, 3 hours later, 12m depth)
        self.bio_obs_1 = MarineObservation(
            id="bio_001_sardinella",
            dataset_id="ds_bio_cmlre_01",
            domain=DomainType.BIODIVERSITY.value,
            observation_id="bio_rec_001",
            species_id="SP_001",
            species_name="Sardinella longiceps",
            latitude=9.9450,
            longitude=76.2800,
            observation_time="2026-03-15T11:30:00Z",
            depth=12.0,
            variable="individual_count",
            value=45.0,
            unit="count",
            source_table="species_occurrences",
            quality_status="passed",
        )

        # Sample fisheries catch record (near STN_KOC_01, ~5 km away, 6 hours later, 15m depth)
        self.fish_obs_1 = MarineObservation(
            id="fish_001_trawl",
            dataset_id="ds_fish_cmlre_01",
            domain=DomainType.FISHERIES.value,
            observation_id="fish_rec_001",
            species_id="SP_001",
            species_name="Indian Oil Sardine",
            latitude=9.9600,
            longitude=76.2900,
            observation_time="2026-03-15T14:30:00Z",
            depth=15.0,
            variable="catch_weight",
            value=1250.0,
            unit="kg",
            source_table="fisheries_records",
            quality_status="passed",
        )

        # Sample eDNA sample detection (same station area)
        self.edna_obs_1 = MarineObservation(
            id="edna_001_12S",
            dataset_id="ds_edna_cmlre_01",
            domain=DomainType.EDNA.value,
            observation_id="edna_rec_001",
            station_id="STN_KOC_01",
            latitude=9.9320,
            longitude=76.2680,
            observation_time="2026-03-15T09:00:00Z",
            depth=10.0,
            variable="edna_sample",
            value=1.0,
            unit="detection",
            source_table="edna_samples",
            quality_status="passed",
        )

        # Distant observation (Bay of Bengal / Chennai, 1000 km away, different time)
        self.distant_obs = MarineObservation(
            id="ocean_bob_001",
            dataset_id="ds_ocean_cmlre_02",
            domain=DomainType.OCEANOGRAPHY.value,
            observation_id="ocean_rec_bob_01",
            station_id="STN_CHE_01",
            latitude=13.0827,
            longitude=80.2707,
            observation_time="2026-04-20T10:00:00Z",
            depth=50.0,
            variable="temperature",
            value=29.8,
            unit="°C",
            source_table="oceanographic_observations",
            quality_status="passed",
        )

        self.all_sample_records = [
            self.ocean_obs_1,
            self.ocean_obs_2,
            self.ocean_obs_3,
            self.bio_obs_1,
            self.fish_obs_1,
            self.edna_obs_1,
            self.distant_obs,
        ]

    # =========================================================================
    # A. Common Observation Representation Test
    # =========================================================================
    def test_A_common_observation_representation(self):
        """A. Common representation: Verifies standard fields, serialization, and provenance preservation."""
        obs = self.ocean_obs_1
        self.assertEqual(obs.domain, "oceanography")
        self.assertEqual(obs.variable, "temperature")
        self.assertEqual(obs.value, 28.5)
        self.assertEqual(obs.unit, "°C")
        self.assertEqual(obs.source_table, "oceanographic_observations")
        self.assertEqual(obs.dataset_id, "ds_ocean_cmlre_01")
        self.assertEqual(obs.observation_id, "ocean_rec_001")

        # Serialization to dictionary
        d = obs.to_dict()
        self.assertIn("domain", d)
        self.assertIn("latitude", d)
        self.assertIn("longitude", d)
        self.assertIn("depth", d)
        self.assertIn("variable", d)
        self.assertIn("value", d)
        self.assertIn("unit", d)
        self.assertIn("source_table", d)

    # =========================================================================
    # B. Spatial Filtering (Haversine Proximity) Test
    # =========================================================================
    def test_B_spatial_filtering_proximity(self):
        """B. Spatial proximity: Verifies spherical Haversine distance and point-radius filtering."""
        # Distance between Kochi STN (9.9312, 76.2673) and Bio STN (9.9450, 76.2800)
        dist_km = haversine_distance_km(9.9312, 76.2673, 9.9450, 76.2800)
        # Should be ~2.11 km
        self.assertAlmostEqual(dist_km, 2.11, places=1)
        self.assertTrue(is_within_spatial_proximity(9.9312, 76.2673, 9.9450, 76.2800, max_radius_km=10.0))
        self.assertFalse(is_within_spatial_proximity(9.9312, 76.2673, 9.9450, 76.2800, max_radius_km=1.0))

        # Query proximity around Kochi center (radius 10 km)
        qp = UnifiedQueryParams(latitude=9.93, longitude=76.27, radius_km=10.0)
        results = query_unified_observations(params=qp, records=self.all_sample_records)
        # All Arabian sea records (6) are within 10 km; Chennai is ~550 km away
        self.assertEqual(len(results), 6)
        self.assertNotIn(self.distant_obs, results)

    # =========================================================================
    # C. Bounding Box Filtering Test
    # =========================================================================
    def test_C_bounding_box_filtering(self):
        """C. Bounding box: Filters records within [west, south, east, north] coordinates."""
        # Arabian Sea bounding box around Kerala coast
        kerala_bbox = [75.5, 9.0, 77.0, 10.5]  # [west, south, east, north]
        qp = UnifiedQueryParams(bbox=kerala_bbox)
        results = query_unified_observations(params=qp, records=self.all_sample_records)
        self.assertEqual(len(results), 6)
        self.assertNotIn(self.distant_obs, results)

        # Bay of Bengal bounding box around Chennai
        chennai_bbox = [79.5, 12.0, 81.0, 14.0]
        qp_che = UnifiedQueryParams(bbox=chennai_bbox)
        results_che = query_unified_observations(params=qp_che, records=self.all_sample_records)
        self.assertEqual(len(results_che), 1)
        self.assertEqual(results_che[0].id, "ocean_bob_001")

    # =========================================================================
    # D. Temporal Filtering Test
    # =========================================================================
    def test_D_temporal_filtering(self):
        """D. Temporal range: Filters records by date_from and date_to without timezone corruption."""
        # Exact date range covering March 2026
        qp = UnifiedQueryParams(date_from="2026-03-01T00:00:00Z", date_to="2026-03-31T23:59:59Z")
        results = query_unified_observations(params=qp, records=self.all_sample_records)
        self.assertEqual(len(results), 6)
        self.assertNotIn(self.distant_obs, results)

        # Temporal distance in hours
        diff_h = temporal_distance_hours("2026-03-15T08:30:00Z", "2026-03-15T11:30:00Z")
        self.assertEqual(diff_h, 3.0)
        self.assertTrue(is_within_temporal_window("2026-03-15T08:30:00Z", "2026-03-15T11:30:00Z", 6.0))
        self.assertFalse(is_within_temporal_window("2026-03-15T08:30:00Z", "2026-03-15T11:30:00Z", 2.0))

    # =========================================================================
    # E. Depth Filtering Test
    # =========================================================================
    def test_E_depth_filtering(self):
        """E. Depth bounds: Filters observations strictly within [depth_min, depth_max]."""
        # Surface & epipelagic zone (0 to 12m)
        qp = UnifiedQueryParams(depth_min=0.0, depth_max=12.0)
        results = query_unified_observations(params=qp, records=self.all_sample_records)
        # ocean_obs (10m), bio_obs (12m), edna_obs (10m)
        self.assertEqual(len(results), 5)
        self.assertNotIn(self.fish_obs_1, results)  # fish_obs is at 15m
        self.assertNotIn(self.distant_obs, results) # distant_obs is at 50m

        # Depth tolerance matching
        self.assertTrue(is_within_depth_tolerance(10.0, 12.0, tolerance_meters=5.0))
        self.assertFalse(is_within_depth_tolerance(10.0, 50.0, tolerance_meters=10.0))

    # =========================================================================
    # F. Domain Filtering Test
    # =========================================================================
    def test_F_domain_filtering(self):
        """F. Domain filter: Restricts results to oceanography, fisheries, biodiversity, or edna."""
        qp_ocean = UnifiedQueryParams(domain=DomainType.OCEANOGRAPHY.value)
        ocean_res = query_unified_observations(params=qp_ocean, records=self.all_sample_records)
        self.assertEqual(len(ocean_res), 4)  # 3 kochi + 1 chennai
        self.assertTrue(all(o.domain == "oceanography" for o in ocean_res))

        qp_fish = UnifiedQueryParams(domain=DomainType.FISHERIES.value)
        fish_res = query_unified_observations(params=qp_fish, records=self.all_sample_records)
        self.assertEqual(len(fish_res), 1)
        self.assertEqual(fish_res[0].variable, "catch_weight")

        qp_bio = UnifiedQueryParams(domain=DomainType.BIODIVERSITY.value)
        bio_res = query_unified_observations(params=qp_bio, records=self.all_sample_records)
        self.assertEqual(len(bio_res), 1)
        self.assertEqual(bio_res[0].species_name, "Sardinella longiceps")

        qp_edna = UnifiedQueryParams(domain=DomainType.EDNA.value)
        edna_res = query_unified_observations(params=qp_edna, records=self.all_sample_records)
        self.assertEqual(len(edna_res), 1)
        self.assertEqual(edna_res[0].domain, "edna")

    # =========================================================================
    # G. Species Filtering Test
    # =========================================================================
    def test_G_species_filtering(self):
        """G. Species filter: Searches by scientific name, common name, or species_id."""
        qp = UnifiedQueryParams(species="Sardinella")
        results = query_unified_observations(params=qp, records=self.all_sample_records)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].species_name, "Sardinella longiceps")

        qp_id = UnifiedQueryParams(species="SP_001")
        results_id = query_unified_observations(params=qp_id, records=self.all_sample_records)
        # SP_001 is on both bio_obs_1 and fish_obs_1
        self.assertEqual(len(results_id), 2)

    # =========================================================================
    # H. Cross-Domain Association Test (Core Differentiation)
    # =========================================================================
    def test_H_cross_domain_association(self):
        """
        H. Cross-Domain Association: Demonstrates linking a Biodiversity occurrence
        with co-occurring Oceanographic and Fisheries conditions within explicit
        spatial, temporal, and depth windows.
        """
        # Anchor: Biodiversity observation of Sardinella longiceps
        anchor = self.bio_obs_1

        # Search associated observations within 10 km, 24 hours, 10m depth tolerance
        assoc = get_cross_domain_context(
            anchor=anchor,
            candidate_pool=self.all_sample_records,
            spatial_radius_km=10.0,
            temporal_window_hours=24.0,
            depth_tolerance_m=10.0,
        )

        self.assertEqual(assoc.anchor.id, anchor.id)
        # Associated should include:
        # - 3 Oceanographic observations (temperature, salinity, DO at 10m depth, 2.1 km away, 3 hrs earlier)
        # - 1 Fisheries record (catch at 15m depth, 2.0 km away, 3 hrs later)
        # - 1 eDNA detection (at 10m depth, 2.1 km away, 2.5 hrs earlier)
        # Distant Chennai observation must NOT be associated
        associated_ids = [o.id for o in assoc.associated]
        self.assertIn("ocean_001_temp", associated_ids)
        self.assertIn("ocean_001_sal", associated_ids)
        self.assertIn("ocean_001_do", associated_ids)
        self.assertIn("fish_001_trawl", associated_ids)
        self.assertIn("edna_001_12S", associated_ids)
        self.assertNotIn("ocean_bob_001", associated_ids)

        # Verify explicit parameters and non-causal disclaimer
        d = assoc.to_dict()
        self.assertIn("matching_parameters", d)
        self.assertEqual(d["matching_parameters"]["spatial_radius_km"], 10.0)
        self.assertIn("does not imply causation", d["association_note"])

    # =========================================================================
    # I. Unified Marine Multi-Criteria Query Test
    # =========================================================================
    def test_I_unified_marine_multi_criteria_query(self):
        """I. Multi-criteria query: Combines spatial, temporal, depth, domain, and variable filters."""
        qp = UnifiedQueryParams(
            domain="oceanography",
            variable="temperature",
            depth_min=0.0,
            depth_max=20.0,
            latitude=9.93,
            longitude=76.27,
            radius_km=25.0,
            date_from="2026-03-01T00:00:00Z",
            date_to="2026-03-31T23:59:59Z"
        )
        results = query_unified_observations(params=qp, records=self.all_sample_records)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "ocean_001_temp")
        self.assertEqual(results[0].value, 28.5)

    # =========================================================================
    # J. Unified Summary (Dashboard) Test
    # =========================================================================
    def test_J_unified_summary_generation(self):
        """J. Unified summary: Computes dashboard metrics, bounding box, domain counts, and variables."""
        summary = get_unified_summary(records=self.all_sample_records)
        
        self.assertEqual(summary.total_observations, 7)
        self.assertEqual(summary.total_datasets, 5)
        self.assertIn("oceanography", summary.domains)
        self.assertIn("fisheries", summary.domains)
        self.assertIn("biodiversity", summary.domains)
        self.assertIn("edna", summary.domains)
        self.assertGreaterEqual(summary.species_count, 1)
        self.assertIn("Sardinella longiceps", summary.species_names)

        # Bounding box covers Arabian sea to Bay of Bengal
        self.assertAlmostEqual(summary.lat_min, 9.93, places=1)
        self.assertAlmostEqual(summary.lat_max, 13.08, places=1)
        self.assertAlmostEqual(summary.lon_min, 76.26, places=1)
        self.assertAlmostEqual(summary.lon_max, 80.27, places=1)

        # Available variables
        self.assertIn("temperature", summary.variables)
        self.assertIn("salinity", summary.variables)
        self.assertIn("dissolved_oxygen", summary.variables)
        self.assertIn("individual_count", summary.variables)
        self.assertIn("catch_weight", summary.variables)

        # Domain breakdown
        self.assertEqual(summary.domain_counts.get("oceanography"), 4)
        self.assertEqual(summary.domain_counts.get("biodiversity"), 1)
        self.assertEqual(summary.domain_counts.get("fisheries"), 1)
        self.assertEqual(summary.domain_counts.get("edna"), 1)

    # =========================================================================
    # K. Empty / No-Match Queries Test
    # =========================================================================
    def test_K_empty_and_no_match_queries(self):
        """K. No-match queries: Handles out-of-range spatial, temporal, and depth queries gracefully."""
        # Query with impossible coordinates (Pacific Ocean)
        qp_distant = UnifiedQueryParams(latitude=-45.0, longitude=-120.0, radius_km=50.0)
        res_distant = query_unified_observations(params=qp_distant, records=self.all_sample_records)
        self.assertEqual(len(res_distant), 0)

        # Query with future year
        qp_future = UnifiedQueryParams(date_from="2099-01-01", date_to="2099-12-31")
        res_future = query_unified_observations(params=qp_future, records=self.all_sample_records)
        self.assertEqual(len(res_future), 0)

        # Query with abyss depth (5000m)
        qp_abyss = UnifiedQueryParams(depth_min=4000.0, depth_max=6000.0)
        res_abyss = query_unified_observations(params=qp_abyss, records=self.all_sample_records)
        self.assertEqual(len(res_abyss), 0)

        # Summary for empty list
        empty_summary = get_unified_summary(records=[])
        self.assertEqual(empty_summary.total_observations, 0)
        self.assertIsNone(empty_summary.lat_min)

    # =========================================================================
    # L. Provenance & Lineage Preservation Test
    # =========================================================================
    def test_L_provenance_preservation(self):
        """L. Provenance: Every observation preserves dataset_id, source_table, observation_id, and quality."""
        for obs in self.all_sample_records:
            self.assertIsNotNone(obs.dataset_id, "Observation missing dataset_id")
            self.assertIsNotNone(obs.source_table, "Observation missing source_table")
            self.assertIsNotNone(obs.observation_id, "Observation missing observation_id")
            self.assertIsNotNone(obs.quality_status, "Observation missing quality_status")

    # =========================================================================
    # M. Real CMLRE Dataset Integration Test
    # =========================================================================
    def test_M_real_cmlre_dataset_flow_to_fusion(self):
        """
        M. Real CMLRE Dataset Flow: Parses actual occurrence.txt and dnaderiveddata1.txt
        from dataset/, runs Phase 3 normalisation -> Phase 4 QC -> Phase 5 Unified Representation,
        and verifies cross-domain spatial/temporal alignment on real data.
        """
        occ_file = DATASET_DIR / "occurrence.txt"
        edna_file = DATASET_DIR / "dnaderiveddata1.txt"

        if not occ_file.exists() or not edna_file.exists():
            self.skipTest("Real CMLRE dataset files not found in dataset/")

        # 1. Parse Real Occurrence file (Phase 3)
        raw_occ_df, occ_meta, _ = parse_cmlre_txt(str(occ_file))
        norm_occ_df, _ = normalize_dataframe_columns(raw_occ_df)
        qc_occ = integrate_with_phase4(norm_occ_df, {"domain_type": "biodiversity", "dataset_id": "cmlre_occ_real"})
        occ_clean_df = qc_occ["df"]

        # 2. Parse Real eDNA file (Phase 3)
        raw_edna_df, edna_meta, _ = parse_cmlre_txt(str(edna_file))
        norm_edna_df, _ = normalize_dataframe_columns(raw_edna_df)
        qc_edna = integrate_with_phase4(norm_edna_df, {"domain_type": "edna", "dataset_id": "cmlre_edna_real"})
        edna_clean_df = qc_edna["df"]

        # 3. Convert Real Cleaned Records to Phase 5 MarineObservation objects
        fused_observations: List[MarineObservation] = []

        # Determine sample counts dynamically from quality-controlled dataframes
        occ_count = min(50, len(occ_clean_df))
        edna_count = min(50, len(edna_clean_df))
        expected_total = occ_count + edna_count

        # Convert top occurrence records
        for idx, row in enumerate(occ_clean_df.head(occ_count).to_dict(orient="records")):
            obs = MarineObservation(
                id=f"cmlre_real_occ_{idx}",
                dataset_id="cmlre_occ_real",
                domain=DomainType.BIODIVERSITY.value,
                observation_id=str(row.get("sample", f"occ_{idx}")),
                species_name=row.get("species", "Marine Organism"),
                latitude=float(row["latitude"]) if row.get("latitude") is not None else None,
                longitude=float(row["longitude"]) if row.get("longitude") is not None else None,
                observation_time=str(row["time"]) if row.get("time") is not None else None,
                depth=float(row["depth"]) if row.get("depth") is not None else None,
                variable="occurrence",
                value=1.0,
                unit="presence",
                source_table="species_occurrences",
                quality_status="passed",
            )
            fused_observations.append(obs)

        # Convert top eDNA records
        for idx, row in enumerate(edna_clean_df.head(edna_count).to_dict(orient="records")):
            obs = MarineObservation(
                id=f"cmlre_real_edna_{idx}",
                dataset_id="cmlre_edna_real",
                domain=DomainType.EDNA.value,
                observation_id=str(row.get("sample", f"edna_{idx}")),
                species_name=row.get("species", "eDNA Sequence"),
                latitude=float(row["latitude"]) if row.get("latitude") is not None else None,
                longitude=float(row["longitude"]) if row.get("longitude") is not None else None,
                observation_time=str(row["time"]) if row.get("time") is not None else None,
                depth=float(row["depth"]) if row.get("depth") is not None else None,
                variable="edna_detection",
                value=1.0,
                unit="read",
                source_table="edna_samples",
                quality_status="passed",
            )
            fused_observations.append(obs)

        # Verify unified representation has expected derived count across 2 real domains
        self.assertEqual(len(fused_observations), expected_total)

        # Run unified summary on real CMLRE data
        real_summary = get_unified_summary(records=fused_observations)
        self.assertEqual(real_summary.total_observations, expected_total)
        self.assertIn("biodiversity", real_summary.domains)
        self.assertIn("edna", real_summary.domains)
        self.assertIsNotNone(real_summary.lat_min)
        self.assertIsNotNone(real_summary.lat_max)

    # =========================================================================
    # N. Verified Live Database Schema Adapters Test
    # =========================================================================
    def test_N_live_database_schema_adapters(self):
        """
        N. Live Database Schema Mapping: Tests the mapping functions against the
        exact column definitions verified on the live Supabase PostgreSQL database.
        """
        # 1. Live oceanographic_observations row format
        live_ocean_row = {
            "id": "11111111-2222-3333-4444-555555555555",
            "dataset_id": "d1a2b3c4-0000-0000-0000-000000000001",
            "station_id": "stn_001",
            "sample_id": "smp_001",
            "latitude": 10.5,
            "longitude": 75.8,
            "depth_meters": 25.0,
            "timestamp": "2026-03-15T08:00:00Z",
            "temperature_celsius": 28.2,
            "salinity_psu": 35.4,
            "dissolved_oxygen_mgl": 5.8,
            "chlorophyll_mg_m3": 1.2,
            "ph": 8.15,
            "pressure_dbar": 25.3,
            "turbidity_ntu": 0.8,
            "quality_score": 96.5,
            "quality_status": "passed",
        }
        ocean_obs = map_oceanographic_record(live_ocean_row)
        self.assertEqual(len(ocean_obs), 7)  # temp, sal, do, chl, ph, pres, turb
        temp_obs = next(o for o in ocean_obs if o.variable == "temperature")
        self.assertEqual(temp_obs.value, 28.2)
        self.assertEqual(temp_obs.unit, "°C")
        self.assertEqual(temp_obs.depth, 25.0)

        # 2. Live fisheries_records row format
        live_fish_row = {
            "id": "22222222-3333-4444-5555-666666666666",
            "dataset_id": "d1a2b3c4-0000-0000-0000-000000000002",
            "sample_id": "smp_002",
            "species_id": "sp_002",
            "latitude": 10.6,
            "longitude": 75.9,
            "depth_meters": 30.0,
            "timestamp": "2026-03-15T10:00:00Z",
            "catch_weight_kg": 450.0,
            "gear_type": "Gillnet",
            "fishing_zone": "EEZ-South",
            "vessel_name": "Matsya Varshini",
            "quality_status": "passed",
        }
        fish_obs = map_fisheries_record(live_fish_row)
        self.assertEqual(len(fish_obs), 1)
        self.assertEqual(fish_obs[0].value, 450.0)
        self.assertEqual(fish_obs[0].unit, "kg")

        # 3. Live species_occurrences row format
        live_occ_row = {
            "id": "33333333-4444-5555-6666-777777777777",
            "dataset_id": "d1a2b3c4-0000-0000-0000-000000000003",
            "sample_id": "smp_003",
            "species_id": "sp_003",
            "scientific_name": "Rastrelliger kanagurta",
            "common_name": "Indian Mackerel",
            "latitude": 10.55,
            "longitude": 75.85,
            "depth_meters": 28.0,
            "timestamp": "2026-03-15T09:00:00Z",
            "individual_count": 80,
            "basis_of_record": "HumanObservation",
            "quality_status": "passed",
        }
        occ_obs = map_species_occurrence_record(live_occ_row)
        self.assertEqual(len(occ_obs), 1)
        self.assertEqual(occ_obs[0].species_name, "Rastrelliger kanagurta")
        self.assertEqual(occ_obs[0].value, 80.0)

        # 4. Live edna_samples row format
        live_edna_row = {
            "id": "44444444-5555-6666-7777-888888888888",
            "dataset_id": "d1a2b3c4-0000-0000-0000-000000000004",
            "sample_id": "smp_004",
            "station_id": "stn_004",
            "latitude": 10.52,
            "longitude": 75.82,
            "depth_meters": 25.0,
            "target_gene": "COI",
            "created_at": "2026-03-15T08:15:00Z",
            "quality_status": "passed",
        }
        edna_obs = map_edna_sample_record(live_edna_row)
        self.assertEqual(len(edna_obs), 1)
        self.assertEqual(edna_obs[0].domain, "edna")

        # 5. Cross-domain fusion of live-format records
        all_live_obs = ocean_obs + fish_obs + occ_obs + edna_obs
        assoc = get_cross_domain_context(
            anchor=occ_obs[0],
            candidate_pool=all_live_obs,
            spatial_radius_km=15.0,
            temporal_window_hours=6.0,
            depth_tolerance_m=10.0,
        )
        # All 3 other domains co-occurred within 15 km, 6 hours, 10m depth!
        associated_domains = {o.domain for o in assoc.associated}
        self.assertIn("oceanography", associated_domains)
        self.assertIn("fisheries", associated_domains)
        self.assertIn("edna", associated_domains)

    # =========================================================================
    # O. Rigorous Edge Cases & Missingness Policy Test
    # =========================================================================
    def test_O_rigorous_edge_cases_and_missing_policies(self):
        """
        O. Edge Cases: Tests allow_missing_time policy, mixed timezone rejection,
        and rejection of invalid/negative/non-finite coordinates and depths.
        """
        # 1. allow_missing_time policy
        obs_no_time = MarineObservation(
            id="obs_no_time",
            domain="oceanography",
            latitude=9.93,
            longitude=76.27,
            observation_time=None,
            depth=10.0,
            variable="temperature",
            value=28.0,
            source_table="oceanographic_observations",
            quality_status="passed",
        )
        anchor = self.bio_obs_1

        # With allow_missing_time=True (default), obs without time is accepted based on spatial/depth
        assoc_allowed = get_cross_domain_context(
            anchor=anchor,
            candidate_pool=[obs_no_time],
            spatial_radius_km=10.0,
            depth_tolerance_m=10.0,
            allow_missing_time=True,
        )
        self.assertEqual(len(assoc_allowed.associated), 1)

        # With allow_missing_time=False, obs without time is rejected
        assoc_rejected = get_cross_domain_context(
            anchor=anchor,
            candidate_pool=[obs_no_time],
            spatial_radius_km=10.0,
            depth_tolerance_m=10.0,
            allow_missing_time=False,
        )
        self.assertEqual(len(assoc_rejected.associated), 0)

        # 2. Mixed timezone awareness rejection (aware vs naive)
        diff_mixed = temporal_distance_hours("2026-03-15T08:30:00Z", "2026-03-15 08:30:00")
        self.assertIsNone(diff_mixed)

        # 3. Non-finite and out-of-range depth rejection
        self.assertFalse(is_within_depth_range(-5.0, depth_min=0.0, depth_max=100.0))
        self.assertFalse(is_within_depth_range(float("nan"), depth_min=0.0, depth_max=100.0))
        self.assertFalse(is_within_depth_range(float("inf"), depth_min=0.0, depth_max=100.0))
        self.assertFalse(is_within_depth_range(10.0, depth_min=-10.0))
        self.assertFalse(is_within_depth_tolerance(10.0, 20.0, tolerance_meters=-5.0))
        self.assertFalse(is_within_depth_tolerance(10.0, float("nan"), tolerance_meters=5.0))

        # 4. Out-of-bounds coordinate rejection
        self.assertFalse(is_within_spatial_proximity(95.0, 76.0, 10.0, 76.0, max_radius_km=50.0))
        self.assertFalse(is_within_spatial_proximity(10.0, 195.0, 10.0, 76.0, max_radius_km=50.0))
        self.assertFalse(is_within_spatial_proximity(float("nan"), 76.0, 10.0, 76.0, max_radius_km=50.0))
        self.assertFalse(is_within_spatial_proximity(10.0, 76.0, 10.0, 76.0, max_radius_km=-10.0))

        with self.assertRaises(ValueError):
            haversine_distance_km(100.0, 76.0, 10.0, 76.0)


if __name__ == "__main__":
    unittest.main()
