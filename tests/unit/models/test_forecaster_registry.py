"""
Unit tests for the ForecasterRegistry and registration mechanism.
"""

import numpy as np
import pandas as pd
import pytest

from dynasir.models.forecasting.base import BaseForecaster
from dynasir.models.forecasting.registry import (
    ForecasterRegistry,
    register_forecaster,
)


class DummyForecaster(BaseForecaster):
    """Dummy forecaster for testing registration."""

    @property
    def backend_name(self) -> str:
        """Return backend name."""
        return "dummy"

    def create_model(self, **kwargs) -> None:
        """Create model."""
        self.model = "dummy_model"

    def fit(self, **kwargs) -> None:
        """Fit model."""
        self.fitted_model = "dummy_fitted_model"

    def forecast_interval(self, steps: int, **kwargs):
        """Generate forecasts."""
        n_vars = self.data.shape[1] if hasattr(self.data, "shape") else 3
        lower = np.zeros((steps, n_vars))
        point = np.ones((steps, n_vars))
        upper = np.ones((steps, n_vars)) * 2
        return lower, point, upper


class AnotherDummyForecaster(BaseForecaster):
    """Another dummy forecaster for testing."""

    @property
    def backend_name(self) -> str:
        """Return backend name."""
        return "another_dummy"

    def create_model(self, **kwargs) -> None:
        """Create model."""
        self.model = "another_model"

    def fit(self, **kwargs) -> None:
        """Fit model."""
        self.fitted_model = "another_fitted"

    def forecast_interval(self, steps: int, **kwargs):
        """Generate forecasts."""
        n_vars = self.data.shape[1] if hasattr(self.data, "shape") else 3
        return (
            np.zeros((steps, n_vars)),
            np.ones((steps, n_vars)),
            np.ones((steps, n_vars)) * 2,
        )


class InvalidForecaster:
    """Invalid forecaster that doesn't inherit from BaseForecaster."""

    pass


@pytest.fixture(autouse=True)
def clean_registry():
    """Clean the registry before and after each test."""
    # Store original state
    original_forecasters = ForecasterRegistry._forecasters.copy()
    original_aliases = ForecasterRegistry._aliases.copy()

    # Clear for test
    ForecasterRegistry.clear()

    yield

    # Restore original state
    ForecasterRegistry._forecasters = original_forecasters
    ForecasterRegistry._aliases = original_aliases


@pytest.fixture
def sample_data():
    """Create sample data for forecaster initialization."""
    dates = pd.date_range("2020-01-01", periods=30, freq="D")
    return pd.DataFrame(
        {
            "logit_alpha": np.random.randn(30),
            "logit_beta": np.random.randn(30),
            "logit_gamma": np.random.randn(30),
        },
        index=dates,
    )


class TestForecasterRegistryRegistration:
    """Test registration functionality."""

    def test_register_basic(self, sample_data):
        """Test basic registration of a forecaster."""
        ForecasterRegistry.register("dummy", DummyForecaster)

        assert "dummy" in ForecasterRegistry.list_available()
        assert ForecasterRegistry.get("dummy") is DummyForecaster

    def test_register_with_aliases(self, sample_data):
        """Test registration with aliases."""
        ForecasterRegistry.register(
            "dummy", DummyForecaster, aliases=["dm", "dummy_backend"]
        )

        assert "dummy" in ForecasterRegistry.list_available()
        assert ForecasterRegistry.get("dummy") is DummyForecaster
        assert ForecasterRegistry.get("dm") is DummyForecaster
        assert ForecasterRegistry.get("dummy_backend") is DummyForecaster

        aliases = ForecasterRegistry.list_aliases()
        assert aliases["dm"] == "dummy"
        assert aliases["dummy_backend"] == "dummy"

    def test_register_empty_name_raises_error(self):
        """Test that registering with empty name raises ValueError."""
        with pytest.raises(ValueError, match="Backend name cannot be empty"):
            ForecasterRegistry.register("", DummyForecaster)

    def test_register_non_forecaster_raises_error(self):
        """Test that registering non-BaseForecaster class raises TypeError."""
        with pytest.raises(TypeError, match="must inherit from BaseForecaster"):
            ForecasterRegistry.register("invalid", InvalidForecaster)

    def test_register_duplicate_name_raises_error(self):
        """Test that registering duplicate name raises ValueError."""
        ForecasterRegistry.register("dummy", DummyForecaster)

        with pytest.raises(ValueError, match="already registered"):
            ForecasterRegistry.register("dummy", AnotherDummyForecaster)

    def test_register_duplicate_alias_raises_error(self):
        """Test that registering duplicate alias raises ValueError."""
        ForecasterRegistry.register("dummy", DummyForecaster, aliases=["dm"])

        with pytest.raises(ValueError, match="Alias 'dm' is already registered"):
            ForecasterRegistry.register(
                "another", AnotherDummyForecaster, aliases=["dm"]
            )

    def test_register_multiple_backends(self):
        """Test registering multiple backends."""
        ForecasterRegistry.register("dummy1", DummyForecaster)
        ForecasterRegistry.register("dummy2", AnotherDummyForecaster)

        available = ForecasterRegistry.list_available()
        assert len(available) == 2
        assert "dummy1" in available
        assert "dummy2" in available


