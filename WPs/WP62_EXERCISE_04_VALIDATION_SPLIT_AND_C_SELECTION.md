# WP62 — Exercise 4: train/validation/test split and validation-based C selection

## Purpose

Revise **Exercise 4: Classification and Metrics**
(`scripts/generate_exercise_04_notebook.py` and its three generated copies)
so that the regularization strength `C` of the logistic-regression model is
chosen honestly from a held-out **validation** set, rather than fixed in
advance at `C_EXAMPLE = 1.0` (WP19's design). This is **not** a return to
WP18's cross-validation (`GridSearchCV`/`StratifiedKFold`) approach, which
WP19 deliberately removed from the first four notebooks — it is a simpler
train/validation/test procedure appropriate at this point in the course.

This WP is **local-only**: no push, no merge to `main`, no deployment, no
monitoring of GitHub Actions. Stop after the WP62 reports for Yoav's review.

---

## 0. Bounded execution contract

1. Hard-stop after 2 hours of active work; if incomplete, leave the
   repository safe and write a partial report.
2. No scheduled wakeups, background watchers, or polling loops.
3. Run focused Exercise 4 tests during development; one final focused gate.
4. A failing test may be rerun once in isolation after a fix; at most two
   fix attempts per failure, then stop and report it.
5. Build the interactive app and the local JupyterLite preview once, after
   the generator stabilizes. Rebuild only after a genuine fix.
6. Do not create or commit screenshots, caches, `.DS_Store`, or virtual
   environments. Use explicit paths with `git add`; never `git add -A`/`.`.
7. **Do not merge, push, or deploy.** Stay on the feature branch.

---

## 1. Starting state and branch

```bash
git status --short --branch
git rev-parse HEAD
```

Expected: clean tree, local `main` at the tip shown above. Create:

```bash
git switch -c revise/exercise-04-validation-split
```

Commit this WP document alone as the checkpoint commit.

---

## 2. Scope

Touch only:

- `scripts/generate_exercise_04_notebook.py` (single source of truth for
  the three generated Exercise 4 notebooks);
- the three generated files it produces (`book/lite/files/v2/exercise_04.ipynb`,
  `book/downloads/chapter_04/exercise_04_portable.ipynb`,
  `book/lite/files/exercise_04_portable.ipynb`) and the reference notebook
  (`scripts/reference_notebooks/exercise_04_reference.ipynb`) — all
  regenerated via the generator's `--write` mode, never hand-edited;
- `tests/test_exercise_04_lite_notebook.py`,
  `tests/test_exercise_04_reference_execution.py`.

Do **not** touch: `scripts/classification_model_audit.py`,
`scripts/classification_model_audit_result.json`,
`scripts/export_classification_threshold_data.py`,
`scripts/export_classification_imbalance_data.py`, or their tests. These
document a separate, still-accurate audit of the retired fixed-`C=1.0`
procedure for callers outside this notebook (confirmed by a repo-wide
grep: nothing in the live `v2/exercise_04.ipynb` path reads them). The
generator's own top-of-file docstring currently claims its recipe
"preserve[s] unchanged" that audit's numbers — fix only that claim (it
becomes false once `C` is validation-selected), without editing the audit
script or its JSON.

Do not touch `book/chapters/chapter_04/exercise_04.ipynb` (the Jupyter
Book transition/redirect page) or any other exercise.

---

## 3. Section 3 changes

### 3.1 Keep as-is

Feature selection (`FEATURES`, the `fsCT_` columns) and building `X`/`y`
remain student `YOUR CODE HERE` tasks, unchanged.

### 3.2 Three-way split (replaces the train/test-only split activity)

Keep the outer split exactly as established: 75% train+validation / 25%
test, stratified, `random_state=42` (same literal
`test_size=0.25, random_state=42, stratify=y` already asserted by
`test_established_split_arguments_present`). Then split that 75% portion
again, the same way, into training and validation:
`test_size=0.25, random_state=42, stratify=` the 75% portion's own labels.
Verified by direct execution against the committed data
(`book/lite/files/data/abide_age_brain.csv`): this gives exactly
**564 train / 189 validation / 251 test** participants out of 1004 total.

