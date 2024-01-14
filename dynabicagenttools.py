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
    df = pd.read_csv(nonHackedPath)

    test = True
    if not test:
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
        ax[1].set_title("Outlier occupancy")

        st.pyplot(fig)


def showLastNGetQueriesFromTopM_demandingIPs(dataset: Union[pd.DataFrame, str], N: int = 10, M: int = 3) -> None:
    interested_columns = ['ip', 'id', 'lat', 'lon']
    df = pd.read_csv(dataset) if isinstance(dataset, str) else dataset
    df_grouped = df.groupby(interested_columns, as_index=False).agg(count=("ip", "count"))
    df_grouped.sort_values(by='count', ascending=False, inplace=True)

    topDemandingIPs = set(df_grouped['ip'][:3].to_dict().values())

    mask = np.where(df['ip'].isin(topDemandingIPs) & df['request_type'].isin([2]))
    st.write(df.loc[mask][['ip', 'request_type', 'start_t', 'end_t', 'request_params']][-N:])

