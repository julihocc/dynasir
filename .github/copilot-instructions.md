# GitHub Copilot Instructions for DynaSIR

**Version 0.10.0** - Fractional Recovery Lag Fix & Comprehensive Reporting

## Project Overview
DynaSIR is a Python epidemiological forecasting library combining discrete **SIRD/SIRDV models** with **VAR time series** on logit-transformed rates. It handles multiple disease patterns (pandemics like COVID-19, elimination cycles like measles) across **native frequencies** (daily, weekly, monthly, annual).

**Key Innovations**:
1. **Logit-Transformed Rates**: Time-varying infection (α), recovery (β), mortality (γ), vaccination (δ) rates stay (0,1) bounded
2. **Fractional Recovery Lag** (v0.10.0): Annual frequency now uses 14/365 years instead of rounding to 0, fixing singular matrix errors
3. **Native Multi-Frequency** (v0.9.0): Annual data stays annual (no artificial reindexing to 5,475 daily rows)
4. **Dual-Mode Architecture**: Supports cumulative (COVID-19 cumsum) and incidence (measles per-year) data
5. **Publication Tools** (v0.10.0): `ModelReport` class generates Markdown reports, LaTeX tables, and 300-600 DPI figures in one call

**Current Status**: Main branch stable (v0.9.1) | Branch `improve-report-tools` in development (reporting enhancements)
- 421/423 tests passing (99.5%), 25+ marked as `@pytest.mark.slow`
- Reporting API stable, all 7 example notebooks validated
- Annual + incidence workflows production-ready

## Architecture at a Glance

### Data Flow Pipeline
```
Raw Data → DataContainer → Feature Engineering → Model → VAR Forecast → Simulation → Results → ModelReport
(CSV/DF)   (Freq-aware)   (Fractional lag)    (Rates)  (Logit-VAR)   (27 scenarios) (SIRD) (Markdown/LaTeX)
           
Modes: CUMULATIVE (COVID) or INCIDENCE (measles)
Frequencies: Daily, Business, Weekly, Monthly, Annual (native, no reindexing)
```

### Critical Module Structure
- **`src/dynasir/core/`**: Constants (`RATIOS`, `COMPARTMENTS`), pydantic config, exceptions
- **`src/dynasir/data/container.py`**: `DataContainer` - mode/frequency detection, validation, smoothing
- **`src/dynasir/data/frequency_handlers.py`**: Frequency-specific handling (fractional lags, VAR defaults)
- **`src/dynasir/data/features.py`**: Feature engineering (SIRD compartments, rate calculation, logit transform)
- **`src/dynasir/models/sird.py`**: `Model` - main API, orchestrates forecasting/simulation
- **`src/dynasir/models/forecasting/var.py`**: `VARForecaster` - statsmodels VAR wrapper with constant detection
- **`src/dynasir/models/simulation.py`**: `EpidemicSimulation` - parallel/sequential (ProcessPoolExecutor)
- **`src/dynasir/analysis/reporting.py`**: `ModelReport` - publication-ready Markdown, LaTeX, figures
- **`src/dynasir/analysis/evaluation.py`**: Metrics (MAE, RMSE, MAPE, SMAPE) per compartment/method

## Mathematical Foundation

### SIRD Compartments (Order-Dependent Calculation)
```python
# MUST follow this sequence in feature_engineering():
R = C.shift(14) - D  # 1. Recovered (14-day lag assumption)
I = C - R - D        # 2. Infected (active cases)
S = N - I - R - D    # 3. Susceptible (remaining population)
A = S + I            # 4. Active (for rate calculations)
```

### Time-Varying Rates
```python
α(t) = (A * dC) / (I * S)  # Infection rate (requires I>0, S>0)
β(t) = dR / I              # Recovery rate
γ(t) = dD / I              # Mortality rate
# All rates → prepare_for_logit_function() → clip to (ε, 1-ε) → logit transform
```

**Critical Constraint**: Rates MUST be (0,1) for logit transform. Use `prepare_for_logit_function()` to clip rates, then `ffill()` for NaN propagation.

## Essential Development Patterns

