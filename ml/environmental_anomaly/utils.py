"""
Utility helpers for Environmental Anomaly Detection.

Includes synthetic dataset generators for development validation and diagnostic visualization generators.
"""

from datetime import datetime, timedelta
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from .config import RESULTS_DIR

logger = logging.getLogger(__name__)


def generate_synthetic_environmental_netcdf(
    output_path: Union[str, Path],
    num_days: int = 60,
    num_lats: int = 20,
    num_lons: int = 25,
    min_lat: float = 8.0,
    max_lat: float = 22.0,
    min_lon: float = 68.0,
    max_lon: float = 78.0,
    inject_anomaly: bool = True,
) -> Path:
    """
    Generates a small, realistic synthetic NetCDF4/HDF5 dataset using h5py.
    Used STRICTLY for development pipeline validation when the real complete dataset is unavailable.

    Schema matches GHRSST / NOAA OISST conventions:
    - time (days)
    - lat, lon
    - analysed_sst (Kelvin, scaled int16, standard scale=0.01, offset=273.15)
    - analysis_error (scaled int16)
    - sea_ice_fraction (scaled int16)
    - mask (int8, 1=sea, 2=land)
    """
    import h5py

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lats = np.linspace(min_lat, max_lat, num_lats, dtype=np.float32)
    lons = np.linspace(min_lon, max_lon, num_lons, dtype=np.float32)
    times = np.arange(num_days, dtype=np.float32)  # days since 2025-01-01

    scale_factor = 0.01
    add_offset = 273.15
    fill_value = -32768

    # Generate synthetic SST (Celsius: 26 to 31 C with seasonal warming and spatial gradient)
    # T(t, lat, lon) = 28.0 - 0.2*(lat - 15) + 2.0*sin(2*pi*t/365) + noise
    sst_array = np.zeros((num_days, num_lats, num_lons), dtype=np.int16)
    err_array = np.zeros((num_days, num_lats, num_lons), dtype=np.int16)
    ice_array = np.zeros((num_days, num_lats, num_lons), dtype=np.int16)
    mask_array = np.ones((num_days, num_lats, num_lons), dtype=np.int8)  # 1 = sea

    # Add land mask in upper right (simulating Indian peninsula coastline)
    for ilat in range(num_lats):
        for ilon in range(num_lons):
            if lats[ilat] > 18.0 and lons[ilon] > 74.0:
                mask_array[:, ilat, ilon] = 2  # land

    np.random.seed(42)
    for t in range(num_days):
        t_season = 2.0 * np.sin(2 * np.pi * t / 365.0)
        for ilat in range(num_lats):
            lat_val = lats[ilat]
            base_temp = 28.5 - 0.25 * (lat_val - 12.0) + t_season
            for ilon in range(num_lons):
                if mask_array[t, ilat, ilon] == 2:
                    sst_array[t, ilat, ilon] = fill_value
                    err_array[t, ilat, ilon] = fill_value
                    continue

                noise = np.random.normal(0, 0.3)
                celsius = base_temp + noise

                # Inject severe Marine Heatwave anomaly at t >= 45 in central sector
                if inject_anomaly and t >= 45 and 12.0 <= lat_val <= 16.0 and 70.0 <= lons[ilon] <= 73.0:
                    celsius += 3.2  # +3.2°C thermal heatwave anomaly!

                kelvin = celsius + add_offset
                packed = int(round((kelvin - add_offset) / scale_factor))
                sst_array[t, ilat, ilon] = np.clip(packed, -30000, 30000)
                err_array[t, ilat, ilon] = int(round(0.25 / scale_factor))

    with h5py.File(str(path), "w") as f:
        # Latitude
        ds_lat = f.create_dataset("lat", data=lats)
        ds_lat.attrs["units"] = "degrees_north"
        ds_lat.attrs["standard_name"] = "latitude"

        # Longitude
        ds_lon = f.create_dataset("lon", data=lons)
        ds_lon.attrs["units"] = "degrees_east"
        ds_lon.attrs["standard_name"] = "longitude"

        # Time
        ds_time = f.create_dataset("time", data=times)
        ds_time.attrs["units"] = "days since 2025-01-01 00:00:00"
        ds_time.attrs["standard_name"] = "time"

        # Analysed SST
        ds_sst = f.create_dataset("analysed_sst", data=sst_array)
        ds_sst.attrs["units"] = "kelvin"
        ds_sst.attrs["scale_factor"] = scale_factor
        ds_sst.attrs["add_offset"] = add_offset
        ds_sst.attrs["_FillValue"] = fill_value

        # Analysis Error
        ds_err = f.create_dataset("analysis_error", data=err_array)
        ds_err.attrs["units"] = "kelvin"
        ds_err.attrs["scale_factor"] = scale_factor
        ds_err.attrs["add_offset"] = 0.0
        ds_err.attrs["_FillValue"] = fill_value

        # Sea Ice Fraction
        ds_ice = f.create_dataset("sea_ice_fraction", data=ice_array)
        ds_ice.attrs["units"] = "1"
        ds_ice.attrs["_FillValue"] = fill_value

        # Mask
        ds_mask = f.create_dataset("mask", data=mask_array)
        ds_mask.attrs["comment"] = "1=sea, 2=land"

    logger.info(f"Synthetic development NetCDF dataset successfully created at: {path}")
    return path


