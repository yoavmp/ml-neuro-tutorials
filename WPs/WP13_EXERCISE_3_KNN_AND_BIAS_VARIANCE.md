# WP13 — Exercise 3: KNN and the Bias–Variance Tradeoff

## Objective

Create a new third notebook, **Exercise 3: KNN and the Bias–Variance
Tradeoff**, using the same ABIDE-II age-prediction setting and visual language
as Exercise 2. The notebook should emphasize practice rather than repeat the
lecture: implement KNN regression correctly, contrast honest evaluation with
resubstitution and leakage, and use KNN's number of neighbours to make the
bias–variance tradeoff concrete.

KNN classification should be mentioned briefly as a later application, but
classification is not taught in this notebook.

## 0. Mandatory Git checkpoint

Before editing:

1. Inspect branch, status, recent log, WP12 report, and WP12 exact changelog.
2. Preserve all current work. If anything is uncommitted, commit a checkpoint;
   never discard or overwrite it.
3. Create tag `wp13-start` at the exact pre-WP13 state. If it exists already,
   stop and report the conflict.
4. Record branch, checkpoint SHA, and tag target in the final report.
5. Continue on the existing Exercise feature branch unless the established
   repository workflow requires a child branch.
6. Do not push, merge, deploy, or change repository visibility.

## 1. Inspect and audit before choosing examples

Read the existing notebook, portable-notebook, interactive-widget, testing,
styling, launch-button, and manifest architecture. Exercise 2 is the source of
truth for:

- ABIDE-II data provenance and loading;
- target (`age`) and canonical cortical-thickness feature recipe;
- fixed outer train/test split;
- metric definitions and visual style;
- green Run/download block and page-level Colab control;
- portable-notebook behavior;
- static, offline interactive components.

Create a deterministic KNN audit script and committed result artifact before
writing conclusions into the notebook. At minimum evaluate standardized KNN
regression for age using:

- the exact Exercise 2 canonical feature set (all eligible CT features);
- a small set of already-predeclared anatomical bundles, if needed to assess
  the effect of dimensionality;
- `k` values spanning 1 through the largest value valid within training-only
  cross-validation, plus the special endpoint in which `k` equals every
  participant in the fitting set.

Use the same locked outer test split as Exercise 2. Select the standard-example
`k` using cross-validation **inside the training partition only**, then evaluate
that locked model once on the outer test set. Do not choose `k`, scaling,
distance metric, feature set, or weighting using outer-test performance.

The audit must report N, p, folds, candidate `k`, selected `k`, train/CV/test
R² and MSE, and runtime. If KNN on 358 CT features is weak because of
high-dimensional distances, retain that honest result and decide whether a
predeclared lower-dimensional bundle produces the clearest teaching example.
Do not perform target-informed feature screening.

Use the audit to choose one primary, defensible configuration. Explain the
choice in the report. Keep Exercise 2 unchanged unless a genuinely shared
infrastructure fix is necessary.

## 2. Notebook and navigation

Create:

- `book/chapters/chapter_03/exercise_03.ipynb`
- `book/downloads/chapter_03/exercise_03_portable.ipynb`

Add the canonical notebook to `_toc.yml` immediately after Exercise 2. The
rendered sidebar and Contents page must read:

> Exercise 3: KNN and the Bias–Variance Tradeoff

Use Arabic numbering consistently. Add correct chapter-specific Colab and raw
portable-notebook links to the green **Run or download this notebook** block.
Extend the page-header Colab mapping so the new button opens Exercise 3's
portable notebook, never the canonical notebook or another chapter.

The opening should state concisely:

- KNN can perform regression by averaging nearby training outcomes;
- KNN can also perform classification by voting among nearby labels, which
  students will see later;
- this notebook practices KNN regression and uses `k` to study model
  flexibility and the bias–variance tradeoff;
- prerequisites are Exercise 2's train/test workflow, R²/MSE, and basic
  scikit-learn pipelines.

Do not add a time budget or repeat the site-wide Introduction page.

## 3. Terminology and mathematical accuracy

Use `k` for the number of neighbours. Do **not** call it `n` or `N`:

- `n` or `N` = number of participants/observations;
- `p` = number of features;
- `k` = number of neighbours used by KNN.

Explain KNN regression compactly:

\[
\hat{y}(x_0)=\frac{1}{k}\sum_{i\in\mathcal{N}_k(x_0)}y_i.
\]

State that the neighbourhood is determined using predictors only and that a
new participant's target value is never used to find neighbours. Explain why
feature scaling belongs inside the pipeline and must be fitted on training
data only. Add one short note on the curse of dimensionality: in many
dimensions, useful notions of “near” can deteriorate.

## 4. Suggested teaching structure

