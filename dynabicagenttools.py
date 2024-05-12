import streamlit as st
import base64

# Use Metrics for showing resources utilization updates between the two https://docs.streamlit.io/library/api-reference/data/st.metric
# Use below column_config to show pandas tables and stats

import streamlit as st
import pandas as pd
import numpy as np
from typing import Union, Dict, List
import matplotlib.pyplot as plt
import matplotlib
import os
# from random import random
import random

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


@st.cache_data
def show_outlier_ips_usage(normaldataset: Union[str, pd.DataFrame], outlierdataset: Union[str, pd.DataFrame]) -> None:
    interested_columns = ['ip', 'id', 'lat', 'lon']
    # Create counts per usage and median values
    df_normal = pd.read_csv(normaldataset) if isinstance(normaldataset, str) else normaldataset
    df_normal = df_normal.groupby(interested_columns, as_index=False).agg(count=("ip", "count"))
    median_normal = df_normal.loc[:, 'count'].median()
    median_normal_plus = median_normal * 1.3

    df_outliers = pd.read_csv(outlierdataset) if isinstance(outlierdataset, str) else outlierdataset
    df_outliers = df_outliers[interested_columns]
    df_outliers = df_outliers.groupby(interested_columns, as_index=False).agg(count=("ip", "count"))

    st.write(
        f"A: The median normal dataset: {median_normal}, and median considered for dataset filter: {median_normal_plus}")

    # Select from dataset only what we are interested in
    ips_which_were_highconsumers_in_past_too = df_normal.loc[np.where(df_normal["count"] > median_normal_plus)][
        "ip"].to_dict().values()
    # print(ips_which_were_highconsumers_in_past_too)

    mask_above_mean_plus = np.where((df_outliers["count"] > median_normal_plus) & ~(
        df_outliers["ip"].isin(ips_which_were_highconsumers_in_past_too)))
    st.write(f"A: The items above mask mean that were not high consumers in the past too are {mask_above_mean_plus}")

    # Filter by the mask and sort the values by usage
    df_outliers = df_outliers.loc[mask_above_mean_plus]
    df_outliers.sort_values(by=["count"], inplace=True, ascending=False)

    # st.write(f"A: The final output is: {df_outliers}")

    st.dataframe(df_outliers.style.highlight_max(axis=0))


############
@st.cache_data
def showResourceUtilizationComparison(nonHackedPath: str, hackedPath: str):
    test = True
    if not test:
        df = pd.read_csv(nonHackedPath)
        st.line_chart(
            df, x="time", y=["dataretrieval_occupancy", "dataupdater_occupancy"], yscale=1.0,
            color=["#FF000080", "#0000FF80"]  # Optional
        )

        df2 = pd.read_csv(hackedPath)
        st.line_chart(
            df2, x="time", y=["dataretrieval_occupancy", "dataupdater_occupancy"], color=["#FF000080", "#0000FF80"]
            # Optional
        )
    else:
        # %%
        df_normal = pd.read_csv(nonHackedPath)
        df_outlier = pd.read_csv(hackedPath)

        # plotting two histograms on the same axis

        fig, ax = plt.subplots(1, 2)

        ax[0].hist([df_normal['dataretrieval_occupancy'], df_normal['dataupdater_occupancy']],
                   bins=[0.2, 0.4, 0.6, 0.8, 1.0], alpha=0.85, color=['red', 'blue'],
                   label=['Retrievers occupancy', 'Updaters occupancy'])
        ax[0].legend()
        ax[0].set_title("Normal occupancy distribution")

        ax[1].hist([df_outlier['dataretrieval_occupancy'], df_outlier['dataupdater_occupancy']],
                   bins=[0.2, 0.4, 0.6, 0.8, 1.0], alpha=0.85, color=['green', 'yellow'],
                   label=['Retrievers occupancy', 'Updaters occupancy'])
        ax[1].legend()
        ax[1].set_title("Current occupancy")

        st.pyplot(fig)

@st.cache_data
def showLastNGetQueriesFromTopM_demandingIPs(M: int = 3, N: int = 10, dataset: Union[pd.DataFrame, str] = None) -> None:
    interested_columns = ['ip', 'id', 'lat', 'lon']
    if type(M) is str:
        M = int(M)
    if type(N) is str:
        N = int(N)

    if dataset is None:
        dataset = "../dynabicChatbot/data/dataForRAG/SmartHome_DDoSSnapshot_Data/DATASET_LOGS_HACKED_True.csv"

    df = pd.read_csv(dataset) if isinstance(dataset, str) else dataset
    df_grouped = df.groupby(interested_columns, as_index=False).agg(count=("ip", "count"))
    df_grouped.sort_values(by='count', ascending=False, inplace=True)

    topDemandingIPs = set(df_grouped['ip'][:M].to_dict().values())

    mask = np.where(df['ip'].isin(topDemandingIPs) & df['request_type'].isin([2]))
    st.write(df.loc[mask][['ip', 'request_type', 'start_t', 'end_t', 'request_params']][-N:])

