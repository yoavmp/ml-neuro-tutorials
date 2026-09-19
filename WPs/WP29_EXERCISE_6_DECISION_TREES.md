# WP29: Exercise 6 — Decision Trees

## 0. Status

Starting branch: `feature/wp28-exercise5-regularization-feature-selection` at `61a6276` (WP28
report/changelog). Working branch: `feature/wp29-exercise6-decision-trees`, created from `61a6276`.
Only permitted untracked files at start: `WPs/reports/WP16_ARCHITECT_REPORT.md`,
`WPs/reports/WP21_DEPLOYMENT_REPORT.md` — left untouched.

## 1. Purpose

Replace the Exercise 6 placeholder (`book/chapters/chapter_06/exercise_06.md`) with a real
notebook, `book/chapters/chapter_06/exercise_06.ipynb`, titled "Exercise 6: Decision Trees."

The notebook teaches:

1. how a regression tree partitions feature space;
2. how the greedy splitting algorithm selects a feature and threshold;
3. how tree complexity affects training and validation error;
4. why a single tree can be sensitive to changes in training data;
5. how bagging and Random Forests reduce this sensitivity.

Boosting is out of scope — a single sentence notes it is next in Exercise 7. Two major interactive
activities only: **Build a Tree Greedily** and **One Tree or Many?**. Tree-complexity material uses
a concise code-generated static figure, not a third widget.

## 2. Starting-state audit (recorded)

```
$ git status --short --branch
## feature/wp28-exercise5-regularization-feature-selection
?? WPs/reports/WP16_ARCHITECT_REPORT.md
?? WPs/reports/WP21_DEPLOYMENT_REPORT.md

$ git rev-parse HEAD
61a62764f55d762e53e43802b23876676594e936

$ git log --oneline --decorate -12
61a6276 (HEAD -> feature/wp28-exercise5-regularization-feature-selection) WP28: add report and exact changelog
2470b62 WP28: update regression-compare source headers to reflect Exercise 5 ownership
52416ae WP28: update repo-wide tests that assumed Exercise 5 was still a placeholder
7e73410 WP28: move the WP16 plot-geometry regression guard to Exercise 5
d578486 WP28: add error-panel and narrow-viewport tests to regularization-explore
4146a0c WP28: built-book Playwright coverage moves with the feature-set comparison
83cca0a WP28: launch-buttons.spec.ts reflects Exercise 5 as implemented
9da89f2 WP28: portable notebooks and launch-button wiring for Exercise 5
3cb95bf WP28: move "Compare Two Feature Sets" out of Exercise 2's Bonus into Exercise 5
322bc27 WP28: convert Exercise 5 placeholder into the regularization/feature-selection notebook
c0f9b99 WP28: add the "Shrink the Coefficients" Ridge/Lasso regularization activity
8c3291f WP28: correct stale Exercise 4 launch-button test
```

State matches expectations exactly. Branch created with
`git switch -c feature/wp29-exercise6-decision-trees`.

## 3. Exercise 5 timing-sensitive visual test

`interactive/e2e-book/chapter05-visual-policy.spec.ts`'s existing `waitForBothPanelsRendered`
helper only waits for each panel's `data-render-count` to go non-zero, i.e. for `Plotly.react()`'s
promise to resolve. Plotly's own `automargin` handling can still adjust a plot's SVG/title geometry
over one or two further animation frames after that promise settles (it measures rendered text,
then relayouts again to fit it) — geometry measured immediately after the render-count check can
race that internal relayout on a loaded CI runner. This, not a missing render-count wait, is WP28's
reported intermittent-failure source.

Fix: added a `waitForStableGeometry(frame, selectors)` helper that polls the named elements'
`getBoundingClientRect()` once per animation frame (Playwright `waitForFunction(..., {polling:
"raf"})`) and only proceeds once every rect is unchanged for 4 consecutive frames, bounded by a
3000ms timeout. Inserted before both geometry-reading assertions (initial render and the
bundle-change redraw). The 12px clearance requirement (`toBeGreaterThanOrEqual(12)`), the
`toBeLessThanOrEqual(geometry.svgBottom + 0.5)` title check, no sleep, no `test.fixme`/`.skip`, and
no global retry change — all untouched.

Validation: `chapter05-visual-policy.spec.ts` in isolation (12/12 pass, 8.3s) and
`--repeat-each=3` at the normal 6-worker setting (36/36 pass, 23.3s), against a clean
`jupyter-book build` + `npm run build`.

## 4. Source material read before implementation

* `NOTEBOOK_AUTHORING_STANDARDS.md` — opening order, run/download admonition, think-first
  admonition, `hide-input`/`hide-cell` rules, portable-notebook regeneration rule.
* `book/chapters/chapter_02/exercise_02.ipynb`, `chapter_04/exercise_04.ipynb`,
  `chapter_05/exercise_05.ipynb` — opening structure, hidden data-loading cell pattern
  (`hide-input`, pinned-SHA `pd.read_csv`), `<iframe title="...">` embedding pattern (title
  attribute is load-bearing — keyed by `build_portable_notebook.py`'s `iframe_replacements` and by
  e2e specs), think-first admonition (`:class: think-first`), `hide-cell` reproduction-cell pattern.
