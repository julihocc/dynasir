"""
Tests for Model class and SIRD modeling functionality.

Following TDD approach - these tests are written before implementation
to define expected behavior and ensure correct extraction.
"""

import itertools
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

# Import from the original module during Phase 2 transition
from dynasir import Model
from dynasir.data import DataContainer


class TestModelInitialization:
    """Test Model class initialization and basic functionality."""

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

    def test_model_init_with_data_container(self, sample_data_container):
        """Test Model initialization with DataContainer."""
        # Act
        model = Model(sample_data_container)

        # Assert
        assert model.data_container is sample_data_container
        assert model.window == sample_data_container.window
        assert hasattr(model, "data")
        assert isinstance(model.data, pd.DataFrame)
        assert hasattr(model, "logit_ratios_values")

    def test_model_init_with_date_range(self, sample_data_container):
        """Test Model initialization with start/stop dates."""
        # Arrange
        start_date = "2020-01-10"
        stop_date = "2020-01-30"

        # Act
        model = Model(sample_data_container, start=start_date, stop=stop_date)

        # Assert
        assert model.start == start_date
        assert model.stop == stop_date
        assert len(model.data) <= len(sample_data_container.data)

    def test_model_init_with_forecast_days(self, sample_data_container):
        """Test Model initialization with custom forecast days."""
        # Arrange
        days_to_forecast = 14

        # Act
        model = Model(sample_data_container, days_to_forecast=days_to_forecast)

        # Assert
        assert model.days_to_forecast == days_to_forecast
        assert model.steps_to_forecast == days_to_forecast

    def test_model_init_with_forecast_steps(self, sample_data_container):
        model = Model(sample_data_container, steps_to_forecast=14)

        assert model.steps_to_forecast == 14
        assert model.days_to_forecast == 14

    def test_model_init_sets_logit_ratios_values(self, sample_data_container):
        """Test that Model extracts logit ratios values correctly."""
        # Act
        model = Model(sample_data_container)

        # Assert
        assert hasattr(model, "logit_ratios_values")
        assert isinstance(model.logit_ratios_values, np.ndarray)
        assert model.logit_ratios_values.shape[1] == 3  # alpha, beta, gamma


class TestModelVARFunctionality:
    """Test VAR modeling functionality."""

    @pytest.fixture
    def fitted_model(self, sample_data_container):
        """Create a model with fitted VAR."""
        model = Model(sample_data_container)
        model.create_model()
        model.fit_model()
        return model

    def test_create_logit_ratios_model(self, sample_data_container):
        """Test VAR model creation."""
        # Arrange
        model = Model(sample_data_container)

        # Act
        model.create_model()

        # Assert
        assert model.logit_ratios_model is not None
        assert hasattr(model.logit_ratios_model, "fit")

    def test_fit_logit_ratios_model(self, sample_data_container):
        """Test VAR model fitting."""
        # Arrange
        model = Model(sample_data_container)
        model.create_model()

        # Act
        model.fit_model()

        # Assert
        assert model.logit_ratios_model_fitted is not None
        assert hasattr(model.logit_ratios_model_fitted, "forecast_interval")
        assert model.days_to_forecast is not None
        assert model.days_to_forecast > 0

    def test_forecast_logit_ratios(self, fitted_model):
        """Test logit ratios forecasting."""
        # Act
        fitted_model.forecast(steps=7)

        # Assert
        assert fitted_model.forecasting_box is not None
        assert fitted_model.forecasting_interval is not None
        assert len(fitted_model.forecasting_interval) == 7

        # Check that all rate forecasts exist
        for rate in [
            "alpha",
            "beta",
            "gamma",
            "logit_alpha",
            "logit_beta",
            "logit_gamma",
        ]:
            assert rate in fitted_model.forecasting_box

    def test_forecast_generates_confidence_intervals(self, fitted_model):
        """Test that forecasting generates proper confidence intervals."""
        # Act
        fitted_model.forecast(steps=5)

        # Assert
        forecasting_levels = ["lower", "point", "upper"]
        for rate in ["alpha", "beta", "gamma"]:
            rate_forecast = fitted_model.forecasting_box[rate]
            assert isinstance(rate_forecast, pd.DataFrame)
            assert len(rate_forecast) == 5
            for level in forecasting_levels:
                assert level in rate_forecast.columns

    def test_forecast_dates_alignment(self, fitted_model):
        """Test that forecast dates are properly aligned."""
        # Act
        fitted_model.forecast(steps=10)

        # Assert
        last_data_date = fitted_model.data.index[-1]
        expected_start = last_data_date + pd.Timedelta(days=1)

        assert fitted_model.forecast_index_start == expected_start
        assert fitted_model.forecasting_interval[0] == expected_start


