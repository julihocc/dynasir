"""Weekly and business-day data stay at their native frequency (#177)."""

import warnings

import numpy as np
import pandas as pd
import pytest

from dynasir import DataContainer, Model
from dynasir.data.frequency_handlers import (
    base_frequency_code,
    detect_frequency_from_index,
)


def _epidemic_curve(n, peak, width, height, seed):
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    return rng.poisson(height * np.exp(-0.5 * ((t - peak) / width) ** 2) + 5).astype(
        float
    )


def _weekly_incidence(n=80, freq="W-MON", seed=0):
    idx = pd.date_range("2020-01-06", periods=n, freq=freq)
    cases = _epidemic_curve(n, peak=40, width=8, height=400, seed=seed)
    return pd.DataFrame(
        {"I": cases, "D": np.cumsum(0.003 * cases), "N": 1e6}, index=idx
    )


def _cumulative(index, seed=0):
    cases = _epidemic_curve(
        len(index), peak=len(index) / 2, width=10, height=300, seed=seed
    )
    return pd.DataFrame(
        {"C": np.cumsum(cases) + 50, "D": np.cumsum(0.01 * cases) + 1, "N": 1e6},
        index=index,
    )


class TestDetection:
    @pytest.mark.parametrize("day", ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"])
    def test_any_weekly_anchor_is_weekly(self, day):
        idx = pd.date_range("2021-01-01", periods=30, freq=f"W-{day}")
        assert detect_frequency_from_index(idx) == "W"

    @pytest.mark.parametrize(
        "freq, expected", [("B", "B"), ("MS", "ME"), ("ME", "ME"), ("YE", "YE")]
    )
    def test_other_frequencies(self, freq, expected):
        idx = pd.date_range("2001-01-01", periods=30, freq=freq)
        assert detect_frequency_from_index(idx) == expected

    @pytest.mark.parametrize(
        "freq, expected",
        [("W-MON", "W"), ("QS-OCT", "QE"), ("YE-DEC", "YE"), ("BME", "ME"), (None, None)],
    )
    def test_base_frequency_code_ignores_anchor(self, freq, expected):
        assert base_frequency_code(freq) == expected


class TestWeeklyContainer:
    def test_incidence_is_not_repeated_on_daily_rows(self):
        df = _weekly_incidence()
        container = DataContainer(df, mode="incidence", frequency="W", window=1)

        assert len(container.data) == len(df)
        assert (container.data.index == df.index).all()
        np.testing.assert_allclose(container.data["C"].iloc[-1], df["I"].sum())

    def test_cumulative_uses_two_week_lag(self):
        idx = pd.date_range("2020-01-06", periods=60, freq="W-MON")
        df = _cumulative(idx)
        data = DataContainer(df, frequency="W", window=1).data
        np.testing.assert_allclose(data["R"], data["C"].shift(2).fillna(0) - data["D"])

    def test_weekly_window_capped_at_three(self):
        with pytest.warns(UserWarning, match="smoothing window is 3"):
            container = DataContainer(
                _weekly_incidence(), mode="incidence", frequency="W", window=7
            )
        assert len(container.data) == 80 - 3

    def test_auto_detected_monday_weeks(self):
        container = DataContainer(_weekly_incidence(), mode="incidence", window=1)
        assert container.frequency == "W"


def _fit(container, start=None, stop=None, steps=4):
    model = Model(container, start=start, stop=stop)
    model.create_model()
    model.fit_model()
    model.forecast(steps=steps)
    model.run_simulations()
    model.generate_result()
    return model


class TestWeeklyModel:
    def test_model_keeps_weekly_rows_and_anchor(self):
        idx = pd.date_range("2020-01-06", periods=80, freq="W-MON")
        container = DataContainer(_cumulative(idx), frequency="W", window=1)
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            # The recovery-lag warm-up note (#184) is expected
            warnings.filterwarnings("ignore", message=".*recovery-lag warm-up")
            model = _fit(container)

        assert len(model.data) == len(container.data)
        forecast_index = model.forecasting_interval
        assert (forecast_index.dayofweek == 0).all()
        assert forecast_index[0] == model.data.index[-1] + pd.Timedelta(days=7)
        assert (np.diff(forecast_index.values) == np.timedelta64(7, "D")).all()

    def test_aggregate_to_weekly_keeps_anchor(self):
        idx = pd.date_range("2020-01-06", periods=80, freq="W-MON")
        model = _fit(DataContainer(_cumulative(idx), frequency="W", window=1))
        weekly = model.aggregate_forecast(
            "C", target_frequency="W", aggregate_func="last"
        )
        assert (weekly.index == model.results["C"].index).all()

    def test_backtest_matches_truncated_data(self):
        df = _weekly_incidence()
        stop = df.index[60]
        full = Model(
            DataContainer(df, mode="incidence", frequency="W", window=1), stop=stop
        )
        cut = Model(
            DataContainer(df.loc[:stop], mode="incidence", frequency="W", window=1),
            stop=stop,
        )
        np.testing.assert_allclose(full.logit_ratios_values, cut.logit_ratios_values)


class TestBusinessDayModel:
    def test_model_keeps_business_days(self):
        idx = pd.bdate_range("2021-01-04", periods=120)
        container = DataContainer(_cumulative(idx), frequency="B", window=1)
        model = _fit(container)

        assert len(model.data) == len(container.data)
        assert (model.data.index.dayofweek < 5).all()
        assert (model.forecasting_interval.dayofweek < 5).all()
