"""
Benchmark script for parallel simulation performance.

This script compares sequential vs parallel execution of epidemic simulations
across different numbers of worker processes.

Usage:
    python benchmarks/parallel_simulation_benchmark.py

Results are saved to benchmarks/parallel_benchmark_results.json
"""

import json
import multiprocessing as mp
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dynasir import DataContainer, Model


def create_benchmark_data(n_days: int = 100, seed: int = 42) -> pd.DataFrame:
    """
    Create synthetic epidemiological data for benchmarking.

    Args:
        n_days: Number of days of data to generate
        seed: Random seed for reproducibility

    Returns:
        DataFrame with synthetic epidemic data
    """
    np.random.seed(seed)
    dates = pd.date_range(start="2020-03-01", periods=n_days, freq="D")

    # Simulate realistic epidemic growth
    base_cases = np.cumsum(np.random.exponential(100, n_days))
    base_deaths = np.cumsum(np.random.exponential(5, n_days))

    data = pd.DataFrame({
        "date": dates,
        "total_cases": base_cases,
        "total_deaths": base_deaths,
        "population": [1000000] * n_days,
    })

    # Process to expected format
    data.set_index("date", inplace=True)
    data.index = pd.DatetimeIndex(data.index)
    data.columns = ["C", "D", "N"]

    return data


def benchmark_simulation(
    n_jobs: int,
    data: pd.DataFrame,
    train_end_idx: int,
    forecast_steps: int = 30
) -> Dict:
    """
    Run a single benchmark trial with specified number of jobs.

    Args:
        n_jobs: Number of parallel jobs (1 = sequential)
        data: Input epidemiological data
        train_end_idx: Index to split training data
        forecast_steps: Number of steps to forecast

    Returns:
        Dictionary with timing and configuration info
    """
    # Create model
    container = DataContainer(data, window=7)

    # Use processed data dates (DataContainer shifts data due to lags)
    processed_data = container.data
    start_date = processed_data.index[0].strftime("%Y-%m-%d")
    stop_idx = min(train_end_idx, len(processed_data) - forecast_steps - 1)
    stop_date = processed_data.index[stop_idx].strftime("%Y-%m-%d")

    model = Model(container, start=start_date, stop=stop_date)

    # Fit model (not timed - same for all)
    model.create_model()
    model.fit_model(max_lag=5, ic="aic")
    model.forecast(steps=forecast_steps)

    # Benchmark simulation execution
    start_time = time.perf_counter()
    model.run_simulations(n_jobs=n_jobs)
    end_time = time.perf_counter()

    execution_time = end_time - start_time

    return {
        "n_jobs": n_jobs,
        "execution_time_seconds": execution_time,
        "forecast_steps": forecast_steps,
        "n_scenarios": 27,  # 3^3 scenarios
    }


def run_benchmark_suite(
    data: pd.DataFrame,
    n_trials: int = 3,
    max_workers: int = None
) -> List[Dict]:
    """
    Run complete benchmark suite comparing different worker counts.

    Args:
        data: Input epidemiological data
        n_trials: Number of trials per configuration
        max_workers: Maximum number of workers to test (default: CPU count)

    Returns:
        List of benchmark results
    """
    cpu_count = mp.cpu_count()
    if max_workers is None:
        max_workers = cpu_count

    # Test configurations: sequential, 2, 4, ..., up to CPU count
    test_configs = [1]  # Sequential
    for n in [2, 4, 6, 8]:
        if n <= max_workers:
            test_configs.append(n)
    if cpu_count not in test_configs and cpu_count <= max_workers:
        test_configs.append(cpu_count)

    results = []
    train_end = int(len(data) * 0.7)  # Use 70% for training

    print(f"CPU Count: {cpu_count}")
    print(f"Testing configurations: {test_configs}")
    print(f"Trials per configuration: {n_trials}")
    print(f"Training data points: {train_end}")
    print("-" * 60)

    for n_jobs in test_configs:
        config_times = []

        print(f"\nTesting n_jobs={n_jobs} ({'sequential' if n_jobs == 1 else 'parallel'})...")

        for trial in range(n_trials):
            result = benchmark_simulation(n_jobs, data, train_end)
            config_times.append(result["execution_time_seconds"])
            print(f"  Trial {trial + 1}/{n_trials}: {result['execution_time_seconds']:.3f}s")

        # Calculate statistics
        mean_time = np.mean(config_times)
        std_time = np.std(config_times)
        min_time = np.min(config_times)
        max_time = np.max(config_times)

        result = {
            "n_jobs": n_jobs,
            "execution_mode": "sequential" if n_jobs == 1 else "parallel",
            "mean_time_seconds": mean_time,
            "std_time_seconds": std_time,
            "min_time_seconds": min_time,
            "max_time_seconds": max_time,
            "trials": n_trials,
            "individual_times": config_times,
        }

        results.append(result)
        print(f"  Average: {mean_time:.3f}s ± {std_time:.3f}s")

    # Calculate speedups relative to sequential
    sequential_time = results[0]["mean_time_seconds"]
    for result in results:
        result["speedup"] = sequential_time / result["mean_time_seconds"]
        result["efficiency"] = result["speedup"] / result["n_jobs"] if result["n_jobs"] > 1 else 1.0

    return results


