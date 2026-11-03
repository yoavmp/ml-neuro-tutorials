# WP62 Report — Exercise 4: train/validation/test split and validation-based C selection

## Overall result: SUCCESS

All work described in
`WPs/WP62_EXERCISE_04_VALIDATION_SPLIT_AND_C_SELECTION.md` is implemented,
regenerated, tested, and locally built. The branch is **not** merged,
pushed, or deployed, per the WP's local-only contract.

## Branch and commits

- Branch: `revise/exercise-04-validation-split`, created from local `main`
  at `7e3a348` (clean tree).
- `b3f1c1b` — WP62: add WP document (checkpoint before implementation).
- `20cff55` — WP62: train/validation/test split and validation-based C
  selection for Exercise 4 (implementation).
- Final branch SHA: `20cff55bd69c55eeecf9c736e25e8336780de2cf`. Local `main`
  is unchanged at `7e3a348`; no merge was performed.

## What changed (Section 3 of the notebook)

1. **Split task** (unchanged cell ids `wp44-331-header`/`-332-instructions`/
   `-333-blank`, tag `wp44-activity-split`): now builds a three-way
   stratified split instead of a train/test split. The outer 75%
   train+validation / 25% test split (`test_size=0.25, random_state=42,
   stratify=y`) is unchanged from WP19; the 75% portion is split again the
   same way (`test_size=0.25, random_state=42, stratify=` the 75%
   portion's own labels) into training and validation. Required output
   names: `X_train`, `X_val`, `X_test`, `y_train`, `y_val`, `y_test`.
   Instructions give hints (two `train_test_split` calls, the second fed by
   the first, both seeded `random_state=42`) without writing the two calls
   out.
2. **Split check** (`wp44-334-check`): verifies all three sizes, prints
   each set's autism rate, and verifies the three sets are pairwise
   disjoint by hashing each row (`tobytes()` of a contiguous float array,
   so it works whether a student used NumPy or pandas).
3. **Validation-based C selection** (new cells `wp44-335-header` /
   `wp44-336-c-search`, both supplied `RUN FIRST` code, not a student
   task): for each `C` in a predetermined grid `C_GRID = [0.01, 0.1, 1.0,
   10.0, 100.0]`, fits `StandardScaler → LogisticRegression` on
   `X_train`/`y_train` only, scores validation ROC AUC from
   `predict_proba` on `X_val`, displays the results table, and selects `C`
   by maximum validation AUC with a deterministic tie rule (grid searched
   smallest→largest; `np.argmax` keeps the first/smallest on a tie). This
   cell's source contains neither `X_test` nor `y_test` (verified by a new
   test).
4. **Final fit** (`wp44-342-fit`, cell id unchanged): concatenates
   `X_train`+`X_val` and `y_train`+`y_val`, refits one pipeline at
   `selected_C`, and computes `y_pred`/`y_proba` on the untouched `X_test`
   exactly once. Guard updated to the full seven-name prerequisite check.
5. **Section 4 (confusion matrix, accuracy/sensitivity/specificity,
   ROC/AUC)**, **Section 5 (threshold widget)**, and the Section 3 sample
   table all consume this same final `y_test`/`y_pred`/`y_proba` — no
   separate recomputation path, unchanged structurally from before.
6. **Section 6 (class imbalance)**: now reuses `selected_C` (previously
   the fixed `C_EXAMPLE`) as the one fixed setting across every ratio;
   its guard now also requires `selected_C` to exist.
7. **Text**: Section 3's header/overview, the opening "What this notebook
   covers" clause, the post-confusion-matrix reflection, the imbalance
   intro, and the "In summary" bullets were updated to describe
   validation-based selection honestly, replacing every claim that `C =
   1.0` was fixed in advance. No WP/implementation references were added
   to student-visible text (verified by the pre-existing
   `test_no_wp_or_script_references_in_student_text`, which still passes).

No k-fold cross-validation (`GridSearchCV`/`StratifiedKFold`/`cross_val_*`)
was reintroduced — WP19's "no early cross-validation" scope for Exercises
1–4 still holds; this is a single train/validation split, not k-fold CV.

## Validation table and selected C (from the executed reference notebook)

| C | validation AUC |
|---:|---:|
| 0.01 | 0.677710 |
| 0.1 | **0.684133** |
| 1.0 | 0.664188 |
| 10.0 | 0.656750 |
| 100.0 | 0.656412 |

**Selected C = 0.1** (highest validation AUC; no tie occurred in this run,
so the tie rule was not exercised, but is implemented and documented).

## Split sizes (out of 1004 total participants)

- `n_train = 564`, `n_val = 189`, `n_test = 251` — matches the WP's target
  of "approximately 564/189/251" exactly.
