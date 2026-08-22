"""
XGBoost Machine Learning Model for Seasonal Species Distribution Shift & Movement Propensity.

Implements:
- Model 1: Structural XGBoost (Spatial, Depth, Cyclical Season, Delta_T, Occurrence Rate)
- Model 2: Environmental XGBoost (Model 1 + Native NaN Physicochemical CTD Features)
- Model 3: Full XGBoost (Model 2 + Empirical Markov Prior Probabilities)

SCIENTIFIC PRINCIPLE:
This is a population-level seasonal distribution shift classifier predicting transition
probabilities across canonical Arabian Sea ecological sectors. It does NOT model
Lagrangian individual fish trajectories.
"""

from dataclasses import asdict, dataclass
import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from data_pipeline.fusion.spatial import haversine_distance_km
from ml.distribution_shift.markov_baseline import CANONICAL_SECTORS, MarkovDistributionBaseline

logger = logging.getLogger(__name__)

# Sector geographic centroids (lat, lon) for displacement error calculations
SECTOR_CENTROIDS: Dict[str, Tuple[float, float]] = {
    "Malabar Upwelling Shelf": (10.5, 75.5),
    "Central Arabian Sea Offshore Basin": (16.0, 68.0),
    "North Arabian Sea / Gujarat Shelf": (21.5, 69.5),
    "Lakshadweep Sea & Ridge": (10.5, 72.5),
    "Wadge Bank / Comorin Sector": (7.5, 77.5),
    "Konkan Coast / Central West Coast": (16.5, 73.0),
    "South-Eastern Arabian Sea EEZ": (9.0, 76.5),
}

# Feature definitions for Model 1, Model 2, Model 3
STRUCTURAL_FEATURES = [
    "species_code",
    "sector_code",
    "current_lat",
    "current_lon",
    "mean_depth_meters",
    "season_code",
    "month_sin",
    "month_cos",
    "delta_t",
    "historical_occurrence_rate",
]

ENVIRONMENTAL_FEATURES = STRUCTURAL_FEATURES + [
    "sst_celsius",
    "salinity_psu",
    "dissolved_oxygen_mgl",
    "chlorophyll_mg_m3",
    "has_environmental_context",
]

MARKOV_PRIOR_FEATURES = [f"markov_prior_{i}" for i in range(len(CANONICAL_SECTORS))]
FULL_FEATURES = ENVIRONMENTAL_FEATURES + MARKOV_PRIOR_FEATURES