def generate_report(results: List[Dict], metadata: Dict) -> str:
    """
    Generate a markdown report from benchmark results.

    Args:
        results: List of benchmark results
        metadata: Benchmark metadata

    Returns:
        Markdown formatted report string
    """
    report = []
    report.append("# Parallel Simulation Benchmark Results\n")
    report.append(f"**Date**: {metadata['timestamp']}")
    report.append(f"**System**: {metadata['system_info']['platform']}")
    report.append(f"**CPU Count**: {metadata['system_info']['cpu_count']}")
    report.append(f"**Python Version**: {metadata['system_info']['python_version']}\n")

    report.append("## Configuration\n")
    report.append(f"- Data points: {metadata['data_points']}")
    report.append(f"- Training data: {metadata['training_points']}")
    report.append(f"- Forecast steps: {metadata['forecast_steps']}")
    report.append(f"- Scenarios: {metadata['n_scenarios']}")
    report.append(f"- Trials per config: {metadata['n_trials']}\n")

    report.append("## Results Summary\n")
    report.append("| n_jobs | Mode | Mean Time (s) | Std (s) | Speedup | Efficiency |")
    report.append("|--------|------|---------------|---------|---------|------------|")

    for result in results:
        report.append(
            f"| {result['n_jobs']:6d} | "
            f"{result['execution_mode']:10s} | "
            f"{result['mean_time_seconds']:13.3f} | "
            f"{result['std_time_seconds']:7.3f} | "
            f"{result['speedup']:7.2f}x | "
            f"{result['efficiency']:10.1%} |"
        )

    report.append("\n## Analysis\n")

    # Find best parallel configuration
    parallel_results = [r for r in results if r["n_jobs"] > 1]
    if parallel_results:
        best_parallel = min(parallel_results, key=lambda x: x["mean_time_seconds"])
        sequential = results[0]

        speedup = best_parallel["speedup"]
        time_saved = sequential["mean_time_seconds"] - best_parallel["mean_time_seconds"]

        report.append(f"- **Best configuration**: n_jobs={best_parallel['n_jobs']}")
        report.append(f"- **Maximum speedup**: {speedup:.2f}x")
        report.append(f"- **Time saved**: {time_saved:.2f}s ({time_saved/sequential['mean_time_seconds']:.1%} reduction)")
        report.append(f"- **Efficiency**: {best_parallel['efficiency']:.1%}")

        if speedup < best_parallel['n_jobs'] * 0.7:  # Less than 70% ideal speedup
            report.append(f"\nNote: Efficiency is moderate ({best_parallel['efficiency']:.1%}), "
                         "suggesting overhead from process creation and data serialization.")

    report.append("\n## Recommendations\n")
    report.append("For production use:")
    if parallel_results:
        report.append(f"- Use `n_jobs={best_parallel['n_jobs']}` for best performance on this system")
        report.append(f"- Expected speedup: ~{speedup:.1f}x over sequential execution")
    report.append("- Set `PARALLEL_SIMULATIONS=True` in config or .env")
    report.append("- Use `n_jobs=1` for debugging or when running many models simultaneously")

    return "\n".join(report)


def main():
    """Run benchmark suite and save results."""
    import platform

    print("=" * 60)
    print("Parallel Simulation Benchmark")
    print("=" * 60)

    # Create output directory
    output_dir = Path(__file__).parent
    output_dir.mkdir(exist_ok=True)

    # Generate benchmark data
    print("\nGenerating benchmark data...")
    data = create_benchmark_data(n_days=150, seed=42)
    train_points = int(len(data) * 0.7)

    # Run benchmarks
    print("\nRunning benchmarks...")
    results = run_benchmark_suite(data, n_trials=3)

    # Compile metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "system_info": {
            "platform": platform.platform(),
            "cpu_count": mp.cpu_count(),
            "python_version": platform.python_version(),
        },
        "data_points": len(data),
        "training_points": train_points,
        "forecast_steps": 30,
        "n_scenarios": 27,
        "n_trials": 3,
    }

    # Save JSON results
    json_output = {
        "metadata": metadata,
        "results": results,
    }

    json_path = output_dir / "parallel_benchmark_results.json"
    with open(json_path, "w") as f:
        json.dump(json_output, f, indent=2)

    print(f"\nResults saved to: {json_path}")

    # Generate and save report
    report = generate_report(results, metadata)
    report_path = output_dir / "parallel_benchmark_report.md"
    with open(report_path, "w") as f:
        f.write(report)

    print(f"Report saved to: {report_path}")

    # Print report to console
    print("\n" + "=" * 60)
    print(report)
    print("=" * 60)


if __name__ == "__main__":
    main()
