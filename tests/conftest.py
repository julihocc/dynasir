"""Test configuration and fixtures."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_owid_data():
    """Sample OWID-format epidemiological data for testing."""
    dates = pd.date_range(start="2020-03-01", end="2020-03-31", freq="D")
    np.random.seed(42)  # Reproducible data

    # Simulate realistic epidemic data
    base_cases = np.cumsum(np.random.exponential(50, len(dates)))
    base_deaths = np.cumsum(np.random.exponential(2, len(dates)))

    data = pd.DataFrame(
        {
            "date": dates,
            "total_cases": base_cases,
            "total_deaths": base_deaths,
            "population": [1000000] * len(dates),
        }
    )

    return data


@pytest.fixture
def sample_processed_data():
    """Sample processed epidemiological data for testing."""
    dates = pd.date_range(start="2020-03-01", end="2020-03-31", freq="D")

    data = pd.DataFrame(
        {
            "C": np.cumsum(np.random.exponential(50, len(dates))),
            "D": np.cumsum(np.random.exponential(2, len(dates))),
            "N": [1000000] * len(dates),
        },
        index=dates,
    )

    return data


@pytest.fixture
def sample_data_container(sample_owid_data):
    """DataContainer instance with processed sample data."""
    from dynasir.data.container import DataContainer

    # Process the data similar to process_data_from_owid
    processed_data = sample_owid_data.copy()
    processed_data.set_index("date", inplace=True)
    processed_data.index = pd.DatetimeIndex(processed_data.index)
    processed_data.columns = ["C", "D", "N"]

    return DataContainer(processed_data)


# --- Annual Data Fixtures (v0.8.0+) ---


@pytest.fixture
def sample_annual_owid_data():
    """Sample annual OWID-format epidemiological data for testing."""
    dates = pd.date_range(start="2015", periods=10, freq="YE")
    np.random.seed(42)  # Reproducible data

    # Simulate annual measles-like data (smaller numbers, more variability)
    base_cases = np.cumsum(np.random.exponential(200, len(dates)))
    base_deaths = np.cumsum(np.random.exponential(5, len(dates)))

    data = pd.DataFrame(
        {
            "date": dates,
            "total_cases": base_cases,
            "total_deaths": base_deaths,
            "population": [300000000] * len(dates),  # Large population (e.g., USA)
        }
    )

    return data


@pytest.fixture
def sample_annual_processed_data():
    """Sample annual processed epidemiological data for testing."""
    dates = pd.date_range(start="2015", periods=10, freq="YE")
    np.random.seed(42)

    data = pd.DataFrame(
        {
            "C": np.cumsum(np.random.exponential(200, len(dates))),
            "D": np.cumsum(np.random.exponential(5, len(dates))),
            "N": [300000000] * len(dates),
        },
        index=dates,
    )

    return data


@pytest.fixture
def sample_annual_data_container(sample_annual_owid_data):
    """DataContainer instance with annual sample data."""
    from dynasir.data.container import DataContainer

    # Process the data
    processed_data = sample_annual_owid_data.copy()
    processed_data.set_index("date", inplace=True)
    processed_data.index = pd.DatetimeIndex(processed_data.index)
    processed_data.columns = ["C", "D", "N"]

    return DataContainer(processed_data, window=1)  # window=1 for annual


@pytest.fixture
def sample_weekly_data():
    """Sample weekly epidemiological data for testing."""
    dates = pd.date_range(start="2020-01-01", periods=52, freq="W")
    np.random.seed(42)

    data = pd.DataFrame(
        {
            "C": np.cumsum(np.random.exponential(100, len(dates))),
            "D": np.cumsum(np.random.exponential(3, len(dates))),
            "N": [1000000] * len(dates),
        },
        index=dates,
    )

    return data


@pytest.fixture
def sample_monthly_data():
    """Sample monthly epidemiological data for testing."""
    dates = pd.date_range(start="2020-01", periods=24, freq="ME")
    np.random.seed(42)

    data = pd.DataFrame(
        {
            "C": np.cumsum(np.random.exponential(500, len(dates))),
            "D": np.cumsum(np.random.exponential(10, len(dates))),
            "N": [1000000] * len(dates),
        },
        index=dates,
    )

    return data
