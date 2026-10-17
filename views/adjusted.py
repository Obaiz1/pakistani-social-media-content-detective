import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analytics.regression import fit_models
from src.ui import MUTED, SERIES, get_data, sidebar_filters, source_banner

loaded = get_data()
st.title("Adjusted effects (mixed-effects model)")
st.caption("The other pages compare one feature at a time. Here every feature is estimated **while holding all the "
           "others constant**, with a random intercept per brand and a month-level variance component "
           "(seasonality and drift). Bars show the % change in engagement rate vs the reference level.")
source_banner(loaded)
videos = sidebar_filters(loaded.data.videos)
if len(videos) < 200:
    st.info("Too few videos under the current filters to fit the model (need ≥ 200).")
    st.stop()

with st.spinner("Fitting models…"):
    try:
        res = fit_models(videos)
    except Exception as exc:  # singular designs on tiny selections
        st.info(f"The model could not be fitted for this selection ({type(exc).__name__}). Widen the filters.")
        st.stop()
t = res["table"].iloc[::-1]

fig = go.Figure()
for robust, color, name in ((True, SERIES, "significant in both models"), (False, MUTED, "not significant (BH-adjusted)")):
    part = t[t["robust"] == robust]
    if part.empty:
        continue
    fig.add_trace(go.Scatter(
        x=part["effect_pct"], y=part["label"], mode="markers", name=name, marker=dict(size=9, color=color),
        error_x=dict(type="data", symmetric=False, array=part["effect_ci_high"] - part["effect_pct"],
                     arrayminus=part["effect_pct"] - part["effect_ci_low"], thickness=2, width=0, color=color),
        hovertemplate="%{y}<br>%{x:+.1f}%<extra></extra>"))
fig.add_vline(x=0, line=dict(width=1, dash="dot", color=MUTED))
fig.update_layout(height=max(380, 30 * len(t) + 120), margin=dict(l=10, r=10, t=30, b=40),
                  xaxis=dict(title="% change in engagement rate (95% CI)", ticksuffix="%", zeroline=False),
                  yaxis=dict(showgrid=False, categoryorder="array", categoryarray=list(t["label"])),
                  legend=dict(orientation="h", y=-0.12))
st.plotly_chart(fig, width="stretch")

n_sig = int(res["table"]["robust"].sum())
st.markdown(
    f"**{n_sig} of {len(res['table'])} effects** survive multiple-comparison correction in both the mixed model and "
    "the fixed-effects robustness check. " + (
        "Once brand, month and the other features are controlled for, **no single content or timing feature has a "
        "reliable effect** in this data. The one-at-a-time differences on other pages are partly explained by season "
        "and brand mix (e.g. wedding/festive videos cluster in the strong wedding season)." if n_sig == 0 else ""))

with st.expander("Table view & model details"):
    show = res["table"][["label", "effect_pct", "effect_ci_low", "effect_ci_high", "p_adj", "effect_pct_fe", "p_adj_fe", "robust"]]
    st.dataframe(show.rename(columns={
        "label": "Term", "effect_pct": "Effect % (mixed)", "effect_ci_low": "CI low %", "effect_ci_high": "CI high %",
        "p_adj": "Adj. p (mixed)", "effect_pct_fe": "Effect % (FE OLS)", "p_adj_fe": "Adj. p (FE OLS)",
        "robust": "Robust"}).style.format(precision=2), hide_index=True, width="stretch")
    st.caption(f"n = {res['n']:,} videos · {res['brands']} brands · {res['months']} months · converged: {res['converged']} · "
               f"brand random-intercept variance {res['brand_var']:.3f} (log scale). Outcome: log(engagement rate). "
               "Reference levels: Monday, Afternoon (12–16), 16–30s, 0 hashtags, untagged. Associational, not causal.")