class TestForecasterRegistryRetrieval:
    """Test retrieval functionality."""

    def test_get_by_name(self):
        """Test retrieving forecaster by canonical name."""
        ForecasterRegistry.register("dummy", DummyForecaster)

        forecaster_class = ForecasterRegistry.get("dummy")
        assert forecaster_class is DummyForecaster

    def test_get_by_alias(self):
        """Test retrieving forecaster by alias."""
        ForecasterRegistry.register("dummy", DummyForecaster, aliases=["dm"])

        forecaster_class = ForecasterRegistry.get("dm")
        assert forecaster_class is DummyForecaster

    def test_get_case_insensitive(self):
        """Test case-insensitive retrieval for canonical names."""
        ForecasterRegistry.register("dummy", DummyForecaster, aliases=["dm"])

        # Canonical name lookup is case-insensitive
        assert ForecasterRegistry.get("dummy") is DummyForecaster
        assert ForecasterRegistry.get("DUMMY") is DummyForecaster
        assert ForecasterRegistry.get("Dummy") is DummyForecaster

        # Alias lookup is also case-insensitive
        assert ForecasterRegistry.get("dm") is DummyForecaster
        assert ForecasterRegistry.get("DM") is DummyForecaster
        assert ForecasterRegistry.get("Dm") is DummyForecaster

    def test_get_unknown_backend_raises_error(self):
        """Test that getting unknown backend raises helpful ValueError."""
        ForecasterRegistry.register("dummy", DummyForecaster)

        with pytest.raises(ValueError, match="Forecaster 'unknown' not found"):
            ForecasterRegistry.get("unknown")

    def test_get_error_message_includes_available_backends(self):
        """Test that error message includes list of available backends."""
        ForecasterRegistry.register("dummy", DummyForecaster, aliases=["dm"])

        with pytest.raises(ValueError) as exc_info:
            ForecasterRegistry.get("unknown")

        error_msg = str(exc_info.value)
        assert "Available backends: ['dummy']" in error_msg
        assert "Available aliases: ['dm']" in error_msg


class TestForecasterRegistryListing:
    """Test listing functionality."""

    def test_list_available_empty(self):
        """Test listing with no registered backends."""
        assert ForecasterRegistry.list_available() == []

    def test_list_available_multiple(self):
        """Test listing multiple backends."""
        ForecasterRegistry.register("dummy1", DummyForecaster)
        ForecasterRegistry.register("dummy2", AnotherDummyForecaster)

        available = ForecasterRegistry.list_available()
        assert len(available) == 2
        assert available == ["dummy1", "dummy2"]  # Should be sorted

    def test_list_available_sorted(self):
        """Test that backends are listed in sorted order."""
        ForecasterRegistry.register("zzz", DummyForecaster)
        ForecasterRegistry.register("aaa", AnotherDummyForecaster)

        available = ForecasterRegistry.list_available()
        assert available == ["aaa", "zzz"]

    def test_list_aliases_empty(self):
        """Test listing aliases with no registered backends."""
        assert ForecasterRegistry.list_aliases() == {}

    def test_list_aliases_multiple(self):
        """Test listing multiple aliases."""
        ForecasterRegistry.register("dummy1", DummyForecaster, aliases=["dm1", "d1"])
        ForecasterRegistry.register("dummy2", AnotherDummyForecaster, aliases=["dm2"])

        aliases = ForecasterRegistry.list_aliases()
        assert len(aliases) == 3
        assert aliases["dm1"] == "dummy1"
        assert aliases["d1"] == "dummy1"
        assert aliases["dm2"] == "dummy2"

    def test_list_available_excludes_aliases(self):
        """Test that list_available returns only canonical names, not aliases."""
        ForecasterRegistry.register("dummy", DummyForecaster, aliases=["dm", "d"])

        available = ForecasterRegistry.list_available()
        assert available == ["dummy"]
        assert "dm" not in available
        assert "d" not in available


