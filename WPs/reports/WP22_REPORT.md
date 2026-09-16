# WP22 Report — Dark-Mode Plotly Repair

Spec: [`WPs/WP22_DARK_MODE_PLOTLY_REPAIR.md`](../WP22_DARK_MODE_PLOTLY_REPAIR.md)
Changelog: [`WP22_EXACT_CHANGELOG.md`](WP22_EXACT_CHANGELOG.md)
Branch: `fix/published-dark-mode-plots`
Starting SHA: `0a28301ceee3c4a3a8891158a73ac0754b4b6150`
Spec checkpoint commit: `4f9bc7014625ed0a50df938f393b957a25c04037`

## 1. Confirmed root cause

`interactive/src/components/plotly-policy.ts`'s `getPlotlyTheme()` computed
the theme exactly once, by calling `window.matchMedia("(prefers-color-scheme:
dark)")` on the **iframe's own window** — the OS/browser preference only.
Every component then called it **once, at `mount()` time**, and cached the
result (and every color derived from it) in an outer `const`, never
re-evaluated afterward. `interactive/src/styles.css` had the identical bug:
its dark palette lived only under `@media (prefers-color-scheme: dark)`.

The published Jupyter Book (pydata-sphinx-theme) does not use
`prefers-color-scheme` for its own toggle at all. Its `theme-switch-button`
calls `setTheme(mode)`
(`.venv/lib/python3.12/site-packages/pydata_sphinx_theme/assets/scripts/pydata-sphinx-theme.js`),
which sets `document.documentElement.dataset.mode` (the reader's choice:
`"light"`/`"dark"`/`"auto"`) and `document.documentElement.dataset.theme` (the
resolved value, always `"light"`/`"dark"`) on the **parent** document. Toggling
it does not touch `prefers-color-scheme` — that only reflects the OS. Each
activity iframe is same-origin with the book, so it can read
`window.parent.document.documentElement.dataset.theme`, but nothing in the
codebase did.

Net effect: whenever the reader's book-selected theme differed from the
browser/OS preference (the *normal* case — clicking the book's own moon icon
does not change the OS), every chart silently kept rendering whichever theme
happened to be true at mount time, forever, regardless of what the reader
selected.

### Why light mode "worked"

Light mode is the default resolved theme for `auto` against a light OS
preference — the overwhelmingly common case in casual browsing/CI — so most
manual light-mode checks simply never crossed the code path that was broken.
Nothing about light-mode rendering itself required any theme resolution to be
correct; a `const theme = getPlotlyTheme()` that is wrong is invisible until
something asks it to be something other than its accidental default.

### Reproduction (built book, real HTTP, §2 of the spec)

