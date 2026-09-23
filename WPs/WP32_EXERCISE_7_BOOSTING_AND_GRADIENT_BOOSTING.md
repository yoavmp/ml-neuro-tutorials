# WP32 — Exercise 7: Boosting and Gradient Boosting

## Purpose

Replace the Exercise 7 placeholder with a concise, student-facing practice notebook on boosting
and gradient boosting. It follows Exercise 6's decision-tree lesson and reuses the ABIDE-II age
regression task so students can focus on how the algorithm changes rather than learning a new
dataset.

The notebook should emphasize practice after the lecture, not reteach the entire lecture. It must
contain exactly two substantial interactive activities:

1. **Build a Boosted Model** — follow residual correction one shallow tree at a time on a small
   simulated dataset;
2. **Explore the Boosting Parameters** — examine learning rate, tree count, and tree depth on the
   real ABIDE development data, including a **Play/Pause** control that adds trees sequentially.

Do not include AdaBoost. Mention XGBoost briefly as a later optimized/regularized implementation,
without adding an `xgboost` package dependency or executable XGBoost model.

## 1. Starting state and Git safety

Expected state after WP31R3:

- `origin/main` at successful production release
  `4f0dc06bc4c0c26f8259d4f679832b9e3eb813a4`;
- Exercises 4–6 are live and verified;
- local `main` is expected to be exactly one WP31R3 documentation-only commit ahead of
  `origin/main`;
- the only permitted pre-existing untracked files are:
  - `WPs/reports/WP16_ARCHITECT_REPORT.md`;
  - `WPs/reports/WP21_DEPLOYMENT_REPORT.md`;
  - this specification before its checkpoint commit.

Procedure:

1. Begin on local `main` and record its actual full SHA and status.
2. Run one `git fetch origin main` and verify the expected remote SHA and documentation-only local
   divergence.
3. Stop on any unexpected modified/untracked file or divergence. Do not pull, reset, rebase,
   stash, delete, overwrite, or resolve it automatically.
4. Create `feature/wp32-exercise7-gradient-boosting` from local `main`.
5. Save this specification as `WPs/WP32_EXERCISE_7_BOOSTING_AND_GRADIENT_BOOSTING.md` and commit it
   as the first checkpoint before implementation changes.
6. Leave the two whitelisted legacy reports untouched and untracked.
7. Work locally only. Do not merge, push, deploy, monitor GitHub Actions, or start WP33.

## 2. Standing course requirements

- Title: **Exercise 7: Boosting and Gradient Boosting**.
- Use ordinary numbering, title capitalization, and established visual styles.
- Place the consistent green Run/Download block below the title.
- Keep **What This Notebook Covers** concise and student-facing.
- Address all prose, questions, titles, code comments, widget labels, and errors to students.
- Use blue Think First blocks consistently.
- Avoid duplicated Think First/Reflect questions between notebook Markdown and widgets.
- Hide familiar data-loading/setup code on the website while preserving visible runnable code in
  the portable notebook.
- The website activities must run directly in the browser with no installation.
- The portable/Colab notebook must remain self-contained and must not tell students to install
  packages from the repository or refer to a repository that may later be private.
- Preserve light/dark mode, responsive layouts, accessible controls, and existing launch buttons.
- Keep the notebook substantially shorter than Exercise 1 and avoid unnecessary theory.
- Exercises 8–12 must remain unchanged placeholders.

## 3. Scope boundaries

Include:

- bagging versus boosting at a conceptual level;
- squared-error gradient boosting for regression;
- shallow trees fitted sequentially to residuals;
- learning rate, number of trees, and tree depth;
- validation-based stopping;
- a compact development-only parameter search and one locked-test evaluation;
- comparison with the existing single-tree and Random Forest baselines;
- a brief explanation of where XGBoost fits.

Exclude:

- AdaBoost in prose, code, tables, activities, or takeaway questions;
- classification boosting;
- derivations involving general loss gradients, Hessians, or second-order optimization;
- executable XGBoost/LightGBM/CatBoost code or new dependencies;
- feature importance, permutation importance, SHAP, or biological interpretation of weights;
- exhaustive or outcome-driven hyperparameter searching;
- a third major interactive activity.

