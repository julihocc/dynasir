"""
Unit tests for the VARForecasting class.
"""

import numpy as np
import pandas as pd
import pytest

from dynasir.data import DataContainer
from dynasir.models.var_forecasting import VARForecasting


class TestVARForecastingSIRD:
    """Test VARForecasting class functionality with SIRD (3-rate) model."""

    @pytest.fixture
    def sample_sird_container(self):
        """Create sample SIRD DataContainer for testing."""
        dates = pd.date_range("2020-01-01", periods=50, freq="D")
        sample_data = pd.DataFrame(
            {
                "C": np.cumsum(np.random.poisson(10, 50)) + 100,
                "D": np.cumsum(np.random.poisson(1, 50)) + 1,
                "N": [1000000] * 50,
            },
            index=dates,
        )
        return DataContainer(sample_data, window=7)

    @pytest.fixture
    def var_forecasting_sird(self, sample_sird_container):
        """Create a VARForecasting instance for SIRD testing."""
        data = sample_sird_container.data
        active_logit_ratios = ["logit_alpha", "logit_beta", "logit_gamma"]
        logit_ratios_values = data[active_logit_ratios].values
        window = sample_sird_container.window
        return VARForecasting(data, logit_ratios_values, window, active_logit_ratios)

    def test_var_forecasting_init_sird(self, var_forecasting_sird):
        """Test VARForecasting initialization with 3 rates."""
        assert var_forecasting_sird.data is not None
        assert var_forecasting_sird.logit_ratios_values is not None
        assert var_forecasting_sird.logit_ratios_values.shape[1] == 3
        assert var_forecasting_sird.window == 7
        assert var_forecasting_sird.forecaster is None
        assert var_forecasting_sird.days_to_forecast is None
        assert len(var_forecasting_sird.active_logit_ratios) == 3

    def test_create_logit_ratios_model_sird(self, var_forecasting_sird):
        """Test creation of the underlying VAR model with 3 rates."""
        var_forecasting_sird.create_logit_ratios_model()
        assert var_forecasting_sird.forecaster is not None
        assert var_forecasting_sird.forecaster.model is not None

    def test_fit_logit_ratios_model_sird(self, var_forecasting_sird):
        """Test fitting of the VAR model with 3 rates."""
        var_forecasting_sird.create_logit_ratios_model()
        var_forecasting_sird.fit_logit_ratios_model()
        assert var_forecasting_sird.forecaster.fitted_model is not None
        assert var_forecasting_sird.days_to_forecast is not None
        assert var_forecasting_sird.days_to_forecast > 0

    def test_forecast_logit_ratios_sird(self, var_forecasting_sird):
        """Test forecasting of logit ratios with 3 rates."""
        var_forecasting_sird.create_logit_ratios_model()
        var_forecasting_sird.fit_logit_ratios_model()
        var_forecasting_sird.forecast_logit_ratios(steps=5)

        assert var_forecasting_sird.forecasting_box is not None
        assert var_forecasting_sird.forecasting_interval is not None
        assert len(var_forecasting_sird.forecasting_interval) == 5

        # Check that all 3 rates and their logit versions are present
        for rate in [
            "alpha",
            "beta",
            "gamma",
            "logit_alpha",
            "logit_beta",
            "logit_gamma",
        ]:
            assert rate in var_forecasting_sird.forecasting_box

        # Check that delta is NOT present
        assert "delta" not in var_forecasting_sird.forecasting_box
        assert "logit_delta" not in var_forecasting_sird.forecasting_box

    def test_forecasting_box_structure_sird(self, var_forecasting_sird):
        """Test that forecasting_box has correct structure for SIRD."""
        var_forecasting_sird.create_logit_ratios_model()
        var_forecasting_sird.fit_logit_ratios_model()
        var_forecasting_sird.forecast_logit_ratios(steps=10)

        # Each rate should have lower, point, upper forecasts
        for rate in ["alpha", "beta", "gamma"]:
            assert rate in var_forecasting_sird.forecasting_box
            df = var_forecasting_sird.forecasting_box[rate]
            assert "lower" in df.columns
            assert "point" in df.columns
            assert "upper" in df.columns
            assert len(df) == 10


