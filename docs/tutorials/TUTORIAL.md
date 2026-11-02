# Case study: Global model for COVID-19 forecasting

We use the data from the [Our World in Data](https://ourworldindata.org/coronavirus-source-data) project. The data is available in the `data_sample` folder. The data is processed using the `process_data_from_owid` function. The function returns a `DataContainer` object. The `DataContainer` object contains the data and the information about the data. The `DataContainer` object is used to create a `Model` object. The `Model` object is used to create a model, fit the model, forecast the model, run simulations, and generate results. The `Model` object is also used to evaluate the forecast. The `Model` object is used to visualize the results.

```python
# !pip install dynasir
import matplotlib.pyplot as plt
from dynasir import process_data_from_owid, DataContainer, Model
```

To make the exposition clearer, `warnings` is used to suppress warnings.

```python

import warnings
warnings.filterwarnings('ignore')
```

At first, we retrieve the global data from the `owid-covid-data.csv` file. The data is processed using the `process_data_from_owid` function. If no argument is passed to the function, the function retrieves the data from the `owid-covid-data.csv` file. The object `global_dataframe` is just a Pandas DataFrame object containing the raw data from the `owid-covid-data.csv` file.

Other sources could be used as long as they have the same structure as the `owid-covid-data.csv` file. By default, the retrieve data is filtered to make use only of global data, by setting the parameter `iso_code` to `OWID_WRL`. The `iso_code` parameter could be used to filter the data by country. For example, `iso_code="MEX"` retrieves the data for Mexico.

```python
global_dataframe = process_data_from_owid()
global_dataframe.head()
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>C</th>
      <th>D</th>
      <th>N</th>
    </tr>
    <tr>
      <th>date</th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>2020-01-05</th>
      <td>2.0</td>
      <td>3.0</td>
      <td>7975105024</td>
    </tr>
    <tr>
      <th>2020-01-06</th>
      <td>2.0</td>
      <td>3.0</td>
      <td>7975105024</td>
    </tr>
    <tr>
      <th>2020-01-07</th>
      <td>2.0</td>
      <td>3.0</td>
      <td>7975105024</td>
    </tr>
    <tr>
      <th>2020-01-08</th>
      <td>2.0</td>
      <td>3.0</td>
      <td>7975105024</td>
    </tr>
    <tr>
      <th>2020-01-09</th>
      <td>2.0</td>
      <td>3.0</td>
      <td>7975105024</td>
    </tr>
  </tbody>
</table>
</div>

Using the `global_dataframe`, we create a `DataContainer` object. The `DataContainer` object contains the data and the information about the data. The `DataContainer` object is used to create a `Model` object. As soon as the raw data is received by `DataContainer`, it is processed to create the `DataContainer` object. The `DataContainer` object contains the data and the information about the data. The `DataContainer` object is used to create a `Model` object.

```python

global_data_container = DataContainer(
    global_dataframe
)

print(
    f"Global data container has {global_data_container.data.shape[0]} rows and {global_data_container.data.shape[1]} columns.")
print(f"Global data container has {global_data_container.data.isna().sum().sum()} missing values.")
```

    Global data container has 1677 rows and 20 columns.
    Global data container has 0 missing values.
    

The attribute `data` from a `DataContainer` object is just a Pandas DataFrame object containing the processed data. Because of this, we can use the Pandas DataFrame methods to visualize the data.

```python
global_data_container.data[["C", "D", "N"]].plot(
    subplots=True
)
plt.show()
```

![png](global_model_files/global_model_10_0.png)

The dictionary containing the meaning of every label could be retrieved from the `COMPARTMENT_LABELS` attribute from the module itself.

```python
from dynasir import COMPARTMENT_LABELS
COMPARTMENT_LABELS
```

    {'A': 'Active',
     'C': 'Confirmed',
     'S': 'Susceptible',
     'I': 'Infected',
     'R': 'Recovered',
     'D': 'Deaths'}

```python
global_data_container.data[["A", "S", "I", "R"]].plot(
    subplots=True
)
plt.show()
```

![png](global_model_files/global_model_14_0.png)

As it was stated in the introduction, the non-constant but time-depending nature of the rate is the core of this model.

```python
global_data_container.data[["alpha", "beta", "gamma"]].plot(
    subplots=True
)
plt.show()
```

![png](global_model_files/global_model_16_0.png)

Create a model using the `global_data_container` object, using information from March 01, 2020, to December 31, 2020.

```python

global_model = Model(
    global_data_container,
    start="2020-03-01",
    stop="2020-12-31",
)

```

In the following, we apply these methods to create and fit a time series model for the logit of the rates $\alpha$, $\beta$ and $\gamma$. This is the core of the model. Please refer to the documentation for more information.

```python
global_model.create_model()
global_model.fit_model()
```

Now that we have a model for these rates, we can adjust the numbers of days (`steps`) to forecast. The `forecast` method generates forecasts for the logit ratios and transforms them back to rates. The `forecasting_interval` attribute contains the forecasting interval.

```python

global_model.forecast(steps=30)
global_model.forecasting_interval
```

    DatetimeIndex(['2021-01-01', '2021-01-02', '2021-01-03', '2021-01-04',
                   '2021-01-05', '2021-01-06', '2021-01-07', '2021-01-08',
                   '2021-01-09', '2021-01-10', '2021-01-11', '2021-01-12',
                   '2021-01-13', '2021-01-14', '2021-01-15', '2021-01-16',
                   '2021-01-17', '2021-01-18', '2021-01-19', '2021-01-20',
                   '2021-01-21', '2021-01-22', '2021-01-23', '2021-01-24',
                   '2021-01-25', '2021-01-26', '2021-01-27', '2021-01-28',
                   '2021-01-29', '2021-01-30'],
                  dtype='datetime64[ns]', freq='D')

Run the simulations and generate the results. The `generate_result` method returns a Pandas DataFrame object `global_model.results` containing the results.

```python

global_model.run_simulations()
global_model.generate_result()

```

Finally, we can visualize the results. The `visualize_results` method displays a plot using Matplotlib. At first, create a testing dataset using global data container and the global model forecasting interval. The `global_testing_data` is a Pandas DataFrame object containing the testing data.

```python

global_testing_data = global_data_container.data.loc[global_model.forecasting_interval]

for compartment in ["C", "D", "I"]:
    global_model.visualize_results(
        compartment,
        global_testing_data,
        log_response=True)
```

![png](global_model_files/global_model_26_0.png)

![png](global_model_files/global_model_26_1.png)

![png](global_model_files/global_model_26_2.png)

The gray dotted lines are several forecasting depending on the confidence interval for the time series model for the logit of the rates $\alpha$, $\beta$ and $\gamma$. The solid red line is the actual data in the forecasting interval. To make it clearer, we add many methods of central tendency to compare the forecasting with the actual data.

A very peculiar feature of this model is that the forecasting is not a single value but a distribution. For example, although the averages of forecasted deaths are not so close to the actual data, the lower forecasting series are very close to the actual data.

A tool for evaluate forecast in a more rigours manner is provided, using several criteria, and this analysis could be saved for further analysis.

```python
import json
evaluation = global_model.evaluate_forecast(global_testing_data, save_evaluation=True, filename="global_evaluation")
```

```python
for category, info in evaluation.items():
    print(category, info['mean']['smape'])
```

    C 2.197310076754546
    D 49.4142982150385
    I 15.371809526744256
