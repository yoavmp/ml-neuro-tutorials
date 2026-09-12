# WP11 — Begin Exercise II: linear regression and generalization with ABIDE

## Objective

Create the first, linear-regression portion of Exercise II using the prepared
ABIDE phenotype-plus-regional-neuroimaging table. The notebook follows the
lecture and tutor presentation, so it should emphasize applied practice,
prediction, evaluation, feature-set choices, and sample-size reasoning rather
than reteaching regression theory at length.

This WP includes:

1. loading and understanding the wide ABIDE modeling table;
2. one transparent linear-regression workflow;
3. an explicit comparison of correct held-out evaluation, optimistic training
   evaluation, and deliberately invalid fit-on-test/evaluate-on-test leakage;
4. a browser-native side-by-side feature-set comparison activity;
5. a careful demonstration of sample-size effects.

Do **not** add KNN or a full bias–variance section yet. Do not merge to `main`,
deploy, change hosting/private-public distribution, or alter Exercise I except
where a shared reusable generator/test must be extended without changing its
rendered content.

## Required reading

Read completely before acting:

- `CLAUDE_INTERACTIVE_WIDGETS.md`
- `WPs/README.md`
- `WPs/reports/WP09_REPORT.md`
- `WPs/reports/WP09_EXACT_CHANGELOG.md`
- `WPs/reports/WP10_REPORT.md`
- `WPs/reports/WP10_EXACT_CHANGELOG.md`
- this WP

Inspect the current source and tests directly; reports are context, not a
substitute for the repository state.

## 1. Branch, checkpoint, and baseline

1. Confirm `feature/course-pages-and-eda-trim` contains the committed WP10
   implementation and reports and has a clean working tree apart from this WP
   brief.
2. Create a new branch from that exact HEAD:
   `feature/regression-practice`.
3. Add this WP and commit `checkpoint: before WP11` before implementation.
4. Create annotated tag `wp11-start` at the checkpoint, with an unambiguous
   suffix only if the tag already exists.
5. Run the complete WP10 baseline and record exact counts/results:
   frontend install/typecheck/unit/audit/build; all widget artifact checks;
   Python tests; portable checks/smoke; standalone Playwright; clean Jupyter
   Book build plus `*.err.log` guard; built-book Playwright; deterministic
   repeated builds.

Never discard user work, use destructive git commands, rewrite history,
force-push, or commit build outputs/caches. Do not merge or deploy WP11.

## 2. Audit the prepared ABIDE modeling data before designing examples

The user wants the compact prepared table containing phenotype variables plus
many regional brain measurements, associated with the Neurohackademy material:

`https://github.com/neurohackademy/nh2020-curriculum/tree/master/tu-machine-learning-yarkoni`

Locate and inspect the exact table already referenced/available in the project,
or the appropriate table at that source. Do not assume it is the same ABIDE-II
phenotype-only file used in Exercise I.

Before notebook authoring, programmatically establish and record:

- authoritative source URL pinned to an immutable commit when possible;
- filename, checksum, provenance, and applicable attribution/usage note;
- whether it is ABIDE-I, ABIDE-II, or a combined/derived sample;
- row count, unique participant count, duplicate status, and identifier field;
- phenotype/target columns and their non-missing counts;
- brain-feature count;
- atlas/parcellation and exact ROI naming convention;
- measurement types represented and how they are encoded in column names;
- hemisphere encoding;
- missingness in brain features;
- sites and diagnostic groups represented;
- any preprocessing already applied to the brain measurements.

Create a deterministic parser/manifest that classifies columns into identifiers,
phenotypes, measurement types, ROIs, hemispheres, and brain features. Do not
scatter fragile string slicing through the notebook or TypeScript frontend.
Unknown or malformed feature names should fail validation with an actionable
message.

If the intended table cannot be identified confidently, if its ROI/measure
semantics cannot be established, or if access/redistribution terms are unclear,
stop before substituting another dataset and report the blocker.

### Leakage guard

The input matrix must contain **brain-derived features only**. Explicitly reject:

- the target itself;
- alternative IQ/test-score columns such as VIQ/PIQ when predicting FIQ;
- diagnosis, age, sex, site, participant id, or other phenotypes unless a later
  analysis explicitly introduces them as covariates;
