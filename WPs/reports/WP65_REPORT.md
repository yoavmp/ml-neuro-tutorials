# WP65 Report — Exercise 7 Interactive Activity 2: precomputed boosting-parameter cache

## Overall result: SUCCESS

Activity 2's (learning rate x depth x tree count) grid is now computed
offline, cross-checked against an already-audited number, committed as a
small cache, and embedded in every notebook copy (JupyterLite, portable,
reference) as plain data. The activity's cell now only builds controls and
draws plots. Measured live in a local JupyterLite build: the cell dropped
from a ~172s live-fit loop to ~43ms. Deployed and verified live.

## What changed

### New: `scripts/generate_exercise_07_explorer_cache.py`

A reproducible, offline (no network) script that:

- Loads the notebook's own same-origin CSV (`book/lite/files/data/abide_age_brain.csv`)
  and its sidecar manifest's `predictor_columns` order — the exact source
  and column order `generate_exercise_07_notebook.py` already embeds as
  `_ABIDE_LITE_FEATURES`.
- Reproduces Section 1's (`wp46-104-load`) two splits exactly:
  `train_test_split(..., test_size=0.25, random_state=42, stratify=groups)`
  then `train_test_split(..., test_size=0.25, random_state=7,
  stratify=groups_train)`. The outer test split (`X_test`/`y_test`/`groups_test`)
  is discarded immediately after the split call and never read again.
- Imports `EXPLORER_LR_GRID` / `EXPLORER_DEPTH_GRID` / `EXPLORER_N_TREES_GRID`
  directly from `generate_exercise_07_notebook.py` (single source of truth —
  the cache and the notebook cannot silently drift apart).
- For each of the 18 (learning_rate, depth) pairs, fits one
  `GradientBoostingRegressor(learning_rate, max_depth=depth,
  n_estimators=300, random_state=42)` on `X_fit`/`y_fit`, and reads every
  tree-count step in `EXPLORER_N_TREES_GRID` from that one fit's
  `staged_predict` on `X_fit` and `X_val` — exactly the computation the
  activity's cell always performed, just offline.
- Writes `scripts/exercise_07_explorer_cache_result.json` (9,561 bytes):
  schema version, split sizes/settings, `lockedTestExcluded: true`, the
  three grids, and `grid["<lr>|<depth>"] = {trainMse: [...], valMse: [...]}`.
- `--run` recomputes and writes; `--check` re-validates offline
  (self-consistency, grid completeness, monotone-non-increasing training
  MSE, no field name containing "test" besides the declared flag).

**Cross-check against an already-audited number.** The cache's
`learning_rate=0.1, max_depth=2` row is mathematically required to
reproduce `generate_exercise_07_notebook.py`'s own module-docstring numbers
for Section 4's independently-fit sweep (`staged_predict` at stage *n* from
one fit with `n_estimators=300` is identical to a fresh fit with
`n_estimators=n`, deterministic for the same `random_state`). Confirmed
exactly:

| n_trees | cache val MSE | Section 4 sweep (already audited) |
| --- | --- | --- |
| 10 | 34.052 | 34.05 |
| 100 | 18.733 | 18.73 |
| 150 | 18.731 | ~18.73 (reported minimum) |
| 300 | 19.365 | 19.37 |

Grid-wide best validation MSE = 17.24 at `learning_rate=0.05, max_depth=3,
n_trees=300`.

### `scripts/generate_exercise_07_notebook.py`

- Added `EXPLORER_CACHE_PATH` and `_explorer_cache_literal()` (same
  embedding pattern as the existing `_feature_list_literal()`): reads the
  committed cache JSON and renders it as a plain Python dict literal with
  `(learning_rate, depth)` tuple keys.
- The setup cell (`wp46-000-setup`, collapsed, hidden) now also embeds
  `_EXPLORER_CACHE = {...}` as plain data, right after the feature list —
  no model fit happens there.
- Activity 2's cell (`wp46-407-explorer-widget`) no longer fits any model:
  the 18-iteration `GradientBoostingRegressor(...).fit(...)` /
  `staged_predict` loop is gone, replaced by `_explorer_cache =
  _EXPLORER_CACHE`. The dropdowns, slider, and `_explorer_render` plotting
  function (two-panel figure: training/validation MSE vs. tree count on a
  log x-axis, left; validation-MSE heatmap across learning rate x tree
  count, right; same metrics line) are byte-for-byte unchanged — same
  plots, same controls, same default values (`learning_rate=0.1, depth=2,
  n_trees=100`).
