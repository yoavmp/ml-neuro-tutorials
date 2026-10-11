# WP53 report: notebook polish across Exercises 3-9 and deploy

## Success or failure -- read this first

**Success.** Every numbered item in WP53 is applied to the relevant
generator(s), Exercises 1-9 regenerated and republished, the full offline
test suite (1192 tests) and the full combined Jupyter Book + JupyterLite
Playwright suite (123 tests, including a new course-wide warning sweep)
both pass, the production deploy succeeded, and the live site has been
verified directly (hub listing, each corrected notebook's own route,
downloads, the replacement image, Chapters 10-12 still unpublished).

## Starting state and branch

Began at `main` tip `66aa6b0` ("WP52: reports..."), matching the WP's own
"Authority and starting point": Exercises 1-9 live, this WP touching
content already in production. Checkpoint branch `checkpoint/wp53-pre-work`
created at that tip before any edit; work done on
`feature/wp53-notebook-polish-and-deploy`.

The WP53 spec itself arrived as a zip (`WPs/WP53_NOTEBOOK_POLISH_AND_DEPLOY.zip`,
containing the spec markdown and the replacement nested-CV image); per this
repo's own convention (every other WP lives as a plain `.md` in `WPs/`,
never a zip), the spec is committed as
`WPs/WP53_NOTEBOOK_POLISH_AND_DEPLOY.md` and the zip itself discarded after
extracting both files.

## Acceptance table

### Exercise 3 -- Classification and metrics

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Data/setup cell no longer fragments the table (no pandas `PerformanceWarning`) | Done | `load_abide_classification_table()` now builds `table` via one `pd.concat([table, demographics[["SEX","SITE"]]], axis=1)` instead of two sequential `table["SEX"] = ...` / `table["SITE"] = ...` assignments onto an already ~360-column frame; column values/names/order/row-alignment all unchanged. `tests/test_exercise_03_reference_execution.py::test_data_setup_cell_emits_no_performance_warning` re-executes this exact cell under `warnings.catch_warnings(record=True)` and asserts zero `PerformanceWarning`. |
| 2 | "Fit the model" degrades gracefully instead of raising `RuntimeError` | Done | Replaced `try/except NameError: raise RuntimeError(...)` with the same `if all(name in globals() for name in (...)): ... else: print("Not complete yet: ...")` guard pattern every other check cell in this notebook already uses; a genuine programming error inside the fit path is no longer caught, so it still surfaces normally. Verified offline (blank-template cell-by-cell executor: zero uncaught exceptions end to end) and live in Chromium (`exercise-03-lite.spec.ts`: "every activity depending on the unfilled blanks degrades gracefully, with zero error cells end to end" -- the former guard cell, Section 4's cm/AUC checks, the threshold widget, and the Section 6 imbalance dropdown all show their own "Not complete yet"/"Complete Section N first" message; `.jp-mod-error` count is 0). The teacher-filled path (`filling in every blank reproduces...`) still passes unchanged. |

### Exercise 4 -- Validation and cross-validation

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Sample-size widget begins at 150, 250, not 30/50 | Done | `_STABILITY_SAMPLE_SIZES` (and its literal docstring copy) changed from `[30, 50, 75, 100, 150, 250, 500, "all"]` to `[150, 250, 500, "all"]`; default dropdown value 100 -> 150. Checked question's own worked example updated "30 or 50 participants" -> "150 or 250 participants". `tests/test_exercise_04_lite_notebook.py::test_sample_sizes_begin_at_150_250_not_30_50` asserts the new list and wording, and the old "30"/" 50," are gone from that cell. `tests/test_exercise_04_reference_execution.py::test_stability_widget_default_matches_wp27_audit` re-derives the new default (sample size=150, seed=0) directly from the data and checks it against `scripts/wp27_validation_audit_result.json`'s own `sample_size=150` entry (that audit already covered every size, 150 included, from before this WP). Live: `exercise-04-lite.spec.ts` selects "250" and confirms the printed summary updates. |
| 2 | Nested-CV diagram replaced with the course author's own image | Done | `book/lite/files/data/exercise_04_nested_cv_diagram.png` replaced with the packaged `WP53_nested_cv_diagram.png` (same file name -- already descriptive, and the generator's `NCV_DIAGRAM_IMAGE_PATH`/`_FILENAME` already pointed at it; re-wiring it to a *new* name would have been pure churn for no behavior change). Re-encoded to a 32-color palette PNG (1831x859, 364KB; original PNG was 1.8MB RGBA truecolor) -- visually identical, verified by direct inspection at multiple sizes, with no loss of legibility. The old matplotlib-rendered diagram script (`scripts/render_exercise_04_nested_cv_diagram.py`) is left in place as a historical record only, with a docstring banner marking it superseded so nobody re-runs it and silently clobbers the replacement. Alt text (describing outer-vs-inner CV) is unchanged -- it already matched the new image's layout almost verbatim. Live: `exercise-04-lite.spec.ts`'s new test confirms the `<img>` renders with `naturalWidth > 400` and causes no horizontal page overflow at both desktop and 390px, with the image's own rendered width capped to the 390px viewport. |

