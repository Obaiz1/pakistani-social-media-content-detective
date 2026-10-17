# ML_EVALUATION — Phase 11 (engagement prediction)

**Run:** 2026-10-17 · snapshot `2026-10-17` · target `log(engagement rate)` · chronological split: train 1476 videos (2024-10-18 → 2026-04-17), test 369 newest videos (2026-04-17 → 2026-10-03) · 42 features (pre-publication only).

| Model | MAE (log) | RMSE (log) | typical miss (×) | Δ MAE vs brand median [95% CI] | Δ MAE vs global median [95% CI] |
|---|---|---|---|---|---|
| baseline: global median | 0.609 | 0.961 | 1.48 | — | — |
| baseline: brand median | 0.699 | 1.043 | 1.48 | — | — |
| ridge | 0.679 | 0.975 | 1.58 | -0.021 [-0.045, +0.005] | +0.069 [+0.007, +0.137] |
| gradient boosting | 0.682 | 0.960 | 1.58 | -0.017 [-0.051, +0.019] | +0.073 [+0.018, +0.126] |

## Verdict

**No model beats the stronger baseline (global median).** Best model: ridge, MAE difference vs global median = +0.069, CI [+0.007, +0.137] (models are significantly worse). Per the plan, engagement prediction is **deferred**: pre-publication features don't predict a new video's engagement better than a single typical value. The global median also beats per-brand medians on the newest videos, which suggests brand engagement levels drifted over time (distribution shift).

## Notes

- *Typical miss (×)*: exp(median |log error|). 1.5 means the prediction is typically off by a factor of 1.5.
- Excluded: low-reliability (<100 views or <14 days) and likely-promoted videos, same as the dashboard.
- Newest videos are younger at snapshot time, which is a mild distribution shift the test set honestly includes.
- No hyper-parameter search on the test set (fixed, conservative settings).
