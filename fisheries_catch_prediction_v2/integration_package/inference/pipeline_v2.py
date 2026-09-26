"""
Pipeline and Preprocessing module for Fisheries Catch Prediction V2.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

from fisheries_catch_prediction_v2.src.features_v2 import (
    ALL_CATEGORICAL_V2,
    NUMERICAL_V2,
    ALL_FEATURES_V2,
    engineer_features_v2
)


def build_preprocessor_v2() -> ColumnTransformer:
    """
    Build scikit-learn ColumnTransformer for V2 features.
    Encodes base + interaction categoricals with OneHotEncoder(handle_unknown='ignore').
    Passes through numerical features.
    """
    return ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ALL_CATEGORICAL_V2),
            ("num", "passthrough", NUMERICAL_V2)
        ],
        remainder="drop"
    )


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
