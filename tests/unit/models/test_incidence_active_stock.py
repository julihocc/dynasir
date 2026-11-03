"""Incidence data with a recovery lag above one period (#178).

``I`` is the period incidence in the input and in the results; ``I_active``
is the active-infection stock (cases of the last recovery-lag periods).
"""

import warnings

import numpy as np
import pandas as pd
import pytest

from dynasir import ACTIVE_INFECTIONS, COMPARTMENTS, RESULT_COMPARTMENTS
from dynasir import DataContainer, Model
from dynasir.core.constants import FORECASTING_LEVELS
from dynasir.models.simulation import EpidemicSimulation

LAG = 14  # daily recovery lag


def _daily(n=150, seed=0, vaccination=False, zeros=None):
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    cases = rng.poisson(500 * np.exp(-0.5 * ((t - 70) / 18) ** 2) + 20).astype(float)
    if zeros is not None:
        cases[zeros] = 0.0
    df = pd.DataFrame(
        {"I": cases, "D": np.cumsum(0.003 * cases), "N": 1e6},
        index=pd.date_range("2021-01-01", periods=n, freq="D"),
    )
    if vaccination:
        df["V"] = np.cumsum(np.full(n, 500.0))
    return df


def _container(df, window=1, **kwargs):
    return DataContainer(df, mode="incidence", frequency="D", window=window, **kwargs)


class TestCompartments:
    def test_stock_and_conservation(self):
        df = _daily()
        data = _container(df).data
        lagged = data["C"].shift(LAG).fillna(0)

        np.testing.assert_allclose(data["I"], df["I"])
        np.testing.assert_allclose(data["C"], df["I"].cumsum())
        np.testing.assert_allclose(data[ACTIVE_INFECTIONS], data["C"] - lagged)
        np.testing.assert_allclose(data["R"], lagged - data["D"])
        np.testing.assert_allclose(data["A"], data["S"] + data[ACTIVE_INFECTIONS])
        np.testing.assert_allclose(
            data["C"], data[ACTIVE_INFECTIONS] + data["R"] + data["D"]
        )

    def test_infection_rate_is_not_saturated(self):
        data = _container(_daily()).data
        clipped = (data["alpha"] >= 1 - 1e-9).mean()
        assert clipped < 0.05

    def test_rates_match_cumulative_mode(self):
        df = _daily()
        incidence = _container(df).data
        cumulative = DataContainer(
            pd.DataFrame({"C": df["I"].cumsum(), "D": df["D"], "N": df["N"]}),
            frequency="D",
            window=1,
        ).data
        for column in ("alpha", "beta", "gamma", "logit_alpha", "logit_beta"):
            np.testing.assert_allclose(incidence[column], cumulative[column])
        np.testing.assert_allclose(incidence[ACTIVE_INFECTIONS], cumulative["I"])

    def test_weekly_stock_spans_two_weeks(self):
        idx = pd.date_range("2021-01-04", periods=60, freq="W-MON")
        cases = np.random.default_rng(1).poisson(80, 60).astype(float)
        df = pd.DataFrame(
            {"I": cases, "D": np.cumsum(0.003 * cases), "N": 1e6}, index=idx
        )
        data = DataContainer(df, mode="incidence", frequency="W", window=1).data
        np.testing.assert_allclose(
            data[ACTIVE_INFECTIONS], data["I"] + data["I"].shift(1).fillna(0)
        )

    def test_annual_cohorts_have_stock_equal_to_incidence(self):
        idx = pd.date_range("1990-12-31", periods=30, freq="YE")
        cases = np.random.default_rng(2).poisson(200, 30).astype(float) + 1
        df = pd.DataFrame(
            {"I": cases, "D": np.cumsum(0.002 * cases), "N": 1e7}, index=idx
        )
        data = DataContainer(df, mode="incidence", frequency="YE").data
        np.testing.assert_allclose(data[ACTIVE_INFECTIONS], data["I"])


