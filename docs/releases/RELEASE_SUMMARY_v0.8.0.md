# DynaSIR v0.8.0 Release Summary

**Release Date**: December 7, 2025  
**Release Type**: GitHub Pre-release (Not on PyPI)  
**Code Name**: Multi-Frequency Support & Annual Data Workarounds  
**Phase**: 1 of 3 (Measles Integration)

---

## Overview

Version 0.8.0 introduces Phase 1 support for multi-frequency epidemiological data, with particular focus on enabling annual surveillance data (e.g., measles) through workarounds and temporal aggregation. This release maintains 100% backward compatibility while adding new capabilities for frequency detection and forecast aggregation.

## Key Features

### 1. Automatic Frequency Detection
- Detects daily (D), weekly (W), monthly (M), and annual (Y) data frequencies
- Warns users when frequency mismatches occur (e.g., annual→daily reindexing)
- Provides actionable recommendations

### 2. Temporal Aggregation
- New `Model.aggregate_forecast()` method
- Convert daily forecasts to annual/monthly/weekly output
- Multiple aggregation functions: sum, mean, last, max, min
- Preserves confidence intervals from simulation scenarios

### 3. Modern Pandas Compatibility
- Updated to pandas 2.2+ frequency aliases (Y→YE, M→ME)
- Eliminated all FutureWarnings
- Forward-compatible with future pandas versions

### 4. Comprehensive Documentation
- New 400+ line User Guide covering all use cases
- Example notebook demonstrating annual data workflow
- Updated README and developer documentation
- Clear migration path to v0.9.0

## Statistics

- **New Code**: 5 new files, ~1,500+ lines
- **Tests**: 45 new tests, 291 total passing (100% pass rate)
- **Documentation**: 3 major docs added/updated
- **Backward Compatibility**: 100% maintained
- **Performance**: No regression, < 100ms overhead for aggregation

## What's New for Users

### For COVID-19/Daily Data Users
✅ **No changes needed** - Everything works exactly as before

### For Annual Data Users (Measles, etc.)
✅ **New workflow available**:
```python
# Suppress warnings (we understand limitations)
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message=".*FREQUENCY MISMATCH.*")
    container = DataContainer(annual_data, window=1)

# Forecast internally in daily resolution
model = Model(container, start="1982", stop="2010")
model.create_model()
model.fit_model(max_lag=3)
model.forecast(steps=365 * 10)  # 10 years
model.run_simulations(n_jobs=1)
model.generate_result()

# Aggregate to annual output
annual_forecast = model.aggregate_forecast(
    "C", target_frequency="Y", aggregate_func="last"
)
```

## Breaking Changes

**None** - This release is 100% backward compatible.

## Known Limitations

- Annual data still reindexed to daily internally (creates artificial patterns)
- Temporal aggregation is a workaround, not a true solution
- Not recommended for production critical decisions

## Installation

**This is a pre-release available only via GitHub:**

```bash
# Install from GitHub (address-measles-integration branch)
pip install git+https://github.com/julihocc/dynasir.git@address-measles-integration

# Or clone and install locally
git clone -b address-measles-integration https://github.com/julihocc/dynasir.git
cd dynasir
pip install -e .
```

**PyPI Release**: v0.7.0 remains the stable PyPI version. v0.9.0+ will be released to PyPI after Phase 2 (Incidence Mode + Native Multi-frequency) is complete.
- Native annual support coming in v0.9.0 (Q1 2026)

## Migration Guide

### From v0.7.0 to v0.8.0

**No changes required** for existing code. All v0.7.0 code runs unchanged.

**To use new features**:
1. Read `docs/USER_GUIDE.md` for annual data guidance
2. See `examples/notebooks/06_annual_measles_workaround.ipynb` for complete workflow
3. Use `Model.aggregate_forecast()` for temporal aggregation

### Preparing for v0.9.0

Version 0.9.0 (Q1 2026) will introduce native multi-frequency support:
- No reindexing needed
- True annual/monthly modeling
- Incidence-first mode
- Production-ready for all frequencies

Current v0.8.0 workarounds will continue to work in v0.9.0 for backward compatibility.

## Installation

```bash
# From PyPI (after publication)
pip install dynasir==0.8.0

# From source
git clone https://github.com/julihocc/dynasir.git
cd dynasir
git checkout v0.8.0
pip install -e .
```

## Testing

```bash
# Run all tests
pytest

# Run only frequency/temporal tests
pytest -k "frequency or temporal or annual"

# With coverage
pytest --cov=src/dynasir --cov-report=html
```

All 291 tests pass with 45 new tests specific to v0.8.0 features.

## Documentation

- **User Guide**: `docs/USER_GUIDE.md` - Start here!
- **Tutorial**: `TUTORIAL.md` - COVID-19 workflow
- **Example Notebooks**: `examples/notebooks/` - Complete workflows
- **Developer Docs**: `CLAUDE.md` - Internal architecture
- **API Audit**: `docs/API_AUDIT.md` - API reference
- **Changelog**: `CHANGELOG.md` - Detailed changes

## What's Next

### Phase 2 (v0.9.0 - Q1 2026)
- Native multi-frequency support
- Incidence-first modeling mode
- Frequency-specific rate calculations
- No reindexing needed

### Phase 3 (v1.0.0 - Q2 2026)
- Outbreak detection
- Probabilistic forecasting enhancements
- Coverage-based SIRDV with waning immunity
- Scenario analysis tools

## Credits

**Lead Developer**: Juliho David Castillo Colmenares (@julihocc)

**Related Issues**:
- #99: Frequency detection
- #100: Temporal aggregation
- #101: Documentation
- #102: Example notebook
- #98: Phase 1 Epic

## Support

- **Issues**: https://github.com/julihocc/dynasir/issues
- **Discussions**: https://github.com/julihocc/dynasir/discussions
- **Email**: See `pyproject.toml` for contact info

---

**Download**: [v0.8.0 Release](https://github.com/julihocc/dynasir/releases/tag/v0.8.0)

**Previous Release**: [v0.7.0](https://github.com/julihocc/dynasir/releases/tag/v0.7.0)
