# WP20 — Student-facing editorial pass for Exercises 1–4

## Purpose

Review and edit every current practice notebook so that the material is clear to a student using it independently, while preserving the analyses, results, and working interactives.

This WP establishes four lasting authoring requirements:

1. Repeated data-loading code is collapsed on the website while its useful output remains visible.
2. Every student-facing word—including headings, markdown, code comments, interactive instructions, figure text, labels, and messages—is written for students and supports self-learning.
3. Every notebook begins with the same concise **What this notebook covers** structure.
4. Introductory lists use simple language and correspond clearly to the numbered notebook sections.

Create a repository-level authoring standard so these requirements are applied to all future notebooks.

This WP is **local-only**. Do not update the Word course overview, push, deploy, monitor GitHub Actions, or begin WP21.

---

## 0. Bounded execution contract — mandatory

1. Use a fresh Claude Code session and read this WP fully before acting.
2. Hard-stop after **2 hours of active work**. If incomplete, leave the repository safe and write a partial report.
3. Do not use scheduled wakeups, background watchers, repeated polling, or placeholder waiting commands.
4. Interrupt any command that produces no result for 15 minutes.
5. Use focused tests during editing and one final relevant validation gate. Do not repeatedly rerun broad suites.
6. A failed test may be rerun once in isolation. Make at most two fixes for the same failure, then stop and report it.
7. Build the interactive app once after text/config changes stabilize and build the Jupyter Book once after notebook regeneration. Rebuild only after a genuine failure-related fix.
8. Do not create or commit screenshots, videos, caches, temporary browser configurations, Jupyter build output, `.DS_Store`, or virtual environments.
9. Use explicit paths with `git add`; never use `git add .`, `git add -A`, or another broad staging command.
10. Do not create a report-update/push/deploy loop. No remote operation is authorized.
11. End after producing the WP20 reports. Do not begin another WP.

---

## 1. Protect and inspect the starting state

Run:

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
git log --oneline --decorate -12
git tag -l 'wp20-start'
```

Expected state:

- local `main` contains the completed WP17–WP19 work and is intentionally ahead of `origin/main`;
- Exercises 1–4 contain no early-course cross-validation or formal parameter-selection lesson;
- `WPs/reports/WP16_ARCHITECT_REPORT.md` remains an acknowledged pre-existing untracked file.

The WP16 architect report is explicitly whitelisted. Do not modify, delete, move, inspect further, or stage it. Its presence must not block WP20.

If any other unexpected modification or untracked project file exists, stop and report it rather than discarding, stashing, resetting, or absorbing it.

At the accepted starting commit:

```bash
git tag -a wp20-start -m "Checkpoint before student-facing editorial pass"
git switch -c edit/student-facing-notebook-language
```

If the tag or branch already exists, inspect rather than overwrite it.

Save this WP verbatim under the established `WPs/` convention and commit only that file as the checkpoint commit.

---

## 2. Files and surfaces to review

Review the final rendered student experience, not only notebook markdown.

Required scope:

- canonical notebooks for Exercises 1–4;
- portable/Colab notebooks for Exercises 1–4;
- text inserted by portable-notebook generation;
- all interactive activity configuration text;
- student-visible strings in interactive TypeScript components;
- figure titles, axis labels, legends, annotations, tooltips, empty/error states, and metric labels;
- code comments displayed in notebook code cells;
- tables and their captions/column labels;
- revealable questions and answers;
- the built Jupyter Book pages for Exercises 1–4.

Inspect shared Introduction/Contents text only when it directly duplicates or contradicts notebook wording. Do not perform an unrelated site-wide rewrite.

Do not edit historical WPs/reports. Do not update
`course_overview/Machine_Learning_for_Neuroscience_Notebook_Overview.docx` or its generator; Yoav has approved the current overview and will request a future update when needed.

Before editing, create a concise inventory of:

- repeated data-loading cells and their current tags;
- the opening/title/coverage structure in each notebook;
- headings or labels likely to be unclear to a first-time ML student;
- developer-facing, tutor-facing, or context-dependent language;
- introductory bullets whose numbering or content does not match the notebook sections.

Record the inventory and final decisions in `WP20_REPORT.md`.

---

## 3. Persistent authoring requirements

Create:

```text
NOTEBOOK_AUTHORING_STANDARDS.md
```

This is an internal contributor document and must not be added to the student-facing Jupyter Book table of contents.

Keep it short and practical. It must state that every future notebook/WP follows these rules:

### 3.1 Audience and voice

- Write directly for students who may be completing the notebook alone at home.
- Do not rely on an instructor being present to interpret the text.
- Prefer “we will…”, “you can…”, and direct explanatory sentences.
- Avoid author/developer notes, implementation history, internal script/report references, and instructions intended only for the tutor.
- Explain a technical term when it first appears; use the correct term afterward.
- Keep the tone professional, encouraging, and precise—not chatty or “vibe tutoring.”

### 3.2 Repeated data loading

- The first instructional data-loading example may remain visible when loading is itself being taught.
- In later notebooks, code that merely repeats already-taught imports/loading/column-selection logistics should carry the project's working `hide-input` metadata/tag.
- Keep the useful output—sample table, dimensions, or class counts—visible.
- Students must be able to expand the code on the website.
- Portable/Colab notebooks must retain runnable loading code even when the web presentation collapses it.
- Do not hide model-fitting or analysis code merely because it is long.

### 3.3 Notebook opening

Every notebook must begin:

1. main Exercise title;
2. `## What this notebook covers`;
3. one concise sentence identifying the exercise in the course;
4. a short, simple list matching the notebook's numbered sections;
5. the established green Run/download block.

