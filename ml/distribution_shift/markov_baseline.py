"""
Scientific Markov Transition Baseline for Population-Level Species Distribution Shifts.

Implements transparent empirical first-order Markov transition matrices conditioned on:
P(target_sector | species, source_sector, season, delta_t)

Features:
- Canonical 7 Arabian Sea Ecological Sectors
- Hierarchical Fallback Smoothing (Levels 1 to 5)
- History-only (zero environmental leakage)
- Evaluation against Persistence Baseline ("Stay in current sector")
- Comprehensive metrics: Top-1 Accuracy, Top-3 Accuracy, Macro F1, Multi-class Log Loss, Brier Score.
"""

from collections import Counter, defaultdict
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

# Canonical 7 Arabian Sea Sectors
CANONICAL_SECTORS: List[str] = [
    "Malabar Upwelling Shelf",
    "Central Arabian Sea Offshore Basin",
    "North Arabian Sea / Gujarat Shelf",
    "Lakshadweep Sea & Ridge",
    "Wadge Bank / Comorin Sector",
    "Konkan Coast / Central West Coast",
    "South-Eastern Arabian Sea EEZ",
]

# Minimum observation support count required at a hierarchical level before falling back
MIN_SUPPORT_THRESHOLD: int = 3


class MarkovDistributionBaseline:
    """
    Transparent empirical Markov transition model with hierarchical fallback smoothing.
    """

    def __init__(
        self,
        min_support: int = MIN_SUPPORT_THRESHOLD,
        sectors: Optional[List[str]] = None,
    ):
        self.min_support = min_support
        self.sectors = sectors or CANONICAL_SECTORS
        self.num_sectors = len(self.sectors)
        self.sector_to_idx = {s: i for i, s in enumerate(self.sectors)}

        # Transition count tables across hierarchical levels
        # Level 1: (species, source_sector, season, delta_t) -> {target_sector: count}
        self.lvl1_counts: Dict[Tuple[str, str, int, int], Counter] = defaultdict(Counter)
        # Level 2: (species, source_sector, season) -> {target_sector: count}
        self.lvl2_counts: Dict[Tuple[str, str, int], Counter] = defaultdict(Counter)
        # Level 3: (source_sector, season, delta_t) -> {target_sector: count}
        self.lvl3_counts: Dict[Tuple[str, int, int], Counter] = defaultdict(Counter)
        # Level 4: (source_sector, season) -> {target_sector: count}
        self.lvl4_counts: Dict[Tuple[str, int], Counter] = defaultdict(Counter)
        # Level 5: Global target sector distribution
        self.lvl5_counts: Counter = Counter()

        self.total_training_transitions: int = 0
        self.is_fitted: bool = False

    def fit(self, transitions: List[Dict[str, Any]]) -> "MarkovDistributionBaseline":
        """
        Fits empirical transition count matrices across all 5 hierarchical levels.
        """
        self.lvl1_counts.clear()
        self.lvl2_counts.clear()
        self.lvl3_counts.clear()
        self.lvl4_counts.clear()
        self.lvl5_counts.clear()

        for t in transitions:
            sp = str(t.get("scientific_name") or t.get("species_id") or "unknown").strip()
            src_sec = str(t.get("current_sector") or "").strip()
            tgt_sec = str(t.get("target_sector") or "").strip()
            season = int(t.get("season_code", 1))

            # Compute delta_t: (target_month - month) % 12
            m_src = int(t.get("month", 1))
            m_tgt = int(t.get("target_month", m_src))
            delta_t = (m_tgt - m_src) % 12
            if delta_t == 0:
                delta_t = 1  # Standard seasonal default if months match

            if src_sec not in self.sector_to_idx or tgt_sec not in self.sector_to_idx:
                continue

            # Update count hierarchies
            self.lvl1_counts[(sp, src_sec, season, delta_t)][tgt_sec] += 1
            self.lvl2_counts[(sp, src_sec, season)][tgt_sec] += 1
            self.lvl3_counts[(src_sec, season, delta_t)][tgt_sec] += 1
            self.lvl4_counts[(src_sec, season)][tgt_sec] += 1
            self.lvl5_counts[tgt_sec] += 1
            self.total_training_transitions += 1

        self.is_fitted = True
        return self

    def predict_distribution(
        self,
        species: str,
        source_sector: str,
        season_code: int,
        delta_t: int = 1,
        mode: str = "species_conditioned",  # 'species_conditioned' (Baseline A) or 'global_seasonal' (Baseline B)
    ) -> Dict[str, Any]:
        """
        Predicts normalized probability distribution over all 7 sectors with hierarchical fallback.
        """
        if not self.is_fitted:
            raise RuntimeError("Markov model must be fit before predict_distribution can be called.")

        sp = str(species).strip()
        src_sec = str(source_sector).strip()
        season = int(season_code)
        dt = max(1, int(delta_t))

        counts_used: Optional[Counter] = None
        fallback_lvl = 5
        lvl_desc = "Global Target Sector Prior"

        if mode == "species_conditioned":
            # Level 1: species + source_sector + season + delta_t
            c1 = self.lvl1_counts.get((sp, src_sec, season, dt))
            if c1 and sum(c1.values()) >= self.min_support:
                counts_used = c1
                fallback_lvl = 1
                lvl_desc = f"Level 1: Exact Species + Sector + Season + Delta_T (N={sum(c1.values())})"

            # Level 2: species + source_sector + season
            if counts_used is None:
                c2 = self.lvl2_counts.get((sp, src_sec, season))
                if c2 and sum(c2.values()) >= self.min_support:
                    counts_used = c2
                    fallback_lvl = 2
                    lvl_desc = f"Level 2: Species + Sector + Season (N={sum(c2.values())})"

        # Level 3: source_sector + season + delta_t (Global Seasonal with delta_t)
        if counts_used is None:
            c3 = self.lvl3_counts.get((src_sec, season, dt))
            if c3 and sum(c3.values()) >= self.min_support:
                counts_used = c3
                fallback_lvl = 3
                lvl_desc = f"Level 3: Global Sector + Season + Delta_T (N={sum(c3.values())})"

        # Level 4: source_sector + season
        if counts_used is None:
            c4 = self.lvl4_counts.get((src_sec, season))
            if c4 and sum(c4.values()) >= self.min_support:
                counts_used = c4
                fallback_lvl = 4
                lvl_desc = f"Level 4: Global Sector + Season (N={sum(c4.values())})"

        # Level 5: Global Prior
        if counts_used is None:
            counts_used = self.lvl5_counts if self.lvl5_counts else Counter({s: 1 for s in self.sectors})
            fallback_lvl = 5
            lvl_desc = f"Level 5: Global Sector Prior (N={sum(counts_used.values())})"

        # Calculate Laplace smoothed probabilities: P(s) = (count + 1e-4) / (total + num_sectors * 1e-4)
        total_counts = sum(counts_used.values())
        smooth_eps = 1e-5
        denominator = total_counts + (self.num_sectors * smooth_eps)

        probabilities: Dict[str, float] = {}
        for s in self.sectors:
            cnt = counts_used.get(s, 0)
            prob = (cnt + smooth_eps) / denominator
            probabilities[s] = prob

        # Normalize to ensure exact 1.0 sum
        prob_sum = sum(probabilities.values())
        probabilities = {s: round(p / prob_sum, 6) for s, p in probabilities.items()}

        # Top-1 argmax prediction
        predicted_sector = max(probabilities.items(), key=lambda x: x[1])[0]

        return {
            "probabilities": probabilities,
            "predicted_sector": predicted_sector,
            "support_count": total_counts,
            "fallback_level": fallback_lvl,
            "fallback_description": lvl_desc,
            "input_context": {
                "species": sp,
                "source_sector": src_sec,
                "season_code": season,
                "delta_t": dt,
                "mode": mode,
            },
        }

    def predict_persistence(self, source_sector: str) -> Dict[str, Any]:
        """
        Persistence baseline: Always predicts 'stay in the current sector' with 100% confidence.
        """
        src = str(source_sector).strip()
        probabilities = {s: 0.0 for s in self.sectors}
        if src in probabilities:
            probabilities[src] = 1.0
        else:
            probabilities[self.sectors[0]] = 1.0
            src = self.sectors[0]

        return {
            "probabilities": probabilities,
            "predicted_sector": src,
            "support_count": 1,
            "fallback_level": 0,
            "fallback_description": "Persistence Baseline (Stay in current sector)",
            "input_context": {"source_sector": src, "mode": "persistence"},
        }

    def export_transition_matrix(self) -> pd.DataFrame:
        """
        Exports sector-by-sector transition probability matrix aggregated across all seasons.
        """
        matrix = np.zeros((self.num_sectors, self.num_sectors))

        for (src_sec, season), tgt_counter in self.lvl4_counts.items():
            if src_sec not in self.sector_to_idx:
                continue
            src_i = self.sector_to_idx[src_sec]
            for tgt_sec, cnt in tgt_counter.items():
                if tgt_sec in self.sector_to_idx:
                    tgt_j = self.sector_to_idx[tgt_sec]
                    matrix[src_i, tgt_j] += cnt

        # Row-normalize
        row_sums = matrix.sum(axis=1, keepdims=True)
        prob_matrix = np.divide(matrix, row_sums, out=np.zeros_like(matrix), where=row_sums != 0)

        df = pd.DataFrame(
            np.round(prob_matrix, 4),
            index=self.sectors,
            columns=self.sectors,
        )
        return df

    def to_dict(self) -> Dict[str, Any]:
        """Serializes Markov state counters to JSON-compatible dictionary."""
        def encode_dict_keys(d):
            return {f"{k[0]}|||{k[1]}|||{k[2]}|||{k[3]}" if len(k) == 4 else
                    f"{k[0]}|||{k[1]}|||{k[2]}" if len(k) == 3 else
                    f"{k[0]}|||{k[1]}": dict(v) for k, v in d.items()}

        unique_species = sorted(list({k[0] for k in self.lvl2_counts.keys()}))

        return {
            "sectors": self.sectors,
            "min_support": self.min_support,
            "is_fitted": self.is_fitted,
            "total_training_transitions": self.total_training_transitions,
            "lvl1_counts": encode_dict_keys(self.lvl1_counts),
            "lvl2_counts": encode_dict_keys(self.lvl2_counts),
            "lvl3_counts": encode_dict_keys(self.lvl3_counts),
            "lvl4_counts": encode_dict_keys(self.lvl4_counts),
            "lvl5_counts": dict(self.lvl5_counts),
            "species_vocabulary": unique_species,
        }

    def save_model(self, filepath: str):
        """Saves Markov model artifact to JSON."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarkovDistributionBaseline":
        """Instantiates Markov model from serialized dictionary."""
        model = cls(sectors=data.get("sectors", CANONICAL_SECTORS), min_support=data.get("min_support", 3))
        model.is_fitted = data.get("is_fitted", True)
        model.total_training_transitions = data.get("total_training_transitions", 0)

        # Decode lvl1
        for k_str, counter_dict in data.get("lvl1_counts", {}).items():
            parts = k_str.split("|||")
            k = (parts[0], parts[1], int(parts[2]), int(parts[3]))
            model.lvl1_counts[k] = Counter(counter_dict)

        # Decode lvl2
        for k_str, counter_dict in data.get("lvl2_counts", {}).items():
            parts = k_str.split("|||")
            k = (parts[0], parts[1], int(parts[2]))
            model.lvl2_counts[k] = Counter(counter_dict)

        # Decode lvl3
        for k_str, counter_dict in data.get("lvl3_counts", {}).items():
            parts = k_str.split("|||")
            k = (parts[0], int(parts[1]), int(parts[2]))
            model.lvl3_counts[k] = Counter(counter_dict)

        # Decode lvl4
        for k_str, counter_dict in data.get("lvl4_counts", {}).items():
            parts = k_str.split("|||")
            k = (parts[0], int(parts[1]))
            model.lvl4_counts[k] = Counter(counter_dict)

        model.lvl5_counts = Counter(data.get("lvl5_counts", {}))
        return model

    @classmethod
    def load_model(cls, filepath: str) -> "MarkovDistributionBaseline":
        """Loads Markov model artifact from JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


