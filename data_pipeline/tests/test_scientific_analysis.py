"""
Comprehensive Test Suite for Phase 6: Scientific Analysis.
Tests oceanographic trends, fisheries trends, species distribution, biodiversity indicators,
spatial grid binning, temporal dynamics, cross-domain correlations, ecosystem relationships,
mathematical accuracy, numerical guards, and real CMLRE dataset integration.
"""

from datetime import datetime
import math
import os
from pathlib import Path
import sys
import unittest
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data_pipeline.analysis import (
    BiodiversityResult,
    CorrelationResult,
    EcosystemRelationshipResult,
    FisheriesTrendResult,
    OceanTrendResult,
    ScientificAnalysisService,
    SpatialAnalysisResult,
    SpeciesDistributionResult,
    TemporalAnalysisResult,
    analyze_ecosystem_relationship,
    analyze_fisheries_trends,
    analyze_ocean_trends,
    analyze_spatial_distribution,
    analyze_species_distribution,
    analyze_temporal_dynamics,
    calculate_biodiversity_indicators,
    calculate_cross_domain_correlation,
    pair_cross_domain_observations,
)
from data_pipeline.fusion.models import DomainType, MarineObservation, UnifiedQueryParams
from data_pipeline.ingestion.schema_normalizer import normalize_dataframe_columns
from data_pipeline.ingestion.txt_parser import parse_cmlre_txt
from data_pipeline.quality_standardisation.phase4_boundary import integrate_with_phase4


