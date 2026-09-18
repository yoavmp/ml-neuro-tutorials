# WP28: Exercise 5 — Regularization and Feature Selection

## 0. Status

Starting branch: `fix/wp27r-validation-refinements` at `cc711b9` (WP27R report/changelog).
Working branch: `feature/wp28-exercise5-regularization-feature-selection`, created from `cc711b9`.
Only permitted untracked files at start: `WPs/reports/WP16_ARCHITECT_REPORT.md`, `WPs/reports/WP21_DEPLOYMENT_REPORT.md` — left untouched.

## 1. Purpose

Replace the Exercise 5 placeholder (`book/chapters/chapter_05/exercise_05.md`) with a real notebook,
`book/chapters/chapter_05/exercise_05.ipynb`, titled "Exercise 5: Regularization and Feature Selection."

The notebook teaches:

1. predefined and manual feature selection;
2. correlation-based feature selection without leakage;
3. Ridge and Lasso regression;
4. regularization-strength tuning using the nested-CV procedure from Exercise 4;
5. a concise introduction to other feature-selection approaches, especially stepwise selection.

The existing "Comparing feature sets" lesson and its `regression-compare` interactive activity move from
Exercise 2's Bonus section into Exercise 5 Section 2. No feature-selection-stability section is added
anywhere.

## 2. Starting-state audit (recorded)

```
$ git status --short --branch
## fix/wp27r-validation-refinements
?? WPs/reports/WP16_ARCHITECT_REPORT.md
?? WPs/reports/WP21_DEPLOYMENT_REPORT.md

$ git rev-parse HEAD
cc711b9dddcf243575904fb1fd6507d019ca5284

$ git log --oneline --decorate -10
cc711b9 (HEAD -> fix/wp27r-validation-refinements) WP27R: add report and exact changelog
83f3f3a WP27R: densify k grids, reveal third test-MSE panel, replace nested-CV diagram
31d5b17 WP27R: add Exercise 4 interaction and nested-CV refinements specification
8d48bca (feature/wp27-validation-cross-validation) WP27: fix unresolved placeholder in final-git-state section of report
a699e8a WP27: built-book Playwright coverage for Exercise 4 (gate 8/10)
4cfbb45 WP27: Playwright tests for the three Exercise 4 widgets
efdbefe WP27: add ~30 focused Python tests for Exercise 4 (spec section 25)
2131f94 WP27: update pre-existing structural tests for Exercise 4 notebook
054a0a1 WP27: launch-button and portable-notebook script wiring
a16c06c WP27: Exercise 4 notebook and portable notebook
```

State matches expectations exactly. Branch created with `git switch -c
feature/wp28-exercise5-regularization-feature-selection`.

## 3. Stale Exercise 4 launch-button test

`interactive/e2e-book/launch-buttons.spec.ts` contains:

```ts
test("a placeholder exercise page (Exercise 4) gets no Colab button", async ({ page }) => {
  await page.goto("/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html");
  await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
});
```

This contradicts `interactive/e2e-book/chapter04.spec.ts`, which already asserts a Colab button IS present
for Exercise 4. Correct it to assert:

* Exercise 4 has a Colab launch button and a downloadable-notebook link, both pointing at
  `exercise_04_portable.ipynb`;
* Exercise 5 (post-WP28) has the same, pointing at `exercise_05_portable.ipynb`;
* Exercises 6–12 remain placeholders with no Colab button.

Run `npx playwright test launch-buttons.spec.ts` (focused) before proceeding to implementation.

## 4. Source material read before implementation

* `NOTEBOOK_AUTHORING_STANDARDS.md` — opening order, run/download admonition, think-first admonition,
  `hide-input`/`hide-cell` rules, portable-notebook regeneration rule.
