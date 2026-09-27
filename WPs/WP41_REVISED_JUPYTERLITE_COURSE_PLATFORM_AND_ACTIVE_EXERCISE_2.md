# WP41 (Revised) — JupyterLite Course Platform and Active Exercise 2

## Status and authority

This specification supersedes WP41_ACTIVE_EXERCISE_2_AND_JUPYTERLITE_PILOT.md.
Do not execute the earlier WP41.

The new course architecture is:

- Jupyter Book remains the polished hub for Introduction, Syllabus, Contents,
  and course navigation.
- Each migrated exercise opens as a primary executable JupyterLite notebook on
  the same GitHub Pages site.
- Supplied code, student-written code, written answers, checked questions, and
  interactive figures all live in that one notebook.
- A prominent **Download my notebook** action downloads the student's current
  notebook, including edits and answers.
- Downloaded notebooks must run in local Jupyter and Colab, including
  notebook-native interactive activities where those environments support the
  standard widget stack.
- This WP establishes reusable infrastructure for all course notebooks but
  migrates and redesigns only Exercise 2.

Work must be reversible and isolated on a new branch. Do not merge, push,
deploy, or alter production.

## 1. Hard scope and exclusions

### In scope

1. Reusable JupyterLite course infrastructure.
2. Book-hub-to-notebook navigation.
3. Personal working copies, browser persistence, reset, and download.
4. A common notebook-native activity toolkit.
5. A course-wide exercise manifest and migration convention.
6. Full migration and active-learning redesign of Exercise 2:
   **Regression and Bias-Variance Trade-Off**.
7. Tests, documentation, and bounded local verification.

### Out of scope

- Do not migrate Exercises 1 or 3–12 in this WP.
- Do not redesign Introduction, Syllabus, or Contents beyond navigation needed
  to open migrated exercises.
- Do not update the Word course overview.
- Do not touch Homework_Materials/ or its private nested repository.
- Do not introduce cross-validation, tuning, or later-course theory into
  Exercise 2.
- Do not intentionally change approved model cohorts, features, splits,
  settings, or results.
- Do not remove the old React/widget implementation used by unmigrated
  exercises.
- Do not merge, push, deploy, or monitor GitHub Actions.
- Do not start WP42.

It is acceptable if unmigrated exercise links are temporarily unavailable in
this feature branch while the new routing is developed. Do not deliberately
damage their source files, and production must remain untouched.

## 2. Git checkpoint and branch

Before editing:

1. Record git status --short --branch, git log -8 --oneline --decorate, local
   main SHA, and origin/main SHA.
2. Confirm there are no unexplained changes.
3. Confirm Homework_Materials/ remains excluded without inspecting or
   modifying it.
4. Preserve the exact start commit in the local archive branch
   archive/pre-wp41-jupyterlite-course-platform.
5. Create and switch to feature/wp41-jupyterlite-course-platform.
6. Commit this revised WP specification as the first branch checkpoint.

If a requested branch already exists at a different commit, or the tree
contains unexplained changes, stop and report. Do not reset, rebase, stash,
delete, or resolve divergence automatically.

## 3. Target student experience

### 3.1 Course navigation

Keep the existing Jupyter Book pages for Introduction, Syllabus, and Contents.

On the Contents page and any Exercise 2 navigation entry, opening Exercise 2
must lead to its JupyterLite notebook as the primary exercise, not to a
competing static lesson.

Use the simplified JupyterLite Notebook interface rather than presenting
students with a full development IDE unless a technical constraint makes that
impossible. Open the exercise notebook directly.

The notebook interface must provide prominent actions:

- **Back to course contents**
- **Download my notebook**
- **Reset from course template**
- a clear save/autosave status

The old Exercise 2 URL may become a small transition page or redirect, but it
must not preserve a second divergent version of the lesson.

### 3.2 Personal working copy

Published course notebooks are immutable templates. On first launch:

1. create or open a personal browser-side working copy;
2. never silently overwrite that working copy on reload;
3. autosave edits to JupyterLite browser storage;
4. make it clear that work is stored only in that browser/device;
5. allow the student to download the current working copy;
6. allow an explicit reset from the current course template after a warning.

