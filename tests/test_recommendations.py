"""Phase 12 tests: only significant findings make cards; every card is complete; the number lock works."""

import numpy as np
import pandas as pd
import pytest

from src.recommendations.engine import Card, build_cards, card_from_finding, collect_findings, Finding
from src.recommendations.llm_wording import number_lock_ok, rewrite_card


def _videos(effect: float = 1.0, seed: int = 3) -> pd.DataFrame:
    """SYNTHETIC: 'wedding_festive' videos get a planted lift in rel_er; everything else is noise."""
    rng = np.random.default_rng(seed)
    n = 400
    tags = [["wedding_festive"] if i % 4 == 0 else ["other"] for i in range(n)]
    rel = rng.lognormal(0, 0.3, n) * np.where([t == ["wedding_festive"] for t in tags], 1 + effect, 1.0)
    return pd.DataFrame({
        "rel_er": rel, "campaign_tags": tags, "duration_bucket": rng.choice(["0-15s", "16-30s"], n),
        "hashtag_count": rng.integers(0, 8, n), "title_has_emoji": rng.random(n) < 0.5,
        "hour_pkt": rng.integers(6, 24, n), "weekday_pkt": rng.choice(["Monday", "Tuesday", "Wednesday"], n),
    })


def test_planted_effect_produces_cards_with_all_fields():
    cards, _ = build_cards(_videos())
    assert cards[0].kind == "next_post" and "wedding/festive" in cards[0].what
    titles = [c.title for c in cards]
    assert "Try more: wedding/festive content" in titles
    for c in cards:
        for f in ("what", "where", "when", "why", "ab_test"):
            assert getattr(c, f).strip()
        assert c.n >= 20 and c.limitations


def test_no_effect_no_cards():
    findings = collect_findings(_videos(effect=0.0, seed=11))
    assert all(f.p_adj < 0.05 and f.n >= 20 for f in findings)
    assert not any(f.group == "wedding_festive" for f in findings)


def _card():
    f = Finding("campaign_tags", "wedding_festive", "wedding/festive content", "content", 238, 1.34, 1.08,
                1.21, 1.48, 0.16, "small", 0.001)
    return card_from_finding(f)


def test_card_states_effect_size_honestly():
    c = _card()
    assert "small effect" in c.why and c.strength == "modest"
    assert any("small or uncertain" in lim for lim in c.limitations)


def test_number_lock_accepts_only_card_numbers():
    c = _card()
    assert number_lock_ok("Wedding/festive videos showed 1.34 median engagement (n 238).", c)
    assert not number_lock_ok("Wedding/festive videos get 50% more engagement.", c)     # invented number
    assert not number_lock_ok("Median engagement was 1.4.", c)                         # re-rounded number


def test_rewrite_falls_back_without_key():
    text, used = rewrite_card(_card(), api_key="")
    assert not used and "1.34" in text


def test_negligible_effects_are_weak_signals_not_cards():
    def f(group, delta, effect, kind="content"):
        return Finding("campaign_tags", group, f"{group} content", kind, 100, 1.2, 1.0, 1.1, 1.3, delta, effect, 0.01)
    from src.recommendations import engine
    findings = [f("big", 0.30, "small"), f("tiny", 0.05, "negligible"),
                Finding("weekday_pkt", "Saturday", "posting on Saturday", "timing", 100, 0.9, 1.1, 0.8, 1.0,
                        -0.2, "small", 0.01)]
    original = engine.collect_findings
    engine.collect_findings = lambda videos: findings
    try:
        cards, weak = build_cards(pd.DataFrame())
    finally:
        engine.collect_findings = original
    titles = [c.title for c in cards]
    assert "Try more: big content" in titles and not any("tiny" in t for t in titles)
    assert [w.title for w in weak] == ["Try more: tiny content"]
    assert cards[0].kind == "next_post" and "except Saturday" in cards[0].when