## 4. Dataset, cohort, and leakage rules

Reuse the established ABIDE-II brain-measurement table:

- target: `age`;
- predictors: the same complete 360 cortical-thickness features used in Exercises 2 and 6;
- cohort: the same 1,004 eligible participants;
- outer split: reconstruct and reuse the exact age-regression outer development/test split already
  declared in the project manifest and earlier exercises;
- inner train/validation split for the interactive explorer: reuse Exercise 6's exact development
  split if available (reported previously as 564 fitting and 189 validation participants), rather
  than inventing a new split;
- keep the locked outer test rows completely absent from both interactive activities and every
  parameter choice;
- use stable participant identifiers to assert disjointness;
- do not scale the cortical-thickness features for tree-based models.

Any final locked-test result must be produced exactly once after all gradient-boosting settings
are selected from development data. Audit and report all sample sizes and participant-set
disjointness.

## 5. Notebook outline

Use this structure unless a very small wording adjustment improves flow:

```text
# Exercise 7: Boosting and Gradient Boosting
[green Run/Download block]
## What This Notebook Covers
## 1. From Bagging to Boosting
## 2. Building a Model One Tree at a Time
## 3. Gradient Boosting with Scikit-Learn
## 4. Learning Rate and Number of Trees
## 5. Choosing When to Stop
## 6. A Complete Gradient-Boosting Pipeline
## 7. Comparing Tree-Based Models
## 8. What Should We Remember?
### Questions to Take Away
```

Aim for approximately 35–45 cells, with exactly two interactive iframes.

## 6. Opening and learning goals

The opening should explain concisely that Exercise 6 compared one tree with ensembles built by
averaging many independently trained trees. Exercise 7 asks what happens when trees are instead
built sequentially, with each new tree correcting errors left by the existing model.

**What This Notebook Covers** should say that students will:

1. distinguish boosting from bagging;
2. follow residual correction tree by tree;
3. explore learning rate, number of trees, and tree depth;
4. choose settings using development data and evaluate a locked test set once;
5. compare a single tree, Random Forest, and gradient boosting.

Do not promise that gradient boosting will outperform Random Forest.

## 7. Section 1 — From Bagging to Boosting

Include a compact four-row comparison table:

| Method | How trees are trained | Combined prediction | Main idea |
|---|---|---|---|
| Single tree | One tree | One prediction | Simple model |
| Bagging | Independently on resampled data | Average | Reduce variance |
| Random Forest | Independently with row and feature randomness | Average | Decorrelate trees |
| Gradient boosting | Sequentially to correct current errors | Weighted sum | Improve the model step by step |

Key points, briefly:

- bagging trees can be trained independently;
- boosting trees depend on earlier trees;
- individual boosting trees are usually shallow;
- the sequence can form a complex nonlinear model;
- sequential correction also creates overfitting risk.

Place one blue Think First block before the algorithm explanation. Questions should ask why
averaging does not necessarily correct shared bias and what risk arises from adding corrective
trees indefinitely.

Do not mention AdaBoost.

## 8. Section 2 — Building a Model One Tree at a Time

Introduce squared-error gradient boosting with only the mathematics needed for practice:

Initial prediction:

\[
\hat y_i^{(0)} = \bar y
\]

Residual before step `m`:

\[
r_i^{(m)} = y_i - \hat y_i^{(m-1)}
\]

Update:

\[
\hat y_i^{(m)} = \hat y_i^{(m-1)} + \eta f_m(x_i)
\]

Explain in plain language:

- the first model predicts the training-target mean;
- the next shallow tree predicts the current residuals;
- the learning rate `η` controls how much of that correction is added;
- the next residuals are recalculated after every update.

Do not derive general gradients. It is enough to say that, for squared error, the negative
gradient corresponds to the residual.

### Interactive Activity 1: Build a Boosted Model

Create a new activity type, suggested ID `boosting-step-by-step`.

#### Data

- Simulate approximately 24 observations from one continuous predictor and a noisy nonlinear
  target using a declared formula and fixed seed.
