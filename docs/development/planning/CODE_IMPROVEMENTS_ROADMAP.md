# Code Improvements Roadmap

Based on analysis of the research notebook, this document outlines specific, actionable code improvements for the dynasir library.

## Priority 1: Critical Enhancements (Implement First)

### 1.1 Add Examples Directory with Research Notebook

**Rationale:** The research notebook demonstrates the library's capabilities and should be accessible to users.

**Implementation:**
```bash
# Directory structure
examples/
├── README.md
├── global_forecasting.ipynb  # Copy from K:\global\global.worktrees\ssrn\report.ipynb
├── regional_comparison.ipynb # New: Compare different countries
└── data/
    └── .gitkeep  # For caching OWID data
```

**Files to create:**
- `examples/README.md`: Overview of examples
- `examples/global_forecasting.ipynb`: Cleaned version of research notebook
- Update main `README.md` to reference examples

**Benefits:**
- Users can reproduce research results
- Provides comprehensive tutorial
- Validates library functionality
- Demonstrates best practices

### 1.2 Add R₀(t) Calculation to Model

**Current Gap:** R₀ calculation is shown in notebook but not accessible through Model API.

**Implementation:**
```python
# In src/dynasir/models/sird.py

class Model:
    # ... existing code ...

    def calculate_R0(self) -> pd.Series:
        """Calculate basic reproduction number R₀(t) = α(t) / (β(t) + γ(t)).

        Returns:
            pd.Series: Time series of R₀ values indexed by date

        Notes:
            R₀ > 1 indicates epidemic growth
            R₀ < 1 indicates epidemic decline
            R₀ = 1 is the critical threshold
        """
        alpha = self.data["alpha"]
        beta = self.data["beta"]
        gamma = self.data["gamma"]

        R0 = alpha / (beta + gamma)
        return R0

    def forecast_R0(self) -> pd.DataFrame:
        """Calculate R₀(t) for forecasted parameters across all scenarios.

        Returns:
            pd.DataFrame: R₀ values for each scenario combination
        """
        if not hasattr(self, 'forecasting_box'):
            raise ValueError("Must call forecast_logit_ratios() first")

        R0_forecasts = {}
        for alpha_level in FORECASTING_LEVELS:
            for beta_level in FORECASTING_LEVELS:
                for gamma_level in FORECASTING_LEVELS:
                    alpha = self.forecasting_box["alpha"][alpha_level]
                    beta = self.forecasting_box["beta"][beta_level]
                    gamma = self.forecasting_box["gamma"][gamma_level]

                    scenario = f"{alpha_level}|{beta_level}|{gamma_level}"
                    R0_forecasts[scenario] = alpha / (beta + gamma)

        return pd.DataFrame(R0_forecasts, index=self.forecasting_interval)
```

**Tests to add:**
```python
# tests/unit/models/test_sird.py

def test_calculate_R0(sample_model):
    """Test R₀ calculation from historical data."""
    R0 = sample_model.calculate_R0()

    assert isinstance(R0, pd.Series)
    assert len(R0) == len(sample_model.data)
    assert all(R0 >= 0)  # R₀ must be non-negative

def test_forecast_R0(fitted_model):
    """Test R₀ forecasting across scenarios."""
    R0_forecast = fitted_model.forecast_R0()

    assert isinstance(R0_forecast, pd.DataFrame)
    assert R0_forecast.shape[1] == 27  # 3x3x3 scenarios
    assert all(R0_forecast.min() >= 0)
```

**Benefits:**
- R₀ is critical epidemiological metric
- Enables threshold-based decision making
- Improves interpretability of forecasts

### 1.3 Enhanced Visualization Helper Functions

**Current Gap:** Notebook has superior time axis formatting not in library.

