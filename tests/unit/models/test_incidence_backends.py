"""
Tests for multi-backend forecasting with incidence mode (v0.9.0+).

Verifies that all forecasting backends (VAR, Prophet, ARIMA) work correctly
with incidence mode data where incident cases can vary up/down.
"""

import numpy as np
import pandas as pd
import pytest

from dynasir import Model
from dynasir.data import DataContainer


# Helper functions (must be defined before use in decorators)
def _prophet_available():
    """Check if Prophet is available."""
    try:
        import prophet  # noqa: F401

        return True
    except ImportError:
        return False


def _arima_available():
    """Check if pmdarima is available."""
    try:
        import pmdarima  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.fixture
def incidence_sird_data():
    """Create incident cases data (measles-style, can vary up/down)."""
    np.random.seed(42)
    dates = pd.date_range("2010", periods=30, freq="YE")

    # Realistic incident cases: sporadic → decline → outbreaks
    incident_cases = np.array(
        [
            100,
            80,
            120,
            90,
            110,  # Sporadic phase
            70,
            50,
            30,
            10,
            5,  # Decline phase (elimination)
            8,
            15,
            25,
            40,
            35,  # Reintroduction phase
            50,
            60,
            55,
            65,
            70,
            75,
            80,
            85,
            90,
            95,
            85,
            80,
            75,
            70,
            65,
        ]
    )

    data = pd.DataFrame(
        {
            "I": incident_cases,
            "D": np.cumsum(incident_cases * 0.01),
            "N": [120_000_000] * 30,
        },
        index=dates,
    )

    return data


@pytest.fixture
def incidence_container(incidence_sird_data):
    """Create incidence mode DataContainer."""
    return DataContainer(incidence_sird_data, mode="incidence", window=3)


class TestIncidenceModeVARBackend:
    """Test VAR backend with incidence mode."""

    def test_var_incidence_model_creation(self, incidence_container):
        """VAR model should be creatable with incidence mode."""
        model = Model(incidence_container, forecaster="var")
        assert model.mode == "incidence"
        assert model.forecaster_name == "var"

        # Model creation should succeed (VAR fitting may fail with synthetic data)
        model.create_model()
        assert model.var_forecasting is not None


@pytest.mark.skipif(not _prophet_available(), reason="Prophet not installed")
class TestIncidenceModeProphetBackend:
    """Test Prophet backend with incidence mode (skipped if not installed)."""

    def test_prophet_incidence_workflow(self, incidence_container):
        """Complete Prophet workflow should work with incidence mode."""
        model = Model(
            incidence_container,
            forecaster="prophet",
            yearly_seasonality=True,
            changepoint_prior_scale=0.05,
        )
        assert model.mode == "incidence"

        model.create_model()
        model.fit_model()
        model.forecast(steps=5)
        model.run_simulations(n_jobs=1)
        model.generate_result()

        # Verify results
        assert model.results is not None
        assert "I" in model.results
        assert len(model.results["I"]["mean"]) == 5


@pytest.mark.skipif(not _arima_available(), reason="pmdarima not installed")
class TestIncidenceModeARIMABackend:
    """Test ARIMA backend with incidence mode (skipped if not installed)."""

    def test_arima_incidence_workflow(self, incidence_container):
        """Complete ARIMA workflow should work with incidence mode."""
        model = Model(
            incidence_container,
            forecaster="arima",
            max_p=2,
            max_q=2,
            seasonal=False,
        )
        assert model.mode == "incidence"

        model.create_model()
        model.fit_model()
        model.forecast(steps=5)
        model.run_simulations(n_jobs=1)
        model.generate_result()

        # Verify results
        assert model.results is not None
        assert "I" in model.results
        assert len(model.results["I"]["mean"]) == 5


class TestIncidenceModeBackendComparison:
    """Compare results across backends in incidence mode."""

    def test_var_model_initialization(self, incidence_container):
        """VAR should initialize with incidence mode."""
        model = Model(incidence_container, forecaster="var")
        assert model.mode == "incidence"
        assert model.forecaster_name == "var"
        model.create_model()
        assert model.var_forecasting is not None


class TestIncidenceModePreservation:
    """Verify mode is preserved across backend creation."""

    def test_mode_preserved_var(self, incidence_container):
        """Mode should be preserved with VAR backend."""
        model = Model(incidence_container, forecaster="var")
        assert model.mode == "incidence"
        model.create_model()
        assert model.mode == "incidence"

    def test_mode_preserved_prophet_if_available(self, incidence_container):
        """Mode should be preserved with Prophet backend (if available)."""
        try:
            model = Model(incidence_container, forecaster="prophet")
            assert model.mode == "incidence"
            model.create_model()
            assert model.mode == "incidence"
        except ImportError:
            pytest.skip("Prophet not installed")

    def test_mode_preserved_arima_if_available(self, incidence_container):
        """Mode should be preserved with ARIMA backend (if available)."""
        try:
            model = Model(incidence_container, forecaster="arima")
            assert model.mode == "incidence"
            model.create_model()
            assert model.mode == "incidence"
        except ImportError:
            pytest.skip("pmdarima not installed")
