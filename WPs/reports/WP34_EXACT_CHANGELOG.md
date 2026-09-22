# WP34 Exact Changelog

Every file added, modified, or removed by WP34 (Part A: Exercise 8 PCA+KNN
correction; Part B: Exercise 9, Advanced Models), relative to the starting
branch tip `feature/wp33-exercise8-unsupervised-learning` @ `a5c6971`.

## Specification checkpoint (already committed before implementation)

- **`WPs/WP34_EXERCISE_9_ADVANCED_MODELS.md`** (added) — the WP34
  specification, committed as the initial checkpoint (`9daffdc`) before
  implementation.

## Manifest

- **`book/config/abide_modeling.json`** (modified) — `unsupervised.
  supervised_pipeline` rewritten for PCA+KNN (`model`, `component_grid`
  narrowed to `[5,10,20,50,100]`, new `k_grid: [5,10,20,40]`, corrected
  `dev_split.random_state` from a stale, unused `7` to the actually-used
  `42`, updated notes); added the top-level `advanced_models` key
  (`recipe`, `pcr_pls_activity` generating-process/preset parameters,
  `svm_activity` generating-process/grid parameters, `abide_comparison`
  outer/inner CV settings, all five models' pipelines and grids, the
  gamma-grid justification, and the documented `LinearSVR` runtime
  substitution note). Verified self-consistent by
  `scripts/abide_modeling_data.py --check`.

## Exercise 8 (Part A)

- **`book/chapters/chapter_08/exercise_08.ipynb`** (modified) — section 8
  rewritten in place (same cell count/position): title, teaching text, and
  code replaced for PCA+KNN vs. raw-feature KNN; imports cell's
  `LinearRegression` replaced with `KNeighborsRegressor`; re-executed with
  0 stored errors.
- **`book/downloads/chapter_08/exercise_08_portable.ipynb`** (modified,
  regenerated) — via `scripts/build_portable_notebook.py --write
  --notebook chapter_08`; smoke-executed outside the repository tree with
  0 errors.
- **`scripts/pca_kmeans_audit.py`** (modified) — `_supervised_pipeline`
  rewritten for the joint (n_components, k) grid search plus the
  raw-feature KNN comparison; `validate()` and `_print_summary()` updated
  to match the new result keys; module docstring updated.
- **`scripts/pca_kmeans_audit_result.json`** (modified, regenerated) — via
  `pca_kmeans_audit.py --run`; re-validated offline (`--check`).
- **`scripts/smoke_portable_notebook.py`** (modified) — `chapter_08`'s
  expected-output strings updated to the new PCA+KNN section's printed
  text; module docstring updated.

## Exercise 9 (Part B)

- **`book/chapters/chapter_09/exercise_09.md`** (removed) — the WP25-era
  placeholder, replaced by the real notebook below.
- **`book/chapters/chapter_09/exercise_09.ipynb`** (added) — the canonical
  Exercise 9 notebook, 27 cells, executed in place (see `WP34_REPORT.md`
  §5 for the exact section list).
- **`book/downloads/chapter_09/exercise_09_portable.ipynb`** (added,
  generated) — via `scripts/build_portable_notebook.py --write --notebook
  chapter_09`; smoke-executed outside the repository tree with 0 errors.

## Portable-notebook generator

- **`scripts/build_portable_notebook.py`** (modified) — added
  `PUBLISHED_PAGE_CH9`, `_CH9_BANNER`, `_CH9_SETUP`,
  `_CH9_PCR_PLS_IFRAME_REPLACEMENT`, `_CH9_SVM_IFRAME_REPLACEMENT`, and the
  `CHAPTER_09` `NotebookSpec`; registered it in `NOTEBOOKS`; updated the
  module docstring's `--notebook` choices list and the "Exercises 10-12
  are placeholders" note (previously "9-12").

## Audit script (new)

- **`scripts/advanced_models_audit.py`** (added) — `--run`/`--check`
  audit: identical outer/inner nested cross-validation for five models
  (standardized OLS, PCR, PLS, `LinearSVR`, RBF `SVR`) on the canonical
  1,004-participant, 360-feature, age-target cohort; records every inner
  candidate, every outer-fold selection and score, mean/SD summaries, and
  every captured convergence warning.
