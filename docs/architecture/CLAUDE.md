# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DynaSIR is a Python library for epidemiological modeling and forecasting that combines discrete SIRD/SIRDV (Susceptible-Infected-Recovered-Deaths-Vaccinated) mathematical models with VAR (Vector Autoregression) time series analysis. Unlike classical epidemiological models with constant parameters, this project models time-varying infection, recovery, mortality, and vaccination rates using logit-transformed rates.

**Key Innovation**: Rates (α, β, γ, δ) are logit-transformed before VAR modeling to ensure they stay within (0,1) bounds, then inverse-transformed back for epidemic simulations.

**Version**: 0.9.1 (in development towards v0.10.0) - Fractional recovery lag fix + comprehensive reporting tools

## What's New in v0.10.0 (Current Development)

**Fractional Recovery Lag Fix**:
- Annual frequency now uses 14/365 = 0.0384 years instead of 0 (rounded)
- Fixes LinAlgError when combining annual frequency + incidence mode
- Native annual + incidence workflows now production-ready
- 421/423 tests passing with 10 new fractional lag validation tests

**Comprehensive Reporting Tools** (NEW):
- `ModelReport` class for publication-ready analysis output
- One-line generation of Markdown reports, LaTeX tables, and high-DPI figures
- Automated summary statistics and forecast accuracy evaluation
- Multi-panel visualization with professional formatting
- Model comparison utilities for side-by-side analysis

**Example Usage**:
```python
from dynasir.analysis import ModelReport

# Create comprehensive report from model results
report = ModelReport(model.results, testing_data)

# Export to various formats
report.export_markdown("analysis_report.md")
report.export_latex_table("summary_table.tex", "summary")
report.export_latex_table("metrics_table.tex", "metrics")

# Generate publication-quality figures
fig = report.plot_forecast_panel(dpi=600)  # For journal submission
fig.savefig("forecast_panel.png", dpi=600, bbox_inches='tight')
```

## What's New in v0.9.1

**Importation Modeling**:
- Added `importation_rate` support for eliminated diseases (measles, polio, rubella)
- Scenario analysis tools: `create_scenario()`, `compare_scenarios()`
- USA measles validation examples and data fetching utilities
- Full backward compatibility with v0.9.0

## What's New in v0.9.0

This release enables the library to handle diverse epidemiological data patterns beyond COVID-19:

**Native Multi-Frequency Support**:
- Data stays in native frequency (Daily, Business Day, Weekly, Monthly, Annual) - no artificial reindexing
- Pluggable `FrequencyHandler` architecture with 5 concrete implementations
- Frequency-aware VAR defaults: Annual (3 lags), Monthly (6), Weekly (8), Daily (14), Business (10)
- Business day calendars (252 trading days/year) with validated recovery lags
- Frequency-aware aggregation skips resampling when source and target match
- Adaptive seasonal pattern detection per frequency

**Incidence Mode (Measles Integration)**:
- Dual-mode data support: cumulative (COVID-19) vs incidence (measles, polio, rubella)
- Mode-aware feature engineering: `I` as input for incidence, `C` derived via cumsum
- Non-monotonic patterns, elimination periods (0 cases), sporadic reintroduction
- Mode propagates automatically: DataContainer → Model → Results
- System forecasts **rates**, not compartments - both modes converge to identical VAR modeling

**Key Use Cases**:

| Use Case | Frequency | Mode | Example |
|----------|-----------|------|---------|
| COVID-19 daily data | `"D"` | `"cumulative"` | Daily confirmed cases (monotonic) |
| Stock/trading analysis | `"B"` | `"cumulative"` | Business day data (252 days/year) |
| Weekly disease reports | `"W"` | `"cumulative"` or `"incidence"` | Weekly case counts |
| Monthly surveillance | `"ME"` | `"incidence"` | Monthly incident cases |
| Annual measles data | `"YE"` | `"incidence"` | Annual sporadic outbreaks |

**Migration from v0.8.0**:
```python
# Old: Annual data reindexed to daily (~13,500 artificial rows)
container = DataContainer(annual_data, window=1)

# New: Native annual processing (40 rows stay 40 rows)
container = DataContainer(annual_data, window=1, frequency="YE", mode="incidence")
```

