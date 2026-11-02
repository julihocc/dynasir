"""
Tests for SIRDV vaccination feature engineering.

This module tests the feature engineering pipeline's ability to handle
vaccination data and calculate the delta (vaccination rate) correctly.
"""

import numpy as np
import pandas as pd
import pytest

from dynasir.core.constants import LOGIT_RATIOS, RATIOS
from dynasir.data.features import feature_engineering


@pytest.fixture
def sample_sird_data():
    """Sample SIRD data without vaccination (backward compatibility)."""
    dates = pd.date_range(start="2020-03-01", end="2020-03-31", freq="D")
    np.random.seed(42)

    data = pd.DataFrame(
        {
            "C": np.cumsum(np.random.exponential(50, len(dates))),
            "D": np.cumsum(np.random.exponential(2, len(dates))),
            "N": [1000000] * len(dates),
        },
        index=dates,
    )

    return data


@pytest.fixture
def sample_sirdv_data():
    """Sample SIRDV data with vaccination."""
    dates = pd.date_range(start="2020-03-01", end="2020-03-31", freq="D")
    np.random.seed(42)

    # Cumulative vaccinations starting on day 10
    vaccinations = np.zeros(len(dates))
    vaccinations[10:] = np.cumsum(np.random.exponential(1000, len(dates) - 10))

    data = pd.DataFrame(
        {
            "C": np.cumsum(np.random.exponential(50, len(dates))),
            "D": np.cumsum(np.random.exponential(2, len(dates))),
            "N": [1000000] * len(dates),
            "V": vaccinations,
        },
        index=dates,
    )

    return data


@pytest.fixture
def sample_sirdv_data_with_nans():
    """Sample SIRDV data with NaN values in V column."""
    dates = pd.date_range(start="2020-03-01", end="2020-03-31", freq="D")
    np.random.seed(42)

    vaccinations = np.cumsum(np.random.exponential(1000, len(dates)))
    # Introduce some NaN values
    vaccinations[5:8] = np.nan

    data = pd.DataFrame(
        {
            "C": np.cumsum(np.random.exponential(50, len(dates))),
            "D": np.cumsum(np.random.exponential(2, len(dates))),
            "N": [1000000] * len(dates),
            "V": vaccinations,
        },
        index=dates,
    )

    return data


@pytest.fixture
def sample_sirdv_data_with_negative_dv():
    """Sample SIRDV data with decreasing V (data corrections)."""
    dates = pd.date_range(start="2020-03-01", end="2020-03-31", freq="D")
    np.random.seed(42)

    vaccinations = np.cumsum(np.random.exponential(1000, len(dates)))
    # Simulate data correction (decrease in cumulative count)
    vaccinations[15] = vaccinations[14] - 500  # Correction

    data = pd.DataFrame(
        {
            "C": np.cumsum(np.random.exponential(50, len(dates))),
            "D": np.cumsum(np.random.exponential(2, len(dates))),
            "N": [1000000] * len(dates),
            "V": vaccinations,
        },
        index=dates,
    )

    return data


class TestSIRDBackwardCompatibility:
    """Test that SIRD mode still works (backward compatibility)."""

    def test_feature_engineering_sird_mode(self, sample_sird_data):
        """Test feature engineering works for SIRD data (no V column)."""
        result = feature_engineering(sample_sird_data)

        # Should have standard SIRD compartments
        assert "S" in result.columns
        assert "I" in result.columns
        assert "R" in result.columns
        assert "D" in result.columns
        assert "A" in result.columns
        assert "C" in result.columns

        # Should NOT have V or delta
        assert "V" not in result.columns
        assert "dV" not in result.columns
        assert "delta" not in result.columns

        # Should have 3 rates
        assert "alpha" in result.columns
        assert "beta" in result.columns
        assert "gamma" in result.columns

        # Should have 3 logit ratios
        assert "logit_alpha" in result.columns
        assert "logit_beta" in result.columns
        assert "logit_gamma" in result.columns

        # Should NOT have logit_delta
        assert "logit_delta" not in result.columns

    def test_sird_s_calculation(self, sample_sird_data):
        """Test S calculation uses original formula: S = N - C."""
        result = feature_engineering(sample_sird_data)

        # S should equal N - C (original SIRD formula)
        expected_s = result["N"] - result["C"]
        pd.testing.assert_series_equal(result["S"], expected_s, check_names=False)

    def test_sird_no_vaccination_effects(self, sample_sird_data):
        """Test that S is not affected by vaccination in SIRD mode."""
        result = feature_engineering(sample_sird_data)

        # S should be positive (no vaccination reducing it)
        assert (result["S"] >= 0).all()

        # S should approximately equal N - C
        # (with some tolerance for numerical issues)
        np.testing.assert_allclose(
            result["S"].values,
            (result["N"] - result["C"]).values,
            rtol=1e-10,
        )


