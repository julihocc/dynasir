"""
Integration tests for multi-backend forecasting support.

Tests verify that all forecasting backends (VAR, Prophet, ARIMA) work end-to-end
and produce compatible outputs for downstream components like EpidemicSimulation.
"""

import numpy as np
import pandas as pd
import pytest

from dynasir import Model
from dynasir.core.constants import FORECASTING_LEVELS
from dynasir.data import DataContainer


@pytest.fixture
def sample_sird_container():
    """Create sample SIRD DataContainer for testing."""
    np.random.seed(42)
    dates = pd.date_range("2020-01-01", periods=100, freq="D")
    sample_data = pd.DataFrame(
        {
            "C": np.cumsum(np.random.poisson(10, 100)) + 100,
            "D": np.cumsum(np.random.poisson(1, 100)) + 10,
            "N": [1000000] * 100,
        },
        index=dates,
    )
    return DataContainer(sample_data, window=7)


@pytest.fixture
def sample_sirdv_container():
    """Create sample SIRDV DataContainer with vaccination data."""
    np.random.seed(42)
    dates = pd.date_range("2020-01-01", periods=100, freq="D")
    sample_data = pd.DataFrame(
        {
            "C": np.cumsum(np.random.poisson(10, 100)) + 100,
            "D": np.cumsum(np.random.poisson(1, 100)) + 10,
            "V": np.cumsum(np.random.poisson(50, 100)),
            "N": [1000000] * 100,
        },
        index=dates,
    )
    return DataContainer(sample_data, window=7)


# Helper functions must be defined before use in parametrize decorators
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


# Backend configurations for parametrized tests
BACKEND_CONFIGS = [
    ("var", {}),
    pytest.param(
        "prophet",
        {
            "yearly_seasonality": False,
            "weekly_seasonality": False,
            "daily_seasonality": False,
        },
        marks=pytest.mark.skipif(
            not _prophet_available(), reason="Prophet not installed"
        ),
    ),
    pytest.param(
        "arima",
        {"max_p": 2, "max_q": 2, "seasonal": False, "suppress_warnings": True},
        marks=pytest.mark.skipif(
            not _arima_available(), reason="pmdarima not installed"
        ),
    ),
]


class TestMultiBackendBasicWorkflow:
    """Test basic workflow with all backends."""

    @pytest.mark.parametrize("backend_name,backend_kwargs", BACKEND_CONFIGS)
    def test_model_creation_with_backend(
        self, sample_sird_container, backend_name, backend_kwargs
    ):
        """Test creating model with different backends."""
        model = Model(
            sample_sird_container,
            start="2020-01-15",
            stop="2020-03-01",
            forecaster=backend_name,
            **backend_kwargs,
        )

        assert model.forecaster_name == backend_name
        assert model.data_container is sample_sird_container

    @pytest.mark.parametrize("backend_name,backend_kwargs", BACKEND_CONFIGS)
    def test_create_and_fit_model(
        self, sample_sird_container, backend_name, backend_kwargs
    ):
        """Test creating and fitting model with all backends."""
        model = Model(
            sample_sird_container,
            start="2020-01-15",
            stop="2020-03-01",
            forecaster=backend_name,
            **backend_kwargs,
        )

        model.create_model()
        assert model.var_forecasting is not None
        assert model.var_forecasting.forecaster is not None

        # Fit with backend-specific parameters
        if backend_name == "var":
            model.fit_model(max_lag=5, ic="aic")
        elif backend_name == "prophet":
            model.fit_model()
        elif backend_name == "arima":
            model.fit_model(max_p=2, max_q=2, seasonal=False)

        assert model.var_forecasting.forecaster.fitted_model is not None

    @pytest.mark.parametrize("backend_name,backend_kwargs", BACKEND_CONFIGS)
    def test_full_workflow_roundtrip(
        self, sample_sird_container, backend_name, backend_kwargs
    ):
        """Test complete workflow: create → fit → forecast → simulate."""
        model = Model(
            sample_sird_container,
            start="2020-01-15",
            stop="2020-03-01",
            forecaster=backend_name,
            **backend_kwargs,
        )

        # Create and fit
        model.create_model()
        if backend_name == "var":
            model.fit_model(max_lag=5, ic="aic")
        elif backend_name == "prophet":
            model.fit_model()
        elif backend_name == "arima":
            model.fit_model(max_p=2, max_q=2, seasonal=False)

        # Forecast
        steps = 14
        model.forecast(steps=steps)

        assert model.forecasting_box is not None
        assert hasattr(model, "forecasting_interval")

        # Run simulations
        model.run_simulations(n_jobs=1)

        assert model.simulation is not None
        assert hasattr(model, "results")