### Standard Analysis Workflow (v0.10.0)
```python
from dynasir import DataContainer, Model
from dynasir.analysis import ModelReport

# 1. Prepare data (auto-detects mode & frequency)
data = pd.DataFrame({'I': [...], 'D': [...], 'N': [...]}, index=dates)
container = DataContainer(data, mode='incidence', frequency='YE', window=1)

# 2. Create and fit model
model = Model(container)
model.create_model()
model.fit_model(max_lag=3)  # VAR lag selection (auto-detects constant columns)
model.forecast(steps=5)
model.run_simulations(n_jobs=None)  # None=auto-CPU, 1=sequential
model.generate_result()

# 3. Generate publication-ready reports (NEW in v0.10.0)
report = ModelReport(model.results, testing_data, compartments=['I', 'D'])
report.export_markdown("analysis.md", include_figure=True)
report.export_latex_table("table1.tex", "summary")
fig = report.plot_forecast_panel(dpi=600, save_path="forecast.png")
```

**Key Mode Behaviors**:
- **Cumulative mode**: Input `C` (monotonic cases), auto-derives `I = diff(C)`
- **Incidence mode**: Input `I` (incident cases), auto-derives `C = cumsum(I)` - USE FOR MEASLES/POLIO
- **Frequency handling**: Annual stays annual, fractional lags handled automatically (14/365 for annual)

### Always Use Constants from `dynasir.core.constants`
```python
from dynasir.core.constants import (
    RATIOS,              # ["alpha", "beta", "gamma"]
    LOGIT_RATIOS,        # ["logit_alpha", "logit_beta", "logit_gamma"]
    COMPARTMENTS,        # ["A", "C", "S", "I", "R", "D"]
    FORECASTING_LEVELS,  # ["lower", "point", "upper"]
    CENTRAL_TENDENCY_METHODS  # ["mean", "median", "gmean", "hmean"]
)
```

### Configuration via Pydantic Settings
```python
from dynasir.core.config import get_settings

settings = get_settings()  # Cached singleton
# Configure via environment variables or .env:
# WINDOW_SIZE=7, RECOVERY_LAG=14, PARALLEL_SIMULATIONS=True
# N_SIMULATION_JOBS=4 (or None for CPU auto-detect)

# Result caching (v0.6.1+):
# RESULT_CACHING_ENABLED=True
# CACHE_DIR=.epydemics_cache
# CACHE_STRICT_VERSION=False  # True invalidates cache on version change

# Vaccination support (v0.6.1+):
# ENABLE_VACCINATION=True
# VACCINATION_COLUMN=people_vaccinated
```

## Critical Development Workflows

### Testing Commands
```bash
# Run all tests (uses pytest markers configured in pyproject.toml)
pytest

# Specific test types
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m "not slow"        # Skip slow tests (25+ marked)

# With coverage (configured in pyproject.toml)
pytest --cov=src/dynasir --cov-report=html

# Parallel execution (requires pytest-xdist)
pytest -n auto
```

### Code Quality Pipeline (Pre-commit)
```bash
# Format + lint (order matters)
black src/ tests/           # Line length: 88
isort src/ tests/           # Import sorting (black profile)
flake8 src/ tests/          # Linting (E203, W503 ignored)
mypy src/                   # Type checking (strict mode)

# Run all pre-commit hooks
pre-commit run --all-files

# Install hooks (runs on git commit)
pre-commit install
```

### VAR Model API Pattern (v0.10.0: Constant Detection)
```python
# VAR models automatically detect constant columns (e.g., alpha=1.0 in elimination phase)
# Use statsmodels VAR.select_order() then access .aic/.bic/.hqic attributes

selector = model.select_order(maxlags=max_lag)  # Returns LagOrderResults
optimal_lag = selector.aic  # Direct attribute access (not ic parameter)

# Constant column handling: automatically uses trend='n' when detected
# This prevents multicollinearity errors with elimination-phase data
fitted = model.fit(optimal_lag)  # Works even if alpha/gamma are constant
```

## Project-Specific Conventions

### Parallel Simulation Pattern (v0.6.0+)
```python
# Module-level function for pickling (multiprocessing requirement)
def _run_single_simulation(data, forecasting_box, interval, levels):
    temp_sim = EpidemicSimulation(data, forecasting_box, interval)
    return (levels, temp_sim.simulate_for_given_levels(levels))

# In EpidemicSimulation.run_simulations():
with ProcessPoolExecutor(max_workers=n_jobs) as executor:
    futures = {executor.submit(_run_single_simulation, ...): scenario}
    # Collect results via as_completed()
```

### Result Storage with python-box
```python
# Nested attribute access (not dict keys)
model.forecasting_box.alpha.lower   # Lower CI
model.forecasting_box.alpha.point   # Point forecast  
model.forecasting_box.alpha.upper   # Upper CI

# 27 simulation scenarios (3×3×3 confidence levels)
model.simulation["lower"]["point"]["upper"]  # DataFrame with SIRD compartments
```

