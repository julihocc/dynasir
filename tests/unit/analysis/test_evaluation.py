"""
Tests for analysis.evaluation module.

Following TDD principles, these tests define the expected behavior
of the evaluation functions for epidemiological models.
"""

import json
import tempfile
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from dynasir.analysis.evaluation import evaluate_forecast, evaluate_model


@pytest.fixture
def sample_results():
    """Sample forecast results structure for testing."""
    dates = pd.date_range("2020-01-01", periods=10, freq="D")

    # Create sample forecast data
    forecast_data = pd.DataFrame(
        {
            "mean": np.random.rand(10) * 100,
            "median": np.random.rand(10) * 100,
            "gmean": np.random.rand(10) * 100,
            "hmean": np.random.rand(10) * 100,
        },
        index=dates,
    )

    results = {
        "C": forecast_data,
        "D": forecast_data.copy() * 0.1,  # Deaths typically lower than cases
        "I": forecast_data.copy() * 0.5,  # Active infections
    }

    return results


@pytest.fixture
def sample_testing_data():
    """Sample testing data for evaluation."""
    dates = pd.date_range("2020-01-01", periods=10, freq="D")

    return pd.DataFrame(
        {
            "C": np.random.rand(10) * 100,
            "D": np.random.rand(10) * 10,
            "I": np.random.rand(10) * 50,
        },
        index=dates,
    )


def test_evaluate_forecast_imports():
    """Test that evaluation functions can be imported."""
    from dynasir.analysis.evaluation import evaluate_forecast, evaluate_model

    assert callable(evaluate_forecast)
    assert callable(evaluate_model)


def test_evaluate_forecast_basic(sample_results, sample_testing_data):
    """Test basic evaluation functionality."""
    evaluation = evaluate_forecast(sample_results, sample_testing_data)

    # Should return a dictionary
    assert isinstance(evaluation, dict)

    # Should have entries for each compartment
    expected_compartments = ("C", "D", "I")
    for compartment in expected_compartments:
        assert compartment in evaluation

    # Each compartment should have metrics for each method
    expected_methods = ["mean", "median", "gmean", "hmean"]
    expected_metrics = ["mae", "mse", "rmse", "mape", "smape"]

    for compartment in expected_compartments:
        assert isinstance(evaluation[compartment], dict)

        for method in expected_methods:
            assert method in evaluation[compartment]
            assert isinstance(evaluation[compartment][method], dict)

            for metric in expected_metrics:
                assert metric in evaluation[compartment][method]
                assert isinstance(evaluation[compartment][method][metric], (int, float))
                assert (
                    evaluation[compartment][method][metric] >= 0
                )  # All metrics should be non-negative


def test_evaluate_forecast_custom_compartments(sample_results, sample_testing_data):
    """Test evaluation with custom compartment selection."""
    compartment_codes = ("C", "D")
    evaluation = evaluate_forecast(
        sample_results, sample_testing_data, compartment_codes=compartment_codes
    )

    # Should only have the specified compartments
    assert set(evaluation.keys()) == set(compartment_codes)
    assert "I" not in evaluation


def test_evaluate_forecast_save_functionality():
    """Test evaluation saving to JSON file."""
    # Create minimal test data
    dates = pd.date_range("2020-01-01", periods=3, freq="D")

    results = {
        "C": pd.DataFrame(
            {
                "mean": [100, 110, 120],
                "median": [95, 105, 115],
                "gmean": [98, 108, 118],
                "hmean": [92, 102, 112],
            },
            index=dates,
        )
    }

    testing_data = pd.DataFrame({"C": [102, 108, 118]}, index=dates)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_filename = f.name[:-5]  # Remove .json extension

    try:
        evaluation = evaluate_forecast(
            results,
            testing_data,
            compartment_codes=("C",),
            save_evaluation=True,
            filename=temp_filename,
        )

        # Check that file was created and contains the evaluation data
        with open(f"{temp_filename}.json", "r") as f:
            saved_data = json.load(f)

        assert saved_data == evaluation

    finally:
        # Clean up
        import os

        try:
            os.unlink(f"{temp_filename}.json")
        except FileNotFoundError:
            pass


