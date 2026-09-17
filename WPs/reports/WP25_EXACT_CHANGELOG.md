# WP25 Exact Changelog

Every modified, moved, deleted, and created file, with a concise reason. Grouped by
area. Line counts are from `git diff --numstat 20f421f db4eda9` (checkpoint spec commit
→ implementation commit).

## Created

| File | Reason |
|---|---|
| `book/chapters/chapter_04/exercise_04.md` | Placeholder page, "Exercise 4: Cross-Validation for Classification and Regression" |
| `book/chapters/chapter_05/exercise_05.md` | Placeholder page, "Exercise 5: Regularization and Feature Selection" |
| `book/chapters/chapter_06/exercise_06.md` | Placeholder page, "Exercise 6: Decision Trees" |
| `book/chapters/chapter_07/exercise_07.md` | Placeholder page, "Exercise 7: Trees and Boosting" |
| `book/chapters/chapter_08/exercise_08.md` | Placeholder page, "Exercise 8: PCA and Clustering" |
| `book/chapters/chapter_09/exercise_09.md` | Placeholder page, "Exercise 9: Advanced Models and Model Comparison" |
| `book/chapters/chapter_10/exercise_10.md` | Placeholder page, "Exercise 10: Common Machine Learning Mistakes" |
| `book/chapters/chapter_11/exercise_11.md` | Placeholder page, "Exercise 11: Embeddings and Representational Similarity Analysis" |
| `book/chapters/chapter_12/exercise_12.md` | Placeholder page, "Exercise 12: Review and Exam-Style Questions" |
| `tests/test_placeholder_exercises.py` | New regression tests: every placeholder exists, has exactly the required title + sentence, excludes disallowed content, has no active portable notebook, no Exercise 13 |
| `tests/test_wp25_content_audit.py` | New regression tests: archive-branch SHA/no-new-commits, Syllabus byte-for-byte unchanged, all 12 titles match required wording, no final-project references, no duplicate active copies, no active knn-abc assets |
| `WPs/WP25_SYLLABUS_ALIGNED_NOTEBOOK_RESTRUCTURE.md` | This WP's specification (committed alone as the checkpoint commit `20f421f`) |
| `WPs/reports/WP25_REPORT.md` | This report |
| `WPs/reports/WP25_EXACT_CHANGELOG.md` | This changelog |

## Deleted

| File | Reason |
|---|---|
| `book/chapters/chapter_04/exercise_04.ipynb` | Old classification notebook moved to `chapter_03/exercise_03.ipynb`; chapter_04 is now a placeholder. Preserved on `archive/pre-syllabus-notebook-structure`. |
| `book/downloads/chapter_04/exercise_04_portable.ipynb` | No portable notebook for a placeholder exercise |
| `book/_static/widgets/configs/knn_abc.json` | Discarded widget (old Exercise 3 Section 3); archived only |
| `book/_static/widgets/data/abide_knn_abc.bin` | Discarded widget's exported binary data |
| `book/_static/widgets/data/abide_knn_abc_manifest.json` | Discarded widget's exported manifest |
| `interactive/src/components/knn-abc.ts` | Discarded widget's DOM component |
| `interactive/src/knn-abc-data.ts` | Discarded widget's data-loading helper |
| `interactive/tests/knn-abc-data.test.ts` | Unit tests for the removed data helper |
| `interactive/e2e/knn-abc.spec.ts` | Standalone e2e spec for the removed widget |
| `scripts/export_knn_abc_data.py` | Data-export generator for the removed widget |
| `tests/test_export_knn_abc_data.py` | Python tests for the removed export script |
| `tests/test_exercise_04_notebook.py` | Superseded by `tests/test_exercise_03_notebook.py` (content moved) |

## Modified — notebooks and portable notebooks

| File | +/− | Reason |
|---|---|---|
| `book/chapters/chapter_01/exercise_01.ipynb` | 41/41 | Title-only: `# Exercise 1 — Exploratory data analysis (EDA)` → `# Exercise 1: Exploratory Data Analysis`. No other content changed. |
| `book/chapters/chapter_02/exercise_02.ipynb` | 667/112 | Rebuilt: renamed "Exercise 2: Regression and Bias-Variance Trade-Off"; merged old Exercise 3 Sections 4–6 (renumbered 5–7); added new Section 4 "Introducing KNN regression"; demoted old Sections 4–5 to `## Bonus` subsections; merged summary/questions; extended the Section 2 split to unpack `groups_train`/`groups_test`; added `KNeighborsRegressor`/`time` imports |
| `book/chapters/chapter_03/exercise_03.ipynb` | 665/587 | Fully replaced: old KNN content (archived) → old Exercise 4's classification content, renamed "Exercise 3: Classification and Metrics", cross-references renumbered ("Exercises 2-3" → "Exercise 2", "Exercise 3 used…k" → "Exercise 2 used…k", Colab/download URLs, `chapter_04`→`chapter_03`) |
| `book/downloads/chapter_01/exercise_01_portable.ipynb` | 2/2 | Regenerated: title-only change from the canonical notebook |
| `book/downloads/chapter_02/exercise_02_portable.ipynb` | 501/76 | Regenerated from the rebuilt canonical notebook; added `knn_explore` iframe replacement |
| `book/downloads/chapter_03/exercise_03_portable.ipynb` | 520/506 | Regenerated: now the classification portable notebook (was KNN); threshold/imbalance iframe replacements renumbered from `chapter_04` |

