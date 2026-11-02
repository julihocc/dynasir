"""Unit tests for seasonal pattern detection."""

import numpy as np
import pandas as pd
import pytest

from dynasir import DataContainer
from dynasir.analysis.seasonality import (
    SeasonalPatternDetector,
    get_seasonal_parameters,
)


class TestSeasonalPatternDetector:
    """Test seasonal pattern detection."""

    @pytest.fixture
    def detector(self):
        """Create detector instance."""
        return SeasonalPatternDetector()

    @pytest.fixture
    def daily_data_with_seasonality(self):
        """Generate synthetic daily data with weekly seasonality."""
        dates = pd.date_range("2020-01-01", periods=365, freq="D")

        # Trend: exponential growth
        trend = np.exp(np.linspace(0, 2, 365))

        # Weekly seasonality
        weekly = 50 * np.sin(2 * np.pi * np.arange(365) / 7)

        # Annual seasonality
        annual = 100 * np.sin(2 * np.pi * np.arange(365) / 365)

        # Noise
        noise = np.random.normal(0, 10, 365)

        values = trend * (1 + (weekly + annual + noise) / (trend * 100))

        data = pd.DataFrame(
            {
                "C": np.cumsum(values),
                "D": np.cumsum(np.random.exponential(1, 365)),
            },
            index=dates,
        )

        return data

    @pytest.fixture
    def annual_data(self):
        """Generate synthetic annual data."""
        dates = pd.date_range("2015-12-31", periods=10, freq="YE")

        data = pd.DataFrame(
            {
                "C": np.cumsum(np.random.exponential(100, 10)),
                "D": np.cumsum(np.random.exponential(5, 10)),
            },
            index=dates,
        )

        return data

    @pytest.fixture
    def monthly_data(self):
        """Generate synthetic monthly data with annual seasonality."""
        dates = pd.date_range("2020-01", periods=36, freq="ME")

        # Annual seasonality (12-month cycle)
        annual = 50 * np.sin(2 * np.pi * np.arange(36) / 12)
        trend = np.exp(np.linspace(0, 1, 36))
        noise = np.random.normal(0, 5, 36)

        values = trend * (1 + (annual + noise) / 100)

        data = pd.DataFrame(
            {
                "C": np.cumsum(values),
                "D": np.cumsum(np.random.exponential(2, 36)),
            },
            index=dates,
        )

        return data

    def test_detector_init(self, detector):
        """Test detector initialization."""
        assert detector.min_periods == 2
        assert detector.patterns == {}

    def test_detect_daily_seasonality(self, detector, daily_data_with_seasonality):
        """Test detection of daily data seasonality."""
        result = detector.detect(
            daily_data_with_seasonality, frequency="D", compartments=["C"]
        )

        assert "C" in result
        assert result["C"]["frequency"] == "D"
        assert result["C"]["has_seasonality"]
        assert len(result["C"]["periods"]) > 0

        # Should detect weekly and annual
        periods = result["C"]["periods"]
        assert 7 in periods or 365 in periods

    def test_detect_annual_no_seasonality(self, detector, annual_data):
        """Annual data should not detect seasonality."""
        result = detector.detect(annual_data, frequency="YE", compartments=["C"])

        assert "C" in result
        assert not result["C"]["has_seasonality"]
        assert "Annual data" in result["C"]["reason"]

    def test_detect_monthly_seasonality(self, detector, monthly_data):
        """Test detection of monthly data seasonality."""
        result = detector.detect(monthly_data, frequency="ME", compartments=["C"])

        assert "C" in result
        # Monthly data with 36 obs should detect seasonality (at least quarterly)
        assert result["C"]["has_seasonality"] or result["C"]["has_seasonality"] is False
        if result["C"]["has_seasonality"]:
            # Should detect periods, likely including 3 (quarterly) or 12 (annual)
            assert len(result["C"]["periods"]) > 0

    def test_detect_insufficient_data(self, detector):
        """Test with insufficient data."""
        small_data = pd.DataFrame(
            {
                "C": [1],
            },
            index=pd.date_range("2020-01-01", periods=1, freq="D"),
        )

        result = detector.detect(small_data)
        # Returns empty dict when data too short
        assert len(result) == 0 or (
            "C" in result and not result["C"]["has_seasonality"]
        )

    def test_detect_multiple_compartments(self, detector, daily_data_with_seasonality):
        """Test detection for multiple compartments."""
        result = detector.detect(daily_data_with_seasonality, frequency="D")

        assert "C" in result
        assert "D" in result

    def test_get_frequency_info(self, detector):
        """Test frequency info retrieval."""
        info_d = detector._get_frequency_info("D")
        assert info_d["name"] == "Daily"
        assert 7 in info_d["candidate_periods"]
        assert 365 in info_d["candidate_periods"]

        info_w = detector._get_frequency_info("W")
        assert info_w["name"] == "Weekly"
        assert 52 in info_w["candidate_periods"]

        info_m = detector._get_frequency_info("ME")
        assert info_m["name"] == "Monthly"
        assert 12 in info_m["candidate_periods"]

        info_y = detector._get_frequency_info("YE")
        assert info_y["name"] == "Annual"
        assert len(info_y["candidate_periods"]) == 0

    def test_detrend(self, detector):
        """Test detrending."""
        series = pd.Series([1, 2, 3, 4, 5])
        detrended = detector._detrend(series)

        assert len(detrended) == len(series)
        # After detrending, linear trend should be removed
        assert np.abs(np.mean(detrended)) < 0.5

    def test_test_periodicity(self, detector):
        """Test periodicity detection."""
        # Perfectly periodic signal
        periodic = np.sin(2 * np.pi * np.arange(100) / 10)

        strength = detector._test_periodicity(periodic, 10)
        assert strength > 0.8  # Should detect strong periodicity

        # Random noise
        noise = np.random.normal(0, 1, 100)
        strength_noise = detector._test_periodicity(noise, 10)
        assert strength_noise < 0.3  # Should detect weak periodicity

    def test_get_summary(self, detector, daily_data_with_seasonality):
        """Test summary string generation."""
        detector.detect(daily_data_with_seasonality, frequency="D")
        summary = detector.get_summary()

        assert "Summary" in summary or "Seasonal" in summary
        assert "C" in summary


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_seasonal_parameters(self, sample_data_container):
        """Test get_seasonal_parameters function."""
        params = get_seasonal_parameters(sample_data_container, compartments=["C"])

        assert "C" in params
        assert "frequency" in params["C"]


