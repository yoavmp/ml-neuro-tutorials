# WP14 — Exercises 2–3 pedagogical revisions and interactive bias–variance demonstration

## Objective

Revise Exercises 2 and 3 according to instructor review:

- simplify Exercise 2 to age prediction with ordinary linear regression;
- use all 360 cortical parcels consistently;
- introduce scaling manually before showing the pipeline shortcut;
- extend the sample-size curve down to genuinely small samples;
- make every Think first box use one shared blue design;
- teach training-only cross-validation explicitly in Exercise 3;
- replace Exercise 3's static honest/invalid comparisons with one interactive
  comparison across `k`;
- improve the existing `k` explorer with precise numeric entry, an identity-line
  legend, and training-resample views that visibly illustrate variance and the
  increasing bias/mean-prediction tendency at large `k`.

This is a correction/refinement WP. Do not add classification material beyond
the existing short forward reference.

## 0. Mandatory Git checkpoint

Before editing:

1. Inspect the current branch, status, recent log, WP13 report, and WP13 exact
   changelog.
2. Preserve all current work. Commit any uncommitted state before editing;
   never discard or overwrite user changes.
3. Create tag `wp14-start` at the exact pre-WP14 state. If it already exists,
   stop and report the conflict.
4. Record the checkpoint SHA, tag target, and branch in the report.
5. Continue on the existing feature branch unless the established workflow
   requires a child branch.
6. Do not push, merge, deploy, or change repository visibility.

## 1. Audit the 360-parcel correction before rewriting outputs

The current code uses 358 cortical-thickness predictors because two columns
were excluded by the bilateral/parcel-name parser. Inspect the raw prepared
ABIDE table and atlas taxonomy directly. Determine the exact two excluded
columns and verify that they are genuine cortical parcel measurements rather
than identifiers, aggregates, or malformed fields.

The intended student-facing feature set is:

> every one of the 360 cortical atlas parcel columns for the selected
> measurement family.

If the inspection confirms 360 genuine CT parcel columns, change the canonical
feature parser/manifest to include all 360. Do not introduce a special-case
student explanation about excluding two labels. Make the taxonomy parser
correctly recognize legitimate parcel names that happen to contain or end in
`L`/`R`; do not simply disable all validation.

If the raw data do not actually contain 360 valid CT parcel columns, stop before
rewriting the notebooks and report the exact schema discrepancy to Yoav.

After changing the feature definition, rerun every affected audit rather than
editing stored metrics manually:

- Exercise 2 OLS audit/output;
- regression comparison catalog;
- Exercise 2 learning curve;
- KNN audit and selected `k`;
- Exercise 3 development curve;
- both KNN interactive artifacts;
- all dependent tests and portable outputs.

Do not assume that WP12/WP13 values such as p=358, k=15, k=17, or their R²/MSE
remain unchanged. The fixed participant splits should remain identical unless a
verified data issue requires otherwise.

## 2. One shared blue Think first component

Standardize **all current canonical notebooks (Exercises 1, 2, and 3)** on one
shared Think first template.

- Use one stable MyST/admonition class, preferably `think-first`.
- Define its appearance once in shared CSS.
- Use a clearly blue border/header/background treatment, accessible contrast,
  and consistent spacing/iconography.
- Replace every old Think first variant with the shared markup.
- Do not recolor the green Run/download blocks or the revealable Check your
  reasoning dropdowns.
- Ensure portable notebooks receive a clean plain-Markdown equivalent and no
  MyST residue.

Add structural and built-page tests proving that every Think first block uses
the shared class and that no legacy Think first template remains. Visually
inspect all three chapters at desktop and mobile widths.

## 3. Exercise 2 revisions

### 3.1 Remove regularization and FIQ from the notebook

Delete the entire current section **“5. Regularisation preview: age vs FIQ with
the full brain.”** Remove all FIQ analysis, FIQ prose, FIQ figures, IQ-specific
literature, code, outputs, questions, and summary references from both:

- `book/chapters/chapter_02/exercise_02.ipynb`;
- `book/downloads/chapter_02/exercise_02_portable.ipynb`.

Exercise 2 should now remain entirely about predicting age using ordinary
linear regression. Renumber the following sample-size section and update every
internal reference. Do not leave a “regularization removed” note for students.

The phenotypic FIQ source/audit may remain as internal historical tooling only
if other reviewed infrastructure still depends on it, but it must not be loaded
or mentioned anywhere in the Exercise 2 canonical/portable notebook or its
student-facing activity/config. Prefer simplifying the Exercise 2 loader to the
single prepared brain table if the age target is already present there.

### 3.2 Add the research-question framing

In the Exercise 2 introduction, add a concise paragraph explaining:

- ABIDE's central research aim concerns autism-related group differences and
  diagnosis/classification;
- rich shared datasets can support multiple scientifically appropriate
  questions beyond their primary aim;