class TestForecastingBoxStructure:
    """Test that forecasting_box has identical structure across backends."""

    @pytest.mark.parametrize("backend_name,backend_kwargs", BACKEND_CONFIGS)
    def test_forecasting_box_keys(
        self, sample_sird_container, backend_name, backend_kwargs
    ):
        """Test that forecasting_box contains expected keys for all backends."""
        model = Model(
            sample_sird_container,
            start="2020-01-15",
            stop="2020-03-01",
            forecaster=backend_name,
            **backend_kwargs,
        )

        model.create_model()
        if backend_name == "var":
            model.fit_model(max_lag=5, ic="aic")
        elif backend_name == "prophet":
            model.fit_model()
        elif backend_name == "arima":
            model.fit_model(max_p=2, max_q=2, seasonal=False)

        model.forecast(steps=14)

        # Check structure
        fb = model.forecasting_box

        # Should have both logit and regular rates
        expected_logit_rates = ["logit_alpha", "logit_beta", "logit_gamma"]
        expected_rates = ["alpha", "beta", "gamma"]

        for rate in expected_logit_rates + expected_rates:
            assert rate in fb, f"Missing {rate} in forecasting_box for {backend_name}"

        # Each rate should have lower/point/upper
        for rate in expected_rates:
            assert hasattr(fb[rate], "lower")
            assert hasattr(fb[rate], "point")
            assert hasattr(fb[rate], "upper")

    @pytest.mark.parametrize("backend_name,backend_kwargs", BACKEND_CONFIGS)
    def test_forecasting_box_shapes(
        self, sample_sird_container, backend_name, backend_kwargs
    ):
        """Test that all forecast arrays have correct shapes."""
        steps = 20
        model = Model(
            sample_sird_container,
            start="2020-01-15",
            stop="2020-03-01",
            forecaster=backend_name,
            **backend_kwargs,
        )

        model.create_model()
        if backend_name == "var":
            model.fit_model(max_lag=5, ic="aic")
        elif backend_name == "prophet":
            model.fit_model()
        elif backend_name == "arima":
            model.fit_model(max_p=2, max_q=2, seasonal=False)

        model.forecast(steps=steps)

        fb = model.forecasting_box

        # Check shapes for regular rates
        for rate in ["alpha", "beta", "gamma"]:
            for level in ["lower", "point", "upper"]:
                arr = getattr(fb[rate], level)
                assert (
                    len(arr) == steps
                ), f"{backend_name}: {rate}.{level} has wrong length"

    @pytest.mark.parametrize("backend_name,backend_kwargs", BACKEND_CONFIGS)
    def test_forecasting_box_value_ranges(
        self, sample_sird_container, backend_name, backend_kwargs
    ):
        """Test that forecasted rates are in valid range (0, 1)."""
        model = Model(
            sample_sird_container,
            start="2020-01-15",
            stop="2020-03-01",
            forecaster=backend_name,
            **backend_kwargs,
        )

        model.create_model()
        if backend_name == "var":
            model.fit_model(max_lag=5, ic="aic")
        elif backend_name == "prophet":
            model.fit_model()
        elif backend_name == "arima":
            model.fit_model(max_p=2, max_q=2, seasonal=False)

        model.forecast(steps=14)

        fb = model.forecasting_box

        # Regular rates should be in (0, 1)
        for rate in ["alpha", "beta", "gamma"]:
            for level in ["lower", "point", "upper"]:
                arr = getattr(fb[rate], level)
                assert np.all(
                    arr > 0
                ), f"{backend_name}: {rate}.{level} has values <= 0"
                assert np.all(
                    arr < 1
                ), f"{backend_name}: {rate}.{level} has values >= 1"

    @pytest.mark.parametrize("backend_name,backend_kwargs", BACKEND_CONFIGS)
    def test_forecasting_box_has_levels(
        self, sample_sird_container, backend_name, backend_kwargs
    ):
        """Test that forecasts have proper confidence levels."""
        model = Model(
            sample_sird_container,
            start="2020-01-15",
            stop="2020-03-01",
            forecaster=backend_name,
            **backend_kwargs,
        )

        model.create_model()
        if backend_name == "var":
            model.fit_model(max_lag=5, ic="aic")
        elif backend_name == "prophet":
            model.fit_model()
        elif backend_name == "arima":
            model.fit_model(max_p=2, max_q=2, seasonal=False)

        model.forecast(steps=14)

        fb = model.forecasting_box

        for rate in ["alpha", "beta", "gamma"]:
            lower = fb[rate].lower
            point = fb[rate].point
            upper = fb[rate].upper

            # Just verify they exist and are arrays
            assert lower is not None
            assert point is not None
            assert upper is not None
            assert len(lower) == 14
            assert len(point) == 14
            assert len(upper) == 14


