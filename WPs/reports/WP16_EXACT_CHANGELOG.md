# WP16 — Exact changelog

Branch `fix/interactive-plot-visuals`, commits `b205985` (checkpoint) →
`f514b9c` (implementation), merged into local `main` at `4292e42`
(`--no-ff`). Diff below is `b205985..f514b9c` (the implementation commit);
the merge commit itself is a plain fast-forward-content merge with no
additional changes.

```
 26 files changed, 576 insertions(+), 204 deletions(-)
```

## New files

- `interactive/src/components/plotly-policy.ts` (99 lines) — shared
  `getPlotlyTheme()`, `PLOT_CONFIG`, `buildPlotLayout(theme, overrides)`.
- `interactive/src/resize-report.ts` (29 lines) — in-page `ResizeObserver` +
  same-origin `postMessage` height reporting.
- `book/_static/activity-resize.js` (45 lines) — parent-page listener that
  syncs an embedding iframe's `style.height` to the reported content height.
- `interactive/e2e/plot-visual-policy.spec.ts` (153 lines) — standalone
  project-wide Plotly-policy regression suite (10 tests).
- `interactive/e2e-book/chapter02-visual-policy.spec.ts` (167 lines) —
  built-book Exercise 2 geometry regression suite (12 tests, 3 viewport
  widths × 4 checks).
- `WPs/reports/wp16_screenshots/*.png` (10 files) — visual evidence,
  742px/390px × 5 activities.

## Modified files

### `interactive/src/plotly.d.ts`
- `PlotData`, `Layout`, `Config` changed from private to `export`ed (needed
  by the new shared helper).
- `Config` gained optional `scrollZoom?: boolean` and
  `doubleClick?: false | "reset" | "autosize" | "reset+autosize"`.

### `interactive/src/components/histogram.ts`, `retention.ts`,
`correlation.ts`, `regression-compare.ts`, `knn-explore.ts`, `knn-abc.ts`,
`runtime-smoke.ts`
- Removed each file's private `prefersDark()` + `axisColor`/`gridColor`
  computation; replaced with `const theme = getPlotlyTheme();` and
  `theme.dark` where a trace-specific color still needs it (bar fill,
  marker color, etc. — unchanged values, e.g. `theme.dark ? "#5a9bd4" :
  "#2a6f9e"`).
