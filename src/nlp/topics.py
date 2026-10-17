"""Data-driven themes from video titles with BERTopic (multilingual embeddings).

Complements the hand-written campaign keyword tags: here the themes come from the data itself.
Titles are cleaned of URLs, hashtag symbols and brand names (so topics describe content, not who posted it).
Deterministic: fixed UMAP random_state.
"""

import re

import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_URL = re.compile(r"https?://\S+")
_MULTISPACE = re.compile(r"\s+")

BRAND_WORDS = ["khaadi", "sapphire", "gul", "ahmed", "gulahmed", "junaid", "jamshed", "j.", "alkaram", "studio",
               "bonanza", "satrangi", "nishat", "linen", "limelight", "pakistan", "official", "shorts", "short"]

# generic words that appear in almost every title and say nothing about the theme
STOP_WORDS = set(ENGLISH_STOP_WORDS) | {"collection", "collections", "new", "wear", "edit", "shop", "online", "available",
                                        "stores", "outlets", "now", "live", "store", "piece", "pieces", "season"}


def clean_title(title: str) -> str:
    t = _URL.sub(" ", title or "").replace("#", " ").lower()
    for w in BRAND_WORDS:
        t = re.sub(rf"(?<!\w){re.escape(w)}(?!\w)", " ", t)
    t = re.sub(r"[|•·\-–—_:/]+", " ", t)
    return _MULTISPACE.sub(" ", t).strip()


def fit_topics(titles: list[str], min_topic_size: int = 25, nr_topics: int = 12, seed: int = 42):
    """Returns (topic_ids, topic_info DataFrame with columns topic, count, label, keywords)."""
    from bertopic import BERTopic
    from hdbscan import HDBSCAN
    from sentence_transformers import SentenceTransformer
    from sklearn.feature_extraction.text import CountVectorizer
    from umap import UMAP

    docs = [clean_title(t) or "untitled" for t in titles]
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = embedder.encode(docs, show_progress_bar=False, batch_size=64)
    model = BERTopic(
        umap_model=UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=seed),
        hdbscan_model=HDBSCAN(min_cluster_size=min_topic_size, metric="euclidean", prediction_data=True),
        vectorizer_model=CountVectorizer(stop_words=list(STOP_WORDS), ngram_range=(1, 1), min_df=3,
                                         token_pattern=r"(?u)\b[^\W\d_]{3,}\b"),
        calculate_probabilities=False, verbose=False)
    model.fit(docs, embeddings)
    model.reduce_topics(docs, nr_topics=nr_topics + 1)   # +1 for the outlier topic (-1)
    topics = model.topics_
    info = model.get_topic_info()[["Topic", "Count"]].rename(columns={"Topic": "topic", "Count": "count"})
    info["keywords"] = info["topic"].map(lambda k: [w for w, _ in (model.get_topic(k) or []) if w][:6])
    info["label"] = info.apply(lambda r: "Outliers (no clear theme)" if r["topic"] == -1
                               else " / ".join(r["keywords"][:3]), axis=1)
    return list(topics), info


def add_topics(videos: pd.DataFrame, min_topic_size: int = 25, nr_topics: int = 12) -> tuple[pd.DataFrame, pd.DataFrame]:
    topics, info = fit_topics(videos["title"].fillna("").tolist(), min_topic_size=min_topic_size, nr_topics=nr_topics)
    out = videos.copy()
    out["topic_id"] = topics
    out["topic_label"] = out["topic_id"].map(info.set_index("topic")["label"])
    return out, info
