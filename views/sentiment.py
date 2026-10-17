import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analytics.compare import MIN_N
from src.analytics.sentiment_agg import sentiment_by
from src.ui import MUTED, SERIES, brand_label, get_data, source_banner

TAG_LABELS = {"eid": "Eid", "ramadan": "Ramadan", "sale": "Sale / discount", "new_arrivals": "New arrivals",
              "lawn_summer": "Lawn / summer", "winter": "Winter", "wedding_festive": "Wedding / festive",
              "independence": "Independence (Azadi)", "kids": "Kids", "men": "Men", "other": "No campaign tag"}

loaded = get_data()
st.title("Audience sentiment")
st.caption("What tone do public comments take? Reported only at brand and campaign level: about 80% of "
           "videos have no comments, so per-video sentiment isn't meaningful.")
source_banner(loaded)

comments = loaded.data.comments
if "sentiment_label" not in comments or comments["sentiment_label"].isna().all():
    st.info("Sentiment labels aren't available for this dataset. Run "
            "`uv run --group nlp python scripts/score_sentiment.py` on a local snapshot.")
    st.stop()

videos = loaded.data.videos[["video_id", "brand_id", "campaign_tags"]]
c = comments.merge(videos, on="video_id", how="left").dropna(subset=["sentiment_label"])
model = c["sentiment_model"].iloc[0] if "sentiment_model" in c else "unknown"

k1, k2, k3, k4 = st.columns(4)
k1.metric("Comments labelled", f"{len(c):,}")
k2.metric("Positive", f"{(c['sentiment_label'] == 'positive').mean():.0%}")
k3.metric("Neutral", f"{(c['sentiment_label'] == 'neutral').mean():.0%}")
k4.metric("Negative", f"{(c['sentiment_label'] == 'negative').mean():.0%}")


def net_chart(summary: pd.DataFrame, title: str, label) -> go.Figure:
    s = summary.iloc[::-1]
    rows = [f"{label(g)}  (n={n:,})" for g, n in zip(s["group"], s["n"])]
    fig = go.Figure()
    for sufficient, color in ((True, SERIES), (False, MUTED)):
        part = s[s["sufficient"] == sufficient]
        if part.empty:
            continue
        fig.add_trace(go.Scatter(
            x=part["net"], y=[f"{label(g)}  (n={n:,})" for g, n in zip(part["group"], part["n"])],
            mode="markers", marker=dict(size=10, color=color),
            error_x=dict(type="data", symmetric=False, array=(part["net_high"] - part["net"]).fillna(0),
                         arrayminus=(part["net"] - part["net_low"]).fillna(0), thickness=2, width=0, color=color),
            hovertext=[f"<b>{label(r.group)}</b><br>net {r.net:+.2f}<br>positive {r.positive:.0%} · neutral "
                       f"{r.neutral:.0%} · negative {r.negative:.0%}<br>n = {r.n}" for r in part.itertuples()],
            hoverinfo="text", name=f"n < {MIN_N} (insufficient)", showlegend=not sufficient))
    fig.add_vline(x=0, line=dict(width=1, dash="dot", color=MUTED))
    fig.update_layout(title=title, height=max(260, 46 * len(s) + 110), margin=dict(l=10, r=10, t=50, b=40),
                      xaxis=dict(title="Net sentiment (share positive − share negative)", range=[-1, 1],
                                 zeroline=False),
                      yaxis=dict(showgrid=False, categoryorder="array", categoryarray=rows),
                      legend=dict(orientation="h", y=-0.2))
    return fig


def table(summary: pd.DataFrame, label) -> pd.DataFrame:
    return pd.DataFrame({
        "Group": summary["group"].map(label), "n": summary["n"],
        "Positive": summary["positive"].map("{:.0%}".format), "Neutral": summary["neutral"].map("{:.0%}".format),
        "Negative": summary["negative"].map("{:.0%}".format), "Net": summary["net"].map("{:+.2f}".format),
        "95% CI": [f"{a:+.2f} – {b:+.2f}" if pd.notna(a) else "insufficient n"
                   for a, b in zip(summary["net_low"], summary["net_high"])],
    })


for title, by, label in (("By brand", "brand_id", brand_label),
                         ("By campaign", "campaign_tags", lambda g: TAG_LABELS.get(g, g))):
    st.subheader(title)
    summary = sentiment_by(c, by)
    st.plotly_chart(net_chart(summary, f"Net comment sentiment {title.lower()} (95% CI)", label), width="stretch")
    with st.expander("Table view"):
        st.dataframe(table(summary, label), hide_index=True, width="stretch")

st.caption(f"Model: `{model}`, chosen by benchmark (see Data & Method). Bonanza Satrangi is excluded "
           "because comments are disabled on almost all its videos. Comment authors are never stored. "
           "Commenters are a self-selected minority of viewers, so this describes commenters, not all viewers.")
