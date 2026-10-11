# WP53 exact changelog

Starting SHA (local and `origin/main`): `66aa6b0` ("WP52: reports -- 15-item
acceptance table, benchmark provenance, real CI results, and live-site
verification").

Checkpoint branch: `checkpoint/wp53-pre-work`, at `66aa6b0`, created before
any WP53 edit.

All WP53 work lands as commits on `feature/wp53-notebook-polish-and-deploy`,
fast-forward-merged into `main` and pushed as the one production release
this WP authorizes (see the report's "Final git state" for the exact SHAs
once pushed).

The WP53 spec itself was delivered as `WPs/WP53_NOTEBOOK_POLISH_AND_DEPLOY.zip`
(spec markdown + the replacement nested-CV PNG). Per this repo's own
convention (every WP lives as a plain `.md` under `WPs/`, never a zip), the
spec markdown is committed as `WPs/WP53_NOTEBOOK_POLISH_AND_DEPLOY.md` and
the zip discarded; the PNG is committed directly at its real destination,
`book/lite/files/data/exercise_04_nested_cv_diagram.png` (see below).

## Files changed

```
A  WPs/WP53_NOTEBOOK_POLISH_AND_DEPLOY.md
M  book/downloads/chapter_0{1..9}/exercise_0{1..9}_portable.ipynb  (9 files)
M  book/lite/files/data/exercise_04_nested_cv_diagram.png
M  book/lite/files/exercise_0{1..9}.ipynb                          (9 files)
M  book/lite/files/exercise_0{1..9}_portable.ipynb                 (9 files)
M  interactive/e2e-book/exercise-0{1..9}-lite.spec.ts              (9 files)
A  interactive/e2e-book/warning-sweep.spec.ts
M  scripts/generate_exercise_0{1..9}_notebook.py                   (9 files)
M  scripts/reference_notebooks/exercise_0{1..9}_reference.ipynb    (9 files)
M  scripts/render_exercise_04_nested_cv_diagram.py
M  tests/test_exercise_0{1..9}_lite_notebook.py                    (9 files, no 09 lite-notebook test needed a new case beyond the shuffle one)
M  tests/test_exercise_0{1..9}_reference_execution.py              (9 files)
```
75 files changed, 2418 insertions(+), 518 deletions(-) (`git diff --stat`
against the starting SHA).

## Per-generator summary

- **`scripts/generate_exercise_01_notebook.py`**: `import random` added to
  the notebook's own hidden setup-cell source (not the generator's top-level
  imports -- the shuffle runs inside the browser kernel, at notebook
  runtime). All 3 questions get a `shuffle_seed`; `show_question()` rewritten
  to shuffle displayed option order deterministically through that seed
  before building the widget.
- **`scripts/generate_exercise_02_notebook.py`**: same `import random` +
  shuffle mechanism for 4 of its 5 questions. `q-honest-evaluation` is a
  documented exception (no `shuffle_seed`): its three options are the exact
  "A."/"B."/"C." row labels of a table displayed just above it, referenced
  by letter in the markdown below -- shuffling it would desynchronize the
  question from both.
- **`scripts/generate_exercise_03_notebook.py`**: `load_abide_classification_table()`
  rebuilt to append SEX/SITE via one `pd.concat` instead of two sequential
  column assignments (no more pandas `PerformanceWarning`). The "Fit the
  model" cell's `try/except NameError: raise RuntimeError(...)` replaced
  with the same graceful `if all(...): ... else: print("Not complete yet: ...")`
  guard every other check cell in this notebook already uses. All 5
  questions get a `shuffle_seed` + the same shuffle mechanism.
- **`scripts/generate_exercise_04_notebook.py`**: `_STABILITY_SAMPLE_SIZES`
  (and its docstring-literal copy `_SAMPLE_SIZES_LITERAL`) changed from
  `[30, 50, 75, 100, 150, 250, 500, "all"]` to `[150, 250, 500, "all"]`;
  dropdown default 100 -> 150; the checked question's own worked example
  "30 or 50" -> "150 or 250". `NCV_DIAGRAM_IMAGE_FILENAME`'s own comment
  updated to describe the new source image (no path/filename change --
  already wired to the same asset). All 3 questions get a `shuffle_seed`.
