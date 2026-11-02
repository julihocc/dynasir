"""
Annual incidence data with a fractional recovery lag (14/365 years).

With a recovery lag of at most one period, incidence data is modelled as
period cohorts: alpha is log-transformed and beta = 1 - gamma.
"""

import numpy as np
import pandas as pd
import pytest

from dynasir import DataContainer, Model
from dynasir.data.frequency_handlers import FrequencyHandlerRegistry


@pytest.fixture
def mexico_annual():
    """Mexico-like annual measles data, 2010-2024."""
    dates = pd.date_range("2010", periods=15, freq="YE")
    incident_cases = np.array(
        [220, 55, 667, 164, 81, 34, 12, 0, 0, 4, 18, 45, 103, 67, 89]
    )
    incident_deaths = np.array([1, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 1])
    return pd.DataFrame(
        {
            "I": incident_cases,
            "D": np.cumsum(incident_deaths),
            "N": [120_000_000 + i * 2_000_000 for i in range(15)],
        },
        index=dates,
    )


def test_annual_recovery_lag_is_fractional():
    handler = FrequencyHandlerRegistry.get("YE")
    assert handler.get_recovery_lag() == pytest.approx(14 / 365)


def test_annual_incidence_rates_vary(mexico_annual):
    container = DataContainer(mexico_annual, mode="incidence", frequency="YE", window=1)

    assert container.data["alpha"].std() > 1e-6
    assert container.data["gamma"].std() > 1e-6
    np.testing.assert_allclose(
        container.data["beta"], 1 - container.data["gamma"], atol=1e-9
    )
    assert "log_alpha" in container.data.columns
    assert "logit_alpha" not in container.data.columns
    assert "logit_beta" not in container.data.columns


def test_annual_incidence_workflow_runs(mexico_annual):
    container = DataContainer(mexico_annual, mode="incidence", frequency="YE", window=1)
    model = Model(container, start="2010-12-31", stop="2020-12-31")
    model.create_model()
    model.fit_model(max_lag=3)
    model.forecast(steps=5)
    model.run_simulations(n_jobs=1)
    model.generate_result()

    forecast_i = model.results["I"]["mean"]
    assert len(forecast_i) == 5
    assert np.isfinite(forecast_i).all()
