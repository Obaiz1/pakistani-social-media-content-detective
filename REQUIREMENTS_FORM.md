# REQUIREMENTS_FORM

**Status:** Phase 0 — Discovery | Batch A in progress
**Statuses:** CONFIRMED / PROPOSED / TBD / REJECTED

## Interview answers

### Batch A — Project foundation
| # | Question | Answer | Status |
|---|---|---|---|
| A1 | Project type (course assignment / semester project / FYP / portfolio / commercial)? Rubric? Deadline? | **Portfolio project.** Rubric: none mentioned. Deadline: TBD | CONFIRMED (deadline TBD) |
| A2 | Final deliverable (notebook+report / Streamlit / full-stack)? Default: Streamlit + modular Python + report | **Streamlit dashboard + modular Python analytics + project report** (owner accepted default) | CONFIRMED |
| A3 | Authorized dataset available today? Which platforms? | Owner said: "use Google's YouTube API, or Meta's API." No existing dataset. Proposed: YouTube Data API v3 as primary source; Meta (Instagram Graph API Business Discovery) optional, depending on account setup | PROPOSED (awaiting confirmation) |
| A4 | One brand / one industry / multiple brands? How to prove/label audience is Pakistani? | Owner said: "data on any Pakistan-related brand, collected by web scraping." Audience is labeled **"Pakistan-related content/brands"**, not "verified Pakistani audience". Web scraping: **not adopted**, because it conflicts with the CLAUDE.md §2 data rules and platform ToS; official APIs are proposed instead. Brand list: TBD | PROPOSED (scraping REJECTED pending owner acknowledgment) |
| A5 | Team members, skill level, environment (OS, Python, Claude Code, GitHub)? | **Individual** (solo). Windows 11, VS Code + Claude Code, Python 3.14.4, git 2.45, GitHub CLI logged in as `Obaiz1`. Owner wants the work **pushed to a GitHub repository progressively**. Skill level: TBD. Repo name/visibility: TBD | CONFIRMED (partial) |

### Batch A follow-ups
| # | Question | Answer | Status |
|---|---|---|---|
| A3a | YouTube Data API v3 as the primary source instead of scraping? | **Yes, proceed** (owner, 2026-10-17) | CONFIRMED |
| A3b | Does the owner have an Instagram Business/Creator account + Facebook Page + Meta developer app (needed for Business Discovery)? | Not answered. Default applied: **YouTube only for MVP**; Instagram deferred | PROPOSED (default) |
| A4b | Which brands/industry first? | **6–8 Pakistani clothing brands' official YouTube channels** (owner accepted default). Candidate list: Khaadi, Sapphire, Gul Ahmed, J. (Junaid Jamshed), Alkaram Studio, Bonanza Satrangi, Nishat Linen, Limelight. Channel existence/activity gets verified in Phase 2 | CONFIRMED (count/industry); list PROPOSED |
| A5b | GitHub repo name + public/private? | **`pakistani-social-media-content-detective`, public** | CONFIRMED |
| A1b | Target deadline? | Owner delegated ("use whatever"). No fixed deadline; work proceeds phase by phase | CONFIRMED (delegated) |
| A5c | Python skill level? | Not stated; owner wants a high-quality, complete result. Claude owns engineering quality; code stays documented and readable | CONFIRMED (delegated) |
| A6 | Hosting for the final deployment | Owner first asked for Vercel. Told that Streamlit can't run on Vercel serverless; owner chose **Option A: Streamlit Community Cloud**, free, deployed from the GitHub repo (2026-10-17). Vercel is dropped | CONFIRMED |

### Batch B — Business scope
Owner instruction for the remaining items: **"use default"** (2026-10-17).

