"""Leakage-safe engagement prediction (Phase 11, 'Could'): can pre-publication features predict ER?

- Target: log(er_views). Not rel_er, whose brand median is computed on ALL videos (incl. test) = leakage.
- Features: only things known before publishing (brand, length, campaign tags, hashtags, emoji,
  title script/length, PKT weekday + time band). No views, likes, comments, age.
- Chronological split: the newest TEST_SHARE of videos is the test set; baselines are fit on train only.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge

from src.analytics.timing import add_time_bands
from src.processing.features import DURATION_ORDER

TEST_SHARE = 0.2
EPS = 1e-4
CAT_COLS = ["brand_id", "duration_bucket", "weekday_pkt", "hour_band_pkt", "title_script"]


def prepare(videos: pd.DataFrame) -> pd.DataFrame:
    """Reliable, non-promoted videos with a known ER, sorted by publish time."""
    df = videos[~videos["low_reliability"] & ~videos["likely_promoted"] & videos["er_views"].notna()].copy()
    df = add_time_bands(df).sort_values("published_at_utc").reset_index(drop=True)
    df["y"] = np.log(df["er_views"].astype(float) + EPS)
    return df


def chronological_split(df: pd.DataFrame, test_share: float = TEST_SHARE) -> tuple[pd.DataFrame, pd.DataFrame]:
    cut = int(round(len(df) * (1 - test_share)))
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()


def features(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """One-hot categoricals + multi-hot campaign tags + numeric title features. `columns` aligns test to train."""
    X = pd.get_dummies(df[CAT_COLS].astype(str), prefix=CAT_COLS, dtype=float)
    tags = df["campaign_tags"].map(lambda t: list(t) if t is not None else [])
    X = X.join(pd.get_dummies(tags.explode()).groupby(level=0).max().add_prefix("tag_").astype(float))
    X["hashtag_count"] = df["hashtag_count"].astype(float)
    X["title_len"] = df["title"].fillna("").str.len().astype(float)
    X["title_has_emoji"] = df["title_has_emoji"].astype(float)
    X["duration_rank"] = df["duration_bucket"].map({b: i for i, b in enumerate(DURATION_ORDER)}).astype(float)
    X = X.fillna(0.0)
    if columns is not None:
        X = X.reindex(columns=columns, fill_value=0.0)
    return X


def brand_median_baseline(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Each test video predicted as its brand's TRAIN median (global train median for unseen brands)."""
    global_median = float(np.median(train["y"]))
    return test["brand_id"].map(train.groupby("brand_id")["y"].median()).fillna(global_median).to_numpy(dtype=float)


def _errors(y: np.ndarray, pred: np.ndarray) -> dict:
    err = pred - y
    return {"mae_log": float(np.mean(np.abs(err))), "rmse_log": float(np.sqrt(np.mean(err ** 2))),
            # typical multiplicative miss on the ER scale: exp(median |log error|)
            "median_factor_error": float(np.exp(np.median(np.abs(err))))}


def evaluate(videos: pd.DataFrame, seed: int = 0, n_boot: int = 2000) -> dict:
    df = prepare(videos)
    train, test = chronological_split(df)
    y_tr, y_te = train["y"].to_numpy(), test["y"].to_numpy()

    preds = {
        "baseline: global median": np.full(len(test), np.median(y_tr)),
        "baseline: brand median": brand_median_baseline(train, test),
    }
    X_tr = features(train)
    X_te = features(test, columns=list(X_tr.columns))
    preds["ridge"] = Ridge(alpha=3.0).fit(X_tr, y_tr).predict(X_te)
    preds["gradient boosting"] = HistGradientBoostingRegressor(
        max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=30, l2_regularization=1.0,
        random_state=seed).fit(X_tr, y_tr).predict(X_te)

    results = {name: _errors(y_te, p) for name, p in preds.items()}

    # paired bootstrap vs BOTH baselines: MAE(model) - MAE(baseline); negative = model better.
    # A model only "wins" if it beats the stronger baseline.
    rng = np.random.default_rng(seed)
    for name in ("ridge", "gradient boosting"):
        model_abs = np.abs(preds[name] - y_te)
        for key, base in (("brand", "baseline: brand median"), ("global", "baseline: global median")):
            diff_abs = model_abs - np.abs(preds[base] - y_te)
            boots = [diff_abs[rng.integers(0, len(diff_abs), len(diff_abs))].mean() for _ in range(n_boot)]
            results[name][f"mae_diff_vs_{key}"] = float(diff_abs.mean())
            results[name][f"mae_diff_vs_{key}_ci"] = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]

    return {
        "n_train": len(train), "n_test": len(test),
        "train_period": [str(train["published_at_utc"].min().date()), str(train["published_at_utc"].max().date())],
        "test_period": [str(test["published_at_utc"].min().date()), str(test["published_at_utc"].max().date())],
        "n_features": X_tr.shape[1], "results": results,
    }
