"""
Tests for constants module.

Following TDD principles, these tests define the expected behavior
of the constants module before implementation.
"""


def test_constants_module_imports():
    """Test that all constants can be imported from core.constants."""
    from dynasir.core.constants import (
        CENTRAL_TENDENCY_METHODS,
        COMPARTMENTS,
        FORECASTING_LEVELS,
        LOGIT_RATIOS,
        RATIOS,
    )

    # Basic import verification
    assert RATIOS is not None
    assert LOGIT_RATIOS is not None
    assert COMPARTMENTS is not None
    assert FORECASTING_LEVELS is not None
    assert CENTRAL_TENDENCY_METHODS is not None


def test_ratios_constants():
    """Test RATIOS constant has correct values and type."""
    from dynasir.core.constants import RATIOS

    expected = ["alpha", "beta", "gamma", "delta"]
    assert isinstance(RATIOS, list)
    assert RATIOS == expected
    assert len(RATIOS) == 4
    assert all(isinstance(item, str) for item in RATIOS)

    # Test backward compatibility - first 3 rates are unchanged
    assert RATIOS[:3] == ["alpha", "beta", "gamma"]


def test_logit_ratios_constants():
    """Test LOGIT_RATIOS constant has correct values and type."""
    from dynasir.core.constants import LOGIT_RATIOS

    expected = ["logit_alpha", "logit_beta", "logit_gamma", "logit_delta"]
    assert isinstance(LOGIT_RATIOS, list)
    assert LOGIT_RATIOS == expected
    assert len(LOGIT_RATIOS) == 4
    assert all(isinstance(item, str) for item in LOGIT_RATIOS)

    # Test backward compatibility - first 3 logit ratios are unchanged
    assert LOGIT_RATIOS[:3] == ["logit_alpha", "logit_beta", "logit_gamma"]


def test_compartments_constants():
    """Test COMPARTMENTS constant has correct values and type."""
    from dynasir.core.constants import COMPARTMENTS

    expected = ["A", "C", "S", "I", "R", "D", "V"]
    assert isinstance(COMPARTMENTS, list)
    assert COMPARTMENTS == expected
    assert len(COMPARTMENTS) == 7
    assert all(isinstance(item, str) for item in COMPARTMENTS)

    # Test backward compatibility - first 6 compartments are unchanged
    assert COMPARTMENTS[:6] == ["A", "C", "S", "I", "R", "D"]


def test_forecasting_levels_constants():
    """Test FORECASTING_LEVELS constant has correct values and type."""
    from dynasir.core.constants import FORECASTING_LEVELS

    expected = ["lower", "point", "upper"]
    assert isinstance(FORECASTING_LEVELS, list)
    assert FORECASTING_LEVELS == expected
    assert len(FORECASTING_LEVELS) == 3
    assert all(isinstance(item, str) for item in FORECASTING_LEVELS)


def test_central_tendency_methods_constants():
    """Test CENTRAL_TENDENCY_METHODS constant has correct values and type."""
    from dynasir.core.constants import CENTRAL_TENDENCY_METHODS

    expected = ["mean", "median", "gmean", "hmean"]
    assert isinstance(CENTRAL_TENDENCY_METHODS, list)
    assert CENTRAL_TENDENCY_METHODS == expected
    assert len(CENTRAL_TENDENCY_METHODS) == 4
    assert all(isinstance(item, str) for item in CENTRAL_TENDENCY_METHODS)


def test_constants_immutability():
    """Test that constants are properly typed and documented."""
    from dynasir.core.constants import (
        CENTRAL_TENDENCY_METHODS,
        COMPARTMENTS,
        FORECASTING_LEVELS,
        LOGIT_RATIOS,
        RATIOS,
    )

    # Test that all constants are lists of strings
    for const in [
        RATIOS,
        LOGIT_RATIOS,
        COMPARTMENTS,
        FORECASTING_LEVELS,
        CENTRAL_TENDENCY_METHODS,
    ]:
        assert isinstance(const, list)
        assert all(isinstance(item, str) for item in const)
        assert len(const) > 0


def test_ratios_correspondence():
    """Test that RATIOS and LOGIT_RATIOS correspond correctly."""
    from dynasir.core.constants import LOGIT_RATIOS, RATIOS

    # Each logit ratio should correspond to a ratio
    for i, ratio in enumerate(RATIOS):
        expected_logit = f"logit_{ratio}"
        assert LOGIT_RATIOS[i] == expected_logit


def test_compartment_labels():
    """Test that COMPARTMENT_LABELS has all compartments including V."""
    from dynasir.core.constants import COMPARTMENT_LABELS, COMPARTMENTS

    # All compartments should have labels
    for compartment in COMPARTMENTS:
        assert compartment in COMPARTMENT_LABELS

    # Test specific labels
    assert COMPARTMENT_LABELS["V"] == "Vaccinated"
    assert COMPARTMENT_LABELS["S"] == "Susceptible"
    assert COMPARTMENT_LABELS["I"] == "Infected"
    assert COMPARTMENT_LABELS["R"] == "Recovered"
    assert COMPARTMENT_LABELS["D"] == "Deaths"
    assert COMPARTMENT_LABELS["C"] == "Confirmed"
    assert COMPARTMENT_LABELS["A"] == "Active"


def test_backward_compatibility():
    """Test that constants maintain backward compatibility with original module."""
    import dynasir

    assert hasattr(dynasir, "RATIOS")
    assert hasattr(dynasir, "LOGIT_RATIOS")
    assert hasattr(dynasir, "COMPARTMENTS")
    assert hasattr(dynasir, "FORECASTING_LEVELS")
    assert hasattr(dynasir, "CENTRAL_TENDENCY_METHODS")

    from dynasir.core.constants import (
        CENTRAL_TENDENCY_METHODS,
        COMPARTMENTS,
        FORECASTING_LEVELS,
        LOGIT_RATIOS,
        RATIOS,
    )

    assert dynasir.RATIOS == RATIOS
    assert dynasir.LOGIT_RATIOS == LOGIT_RATIOS
    assert dynasir.COMPARTMENTS == COMPARTMENTS
    assert dynasir.FORECASTING_LEVELS == FORECASTING_LEVELS
    assert dynasir.CENTRAL_TENDENCY_METHODS == CENTRAL_TENDENCY_METHODS
