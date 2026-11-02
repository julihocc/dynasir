"""
Registry for forecasting backends.

This module provides a registry pattern for dynamically registering and
retrieving forecasting backend implementations without modifying core code.
"""

from typing import Callable, Dict, List, Optional, Type

from .base import BaseForecaster


class ForecasterRegistry:
    """
    Global registry for time series forecasting backends.

    This class maintains a mapping of backend names to forecaster classes,
    enabling dynamic backend selection at runtime. It supports:
    - Registration of new backends via decorator or direct method
    - Alias resolution (e.g., 'vector_ar' -> 'var')
    - Listing available backends
    - Helpful error messages for unknown backends

    The registry is a singleton pattern using class methods, so all
    registrations are globally accessible.

    Examples:
        Register a new backend:

        >>> from dynasir.models.forecasting.base import BaseForecaster
        >>> from dynasir.models.forecasting.registry import register_forecaster
        >>>
        >>> @register_forecaster("my_backend", aliases=["mb"])
        >>> class MyForecaster(BaseForecaster):
        ...     # Implementation here
        ...     pass
        >>>
        >>> # Now users can use it
        >>> from dynasir import Model
        >>> model = Model(container, forecaster="my_backend")
        >>> # Or using the alias
        >>> model = Model(container, forecaster="mb")

        Retrieve a registered backend:

        >>> from dynasir.models.forecasting.registry import ForecasterRegistry
        >>> forecaster_class = ForecasterRegistry.get("var")
        >>> print(forecaster_class)
        <class 'dynasir.models.forecasting.var.VARForecaster'>

        List all available backends:

        >>> backends = ForecasterRegistry.list_available()
        >>> print(backends)
        ['arima', 'lstm', 'prophet', 'var']
    """

    _forecasters: Dict[str, Type[BaseForecaster]] = {}
    _aliases: Dict[str, str] = {}  # alias -> canonical name mapping

    @classmethod
    def register(
        cls,
        name: str,
        forecaster_class: Type[BaseForecaster],
        aliases: Optional[List[str]] = None,
    ) -> None:
        """
        Register a forecaster implementation.

        Args:
            name: Canonical backend name (e.g., 'var', 'prophet', 'arima')
                  Should be lowercase and use underscores for multi-word names
            forecaster_class: Forecaster class that implements BaseForecaster
            aliases: Optional list of alternative names for this backend
                    Example: ['vector_ar', 'vector_autoregression'] for VAR

        Raises:
            TypeError: If forecaster_class doesn't inherit from BaseForecaster
            ValueError: If name is empty or already registered

        Examples:
            >>> from dynasir.models.forecasting.var import VARForecaster
            >>> ForecasterRegistry.register(
            ...     "var",
            ...     VARForecaster,
            ...     aliases=["vector_ar"]
            ... )
        """
        if not name:
            raise ValueError("Backend name cannot be empty")

        if not issubclass(forecaster_class, BaseForecaster):
            raise TypeError(
                f"Forecaster class must inherit from BaseForecaster, "
                f"got {forecaster_class.__name__}"
            )

        if name in cls._forecasters:
            raise ValueError(
                f"Backend '{name}' is already registered. "
                f"Use a different name or unregister the existing backend first."
            )

        # Register the canonical name
        cls._forecasters[name] = forecaster_class

        # Register aliases
        if aliases:
            for alias in aliases:
                if alias in cls._aliases:
                    raise ValueError(
                        f"Alias '{alias}' is already registered for backend "
                        f"'{cls._aliases[alias]}'. Cannot register it for '{name}'."
                    )
                cls._aliases[alias] = name

    @classmethod
    def get(cls, name: str) -> Type[BaseForecaster]:
        """
        Retrieve a forecaster class by name or alias.

        Args:
            name: Backend name or alias (e.g., 'var', 'vector_ar', 'prophet')
                  Case-insensitive lookup

        Returns:
            The forecaster class implementing BaseForecaster

        Raises:
            ValueError: If backend not found, with list of available backends

        Examples:
            >>> # Get by canonical name
            >>> var_class = ForecasterRegistry.get("var")
            >>>
            >>> # Get by alias
            >>> var_class_2 = ForecasterRegistry.get("vector_ar")
            >>> assert var_class is var_class_2  # Same class
            >>>
            >>> # Case insensitive
            >>> var_class_3 = ForecasterRegistry.get("VAR")
            >>> assert var_class is var_class_3
        """
        # Normalize to lowercase for case-insensitive lookup
        name_lower = name.lower()

        # Check aliases first (aliases map to canonical names)
        canonical_name = cls._aliases.get(name_lower, name_lower)

        # Look up the forecaster class
        if canonical_name not in cls._forecasters:
            available = cls.list_available()
            all_names = available + list(cls._aliases.keys())
            raise ValueError(
                f"Forecaster '{name}' not found. "
                f"Available backends: {available}. "
                f"Available aliases: {list(cls._aliases.keys())}. "
                f"All valid names: {sorted(set(all_names))}"
            )

        return cls._forecasters[canonical_name]

    @classmethod
    def list_available(cls) -> List[str]:
        """
        Return list of registered forecaster names (canonical names only).

        Returns:
            Sorted list of backend names

        Examples:
            >>> backends = ForecasterRegistry.list_available()
            >>> print(backends)
            ['arima', 'lstm', 'prophet', 'var']
        """
        return sorted(cls._forecasters.keys())

    @classmethod
    def list_aliases(cls) -> Dict[str, str]:
        """
        Return mapping of all aliases to their canonical names.

        Returns:
            Dictionary mapping alias -> canonical name

        Examples:
            >>> aliases = ForecasterRegistry.list_aliases()
            >>> print(aliases)
            {'vector_ar': 'var', 'vector_autoregression': 'var', ...}
        """
        return dict(cls._aliases)

    @classmethod
    def unregister(cls, name: str) -> None:
        """
        Unregister a forecaster backend.

        This removes the backend and all its aliases from the registry.
        Useful for testing or dynamic backend management.

        Args:
            name: Backend name to unregister

        Raises:
            ValueError: If backend not found

        Examples:
            >>> ForecasterRegistry.unregister("my_backend")
        """
        name_lower = name.lower()

        if name_lower not in cls._forecasters:
            raise ValueError(f"Backend '{name}' not registered")

        # Remove the backend
        del cls._forecasters[name_lower]

        # Remove all aliases pointing to this backend
        aliases_to_remove = [
            alias for alias, target in cls._aliases.items() if target == name_lower
        ]
        for alias in aliases_to_remove:
            del cls._aliases[alias]

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered forecasters and aliases.

        WARNING: This removes all backends including built-in ones.
        Primarily useful for testing.

        Examples:
            >>> ForecasterRegistry.clear()
            >>> print(ForecasterRegistry.list_available())
            []
        """
        cls._forecasters.clear()
        cls._aliases.clear()


def register_forecaster(
    name: str, aliases: Optional[List[str]] = None
) -> Callable[[Type[BaseForecaster]], Type[BaseForecaster]]:
    """
    Decorator for registering a forecaster implementation.

    This provides a clean syntax for registering forecasters at class
    definition time, rather than requiring manual registration calls.

    Args:
        name: Canonical backend name
        aliases: Optional list of alternative names

    Returns:
        Decorator function that registers the class and returns it unchanged

    Examples:
        >>> from dynasir.models.forecasting.base import BaseForecaster
        >>> from dynasir.models.forecasting.registry import register_forecaster
        >>>
        >>> @register_forecaster("var", aliases=["vector_ar", "vector_autoregression"])
        >>> class VARForecaster(BaseForecaster):
        ...     @property
        ...     def backend_name(self) -> str:
        ...         return "var"
        ...
        ...     def create_model(self, **kwargs) -> None:
        ...         # Implementation
        ...         pass
        ...
        ...     def fit(self, **kwargs) -> None:
        ...         # Implementation
        ...         pass
        ...
        ...     def forecast_interval(self, steps: int, **kwargs):
        ...         # Implementation
        ...         pass
        >>>
        >>> # Now the forecaster is automatically registered
        >>> from dynasir.models.forecasting.registry import ForecasterRegistry
        >>> forecaster_class = ForecasterRegistry.get("var")
        >>> print(forecaster_class)
        <class '__main__.VARForecaster'>
    """

    def decorator(cls: Type[BaseForecaster]) -> Type[BaseForecaster]:
        """Register the class and return it unchanged."""
        ForecasterRegistry.register(name, cls, aliases)
        return cls

    return decorator
