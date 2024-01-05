import streamlit as st
import base64

"""### gif from url"""
st.markdown("![Alt Text](https://media.giphy.com/media/vFKqnCdLPNOKc/giphy.gif)")

"""### gif from local file"""
file_ = open("data/characters/boy.gif", "rb")
contents = file_.read()
data_url = base64.b64encode(contents).decode("utf-8")
file_.close()

st.markdown(
    f'<img src="data:image/gif;base64,{data_url}" width="200" height="200" style="opacity:0.4;filter:alpha(opacity=40);" alt="cat gif">',
    unsafe_allow_html=True,
)