**Implementation:**
```python
# New file: src/dynasir/analysis/formatting.py

from datetime import timedelta
from typing import Literal
import matplotlib.dates as mdates
import matplotlib.pyplot as plt


TimeRange = Literal["auto", "short", "medium", "long"]


def format_time_axis(
    ax: plt.Axes,
    data_index: pd.DatetimeIndex,
    time_range: TimeRange = "auto",
    rotation: int = 45,
    labelsize: int = 10
) -> plt.Axes:
    """Apply consistent time axis formatting to matplotlib axes.

    Args:
        ax: Matplotlib axes to format
        data_index: DatetimeIndex from the data
        time_range: Time range category or 'auto' to detect
        rotation: Rotation angle for x-axis labels
        labelsize: Font size for x-axis labels

    Returns:
        Formatted axes object

    Examples:
        >>> fig, ax = plt.subplots()
        >>> ax.plot(data.index, data.values)
        >>> format_time_axis(ax, data.index, time_range="medium")
    """
    time_span = data_index.max() - data_index.min()

    # Auto-detect time range if requested
    if time_range == "auto":
        if time_span <= timedelta(days=60):
            time_range = "short"
        elif time_span <= timedelta(days=365):
            time_range = "medium"
        else:
            time_range = "long"

    # Apply formatting based on time range
    if time_range == "short":  # Less than 2 months
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        ax.xaxis.set_minor_locator(mdates.DayLocator(interval=1))
    elif time_range == "medium":  # 2 months to 1 year
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=1))
    else:  # More than 1 year
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))

    # Apply common formatting
    ax.tick_params(axis="x", rotation=rotation, labelsize=labelsize)
    ax.margins(x=0.01)
    ax.grid(True, alpha=0.3)

    return ax
```

**Update visualization.py to use it:**
```python
# In src/dynasir/analysis/visualization.py

from .formatting import format_time_axis

def visualize_results(
    model: "Model",
    compartment_code: str,
    testing_data: Optional[pd.DataFrame] = None,
    log_response: bool = True,
    format_axis: bool = True  # New parameter
) -> None:
    """Visualize forecasting results for a specific compartment.

    Args:
        model: Fitted Model instance
        compartment_code: Compartment to visualize ("C", "D", "I", etc.)
        testing_data: Optional actual data for comparison
        log_response: Use logarithmic scale for y-axis
        format_axis: Apply professional time axis formatting
    """
    # ... existing plotting code ...

    if format_axis:
        ax = plt.gca()
        format_time_axis(ax, compartment.index, time_range="auto")

    plt.show()
```

**Benefits:**
- Professional-looking plots out of the box
- Consistent formatting across all visualizations
- Reduces code duplication in notebooks

## Priority 2: Performance & Scalability

### 2.1 Parallel Simulation Execution

**Current Issue:** Sequential simulation of 27 scenarios is slow.

**Implementation:**
```python
# In src/dynasir/models/sird.py

from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Optional
import multiprocessing as mp


class Model:
    # ... existing code ...

    def run_simulations(self, n_jobs: Optional[int] = None) -> None:
        """Run epidemic simulations across all forecast scenarios.

        Args:
            n_jobs: Number of parallel jobs. None = CPU count, 1 = sequential
        """
        self.create_simulation_box()

        # Determine parallelization
        if n_jobs is None:
            n_jobs = mp.cpu_count()

        # Generate all scenario combinations
        scenarios = list(itertools.product(
            FORECASTING_LEVELS, FORECASTING_LEVELS, FORECASTING_LEVELS
        ))

        if n_jobs == 1:
            # Sequential execution (original behavior)
            for scenario in scenarios:
                alpha_lvl, beta_lvl, gamma_lvl = scenario
                simulation = self.simulate_for_given_levels(scenario)
                self.simulation[alpha_lvl][beta_lvl][gamma_lvl] = simulation
        else:
            # Parallel execution
            with ProcessPoolExecutor(max_workers=n_jobs) as executor:
                # Submit all jobs
                future_to_scenario = {
                    executor.submit(self._simulate_scenario, scenario): scenario
                    for scenario in scenarios
                }

                # Collect results
                for future in as_completed(future_to_scenario):
                    scenario = future_to_scenario[future]
                    alpha_lvl, beta_lvl, gamma_lvl = scenario
                    simulation = future.result()
                    self.simulation[alpha_lvl][beta_lvl][gamma_lvl] = simulation

    def _simulate_scenario(self, scenario: tuple) -> pd.DataFrame:
        """Helper for parallel simulation execution."""
        return self.simulate_for_given_levels(scenario)
```