- columns computed directly from the target.

Add tests that the feature set cannot contain target or phenotype leakage.

## 3. Select targets and feature sets from evidence, not desired performance

### Main target

Prefer `FIQ` or the table's corresponding full-scale intelligence/test score if
it has high availability after requiring usable brain data. Confirm its exact
meaning and count from the table. If another target is materially more suitable,
explain and report the deviation before using it.

### Lower-availability target

Inspect all plausible continuous test/behavioral scores after merging with valid
brain measurements. Select one with clearly lower availability for the
sample-size discussion only if:

- its meaning is documented;
- it is not essentially confined to one site;
- its availability is not merely structurally absent for an incomparable group
  in a way that makes the exercise misleading;
- enough participants remain for a defensible small linear model and held-out
  evaluation.

The user's ideal contrast is below 100 versus roughly 1,000 participants, but do
not force this. A cleaner contrast such as approximately 300 versus 900 may be
preferable. Report the full availability audit, the chosen target, and why any
lower-N candidate was rejected.

### Literature-motivated anatomy

Define the principal anatomical bundle before inspecting its predictive
performance. Use primary/reputable literature to motivate a broad
frontoparietal intelligence-related set and map it transparently to the table's
actual atlas labels. Candidate starting sources to verify are:

- Jung & Haier (2007), Parieto-Frontal Integration Theory:
  `https://doi.org/10.1017/S0140525X07001185`
- Narr et al. (2007), IQ and regional cortical thickness:
  `https://doi.org/10.1093/cercor/bhl125`

Verify citation details and links. Use literature as hypothesis motivation, not
as proof that those features must predict the score in ABIDE. Do not select or
rename a bundle after seeing which combination maximizes this dataset's result.

Create a small set of pedagogically meaningful, deterministic ROI bundles based
on anatomy/literature—for example frontoparietal, frontal, parietal, temporal,
occipital/comparison, and all eligible ROIs—only where those labels can be
mapped correctly to the actual atlas. Store membership in a reviewed config or
manifest and test every feature-to-bundle mapping.

## 4. Create Exercise II and navigation

Create the canonical notebook at a repository-consistent path such as:

`book/chapters/chapter_02/exercise_02.ipynb`

Use the H1 title:

> Exercise II: Regression

Add it after Exercise I in `_toc.yml` and the Contents page, preserving:

Introduction → Syllabus → Contents → Exercise I → Exercise II

The notebook opening should contain only:

- the H1;
- a compact run/download control consistent with Exercise I;
- **What this notebook covers**, limited to the linear-regression material
  actually implemented in WP11;
- concise prerequisites consistent with the lecture-first course structure.

Do not repeat the course-level Introduction/How-to material. Do not add a time
budget. Keep the established rust/cream design and question/admonition style.

Target a substantially shorter notebook than Exercise I. Prefer roughly 35–50
canonical cells for this linear portion and remove any section that merely
repeats lecture definitions without supporting an activity, decision, or
interpretation.

## 5. Section 1 — Load and inspect the wide modeling table

Briefly explain:

- one row = one participant;
- phenotype columns contain possible outcomes/context;
- brain columns combine a regional measurement with an ROI/hemisphere;
- this is a modeling table rather than the small phenotype-only EDA table.

Show only what students need:

- shape;
- a compact sample that does not print hundreds of columns;
- a short summary of phenotype count, brain-feature count, measurement types,
  and ROI count;
- target availability.

Use a compact, readable representation—for example phenotype columns plus a few
representative brain columns and a separate count summary. Do not dump the full
wide dataframe.

Add one **Think first** card asking students to distinguish outcome, features,
participants, measurement types, and ROIs. Some questions may have a concise
reasoning dropdown; do not provide an answer to every prompt.

Keep data acquisition/parsing code hidden or collapsed in the published book,
but visible/runnable in the portable notebook.

## 6. Section 2 — One transparent linear-regression workflow

Use a deterministic, predeclared compact brain-feature set for the main target.
It should be large enough to illustrate multivariate regression but small enough
that ordinary least squares is identifiable and not dominated by `p >= n`.
Do not choose it because it happens to maximize performance.

Build the correct workflow in readable steps:

1. select brain-only `X` and target `y`;
2. exclude rows missing the target;
3. create a fixed, reproducible train/test split;
4. fit any imputation/scaling **inside a scikit-learn Pipeline on training data
   only** if the audited brain table requires it;
5. fit `LinearRegression` on training data;
6. predict the untouched test data;
7. calculate held-out `R²` and MSE;
8. plot observed versus predicted test scores with a diagonal perfect-prediction
   reference.

Use a split that reasonably preserves important composition such as diagnosis
where feasible without turning this into a splitting lecture. State precisely
what population the split estimates generalization to. Include one short caveat
that a random participant split across a multisite dataset does not establish
generalization to entirely unseen scanners/sites.

Clarify:

- the fitted hyperplane is difficult to draw in the original high-dimensional
  feature space;
- observed-versus-predicted values remain straightforward and informative;
- negative held-out `R²` is valid and means the model performs worse than the
  appropriate mean-prediction baseline.

Do not hide the core `fit`, `predict`, and metric code. Collapse only lengthy
data preparation or plotting logistics.

## 7. Section 3 — Training performance, held-out performance, and leakage

Immediately after the simple model, create a deliberately explicit comparison
using the **same fixed split and same predeclared feature set**:

### A. Correct generalization estimate

```text
fit on training rows → predict/evaluate on untouched test rows
```

### B. Optimistic resubstitution performance

```text
fit on training rows → predict/evaluate on those same training rows
```

This is useful as a training diagnostic but is not an estimate of performance
on new participants.

### C. Deliberately invalid test leakage

```text
fit on test rows → predict/evaluate on those same test rows
```

Label C prominently as **wrong / invalid / do not use**. It exists only to show
why data used for fitting cannot also provide an honest evaluation. Use a
separate clearly named object such as `invalid_test_fitted_model` so it cannot
be reused accidentally later.

Before revealing results, ask students to predict the ordering of the three
scores and explain why. Then show a compact three-row metrics table and, if it
remains readable, three aligned observed-versus-predicted panels with identical
axis limits. Report both `R²` and MSE.

Important safeguards:

- do not call training performance or fit-test/predict-test a valid competing
  model;
- do not cherry-pick a split or feature set to manufacture a dramatic gap;
- use the actual result even if inflation is modest;
- report `n_train`, `n_test`, and feature count so students can interpret model
  flexibility;
- explain that comparing training and test metrics involves different rows,
  while A versus C uses the same test rows and isolates the contamination more
  directly;
- keep this demonstration isolated from all later model comparison artifacts.

Add tests proving the split is disjoint for A, identical fitting/evaluation rows
are used only in B/C, and the invalid model is never used in later sections.

## 8. Section 4 — Interactive feature-set comparison

Create one browser-native, reusable activity consistent with the existing
TypeScript/Vite/config-driven architecture. The activity should let students
configure **Model A** and **Model B** and compare them side by side.

### Controls

Each model must provide:

- main target fixed initially to the selected high-availability test score;
- measurement-type selection using the audited types;
- anatomical/ROI-bundle selection using the reviewed bundle manifest;
- visible list or revealable summary of the exact ROIs included;
- feature count.

Avoid hundreds of raw ROI checkboxes. Prefer a finite, transparent catalog of
measurement subsets × anatomically defined ROI bundles. If checkboxes allow
combining multiple measurement types, support only combinations for which a
canonical model result exists and clearly disable/explain invalid combinations.

### Output

For A and B show:

- out-of-sample/cross-validated `R²`;
- cross-validated MSE;
- observed-versus-out-of-fold-predicted scatterplot with a perfect-prediction
  diagonal;
- participant count;
- feature count.

Use the **same eligible participant cohort and identical deterministic folds**
for every configuration so feature-set comparisons are fair. Preprocessing must
be fitted inside each fold. Do not show training scores.

The activity should explicitly support these comparisons:

- same anatomy, different measurement types;
- same measurement type, different anatomical bundles;
- literature-motivated bundle versus a similarly scoped anatomical comparison;
- selected bundle versus all eligible ROIs, only if ordinary least squares is
  identifiable and numerically defensible in every training fold.

If `p` approaches/exceeds fold training `n`, do not silently use a pseudoinverse
and present the result as ordinary evidence. Exclude/disable that configuration
with a clear reason. Do not introduce ridge regression in this WP unless the
user separately authorizes teaching regularization.

