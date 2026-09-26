"""
Feature engineering module for Fisheries Catch Prediction V2.
Extracts rich temporal, spatial, sub-basin, and categorical interaction features.
"""
import numpy as np
import pandas as pd


CATEGORICAL_BASE = ["Fleet", "Gear", "EffortUnits", "MonsoonSeason", "Region", "Macro_Grid_5deg"]
INTERACTION_FEATURES = [
    "Fleet_x_Gear",
    "Gear_x_Season",
    "Fleet_x_Season",
    "Location_x_Season",
    "Fleet_x_EffortUnit",
    "Gear_x_EffortUnit"
]
ALL_CATEGORICAL_V2 = CATEGORICAL_BASE + INTERACTION_FEATURES

NUMERICAL_V2 = [
    "Effort",
    "Log_Effort",
    "Latitude",
    "Longitude",
    "Abs_Latitude",
    "SpatialResolution",
    "Month",
    "Month_Sin",
    "Month_Cos",
    "Quarter",
    "Year",
    "Year_Scaled"
]
ALL_FEATURES_V2 = ALL_CATEGORICAL_V2 + NUMERICAL_V2


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


def assign_region(lat: float, lon: float) -> str:
    """
    Classify geographic marine basin / sub-region:
    - Arabian Sea (lat >= 5.0, lon 50-78)
    - Bay of Bengal (lat >= 5.0, lon 78-100)
    - Western Equatorial (Somali Basin, Seychelles, Kenya/Tanzania)
    - Eastern Equatorial (Maldives, Chagos, Indonesia, Eastern IO)
    - Mozambique Channel (lat < -10.0, lon 30-50)
    - Southern Indian Ocean (lat < -10.0, lon > 50)
    - Other Oceanic
    """
    if lat >= 5.0 and 50.0 <= lon <= 78.0:
        return "Arabian_Sea"
    elif lat >= 5.0 and 78.0 < lon <= 100.0:
        return "Bay_of_Bengal"
    elif -10.0 <= lat < 5.0 and 40.0 <= lon <= 80.0:
        return "Western_Equatorial"
    elif -10.0 <= lat < 5.0 and lon > 80.0:
        return "Eastern_Equatorial"
    elif lat < -10.0 and 30.0 <= lon <= 50.0:
        return "Mozambique_Channel"
    elif lat < -10.0 and lon > 50.0:
        return "Southern_Indian_Ocean"
    else:
        return "Other_Oceanic"


def engineer_features_v2(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate all V2 feature sets including:
    - Rich temporal features (Month_Sin, Month_Cos, Quarter, Year_Scaled, MonsoonSeason)
    - Spatial & sub-basin features (Abs_Latitude, Region, Macro_Grid_5deg)
    - Interaction features (Fleet x Gear, Gear x Season, Fleet x Season, Location x Season, Fleet x EffortUnit)
    - Log effort scaling
    """
    df_out = df.copy()

    # Ensure string types and clean whitespaces
    for col in ["Fleet", "Gear", "EffortUnits"]:
        if col in df_out.columns:
            df_out[col] = df_out[col].astype(str).str.strip()

    # Numeric guarantees
    for col in ["Effort", "Latitude", "Longitude", "Month", "Year"]:
        if col in df_out.columns:
            df_out[col] = pd.to_numeric(df_out[col], errors="coerce")

    # Temporal features
    m = df_out["Month"].astype(int)
    y = df_out["Year"].astype(int)
    df_out["Month_Sin"] = np.sin(2.0 * np.pi * m / 12.0)
    df_out["Month_Cos"] = np.cos(2.0 * np.pi * m / 12.0)
    df_out["Quarter"] = (m - 1) // 3 + 1
    df_out["MonsoonSeason"] = m.apply(assign_monsoon)
    df_out["Year_Scaled"] = (y - 1970.0) / 52.0

    # Spatial features
    lat = df_out["Latitude"].astype(float)
    lon = df_out["Longitude"].astype(float)
    df_out["Abs_Latitude"] = np.abs(lat)
    if "SpatialResolution" not in df_out.columns:
        df_out["SpatialResolution"] = 1.0

    # Region assignment
    df_out["Region"] = [assign_region(lt, ln) for lt, ln in zip(lat, lon)]

    # Macro grid cell (5-degree spatial block)
    df_out["Macro_Grid_5deg"] = [
        f"G5_{int(np.floor(lt / 5.0) * 5)}_{int(np.floor(ln / 5.0) * 5)}"
        for lt, ln in zip(lat, lon)
    ]

    # Effort transformation
    eff = np.maximum(df_out["Effort"].astype(float), 0.0)
    df_out["Log_Effort"] = np.log1p(eff)

    # Explicit Interaction Features
    df_out["Fleet_x_Gear"] = df_out["Fleet"] + "_" + df_out["Gear"]
    df_out["Gear_x_Season"] = df_out["Gear"] + "_" + df_out["MonsoonSeason"]
    df_out["Fleet_x_Season"] = df_out["Fleet"] + "_" + df_out["MonsoonSeason"]
    df_out["Location_x_Season"] = df_out["Region"] + "_" + df_out["MonsoonSeason"]
    df_out["Fleet_x_EffortUnit"] = df_out["Fleet"] + "_" + df_out["EffortUnits"]
    df_out["Gear_x_EffortUnit"] = df_out["Gear"] + "_" + df_out["EffortUnits"]

    return df_out
