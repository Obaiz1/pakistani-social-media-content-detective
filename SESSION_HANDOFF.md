# SESSION_HANDOFF — read this first, update it after every step

> **For the next Claude agent:** This file tells you exactly where the last session stopped. Read it, then `CLAUDE.md`, then `REQUIREMENTS_FORM.md` / `DECISIONS.md` / `PROGRESS.md`. **Don't re-ask questions already marked CONFIRMED.** After each meaningful step, update the "Current state", "Last actions", and "Next step" sections below, then commit and push.

**Last updated:** 2026-10-17 (session 1)

---

## Current state
- **Phase:** 1 — Gather and finalize requirements (in progress)
- **Batch A:** ✅ done
- **Batch B:** ✅ done (owner said "use default" for all remaining items)
- **Batch C:** ⏳ asked; waiting for owner answers
- **Batches D, E, F:** not asked yet
- **Code written:** none (by design; coding needs Phase 5 approval)

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
- Windows 11, VS Code + Claude Code, Python 3.14.4, git 2.45, gh CLI logged in as `Obaiz1`.
- Repo-local git identity: `Obaiz1` / `196679709+Obaiz1@users.noreply.github.com` (keeps the owner's personal email off the public repo).
- `.env` (git-ignored) holds `STITCH_API_KEY` (set) and `YOUTUBE_API_KEY` (set, tested 2026-10-17: `channels.list forHandle=@khaadi` returned `UCosHRi7jeBb0JGZfFlOHYUA`, 47.3K subs, 819 videos).
- Stitch MCP registered with `claude mcp add stitch -s local` (stored in `~/.claude.json`). Check it with `claude mcp get stitch`.
- **Before every push**, scan for secrets: `git diff --cached | grep -cE "AQ\.Ab8|AIza"` should print 0.
- No other API keys needed for now. A Claude (Anthropic) API key is only optional, for Phase 12, and only after the owner approves a budget (see ADR-008).
- Communicate with the owner in simple Roman Urdu + English technical terms, 3–5 questions per batch.

## Pending owner actions
- [x] YouTube API key added to `.env` (pasted in chat, then saved by Claude; tested OK).
- [ ] Optional: rotate the Stitch and YouTube keys (both were pasted in chat), and restrict the YouTube key to "YouTube Data API v3" in Google Cloud Console.
- [ ] Answer Batch C (C1–C5).

## Last actions (newest first)
0a. Owner asked for sentiment model options. Gave a candidate list (ARCHITECTURE_BLUEPRINT.md → "Sentiment model candidates"). Waiting on the owner's choice: benchmark approach + who labels the eval set.
0. Saved and tested the YouTube API key; answered the owner's question about other API keys (ADR-008).
1. Created this handoff file; added a "read SESSION_HANDOFF.md first" note to `CLAUDE.md`.
2. Recorded Batch B defaults (B1–B4) and asked Batch C.
3. Hosting set to Streamlit Community Cloud (ADR-007).
4. Created the public GitHub repo and pushed.
5. Saved the Stitch key to `.env` and registered the Stitch MCP.
6. Scaffolded all project docs.

## Next step
1. Record the owner's Batch C answers in `REQUIREMENTS_FORM.md`.
2. Ask Batch D (analytics & AI, Q18–Q24), then E and F.
3. Show the one-page scope summary and get **explicit requirements sign-off** (Phase 1 gate).
4. Phase 2: once the YouTube key exists, verify brand channel IDs and audit the real API fields/quota.