## Development Workflow

### Git Worktree Setup

This project uses git worktrees for parallel development:

```bash
# List all worktrees
git worktree list

# Create new worktree for a branch
git worktree add ../dynasir.worktrees/feature-name feature-branch-name

# Remove worktree when done
git worktree remove ../dynasir.worktrees/feature-name
```

### Version Management

- Current version: 0.9.1 (defined in both `pyproject.toml` and `src/dynasir/__init__.py`)
- README.md references v0.10.0 features (fractional recovery lag fix)
- Main branch: `main`
- **IMPORTANT**: When bumping versions, update BOTH `pyproject.toml` and `src/dynasir/__init__.py` - they must stay in sync
- Version inconsistencies across docs indicate v0.10.0 release is imminent

### Development Commands

**Environment Setup**:
```bash
# Install package in editable mode with all dependencies
pip install -e .

# Install with development tools
pip install -e ".[dev,test]"

# Install with documentation tools
pip install -e ".[docs]"
```

**Testing**:
```bash
# Run all tests
pytest

# Run specific test types
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m "not slow"        # Skip slow tests

# Run specific test file
pytest tests/test_model.py

# Run specific test function
pytest tests/test_model.py::test_function_name

# Run with coverage
pytest --cov=src/dynasir --cov-report=html

# Run in parallel
pytest -n auto

# Debug on first failure
pytest -x --pdb
```

**Code Quality**:
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Run all pre-commit hooks
pre-commit run --all-files

# Install pre-commit hooks
pre-commit install
```

**Pre-commit Hooks** (configured in `.pre-commit-config.yaml`):
- Code formatting: `black` (line length 88)
- Import sorting: `isort` (black profile)
- Linting: `flake8`, `pylint`
- Type checking: `mypy`
- Security: `bandit`
- Documentation: `pydocstyle` (Google convention)
- Standard checks: trailing whitespace, EOF fixer, YAML/TOML/JSON validation

**Important**: Pre-commit hooks run automatically before each commit. If hooks fail, the commit will be rejected. Fix issues and retry.

## Architecture Overview

### Core Data Flow

```
Raw OWID Data → DataContainer → Feature Engineering → Model → Forecast → Simulation → Results
     ↓              ↓                  ↓                ↓          ↓          ↓
   CSV          Validation        SIRD Rates      VAR Model   Monte Carlo  Evaluation
              Smoothing         Logit Transform   Forecast    Scenarios    Visualization
           Frequency Handler   (mode-aware)     (freq-aware) (27 or 81)
