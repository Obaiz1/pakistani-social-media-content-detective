"""Exports: aggregated summary tables (Excel/CSV) and a PDF report with charts + caveats.

Only aggregates leave the app; video-level YouTube API data and comment text are never exported.
"""

import io
from datetime import date

import pandas as pd
from fpdf import FPDF

from src.analytics.compare import compare_groups
from src.analytics.sentiment_agg import sentiment_by
from src.analytics.timing import BAND_ORDER, WEEKDAYS
from src.processing.features import DURATION_ORDER
from src.recommendations.engine import TAG_LABELS, Card, prepare_features

CAVEATS = [
    "Pakistan-related brand content: the audience is not verified as Pakistani (no audience-location data in the API).",
    "Correlation, not causation: posting choices and outcomes share hidden causes (budget, season, product).",
    "View counts can include paid ads; 'likely promoted' videos are excluded by default (heuristic flag).",
    "Groups with n < 20 are not tested. Effect sizes are mostly small or negligible.",
    "Public YouTube metrics only: shares, saves, reach and impressions are not available.",
]

SUMMARY_COLS = ["group", "n", "median", "ci_low", "ci_high", "rest_median", "cliffs_delta", "effect", "p_adj", "significant"]


def summary_tables(videos: pd.DataFrame, comments: pd.DataFrame | None = None,
                   brand_label=lambda b: b) -> dict[str, pd.DataFrame]:
    df = prepare_features(videos)
    tables = {
        "Brands (ER)": compare_groups(df, "brand_id", "er_views"),
        "Video length": compare_groups(df, "duration_bucket", "rel_er", order=DURATION_ORDER),
        "Campaign": compare_groups(df, "campaign_tags", "rel_er").assign(
            group=lambda t: t["group"].map(lambda g: "no campaign theme" if g == "other" else TAG_LABELS.get(g, g))),
        "Hashtags": compare_groups(df, "hashtag_band", "rel_er", order=["0", "1–2", "3–5", "6+"]),
        "Time band (PKT)": compare_groups(df, "hour_band_pkt", "rel_er", order=BAND_ORDER),
        "Weekday (PKT)": compare_groups(df, "weekday_pkt", "rel_er", order=WEEKDAYS),
    }
    tables = {k: v[[c for c in SUMMARY_COLS if c in v]] for k, v in tables.items() if not v.empty}
    tables["Brands (ER)"] = tables["Brands (ER)"].assign(group=lambda t: t["group"].map(brand_label))
    if comments is not None and "sentiment_label" in comments and comments["sentiment_label"].notna().any():
        c = comments.merge(videos[["video_id", "brand_id"]], on="video_id").dropna(subset=["sentiment_label"])
        s = sentiment_by(c, "brand_id")
        if not s.empty:
            tables["Sentiment by brand"] = s.assign(group=lambda t: t["group"].map(brand_label))
    return tables


def cards_frame(cards: list[Card]) -> pd.DataFrame:
    return pd.DataFrame([{"title": c.title, "strength": c.strength, "n": c.n, "what": c.what, "where": c.where,
                          "when": c.when, "why": c.why, "ab_test": c.ab_test,
                          "limitations": " | ".join(c.limitations)} for c in cards])


def to_excel_bytes(tables: dict[str, pd.DataFrame], cards: list[Card], meta: dict) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        pd.DataFrame({"field": list(meta) + ["caveat"] * len(CAVEATS),
                      "value": list(meta.values()) + CAVEATS}).to_excel(xw, sheet_name="About", index=False)
        if cards:
            cards_frame(cards).to_excel(xw, sheet_name="Recommendations", index=False)
        for name, t in tables.items():
            t.to_excel(xw, sheet_name=name[:31], index=False)
    return buf.getvalue()


# ---------------- PDF ----------------

_REPLACE = {"–": "-", "—": "-", "−": "-", "δ": "delta", "≥": ">=", "≤": "<=", "×": "x", "’": "'", "‘": "'",
            "“": '"', "”": '"', "…": "...", "→": "->", "·": "-", "~": "~"}


def latin1(text: str) -> str:
    """Core PDF fonts are Latin-1 only; transliterate symbols and drop anything else (e.g. emoji)."""
    for k, v in _REPLACE.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "ignore").decode("latin-1")


