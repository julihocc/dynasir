import itertools
import logging
import numpy as np
from box import Box
import pandas as pd
from matplotlib import pyplot as plt
from scipy.stats import gmean, hmean
from statsmodels.tsa.api import VAR
from sklearn.metrics import mean_absolute_error, mean_squared_error
import json

logging.basicConfig(level=logging.INFO)
logging.getLogger("matplotlib").setLevel(logging.WARNING)

ratios = ["alpha", "beta", "gamma"]
logit_ratios = ["logit_alpha", "logit_beta", "logit_gamma"]
forecasting_levels = ["lower", "point", "upper"]
compartments = ["A", "C", "S", "I", "R", "D"]
compartment_labels = {
    "A": "Active",
    "C": "Confirmed",
    "S": "Susceptible",
    "I": "Infected",
    "R": "Recovered",
    "D": "Deaths",
}
central_tendency_methods = ["mean", "median", "gmean", "hmean"]
method_names = {"mean": "Mean", "median": "Median", "gmean": "Geometric Mean", "hmean": "Harmonic Mean"}
method_colors = {
    "mean": "blue",
    "median": "orange",
    "gmean": "green",
    "hmean": "purple",
}


def prepare_for_logit_function(data):
    logging.debug(f"Filtering data for {logit_ratios}")
    logging.debug(f"alpha min:{data['alpha'].min()} max:{data['alpha'].max()}")
    logging.debug(f"beta min:{data['beta'].min()} max:{data['beta'].max()}")
    logging.debug(f"gamma min:{data['gamma'].min()} max:{data['gamma'].max()}")

    for placeholder in ["alpha", "beta", "gamma"]:
        data[placeholder] = (data[placeholder]
                             .apply(lambda x: x if x > 0 else np.nan)
                             .apply(lambda x: x if x < 1 else np.nan))
        data[placeholder] = data[placeholder].fillna(method="ffill").fillna(method="bfill")

    return data


def logit_function(x):
    return np.log(x / (1 - x))


def logistic_function(x):
    return 1 / (1 + np.exp(-x))


def add_logit_ratios(data):
    data.loc[:, "logit_alpha"] = logit_function(data["alpha"])
    data.loc[:, "logit_beta"] = logit_function(data["beta"])
    data.loc[:, "logit_gamma"] = logit_function(data["gamma"])
    return data


class NotDataFrameError(Exception):
    """Custom exception for when the input is not a Pandas DataFrame."""

    pass


def validate_data(training_data):
    if not isinstance(training_data, pd.DataFrame):
        raise NotDataFrameError("raw data must be a pandas DataFrame")


def process_data_from_owid(
        url="https://covid.ourworldindata.org/data/owid-covid-data.csv",
        iso_code="OWID_WRL"):
    try:
        data = pd.read_csv(url)
    except Exception as e:
        raise Exception(f"Could not download data from {url}: {e}")

    try:
        data = data[data["iso_code"] == iso_code]
    except Exception as e:
        raise Exception(f"Could not filter data for {iso_code}: {e}")

    try:
        data = data[["date", "total_cases", "total_deaths", "population"]]
    except ValueError:
        raise ValueError("Dataframe has not the required columns")

    try:
        data.set_index("date", inplace=True)
    except ValueError:
        raise ValueError("Date could not be set as index")

    try:
        data.index = pd.DatetimeIndex(data.index)
    except Exception:
        raise Exception("Date could not be set as DatetimeIndex")

    try:
        data.columns = [
            "C",
            "D",
            "N",
        ]
    except ValueError:
        raise ValueError("Columns on reduced dataframe could not be renamed")

    # try:
    #     data = data[data["C"] > 0]
    # except ValueError:
    #     raise ValueError("No confirmed cases found")

    return data


def preprocess_data(data, window=7):
    data = data.rolling(window=window).mean()[window:]
    data = reindex_data(data)
    return data


def reindex_data(data, start=None, stop=None):
    start = pd.to_datetime(start) if start is not None else data.index.min()
    stop = pd.to_datetime(stop) if stop is not None else data.index.max()

    if start > stop:
        raise ValueError("Start date is after stop date")

    if start < data.index[0]:
        raise ValueError("Start date is before first date on confirmed cases")

    if stop > data.index[-1]:
        raise ValueError("Stop date is after last date of updated cases")

    try:
        logging.debug(f"Reindex data from {start} to {stop} shape: {data.shape}")
        reindex = pd.date_range(start=start, end=stop, freq="D")
        data = data.reindex(reindex)
    except Exception as e:
        raise Exception(f"Could not reindex data: {e}")

    try:
        data = data.fillna(method="ffill")
    except Exception as e:
        raise Exception(f"Could not fill missing values: {e}")

    try:
        data = data.fillna(0)
    except Exception as e:
        raise Exception(f"Could not fill missing values: {e}")

    try:
        data = data.loc[start:]
    except KeyError:
        raise KeyError("Initial date not found")

    try:
        data = data.loc[:stop]
    except KeyError:
        raise KeyError("Final date not found")

    return data


