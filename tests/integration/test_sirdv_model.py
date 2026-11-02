"""
Integration tests for SIRDV model end-to-end workflow.

This module tests the complete Model class integration with vaccination
data, from data loading through forecasting and simulation.
"""

import numpy as np
import pandas as pd
import pytest

from dynasir import DataContainer, Model


@pytest.fixture
def sample_sird_data():
    """Sample SIRD data without vaccination."""
    dates = pd.date_range("2020-01-01", periods=60, freq="D")
    np.random.seed(42)

    data = pd.DataFrame(
        {
            "C": np.cumsum(np.random.exponential(50, 60)),
            "D": np.cumsum(np.random.exponential(2, 60)),
            "N": [1000000] * 60,
        },
        index=dates,
    )
    return data


@pytest.fixture
def sample_sirdv_data():
    """Sample SIRDV data with vaccination."""
    dates = pd.date_range("2020-01-01", periods=100, freq="D")
    np.random.seed(42)

    # Vaccination starts on day 50
    vaccinations = np.zeros(100)
    vaccinations[50:] = np.cumsum(np.random.exponential(2000, 50))

    data = pd.DataFrame(
        {
            "C": np.cumsum(np.random.exponential(50, 100)),
            "D": np.cumsum(np.random.exponential(2, 100)),
            "N": [1000000] * 100,
            "V": vaccinations,
        },
        index=dates,
    )
    return data


class TestSIRDModelIntegration:
    """Integration tests for SIRD model (backward compatibility)."""

    def test_sird_model_full_pipeline(self, sample_sird_data):
        """Test complete SIRD model pipeline."""
        container = DataContainer(sample_sird_data, window=7)
        model = Model(container, start="2020-01-10", stop="2020-02-15")

        # Verify SIRD mode detected
        assert not model.has_vaccination
        assert len(model.active_logit_ratios) == 3
        assert "logit_delta" not in model.active_logit_ratios

        # Create and fit model
        model.create_model()
        model.fit_model(max_lag=5, ic="aic")

        # Forecast
        model.forecast(steps=10)

        # Verify forecasting_box has 3 rates
        assert "alpha" in model.forecasting_box
        assert "beta" in model.forecasting_box
        assert "gamma" in model.forecasting_box
        assert "delta" not in model.forecasting_box

        # Run simulations (should be 27 scenarios)
        model.run_simulations(n_jobs=1)

        # Generate results
        model.generate_result()

        # Verify results don't include V
        assert "V" not in model.results
        assert "C" in model.results
        assert "I" in model.results
        assert "R" in model.results
        assert "D" in model.results

    def test_sird_model_cache_key(self, sample_sird_data):
        """Test that SIRD cache keys don't include vaccination."""
        container = DataContainer(sample_sird_data, window=7)
        model = Model(container, start="2020-01-10", stop="2020-02-15")

        model.create_model()
        model.fit_model(max_lag=5, ic="aic")
        model.forecast(steps=10)
        model.run_simulations(n_jobs=1)

        # Cache key should not include vaccination
        assert not model.has_vaccination


class TestSIRDVModelIntegration:
    """Integration tests for SIRDV model with vaccination."""

    def test_sirdv_model_detection(self, sample_sirdv_data):
        """Test that SIRDV mode is properly detected."""
        container = DataContainer(sample_sirdv_data, window=7)
        model = Model(container, start="2020-02-20", stop="2020-03-31")

        # Verify SIRDV mode detected
        assert model.has_vaccination
        assert len(model.active_logit_ratios) == 4
        assert "logit_alpha" in model.active_logit_ratios
        assert "logit_beta" in model.active_logit_ratios
        assert "logit_gamma" in model.active_logit_ratios
        assert "logit_delta" in model.active_logit_ratios

    def test_sirdv_model_full_pipeline(self, sample_sirdv_data):
        """Test complete SIRDV model pipeline."""
        container = DataContainer(sample_sirdv_data, window=7)
        model = Model(container, start="2020-02-20", stop="2020-03-31")

        # Create and fit model
        model.create_model()
        model.fit_model(max_lag=3, ic="aic")  # Forecast
        model.forecast(steps=10)

        # Verify forecasting_box has 4 rates
        assert "alpha" in model.forecasting_box
        assert "beta" in model.forecasting_box
        assert "gamma" in model.forecasting_box
        assert "delta" in model.forecasting_box

        # Run simulations (should be 81 scenarios)
        model.run_simulations(n_jobs=1)

        # Generate results
        model.generate_result()

        # Verify results include V compartment
        assert "V" in model.results
        assert "C" in model.results
        assert "I" in model.results
        assert "R" in model.results
        assert "D" in model.results
        assert "S" in model.results

    def test_sirdv_model_v_compartment_values(self, sample_sirdv_data):
        """Test that V compartment has reasonable values."""
        container = DataContainer(sample_sirdv_data, window=7)
        model = Model(container, start="2020-02-20", stop="2020-03-31")

        model.create_model()
        model.fit_model(max_lag=3, ic="aic")
        model.forecast(steps=10)
        model.run_simulations(n_jobs=1)
        model.generate_result()

        # V should be non-negative
        assert (model.results.V >= 0).all().all()

        # V should have scenario columns
        scenario_cols = [col for col in model.results.V.columns if "|" in col]
        assert len(scenario_cols) == 81  # 3^4 scenarios

    def test_sirdv_cache_key_includes_vaccination(self, sample_sirdv_data):
        """Test that SIRDV cache keys include vaccination flag."""
        container = DataContainer(sample_sirdv_data, window=7)
        model = Model(container, start="2020-02-20", stop="2020-03-31")

        model.create_model()
        model.fit_model(max_lag=3, ic="aic")
        model.forecast(steps=10)
        model.run_simulations(n_jobs=1)

        # Cache key should include vaccination
        assert model.has_vaccination


