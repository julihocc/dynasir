"""
Data processing and container modules for DynaSIR.

This module provides data handling functionality including:
- DataContainer: Main data preprocessing and feature engineering class
- Data validation utilities
- Preprocessing functions for epidemiological data
- Feature engineering for SIRD model components
"""

from .container import (
    DataContainer,
    feature_engineering,
    preprocess_data,
    validate_data,
)

__all__ = [
    "DataContainer",
    "validate_data",
    "preprocess_data",
    "feature_engineering",
]
