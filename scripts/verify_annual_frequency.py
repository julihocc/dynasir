"""
Verification script for AnnualFrequencyHandler (Issue #127).

Tests that annual data processing works correctly without reindexing.
"""

import pandas as pd
import numpy as np
from dynasir import DataContainer, Model
from dynasir.data.frequency_handlers import FrequencyHandlerRegistry


def create_annual_measles_data():
    """Create Mexico measles data 2010-2024 (15 annual observations)."""
    return pd.DataFrame(
        {
            "I": [220, 55, 667, 164, 81, 34, 12, 0, 0, 4, 18, 45, 103, 67, 89],
            "D": [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
            "N": [110_000_000] * 15,
        },
        index=pd.date_range("2010", periods=15, freq="YE"),
    )


def test_frequency_detection():
    """Verify frequency is correctly detected as 'YE'."""
    print("\n1. Frequency Detection:")
    print("-" * 70)

    annual_data = create_annual_measles_data()
    container = DataContainer(
        annual_data, window=1, frequency="YE", mode="incidence"
    )

    assert container.frequency == "YE"
    print("✓ Frequency correctly detected as 'YE'")
    return True


def test_handler_selection():
    """Verify AnnualFrequencyHandler is selected for 'YE' frequency."""
    print("\n2. Handler Selection:")
    print("-" * 70)

    registry = FrequencyHandlerRegistry()
    handler = registry.get("YE")

    assert handler.__class__.__name__ == "AnnualFrequencyHandler"
    print(f"✓ AnnualFrequencyHandler selected for 'YE' frequency")
    return True


def test_handler_parameters():
    """Verify AnnualFrequencyHandler has correct parameters."""
    print("\n3. Handler Parameters:")
    print("-" * 70)

    registry = FrequencyHandlerRegistry()
    handler = registry.get("YE")

    assert handler.days_per_year == 365
    assert handler.recovery_lag == 0  # Rounded from 14/365
    assert handler.default_max_lag == 3
    assert handler.min_observations == 10

    print(f"✓ Handler parameters correct:")
    print(f"  - days_per_year: {handler.days_per_year}")
    print(f"  - recovery_lag: {handler.recovery_lag}")
    print(f"  - default_max_lag: {handler.default_max_lag}")
    print(f"  - min_observations: {handler.min_observations}")
    return True


def test_no_reindexing():
    """Verify data stays at original size (no artificial reindexing)."""
    print("\n4. No Reindexing:")
    print("-" * 70)

    annual_data = create_annual_measles_data()
    original_length = len(annual_data)

    container = DataContainer(
        annual_data, window=1, frequency="YE", mode="incidence"
    )

    # Data should stay at 15 rows, not expand to ~5,475 daily rows
    assert len(container.data) == original_length
    print(
        f"✓ No reindexing: data stays at {len(container.data)} rows "
        f"(original: {original_length})"
    )
    return True


def test_feature_engineering():
    """Verify feature engineering works with annual data."""
    print("\n5. Feature Engineering:")
    print("-" * 70)

    annual_data = create_annual_measles_data()
    container = DataContainer(
        annual_data, window=1, frequency="YE", mode="incidence"
    )

    # Check required columns exist
    required_columns = ["C", "I", "R", "D", "S", "A"]
    for col in required_columns:
        assert col in container.data.columns

    print(f"✓ Feature engineering complete")
    print(f"  Columns: {', '.join(container.data.columns[:10])}...")
    return True


def test_rate_calculations():
    """Verify rate calculations are valid for annual data."""
    print("\n6. Rate Calculations:")
    print("-" * 70)

    annual_data = create_annual_measles_data()
    container = DataContainer(
        annual_data, window=1, frequency="YE", mode="incidence"
    )

    # Check rates exist and are valid
    rate_columns = ["alpha", "beta", "gamma"]
    for col in rate_columns:
        assert col in container.data.columns
        # Rates should be between 0 and 1 (or NaN for insufficient data)
        valid_rates = container.data[col].dropna()
        if len(valid_rates) > 0:
            assert (valid_rates >= 0).all() and (valid_rates <= 1).all()

    print(f"✓ Rate calculations valid for annual data")
    return True


def test_model_creation():
    """Verify Model can be created with annual data."""
    print("\n7. Model Creation:")
    print("-" * 70)

    annual_data = create_annual_measles_data()
    container = DataContainer(
        annual_data, window=1, frequency="YE", mode="incidence"
    )

    # Use actual data range (after feature engineering removes some rows)
    start_date = container.data.index[0]
    end_date = container.data.index[10]  # Use first 11 years for training

    model = Model(container, start=start_date, stop=end_date)
    model.create_model()

    assert model.frequency == "YE"
    assert model.mode == "incidence"

    print("✓ Model created successfully with annual data")
    print(f"  - Frequency: {model.frequency}")
    print(f"  - Mode: {model.mode}")
    print(f"  - Training: {start_date.year} to {end_date.year}")
    return True


def test_model_fitting():
    """Verify Model can be fitted with annual data."""
    print("\n8. Model Fitting:")
    print("-" * 70)

    annual_data = create_annual_measles_data()
    container = DataContainer(
        annual_data, window=1, frequency="YE", mode="incidence"
    )

    start_date = container.data.index[0]
    end_date = container.data.index[10]

    model = Model(container, start=start_date, stop=end_date)
    model.create_model()

    # Fit with max_lag=3 (default for annual)
    model.fit_model(max_lag=2, ic="aic")  # Use 2 lags for small dataset

    assert model.logit_ratios_model_fitted is not None
    print("✓ Model fitted successfully with max_lag=2")
    return True


def test_forecasting():
    """Verify forecasting works with annual data."""
    print("\n9. Forecasting:")
    print("-" * 70)

    annual_data = create_annual_measles_data()
    container = DataContainer(
        annual_data, window=1, frequency="YE", mode="incidence"
    )

    start_date = container.data.index[0]
    end_date = container.data.index[10]

    model = Model(container, start=start_date, stop=end_date)
    model.create_model()
    model.fit_model(max_lag=2)

    # Forecast 4 years
    model.forecast(steps=4)

    # Forecast should produce 4 annual periods
    assert model.forecasting_interval is not None
    assert len(model.forecasting_interval) == 4

    print("✓ Forecast generated for 4 annual periods")
    forecast_start = model.forecasting_interval[0]
    forecast_end = model.forecasting_interval[-1]
    print(f"  Forecast: {forecast_start.year} to {forecast_end.year}")
    return True


def test_end_to_end_workflow():
    """Complete end-to-end workflow with annual data."""
    print("\n10. End-to-End Workflow:")
    print("-" * 70)

    annual_data = create_annual_measles_data()

    # 1. Create container
    container = DataContainer(
        annual_data, window=1, frequency="YE", mode="incidence"
    )

    # 2. Create and fit model
    start_date = container.data.index[0]
    end_date = container.data.index[10]

    model = Model(container, start=start_date, stop=end_date)
    model.create_model()
    model.fit_model(max_lag=2)

    # 3. Forecast
    model.forecast(steps=4)

    # 4. Run simulations
    model.run_simulations(n_jobs=1)

    # 5. Generate results
    model.generate_result()

    # 6. Verify results
    assert model.results is not None
    assert "C" in model.results
    assert len(model.results["C"]) == 4  # 4 forecast periods

    print("✓ Complete end-to-end workflow successful")
    train_years = end_date.year - start_date.year + 1
    print(f"  - Training period: {train_years} years")
    print(f"  - Forecast period: 4 years")
    result_keys = ', '.join(list(model.results.keys())[:5])
    print(f"  - Results: {result_keys}...")
    return True


def main():
    """Run all verification tests and generate report."""
    print("=" * 70)
    print("AnnualFrequencyHandler Verification (Issue #127)")
    print("=" * 70)

    # Show test data info
    annual_data = create_annual_measles_data()
    print(f"\nTest data: Mexico measles 2010-2024")
    print(f"  - Shape: {annual_data.shape}")
    print(f"  - Frequency: {annual_data.index.freq}")
    print(f"  - Cases range: {annual_data['I'].min()} - {annual_data['I'].max()}")

    # Run tests
    tests = [
        ("Frequency Detection", test_frequency_detection),
        ("Handler Selection", test_handler_selection),
        ("Handler Parameters", test_handler_parameters),
        ("No Reindexing", test_no_reindexing),
        ("Feature Engineering", test_feature_engineering),
        ("Rate Calculations", test_rate_calculations),
        ("Model Creation", test_model_creation),
        ("Model Fitting", test_model_fitting),
        ("Forecasting", test_forecasting),
        ("End-to-End Workflow", test_end_to_end_workflow),
    ]

    passed = 0
    failed = 0
    errors = []

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n✗ FAILED: {e}")
            failed += 1
            errors.append((test_name, str(e)))

    print()
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if errors:
        print("\nFailed tests:")
        for test_name, error in errors:
            print(f"  - {test_name}: {error}")

    return passed, failed


if __name__ == "__main__":
    passed, failed = main()
    exit(0 if failed == 0 else 1)
