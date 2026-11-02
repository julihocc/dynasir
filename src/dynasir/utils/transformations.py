"""Transformation functions for epidemiological data."""

import logging

import numpy as np
import pandas as pd

from ..core.constants import LOGIT_RATIOS


def prepare_for_logit_function(data: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare data for logit transformation by ensuring ratios are in (0,1) bounds.

    Args:
        data: DataFrame containing alpha, beta, gamma columns

    Returns:
        DataFrame with ratios bounded and missing values forward/backward filled
    """
    logging.debug(f"Filtering data for {LOGIT_RATIOS}")
    logging.debug(f"alpha min:{data['alpha'].min()} max:{data['alpha'].max()}")
    logging.debug(f"beta min:{data['beta'].min()} max:{data['beta'].max()}")
    logging.debug(f"gamma min:{data['gamma'].min()} max:{data['gamma'].max()}")

    for placeholder in ["alpha", "beta", "gamma"]:
        series = data[placeholder]
        series = series.mask(series <= 0, np.nan)
        series = series.mask(series >= 1, np.nan)
        data[placeholder] = series
        data[placeholder] = data[placeholder].ffill().bfill()

    return data


def logit_function(x: pd.Series) -> pd.Series:
    """
    Apply logit transformation: log(x / (1 - x)).

    Args:
        x: Series of values in (0,1)

    Returns:
        Logit-transformed series
    """
    return np.log(x / (1 - x))


def logistic_function(x: pd.Series) -> pd.Series:
    """
    Apply logistic (inverse logit) transformation: 1 / (1 + exp(-x)).

    Args:
        x: Series of logit values

    Returns:
        Values transformed back to (0,1) range
    """
    return 1 / (1 + np.exp(-x))


def add_logit_ratios(data: pd.DataFrame) -> pd.DataFrame:
    """
    Add logit-transformed ratio columns to the data.

    Args:
        data: DataFrame with alpha, beta, gamma columns

    Returns:
        DataFrame with additional logit_alpha, logit_beta, logit_gamma columns
    """
    data.loc[:, "logit_alpha"] = logit_function(data["alpha"])
    data.loc[:, "logit_beta"] = logit_function(data["beta"])
    data.loc[:, "logit_gamma"] = logit_function(data["gamma"])
    return data
