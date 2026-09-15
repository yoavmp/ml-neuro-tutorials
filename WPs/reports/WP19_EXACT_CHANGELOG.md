# WP19 Exact Changelog

## Commits (branch `revise/remove-early-cross-validation`, merged to `main`, plus one direct-to-`main` correction)

| Commit | Message |
|---|---|
| `ea0b34f` | WP19: add WP document (checkpoint before implementation) |
| `ea7c1f7` | WP19: remove early cross-validation and parameter tuning from Exercises 1-4 |
| `30caa85` | Merge revise/remove-early-cross-validation into main (WP19) |
| `1012d1a` | WP19 report: document fixed k=20/C=1.0, removed CV lessons, tests, local-only validation |
| *(this correction)* | WP19 correction: remove Exercise 2's hidden 5-fold KFold/cross_val_predict evaluation — see Claude's final response for the exact SHA |

Starting checkpoint tag: `wp19-start` → `03ac5cf`.

## Correction commit — files created

- (none)

## Correction commit — files modified

- `scripts/export_regression_catalog.py` — rewritten: removed `KFold` /
  `cross_val_predict` / `_fold_assignment`; added `_split_indices` (one
  fixed `train_test_split` on `protocol.holdout_split`, shared across every
  bundle x measure combination); `build_catalog` now fits
  `StandardScaler`+`LinearRegression` once per entry on the training rows
  and scores once on the held-out test rows; `SCHEMA_VERSION` 1 → 2; output
  fields renamed (`observed`→`observedTest`, `crossValidation`→
  `holdoutSplit`, `cvR2`→`testR2`, `cvMSE`→`testMSE`; `foldOf` removed);
  `validate_catalog` updated to match; disabled-reason text and identifiability
  threshold now reference `n_train` instead of `fold_train_n`.