class TestVARForecastingSIRDV:
    """Test VARForecasting class functionality with SIRDV (4-rate) model."""

    @pytest.fixture
    def sample_sirdv_container(self):
        """Create sample SIRDV DataContainer for testing."""
        dates = pd.date_range("2020-01-01", periods=50, freq="D")

        # Add vaccination data starting partway through
        vaccinations = np.zeros(50)
        vaccinations[20:] = np.cumsum(np.random.exponential(1000, 30))

        sample_data = pd.DataFrame(
            {
                "C": np.cumsum(np.random.poisson(10, 50)) + 100,
                "D": np.cumsum(np.random.poisson(1, 50)) + 1,
                "N": [1000000] * 50,
                "V": vaccinations,
            },
            index=dates,
        )
        return DataContainer(sample_data, window=7)

    @pytest.fixture
    def var_forecasting_sirdv(self, sample_sirdv_container):
        """Create a VARForecasting instance for SIRDV testing."""
        data = sample_sirdv_container.data
        active_logit_ratios = [
            "logit_alpha",
            "logit_beta",
            "logit_gamma",
            "logit_delta",
        ]
        logit_ratios_values = data[active_logit_ratios].values
        window = sample_sirdv_container.window
        return VARForecasting(data, logit_ratios_values, window, active_logit_ratios)

    def test_var_forecasting_init_sirdv(self, var_forecasting_sirdv):
        """Test VARForecasting initialization with 4 rates."""
        assert var_forecasting_sirdv.data is not None
        assert var_forecasting_sirdv.logit_ratios_values is not None
        assert var_forecasting_sirdv.logit_ratios_values.shape[1] == 4
        assert var_forecasting_sirdv.window == 7
        assert var_forecasting_sirdv.forecaster is None
        assert var_forecasting_sirdv.days_to_forecast is None
        assert len(var_forecasting_sirdv.active_logit_ratios) == 4

    def test_create_logit_ratios_model_sirdv(self, var_forecasting_sirdv):
        """Test creation of the underlying VAR model with 4 rates."""
        var_forecasting_sirdv.create_logit_ratios_model()
        assert var_forecasting_sirdv.forecaster is not None
        assert var_forecasting_sirdv.forecaster.model is not None

    def test_fit_logit_ratios_model_sirdv(self, var_forecasting_sirdv):
        """Test fitting of the VAR model with 4 rates."""
        var_forecasting_sirdv.create_logit_ratios_model()
        var_forecasting_sirdv.fit_logit_ratios_model()
        assert var_forecasting_sirdv.forecaster.fitted_model is not None
        assert var_forecasting_sirdv.days_to_forecast is not None
        assert var_forecasting_sirdv.days_to_forecast > 0

    def test_forecast_logit_ratios_sirdv(self, var_forecasting_sirdv):
        """Test forecasting of logit ratios with 4 rates."""
        var_forecasting_sirdv.create_logit_ratios_model()
        var_forecasting_sirdv.fit_logit_ratios_model()
        var_forecasting_sirdv.forecast_logit_ratios(steps=5)

        assert var_forecasting_sirdv.forecasting_box is not None
        assert var_forecasting_sirdv.forecasting_interval is not None
        assert len(var_forecasting_sirdv.forecasting_interval) == 5

        # Check that all 4 rates and their logit versions are present
        for rate in [
            "alpha",
            "beta",
            "gamma",
            "delta",
            "logit_alpha",
            "logit_beta",
            "logit_gamma",
            "logit_delta",
        ]:
            assert rate in var_forecasting_sirdv.forecasting_box

    def test_forecasting_box_structure_sirdv(self, var_forecasting_sirdv):
        """Test that forecasting_box has correct structure for SIRDV."""
        var_forecasting_sirdv.create_logit_ratios_model()
        var_forecasting_sirdv.fit_logit_ratios_model()
        var_forecasting_sirdv.forecast_logit_ratios(steps=10)

        # Each rate should have lower, point, upper forecasts
        for rate in ["alpha", "beta", "gamma", "delta"]:
            assert rate in var_forecasting_sirdv.forecasting_box
            df = var_forecasting_sirdv.forecasting_box[rate]
            assert "lower" in df.columns
            assert "point" in df.columns
            assert "upper" in df.columns
            assert len(df) == 10

    def test_inverse_logit_transformation_sirdv(self, var_forecasting_sirdv):
        """Test that inverse logit transformation is applied to all 4 rates."""
        var_forecasting_sirdv.create_logit_ratios_model()
        var_forecasting_sirdv.fit_logit_ratios_model()
        var_forecasting_sirdv.forecast_logit_ratios(steps=5)

        # All transformed rates should be between 0 and 1
        for rate in ["alpha", "beta", "gamma", "delta"]:
            df = var_forecasting_sirdv.forecasting_box[rate]
            assert (df >= 0).all().all()
            assert (df <= 1).all().all()


