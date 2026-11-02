"""
Unit tests for SIRDV simulation engine.

This module tests the simulation engine's ability to handle vaccination
data and perform 81-scenario SIRDV simulations.
"""

import numpy as np
import pandas as pd
import pytest

from dynasir.core.constants import FORECASTING_LEVELS
from dynasir.models.simulation import EpidemicSimulation


@pytest.fixture
def sample_sird_data():
    """Sample SIRD historical data."""
    dates = pd.date_range("2020-01-01", periods=30, freq="D")
    np.random.seed(42)

    data = pd.DataFrame(
        {
            "S": 1000000 - np.cumsum(np.random.poisson(100, 30)),
            "I": np.random.poisson(500, 30),
            "R": np.cumsum(np.random.poisson(50, 30)),
            "D": np.cumsum(np.random.poisson(2, 30)),
            "C": np.cumsum(np.random.poisson(100, 30)),
            "A": 1000000 - np.cumsum(np.random.poisson(50, 30)),
            "alpha": np.random.uniform(0.1, 0.3, 30),
            "beta": np.random.uniform(0.05, 0.15, 30),
            "gamma": np.random.uniform(0.01, 0.03, 30),
        },
        index=dates,
    )
    return data


@pytest.fixture
def sample_sirdv_data():
    """Sample SIRDV historical data with vaccination."""
    dates = pd.date_range("2020-01-01", periods=30, freq="D")
    np.random.seed(42)

    # Add vaccination starting partway
    vaccinations = np.zeros(30)
    vaccinations[15:] = np.cumsum(np.random.exponential(5000, 15))

    data = pd.DataFrame(
        {
            "S": 1000000 - np.cumsum(np.random.poisson(100, 30)) - vaccinations,
            "I": np.random.poisson(500, 30),
            "R": np.cumsum(np.random.poisson(50, 30)),
            "D": np.cumsum(np.random.poisson(2, 30)),
            "V": vaccinations,
            "C": np.cumsum(np.random.poisson(100, 30)),
            "A": 1000000 - np.cumsum(np.random.poisson(50, 30)),
            "alpha": np.random.uniform(0.1, 0.3, 30),
            "beta": np.random.uniform(0.05, 0.15, 30),
            "gamma": np.random.uniform(0.01, 0.03, 30),
            "delta": np.concatenate([np.zeros(15), np.random.uniform(0.01, 0.05, 15)]),
        },
        index=dates,
    )
    return data


@pytest.fixture
def sird_forecasting_box():
    """Sample SIRD forecasting box (3 rates)."""
    dates = pd.date_range("2020-01-31", periods=10, freq="D")

    box = {}
    for rate in ["alpha", "beta", "gamma"]:
        box[rate] = pd.DataFrame(
            {
                "lower": np.random.uniform(0.05, 0.1, 10),
                "point": np.random.uniform(0.1, 0.2, 10),
                "upper": np.random.uniform(0.2, 0.3, 10),
            },
            index=dates,
        )
    return box


@pytest.fixture
def sirdv_forecasting_box():
    """Sample SIRDV forecasting box (4 rates)."""
    dates = pd.date_range("2020-01-31", periods=10, freq="D")

    box = {}
    for rate in ["alpha", "beta", "gamma", "delta"]:
        box[rate] = pd.DataFrame(
            {
                "lower": np.random.uniform(0.05, 0.1, 10),
                "point": np.random.uniform(0.1, 0.2, 10),
                "upper": np.random.uniform(0.2, 0.3, 10),
            },
            index=dates,
        )
    return box


