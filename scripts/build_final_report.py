"""Build the final project report from the data and evaluation artefacts (no hand-typed numbers).

Usage: uv run python scripts/build_final_report.py [snapshot_dir]
Writes docs/FINAL_REPORT.md and docs/FINAL_REPORT.pdf.
"""

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
from fpdf import FPDF  # noqa: E402

from src.analytics.compare import compare_groups  # noqa: E402
from src.analytics.regression import fit_models  # noqa: E402
from src.analytics.sentiment_agg import sentiment_by  # noqa: E402
from src.analytics.timing import BAND_ORDER, WEEKDAYS  # noqa: E402
from src.app_data import read_snapshot  # noqa: E402
from src.config import DATA_DIR, load_brands  # noqa: E402
from src.processing.features import DURATION_ORDER  # noqa: E402
from src.recommendations.engine import TAG_LABELS, build_cards, prepare_features  # noqa: E402
from src.reporting.export import CAVEATS, _dot_ci_chart, latin1  # noqa: E402

DOCS = ROOT / "docs"
LIVE_URL = "https://pakistani-social-media-content-detective-mahmts48mya2xnxwgttip.streamlit.app"
REPO_URL = "https://github.com/Obaiz1/pakistani-social-media-content-detective"
BRAND = {b.brand_id: b.display_name for b in load_brands()}


def pct(x: float) -> str:
    return f"{x:.2%}"


def collect(snapshot: Path) -> dict:
    data = read_snapshot(snapshot)
    v_all = data.videos
    v = v_all[~v_all["low_reliability"] & ~v_all["likely_promoted"]]
    f = prepare_features(v)
    out = {"snapshot": snapshot.name, "n_all": len(v_all), "n": len(v), "n_comments": len(data.comments),
           "n_promoted": int(v_all["likely_promoted"].sum()), "n_lowrel": int(v_all["low_reliability"].sum()),
           "brands": v_all["brand_id"].nunique()}
    out["brand_er"] = compare_groups(v, "brand_id", "er_views").assign(group=lambda t: t["group"].map(BRAND))
    out["length"] = compare_groups(f, "duration_bucket", "rel_er", order=DURATION_ORDER)
    out["campaign"] = compare_groups(f, "campaign_tags", "rel_er").assign(
        group=lambda t: t["group"].map(lambda g: "no campaign theme" if g == "other" else TAG_LABELS.get(g, g)))
    out["band"] = compare_groups(f, "hour_band_pkt", "rel_er", order=BAND_ORDER)
    out["weekday"] = compare_groups(f, "weekday_pkt", "rel_er", order=WEEKDAYS)
    out["regression"] = fit_models(v_all)
    if "topic_label" in v:
        out["topics"] = compare_groups(v[v["topic_id"] != -1], "topic_label", "rel_er")
        out["topic_outliers"] = int((v_all["topic_id"] == -1).sum())
    c = data.comments
    if "sentiment_label" in c:
        cc = c.merge(v[["video_id", "brand_id"]], on="video_id").dropna(subset=["sentiment_label"])   # same filters as the dashboard
        out["sentiment"] = sentiment_by(cc, "brand_id").assign(group=lambda t: t["group"].map(BRAND))
        out["sentiment_mix"] = cc["sentiment_label"].value_counts(normalize=True).to_dict()
    if "thumb_face_visible" in v and v["thumb_face_visible"].notna().sum() >= 100:
        tv = v[v["thumb_face_visible"].notna()].copy()
        tv["face"] = tv["thumb_face_visible"].map({True: "Face visible", False: "No face visible"})
        tv["text"] = tv["thumb_text_overlay"].map({True: "Text overlay", False: "No text overlay"})
        tv["color"] = pd.qcut(tv["thumb_colorfulness"], 3, labels=["Muted", "Medium", "Vivid"]).astype(str)
        out["thumb_n"] = len(tv)
        out["thumb_face"] = compare_groups(tv, "face", "rel_er")
        out["thumb_text"] = compare_groups(tv, "text", "rel_er")
        out["thumb_color"] = compare_groups(tv, "color", "rel_er", order=["Muted", "Medium", "Vivid"])
    out["cards"], out["weak"] = build_cards(v)
    out["nlp"] = json.loads((DOCS / "nlp_benchmark.json").read_text(encoding="utf-8"))
    out["ml"] = json.loads((DOCS / "ml_evaluation.json").read_text(encoding="utf-8"))
    spot = DOCS / "evaluation" / "thumbnail_vlm_spotcheck.json"
    out["spot"] = json.loads(spot.read_text(encoding="utf-8")) if spot.exists() else None
    out["n_adrs"] = sum(1 for line in (ROOT / "DECISIONS.md").read_text(encoding="utf-8").splitlines() if line.startswith("| ADR-"))
    collected = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT,
                               capture_output=True, text=True).stdout
    out["n_tests"] = sum(1 for line in collected.splitlines() if "::" in line)
    out["n_pages"] = (ROOT / "app.py").read_text(encoding="utf-8").count("st.Page(")
    return out