class TestVARForecastingBackwardCompatibility:
    """Test backward compatibility with existing SIRD tests."""

    @pytest.fixture
    def sample_data_container(self):
        """Create sample DataContainer for backward compatibility testing."""
        dates = pd.date_range("2020-01-01", periods=50, freq="D")
        sample_data = pd.DataFrame(
            {
                "C": np.cumsum(np.random.poisson(10, 50)) + 100,
                "D": np.cumsum(np.random.poisson(1, 50)) + 1,
                "N": [1000000] * 50,
            },
            index=dates,
        )
        return DataContainer(sample_data, window=7)

    @pytest.fixture
    def var_forecasting_instance(self, sample_data_container):
        """Create a VARForecasting instance for backward compatibility testing."""
        data = sample_data_container.data
        active_logit_ratios = ["logit_alpha", "logit_beta", "logit_gamma"]
        logit_ratios_values = data[active_logit_ratios].values
        window = sample_data_container.window
        return VARForecasting(data, logit_ratios_values, window, active_logit_ratios)

    def test_var_forecasting_init(self, var_forecasting_instance):
        """Test VARForecasting initialization (backward compatibility)."""
        assert var_forecasting_instance.data is not None
        assert var_forecasting_instance.logit_ratios_values is not None
        assert var_forecasting_instance.window == 7
        assert var_forecasting_instance.forecaster is None
        assert var_forecasting_instance.days_to_forecast is None

    def test_create_logit_ratios_model(self, var_forecasting_instance):
        """Test creation of the underlying VAR model (backward compatibility)."""
        var_forecasting_instance.create_logit_ratios_model()
        assert var_forecasting_instance.forecaster is not None
        assert var_forecasting_instance.forecaster.model is not None

    def test_fit_logit_ratios_model(self, var_forecasting_instance):
        """Test fitting of the VAR model (backward compatibility)."""
        var_forecasting_instance.create_logit_ratios_model()
        var_forecasting_instance.fit_logit_ratios_model()
        assert var_forecasting_instance.forecaster.fitted_model is not None
        assert var_forecasting_instance.days_to_forecast is not None
        assert var_forecasting_instance.days_to_forecast > 0

    def test_forecast_logit_ratios(self, var_forecasting_instance):
        """Test forecasting of logit ratios (backward compatibility)."""
        var_forecasting_instance.create_logit_ratios_model()
        var_forecasting_instance.fit_logit_ratios_model()
        var_forecasting_instance.forecast_logit_ratios(steps=5)

        assert var_forecasting_instance.forecasting_box is not None
        assert var_forecasting_instance.forecasting_interval is not None
        assert len(var_forecasting_instance.forecasting_interval) == 5

        for rate in [
            "alpha",
            "beta",
            "gamma",
            "logit_alpha",
            "logit_beta",
            "logit_gamma",
        ]:
            assert rate in var_forecasting_instance.forecasting_box