```

### Module Structure

**`src/dynasir/core/`** - Core configuration and constants
- `config.py`: Settings management using pydantic-settings
- `constants.py`: RATIOS, LOGIT_RATIOS, COMPARTMENTS, FORECASTING_LEVELS, frequency mappings
- `exceptions.py`: Custom exceptions (NotDataFrameError, DataValidationError, DateRangeError)

**`src/dynasir/data/`** - Data pipeline
- `container.py`: DataContainer class - main entry point (mode-aware, frequency-aware)
- `preprocessing.py`: Rolling window smoothing, frequency detection
- `features.py`: SIRD compartment calculations, rate calculations, logit transforms (dual-mode)
- `validation.py`: Data validation (cumulative and incidence validators)
- `frequency_handlers.py`: Pluggable handlers (Daily, Business Day, Weekly, Monthly, Annual)

**`src/dynasir/models/`** - Modeling components
- `base.py`: BaseModel and SIRDModelMixin abstract classes
- `sird.py`: Model class - main API (mode-aware, frequency-aware)
- `var_forecasting.py`: VARForecasting - VAR time series modeling (frequency-aware defaults)
- `simulation.py`: EpidemicSimulation - Monte Carlo simulations (parallel/sequential)
- `forecasting/var.py`: Additional VAR utilities

**`src/dynasir/analysis/`** - Post-processing and visualization
- `evaluation.py`: Model evaluation metrics (MAE, MSE, RMSE, MAPE, SMAPE)
- `visualization.py`: Plotting functions for results
- `formatting.py`: Professional plot formatting utilities
- `seasonality.py`: Frequency-aware seasonal pattern detection (v0.9.0)
- `reporting.py`: Publication-ready report generation (v0.10.0)
  - ModelReport class for comprehensive analysis
  - Markdown/LaTeX export, high-DPI figures
  - Model comparison utilities

**`src/dynasir/utils/`** - Utilities
- `transformations.py`: Logit/inverse logit transforms, rate bound handling

### Key Classes and Their Roles

**DataContainer**: Entry point for all data processing
- Validates raw data format (cumulative or incidence mode)
- Detects frequency and selects appropriate handler
- Applies rolling window smoothing (frequency-aware defaults)
- Orchestrates feature engineering pipeline
- Stores processed data with all SIRD/SIRDV variables

**Model** (in sird.py): Main modeling interface
- Inherits from BaseModel and SIRDModelMixin
- Inherits mode and frequency from DataContainer
- Wraps VARForecasting and EpidemicSimulation
- API: create_model(), fit_model(), forecast(), run_simulations(), generate_result()
- Delegates to specialized components

**VARForecasting**: Time series modeling component
- Creates and fits VAR models on logit-transformed rates
- Frequency-aware max_lag selection
- Generates confidence intervals for rate forecasts
- Handles inverse logit transformation back to rate space

**EpidemicSimulation**: Monte Carlo simulation engine
- Takes rate forecasts with confidence intervals
- Generates scenarios: 27 for SIRD (3³), 81 for SIRDV (3⁴)
- Runs discrete SIRD/SIRDV simulations forward in time
- Computes central tendency measures (mean, median, gmean, hmean)
- Supports parallel execution (n_jobs parameter)

**FrequencyHandler** (v0.9.0): Frequency-specific configuration
- Base class with concrete implementations per frequency
- Defines: days_per_year, recovery_lag, default_max_lag, min_observations
- Registry pattern for handler lookup
- Validates frequency-specific assumptions

**SeasonalPatternDetector** (v0.9.0): Seasonal pattern detection
- Frequency-specific candidate periods
- Adaptive correlation thresholds
- ARIMA/Prophet model recommendations

## Mathematical Foundation

### SIRD Compartments

```python
S = Susceptible = N - I - R - D  # Population not yet infected
I = Infected = C - R - D          # Currently infected
R = Recovered = C.shift(14) - D  # Recovered (14-day lag assumption)
D = Deaths = cumulative deaths   # Deceased
C = Cases = cumulative cases     # Total confirmed cases
A = S + I                         # Active susceptible + infected
```

### SIRDV Compartments (v0.7.0+)

```python
V = Vaccinated = cumulative vaccinations  # Vaccinated population
S = Susceptible = N - I - R - D - V       # Updated to exclude V
I = Infected = C - R - D                  # Unchanged
R = Recovered = C.shift(14) - D           # Unchanged
D = Deaths = cumulative deaths            # Unchanged
C = Cases = cumulative cases              # Unchanged
A = S + I                                 # Active population

# Conservation law: N = S + I + R + D + V
```

### Time-Varying Rates

```python
# SIRD rates
α(t) = infection rate = (A * dC) / (I * S)
β(t) = recovery rate = dR / I
γ(t) = mortality rate = dD / I

# SIRDV adds vaccination rate
δ(t) = vaccination rate = dV / S
```

### Critical Constraints

- Rates must be in (0, 1) for logit transformation
- S(t) and I(t) must be > 0 for α calculation
- Forward fill (ffill) used for missing rate values
- `prepare_for_logit_function()` ensures rate bounds before logit transform

### Feature Engineering Order (CRITICAL)

Must follow this exact sequence in `features.py`:

1. Calculate R using recovery lag: `R = C.shift(recovery_lag) - D`
2. Calculate I: `I = C - R - D`
3. Calculate differences (dC, dI, dR, dD)
4. Calculate rates (α, β, γ) from differences
5. Apply `prepare_for_logit_function()` to bound rates to (ε, 1-ε)
6. Apply logit transform

**For SIRDV**: Add V calculations and δ rate before step 5.

### Dual-Mode Feature Engineering (v0.9.0)

**Cumulative Mode** (default - COVID-19):
- Input: C (cumulative cases)
- Derive: I = C - R - D
- Monotonic assumption: C always increases

**Incidence Mode** (measles, polio, rubella):
- Input: I (incident cases per period)
- Derive: C = cumsum(I)
- No monotonic assumption: I can vary (0 → 100 → 0 → 50)

**Key Insight**: After feature engineering, both modes produce identical rate calculations. The system forecasts rates, not compartments, so forecasting/simulation code is mode-independent.

## Common Development Patterns

### Publication-Ready Reporting Workflow (v0.10.0)

```python
from dynasir import DataContainer, Model
from dynasir.analysis import ModelReport