### Static-site implementation

Prefer offline Python generation of a finite, deterministic model catalog and
prediction artifact over reimplementing scikit-learn numerics in JavaScript.
The browser should switch among audited precomputed results. The export must:

- use the same source checksum, cohort, folds, preprocessing, and metric
  definitions for every catalog entry;
- contain no participant identifiers;
- store only data required for plots/metrics;
- validate schema, finite values, row alignment, model keys, and canonical
  regeneration;
- fail on target/phenotype leakage;
- remain reasonably sized and load without a CDN/backend.

Show a concise note that trying many configurations is exploratory model
comparison; selecting the best result and reporting the same cross-validation
score as final performance would be selection bias. A locked test set or nested
procedure would be needed for a final unbiased claim.

### Literature framing

Immediately before the activity, include a short paragraph/dropdown with the
verified P-FIT/cortical-morphology links and the exact atlas mapping. Keep it
brief. Literature motivates an a priori feature bundle; it does not guarantee
predictive success or prove that a better-performing bundle is biologically
causal.

### Interaction tests

Test config/schema errors, canonical artifact generation, metric recomputation,
identical folds/cohort, no identifiers/leakage, both model panels, controls,
scatter redraw, negative `R²`, reset/defaults, keyboard access, responsive
layout, subpath deployment, offline/no-CDN behavior, and iframe integration in
the clean built book. A real control change must alter the corresponding plot
and metrics, not only a text label.

## 9. Section 5 — What does sample size change?

This section must distinguish two questions.

### Part A: Two outcomes with different availability

Show the usable participant counts for the high-availability main target and the
audited lower-availability target. Fit the **same compact brain-feature recipe**
with the same evaluation philosophy where feasible.

Ask before interpretation:

> Is a performance difference evidence that one score is intrinsically easier
> to predict, or could it reflect sample size, reliability, range, diagnosis,
> site, or who received the assessment?

State that comparing different outcomes cannot isolate sample size. Do not
compare raw MSE values across differently scaled scores as though smaller were
better. Use `R²` as the principal cross-target metric and, if needed, a clearly
defined normalized error metric. Raw MSE may still be shown within one target.

### Part B: Match the high-N target to the low-N target

Implement the user's proposed control rigorously:

- retain the high-availability target;
- repeatedly subsample its training data to the lower target's usable `N` (or a
  defensible matched training size after holding out evaluation data);
- use many deterministic repetitions, not one lucky random sample;
- keep target, feature recipe, preprocessing, evaluation set/folds, and metric
  definitions constant;
- show the distribution of held-out `R²` rather than a single value;
- mark the full-N high-target performance and the lower-target performance,
  while reminding students that target differences remain.

Use enough repetitions for a stable teaching figure without making notebook or
CI execution excessive. Precompute/cache a deterministic source artifact if
appropriate.

### Part C: Same-target learning curve

Make this the cleanest demonstration of sample size:

- use the same high-availability target and compact feature set;
- hold evaluation data constant where methodologically appropriate;
- train on several increasing sample sizes supported by the actual data;
- repeat sampling at each size;
- plot mean/distribution of held-out `R²` with variability;
- choose the smallest training size safely above the model's feature count and
  report the `n/p` relationship.

The conclusion should focus on performance stability and uncertainty, not claim
that performance must increase monotonically in every random draw.

Keep this section compact: one availability display, one matched-N distribution,
one learning-curve figure, and a short interpretation card. Do not turn it into
a missing-data lecture or a formal learning-curve theory chapter.

## 10. Questions and final synthesis

Use a small number of purposeful questions, placed before results where
possible. The completed linear portion should ask students to reason about:

- outcome versus features;
- why fitting and evaluating on the same observations inflates performance;
- training versus held-out performance;
- feature-set comparison and feature count;
- negative test `R²`;
- why different-target performance does not isolate sample size;
- what the learning curve does and does not show.

Some questions may have **Check your reasoning** dropdowns; leave suitable
discussion questions open. End with a concise synthesis, not a long recap.

Do not create KNN or bias–variance headings/content in this WP beyond one short
forward-looking sentence if needed for flow.

## 11. Portable notebook and future reuse

Create a generated portable notebook at:

`book/downloads/chapter_02/exercise_02_portable.ipynb`

Extend/refactor the existing portable generator into a reusable multi-notebook
mechanism while preserving Exercise I's output byte-for-byte unless a strictly
necessary shared metadata change is documented and tested. Maintain backward
compatibility with existing CI commands or update all callers atomically.

Exercise II portable requirements:

- banner names Machine Learning for Neuroscience;
- optional commented install cell contains only actual lesson packages, likely
  `numpy pandas matplotlib seaborn scikit-learn` after import audit;
- no instruction to install from the repository/`requirements.txt`;
- no local relative runtime data/config dependency;
- immutable public data source works outside the clone;
- core Python regression workflow, evaluation comparison, and sample-size code
  are visible and runnable;
- embedded browser comparison becomes a normal HTTPS link to the published
  Exercise II page;
- no MyST directives, iframes, hide tags, Node requirements, credentials, or
  active automatic install command;
- deterministic `--write`/`--check` and out-of-repo smoke execution;
- no false claim that private GitHub source will remain accessible to all
  students. Carry the existing distribution warning into the report without
  changing hosting in WP11.

The Chapter 2 Colab/raw controls should use the final `main` paths, not the
temporary feature branch. They are expected not to resolve remotely until a
later merge/deployment WP.

## 12. Reproducibility and methodological tests

In addition to existing suites, add targeted tests that verify:

1. source checksum/provenance and parsed feature taxonomy;
2. target counts and target/brain-feature separation;
3. no target, phenotype, identifier, diagnosis, site, age, or sex leakage in `X`;
4. deterministic/disjoint train-test indices;
5. preprocessing is learned only from training rows/folds;
6. correct `R²` and MSE recomputed independently from stored predictions;
7. training/test/leakage table uses the intended fit/evaluation rows and labels
   the invalid case unmistakably;
8. invalid model object/result never enters later comparison/sample-size data;
9. literature/anatomical bundle mapping is valid for the audited atlas and
   fixed independently of outcome performance;
10. every interactive catalog model uses the same cohort/folds;
11. no unsupported `p >= n_train` OLS configuration is offered;
12. matched-N repetitions and learning-curve samples are deterministic and
    correctly nested/independent according to the documented design;
13. browser artifact contains no participant identifiers;
14. observed-versus-predicted plot data align with metrics;
15. navigation, portable links, generator staleness, and out-of-repo execution;
16. Exercise I and its four existing activities remain unchanged and green;
17. clean build, no `*.err.log`, no new warnings, responsive desktop/390 px.

Run the entire WP10 baseline after implementation. Visually inspect the new
notebook opening, wide-table preview, evaluation comparison, feature-comparison
activity, sample-size figures, and portable notebook.

## 13. Exact report and stop

Create:

- `WPs/reports/WP11_REPORT.md`
- `WPs/reports/WP11_EXACT_CHANGELOG.md`

The report must include:

- success/failure for every section and required test;
- branch, checkpoint/tag, implementation commit, and report commit;
- exact data source/version/checksum, ABIDE generation, atlas, table shape,
  brain-feature taxonomy, measurement types, ROI count, and site/diagnosis
  composition;
- target availability audit and rationale for main/lower-N targets;
- exact train/test/CV protocol, preprocessing, seeds, cohort, `n`, `p`, and
  metric definitions;
- actual correct-test, training-resubstitution, and invalid-test-fit results;
- exact literature-based bundle definitions and citations;
- every interactive catalog configuration/default and actual model metrics;
- matched-N and learning-curve design/results;
- all notebook cells/pages/configs/artifacts/scripts/tests added or changed;
- canonical/portable cell and visibility counts;
- full test counts, build warnings, deviations, unresolved risks, and items
  requiring Yoav;
- explicit confirmation that no KNN/full bias–variance content, merge,
  deployment, push, hosting change, destructive git command, or generated build
  output commit occurred.

`WP11_EXACT_CHANGELOG.md` should make the work reviewable without diffing raw
notebook JSON and record stable cell IDs plus artifact schemas/paths.

Commit implementation separately, then commit the report pair with:

```text
WP11 report: document Exercise II linear regression
```

Stop after the report commit on `feature/regression-practice`. Do not begin the
KNN or bias–variance WP.