* `book/chapters/chapter_06/exercise_06.md` — 2-line placeholder, removed after the `.ipynb`
  replaces it.
* Widget stack read for reuse: this is a hand-rolled TypeScript + Vite app (no React, no JSX) —
  `interactive/src/config.ts` (Zod `activityConfigSchema` discriminated union + `checkSemantics()`),
  `interactive/src/components/registry.ts` (component-id → module wiring, `main.ts` never branches
  on type), `interactive/src/components/types.ts` (`WidgetComponent<TConfig,TData>` contract),
  `interactive/src/components/regularization-explore.ts` + `regularization-explore-data.ts` (two/
  three-panel Plotly component shape, `data-render-count` bump pattern), `interactive/src/
  components/nested-cv-explorer.ts` (tab/round-based multi-state widget, closest precedent to a
  multi-round greedy-split activity), `interactive/src/components/knn-explore.ts` (slider + numeric
  readout control pattern), `interactive/src/resize-report.ts` + `book/_static/activity-resize.js`
  (iframe height sync), `interactive/src/theme.ts` + `interactive/src/components/plotly-policy.ts`
  (light/dark policy).
* `interactive/e2e-book/launch-buttons.spec.ts` (`CHAPTERS` array + placeholder-page assertion),
  `book/_static/launch-buttons.js`, `scripts/build_portable_notebook.py` (`NotebookSpec`,
  `NOTEBOOKS` registry, `iframe_replacements`, chapter_05 registration as the template).
* `book/config/abide_modeling.json` + `scripts/abide_modeling_data.py` — reused age target
  (`targets.age`, native `age` column from `abide2.tsv`), `protocol.holdout_split`
  (`test_size=0.25, random_state=42, stratify="group"`, 753 train / 251 test), `bundles` (named ROI
  subsets), `regularization.dev_split` (`test_size=0.25, random_state=7, stratify="group"` on the
  training partition → 564 fit / 189 validation, reused verbatim for the complexity curve).
* `tests/test_placeholder_exercises.py` (`PLACEHOLDER_TITLES`, `PLACEHOLDER_SENTENCE`,
  `test_no_active_portable_notebook_for_any_placeholder`), `tests/test_book_structure.py`
  (`test_exercises_one_through_twelve_follow_in_order`), `tests/test_exercise_05_notebook.py`
  (structural-test template).

## 5. Scope constraints

No classification trees, logistic classification, boosting/AdaBoost/gradient boosting/XGBoost,
feature-selection lessons, impurity-based feature-importance analysis, out-of-bag evaluation as a
main topic, extensive hyperparameter tuning, new datasets, or final-project material. One sentence
may mention boosting is next. No edits to the Syllabus page, Word overview files/generator,
Exercises 1–5. Exercises 7–12 touched only for navigation/placeholder assumptions strictly affected
by Exercise 6 becoming a notebook (the placeholder-title inventory and the "next placeholder" guard
in `launch-buttons.spec.ts` moving from Exercise 6 to Exercise 7).

## 6. Notebook conversion

* Create `book/chapters/chapter_06/exercise_06.ipynb`; delete `exercise_06.md` (history preserved
  via the commit graph).
* `book/_toc.yml`: no change needed (stem-based resolution).
* `book/_static/launch-buttons.js` `PAGE_TO_PORTABLE`: add a `chapter_06` entry; correct the header
  comment ("placeholder Exercises 7-12").
* `scripts/build_portable_notebook.py`: add a `CHAPTER_06` `NotebookSpec`, register it in
  `NOTEBOOKS`, update the module docstring/argparse choices.
* `tests/test_placeholder_exercises.py`: remove `6:` from `PLACEHOLDER_TITLES`, update the
  docstring.
* `tests/test_book_structure.py`: extend the notebook-file check to `(1, 2, 3, 4, 5, 6)` and the
  placeholder-file check to `range(7, 13)`.
* `interactive/e2e-book/launch-buttons.spec.ts`: add a Chapter 6 entry to `CHAPTERS`; move the
  "placeholder gets no button" assertion from Exercise 6 to Exercise 7.
* Add `tests/test_exercise_06_notebook.py` (structural tests, template: `test_exercise_05_notebook.py`).
* Active URL remains `chapters/chapter_06/exercise_06.html`. Exercises 7–12 remain placeholders.

## 7. Opening structure

```markdown
# Exercise 6: Decision Trees
```

followed by the standard run/download admonition, then:

```markdown
## What this notebook covers
```

> Exercise 6 introduces regression trees and the greedy algorithm used to build them. We will then
> compare a single tree with bagging and Random Forest models.

