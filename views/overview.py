import streamlit as st

from src.analytics.compare import compare_groups
from src.ui import (brand_label, get_data, median_ci_chart, page_header, plotly_chart,
                    section_header, sidebar_filters, source_banner)

loaded = get_data()
page_header("AI Social Media Content Detective",
            "What YouTube content gets Pakistani clothing-brand audiences to engage? "
            "Evidence-based analytics + AI-assisted recommendations.", eyebrow="Workspace / Overview")
source_banner(loaded)

videos = sidebar_filters(loaded.data.videos)
if videos.empty:
    st.info("No videos match the current filters.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Brands", videos["brand_id"].nunique(), border=True)
c2.metric("Videos analysed", f"{len(videos):,}", border=True)
c3.metric("Median engagement rate", f"{videos['er_views'].median():.2%}",
          help="(likes + comments) ÷ views, median across the filtered videos", border=True)
c4.metric("Comments collected", f"{len(loaded.data.comments):,}", border=True)
st.caption("Brands, videos and median engagement reflect your filters. Comments collected is the full dataset total.")

section_header("The engagement landscape", "Compare brand medians and uncertainty before exploring content patterns.")
summary = compare_groups(videos, "brand_id", "er_views")
plotly_chart(median_ci_chart(summary, "Median engagement rate by brand (95% CI)", "Engagement rate",
                                label=brand_label, reference=videos["er_views"].median()),
                width="stretch")
st.caption("Dot = median, line = 95% bootstrap confidence interval, dotted line = overall median. "
           "Brand differences partly reflect audience size and ad spend, so use **Content** for "
           "within-brand comparisons.")

with st.expander("How to read this dashboard: key caveats"):
    st.markdown(
        "- **Pakistan-related content, not a verified Pakistani audience.** The API doesn't expose viewer location.\n"
        "- **Correlation, not causation.** A pattern linked to higher engagement doesn't prove it *causes* it.\n"
        "- **Paid views.** Some view counts look ad-boosted; those videos are excluded by default (sidebar toggle).\n"
        "- **Small groups** (n < 20) are shown in grey and never tested.\n"
        "- Full definitions are on **Data & Method**."
    )

section_header("Continue your investigation")
left, right = st.columns(2)
with left.container(border=True):
    st.markdown("**Understand the content**")
    st.caption("Compare formats, campaigns and title features using within-brand relative engagement.")
    if st.button("Explore content", icon=":material/arrow_forward:", width="stretch"):
        st.switch_page("views/content.py")
with right.container(border=True):
    st.markdown("**Turn evidence into an experiment**")
    st.caption("Review supported findings, adjusted checks and limitations before planning an A/B test.")
    if st.button("What to post next", icon=":material/arrow_forward:", width="stretch"):
        st.switch_page("views/recommendations.py")
