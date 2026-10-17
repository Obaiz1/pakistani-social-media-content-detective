"""Aggregate comment sentiment to brand / campaign / month level (ADR-011 P2). No per-video claims."""

import numpy as np
import pandas as pd

from src.analytics.compare import MIN_N

SCORE = {"positive": 1, "neutral": 0, "negative": -1}


def net_sentiment_ci(labels: pd.Series, n_boot: int = 2000, seed: int = 0) -> tuple[float, float]:
    """95% bootstrap CI for net sentiment = share positive - share negative."""
    vals = labels.map(SCORE).to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    means = rng.choice(vals, size=(n_boot, len(vals)), replace=True).mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def sentiment_by(comments: pd.DataFrame, by: str, min_n: int = MIN_N) -> pd.DataFrame:
    """comments needs columns [by, 'sentiment_label']; list-valued `by` (campaign_tags) is exploded."""
    data = comments[[by, "sentiment_label"]].dropna()
    if data[by].map(lambda x: isinstance(x, (list, np.ndarray))).any():
        data = data.explode(by)
    rows = []
    for group, sub in data.groupby(by):
        lab = sub["sentiment_label"]
        n = len(lab)
        row = {"group": group, "n": n,
               "positive": float((lab == "positive").mean()), "neutral": float((lab == "neutral").mean()),
               "negative": float((lab == "negative").mean()), "sufficient": n >= min_n,
               "net": float(lab.map(SCORE).mean()), "net_low": np.nan, "net_high": np.nan}
        if row["sufficient"]:
            row["net_low"], row["net_high"] = net_sentiment_ci(lab)
        rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["sufficient", "net"], ascending=[False, False]).reset_index(drop=True)
