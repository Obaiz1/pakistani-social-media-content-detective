"""Group comparisons with honest uncertainty: n, median, bootstrap CI, tests, effect size, BH correction.

Rules (ARCHITECTURE_BLUEPRINT.md §5): groups with n < MIN_N are marked insufficient and are
never tested; every comparison is associational, not causal.
"""

import numpy as np
import pandas as pd
from scipy import stats

MIN_N = 20
N_BOOT = 2000
ALPHA = 0.05


def bootstrap_median_ci(values: np.ndarray, n_boot: int = N_BOOT, level: float = 0.95,
                        seed: int = 0) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(n_boot, len(values)), replace=True)
    medians = np.median(samples, axis=1)
    tail = (1 - level) / 2 * 100
    return float(np.percentile(medians, tail)), float(np.percentile(medians, 100 - tail))


def cliffs_delta(a: np.ndarray, b: np.ndarray) -> float:
    """P(a > b) - P(a < b), in [-1, 1]. |δ| < .147 negligible, < .33 small, < .474 medium, else large."""
    u = stats.mannwhitneyu(a, b, alternative="two-sided").statistic
    return float(2 * u / (len(a) * len(b)) - 1)


def effect_label(delta: float) -> str:
    d = abs(delta)
    return "negligible" if d < 0.147 else "small" if d < 0.33 else "medium" if d < 0.474 else "large"


def benjamini_hochberg(p: pd.Series) -> pd.Series:
    """BH-adjusted p-values (NaNs stay NaN)."""
    valid = p.dropna()
    if valid.empty:
        return p.astype(float)
    m = len(valid)
    order = valid.sort_values()
    ranked = order * m / np.arange(1, m + 1)
    adjusted = np.minimum.accumulate(ranked[::-1])[::-1].clip(upper=1.0)
    return pd.Series(adjusted, index=order.index).reindex(p.index)


def explode_groups(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """List-valued columns (e.g. campaign_tags) count a video once per group it belongs to."""
    if df[by].map(lambda x: isinstance(x, (list, np.ndarray))).any():
        return df.explode(by)
    return df


def compare_groups(df: pd.DataFrame, by: str, metric: str, min_n: int = MIN_N,
                   order: list[str] | None = None) -> pd.DataFrame:
    """One row per group: n, median, 95% CI; each sufficient group vs all other videos
    (Mann-Whitney U, Cliff's δ, BH-adjusted p). Plus Kruskal-Wallis across sufficient groups in .attrs."""
    data = explode_groups(df[[by, metric]].dropna(subset=[metric]), by).dropna(subset=[by])
    data[metric] = data[metric].astype(float)
    rows = []
    for group, sub in data.groupby(by, sort=False):
        vals = sub[metric].to_numpy()
        row = {"group": group, "n": len(vals), "median": float(np.median(vals)),
               "ci_low": np.nan, "ci_high": np.nan, "sufficient": len(vals) >= min_n,
               "p_value": np.nan, "cliffs_delta": np.nan}
        if row["sufficient"]:
            row["ci_low"], row["ci_high"] = bootstrap_median_ci(vals)
            rest = data.loc[data[by] != group, metric].to_numpy()
            if len(rest) >= min_n:
                row["p_value"] = float(stats.mannwhitneyu(vals, rest, alternative="two-sided").pvalue)
                row["cliffs_delta"] = cliffs_delta(vals, rest)
        rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        out.attrs["kruskal_p"] = np.nan
        return out
    out["p_adj"] = benjamini_hochberg(out["p_value"])
    out["significant"] = out["p_adj"] < ALPHA
    out["effect"] = out["cliffs_delta"].map(lambda d: effect_label(d) if pd.notna(d) else "")
    if order:
        out["group"] = pd.Categorical(out["group"], categories=order, ordered=True)
        out = out.sort_values("group").reset_index(drop=True)
        out["group"] = out["group"].astype(str)
    else:  # tested groups first (highest median on top), insufficient groups last
        out = out.sort_values(["sufficient", "median"], ascending=[False, False]).reset_index(drop=True)
    groups = [data.loc[data[by] == g, metric].to_numpy() for g in out.loc[out["sufficient"], "group"]]
    out.attrs["kruskal_p"] = float(stats.kruskal(*groups).pvalue) if len(groups) >= 2 else np.nan
    return out
