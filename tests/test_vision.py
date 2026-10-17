"""Thumbnail feature tests (SYNTHETIC images and fake API responses; no network)."""

import io

import pandas as pd
from PIL import Image

from src.app_data import merge_thumbnails
from src.vision.thumbnails import VisionLabeler, color_features, parse_vlm_json


def _jpeg(color) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 36), color).save(buf, format="JPEG")
    return buf.getvalue()


def test_color_features_grey_vs_vivid():
    grey, red = color_features(_jpeg((128, 128, 128))), color_features(_jpeg((230, 20, 20)))
    assert grey["saturation"] < 0.05 < red["saturation"]
    assert grey["colorfulness"] < red["colorfulness"]
    assert 0.45 < grey["brightness"] < 0.55


def test_parse_vlm_json_takes_last_valid_block_and_coerces():
    text = 'thinking {"draft": 1} ... {"person": true, "face_visible": "false", "text_overlay": false, ' \
           '"product_closeup": true, "setting": "Studio"}'
    assert parse_vlm_json(text) == {"person": True, "face_visible": False, "text_overlay": False,
                                    "product_closeup": True, "setting": "studio"}
    assert parse_vlm_json("no json here") is None


class _Resp:
    def __init__(self, status, content=None):
        self.status_code, self._content = status, content

    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}


def test_labeler_caches_success_but_not_failure(tmp_path):
    good = '{"person": true, "face_visible": true, "text_overlay": false, "product_closeup": false, "setting": "indoor"}'
    calls = []

    def post(url, timeout, headers, json):
        calls.append(json["messages"][0]["content"])
        return _Resp(200, good) if len(calls) > 1 else _Resp(400)   # first call fails hard

    lab = VisionLabeler("k", tmp_path / "c.json", min_interval=0, post=post)
    assert lab.label("v1", _jpeg((0, 0, 0))) is None            # failure -> not cached
    assert lab.label("v1", _jpeg((0, 0, 0)))["person"] is True  # retried on the next call
    assert lab.label("v1", _jpeg((0, 0, 0)))["person"] is True and len(calls) == 2   # now served from cache
    assert calls[0] == "/no_think"                              # reasoning disabled for speed
    lab.save()
    assert VisionLabeler("k", tmp_path / "c.json").cache["v1"]["setting"] == "indoor"


def test_merge_thumbnails_prefixes_and_keeps_rows():
    videos = pd.DataFrame({"video_id": ["a", "b"], "x": [1, 2]})
    thumbs = pd.DataFrame({"video_id": ["a"], "person": [True], "colorfulness": [30.0]})
    out = merge_thumbnails(videos, thumbs)
    assert list(out["video_id"]) == ["a", "b"] and bool(out.loc[0, "thumb_person"]) is True
    assert pd.isna(out.loc[1, "thumb_colorfulness"])
    assert merge_thumbnails(videos, None) is videos
