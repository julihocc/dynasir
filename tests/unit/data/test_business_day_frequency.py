"""Unit tests for business day frequency handler."""

import pandas as pd
import pytest

from dynasir.data.frequency_handlers import (
    BusinessDayFrequencyHandler,
    FrequencyHandlerRegistry,
)


class TestBusinessDayFrequencyHandler:
    """Test business day frequency handler."""

    @pytest.fixture
    def handler(self):
        """Create handler instance."""
        return BusinessDayFrequencyHandler()

    @pytest.fixture
    def business_day_data(self):
        """Generate business day data."""
        # Create business day index (Mon-Fri)
        dates = pd.bdate_range("2024-01-01", periods=60, freq="B")
        data = pd.DataFrame(
            {
                "C": range(1, 61),
                "D": range(1, 61),
            },
            index=dates,
        )
        return data

    def test_handler_attributes(self, handler):
        """Test handler attributes."""
        assert handler.frequency_code == "B"
        assert handler.frequency_name == "business day"
        assert handler.periods_per_year == 252

    def test_recovery_lag(self, handler):
        """14 days ≈ 10 business days."""
        assert handler.get_recovery_lag() == 10

    def test_default_max_lag(self, handler):
        """Business day uses 10 lags."""
        assert handler.get_default_max_lag() == 10

    def test_min_observations(self, handler):
        """Business day requires at least 60 observations."""
        assert handler.get_min_observations() == 60

    def test_validate_valid_data(self, handler, business_day_data):
        """Valid business day data passes validation."""
        handler.validate_data(business_day_data)  # Should not raise

    def test_validate_insufficient_data(self, handler):
        """Insufficient data raises error."""
        small_data = pd.DataFrame(
            {
                "C": [1, 2],
            },
            index=pd.bdate_range("2024-01-01", periods=2, freq="B"),
        )

        with pytest.raises(ValueError, match="at least 30 observations"):
            handler.validate_data(small_data)

    def test_validate_no_datetime_index(self, handler):
        """Non-datetime index raises error."""
        bad_data = pd.DataFrame(
            {
                "C": range(30),
            }
        )

        with pytest.raises(ValueError, match="DatetimeIndex"):
            handler.validate_data(bad_data)


class TestBusinessDayRegistry:
    """Test business day in handler registry."""

    def test_registry_has_business_day(self):
        """Registry supports business day codes."""
        handler = FrequencyHandlerRegistry.get("B")
        assert isinstance(handler, BusinessDayFrequencyHandler)

    def test_registry_friendly_names(self):
        """Registry supports business day friendly names."""
        for name in ["business day", "businessday", "bday"]:
            handler = FrequencyHandlerRegistry.get(name)
            assert isinstance(handler, BusinessDayFrequencyHandler)

    def test_registry_case_insensitive(self):
        """Registry is case insensitive."""
        handler_b = FrequencyHandlerRegistry.get("b")
        handler_B = FrequencyHandlerRegistry.get("B")

        assert type(handler_b) == type(handler_B)
        assert isinstance(handler_b, BusinessDayFrequencyHandler)


class TestBusinessDayIntegration:
    """Integration tests with DataContainer."""

    def test_business_day_with_container(self):
        """Test business day data with DataContainer."""
        from dynasir import DataContainer

        dates = pd.bdate_range("2024-01-01", periods=60, freq="B")
        data = pd.DataFrame(
            {
                "C": range(1, 61),
                "D": range(1, 61),
                "N": [1000000] * 60,
            },
            index=dates,
        )

        container = DataContainer(data, mode="cumulative", frequency="B")

        assert container.frequency == "B"
        assert container.handler.frequency_name == "business day"
        assert container.handler.get_recovery_lag() == 10
        assert container.handler.get_default_max_lag() == 10

    def test_business_day_vs_daily_comparison(self):
        """Business day should have ~252 periods vs daily ~365."""
        daily_handler = FrequencyHandlerRegistry.get("D")
        bday_handler = FrequencyHandlerRegistry.get("B")

        assert bday_handler.periods_per_year == 252
        assert daily_handler.periods_per_year == 365.25

        # Business day recovery lag should be less than daily (10 vs 14)
        assert bday_handler.get_recovery_lag() < daily_handler.get_recovery_lag()