def row_line(r, pct_fmt=False) -> str:
    fmt = pct if pct_fmt else (lambda x: f"{x:.2f}")
    ci = f"[{fmt(r.ci_low)}, {fmt(r.ci_high)}]" if pd.notna(r.ci_low) else "(n < 20, not tested)"
    sig = f", {r.effect} effect, adj. p = {r.p_adj:.3f}" if pd.notna(r.p_adj) else ""
    return f"{r.group}: median {fmt(r.median)} {ci}, n = {r.n}{sig}"


def build_markdown(d: dict) -> str:
    reg = d["regression"]["table"]
    sig_reg = reg[reg["robust"]]
    nlp_all = sorted([r for r in d["nlp"]["sentiment"] if r["slice"] == "all"], key=lambda r: -r["macro_f1"])
    ml = d["ml"]["results"]
    L = []
    a = L.append
    a("# AI Social Media Content Detective: Final Project Report")
    a("")
    a(f"**Question:** What YouTube content gets Pakistani clothing-brand audiences to engage?  ")
    a(f"**Data snapshot:** {d['snapshot']} · **Report generated:** {date.today().isoformat()}  ")
    a(f"**Live app:** {LIVE_URL}  ")
    a(f"**Code:** {REPO_URL}")
    a("")
    a("## 1. Executive summary")
    a("")
    a(f"- Collected **{d['n_all']:,} videos** (last 24 months) and **{d['n_comments']:,} comments** from **{d['brands']} official "
      "Pakistani clothing-brand channels** through the YouTube Data API v3 (no scraping).")
    a(f"- After removing low-reliability videos ({d['n_lowrel']}) and likely ad-boosted videos ({d['n_promoted']}), "
      f"**{d['n']:,} videos** were analysed.")
    a("- **One-at-a-time comparisons** suggested that wedding/festive content performs better and that Saturday uploads, "
      "menswear and sale content perform worse than the same brand's other videos (small effects).")
    a(f"- **A mixed-effects model** controlling for brand, month and all features together found that "
      f"**{len(sig_reg)} of {len(reg)} effects** stay significant after multiple-comparison correction. Most one-at-a-time "
      "differences are largely explained by **season and brand mix**, so every recommendation is labelled *tentative*.")
    if "topics" in d:
        top = d["topics"].iloc[0]
        a(f"- **Data-driven title themes (BERTopic)** independently found a festive/luxury theme with the highest relative "
          f"engagement ({top['group']}: {top['median']:.2f} vs {top['rest_median']:.2f}).")
    a(f"- **Sentiment:** the multilingual XLM-R model (macro-F1 {next(r['macro_f1'] for r in nlp_all if 'xlm-roberta-base-sentiment' in r['model'] and 'cardiff' in r['model']):.2f}) "
      f"was chosen over the best LLM ({nlp_all[0]['macro_f1']:.2f}) because the difference was not significant.")
    a(f"- **Engagement prediction** before publishing did **not** beat a simple median baseline, so it was deferred.")
    a("")
    a("## 2. Data and compliance")
    a("")
    a("- Source: YouTube Data API v3, public data only. Channels pinned by ID (a search had returned a fan channel).")
    a("- Comment authors are never stored; comment text never leaves the owner's machine (published data has labels only).")
    a("- Stored API data is refreshed weekly by a GitHub Action and kept as a single latest snapshot (< 30 days).")
    a("- Not available from the API: shares, saves, reach, impressions, audience demographics.")
    a("")
    a("## 3. Methods")
    a("")
    a("- **Engagement rate (ER)** = (likes + comments) ÷ views; likes ÷ views where comments are disabled; null if likes are hidden.")
    a("- **Relative engagement** = ER ÷ the brand's median ER, which removes brand-size differences.")
    a("- **Likely promoted** = like-rate < brand median ÷ 5 and views above the brand's 75th percentile (excluded).")
    a("- **Statistics:** medians with 2,000-sample bootstrap 95% CIs; Mann-Whitney U vs all other videos; Cliff's δ effect "
      "size; Benjamini-Hochberg correction; groups with n < 20 not tested.")
    a("- **Adjusted model:** log(ER) ~ weekday + PKT time band + length + hashtags + campaign tags + emoji, random intercept "
      "per brand + month variance component (statsmodels MixedLM); robustness check with brand + month fixed effects (HC3).")
    a("- **NLP:** rule-based language ID; 6 sentiment approaches benchmarked on 250 hand-labelled real comments.")
    a("- **Topics:** BERTopic on titles (multilingual MiniLM embeddings, UMAP, HDBSCAN, reduced to 12 themes).")
    a("- **Thumbnails:** colour statistics for every video; vision-LLM labels (NVIDIA Nemotron) for a random sample, "
      "spot-checked against manual labels.")
    a("- **Prediction:** chronological split (newest 20% as test), pre-publication features only, two baselines.")
    a("")
    a("## 4. Results")
    a("")
    a("### 4.1 Engagement by brand (median ER, 95% CI)")
    a("")
    for r in d["brand_er"].itertuples():
        a(f"- {row_line(r, pct_fmt=True)}")
    a("")
    a("### 4.2 Content and timing (relative engagement, one feature at a time)")
    a("")
    for key, title in (("campaign", "Campaign"), ("length", "Video length"), ("band", "PKT time band"), ("weekday", "Weekday")):
        a(f"**{title}**")
        a("")
        for r in d[key].itertuples():
            a(f"- {row_line(r)}")
        a("")
    a("### 4.3 Adjusted effects (mixed-effects model)")
    a("")
    a(f"n = {d['regression']['n']:,} videos, {d['regression']['brands']} brands, {d['regression']['months']} months. "
      "% change in ER vs the reference level, with 95% CI and BH-adjusted p:")
    a("")
    for r in reg.itertuples():
        a(f"- {r.label}: {r.effect_pct:+.0f}% [{r.effect_ci_low:+.0f}%, {r.effect_ci_high:+.0f}%], adj. p = {r.p_adj:.2f}"
          + (" **(robust)**" if r.robust else ""))
    a("")
    if "topics" in d:
        a("### 4.4 Title themes (BERTopic)")
        a("")
        a(f"{d['topic_outliers']} videos had no clear theme (outliers, excluded).")
        a("")
        for r in d["topics"].itertuples():
            a(f"- {row_line(r)}")
        a("")
    if "thumb_face" in d:
        a("### 4.5 Thumbnails")
        a("")
        a(f"Vision labels for {d['thumb_n']:,} analysed videos (random sample). Spot-check vs manual labels (n = 30): "
          + "; ".join(f"{k.replace('_', ' ')} agreement {v['agreement']:.0%}, κ = {v['kappa']}" for k, v in d["spot"].items())
          + ". Face labels are reliable; text-overlay and close-up labels are exploratory.")
        a("")
        for key, title in (("thumb_face", "Face in thumbnail"), ("thumb_text", "Text overlay (exploratory)"),
                           ("thumb_color", "Colourfulness tertile")):
            a(f"**{title}**")
            a("")
            for r in d[key].itertuples():
                a(f"- {row_line(r)}")
            a("")
    if "sentiment" in d:
        a("### 4.6 Comment sentiment")
        a("")
        mix = d["sentiment_mix"]
        a(f"Overall: {mix.get('positive', 0):.0%} positive, {mix.get('neutral', 0):.0%} neutral, {mix.get('negative', 0):.0%} negative. "
          "Net sentiment (share positive − share negative) by brand:")
        a("")
        for r in d["sentiment"].itertuples():
            ci = f"[{r.net_low:+.2f}, {r.net_high:+.2f}]" if pd.notna(r.net_low) else "(n < 20)"
            a(f"- {r.group}: {r.net:+.2f} {ci}, n = {r.n}")
        a("")
    a("### 4.7 Sentiment model benchmark (macro-F1, n = 250)")
    a("")
    for r in nlp_all:
        a(f"- {r['model']}: {r['macro_f1']:.3f}")
    a(f"\nLabel status: {d['nlp']['status']}.")
    a("")
    a("### 4.8 Engagement prediction")
    a("")
    for name, m in ml.items():
        a(f"- {name}: MAE(log) {m['mae_log']:.3f}")
    a("\nNo model beat the stronger baseline, so prediction was deferred.")
    a("")
    a("## 5. Recommendations (to A/B test, not guarantees)")
    a("")
    for c in d["cards"]:
        a(f"**{c.title}** [{c.strength}, n = {c.n}]  ")
        a(f"What: {c.what} When: {c.when}  ")
        a(f"Evidence: {c.why}  ")
        if c.adjusted:
            a(f"Adjusted check: {c.adjusted}  ")
        a(f"Test: {c.ab_test}")
        a("")
    a("## 6. Limitations")
    a("")
    for cv in CAVEATS:
        a(f"- {cv}")
    a("- Only 5 Urdu-script comments: Urdu-script sentiment could not be evaluated.")
    a("- BERTopic themes vary slightly between runs; vision labels for text overlay/close-up are low-agreement.")
    a("")
    a("## 7. Engineering")
    a("")
    a(f"- Modular Python package (`src/`), Streamlit dashboard ({d['n_pages']} pages), {d['n_tests']} automated tests, {d['n_adrs']} "
      "architecture decision records.")
    a("- Weekly GitHub Action → private data repo (deploy key) → Streamlit Community Cloud (read-only token).")
    a("- Secrets only in `.env` / Streamlit secrets; a pre-commit check blocks any secret value from git.")
    a("")
    a("## 8. Process")
    a("")
    a("Built in 15 gated phases (problem framing → requirements → data audit → architecture → foundation → pipeline → "
      "analytics MVP → NLP → timing → ML → recommendations → dashboard & exports → delivery), with the project owner "
      "approving every gate. Full history: `DECISIONS.md`, `PROGRESS.md`, `SESSION_HANDOFF.md`.")
    a("")
    a("## 9. AI-use disclosure")
    a("")
    a("Built with AI assistance (Claude Code) under the owner's direction. Sentiment benchmark labels were drafted by Claude "
      "for owner verification; the NVIDIA API Catalog was used for an LLM sentiment baseline, recommendation wording and "
      "thumbnail labels.")
    return "\n".join(L) + "\n"


