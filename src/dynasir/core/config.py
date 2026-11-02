"""
Configuration management for the DynaSIR library.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings for the DynaSIR library.

    Settings are loaded in the following order (with later sources
    overriding earlier ones):
    1. Default values defined in the class.
    2. Environment variables.
    3. .env file (if found).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Data Processing Settings ---
    WINDOW_SIZE: int = Field(7, description="Default window size for data processing.")
    RECOVERY_LAG: int = Field(14, description="Default recovery lag in days.")

    # --- OWID Data Settings ---
    OWID_DATA_URL: str = Field(
        "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-19-data.csv",
        description="URL for the OWID COVID-19 data.",
    )
    DEFAULT_ISO_CODES: List[str] = Field(
        ["USA", "GBR", "DEU", "FRA", "ITA"],
        description="Default ISO codes for data filtering.",
    )

    # --- Model Parameters ---
    VAR_MAX_LAG: Optional[int] = Field(
        None, description="Maximum lag for VAR model (None for auto-selection)."
    )
    VAR_CRITERION: str = Field(
        "aic", description="Criterion for VAR lag order selection (e.g., 'aic', 'bic')."
    )

    # --- Forecasting Backend Settings ---
    DEFAULT_FORECASTER: str = Field(
        "var",
        description="Default forecasting backend ('var', 'prophet', 'arima', 'lstm').",
    )
    FORECASTER_ALPHA: float = Field(
        0.05,
        description="Significance level for confidence intervals (alpha = 0.05 for 95% CI).",
    )

    # --- Prophet Backend Settings ---
    PROPHET_YEARLY_SEASONALITY: bool = Field(
        False,
        description="Enable yearly seasonality in Prophet models.",
    )
    PROPHET_WEEKLY_SEASONALITY: bool = Field(
        False,
        description="Enable weekly seasonality in Prophet models.",
    )
    PROPHET_CHANGEPOINT_PRIOR_SCALE: float = Field(
        0.05,
        description="Flexibility of trend changes in Prophet (higher = more flexible).",
    )

    # --- ARIMA Backend Settings ---
    ARIMA_MAX_P: int = Field(
        5,
        description="Maximum AR order for Auto-ARIMA model selection.",
    )
    ARIMA_MAX_Q: int = Field(
        5,
        description="Maximum MA order for Auto-ARIMA model selection.",
    )
    ARIMA_SEASONAL: bool = Field(
        False,
        description="Enable seasonal ARIMA (SARIMA) models.",
    )

    # --- Logging Settings ---
    LOG_LEVEL: str = Field("INFO", description="Default logging level.")
    LOG_FORMAT: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Default logging format.",
    )

    # --- Parallelization Settings ---
    PARALLEL_SIMULATIONS: bool = Field(
        False,
        description=(
            "Run simulations in a process pool when n_jobs is not given. Off by default: "
            "each scenario takes milliseconds, so starting worker processes usually costs more "
            "than it saves, and on spawn platforms (Windows, macOS) scripts need a __main__ guard."
        ),
    )
    N_SIMULATION_JOBS: Optional[int] = Field(
        None,
        description="Number of parallel jobs for simulations (None = auto-detect CPU count, 1 = sequential).",
    )

    # --- Result Caching Settings ---
    RESULT_CACHING_ENABLED: bool = Field(
        False,
        description="Enable disk caching of generated results (per-configuration cache).",
    )
    CACHE_DIR: str = Field(
        ".dynasir_cache",
        description="Directory to store cache artifacts (per project/machine).",
    )
    CACHE_STRICT_VERSION: bool = Field(
        False,
        description="If true, invalidate cache when package version changes.",
    )

    # --- Vaccination Settings ---
    ENABLE_VACCINATION: bool = Field(
        False,
        description="Enable vaccination compartment (V) in SIRDV model.",
    )
    VACCINATION_COLUMN: str = Field(
        "people_vaccinated",
        description="Column name for vaccination data in OWID dataset.",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get the application settings instance.

    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()
