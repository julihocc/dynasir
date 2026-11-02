"""
Data validation utilities.

This module provides functions for validating epidemiological data structures
and types to ensure data integrity before processing.
"""

import pandas as pd

from ..core.exceptions import DataValidationError, NotDataFrameError


def validate_data(training_data: pd.DataFrame, mode: str = "cumulative") -> None:
    """
    Validate that the input data is a pandas DataFrame with required columns.

    Args:
        training_data: The data to validate
        mode: Data mode - 'cumulative' or 'incidence'

    Raises:
        NotDataFrameError: If the data is not a pandas DataFrame
        ValueError: If required columns are missing or data is invalid
    """
    if not isinstance(training_data, pd.DataFrame):
        raise NotDataFrameError("raw data must be a pandas DataFrame")

    # Mode-specific validation
    if mode == "cumulative":
        validate_cumulative_data(training_data)
    elif mode == "incidence":
        validate_incidence_data(training_data)


def validate_cumulative_data(data: pd.DataFrame) -> None:
    """
    Validate data for cumulative mode.

    Args:
        data: DataFrame to validate

    Raises:
        DataValidationError: If required columns missing or data invalid
    """
    required_cols = ["C", "D", "N"]
    missing = [col for col in required_cols if col not in data.columns]

    if missing:
        raise DataValidationError(
            f"Cumulative mode requires columns {required_cols}. "
            f"Missing: {missing}. Current columns: {list(data.columns)}"
        )

    # Optional: Check C is monotonic (can be relaxed for flexibility)
    # if (data['C'].diff().dropna() < 0).any():
    #     raise DataValidationError(
    #         "Cumulative cases 'C' should be monotonically increasing. "
    #         "For data that varies up/down, use mode='incidence'."
    #     )


def validate_incidence_data(data: pd.DataFrame) -> None:
    """
    Validate data for incidence mode.

    Args:
        data: DataFrame to validate

    Raises:
        DataValidationError: If required columns missing or data invalid
    """
    required_cols = ["I", "D", "N"]
    missing = [col for col in required_cols if col not in data.columns]

    if missing:
        raise DataValidationError(
            f"Incidence mode requires columns {required_cols}. "
            f"Missing: {missing}. Current columns: {list(data.columns)}\n\n"
            f"Note: Incidence mode expects 'I' (incident cases per period), not 'C' (cumulative).\n"
            f"If you have cumulative data, use mode='cumulative' (default)."
        )

    # Validate I can be non-negative (but CAN decrease - that's the point!)
    if (data["I"] < 0).any():
        raise DataValidationError(
            "Incident cases 'I' cannot be negative. "
            "Found negative values in 'I' column."
        )
