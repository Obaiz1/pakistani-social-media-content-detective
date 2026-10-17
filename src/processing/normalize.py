"""Turn raw API items into canonical tables. Missing metrics stay null, never zero."""

import pandas as pd

from src.ingestion.youtube import parse_api_time


def _int_or_none(value) -> int | None:
    return None if value is None else int(value)


def channels_frame(items: list[dict], brand_by_channel: dict[str, str], snapshot_date: str) -> pd.DataFrame:
    rows = [{
        "snapshot_date": snapshot_date,
        "brand_id": brand_by_channel[c["id"]],
        "channel_id": c["id"],
        "channel_title": c["snippet"]["title"],
        "subscriber_count": None if c["statistics"].get("hiddenSubscriberCount")
        else _int_or_none(c["statistics"].get("subscriberCount")),
        "video_count": _int_or_none(c["statistics"].get("videoCount")),
        "uploads_playlist_id": c["contentDetails"]["relatedPlaylists"]["uploads"],
        "provenance": "youtube_data_api_v3",
    } for c in items]
    return _typed(pd.DataFrame(rows), ["subscriber_count", "video_count"])


def videos_frame(items: list[dict], brand_by_channel: dict[str, str], snapshot_date: str) -> pd.DataFrame:
    rows = []
    for v in items:
        s, st, cd = v["snippet"], v.get("statistics", {}), v.get("contentDetails", {})
        rows.append({
            "snapshot_date": snapshot_date,
            "brand_id": brand_by_channel[s["channelId"]],
            "channel_id": s["channelId"],
            "video_id": v["id"],
            "published_at_utc": parse_api_time(s["publishedAt"]),
            "title": s.get("title", ""),
            "description": s.get("description", ""),
            "api_tags": "|".join(s.get("tags", [])),
            "duration_iso": cd.get("duration"),
            "view_count": _int_or_none(st.get("viewCount")),
            "like_count": _int_or_none(st.get("likeCount")),        # absent when likes are hidden
            "comment_count": _int_or_none(st.get("commentCount")),  # absent when comments are disabled
            "provenance": "youtube_data_api_v3",
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["published_at_utc"] = pd.to_datetime(df["published_at_utc"], utc=True)
    return _typed(df, ["view_count", "like_count", "comment_count"])


def comments_frame(rows: list[dict], snapshot_date: str) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=["video_id", "comment_id_hash", "published_at_utc", "text", "like_count"])
    df.insert(0, "snapshot_date", snapshot_date)
    df["published_at_utc"] = pd.to_datetime(df["published_at_utc"], utc=True)
    df["provenance"] = "youtube_data_api_v3"
    return _typed(df, ["like_count"])


def _typed(df: pd.DataFrame, int_cols: list[str]) -> pd.DataFrame:
    for col in int_cols:
        if col in df:
            df[col] = df[col].astype("Int64")
    return df
