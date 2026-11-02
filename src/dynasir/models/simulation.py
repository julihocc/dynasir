"""
Epidemic simulation engine.
"""

import itertools
import logging
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from box import Box
from scipy.stats import gmean, hmean

from ..core.config import get_settings
from ..core.constants import COMPARTMENTS, FORECASTING_LEVELS


def _warn_if_flat_median_incidence_forecast(
    data: pd.DataFrame, results: Dict[str, pd.DataFrame]
) -> None:
    if "I" not in results or "I" not in data:
        return

    historical = data["I"].dropna().to_numpy()
    median_forecast = results["I"]["median"].to_numpy()
    if (
        len(historical) > 1
        and np.ptp(historical) > 0
        and len(median_forecast) > 1
        and np.allclose(median_forecast, median_forecast[0])
    ):
        logging.warning(
            "The median infected forecast is flat across %d periods despite "
            "variation in the training data. This does not rule out future "
            "outbreaks; interpret the forecast cautiously and consider "
            "additional data or external importation assumptions.",
            len(median_forecast),
        )


def _run_single_simulation(
    data: pd.DataFrame,
    forecasting_box: Dict[str, pd.DataFrame],
    forecasting_interval: pd.DatetimeIndex,
    simulation_levels: Tuple[str, ...],
    importation_rate: float = 0.0,
) -> Tuple[Tuple[str, ...], pd.DataFrame]:
    """
    Helper function to run a single simulation scenario.

    This function is defined at module level to support pickling for multiprocessing.

    Args:
        data: Historical epidemic data
        forecasting_box: Dictionary with forecasted rate values
        forecasting_interval: Time index for forecast period
        simulation_levels: Tuple of rate levels (3 for SIRD, 4 for SIRDV)
            SIRD: (alpha_level, beta_level, gamma_level)
            SIRDV: (alpha_level, beta_level, gamma_level, delta_level)
        importation_rate: External force of infection (epsilon)

    Returns:
        Tuple of (simulation_levels, simulation_dataframe)
    """
    # Create temporary simulation object to use its method
    temp_sim = EpidemicSimulation(
        data, forecasting_box, forecasting_interval, importation_rate=importation_rate
    )
    result = temp_sim.simulate_for_given_levels(simulation_levels)
    return (simulation_levels, result)