The “This is Exercise X…” sentence belongs under **What this notebook covers**, never loose directly below the main title.

Do not add a separate Learning objectives section unless Yoav explicitly requests one.

### 3.4 Clear headings and introductory language

- Headings must tell a beginner what the section is doing.
- Prefer “Our data table” over “The modelling table.”
- Prefer “Testing the model on new participants” over “Honest evaluation.”
- Use technical headings such as “Confusion matrix” or “Bias–variance trade-off” when the technical concept is what students are learning, but explain it immediately.
- Introductory bullets should use short verbs: load, inspect, predict, compare, test, interpret.
- Avoid long parenthetical details, implementation jargon, and exact sample/feature counts in the opening unless the number is central to the lesson.
- If the opening list is numbered, its numbers and order must match the notebook's numbered section headings.

### 3.5 Interactives and self-learning

- Every control must say what the student is changing.
- Every figure must identify what is plotted and define unfamiliar lines or markers.
- Prompts must be answerable from the notebook and must not assume spoken tutor guidance.
- Interactive exploration must not be described as formal model/feature selection in Exercises 1–4.
- Empty states and errors must tell students what to change or check in plain language.

### 3.6 Technical integrity

- Simplify language, not scientific meaning.
- Preserve train/test separation, model settings, target definitions, metrics, and data provenance unless a WP explicitly changes them.
- Do not describe exploratory comparisons as causal evidence or final model optimization.
- Regenerate portable notebooks and stored outputs after canonical notebook edits.

Future WPs that create or edit notebooks should explicitly read this file before acting.

---

## 4. Repeated data-loading cells

Audit every code cell in Exercises 1–4 that imports libraries, downloads/loads ABIDE data, applies the already-established feature list, or reconstructs the familiar analysis table.

### Exercise 1

- Keep the first genuine data-loading example visible because Exercise 1 introduces the dataset and teaches students how it is loaded.
- If the notebook reloads or reconstructs the same table later only for logistics, collapse those repeated inputs.

### Exercises 2–4

- Collapse code inputs that repeat already-taught ABIDE loading and routine table construction.
- Use the exact cell tag/metadata already proven to work in this Jupyter Book version for **hide input, show output**. Inspect the current project convention rather than guessing the tag spelling.
- The resulting sample/data table, dimensions, class counts, or other useful output must remain visible by default.
- The collapsed control must remain expandable so an interested student can inspect the code.
- Do not use `hide-cell`, `remove-input`, or another treatment that removes the useful output or makes the code inaccessible.
- Do not collapse code that demonstrates scaling, fitting, prediction, metrics, plotting, missing-data handling, or another concept being taught.

Portable/Colab requirements:

- retain all required runnable loading code;
- do not replace it with an iframe or website-only reference;
- verify the portable notebook can execute from a fresh runtime according to the project's established smoke test.

Add a built-page assertion for each applicable notebook proving that the loading input starts collapsed/hidden while its output table is visible and the code can be revealed.

---

## 5. Standardize “What this notebook covers”

Edit the opening of Exercises 1–4 to use one shared pattern, following the concise style already preferred in Exercise 2.

Required structure:

```markdown
# Exercise X: [subject]

## What this notebook covers

This is Exercise X of the Machine Learning for Neuroscience practice series. [One short sentence describing the practice focus, if needed.]

In this notebook, you will:

1. [Simple action matching Section 1]
2. [Simple action matching Section 2]
...
```

Then place the established green Run/download block in the same relative position in every notebook.

Requirements:

- Move Exercise 1's “This is Exercise 1…” sentence from directly below the main title into this section.
- Keep the identifying sentence to one or two short sentences total.
- Use no more than one introductory list item per main numbered section.
- Use simple wording appropriate before students have read the lesson.
- Ensure the list numbers and order match the actual numbered headings exactly.
- Do not introduce advanced terminology in the list unless it is the named lesson topic.
- Remove duplicated overview prose elsewhere in the opening.
- Preserve each notebook's established Exercise number and non-Roman numbering.

