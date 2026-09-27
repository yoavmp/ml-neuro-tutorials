# Machine Learning for Neuroscience
## Project and Conversation Handoff

**Prepared:** 27 September 2026  
**Course author:** Yoav Melamed  
**Purpose:** Upload or paste this file into a new ChatGPT/Codex conversation to
continue the course-notebook project without reconstructing its history.

---

# 1. Instructions for the next assistant

This document is the authoritative conversational handoff for the
Machine Learning for Neuroscience teaching project.

Before proposing or performing new work:

1. Read this entire file.
2. Distinguish carefully among:
   - work already deployed to production;
   - work completed only on a local feature branch;
   - work merely planned in a work-package specification;
   - local-only private homework material.
3. Do not assume that WP41 has been executed. At the time of this handoff, the
   revised WP41 exists only as an instruction file.
4. Do not create the next work package until the user provides the report from
   the current one, unless the user explicitly changes that workflow.
5. When a Claude Code report is provided:
   - give the user a short plain-language summary;
   - flag only decisions or problems needing attention;
   - ask for required input;
   - proceed only when authorized.
6. Preserve the user's work-package conventions, Git safety rules, student-
   facing language standards, and future-private-repository constraint.
7. Do not use emojis in technical answers.

---

# 2. Project identity

## Repository and local paths

- GitHub repository:
  https://github.com/yoavmp/ml-neuro-tutorials
- GitHub Pages root:
  https://yoavmp.github.io/ml-neuro-tutorials/
- Local macOS repository:
  /Users/crazyjoe/Projects/ml-neuro-tutorials
- Python environment:
  /Users/crazyjoe/Projects/ml-neuro-tutorials/.venv
- Jupyter Book version previously reported:
  1.0.4.post1
- Main book source:
  book/
- Typical exercise source:
  book/chapters/chapter_XX/exercise_XX.ipynb
- Typical built page:
  book/_build/html/chapters/chapter_XX/exercise_XX.html

## Official title

Use:

**Machine Learning for Neuroscience**

Keep notebook titles capitalized and use ordinary Arabic numbering:

- Exercise 1
- Exercise 2
- Exercise 3

Do not switch to Roman numerals.

## Course format

- Two-hour lecture.
- Short tutor presentation reviewing relevant ideas.
- One-hour practical/tutoring session.
- Each practical notebook follows the presentation.
- PowerPoint presentations are available on Moodle; student-facing course text
  may mention Moodle but should not add an invented link.
- Notebooks must support both:
  - guided in-class practice;
  - self-learning at home and at the student's own pace.

## Reference material

The course is based partly on:

Gareth James, Daniela Witten, Trevor Hastie, Robert Tibshirani, and Jonathan
Taylor. An Introduction to Statistical Learning: with Applications in Python.
Springer, 2023.

Early structural inspiration:

- https://galkepler.github.io/ml_for_neuro/
- https://asafmm.github.io/ml_for_neuro/

The course materials are original teaching adaptations, not copies of those
sites.

---

# 3. Last known repository and deployment state

## Production

The last confirmed production deployment before the new JupyterLite plan was
the deployment that included Exercises 1–10.

Last confirmed release SHA recorded in this conversation:

    58ed1c61f43f0b3c6d23c1f32212bf2d3b9c9f0b

Exercise 10 and the existing static/custom-interactive architecture were
reported as successfully deployed and production-verified.

## Local state after the homework investigation

During WP40, the outer repository was reported unchanged:

- outer branch: main
- outer local SHA reported:

    24a1bd9...

- origin/main remained at the production release:

    58ed1c6...

- local main was one documentation-only commit ahead of origin/main.

These are historical observations, not a guarantee of the current machine
state. Any new WP must inspect Git rather than assuming these SHAs still apply.

## Important current status

The revised WP41 JupyterLite migration has **not** been run yet.

No JupyterLite platform migration should be described as implemented until the
user supplies WP41_REPORT.md and WP41_EXACT_CHANGELOG.md proving it.

---

# 4. Current production architecture

Before WP41, the site used:

1. Jupyter Book static HTML for prose, code output, navigation, and launch
   blocks.
2. Custom React/TypeScript/Plotly activities embedded in exercise pages.
3. Separate downloadable or Colab-compatible portable notebooks.
4. Static page-local configuration and data assets for widgets.
5. GitHub Actions to test, build, and publish GitHub Pages.

