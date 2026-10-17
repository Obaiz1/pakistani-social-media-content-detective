"""Generate the SYNTHETIC demo dataset in data/synthetic_demo/.

Deterministic (fixed seed) so tests and screenshots are reproducible.
Brand names are fictional placeholders, so the data can't be mistaken for real brand metrics.
Usage: uv run python scripts/make_synthetic_fixture.py
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "data" / "synthetic_demo"
SEED = 42
SNAPSHOT = datetime(2026, 10, 17, tzinfo=timezone.utc)

BRANDS = [f"demo_brand_{c}" for c in "abcdefgh"]
CAMPAIGN_WORDS = ["Eid Collection", "Lawn 2025", "Winter Sale", "New Arrivals", "Wedding Edit", "Azadi Special", ""]
COMMENT_TEXTS = [
    ("Beautiful collection 😍", "english"),
    ("yaar suit bohat cute hai lekin price zyada hai", "roman_urdu"),
    ("bohat acha design hai", "roman_urdu"),
    ("Quality kharab thi, disappointed", "roman_urdu"),
    ("بہت خوبصورت", "urdu"),
    ("When is the sale?", "english"),
    ("❤️❤️❤️", "emoji"),
]


def build(seed: int = SEED) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    channels, videos, comments = [], [], []
    for b_idx, brand in enumerate(BRANDS):
        subs = int(rng.integers(15_000, 260_000))
        channels.append({"brand_id": brand, "channel_id": f"UCSYNTH{b_idx:017d}", "subscriber_count": subs,
                         "snapshot_date": SNAPSHOT.date().isoformat(), "provenance": "SYNTHETIC"})
        for v in range(int(rng.integers(30, 60))):
            published = SNAPSHOT - timedelta(days=int(rng.integers(1, 730)), minutes=int(rng.integers(0, 1440)))
            views = int(rng.lognormal(7.5, 1.4))
            likes = int(views * rng.uniform(0.002, 0.06)) if rng.random() > 0.03 else None  # ~3% hidden likes
            n_comments = int(rng.poisson(0.6))
            vid = f"synth{b_idx}{v:04d}"
            campaign = CAMPAIGN_WORDS[int(rng.integers(0, len(CAMPAIGN_WORDS)))]
            videos.append({
                "snapshot_date": SNAPSHOT.date().isoformat(), "brand_id": brand, "video_id": vid,
                "published_at_utc": published.isoformat(), "title": f"{campaign} #{brand} look {v}".strip(),
                "duration_s": int(rng.choice([12, 20, 28, 45, 58, 90, 150, 600])),
                "view_count": views, "like_count": likes, "comment_count": n_comments,
                "provenance": "SYNTHETIC",
            })
            for c in range(n_comments):
                text, lang = COMMENT_TEXTS[int(rng.integers(0, len(COMMENT_TEXTS)))]
                comments.append({
                    "video_id": vid, "comment_id_hash": f"h{vid}{c}",
                    "published_at_utc": (published + timedelta(hours=int(rng.integers(1, 200)))).isoformat(),
                    "text": text, "language_hint": lang, "like_count": int(rng.poisson(1)),
                    "provenance": "SYNTHETIC",
                })
    return {"channels": pd.DataFrame(channels), "videos": pd.DataFrame(videos).astype({"like_count": "Int64"}),
            "comments": pd.DataFrame(comments)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, df in build().items():
        df.to_csv(OUT / f"{name}.csv", index=False)
        print(f"{name}: {len(df)} rows -> {OUT / (name + '.csv')}")


if __name__ == "__main__":
    main()
