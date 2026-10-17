"""Streamlit entry point. Presentation only; analytics logic lives in src/."""

import streamlit as st

st.set_page_config(page_title="AI Social Media Content Detective", page_icon="🇵🇰", layout="wide")

pages = st.navigation([
    st.Page("views/overview.py", title="Overview", icon="🏠", default=True),
    st.Page("views/recommendations.py", title="What to post next", icon="🎯"),
    st.Page("views/brands.py", title="Brands", icon="🏷️"),
    st.Page("views/content.py", title="Content", icon="🎬"),
    st.Page("views/timing.py", title="Posting time", icon="🕒"),
    st.Page("views/adjusted.py", title="Adjusted effects", icon="🧮"),
    st.Page("views/sentiment.py", title="Sentiment", icon="💬"),
    st.Page("views/exports.py", title="Report & exports", icon="⬇️"),
    st.Page("views/method.py", title="Data & Method", icon="📐"),
])
pages.run()
