"""
Feature engineering utilities.

This module contains functions for calculating SIRD compartments, epidemiological rates,
and applying transformations (like logit) to prepare data for modeling.
"""

import logging
from typing import Optional, Union

import pandas as pd

from dynasir.core.config import get_settings

# Import constants from the core module
from ..core.constants import ACTIVE_INFECTIONS, LOGIT_RATIOS, RATIOS

# Log-transformed infection rate used in cohort mode (alpha can exceed 1)
LOG_ALPHA = "log_alpha"


def uses_cohort_semantics(mode: str, recovery_lag: float) -> bool:
    """
    Return True when incidence data is modelled as period cohorts.

    In incidence mode with a recovery lag of at most one period (annual data,
    14/365, and monthly data, 14/30), the cases of period t are the infectious
    cohort for the step from t to t+1, and that cohort is removed by t+1.
    The infection rate is then new cases in t+1 per case in t (scaled by the
    susceptible share), which can exceed 1, so it is modelled on the log scale.

    Args:
        mode: 'cumulative' or 'incidence'
        recovery_lag: Recovery lag in periods

    Returns:
        True for incidence data with recovery_lag <= 1
    """
    return mode == "incidence" and recovery_lag is not None and recovery_lag <= 1


def uses_log_alpha(mode: str) -> bool:
    """Return True when alpha is a growth ratio that can exceed 1.

    Every incidence series uses that form. Cumulative series keep alpha inside
    (0, 1) and forecast its logit. This is independent of period-cohort
    semantics: a weekly stock can produce alpha > 1 without the whole stock
    leaving in one period.
    """
    return mode == "incidence"


def get_forecast_columns(columns, cohort: Optional[bool] = None) -> list:
    """
    Return the transformed rate columns that a forecaster should model.

    ``log_alpha`` means alpha is forecast on the log scale. It does not by
    itself mean period-cohort semantics. Cohort data omits ``logit_beta``
    because beta = 1 - gamma. Other series that use ``log_alpha`` still
    forecast ``logit_beta``.

    Args:
        columns: Column names of a feature-engineered DataFrame
        cohort: Period-cohort incidence. When omitted, inferred as
            ``log_alpha`` present and ``logit_beta`` absent.

    Returns:
        List of column names in forecasting order
    """
    columns = list(columns)
    if cohort is None:
        cohort = LOG_ALPHA in columns and "logit_beta" not in columns
    if LOG_ALPHA in columns:
        names = [LOG_ALPHA]
        if not cohort:
            names.append("logit_beta")
        names.extend(["logit_gamma", "logit_delta"])
    else:
        names = list(LOGIT_RATIOS)
    return [name for name in names if name in columns]


def prepare_for_logit_function(
    data: pd.DataFrame, cohort: bool = False, log_alpha: bool = False
) -> pd.DataFrame:
    """
    Prepare rate data for logit transformation by ensuring values are in (0,1).

    Args:
        data: DataFrame containing rate columns
        cohort: Kept for callers that have not passed ``log_alpha``. Alpha is
            only bounded below when it is log-transformed.
        log_alpha: If True, alpha can exceed 1 and is only bounded below.

    Returns:
        DataFrame with rates bounded between 0 and 1 (alpha bounded below
        only when it is log-transformed)
    """
    data = data.copy()
    unbounded_alpha = cohort or log_alpha

    # Ensure rates are within (0,1) bounds for logit transformation
    epsilon = 1e-10
    for ratio in RATIOS:
        if ratio in data.columns:
            # Replace NaN and infinite values
            data[ratio] = data[ratio].replace(
                [float("inf"), -float("inf")], float("nan")
            )

            if unbounded_alpha and ratio == "alpha":
                data[ratio] = data[ratio].clip(lower=epsilon)
            else:
                # Bound values between small epsilon and (1-epsilon)
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