class TestEpidemicSimulationCompatibility:
    """Test that EpidemicSimulation works with all backends."""

    @pytest.mark.parametrize("backend_name,backend_kwargs", BACKEND_CONFIGS)
    def test_run_simulations_with_backend(
        self, sample_sird_container, backend_name, backend_kwargs
    ):
        """Test running epidemic simulations with different backends."""
        model = Model(
            sample_sird_container,
            start="2020-01-15",
            stop="2020-03-01",
            forecaster=backend_name,
            **backend_kwargs,
        )

        model.create_model()
        if backend_name == "var":
            model.fit_model(max_lag=5, ic="aic")
        elif backend_name == "prophet":
            model.fit_model()
        elif backend_name == "arima":
            model.fit_model(max_p=2, max_q=2, seasonal=False)

        model.forecast(steps=14)
        model.run_simulations(n_jobs=1)

        assert model.simulation is not None
        assert hasattr(model.simulation, "lower")
        assert hasattr(model.simulation, "point")
        assert hasattr(model.simulation, "upper")

    @pytest.mark.parametrize("backend_name,backend_kwargs", BACKEND_CONFIGS)
    def test_simulation_box_structure(
        self, sample_sird_container, backend_name, backend_kwargs
    ):
        """Test that simulation results have correct 3D structure."""
        model = Model(
            sample_sird_container,
            start="2020-01-15",
            stop="2020-03-01",
            forecaster=backend_name,
            **backend_kwargs,
        )

        model.create_model()
        if backend_name == "var":
            model.fit_model(max_lag=5, ic="aic")
        elif backend_name == "prophet":
            model.fit_model()
        elif backend_name == "arima":
            model.fit_model(max_p=2, max_q=2, seasonal=False)

        model.forecast(steps=14)
        model.run_simulations(n_jobs=1)

        sim = model.simulation

        # Check 3D structure: [alpha_level][beta_level][gamma_level]
        for alpha_level in FORECASTING_LEVELS:
            assert hasattr(sim, alpha_level)
            for beta_level in FORECASTING_LEVELS:
                assert hasattr(getattr(sim, alpha_level), beta_level)
                for gamma_level in FORECASTING_LEVELS:
                    scenario = getattr(getattr(sim, alpha_level), beta_level)
                    assert hasattr(scenario, gamma_level)

    @pytest.mark.parametrize("backend_name,backend_kwargs", BACKEND_CONFIGS)
    def test_simulation_compartments(
        self, sample_sird_container, backend_name, backend_kwargs
    ):
        """Test that simulations contain all SIRD compartments."""
        model = Model(
            sample_sird_container,
            start="2020-01-15",
            stop="2020-03-01",
            forecaster=backend_name,
            **backend_kwargs,
        )

        model.create_model()
        if backend_name == "var":
            model.fit_model(max_lag=5, ic="aic")
        elif backend_name == "prophet":
            model.fit_model()
        elif backend_name == "arima":
            model.fit_model(max_p=2, max_q=2, seasonal=False)

        model.forecast(steps=14)
        model.run_simulations(n_jobs=1)

        # Get one scenario to check compartments
        scenario = model.simulation.point.point.point

        compartments = ["S", "I", "R", "D", "C", "A"]
        for comp in compartments:
            assert hasattr(
                scenario, comp
            ), f"{backend_name}: Missing compartment {comp}"


