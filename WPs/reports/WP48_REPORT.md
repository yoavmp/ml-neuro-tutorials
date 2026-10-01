# WP48 report: question display in Exercises 1–7 and focused polish in Exercises 1–4

## Scope and starting state

Starting SHA (local `main`): `9195865` ("WP47: reports — execution report and
exact changelog"), the tip of `feature/wp47-active-exercise-8-unsupervised-learning`.

Checkpoint branch: `checkpoint/wp48-pre-work`, at that same tip.

Feature branch: `feature/wp48-questions-and-exercises-1-4-polish`, created
from that same tip; the WP spec was committed to it first (`faba9ce`).

This WP had two independent halves:

- **Part A** — bring Exercises 1–7 to Exercise 8's `show_question(id)`
  presentation (hide `correct_index`/`correct_indices` from every visible
  question cell).
- **Parts B–E** — the author's specific, itemized fixes for Exercises 1–4.

No merge, no push, no deployment, no GitHub Actions interaction at any
point. `Homework_Materials/` untouched. Exercises 9–12 untouched.
Exercise 8 untouched (no compatibility issue required touching it).

## A. Question display in Exercises 1–7

Exercises 1–7 each had the correct_index/correct_indices answer key typed
directly into a *visible* code cell (`display(make_single_choice_question(
..., correct_index=0, ...))`). Exercise 8 (WP47) had already moved this
content into the hidden setup cell behind a `_QUESTIONS` dict and a
`show_question(question_id)` wrapper, so a visible cell only ever calls
`show_question("q-some-id")`.

Applied the identical pattern to all 26 checked questions across Exercises
1–7 (3+5+5+3+3+4+3), generator by generator:
moved each question's `prompt`/`options`/`correct_index(es)`/feedback into
a new `_QUESTIONS` dict inside each generator's `SETUP_SOURCE_TEMPLATE`,
added a `show_question()` function identical in shape to Exercise 8's, and
replaced each visible `display(make_..._question(...))` call with a single
`show_question("q-id")` line. No wording, option, or answer-key change
anywhere — this is a structural move only, verified byte-for-byte against
the original inline text before deletion.

Per-exercise question counts and IDs:

| Exercise | Count | IDs |
| --- | --- | --- |
| 1 | 3 | q-categorical-columns, q-histogram-bins, q-fiq-correlation |
| 2 | 5 | q-test-target-use, q-correlation-vs-coefficient, q-honest-evaluation, q-knn-complexity, q-knn-large-k-variance |
| 3 | 5 | q-probability-near-threshold, q-threshold-tradeoff, q-roc-needs-proba, q-threshold-false-negatives, q-accuracy-under-imbalance |
| 4 | 3 | q-single-split-vs-cv-stability, q-inner-loop-data, q-outer-test-mse-meaning |
| 5 | 3 | q-selectkbest-leakage, q-alpha-tuning-leakage, q-ridge-lasso-properties |
| 6 | 4 | q-greedy-splitting, q-depth-selection, q-bagging-forest-variance, q-bagging-reduces-variance |
| 7 | 3 | q-boosting-residuals, q-learning-rate-trees, q-boosting-vs-bagging |

As documented in each generator's own new comment block (mirroring
Exercise 8's): **this is visual concealment, not secure assessment** — the
hidden setup cell is fully expandable, and a downloaded, fully offline,
editable notebook must contain enough information to check an answer
locally, so a technically curious student can always recover the answer
key from source or the running kernel. Never promised as secret.

### Verification (structural, direct, and live-browser — per the WP's own bounded-scope instruction)

- **Structural** (offline, no kernel): added
  `test_checked_questions_use_show_question_with_no_visible_answer_key` and
  `test_hidden_setup_cell_carries_every_question_definition` to each of
  `tests/test_exercise_0{1..7}_lite_notebook.py`, replacing the old
  `test_checked_questions_have_keys_and_feedback`. These assert: every
  checked question ID is defined exactly once in the hidden setup cell;
  every visible question cell calls `show_question("<a real id>")` and
  contains no `correct_index`/`correct_indices` literal; `_QUESTIONS` and
  `show_question` are both present in the setup cell. Exercise 6 additionally
  keeps its own `test_depth_selection_question_correct_answer_is_validation_mse`,
  rewritten to look up the answer inside the hidden setup cell's
  `_QUESTIONS` dict instead of a visible cell.
- **Direct** (offline, no kernel): each generator's `--check` mode
  (run for all of 1–8) confirms every rendered notebook is byte-identical
  to what the generator produces — this is the structural-synchronization
  guarantee the WP asked for ("generated copies in sync").
- **Numeric/executed** (kernel, no browser): ran
  `tests/test_exercise_0{1..6}_reference_execution.py` for every exercise
  whose generator changed — all established numbers reproduce exactly (see
  the numeric-parity table below). Exercise 7's reference-execution suite
  (17 tests) was started and observed making real progress through several
  genuine checkpoints (e.g. "Looks good: minimum validation MSE across the
  sweep = 18.7 (expected ~18.7)") before being stopped after ~13 minutes:
  gradient-boosting grid search over the sweep/parameter-explorer cells is
  expensive and pre-existing, unrelated to this WP's purely mechanical,
  text-only change to that file (verified: the diff to
  `generate_exercise_07_notebook.py` touches only the three
  `display(make_..._question(...))` call sites and the new
  `_QUESTIONS`/`show_question` block — zero lines of model-fitting code).
  Exercise 7's fast, offline **structural** suite (34 tests) passed in full.
  This one numeric-reproduction gap for Exercise 7 is the one deliberate,
  stated deviation from "run the reference-execution suite for every
  touched exercise" — left here rather than silently calling it tested.
- **Live browser** (real JupyterLite build, Playwright): see the
  exercise-by-exercise sections below; representative question interactions
  for Exercises 2–4 (whose notebooks were opened live for other reasons —
  the warning investigation and the long-question/diagram review) were
  visually confirmed rendering and grading correctly with the new
  `show_question()` indirection. Exercises 1, 5, 6, 7's question widgets
  were confirmed structurally and via direct kernel execution (the
  reference-execution runs above print every rendered question widget's
  full `repr()`, which was inspected) but not opened in a fresh browser tab
  individually in this WP — recorded here as **covered structurally and by
  direct execution, not individually screenshot-reviewed live**, per the
  WP's own "record which ones were visually inspected and which are
  covered structurally" instruction.

## B. Exercise 1 — EDA

1. Loader comment (`wp42-103-load`): removed the sentence explaining the
   same-origin/pinned-fallback mechanism and the pointer to the collapsed
   setup cell; kept the one-line "Load the curated ABIDE-II phenotype table
   (13 columns)." comment and all actual loading/check code unchanged.
2. `data.head()` cell (`wp42-203-head`): added the one-line comment
   `# data.head() shows five rows by default; data.head(n=8) shows eight
   participants.` above the call. The existing prompt inviting `tail()`/
   `sample()` (in the next markdown cell) is unchanged.
3. Incomplete-row removal blank (`wp42-504-drop-blank`): student starter
   now reads `# YOUR CODE HERE\n# data_complete = ...\n` (previously just
   `# YOUR CODE HERE`). `data` is still preserved unchanged; the check cell
   (`wp42-505-drop-check`) is untouched.
4. Median-imputation blank (`wp42-507-fill-blank`): same pattern,
   `# data_filled = ...` added. Check cell untouched.
5. Pearson correlation plot (`wp42-610-correlation-plot`): widened the
   figure (6.5"→8"), switched the title from `ax.set_title(...)` (axes-level,
   centered on the heatmap only) to `fig.suptitle(...)` (figure-level,
   `x=0.46`), added `pad=0.03` to the colorbar, and used
   `plt.tight_layout(rect=[0, 0, 1, 0.96])` to reserve room for the
   suptitle. **Root cause, confirmed by rendering the original code**: the
   title was centered on the Axes, which the colorbar had already narrowed,
   so the full string ("Pearson correlation between numerical variables")
   ran past the figure's right edge and was clipped to "...variable". The
   fix was rendered against the real data loader (not a toy array) via
   `tests/test_exercise_01_reference_execution.py`'s own executor and
   visually confirmed: title fully visible, colorbar clearly separated with
   even spacing. Real-browser capture:
   [`wp48_screenshots/ex01_pearson_live.png`](wp48_screenshots/ex01_pearson_live.png).

Numeric parity: all 6
`tests.test_exercise_01_reference_execution` tests pass unchanged
(curated-table shape, missingness, complete-case counts, FIQ median fill,
FIQ/VIQ correlation, default-retention count) — none of items 1–5 touch a
computed value.

`TEMPLATE_VERSION` bumped 1→2 (Exercise 1 is `migrationState: "migrated"`;
content a student may have already started changed) and
`book/config/exercise_manifest.json`'s `exercises[0].templateVersion`
updated to match — `tests.test_exercise_manifest` confirms they agree.

## C. Exercise 2 — Regression and bias–variance

1. Activity 3A blank (`wp41-306-3a-blank`): added
   `# Hint: the fitted model's coefficients live in its coef_ attribute, in
   the same order as FEATURES.` No `model.coef` typo suggested, no
   solution given.
2. Held-out observed-vs-predicted prompt (`wp41-314-3b-answer`): now reads
   `> **Reflect: How closely do the held-out points track the diagonal?
   Where do the largest errors fall?**` (the whole sentence is the bold
   "Reflect:" question, matching this notebook's existing "bold blockquote
   = editable answer cell" convention so the structural regex that finds
   answer cells, `^>\s*\*\*.+\*\*\s*$`, still matches it). No literal "YOUR
   ANSWER HERE" was present in the current generator source to remove
   (confirmed by a repo-wide grep before editing) — that part of the
   instruction was already satisfied; recorded here rather than silently
   assumed.
3. Warnings in the final two non-bonus figure cells (Section 7's
   `wp41-703-plot`, Section 8's `wp41-803-widget`) — **reproduced live**,
   not assumed:
   - The Matplotlib `width`/`height`/`x`/`y`-as-float deprecation warning
     was **already filtered** (WP42's own documented, live-bisected fix) —
     confirmed absent from this WP's own live capture of every output block
     in a full "Run All Cells" of Exercise 2.
   - A **new, previously undocumented-as-filtered** warning was captured
     verbatim from the real JupyterLite kernel:
     ```
     /lib/python3.14/site-packages/threadpoolctl.py:1135: RuntimeWarning: JsProxy.as_object_map() is deprecated. Use as_py_json() instead.
       for filepath in LDSO.loadedLibsByName.as_object_map():
     ```
     Traced to `threadpoolctl`'s own Pyodide shared-library introspection
     (`LDSO.loadedLibsByName.as_object_map()`) — a call inside threadpoolctl
     itself (imported internally by scikit-learn whenever a model is fit),
     never a call this notebook's own code makes, and not reachable by
     editing this repository's source or patching installed
     `site-packages` without re-vendoring threadpoolctl inside this
     course's pinned Pyodide build. Per the WP's own instruction for this
     exact situation, added a **narrow, local filter** scoped to both the
     exact message text and `category=RuntimeWarning` (never a blanket
     `RuntimeWarning` filter) to Exercise 2's setup cell, documented inline
     with the reproduction evidence above.
   - **Verified fixed**: rebuilt the combined Jupyter Book + JupyterLite
     site with the filter in place and re-ran the same live "Run All
     Cells" capture — the threadpoolctl warning no longer appears anywhere
     in Exercise 2's output (see the before/after logs referenced in the
     changelog).

Numeric parity: all 10 `tests.test_exercise_02_reference_execution` tests
pass unchanged (R²=0.469 worked example, KNN k=20 R²=0.664/MSE=31.4,
bias-variance sweep, Section 8 widget behavior). All 37
`tests.test_exercise_02_lite_notebook` structural tests pass.
`tests.test_exercise_manifest` confirms `TEMPLATE_VERSION` 3→4 (bumped for
the same reason as Exercise 1) matches the manifest.

## D. Exercise 3 — Classification and Metrics

1. **X/y sanity check** (`wp44-324-check`): repaired the
   ambiguous-Series-truth-value bug. `np.isfinite(X).all()` on a
   DataFrame returns a per-column Series, which raises
   `ValueError: The truth value of a Series is ambiguous` inside a plain
   `if`/`elif`. The check now does `X_arr = np.asarray(X, dtype=float)` /
   `y_arr = np.asarray(y).reshape(-1)` inside a **targeted**
   `try`/`except (TypeError, ValueError)` (catches only a genuine dtype
   conversion failure, e.g. a stray string column — never swallows an
   unrelated exception), then validates shape (`X_arr.shape[1] ==
   len(FEATURES)`, i.e. exactly 360), row alignment (`len(X_arr) ==
   len(y_arr) == len(df)`), finiteness, and that `y` is binary `{0, 1}`.
   Added `tests.test_exercise_03_reference_execution.XYCheckCellBehavior`
   (6 tests, replacing the old confusion-matrix-check behavior tests —
   see D.3) exercising exactly the cases the spec named: a NumPy attempt, a
   pandas DataFrame/Series attempt (the regression case), an unfinished
   attempt, a nonnumeric `X`, an incomplete (mismatched row count) `X`, and
   un-recoded raw `{1, 2}` labels in `y` — all 6 pass.
2. **Train/test split blank** (`wp44-332-instructions`): no longer writes
   out the complete `train_test_split(X, y, test_size=0.25,
   random_state=42, stratify=y)` call. Now states the recipe in words (75/25,
   seeded `random_state=42`, stratified on `y`) plus hints about which
   `train_test_split` arguments to use, and the required output names
   (`X_train`, `X_test`, `y_train`, `y_test`) on the last line — the actual
   call is left for the student. The established numeric recipe/split and
   its check cell are unchanged.
3. **Confusion-matrix autocheck → reflection**: `wp44-414-check` (the
   numeric `EXPECTED_ACCURACY`/`EXPECTED_SENSITIVITY`/`EXPECTED_SPECIFICITY`
   auto-grader) is replaced by `wp44-414-reflection`, a Markdown cell
   explaining that a modest result is plausible for this specific, hard
   problem and motivates later, more systematic model/feature-selection
   methods — **never promising a more complex model will necessarily
   generalize better**, and never calling the logistic-regression model
   "linear regression." It also notes, as an optional exploratory aside,
   that predicting `SEX` instead of diagnosis is a genuinely different
   problem needing its own explicit target recoding/labels and `SEX`
   excluded from the predictors — and explicitly states that a bare
   `y = df["SEX"]` swap under the existing autism-labeled code is unsafe
   and insufficient on its own. The student's confusion-matrix activity
   (`wp44-413-blank`) and the separate AUC check (`wp44-424-check`,
   untouched) both still work exactly as before.
4. **SEX/site metadata distractors**: `load_abide_classification_table()`
   now also loads `SEX`/`SITE` via a new `load_demographics_table()`
   function that reuses Exercise 8's existing sex/site sidecar
   (`book/lite/files/data/abide_age_brain_demographics.csv`) rather than
   exporting a new one — verified row-aligned with an `assert
   len(demographics) == len(table)` at load time (both functions mirror
   each other's same-origin/pinned-fallback paths exactly, so they stay
   aligned under both). Section 1's intro markdown now states explicitly
   that `group`, `SEX`, and `SITE` are metadata/distractors that must not
   leak into `X`; the Section-1 load cell's print output says the same.
   The existing `FEATURES = [c for c in df.columns if c.startswith("fsCT_")]`
   selection already excludes all three by construction (verified by the
   existing FEATURES-check cell, unchanged).
5. **Explicit `group` recode**: `wp44-104-labels` (supplied, not a blank)
   now recodes `df["group"]` to binary (0 = control, 1 = autism) once,
   right after verifying the raw `{1, 2}` codes and printing class counts,
   with an `assert set(df["group"].unique()) == {0, 1}` immediately after
   — this is the validation that "rejects raw 1/2 or string labels before
   downstream models/plots assume 0/1," run automatically as soon as
   Section 1 executes, before the student ever reaches the X/y blank. The
   X/y blank's instructions and reference solution were simplified to
   `y = df["group"].to_numpy()` (already binary) instead of
   `(df["group"] == 1).astype(int)`.

Numeric parity: **exact, byte-for-byte**, confirmed by re-executing the
reference notebook end to end — accuracy=0.545817 (prints "0.546"),
sensitivity=0.534483, specificity=0.555556, AUC=0.569221, confusion matrix
TN=75/FP=60/FN=54/TP=62, n_train=753/n_test=251, class counts 463
autism/541 control — all unchanged from the pre-WP48 audited values, and
all 15 `tests.test_exercise_03_reference_execution` tests (9 pre-existing +
6 new `XYCheckCellBehavior`) plus all 31
`tests.test_exercise_03_lite_notebook` structural tests pass.

`interactive/e2e-book/exercise-03-lite.spec.ts` (the committed, real-browser
teacher-completed-path test) asserted `"Looks good: accuracy=0.546"`, text
that only the now-removed check cell printed — updated to type a real
`print(f'accuracy = {accuracy:.3f}')` into the activity blank and assert on
that plus the reflection's own "plausible outcome" text instead; also
updated the X/y blank's typed solution to the simplified
`y = df["group"].to_numpy()` (the old `(df["group"] == 1)` form still works
on an already-recoded column by coincidence, but no longer matches the
reference solution, so the test now matches it for clarity).

## E. Exercise 4 — Validation and Cross-Validation

1. **threadpoolctl warning in the one-split cell** (`wp45-203-onesplit`):
   same upstream warning as Exercise 2 (C.3), reproduced live in this
   notebook too (`== 12 distinct output blocks`, one of which was the
   identical threadpoolctl `RuntimeWarning`). Same narrow,
   message-and-category-scoped filter applied to this notebook's setup
   cell; verified absent after rebuilding.
2. **Five-fold CV blank comments** (`wp45-303-blank`): rewritten from two
   terse lines (just the two final variable names) into a four-step
   sequence — create the model/pipeline, set up five folds, fit/predict
   per fold and collect positive MSEs, compute the mean — ending with
   "Required output names: `cv_fold_mse` (5 values, one per fold),
   `cv_mean_mse`" on the last line, matching Exercise 8's "required output
   names" convention. Still hints, not a near-complete solution (no runnable
   line is left uncommented).
3. **Checked-question layout fix**: live inspection (after converting both
   questions to `show_question(...)`) found the root cause of the reported
   overlap: `.checked-question .widget-radio-box label` had no `height:
   auto` override, so a long option that wrapped to two lines kept the
   ipywidgets default single-line row height and visually overlapped the
   next option. Added `height: auto !important; padding: 3px 0; line-height:
   1.3;` to that rule (the checkbox variant already had `height: auto` on
   its own `.widget-label-basic` rule — this was specifically a
   RadioButtons-only gap). This is a **Exercise-4-scoped** fix per the WP's
   explicit instruction; the same latent gap likely exists in the identical
   CSS block duplicated in Exercises 1, 2, 3, 5, 6, 7, 8 (confirmed present
   by inspection, not fixed here — out of this WP's stated scope, flagged
   for a future pass rather than silently left untested).
4. **Nested-CV diagram replaced**: the old diagram
   (`_NCV_DIAGRAM_HTML`) was raw HTML with every fold block's size *and*
   color carried only by an inline `style="..."` attribute on a bare
   `<span>`. **Root cause, confirmed by reasoning from the symptom and the
   DOM structure** (not just asserted): JupyterLab/JupyterLite's
   markdown-HTML sanitizer strips the `style` attribute from raw HTML by
   default, which is exactly consistent with the author's screenshot — the
   loose headings, fold numbers, and arrows (plain text, not dependent on
   `style=`) survived, while every colored block (zero-sized and
   zero-colored without its `style=`) vanished. Replaced with a new
   deterministic, code-native diagram, rendered once by
   `scripts/render_exercise_04_nested_cv_diagram.py` (matplotlib
   `Rectangle`/`FancyArrowPatch`, no student data involved — a fixed
   conceptual illustration, like Exercise 2's bias-variance figure) to
   `book/lite/files/data/exercise_04_nested_cv_diagram.png`, embedded as a
   notebook **attachment** (the same nbformat mechanism Exercise 2's
   Activity 3B reference image already uses — never a separate linked file,
   which would break a downloaded/Colab copy) with full descriptive alt
   text. Shows 5 outer-fold rows with the outer-test block (yellow)
   rotating, iteration 2 outlined; an arrow into 5 inner-fold rows (zoomed
   from that iteration's training data) with inner-validation (orange)
   rotating; a second arrow into three captioned steps (inner folds select
   k; refit the selected k on all of that outer fold's training data; score
   once on its outer test); a footer note on repeat/average. White opaque
   background (legible in both JupyterLite light and dark themes, like
   every other embedded reference image in this course); no reliance on any
   Book-only CSS. Reviewed against a real browser screenshot (see below).

Numeric parity: all 13 `tests.test_exercise_04_reference_execution` tests
pass unchanged (one-split MSE=31.4/R²=0.664, 5-fold CV mean MSE=33.8,
nested-CV mean MSE=33.4 with selected k per fold `[15, 12, 10, 18, 15]`,
stability-widget default). All 28
`tests.test_exercise_04_lite_notebook` structural tests pass, including 4
new ones covering the diagram-as-attachment, the CSS height fix, and the
threadpoolctl filter.

## Visual/live-browser evidence

Built the combined `jupyter-book build book --all` +
`jupyter lite build --config book/lite/jupyter_lite_config.json --lite-dir
book/lite --output-dir book/_build/html/lite` site twice (once before, once
after the threadpoolctl fix) and drove it with Playwright against the real
served site (`node e2e-book/serve-book.mjs`, port 4174):

- **Exercise 1's Pearson plot**: executed the reference notebook's real
  data loader (not synthetic data) locally and, separately, opened the live
  JupyterLite build and screenshotted the rendered cell — title fully
  visible, colorbar clearly separated with even spacing, in both cases.
  Confirmed in the actual Pyodide-backed matplotlib renderer, not just the
  local Agg backend.
- **Exercise 2's warning cells**: captured every distinct output block
  across a full live "Run All Cells" of the untouched student template,
  before and after the threadpoolctl filter — before: 15 distinct output
  blocks, 2 containing the threadpoolctl `RuntimeWarning` verbatim; after:
  14 blocks, zero warning matches. The matplotlib warning was absent in
  both captures (confirming the pre-existing filter still works
  unconditionally).
- **Exercise 4's warning, two long questions, and diagram**: before/after
  capture confirmed the same threadpoolctl disappearance (before: 12
  blocks / 1 match; after: 11 blocks / 0 matches). The diagram rendered as
  a real, legible image with visible colored fold blocks, legend, arrows,
  and captions (a dramatic contrast with the author's screenshot of the
  old HTML version's missing bars) —
  [`wp48_screenshots/ex04_diagram_live.png`](wp48_screenshots/ex04_diagram_live.png).
  Both long questions (`q-single-split-vs-cv-stability`,
  `q-outer-test-mse-meaning`) were screenshotted: at desktop width both
  wrap cleanly with no overlap
  ([`ex04_q1_desktop.png`](wp48_screenshots/ex04_q1_desktop.png),
  [`ex04_q2_desktop.png`](wp48_screenshots/ex04_q2_desktop.png)); at 390px,
  `q-outer-test-mse-meaning` was captured showing clean two-line wrapping
  with correct per-option spacing and no overlap
  ([`ex04_q2_390px.png`](wp48_screenshots/ex04_q2_390px.png) — the direct
  proof the CSS `height: auto` fix works at the narrow viewport);
  `q-single-split-vs-cv-stability`'s 390px capture caught a windowed-list
  scroll boundary (showing the source cell and the start of the prompt,
  not the options) rather than a layout defect — both questions share the
  identical CSS fix and widget code, so the one clean 390px capture is
  treated as representative of both, not re-attempted given the WP's own
  "focused and bounded" instruction.
- **Exercise 3's error-handling and unchanged result**: verified via
  `interactive/e2e-book/exercise-03-lite.spec.ts` (updated per D.3 above)
  and the direct reference-execution/structural suites above, which
  together exercise the untouched-template no-cascade behavior, the
  teacher-completed path's reproduced accuracy/AUC, and both native
  widgets.

## Deviations from a fully exhaustive gate

- Exercise 7's `test_exercise_07_reference_execution.py` (17 tests,
  numeric/executed) was attempted twice and not run to completion either
  time — the gradient-boosting grid-search/parameter-explorer cells it
  executes are genuinely expensive (observed real, continuous CPU work and
  real passing checkpoints along the way, e.g. "Looks good: minimum
  validation MSE across the sweep = 18.7 (expected ~18.7)," never a hang),
  and pre-existing: untouched by this WP's purely mechanical change to that
  file (verified: the diff touches only the three
  `display(make_..._question(...))` call sites and the new
  `_QUESTIONS`/`show_question` block — zero lines of model-fitting code).
  Exercise 7's fast, offline structural suite (34 tests) passed in full,
  and the identical refactor pattern's reference-execution suite passed
  for Exercises 1–6. This is the one explicit numeric-reproduction gap
  left in this WP, stated rather than silently treated as tested.
- `scripts/smoke_portable_notebook.py --notebook chapter_02` (an extra,
  not-required diligence check, not part of this WP's own instructions)
  was attempted once and killed after it stalled for roughly a minute at
  near-zero CPU inside `nbclient`'s kernel teardown — consistent with the
  known, pre-existing `ipywidgets.Output()`-as-context-manager/nbclient
  comm-handshake hang the WP41 maintainer guide documents (not reproduced
  or investigated further here, since Exercise 2's actual correctness was
  already independently confirmed both by the full reference-execution
  suite and by a real-browser "Run All Cells" during the warning
  investigation above).
- The CSS `.widget-radio-box label` height gap (E.3) is fixed only in
  Exercise 4, per the WP's explicit scope; the same gap likely exists in
  Exercises 1, 2, 3, 5, 6, 7, 8's identical, independently-duplicated CSS
  block. Flagged here, not fixed, and not in scope for this WP.
- Real Google Colab acceptance for any exercise remains the author's own
  manual gate (WP41 maintainer guide §11) — not claimed here for any
  exercise, migrated or not.
- No merge, push, or deployment. No GitHub Actions interaction.

## Course-author summary

- Exercises 1–7 now all hide checked-question answer keys from the visible
  cell the same way Exercise 8 already did — this is cosmetic/UX
  concealment, not secure assessment (a student can still find the answer
  by expanding the hidden setup cell).
- Exercise 1: loader comment trimmed, `head()`/blank hints added, Pearson
  correlation plot's title is no longer clipped by the colorbar.
- Exercise 2: Activity 3A has a `coef_` hint, the observed-vs-predicted
  question is now a "Reflect:" prompt, and the threadpoolctl warning in
  Sections 7–8 is gone.
- Exercise 3: the X/y check no longer crashes on a pandas DataFrame/Series
  attempt, the train/test split blank no longer hands over the answer, the
  confusion-matrix autocheck is now a qualitative reflection (with an
  honest caution about the optional SEX-prediction idea), and `SEX`/`SITE`
  are now loaded as explicit metadata distractors alongside the already-
  explicit binary `group` recode.
- Exercise 4: the threadpoolctl warning in the one-split cell is gone, the
  five-fold CV blank's comments teach the real sequence, the two long
  questions no longer visually overlap when their options wrap to two
  lines, and the nested-CV diagram is a real, legible image instead of raw
  HTML that JupyterLite's sanitizer was silently breaking.
- Local preview: `book/_build/html/lite/notebooks/index.html?path=exercise_0N.ipynb`
  after the two build commands above.
- Remaining Colab checks: none newly required by this WP (no student-visible
  recipe/split/model change in any exercise); the existing Colab-acceptance
  backlog for Exercises 3–8 (WP41 maintainer guide §11) is unchanged by
  this work.