# 1. Create and fit model (standard workflow)
container = DataContainer(data, window=7, frequency="ME", mode="incidence")
model = Model(container, start="2010-01", stop="2020-12")
model.create_model()
model.fit_model(max_lag=6)
model.forecast(steps=12)
model.run_simulations(n_jobs=None)
model.generate_result()

# 2. Generate comprehensive report
testing_data = container.data.loc[model.forecasting_interval]
report = ModelReport(model.results, testing_data)

# 3. Export to multiple formats
report.export_markdown("results/monthly_forecast.md")
report.export_latex_table("tables/summary.tex", "summary")
report.export_latex_table("tables/metrics.tex", "metrics")

# 4. Create publication-quality figures
fig = report.plot_forecast_panel(compartments=["C", "I"], dpi=600)
fig.savefig("figures/forecast_panel.png", dpi=600, bbox_inches='tight')

# 5. Compare multiple models
from dynasir.analysis.reporting import create_comparison_report

comparison_df = create_comparison_report([
    (model1.results, testing_data1, "Annual VAR"),
    (model2.results, testing_data2, "Monthly VAR"),
])
print(comparison_df)  # Side-by-side metrics comparison
```

**Key Features**:
- **Markdown Export**: GitHub-ready documentation with formatted tables
- **LaTeX Export**: Academic manuscript-ready tables
- **High-DPI Figures**: 600 DPI for journal submission requirements
- **Multi-Panel Plots**: Automatic layout for 2-6 compartments
- **Model Comparison**: Side-by-side evaluation metrics



### Typical Analysis Workflow

```python
from dynasir import DataContainer, Model, process_data_from_owid

# 1. Load and prepare data
raw_data = process_data_from_owid(iso_code="OWID_WRL")  # Global data
container = DataContainer(raw_data, window=7)

# 2. Create and fit model
model = Model(container, start="2020-03-01", stop="2020-12-31")
model.create_model()
model.fit_model(max_lag=10, ic="aic")

# 3. Forecast and simulate
model.forecast(steps=30)
model.run_simulations(n_jobs=None)  # None = auto-detect CPUs
model.generate_result()

# 4. Evaluate and visualize
testing_data = container.data.loc[model.forecasting_interval]
model.visualize_results("C", testing_data, log_response=True)
evaluation = model.evaluate_forecast(testing_data)
```

### Annual Measles Surveillance Workflow (v0.9.0)

```python
from dynasir import DataContainer, Model
import pandas as pd