## Modified — book config, navigation, widgets

| File | +/− | Reason |
|---|---|---|
| `book/_toc.yml` | 9/1 | Added `chapters/chapter_05/exercise_05` through `chapters/chapter_12/exercise_12` |
| `book/_static/launch-buttons.js` | 2/3 | Removed the `chapter_04` → portable-notebook mapping (placeholder has none); updated comment |
| `book/_static/activity-resize.js` | 2/2 | Comment: removed reference to the discarded "Exercise 3 A-B-C comparison" grid |
| `book/_static/widgets/configs/knn_explore.json` | 2/2 | `description`/`curseOfDimensionalityNote`: "Exercise 3"/"Exercise 2's own" → "Exercise 2"/"the worked example above" (now self-referential) |
| `book/_static/widgets/configs/classification_threshold.json` | 1/1 | `description`: "Exercise 4" → "Exercise 3"; "Exercise 4's own" → "this notebook's own" |
| `book/_static/widgets/configs/classification_imbalance.json` | 1/1 | `description`: "Exercise 4" → "Exercise 3" |
| `book/_static/widgets/data/abide_knn_explore_manifest.json` | 1/1 | Regenerated (`export_knn_explore_data.py --refresh`) solely to pick up the corrected `abide_modeling.json` note text; binary payload SHA-256 unchanged |
| `book/config/abide_modeling.json` | 4/4 | Four `note` fields: "Exercise 3"/"Exercise 4"/"Exercises 2-3"/"Exercise 2/3" cross-references renumbered to "Exercise 2"/"Exercise 3" |

## Modified — portable-notebook generator and audit/export scripts

| File | +/− | Reason |
|---|---|---|
| `scripts/build_portable_notebook.py` | 59/175 | `_CH1_BANNER` title updated; `_CH2_BANNER`/`colab_title` updated, added `_CH2_KNN_EXPLORE_IFRAME_REPLACEMENT` and its `CHAPTER_02.iframe_replacements` entry; replaced `_CH3_BANNER`/`_CH3_SETUP`/iframe-replacement constants (previously KNN) with the classification content moved from the old `_CH4_*` constants, renamed `_CH3_THRESHOLD_IFRAME_REPLACEMENT`/`_CH3_IMBALANCE_IFRAME_REPLACEMENT`; removed `CHAPTER_04` from `NOTEBOOKS` and removed the unused `PUBLISHED_PAGE_CH4` constant; removed the discarded `_CH3_ABC_*` constants; updated the module docstring's `--notebook` choices list |
| `scripts/smoke_portable_notebook.py` | 9/16 | `SMOKE["chapter_02"]` gained the KNN expectations (k=20, R²=0.664, N_fit/N_val); `SMOKE["chapter_03"]` now holds the classification expectations (moved from the old `chapter_04` entry); removed the `chapter_04` entry; updated docstring |
| `scripts/knn_model_audit.py` | 2/2 | Docstring: "Exercise 3" → "Exercise 2" (KNN now lives there) |
| `scripts/classification_model_audit.py` | 4/4 | Docstring/comments: "Exercise 4" → "Exercise 3" |
| `scripts/export_knn_explore_data.py` | 1/1 | Docstring: "Exercise 3" → "Exercise 2" |
| `scripts/export_classification_threshold_data.py` | 2/2 | Docstring: "Exercise 4" → "Exercise 3" |
| `scripts/export_classification_imbalance_data.py` | 2/2 | Docstring: "Exercise 4" → "Exercise 3" |
| `scripts/export_regression_catalog.py` | 4/2 | Comments: "…and Exercise 3)" / "Exercise 3's own outer holdout split" → "…and reused by Exercise 2's own KNN section" (self-reference fix) |
| `scripts/sample_size_audit_result.json` | 1/1 | Regenerated (`sample_size_audit.py --run`) solely to pick up the corrected `abide_modeling.json` note text; all numeric results unchanged |

## Modified — frontend source

