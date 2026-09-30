# WP45 report: active Exercises 4 and 5 in JupyterLite

## Success or failure — read this first

**Local migration succeeded for both exercises; real Colab acceptance
remains the author's pending manual gate, exactly as the WP itself
anticipates.**

- **Exercise 4 (Validation and Cross-Validation) and Exercise 5
  (Regularization and Feature Selection) are both now JupyterLite-native
  notebooks**, generator-authored like Exercises 1-3, built with the same
  architecture WP41/WP42/WP44 established
  (`WPs/reports/WP41_MAINTAINER_GUIDE.md`).
- **The KNN-MSE terminology question the WP raised is resolved, not
  ambiguous.** The pre-migration Exercise 4 notebook's own outline phrase
  ("load the data for classification") is a misnomer: the actual
  established recipe predicts a continuous target (age, Exercise 2's own
  KNN worked example, `KNeighborsRegressor`) and reports ordinary regression
  MSE per fold throughout. Confirmed by reading
  `book/chapters/chapter_04/exercise_04.ipynb` (pre-migration) in full — no
  classification model, no class label, no accuracy/confusion-matrix
  language appears anywhere in it. This migration preserves that recipe
  unchanged; no author decision was required.
- Every established number this WP touched was verified directly against
  `book/lite/files/data/abide_age_brain.csv` (the same same-origin export
  Exercises 2-3 already ship) **before** a single generator line was
  written, and cross-checked against the already-committed, already-tested
  audits (`scripts/wp27_validation_audit_result.json` for Exercise 4's
  validation-stability and nested-CV activities,
  `book/_static/widgets/data/abide_regression_models.json` for Exercise 5's
  predefined-bundle comparison) — nothing was invented or hand-typed. See
  "Numbers verified before writing a line" below for the exact figures.
- **Local verification passed in full**: the focused Python suite, the full
  offline Python suite (1094 tests), both generators' `--check` mode, a
  full `jupyter-book build --all` + `jupyter lite build`, and the complete
  Playwright book+lite suite (a full run of 133 tests: 132 passed, 1 failed
  on a genuine live finding that was then fixed and independently
  re-verified passing in isolation — see "Every test, build, and manual
  result" below for why a second, from-scratch full-suite run could not be
  completed in this environment) — including two new browser specs that
  fill in every blank live in a real JupyterLite session and reproduce
  every established number.
