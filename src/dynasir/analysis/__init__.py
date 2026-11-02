"""
Analysis module for DynaSIR package.

This module provides visualization and evaluation functionality
for epidemiological models and forecasts.

Modules:
    visualization: Functions for plotting and visualizing epidemic data and forecasts
    evaluation: Metrics and evaluation functions for model performance assessment
    formatting: Utilities for professional plot formatting and styling
"""

from .evaluation import evaluate_forecast, evaluate_model
from .formatting import (
    add_forecast_highlight,
    format_subplot_grid,
    format_time_axis,
    set_professional_style,
)
from .reporting import ModelReport, create_comparison_report
from .visualization import visualize_results

__all__ = [
    "evaluate_forecast",
    "evaluate_model",
    "visualize_results",
    "format_time_axis",
    "format_subplot_grid",
    "add_forecast_highlight",
    "set_professional_style",
    "ModelReport",
    "create_comparison_report",
]
