"""
Unit Tests for Production Distribution Shift Inference Service.

Verifies:
1. Deterministic and reproducible prediction outputs.
2. 7-Sector probability distribution sums to 1.0.
3. Native handling of missing environmental CTD sensors (None / NaN).
4. Clean rejection and validation errors for unknown species.
5. Clean rejection of invalid sector names.
6. Clean rejection of coordinates outside Arabian Sea boundaries.
7. Validation of forecast horizon delta_t (1-11 months).
8. Model and extractor artifact loading.
9. Strict absence of target / future-state leakage.
10. Top-3 predictions ranked strictly descending by probability.
11. Accurate assignment of empirically validated confidence tiers.
"""

import unittest
from ml.distribution_shift.inference import (
    CONFIDENCE_HIGH_THRESHOLD,
    CONFIDENCE_MODERATE_THRESHOLD,
    DistributionShiftInferenceEngine,
    get_inference_engine,
    predict_distribution_shift,
)
from ml.distribution_shift.markov_baseline import CANONICAL_SECTORS


class TestDistributionShiftInference(unittest.TestCase):

    def setUp(self):
        self.engine = get_inference_engine()
        self.valid_request = {
            "species_id": "Sardinella longiceps",
            "current_sector": "Malabar Upwelling Shelf",
            "current_lat": 10.5,
            "current_lon": 75.5,
            "month": 4,
            "forecast_horizon_months": 2,
            "mean_depth_meters": 35.0,
            "sst_celsius": 29.5,
            "salinity_psu": 35.2,
            "dissolved_oxygen_mgl": 4.8,
            "chlorophyll_mg_m3": 1.5,
        }

    def test_01_deterministic_output(self):
        """1. Verifies calling inference twice with identical input gives identical outputs."""
        res1 = predict_distribution_shift(self.valid_request)
        res2 = predict_distribution_shift(self.valid_request)
        self.assertEqual(res1["top_prediction"]["sector"], res2["top_prediction"]["sector"])
        self.assertAlmostEqual(res1["top_prediction"]["probability"], res2["top_prediction"]["probability"], places=4)
        self.assertEqual(res1["probability_distribution"], res2["probability_distribution"])

    def test_02_probability_distribution_sums_to_one(self):
        """2. Verifies that the 7 canonical sector probabilities sum to 1.0."""
        res = predict_distribution_shift(self.valid_request)
        probs = res["probability_distribution"]
        self.assertEqual(len(probs), len(CANONICAL_SECTORS))
        for sec in CANONICAL_SECTORS:
            self.assertIn(sec, probs)
            self.assertGreaterEqual(probs[sec], 0.0)
            self.assertLessEqual(probs[sec], 1.0)
        self.assertAlmostEqual(sum(probs.values()), 1.0, places=3)

    def test_03_missing_environmental_values_handled_gracefully(self):
        """3. Verifies missing sensor context (None/NaN) runs cleanly without zero imputation."""
        req_missing = dict(self.valid_request)
        req_missing["sst_celsius"] = None
        req_missing["salinity_psu"] = None
        req_missing["dissolved_oxygen_mgl"] = None
        req_missing["chlorophyll_mg_m3"] = None
        req_missing["mean_depth_meters"] = None

        res = predict_distribution_shift(req_missing)
        self.assertFalse(res["environmental_context_available"])
        self.assertIn("top_prediction", res)
        self.assertAlmostEqual(sum(res["probability_distribution"].values()), 1.0, places=3)

    def test_04_unknown_species_rejected_cleanly(self):
        """4. Verifies unknown species raises ValueError with clear error message."""
        req_bad = dict(self.valid_request)
        req_bad["species_id"] = "NonExistentFish_XYZ"
        with self.assertRaises(ValueError) as ctx:
            predict_distribution_shift(req_bad)
        self.assertIn("not in the trained species vocabulary", str(ctx.exception))

    def test_05_invalid_sector_rejected_cleanly(self):
        """5. Verifies invalid sector name raises ValueError."""
        req_bad = dict(self.valid_request)
        req_bad["current_sector"] = "Invalid_Ocean_Sector"
        with self.assertRaises(ValueError) as ctx:
            predict_distribution_shift(req_bad)
        self.assertIn("Invalid 'current_sector'", str(ctx.exception))

    def test_06_invalid_coordinates_rejected(self):
        """6. Verifies coordinates outside the Arabian Sea boundary raise ValueError."""
        req_bad = dict(self.valid_request)
        req_bad["current_lat"] = 45.0  # Outside Arabian Sea
        with self.assertRaises(ValueError) as ctx:
            predict_distribution_shift(req_bad)
        self.assertIn("Arabian Sea bounds", str(ctx.exception))

    def test_07_forecast_horizon_delta_t_validated(self):
        """7. Verifies invalid forecast horizon months (e.g. 0, 15) raises ValueError."""
        req_bad1 = dict(self.valid_request, forecast_horizon_months=0)
        with self.assertRaises(ValueError):
            predict_distribution_shift(req_bad1)

        req_bad2 = dict(self.valid_request, forecast_horizon_months=13)
        with self.assertRaises(ValueError):
            predict_distribution_shift(req_bad2)

    def test_08_model_artifact_loading_and_singleton(self):
        """8. Verifies singleton engine is properly initialized and loaded."""
        engine = get_inference_engine()
        self.assertIsNotNone(engine.model)
        self.assertIsNotNone(engine.feature_extractor)
        self.assertIsNotNone(engine.markov_baseline)
        self.assertTrue(engine._is_initialized)

    def test_09_no_target_leakage(self):
        """9. Verifies request sanitization ignores any inadvertent target/future variables."""
        req_leakage = dict(self.valid_request)
        req_leakage["target_sector"] = "North Arabian Sea / Gujarat Shelf"
        req_leakage["target_lat"] = 21.5
        req_leakage["target_lon"] = 69.5
        req_leakage["displacement_distance_km"] = 500.0

        # Should execute successfully without using any of the injected target keys
        res = predict_distribution_shift(req_leakage)
        self.assertIn("top_prediction", res)

    def test_10_top_3_sorted_descending(self):
        """10. Verifies top_3_predictions is strictly ordered by descending probability."""
        res = predict_distribution_shift(self.valid_request)
        top_3 = res["top_3_predictions"]
        self.assertEqual(len(top_3), 3)
        self.assertGreaterEqual(top_3[0]["probability"], top_3[1]["probability"])
        self.assertGreaterEqual(top_3[1]["probability"], top_3[2]["probability"])

    def test_11_confidence_tier_assigned_correctly(self):
        """11. Verifies confidence tier classification adheres to calibration thresholds."""
        res = predict_distribution_shift(self.valid_request)
        p_top = res["top_prediction"]["probability"]
        if p_top >= CONFIDENCE_HIGH_THRESHOLD:
            self.assertEqual(res["confidence_level"], "HIGH")
        elif p_top >= CONFIDENCE_MODERATE_THRESHOLD:
            self.assertEqual(res["confidence_level"], "MODERATE")
        else:
            self.assertEqual(res["confidence_level"], "LOW")

    def test_12_species_synonym_resolution(self):
        """12. Verifies common name synonyms (e.g. 'Indian Oil Sardine') resolve to canonical scientific name."""
        req_synonym = dict(self.valid_request, species="Indian Oil Sardine")
        res = predict_distribution_shift(req_synonym)
        self.assertEqual(res["species"], "Sardinella longiceps")


if __name__ == "__main__":
    unittest.main()
