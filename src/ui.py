"""Presentation helpers only: native controls, scoped branding and chart styling."""

from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analytics.compare import MIN_N
from src.app_data import Loaded, load_dashboard_data
from src.config import ROOT, load_brands
from src.processing.features import DURATION_ORDER

SERIES = "#2a78d6"        # categorical slot 1 (reference palette), one series per chart
MUTED = "#a3a29c"         # insufficient-n groups
BRAND_NAMES = {b.brand_id: b.display_name for b in load_brands()}

# Theme colors live in .streamlit/config.toml; keep analytical colors independent.
GRID = "rgba(135, 155, 183, 0.18)"


def _eyebrow(text: str) -> None:
    """Small, wrapping label; CSS targets only markup owned by this module."""
    st.html(
        '<style>.detective-eyebrow {font:600 .75rem/1.5 sans-serif;'
        'letter-spacing:.12em;text-transform:uppercase;margin:0 0 .5rem;opacity:.75;}'
        '</style>'
        f'<p class="detective-eyebrow">{escape(text)}</p>'
    )


def page_header(title: str, description: str = "", *, eyebrow: str = "Workspace") -> None:
    _eyebrow(eyebrow)
    st.title(title)
    if description:
        st.caption(description)


def section_header(title: str, description: str = "") -> None:
    st.subheader(title)
    if description:
        st.caption(description)


def sidebar_brand() -> None:
    st.logo(str(ROOT / ".streamlit" / "brand.svg"), size="large",
            icon_image=str(ROOT / ".streamlit" / "icon.svg"))


def style_chart(fig: go.Figure) -> go.Figure:
    """Style a copy, leaving trace data, axes semantics and the source figure intact."""
    styled = go.Figure(fig)
    styled.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", size=12),
        hoverlabel=dict(bgcolor="#17243a", bordercolor="#40536d", font=dict(color="#f0f5fc", size=13)),
        hovermode="closest",
    )
    styled.update_xaxes(automargin=True, gridcolor=GRID)
    styled.update_yaxes(automargin=True, gridcolor=GRID)
    return styled


def plotly_chart(fig: go.Figure, **kwargs):
    """A consistent native chart surface with a heading that wraps on phones."""
    styled = style_chart(fig)
    title = styled.layout.title.text
    axis_caption = styled.layout.xaxis.title.text
    if axis_caption and len(axis_caption) > 28:
        # Native captions wrap to the available width; Plotly axis titles do not.
        styled.update_xaxes(title_text=None)
    else:
        axis_caption = None
    if title:
        styled.update_layout(title_text=None, margin_t=20)
    with st.container(border=True):
        if title:
            st.markdown(f"**{title}**")
        kwargs.setdefault("width", "stretch")
        kwargs.setdefault("theme", "streamlit")
        chart = st.plotly_chart(styled, **kwargs)
        if axis_caption:
            st.caption(f"Horizontal axis · {axis_caption}")
        return chart


def get_data() -> Loaded:
    """Real data is kept for the session; a synthetic fallback is NOT, so fixed secrets take effect on the next click."""
    cached = st.session_state.get("loaded")
    if cached is not None and cached.source != "synthetic":
        return cached
    if cached is not None and cached.note == "" and cached.source == "synthetic":
        return cached  # deliberate synthetic (tests / no secrets configured): nothing to retry
    loaded = load_dashboard_data()
    st.session_state["loaded"] = loaded
    return loaded


def source_banner(loaded: Loaded) -> None:
    with st.sidebar.container(border=True):
        labels = {"synthetic": "SYNTHETIC DEMO", "snapshot": "LOCAL SNAPSHOT",
                  "remote": "PUBLISHED SNAPSHOT", "live": "LIVE API · CACHED 24 H"}
        st.caption(f"DATASET · {labels.get(loaded.source, loaded.source)}")
        detail = ("Fictional brands · testing only" if loaded.source == "synthetic"
                  else "Public metrics · 30-day retention")
        st.caption(f"Snapshot · {loaded.snapshot_date}  \n{detail}")
    if loaded.source == "synthetic":
        st.warning("**SYNTHETIC DEMO DATA.** Generated for testing with fictional brands. "
                   "These are **not** real measurements. " + loaded.note)
    else:
        label = {"snapshot": "local snapshot", "remote": "weekly published snapshot",
                 "live": "live API collection (cached 24 h)"}.get(loaded.source, loaded.source)
        st.info(f"Real YouTube Data API data · {label} · snapshot **{loaded.snapshot_date}** · "
                "public metrics of 8 Pakistani clothing brands' official channels. " + loaded.note)


def brand_label(brand_id: str) -> str:
    return BRAND_NAMES.get(brand_id, brand_id)


def sidebar_filters(videos: pd.DataFrame) -> pd.DataFrame:
    """Apply the shared filters. Low-reliability videos (<100 views or <14 days old) are always excluded."""
    st.sidebar.subheader("Filters")
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
