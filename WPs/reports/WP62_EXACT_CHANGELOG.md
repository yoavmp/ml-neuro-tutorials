# WP62 Exact Changelog

## Starting point

`main` / `origin/main` at `7e3a348404a93078190d2abe8537bc0d2ff8bc81`
("Fix CI regression: never overwrite a pure editable answer blockquote
with a label"), clean tree.

## Branch

`revise/exercise-04-validation-split`, created from `main` at `7e3a348`.
**Not merged into `main`; not pushed.**

## Commits (in order)

```
b3f1c1b WP62: add WP document (checkpoint before implementation)
20cff55 WP62: train/validation/test split and validation-based C selection for Exercise 4
```

Final branch SHA: `20cff55bd69c55eeecf9c736e25e8336780de2cf`.
(This report and the companion `WP62_REPORT.md` are committed afterward,
as a separate documentation commit — their SHA becomes the new branch
`HEAD` and is reported in the assistant's final response, not here.)

## Files created

- `WPs/WP62_EXERCISE_04_VALIDATION_SPLIT_AND_C_SELECTION.md` (277 lines) —
  the WP specification, committed alone in `b3f1c1b`.
- `WPs/reports/WP62_REPORT.md` — this WP's report.
- `WPs/reports/WP62_EXACT_CHANGELOG.md` — this file.

## Files modified (commit `20cff55`)

```
 scripts/generate_exercise_04_notebook.py            | 218 +++++++++++-----
 book/lite/files/v2/exercise_04.ipynb                 | 174 +++++++++----
 book/downloads/chapter_04/exercise_04_portable.ipynb | 174 +++++++++----
 book/lite/files/exercise_04_portable.ipynb           | 174 +++++++++----
 scripts/reference_notebooks/exercise_04_reference.ipynb | 176 +++++++++----
 tests/test_exercise_04_lite_notebook.py              |  54 +++-
 tests/test_exercise_04_reference_execution.py        |  57 +++--
 7 files changed, 726 insertions(+), 301 deletions(-)
```

The three generated notebooks and the reference notebook were produced
exclusively by `python3 scripts/generate_exercise_04_notebook.py --write`
from the edited generator — never hand-edited — and confirmed idempotent
by a subsequent `--check`.

### `scripts/generate_exercise_04_notebook.py`

- Docstring: replaced the claim that the recipe/split/`C_EXAMPLE`
  "preserve[s] unchanged" against `scripts/classification_model_audit_result.json`
  with an accurate description of the new three-way split and
  validation-based `C` selection, and an explicit note that the retired
  audit JSON is intentionally left unchanged for its other callers.
- Constants: removed `C_EXAMPLE = 1.0`; added `C_GRID`,
  `EXPECTED_SELECTED_C`, `EXPECTED_TN/FP/FN/TP`, `EXPECTED_N_VAL`,
  `EXPECTED_N_TOTAL`, `EXPECTED_N_POSITIVE`, `EXPECTED_N_NEGATIVE`;
  recomputed `EXPECTED_ACCURACY`, `EXPECTED_AUC`, `EXPECTED_SENSITIVITY`,
  `EXPECTED_SPECIFICITY`, `EXPECTED_N_TRAIN` for the new procedure.
- `_title_and_overview()`: one clause added describing the validation-based
  `C` choice.
- `_section_3()`: section header renamed ("Choosing C honestly with a
  validation set"); Section-3 RUN FIRST overview rewritten; imports cell's
  `C_EXAMPLE` line replaced by `C_GRID`; split header/instructions/blank
  rewritten for the three-way split (cell ids unchanged:
  `wp44-331-header`/`-332-instructions`/`-333-blank`); split check cell
  rewritten for three sets + disjointness (`wp44-334-check`, id unchanged);
  two new cells inserted (`wp44-335-header`, `wp44-336-c-search`) for the
  validation search; final-fit header/code rewritten for the
  train+validation refit and single test evaluation (`wp44-341-header`/
  `wp44-342-fit`, ids unchanged).
- `_section_4()`: the post-confusion-matrix reflection's mention of
  `LogisticRegression(C=1.0)` chosen in advance replaced with a
  validation-based description (same cell id `wp44-414-reflection`, same
  required substrings preserved).
- `_section_6()`: imbalance intro text and guard updated from `C_EXAMPLE`
  to `selected_C`; the refit line's `C=C_EXAMPLE` changed to
  `C=selected_C`.
- `_summary()`: one new bullet added on validation-based `C` selection.

### `book/lite/files/v2/exercise_04.ipynb`, `book/downloads/chapter_04/exercise_04_portable.ipynb`, `book/lite/files/exercise_04_portable.ipynb`

Regenerated, byte-identical to each other (verified by
`StructuralSynchronization.test_lite_and_portable_are_identical`).

### `scripts/reference_notebooks/exercise_04_reference.ipynb`

Regenerated; same cell ids as the student template with the five
`blank()` activities' reference solutions instead of `YOUR CODE HERE`
stubs (verified by `StructuralSynchronization.test_reference_has_the_same_cell_ids_and_non_blank_cells_match`).

### `tests/test_exercise_04_lite_notebook.py`

- Removed `test_c_example_fixed_not_tuned`.
- Added `test_c_is_selected_via_validation_not_cross_validation`,
  `test_c_selection_never_references_the_test_set`,
  `test_final_fit_combines_train_and_validation_and_uses_test_once`,
  `test_split_check_covers_all_three_sets`.
- Updated `test_model_fit_cell_is_guarded_against_unfinished_prerequisites`
  for the new seven-name guard.
- Updated `test_established_auc_referenced_in_its_check` to assert the
  generator's own recomputed `EXPECTED_AUC` (imported from the module)
  instead of the hardcoded retired literal `"0.569221"`.

### `tests/test_exercise_04_reference_execution.py`

- Removed the `scripts/classification_model_audit_result.json` read and
  the `AUDIT_RESULT` global; added
  `import generate_exercise_04_notebook as gen` (via the existing
  `scripts/`-on-path convention).
- `test_participant_and_predictor_counts`, `test_class_counts_match_the_audit`:
  now compare against `gen.EXPECTED_N_TOTAL`/`EXPECTED_N_FEATURES`/
  `EXPECTED_N_POSITIVE`/`EXPECTED_N_NEGATIVE` instead of the JSON.
- `test_established_split_sizes`: now asserts all three split sizes
  (`EXPECTED_N_TRAIN`/`EXPECTED_N_VAL`/`EXPECTED_N_TEST`).
- `test_logistic_regression_matches_established_result`,
  `test_confusion_matrix_matches_established_result`: now compare against
  `gen.EXPECTED_*` instead of the JSON's `locked_test_eval`.
- Removed `test_c_example_matches_established_protocol`; added
  `test_selected_c_matches_the_validation_search` (checks `selected_C`
  against `gen.EXPECTED_SELECTED_C` and the validation table's `C` column
  against `gen.C_GRID`).
- Unused `json` import removed; `sys` import added for the `scripts/` path
  insertion.
- Module docstring updated to explain the intentional decoupling from the
  retired audit JSON.

## Files explicitly not touched

`scripts/classification_model_audit.py`,
`scripts/classification_model_audit_result.json`,
`scripts/export_classification_threshold_data.py`,
`scripts/export_classification_imbalance_data.py`, their tests
(`tests/test_classification_model_audit.py`,
`tests/test_export_classification_threshold_data.py`,
`tests/test_export_classification_imbalance_data.py`),
`book/chapters/chapter_04/exercise_04.ipynb`,
`tests/test_exercise_04_transition_page.py`, and every file for any other
exercise. Confirmed by `git diff --stat main...revise/exercise-04-validation-split`
listing exactly the 8 files above (7 implementation files + the WP spec).

## Final state

```
$ git log --oneline --decorate -5 revise/exercise-04-validation-split
20cff55 (HEAD -> revise/exercise-04-validation-split) WP62: train/validation/test split and validation-based C selection for Exercise 4
b3f1c1b WP62: add WP document (checkpoint before implementation)
7e3a348 (origin/main, origin/HEAD, main) Fix CI regression: never overwrite a pure editable answer blockquote with a label
41eddfd Add seven-label pilot (RUN FIRST/YOUR CODE/CHECK/EXPLORE/QUESTION/ILLUSTRATE/INSPECT) across Exercises 1-12
1af7c9f WP61D report: exact release commits, CI run, and real live verification
```

`main` is unchanged at `7e3a348`. Nothing pushed or deployed.
