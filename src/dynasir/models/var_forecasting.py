"""
Vector Autoregression (VAR) forecasting implementation.
"""

import logging
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from ..core.constants import FORECASTING_LEVELS, LOGIT_RATIOS
from ..data.frequency_handlers import make_forecast_index
from ..utils.transformations import logistic_function
from .forecasting.var import VARForecaster


class VARForecasting:
    """
    Encapsulates the VAR forecasting logic extracted from the Model class.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        logit_ratios_values: np.ndarray,
        window: int,
        active_logit_ratios: Optional[list] = None,
    ):
        self.data = data
        self.logit_ratios_values = logit_ratios_values
        self.window = window
        # Use provided active ratios or default to all LOGIT_RATIOS
        self.active_logit_ratios = (
            active_logit_ratios
            if active_logit_ratios is not None
            else list(LOGIT_RATIOS)
        )

        # Log rate count detection
        n_rates = len(self.active_logit_ratios)
        model_type = "SIRDV (4-rate)" if n_rates == 4 else "SIRD (3-rate)"
        logging.info(f"VAR forecasting initialized with {n_rates} rates: {model_type}")

        self.forecaster: Optional[VARForecaster] = None
        self.forecasted_logit_ratios: Optional[pd.DataFrame] = None
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
        """Get the underlying VAR model from the forecaster (for backward compatibility)."""
        return self.forecaster.model if self.forecaster else None

    @property
    def logit_ratios_model_fitted(self):
        """Get the fitted VAR model from the forecaster (for backward compatibility)."""
        return self.forecaster.fitted_model if self.forecaster else None

    def create_logit_ratios_model(self, *args, **kwargs) -> None:
        """
        Create VAR model for logit-transformed rates.

        Args:
            *args: Positional arguments for VAR constructor
            **kwargs: Keyword arguments for VAR constructor
        """
        self.forecaster = VARForecaster(self.logit_ratios_values)
        self.forecaster.create_model(*args, **kwargs)

    def fit_logit_ratios_model(self, *args, **kwargs) -> None:
        """
        Fit the VAR model to logit-transformed rates.

        Args:
            *args: Positional arguments for VAR.fit()
            **kwargs: Keyword arguments for VAR.fit()
        """
        if self.forecaster is None:
            self.create_logit_ratios_model()

        self.forecaster.fit(*args, **kwargs)

        if self.steps_to_forecast is None:
            self.steps_to_forecast = self.forecaster.k_ar + self.window

    def forecast_logit_ratios(self, steps: Optional[int] = None, **kwargs) -> None:
        """
        Generate forecasts for logit-transformed rates.

        Args:
            steps: Number of forecast periods (overrides the configured horizon)
            **kwargs: Keyword arguments for forecast_interval()
        """
        if steps is not None:
            self.steps_to_forecast = steps
        self.forecasting_interval = make_forecast_index(
            self.data.index, self.steps_to_forecast
        )
        self.forecast_index_start = (
            self.forecasting_interval[0] if len(self.forecasting_interval) else None
        )
        self.forecast_index_stop = (
            self.forecasting_interval[-1] if len(self.forecasting_interval) else None
        )
        try:
            self.forecasted_logit_ratios_tuple_arrays = (
                self.forecaster.forecast_interval(self.steps_to_forecast, **kwargs)
            )
        except Exception as e:
            raise Exception(e)

        # Extract (lower, point, upper) arrays
        # Each is shape (steps, n_variables)
        lower_bounds, point_forecasts, upper_bounds = (
            self.forecasted_logit_ratios_tuple_arrays
        )

        # Dynamically create forecasting_box based on active logit ratios
        self.forecasting_box = {}
        for i, logit_ratio_name in enumerate(self.active_logit_ratios):
            # Extract i-th variable from each forecast array
            self.forecasting_box[logit_ratio_name] = pd.DataFrame(
                {
                    "lower": lower_bounds[:, i],
                    "point": point_forecasts[:, i],
                    "upper": upper_bounds[:, i],
                },
                index=self.forecasting_interval,
            )

        # Apply inverse logit (logistic function) to get original rates
        for logit_ratio in self.active_logit_ratios:
            # Remove "logit_" prefix to get original rate name
            rate_name = logit_ratio.replace("logit_", "")
            self.forecasting_box[rate_name] = self.forecasting_box[logit_ratio].apply(
                logistic_function
            )
