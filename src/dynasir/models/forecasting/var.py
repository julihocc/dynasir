"""
Vector Autoregression (VAR) forecasting implementation.

Rate columns that do not vary (for example gamma when all deaths are zero)
make the VAR residual covariance singular. They are removed from the model
and held at their constant value in the forecast. When only one column varies,
a univariate autoregression (AutoReg) is used instead, and when none varies the
forecast is the constant itself.
"""

import logging
from typing import List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR
from statsmodels.tsa.ar_model import AutoReg, ar_select_order

from ...core.exceptions import DynaSIRError
from .base import BaseForecaster
from .registry import register_forecaster

# Columns with a standard deviation below this value are treated as constant.
CONSTANT_STD_TOLERANCE = 1e-10

# Hints shown when a rate column is constant, keyed by rate name.
_CONSTANT_RATE_HINTS = {
    "alpha": "the infection rate does not change over the training window",
    "beta": "the recovery rate does not change over the training window",
    "gamma": "deaths 'D' may be all zero (or a fixed share of cases)",
    "delta": "vaccinations 'V' may not change over the training window",
}


def _rate_name(column: str) -> str:
    for prefix in ("logit_", "log_"):
        if column.startswith(prefix):
            return column[len(prefix) :]
    return column


class _AutoRegFit:
    """Fit results for a single varying column, with a VAR-like interface."""

    def __init__(self, results, lags: Sequence[int], n_obs: int):
        self.results = results
        self.lags = list(lags)
        self.k_ar = max(self.lags) if self.lags else 0
        self._n_obs = n_obs

    def forecast_interval(
        self, y: np.ndarray, steps: int, alpha: float = 0.05, **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return ``(point, lower, upper)`` with shape ``(steps, 1)``."""
        prediction = self.results.get_prediction(
            start=self._n_obs, end=self._n_obs + steps - 1
        )
        point = np.asarray(prediction.predicted_mean).reshape(-1, 1)
        interval = np.asarray(prediction.conf_int(alpha=alpha))
        return point, interval[:, :1], interval[:, 1:2]


class _ConstantFit:
    """Fit results when no column varies: the forecast is the constant."""

    k_ar = 0

    def forecast_interval(
        self, y: np.ndarray, steps: int, alpha: float = 0.05, **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        empty = np.empty((steps, 0))
        return empty, empty, empty


@register_forecaster("var", aliases=["vector_ar", "vector_autoregression"])
class VARForecaster(BaseForecaster):
    """
    Wrapper around statsmodels VAR for epidemiological rate forecasting.

    This class handles the creation, fitting, and forecasting of Vector
    Autoregression models specifically designed for multivariate time series
    of epidemiological rates (or their transforms).

    Constant columns are excluded from the VAR and forecast as their constant
    value at every level. With one varying column the backend fits an AutoReg
    model; with none it returns the constants.
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
        # Optional column names, used in log and error messages.
        self.column_names: Optional[List[str]] = (
            list(data.columns) if isinstance(data, pd.DataFrame) else None
        )
        self._free_idx: Optional[np.ndarray] = None
        self._constant_columns: Optional[np.ndarray] = None
        self._constant_values: Optional[np.ndarray] = None

    @property
    def _values(self) -> np.ndarray:
        values = self.data.values if isinstance(self.data, pd.DataFrame) else self.data
        values = np.asarray(values, dtype=float)
        if values.ndim == 1:
            values = values.reshape(-1, 1)
        return values

    def _names(self, idx: Sequence[int]) -> List[str]:
        if self.column_names is not None and len(self.column_names) == (
            self._values.shape[1]
        ):
            return [self.column_names[i] for i in idx]
        return [f"column {i}" for i in idx]

    def create_model(self) -> None:
        """
        Create the underlying model.

        Splits the columns into varying and constant ones. Builds a VAR on the
        varying columns when there are at least two; otherwise the model is
        created in :meth:`fit`.
        """
        values = self._values
        col_stds = np.nanstd(values, axis=0)
        is_free = np.isfinite(values).all(axis=0) & (col_stds >= CONSTANT_STD_TOLERANCE)
        self._free_idx = np.where(is_free)[0]
        constant_idx = np.where(~is_free)[0]
        self._constant_columns = constant_idx if len(constant_idx) else None
        self._constant_values = np.nanmean(values, axis=0)

        if self._constant_columns is not None:
            names = self._names(constant_idx)
            hints = [
                (
                    f"{name} ({_CONSTANT_RATE_HINTS[_rate_name(name)]})"
                    if _rate_name(name) in _CONSTANT_RATE_HINTS
                    else name
                )
                for name in names
            ]
            logging.warning(
                "Constant rate columns are held fixed in the forecast and left "
                f"out of the model: {', '.join(hints)}."
            )

        if len(self._free_idx) >= 2:
            self.model = VAR(values[:, self._free_idx])
        else:
            # The univariate or constant model is built in fit().
            self.model = None

    def _fit_var(self, max_lag, ic, *args, **kwargs) -> None:
        names = self._names(self._free_idx)
        try:
            if max_lag is not None and ic is not None:
                selector = self.model.select_order(
                    maxlags=max_lag, trend=kwargs.get("trend", "c")
                )
                # The chosen lag is stored as selector.aic, .bic, .hqic or .fpe
                optimal_lag = getattr(selector, ic.lower(), selector.aic)
                self.fitted_model = self.model.fit(optimal_lag, *args, **kwargs)
                self.k_ar = optimal_lag
            else:
                self.fitted_model = self.model.fit(*args, **kwargs)
                self.k_ar = self.fitted_model.k_ar
        except np.linalg.LinAlgError as e:
            raise DynaSIRError(
                "VAR fitting failed because the residual covariance of the rates "
                f"{names} is singular ({e}). This usually means one rate is an "
                "exact function of the others, or the series is too short for "
                "the requested max_lag."
            ) from e

    def _fit_autoreg(self, max_lag, ic, *args, **kwargs) -> None:
        y = self._values[:, self._free_idx[0]]
        trend = kwargs.get("trend", "c")
        if max_lag is not None:
            criterion = (ic or "aic").lower()
            if criterion not in ("aic", "bic", "hqic"):
                criterion = "aic"
            selector = ar_select_order(y, maxlag=max_lag, ic=criterion, trend=trend)
            lags = list(selector.ar_lags or [])
        else:
            n_lags = args[0] if args else kwargs.get("maxlags", 1)
            lags = list(range(1, int(n_lags or 0) + 1))
        results = AutoReg(y, lags=lags or 0, trend=trend).fit()
        self.fitted_model = _AutoRegFit(results, lags, len(y))
        self.k_ar = self.fitted_model.k_ar
        logging.info(
            f"Only {self._names(self._free_idx)[0]} varies; fitted AutoReg "
            f"with lags {lags or 'none'}."
        )

    def fit(self, *args, **kwargs) -> None:
        """
        Fit the model.

        Args:
            *args: Positional arguments for VAR.fit()
            **kwargs: Keyword arguments for VAR.fit(). ``max_lag`` and ``ic``
                select the lag order.
        """
        if self._free_idx is None:
            self.create_model()

        max_lag = kwargs.pop("max_lag", None)
        ic = kwargs.pop("ic", None)

        n_free = len(self._free_idx)
        if n_free >= 2:
            self._fit_var(max_lag, ic, *args, **kwargs)
        elif n_free == 1:
            self._fit_autoreg(max_lag, ic, *args, **kwargs)
        else:
            logging.warning(
                "No rate column varies; the forecast repeats the constant rates."
            )
            self.fitted_model = _ConstantFit()
            self.k_ar = 0

    def forecast_interval(
        self, steps: int, **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate point forecasts and confidence intervals.

        Args:
            steps: Number of steps to forecast
            **kwargs: Additional arguments for forecast_interval (e.g. ``alpha``)

        Returns:
            Tuple of (lower_bound, point_forecast, upper_bound) arrays, each with
            shape (steps, n_columns) in the original column order.
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before forecasting")

        values = self._values
        free_values = values[:, self._free_idx]
        if len(self._free_idx) >= 2 and self.k_ar == 0:
            point_free, lower_free, upper_free = self._var_lag0_interval(
                steps, kwargs.get("alpha", 0.05)
            )
        else:
            # statsmodels returns (point, lower, upper)
            point_free, lower_free, upper_free = self.fitted_model.forecast_interval(
                free_values, steps, **kwargs
            )

        lower = np.tile(self._constant_values, (steps, 1)).astype(float)
        point = lower.copy()
        upper = lower.copy()
        if len(self._free_idx):
            lower[:, self._free_idx] = lower_free
            point[:, self._free_idx] = point_free
            upper[:, self._free_idx] = upper_free
        return lower, point, upper

    def _var_lag0_interval(
        self, steps: int, alpha: float
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Forecast a VAR(0), which statsmodels cannot forecast directly.

        With no lags the forecast is the deterministic term and the forecast
        error covariance is the residual covariance at every step.
        """
        from scipy.stats import norm

        fitted = self.fitted_model
        n_vars = fitted.neqs
        if fitted.trend == "n":
            mean = np.zeros(n_vars)
        elif fitted.trend == "c":
            mean = np.asarray(fitted.coefs_exog)[:, 0]
        else:
            raise DynaSIRError(
                f"Forecasting a VAR(0) with trend='{fitted.trend}' is not supported."
            )
        point = np.tile(mean, (steps, 1))
        sigma = np.sqrt(np.diag(np.asarray(fitted.sigma_u)))
        q = norm.ppf(1 - alpha / 2)
        return point, point - q * sigma, point + q * sigma

    @property
    def backend_name(self) -> str:
        """Return the backend identifier."""
        return "var"
