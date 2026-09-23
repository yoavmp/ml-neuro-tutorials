# WP38 — Exercise 10: Examples and Common Mistakes

## Purpose

Replace the Exercise 10 placeholder with a concise, student-facing review notebook titled:

**Exercise 10: Examples and Common Mistakes**

The notebook should synthesize the most important ways a machine-learning analysis can produce a
misleading estimate of generalization. It should not revisit every prior exercise or introduce a
large new algorithmic syllabus. Its central idea is:

> Final test participants must not influence preprocessing, feature construction, model selection,
> or training.

The notebook must use:

- the existing prepared ABIDE-II data for preprocessing leakage and class-imbalance examples;
- the public UCI Human Activity Recognition Using Smartphones dataset for the related-observation
  example;
- browser-native activities that work directly on GitHub Pages;
- runnable, self-contained portable/Colab material.

This WP is implementation-only. Do not merge, push, deploy, or monitor GitHub Actions.

---

## 1. Starting state and resolved WP37/WP37V dependency

WP37V resolved WP37's bounded monitoring stop:

- GitHub Actions run `35881835065` completed successfully;
- Exercises 7–9 were deployed and passed production verification;
- `origin/main` is expected at release commit
  `f792ad55f34342e627ed1fe3b85ff60777507d85`;
- local `main` is expected at WP37V documentation commit
  `2f74ccae826d14da9dee9997d890697d159d91c0`;
- local `main` is therefore expected to be exactly two documentation-only commits ahead of
  `origin/main` (`bf6aaa2` for WP37 and `2f74cca` for WP37V), with a clean working tree.

WP38 may now begin from that verified local `main`. Do not rerun or redeploy WP37.

Before editing:

1. inspect `git status --short --branch`;
2. record the full local `main` SHA and `origin/main` SHA;
3. confirm local `main` differs from `origin/main` only in the two expected documentation-only
   commits from WP37 and WP37V;
4. confirm there are no unexpected modified or untracked files.

The formerly mentioned WP16 and WP21 report files are tracked in the verified repository state;
do not treat them as expected untracked files.

Do not reset, stash, delete, rebase, or repair an unexpected state.

Create:

`feature/wp38-exercise10-common-mistakes`

from the verified local `main`.

Save this specification as:

`WPs/WP38_EXERCISE_10_EXAMPLES_AND_COMMON_MISTAKES.md`

Commit only the specification as the first checkpoint before implementation.

---

## 2. Inspect and reuse the current architecture

Before changing files, inspect:

- `NOTEBOOK_AUTHORING_STANDARDS.md`;
- Exercises 3–5 and 7–9;
- the current Exercise 10 placeholder;
- `book/_toc.yml`;
- the launch-button/portable-notebook generator;
- the existing widget registry, config schema, theme synchronization, iframe-resize contract, and
  refresh behavior;
- current quiz/question components, if any;
- existing ABIDE data manifests and split definitions;
- current offline audit/export conventions;
- portable smoke-test registration;
- the latest dark-mode, iframe-height, narrow-layout, and launch-button tests.

Reuse working generic infrastructure. Do not create a second widget runtime, a separate theme
system, or a second iframe-resize solution.

---

## 3. Scope and length

This is a review-and-debugging notebook, not a new comprehensive methods chapter.

Target:

- approximately 32–38 canonical notebook cells;
- four browser activities, of which the opening checkbox quiz is intentionally small;
- concise prose addressed directly to students;
- familiar data-loading code hidden on the website;
- reproduction code for browser activities hidden or collapsed on the website and fully runnable
  in the portable notebook;
- no repeated long explanations of material already taught in Exercises 3–9.

Do not add a time budget.

Keep the standard structure:

1. title;
2. green Run or download block;
3. What This Notebook Covers;
4. short numbered sections;
5. concise takeaways.

Replace the Exercise 10 placeholder with:

- `book/chapters/chapter_10/exercise_10.ipynb`;
- `book/downloads/chapter_10/exercise_10_portable.ipynb`.

Remove the old placeholder source only after the notebook, TOC, and launch-button paths are valid.

---

## 4. What This Notebook Covers

Use a short introduction in the established style:

> This is Exercise 10 of *Machine Learning for Neuroscience*. It reviews common choices that can
> make a model appear more generalizable than it really is.

