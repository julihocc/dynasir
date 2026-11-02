"""Period-cohort incidence semantics and training/forecast alignment.

Covers #162 (constant alpha), #163 (R0 tracked I_t / I_(t+1)), #164 (leakage
from data after ``stop``), #165 (zero-width first forecast step) and #166
(simulated I was a stock rather than period incidence).
"""

import numpy as np
import pandas as pd
import pytest

from dynasir import DataContainer, Model
from dynasir.core.constants import FORECASTING_LEVELS
from dynasir.models.simulation import EpidemicSimulation


def _annual_incidence(seed=0, periods=45, vaccination=False):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("1980-12-31", periods=periods, freq="YE")
    incidence = 1.0 + np.round(np.exp(rng.normal(4, 1.5, len(idx))))
    data = pd.DataFrame(
        {"I": incidence, "D": np.cumsum(0.002 * incidence), "N": 38e6}, index=idx
    )
    if vaccination:
        data["V"] = np.cumsum(np.full(len(idx), 1e5))
    return data


def _run(container, start, stop, steps=3):
    model = Model(container, start=start, stop=stop)
    model.create_model()
    model.fit_model()
    model.forecast(steps=steps)
    model.run_simulations(n_jobs=1)
    model.generate_result()
    return model


class TestCohortRates:
    def test_alpha_varies_and_tracks_growth(self):
        df = _annual_incidence()
        data = DataContainer(df, mode="incidence", frequency="YE").data

        # #162: alpha is no longer clipped to a constant
        assert data["alpha"].round(12).nunique() > 1
        growth = df["I"].shift(-1) / df["I"]
        expected = data["A"] * growth / data["S"]
        np.testing.assert_allclose(data["alpha"].iloc[:-1], expected.iloc[:-1])

    def test_r0_rises_before_outbreaks(self):
        df = _annual_incidence()
        model = Model(
            DataContainer(df, mode="incidence", frequency="YE"),
            start="1980-12-31",
            stop="2024-12-31",
        )
        r0 = model.calculate_R0()
        growth = (df["I"].shift(-1) / df["I"]).loc[r0.index]
        decline = (df["I"] / df["I"].shift(-1)).loc[r0.index]

        # #163: R0 now moves with I_(t+1)/I_t, not with I_t/I_(t+1)
        assert r0.corr(growth, method="spearman") > 0.99
        assert r0.corr(decline, method="spearman") < -0.99
        assert ((r0 > 1) == (growth > 1)).all()

    def test_beta_is_rest_of_cohort(self):
        data = DataContainer(_annual_incidence(), mode="incidence", frequency="YE").data
        np.testing.assert_allclose(data["beta"] + data["gamma"], 1.0)
        assert "log_alpha" in data and "logit_gamma" in data
        assert "logit_alpha" not in data and "logit_beta" not in data

    def test_monthly_incidence_uses_cohorts(self):
        idx = pd.date_range("2015-01-31", periods=60, freq="ME")
        rng = np.random.default_rng(1)
        incidence = 1.0 + np.round(np.exp(rng.normal(3, 1, len(idx))))
        df = pd.DataFrame(
            {"I": incidence, "D": np.cumsum(0.002 * incidence), "N": 1e7}, index=idx
        )
        data = DataContainer(df, mode="incidence", frequency="ME").data
        assert "log_alpha" in data

    def test_cumulative_mode_unchanged(self, sample_data_container):
        assert "logit_alpha" in sample_data_container.data
        assert "log_alpha" not in sample_data_container.data


class TestNoLeakage:
    def test_incidence_backtest_ignores_later_data(self):
        df = _annual_incidence()
        stop = "2010-12-31"
        full = _run(
            DataContainer(df, mode="incidence", frequency="YE"), df.index[0], stop
        )
        cut = _run(
            DataContainer(df.loc[:stop], mode="incidence", frequency="YE"),
            df.index[0],
            stop,
        )

        pd.testing.assert_frame_equal(full.results["I"], cut.results["I"])
        for rate in ("alpha", "beta", "gamma"):
            pd.testing.assert_frame_equal(
                full.forecasting_box[rate], cut.forecasting_box[rate]
            )

    def test_cumulative_backtest_ignores_later_data(self):
        idx = pd.date_range("2020-03-01", periods=120, freq="D")
        rng = np.random.default_rng(7)
        df = pd.DataFrame(
            {
                "C": np.cumsum(rng.exponential(50, len(idx))) + 100,
                "D": np.cumsum(rng.exponential(1, len(idx))) + 1,
                "N": 1_000_000,
            },
            index=idx,
        )
        full_container = DataContainer(df)
        start = full_container.data.index[0]
        stop = idx[90]
        full = Model(full_container, start=start, stop=stop)
        cut = Model(DataContainer(df.loc[:stop]), start=start, stop=stop)

        np.testing.assert_allclose(full.logit_ratios_values, cut.logit_ratios_values)

    def test_last_training_row_is_not_fitted(self):
        df = _annual_incidence()
        model = Model(
            DataContainer(df, mode="incidence", frequency="YE"),
            start="1980-12-31",
            stop="2010-12-31",
        )
        assert len(model.logit_ratios_values) == len(model.data) - 1
        expected = model.data[model.active_logit_ratios].values[:-1]
        np.testing.assert_allclose(model.logit_ratios_values, expected)