- **`scripts/advanced_models_audit_result.json`** (added, generated) — the
  committed audit result (`advanced_models_audit.py --run`), re-validated
  offline (`--check`).

## Widget export scripts (new)

- **`scripts/export_pcr_pls_widget.py`** (added) — `--refresh`/`--check`:
  the fixed synthetic 2-D predictor cloud, the three presets' target
  values, and the precomputed PCR/PLS catalogue (method × n_components ×
  preset).
- **`scripts/export_svm_explorer_widget.py`** (added) — `--refresh`/
  `--check`: two fixed synthetic 2-D classification datasets and the
  precomputed SVC catalogue (dataset × kernel × C × gamma-where-relevant),
  including the fixed decision-grid mesh (compact digit-string rows) and
  support-vector ids. Fits inside a `Pipeline(StandardScaler, SVC(...))`
  (added after an initial unstandardized draft produced a pathologically
  slow poly-kernel fit).

## Widget configs and data artifacts (new)

- **`book/_static/widgets/configs/pcr_pls_explore.json`** (added)
- **`book/_static/widgets/configs/svm_explorer.json`** (added; the
  `instructions` field was trimmed once during manual review to remove a
  sentence duplicated by the component's own hardcoded conceptual-
  exploration note — see `WP34_REPORT.md` §9)
- **`book/_static/widgets/data/pcr_pls_explore.json`** (added, generated;
  17.4 KiB uncompressed / 3.4 KiB gzip)
- **`book/_static/widgets/data/svm_explorer.json`** (added, generated;
  321.5 KiB uncompressed / 9.6 KiB gzip — decision grids encoded as
  digit-string rows rather than nested number arrays to avoid a ~10x
  larger pretty-printed artifact)

## Interactive runtime (TypeScript)

- **`interactive/src/config.ts`** (modified) — added the `pcr-pls-explore`
  and `svm-explorer` config schemas (including the `pcrPlsMethod`/
  `pcrPlsPreset`/`svmExplorerDataset`/`svmExplorerKernel` enums) and
  registered both in the discriminated config union; exported their
  inferred types.
- **`interactive/src/components/registry.ts`** (modified) — imported and
  registered `pcrPlsExploreComponent` and `svmExplorerComponent`.
- **`interactive/src/pcr-pls-explore-data.ts`** (added) — Zod schema +
  `catalogKey()`/`catalogEntryFor()`/`targetsFor()`/`directionLinePoints()`
  (pure geometry).
- **`interactive/src/components/pcr-pls-explore.ts`** (added) — Activity
  A's DOM/Plotly mount: method/n-components/preset selects, predictor
  cloud + first-component-direction overlay, observed-vs-predicted panel,
  stats, construction note.
- **`interactive/src/svm-explorer-data.ts`** (added) — Zod schema +
  `catalogKey()`/`catalogEntryFor()`/`decodeDecisionGrid()`/
  `decodeDecisionGridRow()`.
- **`interactive/src/components/svm-explorer.ts`** (added) — Activity B's
  DOM/Plotly mount: dataset/kernel/C/gamma selects (gamma disabled, not
  silently ignored, for the linear kernel) + Reset, filled decision-region
  contour, train/validation markers, support-vector markers, stats.

## Frontend tests (new)

- **`interactive/tests/pcr-pls-explore-data.test.ts`** (added) — schema +
  pure-helper tests (12 tests).
- **`interactive/tests/svm-explorer-data.test.ts`** (added) — schema +
  pure-helper tests (12 tests).

## Playwright specs (new / modified)

- **`interactive/e2e/pcr-pls-explore.spec.ts`** (added) — standalone
  Activity A checks: defaults, method/preset-driven redraw, PCR/PLS
  convergence at 2 components, fixed predictor-cloud positions across
  control changes, narrow viewport, missing-config error panel.
- **`interactive/e2e/svm-explorer.spec.ts`** (added) — standalone Activity
  B checks: defaults, gamma disabled/enabled by kernel, dataset/kernel/C
  control wiring, Reset, narrow viewport, missing-config error panel.
- **`interactive/e2e/plot-visual-policy.spec.ts`** (modified) — added 2
  chart entries (`pcr-pls-explore` cloud, `svm-explorer`) to the shared
  presentation-policy regression guard.