- here, the continuous target is age, so the task is regression: predicting a
  participant's age from cortical measurements.

Do not imply that this notebook answers ABIDE's primary autism question, and do
not introduce classification methods here.

### 3.3 Remove instructor-facing commentary

Remove the phrase:

> without turning this into a splitting lecture

Search both canonical and portable notebooks for other student-facing comments
that refer to WPs, reports, scripts, implementation decisions, or instructions
to the notebook author. Rewrite or remove them. Student-facing provenance links
and meaningful methodological explanations should remain.

### 3.4 Teach scaling explicitly, then show the pipeline shortcut

The first preprocessing/model example must show the underlying steps directly:

```python
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = LinearRegression()
model.fit(X_train_scaled, y_train)
y_pred = model.predict(X_test_scaled)
```

Explain briefly:

- `fit_transform` learns means/standard deviations from training data and
  applies them there;
- `transform` applies those already-learned values to test data;
- the scaler must never be fitted on the test set;
- scaling does not ordinarily change unregularized OLS predictions when an
  intercept is included, but this explicit workflow prepares students for
  distance-based KNN, where scaling matters greatly.

Only after students have seen the explicit form, introduce
`make_pipeline(StandardScaler(), LinearRegression())` as a convenient and safer
shortcut that bundles the same operations. Put the pipeline version in a short
visible or revealable example, not as unexplained magic. Ensure subsequent code
uses one clearly defined model path without duplicating results confusingly.

### 3.5 Use all 360 CT parcels

Replace every 358-feature statement, output, annotation, manifest entry, ratio,
and code assumption with the audited 360-feature definition and freshly
computed values. Refer to them as **360 cortical parcels/features**, not “360
brain regions per hemisphere.” Do not explain the old exclusion.

### 3.6 Start the sample-size demonstration at low N

Revise the age learning curve to begin at genuinely small training sizes. Use a
predeclared sequence such as:

```text
50, 100, 200, 300, 400, 550, full training N
```

Adjust only if deterministic feasibility/testing requires it, and document any
change in the report. Include 50 or 100 as the first point.

Because the smallest samples have fewer observations than predictors, explain
briefly that OLS is underdetermined when `n_train <= p`; scikit-learn can still
return a minimum-norm solution, but it may be extremely unstable. This is part
of the lesson, not a hidden failure.

Use repeated deterministic subsamples and report a central tendency plus a
spread interval. Choose a plot scale/layout that keeps the full honest range
readable—log MSE, a broken/inset view, or separate R²/MSE panels are acceptable.
Do not clip or silently omit extreme negative R² values. Emphasize that the
curve reflects both increasing sample size and movement from `n < p` to
`n > p`.

Update questions and synthesis accordingly.

## 4. Exercise 3 revisions

### 4.1 Use the same 360-feature recipe

Exercise 3 must use the exact same 360-CT-parcel feature definition and locked
participant split as the revised Exercise 2. Rerun the KNN audit. Select `k`
using training-only cross-validation again and update every dependent metric,
figure, annotation, activity default, portable output, and test from the new
result.

Do not retain hardcoded WP13 numbers unless they remain correct after the audit.

### 4.2 Remove internal implementation references from student material

Remove student-facing references to:

- `scripts/knn_model_audit.py`;
- any `scripts/...` path;
- WP13 or another WP report;
- internal JSON artifacts, exporters, test names, or repository implementation
  details.

In particular, remove/rewrite the multi-line comment saying the chosen `k` was
selected by five-fold CV and pointing students to the audit script/report.
Replace it with the actual cross-validation teaching code described below.

Internal scripts, tests, reports, and developer documentation may still use
their real paths.

### 4.3 Teach cross-validation for choosing k

Before fitting the final test model, include a readable, student-facing code
example that:

1. defines a manageable candidate set of `k` values;
2. performs five-fold cross-validation on `X_train, y_train` only;
3. fits `StandardScaler` separately inside every fold (use a pipeline here,
   now that Exercise 2 has already introduced the shortcut);
4. records mean validation R² or MSE for every candidate;
5. selects the best `k` from the validation results;
6. only then refits that chosen pipeline on all training rows;
7. evaluates it once on the untouched test rows.

Prefer a transparent loop with `cross_val_score` or a compact `GridSearchCV`
example whose output students can understand. Explain that the test set does
not choose `k`; it estimates performance after the choice is fixed. Display a
small result table or plot, not an overwhelming list.

The notebook's chosen `k` must arise from this executable code rather than a
number copied from an internal audit. The independent audit should verify the
same answer.

### 4.4 Replace Section 3 with one interactive A/B/C comparison

Remove both current static examples:

- the fixed selected-`k` A/B/C table/figures;
- the separate static `k=1` demonstration.