Examples of the desired simplification:

- Replace “Load a wide modelling table—FreeSurfer brain measurements for 1004 ABIDE-II participants, with `age` as a native column” with “Load our ABIDE-II neuroimaging data, using age as the prediction target.”
- Replace “Evaluate an honest holdout protocol” with “Test the model on participants it has not seen before.”
- Replace “Interrogate empirical generalisation behaviour” with “See how the model behaves on new participants.”

Do not copy these mechanically if the underlying section differs.

---

## 6. Student-facing editorial review

Read every in-scope student-visible string in context and revise it where needed.

### 6.1 Plain-language headings

Replace headings that are technically correct but unclear before the section is read. Examples to inspect include, but are not limited to:

- “Modelling table” → “Our data table” or a more specific student-facing equivalent;
- “Honest evaluation” → “Testing the model on new participants”;
- “A predeclared k/C” → “Choose a value for this example”;
- “Invalid alternatives” → “What goes wrong when we test on training data”;
- “Empirical fitting/validation curve” → “How k changes training and test error”;
- “Locked test evaluation” → “Results on the test participants”;
- “Feature bundle” → “Group of brain regions,” unless the term is immediately defined and useful.

Do not remove a necessary technical term merely because it is unfamiliar. Introduce it clearly and then use it consistently.

### 6.2 Markdown and questions

- Address the student, not the tutor, developer, auditor, or report reader.
- Remove sentences such as “the instructor can explain…”, “as noted in WP…”, “see scripts/…”, or “this cell exists for testing.”
- Replace context-dependent instructions such as “discuss this” with a complete prompt a student can answer alone.
- Ensure references such as “above,” “the second plot,” or “this value” are unambiguous in both the website and portable notebook.
- Keep Think first boxes blue and answers revealable according to the established project design.
- Do not add a time budget.
- Do not make every paragraph longer in the name of explanation. Prefer a short sentence plus a clear example.

### 6.3 Code comments

- Rewrite comments as short explanations of what the next line does or why it is necessary for the analysis.
- Remove implementation-history comments, audit/report references, test instructions, and comments written to Yoav.
- Do not narrate obvious syntax line by line.
- Preserve comments that prevent leakage or clarify train/test behavior, but phrase them for students.

### 6.4 Interactive text and figures

Review all current activities:

- table inspection;
- histogram;
- missing-data retention;
- correlation explorer;
- regression feature comparison;
- KNN honest/invalid comparison;
- KNN `k` explorer and bias–variance displays;
- logistic-regression threshold activity;
- class-imbalance activity.

For every activity:

- use a clear student-facing title;
- make control labels describe the changed quantity;
- explain unfamiliar abbreviations at first use;
- give axes human-readable labels with units where applicable;
- identify identity/chance/reference lines in legends;
- replace internal words such as catalog, artifact, payload, manifest, audit, canonical, schema, render count, or test fixture if they appear to students;
- make success, empty, and error messages actionable;
- retain existing accessibility, responsive layout, Plotly visual policy, fixed axes, hover behavior, and dynamic iframe sizing.

Do not change data, model results, thresholds, splits, features, metrics, or activity calculations during this editorial WP.

---

## 7. Per-notebook focus

### Exercise 1 — Exploratory Data Analysis

- Preserve its role as the first introduction to loading ABIDE data.
- Ensure EDA, categorical variables, missing values, distributions, and correlations are introduced in plain language.
- Keep the opening concise even though this is the longest notebook.
- Ensure the opening list aligns with its final numbered sections.

### Exercise 2 — Linear Regression

- Replace “modelling table” and similarly opaque labels.
- Describe age plainly as the prediction target.
- Describe the fixed train/test procedure as testing on new participants.
- Keep the exploratory brain-region/measurement comparison explicitly exploratory, not feature selection or optimization.
- Preserve the fixed split and current metrics established by the WP19 correction.

### Exercise 3 — KNN Regression and the Bias–Variance Trade-off

- Introduce `k=20` as the value used for the worked example, not as “predeclared,” “selected,” or “optimal.”
- Explain neighbors, flexibility, bias, and variance for students encountering them for the first time.
- Keep interactive changes to `k` framed as learning how behavior changes, not choosing the final model.
- Preserve current fixed-k metrics and all working activities.

### Exercise 4 — Classification with Logistic Regression

- Introduce `C=1.0` simply as the value used in this example; avoid developer-facing “course-design constant” language.
- Explain probabilities, class labels, test participants, confusion-matrix outcomes, ROC/AUC, thresholds, and imbalance in student-facing language.
- Preserve the labelled TN/FP/FN/TP table and suppressed estimator representation.
- Preserve current fixed-C metrics and both working activities.