- Class balance: train autism rate 0.461, validation 0.460, test 0.462.
- All three participant sets confirmed pairwise disjoint by the executed
  check cell and by `tests/test_exercise_04_lite_notebook.py`'s structural
  check of the check cell's source.

## Final test-set metrics (refit on train+validation at C=0.1, evaluated once)

- Confusion matrix: **TN=77  FP=58  FN=59  TP=57**
- accuracy = **0.533865**
- sensitivity = **0.491379**
- specificity = **0.570370**
- AUC = **0.580268**

## Comparison with WP19's fixed C=1.0 result

WP19's fixed-`C=1.0` worked example (`scripts/classification_model_audit_result.json`,
unchanged by this WP): accuracy 0.545817, AUC 0.569221, confusion matrix
TN=75/FP=60/FN=54/TP=62, on a 753/251 train/test split (no validation
set). The validation-selected `C=0.1` on the new three-way split scores
**slightly lower accuracy** (0.533865 vs. 0.545817) and **slightly higher
AUC** (0.580268 vs. 0.569221) on its own, differently-sized test
participants (251 in both cases, but drawn from a different inner split of
the same 753 outer-training rows, since 189 of those 753 now serve as
validation rather than training). This is reported as the honest outcome
of the specified procedure — the grid, tie rule, and split were not
adjusted after seeing this result, and no attempt was made to force a
better- or worse-looking number. The two results are not expected to be
directly comparable in any case, since the WP19 audit's model fits on all
753 outer-training rows under a fixed C, where the live notebook now fits
the grid-search phase on only 564 of those rows and the final refit on all
753 — different training data from the same source split.

## Runtime (measured locally, sklearn 1.9.0 / this machine)

- Validation grid search (5 candidates): **~0.15s**.
- Final refit + test prediction: **~0.02s**.
- Total modeling runtime: **~0.17s** — well within JupyterLite's practical
  budget; no change needed to keep the grid "modest."

## Scope discipline

`scripts/classification_model_audit.py`,
`scripts/classification_model_audit_result.json`,
`scripts/export_classification_threshold_data.py`,
`scripts/export_classification_imbalance_data.py`, and their own tests
were **not touched** — confirmed by `git diff --stat main...HEAD` (see
exact changelog), which lists exactly 8 files, none under those paths.
The generator's docstring claim that its recipe matched that audit's
numbers "unchanged" was corrected (it no longer does, by design) without
editing the audit script or its committed JSON. `book/chapters/chapter_04/exercise_04.ipynb`
(the Jupyter Book redirect page) was not touched; its own test file
(`tests/test_exercise_04_transition_page.py`) was run as an unchanged
smoke check and passes (8/8).

## Tests run

| Command | Result |
|---|---|
| `python3 scripts/generate_exercise_04_notebook.py --check` | OK: all requested outputs are up to date |
| `.venv/bin/python -m unittest discover -s tests -p 'test_exercise_04_lite_notebook.py'` | **36/36 passed**, 0.08s (includes 7 new/rewritten assertions) |
| `.venv/bin/python -m unittest discover -s tests -p 'test_exercise_04_reference_execution.py'` | **17/17 passed**, 4.3s (executes the completed reference notebook end to end) |
| `.venv/bin/python -m unittest discover -s tests -p 'test_exercise_04_transition_page.py'` | **8/8 passed**, 0.04s (smoke check; unchanged) |

No test failed and needed a rerun — all failures observed during
development (3 in the lite-notebook suite, 4 in the reference-execution
suite, all anticipated by the WP's own scope description) were fixed by
the planned test rewrites, not by changing the model/text to dodge them.

## Local build and preview

```
.venv/bin/jupyter lite build --config book/lite/jupyter_lite_config.json \
  --lite-dir book/lite --output-dir /tmp/wp62_lite_build
cd /tmp/wp62_lite_build && python3 -m http.server 8890
```

Build succeeded in ~6s with no errors. Confirmed by `curl` that the built
page serves (HTTP 200) at:

`http://localhost:8890/notebooks/index.html?path=v2/exercise_04.ipynb`

The "completed path" itself (every activity filled in, run end to end) is
verified by the reference-execution test above, not by browser automation
— this notebook's Sections 5–6 use an `ipywidgets.Output()` context
manager that hangs `nbclient`'s real kernel with no frontend attached
(documented in `tests/test_exercise_04_reference_execution.py`'s own
docstring, pre-existing from WP44), so this project's established method
for Exercise 4 is exactly this offline shared-namespace execution, not a
Playwright/kernel-driven run. The live server above is left running for
manual visual confirmation in an actual browser.

## Deviations from the WP

None. The WP's own target numbers (564/189/251 split, a modest grid,
sub-second runtime) were all met without adjustment.

## Confirmation

Nothing was merged, pushed, or deployed. `main` remains at `7e3a348`. No
further WP was started. The branch `revise/exercise-04-validation-split`
is left in place for review.
