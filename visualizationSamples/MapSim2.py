import os
import random

import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from typing import Union, Dict, List, Tuple, Optional


def shopComparativeColumnsDatasets(dataFrame: Union[str, pd.DataFrame], other: Union[str, pd.DataFrame]=None):
    interested_columns = ['ip', 'id', 'lat', 'lon']

    chart_data = dataFrame if isinstance(dataFrame, pd.DataFrame) else pd.read_csv(dataFrame)
    chart_data = chart_data[interested_columns]

    other = other if isinstance(other, pd.DataFrame) else pd.read_csv(other)
    other = other[interested_columns]

    chart_data = chart_data.groupby(interested_columns, as_index=False).agg(count=("ip", "count"))
    other = other.groupby(interested_columns, as_index=False).agg(count=("ip", "count"))

    max_range = max(int(chart_data['count'].max()), int(other['count'].max()))

    LAND_COVER = [[[26.5, 44.0], [26.5, 44.8], [25.7, 44.8], [25.7, 44.0]]]

    chart_data['percent'] = chart_data['count'] / max_range
    other['percent'] = other['count'] / max_range


    #############


    DATA_URL = "https://raw.githubusercontent.com/ajduberstein/geo_datasets/master/housing.csv"
    df = pd.read_csv(DATA_URL)

    view = pdk.data_utils.compute_view(chart_data[["lon", "lat"]])
    view.pitch = 75
    view.bearing = 60


    column_layer = pdk.Layer(
        "ColumnLayer",
        data=chart_data,
        get_position=["lon", "lat"],
        get_elevation="count",
        elevation_scale=10,
        radius=200,
        get_fill_color=["percent*255.0", 0, 0, 140],
        pickable=True,
        auto_highlight=True,
    )

    r1 = pdk.Deck(
        column_layer,
        initial_view_state=view,
        map_provider="mapbox",
        map_style=pdk.map_styles.CARTO_LIGHT,
    )

    #r.to_html("column_layer.html")
    st.pydeck_chart(r1)

    column_layer = pdk.Layer(
        "ColumnLayer",
        data=other,
        get_position=["lon", "lat"],
        get_elevation="count",
        elevation_scale=10,
        radius=200,
        get_fill_color=["percent*255.0", 0, 0, 140],
        pickable=True,
        auto_highlight=True,
    )

    r = pdk.Deck(
        column_layer,
        initial_view_state=view,
        map_provider="mapbox",
        map_style=pdk.map_styles.CARTO_LIGHT,
    )

    # r.to_html("column_layer.html")
    st.pydeck_chart(r)


if __name__ == '__main__':
    st.write("H: Give me a world map of requests by comparing the current Data and a known snapshot with bars")


    print(os.getcwd())
    st.write("A:Here is the map, first is the now version, I will invoke FUNC_CALL shopComparativeColumnsDatasets with Params '../../RAGSupport/dataForRAG/SmartHome_DDoSSnapshot_Data/DATASET_LOGS_HACKED_True.csv' '../../../RAGSupport/dataForRAG/SmartHome_DDoSSnapshot_Data/DATASET_LOGS_HACKED_False.csv'")

    shopComparativeColumnsDatasets("../../RAGSupport/dataForRAG/SmartHome_DDoSSnapshot_Data/DATASET_LOGS_HACKED_True.csv", "../../RAGSupport/dataForRAG/SmartHome_DDoSSnapshot_Data/DATASET_LOGS_HACKED_False.csv")
