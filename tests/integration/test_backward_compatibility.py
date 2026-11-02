"""Integration tests for backward compatibility."""


def test_import_original_functionality():
    """Test that we can still import the original functionality."""
    # This should work throughout the refactoring
    from dynasir import DataContainer, Model, process_data_from_owid

    # Verify classes are importable
    assert DataContainer is not None
    assert Model is not None
    assert process_data_from_owid is not None


def test_import_constants():
    """Test that constants are importable."""
    from dynasir import COMPARTMENTS, RATIOS

    # Verify basic constants
    assert isinstance(RATIOS, list)
    assert isinstance(COMPARTMENTS, list)

    # Verify expected values
    assert "alpha" in RATIOS
    assert "C" in COMPARTMENTS


def test_package_version():
    """Test that package version is accessible."""
    import dynasir

    assert hasattr(dynasir, "__version__")
    assert dynasir.__version__ == "1.0.0"


def test_package_metadata():
    """Test that package metadata is accessible."""
    import dynasir

    assert hasattr(dynasir, "__author__")
    assert hasattr(dynasir, "__email__")
    assert dynasir.__author__ == "Juliho David Castillo Colmenares"


def test_v080_new_constants_available():
    """Test that new v0.8.0 constants are available without breaking old imports."""
    # Original constants should still work
    from dynasir import COMPARTMENTS, RATIOS

    assert isinstance(RATIOS, list)
    assert isinstance(COMPARTMENTS, list)

    # New v0.8.0 constants should be available
    from dynasir.core.constants import (
        DEFAULT_FREQUENCY,
        FREQUENCY_ALIASES,
        RECOVERY_LAG_BY_FREQUENCY,
        SUPPORTED_FREQUENCIES,
    )

    assert DEFAULT_FREQUENCY == "D"
    assert "Y" in SUPPORTED_FREQUENCIES
    assert "annual" in FREQUENCY_ALIASES
    assert "D" in RECOVERY_LAG_BY_FREQUENCY


def test_v080_new_functions_available():
    """Test that new v0.8.0 functions exist and are callable."""
    from dynasir.data.preprocessing import (
        detect_frequency,
        warn_frequency_mismatch,
    )

    # Should be callable
    assert callable(detect_frequency)
    assert callable(warn_frequency_mismatch)


def test_v080_reindex_data_backward_compatible(sample_processed_data):
    """Test that reindex_data maintains v0.7.0 behavior by default."""
    from dynasir.data.preprocessing import reindex_data

    # Call without new parameters (v0.7.0 style)
    reindexed = reindex_data(sample_processed_data)

    # Should default to daily frequency
    assert reindexed.index.freq == "D"
    assert len(reindexed) == len(sample_processed_data)


def test_v080_model_workflow_unchanged(sample_data_container):
    """Test that complete Model workflow works exactly as in v0.7.0."""
    from dynasir import Model

    # Create model using v0.7.0 pattern (no new parameters)
    model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")
    model.create_model()
    model.fit_model(max_lag=3)
    model.forecast(steps=30)
    model.run_simulations(n_jobs=1)
    model.generate_result()

    # Should work exactly as before
    assert model.results is not None
    assert "C" in model.results
    assert "mean" in model.results.C.columns
    assert "median" in model.results.C.columns


def test_v080_aggregate_forecast_method_exists(sample_data_container):
    """Test that new aggregate_forecast method exists on Model."""
    from dynasir import Model

    model = Model(sample_data_container, start="2020-03-10", stop="2020-03-25")

    # Method should exist
    assert hasattr(model, "aggregate_forecast")
    assert callable(model.aggregate_forecast)
