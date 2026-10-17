# AI Social Media Content Detective: Final Project Report

**Question:** What YouTube content gets Pakistani clothing-brand audiences to engage?  
**Data snapshot:** 2026-10-17 · **Report generated:** 2026-10-18  
**Live app:** https://pakistani-social-media-content-detective-mahmts48mya2xnxwgttip.streamlit.app  
**Code:** https://github.com/Obaiz1/pakistani-social-media-content-detective

## 1. Executive summary

- Collected **2,204 videos** (last 24 months) and **781 comments** from **8 official Pakistani clothing-brand channels** through the YouTube Data API v3 (no scraping).
- After removing low-reliability videos (131) and likely ad-boosted videos (242), **1,845 videos** were analysed.
- **One-at-a-time comparisons** suggested that wedding/festive content performs better and that Saturday uploads, menswear and sale content perform worse than the same brand's other videos (small effects).
- **A mixed-effects model** controlling for brand, month and all features together found that **0 of 26 effects** stay significant after multiple-comparison correction. Most one-at-a-time differences are largely explained by **season and brand mix**, so every recommendation is labelled *tentative*.
- **Data-driven title themes (BERTopic)** independently found a festive/luxury theme with the highest relative engagement (festive / luxury / celebrate: 1.34 vs 1.05).
- **Sentiment:** the multilingual XLM-R model (macro-F1 0.82) was chosen over the best LLM (0.87) because the difference was not significant.
- **Engagement prediction** before publishing did **not** beat a simple median baseline, so it was deferred.

## 2. Data and compliance

- Source: YouTube Data API v3, public data only. Channels pinned by ID (a search had returned a fan channel).
- Comment authors are never stored; comment text never leaves the owner's machine (published data has labels only).
- Stored API data is refreshed weekly by a GitHub Action and kept as a single latest snapshot (< 30 days).
- Not available from the API: shares, saves, reach, impressions, audience demographics.

## 3. Methods

- **Engagement rate (ER)** = (likes + comments) ÷ views; likes ÷ views where comments are disabled; null if likes are hidden.
- **Relative engagement** = ER ÷ the brand's median ER, which removes brand-size differences.
- **Likely promoted** = like-rate < brand median ÷ 5 and views above the brand's 75th percentile (excluded).
- **Statistics:** medians with 2,000-sample bootstrap 95% CIs; Mann-Whitney U vs all other videos; Cliff's δ effect size; Benjamini-Hochberg correction; groups with n < 20 not tested.
- **Adjusted model:** log(ER) ~ weekday + PKT time band + length + hashtags + campaign tags + emoji, random intercept per brand + month variance component (statsmodels MixedLM); robustness check with brand + month fixed effects (HC3).
- **NLP:** rule-based language ID; 6 sentiment approaches benchmarked on 250 hand-labelled real comments.
- **Topics:** BERTopic on titles (multilingual MiniLM embeddings, UMAP, HDBSCAN, reduced to 12 themes).
- **Thumbnails:** colour statistics for every video; vision-LLM labels (NVIDIA Nemotron) for a random sample, spot-checked against manual labels.
- **Prediction:** chronological split (newest 20% as test), pre-publication features only, two baselines.

## 4. Results

### 4.1 Engagement by brand (median ER, 95% CI)

- Nishat Linen: median 1.71% [1.57%, 1.83%], n = 459, medium effect, adj. p = 0.000
- Khaadi: median 1.49% [1.39%, 1.67%], n = 185, small effect, adj. p = 0.000
- Sapphire: median 1.32% [1.26%, 1.39%], n = 521, negligible effect, adj. p = 0.000
- Limelight: median 1.22% [1.07%, 1.32%], n = 116, negligible effect, adj. p = 0.426
- Bonanza Satrangi: median 0.85% [0.72%, 1.02%], n = 82, small effect, adj. p = 0.000
- J. (Junaid Jamshed): median 0.83% [0.58%, 1.18%], n = 118, small effect, adj. p = 0.000
- Alkaram: median 0.62% [0.52%, 0.93%], n = 86, medium effect, adj. p = 0.000
- Gul Ahmed: median 0.30% [0.23%, 0.46%], n = 278, large effect, adj. p = 0.000

### 4.2 Content and timing (relative engagement, one feature at a time)

**Campaign**

