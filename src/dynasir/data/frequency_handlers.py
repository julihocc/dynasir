"""
Frequency-specific data handlers for native multi-frequency support.

This module provides pluggable handlers for different data frequencies (annual, monthly,
weekly, daily) to avoid artificial reindexing and enable native processing of
surveillance data at any frequency.

Architecture:
- FrequencyHandler: Abstract base class defining the interface
- Concrete handlers: AnnualFrequencyHandler, MonthlyFrequencyHandler, WeeklyFrequencyHandler, DailyFrequencyHandler
- FrequencyHandlerRegistry: Factory for creating appropriate handler based on frequency string
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Type

import pandas as pd


def make_forecast_index(
    index: pd.DatetimeIndex, steps: int, frequency: Optional[str] = None
) -> pd.DatetimeIndex:
    """Create forecast timestamps at the training index frequency."""
    if frequency is None:
        frequency = index.freqstr
    if frequency is None and len(index) >= 3:
        try:
            frequency = pd.infer_freq(index)
        except ValueError:
            pass
    frequency = frequency or "D"
    return pd.date_range(start=index[-1], periods=steps + 1, freq=frequency)[1:]


class FrequencyHandler(ABC):
    """
    Abstract base class for frequency-specific data processing.

    Handlers encapsulate the logic for different data frequencies (annual, monthly, etc),
    allowing each frequency to have its own recovery lag, lag selection defaults,
    and validation rules.

    Attributes:
        frequency_code (str): Pandas-compatible frequency code ('D', 'W', 'M', 'Y', 'YE', 'ME')
        frequency_name (str): Human-readable name (e.g., 'annual', 'monthly')
        periods_per_year (float): How many periods in one calendar year
    """

    frequency_code: str
    frequency_name: str
    periods_per_year: float

    @abstractmethod
    def validate_data(self, data: pd.DataFrame) -> None:
        """
        Validate that data is suitable for this frequency.

        Args:
            data: DataFrame with date index

        Raises:
            ValueError: If data doesn't meet frequency requirements
        """
        pass

    @abstractmethod
    def get_recovery_lag(self) -> float:
        """
        Get recovery lag in periods (not days) for this frequency.

        For daily data: 14 days = 14 periods
        For annual data: 14 days ≈ 0.038 years = 0.038 periods
        For monthly data: 14 days ≈ 0.5 months = 0.5 periods

        Returns:
            Recovery lag in periods (can be fractional for sub-period accuracy)
        """
        pass

    @abstractmethod
    def get_default_max_lag(self) -> int:
        """
        Get default maximum lag for VAR model selection.

        For data-rich frequencies (daily): 10-14 lags
        For data-sparse frequencies (annual): 2-3 lags

        Returns:
            Default max lag for this frequency
        """
        pass

    def get_min_observations(self) -> int:
        """
        Get minimum number of observations required for reliable modeling.

        Override if frequency-specific requirements differ.

        Returns:
            Minimum observations (default: 2x max_lag)
        """
        return 2 * self.get_default_max_lag()


class DailyFrequencyHandler(FrequencyHandler):
    """Handler for daily frequency data."""

    frequency_code = "D"
    frequency_name = "daily"
    periods_per_year = 365.25

    def validate_data(self, data: pd.DataFrame) -> None:
        """Validate daily frequency data."""
        if len(data) < 30:
            raise ValueError(
                f"Daily data requires at least 30 observations, got {len(data)}"
            )

        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Daily frequency data must have DatetimeIndex")

    def get_recovery_lag(self) -> int:
        """14-day recovery period = 14 daily periods."""
        return 14

    def get_default_max_lag(self) -> int:
        """Use up to 14 lags for daily data (rich time series)."""
        return 14


class BusinessDayFrequencyHandler(FrequencyHandler):
    """Handler for business day (B) frequency data.

    Business days exclude weekends and holidays, resulting in ~252 business days/year.
    Use when data is only collected on working days (e.g., hospital discharge counts).
    """

    frequency_code = "B"
    frequency_name = "business day"
    periods_per_year = 252  # ~5 days/week * 52 weeks

    def validate_data(self, data: pd.DataFrame) -> None:
        """Validate business day frequency data."""
        if len(data) < 30:
            raise ValueError(
                f"Business day data requires at least 30 observations, got {len(data)}"
            )

        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Business day frequency data must have DatetimeIndex")

    def get_recovery_lag(self) -> int:
        """14 days ≈ 10 business days (assuming ~2-day weekends)."""
        return 10

    def get_default_max_lag(self) -> int:
        """Use 10 lags for business day data (between daily and weekly)."""
        return 10

    def get_min_observations(self) -> int:
        """At least 3 months of business days for reliable analysis."""
        return 60  # ~3 months * 20 business days/month


class WeeklyFrequencyHandler(FrequencyHandler):
    """Handler for weekly frequency data."""

    frequency_code = "W"
    frequency_name = "weekly"
    periods_per_year = 52.14

    def validate_data(self, data: pd.DataFrame) -> None:
        """Validate weekly frequency data."""
        if len(data) < 26:
            raise ValueError(
                f"Weekly data requires at least 26 observations (6 months), got {len(data)}"
            )

        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Weekly frequency data must have DatetimeIndex")

    def get_recovery_lag(self) -> int:
        """14 days ≈ 2 weeks."""
        return 2

    def get_default_max_lag(self) -> int:
        """Use up to 8 lags for weekly data."""
        return 8

    def get_min_observations(self) -> int:
        """At least 52 weeks (1 year) for reliable weekly analysis."""
        return 52


class MonthlyFrequencyHandler(FrequencyHandler):
    """Handler for monthly frequency data."""

    frequency_code = "ME"  # Modern pandas alias for month-end
    frequency_name = "monthly"
    periods_per_year = 12

    def validate_data(self, data: pd.DataFrame) -> None:
        """Validate monthly frequency data."""
        if len(data) < 24:
            raise ValueError(
                f"Monthly data requires at least 24 observations (2 years), got {len(data)}"
            )

        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Monthly frequency data must have DatetimeIndex")

    def get_recovery_lag(self) -> float:
        """14 days ≈ 0.47 months (14/30)."""
        return 14 / 30

    def get_default_max_lag(self) -> int:
        """Use up to 6 lags for monthly data."""
        return 6

    def get_min_observations(self) -> int:
        """At least 24 months (2 years) for monthly analysis."""
        return 24


class AnnualFrequencyHandler(FrequencyHandler):
    """
    Handler for annual frequency data.

    The recovery lag is 14/365 years, below one period, so incidence data is
    modelled as period cohorts: the cases of year t are the infectious group
    for the step to year t+1. The infection rate is then about the growth ratio
    I(t+1)/I(t) scaled by the susceptible share, beta = 1 - gamma, and
    ``results["I"]`` is annual incidence.

    Note:
        A fit on a few dozen annual observations does not imply forecast skill.
        Zero-case years make rates undefined (see ``incidence_offset`` in
        DataContainer), and scenario ranges widen quickly with the horizon.
        See docs/user-guide/known-limitations.md.
    """

    frequency_code = "YE"  # Modern pandas alias for year-end
    frequency_name = "annual"
    periods_per_year = 1

    def validate_data(self, data: pd.DataFrame) -> None:
        """Validate annual frequency data."""
        if len(data) < 10:
            raise ValueError(
                f"Annual data requires at least 10 observations (10 years), got {len(data)}"
            )

        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Annual frequency data must have DatetimeIndex")

    def get_recovery_lag(self) -> float:
        """14 days ≈ 0.038 years (14/365)."""
        return 14 / 365

    def get_default_max_lag(self) -> int:
        """Use up to 3 lags for annual data (sparse time series)."""
        return 3

    def get_min_observations(self) -> int:
        """At least 10 years for annual analysis."""
        return 10


class QuarterlyFrequencyHandler(FrequencyHandler):
    """Handler for quarterly frequency data."""

    frequency_code = "QE"  # Modern pandas alias for quarter-end
    frequency_name = "quarterly"
    periods_per_year = 4

    def validate_data(self, data: pd.DataFrame) -> None:
        """Validate quarterly frequency data."""
        if len(data) < 8:
            raise ValueError(
                f"Quarterly data requires at least 8 observations (2 years), got {len(data)}"
            )

        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Quarterly frequency data must have DatetimeIndex")

    def get_recovery_lag(self) -> float:
        """14 days ≈ 0.15 quarters (14/91)."""
        return 14 / 91

    def get_default_max_lag(self) -> int:
        """Use up to 4 lags for quarterly data (one year)."""
        return 4

    def get_min_observations(self) -> int:
        """At least 8 quarters (2 years) for quarterly analysis."""
        return 8


class FrequencyHandlerRegistry:
    """
    Factory and registry for frequency handlers.

    Supports both legacy aliases (D, M, Y) and modern pandas aliases (D, ME, YE).
    """

    # Map of frequency strings to handler classes
    _HANDLERS: Dict[str, Type[FrequencyHandler]] = {
        # Modern pandas aliases (v2.2+)
        "D": DailyFrequencyHandler,
        "B": BusinessDayFrequencyHandler,
        "W": WeeklyFrequencyHandler,
        "ME": MonthlyFrequencyHandler,
        "QE": QuarterlyFrequencyHandler,
        "YE": AnnualFrequencyHandler,
        # Legacy aliases (deprecated in pandas 2.2+)
        "M": MonthlyFrequencyHandler,
        "Q": QuarterlyFrequencyHandler,
        "QS": QuarterlyFrequencyHandler,
        "Y": AnnualFrequencyHandler,
        # Friendly names
        "daily": DailyFrequencyHandler,
        "business day": BusinessDayFrequencyHandler,
        "businessday": BusinessDayFrequencyHandler,
        "bday": BusinessDayFrequencyHandler,
        "weekly": WeeklyFrequencyHandler,
        "monthly": MonthlyFrequencyHandler,
        "quarterly": QuarterlyFrequencyHandler,
        "annual": AnnualFrequencyHandler,
    }

    @classmethod
    def get(cls, frequency: str) -> FrequencyHandler:
        """
        Get a frequency handler instance.

        Args:
            frequency: Frequency code or name ('D', 'W', 'ME', 'YE', or friendly names)

        Returns:
            Instantiated FrequencyHandler

        Raises:
            ValueError: If frequency is not supported
        """
        # First try exact match (case-insensitive for codes)
        frequency_upper = frequency.upper()

        if frequency_upper in cls._HANDLERS:
            handler_class = cls._HANDLERS[frequency_upper]
            return handler_class()

        # Then try lowercase for friendly names
        frequency_lower = frequency.lower()
        if frequency_lower in cls._HANDLERS:
            handler_class = cls._HANDLERS[frequency_lower]
            return handler_class()

        # Not found
        available = sorted(
            set(
                k
                for k in cls._HANDLERS.keys()
                if k not in ("M", "Y")  # Hide deprecated aliases
            )
        )
        raise ValueError(
            f"Unsupported frequency '{frequency}'. Supported: {', '.join(available)}"
        )

    @classmethod
    def get_all_handlers(cls) -> Dict[str, FrequencyHandler]:
        """
        Get all available handlers.

        Returns:
            Dictionary mapping frequency names to handler instances
        """
        unique_handlers = {}
        for frequency, handler_class in cls._HANDLERS.items():
            # Use frequency code as key, skip legacy aliases
            if frequency not in ("M", "Q", "QS", "Y"):
                unique_handlers[frequency] = handler_class()

        return unique_handlers

    @classmethod
    def register(cls, frequency: str, handler_class: Type[FrequencyHandler]) -> None:
        """
        Register a custom frequency handler.

        Args:
            frequency: Frequency code or name
            handler_class: Handler class (subclass of FrequencyHandler)
        """
        if not issubclass(handler_class, FrequencyHandler):
            raise TypeError(f"Handler must be subclass of FrequencyHandler")

        cls._HANDLERS[frequency.upper()] = handler_class
        logging.info(f"Registered custom frequency handler for '{frequency}'")


def get_frequency_handler(frequency: str) -> FrequencyHandler:
    """
    Convenience function to get a frequency handler.

    Args:
        frequency: Frequency code ('D', 'W', 'ME', 'YE') or name ('daily', 'weekly', etc.)

    Returns:
        FrequencyHandler instance

    Raises:
        ValueError: If frequency is not supported

    Examples:
        >>> handler = get_frequency_handler('annual')
        >>> round(handler.get_recovery_lag(), 4)  # 14 days in years
        0.0384
        >>> handler.get_default_max_lag()
        3
    """
    return FrequencyHandlerRegistry.get(frequency)


def detect_frequency_from_index(date_index: pd.DatetimeIndex) -> str:
    """
    Detect frequency from a DatetimeIndex.

    Args:
        date_index: DatetimeIndex to analyze

    Returns:
        Detected frequency code ('D', 'W', 'ME', 'YE')

    Raises:
        ValueError: If frequency cannot be determined
    """
    if len(date_index) < 2:
        raise ValueError("Need at least 2 observations to detect frequency")

    try:
        # Try to infer frequency using pandas
        inferred_freq = pd.infer_freq(date_index)

        if inferred_freq is not None:
            inferred_freq_str = str(inferred_freq).upper()

            # Map inferred frequency to standard codes
            # Check Y/A BEFORE D (since 'D' appears in 'YE-DEC').
            # Check Q before any later letter test: 'QE-DEC' is quarterly.
            if "Y" in inferred_freq_str or "A" in inferred_freq_str:
                return "YE"
            elif "Q" in inferred_freq_str:
                return "QE"
            elif "M" in inferred_freq_str:
                return "ME"
            elif "W" in inferred_freq_str:
                return "W"
            elif "B" in inferred_freq_str:
                return "B"
            elif "D" in inferred_freq_str:
                return "D"

        # Manual detection based on time deltas (average across all observations)
        deltas = (date_index[1:] - date_index[:-1]).days
        avg_delta = deltas.mean()

        # Thresholds: D < 1.5, B ~ 0.7, W < 10, ME < 40, QE about 91, else YE
        # Note: Business day average is ~0.7 days (skips weekends)
        if avg_delta < 0.8:  # Business day has lower average due to weekend skips
            return "B"
        elif avg_delta < 1.5:
            return "D"
        elif avg_delta < 10:
            return "W"
        elif avg_delta < 40:
            return "ME"
        elif 80 <= avg_delta <= 120:
            return "QE"
        else:
            return "YE"

    except Exception as e:
        # Fallback: estimate from delta
        try:
            delta = date_index[1] - date_index[0]
            days = delta.days

            if days < 0.8:
                return "B"
            elif days < 1.5:
                return "D"
            elif days < 10:
                return "W"
            elif days < 40:
                return "ME"
            elif 80 <= days <= 120:
                return "QE"
            else:
                return "YE"
        except Exception:
            raise ValueError(f"Could not detect frequency: {e}")
