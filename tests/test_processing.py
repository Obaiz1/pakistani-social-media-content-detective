"""Feature, metric and validation tests with hand-computed expected values."""

import pandas as pd
import pytest

from src.config import load_brands, load_campaign_tags
from src.processing.features import (add_video_features, build_tag_matchers, campaign_tags, duration_bucket,
                                     extract_hashtags, parse_iso_duration, text_script)
from src.processing.metrics import add_metrics
from src.processing.normalize import videos_frame
from src.validation.schemas import validate_all

SNAPSHOT = pd.Timestamp("2026-10-17T00:00:00Z")


# ---------- config ----------

def test_brands_config_has_8_unique_pinned_channels():
    brands = load_brands()
    assert len(brands) == 8
    ids = [b.channel_id for b in brands]
    assert len(set(ids)) == 8 and all(i.startswith("UC") and len(i) == 24 for i in ids)
    assert "UC5xbg6lBACA3HBdN8idiQvQ" in ids          # official J., not the fan channel
    assert "UCGNI4IB-HTUHpIPAExE42Kg" not in ids      # "I Love Junaid Jamshed" fan channel
    assert [b.brand_id for b in brands if b.exclude_from_sentiment] == ["bonanza_satrangi"]


# ---------- features ----------

@pytest.mark.parametrize("iso,seconds", [("PT45S", 45), ("PT1M5S", 65), ("PT1H", 3600), ("P1DT1S", 86401),
                                         ("PT0S", 0), (None, None), ("garbage", None)])
def test_parse_iso_duration(iso, seconds):
    assert parse_iso_duration(iso) == seconds


@pytest.mark.parametrize("seconds,bucket", [(15, "0-15s"), (16, "16-30s"), (45, "31-60s"), (60, "31-60s"),
                                            (61, "61-180s"), (180, "61-180s"), (181, ">180s"), (None, None)])
def test_duration_bucket_edges(seconds, bucket):
    assert duration_bucket(seconds) == bucket


def test_hashtags_are_lowercased_unique_and_unicode():
    assert extract_hashtags("New #Eid drop #Lawn2025 #eid #عید") == ["eid", "lawn2025", "عید"]


@pytest.mark.parametrize("text,script", [("Eid Collection", "latin"), ("عید مبارک", "urdu_script"),
                                         ("Eid عید مبارک ho", "mixed"), ("🔥🔥", "none"), ("", "none")])
def test_text_script(text, script):
    assert text_script(text) == script


def test_campaign_tags_word_boundaries_and_urdu():
    m = build_tag_matchers(load_campaign_tags())
    assert campaign_tags("Eid Collection 2025 | Flat 50% OFF", m) == ["eid", "sale"]
    assert campaign_tags("عید کلیکشن", m) == ["eid"]
    assert campaign_tags("Unstitched Lawn for summer", m) == ["lawn_summer"]
    assert campaign_tags("Wholesale office wear", m) == ["other"]   # 'sale' inside 'wholesale' must not match
    assert campaign_tags("Women's fashion", m) == ["other"]         # 'men' inside "women" must not match


def test_pkt_conversion_weekday_hour_and_age():
    videos = pd.DataFrame({"published_at_utc": pd.to_datetime(["2024-11-01T19:30:00Z"], utc=True),
                           "title": ["#Eid look"], "description": [""], "duration_iso": ["PT45S"]})
    out = add_video_features(videos, SNAPSHOT, load_campaign_tags())
    row = out.iloc[0]
    # 19:30 UTC Fri + 5h (PKT, no DST) = 00:30 Sat
    assert row["weekday_pkt"] == "Saturday" and row["hour_pkt"] == 0
    assert row["published_at_pkt"].strftime("%Y-%m-%d %H:%M") == "2024-11-02 00:30"
    assert row["age_days"] == 714          # 2024-11-01 19:30 -> 2026-10-17 00:00 = 714 full days
    assert row["duration_bucket"] == "31-60s" and row["hashtags"] == ["eid"]
    assert row["campaign_tags"] == ["eid"]


# ---------- metrics ----------

