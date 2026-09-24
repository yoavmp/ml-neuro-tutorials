# WP38R Exact Changelog

Every file added, modified, or removed by WP38R (Exercise 10 review
corrections), relative to the starting branch tip
`feature/wp38-exercise10-common-mistakes` @
`3b8cdeaf40413ceeec8585ac6c0b838387a82ee2`. 39 files changed, 3219
insertions(+), 1284 deletions(-).

## Specification checkpoint (already committed before implementation)

- **`WPs/WP38R_EXERCISE_10_REVIEW_CORRECTIONS.md`** (added) — the WP38R
  specification, committed as the initial checkpoint (`6c8a3a7`) before
  implementation.

## Section 3 — multiple-selection question layout

- **`interactive/src/styles.css`** (modified) — `.widget-quiz-question`
  gained explicit `display: block`, `width: 100%`, `box-sizing: border-box`
  (hardening; no reproduced defect — see report §3).
- **`interactive/e2e/leakage-quiz.spec.ts`** (modified) — new test:
  question/first-option bounding boxes do not overlap, with a ≥4px gap, at
  desktop / an intermediate wrapping width / 390px, in light and dark, on
  initial load and a reload taken with dark mode already active.

## Section 7 — shared iframe/card whitespace

- **`interactive/src/resize-report.ts`** (modified) — two fixes:
  1. Measures/observes `document.body` instead of
     `document.documentElement` (the latter's `scrollHeight` is floored to
     the current viewport height per the CSSOM View spec, so it can never
     report a shrink below the iframe's current height).
  2. Reports the `ResizeObserver` entry's own `contentRect.height` directly,
     instead of a separately-timed `document.body.scrollHeight` read taken
     on the deferred `requestAnimationFrame` callback (which was observed to
     be stale-by-128px on a dynamically-sized chart's final settle).
- **`book/_static/activity-resize.js`** (modified) — adds the iframe's own
  current border-top/bottom width (read via `getComputedStyle`) to the
  height before applying it, compensating for `box-sizing: border-box` +
  `.ml-activity`'s 1px border under-sizing the interior viewport by exactly
  that border width.
- **`interactive/src/styles.css`** (modified) — `.widget-plot`'s
  `min-height` was lowered from 320px to 240px, then reverted back to
  320px after manual visual inspection showed it was based on a false
  premise (see report §4.4); net change across the WP is a documentation-
  only comment rewrite explaining the investigation and revert.
- **`interactive/e2e-book/iframe-height-contract.spec.ts`** (modified,
  pre-existing WP35-era file) — `childScrollHeight` now reads
  `document.body.scrollHeight`; new `TRAILING_GAP_TOLERANCE_PX` (60px)
  assertion on the gap below the last *rendered* (not merely last-in-DOM)
  element; new reset/contraction step (visibility-filtered); describe title
  corrected to "Exercises 1-10".
- **`interactive/e2e/resize-shrink.spec.ts`** (added) — dedicated regression
  test: an iframe started at a static height far taller than its real
  content correctly shrinks down, through the real production
  `ml-activity-resize` message contract.
- **`interactive/e2e-book/chapter10.spec.ts`** (modified) — iframe title/
  selector constant renamed and updated for the new class-balance-compare
  activity (see Section 5 below); otherwise unaffected by the resize work.

## Section 4 — KNN leakage laboratory

- **`scripts/export_leakage_lab_data.py`** (modified) — `KNeighborsRegressor
  (n_neighbors=15)` replaces `LinearRegression` in `_scaling_entry`,
  `_feature_selection_entry`, `_pca_entry`; module docstring updated.
- **`book/config/abide_modeling.json`** (modified) — `leakage_lab.scenarios.*`
  `model`/`leaky_workflow`/`correct_workflow` description strings updated to
  describe the KNN pipelines; scaling scenario's `note` updated to explain
  KNN's scale-sensitivity (WP38R sec 4 note added).
- **`book/_static/widgets/data/abide_leakage_lab.json`** (regenerated) —
  recomputed artifact; see report §5 for the complete 60-row result table.
- **`interactive/src/leakage-lab-data.ts`** (modified) — top-of-file comment
  corrected: the scaling scenario's correct/leaky pair is no longer
  identical (KNN, unlike OLS, is scale-sensitive).
- **`interactive/src/components/leakage-lab.ts`** (modified) — top-of-file
  "honesty note" corrected the same way; adds `data-testid="leak-r2-diff"`
  and `"leak-mse-diff"` signed-difference readouts (`ΔR²`/`ΔMSE`,
  leaky − correct) near the existing metric tiles, per section 4.2's
  "clearly signed difference" requirement.
- **`interactive/tests/leakage-lab-data.test.ts`** (modified) — replaced the
  OLS-specific "scaling shows no difference" assumption with an honest,
  bounds-checked test reflecting the real recomputed KNN behavior (every
  scaling entry now shows a real, bounded, sign-inconsistent gap).
- **`interactive/e2e/leakage-lab.spec.ts`** (modified) — updated for KNN
  wording and the new signed-difference elements; expected numeric values
  read from the freshly recomputed artifact.
- **`tests/test_export_leakage_lab_data.py`** (modified) — same OLS-specific
  test replaced with `test_scaling_scenario_gap_is_real_but_bounded_for_knn`;
  `test_feature_selection_shows_inflation_at_full_sample`'s threshold
  re-verified (unchanged) against the real recomputed numbers.
- **`book/chapters/chapter_10/exercise_10.ipynb`** (modified) — Section 2's
  three reproduction cells (`071b3679` scaling, `c4d48dca` feature
  selection, `4246560e` PCA) rewritten: `KNeighborsRegressor(n_neighbors=15)`
  replaces `LinearRegression`; all three now share one `train_idx`/
  `test_idx` split and print **both** correct and leaky test R² (previously:
  the scaling/feature-selection cells computed but never printed the leaky
  score, and the PCA cell never fit or scored a downstream model on its
  leaky preprocessing at all). Post-activity narrative cell (`18dbc6d4`)
  rewritten to describe KNN's real, scale-sensitive behavior instead of
  citing OLS's scale-invariance (which no longer applies); the required
  verbatim sentence ("Leakage makes the evaluation invalid even when its
  score is similar...") is preserved exactly once.
- **`book/downloads/chapter_10/exercise_10_portable.ipynb`** (regenerated,
  see Section 8 below) — carries the same KNN cells through.

## Section 5 — class-balance comparison activity (replaces imbalance-threshold)

Added:

- **`scripts/export_class_balance_compare_data.py`** — exporter computing
  both models' full metric set (confusion matrix at threshold 0.5, accuracy,
  majority baseline, balanced accuracy, recall, precision, F1, ROC-AUC,
  PR-AUC, PR-AUC baseline) per balance, reusing
  `classification.imbalance_activity`'s existing predeclared
  cohort/seed/ratio values and `classification_model_audit`'s existing
  feature recipe and fixed `C`.
- **`tests/test_export_class_balance_compare_data.py`** — 16 tests:
  validation/canonicalization, exactly 5 ratio keys (95:5 explicitly
  asserted absent), both models present per ratio, baselines recomputed and
  matched, `modelC` fixed at 1.0, no participant-identifier-shaped keys.
- **`interactive/src/class-balance-compare-data.ts`** — zod schema + parser.
- **`interactive/src/components/class-balance-compare.ts`** — the activity:
  one balance selector (no threshold control), both models shown
  simultaneously, required visual hierarchy, side-by-side confusion
  matrices, one across-balance chart (accuracy-vs-baseline default,
  recall/F1 toggle).
- **`interactive/tests/class-balance-compare-data.test.ts`** — parser unit
  tests.
- **`interactive/e2e/class-balance-compare.spec.ts`** — standalone
  Playwright spec: default render, no threshold control anywhere in the DOM,
  balance-selector-driven updates, baseline values matched to the artifact,
  390px usability.
- **`book/_static/widgets/configs/class_balance_compare.json`** —
  hand-authored config (title "Does higher accuracy mean a better
  classifier?").
- **`book/_static/widgets/data/abide_class_balance_compare.json`** —
  committed artifact; see report §6 for the complete metric table.

Removed:

- **`scripts/export_imbalance_threshold_data.py`**
- **`tests/test_export_imbalance_threshold_data.py`**
- **`interactive/src/imbalance-threshold-data.ts`**
- **`interactive/src/components/imbalance-threshold.ts`**
- **`interactive/tests/imbalance-threshold-data.test.ts`**
- **`interactive/e2e/imbalance-threshold.spec.ts`**
- **`book/_static/widgets/configs/imbalance_threshold.json`**
- **`book/_static/widgets/data/abide_imbalance_threshold.json`**

Modified:

- **`interactive/src/config.ts`** — `imbalanceThresholdConfig`/
  `ImbalanceThresholdConfig` schema member removed; `classBalanceCompareConfig`/
  `ClassBalanceCompareConfig` (type literal `"class-balance-compare"`) added
  to the discriminated union.
- **`interactive/src/components/registry.ts`** — registration swapped.
- **`interactive/tests/config.test.ts`** — test block swapped to match.
- **`book/config/abide_modeling.json`** — added an optional, purely
  self-documenting top-level `class_balance_compare` section (script/
  artifact path, design note); `classification.imbalance_activity` itself
  is untouched (still used, unmodified, by Exercise 3).
- **`book/chapters/chapter_10/exercise_10.ipynb`** — Section 5 intro/
  subheading rewritten (five balances instead of one fixed 90:10 cohort;
  "Does Higher Accuracy Mean a Better Classifier?" replaces "High Accuracy
  Can Still Miss the Minority Class"); iframe `src`/`title` updated to the
  new config; reproduction code cell (`a35e40ca`) replaced with a loop over
  all five balances reproducing the exact cohort/split seeds the widget
  uses (verified to match the committed artifact's numbers exactly); post-
  activity narrative cell (`c0eb3227`) rewritten to state the real,
  once-computed 90:10 finding rather than a generic claim.
- **`interactive/e2e-book/chapter10.spec.ts`** — `IMBALANCE_IFRAME_SELECTOR`
  renamed `CLASS_BALANCE_IFRAME_SELECTOR` (new title string); its describe
  block rewritten to assert no threshold control and to check both models'
  accuracy via the new testids/config paths.
- **`interactive/e2e-book/iframe-height-contract.spec.ts`** — its `CASES`
  entry for Exercise 10's fourth activity updated to the new iframe title.
- **`tests/test_exercise_10_notebook.py`** — `IFRAME_TITLES` and
  `test_iframe_src_paths_point_at_expected_configs` updated to
  `class_balance_compare`; new
  `test_class_balance_activity_has_five_balances_and_no_threshold_language`.

## Section 6 — Fragment 4

- **`book/chapters/chapter_10/exercise_10.ipynb`** (modified) — Fragment 4
  (cell `9451d2b2`, shared with Fragment 5) rewritten: explicitly names
  Section 4's UCI HAR dataset and its `X_har`/`y_har`/`groups_har`
  variables; the code fragment now uses those real variable names; the
  answer names repeated/overlapping windows per participant, names
  `StratifiedGroupKFold` with `groups_har` as the fix, and preserves the
  known-user/new-user nuance rather than declaring row-wise splitting
  universally invalid. Fragment 5 (in the same cell) unchanged.
- **`tests/test_exercise_10_notebook.py`** (modified) — new
  `test_fragment_four_identifies_the_smartphone_window_dataset`.

## Section 8 — notebook execution and portable regeneration

- **`book/chapters/chapter_10/exercise_10.ipynb`** — re-executed in place
  (`jupyter nbconvert --to notebook --execute --inplace`) after all content
  edits above; all cell outputs/execution counts current.
- **`scripts/build_portable_notebook.py`** (modified) — Exercise 10's
  iframe-replacement mapping key updated to the new class-balance-compare
  title; `_CH10_IMBALANCE_IFRAME_REPLACEMENT` prose rewritten to describe
  the new activity (was: threshold-slider description).
- **`book/downloads/chapter_10/exercise_10_portable.ipynb`** (regenerated,
  39 cells) — `--check --notebook all` confirms all 10 chapters up to date;
  smoke-executed outside the repository tree
  (`scripts/smoke_portable_notebook.py --notebook chapter_10`), 0 errors,
  key values matched.

## Files NOT touched (confirmed)

`book/syllabus.md`, `course_overview/` (Word document), `main`, `origin/main`
— none read, opened, or modified at any point in this WP.
