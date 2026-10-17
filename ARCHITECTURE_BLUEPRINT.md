# ARCHITECTURE_BLUEPRINT

**Status:** PROPOSED ONLY — not approved (approval gate is Phase 4)

## Proposed flow (CSV-first)
```text
Approved CSV/Excel or official authorized API
  -> Source validation + provenance + schema mapping
  -> Cleaning, deduplication, timezone and metric normalization
  -> Canonical post dataset (+ optional permitted aggregate audiences/comments)
  -> Descriptive analytics | NLP (hashtags/topics/language/evaluated sentiment) | Optional ML
  -> Evidence + sample size + caveats + traceable insights
  -> Explainable recommendation engine
  -> Streamlit dashboard + filtered exports + project report
```

## Candidate stack (to evaluate in Phase 3, not assumed)
Python 3.11+, Pandas, NumPy, Plotly, Streamlit, Pydantic/Pandera, scikit-learn, pytest; optional multilingual transformer/LLM only if justified; Parquet/SQLite if storage helps.

## Proposed canonical post schema
`source_id, platform, post_id, brand_id, published_at_utc, content_type, caption_text, hashtags, language, like_count, comment_count, share_count, save_count, view_count, reach_count, impression_count, follower_count, imported_at_utc, provenance, data_quality_flags`

## Per-platform engagement definitions
TBD (depends on available columns — Batch C)

## Security / privacy
TBD

## ML / NLP evaluation design
### Sentiment model candidates (PROPOSED 2026-10-17; none has been benchmarked yet)
| Language | Candidate | Notes |
|---|---|---|
| English | `cardiffnlp/twitter-roberta-base-sentiment-latest` | Trained on social-media text; 3 classes |
| English (baseline) | VADER (rule-based) | Fast, simple baseline |
| Multilingual | `cardiffnlp/twitter-xlm-roberta-base-sentiment` | Fine-tuned on 8 languages incl. Hindi, **not Urdu**; Urdu needs testing |
| Roman Urdu | `Khubaib01/roman-urdu-sentiment-xlm-r` | XLM-R fine-tuned, 3 classes, MIT; benchmark claims are self-reported |
| Urdu script | Urdu-specific fine-tuned XLM-R/mBERT on Hugging Face (to be shortlisted in Phase 9) | Some are binary-only |
| Any (LLM zero-shot) | Claude Haiku via API (optional, paid) | Handles code-mixed Roman Urdu well; needs budget approval (ADR-008) |

Plan: language detection routes each text to the right model, then we benchmark the candidates on a **hand-labeled evaluation set** (~200–300 real comments) using macro-F1 + a confusion matrix. Only the measured winner per language gets used, and no accuracy is claimed without this test.

## Deployment
TBD