class TestPhase6ScientificAnalysis(unittest.TestCase):
    """Full test suite covering Phase 6 Scientific Analysis responsibilities."""

    def test_A_oceanographic_trend_analysis(self):
        """A. Oceanographic trends: Verifies monthly aggregation, mean, min, max, std, and slope."""
        obs_list = [
            MarineObservation(
                domain=DomainType.OCEANOGRAPHY.value,
                variable="temperature",
                value=26.0,
                observation_time="2026-01-10T10:00:00Z",
                depth=10.0,
                latitude=10.0,
                longitude=75.0,
            ),
            MarineObservation(
                domain=DomainType.OCEANOGRAPHY.value,
                variable="temperature",
                value=28.0,
                observation_time="2026-01-20T10:00:00Z",
                depth=15.0,
                latitude=10.5,
                longitude=75.5,
            ),
            MarineObservation(
                domain=DomainType.OCEANOGRAPHY.value,
                variable="temperature",
                value=30.0,
                observation_time="2026-02-15T10:00:00Z",
                depth=10.0,
                latitude=11.0,
                longitude=76.0,
            ),
            MarineObservation(
                domain=DomainType.OCEANOGRAPHY.value,
                variable="temperature",
                value=32.0,
                observation_time="2026-03-10T10:00:00Z",
                depth=10.0,
                latitude=11.5,
                longitude=76.5,
            ),
        ]

        result = analyze_ocean_trends(observations=obs_list, variable="temperature", time_aggregation="monthly")

        self.assertEqual(result.variable, "temperature")
        self.assertEqual(result.unit, "°C")
        self.assertEqual(result.data_points_count, 4)
        self.assertAlmostEqual(result.overall_mean, 29.0, places=2)
        self.assertEqual(result.overall_min, 26.0)
        self.assertEqual(result.overall_max, 32.0)
        self.assertEqual(len(result.time_series), 3)  # Jan (2), Feb (1), Mar (1)
        self.assertEqual(result.time_series[0].period, "2026-01")
        self.assertAlmostEqual(result.time_series[0].mean, 27.0, places=2)
        self.assertEqual(result.trend_direction, "increasing")
        self.assertIsNotNone(result.trend_slope)
        self.assertGreater(result.trend_slope, 0.0)

    def test_B_fisheries_trend_analysis(self):
        """B. Fisheries trends: Verifies catch totals, averages, species allocations, and effort disclaimer."""
        obs_list = [
            MarineObservation(
                domain=DomainType.FISHERIES.value,
                variable="catch_weight_kg",
                value=150.5,
                species_name="Rastrelliger kanagurta",
                observation_time="2026-02-01T06:00:00Z",
                latitude=9.5,
                longitude=76.2,
            ),
            MarineObservation(
                domain=DomainType.FISHERIES.value,
                variable="catch_weight_kg",
                value=249.5,
                species_name="Sardinella longiceps",
                observation_time="2026-02-10T06:00:00Z",
                latitude=9.8,
                longitude=76.1,
            ),
            MarineObservation(
                domain=DomainType.FISHERIES.value,
                variable="catch_weight_kg",
                value=100.0,
                species_name="Rastrelliger kanagurta",
                observation_time="2026-03-01T06:00:00Z",
                latitude=10.1,
                longitude=75.9,
            ),
        ]

        result = analyze_fisheries_trends(observations=obs_list, time_aggregation="monthly")

        self.assertEqual(result.records_count, 3)
        self.assertAlmostEqual(result.total_catch_kg, 500.0, places=2)
        self.assertAlmostEqual(result.avg_catch_kg, 166.67, places=2)
        self.assertEqual(result.species_breakdown["Rastrelliger kanagurta"], 250.5)
        self.assertEqual(result.species_breakdown["Sardinella longiceps"], 249.5)
        self.assertFalse(result.has_fishing_effort_data)
        self.assertIn("distinct from fishing effort", result.effort_notes)

    def test_C_species_distribution_analysis(self):
        """C. Species distribution: Calculates spatial points, species centroids, and depth extents."""
        obs_list = [
            MarineObservation(
                domain=DomainType.BIODIVERSITY.value,
                species_name="Nemipterus japonicus",
                latitude=10.0,
                longitude=75.0,
                depth=20.0,
                value=5,
            ),
            MarineObservation(
                domain=DomainType.BIODIVERSITY.value,
                species_name="Nemipterus japonicus",
                latitude=12.0,
                longitude=77.0,
                depth=60.0,
                value=15,
            ),
            MarineObservation(
                domain=DomainType.BIODIVERSITY.value,
                species_name="Epinephelus diacanthus",
                latitude=11.0,
                longitude=76.0,
                depth=40.0,
                value=2,
            ),
        ]

        result = analyze_species_distribution(observations=obs_list)

        self.assertEqual(result.total_occurrences, 22)
        self.assertEqual(result.unique_species_count, 2)
        self.assertEqual(len(result.spatial_points), 3)

        # Check centroid for Nemipterus japonicus
        nem = next(s for s in result.species_summary if s["species_name"] == "Nemipterus japonicus")
        self.assertEqual(nem["total_count"], 20)
        self.assertAlmostEqual(nem["lat_centroid"], 11.0, places=2)
        self.assertAlmostEqual(nem["lon_centroid"], 76.0, places=2)
        self.assertEqual(nem["depth_min_m"], 20.0)
        self.assertEqual(nem["depth_max_m"], 60.0)

        # Bounding box
        self.assertEqual(result.bounding_box["south"], 10.0)
        self.assertEqual(result.bounding_box["north"], 12.0)

    def test_D_biodiversity_indicators_mathematics(self):
        """D. Biodiversity indices: Verifies mathematical correctness of Shannon H', Simpson D, and Pielou J'."""
        # Ground truth test: 4 species, equal abundance (10 each)
        # S = 4, N = 40, p_i = 0.25
        # Shannon H' = -4 * (0.25 * ln(0.25)) = ln(4) ≈ 1.386294
        # Gini-Simpson 1 - D = 1 - 4 * (0.25^2) = 0.75
        # Pielou J' = H' / ln(S) = 1.386294 / ln(4) = 1.0
        obs_list = [
            MarineObservation(domain=DomainType.BIODIVERSITY.value, species_name="Species A", value=10),
            MarineObservation(domain=DomainType.BIODIVERSITY.value, species_name="Species B", value=10),
            MarineObservation(domain=DomainType.BIODIVERSITY.value, species_name="Species C", value=10),
            MarineObservation(domain=DomainType.BIODIVERSITY.value, species_name="Species D", value=10),
        ]

        result = calculate_biodiversity_indicators(observations=obs_list)

        self.assertEqual(result.species_richness, 4)
        self.assertEqual(result.observation_count, 40)
        self.assertAlmostEqual(result.shannon_index, 1.3863, places=3)
        self.assertAlmostEqual(result.simpson_index, 0.75, places=3)
        self.assertAlmostEqual(result.pielou_evenness, 1.0, places=3)

    def test_E_spatial_analysis_and_grid_binning(self):
        """E. Spatial analysis: Verifies grid cell binning, bounding-box queries, and domain summaries."""
        obs_list = [
            MarineObservation(domain=DomainType.OCEANOGRAPHY.value, latitude=10.1, longitude=75.1, variable="temperature", value=28.0),
            MarineObservation(domain=DomainType.BIODIVERSITY.value, latitude=10.2, longitude=75.2, species_name="Taxon 1", value=3),
            MarineObservation(domain=DomainType.FISHERIES.value, latitude=10.8, longitude=75.9, variable="catch_weight_kg", value=50.0),
            MarineObservation(domain=DomainType.OCEANOGRAPHY.value, latitude=15.5, longitude=80.5, variable="salinity", value=35.0),
        ]

        result = analyze_spatial_distribution(observations=obs_list, grid_size_deg=1.0)

        self.assertEqual(result.total_observations, 4)
        self.assertEqual(result.domain_distribution[DomainType.OCEANOGRAPHY.value], 2)
        self.assertEqual(result.domain_distribution[DomainType.BIODIVERSITY.value], 1)
        self.assertEqual(result.domain_distribution[DomainType.FISHERIES.value], 1)

        # There should be 2 distinct 1° grid cells: [10-11, 75-76] with 3 obs, and [15-16, 80-81] with 1 obs
        self.assertEqual(len(result.grid_cells), 2)
        self.assertEqual(result.grid_cells[0].observation_count, 3)
        self.assertEqual(result.grid_cells[0].species_richness, 1)

    def test_F_temporal_dynamics_and_seasons(self):
        """F. Temporal analysis: Tests daily/monthly time buckets and Indian Ocean seasonal aggregation."""
        obs_list = [
            MarineObservation(domain=DomainType.OCEANOGRAPHY.value, observation_time="2026-04-15T12:00:00Z", variable="temperature", value=30.0), # Pre-Monsoon (Apr)
            MarineObservation(domain=DomainType.OCEANOGRAPHY.value, observation_time="2026-07-20T12:00:00Z", variable="temperature", value=27.0), # SW-Monsoon (Jul)
            MarineObservation(domain=DomainType.OCEANOGRAPHY.value, observation_time="2026-10-10T12:00:00Z", variable="temperature", value=28.5), # Post-Monsoon (Oct)
            MarineObservation(domain=DomainType.OCEANOGRAPHY.value, observation_time="2026-12-25T12:00:00Z", variable="temperature", value=26.5), # Winter (Dec)
        ]

        result = analyze_temporal_dynamics(observations=obs_list, period_type="monthly")

        self.assertEqual(result.total_observations, 4)
        self.assertEqual(len(result.time_series), 4)
        self.assertEqual(result.seasonal_summary["Pre-Monsoon"]["observation_count"], 1)
        self.assertEqual(result.seasonal_summary["SW-Monsoon"]["observation_count"], 1)
        self.assertEqual(result.seasonal_summary["Post-Monsoon"]["observation_count"], 1)
        self.assertEqual(result.seasonal_summary["Winter"]["observation_count"], 1)
        self.assertEqual(result.seasonal_summary["Pre-Monsoon"]["variable_means"]["temperature"], 30.0)

    def test_G_cross_domain_correlation_pearson_and_spearman(self):
        """G. Cross-domain correlation: Tests Pearson r, Spearman rho, p-values, and non-causality note."""
        # Perfectly correlated synthetic pairs (y = 2x + 1)
        pairs_perfect = [(1.0, 3.0), (2.0, 5.0), (3.0, 7.0), (4.0, 9.0), (5.0, 11.0)]
        res_pearson = calculate_cross_domain_correlation(
            domain_x="oceanography",
            variable_x="temperature",
            domain_y="biodiversity",
            variable_y="richness",
            paired_data_override=pairs_perfect,
            method="pearson",
        )

        self.assertEqual(res_pearson.sample_size, 5)
        self.assertAlmostEqual(res_pearson.correlation_coefficient, 1.0, places=2)
        self.assertIn("strong positive association", res_pearson.interpretation)
        self.assertIn("Correlation represents empirical co-variation and does NOT imply biological or physical causation", res_pearson.disclaimer)

        # Monotonic non-linear pairs (y = x^3) -> Spearman rho should be exactly 1.0
        pairs_monotonic = [(1.0, 1.0), (2.0, 8.0), (3.0, 27.0), (4.0, 64.0), (5.0, 125.0)]
        res_spearman = calculate_cross_domain_correlation(
            domain_x="oceanography",
            variable_x="temperature",
            domain_y="biodiversity",
            variable_y="richness",
            paired_data_override=pairs_monotonic,
            method="spearman",
        )
        self.assertAlmostEqual(res_spearman.correlation_coefficient, 1.0, places=2)

    def test_H_cross_domain_observation_pairing(self):
        """H. Cross-domain pairing: Verifies 3D spatio-temporal-depth pairing engine."""
        ocean_obs = [
            MarineObservation(
                domain=DomainType.OCEANOGRAPHY.value,
                variable="temperature",
                value=28.5,
                latitude=10.0,
                longitude=76.0,
                depth=20.0,
                observation_time="2026-03-01T12:00:00Z",
            )
        ]
        bio_obs = [
            MarineObservation(
                domain=DomainType.BIODIVERSITY.value,
                variable="individual_count",
                value=12.0,
                latitude=10.05,
                longitude=76.02,
                depth=25.0,
                observation_time="2026-03-02T10:00:00Z", # within 22h, ~7km, ~5m depth
            ),
            MarineObservation(
                domain=DomainType.BIODIVERSITY.value,
                variable="individual_count",
                value=5.0,
                latitude=18.0, # Far away (>800km)
                longitude=85.0,
                depth=100.0,
                observation_time="2026-03-01T12:00:00Z",
            ),
        ]

        pairs = pair_cross_domain_observations(
            ocean_obs,
            bio_obs,
            spatial_radius_km=50.0,
            temporal_window_hours=72.0,
            depth_tolerance_m=20.0,
        )

        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0][0].value, 28.5)
        self.assertEqual(pairs[0][1].value, 12.0)

    def test_I_ecosystem_relationships_synthesis(self):
        """I. Ecosystem relationship: Tests synthesis of Temperature ↔ Species and Oxygen ↔ Biodiversity."""
        obs_pool = [
            MarineObservation(domain=DomainType.OCEANOGRAPHY.value, variable="temperature", value=28.0, latitude=10.0, longitude=75.0, observation_time="2026-03-01T10:00:00Z"),
            MarineObservation(domain=DomainType.BIODIVERSITY.value, species_name="Fish A", variable="individual_count", value=10.0, latitude=10.02, longitude=75.01, observation_time="2026-03-01T12:00:00Z"),
            MarineObservation(domain=DomainType.OCEANOGRAPHY.value, variable="temperature", value=29.0, latitude=11.0, longitude=76.0, observation_time="2026-03-05T10:00:00Z"),
            MarineObservation(domain=DomainType.BIODIVERSITY.value, species_name="Fish B", variable="individual_count", value=20.0, latitude=11.01, longitude=76.01, observation_time="2026-03-05T12:00:00Z"),
            MarineObservation(domain=DomainType.OCEANOGRAPHY.value, variable="temperature", value=30.0, latitude=12.0, longitude=77.0, observation_time="2026-03-10T10:00:00Z"),
            MarineObservation(domain=DomainType.BIODIVERSITY.value, species_name="Fish C", variable="individual_count", value=30.0, latitude=12.01, longitude=77.01, observation_time="2026-03-10T12:00:00Z"),
        ]

        result = analyze_ecosystem_relationship(
            theme_key="temperature_species",
            observations=obs_pool,
            spatial_radius_km=50.0,
            temporal_window_hours=72.0,
        )

        self.assertEqual(result.theme, "Temperature ↔ Species Richness")
        self.assertIsNotNone(result.correlation)
        self.assertEqual(result.correlation.sample_size, 3)
        self.assertAlmostEqual(result.correlation.correlation_coefficient, 1.0, places=2)
        self.assertIn("strong positive association", result.summary_narrative)
        self.assertIn("Further ecological modeling is required to infer functional mechanisms", result.limitation_note)

    def test_J_numerical_safety_and_edge_cases(self):
        """J. Safety & edge cases: Validates zero-division, empty pools, and invalid values."""
        # 1. Empty observation list
        empty_trend = analyze_ocean_trends(observations=[])
        self.assertEqual(empty_trend.data_points_count, 0)
        self.assertEqual(empty_trend.trend_direction, "insufficient_data")

        empty_bio = calculate_biodiversity_indicators(observations=[])
        self.assertEqual(empty_bio.species_richness, 0)
        self.assertIsNone(empty_bio.shannon_index)

        # 2. Insufficient correlation observations (< 3)
        res_insufficient = calculate_cross_domain_correlation(
            domain_x="oceanography", variable_x="temperature",
            domain_y="biodiversity", variable_y="count",
            paired_data_override=[(1.0, 2.0), (2.0, 4.0)],
        )
        self.assertEqual(res_insufficient.sample_size, 2)
        self.assertEqual(res_insufficient.interpretation, "insufficient_paired_observations")

        # 3. Constant values (0 variance)
        res_zero_var = calculate_cross_domain_correlation(
            domain_x="oceanography", variable_x="temperature",
            domain_y="biodiversity", variable_y="count",
            paired_data_override=[(5.0, 10.0), (5.0, 20.0), (5.0, 30.0)],
        )
        self.assertEqual(res_zero_var.correlation_coefficient, 0.0)

    def test_K_scientific_analysis_service_facade(self):
        """K. Service facade: Tests orchestration through ScientificAnalysisService."""
        obs = [MarineObservation(domain=DomainType.OCEANOGRAPHY.value, variable="salinity", value=35.2, observation_time="2026-05-01T00:00:00Z")]
        res = ScientificAnalysisService.analyze_ocean_trends(observations=obs, variable="salinity")
        self.assertEqual(res.variable, "salinity")
        self.assertAlmostEqual(res.overall_mean, 35.2, places=1)

    def test_L_real_cmlre_dataset_flow_to_scientific_analysis(self):
        """L. Real CMLRE dataset flow: Ingestion -> QC -> Fusion -> Phase 6 Analysis on real occurrence.txt."""
        dataset_path = ROOT_DIR / "dataset" / "occurrence.txt"
        if not dataset_path.exists():
            self.skipTest(f"Dataset file {dataset_path} not found.")

        # Phase 3: Ingestion
        df, meta, _ = parse_cmlre_txt(str(dataset_path))
        norm_df, _ = normalize_dataframe_columns(df)

        # Phase 4: QC
        qc_output = integrate_with_phase4(norm_df, dataset_metadata=meta)
        std_df = qc_output["df"]

        # Phase 5: Transform to MarineObservation objects
        observations: List[MarineObservation] = []
        for _, row in std_df.head(200).iterrows():
            observations.append(
                MarineObservation(
                    domain=DomainType.BIODIVERSITY.value,
                    species_name=row.get("species_scientific_name") or row.get("scientific_name") or row.get("species_name") or row.get("scientificName"),
                    latitude=row.get("latitude"),
                    longitude=row.get("longitude"),
                    depth=row.get("depth_meters"),
                    observation_time=row.get("timestamp") or row.get("observation_time"),
                    value=float(row.get("individual_count", 1)) if row.get("individual_count") is not None else 1.0,
                    variable="individual_count",
                )
            )

        # Phase 6: Run Species Distribution & Biodiversity analysis
        dist_res = ScientificAnalysisService.analyze_species_distribution(observations=observations)
        bio_res = ScientificAnalysisService.calculate_biodiversity(observations=observations)

        self.assertGreater(dist_res.total_occurrences, 0)
        self.assertGreater(dist_res.unique_species_count, 0)
        self.assertGreater(bio_res.species_richness, 0)
        self.assertIsNotNone(bio_res.shannon_index)
        self.assertGreater(bio_res.shannon_index, 0.0)


if __name__ == "__main__":
    unittest.main()
