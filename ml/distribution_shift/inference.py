"""
Production Inference Service for Seasonal Species Distribution Shift Prediction.

Scientific Scope:
- Eulerian population-level seasonal distribution shift & movement propensity.
- Probabilistic dispersal forecasting across 7 canonical Arabian Sea ecological sectors.
- Strictly avoids individual fish tracking / telemetry claims.
"""

from dataclasses import asdict, dataclass
import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from ml.distribution_shift.markov_baseline import CANONICAL_SECTORS, MarkovDistributionBaseline
from ml.distribution_shift.movement_model import (
    DistributionFeatureExtractor,
    SECTOR_CENTROIDS,
    XGBoostMovementClassifier,
)

logger = logging.getLogger(__name__)

# Default artifact paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_ARTIFACT_PATH = BASE_DIR / "data_pipeline" / "output" / "models" / "model3_full_xgboost.json"
FEATURE_EXTRACTOR_PATH = BASE_DIR / "data_pipeline" / "output" / "models" / "feature_extractor.json"
MARKOV_ARTIFACT_PATH = BASE_DIR / "data_pipeline" / "output" / "baseline" / "markov_model.json"

# Common name synonyms mapping for robust user queries
SPECIES_SYNONYMS: Dict[str, str] = {
    "indian oil sardine": "Sardinella longiceps",
    "oil sardine": "Sardinella longiceps",
    "sardine": "Sardinella longiceps",
    "sardinella longiceps": "Sardinella longiceps",
    "indian mackerel": "Rastrelliger kanagurta",
    "mackerel": "Rastrelliger kanagurta",
    "rastrelliger kanagurta": "Rastrelliger kanagurta",
    "indian anchovy": "Stolephorus indicus",
    "anchovy": "Stolephorus indicus",
    "stolephorus indicus": "Stolephorus indicus",
    "yellowfin tuna": "Thunnus albacares",
    "yellowfin": "Thunnus albacares",
    "thunnus albacares": "Thunnus albacares",
    "skipjack tuna": "Katsuwonus pelamis",
    "skipjack": "Katsuwonus pelamis",
    "katsuwonus pelamis": "Katsuwonus pelamis",
}

# Empirical confidence tier boundaries from calibration analysis
CONFIDENCE_HIGH_THRESHOLD = 0.70
CONFIDENCE_MODERATE_THRESHOLD = 0.40

MODEL_METADATA = {
    "model_version": "3.0.0-full-xgboost-oof",
    "training_period": "Historical surveys through 2023-12-31 (N=2,577 transitions)",
    "target_definition": "7 Canonical Arabian Sea Ecological Sectors",
    "validation_summary": {
        "shifted_only_top1_accuracy": 0.4897,
        "shifted_only_top3_accuracy": 0.9829,
        "historical_overall_top1_accuracy": 0.7478,
        "historical_overall_top3_accuracy": 0.9922,
        "temporal_holdout_top3_accuracy": 0.8445,
    },
    "limitations": [
        "Eulerian population-level seasonal distribution shift, not individual fish tracking.",
        "Missing environmental sensors (SST/Sal/DO/Chl) are handled natively via NaN decision tree routing without zero imputation.",
        "Predictions represent probabilistic population movement propensity for spatial planning and decision support.",
    ],
}


