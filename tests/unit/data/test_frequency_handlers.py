"""
Tests for frequency handlers.

Tests the frequency-specific data processing infrastructure that enables
native multi-frequency support (annual, monthly, weekly, daily).
"""

import pandas as pd
import pytest

from dynasir.data.frequency_handlers import (
    AnnualFrequencyHandler,
    DailyFrequencyHandler,
    FrequencyHandler,
    FrequencyHandlerRegistry,
    MonthlyFrequencyHandler,
    WeeklyFrequencyHandler,
    detect_frequency_from_index,
    get_frequency_handler,
)


class TestDailyFrequencyHandler:
    """Test daily frequency handler."""

    @pytest.fixture
    def handler(self):
        return DailyFrequencyHandler()

    @pytest.fixture
    def valid_daily_data(self):
        """Create valid daily data."""
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        data = pd.DataFrame(
            {"C": range(100), "D": range(100), "N": [1e6] * 100}, index=dates
        )
        return data

    def test_handler_attributes(self, handler):
        """Test handler properties."""
        assert handler.frequency_code == "D"
        assert handler.frequency_name == "daily"
        assert handler.periods_per_year == 365.25

    def test_recovery_lag(self, handler):
        """14 days = 14 daily periods."""
        assert handler.get_recovery_lag() == 14

    def test_default_max_lag(self, handler):
        """Daily data supports up to 14 lags."""
        assert handler.get_default_max_lag() == 14

    def test_validate_valid_data(self, handler, valid_daily_data):
        """Should accept valid daily data."""
        handler.validate_data(valid_daily_data)  # Should not raise

    def test_validate_insufficient_data(self, handler):
        """Should reject < 30 daily observations."""
        dates = pd.date_range("2020-01-01", periods=15, freq="D")
        data = pd.DataFrame(
            {"C": range(15), "D": range(15), "N": [1e6] * 15}, index=dates
        )

        with pytest.raises(ValueError, match="at least 30"):
            handler.validate_data(data)

    def test_validate_no_datetime_index(self, handler):
        """Should reject non-DatetimeIndex data."""
        data = pd.DataFrame({"C": range(100), "D": range(100), "N": [1e6] * 100})

        with pytest.raises(ValueError, match="DatetimeIndex"):
            handler.validate_data(data)


class TestWeeklyFrequencyHandler:
    """Test weekly frequency handler."""

    @pytest.fixture
    def handler(self):
        return WeeklyFrequencyHandler()

    @pytest.fixture
    def valid_weekly_data(self):
        """Create valid weekly data."""
        dates = pd.date_range("2020-01-01", periods=60, freq="W")
        data = pd.DataFrame(
            {"C": range(60), "D": range(60), "N": [1e6] * 60}, index=dates
        )
        return data

    def test_handler_attributes(self, handler):
        """Test handler properties."""
        assert handler.frequency_code == "W"
        assert handler.frequency_name == "weekly"
        assert abs(handler.periods_per_year - 52.14) < 0.1

    def test_recovery_lag(self, handler):
        """14 days ≈ 2 weeks."""
        assert handler.get_recovery_lag() == 2

    def test_default_max_lag(self, handler):
        """Weekly data supports up to 8 lags."""
        assert handler.get_default_max_lag() == 8

    def test_validate_valid_data(self, handler, valid_weekly_data):
        """Should accept valid weekly data."""
        handler.validate_data(valid_weekly_data)  # Should not raise

    def test_validate_insufficient_data(self, handler):
        """Should reject < 26 weekly observations."""
        dates = pd.date_range("2020-01-01", periods=20, freq="W")
        data = pd.DataFrame(
            {"C": range(20), "D": range(20), "N": [1e6] * 20}, index=dates
        )

        with pytest.raises(ValueError, match="at least 26"):
            handler.validate_data(data)


class TestMonthlyFrequencyHandler:
    """Test monthly frequency handler."""

    @pytest.fixture
    def handler(self):
        return MonthlyFrequencyHandler()

    @pytest.fixture
    def valid_monthly_data(self):
        """Create valid monthly data."""
        dates = pd.date_range("2010-01-31", periods=60, freq="ME")
        data = pd.DataFrame(
            {"C": range(60), "D": range(60), "N": [1e6] * 60}, index=dates
        )
        return data

    def test_handler_attributes(self, handler):
        """Test handler properties."""
        assert handler.frequency_code == "ME"
        assert handler.frequency_name == "monthly"
        assert handler.periods_per_year == 12

    def test_recovery_lag(self, handler):
        """14 days ≈ 0.47 months (14/30)."""
        assert handler.get_recovery_lag() == pytest.approx(14 / 30, rel=1e-3)

    def test_default_max_lag(self, handler):
        """Monthly data supports up to 6 lags."""
        assert handler.get_default_max_lag() == 6

    def test_validate_valid_data(self, handler, valid_monthly_data):
        """Should accept valid monthly data."""
        handler.validate_data(valid_monthly_data)  # Should not raise

    def test_validate_insufficient_data(self, handler):
        """Should reject < 24 monthly observations."""
        dates = pd.date_range("2020-01-31", periods=12, freq="ME")
        data = pd.DataFrame(
            {"C": range(12), "D": range(12), "N": [1e6] * 12}, index=dates
        )

        with pytest.raises(ValueError, match="at least 24"):
            handler.validate_data(data)


