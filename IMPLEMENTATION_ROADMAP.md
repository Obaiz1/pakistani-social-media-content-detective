# IMPLEMENTATION_ROADMAP

**Current phase:** 8 — Analytics MVP built, awaiting **Demo/approve MVP** gate

| Phase | Name | Concrete output | Gate | Status |
|---|---|---|---|---|
| 0 | Understand the real problem | Problem statement, stakeholders, success goals, first questions | Approve problem framing | Completed |
| 1 | Gather and finalize requirements | Filled requirements form, priorities, acceptance criteria | **Approve requirements** | Completed (owner replied "next" to the sign-off request, 2026-10-17) |
| 2 | Feasibility & responsible data audit | Authorized source matrix, sample-column audit, quality/risk report | **Approve data scope** | Completed (P1–P5 approved, ADR-011) |
| 3 | Compare proposed solutions | Notebook vs Streamlit vs full stack, tradeoffs | Approve solution direction | Completed (owner: "next") |
| 4 | Design complete architecture | Diagram, modules, schema, flows, metrics, evaluation | **Approve architecture** | Completed (owner: "next") |
| 5 | Plan execution | Backlog, acceptance tests, file structure, tasks | **Authorize coding** | Completed (owner: "next", 2026-10-17) |
| 6 | Build runnable foundation | Environment, skeleton, app entry, tests, demo fixture | Smoke test | Completed (5/5 tests pass; server health ok) |
| 7 | Implement data pipeline | Import, validation, mapping, cleaning, dedup | Data pipeline tests | Completed (46 tests pass; real run 2,204 videos) |
| 8 | Build analytics MVP | Engagement, platform/content comparisons, filters, charts | **Demo/approve MVP** | Built (63 tests pass; rendered + visually checked); awaiting owner approval |
| 9 | Add multilingual NLP | Urdu/Roman Urdu/English, hashtags, topics, evaluated sentiment | NLP tests/evaluation | Not started |
| 10 | Timing & engagement patterns | Weekday/hour heatmaps, authorized segment views | Insight validation | Not started |
| 11 | Investigate predictive ML | Leakage-safe baseline vs model; defer if infeasible | Model evaluation | Not started |
| 12 | AI-assisted recommendation engine | Explainable next-post experiments, optional LLM captions | **Review quality** | Not started |
| 13 | Complete dashboard and exports | UX, filters, reports, error states, docs | End-to-end demo | Not started |
| 14 | Test and deliver | Unit/integration/acceptance tests, setup, final report/demo | **Final sign-off** | Not started |

---

## Phase 5 — Execution plan

### Feature backlog