- **`scripts/generate_exercise_05_notebook.py`**: all 3 questions get a
  `shuffle_seed` + the shuffle mechanism (no other generator-code changes
  this exercise's own WP53 items needed).
- **`scripts/generate_exercise_06_notebook.py`**: `format_tree_diagram()`'s
  `plot_tree` call: `figsize=(9, 5)` -> `figsize=(15, 9), dpi=140,
  fontsize=12`, `fig.tight_layout()` added. Both "Think first:" -> "Think:".
  `_greedy_render()`'s unconditional `ax.legend()` guarded by
  `if ax.get_legend_handles_labels()[0]`; the left-plot threshold line now
  also draws an always-visible dashed "current selection" preview before
  locking (new radii/offsets for the existing locked-state line too, to
  keep the two styles visually distinct); both the Feature and Threshold
  dropdowns now `.observe(_greedy_render, ...)` so the whole widget redraws
  immediately on any change, not only after a button click. Section 3's
  classification-contrast cell: "(development data only)"/"development ="
  -> "(train-val data only)"/"train-val =" (counts unchanged). The
  "Number of trees" dropdown gets `style={"description_width": "initial"}`
  plus a new small scoped CSS class (`ens-ntrees-row`) wrapping it in its
  own `HBox`. All 4 questions get a `shuffle_seed`; one seed (`137`,
  `q-bagging-reduces-variance`) was deliberately chosen, after the first
  pass left all four of this exercise's own questions landing at the same
  shuffled position, so that at least two distinct positions appear within
  this one exercise.
- **`scripts/generate_exercise_07_notebook.py`**: the "Show the newest
  tree's correction after scaling by the learning rate" `Checkbox` gets
  `layout=widgets.Layout(width="100%")` and is wrapped in its own `VBox`
  carrying the `checked-question` CSS class (this notebook's own existing
  wrap rules, reused rather than duplicated). The GridSearchCV pipeline
  blank's commented-but-complete solution (`param_grid = [...]` /
  `cv = KFold(...)` / `boosting_search = GridSearchCV(...)` /
  `boosting_search.fit(...)` / `boosting_best_model = ...best_estimator_`)
  replaced with a numbered prose hint, matching this course's own
  established style for a hard exercise. All 3 questions get a
  `shuffle_seed`.
- **`scripts/generate_exercise_08_notebook.py`**: the PCA blank's commented
  complete solution replaced with the WP's own three-line example pattern
  (`# Xs = ...` / `# pca_explore = ...` / `# X_pca = ...`). "Required output
  name: `pca_variance_fig`/`pca_scatter_fig`/`pca_loadings_fig`." reworded to
  "Your figure should be defined under the name `...`." (the two *plural*
  "Required output names:" instances for `Xs`/`pca_explore`/`X_pca` and
  `kmeans_results`/... are untouched -- not named by the WP). The
  threadpoolctl `JsProxy.as_object_map()` `RuntimeWarning` filter
  (identical message/category match already used in Exercises 2 and 4)
  added to this notebook's setup cell, which never had it. All 6 questions
  get a `shuffle_seed`.
- **`scripts/generate_exercise_09_notebook.py`**: the PCR/PLS widget's
  legend `loc="lower right"` -> `loc="upper left"`; `axes[0].margins(0.3)`
  added; each of the four directional annotations ("PC1 (fixed)", "PC2
  (fixed)", "true signal", "PLS direction") given its own distinct, fixed
  pixel-space `xytext`/`textcoords="offset points"` (previously placed
  exactly along the arrow direction at a fixed data-space radius, which
  could stack multiple labels exactly on top of each other when two arrows
  became collinear). "...clearly labeled above." dropped from the
  synthetic-data note. SVR task wording: "not run here, since Pyodide has
  no GPU/multiple threads and..." -> "we skip that here for computational
  reasons:...". (This exercise's question shuffle mechanism already existed
  from WP52 and needed no change.)
- **`scripts/render_exercise_04_nested_cv_diagram.py`**: docstring banner
  added marking it superseded by the course author's own replacement image
  -- kept only as a historical record of the diagram's original
  construction; must not be re-run to "refresh" the committed PNG.

## Asset

- **`book/lite/files/data/exercise_04_nested_cv_diagram.png`**: replaced
  (same path/filename) with the packaged `WP53_nested_cv_diagram.png`,
  re-encoded from 1.8MB RGBA truecolor to a 364KB, 32-color palette PNG at
  its original 1831x859 resolution -- visually identical at every size
  checked, just not bloating the repo or the notebook's own base64-embedded
  attachment payload by 5x for no visual benefit.

## Test files changed

