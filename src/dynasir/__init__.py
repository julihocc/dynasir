"""DynaSIR: Hybrid epidemic intelligence for SIRD/SIRDV inverse modeling.

This package provides tools for modeling and analyzing epidemic data using
discrete SIRD/SIRDV models combined with time series analysis.

v1.0.0 Highlights (rename from epydemics):
- Official package name is dynasir on PyPI
- Publication-ready reporting tools (ModelReport class)
- Markdown/LaTeX export and 300-600 DPI figures
- Comprehensive summary statistics and forecast evaluation
- Model comparison utilities
- Fractional recovery lag fix and native multi-frequency support

Version: 1.0.0
"""

import logging

# Import main functionality from modular structure
from .analysis.evaluation import evaluate_forecast, evaluate_model
from .analysis.formatting import (
    add_forecast_highlight,
    format_subplot_grid,
    format_time_axis,
    set_professional_style,
)
from .analysis.visualization import visualize_results
from .core.config import get_settings

# Import specific constants and exceptions to avoid star imports
from .core.constants import (
    CENTRAL_TENDENCY_METHODS,
    COMPARTMENT_LABELS,
    COMPARTMENTS,
    FORECASTING_LEVELS,
    LOGIT_RATIOS,
    METHOD_COLORS,
    METHOD_NAMES,
    RATIOS,
)
from .core.exceptions import (
    DataValidationError,
    DateRangeError,
    DynaSIRError,
    NotDataFrameError,
)
from .data.container import DataContainer, validate_data
from .epydemics import process_data_from_owid
from .models.sird import Model
from .utils.transformations import prepare_for_logit_function

__version__ = "1.0.0"
__author__ = "Juliho David Castillo Colmenares"
__email__ = "juliho.colmenares@gmail.com"

# Configure logging
settings = get_settings()
logging.basicConfig(level=settings.LOG_LEVEL, format=settings.LOG_FORMAT)

# Define __all__ for explicit exports
__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    # Constants
    "RATIOS",
    "LOGIT_RATIOS",
    "COMPARTMENTS",
    "COMPARTMENT_LABELS",
    "FORECASTING_LEVELS",
    "CENTRAL_TENDENCY_METHODS",
    "METHOD_NAMES",
    "METHOD_COLORS",
    # Exceptions
    "DynaSIRError",
    "NotDataFrameError",
    "DataValidationError",
    "DateRangeError",
    # Analysis functions
    "evaluate_forecast",
    "evaluate_model",
    "visualize_results",
    # Formatting utilities
    "format_time_axis",
    "format_subplot_grid",
    "add_forecast_highlight",
    "set_professional_style",
    # Main classes and functions
    "DataContainer",
    "Model",
    "process_data_from_owid",
    "validate_data",
    "prepare_for_logit_function",
]