This system supports rich browser interactives but does not allow arbitrary
student Python to be edited and executed directly inside the exercise page.

Several major infrastructure issues were already solved:

- custom widget figures update correctly;
- light and dark modes are supported;
- Plotly dark-mode backgrounds, marks, grids, and drag layers were repaired;
- iframe/activity height communication was repaired to avoid excess blank
  space;
- portable notebooks are generated and smoke-tested;
- Colab and download links were aligned to the correct exercise;
- Pages deployment dependencies and CI history-fetch issues were repaired.

Do not discard the old React/widget implementation while unmigrated notebooks
still depend on it.

---

# 5. New authoritative platform decision

The user has decided to move from:

- static lesson with custom interactives;
- separate downloadable executable notebook;

to:

- one primary executable notebook environment containing both code and
  interactives.

## Chosen architecture

### Course hub

Keep Jupyter Book as the polished hub for:

- Introduction
- Syllabus
- Contents
- course navigation

### Exercises

Each migrated exercise opens as a primary JupyterLite notebook hosted on the
same GitHub Pages site.

The JupyterLite notebook must contain:

- all supplied code;
- editable student code cells;
- written-answer cells;
- checked multiple-choice and multiple-selection questions;
- interactive figures and controls;
- outputs;
- a clear route back to course contents.

### Interactives

For migrated notebooks, rebuild current interactives as notebook-native Python
activities using standard tools such as:

- ipywidgets;
- Matplotlib;
- Plotly where appropriate.

Do not merely embed the existing React activities as live-site iframes.

The goal is for the activity to sit inside the executable notebook, travel with
the downloaded file, and run in JupyterLite, local Jupyter, and Colab where the
standard widget stack is supported.

### Student working copy

Students should:

1. open the exercise from the course hub;
2. receive or resume a personal browser-side working copy;
3. edit and execute supplied and student-written code;
4. fill written answers;
5. use native interactive activities;
6. autosave in browser storage;
7. download their current notebook.

Required visible actions:

- Back to course contents
- Download my notebook
- Reset from course template
- save/autosave status

The download must contain the student's actual edits and answers. It must not
download the untouched template by mistake.

### Installation

Students should not install Python, Jupyter, or course packages for the browser
path.

JupyterLite should provide the required environment. The downloaded notebook
may retain a commented installation fallback for Colab or local use.

Student-facing text must never instruct students to install the repository's
requirements.txt.

### Scope of first migration

Infrastructure is intended for all exercises.

Only Exercise 2 is to be migrated and redesigned in WP41.

Exercises 1 and 3–12 are explicitly out of scope for that WP. It is acceptable
if they are temporarily inaccessible on the local feature branch during
platform development, but production must not be changed.

---

# 6. Revised WP41

## Authoritative file

Use only:

    WP41_REVISED_JUPYTERLITE_COURSE_PLATFORM_AND_ACTIVE_EXERCISE_2.md

The earlier file:

    WP41_ACTIVE_EXERCISE_2_AND_JUPYTERLITE_PILOT.md

is obsolete and must not be executed.

## Planned Git branches

Archive starting state:

    archive/pre-wp41-jupyterlite-course-platform

Feature branch:

    feature/wp41-jupyterlite-course-platform

## WP41 constraints

- New reversible branch.
- Gate A proves JupyterLite before migrating content.
- Stable and exactly pinned packages.
- No alpha or floating JupyterLite dependencies.
- No generated JupyterLite distribution committed to Git.
- No merge.
- No push.
- No deployment.
- No GitHub Actions monitoring.
- No WP42.
- No touching Homework_Materials/.
- Reports committed locally at the end.

## Gate A requirements

The platform proof must demonstrate:

- direct opening from the book hub;
- browser Python kernel startup;
- NumPy, pandas, scikit-learn, Matplotlib, Plotly if needed, and ipywidgets;
- same-origin data loading without Git access;
- scaler, linear regression, KNN, R², and MSE;
- a native interactive control;
- a checked question;
- cell editing;
- persistence across reload;
- download of the current edited notebook;
- reset with warning;
- return to course contents;
- local Jupyter and Colab portability.

It must measure:

- generated-site size;
- JupyterLite-specific size;
- cold load;
- warm load;
- kernel start;
- first import;
- first model;
- notebook download size.

