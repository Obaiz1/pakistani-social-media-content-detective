# DECISIONS (Architecture Decision Records)

| ID | Date | Decision | Status | Reasoning | Rejected options |
|---|---|---|---|---|---|
| ADR-000 | 2026-10-17 | Use `CLAUDE_PROJECT_MASTER_PROMPT.md` as `CLAUDE.md` operating instructions | CONFIRMED | Owner provided the prompt to start the project | — |
| ADR-001 | 2026-10-17 | Deliverable = Streamlit dashboard + modular Python analytics + project report | CONFIRMED | Owner accepted the recommended default; it makes a strong portfolio demo | Notebook-only; full-stack web app |
| ADR-002 | 2026-10-17 | Data comes from official APIs (YouTube Data API v3 primary, Meta Business Discovery optional), **not web scraping** | PROPOSED (awaiting owner acknowledgment) | Scraping Instagram/Facebook/YouTube violates platform ToS and the CLAUDE.md §2 rules, and it's a risk for a public portfolio. The YouTube API provides public views, likes, comments, titles, descriptions, tags, and publish times for any public channel, all free within quota | Web scraping (owner's initial suggestion) |
| ADR-003 | 2026-10-17 | Label scope as "Pakistan-related content"; no verified-audience claims | PROPOSED | Public API data doesn't include audience country for channels we don't own | Inferring audience nationality from language/hashtags |
| ADR-005 | 2026-10-17 | Use the Google Stitch MCP server for UI/dashboard design mockups | CONFIRMED (tool connected; how it's used gets decided in Phase 4/13) | Owner provided a Stitch API key and asked to use it. Key is stored in git-ignored `.env` and in Claude Code's local-scope MCP config (`~/.claude.json`), never in the repo | — |
| ADR-004 | 2026-10-17 | Initialize a local git repo now; create the GitHub remote after the owner confirms name/visibility | CONFIRMED (remote pending) | The owner asked for GitHub hosting; publishing a repo is outward-facing, so name/visibility are confirmed first | — |
