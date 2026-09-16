# WP23 Report — Merge and deploy dark-mode Plotly repair

**Date:** 2026-09-16
**Status:** `COMPLETED`

## 1. SHAs

| Label | SHA |
|---|---|
| Starting feature-branch SHA (before this WP) | `e5d6ad7fedf519636a2ae047c42de389f16a2966` |
| WP23 specification commit (initial) | `af3e9ea00102b3f46852b13e1709acf445e33d6f` |
| WP23 correction commit (verified starting state) | `1d4629e0dcffcc44925918d4195dad8c13056cc5` |
| **RELEASE_SHA** (merge commit, deployed to GitHub Pages) | `4237ce7b3528526066bcda03e6e94545ca29ad14` |
| Starting `origin/main` SHA | `0a28301ceee3c4a3a8891158a73ac0754b4b6150` |
| Starting local `main` SHA (WP22 doc checkpoint, pre-existing, unpushed) | `4f9bc7014625ed0a50df938f393b957a25c04037` |
| **DOCUMENTATION_SHA** (this report's commit, local-only) | recorded in `git log -1` after commit; see final `git status` below — this commit is intentionally **not pushed** |

## 2. Pre-merge verification

Local `main` was found one commit ahead of `origin/main` (`4f9bc70`, the WP22 specification-doc checkpoint, no implementation code). Per explicit user direction, this was confirmed to be an authorized, harmless checkpoint (option 1: proceed without resetting local `main`). Four checks were run and all passed before merging:

1. `origin/main` (`0a28301...`) is an ancestor of local `main` — **confirmed**.
2. `4f9bc70...` is an ancestor of `fix/published-dark-mode-plots` — **confirmed**.
3. `git diff origin/main..main --stat` before merge showed only the WP22 specification file (253 insertions, no other files) — **confirmed**.
4. The WP23 specification commit contained only its intended file — **confirmed**.

Full detail in `WPs/WP23_MERGE_DEPLOY_DARK_MODE_REPAIR.md` §"Corrected starting-state determination".

## 3. Merge

`git merge --no-ff fix/published-dark-mode-plots -m "Merge WP22 dark-mode Plotly repair"` — **clean, no conflicts**.

Result: `RELEASE_SHA = 4237ce7b3528526066bcda03e6e94545ca29ad14`.

Post-merge confirmation:
* Branch: `main`.
* Working tree: no modified/staged tracked files.
* Untracked files: only `WPs/reports/WP16_ARCHITECT_REPORT.md` and `WPs/reports/WP21_DEPLOYMENT_REPORT.md` (pre-existing, untouched).
* `git diff origin/main..main --stat`: 23 files changed (WP22 implementation — `interactive/src/theme.ts`, `interactive/src/components/*.ts`, `interactive/src/main.ts`, `interactive/src/styles.css`, two new e2e specs, two new unit-test files — plus WP22/WP23 documentation and two before/after screenshots). No unexpected files.

## 4. Focused post-merge verification

Build steps (required — build artifacts are gitignored and were not present from any prior session against the merged tree):

* `cd interactive && npm run build` (`tsc --noEmit && vite build`) → clean, 42 modules, `book/_static/widgets/app/assets/index-DhCEOxCQ.js` (byte-identical to the hash recorded in the WP22 report).
* `source .venv/bin/activate && jupyter-book build book` → "build succeeded, 1 warning" (the warning is pre-existing/unrelated, per WP22's own note). Confirmed the built `chapter_01/exercise_01.html` references the freshly built `index-DhCEOxCQ.js` bundle.

Focused tests (webServer auto-started/stopped by Playwright's own `playwright.book.config.ts`, `reuseExistingServer` disabled since no server was already running):

```
npx playwright test --config playwright.book.config.ts \
  e2e-book/chapter01-dark-mode.spec.ts \
  e2e-book/wp22-cross-chapter-dark-mode.spec.ts
```

**Result: 5/5 passed, 7.1s.** Coverage (per the spec's own assertions):
* Exercise 1: light → dark → reload-while-dark → light full cycle (histogram + correlation), plus a separate dark → light → dark(auto) → dark redraw-correctness test.
* Exercise 2: regression comparison, both panels (A/B), initial dark load.
* Exercise 3: KNN A/B/C all three panels + KNN exploration scatter, initial dark load.
* Exercise 4: classification threshold ROC + class-imbalance, initial dark load.

No test failures; no server-start retry was needed.

## 5. Push

`git push origin main` → **succeeded**: `0a28301..4237ce7  main -> main`.

Confirmed via `git fetch origin main && git rev-parse origin/main` → `4237ce7b3528526066bcda03e6e94545ca29ad14`, matching `RELEASE_SHA` exactly.

**Exactly one push occurred.** No force push, no amend, no second push, no additional product commit.

## 6. GitHub Actions deployment

* Workflow: "Build and deploy Jupyter Book".
* **Run ID: `35104013846`**, found on the first check (`gh run list`), `headSha` matched `RELEASE_SHA` exactly — no 20-second wait was needed.
* Watched with one continuous `gh run watch 35104013846 --interval 20 --exit-status` call (no background process, no scheduled wakeup, no repeated `gh run view`, no manual polling loop).
* **Outcome: success.** All steps green, including "Type-check and unit-test the frontend", "Build the interactive widget app", "End-to-end test the standalone widget app", "Build Jupyter Book", "Fail on notebook execution errors", "End-to-end test the built Chapter 1 page", "Execute the portable notebook outside the repository", "Publish website".
* **Duration: 3m56s** (`build-and-deploy` job).
* One pre-existing, unrelated CI annotation: Node.js 20 deprecation warning (`actions/checkout@v4`, `actions/setup-node@v4` forced onto Node 24) — not a failure, not WP22/WP23-related.
* The workflow was **not** rerun.

## 7. Live verification (production, light-OS-emulated browser)

All four pages returned **HTTP 200** (`curl` preliminary check):
* `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html`
* `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_02/exercise_02.html`
* `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_03/exercise_03.html`
* `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html`

Actual dark-mode verification was done with a real browser (Playwright/Chromium), **not** `curl` alone, per the requirement. `page.emulateMedia({ colorScheme: "light" })` was set on every context, so dark mode could only originate from the book's own theme-toggle control, never from the OS/browser preference. Fresh Playwright browser contexts were used throughout (no persisted disk cache from any prior run), satisfying "cache-busting where practical"; `Cache-Control`/`Pragma: no-cache` request headers were also set.

Since `playwright.book.config.ts` hardcodes a local `baseURL`/`webServer` with no environment override, a temporary out-of-repo Playwright config (`/private/tmp/.../wp23-live/playwright.prod.config.ts`, outside the repository, never committed) was created that reuses the **existing, unmodified** WP22 spec files (`chapter01-dark-mode.spec.ts`, `wp22-cross-chapter-dark-mode.spec.ts`) with `baseURL: "https://yoavmp.github.io"` and no local `webServer`.

```
npx playwright test --config <scratchpad>/playwright.prod.config.ts
```

**Result: 5/5 passed, 11.4s**, run against production, first attempt (no retry needed — the site was not stale).

### Per-exercise results

**Exercise 1** (`chapter01-dark-mode.spec.ts`, both tests):
* Widget root/card background switched to the dark palette (`rgb(28, 26, 38)`) on toggle.
* Histogram bars remained visible (dark blue `rgb(90, 155, 212)`).
* Correlation points remained visible (dark palette `rgb(143, 182, 204)`).
* Gridlines subdued but readable (`rgb(58, 58, 58)`).
* Drag-layer rectangles remained transparent (fill/stroke asserted `rgba(0,0,0,0)`/`transparent`/`none`).
* **Reload while dark mode is selected: PASS** — reloading with dark already persisted (`localStorage`, OS still emulated light) rendered the dark palette from the first snapshot after `waitForBookReady`, confirming no first-paint fallback to light.
* Dark → light → dark(auto, resolves dark against light OS... resolves light) → dark cycle: all transitions redrew the correct palette each time.

**Exercise 2** (`wp22-cross-chapter-dark-mode.spec.ts`):
* Both regression-comparison panels (A/B) used the dark palette (transparent paper/plot background over the dark card, dark gridlines/ticks).
* Data marks (`rgba(120,170,210,0.55)`) and diagonal reference lines (`#d98b5f`) remained visible in both panels.
* No light-gray plot margins or axis bands (paper/plot background confirmed transparent in both panels — nothing to render as a light rectangle).

**Exercise 3 — KNN A/B/C (the activity specifically named in the original bug report):**
* **All three panels (A/B/C) confirmed using the dark palette** (dark card background, transparent paper/plot background, dark gridlines, dark tick text).
* **All three observed-vs-predicted point sets visible** (`rgba(120,170,210,0.55)` marker color present in each panel).
* **All three diagonal reference lines visible** (`#d98b5f` present in each panel).
* **No light-gray margin/axis rectangles** (transparent paper/plot background confirmed in each panel).
* **Drag layers transparent** in all three panels.
* **All three panels styled identically** — background, gridline color, tick color, and marker-color set were asserted equal across panels A, B, and C.
* KNN exploration scatterplot: also confirmed dark palette, validation points visible, diagonal reference line visible.

**Exercise 4:**
* ROC plot: dark palette, readable; ROC curve (`#8fb8da`), chance line (`#b0b0b0`), and selected-threshold marker (`#f0915c`) all present.
* Class-imbalance plot: dark palette; model-accuracy bar (`#5a9bd4`) and baseline-accuracy bar (`#d9a441`) both present (percentage-label rendering is drawn from the same trace data verified here; no separate assertion needed beyond the existing WP22 spec's marker-color checks).

### Supplementary checks (console errors, interactive-control operability)

The reused WP22 specs assert render success (`data-render-count`) and the explicit absence of `[data-testid="widget-error"]`, but do not capture raw browser console output. A small supplementary script (also outside the repository, not committed) was run once against production for Exercises 1, 3, and 4, in light-OS-emulated fresh browser contexts, toggling to dark mode and then exercising one interactive control per page (`histogram-bins`, `knn-k-slider`, `cls-threshold-slider` — each a native `<input type="range">`, changed programmatically and confirmed the value actually changed):

* **All three controls confirmed operable** (slider value changed after interaction).
* Two console/page messages were observed on **every** page, including pages with no widgets at all (confirmed by checking `book/_build/html/intro.html`, which has zero interactive activities):
  1. `console.error`: `"Got invalid theme mode: . Resetting to auto."` — pydata-sphinx-theme's own bootstrap script, fired on a fresh browser context with no `localStorage` theme key yet set. Pre-existing theme-chrome behavior, unrelated to WP22/WP23.
  2. `pageerror`: `SyntaxError: Identifier 'THEBE_JS_URL' has already been declared` — the built book's `<script>const THEBE_JS_URL = ...</script>` tag is emitted **twice**, byte-for-byte identical, by the Sphinx/Thebe build tooling; confirmed present twice in `intro.html` too (a page with no widgets and untouched by WP22). Pre-existing book-template duplication, unrelated to WP22/WP23.
* **Zero console or page errors referencing any WP22/WP23 source file** (`theme.ts`, `plotly-policy.ts`, `histogram.ts`, `knn-abc.ts`, `knn-explore.ts`, `regression-compare.ts`, `classification-threshold.ts`, `classification-imbalance.ts`, or any widget component) — i.e. **no console error attributable to the widgets**, which is the criterion the WP23 spec sets.

### Interactive controls / runtime errors — summary

* All checked pages: **HTTP 200**.
* All checked iframes: **no runtime error** (`[data-testid="widget-error"]` absent in every snapshot).
* Interactive controls: **operable** (confirmed via the supplementary script on 3 representative controls, plus the reused specs themselves drive the theme-toggle button and confirm redraw on every click).
* **No console error attributable to the widgets** on any page (two pre-existing, book-template-wide, widget-unrelated messages noted above for transparency).

No retry of the live verification was needed — the deployed site was not stale on first check.

## 8. Final repository status

```
## main...origin/main [ahead 1]
?? WPs/reports/WP16_ARCHITECT_REPORT.md
?? WPs/reports/WP21_DEPLOYMENT_REPORT.md
```

(after this report's commit — local `main` is exactly one documentation commit ahead of `origin/main`, which remains at `RELEASE_SHA`).

## 9. Confirmations

* **Exactly one push occurred** (`git push origin main`, `0a28301..4237ce7`). No force-push, no amend, no second push, no additional product commit after it.
* **No workflow rerun.** The single `gh run watch` on run `35104013846` completed naturally (success) well inside the 15-minute bound (3m56s); it was never restarted or polled again afterward.
* **No second deployment.** Only one push occurred, and GitHub Pages deployment is push-triggered, so only one deployment ran.
* **No prolonged/manual polling.** The workflow watch used one continuous `gh run watch --interval 20` call; the live-site verification ran once (no 30-second stale-retry was needed).
* This documentation commit (see `WPs/reports/WP23_EXACT_CHANGELOG.md` for exact file attribution) is **local-only and intentionally not pushed** — pushing it would trigger a second, out-of-scope deployment.
* Unrelated untracked reports (`WP16_ARCHITECT_REPORT.md`, `WP21_DEPLOYMENT_REPORT.md`) were never added, edited, moved, or committed.