- wedding/festive: median 1.34 [1.18, 1.47], n = 238, small effect, adj. p = 0.001
- Independence (Azadi): median 1.27 [0.89, 1.83], n = 23, negligible effect, adj. p = 0.896
- new-arrival: median 1.24 [1.08, 1.36], n = 251, negligible effect, adj. p = 0.387
- Ramadan: median 1.24 [1.01, 1.46], n = 35, negligible effect, adj. p = 0.706
- winter: median 1.22 [1.09, 1.34], n = 287, negligible effect, adj. p = 0.449
- Eid: median 1.18 [1.07, 1.28], n = 281, negligible effect, adj. p = 0.298
- lawn/summer: median 1.10 [1.03, 1.18], n = 481, negligible effect, adj. p = 0.896
- menswear: median 1.03 [0.62, 1.24], n = 50, small effect, adj. p = 0.045
- no campaign theme: median 1.01 [0.95, 1.09], n = 499, negligible effect, adj. p = 0.007
- sale/discount: median 0.94 [0.87, 1.10], n = 179, negligible effect, adj. p = 0.007
- kids: median 0.37 (n < 20, not tested), n = 2

**Video length**

- 0-15s: median 1.05 [0.98, 1.12], n = 589, negligible effect, adj. p = 0.010
- 16-30s: median 1.11 [1.05, 1.18], n = 834, negligible effect, adj. p = 0.078
- 31-60s: median 1.18 [1.09, 1.28], n = 355, negligible effect, adj. p = 0.404
- 61-180s: median 1.01 [0.78, 1.75], n = 63, negligible effect, adj. p = 0.932
- >180s: median 1.17 (n < 20, not tested), n = 4

**PKT time band**

- Night (00–06): median 1.65 [0.95, 2.59], n = 27, small effect, adj. p = 0.111
- Morning (06–12): median 1.20 [1.10, 1.31], n = 360, negligible effect, adj. p = 0.042
- Afternoon (12–16): median 1.12 [1.03, 1.23], n = 556, negligible effect, adj. p = 0.465
- Evening (16–20): median 1.04 [1.00, 1.10], n = 578, negligible effect, adj. p = 0.030
- Prime time (20–24): median 1.07 [1.01, 1.20], n = 324, negligible effect, adj. p = 0.465

**Weekday**

- Monday: median 1.17 [1.03, 1.30], n = 349, negligible effect, adj. p = 0.437
- Tuesday: median 1.15 [1.09, 1.25], n = 306, negligible effect, adj. p = 0.437
- Wednesday: median 1.13 [1.02, 1.26], n = 272, negligible effect, adj. p = 0.437
- Thursday: median 1.05 [0.97, 1.17], n = 355, negligible effect, adj. p = 0.437
- Friday: median 1.10 [1.04, 1.24], n = 276, negligible effect, adj. p = 0.437
- Saturday: median 0.93 [0.82, 1.02], n = 183, small effect, adj. p = 0.006
- Sunday: median 1.03 [0.94, 1.18], n = 104, negligible effect, adj. p = 0.437

### 4.3 Adjusted effects (mixed-effects model)

n = 1,830 videos, 8 brands, 25 months. % change in ER vs the reference level, with 95% CI and BH-adjusted p:

- Campaign: independence: +25% [-24%, +105%], adj. p = 0.64
- Emoji in title: +24% [-25%, +105%], adj. p = 0.64
- Weekday: Wednesday (vs Monday): +22% [+5%, +42%], adj. p = 0.10
- Campaign: lawn/summer: +19% [+4%, +37%], adj. p = 0.10
- Weekday: Sunday (vs Monday): +14% [-8%, +41%], adj. p = 0.44
- Weekday: Friday (vs Monday): +14% [-2%, +33%], adj. p = 0.39
- Campaign: eid: +14% [-4%, +35%], adj. p = 0.39
- Campaign: wedding/festive: +12% [-3%, +30%], adj. p = 0.39
- Time band: Morning (06–12) (vs Afternoon (12–16)): +12% [-2%, +28%], adj. p = 0.39
- Weekday: Tuesday (vs Monday): +11% [-4%, +29%], adj. p = 0.41
- Campaign: new/arrivals: +10% [-5%, +27%], adj. p = 0.44
- Hashtags: 1-2 (vs 0): +6% [-30%, +63%], adj. p = 0.87
- Hashtags: 3-5 (vs 0): +4% [-13%, +25%], adj. p = 0.83
- Time band: Prime time (20–24) (vs Afternoon (12–16)): +4% [-11%, +21%], adj. p = 0.83
- Campaign: winter: +4% [-13%, +24%], adj. p = 0.83
- Time band: Night (00–06) (vs Afternoon (12–16)): +4% [-28%, +50%], adj. p = 0.89
- Weekday: Thursday (vs Monday): +2% [-12%, +18%], adj. p = 0.87
- Length: 31-60s (vs 16-30s): -1% [-13%, +13%], adj. p = 0.92
- Hashtags: 6+ (vs 0): -2% [-20%, +21%], adj. p = 0.89
- Length: 0-15s (vs 16-30s): -6% [-15%, +5%], adj. p = 0.55
- Time band: Evening (16–20) (vs Afternoon (12–16)): -8% [-19%, +4%], adj. p = 0.44
- Length: 61-180s (vs 16-30s): -8% [-29%, +18%], adj. p = 0.72
- Campaign: ramadan: -12% [-38%, +26%], adj. p = 0.72
- Weekday: Saturday (vs Monday): -13% [-27%, +4%], adj. p = 0.39
- Campaign: sale: -19% [-33%, -3%], adj. p = 0.15
- Campaign: men: -31% [-47%, -9%], adj. p = 0.10

