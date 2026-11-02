# Release Notes: dynasir v0.7.0

**Release Date:** November 28, 2025  
**Status:** Production Release

## 🎉 Major New Feature: SIRDV Model Support

This release introduces full support for the **SIRDV (Susceptible-Infected-Recovered-Deaths-Vaccinated)** model, enabling epidemic forecasting with vaccination campaigns.

### Key Highlights

- **Vaccination Modeling**: Track vaccination campaigns with the new V (Vaccinated) compartment
- **4-Rate Forecasting**: VAR models now support δ (vaccination rate) alongside α, β, γ
- **81 Simulation Scenarios**: SIRDV runs 3⁴ = 81 scenarios vs 27 for SIRD
- **Automatic Detection**: Models automatically switch to SIRDV when vaccination data is present
- **100% Backward Compatible**: Existing SIRD code continues to work unchanged

## 🆕 New Features

### SIRDV Model Components

1. **V Compartment** - Tracks vaccinated population
2. **δ Rate** - Vaccination rate (δ = dV/S)
3. **Updated Conservation Law** - N = S + I + R + D + V
4. **Vaccination Flow** - vaccination = δ × S (removes from susceptible)

### Enhanced Analysis Tools

- `evaluate_forecast()` - Now supports V compartment metrics
- `visualize_results()` - Displays vaccination forecasts
- Conservation law validation for both SIRD and SIRDV

### Configuration Options

New environment variables for SIRDV control:

```bash
ENABLE_VACCINATION=True              # Enable SIRDV mode
VACCINATION_COLUMN=people_vaccinated # Column name in data
```

## 📊 Performance & Quality

- **192 Tests** - All passing (100%)
- **67% Code Coverage** - Comprehensive test suite
- **4 Example Notebooks** - Complete tutorials for SIRD and SIRDV
- **Parallel Simulations** - 2-7x speedup on multi-core systems

## 🔧 Technical Details

### API Changes

**New Methods:**
- `Model.has_vaccination` - Property to check if model uses SIRDV
- `process_data_from_owid(..., include_vaccination=True)` - Fetch vaccination data

**Enhanced Methods:**
- All analysis functions now support 7 compartments (S, I, R, D, V, C, A)
- Evaluation metrics extended for V compartment
- Visualization tools handle vaccination forecasts

### Mathematical Formulation

**SIRDV Equations:**
```
dS/dt = -α·S·I/N - δ·S
dI/dt = α·S·I/N - β·I - γ·I
dR/dt = β·I
dD/dt = γ·I
dV/dt = δ·S
```

**Conservation:**
```
N = S + I + R + D + V (constant)
```

**Rates:**
```
α(t) = (A·dC)/(I·S)  [infection]
β(t) = dR/I          [recovery]
γ(t) = dD/I          [mortality]
δ(t) = dV/S          [vaccination]
```

## 📦 Installation & Upgrade

### From PyPI

```bash
pip install --upgrade dynasir
```

### From Source

```bash
git clone https://github.com/julihocc/dynasir.git
cd dynasir
pip install -e .
```

## 🚀 Quick Start: SIRDV Example

```python
from dynasir import DataContainer, Model, process_data_from_owid

# Load data with vaccination
raw_data = process_data_from_owid(iso_code="ISR", include_vaccination=True)
container = DataContainer(raw_data, window=7)

# Create model (auto-detects SIRDV)
model = Model(container, start="2021-03-01", stop="2021-09-30")
model.create_model()
model.fit_model(max_lag=7, ic="aic")

# Forecast and simulate (81 scenarios)
model.forecast(steps=30)
model.run_simulations(n_jobs=None)  # Parallel execution
model.generate_result()

# Evaluate including V compartment
testing_data = container.data.loc[model.forecasting_interval]
evaluation = model.evaluate_forecast(testing_data, compartment_codes=("C", "D", "I", "V"))

# Visualize vaccination forecast
model.visualize_results("V", testing_data, log_response=False)
```

## 📚 Documentation

### New Notebooks

1. **01_sird_basic_workflow.ipynb** - Introduction to SIRD modeling
2. **02_sirdv_vaccination_analysis.ipynb** - Complete SIRDV tutorial
3. **03_global_covid19_forecasting.ipynb** - Real-world COVID-19 analysis
4. **04_parallel_simulations.ipynb** - Performance benchmarking

### Updated Documentation

- `README.md` - Updated with SIRDV examples
- `CHANGELOG.md` - Complete v0.7.0 changelog
- `CLAUDE.md` - Developer guide with SIRDV section

## 🔄 Migration Guide

### No Changes Required for SIRD Users

Existing SIRD code works without modification:

```python
# This still works exactly as before
raw_data = process_data_from_owid(iso_code="OWID_WRL")  # No vaccination
container = DataContainer(raw_data, window=7)
model = Model(container, start="2020-03-01", stop="2020-12-31")
# ... rest of SIRD workflow unchanged
```

### Opting Into SIRDV

To use SIRDV, simply include vaccination data:

```python
# Add include_vaccination=True parameter
raw_data = process_data_from_owid(iso_code="USA", include_vaccination=True)
# Everything else automatic!
```

## 🐛 Bug Fixes

- Fixed `VARForecaster` attribute access (`logit_ratios_model_fitted` vs `fitted_model`)
- Corrected `forecasting_box` dict access patterns in notebooks
- Improved error handling for missing vaccination data
- Enhanced conservation law validation

## ⚠️ Known Issues

- Vaccination data not available for all countries/periods
- SIRDV requires longer training periods or smaller `max_lag` (recommend max_lag=7)
- 81 SIRDV scenarios use ~3x more memory than 27 SIRD scenarios

## 🔮 What's Next

### Planned for v0.8.0

- **SEIR Models** - Adding Exposed compartment
- **Age Stratification** - Multi-group epidemic modeling
- **Interactive Dashboards** - Plotly/Dash visualizations
- **GPU Acceleration** - Faster large-scale simulations

### Future Considerations

- Spatial/geographic modeling
- Multiple vaccination strategies
- Real-time data integration
- Uncertainty quantification improvements

## 👥 Contributors

- @julihocc - Project maintainer
- GitHub Copilot - Development assistance

## 📄 License

MIT License - See LICENSE file for details

## 🔗 Links

- **GitHub**: https://github.com/julihocc/dynasir
- **PyPI**: https://pypi.org/project/dynasir/
- **Documentation**: See `docs/` folder and example notebooks
- **Issues**: https://github.com/julihocc/dynasir/issues

## 📧 Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Check example notebooks for usage patterns
- Review CLAUDE.md for development guidelines

---

**Full Changelog**: https://github.com/julihocc/dynasir/blob/main/CHANGELOG.md
