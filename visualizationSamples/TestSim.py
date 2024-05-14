import streamlit as st
import base64

# Use Metrics for showing resources utilization updates between the two https://docs.streamlit.io/library/api-reference/data/st.metric
# Use below column_config to show pandas tables and stats

import streamlit as st
from dynabicagenttools import *
import pandas as pd
import numpy as np
from typing import Union, Dict, List
import matplotlib.pyplot as plt

# from random import random
import random


#########################################
# SCRIPT
########################################

st.write("A: Hi, Alert: I just identified that there are many timeouts and error codes such as 503 of the IoT devices in their homes and the main IoT hub.")


st.write("H: Ok. I'm on it, can you show me a resource utilization graph comparison between a normal session and current situation")
st.write("A: Here it is")
showResourceUtilizationComparison("../RAGSupport/dataForRAG/SmartHome_DDoSSnapshot_Data/good_RESOURCES_OCCUPANCY_HACKED_False.csv",
                                  "../RAGSupport/dataForRAG/SmartHome_DDoSSnapshot_Data/good_RESOURCES_OCCUPANCY_HACKED_True.csv")


st.write(
    "H: Show me the logs of the devices grouped by IP which have more than 25% requests over the median of a normal session per. Sort them by count")
st.write("A: Here it is")

show_outlier_ips_usage("../RAGSupport/dataForRAG/SmartHome_DDoSSnapshot_Data/DATASET_LOGS_HACKED_False.csv",
                       "../RAGSupport/dataForRAG/SmartHome_DDoSSnapshot_Data/DATASET_LOGS_HACKED_True.csv")



M = 3
N = 10
st.write(f"H: show a sample of GET requests from the top {M} demanding IPs, including their start time, end time, ")
st.write("A: Here it is")
showLastNGetQueriesFromTopM_demandingIPs(N=N, M=M, ".../RAGSupport/dataForRAG/SmartHome_DDoSSnapshot_Data/DATASET_LOGS_HACKED_True.csv")

st.write("H: What could it mean if there are many IPs from different locations sending GET commands in a short time with random queries ?")
st.write("A: This could be the sign of a DDoS attack")

st.write("H: What can I do about it ? ")
st.write("A: bla bla...")

st.write("H: Ok, to solve temporarily before rewrite the firmwares can you block the identified top IPs "
         "sending GET commands by adding them to the firewall csv then commit it on Github?")


st.write("H: TODO 	- User ask to compare one of the devices to find differences between a normal device "
         "and a hacked one. => Need DATABASE_STOCK_PROCESSES and DATABASE_ID_PROCESSES. Restock the OS. [PYTHON program]")
exit(0)
############

import streamlit as st

st.metric(label="Gas price", value=4, delta=-0.5,
          delta_color="inverse")

st.metric(label="Active developers", value=123, delta=123,
          delta_color="off")

df = pd.DataFrame(
    {
        "name": ["Roadmap", "Extras", "Issues"],
        "url": ["https://roadmap.streamlit.app", "https://extras.streamlit.app", "https://issues.streamlit.app"],
        "stars": [random.randint(0, 1000) for _ in range(3)],
        "views_history": [[random.randint(0, 5000) for _ in range(30)] for _ in range(3)],
    }
)
st.dataframe(
    df,
    column_config={
        "name": "App name",
        "stars": st.column_config.NumberColumn(
            "Github Stars",
            help="Number of stars on GitHub",
            format="%d ⭐",
        ),
        "url": st.column_config.LinkColumn("App URL"),
        "views_history": st.column_config.LineChartColumn(
            "Views (past 30 days)", y_min=0, y_max=5000
        ),
    },
    hide_index=True,
)
