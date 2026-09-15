# WP18 — Revise Exercise 4 and create the notebook overview document

## Purpose

Revise **Exercise 4: Classification with Logistic Regression** following Yoav's review, then create a polished Word overview of Exercises 1–4.

This WP is **local-only**. Do not push, deploy, monitor GitHub Actions, or begin WP19.

Required Exercise 4 changes:

1. Replace the stratified-versus-unstratified interactive activity with a focused class-imbalance activity comparing model accuracy with the changing majority-class baseline.
2. Put `TN`, `FP`, `FN`, and `TP` directly beside the values in the notebook's displayed confusion-matrix cells.
3. Remove the unwanted gray expandable estimator/scaler representation after the explicit-scaling cell.
4. Select logistic-regression `C` honestly using training-only cross-validation, analogous to the honest selection of `k` in Exercise 3.
5. Create a Word document summarizing Exercises 1–4 by exercise number, subject, and covered material.

---

## 0. Bounded execution contract — mandatory

1. Use a fresh Claude Code session and read this WP fully before acting.
2. Hard-stop after **2 hours of active work**. If incomplete, leave the repository safe and write a partial report.
3. Do not use scheduled wakeups, background watchers, repeated polling, or placeholder waiting commands.
4. Interrupt any command that produces no result for 15 minutes.
5. Run focused tests during development and one final relevant gate. Do not repeatedly rerun full suites.
6. A failed test may be rerun once in isolation. Make at most two fixes for the same failure, then stop and report it.
7. Build the interactive application once after the code stabilizes and the Jupyter Book once after notebook generation. Rebuild only after a genuine failure-related fix.
8. Do not create or commit screenshots, videos, caches, temporary browser configurations, Jupyter build output, `.DS_Store`, or virtual environments.
9. Use explicit file paths with `git add`; never use `git add .`, `git add -A`, or another broad staging command.
10. Do not create a report-update/push/deploy loop. There are no remote operations in this WP.
11. End after the WP18 reports. Do not begin another WP.

---

## 1. Protect and inspect the starting state

