# WP46 report: active Exercises 6 and 7 in JupyterLite

## Success or failure — read this first

Exercises 6 (Decision Trees) and 7 (Boosting and Gradient Boosting) are
migrated to the JupyterLite-native, generator-authored architecture
established by WP41/WP42/WP44/WP45, following
`scripts/generate_exercise_05_notebook.py` and
`scripts/generate_exercise_04_notebook.py`'s exact shape. Both notebooks:

- run end to end, cleanly, both as an untouched student template (zero
  error cells; each `YOUR CODE HERE` blank degrades to its own
  "Not complete yet" message) and as a fully completed teacher reference
  (every check cell prints "Looks good");
- reproduce the legacy notebooks' audited numbers exactly wherever the
  underlying computation is not sensitive to this same-origin data source's
  column ordering, and reproduce close, honestly-computed, and explicitly
  documented **different** numbers wherever it is (see "Numbers verified
  before writing a line" below — this is the single most important
  technical finding of this WP, and it is a genuine property of switching
  data sources, not a defect in either the legacy or the new notebook);
- port every legacy iframe-embedded interactive activity (four total: two
  in Exercise 6, two in Exercise 7) to native `ipywidgets`/Matplotlib
  controls, with no iframe left in either notebook;
- pass the full local offline Python suite, real headless-Chromium
  Playwright runs against the actual combined local Jupyter Book +
  JupyterLite build for both exercises' own spec files (both the
  untouched-template and teacher-completed paths), and `tsc --noEmit`. A
  full combined Playwright run across *all ten* built exercises was not
  attempted (see "Full combined Playwright book suite" below) — this is a
  deliberately left-open gate, not a claimed green result.

WP45's own open gates are carried forward accurately and are **not**
closed by this WP: Exercises 3, 4, and 5's real-Colab verification is
still pending, and WP45's own full-suite Playwright re-run was left as an
open item due to a resource-contention stall it hit at higher parallelism
(not a test failure). This WP adds Exercises 6 and 7 to that same list —
see "The Colab blocker" and "WP45's still-open gates, carried forward"
below.

No merge, no push, no deployment, no GitHub Actions interaction at any
point. `book/config/exercise_manifest.json`'s Exercise 6 and 7 entries stay
`migrationState: "legacy"` with every Lite field `null`, deliberately,
pending the real-Colab acceptance gate (WP41_MAINTAINER_GUIDE.md section
11) — the same treatment Exercises 3, 4, and 5's entries already have.

## Branches and SHAs

Starting SHA (local `main`): `dcc53655b8e4b3eac67ba741e165ff6bbbf0cf3d`,
matching `origin/main` (unchanged since WP45; verified with
`git merge-base --is-ancestor origin/main HEAD`).

