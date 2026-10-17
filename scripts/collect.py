"""Collect a fresh YouTube snapshot for all configured brands.

Usage: uv run python scripts/collect.py
Writes data/processed/<YYYY-MM-DD>/{channels,videos,comments}.parquet (git-ignored).
Per the YouTube API Developer Policies, refresh or delete snapshots within 30 days.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DATA_DIR, get_secret, load_brands, load_campaign_tags  # noqa: E402
from src.ingestion.youtube import YouTubeClient  # noqa: E402
from src.pipeline import collect  # noqa: E402


def main() -> int:
    key = get_secret("YOUTUBE_API_KEY")
    if not key:
        print("YOUTUBE_API_KEY missing: add it to .env", file=sys.stderr)
        return 1
    client = YouTubeClient(key)
    data = collect(client, load_brands(), load_campaign_tags())
    snapshot = data.videos["snapshot_date"].iloc[0]
    out = DATA_DIR / "processed" / snapshot
    out.mkdir(parents=True, exist_ok=True)
    data.channels.to_parquet(out / "channels.parquet", index=False)
    data.videos.to_parquet(out / "videos.parquet", index=False)
    data.comments.to_parquet(out / "comments.parquet", index=False)
    print(f"saved to {out} | channels={len(data.channels)} videos={len(data.videos)} "
          f"comments={len(data.comments)} | quota used={client.quota_used}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