If the platform remains impractical or broken after one focused correction, the
WP must stop before rewriting Exercise 2.

## WP41 reports expected

- WPs/reports/WP41_REPORT.md
- WPs/reports/WP41_EXACT_CHANGELOG.md
- a reusable JupyterLite notebook-migration/authoring guide

## Command previously prepared for Claude

After placing the revised WP file in the repository:

    cd /Users/crazyjoe/Projects/ml-neuro-tutorials

    claude "Read WPs/WP41_REVISED_JUPYTERLITE_COURSE_PLATFORM_AND_ACTIVE_EXERCISE_2.md completely and execute it exactly. This revised specification supersedes every earlier WP41 file. Begin with the Git checkpoint and new feature branch. Complete Gate A before migrating Exercise 2. Follow every bounded-validation and stop condition. Do not merge, push, deploy, monitor GitHub Actions, or start WP42. Finish by committing WP41_REPORT.md and WP41_EXACT_CHANGELOG.md and return only the requested short course-author summary."

---

# 7. Exercise sequence and present content

## Exercise 1 — Exploratory Data Analysis

Main dataset:

- ABIDE-II phenotypic table.

Current teaching scope:

- load a curated smaller phenotypic table;
- inspect rows with head, tail, and sample;
- identify categorical and numerical variables;
- convert hidden categoricals to categorical dtype;
- use info and describe;
- inspect missingness;
- discuss a small number of missing-data strategies;
- inspect distributions;
- calculate Pearson correlations for numeric features.

Important settled decisions:

- The original hundreds of variables were reduced substantially.
- Current teaching table has approximately 13 columns rather than 39.
- It includes ID, major demographics, categorical/numerical measures, and some
  variables with meaningful missingness.
- Interactive sampling should show all selected columns.
- A sample description may state the number of acquisition sites but should not
  list every site's name.
- Replace the word “impute” with plain wording such as “fill in missing
  values.”
- Exercise 1 is Pearson-only. Spearman was removed from text, code, questions,
  interactives, introduction, and summary.
- Range-check/outlier sections were removed to control length.
- The missing-data strategy table should contain at most three broad
  approaches.
- Data-loading code may be hidden while its useful output remains visible.

Exercise 1 remains more lecture-like than later exercises and will be revisited
after the active Exercise 2 redesign.

## Exercise 2 — Regression and Bias-Variance Trade-Off

This is the immediate focus.

Current production content combines:

- the original linear-regression Exercise 2;
- KNN and bias-variance material transferred from the former Exercise 3;
- a Bonus section containing feature-set comparison and sample-size material.

Current target:

- predict age from ABIDE-II neuroimaging features.

Predictors:

- 360 brain-region measurements.

Key current concepts:

- scaling;
- train/test evaluation;
- linear regression;
- observed versus predicted values;
- KNN regression;
- model complexity;
- bias-variance trade-off;
- feature-set comparison;
- sample-size effects.

Current early-course rule:

- no cross-validation or parameter tuning in Exercises 1–3;
- use preselected parameter values and a held-out train/test workflow;
- cross-validation is introduced later in Exercise 4.

The new active redesign is described in Section 8 of this handoff.

## Exercise 3 — Classification and Metrics

Current dataset/question:

- ABIDE-II;
- classify autism diagnosis using logistic regression.

Main content:

- one held-out train/test logistic-regression workflow;
- confusion matrix;
- TN, FP, FN, and TP labels inside the displayed table;
- accuracy;
- ROC AUC;
- class imbalance;
- comparison with changing majority-class baseline accuracy;
- interpretation of why accuracy alone can mislead.

Settled decisions:

- no cross-validation or C tuning in this early exercise;
- no stratified-splitting lesson as the main activity;
- the imbalance interactive compares model performance and baseline across
  increasingly imbalanced class ratios;
- duplicate Think first and Reflect prompts were removed.

## Exercise 4 — Validation and Cross-Validation

Main content:

- why a single train/test split is unstable, especially in small samples;
- cross-validation;
- train/validation/test division for parameter choice;
- nested cross-validation;
- KNN regression and logistic-regression pipeline examples;
- distinction between selecting a parameter and evaluating the selection
  procedure.

Important design decisions:

- first split-instability interactive combines effects of sample size and
  random seed;
