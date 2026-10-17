# PROJECT_SCOPE — Pakistani Social Media Content Detective

**Status:** Phase 0 — Discovery | NOT APPROVED
**Last updated:** 2026-10-17

## Business problem
Central question: **"What type of social-media content gets Pakistani audiences to engage?"**
Users act as junior marketing data scientists: investigate social-media data, present defensible insights, and recommend the next content a Pakistani brand should test.

## Objectives (PROPOSED, from CLAUDE.md §1)
Answer, only where data supports it:
1. Platform performance (with per-platform metric definitions)
2. Content format vs engagement
3. Popular/effective topics, keywords, hashtags
4. Sentiment vs engagement relationship
5. Promising posting days/times (Asia/Karachi)
6. Responsive audience segments — only with credible, permitted segment data
7. What to post next, where, and why
8. AI-assisted, evidence-backed marketing suggestions

## Project type / rubric / deadline
- Type: **Portfolio project, individual** (CONFIRMED)
- Rubric: none mentioned
- Deadline: TBD
- Published progressively to a GitHub repository (CONFIRMED; name/visibility TBD)

## Actors / users
TBD (candidates: student, evaluator, marketing analyst, brand owner)

## In scope
- 6–8 Pakistani clothing brands' official YouTube channels (CONFIRMED; exact list PROPOSED: Khaadi, Sapphire, Gul Ahmed, J., Alkaram Studio, Bonanza Satrangi, Nishat Linen, Limelight)
- Data via YouTube Data API v3 (CONFIRMED primary source)
- Instagram Graph API Business Discovery: deferred (Could)
- Final public deployment on **Streamlit Community Cloud** (CONFIRMED; Vercel dropped, see ADR-007)

## Out of scope (PROPOSED)
- Web scraping of social platforms (owner's initial suggestion; not adopted, see DECISIONS ADR-002)
- Claims about verified Pakistani audience geography (we don't have permitted audience data)
- Scraping restricted pages, bypassing logins, collecting private user info
- Auto-publishing to social-media accounts
- Guaranteeing reach, virality, or business results

## Assumptions
- Most remaining choices are delegated defaults (see REQUIREMENTS_FORM.md); the owner may revise them.
- Selected brands have active official YouTube channels with enough videos (verified in Phase 2).

## Success criteria
- Public Streamlit dashboard answers Q1–Q5 + Q7 for YouTube data, showing n and caveats on every insight
- Sentiment model chosen by a measured benchmark (macro-F1) on a human-verified labeled set
- Every recommendation states what/where/when/why/n/limitations/A-B test idea
- Reproducible setup; tests pass; no secrets in the repo

## One-page scope summary (for Phase 1 sign-off)
| Area | Scope |
|---|---|
| Question | Which YouTube content gets Pakistani clothing brand audiences to engage? |
| Data | YouTube Data API v3: 6–8 brands, last 24 months, videos + up to 100 top comments/video |
| Not included | Scraping, Instagram (deferred), audience demographics, speech-to-text, auto-posting |
| Metric | ER = (likes+comments)/views; videos < 14 days old excluded; PKT time analysis |
| NLP | Language detection → benchmarked sentiment (EN / Urdu / Roman Urdu); keywords/hashtags |
| Optional | Engagement prediction, BERTopic, LLM captions (Claude Haiku, needs budget) |
| Product | Streamlit + Plotly dashboard, CSV/Excel/PDF exports, Streamlit Community Cloud |
| Quality | pytest with hand-checked fixtures; synthetic data only for UI, labeled |
| Done | Deployed app + PDF report + README (screenshots, GIF) + passing tests |

## Deliverables
Streamlit dashboard + modular Python analytics + project report (CONFIRMED 2026-10-17)