class _Report(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", size=8)
        self.set_text_color(110)
        self.cell(0, 8, latin1(f"AI Social Media Content Detective - page {self.page_no()}"), align="C")


def _dot_ci_chart(pdf: FPDF, t: pd.DataFrame, title: str, reference: float | None, pct: bool) -> None:
    """Horizontal median + 95% CI chart drawn with PDF primitives (blue = tested, grey = n<20)."""
    rows = t.reset_index(drop=True)
    label_w, plot_w, row_h = 62, 110, 6.5
    lo = float(pd.concat([rows["ci_low"], rows["median"]]).min())
    hi = float(pd.concat([rows["ci_high"], rows["median"]]).max())
    if reference is not None:
        lo, hi = min(lo, reference), max(hi, reference)
    pad = (hi - lo) * 0.08 or 0.1
    lo, hi = lo - pad, hi + pad
    x0 = pdf.l_margin + label_w
    sx = lambda v: x0 + (v - lo) / (hi - lo) * plot_w  # noqa: E731
    if pdf.get_y() + 14 + row_h * len(rows) > pdf.h - 20:
        pdf.add_page()
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(20)
    pdf.cell(0, 6, latin1(title), new_x="LMARGIN", new_y="NEXT")
    top = pdf.get_y() + 1
    if reference is not None:
        pdf.set_draw_color(160)
        pdf.set_dash_pattern(dash=1, gap=1)
        pdf.line(sx(reference), top, sx(reference), top + row_h * len(rows))
        pdf.set_dash_pattern()
    pdf.set_font("Helvetica", size=8)
    for i, r in rows.iterrows():
        y = top + i * row_h + row_h / 2
        pdf.set_text_color(40)
        pdf.set_xy(pdf.l_margin, y - 2.5)
        pdf.cell(label_w - 2, 5, latin1(f"{r['group']} (n={int(r['n'])})")[:42], align="R")
        color = (42, 120, 214) if r.get("sufficient", r["n"] >= 20) else (163, 162, 156)
        pdf.set_draw_color(*color)
        pdf.set_fill_color(*color)
        pdf.set_line_width(0.5)
        if pd.notna(r["ci_low"]):
            pdf.line(sx(r["ci_low"]), y, sx(r["ci_high"]), y)
        pdf.ellipse(sx(r["median"]) - 1.2, y - 1.2, 2.4, 2.4, style="F")
    pdf.set_line_width(0.2)
    axis_y = top + row_h * len(rows) + 1
    pdf.set_draw_color(120)
    pdf.line(x0, axis_y, x0 + plot_w, axis_y)
    pdf.set_text_color(90)
    for k in range(5):
        v = lo + (hi - lo) * k / 4
        pdf.set_xy(sx(v) - 10, axis_y + 0.5)
        pdf.cell(20, 4, f"{v:.1%}" if pct else f"{v:.2f}", align="C")
    pdf.set_y(axis_y + 7)


def pdf_report(tables: dict[str, pd.DataFrame], cards: list[Card], meta: dict) -> bytes:
    pdf = _Report(format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 9, latin1("AI Social Media Content Detective"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(70)
    pdf.multi_cell(0, 5, latin1("What YouTube content gets Pakistani clothing-brand audiences to engage? "
                                f"Generated {date.today().isoformat()}."), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 5, latin1(" | ".join(f"{k}: {v}" for k, v in meta.items())), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    def heading(text):
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(20)
        pdf.cell(0, 7, latin1(text), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=9)
        pdf.set_text_color(40)

    heading("Recommendations (statistically supported, effect size >= small)")
    if not cards:
        pdf.multi_cell(0, 5, latin1("No finding was both significant and large enough to act on for this selection."), new_x="LMARGIN", new_y="NEXT")
    for c in cards:
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(0, 5, latin1(f"{c.title}  [{c.strength}, n={c.n}]"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=9)
        for k in ("what", "when", "why", "ab_test"):
            pdf.multi_cell(0, 4.5, latin1(f"{'A/B TEST' if k == 'ab_test' else k.upper()}: {getattr(c, k)}"),
                           new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1.5)

    heading("Evidence (median with 95% CI; grey = n < 20, not tested)")
    charts = [("Brands (ER)", "Engagement rate by brand", None, True),
              ("Video length", "Relative engagement by video length", 1.0, False),
              ("Campaign", "Relative engagement by campaign", 1.0, False),
              ("Time band (PKT)", "Relative engagement by PKT time band", 1.0, False),
              ("Weekday (PKT)", "Relative engagement by weekday", 1.0, False)]
    for key, title, ref, pct in charts:
        if key in tables and not tables[key].empty:
            t = tables[key].assign(sufficient=tables[key]["n"] >= 20)
            _dot_ci_chart(pdf, t, title, ref, pct)

    if "Sentiment by brand" in tables:
        heading("Comment sentiment by brand (net = share positive - share negative)")
        for r in tables["Sentiment by brand"].itertuples():
            ci = f"[{r.net_low:+.2f}, {r.net_high:+.2f}]" if pd.notna(r.net_low) else "(n < 20)"
            pdf.cell(0, 4.5, latin1(f"{r.group}: net {r.net:+.2f} {ci}, n={r.n}"), new_x="LMARGIN", new_y="NEXT")

    heading("Caveats")
    for cv in CAVEATS:
        pdf.multi_cell(0, 4.5, latin1(f"- {cv}"), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
