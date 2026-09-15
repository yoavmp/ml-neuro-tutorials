# WP19 — Remove early cross-validation and parameter tuning

## Purpose

Revise the first four practice notebooks so that **cross-validation and formal hyperparameter selection are not taught in the early lessons**.

The lecturer and tutor have agreed that these concepts will be introduced later in the course. Exercises 3 and 4 should therefore use simple, preselected parameter values in their worked train-to-test examples. Students may still interactively explore what happens when a parameter changes, but the notebooks must not present that exploration as an honest parameter-selection procedure.

The notebooks may become shorter. Do not replace removed material merely to preserve length.

This WP is **local-only**. Do not push, deploy, monitor GitHub Actions, or begin WP20.

---

## 0. Bounded execution contract — mandatory

1. Use a fresh Claude Code session and read this WP fully before acting.
2. Hard-stop after **2 hours of active work**. If incomplete, leave the repository safe and write a partial report.
3. Do not use scheduled wakeups, background watchers, repeated polling, or placeholder waiting commands.
4. Interrupt any command that produces no result for 15 minutes.
5. Use focused tests during development and one final relevant validation gate. Do not repeatedly rerun broad suites.
6. A failed test may be rerun once in isolation. Make at most two fixes for the same failure, then stop and report it.
7. Build the interactive app once after code stabilizes and the Jupyter Book once after notebook regeneration. Rebuild only after a genuine failure-related fix.
8. Do not create or commit screenshots, videos, caches, temporary browser configurations, Jupyter build output, `.DS_Store`, or virtual environments.
9. Use explicit paths with `git add`; never use `git add .`, `git add -A`, or another broad staging command.
10. Do not create a report-update/push/deploy loop. No remote operation is authorized in this WP.
11. End after the WP19 reports. Do not begin another WP.

---

## 1. Protect and inspect the starting state

