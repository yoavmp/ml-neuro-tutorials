# WP37V — Production-Status Verification Report

**Date:** 2026-09-23
**Scope:** Production-status verification only, continuing from WP37. No rerun, push, merge,
implementation edit, or WP38 start occurred.

## 1. Overall result

**SUCCESS.** Workflow run `35881835065` ("Build and deploy Jupyter Book") completed with
`conclusion: success`. Full Section 8 production verification of Exercises 7, 8, and 9 passed
against `https://yoavmp.github.io/ml-neuro-tutorials/`.

---

## 2. Workflow status query (exactly once)

```
gh run view 35881835065 --json status,conclusion,url,jobs
```

Result: `"status":"completed"`, `"conclusion":"success"`. All 20 job steps report
`"conclusion":"success"`, including the two that were still `in_progress`/`pending` when WP37
stopped watching:

| Step | Status at WP37 stop | Final status |
|---|---|---|
| 18. Execute the portable notebook outside the repository | `in_progress` (started 15:40:13Z) | `success` (completed 15:46:16Z) |
| 19. Publish website | `pending` | `success` (completed 15:46:21Z) |

Job `build-and-deploy` total duration: `15:28:42Z` → `15:46:25Z` (≈17m43s).

No second query was made. No rerun, cancellation, or repair was attempted or needed.

---

## 3. Production verification (WP37 §8)

Verified against `https://yoavmp.github.io/ml-neuro-tutorials/` using cache-busting query strings
(`curl`) and fresh Playwright browser contexts (no prior cache/storage state). Per WP37 §8's
stated preference, the repository's own existing `interactive/e2e-book/*.spec.ts` files were run
**unmodified** against production, via a temporary Playwright config
(`baseURL: https://yoavmp.github.io`) that existed only inside a `mktemp -d` directory for the
duration of this check and was deleted immediately afterward — never committed. One small
temporary throwaway spec (a console-error sweep for Exercises 8 and 9, the two chapters whose
existing dark-mode specs do not already assert this) was created in the same temporary directory
and removed the same way.

### 3.1 Site structure and unchanged material (§8.1)

| Check | Result |
|---|---|
| `/chapters/chapter_01/exercise_01.html` … `chapter_06/exercise_06.html` | ✅ HTTP 200, titles unregressed ("Exploratory Data Analysis" … "Decision Trees") |
| `/chapters/chapter_07/exercise_07.html` | ✅ HTTP 200, "Exercise 7" content live, no placeholder text |
| `/chapters/chapter_08/exercise_08.html` | ✅ HTTP 200, "Exercise 8" content live, no placeholder text |
| `/chapters/chapter_09/exercise_09.html` | ✅ HTTP 200, "Exercise 9" content live, no placeholder text |
| `/chapters/chapter_10/exercise_10.html` … `chapter_12/exercise_12.html` | ✅ HTTP 200, correct topic titles, placeholder text present ("Materials for this exercise will be added before the practice session.") |
| `/chapters/chapter_13/exercise_13.html` | ✅ HTTP 404 (absent) |
| `/syllabus.html` | ✅ HTTP 200, title "Syllabus" |
| Word course overview | ✅ unchanged — confirmed absent from the `main..WP37_CHECKPOINT_SHA` release diff in the original WP37 run; this file is not part of the GitHub Pages build, so no separate live check applies |
| Colab/download links, Exercises 7–9 | ✅ resolve to `exercise_07_portable.ipynb`, `exercise_08_portable.ipynb`, `exercise_09_portable.ipynb` (`launch-buttons.spec.ts`, reused against production) |

### 3.2 Exercise 7 — Boosting and Gradient Boosting (§8.2)

- Title/structure, both activities present, no AdaBoost mention, Colab button present —
  ✅ (`chapter07.spec.ts`, reused against production).
- Both activities' iframes load with config/data HTTP 200 and render at defaults — ✅.
- "Build a Boosted Model": Next Step advances the stage inside the built page — ✅.
- "Explore the Boosting Parameters": Play advances the tree count, browser refresh restores
  configured defaults — ✅.