- Activity 2's intro markdown (`wp46-406-activity2-intro`) replaced with
  the requested concise wording, plus a sentence clarifying the curves
  reflect the notebook's *original* split:

  > These results were calculated ahead of time from the fitting and
  > validation sets so the activity opens quickly. The locked test set was
  > not used. Changing a control displays saved results rather than
  > training a new model.
  >
  > These curves and the heatmap reflect this notebook's **original**
  > fitting and validation split from Section 1. If you changed that split
  > above, what you see here still reflects the original split, not your
  > edited one.

- Module docstring gained a paragraph documenting the cache's verified
  numbers (the cross-check above), alongside the existing Section 3-7
  documentation.
- Regenerated (`--write`, never hand-edited) into
  `book/lite/files/exercise_07.ipynb`, `book/lite/files/exercise_07_portable.ipynb`,
  `book/downloads/chapter_07/exercise_07_portable.ipynb`, and
  `scripts/reference_notebooks/exercise_07_reference.ipynb`. The cache is
  embedded identically in all four — the lite notebook, its portable copy,
  and a bare downloaded `.ipynb` all carry the data with **no repository
  file dependency at notebook-run time**, confirmed by inspecting each
  generated file directly. File sizes grew from ~64.3KB to ~70.7KB (lite/
  portable) — the committed cache stays small (9.6KB raw JSON).
  `book/chapters/chapter_07/exercise_07.ipynb` (the published transition
  page, a 2-cell stub pointing at the JupyterLite notebook) is untouched —
  it never carried this cell's code. No change to Exercises 1-6, 8-12, or
  any shared/platform file.

### Tests

- `tests/test_exercise_07_lite_notebook.py`: updated the one assertion tied
  to the old intro wording (`"never part of this activity"` ->
  `"The locked test set was not used"`), and added two new tests: the
  Activity 2 cell contains `_EXPLORER_CACHE` and neither `.fit(` nor
  `GradientBoostingRegressor(` (so it structurally cannot train a model),
  and the intro markdown mentions the original split. **39/39 passed**
  (was 37; +2 new).
- New `tests/test_exercise_07_explorer_cache.py` (13 tests): re-validates
  the committed cache (`validate()` passes, locked-test exclusion, grid
  completeness, monotone training MSE, no non-finite values), cross-checks
  cohort/split sizes (n_fit=564, n_val=189, 360 features) and the
  `learning_rate=0.1, max_depth=2` row against Section 4's audited sweep
  numbers (within 0.1 MSE), confirms the grids match
  `generate_exercise_07_notebook`'s own declared constants, and confirms
  the notebook generator's embedded literal actually matches this exact
  committed cache (so the two files cannot drift silently). **13/13
  passed.**
- `tests/test_exercise_07_reference_execution.py` (real-kernel execution
  of the completed reference notebook): **18/18 passed, `Ran 18 tests in
  762.958s — OK`**. Confirms Activity 2 still prints
  `learning rate = 0.1   depth = 2   trees = 100   training MSE = 5.4
  validation MSE = 18.7` — byte-for-byte the same values the old live-fit
  cell produced — and every other section (including the sweep, the
  12-candidate CV pipeline, and the three-model comparison) is unaffected.
- `tests/test_exercise_07_transition_page.py`: **8/8 passed**, unaffected
  (the stub page was never touched).
- `scripts/generate_exercise_07_notebook.py --check` and
  `scripts/generate_exercise_07_explorer_cache.py --check`: **both OK**.
- Not run here (left to the required release gate): the full project-wide
  Python suite and the full combined-book Playwright suite across all
  exercises.

## Timings measured in a real local JupyterLite build

Built locally (`jupyter-book build book` + `jupyter lite build --config
book/lite/jupyter_lite_config.json --lite-dir book/lite --output-dir
book/_build/html/lite`), served via `interactive/e2e-book/serve-book.mjs`,
measured with Playwright driving real headless Chromium against
`/lite/notebooks/index.html?path=exercise_07.ipynb` (wall-clock `Date.now()`
around a `Shift+Enter` + `waitForKernelIdle`, JupyterLab's own
`.jp-Notebook-ExecutionIndicator[data-status]` semantic kernel-status
attribute — not a fixed wait):

