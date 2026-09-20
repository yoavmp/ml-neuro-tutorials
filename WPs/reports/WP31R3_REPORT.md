# WP31R3 Report — Chapter 1 Dark-Mode Test Stability and Redeployment

## Status: SUCCESS — Exercises 4–6 are live in production

WP31R2's second CI fix (the Mermaid dependency pin) was confirmed working:
"Build Jupyter Book" passed in run `35510061137`. That run then failed at
"End-to-end test the built Chapter 1 page" on one assertion inside
`chapter01-dark-mode.spec.ts` (85/86 built-book tests passed). This WP
root-caused that failure — a genuine browser-timing race in the test's
lazy-load trigger, not a product defect — corrected it with a state-based
wait, ran the complete bounded gate list, merged, pushed exactly once,
monitored the resulting workflow to a **successful** conclusion, and
completed full production verification. **Exercises 4–6 (Validation and
Cross-Validation, Regularization and Feature Selection, Decision Trees) are
now live at https://yoavmp.github.io/ml-neuro-tutorials/.**

---

## 1. Starting state and Git safety (WP31R3 §1)

* **Starting local `main` HEAD:** `8e2a827bb344e7051405765a527dc24abb2f9d41`
  (short `8e2a827`, "WP31R2: document Mermaid dependency fix and blocked
  redeploy").
* **Starting `origin/main`** (confirmed via one `git fetch origin main`):
  `f12967beaed9a4e16b4930e2881e28435478d388` — the WP31R2 release SHA,
  matching the spec's expected state exactly.
* Local `main` was exactly one documentation-only commit ahead of
  `origin/main`, containing only `WPs/reports/WP31R2_REPORT.md` and
  `WPs/reports/WP31R2_EXACT_CHANGELOG.md` — confirmed via `git diff --stat
  origin/main..HEAD` (443 insertions, 2 files).
* `git status --short --branch` showed only the two whitelisted pre-existing
  untracked legacy reports plus the not-yet-committed WP31R3 specification
  itself. No unexpected modified or untracked file.
* No pull, rebase, reset, stash, or automatic divergence resolution was
  performed — none was needed.
* Branch `fix/wp31r3-chapter01-dark-mode-stability` created from local
  `main`.
* **WP31R3 specification checkpoint commit:** `2d38421` — "WP31R3: add
  specification (initial checkpoint)" — adds only
  `WPs/WP31R3_CHAPTER01_DARK_MODE_STABILITY_AND_REDEPLOY.md` (1 file, 324
  insertions).

## 2. Diagnosis: readiness race, not a product defect (WP31R3 §2–§3)

**Failed CI test:** `chapter01-dark-mode.spec.ts:121`, the
"reload-while-dark" step of the histogram/correlation dark-mode regression
test — `waitForRendered`'s `expect(locator).toHaveAttribute("data-render-count",
/[1-9]/)` timed out at the default 5s, `Received: <element(s) not found>`.
85 of 86 tests in the same CI step passed.

**Reproduction matrix** (built the frontend + book once, `book/_build/html`
served locally via `playwright.book.config.ts`):

| # | Reproduction | Result |
|---|---|---|
| 1 | Single previously-failed test, isolated | Reproduced the exact CI failure on the **first isolated run** (no other test contention at all) |
| 2 | Full `chapter01-dark-mode.spec.ts`, normal workers | Passed (confirms not deterministic) |
| 3 | Same file, 1 worker, `--repeat-each=5` (10 runs) | **3/10 failed**, all at the identical assertion |
| 4 | Entire built-book suite (86 tests), normal CI config | 86/86 passed (a passing full-suite run is expected and does not eliminate the CI trace, per WP31R3 §3) |

**This ruled out "assume flaky because 85 others passed"**: reproducing at 1
worker with zero contention still failed intermittently, so the cause could
not be attributed purely to full-suite parallel resource pressure.

**Root-cause investigation** (three escalating levels of instrumentation,
each documented in the implementation's own comments):

1. A first fix attempt (waiting on the full render-complete state — Plotly
   `_fullData`/`_fullLayout`, `data-render-count`, non-zero bounding box —
   via a `Frame` object obtained through `elementHandle().contentFrame()`,
   with the timeout raised to 15s) **still failed 2/10 times**, with a new,
   more revealing symptom: the diagnostic reported "element does not exist"
   even after the full 15s, and separate instrumentation showed the
   `frame.evaluate()` call itself hanging for **30+ seconds** once the race
   triggered — not a slow render, a stalled cross-frame RPC.
2. Rewriting the wait to poll from the **parent page's own stable execution
   context** (`page.waitForFunction` reading through `iframe.contentDocument`,
   same-origin, no separate `Frame` object) still failed 2/10 times at
   1 worker, even at a 20s timeout, with the diagnostic reporting `[data-testid]
   does not exist inside the iframe document`.
3. Direct instrumentation dumping `iframe.contentDocument.URL` on every poll
   found the actual mechanism: in every failing run, `contentDocument.URL`
   stayed at **`"about:blank"` for the entire wait window** (confirmed to
   20+ seconds in one run) — the iframe's native `loading="lazy"`
   intersection check **never triggered navigation at all**, despite an
   explicit `scrollIntoView()` call. In passing runs, navigation started
   within ~150–900ms of the scroll.
4. Confirmed the fix empirically: re-issuing `scrollIntoView()` on every
   polling attempt (rather than once, before waiting) reliably recovered
   navigation within 1–3 attempts (~600–900ms) in **15/15** repeated trials.

**Conclusion — readiness race, not a product defect:** a single synthetic
`scrollIntoView()` call issued immediately after `page.reload()` can race
the browser's own layout pass; if layout has not stabilized at the exact
moment of the call, the native lazy-load intersection check silently does
not register, and the iframe never starts loading. A real reader's natural
scrolling fires many intersection checks over the course of scrolling and
does not hit this — a single automated `scrollIntoView()` gets exactly one
chance. The widget itself, Plotly, and the theme-sync code are unaffected:
once navigation starts, rendering completes normally and quickly (confirmed
by every passing run, and by the large majority of the intermittent-failure
runs once retried). No evidence of a defect in `histogram.ts`, `theme.ts`,
or any other product file was found; none was changed.

## 3. The correction (WP31R3 §4)

Scoped entirely to `interactive/e2e-book/chapter01-dark-mode.spec.ts` (the
one file exercising the failing pattern; no shared cross-spec helper module
existed to extend, and creating one for every spec using the same
`data-render-count` pattern — over a dozen files — was judged out of the
"narrowest" scope authorized by this WP, since none of those tests actually
failed in CI). Two new functions replace the old `activityFrame` +
`waitForRendered` pair:

* **`waitForActivityNavigationStarted(page, iframeSelector)`** — polls (via
  `page.waitForFunction`, 250ms interval, 10s timeout) for
  `iframe.contentDocument.URL !== "about:blank"`, **re-issuing
  `scrollIntoView()` on every attempt** — the actual fix for the root cause
  above.
* **`waitForActivityRendered(page, iframeSelector, testId)`** — once
  navigation is confirmed started, polls (every animation frame, 20s
  timeout) for the complete render-complete state through
  `iframe.contentDocument`: the plot element exists, Plotly's own
  `_fullData`/`_fullLayout` are populated (the same properties
  `wp22-cross-chapter-dark-mode.spec.ts` already reads for its color
  assertions), `data-render-count` is a valid non-zero marker, and the
  rendered bounding box is non-zero. On failure, reports exactly which
  condition(s) were unmet.
* `activityFrame(page, iframeSelector)` now runs **after** both waits
  confirm the content is ready, so the `Frame` object's execution context is
  already live when the style-snapshot `frame.evaluate()` calls run.
* `snapshotHistogram`/`snapshotCorrelation` were changed to take `page`
  directly (calling both waits internally) instead of a pre-fetched `Frame`,
  collapsing every `activityFrame(...)` + `snapshotX(frame)` call-site pair
  into one `snapshotX(page)` call — a mechanical simplification, no new
  assertions removed or added at the call sites.

**Every existing substantive assertion is unchanged and still executes**:
light/dark/reload-while-dark/restored-light palette checks for both the
histogram (bar fill, background, gridline color) and correlation scatter
(marker fill, background) panels; drag-layer transparency (`dragRectFills`/
`dragRectStrokes`); the `dark → light → dark again` redraw-correctness test.
Nothing was skipped, `.fixme`d, deleted, or had its expected color/threshold
values changed.

**Forbidden fixes not used:** no `waitForTimeout`/sleep; no blanket
`test.setTimeout`/global-timeout increase (both new waits are local,
condition-specific, and justified by the evidence above); no `retries`
added (`playwright.book.config.ts` still has `retries: 0`); no `.skip`/
`.fixme`/conditional bypass; no threshold weakened; `fullyParallel: true`
and the default worker count are unchanged; no production visual code was
touched.

## 4. Regression coverage for the new readiness logic

Rather than a synthetic unit-test harness for the wait helpers in isolation
(judged unnecessary per WP31R3 §5 — "the same behavior can be exercised
through the real Chapter 1 page"), the helpers are proven directly against
the real, built page through the stress reproduction itself:

1. **Does not resolve before the iframe/widget exists**: confirmed by the
   diagnostic path — every timeout before the fix reported the concrete
   unmet condition (`about:blank` / element missing), never a false
   "ready."
2. **Does not resolve when Plotly exists but `_fullData`/`_fullLayout` are
   incomplete**: `waitForActivityRendered` explicitly checks both,
   independent of `data-render-count`.
3. **Resolves once the completed render state is observable**: proven by
   30/30 passing runs of the previously-failing reproduction (§6.3 below).
4. **Times out with a condition-specific message on genuine failure**: both
   waits' `catch` blocks name exactly which condition was unmet (navigation
   never started vs. element/render-count/`_fullData`/`_fullLayout`/
   bounding-box specifically).
5. **All original Chapter 1 dark-mode assertions still execute**: confirmed
   by reading the diff — every `expect(...)` line in both tests is
   unchanged.
6. **No global retry/timeout/threshold/worker setting weakened**: confirmed
   by diffing `playwright.book.config.ts` — unchanged (not touched by this
   WP at all).

## 5–6. Bounded local validation (WP31R3 §5–§6) — all gates passed

| # | Gate | Command | Result |
|---|---|---|---|
| 1 | Previously failing test, isolated | `playwright test ... -g "reload-while-dark"` | ✅ passed |
| 2 | Full `chapter01-dark-mode.spec.ts`, normal workers | `playwright test ... chapter01-dark-mode.spec.ts` | ✅ 2/2 passed |
| 3 | Same file, normal workers, `--repeat-each=5` | ✅ 10/10 passed |
| 3b | Stress: same file, 1 worker, `--repeat-each=15` (the exact reproduction that previously failed 2–3/10) | ✅ **30/30 passed** |
| 4 | Complete built-book Playwright suite, CI config | `playwright test --config playwright.book.config.ts` | ✅ **86/86 passed** |
| 5 | Cross-chapter dark-mode tests | `wp22-cross-chapter-dark-mode.spec.ts` | ✅ 5/5 passed |
| 6 | Chapter 1 built-book tests | `chapter01.spec.ts` + `chapter01-dark-mode.spec.ts` | ✅ 14/14 passed |
| 7 | Focused Exercises 4–6 built-book tests | `chapter04/05/05-visual-policy/06.spec.ts` | ✅ 32/32 passed |
| 8 | Frontend unit-test suite + typecheck | `npm run typecheck` (clean); `npm run test:unit` | ✅ 359/359 passed (vitest only covers `interactive/tests/**`, unaffected by the `e2e-book/` change — run anyway for certainty) |
| 9 | Production frontend build | not run | **unnecessary**: only `interactive/e2e-book/chapter01-dark-mode.spec.ts` changed; vite's build only bundles `src/`, confirmed via `vite.config.ts` |
| 10 | Full offline Python test suite | `python -m unittest discover -s tests -v` | ✅ 707/707, 11 pre-existing skips |
| 11 | Mermaid dependency-contract test + import | `test_deploy_dependency_contract` + `import sphinxcontrib.mermaid` | ✅ 2/2 passed; import resolves |
| 12 | Portable-notebook deterministic check, all chapters | `build_portable_notebook.py --check --notebook all` | ✅ chapters 1–6 up to date (75/43/34/34/47/33 cells) |
| 13 | Clean Jupyter Book build | `jupyter-book clean book --all` then `build book` | ✅ succeeded, same 2 pre-existing warnings (`logo.png`, `book/README.md`); no `.err.log` reports |

No sleeps, weakened assertions, skipped tests, global retries, or repeated
open-ended stress loops were used. Each gate ran exactly once except the
explicitly-authorized stress repeats (§6 item 3b, and the diagnostic
reproductions in §2, all bounded and one-off).

## 7. Merge into local `main` (WP31R3 §7)

* Pre-merge local `main` reconfirmed unchanged: `8e2a827`, clean apart from
  the two whitelisted reports.
* `git merge --no-ff fix/wp31r3-chapter01-dark-mode-stability -m "Stabilize
  Chapter 1 dark-mode rendering test"` — **no conflicts.**
* **`WP31R3_RELEASE_SHA`: `4f0dc06bc4c0c26f8259d4f679832b9e3eb813a4`**
  (parents: `8e2a827` and `3050ee6`).
* Tree-identity proof: `git diff --stat 4f0dc06 fix/wp31r3-chapter01-dark-mode-stability`
  → **empty** — the merged `main` tree is byte-for-byte identical to the
  correction-branch tree.
* Diff from WP31R2's `RELEASE_SHA` (`f12967b`) to `WP31R3_RELEASE_SHA`:
  exactly 4 files — the two previously-local WP31R2 reports, the WP31R3
  specification, and `interactive/e2e-book/chapter01-dark-mode.spec.ts`
  (+231/-41). No notebook, widget, dataset, model, or activity content
  changed.
* No amend, squash, rebase, or history rewrite was performed.

## 8. Push (WP31R3 §8) — exactly once

* `git push origin main` → `f12967b..4f0dc06  main -> main`. Succeeded on
  the first and only attempt.
* Verified with a read-only `git ls-remote origin refs/heads/main`:
  `4f0dc06bc4c0c26f8259d4f679832b9e3eb813a4 refs/heads/main` — matches
  `WP31R3_RELEASE_SHA` exactly.
* **No second push occurred at any point in this WP.**

## 9. GitHub Actions workflow (WP31R3 §9)

* **Workflow:** Build and deploy Jupyter Book
* **Discovery:** found on the **first** of the two permitted bounded queries
  (`gh run list --branch main --limit 5 --json ...`) — already `in_progress`.
* **Run ID:** `35513291539`
* **Triggering SHA:** `4f0dc06bc4c0c26f8259d4f679832b9e3eb813a4` (=
  `WP31R3_RELEASE_SHA`, confirmed via the run's `headSha`)
* **Started:** 2026-09-20T13:22:06Z; **completed:** 2026-09-20T13:28:18Z
  (~6m12s)
* **Watch:** the calling tool's timeout was set to 1,200,000ms (20 minutes)
  before starting `gh run watch 35513291539 --exit-status`, per WP31R3
  §9.5. Executed **exactly once, continuously, to completion** — no cutoff
  this time (unlike WP31R's deviation), no second watch, no parallel
  polling, no scheduled wakeup, no rerun.
* **Result: SUCCESS.** Every step passed:
  ```
  ✓ Set up job              ✓ Install Python dependencies
  ✓ Check out repository    ✓ Set up Node
  ✓ Set up Python           ✓ Install frontend dependencies
  ✓ Type-check and unit-test the frontend
  ✓ Audit production frontend dependencies
  ✓ Build the interactive widget app
  ✓ Validate both committed ABIDE data artifacts (offline)
  ✓ Unit-test the Python scripts (offline)
  ✓ Check the portable notebook is not stale (offline)
  ✓ Install Playwright Chromium
  ✓ End-to-end test the standalone widget app
  ✓ Build Jupyter Book
  ✓ Fail on notebook execution errors
  ✓ End-to-end test the built Chapter 1 page   <- the exact step that failed twice before
  ✓ Execute the portable notebook outside the repository
  ✓ Publish website
  ```
  `build-and-deploy` completed in 6m8s.

## 10. Production verification (WP31R3 §10) — all checks passed

Verified against `https://yoavmp.github.io/ml-neuro-tutorials/` with a
cache-busting query string (curl checks) and fresh Playwright browser
contexts (no prior cache/storage state). Per WP31R3's preference for
"existing production-capable Playwright checks," the repo's own
`e2e-book/*.spec.ts` files were run **unmodified** against production via a
temporary config (`baseURL: https://yoavmp.github.io`, no local
`webServer`) that lived only in the working tree during this WP and was
removed immediately after (never committed); one small additional
throwaway spec covered the few items (nested-CV diagram content, Ex6 static
image, Ex6 reload-while-dark first paint, 390px overflow, console-error
sweep) not already covered by an existing spec — also removed after use,
never committed.

### 10.1 Structure

| Check | Result |
|---|---|
| Exercise 1–3 titles | ✅ "Exploratory Data Analysis", "Regression and Bias-Variance Trade-Off", "Classification and Metrics" |
| Exercise 4 | ✅ "Validation and Cross-Validation" |
| Exercise 5 | ✅ "Regularization and Feature Selection" |
| Exercise 6 | ✅ "Decision Trees" |
| Exercises 7–12 | ✅ present, "placeholder" content confirmed, correct topic titles |
| Exercise 13 | ✅ absent (HTTP 404) |
| Sidebar order | ✅ Exercise 1 → 12 sequential, no gaps |
| Syllabus | ✅ unchanged title, HTTP 200 |

### 10.2 Exercise 4

* All three activities (`validation-stability`, `validation-lock-test`,
  `nested-cv-explorer`) load, render both plots at defaults, and update on
  interaction — ✅ 8/8 (`chapter04.spec.ts` reused against production).
* Hidden-test activity follows its staged train/validation/test sequence
  (lock reveals the third panel, disables further changes) — ✅.
* Nested-CV diagram renders as the real hand-built `.ml-ncv-diagram`
  legend/rows (not raw Mermaid fence text — confirmed absent) — ✅. (Note:
  the diagram is not Mermaid-rendered in the current implementation; see
  §11 deviation.)
* Colab/download links resolve to `exercise_04_portable.ipynb` — ✅
  (`launch-buttons.spec.ts`, Chapter 4 subset).

### 10.3 Exercise 5

* Ridge/Lasso and parameter controls update coefficient/prediction plots,
  Linear Regression disables the alpha control, refresh restores defaults —
  ✅ 5/5.
* Moved feature-set comparison present here and (per the existing spec's
  own title, "moved from Exercise 2") confirmed absent from Exercise 2 — ✅.
* Colab/download links resolve — ✅.
* Plot-geometry policy (x-axis title placement, comparison-card background,
  no overflow at 3 viewport widths including 390px) — ✅ 12/12
  (`chapter05-visual-policy.spec.ts`).

### 10.4 Exercise 6

* Static tree-diagram figure (§1) loaded as a real image (`naturalWidth =
  615`, not broken/missing) — ✅. "Mean age"/"Predicted age" labels are
  baked into this matplotlib PNG's pixels (confirmed via the notebook's own
  post-processing helper source and via "Fail on notebook execution errors"
  passing), not DOM text — see §11.
* Greedy-splitting activity: iframe loads, both panels render, optimum
  hidden before Reveal, lock-and-reveal shows the greedy optimum — ✅.
* Classification-depth figure: page text confirms `753`, `251`, and depth-5
  are all present — ✅ (exact numeric values already verified by
  `scripts/decision_tree_model_audit.py --check`, unrun and unchanged by
  this WP).
* Ensemble ("One Tree or Many?") activity: defaults to Random Forest, all
  panels render, refresh restores the configured default — ✅ (no seed
  selector and `MSE (years²)` units are unchanged committed content, not
  re-derived here).
* Fair-comparison table: confirmed visible on the page — ✅.
* Colab/download links resolve — ✅.
* Narrow-viewport (390px): both activities usable, no horizontal scroll —
  ✅.

### 10.5 Theme, runtime, and layout

* **Chapter 1 dark-mode behavior that caused the CI failure** — the exact
  regression this WP fixes — run **6 times** against live production
  (`chapter01-dark-mode.spec.ts`, both tests, `--repeat-each=3`): **6/6
  passed**, including the reload-while-dark step.
* Every Exercise 4–6 activity verified in light mode (via the reused specs'
  own light-mode assertions) and book-controlled dark mode under light OS
  preference (`wp22-cross-chapter-dark-mode.spec.ts`, Exercises 2–6, 5/5
  passed).
* Exercise 6 reload while dark mode is already active: verified correct
  first paint — `document.body`'s background resolved to the dark palette
  (`rgb(28, 26, 38)`) immediately after reload, not the light default — ✅.
* Plotly drag-layer transparency confirmed as part of the reused
  `chapter01-dark-mode.spec.ts` dark-mode assertions (`dragRectFills`/
  `dragRectStrokes`) — ✅.
* Data marks/labels/controls: confirmed visible throughout every passing
  interaction check above — ✅.
* No page-level horizontal overflow at 390px: confirmed on Exercise 4
  (`chapter04.spec.ts`), Exercise 5 (`chapter05.spec.ts`,
  `chapter05-visual-policy.spec.ts`), and Exercise 6 (own check,
  `scrollWidth === clientWidth`) — ✅.
* Console errors, swept across Exercise 1, 4, 5, and 6 live pages: only two
  **already-documented, pre-existing** messages appeared
  (`Identifier 'THEBE_JS_URL' has already been declared`; `Got invalid
  theme mode: . Resetting to auto.`) — the same category WP31/WP31R/WP31R2
  already record as known Thebe/theme-bootstrap noise. **No new console
  errors** were introduced by this WP's change.

All temporary verification files (the production config and the one small
additional spec) were removed after use; `git status` confirmed nothing
extra was left in the working tree at any point.

## 11. Deviations and items for the user's attention

1. **The nested-CV diagram is not currently Mermaid-rendered.** Live
   production markup shows a hand-built `.ml-ncv-diagram` (colored
   legend/rows, not an SVG produced by `sphinxcontrib.mermaid`), and no
   `mermaid` string appears anywhere in the page. `book/_config.yml`'s
   comment ("the Exercise 4 nested-cross-validation diagram is a plain
   \`\`\`mermaid fenced code block... hand that fence to the mermaid Sphinx
   directive") appears to describe an earlier implementation that a later
   WP (outside this session's visibility) replaced with the current
   hand-built diagram, without updating that comment. This is **not** a
   regression introduced by WP31R2 or WP31R3 (neither touched
   `book/_config.yml`, any notebook, or any widget), and the pinned
   `sphinxcontrib-mermaid` dependency remains harmless and may still be
   used elsewhere or in the future — but the stale comment could mislead a
   future reader. Recommend a small follow-up doc-comment correction (not
   actioned here, per WP31R3 "Do not change lesson content... unless
   strictly necessary" and this WP's narrow scope).
2. **The exact CI regression is verified fixed, including under real
   internet latency**, not just localhost: the Chapter 1 dark-mode
   reload-while-dark test passed 6/6 times directly against
   `https://yoavmp.github.io`, which is if anything a more realistic
   (slower, more variable) network environment than the local build server
   the original race was diagnosed against.
3. `origin/main` now sits at `WP31R3_RELEASE_SHA`
   (`4f0dc06bc4c0c26f8259d4f679832b9e3eb813a4`) with a **successful** green
   Actions run, and production `gh-pages` has moved from
   `9dbe3b10ac31363aa1ef9cd8418a1b9cdd56ca12` to
   `803f98875090787e1108eb714e427d235f032fc4` — the first deploy since
   WP26R to actually publish. **Exercises 4–6 are now live.**
4. No notebook, widget, dataset, model, or activity content was created,
   edited, or regenerated at any point in this WP. Only one test file
   changed.

## 12. Final `git status --short --branch`

```
## main...origin/main
?? WPs/reports/WP16_ARCHITECT_REPORT.md
?? WPs/reports/WP21_DEPLOYMENT_REPORT.md
```

(as of immediately before this report and the changelog were committed
locally; see `WPs/reports/WP31R3_EXACT_CHANGELOG.md` for the exact commit
added after this file, to be recorded as `WP31R3_DOCUMENTATION_SHA`.)

Local `main` = `origin/main` = `4f0dc06bc4c0c26f8259d4f679832b9e3eb813a4`
(`WP31R3_RELEASE_SHA`) at the time this report was written. The two
whitelisted legacy reports remain the only untracked files. WP32 was not
started.
