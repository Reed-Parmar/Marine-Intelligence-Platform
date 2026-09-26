"""
Performance Benchmarking Module for Fisheries Catch Prediction (Phase 14.3).
Measures:
- Model and artifact loading time
- Single prediction latency distribution (mean, median, p95, min, max)
- Batch prediction throughput (records/sec across various batch sizes)
- Process memory usage (RSS before and after loading)
"""
import os
import sys
import time
import json
import psutil
import numpy as np
import pandas as pd

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from fisheries_catch_prediction.src.predict import FisheriesCatchPredictor


def run_benchmark(base_dir: str = "fisheries_catch_prediction"):
    print("=" * 60)
    print("RUNNING FISHERIES CATCH PREDICTION PERFORMANCE BENCHMARK")
    print("=" * 60)

    process = psutil.Process()
    mem_before_mb = process.memory_info().rss / (1024 * 1024)

    # 1. Model Loading Benchmark
    print("\n[1] Benchmarking Model Artifact Loading Time...")
    t0_load = time.perf_counter()
    predictor = FisheriesCatchPredictor()
    load_time_ms = (time.perf_counter() - t0_load) * 1000.0
    mem_after_mb = process.memory_info().rss / (1024 * 1024)
    mem_delta_mb = mem_after_mb - mem_before_mb

    print(f"Artifact Load Time : {load_time_ms:.2f} ms")
    print(f"Process RAM Before : {mem_before_mb:.2f} MB")
    print(f"Process RAM After  : {mem_after_mb:.2f} MB (Delta: +{mem_delta_mb:.2f} MB)")

    # 2. Single Prediction Latency Benchmark
    print("\n[2] Benchmarking Single Prediction Latency (100 iterations)...")
    sample_request = {
        "Fleet": "EUESP",
        "Gear": "PS",
        "Effort": 45.0,
        "EffortUnits": "FHOURS",
        "Month": 8,
        "Year": 2022,
        "Latitude": 2.5,
        "Longitude": 55.5
    }

    # Warmup
    for _ in range(10):
        _ = predictor.predict(sample_request)

    latencies_ms = []
    for _ in range(100):
        t0 = time.perf_counter()
        _ = predictor.predict(sample_request)
        lat = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(lat)

    latencies_ms = np.array(latencies_ms)
    single_metrics = {
        "mean_latency_ms": float(np.mean(latencies_ms)),
        "median_latency_ms": float(np.median(latencies_ms)),
        "p95_latency_ms": float(np.percentile(latencies_ms, 95)),
        "p99_latency_ms": float(np.percentile(latencies_ms, 99)),
        "min_latency_ms": float(np.min(latencies_ms)),
        "max_latency_ms": float(np.max(latencies_ms))
    }
    print(f"Single Latency (Mean)   : {single_metrics['mean_latency_ms']:.2f} ms")
    print(f"Single Latency (Median) : {single_metrics['median_latency_ms']:.2f} ms")
    print(f"Single Latency (P95)    : {single_metrics['p95_latency_ms']:.2f} ms")

    # 3. Batch Throughput Benchmark
    print("\n[3] Benchmarking Batch Throughput across batch sizes...")
    batch_sizes = [10, 50, 100, 500, 1000]
    batch_results = []

    # Generate synthetic realistic batch items
    fleets = ["EUESP", "EUFRA", "SYC", "MDV", "JPN"]
    gears = ["PS", "BB", "RNOF"]
    units = ["FHOURS", "FDAYS", "SETS"]

    for b_size in batch_sizes:
        batch_items = []
        for i in range(b_size):
            batch_items.append({
                "Fleet": fleets[i % len(fleets)],
                "Gear": gears[i % len(gears)],
                "Effort": float(10 + (i % 60)),
                "EffortUnits": units[i % len(units)],
                "Month": (i % 12) + 1,
                "Year": 2020 + (i % 3),
                "Latitude": float(-10 + (i % 20)),
                "Longitude": float(45 + (i % 35))
            })

        # Run 5 iterations per batch size
        times = []
        for _ in range(5):
            t0 = time.perf_counter()
            _ = predictor.predict_batch(batch_items)
            times.append(time.perf_counter() - t0)

        mean_time = np.mean(times)
        throughput = b_size / mean_time
        per_record_ms = (mean_time / b_size) * 1000.0

        rec = {
            "batch_size": b_size,
            "mean_batch_time_sec": float(mean_time),
            "throughput_records_per_sec": float(throughput),
            "per_record_latency_ms": float(per_record_ms)
        }
        batch_results.append(rec)
        print(f"Batch Size: {b_size:4d} | Time: {mean_time*1000:6.1f} ms | Throughput: {throughput:7.1f} records/s | Per Record: {per_record_ms:5.3f} ms")

    benchmark_summary = {
        "model_name": "IOTC Fisheries Catch Predictor (XGBoost Tuned)",
        "memory_rss_mb": float(mem_after_mb),
        "model_memory_delta_mb": float(mem_delta_mb),
        "model_load_time_ms": float(load_time_ms),
        "single_prediction": single_metrics,
        "batch_benchmarks": batch_results
    }

    out_path = os.path.join(base_dir, "reports", "benchmark_results.json")
    with open(out_path, "w") as f:
        json.dump(benchmark_summary, f, indent=2)
    print(f"\nBenchmark results saved to {out_path}.")
    return benchmark_summary


if __name__ == "__main__":
    run_benchmark()
