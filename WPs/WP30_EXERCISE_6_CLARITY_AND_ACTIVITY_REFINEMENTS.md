# WP30 — Exercise 6 Clarity and Activity Refinements

## Purpose

Refine Exercise 6 after local review. Improve the regression-tree diagram, replace the overly
simple greedy-splitting activity with a noisy but interpretable dataset, simplify the ensemble
activity, and make the model-comparison output easier to read. Audit one optional autism
classification-tree complexity curve and include it only if a predefined rule supports the
intended teaching point.

This is a correction WP. Do not expand Exercise 6 with unrelated material.

## Starting state and Git safety

1. Begin on `feature/wp29-exercise6-decision-trees`.
2. Record the actual starting SHA and `git status --short --branch` in the report. Do not assume a
   SHA from an earlier message.
3. The only permitted pre-existing untracked files are:
   - `WPs/reports/WP16_ARCHITECT_REPORT.md`
   - `WPs/reports/WP21_DEPLOYMENT_REPORT.md`
4. Stop if any other unexpected change is present. Do not reset, stash, delete, or overwrite it.
5. Create and work on `fix/wp30-exercise6-refinements`.
6. Save this specification as `WPs/WP30_EXERCISE_6_CLARITY_AND_ACTIVITY_REFINEMENTS.md` and commit
   it as the initial checkpoint before changing implementation files.
7. Work locally only. Do not merge, push, deploy, or start WP31.

## Standing project requirements

- Preserve the established notebook design, green run/download block, blue Think First boxes,
  light/dark-mode behavior, portable notebook, and browser-only activities.
- Address all text to students using concise, accessible language suitable for self-learning.
- Keep familiar loading/setup code hidden in the website while leaving it usable in the portable
  notebook.
- Do not change numerical results merely to obtain a preferred teaching narrative.
- Keep the ABIDE outer test partition untouched during examples and activity construction.
- Do not introduce boosting, feature importance, classification-tree theory, or other new lesson
  sections beyond the narrowly conditional complexity figure described below.

## 1. Make the single-tree diagram easier to read

Keep the fitted model, data split, underlying columns, predictions, and metrics unchanged.

### 1.1 Short display names

Use short aliases in the diagram only:

| Actual column | Diagram label |
|---|---|
| `fsCT_L_3a_ROI` | `Left 3a thickness` |
| `fsCT_R_2_ROI` | `Right area 2 thickness` |

The real column names must remain in the code, manifest, audits, and reproducible analysis. Make
clear in nearby text that these are shortened display names.

### 1.2 Node wording

- Add the title **Resulting Regression Tree**.
- Replace sklearn's student-facing `value = ...` wording.
- Internal split nodes should say `Mean age = ...`.
- Leaf nodes should be visibly labelled `Leaf` and say `Predicted age = ...`.
- Add a restrained annotation explaining that leaf predictions are the mean ages of the training
  participants who reached those leaves.
- Keep useful information such as sample count and MSE if it remains readable. Do not crowd the
  boxes merely to retain sklearn's default formatting.
- Round displayed ages consistently, preferably to one decimal place.

Use a robust custom formatter or post-process the returned matplotlib text artists. Do not edit a
rendered image manually. Add a test that no visible tree box contains the bare label `value =`.

## 2. Clarify the two-dimensional partition plot

Keep the current colored predicted-age regions and observed-participant points.

- Overlay medium-gray decision-boundary segments separating adjacent terminal rectangles.
- Draw each segment only inside the parent region in which that split applies; do not turn every
  threshold into a full-height or full-width gridline.
- Ensure the lines remain visible without dominating the points or color scale.
- Preserve readable axis labels and colorbar in the built book.
- Verify the figure visually in the rendered notebook.

## 3. Replace the greedy-splitting dataset

The present four-quadrant dataset is too clean. Replace it end-to-end in the exporter, committed
artifact, widget, notebook reproduction, audit, portable notebook, and tests.

### 3.1 Data-generating process

Create exactly 16 synthetic participants from two continuous, normally distributed measurements
and a noisy continuous age target. Use a fixed formula of this general form:

```python
x1 ~ Normal(mu1, sd1)
x2 ~ Normal(mu2, sd2)
age = intercept + beta1*z(x1) + beta2*z(x2) + modest nonlinear_or_interaction_term + noise
noise ~ Normal(0, noise_sd)
```

Declare and commit the exact means, standard deviations, coefficients, noise standard deviation,
and seed. Use student-facing names such as **Brain measure 1** and **Brain measure 2**. State that
the values are simulated and used to understand the algorithm—not ABIDE observations.