class TestModelSimulation:
    """Test SIRD simulation functionality."""

    @pytest.fixture
    def model_with_forecasts(self, sample_data_container):
        """Create model with VAR forecasts ready for simulation."""
        model = Model(sample_data_container)
        model.create_model()
        model.fit_model()
        model.forecast(steps=5)
        return model


class TestModelResults:
    """Test results processing and aggregation."""

    @pytest.fixture
    def model_with_simulations(self, sample_data_container):
        """Create model with complete simulations."""
        model = Model(sample_data_container)
        model.create_model()
        model.fit_model()
        model.forecast(steps=5)
        model.run_simulations()
        return model

    @pytest.mark.slow
    def test_generate_result(self, model_with_simulations):
        """Test complete results generation."""
        # Act
        model_with_simulations.generate_result()

        # Assert
        results = model_with_simulations.results
        assert results is not None

        # Check all SIRD compartments have results
        compartments = ["A", "C", "S", "I", "R", "D"]
        for compartment in compartments:
            assert compartment in results
            assert isinstance(results[compartment], pd.DataFrame)


class TestModelVisualization:
    """Test visualization functionality."""

    @pytest.fixture
    def model_with_results(self, sample_data_container):
        """Create model with complete results (optimized for speed)."""
        model = Model(sample_data_container)
        model.create_model()
        model.fit_model(max_lag=2)  # Reduced from default
        model.forecast(steps=3)  # Reduced from 5
        model.run_simulations(n_jobs=1)  # Sequential for consistency
        model.generate_result()
        return model

    @pytest.mark.slow
    @patch("matplotlib.pyplot.plot")
    @patch("matplotlib.pyplot.title")
    @patch("matplotlib.pyplot.legend")
    @patch("matplotlib.pyplot.grid")
    def test_visualize_results_basic(
        self,
        mock_grid,
        mock_legend,
        mock_title,
        mock_plot,
        model_with_results,
    ):
        """Test basic visualization functionality."""
        # Act
        model_with_results.visualize_results("C")

        # Assert
        assert mock_plot.called
        assert mock_title.called
        assert mock_legend.called
        assert mock_grid.called
        # Note: visualize_results() sets up the plot but doesn't call show()
        # to allow callers to customize before displaying

    @pytest.mark.slow
    @patch("matplotlib.pyplot.show")
    @patch("matplotlib.pyplot.plot")
    def test_visualize_results_with_testing_data(
        self, mock_plot, mock_show, model_with_results, sample_data_container
    ):
        """Test visualization with actual testing data overlay."""
        # Arrange
        testing_data = sample_data_container.data.tail(5)

        # Act
        model_with_results.visualize_results("C", testing_data=testing_data)

        # Assert
        assert mock_plot.called
        # Should have additional call for actual data
        call_count = mock_plot.call_count
        assert call_count > 4  # Gray lines + central tendencies + actual data


