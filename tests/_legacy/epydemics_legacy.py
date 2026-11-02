"""
Epydemics: Epidemiological Forecasting with Time Series Analysis.

This package implements SIRD (Susceptible-Infected-Recovered-Deaths) epidemiological
models with time-varying parameters modeled using VAR (Vector Autoregression) analysis
on logit-transformed rates.

For backward compatibility, the main functionality remains available through:
- process_data_from_owid: Download and process OWID COVID-19 data
- DataContainer: Data preprocessing and feature engineering
- Model: SIRD model with VAR forecasting

New modular imports:
- from dynasir.data import DataContainer
- from dynasir.models import Model
- from dynasir.core.constants import *
"""

import logging
import pandas as pd

from .data.container import DataContainer
from .models.sird import Model
from .core.exceptions import NotDataFrameError

# Configure logging to suppress matplotlib warnings
logging.basicConfig(level=logging.INFO)
logging.getLogger("matplotlib").setLevel(logging.WARNING)


# Import process_data_from_owid for backward compatibility
def process_data_from_owid(
    url="https://covid.ourworldindata.org/data/owid-covid-data.csv", iso_code="OWID_WRL"
):
    """
    Download and process OWID COVID-19 data for epidemiological modeling.

    This function downloads data from Our World in Data (OWID) and processes it
    for use with the epydemics modeling framework. It filters by ISO code,
    selects required columns, and renames them to the internal format.

    Args:
        url: URL to OWID COVID-19 CSV data
        iso_code: ISO country code to filter data (default: "OWID_WRL" for global)

    Returns:
        pd.DataFrame: Processed data with columns [C, D, N] and date index

    Raises:
        Exception: If data download fails
        ValueError: If required columns are missing or date indexing fails
    """
    try:
        data = pd.read_csv(url)
    except Exception as e:
        raise Exception(f"Could not download data from {url}: {e}")

    try:
        data = data[data["iso_code"] == iso_code]
    except Exception as e:
        raise Exception(f"Could not filter data for {iso_code}: {e}")

    try:
        data = data[["date", "total_cases", "total_deaths", "population"]]
    except ValueError:
        raise ValueError("Dataframe has not the required columns")

    try:
        data.set_index("date", inplace=True)
    except ValueError:
        raise ValueError("Date could not be set as index")

    try:
        data.index = pd.DatetimeIndex(data.index)
    except Exception:
        raise Exception("Date could not be set as DatetimeIndex")

    try:
        data.columns = [
            "C",
            "D",
            "N",
        ]
    except ValueError:
        raise ValueError("Columns on reduced dataframe could not be renamed")

    return data


# Export main classes and functions for backward compatibility
__all__ = [
    "DataContainer",
    "Model",
    "NotDataFrameError",
    "process_data_from_owid",
]