Use a reusable versioning convention so later template updates do not silently
replace student work. If the course template version changes, offer a fresh
copy while retaining or downloading the student's old copy.

### 3.3 Download contract

The **Download my notebook** action must export the current .ipynb, not the
original template. It must include:

- all supplied code cells;
- the student's edits in YOUR CODE HERE cells;
- written-answer cells;
- notebook-native interactive code;
- saved outputs where the notebook format normally stores them;
- metadata required for local Jupyter/Colab compatibility.

Students must also be able to use the normal JupyterLite file/download command,
but the course action should be easy to find.

Automated browser verification must edit a unique string into a student cell,
download the notebook, parse the downloaded JSON, and prove that the unique
edit is present.

### 3.4 No installation for the browser path

Students must not run a package-install cell in JupyterLite. The published
browser environment must already provide the common course packages required
by Exercise 2.

The downloaded notebook may retain one commented compatibility/install cell
for Colab or a local environment, following the established project standard.
Do not instruct students to install from the repository requirements.txt.

## 4. Architecture for all current and future notebooks

Build reusable infrastructure rather than a one-off Exercise 2 page.

### 4.1 Stable JupyterLite build

Use stable, exactly pinned, mutually compatible JupyterLite packages and a
browser Python kernel. Do not use alpha or floating versions.

Build JupyterLite into a stable subdirectory of the same GitHub Pages artifact
after the Jupyter Book build. The JupyterLite build must not overwrite the book
hub.

Do not commit generated JupyterLite output, a full Pyodide distribution, build
caches, or browser storage to Git. Commit only source notebooks, configuration,
locked requirements/environment files, generation code, extensions, static
course data/assets, and tests.

### 4.2 Common scientific environment

The browser environment must make these available without student installation:

- NumPy
- pandas
- scikit-learn
- Matplotlib
- Plotly if used
- ipywidgets
- any small accessibility/display dependency needed by the shared toolkit

Prefer standard packages that also work in local Jupyter and Colab. Avoid
JupyterLite-only APIs inside pedagogical cells.

Create one documented process for adding future package requirements. A future
exercise must declare its needs in one manifest rather than adding ad hoc
install logic.

### 4.3 Exercise manifest

Create one machine-readable manifest for Exercises 1–12 containing at least:

- exercise number and title;
- migration state;
- template notebook path;
- browser working-copy name;
- direct JupyterLite URL;
- template version;
- required data assets;
- required common or extra packages;
- fallback downloadable notebook path;
- legacy static-page path while migration is incomplete.

Exercise 2 is the only entry marked migrated/active in this WP.

Use this manifest to generate or validate book links and future notebook
deployment. Do not duplicate route strings across many files.

### 4.4 Data delivery

Bundle or publish course data as static same-origin assets. JupyterLite must not
require Git access, a GitHub token, or repository visibility.

For Exercise 2, provide the established ABIDE-II table needed by the notebook
without duplicating unnecessary large datasets. Validate it by checksum,
schema, participant count, and predictor count.

The same student notebook must locate data in JupyterLite, downloaded local
Jupyter, and Colab.

Keep environment detection in one small tested helper. Do not scatter
repository-specific paths through the notebook. Student-facing text must not
mention repository logistics.

### 4.5 Common notebook-native activity toolkit

Create a small shared Python toolkit that works in JupyterLite, Jupyter, and
Colab. It should support:

- compact single-choice questions;
- compact multiple-selection questions;
- **Check answer**, feedback, and retry/reset;
- short accessible sliders, dropdowns, and typed numeric inputs;
- figures that update predictably;
- light/dark-theme legibility where the host permits;
- helpful incomplete-work checks;
- consistent headings and student-facing instructions.

Use standard ipywidgets plus Matplotlib or Plotly rather than existing React
iframe components for migrated notebooks.

All Exercise 2 interactives must be notebook-native. Do not embed the current
React activities as iframes or depend on the live static widget site.

Keep helper implementation out of the teaching narrative where possible, but
ensure every helper/setup cell is executable and inspectable. A collapsed setup
cell is acceptable; an unexplained external black box is not.

