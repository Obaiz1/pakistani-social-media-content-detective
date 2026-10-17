import streamlit as st

from src.analytics.compare import compare_groups
from src.ui import brand_label, get_data, median_ci_chart, sidebar_filters, source_banner

loaded = get_data()
st.title("AI Social Media Content Detective 🇵🇰")
st.caption("What YouTube content gets Pakistani clothing-brand audiences to engage? "
           "Evidence-based analytics + AI-assisted recommendations.")
source_banner(loaded)

videos = sidebar_filters(loaded.data.videos)
if videos.empty:
    st.info("No videos match the current filters.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Brands", videos["brand_id"].nunique())
c2.metric("Videos analysed", f"{len(videos):,}")
c3.metric("Median engagement rate", f"{videos['er_views'].median():.2%}",
          help="(likes + comments) ÷ views, median across the filtered videos")
c4.metric("Comments collected", f"{len(loaded.data.comments):,}")

summary = compare_groups(videos, "brand_id", "er_views")
st.plotly_chart(median_ci_chart(summary, "Median engagement rate by brand (95% CI)", "Engagement rate",
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