Required output names: `X_train`, `X_val`, `X_test`, `y_train`, `y_val`,
`y_test`. Student instructions describe the two-step procedure and give
hints (call `train_test_split` twice; feed the first call's 75% output
into the second call; stratify each call on its own labels; `random_state=42`
both times) without writing the two calls out. Update the reference
solution and starter stub accordingly (same cell id, same `blank()` tag
`wp44-activity-split`).

### 3.3 Split check (replaces the current train/test-only check)

The check cell must, for all three sets:
- verify exact sizes (564/189/251) against the two-step recipe and give an
  actionable message naming the exact arguments if wrong;
- print each set's autism rate (class balance);
- verify the three sets are mutually disjoint (no participant row appears
  in more than one set) — implemented by hashing each row
  (`np.ascontiguousarray(...).tobytes()` per row) into a set and checking
  pairwise intersections are empty, which works whether a student built
  `X`/`X_train`/etc. as NumPy arrays or pandas objects (mirrors the
  existing `np.asarray` tolerance in the X/y check).

### 3.4 Validation-based C selection (replaces the fixed `C_EXAMPLE = 1.0` fit)

Replace the imports cell's `C_EXAMPLE = 1.0` with a predetermined, modest
grid: `C_GRID = [0.01, 0.1, 1.0, 10.0, 100.0]`. Add one compact, supplied
(not a student task) `RUN FIRST` cell that, guarded on
`X_train`/`y_train`/`X_val`/`y_val` existing:

1. for each `C` in `C_GRID`, fits `make_pipeline(StandardScaler(),
   LogisticRegression(C=C, max_iter=5000))` on `X_train`/`y_train` only;
2. scores it on `X_val` using `roc_auc_score(y_val, predict_proba(...)[:,
   autism_index])`;
3. displays a small `C` vs. validation-AUC table;
4. selects `C` by maximum validation AUC, with a **deterministic tie
   rule**: `C_GRID` is ordered smallest to largest and `np.argmax` returns
   the first maximum, so a tie is always broken toward the smaller
   (more-regularized) candidate — state this plainly in the surrounding
   markdown, not only in a code comment.

No test participant (`X_test`/`y_test`) may appear anywhere in this cell.

Then replace the old fit cell's body (keep its cell id) with: concatenate
`X_train`+`X_val` and `y_train`+`y_val`, fit one final
`StandardScaler`→`LogisticRegression(C=selected_C)` pipeline on the
combination, and compute `y_pred`/`y_proba` on the untouched `X_test`
exactly once. Update its unfinished-prerequisites guard to the full set of
required names (`X_train`, `X_val`, `X_test`, `y_train`, `y_val`, `y_test`,
`selected_C`).

Do not add k-fold cross-validation, `GridSearchCV`, or `StratifiedKFold` —
WP19's "no early cross-validation" scope still applies; this is a plain
train/validation split, not k-fold CV.

### 3.5 Downstream consistency

Every confusion matrix, accuracy/sensitivity/specificity result, ROC/AUC
check, the paired sample table, the Section 5 threshold widget, and the
Section 6 class-imbalance widget must consume the resulting `y_test`,
`y_pred`, `y_proba` (Sections 4–5) or `selected_C` (Section 6's fixed
setting across every ratio, replacing its own `C=C_EXAMPLE` reference)
unchanged in shape — no separate recomputation path.

---

## 4. Text updates

Update, without inserting author-facing commentary, implementation notes,
or WP/script references into student-visible text:

