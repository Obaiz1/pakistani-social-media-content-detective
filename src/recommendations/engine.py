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
    adjusted: str = ""            # what the mixed-effects model says after controlling for brand, month, other features

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
        slot = f.label.replace("posting ", "").removeprefix("on ").removeprefix("in the ")
        return (f"For 4 weeks, alternate comparable videos between {slot} and your usual slot "
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
    avoid = ", ".join(f.label for f in neg if f.kind == "content") or "nothing significant"
    avoid_slots = [f.label.replace("posting ", "").removeprefix("on ").removeprefix("in the ")
                   for f in neg if f.kind == "timing"]
    if timing:
        when = timing.label.replace("posting ", "").capitalize() + " (PKT)."
    elif avoid_slots:
        unit = "day" if all(s in WEEKDAYS for s in avoid_slots) else "slot"
        when = f"Any {unit} except {' / '.join(avoid_slots)} (PKT); no reliable best-time signal."
    else:
        when = "No reliable timing signal; keep your usual schedule."
    used = [f for f in (content, timing) if f]
    return Card(
        title="Next post to test",
        what=(f"A {content.label.replace(' content', '')} video" if content else "Your usual content")
             + f". De-prioritise: {avoid}.",
        where="YouTube, short-form.",
        when=when,
        why=" ".join(card_from_finding(f).why for f in used),
        n=min(f.n for f in used),
        limitations=BASE_LIMITATIONS + ["Combining two signals assumes their effects add up; this is untested."],
        ab_test="Run it as a 4-week A/B: half of comparable uploads follow this plan, half follow the usual plan; "
                "compare median engagement after 14 days per video (≥ 20 videos per arm).",
        strength=min((_strength(f) for f in used), key=["strong", "moderate", "modest", "weak (negligible effect size)"].index),
        kind="next_post",
        numbers={f"{f.dimension}:{k}": v for f in used for k, v in card_from_finding(f).numbers.items()},
    )


ACTIONABLE_EFFECTS = {"small", "medium", "large"}   # |Cliff's δ| >= 0.147; negligible effects aren't worth acting on


def _regression_term(f: Finding) -> str | None:
    """Map a one-at-a-time finding to the matching term of the adjusted model (None if no comparable term)."""
    if f.dimension == "campaign_tags" and f.group != "other":
        return f"tag_{f.group}"
    if f.dimension == "weekday_pkt":
        return f"C(weekday, Treatment(reference='Monday'))[T.{f.group}]"
    if f.dimension == "hour_band_pkt":
        return f"C(band, Treatment(reference='Afternoon (12–16)'))[T.{f.group}]"
    if f.dimension == "duration_bucket":
        return f"C(length, Treatment(reference='16-30s'))[T.{f.group}]"
    return None


def apply_adjusted_check(cards: list[Card], findings: list[Finding], table: pd.DataFrame | None) -> None:
    """Annotate cards with the adjusted-model verdict; downgrade strength when the adjusted model doesn't confirm."""
    if table is None or table.empty:
        return
    by_term = table.set_index("term")
    by_title = {card_from_finding(f).title: f for f in findings}
    for card in cards:
        parts = [by_title.get(card.title)] if card.kind != "next_post" else [
            f for f in findings if card_from_finding(f).why in card.why]
        verdicts = []
        for f in filter(None, parts):
            term = _regression_term(f)
            if term is None or term not in by_term.index:
                continue
            r = by_term.loc[term]
            ok = bool(r["robust"]) and (r["effect_pct"] > 0) == (f.direction == "higher")
            verdicts.append(ok)
            card.adjusted += (f"{r['label']}: {r['effect_pct']:+.0f}% (95% CI {r['effect_ci_low']:+.0f}% to "
                              f"{r['effect_ci_high']:+.0f}%), BH-adjusted p = {r['p_adj']:.2f} → "
                              + ("confirmed. " if ok else "NOT confirmed after adjusting for brand, month and other features. "))
        if verdicts and not all(verdicts):
            card.strength = "tentative (not confirmed by the adjusted model)"
            card.limitations = card.limitations + [
                "The mixed-effects model (brand, month, all features together) does not confirm this effect."]


def build_cards(videos: pd.DataFrame, adjust: bool = True) -> tuple[list[Card], list[Card]]:
    """(actionable cards, weak signals). Weak = significant but negligible effect size: shown, never recommended.
    With adjust=True each card is also checked against the mixed-effects model (src/analytics/regression.py)."""
    findings = sorted(collect_findings(videos), key=lambda f: -abs(f.cliffs_delta))
    actionable = [f for f in findings if f.effect in ACTIONABLE_EFFECTS]
    cards = [c for c in [next_post_card(actionable)] if c]
    cards += [card_from_finding(f) for f in actionable]
    weak = [card_from_finding(f) for f in findings if f.effect not in ACTIONABLE_EFFECTS]
    if adjust and cards and len(videos) >= 200:
        try:
            from src.analytics.regression import fit_models
            apply_adjusted_check(cards, actionable, fit_models(videos)["table"])
        except Exception:  # model can fail on tiny/singular selections; cards stay unadjusted
            pass
    return cards, weak