class TestReplay:
    @pytest.mark.parametrize("window", [1, 7])
    def test_historical_rates_reproduce_history(self, window):
        data = _container(_daily(), window=window).data
        k, n = 30, 20
        history = data.iloc[: k + 1]
        dates = data.index[k + 1 : k + 1 + n]
        box = {
            rate: pd.DataFrame(
                {
                    level: data[rate].iloc[k : k + n].to_numpy()
                    for level in FORECASTING_LEVELS
                },
                index=dates,
            )
            for rate in ("alpha", "beta", "gamma")
        }
        sim = EpidemicSimulation(history, box, dates).simulate_for_given_levels(
            ("point", "point", "point")
        )

        for column in ("I", ACTIVE_INFECTIONS, "C", "D", "R", "S"):
            np.testing.assert_allclose(
                sim[column], data.loc[dates, column], rtol=1e-9, err_msg=column
            )


def _run(container, start=None, stop=None, steps=7):
    model = Model(container, start=start, stop=stop)
    model.create_model()
    model.fit_model()
    model.forecast(steps=steps)
    model.run_simulations()
    model.generate_result()
    return model


def _scenarios(model):
    def walk(node):
        if isinstance(node, pd.DataFrame):
            yield node
        else:
            for child in node.values():
                yield from walk(child)

    return list(walk(model.simulation_engine.simulation))


class TestForecast:
    def test_forecast_reports_incidence_and_stock(self):
        model = _run(_container(_daily()), start="2021-01-15", stop="2021-04-30")
        last = model.data.iloc[-1]

        assert ACTIVE_INFECTIONS in model.results and "I" in model.results
        for sim in _scenarios(model):
            # C grows by the period's new cases from the first step on
            np.testing.assert_allclose(sim["C"].iloc[0] - last["C"], sim["I"].iloc[0])
            assert (np.diff(np.r_[last["C"], sim["C"].to_numpy()]) >= 0).all()
            np.testing.assert_allclose(
                sim["C"], sim[ACTIVE_INFECTIONS] + sim["R"] + sim["D"]
            )
            np.testing.assert_allclose(sim["A"], sim["S"] + sim[ACTIVE_INFECTIONS])

    def test_forecast_incidence_is_on_incidence_scale(self):
        df = _daily()
        model = _run(_container(df), start="2021-01-15", stop="2021-04-30")
        median = model.results["I"]["median"].iloc[0]
        observed = df.loc["2021-04-30", "I"]
        assert 0.5 * observed < median < 2 * observed

    def test_vaccination_conserves_population(self):
        model = _run(
            _container(_daily(vaccination=True)), start="2021-01-15", stop="2021-04-30"
        )
        for sim in _scenarios(model)[:5]:
            np.testing.assert_allclose(
                sim["C"], sim[ACTIVE_INFECTIONS] + sim["R"] + sim["D"]
            )
            assert "V" in sim

    def test_cumulative_results_have_no_stock_column(self, sample_data_container):
        model = _run(sample_data_container, steps=3)
        assert ACTIVE_INFECTIONS not in model.results

    def test_backtest_ignores_later_data(self):
        df = _daily()
        stop = "2021-04-30"
        full = Model(_container(df), start="2021-01-15", stop=stop)
        cut = Model(_container(df.loc[:stop]), start="2021-01-15", stop=stop)
        np.testing.assert_allclose(full.logit_ratios_values, cut.logit_ratios_values)


class TestZeroCases:
    def test_isolated_zero_days_do_not_warn(self):
        # The 14-day stock never reaches zero, so no rate is undefined
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            container = _container(_daily(zeros=[40, 41, 42, 90, 91]))
        assert container.data.attrs["n_filled_rates"] == 0

    def test_zero_stock_warns(self):
        zeros = list(range(100, 130))
        with pytest.warns(UserWarning, match="I_active is zero"):
            _container(_daily(zeros=zeros))


def test_result_compartments():
    assert ACTIVE_INFECTIONS in RESULT_COMPARTMENTS
    assert ACTIVE_INFECTIONS not in COMPARTMENTS
