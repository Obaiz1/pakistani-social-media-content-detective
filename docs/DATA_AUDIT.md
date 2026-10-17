# DATA_AUDIT — Phase 2 Feasibility & Responsible Data Audit

**Status:** Phase 2 | Completed audit, **awaiting data-scope approval (gate)**
**Run date:** 2026-10-17 · **Window:** last 24 months (published ≥ 2024-10-18 UTC)
**Method:** throwaway script (scratchpad, not app code) using YouTube Data API v3 with the owner's key. Quota used: **~1,035 units** of the 10,000/day limit.
**Privacy:** Only aggregate counts are shown here. No comment text and no commenter identities were stored in the repo.

## 1. Authorized source matrix

| Source | Access | Status | Notes |
|---|---|---|---|
| YouTube Data API v3 (public data) | API key | ✅ Working | channels, playlistItems, videos, commentThreads all respond |
| YouTube Analytics API (audience country/age) | Channel-owner OAuth only | ❌ Not available | Confirms "Unavailable" for audience segments |
| Instagram Business Discovery | Not set up | ⏸️ Deferred | ADR-006 |
| NVIDIA API Catalog (LLM) | API key | ✅ Working | ADR-009 |

## 2. Channel resolution (search → choose by legitimacy)

| Brand | Channel used | Handle | Subscribers | Total videos | Videos in 24 m | Note |
|---|---|---|---|---|---|---|
| Khaadi | Khaadi | @khaadi | 47.3K | 819 | 194 | |
| Sapphire | SAPPHIRE Pakistan | @sapphirepakistan | 67.0K | 2,505 | 562 | |
| Gul Ahmed | Gul Ahmed | @gulahmedofficial | 51.8K | 698 | 328 | Channel country not set |
| J. (Junaid Jamshed) | **J. Junaid Jamshed** | @jjunaidjamshedpk | 16.9K | 343 | 150 | ⚠️ The search's top result "I Love Junaid Jamshed" (66.7K) is a **fan channel**, so it was rejected |
| Alkaram | Alkaram | @officialalkaram | 39.1K | 703 | 115 | "Alkaram Studio" alternates are tiny/unofficial |
| Bonanza Satrangi | Bonanza Satrangi | @bonanza-satrangi | 45.3K | 232 | 109 | Comments disabled on 107/109 videos |
| Nishat Linen | Nishat | @nishatlinenofficial | 62.5K | 2,100 | 500–615 | Count differs between runs (paging stop rule; see §5) |
| Limelight | Limelight Official | @limelightofficial | 259K | 459 | 131 | |

**Total in the window: ~2,190–2,300 videos across 8 brands.** That's enough sample size for brand/time/format analysis.

**Lesson:** channel identity has to be pinned by **channel ID in config**, not resolved through search at runtime.

## 3. Field availability (actual)

| Field | Availability | Implication |
|---|---|---|
| views, likes, comments | Present for almost all | J. fan channel had 64 hidden likes, but it's excluded now. Hidden like counts must stay null |
| duration | Present | **~99% of videos are ≤ 180 s** (most ≤ 60 s) |
| tags | Sparse: Khaadi 1/194, Gul Ahmed 0/328, Bonanza 6/109 | Use **title/description hashtags** instead of `tags` |
| title, description, publishedAt | Present | Fine for keywords, campaign tags, PKT timing |
| shares, saves, reach, impressions | Not in the API | As expected |
| channel country | 2 of 8 unset | Doesn't prove audience location either way |

## 4. Comments (the big constraint)

| Brand | Total comments (24 m) | Videos with ≥ 1 comment |
|---|---|---|
| Khaadi | 60 | 42 / 194 |
| Sapphire | 276 | 130 / 562 |
| Gul Ahmed | 138 | 68 / 328 |
| J. (official) | 28 | 19 / 150 |
| Alkaram | 89 | 31 / 115 |
| Bonanza | 8 | 2 / 109 |
| Nishat | 210 | 107 / 500 |
| Limelight | 87 | 36 / 131 |
| **Total** | **~896** | **~435 of ~2,190 (≈ 20%)** |

Sample script mix (top-3 videos per brand, 82 comments): mostly Latin script (English/Roman Urdu), a few Urdu-script comments, plenty of emoji-only ones.

**Implication:** About 80% of videos have zero comments, so **per-video comment sentiment vs engagement isn't feasible**. Sentiment can only be credible at the **brand / campaign / month level**, and there are just enough comments (~900) for a **~250-comment hand-labeled benchmark**.

## 5. Measurement risks found

1. **Ad-boosted views (major).** Views vs likes are wildly inconsistent: Alkaram ≈ 89.2M views but 13.8K likes; Nishat ≈ 210M views; Gul Ahmed ≈ 47M. That pattern strongly suggests **paid YouTube ads** count toward views. The API can't separate organic from paid views, so `(likes+comments)/views` will look tiny and get distorted for promoted videos. Mitigation: robust stats (medians, log scale), a "likely promoted" outlier flag (views far above the brand's typical likes ratio), and likes-based metrics shown alongside view-based ER. **This caveat has to be stated in the report.**
2. **Format comparison.** Nearly every video is short-form, so the planned "Shorts vs long video" comparison has almost no long-form sample. The API also has **no Shorts flag**; duration ≤ 180 s is only a proxy.
3. **Paging rule.** The audit stopped paging early on the first older item, which caused the Nishat count mismatch. The real collector must page the full uploads playlist and filter by date.
4. **Brand size differences.** Limelight has 259K subs vs J.'s 16.9K, so normalize per-subscriber where relevant.
5. **Data retention policy.** The YouTube API Services Developer Policies generally require stored API data to be **refreshed or deleted within 30 days** (exact statistics exemptions not verified from the primary text). Plan: the collector re-runs periodically, each snapshot is dated, raw data stays out of git, and the deployed app holds only data refreshed within 30 days (design gets decided in Phase 4).

## 6. Proposed data-scope changes (need approval)

| # | Original requirement | Proposed change | Reason |
|---|---|---|---|
| P1 | Shorts vs long videos (B4) | **Duration buckets** (≤15 s, 16–30, 31–60, 61–180, >180) + title features (hashtag count, emoji, title language, campaign tag) | ~99% short-form |
| P2 | Comment sentiment per video (D3) | Sentiment at **brand / campaign / month** level only, plus the ~250-comment labeled benchmark. Video-level sentiment is "Unavailable" when n is too small | Only ~20% of videos have comments |
| P3 | ER = (likes+comments)/views (C2) | Keep, **plus** likes/views with outlier "likely promoted" flag; medians and log scales by default | Ad-boosted view inflation |
| P4 | J. via search | Pin all 8 channels by ID (table §2) | Search returned a fan channel |
| P5 | Bonanza in sentiment | Include in engagement; **exclude from sentiment** (8 comments) | Comments disabled |

## Sources
- [YouTube API Services — Developer Policies](https://developers.google.com/youtube/terms/developer-policies)
- [Complying with YouTube's Developer Policies](https://developers.google.com/youtube/terms/developer-policies-guide)