# Load annual incident cases (incidence mode)
measles_data = pd.DataFrame({
    "I": [220, 55, 667, 164, 81, 34, 12, 0, 0, 4, 18, 45, 103, 67, 89],
    "D": [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
    "N": [110000000] * 15,
}, index=pd.date_range("2010", periods=15, freq="YE"))

# Use native annual frequency + incidence mode
container = DataContainer(measles_data, window=1, frequency="YE", mode="incidence")

# Model inherits mode and frequency automatically
model = Model(container, start="2010", stop="2020")
model.create_model()
model.fit_model(max_lag=3)  # Auto-selected for annual frequency
model.forecast(steps=5)  # 5 YEARS (not days)
model.run_simulations(n_jobs=1)
model.generate_result()

# Results already in annual frequency
print(model.results.C)  # Annual case forecasts
```

### Working with Frequency Handlers

```python
from dynasir.data.frequency_handlers import FrequencyHandlerRegistry

# Automatic handler selection
registry = FrequencyHandlerRegistry()

# Annual handler
annual_handler = registry.get_handler("YE")
print(annual_handler.days_per_year)  # 365
print(annual_handler.recovery_lag)   # 0 (rounded from 14/365 years)
print(annual_handler.default_max_lag)  # 3 years

# Business day handler
bday_handler = registry.get_handler("B")
print(bday_handler.days_per_year)  # 252 (trading days)
print(bday_handler.recovery_lag)   # 10 business days
print(bday_handler.default_max_lag)  # 10 (conservative for VAR)
```

### Using Constants

Always import from `dynasir.core.constants`:

```python
from dynasir.core.constants import (
    RATIOS,                      # ["alpha", "beta", "gamma", "delta"]
    LOGIT_RATIOS,                # ["logit_alpha", "logit_beta", "logit_gamma", "logit_delta"]
    COMPARTMENTS,                # ["A", "C", "S", "I", "R", "D", "V"]
    COMPARTMENT_LABELS,          # {"A": "Active", "C": "Confirmed", ...}
    FORECASTING_LEVELS,          # ["lower", "point", "upper"]
    CENTRAL_TENDENCY_METHODS,    # ["mean", "median", "gmean", "hmean"]
    MODERN_FREQUENCY_ALIASES,    # {"D": "D", "W": "W", "M": "ME", "Y": "YE", "A": "YE", "B": "B"}
    RECOVERY_LAG_BY_FREQUENCY,   # {"D": 14, "W": 2, "M": 0.5, "Y": 0.038, "A": 0.038}
)
```

### Result Caching (v0.6.1+)

Enable file-based caching to avoid recomputation:

**Configuration (.env file)**:
```bash
RESULT_CACHING_ENABLED=True
CACHE_DIR=.epydemics_cache
CACHE_STRICT_VERSION=False  # True = invalidate cache on version change
```

**Usage**:
```python
from dynasir.core.config import get_settings
import os

# Enable caching via environment variable
os.environ["RESULT_CACHING_ENABLED"] = "True"

model.generate_result()  # First run: computes and caches
model.generate_result()  # Subsequent runs: loads from cache

# Clear cache manually if needed
from pathlib import Path
import shutil
cache_dir = Path(get_settings().CACHE_DIR)
if cache_dir.exists():
    shutil.rmtree(cache_dir)
```

**Cache invalidates automatically** when data or model parameters change.

### Parallel Simulations (v0.6.0+)

**Configuration (.env file)**:
```bash
PARALLEL_SIMULATIONS=True
N_SIMULATION_JOBS=4  # or None for auto-detection
```

**Usage**:
```python
# Auto-detect CPUs (recommended)
model.run_simulations(n_jobs=None)

# Specific number of workers
model.run_simulations(n_jobs=4)

# Force sequential execution (debugging)
model.run_simulations(n_jobs=1)
```

**When to use parallel**:
- Multiple CPU cores available
- Large datasets (>1000 data points)
- Production forecasting
- Simulation time >> 5 seconds

**When to use sequential**:
- Debugging (easier to trace)
- Running many models simultaneously
- Limited memory
- Small/quick simulations (<1 second)

### VAR Model API Pattern

**IMPORTANT**: statsmodels VAR uses attribute access for information criteria:

```python
from statsmodels.tsa.api import VAR

# Create and select order
var_model = VAR(data)
selector = var_model.select_order(maxlags=max_lag)

# CORRECT: Access information criteria as attributes
optimal_lag_aic = selector.aic
optimal_lag_bic = selector.bic
optimal_lag_hqic = selector.hqic

# INCORRECT: Do NOT pass ic as parameter
# selector = var_model.select_order(maxlags=max_lag, ic="aic")  # Will fail

# Fit with selected lag
fitted = var_model.fit(optimal_lag_aic)
```

### Seasonal Pattern Detection (v0.9.0)

```python
from dynasir.analysis.seasonality import SeasonalPatternDetector

detector = SeasonalPatternDetector()

# Daily data: checks for weekly, monthly, quarterly, annual patterns
daily_result = detector.detect_seasonal_patterns(daily_data, frequency="D")
# Returns: {'has_seasonality': True, 'periods': [7, 365], 'model_recommendation': 'ARIMA'}

# Annual data: no seasonal patterns (insufficient data)
annual_result = detector.detect_seasonal_patterns(annual_data, frequency="YE")
# Returns: {'has_seasonality': False, 'periods': [], 'model_recommendation': 'Simple VAR'}
```

## Known Limitations

### Annual Frequency + Incidence Mode + VAR (FIXED in v0.10.0)

**Previous Issue** (v0.9.0 and earlier): VAR model fitting failed when combining annual frequency with incidence mode.

**Root Cause**:
- Annual frequency used `recovery_lag = 0` (14 days / 365 days rounded to 0)
- In incidence mode, everyone infected in year t recovered in year t
- This made `beta = R/I = I/I = 1.0` (constant)
- All rates became constant → VAR could not fit (singular covariance matrix)

**Fix in v0.10.0**:
- Annual frequency now uses `recovery_lag = 14/365 = 0.0384` years (fractional lag)
- Recovery now happens 0.0384 years after infection
- Rates vary over time → VAR can fit successfully
- Annual + incidence mode is now production-ready

**Current Status**:
- ✅ DataContainer creation (all frequencies)
- ✅ Feature engineering (fractional lag support)
- ✅ Model creation and VAR fitting (annual + incidence works)
- ✅ Forecasting and simulation (fully functional)

**Usage** (v0.10.0+):
```python
# Annual + incidence mode now works!
container = DataContainer(data, mode='incidence', frequency='YE')
model = Model(container)
model.fit_model(max_lag=3)  # Success! Rates vary due to fractional lag
model.forecast(steps=5)
model.run_simulations()
```

**Validation**:
```python
# Verify rates vary over time
rate_variance = container.data[['alpha', 'beta', 'gamma']].var()
assert rate_variance.max() > 1e-10, "Rates should vary"
```

**Documentation**: See `docs/user-guide/known-limitations.md` for complete details and `RELEASE_NOTES_v0.10.0.md` for the fix.

---

## Best Practices

### Multi-Frequency Data

1. **Always specify frequency explicitly** to avoid auto-detection errors:
   ```python
   container = DataContainer(data, frequency="YE")
   ```

2. **Use modern pandas aliases** to avoid FutureWarnings:
   - Annual: `"YE"` (not `"Y"` or `"A"`)
   - Monthly: `"ME"` (not `"M"`)
   - Weekly: `"W"`
   - Daily: `"D"`
   - Business: `"B"`

3. **Match window size to frequency**:
   - Annual: `window=1` (no smoothing)
   - Monthly: `window=1-3`
   - Weekly: `window=1-4`
   - Daily: `window=7-14`
   - Business: `window=5-10`

4. **Use incidence mode for eliminated diseases** (measles, polio, rubella):
   ```python
   container = DataContainer(data, mode="incidence", frequency="YE")
   ```

5. **Trust frequency-aware defaults** - override only when domain knowledge suggests otherwise

### Code Style

**NO EMOJIS** - Never use emojis in:
- Code comments or docstrings
- Commit messages
- Documentation
- Any output

**Type Hints**:
- All functions must have type hints (enforced by mypy)
- Use `Optional[T]` for nullable types
- Use `Dict`, `List`, `Tuple` from typing for Python 3.9 compatibility

**Docstrings**:
- Use Google-style docstrings
- Required for all public classes and functions
- Include Args, Returns, Raises sections

**Formatting**:
- Line length: 88 characters (black default)
- Use black for code formatting
- Use isort with black profile for import sorting

## Common Pitfalls and Solutions

### Problem: "Cannot calculate alpha when S or I is zero"
**Cause**: Early in epidemic, S ≈ N or I = 0
**Solution**: Use `.loc[start:stop]` to select date range where I > 0

### Problem: "Rates outside (0, 1) bounds"
**Cause**: Data issues causing invalid rate calculations
**Solution**: Use `prepare_for_logit_function()` which clips to (ε, 1-ε)

### Problem: "NaN values in logit transform"
**Cause**: Zeros in rate data
**Solution**: Pipeline uses forward fill (ffill) to propagate last valid value

### Problem: "VAR model fails to fit"
**Cause**: Insufficient data or too many lags
**Solution**: Reduce `max_lag` parameter or increase training data range

### Problem: "Annual data creates thousands of artificial rows"
**Cause**: Using v0.8.0 or earlier with annual data
**Solution**: Upgrade to v0.9.0 and use native frequency: `frequency="YE"`

## Important Files to Review

**Data Processing**:
- `src/dynasir/data/features.py` - Feature engineering (cumulative and incidence modes)
- `src/dynasir/data/validation.py` - Data validation (dual-mode support)
- `src/dynasir/data/frequency_handlers.py` - Frequency handler implementations
- `src/dynasir/data/preprocessing.py` - Frequency detection and smoothing

**Modeling**:
- `src/dynasir/models/sird.py` - Main model API (mode-aware, frequency-aware)
- `src/dynasir/models/var_forecasting.py` - VAR forecasting (frequency-aware defaults)
- `src/dynasir/models/simulation.py` - Simulation engine (parallel/sequential)

**Analysis**:
- `src/dynasir/analysis/seasonality.py` - Seasonal pattern detection
- `src/dynasir/analysis/evaluation.py` - Model evaluation metrics
- `src/dynasir/analysis/visualization.py` - Plotting functions
- `src/dynasir/analysis/reporting.py` - Publication-ready reports (v0.10.0)

**Configuration**:
- `pyproject.toml` - Project metadata, dependencies, tool configs
- `src/dynasir/core/config.py` - Runtime settings (caching, parallel simulations)
- `src/dynasir/core/constants.py` - Frequency aliases, recovery lags, compartments, rates
- `.env` - Environment configuration (optional)

**Examples**:
- `examples/global_forecasting.ipynb` - COVID-19 analysis example
- `examples/parallel_simulation_demo.ipynb` - Parallel simulation demonstrations
- `examples/reporting_example.py` - Publication-ready reporting demonstration (v0.10.0)
- `examples/README.md` - Guide to example notebooks

**Testing**:
- `tests/unit/data/test_incidence_mode.py` - Incidence mode unit tests (21 tests)
- `tests/integration/test_incidence_mode_workflow.py` - Incidence mode integration (6 tests)
- `tests/unit/analysis/test_seasonality.py` - Seasonal pattern detection (13 tests)
- `tests/unit/data/test_fractional_recovery_lag.py` - Fractional lag validation (10 tests, v0.10.0)
- `tests/models/test_result_caching.py` - Result caching tests
- `tests/test_parallel_simulations.py` - Parallel simulation tests
- `tests/conftest.py` - Shared fixtures (sample_data, sample_container)

## Data Sources

- Primary: Our World in Data (OWID) COVID-19 dataset
- Required columns (cumulative mode): `date`, `total_cases`, `total_deaths`, `population`
- Required columns (incidence mode): `date`, `incident_cases`, `deaths`, `population`
- ISO codes: `OWID_WRL` (global), country codes like `MEX`, `USA`
- Helper function: `process_data_from_owid()` in `dynasir.py`

## Testing Conventions

### Test Organization
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for full workflows
- `tests/conftest.py` - Shared fixtures

### Test Markers
```python
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.network  # Requires network access
```

### Common Fixtures
- `sample_owid_data`: OWID-format data (31 days, 2020-03-01 to 2020-03-31)
- `sample_processed_data`: Processed data with C, D, N columns
- `sample_data_container`: Pre-initialized DataContainer
- All fixtures use `np.random.seed(42)` for reproducibility

## Performance & Testing Summary

**v0.10.0 Test Coverage** (Current):
- 421/423 tests passing (2 skipped for optional dependencies)
- +10 new tests for fractional recovery lag validation
- Annual + incidence mode now fully functional
- Comprehensive reporting tools added
- Zero regressions - 100% backward compatible

**v0.9.0 Test Coverage**:
- 394 tests passing (32 skipped for optional dependencies)
- +27 new tests for incidence mode (21 unit + 6 integration)
- +13 new tests for seasonal pattern detection
- +12 new tests for business day support
- Zero regressions - 100% backward compatible

**Benchmarks**:
- Parallel simulations: 4-7x speedup on multi-core systems (for large datasets)
- Result caching: Instant load for repeated analyses
- Native frequency: No reindexing overhead (e.g., 40 annual rows stay 40 rows)
- Report generation: <1 second for Markdown/LaTeX export
