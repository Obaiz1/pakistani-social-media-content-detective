"""Prepare the latest snapshot for the PRIVATE data repo: same tables, but comment text removed.

Usage: uv run python scripts/publish_snapshot.py <out_dir> [snapshot_dir]
The deployed dashboard only needs comment-level sentiment/language labels, never the text.
"""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.config import DATA_DIR  # noqa: E402

DROP_COMMENT_COLUMNS = ["text"]


def publish(snapshot: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    for name in ("channels", "videos"):
        shutil.copy2(snapshot / f"{name}.parquet", out / f"{name}.parquet")
    for optional in ("topics", "thumbnails"):
        if (snapshot / f"{optional}.parquet").exists():
            shutil.copy2(snapshot / f"{optional}.parquet", out / f"{optional}.parquet")
    comments = pd.read_parquet(snapshot / "comments.parquet")
    comments.drop(columns=[c for c in DROP_COMMENT_COLUMNS if c in comments]).to_parquet(out / "comments.parquet", index=False)
    meta = {"snapshot_date": snapshot.name, "videos": int(len(pd.read_parquet(out / "videos.parquet"))),
            "comments": int(len(comments)), "comment_text_included": False,
            "has_thumbnails": (out / "thumbnails.parquet").exists()}
    (out / "manifest.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return meta


if __name__ == "__main__":
    out_dir = Path(sys.argv[1])
    snap = Path(sys.argv[2]) if len(sys.argv) > 2 else max(p for p in (DATA_DIR / "processed").iterdir() if p.is_dir())
    print(publish(snap, out_dir))
