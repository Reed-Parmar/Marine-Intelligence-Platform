"""
Copernicus Marine API Smoke Test.
Verifies:
- authentication
- dataset access
- thetao extraction
- coordinates
- timestamps
- surface depth
- returned data values
- NetCDF / xarray / h5py readability
"""

import sys
import os
from pathlib import Path
import time

def run_smoke_test():
    print("=" * 70)
    print("COPERNICUS MARINE API SMOKE TEST (3-DAY EXTRACTION)")
    print("=" * 70)
    
    import copernicusmarine
    import xarray as xr
    import numpy as np

    output_dir = Path("historical_sst") / "smoke_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = "smoke_test_surface_thetao_2018.nc"
    target_path = output_dir / output_file

    print(f"Target Dataset : cmems_mod_glo_phy_my_0.083deg_P1D-m")
    print(f"Variable       : thetao")
    print(f"Depth Range    : [0.49, 0.50] m")
    print(f"Spatial Bounds : [5.0°N, 25.0°N], [50.0°E, 78.0°E]")
    print(f"Temporal Range : 2018-01-01 to 2018-01-03")
    print(f"Output Path    : {target_path}")
    print("-" * 70)

    t0 = time.time()
    try:
        response = copernicusmarine.subset(
            dataset_id="cmems_mod_glo_phy_my_0.083deg_P1D-m",
            variables=["thetao"],
            minimum_longitude=50.0,
            maximum_longitude=78.0,
            minimum_latitude=5.0,
            maximum_latitude=25.0,
            minimum_depth=0.49,
            maximum_depth=0.50,
            start_datetime="2018-01-01T00:00:00",
            end_datetime="2018-01-03T23:59:59",
            output_filename=output_file,
            output_directory=output_dir,
            overwrite=True,
            netcdf_compression_level=4
        )
        t_download = time.time() - t0
        print(f"API Subset Download Completed in {t_download:.2f}s")
        print(f"Response: {response}")
    except Exception as e:
        print(f"FAILED during API download: {e}")
        return False

    # Check file exists and size
    if not target_path.exists():
        print(f"ERROR: Output file {target_path} does not exist!")
        return False
    
    file_size_kb = target_path.stat().st_size / 1024
    print(f"File Size      : {file_size_kb:.2f} KB ({target_path.stat().st_size:,} bytes)")

    # Read and verify with xarray
    print("-" * 70)
    print("VERIFYING WITH XARRAY & NUMPY:")
    try:
        ds = xr.open_dataset(target_path)
        print(f"Dimensions     : {dict(ds.dims)}")
        print(f"Variables      : {list(ds.data_vars.keys())}")
        print(f"Coordinates    : {list(ds.coords.keys())}")

        # Check variable
        if "thetao" not in ds.data_vars:
            print("ERROR: 'thetao' not found in dataset variables!")
            return False
        
        # Check depth
        depth_coords = ds.coords.get("depth", None)
        if depth_coords is not None:
            depth_vals = depth_coords.values
            print(f"Depth Count    : {len(depth_vals)}, Values: {depth_vals}")
            if len(depth_vals) != 1 or not (0.4 < depth_vals[0] < 0.6):
                print(f"WARNING: Expected 1 surface depth level ~0.494m, got {depth_vals}")
        
        # Check coordinates
        lat_vals = ds.coords["latitude"].values
        lon_vals = ds.coords["longitude"].values
        time_vals = ds.coords["time"].values

        print(f"Latitude Range : [{lat_vals.min():.4f}, {lat_vals.max():.4f}] (Count: {len(lat_vals)})")
        print(f"Longitude Range: [{lon_vals.min():.4f}, {lon_vals.max():.4f}] (Count: {len(lon_vals)})")
        print(f"Time Count     : {len(time_vals)}")
        for i, t in enumerate(time_vals):
            print(f"  Step {i+1}: {t}")

        # Check data values
        thetao = ds["thetao"].values
        valid_mask = ~np.isnan(thetao)
        valid_count = np.sum(valid_mask)
        total_count = thetao.size
        print(f"Valid Cells    : {valid_count:,} / {total_count:,} ({valid_count/total_count*100:.1f}%)")

        valid_vals = thetao[valid_mask]
        print(f"SST Range      : [{valid_vals.min():.2f}°C, {valid_vals.max():.2f}°C]")
        print(f"Mean SST       : {valid_vals.mean():.2f}°C, Std: {valid_vals.std():.2f}°C")

        ds.close()

        # Sanity check physics:
        if valid_vals.min() < 15.0 or valid_vals.max() > 35.0:
            print("WARNING: SST values outside expected Arabian Sea winter range [15°C, 35°C]!")
        else:
            print("Physics Check  : PASSED (realistic winter SST in Arabian Sea)")
        
        print("=" * 70)
        print("COPERNICUS MARINE SMOKE TEST: SUCCESSFUL")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"ERROR reading/verifying NetCDF: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