### 4.4 Title themes (BERTopic)

459 videos had no clear theme (outliers, excluded).

- festive / luxury / celebrate: median 1.34 [1.15, 1.48], n = 264, small effect, adj. p = 0.000
- unstitched / summer: median 1.25 [0.83, 1.59], n = 47, negligible effect, adj. p = 0.892
- intermix / unstitched: median 1.21 [0.88, 1.28], n = 26, negligible effect, adj. p = 0.892
- sale / mothers / tribute: median 1.20 [1.01, 1.55], n = 129, negligible effect, adj. p = 0.677
- signature / premium / elegance: median 1.16 [1.02, 1.31], n = 53, negligible effect, adj. p = 0.892
- west / azadi / eid: median 1.12 [0.86, 1.33], n = 113, negligible effect, adj. p = 0.892
- lawn / spring / summer: median 1.09 [0.97, 1.22], n = 237, negligible effect, adj. p = 0.892
- winter / fall / unstitched: median 1.08 [0.95, 1.22], n = 171, negligible effect, adj. p = 0.706
- ready / eid / bloom: median 1.02 [0.97, 1.11], n = 259, negligible effect, adj. p = 0.131
- eid / pret / buy: median 0.91 [0.80, 1.15], n = 68, small effect, adj. p = 0.099
- centre / city / experience: median 0.90 [0.74, 1.31], n = 25, small effect, adj. p = 0.496
- flat / pret / sale: median 0.84 [0.75, 0.92], n = 62, small effect, adj. p = 0.020

### 4.6 Comment sentiment

Overall: 49% positive, 33% neutral, 18% negative. Net sentiment (share positive − share negative) by brand:

- Alkaram: +0.50 [+0.33, +0.65], n = 82
- Khaadi: +0.45 [+0.26, +0.62], n = 53
- Nishat Linen: +0.43 [+0.34, +0.54], n = 196
- Limelight: +0.40 [+0.24, +0.56], n = 70
- Sapphire: +0.19 [+0.09, +0.29], n = 243
- Gul Ahmed: +0.12 [-0.03, +0.26], n = 116
- J. (Junaid Jamshed): +0.05 [-0.29, +0.38], n = 21

### 4.7 Sentiment model benchmark (macro-F1, n = 250)

- nvidia:nvidia/nemotron-3-super-120b-a12b: 0.869
- cardiffnlp/twitter-xlm-roberta-base-sentiment: 0.819
- routed: EN→cardiff-roberta, RU/mixed→roman-urdu-xlmr: 0.786
- Khubaib01/roman-urdu-sentiment-xlm-r: 0.763
- cardiffnlp/twitter-roberta-base-sentiment-latest: 0.721
- vader: 0.602

Label status: PROVISIONAL: labels are Claude drafts, not yet verified by the owner.

### 4.8 Engagement prediction

- baseline: global median: MAE(log) 0.609
- baseline: brand median: MAE(log) 0.699
- ridge: MAE(log) 0.679
- gradient boosting: MAE(log) 0.682

No model beat the stronger baseline, so prediction was deferred.

## 5. Recommendations (to A/B test, not guarantees)

