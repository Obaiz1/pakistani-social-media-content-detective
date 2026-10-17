"""Compute thumbnail features for a snapshot -> <snapshot>/thumbnails.parquet.

Usage: uv run python scripts/analyze_thumbnails.py [snapshot_dir] [--no-vlm] [--limit N] [--vlm-sample N]
Colour features are computed for every video; vision labels for all videos, or for a seeded random sample
(--vlm-sample N, plus anything already cached) because the free vision endpoint is slow when saturated.
Vision labels are cached in data/cache/thumbnail_vlm.json (git-ignored), so reruns only label new videos.
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.config import DATA_DIR, get_secret  # noqa: E402
from src.vision.thumbnails import VisionLabeler, color_features, fetch_thumbnail  # noqa: E402

CACHE = DATA_DIR / "cache" / "thumbnail_vlm.json"


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    def opt(name):
        return int(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else None

    limit, vlm_sample = opt("--limit"), opt("--vlm-sample")
    args = [a for a in args if a not in {str(limit), str(vlm_sample)}]
    snap = Path(args[0]) if args else max(p for p in (DATA_DIR / "processed").iterdir() if p.is_dir())
    ids = pd.read_parquet(snap / "videos.parquet", columns=["video_id"])["video_id"].tolist()[:limit]
    use_vlm = "--no-vlm" not in sys.argv
    labeler = VisionLabeler(get_secret("NVIDIA_API_KEY"), CACHE) if use_vlm else None
    vlm_ids = set(ids)
    if labeler and vlm_sample:
        vlm_ids = set(pd.Series(ids).sample(min(vlm_sample, len(ids)), random_state=7)) | {
            k for k, v in labeler.cache.items() if v is not None}

    def work(vid: str) -> dict:
        img = fetch_thumbnail(vid)
        if img is None:
            return {"video_id": vid}
        row = {"video_id": vid, **color_features(img)}
        if labeler and vid in vlm_ids:
            labels = labeler.label(vid, img)
            if labels:
                row.update(labels)
        return row

    rows, done = [], 0
    with ThreadPoolExecutor(max_workers=2) as pool:
        for fut in as_completed([pool.submit(work, v) for v in ids]):
            rows.append(fut.result())
            done += 1
            if done % 10 == 0:
                if labeler:
                    labeler.save()
                    print(f"{done}/{len(ids)} | cached {sum(v is not None for v in labeler.cache.values())} "
                          f"| retries {labeler.retries} | {time.strftime('%H:%M:%S')}", flush=True)
    if labeler:
        labeler.save()
    out = pd.DataFrame(rows)
    out.to_parquet(snap / "thumbnails.parquet", index=False)
    labelled = out["person"].notna().sum() if "person" in out else 0
    print(f"saved {snap / 'thumbnails.parquet'} | {len(out)} thumbnails | vision-labelled {labelled}")


if __name__ == "__main__":
    main()
