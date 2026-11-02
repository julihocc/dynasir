"""
Tests for parallel simulation execution.

This module tests the parallel execution capabilities of the epidemic simulation
engine, ensuring that parallel and sequential executions produce identical results
while providing performance improvements.
"""

import logging
import multiprocessing as mp
from concurrent.futures import Future
from concurrent.futures.process import BrokenProcessPool
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from dynasir import DataContainer, Model
from dynasir.core.config import get_settings
from dynasir.models import simulation as simulation_module
from dynasir.models.simulation import EpidemicSimulation


class TestParallelSimulations:
    """Test suite for parallel simulation execution."""

    @pytest.mark.slow
    def test_sequential_vs_parallel_identical_results(self, sample_data_container):
        """Test that sequential and parallel execution produce identical results."""
        # Create and fit model
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")
        model.create_model()
        model.fit_model(max_lag=2)
        model.forecast(steps=10)

        # Run sequential simulation
        model.simulation_engine.run_simulations(n_jobs=1)
        sequential_results = model.simulation_engine.simulation.to_dict()

        # Reset simulation
        model.simulation_engine.simulation = None
        model.simulation_engine.results = None

        # Run parallel simulation
        model.simulation_engine.run_simulations(n_jobs=2)
        parallel_results = model.simulation_engine.simulation.to_dict()

        # Compare all scenarios
        for alpha_level in ["lower", "point", "upper"]:
            for beta_level in ["lower", "point", "upper"]:
                for gamma_level in ["lower", "point", "upper"]:
                    seq_sim = sequential_results[alpha_level][beta_level][gamma_level]
                    par_sim = parallel_results[alpha_level][beta_level][gamma_level]

                    # Check DataFrames are equal
                    pd.testing.assert_frame_equal(
                        seq_sim,
                        par_sim,
                        check_exact=False,
                        rtol=1e-10,
                        atol=1e-10,
                    )

    @pytest.mark.slow
    def test_n_jobs_parameter_types(self, sample_data_container):
        """Test different n_jobs parameter values."""
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")
        model.create_model()
        model.fit_model(max_lag=2)
        model.forecast(steps=5)

        # n_jobs=1 (sequential)
        model.simulation_engine.run_simulations(n_jobs=1)
        assert model.simulation_engine.simulation is not None

        # Reset
        model.simulation_engine.simulation = None

        # n_jobs=2 (parallel with 2 workers)
        model.simulation_engine.run_simulations(n_jobs=2)
        assert model.simulation_engine.simulation is not None

        # Reset
        model.simulation_engine.simulation = None

        # n_jobs=None (auto-detect CPU count)
        model.simulation_engine.run_simulations(n_jobs=None)
        assert model.simulation_engine.simulation is not None

    @pytest.mark.slow
    def test_n_jobs_auto_detection(self, sample_data_container):
        """Test that n_jobs=None correctly auto-detects CPU count."""
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")
        model.create_model()
        model.fit_model(max_lag=2)
        model.forecast(steps=5)

        cpu_count = mp.cpu_count()

        # Mock to verify CPU count is used
        with patch("multiprocessing.cpu_count", return_value=cpu_count):
            model.simulation_engine.run_simulations(n_jobs=None)
            assert model.simulation_engine.simulation is not None

    @pytest.mark.slow
    def test_model_run_simulations_accepts_n_jobs(self, sample_data_container):
        """Test that Model.run_simulations() accepts and passes n_jobs parameter."""
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")
        model.create_model()
        model.fit_model(max_lag=2)
        model.forecast(steps=5)

        # Should accept n_jobs parameter without error
        model.run_simulations(n_jobs=1)
        assert model.simulation is not None

        # Reset
        model.simulation = None
        model.simulation_engine.simulation = None

        # Should work with n_jobs=2
        model.run_simulations(n_jobs=2)
        assert model.simulation is not None

    @pytest.mark.slow
    def test_parallel_simulation_all_scenarios_present(self, sample_data_container):
        """Test that parallel execution generates all 27 scenarios."""
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")
        model.create_model()
        model.fit_model(max_lag=2)
        model.forecast(steps=5)

        model.run_simulations(n_jobs=2)

        # Verify all 27 scenarios exist
        count = 0
        for alpha_level in ["lower", "point", "upper"]:
            for beta_level in ["lower", "point", "upper"]:
                for gamma_level in ["lower", "point", "upper"]:
                    scenario = model.simulation[alpha_level][beta_level][gamma_level]
                    assert scenario is not None
                    assert isinstance(scenario, pd.DataFrame)
                    assert len(scenario) == 5  # 5 forecast steps
                    count += 1

        assert count == 27

    @pytest.mark.slow
    def test_parallel_execution_with_generate_result(self, sample_data_container):
        """Test that parallel simulations work with generate_result()."""
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")
        model.create_model()
        model.fit_model(max_lag=2)
        model.forecast(steps=5)

        # Run parallel simulations
        model.run_simulations(n_jobs=2)
        model.generate_result()

        # Verify results were generated
        assert model.results is not None
        assert "C" in model.results
        assert "I" in model.results
        assert "D" in model.results

        # Verify central tendencies calculated
        results_c = model.results["C"]
        assert "mean" in results_c.columns
        assert "median" in results_c.columns
        assert "gmean" in results_c.columns
        assert "hmean" in results_c.columns

    def test_invalid_n_jobs_raises_error(self, sample_data_container):
        """Test that invalid n_jobs values raise appropriate errors."""
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")
        model.create_model()
        model.fit_model(max_lag=2)
        model.forecast(steps=5)

        # n_jobs=0 should raise ValueError
        with pytest.raises(ValueError, match="n_jobs must be None or >= 1"):
            model.simulation_engine.run_simulations(n_jobs=0)

        # n_jobs=-1 should raise ValueError
        with pytest.raises(ValueError, match="n_jobs must be None or >= 1"):
            model.simulation_engine.run_simulations(n_jobs=-1)

    @pytest.mark.slow
    def test_backward_compatibility_no_n_jobs(self, sample_data_container):
        """Test that run_simulations() works without n_jobs parameter (backward compatibility)."""
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")
        model.create_model()
        model.fit_model(max_lag=2)
        model.forecast(steps=5)

        # Should work without n_jobs parameter (uses default)
        model.run_simulations()
        assert model.simulation is not None