- Narrow-viewport (390px), both activities usable without horizontal scroll — ✅.
- "Computational cost is also part of model design" framing present verbatim on the live page —
  ✅ (the partial-grid computational-cost consideration).
- Grouped-bar complete-pipeline chart (MSE y-axis, max-depth groups, learning-rate colors,
  n-trees labels): not independently re-derived pixel-by-pixel against production; verified by
  combination of (a) the identical, tree-verified widget bundle and committed data artifact
  already exercised by the local `boosting-parameter-explorer.spec.ts` standalone spec during the
  original WP37 pre-deployment gates, and (b) the config/data HTTP 200 + panel-render confirmation
  above on the live iframe, which serves that same bundle and data.
- Dark-mode Plotly theme sync, light → dark → reload-while-dark → light, for both activities —
  ✅ (`chapter07-dark-mode.spec.ts`, reused against production; this spec also asserts zero
  unexpected console/runtime errors, which passed).

### 3.3 Exercise 8 — Unsupervised Learning (§8.4)

- Title/structure, both activities present, no out-of-scope methods, Colab button present —
  ✅ (`chapter08.spec.ts`, reused against production).
- "Find the Best Projection": iframe loads, plot renders, true PC1 stays hidden until revealed,
  angle-slider interaction works inside the built page — ✅.
- "Explore PCA and K-Means": iframe loads, defaults applied, all panels render, changing `k` and
  the external characteristic works inside the built page, browser refresh restores defaults — ✅.
- Narrow-viewport (390px), both activities usable without horizontal scroll — ✅.
- Section 8 titled "Using PCA in a Supervised Pipeline" — confirmed present verbatim on the live
  page (three occurrences, including the section heading itself).