- `book/_static/widgets/data/abide_regression_models.json` — regenerated
  (`--refresh`); new schema; `all-eligible__CT` testR2 = 0.469 (matches
  Exercise 2's own Section 2 worked example exactly).
- `book/config/abide_modeling.json` — removed `protocol.cross_validation`;
  reworded `catalog.identifiability_rule` and `catalog.note` to describe the
  fixed holdout split instead of folds/cross-validation.
- `book/downloads/chapter_02/exercise_02_portable.ipynb` — regenerated
  (`build_portable_notebook.py --write`) after the generator's iframe-
  replacement text was reworded.
- `interactive/src/regression-compare-data.ts` — schema rewritten:
  `holdoutSplit` replaces `crossValidation`; `observedTest` replaces
  `observed`; model fields `testR2`/`testMSE` replace `cvR2`/`cvMSE`;
  `schemaVersion` literal 1 → 2; validation logic updated to match.
- `interactive/src/regression-compare.ts` — removed the unused
  `ScatterPoint` interface and `scatterPoints` function (carried a `fold`
  field with no remaining meaning); doc comment reworded ("out-of-fold" →
  "held-out").
- `interactive/src/components/regression-compare.ts` — module doc comment
  reworded (adds the "exploration, not feature selection or optimization"
  framing); cohort-line and per-panel metrics text now report
  `holdoutSplit.nTrain`/`nTest` instead of fold count/seed; all
  `data.observed` references renamed to `data.observedTest`; y-axis title
  "(out of fold)" → "(held-out)"; metrics label "Out-of-sample R2"/"CV MSE"
  → "Held-out R2"/"held-out MSE".
- `book/_static/widgets/configs/regression_compare.json` — `description`,
  `instructions`, and `selectionBiasNote` reworded from
  "cross-validated"/"out-of-fold"/"folds" to "held-out"/"train/test split"
  language; `selectionBiasNote` now explicitly frames the activity as
  exploration, not feature selection or optimization.
- `scripts/build_portable_notebook.py` — `_CH2_IFRAME_REPLACEMENT` text
  reworded ("cross-validated performance... one fixed set of folds" →
  "held-out performance... one fixed train/test split").
- `tests/test_export_regression_catalog.py` — rewritten: removed
  `CvSelectionIsolation`-style fold checks; added
  `test_schema_version_is_2`, `test_no_cross_validation_artifacts_remain`,
  `test_canonical_recipe_matches_exercise_2s_own_worked_example`,
  `test_same_split_reused_across_every_bundle`,
  `test_scaler_and_model_fit_only_on_training_rows`; renamed
  `test_every_bundle_predicts_age_above_chance` →
  `test_most_bundles_predict_age_above_chance` (≥90% positive, not literally
  all — a single fixed split has higher variance than the old aggregated
  5-fold estimate for the 2 smallest/weakest entries).
- `tests/test_wp19_content_audit.py` — added `regression_compare.json` to
  `WIDGET_CONFIG_PATHS`; added `GENERATED_ARTIFACT_PATHS` (all 5 widget data
  artifacts) and `GeneratedArtifactContentAudit`; added
  `EXERCISE_2_EXPORTER_PATH` and `Exercise2ExporterImplementationAudit`
  (checks the executable code, not the module docstring, for `KFold`/
  `cross_val_predict`); extended `PROHIBITED_PATTERNS` with
  `cross_val_predict`, broadened `\bkfold\(` to `\bkfold\b`, and added bare
  `\bfold(s|ing)?\b`.
- `interactive/tests/regression-compare.test.ts` — removed the
  `scatterPoints` import and its `describe` block.
- `interactive/tests/regression-compare-data.test.ts` — fixture and every
  assertion rewritten for the new schema (`holdoutSplit`/`observedTest`/
  `testR2`/`testMSE`); committed-artifact test updated to check
  `nTrain`=753/`nTest`=251 and the ≥90%-positive threshold instead of 100%.
- `interactive/e2e/regression-compare.spec.ts` — metrics-text match
  `/Out-of-sample R2 = 0\.\d+/` → `/Held-out R2 = 0\.\d+/`.
- `interactive/e2e-book/chapter02.spec.ts` — same metrics-text match update.

## Correction commit — files unchanged (audited, no conflict found)

- `book/chapters/chapter_02/exercise_02.ipynb` — no code cell runs the
  regression-compare computation directly (iframe-only); the wording already
  reworded in the original WP19 pass ("one fixed evaluation procedure") now
  reads correctly and needed no further edits.
- `tests/test_exercise_02_notebook.py` — no assertions reference the
  catalog's internal schema; 30/30 still pass unchanged.
- `scripts/regression_model_audit.py` and
  `scripts/regression_model_audit_result.json` — the separate, developer-only
  FIQ/ridge/lasso regularization-preview audit (WP12); not part of Exercise
  2's student-facing content (ridge/lasso are not in the notebook) and not
  named in the correction's scope; left untouched.

## Files deleted

None.

## Files renamed

None (field renames within JSON/TS objects are listed above as
modifications, not file renames).

---

## Original WP19 pass (superseded in part by the correction above)

## Files created

- `WPs/WP19_REMOVE_EARLY_CROSS_VALIDATION_AND_PARAMETER_TUNING.md` (commit `ea0b34f`)
- `tests/test_wp19_content_audit.py` (commit `ea7c1f7`)
- `WPs/reports/WP19_REPORT.md` (this report; committed separately after this changelog is written)
- `WPs/reports/WP19_EXACT_CHANGELOG.md` (this file; committed separately)

## Files modified (commit `ea7c1f7`)

### Book content (notebooks, generated data, config)

- `book/chapters/chapter_01/exercise_01.ipynb` — reworded one forward-looking
  "cross-validation" mention (data-leakage sentence) to avoid naming CV.
- `book/chapters/chapter_02/exercise_02.ipynb` — reworded two mentions of
  "cross-validated R²"/"fixed set of folds" and one questions-cell mention;
  no code, analysis, or output changed.
- `book/chapters/chapter_03/exercise_03.ipynb` — removed the "Choosing k
  honestly" CV-selection section (4 cells), removed a duplicate post-splice
  fit cell; added 2 new cells (`K_EXAMPLE = 20` policy + fit); reworded 8
  markdown/code spots (see WP19_REPORT.md); re-executed end-to-end.
- `book/chapters/chapter_04/exercise_04.ipynb` — removed the "Choosing C
  honestly" section (5 cells: markdown + GridSearchCV code + plot +
  explanatory text); added 2 new cells (`C_EXAMPLE = 1.0` policy + constant);
  reworded 5 markdown/code spots + replaced review question 1; re-executed
  end-to-end.