def feature_engineering(data):
    logging.debug(f"When starting feature engineering, columns are {data.columns}")
    data = data.assign(R=data["C"].shift(14).fillna(0) - data["D"])
    data = data.assign(I=data["C"] - data["R"] - data["D"])
    data = data.assign(S=data["N"] - data["C"])
    data = data.assign(A=data["S"] + data["I"])
    data = data.assign(dC=-data["C"].diff(periods=-1))
    data = data.assign(dA=-data["A"].diff(periods=-1))
    data = data.assign(dS=-data["S"].diff(periods=-1))
    data = data.assign(dI=-data["I"].diff(periods=-1))
    data = data.assign(dR=-data["R"].diff(periods=-1))
    data = data.assign(dD=-data["D"].diff(periods=-1))
    data = data.assign(alpha=(data.A * data.dC) / (data.I * data.S))
    data = data.assign(beta=data.dR / data.I)
    data = data.assign(gamma=data.dD / data.I)
    data = data.assign(R0=data["alpha"] / (data["beta"] + data["gamma"]))
    logging.debug(f"When completing assignments, columns are {data.columns}")
    data = prepare_for_logit_function(data)
    data = add_logit_ratios(data)

    data = data.fillna(method="ffill").fillna(0)
    logging.debug(f"When completing feature engineering, columns are {data.columns}")

    return data


class DataContainer:
    def __init__(
            self,
            raw_data,
            window=7
    ):
        self.raw_data = raw_data
        self.window = window

        validate_data(self.raw_data)
        self.data = preprocess_data(self.raw_data)
        logging.debug(f"Preprocessed data columns: {self.data.columns}")
        self.data = feature_engineering(self.data)
        logging.debug(f"Feature engineered data columns: {self.data.columns}")
        logging.debug(f"Data shape: {self.data.shape}")