Use four concise bullets:

1. keep preprocessing and feature construction away from final test participants;
2. avoid choosing models or parameters with the test set;
3. keep related observations in the same fold;
4. use metrics and training choices that match an imbalanced classification problem.

Do not list every subsection or every metric in the introduction.

---

## 5. Section 1 — The Boundary Around the Training Data

Introduce the main principle with a compact flow diagram:

Raw data → split participants → fit preprocessing/selection on training data → fit model → evaluate
once on locked test data.

Use the project's established diagram style. Keep it responsive, legible in both themes, and
shorter than the nested-CV diagram in Exercise 4.

Explain that excluding test rows from `model.fit()` is insufficient. Test participants must also
be excluded when learning:

- scaling values;
- missing-value fill values;
- PCA directions;
- target-informed feature selection;
- parameter choices;
- the final model.

### 5.1 Interactive multiple-selection question

Create or reuse a generic browser-native checkbox question component.

Question:

> Which operations learn quantities or make data-dependent decisions and must therefore not use
> the final test participants? Select all correct answers.

Options, in this order:

1. Calculating the mean and standard deviation for scaling — **correct**
2. Choosing features based on their correlation with the target — **correct**
3. Fitting PCA — **correct**
4. Calculating median values for filling missing data — **correct**
5. Selecting a model parameter from performance results — **correct**
6. Fitting the final prediction model — **correct**
7. Choosing in advance whether success will be summarized with F1, ROC-AUC, or another metric —
   **incorrect**

Do not include “renaming columns,” “choosing colors,” or another unrelated cosmetic distractor.

Interaction requirements:

- answers remain hidden before **Check answer**;
- students may select any number of options;
- exact full correctness is required for the overall success message;
- after checking:
  - correct selected answers are marked correct;
  - incorrect selected answers are marked incorrect;
  - missed correct answers are visibly identified;
  - concise per-option feedback is available;
- **Try again** resets selections and feedback;
- refresh restores the untouched initial state;
- keyboard interaction, focus indicators, labels, and an `aria-live` feedback region are present;
- do not store student responses or send network requests.

Final feedback:

> The first six operations learn quantities or make decisions from observed data. They may use
> training data—and validation data where appropriate—but they must not use the final test
> participants. A performance metric should be chosen in advance from the scientific question and
> the costs of different errors; it is not learned from the participant data.

Add one short nuance:

> Choosing a metric only after inspecting which one makes a model look best is still poor research
> practice, but it is different from fitting preprocessing or a model on the test participants.

Portable fallback:

- render the same checkbox-style question as Markdown;
- provide the answer in a collapsed solution block;
- do not require the frontend widget to understand the question.

---

## 6. Section 2 — A Leakage Laboratory

Use the existing prepared ABIDE-II cortical-feature table and age regression.

The section should compare a correct procedure with a procedure that lets final evaluation
participants influence an earlier step.

### 6.1 Scenarios

Include three scenarios in one activity:

1. **Scaling before the split**
   - leaky: fit the scaler on all rows, then split;
   - correct: split first, fit the scaler on training rows, transform evaluation rows.

2. **Feature selection before the split**
   - leaky: rank/select ROIs using correlations with age across all rows;
   - correct: learn the selected features inside the training data or training folds.

3. **PCA before the split**
   - leaky: fit scaling and PCA on all rows, then split the component scores;
   - correct: fit scaling and PCA only inside the training pipeline.

Add a short static code comparison for filling missing values:

- leaky: calculate medians from the complete dataset;
- correct: calculate medians from training rows and apply them unchanged to evaluation rows.

Do not add a fourth full imputation activity unless implementation inspection shows it can be added
without making the section long or duplicative.

### 6.2 Interactive activity

Suggested title:

**What Happens When the Test Set Leaks In?**

Controls:

- operation: Scaling / Feature selection / PCA;
- sample size: use a small predeclared set such as 60, 100, 250, and all eligible participants;
- split/seed selector from a finite precomputed set;
- number of selected features or PCA components only when relevant.

Outputs:

- correct-pipeline test MSE and R²;
- leaky-pipeline test MSE and R²;
- paired visual comparison for the selected split;
- an aggregate distribution or paired-difference plot across all predeclared splits, with the
  current split highlighted.

