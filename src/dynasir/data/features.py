"""
Feature engineering utilities.

This module contains functions for calculating SIRD compartments, epidemiological rates,
and applying transformations (like logit) to prepare data for modeling.
"""

import logging
from typing import Union

import pandas as pd

from dynasir.core.config import get_settings

# Import constants from the core module
from ..core.constants import LOGIT_RATIOS, RATIOS


def prepare_for_logit_function(data: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare rate data for logit transformation by ensuring values are in (0,1).

    Args:
        data: DataFrame containing rate columns

    Returns:
        DataFrame with rates bounded between 0 and 1
    """
    data = data.copy()

    # Ensure rates are within (0,1) bounds for logit transformation
    for ratio in RATIOS:
        if ratio in data.columns:
            # Replace NaN and infinite values
            data[ratio] = data[ratio].replace(
                [float("inf"), -float("inf")], float("nan")
            )

            # Bound values between small epsilon and (1-epsilon)
            epsilon = 1e-10
            data[ratio] = data[ratio].clip(lower=epsilon, upper=1 - epsilon)

    return data


def logit_function(x: Union[float, pd.Series]) -> Union[float, pd.Series]:
    """
    Compute the logit transformation: log(x/(1-x)).

    Args:
        x: Value(s) to transform, must be in (0,1)

    Returns:
        Logit-transformed value(s)
    """
    import numpy as np

    return np.log(x / (1 - x))


def logistic_function(x: Union[float, pd.Series]) -> Union[float, pd.Series]:
    """
    Compute the logistic (inverse logit) transformation: 1/(1+exp(-x)).

    Args:
        x: Value(s) to transform

    Returns:
        Logistic-transformed value(s)
    """
    import numpy as np

    return 1 / (1 + np.exp(-x))


def add_logit_ratios(data: pd.DataFrame) -> pd.DataFrame:
    """
    Add logit-transformed ratio columns to the DataFrame.

    Args:
        data: DataFrame containing rate columns

    Returns:
        DataFrame with additional logit rate columns
    """
    data = data.copy()

    # Add logit transformations for each ratio
    ratio_pairs = list(zip(RATIOS, LOGIT_RATIOS))
    for ratio, logit_ratio in ratio_pairs:
        if ratio in data.columns:
            try:
                data[logit_ratio] = logit_function(data[ratio])
            except Exception as e:
                logging.warning(f"Could not compute logit for {ratio}: {e}")
                data[logit_ratio] = float("nan")

    return data


def feature_engineering(
    data: pd.DataFrame, mode: str = "cumulative", handler=None
) -> pd.DataFrame:
    """
    Perform feature engineering to create SIRD/SIRDV compartments and rate calculations.

    This function calculates:
    - SIRD compartments (S, I, R, D) or SIRDV compartments (S, I, R, D, V)
    - Difference values (dC, dI, dR, dD, dV, etc.)
    - Epidemiological rates (alpha, beta, gamma, delta)
    - R0 calculation
    - Logit transformations of rates

    Args:
        data: Preprocessed DataFrame with basic columns
              - cumulative mode: C, D, N (and optionally V)
              - incidence mode: I, D, N (and optionally V)
        mode: 'cumulative' (default) or 'incidence'
        handler: FrequencyHandler instance for frequency-specific parameters
                (default: None - uses daily defaults). When provided, uses
                handler.get_recovery_lag() instead of settings.RECOVERY_LAG.

    Returns:
        DataFrame with full feature set for epidemiological modeling
    """
    logging.debug(f"Feature engineering mode={mode}, columns={data.columns}")

    # Create a copy to avoid modifying original
    engineered_data = data.copy()

    # Detect vaccination presence
    has_vaccination = "V" in engineered_data.columns
    logging.debug(
        f"Vaccination detection: has_vaccination={has_vaccination}, columns={engineered_data.columns.tolist()}"
    )

    # Fill missing vaccination data with zeros if present
    if has_vaccination:
        engineered_data["V"] = engineered_data["V"].fillna(0)
        logging.info("Detected vaccination data (V column). Using SIRDV model.")
    else:
        logging.info("No vaccination data detected. Using SIRD model.")

    # Mode-specific compartment calculations
    settings = get_settings()

    # Get recovery lag from handler or use settings default
    if handler is not None:
        recovery_lag = handler.get_recovery_lag()
        logging.debug(
            f"Using frequency-specific recovery lag: {recovery_lag} ({handler.frequency_name})"
        )
    else:
        recovery_lag = settings.RECOVERY_LAG
        logging.debug(f"Using default recovery lag: {recovery_lag}")

    if mode == "cumulative":
        # CUMULATIVE MODE: C is cumulative cases (always increasing)
        # Calculate compartments from C
        engineered_data = _calculate_compartments_cumulative(
            engineered_data, has_vaccination, settings, recovery_lag
        )
    elif mode == "incidence":
        # INCIDENCE MODE: I is incident cases (can vary)
        # Calculate compartments from I
        engineered_data = _calculate_compartments_incidence(
            engineered_data, has_vaccination, settings, recovery_lag
        )
    else:
        raise ValueError(f"Invalid mode: {mode}. Must be 'cumulative' or 'incidence'")

    # Calculate epidemiological rates (same for both modes)
    engineered_data = _calculate_rates(engineered_data, has_vaccination)

    # R0: Basic reproduction number
    engineered_data = engineered_data.assign(
        R0=engineered_data["alpha"]
        / (engineered_data["beta"] + engineered_data["gamma"])
    )

    logging.debug(f"When completing assignments, columns are {engineered_data.columns}")

    # Prepare rates for logit transformation and apply it
    engineered_data = prepare_for_logit_function(engineered_data)
    engineered_data = add_logit_ratios(engineered_data)

    # Final cleanup: forward fill then zero fill any remaining NaN values
    engineered_data = engineered_data.ffill().fillna(0)

    logging.debug(
        f"When completing feature engineering, columns are {engineered_data.columns}"
    )

    return engineered_data


def _calculate_compartments_cumulative(
    data: pd.DataFrame, has_vaccination: bool, settings, recovery_lag: float = None
) -> pd.DataFrame:
    """
    Calculate SIRD compartments from cumulative cases C.

    Args:
        data: DataFrame with C, D, N columns
        has_vaccination: Whether V (vaccination) column is present
        settings: Config settings object
        recovery_lag: Recovery lag in periods (can be fractional)
    """
    import numpy as np

    # Use provided recovery_lag or default from settings
    lag = recovery_lag if recovery_lag is not None else settings.RECOVERY_LAG

    # R: Recovered (using recovery_lag with interpolation for fractional)
    if lag == int(lag):
        # Integer lag - use standard shift
        C_lagged = data["C"].shift(int(lag)).fillna(0)
    else:
        # Fractional lag - use weighted interpolation
        lag_floor = int(np.floor(lag))
        lag_ceil = int(np.ceil(lag))
        weight = lag - lag_floor

        C_floor = data["C"].shift(lag_floor).fillna(0)
        C_ceil = data["C"].shift(lag_ceil).fillna(0)

        # Linear interpolation
        C_lagged = (1 - weight) * C_floor + weight * C_ceil

    data = data.assign(R=C_lagged - data["D"])

    # I: Currently infected (active cases)
    data = data.assign(I=data["C"] - data["R"] - data["D"])

    # S: Susceptible population
    if has_vaccination:
        # SIRDV: S = N - C - V
        data = data.assign(S=data["N"] - data["C"] - data["V"])
    else:
        # SIRD: S = N - C
        data = data.assign(S=data["N"] - data["C"])

    # A: At-risk population (S + I)
    data = data.assign(A=data["S"] + data["I"])

    # Calculate differences (changes across periods)
    data = data.assign(dC=-data["C"].diff(periods=-1))
    data = data.assign(dA=-data["A"].diff(periods=-1))
    data = data.assign(dS=-data["S"].diff(periods=-1))
    data = data.assign(dI=-data["I"].diff(periods=-1))
    data = data.assign(dR=-data["R"].diff(periods=-1))
    data = data.assign(dD=-data["D"].diff(periods=-1))

    # Calculate vaccination difference if SIRDV
    if has_vaccination:
        data = data.assign(dV=-data["V"].diff(periods=-1))
        data["dV"] = data["dV"].clip(lower=0)

    return data


def _calculate_compartments_incidence(
    data: pd.DataFrame, has_vaccination: bool, settings, recovery_lag: float = None
) -> pd.DataFrame:
    """
    Calculate SIRD compartments from incident cases I.

    Args:
        data: DataFrame with I, D, N columns
        has_vaccination: Whether V (vaccination) column is present
        settings: Config settings object
        recovery_lag: Recovery lag in periods (can be fractional)
    """
    import numpy as np

    # Use provided recovery_lag or default from settings
    lag = recovery_lag if recovery_lag is not None else settings.RECOVERY_LAG

    # I is already present (incident cases per period)
    # Need to calculate C, R, S, A

    # C: Cumulative cases (cumsum of incident)
    data = data.assign(C=data["I"].cumsum())

    # R: Recovered (cumulative incident minus deaths, lagged)
    # Support fractional lags via interpolation
    if lag == int(lag):
        # Integer lag - use standard shift
        recovered_cumulative = data["I"].shift(int(lag)).fillna(0).cumsum()
    else:
        # Fractional lag - use weighted interpolation
        lag_floor = int(np.floor(lag))
        lag_ceil = int(np.ceil(lag))
        weight = lag - lag_floor

        shifted_floor = data["I"].shift(lag_floor).fillna(0)
        shifted_ceil = data["I"].shift(lag_ceil).fillna(0)

        # Linear interpolation between floor and ceil
        recovered_incident = (1 - weight) * shifted_floor + weight * shifted_ceil
        recovered_cumulative = recovered_incident.cumsum()

    data = data.assign(R=(recovered_cumulative - data["D"]).clip(lower=0))

    # S: Susceptible population
    if has_vaccination:
        # SIRDV: S = N - C - V
        data = data.assign(S=data["N"] - data["C"] - data["V"])
    else:
        # SIRD: S = N - C (simplified, assumes no recovered flow back to S)
        data = data.assign(S=data["N"] - data["C"])

    # A: At-risk population (S + I)
    # For annual data, I represents average active during period
    data = data.assign(A=data["S"] + data["I"])

    # Calculate differences
    # dC is just I (incident cases)
    data = data.assign(dC=data["I"])
    data = data.assign(dA=-data["A"].diff(periods=-1))
    data = data.assign(dS=-data["S"].diff(periods=-1))
    data = data.assign(dI=-data["I"].diff(periods=-1))
    data = data.assign(dR=-data["R"].diff(periods=-1))
    data = data.assign(dD=-data["D"].diff(periods=-1))

    # Calculate vaccination difference if SIRDV
    if has_vaccination:
        data = data.assign(dV=-data["V"].diff(periods=-1))
        data["dV"] = data["dV"].clip(lower=0)

    return data


def _calculate_rates(data: pd.DataFrame, has_vaccination: bool) -> pd.DataFrame:
    """Calculate epidemiological rates (alpha, beta, gamma, delta)."""
    # Alpha: infection rate
    data = data.assign(alpha=(data.A * data.dC) / (data.I * data.S))

    # Beta: recovery rate
    data = data.assign(beta=data.dR / data.I)

    # Gamma: mortality rate
    data = data.assign(gamma=data.dD / data.I)

    # Delta: vaccination rate (SIRDV only)
    if has_vaccination:
        data = data.assign(delta=data.dV / data.S)

    return data