class TestSIRDSimulation:
    """Test SIRD simulation (3-rate, 27 scenarios)."""

    def test_sird_simulation_init(self, sample_sird_data, sird_forecasting_box):
        """Test SIRD simulation initialization."""
        interval = pd.date_range("2020-01-31", periods=10, freq="D")
        sim = EpidemicSimulation(sample_sird_data, sird_forecasting_box, interval)

        assert not sim.has_vaccination
        assert sim.data is not None
        assert sim.forecasting_box is not None
        assert "delta" not in sim.forecasting_box

    def test_sird_simulate_single_scenario(
        self, sample_sird_data, sird_forecasting_box
    ):
        """Test single SIRD scenario simulation."""
        interval = pd.date_range("2020-01-31", periods=10, freq="D")
        sim = EpidemicSimulation(sample_sird_data, sird_forecasting_box, interval)

        result = sim.simulate_for_given_levels(("point", "point", "point"))

        # Check result structure
        assert len(result) == 10
        assert "S" in result.columns
        assert "I" in result.columns
        assert "R" in result.columns
        assert "D" in result.columns
        assert "C" in result.columns
        assert "A" in result.columns

        # V should NOT be in SIRD results
        assert "V" not in result.columns
        assert "delta" not in result.columns

        # Check rates are present
        assert "alpha" in result.columns
        assert "beta" in result.columns
        assert "gamma" in result.columns

    def test_sird_27_scenarios(self, sample_sird_data, sird_forecasting_box):
        """Test that SIRD generates 27 scenarios (3^3)."""
        interval = pd.date_range("2020-01-31", periods=10, freq="D")
        sim = EpidemicSimulation(sample_sird_data, sird_forecasting_box, interval)

        sim.run_simulations(n_jobs=1)

        # Count scenarios
        scenario_count = 0
        for alpha_level in FORECASTING_LEVELS:
            for beta_level in FORECASTING_LEVELS:
                for gamma_level in FORECASTING_LEVELS:
                    scenario = sim.simulation[alpha_level][beta_level][gamma_level]
                    assert scenario is not None
                    scenario_count += 1

        assert scenario_count == 27

    def test_sird_simulation_box_structure(
        self, sample_sird_data, sird_forecasting_box
    ):
        """Test SIRD simulation box has 3D structure."""
        interval = pd.date_range("2020-01-31", periods=10, freq="D")
        sim = EpidemicSimulation(sample_sird_data, sird_forecasting_box, interval)

        sim.create_simulation_box()

        # Verify 3D structure (not 4D)
        for alpha_level in FORECASTING_LEVELS:
            for beta_level in FORECASTING_LEVELS:
                for gamma_level in FORECASTING_LEVELS:
                    # This should work for SIRD
                    assert sim.simulation[alpha_level][beta_level][gamma_level] is None

                    # Accessing a 4th level should fail
                    with pytest.raises((KeyError, TypeError)):
                        _ = sim.simulation[alpha_level][beta_level][gamma_level][
                            "lower"
                        ]


class TestSIRDVSimulation:
    """Test SIRDV simulation (4-rate, 81 scenarios)."""

    def test_sirdv_simulation_init(self, sample_sirdv_data, sirdv_forecasting_box):
        """Test SIRDV simulation initialization."""
        interval = pd.date_range("2020-01-31", periods=10, freq="D")
        sim = EpidemicSimulation(sample_sirdv_data, sirdv_forecasting_box, interval)

        assert sim.has_vaccination
        assert sim.data is not None
        assert sim.forecasting_box is not None
        assert "delta" in sim.forecasting_box

    def test_sirdv_simulate_single_scenario(
        self, sample_sirdv_data, sirdv_forecasting_box
    ):
        """Test single SIRDV scenario simulation."""
        interval = pd.date_range("2020-01-31", periods=10, freq="D")
        sim = EpidemicSimulation(sample_sirdv_data, sirdv_forecasting_box, interval)

        result = sim.simulate_for_given_levels(("point", "point", "point", "point"))

        # Check result structure
        assert len(result) == 10
        assert "S" in result.columns
        assert "I" in result.columns
        assert "R" in result.columns
        assert "D" in result.columns
        assert "V" in result.columns
        assert "C" in result.columns
        assert "A" in result.columns

        # Check all 4 rates are present
        assert "alpha" in result.columns
        assert "beta" in result.columns
        assert "gamma" in result.columns
        assert "delta" in result.columns

    def test_sirdv_vaccination_flow(self, sample_sirdv_data, sirdv_forecasting_box):
        """Test that vaccination flow reduces S and increases V."""
        interval = pd.date_range("2020-01-31", periods=10, freq="D")
        sim = EpidemicSimulation(sample_sirdv_data, sirdv_forecasting_box, interval)

        result = sim.simulate_for_given_levels(("point", "point", "point", "point"))

        # V should increase over time (or stay the same if delta=0)
        assert result["V"].iloc[-1] >= result["V"].iloc[0]

        # S should decrease (due to infection and vaccination)
        assert result["S"].iloc[-1] <= result["S"].iloc[0]

    def test_sirdv_81_scenarios(self, sample_sirdv_data, sirdv_forecasting_box):
        """Test that SIRDV generates 81 scenarios (3^4)."""
        interval = pd.date_range("2020-01-31", periods=10, freq="D")
        sim = EpidemicSimulation(sample_sirdv_data, sirdv_forecasting_box, interval)

        sim.run_simulations(n_jobs=1)

        # Count scenarios
        scenario_count = 0
        for alpha_level in FORECASTING_LEVELS:
            for beta_level in FORECASTING_LEVELS:
                for gamma_level in FORECASTING_LEVELS:
                    for delta_level in FORECASTING_LEVELS:
                        scenario = sim.simulation[alpha_level][beta_level][gamma_level][
                            delta_level
                        ]
                        assert scenario is not None
                        scenario_count += 1

        assert scenario_count == 81

    def test_sirdv_simulation_box_structure(
        self, sample_sirdv_data, sirdv_forecasting_box
    ):
        """Test SIRDV simulation box has 4D structure."""
        interval = pd.date_range("2020-01-31", periods=10, freq="D")
        sim = EpidemicSimulation(sample_sirdv_data, sirdv_forecasting_box, interval)

        sim.create_simulation_box()

        # Verify 4D structure
        for alpha_level in FORECASTING_LEVELS:
            for beta_level in FORECASTING_LEVELS:
                for gamma_level in FORECASTING_LEVELS:
                    for delta_level in FORECASTING_LEVELS:
                        # This should work for SIRDV
                        assert (
                            sim.simulation[alpha_level][beta_level][gamma_level][
                                delta_level
                            ]
                            is None
                        )


