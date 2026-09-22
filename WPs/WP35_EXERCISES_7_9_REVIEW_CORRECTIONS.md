# WP35 — Exercises 7–9 Review Corrections and Responsive Widget Heights

## 1. Purpose

Apply the instructor's review corrections to Exercises 7, 8, and 9, audit all existing student-facing material for author-directed wording, and implement a reusable solution for excessive empty space beneath interactive activities throughout the built book.

This WP also closes previously reported issues that remain relevant:

- add dedicated built-book dark-mode coverage for Exercise 7;
- replace time-based Playwright waits in Exercise 7 where an observable state can be used;
- remove the nonconverging `C=10` LinearSVR candidate from Exercise 9;
- make RBF-SVR's `epsilon` explicit rather than relying on an implicit default;
- make Exercise 9's expensive nested comparison optional when students run the portable notebook;
- stop asking a report commit to contain its own impossible-to-know SHA; instead, report the literal final branch-tip SHA in Claude's final response after the reports are committed.

Everything remains local for instructor inspection. This is not a deployment WP.

---

## 2. Starting state and branch safety

1. Record:
   - `git status --short --branch`;
   - current branch and `HEAD`;
   - the tip of `feature/wp34-exercise9-advanced-models`.
2. Start from the final committed WP34 branch tip, including its reports.
3. Resolve and record the literal WP34 report-commit/branch-tip SHA. Do not edit WP34's report merely to backfill it.
4. Confirm that Exercises 7, 8, and 9 are real notebooks and that the two WP34 activities are registered.
5. Preserve these pre-existing untracked files if present:
   - `WPs/reports/WP16_ARCHITECT_REPORT.md`
   - `WPs/reports/WP21_DEPLOYMENT_REPORT.md`
6. Do not reset, rebase, stash, clean, delete, or overwrite unrelated work.
7. If the starting state differs materially, stop and report the discrepancy.
8. Create:

   `fix/wp35-exercises7-9-review`

9. Add and commit this specification as the initial WP35 checkpoint before implementation.
10. At completion, commit implementation and reports locally. Do **not** merge, push, deploy, or monitor GitHub Actions. Do not begin WP36.

---

## 3. General student-facing language audit

Review all canonical notebooks, portable notebooks, widget configurations, and hardcoded widget text for Exercises 1–9. Do not perform blind string replacement; review each instance in context.

### Remove author/operator-directed language

Student-facing material must not refer to private production decisions or speak to the instructor. Rewrite or remove wording such as:

- “predeclared rule” when the rule belongs to the WP or instructor;
- “audited on the target machine”;
- “the WP report” or “see the script/report”;
- internal script paths;
- “per the task/instructions”;
- implementation history that is not part of the lesson;
- comments explaining decisions to the course author rather than to students.

Internal source-code comments, audit scripts, tests, manifests, and WP reports may retain implementation terminology when students never see it.

Add a focused content audit that flags likely author-facing phrases in student-visible material. Keep a narrow allowlist for legitimate instructional uses rather than banning ordinary words globally.

### Replace “development partition” everywhere students see it

Across Exercises 1–9 and their portable/widget content, replace unclear student-facing uses of “development partition” with context-specific plain language:

- **training-and-validation data** or **combined training and validation set** when it means all non-test data;
- **outer training fold** in nested cross-validation;
- **data available before the final test** when that phrasing is clearest.

Do not replace technical variable names such as `dev_indices` solely for style if they are internal or changing them would create risk. Student-visible code comments and printed labels must use clear wording.

Regenerate portable notebooks and outputs after these edits.

---

# Part A — Exercise 7 corrections

## 4. Rewrite the grid-size explanation for students

Find the student-facing paragraph beginning approximately:

> This is 27 candidates. Audited on the target machine...

Replace it with concise student-facing reasoning. It should communicate approximately:

> Computational cost is also part of model design. The full 27-candidate grid took roughly ten times longer than most model runs in these practice notebooks, so here we evaluate a smaller 12-candidate grid. It still represents shallow and deeper trees and combinations of low, medium, and high learning rates and numbers of trees. In your own work, define a manageable search before evaluating the candidates rather than removing settings after seeing their scores.

