"""
Production Training & Evaluation Pipeline for Marine Environmental Anomaly Detection.

Implements:
1. Real-data smoke test on initial slice.
2. Full chronological 2-year production training:
   - Train: 2024 data (366 daily steps, leak-free empirical baseline)
   - Test: 2025 data (365 daily steps, out-of-time evaluation)
3. Strict IHO S-23 Arabian Sea study domain masking (excluding Persian Gulf, Gulf of Oman, Gulf of Aden).
4. Artifact saving, unsupervised evaluation reporting, and diagnostic plotting.

Usage:
  python scripts/train_environmental_anomaly.py [--stride-spatial 2] [--skip-smoke-test]
"""

import argparse
import datetime
import json
import logging
from pathlib import Path
import sys
import time

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from ml.environmental_anomaly.data_loader import EnvironmentalDataLoader
from ml.environmental_anomaly.evaluate import EnvironmentalAnomalyEvaluator
from ml.environmental_anomaly.predict import EnvironmentalAnomalyInferenceEngine
from ml.environmental_anomaly.train import EnvironmentalAnomalyTrainer
from ml.environmental_anomaly.utils import (
    generate_diagnostic_plots,
    generate_synthetic_environmental_netcdf,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TrainEnvironmentalAnomaly")


def run_smoke_test(loader: EnvironmentalDataLoader, dataset_path: Path, stride_spatial: int) -> bool:
    """Executes a limited real-data smoke test to confirm pipeline health before full run."""
    print("\n" + "=" * 85)
    print("STEP 1: REAL-DATA PRE-TRAINING SMOKE TEST")
    print("=" * 85)
    t0 = time.time()
    try:
        # Load 5 days of 2024 train and 2 days of 2025 test
        logger.info("Smoke Test: Loading 5 real training days (2024)...")
        train_sample = loader.load_data(
            dataset_path,
            time_indices=(0, 5),
            stride_spatial=stride_spatial,
            apply_arabian_sea_mask=True,
        )

        logger.info("Smoke Test: Loading 2 real testing days (2025)...")
        test_sample = loader.load_data(
            dataset_path,
            time_indices=(366, 368),
            stride_spatial=stride_spatial,
            apply_arabian_sea_mask=True,
        )

        print(f"  Train slice loaded: {len(train_sample):,} rows ({train_sample['timestamp'].min()} to {train_sample['timestamp'].max()})")
        print(f"  Test slice loaded:  {len(test_sample):,} rows ({test_sample['timestamp'].min()} to {test_sample['timestamp'].max()})")

        # Run trainer on smoke test
        trainer = EnvironmentalAnomalyTrainer()
        enriched_test, meta, enriched_train = trainer.fit_evaluate_chronological(
            train_sample, test_sample, dataset_name=dataset_path.name
        )

        elapsed = time.time() - t0
        print(f"  Features engineered : {meta['features_used']}")
        print(f"  Isolation Forest fit: SUCCESS ({len(enriched_train):,} train, {len(enriched_test):,} test)")
        print(f"  Test anomalies detected: {meta['test_results']['anomaly_count']:,} ({meta['test_results']['anomaly_rate_pct']}%)")
        print(f"  Smoke Test Completed in {elapsed:.2f}s with zero errors!")
        print("=" * 85 + "\n")
        return True
    except Exception as e:
        logger.error(f"Smoke test failed: {e}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(description="Train Marine Environmental Anomaly Detection Model.")
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Path to real NetCDF/HDF5 or CSV dataset.",
    )
    parser.add_argument(
        "--use-synthetic",
        action="store_true",
        help="Generate and train on synthetic development fixture (DEVELOPMENT ONLY).",
    )
    parser.add_argument(
        "--stride-spatial",
        type=int,
        default=2,
        help="Spatial downsampling stride (default: 2 -> ~18.5 km grid).",
    )
    parser.add_argument(
        "--skip-smoke-test",
        action="store_true",
        help="Skip the pre-training smoke test and proceed directly to full training.",
    )
    args = parser.parse_args()

    data_dir = root_dir / "data" / "environmental_anomaly"
    models_dir = root_dir / "models" / "environmental_anomaly"
    results_dir = root_dir / "results" / "environmental_anomaly"

    models_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = None
    is_synthetic = False

    if args.use_synthetic:
        logger.info("Flag --use-synthetic specified. Generating synthetic development fixture...")
        synthetic_path = data_dir / "synthetic_environmental_test.nc"
        generate_synthetic_environmental_netcdf(synthetic_path, num_days=60, num_lats=20, num_lons=25)
        dataset_path = synthetic_path
        is_synthetic = True
    elif args.dataset:
        dataset_path = Path(args.dataset)
    else:
        # Check data_2yr/ first
        data_2yr_dir = root_dir / "data_2yr"
        files_2yr = list(data_2yr_dir.glob("*.nc")) + list(data_2yr_dir.glob("*.csv")) if data_2yr_dir.exists() else []
        files_data = list(data_dir.glob("*.nc")) + list(data_dir.glob("*.csv")) if data_dir.exists() else []

        if files_2yr:
            dataset_path = files_2yr[0]
            logger.info(f"Discovered REAL environmental dataset in data_2yr/: {dataset_path.name}")
        elif files_data:
            dataset_path = files_data[0]
            logger.info(f"Found dataset in data directory: {dataset_path.name}")
        else:
            raise FileNotFoundError("No environmental dataset found in data_2yr/ or data/environmental_anomaly/.")

    print("\n" + "=" * 85)
    print("CMLRE MARINE INTELLIGENCE PLATFORM — PHASE 14.1")
    print("PRODUCTION ENVIRONMENTAL ANOMALY DETECTION MODEL TRAINING")
    print(f"Target Dataset : {dataset_path}")
    print(f"Dataset Nature : {'[SYNTHETIC TEST FIXTURE]' if is_synthetic else '[REAL 2-YEAR OBSERVATIONAL REANALYSIS]'}")
    print(f"Study Region   : Arabian Sea (Strict IHO S-23 Demarcation)")
    print(f"Spatial Stride : {args.stride_spatial} (~18.5 km effective grid)")
    print("=" * 85 + "\n")

    loader = EnvironmentalDataLoader()

    # Step 1: Dynamic Inspection
    report = loader.inspect_dataset(dataset_path)
    report.print_summary()

    # Step 2: Smoke Test (if real data and not skipped)
    if not is_synthetic and not args.skip_smoke_test:
        smoke_passed = run_smoke_test(loader, dataset_path, args.stride_spatial)
        if not smoke_passed:
            logger.error("Smoke test failed. Aborting full production training.")
            sys.exit(1)

    # Step 3: Full Chronological Production Loading
    print("=" * 85)
    print("STEP 2: FULL PRODUCTION DATA LOADING (CHRONOLOGICAL SPLIT)")
    print("=" * 85)
    t_load_start = time.time()

    if not is_synthetic:
        # 2024: indices 0 to 366 (366 days in leap year 2024)
        logger.info("Loading 2024 Training Set (366 days, Arabian Sea masked, stride=2)...")
        train_raw_df = loader.load_data(
            dataset_path,
            time_indices=(0, 366),
            stride_spatial=args.stride_spatial,
            apply_arabian_sea_mask=True,
        )
        print(f"  Loaded 2024 Train: {len(train_raw_df):,} observations ({train_raw_df['timestamp'].min()} to {train_raw_df['timestamp'].max()})")

        # 2025: indices 366 to 731 (365 days in 2025)
        logger.info("Loading 2025 Testing Set (365 days, Arabian Sea masked, stride=2)...")
        test_raw_df = loader.load_data(
            dataset_path,
            time_indices=(366, 731),
            stride_spatial=args.stride_spatial,
            apply_arabian_sea_mask=True,
        )
        print(f"  Loaded 2025 Test : {len(test_raw_df):,} observations ({test_raw_df['timestamp'].min()} to {test_raw_df['timestamp'].max()})")
        print(f"  Total Observations Loaded: {len(train_raw_df) + len(test_raw_df):,} in {time.time()-t_load_start:.2f}s")
    else:
        # Synthetic fallback
        full_raw = loader.load_data(dataset_path, stride_spatial=args.stride_spatial, apply_arabian_sea_mask=True)
        split_idx = int(len(full_raw) * 0.6)
        train_raw_df = full_raw.iloc[:split_idx].copy()
        test_raw_df = full_raw.iloc[split_idx:].copy()

    # Step 4: Model Training & Evaluation
    print("\n" + "=" * 85)
    print("STEP 3: ISOLATION FOREST MODEL TRAINING & CHRONOLOGICAL EVALUATION")
    print("=" * 85)
    t_train_start = time.time()
    trainer = EnvironmentalAnomalyTrainer()

    print(f"Exact Features Configured:")
    print(f"  - analysed_sst (SST at depth=0.494 m)")
    print(f"  - sst_anomaly (T_obs - T_baseline(cell, month))")
    print(f"  - latitude")
    print(f"  - longitude")
    print(f"  - month_sin, month_cos (annual cyclic seasonality)")
    print(f"  - day_sin, day_cos (day-of-year cyclic seasonality)")

    test_predictions, metadata, train_predictions = trainer.fit_evaluate_chronological(
        train_raw_df=train_raw_df,
        test_raw_df=test_raw_df,
        dataset_name=dataset_path.name,
    )
    train_time = round(time.time() - t_train_start, 2)
    metadata["training_duration_seconds"] = train_time
    print(f"Training & Chronological Evaluation completed in {train_time:.2f}s!")

    # Step 5: Save Production Artifacts
    print("\n" + "=" * 85)
    print("STEP 4: SAVING PRODUCTION MODEL ARTIFACTS")
    print("=" * 85)
    trainer.save_artifacts(models_dir, metadata=metadata)
    print(f"  Saved: {models_dir / 'isolation_forest.joblib'}")
    print(f"  Saved: {models_dir / 'baseline_calculator.json'}")
    print(f"  Saved: {models_dir / 'feature_config.json'}")
    print(f"  Saved: {models_dir / 'metadata.json'}")

    # Step 6: Detailed Evaluation & Diagnostics
    print("\n" + "=" * 85)
    print("STEP 5: UNSUPERVISED EVALUATION & STATISTICAL METRICS")
    print("=" * 85)
    eval_report = EnvironmentalAnomalyEvaluator.evaluate(test_predictions)
    eval_report.print_summary()
    EnvironmentalAnomalyEvaluator.save_evaluation_results(eval_report, test_predictions, results_dir)

    # Save a representative 50k prediction sample CSV for inspection & dashboard
    sample_csv_path = results_dir / "predictions_sample.csv"
    sample_df = test_predictions.sample(min(50000, len(test_predictions)), random_state=42)
    sample_df.to_csv(sample_csv_path, index=False)
    print(f"  Saved test predictions sample: {sample_csv_path} ({len(sample_df):,} rows)")

    # Step 7: Diagnostic Visualizations
    print("\n" + "=" * 85)
    print("STEP 6: GENERATING DIAGNOSTIC PLOTS")
    print("=" * 85)
    plots = generate_diagnostic_plots(test_predictions, results_dir)
    for plot_name, plot_path in plots.items():
        print(f"  Generated Plot [{plot_name}]: {plot_path}")

    # Step 8: Verify Inference Engine from Disk
    print("\n" + "=" * 85)
    print("STEP 7: PRODUCTION INFERENCE ENGINE VERIFICATION")
    print("=" * 85)
    engine = EnvironmentalAnomalyInferenceEngine(models_dir).load()
    test_cases = [
        # 1. Normal spring condition in central Arabian Sea
        {"latitude": 15.0, "longitude": 65.0, "timestamp": "2025-04-15T00:00:00Z", "analysed_sst": 28.5},
        # 2. Extreme Marine Heatwave (+3.5°C anomaly)
        {"latitude": 15.0, "longitude": 65.0, "timestamp": "2025-04-15T00:00:00Z", "analysed_sst": 32.5},
        # 3. Severe Upwelling Cold Surge (-3.0°C anomaly off SW coast)
        {"latitude": 9.0, "longitude": 75.5, "timestamp": "2025-07-15T00:00:00Z", "analysed_sst": 24.0},
    ]

    for tc in test_cases:
        res = engine.predict([tc])[0]
        status_label = "[ANOMALY]" if res.is_anomaly else "[NORMAL]"
        print(f"  {status_label} Lat={tc['latitude']}, Lon={tc['longitude']}, SST={tc['analysed_sst']}°C -> "
              f"Baseline={res.sst_baseline_celsius}°C, Anom={res.sst_anomaly_celsius:+.2f}°C, "
              f"Score={res.anomaly_score:.1f}, Severity={res.severity}, Type='{res.anomaly_type}'")

    print("\n" + "=" * 85)
    print("ENVIRONMENTAL ANOMALY DETECTION MODEL TRAINING COMPLETE")
    print(f"DATA SOURCE: {'REAL OBSERVATIONAL DATA (2024-2025)' if not is_synthetic else 'SYNTHETIC FIXTURE'}")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    main()
