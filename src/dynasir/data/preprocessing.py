"""
Data preprocessing utilities.

This module handles the cleaning, smoothing, and temporal alignment of
epidemiological data before feature extraction.
"""

import logging
import warnings
from typing import Optional

import pandas as pd


def _get_effective_window(window: int, frequency: str) -> int:
    """
    Calculate effective rolling window size adapted to data frequency.

    Sparse frequencies (monthly, annual) should use smaller windows to avoid
    excessive smoothing with limited data points.

    Args:
        window: Requested window size
        frequency: Data frequency ('D', 'W', 'ME', 'YE')

    Returns:
        Effective window size capped for frequency
    """
    if frequency in ("D", "W"):
        return window  # Use requested window for dense frequencies
    elif frequency == "ME":  # Monthly
        return min(window, 2)  # Cap at 2 months
    elif frequency == "YE":  # Annual
        return 1  # No smoothing for annual (only 1 observation per year)
    else:
        return window


def preprocess_data(
    data: pd.DataFrame, window: int = 7, frequency: str = None
) -> pd.DataFrame:
    """
    Preprocess raw data by applying rolling window smoothing and conditional reindexing.

    Behavior is frequency-aware:
    - Daily/Weekly: Applies rolling window smoothing and reindexes to daily (current behavior)
    - Monthly/Annual: Applies minimal smoothing and keeps native frequency (no reindexing)

    Args:
        data: Raw input DataFrame with DatetimeIndex
        window: Rolling window size for smoothing (default: 7)
                Automatically reduced for sparse frequencies:
                - Daily/Weekly: uses provided window
                - Monthly: min(window, 2)
                - Annual: min(window, 1) - effectively no smoothing
        frequency: Data frequency ('D', 'W', 'ME', 'YE'). If None, attempts auto-detection.
                  Controls whether data is reindexed to daily or kept in native frequency.

    Returns:
        Preprocessed DataFrame with native frequency preserved (or reindexed to daily for D/W)

    Examples:
        >>> # Daily data: normal smoothing and daily reindexing
        >>> daily_processed = preprocess_data(daily_data, window=7, frequency='D')

        >>> # Annual data: minimal smoothing, NO reindexing
        >>> annual_processed = preprocess_data(annual_data, window=7, frequency='YE')
        >>> # Result: input had ~10 rows → output has ~10 rows (not ~3650)
    """
    # Auto-detect frequency if not provided
    if frequency is None:
        try:
            frequency = detect_frequency(data)
            logging.info(f"Auto-detected frequency in preprocessing: {frequency}")
        except ValueError:
            logging.warning("Could not auto-detect frequency; defaulting to daily")
            frequency = "D"

    # Adapt window size for sparse frequencies
    effective_window = _get_effective_window(window, frequency)

    # Apply rolling window smoothing
    if effective_window > 1:
        smoothed_data = data.rolling(window=effective_window).mean()[effective_window:]
    else:
        smoothed_data = data.copy()

    # Conditional reindexing based on frequency
    if frequency in ("D", "W"):
        # Daily/Weekly: Reindex to daily (backward compatible)
        reindexed_data = reindex_data(smoothed_data, freq="D", warn_on_mismatch=True)
    else:
        # Monthly/Annual: Skip reindexing, keep native frequency
        logging.info(f"Preserving native {frequency} frequency (skipping reindexing)")
        reindexed_data = smoothed_data.ffill()

    logging.debug(
        f"Preprocessing complete: frequency={frequency}, window={effective_window}, shape={reindexed_data.shape}"
    )
    return reindexed_data


def reindex_data(
    data: pd.DataFrame,
    start: Optional[str] = None,
    stop: Optional[str] = None,
    freq: Optional[str] = None,
    warn_on_mismatch: bool = True,
) -> pd.DataFrame:
    """
    Reindex DataFrame to a consistent date range and forward fill missing values.

    Args:
        data: DataFrame to reindex
        start: Start date (ISO format string), defaults to data minimum
        stop: Stop date (ISO format string), defaults to data maximum
        freq: Target frequency ('D', 'W', 'M', 'Y'). Defaults to 'D' for
            backward compatibility.
        warn_on_mismatch: If True, warn when source and target frequencies differ

    Returns:
        Reindexed DataFrame

    Raises:
        ValueError: If start > stop or dates are outside data range

    Examples:
        >>> # Default behavior (v0.7.0 compatible - daily)
        >>> reindexed = reindex_data(data)

        >>> # Explicit annual frequency (no reindexing warning)
        >>> reindexed = reindex_data(data, freq='YE')
    """
    from dynasir.core.constants import DEFAULT_FREQUENCY

    # Handle case where data has no rows
    if len(data) == 0:
        return data

    # Default to daily for backward compatibility
    if freq is None:
        freq = DEFAULT_FREQUENCY

    # Detect source frequency and warn if mismatch
    if warn_on_mismatch and len(data) >= 2:
        try:
            detected_freq = detect_frequency(data)
            if detected_freq != freq:
                # Calculate how many artificial points will be created
                start_date = (
                    pd.to_datetime(start) if start is not None else data.index.min()
                )
                stop_date = (
                    pd.to_datetime(stop) if stop is not None else data.index.max()
                )
                target_range = pd.date_range(start=start_date, end=stop_date, freq=freq)
                artificial_points = len(target_range) - len(data)

                if artificial_points > len(data) * 2:  # Warn if >2x data points
                    warn_frequency_mismatch(detected_freq, freq, artificial_points)
        except ValueError as e:
            logging.debug(f"Could not detect frequency: {e}")

    # Convert dates and set defaults
    start_date = pd.to_datetime(start) if start is not None else data.index.min()
    stop_date = pd.to_datetime(stop) if stop is not None else data.index.max()

    # Validate date range
    if start_date > stop_date:
        raise ValueError("Start date is after stop date")

    logging.debug(f"start_date: {start_date}, data.index[0]: {data.index[0]}")
    if start_date < data.index[0]:
        raise ValueError("Start date is before first date on confirmed cases")

    if stop_date > data.index[-1]:
        raise ValueError("Stop date is after last date of updated cases")

    try:
        logging.debug(
            f"Reindex data from {start_date} to {stop_date} with freq={freq}, shape: {data.shape}"
        )
        reindex = pd.date_range(start=start_date, end=stop_date, freq=freq)
        reindexed_data = data.reindex(reindex)
    except Exception as e:
        raise Exception(f"Could not reindex data: {e}")

    try:
        # Use forward fill for missing values
        reindexed_data = reindexed_data.ffill()
    except Exception as e:
        raise Exception(f"Could not fill missing values: {e}")

    return reindexed_data