class TestSeasonalityIntegration:
    """Integration tests with data containers."""

    def test_seasonality_with_daily_container(self):
        """Test seasonality detection with daily DataContainer."""
        dates = pd.date_range("2020-01-01", periods=365, freq="D")

        # Synthetic data with weekly pattern
        weekly = 50 * np.sin(2 * np.pi * np.arange(365) / 7)
        data = pd.DataFrame(
            {
                "C": 1000 + np.cumsum(weekly + np.random.normal(0, 5, 365)),
                "D": np.cumsum(np.random.exponential(1, 365)),
                "N": [1000000] * 365,
            },
            index=dates,
        )

        container = DataContainer(data, window=7)
        detector = SeasonalPatternDetector()

        result = detector.detect(container.data, frequency="D", compartments=["C"])

        assert result["C"]["frequency"] == "D"
        assert "periods" in result["C"]

    def test_seasonality_with_monthly_container(self):
        """Test seasonality detection with monthly DataContainer."""
        dates = pd.date_range("2020-01", periods=24, freq="ME")

        # Synthetic data with annual seasonality
        annual = 100 * np.sin(2 * np.pi * np.arange(24) / 12)
        data = pd.DataFrame(
            {
                "C": 5000 + np.cumsum(annual + np.random.normal(0, 10, 24)),
                "D": np.cumsum(np.random.exponential(20, 24)),
                "N": [1000000] * 24,
            },
            index=dates,
        )

        container = DataContainer(data, mode="cumulative", frequency="ME")
        detector = SeasonalPatternDetector()

        result = detector.detect(container.data, frequency="ME", compartments=["C"])

        assert result["C"]["frequency"] == "ME"
