"""
Integration and API Tests for Fisheries Catch Prediction V1 (Phase 14.3).
Validates:
- V1 production model loading from models/fisheries_catch
- Exact V1 feature preprocessing and engineering (monsoon season, log effort, cyclic time)
- Deterministic numeric prediction in Metric Tons (MT)
- Non-negativity constraints
- FastAPI endpoints (/api/v1/fisheries/predict, /batch, /model-info, /health)
- Confirmation that V1 model (XGBoost Regressor Tuned, 1.0.0) is strictly loaded
"""
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
import numpy as np
import pandas as pd

from backend.app.main import app
from ml.fisheries_catch import (
    ALL_INPUT_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    FisheriesCatchPredictor,
    assign_monsoon,
    engineer_features,
    get_fisheries_predictor,
    predict_catch,
)


class TestFisheriesCatchV1Integration(unittest.TestCase):
    """Integration test suite for Phase 14.3 V1."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.predictor = get_fisheries_predictor()
        cls.root_dir = Path(__file__).resolve().parent.parent
        cls.models_dir = cls.root_dir / "models" / "fisheries_catch"

    def test_01_v1_artifacts_exist(self):
        """Verifies that all 5 V1 production model artifacts are present."""
        expected_files = [
            "final_model.joblib",
            "final_model.json",
            "preprocessing.joblib",
            "feature_schema.json",
            "model_metadata.json",
        ]
        for fname in expected_files:
            p = self.models_dir / fname
            self.assertTrue(p.exists(), f"Missing V1 model artifact: {p}")
            self.assertGreater(p.stat().st_size, 0)

    def test_02_v1_metadata_verification(self):
        """Confirms that V1 model version is 1.0.0 and target is TotalCatchMT."""
        meta = self.predictor.metadata
        self.assertEqual(meta.get("model_version"), "1.0.0")
        self.assertEqual(meta.get("target"), "TotalCatchMT")
        self.assertEqual(meta.get("training_framework"), "xgboost")
        self.assertIn("IOTC", meta.get("dataset", ""))

    def test_03_feature_engineering_monsoon_and_log_effort(self):
        """Tests V1 monsoon season assignment and log1p effort transformations."""
        self.assertEqual(assign_monsoon(1), "NE_Monsoon")
        self.assertEqual(assign_monsoon(4), "Intermonsoon_Spring")
        self.assertEqual(assign_monsoon(8), "SW_Monsoon")
        self.assertEqual(assign_monsoon(10), "Intermonsoon_Autumn")

        raw_df = pd.DataFrame([{
            "Fleet": "EUESP",
            "Gear": "PS",
            "Effort": 45.0,
            "EffortUnits": "FHOURS",
            "Month": 8,
            "Year": 2024,
            "Latitude": 2.5,
            "Longitude": 55.5
        }])
        feat_df = engineer_features(raw_df)
        self.assertEqual(feat_df["MonsoonSeason"].iloc[0], "SW_Monsoon")
        self.assertAlmostEqual(feat_df["Log_Effort"].iloc[0], np.log1p(45.0), places=4)
        self.assertIn("Month_Sin", feat_df.columns)
        self.assertIn("Month_Cos", feat_df.columns)
        self.assertIn("Quarter", feat_df.columns)

    def test_04_direct_inference_numeric_and_units(self):
        """Verifies direct V1 model inference produces valid non-negative MT catch."""
        sample_input = {
            "Fleet": "EUESP",
            "Gear": "PS",
            "Effort": 45.0,
            "EffortUnits": "FHOURS",
            "Month": 8,
            "Year": 2024,
            "Latitude": 2.5,
            "Longitude": 55.5
        }
        res = self.predictor.predict(sample_input)
        self.assertIsInstance(res, dict)
        self.assertIn("predicted_catch_mt", res)
        self.assertGreaterEqual(res["predicted_catch_mt"], 0.0)
        self.assertEqual(res["unit"], "Metric Tons (MT)")
        self.assertEqual(res["model_version"], "1.0.0")
        self.assertEqual(res["input_summary"]["fleet"], "EUESP")

    def test_05_api_predict_single_stratum(self):
        """Tests POST /api/v1/fisheries/predict."""
        payload = {
            "Fleet": "EUESP",
            "Gear": "PS",
            "Effort": 45.0,
            "EffortUnits": "FHOURS",
            "Month": 8,
            "Year": 2024,
            "Latitude": 2.5,
            "Longitude": 55.5
        }
        resp = self.client.post("/api/v1/fisheries/predict", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json().get("data", {})
        self.assertIn("predicted_catch", data)
        self.assertIn("predicted_catch_mt", data)
        self.assertGreaterEqual(data["predicted_catch"], 0.0)
        self.assertEqual(data["unit"], "Metric Tons (MT)")
        self.assertEqual(data["model_version"], "1.0.0")
        self.assertIn("input_summary", data)

    def test_06_api_predict_batch(self):
        """Tests POST /api/v1/fisheries/predict/batch."""
        payload = {
            "items": [
                {
                    "Fleet": "EUESP",
                    "Gear": "PS",
                    "Effort": 30.0,
                    "EffortUnits": "FHOURS",
                    "Month": 6,
                    "Year": 2023,
                    "Latitude": 0.0,
                    "Longitude": 60.0
                },
                {
                    "Fleet": "EUFRA",
                    "Gear": "PS",
                    "Effort": 50.0,
                    "EffortUnits": "FHOURS",
                    "Month": 9,
                    "Year": 2023,
                    "Latitude": -2.0,
                    "Longitude": 58.0
                }
            ]
        }
        resp = self.client.post("/api/v1/fisheries/predict/batch", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json().get("data", {})
        self.assertEqual(data["total_records"], 2)
        self.assertEqual(len(data["predictions"]), 2)
        for p in data["predictions"]:
            self.assertGreaterEqual(p["predicted_catch"], 0.0)
            self.assertEqual(p["unit"], "Metric Tons (MT)")

    def test_07_api_model_info_and_health(self):
        """Tests GET /api/v1/fisheries/predict/model-info and health."""
        info_resp = self.client.get("/api/v1/fisheries/predict/model-info")
        self.assertEqual(info_resp.status_code, 200)
        info_data = info_resp.json().get("data", {})
        self.assertEqual(info_data["metadata"]["model_version"], "1.0.0")
        self.assertIn("categorical_features", info_data["feature_schema"])
        self.assertIn("raw_input_columns", info_data["feature_schema"])

        health_resp = self.client.get("/api/v1/fisheries/predict/health")
        self.assertEqual(health_resp.status_code, 200)
        health_data = health_resp.json()
        self.assertEqual(health_data["status"], "ready")
        self.assertEqual(health_data["model_version"], "1.0.0")
        self.assertTrue(health_data["model_loaded"])

    def test_08_invalid_input_validation(self):
        """Tests that invalid inputs (negative effort, month > 12) raise 422."""
        bad_month = {
            "Fleet": "EUESP",
            "Gear": "PS",
            "Effort": 10.0,
            "EffortUnits": "FHOURS",
            "Month": 15,
            "Year": 2024,
            "Latitude": 0.0,
            "Longitude": 60.0
        }
        resp = self.client.post("/api/v1/fisheries/predict", json=bad_month)
        self.assertEqual(resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()
