# WP16 — Repair Plotly axes, backgrounds, spacing, and production parity

## Status: implementation complete, merged to local `main`; **push and production deploy withheld pending Yoav's go-ahead** (see §9)

WP16 was executed in full through §5 (implementation + full local validation
gate) and §6 steps 1–5 (commit, fetch, fast-forward `main`, merge, post-merge
local re-validation). Steps 6–10 of §6 (push, monitor deploy, verify
production) were **not** performed: when asked directly, Yoav said not to
push unless explicitly instructed, and to leave that as an open item here
instead. Nothing was force-pushed, no destructive git command was used, nothing was deployed.
`main` locally is 3 commits ahead of `origin/main` and ready to push at any
time — see §9 for the exact command.

---

## 1. SHAs / tags / branches

| | |
|---|---|
| Starting SHA (verified against WP's stated WP15 final SHA) | `92cf7e0152338faf07e5a5e1da6614d9f8645441` |
| Start tag | `wp16-start` (annotated, unsigned — no GPG configured; same as prior WPs) |
| Working branch | `fix/interactive-plot-visuals` |
| Checkpoint commit (WP file added) | `b205985` |
| Implementation commit | `f514b9c` — *"WP16: shared Plotly presentation policy + dynamic iframe height sync"* |
| Merge commit (local `main`, `--no-ff`) | `4292e42` — *"Merge fix/interactive-plot-visuals into main (WP16)"* |
| `origin/main` at start and now | `92cf7e0` (unchanged — nothing pushed yet) |
| Local `main` HEAD | `4292e42` (3 commits ahead of `origin/main`) |

`git status --short --branch` on `main`: `## main...origin/main [ahead 3]`,
clean working tree.

---

## 2. Root cause

### 2.1 X-axis title / ROI-summary overlap (the named Exercise 2 defect)

Every component (`histogram.ts`, `retention.ts`, `correlation.ts`,
`regression-compare.ts`, `knn-explore.ts` ×3 plots, `knn-abc.ts`,
`runtime-smoke.ts`) built its own Plotly `layout` object by hand: a fixed
figure `height` plus a fixed pixel bottom `margin`, and **no `automargin`**
on either axis. Plotly only reserves exactly the declared margin for a
title + tick labels; without `automargin` it does not grow that margin (and
shrink the plot area to compensate) when the title needs more room — it
paints the title in the declared space regardless, and if that isn't enough
the title bleeds toward (or past) the edge of the figure's own box.

Reproducing this in headless Chromium against the pre-WP16 build
(`git worktree add` at `92cf7e0`, both real desktop widths 742px/390px)
found the x-axis title (`"Observed Age at scan"`) exactly flush with the
plot's own SVG bottom edge (`xTitleBottom == svgBottom`, no measurable
negative overlap in this environment/font stack), and only **8px** of
CSS clearance to the following ROI-summary `<details>` — already below the
12px minimum WP16 requires, and the kind of margin that a different
font-rendering pipeline (a different OS/browser, the actual live GitHub
Pages font fallback) tips into a visible overlap, which is what was
reported. Root cause confirmed either way: `margin.b: 48` with no
`automargin` is not a real guarantee of clearance, it is a guess that
happens to hold in one environment.

Fix: `buildPlotLayout` (new `interactive/src/components/plotly-policy.ts`)
sets `automargin: true` on both axes unconditionally, so Plotly itself
guarantees the title/ticks stay inside the figure's declared `height`
regardless of font metrics. `.widget-plot` additionally gets an explicit
`margin-bottom: 16px` in CSS so the *next* DOM element's clearance is
guaranteed by layout, not by hoping Plotly's automargin calculation and the
next element's own top margin add up to something reasonable.

### 2.2 Lavender-gray comparison-card background

`.widget-compare-panel` (used by Exercise 2's regression-compare and
Exercise 3's knn-abc A/B/C activity — the only two activities that use a
compare-grid) had `background: var(--surface-alt)` (`#f4f4f9`), while
Plotly's own `paper_bgcolor`/`plot_bgcolor` were already transparent, so a
white plot sat inside a gray card. Changed to `background: var(--bg)`
(matches the page). `--surface-alt` is untouched everywhere else (tables,
radio/checkbox groups, warnings) per WP16's explicit instruction not to
remove it globally.

### 2.3 Axis drag/pan/zoom left enabled