class TestForecasterRegistryDecorator:
    """Test decorator registration pattern."""

    def test_decorator_registration(self, sample_data):
        """Test registering forecaster using decorator."""

        @register_forecaster("decorated")
        class DecoratedForecaster(BaseForecaster):
            @property
            def backend_name(self) -> str:
                return "decorated"

            def create_model(self, **kwargs) -> None:
                self.model = "decorated_model"

            def fit(self, **kwargs) -> None:
                self.fitted_model = "decorated_fitted"

            def forecast_interval(self, steps: int, **kwargs):
                n_vars = 3
                return (
                    np.zeros((steps, n_vars)),
                    np.ones((steps, n_vars)),
                    np.ones((steps, n_vars)) * 2,
                )

        assert "decorated" in ForecasterRegistry.list_available()
        assert ForecasterRegistry.get("decorated") is DecoratedForecaster

        # Test that the class is still usable
        forecaster = DecoratedForecaster(sample_data)
        assert forecaster.backend_name == "decorated"

    def test_decorator_with_aliases(self, sample_data):
        """Test decorator with aliases."""

        @register_forecaster("decorated", aliases=["dec", "decorated_backend"])
        class DecoratedForecaster(BaseForecaster):
            @property
            def backend_name(self) -> str:
                return "decorated"

            def create_model(self, **kwargs) -> None:
                self.model = "decorated_model"

            def fit(self, **kwargs) -> None:
                self.fitted_model = "decorated_fitted"

            def forecast_interval(self, steps: int, **kwargs):
                n_vars = 3
                return (
                    np.zeros((steps, n_vars)),
                    np.ones((steps, n_vars)),
                    np.ones((steps, n_vars)) * 2,
                )

        assert ForecasterRegistry.get("decorated") is DecoratedForecaster
        assert ForecasterRegistry.get("dec") is DecoratedForecaster
        assert ForecasterRegistry.get("decorated_backend") is DecoratedForecaster

    def test_decorator_returns_class_unchanged(self, sample_data):
        """Test that decorator returns the class unchanged."""

        @register_forecaster("decorated")
        class DecoratedForecaster(BaseForecaster):
            @property
            def backend_name(self) -> str:
                return "decorated"

            def create_model(self, **kwargs) -> None:
                self.model = "decorated_model"

            def fit(self, **kwargs) -> None:
                self.fitted_model = "decorated_fitted"

            def forecast_interval(self, steps: int, **kwargs):
                n_vars = 3
                return (
                    np.zeros((steps, n_vars)),
                    np.ones((steps, n_vars)),
                    np.ones((steps, n_vars)) * 2,
                )

        # Class should be fully functional
        forecaster = DecoratedForecaster(sample_data)
        forecaster.create_model()
        forecaster.fit()
        lower, point, upper = forecaster.forecast_interval(10)

        assert lower.shape == (10, 3)
        assert point.shape == (10, 3)
        assert upper.shape == (10, 3)


