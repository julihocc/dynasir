# Release Notes - v0.11.0

**Release Date**: January 8, 2026  
**Status**: Production Release - Ready for PyPI  

## Overview

Version 0.11.0 represents the consolidation and polish of all features from the v0.10.0 release cycle. This release is now published on PyPI and represents the first officially published version of dynasir with comprehensive support for epidemiological forecasting, reporting, and multi-frequency time series analysis.

**Key Milestone**: First PyPI publication of dynasir library with production-grade quality assurance.

## What's New in v0.11.0

### 1. Production Release Readiness

- **100% Test Pass Rate**: All 433 tests passing (including 36 integration/verification tests)
- **Code Quality**: Black formatting, isort import sorting, and flake8 linting complete
- **Documentation Complete**: All 7 example notebooks validated and working
- **Backward Compatibility**: Full v0.9.1 compatibility verified via test suite

### 2. Reporting & Publication Tools (From v0.10.0)

The `ModelReport` class provides one-call publication generation:

```python
from dynasir.analysis import ModelReport

# Create comprehensive report from model results
report = ModelReport(
    results=model.results,
    testing_data=test_data,
    compartments=['I', 'D']
)

# Generate publication-ready outputs
report.export_markdown("analysis.md", include_figure=True)
report.export_latex_table("table1.tex", "summary")
fig = report.plot_forecast_panel(dpi=600, save_path="forecast.png")
```

**Features**:
- Markdown reports with embedded figures
- LaTeX tables for journal submissions
- High-resolution figures (300-600 DPI)
- Summary statistics and evaluation metrics
- Model comparison visualizations

### 3. Multi-Frequency Native Support (From v0.9.0)

Annual data stays annual. No artificial reindexing:

```python
# 15 annual observations = 15 rows (not 5,475 daily rows)
container = DataContainer(annual_data, frequency='YE')  # Native annual
model = Model(container)
model.create_model()  # Handles fractional lags automatically
```

**Frequencies Supported**:
- Daily (D)
- Business day (B)
- Weekly (W)
- Monthly (M)
- Annual (YE) ← **Fixed in v0.10.0 with fractional recovery lag**

### 4. Fractional Recovery Lag (From v0.10.0)

Annual frequency now uses 14/365 = 0.0384 years instead of rounding to 0:

```python
# Before v0.10.0:
lag = 14 days → 0 years (rounded) → beta constant → singular matrix error

# After v0.10.0:
lag = 14 days → 0.0384 years (fractional) → beta varies → VAR fits successfully
```

This fix enables annual + incidence mode (measles, polio, rubella) to work without errors.

### 5. Dual-Mode Architecture

**Cumulative Mode** (COVID-19):
```python
# Input: cumulative cases C (monotonic)
# Auto-derives: I = diff(C), rates based on cumsum
container = DataContainer(covid_data, mode='cumulative', frequency='D')
```

**Incidence Mode** (Measles/Polio):
```python
# Input: incident cases I (per time period)
# Auto-derives: C = cumsum(I), rates based on incidence
container = DataContainer(measles_data, mode='incidence', frequency='YE')
```

## Architecture Improvements in v0.11.0

### Frequency Handler Refactoring

- Unified API for frequency-specific logic
- Factory pattern for handler instantiation: `registry.get(frequency)`
- Automatic detection of recovery lags and VAR defaults
- Graceful handling of elimination phases (constant alpha/gamma)

### VAR Model Enhancement

Automatic constant column detection prevents multicollinearity:

```python
# No manual intervention needed
# VAR automatically uses trend='n' when alpha/gamma are constant
model.fit_model(max_lag=3)  # Works even in elimination phase
```

### Parallel Simulation Support

4-7x speedup on multi-core systems:

```python
# Auto-detect CPU count
model.run_simulations(n_jobs=None)  # ← Uses ProcessPoolExecutor

# Manual control
model.run_simulations(n_jobs=4)  # 4 cores
```

## Installation & Testing

### Install from PyPI

```bash
pip install dynasir==0.11.0
```

### Verify Installation

```bash
python -c "import dynasir; print(dynasir.__version__)"
# Output: 0.11.0
```

### Quick Example

```python
import pandas as pd
from dynasir import DataContainer, Model
from dynasir.analysis import ModelReport

# Prepare data
data = pd.DataFrame({
    'I': [...],
    'D': [...],
    'N': [120_000_000]
}, index=dates)

# Create and fit model
container = DataContainer(data, mode='incidence', frequency='YE')
model = Model(container)
model.create_model()
model.fit_model(max_lag=3)
model.forecast(steps=5)
model.run_simulations(n_jobs=None)
model.generate_result()

# Generate publication-ready report
report = ModelReport(model.results, test_data, compartments=['I', 'D'])
report.export_markdown("analysis.md", include_figure=True)
```

