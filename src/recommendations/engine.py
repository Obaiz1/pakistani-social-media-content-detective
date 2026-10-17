"""Evidence cards: turn statistically supported findings into testable next-post recommendations.

Only findings with n >= MIN_N and BH-adjusted p < ALPHA become cards. Each card carries
what / where / when / why / n / limitations / A-B test, and states its effect size honestly.
"""

from dataclasses import asdict, dataclass, field

import pandas as pd

from src.analytics.compare import compare_groups
from src.analytics.timing import BAND_ORDER, WEEKDAYS, add_time_bands
from src.processing.features import DURATION_ORDER

TAG_LABELS = {"eid": "Eid", "ramadan": "Ramadan", "sale": "sale/discount", "new_arrivals": "new-arrival",
              "lawn_summer": "lawn/summer", "winter": "winter", "wedding_festive": "wedding/festive",
              "independence": "Independence (Azadi)", "kids": "kids", "men": "menswear", "other": "untagged"}

# dimension -> (column, human label for a group, kind)
DIMENSIONS = {
    "duration_bucket": ("Video length", lambda g: f"{g} videos", "content", DURATION_ORDER),
    "campaign_tags": ("Campaign", lambda g: "videos without a campaign theme" if g == "other"
                      else f"{TAG_LABELS.get(g, g)} content", "content", None),
    "hashtag_band": ("Hashtag count", lambda g: f"videos with {g} hashtags", "content", ["0", "1–2", "3–5", "6+"]),
    "emoji_in_title": ("Emoji in title", lambda g: "videos with an emoji in the title" if g.startswith("Emoji")
                       else "videos without an emoji in the title", "content", None),
    "hour_band_pkt": ("Time band (PKT)", lambda g: f"posting in the {g} slot", "timing", BAND_ORDER),
    "weekday_pkt": ("Weekday (PKT)", lambda g: f"posting on {g}", "timing", WEEKDAYS),
}

BASE_LIMITATIONS = [
    "Correlation, not causation: brands may time or tag their strongest campaigns differently.",
    "YouTube public metrics only; views can include paid ads (likely-promoted videos excluded).",
    "Audience is not verified as Pakistani; this describes Pakistan-related brand content.",
]


@dataclass
class Finding:
    dimension: str
    group: str
    label: str
    kind: str
    n: int
    median: float
    rest_median: float
    ci_low: float
    ci_high: float
    cliffs_delta: float
    effect: str
    p_adj: float

    @property
    def direction(self) -> str:
        return "higher" if self.cliffs_delta > 0 else "lower"


@dataclass
class Card:
    title: str
    what: str
    where: str
    when: str
    why: str
    n: int
    limitations: list[str]
    ab_test: str
    strength: str
    kind: str                     # "do_more" | "do_less" | "next_post"
    numbers: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)


def prepare_features(videos: pd.DataFrame) -> pd.DataFrame:
    df = add_time_bands(videos)
    df["hashtag_band"] = pd.cut(df["hashtag_count"], [-1, 0, 2, 5, 1_000], labels=["0", "1–2", "3–5", "6+"]).astype(str)
    df["emoji_in_title"] = df["title_has_emoji"].map({True: "Emoji in title", False: "No emoji in title"})
    return df


def collect_findings(videos: pd.DataFrame) -> list[Finding]:
    df = prepare_features(videos)
    found = []
    for col, (_, label_fn, kind, order) in DIMENSIONS.items():
        summary = compare_groups(df, col, "rel_er", order=order)
        if summary.empty:
            continue
        for r in summary[summary["significant"].fillna(False).astype(bool)].itertuples():
            found.append(Finding(col, r.group, label_fn(r.group), kind, int(r.n), r.median, r.rest_median,
                                 r.ci_low, r.ci_high, r.cliffs_delta, r.effect, r.p_adj))
    return found


def _strength(f: Finding) -> str:
    return {"large": "strong", "medium": "moderate", "small": "modest"}.get(f.effect, "weak (negligible effect size)")


