import logging
import warnings

import pandas as pd

from dynasir.core.config import get_settings

from .features import feature_engineering
from .frequency_handlers import (
    FrequencyHandler,
    detect_frequency_from_index,
    get_frequency_handler,
)
from .preprocessing import _get_effective_window, preprocess_data
from .validation import validate_data


class DataContainer:
    """
    Container for epidemiological data with preprocessing and feature engineering.

    The DataContainer class handles the transformation of raw epidemiological data
    into a format suitable for SIRD (Susceptible-Infected-Recovered-Deaths) modeling.
    It performs data validation, preprocessing with rolling window smoothing,
    and comprehensive feature engineering to create all necessary epidemiological
    variables and rates.

    **New in v0.10.0**: Supports native multi-frequency processing (daily, weekly,
    monthly, annual) without forced reindexing to daily. Each frequency has its own
    recovery lag and max lag defaults.

    **New in v0.9.0**: Supports both cumulative and incidence mode for different
    data reporting patterns.

    Attributes:
        raw_data: Original input DataFrame
        window: Rolling window size for smoothing operations
        mode: Data interpretation mode ('cumulative' or 'incidence')
        frequency: Data frequency ('D', 'W', 'ME', 'YE') - auto-detected if None
        handler: FrequencyHandler instance managing frequency-specific logic
        data: Processed DataFrame with full feature engineering

    Examples:
        >>> # COVID-19 style: cumulative cases, daily frequency (default)
        >>> data = pd.DataFrame({'C': [100, 150, 200], 'D': [1, 2, 3], 'N': [1e6]*3})
        >>> container = DataContainer(data)  # frequency auto-detected as 'D'

        >>> # Measles style: incident cases per year, annual frequency
        >>> annual_index = pd.date_range('2010-12-31', periods=10, freq='YE')
        >>> data = pd.DataFrame({'I': [50, 30, 80], 'D': [1, 1, 2], 'N': [1e6]*10},
        ...                      index=annual_index)
        >>> container = DataContainer(data, mode='incidence')  # frequency auto-detected as 'YE'

        >>> # Monthly data with explicit frequency
        >>> container = DataContainer(monthly_data, frequency='ME', mode='cumulative')
    """

    def __init__(
        self,
        raw_data: pd.DataFrame,
        window: int = None,
        mode: str = "cumulative",
        frequency: str = None,
        incidence_offset: float = 0.0,
    ) -> None:
        """
        Initialize DataContainer with raw epidemiological data.

        Args:
            raw_data: DataFrame with required columns depending on mode:
                     - cumulative mode: ['C', 'D', 'N'] where:
                       * C = cumulative confirmed cases (monotonically increasing)
                       * D = cumulative deaths (monotonically increasing)
                       * N = population (constant or slowly varying)
                     - incidence mode: ['I', 'D', 'N'] where:
                       * I = incident cases per period (can vary up/down)
                       * D = cumulative deaths (monotonically increasing)
                       * N = population (constant or slowly varying)
            window: Rolling window size for smoothing (default: 7 from config).
                   Larger values (e.g., 14) provide smoother rates.
                   Smaller values (e.g., 3) preserve more variation.
                   NOTE: For annual/sparse data, window should be <= 3.
            mode: Data interpretation mode (default: 'cumulative')
                 - 'cumulative': Input C is cumulative, derives I = dC
                   Use for: COVID-19, flu, ongoing epidemics
                 - 'incidence': Input I is incident, derives C = cumsum(I)
                   Use for: Measles, polio, diseases with elimination cycles
            frequency: Data frequency code (default: auto-detect from index)
                 - 'D': Daily (365.25 observations/year)
                 - 'W': Weekly (52.14 observations/year)
                 - 'ME': Monthly (12 observations/year)
                 - 'YE': Annual (1 observation/year) - for measles
                 Auto-detection requires DatetimeIndex with regular spacing.
            incidence_offset: Constant added to case counts inside the rate
                 formulas in incidence mode (default 0). Periods with zero
                 cases make rates that divide by cases undefined; those rates
                 are carried forward from the previous period with a warning.
                 An offset such as 1 keeps them defined. Compartments (I, C,
                 S, R) are not changed.

        Raises:
            NotDataFrameError: If raw_data is not a pandas DataFrame
            DataValidationError: If required columns missing for specified mode
            ValueError: If mode not in ['cumulative', 'incidence']
            ValueError: If frequency not in ['D', 'W', 'ME', 'YE']

        Examples:
            >>> # Daily COVID-19 data (cumulative, auto-detect)
            >>> container = DataContainer(covid_data, window=7, mode='cumulative')

            >>> # Annual measles data (incidence, explicit frequency)
            >>> container = DataContainer(measles_data, window=3, mode='incidence',
            ...                           frequency='YE')

            >>> # Monthly surveillance data (cumulative)
            >>> container = DataContainer(monthly_data, window=2, frequency='ME')

            >>> # Access processed data
            >>> print(container.data.head())
            >>> print(f"Mode: {container.mode}, Frequency: {container.frequency}")

        See Also:
            - examples/notebooks/07_incidence_mode_measles.ipynb
            - docs/USER_GUIDE.md: Incidence Mode and Multi-frequency sections
        """

        settings = get_settings()

        # Validate mode parameter
        if mode not in ["cumulative", "incidence"]:
            raise ValueError(
                f"Invalid mode '{mode}'. Must be 'cumulative' or 'incidence'"
            )

        if incidence_offset < 0:
            raise ValueError("incidence_offset must be >= 0")

        self.raw_data = raw_data
        self._requested_window = window
        self.window = window if window is not None else settings.WINDOW_SIZE
        self.mode = mode
        self.incidence_offset = float(incidence_offset)

        # Validate input data early (mode-specific)
        validate_data(self.raw_data, mode=self.mode)

        # Detect or validate frequency
        if frequency is None:
            # Auto-detect from DatetimeIndex if available
            if isinstance(self.raw_data.index, pd.DatetimeIndex):
                self.frequency = detect_frequency_from_index(self.raw_data.index)
                logging.info(f"Auto-detected frequency: {self.frequency}")
            else:
                # Default to daily for non-DatetimeIndex
                self.frequency = "D"
                logging.info("DatetimeIndex not found; defaulting to daily frequency")
        else:
            # Validate provided frequency
            valid_frequencies = ["D", "B", "W", "ME", "YE"]
            if frequency not in valid_frequencies:
                raise ValueError(
                    f"Invalid frequency '{frequency}'. Must be one of {valid_frequencies}"
                )
            self.frequency = frequency

        # Get frequency-specific handler
        self.handler = get_frequency_handler(self.frequency)
        logging.info(
            f"Using {self.handler.__class__.__name__} for {self.frequency} frequency"
        )

        self._check_against_frequency()

        self.data = None

        # Run the processing pipeline
        self.process()
        self._warn_about_undefined_rates()

    def _check_against_frequency(self) -> None:
        """Warn when the data or settings do not suit the frequency (#169)."""
        try:
            self.handler.validate_data(self.raw_data)
        except ValueError as e:
            warnings.warn(
                f"{e}. Rates and forecasts may be unreliable.",
                UserWarning,
                stacklevel=3,
            )

        if self._requested_window is not None:
            effective = _get_effective_window(self._requested_window, self.frequency)
            if effective != self._requested_window:
                warnings.warn(
                    f"window={self._requested_window} is not used for "
                    f"{self.handler.frequency_name} data; the smoothing window "
                    f"is {effective}.",
                    UserWarning,
                    stacklevel=3,
                )

    def _warn_about_undefined_rates(self) -> None:
        """Warn when rates were undefined and carried forward (#167)."""
        n_filled = self.data.attrs.get("n_filled_rates", 0)
        zero_dates = []
        if self.mode == "incidence" and self.incidence_offset == 0:
            cases = self.raw_data["I"]
            zero_dates = [
                d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
                for d in cases.index[cases == 0]
            ]
        if zero_dates:
            shown = ", ".join(zero_dates[:10])
            more = f" and {len(zero_dates) - 10} more" if len(zero_dates) > 10 else ""
            warnings.warn(
                f"I is zero in {len(zero_dates)} period(s) ({shown}{more}). Rates "
                "that divide by cases are undefined next to these periods; "
                f"{n_filled} rate value(s) were carried forward from the previous "
                "period. Pass incidence_offset (for example 1) to keep them defined.",
                UserWarning,
                stacklevel=3,
            )
        elif n_filled:
            warnings.warn(
                f"{n_filled} rate value(s) were undefined (division by zero) and "
                "were carried forward from the previous period.",
                UserWarning,
                stacklevel=3,
            )

    def up_to(self, stop) -> "DataContainer":
        """
        Return a container rebuilt from the raw data up to ``stop``.

        Rates use forward differences (the rate in row t uses the value at
        t+1), so features computed on the full series would give the row at
        ``stop`` information from the next period. Rebuilding from truncated
        raw data keeps a model trained up to ``stop`` out of sample.

        Args:
            stop: Last date to keep (inclusive)

        Returns:
            A new DataContainer with the same settings, or ``self`` if no raw
            observation falls after ``stop`` or the raw index is not a
            DatetimeIndex.
        """
        if stop is None or not isinstance(self.raw_data.index, pd.DatetimeIndex):
            return self
        stop = pd.Timestamp(stop)
        if self.raw_data.index.max() <= stop:
            return self
        return self._rebuild(self.raw_data.loc[self.raw_data.index <= stop])

    def _rebuild(self, raw_data: pd.DataFrame) -> "DataContainer":
        # The full container has already warned about its data
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            return type(self)(
                raw_data,
                window=self._requested_window,
                mode=self.mode,
                frequency=self.frequency,
                incidence_offset=self.incidence_offset,
            )

    def process(self) -> None:
        """
        Process the raw data through the preprocessing and feature engineering pipeline.

        This method:

        1. Applies preprocessing (smoothing, reindexing)

        2. Applies feature engineering (SIRD compartments, rates, logit transforms)

        3. Updates the self.data attribute with the result

        The handler is used to determine frequency-specific parameters:
        - recovery_lag: SIRD-specific lag (e.g., 14 days = 1 year for annual data)
        - max_lag: Maximum lag for VAR model (e.g., 14 for daily, 3 for annual)
        """

        # Process data through the pipeline
        # Pass frequency to preprocessing for frequency-aware reindexing
        self.data = preprocess_data(
            self.raw_data, window=self.window, frequency=self.frequency
        )

        logging.debug(f"Preprocessed data columns: {self.data.columns}")
        logging.debug(f"Preprocessed data shape: {self.data.shape}")

        # Apply feature engineering (mode-aware and frequency-aware)
        self.data = feature_engineering(
            self.data,
            mode=self.mode,
            handler=self.handler,
            incidence_offset=self.incidence_offset,
        )

        logging.debug(f"Feature engineered data columns: {self.data.columns}")

        logging.debug(f"Data shape: {self.data.shape}")
        logging.debug(f"Frequency: {self.frequency}, Mode: {self.mode}")
