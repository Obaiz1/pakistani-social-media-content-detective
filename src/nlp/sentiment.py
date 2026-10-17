"""Sentiment adapters with one interface: predict(texts) -> list of 'positive' | 'neutral' | 'negative'.

Heavy imports (torch/transformers/vader) happen lazily so the dashboard never needs them.
"""

import hashlib
import json
import re
import time
from pathlib import Path

import requests

LABELS = ("positive", "neutral", "negative")


def normalize_label(raw: str) -> str:
    """Map any model's label string to the 3 benchmark classes ('mixed' -> neutral, per ARCHITECTURE §6)."""
    s = str(raw).lower()
    if s in {"label_0", "0"}:
        return "negative"
    if s in {"label_1", "1"}:
        return "neutral"
    if s in {"label_2", "2"}:
        return "positive"
    if "pos" in s:
        return "positive"
    if "neg" in s:
        return "negative"
    return "neutral"


class VaderModel:
    name = "vader"

    def __init__(self, threshold: float = 0.05):
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        self._sia, self._t = SentimentIntensityAnalyzer(), threshold

    def predict(self, texts: list[str]) -> list[str]:
        out = []
        for t in texts:
            c = self._sia.polarity_scores(t or "")["compound"]
            out.append("positive" if c >= self._t else "negative" if c <= -self._t else "neutral")
        return out


class HFModel:
    def __init__(self, model_id: str, batch_size: int = 16):
        from transformers import pipeline

        self.name = model_id
        self._pipe = pipeline("text-classification", model=model_id, tokenizer=model_id, device=-1)
        self._bs = batch_size
        self.id2label = dict(self._pipe.model.config.id2label)

    def predict(self, texts: list[str]) -> list[str]:
        res = self._pipe([t or "" for t in texts], batch_size=self._bs, truncation=True, max_length=128)
        return [normalize_label(r["label"]) for r in res]


PROMPT = (
    "You label the sentiment of YouTube comments on Pakistani clothing-brand videos. Comments may be "
    "English, Urdu, Roman Urdu (Urdu in Latin letters) or emoji. Questions and information requests "
    "(price, location, song name) are neutral. Wanting to buy/own the product is positive. Praise plus a "
    "complaint together is neutral. Answer with exactly one word: positive, neutral, or negative.\n\n"
    "Comment: {text}\nLabel:"
)


class NvidiaLLM:
    """Zero-shot labels via the NVIDIA API Catalog (OpenAI-compatible). Responses are cached on disk."""

    URL = "https://integrate.api.nvidia.com/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "nvidia/nemotron-3-super-120b-a12b",
                 cache_path: Path | None = None, min_interval: float = 1.6):
        if not api_key:
            raise ValueError("NVIDIA_API_KEY required")
        self.name, self._key, self._interval = f"nvidia:{model}", api_key, min_interval
        self._model = model
        self._cache_path = cache_path
        self._cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path and cache_path.exists() else {}
        self._last = 0.0

    def _ask(self, text: str) -> str:
        key = hashlib.sha256(f"{self._model}|{PROMPT}|{text}".encode()).hexdigest()
        if key in self._cache:
            return self._cache[key]
        for attempt in range(6):
            wait = self._interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                r = requests.post(self.URL, timeout=120, headers={"Authorization": f"Bearer {self._key}"}, json={
                    "model": self._model, "temperature": 0, "max_tokens": 600,
                    "messages": [{"role": "user", "content": PROMPT.format(text=text)}]})
            except (requests.Timeout, requests.ConnectionError):
                time.sleep(2 ** attempt * 2)
                continue
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"].get("content") or ""
                break
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt * 2)
                continue
            raise RuntimeError(f"NVIDIA API HTTP {r.status_code}: {r.text[:200]}")
        else:
            raise RuntimeError("NVIDIA API: retries exhausted")
        words = re.findall(r"positive|neutral|negative|mixed", content.lower())
        label = normalize_label(words[-1]) if words else "neutral"
        self._cache[key] = label
        if self._cache_path:
            self._cache_path.write_text(json.dumps(self._cache), encoding="utf-8")
        return label

    def predict(self, texts: list[str]) -> list[str]:
        return [self._ask(t or "") for t in texts]
