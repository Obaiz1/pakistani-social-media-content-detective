"""Score sentiment predictions against labels: macro-F1, accuracy, confusion matrix, per language."""

import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from src.nlp.sentiment import LABELS


def score(y_true: list[str], y_pred: list[str]) -> dict:
    return {
        "n": len(y_true),
        "macro_f1": float(f1_score(y_true, y_pred, labels=list(LABELS), average="macro", zero_division=0)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "confusion": confusion_matrix(y_true, y_pred, labels=list(LABELS)).tolist(),
    }


def benchmark_table(labels: pd.DataFrame, predictions: dict[str, list[str]],
                    truth_col: str = "sentiment", lang_col: str = "language",
                    min_n: int = 20) -> pd.DataFrame:
    """One row per (model, slice). Slices with n < min_n are reported but flagged."""
    rows = []
    slices = {"all": labels.index}
    for lang, idx in labels.groupby(lang_col).groups.items():
        slices[lang] = idx
    for model, preds in predictions.items():
        p = pd.Series(preds, index=labels.index)
        for name, idx in slices.items():
            s = score(labels.loc[idx, truth_col].tolist(), p.loc[idx].tolist())
            rows.append({"model": model, "slice": name, "n": s["n"], "macro_f1": s["macro_f1"],
                         "accuracy": s["accuracy"], "sufficient": s["n"] >= min_n, "confusion": s["confusion"]})
    return pd.DataFrame(rows)