### 4.6 Written responses

Open-response prompts must be followed by an editable notebook cell tagged
consistently as a student answer.

Prefer an editable Markdown answer cell with an obvious placeholder, or another
format reliably stored in the .ipynb. Do not rely only on transient widget
state that could disappear from the downloaded file.

Multiple-choice questions may use widgets for immediate self-checking. Written
answers need not be automatically graded.

### 4.7 Template generation and portability

Avoid three manually divergent versions of each exercise.

Use one authoritative structured source or deterministic generator to
produce or validate:

- the JupyterLite template notebook;
- the downloadable and Colab-compatible notebook;
- the minimal book-hub transition or link page;
- any completed reference notebook used only for automated testing.

Prompts, headings, starter code, variable names, activity order, and reference
images must remain synchronized by construction or durable structural tests.

## 5. Gate A — platform proof before content migration

Before rewriting Exercise 2, build a minimal end-to-end platform proof.

The proof notebook must:

1. open directly from the local built book hub;
2. start its browser Python kernel;
3. import the common scientific environment;
4. load a small same-origin data asset;
5. fit a scaler, LinearRegression, and KNeighborsRegressor;
6. calculate R² and MSE;
7. render a Matplotlib or Plotly figure;
8. render and operate a notebook-native slider or dropdown activity;
9. render and check a multiple-selection question;
10. edit and persist a code cell across reload;
11. download the edited notebook and prove the edit is present;
12. reset to the course template;
13. return to the book Contents page;
14. run in a downloaded local-Jupyter and Colab-compatible copy.

Measure and report:

- generated-site size before and after;
- JupyterLite-specific size;
- clean-cache page load;
- kernel start;
- first import;
- first small model;
- warm reload;
- notebook download size.

### Gate A stop condition

After one focused correction, stop before migrating Exercise 2 if any remain:

- the scientific stack cannot run in the browser;
- native widgets do not work;
- edited cells do not persist;
- download exports the template instead of current work;
- reset can destroy work without confirmation;
- ABIDE data delivery requires Git or repository access;
- the combined build overwrites or breaks the book hub;
- measured size or startup cost is clearly impractical for a classroom;
- a downloaded notebook cannot run in local Jupyter and Colab with reasonable
  compatibility instructions.

If Gate A fails, do not leave half-integrated infrastructure presented as
complete. Preserve diagnostics and report the blocker.

## 6. Exercise 2 active-learning redesign

Keep the title:

**Exercise 2: Regression and Bias-Variance Trade-Off**

Keep **What this notebook covers** concise. Explain that students will use
linear regression and KNN regression to predict age from ABIDE-II brain
measurements, run supplied code, complete code themselves, answer questions,
and explore model complexity.

Alternate among short worked code, YOUR CODE HERE activities, editable written
answers, checked questions, and notebook-native interactive figures. Do not
make every cell an exercise.

### Section 1 — Load data and prepare the split

Provide complete executable code for:

- imports needed for loading, cleaning, splitting, scaling, linear regression,
  and metrics;
- loading the approved ABIDE-II data;
- selecting the established 360 brain predictors;
- defining age as y and constructing X;
- making the established reproducible train/test split;
- fitting the scaler on training predictors only;
- transforming train and test predictors.

Do not import KNeighborsRegressor here. Students import it later.

All supplied cells must run in JupyterLite. Keep long logistics compact or
collapsed, but do not show results from non-executable pseudocode.

Remove internal numbered comments such as:

- 1-2. brain-only
- 3. one fixed
- 4-7. written out
- 8. observed vs predicted

Rewrite remaining comments as brief student instructions.

### Section 2 — Inspect the split before modelling

Use only a short introduction. This is a practical check, not another EDA
lecture.

#### Activity 2A — Compare target distributions

Ask students to write code that:

- plots y_train and y_test using the same bins and axis range;
- reports n, mean, standard deviation, minimum, and maximum;
- uses readable labels and a legend.

Starter cell:

    # YOUR CODE HERE

Do not provide a hidden completed solution beside it.

