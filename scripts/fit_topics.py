"""Add BERTopic title themes to a snapshot's videos (columns topic_id, topic_label) + topics.parquet.

Usage: uv run --group nlp python scripts/fit_topics.py [snapshot_dir]
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.config import DATA_DIR  # noqa: E402
from src.nlp.topics import add_topics  # noqa: E402


def main() -> None:
    snap = Path(sys.argv[1]) if len(sys.argv) > 1 else max(p for p in (DATA_DIR / "processed").iterdir() if p.is_dir())
    videos = pd.read_parquet(snap / "videos.parquet").drop(columns=["topic_id", "topic_label"], errors="ignore")
    videos, info = add_topics(videos)
    videos.to_parquet(snap / "videos.parquet", index=False)
    info.assign(keywords=info["keywords"].map(", ".join)).to_parquet(snap / "topics.parquet", index=False)
    print(snap, "|", len(info) - 1, "topics |", int((videos["topic_id"] == -1).sum()), "outliers")
    print(info[["topic", "count", "label"]].to_string(index=False))


if __name__ == "__main__":
    main()