def add_logit_ratios(
    data: pd.DataFrame, cohort: bool = False, log_alpha: bool = False
) -> pd.DataFrame:
    """
    Add logit-transformed ratio columns to the DataFrame.

    Args:
        data: DataFrame containing rate columns
        cohort: If True, add ``log_alpha`` instead of ``logit_alpha`` and no
            ``logit_beta`` (beta is derived as 1 - gamma)
        log_alpha: If True, and this is not cohort data, add ``log_alpha``
            instead of ``logit_alpha`` and still add ``logit_beta``.

    Returns:
        DataFrame with additional logit rate columns
    """
    import numpy as np

    data = data.copy()
    use_log_alpha = cohort or log_alpha

    if use_log_alpha and "alpha" in data.columns:
        data[LOG_ALPHA] = np.log(data["alpha"])

    # Add logit transformations for each ratio
    ratio_pairs = list(zip(RATIOS, LOGIT_RATIOS))
    for ratio, logit_ratio in ratio_pairs:
        if cohort and ratio in ("alpha", "beta"):
            continue
        if use_log_alpha and ratio == "alpha":
            continue
        if ratio in data.columns:
            try:
                data[logit_ratio] = logit_function(data[ratio])
            except Exception as e:
                logging.warning(f"Could not compute logit for {ratio}: {e}")
                data[logit_ratio] = float("nan")

    return data


def feature_engineering(
    data: pd.DataFrame,
    mode: str = "cumulative",
    handler=None,
    incidence_offset: float = 0.0,
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
        incidence_offset: Constant added to case counts (I and next-period
                cases dC) inside the rate formulas in incidence mode, so that
                zero-case periods give defined rates (default 0)

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

    cohort = uses_cohort_semantics(mode, recovery_lag)
    log_alpha = uses_log_alpha(mode)
    if cohort:
        logging.debug(
            f"Incidence data with recovery lag {recovery_lag} <= 1 period: "
            "using period-cohort rates"
        )

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
            engineered_data, has_vaccination, settings, recovery_lag, cohort=cohort
        )
    else:
        raise ValueError(f"Invalid mode: {mode}. Must be 'cumulative' or 'incidence'")

    # Calculate epidemiological rates (same for both modes)
    offset = incidence_offset if mode == "incidence" else 0.0
    engineered_data = _calculate_rates(
        engineered_data, has_vaccination, cohort=cohort, offset=offset
    )

    # R0: Basic reproduction number
    engineered_data = engineered_data.assign(
        R0=engineered_data["alpha"]
        / (engineered_data["beta"] + engineered_data["gamma"])
    )

    logging.debug(f"When completing assignments, columns are {engineered_data.columns}")

    # Prepare rates for logit transformation and apply it
    engineered_data = prepare_for_logit_function(
        engineered_data, log_alpha=log_alpha
    )
    engineered_data = add_logit_ratios(
        engineered_data, cohort=cohort, log_alpha=log_alpha
    )

    # Count undefined rates (division by zero) that the fill below replaces.
    # The last row has no next period, so its rates are always undefined.
    present = [r for r in RATIOS if r in engineered_data.columns]
    n_filled = int(engineered_data[present].iloc[:-1].isna().sum().sum())

    # Final cleanup: forward fill then zero fill any remaining NaN values
    engineered_data = engineered_data.ffill().fillna(0)
    engineered_data.attrs["n_filled_rates"] = n_filled

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
    data: pd.DataFrame,
    has_vaccination: bool,
    settings,
    recovery_lag: float = None,
    cohort: bool = False,
) -> pd.DataFrame:
    """
    Calculate SIRD compartments from incident cases I.

    ``I`` stays the period incidence. The active-infection stock, which the
    rates divide by, is ``I_active``:

    - cohort mode (recovery lag <= 1 period): each period's cases are the
      whole infectious cohort, so ``I_active = I`` and ``R = C - I - D``;
    - longer lags (daily, business-day, weekly data): ``C = cumsum(I)`` and
      the compartments follow cumulative mode, ``R = C_lagged - D`` and
      ``I_active = C - C_lagged``, the cases of the last ``recovery_lag``
      periods. ``C = I_active + R + D`` holds in every row (#178).

    Args:
        data: DataFrame with I, D, N columns
        has_vaccination: Whether V (vaccination) column is present
        settings: Config settings object
        recovery_lag: Recovery lag in periods (can be fractional)
        cohort: If True, every earlier cohort has been removed by period t,
            so R = C - I - D (see uses_cohort_semantics)
    """
    # Use provided recovery_lag or default from settings
    lag = recovery_lag if recovery_lag is not None else settings.RECOVERY_LAG

    incidence = data["I"]

    if not cohort:
        # Rolling stock of the last `lag` periods, as in cumulative mode
        cumulative = data.drop(columns=["I"]).assign(C=incidence.cumsum())
        data = _calculate_compartments_cumulative(
            cumulative, has_vaccination, settings, lag
        )
        data = data.rename(columns={"I": ACTIVE_INFECTIONS, "dI": "dI_active"})
        # C - C_lagged leaves rounding error (about 1e-12) where no case is
        # active; set it to zero so that undefined rates are detected
        stock = data[ACTIVE_INFECTIONS]
        stock = stock.where(stock.abs() > 1e-9 * data["C"].abs().clip(lower=1), 0.0)
        data = data.assign(
            **{ACTIVE_INFECTIONS: stock},
            R=data["C"] - stock - data["D"],
        )
        data = data.assign(A=data["S"] + data[ACTIVE_INFECTIONS])
        data = data.assign(dA=-data["A"].diff(periods=-1))
        data = data.assign(dR=-data["R"].diff(periods=-1))
        data = data.assign(dI_active=-data[ACTIVE_INFECTIONS].diff(periods=-1))
        data.insert(0, "I", incidence)
        data = data.assign(dI=-data["I"].diff(periods=-1))
        return data

    # C: Cumulative cases (cumsum of incident)
    data = data.assign(C=incidence.cumsum())

    # All cohorts before t have been removed: R_t = C_(t-1) - D_t
    recovered_cumulative = data["C"] - incidence
    data = data.assign(R=(recovered_cumulative - data["D"]).clip(lower=0))

    # S: Susceptible population
    if has_vaccination:
        # SIRDV: S = N - C - V
        data = data.assign(S=data["N"] - data["C"] - data["V"])
    else:
        # SIRD: S = N - C (simplified, assumes no recovered flow back to S)
        data = data.assign(S=data["N"] - data["C"])

    # The period's cases are the infectious cohort
    data = data.assign(**{ACTIVE_INFECTIONS: incidence})

    # A: At-risk population (S + I)
    data = data.assign(A=data["S"] + data["I"])

    # Calculate forward differences: dX_t = X_(t+1) - X_t
    # dC_t = I_(t+1), the new cases of the next period
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