class DistributionShiftInferenceEngine:
    """
    Singleton production engine for loading and executing Full XGBoost distribution-shift inference.
    """

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        extractor_path: Optional[Union[str, Path]] = None,
        markov_path: Optional[Union[str, Path]] = None,
    ):
        self.model_path = Path(model_path or MODEL_ARTIFACT_PATH)
        self.extractor_path = Path(extractor_path or FEATURE_EXTRACTOR_PATH)
        self.markov_path = Path(markov_path or MARKOV_ARTIFACT_PATH)

        self.model: Optional[XGBoostMovementClassifier] = None
        self.feature_extractor: Optional[DistributionFeatureExtractor] = None
        self.markov_baseline: Optional[MarkovDistributionBaseline] = None
        self._is_initialized: bool = False

    def load(self) -> "DistributionShiftInferenceEngine":
        """Loads all model artifacts into memory."""
        if not self.extractor_path.exists():
            raise FileNotFoundError(f"Feature extractor artifact missing at: {self.extractor_path}")
        if not self.model_path.exists():
            raise FileNotFoundError(f"XGBoost model artifact missing at: {self.model_path}")
        if not self.markov_path.exists():
            raise FileNotFoundError(f"Markov baseline artifact missing at: {self.markov_path}")

        # 1. Feature Extractor
        self.feature_extractor = DistributionFeatureExtractor.load(str(self.extractor_path))

        # 2. Markov Prior Baseline
        self.markov_baseline = MarkovDistributionBaseline.load_model(str(self.markov_path))

        # 3. XGBoost Movement Classifier
        self.model = XGBoostMovementClassifier(model_type="full")
        self.model.feature_names = self.feature_extractor.sectors  # Temp
        self.model.load_model(str(self.model_path))
        # Set full feature names from extractor schema
        from ml.distribution_shift.movement_model import FULL_FEATURES
        self.model.feature_names = FULL_FEATURES

        self._is_initialized = True
        logger.info("DistributionShiftInferenceEngine loaded successfully.")
        return self

    def predict(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates input request and runs deterministic probabilistic prediction.
        """
        if not self._is_initialized:
            self.load()

        validated = self._validate_and_sanitize_request(request_data)

        # Build single-row transition dictionary
        transition_row = {
            "scientific_name": validated["species"],
            "current_sector": validated["current_sector"],
            "current_lat": validated["current_lat"],
            "current_lon": validated["current_lon"],
            "mean_depth_meters": validated["mean_depth_meters"],
            "season_code": validated["season_code"],
            "month": validated["month"],
            "target_month": validated["target_month"],
            "historical_occurrence_rate": validated.get("historical_occurrence_rate", 0.10),
            "sst_celsius": validated["sst_celsius"],
            "salinity_psu": validated["salinity_psu"],
            "dissolved_oxygen_mgl": validated["dissolved_oxygen_mgl"],
            "chlorophyll_mg_m3": validated["chlorophyll_mg_m3"],
        }

        # Transform using feature extractor + Markov priors
        df_x, _, _ = self.feature_extractor.transform(
            [transition_row],
            model_type="full",
            markov_model=self.markov_baseline,
        )

        # Run XGBoost inference
        raw_probs = self.model.predict_proba(df_x)[0]

        # Normalize and round probabilities
        sum_p = float(np.sum(raw_probs))
        norm_probs = [float(p / sum_p) if sum_p > 0 else 1.0 / len(CANONICAL_SECTORS) for p in raw_probs]

        # Build sector probability map
        prob_dist = {CANONICAL_SECTORS[i]: round(norm_probs[i], 4) for i in range(len(CANONICAL_SECTORS))}

        # Top predictions sorted descending
        ranked_sectors = sorted(
            [{"sector": CANONICAL_SECTORS[i], "probability": round(norm_probs[i], 4), "centroid": SECTOR_CENTROIDS.get(CANONICAL_SECTORS[i])}
             for i in range(len(CANONICAL_SECTORS))],
            key=lambda x: x["probability"],
            reverse=True,
        )

        top_pred = ranked_sectors[0]
        top_3 = ranked_sectors[:3]

        # Confidence Tier
        p_top = top_pred["probability"]
        if p_top >= CONFIDENCE_HIGH_THRESHOLD:
            conf_tier = "High model confidence (Empirical accuracy ~65-75%)"
            conf_level = "HIGH"
        elif p_top >= CONFIDENCE_MODERATE_THRESHOLD:
            conf_tier = "Moderate confidence (Seasonal dispersal signal present)"
            conf_level = "MODERATE"
        else:
            conf_tier = "High uncertainty (Wide probabilistic spread across sectors)"
            conf_level = "LOW"

        # Markov prior baseline output for comparison
        m_pred = self.markov_baseline.predict_distribution(
            species=validated["species"],
            source_sector=validated["current_sector"],
            season_code=validated["season_code"],
            delta_t=validated["forecast_horizon_months"],
            mode="species_conditioned",
        )

        # Calculate target season code
        target_month = validated["target_month"]
        if target_month in (2, 3, 4, 5):
            target_season_code = 1
        elif target_month in (6, 7, 8, 9):
            target_season_code = 2
        else:
            target_season_code = 3

        season_name_map = {
            1: "Pre-Monsoon (Feb-May)",
            2: "SW Monsoon (Jun-Sep)",
            3: "Post-Monsoon (Oct-Jan)",
        }

        forecast_dict = {
            "source_month": validated["month"],
            "target_month": target_month,
            "source_season": {
                "season_code": validated["season_code"],
                "season_name": season_name_map.get(validated["season_code"]),
            },
            "target_season": {
                "season_code": target_season_code,
                "season_name": season_name_map.get(target_season_code),
            },
        }

        return {
            "species": validated["species"],
            "prediction_type": "seasonal_distribution_shift",
            "source_sector": validated["current_sector"],
            "source_coordinates": {
                "latitude": validated["current_lat"],
                "longitude": validated["current_lon"],
            },
            "forecast_horizon_months": validated["forecast_horizon_months"],
            "forecast": forecast_dict,
            "top_prediction": top_pred,
            "top_3_predictions": top_3,
            "probability_distribution": prob_dist,
            "confidence_tier": conf_tier,
            "confidence_level": conf_level,
            "environmental_context_available": validated["has_environmental_context"],
            "environmental_inputs": {
                "sst_celsius": validated["sst_celsius"],
                "salinity_psu": validated["salinity_psu"],
                "dissolved_oxygen_mgl": validated["dissolved_oxygen_mgl"],
                "chlorophyll_mg_m3": validated["chlorophyll_mg_m3"],
                "mean_depth_meters": validated["mean_depth_meters"],
            },
            "markov_baseline_comparison": {
                "top_markov_sector": m_pred["predicted_sector"],
                "markov_probability": round(float(m_pred["probabilities"][m_pred["predicted_sector"]]), 4),
                "fallback_level": m_pred["fallback_level"],
                "fallback_description": m_pred["fallback_description"],
            },
            "model_metadata": MODEL_METADATA,
            "limitations": MODEL_METADATA["limitations"],
        }

    def _validate_and_sanitize_request(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """Validates all input parameters according to scientific domain boundaries."""
        # 1. Species validation & synonym resolution
        raw_sp = str(req.get("species_id") or req.get("species") or "").strip()
        if not raw_sp:
            raise ValueError("Parameter 'species_id' or 'species' is required and cannot be empty.")

        sp_clean = SPECIES_SYNONYMS.get(raw_sp.lower(), raw_sp)

        # Check vocabulary support
        if self.feature_extractor and sp_clean not in self.feature_extractor.species_to_code:
            # Fallback check for case-insensitive match in vocabulary
            vocab_lower = {k.lower(): k for k in self.feature_extractor.species_to_code}
            if sp_clean.lower() in vocab_lower:
                sp_clean = vocab_lower[sp_clean.lower()]
            else:
                raise ValueError(
                    f"Species '{raw_sp}' is not in the trained species vocabulary. "
                    f"Please select one of the supported Arabian Sea species."
                )

        # 2. Sector validation
        current_sector = str(req.get("current_sector") or "").strip()
        if not current_sector or current_sector not in CANONICAL_SECTORS:
            raise ValueError(
                f"Invalid 'current_sector': '{current_sector}'. "
                f"Must be one of: {CANONICAL_SECTORS}"
            )

        # 3. Spatial coordinate validation (Arabian Sea boundaries)
        raw_lat = req.get("latitude") if "latitude" in req else req.get("current_lat")
        raw_lon = req.get("longitude") if "longitude" in req else req.get("current_lon")

        try:
            if raw_lat is None or raw_lon is None:
                raise ValueError()
            lat = float(raw_lat)
            lon = float(raw_lon)
            if not (math.isfinite(lat) and math.isfinite(lon)):
                raise ValueError()
        except (KeyError, TypeError, ValueError):
            raise ValueError("Parameters 'latitude'/'current_lat' and 'longitude'/'current_lon' are required and must be valid finite floats.")

        if not (6.0 <= lat <= 24.0 and 65.0 <= lon <= 78.5):
            raise ValueError(
                f"Coordinates ({lat:.2f}N, {lon:.2f}E) fall outside the Arabian Sea bounds "
                f"(6.0°N-24.0°N, 65.0°E-78.5°E)."
            )

        # 4. Temporal parameters
        try:
            month = int(req.get("month", 1))
            if not (1 <= month <= 12):
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Parameter 'month' must be an integer between 1 and 12.")

        # Delta T (forecast horizon in months)
        try:
            raw_dt = req.get("forecast_horizon_months") if "forecast_horizon_months" in req else req.get("delta_t", 2)
            delta_t = int(raw_dt if raw_dt is not None else 2)
            if not (1 <= delta_t <= 11):
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Parameter 'forecast_horizon_months' must be an integer between 1 and 11.")

        target_month = ((month - 1 + delta_t) % 12) + 1

        # Season code: 1: Pre-Monsoon (Feb-May), 2: SW Monsoon (Jun-Sep), 3: Post-Monsoon (Oct-Jan)
        if "season_code" in req and req["season_code"] is not None:
            try:
                season_code = int(req["season_code"])
                if season_code not in (1, 2, 3):
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValueError("Parameter 'season_code' must be 1 (Pre-Monsoon), 2 (SW Monsoon), or 3 (Post-Monsoon).")
        else:
            # Infer from month
            if month in (2, 3, 4, 5):
                season_code = 1
            elif month in (6, 7, 8, 9):
                season_code = 2
            else:
                season_code = 3

        # 5. Depth and Environmental measurements (Preserve None / NaN)
        depth = float(req["mean_depth_meters"]) if req.get("mean_depth_meters") is not None else None
        sst = float(req["sst_celsius"]) if req.get("sst_celsius") is not None else None
        sal = float(req["salinity_psu"]) if req.get("salinity_psu") is not None else None
        do = float(req["dissolved_oxygen_mgl"]) if req.get("dissolved_oxygen_mgl") is not None else None
        chl = float(req["chlorophyll_mg_m3"]) if req.get("chlorophyll_mg_m3") is not None else None

        has_env = (sst is not None)

        return {
            "species": sp_clean,
            "current_sector": current_sector,
            "current_lat": lat,
            "current_lon": lon,
            "month": month,
            "forecast_horizon_months": delta_t,
            "target_month": target_month,
            "season_code": season_code,
            "mean_depth_meters": depth,
            "sst_celsius": sst,
            "salinity_psu": sal,
            "dissolved_oxygen_mgl": do,
            "chlorophyll_mg_m3": chl,
            "has_environmental_context": has_env,
        }


# Global singleton engine instance
_global_engine: Optional[DistributionShiftInferenceEngine] = None


def get_inference_engine() -> DistributionShiftInferenceEngine:
    """Returns the initialized singleton inference engine."""
    global _global_engine
    if _global_engine is None:
        _global_engine = DistributionShiftInferenceEngine().load()
    return _global_engine


def predict_distribution_shift(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Primary production entrypoint for Seasonal Species Distribution Shift Prediction.
    """
    engine = get_inference_engine()
    return engine.predict(request)
