"""Thumbnail features: local colour statistics + vision-LLM labels (NVIDIA API Catalog).

Images are fetched from YouTube's public thumbnail CDN, analysed in memory and never stored; only the
derived features are saved. Vision labels are cached per video so reruns only label new videos.
"""

import base64
import io
import json
import re
import threading
import time
from pathlib import Path

import numpy as np
import requests
from PIL import Image

THUMB_URL = "https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
VLM_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
VLM_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
VLM_FIELDS = ("person", "face_visible", "text_overlay", "product_closeup")
SETTINGS = ("studio", "outdoor", "indoor", "graphic")
PROMPT = ('Look at this YouTube thumbnail from a Pakistani clothing brand. Answer ONLY with JSON: '
          '{"person": true/false, "face_visible": true/false, "text_overlay": true/false, '
          '"product_closeup": true/false, "setting": "studio"|"outdoor"|"indoor"|"graphic"}. '
          'text_overlay = large added text/graphics (not tiny logos). product_closeup = fabric/garment detail fills the frame.')


def fetch_thumbnail(video_id: str, get=requests.get) -> bytes | None:
    r = get(THUMB_URL.format(video_id=video_id), timeout=30)
    return r.content if r.status_code == 200 and r.content else None


def color_features(image_bytes: bytes) -> dict:
    """Brightness/saturation (HSV means, 0-1) and Hasler-Süsstrunk colorfulness."""
    im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    im.thumbnail((256, 256))
    rgb = np.asarray(im, dtype=float)
    hsv = np.asarray(im.convert("HSV"), dtype=float) / 255.0
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    rg, yb = r - g, 0.5 * (r + g) - b
    colorfulness = np.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2)
    return {"brightness": float(hsv[..., 2].mean()), "saturation": float(hsv[..., 1].mean()),
            "colorfulness": float(colorfulness)}


def parse_vlm_json(text: str) -> dict | None:
    """Take the LAST {...} block (reasoning models think first) and coerce to the expected schema."""
    blocks = re.findall(r"\{[^{}]*\}", text or "")
    for block in reversed(blocks):
        try:
            d = json.loads(block)
        except json.JSONDecodeError:
            continue
        if all(k in d for k in VLM_FIELDS):
            out = {k: bool(d[k]) if isinstance(d[k], bool) else str(d[k]).lower() == "true" for k in VLM_FIELDS}
            setting = str(d.get("setting", "")).lower()
            out["setting"] = setting if setting in SETTINGS else None
            return out
    return None


class VisionLabeler:
    """Thread-safe, rate-limited, cached client for the vision model."""

    def __init__(self, api_key: str, cache_path: Path, min_interval: float = 1.6, post=requests.post):
        self._key, self._interval, self._post = api_key, min_interval, post
        self._cache_path = cache_path
        self.cache: dict = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
        self._lock, self._last = threading.Lock(), 0.0

    def _wait_turn(self) -> None:
        with self._lock:
            wait = self._interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()

    def label(self, video_id: str, image_bytes: bytes) -> dict | None:
        if self.cache.get(video_id) is not None:
            return self.cache[video_id]
        b64 = base64.b64encode(image_bytes).decode()
        result = None
        for attempt in range(8):
            self._wait_turn()
            try:
                r = self._post(VLM_URL, timeout=180, headers={"Authorization": f"Bearer {self._key}"}, json={
                    "model": VLM_MODEL, "temperature": 0, "max_tokens": 600, "messages": [
                        {"role": "system", "content": "/no_think"},   # Nemotron: skip reasoning, answer directly
                        {"role": "user", "content": [
                        {"type": "text", "text": PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}]})
            except (requests.Timeout, requests.ConnectionError):
                time.sleep(2 ** attempt * 2)
                continue
            if r.status_code == 200:
                result = parse_vlm_json(r.json()["choices"][0]["message"].get("content") or "")
                break
            if r.status_code in (429, 500, 502, 503, 504):   # shared free endpoint is often saturated (503)
                time.sleep(min(60, 2 ** attempt * 3))
                continue
            break
        if result is not None:   # failures aren't cached, so a rerun retries them
            with self._lock:
                self.cache[video_id] = result
        return result

    def save(self) -> None:
        with self._lock:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._cache_path.write_text(json.dumps(self.cache), encoding="utf-8")
