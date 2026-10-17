"""Pandera schemas for canonical tables. Validation fails loudly instead of silently fixing data."""

import pandera.pandas as pa

_count = pa.Column("Int64", pa.Check.ge(0), nullable=True)

VIDEOS = pa.DataFrameSchema(
    {
        "snapshot_date": pa.Column(str),
        "brand_id": pa.Column(str),
        "channel_id": pa.Column(str, pa.Check.str_startswith("UC")),
        "video_id": pa.Column(str, unique=True),
        "published_at_utc": pa.Column("datetime64[us, UTC]", coerce=True),
        "title": pa.Column(str, nullable=True),
        "view_count": _count,
        "like_count": _count,
        "comment_count": _count,
    },
    strict=False,
)

COMMENTS = pa.DataFrameSchema(
    {
        "snapshot_date": pa.Column(str),
        "video_id": pa.Column(str),
        "comment_id_hash": pa.Column(str, unique=True),
        "text": pa.Column(str, nullable=True),
        "like_count": _count,
    },
    strict=False,
)

CHANNELS = pa.DataFrameSchema(
    {
        "brand_id": pa.Column(str, unique=True),
        "channel_id": pa.Column(str, pa.Check.str_startswith("UC")),
        "subscriber_count": _count,
    },
    strict=False,
)

FORBIDDEN_COMMENT_COLUMNS = {"author", "authorDisplayName", "authorChannelId", "authorChannelUrl",
                             "authorProfileImageUrl"}


def validate_all(videos, comments, channels):
    leaked = FORBIDDEN_COMMENT_COLUMNS & set(comments.columns)
    if leaked:
        raise ValueError(f"comment author fields must never be stored: {sorted(leaked)}")
    return VIDEOS.validate(videos, lazy=True), COMMENTS.validate(comments, lazy=True), CHANNELS.validate(channels, lazy=True)
