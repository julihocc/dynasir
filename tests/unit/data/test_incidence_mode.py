"""
Tests for incidence mode feature engineering.

This module tests the new incidence mode where:
- I (incident cases) is the input data that can vary up/down
- C (cumulative cases) is derived from I via cumsum
- Suitable for eliminated diseases like measles with sporadic outbreaks
"""

import numpy as np
import pandas as pd
import pytest

from dynasir.data.features import feature_engineering


class TestIncidenceModeBasics:
    """Test basic incidence mode feature engineering."""

    def test_incidence_mode_accepts_i_column(self):
        """Incidence mode should accept I (incident cases) as input."""
        data = pd.DataFrame(
            {"I": [100, 50, 75, 30, 45], "D": [5, 8, 10, 12, 14], "N": [10000] * 5},
            index=pd.date_range("2020-01-01", periods=5, freq="YE"),
        )

        result = feature_engineering(data, mode="incidence")

        # I should be preserved
        assert "I" in result.columns
        pd.testing.assert_series_equal(result["I"], data["I"], check_names=False)

    def test_incidence_mode_calculates_c_from_i(self):
        """In incidence mode, C should be cumsum of I."""
        data = pd.DataFrame(
            {"I": [100, 50, 75, 30, 45], "D": [5, 8, 10, 12, 14], "N": [10000] * 5},
            index=pd.date_range("2020-01-01", periods=5, freq="YE"),
        )

        result = feature_engineering(data, mode="incidence")

        expected_c = data["I"].cumsum()
        assert "C" in result.columns
        pd.testing.assert_series_equal(
            result["C"], expected_c, check_names=False, atol=1
        )

    def test_incidence_mode_i_can_decrease(self):
        """Incidence mode should allow I to decrease (sporadic outbreaks)."""
        # Simulate measles: high outbreak year, then low incidence
        data = pd.DataFrame(
            {
                "I": [220, 55, 667, 164, 81],  # Varies up and down
                "D": [1, 0, 2, 1, 0],
                "N": [100000] * 5,
            },
            index=pd.date_range("2015-01-01", periods=5, freq="YE"),
        )

        result = feature_engineering(data, mode="incidence")

        # I should preserve the variation
        assert result["I"].iloc[1] < result["I"].iloc[0]  # Decrease
        assert result["I"].iloc[2] > result["I"].iloc[1]  # Increase

        # C should still be monotonic (cumulative)
        assert all(result["C"].diff().dropna() >= 0)

    def test_incidence_mode_dc_equals_i(self):
        """In incidence mode, dC should equal I (incident cases)."""
        data = pd.DataFrame(
            {"I": [100, 50, 75, 30, 45], "D": [5, 8, 10, 12, 14], "N": [10000] * 5},
            index=pd.date_range("2020-01-01", periods=5, freq="YE"),
        )

        result = feature_engineering(data, mode="incidence")

        # dC = I (incident cases per period)
        assert "dC" in result.columns
        pd.testing.assert_series_equal(result["dC"], result["I"], check_names=False)


class TestIncidenceModeCompartments:
    """Test SIRD compartment calculations in incidence mode."""

    def test_incidence_mode_calculates_s(self):
        """Susceptible (S) should be N - C."""
        data = pd.DataFrame(
            {"I": [100, 50, 75, 30, 45], "D": [5, 8, 10, 12, 14], "N": [10000] * 5},
            index=pd.date_range("2020-01-01", periods=5, freq="YE"),
        )

        result = feature_engineering(data, mode="incidence")

        # S = N - C (simplified model)
        expected_s = result["N"] - result["C"]
        assert "S" in result.columns
        pd.testing.assert_series_equal(
            result["S"], expected_s, check_names=False, atol=1
        )

    def test_incidence_mode_calculates_r(self):
        """Recovered (R) should be calculated from lagged cumulative I."""
        data = pd.DataFrame(
            {"I": [100, 50, 75, 30, 45], "D": [5, 8, 10, 12, 14], "N": [10000] * 5},
            index=pd.date_range("2020-01-01", periods=5, freq="YE"),
        )

        result = feature_engineering(data, mode="incidence")

        # R should be non-negative
        assert "R" in result.columns
        assert all(result["R"] >= 0)

        # R should be less than C (not all cases recovered yet)
        assert all(result["R"] <= result["C"])

    def test_incidence_mode_calculates_a(self):
        """Active population (A) should be S + I."""
        data = pd.DataFrame(
            {"I": [100, 50, 75, 30, 45], "D": [5, 8, 10, 12, 14], "N": [10000] * 5},
            index=pd.date_range("2020-01-01", periods=5, freq="YE"),
        )

        result = feature_engineering(data, mode="incidence")

        expected_a = result["S"] + result["I"]
        assert "A" in result.columns
        pd.testing.assert_series_equal(
            result["A"], expected_a, check_names=False, atol=1
        )