**Next post to test** [tentative (not confirmed by the adjusted model), n = 238]  
What: A wedding/festive video. De-prioritise: menswear content. When: Any day except Saturday (PKT); no reliable best-time signal.  
Evidence: Wedding/festive content: median relative engagement 1.34 (95% CI 1.18–1.47) vs 1.10 for all other videos (1.00 = a brand's typical video). Cliff's δ +0.15 (small effect), BH-adjusted p = 0.001.  
Adjusted check: Campaign: wedding/festive: +12% (95% CI -3% to +30%), BH-adjusted p = 0.39 → NOT confirmed after adjusting for brand, month and other features.   
Test: Run it as a 4-week A/B: half of comparable uploads follow this plan, half follow the usual plan; compare median engagement after 14 days per video (≥ 20 videos per arm).

**Use less: menswear content** [tentative (not confirmed by the adjusted model), n = 50]  
What: De-prioritise menswear content; test alternatives. When: Keep your usual schedule (see the timing cards).  
Evidence: Menswear content: median relative engagement 1.03 (95% CI 0.62–1.24) vs 1.13 for all other videos (1.00 = a brand's typical video). Cliff's δ -0.19 (small effect), BH-adjusted p = 0.045.  
Adjusted check: Campaign: men: -31% (95% CI -47% to -9%), BH-adjusted p = 0.10 → NOT confirmed after adjusting for brand, month and other features.   
Test: Publish 10–20 menswear content and 10–20 otherwise-similar videos in the same weeks and time slots. Compare median engagement (likes + comments ÷ views) after 14 days; keep ad spend equal or exclude boosted posts.

**Try more: wedding/festive content** [tentative (not confirmed by the adjusted model), n = 238]  
What: Test more wedding/festive content. When: Keep your usual schedule (see the timing cards).  
Evidence: Wedding/festive content: median relative engagement 1.34 (95% CI 1.18–1.47) vs 1.10 for all other videos (1.00 = a brand's typical video). Cliff's δ +0.15 (small effect), BH-adjusted p = 0.001.  
Adjusted check: Campaign: wedding/festive: +12% (95% CI -3% to +30%), BH-adjusted p = 0.39 → NOT confirmed after adjusting for brand, month and other features.   
Test: Publish 10–20 wedding/festive content and 10–20 otherwise-similar videos in the same weeks and time slots. Compare median engagement (likes + comments ÷ views) after 14 days; keep ad spend equal or exclude boosted posts.

**Use less: posting on Saturday** [tentative (not confirmed by the adjusted model), n = 183]  
What: Move some uploads away from Saturday. When: Avoid Saturday (PKT) until tested.  
Evidence: Posting on Saturday: median relative engagement 0.93 (95% CI 0.82–1.02) vs 1.12 for all other videos (1.00 = a brand's typical video). Cliff's δ -0.15 (small effect), BH-adjusted p = 0.006.  
Adjusted check: Weekday: Saturday (vs Monday): -13% (95% CI -27% to +4%), BH-adjusted p = 0.39 → NOT confirmed after adjusting for brand, month and other features.   
Test: For 4 weeks, alternate comparable videos between Saturday and your usual slot (same campaign, length and hashtags). Compare median engagement after 14 days per video; aim for at least 20 videos per arm.

## 6. Limitations

- Pakistan-related brand content: the audience is not verified as Pakistani (no audience-location data in the API).
- Correlation, not causation: posting choices and outcomes share hidden causes (budget, season, product).
- View counts can include paid ads; 'likely promoted' videos are excluded by default (heuristic flag).
- Groups with n < 20 are not tested. Effect sizes are mostly small or negligible.
- Public YouTube metrics only: shares, saves, reach and impressions are not available.
- Only 5 Urdu-script comments: Urdu-script sentiment could not be evaluated.
- BERTopic themes vary slightly between runs; vision labels for text overlay/close-up are low-agreement.

## 7. Engineering

- Modular Python package (`src/`), Streamlit dashboard (10 pages), 77 automated tests, 28 architecture decision records.
- Weekly GitHub Action → private data repo (deploy key) → Streamlit Community Cloud (read-only token).
- Secrets only in `.env` / Streamlit secrets; a pre-commit check blocks any secret value from git.

## 8. Process

Built in 15 gated phases (problem framing → requirements → data audit → architecture → foundation → pipeline → analytics MVP → NLP → timing → ML → recommendations → dashboard & exports → delivery), with the project owner approving every gate. Full history: `DECISIONS.md`, `PROGRESS.md`, `SESSION_HANDOFF.md`.

## 9. AI-use disclosure

Built with AI assistance (Claude Code) under the owner's direction. Sentiment benchmark labels were drafted by Claude for owner verification; the NVIDIA API Catalog was used for an LLM sentiment baseline, recommendation wording and thumbnail labels.
