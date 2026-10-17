# ARCHITECTURE_BLUEPRINT

**Status:** Phase 4 APPROVED (owner replied "next", 2026-10-17). Inputs: REQUIREMENTS_FORM.md, docs/DATA_AUDIT.md (P1–P5 approved), DECISIONS.md.

## 1. System overview

```text
config/brands.yaml (8 pinned channel IDs)
        │
        ▼
[ingestion]  YouTube Data API v3 client
   • full uploads-playlist paging → filter last 24 months
   • videos.list (stats, duration, snippet) in batches of 50
   • commentThreads (≤100 top comments/video, only where commentCount > 0)
   • quota meter, retries/backoff, raw JSON snapshot per run (data/raw/<date>/, git-ignored)
        │
        ▼
[validation] Pandera schemas: types, non-negative counts, nulls preserved, unique (video_id, snapshot_date)
        │
        ▼
[processing] canonical tables (Parquet, data/processed/, git-ignored)
   • UTC → Asia/Karachi; weekday/hour; video age at snapshot
   • duration buckets; hashtags/emoji/title-language from title+description
   • campaign tagger (rule-based keyword dictionary, EN + Roman Urdu + Urdu)
   • engagement metrics + "likely promoted" flag
   • comment text: drop author identity at ingestion
        │
        ├──► [analytics]   group comparisons with n, medians, bootstrap CIs, tests, effect sizes
        ├──► [nlp]         language detection → sentiment adapters → benchmark harness
        ├──► [ml]          (Could) leakage-safe engagement model vs baseline
        ▼
[recommendations] rule-based evidence engine → structured cards (what/where/when/why/n/limits/A-B test)
                  optional NVIDIA LLM rewrites a card into friendly wording (facts locked)
        │
        ▼
[app] Streamlit multipage + Plotly  ──►  [reporting] CSV / Excel / PDF exports
```

## 2. Module layout

```text
app.py                      Streamlit entry (thin; no business logic)
pages/                      1_Overview, 2_Brands, 3_Content, 4_Timing, 5_Sentiment, 6_Recommendations, 7_Data_&_Method
config/brands.yaml          brand → channel_id (pinned), display name
config/campaign_tags.yaml   tag → keyword list (EN / Roman Urdu / Urdu)
src/ingestion/youtube.py    API client, paging, quota, snapshots
src/validation/schemas.py   Pandera schemas
src/processing/             clean.py, features.py (time, duration, hashtags, tags), metrics.py
src/analytics/              compare.py (group stats, CIs, tests), timing.py
src/nlp/                    langid.py, sentiment/{base,hf_models,nvidia_llm}.py, benchmark.py
src/ml/                     (optional) baseline.py, model.py
src/recommendations/        engine.py, cards.py, llm_wording.py
src/reporting/              export.py (CSV/Excel), pdf.py
scripts/                    collect.py (CLI), check_secrets.sh
tests/                      unit + fixture-based tests (hand-computed expectations)
data/synthetic_demo/        SYNTHETIC labeled fixture data (committed, clearly marked)
```

## 3. Canonical schema (YouTube-specific)

**videos** (one row per video per snapshot)
`snapshot_date, brand_id, channel_id, video_id, published_at_utc, published_at_pkt, weekday_pkt, hour_pkt, age_days, title, description, hashtags[list], title_language, has_emoji, duration_s, duration_bucket, campaign_tags[list], view_count?, like_count?, comment_count?, subscriber_count_at_snapshot, er_views?, like_rate?, comment_rate?, views_per_sub?, likely_promoted(bool), low_reliability(bool), dq_flags[list], provenance`
(`?` = nullable; missing is never zero-filled)

**comments** (no author identity, ever)
`snapshot_date, video_id, comment_id_hash, published_at_utc, text, like_count, language, sentiment_label?, sentiment_model?`

**channels**: `snapshot_date, brand_id, channel_id, subscriber_count, video_count`

## 4. Metric definitions

| Metric | Formula | Notes |
|---|---|---|
| `er_views` | (likes + comments) / views | null if views = 0 or likes hidden |
| `like_rate` | likes / views | |
| `comment_rate` | comments / views | very sparse (DATA_AUDIT §4) |
| `views_per_sub` | views / channel subscribers at snapshot | normalizes brand size |
| `rel_er` | er_views / brand median er_views | **main comparison metric**: removes brand-mix confounding |
| `likely_promoted` | like_rate < brand median like_rate ÷ 5 **and** views > brand P75 | heuristic for ad-boosted views; reported separately, not deleted |
| `low_reliability` | views < 100 or age_days < 14 | excluded from main stats |

