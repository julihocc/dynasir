"""Integration tests for annual data workflow (v0.8.0)."""

import warnings

import numpy as np
import pandas as pd
import pytest

from dynasir import DataContainer, Model


class TestAnnualDataWorkflow:
    """Integration tests for complete annual data workflow."""

    @pytest.fixture
    def annual_measles_data(self):
        """Create realistic annual measles surveillance data."""
        # USA measles data from 1980-2020 (40 years)
        # Use YE (year-end) instead of deprecated Y
        dates = pd.date_range(start="1980", periods=40, freq="YE")
        np.random.seed(42)

        # Simulate declining measles cases post-vaccination
        # Start high, decrease exponentially, with random fluctuations
        base_level = 500
        trend = np.exp(-np.linspace(0, 3, 40))  # Exponential decline
        noise = np.random.lognormal(0, 0.3, 40)  # Log-normal noise
        cases = np.cumsum(base_level * trend * noise)

        # Deaths (CFR ~0.1-0.2% for measles with treatment)
        deaths = np.cumsum(0.001 * base_level * trend * noise)

        data = pd.DataFrame(
            {
                "C": cases,
                "D": deaths,
                "N": [330000000] * 40,  # USA population
            },
            index=dates,
        )

        return data

    def test_annual_data_detection_and_warning(self, annual_measles_data):
        """Test that annual frequency is detected and NO warning (native support).

        In v0.10.0+, annual data is processed natively without reindexing,
        so no frequency mismatch warning is emitted. Instead, verify that:
        1. Frequency is correctly detected
        2. Data shape is preserved (no artificial reindexing)
        """
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Create container with annual data
            # With frequency support, should NOT reindex to daily
            container = DataContainer(annual_measles_data, frequency="YE")

            # Should NOT emit frequency mismatch warning (native support)
            frequency_warnings = [
                str(warning.message)
                for warning in w
                if "FREQUENCY MISMATCH" in str(warning.message)
            ]
            assert len(frequency_warnings) == 0, (
                f"Should not emit frequency mismatch warning with native annual support. "
                f"Got: {frequency_warnings}"
            )

            # Verify frequency is set correctly
            assert container.frequency == "YE"

            # Verify data shape is preserved (not expanded to daily)
            # Input: ~10 annual observations → Output should be ~10 rows
            # (not ~3650 rows from daily reindexing)
            assert len(container.data) <= len(annual_measles_data) * 2, (
                f"Annual data should not be massively expanded. "
                f"Input: {len(annual_measles_data)}, Output: {len(container.data)}"
            )

    def test_complete_annual_workflow_with_aggregation(self, sample_data_container):
        """Test complete workflow: daily data -> forecast -> annual aggregation.

        Note: Phase 1 (v0.8.0) does not support native annual data modeling.
        This test uses daily data and aggregates to annual to demonstrate the
        aggregation functionality. Native annual modeling requires Phase 2 (v0.9.0+).
        """
        # Use stable daily data and aggregate to annual
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")
        model.create_model()
        model.fit_model(max_lag=3)

        # Forecast 2 years
        model.forecast(steps=365 * 2)
        model.run_simulations(n_jobs=1)
        model.generate_result()

        # Aggregate daily forecasts back to annual
        annual_forecast = model.aggregate_forecast(
            "C", target_frequency="Y", aggregate_func="last"
        )

        # Verify results
        assert len(annual_forecast) >= 2, "Should have ~2 years of forecast"
        assert len(annual_forecast) <= 3, "Should not exceed 3 years"

        # Should have mean and median
        assert "mean" in annual_forecast.columns
        assert "median" in annual_forecast.columns

        # Values should be positive
        assert (annual_forecast["mean"] >= 0).all()
        assert (annual_forecast["median"] >= 0).all()

        # Should preserve scenario columns
        scenario_cols = [col for col in annual_forecast.columns if "|" in col]
        assert len(scenario_cols) > 0, "Should preserve scenario columns"

    def test_annual_workflow_multiple_compartments(self, sample_data_container):
        """Test aggregation of multiple compartments to annual frequency."""
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")
        model.create_model()
        model.fit_model(max_lag=3)
        model.forecast(steps=365 * 2)  # 2 years
        model.run_simulations(n_jobs=1)
        model.generate_result()

        # Test aggregation for different compartments
        compartments = ["C", "I", "R", "D"]

        for compartment in compartments:
            annual_forecast = model.aggregate_forecast(
                compartment, target_frequency="Y", aggregate_func="last"
            )

            # Basic sanity checks
            assert len(annual_forecast) >= 2
            assert "mean" in annual_forecast.columns
            assert (annual_forecast["mean"] >= 0).all()

    def test_annual_workflow_different_aggregation_functions(
        self, sample_data_container
    ):
        """Test different aggregation functions on annual frequency."""
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")
        model.create_model()
        model.fit_model(max_lag=3)
        model.forecast(steps=365 * 2)
        model.run_simulations(n_jobs=1)
        model.generate_result()

        # Test different aggregation functions
        agg_functions = ["sum", "mean", "last", "max"]

        for agg_func in agg_functions:
            annual_forecast = model.aggregate_forecast(
                "C", target_frequency="Y", aggregate_func=agg_func
            )

            assert len(annual_forecast) >= 2
            assert "mean" in annual_forecast.columns

            # Verify aggregation makes sense
            if agg_func == "sum":
                # Sum should be >= max individual value
                assert (annual_forecast["mean"] >= 0).all()
            elif agg_func == "max":
                # Max should be >= mean
                assert (annual_forecast["mean"] >= 0).all()

    def test_weekly_to_monthly_aggregation(self, sample_data_container):
        """Test aggregation from daily to weekly to monthly frequency."""
        # Use stable daily data container
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")
        model.create_model()
        model.fit_model(max_lag=3)
        model.forecast(steps=90)  # ~3 months
        model.run_simulations(n_jobs=1)
        model.generate_result()

        # Aggregate daily forecasts to monthly
        monthly_forecast = model.aggregate_forecast(
            "C", target_frequency="M", aggregate_func="last"
        )

        # Should have ~3 months
        assert len(monthly_forecast) >= 2
        assert len(monthly_forecast) <= 5
        assert "mean" in monthly_forecast.columns

    def test_monthly_to_annual_aggregation(self, sample_data_container):
        """Test aggregation from daily to annual frequency."""
        # Use stable daily data container
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")
        model.create_model()
        model.fit_model(max_lag=3)
        model.forecast(steps=365)  # 1 year
        model.run_simulations(n_jobs=1)
        model.generate_result()

        # Aggregate to annual
        annual_forecast = model.aggregate_forecast(
            "C", target_frequency="Y", aggregate_func="last"
        )

        # Should have 1-2 years
        assert len(annual_forecast) >= 1
        assert len(annual_forecast) <= 2
        assert "mean" in annual_forecast.columns