| File | +/− | Reason |
|---|---|---|
| `interactive/src/components/knn-explore.ts` | 4/4 | Header comment "Exercise 3's" → "Exercise 2's"; one runtime-visible DOM string reworded from a cross-reference ("Exercise 2's own…") to a self-reference ("…used above") |
| `interactive/src/components/classification-threshold.ts` | 1/1 | Header comment: "Exercise 4's" → "Exercise 3's" |
| `interactive/src/components/classification-imbalance.ts` | 1/1 | Header comment: "Exercise 4's" → "Exercise 3's" |
| `interactive/src/components/registry.ts` | 0/2 | Removed `knnAbcComponent` import and registration |
| `interactive/src/config.ts` | 0/12 | Removed `knnAbcConfig` schema, its union entry, and the `KnnAbcConfig` type export |
| `interactive/src/knn-explore.ts` | 1/1 | Header comment: "Exercise 3" → "Exercise 2" |
| `interactive/src/knn-explore-data.ts` | 1/1 | Header comment: "Exercise 3" → "Exercise 2" |
| `interactive/src/classification-imbalance-data.ts` | 1/1 | Header comment: "Exercise 4" → "Exercise 3" |
| `interactive/src/classification-threshold-data.ts` | 1/1 | Header comment: "Exercise 4" → "Exercise 3" |
| `interactive/src/classification-metrics.ts` | 1/1 | Header comment: "Exercise 4" → "Exercise 3" |
| `interactive/src/resize-report.ts` | 3/3 | Comment: removed reference to the discarded "knn-abc" comparison grid |
| `interactive/src/styles.css` | 1/1 | Comment: "confusion matrices (Exercise 4)" → "(Exercise 3)" |

## Modified — frontend and Python tests

| File | +/− | Reason |
|---|---|---|
| `interactive/tests/config.test.ts` | 0/38 | Removed the `knn-abc` config-validation test block and its fixture |
| `interactive/tests/binary-fixture.ts` | 2/2 | Comment: removed reference to the removed `knn-abc-data` tests |
| `interactive/e2e/plot-visual-policy.spec.ts` | 0/2 | Removed the two `knn-abc` entries from the shared-policy activity tables |
| `interactive/e2e-book/chapter02.spec.ts` | 125/0 | Added the transferred KNN k-exploration test block (moved from the old `chapter03.spec.ts`) |
| `interactive/e2e-book/chapter03.spec.ts` | 68/130 | Fully replaced: old KNN + knn-abc content removed; classification threshold/imbalance content moved in from the old `chapter04.spec.ts`, URL/comments renumbered |
| `interactive/e2e-book/chapter04.spec.ts` | 22/129 | Fully replaced: old classification content removed (moved to chapter03); new minimal placeholder-page spec (title, placeholder sentence, no iframe/Colab button) |
| `interactive/e2e-book/launch-buttons.spec.ts` | 5/5 | Removed the `chapter_04` entry from the `CHAPTERS` table; added a placeholder-page "no Colab button" test |
| `interactive/e2e-book/wp22-cross-chapter-dark-mode.spec.ts` | 12/43 | Folded the KNN dark-mode check into the Exercise 2 test (regression-compare + knn-explore); removed the discarded knn-abc dark-mode check; renamed/renumbered the classification test from "Exercise 4" to "Exercise 3" with the `chapter_03` URL |
| `tests/test_binary_asset.py` | 2/2 | Docstring: removed reference to the deleted `export_knn_abc_data.py` |
| `tests/test_book_structure.py` | 12/9 | `Toc` test class: renamed/rewrote to check all 12 chapters in order (`.ipynb` for 1–3, `.md` for 4–12); added a "no Exercise 13" test |
| `tests/test_exercise_02_notebook.py` | 148/81 | Rewritten for the merged notebook: new title, 7-numbered-section check, Bonus-position/contents checks, transferred-KNN-appears-once checks, old-Section-1–3-absent checks, two-iframe check, `groups_train` dependency-adaptation check, updated executed-output assertions (both R² values) |
| `tests/test_exercise_03_notebook.py` | 234/201 | Rewritten (was the old KNN-notebook test file): now tests the moved classification notebook at its new path/title, with an added no-stale-numbering check |
| `tests/test_notebook_opening_structure.py` | 9/9 | `CANONICAL`/`PORTABLE`/`EXERCISE_NUMBERS` reduced to `chapter_01`–`chapter_03`; loading-cell tests reduced to `chapter_02`–`chapter_03` |
| `tests/test_wp19_content_audit.py` | 16/16 | `NOTEBOOK_PATHS` reduced to the three active chapters (canonical+portable); removed `knn_abc` from `WIDGET_CONFIG_PATHS`/`GENERATED_ARTIFACT_PATHS`; renamed/reindexed the `K_EXAMPLE`/`C_EXAMPLE` index-based tests for the new notebook positions |
| `tests/test_wp24_content_audit.py` | 7/3 | `EX4`/`EX4_PORTABLE` repointed to `chapter_03`; the Section-5 concise-lead-in test now looks for `### What does sample size change?` (demoted heading) instead of `## 5.` |

## Not modified (explicitly out of scope, per the task's own exclusions)

- `book/syllabus.md` — confirmed byte-for-byte unchanged (§10/§13 of the report).
- `scripts/build_course_overview_docx.py` and `course_overview/Machine_Learning_for_
  Neuroscience_Notebook_Overview.docx` — left untouched per the task's explicit
  instruction; flagged as an increasingly stale deviation in the report.
- `interactive/src/main.ts`, all `interactive/e2e/*.spec.ts` widget-level specs other
  than `plot-visual-policy.spec.ts` — chapter-agnostic by design, needed no changes.