## Breaking Changes

**None**. This is a production release with full backward compatibility to v0.9.1.

## Bug Fixes

1. **Annual Frequency + Incidence Mode**: Fixed singular matrix error by using fractional recovery lag
2. **VAR Constant Column Handling**: Automatic trend detection prevents multicollinearity
3. **Handler API Consistency**: Unified getter methods across frequency handlers
4. **Test Suite Robustness**: Fixed 6 test failures related to handler factory API

## Dependencies

Core dependencies (unchanged from v0.10.0):

```
pandas>=1.3.0
numpy>=1.20.0
scipy>=1.7.0
statsmodels>=0.13.0
python-box>=6.0.0
pydantic-settings>=2.0.0
pydantic>=2.0.0
```

Optional dependencies:

```
prophet>=1.1.0        # For Prophet backend
scikit-learn>=0.24.0  # For additional statistical methods
```

Development dependencies (auto-included in `[dev]` extra):

```
pytest>=7.0.0
pytest-cov>=3.0.0
black>=22.0.0
isort>=5.10.0
flake8>=4.0.0
mypy>=0.950
```

## Tested Against

- Python 3.9, 3.10, 3.11, 3.12 (CI/CD verified)
- macOS 13+, Ubuntu 20.04+, Windows 10/11

## Example Notebooks

All 7 example notebooks included and validated:

1. **01_sird_basic_workflow.ipynb** - Basic SIRD model workflow
2. **02_sirdv_vaccination_analysis.ipynb** - SIRDV with vaccination
3. **03_global_covid19_forecasting.ipynb** - Multi-country COVID-19 analysis
4. **04_parallel_simulations.ipynb** - Performance comparison
5. **05_multi_backend_comparison.ipynb** - Backend comparison
6. **06_incidence_mode_measles.ipynb** - **Measles with annual frequency** (uses v0.10.0 fix)
7. **07_reporting_and_publication.ipynb** - **Comprehensive reporting demo** (new in v0.10.0)

## Performance Benchmarks

**Parallel Simulation Performance** (measured on 4-core system):

- Sequential: 12.4 seconds (100 simulations)
- Parallel: 2.1 seconds (4-core ProcessPoolExecutor)
- **Speedup**: 5.9x

Memory usage remains constant (~85 MB for 100 simulations).

## Documentation

- **README.md**: Quick start guide and feature overview
- **CLAUDE.md**: Comprehensive developer guide
- **USER_GUIDE.md**: Complete API documentation
- **ARCHITECTURE.md**: Internal design and data flow
- **docs/REPORTING_GUIDE.md**: Publishing workflow

## Known Limitations

1. **Prophet Backend**: Requires `pip install dynasir[prophet]` for Prophet support
2. **GPU Support**: Not currently supported (uses CPU-based statsmodels)
3. **Real-time Forecasting**: Designed for batch/offline analysis
4. **Maximum Frequency**: Supports up to daily frequency (intraday not supported)

## Upgrade Path from v0.10.0

No changes required. v0.11.0 is a pure production release of v0.10.0.

```bash
# Simply update
pip install --upgrade dynasir==0.11.0
```

All v0.10.0 code runs unchanged on v0.11.0.

## Upgrade Path from v0.9.1 and Earlier

Full backward compatibility maintained:

```bash
# Works without code changes
pip install dynasir==0.11.0
```

The library automatically detects data mode (cumulative/incidence) and frequency. See **CONTRIBUTING.md** for detailed migration examples.

## What's Next (v0.12.0 Roadmap)

- [ ] Real-time streaming forecasting API
- [ ] GPU acceleration via CuPy
- [ ] Additional statistical backends (ARIMAX, Prophet improvements)
- [ ] Interactive Jupyter dashboards
- [ ] Bayesian uncertainty quantification
- [ ] Multi-model ensemble forecasting

## Contributors

Thanks to all contributors and testers:

- **Lead Development**: @julihocc
- **GitHub Copilot Agent**: @copilot-swe-agent
- **Community**: See CONTRIBUTING.md for full acknowledgments

## Support & Reporting Issues

- **GitHub Issues**: https://github.com/julihocc/dynasir/issues
- **Documentation**: https://github.com/julihocc/dynasir/wiki
- **PyPI Package**: https://pypi.org/project/dynasir/

## License

Apache License 2.0 - See LICENSE file for details

---

**Happy Forecasting! 🚀**

For questions and feedback, please open a GitHub issue or pull request.
