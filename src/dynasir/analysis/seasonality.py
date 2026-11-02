"""
Frequency-aware seasonal pattern detection for epidemiological data.

This module detects seasonal patterns in epidemic data and provides
recommendations for seasonal parameters based on data frequency.
Seasonality detection is frequency-sensitive: annual data has limited
patterns, while daily/weekly data can have multiple nested frequencies.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import signal

logger = logging.getLogger(__name__)


class SeasonalPatternDetector:
    """
    Detects seasonal patterns in epidemiological time series.

    Behavior adapts to data frequency:
    - Annual (YE): No seasonality detection (single period per year)
    - Monthly (ME): Detects annual seasonality (~12 months)
    - Weekly (W): Detects annual + sub-annual (~52 weeks, school year)
    - Daily (D): Detects multiple: annual, semi-annual, quarterly, monthly, weekly
    """

    def __init__(self, min_periods: int = 2):
        """
        Initialize detector.

        Args:
            min_periods: Minimum observations required for detection (default 2)
        """
        self.min_periods = min_periods
        self.patterns: Dict[str, Dict] = {}

    def detect(
        self,
        data: pd.DataFrame,
        frequency: Optional[str] = None,
        compartments: Optional[List[str]] = None,
        significance_level: float = 0.05,
    ) -> Dict[str, Dict]:
        """
        Detect seasonal patterns in data.

        Args:
            data: Time-indexed DataFrame with epidemiological compartments
            frequency: Data frequency ('D', 'W', 'ME', 'YE'). If None, inferred.
            compartments: List of columns to analyze. If None, all numeric columns.
            significance_level: p-value threshold for significance (default 0.05)

        Returns:
            Dict mapping compartment → seasonal pattern info:
            {
                'C': {
                    'frequency': 'D',
                    'has_annual': True,
                    'annual_strength': 0.45,
                    'has_weekly': True,
                    'weekly_strength': 0.32,
                    'periods': [7, 365],
                    'recommended_arima_m': 7,
                    'recommended_prophet_periods': [365, 7]
                }
            }
        """
        if len(data) < self.min_periods:
            logger.warning(
                f"Data too short ({len(data)} obs); skipping seasonality detection"
            )
            return {}

        # Auto-detect frequency if needed
        from dynasir.data.preprocessing import detect_frequency

        if frequency is None:
            try:
                frequency = detect_frequency(data)
            except ValueError:
                logger.warning("Could not infer frequency; defaulting to daily")
                frequency = "D"

        # Determine which compartments to analyze
        if compartments is None:
            compartments = data.select_dtypes(include=[np.number]).columns.tolist()

        results = {}
        for compartment in compartments:
            if compartment not in data.columns:
                logger.warning(f"Compartment {compartment} not found; skipping")
                continue

            series = data[compartment].dropna()
            if len(series) < self.min_periods:
                logger.warning(f"{compartment}: insufficient data ({len(series)} obs)")
                results[compartment] = {
                    "frequency": frequency,
                    "has_seasonality": False,
                    "reason": f"insufficient data ({len(series)} obs)",
                }
                continue

            result = self._detect_compartment(series, frequency, significance_level)
            results[compartment] = result

        self.patterns = results
        return results

    def _detect_compartment(
        self,
        series: pd.Series,
        frequency: str,
        significance_level: float,
    ) -> Dict:
        """Detect seasonality for a single compartment."""
        freq_info = self._get_frequency_info(frequency)
        result = {
            "frequency": frequency,
            "frequency_name": freq_info["name"],
            "has_seasonality": False,
            "periods": [],
            "strengths": {},
        }

        # Annual data: no seasonality detection
        if frequency == "YE":
            result["reason"] = "Annual data (1 obs/year); no seasonality"
            return result

        # Detrend series (remove long-term trend)
        detrended = self._detrend(series)

        # Detect candidate periods based on frequency
        candidate_periods = freq_info["candidate_periods"]

        detected_periods = []
        for period in candidate_periods:
            if period >= len(detrended) / 2:
                continue  # Need at least 2 cycles

            # Test for periodicity using autocorrelation
            strength = self._test_periodicity(detrended, period)
            # Adaptive threshold: lower for longer periods (annual) due to fewer cycles
            threshold = 0.2 if period > len(detrended) / 4 else 0.3
            if strength > threshold:
                detected_periods.append(period)
                result["strengths"][f"period_{period}"] = strength
                logger.debug(f"  Detected period {period} (strength={strength:.2f})")

        if detected_periods:
            result["has_seasonality"] = True
            result["periods"] = sorted(detected_periods)
            result["recommended_arima_m"] = detected_periods[0]
            result["recommended_prophet_periods"] = detected_periods
        else:
            result["reason"] = "No significant periodicity detected"

        return result

    def _get_frequency_info(self, frequency: str) -> Dict:
        """Get frequency-specific information."""
        freq_info = {
            "D": {
                "name": "Daily",
                "periods_per_year": 365.25,
                "candidate_periods": [7, 14, 30, 91, 182, 365],  # W, 2W, M, Q, SA, Y
            },
            "W": {
                "name": "Weekly",
                "periods_per_year": 52.14,
                "candidate_periods": [4, 13, 26, 52],  # M, Q, SA, Y
            },
            "ME": {
                "name": "Monthly",
                "periods_per_year": 12,
                "candidate_periods": [3, 6, 12],  # Q, SA, Y
            },
            "YE": {
                "name": "Annual",
                "periods_per_year": 1,
                "candidate_periods": [],  # No seasonality
            },
        }
        return freq_info.get(
            frequency,
            {"name": "Unknown", "periods_per_year": 1, "candidate_periods": []},
        )

    def _detrend(self, series: pd.Series) -> np.ndarray:
        """Remove linear trend from series."""
        x = np.arange(len(series))
        coeffs = np.polyfit(x, series.values, 1)
        trend = np.polyval(coeffs, x)
        return series.values - trend

    def _test_periodicity(self, series: np.ndarray, period: int) -> float:
        """
        Test for periodicity using autocorrelation at lag = period.

        Returns:
            Autocorrelation strength (0 to 1)
        """
        if len(series) < period + 1:
            return 0.0

        # Calculate autocorrelation at specific lag
        lag_values = series[:-period]
        lead_values = series[period:]

        # Pearson correlation
        if np.std(lag_values) == 0 or np.std(lead_values) == 0:
            return 0.0

        correlation = np.corrcoef(lag_values, lead_values)[0, 1]
        return max(0.0, correlation)  # Return non-negative strength

    def get_summary(self) -> str:
        """Return human-readable summary of detected patterns."""
        if not self.patterns:
            return "No patterns detected (run detect() first)"

        lines = ["Seasonal Pattern Summary:"]
        for compartment, info in self.patterns.items():
            lines.append(f"\n{compartment} ({info.get('frequency_name', 'Unknown')})")

            if info.get("has_seasonality"):
                periods_str = ", ".join(str(p) for p in info["periods"])
                lines.append(f"  Periods: {periods_str}")

                for period, strength in info.get("strengths", {}).items():
                    lines.append(f"  {period}: {strength:.3f}")
            else:
                reason = info.get("reason", "Unknown")
                lines.append(f"  No seasonality: {reason}")

        return "\n".join(lines)


def get_seasonal_parameters(
    data_container,
    compartments: Optional[List[str]] = None,
) -> Dict[str, Dict]:
    """
    Convenience function to detect seasonality and return parameters
    for forecasting backends.

    Args:
        data_container: DataContainer with frequency and data
        compartments: Compartments to analyze

    Returns:
        Dict of seasonal parameters keyed by compartment

    Example:
        >>> params = get_seasonal_parameters(container, compartments=['C'])
        >>> params['C']['has_seasonality']  # True/False
        >>> params['C']['recommended_arima_m']  # ARIMA seasonal period
    """
    detector = SeasonalPatternDetector()

    frequency = getattr(data_container, "frequency", None)

    return detector.detect(
        data_container.data,
        frequency=frequency,
        compartments=compartments,
    )
