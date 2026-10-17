"""Optional: an LLM rewrites a card in plain language, with every number locked to the card's evidence.

If the rewrite contains any number that isn't in the card, it's rejected and the template text is used.
Human review is still required; nothing is ever posted automatically.
"""

import re

import requests

from src.recommendations.engine import Card

URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "nvidia/nemotron-3-super-120b-a12b"
_NUM = re.compile(r"[-+]?\d+(?:\.\d+)?")

PROMPT = ("Rewrite this social-media recommendation for a Pakistani clothing brand's marketing manager in 2–3 short, "
          "plain-English sentences. Keep it cautious (it is a correlation to test, not a guarantee). Use ONLY numbers "
          "that appear in the card; do not invent, round differently, or add numbers.\n\nCARD:\n{card}\n\nRewrite:")


def card_text(card: Card) -> str:
    return (f"Title: {card.title}\nWhat: {card.what}\nWhere: {card.where}\nWhen: {card.when}\nWhy: {card.why}\n"
            f"Evidence n: {card.n}\nStrength: {card.strength}\nA/B test: {card.ab_test}")


def numbers_in(text: str) -> set[float]:
    """Numeric VALUES in the text, so '06' == '6' and '+0.15' == '0.15' (sign kept for negatives)."""
    return {float(m) for m in _NUM.findall(text.replace("−", "-"))}


def number_lock_ok(rewrite: str, card: Card) -> bool:
    """Every number value in the rewrite must also appear in the card text (no invented or re-rounded numbers)."""
    allowed = numbers_in(card_text(card))
    allowed |= {abs(x) for x in allowed}          # "-7%" may be phrased as "7% lower"
    return numbers_in(rewrite) <= allowed


def rewrite_card(card: Card, api_key: str, timeout: int = 120) -> tuple[str, bool]:
    """Returns (text, used_llm). Falls back to the template on any error or number-lock failure."""
    template = f"{card.what} {card.when} {card.why}"
    if not api_key:
        return template, False
    try:
        r = requests.post(URL, timeout=timeout, headers={"Authorization": f"Bearer {api_key}"}, json={
            "model": MODEL, "temperature": 0.2, "max_tokens": 800,
            "messages": [{"role": "user", "content": PROMPT.format(card=card_text(card))}]})
        r.raise_for_status()
        text = (r.json()["choices"][0]["message"].get("content") or "").strip()
    except (requests.RequestException, KeyError, ValueError):
        return template, False
    if not text or not number_lock_ok(text, card):
        return template, False
    return text, True
