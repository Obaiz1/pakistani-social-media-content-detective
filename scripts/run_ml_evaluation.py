"""Phase 11: evaluate engagement prediction vs baselines on the latest snapshot.

Usage: uv run python scripts/run_ml_evaluation.py [snapshot_dir]
Writes docs/ML_EVALUATION.md and docs/ml_evaluation.json (aggregate metrics only).
"""

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.config import DATA_DIR  # noqa: E402
from src.ml.engagement_model import evaluate  # noqa: E402


def main() -> None:
    snap = Path(sys.argv[1]) if len(sys.argv) > 1 else max((DATA_DIR / "processed").iterdir())
    r = evaluate(pd.read_parquet(snap / "videos.parquet"))
    res = r["results"]
    best = min(("ridge", "gradient boosting"), key=lambda m: res[m]["mae_log"])
    strong = min(("brand", "global"), key=lambda k: res[f"baseline: {k} median"]["mae_log"])
    lo, hi = res[best][f"mae_diff_vs_{strong}_ci"]
    beats = hi < 0
    verdict = (f"**{best}** beats the stronger baseline ({strong} median): MAE difference CI [{lo:+.3f}, {hi:+.3f}] "
               "is entirely below 0." if beats else
               f"**No model beats the stronger baseline ({strong} median).** Best model: {best}, MAE difference "
               f"vs {strong} median = {res[best][f'mae_diff_vs_{strong}']:+.3f}, CI [{lo:+.3f}, {hi:+.3f}] "
               f"({'models are significantly worse' if lo > 0 else 'includes 0'}). Per the plan, engagement prediction "
               "is **deferred**: pre-publication features don't predict a new video's engagement better than a "
               "single typical value. The global median also beats per-brand medians on the newest videos, which "
               "suggests brand engagement levels drifted over time (distribution shift).")
    lines = [
        "# ML_EVALUATION — Phase 11 (engagement prediction)", "",
        f"**Run:** {date.today().isoformat()} · snapshot `{snap.name}` · target `log(engagement rate)` · "
        f"chronological split: train {r['n_train']} videos ({r['train_period'][0]} → {r['train_period'][1]}), "
        f"test {r['n_test']} newest videos ({r['test_period'][0]} → {r['test_period'][1]}) · {r['n_features']} features "
        "(pre-publication only).", "",
        "| Model | MAE (log) | RMSE (log) | typical miss (×) | Δ MAE vs brand median [95% CI] | Δ MAE vs global median [95% CI] |",
        "|---|---|---|---|---|---|",
    ]

    def delta(m, key):
        if f"mae_diff_vs_{key}_ci" not in m:
            return "—"
        a, b = m[f"mae_diff_vs_{key}_ci"]
        return f"{m[f'mae_diff_vs_{key}']:+.3f} [{a:+.3f}, {b:+.3f}]"

    for name, m in res.items():
        lines.append(f"| {name} | {m['mae_log']:.3f} | {m['rmse_log']:.3f} | {m['median_factor_error']:.2f} | "
                     f"{delta(m, 'brand')} | {delta(m, 'global')} |")
    lines += ["", "## Verdict", "", verdict, "",
              "## Notes", "",
              "- *Typical miss (×)*: exp(median |log error|). 1.5 means the prediction is typically off by a factor of 1.5.",
              "- Excluded: low-reliability (<100 views or <14 days) and likely-promoted videos, same as the dashboard.",
              "- Newest videos are younger at snapshot time, which is a mild distribution shift the test set honestly includes.",
              "- No hyper-parameter search on the test set (fixed, conservative settings)."]
    (ROOT / "docs" / "ML_EVALUATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT / "docs" / "ml_evaluation.json").write_text(json.dumps({**r, "verdict_beats_baseline": beats}, indent=1),
                                                       encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