Keep the notebook focused and shorter than Exercise 1. A target of roughly
30–45 canonical cells is appropriate, but clarity matters more than padding.

### 4.1 The modeling table

Load the same prepared ABIDE-II data and show only a compact preview. Reuse the
Exercise 2 target, feature definitions, provenance, and split. State that one
row is one participant, `age` is the target, and cortical measurements are
predictors. Do not repeat a full EDA lesson.

### 4.2 One standard KNN regression workflow

Start with readable scikit-learn code using:

- `Pipeline(StandardScaler(), KNeighborsRegressor(...))`;
- the same locked train/test indices as Exercise 2;
- a `k` selected using training-only CV, as determined by the audit;
- predictions on the untouched test data;
- held-out R² and MSE;
- an observed-versus-predicted plot with the identity line and equal axes.

Use a **Think first** question before revealing the score. Include a compact
comparison with Exercise 2's OLS result only if both models use exactly the
same participants, split, target, and feature set. Do not present a difference
as a universal KNN-versus-linear-regression conclusion.

### 4.3 Honest evaluation versus invalid alternatives

Using the same fixed `k` and feature recipe, compare:

- **A — valid:** fit on training data, predict outer test data;
- **B — resubstitution:** fit on training data, predict those training data;
- **C — invalid leakage:** fit on outer test data, predict those same test
  data.

Make the differences in evaluated rows explicit, using the improved wording
from Exercise 2. B and C are demonstrations, not candidate models. Keep the
invalid fitted object isolated and ensure it is never reused later.

If the audit-selected `k` does not make the optimism visually clear, add a
small, explicitly labeled `k=1` demonstration: resubstitution at `k=1` is
perfect because every observation is its own nearest neighbour. Do not replace
the honest primary model with this didactic special case.

Ask students to predict the metric ordering before showing it. Use one compact
table and, only if useful, aligned observed-versus-predicted panels.

### 4.4 The classic bias–variance tradeoff

Introduce squared-error decomposition concisely:

\[
\mathbb{E}\left[(Y-\hat f(X))^2\right]
=\operatorname{Bias}(\hat f(X))^2
+\operatorname{Var}(\hat f(X))
+\sigma^2.
\]

Create a polished classic graph showing squared bias, variance, irreducible
error, and expected test error versus model flexibility. Clearly indicate:

- small `k` → high flexibility, low bias, high variance;
- large `k` → low flexibility, higher bias, lower variance;
- training error alone generally favors excessive flexibility;
- expected test error is minimized at an intermediate complexity.

The graph must be labeled as conceptual, not estimated from ABIDE.

### 4.5 Empirical KNN curve from `k=1` to all fitting participants

Create a separate, deterministic development demonstration using only the
outer-training partition. Split it into a fitting subset and a validation
subset. Let

> `N_fit` = number of participants used to fit KNN in this demonstration.

Evaluate every integer `k` from 1 through `N_fit`. At `k=N_fit`, every
validation prediction must equal the fitting-set mean age (verify this in a
test). Plot fitting and validation error against `k`, with annotations for:

- `k=1`;
- the validation-optimal `k`;
- `k=N_fit`;
- the high-flexibility and high-smoothing ends.

Use a log-scaled `k` axis if it materially improves readability, while still
making endpoints and selected `k` obvious. Alternatively, reverse/map the
horizontal axis to model flexibility; never make the direction ambiguous.

This empirical ABIDE graph **illustrates behavior consistent with** the
bias–variance tradeoff but does not directly estimate bias and variance,
because the true population function is unknown and only one observational
dataset is available. Say this explicitly. Do not place empirical training/
validation curves on the same numerical axes as arbitrary conceptual
bias/variance curves. A two-panel figure with aligned explanatory labels is
acceptable.

Do not use this development curve to retune the already reported outer-test
model. The outer test remains locked.

### 4.6 Interactive KNN activity

Add a robust static-site activity in which students vary `k`. At minimum it
must show:

- a slider or equivalent control spanning `k=1` through `N_fit`;
- current `k`, fitting R²/MSE, and validation R²/MSE;
- an observed-versus-predicted validation scatterplot;
- the full fitting/validation error curve with the current `k` highlighted;
- explanatory endpoint text at `k=1` and `k=N_fit`.

Changing `k` must update the actual predictions, plots, and metrics—not just a
label. It must work directly in the static HTML/GitHub Pages build without a
Python kernel, backend, CDN, or network request.

Precompute the finite results deterministically. For efficiency, compute and
sort neighbour distances once and derive predictions for all `k` using
cumulative target sums rather than refitting hundreds of identical models.
Validate representative `k` values against scikit-learn's
`KNeighborsRegressor`. Store no participant identifiers or raw brain features
in the browser artifact.