Refine the exact wording for clarity and brevity. Do not mention a private “predeclared rule,” target machine, WP, audit report, or internal timing protocol.

Review all other Exercise 7 Markdown, code comments, printed text, widget labels, and portable text for the same problem and correct every student-visible occurrence.

## 5. Replace the Section 6 candidate table with a bar graph

In `6. A Complete Gradient-Boosting Pipeline`, remove the visible results table containing:

- learning rate;
- number of estimators;
- maximum depth;
- cross-validation MSE.

Replace it with a readable grouped bar graph:

- y-axis: mean cross-validation MSE, beginning at zero because this is a bar chart;
- major x-axis groups: maximum depth 1, 2, and 3;
- four candidate bars within each depth group;
- color: learning rate;
- number of estimators shown as the minor subgroup/bar label, such as `50 trees`, or as a compact annotation directly associated with each bar;
- legend title: **Learning rate**;
- clarify visibly that lower MSE is better;
- identify the selected candidate without obscuring the bars;
- place the legend outside the plotting area if needed.

The four `(learning_rate, n_estimators)` pairs are the same fixed pairs currently crossed with all three depths. Do not change candidates or results merely to improve the plot.

If fold-level variability is already available, small error bars may be shown only if they remain legible. Do not make the figure visually overloaded.

Keep the underlying numeric details available in a collapsed code/details block or portable code, but do not show a second duplicate table on the website.

Update all explanatory text and questions that refer to “the table” so they refer to the graph.

## 6. Exercise 7 outstanding test corrections

1. Add a dedicated built-book dark-mode Playwright specification for every Exercise 7 interactive activity. Test light → dark → reload while dark → light, Plotly backgrounds/grids/data marks/drag layers, and console/runtime errors.
2. Locate the previously reported bounded `page.waitForTimeout(700)` Play/Pause lifecycle waits. Replace them with observable state/event assertions where possible, such as changed iteration/frame text, button state, or plot trace data.
3. If a short time wait is genuinely unavoidable for animation sampling, keep it only after documenting why no state signal is available, and bound it tightly. Do not retain a generic 700 ms sleep by default.

---

# Part B — Exercise 8 corrections

## 7. Highlight the central unsupervised-learning question

Find the opening sentence:

> This notebook asks a different question: what can we learn from brain measurements when no target is supplied at all?

Keep the short lead-in, but visually emphasize the question itself:

> **What can we learn from brain measurements when no target is supplied at all?**

Use the project's existing Markdown/admonition style rather than custom one-off HTML.

## 8. Correct the cumulative explained-variance plot

For the cumulative explained-variance plot:

- start the y-axis at zero;
- use a clear upper bound appropriate to the displayed data, preferably 100% if this does not flatten the plot excessively;
- include a visible point or concise annotation for PC1's explained/cumulative variance so students can see that the first component alone explains a large portion;
- keep percentage formatting consistent;
- update stored notebook output, portable output, audits, and figure tests.

Do not change the PCA fit or explained-variance values.

## 9. Rephrase the K-means scope sentence

Replace:

> K-means is the only clustering method covered in this notebook.

with student-facing wording equivalent to:

> In this notebook, we use K-means as one practical example for understanding how clustering works.

The wording should not imply that K-means is the only clustering method available.

## 10. Move the cluster legend outside the PC plot

For the static figure titled approximately **Participants in PC1–PC2 space, colored by cluster**:

- move the cluster legend outside the axes;
- reserve enough right margin so the legend is not clipped;
- verify readability for every available `k`, especially the largest;
- update the website, portable notebook, and visual tests.

If an equivalent legend overlaps the plot inside the interactive explorer, apply the same correction there as well.

## 11. Rename Section 8

Rename:

`## 8. Using PCA Before a Model We Already Know`

to:

`## 8. Using PCA in a Supervised Pipeline`

Update the TOC-on-page text, tests, portable notebook, and any references.

The section must still use PCA + KNN, not PCR or linear regression.

## 12. Guide students toward an appropriate interpretation of k

The activity currently shows:

- similar silhouette scores across candidate values of `k`;
- no strong inertia elbow, although `k=3` is a plausible bend;
- with **Age** selected as the external characteristic, `k=2` and `k=3` divide participants into visibly different age ranges;
- larger `k` mostly subdivides those ranges rather than producing a clearly stronger or more meaningful separation.

Add a concise guided exploration immediately before or after the interactive activity:

1. compare inertia and silhouette across `k`;
2. select **Age** as the external characteristic;
3. compare `k=2`, `k=3`, and at least one larger value;
4. ask whether larger `k` reveals new structure or mainly splits an existing age gradient into more bins.

The conclusion must be careful:

- `k=3` is a defensible exploratory summary here, not an objectively proven or uniquely correct number of clusters;
- the age comparison suggests that K-means may be discretizing a continuous developmental/age-related cortical-thickness pattern;
- age separation does not prove the existence of natural biological categories;
- these clusters must not be called autism subtypes.

Use this as an example of why inertia, silhouette, visualization, external characteristics, and scientific interpretation must be considered together.

Do not manipulate the data or metrics to create a clearer elbow.

---

# Part C — Exercise 9 corrections

## 13. Reverse and clarify the PCR/PLS alignment control

In the **PCR or PLS?** activity, replace the control concept:

> Target's alignment with the lower-variance direction

with:

> Target alignment with the highest-variance direction

Use correct spelling: **alignment**.

This must be a real data/model change, not a label-only reversal.

Regenerate the three deterministic presets so that:

- **Weak**: the target depends mostly on the lower-variance direction and weakly on PC1;
- **Moderate**: target information is more balanced across directions;
- **Strong**: the target depends mostly on the highest-variance direction, PC1.

Keep the predictor cloud, training/validation rows, and noise realization fixed across presets so the alignment change is isolated.

Expected teaching behavior with one component:

- under weak alignment with PC1, PLS should have the clearest advantage because it can turn toward the target-relevant lower-variance direction;
- as alignment with PC1 becomes stronger, one-component PCR should improve and the PCR–PLS gap should narrow substantially or disappear;
- with both components retained, PCR and PLS should converge to the same full linear predictor-space result, subject only to numerical tolerance.

Update:

- widget label and help text;
- exported targets and fits;
- construction notes;
- guiding questions;
- hidden reproduction code;
- portable notebook;
- Python and TypeScript tests;
- Playwright expectations;
- any screenshots or stored outputs.

Add explicit invariants testing the expected weak→moderate→strong trend rather than checking only that controls redraw.

## 14. Resolve the LinearSVR nonconvergence issue

The WP34 audit established that `LinearSVR(C=10)` fails to converge even with a much larger iteration limit, while all outer folds select `C=0.1`.

Remove `C=10` from the real-ABIDE LinearSVR comparison grid. Use:

`C ∈ [0.01, 0.1, 1]`

Keep the synthetic SVM activity's `C=100` option; that activity is a different small, well-behaved conceptual example.

Rerun the Exercise 9 ABIDE audit and confirm:

- no LinearSVR convergence warning remains;
- candidate selection and reported metrics are regenerated rather than copied;
- the notebook no longer discusses unresolved warnings;
- the grid table and portable notebook match the audit.

If another candidate still fails to converge, stop and report rather than silently suppressing the problem.

## 15. Make RBF-SVR epsilon explicit

Inspect the current RBF-SVR implementation. It presently reports tuning `C` and `gamma` but does not make `epsilon` visible in the comparison summary.

For this teaching comparison:

- set `epsilon=1.0` year explicitly for RBF SVR;
- continue tuning only `C` and `gamma` for RBF SVR;
- state in the compact grid/parameter details that epsilon is fixed at one year to keep the teaching grid manageable;
- do not imply that epsilon has been optimized;
- retain the conceptual parameter table explaining what epsilon means;
- add a test that prevents regression to scikit-learn's implicit default.

Rerun the full nested comparison because changing epsilon may change results.

## 16. Make the expensive comparison optional in runnable notebooks

The full Exercise 9 nested comparison currently takes approximately 3–4 minutes on the course-development machine. Students should be able to read and execute the notebook without unexpectedly waiting through the full audit.

