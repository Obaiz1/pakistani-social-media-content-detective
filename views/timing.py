import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.analytics.compare import MIN_N, compare_groups
from src.analytics.timing import BAND_ORDER, WEEKDAYS, add_time_bands, heatmap_table
from src.ui import get_data, median_ci_chart, sidebar_filters, source_banner, summary_table

# diverging blue <-> red around 1.0 (= brand median), neutral grey midpoint (reference palette)
DIVERGING = [[0.0, "#e34948"], [0.5, "#f0efec"], [1.0, "#2a78d6"]]

loaded = get_data()
st.title("Posting time (Pakistan Standard Time)")
st.caption("When do videos get more engagement than is typical **for their own brand**? Metric: relative "
           "engagement (1.0 = brand median). Times are PKT (UTC+5).")
source_banner(loaded)
videos = sidebar_filters(loaded.data.videos)
if videos.empty:
    st.info("No videos match the current filters.")
    st.stop()

median, n = heatmap_table(videos)
text = np.where(n.to_numpy() >= MIN_N,
                [[f"{m:.2f}<br>n={c}" for m, c in zip(mr, cr)]
                 for mr, cr in zip(median.to_numpy(), n.to_numpy())],
                [[f"n={c}" for c in cr] for cr in n.to_numpy()])
spread = float(np.nanmax(np.abs(median.to_numpy() - 1))) if np.isfinite(median.to_numpy()).any() else 0.5
fig = go.Figure(go.Heatmap(
    z=median.to_numpy(), x=BAND_ORDER, y=WEEKDAYS, text=text, texttemplate="%{text}",
    colorscale=DIVERGING, zmid=1.0, zmin=1 - spread, zmax=1 + spread, xgap=2, ygap=2,
    textfont=dict(size=12),
    colorbar=dict(title="rel. eng."),
    customdata=n.to_numpy(),
    hovertemplate="%{y}, %{x}<br>median relative engagement %{z:.2f}<br>n = %{customdata}<extra></extra>",
))
fig.update_layout(title="Median relative engagement by weekday × time band (PKT)", height=430,
                  margin=dict(l=10, r=10, t=50, b=30), xaxis=dict(showgrid=False),
                  yaxis=dict(autorange="reversed", showgrid=False))
st.plotly_chart(fig, width="stretch")
st.caption(f"Blue = above the brand's typical engagement, red = below. Cells with n < {MIN_N} are left blank "
           "and only show their count. Cells are **descriptive only** (35 cells means many chance highs and lows); "
           "the statistically tested comparisons are the two charts below.")

banded = add_time_bands(videos)
for title, by, order in (("By time band", "hour_band_pkt", BAND_ORDER), ("By weekday", "weekday_pkt", WEEKDAYS)):
    st.subheader(title)
    summary = compare_groups(banded, by, "rel_er", order=order)
    st.plotly_chart(median_ci_chart(summary, f"Relative engagement {title.lower()} (median, 95% CI)",
                                    "Relative engagement (1.0 = brand median)", pct=False, reference=1.0),
                    width="stretch")
    with st.expander("Table view & statistics"):
        st.dataframe(summary_table(summary, pct=False), hide_index=True, width="stretch")
        st.caption(f"Kruskal-Wallis p = {summary.attrs['kruskal_p']:.3g}.")

with st.expander("When do brands actually post? (volume)"):
    vol = banded.groupby(["weekday_pkt", "hour_band_pkt"]).size().unstack().reindex(index=WEEKDAYS, columns=BAND_ORDER).fillna(0)
    vfig = go.Figure(go.Heatmap(z=vol.to_numpy(), x=BAND_ORDER, y=WEEKDAYS, colorscale=[[0, "#cde2fb"], [1, "#104281"]],
                                texttemplate="%{z:.0f}", xgap=2, ygap=2, colorbar=dict(title="videos"),
                                hovertemplate="%{y}, %{x}<br>%{z:.0f} videos<extra></extra>"))
    vfig.update_layout(height=400, margin=dict(l=10, r=10, t=20, b=30), yaxis=dict(autorange="reversed"))
    st.plotly_chart(vfig, width="stretch")
    st.caption("Few videos in a slot means less evidence about it, not that the slot is bad.")

st.caption("Associational only: a slot that looks better may simply be when brands publish their strongest "
           "campaigns. Test it with an A/B schedule before changing your posting plan.")
