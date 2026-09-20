# WP32 Exact Changelog — Exercise 7: Boosting and Gradient Boosting

Branch: `feature/wp32-exercise7-gradient-boosting`, created from local `main` at
`a64e3492d8796dcda67c7f59b414df5977e8b989` (one WP31R3 documentation-only commit ahead of
`origin/main` `4f0dc06bc4c0c26f8259d4f679832b9e3eb813a4`). Checkpoint commit:
`71267fd70fd0283ddb60f9c1961e65a3cca7c996`.

## Created files

| File | Purpose |
|---|---|
| `scripts/gradient_boosting_model_audit.py` | Audits the sklearn-example fit, the 12-candidate CV-tuning pipeline (with locked-test-once evaluation), and the single-tree/RF/GB comparison |
| `scripts/gradient_boosting_model_audit_result.json` | Committed audit output |
| `scripts/export_boosting_step_widget.py` | Generates the synthetic 24-observation stage-by-stage boosting dataset/artifact |
| `scripts/export_boosting_parameter_widget.py` | Generates the real-ABIDE learning-rate/depth/tree-count grid artifact |
| `book/_static/widgets/data/boosting_step_by_step.json` | Committed data artifact for Activity 1 (108,988 bytes) |
| `book/_static/widgets/data/boosting_parameter_explorer.json` | Committed data artifact for Activity 2 (777,630 bytes raw / 108,043 bytes gzip) |
| `book/_static/widgets/configs/boosting_step_by_step.json` | Activity 1 config (title, instructions, default learning rate, reflection prompts) |
| `book/_static/widgets/configs/boosting_parameter_explorer.json` | Activity 2 config (defaults, `playIntervalMs=600`, `testSetNote`, reflection prompts) |
| `interactive/src/boosting-step-by-step-data.ts` | Zod schema + parser + `stagesForLearningRate` helper for Activity 1 data |
| `interactive/src/boosting-parameter-explorer-data.ts` | Zod schema + parser for Activity 2 data |
| `interactive/src/components/boosting-step-by-step.ts` | Activity 1 component: learning-rate select, stage slider/stepper, Previous/Next, scaled-correction toggle, 3 Plotly panels |
| `interactive/src/components/boosting-parameter-explorer.ts` | Activity 2 component: learning-rate/depth selects, tree-count slider, Play/Pause/Reset, 3 Plotly panels (MSE curve, heatmap, prediction scatter) |
| `book/chapters/chapter_07/exercise_07.ipynb` | Canonical Exercise 7 notebook, 32 cells |
| `book/downloads/chapter_07/exercise_07_portable.ipynb` | Generated portable notebook, 34 cells |
| `interactive/tests/boosting-step-by-step-data.test.ts` | 9 Vitest cases (real artifact + fixture rejection paths) |
| `interactive/tests/boosting-parameter-explorer-data.test.ts` | 8 Vitest cases |
| `interactive/e2e/boosting-step-by-step.spec.ts` | 7 standalone Playwright tests |
| `interactive/e2e/boosting-parameter-explorer.spec.ts` | 10 standalone Playwright tests, including full Play/Pause lifecycle |
| `interactive/e2e-book/chapter07.spec.ts` | 7 built-book Playwright tests |
| `tests/test_gradient_boosting_model_audit.py` | 14 `unittest` cases |
| `tests/test_export_boosting_step_widget_data.py` | 10 `unittest` cases |
| `tests/test_export_boosting_parameter_widget_data.py` | 10 `unittest` cases |
| `tests/test_exercise_07_notebook.py` | 32 `unittest` cases across 9 test classes |
| `WPs/reports/WP32_REPORT.md` | This work package's narrative report |
| `WPs/reports/WP32_EXACT_CHANGELOG.md` | This file |

## Deleted files

| File | Reason |
|---|---|
| `book/chapters/chapter_07/exercise_07.md` | Replaced by `exercise_07.ipynb` (`git rm`) |

## Changed files, exact diffs

### `book/config/abide_modeling.json`
- Inserted a new top-level `gradient_boosting` key (after `decision_tree`, before `bundles`):
  `target`, `canonical_recipe` (identical values to `decision_tree.canonical_recipe`),
  `dev_split` (identical values to `decision_tree.dev_split`: `test_size=0.25,
  random_state=7, stratify=group`), `sklearn_example` (`n_estimators=100,
  learning_rate=0.05, max_depth=2, random_state=42`), `step_by_step` (synthetic formula/
  seed/grid), `parameter_explorer` (grids + defaults), `cv_pipeline` (full/reduced grids,
  runtime audit, selection rule, comparison CV note), `audit_script`, `audit_result`,
  `export_data_scripts`, `export_data_artifacts`.

