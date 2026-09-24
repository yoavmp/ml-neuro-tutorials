# WP38R — Exercise 10 Review Corrections

## Purpose

Correct the reviewed Exercise 10 implementation without expanding its syllabus. The required
changes are:

1. repair the wrapped multiple-selection question so it never overlaps the activity content;
2. make every leakage comparison display both the correct and leaky results;
3. replace linear regression in the leakage laboratory with KNN regression, which is meaningfully
   affected by scaling and PCA;
4. replace the threshold-focused imbalance activity with a comparison across progressively more
   imbalanced control/autism samples;
5. clarify that debugging Fragment 4 refers to the smartphone-window dataset used earlier;
6. eliminate excessive empty space below interactive content through a durable, project-wide
   iframe/card sizing fix.

This is a correction-only work package. Do not merge, push, deploy, monitor GitHub Actions, or
start WP39.

---

## 1. Starting state and checkpoint

Start from the final clean tip of:

`feature/wp38-exercise10-common-mistakes`

Before editing:

1. inspect `git status --short --branch`;
2. record the complete branch-tip SHA;
3. confirm the branch contains, in order:
   - WP38 specification checkpoint `06fd62af0ea0eee8bcf5cc20274c8a5a1d8f7602`;
   - WP38 implementation commit `61a16c6f26a81b32c76c884b3122d266edc31bc1`;
   - one later WP38 report commit;
4. confirm the tree is clean;
5. record `main` and `origin/main`, but do not modify either.

The WP38 report did not record its own final report-commit SHA. Resolve that only by reading the
actual branch log; do not guess or rewrite history.

If the state differs unexpectedly, stop and report it. Do not reset, stash, rebase, delete, or
repair divergence automatically.

Create:

`fix/wp38r-exercise10-review`

from the verified WP38 branch tip.

Save this specification as:

`WPs/WP38R_EXERCISE_10_REVIEW_CORRECTIONS.md`

Commit only this specification as the first checkpoint before implementation.

---

## 2. Inspect before changing

Inspect the canonical Exercise 10 notebook, portable notebook, all four Exercise 10 widgets,
their committed artifacts/exporters, and their tests. Also inspect the shared iframe auto-resize
and widget-card CSS used by Exercises 1–10.

Reproduce each reported visual issue in the freshly built local book before fixing it. Measure the
relevant element and iframe heights in the browser rather than relying only on screenshots.

Preserve the existing architecture:

- one shared widget runtime;
- book-controlled light/dark theme synchronization;
- the existing resize message contract;
- deterministic offline artifacts;
- canonical and portable notebooks generated from the established sources.

Do not introduce a second resize system, a chapter-specific iframe hack, or fixed heights chosen
only for one viewport.

---

## 3. Multiple-selection question layout

The question currently wraps to two lines and drifts down into the activity box. Correct the
layout so that the full question remains visually separate from the answer list and feedback at:

- normal desktop widths;
- intermediate widths where it wraps to two or more lines;
- 390 px viewport width;
- light and dark themes;
- initial load and reload while dark mode is active.

Requirements:

- allow natural wrapping;
- do not truncate the question or reduce it to an unreadably small font;
- remove absolute positioning, fixed line assumptions, or insufficient fixed heights if they are
  the cause;
- retain an appropriate gap between the question and the first checkbox;
- preserve keyboard, label, focus, and ARIA behavior;
- ensure the parent iframe receives the corrected natural height after web fonts and wrapped text
  settle.

Add a focused browser regression test that verifies the question's bounding box does not overlap
the first option/activity region at desktop, an intermediate wrapping width, and 390 px.

---

## 4. Leakage laboratory: use KNN and show both results

### 4.1 Replace the estimator

Replace `LinearRegression` with `KNeighborsRegressor` throughout the Exercise 10 leakage
laboratory:

- exporter/audit logic;
- committed browser artifact;
- canonical notebook prose and code;
- portable notebook reproduction code;
- frontend labels/tooltips;
- tests and expected results.

Use one fixed, predeclared value:

`n_neighbors = 15`

This value is fixed as a familiar course example before the corrected results are calculated. It
must not be selected by inspecting test performance. Keep all existing sample sizes and seeds
unless a value is mathematically invalid for KNN; with the existing 75/25 split, `k=15` is valid
even at `n=60`.