class TestSIRDVConservationLaw:
    """Test SIRDV conservation law: N = S + I + R + D + V."""

    def test_sirdv_conservation_holds(self, sample_sirdv_data, sirdv_forecasting_box):
        """Test that conservation law holds in SIRDV simulation."""
        interval = pd.date_range("2020-01-31", periods=10, freq="D")
        sim = EpidemicSimulation(sample_sirdv_data, sirdv_forecasting_box, interval)

        result = sim.simulate_for_given_levels(("point", "point", "point", "point"))

        # Get initial population N from last historical data
        N = (
            sample_sirdv_data.iloc[-1]["S"]
            + sample_sirdv_data.iloc[-1]["I"]
            + sample_sirdv_data.iloc[-1]["R"]
            + sample_sirdv_data.iloc[-1]["D"]
            + sample_sirdv_data.iloc[-1]["V"]
        )

        # Check conservation: N = S + I + R + D + V
        for idx in result.index:
            total = (
                result.loc[idx, "S"]
                + result.loc[idx, "I"]
                + result.loc[idx, "R"]
                + result.loc[idx, "D"]
                + result.loc[idx, "V"]
            )
            # Allow some tolerance for numerical errors
            assert abs(total - N) / N < 0.01  # Within 1%


class TestParallelSimulationSIRDV:
    """Test parallel execution for SIRDV simulations."""

    def test_parallel_sirdv_matches_sequential(
        self, sample_sirdv_data, sirdv_forecasting_box
    ):
        """Test that parallel SIRDV execution matches sequential."""
        interval = pd.date_range("2020-01-31", periods=5, freq="D")

        # Sequential execution
        sim_seq = EpidemicSimulation(sample_sirdv_data, sirdv_forecasting_box, interval)
        sim_seq.run_simulations(n_jobs=1)

        # Parallel execution
        sim_par = EpidemicSimulation(sample_sirdv_data, sirdv_forecasting_box, interval)
        sim_par.run_simulations(n_jobs=2)

        # Compare a few scenarios
        for alpha_level in ["lower", "point"]:
            for beta_level in ["lower", "point"]:
                for gamma_level in ["lower", "point"]:
                    for delta_level in ["lower", "point"]:
                        seq_result = sim_seq.simulation[alpha_level][beta_level][
                            gamma_level
                        ][delta_level]
                        par_result = sim_par.simulation[alpha_level][beta_level][
                            gamma_level
                        ][delta_level]

                        pd.testing.assert_frame_equal(seq_result, par_result)


class TestResultsGeneration:
    """Test results generation for both SIRD and SIRDV."""

    def test_sirdv_generate_results(self, sample_sirdv_data, sirdv_forecasting_box):
        """Test that generate_result works for SIRDV."""
        interval = pd.date_range("2020-01-31", periods=5, freq="D")
        sim = EpidemicSimulation(sample_sirdv_data, sirdv_forecasting_box, interval)

        sim.run_simulations(n_jobs=1)
        sim.generate_result()

        # Check that results contain V compartment
        assert "V" in sim.results
        assert len(sim.results.V) == 5

        # Check that results have all 81 scenario columns
        scenario_cols = [col for col in sim.results.V.columns if "|" in col]
        assert len(scenario_cols) == 81

        # Check central tendency columns
        assert "mean" in sim.results.V.columns
        assert "median" in sim.results.V.columns
        assert "gmean" in sim.results.V.columns
        assert "hmean" in sim.results.V.columns

    def test_sird_generate_results_no_v(self, sample_sird_data, sird_forecasting_box):
        """Test that SIRD results don't contain V compartment."""
        interval = pd.date_range("2020-01-31", periods=5, freq="D")
        sim = EpidemicSimulation(sample_sird_data, sird_forecasting_box, interval)

        sim.run_simulations(n_jobs=1)
        sim.generate_result()

        # Check that results do NOT contain V compartment
        assert "V" not in sim.results

        # Check that results have 27 scenario columns
        scenario_cols = [col for col in sim.results.C.columns if "|" in col]
        assert len(scenario_cols) == 27
