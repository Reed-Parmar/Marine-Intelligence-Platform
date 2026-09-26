"""
Inference Module for Fisheries Catch Prediction V1 (Phase 14.3).
Provides single-record and batch prediction interfaces with strict input validation,
feature engineering (monsoons, cyclic features, log effort), and tuned XGBoost inference.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb

from .pipeline import ALL_INPUT_FEATURES, engineer_features

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_MODEL_DIR = ROOT_DIR / "models" / "fisheries_catch"
FALLBACK_MODEL_DIR = ROOT_DIR / "fisheries_catch_prediction" / "integration_package" / "model"

REQUIRED_COLUMNS = ["Fleet", "Gear", "Effort", "EffortUnits", "Month", "Year", "Latitude", "Longitude"]

_GLOBAL_PREDICTOR: Optional["FisheriesCatchPredictor"] = None


class FisheriesCatchPredictor:
    """
    Production inference engine for Fisheries Catch Prediction V1.
    Encapsulates preprocessing, feature engineering, and tuned XGBoost regression.
    """

    def __init__(self, model_dir: Optional[Union[str, Path]] = None):
        if model_dir is not None:
            self.model_dir = Path(model_dir)
        elif DEFAULT_MODEL_DIR.exists():
            self.model_dir = DEFAULT_MODEL_DIR
        elif FALLBACK_MODEL_DIR.exists():
            self.model_dir = FALLBACK_MODEL_DIR
        else:
            self.model_dir = DEFAULT_MODEL_DIR

        self.preprocessor_path = self.model_dir / "preprocessing.joblib"
        self.joblib_model_path = self.model_dir / "final_model.joblib"
        self.json_model_path = self.model_dir / "final_model.json"
        self.schema_path = self.model_dir / "feature_schema.json"
        self.metadata_path = self.model_dir / "model_metadata.json"

        self.preprocessor = None
        self.model = None
        self.metadata: Dict[str, Any] = {}
        self.schema: Dict[str, Any] = {}
        self.is_loaded: bool = False

        self._load_artifacts()

    def _load_artifacts(self):
        """Loads serialized preprocessing pipeline, XGBoost model, and metadata."""
        if not self.preprocessor_path.exists():
            raise FileNotFoundError(f"Preprocessor artifact not found at {self.preprocessor_path}")
        self.preprocessor = joblib.load(self.preprocessor_path)

        # Load XGBoost model
        if self.joblib_model_path.exists():
            self.model = joblib.load(self.joblib_model_path)
        elif self.json_model_path.exists():
            self.model = xgb.XGBRegressor()
            self.model._estimator_type = "regressor"
            self.model.load_model(str(self.json_model_path))
        else:
            raise FileNotFoundError(f"XGBoost model file not found in {self.model_dir}")

        if self.metadata_path.exists():
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

        if self.schema_path.exists():
            with open(self.schema_path, "r", encoding="utf-8") as f:
                self.schema = json.load(f)

        self.is_loaded = True
        logger.info(f"Fisheries Catch Predictor V1 loaded from {self.model_dir}")

    def validate_inputs(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validates input DataFrame schema and parameter domains."""
        # Support case-insensitive or common alias mappings
        col_aliases = {
            "fleet": "Fleet",
            "gear": "Gear",
            "effort": "Effort",
            "effort_units": "EffortUnits",
            "effortunits": "EffortUnits",
            "month": "Month",
            "year": "Year",
            "latitude": "Latitude",
            "lat": "Latitude",
            "longitude": "Longitude",
            "lon": "Longitude",
            "spatial_resolution": "SpatialResolution",
            "spatialresolution": "SpatialResolution",
        }
        for col in list(df.columns):
            norm = col_aliases.get(col.lower())
            if norm and norm not in df.columns:
                df[norm] = df[col]

        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Input data is missing required fisheries parameters: {missing}")

        df_val = df.copy()

        # Clean string columns
        df_val["Fleet"] = df_val["Fleet"].astype(str).str.strip().str.upper()
        df_val["Gear"] = df_val["Gear"].astype(str).str.strip().str.upper()
        df_val["EffortUnits"] = df_val["EffortUnits"].astype(str).str.strip().str.upper()

        # Check numeric conversions
        try:
            df_val["Effort"] = pd.to_numeric(df_val["Effort"], errors="raise").astype(float)
            df_val["Month"] = pd.to_numeric(df_val["Month"], errors="raise").astype(int)
            df_val["Year"] = pd.to_numeric(df_val["Year"], errors="raise").astype(int)
            df_val["Latitude"] = pd.to_numeric(df_val["Latitude"], errors="raise").astype(float)
            df_val["Longitude"] = pd.to_numeric(df_val["Longitude"], errors="raise").astype(float)
        except Exception as e:
            raise ValueError(f"Error casting numeric fields: {e}")

        # Range checks
        if (df_val["Month"] < 1).any() or (df_val["Month"] > 12).any():
            raise ValueError("Month values must be integers between 1 and 12.")
        if (df_val["Effort"] < 0).any():
            raise ValueError("Fishing effort cannot be negative.")
        if (df_val["Latitude"] < -90).any() or (df_val["Latitude"] > 90).any():
            raise ValueError("Latitude values must be between -90 and +90.")
        if (df_val["Longitude"] < -180).any() or (df_val["Longitude"] > 180).any():
            raise ValueError("Longitude values must be between -180 and +180.")

        if "SpatialResolution" not in df_val.columns:
            df_val["SpatialResolution"] = 1.0
        else:
            df_val["SpatialResolution"] = pd.to_numeric(df_val["SpatialResolution"], errors="coerce").fillna(1.0)

        return df_val

    def predict(
        self,
        input_data: Union[Dict[str, Any], List[Dict[str, Any]], pd.DataFrame],
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Executes prediction on a single record, list of records, or DataFrame.
        Returns continuous catch prediction in Metric Tons (MT).
        """
        is_single = isinstance(input_data, dict)
        if is_single:
            df_in = pd.DataFrame([input_data])
        elif isinstance(input_data, list):
            df_in = pd.DataFrame(input_data)
        elif isinstance(input_data, pd.DataFrame):
            df_in = input_data.copy()
        else:
            raise TypeError("input_data must be a dict, list of dicts, or pandas DataFrame.")

        if len(df_in) == 0:
            return [] if not is_single else {}

        # 1. Validation
        df_valid = self.validate_inputs(df_in)

        # 2. Feature Engineering
        df_feat = engineer_features(df_valid)

        # 3. Preprocessing (One-Hot & Passthrough)
        X_trans = self.preprocessor.transform(df_feat[ALL_INPUT_FEATURES])

        # 4. Predict & Post-process
        preds = self.model.predict(X_trans)
        preds = np.clip(preds, 0.0, None)  # Ensure non-negative catch

        results = []
        for i, pred_val in enumerate(preds):
            fleet_val = str(df_valid.iloc[i]["Fleet"])
            gear_val = str(df_valid.iloc[i]["Gear"])
            effort_val = float(df_valid.iloc[i]["Effort"])
            units_val = str(df_valid.iloc[i]["EffortUnits"])
            month_val = int(df_valid.iloc[i]["Month"])
            year_val = int(df_valid.iloc[i]["Year"])
            lat_val = float(df_valid.iloc[i]["Latitude"])
            lon_val = float(df_valid.iloc[i]["Longitude"])
            season_val = str(df_feat.iloc[i]["MonsoonSeason"])
            log_effort_val = float(df_feat.iloc[i]["Log_Effort"])

            res = {
                "predicted_catch_mt": round(float(pred_val), 2),
                "unit": "Metric Tons (MT)",
                "model": self.metadata.get("model_type", "XGBoost Regressor (Tuned)"),
                "model_version": self.metadata.get("model_version", "1.0.0"),
                "target_variable": "TotalCatchMT",
                "disclaimer": "Predicted catch is an estimated expectation based on historical IOTC surface fisheries operational strata and not a guaranteed actual harvest.",
                "input_summary": {
                    "fleet": fleet_val,
                    "gear": gear_val,
                    "effort": effort_val,
                    "effort_units": units_val,
                    "month": month_val,
                    "year": year_val,
                    "latitude": lat_val,
                    "longitude": lon_val,
                    "season": season_val,
                    "log_effort": round(log_effort_val, 4),
                },
            }
            results.append(res)

        return results[0] if is_single else results

    def predict_batch(self, df_or_records: Union[List[Dict[str, Any]], pd.DataFrame]) -> List[Dict[str, Any]]:
        """Batch prediction convenience wrapper."""
        res = self.predict(df_or_records)
        return [res] if isinstance(res, dict) else res


def get_fisheries_predictor(model_dir: Optional[Union[str, Path]] = None) -> FisheriesCatchPredictor:
    """Returns singleton instance of FisheriesCatchPredictor."""
    global _GLOBAL_PREDICTOR
    if _GLOBAL_PREDICTOR is None or model_dir is not None:
        _GLOBAL_PREDICTOR = FisheriesCatchPredictor(model_dir=model_dir)
    return _GLOBAL_PREDICTOR


def predict_catch(
    input_data: Union[Dict[str, Any], List[Dict[str, Any]], pd.DataFrame],
    model_dir: Optional[Union[str, Path]] = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Functional interface for predicting fisheries catch."""
    predictor = get_fisheries_predictor(model_dir=model_dir)
    return predictor.predict(input_data)