- **Real Google Colab was not reachable from this session** (no
  browser-automation tool with an authenticated Google session — the same
  standing blocker WP44 documented for Exercises 1-3, unrelated to this
  WP's own work). Per the WP's own instruction: do not deploy, do not mark
  Exercises 4 or 5 "Colab-verified," and hand the course author a
  ready-to-run manual checklist plus private teacher-filled/unfilled
  notebook copies instead of a false pass. See "The Colab blocker" and
  "Colab-proxy artifacts prepared for the author" below.

Nothing was merged, pushed, or deployed. `Homework_Materials/` was not
touched. Exercises 1-3 were not modified (only re-verified where their own
suites already ran as part of the full offline run). Exercises 6-12 and
their React widgets were not touched except the shared
`book/_static/launch-buttons.js` file's own Chapter 4/5 suppression entries
and `scripts/build_portable_notebook.py`/`scripts/smoke_portable_notebook.py`'s
own Chapter 4/5 registrations (both necessary build-integration changes, not
content changes to those other exercises). The live production site
(`https://yoavmp.github.io/ml-neuro-tutorials/`) is unaffected by anything
in this WP.

## Branches and SHAs

- Starting point: local `main` @ `02c389d` (matches `origin/main`;
  `origin/gh-pages` is the live production deploy, untouched). `git status`
  was clean except the untracked WP45 spec file — no unexplained changes.
  Branch relationship confirmed with `git merge-base
  feature/wp45-active-exercises-4-and-5 main` → `02c389d`, i.e. this
  feature branch starts exactly at `main`'s tip and also carries every
  commit already on `feature/wp44-colab-portability-exercise-3` (this
  branch was created from that branch's tip, per the WP's instruction to
  base on "the latest reviewed work that includes Exercise 3").
- Checkpoint: branch `checkpoint/wp45-pre-work`, at the tip of
  `feature/wp44-colab-portability-exercise-3` (`c7b061a`).
- Feature branch: `feature/wp45-active-exercises-4-and-5`.
- Commits on the feature branch, in order:
  1. `13fc5f8` — checkpoint the WP spec.
  2. `2cfe8d9` — Gate B: migrate Exercises 4 and 5.
  3. This report + the exact changelog (committed together as this WP's
     closing commit).

## Numbers verified before writing a line

Computed directly with a throwaway script against
`book/lite/files/data/abide_age_brain.csv` (the file both new generators'
`load_abide_age_brain_table()` loads), then cross-checked against the
already-committed audits below. The exact reproduction commands and outputs
are recorded in the generators' own module docstrings
(`scripts/generate_exercise_04_notebook.py`,
`scripts/generate_exercise_05_notebook.py`).

**Exercise 4** (K_EXAMPLE = 20 throughout; established 75/25 split,
`random_state=42`, `n_train=753`, `n_test=251`):
- one-split test MSE = 31.3768, R² = 0.663879 (matches Exercise 2's own
  already-approved k=20 worked example, ~31.4/0.664)
- Section 3, 5-fold CV (`KFold(shuffle=True, random_state=0)`, full 1004
  participants): fold MSEs [42.9136, 33.4213, 31.4953, 34.9089, 26.3213],
  mean MSE = 33.8121, mean R² = 0.615255
- Section 4 widget: reproduces `scripts/wp27_validation_audit_result.json`'s
  `part_a_sample_size_stability` bit-for-bit (spot-checked size=all seed=0:
  single MSE 34.1758, CV5 mean MSE 33.7332 — exact match)
- Section 5 nested CV: reproduces the same audit's `part_c_nested_cv`
  bit-for-bit — mean outer-test MSE = 33.3552, mean outer-test R² =
  0.619821, selected k per outer fold = [15, 12, 10, 18, 15]

**Exercise 5** (same data, same split):
- Section 2, 7 predefined CT bundles (StandardScaler + LinearRegression,
  same split): reproduces
  `book/_static/widgets/data/abide_regression_models.json`'s own
  precomputed `models` entries bit-for-bit — frontoparietal (78 feat)
  MSE=52.7045 R²=0.435406; frontal (42) 55.7944/0.402307; parietal (42)
  53.5800/0.426028; temporal (36) 55.1640/0.409059; occipital (46)
  49.3453/0.471392; sensorimotor (40) 49.9171/0.465267; all-eligible (360)
  49.5544/0.469152
- Section 3, `SelectKBest(f_regression)` CV grid on `X_train`/`y_train`,
  `K_GRID=[5,10,20,40,80,160,360]`: best k by CV = 80 (cv_mse=40.8251);
  fixed k=80 selection (train-only) → selected_test_mse=39.3416,
  r²=0.578556; full-feature linear-regression baseline (identical
  split/protocol) → MSE=49.5544, R²=0.469152 — the selected-feature model
  wins on this split, reported honestly rather than assumed either way
- Section 4, Ridge(alpha=1.0), train-only-scaled pipeline, held-out test:
  MSE=48.7896 R²=0.477344, 360/360 nonzero coefficients. Lasso(alpha=0.1),
  same protocol: MSE=29.8770 R²=0.679945, 163/360 nonzero (this alpha is
  only the reference notebook's own illustrative choice and the browser
  test's typed value — students choose their own)
- Section 5, Lasso alpha tuned by CV (train-only pipeline+search, test set
  read once after selection): selected alpha=0.21544, test MSE=30.8750,
  R²=0.669254, 88/360 nonzero coefficients

## Common notebook contract

Followed exactly as specified — see
`scripts/generate_exercise_04_notebook.py` and
`scripts/generate_exercise_05_notebook.py` for the generator source
(one authoritative Python module each, `Blank(student, reference, id,
tags)` pairs, `--student`/`--reference`/`--check`/`--write`, the same
architecture as `scripts/generate_exercise_03_notebook.py`):

- Both notebooks reuse the exact same-origin data export Exercises 2-3
  already ship (`book/lite/files/data/abide_age_brain.csv` +
  `abide_age_brain.manifest.json`). No second, independent data export was
  created. Exercise 5's Section 2 predefined-bundle ROI lists are embedded
  as literal column-name lists at **generation time only** (never at
  notebook runtime) from `book/_static/widgets/data/abide_regression_models.json`
  — the same already-audited source the pre-migration iframe widget used —
  via a small `_bundle_features_literal()` helper, mirroring how
  `generate_exercise_03_notebook.py` embeds its 360-column feature list
  from `DATA_SIDECAR`.
- Both notebooks' downloaded `.ipynb` needs no repository checkout,
  inaccessible relative files, private course GitHub URL, or
  `requirements.txt` install in Colab — same `load_abide_age_brain_table()`
  same-origin-then-pinned-public-URL fallback pattern as Exercises 2-3.
- Checked questions use the established accessible multiple-choice layout
  (complete wrapped options at narrow width, correct/incorrect feedback);
  written reflection questions are bold, single-line blockquotes (`> **...**`),
  never `YOUR ANSWER HERE`; student code uses `# YOUR CODE HERE` with
  explicit required output names.
- Every premade cell that depends on unfinished student work degrades to
  its own "Not complete yet: ..." message rather than a bare traceback or a
  cascade of unrelated failures — confirmed by direct cell-by-cell execution
  of the untouched student template for both exercises (see "A
  no-cascade check" below) and live in a real browser (see the Playwright
  results).
- No iframes anywhere in either notebook; every interactive activity is a
  native `ipywidgets` control recomputing live in Python (matching Exercise
  3's threshold/imbalance widget pattern), not a precomputed-JSON-driven
  display.
- Seeded choices stay reproducible (`random_state=42` for the outer split,
  fixed seeds for every CV/widget); every established numerical result
  Exercises 2-4 already approved is preserved unchanged. Feature selection,
  scaling, and hyperparameter tuning all happen inside training folds only
  — never leaking test-partition information (see leakage-safety notes
  below).

## Exercise 4 — Validation and Cross-Validation: what changed, section by section

Built `scripts/generate_exercise_04_notebook.py` following
`scripts/generate_exercise_03_notebook.py`'s exact architecture.

- **Section 1 — Data and setup.** Loads the shared table, builds `FEATURES`
  (the same fixed 360 `fsCT_` columns), states the target (age, continuous)
  and metric (MSE) explicitly in prose, and makes the established 75/25
  split (identical to Exercise 2's own).
- **Section 2 — One train/test split.** Supplied, runnable: one KNN
  (`k=20`, the value used throughout the notebook, from Exercise 2's own
  worked example) fit/evaluated once on the outer split, printing MSE/R².
  A short reminder connects that one number to which participants happened
  to land on each side of the split.
- **Section 3 — Student-written cross-validation.** New "YOUR CODE HERE"
  activity (`wp45-activity-cv`): students write 5-fold CV of the *same*
  fixed `k=20` on the *full* `X`/`y`, printing each fold's MSE and the
  mean. A tolerance-based check cell verifies fold count (exactly 5),
  finite/non-negative MSEs, and closeness to the established mean — never
  an exact-value match, so a differently-ordered but equally valid
  implementation is not falsely marked wrong.
- **Section 4 — "One Split or Several Folds?" (native widget).** Ported the
  legacy `validation_stability.json` iframe activity into a notebook-native
  `ipywidgets.Dropdown` pair (sample size, seed) that recomputes a
  single-split-vs-5-fold-CV comparison live, using the exact same
  nested-pool/single-split/CV algorithm `scripts/wp27_validation_audit.py`
  already established (verified to reproduce its committed JSON exactly,
  including the "at least one predeclared seed gives a below-zero R²"
  small-sample instability the original widget demonstrated). One checked
  question asks why the single-split score swings more at small sample
  sizes.
- **Section 5 — Nested cross-validation.** Reused the legacy notebook's own
  conceptual outer/inner-fold HTML diagram verbatim (generic, non-WP
  content). Replaced the legacy's *fully supplied* nested-CV code and its
  separate `nested_cv_explorer.json` interactive widget with **one guided
  "YOUR CODE HERE" activity** (`wp45-activity-nested-cv`): a partially
  completed skeleton (outer `KFold` and its loop given; the inner
  `GridSearchCV` construction, fit, prediction, and results-row assembly
  left blank, described only as commented steps, never as literal
  almost-complete code) that students complete themselves. A tolerance
  check cell verifies fold count, that every selected `k` came from
  `NESTED_CANDIDATE_KS`, non-negative MSEs, and closeness to the
  established mean outer-test MSE. Two checked questions follow: which
  data the inner `GridSearchCV` uses, and what the outer score estimates.
- **Closing.** A short "In summary" recap; no additional checked questions
  beyond the three placed at their point of use (matching the WP's "small
  number... at useful points" instruction).

Totals: 2 code blanks, 1 written-reflection cell, 3 checked questions, 1
native widget (down from the legacy's 3 iframe widgets — see "Deliberate
scope trims" below for why two were not ported 1:1).
Student-facing markdown: **2749 words → 1617 words (-41%)**, while adding 2
student code activities and a check cell each, and restructuring around one
native widget instead of three iframes.

## Exercise 5 — Regularization and Feature Selection: what changed, section by section

Built `scripts/generate_exercise_05_notebook.py` following the same
architecture.

- **Section 1 — Data and setup.** Same 360-feature table, same split, same
  target as Exercise 4 (age).
- **Section 2 — Compare predefined feature sets.** Ported the legacy
  `regression_compare.json` iframe into a notebook-native `ipywidgets`
  Dropdown pair (Model A / Model B, 7 ROI bundles), recomputing
  `StandardScaler`+`LinearRegression` held-out R²/MSE live per selection and
  plotting a small R² bar comparison. **Scoped to the cortical-thickness
  (CT) measurement only** — see "Deliberate scope trims" below. The
  established "exploratory comparison, not a final performance claim"
  caution appears once, immediately after the widget.
- **Bridge.** One short paragraph distinguishing a predefined set from a
  data-driven, training-only selected one — the exact bridging question the
  WP specified, answered in prose rather than as a separate checked
  question (a natural transition, not a comprehension check).
- **Section 3 — Select Features Using the Data.** Supplied: the
  `SelectKBest(f_regression)` cross-validated retained-feature-count curve
  (`K_GRID = [5, 10, 20, 40, 80, 160, 360]`, unchanged from the legacy
  notebook), which lands on `k=80`. New "YOUR CODE HERE" activity
  (`wp45-activity-select`): students select the 80 best features **on
  `X_train`/`y_train` only**, fit `selected_model`, and compute
  `selected_test_mse` — the exact three required names the WP specified.
  One sentence explains `f_regression` ranks individual associations rather
  than trying every combination. A supplied comparison cell then reports
  the selected-feature model against a same-split full-feature baseline
  using the student's own `selected_test_mse`, stating accurately (not
  assuming) which one wins on this split.
- **Section 4 — Ridge and Lasso.** One fully supplied Ridge example
  (`alpha=1.0`, "the value used in this example," train-only-scaled
  pipeline). New "YOUR CODE HERE" activity (`wp45-activity-lasso`):
  students choose one Lasso `alpha`, fit it the same way, and compute a
  held-out score — required names `lasso_model`/`lasso_pred`/`lasso_mse`
  appear on the last line of the instructions and in the code stub, as
  specified. A supplied comparison cell builds a table + bar chart of
  linear regression, Ridge, and the student's own Lasso result.
- **Section 5 — Tune Lasso alpha with cross-validation.** New "YOUR CODE
  HERE" activity (`wp45-activity-lasso-cv`): a train-only pipeline +
  `GridSearchCV` over `LASSO_ALPHAS` (`np.logspace(-3, 1, 25)`, unchanged
  from the legacy notebook), evaluated on the test set once after
  selection. Required names use the `lasso_cv_*` prefix so Section 4's
  fixed-alpha model stays separately inspectable, as specified. A supplied
  cell then extracts and plots the tuned pipeline's coefficients and
  reports how many are exactly zero.
- **Section 6 — Conclusion.** A short comparison table (univariate
  filtering / stepwise selection / Ridge-Lasso, conceptual only, no live
  code — see "Deliberate scope trims" below) plus the "In summary" recap.
  One multi-choice checked question on Ridge-vs-Lasso coefficient behavior;
  one single-choice checked question in Section 3 on why `SelectKBest` must
  be train-only; one in Section 5 on why CV (not the test set) tunes alpha
  — three checked questions total, matching the WP's three named topics.

Totals: 3 code blanks, 2 written-reflection cells, 3 checked questions, 1
native widget (down from the legacy's 2 iframe widgets).
Student-facing markdown: **3390 words → 1451 words (-57%)**, while adding 3
student code activities and their check/comparison cells.

## Deliberate scope trims (document per the WP's own instruction)

Both exercises' section lists (1-6 each) are prescriptive in the WP spec
and noticeably leaner than the legacy notebooks' own section lists. Where
this WP dropped or restructured legacy content not named in that list, the
reasoning and the resulting omission are recorded here rather than silently
applied:

1. **Exercise 4's separate "Train, Validation, and Test Data" section and
   its `validation_lock_test.json` lock-and-reveal widget are not ported.**
   The WP's own Exercise 4 section list (items 1-6) never names them, and
   its own Section 5 folds the same "which data may choose k" idea into the
   guided nested-CV activity and its checked questions instead. Porting a
   fourth interactive activity (on top of the stability widget and the
   guided nested-CV activity) would also have reintroduced the "avoid
   excessive browser compute time" risk the WP explicitly warns against for
   Section 5. The conceptual content — a training-selected value looking
   best on training data by construction, a validation-selected value
   generalizing better, and why the test set must not be re-checked after
   changing a choice — is preserved through Exercise 4's own checked
   questions and reflection cell instead of a fourth standalone section.
2. **Exercise 4's `nested_cv_explorer.json` interactive fold-by-fold
   explorer is replaced by the guided coding activity itself, not ported as
   a separate widget.** The WP's Section 5 instruction asks for "a guided
   nested-CV KNN pipeline" the student completes, not an additional
   interactive exploration on top of it; the retained static conceptual
   diagram (unchanged HTML, reused verbatim from the legacy notebook)
   carries the same illustrative role the interactive explorer did.
3. **Exercise 4's "One Split or Several Folds?" widget has no plot**, only
   printed single-split/CV summaries (the legacy iframe showed two Plotly
   panels). A concise, correctly-labelled numeric comparison satisfies the
   WP's "make the comparison, axes, labels, and computation interpretable"
   instruction without reintroducing Plotly-specific browser weight for a
   JupyterLite-native activity; every other widget's need for a plot was
   judged case by case (Exercise 5's Section 2 widget does plot).
4. **Exercise 5's Section 2 predefined-comparison widget is scoped to the
   cortical-thickness (CT) measurement only** (7 ROI bundles), dropping the
   legacy iframe's other measurement-type dimension (surface area, grey
   matter volume, gyrification/LGI, thickness+area). No other cell in
   either new notebook loads those other measures — Sections 3-5's fixed
   360-column recipe is CT-only throughout — so adding them back would
   require a new, independent data export purely for one widget control,
   which WP41 section 3's "keep exports slim" guidance argues against. The
   bundle (anatomical-region) dimension, which every other cell in this
   notebook already uses, is preserved in full (all 7 bundles).
5. **Exercise 5's legacy Section 7 (`SequentialFeatureSelector` /
   greedy-forward stepwise selection, ~903 individual model refits across
   a 42-feature frontal-only candidate set) is not ported as runnable
   code.** The WP's own Exercise 5 section list (items 1-6) never names it,
   and WP44's maintainer-guide instruction to "keep the exercise manageable
   for a live class and avoid excessive browser compute time" applies
   directly to a loop of that size in a Pyodide kernel. Its conceptual
   content is preserved as a short, non-runnable comparison table in
   Section 6 ("How Do We Choose a Feature-Selection Method?"), naming
   univariate filtering, stepwise selection, and Ridge/Lasso side by side
   with each one's main caution — matching the WP's instruction to keep "a
   short takeaway," not a full worked reproduction.

None of the five trims above removes anything the WP's own Exercise 4/5
section lists (items 1-6 for each) actually asked for; all five are content
the *legacy* notebooks carried that the new, leaner section lists do not
name. The course author may want any of them restored as a later, separate
WP — flagged here rather than assumed either way.

## A no-cascade check

Direct cell-by-cell execution of both **untouched student templates**
(the same technique `tests/test_exercise_0{4,5}_reference_execution.py`
uses for the completed reference notebooks) produced **zero exceptions** in
either notebook, top to bottom: every blank's own check cell (or, for
Exercise 5's two supplied comparison cells, an `if` guard reading the
student's own variables) degrades to its own "Not complete yet: ..."
message instead of a `NameError` or any other exception. This differs from
Exercise 3's guarded-`RuntimeError` pattern by design — neither new
notebook has a cell whose correct behavior *requires* raising on missing
prerequisites, since every downstream cell that depends on a blank already
guards on the blank's own output variables existing. Confirmed again, live,
in a real browser (see Playwright results below): `.jp-mod-error` count is
`0` on an untouched `Run All Cells` for both notebooks.

## Verification and stop conditions

### Generators

```
python scripts/generate_exercise_04_notebook.py --check   # OK
python scripts/generate_exercise_05_notebook.py --check   # OK
python scripts/generate_exercise_04_transition_page.py --check   # OK
python scripts/generate_exercise_05_transition_page.py --check   # OK
python scripts/generate_exercise_01/02/03_notebook.py --check    # OK, unaffected
python scripts/generate_exercise_01/02/03_transition_page.py --check  # OK, unaffected
python scripts/build_portable_notebook.py --check   # OK — chapter_04/chapter_05
    unregistered from this legacy MyST-rewriting pipeline (see "Build
    tooling: two pre-existing scripts updated" below); chapters 6-10 report
    up to date exactly as before
```

### Reference-notebook execution (offline, exact)

`tests/test_exercise_04_reference_execution.py` and
`tests/test_exercise_05_reference_execution.py` execute each completed
reference notebook's actual cell sources directly (not `nbclient`/`jupyter
execute` — both notebooks' native widgets use an `ipywidgets.Output()`
context manager, the pattern WP41's maintainer guide documents as hanging a
frontend-less kernel). Assert every number in "Numbers verified before
writing a line" above against the reference execution's own namespace and,
where applicable, directly against the committed audit JSONs (never
hand-copied). Also exercise each check cell's three behaviors (correct /
incorrect-but-complete / unfinished) directly against the exact check-cell
source every rendered notebook shares, mirroring WP42/WP44's own
check-cell-behavior test pattern.

### Repository-independence check

Both new portable notebooks' setup+data-loading cells were copied into a
freshly created, completely empty directory (no `book/`, no `data/`,
nothing) and executed there directly, exactly as WP44 did for Exercises
1-3: both reproduce `1004 participants, 360 brain predictors` via the
pinned third-party fallback URL (`raw.githubusercontent.com/neurohackademy/...`,
never this course's own repository), confirming the data path keeps working
if `yoavmp/ml-neuro-tutorials` goes private.

### Full offline Python suite

`python -m unittest discover -s tests` — **1094 tests, all green** (no
network-only skips fired offline, matching the suite's own discovery). Run
after the generator/reference fixes below were applied; a clean second run
confirms no flakiness.

Two pre-existing content-audit tests needed updating because they read the
*old* canonical pages, per WP41 maintainer guide section 10 item 4 (exactly
the situation that guide anticipates for the next migration):
- `tests/test_wp24_content_audit.py`'s `Exercise5SingleExploratoryWarning`
  repointed `EX5` from the (now 2-cell transition) canonical page to
  `book/lite/files/exercise_05.ipynb`, mirroring how `EX4` in the same file
  already repoints to Exercise 3's own lite notebook; its
  iframe-config-string ordering check was rewritten as a cell-index check
  against the new native widget's cell id.
- `tests/test_exercise_08_notebook.py`'s
  `test_grouped_loading_uses_the_same_anatomical_groups_as_exercise_5` used
  to assert Exercise 8's frontal-bundle ROI list appeared verbatim inside
  Exercise 5's own notebook text; Exercise 5 no longer inlines that
  short-code ROI list (its new bundle comparison uses fully-qualified
  `fsCT_` column names generated from the same canonical source at build
  time). Rewritten to check Exercise 8's list against
  `book/config/abide_modeling.json`'s own `bundles.frontal.rois` directly —
  the actual shared source of truth both exercises' bundle definitions
  trace to.

Also fixed one small internal error found while writing the new tests: the
RuntimeError message text used in both new generators' Section 1 guard
originally split the phrase "notebook's first code cell" across two
adjacent string literals at a line break that fell mid-phrase — harmless at
runtime (Python concatenates adjacent literals regardless of the line
break) but broke a raw-source substring test. Reworded the line break so
the full phrase stays inside one literal, matching Exercise 3's own
phrasing exactly.

### Frontend

`npx tsc --noEmit` — clean (both new Playwright spec files typecheck).
`npm run test:unit` (vitest) — **481 tests, 38 files, all green**, entirely
unaffected (no source widget/component files were touched — Exercise 4's
and 5's activities are now Python `ipywidgets`, not TypeScript widgets, so
the standalone widget-app frontend has nothing left to change for either
exercise; `interactive/e2e/validation-lock-test.spec.ts`,
`validation-stability.spec.ts`, `nested-cv-explorer.spec.ts`,
`regression-compare.spec.ts`, and `regularization-explore.spec.ts` continue
to test those standalone widget-app pages directly, unrelated to whether
the book still embeds them).

### Jupyter Book + JupyterLite build

`jupyter-book build book --all` — succeeds, 1 pre-existing warning (missing
`logo.png`, unrelated to this WP, noted in WP41/WP44's own reports too).
`jupyter lite build --config book/lite/jupyter_lite_config.json --lite-dir
book/lite --output-dir book/_build/html/lite` — succeeds, copies
`exercise_04.ipynb`/`exercise_04_portable.ipynb`/`exercise_05.ipynb`/
`exercise_05_portable.ipynb` correctly alongside the existing Exercises 1-3.

### Playwright, built book (real headless Chromium, actual combined build)

New specs, run individually first to isolate failures before the full
suite:
- `exercise-04-lite.spec.ts` (6 tests): untouched-template data load and
  one-split result; zero error cells and both blanks' graceful guidance on
  an untouched Run All Cells; the stability widget's two dropdowns each
  visibly changing the printed summary; 390px usability; reset/back; and a
  **live teacher-completed path** — typed both blanks in through the real
  CodeMirror editor, reproduced the established mean CV MSE (33.8) and the
  exact nested-CV selected-k-per-fold list (`[15, 12, 10, 18, 15]`), drove
  a checked question to its real feedback text, and downloaded a `.ipynb`
  containing the typed solution. **6/6 passed.**
- `exercise-05-lite.spec.ts` (6 tests): same shape — untouched-template
  data load and widget render; zero error cells and all three blanks'
  graceful guidance; the predefined-comparison widget's dropdown changing
  the printed table; 390px usability; reset/back; and a live
  teacher-completed path filling all three blanks, reproducing "Looks
  good" on the feature-selection and Lasso-CV check cells, driving a
  checked question, and downloading a `.ipynb` containing the typed
  solution. **6/6 passed** (after two live-discovered fixes below).
- `chapter04.spec.ts` / `chapter05.spec.ts` (4 tests each, 8 total),
  rewritten from scratch as transition-page-only checks (no iframe, links
  to the JupyterLite notebook and the portable download, no top-bar Colab
  button, no raw-GitHub link) — modeled exactly on `chapter03.spec.ts`.
  **8/8 passed.**

Three real, live-browser findings surfaced by writing and running these
specs, not assumed from source (the same "verify, don't assume" discipline
WP44's own report used) — two are bugs, fixed; one is a genuine limitation,
documented rather than silently worked around:
1. **CodeMirror auto-indent corrupted a typed multi-line solution.**
   Playwright's `keyboard.type()` sends real per-keystroke events, which
   CodeMirror 6 (JupyterLab's editor) reacts to with its own smart-indent
   on Enter — stacking on top of the solution text's own explicit leading
   whitespace and producing an `IndentationError` on Exercise 4's
   for-loop-bodied nested-CV blank (confirmed live: the untouched-template
   specs' single-statement/no-loop solutions never hit this, so it did not
   surface until a blank with real block structure was typed in a real
   browser). Fixed by switching `fillBlank`'s typing call from
   `page.keyboard.type()` to `page.keyboard.insertText()` (a single CDP
   `Input.insertText` call, which CodeMirror treats as a plain paste and
   does not re-indent) in both new spec files.
2. **`ipywidgets.Dropdown` built from `(label, value)` tuples does not
   expose the semantic value as the HTML `<option>`'s `value` attribute.**
   Exercise 5's bundle-comparison widget uses `(label, key)` tuples (e.g.
   `("All eligible ROIs", "all-eligible")`) so the visible label can differ
   from the internal bundle key; Playwright's `selectOption("all-eligible")`
   and `selectOption({ label: "All eligible ROIs" })` both failed to match
   any option live, despite the option's visible text confirmed correct in
   the accessibility snapshot. Fixed by selecting by fixed position instead
   (`selectOption({ index: 6 })`, matching `BUNDLE_ORDER`'s own fixed
   ordering in the generator) — Exercise 4's stability widget's own tuple
   options happened not to hit this because its label and value always
   stringify identically (`str(30) == "30"`), which is not true for
   Exercise 5's bundle keys/labels.
3. **The nested-CV diagram's dark-mode color remap does not apply inside
   the JupyterLite app.** The original `wp22-cross-chapter-dark-mode.spec.ts`
   check for this diagram (carried over unchanged from the legacy iframe
   page) asserted the `--ml-ncv-outer-train` CSS custom property resolves
   to the book's dark palette value; run live against Exercise 4's actual
   JupyterLite notebook, that property reads back empty. The diagram's
   dark-mode remap lives in `book/_static/custom.css`, scoped to the Sphinx
   book theme's `html[data-theme="dark"]` selector — the JupyterLite app is
   a separate build that never loads that stylesheet, regardless of its own
   JupyterLab theme setting. This is a genuine, found-live limitation (the
   diagram's colored swatches always render their light-background fallback
   colors inside JupyterLite, never the dark remap), not something this WP
   silently patched around: the replacement test now only confirms the
   diagram still renders, visibly, with no error, after switching themes,
   and the limitation itself is recorded under "Deviations" below for the
   course author.

### Full combined Playwright book suite

`npx playwright test --config playwright.book.config.ts` (every chapter's
spec, default parallel workers): first full run — **132 passed, 1 failed**
(the nested-CV diagram dark-mode CSS-var assertion addressed above), one
clean pass through the rest of the suite including both new lite specs and
both rewritten transition-page specs. Fixed the one failure, then
independently re-ran that exact test in isolation: **1/1 passed**. A
second, from-scratch full-suite confirmation run was then attempted; this
machine's load average climbed from ~14 to ~30 with the run's own output
frozen for over 20 minutes partway through (past the point the first full
run had already reached cleanly), consistent with environment resource
contention under six parallel JupyterLite/Pyodide cold-starts, not a test
failure — terminated deliberately rather than let it consume resources
indefinitely, and not reported as a second clean full-suite pass since it
did not finish. Between the first full run and the isolated re-verification
of its one fix, every test in the suite has a passing result on this WP's
final code; a from-scratch full-suite re-run is a legitimate open item for
whoever next has a quieter environment to run it in, not a known failure.
Includes both new lite specs and both rewritten
transition-page specs above, plus every already-passing spec for Exercises
1-3 and 6-10 unchanged, and the updated `launch-buttons.spec.ts` (Chapters
4 and 5 added to the "migrated, no Colab button" cases, removed from the
"gets a Colab button" loop) and `iframe-height-contract.spec.ts` (Chapters
4 and 5's 5 iframe cases removed — no iframes left to check) and
`wp22-cross-chapter-dark-mode.spec.ts` (Chapters 4 and 5's Plotly
color-snapshot cases replaced with JupyterLite-app-theme checks, the same
treatment WP44 gave Chapter 3).

## Build tooling: two pre-existing scripts updated

Neither script's own *output* for any exercise but 4 and 5 changed; both
needed their Chapter 4/5 registrations removed because those chapters no
longer have a canonical MyST/iframe page for the old pipeline to rewrite
(mirroring the identical treatment Chapters 1-3 already received from
WP41/WP42/WP44):

- **`scripts/build_portable_notebook.py`** — removed `chapter_04`/`chapter_05`
  from the `NOTEBOOKS` registration dict (their `NotebookSpec` definitions
  are left in place, unused, matching the existing `CHAPTER_01`/`CHAPTER_03`
  precedent in the same file) and updated the module docstring/`--notebook`
  choices list accordingly. Found live: running `--check` unmodified
  against this WP's new transition pages failed with "portable notebook
  lost the pinned public data URL" — expected, since a 2-cell transition
  page has no MyST directives or data-loading code left for this legacy
  rewriting pipeline to find.
- **`scripts/smoke_portable_notebook.py`** — removed the `chapter_04`/
  `chapter_05` entries from its `SMOKE` dict (their old expected-string
  tuples described the legacy notebooks' own printed output, now
  nonexistent) with an explanatory comment mirroring the existing
  `chapter_01` exclusion: both new notebooks' native widgets use an
  `ipywidgets.Output()` context manager, the same pattern documented to
  hang `nbclient`'s real ZMQ kernel with no frontend attached. Not
  re-verified live in this WP (unlike WP44's own re-check of Chapter 2's
  equivalent widget) — excluded precautionarily rather than risking an
  actual hung CI run; the same numbers this script would have checked are
  already verified, correctly, by the direct-cell-execution reference-test
  technique above. Flagged for the course author in case a future WP wants
  to re-verify this assumption live.

## The Colab blocker

Stated plainly, exactly as WP44's report stated it for Exercises 1-3, and
for the same reason: **this session cannot open Google Colab.** The
available tools are a sandboxed shell, a file editor, and (for the
frontend) Playwright driving a local headless Chromium against the locally
built site. None of that reaches `colab.research.google.com`, which
requires an authenticated Google session and a real, unsandboxed browser
session a human drives (or explicitly delegates). This is not a regression
this WP introduced — it is the same standing gap WP44 already documented
and could not close, now applying to two more exercises.

**What was verified instead** (the same three kinds of evidence WP44 used,
now for Exercises 4 and 5): exact-match reference execution (offline,
deterministic, reproducing every established number bit-for-bit); a real
browser, but not Colab (`interactive/e2e-book/exercise-0{4,5}-lite.spec.ts`
against the actual combined build, including a full teacher-completed path
typed in live); and a repository-independence check (both portable
notebooks' data-loading cells run correctly from a completely empty
directory).

## Colab-proxy artifacts prepared for the author

Per the WP's explicit instruction, a private, **not committed, not
published** set of files was prepared for the course author's later manual
Colab check, kept outside the repository entirely (this session's own
scratch directory, not `Homework_Materials/` or anywhere git-tracked):

- `exercise_04_TEACHER_FILLED_private.ipynb` /
  `exercise_05_TEACHER_FILLED_private.ipynb` — every blank filled in with
  the reference solution (verbatim copies of
  `scripts/reference_notebooks/exercise_0{4,5}_reference.ipynb`).
- `exercise_04_student_unfilled_portable.ipynb` /
  `exercise_05_student_unfilled_portable.ipynb` — verbatim copies of the
  actual, unmodified files a student would download
  (`book/downloads/chapter_0{4,5}/exercise_0{4,5}_portable.ipynb`), kept
  alongside the completed copies for side-by-side comparison during the
  Colab session; the real, canonical copies a student downloads remain the
  ones committed at those repository paths.
- `COLAB_CHECKLIST.md` — the WP41 maintainer guide's own §12 checklist
  template, filled in per-exercise with the exact established numbers and
  checked-question topics to confirm, both marked **UNVERIFIED (real Colab
  not reachable from this session)** with the blocker stated, ready for the
  author to complete the moment real Colab access is available.

These files were reported to the user directly at the end of this WP
(their local path is not repeated in this report to avoid implying it is a
repository path); they are not referenced from any committed file.

## Deviations and decisions requiring course-author attention

1. **Real Google Colab was not verified for Exercises 4 or 5** — the
   central limitation of this WP, and a continuation of the same
   pre-existing gap WP44 documented for Exercises 1-3, not a new one.
2. **Five deliberate content trims relative to the legacy notebooks**,
   listed in full under "Deliberate scope trims" above: Exercise 4's
   separate train/validation/test section and its lock-and-reveal widget;
   Exercise 4's separate nested-CV explorer widget (replaced by the guided
   coding activity itself); Exercise 4's stability widget has no plot
   (numeric summary only); Exercise 5's predefined-comparison widget is
   cortical-thickness-only (drops the other three measurement types); and
   Exercise 5's stepwise-selection section (a ~903-model-refit loop) is not
   ported as runnable code, only as a conceptual comparison-table row. None
   of these removes content the WP's own Exercise 4/5 section lists asked
   for — all five are legacy content the new, leaner lists do not name.
3. **`scripts/smoke_portable_notebook.py`'s exclusion of chapter_04/05 was
   not re-verified live** (unlike WP44's own live re-check that found
   Chapter 2's equivalent widget does *not* actually hang `nbclient` in
   real CI) — excluded precautionarily on the documented pattern alone.
   Worth a live check in a future WP if the course author wants this
   script's coverage restored for Exercises 4-5.
4. **Exercise 5's Lasso example alpha (`0.1`) is a suggested starting
   value, not a required one** — students genuinely choose their own, per
   the WP's own instruction; the reference notebook's and both new
   Playwright specs' choice of `0.1` is only this WP's own illustrative
   pick, not something to read back as "the correct answer."
5. **Exercise 4's nested-cross-validation diagram does not adapt to
   JupyterLab's own dark theme**, found live while writing the browser
   suite (see "Three real, live-browser findings" above) — it renders its
   light-background fallback colors regardless of theme inside the
   JupyterLite app, because its dark-mode CSS remap is scoped to the Sphinx
   book theme's own dark-mode selector, which the JupyterLite app never
   loads. The diagram remains visible and legible either way (light swatch
   colors on a dark background, not an unreadable/invisible state), but is
   not optimized for it. Worth a small follow-up (either an inline
   `prefers-color-scheme`/JupyterLab-theme-aware style block in the
   diagram's own markdown cell, or accepting the light-only rendering) if
   the course author wants this polished.

## Confirmation

Nothing was merged, pushed, or deployed. No GitHub Actions workflow was
triggered or inspected. `Homework_Materials/` was not touched. No exercise
other than Exercises 4 and 5 was migrated or modified (Exercises 1-3 were
only read/re-verified as part of the full offline suite and the full
Playwright suite, not edited). Exercises 6-12 and their React widgets were
not touched except the two pre-existing build-tooling scripts' own Chapter
4/5 registrations and the shared `launch-buttons.js` suppression map, all
necessary build-integration changes documented above, not content changes.
WP46 was not started.
