"""End-to-end collection: API -> canonical tables -> validation -> features -> metrics."""

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import pandas as pd

from src.config import Brand
from src.data_sources import Dataset
from src.ingestion.youtube import YouTubeClient
from src.processing.features import add_video_features
from src.processing.metrics import add_metrics
from src.processing.normalize import channels_frame, comments_frame, videos_frame
from src.validation.schemas import validate_all

WINDOW_DAYS = 730
MAX_COMMENTS_PER_VIDEO = 100


def collect(client: YouTubeClient, brands: list[Brand], tags: dict[str, list[str]],
            now: datetime | None = None, window_days: int = WINDOW_DAYS,
            log: Callable[[str], None] = print) -> Dataset:
    now = now or datetime.now(timezone.utc)
    snapshot_date = now.date().isoformat()
    cutoff = now - timedelta(days=window_days)
    brand_by_channel = {b.channel_id: b.brand_id for b in brands}

    channel_items = client.get_channels([b.channel_id for b in brands])
    missing = set(brand_by_channel) - {c["id"] for c in channel_items}
    if missing:
        raise RuntimeError(f"channels not returned by API (deleted/renamed?): {sorted(missing)}")
    channels = channels_frame(channel_items, brand_by_channel, snapshot_date)

    video_items = []
    for row in channels.itertuples():
        ids = list(dict.fromkeys(client.iter_upload_video_ids(row.uploads_playlist_id, cutoff)))
        items = client.get_videos(ids)
        log(f"{row.brand_id}: {len(items)} videos (quota so far {client.quota_used})")
        video_items += items
    videos = videos_frame(video_items, brand_by_channel, snapshot_date)
    videos = videos.drop_duplicates("video_id", keep="last")

    skip_sentiment = {b.brand_id for b in brands if b.exclude_from_sentiment}
    comment_rows = []
    targets = videos[(videos["comment_count"].fillna(0) > 0) & ~videos["brand_id"].isin(skip_sentiment)]
    for vid in targets["video_id"]:
        comment_rows += client.get_comments(vid, MAX_COMMENTS_PER_VIDEO)
    comments = comments_frame(comment_rows, snapshot_date).drop_duplicates("comment_id_hash")
    log(f"comments: {len(comments)} from {len(targets)} videos (quota so far {client.quota_used})")

    videos, comments, channels = validate_all(videos, comments, channels)
    return process(Dataset(channels=channels, videos=videos, comments=comments), pd.Timestamp(now), tags)


def process(data: Dataset, snapshot_utc: pd.Timestamp, tags: dict[str, list[str]]) -> Dataset:
    videos = add_video_features(data.videos, snapshot_utc, tags)
    videos = add_metrics(videos, data.channels)
    return Dataset(channels=data.channels, videos=videos, comments=data.comments)