class TestAnnualFrequencyHandler:
    """Test annual frequency handler."""

    @pytest.fixture
    def handler(self):
        return AnnualFrequencyHandler()

    @pytest.fixture
    def valid_annual_data(self):
        """Create valid annual data (measles-like)."""
        dates = pd.date_range("2010-12-31", periods=15, freq="YE")
        incident = [220, 55, 667, 164, 81, 34, 12, 0, 0, 4, 18, 45, 103, 67, 89]
        data = pd.DataFrame(
            {"I": incident, "D": range(15), "N": [120e6] * 15}, index=dates
        )
        return data

    def test_handler_attributes(self, handler):
        """Test handler properties."""
        assert handler.frequency_code == "YE"
        assert handler.frequency_name == "annual"
        assert handler.periods_per_year == 1

    def test_recovery_lag(self, handler):
        """14 days ≈ 0.038 years (14/365)."""
        assert handler.get_recovery_lag() == pytest.approx(14 / 365, rel=1e-3)

    def test_default_max_lag(self, handler):
        """Annual data supports up to 3 lags (sparse)."""
        assert handler.get_default_max_lag() == 3

    def test_min_observations(self, handler):
        """Annual data needs at least 10 years."""
        assert handler.get_min_observations() == 10

    def test_validate_valid_data(self, handler, valid_annual_data):
        """Should accept valid annual data."""
        handler.validate_data(valid_annual_data)  # Should not raise

    def test_validate_insufficient_data(self, handler):
        """Should reject < 10 annual observations."""
        dates = pd.date_range("2010-12-31", periods=5, freq="YE")
        data = pd.DataFrame(
            {"I": range(5), "D": range(5), "N": [120e6] * 5}, index=dates
        )

        with pytest.raises(ValueError, match="at least 10"):
            handler.validate_data(data)

    def test_validate_no_datetime_index(self, handler):
        """Should reject non-DatetimeIndex."""
        data = pd.DataFrame({"I": range(15), "D": range(15), "N": [120e6] * 15})

        with pytest.raises(ValueError, match="DatetimeIndex"):
            handler.validate_data(data)


