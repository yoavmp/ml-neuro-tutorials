# WP48 exact changelog

Starting SHA (local `main`): `9195865` ("WP47: reports — execution report
and exact changelog"), matching `origin/main`.

Checkpoint: branch `checkpoint/wp48-pre-work`, at the tip of
`feature/wp47-active-exercise-8-unsupervised-learning` (`9195865`).

Feature branch: `feature/wp48-questions-and-exercises-1-4-polish`, created
from that same tip.

Commits made by this WP, in order:
1. `faba9ce` — checkpoint the WP spec on the dedicated feature branch.
2. `08188a8` — question-display migration for Exercises 1–7 + the itemized
   Exercises 1–4 fixes (47 files changed, +4268/-1898; see
   `git show --stat 08188a8` for exact per-file counts).
3. This report + this changelog (committed together as this WP's closing
   commit; see `git log -1` after that commit for the final SHA).

No merge, no push, no deployment, no GitHub Actions interaction at any
point.

## Changed/added files

```
M  book/config/exercise_manifest.json
M  book/downloads/chapter_01/exercise_01_portable.ipynb
M  book/downloads/chapter_02/exercise_02_portable.ipynb
M  book/downloads/chapter_03/exercise_03_portable.ipynb
M  book/downloads/chapter_04/exercise_04_portable.ipynb
M  book/downloads/chapter_05/exercise_05_portable.ipynb
M  book/downloads/chapter_06/exercise_06_portable.ipynb
M  book/downloads/chapter_07/exercise_07_portable.ipynb
A  book/lite/files/data/exercise_04_nested_cv_diagram.png
M  book/lite/files/exercise_01.ipynb
M  book/lite/files/exercise_01_portable.ipynb
M  book/lite/files/exercise_02.ipynb
M  book/lite/files/exercise_02_portable.ipynb
M  book/lite/files/exercise_03.ipynb
M  book/lite/files/exercise_03_portable.ipynb
M  book/lite/files/exercise_04.ipynb
M  book/lite/files/exercise_04_portable.ipynb
M  book/lite/files/exercise_05.ipynb
M  book/lite/files/exercise_05_portable.ipynb
M  book/lite/files/exercise_06.ipynb
M  book/lite/files/exercise_06_portable.ipynb
M  book/lite/files/exercise_07.ipynb
M  book/lite/files/exercise_07_portable.ipynb
M  interactive/e2e-book/exercise-03-lite.spec.ts
M  scripts/generate_exercise_01_notebook.py
M  scripts/generate_exercise_02_notebook.py
M  scripts/generate_exercise_03_notebook.py
M  scripts/generate_exercise_04_notebook.py
M  scripts/generate_exercise_05_notebook.py
M  scripts/generate_exercise_06_notebook.py
M  scripts/generate_exercise_07_notebook.py
A  scripts/render_exercise_04_nested_cv_diagram.py
M  scripts/reference_notebooks/exercise_01_reference.ipynb
M  scripts/reference_notebooks/exercise_02_reference.ipynb
M  scripts/reference_notebooks/exercise_03_reference.ipynb
M  scripts/reference_notebooks/exercise_04_reference.ipynb
M  scripts/reference_notebooks/exercise_05_reference.ipynb
M  scripts/reference_notebooks/exercise_06_reference.ipynb
M  scripts/reference_notebooks/exercise_07_reference.ipynb
M  tests/test_exercise_01_lite_notebook.py
M  tests/test_exercise_02_lite_notebook.py
M  tests/test_exercise_03_lite_notebook.py
M  tests/test_exercise_03_reference_execution.py
M  tests/test_exercise_04_lite_notebook.py
M  tests/test_exercise_05_lite_notebook.py
M  tests/test_exercise_06_lite_notebook.py
M  tests/test_exercise_07_lite_notebook.py
A  WPs/reports/WP48_REPORT.md
A  WPs/reports/wp48_screenshots/ex01_pearson_live.png
A  WPs/reports/wp48_screenshots/ex04_diagram_live.png
A  WPs/reports/wp48_screenshots/ex04_q1_desktop.png
A  WPs/reports/wp48_screenshots/ex04_q2_desktop.png
A  WPs/reports/wp48_screenshots/ex04_q2_390px.png
A  WPs/reports/WP48_EXACT_CHANGELOG.md
```

45 files changed (pre-report commit), +4065/-1898 (`git show --stat` on the
working commit has the exact per-file counts).

## Why each file changed

- `scripts/generate_exercise_0{1..7}_notebook.py` — the single authoritative
  source for each exercise's student/portable/reference notebooks. Every
  one of the 7 files got the Part A `show_question()` migration (new
  `_QUESTIONS` dict + `show_question(question_id)` function inside the
  hidden setup cell; every visible checked-question cell now calls
  `show_question("q-id")` instead of `display(make_..._question(...,
  correct_index=...))`). In addition:
  - `generate_exercise_01_notebook.py` — B.1–B.5 (loader comment trim,
    `head()` note, `data_complete`/`data_filled` starter hints, Pearson
    plot colorbar/title fix); `TEMPLATE_VERSION` 1→2.
  - `generate_exercise_02_notebook.py` — C.1–C.3 (Activity 3A `coef_` hint,
    3B prompt → "Reflect:", threadpoolctl warning filter added alongside
    the pre-existing matplotlib filter); `TEMPLATE_VERSION` 3→4.
  - `generate_exercise_03_notebook.py` — D.1–D.5 (X/y check rewritten to
    avoid the ambiguous-Series-truth-value crash, split-blank instructions
    no longer hand over the answer, confusion-matrix autocheck replaced by
    a qualitative reflection, SEX/SITE loaded as metadata distractors via a
    new `load_demographics_table()` reusing Exercise 8's sidecar, explicit
    binary `group` recode + validation moved into Section 1).
  - `generate_exercise_04_notebook.py` — E.1–E.4 (threadpoolctl warning
    filter, five-fold CV blank's comments rewritten to teach the sequence,
    `.widget-radio-box label` CSS gains `height: auto` so wrapped long
    options don't overlap, the old raw-HTML nested-CV diagram replaced by
    an attachment-embedded rendered image).
  - `generate_exercise_05_notebook.py`, `generate_exercise_06_notebook.py`,
    `generate_exercise_07_notebook.py` — Part A only; no other content
    change (Part A's own scope note: "do not preemptively revise their
    lesson content" for 5–8).
- `scripts/render_exercise_04_nested_cv_diagram.py` — new: the dedicated
  script (mirroring `scripts/render_exercise_02_reference_plot.py`'s
  pattern) that renders the new nested-CV diagram to
  `book/lite/files/data/exercise_04_nested_cv_diagram.png` from matplotlib
  patches — a fixed conceptual illustration, no student data involved.
- `book/lite/files/data/exercise_04_nested_cv_diagram.png` — new: the
  rendered diagram, embedded as a notebook attachment in
  `wp45-503-diagram`.
- `book/lite/files/exercise_0{1..7}.ipynb`,
  `book/lite/files/exercise_0{1..7}_portable.ipynb`,
  `book/downloads/chapter_0{1..7}/exercise_0{1..7}_portable.ipynb`,
  `scripts/reference_notebooks/exercise_0{1..7}_reference.ipynb` —
  regenerated (`--write`) from the generators above; byte-for-byte what
  each generator's `--check` mode verifies.
- `book/config/exercise_manifest.json` — `templateVersion` bumped for
  Exercise 1 (1→2) and Exercise 2 (3→4), the two `migrationState:
  "migrated"` entries whose student-visible template content changed;
  Exercises 3–7 stay `"legacy"` (Colab-acceptance-pending, unchanged by
  this WP) so no manifest field for them needed touching.
- `interactive/e2e-book/exercise-03-lite.spec.ts` — the teacher-completed-
  path test asserted `"Looks good: accuracy=0.546"`, text only the now-
  removed numeric autocheck cell printed; updated to type a real
  `print(f'accuracy = {accuracy:.3f}')` into the activity blank and assert
  on that plus the new reflection cell's own text instead. Also updated the
  X/y blank's typed solution from `y = (df["group"] == 1).astype(int)` to
  the simplified `y = df["group"].to_numpy()` matching the new reference
  solution (the old form still happens to work on an already-recoded
  column, but no longer matches what a student/teacher is actually asked
  to write).
- `tests/test_exercise_0{1,2,4,5,6,7}_lite_notebook.py` — replaced
  `test_checked_questions_have_keys_and_feedback` with
  `test_checked_questions_use_show_question_with_no_visible_answer_key`
  and `test_hidden_setup_cell_carries_every_question_definition` in each
  (Part A's own structural-check requirement); Exercise 6 additionally
  keeps `test_depth_selection_question_correct_answer_is_validation_mse`,
  rewritten to look inside the hidden setup cell instead of a visible one.
  Exercise 4 also gained `test_threadpoolctl_warning_narrowly_filtered`,
  `test_question_radio_labels_do_not_clip_wrapped_rows`, and a rewritten
  `test_nested_cv_conceptual_diagram_present` (now checks for the
  attachment + alt text, not the old `ml-ncv-diagram` HTML class).
  Exercise 2 also gained `test_threadpoolctl_warning_narrowly_filtered`.
  Exercise 1 and 3's edits are Part A only plus (for 3) the items below.
- `tests/test_exercise_03_lite_notebook.py` — Part A's two new tests, plus
  D.4/D.5 coverage (`test_sex_and_site_loaded_as_metadata_distractors`,
  `test_group_is_explicitly_recoded_to_binary_before_xy_activity`) and D.3
  coverage (`test_confusion_matrix_reflection_replaces_the_numeric_autocheck`);
  `test_established_metrics_referenced_in_checks` narrowed to
  `test_established_auc_referenced_in_its_check` (the removed check cell's
  accuracy/sensitivity/specificity literals are gone by design).
- `tests/test_exercise_03_reference_execution.py` — `MetricsCheckCellBehavior`
  (which exercised the now-removed `wp44-414-check`) replaced by
  `XYCheckCellBehavior` (6 tests), exercising the repaired X/y check cell
  against exactly the cases D.1 named: NumPy, pandas DataFrame/Series,
  unfinished, nonnumeric, incomplete (row-count mismatch), and un-recoded
  raw `{1, 2}` labels.
- `WPs/reports/WP48_REPORT.md`, `WPs/reports/WP48_EXACT_CHANGELOG.md` — new:
  this report and this changelog.
- `WPs/reports/wp48_screenshots/*.png` (5 files) — new: live-browser
  visual evidence (Exercise 1's fixed Pearson plot, Exercise 4's new
  diagram, both long questions at desktop and one at 390px), following the
  same `WPs/reports/wp16_screenshots/`/`wp22_screenshots/` convention this
  repo already uses for before/after visual proof.

## Numeric parity summary

| Exercise | Check | Established value | This WP | Match |
| --- | --- | --- | --- | --- |
| 1 | curated table / missingness / FIQ median / FIQ-VIQ r / retention | (unchanged) | (unchanged) | exact — none of B.1–B.5 touch a computed value |
| 2 | worked-example R² | 0.469 | 0.469 | exact |
| 2 | KNN k=20 | R²=0.664, MSE=31.4 | R²=0.664, MSE=31.4 | exact |
| 3 | accuracy / sensitivity / specificity | 0.545817 / 0.534483 / 0.555556 | 0.545817 / 0.534483 / 0.555556 | exact |
| 3 | AUC | 0.569221 | 0.569221 | exact |
| 3 | confusion matrix | TN=75 FP=60 FN=54 TP=62 | TN=75 FP=60 FN=54 TP=62 | exact |
| 3 | split sizes / class counts | n_train=753 n_test=251; 463 autism/541 control | same | exact |
| 4 | one-split KNN(k=20) | MSE=31.4 R²=0.664 | MSE=31.4 R²=0.664 | exact |
| 4 | 5-fold CV mean | MSE=33.8 | MSE=33.8 | exact |
| 4 | nested CV | mean outer MSE=33.4, k per fold [15,12,10,18,15] | same | exact |
| 5 | SelectKBest / Ridge / Lasso / Lasso-CV | (unchanged) | (unchanged) | exact — Part A only |
| 6 | single tree / bagging / Random Forest | mean MSE 56.7/32.8/34.1 | same | exact — Part A only |
| 7 | structural suite (34 tests) | — | OK | Part A only; see Deviations for the reference-execution gap |

## Test/build evidence

- Offline structural suites, all 7 exercises + manifest:
  **230 tests, OK**, 0.3s
  (`tests.test_exercise_0{1..7}_lite_notebook` + `tests.test_exercise_manifest`).
- Offline reference-execution suites, Exercises 1–5:
  **58 tests, OK**, 54.7s.
- Offline reference-execution suite, Exercise 6: **12 tests, OK**, 92.4s.
- Offline reference-execution suite, Exercise 3's new `XYCheckCellBehavior`:
  **6 tests, OK** (included in the 15-test Exercise-3 total above).
- Offline reference-execution suite, Exercise 7 (17 tests): see Deviations
  — not completed; structural suite (part of the 229 above) passed.
- Offline content-audit suite (`test_wp19/24/25_content_audit`,
  `test_notebook_opening_structure`): **61 tests, OK**, 0.2s — confirms
  Exercises 1–4's changes didn't disturb any older cross-reference.
- `jupyter-book build book --all`: succeeded, 2 pre-existing warnings.
- `jupyter lite build`: succeeded.
- Live JupyterLite build, Playwright, real browser (Chromium headless):
  - Exercise 2, full "Run All Cells": threadpoolctl `RuntimeWarning`
    present before the fix (verbatim text captured), confirmed **absent**
    after rebuilding with the fix (14 distinct output blocks, zero
    warning-like text; was 15 blocks / 2 warning matches before).
  - Exercise 4, full "Run All Cells": same warning present before,
    confirmed **absent** after (11 blocks, zero matches; was 12 / 1 match
    before).
  - Exercise 1's Pearson-correlation cell and Exercise 4's nested-CV
    diagram + both long questions (desktop and 390px): screenshotted
    against the live build (see the report's "Visual/live-browser
    evidence" section for what each capture showed).
  - `interactive/e2e-book/exercise-03-lite.spec.ts`: updated per the
    changelog entry above; the committed Exercise 1/2/4 Playwright spec
    files were not run in full in this WP (ad-hoc, narrower live-browser
    scripts were used instead, per the WP's own "focused and bounded"
    instruction — see the report's Deviations section).

## Confirmation

No merge, no push, no deployment, no GitHub Actions interaction.
`Homework_Materials/` untouched. Exercises 8–12's own content untouched.
Exercise 8's generator untouched (no demonstrated compatibility issue
required touching it). The shared `abide_age_brain.csv`/`.manifest.json`
and `abide_age_brain_demographics.csv`/`.manifest.json` exports are
byte-for-byte unmodified (Exercise 3 reuses, never re-exports, the
Exercise-8 sidecar).
