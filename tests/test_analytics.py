"""Analytics tests: known answers, planted effects, the n >= 20 rule."""

import numpy as np
import pandas as pd
import pytest

from src.analytics.compare import benjamini_hochberg, bootstrap_median_ci, cliffs_delta, compare_groups


def test_cliffs_delta_extremes_and_zero():
    assert cliffs_delta(np.array([5, 6, 7]), np.array([1, 2, 3])) == pytest.approx(1.0)
    assert cliffs_delta(np.array([1, 2, 3]), np.array([5, 6, 7])) == pytest.approx(-1.0)
    assert cliffs_delta(np.array([1, 2, 3]), np.array([1, 2, 3])) == pytest.approx(0.0)


def test_benjamini_hochberg_hand_computed():
    # p = .01, .04, .03 (m=3): sorted .01,.03,.04 -> .03, .045, .04 -> monotone: .03, .04, .04
    adj = benjamini_hochberg(pd.Series([0.01, 0.04, 0.03, np.nan], index=list("abcd")))
    assert adj["a"] == pytest.approx(0.03) and adj["c"] == pytest.approx(0.04)
    assert adj["b"] == pytest.approx(0.04) and np.isnan(adj["d"])


def test_bootstrap_ci_brackets_the_median():
    vals = np.arange(1, 101, dtype=float)
    lo, hi = bootstrap_median_ci(vals)
    assert lo < 50.5 < hi and hi - lo < 25


def _planted(n_a=60, n_b=60, n_c=10, shift=1.0, seed=1):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "g": ["a"] * n_a + ["b"] * n_b + ["c"] * n_c,
        "m": np.r_[rng.normal(shift, 0.5, n_a), rng.normal(0, 0.5, n_b), rng.normal(0, 0.5, n_c)],
    })


def test_detects_planted_difference_and_flags_small_groups():
    out = compare_groups(_planted(), "g", "m").set_index("group")
    assert out.loc["a", "significant"] and out.loc["a", "cliffs_delta"] > 0.5
    assert out.loc["a", "effect"] == "large"
    assert not out.loc["c", "sufficient"] and np.isnan(out.loc["c", "p_value"])   # n=10 < 20: not tested
    assert np.isnan(out.loc["c", "ci_low"])
    assert out.attrs["kruskal_p"] < 0.001


def test_no_false_alarm_without_effect():
    out = compare_groups(_planted(shift=0.0, n_c=0, seed=7), "g", "m")
    assert not out["significant"].any()


def test_list_valued_groups_are_exploded():
    df = pd.DataFrame({"tags": [["eid", "sale"]] * 25 + [["other"]] * 25, "m": [1.0] * 25 + [0.0] * 25})
    out = compare_groups(df, "tags", "m").set_index("group")
    assert out.loc["eid", "n"] == 25 and out.loc["sale", "n"] == 25 and out.loc["other", "n"] == 25


def test_null_metric_rows_are_excluded_not_zeroed():
    df = pd.DataFrame({"g": ["a"] * 30, "m": [1.0] * 25 + [None] * 5})
    out = compare_groups(df, "g", "m")
    assert out.loc[0, "n"] == 25 and out.loc[0, "median"] == 1.0


def test_default_order_puts_insufficient_groups_last():
    df = _planted(n_c=5).assign(m=lambda d: d["m"].where(d["g"] != "c", 99.0))  # tiny group with huge median
    assert compare_groups(df, "g", "m")["group"].tolist()[-1] == "c"


def test_explicit_order_is_kept():
    out = compare_groups(_planted(), "g", "m", order=["c", "b", "a"])
    assert out["group"].tolist() == ["c", "b", "a"]


# ---------- sentiment aggregation ----------

from src.analytics.sentiment_agg import sentiment_by  # noqa: E402


def test_sentiment_by_hand_computed_and_min_n():
    df = pd.DataFrame({
        "brand_id": ["a"] * 20 + ["b"] * 5,
        "sentiment_label": ["positive"] * 12 + ["neutral"] * 4 + ["negative"] * 4 + ["negative"] * 5,
    })
    out = sentiment_by(df, "brand_id").set_index("group")
    # a: 12/20 pos, 4/20 neg -> net = 0.6 - 0.2 = 0.4
    assert out.loc["a", "net"] == pytest.approx(0.4) and out.loc["a", "positive"] == pytest.approx(0.6)
    assert out.loc["a", "net_low"] < 0.4 < out.loc["a", "net_high"]
    assert not out.loc["b", "sufficient"] and np.isnan(out.loc["b", "net_low"])
    assert out.index[-1] == "b"        # insufficient groups last


def test_sentiment_by_explodes_campaign_lists():
    df = pd.DataFrame({"campaign_tags": [["eid", "sale"]] * 20, "sentiment_label": ["positive"] * 20})
    out = sentiment_by(df, "campaign_tags").set_index("group")
    assert out.loc["eid", "n"] == 20 and out.loc["sale", "net"] == pytest.approx(1.0)
