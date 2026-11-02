"""
Core constants for the DynaSIR library.
"""

RATIOS = ["alpha", "beta", "gamma", "delta"]
LOGIT_RATIOS = ["logit_alpha", "logit_beta", "logit_gamma", "logit_delta"]
FORECASTING_LEVELS = ["lower", "point", "upper"]
COMPARTMENTS = ["A", "C", "S", "I", "R", "D", "V"]
COMPARTMENT_LABELS = {
    "A": "Active",
    "C": "Confirmed",
    "S": "Susceptible",
    "I": "Infected",
    "R": "Recovered",
    "D": "Deaths",
    "V": "Vaccinated",
}
CENTRAL_TENDENCY_METHODS = ["mean", "median", "gmean", "hmean"]
METHOD_NAMES = {
    "mean": "Mean",
    "median": "Median",
    "gmean": "Geometric Mean",
    "hmean": "Harmonic Mean",
}
METHOD_COLORS = {
    "mean": "blue",
    "median": "orange",
    "gmean": "green",
    "hmean": "purple",
}

# --- Multi-Frequency Support (v0.8.0+) ---
FREQUENCY_ALIASES = {
    "D": "daily",
    "W": "weekly",
    "M": "monthly",
    "Y": "annual",
    "A": "annual",  # Pandas uses 'A' for annual
    "daily": "D",
    "weekly": "W",
    "monthly": "M",
    "annual": "Y",
}

SUPPORTED_FREQUENCIES = ["D", "W", "M", "Y", "A"]

DEFAULT_FREQUENCY = "D"

# Modern pandas frequency aliases (to avoid FutureWarnings)
# Maps deprecated aliases to their modern equivalents
MODERN_FREQUENCY_ALIASES = {
    "Y": "YE",  # Year-end
    "A": "YE",  # Annual (year-end)
    "M": "ME",  # Month-end
    "W": "W",  # Weekly (no change)
    "D": "D",  # Daily (no change)
}

# Recovery lag mappings by frequency
# Biological constant: Measles recovery ≈ 14 days
# Converted to appropriate units for each frequency
RECOVERY_LAG_BY_FREQUENCY = {
    "D": 14,  # 14 days
    "W": 2,  # 2 weeks
    "M": 0.5,  # ~0.5 months (approximately 2 weeks)
    "Y": 0.038,  # 14/365 years
    "A": 0.038,  # Same as 'Y'
}
