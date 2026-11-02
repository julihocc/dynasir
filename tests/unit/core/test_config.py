"""
Unit tests for the configuration management system.
"""

import os
from unittest.mock import patch

import pytest

from dynasir.core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear the lru_cache for get_settings before each test."""
    get_settings.cache_clear()
    yield


class TestSettings:
    """Test the Settings class and its behavior."""

    def test_default_settings_load_correctly(self):
        """Ensure default settings are loaded as expected."""
        settings = Settings()
        assert settings.WINDOW_SIZE == 7
        assert settings.RECOVERY_LAG == 14
        assert (
            settings.OWID_DATA_URL
            == "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-19-data.csv"
        )
        assert settings.DEFAULT_ISO_CODES == ["USA", "GBR", "DEU", "FRA", "ITA"]
        assert settings.VAR_MAX_LAG is None
        assert settings.VAR_CRITERION == "aic"
        assert settings.LOG_LEVEL == "INFO"
        assert (
            settings.LOG_FORMAT
            == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def test_environment_variables_override_defaults(self):
        """Test that environment variables can override default settings."""
        with patch.dict(
            os.environ,
            {
                "WINDOW_SIZE": "10",
                "VAR_MAX_LAG": "5",
                "LOG_LEVEL": "DEBUG",
                "DEFAULT_ISO_CODES": '["ARG", "BRA"]',  # Test list parsing
            },
        ):
            settings = Settings()
            assert settings.WINDOW_SIZE == 10
            assert settings.VAR_MAX_LAG == 5
            assert settings.LOG_LEVEL == "DEBUG"
            assert settings.DEFAULT_ISO_CODES == ["ARG", "BRA"]

    def test_get_settings_caches_instance(self):
        """Verify that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

        with patch.dict(os.environ, {"WINDOW_SIZE": "12"}):
            settings3 = get_settings()  # Should still be the cached instance
            assert settings3.WINDOW_SIZE == 7  # Not 12

        get_settings.cache_clear()  # Clear cache to load new settings
        with patch.dict(os.environ, {"WINDOW_SIZE": "12"}):
            settings4 = get_settings()
            assert settings4.WINDOW_SIZE == 12

    def test_missing_env_vars_use_defaults(self):
        """Ensure settings revert to defaults if env vars are removed."""
        # Set some env vars
        os.environ["WINDOW_SIZE"] = "20"
        os.environ["VAR_CRITERION"] = "bic"
        get_settings.cache_clear()
        settings = get_settings()
        assert settings.WINDOW_SIZE == 20
        assert settings.VAR_CRITERION == "bic"

        # Remove env vars and clear cache
        del os.environ["WINDOW_SIZE"]
        del os.environ["VAR_CRITERION"]
        get_settings.cache_clear()
        settings = get_settings()
        assert settings.WINDOW_SIZE == 7
        assert settings.VAR_CRITERION == "aic"

    def test_owid_data_url_and_iso_codes(self):
        """Test OWID specific settings."""
        settings = Settings()
        assert (
            settings.OWID_DATA_URL
            == "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-19-data.csv"
        )
        assert isinstance(settings.DEFAULT_ISO_CODES, list)
        assert "USA" in settings.DEFAULT_ISO_CODES
