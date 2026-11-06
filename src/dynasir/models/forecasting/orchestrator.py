"""
Backend-agnostic forecasting orchestrator.

This module provides the ForecastingOrchestrator class which handles domain-specific
logic (logit transformations, rate selection, forecasting_box creation) while
delegating the actual time series forecasting to pluggable backend implementations.
"""

import logging
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from ...core.config import get_settings
from ...core.constants import FORECASTING_LEVELS, LOGIT_RATIOS
from ...data.frequency_handlers import make_forecast_index
from ...utils.transformations import logistic_function
from .base import BaseForecaster
from .registry import ForecasterRegistry


class ForecastingOrchestrator:
    """
    Backend-agnostic orchestrator for epidemiological rate forecasting.

    This class separates epidemiological domain logic from the statistical
    forecasting implementation. It handles:
    - Backend selection and instantiation via registry
    - Logit/inverse-logit transformations (domain-specific)
    - Rate selection (SIRD: 3 rates vs SIRDV: 4 rates)
    - forecasting_box structure creation for downstream compatibility

    The orchestrator is compatible with any forecasting backend that implements
    the BaseForecaster interface (VAR, Prophet, ARIMA, LSTM, etc.).

    Attributes:
        data: Full DataFrame with all columns
        logit_ratios_values: Array of logit-transformed rates (T, n_rates)
        window: Smoothing window size
        backend_name: Name of the forecasting backend being used
        active_logit_ratios: List of active logit ratio names
        forecaster: Instance of the selected forecasting backend
        forecasting_box: Dict structure with rate forecasts (lower/point/upper)

    Examples:
        Using with VAR backend (default):

        >>> from dynasir.models.forecasting.orchestrator import ForecastingOrchestrator
        >>> orchestrator = ForecastingOrchestrator(
        ...     data=data,
        ...     logit_ratios_values=logit_vals,
        ...     window=7,
        ...     backend="var"
        ... )
        >>> orchestrator.create_logit_ratios_model()
        >>> orchestrator.fit_logit_ratios_model(max_lag=10, ic="aic")
        >>> orchestrator.forecast_logit_ratios(steps=30)
        >>> print(orchestrator.forecasting_box.keys())
        dict_keys(['logit_alpha', 'logit_beta', 'logit_gamma', 'alpha', 'beta', 'gamma'])

        Using with Prophet backend:

        >>> orchestrator = ForecastingOrchestrator(
        ...     data=data,
        ...     logit_ratios_values=logit_vals,
        ...     window=7,
        ...     backend="prophet"
        ... )
        >>> orchestrator.create_logit_ratios_model(yearly_seasonality=True)
        >>> orchestrator.fit_logit_ratios_model()
        >>> orchestrator.forecast_logit_ratios(steps=30)
    """

    def __init__(
        self,
        data: pd.DataFrame,
        logit_ratios_values: np.ndarray,
        window: int,
        active_logit_ratios: Optional[list] = None,
        backend: str = "var",
        frequency: Optional[str] = None,
        rate_index: Optional[pd.DatetimeIndex] = None,
    ):
        """
        Initialize the forecasting orchestrator.

        Args:
            data: Full DataFrame with all epidemiological data
            logit_ratios_values: Array of logit-transformed rates, shape (T, n_rates)
                                where T is time steps and n_rates is 3 (SIRD) or 4 (SIRDV)
            window: Smoothing window size in days
            active_logit_ratios: List of active logit ratio column names
                                If None, defaults to all LOGIT_RATIOS from constants
            backend: Forecasting backend to use ('var', 'prophet', 'arima', 'lstm')

        Raises:
            ValueError: If backend is not registered

        Examples:
            >>> # SIRD model (3 rates)
            >>> orchestrator = ForecastingOrchestrator(
            ...     data=data,
            ...     logit_ratios_values=np.array([[...]]),  # shape (T, 3)
            ...     window=7,
            ...     backend="var"
            ... )
            >>>
            >>> # SIRDV model (4 rates)
            >>> orchestrator = ForecastingOrchestrator(
            ...     data=data,
            ...     logit_ratios_values=np.array([[...]]),  # shape (T, 4)
            ...     window=7,
            ...     active_logit_ratios=["logit_alpha", "logit_beta", "logit_gamma", "logit_delta"],
            ...     backend="prophet"
            ... )
        """
        self.data = data
        self.logit_ratios_values = logit_ratios_values
        self.window = window
        self.backend_name = backend
        self.frequency = frequency
        self.rate_index = rate_index

        # Use provided active ratios or default to all LOGIT_RATIOS
        self.active_logit_ratios = (
            active_logit_ratios
            if active_logit_ratios is not None
            else list(LOGIT_RATIOS)
        )

        # Log initialization with model type detection
        n_rates = len(self.active_logit_ratios)
        model_type = "SIRDV (4-rate)" if n_rates == 4 else "SIRD (3-rate)"
        logging.info(
            f"Forecasting orchestrator initialized: backend='{backend}', "
            f"{n_rates} rates ({model_type})"
        )

        # Instantiate the forecaster from registry
        try:
            forecaster_class = ForecasterRegistry.get(backend)
        except ValueError as e:
            available = ForecasterRegistry.list_available()
            raise ValueError(
                f"Unknown forecasting backend '{backend}'. "
                f"Available backends: {available}. "
                f"Original error: {e}"
            )

        # Give the backend the training dates. A bare array makes Prophet
        # invent a daily index, so weekly or annual rates are fitted as days.
        n_rows = len(self.logit_ratios_values)
        if self.rate_index is not None:
            training_index = self.rate_index
        else:
            training_index = self.data.index[:n_rows]
        framed = pd.DataFrame(
            self.logit_ratios_values,
            index=training_index,
            columns=list(self.active_logit_ratios),
        )
        self.forecaster: BaseForecaster = forecaster_class(framed)
        if hasattr(self.forecaster, "column_names"):
            self.forecaster.column_names = list(self.active_logit_ratios)

        # State attributes (populated during execution)
        self.forecasted_logit_ratios_tuple_arrays: Optional[Any] = None
        self.forecasting_interval: Optional[pd.DatetimeIndex] = None
        self.forecast_index_stop: Optional[pd.Timestamp] = None
        self.forecast_index_start: Optional[pd.Timestamp] = None
        self.steps_to_forecast: Optional[int] = None
        self.forecasting_box: Optional[Dict[str, pd.DataFrame]] = None

    @property
    def days_to_forecast(self) -> Optional[int]:
        """Backward-compatible alias for the frequency-independent forecast steps."""
        return self.steps_to_forecast

    @days_to_forecast.setter
    def days_to_forecast(self, value: Optional[int]) -> None:
        self.steps_to_forecast = value

    @property
    def logit_ratios_model(self):
        """
        Get the underlying forecasting model (for backward compatibility).

        This property provides access to the backend-specific model object.
        For VAR, this returns the statsmodels.VAR instance.

        Returns:
            Backend-specific model object, or None if not created

        Examples:
            >>> orchestrator = ForecastingOrchestrator(data, logit_vals, 7, backend="var")
            >>> orchestrator.create_logit_ratios_model()
            >>> var_model = orchestrator.logit_ratios_model
            >>> print(type(var_model))
            <class 'statsmodels.tsa.vector_ar.var_model.VAR'>
        """
        return self.forecaster.model if self.forecaster else None

    @property
    def logit_ratios_model_fitted(self):
        """
        Get the fitted forecasting model (for backward compatibility).

        This property provides access to the fitted backend-specific model object.
        For VAR, this returns the VARResults instance.

        Returns:
            Backend-specific fitted model object, or None if not fitted

        Examples:
            >>> orchestrator = ForecastingOrchestrator(data, logit_vals, 7, backend="var")
            >>> orchestrator.create_logit_ratios_model()
            >>> orchestrator.fit_logit_ratios_model(max_lag=10, ic="aic")
            >>> fitted = orchestrator.logit_ratios_model_fitted
            >>> print(fitted.k_ar)  # Number of lags used
            5
        """
        return self.forecaster.fitted_model if self.forecaster else None

    def create_logit_ratios_model(self, **kwargs) -> None:
        """
        Create the forecasting model for logit-transformed rates.

        This delegates to the backend's create_model() method, passing through
        any backend-specific kwargs.

        Args:
            **kwargs: Backend-specific model creation parameters
                     VAR: (no specific kwargs)
                     Prophet: yearly_seasonality, weekly_seasonality, etc.
                     ARIMA: order, seasonal_order, etc.

        Examples:
            >>> # VAR (no specific kwargs needed)
            >>> orchestrator.create_logit_ratios_model()
            >>>
            >>> # Prophet with seasonality
            >>> orchestrator.create_logit_ratios_model(
            ...     yearly_seasonality=True,
            ...     changepoint_prior_scale=0.1
            ... )
        """
        self.forecaster.create_model(**kwargs)

    def fit_logit_ratios_model(self, **kwargs) -> None:
        """
        Fit the forecasting model to logit-transformed rates.

        This delegates to the backend's fit() method, passing through
        any backend-specific kwargs. It also sets the default forecast
        horizon if not already specified.

        Args:
            **kwargs: Backend-specific fitting parameters
                     VAR: max_lag, ic (information criterion)
                     Prophet: (fitting params usually in create_model)
                     ARIMA: max_p, max_q, seasonal

        Examples:
            >>> # VAR with lag selection
            >>> orchestrator.fit_logit_ratios_model(max_lag=10, ic="aic")
            >>>
            >>> # ARIMA with auto-selection
            >>> orchestrator.fit_logit_ratios_model(max_p=5, max_q=5, seasonal=False)
        """
        if self.forecaster.model is None:
            self.create_logit_ratios_model()

        self.forecaster.fit(**kwargs)

        # Set default forecast horizon if not specified
        # For VAR: use k_ar + window (lag order + smoothing window)
        # For others: use window only
        if self.steps_to_forecast is None:
            if hasattr(self.forecaster, "k_ar"):
                self.steps_to_forecast = self.forecaster.k_ar + self.window
            else:
                self.steps_to_forecast = self.window

    def forecast_logit_ratios(self, steps: Optional[int] = None, **kwargs) -> None:
        """
        Generate forecasts for logit-transformed rates.

        This creates the forecasting_box structure which contains both:
        1. Logit-space forecasts (logit_alpha, logit_beta, logit_gamma, [logit_delta])
        2. Rate-space forecasts (alpha, beta, gamma, [delta]) via inverse logit

        Each entry has columns: 'lower', 'point', 'upper' for confidence intervals.

        Args:
            steps: Number of forecast periods. If provided, overrides the configured horizon.
            **kwargs: Backend-specific forecast parameters
                     Common: alpha (significance level for CI; defaults to
                     the FORECASTER_ALPHA setting, 0.05)
                     Backend-specific: passed to forecast_interval()

        Raises:
            Exception: If forecasting fails, with backend name in error message

        Examples:
            >>> orchestrator.forecast_logit_ratios(steps=30)
            >>> print(orchestrator.forecasting_box.keys())
            dict_keys(['logit_alpha', 'logit_beta', 'logit_gamma',
                      'alpha', 'beta', 'gamma'])
            >>>
            >>> # Access specific forecast
            >>> alpha_forecast = orchestrator.forecasting_box['alpha']
            >>> print(alpha_forecast.columns)
            Index(['lower', 'point', 'upper'], dtype='object')
        """
        if steps is not None:
            self.steps_to_forecast = steps

        kwargs.setdefault("alpha", get_settings().FORECASTER_ALPHA)

        self.forecasting_interval = make_forecast_index(
            self.data.index, self.steps_to_forecast, self.frequency
        )
        self.forecast_index_start = (
            self.forecasting_interval[0] if len(self.forecasting_interval) else None
        )
        self.forecast_index_stop = (
            self.forecasting_interval[-1] if len(self.forecasting_interval) else None
        )

        # Generate forecasts from backend
        try:
            self.forecasted_logit_ratios_tuple_arrays = (
                self.forecaster.forecast_interval(self.steps_to_forecast, **kwargs)
            )
        except Exception as e:
            raise Exception(
                f"Forecasting failed with backend '{self.backend_name}': {e}"
            ) from e

        # Extract (lower, point, upper) arrays from backend
        # Each array has shape (steps, n_variables)
        lower_bounds, point_forecasts, upper_bounds = (
            self.forecasted_logit_ratios_tuple_arrays
        )

        # Build forecasting_box: create DataFrames for each logit ratio
        self.forecasting_box = {}

        for i, logit_ratio_name in enumerate(self.active_logit_ratios):
            # Extract i-th variable (column) from each forecast array
            self.forecasting_box[logit_ratio_name] = pd.DataFrame(
                {
                    "lower": lower_bounds[:, i],
                    "point": point_forecasts[:, i],
                    "upper": upper_bounds[:, i],
                },
                index=self.forecasting_interval,
            )

        # Invert the transforms to get the rates (alpha, beta, gamma, [delta]):
        # logistic for "logit_" columns, exp for "log_" columns
        for column in self.active_logit_ratios:
            if column.startswith("log_"):
                rate_name = column[len("log_") :]
                self.forecasting_box[rate_name] = np.exp(self.forecasting_box[column])
            else:
                rate_name = column.replace("logit_", "")
                self.forecasting_box[rate_name] = self.forecasting_box[column].apply(
                    logistic_function
                )

        # Period-cohort incidence data forecasts gamma only; the rest of the
        # cohort recovers, so beta = 1 - gamma (levels mirrored)
        if "beta" not in self.forecasting_box and "gamma" in self.forecasting_box:
            gamma = self.forecasting_box["gamma"]
            self.forecasting_box["beta"] = pd.DataFrame(
                {
                    "lower": 1 - gamma["upper"],
                    "point": 1 - gamma["point"],
                    "upper": 1 - gamma["lower"],
                },
                index=gamma.index,
            )

    def __repr__(self) -> str:
        """
        Return string representation of the orchestrator.

        Returns:
            String showing backend, model type, and state
        """
        n_rates = len(self.active_logit_ratios)
        model_type = "SIRDV" if n_rates == 4 else "SIRD"
        fitted_status = "fitted" if self.logit_ratios_model_fitted else "not fitted"
        forecasted_status = "forecasted" if self.forecasting_box else "not forecasted"

        return (
            f"ForecastingOrchestrator("
            f"backend='{self.backend_name}', "
            f"model_type={model_type}, "
            f"n_rates={n_rates}, "
            f"status={fitted_status}/{forecasted_status})"
        )
