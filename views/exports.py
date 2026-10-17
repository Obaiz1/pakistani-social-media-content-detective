from datetime import date

import streamlit as st

from src.recommendations.engine import build_cards
from src.reporting.export import cards_frame, pdf_report, summary_tables, to_excel_bytes
from src.ui import brand_label, get_data, sidebar_filters, source_banner

loaded = get_data()
st.title("Report & exports")
st.caption("Download what you see under the current sidebar filters: aggregated tables, recommendation cards and a "
           "PDF report. Video-level YouTube data and comment text are never exported.")
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

c1, c2, c3 = st.columns(3)
c1.download_button("⬇️ Excel workbook (all tables)", to_excel_bytes(tables, cards, meta),
                   file_name=f"content_detective_{stamp}.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
c2.download_button("⬇️ Recommendations (CSV)", cards_frame(cards).to_csv(index=False).encode("utf-8-sig"),
                   file_name=f"recommendations_{stamp}.csv", mime="text/csv", width="stretch",
                   disabled=not cards)
c3.download_button("⬇️ PDF report", pdf_report(tables, cards, meta), file_name=f"content_detective_report_{stamp}.pdf",
                   mime="application/pdf", width="stretch")

st.subheader("Preview")
name = st.selectbox("Table", list(tables))
st.dataframe(tables[name], hide_index=True, width="stretch")