def _metric_fixture():
    videos = pd.DataFrame({
        "brand_id": ["a"] * 5 + ["b"],
        "video_id": ["a1", "a2", "a3", "a4", "a5", "b1"],
        "view_count": pd.array([1000, 2000, 4000, 100000, 50, 1000], dtype="Int64"),
        "like_count": pd.array([20, 30, 40, 50, 5, None], dtype="Int64"),   # b1: hidden likes
        "comment_count": pd.array([10, 10, 20, 50, 0, 5], dtype="Int64"),
        "age_days": [30, 30, 30, 30, 30, 30],
    })
    channels = pd.DataFrame({"brand_id": ["a", "b"], "subscriber_count": pd.array([10000, None], dtype="Int64")})
    return add_metrics(videos, channels).set_index("video_id")


def test_engagement_rates_hand_computed():
    m = _metric_fixture()
    assert m.loc["a1", "er_views"] == pytest.approx(30 / 1000, abs=1e-12)
    assert m.loc["a2", "like_rate"] == pytest.approx(30 / 2000, abs=1e-12)
    assert m.loc["a3", "comment_rate"] == pytest.approx(20 / 4000, abs=1e-12)
    assert m.loc["a1", "views_per_sub"] == pytest.approx(0.1, abs=1e-12)


def test_hidden_likes_and_missing_subs_give_null_not_zero():
    m = _metric_fixture()
    assert pd.isna(m.loc["b1", "er_views"]) and pd.isna(m.loc["b1", "like_rate"])
    assert pd.isna(m.loc["b1", "views_per_sub"])
    assert m.loc["b1", "comment_rate"] == pytest.approx(0.005)


def test_low_reliability_rel_er_and_promoted_flag():
    m = _metric_fixture()
    assert bool(m.loc["a5", "low_reliability"]) and not bool(m.loc["a1", "low_reliability"])
    # reliable brand-a ERs: 0.03, 0.02, 0.015, 0.001 -> median = (0.02 + 0.015) / 2 = 0.0175
    assert m.loc["a1", "rel_er"] == pytest.approx(0.03 / 0.0175, abs=1e-12)
    # brand-a like-rate median of (0.02, 0.015, 0.01, 0.0005) = 0.0125 -> threshold 0.0025;
    # views P75 of (1000, 2000, 4000, 100000) = 28000 -> a4 (0.0005, 100k views) is flagged, a3 is not
    assert bool(m.loc["a4", "likely_promoted"]) and not bool(m.loc["a3", "likely_promoted"])
    assert not bool(m.loc["b1", "likely_promoted"])


# ---------- normalization + validation ----------

def _api_video(vid, stats):
    return {"id": vid, "snippet": {"channelId": "UCosHRi7jeBb0JGZfFlOHYUA", "publishedAt": "2025-05-01T10:00:00Z",
                                   "title": "t", "description": ""},
            "statistics": stats, "contentDetails": {"duration": "PT30S"}}


def test_normalize_keeps_missing_stats_null():
    df = videos_frame([_api_video("v1", {"viewCount": "10"})], {"UCosHRi7jeBb0JGZfFlOHYUA": "khaadi"}, "2026-10-17")
    assert df.loc[0, "view_count"] == 10
    assert pd.isna(df.loc[0, "like_count"]) and pd.isna(df.loc[0, "comment_count"])


def _valid_tables():
    videos = videos_frame([_api_video("v1", {"viewCount": "10", "likeCount": "1", "commentCount": "0"})],
                          {"UCosHRi7jeBb0JGZfFlOHYUA": "khaadi"}, "2026-10-17")
    comments = pd.DataFrame({"snapshot_date": ["2026-10-17"], "video_id": ["v1"], "comment_id_hash": ["abc"],
                             "text": ["nice"], "like_count": pd.array([0], dtype="Int64")})
    channels = pd.DataFrame({"brand_id": ["khaadi"], "channel_id": ["UCosHRi7jeBb0JGZfFlOHYUA"],
                             "subscriber_count": pd.array([1], dtype="Int64")})
    return videos, comments, channels


def test_validation_accepts_clean_tables():
    validate_all(*_valid_tables())


def test_validation_rejects_negative_counts_and_duplicates():
    videos, comments, channels = _valid_tables()
    bad = pd.concat([videos, videos], ignore_index=True)
    bad.loc[0, "view_count"] = -5
    with pytest.raises(Exception):
        validate_all(bad, comments, channels)


def test_validation_rejects_author_fields():
    videos, comments, channels = _valid_tables()
    comments["authorDisplayName"] = ["Real Person"]
    with pytest.raises(ValueError, match="author"):
        validate_all(videos, comments, channels)
