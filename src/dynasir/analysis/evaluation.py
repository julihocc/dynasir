"""
Evaluation metrics for epidemiological models and forecasts.

This module provides functions to evaluate the performance of epidemiological
models against test data using various statistical metrics.
"""

import json
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from ..core.constants import CENTRAL_TENDENCY_METHODS


def evaluate_forecast(
    results: Dict[str, Any],
    testing_data: pd.DataFrame,
    compartment_codes: Tuple[str, ...] = ("C", "D", "I"),
    save_evaluation: bool = False,
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluate forecast performance against test data.

    Args:
        results: Dictionary containing forecast results for each compartment
        testing_data: DataFrame with actual values for comparison
        compartment_codes: Tuple of compartment codes to evaluate
        save_evaluation: Whether to save results to JSON file
        filename: Optional filename for saving (auto-generated if None)

    Returns:
        Dictionary with evaluation metrics for each compartment and method
    """
    evaluation = {}

    for compartment_code in compartment_codes:
        compartment = results[compartment_code]
        evaluation[compartment_code] = {}

        for method in CENTRAL_TENDENCY_METHODS:
            forecast = np.array(compartment[method].values, copy=True)
            actual = np.array(testing_data[compartment_code].values, copy=True)

            # Replace NaN or inf with 0
            if forecast.size > 0:
                forecast[~np.isfinite(forecast)] = 0
            if actual.size > 0:
                actual[~np.isfinite(actual)] = 0

            if actual.size == 0 and forecast.size == 0:
                mae, mse, rmse, mape, smape = 0, 0, 0, 0, 0
            else:
                mae = mean_absolute_error(actual, forecast)
                mse = mean_squared_error(actual, forecast)
                rmse = np.sqrt(mse)
                mape = np.mean(np.abs((actual - forecast) / actual)) * 100
                smape = np.mean(np.abs((actual - forecast) / (actual + forecast))) * 100

            evaluation[compartment_code][method] = {
                "mae": mae,
                "mse": mse,
                "rmse": rmse,
                "mape": mape,
                "smape": smape,
            }

    if save_evaluation:
        if filename is None:
            now = pd.Timestamp.now()
            filename = now.strftime("%Y%m%d%H%M%S")
        with open(f"{filename}.json", "w") as f:
            json.dump(evaluation, f)

    return evaluation


def evaluate_model(
    results: Dict[str, Any], testing_data: pd.DataFrame, **kwargs
) -> Dict[str, Any]:
    """
    Evaluate model performance against test data.

    This is a convenience wrapper around evaluate_forecast.

    Args:
        results: Dictionary containing forecast results for each compartment
        testing_data: DataFrame with actual values for comparison
        **kwargs: Additional keyword arguments passed to evaluate_forecast

    Returns:
        Dictionary with evaluation metrics for each compartment and method
    """
    return evaluate_forecast(results, testing_data, **kwargs)