- very small sample sizes may be used to demonstrate instability;
- hidden-test KNN activity includes several nearby k values;
- validation and test MSE should be compared after locking a choice;
- the nested-CV diagram should visibly show outer test folds and inner
  train/validation folds;
- candidate k values should be dense enough that different outer folds can
  select different values;
- this is not a homework-length extension; keep it focused.

## Exercise 5 — Regularization and Feature Selection

Main content:

- manual feature selection using literature and train-only relationships;
- comparison of predefined brain-feature sets;
- motivation: not every regional measurement is useful;
- Ridge regression;
- Lasso regression;
- effect of regularization strength;
- coefficient shrinkage and sparsity;
- complete tuning pipeline, now appropriate after Exercise 4;
- brief introduction to stepwise selection;
- compact comparison of at most three additional approaches;
- PCA mentioned as a future/different method.

Removed from plan:

- feature-selection stability section;
- long “Choosing a method” section.

End with an open question and general answer: method choice depends on research
question, data type, dimensionality, interpretability, and validation design.

## Exercise 6 — Decision Trees

Main content:

- one shallow regression tree;
- clear short names for the two displayed brain features;
- tree diagram with mean age/internal values and predicted age at leaves;
- title for the resulting tree;
- two-dimensional decision rectangles with visible separating lines;
- greedy split construction on a controlled but not perfectly separable
  16-participant dataset;
- tree complexity and overfitting;
- bagging;
- Random Forest;
- fair comparison on the same data and folds.

Settled corrections:

- greedy example must not be trivially separated;
- avoid duplicate post-activity reflections;
- single selected seed for model-comparison activity;
- concise y-axis labels;
- fair model-comparison table visible while its input code is hidden;
- a classification-tree depth figure is included only if the audited autism
  example genuinely demonstrates a deeper useful tree.

## Exercise 7 — Boosting and Gradient Boosting

Main content:

- boosting intuition;
- gradient boosting following decision trees;
- effect of learning rate, depth, and number of estimators;
- a complete gradient-boosting pipeline;
- computational cost as a practical consideration;
- parameter-grid results visualized rather than only tabulated.

Settled decisions:

- no AdaBoost for now;
- expensive partial grids must be explained to students as a computational
  trade-off, not as an internal author rule;
- all prose and code notes must address students.

## Exercise 8 — Unsupervised Learning

Main content:

- dimensionality reduction;
- PCA;
- explained and cumulative variance;
- PCA loadings summarized by brain region/lobe where meaningful;
- clustering as a concept;
- K-means as the method used to demonstrate clustering;
- selecting k using inertia and silhouette with cautious interpretation;
- example of unsupervised research use;
- PCA components used inside a previously learned supervised model.

Settled decisions:

- hierarchical clustering omitted;
- PCR is not introduced here;
- cumulative explained-variance y-axis starts at zero;
- cluster legend placed outside PC1–PC2 plot;
- supervised section title:
  “Using PCA in a Supervised Pipeline”
- when clustering metrics are ambiguous, guide students to inspect substantive
  patterns such as age separation rather than claiming one mathematically
  decisive k;
- replace “development partition only” with clearer train-plus-validation
  wording.

## Exercise 9 — Advanced Models

Lecture topics:

- PCR;
- PLS;
- SVM;
- kernels.

Notebook content:

- concise code examples rather than repeating an entire pipeline;
- important implementation differences;
- strengths, weaknesses, and when to use each;
- real ABIDE comparison;
- exam-oriented reasoning questions;
- relevant interactives.

Settled correction:

- the PCR/PLS interactive should describe alignment with the
  highest-variance direction, with results oriented consistently and
  intuitively.

## Exercise 10 — Examples and Common Mistakes

Purpose:

- synthesize earlier lessons around “What can go wrong in machine learning?”

Content:

- leakage from scaling before splitting;
- leakage from feature selection before splitting;
- leakage from PCA before splitting;
- leakage from filling missing values before splitting;
- parameter-selection leakage;
- model-fitting leakage;
- UCI smartphone/HAR data used to demonstrate grouped versus row-wise
  splitting when many observations come from the same participant;
- imbalance and appropriate metrics;
- spotting mistakes in code fragments;
- multiple-selection question about which operations learn from data.

Important question answer key:

Operations that learn quantities or make data-dependent decisions and must not
see final test participants:

1. Scaling
2. Feature selection
3. PCA
4. Filling missing values
5. Parameter selection
6. Model fitting

Selecting success measures such as F1 or AUC is the intended incorrect option
because choosing a metric conceptually does not estimate a value from the
dataset.

Settled corrections:

- KNN used in leakage demonstrations because scaling and PCA materially affect
  it;
- leaky and correct R² shown together;
- imbalance compares models across 50/50 through 90/10 ratios with several
  metrics;
- phone-data code fragment explicitly identified as belonging to the earlier
  phone activity;
- activity containers must not leave large blank areas.

## Exercises 11–12

These are currently syllabus-based placeholders.

Exact placeholder titles should be read from the repository/manifest rather
than reconstructed from memory.

## Exercise 13

There is no Exercise 13 notebook. The syllabus final-project material is
handled separately.

---

# 8. Exercise 2 active redesign requirements

These requirements led to the revised WP41.

## Overall goal

The lecturer's main feedback was that notebooks must be more active.

Students will bring computers and should:

- run supplied code;
- fill missing code themselves;
- type real written answers;
- use checked questions;
- use interactive figures;
- get their hands dirty rather than watching the tutor scroll.

Students may use AI for assistance, but the task structure must still require
them to edit, run, inspect, and interpret code.

## Given code

Provide full executable code for:

- loading data;
- selecting the 360 predictors;
- defining X and y;
- train/test split;
- scaling;
- first linear-regression fit;
- prediction;
- R² and MSE.

Do not make the first complete model workflow a blank exercise.

## Student activity: inspect y

Students write code to:

- inspect and plot y_train and y_test distributions;
- use the same bins and ranges;
- calculate n, mean, standard deviation, minimum, and maximum;
- answer whether distributions are similar;
- name one similarity and one difference.

This comparison is descriptive. Students should be told not to select features
or parameters based on the test target distribution.

## Student activity: train-only correlations

Students write code to:

- calculate Pearson correlations between training predictors and y_train;
- rank by absolute magnitude;
- retain the sign;
- show the strongest ten;
- make a readable plot.

They predict which features may later receive large coefficients.

The notebook must not promise that rankings will match. Marginal correlations
and multivariable coefficients answer different questions, especially with
correlated brain predictors.

## Given code: linear model

Provide:

- LinearRegression construction;
- fit;
- test prediction;
- test R²;
- test MSE.

## Student activity: coefficients

Students write code to:

- pair features and fitted coefficients;
- rank by absolute coefficient;
- plot readable largest positive and negative coefficients;
- compare coefficient and correlation rankings;
- interpret standardized coefficients correctly.

## Student activity: observed versus predicted

Remove the hidden supplied plotting solution.

Ask students to reproduce the plot themselves.

Provide:

- task description;
- a pasted static reference image from the approved result;
- checklist for x/y axes, diagonal, labels, and title;
- a blank YOUR CODE HERE cell;
- a written interpretation prompt.

Do not hide the completed solution elsewhere in the student notebook.

## Correct versus misleading evaluation

Keep the useful comparison, now notebook-native.

Add a checked question:

> Which evaluation can estimate performance for a new participant?

Correct answer:

- fit on training participants;
- evaluate on held-out test participants.

## Student activity: build KNN

Remove the worked k=20 KNN example.

Ask students to:

1. import KNeighborsRegressor;
2. create the model;
3. use k=20 as the initial fixed value unless the current approved example
   uses another;
4. fit the same scaled X_train and y_train;
5. predict X_test;
6. calculate R² and MSE;
7. produce observed versus predicted;
8. compare with linear regression.

KNeighborsRegressor must not be imported in the initial loading cell.

## Model-complexity axis

For every plot where k is horizontal:

- numerical coordinate becomes 1/k;
- visible axis title is **Model complexity**;
- complexity increases from left to right;
- integer k remains visible in hover/readout/ticks;
- never label the visible axis “1/k.”

This applies to:

- premade plots;
- interactive plots;
- the “How performance changes across every k” section;
- the “Explore k yourselves” section.

## Text reduction

Remove:

- curse-of-dimensionality paragraph;
- repeated regression theory;
- repeated train/test theory;
- repeated metric definitions;
- duplicated Think first and Reflect prompts;
- internal audit notes;
- meaningless numbered code comments such as:
  - 1–2 brain-only;
  - 3 one fixed;
  - 4–7 written out;
  - 8 observed versus predicted.