Implement the established portable/canonical pattern so that:

- the full comparison code remains visible in the portable notebook and available in a collapsed/hidden website block;
- an explicit variable such as `RUN_FULL_NESTED_CV = False` defaults to not recomputing the entire comparison;
- default execution uses compact embedded audited results and immediately reproduces the visible table/plot;
- changing the variable to `True` runs the full nested comparison from the supplied code;
- a short student-facing note says the optional full run can take several minutes;
- the portable notebook has no dependency on a public GitHub repository or private local file to obtain the default embedded results;
- the Jupyter Book build no longer spends several minutes recomputing this unchanged comparison;
- the independent audit script remains the authoritative reproducibility path and still performs the complete calculation when explicitly invoked.

The displayed results must match the newly regenerated audit after the LinearSVR and RBF-epsilon corrections.

---

# Part D — Reusable interactive-height correction

## 17. Remove excessive empty space below interactive activities

Many built-book interactive iframes reserve substantially more vertical space than their contents require. Implement one reusable, future-proof resizing mechanism rather than manually tuning every notebook's fixed height.

### Required behavior

1. Each widget reports its natural rendered content height to the parent page after mounting.
2. Use `ResizeObserver` or an equivalent content-size signal inside the widget so height updates after:
   - Plotly rendering/relayout;
   - control changes;
   - reveal/collapse actions;
   - light/dark theme changes;
   - narrow/wide viewport changes.
3. The parent page listens for messages from the corresponding iframe and updates only that iframe's height.
4. Validate the sender by matching `event.source` to the iframe's `contentWindow` and use same-origin targeting where possible.
5. Debounce or animation-frame-batch resize messages and ignore trivial one-pixel oscillations.
6. Retain a reasonable initial fallback height before the first measurement, but replace it as soon as the widget reports its natural height.
7. Leave only a small visual allowance below the widget card—approximately 8–24 px, consistent with surrounding book spacing.
8. Do not introduce internal iframe scrollbars, content clipping, resize loops, or layout jumps after the initial settle.
9. Remove component/card CSS `min-height`, `height: 100%`, or large bottom padding only where it is responsible for artificial space and can be safely removed.
10. Apply the mechanism to every existing interactive activity in Exercises 1–9 and make it the default for future activities.

Do not solve this by maintaining a new table of manually calibrated pixel heights per widget.

### Required tests

Add reusable built-book tests that enumerate every interactive iframe in Exercises 1–9 and verify after layout settles:

- iframe height is at least the child document's required height within a small tolerance;
- bottom slack does not exceed a defined tolerance, such as 32 px;
- the child document has no vertical scrollbar caused by clipping;
- controls that change content still trigger an appropriate resize;
- dark mode and a 390 px viewport still fit;
- no resize-message or cross-window runtime error is emitted.

Use state/layout conditions rather than arbitrary long sleeps.

Document the reusable authoring behavior in `NOTEBOOK_AUTHORING_STANDARDS.md` so future notebooks do not add oversized hardcoded iframe heights.

---

## 18. Portable notebooks and generated artifacts

Regenerate all portable notebooks whose canonical content or terminology changes. At minimum this includes Exercises 7, 8, and 9; include earlier exercises if the “development partition” audit changes them.

Requirements:

- generator `--check` clean for all registered notebooks;
- Exercises 7–9 smoke-execute outside the repository tree;
- any earlier modified portable notebook receives its focused smoke check;
- no student-facing repository-install wording is introduced;
- Colab/download targets remain correct.

---

## 19. Focused regression tests

Add or update tests protecting:

### Exercise 7

- no author-facing grid-selection paragraph remains;
- 12 candidates unchanged;
- bar graph encodes depth, learning rate, number of estimators, and CV MSE;
- visible duplicate results table absent;
- dedicated built-book dark-mode coverage;
- animation tests no longer rely on the generic 700 ms wait.

### Exercise 8

- emphasized central question;
- cumulative explained-variance y-axis starts at zero;
- PC1 annotation/value matches the audit;
- revised K-means sentence;
- legends outside plotting areas;
- renamed Section 8 while retaining PCA + KNN;
- age-guided clustering questions and cautious conclusion present;
- no claim that `k=3` is uniquely correct or that clusters are autism subtypes.