- Use a smooth signal plus noise so the relationship is visible but not perfectly clean.
- Keep the exact generating formula, seed, observation values, model settings, and stage outputs
  in a committed, offline-checkable artifact.
- Fit shallow regression stumps (`max_depth=1`) sequentially to residuals.
- Precompute stages 0 through at least 10 for several learning rates, for example
  `[0.1, 0.3, 0.5, 1.0]`.
- Verify stage 0 equals the target mean and that every stored update follows the declared equation.

#### Controls

- learning-rate selector;
- boosting-stage slider or stepper;
- Previous / Next step buttons;
- optional toggle showing the newest tree's correction separately.

Do not put the main Play control here; reserve it for the ABIDE parameter explorer.

#### Visuals

Use a compact responsive layout with:

1. observed points and current ensemble prediction;
2. residuals before the current update and the shallow tree fitted to those residuals;
3. a small training-MSE-by-stage curve with the current stage highlighted.

At stage 0, the plots must clearly show the mean prediction and initial residuals. At later stages,
students should see the piecewise correction and changed residuals.

#### Student prompts

Use one prompt set only:

- What does the model predict before adding a tree?
- Does the new tree predict age directly or the current residuals?
- What changes when the learning rate decreases?
- Why does a smaller learning rate usually require more trees?
- Can training error continue falling after the model has started overfitting?

The optimum or takeaway must not be duplicated in a second post-activity Markdown block.

Provide a compact optional Python reproduction tagged `hide-cell` on the website and fully visible
in the portable notebook.

## 9. Section 3 — Gradient Boosting with Scikit-Learn

Show one short `GradientBoostingRegressor` example using development data only:

```python
from sklearn.ensemble import GradientBoostingRegressor

gb_model = GradientBoostingRegressor(
    n_estimators=100,
    learning_rate=0.05,
    max_depth=2,
    random_state=42,
)

gb_model.fit(X_train, y_train)
predictions = gb_model.predict(X_validation)
```

Use the actual project variables and surrounding code necessary for execution, but keep the
student-visible example this concise.

Include a four-row parameter table:

| Parameter | Meaning | Effect of increasing it |
|---|---|---|
| `n_estimators` | Number of sequential trees | More corrections and greater overfitting risk |
| `learning_rate` | Contribution of each new tree | Faster, less cautious updates |
| `max_depth` | Complexity of each tree | More complex corrections |
| `subsample` | Fraction of training rows per tree | Adds randomness below 1 |

Keep the main lesson on the first three. State that tree-based models do not require feature
scaling.

## 10. Section 4 — Learning Rate and Number of Trees

This is the main real-data activity.

### Interactive Activity 2: Explore the Boosting Parameters

Create a new activity type, suggested ID `boosting-parameter-explorer`.

#### Audit data

Use only the fixed 564-participant fitting subset and 189-participant validation subset from the
outer development partition. The locked outer test must not appear in the widget artifact.

Precompute a defensible grid such as:

- learning rates: `[0.01, 0.03, 0.05, 0.1, 0.2, 0.5]`;
- tree depths: `[1, 2, 3]`;
- a discrete tree-count path dense enough for learning but small enough for a compact artifact,
  for example `[1, 5, 10, 20, 30, 50, 75, 100, 150, 200, 300]`.

For each combination, retain:

- training MSE;
- validation MSE;
- validation R²;
- validation predictions only at the displayed tree-count steps;
- sufficient metadata to verify all metrics and cohort sizes offline.

Do not choose the grid after seeing which values create the neatest story. Record settings before
exporting results. Use staged predictions from the same fitted model where mathematically
equivalent, rather than redundantly refitting every tree count.

#### Controls

- learning-rate selector;
- tree-depth selector;
- tree-count slider/stepper over the committed discrete grid;
- **Play/Pause** button;
- Reset button.

#### Play behavior

- Play advances through the tree-count grid at the currently selected learning rate and depth.
- The vertical marker, heatmap selection, metrics, and prediction plot update at every step.
- Pause preserves the current point.
- Reaching the final tree count stops automatically and restores the Play label/state.
- Changing any control pauses playback before applying the new value.
- Reset restores the declared defaults and stops playback.
- Remove timers/listeners when the activity disconnects; do not leave background animation loops.
- Respect `prefers-reduced-motion`: the controls must remain usable and the animation must not
  force rapid motion for those users.

