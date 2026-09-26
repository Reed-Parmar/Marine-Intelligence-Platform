"""
Inference and Preprocessing Pipeline for Fisheries Catch Prediction.
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder


CATEGORICAL_FEATURES = ["Fleet", "Gear", "EffortUnits", "MonsoonSeason"]
NUMERICAL_FEATURES = [
    "Effort", "Log_Effort", "Latitude", "Longitude",
    "SpatialResolution", "Month", "Month_Sin", "Month_Cos", "Quarter", "Year"
]
ALL_INPUT_FEATURES = CATEGORICAL_FEATURES + NUMERICAL_FEATURES


def assign_monsoon(month: int) -> str:
    """Classify Indian Ocean / Arabian Sea monsoon season from month."""
    if month in [12, 1, 2]:
        return "NE_Monsoon"
    elif month in [3, 4, 5]:
        return "Intermonsoon_Spring"
    elif month in [6, 7, 8, 9]:
        return "SW_Monsoon"
    else:
        return "Intermonsoon_Autumn"


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive engineered features from raw input columns:
    Month_Sin, Month_Cos, Quarter, MonsoonSeason, Log_Effort.
    """
    df_out = df.copy()
    if "Month" in df_out.columns:
        m = df_out["Month"].astype(int)
        df_out["Month_Sin"] = np.sin(2 * np.pi * m / 12.0)
        df_out["Month_Cos"] = np.cos(2 * np.pi * m / 12.0)
        df_out["Quarter"] = (m - 1) // 3 + 1
        df_out["MonsoonSeason"] = m.apply(assign_monsoon)
    
    if "Effort" in df_out.columns:
        df_out["Log_Effort"] = np.log1p(np.maximum(df_out["Effort"].astype(float), 0.0))

    if "SpatialResolution" not in df_out.columns:
        df_out["SpatialResolution"] = 1.0

    return df_out


def build_preprocessor() -> ColumnTransformer:
    """Build scikit-learn ColumnTransformer for categorical and numerical features."""
    return ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
            ("num", "passthrough", NUMERICAL_FEATURES)
        ],
        remainder="drop"
    )


class BaselineCatchRegressor(BaseEstimator, RegressorMixin):
    """Simple baseline predictor using empirical mean and median catch."""
    def __init__(self, strategy: str = "mean"):
        self.strategy = strategy
        self.prediction_value_ = 0.0

    def fit(self, X, y):
        if self.strategy == "median":
            self.prediction_value_ = float(np.median(y))
        else:
            self.prediction_value_ = float(np.mean(y))
        return self

    def predict(self, X):
        n_samples = len(X) if hasattr(X, "__len__") else X.shape[0]
        return np.full(n_samples, self.prediction_value_, dtype=np.float64)


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    Calculate comprehensive regression metrics:
    MAE, RMSE, R2, Median Absolute Error, sMAPE (zero-safe), Bias, Under/Over %.
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    y_pred = np.clip(y_pred, 0.0, None)  # Catch cannot be negative

    errors = y_pred - y_true
    abs_errors = np.abs(errors)
    sq_errors = errors ** 2

    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(sq_errors)))
    medae = float(np.median(abs_errors))

    # R-squared
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    ss_res = np.sum(sq_errors)
    r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

    # Zero-safe symmetric MAPE (sMAPE): bounded between 0% and 200%
    denom = np.abs(y_true) + np.abs(y_pred) + 1e-8
    smape = float(np.mean(200.0 * abs_errors / denom))

    # Bias and over/under prediction
    bias = float(np.mean(errors))
    mean_true = float(np.mean(y_true))
    mean_pred = float(np.mean(y_pred))
    under_pct = float(np.mean(errors < 0) * 100.0)
    over_pct = float(np.mean(errors > 0) * 100.0)
    exact_pct = float(np.mean(errors == 0) * 100.0)

    return {
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2,
        "MedAE": medae,
        "sMAPE": smape,
        "Bias": bias,
        "Mean_Actual": mean_true,
        "Mean_Predicted": mean_pred,
        "Underprediction_Pct": under_pct,
        "Overprediction_Pct": over_pct,
        "Exact_Pct": exact_pct
    }
