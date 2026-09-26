"""
Script to Measure Inference Performance (Phase U).
Measures model file size, parameter counts, latency percentiles (P50, P90, P99),
and throughput (images/sec) across real test images.
"""

import json
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.inference.predict import MarineSpeciesIdentifier


def main():
    print("=" * 60)
    print("PHASE U: INFERENCE PERFORMANCE BENCHMARKING")
    print("=" * 60)

    identifier = MarineSpeciesIdentifier()
    test_csv = PROJECT_ROOT / "data" / "splits" / "test.csv"
    df = pd.read_csv(test_csv)

    sample_size = min(150, len(df))
    sample_df = df.sample(n=sample_size, random_state=42).reset_index(drop=True)
    sample_paths = [Path(p) for p in sample_df["image_path"]]

    # Model file size
    weights_path = identifier.weights_path
    file_size_mb = round(weights_path.stat().st_size / (1024 * 1024), 2)

    # Warmup
    print(f"Warming up model on 10 images...")
    for p in sample_paths[:10]:
        _ = identifier.predict(p)

    # Latency benchmarking
    print(f"Benchmarking inference latency on {sample_size} real test images...")
    latencies_ms = []

    for p in sample_paths:
        t0 = time.perf_counter()
        _ = identifier.predict(p)
        lat = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(lat)

    latencies = np.array(latencies_ms)
    mean_lat = float(np.mean(latencies))
    median_lat = float(np.median(latencies))
    p90_lat = float(np.percentile(latencies, 90))
    p95_lat = float(np.percentile(latencies, 95))
    p99_lat = float(np.percentile(latencies, 99))
    throughput_fps = float(1000.0 / mean_lat)

    # Parameter count
    total_params = sum(p.numel() for p in identifier.model.parameters())
    trainable_params = sum(p.numel() for p in identifier.model.parameters() if p.requires_grad)

    results = {
        "model_architecture": "ResNet-18 Transfer Learning",
        "device": str(identifier.device),
        "model_file_size_mb": file_size_mb,
        "total_parameters": total_params,
        "trainable_parameters": trainable_params,
        "benchmark_samples": sample_size,
        "mean_latency_ms": round(mean_lat, 2),
        "median_latency_ms": round(median_lat, 2),
        "p90_latency_ms": round(p90_lat, 2),
        "p95_latency_ms": round(p95_lat, 2),
        "p99_latency_ms": round(p99_lat, 2),
        "approximate_throughput_fps": round(throughput_fps, 1)
    }

    results_path = PROJECT_ROOT / "results" / "performance_metrics.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n--- PERFORMANCE SUMMARY ---")
    print(f"Device:               {identifier.device}")
    print(f"Model File Size:      {file_size_mb} MB")
    print(f"Total Parameters:     {total_params:,}")
    print(f"Mean Latency:         {mean_lat:.2f} ms")
    print(f"Median (P50) Latency: {median_lat:.2f} ms")
    print(f"P95 Latency:          {p95_lat:.2f} ms")
    print(f"P99 Latency:          {p99_lat:.2f} ms")
    print(f"Throughput:           {throughput_fps:.1f} images/sec (FPS)")
    print(f"Saved to {results_path}")


if __name__ == "__main__":
    main()
