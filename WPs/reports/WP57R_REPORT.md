# WP57R Report — Exercise 12 revision (local review only)

Revises Exercise 12 ("Common Mistakes and Pitfalls") per 8 author notes,
on the existing branch `feature/wp57-active-exercise-12-common-mistakes`.
**Nothing merged, pushed, or deployed.** Regenerated the student, portable,
and reference notebooks from the generator for every change.

## Changes by note

1. **Bolded "that is the real danger"** in the opening paragraph.
2. **Removed the six-item "In this notebook you will" list** (it previewed
   each case's diagnosis). Kept the run → diagnose → repair → inspect
   paragraph. Renamed the now-ill-fitting heading from "What this notebook
   covers" to **"How This Notebook Works."**
3. **Fixed Case 1's scaler check.** The original compared one feature's
   mean to a hardcoded constant with `TOLERANCE=0.01` — looser than the
   real diff, so it would have accepted a leaky scaler submitted by
   mistake. The check now compares `scaler_honest.mean_` against
   `X_train.mean(axis=0)`, computed live, with `TOLERANCE=1e-6`. Directly
   demonstrated in a new test
   (`test_case1_check_cell_passes_for_honest_and_fails_for_leaky`) that a
   scaler fit on `X_train` passes and the supplied `scaler_leaky` fails.
   The check's own printed caveat now reads "cannot by itself prove
   **every possible solution** is leakage-free."
4. **Rewrote Case 1's takeaway**: states the diff is a few thousandths in
   this 602-participant partition, and that the *same kind* of leak
   "could shift" statistics by more in a 60-participant study — never
   claims a large effect is guaranteed.
5. **Added a supplied, ready-to-run score-level comparison** (Case 1):
   `KNeighborsRegressor(n_neighbors=5)`, fixed before inspecting any
   result, compares leaky vs. honest scaling at the full split and at two
   predetermined smaller sizes (100, 60; fixed seed 0). All three draws
   come only from the train+validation pool — **never `X_test`**. See
   "Actual values" below for every attempted size's real result (reported
   honestly, including two sizes where the "leaky" score was actually
   *better*).
6. **Redesigned Case 2** so inclusion of `y` in PCA is the *one* deliberate
   mistake. Removed the 3× scale-up. Both paths now standardize their own
   input columns and fit PCA on **training rows only** — the contaminated
   path's own columns are `[x1, x2, y]`, so transforming any row
   (including a held-out one) structurally requires that row's own `y`;
   the honest path's columns are `[x1, x2]` and never need `y`. Updated
   the self-contained widget, labels, expected numbers, checks, and
   markdown to match. The resulting gap (0.8973 vs. 0.1209) is still
   large — accepted as the real, corrected demonstration's own result, not
   tuned for size.