class TestFrequencyHandlerRegistry:
    """Test frequency handler registry and factory."""

    def test_get_daily(self):
        """Should return daily handler."""
        handler = FrequencyHandlerRegistry.get("D")
        assert isinstance(handler, DailyFrequencyHandler)

    def test_get_weekly(self):
        """Should return weekly handler."""
        handler = FrequencyHandlerRegistry.get("W")
        assert isinstance(handler, WeeklyFrequencyHandler)

    def test_get_monthly_modern(self):
        """Should return monthly handler with modern alias."""
        handler = FrequencyHandlerRegistry.get("ME")
        assert isinstance(handler, MonthlyFrequencyHandler)

    def test_get_monthly_legacy(self):
        """Should return monthly handler with legacy alias."""
        handler = FrequencyHandlerRegistry.get("M")
        assert isinstance(handler, MonthlyFrequencyHandler)

    def test_get_annual_modern(self):
        """Should return annual handler with modern alias."""
        handler = FrequencyHandlerRegistry.get("YE")
        assert isinstance(handler, AnnualFrequencyHandler)

    def test_get_annual_legacy(self):
        """Should return annual handler with legacy alias."""
        handler = FrequencyHandlerRegistry.get("Y")
        assert isinstance(handler, AnnualFrequencyHandler)

    def test_get_friendly_names(self):
        """Should accept friendly frequency names."""
        assert isinstance(FrequencyHandlerRegistry.get("daily"), DailyFrequencyHandler)
        assert isinstance(
            FrequencyHandlerRegistry.get("weekly"), WeeklyFrequencyHandler
        )
        assert isinstance(
            FrequencyHandlerRegistry.get("monthly"), MonthlyFrequencyHandler
        )
        assert isinstance(
            FrequencyHandlerRegistry.get("annual"), AnnualFrequencyHandler
        )

    def test_get_case_insensitive(self):
        """Registry should be case-insensitive."""
        h1 = FrequencyHandlerRegistry.get("annual")
        h2 = FrequencyHandlerRegistry.get("ANNUAL")
        h3 = FrequencyHandlerRegistry.get("Annual")

        assert type(h1) == type(h2) == type(h3)

    def test_invalid_frequency(self):
        """Should raise error for invalid frequency."""
        with pytest.raises(ValueError, match="Unsupported frequency"):
            FrequencyHandlerRegistry.get("INVALID")

    def test_get_all_handlers(self):
        """Should return all unique handlers."""
        handlers = FrequencyHandlerRegistry.get_all_handlers()

        assert "D" in handlers
        assert "W" in handlers
        assert "ME" in handlers
        assert "YE" in handlers
        # Legacy aliases should not be in results
        assert "M" not in handlers or "M" == "ME"


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_frequency_handler(self):
        """Test get_frequency_handler convenience function."""
        handler = get_frequency_handler("annual")
        assert isinstance(handler, AnnualFrequencyHandler)
        assert handler.get_recovery_lag() == pytest.approx(14 / 365, rel=1e-3)
        assert handler.get_default_max_lag() == 3

    def test_detect_frequency_daily(self):
        """Detect daily frequency."""
        dates = pd.date_range("2020-01-01", periods=30, freq="D")
        freq = detect_frequency_from_index(dates)
        assert freq == "D"

    def test_detect_frequency_weekly(self):
        """Detect weekly frequency."""
        dates = pd.date_range("2020-01-01", periods=26, freq="W")
        freq = detect_frequency_from_index(dates)
        assert freq == "W"

    def test_detect_frequency_monthly(self):
        """Detect monthly frequency."""
        dates = pd.date_range("2020-01-31", periods=12, freq="ME")
        freq = detect_frequency_from_index(dates)
        assert freq in ("ME", "M")

    def test_detect_frequency_annual(self):
        """Detect annual frequency."""
        dates = pd.date_range("2010-12-31", periods=10, freq="YE")
        freq = detect_frequency_from_index(dates)
        assert freq in ("YE", "Y")

    def test_detect_frequency_insufficient_data(self):
        """Should raise error with insufficient data."""
        dates = pd.date_range("2020-01-01", periods=1, freq="D")

        with pytest.raises(ValueError, match="at least 2"):
            detect_frequency_from_index(dates)


class TestFrequencyHandlerInterfaces:
    """Test that all handlers implement required interface."""

    @pytest.mark.parametrize("frequency", ["D", "W", "ME", "YE"])
    def test_all_handlers_have_interface(self, frequency):
        """All handlers should have required methods."""
        handler = FrequencyHandlerRegistry.get(frequency)

        # Check required attributes
        assert hasattr(handler, "frequency_code")
        assert hasattr(handler, "frequency_name")
        assert hasattr(handler, "periods_per_year")

        # Check required methods
        assert callable(handler.validate_data)
        assert callable(handler.get_recovery_lag)
        assert callable(handler.get_default_max_lag)
        assert callable(handler.get_min_observations)

        # Check return types
        assert isinstance(handler.get_recovery_lag(), (int, float))
        assert handler.get_recovery_lag() > 0
        assert isinstance(handler.get_default_max_lag(), int)
        assert handler.get_default_max_lag() >= 1
        assert isinstance(handler.get_min_observations(), int)

    @pytest.mark.parametrize("frequency", ["D", "W", "ME", "YE"])
    def test_recovery_lag_proportional_to_frequency(self, frequency):
        """Recovery lag should be appropriate for each frequency."""
        handler = FrequencyHandlerRegistry.get(frequency)
        lag = handler.get_recovery_lag()

        # Recovery lags should be reasonable in each frequency's units
        # Daily: ~14 periods (days)
        # Weekly: ~2 periods (weeks, ~14 days)
        # Monthly: ~0.47 periods (~14 days)
        # Annual: ~0.038 periods (~14 days)
        if frequency == "D":
            assert 10 < lag < 20
        elif frequency == "W":
            assert 1.5 < lag < 3
        elif frequency == "ME":
            assert 0.4 < lag < 0.5
        elif frequency == "YE":
            assert 0.03 < lag < 0.05

    @pytest.mark.parametrize("frequency", ["D", "W", "ME", "YE"])
    def test_max_lag_inversely_proportional_to_frequency(self, frequency):
        """Max lag should decrease with fewer data points."""
        handler = FrequencyHandlerRegistry.get(frequency)
        max_lag = handler.get_default_max_lag()

        # Annual (sparse) should have smaller lag than daily (rich)
        if frequency == "YE":
            assert max_lag <= 3
        elif frequency == "D":
            assert max_lag >= 10