class TestIncidenceModeRates:
    """Test epidemiological rate calculations in incidence mode."""

    def test_incidence_mode_calculates_alpha(self):
        """Infection rate (alpha) should be calculated from A, dC, I, S."""
        data = pd.DataFrame(
            {"I": [100, 50, 75, 30, 45], "D": [5, 8, 10, 12, 14], "N": [10000] * 5},
            index=pd.date_range("2020-01-01", periods=5, freq="YE"),
        )

        result = feature_engineering(data, mode="incidence")

        # alpha = (A * dC) / (I * S)
        assert "alpha" in result.columns
        assert all(result["alpha"].dropna() >= 0)

    def test_incidence_mode_calculates_beta(self):
        """Recovery rate (beta) should be dR / I."""
        data = pd.DataFrame(
            {"I": [100, 50, 75, 30, 45], "D": [5, 8, 10, 12, 14], "N": [10000] * 5},
            index=pd.date_range("2020-01-01", periods=5, freq="YE"),
        )

        result = feature_engineering(data, mode="incidence")

        assert "beta" in result.columns
        assert all(result["beta"].dropna() >= 0)

    def test_incidence_mode_calculates_gamma(self):
        """Mortality rate (gamma) should be dD / I."""
        data = pd.DataFrame(
            {"I": [100, 50, 75, 30, 45], "D": [5, 8, 10, 12, 14], "N": [10000] * 5},
            index=pd.date_range("2020-01-01", periods=5, freq="YE"),
        )

        result = feature_engineering(data, mode="incidence")

        assert "gamma" in result.columns
        assert all(result["gamma"].dropna() >= 0)

    def test_incidence_mode_calculates_r0(self):
        """R0 should be alpha / (beta + gamma)."""
        data = pd.DataFrame(
            {"I": [100, 50, 75, 30, 45], "D": [5, 8, 10, 12, 14], "N": [10000] * 5},
            index=pd.date_range("2020-01-01", periods=5, freq="YE"),
        )

        result = feature_engineering(data, mode="incidence")

        assert "R0" in result.columns
        # R0 should be positive where defined
        assert all(result["R0"].dropna() > 0)


class TestIncidenceVsCumulativeMode:
    """Compare incidence and cumulative modes."""

    def test_cumulative_mode_requires_c_column(self):
        """Cumulative mode should require C (cumulative cases)."""
        data = pd.DataFrame(
            {"C": [100, 150, 225, 255, 300], "D": [5, 8, 10, 12, 14], "N": [10000] * 5},
            index=pd.date_range("2020-01-01", periods=5, freq="D"),
        )

        result = feature_engineering(data, mode="cumulative")

        # C should be preserved
        assert "C" in result.columns
        pd.testing.assert_series_equal(result["C"], data["C"], check_names=False)

    def test_cumulative_mode_derives_i_from_c(self):
        """Cumulative mode should derive I from C - R - D."""
        data = pd.DataFrame(
            {"C": [100, 150, 225, 255, 300], "D": [5, 8, 10, 12, 14], "N": [10000] * 5},
            index=pd.date_range("2020-01-01", periods=5, freq="D"),
        )

        result = feature_engineering(data, mode="cumulative")

        # I = C - R - D
        assert "I" in result.columns
        assert all(result["I"] >= 0)

    def test_modes_use_same_rate_formulas(self):
        """Both modes should use identical rate calculation formulas."""
        # Create data where I pattern is same in both modes
        data_cumulative = pd.DataFrame(
            {"C": [100, 150, 225, 255, 300], "D": [5, 8, 10, 12, 14], "N": [10000] * 5},
            index=pd.date_range("2020-01-01", periods=5, freq="D"),
        )

        data_incidence = pd.DataFrame(
            {
                "I": [100, 50, 75, 30, 45],  # Matches dC from cumulative
                "D": [5, 8, 10, 12, 14],
                "N": [10000] * 5,
            },
            index=pd.date_range("2020-01-01", periods=5, freq="D"),
        )

        result_cum = feature_engineering(data_cumulative, mode="cumulative")
        result_inc = feature_engineering(data_incidence, mode="incidence")

        # Both should have same rate columns
        rate_columns = ["alpha", "beta", "gamma", "R0"]
        assert all(col in result_cum.columns for col in rate_columns)
        assert all(col in result_inc.columns for col in rate_columns)


