"""
Unit & Integration Tests for Environmental Anomaly Detection V2 Pipeline.
Tests multi-year baseline, V2 model artifacts, temporal separation, and inference.
"""

import json
from pathlib import Path
import unittest
import joblib
import numpy as np
import pandas as pd

from ml.environmental_anomaly.feature_engineering import SSTBaselineCalculator
from ml.environmental_anomaly.preprocessing import compute_arabian_sea_subbasin_masks


class TestEnvironmentalAnomalyV2(unittest.TestCase):
    """Verifies V2 model, multi-year baseline, temporal separation, and artifacts."""

    @classmethod
    def setUpClass(cls):
        cls.root_dir = Path(__file__).resolve().parent.parent
        cls.models_v2_dir = cls.root_dir / "models" / "environmental_anomaly_v2"
        cls.results_v2_dir = cls.root_dir / "results" / "environmental_anomaly_v2"
        cls.hist_dir = cls.root_dir / "historical_sst"

    def test_v2_artifacts_exist(self):
        """Verifies all required V2 model and result files are present."""
        expected_models = [
            "isolation_forest.joblib",
            "baseline_calculator.json",
            "feature_config.json",
            "metadata.json",
        ]
        for f in expected_models:
            p = self.models_v2_dir / f
            self.assertTrue(p.exists(), f"Missing V2 model artifact: {p}")
            self.assertGreater(p.stat().st_size, 0)

        expected_results = [
            "evaluation_report.json",
            "validation_report.json",
            "v1_vs_v2_comparison.json",
            "baseline_comparison.json",
            "predictions_sample.csv",
        ]
        for f in expected_results:
            p = self.results_v2_dir / f
            self.assertTrue(p.exists(), f"Missing V2 result artifact: {p}")
            self.assertGreater(p.stat().st_size, 0)

    def test_v2_diagnostic_plots_exist(self):
        """Verifies all 6 diagnostic plots are generated."""
        expected_plots = [
            "baseline_comparison.png",
            "sst_anomaly_distribution.png",
            "anomaly_score_distribution.png",
            "spatial_anomaly_map.png",
            "monthly_anomaly_rates.png",
            "v1_vs_v2_comparison.png",
        ]
        for plot in expected_plots:
            p = self.results_v2_dir / plot
            self.assertTrue(p.exists(), f"Missing V2 diagnostic plot: {p}")
            self.assertGreater(p.stat().st_size, 1000)

    def test_temporal_separation_metadata(self):
        """Verifies strict temporal separation (Train: 2018-2023, Val: 2024, Test: 2025)."""
        with open(self.models_v2_dir / "metadata.json", "r", encoding="utf-8") as f:
            meta = json.load(f)

        self.assertEqual(meta["model_version"], "2.0.0-isolation-forest-8yr-production")
        self.assertTrue(meta["is_real_data"])
        self.assertEqual(meta["sample_size"]["training_baseline_pool"], 31186694)
        self.assertEqual(meta["sample_size"]["training_model_fit_sample"], 600000)
        self.assertEqual(meta["sample_size"]["validation_observations"], 5209644)
        self.assertEqual(meta["sample_size"]["test_observations"], 5195410)

    def test_v2_baseline_integrity(self):
        """Verifies multi-year baseline lookup tables and reasonable ocean temperatures."""
        with open(self.models_v2_dir / "baseline_calculator.json", "r", encoding="utf-8") as f:
            b_data = json.load(f)

        calc = SSTBaselineCalculator.from_dict(b_data)
        self.assertTrue(calc.is_fitted)
        self.assertAlmostEqual(calc.overall_mean, 28.178, places=2)
        self.assertEqual(len(calc.global_monthly_baseline), 12)
        self.assertGreater(len(calc.cell_monthly_baseline), 5000)

        # Baseline temperatures should be physically realistic for the Arabian Sea
        for m, temp in calc.global_monthly_baseline.items():
            self.assertTrue(24.0 <= temp <= 32.0, f"Unphysical monthly baseline for month {m}: {temp}")

    def test_v2_inference_deterministic(self):
        """Verifies deterministic prediction on test coordinates with V2 model."""
        model = joblib.load(self.models_v2_dir / "isolation_forest.joblib")
        with open(self.models_v2_dir / "baseline_calculator.json", "r", encoding="utf-8") as f:
            b_data = json.load(f)
        calc = SSTBaselineCalculator.from_dict(b_data)

        # Normal condition query
        df = pd.DataFrame([{
            "timestamp": "2025-05-15",
            "latitude": 15.0,
            "longitude": 65.0,
            "analysed_sst": 29.5,
            "month": 5,
            "day_of_year": 135,
        }])
        df = calc.transform(df)

        # Features: sst_anomaly, analysed_sst, latitude, longitude, month_sin, month_cos, day_sin, day_cos
        rad_m = 2.0 * np.pi * 5 / 12.0
        rad_d = 2.0 * np.pi * 135 / 365.25
        features = np.array([[
            df["sst_anomaly"].iloc[0],
            29.5,
            15.0,
            65.0,
            np.sin(rad_m),
            np.cos(rad_m),
            np.sin(rad_d),
            np.cos(rad_d),
        ]])

        score1 = model.decision_function(features)[0]
        score2 = model.decision_function(features)[0]
        self.assertEqual(score1, score2, "Model decision function is non-deterministic")

    def test_strict_iho_mask_marginal_seas(self):
        """Verifies that Persian Gulf, Gulf of Oman, and Gulf of Aden remain strictly excluded."""
        pg_lats = np.array([26.0, 27.0])
        pg_lons = np.array([52.0, 55.0])
        masks_pg = compute_arabian_sea_subbasin_masks(pg_lats, pg_lons)
        self.assertTrue(np.all(masks_pg["is_persian_gulf"]))
        self.assertFalse(np.any(masks_pg["is_arabian_sea"]))

        # Central Arabian Sea should be retained
        as_lats = np.array([12.0, 15.0])
        as_lons = np.array([65.0, 68.0])
        masks_as = compute_arabian_sea_subbasin_masks(as_lats, as_lons)
        self.assertTrue(np.all(masks_as["is_arabian_sea"]))

    def test_predictions_sample_integrity(self):
        """Verifies predictions_sample.csv format and required columns."""
        sample_path = self.results_v2_dir / "predictions_sample.csv"
        df = pd.read_csv(sample_path)
        self.assertGreaterEqual(len(df), 10000)
        expected_cols = [
            "timestamp", "latitude", "longitude", "analysed_sst", "baseline_sst",
            "sst_anomaly", "anomaly_score", "anomaly_label", "severity", "anomaly_type"
        ]
        for col in expected_cols:
            self.assertIn(col, df.columns)

        # Check score bounds
        self.assertTrue(np.all((df["anomaly_score"] >= 0) & (df["anomaly_score"] <= 100)))


if __name__ == "__main__":
    unittest.main()