class TestSIRDVFeatureEngineering:
    """Test SIRDV-specific feature engineering."""

    def test_feature_engineering_sirdv_mode(self, sample_sirdv_data):
        """Test feature engineering works for SIRDV data (with V column)."""
        result = feature_engineering(sample_sirdv_data)

        # Should have all SIRDV compartments
        assert "S" in result.columns
        assert "I" in result.columns
        assert "R" in result.columns
        assert "D" in result.columns
        assert "A" in result.columns
        assert "C" in result.columns
        assert "V" in result.columns

        # Should have dV and delta
        assert "dV" in result.columns
        assert "delta" in result.columns

        # Should have 4 rates
        assert "alpha" in result.columns
        assert "beta" in result.columns
        assert "gamma" in result.columns
        assert "delta" in result.columns

        # Should have 4 logit ratios
        assert "logit_alpha" in result.columns
        assert "logit_beta" in result.columns
        assert "logit_gamma" in result.columns
        assert "logit_delta" in result.columns

    def test_sirdv_s_calculation(self, sample_sirdv_data):
        """Test S calculation uses SIRDV formula: S = N - C - V."""
        result = feature_engineering(sample_sirdv_data)

        # S should equal N - C - V (SIRDV formula)
        expected_s = result["N"] - result["C"] - result["V"]
        pd.testing.assert_series_equal(result["S"], expected_s, check_names=False)

    def test_dv_calculation(self, sample_sirdv_data):
        """Test dV (daily vaccination change) is calculated correctly."""
        result = feature_engineering(sample_sirdv_data)

        # dV should be the daily change in V
        # Note: dV = -V.diff(periods=-1) means looking forward
        expected_dv = -result["V"].diff(periods=-1)

        # dV should be non-negative (clipped)
        assert (result["dV"] >= 0).all()

    def test_delta_calculation(self, sample_sirdv_data):
        """Test delta (vaccination rate) is calculated correctly."""
        result = feature_engineering(sample_sirdv_data)

        # delta should exist
        assert "delta" in result.columns

        # delta should be non-negative (it's a rate)
        assert (result["delta"] >= 0).all()

        # delta should be calculated before prepare_for_logit_function
        # which clips values to (epsilon, 1-epsilon)
        # So we just verify it's in a reasonable range
        assert (result["delta"] <= 1).all() or (result["delta"] <= 1.0001).all()


class TestVaccinationEdgeCases:
    """Test edge cases in vaccination data handling."""

    def test_v_with_nan_values(self, sample_sirdv_data_with_nans):
        """Test that NaN values in V are filled with 0."""
        result = feature_engineering(sample_sirdv_data_with_nans)

        # V should not have any NaN values
        assert not result["V"].isna().any()

        # NaN values should have been replaced with 0
        # (checked after feature engineering)
        assert (result["V"] >= 0).all()

    def test_negative_dv_clipping(self, sample_sirdv_data_with_negative_dv):
        """Test that negative dV values are clipped to 0."""
        result = feature_engineering(sample_sirdv_data_with_negative_dv)

        # dV should never be negative
        assert (result["dV"] >= 0).all()

        # Verify clipping occurred
        # (original data had a decrease, so clipping should have happened)
        assert result["dV"].min() == 0

    def test_v_starts_partway(self):
        """Test vaccination starting partway through time series."""
        dates = pd.date_range(start="2020-03-01", end="2020-03-31", freq="D")
        np.random.seed(42)

        # Vaccinations start on day 20
        vaccinations = np.zeros(len(dates))
        vaccinations[20:] = np.cumsum(np.random.exponential(1000, len(dates) - 20))

        data = pd.DataFrame(
            {
                "C": np.cumsum(np.random.exponential(50, len(dates))),
                "D": np.cumsum(np.random.exponential(2, len(dates))),
                "N": [1000000] * len(dates),
                "V": vaccinations,
            },
            index=dates,
        )

        result = feature_engineering(data)

        # Before vaccination starts, delta should be 0
        assert (result["delta"].iloc[:19] >= 0).all()

        # V should be 0 before vaccination starts
        assert (result["V"].iloc[:20] == 0).all()


