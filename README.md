# DynaSIR: Forecasting COVID-19 using time series and machine learning

Note: DynaSIR (formerly epydemics) is the canonical package name going forward.

**Version 1.0.0** - Official dynasir release and publication-ready reporting tools

`dynasir` is a Python library for epidemiological modeling and forecasting. It provides tools for creating, fitting, and evaluating discrete SIRD/SIRDV models with time-dependent parameters. The library is designed to be flexible and extensible, allowing users to easily incorporate their own data and models.

**📖 New Users?** Start with the **[User Guide](docs/USER_GUIDE.md)** to understand when and how to use dynasir.

✨ **v1.0.0 Features**: Publication-ready reporting tools with ModelReport class for Markdown, LaTeX, and high-DPI figure export. See [Reporting Guide](docs/REPORTING_GUIDE.md) for complete workflow examples.

## Features

-   **Discrete SIRD Model**: A discrete Susceptible-Infected-Recovered-Deceased (SIRD) model with time-dependent parameters.
-   **SIRDV Vaccination Model** (v0.7.0): Extended model including Vaccinated compartment (V) and vaccination rate (δ).
-   **Time Series Forecasting**: Use of VAR (Vector Autoregression) models to forecast epidemic rates with logit transformation.
-   **Multi-Frequency Support** (v0.9.0): Native processing of daily, business day, weekly, monthly, and annual data with automatic detection and handler-based validation (no artificial reindexing).
-   **Temporal Aggregation** (v0.9.0): Frequency-aware aggregation that skips resampling when source and target frequencies match.
-   **Business Day Support** (v0.9.0): Dedicated handler for trading-day calendars (252 days/year) with validated lags and recovery windows.
-   **Data Container**: A convenient class for loading, preprocessing, and storing epidemiological data.
-   **Scenario Simulations**: 27 scenarios for SIRD, 81 for SIRDV, run sequentially by default, with an optional process pool (`n_jobs`).
-   **Result Caching**: File-based caching to avoid recomputing identical analyses.
-   **Model Evaluation**: Tools for evaluating model performance with MAE, MSE, RMSE, MAPE, SMAPE metrics.
-   **Visualization**: Professional plotting functions for results and forecasts.
-   **Reporting Tools** (v0.11.1): Publication-ready report generation with Markdown, LaTeX, and high-DPI figure exports. See `ModelReport` class and [examples/notebooks/07_reporting_and_publication.ipynb](examples/notebooks/07_reporting_and_publication.ipynb).

