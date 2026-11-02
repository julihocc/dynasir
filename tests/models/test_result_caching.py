import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from dynasir import DataContainer, Model
from dynasir.core.config import get_settings


@pytest.fixture
def caching_test_container():
    """Fixture with realistic epidemic data suitable for VAR modeling."""
    dates = pd.date_range(start="2020-03-01", end="2020-04-15", freq="D")
    np.random.seed(42)

    # Simulate growth with variation to avoid constant columns
    t = np.arange(len(dates))
    base_trend = 10 * np.exp(0.1 * t) + np.random.normal(0, 5, len(dates))
    base_trend = np.maximum(base_trend, 10)  # Ensure positivity

    cases = np.cumsum(np.maximum(base_trend + np.random.normal(0, 10, len(dates)), 1))
    deaths = np.cumsum(
        np.maximum(0.02 * base_trend + np.random.normal(0, 0.5, len(dates)), 0)
    )

    data = pd.DataFrame(
        {"C": cases, "D": deaths, "N": [1000000] * len(dates)}, index=dates
    )

    return DataContainer(data, window=3)


def test_generate_result_uses_cache_roundtrip(
    tmp_path, monkeypatch, caching_test_container
):
    # Enable caching and set a dedicated cache directory
    cache_dir = tmp_path / ".cache"
    monkeypatch.setenv("RESULT_CACHING_ENABLED", "1")
    monkeypatch.setenv("CACHE_DIR", str(cache_dir))
    monkeypatch.setenv("CACHE_STRICT_VERSION", "0")
    # Refresh settings cache to pick up env changes
    get_settings.cache_clear()  # type: ignore[attr-defined]

    # First run: create results and populate cache
    model1 = Model(caching_test_container, start="2020-03-10", stop="2020-03-30")
    model1.create_model()
    model1.fit_model(max_lag=2)
    model1.forecast(steps=5)
    model1.run_simulations(n_jobs=1)
    model1.generate_result()
    assert model1.results is not None
    assert cache_dir.exists()
    # Ensure compartment files exist in exactly one subdir
    subdirs = [p for p in cache_dir.glob("*/") if (p / "C.csv").exists()]
    assert len(subdirs) == 1
    cached_dir = subdirs[0]

    first_C = model1.results["C"].copy()

    # Second run: new model instance, same configuration
    model2 = Model(caching_test_container, start="2020-03-10", stop="2020-03-30")
    model2.create_model()
    model2.fit_model(max_lag=2)
    model2.forecast(steps=5)

    # Do NOT run simulations; generate_result should hit cache and load
    model2.generate_result()

    assert model2.results is not None
    second_C = model2.results["C"]

    # DataFrames should be identical (check values and index, ignoring frequency)
    pd.testing.assert_frame_equal(first_C, second_C, check_freq=False)

    # Confirm we used existing cache directory (no extra directories created)
    subdirs_after = [p for p in cache_dir.glob("*/") if (p / "C.csv").exists()]
    assert len(subdirs_after) == 1
