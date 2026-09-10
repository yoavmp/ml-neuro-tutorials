# WP12 — Exercise 2 consistency corrections and regression model audit

## Objective

Correct the presentation and navigation inconsistencies in Exercise 2, then
empirically determine the most pedagogically useful and scientifically honest
regression examples. Test age and FIQ prediction with ordinary linear
regression, ridge, and lasso before restructuring the remainder of the
notebook around the results.

This WP modifies the existing Exercise 2 work. It does **not** add the KNN or
bias–variance sections yet.

## 0. Mandatory Git checkpoint before any edits

1. Inspect the current branch, status, log, and existing WP11 report.
2. Preserve every current change. If the working tree is not clean, commit the
   current state as a checkpoint before editing; do not discard, reset, or
   overwrite user work.
3. Create an annotated or lightweight tag named `wp12-start` at the exact
   pre-WP12 state. If that tag already exists, stop and report the conflict.
4. Record the branch name, checkpoint commit SHA, and tag target in the report.
5. Work on the existing Exercise 2 feature branch unless the repository's
   established WP workflow requires a new child branch.
6. Do not push, merge to `main`, or deploy in this WP.

## 1. Inspect before editing

Read the current implementations rather than assuming paths or architecture:

- canonical Exercise 1 and Exercise 2 notebooks;
- both portable notebooks and their generator;
- Jupyter Book configuration, TOC, theme overrides, CSS, and templates;
- current notebook download control and any launch-button configuration;
- interactive TypeScript app, configs, generated regression catalog, exporter,
  and tests;
- WP11 report and exact changelog.

Exercise 1 is the visual/content reference for the green **Run or download this
notebook** block. Preserve its behavior and styling unless a shared fix is
needed to make both chapters consistent.

## 2. Correct titles and opening language

Use Arabic numbering consistently:

- page title: `Exercise 2: Regression`;
- TOC/sidebar/Contents references: `Exercise 2`, not `Exercise II`;
- portable notebook title and metadata: `Exercise 2`;
- tests and accessible labels where the title is asserted.

Do not rename URLs or directory names merely for this wording change unless
the current routing actually requires it.

Remove or replace this inaccurate sentence:

> This is the linear-regression half of Exercise II. It follows the lecture,
> so it is short on theory and long on practice.

The opening must instead make clear, concisely, that:

- this is Exercise 2 of *Machine Learning for Neuroscience*;
- Exercise 2 concerns regression and the bias–variance tradeoff;
- this current portion starts with linear regression on real neuroimaging data;
- KNN and the explicit bias–variance section will be added later.

Do not compare this notebook with Asaf's website or claim that its exact format
is dictated by his page.

## 3. Make Run/download presentation and actions consistent

### 3.1 Opening block

Make Exercise 2's **Run or download this notebook** block match Exercise 1's
green design exactly: same MyST/admonition class, color, spacing, heading style,
and link wording pattern. Keep chapter-specific destinations.

As in Exercise 1, the block must contain direct links for both:

- opening the chapter-specific **portable** notebook in Google Colab;
- downloading the chapter-specific portable `.ipynb` file.

Both links must refer to Exercise 2, not an older notebook or the canonical
Jupyter-Book source notebook. The Colab title must be `Exercise 2: Regression`.

### 3.2 Page controls

Keep the existing download-`.ipynb` page control and add a visible Colab page
control/button. The Colab control must open the Exercise 2 portable notebook,
not the canonical notebook containing static-site iframe/MyST machinery.

If Jupyter Book's standard global `launch_buttons.colab_url` cannot target the
generated portable notebook correctly on a per-page basis, implement a tested
theme/template or page-metadata mapping instead of accepting the wrong target.
Do not create a decorative button whose destination is unverified.

Exercise 1 and Exercise 2 must have consistent controls, with each control
opening that chapter's own portable notebook. Verify both chapter mappings to
prevent regression to the previously observed “older notebook” problem.

The portable notebooks must remain usable outside the repository and include
their commented package-install cell. Do not restore any instruction telling
students to install from the repository's `requirements.txt`.

## 4. Small wording/code corrections

1. In the code or displayed source for the three scoring approaches, place
   `# B: resubstitution` on a new line. Fix the literal/missing newline rather
   than merely changing rendered CSS.
