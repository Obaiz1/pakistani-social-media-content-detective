"""Adjusted effects: mixed-effects regression of log(engagement rate) on content + timing features.

Why: the group comparisons look at one feature at a time, so a "Saturday effect" could really be a
campaign or brand effect. Here every feature is estimated *holding the others constant*, with a random
intercept per brand and a variance component per calendar month (seasonality / drift).
Robustness check: OLS with brand + month fixed effects and HC3 standard errors.
Effects are reported as % change in engagement rate vs the reference level: exp(beta) - 1.
"""

import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from src.analytics.compare import benjamini_hochberg
from src.analytics.timing import add_time_bands

REFERENCES = {"weekday": "Monday", "band": "Afternoon (12–16)", "length": "16-30s", "hashtags": "0"}
TAG_COLUMNS = ["eid", "ramadan", "sale", "new_arrivals", "lawn_summer", "winter", "wedding_festive",
               "independence", "men", "kids"]
MIN_TAG_N = 20


def model_frame(videos: pd.DataFrame) -> pd.DataFrame:
    df = videos[~videos["low_reliability"] & ~videos["likely_promoted"] & (videos["er_views"] > 0)].copy()
    df = add_time_bands(df)
    out = pd.DataFrame({
        "y": np.log(df["er_views"].astype(float)),
        "brand": df["brand_id"].astype(str),
        "month": df["published_at_pkt"].dt.strftime("%Y-%m"),
        "weekday": df["weekday_pkt"].astype(str),
        "band": df["hour_band_pkt"].astype(str),
        "length": df["duration_bucket"].astype(str),
        "hashtags": pd.cut(df["hashtag_count"], [-1, 0, 2, 5, 1_000], labels=["0", "1-2", "3-5", "6+"]).astype(str),
        "emoji": df["title_has_emoji"].astype(int),
    }, index=df.index)
    tags = df["campaign_tags"].map(lambda t: set(t) if t is not None else set())
    for tag in TAG_COLUMNS:
        out[f"tag_{tag}"] = tags.map(lambda s, tag=tag: int(tag in s))
    # drop tags too rare to estimate; drop levels with < 10 videos into NaN rows (removed below)
    out = out[[c for c in out if not c.startswith("tag_") or out[c].sum() >= MIN_TAG_N]]
    for col in ("band", "length"):
        counts = out[col].value_counts()
        out = out[out[col].isin(counts[counts >= 10].index)]
    return out.reset_index(drop=True)


def _formula(frame: pd.DataFrame) -> str:
    tag_terms = [c for c in frame if c.startswith("tag_")]
    cats = [f"C({col}, Treatment(reference='{ref}'))" for col, ref in REFERENCES.items() if ref in set(frame[col])]
    return "y ~ " + " + ".join(cats + tag_terms + ["emoji"])


def _tidy(params: pd.Series, conf: pd.DataFrame, pvalues: pd.Series, model: str) -> pd.DataFrame:
    keep = [t for t in params.index if t not in ("Intercept",) and not t.startswith(("C(brand", "C(month", "Group", "month"))
            and not t.endswith(" Var")]
    t = pd.DataFrame({"term": keep, "coef": params[keep].values, "ci_low": conf.loc[keep, 0].values,
                      "ci_high": conf.loc[keep, 1].values, "p_value": pvalues[keep].values})
    t["effect_pct"] = np.expm1(t["coef"]) * 100
    t["effect_ci_low"] = np.expm1(t["ci_low"]) * 100
    t["effect_ci_high"] = np.expm1(t["ci_high"]) * 100
    t["p_adj"] = benjamini_hochberg(t["p_value"]).values
    t["significant"] = t["p_adj"] < 0.05
    t["label"] = t["term"].map(readable_term)
    t["model"] = model
    return t


def readable_term(term: str) -> str:
    if term.startswith("tag_"):
        return f"Campaign: {term[4:].replace('_', '/')}"
    if term == "emoji":
        return "Emoji in title"
    for col, nice in (("weekday", "Weekday"), ("band", "Time band"), ("length", "Length"), ("hashtags", "Hashtags")):
        if term.startswith(f"C({col}"):
            level = term.split("[T.", 1)[1].rstrip("]")
            return f"{nice}: {level} (vs {REFERENCES[col]})"
    return term


def fit_models(videos: pd.DataFrame) -> dict:
    frame = model_frame(videos)
    formula = _formula(frame)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mixed = smf.mixedlm(formula, frame, groups="brand", vc_formula={"month": "0 + C(month)"},
                            re_formula="1").fit(reml=True, method="lbfgs")
        fe = smf.ols(formula + " + C(brand) + C(month)", frame).fit(cov_type="HC3")
    mixed_t = _tidy(mixed.fe_params, mixed.conf_int().loc[mixed.fe_params.index], mixed.pvalues[mixed.fe_params.index],
                    "mixed effects (brand RE + month VC)")
    fe_t = _tidy(fe.params, fe.conf_int(), fe.pvalues, "OLS brand+month FE, HC3")
    both = mixed_t.merge(fe_t[["term", "effect_pct", "p_adj", "significant"]], on="term", suffixes=("", "_fe"))
    both["robust"] = both["significant"] & both["significant_fe"] & (np.sign(both["effect_pct"]) == np.sign(both["effect_pct_fe"]))
    return {"n": len(frame), "brands": frame["brand"].nunique(), "months": frame["month"].nunique(),
            "formula": formula, "table": both.sort_values("effect_pct", ascending=False).reset_index(drop=True),
            "brand_var": float(mixed.cov_re.iloc[0, 0]), "converged": bool(mixed.converged)}
