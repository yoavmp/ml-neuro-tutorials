# WP66 Report — Exercise 7 Section 6: fix Graph A's missing bars

## Overall result: SUCCESS

`lr_n_estimators_pairs` is now `[(0.05, 100), (0.05, 200), (0.1, 100),
(0.1, 200)]` -- a balanced 2-learning-rate x 2-n_estimators set, still
crossed with the unchanged `max_depth_grid = [1, 2, 3]` (12 candidates,
5-fold `KFold` = 60 fits). Graph A (grouped by `n_estimators` and
`learning_rate` at `max_depth=2`, fixed) now shows both `n_estimators`
values at both `learning_rate` values -- no missing bars. Graph B
(grouped by `n_estimators` and `max_depth` at `learning_rate=0.1`, fixed)
already had both `n_estimators` values at every depth and still does.
Re-executing the completed reference pipeline confirmed the selected
configuration, mean cross-validation MSE, and locked-test MSE/R2 are
numerically **unchanged** from before this fix -- not assumed, verified.
Pushed, deployed, and verified live.

## The bug

The prior grid was `[(0.03, 50), (0.05, 100), (0.1, 100), (0.1, 200)]`.
Sliced for Graph A at `max_depth=2` (as `wp46-610-bar-blank` already
does), the four `(learning_rate, n_estimators)` combinations present were
`(0.03, 50)`, `(0.05, 100)`, `(0.1, 100)`, `(0.1, 200)` -- three different
learning rates, each with only **one** `n_estimators` value except
`learning_rate=0.1`. A chart meant to show "both estimator counts for
each learning rate" could only do that for one of the three learning
rates on display; the other two each show a single bar with no partner at
the other `n_estimators` value, i.e. missing bars. Graph B (sliced at
`learning_rate=0.1`) was never affected by this: `(0.1, 100)` and `(0.1,
200)` were already both present at every depth.

## The fix

`CV_PAIRS` in `scripts/generate_exercise_07_notebook.py` is now
`[(0.05, 100), (0.05, 200), (0.1, 100), (0.1, 200)]`: exactly two learning
rates (0.05, 0.1), each crossed with both `n_estimators` values (100,
200). `max_depth_grid = [1, 2, 3]` is untouched. This is still 4 pairs x 3
depths = 12 candidates, still `KFold(n_splits=5, shuffle=True,
random_state=13)` = 60 fits -- same cost, same structure, same student
code path (`param_grid` built as one dict per pair, each offering the full
depth grid). See `WPs/reports/WP66_EXACT_CHANGELOG.md` for the precise
before/after diff of every changed line.

**Inspection of the plotting code found no second defect.** The grouped-
bar implementation (`slice_a`/`slice_b` filtering + `ax.bar(...)`, cell
`wp46-610-bar-blank`) already does exactly the right thing given a
complete grid -- it was never the problem. It is unchanged.

## Why the selected configuration and final numbers did not change

Re-running the actual `GridSearchCV` with the new grid (same `X_train`/
`y_train`, same `KFold(5, shuffle=True, random_state=13)`,
`GradientBoostingRegressor(random_state=42)`) gives the full 12-row table:

| learning_rate | max_depth | n_estimators | mean_cv_mse | sd_cv_mse |
| --- | --- | --- | --- | --- |
| 0.05 | 1 | 100 | 36.54 | 5.31 |
| 0.05 | 1 | 200 | 31.43 | 3.77 |
| 0.10 | 1 | 100 | 31.26 | 3.69 |
| 0.10 | 1 | 200 | 28.67 | 3.30 |
| 0.05 | 2 | 100 | 29.68 | 5.23 |
| 0.05 | 2 | 200 | 27.89 | 5.01 |
| 0.10 | 2 | 100 | 28.33 | 5.55 |
| **0.10** | **2** | **200** | **27.42** | 5.81 |
| 0.05 | 3 | 100 | 29.01 | 5.64 |
| 0.05 | 3 | 200 | 28.10 | 5.89 |
| 0.10 | 3 | 100 | 28.14 | 6.63 |
| 0.10 | 3 | 200 | 27.77 | 6.64 |

`(learning_rate=0.1, n_estimators=200, max_depth=2)` is the best candidate
by mean CV MSE in this new grid, exactly as it was in the old one --
because this exact candidate was already present in the old grid's own 12
rows and was already its own winner there. Each candidate's own
cross-validation MSE is a function only of its hyperparameters and the
fixed `KFold` fold assignment, never of which other candidates happen to
share the grid, so swapping out `(0.03, 50)`/`(0.05, 100)` rows for
`(0.05, 100)`/`(0.05, 200)` rows cannot change the winning candidate's own
score, and none of the new or retained candidates beats 27.42. Confirmed
directly by execution, not inferred:

- Selected: `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 200}`
- Mean CV MSE: **27.4236** (unchanged)
- Locked-test MSE: **29.3842** (unchanged)
- Locked-test R2: **0.685223** (unchanged)

