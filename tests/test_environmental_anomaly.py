"""
Unit & Integration Tests for Environmental Anomaly Detection ML Pipeline.
Phase 14.1 of CMLRE Marine Intelligence Platform.
"""

from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd

from ml.environmental_anomaly.config import PipelineConfig
from ml.environmental_anomaly.data_loader import EnvironmentalDataLoader
from ml.environmental_anomaly.evaluate import EnvironmentalAnomalyEvaluator
from ml.environmental_anomaly.feature_engineering import (
    EnvironmentalFeatureEngineer,
    SSTBaselineCalculator,
)
from ml.environmental_anomaly.predict import (
    AnomalyPredictionResult,
    EnvironmentalAnomalyInferenceEngine,
    predict_environmental_anomaly,
)
from ml.environmental_anomaly.preprocessing import (
    EnvironmentalPreprocessor,
    compute_arabian_sea_subbasin_masks,
)
from ml.environmental_anomaly.train import EnvironmentalAnomalyTrainer
from ml.environmental_anomaly.utils import (
    generate_synthetic_environmental_df,
    generate_synthetic_environmental_netcdf,
)


class TestEnvironmentalAnomalyPipeline(unittest.TestCase):
    """
    Validates data loading, preprocessing, baseline calculation, model fitting, and inference.
    """

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.temp_path = Path(cls.temp_dir.name)

        # 1. Create a synthetic development NetCDF file fixture
        cls.nc_path = cls.temp_path / "synthetic_test_ocean.nc"
        generate_synthetic_environmental_netcdf(
            cls.nc_path,
            num_days=30,
            num_lats=15,
            num_lons=15,
            min_lat=10.0,
            max_lat=20.0,
            min_lon=70.0,
            max_lon=78.0,
            inject_anomaly=True,
        )

        # 2. Create a synthetic DataFrame fixture
        cls.df_fixture = generate_synthetic_environmental_df(
            num_samples=400, inject_anomaly_pct=0.08, random_state=42
        )

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_01_dynamic_loader_inspection(self):
        """1. Verifies dynamic inspection of NetCDF metadata without full array loading."""
        loader = EnvironmentalDataLoader()
        report = loader.inspect_dataset(self.nc_path)

        self.assertEqual(report.file_format, "NetCDF4/HDF5")
        self.assertIn("analysed_sst", report.resolved_canonical_variables.values())
        self.assertIn("lat", report.resolved_canonical_variables.values())
        self.assertIn("lon", report.resolved_canonical_variables.values())
        self.assertIn("time", report.resolved_canonical_variables.values())

        # Coordinates
        self.assertAlmostEqual(report.spatial_coverage["lat_min"], 10.0, places=1)
        self.assertAlmostEqual(report.spatial_coverage["lat_max"], 20.0, places=1)
        self.assertEqual(report.time_range["total_steps"], 30)

        # SST properties
        self.assertIsNotNone(report.sst_summary["mean_celsius"])
        self.assertGreater(report.sst_summary["mean_celsius"], 20.0)
        self.assertLess(report.sst_summary["mean_celsius"], 35.0)

    def test_02_data_loader_loading_and_slicing(self):
        """2. Verifies chunked loading and spatial-temporal bounding from NetCDF."""
        loader = EnvironmentalDataLoader()
        df = loader.load_data(
            self.nc_path,
            spatial_bounds={"min_lat": 12.0, "max_lat": 18.0, "min_lon": 72.0, "max_lon": 76.0},
            max_time_steps=10,
        )

        self.assertGreater(len(df), 0)
        self.assertIn("analysed_sst", df.columns)
        self.assertIn("latitude", df.columns)
        self.assertIn("longitude", df.columns)
        self.assertIn("month", df.columns)
        self.assertIn("day_of_year", df.columns)

        # Check bounds
        self.assertTrue((df["latitude"] >= 12.0).all())
        self.assertTrue((df["latitude"] <= 18.0).all())
        self.assertTrue((df["analysed_sst"] >= 20.0).all())
        self.assertTrue((df["analysed_sst"] <= 40.0).all())

    def test_03_preprocessing_missing_values_and_units(self):
        """3. Verifies QC filtering, Kelvin-to-Celsius conversion, and land mask filtering."""
        preprocessor = EnvironmentalPreprocessor()

        raw_records = pd.DataFrame([
            {"latitude": 15.0, "longitude": 72.0, "analysed_sst": 301.15, "mask": 1},  # Kelvin 28°C
            {"latitude": 15.1, "longitude": 72.1, "analysed_sst": 303.15, "mask": 1},  # Kelvin 30°C
            {"latitude": 95.0, "longitude": 72.0, "analysed_sst": 28.0, "mask": 1},    # Invalid lat > 90
            {"latitude": 15.0, "longitude": 72.0, "analysed_sst": -999.0, "mask": 1},  # Missing SST
            {"latitude": 15.0, "longitude": 72.0, "analysed_sst": 28.0, "mask": 2},    # Land mask = 2
            {"latitude": 15.0, "longitude": 72.0, "analysed_sst": 65.0, "mask": 1},    # Physical impossible > 45°C
        ])

        clean_df, audit = preprocessor.fit_transform(raw_records)

        self.assertEqual(len(clean_df), 2)
        self.assertEqual(audit.dropped_invalid_coords, 1)
        self.assertEqual(audit.dropped_missing_sst, 1)
        self.assertEqual(audit.dropped_land_pixels, 1)
        self.assertEqual(audit.dropped_out_of_bounds_sst, 1)
        self.assertTrue(audit.kelvin_converted)
        self.assertAlmostEqual(clean_df.iloc[0]["analysed_sst"], 28.0, places=1)

    def test_04_sst_baseline_calculator_and_anomaly(self):
        """4. Verifies empirical SST seasonal-spatial baseline and hierarchical fallback."""
        calc = SSTBaselineCalculator()
        calc.fit(self.df_fixture)

        self.assertTrue(calc.is_fitted)
        self.assertGreater(len(calc.cell_monthly_baseline), 0)

        transformed = calc.transform(self.df_fixture)
        self.assertIn("baseline_sst", transformed.columns)
        self.assertIn("sst_anomaly", transformed.columns)
        self.assertIn("sst_abs_anomaly", transformed.columns)

        # Verify mathematical identity: anomaly = observed - baseline
        diff = (transformed["analysed_sst"] - transformed["baseline_sst"]).round(3)
        self.assertTrue(np.allclose(transformed["sst_anomaly"], diff, atol=1e-3))

        # Test serialization
        calc_dict = calc.to_dict()
        calc_reloaded = SSTBaselineCalculator.from_dict(calc_dict)
        self.assertEqual(
            calc.get_baseline(15.0, 72.0, 5),
            calc_reloaded.get_baseline(15.0, 72.0, 5),
        )

    def test_05_feature_engineering_cyclic_and_variance(self):
        """5. Verifies cyclic time features and zero-variance feature filtering."""
        fe = EnvironmentalFeatureEngineer(use_cyclic_time=True, use_sea_ice_fraction=True)

        df_calc = SSTBaselineCalculator().fit(self.df_fixture).transform(self.df_fixture)
        enriched, X = fe.fit(df_calc).transform(df_calc)

        # Check cyclic time columns
        self.assertIn("month_sin", enriched.columns)
        self.assertIn("month_cos", enriched.columns)
        self.assertIn("day_sin", enriched.columns)
        self.assertIn("day_cos", enriched.columns)

        # Verify sin^2 + cos^2 = 1.0 identity
        trig_sum = (enriched["month_sin"] ** 2 + enriched["month_cos"] ** 2).round(2)
        self.assertTrue((trig_sum == 1.0).all())

        # Check that constant sea_ice_fraction (all 0.0) is correctly filtered out
        self.assertNotIn("sea_ice_fraction", fe.selected_features)
        self.assertEqual(X.shape[0], len(df_calc))
        self.assertFalse(X.isna().any().any())

    def test_06_model_training_and_score_calibration(self):
        """6. Verifies Isolation Forest training, normalized anomaly scores, and severities."""
        trainer = EnvironmentalAnomalyTrainer()
        df_pred, metadata = trainer.fit_predict(self.df_fixture, dataset_name="synthetic_unit_test")

        self.assertTrue(trainer.is_fitted)
        self.assertIn("anomaly_label", df_pred.columns)
        self.assertIn("anomaly_score", df_pred.columns)
        self.assertIn("severity", df_pred.columns)

        # Scores must be bounded [0.0, 100.0]
        self.assertTrue((df_pred["anomaly_score"] >= 0.0).all())
        self.assertTrue((df_pred["anomaly_score"] <= 100.0).all())

        # Anomaly count must be positive
        anom_count = (df_pred["anomaly_label"] == -1).sum()
        self.assertGreater(anom_count, 0)
        self.assertIn("algorithm", metadata)
        self.assertEqual(metadata["algorithm"], "IsolationForest")

    def test_07_model_artifact_saving_and_inference_engine(self):
        """7. Verifies artifact serialization and API-ready inference execution."""
        trainer = EnvironmentalAnomalyTrainer()
        df_pred, metadata = trainer.fit_predict(self.df_fixture)

        # Save artifacts to temp directory
        models_out = self.temp_path / "models_export"
        trainer.save_artifacts(models_out, metadata=metadata)

        self.assertTrue((models_out / "isolation_forest.joblib").exists())
        self.assertTrue((models_out / "baseline_calculator.json").exists())
        self.assertTrue((models_out / "feature_config.json").exists())
        self.assertTrue((models_out / "metadata.json").exists())

        # Load Inference Engine from disk
        engine = EnvironmentalAnomalyInferenceEngine(models_out).load()
        self.assertTrue(engine.is_loaded)

        # Test single normal observation
        normal_obs = {
            "latitude": 15.0,
            "longitude": 72.0,
            "analysed_sst": 28.0,
            "month": 4,
            "day_of_year": 100,
        }
        res_normal = engine.predict([normal_obs])[0]
        self.assertIsInstance(res_normal, AnomalyPredictionResult)
        self.assertIn("Normal", res_normal.anomaly_type)
        self.assertEqual(res_normal.severity, "low")

        # Test extreme marine heatwave observation (+4.5°C anomaly)
        mhw_obs = {
            "latitude": 15.0,
            "longitude": 72.0,
            "analysed_sst": 33.5,
            "month": 4,
            "day_of_year": 100,
        }
        res_mhw = engine.predict([mhw_obs])[0]
        self.assertTrue(res_mhw.is_anomaly)
        self.assertEqual(res_mhw.anomaly_type, "Marine Heatwave (MHW)")
        self.assertIn(res_mhw.severity, ("high", "critical"))
        self.assertGreater(res_mhw.anomaly_score, 70.0)

        # Test helper function
        dict_out = predict_environmental_anomaly(mhw_obs, models_dir=models_out)
        self.assertTrue(dict_out["is_anomaly"])
        self.assertEqual(dict_out["anomaly_type"], "Marine Heatwave (MHW)")

    def test_08_unsupervised_evaluation_metrics(self):
        """8. Verifies unsupervised evaluation calculations and persistence detection."""
        trainer = EnvironmentalAnomalyTrainer()
        df_pred, _ = trainer.fit_predict(self.df_fixture)

        eval_report = EnvironmentalAnomalyEvaluator.evaluate(df_pred)

        self.assertEqual(eval_report.total_observations, len(df_pred))
        self.assertGreater(eval_report.anomaly_count, 0)
        self.assertIn("mean", eval_report.score_distribution)
        self.assertIn("p99", eval_report.score_distribution)
        self.assertIn("pearson_r", eval_report.correlation_with_sst_deviation)

        # Positive correlation expected between anomaly score and |SST - Baseline|
        self.assertGreater(eval_report.correlation_with_sst_deviation["pearson_r"], 0.20)

        # Check export
        results_out = self.temp_path / "results_export"
        EnvironmentalAnomalyEvaluator.save_evaluation_results(eval_report, df_pred, results_out)
        self.assertTrue((results_out / "evaluation_report.json").exists())
        self.assertTrue((results_out / "predictions_sample.csv").exists())

    def test_09_arabian_sea_geographic_masking_subbasins(self):
        """9. Verifies IHO S-23 exclusion of Persian Gulf, Gulf of Oman, and Gulf of Aden."""
        test_df = pd.DataFrame([
            # 1. Persian Gulf points (must be excluded)
            {"latitude": 24.5, "longitude": 54.0, "analysed_sst": 29.0, "name": "Persian Gulf (Abu Dhabi)"},
            {"latitude": 25.0, "longitude": 52.0, "analysed_sst": 30.0, "name": "Persian Gulf (Qatar)"},
            # 2. Gulf of Oman points (must be excluded)
            {"latitude": 24.0, "longitude": 58.0, "analysed_sst": 28.5, "name": "Gulf of Oman (Muscat)"},
            {"latitude": 24.8, "longitude": 60.5, "analysed_sst": 28.0, "name": "Gulf of Oman (Chabahar offshore)"},
            # 3. Gulf of Aden points (must be excluded)
            {"latitude": 12.0, "longitude": 50.5, "analysed_sst": 27.5, "name": "Gulf of Aden (N. Somalia)"},
            {"latitude": 13.5, "longitude": 51.0, "analysed_sst": 28.0, "name": "Gulf of Aden (S. Yemen)"},
            # 4. Valid Arabian Sea Core points (must be retained)
            {"latitude": 15.0, "longitude": 65.0, "analysed_sst": 28.5, "name": "Central Arabian Sea"},
            {"latitude": 10.0, "longitude": 73.0, "analysed_sst": 29.0, "name": "Lakshadweep Sea"},
            {"latitude": 19.0, "longitude": 71.0, "analysed_sst": 28.2, "name": "Mumbai Offshore Shelf"},
            {"latitude": 7.0, "longitude": 76.5, "analysed_sst": 29.2, "name": "SW Indian Coast (Kerala)"},
            {"latitude": 21.0, "longitude": 67.0, "analysed_sst": 27.0, "name": "Gujarat/Saurashtra Offshore"},
            {"latitude": 18.0, "longitude": 58.0, "analysed_sst": 26.5, "name": "Oman Upwelling Zone (Arabian Sea)"},
        ])

        # Test preprocessor with Arabian Sea mask enabled
        preproc = EnvironmentalPreprocessor(apply_arabian_sea_mask=True)
        clean_df, audit = preproc.transform(test_df)

        # Audit must correctly record exactly 2 PG, 2 GO, 2 GA dropped
        self.assertEqual(audit.dropped_persian_gulf, 2)
        self.assertEqual(audit.dropped_gulf_of_oman, 2)
        self.assertEqual(audit.dropped_gulf_of_aden, 2)
        self.assertEqual(len(clean_df), 6)

        # Retained records must only be the valid Arabian Sea points
        retained_names = list(clean_df["name"])
        self.assertIn("Central Arabian Sea", retained_names)
        self.assertIn("Lakshadweep Sea", retained_names)
        self.assertIn("Mumbai Offshore Shelf", retained_names)
        self.assertIn("SW Indian Coast (Kerala)", retained_names)
        self.assertIn("Gujarat/Saurashtra Offshore", retained_names)
        self.assertIn("Oman Upwelling Zone (Arabian Sea)", retained_names)

        # None of the excluded regions should appear in clean_df
        for name in retained_names:
            self.assertNotIn("Persian Gulf", name)
            self.assertNotIn("Gulf of Oman", name)
            self.assertNotIn("Gulf of Aden", name)

    def test_10_arabian_sea_boundary_behavior(self):
        """10. Verifies precise geodesic line boundary behavior on sub-basin margins."""
        # Test directly on demarcation boundary coordinates
        lats = [22.53, 25.02, 11.83, 15.63, 15.0]
        lons = [59.80, 61.74, 51.28, 52.23, 65.0]

        masks = compute_arabian_sea_subbasin_masks(lats, lons)
        self.assertIn("is_persian_gulf", masks)
        self.assertIn("is_gulf_of_oman", masks)
        self.assertIn("is_gulf_of_aden", masks)
        self.assertIn("is_arabian_sea", masks)

        # Central Arabian Sea (15.0 N, 65.0 E) must be True
        self.assertTrue(masks["is_arabian_sea"][4])

        # A point just north of Ras al Hadd line (lat 23.5, lon 60.0) -> must be in Gulf of Oman
        # Line at 60.0 E: 22.53 + 1.2835 * 0.20 = 22.787 -> lat 23.5 is ABOVE line (in Gulf of Oman)
        north_of_line = compute_arabian_sea_subbasin_masks([23.5], [60.0])
        self.assertTrue(north_of_line["is_gulf_of_oman"][0])
        self.assertFalse(north_of_line["is_arabian_sea"][0])

        # A point just south of Ras al Hadd line (lat 22.0, lon 60.0) -> must be in Arabian Sea
        south_of_line = compute_arabian_sea_subbasin_masks([22.0], [60.0])
        self.assertFalse(south_of_line["is_gulf_of_oman"][0])
        self.assertTrue(south_of_line["is_arabian_sea"][0])


if __name__ == "__main__":
    unittest.main()