- `book/downloads/chapter_01/exercise_01_portable.ipynb` — regenerated
  (`build_portable_notebook.py --write`).
- `book/downloads/chapter_02/exercise_02_portable.ipynb` — regenerated.
- `book/downloads/chapter_03/exercise_03_portable.ipynb` — regenerated;
  smoke-executed.
- `book/downloads/chapter_04/exercise_04_portable.ipynb` — regenerated;
  smoke-executed.
- `book/config/abide_modeling.json` — `knn`: removed `cv_for_k_selection`;
  renamed `selected_k` (15) → `worked_example_k` (20) with new rationale.
  `classification`: rewrote `model` string; removed `cv_for_c_selection`;
  renamed `selected_C` (0.01) → `worked_example_C` (1.0) with new
  rationale; updated `imbalance_activity.split_seeds_note` reference.
- `book/_static/widgets/configs/knn_explore.json` — `defaultK`:
  `"validation-optimal"` → `20`.
- `book/_static/widgets/data/abide_knn_explore_manifest.json` —
  regenerated (`export_knn_explore_data.py --refresh`); field
  `selectedKFromAudit` → `workedExampleK` (15 → 20); binary payload
  unchanged (byte-identical).
- `book/_static/widgets/data/abide_knn_abc_manifest.json` — regenerated
  (`export_knn_abc_data.py --refresh`); field `selectedKFromAudit` →
  `workedExampleK` (15 → 20); binary payload unchanged.
- `book/_static/widgets/data/abide_classification_threshold.json` —
  regenerated (`export_classification_threshold_data.py --refresh`);
  field `selectedC` → `modelC`; C 0.01 → 1.0; AUC/accuracy updated to
  0.569/0.546; labels/probabilities recomputed.
- `book/_static/widgets/data/abide_classification_imbalance.json` —
  regenerated (`export_classification_imbalance_data.py --refresh`);
  field `selectedC` → `modelC`; C 0.01 → 1.0; all 30 ratio/seed entries
  recomputed.

### Developer scripts

- `scripts/knn_model_audit.py` — rewritten: removed `_cv_select_k`,
  `CANDIDATE_KS`/`_k_grid`, `KFold`/`cross_val_score` usage; added
  `K_EXAMPLE = 20`; each of the 3 candidate feature spaces now evaluated
  once at the fixed k.
- `scripts/classification_model_audit.py` — rewritten: removed `_select_c`,
  `C_GRID`, `GridSearchCV`/`StratifiedKFold` usage; added `C_EXAMPLE = 1.0`;
  `select_canonical_c()` now returns the constant.
- `scripts/knn_model_audit_result.json` — regenerated (`--run`); schema
  changed (no `cv_curve`/`selected_k`; new `k_example`).
- `scripts/classification_model_audit_result.json` — regenerated
  (`--run`); schema changed (no `cv_selection`; `protocol.model` cites
  fixed C).
- `scripts/export_knn_explore_data.py` — reads `knn_cfg["worked_example_k"]`
  instead of `["selected_k"]`; writes `workedExampleK`; summary print
  label updated.
- `scripts/export_knn_abc_data.py` — same rename; default-k error message
  updated.
- `scripts/export_classification_threshold_data.py` — writes `modelC`
  instead of `selectedC`; docstring/comments reworded (fixed value, not
  CV-selected).
- `scripts/export_classification_imbalance_data.py` — writes `modelC`
  instead of `selectedC`; validator checks against
  `classification.worked_example_C`; docstring/comments reworded.