The activity must not imply that leakage improves every individual split. State clearly:

> Leakage makes the evaluation invalid even when its score is similar—or occasionally worse—in one
> particular split.

### 6.3 Predeclared audit design

Before building the browser artifact, define and document:

- eligible ABIDE participants;
- target;
- fixed model per scenario;
- sample sizes;
- seeds/splits;
- feature-count/component-count choices;
- exact correct and leaky workflows.

Use the same rows and outer splits within every paired comparison.

Do not search seeds for a visually dramatic example. Display a fixed series of consecutive or
otherwise predeclared seeds and summarize all of them.

Target-informed feature selection should usually provide the clearest inflation. Scaling and PCA
may show smaller differences; report that honestly.

### 6.4 Code cells

Show one concise wrong/correct code pair for each of:

- scaling;
- target-informed feature selection;
- PCA;
- median filling.

Use a scikit-learn `Pipeline` in the correct feature-selection and PCA examples. Avoid turning
this into another long pipeline tutorial.

On the website, hide or collapse code/output that merely reproduces the interactive figures. Keep
all code visible and runnable in the portable notebook.

### 6.5 Questions

Include a small blue Think First block:

- Which participants influenced this preprocessing step?
- Why is target-informed feature selection more direct leakage than scaling?
- If the two scores are almost equal, does that make the leaky procedure valid?
- Why can small samples be more vulnerable?

Keep the post-activity reflection distinct; do not repeat the same questions twice.

---

## 7. Section 3 — Do Not Choose the Model With the Test Set

Keep this section brief because validation and nested CV were taught in Exercise 4.

Present three compact workflows:

1. choose a parameter from training performance;
2. choose a parameter from test performance;
3. choose a parameter using validation/CV, then evaluate once on test.

Use KNN `k` as the familiar example.

Ask:

- Which workflow gives an optimistic final estimate?
- Why does trying more values on the test set make the problem worse?
- What role should the test set have after a model-development plan is fixed?

Use a small static figure or table backed by deterministic code. Do not add another major widget.

---

## 8. Section 4 — Related Observations Must Stay Together

Use the public UCI Human Activity Recognition Using Smartphones dataset:

- source: https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones
- DOI: https://doi.org/10.24432/C54S4K
- license: CC BY 4.0

The source dataset contains:

- 10,299 windows;
- 30 participants;
- six activity labels;
- smartphone accelerometer and gyroscope measurements;
- a participant ID for every row;
- 2.56-second windows with 50% overlap;
- an original participant-disjoint train/test split.

Explain:

> A row is a sensor window, not an independent person. Randomly splitting rows allows windows from
> the same participant—and sometimes overlapping signal segments—to appear on both sides of the
> evaluation boundary.

Connect this explicitly to neuroscience:

- repeated scans;
- longitudinal visits;
- multiple trials from one participant;
- twins/siblings sharing a family;
- acquisition sites when the goal is a new-site evaluation.

### 8.1 Compact, legally reusable course subset

Do not commit the complete 58 MB UCI archive.

Create a compact derived table containing:

- participant ID;
- activity label/name;
- a fixed, interpretable feature subset chosen by measurement family, never by association with
  the activity label.

Use this predeclared 18-feature subset if the official names are present exactly:

- `tBodyAcc-mean()-X/Y/Z`;
- `tBodyAcc-std()-X/Y/Z`;
- `tGravityAcc-mean()-X/Y/Z`;
- `tGravityAcc-std()-X/Y/Z`;
- `tBodyGyro-mean()-X/Y/Z`;
- `tBodyGyro-std()-X/Y/Z`.

If official feature-name formatting differs, map the same semantic 18 measurements and document
the exact names. Do not replace them based on predictive performance.

Store the compact table compressed if useful. Add a data/provenance note containing:

- dataset title and authors;
- UCI source URL and DOI;
- CC BY 4.0 attribution;
- original archive version/date if available;
- original archive checksum;
- deterministic extraction script and chosen columns;
- derived-file checksum.

Notebook and CI execution must be offline. A refresh/download mode may exist for maintainers, but
all checks and student notebook execution must use the committed compact subset.

### 8.2 Mandatory preflight audit before implementing the section