Follow it with an editable answer cell:

> Are the two distributions similar enough for this exercise? Name one
> similarity and one difference. Do not choose model settings from the test
> distribution.

Add a checked question about which uses of the test target are allowed. Explain
that this comparison is descriptive and must not guide feature or model
selection.

#### Activity 2B — Find features correlated with age

Ask students to write training-only code that:

- calculates Pearson correlations between every brain feature and y_train;
- sorts by absolute correlation;
- displays and plots the ten strongest relationships while preserving sign;
- uses shortened readable region labels.

Add an editable prediction cell:

> Which two or three features do you expect to have large fitted coefficients,
> and why?

Treat this as a hypothesis. Audit actual overlap between strongest train-only
correlations and later coefficients. Explain the real result: marginal
correlations and multivariable coefficients need not rank features identically.

### Section 3 — Fit linear regression

Provide complete executable code for:

- creating LinearRegression;
- fitting on scaled training predictors;
- predicting the test set;
- calculating and displaying test R² and MSE.

This is their first regression workflow, so do not turn these cells into blanks.

#### Activity 3A — Inspect coefficients

Ask students to write code that:

- pairs the 360 names with fitted coefficients;
- sorts by absolute magnitude;
- selects a readable number of largest positive and negative coefficients;
- draws a labelled horizontal bar plot;
- describes the coefficient axis correctly for standardized predictors.

Follow with an editable answer comparing correlation and coefficient rankings.

Add a checked multiple-selection question:

> Why can a feature's correlation with age and its fitted regression
> coefficient tell different stories?

Correct feedback should cover marginal versus conditional relationships and
correlation among predictors in plain language.

#### Activity 3B — Create observed versus predicted plot

Remove the supplied plotting solution from the student notebook.

Provide:

1. a task asking students to create an observed-versus-predicted scatter plot
   from y_test and the predictions;
2. a pasted reference image generated from the approved current result;
3. a checklist: observed age on x, predicted age on y, visible
   perfect-prediction diagonal, readable labels, useful title;
4. one YOUR CODE HERE cell;
5. an editable interpretation answer.

Embed the reference image portably. Do not hide completed plotting code
elsewhere in the student notebook.

### Section 4 — Correct and misleading evaluation

Rebuild the current comparison as a notebook-native activity. Shorten repeated
prose.

Convert one reflection into a checked question:

> Which evaluation can estimate performance for a new participant?

The correct choice is fit on training participants and evaluate on held-out
test participants. Explain why training-row evaluation and fitting on test
rows are misleading.

### Section 5 — Build KNN regression yourselves

Keep only a short reminder that KNN predicts from nearby training participants
and k controls model complexity.

Remove the worked k=20 model. Ask students to:

1. import KNeighborsRegressor;
2. create a model, initially with k=20 unless the current approved example uses
   another fixed starting value;
3. fit it on the same scaled X_train and y_train;
4. predict X_test;
5. calculate R² and MSE;
6. produce an observed-versus-predicted plot;
7. compare it with linear regression in an editable answer cell.

Use starter comments, not a nearly complete solution.

Add a graceful check cell. If expected variables exist, verify prediction
length and finite metrics; otherwise explain what remains incomplete without
breaking later independent sections.

### Section 6 — Bias and variance

Keep the classic bias-variance figure and essential KNN connection.

Remove the curse-of-dimensionality paragraph completely.

Cut repeated lecture theory: regression and train/test definitions, repeated
R²/MSE explanations, repeated warnings, author/audit notes, and repeated
small-k/large-k explanations.

State once:

- small k means greater model complexity, lower bias, and higher variance;
- large k means lower model complexity, higher bias, and lower variance.

Add one checked directionality question about changes that increase KNN model
complexity.

### Section 7 — Performance across model complexity

For every existing plot whose horizontal variable is k:

- use numerical x coordinate 1/k;
- display x-axis title **Model complexity**;
- make greater complexity run left to right;
- keep integer k visible in hover text, labels, or a companion readout;
- never label the visible axis 1/k;
- preserve existing predictions and metrics exactly;
- use accessible ticks for important tested k values.