2. Replace the confusing sentence beginning `B compares different rows...`
   with wording equivalent to:

   > B evaluates the model on its training data, whereas A and C are evaluated
   > on the test data. A is the only valid estimate of performance on unseen
   > participants; C is invalid because the test data were used for fitting.

   Adapt surrounding prose so it is accurate, concise, and non-duplicative.

## 5. Modeling audit — perform before choosing the revised story

Create a reproducible audit script or extend the existing modeling audit. Do
not manually experiment in the canonical notebook and then copy only a favored
result. Save the audit code and summarize all tested configurations and results
in the WP report.

### 5.1 Outcomes

Evaluate:

- `age` from the prepared brain table (expected N about 1004);
- `FIQ` from the deterministic phenotypic join (expected N about 908).

Verify exact usable N, target distributions, and absence of missing brain
features. Never allow identifiers, diagnosis, site, age, sex, other phenotypes,
or the target itself into `X`.

### 5.2 Feature sets

At minimum test the following predeclared spaces for each outcome:

1. every eligible cortical brain feature across all available measures;
2. each single measurement family across all eligible ROIs;
3. the current predeclared compact anatomical bundle where scientifically
   relevant.

Report the exact `p`, training N, and `p / n_train` for every final candidate.
Do not silently discard features based on their association with the full
target. Any supervised feature selection must occur within training folds. A
predeclared measurement family or anatomical bundle is acceptable, provided it
was not chosen after inspecting test performance.

### 5.3 Models

Evaluate these model families:

- `LinearRegression`;
- ridge regression over a documented logarithmic alpha grid;
- lasso regression over a documented alpha grid.

Use `Pipeline(StandardScaler(), model)` so scaling is learned only from
training data/folds. Hyperparameter selection must occur using inner CV on the
training partition only. The held-out test set must be evaluated exactly once
per locked final candidate. Do not choose the target, feature set, model family,
or alpha by repeatedly consulting the held-out test score.

Prefer nested or otherwise properly isolated cross-validation for the audit.
Use deterministic seeds/folds. Record held-out or outer-CV R² and MSE; include
the chosen alpha and, for lasso, the number of non-zero coefficients. Treat a
single positive test R² accompanied by negative cross-validated performance as
unstable, not as successful prediction.

It is acceptable to compute ordinary least squares when `p >= n_train` for
diagnostic comparison, but label the solution underdetermined and do not make
it the recommended model. Do not imply that scaling fixes dimensionality.

### 5.4 Decision policy

Base the revised notebook on the complete audit:

- If age has reliably positive out-of-sample R², use age as the main ordinary
  linear-regression example.
- If ridge or lasso gives reliably positive out-of-sample FIQ R², retain FIQ as
  a compact secondary example showing how regularization can stabilize a broad
  feature set.
- If regularized FIQ remains at or below zero, report that honestly. Do not
  cherry-pick a split, alpha, ROI bundle, or measurement family to manufacture
  a positive result.
- Even if both targets work, keep the primary flow simple: one main age example
  plus one short age-versus-FIQ/regularization bridge is preferable to two
  parallel full tutorials.

Report the audit table before describing which narrative was selected and why.

## 6. Revise the notebook around the audit result

The likely preferred structure, if supported by the audit, is:

1. load and briefly inspect the wide ABIDE-II modeling table;
2. use age for one honest ordinary-linear-regression train/test workflow;
3. use the same age model for the train/test/resubstitution/leakage comparison;
4. use age in the interactive measurement-family/ROI comparison;
5. introduce a concise **regularization preview** comparing age and FIQ with
   the full brain feature space;
6. use a same-target learning curve to demonstrate the effect of sample size.

If the audit contradicts this plan, choose the closest scientifically honest
structure and explicitly justify the deviation in the report.

### 6.1 Dimensionality and regularization preview

Explain in plain language that when the number of features `p` is comparable
to, or larger than, the number of training participants `n`, unregularized
linear regression can be unstable or underdetermined. Broad brain-wide feature
sets may therefore require a predeclared reduction of the feature space and/or
regularization. State that feature selection and regularization will be treated
properly in later lessons.

Do not say that ridge/lasso “marginally reduce X”:

- ridge shrinks coefficients but normally retains all features;
- lasso can shrink some coefficients exactly to zero;
- anatomical or measurement-family selection reduces the actual input feature
  count.

