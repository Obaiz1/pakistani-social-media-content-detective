"""Phase 6 smoke tests: fixture integrity and that the app renders."""

import pandas as pd
from streamlit.testing.v1 import AppTest

from scripts.make_synthetic_fixture import build
from src.data_sources import load_synthetic_fixture


def test_fixture_is_fully_labeled_synthetic():
    data = load_synthetic_fixture()
    for df in (data.channels, data.videos, data.comments):
        assert len(df) > 0
        assert (df["provenance"] == "SYNTHETIC").all()


def test_fixture_matches_generator_deterministically():
    regenerated = build()["videos"]
    on_disk = load_synthetic_fixture().videos
    assert len(regenerated) == len(on_disk)
    assert regenerated["video_id"].tolist() == on_disk["video_id"].tolist()


def test_hidden_likes_stay_null_not_zero():
    videos = load_synthetic_fixture().videos
    assert videos["like_count"].isna().any(), "fixture should include hidden-like cases"
    assert not (videos["like_count"] == 0).all()


def test_video_ids_unique_and_comments_reference_videos():
    data = load_synthetic_fixture()
    assert data.videos["video_id"].is_unique
    assert set(data.comments["video_id"]) <= set(data.videos["video_id"])


def test_app_renders_with_synthetic_banner():
    at = AppTest.from_file("../app.py", default_timeout=60).run()
    assert not at.exception
    assert any("SYNTHETIC" in w.value for w in at.warning)
    assert len(at.metric) == 3