class TestBackendSpecificKwargs:
    """Test that backend-specific kwargs are forwarded correctly."""

    def test_var_kwargs_forwarding(self, sample_sird_container):
        """Test that VAR-specific kwargs (max_lag, ic) work."""
        model = Model(
            sample_sird_container,
            start="2020-01-15",
            stop="2020-03-01",
            forecaster="var",
        )

        model.create_model()
        model.fit_model(max_lag=7, ic="bic")  # VAR-specific params
        model.forecast(steps=10)

        assert model.forecasting_box is not None

    @pytest.mark.skipif(not _prophet_available(), reason="Prophet not installed")
    def test_prophet_kwargs_forwarding(self, sample_sird_container):
        """Test that Prophet-specific kwargs work."""
        model = Model(
            sample_sird_container,
            start="2020-01-15",
            stop="2020-03-01",
            forecaster="prophet",
            yearly_seasonality=False,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
        )

        model.create_model()
        model.fit_model()
        model.forecast(steps=10)

        assert model.forecasting_box is not None

    @pytest.mark.skipif(not _arima_available(), reason="pmdarima not installed")
    def test_arima_kwargs_forwarding(self, sample_sird_container):
        """Test that ARIMA-specific kwargs work."""
        model = Model(
            sample_sird_container,
            start="2020-01-15",
            stop="2020-03-01",
            forecaster="arima",
            max_p=3,
            max_q=3,
            seasonal=False,
        )

        model.create_model()
        model.fit_model(max_p=3, max_q=3, seasonal=False, suppress_warnings=True)
        model.forecast(steps=10)

        assert model.forecasting_box is not None


class TestVaccinationSupport:
    """Test multi-backend support with SIRDV (vaccination) models."""

    @pytest.mark.parametrize("backend_name,backend_kwargs", BACKEND_CONFIGS)
    def test_sirdv_with_backends(
        self, sample_sirdv_container, backend_name, backend_kwargs
    ):
        """Test that all backends work with SIRDV (4 rates)."""
        model = Model(
            sample_sirdv_container,
            start="2020-01-15",
            stop="2020-03-01",
            forecaster=backend_name,
            **backend_kwargs,
        )

        model.create_model()
        if backend_name == "var":
            model.fit_model(max_lag=5, ic="aic")
        elif backend_name == "prophet":
            model.fit_model()
        elif backend_name == "arima":
            model.fit_model(max_p=2, max_q=2, seasonal=False)

        model.forecast(steps=14)

        fb = model.forecasting_box

        # Should have 4 rates for SIRDV
        if model.has_vaccination:
            expected_rates = ["alpha", "beta", "gamma", "delta"]
            for rate in expected_rates:
                assert rate in fb, f"Missing {rate} for SIRDV with {backend_name}"


class TestResultsGeneration:
    """Test that generate_result() works with all backends."""

    @pytest.mark.parametrize("backend_name,backend_kwargs", BACKEND_CONFIGS)
    def test_generate_result_with_backend(
        self, sample_sird_container, backend_name, backend_kwargs
    ):
        """Test that generate_result() produces complete results for all backends."""
        model = Model(
            sample_sird_container,
            start="2020-01-15",
            stop="2020-03-01",
            forecaster=backend_name,
            **backend_kwargs,
        )

        model.create_model()
        if backend_name == "var":
            model.fit_model(max_lag=5, ic="aic")
        elif backend_name == "prophet":
            model.fit_model()
        elif backend_name == "arima":
            model.fit_model(max_p=2, max_q=2, seasonal=False)

        model.forecast(steps=14)
        model.run_simulations(n_jobs=1)
        model.generate_result()

        assert model.results is not None

        # Check that results contain expected compartments
        compartments = ["S", "I", "R", "D", "C", "A"]
        for comp in compartments:
            assert comp in model.results, f"{backend_name}: Missing {comp} in results"
            # Each compartment should be a DataFrame
            assert isinstance(
                model.results[comp], pd.DataFrame
            ), f"{backend_name}: {comp} should be a DataFrame"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_unknown_backend_raises_error(self, sample_sird_container):
        """Test that unknown backend raises ValueError."""
        with pytest.raises(ValueError, match="Forecaster 'unknown_backend' not found"):
            Model(sample_sird_container, forecaster="unknown_backend")

    def test_default_backend_is_var(self, sample_sird_container):
        """Test that default backend is VAR for backward compatibility."""
        model = Model(sample_sird_container)
        assert model.forecaster_name == "var"

    @pytest.mark.parametrize("backend_name,backend_kwargs", BACKEND_CONFIGS)
    def test_very_short_forecast(
        self, sample_sird_container, backend_name, backend_kwargs
    ):
        """Test forecasting with very short horizon (1 step)."""
        model = Model(
            sample_sird_container,
            start="2020-01-15",
            stop="2020-03-01",
            forecaster=backend_name,
            **backend_kwargs,
        )

        model.create_model()
        if backend_name == "var":
            model.fit_model(max_lag=5, ic="aic")
        elif backend_name == "prophet":
            model.fit_model()
        elif backend_name == "arima":
            model.fit_model(max_p=2, max_q=2, seasonal=False)

        model.forecast(steps=1)

        assert model.forecasting_box is not None
        assert len(model.forecasting_box["alpha"].point) == 1
