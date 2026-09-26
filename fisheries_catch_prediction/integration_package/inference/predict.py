"""
Inference Module for Fisheries Catch Prediction (Phase 14.3).
Provides robust single-record and batch prediction interfaces with input validation.
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Union, Any
import xgboost as xgb

from fisheries_catch_prediction.src.pipeline import (
    ALL_INPUT_FEATURES,
    engineer_features
)


REQUIRED_COLUMNS = ["Fleet", "Gear", "Effort", "EffortUnits", "Month", "Year", "Latitude", "Longitude"]


class FisheriesCatchPredictor:
    """
    Production-ready predictor for Fisheries Catch Prediction.
    Encapsulates preprocessing, feature engineering, and tuned XGBoost inference.
    """
    def __init__(self, model_dir: str = None):
        if model_dir is None:
            # Default to models/final_model relative to this file
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            model_dir = os.path.join(base_dir, "models", "final_model")

        self.model_dir = model_dir
        self.preprocessor_path = os.path.join(model_dir, "preprocessing.joblib")
        self.joblib_model_path = os.path.join(model_dir, "final_model.joblib")
        self.json_model_path = os.path.join(model_dir, "final_model.json")
        self.schema_path = os.path.join(model_dir, "feature_schema.json")
        self.metadata_path = os.path.join(model_dir, "model_metadata.json")

        self._load_artifacts()

    def _load_artifacts(self):
        """Load preprocessing pipeline, model, and metadata."""
        if not os.path.exists(self.preprocessor_path):
            raise FileNotFoundError(f"Preprocessor not found at {self.preprocessor_path}")
        self.preprocessor = joblib.load(self.preprocessor_path)

        # Load XGBoost model
        if os.path.exists(self.joblib_model_path):
            self.model = joblib.load(self.joblib_model_path)
        elif os.path.exists(self.json_model_path):
            self.model = xgb.XGBRegressor()
            self.model._estimator_type = "regressor"
            self.model.load_model(self.json_model_path)
        else:
            raise FileNotFoundError(f"Model file not found in {self.model_dir}")

        # Load metadata & schema
        self.metadata = {}
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r") as f:
                self.metadata = json.load(f)

        self.schema = {}
        if os.path.exists(self.schema_path):
            with open(self.schema_path, "r") as f:
                self.schema = json.load(f)

    def validate_inputs(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate input dataframe, check required columns and valid value ranges."""
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Input data is missing required fisheries columns: {missing}")

        df_val = df.copy()

        # Clean string columns
        df_val["Fleet"] = df_val["Fleet"].astype(str).str.strip()
        df_val["Gear"] = df_val["Gear"].astype(str).str.strip()
        df_val["EffortUnits"] = df_val["EffortUnits"].astype(str).str.strip()

        # Check numeric conversions
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
        Execute prediction on single record, list of records, or DataFrame.
        Returns prediction dictionary with continuous catch quantity in Metric Tons (MT).
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
            res = {
                "predicted_catch_mt": round(float(pred_val), 2),
                "unit": "Metric Tons (MT)",
                "model": self.metadata.get("model_type", "XGBoost Regressor (Tuned)"),
                "model_version": self.metadata.get("model_version", "1.0.0"),
                "input_summary": {
                    "fleet": str(df_valid.iloc[i]["Fleet"]),
                    "gear": str(df_valid.iloc[i]["Gear"]),
                    "effort": float(df_valid.iloc[i]["Effort"]),
                    "effort_units": str(df_valid.iloc[i]["EffortUnits"]),
                    "month": int(df_valid.iloc[i]["Month"]),
                    "year": int(df_valid.iloc[i]["Year"]),
                    "latitude": float(df_valid.iloc[i]["Latitude"]),
                    "longitude": float(df_valid.iloc[i]["Longitude"]),
                    "season": str(df_feat.iloc[i]["MonsoonSeason"])
                }
            }
            results.append(res)

        return results[0] if is_single else results

    def predict_batch(self, df_or_records: Union[List[Dict[str, Any]], pd.DataFrame]) -> List[Dict[str, Any]]:
        """Batch prediction convenience wrapper."""
        res = self.predict(df_or_records)
        return [res] if isinstance(res, dict) else res


# Global singleton instance for efficient re-use
_GLOBAL_PREDICTOR = None


def predict_catch(input_data: Union[Dict[str, Any], List[Dict[str, Any]], pd.DataFrame], model_dir: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Top-level functional interface for predicting fisheries catch."""
    global _GLOBAL_PREDICTOR
    if _GLOBAL_PREDICTOR is None or model_dir is not None:
        _GLOBAL_PREDICTOR = FisheriesCatchPredictor(model_dir=model_dir)
    return _GLOBAL_PREDICTOR.predict(input_data)