Before building notebook prose or frontend code, test the exact proposed task:

- target: six-class activity classification;
- features: the fixed 18-feature subset above;
- model: `Pipeline(StandardScaler(), KNeighborsClassifier())`;
- predeclared `k` values: 1, 3, 5, 11, and 25;
- ordinary comparison:
  `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`;
- participant-grouped comparison:
  `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)`, with participant ID as
  `groups`;
- metrics: accuracy and macro-F1;
- identical rows for both comparisons.

Also calculate:

- how many participants cross folds under ordinary splitting;
- how many cross folds under grouped splitting;
- number of observations per participant;
- confirmation that grouped folds have disjoint participant sets.

Proceed only if:

1. ordinary splitting places participant data across training and validation in every fold;
2. grouped splitting has zero participant overlap;
3. ordinary splitting is more optimistic by at least 0.03 in accuracy or macro-F1 for at least two
   of the predeclared `k` values;
4. the direction is not supported solely by one anomalous fold.

If these conditions fail:

- do not search new feature subsets, seeds, or arbitrary models;
- do not fabricate or simulate a stronger result;
- stop WP38 and report the complete preflight table for the user's decision.

If the conditions pass, retain and display all five predeclared `k` values, not only the ones with
the largest gap.

### 8.3 Interactive activity

Suggested title:

**Random Windows or New Participants?**

Controls:

- splitting method:
  - Randomly split windows;
  - Keep each participant in one fold;
- KNN `k`: 1, 3, 5, 11, 25;
- fold selector, if it remains readable.

Outputs:

- a participant/fold assignment diagram;
- number of participants appearing on both sides of the selected fold;
- validation accuracy and macro-F1;
- confusion matrix;
- an across-fold summary for the selected `k`.

Visual behavior:

- represent 30 participants as compact rows/tiles;
- under ordinary splitting, visibly show that participant windows appear in several fold colors;
- under grouped splitting, each participant receives exactly one fold color;
- avoid drawing hundreds of individual windows if that makes the display noisy;
- explain the 50% overlap without implying every pair of windows overlaps.

### 8.4 Scientific interpretation

Do not say row-wise splitting is universally invalid. Ask what future population the model must
serve:

- new windows from already-known users;
- completely new users.

For a claim about generalizing to new people, participant-grouped evaluation is required.

Guiding questions:

- What is the independent experimental unit?
- Why can windows from the same person be unusually similar?
- How does overlapping segmentation increase the risk?
- What is the neuroscience equivalent of participant ID?

---

## 9. Section 5 — Class Imbalance Changes the Question

Use the existing ABIDE autism-classification data and established logistic-regression pipeline.

Construct one deterministic imbalanced development/evaluation example, such as approximately 90%
control and 10% autism, using a predeclared sampling rule. Preserve a correctly stratified,
untouched evaluation set with the same intended prevalence.

Compare two valid approaches:

1. ordinary logistic regression;
2. logistic regression with `class_weight="balanced"`.

Both must use correct training-only preprocessing. This is not a leakage comparison.

### 9.1 Interactive activity

Suggested title:

**High Accuracy Can Still Miss the Minority Class**

Controls:

- ordinary versus class-weighted logistic regression;
- classification threshold;
- optional fixed set of precomputed prevalence levels only if this adds something materially new
  beyond Exercise 3. Default to a single 90/10 example to avoid duplication.

Outputs:

- confusion matrix;
- majority-class baseline;
- accuracy;
- balanced accuracy;
- ROC-AUC;
- PR-AUC;
- F1;
- precision and recall.

Keep the visual hierarchy clear. Do not present eight equally prominent numbers. Emphasize:

- accuracy versus majority baseline;
- PR-AUC and its prevalence baseline;
- F1/precision/recall at the selected threshold;
- ROC-AUC as a threshold-independent ranking metric.

State accurately:

- class weighting may improve minority recall or balanced accuracy while reducing raw accuracy;
- it is not guaranteed to improve every metric;
- “better” depends on the scientific objective and the costs of false positives and false
  negatives.

Do not tune the threshold on the locked test set. If the activity allows threshold exploration,
label it as a demonstration on fixed displayed predictions, not as a valid procedure for choosing
and reporting a final threshold from the same test data.

