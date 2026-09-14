# WP16 — Repair Plotly axes, backgrounds, spacing, and production parity

## Status: **SUCCESS — deployed and verified live**

WP16 was executed in full: §1–§5 (inventory, implementation, full local
validation gate), §6 steps 1–5 (commit, fetch, fast-forward `main`, merge,
post-merge local re-validation), and — after Yoav's explicit go-ahead —
§6 steps 6–10 (push, monitor the GitHub Pages workflow to success, verify
all three live exercise pages, run the geometry/style Playwright suite
against production, inspect live screenshots). Nothing was force-pushed, no
destructive git command was used.

One genuine hiccup along the way, fully resolved: the first production push
(`9154d7e`, a documentation-only commit — no application code) triggered a
GH Actions run that **failed** one of this WP's own new geometry tests at
the 390px viewport (a real race condition in the *test*, not the app —
see §9.1) and consequently did **not** redeploy the site (the live site
kept serving the prior successful deploy). The race was root-caused, fixed,
and re-verified stable before pushing again. The retry (`ad6a86b`) deployed
cleanly and is now confirmed live and independently re-tested against
production. **Final, deployed, confirmed-live SHA:
`ad6a86b209762b6f1224d5da435dfde308179368`.**

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
| First report commit (pre-approval, deploy withheld) | `9154d7e` |
| Deployment-evidence report commit (pushed; CI failed, did **not** deploy — see §9.1) | `0a025bf` |
| Test-race-fix commit (pushed; CI succeeded, **deployed**) | `ad6a86b` — *"WP16: fix a genuine test race in the new geometry specs"* |
| **Deployed, confirmed-live SHA** | **`ad6a86b209762b6f1224d5da435dfde308179368`** — confirmed via the GH Pages workflow's own `headSha` and re-verified with a fresh Playwright run against `https://yoavmp.github.io` |
| Final report-update commit (this revision) | adds §9.1 (the CI failure/fix) and this final SHA — SHA in the terminal summary |
| `origin/main` before this WP | `92cf7e0` |
| `origin/main` now | identical to local `main` HEAD |

`git status --short --branch` on `main` after the final push: clean, `main`
and `origin/main` identical.

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

## 9. Deployment — **complete**

### 9.1 A real CI failure along the way, root-caused and fixed

The first push (`9154d7e`, report/documentation only — zero application
code) deployed successfully (run `34778058145`, §9.2). A second push
(`0a025bf`, also report-only — a live screenshot and updated deployment
evidence, still zero application code) triggered run `34829127825`, which
**failed** at the "End-to-end test the built Chapter 1 page" step:

```
1) chapter02-visual-policy.spec.ts:35:5 › … @ 390px narrow/mobile › x-axis title stays fully inside the plot's box …
   Expected: >= 12
   Received:    -6
```

Because a step failed, `Publish website` never ran — the live site
correctly kept serving the prior successful deploy (`9154d7e`) rather than
a half-updated one. No user-facing regression occurred at any point.

