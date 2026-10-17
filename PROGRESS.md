# PROGRESS

**Current phase:** 12 — Recommendations | Built, awaiting review

## Log
### 2026-10-17
- Inspected project folder: it was empty (no existing work, data, or secrets).
- Created `CLAUDE.md` (copy of master prompt) and scaffolds: `PROJECT_SCOPE.md`, `REQUIREMENTS_FORM.md`, `ARCHITECTURE_BLUEPRINT.md`, `IMPLEMENTATION_ROADMAP.md`, `DECISIONS.md`, `PROGRESS.md`, `README.md`.
- Tests run: none (no code yet, by design).
- Asked Batch A questions (A1–A5).

- Recorded Batch A answers: portfolio, individual, Streamlit+Python+report confirmed, GitHub wanted.
- Flagged web scraping as non-compliant; proposed official APIs instead (ADR-002).
- Environment check (actual output): git 2.45.2, gh 2.93.0 (logged in as Obaiz1), Python 3.14.4.
- Initialized local git repo with `.gitignore` and made the first commit of the docs. No GitHub remote yet.

- Owner provided a Google Stitch API key. Saved it to `.env` (git-ignored, verified with `git check-ignore`) and added `.env.example` with empty placeholders. Registered the Stitch MCP server with `claude mcp add -s local`; `claude mcp get stitch` reported **✓ Connected**.

- Batch A closed: YouTube API confirmed, 6–8 clothing brands, public repo confirmed, deadline/skill delegated, Vercel deployment requested.
- Created the public GitHub repo `Obaiz1/pakistani-social-media-content-detective` and pushed `main`.

- Hosting decided: Streamlit Community Cloud (ADR-007).

- Batch B closed with defaults (owner: "use default").
- Added `SESSION_HANDOFF.md` per the owner's request so future sessions can resume; `CLAUDE.md` now says to read it first.

- YouTube API key saved to `.env`. Test call (actual result): `channels.list?forHandle=@khaadi` → `UCosHRi7jeBb0JGZfFlOHYUA | Khaadi | subs: 47300 | videos: 819`. Cost: 1 quota unit.

- Phase 1 signed off (owner: "next").
- Phase 2 audit run (actual): 8 channels resolved, ~2,190–2,300 videos in 24 m, ~896 comments total, ~1,035 quota units. Results in docs/DATA_AUDIT.md.

- Phase 2 gate approved (owner: "next"). Phase 3 doc + Phase 4 architecture drafted.

- Phase 3/4 approved (owner: "next"); Phase 5 plan drafted.

- Coding authorized (owner: "next").
- Phase 6 (actual results): `python -m pip install --user uv` → uv 0.13.1; `uv python install 3.12` → cpython-3.12.15; `uv sync` OK; fixture: channels 8, videos 357, comments 239 rows; `uv run pytest -q` → **5 passed in 3.97s** (first run 1 failed: AppTest path is relative to the test file, fixed to `../app.py`); `streamlit run` headless → `/_stcore/health` = ok, page HTTP 200.

- Phase 7: implemented F-03..F-10. `uv run pytest` → **46 passed**. First real run crashed (`requests.ConnectionError: RemoteDisconnected`), since network errors weren't retried; fixed + 2 tests. Phase 7 real run 2026-10-17 (actual): `uv run python scripts/collect.py` → exit 0, channels=8, videos=2,204, comments=781 from 444 videos, quota=655 units. Per-brand video counts match the Phase 2 audit exactly (0.0% diff; Nishat=615 confirms full paging). 0 duplicate videos/comments, 0 author columns, 0 hidden likes. Duration buckets: 0-15s 728, 16-30s 939, 31-60s 444, 61-180s 88, >180s 5. likely_promoted=242 (11%). low_reliability=131. Comment scripts: latin 654, emoji/none 122, **Urdu script only 5** (Urdu-script sentiment benchmark n will be tiny). 781 < ~888 audit commentCount because commentCount includes replies; we fetch top-level only.