Use the same KNN estimator in all three scenarios so the comparison changes only the relevant
preprocessing step:

1. **Scaling**
   - correct: split first; fit `StandardScaler` and KNN on training rows only;
   - leaky: fit the scaler on all selected rows, split the transformed rows, then fit KNN on the
     training rows only.
2. **Target-informed feature selection**
   - correct: split first; fit feature selection, scaling, and KNN using training rows only;
   - leaky: select features using all selected rows and their targets, then split; fit downstream
     scaling/KNN without using test targets again.
3. **PCA**
   - correct: split first; fit scaling, PCA, and KNN using training rows only;
   - leaky: fit scaling and PCA on all selected rows, then split the component scores; fit KNN on
     training rows only.

Use identical participants and identical outer splits within every correct/leaky pair. Preserve
the predeclared sample sizes and consecutive seed catalog. Do not search for seeds, feature
counts, component counts, or a different `k` after seeing the results.

KNN should make scaling and PCA consequential, but the notebook must still state that leakage is
invalid even when one split shows little improvement or a worse score.

### 4.2 Display paired metrics consistently

Audit every visible leakage example and result block. Wherever a correct-pipeline R² or MSE is
shown, display the matching leaky-pipeline value beside it.

For each selected scenario/sample size/seed, show:

- correct R²;
- leaky R²;
- correct MSE;
- leaky MSE;
- the clearly signed difference, with its direction defined in the label.

Use unambiguous labels such as **Correct pipeline** and **Leaky pipeline**. Do not rely only on
color. The comparison must be present in:

- the browser activity;
- visible notebook result summaries;
- the portable notebook output;
- any static reproduction table or figure retained in the notebook.

If the code that reproduces the browser figure remains hidden/collapsed on the website, students
should still see the paired result; the portable notebook should expose the runnable code.

Recompute the committed leakage artifact once under the predeclared design and report the complete
new result table. Do not curate the displayed seed.

---

## 5. Redesign the class-imbalance activity

Replace **High Accuracy Can Still Miss the Minority Class** as a threshold-comparison activity.
Remove the threshold slider and all threshold-selection framing from Exercise 10.

The new activity should compare the same two valid pipelines across these fixed class balances:

- 50% control / 50% autism;
- 60% control / 40% autism;
- 70% control / 30% autism;
- 80% control / 20% autism;
- 90% control / 10% autism.

Models:

1. ordinary logistic regression;
2. logistic regression with `class_weight="balanced"`.

Use the established ABIDE autism-classification feature set and preprocessing. For each balance,
both models must use the same participants, split, scaling, fixed `C=1.0`, and decision threshold
0.5. Preprocessing remains training-only. Do not tune a threshold or any model parameter on the
test data.

Use one predeclared deterministic sampling/splitting rule across all ratios. If multiple
predeclared seeds are retained to show variability, define them before generating results and
display/summarize all of them; do not search for a favorable seed. Keep total cohort size fixed
where feasible so changing prevalence, rather than sample size, is the central manipulation.

### 5.1 Interaction and output

Required primary control:

- control/autism balance selector: 50/50, 60/40, 70/30, 80/20, 90/10.

Do not include a threshold control.

Show both models simultaneously for the selected balance. Include:

- majority-class baseline accuracy;
- accuracy;
- balanced accuracy;
- autism recall;
- precision;
- F1;
- ROC-AUC;
- PR-AUC;
- PR-AUC baseline equal to autism prevalence;
- side-by-side confusion matrices or another equally clear presentation of TN/FP/FN/TP.

Avoid presenting every metric as an equally prominent tile. The visual hierarchy should first
make these comparisons clear:

1. model accuracy versus the majority baseline;
2. minority-class detection, especially recall and F1;
3. threshold-independent ROC-AUC and prevalence-sensitive PR-AUC.

Add one compact across-balance graph so students can see how accuracy, its baseline, and the
minority-sensitive measures change as imbalance increases. A selected-metric control is
acceptable if it keeps the figure readable, but the default view must expose the central
accuracy-versus-baseline lesson immediately.

### 5.2 Student-facing interpretation

Keep the explanation concise. Make these points:

- raw accuracy can increase merely because the majority class becomes easier to guess;
- the majority baseline changes with prevalence;
- class weighting may improve autism recall, balanced accuracy, or F1 while reducing raw
  accuracy;
- class weighting is not guaranteed to improve every metric;
- ROC-AUC evaluates ranking across thresholds, whereas PR-AUC is sensitive to positive-class
  prevalence;
- the useful metric depends on the scientific question and the costs of false positives and false
  negatives.

Use questions such as:

- As controls become more common, does higher accuracy necessarily mean a better classifier?
- How far is each model above the majority baseline?
- Which model detects more autistic participants?
- Which conclusion changes when you inspect recall, F1, or PR-AUC instead of accuracy alone?

Update all notebook prose, activity text, artifacts, schemas/components, portable code, tests, and
the final checklist if required. Remove stale threshold-focused Exercise 10 text everywhere.

---

## 6. Clarify debugging Fragment 4

Rewrite Fragment 4 so students cannot mistake it for a generic independent-row prediction task.
State explicitly that it uses the UCI smartphone activity dataset from Section 4, where each
participant contributes many sensor windows and some windows overlap in time.

The fragment and its answer should make clear that randomly splitting windows places observations
from the same participant on both sides of the evaluation boundary. The correction is a
participant-grouped split when the goal is generalization to new people.

Do not state that row-wise splitting is universally invalid; preserve the distinction between
generalizing to new windows from known users and generalizing to new users.

---

## 7. Remove excessive empty space from interactive boxes

This is a project-wide correction, not a one-off Exercise 10 CSS patch.

Inspect the shared widget card, document/root layout, Plotly container sizing, iframe natural-
height reporting, host-page message handler, and resize behavior after content contraction.
Identify the actual source or sources of the large blank lower regions reported by the user.

Common possibilities to verify rather than assume include:

- fixed or excessive `min-height` on the widget/card/root;
- a flex child growing to fill an inherited height;
- Plotly containers retaining an obsolete height;
- the iframe reporting only growth and not shrinkage;
- height measured before fonts/plots settle and never corrected;
- the host accepting a maximum historical height rather than the current natural height;
- default body/root margins or padding being counted twice.

Implement the smallest shared fix that allows both growth and shrinkage. Do not shorten plots so
far that labels or legends become unreadable, and do not solve whitespace by clipping overflow.

### 7.1 Quantitative height contract

Strengthen the existing iframe-height tests so they fail on excessive blank space as well as
clipping. Test every registered activity in Exercises 1–10, with particular inspection of all
four Exercise 10 activities.

At minimum verify:

- desktop and 390 px;
- light and dark mode;
- initial render;
- after a control expands content;
- after reset or a control change contracts content;
- wrapped headings and delayed Plotly/font layout;
- iframe height closely tracks the widget document's current natural height;
- the distance below the final meaningful element is limited to intentional card padding, not a
  large residual region;
- no axis title, legend, feedback panel, or focus ring is clipped.

Choose explicit tolerances based on the shared design's intended padding and document them in the
test. Do not use a loose threshold that would allow the currently reported large gaps. Capture
before/after measurements in the WP38R report.

Manually inspect every Exercise 10 activity at desktop and 390 px in both themes after the
automated contract passes.

---

## 8. Canonical and portable notebook consistency

After the corrections:

- execute the canonical Exercise 10 notebook once;
- regenerate the Chapter 10 portable notebook using the established generator;
- run the all-chapter portable `--check`;
- smoke-execute Chapter 10 outside the repository;
- confirm the portable notebook contains the new KNN leakage examples and balance-based imbalance
  comparison, with no frontend dependency;
- confirm website-hidden reproduction code remains visible and runnable in the portable notebook;
- confirm no student-facing text references WPs, scripts, repository internals, or
  `requirements.txt`.

Do not alter the Syllabus or Word course overview.

---

## 9. Required tests

Add or update focused tests for at least:

### 9.1 Quiz layout

- no question/options overlap at desktop, an intermediate wrapping width, and 390 px;
- correct natural-height report after wrapping;
- unchanged quiz correctness, reset, keyboard, focus, and ARIA behavior.

### 9.2 Leakage laboratory

