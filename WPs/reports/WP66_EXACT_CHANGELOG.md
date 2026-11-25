# WP66 — Exact changelog

## scripts/generate_exercise_07_notebook.py

### `CV_PAIRS` constant

**Before:**
```python
CV_PAIRS = [(0.03, 50), (0.05, 100), (0.1, 100), (0.1, 200)]
```

**After:**
```python
CV_PAIRS = [(0.05, 100), (0.05, 200), (0.1, 100), (0.1, 200)]
```

`CV_DEPTH_GRID = [1, 2, 3]` is unchanged. `EXPECTED_CV_BEST_MEAN_MSE`,
`EXPECTED_CV_TEST_MSE`, and `EXPECTED_CV_TEST_R2` are unchanged (see the
report for why: the winning candidate is present in both grids and its own
cross-validation score does not depend on its co-candidates).

### Module docstring, Section 6 paragraph

**Before:**
```
  Section 6 pipeline (12-candidate reduced grid: lr/n_estimators pairs
    [(0.03,50), (0.05,100), (0.1,100), (0.1,200)] x max_depth in [1,2,3],
    KFold(5, shuffle=True, random_state=13) on the 753-row development
    partition): selected (learning_rate=0.1, n_estimators=200,
    max_depth=2), mean CV MSE=27.4236; refit on all 753, evaluated once on
    the locked 251-row test set: test MSE=29.3842, R2=0.685223. Differs
    from the legacy audit's selected (..., max_depth=3), mean CV MSE=27.2085,
    test MSE=32.3679, R2=0.653261 -- the order-sensitivity difference
    documented above; both are genuine, honestly-computed selections from
    the same declared procedure, and this notebook's own number is the one
    embedded in its check cells.
```

**After:**
```
  Section 6 pipeline (12-candidate reduced grid: lr/n_estimators pairs
    [(0.05,100), (0.05,200), (0.1,100), (0.1,200)] x max_depth in [1,2,3],
    KFold(5, shuffle=True, random_state=13) on the 753-row development
    partition): selected (learning_rate=0.1, n_estimators=200,
    max_depth=2), mean CV MSE=27.4236; refit on all 753, evaluated once on
    the locked 251-row test set: test MSE=29.3842, R2=0.685223. WP66
    replaced the prior grid's [(0.03,50), (0.05,100), (0.1,100), (0.1,200)]
    pairs with this balanced 2-learning-rate x 2-n_estimators set: the old
    pairs gave Section 6's Graph A (grouped by learning_rate and
    n_estimators at max_depth=2, fixed) only one n_estimators value at
    learning_rate=0.03 and only one at learning_rate=0.05, leaving that
    grouped bar chart with missing bars. Every one of the four pairs now
    crosses both n_estimators values at every depth. The winning candidate,
    (learning_rate=0.1, n_estimators=200, max_depth=2), was already present
    in the prior grid and remains the single best mean-CV-MSE candidate in
    this one too -- each candidate's own cross-validation MSE depends only
    on its own hyperparameters and the fixed KFold assignment, not on which
    other candidates share the grid -- so the selected configuration, mean
    CV MSE, and locked-test MSE/R2 are numerically unchanged from the prior
    grid; verified directly, not assumed. The legacy audit's own grid
    (identical pairs to this notebook's prior grid) selected (...,
    max_depth=3), mean CV MSE=27.2085, test MSE=32.3679, R2=0.653261, on a
    different data source (the order-sensitivity difference documented
    above) -- that comparison point is independent of the WP66 pair swap
    and still stands as before.
```

Section 7's docstring paragraph (single tree/Random Forest/gradient
boosting numbers) is unchanged -- those numbers do not depend on `CV_PAIRS`.

## Regenerated files (via `--write`, never hand-edited)

Each file's only change is the one line carrying `lr_n_estimators_pairs`
inside cell `wp46-604-blank` (the pipeline activity's starter/solution
code):

**Before (every file):**
```python
lr_n_estimators_pairs = [(0.03, 50), (0.05, 100), (0.1, 100), (0.1, 200)]
```

**After (every file):**
```python
lr_n_estimators_pairs = [(0.05, 100), (0.05, 200), (0.1, 100), (0.1, 200)]
```

- `book/lite/files/exercise_07.ipynb` (student template)
- `book/lite/files/exercise_07_portable.ipynb` (student, served copy)
- `book/downloads/chapter_07/exercise_07_portable.ipynb` (student, download)
- `scripts/reference_notebooks/exercise_07_reference.ipynb` (teacher-completed)

No other cell in any of the four files changed -- confirmed by `git diff
--stat` showing exactly one changed line per file. In particular, the
grouped-bar plotting code (`ax.bar(labels_a, ...)` / `ax.bar(labels_b,
...)`), every cell id, every student `# YOUR CODE HERE` blank, every
hidden check-cell answer key, and the checked questions are byte-for-byte
unchanged.

## tests/test_exercise_07_lite_notebook.py

**Before:**
```python
self.assertIn("lr_n_estimators_pairs = [(0.03, 50), (0.05, 100), (0.1, 100), (0.1, 200)]", source)
```

**After:**
```python
self.assertIn("lr_n_estimators_pairs = [(0.05, 100), (0.05, 200), (0.1, 100), (0.1, 200)]", source)
```

## tests/test_exercise_07_reference_execution.py

No change. Its three numeric assertions (mean CV MSE ~27.4236, locked-test
MSE ~29.3842, locked-test R2 ~0.685223) still pass unmodified because the
recomputed numbers are identical to before (see report) -- confirmed by a
real reference-notebook execution, not left unchanged by assumption.

## interactive/e2e-book/exercise-07-lite.spec.ts

No change. Its anchor text (including the literal
`EXPECTED_CV_BEST_MEAN_MSE = 27.4236`, used only to locate and run that
check cell) still matches the regenerated notebook, confirmed by a real
local Playwright run (7/7 passed, including the teacher-completed path
that fills the pipeline blank with the new grid).

## No other files changed

No change to `book/config/abide_modeling.json` (the frozen legacy-audit
record), any other exercise, any shared/platform file, or any build/deploy
config.
