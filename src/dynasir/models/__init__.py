"""
Epidemiological modeling module.

This module provides epidemiological modeling implementations including:
- BaseModel: Abstract base class for epidemiological models
- Model: SIRD model with VAR time series forecasting
- Simulation engines and forecasting utilities
"""

from . import simulation, var_forecasting
from .base import BaseModel, SIRDModelMixin
from .sird import Model

__all__ = [
    "BaseModel",
    "SIRDModelMixin",
    "Model",
    "var_forecasting",
    "simulation",
]