**Configuration:**
```python
# In src/dynasir/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... existing settings ...

    # Parallelization settings
    PARALLEL_SIMULATIONS: bool = True
    N_SIMULATION_JOBS: Optional[int] = None  # None = auto-detect
```

**Benefits:**
- 27x speedup potential on multi-core systems
- Configurable for different hardware
- Backward compatible (n_jobs=1 for sequential)

### 2.2 Result Caching

**Current Issue:** Re-running identical forecasts repeats expensive computations.

**Implementation:**
```python
# New file: src/dynasir/utils/caching.py

import hashlib
import pickle
from pathlib import Path
from functools import wraps
from typing import Any, Callable


def cache_forecast(cache_dir: str = ".epydemics_cache") -> Callable:
    """Decorator to cache expensive forecast computations.

    Args:
        cache_dir: Directory to store cache files
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Create cache directory
            cache_path = Path(cache_dir)
            cache_path.mkdir(exist_ok=True)

            # Generate cache key from model state
            cache_key = self._generate_cache_key(func.__name__, args, kwargs)
            cache_file = cache_path / f"{cache_key}.pkl"

            # Check cache
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)

            # Compute result
            result = func(self, *args, **kwargs)

            # Save to cache
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)

            return result
        return wrapper
    return decorator


# In src/dynasir/models/sird.py

from dynasir.utils.caching import cache_forecast

class Model:
    # ... existing code ...

    @cache_forecast(cache_dir=".epydemics_cache")
    def forecast_logit_ratios(self, steps: Optional[int] = None, **kwargs):
        """Forecast logit-transformed rates (with caching)."""
        # ... existing implementation ...

    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate unique cache key from model state."""
        key_data = {
            'function': func_name,
            'data_hash': hashlib.md5(
                pd.util.hash_pandas_object(self.data).values
            ).hexdigest(),
            'start': str(self.start),
            'stop': str(self.stop),
            'args': args,
            'kwargs': kwargs
        }
        key_str = str(sorted(key_data.items()))
        return hashlib.md5(key_str.encode()).hexdigest()
```

**Benefits:**
- Avoid recomputing identical forecasts
- Faster iteration during development
- Configurable cache location

## Priority 3: Extended Functionality

### 3.1 Alternative Time Series Models

**Rationale:** Notebook suggests SARIMAX, Prophet as future work.

**Implementation:**
```python
# New file: src/dynasir/models/forecasting/sarimax.py

from statsmodels.tsa.statespace.sarimax import SARIMAX
from typing import Optional, Tuple
import pandas as pd


class SARIMAXForecaster:
    """SARIMAX-based forecasting for epidemic parameters."""

    def __init__(
        self,
        order: Tuple[int, int, int] = (1, 0, 1),
        seasonal_order: Tuple[int, int, int, int] = (1, 0, 1, 7)
    ):
        """Initialize SARIMAX forecaster.

        Args:
            order: (p, d, q) order for ARIMA
            seasonal_order: (P, D, Q, s) seasonal order
        """
        self.order = order
        self.seasonal_order = seasonal_order
        self.models = {}

    def fit(self, data: pd.DataFrame, endog_cols: list) -> None:
        """Fit SARIMAX models for each parameter.

        Args:
            data: Time series data
            endog_cols: Column names to forecast (e.g., logit_ratios)
        """
        for col in endog_cols:
            model = SARIMAX(
                data[col],
                order=self.order,
                seasonal_order=self.seasonal_order
            )
            self.models[col] = model.fit(disp=False)

    def forecast(self, steps: int) -> pd.DataFrame:
        """Generate forecasts.

        Args:
            steps: Number of steps to forecast

        Returns:
            DataFrame with forecasted values
        """
        forecasts = {}
        for col, fitted_model in self.models.items():
            forecast = fitted_model.forecast(steps=steps)
            forecasts[col] = forecast

        return pd.DataFrame(forecasts)
```