def evaluate_predictions(
    y_true: List[str],
    y_prob_dicts: List[Dict[str, float]],
    sectors: Optional[List[str]] = None,
) -> Dict[str, float]:
    """
    Computes rigorous classification and calibration metrics:
    Top-1 Accuracy, Top-3 Accuracy, Macro F1, Multi-class Log Loss, Brier Score.
    """
    sec_list = sectors or CANONICAL_SECTORS
    sec_map = {s: i for i, s in enumerate(sec_list)}
    K = len(sec_list)
    N = len(y_true)

    if N == 0:
        return {"top_1_accuracy": 0.0, "top_3_accuracy": 0.0, "macro_f1": 0.0, "log_loss": 0.0, "brier_score": 0.0}

    y_true_indices = [sec_map[y] for y in y_true if y in sec_map]
    prob_matrix = np.zeros((N, K))

    for i, p_dict in enumerate(y_prob_dicts):
        for j, s in enumerate(sec_list):
            prob_matrix[i, j] = p_dict.get(s, 1e-15)

    # Normalize rows
    prob_matrix = prob_matrix / prob_matrix.sum(axis=1, keepdims=True)

    # Top-1 predictions
    y_pred_indices = np.argmax(prob_matrix, axis=1)
    top_1_acc = np.mean(y_pred_indices == y_true_indices)

    # Top-3 predictions
    top_3_indices = np.argsort(prob_matrix, axis=1)[:, -3:]
    top_3_hits = [y_true_indices[i] in top_3_indices[i] for i in range(N)]
    top_3_acc = np.mean(top_3_hits)

    # Multi-class Log Loss (Cross-Entropy with epsilon clipping)
    eps = 1e-15
    clipped_probs = np.clip(prob_matrix, eps, 1.0 - eps)
    true_probs = clipped_probs[np.arange(N), y_true_indices]
    log_loss = -np.mean(np.log(true_probs))

    # Multi-class Brier Score: 1/N * sum_i sum_k (p_ik - y_ik)^2
    one_hot = np.zeros((N, K))
    one_hot[np.arange(N), y_true_indices] = 1.0
    brier_score = np.mean(np.sum((prob_matrix - one_hot) ** 2, axis=1))

    # Macro F1 Score
    f1_list = []
    for k in range(K):
        tp = np.sum((y_pred_indices == k) & (np.array(y_true_indices) == k))
        fp = np.sum((y_pred_indices == k) & (np.array(y_true_indices) != k))
        fn = np.sum((y_pred_indices != k) & (np.array(y_true_indices) == k))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        f1_list.append(f1)

    macro_f1 = float(np.mean(f1_list))

    return {
        "top_1_accuracy": round(float(top_1_acc), 4),
        "top_3_accuracy": round(float(top_3_acc), 4),
        "macro_f1": round(macro_f1, 4),
        "log_loss": round(float(log_loss), 4),
        "brier_score": round(float(brier_score), 4),
    }
