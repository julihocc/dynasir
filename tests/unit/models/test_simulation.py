"""
Unit tests for the EpidemicSimulation class.
"""

import itertools
import logging

import numpy as np
import pandas as pd
import pytest

from dynasir.data import DataContainer
from dynasir.models.simulation import EpidemicSimulation
from dynasir.models.var_forecasting import VARForecasting


class TestEpidemicSimulation:
    """Test EpidemicSimulation class functionality."""

    @pytest.fixture
    def sample_data_container(self):
        """Create sample DataContainer for testing."""
        dates = pd.date_range("2020-01-01", periods=50, freq="D")
        sample_data = pd.DataFrame(
            {
                "C": np.cumsum(np.random.poisson(10, 50)) + 100,
                "D": np.cumsum(np.random.poisson(1, 50)) + 1,
                "N": [1000000] * 50,
            },
            index=dates,
        )
        return DataContainer(sample_data, window=7)

    @pytest.fixture
    def setup_simulation_data(self, sample_data_container):
        """Set up data required for EpidemicSimulation."""
        data = sample_data_container.data
        active_logit_ratios = ["logit_alpha", "logit_beta", "logit_gamma"]
        logit_ratios_values = data[active_logit_ratios].values
        window = sample_data_container.window

        var_forecasting = VARForecasting(
            data, logit_ratios_values, window, active_logit_ratios
        )
        var_forecasting.create_logit_ratios_model()
        var_forecasting.fit_logit_ratios_model()
        var_forecasting.forecast_logit_ratios(steps=5)

        forecasting_box = var_forecasting.forecasting_box
        forecasting_interval = var_forecasting.forecasting_interval

        return data, forecasting_box, forecasting_interval

    @pytest.fixture
    def epidemic_simulation_instance(self, setup_simulation_data):
        """Create an EpidemicSimulation instance for testing."""
        data, forecasting_box, forecasting_interval = setup_simulation_data
        return EpidemicSimulation(data, forecasting_box, forecasting_interval)

    def test_epidemic_simulation_init(self, epidemic_simulation_instance):
        """Test EpidemicSimulation initialization."""
        assert epidemic_simulation_instance.data is not None
        assert epidemic_simulation_instance.forecasting_box is not None
        assert epidemic_simulation_instance.forecasting_interval is not None
        assert epidemic_simulation_instance.simulation is None
        assert epidemic_simulation_instance.results is None

    def test_create_simulation_box(self, epidemic_simulation_instance):
        """Test simulation box structure creation."""
        epidemic_simulation_instance.create_simulation_box()
        simulation = epidemic_simulation_instance.simulation
        assert simulation is not None

        levels = ["lower", "point", "upper"]
        for alpha_level in levels:
            assert alpha_level in simulation
            for beta_level in levels:
                assert beta_level in simulation[alpha_level]
                for gamma_level in levels:
                    assert gamma_level in simulation[alpha_level][beta_level]

    def test_simulate_for_given_levels(self, epidemic_simulation_instance):
        """Test individual simulation scenario."""
        simulation_levels = ["point", "point", "point"]
        result = epidemic_simulation_instance.simulate_for_given_levels(
            simulation_levels
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(epidemic_simulation_instance.forecasting_interval)

        sird_cols = ["S", "I", "R", "D", "C", "A"]
        for col in sird_cols:
            assert col in result.columns
        rate_cols = ["alpha", "beta", "gamma"]
        for col in rate_cols:
            assert col in result.columns

    def test_simulation_conservation_laws(self, epidemic_simulation_instance):
        """Test that SIRD simulation respects conservation laws."""
        simulation_levels = ["point", "point", "point"]
        result = epidemic_simulation_instance.simulate_for_given_levels(
            simulation_levels
        )

        for idx in result.index:
            row = result.loc[idx]
            assert np.isclose(row["S"] + row["I"], row["A"])
            assert np.isclose(row["C"], row["I"] + row["R"] + row["D"])

    @pytest.mark.slow
    def test_run_simulations(self, epidemic_simulation_instance):
        """Test running all 27 simulation scenarios."""
        epidemic_simulation_instance.run_simulations()
        simulation = epidemic_simulation_instance.simulation
        levels = ["lower", "point", "upper"]

        count = 0
        for alpha_level in levels:
            for beta_level in levels:
                for gamma_level in levels:
                    scenario = simulation[alpha_level][beta_level][gamma_level]
                    assert scenario is not None
                    assert isinstance(scenario, pd.DataFrame)
                    count += 1
        assert count == 27

    @pytest.mark.slow
    def test_create_results_dataframe(self, epidemic_simulation_instance):
        """Test results dataframe creation for specific compartment."""
        epidemic_simulation_instance.run_simulations()
        results_df = epidemic_simulation_instance.create_results_dataframe("C")

        assert isinstance(results_df, pd.DataFrame)
        assert len(results_df) == len(epidemic_simulation_instance.forecasting_interval)

        expected_cols = 27 + 4
        assert len(results_df.columns) == expected_cols

        central_methods = ["mean", "median", "gmean", "hmean"]
        for method in central_methods:
            assert method in results_df.columns

    @pytest.mark.slow
    def test_generate_result(self, epidemic_simulation_instance):
        """Test complete results generation."""
        epidemic_simulation_instance.run_simulations()
        epidemic_simulation_instance.generate_result()
        results = epidemic_simulation_instance.results
        assert results is not None

        compartments = ["A", "C", "S", "I", "R", "D"]
        for compartment in compartments:
            assert compartment in results
            assert isinstance(results[compartment], pd.DataFrame)

    def test_warns_for_flat_median_incidence_forecast(self, caplog):
        """Warn when the median infected forecast is flat despite historical variation."""
        forecast_index = pd.date_range("2020-12-31", periods=2, freq="YE")
        historical = pd.DataFrame(
            {
                "A": [100.0, 100.0],
                "C": [1.0, 3.0],
                "S": [99.0, 97.0],
                "I": [1.0, 3.0],
                "R": [0.0, 0.0],
                "D": [0.0, 0.0],
                "alpha": [0.0, 0.0],
                "beta": [0.0, 0.0],
                "gamma": [0.0, 0.0],
            },
            index=pd.date_range("2018-12-31", periods=2, freq="YE"),
        )
        forecast_rates = {
            rate: pd.DataFrame(
                0.0, index=forecast_index, columns=["lower", "point", "upper"]
            )
            for rate in ("alpha", "beta", "gamma")
        }
        simulation = EpidemicSimulation(historical, forecast_rates, forecast_index)

        simulation.run_simulations(n_jobs=1)
        with caplog.at_level(logging.WARNING):
            simulation.generate_result()

        assert "median infected forecast is flat across 2 periods" in caplog.text