| # | Question | Answer | Status |
|---|---|---|---|
| B1 | Main dashboard user | Recruiter/portfolio viewer + brand marketing analyst. Plain-English insights, technical detail in expandable sections | CONFIRMED (default) |
| B2 | Industries | Clothing (from A4b) | CONFIRMED |
| B3 | Platforms mandatory vs optional | YouTube mandatory; Instagram optional/deferred | CONFIRMED |
| B4 | Content types & objectives | Shorts vs long-form videos; campaign tags derived from title/description (Eid/festive, sale, new collection, lawn/summer, winter, etc.). Objective = engagement | CONFIRMED (default) |
| B5 | Timeframe / volume | Last 24 months of videos for 6–8 brands | CONFIRMED (default) |
| B6 | Report / demo deliverables | PDF report + README screenshots + short demo GIF; no slides | CONFIRMED (default) |

> **Delegation note (2026-10-17):** For everything still pending, the owner said *"abhe procced kro bad mae dekhte"* (proceed now, we'll revisit later). Every item below marked **DEFAULT** is a documented Claude default under that delegation. The owner can change any of them later; when that happens, update the row and DECISIONS.md.

### Batch C — Data quality and metrics
| # | Question | Answer | Status |
|---|---|---|---|
| C1 | Available columns | YouTube API (to be verified in Phase 2): video_id, channel_id, published_at, title, description, tags, duration, view_count, like_count (can be hidden → null), comment_count (null if comments disabled), channel subscriber_count; public comment text + like count. **Not available:** shares, saves, reach, impressions, audience country/age/gender | DEFAULT |
| C2 | Engagement definition | Primary: **ER_views = (likes + comments) / views**. Secondary: per-subscriber views. Videos with < 100 views get flagged low-reliability. Formula and coverage are shown in the UI | DEFAULT |
| C3 | Observation window | Record a snapshot date at collection; exclude videos younger than **14 days**; video age (days) is a control variable | DEFAULT |
| C4 | Comment text & privacy | Up to **100 top comments per video**. Drop commenter name, channel ID, and profile URL; keep only text, like count, and published time | DEFAULT |
| C5 | Time zone | Store in UTC, display/analyze in **Asia/Karachi** | DEFAULT |
| C6 | Audience segments | No permitted audience data, so the segment view shows **"Unavailable"** | DEFAULT |
| C7 | Validation / duplicates / retention | Deduplicate on video_id (latest snapshot wins); warn when a brand has < 30 videos; missing values stay null; raw API data stays local and out of git. Retention must follow the YouTube API Developer Policies, which get checked in Phase 2 (stored API data may need periodic refresh/deletion) | DEFAULT |

### Batch D — Analytics and AI
| # | Question | Answer | Status |
|---|---|---|---|
| D1 | Must-have charts/filters | KPI tiles; brand comparison; Shorts vs long (distribution plots); campaign-tag comparison; weekday × hour heatmap (PKT); sentiment vs ER scatter; top keywords/hashtags. Filters: brand, date range, format, campaign tag, language. Every chart shows n and caveats | DEFAULT |
| D2 | Languages | English, Urdu script, Roman Urdu, and mixed, with language detection routing | DEFAULT |
| D3 | Sentiment level & labels | Comment-level sentiment, aggregated per video. Benchmark the candidate models (ARCHITECTURE_BLUEPRINT) on ~200–300 real comments. **Claude drafts labels, owner verifies.** Metrics: macro-F1 + confusion matrix | DEFAULT |
| D4 | Topics/hashtags | Frequency + TF-IDF first; BERTopic optional (Could) | DEFAULT |
| D5 | Engagement prediction | **Could-have.** Target: log(views) or ER at a fixed age; chronological split; median baseline; MAE/RMSE. Deferred if it doesn't beat the baseline | DEFAULT |
| D6 | AI output scope | Evidence-based recommendations first (what/where/when/why/n/limitations/A-B idea). LLM captions are optional later. Human approval is always required; no auto-posting | DEFAULT |
| D7 | AI provider / budget | Free local Hugging Face models + **NVIDIA API Catalog LLM (free, owner-provided keys, ADR-009)**. No paid AI. Internet is needed only for data collection; the dashboard runs on stored data | DEFAULT |

### Batch E — Software and delivery
| # | Question | Answer | Status |
|---|---|---|---|
| E1 | Stack | Python + Pandas + Plotly + Streamlit, modular `src/` services, Parquet storage, Pandera validation, pytest | DEFAULT |
| E2 | Hosting | Streamlit Community Cloud (A6) | CONFIRMED |
| E3 | Login | None. Public, read-only, single-user app | DEFAULT |
| E4 | Exports | CSV + Excel (filtered data) + PDF report | DEFAULT |
| E5 | Visual / accessibility | Clean professional theme, colorblind-safe palette, readable on mobile; mockups via Stitch MCP | DEFAULT |
| E6 | Hardware / budget / deadline | Personal laptop, **free tiers only**, no fixed deadline | DEFAULT |

### Batch F — Privacy, evaluation, acceptance
| # | Question | Answer | Status |
|---|---|---|---|
| F1 | Ethics / licensing / AI-use | No university constraints (portfolio). Must follow the YouTube API ToS + Developer Policies and Hugging Face model licenses; AI assistance is disclosed in the README | DEFAULT |
| F2 | Evaluation metrics | Pipeline: tests pass on fixtures. Sentiment: macro-F1 per language. ML: MAE vs baseline. Recommendations: each one cites evidence + n | DEFAULT |
| F3 | How results are verified | Small fixture CSV with hand-computed expected values in pytest; the README documents how to reproduce | DEFAULT |
| F4 | Synthetic data | Allowed **for UI/tests only**, always labeled "SYNTHETIC" | DEFAULT |
| F5 | Approver | Owner (Obaiz1) approves every gate | CONFIRMED |
| F6 | Completion / deferrable | Done = deployed dashboard + PDF report + README + passing tests. Deferrable: Instagram, ML prediction, LLM captions, BERTopic | DEFAULT |

## Requirements register
Format: `REQ-ID | Description / user story | Priority | Data dependency | Status | Acceptance criterion | Phase`

| REQ-ID | Description | Priority | Data dependency | Status | Acceptance criterion | Phase |
|---|---|---|---|---|---|---|
| REQ-NF-01 | Use only legitimate, permissioned, or officially accessible data | Must | — | PROPOSED | Every source has documented provenance/permission | 2 |
| REQ-NF-02 | Missing metrics stay null, never defaulted to zero | Must | Post metrics | PROPOSED | Pipeline tests confirm nulls preserved | 7 |
| REQ-NF-03 | Synthetic data clearly labeled, never presented as real evidence | Must | — | PROPOSED | Synthetic rows/charts carry a visible label | 6 |
| REQ-NF-04 | No auto-publishing; AI output requires human review | Must | — | PROPOSED | No publish integration exists | 12 |
| REQ-D-01 | Collect public video metadata/statistics for 6–8 Pakistani clothing brand channels via YouTube Data API v3 | Must | YouTube API key (owner-created, stored in `.env`) | CONFIRMED | Ingestion stays within free quota; raw responses saved with provenance | 7 |
| REQ-D-02 | Optionally collect public post metrics for other IG business accounts via Instagram Graph API Business Discovery | Could | Owner's IG Business account + FB Page + Meta app | PROPOSED | Works only if owner confirms access; otherwise documented as deferred | 7 |
| REQ-D-03 | Label analysis as "Pakistan-related content"; audience segment views show "Unavailable" without permitted audience data | Must | — | PROPOSED | UI/report never claims a verified Pakistani audience | 10 |
| REQ-DEL-01 | Streamlit dashboard + modular Python analytics + project report | Must | — | CONFIRMED | All three delivered at Phase 14 | 14 |
| REQ-DEL-03 | Deploy the dashboard publicly on Streamlit Community Cloud from the GitHub repo; secrets via Streamlit secrets, never in the repo | Must | YouTube API key or pre-collected dataset | CONFIRMED | Public `*.streamlit.app` URL loads the dashboard | 14 |
| REQ-DEL-02 | Version-controlled GitHub repository updated as the work progresses; no secrets committed | Must | — | CONFIRMED | Repo exists; `.env` git-ignored | 6 |

## Outstanding questions
None blocking. **Phase 1 gate: waiting for the owner's explicit requirements sign-off** (see PROJECT_SCOPE.md → "One-page scope summary").
