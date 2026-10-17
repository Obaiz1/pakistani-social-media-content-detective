"""Contract tests for the YouTube client against recorded-style SYNTHETIC responses (no live calls)."""

from datetime import datetime, timezone

import pytest
import requests

from src.ingestion.youtube import QuotaExceededError, YouTubeAPIError, YouTubeClient


class FakeResponse:
    def __init__(self, status: int, payload: dict):
        self.status_code = status
        self._payload = payload

    def json(self):
        return self._payload


class FakeSession:
    """Returns queued responses per endpoint and records every call."""

    def __init__(self, responses: dict[str, list[FakeResponse]]):
        self.responses = responses
        self.calls: list[tuple[str, dict]] = []

    def get(self, url, params, timeout):
        endpoint = url.rsplit("/", 1)[-1]
        self.calls.append((endpoint, dict(params)))
        return self.responses[endpoint].pop(0)


def ok(payload):
    return FakeResponse(200, payload)


def error(status, reason):
    return FakeResponse(status, {"error": {"errors": [{"reason": reason}]}})


def item(video_id, published):
    return {"contentDetails": {"videoId": video_id, "videoPublishedAt": published}}


CUTOFF = datetime(2025, 1, 1, tzinfo=timezone.utc)


def test_pages_through_entire_playlist_without_early_stop():
    # page 1 has an OLD video before a NEW one: an early-stop rule would lose v3 on page 2
    session = FakeSession({"playlistItems": [
        ok({"items": [item("v1", "2025-06-01T00:00:00Z"), item("old", "2023-01-01T00:00:00Z")],
            "nextPageToken": "p2"}),
        ok({"items": [item("v3", "2025-02-01T00:00:00Z")]}),
    ]})
    client = YouTubeClient("k", session=session)
    assert list(client.iter_upload_video_ids("UU1", CUTOFF)) == ["v1", "v3"]
    assert client.quota_used == 2
    assert session.calls[1][1]["pageToken"] == "p2"


def test_videos_are_batched_by_50():
    session = FakeSession({"videos": [ok({"items": [{"id": "a"}]}), ok({"items": [{"id": "b"}]})]})
    client = YouTubeClient("k", session=session)
    out = client.get_videos([f"v{i}" for i in range(51)])
    assert [v["id"] for v in out] == ["a", "b"]
    assert len(session.calls[0][1]["id"].split(",")) == 50
    assert len(session.calls[1][1]["id"].split(",")) == 1


def test_quota_exceeded_raises_clear_error():
    client = YouTubeClient("k", session=FakeSession({"videos": [error(403, "quotaExceeded")]}))
    with pytest.raises(QuotaExceededError):
        client.get_videos(["a"])


def test_transient_errors_are_retried_with_backoff():
    sleeps = []
    session = FakeSession({"videos": [error(503, "backendError"), ok({"items": [{"id": "a"}]})]})
    client = YouTubeClient("k", session=session, sleep=sleeps.append)
    assert client.get_videos(["a"]) == [{"id": "a"}]
    assert sleeps == [1]


class FlakySession(FakeSession):
    """Drops the connection N times before answering (the real Phase 7 run hit RemoteDisconnected)."""

    def __init__(self, failures: int, response: FakeResponse):
        super().__init__({})
        self.failures, self.response = failures, response

    def get(self, url, params, timeout):
        self.calls.append((url, dict(params)))
        if self.failures:
            self.failures -= 1
            raise requests.ConnectionError("Remote end closed connection without response")
        return self.response


def test_network_errors_are_retried():
    sleeps = []
    client = YouTubeClient("k", session=FlakySession(2, ok({"items": [{"id": "a"}]})), sleep=sleeps.append)
    assert client.get_videos(["a"]) == [{"id": "a"}]
    assert sleeps == [1, 2]


def test_persistent_network_errors_raise_api_error():
    client = YouTubeClient("k", session=FlakySession(99, ok({})), max_retries=2, sleep=lambda s: None)
    with pytest.raises(YouTubeAPIError, match="network error"):
        client.get_videos(["a"])


def test_other_errors_are_not_swallowed():
    client = YouTubeClient("k", session=FakeSession({"videos": [error(400, "badRequest")]}))
    with pytest.raises(YouTubeAPIError):
        client.get_videos(["a"])


def test_comments_drop_author_identity_and_hash_ids():
    thread = {"snippet": {"topLevelComment": {"id": "Ugx123", "snippet": {
        "textOriginal": "bohat acha", "likeCount": 3, "publishedAt": "2025-03-01T10:00:00Z",
        "authorDisplayName": "Real Person", "authorChannelId": {"value": "UCperson"}}}}}
    client = YouTubeClient("k", session=FakeSession({"commentThreads": [ok({"items": [thread]})]}))
    [c] = client.get_comments("vid")
    assert c["text"] == "bohat acha" and c["like_count"] == 3
    assert "Ugx123" not in c["comment_id_hash"] and len(c["comment_id_hash"]) == 16
    assert not any(k.startswith("author") for k in c)
    assert "Real Person" not in str(c)


def test_comments_disabled_returns_empty():
    client = YouTubeClient("k", session=FakeSession({"commentThreads": [error(403, "commentsDisabled")]}))
    assert client.get_comments("vid") == []


def test_requires_api_key():
    with pytest.raises(ValueError):
        YouTubeClient("")
