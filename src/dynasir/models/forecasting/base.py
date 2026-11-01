"""
Base abstract class for time series forecasters.

This module defines the interface that all forecasting backends must implement
to ensure compatibility with the epydemics epidemiological modeling framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple, Union

import numpy as np
import pandas as pd


class BaseForecaster(ABC):
    """
    Abstract base class for time series forecasters.

    All forecasting backends must inherit from this class and implement the
    required abstract methods. This ensures a consistent interface across
    different forecasting methods (VAR, Prophet, ARIMA, LSTM, etc.).

    The key requirement is that all forecasters must return confidence intervals
    in the form of (lower, point, upper) tuples to ensure compatibility with
    the EpidemicSimulation's scenario generation (27 scenarios for SIRD,
    81 scenarios for SIRDV).

    Attributes:
        data: Input time series data (DataFrame or array)
        model: The underlying forecasting model object
        fitted_model: The fitted model object after training

    Examples:
        Implementing a new forecaster backend:

        >>> from dynasir.models.forecasting.base import BaseForecaster
        >>> from dynasir.models.forecasting.registry import register_forecaster
        >>>
        >>> @register_forecaster("my_method")
        >>> class MyForecaster(BaseForecaster):
        ...     @property
        ...     def backend_name(self) -> str:
        ...         return "my_method"
        ...
        ...     def create_model(self, **kwargs) -> None:
        ...         # Create your model
        ...         self.model = MyModel(**kwargs)
        ...
        ...     def fit(self, **kwargs) -> None:
        ...         # Fit the model to data
        ...         self.fitted_model = self.model.fit(self.data, **kwargs)
        ...
        ...     def forecast_interval(self, steps: int, **kwargs):
        ...         # Generate forecasts with confidence intervals
        ...         lower, point, upper = self.fitted_model.predict(steps)
        ...         return (lower, point, upper)
    """

    def __init__(self, data: Union[pd.DataFrame, np.ndarray]):
        """
        Initialize the forecaster with time series data.

        Args:
            data: Multivariate time series data with shape (T, n_variables)
                  where T is the number of time steps and n_variables is the
                  number of rates being forecasted (3 for SIRD, 4 for SIRDV).
                  Can be either a pandas DataFrame or numpy array.

        Raises:
            ValueError: If data is empty or has invalid shape
        """
        if isinstance(data, pd.DataFrame):
            if data.empty:
                raise ValueError("Data cannot be empty")
        elif isinstance(data, np.ndarray):
            if data.size == 0:
                raise ValueError("Data cannot be empty")
        else:
            raise TypeError(
                f"Data must be DataFrame or ndarray, got {type(data).__name__}"
            )

        self.data = data
        self.model: Optional[Any] = None
        self.fitted_model: Optional[Any] = None

    @abstractmethod
    def create_model(self, **kwargs) -> None:
        """
        Create the underlying forecasting model.

        This method should instantiate the backend-specific model object
        and store it in self.model. It should not fit the model yet.

        Args:
            **kwargs: Backend-specific parameters for model creation
                     Examples:
                     - VAR: No specific kwargs needed
                     - Prophet: yearly_seasonality, weekly_seasonality, etc.
                     - ARIMA: order, seasonal_order, etc.

        Raises:
            NotImplementedError: If the backend hasn't implemented this method
        """
        pass

    @abstractmethod
    def fit(self, **kwargs) -> None:
        """
        Fit the forecasting model to the data.

        This method should train the model on self.data and store the
        fitted model in self.fitted_model.

        Args:
            **kwargs: Backend-specific fitting parameters
                     Examples:
                     - VAR: max_lag (int), ic (str) - information criterion
                     - Prophet: (fitting params handled in create_model)
                     - ARIMA: max_p (int), max_q (int), seasonal (bool)

        Raises:
            ValueError: If model hasn't been created yet (call create_model first)
            NotImplementedError: If the backend hasn't implemented this method
        """
        pass

    @abstractmethod
    def forecast_interval(
        self, steps: int, **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate point forecasts with confidence intervals.

        This is the most critical method - all backends MUST return forecasts
        in the exact same format to ensure compatibility with downstream
        components (especially EpidemicSimulation).

        Args:
            steps: Number of forecast periods into the future
            **kwargs: Backend-specific forecast parameters
                     Common kwargs:
                     - alpha (float): Significance level for CI (default 0.05)
                     - Additional backend-specific parameters

        Returns:
            A tuple of three numpy arrays (lower, point, upper):
            - lower: Lower confidence bounds, shape (steps, n_variables)
            - point: Point forecasts, shape (steps, n_variables)
            - upper: Upper confidence bounds, shape (steps, n_variables)

            Each array has:
            - Rows: forecast time steps (0 to steps-1)
            - Columns: variables being forecasted (rates)

        Raises:
            ValueError: If model hasn't been fitted yet (call fit first)
            NotImplementedError: If the backend hasn't implemented this method

        Examples:
            >>> forecaster = VARForecaster(data)
            >>> forecaster.create_model()
            >>> forecaster.fit(max_lag=10, ic="aic")
            >>> lower, point, upper = forecaster.forecast_interval(steps=30)
            >>> print(lower.shape)  # (30, 3) for SIRD or (30, 4) for SIRDV
            >>> print(point.shape)  # (30, 3) for SIRD or (30, 4) for SIRDV
            >>> print(upper.shape)  # (30, 3) for SIRD or (30, 4) for SIRDV
        """
        pass

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """
        Return the canonical name of this forecasting backend.

        This name is used for:
        - Registry lookups
        - Logging and debugging
        - User-facing display

        Returns:
            Backend identifier string (e.g., 'var', 'prophet', 'arima', 'lstm')

        Examples:
            >>> forecaster = VARForecaster(data)
            >>> print(forecaster.backend_name)
            'var'
        """
        pass

    def __repr__(self) -> str:
        """
        Return string representation of the forecaster.

        Returns:
            String showing backend name and data shape
        """
        if isinstance(self.data, pd.DataFrame):
            data_shape = self.data.shape
        else:
            data_shape = self.data.shape if hasattr(self.data, "shape") else "unknown"

        fitted_status = "fitted" if self.fitted_model is not None else "not fitted"

        return (
            f"{self.__class__.__name__}("
            f"backend='{self.backend_name}', "
            f"data_shape={data_shape}, "
            f"status={fitted_status})"
        )
