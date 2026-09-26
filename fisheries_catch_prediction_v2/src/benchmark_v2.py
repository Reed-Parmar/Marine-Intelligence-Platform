"""
Benchmarking script for Fisheries Catch Prediction V2.
Measures artifact load time, single prediction latency, and batch throughput.
"""
import os
import sys
import time
import json
import psutil
import numpy as np

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from fisheries_catch_prediction_v2.src.predict_v2 import FisheriesCatchPredictorV2


def run_benchmark_v2(base_dir: str = "fisheries_catch_prediction_v2"):
    print("=" * 60)
    print("RUNNING FISHERIES CATCH PREDICTION V2 BENCHMARK")
    print("=" * 60)

    process = psutil.Process()
    mem_before_mb = process.memory_info().rss / (1024 * 1024)

    # 1. Model Loading Benchmark
    t0_load = time.perf_counter()
    predictor = FisheriesCatchPredictorV2()
    load_time_ms = (time.perf_counter() - t0_load) * 1000.0
    mem_after_mb = process.memory_info().rss / (1024 * 1024)
    mem_delta_mb = mem_after_mb - mem_before_mb

    print(f"V2 Artifact Load Time : {load_time_ms:.2f} ms")
    print(f"Process RAM Before    : {mem_before_mb:.2f} MB")
    print(f"Process RAM After     : {mem_after_mb:.2f} MB (Delta: +{mem_delta_mb:.2f} MB)")

    # 2. Single Latency Benchmark
    sample = {
        "Fleet": "EUESP",
        "Gear": "PS",
        "Effort": 45.0,
        "EffortUnits": "FHOURS",
        "Month": 8,
        "Year": 2022,
        "Latitude": 12.5,
        "Longitude": 62.5
    }

    # Warmup
    for _ in range(10):
        _ = predictor.predict(sample)

    latencies = []
    for _ in range(100):
        t0 = time.perf_counter()
        _ = predictor.predict(sample)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    latencies = np.array(latencies)
    single_res = {
        "mean_latency_ms": float(np.mean(latencies)),
        "median_latency_ms": float(np.median(latencies)),
        "p95_latency_ms": float(np.percentile(latencies, 95)),
        "min_latency_ms": float(np.min(latencies)),
        "max_latency_ms": float(np.max(latencies))
    }
    print(f"Single Latency (Mean)   : {single_res['mean_latency_ms']:.2f} ms")
    print(f"Single Latency (Median) : {single_res['median_latency_ms']:.2f} ms")
    print(f"Single Latency (P95)    : {single_res['p95_latency_ms']:.2f} ms")

    # 3. Batch Throughput Benchmark
    batch_sizes = [10, 50, 100, 500, 1000]
    batch_res = []

    fleets = ["EUESP", "EUFRA", "SYC", "MDV", "JPN"]
    gears = ["PS", "BB", "RNOF"]
    units = ["FHOURS", "FDAYS", "SETS"]

    for b_size in batch_sizes:
        items = []
        for i in range(b_size):
            items.append({
                "Fleet": fleets[i % len(fleets)],
                "Gear": gears[i % len(gears)],
                "Effort": float(10 + (i % 60)),
                "EffortUnits": units[i % len(units)],
                "Month": (i % 12) + 1,
                "Year": 2020 + (i % 3),
                "Latitude": float(5 + (i % 15)),
                "Longitude": float(50 + (i % 25))
            })

        times = []
        for _ in range(5):
            t0 = time.perf_counter()
            _ = predictor.predict_batch(items)
            times.append(time.perf_counter() - t0)

        mean_time = np.mean(times)
        throughput = b_size / mean_time
        per_rec = (mean_time / b_size) * 1000.0

        rec = {
            "batch_size": b_size,
            "mean_batch_time_sec": float(mean_time),
            "throughput_records_per_sec": float(throughput),
            "per_record_latency_ms": float(per_rec)
        }
        batch_res.append(rec)
        print(f"Batch Size: {b_size:4d} | Time: {mean_time*1000:6.1f} ms | Throughput: {throughput:7.1f} records/s | Per Record: {per_rec:5.3f} ms")

    bench_summary = {
        "model_name": predictor.metadata.get("model_name", "Fisheries Catch Predictor V2"),
        "load_time_ms": float(load_time_ms),
        "memory_rss_mb": float(mem_after_mb),
        "memory_delta_mb": float(mem_delta_mb),
        "single_prediction": single_res,
        "batch_benchmarks": batch_res
    }

    out_file = os.path.join(base_dir, "reports", "v2_benchmark_results.json")
    with open(out_file, "w") as f:
        json.dump(bench_summary, f, indent=2)
    print(f"\nSaved benchmark results to {out_file}.")
    return bench_summary


if __name__ == "__main__":
    run_benchmark_v2()