Questions:

- Which model detects more autistic participants?
- Which looks better if you inspect accuracy alone?
- Is 94% accuracy useful when the majority baseline is 95%?
- Which error matters more for the intended application?

---

## 10. Section 6 — Does the Split Match the Scientific Question? (Bonus)

Keep this short and conceptual.

Use ABIDE sites to contrast:

- random participant splitting with familiar sites in both sets;
- leave-one-site-out evaluation for performance at an unseen scanner/site.

Explain that neither is universally correct:

- random participant splitting estimates generalization to new participants from familiar sites;
- leave-one-site-out estimates generalization to a new site.

Use one compact diagram or question. Do not build another model grid or browser activity.

---

## 11. Section 7 — Find the Mistake

End with an exam-like debugging exercise containing short code fragments for:

1. scaling before splitting;
2. PCA before cross-validation;
3. target-informed feature selection on all rows;
4. random row splitting of repeated observations;
5. selecting `k` using test performance.

For each fragment, ask:

- What crossed the intended evaluation boundary?
- Why might the reported score be misleading?
- Where should the operation occur instead?

Use concise dropdown answers. Do not repeat the full explanations from earlier sections.

---

## 12. Final Checklist

End with a reusable checklist:

- split independent participants before learning anything from the data;
- fit scaling and missing-value filling on training data;
- place feature selection and PCA inside the validation pipeline;
- tune parameters without examining the final test set;
- group families, repeated scans, visits, trials, or sensor windows appropriately;
- make the split reflect the intended future population or site;
- compare classification performance with a meaningful baseline;
- choose metrics from the scientific goal and important error types;
- use the final test set only after development decisions are fixed.

Keep this to one compact block.

---

## 13. Data, audit, and artifact architecture

Follow the repository's established pattern:

- one deterministic audit script for the ABIDE leakage activity;
- one deterministic UCI HAR extraction/audit script;
- one deterministic audit for the imbalance comparison;
- committed semantic JSON artifacts for browser activities;
- `--check` modes that are offline and do not rewrite files;
- network access only in an explicit maintainer refresh path for obtaining the original UCI
  archive;
- notebook outputs and portable defaults derived from committed audited results;
- frontend schemas validating all data.

Record:

- cohort/sample counts;
- split definitions;
- seeds;
- models and fixed parameters;
- feature lists;
- all metrics;
- artifact hashes/provenance.

Do not allow browser code and notebook code to maintain separate unexplained copies of the same
numbers.

---

## 14. Portable notebook

Register Exercise 10 in the portable generator and smoke-test infrastructure.

The portable notebook must:

- run outside the repository;
- include the compact UCI HAR subset or another self-contained access method that does not require
  repository paths;
- not depend on frontend widgets;
- include an optional package-install cell in the established portable style, without telling
  students to install from the repository;
- include runnable correct/leaky comparisons;
- expose code hidden on the website;
- replace browser interactives with executable matplotlib/seaborn/scikit-learn equivalents and
  questions;
- default to bounded runtimes;
- contain attribution for UCI HAR.

Do not include student-facing references to repository internals, audit scripts, WPs, or
`requirements.txt`.

---

## 15. Frontend requirements

Create the minimum new components necessary and prefer reusable schemas/components.

Every activity must:

- update plots or displayed metrics when controls change;
- support refresh/reset;
- follow book-controlled light/dark theme, including first paint and reload while dark;
- use transparent Plotly drag layers;
- avoid controls or overlays covering axis titles;
- fit at 390px without page-level horizontal overflow;
- report its natural height through the existing iframe-resize mechanism;
- shrink after reset/content contraction;
- avoid large blank residual space;
- remain keyboard accessible;
- produce no runtime console errors.

Do not use JupyterLite.

---

## 16. Tests

Add focused tests for at least:

### 16.1 Notebook structure/content

- title and Exercise number;
- concise What This Notebook Covers;
- required sections in order;
- student-facing language;
- absence of author-only engineering notes;
- data-loading and reproduction-cell tags;
- no duplicate Think First/Reflect prompts;
- takeaways/checklist;
- Syllabus and Word overview untouched.

### 16.2 Multiple-selection question