class TestIncidenceModeValidation:
    """Test validation and edge cases for incidence mode."""

    def test_invalid_mode_raises_error(self):
        """Invalid mode parameter should raise ValueError."""
        data = pd.DataFrame(
            {"I": [100, 50, 75], "D": [5, 8, 10], "N": [10000] * 3},
            index=pd.date_range("2020-01-01", periods=3, freq="D"),
        )

        with pytest.raises(ValueError, match="Invalid mode"):
            feature_engineering(data, mode="invalid_mode")

    def test_incidence_mode_handles_zero_i(self):
        """Incidence mode should handle periods with zero incident cases."""
        data = pd.DataFrame(
            {
                "I": [100, 0, 75, 0, 45],  # Some zero incidents
                "D": [5, 8, 10, 12, 14],
                "N": [10000] * 5,
            },
            index=pd.date_range("2020-01-01", periods=5, freq="YE"),
        )

        result = feature_engineering(data, mode="incidence")

        # Should not raise errors
        assert "C" in result.columns
        assert all(result["C"].diff().dropna() >= 0)  # C still monotonic

    def test_incidence_mode_with_small_population(self):
        """Incidence mode should work with small population sizes."""
        data = pd.DataFrame(
            {
                "I": [10, 5, 15, 3, 8],
                "D": [0, 1, 0, 1, 0],
                "N": [1000] * 5,  # Small population
            },
            index=pd.date_range("2020-01-01", periods=5, freq="YE"),
        )

        result = feature_engineering(data, mode="incidence")

        # Should calculate all compartments
        assert all(col in result.columns for col in ["S", "I", "R", "D", "A"])


class TestIncidenceModeSIRDV:
    """Test incidence mode with vaccination (SIRDV)."""

    def test_incidence_mode_with_vaccination(self):
        """Incidence mode should support vaccination column V."""
        data = pd.DataFrame(
            {
                "I": [100, 50, 75, 30, 45],
                "D": [5, 8, 10, 12, 14],
                "V": [0, 1000, 2500, 4000, 5500],  # Cumulative vaccination
                "N": [10000] * 5,
            },
            index=pd.date_range("2020-01-01", periods=5, freq="YE"),
        )

        result = feature_engineering(data, mode="incidence")

        # Should have SIRDV columns
        assert "V" in result.columns
        assert "dV" in result.columns
        assert "delta" in result.columns

    def test_incidence_sirdv_s_calculation(self):
        """In SIRDV incidence mode, S = N - C - V."""
        data = pd.DataFrame(
            {
                "I": [100, 50, 75, 30, 45],
                "D": [5, 8, 10, 12, 14],
                "V": [0, 1000, 2500, 4000, 5500],
                "N": [10000] * 5,
            },
            index=pd.date_range("2020-01-01", periods=5, freq="YE"),
        )

        result = feature_engineering(data, mode="incidence")

        # S = N - C - V
        expected_s = result["N"] - result["C"] - result["V"]
        pd.testing.assert_series_equal(
            result["S"], expected_s, check_names=False, atol=1
        )


class TestIncidenceModeRealWorld:
    """Test incidence mode with realistic measles data patterns."""

    def test_measles_annual_pattern(self):
        """Test with realistic measles annual case counts."""
        # Based on Mexico measles data: sporadic outbreaks
        data = pd.DataFrame(
            {
                "I": [220, 55, 667, 164, 81, 34, 0, 0, 12, 4],  # Varying annual cases
                "D": [1, 0, 2, 1, 0, 0, 0, 0, 0, 0],
                "N": [120000000] * 10,  # Mexico population
            },
            index=pd.date_range("2010-01-01", periods=10, freq="YE"),
        )

        result = feature_engineering(data, mode="incidence")

        # Should handle the outbreak in 2012 (667 cases)
        assert result["I"].max() == 667

        # Should handle zero-incidence years (elimination periods)
        assert (result["I"] == 0).any()

        # C should still accumulate
        assert all(result["C"].diff().dropna() >= 0)

    def test_post_elimination_reintroduction(self):
        """Test pattern where disease is eliminated then reintroduced."""
        data = pd.DataFrame(
            {
                "I": [
                    50,
                    20,
                    5,
                    0,
                    0,
                    0,
                    15,
                    45,
                    30,
                    10,
                ],  # Elimination then reintroduction
                "D": [0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
                "N": [50000000] * 10,
            },
            index=pd.date_range("2010-01-01", periods=10, freq="YE"),
        )

        result = feature_engineering(data, mode="incidence")

        # Should show zero incidence during elimination
        elimination_period = result["I"].iloc[3:6]
        assert all(elimination_period == 0)

        # Should show reintroduction
        assert result["I"].iloc[6] > 0

        # C should still be monotonic
        assert all(result["C"].diff().dropna() >= 0)
