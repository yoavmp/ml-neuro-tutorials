# WP28 Exact Changelog

Diff base: `cc711b9` (WP27R, tip of `fix/wp27r-validation-refinements`) → WP28 implementation HEAD
`2470b62e2d3c031661598621de27b3cf9426c4d2`, on `feature/wp28-exercise5-regularization-feature-selection`.
39 files changed (`git diff --stat cc711b9..2470b62`: 6084 insertions, 336 deletions). This file and
`WPs/reports/WP28_REPORT.md` are committed after `2470b62` and are not included in that diff.

## Created

- `WPs/WP28_EXERCISE_5_REGULARIZATION_AND_FEATURE_SELECTION.md` — WP28 specification.
- `book/chapters/chapter_05/exercise_05.ipynb` — the Exercise 5 notebook (45 cells).
- `book/downloads/chapter_05/exercise_05_portable.ipynb` — its portable/Colab derivative (47 cells).
- `book/_static/widgets/configs/regularization_explore.json` — "Shrink the Coefficients" activity config.
- `book/_static/widgets/data/regularization_explore.json` — precomputed widget data artifact (83,462 bytes raw / 32,577 bytes gzip).
- `scripts/regularization_model_audit.py` — dev-split alpha curves, nested-CV comparison, `SelectKBest` k-grid, correlation ranking, and stepwise-selection audit.
- `scripts/regularization_model_audit_result.json` — committed audit result (13,304 bytes).
- `scripts/export_regularization_widget.py` — independent exporter for the widget data artifact.
- `interactive/src/components/regularization-explore.ts` — the new widget component.
- `interactive/src/regularization-explore.ts` — pure helpers (`sharedAxisRange`, `formatAlpha`, `clampAlphaIndex`).
- `interactive/src/regularization-explore-data.ts` — zod schema + parser for the data artifact.
- `interactive/tests/regularization-explore.test.ts` — 8 unit tests for the pure helpers.
- `interactive/tests/regularization-explore-data.test.ts` — 7 unit tests for the data parser.
- `interactive/e2e/regularization-explore.spec.ts` — 12 standalone Playwright tests.
- `interactive/e2e-book/chapter05.spec.ts` — 11 built-book Playwright tests for both Exercise 5 activities.
- `interactive/e2e-book/chapter05-visual-policy.spec.ts` — renamed from `chapter02-visual-policy.spec.ts` (see Renamed, below); no new file beyond the rename.
- `tests/test_exercise_05_notebook.py` — 40 focused structural/leakage/content tests for the notebook.

## Renamed

- `interactive/e2e-book/chapter02-visual-policy.spec.ts` → `interactive/e2e-book/chapter05-visual-policy.spec.ts`
  (git-detected as a 94%-similarity rename). The file's 12 tests exclusively check the
  regression-compare activity's plot geometry (x-axis-title clearance, comparison-card background)
  on the built page; since that activity moved to Exercise 5, `CHAPTER_URL` and both
  `test.describe` labels were retargeted from Chapter 2 to Chapter 5. Found only by running the
  *full* built-book Playwright suite, not the Exercise-2/5-scoped specs.

## Deleted

- `book/chapters/chapter_05/exercise_05.md` — the 3-line placeholder, replaced by the `.ipynb` above.
  History preserved via `git log` (origin commit `db4eda9`, WP25).

## Modified

- `book/_static/launch-buttons.js` — added `chapters/chapter_05/exercise_05.html` →
  `book/downloads/chapter_05/exercise_05_portable.ipynb` to `PAGE_TO_PORTABLE`; updated the header
  comment's placeholder range from "Exercises 5-12" to "Exercises 6-12".
- `book/chapters/chapter_02/exercise_02.ipynb` — removed cells `wp25-010`, `wp11-041`, `wp11-042`
  ("Comparing feature sets" prose, its iframe, its think-first box); reworded the `## Bonus` intro
  sentence to singular; renumbered "Questions to take away" (removed old Q13, 14→13, 15→14).
  44 cells → 41 cells.
- `book/config/abide_modeling.json` — added a top-level `regularization` key (canonical recipe,
  `dev_split` identical to `knn.dev_split`, `ridge_alpha_grid`/`lasso_alpha_grid`, nested-CV
  protocol description, audit/export script references, stepwise candidate bundle).
- `book/downloads/chapter_02/exercise_02_portable.ipynb` — regenerated; drops the moved activity's
  pointer cell. 46 cells → 43 cells.
- `interactive/e2e-book/chapter02.spec.ts` — removed the regression-compare `test.describe` block
  (12 tests, moved to `chapter05.spec.ts`); added a 1-test "structure" block confirming Exercise 2
  embeds exactly one iframe (`knn_explore.json`) and none for `regression_compare.json`.