- Cumulative explained-variance reporting present ("cumulative explained variance through PC2 =
  42.0%", "through PC5 = 49.4%", etc.) — ✅.
- K-means framing confirmed non-exclusive: "In this notebook, we use K-means as one practical
  example for understanding how clustering works" — explicitly frames it as the method used here,
  not the only possible clustering method — ✅.
- Inertia/silhouette guidance present ("inertia and the elbow", "inertia (the quantity K-means
  minimizes)", "silhouette score") without an unambiguous-answer claim — ✅.
- Dark-mode Plotly theme sync, light → dark → reload-while-dark → light, for both activities —
  ✅ (`chapter08-dark-mode.spec.ts`, reused against production).
- Console-error sweep (light + toggled dark): zero unexpected console/runtime errors — ✅
  (temporary throwaway spec, since `chapter08-dark-mode.spec.ts` does not itself assert this).

### 3.4 Exercise 9 — Advanced Models (§8.3 in WP37's own numbering, "9. Advanced Models")

- Title/structure, both activities present, no out-of-scope methods, Colab button present —
  ✅ (`chapter09.spec.ts`, reused against production).
- "PCR or PLS?": iframe loads, both panels render, changing method and preset works inside the
  built page — ✅.
- "Explore an SVM Boundary": iframe loads, defaults applied, plot renders, changing dataset and
  kernel works inside the built page, browser refresh restores defaults — ✅.
- Narrow-viewport (390px), both activities usable without horizontal scroll — ✅.
- Alignment control framed as the "highest-variance direction" — confirmed present verbatim
  (two occurrences) — ✅.
- Fixed signal/noise framing confirmed verbatim: "All three presets below share the same signal
  strength and the same noise level; only the direction of the predictive signal changes." — ✅.
- One-component PCR/PLS convergence-at-two-components and the PLS-advantage-shrinks behavior:
  not independently re-derived against production; verified by the identical, tree-verified
  widget bundle and committed data artifact (`pcr_pls_explore.json`) already exercised by the
  local `pcr-pls-explore.spec.ts` standalone spec during the original WP37 pre-deployment gates,
  combined with the config/data HTTP 200 + interaction confirmation above on the live iframe,
  which serves that same bundle and data.
- The real ABIDE-II advanced-model comparison is present, described as comparing "standardized
  ordinary linear regression … PCR; PLS regression; linear SVR; RBF SVR" under one shared nested
  cross-validation structure, with the outer-fold numbers explicitly stated to be "exactly what
  nested cross-validation produced" (no post-hoc test-set selection) — and all five committed MSE
  values appear **verbatim** on the live page: OLS 49.14 (`49.1359`), PCR 31.74 (`31.7446`), PLS
  32.42 (`32.420`), Linear SVR 40.28 (`40.2761`), RBF SVR 20.38 (`20.3783`) — an exact match to
  `scripts/advanced_models_audit_result.json`, confirming the live comparison is unchanged from
  its reviewed WP35 state and renders immediately (not gated behind the expensive full nested
  audit, which remains optional/off by default) — ✅.
- Dark-mode Plotly theme sync, light → dark → reload-while-dark → light, for both activities —
  ✅ (`chapter09-dark-mode.spec.ts`, reused against production).
- Console-error sweep (light + toggled dark): zero unexpected console/runtime errors — ✅
  (temporary throwaway spec, since `chapter09-dark-mode.spec.ts` does not itself assert this).

### 3.5 Theme, responsive layout, iframe height, and runtime — every Exercise 7–9 activity (§8.5)

- Light mode: verified via each reused spec's own light-mode assertions (all pass) — ✅.
- Book's own theme toggle to dark mode under light OS/browser preference, and a reload while dark
  mode is already active (correct first paint): verified via `chapter07/08/09-dark-mode.spec.ts`'s
  "light → dark → reload-while-dark → light" sequence, reused unmodified against production — ✅.
- Plotly backgrounds, gridlines, marks, legends, controls, and text following the intended theme;
  Plotly drag-layer transparency (not covering axis titles): verified via the same dark-mode
  specs' internal palette/drag-layer assertions — ✅.
- Controls actually changing figures/metrics (not text alone): verified via every reused
  interaction assertion above (Next Step, Play, angle slider, `k`/retained-PC/method/preset/
  dataset/kernel changes) — ✅.
- Iframe height contracts after rendering, survives a control change, and fits in dark mode at
  390px, with no large empty lower region, for every Exercise 1–9 activity (including all five
  Exercise 7–9 activities): ✅ (`iframe-height-contract.spec.ts`, reused unmodified against
  production — all Exercises 1–9 rows passed).
- No content clipped after interaction: confirmed by the same iframe-height-contract assertions
  and by every activity's own post-interaction render checks above — ✅.
- No page-level horizontal overflow at 390px: confirmed via each chapter spec's own
  narrow-viewport test and via `iframe-height-contract.spec.ts`'s 390px checks — ✅.
- Console errors distinguished from the two historically documented, unrelated Thebe/theme-
  bootstrap messages (`Identifier 'THEBE_JS_URL' has already been declared`; `Got invalid theme
  mode: . Resetting to auto.`): Exercise 7 covered by `chapter07-dark-mode.spec.ts`'s own built-in
  assertion (passed, zero unexpected errors); Exercises 8 and 9 covered by the temporary
  console-sweep spec described above (passed, zero unexpected errors, and neither known noise
  message appeared at all in this particular sweep). **No new runtime error was found — not a
  stop condition.**

---

## 4. Items requiring the user's attention

None. The workflow succeeded, and every WP37 §8 production check for Exercises 7, 8, and 9
passed. The one previously open item from the original WP37 report — the unknown workflow
conclusion — is now resolved as `success`.

---

## 5. Final git status and log

```text
## main...origin/main [ahead 2]
```

(Clean working tree; local `main` is now two documentation-only commits ahead of `origin/main`:
the original WP37 documentation commit and this WP37V documentation commit. Neither is pushed,
per both WPs' instruction not to trigger a second deployment via a documentation-only push.)

```text
<WP37V documentation commit> WP37V: reports — production-status verification report and exact changelog
bf6aaa2 WP37: reports — deployment execution report and exact changelog
f792ad5 (origin/main, origin/HEAD) Merge Exercises 7-9 course materials
d2d3255 WP37: add specification (initial checkpoint)
```
