"""
Backward compatibility tests: Ensure v0.8.0+ behavior matches v0.7.0 defaults.

These tests are structured to compare current outputs against reference
fixtures generated from dynasir v0.7.0. When fixtures are missing, tests
will be skipped to keep CI passing until fixtures are populated.

Usage:
    - Place v0.7.0 reference .pkl files under
      tests/fixtures/v0_7_0_reference/
    - Run `pytest -k backward_compatibility`

"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
import pytest

from dynasir.models.sird import Model

# Tolerances for backward compatibility tests – adjust if needed after fixture generation
POINT_ATOL = 1e-6
POINT_RTOL = 1e-5
CI_ATOL = 1e-5
CI_RTOL = 1e-4

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "v0_7_0_reference"


def _load_pickle(path: Path) -> Dict[str, Any]:
    with path.open("rb") as f:
        return pickle.load(f)


def _assert_arrays_close(
    a: np.ndarray, b: np.ndarray, *, atol: float, rtol: float
) -> None:
    assert a.shape == b.shape, "Shapes differ"
    assert np.allclose(a, b, atol=atol, rtol=rtol), "Arrays differ beyond tolerance"


def _assert_dataframes_equal(df1: pd.DataFrame, df2: pd.DataFrame) -> None:
    assert list(df1.columns) == list(df2.columns), "Column sets differ"
    assert len(df1) == len(df2), "Row counts differ"
    # Compare numeric values strictly for compartments
    pd.testing.assert_frame_equal(
        df1.reset_index(drop=True), df2.reset_index(drop=True), check_dtype=False
    )


@pytest.mark.skipif(
    not (FIXTURE_DIR / "covid_cumulative_forecast.pkl").exists(),
    reason="v0.7.0 COVID fixture missing",
)
def test_forecast_equivalence_covid_reference_only() -> None:
    """
    Smoke test that verifies the reference fixture structure is usable.
    Once generation and current-run comparison are implemented, this will
    compare current outputs against the reference.
    """
    ref = _load_pickle(FIXTURE_DIR / "covid_cumulative_forecast.pkl")

    # Sanity checks on reference content
    assert {"alpha_point", "alpha_lower", "alpha_upper", "compartments"}.issubset(
        ref.keys()
    )
    assert isinstance(ref["alpha_point"], np.ndarray)
    assert isinstance(ref["alpha_lower"], np.ndarray)
    assert isinstance(ref["alpha_upper"], np.ndarray)
    assert isinstance(ref["compartments"], pd.DataFrame)


@pytest.mark.skipif(
    not (FIXTURE_DIR / "covid_cumulative_forecast.pkl").exists(),
    reason="v0.7.0 COVID fixture missing",
)
def test_forecast_equivalence_covid_current_vs_reference(sample_data_container) -> None:
    """Compare current VAR forecast to v0.7.0 reference on the same data."""
    ref = _load_pickle(FIXTURE_DIR / "covid_cumulative_forecast.pkl")

    steps = int(np.asarray(ref["alpha_point"]).shape[0])

    # Run current model with defaults (VAR backend)
    model = Model(sample_data_container)
    model.create_model()
    model.fit_model(max_lag=3)
    model.forecast(steps=steps)

    alpha_point = np.asarray(model.forecasting_box["alpha"]["point"])
    alpha_lower = np.asarray(model.forecasting_box["alpha"]["lower"])
    alpha_upper = np.asarray(model.forecasting_box["alpha"]["upper"])

    _assert_arrays_close(
        alpha_point, ref["alpha_point"], atol=POINT_ATOL, rtol=POINT_RTOL
    )
    _assert_arrays_close(
        alpha_lower, np.asarray(ref["alpha_lower"]), atol=CI_ATOL, rtol=CI_RTOL
    )
    _assert_arrays_close(
        alpha_upper, np.asarray(ref["alpha_upper"]), atol=CI_ATOL, rtol=CI_RTOL
    )


@pytest.mark.skipif(
    not (FIXTURE_DIR / "measles_incidence_forecast.pkl").exists(),
    reason="v0.7.0 measles fixture missing",
)
def test_forecast_equivalence_measles_reference_only() -> None:
    ref = _load_pickle(FIXTURE_DIR / "measles_incidence_forecast.pkl")

    assert {"alpha_point", "alpha_lower", "alpha_upper", "compartments"}.issubset(
        ref.keys()
    )
    assert isinstance(ref["alpha_point"], np.ndarray)
    assert isinstance(ref["alpha_lower"], np.ndarray)
    assert isinstance(ref["alpha_upper"], np.ndarray)
    assert isinstance(ref["compartments"], pd.DataFrame)


@pytest.mark.skipif(
    not (FIXTURE_DIR / "annual_cumulative_forecast.pkl").exists(),
    reason="v0.7.0 annual cumulative fixture missing",
)
def test_forecast_equivalence_annual_current_vs_reference(
    sample_annual_data_container,
) -> None:
    """Annual cumulative data: compare current model to v0.7.0 reference."""
    ref = _load_pickle(FIXTURE_DIR / "annual_cumulative_forecast.pkl")

    steps = int(np.asarray(ref["alpha_point"]).shape[0])

    model = Model(sample_annual_data_container)
    model.create_model()
    model.fit_model(max_lag=3)
    model.forecast(steps=steps)

    alpha_point = np.asarray(model.forecasting_box["alpha"]["point"])
    alpha_lower = np.asarray(model.forecasting_box["alpha"]["lower"])
    alpha_upper = np.asarray(model.forecasting_box["alpha"]["upper"])

    _assert_arrays_close(
        alpha_point, np.asarray(ref["alpha_point"]), atol=POINT_ATOL, rtol=POINT_RTOL
    )
    _assert_arrays_close(
        alpha_lower, np.asarray(ref["alpha_lower"]), atol=CI_ATOL, rtol=CI_RTOL
    )
    _assert_arrays_close(
        alpha_upper, np.asarray(ref["alpha_upper"]), atol=CI_ATOL, rtol=CI_RTOL
    )


# Future: Add tests that run current Model on identical data and compare
# against reference fixtures using the helpers above. For now, we validate
# fixture structure and skip if not present.
