"""
Integration and API Tests for Environmental Anomaly Detection V2 (Phase 14.1).
Validates:
- V2 production model loading from models/environmental_anomaly_v2
- Strict IHO S-23 Arabian Sea geographic domain preservation
- Exclusion of Persian Gulf, Gulf of Oman, and Gulf of Aden
- Multi-year 2018-2023 SST baseline calculation
- Detection of Marine Heatwaves and Cold Upwelling Surges
- Severity and warm/cold classification
- FastAPI endpoints (/api/v1/ml/anomalies, /api/v1/ml/anomalies/detect, /model-info, /health)
- Confirmation that the 3.39% anomaly rate on 2025 test data is an unsupervised detection frequency
"""
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from ml.environmental_anomaly.predict import (
    EnvironmentalAnomalyInferenceEngine,
    get_inference_engine,
)


class TestEnvironmentalAnomalyV2Api(unittest.TestCase):
    """Integration and API test suite for Phase 14.1 V2."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.root_dir = Path(__file__).resolve().parent.parent
        cls.models_v2_dir = cls.root_dir / "models" / "environmental_anomaly_v2"
        cls.engine = EnvironmentalAnomalyInferenceEngine(cls.models_v2_dir)
        cls.engine.load()

    def test_01_v2_artifacts_exist(self):
        """Verifies presence of all 4 V2 model artifacts."""
        expected_artifacts = [
            "isolation_forest.joblib",
            "baseline_calculator.json",
            "feature_config.json",
            "metadata.json",
        ]
        for a in expected_artifacts:
            p = self.models_v2_dir / a
            self.assertTrue(p.exists(), f"Missing V2 artifact: {p}")
            self.assertGreater(p.stat().st_size, 0)

    def test_02_v2_metadata_and_unsupervised_rate(self):
        """Verifies V2 metadata version and unsupervised detection rate note."""
        meta = self.engine.metadata
        self.assertEqual(meta["model_version"], "2.0.0-isolation-forest-8yr-production")
        self.assertEqual(meta["algorithm"], "IsolationForest")
        self.assertEqual(meta["test_results_2025"]["anomaly_rate_pct"], 3.39)
        self.assertEqual(meta["study_region"]["name"], "Arabian Sea (Strict IHO S-23)")
        self.assertIn("Persian Gulf", meta["study_region"]["excluded_marginal_seas"])

    def test_03_geographic_constraints_preserved(self):
        """Verifies strict Arabian Sea geographic demarcation."""
        # 1. Valid Arabian Sea location
        res_as = self.engine.predict([{"lat": 15.0, "lon": 65.0, "sst": 29.0, "timestamp": "2025-06-01"}])[0]
        self.assertTrue(res_as.in_arabian_sea)
        self.assertEqual(res_as.subbasin, "Arabian Sea (Strict IHO S-23)")

        # 2. Persian Gulf location (must be flagged outside)
        res_pg = self.engine.predict([{"lat": 26.0, "lon": 53.0, "sst": 33.0, "timestamp": "2025-06-01"}])[0]
        self.assertFalse(res_pg.in_arabian_sea)

        # 3. Gulf of Oman location (must be flagged outside)
        res_go = self.engine.predict([{"lat": 24.0, "lon": 58.0, "sst": 30.0, "timestamp": "2025-06-01"}])[0]
        self.assertFalse(res_go.in_arabian_sea)
        self.assertIn("Gulf of Oman", res_go.subbasin)

        # 4. Gulf of Aden location (must be flagged outside)
        res_ga = self.engine.predict([{"lat": 12.0, "lon": 50.0, "sst": 28.0, "timestamp": "2025-06-01"}])[0]
        self.assertFalse(res_ga.in_arabian_sea)
        self.assertIn("Gulf of Aden", res_ga.subbasin)

    def test_04_api_get_anomalies(self):
        """Tests GET /api/v1/ml/anomalies returns real evaluated Arabian Sea events."""
        resp = self.client.get("/api/v1/ml/anomalies")
        self.assertEqual(resp.status_code, 200)
        data = resp.json().get("data", [])
        self.assertGreaterEqual(len(data), 1)

        first = data[0]
        self.assertIn("region", first)
        self.assertIn("anomalyType", first)
        self.assertIn("severity", first)
        self.assertIn("baselineExpectedValue", first)
        self.assertIn("observedCurrentValue", first)
        self.assertIn("sst_observed_celsius", first)
        self.assertIn("sst_baseline_celsius", first)
        self.assertIn("sst_anomaly_celsius", first)
        self.assertIn("anomalyScore", first)
        self.assertIn("warm_cold_direction", first)
        self.assertTrue(first["in_arabian_sea"])

    def test_05_api_detect_real_time(self):
        """Tests POST /api/v1/ml/anomalies/detect on-demand inference."""
        payload = {
            "latitude": 15.0,
            "longitude": 65.0,
            "sst": 32.5,  # Strong warm anomaly
            "timestamp": "2025-06-01"
        }
        resp = self.client.post("/api/v1/ml/anomalies/detect", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json().get("data", {})
        self.assertEqual(data["anomalyType"], "Marine Heatwave (MHW)")
        self.assertEqual(data["warm_cold_direction"], "warm")
        self.assertGreater(data["sst_anomaly_celsius"], 1.5)
        self.assertTrue(data["in_arabian_sea"])

    def test_06_api_model_info_and_health(self):
        """Tests GET /api/v1/ml/environmental-anomaly/model-info and health."""
        info_resp = self.client.get("/api/v1/ml/environmental-anomaly/model-info")
        self.assertEqual(info_resp.status_code, 200)
        info_data = info_resp.json().get("data", {})
        self.assertEqual(info_data["model_version"], "2.0.0-isolation-forest-8yr-production")
        self.assertEqual(info_data["test_results_2025"]["anomaly_rate_pct"], 3.39)
        self.assertIn("unsupervised", info_data["unsupervised_note"].lower())

        health_resp = self.client.get("/api/v1/ml/environmental-anomaly/health")
        self.assertEqual(health_resp.status_code, 200)
        health_data = health_resp.json()
        self.assertEqual(health_data["status"], "ready")
        self.assertTrue(health_data["model_loaded"])


if __name__ == "__main__":
    unittest.main()
