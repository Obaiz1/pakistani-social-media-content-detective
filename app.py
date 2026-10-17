"""Streamlit entry point. Presentation only; analytics logic lives in src/."""

import streamlit as st

from src.data_sources import load_synthetic_fixture

st.set_page_config(page_title="Pakistani Social Media Content Detective", page_icon="🇵🇰", layout="wide")

st.title("Pakistani Social Media Content Detective 🇵🇰")
st.caption("What YouTube content gets Pakistani clothing-brand audiences to engage?")

data = load_synthetic_fixture()

st.warning(
    "**SYNTHETIC DEMO DATA.** These numbers are generated for testing and are not real "
    "measurements of any brand. Live YouTube data arrives in a later phase."
)

c1, c2, c3 = st.columns(3)
c1.metric("Brands", data.videos["brand_id"].nunique())
c2.metric("Videos", len(data.videos))
c3.metric("Comments", len(data.comments))

st.dataframe(data.videos.head(20), use_container_width=True)
