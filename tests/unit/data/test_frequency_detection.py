"""Unit tests for frequency detection functionality."""

import warnings

import numpy as np
import pandas as pd
import pytest

from dynasir.data.preprocessing import detect_frequency, warn_frequency_mismatch


class TestDetectFrequency:
    """Test frequency detection function."""

    def test_detect_daily_frequency(self, sample_processed_data):
        """Test detection of daily frequency."""
        freq = detect_frequency(sample_processed_data)
        assert freq == "D"

    def test_detect_weekly_frequency(self, sample_weekly_data):
        """Test detection of weekly frequency."""
        freq = detect_frequency(sample_weekly_data)
        assert freq == "W"

    def test_detect_monthly_frequency(self, sample_monthly_data):
        """Test detection of monthly frequency."""
        freq = detect_frequency(sample_monthly_data)
        assert freq == "M"

    def test_detect_annual_frequency(self, sample_annual_processed_data):
        """Test detection of annual frequency."""
        freq = detect_frequency(sample_annual_processed_data)
        assert freq == "Y"

    def test_detect_frequency_insufficient_data(self):
        """Test that detection fails with insufficient data."""
        single_point = pd.DataFrame(
            {"C": [100], "D": [10], "N": [1000000]},
            index=pd.date_range("2020-01-01", periods=1, freq="D"),
        )

        with pytest.raises(ValueError, match="at least 2 data points"):
            detect_frequency(single_point)

    def test_detect_frequency_irregular_spacing(self):
        """Test that detection fails with irregular spacing."""
        # Create data with irregular gaps that fall between supported frequencies
        # Gaps: 15 days, 50 days, 100 days (median ~50 days)
        # This falls between our M (45 days) and Y (300 days) thresholds
        dates = pd.to_datetime(["2020-01-01", "2020-01-16", "2020-03-06", "2020-06-14"])
        irregular_data = pd.DataFrame(
            {"C": [100, 150, 200, 250], "D": [10, 15, 20, 25], "N": [1000000] * 4},
            index=dates,
        )

        with pytest.raises(ValueError, match="irregular frequency"):
            detect_frequency(irregular_data)

    def test_detect_frequency_edge_case_two_points(self):
        """Test detection with exactly 2 data points."""
        # Daily spacing
        daily_two = pd.DataFrame(
            {"C": [100, 150], "D": [10, 15], "N": [1000000, 1000000]},
            index=pd.date_range("2020-01-01", periods=2, freq="D"),
        )
        assert detect_frequency(daily_two) == "D"

        # Annual spacing
        annual_two = pd.DataFrame(
            {"C": [100, 150], "D": [10, 15], "N": [1000000, 1000000]},
            index=pd.date_range("2015", periods=2, freq="YE"),
        )
        assert detect_frequency(annual_two) == "Y"

    def test_detect_frequency_handles_timedelta_conversion(self):
        """Test that function handles Timedelta conversion correctly."""
        # This tests the bug fix for numpy.float64 vs Timedelta comparison
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        data = pd.DataFrame(
            {
                "C": np.cumsum(np.random.exponential(50, 100)),
                "D": np.cumsum(np.random.exponential(2, 100)),
                "N": [1000000] * 100,
            },
            index=dates,
        )

        # Should not raise TypeError
        freq = detect_frequency(data)
        assert freq == "D"


class TestWarnFrequencyMismatch:
    """Test frequency mismatch warning function."""

    def test_warn_frequency_mismatch_emits_warning(self):
        """Test that warning is emitted for frequency mismatch."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warn_frequency_mismatch("Y", "D", 13516)

            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            assert "FREQUENCY MISMATCH WARNING" in str(w[0].message)
            assert "annual" in str(w[0].message).lower()
            assert "daily" in str(w[0].message).lower()
            assert "13516" in str(w[0].message)

    def test_warn_frequency_mismatch_message_content(self):
        """Test warning message contains all required information."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warn_frequency_mismatch("Y", "D", 13516)

            message = str(w[0].message)
            # Check for key components
            assert "Source data frequency" in message
            assert "Target frequency" in message
            assert "Artificial data points created" in message
            assert "Recommended actions" in message
            assert "v0.9.0" in message  # Mention of future native support

    def test_warn_frequency_mismatch_different_combinations(self):
        """Test warning with different frequency combinations."""
        combinations = [
            ("Y", "D", 13516),  # Annual to daily
            ("M", "D", 730),  # Monthly to daily
            ("W", "D", 105),  # Weekly to daily
        ]

        for detected, target, points in combinations:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                warn_frequency_mismatch(detected, target, points)

                assert len(w) == 1
                assert str(points) in str(w[0].message)


class TestFrequencyDetectionIntegration:
    """Integration tests for frequency detection in preprocessing pipeline."""

    def test_reindex_data_detects_and_warns_annual(self, sample_annual_processed_data):
        """Test that reindex_data detects annual frequency and warns."""
        from dynasir.data.preprocessing import reindex_data

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Reindex annual data to daily (default)
            reindexed = reindex_data(sample_annual_processed_data)

            # Should emit warning
            assert len(w) >= 1
            warning_messages = [str(warning.message) for warning in w]
            assert any(
                "FREQUENCY MISMATCH" in msg for msg in warning_messages
            ), f"Expected frequency mismatch warning. Got: {warning_messages}"

    def test_reindex_data_no_warning_when_freq_matches(
        self, sample_annual_processed_data
    ):
        """Test that no warning is emitted when frequencies match."""
        from dynasir.data.preprocessing import reindex_data

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Reindex annual data to annual (matching)
            reindexed = reindex_data(sample_annual_processed_data, freq="YE")

            # Should NOT emit frequency mismatch warning
            warning_messages = [str(warning.message) for warning in w]
            assert not any(
                "FREQUENCY MISMATCH" in msg for msg in warning_messages
            ), f"Unexpected warning: {warning_messages}"

    def test_reindex_data_warning_can_be_suppressed(self, sample_annual_processed_data):
        """Test that frequency mismatch warning can be suppressed."""
        from dynasir.data.preprocessing import reindex_data

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Suppress warning
            reindexed = reindex_data(
                sample_annual_processed_data, warn_on_mismatch=False
            )

            # Should NOT emit warning
            warning_messages = [str(warning.message) for warning in w]
            assert not any("FREQUENCY MISMATCH" in msg for msg in warning_messages)

    def test_reindex_data_explicit_freq_parameter(self, sample_processed_data):
        """Test reindex_data with explicit freq parameter."""
        from dynasir.data.preprocessing import reindex_data

        # Daily data, explicitly request daily
        reindexed = reindex_data(sample_processed_data, freq="D")

        # Should maintain daily frequency
        assert len(reindexed) == len(sample_processed_data)
        assert reindexed.index.freq == "D"

    def test_reindex_data_backward_compatibility(self, sample_processed_data):
        """Test that reindex_data maintains backward compatibility."""
        from dynasir.data.preprocessing import reindex_data

        # Call without new parameters (v0.7.0 style)
        reindexed = reindex_data(sample_processed_data)

        # Should work and default to daily
        assert len(reindexed) == len(sample_processed_data)
        assert reindexed.index.freq == "D"
