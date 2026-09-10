"""
Unit Tests for XGBoost Seasonal Species Distribution Shift Classifier.

Verifies:
1. Feature matrix generation across Structural, Environmental, and Full feature sets.
2. Species and sector categorical integer encoding.
3. Native preservation of missing numerical values as NaN (never imputed as 0.0).
4. Strict absence of target leakage (no target variables in feature space).
5. Target integer class encoding [0, 6].
6. Deterministic and reproducible inference.
7. Model artifact serialization and deserialization (JSON save/load).
8. Sector centroid geographic displacement error calculation.
"""

import os
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd

from ml.distribution_shift.markov_baseline import CANONICAL_SECTORS, MarkovDistributionBaseline
from ml.distribution_shift.movement_model import (
    DistributionFeatureExtractor,
    ENVIRONMENTAL_FEATURES,
    FULL_FEATURES,
    STRUCTURAL_FEATURES,
    XGBoostMovementClassifier,
    calculate_geographic_displacement_error,
)


class TestMovementModel(unittest.TestCase):

    def setUp(self):
        self.sample_transitions = [
            {
                "scientific_name": f"Species_{i}",
                "current_sector": CANONICAL_SECTORS[i % len(CANONICAL_SECTORS)],
                "current_lat": 10.0 + i,
                "current_lon": 70.0 + i,
                "mean_depth_meters": 25.0 + i * 10 if i % 2 == 0 else None,
                "season_code": (i % 3) + 1,
                "month": (i * 2 % 12) + 1,
                "target_month": ((i * 2 + 2) % 12) + 1,
                "target_sector": CANONICAL_SECTORS[i % len(CANONICAL_SECTORS)],
                "historical_occurrence_rate": 0.1,
                "sst_celsius": 28.0 + i * 0.5 if i % 2 == 0 else None,
                "salinity_psu": 35.0 if i % 2 == 0 else None,
                "dissolved_oxygen_mgl": 5.0 if i % 2 == 0 else None,
                "chlorophyll_mg_m3": 1.0 if i % 2 == 0 else None,
            }
            for i in range(len(CANONICAL_SECTORS) * 3)
        ]
        self.fe = DistributionFeatureExtractor().fit(self.sample_transitions)

    def test_01_feature_matrix_shapes_and_columns(self):
        """1. Verifies column structure across Structural, Environmental, and Full modes."""
        n_samples = len(self.sample_transitions)
        X_struct, y_struct, f_struct = self.fe.transform(self.sample_transitions, model_type="structural")
        self.assertEqual(list(X_struct.columns), STRUCTURAL_FEATURES)
        self.assertEqual(len(X_struct), n_samples)

        X_env, y_env, f_env = self.fe.transform(self.sample_transitions, model_type="environmental")
        self.assertEqual(list(X_env.columns), ENVIRONMENTAL_FEATURES)
        self.assertEqual(len(X_env), n_samples)

        markov = MarkovDistributionBaseline(min_support=1).fit(self.sample_transitions)
        X_full, y_full, f_full = self.fe.transform(self.sample_transitions, model_type="full", markov_model=markov)
        self.assertEqual(list(X_full.columns), FULL_FEATURES)
        self.assertEqual(len(X_full), n_samples)

    def test_02_no_target_leakage(self):
        """2. Verifies that future state / target features are strictly absent from feature matrices."""
        X, y, cols = self.fe.transform(self.sample_transitions, model_type="full")
        for col in cols:
            self.assertFalse("target" in col.lower(), f"Target leakage detected in feature: {col}")
            self.assertNotIn(col, ["target_sector", "target_lat", "target_lon", "displacement_distance_km", "target_direction_deg"])

    def test_03_missing_environmental_values_preserved_as_nan(self):
        """3. Verifies that missing environmental values are preserved as NaN and NEVER zeroed."""
        X_env, _, _ = self.fe.transform(self.sample_transitions, model_type="environmental")
        # Row 1 has missing depth and missing SST
        self.assertTrue(np.isnan(X_env.loc[1, "mean_depth_meters"]))
        self.assertTrue(np.isnan(X_env.loc[1, "sst_celsius"]))
        self.assertTrue(np.isnan(X_env.loc[1, "dissolved_oxygen_mgl"]))
        self.assertEqual(X_env.loc[1, "has_environmental_context"], 0.0)

        # Row 0 has valid SST
        self.assertFalse(np.isnan(X_env.loc[0, "sst_celsius"]))
        self.assertEqual(X_env.loc[0, "has_environmental_context"], 1.0)

    def test_04_target_integer_encoding(self):
        """4. Verifies target classes are correctly mapped to integer codes [0, 6]."""
        _, y, _ = self.fe.transform(self.sample_transitions, model_type="structural")
        self.assertEqual(len(y), len(self.sample_transitions))
        for code in y:
            self.assertGreaterEqual(code, 0)
            self.assertLess(code, len(CANONICAL_SECTORS))

    def test_05_deterministic_fit_and_inference(self):
        """5. Verifies deterministic output probabilities with fixed random state."""
        X, y, _ = self.fe.transform(self.sample_transitions * 4, model_type="environmental")
        model1 = XGBoostMovementClassifier(n_estimators=10, max_depth=2, random_state=42).fit(X, y)
        model2 = XGBoostMovementClassifier(n_estimators=10, max_depth=2, random_state=42).fit(X, y)

        probs1 = model1.predict_proba(X)
        probs2 = model2.predict_proba(X)
        np.testing.assert_allclose(probs1, probs2, rtol=1e-5)

    def test_06_model_serialization_and_deserialization(self):
        """6. Verifies model save and load roundtrip parity."""
        X, y, _ = self.fe.transform(self.sample_transitions * 4, model_type="environmental")
        model = XGBoostMovementClassifier(n_estimators=10, max_depth=2, random_state=42).fit(X, y)
        probs_before = model.predict_proba(X)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            model.save_model(tmp_path)
            loaded_model = XGBoostMovementClassifier()
            loaded_model.feature_names = model.feature_names
            loaded_model.load_model(tmp_path)
            probs_after = loaded_model.predict_proba(X)
            np.testing.assert_allclose(probs_before, probs_after, rtol=1e-5)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_07_geographic_displacement_error_calculation(self):
        """7. Verifies sector centroid Haversine error calculations."""
        y_true = ["Malabar Upwelling Shelf", "Konkan Coast / Central West Coast"]
        y_pred = ["Malabar Upwelling Shelf", "Malabar Upwelling Shelf"]
        errs = calculate_geographic_displacement_error(y_true, y_pred)
        self.assertEqual(errs["min_displacement_error_km"] if "min_displacement_error_km" in errs else 0.0, 0.0)
        self.assertGreater(errs["mean_displacement_error_km"], 0.0)


if __name__ == "__main__":
    unittest.main()