- `interactive/e2e-book/launch-buttons.spec.ts` — added Chapter 4 (§3 stale-test fix) and Chapter 5
  (§6) to the `CHAPTERS` loop; the placeholder-guard test retargeted twice, ending on Exercise 6.
- `interactive/e2e-book/wp22-cross-chapter-dark-mode.spec.ts` — split the former "Exercise 2 —
  regression feature-set comparison and KNN exploration" dark-mode test into "Exercise 2 — KNN
  exploration" (unchanged assertions, regression-compare part removed) and a new "Exercise 5 —
  feature-set comparison and regularization exploration" test.
- `interactive/e2e/plot-visual-policy.spec.ts` — added `regularization-explore` to the shared
  `CHARTS` policy-check array.
- `interactive/src/components/registry.ts` — imported and registered `regularizationExploreComponent`.
- `interactive/src/components/regression-compare.ts` — header comment: "Exercise II" → "Exercise 5"
  (comment only; component unchanged).
- `interactive/src/config.ts` — added `regularizationExploreModel` enum and
  `regularizationExploreConfig` schema; added both to `activityConfigSchema`'s discriminated union
  and the exported-type list.
- `interactive/src/regression-compare-data.ts` — header comment: "Exercise II" → "Exercise 5"
  (comment only).
- `interactive/src/regression-compare.ts` — header comment: "Exercise II" → "Exercise 5" (comment only).
- `interactive/tests/config.test.ts` — added 4 tests for the `regularization-explore` config schema.
- `scripts/build_portable_notebook.py` — added `PUBLISHED_PAGE_CH5`; moved the regression-compare
  `iframe_replacements` entry out of `CHAPTER_02` (its banner text also updated to singular); added
  `_CH5_BANNER`/`_CH5_SETUP`/two iframe-replacement constants and a `CHAPTER_05` `NotebookSpec`,
  registered in `NOTEBOOKS`; updated the module docstring and the `--notebook` choices comment.
- `tests/test_book_structure.py` — `test_exercises_one_through_twelve_follow_in_order`: the
  ipynb/md chapter split moved from `(1,2,3,4)` / `range(5,13)` to `(1,2,3,4,5)` / `range(6,13)`.
- `tests/test_exercise_02_notebook.py` — `test_bonus_contains_feature_set_and_sample_size_as_subsections`
  → `test_bonus_contains_only_sample_size_subsection` (asserts absence, not presence, of the moved
  subsection); `test_two_iframes_regression_compare_and_knn_explore_each_once` →
  `test_one_iframe_knn_explore_only`; removed `test_activity_iframe_points_at_the_regression_compare_config`;
  `test_age_literature_citations_present` → `test_age_literature_named_without_requiring_doi_links`
  (no longer requires the DOI strings, which moved to Exercise 5).
- `tests/test_exercise_04_notebook.py` — `test_exercises_5_through_12_remain_placeholders_without_launch_buttons`
  → `test_exercises_6_through_12_remain_placeholders_without_launch_buttons`, range `range(5,13)` →
  `range(6,13)`.
- `tests/test_placeholder_exercises.py` — removed exercise `5` from `PLACEHOLDER_TITLES`; module
  docstring updated ("Exercises 5-12" → "Exercises 6-12", noting WP28 alongside WP27).
- `tests/test_wp24_content_audit.py` — added `EX5` path constant and a `_norm_ws` helper; renamed
  `Exercise2SingleExploratoryWarning` → `Exercise5SingleExploratoryWarning`, retargeted its three
  tests at `EX5` with the corrected needle text (`"exploratory comparison"`, not `"exploratory model
  comparison"`), and added a fourth test confirming Exercise 2 carries no trace of the warning.
- `tests/test_wp25_content_audit.py` — `ExerciseOneThroughTwelveTitles._title_of` and
  `NoFinalProjectReferences.test_no_final_project_reference_in_any_exercise_1_to_12_page`: ipynb/md
  threshold `n <= 4` → `n <= 5` (both occurrences);
  `test_no_final_project_reference_in_portable_notebooks`: `(1,2,3,4)` → `(1,2,3,4,5)`.

## Not modified (explicitly in scope to leave alone)

`book/syllabus.md`, the Word overview generator, `book/chapters/chapter_01/exercise_01.ipynb`,
`book/chapters/chapter_03/exercise_03.ipynb`, `book/chapters/chapter_04/exercise_04.ipynb`,
`book/_toc.yml` (stem-based resolution needed no edit), and every `chapter_06`–`chapter_12`
placeholder page.
