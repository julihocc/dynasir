#!/usr/bin/env python3
"""
Smoke test to ensure the epydemics library functions correctly.

Tests basic functionality without full notebook execution.
"""
import sys
import pandas as pd
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

def test_basic_workflow():
    """Test basic SIRD workflow with cumulative mode."""
    print("\n=== Testing Basic SIRD Workflow ===")

    try:
        from dynasir import DataContainer, Model

        # Create simple cumulative data (daily frequency)
        dates = pd.date_range("2020-01-01", periods=60, freq="D")
        data = pd.DataFrame({
            "C": np.cumsum(np.random.randint(10, 50, 60)),  # Cumulative cases
            "D": np.cumsum(np.random.randint(0, 3, 60)),    # Cumulative deaths
            "N": [100000] * 60                               # Population
        }, index=dates)

        print("  Creating DataContainer (cumulative mode)...", end=" ")
        container = DataContainer(data, window=7, frequency="D", mode="cumulative")
        print("✅")

        print("  Creating Model...", end=" ")
        model = Model(container, start="2020-01-15", stop="2020-02-15")
        model.create_model()
        print("✅")

        print("  Fitting VAR model...", end=" ")
        model.fit_model(max_lag=5)
        print("✅")

        print("  Forecasting...", end=" ")
        model.forecast(steps=10)
        print("✅")

        print("  Running simulations...", end=" ")
        model.run_simulations(n_jobs=1)
        print("✅")

        print("  Generating results...", end=" ")
        model.generate_result()
        print("✅")

        print("\n✅ Basic workflow test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Basic workflow test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_incidence_mode_monthly():
    """Test incidence mode with monthly frequency (should work)."""
    print("\n=== Testing Incidence Mode (Monthly) ===")

    try:
        from dynasir import DataContainer, Model

        # Create incidence data (monthly frequency) with realistic pattern
        # Pattern: outbreak followed by decline
        dates = pd.date_range("2020-01", periods=24, freq="ME")
        pattern = [10, 15, 25, 45, 80, 120, 95, 70, 50, 35, 25, 20,
                   15, 12, 10, 15, 20, 25, 18, 12, 8, 6, 4, 3]
        data = pd.DataFrame({
            "I": pattern,                        # Incident cases
            "D": [0, 0, 1, 1, 2, 3, 2, 1, 1, 0, 0, 0,
                  0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],  # Deaths
            "N": [100000] * 24                   # Population
        }, index=dates)

        print("  Creating DataContainer (incidence mode, monthly)...", end=" ")
        container = DataContainer(data, window=3, frequency="ME", mode="incidence")
        print("✅")

        print("  Creating Model...", end=" ")
        # DataContainer trims early dates due to smoothing window
        # Use dates from processed data
        start_date = container.data.index[5]
        stop_date = container.data.index[15]
        model = Model(container, start=start_date, stop=stop_date)
        model.create_model()
        print("✅")

        print("  Fitting VAR model...", end=" ")
        model.fit_model(max_lag=6)
        print("✅")

        print("  Forecasting...", end=" ")
        model.forecast(steps=6)
        print("✅")

        print("  Running simulations...", end=" ")
        model.run_simulations(n_jobs=1)
        print("✅")

        print("  Generating results...", end=" ")
        model.generate_result()
        print("✅")

        print("\n✅ Incidence mode (monthly) test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Incidence mode (monthly) test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_annual_incidence_known_failure():
    """Test that annual + incidence mode fails as expected."""
    print("\n=== Testing Annual + Incidence (Expected Failure) ===")

    try:
        from dynasir import DataContainer, Model

        # Create annual incidence data
        dates = pd.date_range("2010", periods=15, freq="YE")
        data = pd.DataFrame({
            "I": [220, 55, 667, 164, 81, 34, 12, 0, 0, 4, 18, 45, 103, 67, 89],
            "D": [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
            "N": [110000000] * 15
        }, index=dates)

        print("  Creating DataContainer (incidence mode, annual)...", end=" ")
        container = DataContainer(data, window=1, frequency="YE", mode="incidence")
        print("✅")

        print("  Creating Model...", end=" ")
        # Use actual dates from the data (2010-12-31 to 2024-12-31)
        model = Model(container, start="2010-12-31", stop="2020-12-31")
        model.create_model()
        print("✅")

        print("  Fitting VAR model (expecting failure)...", end=" ")
        try:
            model.fit_model(max_lag=3)
            print("❌ UNEXPECTED: Model fit succeeded (should have failed)")
            return False
        except Exception as e:
            error_str = str(e)
            # Check for various forms of the singular matrix error
            if ("LinAlgError" in error_str or
                "singular" in error_str.lower() or
                "not positive definite" in error_str.lower()):
                print("✅ EXPECTED FAILURE (Singular matrix)")
                print(f"     Error: {str(e)[:100]}")
                print("\n✅ Known limitation correctly identified")
                return True
            else:
                print(f"❌ UNEXPECTED ERROR: {e}")
                return False

    except Exception as e:
        print(f"\n❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all smoke tests."""
    print("=" * 80)
    print("EPYDEMICS LIBRARY SMOKE TESTS")
    print("=" * 80)

    results = []

    # Test 1: Basic workflow (cumulative mode, daily)
    results.append(("Basic SIRD Workflow", test_basic_workflow()))

    # Test 2: Incidence mode with monthly frequency
    results.append(("Incidence Mode (Monthly)", test_incidence_mode_monthly()))

    # Test 3: Annual + incidence mode (expected to fail)
    results.append(("Annual + Incidence (Known Limitation)", test_annual_incidence_known_failure()))

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status}: {test_name}")

    print()
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ ALL SMOKE TESTS PASSED")
        print("   Library functionality is working as expected")
        print("   Documentation changes did not break core functionality")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