#### Visuals

1. training and validation MSE versus number of trees, with the current tree count marked;
2. validation-MSE heatmap for learning rate × tree count at the selected depth, with the current
   cell highlighted;
3. observed versus predicted validation age for the selected configuration, including a labelled
   perfect-prediction diagonal.

Use short axis labels. Keep all Plotly drag layers transparent and preserve the project's existing
light/dark palettes.

#### Student framing

State explicitly that:

- the activity uses development data only;
- the locked test remains unavailable while settings are explored;
- lower training MSE does not automatically mean better validation performance.

Use one prompt set only:

- Which learning rate reduces training error fastest?
- Does the fastest reduction give the best validation MSE?
- Why does a smaller learning rate need more trees?
- Where does validation performance stop improving?
- Can different learning-rate/tree-count pairs perform similarly?
- Why should the test set remain hidden here?

## 11. Section 5 — Choosing When to Stop

Use the preceding activity rather than adding a third widget.

Include one small static annotated curve or a concise reuse of committed activity results showing:

- underfitting region;
- best validation point;
- overfitting region.

Explain:

- training MSE can continue decreasing as trees are added;
- validation MSE can flatten or rise;
- validation performance, not minimum training error, guides tree count;
- this is the basic idea behind early stopping.

Ask one question: if 300 trees have lower training MSE but higher validation MSE than 120 trees,
which model should be selected and why?

Do not introduce a new interactive control or implementation of automatic early stopping.

## 12. Section 6 — A Complete Gradient-Boosting Pipeline

Apply the validation material from Exercise 4 without reteaching it.

Pipeline:

1. preserve the locked outer test;
2. run cross-validation only within the outer development partition;
3. compare a small parameter grid;
4. select one configuration by mean CV MSE;
5. refit it on all development participants;
6. evaluate the locked test exactly once.

Start from this intended grid:

```python
parameter_grid = {
    "learning_rate": [0.03, 0.05, 0.1],
    "n_estimators": [50, 100, 200],
    "max_depth": [1, 2, 3],
}
```

Before committing to the canonical notebook, audit runtime on the target machine and in a clean
build. If this 27-candidate × 5-fold grid makes notebook execution unreasonably long, reduce it
once to a predefined balanced subset of at least 12 candidates without inspecting which omitted
settings would help the result. Document the runtime rule and final grid. Do not prune candidates
based on their scores.

Use a fixed 5-fold shuffled CV with a declared seed and negative MSE scoring. Select the minimum
mean CV MSE. Do not use the outer test to resolve ties or choose the grid.

Website presentation:

- hide the fitting code input;
- show a compact CV-results table, selected settings, and final locked-test MSE/R²;
- keep the full runnable code visible in the portable notebook.

Audit the exact participant membership, folds, selected parameters, CV metrics, refit, and
single test evaluation in a committed result file.

## 13. Section 7 — Comparing Tree-Based Models

Compare:

- the existing Exercise 6 single regression tree;
- the existing Exercise 6 Random Forest;
- the selected gradient-boosting model.

Use the same participant split, 360 features, target, and metrics. Carry forward existing model
settings/results rather than silently retuning the older models for this comparison. Label this as
a consistent held-out comparison, not proof that one algorithm universally wins.

Show a concise table with locked-test MSE and R² plus one sentence interpreting the observed
result honestly. Do not force gradient boosting to win.

### Where XGBoost Fits

Include one short dropdown/callout explaining:

- XGBoost is an efficient, regularized implementation of gradient-boosted trees;
- it follows the same broad sequential-correction principle;
- it adds computational and regularization features useful for tabular data;
- understanding ordinary gradient boosting should come first.

If helpful, include a minimal `XGBRegressor` example as a **Markdown code block only**. Do not
import or execute `xgboost`, add it to requirements, add a Colab install command, or compare its
performance in this notebook.

Do not mention AdaBoost.