### Type Hints (Enforced by mypy)
```python
from typing import Optional, Dict, List, Tuple

def forecast(self, steps: int, alpha: float = 0.05) -> None:
    """Type hints required for all public methods."""
    pass

# Exception: Python 3.9+ tuples in signatures OK
def process(data: pd.DataFrame) -> tuple[str, ...]:
    pass
```

## Common Pitfalls & Solutions

### 1. "Cannot calculate alpha when S or I is zero"
**Cause**: Early epidemic data where S ≈ N or I = 0  
**Solution**: Use `.loc[start:stop]` to select date range after epidemic starts (I > 0)

### 2. "NaN values in logit transform"
**Cause**: Zeros or out-of-bounds rates  
**Solution**: Pipeline auto-applies `prepare_for_logit_function()` + `ffill()` - ensure feature engineering order is correct

### 3. VAR model fails with "singular matrix" (FIXED in v0.10.0)
**Cause**: Constant columns (e.g., alpha=1.0 in elimination phase) with `trend='c'`  
**Solution**: Auto-detection in `VARForecaster` now uses `trend='n'` when constants detected - no manual fix needed

### 4. Annual + incidence mode: "LinAlgError: 1-th leading minor not positive definite"
**Cause**: Integer recovery lag (14 days → 0 years) made beta constant  
**Solution**: v0.10.0 uses fractional lag (14/365 = 0.0384 years) - beta now varies, VAR fits successfully

### 5. Slow simulation performance
**Solution**: Use `model.run_simulations(n_jobs=None)` for auto-detected parallel execution (4-7x speedup on multi-core)

## Style Requirements (Critical)

### NO EMOJIS Rule
Never use emojis in:
- Code comments/docstrings
- Commit messages
- Documentation
- Any output

Use clear, professional text only.

### Docstrings (Google Style)
```python
def forecast(self, steps: int) -> None:
    """
    Generate VAR forecasts for epidemic rates.

    Args:
        steps: Number of time steps to forecast

    Raises:
        RuntimeError: If model not fitted
        ValueError: If steps < 1

    Example:
        >>> model.forecast(steps=30)
    """
```

## Reporting Tools (v0.10.0)

### ModelReport API
```python
from dynasir.analysis import ModelReport

# Create comprehensive report from model results
report = ModelReport(
    results=model.results,
    testing_data=test_data,
    compartments=['I', 'D'],  # Optional: auto-detects if omitted
    model_name="Mexico Measles 2010-2024"
)

# Generate summary statistics
summary_df = report.generate_summary()  # Returns DataFrame with mean, median, std, CV, etc.

# Evaluate forecast accuracy against test data
eval_df = report.get_evaluation_summary()  # MAE, RMSE, MAPE, SMAPE per compartment/method

# Create multi-panel visualization
fig = report.plot_forecast_panel(figsize=(14, 8), dpi=300, save_path="forecast.png")

# Export to multiple formats
report.export_markdown("analysis.md", include_summary=True, include_figure=True)
report.export_latex_table("table1.tex", table_type="summary")  # or "evaluation"
```

### Model Comparison
```python
from dynasir.analysis import create_comparison_report

models = {
    "Model A": results_a,
    "Model B": results_b,
    "Model C": results_c,
}

fig = create_comparison_report(
    models=models,
    testing_data=test_data,
    compartment='I',
    save_path="comparison.png"
)
```

## Key Files for Common Tasks

**Reporting**: [src/dynasir/analysis/reporting.py](src/dynasir/analysis/reporting.py) (ModelReport class + create_comparison_report)  
**Modify Data Processing**: [src/dynasir/data/features.py](src/dynasir/data/features.py) (feature engineering logic)  
**Modify Modeling API**: [src/dynasir/models/sird.py](src/dynasir/models/sird.py) (main Model class)  
**Modify Simulation Logic**: [src/dynasir/models/simulation.py](src/dynasir/models/simulation.py) (parallel/sequential execution)  
**Add Configuration**: [src/dynasir/core/config.py](src/dynasir/core/config.py) (pydantic Settings)  
**View Examples**: [examples/notebooks/07_reporting_and_publication.ipynb](examples/notebooks/07_reporting_and_publication.ipynb) (comprehensive reporting demo)  
**Test Patterns**: [tests/conftest.py](tests/conftest.py) (fixtures: `sample_data`, `sample_container`)

## Development Environment Setup