Update questions and prose to use model-complexity language and connect the
plot to the classic bias-variance figure.

### Section 8 — Explore model complexity

Rebuild the KNN exploration as a notebook-native widget.

- k remains an integer control.
- Provide a usable slider and typed numeric input where appropriate.
- Display selected k clearly.
- Use 1/k only for plot position where k is horizontal.
- Visible axis title is **Model complexity**.
- Hover or readout reports k and model complexity.
- Preserve the approved training-sample comparison if currently included.
- Keep one non-duplicated reflection.

Add one checked question grounded in actual activity behavior.

### Bonus — Feature sets and sample size

Keep the current Bonus section visibly separate.

Port its current useful interactives to notebook-native controls. Keep the
approved warning once: trying many feature sets is exploratory comparison, not
formal feature selection.

Shorten repeated text. Do not add material merely to replace removed prose.

## 7. Question and activity audit

Review every existing Exercise 2 Think first, Reflect, question, and
instruction. Assign each one exactly one outcome:

- checked single or multiple-selection question;
- editable written-answer cell;
- concise non-response transition;
- removal because it duplicates another activity.

Aim for approximately:

- 4–6 student-written code tasks;
- 3–4 editable written answers;
- 4–6 checked questions;
- existing useful interactives rebuilt notebook-natively.

Each checked question must assess a distinct exam-relevant decision or
interpretation. Do not create a wall of quizzes.

## 8. Student-code conventions

Student code cells must:

- begin with a concise action;
- contain YOUR CODE HERE;
- use only short hints or intended variable names;
- avoid raise NotImplementedError;
- not reveal a full solution through comments;
- not define variables required by unrelated later sections unless a graceful
  dependency check exists.

All supplied code cells must execute successfully in sequence.

The untouched template need not solve blank exercises, but running supplied and
independent cells must not create a cascade of uncaught errors. Use section
independence and clear checks, not hidden solution fallbacks.

Create a completed reference notebook outside student-facing content for
testing solutions. Generate it from the same source or validate it against the
student template.

## 9. Student-facing editorial audit

Audit markdown, code comments, answer prompts, question feedback, plot text,
widget instructions, incomplete-work messages, navigation, and reset/download
explanations.

Requirements:

- address students directly;
- use short plain language;
- remove developer, tutor, audit, script, and WP commentary;
- remove meaningless numbered code notes;
- use consistent capitalization;
- prefer “held-out test evaluation” or “correct evaluation” to vague “honest”;
- avoid unexplained jargon;
- make the notebook materially more active while reducing total prose.

Report before and after student-facing prose word counts, excluding code,
tables, and generated output.

## 10. Numerical integrity

Record before and after:

- eligible participant count;
- train/test counts;
- predictor count, expected 360;
- linear-regression test R² and MSE;
- fixed-k KNN test R² and MSE;
- all existing complexity, feature-set, and sample-size values retained.

Migration and x-axis transformation must not change approved results. Explain
any drift concretely.

## 11. Course-wide migration documentation

Create a concise maintainer guide covering:

1. adding or updating the exercise manifest;
2. declaring packages and data;
3. generating template and portable notebooks;
4. using the shared question and widget toolkit;
5. creating personal working-copy routing;
6. adding Back, Download, Reset, and autosave behavior;
7. writing portability-safe code;
8. adding focused browser and notebook tests;
9. preserving model-result audits;
10. retiring an old static exercise only after parity is verified.

This becomes the infrastructure contract for Exercises 1 and 3–12.

## 12. Durable tests

Add focused tests for at least:

### Git and configuration

1. archive branch and start identity;
2. exact stable JupyterLite pins;
3. generated Lite output excluded from Git;
4. combined build retains book hub and Lite app;
5. manifest schema and unique routes;
6. only Exercise 2 marked migrated.

### Browser platform

7. Contents opens Exercise 2 working copy;
8. direct URL opens intended notebook;
9. required imports work;
10. data loads without Git access;
11. small linear and KNN models run;
12. native widget changes its figure or result;
13. checked questions return correct and incorrect feedback;
14. edited code persists after reload;
15. edited answer persists after reload;
16. downloaded file contains a unique browser edit;
17. reset warns and restores template;
18. Back to contents works;
19. 390px viewport remains usable;
20. light and dark presentation is readable;
21. no unexpected WP41 console or runtime errors.