class Model:
    def __init__(self, data_container, start=None, stop=None, days_to_forecast=None):

        self.data = None
        self.data_container = data_container
        self.window = data_container.window
        self.start = start
        self.stop = stop
        self.results = None
        self.simulation = None
        self.forecasting_box = None
        self.forecasted_logit_ratios_tuple_arrays = None
        self.forecasting_interval = None
        self.forecast_index_stop = None
        self.forecast_index_start = None
        self.days_to_forecast = days_to_forecast
        self.logit_ratios_model = None
        self.logit_ratios_model_fitted = None
        self.forecasted_logit_ratios = None

        self.data = reindex_data(data_container.data, start, stop)
        self.logit_ratios_values = self.data[logit_ratios].values

    def create_logit_ratios_model(self, *args, **kwargs):
        self.logit_ratios_model = VAR(self.logit_ratios_values, *args, **kwargs)

    def fit_logit_ratios_model(self, *args, **kwargs):
        self.logit_ratios_model_fitted = self.logit_ratios_model.fit(*args, **kwargs)
        if self.days_to_forecast is None:
            self.days_to_forecast = self.logit_ratios_model_fitted.k_ar + self.window

    def forecast_logit_ratios(self, steps=None, **kwargs):
        if steps:
            self.days_to_forecast = steps
        last_date = self.data.index[-1]
        self.forecast_index_start = last_date + pd.Timedelta(days=1)
        self.forecast_index_stop = last_date + pd.Timedelta(days=self.days_to_forecast)
        self.forecasting_interval = pd.date_range(
            start=self.forecast_index_start,
            end=self.forecast_index_stop,
            freq="D",
        )
        try:
            self.forecasted_logit_ratios_tuple_arrays = self.logit_ratios_model_fitted.forecast_interval(
                self.logit_ratios_values, self.days_to_forecast, **kwargs
            )
        except Exception as e:
            raise Exception(e)

        self.forecasting_box = {
            logit_ratios[0]: pd.DataFrame(
                self.forecasted_logit_ratios_tuple_arrays[0],
                index=self.forecasting_interval,
                columns=forecasting_levels,
            ),
            logit_ratios[1]: pd.DataFrame(
                self.forecasted_logit_ratios_tuple_arrays[1],
                index=self.forecasting_interval,
                columns=forecasting_levels,
            ),
            logit_ratios[2]: pd.DataFrame(
                self.forecasted_logit_ratios_tuple_arrays[2],
                index=self.forecasting_interval,
                columns=forecasting_levels,
            ),
        }

        self.forecasting_box["alpha"] = self.forecasting_box["logit_alpha"].apply(logistic_function)
        self.forecasting_box["beta"] = self.forecasting_box["logit_beta"].apply(logistic_function)
        self.forecasting_box["gamma"] = self.forecasting_box["logit_gamma"].apply(logistic_function)

        self.forecasting_box = Box(self.forecasting_box)

    def simulate_for_given_levels(self, simulation_levels):

        simulation = self.data[["A", "C", "S", "I", "R", "D", "alpha", "beta", "gamma"]].iloc[-1:].copy()

        for t1 in self.forecasting_interval:
            t0 = t1 - pd.Timedelta(days=1)
            previous = simulation.loc[t0]
            S = previous.S - previous.I * previous.alpha * previous.S / previous.A
            I = (previous.I
                 + previous.I * previous.alpha * previous.S / previous.A
                 - previous.beta * previous.I
                 - previous.gamma * previous.I)
            R = previous.R + previous.beta * previous.I
            D = previous.D + previous.gamma * previous.I
            C = I + R + D
            A = previous.A

            simulation.loc[t1] = [
                A, C, S, I, R, D,
                self.forecasting_box["alpha"][simulation_levels[0]].loc[t1],
                self.forecasting_box["beta"][simulation_levels[1]].loc[t1],
                self.forecasting_box["gamma"][simulation_levels[2]].loc[t1]
            ]

        simulation = simulation.iloc[1:]
        try:
            simulation.index = self.forecasting_interval
        except Exception as e:
            raise Exception(e)

        return simulation

    def create_simulation_box(self):
        self.simulation = Box()
        for logit_alpha_level in forecasting_levels:
            self.simulation[logit_alpha_level] = Box()
            for logit_beta_level in forecasting_levels:
                self.simulation[logit_alpha_level][logit_beta_level] = Box()
                for logit_gamma_level in forecasting_levels:
                    self.simulation[logit_alpha_level][logit_beta_level][logit_gamma_level] = None

    def run_simulations(self):
        self.create_simulation_box()
        for current_levels in itertools.product(forecasting_levels, forecasting_levels, forecasting_levels):
            logit_alpha_level, logit_beta_level, logit_gamma_level = current_levels
            current_simulation = self.simulate_for_given_levels(current_levels)
            self.simulation[logit_alpha_level][logit_beta_level][logit_gamma_level] = current_simulation

    def create_results_dataframe(self, compartment):
        results_dataframe = pd.DataFrame()
        logging.debug(results_dataframe.head())

        levels_interactions = itertools.product(forecasting_levels, forecasting_levels, forecasting_levels)

        for logit_alpha_level, logit_beta_level, logit_gamma_level in levels_interactions:
            column_name = f"{logit_alpha_level}|{logit_beta_level}|{logit_gamma_level}"
            simulation = self.simulation[logit_alpha_level][logit_beta_level][logit_gamma_level]
            results_dataframe[column_name] = simulation[compartment].values

        results_dataframe["mean"] = results_dataframe.mean(axis=1)
        results_dataframe["median"] = results_dataframe.median(axis=1)
        results_dataframe["gmean"] = results_dataframe.apply(gmean, axis=1)
        results_dataframe["hmean"] = results_dataframe.apply(hmean, axis=1)

        results_dataframe.index = self.forecasting_interval

        return results_dataframe

    def generate_result(self):

        self.results = Box()

        for compartment in compartments:
            self.results[compartment] = self.create_results_dataframe(compartment)

    def visualize_results(self,
                          compartment_code,
                          testing_data=None,
                          log_response=True):
        compartment = self.results[compartment_code]
        compartment_levels = [column for column in compartment.columns if column not in central_tendency_methods]

        for level in compartment_levels:
            plt.plot(
                compartment.index,
                compartment[level].values,
                color="gray",
                linestyle="dashdot",
                alpha=0.25,
            )

        for method in central_tendency_methods:
            plt.plot(
                compartment.index,
                compartment[method].values,
                label=method_names[method],
                color=method_colors[method],
                linestyle="dashed",
            )

        if testing_data is not None:
            plt.plot(
                testing_data.index,
                testing_data[compartment_code].values,
                color="red",
                label="Actual data"
            )

        plt.title(f"{compartment_labels[compartment_code]}")

        if log_response:
            plt.title(f"{compartment_labels[compartment_code]} (logarithmic response)")
            plt.yscale("log")

        plt.grid(True)
        plt.legend(loc="upper left")
        plt.show()

    def evaluate_forecast(self, testing_data, compartment_codes=("C", "D", "I"), save_evaluation=False, filename=None):

        evaluation = {}

        for compartment_code in compartment_codes:
            compartment = self.results[compartment_code]

            evaluation[compartment_code] = {}

            for method in central_tendency_methods:

                forecast = compartment[method].values
                actual = testing_data[compartment_code].values
                mae = mean_absolute_error(actual, forecast)
                mse = mean_squared_error(actual, forecast)
                rmse = np.sqrt(mse)
                mape = np.mean(np.abs((actual - forecast) / actual)) * 100
                smape = np.mean(np.abs((actual - forecast) / (actual + forecast))) * 100

                evaluation[compartment_code][method] = {
                    "mae": mae,
                    "mse": mse,
                    "rmse": rmse,
                    "mape": mape,
                    "smape": smape,
                }

        if save_evaluation:
            if filename is None:
                now = pd.Timestamp.now()
                filename = now.strftime("%Y%m%d%H%M%S")
            with open(f"{filename}.json", "w") as f:
                json.dump(evaluation, f)

        return evaluation