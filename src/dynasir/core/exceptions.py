"""
Custom exceptions for the DynaSIR library.
"""


class DynaSIRError(Exception):
    """Base exception for the DynaSIR library."""

    pass


class NotDataFrameError(DynaSIRError):
    """Custom exception for when the input is not a Pandas DataFrame."""

    def __init__(self, message="Input data must be a pandas DataFrame"):
        super().__init__(message)


class DataValidationError(DynaSIRError):
    """Custom exception for data validation errors."""

    def __init__(self, *args):
        if not args:
            super().__init__("Data validation failed")

        else:
            super().__init__(*args)


class DateRangeError(DynaSIRError):
    """Custom exception for date range errors."""

    def __init__(self, message="Invalid date range"):
        super().__init__(message)
