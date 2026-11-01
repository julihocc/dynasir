"""
Auto-ARIMA forecasting backend using pmdarima.

This module provides an ARIMA-based forecaster that uses automatic order selection
(auto_arima) for each epidemiological rate independently. ARIMA models are effective
for stationary time series with autocorrelation patterns.
"""

import logging
from typing import Any, Optional, Tuple, Union

import numpy as np
import pandas as pd

from .base import BaseForecaster
from .registry import register_forecaster


def _lazy_import_pmdarima():
    """
    Lazy import for pmdarima package.

    Returns:
        auto_arima function from pmdarima

    Raises:
        ImportError: If pmdarima is not installed with installation instructions
    """
    try:
        from pmdarima import auto_arima

        return auto_arima
    except ImportError as e:
        raise ImportError(
            "ARIMA backend requires the 'pmdarima' package. "
            "Install it with: pip install pmdarima\n"
            "Or install dynasir with ARIMA support: pip install 'dynasir[arima]'\n"
            f"Original error: {e}"
        )


@register_forecaster("arima", aliases=["auto_arima", "autoarima"])
class ARIMAForecaster(BaseForecaster):
    """
    Auto-ARIMA forecasting backend for epidemiological rates.

    This forecaster uses the auto_arima algorithm from pmdarima to automatically
    select optimal ARIMA(p,d,q) orders for each rate independently. Auto-ARIMA
    performs a stepwise search over model space to minimize information criteria
    (AIC, BIC, etc.).

    ARIMA models are particularly effective for:
    - Stationary or differenced stationary time series
    - Data with autocorrelation structure
    - Short to medium-term forecasts

    The forecaster creates N independent ARIMA models (where N = 3 for SIRD
    or N = 4 for SIRDV) and uses bootstrap or analytical methods for confidence
    interval estimation.

    Attributes:
        data: Input time series data (T, n_rates)
        models: List of auto_arima search results (one per rate)
        fitted_models: List of fitted ARIMA models after training
        n_rates: Number of rates being forecasted

    Examples:
        Basic usage:

        >>> from dynasir.models.forecasting.arima import ARIMAForecaster
        >>> import numpy as np
        >>>
        >>> # SIRD data (3 rates)
        >>> data = np.random.rand(100, 3)
        >>> forecaster = ARIMAForecaster(data)
        >>> forecaster.create_model()
        >>> forecaster.fit(max_p=5, max_q=5, seasonal=False)
        >>> lower, point, upper = forecaster.forecast_interval(steps=30)
        >>> print(lower.shape, point.shape, upper.shape)
        (30, 3) (30, 3) (30, 3)

        With seasonal ARIMA:

        >>> forecaster = ARIMAForecaster(data)
        >>> forecaster.create_model()
        >>> forecaster.fit(
        ...     max_p=3,
        ...     max_q=3,
        ...     seasonal=True,
        ...     m=7  # Weekly seasonality
        ... )
        >>> lower, point, upper = forecaster.forecast_interval(steps=14)

    References:
        - pmdarima documentation: http://alkaline-ml.com/pmdarima/
        - Hyndman & Khandakar (2008): "Automatic Time Series Forecasting"
    """

    def __init__(self, data: Union[pd.DataFrame, np.ndarray]):
        """
        Initialize ARIMA forecaster with time series data.

        Args:
            data: Multivariate time series data, shape (T, n_rates)
                 where T is time steps and n_rates is 3 (SIRD) or 4 (SIRDV)

        Raises:
            ValueError: If data is empty or invalid
            ImportError: If pmdarima package is not installed
        """
        super().__init__(data)

        # Ensure data is numpy array for consistent handling
        if isinstance(data, pd.DataFrame):
            self.data_array = data.values
            self.data_index = data.index
        else:
            self.data_array = data
            self.data_index = None

        self.n_rates = self.data_array.shape[1]
        self.models: Optional[list] = None
        self.fitted_models: Optional[list] = None

        # Verify pmdarima is available (lazy import on first use)
        self._auto_arima_func = None

        logging.info(f"ARIMAForecaster initialized with {self.n_rates} rates")

    @property
    def backend_name(self) -> str:
        """Return the canonical name of this backend."""
        return "arima"

    def create_model(self, **kwargs) -> None:
        """
        Prepare for ARIMA model creation.

        For ARIMA, model creation and fitting happen together in auto_arima,
        so this method just stores configuration and verifies pmdarima availability.

        Args:
            **kwargs: Not used for ARIMA (configuration happens in fit())

        Raises:
            ImportError: If pmdarima is not installed

        Examples:
            >>> forecaster.create_model()
        """
        if self._auto_arima_func is None:
            self._auto_arima_func = _lazy_import_pmdarima()

        # For ARIMA, models are created during fit()
        # This method serves to check dependencies and prepare state
        self.models = []

        # Store in self.model for BaseForecaster compatibility
        self.model = self.models

        logging.info("ARIMA forecaster ready for fitting")

    def fit(
        self,
        max_p: int = 5,
        max_q: int = 5,
        max_d: int = 2,
        seasonal: bool = False,
        m: int = 1,
        **kwargs,
    ) -> None:
        """
        Fit auto-ARIMA models to each rate time series.

        This method uses auto_arima to automatically select the optimal ARIMA
        order (p,d,q) for each rate independently through stepwise search.

        Args:
            max_p: Maximum AR order to search (default 5)
            max_q: Maximum MA order to search (default 5)
            max_d: Maximum differencing order (default 2)
            seasonal: Enable seasonal ARIMA (SARIMA) if True (default False)
            m: Seasonal period (e.g., 7 for weekly, 12 for monthly) (default 1)
            **kwargs: Additional auto_arima parameters:
                start_p, start_q: Starting values for search
                stepwise: Use stepwise algorithm (default True)
                trace: Print search progress (default False)
                information_criterion: 'aic', 'bic', 'hqic', 'oob' (default 'aic')
                suppress_warnings: Suppress convergence warnings (default True)

        Raises:
            ValueError: If create_model() hasn't been called
            RuntimeError: If auto_arima fails for any rate

        Examples:
            >>> # Non-seasonal ARIMA
            >>> forecaster.create_model()
            >>> forecaster.fit(max_p=5, max_q=5, seasonal=False)
            >>>
            >>> # Seasonal ARIMA with weekly pattern
            >>> forecaster.fit(max_p=3, max_q=3, seasonal=True, m=7)
        """
        if self._auto_arima_func is None:
            raise ValueError(
                "auto_arima function not initialized. Call create_model() first."
            )

        self.fitted_models = []

        # Set defaults for auto_arima
        kwargs.setdefault("stepwise", True)
        kwargs.setdefault("suppress_warnings", True)
        kwargs.setdefault("error_action", "ignore")
        kwargs.setdefault("information_criterion", "aic")

        # Fit each rate independently
        for i in range(self.n_rates):
            try:
                # Run auto_arima to find optimal order
                fitted_model = self._auto_arima_func(
                    self.data_array[:, i],
                    max_p=max_p,
                    max_q=max_q,
                    max_d=max_d,
                    seasonal=seasonal,
                    m=m,
                    **kwargs,
                )
                self.fitted_models.append(fitted_model)

                # Log selected order
                order = fitted_model.order
                if seasonal:
                    seasonal_order = fitted_model.seasonal_order
                    logging.info(f"Rate {i}: ARIMA{order} × SARIMA{seasonal_order}")
                else:
                    logging.info(f"Rate {i}: ARIMA{order}")

            except Exception as e:
                logging.error(f"Failed to fit ARIMA model for rate {i}: {e}")
                raise RuntimeError(
                    f"auto_arima failed for rate {i}. "
                    f"Try adjusting max_p, max_q, or enabling seasonal=True. "
                    f"Error: {e}"
                )

        # Store in self.fitted_model for BaseForecaster compatibility
        self.fitted_model = self.fitted_models

        logging.info(f"Fitted {self.n_rates} ARIMA models successfully")

    def forecast_interval(
        self, steps: int, alpha: float = 0.05, **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate forecasts with confidence intervals for all rates.

        pmdarima's predict() method returns confidence intervals based on
        the forecast error variance under the assumption of normally
        distributed errors.

        Args:
            steps: Number of forecast periods
            alpha: Significance level for confidence intervals (default 0.05 for 95% CI)
            **kwargs: Additional forecast parameters:
                return_conf_int: Always True (internal)

        Returns:
            Tuple of (lower, point, upper) arrays, each with shape (steps, n_rates)
            - lower: Lower confidence bound (alpha/2 quantile)
            - point: Point forecast
            - upper: Upper confidence bound (1 - alpha/2 quantile)

        Raises:
            ValueError: If fit() hasn't been called
            ValueError: If steps < 1

        Examples:
            >>> lower, point, upper = forecaster.forecast_interval(steps=30)
            >>> # 95% confidence intervals (default alpha=0.05)
            >>>
            >>> # Custom confidence level (90% CI)
            >>> lower, point, upper = forecaster.forecast_interval(steps=30, alpha=0.1)
        """
        if self.fitted_models is None:
            raise ValueError(
                "Models must be fitted before forecasting. Call fit() first."
            )

        if steps < 1:
            raise ValueError(f"steps must be >= 1, got {steps}")

        # Initialize output arrays
        lower = np.zeros((steps, self.n_rates))
        point = np.zeros((steps, self.n_rates))
        upper = np.zeros((steps, self.n_rates))

        # Generate forecasts for each rate
        for i, model in enumerate(self.fitted_models):
            # Get point forecast and confidence intervals
            forecast, conf_int = model.predict(
                n_periods=steps, return_conf_int=True, alpha=alpha
            )

            point[:, i] = forecast
            lower[:, i] = conf_int[:, 0]  # Lower bound
            upper[:, i] = conf_int[:, 1]  # Upper bound

        logging.info(
            f"Generated {steps}-step forecasts for {self.n_rates} rates "
            f"with alpha={alpha}"
        )

        return lower, point, upper
