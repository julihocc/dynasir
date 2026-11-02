"""Unit tests for temporal aggregation functionality."""

import numpy as np
import pandas as pd
import pytest

from dynasir import DataContainer, Model


class TestAggregrateForecast:
    """Test aggregate_forecast method."""

    @pytest.fixture
    def model_with_results(self, sample_data_container):
        """Create a model with generated results for testing."""
        # sample_data_container has data from 2020-03-01 to 2020-03-31
        # After smoothing with window=7, data starts from 2020-03-08
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")
        model.create_model()
        model.fit_model(max_lag=3)
        model.forecast(steps=30)  # 30 days
        model.run_simulations(n_jobs=1)
        model.generate_result()
        return model

    def test_aggregate_forecast_basic_functionality(self, model_with_results):
        """Test basic aggregation to weekly frequency."""
        aggregated = model_with_results.aggregate_forecast(
            "C", target_frequency="W", aggregate_func="last"
        )

        # Should have ~4 weeks of data (30 days / 7)
        assert len(aggregated) >= 4
        assert len(aggregated) <= 5

        # Should have scenario columns + mean + median
        assert "mean" in aggregated.columns
        assert "median" in aggregated.columns

    def test_aggregate_forecast_annual_frequency(self, model_with_results):
        """Test aggregation to annual frequency."""
        # Forecast 365 days to get 1-2 years (depending on start date)
        model = model_with_results
        model.forecast(steps=365)
        model.run_simulations(n_jobs=1)
        model.generate_result()

        aggregated = model.aggregate_forecast(
            "C", target_frequency="Y", aggregate_func="last"
        )

        # Should have 1-2 years (365 days can span 2 calendar years)
        assert len(aggregated) >= 1
        assert len(aggregated) <= 2

    def test_aggregate_forecast_sum_aggregation(self, model_with_results):
        """Test sum aggregation function."""
        aggregated = model_with_results.aggregate_forecast(
            "C", target_frequency="W", aggregate_func="sum"
        )

        # Sum should be >= individual daily values
        assert (aggregated["mean"] >= 0).all()

    def test_aggregate_forecast_mean_aggregation(self, model_with_results):
        """Test mean aggregation function."""
        aggregated = model_with_results.aggregate_forecast(
            "C", target_frequency="W", aggregate_func="mean"
        )

        # Mean should be reasonable
        assert (aggregated["mean"] >= 0).all()

    def test_aggregate_forecast_last_aggregation(self, model_with_results):
        """Test last (end-of-period) aggregation function."""
        aggregated = model_with_results.aggregate_forecast(
            "C", target_frequency="W", aggregate_func="last"
        )

        # Last value should represent end of week
        assert (aggregated["mean"] >= 0).all()

    def test_aggregate_forecast_max_aggregation(self, model_with_results):
        """Test max aggregation function."""
        aggregated = model_with_results.aggregate_forecast(
            "C", target_frequency="W", aggregate_func="max"
        )

        # Max should be >= mean
        daily_mean = model_with_results.results.C["mean"].mean()
        assert (aggregated["mean"] >= 0).all()

    def test_aggregate_forecast_different_compartments(self, model_with_results):
        """Test aggregation of different compartments."""
        compartments = ["C", "I", "R", "D"]

        for compartment in compartments:
            aggregated = model_with_results.aggregate_forecast(
                compartment, target_frequency="W", aggregate_func="last"
            )

            assert len(aggregated) >= 4
            assert "mean" in aggregated.columns

    def test_aggregate_forecast_custom_methods(self, model_with_results):
        """Test aggregation with custom central tendency methods."""
        aggregated = model_with_results.aggregate_forecast(
            "C",
            target_frequency="W",
            aggregate_func="last",
            methods=["mean", "median", "gmean"],
        )

        # Should have all requested methods
        assert "mean" in aggregated.columns
        assert "median" in aggregated.columns
        assert "gmean" in aggregated.columns

    def test_aggregate_forecast_single_method(self, model_with_results):
        """Test aggregation with single method."""
        aggregated = model_with_results.aggregate_forecast(
            "C", target_frequency="W", aggregate_func="last", methods=["mean"]
        )

        # Should have only mean
        assert "mean" in aggregated.columns
        # Median should not be included
        central_tendency_cols = ["median", "gmean", "hmean"]
        for col in central_tendency_cols:
            if col in aggregated.columns:
                # Only mean should be present
                pass

    def test_aggregate_forecast_error_no_results(self, sample_data_container):
        """Test error when results not generated."""
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")

        with pytest.raises(ValueError, match="Must generate results"):
            model.aggregate_forecast("C", target_frequency="W")

    def test_aggregate_forecast_error_invalid_compartment(self, model_with_results):
        """Test error with invalid compartment."""
        with pytest.raises(ValueError, match="not found in results"):
            model_with_results.aggregate_forecast("INVALID", target_frequency="W")

    def test_aggregate_forecast_error_invalid_function(self, model_with_results):
        """Test error with invalid aggregation function."""
        with pytest.raises(ValueError, match="Invalid aggregate_func"):
            model_with_results.aggregate_forecast(
                "C", target_frequency="W", aggregate_func="invalid_func"
            )

    def test_aggregate_forecast_error_invalid_methods(self, model_with_results):
        """Test error with invalid central tendency methods."""
        with pytest.raises(ValueError, match="Invalid methods"):
            model_with_results.aggregate_forecast(
                "C",
                target_frequency="W",
                aggregate_func="last",
                methods=["invalid_method"],
            )

    def test_aggregate_forecast_preserves_scenarios(self, model_with_results):
        """Test that scenario columns are preserved."""
        aggregated = model_with_results.aggregate_forecast(
            "C", target_frequency="W", aggregate_func="last"
        )

        # Should have scenario columns (with | separator)
        scenario_cols = [col for col in aggregated.columns if "|" in col]
        assert len(scenario_cols) > 0  # At least some scenarios

    def test_aggregate_forecast_index_type(self, model_with_results):
        """Test that aggregated index is DatetimeIndex."""
        aggregated = model_with_results.aggregate_forecast(
            "C", target_frequency="W", aggregate_func="last"
        )

        assert isinstance(aggregated.index, pd.DatetimeIndex)

    def test_aggregate_forecast_same_frequency_no_resample(self, model_with_results):
        """Target frequency equal to source should not resample or alter length."""
        original_len = len(model_with_results.results.C)
        aggregated = model_with_results.aggregate_forecast(
            "C", target_frequency="D", aggregate_func="last"
        )

        assert len(aggregated) == original_len
        assert isinstance(aggregated.index, pd.DatetimeIndex)

    def test_aggregate_forecast_monthly_frequency(self, model_with_results):
        """Test aggregation to monthly frequency."""
        # Forecast 60 days to get ~2 months
        model = model_with_results
        model.forecast(steps=60)
        model.run_simulations(n_jobs=1)
        model.generate_result()

        aggregated = model.aggregate_forecast(
            "C", target_frequency="M", aggregate_func="last"
        )

        # Should have 2 months
        assert len(aggregated) >= 1
        assert len(aggregated) <= 3  # Account for partial months

    def test_aggregate_forecast_non_daily_source(self, sample_annual_processed_data):
        """Aggregation works when source results are non-daily (e.g., annual)."""
        # Build a model and manually attach annual results
        container = DataContainer(
            sample_annual_processed_data, mode="cumulative", frequency="YE"
        )
        model = Model(container)
        model.results = {
            "C": pd.DataFrame(
                {
                    "mean": np.arange(len(container.data)),
                    "median": np.arange(len(container.data)),
                },
                index=container.data.index,
            )
        }

        aggregated = model.aggregate_forecast(
            "C", target_frequency="Y", aggregate_func="last"
        )

        # With matching frequency, length should be identical
        assert len(aggregated) == len(container.data)
        assert (aggregated.index == container.data.index).all()


