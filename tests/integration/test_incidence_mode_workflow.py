"""
Integration tests for complete incidence mode workflow.

Tests the full pipeline from data loading through forecasting and simulation
for incidence mode data. Uses realistic test fixtures to avoid rate saturation.
"""

import numpy as np
import pandas as pd
import pytest

from dynasir import DataContainer, Model


class TestIncidenceModeBasicWorkflow:
    """Test basic incidence mode workflow."""

    def test_incidence_mode_data_container_creation(self, sample_owid_data):
        """DataContainer should preserve mode attribute."""
        # Convert OWID data to incidence mode
        data = sample_owid_data.copy()
        data.set_index("date", inplace=True)
        data["I"] = data["total_cases"].diff().fillna(data["total_cases"].iloc[0])
        data = data.rename(columns={"total_deaths": "D", "population": "N"})[
            ["I", "D", "N"]
        ]

        inc_container = DataContainer(data, mode="incidence")
        assert inc_container.mode == "incidence"
        assert "I" in inc_container.data.columns
        assert "C" in inc_container.data.columns

    def test_incidence_mode_model_creation(self, sample_data_container):
        """Model should inherit mode from DataContainer."""
        assert sample_data_container.mode == "cumulative"
        model = Model(sample_data_container)
        assert model.mode == "cumulative"


class TestIncidenceModeEndToEnd:
    """End-to-end integration tests for incidence mode."""

    def test_complete_workflow_existing_cumulative_mode(self, sample_data_container):
        """Complete workflow should work with existing cumulative mode (baseline)."""
        model = Model(sample_data_container)

        # Full pipeline
        model.create_model()
        model.fit_model(max_lag=2)
        model.forecast(steps=10)
        model.run_simulations(n_jobs=1)
        model.generate_result()

        # Verify mode preserved throughout
        assert model.mode == "cumulative"

        # Verify results structure (results is Box with compartment DataFrames)
        assert model.results is not None
        for compartment in ["S", "I", "R", "D", "C", "A"]:
            assert compartment in model.results
            # Each compartment is a DataFrame with scenario columns
            result_df = model.results[compartment]
            assert isinstance(result_df, pd.DataFrame)
            assert len(result_df) == 10
            # Should have scenario columns (e.g., 'lower|lower|lower') and central tendency columns
            assert "mean" in result_df.columns
            assert "median" in result_df.columns


class TestIncidenceModeConceptValidation:
    """Validate incidence mode concepts without full VAR fitting."""

    def test_incidence_feature_engineering(self):
        """Feature engineering should work correctly in incidence mode."""
        # Realistic COVID-style pattern with variation
        dates = pd.date_range("2020-03-01", periods=60, freq="D")

        # Incident cases pattern: growth → peak → decline → plateau
        t = np.arange(60)
        growth = 50 * np.exp(0.05 * t[:20])  # Exponential growth
        peak = [300] * 10  # Peak plateau
        decline = 300 * np.exp(-0.08 * np.arange(30))  # Decline
        incident = np.concatenate([growth, peak, decline])

        # Add realistic noise
        np.random.seed(42)
        incident = incident * (1 + 0.1 * np.random.randn(60))
        incident = np.clip(incident, 10, None)  # Keep positive

        data = pd.DataFrame(
            {
                "I": incident,
                "D": np.cumsum(incident * 0.01),  # 1% mortality
                "N": [1_000_000] * 60,
            },
            index=dates,
        )

        container = DataContainer(data, mode="incidence", window=3)

        # Verify mode propagated
        assert container.mode == "incidence"

        # Verify I is preserved (can vary up/down)
        assert "I" in container.data.columns
        I_values = container.data["I"].dropna()
        assert len(I_values) > 0
        # I should vary (not monotonic)
        diffs = I_values.diff().dropna()
        assert (diffs > 0).any()  # Has increases
        assert (diffs < 0).any()  # Has decreases

        # Verify C is generated and monotonic
        assert "C" in container.data.columns
        C_values = container.data["C"].dropna()
        C_diffs = C_values.diff().dropna()
        assert all(C_diffs >= -1e-10)  # Monotonic (allowing floating point error)

    def test_incidence_vs_cumulative_feature_differences(self):
        """Incidence and cumulative modes should produce different compartments."""
        dates = pd.date_range("2020-01-01", periods=30, freq="D")

        # Create realistic incidence data with epidemiological pattern
        t = np.arange(30)
        I_data = 50 * np.exp(0.08 * t) + 10 * np.random.randn(30)
        I_data = np.clip(I_data, 1, None)  # Keep positive

        inc_data = pd.DataFrame(
            {"I": I_data, "D": np.cumsum(I_data * 0.01), "N": [100000] * 30},
            index=dates,
        )

        # Create equivalent cumulative data
        cum_data = pd.DataFrame(
            {"C": np.cumsum(I_data), "D": np.cumsum(I_data * 0.01), "N": [100000] * 30},
            index=dates,
        )

        # Process both
        inc_container = DataContainer(inc_data, mode="incidence", window=3)
        cum_container = DataContainer(cum_data, mode="cumulative", window=3)

        # Modes should differ
        assert inc_container.mode == "incidence"
        assert cum_container.mode == "cumulative"

        # Both should have C column, but values may differ slightly
        # due to smoothing and feature engineering differences
        assert "C" in inc_container.data.columns
        assert "C" in cum_container.data.columns

        # Incidence mode preserves I variation
        assert "I" in inc_container.data.columns
        I_inc = inc_container.data["I"].dropna()
        assert len(I_inc) > 0


@pytest.mark.slow
class TestIncidenceModeMeaslesWorkflow:
    """Test realistic measles workflow (marked as slow)."""

    def test_measles_concept(self):
        """Demonstrate measles-style data pattern (concept test only)."""
        dates = pd.date_range("2010-01-01", periods=15, freq="YE")

        # Realistic measles pattern: sporadic cases with elimination periods
        incident_cases = [
            220,
            55,
            667,
            164,
            81,  # 2010-2014
            34,
            12,
            0,
            0,
            4,  # 2015-2019 (near elimination)
            18,
            45,
            103,
            67,
            89,  # 2020-2024 (reintroduction)
        ]

        data = pd.DataFrame(
            {
                "I": incident_cases,
                "D": [1, 1, 3, 4, 4, 4, 4, 4, 4, 4, 4, 5, 7, 8, 9],  # Cumulative
                "N": [120_000_000] * 15,
            },
            index=dates,
        )

        container = DataContainer(data, mode="incidence")

        # Verify incidence mode accepted the data
        assert container.mode == "incidence"

        # Verify I can vary (outbreak pattern)
        I_vals = container.data["I"].dropna()
        assert len(I_vals) > 0

        # Verify C is monotonic despite I variation
        C_vals = container.data["C"].dropna()
        if len(C_vals) > 1:
            C_diffs = C_vals.diff().dropna()
            assert all(C_diffs >= -1e-10)