**Integration with Model:**
```python
# In src/dynasir/models/sird.py

class Model:
    def __init__(
        self,
        data_container,
        start=None,
        stop=None,
        days_to_forecast=None,
        forecaster: str = "var"  # New parameter
    ):
        # ... existing code ...
        self.forecaster_type = forecaster

    def create_logit_ratios_model(self, *args, **kwargs):
        """Create time series model for logit rates."""
        if self.forecaster_type == "var":
            self.logit_ratios_model = VAR(self.logit_ratios_values, *args, **kwargs)
        elif self.forecaster_type == "sarimax":
            from dynasir.models.forecasting.sarimax import SARIMAXForecaster
            self.logit_ratios_model = SARIMAXForecaster(*args, **kwargs)
        else:
            raise ValueError(f"Unknown forecaster: {self.forecaster_type}")
```

**Benefits:**
- Seasonal pattern detection
- Potentially better performance for certain datasets
- Research comparison capabilities

### 3.2 Regional Comparison Utilities

**Rationale:** Notebook suggests testing across different regions.

**Implementation:**
```python
# New file: src/dynasir/comparison.py

from typing import List, Dict
import pandas as pd
import matplotlib.pyplot as plt
from .data.container import DataContainer
from .models.sird import Model


class RegionalComparison:
    """Compare epidemic forecasts across multiple regions."""

    def __init__(self, iso_codes: List[str]):
        """Initialize regional comparison.

        Args:
            iso_codes: List of ISO country codes (e.g., ["MEX", "USA", "CAN"])
        """
        self.iso_codes = iso_codes
        self.containers = {}
        self.models = {}

    def load_data(self, **data_kwargs) -> None:
        """Load data for all regions."""
        from .dynasir import process_data_from_owid

        for iso_code in self.iso_codes:
            data = process_data_from_owid(iso_code=iso_code, **data_kwargs)
            self.containers[iso_code] = DataContainer(data)

    def fit_models(self, start: str, stop: str, **model_kwargs) -> None:
        """Fit models for all regions."""
        for iso_code, container in self.containers.items():
            model = Model(container, start=start, stop=stop, **model_kwargs)
            model.create_logit_ratios_model()
            model.fit_logit_ratios_model()
            self.models[iso_code] = model

    def forecast_all(self, steps: int = 30) -> None:
        """Generate forecasts for all regions."""
        for model in self.models.values():
            model.forecast_logit_ratios(steps=steps)
            model.run_simulations()
            model.generate_result()

    def compare_metrics(
        self,
        testing_data: Dict[str, pd.DataFrame],
        compartments: List[str] = ["C", "D", "I"]
    ) -> pd.DataFrame:
        """Compare forecast performance across regions.

        Args:
            testing_data: Dict mapping iso_code to testing DataFrame
            compartments: Compartments to evaluate

        Returns:
            DataFrame with performance metrics for each region
        """
        results = []

        for iso_code, model in self.models.items():
            eval_result = model.evaluate_forecast(
                testing_data[iso_code],
                compartment_codes=tuple(compartments)
            )

            for compartment, metrics in eval_result.items():
                for method, values in metrics.items():
                    results.append({
                        'region': iso_code,
                        'compartment': compartment,
                        'method': method,
                        **values
                    })

        return pd.DataFrame(results)

    def plot_comparison(
        self,
        compartment: str = "C",
        metric: str = "mae"
    ) -> None:
        """Visualize comparison across regions."""
        # Implementation for comparative visualization
        pass
```