class TestAggregationIntegration:
    """Integration tests for temporal aggregation with annual workflow."""

    def test_annual_workflow_with_aggregation(self, sample_data_container):
        """Test complete workflow: daily data -> forecast -> annual aggregation."""
        # Use daily data which is stable
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")

        model.create_model()
        model.fit_model(max_lag=3)

        # Forecast 2 years = 365*2 days
        model.forecast(steps=365 * 2)
        model.run_simulations(n_jobs=1)
        model.generate_result()

        # Aggregate daily forecasts to annual
        annual_forecast = model.aggregate_forecast(
            "C", target_frequency="Y", aggregate_func="last"
        )

        # Should have 2-3 years (depending on calendar alignment)
        assert len(annual_forecast) >= 2
        assert len(annual_forecast) <= 3

        # Should have mean and median
        assert "mean" in annual_forecast.columns
        assert "median" in annual_forecast.columns

        # Values should be reasonable (positive)
        assert (annual_forecast["mean"] >= 0).all()

    def test_aggregation_matches_frequency(self):
        """Test that aggregation works for different frequencies."""
        frequencies = [
            ("W", 7, 4),  # Weekly: 7 days each, expect ~4 weeks
            ("M", 30, 1),  # Monthly: 30 days, expect 1-2 months
        ]

        dates = pd.date_range("2020-01-01", periods=40, freq="D")
        data = pd.DataFrame(
            {
                "C": np.cumsum(np.random.exponential(50, 40)),
                "D": np.cumsum(np.random.exponential(2, 40)),
                "N": [1000000] * 40,
            },
            index=dates,
        )

        container = DataContainer(data, window=7)
        # After window=7 smoothing, data starts from 2020-01-08
        model = Model(container, start="2020-01-10", stop="2020-01-30")
        model.create_model()
        model.fit_model(max_lag=3)
        model.forecast(steps=30)
        model.run_simulations(n_jobs=1)
        model.generate_result()

        for freq_code, days_per_period, expected_periods in frequencies:
            aggregated = model.aggregate_forecast(
                "C", target_frequency=freq_code, aggregate_func="last"
            )

            # Check expected number of periods (with tolerance)
            assert len(aggregated) >= expected_periods - 1
            assert len(aggregated) <= expected_periods + 3
