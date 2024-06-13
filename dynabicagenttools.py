import base64
import ast
# Use Metrics for showing resources utilization updates between the two https://docs.streamlit.io/library/api-reference/data/st.metric
# Use below column_config to show pandas tables and stats

#import streamlit as st
#import pydeck as pdk

import pandas as pd
import numpy as np
from typing import Union, Dict, List
import matplotlib.pyplot as plt
import matplotlib
import os
# from random import random
import random
from datetime import datetime
from typing import Union, Dict, List, Tuple, Optional, Any
import sys
from projsecrets import project_path
import textwrap
sys.path.append(project_path)

RAG_DATA_PATH = os.path.join(project_path, "RAGSupport", "dataForRAG")
thismodule = sys.modules[__name__]


def hook_call(func_name:str, args, **kwargs) -> Tuple[str, str]:
    print(f"Hook function called. func name {func_name}. Args: {args}  kwargs: {kwargs}")

    # Solve the folder path for reading data
    prev_cwd = os.getcwd()
    os.chdir(RAG_DATA_PATH)

    # call the function
    func = getattr(thismodule, func_name)
    try:
        response_text, python_ui_code = func(*args, **kwargs)
        # If indented, remove the indentation
        if python_ui_code is not None:
            python_ui_code = textwrap.dedent(python_ui_code)
    except Exception as e:
        print(f"Error in external tool function call: {e}")
        return "Error in external tool function call", ""

    # Change back to the previous working directory
    finally:
        os.chdir(prev_cwd)

    return response_text, python_ui_code

def showComparativeColumnsDatasets(dataFrame: Union[str, pd.DataFrame], other: Union[str, pd.DataFrame]=None) -> str:
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

    # column_layer = pdk.Layer(
    #     "ColumnLayer",
    #     data=other,
    #     get_position=["lon", "lat"],
    #     get_elevation="count",
    #     elevation_scale=10,
    #     radius=200,
    #     get_fill_color=["percent*255.0", 0, 0, 140],
    #     pickable=True,
    #     auto_highlight=True,
    # )
    #
    # r = pdk.Deck(
    #     column_layer,
    #     initial_view_state=view,
    #     map_provider="mapbox",
    #     map_style=pdk.map_styles.CARTO_LIGHT,
    # )
    #
    # # r.to_html("column_layer.html")
    # st.pydeck_chart(r)

    return (f"These are the top demanding IP pairs: "
            f"[{list(zip(chart_data['ip'].to_string(), chart_data['count'].to_string()))}]")

#@st.cache_data
def show_outlier_ips_usage(normaldataset: Union[str, pd.DataFrame], outlierdataset: Union[str, pd.DataFrame]) -> str:
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
    #st.write(f"A: The items above mask mean that were not high consumers in the past too are {mask_above_mean_plus}")

    # Filter by the mask and sort the values by usage
    df_outliers = df_outliers.loc[mask_above_mean_plus]
    df_outliers.sort_values(by=["count"], inplace=True, ascending=False)

    # st.write(f"A: The final output is: {df_outliers}")

    st.dataframe(df_outliers.style.highlight_max(axis=0))

    return f"Outlier IPs usage: {df_outliers.to_string()}"
