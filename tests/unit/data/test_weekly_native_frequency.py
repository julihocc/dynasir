"""Weekly incidence stays on the weekly index (#177)."""

import warnings

import numpy as np
import pandas as pd

from dynasir import DataContainer, Model
from dynasir.data.preprocessing import preprocess_data


def _weekly_incidence(periods: int = 30) -> pd.DataFrame:
    index = pd.date_range("2020-01-05", periods=periods, freq="W")
    return pd.DataFrame(
        {"I": np.full(periods, 10.0), "D": np.zeros(periods), "N": 1e6},
        index=index,
    )


def _mismatch_warnings(caught):
    return [
        str(item.message)
        for item in caught
        if "FREQUENCY MISMATCH" in str(item.message)
    ]


class TestWeeklyNativeFrequency:
    """The issue reproduction: 30 weeks of 10 cases must not become ~204 daily rows."""

    def test_explicit_weekly_frequency_keeps_native_index(self):
        raw = _weekly_incidence()

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            container = DataContainer(
                raw, mode="incidence", frequency="W", window=1
            )

        assert _mismatch_warnings(caught) == []
        assert container.frequency == "W"
        assert len(container.data) == 30
        assert container.data["C"].iloc[-1] == 300.0
        assert np.allclose(container.data["I"].to_numpy(), raw["I"].to_numpy())
        # Lag 2: the stock holds this week and the previous one.
        assert container.data["I_active"].iloc[0] == 10.0
        assert container.data["I_active"].iloc[1:].eq(20.0).all()
        steps = container.data.index.to_series().diff().dropna()
        assert steps.median() == pd.Timedelta(days=7)
        # I.shift(2).cumsum() on a constant 10: the last row has 28 recovered cases.
        assert container.data["R"].iloc[-1] == 280.0

    def test_auto_detected_weekly_frequency_keeps_native_index(self):
        raw = _weekly_incidence()

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            container = DataContainer(raw, mode="incidence", window=1)

        assert _mismatch_warnings(caught) == []
        assert container.frequency == "W"
        assert len(container.data) == 30
        assert container.data["C"].iloc[-1] == raw["I"].sum()

    def test_model_keeps_weekly_index(self):
        raw = _weekly_incidence()
        container = DataContainer(raw, mode="incidence", frequency="W", window=1)
        model = Model(container)
        assert len(model.data) == 30
        assert model.data.index.to_series().diff().dropna().median() == pd.Timedelta(
            days=7
        )

    def test_weekly_fit_skips_the_two_week_warmup(self):
        raw = _weekly_incidence()
        container = DataContainer(raw, mode="incidence", frequency="W", window=1)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = Model(container)

        # 30 rows, drop the 2-week warm-up and the last out-of-sample row.
        assert len(model.logit_ratios_values) == 27
        assert model.fit_index[0] > raw.index[1]
        assert any("warm-up" in str(item.message) for item in caught)

    def test_daily_frequency_still_fills_gaps(self):
        index = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-04"])
        raw = pd.DataFrame({"I": [1.0, 2.0, 4.0]}, index=index)

        processed = preprocess_data(raw, window=1, frequency="D")

        assert len(processed) == 4
        assert processed.index.freqstr == "D"
        assert processed["I"].iloc[2] == 2.0
