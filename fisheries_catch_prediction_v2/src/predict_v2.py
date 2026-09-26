"""
Inference Module for Fisheries Catch Prediction V2.
Provides single-record and high-throughput batch prediction interfaces with input validation
and automated feature engineering (detecting matching V1 or V2 preprocessing).
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Union, Any

from fisheries_catch_prediction.src.pipeline import (
    ALL_INPUT_FEATURES as V1_INPUT_FEATURES,
    engineer_features as engineer_features_v1
)
from fisheries_catch_prediction_v2.src.features_v2 import (
    ALL_FEATURES_V2,
    engineer_features_v2
)


REQUIRED_COLUMNS = ["Fleet", "Gear", "Effort", "EffortUnits", "Month", "Year", "Latitude", "Longitude"]


class FisheriesCatchPredictorV2:
    """
    Production inference engine for Fisheries Catch Prediction V2.
    Loads V2 trained model, matching preprocessor, and metadata.
    """
    def __init__(self, model_dir: str = None):
        if model_dir is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            model_dir = os.path.join(base_dir, "models", "final_model")

        self.model_dir = model_dir
        self.preprocessor_path = os.path.join(model_dir, "preprocessing.joblib")
        self.model_path = os.path.join(model_dir, "final_model.joblib")
        self.schema_path = os.path.join(model_dir, "feature_schema.json")
        self.metadata_path = os.path.join(model_dir, "model_metadata.json")

        self._load_artifacts()

    def _load_artifacts(self):
        """Load preprocessing pipeline, model, and metadata."""
        if not os.path.exists(self.preprocessor_path):
            raise FileNotFoundError(f"Preprocessor not found at {self.preprocessor_path}")
        self.preprocessor = joblib.load(self.preprocessor_path)

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found at {self.model_path}")
        self.model = joblib.load(self.model_path)

        self.metadata = {}
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r") as f:
                self.metadata = json.load(f)

        self.schema = {}
        if os.path.exists(self.schema_path):
            with open(self.schema_path, "r") as f:
                self.schema = json.load(f)

        # Detect feature version: V1 (48 features) vs V2 (391 features)
        self.feature_version = self.schema.get("feature_version", "v1")
        if hasattr(self.preprocessor, "transformers_"):
            n_cats = len(self.preprocessor.transformers_[0][2])
            if n_cats > 6:
                self.feature_version = "v2"
            else:
                self.feature_version = "v1"

    def validate_inputs(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate input dataframe, enforce data types and physical value bounds."""
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Input data is missing required fisheries columns: {missing}")

        df_val = df.copy()

        # Clean string columns
        df_val["Fleet"] = df_val["Fleet"].astype(str).str.strip()
        df_val["Gear"] = df_val["Gear"].astype(str).str.strip()
        df_val["EffortUnits"] = df_val["EffortUnits"].astype(str).str.strip()

        # Numeric conversions
        try:
            df_val["Effort"] = pd.to_numeric(df_val["Effort"], errors="raise")
            df_val["Month"] = pd.to_numeric(df_val["Month"], errors="raise").astype(int)
            df_val["Year"] = pd.to_numeric(df_val["Year"], errors="raise").astype(int)
            df_val["Latitude"] = pd.to_numeric(df_val["Latitude"], errors="raise")
            df_val["Longitude"] = pd.to_numeric(df_val["Longitude"], errors="raise")
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

        return df_val

    def predict(self, input_data: Union[Dict[str, Any], List[Dict[str, Any]], pd.DataFrame]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Execute continuous catch prediction on single dict, list of dicts, or DataFrame.
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

        # 1. Input Validation
        df_valid = self.validate_inputs(df_in)

        # 2. Feature Engineering matching the loaded preprocessor
        if self.feature_version == "v2":
            df_feat = engineer_features_v2(df_valid)
            cols = ALL_FEATURES_V2
        else:
            df_feat = engineer_features_v1(df_valid)
            cols = V1_INPUT_FEATURES

        # 3. Preprocessing Transformation
        X_trans = self.preprocessor.transform(df_feat[cols])

        # 4. Model Prediction
        if isinstance(self.model, dict) and "stage1" in self.model:
            p_occ = self.model["stage1"].predict_proba(X_trans)[:, 1]
            mu_pos = np.clip(self.model["stage2"].predict(X_trans), 0, None)
            strategy = self.model.get("strategy", "Continuous")
            if "Thresholded" in strategy:
                tau = self.metadata.get("validation_metrics", {}).get("best_tau", 0.5)
                preds = np.where(p_occ >= tau, mu_pos, 0.0)
            else:
                preds = p_occ * mu_pos
        else:
            preds = self.model.predict(X_trans)

        preds = np.clip(preds, 0.0, None)  # Ensure non-negative catch

        results = []
        for i, pred_val in enumerate(preds):
            res = {
                "predicted_catch_mt": round(float(pred_val), 2),
                "unit": "Metric Tons (MT)",
                "model": self.metadata.get("model_type", "XGBoost Regressor V2"),
                "version": self.metadata.get("version", "2.0.0"),
                "input_summary": {
                    "fleet": str(df_valid.iloc[i]["Fleet"]),
                    "gear": str(df_valid.iloc[i]["Gear"]),
                    "effort": float(df_valid.iloc[i]["Effort"]),
                    "effort_units": str(df_valid.iloc[i]["EffortUnits"]),
                    "month": int(df_valid.iloc[i]["Month"]),
                    "year": int(df_valid.iloc[i]["Year"]),
                    "latitude": float(df_valid.iloc[i]["Latitude"]),
                    "longitude": float(df_valid.iloc[i]["Longitude"])
                }
            }
            results.append(res)

        return results[0] if is_single else results

    def predict_batch(self, df_or_records: Union[List[Dict[str, Any]], pd.DataFrame]) -> List[Dict[str, Any]]:
        """Batch prediction convenience wrapper."""
        res = self.predict(df_or_records)
        return [res] if isinstance(res, dict) else res


_GLOBAL_PREDICTOR_V2 = None


def predict_catch_v2(input_data: Union[Dict[str, Any], List[Dict[str, Any]], pd.DataFrame], model_dir: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Top-level functional interface for V2 fisheries catch prediction."""
    global _GLOBAL_PREDICTOR_V2
    if _GLOBAL_PREDICTOR_V2 is None or model_dir is not None:
        _GLOBAL_PREDICTOR_V2 = FisheriesCatchPredictorV2(model_dir=model_dir)
    return _GLOBAL_PREDICTOR_V2.predict(input_data)
