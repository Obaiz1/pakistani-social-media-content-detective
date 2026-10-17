# SESSION_HANDOFF — read this first, update it after every step

> **For the next Claude agent:** This file tells you exactly where the last session stopped. Read it, then `CLAUDE.md`, then `REQUIREMENTS_FORM.md` / `DECISIONS.md` / `PROGRESS.md`. **Don't re-ask questions already marked CONFIRMED.** After each meaningful step, update the "Current state", "Last actions", and "Next step" sections below, then commit and push.

**Last updated:** 2026-10-17 (session 1)

---

## Current state
- **Phase:** 8 built (S3), waiting on the **Demo/approve MVP** gate (owner). After approval → Phase 9 NLP (F-14..F-17).
- **Batch A:** ✅ done
- **Batch B:** ✅ done (owner said "use default" for all remaining items)
- **Batches C–F:** ✅ filled with documented DEFAULTS. Owner delegated: "abhe procced kro bad mae dekhte" (proceed now, revisit later)
- **Phase 1 gate:** ✅ owner replied "next" to the sign-off request (treated as approval)
- **Code written:** pipeline (`src/` ingestion/processing/validation/pipeline), analytics (`src/analytics/compare.py`), dashboard (`app.py` + `views/{overview,brands,content,method}.py`, `src/ui.py`, `src/app_data.py`), 63 tests. Latest real snapshot: `data/processed/2026-10-17/` (git-ignored; refresh/delete by 2026-11-16). Run: `python -m uv run streamlit run app.py`.

## Key confirmed decisions (details in DECISIONS.md)
| Topic | Decision |
|---|---|
| Project type | Portfolio, individual |
| Deliverable | Streamlit dashboard + modular Python analytics + project report |
| Data source | YouTube Data API v3 only (no scraping; Instagram deferred) |
| Scope | 6–8 Pakistani clothing brands' official YouTube channels |
| Audience label | "Pakistan-related content"; segments show "Unavailable" |
| Hosting | Streamlit Community Cloud (Vercel dropped) |
| Repo | https://github.com/Obaiz1/pakistani-social-media-content-detective (public) |
| Deadline / skill | Delegated to Claude; aim for high quality |
| Main user | Recruiter/portfolio viewer + brand marketing analyst |
| Content types | Shorts vs long videos + campaign tags from title/description |
| Timeframe | Last 24 months |
| Report | PDF report + README screenshots + short demo GIF (no slides) |
| UI design tool | Google Stitch MCP (for mockups in Phase 4/13) |