def test_evaluate_forecast_auto_filename():
    """Test evaluation with auto-generated filename."""
    dates = pd.date_range("2020-01-01", periods=3, freq="D")

    results = {
        "C": pd.DataFrame(
            {
                "mean": [100, 110, 120],
                "median": [95, 105, 115],
                "gmean": [98, 108, 118],
                "hmean": [92, 102, 112],
            },
            index=dates,
        )
    }

    testing_data = pd.DataFrame({"C": [102, 108, 118]}, index=dates)

    # Mock timestamp to have predictable filename
    with patch("pandas.Timestamp.now") as mock_now:
        mock_now.return_value = pd.Timestamp("2020-01-01 12:00:00")

        with tempfile.TemporaryDirectory() as temp_dir:
            import os

            old_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                evaluation = evaluate_forecast(
                    results,
                    testing_data,
                    compartment_codes=("C",),
                    save_evaluation=True,
                    filename=None,  # Should auto-generate
                )

                # Check that file was created with expected name
                expected_filename = "20200101120000.json"
                assert os.path.exists(expected_filename)

                with open(expected_filename, "r") as f:
                    saved_data = json.load(f)

                assert saved_data == evaluation

            finally:
                os.chdir(old_cwd)


def test_evaluate_model_wrapper(sample_results, sample_testing_data):
    """Test that evaluate_model is a proper wrapper around evaluate_forecast."""
    # Test that it calls evaluate_forecast with the same arguments
    evaluation1 = evaluate_forecast(sample_results, sample_testing_data)
    evaluation2 = evaluate_model(sample_results, sample_testing_data)

    # Results should be identical
    assert evaluation1 == evaluation2


def test_evaluate_forecast_empty_data():
    """Test evaluation with empty data handles gracefully."""
    empty_results = {"C": pd.DataFrame(columns=["mean", "median", "gmean", "hmean"])}
    empty_testing = pd.DataFrame(columns=["C"])

    # Should handle empty data without crashing
    evaluation = evaluate_forecast(
        empty_results, empty_testing, compartment_codes=("C",)
    )
    assert isinstance(evaluation, dict)


def test_evaluate_forecast_metrics_accuracy():
    """Test that evaluation metrics are calculated correctly."""
    # Create simple test data with known expected results
    dates = pd.date_range("2020-01-01", periods=3, freq="D")

    # Perfect prediction (forecast = actual)
    results = {
        "C": pd.DataFrame(
            {
                "mean": [100, 200, 300],
                "median": [100, 200, 300],
                "gmean": [100, 200, 300],
                "hmean": [100, 200, 300],
            },
            index=dates,
        )
    }

    testing_data = pd.DataFrame({"C": [100, 200, 300]}, index=dates)  # Exact match

    evaluation = evaluate_forecast(results, testing_data, compartment_codes=("C",))

    # For perfect predictions, MAE and MSE should be 0
    for method in ["mean", "median", "gmean", "hmean"]:
        assert evaluation["C"][method]["mae"] == pytest.approx(0.0, abs=1e-10)
        assert evaluation["C"][method]["mse"] == pytest.approx(0.0, abs=1e-10)
        assert evaluation["C"][method]["rmse"] == pytest.approx(0.0, abs=1e-10)
        assert evaluation["C"][method]["mape"] == pytest.approx(0.0, abs=1e-10)
        assert evaluation["C"][method]["smape"] == pytest.approx(0.0, abs=1e-10)


def test_numpy_array_conversion():
    """Test that pandas arrays are properly converted to numpy arrays for sklearn."""
    dates = pd.date_range("2020-01-01", periods=3, freq="D")

    # Use extension dtype that might cause issues
    results = {
        "C": pd.DataFrame(
            {
                "mean": pd.array([100.0, 200.0, 300.0], dtype="Float64"),
                "median": [100, 200, 300],
                "gmean": [100, 200, 300],
                "hmean": [100, 200, 300],
            },
            index=dates,
        )
    }

    testing_data = pd.DataFrame(
        {"C": pd.array([102.0, 198.0, 305.0], dtype="Float64")}, index=dates
    )

    # Should not raise type errors
    evaluation = evaluate_forecast(results, testing_data, compartment_codes=("C",))
    assert isinstance(evaluation, dict)
    assert "C" in evaluation


def test_evaluate_forecast_read_only_arrays(sample_results, sample_testing_data):
    """Test evaluation with read-only pandas-backed arrays."""
    for frame in (*sample_results.values(), sample_testing_data):
        for column in frame.columns:
            frame[column].values.setflags(write=False)

    evaluation = evaluate_forecast(sample_results, sample_testing_data)

    assert "C" in evaluation