- `scripts/build_portable_notebook.py` — fixed a latent bug: the Exercise 3
  ABC-activity static-replacement code cell referenced `K_SELECTED`
  (undefined after the canonical notebook's CV section was removed);
  changed to `K_EXAMPLE`.
- `scripts/build_course_overview_docx.py` — Exercise 3/4 row text updated
  (no CV claim); added `_set_row_cant_split` (every row gets
  `w:cantSplit`) and `_tighten_paragraph` (reduced spacing) to fix the
  WP18 row-splitting layout defect.

### Frontend (TypeScript)

- `interactive/src/knn-explore-data.ts` — schema/type/validation field
  `selectedKFromAudit` → `workedExampleK`.
- `interactive/src/knn-abc-data.ts` — same rename.
- `interactive/src/components/knn-abc.ts` — default-k source
  `data.selectedKFromAudit` → `data.workedExampleK`; error message updated.
- `interactive/src/components/classification-imbalance.ts` — comment
  reworded (fixed C, not CV-selected).
- `interactive/src/classification-imbalance-data.ts` — schema field
  `selectedC` → `modelC`.

### Tests

- `tests/test_knn_model_audit.py` — removed `CvSelectionIsolation` class
  and CV-curve assertions; added `test_k_example_is_20_everywhere`;
  renamed/rewrote assertions to match the fixed-k schema.
- `tests/test_classification_model_audit.py` — removed
  `SelectCIsolation`/CV assertions; added `test_c_is_fixed_at_1_0_by_course_design`,
  `SelectCanonicalCIsolation`.
- `tests/test_exercise_03_notebook.py` — allowed `wp19-` cell-id prefix;
  replaced the CV-selection test with `test_k_is_fixed_by_course_design_not_a_search`;
  updated `test_uses_k_not_n_for_neighbour_count`,
  `test_executable_cv_reproduces_the_committed_audit_selected_k`,
  `test_executed_outputs_are_present_and_teach_the_point` for k=20/R²=0.664.
- `tests/test_exercise_04_notebook.py` — allowed `wp19-` cell-id prefix;
  replaced the CV-selection test with `test_c_is_fixed_by_course_design_not_a_search`;
  removed the stale "tuning is not promised to help" text-match test; updated
  cell-id-based `C_SELECTED` → `C_EXAMPLE` references.
- `tests/test_export_knn_explore_data.py` / `test_export_knn_abc_data.py` —
  `selectedKFromAudit` → `workedExampleK` (value 15 → 20).
- `tests/test_export_classification_threshold_data.py` /
  `test_export_classification_imbalance_data.py` — `selectedC` → `modelC`;
  renamed/reworded the stale "not the old untuned default" test (C is now
  intentionally the untuned default, 1.0, by course design).
- `tests/test_course_overview_docx.py` — updated
  `EXPECTED_COVERAGE_PHRASES`; added `PROHIBITED_COVERAGE_PHRASES`,
  `test_no_early_cross_validation_or_tuning_claim`,
  `test_rows_are_marked_cant_split`.
- `interactive/tests/classification-imbalance-data.test.ts` — fixture
  `selectedC: 0.01` → `modelC: 1.0`.
- `interactive/tests/knn-abc-data.test.ts` — fixture/assertions
  `selectedC` → `workedExampleK` (1 → default; 15 → 20 in the committed
  case).
- `interactive/tests/knn-explore-data.test.ts` — fixture/assertions
  `selectedC` → `workedExampleK`.
- `interactive/e2e/knn-explore.spec.ts` — default-k expectations `"17"` →
  `"20"` (7 occurrences); one test title reworded.
- `interactive/e2e/knn-abc.spec.ts` — default-k expectations `"15"` →
  `"20"` (3 occurrences); one test title reworded.
- `interactive/e2e-book/chapter03.spec.ts` — default-k expectations `"17"`
  → `"20"` (3 occurrences, including one fixed in the post-gate rerun).
- `interactive/e2e-book/chapter04.spec.ts` — default-worked-example-k title
  reworded; AUC expectation `0.593` → `0.569` (2 occurrences, fixed in the
  post-gate rerun).

## Files unchanged (audited, no conflict found)

- `book/chapters/chapter_01/exercise_01.ipynb` analyses/outputs/interactives
  (only the one wording fix above).
- `book/chapters/chapter_02/exercise_02.ipynb` analyses/outputs/interactives
  in this original pass, including the `regression-compare` KFold-based
  evaluation pipeline (`scripts/export_regression_catalog.py`,
  `interactive/src/regression-compare*.ts`), left untouched here as a
  judgment call — **superseded by the correction above**: that pipeline's
  hidden cross-validation was removed and its model results were recomputed
  under a fixed train/test split.
- All WP01–WP18 WP documents and reports (historical records, not rewritten).
- `WPs/reports/WP16_ARCHITECT_REPORT.md` (pre-existing, whitelisted,
  untouched, still untracked).

## Files deleted

None.

## Files renamed

None (field renames within JSON/TS objects are listed above as
modifications, not file renames).
