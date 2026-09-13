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

## Commit list (feature branch → merge)

```
b205985 checkpoint: begin WP16 interactive plot visual repair
f514b9c WP16: shared Plotly presentation policy + dynamic iframe height sync
4292e42 Merge fix/interactive-plot-visuals into main (WP16)   [on main, --no-ff]
```

Tag `wp16-start` → `92cf7e0152338faf07e5a5e1da6614d9f8645441` (annotated,
unsigned).
