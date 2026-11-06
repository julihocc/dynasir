# DynaSIR User Guide

**Version**: 1.0.0
**Last Updated**: November 2026

## Table of Contents

1. [When to Use DynaSIR](#when-to-use-dynasir)
2. [When NOT to Use](#when-not-to-use)
3. [Data Preparation Guide](#data-preparation-guide)
4. [Working with Different Data Frequencies](#working-with-different-data-frequencies)
5. [Incidence Mode (v0.9.0+)](#incidence-mode-v090)
6. [Annual Surveillance Data](#annual-surveillance-data)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Additional Resources](#additional-resources)

---

## When to Use DynaSIR

DynaSIR is designed for **epidemiological forecasting** using discrete compartmental models (SIRD/SIRDV) combined with VAR time series analysis. It works best for:

### Ideal Use Cases

**1. COVID-19 and Similar Emerging Epidemics**
- **Data Type**: Daily cumulative confirmed cases and deaths
- **Pattern**: Ongoing epidemic with continuous growth
- **Frequency**: Daily or weekly observations
- **Example**: OWID COVID-19 data
```python
from dynasir import process_data_from_owid, DataContainer, Model

# Load daily COVID-19 data
data = process_data_from_owid(iso_code="USA")
container = DataContainer(data, window=7)

# Model and forecast
model = Model(container, start="2020-03-01", stop="2020-12-31")
model.create_model()
model.fit_model(max_lag=10)
model.forecast(steps=30)
model.run_simulations()
model.generate_result()
```

**2. Influenza and Seasonal Epidemics**
- **Data Type**: Weekly incident cases or cumulative
- **Pattern**: Seasonal outbreaks with clear cyclical patterns
- **Frequency**: Weekly observations
- **Note**: Weekly data works well natively in v0.8.0

**3. Vaccine-Preventable Diseases (with vaccination data)**
- **Data Type**: Cases, deaths, AND vaccination coverage
- **Model**: SIRDV (with V compartment)
- **Example**: Measles with vaccination campaigns
```python
# SIRDV with vaccination data
data = pd.DataFrame({
    'C': cumulative_cases,
    'D': cumulative_deaths,
    'V': people_vaccinated,  # Vaccination coverage
    'N': population
}, index=date_index)

container = DataContainer(data, window=7)
# SIRDV model automatically detected
```

---

## When NOT to Use

DynaSIR may not be suitable for:

### ❌ Very Sparse Data
- **Limitation**: < 20 time points
- **Reason**: Insufficient data for VAR model estimation
- **Alternative**: Consider simpler statistical models or SIR-only approaches

### ✅ Annual Data (v0.10.0+)
- **Status**: Supported, including incidence mode, with a fractional recovery lag
- **How**: Annual frequency uses 14/365 years (0.0384) instead of integer 0
- **Works with**: Both cumulative and incidence modes
- **Caution**: Technical support does not guarantee useful forecasts; short annual series can have flat medians and widening scenario ranges.

### ❌ Non-Infectious Diseases
- **Limitation**: Diseases without transmission dynamics
- **Reason**: SIRD compartmental model assumes susceptible→infected→recovered/dead flow
- **Examples**: Cancer, heart disease, genetic conditions

### ❌ Vector-Borne Diseases (without modification)
- **Limitation**: Diseases requiring vector compartments (mosquitoes, ticks)
- **Examples**: Malaria, dengue, Lyme disease
- **Note**: Would need custom compartmental model extensions

---

## Data Preparation Guide

### Required Data Format

DynaSIR expects a pandas DataFrame with:

```python
import pandas as pd

data = pd.DataFrame({
    'C': [100, 250, 450, ...],      # Cumulative confirmed cases (required)
    'D': [5, 12, 23, ...],           # Cumulative deaths (required)
    'N': [1000000, 1000000, ...],    # Population (required)
    'V': [0, 5000, 12000, ...]       # Vaccinated count (optional, for SIRDV)
}, index=pd.date_range('2020-01-01', periods=100, freq='D'))
```

### Cumulative vs Incidence Data

**Cumulative Data (Current Default)**
- Values MUST be monotonically increasing
- Represents total cases up to that date
- Example: Total COVID-19 cases = 100 → 250 → 450

```python
# If you have cumulative data (COVID-19 style)
container = DataContainer(cumulative_data, window=7)
```

**Incidence Data (v0.9.0+)**
- Values can fluctuate up and down
- Represents NEW cases in that period
- Example: Annual measles = 200 → 50 → 180

```python
# FUTURE API (v0.9.0) - NOT AVAILABLE in v0.8.0
container = DataContainer(incidence_data, mode='incidence', frequency='Y')
```

**Converting Incidence to Cumulative (v0.8.0 Workaround)**
```python
# If you have incidence data, convert to cumulative
data['C'] = data['incident_cases'].cumsum()
data['D'] = data['incident_deaths'].cumsum()

# Then use as normal
container = DataContainer(data, window=1)  # window=1 for pre-cumulated data
```

### Frequency Requirements

| Frequency | Code | Status | Notes |
|-----------|------|--------|-------|
| Daily | `D` | ✅ Native | Preferred, most tested |
| Weekly | `W` | ✅ Native | Works well, set `window=1` |
| Monthly | `M` | ✅ Native | Recovery lag = 14/30 months (0.47) |
| Annual | `Y` | ✅ Native | Recovery lag = 14/365 years (0.0384) - v0.10.0+ |

---

## Working with Different Data Frequencies

### Daily Data (Recommended)

```python
# COVID-19 daily data
data = process_data_from_owid(iso_code="USA")
container = DataContainer(data, window=7)  # 7-day smoothing
```

### Weekly Data

```python
# Weekly influenza surveillance
weekly_data = pd.DataFrame({
    'C': cumulative_cases,
    'D': cumulative_deaths,
    'N': population
}, index=pd.date_range('2020-01-01', periods=52, freq='W'))

container = DataContainer(weekly_data, window=1)  # No smoothing needed
```

### Monthly Data → Daily Forecast → Monthly Output

```python
# Load monthly data (will be reindexed to daily internally)
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message=".*FREQUENCY MISMATCH.*")
    container = DataContainer(monthly_data, window=1)

# Forecast in daily resolution
model = Model(container, start="2020-01", stop="2021-12")
model.create_model()
model.fit_model(max_lag=3)
model.forecast(steps=365)  # 1 year
model.run_simulations()
model.generate_result()

# Aggregate back to monthly
monthly_forecast = model.aggregate_forecast(
    "C", 
    target_frequency="M",
    aggregate_func="last",  # End-of-month value
    methods=["mean", "median"]
)
```

---

## Annual Surveillance Data

**v0.10.0+** supports annual frequency natively, including incidence mode, with a fractional recovery lag. This fixes a model-fitting limitation; it does not establish predictive skill. With only a few dozen annual observations, VAR forecasts may be unstable or uninformative.

### What Changed in v0.10.0

The recovery lag is fractional rather than rounded to zero:
- **Recovery lag**: Changed from integer 0 to float 0.0384 (14 days / 365 days)
- **Result**: Annual incidence VAR models can fit without the former constant-rate failure
- **Compatibility**: 100% backward compatible with existing code

### Recommended Workflow (v0.10.0+)

```python
import pandas as pd
import numpy as np
from dynasir import DataContainer, Model

# 1. Load annual measles data (incidence mode)
annual_data = pd.DataFrame({
    "I": [220, 55, 667, 164, 81, 34, 12, 0, 0, 4, ...],  # Incident cases per year
    "D": np.cumsum([5, 4, 3, 2, 1, ...]),                 # Cumulative deaths
    "N": [330000000] * 40,                                # Population
}, index=pd.date_range("1980", periods=40, freq="YE"))  # Year-end

# 2. Create container with incidence mode (annual data is not smoothed)
container = DataContainer(annual_data, mode='incidence', frequency='YE')

# 3. Create model and forecast - works natively with annual frequency!
model = Model(container, start="1990", stop="2015")
model.create_model()
model.fit_model(max_lag=3)  # Annual lags (3 years back)
model.forecast(steps=5)     # 5 years ahead
model.run_simulations(n_jobs=1)
model.generate_result()

# 4. Results are already in annual frequency - no aggregation needed!
print(model.results['I'])  # Annual incident cases forecast
print(model.calculate_R0())  # About I(t+1)/I(t): a year-to-year ratio
# Forecast values depend on the input data and model fit.
```

### Key Improvements in v0.10.0

**1. Fractional Recovery Lag**
```python
# Annual frequency: recovery_lag = 14/365 = 0.0384 years
# Monthly frequency: recovery_lag = 14/30 = 0.47 months
```

**2. Resolves the former annual-incidence fitting failure**
```python
# v0.9.x: Annual + incidence could produce constant rates and fail VAR fitting.
# v0.10.0+: Fractional recovery lag removes that specific failure mode.
# A successful fit does not imply an informative or accurate forecast.
```

**3. Native annual workflow**
```python
container = DataContainer(measles_data, mode='incidence', frequency='YE')
model = Model(container)
model.create_model()
model.fit_model(max_lag=3)
model.forecast(steps=5)
# No reindexing or aggregation is needed; validate forecast skill separately.
```

**4. Period-cohort rates (next release)**

Annual and monthly incidence is modelled as period cohorts: each period's
cases are the infectious group for the step to the next period. The infection
rate is estimated from the data, R0 rises before outbreaks, `results['I']` is
period incidence, and `Model(stop=...)` uses no data after `stop`. Zero-case
periods raise a warning; `DataContainer(..., incidence_offset=1)` keeps the
rates defined. See [Known Limitations](user-guide/known-limitations.md).

### Short Annual Series: Validate Before Interpreting

There is no universal minimum number of annual observations that guarantees a
useful VAR forecast. A few dozen points can be enough for the model to fit, but
not enough to estimate stable dynamics; results depend on variation, missingness,
lag selection, and forecast horizon. A flat median with a widening scenario
range is a warning of weakly informative output, not evidence that an outbreak
is unlikely. `generate_result()` logs a warning when the median infected
forecast is flat despite variation in the historical series.

Before using annual forecasts:

- Compare rolling-origin forecasts with simple baselines (such as persistence
  and a trailing median) at the same horizons.
- Inspect the median and scenario spread at each horizon; do not rely on a
  single fitted forecast or reproduction-number estimate.
- Report the number of usable annual observations and failed fits. Do not treat
  a successful VAR fit as validation.

The scenario columns enumerate combinations of rate confidence levels; they
are not calibrated probability samples. The fraction of scenarios exceeding a
case threshold can be reported as a scenario share, but must not be described
as a probability unless separately calibrated against out-of-sample outcomes.

`importation_rate` adds an external force of infection to the model. It is not
estimated from the case series. Set it using independent importation or travel
surveillance evidence where available, and otherwise compare explicitly stated
values as sensitivity scenarios rather than selecting a value to produce a
desired outbreak forecast.

---

## Best Practices

### 1. Data Quality

✅ **DO:**
- Use at least 50+ time points for training
- Verify cumulative data is monotonically increasing
- Check for missing dates and handle gaps
- Use appropriate smoothing (window=7 for noisy daily data)

❌ **DON'T:**
- Mix cumulative and incidence data formats
- Use data with large gaps without interpolation
- Ignore validation warnings

### 2. Model Configuration

✅ **DO:**
- Start with `max_lag=10` for initial exploration
- Use AIC for lag selection: `model.fit_model(max_lag=10, ic="aic")`
- Forecast reasonable horizons (30-90 days for daily data)
- Keep the default sequential simulations; parallel workers rarely pay off (see Slow Simulation Performance)

❌ **DON'T:**
- Over-forecast (> 6 months ahead gets unreliable)
- Use too many lags (max_lag > data points / 3)
- Run simulations sequentially on multi-core systems

### 3. Annual Data (v0.10.0+)

✅ **DO:**
- Use `mode='incidence'` for incident cases (e.g., measles)
- Leave `window` unset: annual data is not smoothed, and a requested window is ignored with a warning
- Pass `incidence_offset` when some years have zero cases, and report it
- Set reasonable `max_lag` for annual frequency (2-4 years)
- Verify fractional recovery lag is applied correctly

❌ **DON'T:**
- Mix annual and daily data without understanding frequency handling
- Use very long forecast horizons (>10 years becomes unreliable)
- Ignore validation of annual forecasts against historical patterns

---

## Troubleshooting

### "Cannot calculate alpha when S or I is zero"

**Cause**: Early epidemic data where susceptible ≈ population or infected = 0

**Solution**: Start after epidemic begins
```python
# Skip early dates with no infections
model = Model(container, start="2020-03-10", stop="2020-12-31")  # Not Jan 1
```

### "NaN values in logit transform"

**Cause**: Rates outside (0, 1) bounds or zero denominators

**Solution**: Automatic in v0.8.0 - pipeline applies `prepare_for_logit_function()` + `ffill()`

Check feature engineering order is correct (S, I, R calculated in sequence)

### "Singular matrix" in VAR fitting

**Cause**: Insufficient data for chosen lag order

**Solution**: Reduce lag or increase training period
```python
model.fit_model(max_lag=5)  # Instead of 10
# OR use longer training period
model = Model(container, start="2020-01-01", stop="2021-12-31")
```

### Slow Simulation Performance

Simulations run sequentially by default. Each scenario (27 for SIRD, 81 for
SIRDV) takes milliseconds, so starting worker processes usually costs more than
it saves. On a 12-core Windows machine, 60-day forecasts took about 0.02 s (SIRD)
and 0.05-0.08 s (SIRDV) sequentially, against about 5 s with one worker per CPU.
Benchmark before switching parallel execution on.

```python
model.run_simulations()          # Default: sequential
model.run_simulations(n_jobs=4)  # Process pool with 4 workers
```

To make a process pool the default, set `PARALLEL_SIMULATIONS=true` (and
optionally `N_SIMULATION_JOBS`) in the environment or a `.env` file.

On Windows and macOS, worker processes are started with `spawn` and re-import
the calling script. Scripts that request parallel execution must put the code
that runs simulations behind a `__main__` guard; otherwise each worker re-runs
the script's top-level code and fails. If the pool breaks, DynaSIR logs a
warning and reruns the simulations sequentially. In notebooks and interactive
sessions, keep the sequential default.

```python
def main():
    model.run_simulations(n_jobs=4)


if __name__ == "__main__":
    main()
```

For short annual incidence series, forecasts may have a flat median or rapidly
widening scenario ranges. DynaSIR does not have a validated universal minimum
sample size for annual forecasting; use annual-data results as uncertain
scenarios rather than precise outbreak predictions. A flat median infected
forecast is logged as a warning when the training data varied.

---

## Incidence Mode (v0.9.0+)

**New in v0.9.0**: Native support for **incidence data** (incident cases per period) without requiring conversion to cumulative format.

### Understanding Incidence vs Cumulative

**Cumulative Mode** (default):
- Input: Total cumulative cases `C` (monotonically increasing)
- Derived: Incident cases `I = dC/dt` (calculated from differences)
- Use case: COVID-19, flu pandemics, most OWID data

**Incidence Mode** (v0.9.0+):
- Input: Incident cases per period `I` (can vary up/down)
- Derived: Cumulative cases `C = cumsum(I)` (generated automatically)
- Use case: Measles, polio, vaccine-preventable diseases with elimination cycles

### When to Use Incidence Mode

✅ **Use `mode='incidence'` when:**
- Data reports **new cases per time period** (not running totals)
- Cases can **decrease between periods** (e.g., outbreak → elimination)
- Disease: Near-elimination status, sporadic outbreaks
- Examples: Measles, polio, rubella in countries with strong vaccination
- Frequency: Typically annual, quarterly, or monthly surveillance

❌ **Use default `mode='cumulative'` when:**
- Data reports **total cumulative cases**
- Cases **always increase** (or stay constant)
- Disease: Ongoing epidemic, endemic circulation
- Examples: COVID-19, seasonal flu, most OWID datasets
- Frequency: Daily, weekly observations

### Basic Workflow

```python
import pandas as pd
from dynasir import DataContainer, Model

# Example: Mexico measles (annual incident cases)
dates = pd.date_range('2010', periods=15, freq='YE')
data = pd.DataFrame({
    'I': [220, 55, 667, 164, 81,      # Incident cases (can vary)
          34, 12, 0, 0, 4,            # Near-elimination
          18, 45, 103, 67, 89],       # Reintroduction
    'D': [1, 1, 3, 4, 4, ...],        # Cumulative deaths
    'N': [120_000_000] * 15
}, index=dates)

# Create container with incidence mode (zero-case years: see incidence_offset)
container = DataContainer(data, mode='incidence', frequency='YE', incidence_offset=1)

# Standard workflow (no changes!)
model = Model(container)
model.create_model()
model.fit_model(max_lag=3)
model.forecast(steps=5)
model.run_simulations(n_jobs=1)
model.generate_result()

# Results include I (period incidence), I_active (active infections) and C
print(model.results['I'])         # Incident cases per period (can vary)
print(model.results['I_active'])  # Currently infected
print(model.results['C'])         # Cumulative (monotonic)
```

### How It Works

1. **Data Processing:**
   - Incidence mode: `I` preserved, `C = cumsum(I)` generated
   - Cumulative mode: `C` preserved, `I = C - C_lagged` (active infections) generated

2. **Feature Engineering:**
   - In incidence mode `I` is always period incidence, and `I_active` is the
     active-infection stock that the rates divide by:
     - annual and monthly data (recovery lag of at most one period): each
       period's cases are the infectious cohort, so `I_active = I`;
     - daily, business-day and weekly data: `I_active = C - C_lagged`, the
       cases of the last recovery-lag periods, exactly as cumulative mode's `I`.
   - `C = I_active + R + D` in every row; forecasts report `I` as incidence
     and `I_active` as the stock. Aggregate `I` with `sum` and `I_active`
     with `mean` or `last`.
   - Same VAR forecasting approach in both modes

3. **Mode Propagation:**
   ```python
   container = DataContainer(data, mode='incidence')
   model = Model(container)  
   print(model.mode)  # → 'incidence' (auto-inherited)
   ```

### Example: Measles Outbreak Cycles

```python
# Elimination → reintroduction pattern
incident_cases = np.array([
    220, 55, 667, 164, 81,   # Sporadic
    34, 12, 0, 0, 4,         # Elimination
    18, 45, 103, 67, 89      # Reintroduction
])

container = DataContainer(data, mode='incidence')

# I can decrease to zero (elimination achieved)
print("Elimination years:", (container.data['I'] == 0).sum())

# But C is always monotonic
print("C monotonic:", all(container.data['C'].diff() >= 0))
```

### See Also

- **Notebook**: `examples/notebooks/07_incidence_mode_measles.ipynb`
- **Tests**: `tests/integration/test_incidence_mode_workflow.py`

---

## Looking Ahead: v0.11.0+

Future enhancements may include:
- Complete visualization test suite (423/423 passing)
- Real-world measles data validation with published datasets
- Importation modeling for eliminated diseases
- Advanced probabilistic forecasting workflows

---

## Additional Resources

- **Developer Documentation**: See `CLAUDE.md` for internal architecture
- **API Reference**: See `docs/API_AUDIT.md`
- **Examples**: Check `examples/notebooks/` for complete workflows
- **Issues**: Report problems at https://github.com/julihocc/dynasir/issues

---

**Questions?** Open an issue or check the examples in `examples/notebooks/`.

**Contributing?** See `CONTRIBUTING.md` for development guidelines.