############
#@st.cache_data
def showResourceUtilizationComparison(nonHackedPath: str, hackedPath: str) -> str:
    test = True
    if not test:
        df_normal = pd.read_csv(nonHackedPath)
        st.line_chart(
            df_normal, x="time", y=["dataretrieval_occupancy", "dataupdater_occupancy"], yscale=1.0,
            color=["#FF000080", "#0000FF80"]  # Optional
        )

        df_outlier = pd.read_csv(hackedPath)
        st.line_chart(
            df_outlier, x="time", y=["dataretrieval_occupancy", "dataupdater_occupancy"], color=["#FF000080", "#0000FF80"]
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

    return f"Resource Utilization Comparison. Normal case {df_normal.to_string()}, Hacked case {df_outlier.to_string()}"


#@st.cache_data
def showResourceUtilizationComparison_v2(nonHackedPath: str, hackedPath: str) -> str:
    test = True
    if not test:
        df_normal = pd.read_csv(nonHackedPath)
        st.line_chart(
            df_normal, x="time", y=["dataretrieval_occupancy", "dataupdater_occupancy"], yscale=1.0,
            color=["#FF000080", "#0000FF80"]  # Optional
        )

        df_outlier = pd.read_csv(hackedPath)
        st.line_chart(
            df_outlier, x="time", y=["dataretrieval_occupancy", "dataupdater_occupancy"], color=["#FF000080", "#0000FF80"]
            # Optional
        )
    else:
        # %%
        cwd = os.getcwd()
        print(f"Current working directory: {cwd}")

        df_normal = pd.read_csv(nonHackedPath)
        df_outlier = pd.read_csv(hackedPath)

        # plotting two histograms on the same axis

        fig, ax = plt.subplots(1, 1)

        counts, bins, patchces = ax.hist([df_normal['dataretrieval_occupancy'], df_normal['dataupdater_occupancy'],
                    df_outlier['dataretrieval_occupancy'], df_outlier['dataupdater_occupancy']],
                   bins=[0.2, 0.4, 0.6, 0.8, 1.0], alpha=0.85, color=['red', 'blue', 'green', 'yellow'],
                   label=['Average-Retrievers', 'Average-Updaters', 'Last24h-Retrievers', 'Last24h-Updaters'],
                orientation='horizontal')

        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'])

        ax.set_xlabel('Time percentage')
        ax.set_ylabel('Occupancy percentage')
        ax.legend()
        ax.set_title("Average vs Last 24h resources occupancy distribution")

        st.pyplot(fig)

    return f"Resource Utilization Comparison. Normal case {df_normal.to_string()}, Hacked case {df_outlier.to_string()}"

#@st.cache_data
def showLastNGetQueriesFromTopM_demandingIPs(N: int = 10, M: int = 3, dataset: Union[pd.DataFrame, str] = None) -> str:
    interested_columns = ['ip', 'id', 'lat', 'lon']
    if type(M) is str:
        M = int(M)
    if type(N) is str:
        N = int(N)

    if dataset is None:
        dataset = "Hospital_DDoSSnapshot_Data/DATASET_LOGS_HACKED_True.csv"

    df = pd.read_csv(dataset) if isinstance(dataset, str) else dataset
    df_grouped = df.groupby(interested_columns, as_index=False).agg(count=("ip", "count")).reset_index() #
    df_grouped.sort_values(by='count', ascending=False, inplace=True)
    df_grouped = df_grouped.reset_index(drop=True)
    df_grouped = df_grouped.drop('index', axis=1)

    topDemandingIPs = set(df_grouped['ip'][:M].to_dict().values())

    #mask = np.where(df['ip'].isin(topDemandingIPs) & df['request_type'].isin([2]))
    #df = df.loc[mask][['ip', 'request_type', 'start_t', 'end_t', 'request_params']][-N:]
    #df['ind'] = list(range(len(df)))
    def color_coding(row):
        return ['background-color:red'] * len(
            row) if row.ip in topDemandingIPs else ['background-color:yellow'] * len(row)

    st.dataframe(df_grouped.style.apply(color_coding, axis=1), hide_index=True)


    prompt_return = "The top demanding IPs are: " + ', '.join(e for e in topDemandingIPs)
    return prompt_return

#@st.cache_data
def showCSVTable(path: str, *kwargs) -> str:
    df = pd.read_csv(path)
    if 'highlight' in kwargs[0]:
        # list as string to list
        #kwargs[1] = ast.literal_eval(kwargs[1])
        rowsToHightlight = kwargs[1]

        def color_coding(row):
            nonlocal rowsToHightlight
            #print(row)

            #return ['background-color:black'] * len(row)
            return ['background-color:red'] * len(row) if row[0] == rowsToHightlight \
                else ['background-color:black'] * len(row)

        st.dataframe(df.style.apply(color_coding, axis=1), hide_index=True)
    else:
        st.dataframe(df)

    return df.to_string()

# Update the firewall rules using the provided IPs and the context
#@st.cache_data
def firewallUpdate(*kwargs) -> Tuple[str, str]:
    # Step 1: Read the arguments, update the dataset
    # The first argument is if the IPs are to be blocked or allowed
    is_allow = kwargs[0]
    # The second argument is if the IPs in the list are excepting to the ips in the context list
    is_except = kwargs[1]
    # The third argument is the list of IPs to be blocked or allowed
    param_ips = kwargs[2]

    num_ips = len(param_ips)
    all_service_names = ['doctoronline.com', 'simair.bk', 'ali24', 'blackfriday']
    service_names = np.random.choice(all_service_names, num_ips, replace=True)
    blocked = [1]*num_ips if is_allow else [0]*num_ips
    limited_bandwidth = [2000]*num_ips

    # Read the previous dataset
    df1 = pd.read_csv("Hospital_DDoSSnapshot_Data/FIREWALL_PROCESSES.csv",
                      index_col=False)
    # Create the dataset
    df_new = pd.DataFrame({'IP': param_ips, 'NAME': service_names, 'DATE': datetime.now(), 'BLOCKED': blocked,
                           'LIMITED_BANDWIDTH': limited_bandwidth})
    # Concat with previous
    df1 = pd.concat([df1, df_new])  # , ignore_index=True)
    # Save to disk
    df1.to_csv("Hospital_DDoSSnapshot_Data/FIREWALL_PROCESSES.csv", index=False)


    # Step 2: Show the updated dataset
    python_ui_code = f'''
    df = pd.read_csv("Hospital_DDoSSnapshot_Data/FIREWALL_PROCESSES.csv")
    if 'highlight' in kwargs[0]:
        # list as string to list
        #kwargs[1] = ast.literal_eval(kwargs[1])
        rowsToHightlight = kwargs[1]

        def color_coding(row):
            nonlocal rowsToHightlight
            #print(row)

            #return ['background-color:black'] * len(row)
            return ['background-color:red'] * len(row) if row[0] == rowsToHightlight \
                else ['background-color:black'] * len(row)

        st.dataframe(df.style.apply(color_coding, axis=1), hide_index=True)
    else:
        st.dataframe(df)
    '''

    response_text = f"Firewall rules updated."
    return response_text, python_ui_code