class TestFirstStep:
    def test_first_step_scenarios_differ(self):
        df = _annual_incidence()
        model = _run(
            DataContainer(df, mode="incidence", frequency="YE"),
            "1980-12-31",
            "2010-12-31",
        )
        scenarios = model.results["I"].drop(
            columns=["mean", "median", "gmean", "hmean"]
        )
        width = scenarios.max(axis=1) - scenarios.min(axis=1)

        # #165: the first forecast rate drives the first step
        assert width.iloc[0] > 0

    def test_first_step_uses_first_forecast_rate(self, sample_data_container):
        model = Model(sample_data_container)
        model.create_model()
        model.fit_model(max_lag=1)
        model.forecast(steps=3)
        model.run_simulations(n_jobs=1)
        model.generate_result()

        sim = model.simulation_engine.simulation["upper"]["point"]["point"]
        np.testing.assert_allclose(
            sim["alpha"].values,
            model.forecasting_box["alpha"]["upper"].values,
        )


class TestCohortSimulation:
    def _replay(self, df, k, n):
        """Simulate n steps from period k with the historical rates."""
        data = DataContainer(df, mode="incidence", frequency="YE").data
        history = data.iloc[: k + 1]
        dates = data.index[k + 1 : k + 1 + n]
        box = {}
        for rate in ("alpha", "beta", "gamma", "delta"):
            if rate in data:
                values = data[rate].iloc[k : k + n].to_numpy()
                box[rate] = pd.DataFrame(
                    {level: values for level in FORECASTING_LEVELS}, index=dates
                )
        sim = EpidemicSimulation(history, box, dates)
        levels = ("point",) * len(box)
        return data, sim.simulate_for_given_levels(levels), dates

    def test_replay_reproduces_incidence(self):
        df = _annual_incidence()
        data, sim, dates = self._replay(df, k=20, n=5)

        # #166: simulated I is the incidence of each period
        np.testing.assert_allclose(sim["I"], data.loc[dates, "I"], rtol=1e-9)
        np.testing.assert_allclose(sim["C"], data.loc[dates, "C"], rtol=1e-9)
        np.testing.assert_allclose(sim["D"], data.loc[dates, "D"], rtol=1e-6)

    @pytest.mark.parametrize("vaccination", [False, True])
    def test_forecast_conserves_population(self, vaccination):
        df = _annual_incidence(vaccination=vaccination)
        model = _run(
            DataContainer(df, mode="incidence", frequency="YE"),
            "1980-12-31",
            "2010-12-31",
        )
        assert model.simulation_engine.cohort
        node = model.simulation_engine.simulation
        while not isinstance(node, pd.DataFrame):
            node = node["point"]
        np.testing.assert_allclose(node["C"], node["I"] + node["R"] + node["D"])
        np.testing.assert_allclose(node["A"], node["S"] + node["I"])
        assert (node["I"] >= 0).all()


class TestCohortForecastR0:
    def test_forecast_r0_equals_alpha_in_every_scenario(self):
        df = _annual_incidence()
        model = Model(
            DataContainer(df, mode="incidence", frequency="YE"),
            start="1980-12-31",
            stop="2010-12-31",
        )
        model.create_model()
        model.fit_model()
        model.forecast(steps=3)
        r0 = model.forecast_R0()

        for level in FORECASTING_LEVELS:
            alpha = model.forecasting_box["alpha"][level]
            for column in [c for c in r0.columns if c.startswith(f"{level}|")]:
                np.testing.assert_allclose(r0[column], alpha)

    def test_beta_level_does_not_change_cohort_simulation(self):
        df = _annual_incidence()
        model = _run(
            DataContainer(df, mode="incidence", frequency="YE"),
            "1980-12-31",
            "2010-12-31",
        )
        sim = model.simulation_engine.simulation
        for beta_level in ("lower", "upper"):
            np.testing.assert_allclose(
                sim["point"][beta_level]["point"]["I"],
                sim["point"]["point"]["point"]["I"],
            )