Checkpoint: branch `checkpoint/wp46-pre-work`, at the tip of
`feature/wp45-active-exercises-4-and-5` (`350a931` — "WP45: reports —
execution report and exact changelog").

Feature branch: `feature/wp46-active-exercises-6-and-7`, created from that
same tip. Working tree had no unexplained changes at checkout time (only
the new, untracked `WPs/WP46_ACTIVE_EXERCISES_6_AND_7.md`).

Commits made by this WP, in order:
1. `2bd24d7` — checkpoint the WP spec on the dedicated feature branch.
2. `2c6bc0a` — Gate B: migrate Exercises 6 and 7 to JupyterLite-native
   notebooks (34 files changed, +14995/-5427; see
   `WPs/reports/WP46_EXACT_CHANGELOG.md` for the full file list).
3. This report + this changelog (committed together as this WP's closing
   commit; see `git log -1` after that commit for the final SHA).

## Numbers verified before writing a line

Both `book/lite/files/data/abide_age_brain.csv` (the established same-origin
export Exercises 2, 4, 5, and now 6/7 all share — no new export was
created) and every relevant audit script/JSON
(`scripts/decision_tree_model_audit.py` /
`scripts/decision_tree_model_audit_result.json`,
`scripts/gradient_boosting_model_audit.py` /
`scripts/gradient_boosting_model_audit_result.json`,
`scripts/export_tree_greedy_widget.py`, `scripts/export_boosting_step_widget.py`)
were read and executed directly against this data source before either
generator was written, per the WP's explicit instruction not to assume a
decorative reference is numerically compatible with a changed split.

**The central finding**: the legacy (pre-migration) Exercise 6 and 7
notebooks loaded the ABIDE-II cohort directly from the pinned raw TSV over
the network, whose 360 `fsCT_*` columns are encountered in the original
scan's own order. The established same-origin CSV export this migration
uses (matching every other migrated exercise, and the JupyterLite
no-network-dependency requirement) has those same 360 columns in a
different — alphabetical-looking — order, and the exported CSV values are
rounded to ~6 significant figures (present since Exercise 2). Neither
difference matters for a shallow, few-split computation on named features
(splits are the same regardless of scan order when there are no real
near-ties, which is the overwhelmingly common case with continuous brain
measures). It **does** occasionally matter for a *deep* tree-based model
(`max_depth=6` ensembles, or GradientBoosting's `max_depth`-1..3 CV search)
fit on all 360 features: with enough splits, the tiny value-rounding
occasionally flips which of two near-tied candidate splits is chosen,
which cascades into a genuinely different (but equally valid) fitted model
downstream.

Verified directly, section by section:

**Exercise 6**
- Single tree (`SMALL_TREE_FEATURES`, `max_depth=3, min_samples_leaf=20,
  random_state=42`, dev split `n_fit=564, n_val=189`): 8 leaves, depth 3,
  val MSE = 45.9783, val R² = 0.361081 — **matches the legacy audit
  exactly** (not order-sensitive: two named features, shallow tree).
- Complexity curve (depths 1–10, `min_samples_leaf=5, random_state=42`,
  full p=360, same dev split): best depth = 2, val MSE = 41.6389 —
  **matches exactly**.
- Classification-depth contrast (WP30R-corrected recipe: development-only,
  753 of 1004, 251 outer-test excluded and proven disjoint,
  `StratifiedKFold(5, shuffle=True, random_state=42)`,
  `min_samples_leaf=5`, depths 1–10): best depth = 5, val AUC = 0.5712,
  depth-2 AUC = 0.5337 (exact match to the legacy value), margin = 0.0375.
  Close to, not bit-identical to, the legacy audit's 0.5672/0.5337/0.0335
  — the inclusion rule (`depth ≥ 3` and `margin ≥ 0.01`) still passes
  against this data source, confirmed by direct re-computation before
  deciding to keep the figure, per the WP's explicit condition ("only if an
  audited example actually supports its interpretation").
- Ensemble replicate widget ("One Tree or Many?"): live-recomputed inside
  the notebook every time it runs (5 replicate seeds × the full
  `[1,5,10,25,50,100]` n_trees grid, exactly as the legacy widget data
  used) — not compared against a hardcoded legacy number, only
  sanity-checked for the qualitative finding the activity teaches (bagging
  and Random Forest reduce variance relative to a single tree; variance
  falls as trees are added), which holds against this data source.
- Model comparison (`KFold(5, shuffle=True, random_state=100)`, full
  n=1004, p=360, `tree_settings=dict(max_depth=6, min_samples_leaf=5,
  random_state=42)`, `n_estimators=50`, `max_features=19`): Single tree
  mean MSE = 56.7434 R² = 0.3201; Bagging = 32.7764 / 0.6356; Random Forest
  = 34.0980 / 0.6211. Close to, not bit-identical to, the legacy audit's
  57.4426/32.6774/34.33 — the order-sensitivity case above, on the deepest
  model in this notebook. Bagging still edges out Random Forest here,
  reproducing the legacy notebook's own finding.

**Exercise 7**
- "Build a Boosted Model" (entirely synthetic: N=24, seed=7, formula from
  the manifest's `gradient_boosting.step_by_step`): stage-0 training MSE =
  16.20, matching `scripts/export_boosting_step_widget.py`'s own algorithm
  exactly (this notebook replicates that algorithm verbatim in the setup
  cell; no ABIDE data involved, so no order-sensitivity applies at all).
- Illustrative sklearn example (`n_estimators=100, learning_rate=0.05,
  max_depth=2, random_state=42`): validation MSE = 18.3254, R² = 0.745349.
  Close to the legacy audit's 18.2258/0.746733 — not order-sensitive enough
  to diverge further at this shallow depth (confirmed live in a real
  Pyodide browser session too: `validation R2 = 0.746`, a few ULPs of
  floating-point drift from the WASM-compiled numpy/scikit-learn build,
  documented directly in `exercise-07-lite.spec.ts`).
- Learning-rate/tree-count sweep (`learning_rate=0.1, max_depth=2`,
  `N_TREES_VALUES=[10, 25, 50, 100, 150, 200, 300]`): validation MSE falls
  from 34.05 (10 trees) to a minimum of 18.73 (100–150 trees) and rises to
  19.37 (300 trees) — the same underfit/best/slight-overfit shape the
  legacy audit reported (its own minimum ≈18.78 at 100–150 trees, 19.58 at
  300).
- "Choosing When to Stop" curve (same settings, `n_estimators=300`, via
  `staged_predict`): training MSE falls to 0.81 by 300 trees (an exact
  match to the legacy audit) while validation bottoms out around 100–150
  trees and rises to 19.37 by 300.
- Complete pipeline (12-candidate reduced grid — `lr/n_estimators` pairs
  `[(0.03,50),(0.05,100),(0.1,100),(0.1,200)]` × `max_depth` in `[1,2,3]`,
  `KFold(5, shuffle=True, random_state=13)` on the 753-row development
  partition): **this notebook's own data source selects
  `(learning_rate=0.1, n_estimators=200, max_depth=2)`**, mean CV MSE =
  27.4236; refit on all 753, evaluated once on the locked 251-row test:
  test MSE = 29.3842, R² = 0.685223. The legacy audit selected
  `(..., max_depth=3)`, mean CV MSE = 27.2085, test MSE = 32.3679, R² =
  0.653261 — a genuine, honestly-computed, **different** selection driven
  entirely by the data-source column-order difference explained above, not
  a bug in either notebook. Both are legitimate outcomes of the identical
  declared procedure. This notebook's own number (not the legacy one) is
  what its check cells and reference-execution tests assert against.
- Model-family comparison (`fair_tree_settings=dict(max_depth=6,
  min_samples_leaf=5, random_state=42)`, `n_estimators=50`,
  `max_features=19`, same 753/251 split): Single tree MSE = 71.2880 R² =
  0.2363; Random Forest = 35.6616 / 0.6180; gradient boosting reuses the
  pipeline's own 29.3842/0.685223 (no second locked-test read). Differs
  from the legacy audit's 70.13/0.249, 38.20/0.591, 32.37/0.653 for the
  same reason; gradient boosting still has the lowest test MSE of the
  three, reproducing the legacy notebook's own finding.

## Common notebook contract

Both generators follow `scripts/generate_exercise_05_notebook.py`'s pattern
exactly: a `Blank(student, reference, id, tags)` class; `--student` /
`--reference` / `--check` / `--write`; a hidden, collapsed setup cell
duplicating (never importing) the checked-question helpers
(`make_single_choice_question`, `make_multi_choice_question`) and
`load_abide_age_brain_table()` (same-origin CSV first, pinned public TSV
fallback); a "Run the cell below first" notice; cell ids of the form
`wp46-NNN-slug`; every blank's check cell degrading to "Not complete yet"
rather than raising; `# YOUR CODE HERE` stubs with commented, non-executable
hints; "Required output name(s): ..." as the last line of each activity's
instructions. Each generator is fully self-contained (WP41 maintainer guide
section 4.7) — neither imports from the other or from any prior exercise's
generator.

## Exercise 6 — Decision Trees: what changed, section by section

1. **One Regression Tree.** `TREE_FEATURES` renamed to `SMALL_TREE_FEATURES`
   consistently (generator, notebook, diagram, partition plot, and the one
   test assertion that previously pinned the old name — confirmed by
   research that this name appears nowhere else in `scripts/`,
   `book/_static/widgets/`, `interactive/src/`, or the manifest, so the
   rename is fully scoped). Data load/split, the fitted tree, the relabeled
   tree diagram (`format_tree_diagram`), and the 2D partition plot
   (`draw_partition_boundaries`) are all supplied, runnable code —
   preserved from the legacy notebook with no numeric changes (see above).
   The 16-participant "Build a Tree Greedily" activity is preserved (same
   formula, same seed 17, same 3-round root/left-child/right-child
   structure) and ported to native `ipywidgets`: feature/threshold
   dropdowns, Lock/Reveal/Continue/Reset buttons, a live feature-space
   scatter with accepted-split overlays and a candidate-threshold bar
   chart. The activity always advances using the true greedy optimum, not
   the student's proposal, matching the legacy widget's own rule.
2. **How Large Should the Tree Be?** The stopping-criteria table is kept to
   three rows (`max_depth`, `min_samples_leaf`, `ccp_alpha`). `MAX_DEPTHS =
   [1..10]` is fixed. Students fit one tree per depth on
   `X_fit`/`y_fit`, score train/validation MSE, and plot both curves
   (`wp46-activity-depth`, required names `tree_depth_train_mse`,
   `tree_depth_val_mse`, `tree_depth_fig`); the check cell validates depth
   coverage, shape, non-negativity, and a generous-tolerance comparison to
   the audited best depth/MSE — never bit-for-bit equality. A checked
   question ("Which depth should we select before predicting the test
   set?") is answered correctly by "validation MSE," with tie-handling
   explained in the feedback text. The classification-depth contrast is
   kept as a supplied, hide-input-style cell (re-verified live before
   inclusion, per above) with the same interpretation caveats (higher- vs.
   lower-is-better, "does not mean classification is inherently more
   complex").
3. **From One Tree to an Ensemble.** The bagging/Random Forest comparison
   table (3 rows, verbatim) and the root-split-sensitivity demonstration
   (3 seeds, 70% resamples) are preserved as supplied code. "One Tree or
   Many?" is ported to a native `ipywidgets.Dropdown` (number of trees,
   full `[1,5,10,25,50,100]` grid) with two Matplotlib panels (box plot of
   validation MSE across replicates at the selected tree count; MSE vs.
   ensemble size for bagging/RF with a single-tree reference line) — the
   whole (replicate × grid) computation runs once and is cached, so the
   dropdown only looks up and redraws. The third legacy panel
   ("observed vs. predicted, fixed replicate") is dropped as a deliberate
   scope trim (see below). A checked multi-choice question covers variance
   reduction and Random Forest's extra feature-subsampling randomness.
4. **Model comparison (new activity, spec section 6).** This is the one
   genuinely new section relative to the legacy notebook: the previous
   hidden, fully-supplied "fair comparison" cell is turned into a guided
   student activity. Using one shared `cv.split(X)` call (so every model
   sees identical folds — not a separate `cross_val_score` per model),
   students fit Single tree / Bagging / Random Forest at the same fixed
   settings the legacy notebook used and collect per-fold MSE/R² into
   `tree_cv_fold_results` (`wp46-activity-comparison`, the one required
   student output name). A supplied follow-on cell derives `tree_cv_summary`
   (means/sds) and a bar chart with error bars from that dict — never a
   fabricated row. The check cell validates fold counts and that both
   ensembles beat the single tree, with the same generous-tolerance,
   never-say-"wrong" phrasing every other check cell in this course uses.
5. Closing summary trimmed to five bullets plus five takeaway questions: a
   modest reduction from the legacy notebook's more repetitive prose.

## Exercise 7 — Boosting and Gradient Boosting: what changed, section by section

1. **Setup and intuition.** Data load/split identical to Exercise 6's
   recipe (564/189/753/251). The bagging-vs-boosting table (4 rows,
   verbatim) is preserved; no AdaBoost anywhere, per the course plan.
2. **Building a Model One Tree at a Time.** The update-equation math is
   preserved. "Build a Boosted Model" is ported to native `ipywidgets`: a
   learning-rate dropdown, an `IntSlider` stage control with Previous/Next
   buttons, and a checkbox toggling the residual panel between a stage's
   raw tree output and its learning-rate-scaled correction — three
   Matplotlib panels (observations + ensemble prediction; residuals + the
   newest stump; training MSE by stage), all driven by one verbatim
   reimplementation of `export_boosting_step_widget.py`'s stage-building
   algorithm (computed once at setup time, not per interaction).
3. **Gradient Boosting with Scikit-Learn.** The short illustrative example
   and its 4-row parameter table are preserved as supplied code.
4. **Learning Rate and Number of Trees.** A new guided sweep activity
   (`wp46-activity-sweep`; required names `boosting_sweep_results`,
   `boosting_sweep_fig`) replaces what was previously only the interactive
   widget: fixing `learning_rate=0.1, max_depth=2`, students fit one model
   per entry of a fixed, practical `N_TREES_VALUES = [10, 25, 50, 100, 150,
   200, 300]` (a bounded subset of the legacy parameter-explorer's full
   11-value grid, chosen to keep one supplied-code blank's browser compute
   practical while still spanning the underfit/best/overfit shape) and plot
   validation MSE against tree count. "Explore the Boosting Parameters" is
   then ported to native `ipywidgets`: learning-rate and depth dropdowns
   plus a `SelectionSlider` over the full 11-value tree-count grid, backed
   by one bounded, cached (learning_rate × depth) grid computed via
   `staged_predict` (18 real fits, not 18×11) — never refit per slider
   move. The activity's own text states plainly that the locked test set is
   never touched here, matching the legacy widget's `testSetNote`.
5. **Choosing When to Stop.** Preserved as supplied code (same settings,
   same `STOP_N_TREES_GRID`), with the same "300 vs. 120 trees" checked
   written-answer question the legacy notebook used.
6. **A Complete Gradient-Boosting Pipeline.** The reduced-grid rationale
   text (27→12 candidates, computational-cost framing) is preserved
   essentially verbatim from the already-WP35-cleaned legacy prose (no
   author-facing language reintroduced — checked directly against
   `tests/test_wp35_content_audit.py`'s forbidden-phrase list, and one
   instance of "development partition" caught and rewritten to
   "training-and-validation data" during this WP's own verification, before
   this report was written). The guided blank
   (`wp46-activity-pipeline`; required names `boosting_search`,
   `boosting_best_model`, `boosting_test_mse`, `boosting_test_r2`) builds
   `param_grid` as a *list* of per-pair dicts (not a naive 3×3×3 cross
   product), so `GridSearchCV` evaluates exactly the declared 12
   candidates; `GridSearchCV`'s own default `refit=True` performs steps
   4–5 (select by mean CV MSE, refit on all of `X_train`/`y_train`)
   automatically, and the test set is predicted exactly once immediately
   after. A supplied follow-on cell derives `boosting_cv_results` (a tidy
   table) from `boosting_search.cv_results_` directly — no fabricated
   numbers. Students then build two grouped bar charts
   (`wp46-activity-bars`; required names `boosting_bar_fig_a`,
   `boosting_bar_fig_b`) from `boosting_cv_results`: (A) MSE by
   `n_estimators` × `learning_rate` at `max_depth=2` (4 bars, all 4 pairs
   present at that depth); (B) MSE by `n_estimators` × `max_depth` at
   `learning_rate=0.1` (6 bars — the reduced grid's `lr=0.1` slice covers
   only `n_estimators` 100 and 200, which is sufficient coverage; no grid
   revision was needed). A supplied check cell verifies both slices have
   at least 2 candidates and are sourced from the student's own
   `boosting_cv_results`.
7. **Comparing Tree-Based Models.** Preserved as supplied code, reusing
   Exercise 6's exact fair-comparison settings and Section 6's own
   `boosting_test_mse`/`boosting_test_r2` (no second locked-test read for
   gradient boosting). The XGBoost discussion is Markdown-only, inside an
   HTML `<details>` block (the legacy notebook's MyST `{dropdown}` fence
   has no equivalent inside a plain JupyterLite markdown cell, so this is
   a deliberate, cosmetically-different but functionally equivalent
   substitution) — no `xgboost` import anywhere.
8. Closing summary and 6 takeaway questions preserved from the legacy
   notebook's own list, condensed slightly.

**A note on the "six actions" image**: the WP46 spec's Exercise 7 §5
mentions "the six actions shown in the author's image." Direct inspection
of the legacy notebook, WP32/WP35's specs and reports, and every widget
data/config artifact found no such image or figure asset anywhere in this
course — the six actions have only ever existed as a plain numbered
Markdown list in the legacy notebook's own Section 6 prose. This migration
preserves that same six-item numbered list (see the pipeline instructions
above); no new image was fabricated to match the spec's wording, since
doing so would not reflect anything that already exists. Flagged here for
the course author rather than silently assumed.

## Deliberate scope trims (documenting per the WP's own instruction)

- Exercise 6's "One Tree or Many?" widget drops the legacy panel 3
  ("observed vs. predicted, fixed replicate 0"): the two remaining panels
  (variance-across-replicates box plot; MSE-vs-ensemble-size curve) already
  carry the section's stated lesson (averaging and larger samples reduce
  variance), and dropping the third bounds the widget's own setup-time
  compute (5 replicates × 6 tree-count grid points × 2 ensemble types × up
  to 100 trees each = 60 real fits, already the heaviest single
  once-per-notebook-load computation in Exercise 6).
- Exercise 7's learning-rate/tree-count sweep activity uses a 7-value
  `N_TREES_VALUES` list rather than the legacy parameter-explorer's full
  11-value grid, for the same reason — it is a *student-written* loop
  (unlike the explorer widget's own cached-and-precomputed grid), so its
  browser cost scales directly with list length in a way the guided blank
  itself does not hide.
- Neither trim altered any audited number materially or removed a
  pedagogical point the section's surrounding text claims to make — see
  "Numbers verified before writing a line" above for the actual curve
  shapes both trims still reproduce.
- WP45's own nested-CV diagram (Exercise 4, non-theme-adapting in dark
  mode) was **not** touched, per the WP's explicit instruction not to fold
  unrelated WP45 polish into this WP without a concrete need — none arose.

## A no-cascade check

Both untouched student templates were executed cell-by-cell (the same
offline executor `tests/test_exercise_0{6,7}_reference_execution.py` uses,
applied to the *student*, not reference, notebook) before any browser
testing: zero exceptions in either notebook; every blank's own check cell
printed its "Not complete yet" guidance in place of a result. Confirmed
again live in a real Chromium session (`.jp-mod-error` count of 0 on
"Run All Cells" for both exercises' untouched templates).

## Verification and stop conditions

### Generators
`python scripts/generate_exercise_06_notebook.py --check` and
`python scripts/generate_exercise_07_notebook.py --check` (and the
corresponding `_transition_page.py --check`) all pass: every committed
output file is byte-identical to what the generator produces now.

### Reference-notebook execution (offline, exact)
`tests/test_exercise_06_reference_execution.py` (12 tests) and
`tests/test_exercise_07_reference_execution.py` (12 tests) both pass:
executing every cell's actual source, in order, in one shared namespace
(the same semantics a kernel uses — never `nbclient`, since both
notebooks' native widgets use `ipywidgets.Output()` as a context manager,
which hangs a real ZMQ kernel with no frontend attached), from a clean
working directory containing only `book/lite/files/data/abide_age_brain.csv`.
Every established number above is asserted against either a literal or the
notebook's own recomputed values; check-cell behavior (correct /
incorrect-but-complete / unfinished) is exercised directly against the
shared check-cell source, without a browser, for all five blanks across
both notebooks.

### Structural / offline
`tests/test_exercise_06_lite_notebook.py` (31 tests) and
`tests/test_exercise_07_lite_notebook.py` (33 tests) pass: required blanks
exist and are not pre-solved even in comment form (except as
non-executable hints), no `NotImplementedError`, no install cells, no
iframe or legacy-widget-config reference anywhere, checked questions all
carry `correct_index=`/`correct_indices=`, no WP/script self-reference
leaks into student-facing text, and the student template / portable copy /
reference notebook stay structurally synchronized cell-by-cell (only
`Blank`-tagged cells may differ). `tests/test_exercise_06_transition_page.py`
(8 tests) and `tests/test_exercise_07_transition_page.py` (8 tests) pass:
H1 unchanged, correct Lite/download links, no raw-GitHub or Colab deep
link, no duplicated analysis code.

### Repository-wide content audit
`tests/test_wp35_content_audit.py` (7 tests, scanning every canonical and
portable notebook including the two new transition pages and portable
copies) passes — no author-facing phrase, no stray WP-number reference, no
"development partition" phrasing anywhere a student can see it (one
instance was caught in Exercise 7's pipeline instructions during this WP's
own verification pass and rewritten to "training-and-validation data"
before this report was written). `tests/test_exercise_manifest.py`,
`tests/test_wp19_content_audit.py`, `tests/test_wp24_content_audit.py`,
and `tests/test_wp25_content_audit.py` all pass unchanged.

### Full offline Python suite
`.venv/bin/python -m unittest discover -s tests`: **1067 tests, OK
(skipped=11)** — a clean full pass across all ten built exercises, run
twice (the first run, started before `tests/test_exercise_07_notebook.py`
was deleted mid-run, showed 19 failures + 12 errors, every one of them in
that one now-deleted legacy test file, whose assertions targeted the old
pre-migration Exercise 7 content; the second run, after deletion, is the
1067/OK result quoted above and reported here). **Measured wall-clock:
~21 minutes both times (1271–1281s)** — see "Tests that take longer than
5 minutes" below.

### Frontend
`npx tsc --noEmit` (from `interactive/`) passes with no errors, both
immediately after the Exercise 6/7 spec rewrites and after the subsequent
removal of the now-fully-dead cross-chapter Plotly dark-mode snapshot
helpers (see "Build tooling" below).

### Jupyter Book + JupyterLite build
`jupyter-book build book --all` succeeds (2 pre-existing, unrelated
warnings only: a missing `logo.png`, and `book/README.md` not in any
toctree — both present before this WP). `jupyter lite build --config
book/lite/jupyter_lite_config.json --lite-dir book/lite --output-dir
book/_build/html/lite` succeeds; `exercise_06.ipynb`, `exercise_06_portable.ipynb`,
`exercise_07.ipynb`, and `exercise_07_portable.ipynb` all copy into the
built `lite/files/` tree correctly, with no per-exercise JupyterLite
registration needed (`book/lite/overrides.json` and
`book/lite/jupyter_lite_config.json` are both exercise-agnostic).

### Playwright, built book (real headless Chromium, actual combined build)
Run individually first, per WP45's own precedent, before attempting a
combined run:

- `chapter06.spec.ts` / `chapter07.spec.ts` (rewritten to the
  transition-page-only pattern, mirroring `chapter05.spec.ts`): both pass
  — no iframe, exactly one correctly-labeled Lite link, a working
  download link, no top-bar Colab button, no raw-GitHub/Colab deep link.
  Fast (seconds).
- `exercise-06-lite.spec.ts`, each test run standalone first to isolate two
  live bugs this WP found and fixed (documented in full, not glossed
  over): (1) the "One Tree or Many?" dropdown-change test initially
  asserted against `.jp-OutputArea-output` scoped to the widget cell,
  which never changes for content rendered inside a nested
  `ipywidgets.Output()` context (the same structural gap
  `scripts/smoke_portable_notebook.py`'s own docstring already documents
  for a different exercise) — fixed by asserting against
  `page.locator("body")` instead, exactly like `exercise-04-lite.spec.ts`'s
  proven "sample size:" widget test, plus adding one trailing `print()` so
  the printed summary text actually changes with the dropdown (the
  ensemble widget's final output had been a Matplotlib figure with no
  text at all); (2) the teacher-completed path's post-fill wait after the
  model-comparison blank was initially too short (30s) for that blank's
  real cost (3 models × 5 folds on the full 1004×360 cohort) — increased
  to 90s. **After both fixes, the full 7-test file was run together once,
  cleanly: 7/7 passed in ~15.2 minutes** (see "Tests that take longer than
  5 minutes" below — no single test in this file exceeds 5 minutes, but
  the file as a whole does).
- `exercise-07-lite.spec.ts`, same standalone-first approach, found and
  fixed four live issues: (1) the untouched-template illustration check
  asserted `validation R2 = 0.745` exactly; a real Pyodide session's
  WASM-compiled numpy/scikit-learn produced `0.746` — a few ULPs of
  floating-point drift across 100 sequential trees relative to a native
  build, not a correctness issue — relaxed to a 2-decimal `0.74` check,
  documented inline; (2)-(4), all in the teacher-completed-path test: its
  wait after the pipeline blank (`GridSearchCV` over 12 candidates × 5
  folds, up to 200 trees per candidate — by far the heaviest single
  computation in either notebook) went through three corrections before
  landing on a reliable value — 90s, then 300s, then **900s (15 minutes)**
  — because Pyodide's WASM-compiled scikit-learn (no native BLAS; tree
  building is not BLAS-vectorized to begin with) is markedly slower here
  than the ~153s this exact reduced grid takes natively (per
  `book/config/abide_modeling.json`'s own committed
  `gradient_boosting.cv_pipeline.runtime_audit`); an attempt to avoid this
  cost by running only the newly-filled cell forward (instead of a full
  "Run All Cells" after each blank) was tried and reverted after it proved
  unreliable (JupyterLab's windowed cell list does not reliably keep an
  off-screen "next" cell selected across a wait) — replaced with an
  explicit `runCell()` helper that re-locates and clicks each target cell
  by its own anchor text before running it, and an explicit 60s settle
  wait after the (cheaper, but non-trivial: 7 `GradientBoostingRegressor`
  fits) sweep blank, which the same investigation found was also
  originally under-waited. **With all of this, the teacher-completed-path
  test alone passed in ~19.5–20.3 minutes** (measured twice). A **full
  7-test run of this file together** then showed **5 passed, 2 failed**
  (~32.4 minutes total) — the two failures were in the cheaper
  untouched-template tests that had each already passed standalone, with
  the same symptom (a fixed wait that was sufficient in isolation was not
  sufficient after several Pyodide-heavy tests had already run in the same
  worker/browser process). This is the same resource-contention pattern
  WP45's own report already documented and explicitly anticipated
  recurring at this exercise count, not a newly discovered functional
  defect — every one of this file's 7 tests has demonstrably passed at
  least once against the real, final notebook content.

### Full combined Playwright book suite (all ten built exercises)
**Not attempted, deliberately, and this gate is left open.** The evidence
above — a single exercise's own `*-lite.spec.ts` file already showing
cross-test resource contention at 7 tests, one of which alone takes ~20
minutes — makes a combined run across all ten exercises' specs very likely
to hit the same stall WP45's own full-suite re-run hit at only 5–6
Pyodide-heavy files, this time at a much higher likely total wall-clock
cost. Per the WP's own explicit instructions ("diagnose actual failures;
do not weaken checks, loop on speculative reruns, or call a prior run a
clean pass" and "if the full run cannot finish, report the limitation
explicitly and leave integration/release gates open"), this report does
not fabricate a green combined-suite status. Every individual exercise
file (1 through 7's own lite/transition specs) has its own confirmed-green
run on record; the course author should decide when to spend the
wall-clock budget a full combined run would need (see the time estimates
below) and, per WP45's own precedent, consider `--workers=1` or `=2`
explicitly when they do.

## Tests that take longer than 5 minutes (for planning future runs)

Per request, every command/test observed to take longer than 5 minutes
during this WP's own verification, with its measured wall-clock time:

| Command | Measured time | Why |
| --- | --- | --- |
| `exercise-07-lite.spec.ts`'s "teacher-completed path" test, run alone (`--grep "teacher-completed"`) | **~19.5–20.3 min** | Section 6's `GridSearchCV` pipeline blank (12 candidates × 5 folds, up to 200 trees/candidate) run inside Pyodide's WASM-compiled scikit-learn; this single blank's own execution is the dominant cost (budgeted 900s/15 min of wait alone). |
| `exercise-07-lite.spec.ts`, full file (all 7 tests, `--workers=1`) | **~32.4 min** | The teacher-completed-path cost above, plus two tests that showed resource-contention flakiness after several prior Pyodide-heavy tests in the same run (each passed standalone in ~3.2 min). |
| `exercise-06-lite.spec.ts`, full file (all 7 tests, `--workers=1`) | **~15.2 min** | No single test exceeds 5 minutes (the slowest, the teacher-completed path, is ~4.7 min) — only the file's total crosses the 5-minute mark. |
| `.venv/bin/python -m unittest discover -s tests` (full offline suite, all ten exercises) | **~21 min** (1271–1281s, measured twice) | Cumulative cost of every exercise's own reference-execution/audit tests, including this WP's two new ones. |
| A full combined Playwright run across all ten exercises | **Not measured — likely 45+ min, possibly much more** | Not attempted this WP (see above); flagged here so a future attempt is budgeted, not assumed quick. |

Everything else this WP ran (generator `--check`, the structural/
transition-page test triads, `tsc --noEmit`, `jupyter-book build`,
`jupyter lite build`, `chapter06.spec.ts`/`chapter07.spec.ts`, and each
`exercise-0{6,7}-lite.spec.ts` test run individually except the one named
above) completed in well under 5 minutes.

## Build tooling: files updated

- `book/config/exercise_manifest.json`: `$comment` extended to name
  Exercises 6–7 as built-and-locally-verified-pending-Colab, alongside 3–5;
  the actual per-exercise entries for 6 and 7 are untouched
  (`migrationState: "legacy"`, every Lite field `null`), matching the
  existing entries for 3, 4, and 5 exactly. `tests/test_exercise_manifest.py`
  needed no changes (it already hardcodes `migrated == [1, 2]`
  unconditionally).
- `book/_static/launch-buttons.js`: `chapter_06`/`chapter_07` removed from
  `PAGE_TO_PORTABLE`; the file-header comment and its list of transition-
  page generator scripts both extended to name Exercises 6–7 alongside
  1–5.
- `interactive/e2e-book/launch-buttons.spec.ts`: the `CHAPTERS` array (page
  → portable-notebook → Colab-button mapping) no longer includes Chapters 6
  or 7; two new "gets no top-bar Colab button" suppression tests added for
  them, matching the existing Chapter 1–5 pattern.
- `interactive/e2e-book/iframe-height-contract.spec.ts`: the four
  Exercise-6/7 iframe cases removed from `CASES`; the file's own
  explanatory comment extended to cover Exercises 1–7 (there is no
  iframe-height contract left to check for any JupyterLite-native
  exercise).
- `interactive/e2e-book/wp22-cross-chapter-dark-mode.spec.ts`: the one
  remaining legacy iframe test in this file ("Exercise 6 — one tree or
  many?: initial dark load", the last surviving Plotly-snapshot case)
  replaced with a JupyterLite-app-theme test matching Exercises 2–5's own
  existing replacements; a second, equivalent test added for Exercise 7.
  With that replacement, every helper this file's original Plotly
  `_fullData`/`_fullLayout` color-snapshot technique needed
  (`gotoDark`, `activityFrame`, `snapshotPlot`, `assertDarkFigure`,
  `waitForBookReady`, the dark-palette constants, and the `PlotSnapshot`
  interface) had zero remaining call sites anywhere in the file — removed
  outright (required for `tsc --noEmit`'s `noUnusedLocals`/
  `noUnusedParameters`, not optional cleanup), with the file's header
  comment rewritten to explain why. `interactive/e2e-book/chapter07-dark-mode.spec.ts`
  (a dedicated Plotly-color regression guard for Exercise 7's two old
  iframe activities) is deleted outright — mirroring WP45's exact
  treatment of `chapter05-visual-policy.spec.ts` — since there is no
  iframe left on that page for it to check.
- `scripts/build_portable_notebook.py`: `CHAPTER_06`/`CHAPTER_07` removed
  from the `NOTEBOOKS` registry dict (their `NotebookSpec` constants left
  in place, unused, matching the existing precedent for chapters 1–5); the
  module docstring's `--notebook` choices list and explanatory comment
  updated to name chapters 1–7 as absent. `--check` passes against the
  three still-registered chapters (8, 9, 10).
- `scripts/smoke_portable_notebook.py`: the `chapter_06`/`chapter_07`
  `SMOKE` entries removed, with the same explanatory comment template
  (`ipywidgets.Output()` / `nbclient` hang) already used for chapters 1, 4,
  and 5; the module docstring's bullet list updated to match.

No changes were made to Exercises 1–5 or 8–12's own content, to
`Homework_Materials/`, to `book/lite/extensions/course-toolbar/`, to
`book/lite/overrides.json`, to `book/lite/jupyter_lite_config.json`, or to
any legacy React widget component/export-data script/config
(`interactive/src/components/tree-greedy-split.ts`, `tree-ensemble-compare.ts`,
`boosting-step-by-step.ts`, `boosting-parameter-explorer.ts`, and their
registry entries, `book/_static/widgets/configs/*.json`,
`book/_static/widgets/data/*.json`, `scripts/export_tree_greedy_widget.py`,
`scripts/export_tree_ensemble_widget.py`, `scripts/export_boosting_step_widget.py`,
`scripts/export_boosting_parameter_widget.py`) — all left in place, unused,
matching the exact precedent WP44/45 already set for the analogous
Exercise 1–5 components.

## The Colab blocker

This session has no real Google Colab access (no browser session against
`colab.research.google.com`). Local verification instead ran the actual
reference/portable/student notebooks through a real Python execution
(reproducing every established number above exactly, from the committed
same-origin CSV) and a real headless-Chromium Playwright session against
the actual combined local build (both exercises, both the untouched and
teacher-completed paths, every checked question and native widget, 390px,
reset/back, download-contains-edits). Real Colab verification for
Exercises 6 and 7 is a required, explicit open item for the course author,
exactly as it already is for Exercises 3, 4, and 5.

## WP45's still-open gates, carried forward

Per the WP's explicit instruction to keep these honest rather than treat
them as closed by unrelated later work:

- Exercises 3, 4, and 5's real-Colab acceptance gate (WP41 maintainer
  guide section 11) is **still open**. This WP does not touch those
  exercises and does not affect that gate either way.
- WP45's own full combined Playwright suite: its first full run was
  132/133 (one failure, a dark-mode CSS-variable assertion on Exercise 4's
  nested-CV diagram, fixed and re-verified 1/1 in isolation); a
  from-scratch full re-run then stalled under real machine load
  (contention across six parallel JupyterLite/Pyodide cold starts, not a
  test failure) and was terminated deliberately rather than reported as a
  second clean pass. That specific open item (a clean, uninterrupted
  from-scratch full-suite run covering Exercises 1–5) is **still open**;
  this WP did not attempt a combined run spanning all ten exercises (see
  "Full combined Playwright book suite" above), so it provides no new data
  toward closing WP45's specific item either way. It does provide a
  closely related, corroborating data point: `exercise-07-lite.spec.ts`
  alone (7 tests, one exercise) showed the same class of resource-
  contention flakiness WP45 described, at a smaller scale — consistent
  with, not a resolution of, WP45's finding.

## Colab-proxy artifacts prepared for the author

Per the WP's explicit instruction, a private, **not committed, not
published** set of files was prepared for the course author's later manual
Colab check, kept outside the repository entirely (this session's own
scratch directory, not `Homework_Materials/` and not any git-tracked
path):

- `exercise_06_TEACHER_FILLED_private.ipynb` / `exercise_07_TEACHER_FILLED_private.ipynb`
  — verbatim copies of `scripts/reference_notebooks/exercise_0{6,7}_reference.ipynb`,
  every blank filled with the reference solution.
- `exercise_06_student_unfilled_portable.ipynb` / `exercise_07_student_unfilled_portable.ipynb`
  — verbatim copies of the actual, unmodified files a student would
  download (`book/downloads/chapter_0{6,7}/exercise_0{6,7}_portable.ipynb`),
  kept alongside the completed copies for side-by-side comparison; the
  real, canonical copies a student downloads remain the ones committed at
  those repository paths.
- `COLAB_CHECKLIST.md` — the WP41 maintainer guide's own section 12
  checklist template, filled in per exercise with this WP's actual
  established numbers and every checked-question topic to confirm, both
  marked **UNVERIFIED (real Colab not reachable from this session)** with
  the blocker stated, ready for the author to complete the moment real
  Colab access is available.

These files were reported to the user directly at the end of this WP
(their local path is not repeated in this report to avoid implying it is a
repository path); they are not referenced from any committed file.

## Deviations and decisions requiring course-author attention

1. **Exercise 7's pipeline selects a different configuration than the
   legacy notebook** (`max_depth=2`, not `3`) on this same-origin data
   source, with a correspondingly different locked-test MSE/R² (29.4/0.685
   vs. the legacy 32.4/0.653) — see "Numbers verified before writing a
   line" for the full explanation (a genuine column-order sensitivity in a
   `max_depth`-searching CV grid, not an error). The course author should
   decide whether this deserves a one-line note in the notebook itself
   beyond what is already there, or whether the current framing (report
   only, no notebook-visible caveat, since the notebook's own numbers are
   internally consistent and correctly derived) is sufficient.
2. **The "six actions" image** the WP46 spec names does not exist anywhere
   in this course's current materials (see above) — the six actions are,
   and remain, a plain numbered list. Flagged for the author in case a
   diagram was expected to exist elsewhere and was simply not found.
3. Exercise 6's ensemble widget and Exercise 7's parameter-explorer widget
   both use a bounded subset of their legacy widgets' original grids
   (Exercise 6 keeps the full `n_trees` grid but a 3-seed subset of the
   original 5-seed sensitivity estimate is **not** used — the full 5 seeds
   are kept; Exercise 7's *guided sweep blank* uses a 7-value list, a
   proper subset of the interactive explorer's own 11-value grid, which
   itself is kept in full for the explorer widget). See "Deliberate scope
   trims" above for the reasoning; flagged here in case the author wants
   the sweep activity's list widened once real Colab timing data is
   available.
4. `book/README.md` still not in any toctree (pre-existing warning,
   unrelated to this WP, left as found).

## Confirmation

No merge, no push, no deployment, and no GitHub Actions interaction at any
point in this WP. `Homework_Materials/` was never inspected or modified.
Exercises 1–5 and 8–12's own content is untouched except for the narrow,
required cross-referencing changes to shared test/build-tooling files
listed under "Build tooling" above. The manifest's Exercise 6 and 7 entries
remain `migrationState: "legacy"`, exactly like Exercises 3, 4, and 5,
pending the course author's own real-Colab check.
