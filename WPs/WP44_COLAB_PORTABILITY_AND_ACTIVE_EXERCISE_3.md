# WP44 — Colab portability and active Exercise 3

## Authority and goal

The course author wants every migrated JupyterLite notebook to work end to end after a student downloads its current `.ipynb` and uploads it to Google Colab. This is now an acceptance requirement for Exercises 1 and 2 and every future migrated notebook. In the same WP, migrate Exercise 3, **Classification and Metrics**, to the active JupyterLite format and verify its Colab portability too.

Read the WP41 maintainer guide, WP42 and final WP43 deployment reports, the exercise manifest, the current Exercise 3 notebook, and the Exercise 1/2 generators and tests. Inspect current Git status, recent history, local/remote `main`, and the deployed SHA before editing. Preserve the exact start state with a checkpoint and work on a dedicated reversible branch. Stop on unexplained changes or divergence; do not reset, stash, or overwrite unrelated work. Do not touch `Homework_Materials/`. Do not merge, push, or deploy this WP. The currently live site must remain available while this work is reviewed.

## Gate A — Real Colab acceptance for Exercises 1 and 2

Test the **published downloadable notebook** for each exercise, as a student would: download the `.ipynb` from the course page, upload it to a fresh Google Colab session, and run from the top without a repository checkout, companion files, mounted Drive, or author-only environment variables. Use the notebook's actual setup and data-loading path. Verify its data source still works if the GitHub source repository becomes private; do not rely on a raw GitHub URL or a local relative CSV absent from the downloaded file. Check checksum/schema and approved numerical results.

For a complete execution test, make a temporary **teacher-only filled-in copy** of every `# YOUR CODE HERE` cell using the intended student workflow, then run all cells in sequence in fresh Colab. Do not publish solutions in the student notebook or copy teacher solutions into hidden student cells. Also run the untouched student template to verify unfinished exercises receive helpful messages rather than cascading failures. For both notebooks, test:

- every import and supplied code cell;
- every student task in the teacher-only completed copy;
- every checked single/multiple-choice question: incorrect feedback, correct feedback, and retry/reset where offered;
- every notebook-native slider, dropdown, typed input, and interactive figure: changing a control visibly changes the intended result;
- reference images and conceptual figures; editable written-answer cells; saving a copy and downloading the edited `.ipynb`;
- no student installation from repository requirements or Git access.

If Colab needs a package unavailable in its default runtime, add a concise, Colab-only setup cell installing **only the relevant pinned packages**, with no effect on JupyterLite's no-install browser path or normal local Jupyter. Avoid upgrading Colab's entire scientific stack without a demonstrated need. Reconcile versions, imports, rendering, data retrieval, and widget event handling based on observed failures. Update the authoritative generators, not only generated `.ipynb` files. Keep one source of truth and maintain byte/structural synchronization where intended. Preserve Exercise 1's 1114×13 curated table and established missingness/statistics; preserve Exercise 2's 1004×360 data, split, R²/MSE, KNN k=20 and k-sweep results.

**Evidence rule:** Do not call a local Jupyter run, `nbclient`, or static inspection a live Colab test. Record Colab runtime Python/package versions, notebook source/commit, exact cells and widget interactions, screenshots or concise observations, errors and fixes. If authenticated Colab access is unavailable, do all independent local work, document the exact blocker and a short manual test checklist, and mark Colab acceptance **unverified**; do not claim this gate passed or deploy. Do not enter or request the user's credentials through Claude.

## Gate B — Migrate Exercise 3 to JupyterLite

Title: **Exercise 3: Classification and Metrics**. Keep the established ABIDE-II autism-diagnosis question and the early-course rule: one fixed held-out train/test workflow, no cross-validation, tuning, or later-course feature selection. Preserve approved participant cohort, feature recipe, split, `C_EXAMPLE`, metric values, and useful existing activities unless a concrete correction is required. Audit the old notebook and record baseline results before migration. Keep `What this notebook covers` brief; remove repeated lecture explanations and duplicate Think first/Reflect prompts. Address students directly. Keep final takeaway questions.

### Section 1 — Data and setup

Give complete executable code for imports and loading the approved modelling table from same-origin assets in JupyterLite and a stable public, checksummed fallback in a bare downloaded notebook/Colab. No repository checkout or private GitHub access. Give a short explanation of diagnosis labels. If labels are strings, map them explicitly and reproducibly to **0 = control, 1 = autism** (verify the source values first), and display/check the class counts. Do not silently infer a mapping from alphabetical order.

### Section 2 — From a linear score to a probability

Briefly introduce the logistic sigmoid as the mapping from the model's linear score to a probability; no extended derivation. Convert the old 0.48-versus-0.52 prompt into a checked multiple-choice question: two predicted labels can differ at a 0.5 threshold even when the probabilities and underlying scores are close. Use fully visible options and useful feedback, following the repaired shared question layout.

### Section 3 — One logistic-regression model

Sequence the student activities as follows, without duplicating the split:

1. Students select feature column names from `df` into `FEATURES` using the hint that the cortical-thickness names start with `fsCT_`. Require **exactly 360** features; add a clear student-facing sanity check (count, names, numeric content) without silently filling them in.
2. Students define `X` and `y` using `df` and `FEATURES`, with `y` encoded 0/1 as established above. Check row alignment, shape, finite/numeric predictors, and class counts; provide helpful incomplete/different-valid messages.
3. Students make the established reproducible train/test split, preserving the approved stratification and seed if present. Give a compact hint and a check for expected sizes/class balance, but do not give a near-complete solution.
4. **Given code** uses their `X_train`, `X_test`, `y_train`, and `y_test`:

   ```python
   model = make_pipeline(StandardScaler(), LogisticRegression(C=C_EXAMPLE, max_iter=5000))
   model.fit(X_train, y_train)
   y_pred = model.predict(X_test)
   y_proba = model.predict_proba(X_test)[:, list(model.classes_).index(1)]
   ```

   Import the required classes in a supplied setup cell. Keep scaling inside the pipeline, fit only on training participants, and use the current approved `C_EXAMPLE`; do not tune it here. Guard this given cell if student prerequisites are unfinished so a fresh Run All on the blank template does not cause a long traceback cascade. When completed, use the student's actual variables, never a hidden alternate model.
5. Give code displaying a small paired sample of `y_test`, `y_pred`, and `y_proba`, with readable labels. Add a checked question or editable prompt on predicted class versus probability: confusion matrix/accuracy use a decision label, whereas probability-sensitive measures such as log loss and ROC use scores/probabilities. Keep terminology precise (ROC AUC uses ranking/scores; log loss uses calibrated probability values).

### Section 4 — Classification outcomes and metrics

Show the existing outcomes table with **TN, FP, FN, TP** clearly labeled and oriented consistently with the confusion matrix. Briefly give formulas and plain-language meaning for accuracy, sensitivity (recall for autism), and specificity (recall for controls). Students write code to construct and plot the confusion matrix and print accuracy, sensitivity, and specificity for their held-out predictions. Then students plot the ROC curve and print AUC using `y_proba`. Give concise starter hints, not solved code. Add teacher-only completed reference cells and helpful checks without leaking solutions into the student notebook. Check axes, class labels, denominator safety, values, and interpretation against the approved old notebook.

### Section 5 — Choosing a decision threshold

Rebuild the existing threshold activity as a notebook-native `ipywidgets` control. Show how threshold changes predictions and the confusion matrix/sensitivity/specificity; keep the underlying probabilities fixed. Use a typed numeric control if a slider alone is awkward. Ensure it works in JupyterLite, local Jupyter, and Colab. Keep one distinct reflection or checked question.

### Section 6 — Class imbalance and misleading accuracy

Rebuild the existing activity as a notebook-native control. Preserve its comparison across class ratios, model performance, and majority-class baseline; make the reason accuracy can mislead visible and clearly labeled. Use approved data/results. Avoid duplicate explanations and keep the activity runnable independently of an unfinished earlier student code cell where practical. Keep the final takeaway questions.

Use bold editable questions without `YOUR ANSWER HERE` in answer cells; code blanks use `# YOUR CODE HERE`. Ensure all option text wraps at 390px. No `raise NotImplementedError`, no hidden solution fallback. A completed reference notebook exists only for tests. Give a clear first-run setup instruction. Make code, Markdown answers, checked questions, and native figures travel in the downloaded notebook. Use a generator and manifest entry with template version, data assets, packages, direct Lite route, and portable route. Replace the old Book page with a transition page **only after** numeric, browser, and Colab parity pass. Keep old content recoverable in Git and do not disturb Exercises 4–12 or their React widgets.

## Gate C — Exercise 3 verification and global portability contract

Run the same real-Colab end-to-end procedure for Exercise 3's downloaded student notebook and teacher-only completed copy. Verify every widget and checked question by actual interaction. Also test a fresh JupyterLite browser profile through Contents → Exercise 3, kernel start, same-origin data, given code and a completed student path, save/reload/download with a unique edit, Reset warning, Back, light/dark, 390px, and an unchanged legacy Exercise 4. Verify no approved metric drift.

Add a documented **Colab acceptance gate** to the maintainer guide and migration template for every present/future JupyterLite notebook: published download → upload to fresh Colab → run untouched and teacher-completed copies → exercise all widgets/questions → inspect data/results → record runtime versions and evidence. Add automated structural and local execution checks as an early proxy, but do not present them as proof of Colab UI behavior. Establish one small teacher checklist/report template and ensure manifest/generator tests enforce Colab-safe data/package declarations. Do not add a CI job that needs the instructor's personal Google credentials. If live Colab cannot be verified, preserve work on the feature branch, report it, and do not mark Exercise 3 migrated/active or deploy.

## Tests, reports, and stop

Use focused checks during each gate; for a failure, diagnose and correct the actual issue rather than looping on whole suites. After the gates pass, run one bounded full Python suite, one combined Jupyter Book + Lite build, and one book browser suite. The current production site stays unchanged; **no merge, push, or deployment** in this WP.

Write `WPs/reports/WP44_REPORT.md` and `WPs/reports/WP44_EXACT_CHANGELOG.md` with branches/SHAs, changed files, before/after results, exact Colab environment and interactions for each notebook, local/browser tests, prose counts for Exercise 3, deviations, limitations, and decisions needing course-author attention. Commit reports locally. Return a short course-author summary saying separately whether Exercises 1, 2, and 3 passed **real Colab** verification and whether Exercise 3 is ready for local review. Do not start WP45.