**Usage example:**
```python
# In examples/regional_comparison.ipynb

from dynasir.comparison import RegionalComparison

# Compare North American countries
comparison = RegionalComparison(["MEX", "USA", "CAN"])
comparison.load_data()
comparison.fit_models(start="2020-03-01", stop="2020-12-31")
comparison.forecast_all(steps=30)

# Load testing data
testing_data = {iso: container.data.loc[comparison.models[iso].forecasting_interval]
                for iso, container in comparison.containers.items()}

# Compare performance
results = comparison.compare_metrics(testing_data)
print(results.groupby(['region', 'compartment'])['mae'].mean())
```

**Benefits:**
- Easy multi-region analysis
- Comparative performance evaluation
- Research validation across contexts

## Priority 4: Documentation & Examples

### 4.1 Comprehensive API Documentation

**Implementation:**
```bash
# Enhance docstrings with examples
# In every major function/class

def forecast_logit_ratios(self, steps: Optional[int] = None, **kwargs) -> None:
    """Forecast logit-transformed epidemiological rates.

    This method uses the fitted VAR model to generate forecasts for
    infection (α), recovery (β), and mortality (γ) rates over a specified
    time horizon. Forecasts include confidence intervals at lower, point,
    and upper levels.

    Args:
        steps: Number of days to forecast. If None, uses model default
            based on lag order (k_ar + window)
        **kwargs: Additional arguments passed to VAR.forecast_interval()

    Returns:
        None. Results stored in self.forecasting_box attribute

    Raises:
        ValueError: If model has not been fitted

    Examples:
        >>> model = Model(container, start="2020-03-01", stop="2020-12-31")
        >>> model.create_logit_ratios_model()
        >>> model.fit_logit_ratios_model()
        >>> model.forecast_logit_ratios(steps=30)
        >>> print(model.forecasting_interval)
        DatetimeIndex(['2021-01-01', '2021-01-02', ..., '2021-01-30'])

    Notes:
        - Forecasts are in logit space; use self.forecasting_box["alpha"]
          to access transformed rates
        - Uncertainty grows with forecast horizon
        - See forecast_R0() for reproduction number forecasts
    """
    # ... implementation ...
```

### 4.2 Tutorial Notebooks

**Create:**
1. `examples/01_quickstart.ipynb` - 10-minute introduction
2. `examples/02_global_forecasting.ipynb` - Research notebook
3. `examples/03_regional_comparison.ipynb` - Multi-region analysis
4. `examples/04_custom_models.ipynb` - Using alternative forecasters
5. `examples/05_visualization_guide.ipynb` - Advanced plotting

## Implementation Timeline

### Week 1: Foundation
- [ ] Add R₀ calculation methods
- [ ] Create examples directory
- [ ] Copy and clean research notebook

### Week 2: Performance
- [ ] Implement parallel simulations
- [ ] Add result caching
- [ ] Benchmark improvements

### Week 3: Extensions
- [ ] Implement SARIMAX forecaster
- [ ] Add regional comparison utilities
- [ ] Create comparison notebook

### Week 4: Polish
- [ ] Enhance all docstrings with examples
- [ ] Create tutorial notebooks
- [ ] Update README with new features

## Testing Strategy

For each new feature:
1. Unit tests in `tests/unit/`
2. Integration tests in `tests/integration/`
3. Example notebook validating functionality
4. Documentation in docstrings

## Backward Compatibility

All improvements maintain backward compatibility:
- New parameters have sensible defaults
- Existing API unchanged
- Deprecation warnings for any future removals

## Success Metrics

- [ ] All notebook functionality accessible via library API
- [ ] 10x speedup in simulation execution (parallel)
- [ ] 100% test coverage for new code
- [ ] Tutorial notebooks running without errors
- [ ] Documentation build successful
- [ ] PyPI package updated to v0.7.0