Replace them with one interactive activity where the student chooses `k` and
sees three synchronized observed-versus-predicted panels and metrics:

- **A — valid:** fit on training rows, evaluate test rows;
- **B — resubstitution:** fit on training rows, evaluate those training rows;
- **C — invalid leakage:** fit on test rows, evaluate those same test rows.

Use the same standardized 360-feature recipe throughout. Provide both a slider
and numeric input. Since C is fitted on the smaller test set, the common valid
range should be `1..min(n_train, n_test)` unless a better, clearly explained UI
handles unavailable values. Do not silently let `k` exceed a fitted sample.

Changing `k` must recompute all three real prediction arrays, plots, R², and
MSE—not merely labels. Use identical axes across the three panels. The perfect
prediction identity line must appear in every panel and be identified in a
legend.

Default to the newly CV-selected `k`. Add endpoint/prompt text making clear:

- at `k=1`, B and C are exactly perfect because each evaluated fitted point is
  its own nearest neighbour;
- A at `k=1` is not perfect because test participants were not used for fitting;
- therefore `k=1` gives the clearest evidence that evaluating on fitted data is
  invalid, not evidence that KNN generalizes perfectly;
- increasing `k` averages more observations and usually reduces this dramatic
  resubstitution effect.

Precompute results deterministically for static-browser use. Do not store
participant identifiers or raw brain features. Validate representative and
endpoint predictions independently against scikit-learn. Ensure the invalid
test-fitted information is isolated to this activity and never used by later
sections or model selection.

For the portable notebook, replace the iframe with runnable Python code using a
clearly editable `k_demo` variable and a three-panel static output. It does not
need browser widgets, but it must preserve the same valid/invalid lesson.

### 4.5 Improve the existing Explore k control

Keep the range slider, but add a synchronized numeric input beside it so a
student can type an exact integer such as 15 or 20.

- Accepted range: `1..N_fit`.
- Clamp or visibly reject invalid/non-integer input; never produce an invalid
  model silently.
- Slider changes update the number field and typed changes update the slider.
- Both keyboard and pointer interaction must work.
- Refresh restores the documented default.

### 4.6 Explain the dotted line

In **Observed vs predicted (validation set)**, label the dotted diagonal in a
visible legend as:

> Perfect prediction (`observed = predicted`)

Do not rely only on surrounding prose or hover text. Use the same identity-line
legend convention in the new Section 3 activity.

### 4.7 Remove duplicate reflection prompts

The current Section 6 “Reflect” and “Think first” prompts substantially repeat
one another. Retain one concise blue Think first block and remove the duplicate.
Update headings and spacing so no empty wrapper remains.

### 4.8 Add training-sample variation to illustrate variance

Enhance the existing `k` explorer while preserving its fixed validation set.
Create **three deterministic alternative training-set selections** from the
same development training pool, preferably equal-sized bootstrap resamples or
equal-sized subsamples chosen without reference to validation outcomes.

Add three clearly labeled buttons/tabs, for example `Training sample A`, `B`,
and `C`. Switching among them must leave validation participants unchanged but
update their predictions and the scatterplot for the current `k`.

The activity should make visible that:

- at small `k`, changing the training sample can change predictions strongly
  (high training-sample sensitivity / high variance);
- at large `k`, the fitted functions/predictions become more similar and move
  toward a training-sample mean (lower variance, stronger smoothing).

Include a compact quantitative **variance proxy**, such as the mean across
validation participants of the prediction variance/SD across the three
training samples. Label it explicitly as an empirical training-sample
sensitivity measure, not the formal population variance term.

### 4.9 Illustrate increasing bias at large k accurately

Add a complementary display showing systematic smoothing toward the mean. A
recommended implementation is a binned calibration/smoothing panel:

- x-axis: observed validation age (or age bins);
- y-axis: prediction averaged across the three training selections;
- include the perfect-prediction identity line;
- show how large `k` flattens the relationship, underpredicting older
  participants and overpredicting younger participants.

You may instead use another compact visualization if it communicates the same
idea more clearly. Include a quantitative **systematic-error/bias proxy** based
on ensemble-mean predictions, but label it carefully:

> This is an observable bias-like underfitting proxy, not formal bias², because
> ABIDE does not reveal the unknown population function and observed age-level
> outcomes still contain irreducible variation.

The classic conceptual graph remains the source for the formal decomposition.
Do not claim that the ABIDE interaction directly estimates true statistical
bias or irreducible error.

### 4.10 State the central k–complexity relationship explicitly

Add a prominent concise explanation and connect it to both interactives:

- **larger `k`** averages more neighbours, approaches predicting the mean, and
  produces a **simpler, smoother model: lower variance but higher bias**;
- **smaller `k`** follows individual observations more closely and produces a
  **more flexible/complex model: lower bias but higher variance and greater
  overfitting risk**.