- **`interactive/e2e-book/chapter09.spec.ts`** (added) — built-book
  structural + interaction checks for both new activities (title, iframe
  count, Colab button, control wiring, refresh-restores-defaults, narrow
  viewport).
- **`interactive/e2e-book/chapter09-dark-mode.spec.ts`** (added) —
  dedicated built-book dark-mode regression guard for both new activities,
  following the `chapter08-dark-mode.spec.ts` template.
- **`interactive/e2e-book/launch-buttons.spec.ts`** (modified) — added a
  "Chapter 9" case to `CHAPTERS`; moved the "placeholder gets no Colab
  button" assertion from Exercise 9 to Exercise 10.

## Launch-button registration

- **`book/_static/launch-buttons.js`** (modified) — registered
  `chapters/chapter_09/exercise_09.html` → the new portable notebook;
  updated the "placeholder Exercises 9-12" comment to "10-12" (both
  occurrences).

## Python tests (new / modified)

- **`tests/test_exercise_09_notebook.py`** (added) — 46 tests: opening
  structure, PCR-introduced-here-not-earlier, PCR/PLS section content and
  reproduction cell, SVM section content and reproduction cell, ABIDE
  comparison structure/grids/results/discussion, strengths/weaknesses
  table, test-oriented questions with dropdown answers, launch-button/
  portable-notebook registration.
- **`tests/test_advanced_models_audit.py`** (added) — 13 tests
  re-validating the committed audit result (grids, identical folds, fresh
  minimum-inner-MSE recomputation, no non-finite values).
- **`tests/test_export_pcr_pls_widget_data.py`** (added) — 13 tests,
  including a fresh full-recomputation semantic diff and the PCR-direction
  -is-preset-independent / PLS-direction-changes-with-preset invariants.
- **`tests/test_export_svm_explorer_widget_data.py`** (added) — 11 tests,
  including full-grid combination coverage and the
  support-vectors-are-training-rows invariant.
- **`tests/test_exercise_08_notebook.py`** (modified) — `SECTION_TITLES`
  updated for the renamed section 8; `SupervisedPipeline` test class
  rewritten for the PCA+KNN pipeline and its raw-feature comparison; added
  `test_pcr_is_not_introduced_here`; renamed/updated the launch-button
  range test from "9-12" to "10-12".
- **`tests/test_pca_kmeans_audit.py`** (modified) — updated for the new
  `pca_knn_cv_results`/`raw_knn_cv_results` result shape and grids.
- **`tests/test_book_structure.py`** (modified) — extended the
  `.ipynb`-exists range to include chapter 9 and the `.md`-placeholder
  range to start at 10.
- **`tests/test_exercise_04_notebook.py`**,
  **`tests/test_exercise_06_notebook.py`**,
  **`tests/test_exercise_07_notebook.py`** (modified) — the "placeholder,
  no launch button / no portable notebook" ranges moved from `range(9,
  13)` to `range(10, 13)`.
- **`tests/test_placeholder_exercises.py`** (modified) — removed exercise
  9 from `PLACEHOLDER_TITLES` (now 10-12) and updated the module
  docstring.
- **`tests/test_wp25_content_audit.py`** (modified) — corrected
  `EXERCISE_TITLES[9]` from the stale `"Exercise 9: Advanced Models and
  Model Comparison"` to WP34's required `"Exercise 9: Advanced Models"`
  (flagged for attention, see `WP34_REPORT.md` §9); updated the matching
  required title-case phrase; updated `_title_of`'s `.ipynb`-vs-`.md`
  cutoff from `n <= 8` to `n <= 9`; extended the final-project-reference
  and no-duplicate-copy checks' chapter ranges to include chapter 9.

## Reports

- **`WPs/reports/WP34_REPORT.md`** (added) — this report.
- **`WPs/reports/WP34_EXACT_CHANGELOG.md`** (added) — this file.

## Untouched (confirmed)

- `book/syllabus.md` — not opened or modified.
- `course_overview/` (Word course-overview document) — not opened or
  modified.
- `book/_toc.yml` — not modified (already referenced chapter 9
  extensionlessly).
- `WPs/reports/WP16_ARCHITECT_REPORT.md`,
  `WPs/reports/WP21_DEPLOYMENT_REPORT.md` — preserved untracked, as
  required by WP34 §2.5.