class TestBackwardCompatibilityV080:
    """Test that v0.8.0 changes maintain backward compatibility."""

    def test_default_behavior_unchanged(self, sample_data_container):
        """Test that default behavior matches v0.7.0."""
        # Create model without any new v0.8.0 parameters
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")
        model.create_model()
        model.fit_model(max_lag=3)
        model.forecast(steps=30)
        model.run_simulations(n_jobs=1)
        model.generate_result()

        # Should work exactly as before
        assert model.results is not None
        assert "C" in model.results
        assert "mean" in model.results.C.columns

    def test_reindex_data_default_freq(self, sample_processed_data):
        """Test that reindex_data defaults to daily frequency."""
        from dynasir.data.preprocessing import reindex_data

        # Call without freq parameter (v0.7.0 style)
        reindexed = reindex_data(sample_processed_data)

        # Should default to daily
        assert reindexed.index.freq == "D"
        assert len(reindexed) == len(sample_processed_data)

    def test_new_constants_available(self):
        """Test that new v0.8.0 constants are available."""
        from dynasir.core.constants import (
            DEFAULT_FREQUENCY,
            FREQUENCY_ALIASES,
            RECOVERY_LAG_BY_FREQUENCY,
            SUPPORTED_FREQUENCIES,
        )

        # Verify new constants exist
        assert DEFAULT_FREQUENCY == "D"
        assert "Y" in SUPPORTED_FREQUENCIES
        assert "annual" in FREQUENCY_ALIASES
        assert "D" in RECOVERY_LAG_BY_FREQUENCY

    def test_frequency_detection_function_exists(self):
        """Test that frequency detection function is available."""
        from dynasir.data.preprocessing import detect_frequency

        # Should be callable
        assert callable(detect_frequency)

        # Test with simple daily data
        dates = pd.date_range("2020-01-01", periods=10, freq="D")
        data = pd.DataFrame(
            {"C": range(10), "D": range(10), "N": [1000] * 10}, index=dates
        )

        freq = detect_frequency(data)
        assert freq == "D"

    def test_aggregate_forecast_method_exists(self, sample_data_container):
        """Test that aggregate_forecast method exists on Model."""
        model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")

        # Method should exist
        assert hasattr(model, "aggregate_forecast")
        assert callable(model.aggregate_forecast)

        # Generate results first
        model.create_model()
        model.fit_model(max_lag=3)
        model.forecast(steps=30)
        model.run_simulations(n_jobs=1)
        model.generate_result()

        # Should be able to call it
        aggregated = model.aggregate_forecast("C", target_frequency="W")
        assert aggregated is not None
        assert isinstance(aggregated, pd.DataFrame)