- Phase 8 (actual): `uv run pytest` → **63 passed**. All 4 pages render on the real snapshot (AppTest, no exceptions) and in headless Edge (screenshots checked). Fixes found while verifying: Bonanza 107/109 null ER → ADR-015; Plotly category order; insufficient groups sorted last; deprecated `use_container_width`. Preliminary real-data findings (snapshot 2026-10-17; reliable, non-promoted videos n=1,845; metric rel_er; BH-adjusted): Wedding/festive median 1.34 (CI 1.21–1.48, adj p 0.001, small effect δ≈0.16), the only campaign clearly above typical. Sale/discount 0.94 (adj p 0.015) and untagged 1.00 (adj p 0.002) are below the rest. 0–15 s videos 1.05 vs the rest (adj p 0.006, negligible effect). 0 hashtags 1.22 (adj p 0.002) vs 6+ hashtags 1.03 (adj p 0.003), both negligible effects. Title script/emoji: insufficient n for non-Latin/emoji groups. Brand median ER: Nishat > Khaadi > Sapphire > Limelight > Bonanza > J. > Alkaram > Gul Ahmed.

- MVP approved (owner: "next").
- Phase 9 (actual): language ID accuracy 0.872 (EN P/R 0.91/0.92, RU 0.94/0.82). Sentiment macro-F1 on 250 PROVISIONAL labels: Nemotron-3-Super 0.869, XLM-R twitter 0.819, routed 0.786, RU-XLM-R 0.763, RoBERTa-EN 0.721, VADER 0.602. Nemotron − XLM-R = +0.051, CI [-0.007, +0.116] → not significant. Scored 781 real comments with XLM-R: 382 pos / 255 neu / 144 neg; language EN 448, RU 158, other 146, mixed 24, Urdu script 5. Net sentiment by brand: Alkaram +0.50, Khaadi +0.45, Nishat +0.43, Limelight +0.40, Sapphire +0.19, Gul Ahmed +0.12, J. +0.05 (n=21, wide CI). `uv run pytest` → 83 passed.

- Owner chose sentiment Option A (XLM-R), ADR-017 confirmed.
- Phase 10 (actual, reliable non-promoted n=1,845, rel_er): time bands: Morning 06–12 median 1.20 (CI 1.10–1.31, adj p 0.042, negligible δ 0.08); Evening 16–20 1.04 (adj p 0.030, negligible, below rest); Night n=27, CI 0.95–2.59 (not significant). Weekday: Saturday 0.93 (CI 0.82–1.02, adj p 0.006, small δ −0.15), the only significant day; Kruskal p 0.016. Heatmap highs (descriptive): Wed morning 1.41 (n=66), Mon afternoon 1.38 (n=119); low: Sat afternoon 0.72 (n=54). Brands rarely post at night or on Sat/Sun mornings. Heatmap text overlap + grid artifacts found in a screenshot and fixed. `uv run pytest` → 91 passed.

- Phase 11 (actual): target log(ER), chronological split, train 1,476 (2024-10-18→2026-04-17), test 369 newest (2026-04-17→2026-10-03), 42 pre-publication features. MAE(log): global median 0.609, brand median 0.699, ridge 0.679, gradient boosting 0.682. vs global median: ridge +0.069 [+0.007, +0.137], GB +0.073 [+0.018, +0.126], i.e. models are significantly WORSE than the simplest baseline → prediction DEFERRED. Global median beating brand medians implies brand ER levels drifted over time. `uv run pytest` → 96 passed.

- Phase 12 (actual, real snapshot, reliable non-promoted videos): 11 cards = 1 'Next post' + 10 evidence cards. Next post: wedding/festive video (1.34 [1.18–1.47] vs 1.10 rest, small effect, adj p 0.001) in the morning 06–12 PKT (1.20 vs 1.07, negligible, adj p 0.042); de-prioritise menswear (n=50, small), Saturday (0.93 vs 1.12, small), sale/discount (negligible). Strength labels: 4 modest, 7 weak/negligible. NVIDIA rewrites accepted by the number lock: 4/11 (the rest fell back to templates). `uv run pytest` → 102 passed.

## Blockers
- Review quality gate (owner). Open: owner verification of the 250 draft labels.

## Next action
Owner review → Phase 13 exports + UI polish.
