"""
Forecasting models for epidemiological parameters.

This module provides interfaces and implementations for forecasting time-dependent
parameters (like infection rates) using various statistical and ML methods.

Available Backends:
    - VAR: Vector Autoregression (statsmodels) - default
    - Prophet: Facebook Prophet for seasonal patterns
    - ARIMA: Auto-ARIMA (pmdarima) for univariate modeling
    - LSTM: Neural networks (stub - not yet implemented)
"""

from .arima import ARIMAForecaster
from .base import BaseForecaster
from .lstm import LSTMForecaster
from .orchestrator import ForecastingOrchestrator

# Import new backends to trigger registration
# These use lazy imports internally, so no hard dependencies
from .prophet import ProphetForecaster
from .registry import ForecasterRegistry, register_forecaster
from .var import VARForecaster

__all__ = [
    "BaseForecaster",
    "ForecastingOrchestrator",
    "ForecasterRegistry",
    "register_forecaster",
    "VARForecaster",
    "ProphetForecaster",
    "ARIMAForecaster",
    "LSTMForecaster",
]
