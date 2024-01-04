import streamlit as st
import base64

"""### gif from url"""
st.markdown("![Alt Text](https://media.giphy.com/media/vFKqnCdLPNOKc/giphy.gif)")

"""### gif from local file"""
file_ = open("data/characters/talking_head1.gif", "rb")
contents = file_.read()
data_url = base64.b64encode(contents).decode("utf-8")
file_.close()

st.markdown(
    f'<img src="data:image/gif;base64,{data_url}" style="width:30px height:30px" alt="cat gif">',
    unsafe_allow_html=True,
)