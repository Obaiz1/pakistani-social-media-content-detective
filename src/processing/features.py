"""Derived features: Pakistan time, video age, duration buckets, hashtags, emoji, script, campaign tags."""

import re

import pandas as pd

PKT = "Asia/Karachi"
DURATION_BINS = [(15, "0-15s"), (30, "16-30s"), (60, "31-60s"), (180, "61-180s")]
LONG_BUCKET = ">180s"
DURATION_ORDER = [label for _, label in DURATION_BINS] + [LONG_BUCKET]

_ISO_DURATION = re.compile(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$")
_HASHTAG = re.compile(r"#(\w+)", re.UNICODE)
_URDU = re.compile(r"[؀-ۿ]")
_LATIN = re.compile(r"[A-Za-z]")
_EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]")


def parse_iso_duration(value: str | None) -> int | None:
    """ISO-8601 duration like 'PT1M5S' -> 65 seconds. None if missing/unparseable."""
    if not value:
        return None
    m = _ISO_DURATION.match(value)
    if not m:
        return None
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def duration_bucket(seconds: int | None) -> str | None:
    if seconds is None or pd.isna(seconds):
        return None
    for limit, label in DURATION_BINS:
        if seconds <= limit:
            return label
    return LONG_BUCKET


def extract_hashtags(text: str) -> list[str]:
    seen: dict[str, None] = {}
    for tag in _HASHTAG.findall(text or ""):
        seen.setdefault(tag.lower(), None)
    return list(seen)


def text_script(text: str) -> str:
    """'urdu_script', 'latin', 'mixed' or 'none'. Roman Urdu vs English is split later (Phase 9)."""
    urdu, latin = len(_URDU.findall(text or "")), len(_LATIN.findall(text or ""))
    if urdu == 0 and latin == 0:
        return "none"
    if urdu and latin:
        share = urdu / (urdu + latin)
        if 0.2 <= share <= 0.8:
            return "mixed"
        return "urdu_script" if share > 0.8 else "latin"
    return "urdu_script" if urdu else "latin"


def has_emoji(text: str) -> bool:
    return bool(_EMOJI.search(text or ""))


def build_tag_matchers(tags: dict[str, list[str]]) -> dict[str, re.Pattern]:
    matchers = {}
    for tag, words in tags.items():
        parts = []
        for w in words:
            escaped = re.escape(w.lower())
            if _URDU.search(w):  # Urdu script: substring match
                parts.append(escaped)
                continue
            # word boundaries only on sides that are word characters ("% off" must match "50% off")
            before = r"(?<!\w)" if w[0].isalnum() else ""
            after = r"(?!\w)" if w[-1].isalnum() else ""
            parts.append(f"{before}{escaped}{after}")
        matchers[tag] = re.compile("|".join(parts))
    return matchers


def campaign_tags(text: str, matchers: dict[str, re.Pattern]) -> list[str]:
    lowered = (text or "").lower()
    found = [tag for tag, rx in matchers.items() if rx.search(lowered)]
    return found or ["other"]


def add_video_features(videos: pd.DataFrame, snapshot_utc: pd.Timestamp,
                       tags: dict[str, list[str]]) -> pd.DataFrame:
    df = videos.copy()
    pkt = df["published_at_utc"].dt.tz_convert(PKT)
    df["published_at_pkt"] = pkt
    df["weekday_pkt"] = pkt.dt.day_name()
    df["hour_pkt"] = pkt.dt.hour
    df["age_days"] = (snapshot_utc - df["published_at_utc"]).dt.days
    df["duration_s"] = df["duration_iso"].map(parse_iso_duration).astype("Int64")
    df["duration_bucket"] = df["duration_s"].map(duration_bucket)
    text = df["title"].fillna("") + "\n" + df["description"].fillna("")
    df["hashtags"] = text.map(extract_hashtags)
    df["hashtag_count"] = df["hashtags"].map(len)
    df["title_script"] = df["title"].map(text_script)
    df["title_has_emoji"] = df["title"].map(has_emoji)
    matchers = build_tag_matchers(tags)
    df["campaign_tags"] = text.map(lambda t: campaign_tags(t, matchers))
    return df
