"""SIRD epidemiological model with VAR time series forecasting."""

import hashlib
import json
import logging
import math
import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd
from box import Box

from dynasir.core.config import get_settings

from ..analysis.evaluation import evaluate_forecast as _evaluate_forecast
from ..analysis.visualization import visualize_results as _visualize_results
from ..core.constants import COMPARTMENTS, FORECASTING_LEVELS, LOGIT_RATIOS
from ..data.features import LOG_ALPHA, get_forecast_columns
from ..data.preprocessing import reindex_data
from .base import BaseModel, SIRDModelMixin
from .forecasting.orchestrator import ForecastingOrchestrator
from .simulation import EpidemicSimulation, _warn_if_flat_median_incidence_forecast
from .var_forecasting import VARForecasting  # Keep for backward compat


# Import __version__ after full module initialization to avoid circular import
def _get_pkg_version() -> str:
    from dynasir import __version__

    return __version__


class Model(BaseModel, SIRDModelMixin):
    """
    SIRD epidemiological model with multi-backend time series forecasting.

    This model implements the SIRD (Susceptible-Infected-Recovered-Deaths)
    compartmental model with time-varying rates. Supports multiple forecasting
    backends: VAR (default), Prophet, ARIMA, and LSTM (stub).

    **Data Modes (v0.9.0+):**

    The model operates in two modes (automatically inherited from DataContainer):

    - **Cumulative mode** (default):
      * Input: C (cumulative cases) - monotonically increasing
      * Derived: I = dC (incident cases calculated from differences)
      * Use for: COVID-19, flu pandemics, ongoing epidemics
      * Data example: [100, 150, 200] total cases

    - **Incidence mode** (NEW in v0.9.0):
      * Input: I (incident cases per period) - can vary up/down
      * Derived: C = cumsum(I) (cumulative generated automatically)
      * Use for: Measles, polio, diseases with elimination cycles
      * Data example: [100, 50, 120] new cases per period

    **Forecasting Backends:**

    The forecasting backend is selected via the `forecaster` parameter:
    - 'var' (default): Vector Autoregression - fast, reliable
    - 'prophet': Facebook Prophet - handles seasonality, holidays
    - 'arima': Auto-ARIMA - automatic order selection
    - Backend-specific configuration via `forecaster_kwargs`

    Attributes:
        mode (str): Data mode inherited from DataContainer ('cumulative' or 'incidence')
        forecaster_name (str): Active forecasting backend
        data (pd.DataFrame): Processed epidemiological data
        forecasting_box (Box): Forecasted rates with confidence intervals
        simulation (Box): Monte Carlo simulation scenarios
        results (Box): Final aggregated compartment predictions

    Examples:
        **COVID-19 with default VAR backend:**

        >>> data = pd.DataFrame({'C': [100, 150, 200], 'D': [1, 2, 3], 'N': [1e6]*3})
        >>> container = DataContainer(data)  # mode='cumulative' by default
        >>> model = Model(container, start="2020-03-01", stop="2020-12-31")
        >>> model.create_model()
        >>> model.fit_model(max_lag=10)
        >>> model.forecast(steps=30)
        >>> model.run_simulations()
        >>> model.generate_result()

        **Measles with incidence mode:**

        >>> data = pd.DataFrame({'I': [220, 55, 667, 164], 'D': [1, 1, 3, 4], 'N': [120e6]*4})
        >>> container = DataContainer(data, mode='incidence')
        >>> model = Model(container)
        >>> print(f"Mode: {model.mode}")  # → 'incidence'
        >>> model.create_model()
        >>> model.fit_model(max_lag=3)
        >>> model.forecast(steps=5)
        >>> model.run_simulations(n_jobs=1)
        >>> model.generate_result()

        **Prophet backend with seasonality:**

        >>> model = Model(
        ...     container,
        ...     forecaster="prophet",
        ...     yearly_seasonality=True,
        ...     changepoint_prior_scale=0.1
        ... )
        >>> model.create_model()
        >>> model.fit_model()
        >>> model.forecast(steps=30)

    See Also:
        - DataContainer: Data preprocessing and mode selection
        - examples/notebooks/07_incidence_mode_measles.ipynb: Incidence mode tutorial
        - examples/notebooks/05_multi_backend_comparison.ipynb: Backend comparison
        - docs/USER_GUIDE.md: Comprehensive usage guide
    """

    def __init__(
        self,
        data_container,
        start: Optional[str] = None,
        stop: Optional[str] = None,
        days_to_forecast: Optional[int] = None,
        forecaster: str = "var",
        importation_rate: float = 0.0,
        steps_to_forecast: Optional[int] = None,
        **forecaster_kwargs,
    ):
        """
        Initialize the SIRD Model.

        The model's data mode (cumulative vs incidence) is **automatically inherited**
        from the DataContainer. The mode affects data interpretation but not the
        underlying SIRD equations or forecasting approach.

        Args:
            data_container: DataContainer instance with preprocessed data.
                          The model inherits the mode ('cumulative' or 'incidence')
                          from this container.
            start: Start date for model training (YYYY-MM-DD format).
                  If None, uses first available date in data.
            stop: Stop date for model training (YYYY-MM-DD format).
                 If None, uses last available date in data.
            days_to_forecast: Backward-compatible alias for the forecast period
                              count. Prefer steps_to_forecast.
            steps_to_forecast: Number of data periods to forecast. Preferred
                               frequency-independent alternative to days_to_forecast.
            forecaster: Forecasting backend to use. Options:
                - 'var' (default): Vector Autoregression (statsmodels VAR)
                  Fast, reliable, no external dependencies
                - 'prophet': Facebook Prophet
                  Handles seasonality, holidays (requires fbprophet)
                - 'arima': Auto-ARIMA (pmdarima)
                  Automatic order selection (requires pmdarima)
                - 'lstm': LSTM neural network
                  NOT YET IMPLEMENTED (stub only)
            importation_rate: External force of infection (epsilon).
                            Represents sporadic cases arriving from outside.
                            Useful for eliminated diseases (R0 < 1).
            **forecaster_kwargs: Backend-specific configuration parameters.
                VAR: max_lag (int), ic (str: 'aic'/'bic'/'hqic')
                Prophet: yearly_seasonality (bool), weekly_seasonality (bool),
                        changepoint_prior_scale (float)
                ARIMA: max_p (int), max_q (int), seasonal (bool)

        Raises:
            ValueError: If forecaster not in ['var', 'prophet', 'arima', 'lstm']
            ImportError: If forecaster backend not installed (Prophet, ARIMA)

        Examples:
            **Cumulative mode (COVID-19):**

            >>> covid_data = pd.DataFrame({'C': [100, 150, 200], ...})
            >>> container = DataContainer(covid_data)  # cumulative by default
            >>> model = Model(container, start="2020-03-01", stop="2020-12-31")

            **Incidence mode (Measles) with importation:**

            >>> measles_data = pd.DataFrame({'I': [220, 55, 667], ...})
            >>> container = DataContainer(measles_data, mode='incidence')
            >>> model = Model(container, importation_rate=0.5)

        Notes:
            - Mode propagates automatically: DataContainer.mode → Model.mode
            - Both modes use identical SIRD equations and forecasting methods
        """
        # Data and model attributes
        self.data: Optional[pd.DataFrame] = None
        self.data_container = data_container
        self.window = data_container.window
        self.mode = data_container.mode  # Inherit: 'cumulative' or 'incidence'
        self.start = start
        self.stop = stop

        # Model parameters
        if (
            days_to_forecast is not None
            and steps_to_forecast is not None
            and days_to_forecast != steps_to_forecast
        ):
            raise ValueError(
                "days_to_forecast and steps_to_forecast cannot specify different values"
            )
        self.steps_to_forecast = (
            steps_to_forecast if steps_to_forecast is not None else days_to_forecast
        )
        self.importation_rate = importation_rate

        # Forecasting configuration
        self.forecaster_name = forecaster
        self.forecaster_kwargs = forecaster_kwargs

        # Rates use forward differences, so features built on the full series
        # would give the row at `stop` the next period's data. Rebuild the
        # features from the raw data up to `stop` (#164).
        training_container = (
            data_container.up_to(stop)
            if hasattr(data_container, "up_to")
            else data_container
        )
        self.training_container = training_container

        # Keep every non-daily frequency on its own grid. Reindexing weekly
        # or quarterly data to daily repeats each count on many rows.
        native_frequencies = ("B", "W", "ME", "QE", "YE")
        if (
            hasattr(data_container, "frequency")
            and data_container.frequency in native_frequencies
        ):
            freq_to_use = data_container.frequency
            logging.debug(f"Using frequency-aware reindexing: {freq_to_use}")
            self.data = reindex_data(
                training_container.data,
                start,
                stop,
                freq=freq_to_use,
                warn_on_mismatch=False,
                fill=self.mode != "incidence",
            )
        else:
            # Daily, or no frequency info: complete daily range
            self.data = reindex_data(
                training_container.data,
                start,
                stop,
                fill=self.mode != "incidence",
            )

        # Transformed rates to forecast: logit rates, or for period-cohort
        # incidence data log alpha and logit gamma (beta = 1 - gamma)
        available_logit_ratios = get_forecast_columns(self.data.columns)
        self.cohort = LOG_ALPHA in available_logit_ratios
        # The rate in row t is the step from t to t+1; the last row's step
        # leaves the training window, so it is not used for fitting (#164, #165).
        # The first ceil(lag) rows are a recovery warm-up when the lag is
        # longer than one period: the lagged cumulative is still zero there
        # and the rates are not usable (#184).
        fit_rates = self._rates_for_fitting(
            self.data[available_logit_ratios], data_container, start
        )
        self.logit_ratios_values = fit_rates.values
        self.fit_index = fit_rates.index
        self.active_logit_ratios = available_logit_ratios  # Store for later use

        # Detect vaccination presence
        self.has_vaccination = "logit_delta" in available_logit_ratios

        # Log model type detection
        model_type = "SIRDV" if self.has_vaccination else "SIRD"
        logging.info(
            f"Model initialized with {len(available_logit_ratios)} forecast rates "
            f"({model_type} mode), forecaster='{forecaster}'"
        )

        # Forecasting component - use orchestrator for multi-backend support
        self.var_forecasting = ForecastingOrchestrator(
            self.data,
            self.logit_ratios_values,
            self.window,
            active_logit_ratios=available_logit_ratios,
            backend=forecaster,
            frequency=self.data.index.freqstr or data_container.frequency,
            rate_index=self.fit_index,
        )
        if self.steps_to_forecast is not None:
            self.var_forecasting.steps_to_forecast = self.steps_to_forecast

        # Results and simulation attributes (set during model execution)
        self.results: Optional[Box] = None
        self.simulation_engine: Optional[EpidemicSimulation] = None

    def _rates_for_fitting(self, rates: pd.DataFrame, data_container, start):
        """Drop the recovery warm-up and the last row, whose step is out of sample."""
        handler = getattr(data_container, "handler", None)
        lag = handler.get_recovery_lag() if handler is not None else 0
        warmup = math.ceil(lag) if lag and lag > 1 else 0
        raw_index = getattr(getattr(data_container, "raw_data", None), "index", None)
        if (
            warmup
            and raw_index is not None
            and len(raw_index) > warmup
            and isinstance(raw_index, pd.DatetimeIndex)
        ):
            warmup_end = raw_index[warmup - 1]
            kept = rates.loc[rates.index > warmup_end]
            if len(kept) < len(rates):
                start_ts = None if start is None else pd.Timestamp(start)
                if start_ts is None or start_ts <= warmup_end:
                    warnings.warn(
                        f"The first {warmup} period(s), through "
                        f"{pd.Timestamp(warmup_end).date()}, are the recovery-lag "
                        "warm-up. Their rates are excluded from fitting.",
                        UserWarning,
                        stacklevel=3,
                    )
            rates = kept
        return rates.iloc[:-1]

    @property
    def logit_ratios_model(self):
        """Get the underlying VAR model from the forecaster (for backward compatibility)."""
        return self.var_forecasting.logit_ratios_model

    @property
    def logit_ratios_model_fitted(self):
        """Get the fitted VAR model from the forecaster (for backward compatibility)."""
        return self.var_forecasting.logit_ratios_model_fitted

    def create_model(self, *args, **kwargs) -> None:
        """
        Create the forecasting model for logit-transformed rates.

        This prepares the internal forecaster (VAR, Prophet, ARIMA, etc.) on the
        logit-transformed α, β, γ (and optionally δ for SIRDV) rates using the
        configured smoothing window.

        Args:
            **kwargs: Backend-specific creation parameters (forwarded to backend)

        Examples:
            >>> from dynasir import Model, process_data_from_owid
            >>> raw = process_data_from_owid("OWID_WRL")
            >>> container = DataContainer(raw, window=7)
            >>>
            >>> # Default VAR backend
            >>> model = Model(container, start="2020-03-01", stop="2020-12-31")
            >>> model.create_model()
            >>>
            >>> # Prophet backend
            >>> model = Model(container, forecaster="prophet")
            >>> model.create_model()
        """
        self.var_forecasting.create_logit_ratios_model(*args, **kwargs)

    def create_logit_ratios_model(self, *args, **kwargs) -> None:
        """DEPRECATED: Use create_model() instead.

        This method is deprecated and will be removed in v0.8.0.
        Use create_model() for the same functionality.
        """
        warnings.warn(
            "create_logit_ratios_model() is deprecated and will be removed in v0.8.0. "
            "Use create_model() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.create_model(*args, **kwargs)

    def fit_model(self, *args, **kwargs) -> None:
        """
        Fit the forecasting model to the data.

        Merges initialization-time kwargs (from __init__) with call-time kwargs,
        with call-time kwargs taking precedence. This allows flexible configuration:

        - Set defaults at initialization: Model(..., max_lag=10)
        - Override at fit time: model.fit_model(max_lag=15)

        Frequency-aware defaults: If max_lag is not provided, uses frequency-specific
        defaults from DataContainer.handler (if available), otherwise uses settings:
        - Daily: max_lag=14 (rich time series)
        - Weekly: max_lag=10
        - Monthly: max_lag=6 (sparser data)
        - Annual: max_lag=3 (very sparse data)

        Args:
            **kwargs: Backend-specific parameters. Common options:
                For VAR:
                    max_lag: Maximum lag order for selection (default from frequency handler or settings)
                    ic: Information criterion ('aic', 'bic', etc.)
                For Prophet:
                    yearly_seasonality: Enable yearly patterns
                    weekly_seasonality: Enable weekly patterns
                    changepoint_prior_scale: Trend flexibility
                For ARIMA:
                    max_p: Maximum AR order
                    max_q: Maximum MA order
                    seasonal: Enable seasonal ARIMA

        Examples:
            >>> # VAR with defaults (frequency-aware)
            >>> model = Model(container)
            >>> model.create_model()
            >>> model.fit_model(max_lag=10)
            >>>
            >>> # VAR with init-time and fit-time config
            >>> model = Model(container, max_lag=5)
            >>> model.fit_model(ic="bic")  # Uses max_lag=5, ic="bic"
            >>>
            >>> # Prophet with seasonality
            >>> model = Model(container, forecaster="prophet")
            >>> model.fit_model(yearly_seasonality=True)
        """
        settings = get_settings()

        # Merge init-time kwargs with call-time kwargs (call-time takes precedence)
        merged_kwargs = {**self.forecaster_kwargs, **kwargs}

        # Apply backend-specific defaults from settings
        if self.forecaster_name == "var":
            # Use frequency-specific max_lag if available and not explicitly provided
            if "max_lag" not in merged_kwargs:
                # Check if container has frequency handler
                if hasattr(self.data_container, "handler"):
                    frequency_max_lag = (
                        self.data_container.handler.get_default_max_lag()
                    )
                    merged_kwargs.setdefault("max_lag", frequency_max_lag)
                    logging.info(
                        f"Using frequency-specific max_lag={frequency_max_lag} "
                        f"({self.data_container.handler.frequency_name})"
                    )
                else:
                    merged_kwargs.setdefault("max_lag", settings.VAR_MAX_LAG)

            # Adjust max_lag if it exceeds available data
            # VAR needs roughly max_lag * n_equations observations, so be very conservative
            available_obs = len(self.logit_ratios_values)
            # Rule: max_lag should leave at least 20 observations for stable covariance
            # With 3 rates: each lag costs ~3 df, so (available - 20) / 3 / 2 (additional safety)
            max_allowed_lag = max(1, (available_obs - 20) // 6)
            if merged_kwargs["max_lag"] > max_allowed_lag:
                old_lag = merged_kwargs["max_lag"]
                merged_kwargs["max_lag"] = max_allowed_lag
                logging.warning(
                    f"Reduced max_lag from {old_lag} to {max_allowed_lag} "
                    f"due to limited observations ({available_obs})"
                )

            merged_kwargs.setdefault("ic", settings.VAR_CRITERION)

        # Auto-create model if not yet created, passing through creation-specific kwargs
        # This handles cases where create_model() is not explicitly called
        if self.var_forecasting.forecaster.model is None:
            # For Prophet, separate creation-specific kwargs from fit kwargs
            if self.forecaster_name == "prophet":
                prophet_creation_params = {
                    "yearly_seasonality",
                    "weekly_seasonality",
                    "daily_seasonality",
                    "changepoint_prior_scale",
                    "seasonality_prior_scale",
                    "seasonality_mode",
                    "interval_width",
                    "growth",
                    "capacity",
                    "floor",
                    "uncertainty_samples",
                    "holidays_prior_scale",
                }
                creation_kwargs = {
                    k: v
                    for k, v in merged_kwargs.items()
                    if k in prophet_creation_params
                }
                fit_kwargs = {
                    k: v
                    for k, v in merged_kwargs.items()
                    if k not in prophet_creation_params
                }

                self.var_forecasting.create_logit_ratios_model(**creation_kwargs)
                merged_kwargs = fit_kwargs
            else:
                # For other backends, just create with no special kwargs
                self.var_forecasting.create_logit_ratios_model()

        self.var_forecasting.fit_logit_ratios_model(*args, **merged_kwargs)
        self.steps_to_forecast = self.var_forecasting.steps_to_forecast

    def fit_logit_ratios_model(self, *args, **kwargs) -> None:
        """DEPRECATED: Use fit_model() instead.

        This method is deprecated and will be removed in v0.8.0.
        Use fit_model() for the same functionality.
        """
        warnings.warn(
            "fit_logit_ratios_model() is deprecated and will be removed in v0.8.0. "
            "Use fit_model() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.fit_model(*args, **kwargs)

    def forecast(self, steps: Optional[int] = None, **kwargs) -> None:
        """
        Generate forecasts for the specified number of steps.

        After fitting the model, this generates forecasts for the logit-transformed
        rates and initializes the simulation engine for downstream simulations.

        Args:
            steps: Number of forecast periods. If None, uses the configured horizon.

        Examples:
            >>> model.create_model()
            >>> model.fit_model()
            >>> model.forecast(steps=30)
        """
        self.var_forecasting.forecast_logit_ratios(steps, **kwargs)
        self.steps_to_forecast = self.var_forecasting.steps_to_forecast
        self.forecasting_box = self.var_forecasting.forecasting_box
        self.forecasting_interval = self.var_forecasting.forecasting_interval
        self.forecast_index_stop = self.var_forecasting.forecast_index_stop
        self.forecast_index_start = self.var_forecasting.forecast_index_start

        # Initialize simulation engine after forecasting is done
        self.simulation_engine = EpidemicSimulation(
            self.data,
            self.forecasting_box,
            self.forecasting_interval,
            importation_rate=self.importation_rate,
        )

    def forecast_logit_ratios(self, steps: Optional[int] = None, **kwargs) -> None:
        """DEPRECATED: Use forecast() instead.

        This method is deprecated and will be removed in v0.8.0.
        Use forecast() for the same functionality.
        """
        warnings.warn(
            "forecast_logit_ratios() is deprecated and will be removed in v0.8.0. "
            "Use forecast() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.forecast(steps, **kwargs)

    def run_simulations(self, n_jobs: Optional[int] = None) -> None:
        """
        Run epidemic simulations based on forecasted rates.

        Runs sequentially by default. A process pool (n_jobs > 1) rarely pays off because each
        scenario takes milliseconds; on Windows and macOS it also requires an
        ``if __name__ == "__main__":`` guard in scripts. See ``EpidemicSimulation.run_simulations``.

        Args:
            n_jobs: Number of parallel jobs to use:
                - None: Use the configured default (sequential unless PARALLEL_SIMULATIONS=True)
                - 1: Sequential execution
                - >1: Parallel execution with specified number of workers

        Raises:
            RuntimeError: If forecast has not been generated yet
            ValueError: If n_jobs < 1

        Examples:
            >>> model.run_simulations()  # Configured default (sequential)
            >>> model.run_simulations(n_jobs=1)  # Force sequential
            >>> model.run_simulations(n_jobs=4)  # Use 4 parallel workers
        """
        if self.simulation_engine is None:
            raise RuntimeError("Forecast must be generated before simulating epidemic.")
        self.simulation_engine.run_simulations(n_jobs=n_jobs)
        self.simulation = self.simulation_engine.simulation
        self.results = self.simulation_engine.results

    def generate_result(self) -> None:
        """
        Generate results for all compartments.

        Aggregates simulation outputs into the final `results` structure
        (S, I, R, D, A, C) across confidence levels.

        Raises:
            RuntimeError: If simulation has not been executed yet

        Examples:
            >>> model.run_simulations()
            >>> model.generate_result()
            >>> assert model.results is not None
        """
        settings = get_settings()

        # Helper: compute a deterministic cache key from forecast + last history state
        def _hash_series_values(s: pd.Series) -> str:
            # Use raw bytes for stability
            h = hashlib.sha256()
            h.update(s.to_numpy().tobytes())
            h.update(str(s.dtype).encode("utf-8"))
            return h.hexdigest()

        def _compute_cache_key() -> str:
            last_hist = self.data.iloc[-1]

            # Build initial state with required compartments
            initial_state_keys = [
                "A",
                "C",
                "S",
                "I",
                "R",
                "D",
            ]
            if self.has_vaccination:
                initial_state_keys.append("V")

            initial_state = {
                k: float(last_hist[k])
                for k in initial_state_keys
                if k in last_hist.index
            }

            # Build rates hash with required rates
            rates_to_hash = ["alpha", "beta", "gamma"]
            if self.has_vaccination:
                rates_to_hash.append("delta")

            rates_hash = {
                ratio: {
                    level: _hash_series_values(
                        self.forecasting_box[ratio][level].loc[
                            self.forecasting_interval
                        ]
                    )
                    for level in FORECASTING_LEVELS
                }
                for ratio in rates_to_hash
                if ratio in self.forecasting_box
            }

            payload: Dict[str, Any] = {
                "pkg_version": _get_pkg_version(),
                "start": self.start,
                "stop": self.stop,
                "window": self.window,
                "steps_to_forecast": self.steps_to_forecast,
                "has_vaccination": self.has_vaccination,
                "mode": self.mode,
                "cohort": self.cohort,
                "importation_rate": self.importation_rate,
                "forecaster": self.forecaster_name,  # Include backend in cache key
                "forecaster_kwargs": self.forecaster_kwargs,  # Include config in cache key
                "interval": [d.strftime("%Y-%m-%d") for d in self.forecasting_interval],
                "initial_state": initial_state,
                "rates_hash": rates_hash,
            }
            blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
            return hashlib.sha256(blob).hexdigest()

        def _cache_dir_for_key(key: str) -> Path:
            base = Path(settings.CACHE_DIR)
            return base / key

        def _load_from_cache(dir_path: Path) -> Optional[Box]:
            meta_path = dir_path / "meta.json"
            if not meta_path.exists():
                return None
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                return None
            if (
                settings.CACHE_STRICT_VERSION
                and meta.get("pkg_version") != _get_pkg_version()
            ):
                return None

            box = Box()
            try:
                # Load all CSV files in the cache directory (dynamic compartments)
                for comp_file in dir_path.glob("*.csv"):
                    comp = comp_file.stem  # Get compartment name from filename
                    df = pd.read_csv(comp_file, index_col=0, parse_dates=True)
                    # Ensure index aligns to forecasting interval
                    df = df.loc[self.forecasting_interval]
                    box[comp] = df
                # Ensure we have at least the core SIRD compartments
                required_comps = ["C", "I", "R", "D"]
                if not all(comp in box for comp in required_comps):
                    return None
                return box
            except Exception:
                return None

        def _save_to_cache(dir_path: Path, results_box: Box) -> None:
            dir_path.mkdir(parents=True, exist_ok=True)
            meta = {
                "pkg_version": _get_pkg_version(),
                "start": str(self.start) if self.start else None,
                "stop": str(self.stop) if self.stop else None,
                "window": int(self.window) if self.window is not None else None,
                "steps_to_forecast": (
                    int(self.steps_to_forecast)
                    if self.steps_to_forecast is not None
                    else None
                ),
            }
            (dir_path / "meta.json").write_text(
                json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8"
            )
            # Only save compartments that exist in results
            for comp in results_box.keys():
                results_box[comp].to_csv(dir_path / f"{comp}.csv")

        # Attempt cache if enabled
        cache_used = False
        if settings.RESULT_CACHING_ENABLED:
            try:
                key = _compute_cache_key()
                cdir = _cache_dir_for_key(key)
                cached = _load_from_cache(cdir)
                if cached is not None:
                    logging.info("Loaded results from cache: %s", cdir)
                    self.results = cached
                    cache_used = True
                else:
                    logging.debug("No cache hit for key: %s", key)
            except Exception as e:
                logging.debug("Result cache check failed: %s", e)

        if not cache_used:
            if self.simulation_engine is None:
                raise RuntimeError(
                    "Forecast and simulation must be generated before generating results."
                )
            self.simulation_engine.generate_result()
            self.results = self.simulation_engine.results

            # Save to cache if enabled
            if settings.RESULT_CACHING_ENABLED:
                try:
                    key = _compute_cache_key()
                    cdir = _cache_dir_for_key(key)
                    _save_to_cache(cdir, self.results)
                    logging.info("Saved results to cache: %s", cdir)
                except Exception as e:
                    logging.error("Result cache save failed: %s", e, exc_info=True)
        elif self.results is not None:
            _warn_if_flat_median_incidence_forecast(self.data, self.results)

    def calculate_R0(self) -> pd.Series:
        """Calculate basic reproduction number R₀(t) = α(t) / (β(t) + γ(t)).

        The basic reproduction number R₀ represents the average number of secondary
        infections caused by a single infected individual in a completely susceptible
        population. It is a critical epidemiological metric for understanding epidemic
        dynamics:
        - R₀ > 1: Epidemic grows (each infected person infects more than one other)
        - R₀ = 1: Critical threshold (epidemic remains stable)
        - R₀ < 1: Epidemic declines (insufficient transmission to sustain spread)

        Returns:
            pd.Series: Time series of R₀ values indexed by date

        Raises:
            ValueError: If required rate columns are not present in data

        Examples:
            >>> model = Model(container, start="2020-03-01", stop="2020-12-31")
            >>> R0 = model.calculate_R0()
            >>> print(f"Mean R₀: {R0.mean():.2f}")
            Mean R₀: 1.85
            >>> print(f"R₀ > 1 for {(R0 > 1).sum()} days")
            R₀ > 1 for 245 days

        Notes:
            - Calculated from historical data rates (alpha, beta, gamma)
            - The value at date t describes the step from t to t+1, so the last
              training date (whose step leaves the training window) is excluded
            - For period-cohort incidence data (annual or monthly incidence),
              beta + gamma = 1 and R₀(t) = α(t), which is close to the growth
              ratio I(t+1)/I(t). With annual counts it is a ratio between
              successive years, not a per-generation reproduction number.
            - Use forecast_R0() for forecasted reproduction numbers
            - High variability in R₀ reflects changing interventions and behavior
        """
        required_cols = ["alpha", "beta", "gamma"]
        missing_cols = [col for col in required_cols if col not in self.data.columns]
        if missing_cols:
            raise ValueError(
                f"Missing required columns for R₀ calculation: {missing_cols}"
            )

        complete_steps = self.data.iloc[:-1]
        alpha = complete_steps["alpha"]
        beta = complete_steps["beta"]
        gamma = complete_steps["gamma"]

        R0 = alpha / (beta + gamma)
        R0.name = "R0"

        return R0

    def create_scenario(self, name: str, parameter_modifiers: Dict[str, float]) -> Box:
        """
        Run a simulation scenario with modified parameters.

        Allows exploring "what-if" scenarios by modifying forecasted rates or parameters.

        Args:
            name: Name of the scenario (for metadata)
            parameter_modifiers: Dictionary of parameter modifiers.
                - Multipliers for rates: 'beta': 0.9 (reduce beta by 10%)
                - Overrides for scalars: 'importation_rate': 0.05

        Returns:
            Box: Results object containing simulated compartments (same structure as `model.generate_result()`)

        Raises:
            RuntimeError: If forecast has not been generated yet.

        Examples:
            >>> # Scenario 1: Increase transmission by 20%
            >>> results_high = model.create_scenario("High Beta", {'beta': 1.2})
            >>>
            >>> # Scenario 2: Stop importation
            >>> results_closed = model.create_scenario("Closed Border", {'importation_rate': 0.0})
        """
        if self.forecasting_box is None:
            raise RuntimeError("Forecast must be generated before running scenarios.")

        logging.info(f"Running scenario '{name}' with modifiers: {parameter_modifiers}")

        # Create a COPY of the forecasting box to avoid mutating the baseline
        # Box matches the structure: rate -> level -> Series
        scenario_forecasting_box = Box()

        # Apply rate modifiers (alpha, beta, gamma, delta)
        # We iterate through the original box and apply multipliers if present
        for rate in self.forecasting_box.keys():
            scenario_forecasting_box[rate] = Box()
            multiplier = parameter_modifiers.get(rate, 1.0)

            for level in self.forecasting_box[rate].keys():
                original_series = self.forecasting_box[rate][level]
                # Apply multiplier
                modified_series = original_series * multiplier
                scenario_forecasting_box[rate][level] = modified_series

        # Determine importation rate for this scenario
        # Default to model's current rate, override if in modifiers
        scenario_importation = parameter_modifiers.get(
            "importation_rate", self.importation_rate
        )

        # Initialize a temporary simulation engine
        temp_simulation = EpidemicSimulation(
            self.data,
            scenario_forecasting_box,
            self.forecasting_interval,
            importation_rate=scenario_importation,
        )

        # Run simulation with the configured default n_jobs
        temp_simulation.run_simulations(n_jobs=None)
        temp_simulation.generate_result()

        return temp_simulation.results

    def forecast_R0(self) -> pd.DataFrame:
        """Calculate R₀(t) for forecasted parameters across all scenarios.

        Generates basic reproduction number forecasts by combining forecasted
        infection rates (α) with recovery (β) and mortality (γ) rates across
        all 27 scenario combinations (3 confidence levels × 3 rates).

        Returns:
            pd.DataFrame: R₀ values for each scenario combination.
                Columns are named as "alpha_level|beta_level|gamma_level"
                (e.g., "lower|point|upper"). Index is the forecasting interval.

        Raises:
            ValueError: If forecast has not been generated yet

        Examples:
            >>> model = Model(container, start="2020-03-01", stop="2020-12-31")
            >>> model.create_model()
            >>> model.fit_model()
            >>> model.forecast(steps=30)
            >>> R0_forecast = model.forecast_R0()
            >>> print(R0_forecast.shape)
            (30, 27)
            >>> # Get mean R₀ across all scenarios
            >>> mean_R0 = R0_forecast.mean(axis=1)
            >>> print(f"Average forecasted R₀: {mean_R0.mean():.2f}")
            Average forecasted R₀: 1.15

        Notes:
            - Requires forecast_logit_ratios() to be called first
            - Each column represents a different scenario combination
            - Use mean(axis=1) to get average R₀ across scenarios
            - Uncertainty in R₀ reflects uncertainty in underlying rates
            - For period-cohort incidence data beta = 1 - gamma, so R₀ equals
              alpha in every scenario; the beta and gamma levels in the column
              names do not change the value
        """
        if not hasattr(self, "forecasting_box") or self.forecasting_box is None:
            raise ValueError(
                "Forecast must be generated before calculating R₀. "
                "Call forecast() first."
            )

        R0_forecasts = {}
        cohort = getattr(self, "cohort", False)

        for alpha_level in FORECASTING_LEVELS:
            for beta_level in FORECASTING_LEVELS:
                for gamma_level in FORECASTING_LEVELS:
                    alpha = self.forecasting_box["alpha"][alpha_level]
                    scenario = f"{alpha_level}|{beta_level}|{gamma_level}"
                    if cohort:
                        # beta + gamma = 1 for each cohort; independent beta
                        # and gamma levels would not add up to one
                        R0_forecasts[scenario] = alpha.copy()
                        continue
                    beta = self.forecasting_box["beta"][beta_level]
                    gamma = self.forecasting_box["gamma"][gamma_level]
                    R0_forecasts[scenario] = alpha / (beta + gamma)

        result = pd.DataFrame(R0_forecasts, index=self.forecasting_interval)

        # Calculate summary statistics from scenario columns only
        scenario_data = result.copy()  # Preserve original scenario-only data
        result["mean"] = scenario_data.mean(axis=1)
        result["median"] = scenario_data.median(axis=1)
        result["std"] = scenario_data.std(axis=1)
        result["min"] = scenario_data.min(axis=1)
        result["max"] = scenario_data.max(axis=1)

        return result

    def aggregate_forecast(
        self,
        compartment_code: str,
        target_frequency: str = "Y",
        aggregate_func: str = "sum",
        methods: Optional[list] = None,
    ) -> pd.DataFrame:
        """
        Aggregate daily forecasts to target frequency (e.g., annual).

        This enables forecasting with daily internal model but reporting
        results at coarser frequency (e.g., annual cases from daily model).

        Args:
            compartment_code: Compartment to aggregate (C, I, R, D, V)
            target_frequency: Target frequency ('W', 'M', 'Y')
            aggregate_func: Aggregation function:
                - 'sum': Sum values (for incident cases, deaths)
                - 'mean': Average values (for prevalence)
                - 'last': Last value in period (for cumulative totals)
                - 'max': Maximum value (for peak detection)
                - 'min': Minimum value
            methods: Central tendency methods to include.
                     Defaults to ['mean', 'median']

        Returns:
            DataFrame with aggregated forecasts

        Raises:
            ValueError: If forecast not generated or invalid parameters

        Examples:
            >>> # Forecast 365 days, aggregate to annual
            >>> model.forecast(steps=365)
            >>> model.run_simulations()
            >>> model.generate_result()
            >>> annual = model.aggregate_forecast('C', target_frequency='Y', aggregate_func='last')

            >>> # Weekly aggregation for incident cases
            >>> model.forecast(steps=52*7)  # 1 year
            >>> model.run_simulations()
            >>> model.generate_result()
            >>> weekly = model.aggregate_forecast('C', target_frequency='W', aggregate_func='sum')
        """
        import numpy as np

        from dynasir.core.constants import CENTRAL_TENDENCY_METHODS

        if self.results is None:
            raise ValueError(
                "Must generate results before aggregating. Call generate_result() first."
            )

        if compartment_code not in self.results:
            raise ValueError(f"Compartment '{compartment_code}' not found in results")

        if methods is None:
            methods = ["mean", "median"]

        # Validate methods
        invalid_methods = [m for m in methods if m not in CENTRAL_TENDENCY_METHODS]
        if invalid_methods:
            raise ValueError(
                f"Invalid methods: {invalid_methods}. "
                f"Must be in {CENTRAL_TENDENCY_METHODS}"
            )

        # Get forecast results (may be daily or native frequency)
        daily_results = self.results[compartment_code]

        # Convert to modern frequency aliases to avoid FutureWarnings
        from dynasir.core.constants import MODERN_FREQUENCY_ALIASES

        modern_target_freq = MODERN_FREQUENCY_ALIASES.get(
            target_frequency, target_frequency
        )

        # Detect source frequency: prefer inferred index freq, fallback to container
        source_freq = pd.infer_freq(daily_results.index)
        if source_freq is None and hasattr(self, "data_container"):
            source_freq = getattr(self.data_container, "frequency", None)
        modern_source_freq = (
            MODERN_FREQUENCY_ALIASES.get(source_freq, source_freq)
            if source_freq
            else None
        )

        # Define aggregation function
        agg_funcs = {
            "sum": lambda x: x.sum(),
            "mean": lambda x: x.mean(),
            "last": lambda x: x.iloc[-1] if len(x) > 0 else np.nan,
            "max": lambda x: x.max(),
            "min": lambda x: x.min(),
        }

        if aggregate_func not in agg_funcs:
            raise ValueError(
                f"Invalid aggregate_func: {aggregate_func}. "
                f"Must be one of {list(agg_funcs.keys())}"
            )

        # If target frequency matches source, skip resampling
        if modern_source_freq and modern_source_freq == modern_target_freq:
            aggregated = daily_results.copy()
        else:
            resampler = daily_results.resample(modern_target_freq)
            aggregated = resampler.apply(agg_funcs[aggregate_func])

        # Only keep the central tendency columns requested
        all_cols = list(aggregated.columns)
        scenario_cols = [col for col in all_cols if "|" in col]  # Scenario columns

        # Keep scenarios + requested methods
        cols_to_keep = scenario_cols + methods
        cols_to_keep = [col for col in cols_to_keep if col in aggregated.columns]

        return aggregated[cols_to_keep]

    def visualize_results(
        self,
        compartment_code: str,
        testing_data: Optional[pd.DataFrame] = None,
        log_response: bool = True,
    ) -> None:
        """
        Visualize forecast results for a specific compartment.

        Args:
            compartment_code: Compartment to visualize (A, C, S, I, R, D)
            testing_data: Optional test data for comparison
            log_response: Whether to use logarithmic scale

        Examples:
            >>> # Visualize confirmed cases with test split overlay
            >>> model.visualize_results("C", testing_data=testing_data, log_response=True)
        """
        _visualize_results(
            results=self.results if self.results else self.simulation_engine.results,
            compartment_code=compartment_code,
            testing_data=testing_data,
            log_response=log_response,
        )

    def evaluate_forecast(
        self,
        testing_data: pd.DataFrame,
        compartment_codes: Tuple[str, ...] = ("C", "D", "I"),
        save_evaluation: bool = False,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate forecast performance against test data.

        Args:
            testing_data: DataFrame with actual values for comparison
            compartment_codes: Tuple of compartment codes to evaluate
            save_evaluation: Whether to save results to JSON file
            filename: Optional filename for saving (auto-generated if None)

        Returns:
            Dictionary with evaluation metrics for each compartment and method

        Examples:
            >>> testing = container.data.loc[model.forecasting_interval]
            >>> eval_dict = model.evaluate_forecast(testing)
            >>> # Save results to JSON
            >>> model.evaluate_forecast(testing, save_evaluation=True, filename="evaluation_output")
        """
        return _evaluate_forecast(
            results=self.results if self.results else self.simulation_engine.results,
            testing_data=testing_data,
            compartment_codes=compartment_codes,
            save_evaluation=save_evaluation,
            filename=filename,
        )