The dataset should satisfy all of these objective teaching requirements:

- age is associated with both features but not determined perfectly by either one;
- the feature-space points visibly overlap rather than forming four neat blocks;
- several candidate feature/threshold choices appear plausible before calculation;
- the best weighted-MSE split is unique at each of the three activity rounds;
- each selected split leaves enough observations on both sides to remain interpretable;
- across the complete three-round tree, both features are used if a deterministic candidate
  satisfying the other requirements permits it;
- the optimal choice is discoverable from the activity but not visually obvious before students
  compare the MSE values.

To avoid an unbounded search, define the formula first and inspect at most seeds `0..49` in order.
Select the **first** seed meeting documented numerical acceptance criteria; do not select the seed
with the most dramatic MSE reduction. If none meets the criteria, stop and report the blocker
rather than continuing to search.

Record in the report:

- the full generating formula and chosen seed;
- Pearson correlations of both features with age;
- all three greedy choices, parent sizes, thresholds, weighted MSEs, and MSE reductions;
- the second-best candidate at each round and the gap from the optimum;
- confirmation that no answer is present in the DOM before Reveal is used.

### 3.2 Activity behavior

Preserve the existing interaction sequence: choose a feature, inspect candidate thresholds and
weighted MSE, lock an answer, reveal the greedy optimum, continue, and reset.

- Update axes and explanations for the new overlapping data.
- Do not reveal or visually highlight the optimal threshold before the student requests it.
- Accepted earlier splits must remain visible during later rounds.
- Preserve keyboard usability, narrow-screen usability, and both themes.
- Keep only **one** post-activity reflection block. Remove the duplicate Think Again/Reflect set
  from the website and portable notebook.

## 4. Tree-complexity section and conditional classification audit

The current 360-feature age-regression complexity curve is valid and should remain the primary
figure. Do not describe it as a two-feature curve.

Audit whether an autism classification tree supplies a useful contrasting example. This is a
bounded, conditional audit—not permission to tune until the desired result appears.

### 4.1 Prespecified classification audit

- Use the same eligible ABIDE diagnosis cohort and target coding established in Exercise 3.
- Use the same 360 cortical-thickness feature recipe.
- Use `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`.
- Fit a `DecisionTreeClassifier` at `max_depth=1..10`.
- Fix all other settings before viewing the curve. Use a defensible fixed
  `min_samples_leaf` and report it. Do not scan several leaf-size values to find a favorable
  picture.
- Compare mean training and validation ROC AUC. Use predicted probabilities for AUC.
- Do not touch or report performance on the locked outer test set.

### 4.2 Inclusion rule

Add the classification curve as a second figure only if:

1. the highest mean validation ROC AUC occurs at `max_depth >= 3`; and
2. it exceeds the depth-2 mean validation ROC AUC by at least `0.01`.

If several depths tie at the displayed precision, treat the shallower one as preferred. Do not
alter the metric, folds, seed, feature recipe, depth range, or tree settings after seeing the
result.

If the rule passes:

- add a concise second figure beside or immediately after the regression curve;
- label the regression and classification panels clearly;
- explain that useful tree depth depends on the target, data, and validation results;
- explicitly avoid claiming that classification is inherently more complex than regression;
- explain that ROC AUC is higher-is-better whereas MSE is lower-is-better.

If the rule fails:

- leave the student-facing complexity section as a single regression figure;
- do not mention the unsuccessful audit in the notebook;
- report the complete classification audit results and the failed inclusion criterion in
  `WP30_REPORT.md`.

In either case, make the audit reproducible and offline-checkable. It may extend the existing
decision-tree audit script/result rather than creating redundant infrastructure.

## 5. Simplify “One Tree or Many?”

Remove the visible training-replicate/seed selector.

- Keep the performance-distribution panel across all five audited training samples.
- Keep the ensemble-size curve aggregated across the audited samples.
- Use one fixed, predeclared training sample for the observed-versus-predicted panel. Prefer the
  first existing replicate unless there is a documented technical reason not to do so.
- Student-facing text should call this a **fixed training sample**, not discuss a seed.
- Do not delete the other replicates from the artifact; they remain necessary for the distribution
  and ensemble-size summaries.
- Remove obsolete config/schema/UI state and update tests rather than merely hiding the selector
  with CSS.

Shorten long MSE y-axis titles to exactly:

```text
MSE (years²)
```

Explain `lower is better` in nearby prose or a compact annotation rather than extending the axis
title. Preserve readable tick and title font sizes.

