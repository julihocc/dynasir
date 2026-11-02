# Reporting Tools Guide

**Version**: 0.10.0
**Module**: `dynasir.analysis.reporting`

## Overview

The reporting module provides high-level tools for generating publication-ready analysis reports from dynasir model results. It simplifies the process of creating comprehensive reports with summary statistics, evaluation metrics, and professional visualizations.

## Quick Start

```python
from dynasir import DataContainer, Model
from dynasir.analysis import ModelReport

# 1. Fit your model (see Tutorial for details)
container = DataContainer(train_data, mode='incidence')
model = Model(container)
model.create_model()
model.fit_model(max_lag=3)
model.forecast(steps=10)
model.run_simulations(n_jobs=-1)
model.generate_result()

# 2. Create report with testing data for evaluation
report = ModelReport(
    results=model.results,
    testing_data=test_data,
    compartments=['I', 'D'],
    model_name="Measles Forecast - Mexico"
)

# 3. Export everything in one line
report.export_markdown("reports/forecast.md", include_figure=True)
report.export_latex_table("tables/summary.tex", "summary")
fig = report.plot_forecast_panel(dpi=600, save_path="figures/forecast.png")
```

**Complete working examples:**
- [07_reporting_and_publication.ipynb](../examples/notebooks/07_reporting_and_publication.ipynb): Comprehensive notebook walkthrough
- [reporting_example.py](../examples/reporting_example.py): Standalone Python script

## Features

### 1. ModelReport Class

The `ModelReport` class provides a convenient interface for analyzing and reporting model results.

#### Create a Report

```python
from dynasir.analysis import ModelReport

report = ModelReport(
    results=model.results,          # Model results dictionary
    testing_data=test_df,            # Optional test data for evaluation
    compartments=['C', 'D'],         # Compartments to include
    model_name="My Epidemic Model"   # Name for report headers
)
```

#### Generate Summary Statistics

```python
# Get summary as DataFrame
summary_df = report.generate_summary()
print(summary_df)

# Output:
# | Compartment | Code | Mean    | Median  | Std Dev | Min   | Max    | Range  | CV (%) |
# |-------------|------|---------|---------|---------|-------|--------|--------|--------|
# | Confirmed   | C    | 1234.5  | 1200.3  | 456.7   | 500.0 | 2500.0 | 2000.0 | 37.0   |
# | Deaths      | D    | 45.2    | 42.1    | 15.3    | 20.0  | 85.0   | 65.0   | 33.8   |
```

#### Evaluate Forecast Accuracy

```python
# Requires testing_data to be provided
eval_df = report.get_evaluation_summary()
print(eval_df)

# Output:
# | Compartment | Method | MAE    | RMSE   | MAPE (%) | SMAPE (%) |
# |-------------|--------|--------|--------|----------|-----------|
# | Confirmed   | Mean   | 123.4  | 156.7  | 10.2     | 9.8       |
# | Deaths      | Mean   | 5.6    | 7.2    | 12.5     | 11.9      |
```

#### Create Multi-Panel Visualizations

```python
# Create publication-quality figure with all compartments
fig = report.plot_forecast_panel(
    figsize=(15, 10),
    save_path="figures/forecast_panel.png",
    dpi=300
)
```

#### Export Reports

**Markdown Export** (for GitHub, documentation, etc.):
```python
report.export_markdown(
    filepath="reports/forecast_report.md",
    include_summary=True,
    include_evaluation=True,
    include_figure=True
)
```

**LaTeX Tables** (for academic publications):
```python
# Summary statistics table
report.export_latex_table(
    filepath="tables/summary.tex",
    table_type="summary"
)

# Evaluation metrics table
report.export_latex_table(
    filepath="tables/evaluation.tex",
    table_type="evaluation"
)
```

### 2. Model Comparison

Compare multiple models or scenarios side-by-side:

```python
from dynasir.analysis import create_comparison_report

models = {
    "Baseline": baseline_model.results,
    "With Intervention": intervention_model.results,
    "High Vaccination": vaccine_model.results
}

fig = create_comparison_report(
    models=models,
    testing_data=test_data,
    compartment='C',
    save_path="figures/model_comparison.png"
)
```

## Complete Example

