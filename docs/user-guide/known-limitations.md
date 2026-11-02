# Known Limitations

This document describes known limitations in the dynasir library and provides recommended workarounds.

## Annual Incidence Data with VAR Forecasting

**Version Affected**: v0.9.0+
**Severity**: ⚠️ **High** - VAR model fitting will fail
**Status**: Documented limitation with clear workarounds

### Problem Description

When using **annual frequency** (`freq='YE'`) data with **incidence mode** (`mode='incidence'`), the VAR forecasting model cannot fit successfully due to mathematical constraints.

**Root Cause**:
1. Annual frequency results in `recovery_lag = 0` (14 days ÷ 365 days ≈ 0)
2. In incidence mode, everyone infected in year *t* recovers in the same year *t*
3. This makes the recovery rate constant: `beta(t) = R/I = I/I = 1.0` (always)
4. Similarly, infection and mortality rates become constant
5. VAR cannot fit models on data with zero variance (constant rates)

**Error Message**:
```
numpy.linalg.LinAlgError: N-th leading minor of the array is not positive definite
```

### Example of Problematic Code

```python
import pandas as pd
from dynasir import DataContainer, Model

# Annual measles incident data (WILL FAIL)
data = pd.DataFrame({
    'I': [220, 55, 667, 164, 81, 34, 12, 0, 0, 4, 18, 45, 103, 67, 89],
    'D': [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
    'N': [110_000_000] * 15
}, index=pd.date_range('2010', periods=15, freq='YE'))

# This combination will fail at VAR fitting
container = DataContainer(data, mode='incidence', frequency='YE')
model = Model(container, start='2010', stop='2020')
model.create_model()
model.fit_model()  # ❌ FAILS: LinAlgError
```

### What Works

✅ **DataContainer creation** - Works correctly
✅ **Feature engineering** - All SIRD compartments calculated
✅ **Model object creation** - No issues
❌ **VAR model fitting** - **FAILS** due to constant rates

### Recommended Solutions

#### Solution 1: Use Monthly or Weekly Data (Recommended)

Monthly (`freq='ME'`) or weekly (`freq='W'`) data provides sufficient temporal resolution for VAR modeling while maintaining the incidence mode benefits.

```python
# Convert annual to monthly (recommended)
# Option A: If you have monthly data available
monthly_data = pd.DataFrame({
    'I': monthly_incident_cases,  # Monthly incident cases
    'D': cumulative_deaths,
    'N': population
}, index=pd.date_range('2010', periods=180, freq='ME'))

# Monthly + incidence works perfectly ✅
container = DataContainer(monthly_data, mode='incidence', frequency='ME')
model = Model(container, start='2010-01', stop='2020-12')
model.create_model()
model.fit_model(max_lag=6)  # ✅ Works! Rates vary over time
model.forecast(steps=12)
model.run_simulations()
model.generate_result()
```

**Why This Works**:
- Monthly recovery lag = 0.5 months (14 days ÷ 30 days)
- Recovery occurs in next period, creating time-varying rates
- VAR can model the dynamics successfully

#### Solution 2: Use Cumulative Mode with Annual Data

If you only have annual data and want to use VAR, switch to cumulative mode (if your data represents cumulative totals).

```python
# Annual + cumulative works ✅
annual_cumulative = pd.DataFrame({
    'C': cumulative_cases,  # Cumulative, not incident
    'D': cumulative_deaths,
    'N': population
}, index=pd.date_range('2010', periods=15, freq='YE'))

container = DataContainer(annual_cumulative, mode='cumulative', frequency='YE')
model = Model(container)
model.create_model()
model.fit_model(max_lag=2)  # ✅ May work with sufficient data
```

**Note**: Annual cumulative data with VAR still requires 20+ years of data due to small sample size.

#### Solution 3: Use Alternative Forecasting Methods (Future)

For annual incidence data, non-VAR forecasting methods are more appropriate:

- **ARIMA**: Direct time series forecasting on incident cases
- **Prophet**: Handles seasonality and trends
- **Simple Exponential Smoothing**: For basic forecasting

**Status**: These backends are planned for v0.10.0+ (see [OPTION_D_IMPLEMENTATION.md](../development/OPTION_D_IMPLEMENTATION.md))

```python
# Future API (v0.10.0+)
model.fit_model(backend='arima', max_lag=3)  # Not yet available
```

### Frequency Recommendations by Data Type

| Data Type | Frequency | Mode | VAR Compatible | Notes |
|-----------|-----------|------|----------------|-------|
| COVID-19 daily | `D` | `cumulative` | ✅ Yes | Ideal for VAR |
| COVID-19 weekly | `W` | `cumulative` | ✅ Yes | Good for VAR |
| Measles monthly | `ME` | `incidence` | ✅ Yes | **Recommended** |
| Measles weekly | `W` | `incidence` | ✅ Yes | Good for VAR |
| Measles annual | `YE` | `incidence` | ❌ **NO** | Use monthly instead |
| Measles annual | `YE` | `cumulative` | ⚠️ Maybe | Need 20+ years |
| Stock/trading | `B` | `cumulative` | ✅ Yes | Business days |

### How to Check if Your Data Will Work

```python
from dynasir import DataContainer

# Create container
container = DataContainer(data, mode='incidence', frequency='YE')

# Check rate variance (should be > 0 for VAR to work)
rate_variance = container.data[['alpha', 'beta', 'gamma']].var()
print(rate_variance)

# If all variances are near zero (< 1e-10), VAR will fail
if rate_variance.max() < 1e-10:
    print("⚠️ WARNING: Constant rates detected!")
    print("   VAR model fitting will fail.")
    print("   Use monthly/weekly data or non-VAR backend.")
```

### Detection and Warnings

The library will attempt to detect this situation and provide helpful warnings:

```python
# Planned for future versions
2025-12-21 - WARNING - dynasir.data.frequency_handlers
  AnnualFrequencyHandler with incidence mode may produce constant rates.
  Consider using monthly (ME) or weekly (W) frequency for better VAR performance.
```

### Related Issues

- **Issue #127**: AnnualFrequencyHandler verification
- **Issue #128**: Complete measles workflow verification (identified limitation)
- **Task 2**: Verification results documenting this limitation
- **Option D**: Hybrid approach for addressing limitation

### Additional Resources

- [Verification Results](../development/VERIFICATION_RESULTS.md#task-2-complete-measles-workflow-128) - Root cause analysis
- [Option D Implementation Plan](../development/OPTION_D_IMPLEMENTATION.md) - Future enhancements
- [CLAUDE.md](../../CLAUDE.md) - Development guide with best practices

### Summary

**TL;DR**:
- ❌ **Don't use**: Annual frequency + incidence mode + VAR
- ✅ **Use instead**: Monthly/weekly frequency + incidence mode + VAR
- ⚠️ **Or wait for**: v0.10.0+ with ARIMA/Prophet backends

This is a mathematical limitation, not a bug. The infrastructure works correctly; VAR is simply not the right tool for this specific data combination.

---

**Last Updated**: December 21, 2025
**Version**: v0.9.1+
