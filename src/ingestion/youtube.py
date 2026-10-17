"""YouTube Data API v3 client: full paging, batching, quota metering, retries.

Only public data is requested. Comment author identity is never returned by this module.
"""

import hashlib
import time
from collections.abc import Callable, Iterator
from datetime import datetime

import requests

BASE_URL = "https://www.googleapis.com/youtube/v3"
# Quota cost per call (https://developers.google.com/youtube/v3/determine_quota_cost)
QUOTA_COST = {"channels": 1, "playlistItems": 1, "videos": 1, "commentThreads": 1, "search": 100}
RETRY_STATUSES = {429, 500, 502, 503, 504}


class YouTubeAPIError(RuntimeError):
    pass


class QuotaExceededError(YouTubeAPIError):
    pass


def hash_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def parse_api_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class YouTubeClient:
    def __init__(self, api_key: str, session: requests.Session | None = None,
                 max_retries: int = 4, sleep: Callable[[float], None] = time.sleep):
        if not api_key:
            raise ValueError("YouTube API key is required")
        self._key = api_key
        self._session = session or requests.Session()
        self._max_retries = max_retries
        self._sleep = sleep
        self.quota_used = 0

    def _get(self, endpoint: str, **params) -> dict:
        params = {k: v for k, v in params.items() if v is not None}
        params["key"] = self._key
        for attempt in range(self._max_retries + 1):
            self.quota_used += QUOTA_COST[endpoint]
            try:
                resp = self._session.get(f"{BASE_URL}/{endpoint}", params=params, timeout=30)
            except (requests.ConnectionError, requests.Timeout) as exc:
                if attempt < self._max_retries:
                    self._sleep(2 ** attempt)
                    continue
                raise YouTubeAPIError(f"{endpoint} failed: network error after retries ({exc})") from exc
            if resp.status_code == 200:
                return resp.json()
            reason = _error_reason(resp)
            if resp.status_code == 403 and reason in {"quotaExceeded", "dailyLimitExceeded"}:
                raise QuotaExceededError(f"YouTube quota exhausted (used ~{self.quota_used} units this run)")
            if resp.status_code in RETRY_STATUSES and attempt < self._max_retries:
                self._sleep(2 ** attempt)
                continue
            raise YouTubeAPIError(f"{endpoint} failed: HTTP {resp.status_code} {reason}")
        raise YouTubeAPIError(f"{endpoint} failed after retries")  # pragma: no cover

    def get_channels(self, channel_ids: list[str]) -> list[dict]:
        items = []
        for batch in _chunks(channel_ids, 50):
            data = self._get("channels", part="snippet,statistics,contentDetails", id=",".join(batch))
            items += data.get("items", [])
        return items

    def iter_upload_video_ids(self, uploads_playlist_id: str, published_after: datetime) -> Iterator[str]:
        """Page through the *entire* uploads playlist and yield ids published after the cutoff.

        No early stop: playlist order isn't guaranteed to be strictly chronological
        (the Phase 2 audit lost videos with an early-stop rule).
        """
        token = None
        while True:
            data = self._get("playlistItems", part="contentDetails", playlistId=uploads_playlist_id,
                             maxResults=50, pageToken=token)
            for item in data.get("items", []):
                published = item["contentDetails"].get("videoPublishedAt")
                if published and parse_api_time(published) >= published_after:
                    yield item["contentDetails"]["videoId"]
            token = data.get("nextPageToken")
            if not token:
                return

    def get_videos(self, video_ids: list[str]) -> list[dict]:
        items = []
        for batch in _chunks(video_ids, 50):
            data = self._get("videos", part="snippet,statistics,contentDetails", id=",".join(batch))
            items += data.get("items", [])
        return items

    def get_comments(self, video_id: str, max_comments: int = 100) -> list[dict]:
        """Top-level comments by relevance, with author identity removed."""
        try:
            data = self._get("commentThreads", part="snippet", videoId=video_id,
                             maxResults=min(max_comments, 100), order="relevance", textFormat="plainText")
        except YouTubeAPIError as exc:
            if "commentsDisabled" in str(exc) or "HTTP 404" in str(exc):
                return []
            raise
        out = []
        for thread in data.get("items", [])[:max_comments]:
            c = thread["snippet"]["topLevelComment"]
            s = c["snippet"]
            out.append({
                "video_id": video_id,
                "comment_id_hash": hash_id(c["id"]),
                "published_at_utc": s.get("publishedAt"),
                "text": s.get("textOriginal") or s.get("textDisplay") or "",
                "like_count": s.get("likeCount"),
            })
        return out


def _error_reason(resp: requests.Response) -> str:
    try:
        errors = resp.json().get("error", {}).get("errors", [])
        return errors[0].get("reason", "") if errors else ""
    except ValueError:
        return ""


def _chunks(seq: list, size: int) -> Iterator[list]:
    for i in range(0, len(seq), size):
        yield seq[i:i + size]
