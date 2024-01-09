import streamlit as st
import base64

# Use Metrics for showing resources utilization updates between the two https://docs.streamlit.io/library/api-reference/data/st.metric
# Use below column_config to show pandas tables and stats

import streamlit as st
import pandas as pd
import numpy as np
#from random import random
import random
df = pd.DataFrame(np.random.randn(50, 20), columns=("col %d" % i for i in range(20)))

st.dataframe(df.style.highlight_max(axis=0))

############

import pandas as pd
df = pd.read_csv("data/sim/RESOURCES_OCCUPANCY_HACKED_False.csv")

"""
chart_data = pd.DataFrame(np.random.randn(20, 3), columns=["col1", "col2", "col3"])

st.line_chart(
   chart_data, x="col1", y=["col2", "col3"], color=["#FF0000", "#0000FF"]  # Optional
)
"""
st.line_chart(
   df, x="time", y=["dataretrieval_occupancy", "dataupdater_occupancy"], color=["#FF0000", "#0000FF"]  # Optional
)

df2 = pd.read_csv("data/sim/RESOURCES_OCCUPANCY_HACKED_True.csv")
st.line_chart(
   df2, x="time", y=["dataretrieval_occupancy", "dataupdater_occupancy"], color=["#FF0000", "#0000FF"]  # Optional
)

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