### Exercise 6 -- Decision trees

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Regression-tree diagram genuinely readable | Done | `format_tree_diagram()`'s `plot_tree` call: `figsize=(9, 5)` (default auto-shrunk `fontsize=None`) -> `figsize=(15, 9), dpi=140, fontsize=12` explicit -- fixes the actual rendered pixel resolution and text size, not just a CSS display width over the same small raster. Live: `exercise-06-lite.spec.ts`'s new test confirms the rendered `<img>`'s own `naturalWidth >= 1800` / `naturalHeight >= 1000`. |
| 2 | "Think first:" -> "Think:" | Done | Both occurrences in this notebook changed (the other exercise's own unrelated "Think first:" text, Exercise 7, is untouched -- out of scope). `tests/test_exercise_06_lite_notebook.py::test_think_first_replaced_with_think`. |
| 3 | Greedy-tree legend warning eliminated | Done | `ax.legend()` in `_greedy_render()` was called unconditionally, including on the very first, untouched render (no "your proposal"/"greedy optimum" line yet) -- `No artists with labels found to put in legend`. Now guarded: `if ax.get_legend_handles_labels()[0]: ax.legend(...)`. `tests/test_exercise_06_lite_notebook.py::test_greedy_legend_only_requested_when_labels_exist`; live, the widget's own rendered text is asserted to never match `/Warning/` before or after locking. |
| 4 | Feature/threshold dropdowns update the candidate-threshold figure and the left-plot threshold line immediately | Done | Both dropdowns previously only called `_greedy_render()` from button clicks (Lock/Reveal/Continue/Reset); changing Feature only refreshed the threshold dropdown's *options*, and the left plot drew a "your proposal" line only once locked. Added `_greedy_feature_dd.observe(_greedy_render, ...)` and `_greedy_threshold_dd.observe(_greedy_render, ...)`, and a new always-visible "current selection" preview line (dashed, distinct style from the post-lock solid "your proposal" line) drawn from the live dropdown values whenever nothing is locked yet. "Lock My Answer" still commits/enables Reveal; it is no longer required to preview a choice. Live: `exercise-06-lite.spec.ts` changes both dropdowns and asserts the rendered image's own `src` actually changes each time (a real redraw, not just no-crash), then locks/reveals as before. |
| 5 | "(development data only)" / "development = N" -> "train-val" | Done | Both occurrences in the Section 3 classification-contrast cell changed; the underlying counts (753) are unchanged -- only the label. `tests/test_exercise_06_lite_notebook.py::test_train_val_wording_used_instead_of_development`. |
| 6 | "Number of trees" label not clipped | Done | `widgets.Dropdown(..., style={"description_width": "initial"})` plus a small scoped CSS backstop (`.ens-ntrees-row .widget-label { width: auto; white-space: normal; ... }`, the same pattern already verified live for Exercise 9's own widget rows) wrapping the dropdown in its own `HBox`. `tests/test_exercise_06_lite_notebook.py::test_number_of_trees_label_is_not_clipped`; live, `exercise-06-lite.spec.ts` asserts the real rendered label's `scrollWidth <= clientWidth`. |

### Exercise 7 -- Boosting

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Full checkbox label shown, no hidden controls | Done | `widgets.Checkbox(..., layout=widgets.Layout(width="100%"))` wrapped in its own `VBox` with the `checked-question` CSS class (reusing this notebook's own already-verified-live wrap rules, not a new rule). `tests/test_exercise_07_lite_notebook.py::test_scaled_correction_checkbox_label_is_not_clipped`; live, `exercise-07-lite.spec.ts` confirms the full label text is present, `scrollWidth<=clientWidth` at both desktop and 390px, and the Previous/Next Step buttons stay visible alongside it at 390px with no page overflow. |

### Exercise 8 -- Unsupervised learning

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | PCA blank: no commented complete solution | Done | The blank's starter (`# Xs = StandardScaler().fit_transform(...)` / `# pca_explore = PCA(...).fit(Xs)` / `# X_pca = pca_explore.transform(Xs)` -- a complete, directly-runnable-if-uncommented solution) replaced with the WP's own example pattern: `# Xs = ...` / `# pca_explore = ...` / `# X_pca = ...`, one short purpose comment each. `tests/test_exercise_08_lite_notebook.py::test_pca_blank_has_no_executable_solution_even_commented` asserts none of `StandardScaler(`, `PCA(`, `.fit(`, `.transform(` appear anywhere in the blank, commented or not. |
| 2 | "Required output name: X" -> "Your figure should be defined under the name X" | Done | Applied to all three instances (`pca_variance_fig`, `pca_scatter_fig`, `pca_loadings_fig`); the two plural "Required output names:" instances (`Xs`/`pca_explore`/`X_pca` and `kmeans_results`/...) are untouched -- the WP named only the three figure instances. |
| 3 | K-means activity's threadpoolctl warning fixed | Done | This notebook never had the `JsProxy.as_object_map()` RuntimeWarning filter Exercises 2 and 4 already carry for the identical upstream Pyodide/threadpoolctl message -- added, same narrow `message=`+`category=RuntimeWarning` match (never a blanket filter). `tests/test_exercise_08_lite_notebook.py::test_threadpoolctl_warning_narrowly_filtered`; live, `exercise-08-lite.spec.ts`'s teacher-completed test exercises the native "Explore PCA and K-Means" widget (changes both the retained-PCs and k dropdowns) and asserts its own rendered text never matches `/Warning/`. |

### Exercise 9 -- Advanced models

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | PCR/PLS legend and annotations no longer overlap the colorbar | Done | Legend moved `loc="lower right"` -> `loc="upper left"`; `axes[0].margins(0.3)` added so the fixed-radius directional annotations ("PC1 (fixed)", "PC2 (fixed)", "true signal", "PLS direction") stay inside the data view instead of crowding the right edge where the colorbar sits; each annotation also got its own small, fixed pixel-space text offset (not based on the data angle) so the labels stay legible even at settings where two arrows become collinear (e.g. weight on PC1 = 0 or 1) -- verified by direct rendering at w1 in {0, 0.25, 0.5, 0.7071, 0.9, 1.0} x components in {1, 2} (29 renders inspected). One honestly-reported residual: at the few settings where two arrows are *exactly* collinear, their text labels can still touch slightly (an inherent limit of fixed offsets against a continuously rotating angle) -- the colorbar itself and the legend are clear of collisions at every setting checked. `tests/test_exercise_09_lite_notebook.py::test_pcr_pls_legend_and_annotations_do_not_collide_with_the_colorbar`; live, `exercise-09-lite.spec.ts`'s teacher-completed test exercises weight=0.9 (the setting closest to the original bug) and confirms the rendered image is present with no page overflow. |
| 2 | "...clearly labeled above" removed | Done | "This activity uses entirely synthetic data -- not ABIDE -- clearly labeled above." -> "This activity uses entirely synthetic data -- not ABIDE." `tests/test_exercise_09_lite_notebook.py::test_pcr_pls_note_no_longer_claims_clearly_labeled_above`. |
| 3 | SVR wording: no blanket Pyodide/GPU claim | Done | "not run here, since Pyodide has no GPU/multiple threads and GridSearchCV's own internal cross-validation would multiply..." -> "we skip that here for computational reasons: GridSearchCV's own internal cross-validation would multiply...". `tests/test_exercise_09_lite_notebook.py::test_svr_task_computational_reasons_wording`. |

### Course-wide (published Exercises 1-9)

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | "YOUR CODE HERE" audit: no complete hidden solutions | Done | Every blank across all 9 generators reviewed (full inventory below). Two were real complete-solution leaks and fixed: Exercise 8's PCA blank (item 1 above) and Exercise 7's GridSearchCV pipeline blank (`param_grid`/`cv`/`boosting_search = GridSearchCV(...)`/`boosting_search.fit(...)`/`boosting_best_model = ...best_estimator_` were all complete, literal, directly-runnable code, only the final 3 scoring lines used `...`) -- rewritten to the same numbered-prose-hint style already used successfully elsewhere in this course (`tests/test_exercise_07_lite_notebook.py::test_pipeline_blank_is_not_pre_populated_with_the_solution`, strengthened to assert `GridSearchCV(`/`boosting_search.fit(` are absent even commented, not just "commented is fine"). Every other blank reviewed was a genuine partial scaffold (a stub assignment, a numbered prose outline, or at most one trivial given line for a hard exercise) and left unchanged, per the WP's own instruction not to rewrite good hints. |
| 2 | Checked-question answer order: fixed per-question seed, not always-first | Done | **Every** checked question in Exercises 1-8 had its correct answer at options index 0 (Exercise 9 already fixed this in WP52) -- confirmed by direct inspection of all 8 generators before any edit. Replicated WP52's exact mechanism in all 8: each question dict gets a `shuffle_seed=<int>`; `show_question()` computes `order = list(range(len(options))); random.Random(seed).shuffle(order)` once per invocation (deterministic given the fixed seed -- the same order every time the cell runs, never reshuffled across clicks within a render, and identical again on a fresh "Run All"), and remaps the correct index/indices through that order. One question (Exercise 2's `q-honest-evaluation`) is a deliberate, documented exception: its three options are the literal "A. correct"/"B. training score"/"C. invalid" row labels of a comparison table displayed immediately above it, referenced by letter in the markdown right below -- permuting it would desynchronize the question from both the table and that text, matching the WP's own named exception for meaningfully ordered, referenced labels. Across all 31 shuffled questions, correct-answer positions land at 0/1/2 with real variety (not systematically first), and no single exercise has every one of its own questions land at the same position. Verified two ways per exercise: a structural test (every question declares `shuffle_seed=`) and an *executed* test (`test_shuffle_is_reproducible_and_varies_positions_across_questions`, in every `test_exercise_0N_reference_execution.py`) that re-derives each question's shuffled order twice from the same seed and asserts identical results, and that positions are not systematically 0. Live: the full Playwright suite (including every teacher-completed path, which clicks every checked question by its own option *text*, never position) passes end to end -- the pre-existing tests that *did* assume position-0-is-correct (Exercises 1, 2, 3, 4, 5, 6, 7) were all found and fixed to select by text during this WP's own verification (see "Bugs found and fixed" below). |
| 3 | Native-activity browser warning sweep | Done | New permanent spec `interactive/e2e-book/warning-sweep.spec.ts`: runs "Run All Cells" on each of Exercises 1-9's **untouched** JupyterLite template once, scrolls the full windowed notebook, and scans every `.jp-OutputArea-output` element's rendered text (not source code, which routinely mentions "warning" in an explanatory comment) for the word "warning", failing with the exact offending line(s) if found. All 9 exercises pass cleanly in a real Chromium run. This is in addition to, not instead of, the specific Exercise 6 legend and Exercise 8 threadpoolctl checks above (both exercised live by their own specs, changing representative controls, not just inspected statically) and the pre-existing per-exercise warning filters (Exercises 1/2/4/8's `MatplotlibDeprecationWarning`/threadpoolctl filters, Exercise 9's `set_xticklabels` fix from WP52) -- all re-confirmed clean in this same run. No new warning was discovered beyond the two the WP named. |

## Bugs found and fixed during this WP (caught before any of this reached a student)

1. **The question-shuffle fix broke seven pre-existing Playwright tests that assumed the correct answer was always at option position 0** (Exercises 1, 2, 3, 4, 5, 6, 7's own checked-question interactions, plus one in Exercise 8's loop that was coincidentally still safe). Every one rewritten to click by the option's own **text**, matching the convention WP52 already established for Exercise 9. Caught by running the full combined Playwright suite, not by guessing.
2. **"WP53" leaked into eight shipped notebook cells.** My own explanatory comments for several of the fixes above (`# WP53: ...`) were written inside generator string literals that become actual notebook cell source, not the generator's own (never-shipped) comments -- caught immediately by the pre-existing `tests/test_wp35_content_audit.py::test_no_author_facing_phrases_in_portable_notebooks` on the first full offline run. All eight reworded to drop the WP reference while keeping the rationale; notebooks regenerated; the audit is clean on the second full run.
3. **Exercise 7's own Playwright test had a stale `fillBlank` anchor** (`"# param_grid = ["`) that no longer existed after that blank's own rewrite (course-wide item 1). Updated to the new anchor text.
4. **A brittle, pre-existing scroll-to-visible helper (shared boilerplate across every `exercise-0N-lite.spec.ts`) intermittently failed to find a cell whose own output is substantially taller than the windowed panel's internal row-height estimate** -- reproduced live for Exercise 6's now much taller regression-tree image (figsize increase, item 1 above) and, independently, for Exercise 9's SVM widget cell at a 390px viewport. The coarse "5% of total scrollHeight" step can land just past the narrow scrollTop range where such a cell is actually rendered, even though the arithmetic says a step should land inside it. Fixed locally in both specs with a finer, fixed-300px scrollTop sweep instead of a percentage of (dynamically re-estimated) total height; the shared helper used by every other, unaffected test is left exactly as it was, since changing it for everyone risked a different, unverified set of regressions for no benefit to the 25+ tests it already serves correctly.
5. **An editorial overlap this WP did not ask for, but found while rendering the Exercise 9 fix:** the first version of the new legend/annotation fix (moving the legend only) left "true signal"/"PLS direction"/"PC1 (fixed)" text overlapping at a handful of `w1` extremes, where two arrows become exactly collinear. Diversified each label's own fixed pixel-space offset; reduced, not eliminated, at the genuinely-collinear settings (see Exercise 9 item 1's own entry above for the honest residual).

None of (1)-(4) reflect a defect a student would ever have hit (all four are pre-existing or newly-added test-authoring issues, caught and fixed before landing); (5) is a direct, in-scope improvement to the one visual the WP named.

## Verification

### Local, offline (Python)

```
.venv/bin/python -m unittest discover -s tests
```
**1192 tests, ~23 min (two full runs: the first caught the WP-number leak above;
the second, after the fix, is the clean one), 0 failures, 11 skipped**
(pre-existing, unrelated to this WP).

Targeted re-runs during development (generator `--check` for all nine
exercises; `tests.test_wp35_content_audit`; each touched exercise's own
`test_exercise_0N_lite_notebook`/`test_exercise_0N_reference_execution`)
all green before each full run, per the WP's own "scope local work
intelligently" guidance.

### Local, browser (real headless Chromium against the actual combined build)

```
rm -rf book/_build
.venv/bin/jupyter-book build book
.venv/bin/jupyter lite build --config book/lite/jupyter_lite_config.json \
  --lite-dir book/lite --output-dir book/_build/html/lite
cd interactive && npm run test:e2e:book
```
**123/123 passed, 31.0 min** -- the entire combined suite (every
`exercise-0N-lite.spec.ts`, every `chapterNN.spec.ts`, `launch-buttons`,
`sidebar-toggle`, the WP22 cross-chapter dark-mode guard, and the new
`warning-sweep.spec.ts`), confirming no regression to any exercise and
every WP53 fix working live: Exercise 3's graceful no-cascade degradation,
Exercise 4's new sample sizes and diagram, Exercise 6's diagram/legend/
reactivity/wording/label fixes, Exercise 7's checkbox label, Exercise 8's
PCA blank and threadpoolctl fix, and Exercise 9's legend/colorbar and
wording fixes -- all exercised with real control interactions, not static
inspection.

Also ran (unaffected by this WP, confirmed clean):
`npm run typecheck` and `npm run test:unit` (481 tests).

### Teacher-filled portable notebooks, offline

Every touched exercise's `test_exercise_0N_reference_execution.py` executes
`scripts/reference_notebooks/exercise_0N_reference.ipynb` (every blank
filled with the generator's own reference solution) in one shared Python
namespace, the same approach established since WP41. All reproduce their
previously-established numbers unchanged (this WP changed no modeling
code, only presentation/wording/warning/shuffle logic) and additionally now
assert: Exercise 3's data-setup cell emits zero `PerformanceWarning`;
Exercises 1-8's `_QUESTIONS` shuffle deterministically and are not
systematically first.

### Colab

Not re-verified this WP (no modeling-code change in any exercise; WP53 did
not ask for it, unlike a prior migration WP).

## The production push

`scripts/classify_release_change.py` on the actual pushed commit:
```
GATE: full
reason: shared/unknown path(s) changed: book/lite/files/data/exercise_04_nested_cv_diagram.png
  (shared: shared exported data asset); interactive/e2e-book/warning-sweep.spec.ts
  (shared: shared book browser-test fixture/spec); scripts/render_exercise_04_nested_cv_diagram.py
  (shared: shared script (not a per-exercise generator))
affected exercise IDs: [1, 2, 3, 4, 5, 6, 7, 8, 9]
```
Not overridden or second-guessed, exactly as the WP itself anticipated
("expect a `full` release classification").

Pushed: `git push origin main` (fast-forward, `66aa6b0` -> `4c4c09c`).

### The real CI run

GitHub Actions run
[`38118316155`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/38118316155)
("Build and deploy Jupyter Book"): **success**. `classify` job 7s;
`build-and-deploy` job **2h3m13s**. Every step succeeded, including:

| Step | Result |
|---|---|
| Check every migrated exercise generator is not stale (offline, full gate) | passed |
| Unit-test the Python scripts (offline, full gate) | **1192 tests, 1766.181s (~29m26s), OK, 11 skipped** -- identical counts to the local run |
| Check the portable notebook is not stale (offline, full gate) | passed |
| End-to-end test the standalone widget app | passed |
| Build Jupyter Book / Build JupyterLite (Exercises 1-9) | passed |
| End-to-end test the combined book + JupyterLite build (full gate) | **123 passed, ~1.5h** -- identical count to the local run |
| Execute the portable notebook outside the repository (Exercises 1-9 only, full gate) | passed |
| Publish website | succeeded in ~4s |

### Live-site verification (after the deploy, by direct HTTP check against the real published site)

- `gh-pages` branch HEAD commit message: `deploy: 4c4c09c70db3b17f1693e9e022c823561e0f1c97`
  -- matches the pushed `main` SHA exactly.
- `https://yoavmp.github.io/ml-neuro-tutorials/contents.html` links to all
  nine `chapters/chapter_0N/exercise_0N.html` pages (Exercises 1-9).
- All nine chapter pages, all nine JupyterLite notebook routes
  (`/lite/notebooks/index.html?path=exercise_0N.ipynb` for the exercises
  this WP touched), and all nine `exercise_0N.ipynb`/`_portable.ipynb` raw
  files return HTTP 200.
- `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_1{0,1,2}/exercise_1{0,1,2}.html`
  -- all three HTTP **404** (Chapters 10-12 remain unpublished).
- The live `exercise_04_nested_cv_diagram.png` downloaded from
  `/lite/files/data/` is **byte-for-byte identical** to the committed file
  (364372 bytes, 1831x859, confirmed with `diff`).
- `_static/launch-buttons.js`'s live `PAGE_TO_PORTABLE` map contains only
  `chapter_10` (Exercises 1-9 all correctly suppress the top-bar Colab
  button as migrated content).
- Every specific fix checked directly against the live notebook JSON:
  Exercise 3's fit cell contains `"Not complete yet"` and no `RuntimeError`;
  Exercise 4's `_STABILITY_SAMPLE_SIZES = [150, 250, 500, "all"]`; Exercise
  6 contains `"**Think:**"` (not `"Think first:"`), the
  `get_legend_handles_labels` guard, and `"train-val data only"` (not
  `"development data only"`); Exercise 7's full checkbox label text is
  present; Exercise 8 has no `StandardScaler`/`.fit`/`.transform` in its PCA
  blank, has the `as_object_map` threadpoolctl filter, and the reworded
  "Your figure should be defined under the name..." text; Exercise 9 has
  `"not ABIDE."` (not "...clearly labeled above"), the computational-reasons
  SVR wording, and `loc="upper left"` for the PCR/PLS legend. Every
  exercise's hidden setup cell contains its expected count of
  `shuffle_seed=` declarations (spot-checked Exercises 1 and 5, 3 each).

All of this is live-HTTP evidence against the actual published site, not a
repeat of the local/CI browser-automation checks above.

## Final git state

- `main` (local and `origin/main`, in sync): `4c4c09c`.
- `gh-pages`: `50db44d`, marker `deploy: 4c4c09c...`.
- Checkpoint branch `checkpoint/wp53-pre-work` left in place at the
  pre-WP53 tip (`66aa6b0`) for reference.
- This report and the changelog are added in a separate, `WPs/**`-only
  closing commit (`paths-ignore` keeps it from triggering another deploy).
