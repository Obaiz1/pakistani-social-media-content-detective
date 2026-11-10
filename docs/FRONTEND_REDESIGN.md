# Frontend redesign

## Audit and scope

Baseline: `957e3b6` on `main`, clean checkout. The app actually registers **nine** pages: Overview, What to post next, Brands, Content, Posting time, Adjusted effects, Sentiment, Report & exports, and Data & Method. Older eight-page documentation predates Adjusted effects.

`app.py` owns native navigation. `src/ui.py` owns data provenance, the shared sidebar controls and median/CI presentation. Views call the existing analytics/recommendation/reporting modules. Data-source precedence, caches and `loaded`/`rewrites` state remain in their existing modules. Brand, PKT date, duration and promotion filters retain their original keys, options, defaults and calculations. Method intentionally shows the whole dataset; Brands coverage and Overview's collected-comment count also remain whole-dataset values, now labeled explicitly.

## Presentation changes

- Native navy/slate theme with teal controls, readable borders, compact headings and responsive native containers. Branding uses local SVG assets through `st.logo`; the only CSS targets our own eyebrow class. No injected JavaScript, frontend framework or new runtime dependency.
- Grouped sidebar navigation, compact source/date status, consistent page/section headings, bordered KPI cards, chart surfaces, recommendation evidence panels and export format cards across all nine pages.
- Shared Plotly styling copies figures, preserves trace data, CI arrays, reference lines, categories and existing blue/red semantics. Titles render above the chart and long horizontal-axis descriptions below it so they wrap at narrow widths with their original wording. Streamlit continues to supply theme-aware chart text; toolbars, hover and zoom remain native.
- Synthetic provenance remains prominent on every page. Method now accurately identifies fictional records and distinguishes saved real benchmark evidence. Statistical caveats, adjusted-model checks, insufficient samples and unavailable-service states remain visible.
- Fixed an audited pre-existing navigation issue: shared filters reset when switching pages. Re-saving the four existing widget keys in the entry point follows Streamlit's documented [multipage widget pattern](https://docs.streamlit.io/develop/concepts/multipage-apps/widgets#option-3-interrupt-the-widget-clean-up-process), including navigation through Method, which has no filter widgets. No filter semantics changed.
- Browser QA exposed an existing table-preview compatibility issue: an unavailable Kruskal p-value in pandas metadata serialized as invalid JSON `NaN`. Exports now clears metadata on a **display-only copy**. Original statistical tables, values and download inputs retain their metadata and are unchanged.

## Verification

Environment: Python 3.12.14, `uv sync`, locked Streamlit 1.66.0 / Plotly 7.1.0. In this managed workspace, commands use `uv --cache-dir /workspace/work/uv-cache` because the default home cache is read-only.

- Before edits: `uv run pytest -q` — **122 passed**.
- An independent AppTest capture of all nine pages before/after confirms identical metric labels/values, Plotly trace data and confidence intervals, table contents, and all original widget labels/options/defaults/disabled states. The only added controls are two Overview navigation buttons.
- Six focused interaction tests cover the three brand metrics, empty brand/duration selections, promoted/reliability exclusions, all four filters across pages (including Method), both new navigation buttons, seven export previews and download availability.
- Final full suite: `uv run pytest -q` — **128 passed**. The export test additionally exercises the existing `61-180s` / include-promoted selection, which enables the CSV button through supported evidence rather than a fabricated card.
- Chromium/Playwright rendered all nine pages at 1440px desktop and 390px mobile widths with synthetic provenance, zero application exceptions and no document/main horizontal overflow. Tables keep native internal scrolling. A narrow-screen review prompted clearer timing heatmap counts and shorter axis tick labels; full time-band labels and values remain in hover.
- Browser checks cover navigation, all three brand metric choices, filter persistence, empty selections, seven export previews and actual Excel/PDF/CSV downloads. Default synthetic data correctly disables CSV when no supported cards exist; an eligible selection enables and downloads it. Only the configured dark theme was visually validated; this installed Streamlit menu does not expose a theme switch. The synthetic adjusted-model unavailable state was tested; private real-data model output was not.

No `.env`, dataset, processing, scientific model, statistical threshold, recommendation algorithm or report-generation code was changed. Private snapshots, optional NLP fitting and external API calls are unavailable in this environment; validation uses the existing clearly labeled synthetic fixture. Saved benchmark tables remain the original tracked evidence. A successful local test is not a claim that real data or hosted production was tested.

## Publishing

Published on 2026-11-10 to [`ali-ahmad-ai/pakistani-social-media-content-detective`, branch `codex/frontend-redesign`](https://github.com/ali-ahmad-ai/pakistani-social-media-content-detective/tree/codex/frontend-redesign). The original UI implementation commit is `1d40dee`.

The authorized account can read the original repository but has no upstream push permission, so publication uses a GitHub fork. `origin` still points to `Obaiz1/pakistani-social-media-content-detective`; the local `fork` remote points to the authorized account. Existing branches and upstream `main` were not overwritten.

- [Pull request #1 against the original repository](https://github.com/Obaiz1/pakistani-social-media-content-detective/pull/1)
- [Download the finished source as a ZIP](https://github.com/ali-ahmad-ai/pakistani-social-media-content-detective/archive/refs/heads/codex/frontend-redesign.zip)

The pull request is open for review; the redesign has not been merged or deployed to the existing hosted app. Historical handoff credentials describe a different machine, and no authentication tokens are included in the repository or download.