### Exercise 2 content

22. all requested YOUR CODE HERE tasks exist;
23. no raise NotImplementedError;
24. KNeighborsRegressor is not imported before student task;
25. correlations use training rows only;
26. no hidden plotting solution beside reference image;
27. required editable answer cells exist;
28. checked questions have keyed answers and feedback;
29. curse-of-dimensionality text is absent;
30. internal numbered comments are absent;
31. metrics match baseline;
32. former k-axis plots use numeric 1/k, visible **Model complexity**, and still
    report integer k;
33. no visible 1/k axis title;
34. no duplicated Think first or Reflect prompts.

### Portability

35. downloaded template opens and executes supplied cells in local Jupyter;
36. Colab-compatible path works or is mechanically verified if full Colab
    automation is unavailable;
37. notebook-native activities use standard portable APIs;
38. completed reference notebook executes end to end;
39. student template and reference stay structurally synchronized;
40. reference image and data assets are portable and checksummed.

## 13. Bounded validation

Use focused tests while editing. Do not repeatedly run full suites.

1. Gate A proof and focused platform tests.
2. Manifest and generator checks.
3. Focused Exercise 2 structural, data, and metric tests.
4. Focused shared toolkit tests.
5. Frontend or extension typecheck/build if applicable.
6. One Jupyter Book build.
7. One JupyterLite build into combined publish tree.
8. Focused Playwright platform and Exercise 2 tests.
9. Completed-reference execution.
10. Student-template supplied-cell and no-cascade execution.
11. Downloaded local-Jupyter smoke test.
12. One full Python suite.
13. One full frontend suite if shared frontend code remains affected.
14. One final combined-site sanity check covering the hub, Exercise 2, and one
    unchanged legacy exercise if still routable.

For a failed gate, diagnose once, make one focused correction, and rerun only
that gate once. Stop and report if it still fails.

Do not use long polling, repeated arbitrary sleeps, or repeated full-suite runs.

Manual verification:

- clean browser profile;
- desktop and 390px viewport;
- light and dark mode;
- cold and warm JupyterLite start;
- open, edit code, run, save, and reload;
- edit written answer, save, and reload;
- operate every Exercise 2 interactive;
- check every self-check question;
- download and inspect edited .ipynb;
- reset after warning;
- return to Contents;
- no large unexplained blank areas;
- no unexpected WP41 console errors.

## 14. Commits and reports

Use small local commits:

1. revised WP checkpoint;
2. Gate A platform proof;
3. reusable course infrastructure;
4. Exercise 2 migration and active redesign;
5. tests and reports as appropriate.

Write:

- WPs/reports/WP41_REPORT.md
- WPs/reports/WP41_EXACT_CHANGELOG.md
- the course-wide JupyterLite migration and authoring guide required above.

The report must include:

- success or failure;
- starting and final SHA;
- archive and feature branches;
- exact JupyterLite, kernel, and package pins;
- concise mapping of hub, template, working copy, storage, download, and
  portable notebook;
- cold and warm timings and size impact;
- how ABIDE data works without Git access;
- proof download contains student edits;
- active-learning tasks added;
- interactives migrated and their implementation;
- exact prose and sections removed;
- before and after prose word counts;
- before and after metrics;
- changed files;
- every test, build, and manual result;
- deviations and decisions;
- anything requiring course-author attention.

After committing reports, stop. Do not merge, push, deploy, start WP42, or
watch GitHub Actions.

## 15. Required final response

Return a short course-author summary:

1. whether WP41 succeeded;
2. whether students can execute supplied and self-written code in one browser
   notebook;
3. whether native interactives and checked questions work there;
4. whether edited work persists and downloads correctly;
5. measured startup and size cost;
6. whether model results changed;
7. any decision or limitation requiring attention;
8. final feature branch and SHA;
9. confirmation nothing was merged, pushed, or deployed.
