"""Regression tests for the legacy ``dynasir.epydemics.Model`` kept for backward compatibility."""

import numpy as np
import pandas as pd

from dynasir.epydemics import SIRD_COMPARTMENTS, SIRD_LOGIT_RATIOS
from dynasir.epydemics import DataContainer as LegacyDataContainer
from dynasir.epydemics import Model as LegacyModel


def _legacy_container():
    dates = pd.date_range("2020-03-01", periods=60, freq="D")
    rng = np.random.default_rng(42)
    data = pd.DataFrame(
        {
            "C": np.cumsum(rng.exponential(50, len(dates))) + 100,
            "D": np.cumsum(rng.exponential(2, len(dates))) + 1,
            "N": 1_000_000,
        },
        index=dates,
    )
    return LegacyDataContainer(data)


def test_legacy_model_init_sets_training_data():
    container = _legacy_container()
    start, stop = container.data.index[10], container.data.index[40]

    model = LegacyModel(container, start=start, stop=stop)

    assert model.data is not None
    assert model.data.index[0] == start
    assert model.data.index[-1] == stop
    assert model.logit_ratios_values.shape == (len(model.data), len(SIRD_LOGIT_RATIOS))


def test_legacy_model_pipeline_runs_end_to_end():
    container = _legacy_container()
    model = LegacyModel(
        container, start=container.data.index[5], stop=container.data.index[40]
    )

    model.create_logit_ratios_model()
    model.fit_logit_ratios_model(maxlags=2)
    model.forecast_logit_ratios(steps=3)
    model.run_simulations()
    model.generate_result()

    assert len(model.forecasting_interval) == 3
    assert set(model.results.keys()) == set(SIRD_COMPARTMENTS)
    assert all(len(model.results[c]) == 3 for c in SIRD_COMPARTMENTS)


def test_legacy_days_to_forecast_alias():
    model = LegacyModel(_legacy_container(), days_to_forecast=5)
    assert model.days_to_forecast == 5

    model.days_to_forecast = 7

    assert model.steps_to_forecast == 7
    assert model.days_to_forecast == 7
