"""Tests for VAR forecast level order, constant rate columns and the default interval level.

Covers #175 (lower and point swapped), #168 (constant columns made the VAR
covariance singular) and #170 (FORECASTER_ALPHA was never used).
"""

import logging

import numpy as np
import pandas as pd
import pytest

from dynasir import DataContainer, Model
from dynasir.core.config import get_settings
from dynasir.epydemics import DataContainer as LegacyDataContainer
from dynasir.epydemics import Model as LegacyModel
from dynasir.models.forecasting.var import VARForecaster


def _var_series(n=80, k=3, seed=0):
    rng = np.random.default_rng(seed)
    y = np.zeros((n, k))
    for t in range(1, n):
        y[t] = 0.6 * y[t - 1] + rng.normal(0, 1, k)
    return y


def _annual_incidence(seed=0, periods=45):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("1980-12-31", periods=periods, freq="YE")
    incidence = 1.0 + np.round(np.exp(rng.normal(4, 1.5, len(idx))))
    return pd.DataFrame(
        {"I": incidence, "D": np.cumsum(0.002 * incidence), "N": 38e6}, index=idx
    )


def _assert_ordered(lower, point, upper):
    assert np.all(lower <= point)
    assert np.all(point <= upper)


class TestLevelOrder:
    def test_var_backend_returns_lower_point_upper(self):
        forecaster = VARForecaster(_var_series())
        forecaster.create_model()
        forecaster.fit(max_lag=2, ic="aic")
        lower, point, upper = forecaster.forecast_interval(5)

        assert lower.shape == point.shape == upper.shape == (5, 3)
        assert np.all(lower < point)
        assert np.all(point < upper)

    def test_forecasting_box_levels_are_ordered(self, sample_data_container):
        model = Model(sample_data_container)
        model.create_model()
        model.fit_model(max_lag=3)
        model.forecast(steps=5)

        for rate in ("logit_alpha", "logit_beta", "logit_gamma", "alpha", "beta"):
            box = model.forecasting_box[rate]
            _assert_ordered(box["lower"], box["point"], box["upper"])

    def test_legacy_model_box_uses_each_rate_forecast(self):
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
        container = LegacyDataContainer(data)
        index = container.data.index
        model = LegacyModel(container, start=index[5], stop=index[40])
        model.create_logit_ratios_model()
        model.fit_logit_ratios_model(maxlags=2)
        model.forecast_logit_ratios(steps=3)

        point, lower, upper = model.forecasted_logit_ratios_tuple_arrays
        for i, ratio in enumerate(("logit_alpha", "logit_beta", "logit_gamma")):
            box = model.forecasting_box[ratio]
            np.testing.assert_allclose(box["point"], point[:, i])
            np.testing.assert_allclose(box["lower"], lower[:, i])
            np.testing.assert_allclose(box["upper"], upper[:, i])


class TestConstantColumns:
    def test_zero_deaths_fit_without_linalg_error(self, caplog):
        # Repro from #168: D all zero makes gamma constant.
        df = _annual_incidence().assign(D=0.0)
        model = Model(
            DataContainer(df, mode="incidence", frequency="YE"),
            start="1980-12-31",
            stop="2024-12-31",
        )
        model.create_model()
        with caplog.at_level(logging.WARNING):
            model.fit_model()
        model.forecast(steps=3)

        assert "logit_gamma" in caplog.text
        assert "'D' may be all zero" in caplog.text
        gamma = model.forecasting_box["logit_gamma"]
        np.testing.assert_allclose(gamma["lower"], gamma["upper"])
        assert np.ptp(gamma["point"].to_numpy()) == 0

    def test_single_varying_column_uses_autoreg(self):
        y = _var_series(k=1)
        data = np.column_stack([np.full(len(y), 2.0), y[:, 0], np.full(len(y), -1.0)])
        forecaster = VARForecaster(data)
        forecaster.create_model()
        forecaster.fit(max_lag=3, ic="aic")
        lower, point, upper = forecaster.forecast_interval(4)

        assert forecaster.model is None
        assert hasattr(forecaster.fitted_model, "results")
        np.testing.assert_allclose(point[:, 0], 2.0)
        np.testing.assert_allclose(point[:, 2], -1.0)
        np.testing.assert_allclose(lower[:, [0, 2]], upper[:, [0, 2]])
        assert np.all(lower[:, 1] < point[:, 1])
        assert np.all(point[:, 1] < upper[:, 1])

    def test_all_constant_columns_repeat_constants(self):
        data = np.tile([0.5, -2.0, 3.0], (20, 1))
        forecaster = VARForecaster(data)
        forecaster.create_model()
        forecaster.fit(max_lag=2, ic="aic")
        lower, point, upper = forecaster.forecast_interval(3)

        assert forecaster.k_ar == 0
        for arr in (lower, point, upper):
            np.testing.assert_allclose(arr, np.tile([0.5, -2.0, 3.0], (3, 1)))

    def test_constant_column_with_var_on_the_rest(self):
        y = _var_series(k=2)
        data = np.column_stack([y[:, 0], np.full(len(y), 7.0), y[:, 1]])
        forecaster = VARForecaster(data)
        forecaster.create_model()
        forecaster.fit(max_lag=2, ic="aic")
        lower, point, upper = forecaster.forecast_interval(5)

        np.testing.assert_allclose(point[:, 1], 7.0)
        np.testing.assert_allclose(lower[:, 1], upper[:, 1])
        assert np.all(lower[:, [0, 2]] < upper[:, [0, 2]])

    def test_var_with_zero_lags_forecasts_intercept(self):
        rng = np.random.default_rng(3)
        data = rng.normal([1.0, -1.0], 0.5, size=(40, 2))
        forecaster = VARForecaster(data)
        forecaster.create_model()
        forecaster.fit(0)
        lower, point, upper = forecaster.forecast_interval(3, alpha=0.05)

        assert forecaster.k_ar == 0
        np.testing.assert_allclose(point, np.tile(data.mean(axis=0), (3, 1)))
        assert np.all(lower < point)
        assert np.all(point < upper)


class TestForecasterAlphaSetting:
    def _band_width(self, container):
        model = Model(container)
        model.create_model()
        model.fit_model(max_lag=3)
        model.forecast(steps=5)
        box = model.forecasting_box["logit_beta"]
        return float((box["upper"] - box["lower"]).mean())

    def test_setting_changes_default_interval(self, sample_data_container, monkeypatch):
        default_width = self._band_width(sample_data_container)

        monkeypatch.setenv("FORECASTER_ALPHA", "0.5")
        get_settings.cache_clear()
        try:
            narrow_width = self._band_width(sample_data_container)
        finally:
            monkeypatch.delenv("FORECASTER_ALPHA")
            get_settings.cache_clear()

        assert narrow_width < default_width

    def test_explicit_alpha_overrides_setting(self, sample_data_container):
        model = Model(sample_data_container)
        model.create_model()
        model.fit_model(max_lag=3)
        model.forecast(steps=5)
        default = model.forecasting_box["logit_beta"].copy()
        model.forecast(steps=5, alpha=0.5)
        narrow = model.forecasting_box["logit_beta"]

        assert (
            (narrow["upper"] - narrow["lower"]) < (default["upper"] - default["lower"])
        ).all()