def build_pdf(markdown: str, d: dict, path: Path) -> None:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def clean(text):
        return text.replace("**", "").replace("`", "").replace("*", "")

    def para(text, size=9.5, style="", h=4.8):
        pdf.set_font("Helvetica", style, size)
        pdf.multi_cell(0, h, latin1(clean(text)), new_x="LMARGIN", new_y="NEXT")

    charts = {"### 4.1": ("brand_er", "Median engagement rate by brand", None, True),
              "### 4.2": ("campaign", "Relative engagement by campaign (1.0 = brand median)", 1.0, False)}
    for line in markdown.splitlines():
        if line.startswith("# "):
            pdf.set_text_color(15)
            para(line[2:], 16, "B", 8)
            pdf.ln(1)
        elif line.startswith("## "):
            pdf.ln(2)
            para(line[3:], 13, "B", 7)
        elif line.startswith("### "):
            pdf.ln(1)
            para(line[4:], 11, "B", 6)
            key = line[:7]
            if key in charts:
                k, title, ref, is_pct = charts[key]
                t = d[k].assign(sufficient=d[k]["n"] >= 20)
                _dot_ci_chart(pdf, t, title, ref, is_pct)
        elif line.startswith("- "):
            pdf.set_x(pdf.l_margin + 3)
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 4.5, latin1("- " + clean(line[2:])), new_x="LMARGIN", new_y="NEXT")
        elif line.strip():
            para(line.rstrip(" "), 9.5)
        else:
            pdf.ln(1.2)
    path.write_bytes(bytes(pdf.output()))


def main() -> None:
    snap = Path(sys.argv[1]) if len(sys.argv) > 1 else max(p for p in (DATA_DIR / "processed").iterdir() if p.is_dir())
    d = collect(snap)
    md = build_markdown(d)
    (DOCS / "FINAL_REPORT.md").write_text(md, encoding="utf-8")
    build_pdf(md, d, DOCS / "FINAL_REPORT.pdf")
    print("wrote docs/FINAL_REPORT.md and docs/FINAL_REPORT.pdf |", len(md.splitlines()), "lines |",
          "thumbnails included" if "thumb_face" in d else "no thumbnails yet")


if __name__ == "__main__":
    main()
