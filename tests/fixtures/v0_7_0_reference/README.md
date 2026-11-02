# v0.7.0 Reference Fixtures

This folder stores reference outputs produced by dynasir v0.7.0 for backward compatibility testing.

Populate with small, serialized artifacts (pickled `.pkl` files) representing model results for representative datasets:

- `covid_cumulative_forecast.pkl` — SIRD cumulative workflow (COVID-19)
- `measles_incidence_forecast.pkl` — Incidence workflow (measles, annual frequency)
- Optional: `sirdv_vaccination_forecast.pkl` — SIRDV workflow with vaccination

Each pickle should contain a dict of arrays/DataFrames for key comparables:

```python
{
  "alpha_point": np.ndarray,    # Infection rate point forecast
  "alpha_lower": np.ndarray,    # Lower CI
  "alpha_upper": np.ndarray,    # Upper CI
  "compartments": pd.DataFrame, # S, I, R, D over forecast horizon
  "r0_series": np.ndarray       # R0 values (optional)
}
```

Note: This repository branch does not include the large inputs or generation scripts. Generate fixtures from a clean v0.7.0 checkout and copy the resulting small `.pkl` files here.