class TestModelEvaluation:
    """Test forecast evaluation functionality."""

    @pytest.fixture
    def model_with_results(self, sample_data_container):
        """Create model with results for evaluation."""
        model = Model(sample_data_container)
        model.create_model()
        model.fit_model()
        model.forecast(steps=5)
        model.run_simulations()
        model.generate_result()
        return model

    def test_evaluate_forecast_basic(self, model_with_results, sample_data_container):
        """Test basic forecast evaluation."""
        # Arrange
        testing_data = sample_data_container.data.tail(5)

        # Act
        evaluation = model_with_results.evaluate_forecast(testing_data)

        # Assert
        assert isinstance(evaluation, dict)

        # Default compartments to evaluate
        default_compartments = ["C", "D", "I"]
        for compartment in default_compartments:
            assert compartment in evaluation

        # Check metrics for each compartment
        central_methods = ["mean", "median", "gmean", "hmean"]
        expected_metrics = ["mae", "mse", "rmse", "mape", "smape"]

        for compartment in default_compartments:
            for method in central_methods:
                assert method in evaluation[compartment]
                for metric in expected_metrics:
                    assert metric in evaluation[compartment][method]
                    assert isinstance(
                        evaluation[compartment][method][metric], (int, float)
                    )

    @pytest.mark.slow
    def test_evaluate_forecast_custom_compartments(
        self, model_with_results, sample_data_container
    ):
        """Test evaluation with custom compartments."""
        # Arrange
        testing_data = sample_data_container.data.tail(5)
        custom_compartments = ["S", "R"]

        # Act
        evaluation = model_with_results.evaluate_forecast(
            testing_data, compartment_codes=custom_compartments
        )

        # Assert
        assert len(evaluation) == 2
        for compartment in custom_compartments:
            assert compartment in evaluation

    @pytest.mark.slow
    def test_evaluate_forecast_save_results(
        self, model_with_results, sample_data_container, tmp_path
    ):
        """
        Test saving evaluation results to JSON.

        Uses real temporary file to avoid pytest-cov stalling issues
        that occurred with mocked builtins.open.
        """
        # Arrange
        testing_data = sample_data_container.data.tail(5)
        # Create filename in temporary directory without extension
        test_file = tmp_path / "test_evaluation"
        filename = str(test_file)

        # Act
        evaluation = model_with_results.evaluate_forecast(
            testing_data, save_evaluation=True, filename=filename
        )

        # Assert
        # Check that JSON file was created
        json_file = Path(f"{filename}.json")
        assert json_file.exists(), "JSON file should be created"

        # Verify file contains valid JSON with expected structure
        with open(json_file, "r") as f:
            saved_data = json.load(f)

        # Check that saved data matches evaluation results
        assert isinstance(saved_data, dict)

        # Default compartments to evaluate
        default_compartments = ["C", "D", "I"]
        for compartment in default_compartments:
            assert compartment in saved_data

        # Verify structure matches evaluation dict
        central_methods = ["mean", "median", "gmean", "hmean"]
        expected_metrics = ["mae", "mse", "rmse", "mape", "smape"]

        for compartment in default_compartments:
            for method in central_methods:
                assert method in saved_data[compartment]
                for metric in expected_metrics:
                    assert metric in saved_data[compartment][method]


class TestModelIntegration:
    """Integration tests for complete Model workflow."""

    @pytest.mark.slow
    def test_complete_workflow(self, sample_data_container):
        """Test complete end-to-end Model workflow."""
        # Arrange & Act - Complete pipeline
        model = Model(sample_data_container)
        model.create_model()
        model.fit_model()
        model.forecast(steps=7)
        model.run_simulations()
        model.generate_result()

        # Assert - All components should be populated
        assert model.logit_ratios_model_fitted is not None
        assert model.forecasting_box is not None
        assert model.simulation_engine.simulation is not None
        assert model.results is not None

        # Results should contain all compartments
        compartments = ["A", "C", "S", "I", "R", "D"]
        for compartment in compartments:
            assert compartment in model.results

    @pytest.mark.slow
    def test_model_performance_reasonable_time(self, sample_data_container):
        """Test that complete model workflow completes in reasonable time."""
        # Arrange
        import time

        # Act - Time the complete workflow
        start_time = time.time()
        model = Model(sample_data_container)
        model.create_model()
        model.fit_model()
        model.forecast(steps=5)  # Smaller forecast for speed
        model.run_simulations()
        model.generate_result()
        end_time = time.time()

        # Assert - Should complete within reasonable time (30 seconds max)
        execution_time = end_time - start_time
        assert (
            execution_time < 30.0
        ), f"Model workflow took {execution_time:.2f}s, expected <30s"

    def test_model_backward_compatibility(self, sample_data_container):
        """Test that Model maintains backward compatibility with existing usage."""
        # Act - Use Model the same way as legacy code
        model = Model(
            sample_data_container,
            start="2020-03-10",
            stop="2020-03-25",
            days_to_forecast=7,
        )

        # Assert - Should maintain same interface and attributes
        assert hasattr(model, "data_container")
        assert hasattr(model, "data")
        assert hasattr(model, "window")
        assert hasattr(model, "start")
        assert hasattr(model, "stop")
        assert hasattr(model, "days_to_forecast")

        # Should be able to create and fit model
        model.create_model()
        model.fit_model()
        assert model.logit_ratios_model is not None
        assert model.logit_ratios_model_fitted is not None


