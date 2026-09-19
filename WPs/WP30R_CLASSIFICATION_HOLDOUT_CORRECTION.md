# WP30R — Classification-Tree Holdout Correction

## Purpose

Correct one methodological inconsistency found during review of WP30. The optional
classification-tree depth audit currently performs cross-validation on all 1,004 eligible
participants. Although it never explicitly loads the saved outer-test indices, that full cohort
necessarily includes Exercise 3's locked test participants.

Rerun the classification-depth audit using only Exercise 3's training/development partition,
reapply WP30's original inclusion rule unchanged, and update or remove the student-facing figure
according to the result.

This is a narrow correction WP. Do not redesign Exercise 6 or deploy anything.

## 1. Git safety

1. Begin on `fix/wp30-exercise6-refinements`.
2. Record the actual starting SHA and `git status --short --branch`.
3. The only permitted pre-existing untracked files are:
   - `WPs/reports/WP16_ARCHITECT_REPORT.md`
   - `WPs/reports/WP21_DEPLOYMENT_REPORT.md`
   - this WP specification, if it has not yet been committed
4. Stop if anything else is unexpectedly modified or untracked. Do not reset, stash, delete, or
   overwrite it.
5. Create `fix/wp30r-classification-holdout`.
6. Save this file as `WPs/WP30R_CLASSIFICATION_HOLDOUT_CORRECTION.md` and commit it as the first
   checkpoint before implementation changes.
7. Work locally only. Do not merge, push, deploy, monitor GitHub Actions, or start WP31.

## 2. Reconstruct the exact Exercise 3 outer split

Use the existing Exercise 3 classification cohort, target coding, manifest, and split settings.
Do not invent a new split.

- Reconstruct the same outer train/test partition used by Exercise 3 from
  `classification.holdout_split`.
- Use stable participant-row identifiers or indices so that the audit can prove which rows are in
  each partition.
- The outer test rows must be excluded before any classification-depth cross-validation begins.
- Assert that development and outer-test participant sets are disjoint and their union equals the
  full eligible cohort.
- Record the eligible, development, and outer-test sample sizes and class counts in the committed
  audit result and final report.

Do not evaluate any tree on the locked outer-test rows. Do not use them to choose depth, confirm
the narrative, or decide whether the figure should remain.

## 3. Repeat the prespecified depth audit within development data only

Keep every WP30 setting unchanged except the participant pool:

- target: autism diagnosis, coded exactly as in Exercise 3;
- predictors: the same 360 cortical-thickness features;
- estimator: `DecisionTreeClassifier`;
- `min_samples_leaf=5`;
- `max_depth=1..10`;
- `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` applied only to the outer-training /
  development rows;
- metric: mean training and validation ROC AUC from predicted probabilities;
- natural feature-column order already used consistently by the Exercise 6 notebook and audit;
- same displayed-precision shallower-depth tie rule.

Run this corrected audit once. Do not scan alternative seeds, folds, metrics, leaf sizes, feature
orders, depth ranges, or participant subsets after seeing the result.

## 4. Reapply the existing inclusion rule exactly

Retain the classification figure only if both conditions remain true:

1. the highest mean validation ROC AUC occurs at `max_depth >= 3`; and
2. it exceeds the depth-2 mean validation ROC AUC by at least `0.01`.

If multiple depths tie at the displayed precision, prefer the shallowest one as already
specified. Do not weaken or reinterpret either condition.

### If the corrected audit passes

- Keep the second classification figure.
- Update its plotted values, annotations, executed output, and nearby prose to the corrected
  development-only results.
- State concisely that depth was compared by cross-validation within the development data and
  that the locked test data were not used.
- Retain the existing cautions: ROC AUC is higher-is-better, MSE is lower-is-better,
  classification is not inherently more complex than regression, and modest AUC values should
  not be presented as a strong classifier.

### If the corrected audit fails

- Remove the classification figure and its associated student-facing explanation from both the
  canonical and portable notebooks.
- Leave the original 360-feature age-regression complexity figure unchanged as the only figure in
  that subsection.
- Keep the corrected classification audit result committed for reproducibility, but do not
  discuss the failed exploratory contrast in student-facing material.
- Update tests so figure presence is conditional on the committed audit's corrected inclusion
  result.

## 5. Correct misleading provenance statements

Remove or revise any assertion that the earlier full-cohort audit preserved the outer holdout
merely because it did not read a stored test-index object. The corrected evidence must be based on
participant-set exclusion.

Update the audit schema/result and tests so they demonstrate all of the following:

- CV input participant IDs/indices are a subset of Exercise 3's development partition;
- CV input and outer-test participant sets have an empty intersection;
- CV input size equals the development-partition size;
- the audit never evaluates or reports outer-test ROC AUC;
- the inclusion result is reproducible from the corrected validation-AUC curve.

## 6. Files and generated artifacts

Update every affected layer, as applicable:

- `scripts/decision_tree_model_audit.py`;
- `scripts/decision_tree_model_audit_result.json`;
- `book/config/abide_modeling.json` only if its provenance/rationale needs clarification;
- `book/chapters/chapter_06/exercise_06.ipynb`;
- `book/downloads/chapter_06/exercise_06_portable.ipynb`;
- focused Python/notebook tests;
- built-book tests if figure presence, text, or expected values change.

Do not change either Exercise 6 widget, the greedy dataset, the regression complexity curve, the
ensemble activity, or any earlier notebook unless a narrowly necessary stale assertion refers to
the corrected classification audit.

Do not update the Word overview.

## 7. Required validation

Run each gate once. If this WP causes a failure, make one focused correction and rerun only the
failed gate once. Do not rerun passing gates unless their inputs changed.

1. Run the corrected decision-tree audit and its `--check` mode.
2. Run focused decision-tree-audit and Exercise 6 notebook tests.
3. Regenerate the Exercise 6 portable notebook and run deterministic `--check`.
4. Run the dedicated portable-notebook smoke execution that WP30 did not run separately.
5. Run the full Python test suite once.
6. Run frontend typecheck only if frontend files changed.
7. Run one production frontend build only if frontend inputs changed; otherwise document why it
   was unnecessary.
8. Run one clean Jupyter Book build.
9. Run focused built-book Exercise 6 Playwright tests.
10. Run launch-button and relevant dark-mode checks if the classification figure remains or its
    structure changes.

Do not use arbitrary sleeps, skipped tests, weakened assertions, global retries, or repeated
workflow polling.

## 8. Manual verification

Inspect the built Exercise 6 page and confirm:

- the regression complexity figure remains unchanged;
- the classification figure is present if and only if the corrected inclusion rule passes;
- any retained classification curve and prose show development-only results;
- no student-facing text implies that locked test rows were used for depth comparison;
- light and dark rendering remain readable;
- the portable notebook matches the canonical decision about including or removing the figure.

## 9. Reports and stopping point

Create and commit:

- `WPs/reports/WP30R_REPORT.md`
- `WPs/reports/WP30R_EXACT_CHANGELOG.md`

The report must include:

- starting and final branch/SHA/status;
- exact reconstruction of the Exercise 3 outer split;
- eligible/development/test sample sizes and class counts;
- proof of zero participant overlap between CV data and outer test;
- the complete corrected depth-by-depth training and validation ROC AUC table;
- the corrected best depth, depth-2 AUC, margin, and inclusion decision;
- whether the student-facing classification figure was retained or removed;
- every test/build run, failure, correction, and rerun;
- deviations and anything requiring user attention.

Stop after committing implementation and reports locally. Do not merge, push, deploy, monitor
GitHub Actions, or begin WP31.
