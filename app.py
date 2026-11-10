"""Streamlit entry point. Presentation only; analytics logic lives in src/."""

import streamlit as st

from src.ui import sidebar_brand

st.set_page_config(page_title="AI Social Media Content Detective", page_icon=":material/query_stats:", layout="wide")

# Re-save shared widget state in the entry point before a page's widgets render.
# Streamlit's documented multipage pattern keeps filters through navigation,
# including Data & Method, which does not itself create filter widgets.
for filter_key in ("f_brands", "f_dates", "f_buckets", "f_promo"):
    if filter_key in st.session_state:
        st.session_state[filter_key] = st.session_state[filter_key]

with st.sidebar:
    sidebar_brand()

pages = st.navigation({
    "Workspace": [
        st.Page("views/overview.py", title="Overview", icon=":material/dashboard:", default=True),
        st.Page("views/recommendations.py", title="What to post next", icon=":material/target:"),
    ],
    "Explore": [
        st.Page("views/brands.py", title="Brands", icon=":material/storefront:"),
        st.Page("views/content.py", title="Content", icon=":material/video_library:"),
        st.Page("views/timing.py", title="Posting time", icon=":material/schedule:"),
        st.Page("views/adjusted.py", title="Adjusted effects", icon=":material/tune:"),
        st.Page("views/sentiment.py", title="Sentiment", icon=":material/forum:"),
    ],
    "Evidence & delivery": [
        st.Page("views/exports.py", title="Report & exports", icon=":material/download:"),
        st.Page("views/method.py", title="Data & Method", icon=":material/menu_book:"),
    ],
})
pages.run()