Diagnostic Playwright run against `book/_build/html` served over
`http://localhost:4174`, OS/browser forced to `light` via
`page.emulateMedia({ colorScheme: "light" })` (so the only way `dark` can
appear anywhere is via the book's own toggle), against
`chapters/chapter_01/exercise_01.html`'s histogram, before any WP22 code
change:

| State | Parent `data-theme` | Widget `body` background | Histogram bar fill |
|---|---|---|---|
| 1. Initial load (book `auto`) | `light` | `rgb(255,255,255)` (correct: light) | `rgb(42,111,158)` (correct: light) |
| 2. Click toggle → book dark, OS still light | `dark` | `rgb(255,255,255)` (**wrong** — still white) | `rgb(42,111,158)` (**wrong** — still light-theme blue) |
| 3. Reload page while dark is selected | `dark` | `rgb(255,255,255)` (**wrong**) | `rgb(42,111,158)` (**wrong**) |

The drag layer (`.draglayer rect`) was already computed as fully transparent
(`fill: rgba(0,0,0,0)`, `stroke: none`) in every one of these three states —
see §5.

Screenshot evidence: [`wp22_screenshots/before-dark-book-light-widget.png`](wp22_screenshots/before-dark-book-light-widget.png)
— book chrome fully dark, histogram card rendering as a stark white rectangle
with light-blue bars and light gridlines in the middle of it. This — not a
literal "light-gray" hex value — is what the deployed bug report's "light-gray
plot background… thick gray rectangles" almost certainly describes: the
widget's own light-themed white card and border sitting inside an otherwise
dark page.

## 2. Every affected plotting component

All nine components that render a Plotly figure (`registry.ts`'s full list;
`table-inspection.ts` has no Plotly and was not touched):

- `histogram.ts` (EDA histogram)
- `correlation.ts` (EDA correlation explorer)
- `regression-compare.ts` (Exercise 2 feature-set comparison)
- `knn-abc.ts` (Exercise 3 A/B/C KNN evaluation)
- `knn-explore.ts` (Exercise 3 KNN exploration + bias/variance, 3 Plotly figures)
- `classification-threshold.ts` (Exercise 4 ROC curve)
- `classification-imbalance.ts` (Exercise 4 imbalance bar chart)
- `retention.ts` (EDA retention-by-site bar chart)
- `runtime-smoke.ts` (developer smoke-test activity — fixed for consistency, not course content)

## 3. Centralized theme mechanism

New `interactive/src/theme.ts` (see WP22_EXACT_CHANGELOG.md for the full
contract). One detection/observation module, consumed in two places:

1. `main.ts`, once at boot, mirrors the resolved theme onto this document's
   own `data-theme` attribute (so `styles.css`'s `[data-theme]` rules —
   page/card background, borders, text — track the book) and keeps it synced
   for the life of the page.
2. Each Plotly component's own `mount()` subscribes independently, reassigns
   its local `theme` variable, and re-invokes its own draw function(s) — so
   every chart redraws with the new palette. `destroy()` calls the returned
   unsubscribe function alongside the existing `Plotly.purge(...)` calls.

No component re-implements theme detection; all of them call
`getActiveTheme()`/`subscribeToThemeChanges()` from `theme.ts` and
`getPlotlyTheme(theme)` from `plotly-policy.ts`.

### A real bug caught during implementation, not just review

The first version of `theme.ts` attached a MutationObserver to **this
document's own** root unconditionally (as a defensive fallback for
standalone/test use). `main.ts`'s callback writes the resolved theme onto
that very attribute. When embedded, that created a synchronous feedback
loop — the own-document observer would fire on `main.ts`'s own write, recompute
the theme (unchanged, since the parent is the source of truth), and write it
again, forever. This surfaced immediately as 100%+ CPU pegged in the
Playwright browser process during the built-book test (§7) — not a silent
correctness bug, but exactly the kind of thing manual light-mode checking
would never catch either. Fixed two ways, both now in `theme.ts`: (1) the
own-document observer is only attached when there is **no** parent to defer
to; (2) `subscribeToThemeChanges` deduplicates — it only calls back when the
newly resolved theme actually differs from the last one notified, so even a
redundant same-value write cannot re-trigger a subscriber.

## 4. Explicit light/dark Plotly palettes

