"""Missing incidence periods stay undefined (#187)."""

import warnings

import pandas as pd

from dynasir import DataContainer, Model


def _annual_with_gap():
    years = [2010, 2011, 2012, 2013, 2014, 2016, 2017, 2018, 2019, 2020]
    index = pd.to_datetime([f"{year}-12-31" for year in years])
    cases = [float(i + 1) for i in range(len(years))]
    incidence = pd.DataFrame(
        {"I": cases, "D": [0.0] * len(years), "N": [1e6] * len(years)},
        index=index,
    )
    cumulative = pd.DataFrame(
        {
            "C": pd.Series(cases, index=index).cumsum(),
            "D": [0.0] * len(years),
            "N": [1e6] * len(years),
        },
        index=index,
    )
    return incidence, cumulative


class TestMissingIncidencePeriods:
    def test_incidence_gap_is_left_undefined(self):
        incidence, _ = _annual_with_gap()
        container = DataContainer(
            incidence, mode="incidence", frequency="YE", window=1
        )

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = Model(container)

        messages = [str(item.message) for item in caught]
        assert any("2015-12-31" in message for message in messages)
        gap = model.data.loc["2015-12-31", "I"]
        assert pd.isna(gap)
        assert model.data["I"].sum(skipna=True) == incidence["I"].sum()

    def test_cumulative_gap_keeps_the_previous_value(self):
        _, cumulative = _annual_with_gap()
        container = DataContainer(
            cumulative, mode="cumulative", frequency="YE", window=1
        )
        model = Model(container)
        previous = model.data.loc["2014-12-31", "C"]
        assert model.data.loc["2015-12-31", "C"] == previous