Qualify “lower bias” as a general KNN tendency rather than an absolute result
for every finite sample. At `k=N_fit`, predictions for new observations equal
the fitting-set target mean; test this exact endpoint.

## 5. Interactive architecture and performance

Implement the Section 3 comparison as a new config-driven activity type or a
clean extension of the existing KNN component—choose the design with the
clearest separation of valid and deliberately invalid artifacts. Reuse shared
plot/control utilities where sensible.

For the enhanced Section 6 activity:

- continue using a fixed validation set;
- keep all calculations deterministic;
- store only the minimum precomputed target-neighbour information needed;
- exclude participant IDs, raw cortical features, site, diagnosis, and other
  phenotypes;
- keep the artifact reasonably sized and document its byte size;
- load with no kernel, backend, CDN, WebSocket, or live data request;
- remain responsive at 390 px without horizontal page overflow.

For all generated predictions and metrics, perform independent schema and
numeric validation. Representative `k` values, all endpoints, and all three
training selections must agree with scikit-learn to an appropriate tolerance.

## 6. Portable notebooks and student-facing cleanliness

Regenerate Exercises 2 and 3 through the existing spec-driven generator.
Exercise 1 should change only as required for the standardized blue Think first
template. Verify:

- no WP/report/script/test/internal-artifact references in any student-facing
  canonical or portable notebook;
- no repository-dependent data path;
- correct package-install comments;
- no MyST directive, iframe, hide tag, Node requirement, credentials, or active
  install command in portable notebooks;
- Exercise 2 contains age/OLS only and no FIQ/regularization section;
- Exercise 3 contains runnable CV selection and portable A/B/C demonstration;
- all three portable notebooks execute from outside the repository.

## 7. Required validation

Run and report at minimum:

1. raw-schema/taxonomy audit proving exactly 360 valid parcel features per
   measurement family;
2. updated OLS and KNN audits with deterministic results;
3. notebook validation, unique cell IDs, allowed hide tags, current outputs,
   and no stderr/errors;
4. no FIQ/regularization content in Exercise 2;
5. no student-facing `scripts/`, WP, report, internal JSON, exporter, or test
   reference in canonical/portable notebooks;
6. manual-scaling sequence and pipeline-equivalence checks;
7. Exercise 2/3 exact 360-feature-recipe identity and leakage guards;
8. Exercise 2 learning-curve endpoints beginning at 50 or 100, deterministic
   repeated samples, and honest handling of extreme results;
9. Exercise 3 executable training-only CV selection reproduces the audit's
   chosen `k` before the single outer-test evaluation;
10. Section 3 interactive predictions/metrics recomputed independently for all
    `k`, including exact `k=1` resubstitution;
11. slider/numeric-input synchronization, validation, keyboard access, and
    refresh behavior in both KNN activities;
12. fixed validation rows across all three training selections;
13. independent verification of the variance proxy and bias-like proxy;
14. exact `k=N_fit` mean-prediction property for every training selection;
15. TypeScript typecheck/unit tests, Python tests, production build, and npm
    audit;
16. standalone and built-book Playwright tests under both root and project
    subpath, including real plot/metric changes;
17. portable freshness and out-of-repository smoke execution for all three
    notebooks;
18. clean Jupyter Book build with no new warnings/error logs;
19. link-target checks for every chapter's Colab/download controls;
20. desktop and 390-pixel visual inspection of all revised notebook sections,
    blue Think first boxes, legends, numeric controls, and multi-sample views.

Do not weaken or delete existing methodological tests merely to make changed
outputs pass. Update assertions to freshly audited values and add coverage for
the new behavior.

## 8. Deliverables and stop condition

Commit the implementation locally, then create and commit:

- `WPs/reports/WP14_REPORT.md`
- `WPs/reports/WP14_EXACT_CHANGELOG.md`

The report must begin with **SUCCESS**, **PARTIAL**, or **FAILED** and include:

- checkpoint/tag and final commit SHAs;
- exact identity of the two newly included parcel columns and proof that all
  four measurement families now contain 360 valid parcels;
- all updated Exercise 2 and KNN metrics;
- revised sample-size values and plot treatment;
- cross-validation candidate set and selected `k`;
- Section 3 interactive range/default/endpoints;
- training-resample construction and confirmation of fixed validation rows;
- observed variance-proxy and bias-like-proxy behavior at small, intermediate,
  and maximum `k`;
- every student-facing phrase/reference removed;
- Think first template changes across all notebooks;
- exact test commands and results;
- warnings, deviations, unresolved risks, and decisions needed from Yoav;
- explicit confirmation that nothing was pushed, merged, or deployed.

The exact changelog must identify every modified notebook cell by stable cell ID
and separate source, configuration, generated-reviewed data, portable, test,
and build-output changes.

Stop after committing both reports. Do not create WP15, push, merge, deploy, or
begin a classification notebook.
