"""Posting-time analysis in Pakistan Standard Time, on within-brand relative engagement (rel_er)."""

import numpy as np
import pandas as pd

from src.analytics.compare import MIN_N

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
HOUR_BANDS = [(0, 6, "Night (00–06)"), (6, 12, "Morning (06–12)"), (12, 16, "Afternoon (12–16)"),
              (16, 20, "Evening (16–20)"), (20, 24, "Prime time (20–24)")]
BAND_ORDER = [label for _, _, label in HOUR_BANDS]


def hour_band(hour: int) -> str:
    for lo, hi, label in HOUR_BANDS:
        if lo <= hour < hi:
            return label
    raise ValueError(f"hour out of range: {hour}")


def add_time_bands(videos: pd.DataFrame) -> pd.DataFrame:
    out = videos.copy()
    out["hour_band_pkt"] = out["hour_pkt"].map(hour_band)
    return out


def heatmap_table(videos: pd.DataFrame, metric: str = "rel_er", min_n: int = MIN_N) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(median, n) pivots: rows = weekday (Mon..Sun), cols = PKT hour band. Cells with n < min_n -> NaN median."""
    data = add_time_bands(videos).dropna(subset=[metric])
    grouped = data.groupby(["weekday_pkt", "hour_band_pkt"])[metric]
    median = grouped.median().unstack().reindex(index=WEEKDAYS, columns=BAND_ORDER)
    n = grouped.size().unstack().reindex(index=WEEKDAYS, columns=BAND_ORDER).fillna(0).astype(int)
    median = median.where(n >= min_n)
    return median.astype(float), n