### Initial Setup
```bash
# Clone and setup virtual environment
git clone https://github.com/julihocc/dynasir.git
cd dynasir
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev,test]"

# Install pre-commit hooks
pre-commit install
```

### Git Worktree Workflow (Advanced)
This project supports parallel development using git worktrees:

```bash
# List all worktrees
git worktree list

# Create new worktree for feature branch
git worktree add ../dynasir-feature-name feature-name

# Remove worktree when done
git worktree remove ../dynasir-feature-name
```

**Current workspace**: Branch `improve-report-tools` in worktree (reporting enhancements development)

### CI/CD Workflows
The project uses GitHub Actions for continuous integration:

- **`.github/workflows/ci.yml`**: Main CI pipeline
  - Tests on Python 3.9, 3.10, 3.11, 3.12
  - Runs pytest with coverage reporting
  - Uploads coverage to Codecov
  - Code quality checks (black, isort, flake8, mypy)

- **`.github/workflows/release.yml`**: Automated releases and PyPI publishing

Run quality checks locally before pushing:
```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Or manually:
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/
pytest -m "not slow"  # Fast tests only
```

## Example Notebooks

The [examples/notebooks/](examples/notebooks/) directory contains 7 comprehensive notebooks:

1. **01_sird_basic_workflow.ipynb**: Basic SIRD model workflow
2. **02_sirdv_vaccination_analysis.ipynb**: SIRDV model with vaccination
3. **03_global_covid19_forecasting.ipynb**: Multi-country COVID-19 analysis
4. **04_parallel_simulations.ipynb**: Performance comparison of parallel vs sequential
5. **05_multi_backend_comparison.ipynb**: Backend comparison (VAR, ARIMA, etc.)
6. **06_incidence_mode_measles.ipynb**: Measles elimination cycles with annual data
7. **07_reporting_and_publication.ipynb**: Publication-ready report generation (v0.10.0)

All notebooks are validated and maintained with real-world data examples.

## Integration Points

- **External Data**: OWID GitHub repo (auto-fetched by `process_data_from_owid()`)
- **Time Series**: statsmodels VAR (wrapped in `VARForecaster`)
- **Parallel Processing**: `concurrent.futures.ProcessPoolExecutor` (Python stdlib)
- **Config Management**: Environment variables via pydantic-settings (`.env` file support)

## Recent Major Changes (v0.10.0)

1. **✅ Fractional Recovery Lag Fix (v0.10.0 - COMPLETE)**:
   - Annual frequency now uses 14/365 = 0.0384 years instead of 0 (rounded)
   - Fixes LinAlgError when combining annual frequency + incidence mode
   - Automatic constant column detection in VAR models
   - Uses `trend='n'` when alpha/gamma are constant (elimination phase)
   - See [RELEASE_NOTES_v0.10.0.md](RELEASE_NOTES_v0.10.0.md) for details

2. **✅ Comprehensive Reporting Tools (v0.10.0)**:
   - `ModelReport` class for publication-ready analysis
   - One-line export to Markdown, LaTeX tables, and 300-600 DPI figures
   - Automated summary statistics and forecast accuracy evaluation
   - Model comparison utilities (`create_comparison_report()`)
   - See [examples/notebooks/07_reporting_and_publication.ipynb](examples/notebooks/07_reporting_and_publication.ipynb) for complete demo

3. **✅ Multi-Frequency Native Support (v0.9.0)**:
   - Annual data stays annual (no artificial reindexing to 5,475 daily rows)
   - Pluggable frequency handlers with 5 implementations
   - Frequency-aware VAR defaults: Annual (3), Monthly (6), Weekly (8), Daily (14)

4. **✅ Incidence Mode (v0.9.0)**:
   - Dual-mode support: cumulative (COVID-19) and incidence (measles/polio)
   - Mode propagates through DataContainer → Model → Results automatically
   - Handles elimination cycles and sporadic reintroduction

5. **✅ SIRDV Model Support (v0.6.1)**:
   - Automatic detection of vaccination column
   - Dynamic rate calculation including delta (vaccination rate)
   - Backward compatible with SIRD models

6. **✅ Parallel Simulations (v0.6.0)**:
   - Added `n_jobs` parameter to `run_simulations()` with auto-CPU detection
   - 4-7x speedup on multi-core systems using ProcessPoolExecutor

7. **✅ Test Infrastructure**:
   - Added `@pytest.mark.slow` to 25+ integration tests for faster CI/CD
   - 421/423 tests passing (99.5%), comprehensive coverage
