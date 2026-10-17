"""Mixed-effects tests (SYNTHETIC): recovers a planted effect, controls a brand confound, annotates cards."""

import numpy as np
import pandas as pd

from src.analytics.regression import fit_models, readable_term
from src.recommendations.engine import Card, Finding, apply_adjusted_check, card_from_finding


def _videos(seed=0, tag_effect=0.0, confound=False):
    rng = np.random.default_rng(seed)
    n = 800
    brand = rng.choice(list("abcdefgh"), n)
    brand_level = {b: v for b, v in zip("abcdefgh", np.linspace(-1.0, 1.0, 8))}
    # confound: wedding videos come mostly from the strongest brand
    p_tag = np.where(brand == "h", 0.7, 0.05) if confound else np.full(n, 0.25)
    wedding = rng.random(n) < p_tag
    log_er = -4.5 + np.vectorize(brand_level.get)(brand) + tag_effect * wedding + rng.normal(0, 0.4, n)
    published = pd.Timestamp("2025-01-01", tz="UTC") + pd.to_timedelta(rng.integers(0, 365, n), unit="D")
    return pd.DataFrame({
        "brand_id": brand, "er_views": np.exp(log_er), "low_reliability": False, "likely_promoted": False,
        "published_at_pkt": published.tz_convert("Asia/Karachi"),
        "weekday_pkt": rng.choice(["Monday", "Tuesday", "Saturday"], n), "hour_pkt": rng.integers(6, 24, n),
        "duration_bucket": rng.choice(["0-15s", "16-30s", "31-60s"], n), "hashtag_count": rng.integers(0, 8, n),
        "title_has_emoji": rng.random(n) < 0.1,
        "campaign_tags": [["wedding_festive"] if w else ["other"] for w in wedding],
    })


def _row(res, term):
    return res["table"].set_index("term").loc[term]


def test_recovers_planted_effect():
    res = fit_models(_videos(tag_effect=np.log(1.5)))          # +50% planted
    r = _row(res, "tag_wedding_festive")
    assert r["significant"] and r["robust"]
    assert r["effect_ci_low"] < 50 < r["effect_ci_high"]


def test_brand_confound_is_controlled():
    # no true tag effect, but tagged videos come from the best brand -> raw difference is large, adjusted is not
    v = _videos(confound=True, tag_effect=0.0, seed=4)
    raw = np.log(v.loc[v["campaign_tags"].str[0] == "wedding_festive", "er_views"]).mean() - \
          np.log(v.loc[v["campaign_tags"].str[0] == "other", "er_views"]).mean()
    assert raw > 0.5
    assert not _row(fit_models(v), "tag_wedding_festive")["robust"]


def test_readable_terms():
    assert readable_term("tag_wedding_festive") == "Campaign: wedding/festive"
    assert readable_term("C(weekday, Treatment(reference='Monday'))[T.Saturday]") == "Weekday: Saturday (vs Monday)"


def test_cards_get_downgraded_when_not_confirmed():
    f = Finding("campaign_tags", "wedding_festive", "wedding/festive content", "content", 238, 1.34, 1.10,
                1.18, 1.47, 0.15, "small", 0.001)
    card = card_from_finding(f)
    table = pd.DataFrame([{"term": "tag_wedding_festive", "label": "Campaign: wedding/festive", "effect_pct": 12.0,
                           "effect_ci_low": -3.0, "effect_ci_high": 30.0, "p_adj": 0.39, "robust": False}])
    apply_adjusted_check([card], [f], table)
    assert "NOT confirmed" in card.adjusted and card.strength.startswith("tentative")