## 5. Statistical rules

- Report **median + bootstrap 95% CI** and **n** for every group; log scale for count metrics.
- Group differences: Kruskal-Wallis / Mann-Whitney with effect size (Cliff's δ); **Benjamini-Hochberg** correction across many comparisons.
- Minimum **n ≥ 20 per cell**; below that the UI shows "Insufficient data".
- Timing heatmap uses `rel_er` (within-brand) so a brand that posts a lot at one hour doesn't dominate.
- Wording is always associational ("is associated with"), never causal.

## 6. NLP design

- **Language ID:** script detection (Urdu block U+0600–06FF) → for Latin text, a Roman Urdu vs English classifier (lexicon heuristic first, benchmarked on the labeled set).
- **Sentiment candidates:** see table below. **Benchmark:** ~250 real comments, Claude-drafted + owner-verified labels (positive / negative / neutral / mixed→neutral), macro-F1 + confusion matrix per language. The winner per language is used.
- **Reporting level:** brand / campaign / month aggregates only (P2). Bonanza is excluded (P5).

| Language | Candidate |
|---|---|
| English | `cardiffnlp/twitter-roberta-base-sentiment-latest`; VADER baseline |
| Multilingual | `cardiffnlp/twitter-xlm-roberta-base-sentiment` (Urdu untested) |
| Roman Urdu | `Khubaib01/roman-urdu-sentiment-xlm-r` |
| Urdu script | shortlist in Phase 9 |
| All (LLM zero-shot) | NVIDIA `nvidia/nemotron-3-super-120b-a12b` (ADR-009) |

## 7. Recommendation engine

Rule-based: it scans analytics results for **statistically supported** findings (CI excludes the brand median, n ≥ 20, BH-adjusted p < 0.05) and turns each into a card:
`what` (e.g. "15–30 s Eid-tagged video") · `where` (YouTube) · `when` (PKT weekday/hour band) · `why` (effect + CI) · `n` · `limitations` (promoted views, correlation only) · `A/B test` (concrete test design).
The optional NVIDIA LLM only rephrases a card; numbers are injected from the card and checked after generation. Human review is required, and nothing is posted automatically.

## 8. Deployment & data-retention design (YouTube 30-day policy)

**Recommended:** the deployed app **collects live** from the API using the key in **Streamlit secrets**, caching for 24 h (`st.cache_data(ttl=24h)`). One full refresh costs ≈ 1,100–3,500 quota units (videos + comments), well under 10K/day. Stored data is therefore never older than 30 days, and no API data is committed to the public repo.
Heavy HF models don't run on Streamlit Cloud (≈1 GB RAM limit). In the deployed app, sentiment uses whichever benchmark winner fits: a small model, or the NVIDIA API, cached.
**Fallback:** if live collection fails (quota/network), the app shows the clearly labeled SYNTHETIC demo dataset with a banner.

## 9. Security

- Secrets only in `.env` (local) and Streamlit secrets (cloud); `scripts/check_secrets.sh` runs before every commit.
- No commenter identities are stored; comment IDs are hashed.
- Read-only public app, no login, no write access to any platform.

## 10. Testing strategy

- Unit tests: metrics on a hand-computed fixture, PKT conversion (DST-free), duration bucketing, hashtag/campaign extraction, null preservation, dedup.
- Contract tests: API client against recorded **synthetic** JSON responses (no live calls in CI).
- NLP: benchmark script produces a reproducible metrics table.
- App smoke test: Streamlit `AppTest` loads each page with synthetic data.

## 11. Environment

Python **3.12** recommended (Streamlit Cloud + torch/transformers wheel compatibility); the owner's machine has 3.14.4. Proposal: create a 3.12 venv via `uv` (needs permission to install `uv`). Alternative: try 3.14 and fall back if wheels fail.
Core deps: pandas, pyarrow, pandera, plotly, streamlit, scipy, scikit-learn, pyyaml, python-dotenv, requests, openpyxl, fpdf2, pytest. NLP (Phase 9): transformers, torch (CPU), vaderSentiment.

## 12. UI design

Mockups via the Google Stitch MCP in Phase 13 (the MCP is registered but its tools load only in a new session).
