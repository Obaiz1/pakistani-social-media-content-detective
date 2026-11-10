import json

import pandas as pd
import streamlit as st

from src.config import ROOT
from src.ui import get_data, page_header, section_header, source_banner

loaded = get_data()
page_header(
    "Data & Method",
    "Trace the source, measurement definitions and evidence standards behind the dashboard.",
    eyebrow="Evidence / Methodology",
)
source_banner(loaded)
v, c = loaded.data.videos, loaded.data.comments

with st.container(border=True):
    section_header("Source", "Dataset provenance and the limits of available public data.")
    if loaded.source == "synthetic":
        st.markdown(
            f"- **SYNTHETIC DEMO DATA**, generated for testing. Reference date **{loaded.snapshot_date}**.\n"
            f"- {v['brand_id'].nunique()} fictional brands, {len(v):,} generated videos and {len(c):,} generated comments.\n"
            "- These records are **not real measurements** or evidence about actual brand performance."
        )
    else:
        st.markdown(
            f"- **YouTube Data API v3**, public data only. Snapshot **{loaded.snapshot_date}**, last 24 months.\n"
            f"- {v['brand_id'].nunique()} official brand channels, pinned by channel ID (`config/brands.yaml`).\n"
            f"- {len(v):,} videos, {len(c):,} top-level comments (author identity never stored)."
        )
    st.markdown(
        "- The production project uses **YouTube Data API v3**, public data only. Comment author identity is never stored.\n"
        "- Not available from the API: shares, saves, reach, impressions, audience country/age/gender.\n"
        "- Per the YouTube API Developer Policies, stored data is refreshed or deleted within 30 days."
    )

section_header("Metric definitions", "Missing measurements remain unknown; each metric keeps its original denominator.")
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

section_header("Statistics", "Uncertainty, sample sizes and multiple comparisons are part of every interpretation.")
st.markdown(
    "- Medians with **95% bootstrap confidence intervals** (2,000 resamples).\n"
    "- Each group vs all other videos: **Mann-Whitney U**, effect size **Cliff's δ** "
    "(|δ| < .147 negligible, < .33 small, < .474 medium, else large).\n"
    "- p-values adjusted with **Benjamini-Hochberg** across the groups in a chart; significant = adj. p < 0.05.\n"
    "- Groups with **n < 20** are shown but not tested.\n"
    "- Time is analysed in **Pakistan Standard Time (UTC+5)**."
)

section_header("Data quality in this dataset", "Full-dataset coverage before analytical filters are applied.")
q1, q2, q3, q4 = st.columns(4)
q1.metric("Likely promoted", f"{int(v['likely_promoted'].sum()):,}", border=True)
q2.metric("Low reliability", f"{int(v['low_reliability'].sum()):,}", border=True)
q3.metric("Hidden likes", f"{int(v['like_count'].isna().sum()):,}", border=True)
q4.metric("Videos with comments", f"{int((v['comment_count'].fillna(0) > 0).sum()):,}", border=True)

section_header("Sentiment model benchmark", "Saved evaluation evidence; independent of the current dashboard filters and demo records.")
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

section_header("Engagement prediction (deferred)", "Predictive models are evaluated against simple baselines before they can inform the product.")
ml_path = ROOT / "docs" / "ml_evaluation.json"
if ml_path.exists():
    ml = json.loads(ml_path.read_text(encoding="utf-8"))
    res = pd.DataFrame(ml["results"]).T[["mae_log", "rmse_log", "median_factor_error"]]
    res.columns = ["MAE (log)", "RMSE (log)", "Typical miss (×)"]
    st.dataframe(res.style.format("{:.3f}"), width="stretch")
    st.caption(f"Chronological test on the {ml['n_test']} newest videos ({ml['test_period'][0]} → {ml['test_period'][1]}), "
               f"trained on {ml['n_train']} older ones, pre-publication features only. "
               + ("A model beat the stronger baseline." if ml["verdict_beats_baseline"] else
                  "**No model beat a single typical value**, so prediction is deferred and the dashboard makes no "
                  "per-video forecasts. Brand engagement levels also drifted over time."))

section_header("Limitations", "Keep these boundaries alongside every decision or report.")
st.markdown(
    "- Results describe **Pakistan-related brand content**, not a verified Pakistani audience.\n"
    "- **Correlation ≠ causation**: posting choices and outcomes share many hidden causes (budget, season, product).\n"
    "- View counts can include paid advertising; the promoted flag is a heuristic, not ground truth.\n"
    "- ~99% of videos are ≤ 3 minutes, so format is analysed by length, and long-form evidence is thin.\n"
    "- Comments are sparse; sentiment is reported only at aggregate level."
)
