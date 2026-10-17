# SESSION_HANDOFF — read this first, update it after every step

> **For the next Claude agent:** This file tells you exactly where the last session stopped. Read it, then `CLAUDE.md`, then `REQUIREMENTS_FORM.md` / `DECISIONS.md` / `PROGRESS.md`. **Don't re-ask questions already marked CONFIRMED.** After each meaningful step, update the "Current state", "Last actions", and "Next step" sections below, then commit and push.

**Last updated:** 2026-10-17 (session 1)

---

## Current state
- **Phase:** 14: app DEPLOYED and showing real data at https://pakistani-social-media-content-detective-mahmts48mya2xnxwgttip.streamlit.app (owner confirmed 'chal gya ha'). Remaining: final project report (PDF), final sign-off, owner label verification, rotate the DATA_REPO_TOKEN (it was pasted in chat several times), optional Stitch polish. Owner is now asking for improvement ideas.
- **Batch A:** ✅ done
- **Batch B:** ✅ done (owner said "use default" for all remaining items)
- **Batches C–F:** ✅ filled with documented DEFAULTS. Owner delegated: "abhe procced kro bad mae dekhte" (proceed now, revisit later)
- **Phase 1 gate:** ✅ owner replied "next" to the sign-off request (treated as approval)
- **Code written:** pipeline, analytics, 8-page dashboard (Overview, What to post next, Brands, Content, Posting time, Sentiment, Report & exports, Data & Method), NLP (`src/nlp/{langid,sentiment,benchmark}.py`, `scripts/{draft_labels_v1,run_sentiment_benchmark,score_sentiment}.py`), 109 tests. NLP deps live in the `nlp` group (`--group nlp`). Snapshot `data/processed/2026-10-17/` (comments now have language + sentiment_label; refresh/delete by 2026-11-16). Labels/predictions/LLM cache in `data/labels/` (git-ignored: real comment text).

