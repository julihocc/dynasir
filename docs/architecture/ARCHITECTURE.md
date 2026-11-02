# Architecture

This document provides a high-level overview of the `dynasir` project's architecture.

## Project Structure

The project is organized into the following main directories:

*   `dynasir`: The main source code for the `dynasir` library.
*   `tests`: Contains all the tests for the project.
*   `.github`: Contains GitHub-specific files, such as workflows and issue templates.
*   `scripts`: Contains various scripts for managing the project.

## Core Components

The `dynasir` library is built around a few core components:

*   **`DataContainer`**: This class is responsible for loading, preprocessing, and storing the data used for the epidemiological models. It is located in `dynasir/data/container.py`.

*   **`Model`**: This is the main class for creating and managing the epidemiological models. It takes a `DataContainer` object as input and provides methods for creating, fitting, and forecasting the models. It is located in `dynasir/models/base.py`.

*   **SIRD Model**: The `dynasir` library includes a discrete Susceptible-Infected-Recovered-Deceased (SIRD) model. The core logic for this model is implemented in `dynasir/models/sird.py`.

*   **Analysis and Visualization**: The `dynasir/analysis` directory contains modules for evaluating and visualizing the results of the models.

## Data Pipeline

The data pipeline in `dynasir` is designed to be flexible and extensible. It consists of the following steps:

1.  **Data Loading**: Data is loaded from a source, such as a CSV file, into a pandas DataFrame.
2.  **Preprocessing**: The raw data is preprocessed to prepare it for the models. This includes cleaning the data, handling missing values, and engineering new features.
3.  **Data Validation**: The preprocessed data is validated to ensure it meets the requirements of the models.
4.  **Data Container**: The validated data is stored in a `DataContainer` object, which provides a convenient interface for accessing the data.

## Modeling Workflow

The modeling workflow in `dynasir` is as follows:

1.  **Model Creation**: A `Model` object is created with a `DataContainer` object and other parameters, such as the start and end dates for the model.
2.  **Model Fitting**: The `Model` object is used to fit a time series model to the epidemiological data.
3.  **Forecasting**: The fitted model is used to forecast the future evolution of the pandemic.
4.  **Simulation**: The `Model` object can be used to run simulations to generate a distribution of possible outcomes.
5.  **Evaluation**: The forecasted results are evaluated against the actual data to assess the performance of the model.
6.  **Visualization**: The results of the model are visualized to help understand the dynamics of the pandemic.
