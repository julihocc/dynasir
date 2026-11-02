"""
Tests for Model class mode attribute (cumulative vs incidence).

Verifies that the Model class correctly inherits and propagates the mode
from DataContainer through the entire modeling pipeline.
"""

import numpy as np
import pandas as pd
import pytest

from dynasir import DataContainer, Model


@pytest.fixture
def cumulative_data():
    """Generate sufficient cumulative data for model initialization."""
    dates = pd.date_range("2020-01-01", periods=50, freq="D")
    np.random.seed(42)
    data = pd.DataFrame(
        {
            "C": np.cumsum(np.random.exponential(50, len(dates))),
            "D": np.cumsum(np.random.exponential(2, len(dates))),
            "N": [100000] * len(dates),
        },
        index=dates,
    )
    return data


@pytest.fixture
def incidence_data():
    """Generate sufficient incidence data for model initialization."""
    dates = pd.date_range("2020-01-01", periods=50, freq="D")
    np.random.seed(42)
    # Incident cases can vary (not cumulative)
    data = pd.DataFrame(
        {
            "I": np.random.exponential(50, len(dates)),
            "D": np.cumsum(np.random.exponential(2, len(dates))),
            "N": [100000] * len(dates),
        },
        index=dates,
    )
    return data


class TestModelModeInheritance:
    """Test that Model inherits mode from DataContainer."""

    def test_model_inherits_cumulative_mode(self, cumulative_data):
        """Model should inherit cumulative mode from DataContainer."""
        container = DataContainer(cumulative_data, window=3, mode="cumulative")
        model = Model(container)

        assert model.mode == "cumulative"

    def test_model_inherits_incidence_mode(self, incidence_data):
        """Model should inherit incidence mode from DataContainer."""
        container = DataContainer(incidence_data, window=3, mode="incidence")
        model = Model(container)

        assert model.mode == "incidence"

    def test_model_default_mode_is_cumulative(self, cumulative_data):
        """Model should default to cumulative mode when not specified."""
        container = DataContainer(cumulative_data, window=3)  # No mode specified
        model = Model(container)

        assert model.mode == "cumulative"


class TestModelModeInDataProcessing:
    """Test that mode affects data processing correctly."""

    def test_cumulative_mode_has_c_column(self, cumulative_data):
        """Cumulative mode should preserve C column in model data."""
        container = DataContainer(cumulative_data, mode="cumulative")
        model = Model(container)

        assert "C" in model.data.columns
        assert model.mode == "cumulative"

    def test_incidence_mode_has_i_column(self, incidence_data):
        """Incidence mode should preserve I column in model data."""
        container = DataContainer(incidence_data, mode="incidence")
        model = Model(container)

        assert "I" in model.data.columns
        assert model.mode == "incidence"

    def test_incidence_mode_generates_c_from_i(self, incidence_data):
        """Incidence mode should generate C from cumsum(I)."""
        container = DataContainer(incidence_data, mode="incidence")
        model = Model(container)

        # Both I and C should exist
        assert "I" in model.data.columns
        assert "C" in model.data.columns

        # C should be monotonic (cumulative)
        assert all(model.data["C"].diff().dropna() >= 0)


class TestModelModeWithDifferentBackends:
    """Test that mode works with different forecasting backends."""

    def test_incidence_mode_with_var_backend(self, incidence_data):
        """Incidence mode should work with VAR backend (default)."""
        container = DataContainer(incidence_data, mode="incidence")
        model = Model(container, forecaster="var")

        assert model.mode == "incidence"
        assert model.forecaster_name == "var"

    def test_incidence_mode_with_prophet_backend(self, incidence_data):
        """Incidence mode should work with Prophet backend."""
        container = DataContainer(incidence_data, mode="incidence")
        model = Model(container, forecaster="prophet")

        assert model.mode == "incidence"
        assert model.forecaster_name == "prophet"


class TestModelModeBackwardCompatibility:
    """Test backward compatibility for existing code."""

    def test_existing_code_without_mode_works(self, cumulative_data):
        """Existing code that doesn't specify mode should still work."""
        # Old code pattern: DataContainer without mode parameter
        container = DataContainer(cumulative_data)
        model = Model(container)

        # Should default to cumulative
        assert model.mode == "cumulative"
        assert "C" in model.data.columns

    def test_model_with_date_range_respects_mode(self, incidence_data):
        """Model with start/stop dates should respect mode."""
        container = DataContainer(incidence_data, mode="incidence")
        # Use dates within the actual data range
        model = Model(
            container,
            start="2020-01-08",  # After processing shifts
            stop="2020-02-10",
        )

        assert model.mode == "incidence"
        assert model.start == "2020-01-08"
        assert model.stop == "2020-02-10"


class TestModelModeInForecasting:
    """Test that mode is accessible during forecasting workflow."""

    def test_mode_accessible_before_forecast(self, incidence_data):
        """Mode should be accessible after model creation."""
        container = DataContainer(incidence_data, mode="incidence")
        model = Model(container)
        model.create_model()

        assert model.mode == "incidence"

    def test_mode_accessible_after_fit(self, sample_data_container):
        """Mode should remain accessible after fitting.

        Uses existing sample_data_container fixture which has realistic data
        that avoids constant logit columns.
        """
        from dynasir import Model

        model = Model(sample_data_container)
        model.create_model()
        model.fit_model(max_lag=2)

        assert model.mode == "cumulative"  # Default mode from fixture


class TestModelModeDocumentation:
    """Test that mode is properly documented in Model class."""

    def test_model_has_mode_attribute(self, cumulative_data):
        """Model class should have mode attribute."""
        container = DataContainer(cumulative_data)
        model = Model(container)

        assert hasattr(model, "mode")

    def test_model_mode_is_string(self, incidence_data):
        """Model mode should be a string."""
        container = DataContainer(incidence_data, mode="incidence")
        model = Model(container)

        assert isinstance(model.mode, str)
        assert model.mode in ["cumulative", "incidence"]