- Removed each file's local `const plotConfig = { displayModeBar: false,
  responsive: true };`; all `Plotly.react(...)` calls now pass the shared
  `PLOT_CONFIG` directly.
- Replaced every hand-written `layout` object literal with
  `buildPlotLayout(theme, { ...only the activity-specific overrides... })`.
  Numeric margins/heights/legend positions are **unchanged values** — e.g.
  regression-compare's `margin: { t: 12, r: 12, b: 48, l: 56 }` is now
  simply omitted (identical to the shared default), knn-abc's
  `margin: { t: 12, r: 8, b: 44, l: 52 }` is now `margin: { r: 8, b: 44, l:
  52 }` (t:12 matches the default), retention's `margin: { t: 12, r: 12, b:
  110, l: 56 }` is now `margin: { b: 110 }`. No trace data, axis ranges,
  shapes, annotations, or legend y-offsets were changed in value — only
  where the shared `fixedrange`/`automargin`/`gridcolor`/`zeroline`/
  `paper_bgcolor`/`plot_bgcolor`/`dragmode` keys used to be repeated
  per-file, they are now supplied once by `buildPlotLayout`.
- `correlation.ts`'s "same variable" empty-plot layout changed from the ad
  hoc `{ autosize: true }` to `buildPlotLayout(theme)` (same effective
  behavior, now carrying the shared interaction lock too).

### `interactive/src/main.ts`
- Added `import { startHeightReporting } from "./resize-report";` and one
  call `startHeightReporting();` inside `boot()`, right after the
  `beforeunload` listener is registered. No other change.

### `interactive/src/styles.css`
- `.widget-plot`: added `margin-bottom: 16px;`.
- `.widget-compare-panel`: `background: var(--surface-alt);` →
  `background: var(--bg);`.
- `.widget-compare-panel .widget-plot`: removed the now-redundant
  `background: var(--bg);` line (inherited, same value, no visual change).

### `book/_config.yml`
- Added `activity-resize.js` to `sphinx.config.html_js_files` (after
  `launch-buttons.js`).
- Added an explanatory comment block above the portable-notebook comment,
  documenting the new script (matches the file's existing WP-numbered
  comment convention).

## Unchanged (verified, not touched)

- `book/config/abide_modeling.json`, all `scripts/*.py`, all
  `book/_static/widgets/data/*` and `*.bin` binary assets, all 3 canonical
  notebooks' code cells and `height="N"` iframe attributes, all 3 portable
  notebooks, `book/_static/custom.css`, `book/_static/launch-buttons.js`,
  `book/_static/sidebar-toggle-fix.js`.
- Every existing test file (`interactive/tests/*.test.ts`,
  `interactive/e2e/*.spec.ts` other than the one new file,
  `interactive/e2e-book/*.spec.ts` other than the one new file,
  `tests/test_*.py`) — 0 lines changed.

## Commit list (feature branch → merge → deploy)

```
b205985 checkpoint: begin WP16 interactive plot visual repair
f514b9c WP16: shared Plotly presentation policy + dynamic iframe height sync
4292e42 Merge fix/interactive-plot-visuals into main (WP16)                    [on main, --no-ff]
9154d7e WP16 report: shared Plotly policy, iframe resize sync, deploy withheld [pushed, DEPLOYED -- run 34778058145, success]
0a025bf WP16 report: add deployment and live-production verification evidence [pushed, CI FAILED -- run 34829127825, see below]
ad6a86b WP16: fix a genuine test race in the new geometry specs               [pushed, DEPLOYED -- run 34832347096, success]
```

Tag `wp16-start` → `92cf7e0152338faf07e5a5e1da6614d9f8645441` (annotated,
unsigned).

## Deploy history

- `9154d7e` deployed by run `34778058145` (`build-and-deploy`, success,
  3m30s, `headSha=9154d7e27745adbe7c2b0278674c470e05ee0820`).
- `0a025bf` (report/screenshot only — zero application-code changes)
  triggered run `34829127825`, which **failed** at the built-book
  Playwright step: `chapter02-visual-policy.spec.ts`'s 390px "x-axis title"
  test measured clearance `-6` instead of `>=12`. Root cause: a race
  condition in the *test* (introduced by this WP's own new spec files) —
  geometry was read right after `data-widget-ready`, which does not
  guarantee the async `Plotly.react()` call inside each panel's `draw()`
  has resolved; a loaded CI runner can expose a window where the plot div
  is still at its CSS `min-height` placeholder rather than its true
  rendered height. `Publish website` did not run for this commit — the
  live site correctly kept serving `9154d7e` throughout. See
  `WPs/reports/WP16_REPORT.md` §9.1 for the full account.
- `ad6a86b` — test-only fix (both new spec files now wait for each plot's
  `data-render-count` before reading geometry/state; same fix applied to
  the "control change" test's post-redraw read) — deployed by run
  `34832347096` (`build-and-deploy`, success, 3m36s,
  `headSha=ad6a86b209762b6f1224d5da435dfde308179368`).
- `85d683d` (report/screenshot only — zero application-code changes)
  triggered run `34840155813`, which **failed** the same
  `chapter02-visual-policy.spec.ts` clearance assertion again, this time
  at **wide desktop (1920px)** instead of 390px, with the identical `-6`
  measurement. Root cause this time: not the render-count test race (that
  was already fixed by `ad6a86b`) — a constant `-6px` offset independent
  of viewport width points to a platform-level rendering difference in the
  browser's native `<summary>` disclosure-marker box (observed a few px
  shorter on Linux/Chromium CI than on macOS). `Publish website` did not
  run for this commit — the live site kept serving `ad6a86b` throughout.
- `a57fefc` — widened `.widget-plot`'s CSS `margin-bottom` from `16px` to
  `28px` (`interactive/src/styles.css`), giving the guaranteed 12px
  minimum clearance real headroom against this class of small,
  non-deterministic-per-machine rendering variance. Stable across 3
  repeated local runs of the affected spec plus a full 158/158 run of both
  Playwright suites. Deployed by run `34842940655` (`build-and-deploy`,
  success, `headSha=a57fefc01fa63e67805afb3db64b74507b36133f`). **This is
  the final deployed revision.**

See `WPs/reports/WP16_REPORT.md` §9 for the full live-production
verification: 34/34 Playwright tests against `https://yoavmp.github.io`
after the first deploy, a further 12/12 re-run (including the exact
previously-failing 390px case) against `ad6a86b`, and (§9.4, WP16R
completion session) a 31-test re-run against the final deployed revision
`a57fefc` — 31/31 passing serially, with the live CSS directly confirmed
to be serving the 28px buffer.

## Modified files (test-race fix, `0a025bf..ad6a86b`)

- `interactive/e2e-book/chapter02-visual-policy.spec.ts` — added
  `waitForBothPanelsRendered()`, called after every `data-widget-ready`
  check; the "control change" test additionally waits for
  `data-render-count` to bump (not just `data-feature-count`) before
  reading post-redraw state.
- `interactive/e2e/plot-visual-policy.spec.ts` — added `waitForRendered()`,
  called after every `data-widget-ready` check before reading geometry or
  `_fullLayout` state.

No application code (components, `plotly-policy.ts`, CSS, `main.ts`,
`resize-report.ts`, `activity-resize.js`) changed in this fix — test files
only.

## Modified files (cross-platform clearance-buffer fix, `85d683d..a57fefc`)

- `interactive/src/styles.css` — `.widget-plot`'s `margin-bottom: 16px` →
  `margin-bottom: 28px`, plus an explanatory comment. 1 rule changed, no
  other selectors touched. `git show --stat a57fefc`:
  `interactive/src/styles.css | 10 +++++++++-` (9 insertions, 1 deletion —
  the extra lines are the added comment).
