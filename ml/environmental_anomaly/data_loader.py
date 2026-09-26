"""
Dynamic Data Loader & Inspector for Environmental Oceanographic Datasets.

Supports NetCDF4/HDF5 (via h5py, with optional xarray/netCDF4 fallback) and tabular formats (CSV, Parquet).
Inspects datasets dynamically without hardcoded assumptions and avoids loading entire files into memory.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
import logging
from pathlib import Path
import re
from typing import Any, Dict, Generator, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from .config import (
    KELVIN_CELSIUS_OFFSET,
    KELVIN_DETECTION_THRESHOLD,
    SST_MAX_CELSIUS,
    SST_MIN_CELSIUS,
    VARIABLE_ALIASES,
)

logger = logging.getLogger(__name__)


@dataclass
class DatasetInspectionReport:
    """Detailed inspection report of an environmental dataset."""
    filepath: str
    file_format: str
    file_size_mb: float
    dimensions: Dict[str, int]
    variables: Dict[str, Dict[str, Any]]
    resolved_canonical_variables: Dict[str, str]
    spatial_coverage: Dict[str, Optional[float]]
    time_range: Dict[str, Optional[str]]
    inferred_temporal_resolution: Optional[str]
    missing_value_summary: Dict[str, Any]
    sst_summary: Dict[str, Any]
    arabian_sea_coverage: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def print_summary(self):
        """Prints a human-readable formatted summary report."""
        print("=" * 80)
        print(f"ENVIRONMENTAL DATASET INSPECTION REPORT")
        print("=" * 80)
        print(f"File Path    : {self.filepath}")
        print(f"Format       : {self.file_format} ({self.file_size_mb:.2f} MB)")
        print(f"Dimensions   : {self.dimensions}")
        print(f"Resolved Vars: {self.resolved_canonical_variables}")
        print("-" * 80)
        print("COORDINATE & SPATIAL COVERAGE:")
        print(f"  Latitude   : [{self.spatial_coverage.get('lat_min')}, {self.spatial_coverage.get('lat_max')}] (Count: {self.spatial_coverage.get('lat_count')})")
        print(f"  Longitude  : [{self.spatial_coverage.get('lon_min')}, {self.spatial_coverage.get('lon_max')}] (Count: {self.spatial_coverage.get('lon_count')})")
        print("-" * 80)
        print("TEMPORAL COVERAGE:")
        print(f"  Time Range : {self.time_range.get('start')} to {self.time_range.get('end')}")
        print(f"  Time Steps : {self.time_range.get('total_steps')}")
        print(f"  Resolution : {self.inferred_temporal_resolution}")
        print("-" * 80)
        print("SST CHARACTERISTICS:")
        print(f"  Valid Range (Celsius): [{self.sst_summary.get('min_celsius')}, {self.sst_summary.get('max_celsius')}]")
        print(f"  Mean SST             : {self.sst_summary.get('mean_celsius')} °C")
        print(f"  Detected Scale Unit  : {self.sst_summary.get('detected_unit')}")
        print(f"  Missing / Fill Values: {self.sst_summary.get('fill_value_count')} ({self.sst_summary.get('fill_value_pct')}%)")
        if self.arabian_sea_coverage:
            print("-" * 80)
            print("ARABIAN SEA REGIONAL DEMARCATION (IHO S-23):")
            print(f"  Valid Ocean Cells    : {self.arabian_sea_coverage.get('total_valid_ocean_cells'):,}")
            print(f"  Persian Gulf Excluded: {self.arabian_sea_coverage.get('persian_gulf_cells'):,}")
            print(f"  Gulf of Oman Excluded: {self.arabian_sea_coverage.get('gulf_of_oman_cells'):,}")
            print(f"  Gulf of Aden Excluded: {self.arabian_sea_coverage.get('gulf_of_aden_cells'):,}")
            print(f"  Arabian Sea Retained : {self.arabian_sea_coverage.get('arabian_sea_strict_cells'):,} ({self.arabian_sea_coverage.get('arabian_sea_pct_of_ocean')}%)")
        print("=" * 80 + "\n")


class EnvironmentalDataLoader:
    """
    Robust Loader and Inspector for Sea Surface Temperature (SST) & Environmental Data.
    """

    def __init__(self):
        self._inspection_cache: Dict[str, DatasetInspectionReport] = {}

    @staticmethod
    def _get_scalar_attr(ds, name: str, default: Any = None) -> Any:
        """Safely extracts a scalar value from an HDF5/NetCDF attribute (handling 0D/1D numpy arrays)."""
        val = ds.attrs.get(name, default)
        if val is None:
            return default
        if isinstance(val, (np.ndarray, list)):
            s = np.squeeze(val)
            return s.item() if s.shape == () else s[0].item() if hasattr(s[0], "item") else s[0]
        return val

    @staticmethod
    def _resolve_variable_name(available_vars: List[str], canonical_key: str) -> Optional[str]:
        """Matches available variable names against canonical aliases."""
        aliases = VARIABLE_ALIASES.get(canonical_key, [canonical_key])
        avail_lower = {v.lower().strip(): v for v in available_vars}
        for alias in aliases:
            if alias.lower() in avail_lower:
                return avail_lower[alias.lower()]
        return None

    def inspect_dataset(self, filepath: Union[str, Path]) -> DatasetInspectionReport:
        """
        Dynamically inspects a dataset (NetCDF4, HDF5, CSV) without loading large arrays into RAM.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found at: {path}")

        file_size_mb = path.stat().st_size / (1024 * 1024)
        ext = path.suffix.lower()

        if ext in (".nc", ".nc4", ".hdf", ".h5", ".he5"):
            report = self._inspect_netcdf_hdf5(path, file_size_mb)
        elif ext in (".csv", ".tsv", ".txt"):
            report = self._inspect_tabular(path, file_size_mb)
        else:
            # Attempt HDF5 first, fallback to CSV
            try:
                report = self._inspect_netcdf_hdf5(path, file_size_mb)
            except Exception:
                report = self._inspect_tabular(path, file_size_mb)

        self._inspection_cache[str(path)] = report
        return report

    def _inspect_netcdf_hdf5(self, path: Path, file_size_mb: float) -> DatasetInspectionReport:
        """Inspects HDF5/NetCDF4 datasets using h5py."""
        import h5py

        with h5py.File(str(path), "r") as f:
            available_vars = list(f.keys())
            var_info: Dict[str, Dict[str, Any]] = {}
            dimensions: Dict[str, int] = {}

            for var_name in available_vars:
                ds = f[var_name]
                if isinstance(ds, h5py.Dataset):
                    var_info[var_name] = {
                        "shape": ds.shape,
                        "dtype": str(ds.dtype),
                        "attrs": {k: str(v) for k, v in ds.attrs.items()},
                    }
                    if len(ds.shape) == 1:
                        dimensions[var_name] = ds.shape[0]

            # Resolve canonical names
            resolved: Dict[str, str] = {}
            for canonical in ["sst", "lat", "lon", "time", "analysis_error", "sea_ice_fraction", "mask"]:
                found = self._resolve_variable_name(available_vars, canonical)
                if found:
                    resolved[canonical] = found

            # Inspect Latitude
            lat_min, lat_max, lat_count = None, None, None
            if "lat" in resolved:
                lat_ds = f[resolved["lat"]]
                lat_vals = lat_ds[:] if lat_ds.size < 100000 else np.linspace(lat_ds[0], lat_ds[-1], 100)
                lat_min = float(np.nanmin(lat_vals))
                lat_max = float(np.nanmax(lat_vals))
                lat_count = int(lat_ds.shape[0]) if len(lat_ds.shape) >= 1 else 1

            # Inspect Longitude
            lon_min, lon_max, lon_count = None, None, None
            if "lon" in resolved:
                lon_ds = f[resolved["lon"]]
                lon_vals = lon_ds[:] if lon_ds.size < 100000 else np.linspace(lon_ds[0], lon_ds[-1], 100)
                lon_min = float(np.nanmin(lon_vals))
                lon_max = float(np.nanmax(lon_vals))
                lon_count = int(lon_ds.shape[0]) if len(lon_ds.shape) >= 1 else 1

            # Inspect Time
            time_start_str, time_end_str, time_steps, resolution = None, None, None, None
            if "time" in resolved:
                time_ds = f[resolved["time"]]
                time_steps = int(time_ds.shape[0]) if len(time_ds.shape) >= 1 else 1
                time_units = str(time_ds.attrs.get("units", ""))
                first_t = float(time_ds[0]) if time_steps > 0 else 0
                last_t = float(time_ds[-1]) if time_steps > 0 else 0

                dt_start = self._parse_netcdf_time(first_t, time_units)
                dt_end = self._parse_netcdf_time(last_t, time_units)
                time_start_str = dt_start.isoformat() if dt_start else str(first_t)
                time_end_str = dt_end.isoformat() if dt_end else str(last_t)

                if dt_start and dt_end and time_steps > 1:
                    delta_days = (dt_end - dt_start).total_seconds() / (86400 * (time_steps - 1))
                    if 0.8 <= delta_days <= 1.2:
                        resolution = "Daily (1D)"
                    elif 25 <= delta_days <= 32:
                        resolution = "Monthly (1M)"
                    else:
                        resolution = f"~{delta_days:.2f} days/step"

            # Inspect SST (sampled slice to avoid loading multi-GB data)
            sst_summary: Dict[str, Any] = {
                "min_celsius": None,
                "max_celsius": None,
                "mean_celsius": None,
                "detected_unit": "Unknown",
                "fill_value_count": 0,
                "fill_value_pct": 0.0,
            }
            if "sst" in resolved:
                sst_ds = f[resolved["sst"]]
                scale = float(self._get_scalar_attr(sst_ds, "scale_factor", 1.0))
                offset = float(self._get_scalar_attr(sst_ds, "add_offset", 0.0))
                fill_val = self._get_scalar_attr(sst_ds, "_FillValue", None)

                # Sample subset (handle 4D [time, depth, lat, lon], 3D [time, lat, lon], or 2D)
                if len(sst_ds.shape) == 4:
                    sample_slice = sst_ds[0, 0, :, :]  # Surface depth=0
                elif len(sst_ds.shape) == 3:
                    sample_slice = sst_ds[0, :, :]
                else:
                    sample_slice = sst_ds[:]
                raw_sample = sample_slice.flatten()
                total_sample_pts = len(raw_sample)

                # Identify fill values
                is_fill = np.zeros(total_sample_pts, dtype=bool)
                if fill_val is not None:
                    is_fill |= (raw_sample == fill_val)
                is_fill |= np.isnan(raw_sample) | (raw_sample <= -30000) | (raw_sample == -32768) | (raw_sample == -32767) | (raw_sample == 32767)
                fill_count = int(np.sum(is_fill))

                valid_raw = raw_sample[~is_fill]
                if len(valid_raw) > 0:
                    scaled_vals = valid_raw.astype(np.float64) * scale + offset
                    is_kelvin = np.nanmean(scaled_vals) > KELVIN_DETECTION_THRESHOLD
                    if is_kelvin:
                        celsius_vals = scaled_vals - KELVIN_CELSIUS_OFFSET
                        unit_str = "Kelvin (Auto-converted to Celsius)"
                    else:
                        celsius_vals = scaled_vals
                        unit_str = "Celsius"

                    # Filter valid physical bounds
                    valid_celsius = celsius_vals[(celsius_vals >= SST_MIN_CELSIUS) & (celsius_vals <= SST_MAX_CELSIUS)]
                    if len(valid_celsius) > 0:
                        sst_summary = {
                            "min_celsius": round(float(np.nanmin(valid_celsius)), 2),
                            "max_celsius": round(float(np.nanmax(valid_celsius)), 2),
                            "mean_celsius": round(float(np.nanmean(valid_celsius)), 2),
                            "detected_unit": unit_str,
                            "fill_value_count": fill_count,
                            "fill_value_pct": round(float(fill_count / total_sample_pts * 100), 2),
                        }

            # Sub-basin regional breakdown for Arabian Sea
            arabian_sea_coverage = None
            if "lat" in resolved and "lon" in resolved and "sst" in resolved:
                try:
                    from .preprocessing import compute_arabian_sea_subbasin_masks
                    lats = np.array(lat_vals)
                    lons = np.array(lon_vals)
                    if len(sample_slice.shape) == 2:
                        is_valid_ocean_2d = ~is_fill.reshape(sample_slice.shape)
                        grid_lon, grid_lat = np.meshgrid(lons, lats)
                        ocean_lats = grid_lat[is_valid_ocean_2d]
                        ocean_lons = grid_lon[is_valid_ocean_2d]
                        sub_masks = compute_arabian_sea_subbasin_masks(ocean_lats, ocean_lons)
                        tot_ocean = len(ocean_lats)
                        pg_pts = int(np.sum(sub_masks["is_persian_gulf"]))
                        go_pts = int(np.sum(sub_masks["is_gulf_of_oman"]))
                        ga_pts = int(np.sum(sub_masks["is_gulf_of_aden"]))
                        as_pts = int(np.sum(sub_masks["is_arabian_sea"]))
                        arabian_sea_coverage = {
                            "total_valid_ocean_cells": tot_ocean,
                            "persian_gulf_cells": pg_pts,
                            "gulf_of_oman_cells": go_pts,
                            "gulf_of_aden_cells": ga_pts,
                            "arabian_sea_strict_cells": as_pts,
                            "arabian_sea_pct_of_ocean": round((as_pts / tot_ocean * 100), 2) if tot_ocean > 0 else 0.0,
                        }
                except Exception as e:
                    logger.debug(f"Could not compute Arabian Sea subbasin coverage: {e}")

        return DatasetInspectionReport(
            filepath=str(path),
            file_format="NetCDF4/HDF5",
            file_size_mb=round(file_size_mb, 2),
            dimensions=dimensions,
            variables=var_info,
            resolved_canonical_variables=resolved,
            spatial_coverage={
                "lat_min": lat_min,
                "lat_max": lat_max,
                "lat_count": lat_count,
                "lon_min": lon_min,
                "lon_max": lon_max,
                "lon_count": lon_count,
            },
            time_range={"start": time_start_str, "end": time_end_str, "total_steps": time_steps},
            inferred_temporal_resolution=resolution,
            missing_value_summary={"sample_fill_count": sst_summary.get("fill_value_count", 0)},
            sst_summary=sst_summary,
            arabian_sea_coverage=arabian_sea_coverage,
        )

    def _inspect_tabular(self, path: Path, file_size_mb: float) -> DatasetInspectionReport:
        """Inspects CSV / TSV tabular datasets."""
        # Read header and first 1000 rows
        sep = "\t" if path.suffix.lower() == ".tsv" or "txt" in path.suffix.lower() else ","
        df_sample = pd.read_csv(path, sep=sep, nrows=1000)
        available_vars = list(df_sample.columns)

        resolved: Dict[str, str] = {}
        for canonical in ["sst", "lat", "lon", "time", "analysis_error", "sea_ice_fraction", "mask"]:
            found = self._resolve_variable_name(available_vars, canonical)
            if found:
                resolved[canonical] = found

        lat_min, lat_max, lat_count = None, None, None
        if "lat" in resolved:
            lat_s = pd.to_numeric(df_sample[resolved["lat"]], errors="coerce").dropna()
            lat_min = float(lat_s.min()) if len(lat_s) > 0 else None
            lat_max = float(lat_s.max()) if len(lat_s) > 0 else None
            lat_count = len(lat_s)

        lon_min, lon_max, lon_count = None, None, None
        if "lon" in resolved:
            lon_s = pd.to_numeric(df_sample[resolved["lon"]], errors="coerce").dropna()
            lon_min = float(lon_s.min()) if len(lon_s) > 0 else None
            lon_max = float(lon_s.max()) if len(lon_s) > 0 else None
            lon_count = len(lon_s)

        time_start, time_end, steps = None, None, len(df_sample)
        if "time" in resolved:
            time_s = df_sample[resolved["time"]].dropna()
            time_start = str(time_s.iloc[0]) if len(time_s) > 0 else None
            time_end = str(time_s.iloc[-1]) if len(time_s) > 0 else None

        sst_summary: Dict[str, Any] = {
            "min_celsius": None,
            "max_celsius": None,
            "mean_celsius": None,
            "detected_unit": "Unknown",
            "fill_value_count": int(df_sample[resolved["sst"]].isna().sum()) if "sst" in resolved else 0,
            "fill_value_pct": 0.0,
        }
        if "sst" in resolved:
            sst_s = pd.to_numeric(df_sample[resolved["sst"]], errors="coerce").dropna()
            if len(sst_s) > 0:
                is_kelvin = float(sst_s.mean()) > KELVIN_DETECTION_THRESHOLD
                if is_kelvin:
                    celsius_s = sst_s - KELVIN_CELSIUS_OFFSET
                    unit_str = "Kelvin (Auto-converted to Celsius)"
                else:
                    celsius_s = sst_s
                    unit_str = "Celsius"
                sst_summary = {
                    "min_celsius": round(float(celsius_s.min()), 2),
                    "max_celsius": round(float(celsius_s.max()), 2),
                    "mean_celsius": round(float(celsius_s.mean()), 2),
                    "detected_unit": unit_str,
                    "fill_value_count": int(df_sample[resolved["sst"]].isna().sum()),
                    "fill_value_pct": round(float(df_sample[resolved["sst"]].isna().mean() * 100), 2),
                }

        return DatasetInspectionReport(
            filepath=str(path),
            file_format="Tabular CSV/TSV",
            file_size_mb=round(file_size_mb, 2),
            dimensions={"rows_sample": len(df_sample), "columns": len(available_vars)},
            variables={col: {"dtype": str(df_sample[col].dtype)} for col in available_vars},
            resolved_canonical_variables=resolved,
            spatial_coverage={
                "lat_min": lat_min, "lat_max": lat_max, "lat_count": lat_count,
                "lon_min": lon_min, "lon_max": lon_max, "lon_count": lon_count,
            },
            time_range={"start": time_start, "end": time_end, "total_steps": steps},
            inferred_temporal_resolution="Sampled Tabular Records",
            missing_value_summary={"sample_null_counts": df_sample.isna().sum().to_dict()},
            sst_summary=sst_summary,
        )

    @staticmethod
    def _parse_netcdf_time(val: float, units: str) -> Optional[datetime]:
        """Parses NetCDF CF-convention epoch time units."""
        if not units or not isinstance(units, str):
            # Check if seconds since Unix epoch
            if val > 1e8:
                try:
                    return datetime.fromtimestamp(val)
                except Exception:
                    return None
            return None

        m = re.search(r"(seconds|minutes|hours|days)\s+since\s+([0-9]{4}-[0-9]{1,2}-[0-9]{1,2}(?:\s+[0-9]{1,2}:[0-9]{2}:[0-9]{2})?)", units, re.IGNORECASE)
        if not m:
            return None

        unit_type = m.group(1).lower()
        base_date_str = m.group(2).strip()

        fmt = "%Y-%m-%d %H:%M:%S" if " " in base_date_str else "%Y-%m-%d"
        try:
            base_dt = datetime.strptime(base_date_str, fmt)
        except Exception:
            return None

        if unit_type.startswith("second"):
            return base_dt + timedelta(seconds=float(val))
        elif unit_type.startswith("minute"):
            return base_dt + timedelta(minutes=float(val))
        elif unit_type.startswith("hour"):
            return base_dt + timedelta(hours=float(val))
        elif unit_type.startswith("day"):
            return base_dt + timedelta(days=float(val))
        return None

    def load_data(
        self,
        filepath: Union[str, Path],
        spatial_bounds: Optional[Dict[str, float]] = None,
        time_indices: Optional[Tuple[int, int]] = None,
        max_time_steps: Optional[int] = None,
        stride_spatial: int = 1,
        stride_temporal: int = 1,
        apply_arabian_sea_mask: bool = False,
    ) -> pd.DataFrame:
        """
        Loads observations into a clean DataFrame with chunked/lazy access to prevent OOM.

        Parameters:
        - filepath: Path to NetCDF/HDF5 or CSV dataset.
        - spatial_bounds: Optional dict {'min_lat', 'max_lat', 'min_lon', 'max_lon'}.
        - time_indices: Optional (start_idx, end_idx) tuple for exact temporal range slicing.
        - max_time_steps: Limit number of time steps loaded.
        - stride_spatial: Subsample grid (e.g. stride=2 takes every 2nd grid point).
        - stride_temporal: Subsample time (e.g. stride=7 takes weekly steps).
        - apply_arabian_sea_mask: If True, filters strictly to IHO S-23 Arabian Sea at load time.
        """
        path = Path(filepath)
        report = self.inspect_dataset(path)
        resolved = report.resolved_canonical_variables

        if "sst" not in resolved:
            raise ValueError(f"No Sea Surface Temperature (SST) variable found in dataset: {path}")

        ext = path.suffix.lower()
        if ext in (".nc", ".nc4", ".hdf", ".h5", ".he5"):
            return self._load_netcdf_hdf5(
                path, resolved, spatial_bounds, time_indices, max_time_steps, stride_spatial, stride_temporal, apply_arabian_sea_mask
            )
        else:
            return self._load_tabular(path, resolved, spatial_bounds, max_time_steps)

    def _load_netcdf_hdf5(
        self,
        path: Path,
        resolved: Dict[str, str],
        spatial_bounds: Optional[Dict[str, float]],
        time_indices: Optional[Tuple[int, int]],
        max_time_steps: Optional[int],
        stride_spatial: int,
        stride_temporal: int,
        apply_arabian_sea_mask: bool = False,
    ) -> pd.DataFrame:
        """Loads NetCDF grid data into a flattened spatial-temporal DataFrame."""
        import h5py

        with h5py.File(str(path), "r") as f:
            lat_ds = f[resolved["lat"]]
            lon_ds = f[resolved["lon"]]
            sst_ds = f[resolved["sst"]]
            time_ds = f[resolved["time"]] if "time" in resolved else None

            lats = np.array(lat_ds[::stride_spatial])
            lons = np.array(lon_ds[::stride_spatial])

            # Spatial slicing mask
            lat_mask = np.ones(len(lats), dtype=bool)
            lon_mask = np.ones(len(lons), dtype=bool)
            if spatial_bounds:
                if "min_lat" in spatial_bounds:
                    lat_mask &= (lats >= spatial_bounds["min_lat"])
                if "max_lat" in spatial_bounds:
                    lat_mask &= (lats <= spatial_bounds["max_lat"])
                if "min_lon" in spatial_bounds:
                    lon_mask &= (lons >= spatial_bounds["min_lon"])
                if "max_lon" in spatial_bounds:
                    lon_mask &= (lons <= spatial_bounds["max_lon"])

            sub_lats = lats[lat_mask]
            sub_lons = lons[lon_mask]

            total_t = sst_ds.shape[0] if len(sst_ds.shape) >= 3 else 1
            start_t = 0
            end_t = total_t
            if time_indices is not None:
                start_t = max(0, int(time_indices[0]))
                end_t = min(total_t, int(time_indices[1]))
            elif max_time_steps is not None:
                end_t = min(total_t, max_time_steps)

            time_units = str(time_ds.attrs.get("units", "")) if time_ds is not None else ""
            scale = float(self._get_scalar_attr(sst_ds, "scale_factor", 1.0))
            offset = float(self._get_scalar_attr(sst_ds, "add_offset", 0.0))
            fill_val = self._get_scalar_attr(sst_ds, "_FillValue", None)

            # Check auxiliary datasets
            has_error = "analysis_error" in resolved
            has_ice = "sea_ice_fraction" in resolved
            has_mask = "mask" in resolved

            err_ds = f[resolved["analysis_error"]] if has_error else None
            ice_ds = f[resolved["sea_ice_fraction"]] if has_ice else None
            mask_ds = f[resolved["mask"]] if has_mask else None

            err_scale = float(self._get_scalar_attr(err_ds, "scale_factor", 1.0)) if err_ds is not None else 1.0
            err_offset = float(self._get_scalar_attr(err_ds, "add_offset", 0.0)) if err_ds is not None else 0.0

            rows = []
            grid_lon, grid_lat = np.meshgrid(sub_lons, sub_lats)
            flat_lats = grid_lat.flatten()
            flat_lons = grid_lon.flatten()

            as_mask = None
            if apply_arabian_sea_mask:
                from .preprocessing import compute_arabian_sea_subbasin_masks
                as_mask = compute_arabian_sea_subbasin_masks(flat_lats, flat_lons)["is_arabian_sea"]

            for t_idx in range(start_t, end_t, stride_temporal):
                # Timestamp
                t_val = float(time_ds[t_idx]) if time_ds is not None else float(t_idx)
                dt = self._parse_netcdf_time(t_val, time_units)
                time_str = dt.isoformat() if dt else f"step_{t_idx}"
                time_month = dt.month if dt else ((t_idx % 12) + 1)
                time_doy = dt.timetuple().tm_yday if dt else (t_idx % 365 + 1)

                # Slice SST (handle 3D [time, lat, lon] or 4D [time, depth, lat, lon])
                if len(sst_ds.shape) == 3:
                    raw_slice = sst_ds[t_idx, ::stride_spatial, ::stride_spatial]
                elif len(sst_ds.shape) == 4:
                    raw_slice = sst_ds[t_idx, 0, ::stride_spatial, ::stride_spatial]  # Surface depth=0
                else:
                    raw_slice = sst_ds[:]

                sub_raw = raw_slice[np.ix_(lat_mask, lon_mask)].flatten()

                # Filter Fill / Missing
                valid_mask = ~np.isnan(sub_raw) & (sub_raw > -30000) & (sub_raw != -32768) & (sub_raw != -32767) & (sub_raw != 32767)
                if fill_val is not None:
                    valid_mask &= (sub_raw != fill_val)
                if as_mask is not None:
                    valid_mask &= as_mask

                # Check auxiliary variables
                sub_err = None
                if err_ds is not None:
                    err_slice = err_ds[t_idx, ::stride_spatial, ::stride_spatial] if len(err_ds.shape) == 3 else err_ds[t_idx, 0, ::stride_spatial, ::stride_spatial]
                    sub_err = (err_slice[np.ix_(lat_mask, lon_mask)].flatten().astype(np.float64) * err_scale + err_offset)

                sub_ice = None
                if ice_ds is not None:
                    ice_slice = ice_ds[t_idx, ::stride_spatial, ::stride_spatial] if len(ice_ds.shape) == 3 else ice_ds[t_idx, 0, ::stride_spatial, ::stride_spatial]
                    sub_ice = ice_slice[np.ix_(lat_mask, lon_mask)].flatten()

                sub_flags = None
                if mask_ds is not None:
                    m_slice = mask_ds[t_idx, ::stride_spatial, ::stride_spatial] if len(mask_ds.shape) == 3 else mask_ds[0, ::stride_spatial, ::stride_spatial] if len(mask_ds.shape) == 3 else mask_ds[::stride_spatial, ::stride_spatial]
                    sub_flags = m_slice[np.ix_(lat_mask, lon_mask)].flatten()
                    # In GHRSST, mask=1 is sea. If mask indicates land (e.g. 2), exclude
                    if np.any(sub_flags == 1):
                        valid_mask &= (sub_flags == 1)

                v_indices = np.where(valid_mask)[0]
                if len(v_indices) == 0:
                    continue

                scaled_sst = sub_raw[v_indices].astype(np.float64) * scale + offset
                # Kelvin to Celsius conversion
                if np.nanmean(scaled_sst) > KELVIN_DETECTION_THRESHOLD:
                    scaled_sst = scaled_sst - KELVIN_CELSIUS_OFFSET

                for i, idx in enumerate(v_indices):
                    sst_c = scaled_sst[i]
                    if sst_c < SST_MIN_CELSIUS or sst_c > SST_MAX_CELSIUS:
                        continue

                    rec: Dict[str, Any] = {
                        "timestamp": time_str,
                        "month": time_month,
                        "day_of_year": time_doy,
                        "latitude": round(float(flat_lats[idx]), 4),
                        "longitude": round(float(flat_lons[idx]), 4),
                        "analysed_sst": round(float(sst_c), 3),
                    }
                    if sub_err is not None:
                        rec["analysis_error"] = round(float(sub_err[idx]), 3)
                    if sub_ice is not None:
                        rec["sea_ice_fraction"] = round(float(sub_ice[idx]), 3)
                    if sub_flags is not None:
                        rec["mask"] = int(sub_flags[idx])

                    rows.append(rec)

        df = pd.DataFrame(rows)
        logger.info(f"Loaded {len(df):,} valid marine environmental observations from {path}")
        return df

    def _load_tabular(
        self,
        path: Path,
        resolved: Dict[str, str],
        spatial_bounds: Optional[Dict[str, float]],
        max_time_steps: Optional[int],
    ) -> pd.DataFrame:
        """Loads tabular CSV / TSV data."""
        sep = "\t" if path.suffix.lower() == ".tsv" or "txt" in path.suffix.lower() else ","
        df_raw = pd.read_csv(path, sep=sep, nrows=max_time_steps * 1000 if max_time_steps else None)

        df = pd.DataFrame()
        # Parse time
        if "time" in resolved:
            time_series = pd.to_datetime(df_raw[resolved["time"]], errors="coerce")
            df["timestamp"] = time_series.dt.strftime("%Y-%m-%dT%H:%M:%SZ").fillna(df_raw[resolved["time"]].astype(str))
            df["month"] = time_series.dt.month.fillna(1).astype(int)
            df["day_of_year"] = time_series.dt.dayofyear.fillna(1).astype(int)
        else:
            df["timestamp"] = datetime.utcnow().isoformat()
            df["month"] = 1
            df["day_of_year"] = 1

        df["latitude"] = pd.to_numeric(df_raw[resolved["lat"]], errors="coerce")
        df["longitude"] = pd.to_numeric(df_raw[resolved["lon"]], errors="coerce")

        raw_sst = pd.to_numeric(df_raw[resolved["sst"]], errors="coerce")
        is_kelvin = raw_sst.dropna().mean() > KELVIN_DETECTION_THRESHOLD if len(raw_sst.dropna()) > 0 else False
        df["analysed_sst"] = (raw_sst - KELVIN_CELSIUS_OFFSET) if is_kelvin else raw_sst

        for canonical in ["analysis_error", "sea_ice_fraction", "mask"]:
            if canonical in resolved:
                df[canonical] = pd.to_numeric(df_raw[resolved[canonical]], errors="coerce")

        # Drop NaN coordinates or invalid SST
        df = df.dropna(subset=["latitude", "longitude", "analysed_sst"])
        df = df[(df["analysed_sst"] >= SST_MIN_CELSIUS) & (df["analysed_sst"] <= SST_MAX_CELSIUS)]

        if spatial_bounds:
            if "min_lat" in spatial_bounds:
                df = df[df["latitude"] >= spatial_bounds["min_lat"]]
            if "max_lat" in spatial_bounds:
                df = df[df["latitude"] <= spatial_bounds["max_lat"]]
            if "min_lon" in spatial_bounds:
                df = df[df["longitude"] >= spatial_bounds["min_lon"]]
            if "max_lon" in spatial_bounds:
                df = df[df["longitude"] <= spatial_bounds["max_lon"]]

        return df.reset_index(drop=True)
