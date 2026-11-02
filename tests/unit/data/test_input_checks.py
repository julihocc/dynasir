"""Input checks and metrics: zero incidence (#167), frequency validation and
window overrides (#169), and MAPE/sMAPE with zero values (#171)."""

import warnings

import numpy as np
import pandas as pd
import pytest

from dynasir import DataContainer, Model
from dynasir.analysis.evaluation import evaluate_forecast


def _annual(cases, deaths=None, start="2000-12-31"):
    idx = pd.date_range(start, periods=len(cases), freq="YE")
    cases = np.asarray(cases, dtype=float)
    if deaths is None:
        deaths = np.cumsum(0.002 * cases)
    return pd.DataFrame({"I": cases, "D": deaths, "N": 1e7}, index=idx)


CASES = [120, 40, 0, 0, 15, 300, 80, 20, 5, 60, 90, 30]


class TestZeroIncidence:
    def test_zero_cases_warn_with_dates(self):
        with pytest.warns(UserWarning, match=r"I is zero in 2 period\(s\)") as record:
            DataContainer(_annual(CASES), mode="incidence", frequency="YE")
        message = str(record[0].message)
        assert "2002-12-31" in message and "2003-12-31" in message
        assert "incidence_offset" in message

    def test_offset_keeps_rates_defined(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            container = DataContainer(
                _annual(CASES), mode="incidence", frequency="YE", incidence_offset=1
            )
        data = container.data
        assert data.attrs["n_filled_rates"] == 0
        # alpha_t uses (I_(t+1) + 1) / (I_t + 1), so it is never clipped to ~0
        assert data["log_alpha"].iloc[:-1].min() > -10
        np.testing.assert_allclose(
            data["alpha"].iloc[1],
            data["A"].iloc[1] * (CASES[2] + 1) / ((CASES[1] + 1) * data["S"].iloc[1]),
        )
        # Compartments are unchanged by the offset
        np.testing.assert_allclose(data["I"], CASES)

    def test_negative_offset_rejected(self):
        with pytest.raises(ValueError, match="incidence_offset"):
            DataContainer(
                _annual(CASES), mode="incidence", frequency="YE", incidence_offset=-1
            )

    def test_model_rebuild_does_not_repeat_warning(self):
        with pytest.warns(UserWarning):
            container = DataContainer(_annual(CASES), mode="incidence", frequency="YE")
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            Model(container, start="2000-12-31", stop="2008-12-31")

    def test_offset_carried_into_training_container(self):
        container = DataContainer(
            _annual(CASES), mode="incidence", frequency="YE", incidence_offset=1
        )
        model = Model(container, start="2000-12-31", stop="2008-12-31")
        assert model.training_container.incidence_offset == 1


class TestFrequencyValidation:
    def test_short_annual_series_warns(self):
        with pytest.warns(UserWarning, match="at least 10 observations"):
            DataContainer(_annual([10, 20, 5, 8, 12]), mode="incidence", frequency="YE")

    def test_overridden_window_warns(self):
        with pytest.warns(UserWarning, match="window=3 is not used for annual data"):
            DataContainer(
                _annual([10 + i for i in range(12)]),
                mode="incidence",
                frequency="YE",
                window=3,
            )

    def test_default_window_does_not_warn(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            DataContainer(
                _annual([10 + i for i in range(12)]), mode="incidence", frequency="YE"
            )


def _evaluation(actual, forecast):
    idx = pd.date_range("2020-12-31", periods=len(actual), freq="YE")
    results = {
        "I": pd.DataFrame(
            {m: forecast for m in ("mean", "median", "gmean", "hmean")}, index=idx
        )
    }
    return evaluate_forecast(
        results, pd.DataFrame({"I": actual}, index=idx), compartment_codes=("I",)
    )["I"]["median"]


class TestPercentageErrors:
    def test_mape_skips_zero_actuals(self):
        with pytest.warns(UserWarning, match="MAPE skips 1 of 2"):
            metrics = _evaluation([0.0, 10.0], [1.0, 12.0])
        assert metrics["mape"] == pytest.approx(20.0)

    def test_mape_is_nan_when_all_actuals_zero(self):
        with pytest.warns(UserWarning):
            metrics = _evaluation([0.0, 0.0], [1.0, 2.0])
        assert np.isnan(metrics["mape"])

    def test_smape_standard_formula(self):
        metrics = _evaluation([0.0, 10.0], [0.0, 12.0])
        # 200 * mean(0, 2/22)
        assert metrics["smape"] == pytest.approx(200 * (2 / 22) / 2)

    def test_smape_bounded(self):
        metrics = _evaluation([0.0, 10.0], [5.0, 0.0])
        assert metrics["smape"] == pytest.approx(200.0)