No component set `dragmode`, `fixedrange`, `scrollZoom`, or `doubleClick`.
`buildPlotLayout` now sets `dragmode: false` plus `fixedrange: true` on both
axes; the shared `PLOT_CONFIG` sets `scrollZoom: false` and
`doubleClick: false`. Verified via the chart's own runtime
`_fullLayout.dragmode`/`_fullLayout.{x,y}axis.fixedrange` (not just visual
inspection) in `interactive/e2e/plot-visual-policy.spec.ts`, plus a live
drag/scroll-wheel/double-click attempt on the actual chart that leaves
`xaxis.range` unchanged. Hover tooltips are unaffected (also tested).

---

## 3. Plotly call sites audited

| File | Plot(s) | Notes |
|---|---|---|
| `components/histogram.ts` | 1 bar chart | Exercise 1 histogram |
| `components/retention.ts` | 1 bar chart | Exercise 1 missingness/retention |
| `components/correlation.ts` | 1 scatter (+ empty-state layout) | Exercise 1 correlation explorer |
| `components/table-inspection.ts` | none | plain HTML table, not a Plotly consumer — confirmed via `grep -l Plotly`, out of scope |
| `components/regression-compare.ts` | 2 scatter (panels A/B) | **Exercise 2 — the named defect** |
| `components/knn-explore.ts` | 3 plots (scatter, error curve, binned-calibration) | Exercise 3 k explorer |
| `components/knn-abc.ts` | 3 scatter (panels A/B/C) | Exercise 3 A/B/C comparison |
| `components/runtime-smoke.ts` | 1 bar chart | developer smoke test, not course content — updated anyway for one project-wide policy |

Every one of these previously duplicated its own `prefersDark()` /
`axisColor`/`gridColor` computation and its own `layout`/`plotConfig`
object; all now import `getPlotlyTheme`, `buildPlotLayout`, `PLOT_CONFIG`
from the one shared module. Net diff across the 8 component files:
**+40 / −204 lines** (consolidation, not duplication of a fix).

---

## 4. Shared layout/config/CSS changes

- **New `interactive/src/components/plotly-policy.ts`**: `getPlotlyTheme()`
  (dark-mode-aware axis/grid colors), `PLOT_CONFIG` (modebar off,
  responsive, scroll-zoom off, double-click off), `buildPlotLayout(theme,
  overrides)` — a merge that goes one level deep into `margin`, `xaxis`,
  `yaxis`, `legend`, `font` so an activity overriding e.g. `xaxis.range`
  cannot silently drop the shared `fixedrange`/`automargin`/`gridcolor`
  defaults alongside it. Activity-specific titles, ranges, traces, shapes,
  annotations, legends are passed through as overrides exactly as before.
- **`interactive/src/plotly.d.ts`**: exported the previously-private
  `Layout`/`Config`/`PlotData` ambient types (needed to type the shared
  helper) and declared `scrollZoom`/`doubleClick` on `Config`.
- **`interactive/src/styles.css`**: `.widget-plot { margin-bottom: 16px }`;
  `.widget-compare-panel { background: var(--bg) }` (was
  `var(--surface-alt)`); removed the now-redundant
  `.widget-compare-panel .widget-plot { background: var(--bg) }` override.

---

## 5. A second, deeper defect found while writing the regression tests

Building the geometry regression test for Exercise 2 (WP16 §4 item 9: "no
internal iframe clipping … at each canonical embedded height") surfaced a
**pre-existing, separate defect**: every activity's Jupyter Book iframe uses
one static HTML `height="N"` attribute, but each activity's real content
height changes with viewport width (the compare-grid collapsing from
side-by-side panels to a stacked column below ~620px of *iframe* width;
controls wrapping to more rows). Measured against the pre-WP16 build at
742px/390px, Exercise 2's iframe (`height="1180"`) already needed
1241px/2482px — already clipped before this WP touched anything.

Worse: the book theme's own responsive layout (secondary/TOC sidebar
visibility) is **not monotonic** in outer page width — e.g. at 1200px
outer viewport the content column is narrower than at 1350px, non-linearly,
so no single CSS media-query breakpoint on the outer page can reliably
predict when a given iframe's *own* rendered width will trigger its
internal grid to reflow. A static breakpoint hack would have "fixed" the
problem at the exact widths tested and silently reintroduced clipping at
others.

**Fix implemented** (in scope because it directly serves WP16 §2.5's own
instruction — *"update the existing embedding-height mechanism safely and
consistently rather than clipping content"* — and because Exercise 2 and
knn-abc are the two activities WP16 explicitly named): a small,
self-contained dynamic-height mechanism, not a magic-number CSS breakpoint:

- `interactive/src/resize-report.ts` — inside every activity, a
  `ResizeObserver` on `document.documentElement` posts
  `{type:"ml-activity-resize", height}` to `window.parent` (same-origin
  only; no-ops when not embedded, so it is inert for the standalone Vite
  build and its Playwright suite).