def _fitted_model(data_container):
    model = Model(data_container, start="2020-03-10", stop="2020-03-25")
    model.create_model()
    model.fit_model(max_lag=2)
    model.forecast(steps=5)
    return model


def _fake_executor(created_with, error=None):
    """Stand-in for ProcessPoolExecutor that runs jobs in-process, or fails each job with `error`."""

    class _Executor:
        def __init__(self, max_workers=None):
            created_with.append(max_workers)

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def submit(self, fn, *args, **kwargs):
            future = Future()
            if error is None:
                future.set_result(fn(*args, **kwargs))
            else:
                future.set_exception(error)
            return future

    return _Executor


@pytest.fixture
def clean_settings(monkeypatch):
    monkeypatch.delenv("PARALLEL_SIMULATIONS", raising=False)
    monkeypatch.delenv("N_SIMULATION_JOBS", raising=False)
    get_settings.cache_clear()
    yield monkeypatch
    get_settings.cache_clear()


class TestExecutionModeDefaults:
    """Default execution mode and recovery from a broken process pool (issue #160)."""

    def test_default_runs_sequentially_without_process_pool(
        self, sample_data_container, clean_settings
    ):
        created_with = []
        clean_settings.setattr(
            simulation_module, "ProcessPoolExecutor", _fake_executor(created_with)
        )
        model = _fitted_model(sample_data_container)

        model.run_simulations()

        assert created_with == []
        assert model.simulation is not None

    def test_parallel_opt_in_via_settings_uses_process_pool(
        self, sample_data_container, clean_settings
    ):
        clean_settings.setenv("PARALLEL_SIMULATIONS", "true")
        clean_settings.setenv("N_SIMULATION_JOBS", "3")
        get_settings.cache_clear()
        created_with = []
        clean_settings.setattr(
            simulation_module, "ProcessPoolExecutor", _fake_executor(created_with)
        )
        model = _fitted_model(sample_data_container)

        model.run_simulations()

        assert created_with == [3]

    def test_broken_process_pool_falls_back_to_sequential(
        self, sample_data_container, clean_settings, caplog
    ):
        expected = _fitted_model(sample_data_container)
        expected.run_simulations(n_jobs=1)
        expected.generate_result()

        clean_settings.setattr(
            simulation_module,
            "ProcessPoolExecutor",
            _fake_executor([], error=BrokenProcessPool("worker died")),
        )
        model = _fitted_model(sample_data_container)
        with caplog.at_level(logging.WARNING):
            model.run_simulations(n_jobs=2)
        model.generate_result()

        assert "__main__" in caplog.text
        assert "n_jobs=1" in caplog.text
        for compartment in expected.results:
            pd.testing.assert_frame_equal(
                model.results[compartment], expected.results[compartment]
            )