| Cell | Before (live fit) | After (precomputed cache) |
| --- | --- | --- |
| Setup cell (collapsed, first) | — (unchanged by this WP) | **12.6s** (dominated by `micropip.install(["ipywidgets"])`; parsing the embedded feature list + cache literal is negligible) |
| Activity 2 cell, run standalone right after setup | *cannot run standalone* — depends on Section 1's `X_fit`/`X_val`/imports | **43ms** |
| Activity 2 cell, after Section 1 has run | **172,084ms (~2m52s)** — 18 `GradientBoostingRegressor` fits via `staged_predict`, in-browser Pyodide/WASM | 43ms (same measurement; no longer depends on Section 1 at all) |

The "before" number was measured by temporarily swapping the previous
commit's `exercise_07.ipynb` into the local JupyterLite build output,
running setup -> Section 1's data-load cell -> Activity 2 (since the old
cell required `X_fit`/`X_val` from Section 1), then restoring the build
output to match the committed source exactly (confirmed via `diff`) before
any further testing. A genuine, measured before/after, not an estimate.

The new cell's independence from Section 1 is itself a verified structural
improvement: Activity 2 now needs only the setup cell
(`widgets`/`np`/`plt`/`display`/`_EXPLORER_CACHE`), not Section 1's data
load or scikit-learn imports — confirmed by running it standalone and by
the new `test_exercise_07_lite_notebook.py` assertions.

## Plots and controls verified unchanged

Local Playwright run against the rebuilt site,
`interactive/e2e-book/exercise-07-lite.spec.ts --workers=1` (matches CI's
serialized setting): **7/7 passed in 19.8 minutes** (the slow
teacher-completed-path test: 17.0m, a real 12-candidate x 5-fold
`GridSearchCV` inside Pyodide WASM, unrelated to this change but exercised
as part of the same file). Explicitly includes "the Explore the Boosting
Parameters widget changes its metrics line when depth changes" (39.0s) —
same two dropdowns + slider, same default
`learning rate = 0.1   depth = 2   trees = 100` metrics line, same
depth-change-updates-the-line behavior — and "no error cells anywhere on
an untouched Run All Cells" (36.7s), proving the new setup-cell embedding
introduces no execution error anywhere in the notebook.

## CI-caught fix: an internal script-path leak into the portable notebook

The first push (commit `58a84f2`) selected the **full gate** (`classify`:
the new `scripts/generate_exercise_07_explorer_cache.py` and
`tests/test_exercise_07_explorer_cache.py` don't match any of
`classify_release_change.py`'s per-exercise path patterns, so its generic
`^scripts/`/`^tests/` shared-script/shared-test rules correctly forced the
broader gate -- expected and left as-is, not worked around, per this WP's
instruction not to re-run broad suites locally and instead let CI's own
required gate run). CI's full project-wide suite (run
[`44370812687`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/44370812687),
1442 tests) caught a real defect this WP's own local focused-test scope
had not covered: `tests/test_wp35_content_audit.py`'s
`test_no_author_facing_phrases_in_portable_notebooks` failed --
`SCRIPT_PATH_RE` (`\bscripts/[\w.]+\.py\b`) matched the literal string
`scripts/generate_exercise_07_explorer_cache.py` inside two of my own new
code comments (the setup cell and the Activity 2 cell), which is exactly
the "internal script/report reference" category that audit exists to keep
out of anything a student can read. `build-and-deploy` failed at "Unit-test
the Python scripts (offline, full gate)" after 22m55s, before ever reaching
the build/deploy steps -- nothing was published.

Fix (commit `e0ad24e`): reworded both comments to describe the
precomputation ("precomputed offline... the locked test set was never
read") without naming the script file -- no behavior change, regenerated
into all four notebook copies. Re-verified locally: `test_wp35_content_audit`
(7/7), plus `test_exercise_07_lite_notebook` (39/39),
`test_exercise_07_explorer_cache` (13/13), `test_exercise_07_transition_page`
(8/8), and both generators' `--check`, all green. Confirmed (by direct
Python scan of the regenerated `.ipynb` JSON) that no cell anywhere
mentions a `scripts/*.py` path or a `wp\d{2}` reference. Did not re-run the
full 1442-test project-wide suite locally for this follow-up fix, per the
same "let CI run its required gate" instruction -- the second push's own
CI run is the gate that actually re-verifies it.

