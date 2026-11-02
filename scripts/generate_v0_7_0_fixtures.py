"""
Generate v0.7.0 reference fixtures for backward compatibility tests.

IMPORTANT: Run this script in a clean environment where epydemics==0.7.0
is installed. The outputs should be copied into:
  tests/fixtures/v0_7_0_reference/

This script uses deterministic sample datasets that mirror the test
fixtures in tests/conftest.py to ensure identical inputs.

Outputs:
  - covid_cumulative_forecast.pkl
  - annual_cumulative_forecast.pkl
  (Optional) measles_incidence_forecast.pkl if incidence data is prepared

Each pickle contains a dict with keys:
  {"alpha_point", "alpha_lower", "alpha_upper", "compartments"}

"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd


def make_covid_cumulative_data() -> pd.DataFrame:
    dates = pd.date_range(start="2020-03-01", end="2020-03-31", freq="D")
    np.random.seed(42)
    C = np.cumsum(np.random.exponential(50, len(dates)))
    D = np.cumsum(np.random.exponential(2, len(dates)))
    N = np.full(len(dates), 1_000_000)
    return pd.DataFrame({"C": C, "D": D, "N": N}, index=dates)


def make_annual_cumulative_data() -> pd.DataFrame:
    dates = pd.date_range(start="2015", periods=10, freq="YE")
    np.random.seed(42)
    C = np.cumsum(np.random.exponential(200, len(dates)))
    D = np.cumsum(np.random.exponential(5, len(dates)))
    N = np.full(len(dates), 300_000_000)
    return pd.DataFrame({"C": C, "D": D, "N": N}, index=dates)


def run_model_and_export(df: pd.DataFrame, steps: int) -> Dict[str, Any]:
    # NOTE: Import epydemics from v0.7.0 environment
    from dynasir.data.container import DataContainer
    from dynasir.models.sird import Model

    container = DataContainer(df)
    model = Model(container)
    model.create_model()
    model.fit_model(max_lag=3)
    model.forecast(steps=steps)

    # Optional: include compartments from results if available
    try:
        model.run_simulations(n_jobs=1)
        model.generate_result()
        compartments = model.results.get("compartments", None)
    except Exception:
        compartments = None

    out = {
        "alpha_point": np.asarray(model.forecasting_box.alpha.point),
        "alpha_lower": np.asarray(model.forecasting_box.alpha.lower),
        "alpha_upper": np.asarray(model.forecasting_box.alpha.upper),
    }
    if compartments is not None:
        out["compartments"] = compartments
    else:
        # Fallback to empty DataFrame to satisfy structure
        out["compartments"] = pd.DataFrame()
    return out


def main() -> None:
    target = Path("tests/fixtures/v0_7_0_reference")
    target.mkdir(parents=True, exist_ok=True)

    covid_df = make_covid_cumulative_data()
    covid_ref = run_model_and_export(covid_df, steps=10)
    with (target / "covid_cumulative_forecast.pkl").open("wb") as f:
        pickle.dump(covid_ref, f)

    annual_df = make_annual_cumulative_data()
    annual_ref = run_model_and_export(annual_df, steps=5)
    with (target / "annual_cumulative_forecast.pkl").open("wb") as f:
        pickle.dump(annual_ref, f)

    print("Generated fixtures in", target)


if __name__ == "__main__":
    main()