`plotly-policy.ts`'s `getPlotlyTheme(theme: Theme): PlotlyTheme` is now a
pure function of the resolved theme (previously it called `matchMedia`
itself — the root cause). Explicit fields: `axisColor`, `gridColor`,
`legendBg`, `legendText`, `annotationText`, `markerPrimary`, `diagonalLine`.
`buildPlotLayout` wires these into `font.color`, `xaxis`/`yaxis`
`gridcolor`/`linecolor`/`tickcolor`, and the legend's `bgcolor`/`font.color` —
the legend background/text was previously unset anywhere (Plotly's own
default legend chip is an opaque near-white, unreadable on a dark card).
`paper_bgcolor`/`plot_bgcolor` remain intentionally transparent in both
themes — see the design note in `plotly-policy.ts`: the genuinely dark plot
surface comes from the widget card (`body`'s `--bg`, now theme-synced, §3)
showing through, not from Plotly's own background fill. This was a
deliberate, pre-existing (WP16) design choice this WP kept, not something
introduced here.

Two colors that were byte-for-byte duplicated across three independent files
(`regression-compare.ts`, `knn-abc.ts`, `knn-explore.ts`) — the "observed vs
predicted" marker color and the dashed "perfect prediction" reference-line
color — are now defined once as `theme.markerPrimary`/`theme.diagonalLine`.
`classification-imbalance.ts`'s bar-chart percentage labels
(`textposition: "outside"`) and plot title now get an explicit
`textfont`/`font.color` instead of relying on Plotly's own default cascade,
per the spec's explicit call-out of trace/label colors left to defaults.

Light mode is visually unchanged (same hex values as before this WP; the only
change to the light path is the new explicit legend/axis-line/tick colors,
which match what was already the effective rendered color). No data, metric,
selected value, or model result changes with theme — every color change is in
presentation-layer code only (`plotly-policy.ts`, the per-component `marker`/
`line`/`textfont` objects, `styles.css`); nothing that computes histogram
bins, correlations, model predictions, or metrics was touched.

## 5. Plotly drag layers

Computed-style inspection against the built book (§1's reproduction, and
again in the §7 automated spec) found `.draglayer rect` already
`fill: rgba(0,0,0,0)` / `stroke: none` in every state tested — light, dark,
and reload-in-dark — under the existing WP16 policy (`dragmode: false` +
`fixedrange: true` on both axes + `displayModeBar: false` + `scrollZoom:
false` + `doubleClick: false`, all already in place and untouched). No
currently-visible drag-rectangle defect was reproduced.

Per the spec's explicit request to eliminate this class of bug regardless,
`styles.css` adds one narrowly-scoped hardening rule:

```css
.widget-plot .draglayer rect {
  fill: transparent !important;
  stroke: none !important;
}
```

`!important` is necessary for this rule to do anything: Plotly sets these as
plain (non-`!important`) inline styles, which only an `!important` stylesheet
rule can override. Scoped to `.widget-plot .draglayer rect` only — never a
global `svg rect` rule, which would repaint histogram bars, heatmap cells,
and legend swatches too. No `forced-color-adjust` was added anywhere (no
OS high-contrast-mode issue was found or reported, and blanket-applying it
would be an accessibility regression with no observed problem to justify
it). No Dark Reader lock was added; Dark Reader was never implicated by any
reproduction step.

## 6. Verification results

### Light mode
Unchanged from the pre-WP22 correct design (§4). Confirmed both by the
existing `e2e/plot-visual-policy.spec.ts`-style computed-style checks folded
into the new spec's "light mode" assertions, and visually.

### Dark mode (book toggle, OS forced light throughout)
Widget card background, histogram bar color, correlation-scatter marker
color, and gridline color all now match the intended dark palette; drag-layer
rects remain transparent. Screenshot:
[`wp22_screenshots/after-dark-book-dark-widget.png`](wp22_screenshots/after-dark-book-dark-widget.png)
— same page as the "before" screenshot, same OS-light forcing, book toggled
to dark: the widget card is now genuinely dark, bars are the intended lighter
blue, gridlines are subdued but visible, no stray light rectangle.

### Reload while dark is already selected
The single most direct test of the actual bug (theme used to be read once at
mount): reloading the page with the book's dark mode already selected (mode
persisted via the book's own `localStorage`, OS still light) now renders the
dark palette from the very first paint. Confirmed automatically (§7) and
manually via the diagnostic script.

### Dark → light → dark again
Confirmed automatically: `e2e-book/chapter01-dark-mode.spec.ts`'s second test
clicks the toggle four times (`auto→dark→light→auto→dark`) and asserts the
histogram bar color matches the correct palette after each dark state.

## 7. Tests, builds, and outcomes

Bounded verification, in the order the spec requires (§8). Each command's
outcome:

1. **Focused frontend unit/component tests**
   `npx vitest run tests/theme.test.ts tests/plotly-policy.test.ts` →
   13/13 passed.
   Full unit suite (`npm run test:unit`) also run as a non-regression check
   (not required by §8, but cheap and confirms nothing else broke):
   315/315 passed across all 21 test files.

2. **Frontend typecheck**
   `npm run build` (which runs `tsc --noEmit` first) → clean, no errors.

3. **Production interactive build**
   `vite build` → succeeded, 42 modules transformed
   (`book/_static/widgets/app/assets/index-DhCEOxCQ.js`). The pre-existing
   >500kB chunk-size warning is Plotly's own bundle size, unrelated to this
   WP and present before it too.

4. **Jupyter Book build**
   `jupyter-book build book` (from `.venv`) → "build succeeded, 1 warning"
   (the warning is pre-existing and unrelated — not investigated per the
   spec's bounded-verification instruction to touch only what a failing gate
   requires).

5. **Focused built-book dark-mode browser tests**
   `npx playwright test --config playwright.book.config.ts
   e2e-book/chapter01-dark-mode.spec.ts` → 2/2 passed, ~5–7s.

   **Confirmed this spec fails against the pre-WP22 code**, per the spec's
   explicit requirement: `git stash` (tracked-file changes only — the new
   test file and `theme.ts` are untracked and stayed in place), rebuilt the
   widget bundle and book with the reverted code (41 modules, no `theme.ts`),
   reran the same spec → **2/2 failed**, with exactly the expected symptom
   (`histogram dark: widget card background` expected `rgb(28,26,38)`,
   received `rgb(255,255,255)`; bar color expected the dark blue, received
   the light-theme blue). `git stash pop` restored the fix; both builds were
   rerun with the fix in place and reconfirmed green (2/2 passed) before
   moving on.

### One environment-specific test-authoring issue (not a product bug)

This sandbox's headless Chromium cannot reach whatever external resource
(likely a font or an icon on GitHub's or Google's CDN) the book's chrome
references, so `page.goto(url)`/`page.reload()` with the default `waitUntil:
"load"` — and even `"domcontentloaded"` — never resolved, hanging
indefinitely (confirmed: plain `curl` to the same local URL is instant; the
page's own inline scripts visibly ran, printed to `console`, and finished
well within a few seconds). The final spec navigates with `waitUntil:
"commit"` and then polls for the book's own theme script having actually run
(`document.documentElement.dataset.mode !== ""`) before touching anything,
rather than trusting a lifecycle event this environment cannot reliably
fire. This is a property of the sandbox network policy for headless browser
processes, not of the interactive app or the published site — the same URLs
load normally in an ordinary browser. Documented here as the "remaining
browser-specific uncertainty" item requested by the spec (§12 below).

Two secondary fixes needed along the way, both narrow and documented inline
in the spec file with the WP22 comment: (1) each activity iframe is
`loading="lazy"` (WP16), so `page.locator(...).scrollIntoViewIfNeeded()` —
which waits for the element's bounding box to be *stable* — could hang
indefinitely against `activity-resize.js`'s continuous height nudging; a
plain `locator.evaluate(el => el.scrollIntoView())` (no stability wait) is
used instead. (2) the per-test default 30s Playwright timeout is too tight
for a spec that drives two iframes through three-to-four theme states plus a
full reload; raised to 90s via `test.describe.configure({ timeout: 90_000
})`.

## 8. Preserved / not touched

No notebook teaching content, dataset, participant split, model parameter,
metric, interaction default, existing student question, or portable-notebook
calculation was changed. `table-inspection.ts` (no Plotly) untouched. No
`.ipynb` file was edited. Untracked pre-existing reports
(`WPs/reports/WP16_ARCHITECT_REPORT.md`, `WPs/reports/WP21_DEPLOYMENT_REPORT.md`)
were not added, modified, deleted, or moved.

## 9. Commit / push / deploy

Implementation commit SHA: see the final chat response to Yoav (not
duplicated here, to avoid amending this report merely to insert its own
commit's SHA — matching the convention already established in
`WP20_REPORT.md`).

**Nothing was pushed to any remote and nothing was deployed.** No GitHub
Actions run was triggered or monitored. All work is local to the
`fix/published-dark-mode-plots` branch.

## 10. Remaining uncertainty

- **Browser-specific**: this WP's automated verification ran on Chromium
  only (the project's existing Playwright config default). Safari/WebKit and
  Firefox were not tested; `theme.ts`'s `MutationObserver`/`matchMedia`
  usage is standard and should behave identically, but that is not the same
  as having actually verified it.
- **Sandbox networking**: as documented in §7, this development sandbox
  cannot reach some external resource the book's chrome references, which
  required a navigation-strategy workaround in the test itself. This should
  not affect real users (ordinary browsers with normal network access), but
  it does mean this WP's own verification never exercised a fully "everything
  the browser would normally fetch" page load.
- **Other browser pages/activities**: the built-book spec covers Chapter 1's
  histogram and correlation scatter specifically (per the spec's "at least
  one histogram and one scatterplot" minimum). The remaining seven components
  share the identical `theme.ts`/`plotly-policy.ts` mechanism and were
  verified via the focused unit tests (§7.1) and a full production build, but
  were not each individually re-verified against the built book's other
  chapter pages — doing so was judged out of scope for this WP's bounded
  verification budget (§8 of the spec explicitly caps this to "focused"
  gates).

  **Addressed by the cross-chapter verification addendum below.**

---

## Cross-chapter verification addendum

Requested because one of the original bug screenshots showed the Exercise 3
KNN A/B/C activity specifically, and — as §10 above already flagged — no
automated built-book spec had checked it, or any Exercise 2/3/4 activity,
before this addendum. The implementation itself (§2–§4 above) already applied
identically to every Plotly component; this addendum only extends the
*automated verification*, per the note in §10.

### Activities checked

All against the **built** Jupyter Book (`book/_build/html`, already current
for this branch — no rebuild was required) over real HTTP
(`http://localhost:4174`), OS/browser color scheme forced to `light`
throughout via `page.emulateMedia`, so the only way "dark" can appear
anywhere is via the book's own toggle button — the exact mismatch the
pre-WP22 code could not handle.

| Exercise | Activity | Figures checked |
|---|---|---|
| 2 | `regression-compare` | Both panels (`regression-A-plot`, `regression-B-plot`) |
| 3 | `knn-abc` | **All three panels** — A (valid), B (resubstitution), C (invalid/leakage) |
| 3 | `knn-explore` | The observed-vs-predicted scatter (`knn-scatter-plot`) |
| 4 | `classification-threshold` | The ROC plot (`cls-roc-plot`) |
| 4 | `classification-imbalance` | The accuracy-comparison bar chart (`cls-imb-plot`) |

8 distinct Plotly figures across 5 components, 3 test cases (one per exercise
page, each doing a single navigation + single dark-toggle click, then
checking every activity iframe already present on that page).

### Exact assertions, per figure

1. No `[data-testid="widget-error"]` element present in the iframe.
2. The iframe's own `document.documentElement.getAttribute("data-theme")` is
   `"dark"` (set by `main.ts`'s theme bridge, §3 of the main report).
3. `getComputedStyle(document.body).backgroundColor` is `rgb(28, 26, 38)`
   (`#1c1a26`, the dark `--bg` token).
4. Plotly's own `_fullLayout.paper_bgcolor` and `.plot_bgcolor` are both
   `"rgba(0, 0, 0, 0)"` — transparent by design in both themes (§4 of the
   main report); the dark surface comes from the card underneath.
5. The first `.gridlayer path`'s computed `stroke` is `rgb(58, 58, 58)`
   (`#3a3a3a`); the first axis tick text's computed `fill` is
   `rgb(201, 201, 201)` (`#c9c9c9`).
6. At least one principal data mark is present and its resolved color — read
   from Plotly's own `_fullData[i].marker.color`/`.line.color`, not computed
   SVG style (see "why `_fullData`" below) — is not black
   (`rgb(0, 0, 0)`/`#000000`/`#000`/`black`), and additionally matches the
   *exact* expected dark palette value for that trace (e.g.
   `rgba(120,170,210,0.55)` for every scatter marker sharing
   `theme.markerPrimary`, `#d98b5f` for every dashed diagonal reference line,
   `#8fb8da`/`#b0b0b0`/`#f0915c` for the ROC curve/chance line/threshold
   marker, `#5a9bd4`/`#d9a441` for the imbalance chart's two bars).
7. Every `.draglayer rect`'s computed `fill` is `rgba(0, 0, 0, 0)` (or
   `transparent`) and `stroke` is `none` (or `rgba(0, 0, 0, 0)`).
8. (KNN A/B/C only) All three panels' background, gridline color, tick-text
   color, and marker-color *set* are asserted equal to each other — a
   stronger, structural version of "same dark styling" than a visual
   comparison would give.

### Why `_fullData` instead of computed SVG style

`regression-compare.ts`, `knn-abc.ts`, and `knn-explore.ts`'s scatter panel
all use Plotly's `scattergl` trace type (confirmed by reading each file's
`type: "scattergl" as const`), which renders through WebGL — there is no
per-point `<path class="point">` SVG element whose `fill` a
`getComputedStyle` check could read, unlike the regular `"scatter"` type used
by Exercise 1's correlation activity. Reading `marker.color`/`line.color` off
`_fullData` — Plotly's own fully-resolved trace data, what it actually used
to draw the figure — works identically for every trace type (`scattergl`,
`scatter`, `bar`) and is a more direct verification of the same code path
`plotly-policy.ts` feeds than a rendered-pixel/SVG-attribute check would be.

### Results

**3/3 passed**, runtime 5.4s for the corrected run (all three exercise pages
together). First run: **3/3 failed**, all three at the identical assertion
(`paper_bgcolor`/`plot_bgcolor` transparency check) with the identical cause.

### Implementation correction required

One bounded correction, per the spec's bounded-execution rule. The new
spec's own expected string for Plotly's transparent background was
`"rgba(0,0,0,0)"` (no spaces — the literal string `plotly-policy.ts` passes
into `buildPlotLayout`'s `paper_bgcolor`/`plot_bgcolor`), but Plotly
normalizes it internally to `"rgba(0, 0, 0, 0)"` (with spaces) before storing
it on `_fullLayout`. This is a formatting mismatch in the new test's own
expectation, not a product defect: every other assertion in every test
(theme sync, all five palette-color checks, drag-layer transparency, the
three-panel structural-equality check) already passed on the first run: only
this one string literal was wrong, and identically wrong in all three tests
since they share the same `assertDarkFigure` helper. Fixed by adding the two
spaces; the single allowed rerun passed 3/3, confirming this was purely a
test-authoring issue.

No change was made to any implementation file
(`theme.ts`/`plotly-policy.ts`/any component/`styles.css`/`main.ts`) as part
of this addendum — the spec in §1 of this addendum ("preserve the current
implementation... do not redesign the theme mechanism unless these tests
expose a real defect") was followed: no real defect was exposed.

### Commit / branch state

- Implementation commit SHA (the WP22 core fix, unchanged by this addendum):
  `6bce45c88268559efb4c8ca95cfaaac71a66bb7c`
- Addendum commit SHA / final local branch SHA: see the final chat response
  to Yoav (not duplicated here, to avoid amending this report merely to
  insert its own commit's SHA — same convention as `WP20_REPORT.md` and the
  main WP22 report above).

**Nothing was merged, pushed, or deployed.** All work stays local to
`fix/published-dark-mode-plots`. No GitHub Actions run was triggered or
monitored. The pre-existing untracked `WPs/reports/WP16_ARCHITECT_REPORT.md`
and `WPs/reports/WP21_DEPLOYMENT_REPORT.md` were not touched.
