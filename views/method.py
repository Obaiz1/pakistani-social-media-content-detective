import json

import pandas as pd
import streamlit as st

from src.config import ROOT
from src.ui import get_data, source_banner

loaded = get_data()
st.title("Data & Method")
source_banner(loaded)
v, c = loaded.data.videos, loaded.data.comments

st.subheader("Source")
st.markdown(
    f"- **YouTube Data API v3**, public data only. Snapshot **{loaded.snapshot_date}**, last 24 months.\n"
    f"- {v['brand_id'].nunique()} official brand channels, pinned by channel ID (`config/brands.yaml`).\n"
    f"- {len(v):,} videos, {len(c):,} top-level comments (author identity never stored).\n"
    "- Not available from the API: shares, saves, reach, impressions, audience country/age/gender.\n"
    "- Per the YouTube API Developer Policies, stored data is refreshed or deleted within 30 days."
)

st.subheader("Metric definitions")
st.markdown(
    "| Metric | Definition |\n|---|---|\n"
    "| Engagement rate | (likes + comments) ÷ views. Unknown (not 0) if likes are hidden; "
    "likes ÷ views where the channel **disabled comments** (nobody could comment) |\n"
    "| Like rate | likes ÷ views |\n"
    "| Views per subscriber | views ÷ channel subscribers at snapshot |\n"
    "| Relative engagement | engagement rate ÷ the brand's median engagement rate (reliable videos) |\n"
    "| Likely promoted | like rate < brand median ÷ 5 **and** views > brand 75th percentile |\n"
    "| Low reliability | < 100 views or < 14 days old. Always excluded from statistics |\n"
)

st.subheader("Statistics")
st.markdown(
    "- Medians with **95% bootstrap confidence intervals** (2,000 resamples).\n"
    "- Each group vs all other videos: **Mann-Whitney U**, effect size **Cliff's δ** "
    "(|δ| < .147 negligible, < .33 small, < .474 medium, else large).\n"
    "- p-values adjusted with **Benjamini-Hochberg** across the groups in a chart; significant = adj. p < 0.05.\n"
    "- Groups with **n < 20** are shown but not tested.\n"
    "- Time is analysed in **Pakistan Standard Time (UTC+5)**."
)

st.subheader("Data quality in this dataset")
q1, q2, q3, q4 = st.columns(4)
q1.metric("Likely promoted", f"{int(v['likely_promoted'].sum()):,}")
q2.metric("Low reliability", f"{int(v['low_reliability'].sum()):,}")
q3.metric("Hidden likes", f"{int(v['like_count'].isna().sum()):,}")
q4.metric("Videos with comments", f"{int((v['comment_count'].fillna(0) > 0).sum()):,}")

st.subheader("Sentiment model benchmark")
bench_path = ROOT / "docs" / "nlp_benchmark.json"
if bench_path.exists():
    bench = json.loads(bench_path.read_text(encoding="utf-8"))
    st.caption(f"{bench['status']} · n = {bench['n']} hand-labelled real comments · "
               f"language-ID accuracy {bench['language_id_accuracy']:.0%}")
    rows = pd.DataFrame(bench["sentiment"])
    pivot = rows.pivot_table(index="model", columns="slice", values="macro_f1").reindex(
        columns=[c for c in ("all", "english", "roman_urdu", "other") if c in set(rows["slice"])])
    st.dataframe(pivot.sort_values("all", ascending=False).style.format("{:.3f}"), width="stretch")
    st.caption("Macro-F1 (3 classes). Urdu-script (n=1) and mixed (n=3) slices are too small to score.")
else:
    st.caption("Benchmark not run yet.")

st.subheader("Limitations")
st.markdown(
    "- Results describe **Pakistan-related brand content**, not a verified Pakistani audience.\n"
    "- **Correlation ≠ causation**: posting choices and outcomes share many hidden causes (budget, season, product).\n"
    "- View counts can include paid advertising; the promoted flag is a heuristic, not ground truth.\n"
    "- ~99% of videos are ≤ 3 minutes, so format is analysed by length, and long-form evidence is thin.\n"
    "- Comments are sparse; sentiment (next phase) is reported only at aggregate level."
)
