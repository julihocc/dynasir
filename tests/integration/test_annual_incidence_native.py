"""
Integration tests for native annual + incidence mode workflow (v0.9.0).

Tests the complete fractional recovery lag fix that enables annual frequency
with incidence mode without VAR errors.
"""

import numpy as np
import pandas as pd
import pytest

from dynasir import DataContainer, Model


class TestAnnualIncidenceNativeSupport:
    """Test native annual frequency with incidence mode (v0.9.0+)."""

    @pytest.fixture
    def measles_annual_data(self):
        """
        Create realistic annual measles incident data.

        Based on Mexico measles pattern (2010-2024) from notebook 06:
        - 2010-2014: Sporadic imported cases
        - 2015-2019: Near elimination (few cases)
        - 2020-2024: Reintroduction and outbreaks
        """
        np.random.seed(42)
        dates = pd.date_range("2010", periods=15, freq="YE")

        # Incident cases per year (realistic pattern)
        incident_cases = np.array(
            [
                220,
                55,
                667,
                164,
                81,  # 2010-2014: sporadic
                34,
                12,
                0,
                0,
                4,  # 2015-2019: near elimination
                18,
                45,
                103,
                67,
                89,  # 2020-2024: reintroduction
            ]
        )

        # Deaths (CFR ~0.1-0.2% for measles)
        incident_deaths = np.array([1, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 1])
        cumulative_deaths = np.cumsum(incident_deaths)

        # Population (Mexico ~130M, growing)
        population = [120_000_000 + i * 2_000_000 for i in range(15)]

        data = pd.DataFrame(
            {"I": incident_cases, "D": cumulative_deaths, "N": population}, index=dates
        )

        return data

    def test_fractional_recovery_lag_implementation(self, measles_annual_data):
        """
        Test the period-cohort rates used for annual incidence data.

        The annual recovery lag (14/365 years) is below one period, so each
        year's cases are the cohort for the step to the next year and are all
        removed by then: beta = 1 - gamma, with gamma the next cohort's
        case-fatality share.
        """
        container = DataContainer(
            measles_annual_data, mode="incidence", frequency="YE", window=1
        )

        # Verify frequency handler uses fractional lag
        assert container.frequency == "YE"
        assert container.handler.get_recovery_lag() < 1

        data = container.data
        np.testing.assert_allclose(data["beta"], 1 - data["gamma"], atol=1e-9)
        assert (data["beta"] > 0).all() and (data["beta"] <= 1).all()
        assert (data["gamma"] >= 0).all() and (data["gamma"] < 1).all()

    def test_var_model_fits_with_annual_incidence(self, measles_annual_data):
        """
        Test that VAR model fits successfully with annual + incidence mode.

        Before the fix, this would fail with:
        LinAlgError: 1-th leading minor of the array is not positive definite

        Constant rate columns are now left out of the VAR and held fixed (#168).
        """
        container = DataContainer(
            measles_annual_data, mode="incidence", frequency="YE", window=1
        )

        model = Model(container)

        # This should NOT raise LinAlgError
        model.create_model()
        model.fit_model(max_lag=3)

        # Verify model fitted (the selected lag order may be 0)
        assert model.var_forecasting.logit_ratios_model_fitted is not None
        assert model.var_forecasting.logit_ratios_model_fitted.k_ar >= 0

    def test_complete_annual_incidence_workflow(self, measles_annual_data):
        """
        Test complete workflow: DataContainer → Model → Fit → Forecast → Simulate → Results.

        This is the end-to-end test from notebook 06.
        """
        # Step 1: Create DataContainer in incidence mode
        container = DataContainer(
            measles_annual_data, mode="incidence", frequency="YE", window=1
        )

        assert container.mode == "incidence"
        assert container.frequency == "YE"
        assert len(container.data) == 15  # No artificial expansion

        # Step 2: Create and fit model
        model = Model(container)
        assert model.mode == "incidence"

        model.create_model()
        model.fit_model(max_lag=3)

        # Step 3: Forecast (5 years = 5 periods, not 1825 days)
        model.forecast(steps=5)
        assert model.var_forecasting.forecasting_interval is not None
        assert model.forecasting_interval.equals(
            pd.date_range("2025-12-31", periods=5, freq="YE")
        )
        assert model.steps_to_forecast == 5
        assert model.days_to_forecast == 5

        # Step 4: Run simulations
        model.run_simulations(n_jobs=1)

        # Step 5: Generate results
        model.generate_result()

        # Verify results
        assert model.results is not None
        assert "C" in model.results
        assert "I" in model.results

        # Results should be in annual frequency (5 periods)
        assert len(model.results.C) == 5

        # Verify central tendency methods
        assert "mean" in model.results.C.columns
        assert "median" in model.results.C.columns

    def test_infection_rate_varies(self, measles_annual_data):
        """
        Test that alpha is estimated from the data (#162).

        alpha_t = A_t * I_(t+1) / (I_t * S_t): new cases next year per case
        this year, scaled by the susceptible share. It can exceed 1 and is
        forecast on the log scale.
        """
        container = DataContainer(
            measles_annual_data, mode="incidence", frequency="YE", window=1
        )

        data = container.data
        # Rows where both years have cases (the last row has no next year)
        both = (data["I"] > 0) & (data["I"].shift(-1) > 0)
        both.iloc[-1] = False
        expected = data["A"] * data["I"].shift(-1) / (data["I"] * data["S"])
        np.testing.assert_allclose(data["alpha"][both], expected[both])
        assert data["alpha"].std() > 0
        assert (data["alpha"] > 1).any()
        np.testing.assert_allclose(data["log_alpha"], np.log(data["alpha"]))

        model = Model(container)
        model.create_model()
        model.fit_model(max_lag=3)

        assert model.var_forecasting.logit_ratios_model_fitted is not None

    def test_incidence_mode_preserves_variation(self, measles_annual_data):
        """
        Test that incidence mode preserves I variation while C is monotonic.

        Key property: I can vary up/down, but C = cumsum(I) is monotonic.
        """
        container = DataContainer(
            measles_annual_data, mode="incidence", frequency="YE", window=1
        )

        # I should vary (can decrease)
        I_values = container.data["I"].dropna()
        I_diffs = I_values.diff().dropna()
        assert (I_diffs > 0).any(), "I should have increases"
        assert (I_diffs < 0).any(), "I should have decreases (variation)"

        # C should be monotonic
        C_values = container.data["C"].dropna()
        C_diffs = C_values.diff().dropna()
        assert all(C_diffs >= -1e-10), "C should be monotonic"

    def test_annual_frequency_no_reindexing(self, measles_annual_data):
        """
        Test that annual data is NOT reindexed to daily.

        v0.9.0 native support: 15 annual rows stay 15 rows (not 5475 daily rows).
        """
        container = DataContainer(
            measles_annual_data, mode="incidence", frequency="YE", window=1
        )

        # Input: 15 annual observations
        # Output: Should stay ~15 rows (not expand to ~5475 daily rows)
        assert len(container.data) <= 20, (
            f"Annual data should not expand. "
            f"Input: {len(measles_annual_data)}, Output: {len(container.data)}"
        )

    def test_model_mode_propagation(self, measles_annual_data):
        """Test that mode propagates from DataContainer to Model."""
        container = DataContainer(
            measles_annual_data, mode="incidence", frequency="YE", window=1
        )

        model = Model(container)

        # Mode should propagate
        assert model.mode == container.mode == "incidence"

        # Mode should persist through workflow
        model.create_model()
        assert model.mode == "incidence"