All comments and prose must address students.

## Activity mix

Approximate target:

- 4–6 student-written code tasks;
- 3–4 editable written-answer cells;
- 4–6 checked questions;
- current useful interactives rebuilt notebook-natively.

Do not create a wall of quizzes.

## Blank-cell convention

Student code cells use:

    # YOUR CODE HERE

Do not use:

    raise NotImplementedError()

Avoid hidden solution fallbacks.

Independent later sections should not collapse into uncaught errors if an
earlier student exercise remains incomplete.

---

# 9. Global pedagogical and editorial standards

## Tone

- Professional.
- Clear and concise.
- Address students directly.
- Suitable for self-learning.
- Avoid “vibe tutoring.”
- No developer-facing or tutor-facing notes in student content.
- No emojis in technical material.

## Notebook opening

Use a concise **What this notebook covers** section.

The sentence “This is Exercise X...” belongs under that heading consistently.

The opening should:

- be short;
- use simple wording;
- match numbered notebook sections;
- avoid advanced jargon before it is introduced.

Do not add a time budget.

Questions may:

- deepen understanding;
- resemble exam questions;
- have revealable answers when appropriate;
- remain open when no single answer exists.

## Code and data

- Hide routine loading input once students already know it.
- Keep useful table output visible.
- Comments must explain actions to students.
- Remove author notes about scripts, reports, WPs, seeds, audit procedures, or
  implementation mechanics.
- Use exact reproducible seeds when needed, but explain only student-relevant
  meaning.
- Keep approved numerical results honest; do not massage a model to force a
  narrative.

## Admonitions and questions

- Blue is the preferred standard for Think first boxes.
- Do not show nearly identical Think first and Reflect prompts.
- Move decision instructions before the interactive they govern.
- Use compact self-check questions where useful.
- Not every question needs a revealed answer.

## Language

Use plain wording for non-native English speakers.

Examples:

- prefer “fill in missing values” over “impute” in early notebooks;
- explain acronyms;
- use “our data table” instead of unexplained “modelling table”;
- use “correct evaluation” or “held-out test evaluation” instead of vague
  moral language such as “honest.”

## Visual design

- Consistent green run/download block.
- Tables should be readable and attractive.
- Figures must use clear titles, labels, legends, and accessible colors.
- Dark and light mode both need testing.
- Interactive cards should fit their content without large blank lower areas.
- Avoid legends covering data.
- Provide typed numeric inputs when sliders cover a large range.
- Explain reference lines in legends.

## Length

Keep notebooks as concise as possible.

The lecture introduces theory. Practice notebooks should emphasize:

- applying;
- changing;
- comparing;
- interpreting;
- writing code.

It is acceptable for a notebook to become shorter after removing material.
Do not add filler to replace removed theory.

---

# 10. Repository privacy and student-facing links

The repository may become private after the course is ready.

Therefore student-facing materials must not depend on:

- cloning the repository;
- reading private source paths;
- installing from the repository;
- public raw GitHub repository URLs;
- pip install -r requirements.txt.

Browser notebooks and data must work from published course assets.

Download/Colab notebooks may contain a code cell that installs the exact
packages they require, but should not assume access to the private repository.

Students with the site link must be able to use materials but cannot modify the
course author's source. Their browser edits exist only in their own working
copy.

---

# 11. Work-package and Claude Code workflow

The user manages larger edits through written WP Markdown files executed by
Claude Code.

## Required WP behavior

Every WP should:

1. inspect current Git status and recent log;
2. checkpoint/preserve starting state;
3. use a dedicated branch when appropriate;
4. avoid destructive Git commands;
5. preserve unrelated and untracked work;
6. implement only authorized scope;
7. run bounded focused checks before full suites;
8. avoid repeated loops and long arbitrary polling;
9. write a report and exact changelog;
10. stop before merge/push/deploy unless deployment is explicitly authorized.

## Reports

Typical names:

- WPs/reports/WPXX_REPORT.md
- WPs/reports/WPXX_EXACT_CHANGELOG.md

Reports should include:

- success/failure;
- starting/final SHA;
- branch;
- changed files;
- exact tests/builds;
- deviations;
- judgment calls;
- unresolved decisions;
- whether anything was merged, pushed, or deployed.

