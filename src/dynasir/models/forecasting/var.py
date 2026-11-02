"""
Vector Autoregression (VAR) forecasting implementation.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR

from .base import BaseForecaster
from .registry import register_forecaster


@register_forecaster("var", aliases=["vector_ar", "vector_autoregression"])
class VARForecaster(BaseForecaster):
    """
    Wrapper around statsmodels VAR for epidemiological rate forecasting.

    This class handles the creation, fitting, and forecasting of Vector
    Autoregression models specifically designed for multivariate time series
    of epidemiological rates (or their transforms).
    """

    def __init__(self, data: Union[pd.DataFrame, np.ndarray]):
        """
        Initialize the VAR forecaster.

        Args:
            data: DataFrame or numpy array containing the multivariate time series to model.
                  Rows are time steps, columns are variables.
        """
        super().__init__(data)
        self.k_ar: int = 0

    def create_model(self) -> None:
        """
        Create the underlying VAR model.
        """
        import numpy as np

        # statsmodels VAR handles both array and dataframe, but usually expects array-like
        # If it's a DataFrame, .values extracts the numpy array.
        # If it's already an array, we use it directly.
        data_values = (
            self.data.values if isinstance(self.data, pd.DataFrame) else self.data
        )

        # Check for constant columns
        if isinstance(data_values, np.ndarray):
            col_stds = np.std(data_values, axis=0)
            has_constant = np.any(col_stds < 1e-10)

            if has_constant:
                # Store which columns are constant for later handling
                self._constant_columns = np.where(col_stds < 1e-10)[0]
                logging.warning(
                    f"Detected constant columns: {self._constant_columns.tolist()}. "
                    "VAR fitting will use trend='n' to avoid conflicts."
                )
            else:
                self._constant_columns = None
        else:
            self._constant_columns = None

        self.model = VAR(data_values)

    def fit(self, *args, **kwargs) -> None:
        """
        Fit the VAR model.

        Args:
            *args: Positional arguments for fit()
            **kwargs: Keyword arguments for fit()
        """
        if self.model is None:
            self.create_model()

        max_lag = kwargs.pop("max_lag", None)
        ic = kwargs.pop("ic", None)

        # If constant columns detected, use trend='n' to avoid conflicts
        if hasattr(self, "_constant_columns") and self._constant_columns is not None:
            if "trend" not in kwargs:
                kwargs["trend"] = "n"
                logging.info("Using trend='n' (no trend) due to constant columns")

        if max_lag is not None and ic is not None:
            # Select optimal lag order
            # Pass trend parameter to select_order as well
            selector = self.model.select_order(
                maxlags=max_lag, trend=kwargs.get("trend", "c")
            )
            # The chosen lag is stored in different attributes depending on IC
            # selector.aic, selector.bic, selector.hqic, selector.fpe
            optimal_lag = getattr(selector, ic.lower(), selector.aic)
            self.fitted_model = self.model.fit(optimal_lag, *args, **kwargs)
            self.k_ar = optimal_lag
        else:
            # Fit with default lag (or already specified lag)
            self.fitted_model = self.model.fit(*args, **kwargs)
            self.k_ar = self.fitted_model.k_ar

    def forecast_interval(
        self, steps: int, **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate point forecasts and confidence intervals.

        Args:
            steps: Number of steps to forecast
            **kwargs: Additional arguments for forecast_interval

        Returns:
            Tuple of (lower_bound, point_forecast, upper_bound) arrays
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before forecasting")

        data_values = (
            self.data.values if isinstance(self.data, pd.DataFrame) else self.data
        )
        return self.fitted_model.forecast_interval(data_values, steps, **kwargs)

    @property
    def backend_name(self) -> str:
        """Return the backend identifier."""
        return "var"