- estimator is KNN regression with fixed `k=15` everywhere;
- no remaining Exercise 10 leakage-lab `LinearRegression` usage or student text;
- correct/leaky pairs use identical rows and splits;
- preprocessing boundaries match Section 4.1;
- all visible results contain both R² values and both MSE values;
- browser artifact matches independent Python recomputation;
- no post-result seed, feature-count, component-count, or parameter selection;
- portable output matches the committed artifact.

### 9.3 Imbalance activity

- exact five balance levels;
- fixed total cohort size where the data permit it;
- both models share participants/splits/preprocessing/`C=1.0`/threshold 0.5 within each balance;
- no threshold control or stale threshold-focused Exercise 10 language;
- majority and PR-AUC baselines are correct for every balance;
- confusion matrices and all displayed metrics are internally consistent;
- browser values match the audited Python artifact;
- class weighting is not described as universally superior.

### 9.4 Fragment 4

- explicitly identifies the earlier smartphone-window dataset;
- names repeated windows per participant and participant-grouped evaluation;
- preserves the known-user versus new-user nuance.

### 9.5 Shared iframe/card sizing

- every registered Exercise 1–10 activity remains unclipped;
- iframe can shrink after contraction/reset;
- explicit maximum residual-space tolerance;
- wrapped headings and Plotly activities covered;
- desktop/390 px and light/dark coverage;
- no page-level horizontal overflow or unexpected console errors.

---

## 10. Bounded validation plan

Run one normal attempt per gate. For a genuine defect, allow at most one targeted correction and
one targeted rerun before reporting it. Do not repeatedly restart full suites.

1. Reproduce and record the quiz overlap and representative whitespace measurements.
2. Recompute the KNN leakage artifact once under the predeclared design.
3. Compute the five-balance imbalance artifact once under the predeclared design.
4. Run focused exporter/audit checks.
5. Run focused Exercise 10 notebook/content tests.
6. Execute the canonical notebook once.
7. Regenerate Chapter 10 portable notebook and run the all-chapter generator check.
8. Smoke-execute Chapter 10 portable notebook outside the repository.
9. Run frontend typecheck and focused unit tests.
10. Run one frontend production build.
11. Run focused standalone Playwright tests for the corrected activities and height contract.
12. Run one clean Jupyter Book build.
13. Run focused built-book Exercise 10, quiz-layout, dark-mode, narrow-layout, launch-button, and
    quantitative iframe-height tests.
14. Run the full offline Python suite once.
15. Run the full frontend unit suite once.
16. Run the full standalone Playwright suite once.
17. Run the full built-book Playwright suite once.
18. Perform the required manual visual inspection.

Do not:

- search seeds, models, feature counts, PCA dimensions, or K values after seeing results;
- weaken a scientific inclusion rule to obtain a clearer figure;
- use sleeps or repeated stress runs to hide resize timing defects;
- regenerate unrelated artifacts;
- leave background servers or watchers running;
- merge, push, deploy, or monitor GitHub Actions.

---

## 11. Reports and final state

Create:

- `WPs/reports/WP38R_REPORT.md`;
- `WPs/reports/WP38R_EXACT_CHANGELOG.md`.

The report must include:

1. overall success/failure;
2. exact starting WP38 branch-tip SHA, local `main`, and `origin/main`;
3. checkpoint, implementation, and final report SHAs;
4. the root cause of the quiz overlap;
5. the root cause of excessive iframe/card whitespace;
6. quantitative before/after height measurements and chosen tolerances;
7. the complete KNN leakage design and result table across all sample sizes/seeds;
8. confirmation that every visible leakage comparison shows both R² and MSE values;
9. exact class counts and all metrics for both logistic models at every class balance;
10. updated notebook outline/cell count;
11. every validation command and outcome;
12. retries, deviations, judgment calls, and unresolved issues;
13. confirmation that Syllabus and Word overview were untouched;
14. confirmation that nothing was merged, pushed, deployed, or monitored through CI;
15. literal final `git status --short --branch` captured after the report commit;
16. the actual final report-commit SHA obtained from `git log`, not a placeholder.

Commit implementation and reports locally on:

`fix/wp38r-exercise10-review`

Do not merge into `main`, push, deploy, monitor GitHub Actions, or start WP39.
