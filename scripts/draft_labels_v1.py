"""Claude's DRAFT labels for data/labels/sample_v1.csv (250 real comments; text stays out of git).

Codes: sentiment p/n/u = positive/negative/neutral; language e/r/d/m/o = english, roman_urdu,
urdu_script, mixed (English + Roman Urdu clauses), other (emoji/names/links/non-EN-UR).
Guideline: questions/info requests -> neutral; explicit desire to own/buy -> positive;
praise + complaint in one comment -> neutral (ARCHITECTURE_BLUEPRINT §6: mixed -> neutral).
Owner verification is required before any score is reported as final (F-15).
Usage: uv run python scripts/draft_labels_v1.py  -> data/labels/labels_v1.csv
"""

from pathlib import Path

import pandas as pd

DRAFT_LINES = [            # items
    "ue ue pe ue po ue pe ur ue pe",   # 1-10
    "ue ur pr ue po pr pe po pr pe",   # 11-20
    "ur nr pe pe ur ne ue ne pe ue",   # 21-30
    "ur ue uo po pe ur po ne ue ue",   # 31-40
    "pe pe ur pe ur pe pe pr pe po",   # 41-50
    "ur pe pe pe ue pr pe ue ur nr",   # 51-60
    "ue pr pr ne nr pe po pe ur nr",   # 61-70
    "ue ne pe uo nr pe pe pe pr ue",   # 71-80
    "ue pe ue ue ur nr po ur pe pe",   # 81-90
    "pd ue nr nr ne nr ne uo nr ur",   # 91-100
    "pr pe ue ue pe ue nr ue pe ur",   # 101-110
    "pe ur ne ue pe ne pe ue ur ue",   # 111-120
    "pe ue pe pe pe nr ue ur pe uo",   # 121-130
    "nr pe ue pe ne pr pe pe pe ue",   # 131-140
    "ue nm pe uo pm nr ue pe pe nr",   # 141-150
    "ue pe pe ne ne pe pe pe ur nr",   # 151-160
    "ne pe pe pe pe pe ue pe pe po",   # 161-170
    "uo nr pe pe pr pe ne pe pe pr",   # 171-180
    "pe pe pr po ur pr po pe ue pr",   # 181-190
    "ue pe ue pe ne ue pe pe pe pe",   # 191-200
    "ue nr ne ne pe pe ue ue ne pe",   # 201-210
    "nr po ne um uo po ue po pe uo",   # 211-220
    "nr ur po pe ue pe nr ue pr ue",   # 221-230
    "ne pe pe pe ue pe po ue pe uo",   # 231-240
    "uo ue ur ur pe ne ue ue ue uo",   # 241-250
]
DRAFT = " ".join(DRAFT_LINES)
LOW_CONFIDENCE = {6, 33, 35, 41, 48, 54, 58, 64, 68, 75, 84, 106, 133, 142, 154, 155, 183, 185, 216, 246, 249}
SENT = {"p": "positive", "n": "negative", "u": "neutral"}
LANG = {"e": "english", "r": "roman_urdu", "d": "urdu_script", "m": "mixed", "o": "other"}
LABELS = Path(__file__).resolve().parent.parent / "data" / "labels"


def draft_frame() -> pd.DataFrame:
    codes = DRAFT.split()
    assert len(codes) == 250, len(codes)
    return pd.DataFrame({
        "item_id": range(1, 251),
        "sentiment_draft": [SENT[c[0]] for c in codes],
        "language_draft": [LANG[c[1]] for c in codes],
        "draft_confidence": ["low" if i in LOW_CONFIDENCE else "normal" for i in range(1, 251)],
        "labeled_by": "claude_draft",
    })


def main() -> None:
    sample = pd.read_csv(LABELS / "sample_v1.csv", encoding="utf-8-sig")
    out = sample.merge(draft_frame(), on="item_id")
    out["owner_sentiment"] = ""   # owner fills only where they disagree
    out["owner_language"] = ""
    out["verified_by_owner"] = False
    out.to_csv(LABELS / "labels_v1.csv", index=False, encoding="utf-8-sig")
    print(out["sentiment_draft"].value_counts().to_dict(), out["language_draft"].value_counts().to_dict())


if __name__ == "__main__":
    main()