Keep controls manageable on mobile. Keyboard interaction, accessible labels,
responsive layout, and browser-refresh restoration of defaults are required.

Optional, only if it remains concise and produces a visibly meaningful
difference: add a scaling on/off comparison. It must be labeled as a
preprocessing demonstration and must not allow outer-test-driven selection.

### 4.7 Questions and synthesis

Use **Think first** prompts before results and revealable **Check your
reasoning** answers where helpful. Include questions such as:

- What happens to flexibility when `k` increases?
- Why can `k=1` achieve perfect training performance?
- Why is that not evidence of good generalization?
- What does `k=N_fit` predict for every new participant?
- Why must scaling be learned only from training data?
- Why is a validation curve not a direct measurement of bias and variance?
- Would the selected `k` necessarily generalize to a completely new scanning
  site?

End with a short synthesis, not a long recap. Mention classification only as a
forward-looking application.

## 5. Portable notebook

Extend the existing spec-driven generator rather than creating a one-off copy.
The Exercise 3 portable notebook must:

- have title/Colab metadata `Exercise 3: KNN and the Bias–Variance Tradeoff`;
- include a commented package-install cell with only required packages;
- load data from pinned remote sources and have no repository dependency;
- contain executable equivalents of canonical code and current outputs;
- replace the static-site iframe with a short link to the published activity
  plus a non-interactive Python/Matplotlib version of the `k` exploration where
  practical;
- contain no MyST directives, iframe, hide tags, Node requirement, credentials,
  or active install command;
- execute successfully from outside the repository.

Do not modify the generated Exercise 1 or Exercise 2 portable notebooks except
through a necessary backward-compatible generator improvement; verify both are
byte-identical if no change is required.

## 6. Implementation and methodological safeguards

- Use deterministic seeds and record them in code/config.
- Fit `StandardScaler` only on the appropriate fitting/training partition.
- Keep the outer test partition untouched by KNN hyperparameter selection and
  the all-`k` interactive development curve.
- No identifier, site, diagnosis, sex, target, or phenotype leakage into `X`.
- Validate metric values independently from stored predictions.
- Ensure `k <= n_fit` everywhere and handle endpoints without NaN/Infinity.
- The invalid leakage model must never feed later sections or artifacts.
- Avoid claiming causal or new-site generalization from a random participant
  split across the same ABIDE sites.
- Do not call the empirical ABIDE curve a direct proof or measurement of bias
  and variance.

## 7. Testing and visual verification

Run and report at minimum:

1. notebook validation, unique cell IDs, valid hide tags, current outputs, and
   no stale Exercise 2/FIQ wording;
2. data provenance, split identity with Exercise 2, and feature leakage guards;
3. audit reproducibility and training-only `k` selection tests;
4. exact endpoint tests (`k=1`; `k=N_fit` equals fitting-target mean);
5. independent R²/MSE recomputation for all stored interactive predictions;
6. representative fast predictions checked against scikit-learn;
7. Python test suite;
8. TypeScript typecheck/unit tests and production build;
9. standalone and built-book Playwright tests, including real control changes;
10. portable freshness and out-of-repository smoke execution for all three
    notebooks;
11. clean Jupyter Book build and no new warnings/error logs;
12. correct TOC, prev/next order, page title, green opening block, download
    link, and header Colab target;
13. desktop and 390-pixel visual checks with no horizontal page overflow;
14. confirmation that Exercises 1 and 2 and their existing activities remain
    functional.

Manually verify the conceptual graph, empirical curve, and interactive layout.
Confirm that changing `k` updates both graphs and every displayed metric, and
that refresh restores the documented default.

## 8. Deliverables and stop condition

Commit the completed implementation locally. Then create and commit:

- `WPs/reports/WP13_REPORT.md`
- `WPs/reports/WP13_EXACT_CHANGELOG.md`

The report must begin with **SUCCESS**, **PARTIAL**, or **FAILED** and include:

- checkpoint/tag and final commit SHAs;
- exact files changed;
- complete KNN audit table and the rationale for the selected configuration;
- canonical, development, and outer-test sample sizes;
- selected `k`, selection procedure, and final metrics;
- actual A/B/C evaluation metrics;
- behavior at `k=1`, the validation optimum, and `k=N_fit`;
- interactive artifact structure and privacy checks;
- every test command and exact result;
- all warnings, deviations, unresolved risks, and decisions needed from Yoav;
- explicit confirmation that nothing was pushed, merged, or deployed.

The exact changelog must identify notebook cells by stable cell ID and separate
source, generated-review artifact, portable, test, and build-output changes.

Stop after the two reports are committed. Do not create WP14, merge to `main`,
push, deploy, or begin a classification exercise.