class DistributionFeatureExtractor:
    """
    Transforms raw transition records into strictly validated feature matrices without data leakage.
    """

    def __init__(self, sectors: Optional[List[str]] = None):
        self.sectors = sectors or CANONICAL_SECTORS
        self.sector_to_idx = {s: i for i, s in enumerate(self.sectors)}
        self.species_to_code: Dict[str, int] = {}
        self.is_fitted: bool = False

    def fit(self, transitions: List[Dict[str, Any]]) -> "DistributionFeatureExtractor":
        """Learns species vocabulary from training transitions."""
        unique_species = sorted(list({
            str(t.get("scientific_name") or t.get("species_id") or "unknown").strip()
            for t in transitions
        }))
        self.species_to_code = {sp: i + 1 for i, sp in enumerate(unique_species)}  # 0 reserved for unknown
        self.is_fitted = True
        return self

    def transform(
        self,
        transitions: List[Dict[str, Any]],
        model_type: str = "environmental",  # 'structural', 'environmental', or 'full'
        markov_model: Optional[MarkovDistributionBaseline] = None,
    ) -> Tuple[pd.DataFrame, np.ndarray, List[str]]:
        """
        Extracts feature matrix X and target vector y.
        """
        if not self.is_fitted:
            raise RuntimeError("DistributionFeatureExtractor must be fitted on training data before transform.")

        feature_names = (
            STRUCTURAL_FEATURES if model_type == "structural"
            else ENVIRONMENTAL_FEATURES if model_type == "environmental"
            else FULL_FEATURES
        )

        rows_x = []
        rows_y = []

        for t in transitions:
            sp = str(t.get("scientific_name") or t.get("species_id") or "unknown").strip()
            sp_code = self.species_to_code.get(sp, 0)

            src_sec = str(t.get("current_sector") or "").strip()
            sec_code = self.sector_to_idx.get(src_sec, 0)

            lat = float(t.get("current_lat", 0.0))
            lon = float(t.get("current_lon", 0.0))

            depth = float(t["mean_depth_meters"]) if t.get("mean_depth_meters") is not None else np.nan
            season_code = int(t.get("season_code", 1))

            m_src = int(t.get("month", 1))
            m_tgt = int(t.get("target_month", m_src))
            delta_t = (m_tgt - m_src) % 12
            if delta_t == 0:
                delta_t = 1

            month_sin = round(math.sin(2 * math.pi * m_src / 12.0), 4)
            month_cos = round(math.cos(2 * math.pi * m_src / 12.0), 4)
            hist_rate = float(t.get("historical_occurrence_rate", 0.0))

            feat_dict: Dict[str, Any] = {
                "species_code": sp_code,
                "sector_code": sec_code,
                "current_lat": lat,
                "current_lon": lon,
                "mean_depth_meters": depth,
                "season_code": season_code,
                "month_sin": month_sin,
                "month_cos": month_cos,
                "delta_t": delta_t,
                "historical_occurrence_rate": hist_rate,
            }

            if model_type in ("environmental", "full"):
                sst = float(t["sst_celsius"]) if t.get("sst_celsius") is not None else np.nan
                sal = float(t["salinity_psu"]) if t.get("salinity_psu") is not None else np.nan
                do = float(t["dissolved_oxygen_mgl"]) if t.get("dissolved_oxygen_mgl") is not None else np.nan
                chl = float(t["chlorophyll_mg_m3"]) if t.get("chlorophyll_mg_m3") is not None else np.nan
                has_env = 1.0 if not np.isnan(sst) else 0.0

                feat_dict.update({
                    "sst_celsius": sst,
                    "salinity_psu": sal,
                    "dissolved_oxygen_mgl": do,
                    "chlorophyll_mg_m3": chl,
                    "has_environmental_context": has_env,
                })

            if model_type == "full":
                if markov_model is not None:
                    m_pred = markov_model.predict_distribution(
                        species=sp,
                        source_sector=src_sec,
                        season_code=season_code,
                        delta_t=delta_t,
                        mode="species_conditioned"
                    )
                    probs = m_pred["probabilities"]
                    for i, s in enumerate(self.sectors):
                        feat_dict[f"markov_prior_{i}"] = float(probs.get(s, 0.0))
                else:
                    for i in range(len(self.sectors)):
                        feat_dict[f"markov_prior_{i}"] = 1.0 / len(self.sectors)

            tgt_sec = str(t.get("target_sector") or "").strip()
            tgt_code = self.sector_to_idx.get(tgt_sec, -1)

            rows_x.append(feat_dict)
            rows_y.append(tgt_code)

        df_x = pd.DataFrame(rows_x)[feature_names]
        arr_y = np.array(rows_y, dtype=int)
        return df_x, arr_y, feature_names

    def to_dict(self) -> Dict[str, Any]:
        """Serializes feature extractor metadata and vocabulary."""
        return {
            "sectors": self.sectors,
            "sector_to_idx": self.sector_to_idx,
            "species_to_code": self.species_to_code,
            "is_fitted": self.is_fitted,
        }

    def save(self, filepath: str):
        """Saves extractor schema and vocabulary to JSON."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "DistributionFeatureExtractor":
        """Loads extractor schema and vocabulary from JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        fe = cls(sectors=data.get("sectors", CANONICAL_SECTORS))
        fe.sector_to_idx = data.get("sector_to_idx", {s: i for i, s in enumerate(fe.sectors)})
        fe.species_to_code = data.get("species_to_code", {})
        fe.is_fitted = data.get("is_fitted", True)
        return fe


