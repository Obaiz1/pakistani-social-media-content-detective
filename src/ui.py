"""Shared dashboard pieces: data banner, sidebar filters, the median-with-CI chart."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analytics.compare import MIN_N
from src.app_data import Loaded, load_dashboard_data
from src.config import load_brands
from src.processing.features import DURATION_ORDER

SERIES = "#2a78d6"        # categorical slot 1 (reference palette), one series per chart
MUTED = "#a3a29c"         # insufficient-n groups
BRAND_NAMES = {b.brand_id: b.display_name for b in load_brands()}


def get_data() -> Loaded:
    if "loaded" not in st.session_state:
        st.session_state["loaded"] = load_dashboard_data()
    return st.session_state["loaded"]


def source_banner(loaded: Loaded) -> None:
    if loaded.source == "synthetic":
        st.warning("**SYNTHETIC DEMO DATA.** Generated for testing with fictional brands. "
                   "These are **not** real measurements. " + loaded.note)
    else:
        label = "local snapshot" if loaded.source == "snapshot" else "live API collection (cached 24 h)"
        st.info(f"Real YouTube Data API data · {label} · snapshot **{loaded.snapshot_date}** · "
                "public metrics of 8 Pakistani clothing brands' official channels. " + loaded.note)


def brand_label(brand_id: str) -> str:
    return BRAND_NAMES.get(brand_id, brand_id)


def sidebar_filters(videos: pd.DataFrame) -> pd.DataFrame:
    """Apply the shared filters. Low-reliability videos (<100 views or <14 days old) are always excluded."""
    st.sidebar.header("Filters")
    brands = sorted(videos["brand_id"].unique(), key=brand_label)
    chosen = st.sidebar.multiselect("Brands", brands, default=brands, format_func=brand_label, key="f_brands")
    dates = videos["published_at_pkt"].dt.date
    start, end = dates.min(), dates.max()
    picked = st.sidebar.date_input("Published between (PKT)", (start, end), min_value=start, max_value=end,
                                   key="f_dates")
    lo, hi = (picked if isinstance(picked, tuple) and len(picked) == 2 else (start, end))
    buckets = [b for b in DURATION_ORDER if b in set(videos["duration_bucket"].dropna())]
    chosen_buckets = st.sidebar.multiselect("Video length", buckets, default=buckets, key="f_buckets")
    include_promoted = st.sidebar.toggle("Include 'likely promoted' videos", value=False, key="f_promo",
                                         help="Videos whose views look ad-boosted (like-rate < brand median ÷ 5 "
                                              "and views above the brand's 75th percentile). Excluded by default "
                                              "because paid views dilute engagement rates.")
    mask = (videos["brand_id"].isin(chosen) & dates.between(lo, hi)
            & videos["duration_bucket"].isin(chosen_buckets) & ~videos["low_reliability"])
    if not include_promoted:
        mask &= ~videos["likely_promoted"]
    out = videos[mask]
    st.sidebar.caption(f"{len(out):,} of {len(videos):,} videos match. "
                       "Always excluded: <100 views or <14 days old.")
    return out


def median_ci_chart(summary: pd.DataFrame, title: str, x_title: str, pct: bool = True,
                    label=lambda g: g, reference: float | None = None) -> go.Figure:
    """Horizontal dot plot: median with 95% bootstrap CI per group; groups with n < MIN_N are muted."""
    s = summary.iloc[::-1]  # first row on top
    fmt = (lambda v: f"{v:.2%}") if pct else (lambda v: f"{v:.2f}")
    fig = go.Figure()
    for sufficient, color in ((True, SERIES), (False, MUTED)):
        part = s[s["sufficient"] == sufficient]
        if part.empty:
            continue
        hover = [
            f"<b>{label(r.group)}</b><br>median {fmt(r.median)}"
            + (f"<br>95% CI {fmt(r.ci_low)} – {fmt(r.ci_high)}" if sufficient else f"<br>n < {MIN_N}: not tested")
            + f"<br>n = {r.n:,}"
            + (f"<br>vs rest: {r.effect} effect, adj. p = {r.p_adj:.3g}" if pd.notna(r.p_adj) else "")
            for r in part.itertuples()
        ]
        fig.add_trace(go.Scatter(
            x=part["median"], y=[f"{label(g)}  (n={n:,})" for g, n in zip(part["group"], part["n"])],
            mode="markers", marker=dict(size=10, color=color, line=dict(width=2, color="rgba(0,0,0,0)")),
            error_x=dict(type="data", symmetric=False, array=(part["ci_high"] - part["median"]).fillna(0),
                         arrayminus=(part["median"] - part["ci_low"]).fillna(0), thickness=2, width=0,
                         color=color),
            hovertext=hover, hoverinfo="text",
            name="n ≥ 20 (tested)" if sufficient else f"n < {MIN_N} (insufficient)",
            showlegend=not sufficient,
        ))
    if reference is not None:
        fig.add_vline(x=reference, line=dict(width=1, dash="dot", color=MUTED))
    # pin row order to the summary's order (first row on top) instead of trace-appearance order
    rows = [f"{label(g)}  (n={n:,})" for g, n in zip(s["group"], s["n"])]
    fig.update_layout(title=title, height=max(260, 46 * len(s) + 110), margin=dict(l=10, r=10, t=50, b=40),
                      xaxis=dict(title=x_title, tickformat=".1%" if pct else None, zeroline=False,
                                 showgrid=True, gridwidth=1),
                      yaxis=dict(showgrid=False, categoryorder="array", categoryarray=rows),
                      legend=dict(orientation="h", y=-0.2))
    return fig


def summary_table(summary: pd.DataFrame, label=lambda g: g, pct: bool = True) -> pd.DataFrame:
    fmt = (lambda v: f"{v:.2%}") if pct else (lambda v: f"{v:.2f}")
    t = pd.DataFrame({
        "Group": summary["group"].map(label),
        "n": summary["n"],
        "Median": summary["median"].map(fmt),
        "95% CI": [f"{fmt(a)} – {fmt(b)}" if pd.notna(a) else "insufficient n" for a, b in
                   zip(summary["ci_low"], summary["ci_high"])],
        "vs rest (Cliff's δ)": [f"{d:+.2f} ({e})" if pd.notna(d) else "—" for d, e in
                                zip(summary["cliffs_delta"], summary["effect"])],
        "Adj. p (BH)": summary["p_adj"].map(lambda p: f"{p:.3g}" if pd.notna(p) else "—"),
        "Significant": summary["significant"].map({True: "yes", False: "no"}),
    })
    return t
