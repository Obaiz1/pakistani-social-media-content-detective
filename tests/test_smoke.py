"""Smoke tests: fixture integrity, data-source selection, and every dashboard page rendering."""

from datetime import date

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import src.app_data as app_data
from scripts.make_synthetic_fixture import build
from src.app_data import Loaded, synthetic_dataset
from src.data_sources import load_synthetic_fixture

PAGES = ["overview", "brands", "content", "sentiment", "method"]


def test_fixture_is_fully_labeled_synthetic():
    data = load_synthetic_fixture()
    for df in (data.channels, data.videos, data.comments):
        assert len(df) > 0
        assert (df["provenance"] == "SYNTHETIC").all()


def test_fixture_matches_generator_deterministically():
    regenerated = build()["videos"]
    on_disk = load_synthetic_fixture().videos
    assert regenerated["video_id"].tolist() == on_disk["video_id"].tolist()


def test_hidden_likes_stay_null_not_zero():
    videos = synthetic_dataset().videos
    hidden = videos["like_count"].isna()
    assert hidden.any()
    assert videos.loc[hidden, "er_views"].isna().all()


def test_video_ids_unique_and_comments_reference_videos():
    data = load_synthetic_fixture()
    assert data.videos["video_id"].is_unique
    assert set(data.comments["video_id"]) <= set(data.videos["video_id"])


def test_stale_snapshot_is_ignored(tmp_path, monkeypatch):
    for name in ("2026-08-01", "2026-10-10"):
        (tmp_path / "processed" / name).mkdir(parents=True)
        (tmp_path / "processed" / name / "videos.parquet").write_bytes(b"")
    monkeypatch.setattr(app_data, "DATA_DIR", tmp_path)
    path, stale = app_data.latest_snapshot_dir(today=date(2026, 10, 17))
    assert path.name == "2026-10-10" and stale is None
    path, stale = app_data.latest_snapshot_dir(today=date(2026, 11, 30))   # 51 days old
    assert path is None and stale == "2026-10-10"


def test_falls_back_to_synthetic_without_snapshot_or_key(monkeypatch):
    monkeypatch.setattr(app_data, "latest_snapshot_dir", lambda: (None, None))
    monkeypatch.setattr(app_data, "get_secret", lambda name: None)
    loaded = app_data.load_dashboard_data()
    assert loaded.source == "synthetic"
    assert (loaded.data.videos["provenance"] == "SYNTHETIC").all()


@pytest.fixture(scope="module")
def synthetic_loaded():
    return Loaded(synthetic_dataset(), "synthetic", "2026-10-17")


@pytest.mark.parametrize("page", PAGES)
def test_every_page_renders_on_synthetic_data_with_banner(page, synthetic_loaded):
    at = AppTest.from_file(f"../views/{page}.py", default_timeout=60)
    at.session_state["loaded"] = synthetic_loaded
    at.run()
    assert not at.exception, at.exception
    assert any("SYNTHETIC" in w.value for w in at.warning)


def test_app_entry_navigates_to_overview(synthetic_loaded):
    at = AppTest.from_file("../app.py", default_timeout=60)
    at.session_state["loaded"] = synthetic_loaded
    at.run()
    assert not at.exception, at.exception
    assert at.title[0].value.startswith("Pakistani Social Media Content Detective")
    assert len(at.metric) == 4


def test_filters_never_include_low_reliability(synthetic_loaded):
    at = AppTest.from_file("../views/brands.py", default_timeout=60)
    at.session_state["loaded"] = synthetic_loaded
    at.run()
    assert not at.exception
    assert any("Always excluded" in c.value for c in at.sidebar.caption)