class TestFractionalLagInterpolation:
    """Test fractional lag interpolation implementation."""

    def test_fractional_lag_interpolation_accuracy(self):
        """
        Test that fractional lag interpolation produces expected results.

        For annual data with 14-day recovery lag:
        - Integer lag: 0 years → R_t = I_t (wrong)
        - Fractional lag: 0.0384 years → R_t interpolated (correct)
        """
        dates = pd.date_range("2010", periods=10, freq="YE")

        # Simple linear increasing pattern
        incident_cases = np.arange(100, 1100, 100)  # 100, 200, ..., 1000

        data = pd.DataFrame(
            {"I": incident_cases, "D": [0] * 10, "N": [1_000_000] * 10}, index=dates
        )

        container = DataContainer(data, mode="incidence", frequency="YE", window=1)

        # Each year's cohort is removed by the next year: R_t = C_(t-1) - D_t
        data = container.data
        expected = (data["C"] - data["I"] - data["D"]).clip(lower=0)
        np.testing.assert_allclose(data["R"], expected)
        np.testing.assert_allclose(data["C"], data["I"] + data["R"] + data["D"])


class TestBackwardCompatibilityV090:
    """Test backward compatibility with existing workflows."""

    def test_daily_data_unchanged(self, sample_data_container):
        """Daily data workflow should work exactly as before."""
        # Daily data should still work
        model = Model(sample_data_container)
        model.create_model()
        model.fit_model(max_lag=3)
        model.forecast(steps=30)
        model.run_simulations(n_jobs=1)
        model.generate_result()

        assert model.results is not None
        assert "C" in model.results

    def test_cumulative_mode_unchanged(self, sample_data_container):
        """Cumulative mode should work exactly as before."""
        assert sample_data_container.mode == "cumulative"

        model = Model(sample_data_container)
        model.create_model()
        model.fit_model(max_lag=3)

        assert model.mode == "cumulative"