Because these are unchanged, `EXPECTED_CV_BEST_MEAN_MSE`,
`EXPECTED_CV_TEST_MSE`, and `EXPECTED_CV_TEST_R2` in the generator, the
three numeric assertions in `tests/test_exercise_07_reference_execution.py`,
and the `EXPECTED_CV_BEST_MEAN_MSE = 27.4236` anchor text in
`interactive/e2e-book/exercise-07-lite.spec.ts` all needed **no edit** --
confirmed by running all three unmodified and watching them pass against
the regenerated notebook, not left alone by assumption. Section 7's
three-model comparison (`Gradient boosting` row reuses Section 6's own
`boosting_test_mse`/`boosting_test_r2`) is consequently also unchanged:
Single tree MSE=71.288 R2=0.236, Random Forest MSE=35.662 R2=0.618,
Gradient boosting MSE=29.384 R2=0.685 -- gradient boosting still has the
lowest test MSE of the three. The test set was never touched during
parameter selection in either grid; this is a genuine recomputation whose
honest result happens to be "no change to the final numbers," reported as
such rather than assumed.

What *did* change: 3 of the 12 rows in `boosting_cv_results` (the ones
for the dropped `(0.03, 50)` pair are gone; two new rows for `(0.05,
200)` appear instead, at all three depths) -- which is exactly what fixes
Graph A, and the only actual change a student sees in that table/the two
charts.

## Changes

See `WPs/reports/WP66_EXACT_CHANGELOG.md` for the exact diff. Summary:
`scripts/generate_exercise_07_notebook.py` (`CV_PAIRS` constant and its
module-docstring paragraph), regenerated (`--write`, never hand-edited)
into `book/lite/files/exercise_07.ipynb`,
`book/lite/files/exercise_07_portable.ipynb`,
`book/downloads/chapter_07/exercise_07_portable.ipynb`, and
`scripts/reference_notebooks/exercise_07_reference.ipynb` (one line
changed per file -- confirmed by `git diff --stat`), plus one literal
string in `tests/test_exercise_07_lite_notebook.py`. No change to any
other exercise or shared/platform file. No implementation notes
referencing this WP, a script path, or an author-facing explanation were
added to any student-facing cell -- the explanation lives only in the
generator's module docstring (a maintainer-facing comment) and in this
report.

## Focused tests and local browser check (as scoped; broader CI left to the release gate)

- `scripts/generate_exercise_07_notebook.py --check`: **OK**, all four
  outputs up to date with the edited generator.
- `tests/test_exercise_07_lite_notebook.py`: **39/39 passed** (offline
  structural checks, generator `--check` included, the updated
  `lr_n_estimators_pairs` literal assertion included).
- `tests/test_exercise_07_reference_execution.py` +
  `tests/test_exercise_07_transition_page.py` (real-kernel execution of
  the completed reference notebook): **26/26 passed, `Ran 26 tests in
  934.721s -- OK`**. Confirms, printed live from the actual executed
  notebook: `selected settings: {'learning_rate': 0.1, 'max_depth': 2,
  'n_estimators': 200}   mean CV MSE = 27.4`, `locked-test MSE = 29.4
  locked-test R2 = 0.685`, the full 12-row `boosting_cv_results` table
  shown above, `plot A compares 4 candidates at max_depth=2; plot B
  compares 6 candidates at learning_rate=0.1`, and the three-model
  comparison table (Single tree 71.288/0.236, Random Forest 35.662/0.618,
  Gradient boosting 29.384/0.685). Every other section (sweep, step-by-
  step activity, explorer cache, checked questions) is unaffected.
- Real local JupyterLite browser check: built `jupyter-book build book`
  then `jupyter lite build --config book/lite/jupyter_lite_config.json
  --lite-dir book/lite --output-dir book/_build/html/lite` against the
  regenerated notebooks, served via `interactive/e2e-book/serve-book.mjs`,
  and ran `interactive/e2e-book/exercise-07-lite.spec.ts --workers=1`
  (matching CI's serialized setting) in real headless Chromium:
  **7/7 passed in 20.0 minutes**, including the slow teacher-completed-
  path test (17.1m: filling in the sweep blank, the pipeline blank -- a
  real 12-candidate x 5-fold `GridSearchCV` with the *new* grid, inside
  Pyodide WASM -- and the bar-chart blank, then checking a question),
  which ran the check cell containing the unmodified
  `EXPECTED_CV_BEST_MEAN_MSE = 27.4236` text and confirmed it still
  reports "Looks good." Also confirms "no error cells anywhere on an
  untouched Run All Cells" and the Explore the Boosting Parameters widget
  (Activity 2, WP65's precomputed cache, untouched by this WP) still
  behaves correctly.
- Not run here (left to the required release gate per the task's scope):
  the full project-wide Python suite and the full combined-book
  Playwright suite across all exercises.

## Push, deploy, and live verification

<!-- Filled in after push; see commit/run details below. -->
