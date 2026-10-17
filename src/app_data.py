"""Choose the dataset the dashboard shows, in priority order:

1. a local snapshot in data/processed/ that is < 30 days old (YouTube API policy),
2. a live collection via the API key (Streamlit secrets / .env), cached 24 h,
3. the SYNTHETIC fixture (clearly bannered).
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone

import pandas as pd
import streamlit as st

from src.config import DATA_DIR, get_secret, load_brands, load_campaign_tags
from src.data_sources import Dataset, load_synthetic_fixture
from src.pipeline import process

MAX_SNAPSHOT_AGE_DAYS = 30
SYNTHETIC_SNAPSHOT = pd.Timestamp("2026-10-17T00:00:00Z")


@dataclass(frozen=True)
class Loaded:
    data: Dataset
    source: str           # "snapshot" | "live" | "synthetic"
    snapshot_date: str
    note: str = ""


def latest_snapshot_dir(today: date | None = None):
    today = today or datetime.now(timezone.utc).date()
    root = DATA_DIR / "processed"
    if not root.exists():
        return None, None
    dated = sorted((d for d in root.iterdir() if d.is_dir() and (d / "videos.parquet").exists()), reverse=True)
    for d in dated:
        try:
            age = (today - date.fromisoformat(d.name)).days
        except ValueError:
            continue
        return (d, None) if age < MAX_SNAPSHOT_AGE_DAYS else (None, d.name)
    return None, None


def read_snapshot(path) -> Dataset:
    return Dataset(channels=pd.read_parquet(path / "channels.parquet"),
                   videos=pd.read_parquet(path / "videos.parquet"),
                   comments=pd.read_parquet(path / "comments.parquet"))


def synthetic_dataset() -> Dataset:
    raw = load_synthetic_fixture()
    v = raw.videos.copy()
    v["published_at_utc"] = pd.to_datetime(v["published_at_utc"], utc=True)
    v["description"] = ""
    v["duration_iso"] = "PT" + v["duration_s"].astype(str) + "S"
    for col in ("view_count", "like_count", "comment_count"):
        v[col] = v[col].astype("Int64")
    channels = raw.channels.assign(subscriber_count=raw.channels["subscriber_count"].astype("Int64"))
    comments = raw.comments.copy()
    # deterministic SYNTHETIC sentiment so the Sentiment page can be exercised without NLP models
    comments["sentiment_label"] = [("positive", "positive", "neutral", "negative")[i % 4] for i in range(len(comments))]
    comments["sentiment_model"] = "SYNTHETIC"
    return process(Dataset(channels=channels, videos=v.drop(columns=["duration_s"]), comments=comments),
                   SYNTHETIC_SNAPSHOT, load_campaign_tags())


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def _live_collect(_key_fingerprint: str) -> Dataset:
    from src.ingestion.youtube import YouTubeClient
    from src.pipeline import collect

    return collect(YouTubeClient(get_secret("YOUTUBE_API_KEY")), load_brands(), load_campaign_tags(), log=lambda m: None)


@st.cache_resource(show_spinner=False)
def _synthetic_cached() -> Dataset:
    return synthetic_dataset()


def fetch_remote_snapshot(repo: str, token: str, get=None) -> tuple[Dataset, dict]:
    """Read the latest snapshot from the PRIVATE data repo (written weekly by .github/workflows/refresh-data.yml)."""
    import io
    import json

    import requests

    get = get or requests.get
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.raw+json",
               "X-GitHub-Api-Version": "2022-11-28"}

    def raw(name: str) -> bytes:
        r = get(f"https://api.github.com/repos/{repo}/contents/{name}?ref=main", headers=headers, timeout=60)
        r.raise_for_status()
        return r.content

    manifest = json.loads(raw("manifest.json"))
    tables = {n: pd.read_parquet(io.BytesIO(raw(f"{n}.parquet"))) for n in ("channels", "videos", "comments")}
    return Dataset(**tables), manifest


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def _remote_cached(repo: str, _token: str) -> tuple[Dataset, dict]:
    return fetch_remote_snapshot(repo, _token)


def load_dashboard_data() -> Loaded:
    path, stale = latest_snapshot_dir()
    if path is not None:
        return Loaded(read_snapshot(path), "snapshot", path.name)
    note = f"Local snapshot {stale} is older than {MAX_SNAPSHOT_AGE_DAYS} days and was ignored. " if stale else ""
    repo, token = get_secret("DATA_REPO"), get_secret("DATA_REPO_TOKEN")
    if repo and token:
        try:
            data, manifest = _remote_cached(repo, token)
            age = (datetime.now(timezone.utc).date() - date.fromisoformat(manifest["snapshot_date"])).days
            if age < MAX_SNAPSHOT_AGE_DAYS:
                return Loaded(data, "remote", manifest["snapshot_date"], note)
            note += f"Published snapshot {manifest['snapshot_date']} is {age} days old and was ignored. "
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            hint = {401: "token invalid or expired", 403: "token lacks Contents: read",
                    404: "token can't see the data repo (wrong/old token or repo not selected)"}.get(status, "")
            note += (f"Could not read the published snapshot ({type(exc).__name__}"
                     f"{f' {status}: {hint}' if status else ''}). ")
    key = get_secret("YOUTUBE_API_KEY")
    if key:
        try:
            with st.spinner("Collecting live YouTube data (first load takes a few minutes, then cached for 24 h)…"):
                data = _live_collect(key[-6:])
            return Loaded(data, "live", data.videos["snapshot_date"].iloc[0], note)
        except Exception as exc:  # quota/network: degrade to synthetic, but say so
            note += f"Live collection failed ({type(exc).__name__}: {exc}). "
    return Loaded(_synthetic_cached(), "synthetic", SYNTHETIC_SNAPSHOT.date().isoformat(), note)
