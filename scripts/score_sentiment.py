"""Add language + sentiment labels to a snapshot's comments using the benchmark-selected model.

Usage: uv run --group nlp python scripts/score_sentiment.py [snapshot_dir]
Writes <snapshot>/comments.parquet in place with columns: language, sentiment_label, sentiment_model.
Brands flagged exclude_from_sentiment in config/brands.yaml are left unlabeled.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.config import DATA_DIR, load_brands  # noqa: E402
from src.nlp.langid import detect_language  # noqa: E402
from src.nlp.sentiment import HFModel  # noqa: E402

SELECTED_MODEL = "cardiffnlp/twitter-xlm-roberta-base-sentiment"   # docs/NLP_BENCHMARK.md, ADR-017


def main() -> None:
    snap = Path(sys.argv[1]) if len(sys.argv) > 1 else max((DATA_DIR / "processed").iterdir())
    comments = pd.read_parquet(snap / "comments.parquet")
    videos = pd.read_parquet(snap / "videos.parquet", columns=["video_id", "brand_id"])
    excluded = {b.brand_id for b in load_brands() if b.exclude_from_sentiment}
    brand = comments["video_id"].map(videos.set_index("video_id")["brand_id"])
    keep = ~brand.isin(excluded)
    texts = comments["text"].fillna("").astype(str)
    comments["language"] = texts.map(detect_language)
    comments["sentiment_label"] = pd.NA
    comments.loc[keep, "sentiment_label"] = HFModel(SELECTED_MODEL).predict(texts[keep].tolist())
    comments["sentiment_model"] = SELECTED_MODEL
    comments.to_parquet(snap / "comments.parquet", index=False)
    print(snap, comments["sentiment_label"].value_counts(dropna=False).to_dict(),
          comments["language"].value_counts().to_dict())


if __name__ == "__main__":
    main()
