"""
Tests for exceptions module.

Following TDD principles, these tests define the expected behavior
of the exceptions module before implementation.
"""


def test_exceptions_module_imports():
    """Test that all exceptions can be imported from core.exceptions."""
    from dynasir.core.exceptions import (
        DataValidationError,
        DateRangeError,
        DynaSIRError,
        NotDataFrameError,
    )

    # Basic import verification
    assert NotDataFrameError is not None
    assert DynaSIRError is not None
    assert DataValidationError is not None
    assert DateRangeError is not None


def test_base_exception_hierarchy():
    """Test that custom exceptions inherit from proper base classes."""
    from dynasir.core.exceptions import (
        DataValidationError,
        DateRangeError,
        DynaSIRError,
        NotDataFrameError,
    )

    # Test inheritance hierarchy
    assert issubclass(DynaSIRError, Exception)
    assert issubclass(NotDataFrameError, DynaSIRError)
    assert issubclass(DataValidationError, DynaSIRError)
    assert issubclass(DateRangeError, DynaSIRError)


def test_not_dataframe_error():
    """Test NotDataFrameError functionality."""
    from dynasir.core.exceptions import NotDataFrameError

    # Test basic functionality
    error = NotDataFrameError("Test message")
    assert isinstance(error, Exception)
    assert str(error) == "Test message"

    # Test default message
    error_default = NotDataFrameError()
    assert str(error_default) == "Input data must be a pandas DataFrame"


def test_data_validation_error():
    """Test DataValidationError functionality."""
    from dynasir.core.exceptions import DataValidationError

    # Test with custom message
    error = DataValidationError("Invalid data format")
    assert isinstance(error, Exception)
    assert str(error) == "Invalid data format"


def test_date_range_error():
    """Test DateRangeError functionality."""
    from dynasir.core.exceptions import DateRangeError

    # Test with custom message
    error = DateRangeError("Invalid date range")
    assert isinstance(error, Exception)
    assert str(error) == "Invalid date range"


def test_exception_raising():
    """Test that exceptions can be raised properly."""
    from dynasir.core.exceptions import DataValidationError, NotDataFrameError

    try:
        raise NotDataFrameError("Test raising")
        assert False, "Exception should have been raised"
    except NotDataFrameError as e:
        assert str(e) == "Test raising"

    try:
        raise DataValidationError("Validation failed")
        assert False, "Exception should have been raised"
    except DataValidationError as e:
        assert str(e) == "Validation failed"


def test_exception_with_context():
    """Test exceptions with additional context information."""
    from dynasir.core.exceptions import DataValidationError

    # Test exception with context
    try:
        raise DataValidationError(
            "Missing required columns: ['total_cases', 'total_deaths']"
        )
        assert False, "Exception should have been raised"
    except DataValidationError as e:
        assert "total_cases" in str(e)
        assert "total_deaths" in str(e)


def test_top_level_exports():
    """Test that exceptions are exported at the package top-level."""
    import dynasir

    assert hasattr(dynasir, "DynaSIRError")
    assert hasattr(dynasir, "NotDataFrameError")
    assert hasattr(dynasir, "DataValidationError")
    assert hasattr(dynasir, "DateRangeError")


def test_exception_documentation():
    """Test that exceptions have proper documentation."""
    from dynasir.core.exceptions import (
        DataValidationError,
        DateRangeError,
        DynaSIRError,
        NotDataFrameError,
    )

    # Check that all exceptions have docstrings
    assert DynaSIRError.__doc__ is not None
    assert NotDataFrameError.__doc__ is not None
    assert DataValidationError.__doc__ is not None
    assert DateRangeError.__doc__ is not None

    # Check that docstrings are meaningful
    assert len(DynaSIRError.__doc__.strip()) > 10
    assert len(NotDataFrameError.__doc__.strip()) > 10


def test_exception_args_handling():
    """Test that exceptions handle arguments properly."""
    from dynasir.core.exceptions import DataValidationError, NotDataFrameError

    # Test with single argument
    error1 = NotDataFrameError("Single message")
    assert error1.args == ("Single message",)

    # Test with multiple arguments
    error2 = DataValidationError("Error", "Additional info", 123)
    assert error2.args == ("Error", "Additional info", 123)

    # Test with no arguments (gets default message)
    error3 = NotDataFrameError()
    assert error3.args == ("Input data must be a pandas DataFrame",)


def test_exception_chaining():
    """Test exception chaining works properly."""
    from dynasir.core.exceptions import DataValidationError

    try:
        try:
            # Simulate original error
            raise ValueError("Original problem")
        except ValueError as original:
            # Chain with our custom exception
            raise DataValidationError("Validation failed") from original
    except DataValidationError as e:
        assert e.__cause__ is not None
        assert isinstance(e.__cause__, ValueError)
        assert str(e.__cause__) == "Original problem"