### `book/_config.yml`
- Replaced the stale WP27 comment above `sphinx.extra_extensions` (which incorrectly claimed
  the Exercise 4 nested-CV diagram is a ` ```mermaid ` fence) with a WP32 comment stating the
  diagram is hand-built HTML/CSS and that `sphinxcontrib.mermaid` /
  `myst_fence_as_directive` are kept for future/other Mermaid content. No extension, no
  `myst_fence_as_directive` list, and no rendered content changed.

### `book/_static/launch-buttons.js`
- Added `"chapters/chapter_07/exercise_07.html": "book/downloads/chapter_07/exercise_07_portable.ipynb"`
  to `PAGE_TO_PORTABLE`.
- Updated the header comment's placeholder range from "Exercises 7-12" to "Exercises 8-12".

### `scripts/build_portable_notebook.py`
- Added `PUBLISHED_PAGE_CH7`.
- Added `_CH7_BANNER`, `_CH7_SETUP`, `_CH7_STEP_BY_STEP_IFRAME_REPLACEMENT`,
  `_CH7_PARAMETER_EXPLORER_IFRAME_REPLACEMENT`, and a `CHAPTER_07 = NotebookSpec(...)`
  (mirroring `CHAPTER_06`'s shape; `preserve_output_ids=frozenset()`,
  `colab_title="Exercise 7: Boosting and Gradient Boosting"`).
- Added `CHAPTER_07.key: CHAPTER_07` to `NOTEBOOKS`.
- Updated the module docstring: `--notebook {...,chapter_06,all}` →
  `{...,chapter_06,chapter_07,all}`; "Exercises 7-12 are placeholder pages" →
  "Exercises 8-12 are placeholder pages".

### `interactive/src/config.ts`
- Added `boostingStepByStepConfig` (`type: "boosting-step-by-step"`,
  `defaultLearningRate`, `reflectionPrompts?`) and `boostingParameterExplorerConfig`
  (`type: "boosting-parameter-explorer"`, `defaultLearningRate`, `defaultDepth`,
  `defaultNTrees`, `playIntervalMs`, `testSetNote`, `reflectionPrompts?`), both `.strict()`.
- Added both to `activityConfigSchema`'s discriminated union and exported their inferred
  types.

### `interactive/src/components/registry.ts`
- Imported and registered `boostingStepByStepComponent` and
  `boostingParameterExplorerComponent`.

### `interactive/e2e/plot-visual-policy.spec.ts`
- Added 3 entries to `CHARTS`: `boosting-step-by-step` (observation plot),
  `boosting-parameter-explorer (MSE plot)`, `boosting-parameter-explorer (heatmap)`.

### `interactive/e2e-book/launch-buttons.spec.ts`
- Added a `Chapter 7` entry to the `CHAPTERS` array (same shape as chapters 1-6).
- Replaced the "a placeholder exercise page (Exercise 7) gets no Colab button" test with "a
  placeholder exercise page (Exercise 8) gets no Colab button", updated the comment above it.

### `tests/test_placeholder_exercises.py`
- Removed key `7` from `PLACEHOLDER_TITLES`.
- Updated the module docstring's range from "7-12" to "8-12" and its WP-history sentence to
  mention WP32/Exercise 7.

### `tests/test_exercise_06_notebook.py`
- Renamed `test_exercises_7_through_12_still_have_no_portable_notebook` to
  `test_exercises_8_through_12_still_have_no_portable_notebook`, changed `range(7, 13)` to
  `range(8, 13)`, added a one-line comment.

### `tests/test_exercise_04_notebook.py`
- Renamed `test_exercises_7_through_12_remain_placeholders_without_launch_buttons` to
  `test_exercises_8_through_12_remain_placeholders_without_launch_buttons`, changed
  `range(7, 13)` to `range(8, 13)`, updated the preceding comment block.

### `tests/test_book_structure.py`
- `test_exercises_one_through_twelve_follow_in_order`: the `.ipynb`-existence tuple changed
  from `(1, 2, 3, 4, 5, 6)` to `(1, 2, 3, 4, 5, 6, 7)`; the `.md`-existence loop changed from
  `range(7, 13)` to `range(8, 13)`.

### `tests/test_wp25_content_audit.py`
- `EXERCISE_TITLES[7]`: `"Exercise 7: Trees and Boosting"` →
  `"Exercise 7: Boosting and Gradient Boosting"`.
- `ExerciseOneThroughTwelveTitles._title_of`: `if n <= 6:` → `if n <= 7:` (reads the `.ipynb`
  title for Exercise 7 instead of a nonexistent `.md`).
- `NoFinalProjectReferences.test_no_final_project_reference_in_any_exercise_1_to_12_page`:
  `if n <= 6:` → `if n <= 7:`.
- `NoFinalProjectReferences.test_no_final_project_reference_in_portable_notebooks`: the tuple
  `(1, 2, 3, 4, 5, 6)` → `(1, 2, 3, 4, 5, 6, 7)`.

## Notebook content summary (`exercise_07.ipynb`)

Title `# Exercise 7: Boosting and Gradient Boosting`; green run/download admonition linking to
the Chapter 7 portable notebook; "What this notebook covers" (5-item list, no promise that
gradient boosting beats Random Forest); sections 1-8 exactly matching the spec's suggested
outline (`## 1. From Bagging to Boosting` through `## 8. What Should We Remember?`); exactly 2
`<iframe>` embeds (`boosting_step_by_step.json`, `boosting_parameter_explorer.json`); one blue
Think First block (end of section 1); one `hide-cell` optional Python reproduction of the
synthetic dataset's first stage; one concise `GradientBoostingRegressor` illustration cell
(section 3, matching the spec's exact code); one `hide-input` static early-stopping curve cell
(section 5, live-refits one model with `staged_predict`, no `_static/` reference); one
`hide-input` 12-candidate CV-tuning cell plus a visible results-table/selected-settings/
test-metrics cell (section 6); one `hide-input` comparison-fitting cell plus a visible
comparison-table cell (section 7); one Markdown-only XGBoost `{dropdown}` (no `xgboost`
import/dependency anywhere, verified in code and tested); summary (6 bullets) and 6 takeaway
questions (section 8). No AdaBoost, no classification-boosting material anywhere.