- `book/_static/activity-resize.js` — a same-origin `message` listener that
  finds the matching `iframe[src*="/widgets/app/"]` by `event.source` and
  sets its `style.height`, clamped to `[200px, 8000px]`.
- Each notebook's `height="N"` attribute is unchanged and now serves only
  as the pre-JS fallback (no layout jump for a no-JS reader; a sane initial
  paint before the first message arrives).

This generalizes correctly to *every* activity (not just the two named
ones) and adapts to any future content change or viewport width without
another magic number.

**Deliberately left out of WP16's scope**: the other 5 activities
(histogram, retention, correlation, table-inspection, knn-explore) show the
*same class* of static-height shortfall — measured against the current,
merged build:

| Activity | declared height | needed @742px | needed @390px |
|---|---:|---:|---:|
| table-inspection | 760 | 762 | 975 |
| retention | 900 | 1168 | 1795 |
| histogram | 680 | 762 | 999 |
| correlation | 820 | 1120 | 1669 |
| knn-explore | 2700 | 2698 | 3920 |

These now self-correct at runtime via the same `activity-resize.js`
mechanism (it listens for *any* matching iframe, not just the two WP16
named), so **this is fixed for all 7 activities**, not only the two named
ones — the dynamic mechanism is genuinely project-wide by construction, not
scoped per activity. Flagged here only so the previously-static numbers in
the table above are visible for the record; no further action is needed.

---

## 6. Before/after geometry — Exercise 2

Measured with Playwright against the actual built Jupyter Book
(`chapters/chapter_02/exercise_02.html`), panel A, `svg.main-svg` /
`.xtitle` / `[data-testid="regression-A-roi-summary"]`.

| | Before (pre-WP16, `92cf7e0`) | After (this WP, both widths) |
|---|---|---|
| x-axis title bottom vs. plot SVG bottom | flush (0px to spare) | flush by construction (`automargin`), never exceeds |
| Clearance to ROI-summary `<details>` | **8px** (742px and 390px) | **16px** (742px, wide desktop, 390px — all three) |
| Comparison-card background | `rgb(244, 244, 249)` (`#f4f4f9`) | `rgb(255, 255, 255)` (matches page `<body>` background) |
| Iframe content vs. declared height @742px | needs 1241px, declared 1180px (clipped) | needs 1245–1249px, iframe dynamically resizes to match (no clipping) |
| Iframe content vs. declared height @390px | needs 2482px, declared 1180px (severely clipped) | needs 2492–2498px, iframe dynamically resizes to match (no clipping) |

---

## 7. Axis dragging / hover / modebar / responsiveness / accessibility

Verified via `interactive/e2e/plot-visual-policy.spec.ts` against every
plot testid across 6 activities (histogram, retention, correlation,
regression-compare, knn-abc, knn-explore):

- `_fullLayout.dragmode === false`, `_fullLayout.xaxis.fixedrange === true`,
  `_fullLayout.yaxis.fixedrange === true` — every chart.
- No `.modebar` element present — every chart.
- A drag, a scroll-wheel event, and a double-click on the plot leave
  `xaxis.range` unchanged (regression-compare, representative).
- Hovering a data point still shows `.hoverlayer .hovertext` (regression-
  compare) — the interaction lock does not remove hover.
- Existing per-activity specs (unchanged, all still passing) already prove
  slider/select/tab control changes still redraw the real trace data and
  metrics, not just labels.
- Keyboard operability of every lesson control is untouched — no control
  markup was changed, only the Plotly figure's own layout/config.

---

## 8. Test commands and results (this WP)

```
(cd interactive && npm run typecheck)                                    # PASS
(cd interactive && npm run test:unit)                                    # 276 / 276
(cd interactive && npm run build)                                        # succeeded, pre-existing 500kB chunk advisory only
(cd interactive && npm audit --omit=dev)                                 # 0 vulnerabilities
python -m unittest discover -s tests                                     # 308 / 308
python scripts/export_regression_catalog.py --check                     # OK
python scripts/regression_model_audit.py --check                        # OK
python scripts/knn_model_audit.py --check                                # OK
python scripts/export_knn_abc_data.py --check                           # OK
python scripts/export_widget_data.py --check                            # OK
python scripts/sample_size_audit.py --check                             # OK
python scripts/abide_modeling_data.py --check                           # OK
python scripts/export_knn_explore_data.py --check                       # OK
python scripts/build_portable_notebook.py --check                       # all 3 up to date
python scripts/smoke_portable_notebook.py --notebook all                # OK x3, key values matched
jupyter-book build book (clean, ×2 consecutive)                         # identical HTML output both times; 2 pre-existing warnings (logo.png, README.md toctree), unchanged
(cd interactive && npx playwright test)                                  # 110 / 110 (100 pre-existing + 10 new in plot-visual-policy.spec.ts)
(cd interactive && npx playwright test --config playwright.book.config.ts) # 48 / 48 (36 pre-existing + 12 new in chapter02-visual-policy.spec.ts)
```