def test_backward_compatibility_imports():
    """Test that analysis functions maintain backward compatibility."""
    # Should be able to import from analysis module
    from dynasir.analysis import evaluate_forecast, evaluate_model

    assert callable(evaluate_forecast)
    assert callable(evaluate_model)


# SIRDV-specific tests
@pytest.fixture
def sample_sirdv_results():
    """Sample SIRDV forecast results including V compartment."""
    dates = pd.date_range("2020-01-01", periods=10, freq="D")

    # Create sample forecast data
    forecast_data = pd.DataFrame(
        {
            "mean": np.random.rand(10) * 100,
            "median": np.random.rand(10) * 100,
            "gmean": np.random.rand(10) * 100,
            "hmean": np.random.rand(10) * 100,
        },
        index=dates,
    )

    results = {
        "C": forecast_data,
        "D": forecast_data.copy() * 0.1,
        "I": forecast_data.copy() * 0.5,
        "R": forecast_data.copy() * 0.8,
        "S": forecast_data.copy() * 5.0,
        "V": forecast_data.copy() * 2.0,  # Vaccination compartment
        "A": forecast_data.copy() * 5.5,
    }

    return results


@pytest.fixture
def sample_sirdv_testing_data():
    """Sample SIRDV testing data including V compartment."""
    dates = pd.date_range("2020-01-01", periods=10, freq="D")

    return pd.DataFrame(
        {
            "C": np.random.rand(10) * 100,
            "D": np.random.rand(10) * 10,
            "I": np.random.rand(10) * 50,
            "R": np.random.rand(10) * 80,
            "S": np.random.rand(10) * 500,
            "V": np.random.rand(10) * 200,  # Vaccination data
            "A": np.random.rand(10) * 550,
        },
        index=dates,
    )


def test_evaluate_forecast_v_compartment(
    sample_sirdv_results, sample_sirdv_testing_data
):
    """Test evaluation includes V (Vaccinated) compartment."""
    evaluation = evaluate_forecast(
        sample_sirdv_results,
        sample_sirdv_testing_data,
        compartment_codes=("C", "D", "I", "V"),
    )

    assert "V" in evaluation
    assert "mean" in evaluation["V"]
    assert "mae" in evaluation["V"]["mean"]


def test_evaluate_forecast_all_sirdv_compartments(
    sample_sirdv_results, sample_sirdv_testing_data
):
    """Test evaluation works for all SIRDV compartments."""
    compartments = ("S", "I", "R", "D", "V", "C", "A")

    evaluation = evaluate_forecast(
        sample_sirdv_results, sample_sirdv_testing_data, compartment_codes=compartments
    )

    # Should evaluate all requested compartments
    for compartment in compartments:
        assert compartment in evaluation
        assert "mean" in evaluation[compartment]


def test_evaluate_forecast_v_compartment_metrics(
    sample_sirdv_results, sample_sirdv_testing_data
):
    """Test that V compartment evaluation includes all metrics."""
    evaluation = evaluate_forecast(
        sample_sirdv_results,
        sample_sirdv_testing_data,
        compartment_codes=("V",),
    )

    v_metrics = evaluation["V"]["mean"]
    assert "mae" in v_metrics
    assert "mse" in v_metrics
    assert "rmse" in v_metrics
    assert "mape" in v_metrics
    assert "smape" in v_metrics


def test_evaluate_forecast_sirdv_backward_compatibility(
    sample_results, sample_testing_data, sample_sirdv_results, sample_sirdv_testing_data
):
    """Test that SIRDV evaluation doesn't break SIRD functionality."""
    # SIRD evaluation should still work
    sird_eval = evaluate_forecast(
        sample_results, sample_testing_data, compartment_codes=("C", "D", "I")
    )
    assert "C" in sird_eval
    assert "D" in sird_eval
    assert "I" in sird_eval
    assert "V" not in sird_eval

    # SIRDV evaluation should work
    sirdv_eval = evaluate_forecast(
        sample_sirdv_results,
        sample_sirdv_testing_data,
        compartment_codes=("C", "D", "I", "V"),
    )
    assert "C" in sirdv_eval
    assert "D" in sirdv_eval
    assert "I" in sirdv_eval
    assert "V" in sirdv_eval


def test_evaluate_model_v_compartment(sample_sirdv_results, sample_sirdv_testing_data):
    """Test evaluate_model works with V compartment."""
    evaluation = evaluate_model(
        sample_sirdv_results,
        sample_sirdv_testing_data,
        compartment_codes=("C", "V"),
    )

    assert "V" in evaluation
    assert "C" in evaluation
