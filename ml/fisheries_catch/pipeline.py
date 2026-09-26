"""
Inference and Feature Engineering Pipeline for Fisheries Catch Prediction (Phase 14.3 V1).
Preserves the exact V1 feature engineering:
- Monsoon season classification (NE_Monsoon, SW_Monsoon, Intermonsoons)
- Cyclic month transformation (sin/cos)
- Calendar quarter
- Log1p effort transformation (Log_Effort)
- Categorical one-hot encoding with passthrough numericals
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

CATEGORICAL_FEATURES = ["Fleet", "Gear", "EffortUnits", "MonsoonSeason"]
NUMERICAL_FEATURES = [
    "Effort",
    "Log_Effort",
    "Latitude",
    "Longitude",
    "SpatialResolution",
    "Month",
    "Month_Sin",
    "Month_Cos",
    "Quarter",
    "Year",
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
            ("num", "passthrough", NUMERICAL_FEATURES),
        ],
        remainder="drop",
    )