## Environment facts (not visible in the repo)
- Run everything with `python -m uv run ...` (venv = `.venv`, Python 3.12.15). Windows 11, VS Code + Claude Code, system Python 3.14.4, git 2.45, gh CLI logged in as `Obaiz1`.
- Repo-local git identity: `Obaiz1` / `196679709+Obaiz1@users.noreply.github.com` (keeps the owner's personal email off the public repo).
- `.env` (git-ignored) holds `STITCH_API_KEY` (set) and `YOUTUBE_API_KEY` (set, tested 2026-10-17: `channels.list forHandle=@khaadi` returned `UCosHRi7jeBb0JGZfFlOHYUA`, 47.3K subs, 819 videos).
- Stitch MCP registered with `claude mcp add stitch -s local` (stored in `~/.claude.json`). Check it with `claude mcp get stitch`.
- **Before every commit**, run `bash scripts/check_secrets.sh && git commit ...`. It compares the staged diff against the real `.env` values and exits 1 if anything leaks. (The old regex scan gave false positives.)
- `.env` also has `NVIDIA_API_KEY` + `NVIDIA_API_KEY_2` (same NVIDIA account; tested OK with `nvidia/nemotron-3-super-120b-a12b` at `https://integrate.api.nvidia.com/v1/chat/completions`, OpenAI-compatible). Several catalog models return 404/410 for this account. See ADR-009.
- Project skills in `.claude/skills/`: `data-designer` (use for SYNTHETIC test data), `rag-blueprint` and `deepstream-import-vision-model` (installed but not used in MVP, see ADR-010). No NVIDIA GPU on this laptop; Docker 29.8 is available.
- Claude Haiku is no longer needed (NVIDIA LLM is free).
- Communicate with the owner in simple Roman Urdu + English technical terms, 3–5 questions per batch.

## Pending owner actions
- [x] YouTube API key added to `.env` (pasted in chat, then saved by Claude; tested OK).
- [ ] Optional: rotate the Stitch, YouTube and NVIDIA keys (all were pasted in chat), and restrict the YouTube key to "YouTube Data API v3" in Google Cloud Console.
- [ ] Sign off on Phase 1 requirements (one-page summary).

## Last actions (newest first)
000000000. Phase 8 built: compare.py (median + bootstrap CI, Mann-Whitney + Cliff's δ, BH, Kruskal, n≥20), 4 dashboard pages, data-source priority (fresh snapshot → live API with 24 h cache → SYNTHETIC with banner). Found + fixed: Bonanza null ER (ADR-015), Plotly row order, deprecated use_container_width. Screenshots via a headless-Edge CDP script (scratchpad/shot.py; restart Streamlit after src/ edits). Preliminary real-data findings (snapshot 2026-10-17; reliable, non-promoted videos n=1,845; metric rel_er; BH-adjusted): Wedding/festive median 1.34 (CI 1.21–1.48, adj p 0.001, small effect δ≈0.16), the only campaign clearly above typical. Sale/discount 0.94 (adj p 0.015) and untagged 1.00 (adj p 0.002) are below the rest. 0–15 s videos 1.05 vs the rest (adj p 0.006, negligible effect). 0 hashtags 1.22 (adj p 0.002) vs 6+ hashtags 1.03 (adj p 0.003), both negligible effects. Title script/emoji: insufficient n for non-Latin/emoji groups. Brand median ER: Nishat > Khaadi > Sapphire > Limelight > Bonanza > J. > Alkaram > Gul Ahmed.
00000000. Phase 7 real run 2026-10-17 (actual): `uv run python scripts/collect.py` → exit 0, channels=8, videos=2,204, comments=781 from 444 videos, quota=655 units. Per-brand video counts match the Phase 2 audit exactly (0.0% diff; Nishat=615 confirms full paging). 0 duplicate videos/comments, 0 author columns, 0 hidden likes. Duration buckets: 0-15s 728, 16-30s 939, 31-60s 444, 61-180s 88, >180s 5. likely_promoted=242 (11%). low_reliability=131. Comment scripts: latin 654, emoji/none 122, **Urdu script only 5** (Urdu-script sentiment benchmark n will be tiny). 781 < ~888 audit commentCount because commentCount includes replies; we fetch top-level only. First run crashed on `RemoteDisconnected`; fixed: client retries network errors (tests added).
0000000. Owner said "next", treated as Authorize coding. Phase 6 done: installed uv 0.13.1 (`python -m pip install --user uv`; call it as `python -m uv`, since `uv` isn't on PATH), Python 3.12.15 via uv, `uv sync`, generated the SYNTHETIC fixture (8 fictional brands, 357 videos, 239 comments), `uv run pytest` → 5 passed, Streamlit headless health check ok.
000000. Owner said "next", treated as approval of Phase 3/4 + the uv/3.12 default. Wrote the Phase 5 backlog (F-01..F-26 with acceptance tests) and sprint plan S1–S7.
00000. Owner said "next", treated as approval of P1–P5. Wrote the Phase 3 options doc and the full Phase 4 architecture draft (modules, schema, metrics incl. rel_er/likely_promoted, stats rules, NLP benchmark, recommendation cards, live-collect + 24 h cache deployment for the 30-day policy).
0000. Ran the Phase 2 audit (~1,035 quota units). Found: J. search result was a fan channel (official = @jjunaidjamshedpk, UC5xbg6lBACA3HBdN8idiQvQ); ~99% of videos ≤180 s; only ~896 comments total (~20% of videos have any); ad-boosted views likely. Wrote docs/DATA_AUDIT.md with proposals P1–P5.
000. Saved + tested 2 NVIDIA API keys; installed 3 NVIDIA skills; recorded ADR-009/010. Phase 1 sign-off still pending.
00. Owner delegated the pending choices. Filled Batches C–F with defaults, wrote the one-page scope summary, and asked for Phase 1 sign-off.
0a. Owner asked for sentiment model options. Gave a candidate list (ARCHITECTURE_BLUEPRINT.md → "Sentiment model candidates"). Waiting on the owner's choice: benchmark approach + who labels the eval set.
0. Saved and tested the YouTube API key; answered the owner's question about other API keys (ADR-008).
1. Created this handoff file; added a "read SESSION_HANDOFF.md first" note to `CLAUDE.md`.
2. Recorded Batch B defaults (B1–B4) and asked Batch C.
3. Hosting set to Streamlit Community Cloud (ADR-007).
4. Created the public GitHub repo and pushed.
5. Saved the Stitch key to `.env` and registered the Stitch MCP.
6. Scaffolded all project docs.

## Next step
1. Owner reviews the MVP demo (`python -m uv run streamlit run app.py`) → approve or request changes.
2. Phase 9: F-14 language ID, F-15 labeled set (~250 comments; Claude drafts, owner verifies; keep comment text out of git), F-16 sentiment benchmark (HF + VADER + NVIDIA Nemotron), F-17 sentiment page. Note: only 5 Urdu-script comments exist.
3. Pinned channel IDs: Khaadi UCosHRi7jeBb0JGZfFlOHYUA · Sapphire UCvMjM0BkK7SzlYnPTi5CBUQ · Gul Ahmed UCsAIxl3qvpy1DofpwDEx6Ow · J. UC5xbg6lBACA3HBdN8idiQvQ · Alkaram UCG-I5rH3YEFu3VKUAtmxLIg · Bonanza UCDblU9Vxyi7kXxX0uf-cvyg · Nishat UCVQd-OGmpDTnXGfVR8eRrGQ · Limelight UCbvMxYDdZki0P95gCORO8oA
