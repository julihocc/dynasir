# Release Notes - v0.9.1

**Release Date**: December 23, 2025

## 🎯 Native Annual Frequency Support

Version 0.9.1 introduces native annual frequency support with fractional recovery lag, enabling epidemiological modeling of eliminated diseases (measles, polio, rubella) with sporadic outbreak patterns.

### The Problem We Solved

**Before v0.9.1**: Using annual frequency with incidence mode failed with:
```
LinAlgError: 1-th leading minor of the array is not positive definite
```

**Root Cause**: Integer recovery lag (14 days → 0 years) caused beta rate to be constant (1.0), creating a singular covariance matrix for VAR models.

**After v0.9.1**: Beta varies naturally (0.038 to 1.0), VAR fits successfully, and forecasts work correctly.

## ✨ New Features

### Fractional Recovery Lag
- **Annual Frequency**: 14 days = 0.0384 years (14/365)
- **Monthly Frequency**: 14 days = 0.47 months (14/30)
- **Linear Interpolation**: Smooth handling of fractional time shifts

### Automatic Constant Column Detection
- VAR models automatically detect constant columns (e.g., alpha = 1.0)
- Uses `trend='n'` (no trend) to prevent multicollinearity errors
- Handles elimination-phase disease patterns gracefully

### Native Frequency Processing
- Annual data stays annual (no artificial reindexing)
- 15 annual observations remain 15 rows (not 5,475 daily rows)
- Frequency-aware feature engineering and forecasting

## 📊 Example Usage

```python
import pandas as pd
import numpy as np
from dynasir import DataContainer, Model

# Annual measles incident cases (Mexico 2010-2024)
dates = pd.date_range("2010", periods=15, freq="YE")
data = pd.DataFrame({
    "I": [220, 55, 667, 164, 81, 34, 12, 0, 0, 4, 18, 45, 103, 67, 89],
    "D": [1, 1, 3, 4, 4, 4, 4, 4, 4, 4, 4, 5, 7, 8, 9],
    "N": [120_000_000] * 15
}, index=dates)

# Native annual frequency + incidence mode
container = DataContainer(data, mode="incidence", frequency="YE", window=1)
model = Model(container)
model.create_model()
model.fit_model(max_lag=3)  # ✅ Works! Beta varies: 0.038 to 1.0
model.forecast(steps=5)      # Forecast 5 YEARS
model.run_simulations(n_jobs=1)
model.generate_result()

print(model.results.C)  # Annual forecasts
```

## 🔧 Technical Changes

### Core Implementation

**`src/dynasir/data/frequency_handlers.py`**
- Changed `get_recovery_lag()` return type: `int` → `float`
- `AnnualFrequencyHandler.get_recovery_lag()`: returns `14/365` (0.0384)
- `MonthlyFrequencyHandler.get_recovery_lag()`: returns `14/30` (0.47)

**`src/dynasir/data/features.py`**
- Implemented fractional lag interpolation
- Formula: `(1-weight) * shift(floor) + weight * shift(ceil)`
- Applied to both cumulative and incidence modes

**`src/dynasir/models/forecasting/var.py`**
- Added automatic constant column detection
- Uses `trend='n'` when constants present
- Logs warnings for better debugging

### Testing

**New Tests**: +10 comprehensive integration tests
- `test_fractional_recovery_lag_implementation`
- `test_var_model_fits_with_annual_incidence`
- `test_complete_annual_incidence_workflow`
- `test_constant_column_detection`
- `test_incidence_mode_preserves_variation`
- `test_annual_frequency_no_reindexing`
- `test_model_mode_propagation`
- `test_fractional_lag_interpolation_accuracy`
- `test_daily_data_unchanged`
- `test_cumulative_mode_unchanged`

**Updated Tests**: 51 frequency handler tests updated for fractional lags

**Test Results**: 421/423 passing (99.5%)

### Notebooks

- ✅ All 6 example notebooks validated and passing
- ✅ Deleted obsolete `06_annual_measles_workaround.ipynb`
- ✅ Renamed `07_incidence_mode_measles.ipynb` → `06_incidence_mode_measles.ipynb`
- ✅ Updated notebook 06 with v0.9.1 API

## 🔄 Breaking Changes

**None**. Version 0.9.1 is fully backward compatible with v0.8.0.

## 📈 Performance

- No performance degradation for existing workflows
- Significant improvement for annual data (no artificial reindexing overhead)
- Memory usage reduced for annual frequency data

## 🚀 Migration Guide

### No Migration Needed!

Existing code continues to work without changes.

### New Capability (Optional)

```python
# Old approach (v0.8.0): Would fail with LinAlgError
container = DataContainer(annual_data, mode="incidence")

# New approach (v0.9.1): Works natively
container = DataContainer(annual_data, mode="incidence", frequency="YE")
```

## 📚 Documentation

- **PR #138**: Full implementation details
- **Notebook 06**: `incidence_mode_measles.ipynb` demonstrates complete workflow
- **FIX_SUMMARY.md**: Technical documentation of the fractional lag fix
- **TESTING_RESULTS.md**: Comprehensive test validation report

## 🙏 Acknowledgments

This release addresses a critical limitation for modeling eliminated diseases with sporadic outbreak patterns. Special thanks to the epidemiology community for highlighting the need for native annual frequency support.

## 🐛 Known Issues

- 2 pre-existing visualization test failures (unrelated to v0.9.1 changes)
- See issue #141 for tracking

## 📦 Installation

```bash
pip install dynasir==0.9.1
```

Or upgrade from previous version:

```bash
pip install --upgrade dynasir
```

## 🔗 Links

- **Full Changelog**: [v0.8.0...v0.9.1](https://github.com/julihocc/dynasir/compare/v0.8.0...v0.9.1)
- **Pull Request**: [#138](https://github.com/julihocc/dynasir/pull/138)
- **Documentation**: [USER_GUIDE.md](docs/USER_GUIDE.md)
- **Examples**: [examples/notebooks/](examples/notebooks/)

## 🎉 What's Next

See our [roadmap](https://github.com/julihocc/dynasir/issues) for upcoming features:
- Real-world measles data validation (#142)
- Outbreak detection module (#124-126)
- Additional frequency support

---

**Questions or Issues?** Please report at https://github.com/julihocc/dynasir/issues