## 14. Section 8 — Summary and takeaway questions

Keep the summary to approximately six bullets:

- boosting builds trees sequentially;
- each shallow tree corrects current residuals;
- learning rate controls the size of each correction;
- learning rate and tree count must be considered together;
- validation data guide stopping and parameter selection;
- the test set is used once after choices are fixed.

Takeaway questions:

1. How does boosting differ from bagging?
2. What does each new tree predict for squared-error gradient boosting?
3. Why does a smaller learning rate usually require more trees?
4. Why can training MSE improve while validation MSE becomes worse?
5. Why must the test remain hidden while choosing the learning rate and number of trees?
6. Is XGBoost a completely different principle or an extension of gradient boosting?

## 15. Data/export/audit architecture

Follow the established committed-artifact architecture. Suggested files:

- `scripts/gradient_boosting_model_audit.py`;
- `scripts/gradient_boosting_model_audit_result.json`;
- `scripts/export_boosting_step_widget.py`;
- `scripts/export_boosting_parameter_widget.py`;
- `book/_static/widgets/data/boosting_step_by_step.json`;
- `book/_static/widgets/data/boosting_parameter_explorer.json`;
- matching config files under `book/_static/widgets/configs/`;
- a `gradient_boosting` manifest block in `book/config/abide_modeling.json`.

Every script must provide deterministic `--check` behavior. Use the existing semantic JSON
comparison utility where cross-platform floating-point recomputation could differ insignificantly;
do not reintroduce byte-exact float comparisons.

Validate:

- declared seed/formula and stage-by-stage update equation;
- stage 0 mean prediction;
- residual/correction consistency;
- training/validation/test disjointness;
- locked-test exclusion from both widget artifacts;
- exact metric recomputation;
- parameter grids and declared defaults;
- CV folds and test-once policy;
- no non-finite values.

Suggested asset budgets:

- step-by-step activity: under 150 KB raw;
- parameter explorer: under 1.5 MB raw and under 300 KB gzip;
- report actual sizes and justify any excess before proceeding.

## 16. Frontend architecture

Add two registered activity types through the existing schema/config/component registry:

- `boosting-step-by-step`;
- `boosting-parameter-explorer`.

Requirements:

- strict schemas;
- informative loading/error states;
- no network computation or Python in the browser;
- precomputed committed data only;
- keyboard-operable controls and labelled inputs;
- light/dark theme synchronization;
- transparent Plotly drag layers;
- correct rendering under the GitHub Pages project subpath;
- responsive stacking with no page-level horizontal overflow at 390px;
- the parameter explorer's Play/Pause lifecycle must be deterministic and cleaned up on disconnect.

Use existing shared plotting/theme helpers. Do not create another parallel widget framework.

## 17. Notebook, portable version, and navigation

- Replace `book/chapters/chapter_07/exercise_07.md` with
  `book/chapters/chapter_07/exercise_07.ipynb` while preserving history.
- Add `book/downloads/chapter_07/exercise_07_portable.ipynb` through the existing generator.
- Register Chapter 7 in the portable-notebook builder and launch-button mapping.
- Preserve iframe-to-published-page replacement behavior in the portable notebook.
- All canonical code cells must execute successfully.
- The website may hide reproduction/fitting code, but the portable notebook must keep it visible and
  runnable.
- Exercises 8–12 remain `.md` placeholders with no launch buttons.
- Update stale repo-wide assumptions that only Exercises 1–6 are notebooks, narrowly and correctly.

## 18. Small approved maintenance correction

Update the stale comment in `book/_config.yml` that claims the Exercise 4 nested-CV diagram is a
Mermaid fence. The current diagram is hand-built HTML/CSS. Change only the comment so it accurately
states why the Mermaid extension remains enabled (future/other Mermaid content). Do not remove the
extension or its newly pinned dependency, and do not alter rendered content.

## 19. Required tests

Add focused Python tests for:

- notebook title, structure, cell tags, concise opening, two iframe count, and absence of AdaBoost;
- data-loading code hidden on the website and visible in portable form;
- exact cohort/split reuse and test exclusion;
- synthetic generating formula and deterministic stages;
- residual-update equation and stage-0 mean;
- parameter grids, metrics, and prediction arrays;
- CV-only tuning and single locked-test evaluation;
- comparison-table consistency;
- XGBoost is contextual Markdown only and no package/import/dependency was added;
- Chapter 7 portable generation and smoke execution;
- Exercises 8–12 remain placeholders;
- updated `_config.yml` comment matches the actual hand-built nested-CV diagram.

Add focused frontend/unit/Playwright tests for:

- strict schema validation;
- both activities loading under site root and project subpath;
- controls changing metrics and plots, not only labels;
- stage 0 and later boosting steps;
- Previous/Next boundary behavior;
- parameter explorer learning-rate/depth/tree-count controls;
- Play advances through the committed tree-count grid;
- Pause stops advancement;
- control changes pause playback;
- Play stops at the final value;
- Reset stops playback and restores defaults;
- no orphan timer after disconnect/reload;
- perfect-prediction line labelled correctly;
- test set absent from widget data/text;
- light/dark colors and transparent drag layers;
- 390px layout without horizontal overflow;
- Chapter 7 launch/download buttons;
- Exercises 8–12 have no launch buttons.

Tests must assert actual Plotly state/data where relevant, not merely changed text.

## 20. Bounded validation procedure

Run each gate once. If a gate fails because of WP32, make one focused correction and rerun only
that failed gate once. Do not rerun already-passing gates unless their inputs changed. Stop on a
repeated or unrelated failure.

Recommended order:

1. audit/export scripts in run/refresh mode once, then `--check`;
2. focused Python tests for audit, exporters, notebook, portable notebook, and book structure;
3. portable-notebook generation and deterministic `--check --notebook all`;
4. independent Chapter 7 portable smoke execution in a fresh temporary directory;
5. frontend typecheck and focused frontend unit tests;
6. one production frontend build;
7. one clean Jupyter Book build and execution-error-log check;
8. focused standalone Playwright tests for both new activities;
9. focused built-book Chapter 7 and launch-button tests;
10. light/dark and 390px checks;
11. full offline Python suite;
12. full frontend unit suite;
13. full standalone Playwright suite;
14. full built-book Playwright suite, including the WP31R3 Chapter 1 dark-mode regression;
15. portable smoke coverage for existing chapters as needed by the repository's standard gate.

Do not use sleeps, weakened assertions, skipped tests, global retries, reduced workers, or
open-ended stress loops. A Play-control test may use fake timers or event/state observation rather
than waiting through a long real-time animation.

## 21. Manual verification

Inspect the built Exercise 7 page in light and dark modes and at 390px. Confirm:

- the notebook is concise and flows naturally from Exercise 6;
- exactly two activities appear;
- the simulated activity clearly shows mean prediction, residual correction, and stage-wise MSE;
- the ABIDE activity never exposes locked-test data;
- Play, Pause, Reset, and manual controls behave consistently;
- plots update visibly at every selected step;
- learning-rate/tree-count trade-offs are interpretable;
- early stopping is explained without a third activity;
- code/output hiding matches the project standard;
- the XGBoost note is brief and non-executable;
- no AdaBoost material appears;
- Chapter 7 Colab/download links resolve;
- Exercises 8–12 remain unchanged placeholders;
- no new console errors appear.

## 22. Reports and stopping point

Create and commit:

- `WPs/reports/WP32_REPORT.md`;
- `WPs/reports/WP32_EXACT_CHANGELOG.md`.

The report must include:

- starting and final branch/SHA/status;
- final notebook outline and cell count;
- exact cohort and split sizes;
- synthetic formula/seed and activity stages;
- ABIDE grids, defaults, asset sizes, and Play behavior;
- final CV grid, runtime, selected settings, CV/test metrics;
- single-tree/Random-Forest/gradient-boosting comparison;
- every file created/changed/deleted;
- every test/build command and result;
- failures, focused corrections, and reruns;
- deviations and anything requiring user attention.

Stop after committing implementation and reports locally on
`feature/wp32-exercise7-gradient-boosting`. Do not merge, push, deploy, monitor GitHub Actions, or
start WP33.