- **Every `tests/test_exercise_0N_lite_notebook.py` (01-09)**: a new
  `test_every_question_declares_a_shuffle_seed[...]` structural test (01, 03,
  04, 05, 06, 07, 08; 02's version carves out the one documented exception;
  09 already had this from WP52). Exercise-specific additions: 03 (the new
  friendly-guard structural test, replacing the old RuntimeError-expecting
  one), 04 (sample-size-list + diagram-asset-size tests), 06 (six new tests
  covering every one of that exercise's own WP53 items), 07 (checkbox-label
  test), 08 (threadpoolctl-filter test + a stronger no-executable-solution
  test for the PCA blank, replacing a weaker "commented is fine" one), 09
  (three new tests for the legend/margin fix and the two wording changes).
- **Every `tests/test_exercise_0N_reference_execution.py` (01-09)**: a new
  `test_shuffle_is_reproducible_and_varies_positions_across_questions`
  (02's version accounts for the one excluded question); 03 additionally
  gets `test_data_setup_cell_emits_no_performance_warning`.

## Playwright spec files changed

- **Every `interactive/e2e-book/exercise-0N-lite.spec.ts` (01-09)**: fixed
  every pre-existing checked-question interaction that assumed the correct
  answer was always at option position 0 (now shuffled) to select by the
  option's own text instead (01, 02, 03, 04, 05, 06, 07; 08's one
  coincidentally-still-safe `nth()` left as is; 09 already did this from
  WP52). Exercise-specific additions/fixes: 03 (header comment + `runAllCells`
  switched from a fixed wait to genuine kernel-idle polling, now that the
  guard no longer halts execution; the old single "degrades gracefully, guard
  raises" test replaced with "every activity ... degrades gracefully, with
  zero error cells end to end"), 04 (sample-size values 100/"30" ->
  150/"250"; new nested-CV-diagram-visibility test, located by the image's
  own `alt` attribute rather than `scrollToVisible`'s text matching, which
  cannot see `alt=`), 06 (new diagram-resolution, legend-and-reactivity,
  and label-clipping tests; a finer fixed-pixel scroll sweep for the new,
  much-taller diagram cell, since the shared `scrollToVisible` helper's
  coarse percentage-based steps intermittently missed it), 07 (stale
  `fillBlank` anchor `"# param_grid = ["` updated to `"# 1. param_grid = ..."`;
  new checkbox-label test), 08 (new threadpoolctl live-warning-absence
  check; stale solution-text assertion updated to the new placeholder),
  09 (redundant second `runAllCells()` call inside the 390px test's loop
  removed -- it was re-running the whole notebook, including the slow SVM
  grid search, a second time for no benefit, and could leave the next
  anchor's own scroll search timing out; a new finer fixed-pixel
  `scrollToVisibleFine` helper used for both anchors in that test; new
  colorbar/legend live-render check).
- **`interactive/e2e-book/warning-sweep.spec.ts`** (new): course-wide
  browser warning sweep across Exercises 1-9's untouched templates, scoped
  to rendered `.jp-OutputArea-output` text only (not cell source, which
  routinely explains a fix in a comment using the word "warning").

## Verification

See `WPs/reports/WP53_REPORT.md` for full command output, timings, and the
"Bugs found and fixed" section (the WP-number leak this changelog's own
file list reflects the *fixed* state of, the seven pre-existing
position-based Playwright tests, the one stale `fillBlank` anchor, and the
two scroll-timing fixes).

## The push

Fast-forward merged into `main` (`git checkout main && git merge --ff-only
feature/wp53-notebook-polish-and-deploy`, `66aa6b0` -> `4c4c09c`, no merge
commit) and pushed (`git push origin main`), one commit, as the single
production release this WP authorizes.

## Final git state

- `main` (local and `origin/main`, in sync): `4c4c09c`.
- `gh-pages`: `50db44d`, marker `deploy: 4c4c09c70db3b17f1693e9e022c823561e0f1c97`
  -- matches the pushed SHA exactly.
- GitHub Actions run `38118316155` ("Build and deploy Jupyter Book"):
  success; `classify` 7s, `build-and-deploy` 2h3m13s (offline suite 1192
  tests/1766s/11 skipped, combined Playwright suite 123 tests/~1.5h, both
  matching the local pre-push run exactly); `Publish website` ~4s. Full
  details and live-site HTTP verification in `WPs/reports/WP53_REPORT.md`.
- Checkpoint branch `checkpoint/wp53-pre-work` left in place at the
  pre-WP53 tip (`66aa6b0`) for reference.
- This report and the changelog are added in a separate, `WPs/**`-only
  closing commit (`paths-ignore` keeps it from triggering another deploy).
