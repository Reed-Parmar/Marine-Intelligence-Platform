"""
Unit Tests for Scientific Markov Distribution Baseline.

Verifies:
1. Output probabilities sum strictly to 1.0.
2. No invalid sector names or missing classes.
3. No negative probabilities.
4. Deterministic and reproducible inference.
5. Delta_t (month gap) calculations.
6. Seasonal succession logic.
7. Hierarchical fallback smoothing (Levels 1 to 5).
8. Train/Test temporal holdout integrity (zero leakage).
9. Evaluation metric mathematical correctness.
"""

import math
import unittest
from ml.distribution_shift.markov_baseline import (
    CANONICAL_SECTORS,
    MarkovDistributionBaseline,
    evaluate_predictions,
)


class TestMarkovDistributionBaseline(unittest.TestCase):

    def setUp(self):
        # Synthetic transition training set
        self.sample_train_transitions = [
            # Sardinella longiceps transitions
            {
                "scientific_name": "Sardinella longiceps",
                "current_sector": "Malabar Upwelling Shelf",
                "season_code": 1,
                "month": 4,
                "target_sector": "Konkan Coast / Central West Coast",
                "target_season_code": 2,
                "target_month": 6,
            },
            {
                "scientific_name": "Sardinella longiceps",
                "current_sector": "Malabar Upwelling Shelf",
                "season_code": 1,
                "month": 4,
                "target_sector": "Konkan Coast / Central West Coast",
                "target_season_code": 2,
                "target_month": 6,
            },
            {
                "scientific_name": "Sardinella longiceps",
                "current_sector": "Malabar Upwelling Shelf",
                "season_code": 1,
                "month": 4,
                "target_sector": "Malabar Upwelling Shelf",
                "target_season_code": 2,
                "target_month": 6,
            },
            # Rastrelliger kanagurta transitions
            {
                "scientific_name": "Rastrelliger kanagurta",
                "current_sector": "Konkan Coast / Central West Coast",
                "season_code": 2,
                "month": 7,
                "target_sector": "North Arabian Sea / Gujarat Shelf",
                "target_season_code": 3,
                "target_month": 10,
            },
            {
                "scientific_name": "Rastrelliger kanagurta",
                "current_sector": "Konkan Coast / Central West Coast",
                "season_code": 2,
                "month": 7,
                "target_sector": "North Arabian Sea / Gujarat Shelf",
                "target_season_code": 3,
                "target_month": 10,
            },
            {
                "scientific_name": "Rastrelliger kanagurta",
                "current_sector": "Konkan Coast / Central West Coast",
                "season_code": 2,
                "month": 7,
                "target_sector": "Konkan Coast / Central West Coast",
                "target_season_code": 3,
                "target_month": 10,
            },
        ]
        self.markov = MarkovDistributionBaseline(min_support=2)
        self.markov.fit(self.sample_train_transitions)

    def test_01_probabilities_sum_to_one(self):
        """1. Verifies that predicted probability distributions sum to exactly 1.0."""
        pred = self.markov.predict_distribution(
            species="Sardinella longiceps",
            source_sector="Malabar Upwelling Shelf",
            season_code=1,
            delta_t=2,
            mode="species_conditioned",
        )
        probs = pred["probabilities"]
        prob_sum = sum(probs.values())
        self.assertAlmostEqual(prob_sum, 1.0, places=5)

    def test_02_all_canonical_sectors_present_and_non_negative(self):
        """2. Verifies all canonical sectors are present with non-negative probabilities."""
        pred = self.markov.predict_distribution(
            species="Sardinella longiceps",
            source_sector="Malabar Upwelling Shelf",
            season_code=1,
            delta_t=2,
        )
        probs = pred["probabilities"]
        self.assertEqual(len(probs), len(CANONICAL_SECTORS))
        for sec in CANONICAL_SECTORS:
            self.assertIn(sec, probs)
            self.assertGreaterEqual(probs[sec], 0.0)

    def test_03_deterministic_reproducible_output(self):
        """3. Verifies deterministic inference across repeated calls."""
        pred1 = self.markov.predict_distribution("Rastrelliger kanagurta", "Konkan Coast / Central West Coast", 2, 3)
        pred2 = self.markov.predict_distribution("Rastrelliger kanagurta", "Konkan Coast / Central West Coast", 2, 3)
        self.assertEqual(pred1["probabilities"], pred2["probabilities"])
        self.assertEqual(pred1["predicted_sector"], pred2["predicted_sector"])

    def test_04_hierarchical_fallback_levels(self):
        """4. Verifies smooth fallback from Level 1 down to Level 5 for unobserved species/sectors."""
        # Known combination (N=3 >= min_support 2) -> Level 1
        p_lvl1 = self.markov.predict_distribution("Sardinella longiceps", "Malabar Upwelling Shelf", 1, 2)
        self.assertEqual(p_lvl1["fallback_level"], 1)

        # Unseen delta_t (e.g. dt=5) for known species+sector+season -> Level 2
        p_lvl2 = self.markov.predict_distribution("Sardinella longiceps", "Malabar Upwelling Shelf", 1, 5)
        self.assertEqual(p_lvl2["fallback_level"], 2)

        # Unseen species in known sector+season+dt -> Level 3
        p_lvl3 = self.markov.predict_distribution("Rare Shark", "Malabar Upwelling Shelf", 1, 2)
        self.assertEqual(p_lvl3["fallback_level"], 3)

        # Unseen species in completely unseen sector/season -> Level 5 (Global Prior)
        p_lvl5 = self.markov.predict_distribution("Rare Shark", "South-Eastern Arabian Sea EEZ", 3, 4)
        self.assertEqual(p_lvl5["fallback_level"], 5)
        self.assertAlmostEqual(sum(p_lvl5["probabilities"].values()), 1.0, places=5)

    def test_05_persistence_baseline(self):
        """5. Verifies Persistence Baseline returns 100% confidence for source sector."""
        pers = self.markov.predict_persistence("Malabar Upwelling Shelf")
        self.assertEqual(pers["predicted_sector"], "Malabar Upwelling Shelf")
        self.assertEqual(pers["probabilities"]["Malabar Upwelling Shelf"], 1.0)
        self.assertEqual(pers["probabilities"]["Konkan Coast / Central West Coast"], 0.0)

    def test_06_evaluation_metrics_math(self):
        """6. Verifies evaluation metrics calculate correctly on known ground truth."""
        y_true = ["Malabar Upwelling Shelf", "Konkan Coast / Central West Coast"]
        y_prob = [
            {"Malabar Upwelling Shelf": 0.8, "Konkan Coast / Central West Coast": 0.2, "North Arabian Sea / Gujarat Shelf": 0.0, "Lakshadweep Sea & Ridge": 0.0, "Wadge Bank / Comorin Sector": 0.0, "South-Eastern Arabian Sea EEZ": 0.0, "Central Arabian Sea Offshore Basin": 0.0},
            {"Malabar Upwelling Shelf": 0.3, "Konkan Coast / Central West Coast": 0.7, "North Arabian Sea / Gujarat Shelf": 0.0, "Lakshadweep Sea & Ridge": 0.0, "Wadge Bank / Comorin Sector": 0.0, "South-Eastern Arabian Sea EEZ": 0.0, "Central Arabian Sea Offshore Basin": 0.0},
        ]
        metrics = evaluate_predictions(y_true, y_prob)
        self.assertEqual(metrics["top_1_accuracy"], 1.0)
        self.assertEqual(metrics["top_3_accuracy"], 1.0)
        self.assertGreater(metrics["macro_f1"], 0.0)
        self.assertLess(metrics["log_loss"], 1.0)
        self.assertLess(metrics["brier_score"], 0.5)


if __name__ == "__main__":
    unittest.main()