## 6. Show the fair-comparison table but hide its code

In **A Fair Model Comparison**, change the relevant notebook cell from `hide-cell` to
`hide-input`:

- the code should be collapsed/hidden on the website;
- the resulting comparison table must remain visible;
- the portable notebook must retain visible, runnable code and output according to the existing
  portable-notebook policy.

## 7. Consistency updates

Update every affected layer rather than patching only the visible notebook:

- canonical Exercise 6 notebook;
- executed outputs;
- decision-tree manifest/audit result where appropriate;
- widget exporters and committed data;
- widget configs, schemas, and components;
- portable-notebook generator and generated Exercise 6 portable notebook;
- focused Python, frontend-unit, and Playwright tests;
- dark-mode and narrow-layout checks where selectors or plot labels changed.

Search for and remove stale student-facing statements describing the old four-quadrant synthetic
data, duplicate reflection prompts, the removed seed selector, or the old long MSE axis title.

Do not update the Word course overview unless explicitly requested in a later WP.

## 8. Required focused tests

At minimum, add or update tests proving:

1. diagram aliases are used while real feature names remain in analysis code;
2. internal nodes say `Mean age` and leaves say `Predicted age`;
3. the bare sklearn label `value =` is absent from the displayed diagram;
4. partition boundaries correspond to the fitted tree's hierarchical regions;
5. the synthetic artifact has exactly 16 participants and matches the declared formula/seed;
6. both feature–age associations are non-perfect and meet the documented criteria;
7. every greedy round's optimum and runner-up are recomputed correctly;
8. no optimal answer is exposed before Reveal;
9. only one post-activity reflection set remains;
10. the classification inclusion rule is evaluated exactly as specified;
11. the classification figure is present if and only if the rule passes;
12. the ensemble replicate selector is absent from schema/config/UI;
13. the prediction panel uses the declared fixed replicate;
14. both relevant ensemble y axes read `MSE (years²)`;
15. the fair-comparison cell is `hide-input`, its output exists, and portable code remains visible;
16. Exercise 6 launch/download behavior still works;
17. both activities work under the deployed project subpath, in light/dark mode and at 390px.

## 9. Bounded validation procedure

Run each required gate once. If a gate fails because of this WP, make one focused correction and
rerun that failed gate once. Do not repeatedly rebuild or poll without new evidence. Do not rerun
gates that already passed unless their inputs changed.

Recommended order:

1. all decision-tree audit/export `--check` commands;
2. focused Exercise 6 Python tests;
3. portable-notebook regeneration and deterministic `--check`;
4. Exercise 6 portable-notebook smoke execution;
5. focused frontend unit tests and typecheck;
6. one production frontend build;
7. one clean Jupyter Book build;
8. focused standalone and built-book Exercise 6 Playwright tests;
9. launch-button, dark-mode, and narrow-viewport checks;
10. full Python suite;
11. full frontend unit suite;
12. full standalone Playwright suite;
13. full built-book Playwright suite, including the hardened Exercise 5 geometry test.

If an unrelated pre-existing failure appears, document it with evidence and stop rather than
changing unrelated code. Do not use arbitrary sleeps, lowered visual thresholds, skipped tests,
global retries, or repeated GitHub Actions runs.

## 10. Manual verification

Inspect the built Exercise 6 page and confirm:

- shortened feature names make it immediately obvious that the first tree uses two features;
- internal and terminal-node predictions are understandable without knowing sklearn terminology;
- gray partition boundaries clarify adjacent prediction regions;
- the new greedy dataset is not neatly separated but remains teachable;
- only one post-activity reflection block appears;
- any classification curve obeys the inclusion rule and carries the required caution;
- “One Tree or Many?” has no seed selector and its y-axis titles are concise;
- the fair-comparison table is visible while its code is hidden;
- both themes and a 390px viewport remain usable.

## 11. Reports and stopping point

Create and commit:

- `WPs/reports/WP30_REPORT.md`
- `WPs/reports/WP30_EXACT_CHANGELOG.md`

The report must state:

- starting and final branch/SHA/status;
- every requested change and whether it succeeded;
- the synthetic formula, seed, correlations, greedy decisions, runner-up gaps, and acceptance
  criteria;
- complete classification-depth audit results and whether the conditional figure was included;
- the fixed ensemble replicate used for the prediction panel;
- tests/builds run, runtime, failures, corrections, and reruns;
- deviations and anything requiring the user's attention.

Stop after committing the implementation and reports locally. Do not merge, push, deploy, monitor
GitHub Actions, or begin another WP.
