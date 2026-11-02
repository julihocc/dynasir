"""
Verification tests for AnnualFrequencyHandler (Issue #127).

Tests that annual data processing works correctly without reindexing.
"""

import numpy as np
import pandas as pd
import pytest

from dynasir import DataContainer, Model
from dynasir.data.frequency_handlers import FrequencyHandlerRegistry


class TestAnnualFrequencyHandlerVerification:
    """Verification tests for annual frequency handling."""

    @pytest.fixture
    def annual_measles_data(self):
        """Mexico measles data 2010-2024 (15 annual observations)."""
        return pd.DataFrame(
            {
                "I": [220, 55, 667, 164, 81, 34, 12, 0, 0, 4, 18, 45, 103, 67, 89],
                "D": [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
                "N": [110_000_000] * 15,
            },
            index=pd.date_range("2010", periods=15, freq="YE"),
        )

    def test_frequency_detection(self, annual_measles_data):
        """Verify frequency is correctly detected as 'YE'."""
        container = DataContainer(
            annual_measles_data, window=1, frequency="YE", mode="incidence"
        )

        assert container.frequency == "YE"
        print("✓ Frequency correctly detected as 'YE'")

    def test_handler_selection(self):
        """Verify AnnualFrequencyHandler is selected for 'YE' frequency."""
        registry = FrequencyHandlerRegistry()
        handler = registry.get("YE")

        assert handler.__class__.__name__ == "AnnualFrequencyHandler"
        print(f"✓ AnnualFrequencyHandler selected for 'YE' frequency")

    def test_handler_parameters(self):
        """Verify AnnualFrequencyHandler has correct parameters."""
        registry = FrequencyHandlerRegistry()
        handler = registry.get("YE")

        assert handler.frequency_code == "YE"
        assert handler.frequency_name == "annual"
        assert handler.periods_per_year == 1
        assert handler.get_recovery_lag() == pytest.approx(
            14 / 365, rel=1e-3
        )  # Fractional lag
        assert handler.get_default_max_lag() == 3
        assert handler.get_min_observations() == 10

        print(f"✓ Handler parameters correct:")
        print(f"  - frequency_code: {handler.frequency_code}")
        print(f"  - frequency_name: {handler.frequency_name}")
        print(f"  - recovery_lag: {handler.get_recovery_lag():.6f}")
        print(f"  - default_max_lag: {handler.get_default_max_lag()}")
        print(f"  - min_observations: {handler.get_min_observations()}")

    def test_no_reindexing(self, annual_measles_data):
        """Verify data stays at original size (no artificial reindexing)."""
        original_length = len(annual_measles_data)

        container = DataContainer(
            annual_measles_data, window=1, frequency="YE", mode="incidence"
        )

        # Data should stay at 15 rows, not expand to ~5,475 daily rows
        assert len(container.data) == original_length
        print(
            f"✓ No reindexing: data stays at {len(container.data)} rows "
            f"(original: {original_length})"
        )

    def test_feature_engineering(self, annual_measles_data):
        """Verify feature engineering works with annual data."""
        container = DataContainer(
            annual_measles_data, window=1, frequency="YE", mode="incidence"
        )

        # Check required columns exist
        required_columns = ["C", "I", "R", "D", "S", "A"]
        for col in required_columns:
            assert col in container.data.columns

        print(
            f"✓ Feature engineering complete, columns: {list(container.data.columns)}"
        )

    def test_rate_calculations(self, annual_measles_data):
        """Verify rate calculations are valid for annual data."""
        container = DataContainer(
            annual_measles_data, window=1, frequency="YE", mode="incidence"
        )

        # Check rates exist and are valid
        rate_columns = ["alpha", "beta", "gamma"]
        for col in rate_columns:
            assert col in container.data.columns
            # Rates should be between 0 and 1 (or NaN for insufficient data)
            valid_rates = container.data[col].dropna()
            assert (valid_rates >= 0).all() and (valid_rates <= 1).all()

        print(f"✓ Rate calculations valid for annual data")

    def test_model_creation(self, annual_measles_data):
        """Verify Model can be created with annual data."""
        container = DataContainer(
            annual_measles_data, window=1, frequency="YE", mode="incidence"
        )

        # Create model (use subset for training: 2010-2019 data)
        # Note: annual data is indexed as year-end dates (2010-12-31)
        model = Model(container, start="2010-12-31", stop="2019-12-31")
        model.create_model()

        assert model.data_container.frequency == "YE"
        assert model.mode == "incidence"

        print(f"✓ Model created successfully with annual data")
        print(f"  - Frequency: {model.data_container.frequency}")
        print(f"  - Mode: {model.mode}")

    def test_model_fitting(self, annual_measles_data):
        """Verify Model can be fitted with annual data."""
        container = DataContainer(
            annual_measles_data, window=1, frequency="YE", mode="incidence"
        )

        model = Model(container, start="2010-12-31", stop="2019-12-31")
        model.create_model()

        # Fit with max_lag=3 (default for annual)
        model.fit_model(max_lag=3, ic="aic")

        assert model.logit_ratios_model_fitted is not None
        print(f"✓ Model fitted successfully with max_lag=3")

    def test_forecasting(self, annual_measles_data):
        """Verify forecasting works with annual data."""
        container = DataContainer(
            annual_measles_data, window=1, frequency="YE", mode="incidence"
        )

        model = Model(container, start="2010-12-31", stop="2019-12-31")
        model.create_model()
        model.fit_model(max_lag=3)

        # Forecast 5 years
        model.forecast(steps=5)

        # Forecast should produce 5 annual periods
        assert model.forecasting_interval is not None
        assert len(model.forecasting_interval) == 5

        print("✓ Forecast generated for 5 annual periods")

    def test_end_to_end_workflow(self, annual_measles_data):
        """Complete end-to-end workflow with annual data."""
        # 1. Create container
        container = DataContainer(
            annual_measles_data, window=1, frequency="YE", mode="incidence"
        )

        # 2. Create and fit model
        model = Model(container, start="2010-12-31", stop="2019-12-31")
        model.create_model()
        model.fit_model(max_lag=3)

        # 3. Forecast
        model.forecast(steps=5)

        # 4. Run simulations
        model.run_simulations(n_jobs=1)

        # 5. Generate results
        model.generate_result()

        # 6. Verify results
        assert model.results is not None
        assert "C" in model.results
        assert len(model.results["C"]) == 5  # 5 forecast periods

        print("✓ Complete end-to-end workflow successful")
        print("  - Training period: 2010-2020 (11 years)")
        print("  - Forecast period: 5 years")
        print(f"  - Results generated: {list(model.results.keys())}")


def run_verification():
    """Run all verification tests and generate report."""
    print("=" * 70)
    print("AnnualFrequencyHandler Verification (Issue #127)")
    print("=" * 70)
    print()

    # Create test instance
    test_instance = TestAnnualFrequencyHandlerVerification()

    # Create test data
    annual_data = test_instance.annual_measles_data(None)
    print("Test data: Mexico measles 2010-2024")
    print(f"  - Shape: {annual_data.shape}")
    print(f"  - Frequency: {annual_data.index.freq}")
    print()

    # Run tests
    tests = [
        (
            "Frequency Detection",
            lambda: test_instance.test_frequency_detection(annual_data),
        ),
        ("Handler Selection", lambda: test_instance.test_handler_selection()),
        ("Handler Parameters", lambda: test_instance.test_handler_parameters()),
        ("No Reindexing", lambda: test_instance.test_no_reindexing(annual_data)),
        (
            "Feature Engineering",
            lambda: test_instance.test_feature_engineering(annual_data),
        ),
        (
            "Rate Calculations",
            lambda: test_instance.test_rate_calculations(annual_data),
        ),
        ("Model Creation", lambda: test_instance.test_model_creation(annual_data)),
        ("Model Fitting", lambda: test_instance.test_model_fitting(annual_data)),
        ("Forecasting", lambda: test_instance.test_forecasting(annual_data)),
        (
            "End-to-End Workflow",
            lambda: test_instance.test_end_to_end_workflow(annual_data),
        ),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 70)
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ FAILED: {e}")
            failed += 1

    print()
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_verification()
    exit(0 if failed == 0 else 1)