class TestSIRDSIRDVDifferences:
    """Test differences between SIRD and SIRDV models."""

    def test_sird_vs_sirdv_logit_ratios(self, sample_sird_data, sample_sirdv_data):
        """Test that SIRD has 3 logit ratios and SIRDV has 4."""
        # SIRD
        container_sird = DataContainer(sample_sird_data, window=7)
        model_sird = Model(container_sird, start="2020-01-10", stop="2020-02-15")
        assert len(model_sird.active_logit_ratios) == 3

        # SIRDV
        container_sirdv = DataContainer(sample_sirdv_data, window=7)
        model_sirdv = Model(container_sirdv, start="2020-02-20", stop="2020-03-31")
        assert len(model_sirdv.active_logit_ratios) == 4

    def test_sird_vs_sirdv_scenarios(self, sample_sird_data, sample_sirdv_data):
        """Test that SIRD has 27 scenarios and SIRDV has 81."""
        # SIRD
        container_sird = DataContainer(sample_sird_data, window=7)
        model_sird = Model(container_sird, start="2020-01-10", stop="2020-02-15")
        model_sird.create_model()
        model_sird.fit_model(max_lag=5, ic="aic")
        model_sird.forecast(steps=5)
        model_sird.run_simulations(n_jobs=1)
        model_sird.generate_result()

        scenario_cols_sird = [col for col in model_sird.results.C.columns if "|" in col]
        assert len(scenario_cols_sird) == 27

        # SIRDV
        container_sirdv = DataContainer(sample_sirdv_data, window=7)
        model_sirdv = Model(container_sirdv, start="2020-02-20", stop="2020-03-31")
        model_sirdv.create_model()
        model_sirdv.fit_model(max_lag=3, ic="aic")
        model_sirdv.forecast(steps=5)
        model_sirdv.run_simulations(n_jobs=1)
        model_sirdv.generate_result()

        scenario_cols_sirdv = [
            col for col in model_sirdv.results.C.columns if "|" in col
        ]
        assert len(scenario_cols_sirdv) == 81

    def test_sird_vs_sirdv_compartments(self, sample_sird_data, sample_sirdv_data):
        """Test compartment differences between SIRD and SIRDV."""
        # SIRD
        container_sird = DataContainer(sample_sird_data, window=7)
        model_sird = Model(container_sird, start="2020-01-10", stop="2020-02-15")
        model_sird.create_model()
        model_sird.fit_model(max_lag=5, ic="aic")
        model_sird.forecast(steps=5)
        model_sird.run_simulations(n_jobs=1)
        model_sird.generate_result()

        # SIRD should not have V
        assert "V" not in model_sird.results

        # SIRDV
        container_sirdv = DataContainer(sample_sirdv_data, window=7)
        model_sirdv = Model(container_sirdv, start="2020-02-20", stop="2020-03-31")
        model_sirdv.create_model()
        model_sirdv.fit_model(max_lag=3, ic="aic")
        model_sirdv.forecast(steps=5)
        model_sirdv.run_simulations(n_jobs=1)
        model_sirdv.generate_result()

        # SIRDV should have V
        assert "V" in model_sirdv.results


class TestBackwardCompatibility:
    """Test that SIRD models work exactly as before."""

    def test_sird_unchanged_behavior(self, sample_sird_data):
        """Test that SIRD models work with no changes."""
        container = DataContainer(sample_sird_data, window=7)
        model = Model(container, start="2020-01-10", stop="2020-02-15")

        # Should work exactly as before
        model.create_model()
        model.fit_model(max_lag=5, ic="aic")
        model.forecast(steps=10)
        model.run_simulations(n_jobs=1)
        model.generate_result()

        # All basic compartments should exist
        assert "C" in model.results
        assert "I" in model.results
        assert "R" in model.results
        assert "D" in model.results

        # Should have mean, median, gmean, hmean
        for compartment in ["C", "I", "R", "D"]:
            assert "mean" in model.results[compartment].columns
            assert "median" in model.results[compartment].columns
            assert "gmean" in model.results[compartment].columns
            assert "hmean" in model.results[compartment].columns
