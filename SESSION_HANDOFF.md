# SESSION_HANDOFF — read this first, update it after every step

> **For the next Claude agent:** This file tells you exactly where the last session stopped. Read it, then `CLAUDE.md`, then `REQUIREMENTS_FORM.md` / `DECISIONS.md` / `PROGRESS.md`. **Don't re-ask questions already marked CONFIRMED.** After each meaningful step, update the "Current state", "Last actions", and "Next step" sections below, then commit and push.

**Last updated:** 2026-10-17 (session 1)

---

## Current state
- **Phase:** 12 built, waiting on the owner's **Review quality** gate (page 'What to post next'). After approval → Phase 13 (exports CSV/Excel/PDF, Stitch UI polish, accessibility).
- **Batch A:** ✅ done
- **Batch B:** ✅ done (owner said "use default" for all remaining items)
- **Batches C–F:** ✅ filled with documented DEFAULTS. Owner delegated: "abhe procced kro bad mae dekhte" (proceed now, revisit later)
- **Phase 1 gate:** ✅ owner replied "next" to the sign-off request (treated as approval)
- **Code written:** pipeline, analytics, 7-page dashboard (Overview, What to post next, Brands, Content, Posting time, Sentiment, Data & Method), NLP (`src/nlp/{langid,sentiment,benchmark}.py`, `scripts/{draft_labels_v1,run_sentiment_benchmark,score_sentiment}.py`), 102 tests. NLP deps live in the `nlp` group (`--group nlp`). Snapshot `data/processed/2026-10-17/` (comments now have language + sentiment_label; refresh/delete by 2026-11-16). Labels/predictions/LLM cache in `data/labels/` (git-ignored: real comment text).

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
0000000000000. Phase 12 (actual, real snapshot, reliable non-promoted videos): 11 cards = 1 'Next post' + 10 evidence cards. Next post: wedding/festive video (1.34 [1.18–1.47] vs 1.10 rest, small effect, adj p 0.001) in the morning 06–12 PKT (1.20 vs 1.07, negligible, adj p 0.042); de-prioritise menswear (n=50, small), Saturday (0.93 vs 1.12, small), sale/discount (negligible). Strength labels: 4 modest, 7 weak/negligible. NVIDIA rewrites accepted by the number lock: 4/11 (the rest fell back to templates). Fixed during review: cards compared to 1.0 (misleading 'use less' at +3%) → now vs other videos' median; awkward wording; number lock compared strings (06 vs 6) → now values.
000000000000. Phase 11 (actual): target log(ER), chronological split, train 1,476 (2024-10-18→2026-04-17), test 369 newest (2026-04-17→2026-10-03), 42 pre-publication features. MAE(log): global median 0.609, brand median 0.699, ridge 0.679, gradient boosting 0.682. vs global median: ridge +0.069 [+0.007, +0.137], GB +0.073 [+0.018, +0.126], i.e. models are significantly WORSE than the simplest baseline → prediction DEFERRED. Global median beating brand medians implies brand ER levels drifted over time. scikit-learn moved to main deps. Fixed my own weak test (baseline-uses-train-only) and a biased verdict (it only compared against the weaker baseline).
00000000000. Owner chose sentiment Option A (XLM-R). Phase 10 (actual, reliable non-promoted n=1,845, rel_er): time bands: Morning 06–12 median 1.20 (CI 1.10–1.31, adj p 0.042, negligible δ 0.08); Evening 16–20 1.04 (adj p 0.030, negligible, below rest); Night n=27, CI 0.95–2.59 (not significant). Weekday: Saturday 0.93 (CI 0.82–1.02, adj p 0.006, small δ −0.15), the only significant day; Kruskal p 0.016. Heatmap highs (descriptive): Wed morning 1.41 (n=66), Mon afternoon 1.38 (n=119); low: Sat afternoon 0.72 (n=54). Brands rarely post at night or on Sat/Sun mornings.
0000000000. Phase 9 (actual): language ID accuracy 0.872 (EN P/R 0.91/0.92, RU 0.94/0.82). Sentiment macro-F1 on 250 PROVISIONAL labels: Nemotron-3-Super 0.869, XLM-R twitter 0.819, routed 0.786, RU-XLM-R 0.763, RoBERTa-EN 0.721, VADER 0.602. Nemotron − XLM-R = +0.051, CI [-0.007, +0.116] → not significant. Scored 781 real comments with XLM-R: 382 pos / 255 neu / 144 neg; language EN 448, RU 158, other 146, mixed 24, Urdu script 5. Net sentiment by brand: Alkaram +0.50, Khaadi +0.45, Nishat +0.43, Limelight +0.40, Sapphire +0.19, Gul Ahmed +0.12, J. +0.05 (n=21, wide CI). Bugs fixed: NVIDIA client didn't retry ReadTimeout; benchmark tests skip without sklearn.
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
1. Owner reviews the 'What to post next' page → approve/changes.
2. Phase 13: F-22 exports (filtered CSV + Excel; PDF report with charts + caveats), F-23 Stitch mockups (Stitch MCP tools load in a NEW session) + accessibility check.
2. Still open for the owner: verify the 250 labels.
3. Pinned channel IDs: Khaadi UCosHRi7jeBb0JGZfFlOHYUA · Sapphire UCvMjM0BkK7SzlYnPTi5CBUQ · Gul Ahmed UCsAIxl3qvpy1DofpwDEx6Ow · J. UC5xbg6lBACA3HBdN8idiQvQ · Alkaram UCG-I5rH3YEFu3VKUAtmxLIg · Bonanza UCDblU9Vxyi7kXxX0uf-cvyg · Nishat UCVQd-OGmpDTnXGfVR8eRrGQ · Limelight UCbvMxYDdZki0P95gCORO8oA