def detect_frequency(data: pd.DataFrame) -> str:
    """
    Detect the frequency of a time-indexed DataFrame.

    Analyzes the temporal spacing between consecutive observations to determine
    whether data is daily, weekly, monthly, or annual.

    Args:
        data: DataFrame with DatetimeIndex

    Returns:
        Frequency string ('D', 'W', 'M', 'Y')

    Raises:
        ValueError: If frequency cannot be detected or data has < 2 observations

    Examples:
        >>> # Daily COVID-19 data
        >>> daily_data = pd.DataFrame({'cases': [100, 150, 200]},
        ...                           index=pd.date_range('2020-01-01', periods=3, freq='D'))
        >>> detect_frequency(daily_data)
        'D'

        >>> # Annual measles data
        >>> annual_data = pd.DataFrame({'cases': [50, 60, 55]},
        ...                            index=pd.date_range('2015', periods=3, freq='YE'))
        >>> detect_frequency(annual_data)
        'Y'
    """
    if len(data) < 2:
        raise ValueError(
            "Need at least 2 data points to detect frequency. "
            f"Provided data has {len(data)} points."
        )

    # Calculate median difference between consecutive dates
    diffs = data.index.to_series().diff().dropna()
    median_diff = diffs.median()

    # Handle case where median returns numeric instead of Timedelta
    if not isinstance(median_diff, pd.Timedelta):
        # Convert to Timedelta if numeric (in nanoseconds)
        median_diff = pd.Timedelta(median_diff)

    # Classify based on median difference
    if median_diff <= pd.Timedelta(days=2):
        return "D"
    elif median_diff <= pd.Timedelta(days=10):
        return "W"
    elif median_diff <= pd.Timedelta(days=45):
        return "M"
    elif median_diff >= pd.Timedelta(days=300):
        return "Y"
    else:
        raise ValueError(
            f"Detected irregular frequency with median gap of {median_diff.days} days. "
            "Supported frequencies: daily (D), weekly (W), monthly (M), annual (Y). "
            "Data may have irregular spacing or mixed frequencies."
        )


def warn_frequency_mismatch(
    detected_freq: str, target_freq: str, data_points: int
) -> None:
    """
    Warn when reindexing will create artificial data points.

    Emits a UserWarning when source and target frequencies differ significantly,
    which can lead to artificial patterns in epidemiological rate calculations.

    Args:
        detected_freq: Detected source frequency
        target_freq: Target frequency for reindexing
        data_points: Number of artificial data points that will be created

    Examples:
        >>> # Annual data being reindexed to daily creates ~365x points
        >>> warn_frequency_mismatch('Y', 'D', 13516)
        # Emits warning about frequency mismatch
    """
    from dynasir.core.constants import FREQUENCY_ALIASES

    source_name = FREQUENCY_ALIASES.get(detected_freq, detected_freq)
    target_name = FREQUENCY_ALIASES.get(target_freq, target_freq)

    warnings.warn(
        f"\n{'=' * 60}\n"
        f"FREQUENCY MISMATCH WARNING\n"
        f"{'=' * 60}\n"
        f"Source data frequency: {source_name} ({detected_freq})\n"
        f"Target frequency: {target_name} ({target_freq})\n"
        f"Artificial data points created: {data_points}\n\n"
        f"Reindexing {source_name} data to {target_name} creates {data_points} "
        f"rows via forward-fill, which may produce meaningless rate\n"
        f"calculations and forecasts.\n\n"
        f"Recommended actions:\n"
        f"1. Use native frequency support (v0.9.0+): frequency='{detected_freq}'\n"
        f"2. Use temporal aggregation to convert forecasts back to {source_name}\n"
        f"3. See documentation for {source_name} surveillance data best practices\n"
        f"{'=' * 60}\n",
        UserWarning,
        stacklevel=3,
    )
