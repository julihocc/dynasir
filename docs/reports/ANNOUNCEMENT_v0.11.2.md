# DynaSIR v1.0.0 Release Announcement

**Official rename from epydemics to dynasir with publication-ready reporting tools**

We're excited to announce the official **dynasir v1.0.0** release on PyPI. This formalizes the package rename from epydemics to dynasir and carries forward the ModelReport reporting tools introduced in v0.11.x.

## 🎉 What's New

### ModelReport Class (v0.11.x Feature)
Publication-ready analysis and reporting in one line of code:

```python
from dynasir.analysis import ModelReport

# Create comprehensive report
report = ModelReport(model.results, testing_data, compartments=['I', 'D'])

# Export to multiple formats
report.export_markdown("analysis.md", include_figure=True)
report.export_latex_table("table1.tex", "summary")
fig = report.plot_forecast_panel(dpi=600, save_path="forecast.png")
```

**Key Features:**
- Automated summary statistics: Mean, median, std, CV per compartment
- Forecast evaluation: MAE, RMSE, MAPE, SMAPE metrics
- Markdown export: One-line report generation with embedded figures
- LaTeX tables: Publication-quality tables for academic papers
- High-DPI figures: 300-600 DPI multi-panel visualizations
- Model comparison: Compare multiple models side-by-side

### CI/CD Improvements (v1.0.0)
- Pipelines aligned to dynasir package paths and PyPI publishing target
- All tests passing on Python 3.9, 3.10, 3.11, 3.12

## 📦 Installation

```bash
pip install dynasir==1.0.0
```

Or upgrade from previous versions:

```bash
pip install --upgrade dynasir
```

## 📖 Documentation & Examples

- **Complete Tutorial**: [examples/notebooks/07_reporting_and_publication.ipynb](https://github.com/julihocc/dynasir/blob/main/examples/notebooks/07_reporting_and_publication.ipynb)
- **User Guide**: [docs/USER_GUIDE.md](https://github.com/julihocc/dynasir/blob/main/docs/USER_GUIDE.md)
- **Reporting Guide**: [docs/REPORTING_GUIDE.md](https://github.com/julihocc/dynasir/blob/main/docs/REPORTING_GUIDE.md)
- **API Documentation**: Full docstrings in `dynasir.analysis.reporting`

## 🔧 Quick Start

```python
from dynasir import DataContainer, Model
from dynasir.analysis import ModelReport
import pandas as pd

# 1. Prepare data
data = pd.DataFrame({'I': [...], 'D': [...], 'N': [...]}, index=dates)
container = DataContainer(data, mode='cumulative', frequency='D')

# 2. Create and run model
model = Model(container)
model.create_model()
model.fit_model(max_lag=14)
model.forecast(steps=30)
model.run_simulations(n_jobs=None)
model.generate_result()

# 3. Generate publication-ready reports
report = ModelReport(model.results, test_data)
report.export_markdown("covid_analysis.md", include_figure=True)
report.export_latex_table("forecast_metrics.tex", "evaluation")
```

## 🆕 All v1.0.0 Features

- ModelReport class for publication-ready analysis
- Multi-format export: Markdown, LaTeX, PNG (300-600 DPI)
- Automated metrics: Summary stats and forecast accuracy
- Model comparison utilities
- CI/CD aligned to dynasir package namespace
- All v0.10.0+ features: Fractional recovery lag, native multi-frequency, parallel simulations

## 🔗 Links

- **PyPI**: https://pypi.org/project/dynasir/1.0.0/
- **GitHub**: https://github.com/julihocc/dynasir
- **GitHub Release**: https://github.com/julihocc/dynasir/releases/tag/v1.0.0
- **Changelog**: [CHANGELOG.md](https://github.com/julihocc/dynasir/blob/main/CHANGELOG.md)

## 🙏 Feedback

We'd love to hear from you! Please report issues or request features at:
https://github.com/julihocc/dynasir/issues

## 📝 Release Notes

See [CHANGELOG.md](https://github.com/julihocc/dynasir/blob/main/CHANGELOG.md) for detailed release notes and version history.

---

**Happy modeling!** 🎉

*DynaSIR Development Team*