---

## 8. Portable notebooks and outputs

After canonical edits:

- regenerate all four portable notebooks using the established generator;
- execute/smoke-test portable notebooks only where the changed text/tags or generation logic require it;
- ensure loading code remains runnable and visible in Colab/downloaded notebooks;
- ensure website-only iframe replacements remain understandable without the browser activity;
- ensure no old heading, caption, question, answer, or code comment survives only in a portable notebook;
- ensure stored canonical outputs remain aligned with the unchanged calculations.

Do not add dependencies or private-repository references.

---

## 9. Tests and validation

Add or update focused tests without attempting to automate subjective prose quality completely.

Required structural assertions:

- each notebook has exactly one `What this notebook covers` heading;
- the “This is Exercise X…” sentence appears beneath that heading and not directly below the main title;
- every opening list is concise and matches the order/count of the main numbered sections;
- repeated loading cells in Exercises 2–4 carry the correct hide-input/show-output tag;
- Exercise 1's first instructional loading cell remains visible;
- built HTML starts repeated loading inputs collapsed while keeping their output visible;
- portable notebooks retain executable loading code;
- known unclear/internal headings and student-visible terms identified by the audit are absent;
- no student-facing script/WP/report/internal-artifact references remain;
- Exercise 2–4 model settings, features, splits, and metrics are unchanged;
- all interactive default values and calculations are unchanged;
- the new `NOTEBOOK_AUTHORING_STANDARDS.md` contains all four durable requirements.

Update existing tests and Playwright selectors that legitimately depend on revised visible titles. Prefer stable test IDs over fragile full-title selectors where an existing component can be improved without changing behavior.

Final validation gate, run once after the editorial work stabilizes:

1. notebook-authoring structural/content tests for Exercises 1–4;
2. portable notebook build/check for all four and focused smoke execution as needed;
3. affected Python notebook/export tests;
4. frontend typecheck and affected component/unit tests;
5. one frontend production build;
6. one Jupyter Book build;
7. built-book Playwright smoke tests for Exercises 1–4 with `--workers=1`, focused on opening structure, loading-cell visibility, and interactive readiness;
8. standalone interactive tests only for activities whose visible text/config/component changed.

Do not run model audits or regenerate model/data artifacts unless a validation check shows that an editorial change accidentally affected them. This WP must not change numerical results.

---

## 10. Local integration and stopping point

After validation:

1. Commit the implementation on `edit/student-facing-notebook-language`, staging explicit paths only.
2. Switch to local `main` and merge with `--no-ff`.
3. If conflict-free, perform only a brief post-merge smoke check. Do not repeat the full gate.
4. Create and commit exactly the two WP20 reports below.
5. Confirm the only remaining untracked file is the acknowledged WP16 architect report.
6. Stop without pushing or deploying.

If the merge conflicts, stop and report rather than guessing.

---

## 11. Required reports

Create exactly:

- `WPs/reports/WP20_REPORT.md`
- `WPs/reports/WP20_EXACT_CHANGELOG.md`

Do not create numbered duplicates.

The report must include:

- completion status at the top;
- start tag/SHA, branch, implementation commit, merge commit, and final local SHA;
- per-notebook inventory of repeated loading cells and opening structure before editing;
- final wording of each notebook's concise opening sentence and numbered coverage list;
- old → new list of every changed main section heading;
- representative examples of markdown, code-comment, interactive, and figure-label edits for each notebook;
- exact cells given hide-input/show-output treatment and proof their outputs remain visible;
- confirmation that portable loading code remains runnable;
- confirmation that model settings, metrics, data, and calculations did not change;
- authoring-standard file created and its future-use instructions;
- tests, timings, failures, and permitted reruns;
- deviations and anything requiring Yoav's attention;
- local build command and URLs for all four exercises;
- confirmation that the Word overview was untouched;
- confirmation that nothing was pushed/deployed and WP21 was not started.

The exact changelog must list every created, modified, renamed, and deleted file plus all commits. Do not amend reports merely to insert their own commit SHA; return that SHA only in Claude's final response.

---

## 12. Final response to Yoav

Return a concise recap rather than pasting the reports:

1. success/partial/failure;
2. what changed across Exercises 1–4;
3. which loading cells are now collapsed and whether outputs remain visible;
4. examples of important heading/wording improvements;
5. confirmation that all four openings now follow one concise structure;
6. confirmation that analysis code, data, and metrics are unchanged;
7. authoring-standard path;
8. key test results;
9. final local `main` SHA and working-tree state;
10. anything requiring Yoav's attention;
11. report paths;
12. confirmation that the Word overview was untouched, nothing was pushed/deployed, and WP21 was not started.

Then stop.
