# WP17 — Exercise 4: Classification with Logistic Regression

## Purpose

Create the fourth tutoring notebook for **Machine Learning for Neuroscience**:

> **Exercise 4: Classification with Logistic Regression**

This exercise follows the lecture and tutor presentation. It should be a concise practice notebook—not a comprehensive classification textbook. It must reuse the project's ABIDE neuroimaging data and established design, portable-notebook, interactive-widget, testing, and Jupyter Book conventions.

The notebook should teach students how to build and honestly evaluate one binary classifier for autism diagnosis, understand a confusion matrix, accuracy, ROC/AUC, decision thresholds, class imbalance, and stratified train/test splitting.

This WP is **local implementation and validation only**. Do not push, deploy, start a GitHub Actions workflow, or begin WP18.

---

## 0. Bounded execution contract — mandatory

These rules override any broader testing/reporting habits from earlier WPs.

1. Work in a **fresh Claude Code session**.
2. Record the start time. Hard-stop this WP after **3 hours of active work**. If it is incomplete at that point, leave the repository safe and write a partial failure/blocker report.
3. Do not use `ScheduleWakeup`, background workflow watchers, repeated polling, or placeholder commands such as `echo waiting`.
4. Do not run any command silently for more than 15 minutes. Interrupt it, record the problem, and continue only with a targeted alternative.
5. Run targeted tests while developing. Run each broad/full validation suite no more than **once after the implementation is stable**.
6. A failed test may be rerun once in isolation to distinguish a reproducible failure from a flake. Do not repeatedly rerun until green.
7. Make at most two implementation attempts for the same failure. If it still fails, stop and report the blocker.
8. Do not run unrelated data/model audits for Exercises 1–3 unless a shared file changed and a specific dependency requires them.
9. Build the Jupyter Book once after implementation. A second build is allowed only after an actual fix to a build failure.
10. Do not create or commit screenshots, videos, temporary Playwright configurations, generated caches, `.DS_Store`, virtual environments, or Jupyter build artifacts unless those artifacts are already intentionally tracked by this repository's established workflow.
11. Do not update a report merely to record the SHA of the commit containing that same report. Reports must not create a self-referential commit loop.
12. **No remote operations:** do not `git push`, deploy GitHub Pages, or monitor GitHub Actions in WP17.
13. End after producing the two WP17 reports. Do not start another WP.

---

## 1. Protect and inspect the starting state

