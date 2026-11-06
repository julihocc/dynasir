"""Prophet uses the training index instead of a synthetic daily one (#188)."""

import numpy as np
import pandas as pd

from dynasir.models.forecasting.orchestrator import ForecastingOrchestrator
from dynasir.models.forecasting.prophet import ProphetForecaster


def test_prophet_keeps_a_weekly_index():
    index = pd.date_range("2020-01-05", periods=12, freq="W")
    frame = pd.DataFrame(np.ones((12, 3)), index=index)
    forecaster = ProphetForecaster(frame)

    assert forecaster.data_index.equals(index)
    assert str(forecaster._forecast_freq()).startswith("W")


def test_orchestrator_passes_annual_dates_not_a_daily_range():
    index = pd.date_range("2010-12-31", periods=12, freq="YE")
    values = np.column_stack(
        [np.linspace(-1, 1, 11), np.linspace(0.2, 0.4, 11), np.linspace(0.1, 0.2, 11)]
    )
    data = pd.DataFrame(
        {"logit_alpha": 0.0, "logit_beta": 0.0, "logit_gamma": 0.0},
        index=index,
    )
    orchestrator = ForecastingOrchestrator(
        data,
        values,
        window=1,
        active_logit_ratios=["logit_alpha", "logit_beta", "logit_gamma"],
        backend="prophet",
    )
    received = orchestrator.forecaster.data_index

    assert len(received) == 11
    assert received.equals(index[:11])
    assert not str(orchestrator.forecaster._forecast_freq()).startswith("D")