class EpidemicSimulation:
    """
    Encapsulates the epidemic simulation logic extracted from the Model class.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        forecasting_box: Dict[str, pd.DataFrame],
        forecasting_interval: pd.DatetimeIndex,
        importation_rate: float = 0.0,
    ):
        self.data = data
        self.forecasting_box = forecasting_box
        self.forecasting_interval = forecasting_interval
        self.importation_rate = importation_rate

        # Detect if we have vaccination (delta rate present)
        self.has_vaccination = "delta" in forecasting_box
        if self.has_vaccination:
            logging.info("Simulation initialized with vaccination (SIRDV mode)")
        else:
            logging.info("Simulation initialized without vaccination (SIRD mode)")

        if self.importation_rate > 0:
            logging.info(f"Importation enabled (rate={self.importation_rate})")

        self.simulation: Optional[Box] = None
        self.results: Optional[Box] = None

    def simulate_for_given_levels(
        self, simulation_levels: Tuple[str, ...]
    ) -> pd.DataFrame:
        """
        Simulate epidemic dynamics for given rate confidence levels.

        Args:
            simulation_levels: Tuple of rate levels (3 for SIRD, 4 for SIRDV)
                SIRD: (alpha_level, beta_level, gamma_level)
                SIRDV: (alpha_level, beta_level, gamma_level, delta_level)

        Returns:
            DataFrame with simulated compartment values
        """
        # Get initial state from the last historical data point
        last_hist = self.data.iloc[-1]

        # Current state variables
        S = last_hist.S
        I = last_hist.I
        R = last_hist.R
        D = last_hist.D
        # A and C are also needed (A used in alpha term)
        A = last_hist.A
        C = last_hist.C

        # Initialize V if vaccination is present
        if self.has_vaccination:
            V = last_hist.V if "V" in last_hist.index else 0
        else:
            V = 0

        # Current rates (from history) used for the first step calculation
        alpha = last_hist.alpha
        beta = last_hist.beta
        gamma = last_hist.gamma
        if self.has_vaccination:
            delta = last_hist.delta if "delta" in last_hist.index else 0
        else:
            delta = 0

        # Get forecasted rates as numpy arrays for performance
        forecast_alphas = (
            self.forecasting_box["alpha"][simulation_levels[0]]
            .loc[self.forecasting_interval]
            .values
        )
        forecast_betas = (
            self.forecasting_box["beta"][simulation_levels[1]]
            .loc[self.forecasting_interval]
            .values
        )
        forecast_gammas = (
            self.forecasting_box["gamma"][simulation_levels[2]]
            .loc[self.forecasting_interval]
            .values
        )
        if self.has_vaccination:
            forecast_deltas = (
                self.forecasting_box["delta"][simulation_levels[3]]
                .loc[self.forecasting_interval]
                .values
            )
        else:
            forecast_deltas = None

        n_steps = len(self.forecasting_interval)

        # Pre-allocate result arrays
        # SIRD: A, C, S, I, R, D, alpha, beta, gamma (9 columns)
        # SIRDV: A, C, S, I, R, D, V, alpha, beta, gamma, delta (11 columns)
        n_cols = 11 if self.has_vaccination else 9
        results = np.zeros((n_steps, n_cols))

        for i in range(n_steps):
            # Dynamics using CURRENT (previous step's) state and rates
            # Calculate flows
            # Force of Infection = alpha * I / A + epsilon (importation)
            # New Infections = FoI * S
            force_of_infection = (alpha * I / A) + self.importation_rate
            infection = force_of_infection * S

            recovery = beta * I
            death = gamma * I

            if self.has_vaccination:
                # Vaccination flow: delta * S
                vaccination = delta * S
                # Update S with both infection and vaccination
                new_S = S - infection - vaccination
                new_V = V + vaccination
            else:
                # SIRD: S only reduced by infection
                new_S = S - infection
                new_V = 0

            # I(t) = I(t-1) + infection - recovery - death
            new_I = I + infection - recovery - death
            new_R = R + recovery
            new_D = D + death

            new_C = new_I + new_R + new_D
            new_A = new_S + new_I

            # Get the rates for THIS forecasted step (to be used in NEXT iteration)
            new_alpha = forecast_alphas[i]
            new_beta = forecast_betas[i]
            new_gamma = forecast_gammas[i]
            if self.has_vaccination:
                new_delta = forecast_deltas[i]

            # Store results
            results[i, 0] = new_A
            results[i, 1] = new_C
            results[i, 2] = new_S
            results[i, 3] = new_I
            results[i, 4] = new_R
            results[i, 5] = new_D
            if self.has_vaccination:
                results[i, 6] = new_V
                results[i, 7] = new_alpha
                results[i, 8] = new_beta
                results[i, 9] = new_gamma
                results[i, 10] = new_delta
            else:
                results[i, 6] = new_alpha
                results[i, 7] = new_beta
                results[i, 8] = new_gamma

            # Update state for next iteration
            S, I, R, D, A, C = new_S, new_I, new_R, new_D, new_A, new_C
            alpha, beta, gamma = new_alpha, new_beta, new_gamma
            if self.has_vaccination:
                V = new_V
                delta = new_delta

        # Create DataFrame from results
        if self.has_vaccination:
            columns = [
                "A",
                "C",
                "S",
                "I",
                "R",
                "D",
                "V",
                "alpha",
                "beta",
                "gamma",
                "delta",
            ]
        else:
            columns = ["A", "C", "S", "I", "R", "D", "alpha", "beta", "gamma"]

        simulation_df = pd.DataFrame(
            results, index=self.forecasting_interval, columns=columns
        )

        return simulation_df

    def create_simulation_box(self) -> None:
        """
        Create nested Box structure for storing simulation results.

        Creates 3D structure for SIRD (27 scenarios) or 4D for SIRDV (81 scenarios).
        """
        self.simulation = Box()
        for logit_alpha_level in FORECASTING_LEVELS:
            self.simulation[logit_alpha_level] = Box()
            for logit_beta_level in FORECASTING_LEVELS:
                self.simulation[logit_alpha_level][logit_beta_level] = Box()
                for logit_gamma_level in FORECASTING_LEVELS:
                    if self.has_vaccination:
                        # 4D structure for SIRDV
                        self.simulation[logit_alpha_level][logit_beta_level][
                            logit_gamma_level
                        ] = Box()
                        for logit_delta_level in FORECASTING_LEVELS:
                            self.simulation[logit_alpha_level][logit_beta_level][
                                logit_gamma_level
                            ][logit_delta_level] = None
                    else:
                        # 3D structure for SIRD
                        self.simulation[logit_alpha_level][logit_beta_level][
                            logit_gamma_level
                        ] = None

    def run_simulations(self, n_jobs: Optional[int] = None) -> None:
        """
        Run epidemic simulations for all combinations of rate confidence levels.

        Execution modes:
        - n_jobs=None: use the configured default. This is sequential unless the
          ``PARALLEL_SIMULATIONS`` setting is enabled, in which case
          ``N_SIMULATION_JOBS`` (or the CPU count) workers are used.
        - n_jobs=1: sequential execution.
        - n_jobs>1: a process pool with that many workers.

        Each scenario takes milliseconds, so a process pool rarely pays off: on
        Windows and macOS, where workers are started with ``spawn``, starting
        them usually costs far more than the simulations themselves. Spawned
        workers also re-import the calling script, so scripts that request
        parallel execution need an ``if __name__ == "__main__":`` guard. If the
        pool breaks (for example because that guard is missing), the
        simulations are rerun sequentially and a warning is logged.

        Args:
            n_jobs: Number of parallel jobs (None for the configured default,
                1 for sequential, >1 for a process pool with that many workers).

        Raises:
            ValueError: If n_jobs < 1

        Examples:
            >>> sim.run_simulations()  # Configured default (sequential)
            >>> sim.run_simulations(n_jobs=1)  # Sequential
            >>> sim.run_simulations(n_jobs=4)  # 4 worker processes
        """
        if n_jobs is not None and n_jobs < 1:
            raise ValueError("n_jobs must be None or >= 1")

        if n_jobs is None:
            settings = get_settings()
            if settings.PARALLEL_SIMULATIONS:
                n_jobs = settings.N_SIMULATION_JOBS or mp.cpu_count()
            else:
                n_jobs = 1

        self.create_simulation_box()

        # SIRD: 27 scenarios (3^3), SIRDV: 81 scenarios (3^4)
        n_rates = 4 if self.has_vaccination else 3
        scenarios = list(itertools.product(FORECASTING_LEVELS, repeat=n_rates))
        logging.info(
            f"Running {len(scenarios)} {'SIRDV' if self.has_vaccination else 'SIRD'} "
            f"scenarios (3^{n_rates})"
        )

        if n_jobs == 1:
            self._run_sequential(scenarios)
            return

        try:
            self._run_parallel(scenarios, n_jobs)
        except BrokenProcessPool:
            logging.warning(
                "The simulation process pool broke (a worker process exited unexpectedly), "
                "so the simulations were rerun sequentially. On Windows and macOS worker "
                "processes re-import the calling script; put the code that runs simulations "
                'under an `if __name__ == "__main__":` guard, or use n_jobs=1 (the default).'
            )
            self.create_simulation_box()
            self._run_sequential(scenarios)

    def _run_sequential(self, scenarios) -> None:
        for levels in scenarios:
            self._store_simulation(levels, self.simulate_for_given_levels(levels))

    def _run_parallel(self, scenarios, n_jobs: int) -> None:
        with ProcessPoolExecutor(max_workers=n_jobs) as executor:
            futures = [
                executor.submit(
                    _run_single_simulation,
                    self.data,
                    self.forecasting_box,
                    self.forecasting_interval,
                    scenario,
                    self.importation_rate,
                )
                for scenario in scenarios
            ]
            for future in as_completed(futures):
                self._store_simulation(*future.result())

    def _store_simulation(self, levels, simulation_result: pd.DataFrame) -> None:
        """Store one scenario's result in the nested simulation box."""
        node = self.simulation
        for level in levels[:-1]:
            node = node[level]
        node[levels[-1]] = simulation_result

    def create_results_dataframe(self, compartment: str) -> pd.DataFrame:
        """
        Create results DataFrame for a specific compartment.

        Args:
            compartment: Compartment code (A, C, S, I, R, D, V)

        Returns:
            DataFrame with simulation results and central tendencies
        """
        results_dataframe = pd.DataFrame()
        logging.debug(results_dataframe.head())

        if self.has_vaccination:
            # 4D iteration for SIRDV
            levels_interactions = itertools.product(
                FORECASTING_LEVELS,
                FORECASTING_LEVELS,
                FORECASTING_LEVELS,
                FORECASTING_LEVELS,
            )

            for (
                logit_alpha_level,
                logit_beta_level,
                logit_gamma_level,
                logit_delta_level,
            ) in levels_interactions:
                column_name = f"{logit_alpha_level}|{logit_beta_level}|{logit_gamma_level}|{logit_delta_level}"
                simulation = self.simulation[logit_alpha_level][logit_beta_level][
                    logit_gamma_level
                ][logit_delta_level]
                results_dataframe[column_name] = simulation[compartment].values
        else:
            # 3D iteration for SIRD
            levels_interactions = itertools.product(
                FORECASTING_LEVELS, FORECASTING_LEVELS, FORECASTING_LEVELS
            )

            for (
                logit_alpha_level,
                logit_beta_level,
                logit_gamma_level,
            ) in levels_interactions:
                column_name = (
                    f"{logit_alpha_level}|{logit_beta_level}|{logit_gamma_level}"
                )
                simulation = self.simulation[logit_alpha_level][logit_beta_level][
                    logit_gamma_level
                ]
                results_dataframe[column_name] = simulation[compartment].values

        results_dataframe["mean"] = results_dataframe.mean(axis=1)
        results_dataframe["median"] = results_dataframe.median(axis=1)
        results_dataframe["gmean"] = results_dataframe.apply(gmean, axis=1)
        results_dataframe["hmean"] = results_dataframe.apply(hmean, axis=1)

        results_dataframe.index = self.forecasting_interval

        return results_dataframe

    def generate_result(self) -> None:
        """Generate results for all compartments."""
        self.results = Box()

        # Get available compartments from a sample simulation (they're all the same)
        if self.has_vaccination:
            sample_simulation = self.simulation[FORECASTING_LEVELS[0]][
                FORECASTING_LEVELS[0]
            ][FORECASTING_LEVELS[0]][FORECASTING_LEVELS[0]]
        else:
            sample_simulation = self.simulation[FORECASTING_LEVELS[0]][
                FORECASTING_LEVELS[0]
            ][FORECASTING_LEVELS[0]]

        available_compartments = [
            c for c in COMPARTMENTS if c in sample_simulation.columns
        ]

        for compartment in available_compartments:
            self.results[compartment] = self.create_results_dataframe(compartment)

        if self.results is not None:
            _warn_if_flat_median_incidence_forecast(self.data, self.results)