class TestModelR0Calculations:
    """Test R₀ (basic reproduction number) calculation functionality."""

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
    def fitted_model_with_forecast(self, sample_data_container):
        """Create a model with fitted VAR and forecast."""
        model = Model(sample_data_container)
        model.create_model()
        model.fit_model()
        model.forecast(steps=10)
        return model

    def test_calculate_R0_returns_series(self, sample_data_container):
        """Test that calculate_R0 returns a pandas Series."""
        # Arrange
        model = Model(sample_data_container)

        # Act
        R0 = model.calculate_R0()

        # Assert
        assert isinstance(R0, pd.Series)
        assert R0.name == "R0"

    def test_calculate_R0_correct_length(self, sample_data_container):
        """Test that R₀ series has same length as model data."""
        # Arrange
        model = Model(sample_data_container)

        # Act
        R0 = model.calculate_R0()

        # Assert
        assert len(R0) == len(model.data)

    def test_calculate_R0_non_negative(self, sample_data_container):
        """Test that R₀ values are non-negative."""
        # Arrange
        model = Model(sample_data_container)

        # Act
        R0 = model.calculate_R0()

        # Assert
        assert all(R0 >= 0), "R₀ values must be non-negative"

    def test_calculate_R0_correct_formula(self, sample_data_container):
        """Test that R₀ calculation uses correct formula: α / (β + γ)."""
        # Arrange
        model = Model(sample_data_container)

        # Act
        R0 = model.calculate_R0()

        # Calculate expected values manually
        alpha = model.data["alpha"]
        beta = model.data["beta"]
        gamma = model.data["gamma"]
        expected_R0 = alpha / (beta + gamma)

        # Assert
        pd.testing.assert_series_equal(R0, expected_R0, check_names=False)

    def test_calculate_R0_missing_columns_raises_error(self):
        """Test that calculate_R0 raises error when required columns missing."""
        # Arrange - Create data without required rate columns
        dates = pd.date_range("2020-01-01", periods=20, freq="D")
        incomplete_data = pd.DataFrame(
            {
                "C": np.cumsum(np.random.poisson(10, 20)) + 100,
                "D": np.cumsum(np.random.poisson(1, 20)) + 1,
                "N": [1000000] * 20,
            },
            index=dates,
        )
        # Create container but manually modify data to remove rate columns
        container = DataContainer(incomplete_data, window=7)
        model = Model(container)

        # Remove rate columns to simulate missing data
        model.data = model.data.drop(columns=["alpha", "beta", "gamma"])

        # Act & Assert
        with pytest.raises(ValueError, match="Missing required columns"):
            model.calculate_R0()

    def test_forecast_R0_returns_dataframe(self, fitted_model_with_forecast):
        """Test that forecast_R0 returns a pandas DataFrame."""
        # Act
        R0_forecast = fitted_model_with_forecast.forecast_R0()

        # Assert
        assert isinstance(R0_forecast, pd.DataFrame)

    def test_forecast_R0_correct_shape(self, fitted_model_with_forecast):
        """Test that forecast_R0 has correct shape (steps × scenarios)."""
        # Act
        R0_forecast = fitted_model_with_forecast.forecast_R0()

        # Assert
        # Should have 10 rows (steps) and 27 scenario columns + 5 summary columns
        assert R0_forecast.shape[0] == 10
        assert (
            R0_forecast.shape[1] == 27 + 5
        )  # 27 scenarios + mean, median, std, min, max

    def test_forecast_R0_has_summary_statistics(self, fitted_model_with_forecast):
        """Test that forecast_R0 includes summary statistic columns."""
        # Act
        R0_forecast = fitted_model_with_forecast.forecast_R0()

        # Assert
        summary_cols = ["mean", "median", "std", "min", "max"]
        for col in summary_cols:
            assert col in R0_forecast.columns, f"Missing summary column: {col}"

    def test_forecast_R0_correct_index(self, fitted_model_with_forecast):
        """Test that forecast_R0 has correct forecasting interval index."""
        # Act
        R0_forecast = fitted_model_with_forecast.forecast_R0()

        # Assert
        pd.testing.assert_index_equal(
            R0_forecast.index, fitted_model_with_forecast.forecasting_interval
        )

    def test_forecast_R0_non_negative(self, fitted_model_with_forecast):
        """Test that all forecasted R₀ values are non-negative."""
        # Act
        R0_forecast = fitted_model_with_forecast.forecast_R0()

        # Assert
        assert (R0_forecast >= 0).all().all(), "All R₀ forecasts must be non-negative"

    def test_forecast_R0_without_forecast_raises_error(self, sample_data_container):
        """Test that forecast_R0 raises error if forecast not generated."""
        # Arrange
        model = Model(sample_data_container)
        model.create_model()
        model.fit_model()
        # Don't call forecast()

        # Act & Assert
        with pytest.raises(ValueError, match="Forecast must be generated"):
            model.forecast_R0()

    def test_forecast_R0_scenario_naming(self, fitted_model_with_forecast):
        """Test that forecast_R0 scenarios are named correctly."""
        # Act
        R0_forecast = fitted_model_with_forecast.forecast_R0()

        # Assert
        # Check that scenario columns follow pattern: level|level|level
        scenario_cols = [
            col
            for col in R0_forecast.columns
            if col not in ["mean", "median", "std", "min", "max"]
        ]

        assert len(scenario_cols) == 27, "Should have 27 scenario combinations"

        # Check format of scenario names
        for col in scenario_cols:
            parts = col.split("|")
            assert len(parts) == 3, f"Scenario name {col} should have 3 parts"
            assert all(
                part in ["lower", "point", "upper"] for part in parts
            ), f"Invalid scenario level in {col}"

    def test_R0_interpretation_threshold(self, sample_data_container):
        """Test R₀ interpretation around critical threshold of 1."""
        # Arrange
        model = Model(sample_data_container)
        R0 = model.calculate_R0()

        # Act - Count days above/below threshold
        growing_days = (R0 > 1).sum()
        declining_days = (R0 < 1).sum()
        stable_days = (R0 == 1).sum()

        # Assert
        total_days = growing_days + declining_days + stable_days
        assert total_days == len(R0), "All days should be classified"
        assert growing_days + declining_days + stable_days == len(R0)

    def test_forecast_R0_summary_statistics_correct(self, fitted_model_with_forecast):
        """Test that summary statistics are calculated correctly."""
        # Act
        R0_forecast = fitted_model_with_forecast.forecast_R0()

        # Get scenario columns only (27 scenarios with pattern: level|level|level)
        scenario_cols = [
            col
            for col in R0_forecast.columns
            if col not in ["mean", "median", "std", "min", "max"]
        ]

        # Calculate expected statistics manually from scenario columns only
        scenario_data = R0_forecast[scenario_cols]

        # Assert - use lower precision due to floating point variations
        np.testing.assert_array_almost_equal(
            R0_forecast["mean"].values,
            scenario_data.mean(axis=1).values,
            decimal=8,
            err_msg="Mean calculation incorrect",
        )

        np.testing.assert_array_almost_equal(
            R0_forecast["median"].values,
            scenario_data.median(axis=1).values,
            decimal=8,
            err_msg="Median calculation incorrect",
        )

        np.testing.assert_array_almost_equal(
            R0_forecast["min"].values,
            scenario_data.min(axis=1).values,
            decimal=8,
            err_msg="Min calculation incorrect",
        )

        np.testing.assert_array_almost_equal(
            R0_forecast["max"].values,
            scenario_data.max(axis=1).values,
            decimal=8,
            err_msg="Max calculation incorrect",
        )


