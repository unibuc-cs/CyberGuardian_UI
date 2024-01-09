import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

chart_data_normal = pd.read_csv("data/sim/DATASET_LOGS_HACKED_True.csv")
chart_data_normal = chart_data_normal[['lat', 'lon']]



chart_data_random = pd.DataFrame(
   np.random.randn(100, 2) / [50, 50] + [44.42810022576185, 26.10414240626916],
   columns=['lat', 'lon'])

chart_data = chart_data_normal

st.pydeck_chart(pdk.Deck(
    map_style=None,
    initial_view_state=pdk.ViewState(
        latitude=44.42810022576185,
        longitude=26.10414240626916,
        zoom=10,
        pitch=40,
    ),
    layers=[
        pdk.Layer(
           'HexagonLayer',
           data=chart_data,
           get_position='[lon, lat]',
           radius=200,
           elevation_scale=5,
           elevation_range=[0, 500],
           pickable=True,
           extruded=True,
        ),
        pdk.Layer(
            'ScatterplotLayer',
            data=chart_data,
            get_position='[lon, lat]',
            get_color='[200, 30, 0, 160]',
            get_radius=200,
        ),
    ],
))