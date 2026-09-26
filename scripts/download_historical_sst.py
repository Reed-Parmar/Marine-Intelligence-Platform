"""
Automated Downloader & Validator for 8-Year Historical SST (Copernicus Marine).

Downloads:
- 2018 through 2025 (8 annual NetCDF files)
- Region: 5°N to 25°N, 50°E to 78°E
- Variable: surface thetao only (depth = 0.494 m)
- Destination: historical_sst/surface_thetao_<YYYY>.nc
- Generates: historical_sst/manifest.json
"""

import datetime
import hashlib
import json
import logging
from pathlib import Path
import sys
import time

import copernicusmarine
import numpy as np
import xarray as xr

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DownloadHistoricalSST")

DATASET_ID = "cmems_mod_glo_phy_my_0.083deg_P1D-m"
OUTPUT_DIR = Path("historical_sst")
YEARS = list(range(2018, 2026))

EXPECTED_DAYS = {
    2018: 365,
    2019: 365,
    2020: 366,  # Leap year
    2021: 365,
    2022: 365,
    2023: 365,
    2024: 366,  # Leap year
    2025: 365,
}

def compute_sha256(filepath: Path) -> str:
    """Computes SHA256 checksum of a file in streaming chunks."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def verify_annual_file(filepath: Path, expected_year: int) -> dict:
    """Rigorous integrity verification of an annual NetCDF file."""
    assert filepath.exists(), f"File does not exist: {filepath}"
    file_size_bytes = filepath.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)

    # Open with xarray
    with xr.open_dataset(filepath) as ds:
        dims = {k: int(v) for k, v in ds.sizes.items()}
        data_vars = list(ds.data_vars.keys())
        coords = list(ds.coords.keys())

        # Check variable
        assert "thetao" in data_vars, f"'thetao' variable missing in {filepath}"
        
        # Check depth
        assert "depth" in ds.coords, f"'depth' coord missing in {filepath}"
        depth_vals = ds.coords["depth"].values
        assert len(depth_vals) == 1, f"Expected 1 depth level, got {len(depth_vals)}"
        assert 0.48 <= depth_vals[0] <= 0.52, f"Expected surface depth ~0.494m, got {depth_vals[0]}"

        # Check coordinates
        lat_vals = ds.coords["latitude"].values
        lon_vals = ds.coords["longitude"].values
        time_vals = ds.coords["time"].values

        assert len(lat_vals) == 241, f"Expected 241 latitude points, got {len(lat_vals)}"
        assert len(lon_vals) == 337, f"Expected 337 longitude points, got {len(lon_vals)}"
        assert np.isclose(lat_vals.min(), 5.0, atol=0.01), f"Unexpected min lat: {lat_vals.min()}"
        assert np.isclose(lat_vals.max(), 25.0, atol=0.01), f"Unexpected max lat: {lat_vals.max()}"
        assert np.isclose(lon_vals.min(), 50.0, atol=0.01), f"Unexpected min lon: {lon_vals.min()}"
        assert np.isclose(lon_vals.max(), 78.0, atol=0.01), f"Unexpected max lon: {lon_vals.max()}"

        # Check time
        expected_steps = EXPECTED_DAYS[expected_year]
        actual_steps = len(time_vals)
        assert actual_steps == expected_steps, (
            f"Year {expected_year}: Expected {expected_steps} days, got {actual_steps}"
        )

        time_start = str(time_vals[0])[:19]
        time_end = str(time_vals[-1])[:19]
        assert str(expected_year) in time_start, f"Start time {time_start} doesn't match {expected_year}"
        assert str(expected_year) in time_end, f"End time {time_end} doesn't match {expected_year}"

        # Check physical bounds on a slice
        sample_slice = ds["thetao"].isel(time=0).values
        valid_mask = ~np.isnan(sample_slice)
        valid_count = int(np.sum(valid_mask))
        valid_vals = sample_slice[valid_mask]

        min_sst = float(valid_vals.min())
        max_sst = float(valid_vals.max())
        mean_sst = float(valid_vals.mean())
        assert 12.0 <= min_sst <= 32.0, f"Unphysical min SST: {min_sst}"
        assert 22.0 <= max_sst <= 38.0, f"Unphysical max SST: {max_sst}"

    checksum = compute_sha256(filepath)

    meta = {
        "year": expected_year,
        "filename": filepath.name,
        "filepath": str(filepath.resolve()),
        "time_start": time_start,
        "time_end": time_end,
        "num_time_steps": actual_steps,
        "spatial_dimensions": {
            "latitude": len(lat_vals),
            "longitude": len(lon_vals),
            "lat_min": float(lat_vals.min()),
            "lat_max": float(lat_vals.max()),
            "lon_min": float(lon_vals.min()),
            "lon_max": float(lon_vals.max()),
        },
        "depth": float(depth_vals[0]),
        "variable": "thetao",
        "dtype": str(sample_slice.dtype),
        "valid_ocean_cells_day1": valid_count,
        "sst_day1_summary": {
            "min_celsius": round(min_sst, 3),
            "max_celsius": round(max_sst, 3),
            "mean_celsius": round(mean_sst, 3),
        },
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(file_size_mb, 2),
        "sha256": checksum,
        "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "integrity_status": "PASSED",
    }
    return meta

def download_and_verify_all():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_records = []
    
    print("\n" + "=" * 80)
    print("COPERNICUS MARINE 8-YEAR (2018-2025) HISTORICAL SST ACQUISITION")
    print("=" * 80)
    print(f"Target Directory: {OUTPUT_DIR.resolve()}")
    print(f"Years to fetch  : {YEARS}")
    print(f"Region          : Lat [5.0°N, 25.0°N], Lon [50.0°E, 78.0°E]")
    print(f"Variable        : surface thetao only (depth = 0.494 m)")
    print("-" * 80)

    t_start = time.time()

    for year in YEARS:
        filename = f"surface_thetao_{year}.nc"
        target_path = OUTPUT_DIR / filename
        expected_steps = EXPECTED_DAYS[year]

        # Check if already downloaded and valid
        if target_path.exists():
            logger.info(f"Checking existing file for {year}: {target_path}...")
            try:
                meta = verify_annual_file(target_path, year)
                logger.info(f"Year {year} already downloaded and verified ({meta['file_size_mb']} MB, {meta['num_time_steps']} steps).")
                manifest_records.append(meta)
                continue
            except Exception as e:
                logger.warning(f"Existing file {target_path} failed verification: {e}. Re-downloading...")
                target_path.unlink(missing_ok=True)

        logger.info(f"Downloading Year {year} ({expected_steps} days)...")
        start_dt = f"{year}-01-01T00:00:00"
        end_dt = f"{year}-12-31T23:59:59"
        
        t0 = time.time()
        max_retries = 3
        success = False

        for attempt in range(1, max_retries + 1):
            try:
                copernicusmarine.subset(
                    dataset_id=DATASET_ID,
                    variables=["thetao"],
                    minimum_longitude=50.0,
                    maximum_longitude=78.0,
                    minimum_latitude=5.0,
                    maximum_latitude=25.0,
                    minimum_depth=0.49,
                    maximum_depth=0.50,
                    start_datetime=start_dt,
                    end_datetime=end_dt,
                    output_filename=filename,
                    output_directory=OUTPUT_DIR,
                    overwrite=True,
                    netcdf_compression_level=4,
                    disable_progress_bar=True,
                )
                dt_dl = time.time() - t0
                logger.info(f"Year {year} downloaded successfully in {dt_dl:.2f}s.")
                success = True
                break
            except Exception as err:
                logger.error(f"Attempt {attempt}/{max_retries} failed for Year {year}: {err}")
                if attempt < max_retries:
                    time.sleep(5)
                else:
                    raise RuntimeError(f"Failed to download {year} after {max_retries} attempts: {err}")

        # Verify file immediately
        meta = verify_annual_file(target_path, year)
        logger.info(
            f"Verified {year}: {meta['file_size_mb']} MB, "
            f"steps: {meta['num_time_steps']}, "
            f"SST day 1: [{meta['sst_day1_summary']['min_celsius']} - {meta['sst_day1_summary']['max_celsius']}] °C, "
            f"SHA256: {meta['sha256'][:12]}..."
        )
        manifest_records.append(meta)

    total_time = time.time() - t_start
    total_mb = sum(r["file_size_mb"] for r in manifest_records)
    total_steps = sum(r["num_time_steps"] for r in manifest_records)

    # Save manifest
    manifest_data = {
        "manifest_version": "1.0",
        "dataset_name": "8-Year Surface SST Reanalysis (Arabian Sea)",
        "source_product": "GLOBAL_MULTIYEAR_PHY_001_030",
        "source_dataset": DATASET_ID,
        "temporal_range": {
            "start": manifest_records[0]["time_start"],
            "end": manifest_records[-1]["time_end"],
            "total_years": len(manifest_records),
            "total_time_steps": total_steps,
        },
        "spatial_coverage": {
            "latitude_min": 5.0,
            "latitude_max": 25.0,
            "longitude_min": 50.0,
            "longitude_max": 78.0,
            "depth_m": 0.494025,
            "resolution_deg": 0.083333,
        },
        "study_region_mask": "Strict IHO S-23 Arabian Sea to be applied by ML pipeline",
        "total_storage_mb": round(total_mb, 2),
        "acquisition_duration_seconds": round(total_time, 2),
        "files": manifest_records,
    }

    manifest_path = OUTPUT_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    print("\n" + "=" * 80)
    print("ACQUISITION & INTEGRITY AUDIT COMPLETE")
    print("=" * 80)
    print(f"Annual Files Downloaded : {len(manifest_records)} / {len(YEARS)}")
    print(f"Total Time Steps        : {total_steps} days (2018-01-01 to 2025-12-31)")
    print(f"Total Disk Size         : {total_mb:.2f} MB")
    print(f"Total Duration          : {total_time:.2f} seconds ({total_time/60:.2f} min)")
    print(f"Manifest Saved To       : {manifest_path.resolve()}")
    print("=" * 80 + "\n")

    return True

if __name__ == "__main__":
    download_and_verify_all()