def _ab_test(f: Finding) -> str:
    if f.kind == "timing":
        return (f"For 4 weeks, alternate comparable videos between {f.label.replace('posting ', '')} and your usual slot "
                "(same campaign, length and hashtags). Compare median engagement after 14 days per video; "
                "aim for at least 20 videos per arm.")
    return (f"Publish 10–20 {f.label} and 10–20 otherwise-similar videos in the same weeks and time slots. Compare "
            "median engagement (likes + comments ÷ views) after 14 days; keep ad spend equal or exclude boosted posts.")


def card_from_finding(f: Finding) -> Card:
    up = f.direction == "higher"
    slot = f.label.replace("posting ", "")
    numbers = {"median": round(f.median, 2), "rest_median": round(f.rest_median, 2), "ci_low": round(f.ci_low, 2),
               "ci_high": round(f.ci_high, 2), "n": f.n, "p_adj": round(f.p_adj, 3),
               "cliffs_delta": round(f.cliffs_delta, 2)}
    why = (f"{f.label[0].upper() + f.label[1:]}: median relative engagement {f.median:.2f} (95% CI "
           f"{f.ci_low:.2f}–{f.ci_high:.2f}) vs {f.rest_median:.2f} for all other videos (1.00 = a brand's typical "
           f"video). Cliff's δ {f.cliffs_delta:+.2f} ({f.effect} effect), BH-adjusted p = {f.p_adj:.3f}.")
    if f.kind == "content":
        what = f"Test more {f.label}." if up else f"De-prioritise {f.label}; test alternatives."
        when = "Keep your usual schedule (see the timing cards)."
    else:
        what = f"Schedule comparable uploads {slot}." if up else f"Move some uploads away from {slot.removeprefix('on ').removeprefix('in the ')}."
        when = f"{slot[0].upper() + slot[1:]} (PKT)." if up else f"Avoid {slot.removeprefix('on ').removeprefix('in the ')} (PKT) until tested."
    return Card(
        title=("Try more: " if up else "Use less: ") + f.label,
        what=what, when=when,
        where="YouTube (short-form ≤ 3 min, matching ~99% of the brands' uploads).",
        why=why, n=f.n, limitations=BASE_LIMITATIONS + (
            [f"Effect size is {f.effect}: expect a small or uncertain lift."] if f.effect in {"negligible", "small"} else []),
        ab_test=_ab_test(f), strength=_strength(f), kind="do_more" if up else "do_less", numbers=numbers,
    )


def next_post_card(findings: list[Finding]) -> Card | None:
    """Combine the best supported content and timing signals into one testable next-post plan."""
    pos = sorted([f for f in findings if f.direction == "higher"], key=lambda f: -f.cliffs_delta)
    neg = sorted([f for f in findings if f.direction == "lower"], key=lambda f: f.cliffs_delta)
    content = next((f for f in pos if f.kind == "content"), None)
    timing = next((f for f in pos if f.kind == "timing"), None)
    if content is None and timing is None:
        return None
    avoid = ", ".join(f.label for f in neg[:3]) or "nothing significant"
    used = [f for f in (content, timing) if f]
    return Card(
        title="Next post to test",
        what=(f"A {content.label.replace(' content', '')} video" if content else "Your usual content")
             + f". De-prioritise: {avoid}.",
        where="YouTube, short-form.",
        when=(timing.label.replace("posting ", "").capitalize() + " (PKT)") if timing else "No reliable timing signal; keep schedule.",
        why=" ".join(card_from_finding(f).why for f in used),
        n=min(f.n for f in used),
        limitations=BASE_LIMITATIONS + ["Combining two signals assumes their effects add up; this is untested."],
        ab_test="Run it as a 4-week A/B: half of comparable uploads follow this plan, half follow the usual plan; "
                "compare median engagement after 14 days per video (≥ 20 videos per arm).",
        strength=min((_strength(f) for f in used), key=["strong", "moderate", "modest", "weak (negligible effect size)"].index),
        kind="next_post",
        numbers={f"{f.dimension}:{k}": v for f in used for k, v in card_from_finding(f).numbers.items()},
    )


def build_cards(videos: pd.DataFrame) -> list[Card]:
    findings = collect_findings(videos)
    cards = [c for c in [next_post_card(findings)] if c]
    cards += [card_from_finding(f) for f in sorted(findings, key=lambda f: -abs(f.cliffs_delta))]
    return cards
