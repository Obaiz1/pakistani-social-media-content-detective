import streamlit as st

from src.config import get_secret
from src.recommendations.engine import build_cards
from src.recommendations.llm_wording import rewrite_card
from src.ui import get_data, sidebar_filters, source_banner

loaded = get_data()
st.title("What to post next")
st.caption("Evidence cards built **only** from statistically supported findings (n ≥ 20, Benjamini-Hochberg "
           "adjusted p < 0.05). Each one is a hypothesis to A/B test, not a guarantee. Use the sidebar to focus on "
           "one brand; fewer videos means fewer supported findings.")
source_banner(loaded)
videos = sidebar_filters(loaded.data.videos)
if videos.empty:
    st.info("No videos match the current filters.")
    st.stop()

cards = build_cards(videos)
if not cards:
    st.info("No statistically supported findings for this selection, so there's no recommendation. That's an honest "
            "answer: try a wider selection (more brands or dates).")
    st.stop()

nvidia_key = get_secret("NVIDIA_API_KEY")
use_llm = st.toggle("Plain-language rewrite with NVIDIA Nemotron (numbers locked to the evidence)", value=False,
                    disabled=not nvidia_key, help="Sends only the card text (no personal data) to the NVIDIA API. "
                    "If the rewrite changes or adds any number, the template text is shown instead.")
if "rewrites" not in st.session_state:
    st.session_state["rewrites"] = {}

ICON = {"next_post": "🎯", "do_more": "📈", "do_less": "📉"}
for i, card in enumerate(cards):
    with st.container(border=True):
        st.subheader(f"{ICON[card.kind]} {card.title}")
        st.caption(f"Evidence strength: **{card.strength}** · n = {card.n:,}")
        if use_llm:
            key = card.title + card.why
            if key not in st.session_state["rewrites"]:
                with st.spinner("Rewriting…"):
                    st.session_state["rewrites"][key] = rewrite_card(card, nvidia_key)
            text, used = st.session_state["rewrites"][key]
            st.markdown(text)
            st.caption("✍️ AI-worded (number-locked); review before use." if used
                       else "Template text shown (the AI rewrite failed the number-lock check or was unavailable).")
        c1, c2 = st.columns(2)
        c1.markdown(f"**What:** {card.what}\n\n**Where:** {card.where}\n\n**When:** {card.when}")
        c2.markdown(f"**Why:** {card.why}")
        with st.expander("A/B test & limitations"):
            st.markdown(f"**Test it:** {card.ab_test}")
            st.markdown("\n".join(f"- {lim}" for lim in card.limitations))

st.caption("Human review required: these cards never post anything automatically.")