* `book/chapters/chapter_02/exercise_02.ipynb` (44 cells) — cells 34–37 (Bonus heading, "Comparing feature
  sets" prose, `regression_compare.json` iframe, think-first box) and Question 13 in cell 43 are the exact
  material moving to Exercise 5. Cells 38–41 (sample-size Bonus subsection) stay.
* `book/chapters/chapter_04/exercise_04.ipynb` (32 cells) — Section 6 nested-CV pattern (cell 25 inner
  `GridSearchCV`/outer `KFold` pipeline, cell 28 `nested_cv_explorer.json` iframe) reused conceptually by
  Exercise 5 Section 6, without re-teaching it.
* `book/chapters/chapter_05/exercise_05.md` — 3-line placeholder, removed after the `.ipynb` replaces it
  (Git history preserves it via the commit graph).
* `regression-compare` widget stack: `interactive/src/components/regression-compare.ts`,
  `interactive/src/regression-compare.ts`, `interactive/src/regression-compare-data.ts`,
  `interactive/src/config.ts` (`regressionCompareConfig`), `book/_static/widgets/configs/regression_compare.json`,
  `scripts/export_regression_catalog.py`, `book/_static/widgets/data/abide_regression_models.json`,
  `interactive/tests/regression-compare.test.ts`, `interactive/tests/regression-compare-data.test.ts`,
  `interactive/e2e/regression-compare.spec.ts`, `interactive/e2e-book/chapter02.spec.ts`.
* Exercise 4 nested-CV widget: `interactive/src/components/nested-cv-explorer.ts` (tab-based, per-outer-fold).
* `interactive/src/components/knn-explore.ts` — slider+number-input+`<output>` DOM pattern reused for the
  new alpha control (no log-scale slider precedent exists; this is new UI).
* `book/config/abide_modeling.json` — bundle/measure/target manifest, `leakage_guard`, `holdout_split`
  (`test_size=0.25, random_state=42, stratify="group"`), FIQ's `role: "regularization_preview"`.
* `scripts/regression_model_audit.py` / `scripts/regression_model_audit_result.json` — already-audited
  Ridge/Lasso numbers for `age` and `FIQ` on `all-eligible` (p > n), reused rather than recomputed:
  `ridge_alpha_grid = np.logspace(-1, 6, 29)`, `lasso_alpha_grid = np.logspace(-3, 2, 26)`.
* `book/_static/launch-buttons.js` (`PAGE_TO_PORTABLE`), `scripts/build_portable_notebook.py`
  (`NotebookSpec`, `NOTEBOOKS` registry, `iframe_replacements`), `book/_toc.yml` (no edit needed — Jupyter
  Book resolves `.md` or `.ipynb` at the same stem), `tests/test_exercise_02_notebook.py`.

## 5. Scope constraints

Reuse the existing ABIDE age-prediction problem and 360/1440-column HCP-MMP1.0 neuroimaging table. No
classification, logistic regression, tree-based importance, random forests, boosting, PCA implementation,
stability analysis, frequency heatmaps, a fourth major widget, new datasets, or final-project material. PCA
is mentioned once, prospectively, in Section 7's table only. No edits to the Syllabus page, Word overview
generator, or Exercises 1/3/4. Exercise 2 changes only to remove the moved activity and adjust its Bonus
heading/summary/questions/portable notebook.

## 6. Notebook conversion

* Create `book/chapters/chapter_05/exercise_05.ipynb`.
* Delete `book/chapters/chapter_05/exercise_05.md` (history preserved via `git log --follow`/prior commits).
* `book/_toc.yml`: no change required (stem-based resolution already points at `chapters/chapter_05/exercise_05`).
* Update `book/_static/launch-buttons.js` `PAGE_TO_PORTABLE` to add a `chapter_05` entry and correct its
  header comment ("placeholder Exercises 6-12").
* Update `scripts/build_portable_notebook.py`: add a `CHAPTER_05` `NotebookSpec`, register it in
  `NOTEBOOKS`, update the module docstring/argparse choices, move the `regression_compare` iframe-replacement
  entry out of `CHAPTER_02` into `CHAPTER_05`.
* Update `tests/test_exercise_02_notebook.py` (remove/rewrite feature-set-comparison assertions) and add
  `tests/test_exercise_05_notebook.py`.
* Active URL remains `chapters/chapter_05/exercise_05.html`. Exercises 6–12 remain placeholders.

## 7. Opening structure

```markdown
# Exercise 5: Regularization and Feature Selection
```

followed by the standard run/download admonition, then:

```markdown
## What this notebook covers
```

> Exercise 5 examines how we decide which predictors to include in a model. We will compare predefined and
> data-driven feature selection, use Ridge and Lasso regression, and introduce stepwise selection.

Numbered list (5 items, matching the 8 `## N.` headings only loosely per the authoring standard's "count
matches section count" — reconciled to match the notebook's outline in Section 8 below, one covers-item per
`## N.` heading):

1. compare feature sets chosen from prior knowledge;
2. select features using training-data correlations;
3. examine how Ridge and Lasso change model coefficients;
4. tune regularization inside cross-validation;
5. introduce stepwise feature selection.

No mention of stability, selection frequency, or a dedicated "choosing a method" section in this list.

## 8. Final notebook outline

```
1. Why Select Features?
2. Compare Predefined Feature Sets                 (moved from Exercise 2 Bonus)
3. Select Features Using the Data
4. Ridge and Lasso Regression
5. Explore Regularization                          ("Shrink the Coefficients" — new widget)
6. A Complete Regularized Regression Pipeline
7. Other Feature-Selection Methods
8. How Do We Choose a Feature-Selection Method?     (open question + brief answer only)
```

## 9–20. Section content

Sections 1, 3, 4, 6, 7, 8 follow the detailed prose/code/table specifications given in the WP28 task brief
verbatim (predefined-vs-data-driven framing; leakage-safe `SelectKBest(score_func=f_regression)` inside the
CV pipeline with candidate counts `5, 10, 20, 40, 80, 160, all`; Ridge/Lasso formulas and shrink-vs-select
distinction; the three-row Section 7 table with `SequentialFeatureSelector` demonstrated on the frontal
prefrontal-thickness bundle; Section 8 as a single open-question box with a ≤4-bullet answer). Section 2 is
the moved "Comparing feature sets" material, reframed with the predefined-feature-set framing and the
"useful for prediction... but are all of these features useful" transition into Section 3, retaining its
exploratory-comparison warning. Section 5 is the new "Shrink the Coefficients" widget per Section 22 below.
No stability section, no selection-frequency heatmap, no fourth major widget, no duplicate methods table at
the end.

## 21. Portable notebook

Create `book/downloads/chapter_05/exercise_05_portable.ipynb` (banner/setup/install cells matching
`exercise_04_portable.ipynb`'s shape, `lesson_packages` including `scikit-learn` for
`SelectKBest`/`Ridge`/`Lasso`/`SequentialFeatureSelector`), no local absolute paths, all widgets replaced by
runnable Python, outputs matching canonical calculations. Regenerate
`book/downloads/chapter_02/exercise_02_portable.ipynb` after removing the transferred activity.

## 22. Interactive implementation — "Shrink the Coefficients"

New component `interactive/src/components/regularization-explore.ts` (name generic per Section 10 tolerance),
config type `regularizationExploreConfig` in `interactive/src/config.ts`, config JSON
`book/_static/widgets/configs/regularization_explore.json`, data exporter
`scripts/export_regularization_widget.py` reshaping `scripts/regression_model_audit_result.json` (no new
modeling), data artifact `book/_static/widgets/data/regularization_explore.json`, registered in
`interactive/src/components/registry.ts`. Controls: model (Linear/Ridge/Lasso), log-scale alpha (new slider
pattern — linear range input mapped through `Math.pow(10, x)`, paired with a numeric readout, following
`knn-explore.ts`'s wiring). Displays: observed-vs-predicted (validation only, diagonal + legend),
coefficients (top-N standardized, labeled as a display choice), performance (train/validation MSE, selected
α, best validation α, unregularized baseline, nonzero-coefficient count, coefficient norm). No test results
exposed. Precomputed deterministic configurations for GitHub Pages (no client-side model fitting).

## 23–24. Language and website visibility

Student-facing throughout; "useful for prediction" not "important"; define feature selection, regularization,
Ridge, Lasso, alpha, stepwise selection on first use. Hide familiar loading inputs (`hide-input`), collapse
reproduction code for the two interactive activities and the full nested-CV nested nested nested reuse via
`hide-cell` only where it purely reproduces an activity the student already used, keep portable-notebook code
fully visible.

## 25–26. Tests and validation gates

Per the WP28 task brief's 34-point test checklist (Section 25) and 15-point bounded-validation gate list
(Section 26), run each gate once, with at most one diagnosis-and-rerun per failure; stop and report on a
second failure rather than looping. Run the full `launch-buttons.spec.ts` once (its stale assertion is being
repaired). Run the full Python suite and full frontend unit suite once each.

## 27–29. Manual verification, reports, completion

Manually confirm the properties listed in Section 27 of the task brief. Produce `WPs/reports/WP28_REPORT.md`
and `WPs/reports/WP28_EXACT_CHANGELOG.md`. Commit specification, implementation, and reports separately.
Stop with all work local on `feature/wp28-exercise5-regularization-feature-selection` — no merge, push,
deploy, Actions monitoring, Word/Syllabus edits, or WP29.
