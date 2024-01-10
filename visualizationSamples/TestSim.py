import streamlit as st
import base64

# Use Metrics for showing resources utilization updates between the two https://docs.streamlit.io/library/api-reference/data/st.metric
# Use below column_config to show pandas tables and stats

import streamlit as st
import pandas as pd
import numpy as np
#from random import random
import random


interested_columns = ['ip','id', 'lat', 'lon']

st.write("H: Show me the devices grouped by IP which have more than 25% requests over the median of a normal session per. Sort them by count")
st.write("A: Here it is")

st.write("A: Finding the median of a normal session")
df_normal = pd.read_csv("../dynabicChatbot/DATASET_LOGS_HACKED_False.csv")
df_normal = df_normal.groupby(interested_columns, as_index=False).agg(count=("ip", "count"))
mean_normal = df_normal.loc[:, 'count'].mean()
st.write(f"A: The mean value is {mean_normal}")

mean_normal_plus = mean_normal*1.25

df = pd.read_csv("../dynabicChatbot/DATASET_LOGS_HACKED_True.csv")
df = df[interested_columns]
#df.groupby(interested_columns).count().reset_index()[interested_columns.append('Count')]

df = df.groupby(interested_columns, as_index=False).agg(count=("ip", "count"))
df.sort_values(by=["count"], inplace=True, ascending=False)
df = df[np.where(df["count"] > mean_normal_plus)]
st.dataframe(df.style.highlight_max(axis=0))

############
def showResourceUtilizationComparison(nonHackedPath: str, hackedPath: str):
    df = pd.read_csv(nonHackedPath)

    st.line_chart(
       df, x="time", y=["dataretrieval_occupancy", "dataupdater_occupancy"], color=["#FF000080", "#0000FF80"]  # Optional
    )

    df2 = pd.read_csv(hackedPath)
    st.line_chart(
       df2, x="time", y=["dataretrieval_occupancy", "dataupdater_occupancy"], color=["#FF000080", "#0000FF80"]  # Optional
    )

st.write("H: Show me a resource utilization graph comparison between a normal session and current situation.")
st.write("A: Here it is")
df = pd.read_csv("../dynabicChatbot/DATASET_LOGS_HACKED_True.csv")

interested_columns = ['ip','id', 'lat', 'lon']
df = df[interested_columns]
#df.groupby(interested_columns).count().reset_index()[interested_columns.append('Count')]

df.groupby(interested_columns, as_index=False).agg(count=("ip", "count"))
showResourceUtilizationComparison("../dynabicChatbot/good_RESOURCES_OCCUPANCY_HACKED_False.csv",
                                  "../dynabicChatbot/good_RESOURCES_OCCUPANCY_HACKED_True.csv")

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