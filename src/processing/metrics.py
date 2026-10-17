"""Engagement metrics (definitions: ARCHITECTURE_BLUEPRINT.md §4). Nulls propagate; nothing is zero-filled."""

import pandas as pd

MIN_VIEWS = 100
MIN_AGE_DAYS = 14
PROMOTED_LIKE_RATE_DIVISOR = 5
PROMOTED_VIEWS_QUANTILE = 0.75


def _ratio(num: pd.Series, den: pd.Series) -> pd.Series:
    num, den = num.astype("Float64"), den.astype("Float64")
    return (num / den.where(den > 0)).astype("Float64")


def add_metrics(videos: pd.DataFrame, channels: pd.DataFrame) -> pd.DataFrame:
    df = videos.copy()
    subs = channels.set_index("brand_id")["subscriber_count"]
    df["subscriber_count_at_snapshot"] = df["brand_id"].map(subs).astype("Int64")

    df["like_rate"] = _ratio(df["like_count"], df["view_count"])
    df["comment_rate"] = _ratio(df["comment_count"], df["view_count"])
    # Both components must be present; hidden likes or disabled comments make ER unknown, not smaller.
    df["er_views"] = _ratio(df["like_count"] + df["comment_count"], df["view_count"])
    df["views_per_sub"] = _ratio(df["view_count"], df["subscriber_count_at_snapshot"])

    df["low_reliability"] = (df["view_count"].fillna(0) < MIN_VIEWS) | (df["age_days"] < MIN_AGE_DAYS)

    reliable = df[~df["low_reliability"]]
    brand_er_median = reliable.groupby("brand_id")["er_views"].median()
    brand_like_median = reliable.groupby("brand_id")["like_rate"].median()
    brand_views_p75 = reliable.groupby("brand_id")["view_count"].quantile(PROMOTED_VIEWS_QUANTILE)

    er_median = df["brand_id"].map(brand_er_median).astype("Float64")
    df["rel_er"] = (df["er_views"] / er_median.where(er_median > 0)).astype("Float64")

    like_threshold = df["brand_id"].map(brand_like_median).astype("Float64") / PROMOTED_LIKE_RATE_DIVISOR
    views_threshold = df["brand_id"].map(brand_views_p75).astype("Float64")
    df["likely_promoted"] = ((df["like_rate"] < like_threshold) & (df["view_count"] > views_threshold)).fillna(False).astype(bool)
    return df
