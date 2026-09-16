# WP22 — Exact Changelog

Branch: `fix/published-dark-mode-plots`
Base commit: `4f9bc7014625ed0a50df938f393b957a25c04037` (WP22 spec checkpoint)

## New files

- **`interactive/src/theme.ts`**
  Centralized theme-detection/subscription module. `getActiveTheme()` resolves,
  in order: the parent document's `data-theme`/`data-mode` (same-origin,
  try/catch-guarded) → this document's own `data-theme`/`data-mode` (test
  harness / standalone fallback) → `prefers-color-scheme` → `"light"`.
  `subscribeToThemeChanges(onChange)` attaches a `MutationObserver` to the
  parent's root element (when a parent exists) or, only when there is no
  parent, to this document's own root; always attaches a `prefers-color-scheme`
  `change` listener. Deduplicates: only calls `onChange` when the resolved
  theme actually differs from the last notification (this is also what
  prevents the own-document observer from re-triggering itself when this
  app's own code writes to its own `data-theme` attribute — see `main.ts`
  below). Returns one cleanup function that disconnects every observer/
  listener; safe to call more than once.

- **`interactive/tests/theme.test.ts`** (7 tests)
  Unit tests for `theme.ts` against hand-written fakes of `MutationObserver`,
  `matchMedia`, and DOM elements (no `jsdom` dependency added). Covers: reads
  an already-active parent dark theme; falls back to `prefers-color-scheme`
  when no parent theme is available; falls back to light; does not throw when
  the parent is cross-origin; calls back on a parent attribute change; calls
  back on a browser-preference change when no parent is available; cleans up
  every observer and the media-query listener on unsubscribe (and is
  idempotent).

- **`interactive/tests/plotly-policy.test.ts`** (6 tests)
  Unit tests for the theme→palette mapping and layout helper in
  `plotly-policy.ts`: light/dark palettes are genuinely distinct in every
  field; every color field is a non-empty explicit string in both themes;
  `buildPlotLayout` actually wires the theme's axis/grid/legend colors into
  the Plotly layout (not a default); paper/plot background stays intentionally
  transparent in both themes; the WP16 interaction lock (`dragmode:false`,
  `fixedrange:true`) survives theme changes; a component's nested-axis
  override does not drop the shared defaults alongside it.

- **`interactive/e2e-book/chapter01-dark-mode.spec.ts`** (2 tests)
  Built-book Playwright spec against the histogram and correlation-scatter
  activities on `chapters/chapter_01/exercise_01.html`, served over real HTTP.
  See WP22_REPORT.md §6–7 for the exact assertions, the sandbox-specific
  navigation workaround, and confirmation that this spec fails against the
  pre-WP22 code.

## Modified files

- **`interactive/src/components/plotly-policy.ts`**
  `getPlotlyTheme()` changed from a zero-argument function that called
  `matchMedia` itself (the actual root-cause bug) to `getPlotlyTheme(theme:
  Theme): PlotlyTheme`, a pure function of the resolved theme from
  `theme.ts`. `PlotlyTheme` gained four explicit fields: `legendBg`,
  `legendText` (previously unset anywhere — Plotly's own default legend chip
  is an opaque near-white, unreadable once the card went dark),
  `markerPrimary` and `diagonalLine` (the "observed vs predicted" marker
  color and dashed reference-line color, previously the exact same ternary
  copied into `regression-compare.ts`, `knn-abc.ts`, and `knn-explore.ts`
  independently — now one definition). `buildPlotLayout` now sets
  `xaxis`/`yaxis` `linecolor`/`tickcolor` explicitly (previously unset) and
  gives the legend an explicit `bgcolor`/`font.color` by default instead of
  Plotly's own default.

- **`interactive/src/main.ts`**
  Imports `getActiveTheme`/`subscribeToThemeChanges` from `./theme`. Before
  `boot()` runs, sets `document.documentElement.dataset.theme =
  getActiveTheme()` on this app's OWN document and subscribes to keep it in
  sync for the life of the page. This is the one place that bridges the
  resolved theme into `styles.css`'s `[data-theme]` selectors; it does not
  redraw any chart itself (each component does that independently, below).

- **`interactive/src/styles.css`**
  The dark palette, previously only under `@media (prefers-color-scheme:
  dark)`, now also has an explicit `:root[data-theme="dark"]` block (same
  values) that wins once `main.ts` has run; the media-query block is guarded
  with `:not([data-theme="light"])` so an explicit light choice from the
  parent always beats a dark OS preference. Added `.widget-plot .draglayer
  rect { fill: transparent !important; stroke: none !important; }`, scoped
  only inside a chart's own drag layer (not a global `svg rect` rule) — a
  hardening guard; computed-style verification against the built book showed
  these rects were already transparent via the existing `dragmode:false` +
  `fixedrange:true` policy (WP16), see WP22_REPORT.md §5.

- **`interactive/src/components/histogram.ts`**,
  **`correlation.ts`**, **`regression-compare.ts`**, **`knn-abc.ts`**,
  **`knn-explore.ts`**, **`classification-threshold.ts`**,
  **`classification-imbalance.ts`**, **`retention.ts`**,
  **`runtime-smoke.ts`** (dev smoke-test activity, fixed for consistency)
  Each: (1) `const theme = getPlotlyTheme();` → `let theme =
  getPlotlyTheme(getActiveTheme());`; (2) every theme-dependent color that
  used to be computed once, outside `draw()`, moved inside the relevant draw
  function so it is recomputed from the current `theme` on every call; (3)
  calls `subscribeToThemeChanges` once during `mount()`, reassigns `theme`
  and re-invokes the component's own draw function(s) on every change; (4)
  the returned `unsubscribeTheme()` is called from the component's
  `destroy()` alongside the existing `Plotly.purge(...)` calls.
  `classification-imbalance.ts` additionally pins an explicit
  `textfont: { color: theme.axisColor }` on its bar trace's outside-positioned
  percentage labels and an explicit color on its plot title font (both
  previously left to Plotly's own default).
  `regression-compare.ts`, `knn-abc.ts`, and `knn-explore.ts` additionally
  read the deduplicated `theme.markerPrimary`/`theme.diagonalLine` from
  `plotly-policy.ts` instead of each re-deriving the identical ternary.

## Cross-chapter verification addendum

- **`interactive/e2e-book/wp22-cross-chapter-dark-mode.spec.ts`** (new, 3 tests)
  Built-book Playwright spec extending dark-mode coverage beyond Exercise 1
  (`chapter01-dark-mode.spec.ts`) to one Plotly activity from every other
  exercise: `regression-compare` (Exercise 2, both panels), `knn-abc`
  (Exercise 3, all three panels — the activity shown in the original bug
  screenshot) plus `knn-explore`'s scatter, and `classification-threshold`'s
  ROC plot plus `classification-imbalance`'s bar chart (Exercise 4). Reads
  each figure's principal data-mark color directly off Plotly's own
  `_fullData[i].marker.color`/`.line.color` rather than computed SVG style,
  since three of these activities' scatter panels use the `scattergl` (WebGL)
  trace type, which has no per-point SVG element to inspect. See
  `WP22_REPORT.md` §"Cross-chapter verification addendum" for the full
  assertion list, results, and the one bounded correction required (a test
  formatting mismatch, not a product defect).

## Not changed

Notebook teaching content, datasets, participant splits, model parameters,
metrics, interaction defaults, student questions, and portable-notebook
calculations are untouched. `table-inspection.ts` (no Plotly) is untouched.
No `.ipynb` file was edited.