class TestDeprecatedAPIBackwardCompatibility:
    """Test deprecated API methods for backward compatibility."""

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

    def test_create_logit_ratios_model_deprecated(self, sample_data_container):
        """Test that create_logit_ratios_model emits deprecation warning."""
        # Arrange
        model = Model(sample_data_container)

        # Act & Assert - Should emit DeprecationWarning
        with pytest.warns(
            DeprecationWarning,
            match="create_logit_ratios_model.*deprecated.*create_model",
        ):
            model.create_logit_ratios_model()

        # Should still work correctly
        assert model.logit_ratios_model is not None

    def test_fit_logit_ratios_model_deprecated(self, sample_data_container):
        """Test that fit_logit_ratios_model emits deprecation warning."""
        # Arrange
        model = Model(sample_data_container)
        model.create_model()

        # Act & Assert - Should emit DeprecationWarning
        with pytest.warns(
            DeprecationWarning, match="fit_logit_ratios_model.*deprecated.*fit_model"
        ):
            model.fit_logit_ratios_model()

        # Should still work correctly
        assert model.logit_ratios_model_fitted is not None

    def test_forecast_logit_ratios_deprecated(self, sample_data_container):
        """Test that forecast_logit_ratios emits deprecation warning."""
        # Arrange
        model = Model(sample_data_container)
        model.create_model()
        model.fit_model()

        # Act & Assert - Should emit DeprecationWarning
        with pytest.warns(
            DeprecationWarning, match="forecast_logit_ratios.*deprecated.*forecast"
        ):
            model.forecast_logit_ratios(steps=5)

        # Should still work correctly
        assert model.forecasting_box is not None
        assert len(model.forecasting_interval) == 5

    @pytest.mark.slow
    def test_deprecated_api_complete_workflow(self, sample_data_container):
        """Test complete workflow using deprecated API methods."""
        # Arrange
        model = Model(sample_data_container)

        # Act - Use old API (should emit warnings but work)
        with pytest.warns(DeprecationWarning):
            model.create_logit_ratios_model()

        with pytest.warns(DeprecationWarning):
            model.fit_logit_ratios_model()

        with pytest.warns(DeprecationWarning):
            model.forecast_logit_ratios(steps=7)

        model.run_simulations()
        model.generate_result()

        # Assert - Should produce same results as new API
        assert model.logit_ratios_model_fitted is not None
        assert model.forecasting_box is not None
        assert model.results is not None

        # Results should contain all compartments
        compartments = ["A", "C", "S", "I", "R", "D"]
        for compartment in compartments:
            assert compartment in model.results

    def test_deprecated_and_new_api_equivalence(self, sample_data_container):
        """Test that deprecated and new APIs produce identical results."""
        # Arrange - Model with old API
        model_old = Model(sample_data_container, start="2020-01-10", stop="2020-01-30")

        with pytest.warns(DeprecationWarning):
            model_old.create_logit_ratios_model()
        with pytest.warns(DeprecationWarning):
            model_old.fit_logit_ratios_model(max_lag=2)  # Reduced lag for small dataset
        with pytest.warns(DeprecationWarning):
            model_old.forecast_logit_ratios(steps=5)

        # Arrange - Model with new API
        model_new = Model(sample_data_container, start="2020-01-10", stop="2020-01-30")
        model_new.create_model()
        model_new.fit_model(max_lag=2)  # Same reduced lag
        model_new.forecast(steps=5)

        # Assert - Results should be identical
        pd.testing.assert_index_equal(
            model_old.forecasting_interval, model_new.forecasting_interval
        )

        # Check that forecasting boxes have same structure
        for rate in ["alpha", "beta", "gamma"]:
            pd.testing.assert_frame_equal(
                model_old.forecasting_box[rate], model_new.forecasting_box[rate]
            )

    def test_deprecation_warning_mentions_removal_version(self, sample_data_container):
        """Test that deprecation warnings mention when methods will be removed."""
        # Arrange
        model = Model(sample_data_container)

        # Act & Assert - Should mention v0.8.0 removal
        with pytest.warns(DeprecationWarning, match="removed in v0.8.0"):
            model.create_logit_ratios_model()

        model.create_model()  # Ensure model exists for next test

        with pytest.warns(DeprecationWarning, match="removed in v0.8.0"):
            model.fit_logit_ratios_model()

        model.fit_model()  # Ensure fitted for next test

        with pytest.warns(DeprecationWarning, match="removed in v0.8.0"):
            model.forecast_logit_ratios(steps=5)

    def test_deprecated_methods_accept_same_arguments(self, sample_data_container):
        """Test that deprecated methods accept same arguments as new methods."""
        # Arrange
        model = Model(sample_data_container)

        # Act - Test with various arguments
        with pytest.warns(DeprecationWarning):
            model.create_logit_ratios_model()  # No args

        with pytest.warns(DeprecationWarning):
            model.fit_logit_ratios_model(max_lag=7, ic="bic")  # With kwargs

        with pytest.warns(DeprecationWarning):
            model.forecast_logit_ratios(10, alpha=0.1)  # With args and kwargs

        # Assert - Should work without errors
        assert model.forecasting_box is not None
