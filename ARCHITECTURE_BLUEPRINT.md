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
TBD

## Deployment
TBD