def generate_synthetic_environmental_df(
    num_samples: int = 1000,
    inject_anomaly_pct: float = 0.05,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Generates a synthetic DataFrame representing daily environmental observations.
    Used for unit testing and development pipeline verification.
    """
    np.random.seed(random_state)
    start_date = datetime(2025, 1, 1)

    records = []
    num_anomalies = int(num_samples * inject_anomaly_pct)

    for i in range(num_samples):
        day_offset = int(np.random.randint(0, 365))
        dt = start_date + timedelta(days=day_offset)
        lat = round(float(np.random.uniform(8.0, 22.0)), 4)
        lon = round(float(np.random.uniform(68.0, 78.0)), 4)

        # Baseline expected seasonal SST
        t_season = 2.0 * math.sin(2 * math.pi * dt.timetuple().tm_yday / 365.25)
        base_sst = 28.5 - 0.25 * (lat - 12.0) + t_season
        noise = np.random.normal(0, 0.35)
        sst = round(base_sst + noise, 3)

        # Inject extreme MHW or cold anomaly in a subset
        if i < num_anomalies:
            is_hot = (i % 2 == 0)
            sst = round(sst + (3.5 if is_hot else -3.2), 3)

        records.append({
            "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "month": dt.month,
            "day_of_year": dt.timetuple().tm_yday,
            "latitude": lat,
            "longitude": lon,
            "analysed_sst": sst,
            "analysis_error": round(float(np.random.uniform(0.15, 0.45)), 3),
            "sea_ice_fraction": 0.0,
            "mask": 1,
        })

    return pd.DataFrame(records)


def generate_diagnostic_plots(
    df: pd.DataFrame,
    output_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, str]:
    """
    Generates diagnostic visual plots for the anomaly detection report.
    Returns dictionary mapping plot names to saved filepaths.
    """
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt

    target_dir = Path(output_dir or RESULTS_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)
    generated_plots = {}

    plot_df = df
    if len(df) > 100000:
        is_anom = df["anomaly_label"] == -1
        anom_sub = df[is_anom]
        norm_sub = df[~is_anom].sample(min(50000, int((~is_anom).sum())), random_state=42)
        plot_df = pd.concat([norm_sub, anom_sub]).sample(frac=1.0, random_state=42).reset_index(drop=True)

    anom_mask = plot_df["anomaly_label"] == -1

    # 1. SST Anomaly Distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(plot_df.loc[~anom_mask, "sst_anomaly"], bins=40, alpha=0.7, color="#0284c7", label="Normal Conditions")
    if anom_mask.sum() > 0:
        ax.hist(plot_df.loc[anom_mask, "sst_anomaly"], bins=30, alpha=0.85, color="#ef4444", label="Flagged Anomalies")
    ax.set_title("SST Anomaly Distribution (°C)", fontsize=13, fontweight="bold")
    ax.set_xlabel("SST Anomaly (°C)")
    ax.set_ylabel("Observation Count")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()
    p1 = target_dir / "sst_anomaly_distribution.png"
    plt.tight_layout()
    plt.savefig(p1, dpi=150)
    plt.close(fig)
    generated_plots["sst_anomaly_distribution"] = str(p1)

    # 2. Anomaly Score Distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(plot_df["anomaly_score"], bins=40, color="#6366f1", edgecolor="black", alpha=0.8)
    ax.axvline(60.0, color="#f59e0b", linestyle="--", label="Moderate (60)")
    ax.axvline(75.0, color="#f97316", linestyle="--", label="High (75)")
    ax.axvline(85.0, color="#ef4444", linestyle="--", label="Critical (85)")
    ax.set_title("Normalized Anomaly Score Distribution (0-100)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Anomaly Score (Higher = More Anomalous)")
    ax.set_ylabel("Count")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()
    p2 = target_dir / "anomaly_score_distribution.png"
    plt.tight_layout()
    plt.savefig(p2, dpi=150)
    plt.close(fig)
    generated_plots["anomaly_score_distribution"] = str(p2)

    # 3. Spatial Anomaly Scatter Plot
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(plot_df.loc[~anom_mask, "longitude"], plot_df.loc[~anom_mask, "latitude"], c="#94a3b8", s=10, alpha=0.4, label="Normal")
    if anom_mask.sum() > 0:
        sc = ax.scatter(
            plot_df.loc[anom_mask, "longitude"],
            plot_df.loc[anom_mask, "latitude"],
            c=plot_df.loc[anom_mask, "anomaly_score"],
            cmap="YlOrRd",
            s=40,
            edgecolor="black",
            linewidth=0.5,
            label="Anomalies",
        )
        cbar = plt.colorbar(sc, ax=ax)
        cbar.set_label("Anomaly Score")
    ax.set_title("Spatial Distribution of Marine Observations & Anomalies", fontsize=13, fontweight="bold")
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left")
    p3 = target_dir / "spatial_anomaly_map.png"
    plt.tight_layout()
    plt.savefig(p3, dpi=150)
    plt.close(fig)
    generated_plots["spatial_anomaly_map"] = str(p3)

    logger.info(f"Diagnostic plots saved to {target_dir}")
    return generated_plots