### Exercise 9

- highest-variance-direction control label and regenerated behavior;
- weak/moderate/strong alignment invariants;
- LinearSVR grid excludes `C=10` and produces no convergence warnings;
- RBF SVR explicitly uses `epsilon=1.0`;
- displayed nested-CV results match the updated audit;
- default notebook execution does not run the expensive comparison;
- optional full-run path remains executable;
- portable notebook embeds audited defaults without repository access.

### Cross-book

- no unclear student-facing “development partition” remains in Exercises 1–9;
- likely author-facing phrases are absent from student-visible notebook/widget material;
- every interactive iframe passes the new content-height contract.

---

## 20. Bounded validation plan

Run in this order:

1. focused student-language and terminology audits;
2. Exercise 7 content/plot/audit tests;
3. Exercise 8 content/PCA/K-means audit tests;
4. regenerate Exercise 9 PCR/PLS artifact and run focused tests;
5. rerun the Exercise 9 ABIDE advanced-model audit once with the corrected grids/settings, then `--check`;
6. Exercise 9 notebook/content/result tests;
7. regenerate affected portable notebooks and run generator `--check`;
8. portable smoke execution for every affected chapter;
9. focused frontend unit tests and typecheck;
10. one frontend production build;
11. focused standalone Playwright tests for affected widgets, including state-based animation checks;
12. one Jupyter Book build;
13. focused built-book tests for Exercises 7–9 and the global iframe-height contract in light/dark/narrow layouts;
14. full Python suite once;
15. full frontend unit suite once;
16. full standalone and built-book Playwright suites once;
17. manual review of Exercises 7–9 and representative earlier widgets in light, dark, and narrow layouts.

Bounded-execution rules:

- Do not rerun a passing full suite.
- On failure, diagnose the root cause, make one bounded correction, and rerun only the failed focused gate once.
- If it still fails, stop and report instead of entering a repair loop.
- Do not use arbitrary long sleeps when observable state or layout is available.
- Do not run, watch, or poll GitHub Actions.
- Do not merge, push, or deploy.

---

## 21. Manual review checklist

Verify visually that:

- Exercise 7's grid explanation speaks to students;
- its grouped bar graph makes all four quantities understandable without overcrowding;
- Exercise 8's central question is visibly emphasized;
- cumulative explained variance begins at zero and PC1's contribution is obvious;
- cluster legends never cover observations;
- the age-guided K-means exploration leads to a cautious continuous-gradient interpretation;
- Exercise 9's alignment control behaves intuitively;
- Exercise 9 no longer exposes convergence warnings;
- its default runnable path is fast while the full code remains available;
- all interactive blocks shrink to their content without large empty lower regions;
- no content is clipped after interaction, theme switching, or viewport resizing.

---

## 22. Reports and stopping condition

Create:

- `WPs/reports/WP35_REPORT.md`
- `WPs/reports/WP35_EXACT_CHANGELOG.md`

The report must include:

1. overall success or failure;
2. resolved WP34 branch-tip SHA;
3. WP35 starting branch/SHA;
4. implementation commit SHA;
5. exact corrections in Exercises 7, 8, and 9;
6. updated Exercise 8 and Exercise 9 model metrics;
7. final Exercise 9 parameter grids and explicit RBF epsilon;
8. iframe auto-resize architecture and measured slack/clipping results;
9. language-audit findings and every student-facing phrase changed;
10. validation commands, durations, outcomes, retries, and deviations;
11. confirmation that Syllabus and Word overview were untouched;
12. confirmation that nothing was merged, pushed, deployed, or monitored through GitHub Actions;
13. final pre-report-commit status and decorated log.

Do **not** place a placeholder claiming the report contains its own final commit SHA. A commit cannot contain its own SHA. After committing the reports:

1. run `git rev-parse HEAD`;
2. run `git status --short --branch`;
3. include the literal final branch-tip SHA and final status in Claude's final response to the user.

The exact changelog must list every added, modified, renamed, and removed file and explain its purpose.

After the reports are committed, stop. Do not begin deployment or WP36.
