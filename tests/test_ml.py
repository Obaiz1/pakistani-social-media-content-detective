"""Phase 11 tests: no future leakage, baselines fit on train only, features aligned (SYNTHETIC data)."""

import numpy as np
import pandas as pd

from src.app_data import synthetic_dataset
from src.ml.engagement_model import brand_median_baseline, chronological_split, evaluate, features, prepare


def _videos():
    return synthetic_dataset().videos


def test_split_is_chronological_with_no_overlap():
    train, test = chronological_split(prepare(_videos()))
    assert train["published_at_utc"].max() <= test["published_at_utc"].min()
    assert len(test) == round(0.2 * (len(train) + len(test)))


def test_prepare_drops_unreliable_promoted_and_unknown_er():
    df = prepare(_videos())
    assert not df["low_reliability"].any() and not df["likely_promoted"].any()
    assert df["er_views"].notna().all() and np.isfinite(df["y"]).all()


def test_features_exclude_outcomes_and_align_test_to_train():
    train, test = chronological_split(prepare(_videos()))
    X_tr = features(train)
    X_te = features(test, columns=list(X_tr.columns))
    assert list(X_te.columns) == list(X_tr.columns)
    leaky = [c for c in X_tr.columns if any(k in c for k in ("view", "like", "comment", "er_", "age", "rel_"))]
    assert leaky == []


def test_brand_baseline_uses_train_only():
    train = pd.DataFrame({"brand_id": ["a", "a", "a", "b"], "y": [1.0, 2.0, 9.0, 5.0]})
    test = pd.DataFrame({"brand_id": ["a", "b", "new"], "y": [100.0, -100.0, 7.0]})
    before = brand_median_baseline(train, test)
    assert before.tolist() == [2.0, 5.0, 3.5]          # a: median(1,2,9); b: 5; unseen brand: global train median
    test["y"] = [-1e6, 1e6, 0.0]                        # changing test targets must not move the baseline
    assert brand_median_baseline(train, test).tolist() == before.tolist()


def test_evaluate_reports_ci_for_models():
    r = evaluate(_videos(), n_boot=100)
    for m in ("ridge", "gradient boosting"):
        for key in ("brand", "global"):
            lo, hi = r["results"][m][f"mae_diff_vs_{key}_ci"]
            assert lo <= r["results"][m][f"mae_diff_vs_{key}"] <= hi