| ID | Feature | Priority | Phase | Depends on | Acceptance test |
|---|---|---|---|---|---|
| F-01 | Env: `uv` + Python 3.12 venv, `pyproject.toml`, secret check before commits | Must | 6 | — | `uv run pytest` runs; `streamlit run app.py` opens a placeholder page |
| F-02 | SYNTHETIC fixture dataset (videos, comments, channels) | Must | 6 | F-01 | Fixture loads; every row has `provenance="SYNTHETIC"` |
| F-03 | `config/brands.yaml` with 8 pinned channel IDs | Must | 7 | — | 8 unique IDs, all start with `UC` |
| F-04 | YouTube client: full uploads paging, batched `videos.list`, quota meter, retry/backoff | Must | 7 | F-03 | Contract tests on recorded synthetic JSON: all pages collected; quota counted; quota-exceeded 403 raises a clear error |
| F-05 | Comments (≤100/video, only if `commentCount>0`); author identity dropped; comment ID hashed | Must | 7 | F-04 | No author fields in output; zero-comment videos skipped |
| F-06 | Pandera schemas + validation report | Must | 7 | F-04 | Negative counts rejected; nulls preserved (never 0); duplicates detected |
| F-07 | Processing: PKT time, weekday/hour, age_days, duration buckets, hashtags, emoji, title language | Must | 7 | F-06 | Hand-computed: `2024-11-01T19:30Z` → PKT Sat 00:30; 45 s → `31–60s`; `#Eid #Lawn` parsed |
| F-08 | Campaign tagger (`config/campaign_tags.yaml`, EN / Roman Urdu / Urdu) | Must | 7 | F-07 | Fixture titles map to expected tags; untagged → `other` |
| F-09 | Metrics: er_views, like_rate, comment_rate, views_per_sub, rel_er, likely_promoted, low_reliability | Must | 7 | F-07 | Hand-computed values match to 1e-9; hidden likes → null ER |
| F-10 | Collector CLI `scripts/collect.py` → dated snapshot Parquet (git-ignored) | Must | 7 | F-04–F-09 | Real 8-brand run completes; quota reported; counts within ±5% of audit |
| F-11 | Analytics: median + bootstrap CI + n, Kruskal/Mann-Whitney, Cliff's δ, BH correction, n≥20 rule | Must | 8 | F-09 | Planted synthetic difference detected; n<20 → "insufficient" |
| F-12 | Dashboard MVP: Overview, Brands, Content, Data & Method pages + filters | Must | 8 | F-11 | `AppTest` loads every page with fixture; every chart shows n |
| F-13 | Live mode: Streamlit secrets + 24 h cache; synthetic fallback with banner | Must | 8 | F-10, F-12 | No key → banner + synthetic; key → real data |
| F-14 | Language ID (Urdu script / Roman Urdu / English) | Must | 9 | F-05 | Accuracy measured on labeled set and reported |
| F-15 | Labeled benchmark (~250 real comments; Claude drafts, owner verifies) | Must | 9 | F-10 | Labels file with `verified_by_owner=true` (kept out of git if it contains comment text) |
| F-16 | Sentiment adapters (HF, VADER, NVIDIA LLM) + benchmark (macro-F1, confusion matrix) | Must | 9 | F-15 | Reproducible scores table committed (no comment text) |
| F-17 | Sentiment page: brand/campaign/month aggregates; Bonanza excluded | Must | 9 | F-16 | n<20 groups show "Insufficient data" |
| F-18 | Timing: weekday × hour PKT heatmap on rel_er | Must | 10 | F-11 | Fixture cells match hand totals |
| F-19 | Engagement prediction (chronological split, median baseline, MAE/RMSE) | Could | 11 | F-10 | Reported vs baseline; deferred if not better |
| F-20 | Recommendation engine → evidence cards | Must | 12 | F-11, F-18 | Every card has all 7 fields; only significant findings produce cards |
| F-21 | Optional NVIDIA LLM wording with number-lock check | Should | 12 | F-20 | Numbers in the text equal the card's numbers, else template fallback |
| F-22 | Exports: filtered CSV, Excel, PDF report | Must | 13 | F-12 | Files open; PDF includes charts + caveats |
| F-23 | UI polish via Stitch mockups; colorblind palette; mobile check | Should | 13 | F-12 | Manual checklist passes |
| F-24 | README (setup, screenshots, GIF, limitations, AI-use disclosure) + final report | Must | 14 | all | Fresh clone works using README alone |
| F-25 | Deploy to Streamlit Community Cloud | Must | 14 | F-13 | Public URL loads; no secrets in repo |
| F-26 | Instagram Business Discovery | Won't (MVP) | — | — | Deferred |

### Target file structure
See ARCHITECTURE_BLUEPRINT.md §2, plus `pyproject.toml`, `uv.lock`, `.streamlit/config.toml`.

### Sprint plan

| Sprint | Phases | Features | Exit gate |
|---|---|---|---|
| S1 | 6 | F-01, F-02 | Smoke test passes |
| S2 | 7 | F-03 → F-10 | Pipeline tests pass + real collection run |
| S3 | 8 | F-11 → F-13 | **Demo/approve MVP** |
| S4 | 9 | F-14 → F-17 | NLP benchmark reviewed |
| S5 | 10–11 | F-18, F-19 | Insight validation; model evaluated or deferred |
| S6 | 12 | F-20, F-21 | **Review quality** |
| S7 | 13–14 | F-22 → F-25 | **Final sign-off** |

### Definition of done (per feature)
Input contract + implementation + error/empty states + passing tests + docs + visible output. PROGRESS.md and SESSION_HANDOFF.md updated, secret check passed, pushed.