```python
import pandas as pd
from dynasir import DataContainer, Model
from dynasir.analysis import ModelReport

# 1. Prepare data
data = pd.read_csv("measles_data.csv", index_col=0, parse_dates=True)
train = data.iloc[:30]
test = data.iloc[30:]

# 2. Create and run model
container = DataContainer(train, mode='incidence')
model = Model(container)
model.create_model()
model.fit_model(max_lag=3)
model.forecast(steps=10)
model.run_simulations(n_jobs=-1)
model.generate_result()

# 3. Create comprehensive report
report = ModelReport(
    results=model.results,
    testing_data=test,
    compartments=['I', 'D'],
    model_name="Measles Forecast - Mexico"
)

# 4. Export everything
from pathlib import Path
output_dir = Path("publications/measles_2024")
output_dir.mkdir(parents=True, exist_ok=True)

# Markdown report for documentation
report.export_markdown(
    filepath=output_dir / "forecast_report.md",
    include_summary=True,
    include_evaluation=True,
    include_figure=True
)

# LaTeX tables for paper
report.export_latex_table(
    filepath=output_dir / "table1_summary.tex",
    table_type="summary"
)
report.export_latex_table(
    filepath=output_dir / "table2_evaluation.tex",
    table_type="evaluation"
)

# High-res figure for paper
fig = report.plot_forecast_panel(
    figsize=(14, 10),
    save_path=output_dir / "figure1_forecast.png",
    dpi=600  # Publication quality
)

print(f"✅ Reports generated in {output_dir}")
```

## Use Cases

### Academic Publications

1. **Generate LaTeX tables** for your manuscript
2. **Create high-DPI figures** (600+ DPI) for submission
3. **Export summary statistics** in standardized format
4. **Compare models** with side-by-side visualizations

### Reports & Presentations

1. **Markdown reports** for GitHub/internal documentation
2. **Multi-panel figures** for presentations
3. **Evaluation summaries** for stakeholders
4. **Model comparisons** for decision support

### Reproducible Research

1. **Automated report generation** from model results
2. **Consistent formatting** across analyses
3. **Version-controlled outputs** (Markdown + code)
4. **Publication-ready artifacts** with single function call

## Best Practices

### For Publications

```python
# Use high DPI for submission
report.plot_forecast_panel(
    figsize=(14, 10),
    save_path="manuscript/figure1.png",
    dpi=600
)

# Generate LaTeX tables
report.export_latex_table("manuscript/table1.tex", "summary")
report.export_latex_table("manuscript/table2.tex", "evaluation")
```

### For Documentation

```python
# Markdown format for GitHub/documentation sites
report.export_markdown(
    filepath="docs/analysis_report.md",
    include_summary=True,
    include_evaluation=True,
    include_figure=True
)
```

### For Presentations

```python
# Lower DPI, larger fonts
report.plot_forecast_panel(
    figsize=(12, 8),
    save_path="presentation/slide_forecast.png",
    dpi=150
)
```

## API Reference

### ModelReport

**Constructor**:
- `results`: Model results dictionary
- `testing_data`: Optional test data for evaluation
- `compartments`: List of compartments to include
- `model_name`: Name for report headers

**Methods**:
- `generate_summary()`: Get summary statistics DataFrame
- `evaluate()`: Compute forecast accuracy metrics
- `get_evaluation_summary()`: Get evaluation metrics DataFrame
- `plot_forecast_panel()`: Create multi-panel visualization
- `export_markdown()`: Export Markdown report
- `export_latex_table()`: Export LaTeX table

### create_comparison_report

**Parameters**:
- `models`: Dict mapping model names to results
- `testing_data`: Optional test data
- `compartment`: Compartment to compare
- `save_path`: Path to save figure

**Returns**: Matplotlib Figure object

## Examples

See:
- `examples/reporting_example.py` - Complete demonstration
- `examples/reports/` - Sample output files
- `examples/notebooks/` - Interactive examples

## Requirements

The reporting module requires:
- `matplotlib` (visualization)
- `pandas` (data handling)
- `numpy` (computations)
- `tabulate` (Markdown table formatting)

All dependencies are automatically installed with dynasir.

## Tips

1. **Use descriptive model names** - They appear in report headers
2. **Provide testing data** - Enables evaluation metrics
3. **Set appropriate DPI** - 300 for screen, 600+ for print
4. **Organize outputs** - Use separate directories for different projects
5. **Version control reports** - Markdown reports work great with git

## See Also

- [Visualization Guide](VISUALIZATION_GUIDE.md)
- [Evaluation Metrics](EVALUATION_GUIDE.md)
- [API Documentation](API_AUDIT.md)
