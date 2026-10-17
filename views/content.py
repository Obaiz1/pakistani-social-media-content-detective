import pandas as pd
import streamlit as st

from src.analytics.compare import compare_groups
from src.processing.features import DURATION_ORDER
from src.ui import get_data, median_ci_chart, sidebar_filters, source_banner, summary_table

TAG_LABELS = {"eid": "Eid", "ramadan": "Ramadan", "sale": "Sale / discount", "new_arrivals": "New arrivals",
              "lawn_summer": "Lawn / summer", "winter": "Winter", "wedding_festive": "Wedding / festive",
              "independence": "Independence (Azadi)", "kids": "Kids", "men": "Men", "other": "No campaign tag"}

loaded = get_data()
st.title("Content")
st.caption("Which content features go with higher engagement **within** a brand? Metric: relative engagement "
           "= video's engagement rate ÷ its brand's median (1.0 = typical for that brand).")
source_banner(loaded)
videos = sidebar_filters(loaded.data.videos).copy()
if videos.empty:
    st.info("No videos match the current filters.")
    st.stop()


def section(title: str, by: str, label=lambda g: g, order=None, note: str = "") -> None:
    st.subheader(title)
    summary = compare_groups(videos, by, "rel_er", order=order)
    if summary.empty:
        st.info("No data for this view under the current filters.")
        return
    st.plotly_chart(median_ci_chart(summary, f"Relative engagement by {title.lower()} (median, 95% CI)",
                                    "Relative engagement (1.0 = brand median)", pct=False, label=label,
                                    reference=1.0), width="stretch")
    with st.expander("Table view & statistics"):
        st.dataframe(summary_table(summary, label=label, pct=False), hide_index=True, width="stretch")
        st.caption(f"Kruskal-Wallis p = {summary.attrs['kruskal_p']:.3g}. {note}")


section("Video length", "duration_bucket", order=DURATION_ORDER,
        note="Length is a proxy for format: the API has no Shorts flag.")
section("Campaign", "campaign_tags", label=lambda g: TAG_LABELS.get(g, g),
        note="Tags come from keywords in the title/description; a video can carry several tags.")

if "topic_label" in videos and videos["topic_label"].notna().any():
    topic_videos = videos[videos["topic_id"] != -1]
    st.subheader("Data-driven themes (BERTopic)")
    st.caption("Themes discovered from the titles themselves (multilingual embeddings + clustering), instead of our "
               "keyword list. Videos that fit no theme (outliers) are left out.")
    summary = compare_groups(topic_videos, "topic_label", "rel_er")
    if not summary.empty:
        st.plotly_chart(median_ci_chart(summary, "Relative engagement by title theme (median, 95% CI)",
                                        "Relative engagement (1.0 = brand median)", pct=False, reference=1.0),
                        width="stretch")
        with st.expander("Table view & statistics"):
            st.dataframe(summary_table(summary, pct=False), hide_index=True, width="stretch")
            st.caption(f"Kruskal-Wallis p = {summary.attrs['kruskal_p']:.3g}. "
                       f"{int((videos['topic_id'] == -1).sum())} videos had no clear theme.")

if "thumb_person" in videos and videos["thumb_person"].notna().sum() >= 100:
    st.subheader("Thumbnails")
    st.caption("Vision-LLM labels (NVIDIA Nemotron, spot-checked against manual labels; see Data & Method) and colour "
               "statistics computed from the public thumbnail. Images are analysed in memory and never stored.")
    tv = videos[videos["thumb_person"].notna()].copy()
    yes_no = lambda col, yes, no: tv[col].map({True: yes, False: no})  # noqa: E731
    tv["t_face"] = yes_no("thumb_face_visible", "Face visible", "No face visible")
    tv["t_text"] = yes_no("thumb_text_overlay", "Text overlay", "No text overlay")
    tv["t_close"] = yes_no("thumb_product_closeup", "Product close-up", "Not a close-up")
    tv["t_color"] = pd.qcut(tv["thumb_colorfulness"], 3, labels=["Muted colours", "Medium colours", "Vivid colours"]).astype(str)
    for title, col in (("Face in thumbnail", "t_face"), ("Text overlay", "t_text"), ("Product close-up", "t_close"),
                       ("Colourfulness (tertiles)", "t_color")):
        summary = compare_groups(tv, col, "rel_er")
        if not summary.empty:
            st.plotly_chart(median_ci_chart(summary, f"Relative engagement: {title.lower()} (median, 95% CI)",
                                            "Relative engagement (1.0 = brand median)", pct=False, reference=1.0),
                            width="stretch")

videos["hashtag_band"] = pd.cut(videos["hashtag_count"], [-1, 0, 2, 5, 1_000],
                                labels=["0", "1–2", "3–5", "6+"]).astype(str)
section("Hashtag count", "hashtag_band", order=["0", "1–2", "3–5", "6+"])

videos["title_style"] = videos["title_script"].map(
    {"latin": "Latin script (English / Roman Urdu)", "urdu_script": "Urdu script", "mixed": "Mixed scripts",
     "none": "No letters (emoji/numbers)"})
section("Title script", "title_style")

videos["emoji_in_title"] = videos["title_has_emoji"].map({True: "Emoji in title", False: "No emoji"})
section("Emoji in title", "emoji_in_title")

st.caption("All comparisons are associational. A group being higher doesn't prove the feature *causes* "
           "engagement; brands that use a feature may differ in other ways too.")
