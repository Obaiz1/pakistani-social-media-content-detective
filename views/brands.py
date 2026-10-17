import pandas as pd
import streamlit as st

from src.analytics.compare import compare_groups
from src.ui import brand_label, get_data, median_ci_chart, sidebar_filters, source_banner, summary_table

METRICS = {
    "Engagement rate: (likes + comments) ÷ views": ("er_views", True),
    "Like rate: likes ÷ views": ("like_rate", True),
    "Views per subscriber": ("views_per_sub", False),
}

loaded = get_data()
st.title("Brands")
source_banner(loaded)
all_videos = loaded.data.videos
videos = sidebar_filters(all_videos)
if videos.empty:
    st.info("No videos match the current filters.")
    st.stop()

choice = st.radio("Metric", list(METRICS), horizontal=True)
metric, pct = METRICS[choice]
summary = compare_groups(videos, "brand_id", metric)
st.plotly_chart(median_ci_chart(summary, f"{choice}: median by brand (95% CI)", choice.split(":")[0],
                                pct=pct, label=brand_label, reference=videos[metric].median()),
                width="stretch")
st.dataframe(summary_table(summary, label=brand_label, pct=pct), hide_index=True, width="stretch")
st.caption(f"Kruskal-Wallis across brands: p = {summary.attrs['kruskal_p']:.3g}. "
           "Each brand is compared with all other filtered videos (Mann-Whitney U, Benjamini-Hochberg adjusted).")

st.subheader("Data coverage per brand")
g = all_videos.groupby("brand_id")
coverage = pd.DataFrame({
    "Brand": [brand_label(b) for b in g.size().index],
    "Videos (24 months)": g.size().values,
    "Likely promoted": g["likely_promoted"].sum().values,
    "Low reliability": g["low_reliability"].sum().values,
    "Hidden likes": g["like_count"].apply(lambda s: s.isna().sum()).values,
    "Videos with comments": g["comment_count"].apply(lambda s: (s.fillna(0) > 0).sum()).values,
})
st.dataframe(coverage, hide_index=True, width="stretch")
st.caption("Brand-level differences mix content, audience size and ad spend. The Content page compares "
           "content features using within-brand relative engagement to reduce that confounding.")
