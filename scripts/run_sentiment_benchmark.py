"""Benchmark language ID + sentiment models on data/labels/labels_v1.csv.

Usage: uv run --group nlp python scripts/run_sentiment_benchmark.py [--skip-llm]
Writes scores only (no comment text) to docs/NLP_BENCHMARK.md and docs/nlp_benchmark.json.
Predictions per comment go to data/labels/predictions_v1.csv (git-ignored).
"""

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import accuracy_score, classification_report, f1_score  # noqa: E402

from src.config import get_secret  # noqa: E402
from src.nlp.benchmark import benchmark_table  # noqa: E402
from src.nlp.langid import detect_language  # noqa: E402
from src.nlp.sentiment import HFModel, NvidiaLLM, VaderModel  # noqa: E402

LABELS = ROOT / "data" / "labels"
HF_MODELS = [
    "cardiffnlp/twitter-roberta-base-sentiment-latest",
    "cardiffnlp/twitter-xlm-roberta-base-sentiment",
    "Khubaib01/roman-urdu-sentiment-xlm-r",
]


def main() -> None:
    df = pd.read_csv(LABELS / "labels_v1.csv", encoding="utf-8-sig")
    verified = bool(df["verified_by_owner"].all())
    df["sentiment"] = df["owner_sentiment"].fillna("").replace("", pd.NA).fillna(df["sentiment_draft"])
    df["language"] = df["owner_language"].fillna("").replace("", pd.NA).fillna(df["language_draft"])
    texts = df["text"].astype(str).tolist()

    # ---- language ID ----
    df["lang_pred"] = [detect_language(t) for t in texts]
    lang_acc = accuracy_score(df["language"], df["lang_pred"])
    lang_report = classification_report(df["language"], df["lang_pred"], zero_division=0, output_dict=True)

    # ---- sentiment ----
    preds, notes = {}, {}
    preds["vader"] = VaderModel().predict(texts)
    for m in HF_MODELS:
        try:
            model = HFModel(m)
            notes[m] = f"id2label={model.id2label}"
            preds[m] = model.predict(texts)
            print("done", m, notes[m])
        except Exception as exc:  # report, don't fake
            notes[m] = f"FAILED: {type(exc).__name__}: {exc}"[:300]
            print(notes[m])
    if "--skip-llm" not in sys.argv:
        key = get_secret("NVIDIA_API_KEY")
        try:
            llm = NvidiaLLM(key, cache_path=LABELS / "nvidia_cache.json")
            preds[llm.name] = llm.predict(texts)
            print("done", llm.name)
        except Exception as exc:
            notes["nvidia"] = f"FAILED: {type(exc).__name__}: {exc}"[:300]
            print(notes["nvidia"])

    # routed: per-language best single model is chosen *after* scoring; also a fixed rule-based route
    if "cardiffnlp/twitter-roberta-base-sentiment-latest" in preds and "Khubaib01/roman-urdu-sentiment-xlm-r" in preds:
        en, ru = preds["cardiffnlp/twitter-roberta-base-sentiment-latest"], preds["Khubaib01/roman-urdu-sentiment-xlm-r"]
        preds["routed: EN→cardiff-roberta, RU/mixed→roman-urdu-xlmr"] = [
            r if lp in {"roman_urdu", "mixed"} else e for e, r, lp in zip(en, ru, df["lang_pred"])]

    table = benchmark_table(df, preds)
    out = df[["item_id", "sentiment", "language", "lang_pred"]].copy()
    for name, p in preds.items():
        out[f"pred::{name}"] = p
    out.to_csv(LABELS / "predictions_v1.csv", index=False, encoding="utf-8-sig")

    # ---- report (scores only) ----
    status = "OWNER-VERIFIED" if verified else "PROVISIONAL: labels are Claude drafts, not yet verified by the owner"
    dist = df["sentiment"].value_counts().to_dict()
    ldist = df["language"].value_counts().to_dict()
    lines = [
        "# NLP_BENCHMARK — Phase 9", "",
        f"**Run:** {date.today().isoformat()} · **Labels:** `data/labels/labels_v1.csv` (n={len(df)}) · **Status:** {status}", "",
        f"Label distribution: {dist}. Language distribution: {ldist}.", "",
        "## Language ID (rule-based, `src/nlp/langid.py`)", "",
        f"Accuracy **{lang_acc:.3f}** on n={len(df)}.", "",
        "| Language | precision | recall | support |", "|---|---|---|---|",
    ]
    for k, v in lang_report.items():
        if isinstance(v, dict) and "support" in v and k not in {"macro avg", "weighted avg"}:
            lines.append(f"| {k} | {v['precision']:.2f} | {v['recall']:.2f} | {int(v['support'])} |")
    lines += ["", "## Sentiment (3 classes; macro-F1 is the selection metric)", "",
              "| Model | Slice | n | macro-F1 | accuracy |", "|---|---|---|---|---|"]
    for r in table.sort_values(["slice", "macro_f1"], ascending=[True, False]).itertuples():
        flag = "" if r.sufficient else " ⚠️ n<20"
        lines.append(f"| {r.model} | {r.slice} | {r.n}{flag} | {r.macro_f1:.3f} | {r.accuracy:.3f} |")
    # paired bootstrap: is the best model really better than the runner-up?
    overall = table[table["slice"] == "all"].sort_values("macro_f1", ascending=False)
    top, second = overall["model"].iloc[0], overall["model"].iloc[1]
    rng, L = np.random.default_rng(0), ["positive", "neutral", "negative"]
    lines += ["", f"## Is `{top}` really better than `{second}`? (paired bootstrap, 2,000 resamples)", "",
              "| Slice | n | Δ macro-F1 (top − runner-up) | 95% CI |", "|---|---|---|---|"]
    for name, mask in (("all", df.index == df.index), ("english", df["language"] == "english"),
                       ("roman_urdu", df["language"] == "roman_urdu")):
        y, pa, pb = (df.loc[mask, "sentiment"].to_numpy(), np.array(preds[top])[mask.to_numpy() if hasattr(mask, "to_numpy") else mask],
                     np.array(preds[second])[mask.to_numpy() if hasattr(mask, "to_numpy") else mask])
        diffs = []
        for _ in range(2000):
            i = rng.integers(0, len(y), len(y))
            diffs.append(f1_score(y[i], pa[i], labels=L, average="macro", zero_division=0)
                         - f1_score(y[i], pb[i], labels=L, average="macro", zero_division=0))
        lo, hi = np.percentile(diffs, [2.5, 97.5])
        lines.append(f"| {name} | {len(y)} | {np.mean(diffs):+.3f} | [{lo:+.3f}, {hi:+.3f}]"
                     f"{' (includes 0: not significant)' if lo <= 0 <= hi else ''} |")
    lines += ["", "## Caveats", "",
              "- Labels are drafts by Claude (an LLM) until the owner verifies them; an LLM judge may agree with "
              "LLM-drafted labels more than a human would.",
              "- The NVIDIA LLM prompt contains the same labelling rubric the annotator used (questions → neutral, "
              "desire to buy → positive, praise + complaint → neutral); the local models don't see it.",
              "- Urdu-script (n=1) and mixed (n=3) comments are too rare to evaluate.", "",
              "Confusion matrices (rows = truth, cols = prediction; order positive, neutral, negative) are in "
              "`docs/nlp_benchmark.json`.", "", "## Notes", ""] + [f"- `{k}`: {v}" for k, v in notes.items()]
    (ROOT / "docs" / "NLP_BENCHMARK.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT / "docs" / "nlp_benchmark.json").write_text(json.dumps({
        "status": status, "n": len(df), "language_id_accuracy": lang_acc,
        "sentiment": table.to_dict(orient="records"), "notes": notes}, indent=1), encoding="utf-8")
    print(table.drop(columns="confusion").to_string())
    print("lang acc", round(lang_acc, 3))


if __name__ == "__main__":
    main()