def _calculate_rates(
    data: pd.DataFrame,
    has_vaccination: bool,
    cohort: bool = False,
    offset: float = 0.0,
) -> pd.DataFrame:
    """
    Calculate epidemiological rates (alpha, beta, gamma, delta).

    The rate in row t describes the step from t to t+1, so the last row has
    no rate. In cohort mode (see uses_cohort_semantics) gamma is the share of
    the next cohort that dies, and beta = 1 - gamma: the whole cohort of
    period t leaves I by t+1.

    ``offset`` is added to the case counts (I and dC) in the formulas, so
    that zero-case periods give defined rates.
    """
    # Infectious stock: I_active in incidence mode, I in cumulative mode
    stock = data[ACTIVE_INFECTIONS] if ACTIVE_INFECTIONS in data.columns else data.I
    cases = stock + offset
    new_cases = data.dC + offset

    # Alpha: infection rate
    data = data.assign(alpha=(data.A * new_cases) / (cases * data.S))

    if cohort:
        # Gamma: deaths in t+1 per new case in t+1; beta: the rest of the cohort
        data = data.assign(gamma=data.dD / new_cases)
        data = data.assign(beta=1 - data.gamma)
    else:
        # Beta: recovery rate
        data = data.assign(beta=data.dR / cases)

        # Gamma: mortality rate
        data = data.assign(gamma=data.dD / cases)

    # Delta: vaccination rate (SIRDV only)
    if has_vaccination:
        data = data.assign(delta=data.dV / data.S)

    return data