## ▶ Owner's open requests (2026-10-18)
1. ✅ Mixed-effects regression (ADR-026) · ✅ BERTopic (ADR-027) · ⏳ Thumbnail analysis (scripts/analyze_thumbnails.py --vlm-sample 700; spot-check in docs/evaluation/) · ⏳ Final report (scripts/build_final_report.py → docs/FINAL_REPORT.md/.pdf) + final sign-off.
2. **Stitch UI redesign: do this at the START of a NEW session** (the Stitch MCP was added mid-session 1, so its tools never loaded). First call ToolSearch "stitch" to confirm the tools exist, then design: a custom Streamlit theme (.streamlit/config.toml colours/fonts) + a landing/overview layout; keep the validated chart palette (#2a78d6 / #e34948).
3. Owner chores: rotate DATA_REPO_TOKEN (pasted in chat several times) and update Streamlit Secrets; verify the 250 sentiment labels.

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
- Deployment: secrets in the code repo = YOUTUBE_API_KEY, DATA_REPO_DEPLOY_KEY. Private data repo = Obaiz1/pakistani-smcd-data (deploy key 'refresh-data workflow (write)'). Workflow: .github/workflows/refresh-data.yml (`gh workflow run refresh-data`). Streamlit secrets needed: DATA_REPO="Obaiz1/pakistani-smcd-data", DATA_REPO_TOKEN=<read-only PAT>; optional YOUTUBE_API_KEY, NVIDIA_API_KEY.
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
00000000000000000000. Done 2/5: BERTopic (multilingual MiniLM embeddings, UMAP seed 42, HDBSCAN min 25, reduced to 12 themes; brand names/URLs/hashtags removed; generic words stop-listed). ~21–23% of titles are outliers. Theme vs rel_er: 'festive/luxury/celebrate' 1.34 [1.15–1.48] vs 1.05 rest, small, adj p<0.001 (independently replicates the wedding/festive tag finding); 'flat/pret/sale' 0.84 [0.75–0.92] vs 1.11, small, adj p 0.02. Caveat: topics are not perfectly reproducible run-to-run (outliers 459–502, labels shift) despite the fixed seed. Next: thumbnail analysis, then final report.
0000000000000000000. Owner asked for: final report + sign-off, thumbnail analysis, BERTopic, mixed-effects, Stitch. Done 1/5: Mixed-effects regression (statsmodels 0.15; log ER ~ weekday + time band + length + hashtags + campaign tags + emoji; random intercept brand + month variance component; robustness: OLS brand+month FE HC3). n=1,830, 8 brands, 25 months. After BH correction NO term is significant in both models. Wedding/festive +12% [−3%, +30%] (was +34% one-at-a-time), Saturday −13% [−27%, +4%], menswear −31% [−47%, −9%] adj p 0.10, sale −19% adj p 0.15. Interpretation: one-at-a-time effects are largely explained by season/brand mix. All 4 recommendation cards are now marked 'tentative (not confirmed by the adjusted model)'. 115 tests. Next: BERTopic → thumbnails (Nemotron VL via NVIDIA API) → final report → sign-off. Stitch needs a NEW session (MCP tools not loaded here).
000000000000000000. Deployed on Streamlit Community Cloud (Python 3.14 in Cloud settings; requirements.txt). Debugged HTTP 401: Secrets held a 32-char truncated token (copied from an illustrative '…' line in chat; screenshots also overwrote the clipboard). Fixes shipped: HTTP status + token fingerprint in the banner, token whitespace/quote stripping, failed loads not pinned in session_state. Live link added to README.
00000000000000000. First refresh-data run (manual, 2026-10-17 19:11 UTC): success in 3m27s → private repo has 1 commit with channels/videos/comments.parquet + manifest {snapshot 2026-10-17, 2,190 videos, 763 comments, comment_text_included: false}. Verified with the app's remote loader: 8 brands, no 'text' column, sentiment 380/244/139. (2,190 vs 2,204 locally: the 24-month window moved by hours, plus deletions.) Annotation: actions on Node 20 are deprecated; still works. Streamlit deploy could NOT be automated: no Streamlit Cloud API, and the 'Claude in Chrome' extension isn't connected; the owner deploys via share.streamlit.io.
0000000000000000. Owner chose deployment Option A and the name 'AI Social Media Content Detective'. Built the weekly refresh pipeline (private data repo + deploy key + workflow + remote loader). 110 tests pass.
000000000000000. Phase 13 (actual, 2026-10-18): new page 'Report & exports': Excel workbook (About+caveats, Recommendations, 7 summary sheets), Recommendations CSV, 3-page PDF (cards, 5 median+CI charts drawn with fpdf2 primitives, sentiment, caveats). Only aggregates are exported (tests assert no video_id/title/text columns). Accessibility: chart colors #2a78d6/#e34948 pass the dataviz validator in light+dark (CVD ΔE 21.6, contrast ≥3:1); phone width 390 px renders cleanly. Fixed while reviewing the real PDF: Sentiment page ignored sidebar filters (now filtered like every page; numbers change accordingly), raw campaign keys in PDF, 'AB/TEST' label, 'between on Saturday' wording; fpdf2 multi_cell cursor bug.
00000000000000. Owner asked to fix the weak cards (2026-10-17): findings that are significant but have a NEGLIGIBLE effect (|Cliff's δ| < 0.147) are no longer recommendation cards; they're listed under 'Weak signals: real but too small to act on'. Now 4 actionable cards: Next post = wedding/festive video, any day except Saturday, de-prioritise menswear; plus Try more wedding/festive, Use less menswear, Use less Saturday. 7 weak signals. 109 tests pass.
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
1. Phase 14: (a) README with screenshots (headless-Edge CDP script: scratchpad shot.py pattern) + short GIF; (b) deployment plan for Streamlit Community Cloud: live mode needs YOUTUBE_API_KEY in Streamlit secrets; sentiment needs either precomputed labels or NVIDIA (ADR-017 says local XLM-R; on Cloud torch won't fit, so decide with the owner); (c) final PDF project report; (d) final full test run.
2. Still open for the owner: verify the 250 labels.
3. Pinned channel IDs: Khaadi UCosHRi7jeBb0JGZfFlOHYUA · Sapphire UCvMjM0BkK7SzlYnPTi5CBUQ · Gul Ahmed UCsAIxl3qvpy1DofpwDEx6Ow · J. UC5xbg6lBACA3HBdN8idiQvQ · Alkaram UCG-I5rH3YEFu3VKUAtmxLIg · Bonanza UCDblU9Vxyi7kXxX0uf-cvyg · Nishat UCVQd-OGmpDTnXGfVR8eRrGQ · Limelight UCbvMxYDdZki0P95gCORO8oA