class XGBoostMovementClassifier:
    """
    Multi-Class XGBoost Model for Ecological Sector Shift Prediction.
    """

    def __init__(
        self,
        model_type: str = "environmental",  # 'structural', 'environmental', or 'full'
        n_estimators: int = 100,
        max_depth: int = 4,
        learning_rate: float = 0.05,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        random_state: int = 42,
    ):
        self.model_type = model_type
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.random_state = random_state
        self.sectors = CANONICAL_SECTORS
        self.num_classes = len(self.sectors)

        self.model = None
        self.feature_names: List[str] = []
        self.is_fitted: bool = False

    def fit(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        eval_set: Optional[List[Tuple[pd.DataFrame, np.ndarray]]] = None,
        early_stopping_rounds: Optional[int] = 15,
    ) -> "XGBoostMovementClassifier":
        """Fits XGBoost multi-class classifier."""
        import xgboost as xgb

        self.feature_names = list(X.columns)

        self.model = xgb.XGBClassifier(
            objective="multi:softprob",
            num_class=self.num_classes,
            eval_metric="mlogloss",
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            random_state=self.random_state,
            tree_method="hist",
            n_jobs=1,
        )

        fit_kwargs: Dict[str, Any] = {}
        if eval_set is not None:
            fit_kwargs["eval_set"] = eval_set
            fit_kwargs["verbose"] = False

        self.model.fit(X, y, **fit_kwargs)
        self.is_fitted = True
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Returns N x 7 probability array."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict_proba.")
        return self.model.predict_proba(X[self.feature_names])

    def predict(self, X: pd.DataFrame) -> List[str]:
        """Returns predicted sector name strings."""
        probs = self.predict_proba(X)
        pred_indices = np.argmax(probs, axis=1)
        return [self.sectors[idx] for idx in pred_indices]

    def get_feature_importances(self) -> pd.DataFrame:
        """Returns feature importance by gain and weight."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before get_feature_importances.")

        booster = self.model.get_booster()
        gain_dict = booster.get_score(importance_type="gain")
        weight_dict = booster.get_score(importance_type="weight")

        records = []
        for feat in self.feature_names:
            records.append({
                "feature": feat,
                "gain": float(gain_dict.get(feat, 0.0)),
                "weight": float(weight_dict.get(feat, 0.0)),
            })

        df = pd.DataFrame(records).sort_values("gain", ascending=False)
        total_gain = df["gain"].sum()
        df["gain_pct"] = (df["gain"] / total_gain * 100).round(2) if total_gain > 0 else 0.0
        return df

    def save_model(self, filepath: str):
        """Saves model to JSON artifact."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before save.")
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        self.model.save_model(filepath)

    def load_model(self, filepath: str):
        """Loads model from JSON artifact."""
        import xgboost as xgb
        self.model = xgb.XGBClassifier()
        self.model.load_model(filepath)
        self.is_fitted = True


def calculate_geographic_displacement_error(
    y_true_sectors: List[str],
    y_pred_sectors: List[str],
) -> Dict[str, float]:
    """
    Calculates geographic displacement error in kilometers between predicted sector
    centroid and true target sector centroid.
    """
    errors_km = []
    for true_sec, pred_sec in zip(y_true_sectors, y_pred_sectors):
        true_c = SECTOR_CENTROIDS.get(true_sec)
        pred_c = SECTOR_CENTROIDS.get(pred_sec)
        if true_c and pred_c:
            dist = haversine_distance_km(pred_c[0], pred_c[1], true_c[0], true_c[1])
            errors_km.append(dist)

    err_s = pd.Series(errors_km) if errors_km else pd.Series([0.0])
    return {
        "mean_displacement_error_km": round(float(err_s.mean()), 2),
        "median_displacement_error_km": round(float(err_s.median()), 2),
        "p90_displacement_error_km": round(float(err_s.quantile(0.90)), 2),
        "max_displacement_error_km": round(float(err_s.max()), 2),
    }