## Push, deploy, and live verification

- Commits pushed to `main`: `58a84f2` (the WP65 change itself), then
  `e0ad24e` (the CI-caught content-audit fix above).
- GitHub Actions deploy workflow run
  [`44377438444`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/44377438444),
  triggered by `e0ad24e`: `classify` selected the **full gate** (for the
  reason above); `build-and-deploy` **succeeded in 1h32m53s** -- every
  step green, including "Unit-test the Python scripts (full gate)", "Build
  Jupyter Book", "Fail on notebook execution errors", "Build JupyterLite
  (Exercises 1-9)", "End-to-end test the combined book + JupyterLite build
  (full gate)" (the project's own Playwright book suite, including
  `exercise-07-lite.spec.ts`'s "Explore the Boosting Parameters widget
  changes its metrics line when depth changes" test), and "Publish
  website". Monitored to completion via `gh run watch --exit-status`
  (run detached so it survived two unrelated session restarts).
- Deployed `gh-pages` commit: `5abcbb1730a857fae74846f5aee9b3ed60037945`
  (`deploy: e0ad24e11dd7936159bef794bbcf5cb801f9066c`), confirmed via
  `git fetch origin gh-pages && git log origin/gh-pages -1` -- matches the
  pushed commit exactly.
- Fetched the live notebook directly
  (`https://yoavmp.github.io/ml-neuro-tutorials/lite/files/exercise_07.ipynb`)
  and diffed it byte-for-byte against the locally committed
  `book/lite/files/exercise_07.ipynb`: **identical**. Confirmed in the
  fetched JSON: `_EXPLORER_CACHE = {` present in the setup cell; no
  `generate_exercise_07_explorer_cache.py` mention anywhere; the Activity 2
  cell contains neither `GradientBoostingRegressor(` nor `.fit(`; the intro
  cell carries the exact new wording ("These results were calculated ahead
  of time...", "The locked test set was not used...", and the
  original-split clarification).
- Live browser verification (headless Chromium via `playwright-core`,
  driven from the terminal against the live URL
  `https://yoavmp.github.io/ml-neuro-tutorials/lite/notebooks/index.html?path=exercise_07.ipynb`):
  console log showed every Pyodide package loading cleanly (numpy, pandas,
  matplotlib, then "Loading/Loaded joblib, scikit-learn, scipy,
  threadpoolctl"), "Run All Cells" completed with the kernel reaching
  `idle` and **zero** `.jp-mod-error` cells; a screenshot taken immediately
  after confirms the notebook ran cleanly through to its last cell (17
  executed cells, ending at Section 8's checked question) with the
  "Unsaved changes (stored only in this browser)" banner -- normal
  JupyterLite behavior, not an error. Scrolled to the "Explore the Boosting
  Parameters" widget and confirmed the exact expected metrics line is
  rendered live: `learning rate = 0.1   depth = 2   trees = 100
  training MSE = 5.4   validation MSE = 18.7` -- byte-for-byte the same
  values the pre-change live-fit cell always produced, now served from the
  precomputed cache. This is corroborated by (not a substitute for) the
  deploy run's own green "End-to-end test the combined book + JupyterLite
  build" step, which ran this exact scenario (`exercise-07-lite.spec.ts`'s
  "widget changes its metrics line when depth changes" test) against this
  exact built artifact before it was published, and by this WP's own local
  7/7 pass of the identical spec before the first push.

## Summary of timings

| Measurement | Value |
| --- | --- |
| Setup cell (collapsed, first; includes `micropip.install(["ipywidgets"])`) | 12.6s |
| Activity 2 cell, before (live fit, 18 `GradientBoostingRegressor` fits via `staged_predict`) | ~172.1s |
| Activity 2 cell, after (precomputed cache; controls + plots only) | ~43ms |
| Speedup | ~4,000x |
| CI deploy run (full gate, after the content-audit fix) | 1h32m53s |

Deployed SHA: `e0ad24e11dd7936159bef794bbcf5cb801f9066c` (gh-pages:
`5abcbb1730a857fae74846f5aee9b3ed60037945`).