Run:

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
git log --oneline --decorate -12
git tag -l 'wp19-start'
```

Expected state:

- local `main` contains completed WP17 and WP18 work and is intentionally ahead of `origin/main`;
- WP18 has not been pushed;
- `WPs/reports/WP16_ARCHITECT_REPORT.md` remains an acknowledged pre-existing untracked file.

The WP16 architect report is explicitly whitelisted. Do not modify, delete, move, inspect further, or stage it. Its presence must not block WP19.

If any other unexpected modification or untracked project file exists, stop and report it rather than discarding, stashing, resetting, or absorbing it.

At the accepted starting commit:

```bash
git tag -a wp19-start -m "Checkpoint before removing early cross-validation material"
git switch -c revise/remove-early-cross-validation
```

If the tag or branch already exists, inspect rather than overwrite it.

Save this WP verbatim under the established `WPs/` convention and commit only that file as the checkpoint commit.

---

## 2. Inventory before editing

Inspect all student-facing material for Exercises 1–4 and all files that generate or test it. Search for, at minimum:

- `cross-validation`, `cross validation`, `cross_validate`, `cross_val_score`;
- `GridSearchCV`, `KFold`, `StratifiedKFold`;
- `CV`, `mean CV`, `fold`, `5-fold`;
- `hyperparameter`, `tuning`, `tuned`;
- `select C`, `selected C`, `best C`, `C grid`;
- `select k`, `selected k`, `best k`, `choose k`, `choosing k`;
- claims that a parameter was selected without touching the test set;
- questions, answers, captions, plot annotations, config text, portable replacements, and overview-document text containing those concepts.

Inspect canonical notebooks, portable notebooks, configuration files, generated JSON, Python model/export scripts, frontend code, test fixtures/assertions, launch content, Contents/Introduction pages, and the course-overview document generator.

Record a concise inventory in the final report. Do not blindly replace the letters `CV`, `C`, or `k`; determine their meaning in context.

### Scope rule

- Exercises 1–4 must not teach cross-validation or formal parameter selection.
- Exercise 3 and Exercise 4 are the expected substantive changes.
- Exercise 1 and Exercise 2 should change only if they contain student-facing references that conflict with the new course sequence.
- Developer tests may still use multiple cases for software validation, but the actual model-generation logic for the worked examples must use preselected parameters rather than secretly reproducing the removed selection procedure.
- Historical WP documents and completed WP reports are records. Do not rewrite WP13–WP18 reports or old WP instructions to erase history.

---

## 3. Project-wide teaching policy for the first four notebooks

The student-facing rule should be expressed briefly and consistently:

> In this introductory exercise, we choose one model setting in advance, fit the model using the training participants, and evaluate it on the test participants. A later lesson will introduce systematic methods for selecting model settings.

Do not name or explain cross-validation in that forward-looking sentence. Do not tell students that the current pipeline is “wrong” or “inaccurate”; simply present it as the deliberately simplified procedure used at this stage of the course.

Maintain the distinction between:

- **one worked evaluation:** parameter fixed in advance, fit on training data, evaluate on test data;
- **interactive exploration:** a teaching sandbox showing how model behavior changes as a parameter changes.

The interactive explorer must not instruct students to choose the parameter that maximizes held-out/test performance, call the maximum the “best” model, or report the explorer as an unbiased final performance estimate.

Do not add replacement theory. Shorter notebooks are desirable if the removed material was substantial.

---

## 4. Exercise 3 — KNN regression and bias–variance

Revise the canonical and portable Exercise 3 notebooks, KNN audit/export scripts, configuration, frontend text/annotations, generated artifacts, and tests.

### 4.1 Fixed worked-example parameter

Use this predeclared teaching value:

```python
K_EXAMPLE = 20
```

This value is selected by course design before inspecting the held-out result. Do not change it after running the model. Do not claim it was optimized, selected, validated, or chosen because it performed best.

The main worked example should be:

1. define the existing ABIDE age-prediction data and 360 ROI predictors;
2. create the established train/test split;
3. fit scaling on the training predictors and transform train/test data;
4. fit `KNeighborsRegressor(n_neighbors=20)` on the training participants;
5. predict and evaluate the test participants using the existing regression metrics.

Keep the existing honest-versus-invalid evaluation lesson if it does not depend on parameter selection.

### 4.2 Remove formal selection content

Remove or rewrite all student-facing material that:

- teaches five-fold or any other cross-validation;
- presents code that searches candidate `k` values to select the best one;
- calls `k=20` or any other value “CV-selected,” “optimal,” “best,” or “selected on training folds”;
- asks why parameter selection must occur inside training data;
- labels a plot line or marker as selected/best/optimal `k` based on validation performance;
- lists cross-validation or parameter tuning in What this notebook covers, Takeaways, prerequisites, review questions, captions, comments, or revealable answers.

Remove the selection code and its output rather than hiding it.

### 4.3 Preserve interactive exploration

Retain the existing Explore `k` browser activity and bias–variance demonstrations where useful. The activity may let students examine several `k` values, including small and large values, because this illustrates model complexity.

Requirements:

- default to `k=20` where a default worked-example value is needed;
- retain the precise numeric input beside the slider;
- retain the training-sample selector used to illustrate variance;
- retain the explanation that small `k` creates a flexible, high-variance/low-bias model and large `k` creates a smoother, low-variance/high-bias model;
- retain the observed-versus-predicted identity-line legend;
- remove any “best `k`” or “choose `k` from these test results” interpretation;
- label the activity as exploration of model behavior, not parameter selection;
- if a curve shows test or demonstration-set performance for many `k` values, add one brief sentence that repeatedly inspecting those results is for illustration here and is not being used to claim a final optimized score;
- do not introduce the postponed selection method by name.

If a static graph currently marks the CV-selected `k`, replace that annotation with **Worked-example k = 20** or remove it if the annotation is unnecessary.

### 4.4 KNN implementation and artifacts

The KNN audit and committed artifacts must genuinely use fixed `k=20` for the worked example. Do not retain a hidden search that happens to return 20.

It is acceptable for the interactive artifact to contain predictions/metrics for many `k` values because that data powers the teaching explorer. Its schema and documentation must distinguish this from formal model selection.

Update:

- model audit result and any manifest that records the main `k`;
- portable notebook values and outputs;
- frontend defaults and reset behavior;
- tests that previously asserted a CV-selected `k`;
- comments that reference audit scripts or old WP reports in student-facing code.

Record the fixed-k held-out metrics in the WP19 report.

---

## 5. Exercise 4 — logistic-regression classification

Revise the canonical and portable Exercise 4 notebooks, classification audit/export scripts, configuration, frontend artifacts, and tests.

### 5.1 Fixed worked-example parameter

Use the conventional predeclared setting:

```python
C_EXAMPLE = 1.0
```

This value is fixed by course design before inspecting the held-out result. Restore the original WP17 model specification and expected honest metrics unless recomputation reveals a reproducibility discrepancy:

- `LogisticRegression(C=1.0, max_iter=5000)`;
- expected test accuracy approximately `0.546`;
- expected test AUC approximately `0.569`;
- expected confusion matrix: TN=75, FP=60, FN=54, TP=62.

Recompute and verify these values; do not copy them without running the audit.

### 5.2 Remove C-selection material

Remove from student-facing Exercise 4:

- the entire “Choosing C honestly” subsection;
- `GridSearchCV`, `StratifiedKFold`, candidate grids, fold counts, CV-result tables, and the CV-AUC-versus-C plot;
- explanations comparing smaller/larger `C` if they exist solely to support tuning;
- questions and revealable answers about keeping the test set outside `C` selection;
- statements that `C=0.01` was selected or tuned;
- cross-validation/tuning entries from What this notebook covers, Takeaways, closing review questions, and portable content.

Do not replace this material. Let the notebook become shorter.

The worked pipeline should show only:

1. the established train/test split;
2. explicit train-only scaling for pedagogy;
3. the equivalent simple pipeline using fixed `C=1.0`;
4. fitting on the training participants;
5. one evaluation on test participants.

Keep the gray estimator representation suppressed and retain the labelled `TN = value`, `FP = value`, `FN = value`, `TP = value` confusion-matrix cells.

### 5.3 Preserve the appropriate interactive lessons

Retain:

- the decision-threshold activity;
- the class-imbalance and misleading-accuracy activity;
- the model-versus-majority-baseline accuracy plot;
- AUC, balanced accuracy, sensitivity, specificity, and test class counts;
- the lesson that threshold changes alter predicted labels/confusion-matrix measures but do not change the fixed model's AUC.

Regenerate both interactive artifacts using fixed `C=1.0`.

Do not add a new `C`-selection section or widget. The user explicitly permits the notebook to become shorter.

Remove obsolete `selectedC`, `cv_selection`, `best C`, or tuning fields from public artifacts/configs where they no longer represent the course procedure. A neutral field such as `modelC: 1.0` is acceptable if the frontend requires the fixed model setting.

In the imbalance activity, use fixed `C=1.0` at every class ratio and seed. Do not tune a separate value for each ratio.

### 5.4 Revise review questions

Maintain exactly three concise final review questions, covering:

1. probabilities versus class labels or why `predict_proba()` is used for ROC/AUC;
2. how lowering the threshold affects false negatives;
3. why accuracy can be misleading under class imbalance and what other information should be inspected.

No final question should concern cross-validation, tuning, parameter selection, folds, or selecting `C`.

Record the fixed-C held-out metrics in the WP19 report.

---

## 6. Audit Exercises 1 and 2

Read the canonical and portable notebooks for Exercises 1 and 2.

- If they contain no cross-validation or formal parameter-selection lesson, leave them unchanged.
- If they mention these subjects only as material for later lessons, remove or simplify that wording.
- Do not modify their analyses, outputs, interactives, or model results unless a direct conflict with the new first-four-notebooks policy is present.

Report explicitly whether any changes were necessary.

---

## 7. Update the Word notebook overview

Update both the overview generator and:

```text
course_overview/Machine_Learning_for_Neuroscience_Notebook_Overview.docx
```

Required content corrections:

- Exercise 3 must say that the worked KNN model uses a preselected `k=20`; remove the claim that `k` is chosen through training-only five-fold cross-validation.
- Exercise 4 must say that logistic regression uses fixed `C=1.0`; remove training-only cross-validation and `C` selection.
- Preserve the other accurate material descriptions.

Also correct the known layout defect from WP18: the Exercise 4 row must not split awkwardly across a nearly empty second page.

Keep the requested landscape orientation and readable 12-point body text. Prefer:

- shortening the coverage phrases without losing the main topics;
- reducing excessive title/introduction/table spacing;
- sensible page margins;
- keeping each table row together (`cantSplit`) where supported;
- preserving the blue header, clear borders, deliberate column widths, and vertical alignment.

The desired output is a clean one-page overview. Do not reduce body text below 11.5pt merely to force one page.

Validate the DOCX structurally. If an already-installed renderer is available, render and inspect it once. Do not install LibreOffice or let rendering delay the WP. If visual rendering is unavailable, state that clearly in the report so Yoav can return the file for external visual inspection.

Do not add `python-docx` to the student notebook requirements.

---

## 8. Required tests

Update meaningful tests rather than simply deleting assertions about the former procedure.

### 8.1 Repository-wide content audit

Add or update a test that inspects the rendered student-facing sources for Exercises 1–4 and confirms that prohibited early-course terms/code are absent where contextually appropriate:

- `GridSearchCV`;
- `cross_val_score` / `cross_validate`;
- `StratifiedKFold` / `KFold` used for model selection;
- “cross-validation” / “5-fold cross-validation”;
- “best/selected/optimal C” and “best/CV-selected k” claims;
- obsolete CV-result output cells.

Do not scan historical WP/report files with this test.

### 8.2 Exercise 3

Assert:

- worked model uses `k=20` with no hidden parameter search;
- train/test separation and train-only scaling remain intact;
- canonical/portable outputs and model audit agree;
- interactive default is `k=20` where applicable;
- changing `k` updates actual predictions and metrics;
- no UI or question calls an interactively viewed value “best” or “selected”;
- bias–variance explanations and training-sample variability remain functional.

### 8.3 Exercise 4

Assert:

- worked model uses fixed `C=1.0` with no hidden parameter search;
- no `GridSearchCV`, candidate grid, CV plot/table, or `cv_selection` result remains;
- fixed-C confusion matrix, accuracy, AUC, sensitivity, and specificity match trusted Python calculations;
- threshold and imbalance artifacts use the same fixed C;
- AUC remains invariant to threshold changes;
- imbalance baseline/model comparison remains correct;
- labelled TN/FP/FN/TP cells remain present;
- no rich estimator representation returns;
- canonical and portable notebook content/outputs agree.

### 8.4 Overview document

Assert:

- Exercises 1–4 are present once each;
- Exercise 3 contains fixed/preselected `k=20` and no cross-validation claim;
- Exercise 4 contains fixed `C=1.0` and no cross-validation/tuning claim;
- the table structure remains valid;
- row-splitting prevention is encoded where supported.

### 8.5 Final validation gate

Run once after implementation stabilizes:

1. focused KNN audit/export/notebook tests;
2. focused classification audit/export/notebook tests;
3. portable Exercise 3 and Exercise 4 build/check and one smoke execution each;
4. student-facing content-audit tests for Exercises 1–4;
5. relevant frontend unit tests and typecheck;
6. one frontend production build;
7. one Jupyter Book build;
8. Exercise 3 and Exercise 4 standalone/built-book Playwright specs with `--workers=1`;
9. Word-document structural validation.

Run a broad suite only when a changed shared file is not adequately covered by these focused checks. Record exact commands, counts, timings, failures, and the one permitted isolated rerun.

---

## 9. Local integration and stopping point

After validation:

1. Commit the implementation on `revise/remove-early-cross-validation`, staging explicit files only.
2. Switch to local `main` and merge with `--no-ff`.
3. If conflict-free, run only a brief post-merge smoke check. Do not repeat the full gate.
4. Create and commit exactly the two WP19 reports below.
5. Confirm the only remaining untracked file is the acknowledged WP16 architect report.
6. Stop without pushing or deploying.

If the merge conflicts, stop and report rather than guessing.

---

## 10. Required reports

Create exactly:

- `WPs/reports/WP19_REPORT.md`
- `WPs/reports/WP19_EXACT_CHANGELOG.md`

Do not create numbered duplicates.

The report must include:

- completion status at the top;
- starting tag/SHA, branch, implementation commit, merge commit, and final local SHA;
- complete inventory of early CV/parameter-selection material found before editing;
- exactly what was removed, retained, or reworded in each Exercise 1–4;
- fixed `k` and fixed `C` model specifications and recomputed test metrics;
- confirmation that interactive exploration is not presented as parameter selection;
- confirmation that the threshold and imbalance activities still work;
- overview DOCX changes, structural validation, and visual-render status;
- test commands, results, timings, failures, and single reruns if any;
- deviations and anything requiring Yoav's attention;
- local build commands and URLs for Exercises 3 and 4;
- confirmation that nothing was pushed/deployed and WP20 was not started.

The exact changelog must list every created, modified, renamed, and deleted file plus all commits. Do not amend reports merely to insert the SHA of their own commit; return that SHA only in Claude's final response.

---

## 11. Final response to Yoav

Return a short recap rather than pasting the reports:

1. success/partial/failure;
2. what changed in Exercises 3 and 4;
3. whether Exercises 1 or 2 required changes;
4. fixed-k and fixed-C held-out metrics;
5. confirmation that no early-course CV/parameter-selection lesson remains;
6. status of both interactive notebooks;
7. Word overview path and whether it is now one page;
8. key test results;
9. final local `main` SHA and working-tree state;
10. anything requiring Yoav's attention;
11. report paths;
12. confirmation that nothing was pushed/deployed and WP20 was not started.

Then stop.