This section is a preview/teaser, not a full regularization lecture. It must
show honest out-of-sample metrics for both age and FIQ where space permits and
make clear that target scales make their raw MSE values incomparable.

### 6.2 Literature framing

If the main target changes to age, replace the intelligence-specific P-FIT
framing wherever it no longer applies. Use one or two verified primary-source
links supporting age-related cortical morphometry and explain that literature
motivates hypotheses, not guaranteed prediction. Retain IQ literature only
beside an actual FIQ analysis.

### 6.3 Interactive activity

Regenerate the interactive regression catalog and defaults for the selected
main target. Controls, plots, R², MSE, N, and feature counts must update from
real precomputed out-of-fold predictions. The activity must remain fully
functional on static GitHub Pages with no kernel, backend, CDN, or live data
download.

Do not disable all-features regularized configurations merely because `p >= n`;
that restriction belongs to unregularized OLS. Clearly distinguish model
families if regularized configurations are exposed. Keep the activity focused;
do not make students navigate an overwhelming grid of choices.

### 6.4 Sample-size section

Update the sample-size discussion and figures to the chosen main target. Prefer
the current rigorous same-target learning curve over a weak comparison between
different outcomes. Remove or shorten the FIQ-versus-SRS availability section
if it no longer adds a clear lesson. Never imply that outcome differences
isolate sample-size effects.

### 6.5 Global consistency

After changing the main example, update every dependent item:

- prose, questions, answers, headings, annotations, and summary;
- code, outputs, tables, figures, captions, and axis labels;
- interactive configs and generated artifacts;
- literature links and ROI explanations;
- portable notebook transformations;
- unit, notebook, artifact, and end-to-end browser tests.

No stale FIQ, ROI-count, sample-size, R², MSE, or “Exercise II” statements may
remain outside sections that intentionally still analyze FIQ.

## 7. Scope and preservation

- Do not add KNN teaching content yet.
- Do not add the full bias–variance section yet; only retain accurate
  forward-looking language and concepts needed to interpret generalization.
- Do not push, merge, deploy, or change GitHub Pages configuration.
- Do not alter Exercise 1 content except for a necessary shared Colab-button
  implementation or consistency fix; document every such change exactly.
- Preserve the offline, static, configuration-driven interactive architecture.
- Preserve deterministic generation and avoid committing transient build
  directories or platform files.

## 8. Required validation

Run and report, at minimum:

1. notebook-format validation and unique cell IDs;
2. modeling data/provenance and leakage-guard tests;
3. audit reproducibility tests, including training-only hyperparameter tuning;
4. regression-catalog schema, metric-recomputation, and deterministic-output
   tests;
5. Python test suite;
6. TypeScript typecheck, unit tests, and production build;
7. standalone Playwright tests for every Exercise 2 activity;
8. portable-notebook freshness checks and out-of-repository smoke execution for
   Exercises 1 and 2;
9. a clean Jupyter Book build;
10. built-book Playwright tests under the GitHub Pages subpath;
11. visual checks at desktop and 390-pixel widths;
12. link-target tests confirming that both the opening links and page buttons
    for Exercises 1 and 2 open the correct chapter-specific portable notebooks.

Manually verify that changing interactive controls changes both the figure and
metrics. Verify that browser refresh restores documented defaults.

## 9. Deliverables and stop condition

Commit the completed WP locally. Then create both:

- `WP12_REPORT.md`
- `WP12_EXACT_CHANGELOG.md`

The report must begin with **SUCCESS**, **PARTIAL**, or **FAILED**, followed by
a short executive summary. Include:

- starting checkpoint/tag and final commit SHA;
- exact files changed;
- complete audit table for age and FIQ, including model, feature set, N, p,
  tuning method/selected alpha, R², and MSE;
- which notebook narrative was selected and why;
- every wording/design/navigation correction made;
- confirmation of the Exercise 1 and Exercise 2 Colab/download destinations;
- test commands and exact results;
- warnings, deviations, unresolved risks, and items requiring Yoav's decision;
- confirmation that nothing was pushed, merged, or deployed.

The exact changelog must identify notebook cells by stable cell ID and list
changes to generated assets/configs/tests separately from source changes.

Stop after producing and committing the two reports. Do not begin KNN or the
bias–variance material. Do not create WP13.