The user generally does not read full reports.

When the user uploads one:

1. provide a short recap;
2. say whether anything requires attention;
3. ask only necessary questions;
4. wait for authorization before creating the next WP.

## Avoiding Claude loops

Previous WPs sometimes took many hours because Claude:

- waited too long on workflow status;
- rechecked too infrequently;
- repeated broad test suites;
- treated bounded stop conditions as reasons to remain active;
- repeatedly polled GitHub Actions.

New WPs should specify:

- exact test gates;
- at most one focused correction and one rerun per failing gate;
- clear stop conditions;
- no repeated full suites;
- no arbitrary long sleeps;
- no deployment watch unless deployment is in scope.

For deployment, note that one successful workflow took approximately 17m43s.
A 15-minute hard timeout was too short. Use a sensible continuous watcher or a
single later status check according to the WP, not repeated manual nudges.

---

# 12. Local build and test commands

Run from the repository root, not from a nested interactive directory.

Activate environment:

    cd /Users/crazyjoe/Projects/ml-neuro-tutorials
    source .venv/bin/activate

Build:

    jupyter-book build book

Serve:

    python3 -m http.server 8000 --directory book/_build/html

Examples:

    http://localhost:8000/
    http://localhost:8000/chapters/chapter_01/exercise_01.html
    http://localhost:8000/chapters/chapter_02/exercise_02.html

If Jupyter Book says it cannot find a table of contents, confirm the terminal is
at:

    /Users/crazyjoe/Projects/ml-neuro-tutorials

and that:

    book/_toc.yml

exists.

Do not use file:// URLs for testing interactive assets. Use the local HTTP
server.

WP41 will likely add a second build step for JupyterLite; use the exact commands
reported by WP41 rather than inventing them now.

---

# 13. Git and deployment safety

## Ordinary update pattern

Before push:

    git status
    git add <specific files>
    git commit -m "..."
    git pull --rebase origin main
    git push origin main

Do not use force-push unless explicitly authorized.

If a push is rejected because remote contains work:

    git pull --rebase origin main

then resolve safely and push.

## Generated files

Past problems occurred when built/cache files under book/_build and notebook
checkpoint files were locally modified.

Do not assume generated artifacts should be committed. Follow current repo
rules and the active WP.

Do not run destructive broad cleanup commands.

## Production deployment

GitHub Pages is built through GitHub Actions.

Deployment WPs should:

- verify local and origin ancestry;
- merge only when authorized;
- push exactly as authorized;
- observe the one triggered workflow;
- avoid rerunning or pushing speculative fixes under a bounded deployment WP;
- verify production URLs after success;
- keep documentation-only report commits local if the WP requires avoiding a
  second deployment.

---

# 14. ABIDE data and modelling conventions

## Phenotypic data

- Official source: ABIDE-II.
- Official phenotypic legend should be linked.
- Full source contains hundreds of variables.
- Exercise 1 uses a small teaching subset.

## Neuroimaging modelling table

- Approximately 1004 eligible participants in established analyses.
- 360 regional neuroimaging predictors in current modelling exercises.
- Age is the main regression target in Exercise 2.
- Autism diagnosis is the classification target in Exercise 3.

## Evaluation principles

Early exercises:

- fixed held-out train/test evaluation;
- no CV or parameter tuning before Exercise 4.

Later exercises:

- Exercise 4 introduces CV, validation, tuning, and nested CV;
- subsequent regularization/model-comparison notebooks may use those methods.

Do not move later-course procedures back into Exercises 2 or 3 without explicit
approval.

---

# 15. Local-only Allen Cell Types homework investigation

This is not the immediate task, but it should be remembered for later.

## Location and privacy

All work lives under:

    Homework_Materials/

This directory:

- is excluded locally from the outer public repository;
- has its own nested Git repository;
- has no remote;
- must not be uploaded to public Git.

Nested repository final SHA reported by WP40:

    1a0eb84

Outer repository remained unchanged during WP40.

## Data prepared

Frozen Allen API snapshots:

- 2,336 by 56 electrophysiology table;
- 2,333 by 54 specimen metadata;
- 2,333 merged rows;
- 1,920 mouse cells;
- 1,813 mouse spiny/aspiny cells;
- 921 aspiny;
- 892 spiny.

Compact student table:

- approximately 15 teaching features;
- includes numerical, categorical, and missing values.