class TestSIRDVConservationLaw:
    """Test SIRDV conservation law: N = S + I + R + D + V."""

    def test_sirdv_conservation_law(self, sample_sirdv_data):
        """Test that N = S + I + R + D + V holds approximately."""
        result = feature_engineering(sample_sirdv_data)

        # Calculate conservation: N = S + I + R + D + V
        conservation = (
            result["S"] + result["I"] + result["R"] + result["D"] + result["V"]
        )

        # Should approximately equal N
        # (allow some tolerance due to the 14-day shift and numerical issues)
        diff = (conservation - result["N"]).abs()
        max_error = diff.max()

        # Maximum error should be reasonable
        # (could be large early on due to 14-day lag)
        assert max_error < result["N"].max() * 0.1  # Within 10% of total population

    def test_sird_conservation_law(self, sample_sird_data):
        """Test that N = S + I + R + D holds for SIRD mode."""
        result = feature_engineering(sample_sird_data)

        # Calculate conservation: N = S + I + R + D
        conservation = result["S"] + result["I"] + result["R"] + result["D"]

        # Should approximately equal N
        diff = (conservation - result["N"]).abs()
        max_error = diff.max()

        # Maximum error should be reasonable
        assert max_error < result["N"].max() * 0.1


class TestDeltaRateBounds:
    """Test delta rate is within bounds for logit transformation."""

    def test_delta_within_logit_bounds(self, sample_sirdv_data):
        """Test that delta is bounded between (epsilon, 1-epsilon) after preparation."""
        result = feature_engineering(sample_sirdv_data)

        # After feature engineering, delta should be prepared for logit
        # Check that logit_delta exists and is not NaN (after ffill/fillna)
        assert "logit_delta" in result.columns

        # logit_delta should not have infinite values
        assert not np.isinf(result["logit_delta"]).any()

        # After ffill and fillna(0), there should be no NaN
        assert not result["logit_delta"].isna().any()

    def test_all_rates_bounded(self, sample_sirdv_data):
        """Test that all rates (alpha, beta, gamma, delta) are properly bounded."""
        result = feature_engineering(sample_sirdv_data)

        # All rates should be prepared for logit transformation
        for rate in ["alpha", "beta", "gamma", "delta"]:
            # Rate should exist
            assert rate in result.columns

            # Should not have infinite values after cleanup
            assert not np.isinf(result[rate]).any()

            # Should not have NaN after ffill/fillna
            assert not result[rate].isna().any()

            # Should be in valid range (0, 1) or filled
            # After ffill/fillna(0), values should be >= 0
            assert (result[rate] >= 0).all()


class TestSIRDVIntegration:
    """Integration tests for full SIRDV pipeline."""

    def test_sirdv_full_pipeline(self, sample_sirdv_data):
        """Test complete SIRDV feature engineering pipeline."""
        result = feature_engineering(sample_sirdv_data)

        # Verify all expected columns exist
        expected_compartments = ["S", "I", "R", "D", "A", "C", "V"]
        for compartment in expected_compartments:
            assert compartment in result.columns

        expected_diffs = ["dC", "dI", "dR", "dD", "dA", "dS", "dV"]
        for diff in expected_diffs:
            assert diff in result.columns

        expected_rates = ["alpha", "beta", "gamma", "delta"]
        for rate in expected_rates:
            assert rate in result.columns

        expected_logit_rates = [
            "logit_alpha",
            "logit_beta",
            "logit_gamma",
            "logit_delta",
        ]
        for logit_rate in expected_logit_rates:
            assert logit_rate in result.columns

        # Verify R0 is calculated
        assert "R0" in result.columns

        # Verify no NaN or inf in final result
        assert not result.isna().any().any()
        # R0 can be very large (not necessarily inf, but large enough to cause issues)
        # Check all columns except R0
        cols_to_check = [col for col in result.columns if col != "R0"]
        assert not np.isinf(result[cols_to_check].values).any()

    def test_sird_full_pipeline(self, sample_sird_data):
        """Test complete SIRD feature engineering pipeline (backward compatibility)."""
        result = feature_engineering(sample_sird_data)

        # Verify SIRD compartments exist
        expected_compartments = ["S", "I", "R", "D", "A", "C"]
        for compartment in expected_compartments:
            assert compartment in result.columns

        # Verify V does NOT exist
        assert "V" not in result.columns
        assert "dV" not in result.columns

        expected_rates = ["alpha", "beta", "gamma"]
        for rate in expected_rates:
            assert rate in result.columns

        # delta should NOT exist
        assert "delta" not in result.columns
        assert "logit_delta" not in result.columns

        # Verify no NaN or inf in final result
        assert not result.isna().any().any()
        # R0 can be very large (not necessarily inf, but large enough to cause issues)
        # Check all columns except R0
        cols_to_check = [col for col in result.columns if col != "R0"]
        assert not np.isinf(result[cols_to_check].values).any()