> **✅ Native Multi-Frequency**: v0.9.0 processes annual/monthly/weekly/business-day data without artificial daily reindexing. See [User Guide](docs/USER_GUIDE.md#annual-surveillance-data-workaround) for frequency guidance.

## SIRDV Model (New in v0.7.0)

The SIRDV model extends the classical SIRD model by incorporating vaccination:

**Compartments:**
- S: Susceptible
- I: Infected (active cases)
- R: Recovered
- D: Deaths
- V: Vaccinated (new)

**Rates:**
- α: Infection rate
- β: Recovery rate
- γ: Mortality rate
- δ: Vaccination rate (new)

**Key Features:**
- Automatic detection from vaccination data
- 81 simulation scenarios (3⁴ confidence levels)
- Conservation law: N = S + I + R + D + V
- Sequential simulation by default; the 81 scenarios take well under a second

## Quick Start: Reporting

Generate publication-ready reports with one API:

```python
from dynasir import DataContainer, Model
from dynasir.analysis import ModelReport

# Fit model (see Tutorial for full workflow)
container = DataContainer(data, mode='incidence')
model = Model(container)
model.create_model()
model.fit_model(max_lag=3)
model.forecast(steps=10)
model.run_simulations()
model.generate_result()

# Generate comprehensive report
report = ModelReport(model.results, testing_data=test_data)
report.export_markdown("report.md", include_figure=True)
report.export_latex_table("table.tex", "summary")
fig = report.plot_forecast_panel(dpi=600, save_path="forecast.png")
```

**See:** [Reporting Guide](docs/REPORTING_GUIDE.md) | [Notebook Example](examples/notebooks/07_reporting_and_publication.ipynb) | [Script Example](examples/reporting_example.py)

## Getting Started

To get started with `dynasir`, we recommend following the tutorial in [TUTORIAL.md](docs/tutorials/TUTORIAL.md).

## Installation

You can install `dynasir` from PyPI:

```bash
pip install dynasir
```

To install the latest development version, you can clone this repository and install it in editable mode:

```bash
git clone https://github.com/julihocc/dynasir.git
cd dynasir
pip install -e .
```

## Documentation

**User Documentation**:
-   **[User Guide](docs/USER_GUIDE.md)**: Complete guide on when to use dynasir, data preparation, and frequency handling
-   **[Tutorial](docs/tutorials/TUTORIAL.md)**: Step-by-step guide for COVID-19 forecasting
-   **[CHANGELOG.md](docs/CHANGELOG.md)**: Version history and detailed changes
-   **[Quick Reference](docs/QUICK_REFERENCE.md)**: Quick lookup for common workflows

**Developer Documentation**:
-   **[Architecture](docs/architecture/ARCHITECTURE.md)**: High-level architecture overview
-   **[Contributing](docs/CONTRIBUTING.md)**: Contribution guidelines and workflow
-   **[CLAUDE.md](docs/architecture/CLAUDE.md)**: Developer guide for AI assistants
-   **[Documentation Index](docs/INDEX.md)**: Complete documentation organization and navigation

**Release Documentation**:
-   **[v1.0.0 Release Notes](docs/releases/RELEASE_v1.0.0.md)**: Official release with publication-ready reporting
-   **[v0.11.0 Release Notes](docs/releases/RELEASE_NOTES_v0.11.0.md)**: Comprehensive reporting tools
-   **[v0.10.0 Release Notes](docs/releases/RELEASE_NOTES_v0.10.0.md)**: Fractional recovery lag fix
-   **[v0.9.0 Release Notes](docs/releases/RELEASE_NOTES_v0.9.0.md)**: Native multi-frequency support
-   **[Migration Guide](docs/releases/MIGRATION_GUIDE.md)**: Upgrade from v0.8.0 to v0.9.0
-   **[PyPI Publication Guide](docs/releases/PYPI_PUBLICATION_GUIDE.md)**: Publishing to PyPI

## Further work

Recent additions in v0.10.0:
-   ✅ **Fractional Recovery Lag**: Annual frequency now uses 14/365 years (0.0384) instead of 0, fixing LinAlgError with incidence mode
-   ✅ **Annual + Incidence Mode**: Production-ready native support for annual surveillance data with incident cases
-   ✅ **Enhanced Testing**: 10 new tests for fractional lag validation (421/423 tests passing)

Recent additions in v0.9.0:
-   ✅ **Native Multi-Frequency**: Daily, business day, weekly, monthly, annual handlers; no artificial reindexing
-   ✅ **Frequency-Aware Aggregation**: Skip resampling when source and target frequencies match
-   ✅ **Frequency-Aware Seasonality**: Adaptive seasonal detection per frequency
-   ✅ **Business Day Support**: Trading-day defaults (252 days/year, 10-lag VAR, 10-day recovery)

Previous releases (v0.6.1-v0.7.0):
-   ✅ **SIRDV Model Support**: Automatic detection and modeling of vaccination data
-   ✅ **Parallel Simulations**: Multi-core execution for improved performance
-   ✅ **Result Caching**: Optional caching to avoid recomputation
-   ✅ **Enhanced Testing**: Comprehensive test coverage with slow test markers

Future directions (v1.0.0+):

-   **Incidence-First Mode**: Direct modeling of incident cases (not just cumulative)
-   **Importation Modeling**: Handle external case introductions for eliminated diseases
-   **Probabilistic & Scenario Forecasting**: Monte Carlo and intervention comparison workflows
-   **More advanced time series models**: SARIMAX, Prophet, or deep learning approaches
-   **Support for other epidemiological models**: Extend to SEIR, SEIRD, or metapopulation models
-   **Improved visualization**: Interactive dashboards and real-time updating plots

## References

**Allen u.a. 2008** Allen, L.J.S. ; Brauer, F. ; Driessche, P. van den ;
 Bauch, C.T. ; Wu, J. ; Castillo-Chavez, C. ; Earn, D. ; Feng, Z. ;
 Lewis, M.A. ; Li, J. u.a.: Mathematical Epidemiology. Springer Berlin
 Heidelberg, 2008 (Lecture Notes in Mathematics).– URL https://books.
 google.com/books?id=gcP5l1a22rQC.– ISBN 9783540789109

**Andrade u.a. 2021** Andrade, Marinho G. ; Achcar, Jorge A. ; Conce
icc˜ ao, Katiane S. ; Ravishanker, Nalini: Time Series Regression Models
 for COVID-19 Deaths. In: J. Data Sci 19 (2021), Nr. 2, S. 269–292

**Hawas 2020** Hawas, Mohamed: Generated time-series prediction data of
 COVID-19s daily infections in Brazil by using recurrent neural networks. In:
 Data in brief 32 (2020), S. 106175

**Maleki u.a. 2020** Maleki, Mohsen ; Mahmoudi, Mohammad R. ; Wraith,
 Darren ; Pho, Kim-Hung: Time series modelling to forecast the confirmed
 and recovered cases of COVID-19. In: Travel medicine and infectious disease
 37 (2020), S. 101742

**Martcheva 2015** Martcheva, M.: An Introduction to Mathematical Epi
demiology. Springer US, 2015 (Texts in Applied Mathematics).– URL https:
 //books.google.com/books?id=tt7HCgAAQBAJ.– ISBN 9781489976123

**Singh u.a. 2020** Singh, Vijander ; Poonia, Ramesh C. ; Kumar, Sandeep ;
 Dass, Pranav ; Agarwal, Pankaj ; Bhatnagar, Vaibhav ; Raja, Linesh:
 Prediction of COVID-19 coronavirus pandemic based on time series data
 using Support Vector Machine. In: Journal of Discrete Mathematical Sciences
 and Cryptography 23 (2020), Nr. 8, S. 1583–1597

**Wacker und Schluter 2020** Wacker, Benjamin; Schluter, Jan: Time
continuous and time-discrete SIR models revisited: theory and applications.
 In: Advances in Difference Equations 2020 (2020), Nr. 1, S. 1–44.– ISSN
 1687-1847.– URL https://doi.org/10.1186/s13662-020-02907-9