Before editing:

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
git log --oneline --decorate -8
```

Expected starting point from WP16:

```text
a57fefc01fa63e67805afb3db64b74507b36133f
```

Rules:

- Confirm that the current repository is `ml-neuro-tutorials`.
- Confirm that local `main` and `origin/main` are consistent, or clearly document any newer intentional commits.
- If the working tree contains unexpected edits or untracked project files, stop and report them. Do not discard, overwrite, stash, reset, or absorb unknown work.
- If clean, create an annotated local safety tag at the actual starting SHA:

```bash
git tag -a wp17-start -m "Checkpoint before WP17 classification notebook"
```

- If `wp17-start` already exists, inspect it. Do not move or overwrite it without explicit approval.
- Create and work on:

```bash
git switch -c feature/exercise-04-classification
```

- Save this WP verbatim under the repository's established `WPs/` convention before implementation. Commit it as the first checkpoint commit.

Inspect, but do not redesign, the relevant conventions established by Exercises 1–3:

- canonical notebook and chapter layout;
- `_toc.yml` and Contents-page entries;
- green **Run or download this notebook** block;
- blue **Think first** boxes and revealable answers;
- Colab/download links and portable-notebook generation;
- ABIDE modeling configuration and 360-ROI feature selection;
- shared Plotly policy and dynamic iframe resizing added in WP16;
- interactive TypeScript component registration, data exports, tests, accessibility, and responsive layout.

Do not copy obsolete wording or inconsistent styles that later WPs already corrected.

---

## 2. Data and modeling audit — before writing the lesson

Audit the actual prepared ABIDE table and current modeling configuration. Record the following in the final report:

- diagnosis column name and exact coding;
- number of usable autistic and control participants;
- confirmation that each row is one participant;
- exact 360 neuroimaging feature columns reused from Exercises 2–3;
- missingness in those features;
- whether any duplicate participant IDs exist;
- class balance before splitting.

Modeling requirements:

- Positive class: **autistic participant**.
- Negative class: **control participant**.
- Predictors: the same 360 neuroimaging ROI features used by the current regression exercises.
- Do **not** include diagnosis-derived fields, participant ID, age, sex, acquisition site, behavioral scores, or other phenotypes as predictors.
- Do not select ROIs, a split seed, or a model configuration because it produces an attractive test result.
- Use one project-standard deterministic random seed chosen before inspecting test performance.
- Use a participant-level held-out test set, normally 25%, with `stratify=y`.
- Fit every learned preprocessing step on training data only.
- Use median imputation only if the ROI features require it, followed by `StandardScaler` and L2-regularized `LogisticRegression` with a sufficient `max_iter`.
- Use a fixed, ordinary regularization setting such as `C=1.0`; do not tune it on the test set.
- Report the result honestly even if discrimination is modest.
- Explicitly state that a random participant split estimates generalization to new participants drawn from the represented sites; it is not evidence of generalization to a completely unseen acquisition site.

Add automated checks for target leakage, exact feature count, split disjointness, train-only preprocessing, reproducibility, and metric consistency.

---

## 3. Notebook scope and teaching structure

Create the canonical Exercise 4 notebook using the repository's actual naming/path conventions. Add it to the Jupyter Book table of contents, sidebar, Contents page, and relevant launch/download machinery.

Use the exact title style:

> **Exercise 4: Classification with Logistic Regression**

Keep it shorter than Exercise 1. Aim for approximately **35–45 minutes of guided practice**, excluding optional experimentation. Avoid repeating the general course introduction already present elsewhere.

### 3.1 What this notebook covers

Include a short opening list:

- predicting a categorical outcome;
- logistic-regression probabilities and class decisions;
- honest held-out evaluation;
- confusion matrices, accuracy, ROC curves, and AUC;
- class imbalance and stratified splitting.

Use the same green Run/download block as the other current exercises. Colab and downloaded notebook links must point to Exercise 4, not an older notebook.

The portable/Colab notebook must include the project's established optional package-installation cell and must not require access to a private repository at runtime.

### 3.2 Load the ABIDE classification data

Briefly explain that ABIDE's central scientific distinction is autism diagnosis, whereas the previous exercises used the same rich dataset to ask a regression question about age.

Show only:

- dimensions of the classification table;
- class counts;
- a compact sample with participant ID, diagnosis, and a few representative ROI columns;
- a concise missingness statement.

Do not repeat the EDA chapter.

Add a blue Think first question asking what one row and the target represent.

### 3.3 From a linear score to a probability

Introduce only the minimum theory needed:

\[
P(Y=1\mid X)=\frac{1}{1+e^{-z}}
\]

Explain in plain language:

1. Logistic regression calculates a weighted linear score.
2. The sigmoid transforms it to a probability between 0 and 1.
3. A decision threshold, commonly 0.50, converts the probability into a predicted class.

Include a small, clean sigmoid figure or concise code example. Do not derive the loss function or maximum-likelihood estimator.

Think first:

> If two participants receive autism probabilities of 0.48 and 0.52, must their underlying model evidence be very different merely because their predicted labels differ?

Provide a concise revealable answer.

### 3.4 One honest logistic-regression model

Show readable Python code for:

1. defining `X` and binary `y`;
2. a stratified train/test split;
3. train-only imputation/scaling;
4. fitting logistic regression;
5. obtaining `predict()` labels and `predict_proba()` probabilities on the test set.

Use the project's established progression for scaling: if pedagogically helpful, show the explicit `fit`/`transform` steps first and then place the equivalent pipeline version in a collapsed code block. Do not let preprocessing fit on the complete dataset.

Do not repeat the invalid train-on-test or resubstitution demonstrations from Exercises 2–3. Include only one brief reminder that all reported metrics use participants excluded from fitting.

### 3.5 Classification outcomes and metrics

Display a confusion matrix whose axes state unambiguously:

- rows: actual diagnosis;
- columns: predicted diagnosis.

Use autism as the positive class. Explain all four cells in the ABIDE context:

| Outcome | Interpretation |
|---|---|
| True negative | A control participant is classified as control. |
| False positive | A control participant is classified as autistic. |
| False negative | An autistic participant is classified as control. |
| True positive | An autistic participant is classified as autistic. |

Introduce accuracy:

\[
\mathrm{Accuracy}=\frac{TP+TN}{TP+TN+FP+FN}
\]

Then concisely introduce:

- sensitivity/recall as the proportion of autistic participants detected;
- specificity as the proportion of controls correctly identified;
- the ROC curve as sensitivity versus false-positive rate while the threshold changes;
- AUC as threshold-independent ranking performance, where 0.5 is chance-level ranking and 1.0 is perfect ranking.

Show the honest test-set confusion matrix, accuracy, ROC curve, and AUC. Avoid a broad catalogue of classification metrics.

Add one Think first question asking why `predict_proba()` rather than `predict()` is needed for ROC/AUC.

---

## 4. Interactive activity A — decision threshold

Build one direct-in-browser interactive activity consistent with the existing TypeScript/Plotly architecture.

Use the fixed honest test-set predicted probabilities. Do not refit the model when the threshold changes.

Controls:

- probability-threshold slider, approximately 0.05–0.95;
- synchronized numeric input for precise values;
- reset-to-0.50 control.

Update together:

- confusion matrix;
- accuracy;
- sensitivity;
- specificity;
- number or percentage predicted autistic;
- ROC curve with a clearly labelled point corresponding to the selected threshold.

Requirements:

- Explain that threshold changes labels and the confusion matrix but does not change the fitted model or its AUC.
- The ROC diagonal must have a legend such as **Chance-level ranking**.
- Make all axis titles and legends visible at desktop and narrow widths.
- Reuse WP16's shared Plotly policy: white/theme-matching backgrounds, no modebar, fixed axes, hover preserved, automargins, and dynamic iframe height.
- Provide accessible labels and keyboard-operable controls.
- Avoid a visually dense multi-panel dashboard; prefer one confusion-matrix panel, one ROC panel, and compact metric cards.

Think first:

> If failing to identify an autistic participant were considered more costly than falsely flagging a control, would you generally lower or raise the decision threshold?

Provide a revealable answer after the activity.

For the portable/Colab notebook, supply ordinary editable Python code with a clearly marked `threshold = 0.50` line that students can change and rerun. Do not require the browser widget bundle or `ipywidgets`.

---

## 5. Interactive activity B — class imbalance and stratified splitting

Build a second concise browser activity using real ABIDE participants resampled into the following class ratios, with **control as the majority class**:

- 50:50
- 60:40
- 70:30
- 80:20
- 90:10
- 95:5

Important terminology throughout the notebook and interface:

> Compare a **stratified split** with an **unstratified split**. Do not call either classifier a “stratified model.”

Before implementation, determine a fixed total cohort size supported by the available class counts. It should make the 95:5 case meaningfully sparse while retaining enough minority observations for a stratified test set whenever mathematically possible. Document the chosen size and reasoning in the report, not at length in the student notebook.

Controls:

- class-ratio selector;
- a small selector for three to five predetermined split seeds.

For the selected resampled cohort, compare side by side:

1. `train_test_split(..., stratify=y)`;
2. the same split configuration without `stratify`.

Show prominently:

- full-cohort class counts;
- training and test class counts for each split;
- confusion matrix for each held-out test set;
- accuracy and AUC for each split;
- a majority-class baseline accuracy.

If a test partition has only one class, display AUC as **undefined: both classes are required** rather than crashing or substituting a number.

Implementation and interpretation requirements:

- Use the same preprocessing/model specification for both sides.
- Do not suggest that stratification inherently improves the classifier.
- Explain that stratification preserves approximate class proportions and makes evaluation more reliable.
- Explain that it does not create minority observations, guarantee good sensitivity, or correct a model's learning objective.
- At 95:5, make clear that a classifier predicting every participant as control could achieve 95% accuracy while detecting no autistic participants.
- Because individual splits are stochastic, frame metric differences as examples of split stability—not proof that one single stratified split must always score higher.
- Keep the activity responsive and readable. Reuse the shared Plotly and iframe policies.

Think first:

> At a 95:5 class balance, what accuracy would a classifier achieve by predicting “control” for everyone? What important information would that accuracy conceal?

Provide a concise revealable answer.

For the portable/Colab notebook, provide editable Python code with obvious `class_ratio` and `random_state` variables. Show its output when the canonical notebook is executed. Do not depend on the website's TypeScript widget.

---

## 6. Closing section

End with a short **Takeaways** section:

- Logistic regression outputs probabilities before class labels.
- Honest evaluation uses participants excluded from fitting.
- A confusion matrix identifies the kinds of correct and incorrect decisions.
- Accuracy can be misleading under class imbalance.
- ROC/AUC evaluates ranking across thresholds.
- Stratification protects class composition across a split but does not eliminate imbalance.

Add exactly three short exam-like review questions with revealable answers:

1. Why can 95% accuracy describe a useless classifier?
2. What generally happens to false negatives when the decision threshold is lowered?
3. What problem does stratification solve, and what problem does it not solve?

Do not add a time budget to the student-facing notebook.

---

## 7. Explicit exclusions

Do not expand this exercise into the following topics:

- derivation of logistic loss or maximum likelihood;
- multiclass classification;
- hyperparameter searches;
- selecting features or seeds for the best test result;
- SMOTE or synthetic oversampling;
- detailed class weighting;
- probability calibration;
- precision–recall curves unless required to correct a genuine pedagogical problem;
- site-held-out or nested cross-validation;
- model interpretation or coefficient maps;
- repetition of the train/test-invalidity demonstrations from earlier exercises.

If one of these becomes technically necessary, stop and ask rather than silently expanding scope.

---

## 8. Implementation requirements

Follow the existing architecture rather than creating a parallel system.

- Reuse the current ABIDE source and modeling configuration.
- Extend existing generation/export scripts cleanly; do not hand-edit generated artifacts.
- Add deterministic data/model audit output for Exercise 4.
- Keep browser payloads compact. Do not embed the complete source dataset if only probabilities, labels, counts, and precomputed imbalance results are needed.
- Do not duplicate Plotly layout/config code; use the shared policy from WP16.
- Reuse the dynamic iframe-height mechanism.
- Keep all user-facing text professional and concise.
- Ensure the activity works on GitHub Pages without a Python kernel or server.
- Ensure the canonical notebook builds without executing network downloads.
- Ensure the portable/Colab notebook uses ordinary Python and locally bundled or stable public data access consistent with the existing portable notebooks.
- If adding Exercise 4 reveals scripts that hard-code “three notebooks,” generalize them safely and add tests rather than creating a one-off bypass.

---

## 9. Required tests — bounded

During development, run only focused tests for the files being changed.

After implementation is stable, run this final gate once:

1. Exercise 4 data/model audit and its targeted Python tests.
2. Portable Exercise 4 generation/check and one smoke execution.
3. Frontend typecheck.
4. Frontend unit tests, including new metric and state-transition tests.
5. Frontend production build.
6. Jupyter Book build once.
7. Exercise 4 built-book Playwright tests with `--workers=1`.
8. Existing shared-widget tests once only if shared widget infrastructure changed.

Required automated assertions include:

- exactly 360 approved ROI predictors and no forbidden phenotype/ID columns;
- train/test participant disjointness;
- reproducible split and metrics;
- confusion-matrix orientation and TP/TN/FP/FN values;
- accuracy and AUC match trusted Python calculations;
- AUC remains constant while threshold changes;
- threshold changes alter predicted labels and confusion-matrix values;
- slider, numeric input, and reset stay synchronized;
- class-ratio and seed controls update real data, not labels alone;
- stratified counts preserve the selected proportion as closely as integer counts permit;
- undefined AUC is handled explicitly for a one-class test partition;
- majority-baseline accuracy is correct;
- iframe content is not clipped at normal desktop and narrow widths;
- Plotly backgrounds, axes, hover, modebar, legends, and spacing follow WP16 policy;
- browser refresh restores documented defaults;
- portable notebook runs without the TypeScript widgets.

If a broad suite fails for an unrelated pre-existing reason, record evidence that it is pre-existing and do not repair unrelated systems in this WP.

---

## 10. Local integration and stopping point

After the final gate passes:

1. Commit the implementation on `feature/exercise-04-classification`.
2. Switch to local `main`.
3. Merge with `--no-ff`.
4. Perform only a short post-merge smoke check: repository status, Exercise 4 build artifact exists, and the relevant Exercise 4 page opens locally. Do not repeat the full gate after a conflict-free merge.
5. Create the reports below and commit them once on local `main`.
6. Confirm the working tree is clean.
7. Stop. **Do not push or deploy.**

If the merge has conflicts, stop and report them instead of guessing.

---

## 11. Required reports

Create exactly:

- `WPs/reports/WP17_REPORT.md`
- `WPs/reports/WP17_EXACT_CHANGELOG.md`

Do not create numbered duplicates such as `(1)` or `(2)`.

`WP17_REPORT.md` must begin with a short plain-language status:

- `SUCCESS — implemented and validated locally`, or
- `PARTIAL/FAILED — not ready`, followed immediately by the blocker.

Include:

- start SHA/tag and final local SHA;
- branch and merge status;
- data audit results and exact diagnosis coding;
- exact feature definition;
- model/split/preprocessing specification;
- honest held-out confusion matrix, accuracy, and AUC;
- imbalance cohort size and why it was selected;
- notebook and interactive content delivered;
- tests run once, with pass/fail counts and elapsed time;
- any failed/flaky test and whether its single permitted rerun passed;
- deviations from this WP;
- issues requiring Yoav's attention;
- exact terminal commands for Yoav to build and test Exercise 4 locally;
- explicit statement: `No push or deployment was performed in WP17.`

`WP17_EXACT_CHANGELOG.md` must list:

- every created, modified, renamed, or deleted file;
- concise purpose of each change;
- commits created;
- generated artifacts and whether they are intentionally tracked;
- confirmation that no screenshots or temporary files were committed.

Do not update either report after committing merely to insert its own commit SHA. Put the final report-commit SHA only in Claude's terminal response.

---

## 12. Final response to Yoav

Return a concise summary—do not paste the full reports. State:

1. success, partial completion, or failure;
2. what Exercise 4 now contains;
3. honest test-set accuracy and AUC;
4. local `main` SHA and whether the tree is clean;
5. the most important test results;
6. anything requiring Yoav's decision or attention;
7. the two report paths;
8. the local URL/path Yoav should use after running the provided build command;
9. confirmation that nothing was pushed or deployed and that WP18 was not started.

Then stop.