Run:

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
git log --oneline --decorate -10
git tag -l 'wp18-start'
```

Expected state:

- local `main` contains the completed WP17 implementation and report commit;
- local `main` is ahead of `origin/main`, because WP17 was deliberately not pushed;
- `WPs/reports/WP16_ARCHITECT_REPORT.md` remains an acknowledged, pre-existing untracked file.

The old WP16 architect report is explicitly whitelisted: do not modify, delete, move, inspect further, or stage it. Its presence must not block WP18.

If any other unexpected modification or untracked project file exists, stop and report it. Do not discard, stash, reset, or absorb it.

At the actual clean/accepted starting commit:

```bash
git tag -a wp18-start -m "Checkpoint before WP18 Exercise 4 revisions"
git switch -c revise/exercise-04-classification
```

If the tag or branch already exists, inspect rather than overwrite it.

Save this WP verbatim under the established `WPs/` path and make one checkpoint commit containing only that file.

---

## 2. Honest hyperparameter selection for logistic-regression C

Revise Section 3, **One honest logistic-regression model**.

### 2.1 Required procedure

Keep the existing fixed outer participant split:

- 25% held-out test set;
- `random_state=42`;
- diagnosis-stratified split;
- the test set untouched until the final model has been selected and fitted.

Select `C` using only the outer training partition:

- put `StandardScaler` and `LogisticRegression` inside one scikit-learn `Pipeline`;
- use `GridSearchCV` with a predetermined logarithmic grid, preferably
  `np.logspace(-4, 4, 9)` unless an established project convention requires a different fixed grid;
- use five-fold cross-validation on the training partition;
- use deterministic shuffled folds with `random_state=42`;
- preserve class proportions within the CV folds using `StratifiedKFold` as an implementation detail;
- select `C` using ROC AUC, not held-out test accuracy;
- use no test-set result to adjust the grid, folds, feature set, seed, or scoring rule;
- refit the selected pipeline on the complete outer training partition;
- evaluate exactly once on the untouched outer test partition.

Do not promise that tuning improves held-out performance. Explain:

> Cross-validation selects the value that performed best within the training data. It may improve generalization, but it does not guarantee a better score on one particular held-out test set.

### 2.2 Student-facing presentation

Make the sequence parallel the “choosing `k` honestly” presentation in Exercise 3:

1. Split into training and test data.
2. Compare candidate `C` values using cross-validation within the training set.
3. Select the best `C` without looking at the test labels.
4. Fit the selected pipeline to all training participants.
5. Evaluate once on the test participants.

Include a compact cross-validation results table or small plot of mean CV AUC against `C` on a logarithmic x-axis. Mark the selected `C`. Keep this compact; do not turn the section into a general hyperparameter-tuning lecture.

Add a short explanation of `C`:

- smaller `C` means stronger regularization and a more constrained model;
- larger `C` means weaker regularization and greater flexibility.

One concise Think first question is enough:

> Why must the held-out test participants remain outside the process used to select `C`?

Provide a revealable answer.

### 2.3 Explicit scaling and pipeline display

Preserve the pedagogical explicit-scaling example showing that `fit_transform` learns scaling parameters from the training columns and `transform` applies those parameters to the test columns.

Immediately after this cell, remove the unwanted gray expandable representation of the scaler, pipeline, or estimator:

- the cell must not end with a bare estimator/scaler object;
- end assignments with a semicolon where appropriate;
- clear any stored rich `text/html` or `text/plain` estimator output from the canonical notebook;
- verify the built HTML has no estimator parameter table at this location.

Show the pipeline as readable code in the existing collapsed-code style, not as scikit-learn's rich estimator diagram.

### 2.4 Audit and downstream consistency

Update the classification audit, committed result, threshold exporter, notebook outputs, portable notebook, text, and tests to use the honestly selected `C`.

The decision-threshold activity must use probabilities from the final tuned model. AUC must remain constant as the threshold changes.

Record in the report:

- candidate grid;
- fold specification and scoring metric;
- selected `C`;
- best mean training-CV AUC;
- final untouched-test confusion matrix, accuracy, sensitivity, specificity, and AUC;
- comparison with WP17's fixed-`C=1` test accuracy `0.546` and AUC `0.569`, explicitly noting that the test set was not used for selection.

If the selected model performs no better on the test set, keep it and explain the honest result. Do not change the method after seeing the outcome.

---

## 3. Static confusion-matrix cell labels

In Section 4, **Classification outcomes and metrics**, revise the displayed pandas confusion matrix created near `display(cm_table)`.

Every numeric cell must include its outcome abbreviation directly beside the value, for example:

- `TN = 75`
- `FP = 60`
- `FN = 54`
- `TP = 62`

Keep the axes unambiguous:

- rows: actual diagnosis;
- columns: predicted diagnosis;
- control first, autism second;
- autism is the positive class.

Use a compact, readable pandas `DataFrame`/`Styler`. Do not add another figure. Ensure the same labelled cells appear in the canonical and portable notebooks after execution.

If either browser activity displays a confusion-matrix table, confirm its cells already show `TN`/`FP`/`FN`/`TP`; make it consistent if they do not.

---

## 4. Replace Activity 6 with a focused class-imbalance activity

Replace the current **Interactive activity: class imbalance and stratified splitting** with:

> **Interactive activity: class imbalance and misleading accuracy**

Remove from student-facing Exercise 4:

- the stratified-versus-unstratified comparison;
- paired split panels;
- split-kind language;
- questions specifically asking what stratification solves;
- discussion of one-class test partitions or undefined AUC;
- any suggestion that the lesson is comparing a “stratified model” with another model.

The honest main model may retain one concise sentence explaining why its train/test split preserves diagnosis proportions. Do not make stratification a separate learning objective or review question.

### 4.1 Interactive controls

Retain these class ratios, with control as the majority class:

- 50:50
- 60:40
- 70:30
- 80:20
- 90:10
- 95:5

Retain a small selector for predetermined random seeds if it helps students observe sampling variability without clutter. Use a stratified split internally so the displayed test partition represents the selected ratio, but present this only as an implementation detail—not the lesson's comparison.

Use real ABIDE participants and a fixed supported cohort size. Preserve the existing N=400 design unless the revised audit reveals a concrete mathematical or data-validity problem.

### 4.2 Required display

For each selected ratio, show one clear comparison plot:

- **Logistic-regression test accuracy**;
- **majority-class baseline accuracy**.

The majority baseline must be recalculated from the displayed test partition for every ratio. Do not hard-code the label text alone.

Prefer a simple two-bar chart with:

- y-axis from 0 to 1 or 0% to 100%;
- values printed above the bars;
- a title that includes the selected class ratio;
- responsive sizing and the shared WP16 Plotly policy;
- no modebar, fixed axes, hover preserved, white/theme-matching background, automargins, and no clipping.

Below or beside the plot, show compact model metrics:

- AUC;
- balanced accuracy;
- sensitivity;
- specificity;
- test-set class counts.

Do not create a large metric dashboard or multiple redundant plots.

### 4.3 Teaching text and questions

The surrounding explanation must establish:

- as imbalance increases, predicting only the majority class produces increasingly high accuracy;
- a high accuracy can therefore coexist with complete failure to identify autistic participants;
- the model should be compared with an appropriate baseline;
- the confusion matrix, sensitivity, specificity, balanced accuracy, and AUC reveal information concealed by accuracy;
- no single metric is universally sufficient—the relevant errors depend on the scientific or clinical question.

Use no more than two questions:

1. Before changing to 95:5, ask students to predict the majority baseline accuracy.
2. Ask which displayed measures reveal that a high-accuracy classifier is failing on the minority class.

Provide concise revealable answers. Remove the previous final review question about what stratification solves and replace it with an accuracy/imbalance question.

### 4.4 Modeling consistency

To isolate the effect of class balance:

- use the same 360 ROI predictors;
- use the same preprocessing steps;
- use the `C` selected honestly in Section 3 as a fixed setting throughout the imbalance activity;
- do not tune a separate `C` after viewing each ratio's test result;
- keep resampling and split seeds deterministic;
- preserve train/test separation for every ratio;
- compute all displayed metrics from the selected real-data test partition.

Simplify or regenerate the imbalance artifact and frontend data schema so obsolete `stratified`/`unstratified` duplicated results are not retained merely for compatibility. Keep browser payloads compact.

### 4.5 Portable/Colab equivalent

Replace the old stratification-comparison code with an ordinary editable Python example containing obvious variables such as:

```python
class_ratio = "90:10"
random_state = 42
```

The code must:

- create the selected real-data ratio;
- split it reproducibly;
- fit the same fixed tuned model using training data only;
- calculate model accuracy and majority-baseline accuracy;
- plot the two accuracies;
- print AUC, balanced accuracy, sensitivity, specificity, and test class counts.

Execute and save a representative output. Do not require TypeScript or `ipywidgets`.

---

## 5. Revise opening, coverage, and closing text

Update all Exercise 4 descriptions so they match the revised content:

- include training-only cross-validation for selecting `C`;
- retain logistic probabilities, honest evaluation, confusion matrix, accuracy, ROC/AUC, and decision thresholds;
- describe the second activity as class imbalance and misleading accuracy;
- remove stratified-versus-unstratified splitting as a stated learning topic;
- remove all student questions specifically about stratification.

The Takeaways should remain concise and include:

- selecting `C` inside the training set protects the held-out evaluation;
- accuracy should be interpreted relative to class balance and a baseline;
- confusion-matrix-derived measures and AUC can reveal failures hidden by accuracy.

Maintain exactly three final exam-like review questions, revised to cover:

1. test-set isolation during `C` selection;
2. threshold changes and false negatives;
3. misleading accuracy under class imbalance and a better set of measures to inspect.

Do not add a time budget.

---

## 6. Create the Word overview document

After the notebook revisions are complete, create:

```text
course_overview/Machine_Learning_for_Neuroscience_Notebook_Overview.docx
```

The document should be a polished, easily editable Word document titled:

> **Machine Learning for Neuroscience — Practice Notebook Overview**

Include a short introductory sentence explaining that it summarizes the practice notebooks currently developed for the course.

Use a landscape page and a readable 12-point font. Create a three-column table:

| Exercise | Subject | Covered materials |
|---|---|---|

Include Exercises 1–4 only. Inspect the current notebooks rather than relying solely on old WP descriptions. Summarize the material accurately and concisely:

- **Exercise 1 — Exploratory Data Analysis (EDA):** ABIDE phenotypic data; initial inspection using `head`, `tail`, and `sample`; data types and categorical variables; summary statistics; missing values; distributions; correlations; relevant browser activities.
- **Exercise 2 — Linear Regression:** ABIDE neuroimaging ROI data; age prediction; scaling; train/test separation; multivariable linear regression; R² and MSE; honest versus invalid evaluation; sample-size effects; relevant browser activities.
- **Exercise 3 — KNN Regression and the Bias–Variance Trade-off:** KNN age prediction; scaling; training-only cross-validation for `k`; honest versus invalid evaluation; effect of `k`; model complexity, bias, variance, and training-sample variability; relevant browser activities.
- **Exercise 4 — Classification with Logistic Regression:** ABIDE autism classification; logistic probabilities; training-only cross-validation for `C`; confusion matrix and its four outcomes; accuracy, sensitivity, specificity, balanced accuracy, ROC/AUC; decision thresholds; class imbalance and majority baselines; relevant browser activities.

The examples above define the expected coverage but must be reconciled with the actual final notebooks. Do not claim content that is absent.

Formatting requirements:

- clear header row with subtle course-consistent blue styling;
- adequate column widths, with the Covered materials column widest;
- vertically aligned cells;
- concise semicolon-separated phrases or bullets within each Covered materials cell;
- no tiny text, clipped content, or unnecessary decorative graphics;
- document metadata/title set where practical.

Use `python-docx` if available. If it is unavailable, do not modify student runtime requirements merely for this administrative document. Either use an already available document-generation route or stop and report the dependency blocker.

Validate the `.docx` by reopening it programmatically and confirming:

- one non-empty title;
- one table;
- three columns;
- one header row plus four exercise rows;
- all required exercise numbers and subjects are present;
- the ZIP/docx structure is valid.

If LibreOffice is already installed, optionally render once to PDF for visual inspection, but do not install it and do not commit the PDF. Do not let document rendering delay the WP.

---

## 7. Required focused tests

Update tests to match the revised lesson rather than weakening or deleting meaningful assertions.

Required checks:

### Modeling and notebook

- the outer test set remains untouched during `C` selection;
- scaler and logistic regression are inside the cross-validation pipeline;
- candidate grid and fold definition are deterministic;
- selected `C` matches the committed CV results;
- final confusion matrix and all metrics match trusted Python calculations;
- threshold artifact uses the tuned model's fixed test probabilities;
- notebook contains no rich estimator/scaler representation after the explicit-scaling cell;
- the static confusion matrix contains all four abbreviations beside their values;
- canonical and portable notebook content/outputs agree.

### Imbalance activity

- every ratio and seed maps to actual computed data;
- the two plotted accuracies equal trusted Python calculations;
- majority-baseline accuracy changes with the class ratio;
- AUC, balanced accuracy, sensitivity, specificity, and counts are correct;
- no obsolete stratified/unstratified comparison remains in the notebook, activity UI, config, or exported artifact;
- controls redraw plot data and metrics, not labels alone;
- browser refresh restores documented defaults;
- narrow and desktop layouts do not clip content;
- shared Plotly visual/interaction policy remains active.

### Word document

- `.docx` opens successfully with the chosen library;
- title and 5-row × 3-column table are present;
- Exercises 1–4 are represented once each;
- required subjects and key coverage phrases are present.

Final validation gate, run once after implementation stabilizes:

1. targeted Exercise 4 Python/audit/export/notebook tests;
2. portable Exercise 4 build/check and one smoke execution;
3. frontend typecheck and relevant classification unit tests;
4. frontend production build;
5. Jupyter Book build once;
6. Exercise 4 standalone and built-book Playwright specs with `--workers=1`;
7. Word document structural validation.

Run project-wide suites only if a shared project file was changed in a way not covered by the focused tests. Record exact commands, counts, and elapsed times.

---

## 8. Local integration and stopping point

After validation:

1. Commit the implementation on `revise/exercise-04-classification` using explicit paths.
2. Switch to local `main` and merge with `--no-ff`.
3. If the merge is conflict-free, perform only a brief post-merge smoke check. Do not repeat the full gate.
4. Write and commit exactly the two WP18 reports below on local `main`.
5. Confirm the tree contains only the acknowledged untracked WP16 architect report and no other unintended files.
6. Stop without pushing or deploying.

If a conflict occurs, stop and report it rather than guessing.

---

## 9. Required reports

Create exactly:

- `WPs/reports/WP18_REPORT.md`
- `WPs/reports/WP18_EXACT_CHANGELOG.md`

Do not create numbered duplicates.

The report must state:

- success/partial/failure at the top;
- start tag/SHA, branch, implementation commit, merge commit, and final local SHA;
- selected `C`, CV specification, mean CV AUC, and honest test metrics;
- whether tuning improved or worsened WP17's test accuracy/AUC;
- the final imbalance activity behavior and metrics shown;
- confirmation that all stratification-comparison content/questions were removed;
- confusion-matrix label and estimator-output fixes;
- Word document path and validation result;
- tests, results, timings, failures, and single reruns if any;
- deviations and anything requiring Yoav's attention;
- concise commands and URL for local Exercise 4 testing;
- explicit confirmation that nothing was pushed/deployed and WP19 was not started.

The exact changelog must list every created, modified, renamed, or deleted file and every commit. Do not amend reports merely to insert the SHA of their own commit; return that SHA only in Claude's final response.

---

## 10. Final response to Yoav

Return a short recap rather than pasting the reports:

1. completion status;
2. selected `C` and honest updated accuracy/AUC;
3. the four requested notebook corrections completed;
4. Word document path;
5. key focused-test results;
6. final local `main` SHA and working-tree state;
7. any issue that requires Yoav's decision;
8. local build command and Exercise 4 URL;
9. report paths;
10. confirmation that no push/deployment occurred and WP19 was not started.

Then stop.
