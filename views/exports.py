from datetime import date

import streamlit as st

from src.recommendations.engine import build_cards
from src.reporting.export import cards_frame, pdf_report, summary_tables, to_excel_bytes
from src.ui import brand_label, get_data, page_header, section_header, sidebar_filters, source_banner

loaded = get_data()
page_header(
    "Report & exports",
    "Download what you see under the current sidebar filters: aggregated tables, recommendation cards and a "
    "PDF report. Video-level YouTube data and comment text are never exported.",
    eyebrow="Evidence / Reports",
)
source_banner(loaded)
videos = sidebar_filters(loaded.data.videos)
if videos.empty:
    st.info("No videos match the current filters.")
    st.stop()

with st.spinner("Building tables…"):
    tables = summary_tables(videos, loaded.data.comments, brand_label)
    cards, _weak = build_cards(videos)
meta = {"data source": "SYNTHETIC demo data (not real)" if loaded.source == "synthetic" else "YouTube Data API v3",
        "snapshot": loaded.snapshot_date, "videos analysed": f"{len(videos):,}",
        "brands": ", ".join(sorted(brand_label(b) for b in videos["brand_id"].unique()))}
stamp = f"{loaded.snapshot_date}_{date.today().isoformat()}"

section_header("Export your analysis", "Every download reflects the current selection. Review the evidence and limitations before sharing.")
c1, c2, c3 = st.columns(3)
with c1, st.container(border=True):
    st.subheader("Excel workbook")
    st.caption("All aggregate tables, recommendations, source details and analytical caveats in one workbook.")
    st.download_button("⬇️ Excel workbook (all tables)", to_excel_bytes(tables, cards, meta),
                       file_name=f"content_detective_{stamp}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
with c2, st.container(border=True):
    st.subheader("Recommendation cards")
    st.caption("Evidence-backed experiments in CSV format. Available when this selection supports recommendations.")
    st.download_button("⬇️ Recommendations (CSV)", cards_frame(cards).to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"recommendations_{stamp}.csv", mime="text/csv", width="stretch",
                       disabled=not cards)
with c3, st.container(border=True):
    st.subheader("PDF report")
    st.caption("A readable report with summary charts, recommendation evidence and limitations for review.")
    st.download_button("⬇️ PDF report", pdf_report(tables, cards, meta), file_name=f"content_detective_report_{stamp}.pdf",
                       mime="application/pdf", width="stretch")

with st.container(border=True):
    section_header("Preview", "Inspect an aggregated table before downloading your report.")
    name = st.selectbox("Table", list(tables))
    # Pandas attrs may contain an unavailable Kruskal p-value (NaN), which is
    # invalid JSON in Arrow's frontend metadata. Keep the scientific source
    # tables and downloads intact; the preview needs only the table cells.
    preview = tables[name].copy()
    preview.attrs = {}
    st.dataframe(preview, hide_index=True, width="stretch")