Numbered list (4 items, matching the 4 objectives requested — reconciled against the 7 `## N.`
section headings the same way WP28's opening list covered its 8 sections one-for-one is not
required here per the brief's explicit "four concise objectives"):

1. examine how a tree divides feature space;
2. choose a split using MSE;
3. see how tree complexity affects overfitting;
4. compare a single tree, bagging, and Random Forest.

## 8. Final notebook outline

```
1. One Regression Tree
2. Build a Tree Greedily
3. How Large Should the Tree Be?
4. From One Tree to an Ensemble
5. One Tree or Many?
6. A Fair Model Comparison
7. What Should We Remember?
```

Shorter than Exercise 1. No stability/importance/boosting sections.

## 9. Section 1: One Regression Tree — feature choice and tree settings

Two fixed predictors from the existing `sensorimotor_core` bundle (`book/config/abide_modeling.json`
→ `bundles.sensorimotor_core`, the compact 5-ROI bundle already reused by prior exercises): the two
CT columns with the largest-magnitude training-partition correlation with age *within that bundle*
(not searched across the full 360-column recipe) — `fsCT_L_3a_ROI` (r=-0.498) and `fsCT_R_2_ROI`
(r=-0.491), computed on the 753-row outer-training partition only (`protocol.holdout_split`).

Tree: `DecisionTreeRegressor(max_depth=3, min_samples_leaf=20, random_state=42)` — the exact
suggested settings, audited and confirmed to produce a readable 7-leaf tree (no unreadable or
degenerate leaves): predictions range from 9.10 to 32.49 years, held-out MSE ≈ 67.2, R² ≈ 0.280.

## 10–16. Section content

Sections 2–7 follow the detailed content/panel/control specifications in the WP29 task brief
verbatim: greedy-splitting math (leaf mean, MSE, weighted split MSE, "largest reduction now, not
several steps ahead"); the "Build a Tree Greedily" activity (synthetic 2-predictor dataset, 3
rounds, midpoint-threshold candidates, lock/reveal, no pre-reveal leakage); the complexity table
(`max_depth`, `min_samples_leaf`, `ccp_alpha` only) and train/validation MSE-vs-depth static figure
using the `regularization.dev_split` recipe; bagging/Random Forest explanations and the 3-row
comparison table (verbatim wording); the "One Tree or Many?" activity (deterministic training
replicates drawn without replacement at fixed seeds, same fixed predictor table, single
tree/bagging/Random Forest, ensemble-size curve, 3 panels); the fair Python comparison
(`DecisionTreeRegressor`/`BaggingRegressor`/`RandomForestRegressor`, identical CV folds, fixed
settings, reported honestly whichever way the numbers land); the closing summary with the
boosting-is-next sentence and takeaway questions.

## 17. Interactive implementation

New components `interactive/src/components/tree-greedy-split.ts` and
`interactive/src/components/tree-ensemble-compare.ts`, config types in `interactive/src/config.ts`,
config JSON under `book/_static/widgets/configs/`, registered in
`interactive/src/components/registry.ts`. Deterministic data exported by new
`scripts/decision_tree_model_audit.py` (→ `scripts/decision_tree_model_audit_result.json`) and two
export scripts (`scripts/export_tree_greedy_widget.py`, `scripts/export_tree_ensemble_widget.py` →
`book/_static/widgets/data/tree_greedy_split.json` / `tree_ensemble_compare.json`), registered in
`book/config/abide_modeling.json` under a new `decision_tree` key mirroring the `regularization`
block's shape. Reuses the established iframe-embedding, resize, theme, and `data-render-count`
patterns; no client-side model fitting; no runtime internet dependency.

## 18. Portable notebook

Create `book/downloads/chapter_06/exercise_06_portable.ipynb` and register it in
`scripts/build_portable_notebook.py`'s `NOTEBOOKS`, matching chapter_05's banner/setup/install-cell
shape (`lesson_packages` including `scikit-learn` for `DecisionTreeRegressor`/`BaggingRegressor`/
`RandomForestRegressor`), both iframes replaced with runnable Python reproductions, no local
absolute paths, executable top to bottom.

## 19–24. Language, visibility, tests, validation, manual verification

Follow the WP29 task brief's Sections 19–24 verbatim: student-facing terminology defined on first
use (node, leaf, threshold, greedy, bootstrap sample, bagging, Random Forest); "participant"/"lower
MSE is better"/"useful for prediction" conventions; hidden familiar loading inputs, collapsed
reproduction/comparison code on the website, fully visible/runnable code in the portable notebook;
the 30-point Python test checklist plus frontend unit/Playwright coverage (configuration validation,
round progression, feature/threshold switching, proposed-MSE calculation, lock/reveal, reset,
no-pre-reveal-leakage, replicate/ensemble-size controls, model highlighting, plot updates,
light/dark, narrow-screen, error states, no console errors); the 16-gate bounded-validation
sequence (one diagnosis + one rerun per failure, stop and report on a second failure, except the
Exercise-5 timing fix's specified 3-repeat stress allowance already exercised in §3 above); the
manual-verification checklist.

## 25. Completion

Commit specification, implementation, and reports separately. Stop with all work local on
`feature/wp29-exercise6-decision-trees` — no merge, push, deploy, Actions monitoring, Word/Syllabus
edits, or WP30.
