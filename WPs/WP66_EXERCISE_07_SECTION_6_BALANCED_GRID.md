# WP66 — Exercise 7 Section 6: fix Graph A's missing bars with a balanced grid

## Authority and trigger

The course author identified a bug in Exercise 7, Section 6 ("A Complete
Gradient-Boosting Pipeline"): the committed `lr_n_estimators_pairs` —
`[(0.03, 50), (0.05, 100), (0.1, 100), (0.1, 200)]` — leaves **Graph A**
(grouped by `n_estimators` and `learning_rate`, `max_depth=2` fixed) with
missing bars. Only `learning_rate=0.1` has both `n_estimators` values
(100, 200) represented at every depth; `learning_rate=0.03` has only
`n_estimators=50` and `learning_rate=0.05` has only `n_estimators=100`, so
the chart cannot show "both estimator counts for each learning rate."

## Execution contract

1. Replace `lr_n_estimators_pairs` with the balanced grid
   `[(0.05, 100), (0.05, 200), (0.1, 100), (0.1, 200)]`, crossed with the
   unchanged `max_depth_grid = [1, 2, 3]` — still 12 candidates, still
   5-fold `KFold(n_splits=5, shuffle=True, random_state=13)` (60 fits).
   Graph A (grouped by `n_estimators`/`learning_rate` at `max_depth=2`,
   fixed) must show both `n_estimators` values at both `learning_rate`
   values, with no missing bar. Graph B (grouped by `n_estimators`/
   `max_depth` at `learning_rate=0.1`, fixed) must retain both
   `n_estimators` values at every depth — true before this change and
   still true after, since `(0.1, 100)` and `(0.1, 200)` are unchanged.
2. Make this change only in `scripts/generate_exercise_07_notebook.py`
   (the `CV_PAIRS` constant and its module-docstring documentation),
   regenerated (`--write`, never hand-edited) into every derived copy:
   `book/lite/files/exercise_07.ipynb`,
   `book/lite/files/exercise_07_portable.ipynb`,
   `book/downloads/chapter_07/exercise_07_portable.ipynb`, and
   `scripts/reference_notebooks/exercise_07_reference.ipynb`. Preserve the
   existing cell IDs, student `# YOUR CODE HERE` blanks, hidden check-cell
   answer keys, and the grouped-bar plotting implementation itself
   (`ax.bar(...)` on `slice_a`/`slice_b`) unless inspection of the actual
   bug turns up a second, separate defect in that plotting code — it does
   not; the plotting code already does the right thing with a complete
   grid, the grid was the only defect.
3. Re-execute the completed reference pipeline on this notebook's own data
   source (not assumed, not copied from an old audit) to get the real
   selected configuration, mean cross-validation MSE, and locked-test
   MSE/R² for the new grid. Update every hardcoded expectation that
   changes (generator `EXPECTED_CV_*` constants, module-docstring numbers,
   test assertions, the e2e spec's anchor text) and leave unchanged ones
   alone — do not touch a number that is still correct. The locked test
   set must not be touched during parameter selection; report the actual
   recomputed results even if they are worse than before.
4. Update `tests/test_exercise_07_lite_notebook.py` (the literal
   `lr_n_estimators_pairs` string it asserts on) and
   `tests/test_exercise_07_reference_execution.py` (only if the recomputed
   numbers actually differ from what it currently asserts) to match.
   Check `interactive/e2e-book/exercise-07-lite.spec.ts` for any anchor
   text or literal values tied to the old grid or its numbers and update
   only what the recomputation actually changed.
5. Keep every student-facing cell free of implementation notes addressed
   to the course author (why the grid changed, this WP's number, etc.);
   that explanation belongs in the generator's module docstring and in
   this WP's own spec/report, never in a markdown or code cell a student
   can read.
6. Preserve JupyterLite and Colab/local compatibility exactly as already
   established (no new install step, no behavior change outside Section
   6's grid and its two downstream numbers if they change).
7. Verify with the focused Exercise 7 checks (`generate_exercise_07_notebook.py
   --check`, `tests/test_exercise_07_lite_notebook.py`,
   `tests/test_exercise_07_reference_execution.py`,
   `tests/test_exercise_07_transition_page.py`) and a real local
   JupyterLite browser run of `interactive/e2e-book/exercise-07-lite.spec.ts`
   (`--workers=1`, matching CI's serialized setting) against a real local
   `jupyter-book build` + `jupyter lite build` output. Do not run or wait
   on the full project-wide suite here — the required release gate
   (`.github/workflows/deploy.yml`) covers that on push.
8. Push to `main`, monitor the deploy workflow through completion and
   publication, and verify the live notebook: both Section 6 charts
   render with no missing bars, and the notebook's other sections are
   unaffected. Note for returning users: anyone with a saved, edited
   JupyterLite copy of this notebook (IndexedDB) should download their
   work before using "Reset from course template," since reset replaces
   their saved copy with this updated template.

## Required report

Write `WPs/reports/WP66_REPORT.md` (overall result, the exact grid change
and why it fixes Graph A, the recomputed selected configuration/mean CV
MSE/locked-test MSE-R² and whether they actually changed from before, the
focused test and local-browser results, the push/deploy run id and
conclusion, and live verification of both charts) and
`WPs/reports/WP66_EXACT_CHANGELOG.md` (the precise before/after diff of
every changed line, generator included).
