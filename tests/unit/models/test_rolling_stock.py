"""Active-infection stock for incidence lags above one period (#178).

``I`` stays the weekly incidence; ``I_active`` is the stock of the last two weeks.
"""

import numpy as np
import pandas as pd

from dynasir import ACTIVE_INFECTIONS, DataContainer, Model
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
    np.testing.assert_allclose(data["I"], raw["I"])
    np.testing.assert_allclose(data[ACTIVE_INFECTIONS], expected)
    # Alpha above 1 stays on the log scale, and beta is still its own rate.
    assert "log_alpha" in data.columns
    assert "logit_beta" in data.columns
    assert "logit_alpha" not in data.columns
    growth = data["I"].shift(-1)
    expected_alpha = data["A"] * growth / (data[ACTIVE_INFECTIONS] * data["S"])
    np.testing.assert_allclose(
        data["alpha"].iloc[:-1], expected_alpha.iloc[:-1], rtol=1e-6
    )
    assert (expected_alpha.iloc[:-1] > 1).any()
    container = DataContainer(raw, mode="incidence", frequency="W", window=1)
    assert container.cohort is False
    assert Model(container).cohort is False


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
        simulated["I"], data.loc[dates, "I"], rtol=1e-6, atol=1e-6
    )
    np.testing.assert_allclose(
        simulated["C"], data.loc[dates, "C"], rtol=1e-6, atol=1e-4
    )
