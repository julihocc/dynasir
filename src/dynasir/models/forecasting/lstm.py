"""
LSTM neural network forecasting backend (stub - not yet implemented).

This module provides a placeholder for a future LSTM-based forecasting backend.
The implementation is planned for a future release and will include:
- Multivariate LSTM with attention mechanisms
- Bootstrap-based confidence interval estimation
- GPU acceleration support via TensorFlow/PyTorch
"""

import logging
from typing import Any, Tuple, Union

import numpy as np
import pandas as pd

from .base import BaseForecaster
from .registry import register_forecaster


@register_forecaster("lstm", aliases=["neural_net", "deep_learning", "rnn"])
class LSTMForecaster(BaseForecaster):
    """
    LSTM neural network forecasting backend (NOT YET IMPLEMENTED).

    This is a registered stub for a future LSTM-based forecasting implementation.
    When fully implemented, this backend will provide:

    Planned Features:
        - Multivariate LSTM architecture with attention mechanisms
        - Handles non-linear temporal dependencies
        - Bootstrap or Monte Carlo dropout for uncertainty quantification
        - GPU acceleration for large-scale forecasting
        - Transfer learning from pre-trained epidemic models

    Technical Approach:
        - Sequence-to-sequence architecture with encoder-decoder
        - Attention mechanism for long-term dependencies
        - Dropout layers for uncertainty estimation
        - Early stopping and regularization for generalization

    Use Cases:
        - Complex non-linear epidemic dynamics
        - Long-term forecasts with deep temporal patterns
        - Large datasets where neural networks excel
        - Transfer learning across different regions/diseases

    Current Status:
        🚧 NOT IMPLEMENTED - This is a placeholder for future development

    Examples:
        This backend is registered but will raise NotImplementedError:

        >>> from dynasir import Model, DataContainer
        >>> model = Model(container, forecaster="lstm")  # Will fail
        Traceback (most recent call last):
        NotImplementedError: LSTM backend is not yet implemented...

    Tracking:
        - GitHub Issue: https://github.com/julihocc/dynasir/issues/90
        - Target Release: v0.9.0 or later
        - Planned Dependencies: tensorflow or pytorch, keras (optional)

    Contributing:
        If you're interested in implementing this backend, please see:
        - CONTRIBUTING.md in the repository
        - Open issue #90 for discussion
        - Contact: julihocc@github
    """

    def __init__(self, data: Union[pd.DataFrame, np.ndarray]):
        """
        Initialize LSTM forecaster (stub).

        Args:
            data: Multivariate time series data

        Raises:
            NotImplementedError: Always raised - this backend is not implemented
        """
        super().__init__(data)
        self.n_rates = data.shape[1] if len(data.shape) > 1 else 1

        logging.warning(
            "LSTMForecaster is a stub and not yet implemented. "
            "See https://github.com/julihocc/dynasir/issues/90 for status."
        )

    @property
    def backend_name(self) -> str:
        """Return the canonical name of this backend."""
        return "lstm"

    def create_model(self, **kwargs) -> None:
        """
        Create LSTM model (not implemented).

        Raises:
            NotImplementedError: Always - backend not implemented
        """
        raise NotImplementedError(
            "LSTM backend is not yet implemented. "
            "This feature is planned for a future release (v0.9.0+).\n\n"
            "Planned implementation will include:\n"
            "  - Multivariate LSTM with attention mechanisms\n"
            "  - Bootstrap confidence intervals\n"
            "  - GPU acceleration (TensorFlow/PyTorch)\n\n"
            "Track progress at: https://github.com/julihocc/dynasir/issues/90\n\n"
            "For now, please use one of the available backends:\n"
            "  - 'var' (Vector Autoregression - default)\n"
            "  - 'prophet' (Facebook Prophet)\n"
            "  - 'arima' (Auto-ARIMA)\n\n"
            "Example:\n"
            "  model = Model(container, forecaster='prophet')"
        )

    def fit(self, **kwargs) -> None:
        """
        Fit LSTM model (not implemented).

        Raises:
            NotImplementedError: Always - backend not implemented
        """
        raise NotImplementedError(
            "LSTM backend is not yet implemented. "
            "See create_model() error message for details and alternatives."
        )

    def forecast_interval(
        self, steps: int, **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate forecasts with LSTM (not implemented).

        Args:
            steps: Number of forecast steps
            **kwargs: Additional parameters

        Raises:
            NotImplementedError: Always - backend not implemented
        """
        raise NotImplementedError(
            "LSTM backend is not yet implemented. "
            "See create_model() error message for details and alternatives."
        )
