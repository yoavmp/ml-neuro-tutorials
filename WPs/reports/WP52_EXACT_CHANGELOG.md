# WP52 exact changelog

Starting SHA (local `feature/wp51-active-exercise-09`, matching its own
report): `14fb73e`. Branched from `main` at `c5acbe3` originally (WP51).

Checkpoint branch: `checkpoint/wp52-pre-work`, at `14fb73e`, created before
any WP52 edit.

One commit on the feature branch: `2e18798` ("WP52: Exercise 9 review
fixes (all 15 items) and publication"). That branch, already an
undiverged descendant of `main`, was then fast-forward-merged into `main`
(`git checkout main && git merge --ff-only feature/wp51-active-exercise-09`)
and pushed (`git push origin main`, `c5acbe3` -> `2e18798`, no merge
commit). This report + this changelog are added together as a separate,
`WPs/**`-only closing commit (paths-ignore keeps it from triggering another
deploy).

## Files changed (commit `2e18798`)

```
M  .github/workflows/deploy.yml
M  .github/workflows/legacy-notebook-smoke.yml
A  WPs/WP52_EXERCISE_09_REVIEW_FIXES_AND_RELEASE.md
M  book/_config.yml
M  book/_static/launch-buttons.js
M  book/_toc.yml
M  book/chapters/chapter_09/exercise_09.ipynb
M  book/config/exercise_manifest.json
M  book/downloads/chapter_09/exercise_09_portable.ipynb
M  book/lite/files/exercise_09.ipynb
M  book/lite/files/exercise_09_portable.ipynb
D  interactive/e2e-book/chapter09-dark-mode.spec.ts
M  interactive/e2e-book/chapter09.spec.ts
A  interactive/e2e-book/exercise-09-lite.spec.ts
M  interactive/e2e-book/launch-buttons.spec.ts
M  interactive/playwright.book.config.ts
M  scripts/classify_release_change.py
A  scripts/compute_exercise_09_svr_benchmark.py
M  scripts/generate_exercise_09_notebook.py
A  scripts/generate_exercise_09_transition_page.py
M  scripts/reference_notebooks/exercise_09_reference.ipynb
A  scripts/reference_notebooks/exercise_09_svr_benchmark.json
M  tests/test_book_structure.py
M  tests/test_classify_release_change.py
M  tests/test_exercise_09_lite_notebook.py
D  tests/test_exercise_09_notebook.py
M  tests/test_exercise_09_reference_execution.py
A  tests/test_exercise_09_svr_benchmark.py
A  tests/test_exercise_09_transition_page.py
M  tests/test_exercise_manifest.py
```
30 files changed, 3175 insertions(+), 4085 deletions(-) (`git show --stat
2e18798`).

## Per-file summary

- **`scripts/generate_exercise_09_notebook.py`** (~1770 lines, the sole
  generator for all four of Exercise 9's derived notebooks): all 15 review
  items implemented here. Title; `_WIDGET_CONTROL_CSS` +
  `_widget_control_style_widget()` + `controls_row()` (new, applied to both
  native widgets); `make_multi_choice_question()` (new, the "mark all
  correct" SVM/SVR question); `show_question()` rewritten to shuffle each
  question's displayed order from a per-question `shuffle_seed` before
  building its widget; `_QUESTIONS` reduced from 6 to 5 entries (`q-pcr-vs-pls`,
  `q-leakage`, `q-c-gamma-epsilon` [now `type="multi"`], `q-train-vs-val`,
  `q-exact-vs-approx`; `q-knn-trees` removed with its own section, see
  below); PCR/PLS blanks rewritten (exact required starter shape, prose
  hints only, `val_r2` added to both schemas and both check cells, with a
  new `R2_TOLERANCE`); the PCR-vs-PLS widget rewritten (`_pcrpls_fit_and_score`
  split out so the global-max MSE can be precomputed once;
  `_PCRPLS_MSE_YLIM`; target-colored scatter; `signal_dir`/`pls_dir`
  arrows); Section 4's "A compact SVC example" cells removed, with
  `make_svc_dataset` relocated into the SVM activity's own cell; SVR blank
  rewritten (prose hint, GridSearchCV comment, no disguised solution);
  Section 5's kernel-application table and the Lasso/logistic/KNN/trees
  tail removed (cells through `q-knn-trees`); Ridge-vs-KernelRidge intro
  rewritten without the table, with the "no identical-predictions" caveat;
  that blank rewritten (hint only); Section 6 (`_section_6_compare_and_reflect`)
  rewritten to take the benchmark dict as a parameter, embed it as
  `SVR_BENCHMARK`, compare on full training data only, print the student's
  own subset result separately, use `set_xticks` before `set_xticklabels`,
  and drop the historical `<details>` block entirely. New module-level
  `SVR_BENCHMARK_PATH`/`_svr_benchmark()`, `EXPECTED_PCR_R2`/`EXPECTED_PLS_R2`;
  removed `LASSO_ALPHA`/`RBF_SAMPLER_*`/`RBF_LOGISTIC_*` (dead after the
  Section 5 cut).
- **`scripts/compute_exercise_09_svr_benchmark.py`** (new, 133 lines):
  offline, reproducible computation of the full-training-data instructor
  SVR benchmark (library-default `SVR()`, same split as every other model),
  `--write`/`--check` modes, writes the committed JSON artifact.
- **`scripts/reference_notebooks/exercise_09_svr_benchmark.json`** (new):
  that artifact -- `val_mse=54.083`, `val_r2=0.421`, `n_train=753`,
  `n_val=251`, `n_features=360`, the exact split parameters, and
  `params_chosen_without_validation_tuning: true`. `fit_seconds` is
  deliberately **not** persisted (wall-clock timing isn't reproducible;
  printed at compute time only, to keep `--check` deterministic).
- **`scripts/generate_exercise_09_transition_page.py`** (new, 92 lines):
  Exercise 9's own transition-page generator, modeled byte-for-byte on
  `generate_exercise_08_transition_page.py`.
- **`book/lite/files/exercise_09.ipynb`**, **`exercise_09_portable.ipynb`**,
  **`book/downloads/chapter_09/exercise_09_portable.ipynb`**,
  **`scripts/reference_notebooks/exercise_09_reference.ipynb`**: all four
  regenerated from the corrected generator (`--write`); 48 cells (down
  from 60), 4 required blanks (down from 5 required + 1 optional).
- **`book/chapters/chapter_09/exercise_09.ipynb`**: the old 65KB legacy
  nested-CV notebook replaced by the new transition page's 2-cell output
  (`--write` from the new transition-page generator).
- **`book/config/exercise_manifest.json`**: Exercise 9's entry flipped to
  `migrationState: "migrated"` with real `templateNotebookPath`/
  `browserWorkingCopyName`/`liteUrl`/`templateVersion: 1`/`dataAssets`;
  `$comment` updated.
- **`book/_toc.yml`**: `chapters/chapter_09/exercise_09` added; comment
  updated to "Exercises 10-12".
- **`book/_config.yml`**: `chapters/chapter_09/*` removed from
  `exclude_patterns`; comment updated.
- **`book/_static/launch-buttons.js`**: `chapter_09` entry removed from
  `PAGE_TO_PORTABLE`; header comment updated (lists Exercise 9's own
  transition-page generator, says "1-9" instead of "1-8").
- **`.github/workflows/legacy-notebook-smoke.yml`**: renamed to "Legacy
  notebook smoke test (Exercise 10)"; stale Exercise 9 step and its
  trigger path removed; Exercise 10's own step/comment clarified.
- **`.github/workflows/deploy.yml`**: full-gate generator-staleness loop
  widened `01..08` -> `01..09`, plus a new
  `compute_exercise_09_svr_benchmark.py --check` call; two step
  names/comments updated to "Exercises 1-9".
- **`scripts/classify_release_change.py`**: all eight per-exercise
  `(0[1-8])` regexes -> `(0[1-9])`; `PUBLISHED_EXERCISE_NUMBERS` ->
  `range(1, 10)`; docstring updated.
- **`tests/test_book_structure.py`**: `test_exercises_one_through_eight_follow_in_order`
  -> `test_exercises_one_through_nine_follow_in_order` (range widened to
  9); `test_exercises_nine_through_twelve_source_preserved_but_not_published`
  -> `test_exercises_ten_through_twelve_source_preserved_but_not_published`
  (Exercise 9 removed from the "must not appear" list);
  `test_no_exercise_13_in_toc`'s `len(files)` expectation `8` -> `9`.
- **`tests/test_classify_release_change.py`**:
  `test_legacy_exercise_paths_are_not_fast_pathed` retargeted from
  `chapter_09` (now migrated) to `chapter_10` (still legacy).
- **`tests/test_exercise_manifest.py`**:
  `test_only_exercises_1_through_8_are_migrated` ->
  `test_only_exercises_1_through_9_are_migrated` (`[1..8]` -> `[1..9]`);
  module docstring updated.
- **`tests/test_exercise_09_lite_notebook.py`**: substantially rewritten
  for the new 48-cell/4-blank/5-question/multiselect structure; new tests
  for the shuffle-seed declarations, the multiselect question, the
  widget-label-overflow fix, the removed sections (SVC demo, kernel table,
  Lasso/KNN/trees, historical reference), the R2 schema additions, and the
  separate instructor-benchmark labeling in Section 6.
- **`tests/test_exercise_09_reference_execution.py`**: rewritten for the
  new schemas (R2 on PCR/PLS/Ridge/KernelRidge), the relocated
  `make_svc_dataset`, the new `SVR_BENCHMARK` global and its distinctness
  from the student's own subset result, the Matplotlib-warning-free
  Section 6 compare cell (re-executed in isolation under
  `warnings.catch_warnings`), and the executed shuffle-position/feedback
  checks (`_QUESTIONS`, `make_single_choice_question`,
  `make_multi_choice_question`, read directly from the executed
  namespace).
- **`tests/test_exercise_09_svr_benchmark.py`** (new, 80 lines): keeps the
  committed benchmark artifact honest (`--check`, split/row/feature
  counts, untuned-defaults flag, plausible scores, description wording).
- **`tests/test_exercise_09_transition_page.py`** (new, 74 lines): offline
  structural tests for the new transition page, modeled on
  `test_exercise_08_transition_page.py`.
- **`tests/test_exercise_09_notebook.py`** (deleted, 549 lines): the old
  legacy static-page structural suite, obsolete now that
  `book/chapters/chapter_09/exercise_09.ipynb` is a transition page, not
  the lesson itself -- replaced by `test_exercise_09_transition_page.py`.
- **`interactive/e2e-book/chapter09-dark-mode.spec.ts`** (deleted, 170
  lines): a Plotly-color regression guard for the old iframe-embedded
  page's activities; no iframe is left on the new transition page for it
  to check (same precedent as `chapter08-dark-mode.spec.ts`'s own earlier
  deletion).
- **`interactive/e2e-book/chapter09.spec.ts`**: rewritten from a legacy
  iframe-page suite to a transition-page suite, modeled on
  `chapter08.spec.ts`.
- **`interactive/e2e-book/exercise-09-lite.spec.ts`** (new, 399 lines): the
  real-browser suite for the corrected notebook -- untouched-template
  Run-All-Cells, a 390px label-overflow check covering both widgets, reset/
  back navigation, and a teacher-completed path (all four blanks, both
  widgets' live interaction, all five checked questions answered by option
  text, the multiselect question's full-correct and partial-wrong cases, a
  deliberately-wrong single-choice case, and a download-contains-edits
  check).
- **`interactive/e2e-book/launch-buttons.spec.ts`**: added "Chapter 9
  (migrated to JupyterLite) gets no top-bar Colab button"; header comment
  updated.
- **`interactive/playwright.book.config.ts`**: `testIgnore` narrowed from
  `[chapter09.spec.ts, chapter09-dark-mode.spec.ts, chapter10.spec.ts,
  iframe-height-contract.spec.ts]` to `[chapter10.spec.ts,
  iframe-height-contract.spec.ts]` (Exercise 9's specs now run); comment
  rewritten to explain both remaining exclusions precisely.

No change to Exercises 1-8's own generators, tests, or Playwright specs.
No change to `interactive/src/` (confirmed by `npm run test:unit` staying
at 481 passed, identical to before this WP).
