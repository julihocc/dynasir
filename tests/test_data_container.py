"""
Tests for DataContainer class and data processing functionality.

Following TDD approach - these tests are written before implementation
to define expected behavior and ensure correct extraction.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from dynasir.core.exceptions import NotDataFrameError

# Import from the new extracted module
from dynasir.data import DataContainer


class TestDataContainerInitialization:
    """Test DataContainer class initialization and basic functionality."""

    def test_datacontainer_init_with_valid_data(self):
        """Test DataContainer initialization with valid DataFrame."""
        # Arrange - Create data with proper datetime index
        dates = pd.date_range("2020-01-01", periods=10, freq="D")
        sample_data = pd.DataFrame(
            {
                "C": [100, 150, 200, 250, 300, 350, 400, 450, 500, 550],
                "D": [1, 2, 5, 8, 12, 18, 25, 32, 40, 48],
                "N": [1000000] * 10,
            },
            index=dates,
        )

        # Act
        container = DataContainer(sample_data, window=7)

        # Assert
        assert container.raw_data is sample_data
        assert container.window == 7
        assert hasattr(container, "data")
        assert isinstance(container.data, pd.DataFrame)

    def test_datacontainer_init_with_custom_window(self):
        """Test DataContainer with custom window size."""
        # Arrange - Create data with proper datetime index
        dates = pd.date_range("2020-01-01", periods=20, freq="D")
        sample_data = pd.DataFrame(
            {
                "C": list(range(100, 300, 10)),
                "D": list(range(1, 21)),
                "N": [1000000] * 20,
            },
            index=dates,
        )

        # Act
        container = DataContainer(sample_data, window=14)

        # Assert
        assert container.window == 14

    def test_datacontainer_init_default_window(self):
        """Test DataContainer with default window size."""
        # Arrange - Create data with proper datetime index
        dates = pd.date_range("2020-01-01", periods=15, freq="D")
        sample_data = pd.DataFrame(
            {
                "C": list(range(100, 250, 10)),
                "D": list(range(1, 16)),
                "N": [1000000] * 15,
            },
            index=dates,
        )

        # Act
        container = DataContainer(sample_data)

        # Assert
        assert container.window == 7

    def test_datacontainer_init_invalid_data_type(self):
        """Test DataContainer raises error with invalid data type."""
        # Arrange
        invalid_data = [100, 150, 200]  # List instead of DataFrame

        # Act & Assert
        with pytest.raises(
            NotDataFrameError, match="raw data must be a pandas DataFrame"
        ):
            DataContainer(invalid_data)

    def test_datacontainer_init_none_data(self):
        """Test DataContainer raises error with None data."""
        # Act & Assert
        with pytest.raises(NotDataFrameError):
            DataContainer(None)


class TestDataContainerProcessing:
    """Test data processing pipeline within DataContainer."""

    @pytest.fixture
    def sample_owid_data(self):
        """Create sample data in OWID format."""
        dates = pd.date_range("2020-01-01", periods=30, freq="D")
        return pd.DataFrame(
            {
                "C": np.cumsum(np.random.poisson(10, 30)) + 100,
                "D": np.cumsum(np.random.poisson(1, 30)) + 1,
                "N": [1000000] * 30,
            },
            index=dates,
        )

    def test_datacontainer_creates_processed_data(self, sample_owid_data):
        """Test that DataContainer creates processed data."""
        # Act
        container = DataContainer(sample_owid_data)

        # Assert
        assert hasattr(container, "data")
        assert isinstance(container.data, pd.DataFrame)
        assert len(container.data) > 0

    def test_datacontainer_feature_engineering(self, sample_owid_data):
        """Test that feature engineering creates expected columns."""
        # Act
        container = DataContainer(sample_owid_data)

        # Assert - Check for SIRD compartments
        expected_columns = ["S", "I", "R", "D", "C", "A"]
        for col in expected_columns:
            assert (
                col in container.data.columns
            ), f"Column {col} missing from processed data"

    def test_datacontainer_rate_calculations(self, sample_owid_data):
        """Test that rate calculations are performed."""
        # Act
        container = DataContainer(sample_owid_data)

        # Assert - Check for rate columns
        expected_rates = ["alpha", "beta", "gamma"]
        for rate in expected_rates:
            assert (
                rate in container.data.columns
            ), f"Rate {rate} missing from processed data"

    def test_datacontainer_logit_transformations(self, sample_owid_data):
        """Test that logit transformations are applied."""
        # Act
        container = DataContainer(sample_owid_data)

        # Assert - Check for logit rate columns
        expected_logit_rates = ["logit_alpha", "logit_beta", "logit_gamma"]
        for logit_rate in expected_logit_rates:
            assert (
                logit_rate in container.data.columns
            ), f"Logit rate {logit_rate} missing"

    def test_datacontainer_difference_calculations(self, sample_owid_data):
        """Test that difference calculations are performed."""
        # Act
        container = DataContainer(sample_owid_data)

        # Assert - Check for difference columns
        expected_diffs = ["dC", "dI", "dR", "dD"]
        for diff in expected_diffs:
            assert (
                diff in container.data.columns
            ), f"Difference {diff} missing from processed data"

    def test_datacontainer_manual_process_call(self, sample_owid_data):
        """Test that process() can be called manually to update results."""
        # Act
        container = DataContainer(sample_owid_data, window=7)
        initial_data = container.data.copy()

        # Change window and re-process
        container.window = 14
        container.process()

        # Assert
        assert container.data is not None
        # Data should be different due to different smoothing window
        assert not container.data.equals(initial_data)


class TestDataContainerEdgeCases:
    """Test DataContainer behavior with edge cases and boundary conditions."""

    def test_datacontainer_with_minimal_data(self):
        """Test DataContainer with minimal valid data."""
        # Arrange - Just 2 rows of data
        minimal_data = pd.DataFrame(
            {"C": [100, 150], "D": [1, 2], "N": [1000000, 1000000]}
        )

        # Act & Assert - Should not raise error
        container = DataContainer(minimal_data)
        assert container is not None
        assert hasattr(container, "data")

    def test_datacontainer_with_zero_cases(self):
        """Test DataContainer handles zero cases appropriately."""
        # Arrange
        zero_data = pd.DataFrame(
            {"C": [0, 0, 5, 10], "D": [0, 0, 1, 2], "N": [1000000] * 4}
        )

        # Act - Should handle gracefully
        container = DataContainer(zero_data)

        # Assert
        assert container is not None
        # Check that processing completed without errors
        assert hasattr(container, "data")

    def test_datacontainer_with_missing_values(self):
        """Test DataContainer handles missing values appropriately."""
        # Arrange
        data_with_nans = pd.DataFrame(
            {"C": [100, np.nan, 200, 250], "D": [1, 2, np.nan, 5], "N": [1000000] * 4}
        )

        # Act
        container = DataContainer(data_with_nans)

        # Assert - Processing should handle NaN values
        assert container is not None
        assert hasattr(container, "data")


class TestDataContainerBackwardCompatibility:
    """Test that DataContainer maintains backward compatibility."""

    @pytest.fixture
    def legacy_usage_data(self):
        """Create data that mimics legacy usage patterns."""
        return pd.DataFrame(
            {
                "C": [100, 150, 200, 300, 450, 600],
                "D": [2, 3, 8, 15, 25, 40],
                "N": [1000000] * 6,
            }
        )

    def test_datacontainer_legacy_api_compatibility(self, legacy_usage_data):
        """Test that existing API usage patterns still work."""
        # Act - Use the same way as in legacy code
        container = DataContainer(legacy_usage_data, window=7)

        # Assert - Same attributes should be available
        assert hasattr(container, "raw_data")
        assert hasattr(container, "window")
        assert hasattr(container, "data")

        # Data should be accessible in the same way
        assert isinstance(container.data, pd.DataFrame)
        assert container.window == 7

    def test_datacontainer_maintains_data_structure(self, legacy_usage_data):
        """Test that processed data maintains expected structure."""
        # Act
        container = DataContainer(legacy_usage_data)

        # Assert - Data should have expected characteristics
        assert isinstance(container.data, pd.DataFrame)
        assert len(container.data) <= len(legacy_usage_data)  # May be filtered

        # Should have all the columns that dependent code expects
        assert "C" in container.data.columns
        assert "D" in container.data.columns


class TestDataContainerPerformance:
    """Test DataContainer performance characteristics."""

    def test_datacontainer_reasonable_processing_time(self):
        """Test that DataContainer processes data in reasonable time."""
        # Arrange - Larger dataset
        large_data = pd.DataFrame(
            {
                "C": np.cumsum(np.random.poisson(10, 1000)) + 100,
                "D": np.cumsum(np.random.poisson(1, 1000)) + 1,
                "N": [1000000] * 1000,
            }
        )

        # Act & Assert - Should complete quickly
        import time

        start_time = time.time()
        container = DataContainer(large_data)
        end_time = time.time()

        # Processing should complete within reasonable time (5 seconds max)
        assert (end_time - start_time) < 5.0
        assert container is not None

    def test_datacontainer_memory_efficient(self):
        """Test that DataContainer doesn't create excessive memory usage."""
        # Arrange
        data = pd.DataFrame(
            {
                "C": list(range(1000)),
                "D": list(range(0, 500, 1)) + [500] * 500,
                "N": [1000000] * 1000,
            }
        )

        # Act
        container = DataContainer(data)

        # Assert - Should not dramatically increase memory usage
        # (This is a qualitative test - mainly checking no errors)
        assert container is not None
        assert len(container.data.columns) > len(data.columns)  # Features added
        # But not excessively more columns
        assert len(container.data.columns) < 50  # Reasonable upper bound