- Section 3's `RUN FIRST` overview (currently states `C = 1.0 ... chosen in
  advance rather than tuned`) — describe the three-way split and
  validation-based selection instead;
- the notebook's opening "What this notebook covers" sentence describing
  the model (currently silent on `C`, add a short clause);
- the post-confusion-matrix reflection's mention of `LogisticRegression(C=1.0)`
  chosen in advance — update to describe validation-based selection, while
  preserving every substring the existing test
  (`test_confusion_matrix_reflection_replaces_the_numeric_autocheck`)
  requires;
- Section 6's imbalance-activity intro, which names `C = C_EXAMPLE`;
- the "In summary" bullets — add one honest bullet on choosing `C` from a
  validation set without touching the test set.

Student-facing prose and code comments describe the method only — no
"as requested," no WP identifiers, no mention of this revision.

---

## 5. Numeric constants and expected values

Recompute, by executing the actual completed reference notebook (not by
copying a prior audit's numbers), and update the generator's module-level
constants (`EXPECTED_SELECTED_C`, `EXPECTED_ACCURACY`, `EXPECTED_AUC`,
`EXPECTED_SENSITIVITY`, `EXPECTED_SPECIFICITY`, `EXPECTED_N_TRAIN`,
`EXPECTED_N_VAL`, `EXPECTED_N_TEST`) and every place a generated notebook
embeds one of these as a literal (the AUC check's tolerance band, the
split-size check, the imbalance-test regression check). Report whatever
the procedure actually selects — do not adjust the grid, split, or tie
rule to produce a particular number.

---

## 6. Required test updates

`tests/test_exercise_04_lite_notebook.py`:
- replace `test_c_example_fixed_not_tuned` with a check that `C_GRID` and
  `selected_C` exist, and that `GridSearchCV`/`StratifiedKFold`/`cross_val`
  remain absent (no k-fold CV was reintroduced);
- add a check that the C-selection cell's own source contains neither
  `X_test` nor `y_test` (test data never participates in selection);
- add a check that the final-fit cell combines train+validation (e.g.
  `np.concatenate`) and computes exactly one `predict`/`predict_proba`
  call against `X_test`;
- update `test_model_fit_cell_is_guarded_against_unfinished_prerequisites`
  for the new seven-name guard;
- update `test_established_auc_referenced_in_its_check` to the recomputed
  AUC literal.

`tests/test_exercise_04_reference_execution.py`:
- stop comparing against `scripts/classification_model_audit_result.json`
  (that JSON documents the retired fixed-`C` procedure and is intentionally
  left unchanged, per section 3); compare instead against the generator's
  own recomputed `EXPECTED_*` constants;
- update split-size, confusion-matrix, accuracy/AUC/sensitivity/specificity
  assertions to the new three-way-split, validation-selected-`C` numbers;
- replace `test_c_example_matches_established_protocol` with a check that
  `selected_C` matches `EXPECTED_SELECTED_C` and that the validation table
  has one row per `C_GRID` entry.

Do not touch `test_exercise_04_transition_page.py` (out of scope; the
redirect page's content is unaffected).

---

## 7. Validation gate (run once, after the generator stabilizes)

1. `python3 scripts/generate_exercise_04_notebook.py --write` then
   `--check`.
2. `.venv/bin/python -m unittest discover -s tests -p 'test_exercise_04_lite_notebook.py'`
3. `.venv/bin/python -m unittest discover -s tests -p 'test_exercise_04_reference_execution.py'`
4. `.venv/bin/python -m unittest discover -s tests -p 'test_exercise_04_transition_page.py'`
   (smoke-check only; expected unchanged).
5. One local JupyterLite build/preview; manually step through the
   completed path (via the reference notebook or a hand run) to confirm
   the validation table, selected `C`, and final test metrics render as
   expected and the runtime stays practical (sub-second grid search
   observed in prototyping).

Do not run the project-wide test suite or other exercises' suites.

---

## 8. Required reports

Create exactly:

- `WPs/reports/WP62_REPORT.md`
- `WPs/reports/WP62_EXACT_CHANGELOG.md`

The report must state: success/partial/failure; branch and commit SHAs;
the three split sizes and a disjointness confirmation; the full validation
table (`C` vs. validation AUC) and selected `C` with the tie rule as
actually exercised; final test confusion matrix, accuracy, sensitivity,
specificity, AUC; measured grid-search and total runtime; comparison with
WP19's fixed-`C=1.0` test accuracy (0.545817) and AUC (0.569221), noting
the test set was never used for selection; test commands/results/timings;
deviations; explicit confirmation that nothing was merged, pushed, or
deployed.

---

## 9. Final response to Yoav

Local preview URL/command, selected `C`, the validation table, final test
metrics, measured runtime, and the tracked WP/report file paths. Then
stop for review — do not merge, push, deploy, or start another WP.
