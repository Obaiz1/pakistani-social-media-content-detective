# Pakistani Social Media Content Detective 🇵🇰

An evidence-based analytics project that answers: **"What YouTube content gets Pakistani clothing-brand audiences to engage?"** It covers 8 brands' official channels, using data from the YouTube Data API v3.

**Status:** Phase 6 (runnable foundation). The app currently shows **SYNTHETIC demo data** only; the live YouTube pipeline arrives in Phase 7.

## Setup

Requires [uv](https://docs.astral.sh/uv/) (it manages Python 3.12 for you).

```bash
pip install uv                      # once
uv sync                             # creates .venv with Python 3.12 + dependencies
cp .env.example .env                # then fill in your own keys (never commit .env)
```

## Run

```bash
uv run streamlit run app.py         # dashboard at http://localhost:8501
uv run pytest                       # tests
uv run python scripts/make_synthetic_fixture.py   # regenerate the SYNTHETIC demo data
```

## Configuration

| Variable | Purpose |
|---|---|
| `YOUTUBE_API_KEY` | YouTube Data API v3 (public channel/video/comment data) |
| `NVIDIA_API_KEY` | Optional: NVIDIA API Catalog LLM (sentiment benchmark candidate, recommendation wording) |
| `STITCH_API_KEY` | Optional: Google Stitch MCP for UI mockups (development only) |

Before committing, run `bash scripts/check_secrets.sh`. It blocks any `.env` value from entering git.

## Data

- `data/synthetic_demo/` is **SYNTHETIC**. It's generated with fictional brand names for tests and UI only, and **is not real evidence**.
- Real API data stays local (`data/raw/`, `data/processed/` are git-ignored) and follows the YouTube API Services Developer Policies (refresh/delete within 30 days).

## Known limitations (from the Phase 2 audit, `docs/DATA_AUDIT.md`)

- Audience location/demographics aren't available, so results describe **Pakistan-related brand content**, not a verified Pakistani audience.
- About 99% of the videos are short-form, so format analysis uses duration buckets.
- Comments are sparse (~900 in 24 months), so sentiment is reported only at brand/campaign/month level.
- View counts likely include paid ad views, so promoted-looking videos are flagged.
- Every finding is correlational, not causal.

## Project documents

`CLAUDE.md` · `SESSION_HANDOFF.md` · `PROJECT_SCOPE.md` · `REQUIREMENTS_FORM.md` · `ARCHITECTURE_BLUEPRINT.md` · `IMPLEMENTATION_ROADMAP.md` · `DECISIONS.md` · `PROGRESS.md` · `docs/`

## AI-use disclosure

This project is built with AI assistance (Claude Code). All requirements and approvals come from the project owner.