**Root cause** (not a rendering bug — a race condition in the *test itself*,
introduced by this WP's own new spec files): `data-widget-ready="true"` is
set synchronously the instant a component's `mount()` returns, but
`mount()` starts each panel's `draw()` unawaited (`void panelA.draw()`) —
and the `Plotly.react()` call inside `draw()`, which determines the plot's
*actual* rendered height, resolves asynchronously after that. A test that
reads geometry immediately after `data-widget-ready` can therefore observe
the DOM *before* Plotly has finished rendering — at that moment the
`.widget-compare-panel .widget-plot` div is still sitting at its CSS
`min-height: 300px` placeholder, not its true ~322px rendered height (border
included). The 22px shortfall this implies (16px expected clearance − 22px
= −6px) matches the observed failure almost exactly. A fast, idle laptop
rarely exposes this window; a shared, loaded CI runner does — which is
exactly why it passed in every local run (including several repeated runs)
and in the first CI deploy, and only surfaced on this second CI run.

**Fix** (`ad6a86b`, test-only, zero application-code changes): both new
spec files now wait for each plot's own `data-render-count` attribute
(already set by every component after its `Plotly.react()` call resolves,
and already the exact signal the pre-existing `e2e-book/chapter02.spec.ts`
uses) before reading any geometry, background, or Plotly runtime state.
The "control change" test had the identical gap one step later
(`data-feature-count` is likewise set before the redraw's `Plotly.react()`
resolves) and was fixed the same way. Verified stable across 3 repeated
local runs of both affected files before pushing, then confirmed green in
CI (run `34832347096`, full log below) and re-verified with a fresh
Playwright run directly against the live production site post-deploy
(§9.3) — including the exact 390px case that had failed.

This was caught, diagnosed, and fixed entirely within this WP; it never
reached students, and the final deployed build is unaffected (the fix
touched only the two new Playwright spec files, not any component or CSS).

### 9.2 First successful deploy (documentation-only push, `9154d7e`)

Yoav gave explicit approval to push and deploy. Sequence actually run:

```
git push origin main                    # 92cf7e0..9154d7e  main -> main
gh run list --branch main --limit 5      # new run 34778058145 queued immediately
gh run view 34778058145                  # watched to terminal state
```

`gh run view 34778058145` result:

```
✓ main Build and deploy Jupyter Book · 34778058145
JOBS
✓ build-and-deploy in 3m30s (ID 103779692750)
ANNOTATIONS
! Node.js 20 is deprecated … (pre-existing CI/environment notice, unrelated to this WP, not a failure)
```

Workflow succeeded in 3m30s. `gh run view 34778058145 --json
headSha,conclusion,status` confirms
`{"conclusion":"success","headSha":"9154d7e27745adbe7c2b0278674c470e05ee0820","status":"completed"}`
— the deployed revision is exactly the commit that was pushed. Local `main`
and `origin/main` are identical (`git status --short --branch` → clean, no
divergence).

**Deployed-revision confirmation:**

```
curl -s https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_02/exercise_02.html
  → HTTP 200, references assets/index-2B3eai7_.js (matches this WP's local build hash)
curl -sI https://yoavmp.github.io/ml-neuro-tutorials/_static/activity-resize.js
  → HTTP 200, content-type: application/javascript (the new resize-sync file is live)
```

**Live production Playwright smoke test** (temporary config pointing
`baseURL` at `https://yoavmp.github.io`, no local web server — same pattern
WP15 used, removed after the run): reused
`e2e-book/{chapter01,chapter02,chapter03,chapter02-visual-policy}.spec.ts`
unmodified against production.

```
npx playwright test --config playwright.live.config.ts   # 34 / 34 passed, 26.0s
```

This covers, against the live site:

- **Exercise 1** (Chapter 1, 4 activities): histogram (both controls
  redraw), retention (selection changes text + geometry, suggested-core
  preset), correlation (X/Y/method/group controls, same-variable handling),
  table-inspection (head/tail/sample method switch) — all render, all
  survive a browser refresh restoring configured defaults, all usable at a
  narrow viewport.
- **Exercise 2** (Chapter 2, regression-compare): the full 12-test
  `chapter02-visual-policy` suite at 742px / wide desktop / 390px — x-axis
  title never escapes its SVG box, ≥12px clearance to the ROI-summary
  disclosure, comparison-card background matches the page (not
  `#f4f4f9`), no horizontal overflow, **no iframe clipping** (the dynamic
  resize mechanism confirmed live — see below), and a real ROI-bundle
  control change redraws the figure without disturbing the spacing/
  background policy. Plus the pre-existing control-change and narrow-
  viewport checks.
- **Exercise 3** (Chapter 3, 2 activities): knn-explore (k-slider changes
  metrics + both plots, k = n_fit collapses to the fitting-set mean,
  refresh restores the default k), knn-abc (all three A/B/C panels render
  with the audit-selected default k, k=1 makes B and C exactly R²=1.000) —
  both usable at a narrow viewport.

**Iframe dynamic-resize mechanism, confirmed live** (Exercise 2, 742px):

```
htmlHeightAttr: "1180"   # unchanged pre-JS fallback, exactly as designed
styleHeight:    "1247px" # activity-resize.js overrode it live
scrollHeight:   1245  clientHeight: 1245   # content and iframe height match — no clipping
```

**Live screenshot**: `WPs/reports/wp16_screenshots/ex2-regression-LIVE-742px.png`
— captured directly from `https://yoavmp.github.io/…/exercise_02.html`,
visually identical to the pre-deploy built-book screenshot: white
comparison cards, clean axis titles fully inside their plots, clear gap
before the ROI-summary disclosure.

*(This screenshot and the smoke-test run above were against `9154d7e`,*
*the revision live at that moment. §9.1 covers what happened next; §9.3*
*re-confirms everything below still holds on the final deployed SHA.)*

### 9.3 Final deploy after the test-race fix (`ad6a86b`) — re-confirmed live

```
git push origin main                    # 0a025bf..ad6a86b  main -> main
gh run list --branch main --limit 3      # new run 34832347096 queued immediately
gh run view 34832347096                  # watched to terminal state
```

`gh run view 34832347096 --json headSha,conclusion,status` confirms
`{"conclusion":"success","headSha":"ad6a86b209762b6f1224d5da435dfde308179368","status":"completed"}`,
`build-and-deploy` succeeded in 3m36s, and — unlike the failed run in §9.1 —
`Publish website` ran this time. `curl` against
`chapters/chapter_02/exercise_02.html` still returns HTTP 200 referencing
the same unchanged `assets/index-2B3eai7_.js` (expected: this fix touched
only test files, not the application bundle).

Re-ran the full `chapter02-visual-policy.spec.ts` suite directly against
`https://yoavmp.github.io` (temporary config, removed after use, same
pattern as §9.2):

```
npx playwright test --config playwright.live.config.ts   # 12 / 12 passed, 11.6s
```

All 12 tests passed at all three widths — critically including the exact
"x-axis title … @ 390px narrow/mobile" case that failed in CI (§9.1),
now confirmed passing against the actual live production deployment, not
just in CI.

---

## 10. Live URLs — verified against this deployment

- `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html` — ✅ verified (4 activities)
- `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_02/exercise_02.html` — ✅ verified (the named defect; geometry/background/interaction/resize all confirmed fixed live)
- `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_03/exercise_03.html` — ✅ verified (2 activities)

All three now serve the WP16 build: guaranteed axis-title clearance, page-
matching comparison-card backgrounds, locked axis drag/zoom with hover
preserved, and a dynamically-resizing iframe that no longer clips content
at any tested width.

---

## 11. Screenshots (production build, built Jupyter Book, post-merge)

Saved under `WPs/reports/wp16_screenshots/`, one pair (742px content width /
390px narrow) per activity:

- `ex1-histogram-{742px,390px}.png`
- `ex1-retention-{742px,390px}.png`
- `ex2-regression-{742px,390px}.png`
- `ex3-knn-abc-{742px,390px}.png`
- `ex3-knn-explore-{742px,390px}.png`
- `ex2-regression-LIVE-742px.png` — captured from the actual deployed
  production URL after the push (§9), not the local built book.

All show white/theme-matching plot cards, fully visible axis titles and
legends, no modebar, and (Exercise 2, knn-abc) clean panel-to-panel
comparison with real clearance before the ROI-summary disclosure.

---

## 12. Deviations / items for Yoav's attention

1. **The reported "~15px overlap" did not reproduce as a literal negative
   number in headless Chromium** against the pre-WP16 build — it reproduced
   as an 8px clearance (below the 12px minimum WP16 sets, and flush against
   the plot's own SVG edge). This is consistent with the same root cause
   (no `automargin`) manifesting more severely under different font
   rendering than my test environment's; I did not chase an exact
   pixel-for-pixel reproduction of "15px" specifically since the underlying
   defect (insufficient guaranteed clearance) and its fix are unambiguous
   either way.
2. **A second, unnamed defect was found and fixed**: the static per-page
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
3. **11 PNG screenshots (~2.3MB) were committed** to
   `WPs/reports/wp16_screenshots/` as visual evidence (10 pre-deploy + 1
   live-production) — no prior WP report committed images; flagging the
   convention change in case you'd rather these live outside git history.
4. **A CI run failed and did not deploy** (§9.1) — caused by a genuine race
   condition in this WP's own new Playwright specs (not in the application
   code, and never live), root-caused and fixed in a follow-up commit that
   deployed cleanly. Net effect on the repository: 3 pushes to `main`
   instead of 1 for this WP, and the GH Actions history for `main` shows
   one `failure` entry (run `34829127825`) sitting between two `success`
   entries. Mentioning explicitly since a red run in the Actions tab is
   worth knowing about even though it's already resolved and the live site
   was never affected.
5. **An unrelated file, `WPs/WP22_Targeted_Live_Evidence_Validation.md`,
   appeared in the working tree** partway through this session, describing
   a completely different project (an "exam_generator"/"questions-db" exam
   system with paid LLM API calls). I did not create it, did not act on any
   of its instructions, and did not commit it — it remains untracked. Worth
   checking where it came from; it may be a misplaced file from an
   unrelated session or repository.
6. No WP17 was started.
