"""Rolling infectious stock for incidence lags above one period (#178)."""

import numpy as np
import pandas as pd

from dynasir import DataContainer
from dynasir.core.constants import FORECASTING_LEVELS
from dynasir.models.simulation import EpidemicSimulation


def _weekly_incidence():
    index = pd.date_range("2020-01-05", periods=20, freq="W")
    incidence = np.array(
        [10, 11, 9, 10, 12, 11, 10, 9, 10, 11, 10, 9, 10, 11, 10, 12, 11, 10, 9, 10],
        dtype=float,
    )
    # A small share of each week's cases is recorded as a death next week.
    deaths = np.cumsum(0.02 * incidence)
    return pd.DataFrame({"I": incidence, "D": deaths, "N": 1e6}, index=index)


def test_weekly_stock_is_the_last_two_cohorts():
    raw = _weekly_incidence()
    data = DataContainer(raw, mode="incidence", frequency="W", window=1).data

    expected = raw["I"] + raw["I"].shift(1).fillna(0)
    np.testing.assert_allclose(data["incidence"], raw["I"])
    np.testing.assert_allclose(data["I"], expected)
    assert "log_alpha" not in data.columns
    # Denominator of alpha is the stock, not this week's cases.
    # Values above 1 are clipped by the logit transform (#185).
    growth = data["incidence"].shift(-1)
    expected_alpha = data["A"] * growth / (data["I"] * data["S"])
    stored = data["alpha"].iloc[:-1]
    raw_alpha = expected_alpha.iloc[:-1]
    free = raw_alpha < 0.99
    np.testing.assert_allclose(stored[free], raw_alpha[free], rtol=1e-6)
    assert (raw_alpha[~free] > 1).any()
    assert (stored[~free] < 1).all()


def test_weekly_replay_reports_new_cases():
    raw = _weekly_incidence()
    data = DataContainer(raw, mode="incidence", frequency="W", window=1).data
    k, n = 8, 4
    history = data.iloc[: k + 1]
    dates = data.index[k + 1 : k + 1 + n]
    box = {}
    for rate in ("alpha", "beta", "gamma"):
        values = data[rate].iloc[k : k + n].to_numpy()
        box[rate] = pd.DataFrame(
            {level: values for level in FORECASTING_LEVELS}, index=dates
        )
    simulated = EpidemicSimulation(history, box, dates).simulate_for_given_levels(
        ("point",) * 3
    )

    np.testing.assert_allclose(
        simulated["I"], data.loc[dates, "incidence"], rtol=1e-6, atol=1e-6
    )
    np.testing.assert_allclose(
        simulated["C"], data.loc[dates, "C"], rtol=1e-6, atol=1e-4
    )