## Modelling findings

Classification, spiny versus aspiny:

- broad features: approximately 0.95–0.97 accuracy;
- compact features: approximately 0.89–0.93;
- dummy baseline: approximately 0.51.

RI regression:

- stronger regression target;
- stable broad models up to approximately R² 0.83;
- compact models approximately R² 0.24–0.50.

Tau regression:

- more difficult;
- stable broad models up to approximately R² 0.62;
- compact models approximately R² 0.28–0.45.

Important caveats:

- unregularized OLS can be numerically unstable on the correlated broad feature
  table;
- Ridge and Random Forest were stable;
- Lasso was not benchmarked in WP40 and needs a teacher-only audit before
  assigning it;
- multiple cells can come from the same donor;
- donor grouping is important;
- for a clean RI homework, consider excluding conceptually near-duplicate
  resistance measurements;
- if students have not learned grouped CV, provide a fixed donor-disjoint split
  or fold column.

User said this homework discussion will resume later.

---

# 16. Licensing and access expectations

The course website should be readable by students with the link.

Students must not be able to alter the instructor's source simply by using the
site.

JupyterLite personal edits are expected to remain in the student's browser
storage and downloaded notebook, not in the course repository.

The precise repository license choice was discussed earlier, but the current
handoff should not invent or change it. Inspect the repository's LICENSE before
making any licensing statement.

---

# 17. Immediate next step

The next step is not to redesign another notebook.

It is:

1. put the revised WP41 file into the local WPs directory;
2. execute it with Claude Code;
3. wait for Claude's final WP41 summary and reports;
4. upload WP41_REPORT.md and WP41_EXACT_CHANGELOG.md to the conversation;
5. assess whether JupyterLite passed Gate A;
6. assess whether Exercise 2 was migrated successfully;
7. ask only for decisions actually required;
8. do not merge, push, or deploy until the user has inspected the result
   locally and explicitly authorizes deployment.

After WP41, likely next phases are:

- local review and corrections to Exercise 2;
- deployment only after approval;
- migration of other notebooks one at a time using the new authoring guide;
- later revisit Exercise 1's more lecture-like structure;
- later resume Allen Cell Types homework design.

---

# 18. What the next assistant should ask for

If continuing immediately and no WP41 report is attached, ask:

> Has Claude finished WP41? If yes, please attach WP41_REPORT.md and
> WP41_EXACT_CHANGELOG.md. If not, run the revised WP41 rather than the obsolete
> earlier version.

If the user supplies Claude's short summary without files, it is acceptable to
review that first, but request the reports when exact implementation or test
details matter.

If WP41 stopped at Gate A, do not assume failure means JupyterLite is impossible.
Read the exact blocker and determine whether:

- one bounded correction is appropriate;
- a follow-up infrastructure WP is needed;
- the architecture should change.

Do not silently revert to the old static-plus-download approach because the
user explicitly chose a unified executable notebook environment.

---

# 19. Compact state summary

## Completed and live

- Jupyter Book course hub.
- Exercises 1–10.
- Current static/custom-interactive implementation.
- Dark-mode Plotly fixes.
- Responsive activity-height fixes.
- Portable notebooks and GitHub Pages deployment.
- Syllabus-aligned notebook ordering.

## Completed locally but private

- Allen Cell Types homework investigation under Homework_Materials/.

## Planned but not yet executed

- Revised WP41.
- Reusable JupyterLite exercise platform.
- Native notebook interactives.
- Browser personal working copies.
- Download-current-work feature.
- Active Exercise 2 redesign.

## Do not do yet

- Do not claim JupyterLite is installed.
- Do not merge or deploy WP41.
- Do not migrate all exercises in one WP.
- Do not start WP42 before reviewing WP41.
- Do not upload Homework_Materials/.
- Do not use the obsolete WP41.

---

# 20. Final reminder

The central pedagogical shift is:

> Students should not merely watch a polished interactive notebook. They should
> execute the supplied analysis, write meaningful pieces of code, record their
> interpretations, test their understanding, and leave with their own edited
> notebook.

The central technical shift is:

> Keep Jupyter Book as the course hub, but make each migrated exercise a
> browser-executable JupyterLite notebook with native Python interactives and a
> download action that exports the student's current work.

The revised WP41 is the first implementation of this direction.
