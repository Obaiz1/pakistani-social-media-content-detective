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
Not yet asked (Q6–Q11 in CLAUDE.md §4).

### Batch C — Data quality and metrics
Not yet asked (Q12–Q17).

### Batch D — Analytics and AI
Not yet asked (Q18–Q24).

### Batch E — Software and delivery
Not yet asked (Q25–Q30).

### Batch F — Privacy, evaluation, acceptance
Not yet asked (Q31–Q36).

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
Batch B: B1 main user, B2 content types/campaign tags, B3 timeframe, B4 report format. Then Batch C onward.