class TestDataContainerIntegration:
    """Integration tests for DataContainer with real-world scenarios."""

    def test_datacontainer_with_real_owid_structure(self):
        """Test DataContainer with realistic OWID-like data."""
        # Arrange - Data structure similar to OWID
        dates = pd.date_range("2020-03-01", periods=100, freq="D")
        owid_like_data = pd.DataFrame(
            {
                "C": np.cumsum(np.random.poisson(50, 100)) + 1000,
                "D": np.cumsum(np.random.poisson(2, 100)) + 10,
                "N": [50000000] * 100,
            },
            index=dates,
        )

        # Act
        container = DataContainer(owid_like_data, window=7)

        # Assert
        assert container is not None
        assert len(container.data) > 0

        # Should have all expected epidemiological features
        epidemio_features = [
            "S",
            "I",
            "R",
            "D",
            "C",
            "A",  # Compartments
            "dC",
            "dI",
            "dR",
            "dD",  # Differences
            "alpha",
            "beta",
            "gamma",  # Rates
            "logit_alpha",
            "logit_beta",
            "logit_gamma",  # Logit rates
        ]

        for feature in epidemio_features:
            assert feature in container.data.columns, f"Missing feature: {feature}"

    @patch("dynasir.data.container.logging")
    def test_datacontainer_logging_behavior(self, mock_logging):
        """Test that DataContainer maintains proper logging behavior."""
        # Arrange
        data = pd.DataFrame({"C": [100, 200, 300], "D": [1, 5, 10], "N": [1000000] * 3})

        # Act
        container = DataContainer(data)

        # Assert - Should have called logging.debug
        assert mock_logging.debug.called
        assert container is not None