- exactly seven required options;
- exactly six correct options;
- choosing the performance metric in advance is the only incorrect option;
- no color/renaming distractors;
- no answer leakage before Check;
- partial answers do not pass;
- missed and incorrect options receive correct feedback;
- Try again and refresh reset state;
- keyboard and ARIA behavior.

### 16.3 Leakage activity

- paired comparisons use identical participants/splits;
- correct preprocessing fits training data only;
- leaky variants match their explicitly documented mistake;
- feature selection uses the target only in the designated leaky comparison;
- seed/sample-size catalog is predeclared;
- aggregate summaries match point-level artifacts;
- browser metrics match independent Python results.

### 16.4 UCI HAR

- source URL, DOI, licence, and checksums recorded;
- compact table contains the fixed semantic 18-feature subset;
- no target-based feature selection;
- 30 participants and six activities, unless source-version inspection documents an official
  difference;
- repeated rows per participant;
- ordinary split participant overlap;
- grouped split zero participant overlap;
- preflight inclusion rule satisfied;
- all five `k` values preserved;
- frontend metrics match the audit;
- attribution appears in canonical and portable notebooks.

### 16.5 Imbalance activity

- deterministic class counts;
- identical split and preprocessing for ordinary/class-weighted models;
- no final-test tuning;
- confusion matrix and metrics internally consistent;
- PR-AUC baseline equals positive prevalence;
- class weighting is not described as universally superior.

### 16.6 Portable and launch behavior

- Exercise 10 portable generation deterministic;
- standalone smoke execution;
- Colab/download URLs point to Exercise 10;
- portable notebook contains no repository-relative dependency.

### 16.7 Visual/runtime

- standalone interactions;
- built-book structure;
- dark mode;
- reload while dark;
- narrow viewport;
- iframe height after expansion/contraction;
- no clipping or excess lower whitespace;
- no console errors.

---

## 17. Bounded validation plan

Run gates in this order. One normal attempt per gate; at most one targeted correction and one
targeted rerun for a genuine implementation defect. Do not restart full suites repeatedly.

1. UCI HAR source retrieval/provenance and mandatory preflight audit.
2. If preflight passes, commit the compact data subset and extraction/audit architecture.
3. Focused audit/export checks.
4. Focused Exercise 10 notebook/content tests.
5. Execute the canonical notebook once.
6. Generate Exercise 10 portable notebook and run generator check for all chapters.
7. Smoke-execute Exercise 10 portable notebook outside the repository.
8. Frontend typecheck and focused unit tests.
9. One frontend production build.
10. Focused standalone Playwright for Exercise 10 activities.
11. One clean Jupyter Book build.
12. Focused built-book Exercise 10, launch-button, dark-mode, narrow-layout, and iframe-height
    tests.
13. Full offline Python suite once.
14. Full frontend unit suite once.
15. Full standalone Playwright suite once.
16. Full built-book Playwright suite once.
17. Manual visual inspection of Exercise 10 at desktop and 390px in light and dark modes.

Do not:

- run repeated stress suites;
- search seeds/features/models after seeing results;
- refresh unchanged model artifacts speculatively;
- leave a background process/watch running;
- poll GitHub Actions;
- push or deploy.

---

## 18. Reports and final state

Create:

- `WPs/reports/WP38_REPORT.md`;
- `WPs/reports/WP38_EXACT_CHANGELOG.md`.

The report must include:

1. overall success/failure;
2. exact starting local-main SHA and origin-main SHA;
3. checkpoint, implementation, and final report SHAs;
4. final notebook outline and cell count;
5. exact checkbox options and answer behavior;
6. leakage scenarios, data, splits, and before/after results;
7. UCI HAR provenance, licence, fixed features, checksums, and extraction method;
8. complete HAR preflight table for all five `k` values;
9. participant overlap evidence for ordinary versus grouped splits;
10. imbalance class counts and complete metric comparison;
11. every validation command and result;
12. retries, deviations, judgment calls, and unresolved issues;
13. confirmation that Syllabus and Word overview were untouched;
14. confirmation that nothing was merged, pushed, deployed, or monitored through CI;
15. literal final `git status --short --branch`.

Commit implementation and reports locally on:

`feature/wp38-exercise10-common-mistakes`

Do not merge into `main`, push, deploy, monitor GitHub Actions, or start WP39.