All of the above re-run and green **after** the `--no-ff` merge to local
`main` (post-merge gate), not only on the feature branch.

No generated data or notebook content changed: every `--check` above
re-validates a **committed, unmodified** artifact; the portable-notebook
smoke test re-executes all 3 notebooks end to end and matches recorded key
values. This was a presentation-only change (CSS/Plotly layout/config,
plus the resize-sync JS) — no regression/KNN math, splits, features, scores,
or binary data were touched.

---

## 9. Deployment — **withheld pending your decision**

Per WP16 §6, the intended remaining steps are: push `main`, monitor the
GitHub Pages workflow, hard-refresh and verify the three live exercise
pages, run the geometry/style Playwright checks against the live site, and
inspect production screenshots. **None of this was done.** When I checked
whether to push, you said not to unless explicitly instructed, and to leave
it here as an open item instead.

Local `main` is fully ready: 3 commits ahead of `origin/main`
(`b205985` checkpoint → `f514b9c` implementation → `4292e42` merge), clean
working tree, every test above green post-merge. To ship it:

```
git push origin main
```

Then watch the "pages build and deployment" GitHub Actions workflow to
terminal success, hard-refresh
`https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_02/exercise_02.html`
(and chapters 1 and 3), and confirm the deployed revision matches
`4292e42`. I can do all of that in one pass whenever you say go.

---

## 10. Live URLs (not yet re-verified against this change)

- `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html`
- `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_02/exercise_02.html`
- `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_03/exercise_03.html`

These currently still serve the pre-WP16 build (`92cf7e0`), including the
tight 8px clearance, the gray comparison-card background, and enabled axis
dragging. They will reflect this WP's fix once `main` is pushed and the
Pages workflow completes.

---

## 11. Screenshots (production build, built Jupyter Book, post-merge)

Saved under `WPs/reports/wp16_screenshots/`, one pair (742px content width /
390px narrow) per activity:

- `ex1-histogram-{742px,390px}.png`
- `ex1-retention-{742px,390px}.png`
- `ex2-regression-{742px,390px}.png`
- `ex3-knn-abc-{742px,390px}.png`
- `ex3-knn-explore-{742px,390px}.png`

All show white/theme-matching plot cards, fully visible axis titles and
legends, no modebar, and (Exercise 2, knn-abc) clean panel-to-panel
comparison with real clearance before the ROI-summary disclosure.

---

## 12. Deviations / items for Yoav's attention

1. **Push/deploy/production verification not performed** — see §9. This is
   the only incomplete part of WP16's own checklist, and it is incomplete
   because you asked me to hold, not because anything failed.
2. **The reported "~15px overlap" did not reproduce as a literal negative
   number in headless Chromium** against the pre-WP16 build — it reproduced
   as an 8px clearance (below the 12px minimum WP16 sets, and flush against
   the plot's own SVG edge). This is consistent with the same root cause
   (no `automargin`) manifesting more severely under different font
   rendering than my test environment's; I did not chase an exact
   pixel-for-pixel reproduction of "15px" specifically since the underlying
   defect (insufficient guaranteed clearance) and its fix are unambiguous
   either way.
3. **A second, unnamed defect was found and fixed**: the static per-page
   iframe `height` was already insufficient pre-WP16 (Exercise 2 clipped by
   61–1300px depending on width), and the same class of shortfall existed
   on all 5 other activities, most severely on mobile widths. Fixed
   project-wide via a `ResizeObserver` + `postMessage` mechanism
   (§5) rather than a per-page static number, since the book theme's own
   layout is not monotonic in viewport width and a static breakpoint would
   have been fragile. This is a bigger change than "Plotly axes,
   backgrounds, spacing" strictly implies, but WP16 §2.5 explicitly
   anticipates exactly this ("update the existing embedding-height
   mechanism … rather than clipping content"; "or a shared ResizeObserver
   if necessary").
4. **10 PNG screenshots (~2.1MB) were committed** to
   `WPs/reports/wp16_screenshots/` as visual evidence — no prior WP report
   committed images; flagging the convention change in case you'd rather
   these live outside git history.
5. No WP17 was started.