class TestForecasterRegistryUnregister:
    """Test unregister functionality."""

    def test_unregister_basic(self):
        """Test basic unregister functionality."""
        ForecasterRegistry.register("dummy", DummyForecaster)
        assert "dummy" in ForecasterRegistry.list_available()

        ForecasterRegistry.unregister("dummy")
        assert "dummy" not in ForecasterRegistry.list_available()

    def test_unregister_removes_aliases(self):
        """Test that unregister removes associated aliases."""
        ForecasterRegistry.register("dummy", DummyForecaster, aliases=["dm", "d"])

        ForecasterRegistry.unregister("dummy")

        assert "dummy" not in ForecasterRegistry.list_available()
        aliases = ForecasterRegistry.list_aliases()
        assert "dm" not in aliases
        assert "d" not in aliases

    def test_unregister_unknown_raises_error(self):
        """Test that unregistering unknown backend raises ValueError."""
        with pytest.raises(ValueError, match="not registered"):
            ForecasterRegistry.unregister("unknown")

    def test_unregister_case_insensitive(self):
        """Test case-insensitive unregister."""
        ForecasterRegistry.register("dummy", DummyForecaster)

        ForecasterRegistry.unregister("DUMMY")
        assert "dummy" not in ForecasterRegistry.list_available()


class TestForecasterRegistryClear:
    """Test clear functionality."""

    def test_clear_empty_registry(self):
        """Test clearing an empty registry."""
        ForecasterRegistry.clear()
        assert ForecasterRegistry.list_available() == []
        assert ForecasterRegistry.list_aliases() == {}

    def test_clear_removes_all_backends(self):
        """Test that clear removes all backends."""
        ForecasterRegistry.register("dummy1", DummyForecaster)
        ForecasterRegistry.register("dummy2", AnotherDummyForecaster)

        assert len(ForecasterRegistry.list_available()) == 2

        ForecasterRegistry.clear()

        assert ForecasterRegistry.list_available() == []

    def test_clear_removes_all_aliases(self):
        """Test that clear removes all aliases."""
        ForecasterRegistry.register("dummy1", DummyForecaster, aliases=["dm1", "d1"])
        ForecasterRegistry.register("dummy2", AnotherDummyForecaster, aliases=["dm2"])

        assert len(ForecasterRegistry.list_aliases()) == 3

        ForecasterRegistry.clear()

        assert ForecasterRegistry.list_aliases() == {}


class TestForecasterRegistryEdgeCases:
    """Test edge cases and special scenarios."""

    def test_register_with_empty_aliases_list(self):
        """Test registering with empty aliases list."""
        ForecasterRegistry.register("dummy", DummyForecaster, aliases=[])

        assert "dummy" in ForecasterRegistry.list_available()
        assert ForecasterRegistry.list_aliases() == {}

    def test_register_with_none_aliases(self):
        """Test registering with None aliases."""
        ForecasterRegistry.register("dummy", DummyForecaster, aliases=None)

        assert "dummy" in ForecasterRegistry.list_available()
        assert ForecasterRegistry.list_aliases() == {}

    def test_multiple_aliases_point_to_same_backend(self):
        """Test multiple aliases correctly resolve to same backend."""
        ForecasterRegistry.register(
            "dummy", DummyForecaster, aliases=["alias1", "alias2", "alias3"]
        )

        assert ForecasterRegistry.get("dummy") is DummyForecaster
        assert ForecasterRegistry.get("alias1") is DummyForecaster
        assert ForecasterRegistry.get("alias2") is DummyForecaster
        assert ForecasterRegistry.get("alias3") is DummyForecaster

    def test_registry_is_singleton(self):
        """Test that registry maintains state across accesses."""
        ForecasterRegistry.register("dummy", DummyForecaster)

        # Access from different "instances" should see the same data
        available1 = ForecasterRegistry.list_available()
        available2 = ForecasterRegistry.list_available()

        assert available1 is not available2  # Different list objects
        assert available1 == available2  # But same content

    def test_instantiate_registered_forecaster(self, sample_data):
        """Test that registered forecasters can be instantiated and used."""
        ForecasterRegistry.register("dummy", DummyForecaster)

        forecaster_class = ForecasterRegistry.get("dummy")
        forecaster = forecaster_class(sample_data)

        assert isinstance(forecaster, BaseForecaster)
        assert forecaster.backend_name == "dummy"

        forecaster.create_model()
        forecaster.fit()
        lower, point, upper = forecaster.forecast_interval(10)

        assert lower.shape == (10, 3)
        assert point.shape == (10, 3)
        assert upper.shape == (10, 3)