7. **Renamed all six "### Diagnose" headings to "### Think first"** ("###
   Diagnose and repair" → "### Think first and repair"). The
   diagnose/repair pattern explanation in the overview paragraph is
   unchanged.
8. **Trimmed the Case 3 plot caption** to "Supplied: a ready-to-run plot."
   — removed "handled gracefully if the repair above is not complete
   yet." The code's own graceful incomplete-task behavior is unchanged.

## Actual Case 1 and Case 2 values (directly verified; see the
generator's own module docstring for the full transcript)

**Case 1** — contaminated scaler now fit on `X_train_and_val` (803 rows:
`X_train` 602 + `X_val` 201) — **never `X_test`**, which stays genuinely
untouched for Case 3 throughout:
- Feature `fsCT_L_1_ROI` mean: contaminated (803 rows) = **2.371498**,
  honest (`X_train`, 602 rows) = **2.371573** — diff 0.000075; largest
  diff across all 360 features = **0.020635**.
- Check-cell discrimination (tight, live, `TOLERANCE=1e-6`): a scaler fit
  on `X_train` passes (max diff ~1e-15, floating-point noise); the
  supplied `scaler_leaky` fails (max diff 0.020635 ≫ 1e-6).
- KNN score comparison (`n_neighbors=5`, fixed; every size drawn only
  from `X_train`+`X_val`):
  | Size | leaky val MSE | honest val MSE | direction |
  |---|---|---|---|
  | full (602/201) | 32.715 | 32.390 | leaky **worse** by 0.324 |
  | n=100 (75/25, seed 0) | 60.014 | 60.911 | leaky **better** by 0.897 |
  | n=60 (45/15, seed 0) | 10.334 | 10.630 | leaky **better** by 0.296 |

  Reported exactly as computed — small and direction-inconsistent across
  the three predetermined sizes; no seed or size was searched for a
  favorable result.

**Case 2** — both paths standardize + fit PCA on training rows only;
`y` is the one structural difference between them:
- Contaminated (`[x1, x2, y]`, needs the held-out `y` to transform any
  row): held-out **R² = 0.8973**.
- Honest (`[x1, x2]`, never needs `y`): held-out **R² = 0.1209**.
- (For contrast, the WP57-original mechanism — PCA fit on all rows
  including `y`×3 scale-up — gave 0.9997 vs. 0.4489; this revision's gap
  is differently shaped but still large, and is the real, unforced result
  of the corrected, single-mistake mechanism.)

## Focused tests and timings (Exercise-12-only; no course-wide suite run)

| Suite | Result | Time |
|---|---|---|
| `tests/test_exercise_12_lite_notebook.py` | 51/51 OK (14 new/changed assertions for this revision) | 0.10s |
| `tests/test_exercise_12_reference_execution.py` | 32/32 OK (6 new, including the check-cell pass/fail demonstration and the KNN-comparison numbers) | 5.4s |
| `tests/test_exercise_12_transition_page.py` | 9/9 OK (unaffected by this revision) | 0.03s |
| **Exercise-12-only offline total** | **92/92 OK** | **4.3–4.5s** |
| Local combined build (`jupyter-book build book --all` + `jupyter lite build`) | both exit 0, no errors | detached, completed before next check |
| `interactive/e2e-book/exercise-12-lite.spec.ts` (real Chromium/Pyodide) | **4/4 passed** | **1.5 minutes** (run once; no fix was needed, so no repeat) |

No command needed a second run: the structural/reference suite and the
Playwright spec each passed on their first run after the implementation
settled, per the WP's own instruction.

## Audit for spoilers, hidden-answer leaks, and stale numeric claims

Scanned the generated student notebook directly (not by memory):
- No stale numbers: `0.9997`, `0.4489`, `2.373286`, the old `3 *` scale-up,
  "scaled up", "almost perfect", and "dominates the first component" all
  absent from both markdown and code.
- No heading spoilers: none of the six `## N.` headings or any `###`
  subheading contains "leakage", "mistake", "bug", "the flaw", or
  "incorrect".
- `correct_index`/`correct_indices` confirmed absent from every visible
  `show_question(...)` cell (unchanged by this revision; re-verified).
- Blank hints re-scanned against the forbidden-fragment list (now also
  covering `.transform(` and `StandardScaler().fit(` in addition to the
  original set) — clean, including in comments.

## Deviations

None from the 8 notes. One judgment call: note 5 allowed either
"preserve a genuinely untouched test partition for Case 3" or "use a
separate clearly named Case 1 split" — this revision took the first
option (confining Case 1's own contaminated scaler to `X_train_and_val`,
excluding `X_test`) because it fixes the same underlying problem for
*both* Case 1's original demonstration and the new KNN comparison with
one change, rather than leaving Case 1's "Run it" cell still touching
`X_test` while only the new comparison avoided it.

## Files touched this revision

- `scripts/generate_exercise_12_notebook.py` (generator)
- `book/lite/files/exercise_12.ipynb`, `exercise_12_portable.ipynb`,
  `book/downloads/chapter_12/exercise_12_portable.ipynb`,
  `scripts/reference_notebooks/exercise_12_reference.ipynb` (regenerated)
- `tests/test_exercise_12_lite_notebook.py`,
  `tests/test_exercise_12_reference_execution.py` (updated/extended)
- `interactive/e2e-book/exercise-12-lite.spec.ts` (anchors/solutions
  updated to match the new Case 1/2 mechanisms)

Not touched: `book/_toc.yml`, `book/_config.yml`,
`book/config/exercise_manifest.json`, the transition page, the Exercise
10/11 placeholders, or anything in Exercises 1–9.

## Branch and final git state

- Branch: `feature/wp57-active-exercise-12-common-mistakes` (unchanged).
- Implementation commit: `ce6f02e` — "WP57R: fix Case 1 test-partition
  leakage and check, redesign Case 2's single mistake (local only)".
- Report commit: this file's own commit (see the terminal summary for its
  exact SHA).
- Working tree: clean after both commits.
- **No merge, push, CI release run, or deployment was performed or
  attempted.**
