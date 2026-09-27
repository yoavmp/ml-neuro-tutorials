# WP41 report: JupyterLite course platform and active Exercise 2

## Success or failure

**Success.** Gate A's platform proof and the full Exercise 2 migration are
both complete, tested, and verified against a real browser running the
actual combined `jupyter-book` + `jupyter-lite` build. Nothing was merged,
pushed, or deployed.

## Branches and SHAs

- Starting SHA (local `main`): `24a1bd99e697acb8c0ec8355efb43bc485c6ffd2`
- Archive branch: `archive/pre-wp41-jupyterlite-course-platform` (same SHA)
- Feature branch: `feature/wp41-jupyterlite-course-platform`
- Final feature-branch SHA: see `git log -1` after this report's own commit
  (this report is committed together with the changelog as WP41's closing
  commit, per section 14).

## Exact pins

- `jupyterlite-core==0.8.3`, `jupyterlite-pyodide-kernel==0.8.5`
  (`requirements-lite.txt`). Both are one patch behind the current stable
  release (0.8.4 / 0.8.6); no alpha/rc/dev version was used.
- Browser kernel: Pyodide 314.0.5 (CPython 3.14), loaded from the jsdelivr
  CDN at first kernel start -- not bundled into the repository or the
  build output (`book/lite/overrides.json` only *names* packages; nothing
  Pyodide-related is committed to Git).
- Preloaded packages (no install cell, ever): numpy, pandas, scikit-learn,
  matplotlib -- all have prebuilt Pyodide wheels. `ipywidgets` does not, so
  it is fetched once via `micropip` inside a collapsed setup cell, guarded
  by `sys.platform == "emscripten"` so local Jupyter/Colab (which already
  have it) never see this.

## Hub / template / working-copy / storage / download / portable mapping

- **Hub**: `book/` (Jupyter Book), built to `book/_build/html/`. Unchanged
  except `book/_config.yml` now excludes `book/lite/` from its source scan.
- **JupyterLite app**: built as a separate step, straight into
  `book/_build/html/lite/` (`jupyter lite build --config
  book/lite/jupyter_lite_config.json --lite-dir book/lite --output-dir
  book/_build/html/lite`), after the Jupyter Book build. Verified to
  coexist without overwriting the hub (both trees present simultaneously in
  the same output directory; `chapters/chapter_02/exercise_02.html` and
  `lite/notebooks/index.html` both served correctly side by side).
- **Template**: `book/lite/files/exercise_02.ipynb` (source of truth,
  generated). Its browser-served copy is `<site>/lite/files/exercise_02.ipynb`
  (the untouched static original, used by "Reset").
- **Working copy**: JupyterLite's own contents manager layers browser
  storage (IndexedDB) over the static template automatically -- first open
  seeds from the static file, every save afterward reads/writes IndexedDB.
  No extra code was needed for personal per-browser working copies or
  autosave.
- **Storage boundary**: made explicit to students via the toolbar's save
  status text ("Saved in this browser" / "Unsaved changes (stored only in
  this browser)").
- **Download**: the toolbar's **Download my notebook** button serializes
  the live in-memory document model (not the template) to a `.ipynb` file
  via a Blob + object URL, independent of the browser's own File > Download
  command (which also works, unchanged).
- **Portable/Colab copy**: `book/downloads/chapter_02/exercise_02_portable.ipynb`,
  byte-identical to the JupyterLite template (both generated from the same
  source; no MyST/iframe rewriting is needed because this notebook was
  designed portable-first).
- **Old URL**: `book/chapters/chapter_02/exercise_02.ipynb` is now a
  2-cell transition page linking to both of the above.

## Cold/warm timings and size impact

Measured locally (Gate A proof notebook; Exercise 2's own notebook is
heavier and was not independently re-timed, but uses the identical
platform and package set):

- Book hub alone: 22.1 MB. Combined with JupyterLite: 49.2 MB
  (JupyterLite app + Exercise 2's data/notebook assets: +27.1 MB). Pyodide
  itself is not part of this -- it streams from the CDN on first kernel
  start.
- Cold start (empty cache, first-ever visit): kernel start + package fetch
  + full run, ~89s (Gate A measurement; Exercise 2's Playwright tests each
  budgeted 100s for the same phase and passed comfortably within it).
- Warm reload (browser cache already populated): ~21s for the same
  sequence.
- Exercise 2 notebook download size: ~97 KB unexecuted (student template);
  larger once executed with outputs (matplotlib PNGs).

**Course-author judgment call**: a ~90-second one-time cold start per
student per browser is the main practical cost of this architecture. It is
not disqualifying (comparable to loading a modern in-browser IDE once, and
cached thereafter for that browser), but it is worth telling students to
open the notebook a few minutes before they need to use it the first time.

## How ABIDE data works without Git access

`scripts/export_abide_lite_data.py` computes the exact established
canonical recipe (bundle `all-eligible`, measure `CT`, target `age`; 360
bilateral cortical-thickness predictors) once, offline from the student's
perspective, and commits the result as a plain CSV
(`book/lite/files/data/abide_age_brain.csv`, 1004 participants x 360
predictors + age + group) plus a sidecar manifest recording its SHA-256,
participant count, and predictor count. JupyterLite serves this as an
ordinary same-origin static file; the notebook's own Python `pd.read_csv`
call needs no network access, GitHub token, or repository visibility.
`--check` (offline) validates the committed file against its own manifest
and the live `book/config/abide_modeling.json` recipe;
`tests/test_export_abide_lite_data.py` covers this in CI.

The downloaded/Colab copy does *not* receive this sibling file (the
download contract only covers the `.ipynb` itself), so it falls back to
the same pinned, checksummed public URL the course already used elsewhere.
Both paths are unified behind one small helper,
`load_abide_age_brain_table()`, in the notebook's own collapsed setup cell
-- verified to produce bit-for-bit identical modelling results either way
(see Numerical integrity below).

## Proof download contains student edits

Both Gate A's proof notebook and Exercise 2 itself were verified end to end
in a real headless Chromium browser against the actual combined build:
edit a cell, save, reload, confirm the edit persisted; download the
notebook and parse the downloaded JSON to confirm the edited text is
present (`interactive/e2e-book/exercise-02-lite.spec.ts`, "an edit persists
across reload and downloads with the edit present" -- passing).

## Active-learning tasks added (Exercise 2)

- 5 student-written code tasks (Activities 2A, 2B, 3A, 3B; Section 5's KNN
  build). Spec target was 4-6.
- 5 editable written-answer cells (2A, 2B's prediction, 3A, 3B, Section 5).
  Spec target was "approximately 3-4"; this notebook has 5, one more than
  the guideline, because each answer sits at a genuinely distinct
  decision point (see "Deviations" below).
- 5 checked questions (2A's allowed-test-uses multi-select, 3A's
  correlation-vs-coefficient multi-select, Section 4's which-evaluation
  single-choice, Section 6's complexity-direction single-choice, Section
  8's large-k-behaviour single-choice). Spec target was 4-6.
- A graceful dependency check after Section 5 (verifies `knn_pred`/`knn_r2`/
  `knn_mse` exist and are finite without breaking Section 6-8 if left
  incomplete).

## Interactives migrated and their implementation

- **Section 8 "Explore model complexity"** (replaces the old React/Plotly
  knn-explore widget for Exercise 2 specifically -- the old widget code
  itself is untouched and still used by no other active exercise, per
  scope): an `ipywidgets.IntSlider` + `BoundedIntText` pair (two-way
  synced) drives a live-refit two-panel Matplotlib figure -- an
  observed-vs-predicted scatter overlaying three deterministic bootstrap
  training-sample resamples, and the Section 7 error curve with a moving
  marker at the current k. Preserves the old widget's training-sample
  comparison; does not port its calibration plot or bias/variance-proxy
  numerics (see "Deviations").
- All other notebook-native pieces (checked single/multi-choice questions
  with immediate feedback) are built from two small shared helper
  functions (`make_single_choice_question`, `make_multi_choice_question`)
  defined once in the collapsed setup cell and reused five times.

## Exact prose and sections removed

- The curse-of-dimensionality paragraph (Section 6): removed completely,
  per spec.
- Internal numbered comments ("1-2. brain-only", "3. one fixed", "4-7.
  written out", "8. observed vs predicted"): removed; replaced with brief
  student instructions.
- Repeated train/test/R²/MSE definitions, repeated small-k/large-k
  explanations, and author/audit notes: consolidated into single
  statements (Section 6's "small k means... large k means...").
- The three "Think first" + "Check your reasoning" MyST admonition pairs
  from the old notebook: replaced by checked questions or editable answers
  (never both for the same prompt), per the question/activity audit.
- Vague "honest" evaluation language: replaced with "correct
  evaluation"/"held-out test evaluation" throughout.

## Before and after prose word counts

Student-facing markdown prose (approximate, code/tables/output excluded):
**2847 words -> 1034 words (-64%)**, while adding the 5+5+5 active-learning
elements listed above. Measured by stripping MyST directive fences/options
and inline code spans from every markdown cell and counting the remainder
(old notebook read from `archive/pre-wp41-jupyterlite-course-platform`; new
notebook is `book/lite/files/exercise_02.ipynb`).

## Before and after metrics

All values below are bit-for-bit reproduced by the new same-origin data
export and its established split (verified in
`tests/test_exercise_02_reference_execution.py`, which executes the
completed reference notebook's actual cell sources -- not hand-copied
numbers):

| Metric | Before | After |
|---|---|---|
| Eligible participants | 1004 | 1004 |
| Predictor count | 360 | 360 |
| Train / test rows | 753 / 251 | 753 / 251 |
| Linear regression held-out R² / MSE | 0.469 / 49.55 | 0.469 / 49.55 |
| Training-score R² / MSE (Section 4 panel B) | 0.845 / 13.53 | 0.845 / 13.53 |
| Invalid fit-on-test R² / MSE (Section 4 panel C) | 1.000 / 0.000 | 1.000 / 0.000 |
| KNN (k=20) held-out R² / MSE | 0.664 / 31.4 | 0.664 / 31.4 |
| K-sweep N_fit / N_val / best k | 564 / 189 / 17 | 564 / 189 / 17 |
| Bonus sample-size feature count | 10 (sensorimotor bundle) | 10 (same bundle) |

No result changed. Migration and the 1/k axis transformation are purely
presentational/architectural.

## Changed files

See `WPs/reports/WP41_EXACT_CHANGELOG.md` for the complete, exact list
(42 files changed, 15336 insertions(+), 3027 deletions(-) across the whole
branch).

## Every test, build, and manual result

**Python (offline, no network)**: `python -m unittest discover -s tests` --
1079 tests, all green, 11 skipped (network-only tests, expected offline).
Includes the new Exercise 2 test files and the five updated
cross-notebook tests.

**Generators**: `scripts/generate_exercise_02_notebook.py --check
--student --reference`, `scripts/generate_exercise_02_transition_page.py
--check`, `scripts/export_abide_lite_data.py --check` -- all report up to
date / OK.

**Frontend**: `npm run typecheck` in `interactive/` -- clean (the
course-toolbar extension lives outside `interactive/`'s TypeScript project
and was typechecked separately via its own `tsc`; both clean).

**Jupyter Book build**: `jupyter-book build book` -- succeeds, 0 errors,
2 pre-existing warnings unrelated to this WP. (Required fixing a real
Sphinx source-scan collision: `book/lite/`'s own labextension
`node_modules`/build tree was being scanned as book content until
`book/_config.yml` excluded `lite/*`/`lite/**`.)

**JupyterLite build**: `jupyter lite build --config
book/lite/jupyter_lite_config.json --lite-dir book/lite --output-dir
book/_build/html/lite` -- succeeds; coexists with the book hub in the same
output tree.

**Playwright, built book** (`playwright.book.config.ts`, real headless
Chromium against the actual combined build):
- `exercise-02-lite.spec.ts`: 6/6 passing (opens+runs+reproduces R²=0.469;
  Section 8 slider operable; a checked question grades correctly; edit
  persists across reload and downloads with the edit present; reset
  restores the template and Back returns to Contents; usable at 390px).
- `chapter02.spec.ts` (rewritten for the transition page): 2/2 passing.
- `chapter01.spec.ts` (untouched legacy exercise, regression check): 12/12
  passing -- confirms the unmigrated exercises are unaffected.

**Manual verification**: performed directly (not just via the automated
Playwright specs above) during development -- clean browser profile, cold
and warm JupyterLite start, opened/edited/ran/saved/reloaded, operated
every Exercise 2 interactive (Section 8 slider, all 5 checked questions),
downloaded and inspected an edited `.ipynb`, reset after the warning
dialog, returned to Contents. Not separately re-verified: 390px + light/dark
combined (the 390px check ran in default/light theme only; dark-mode
JupyterLite rendering was not manually inspected -- see Deviations).

## Deviations and decisions

1. **`jupyter execute`/nbclient hangs on this notebook's Section 8 cell.**
   A real Jupyter kernel with no frontend attached appears to deadlock on
   an `ipywidgets.Output()` used as a context manager (no comm-handshake
   acknowledgment ever arrives). Root-caused via a from-scratch
   synchronous-exec harness that runs each cell's source directly (with
   `ast.PyCF_ALLOW_TOP_LEVEL_AWAIT` + `asyncio` for the one guarded
   top-level `await`), which reproduces identical results in ~5 seconds
   with no such issue. That harness is what
   `tests/test_exercise_02_reference_execution.py` uses instead of
   `jupyter execute`. Documented in the maintainer guide as a real,
   load-bearing gotcha for anyone adding the next migrated exercise's
   numeric-integrity test.
2. **Editable answer cells: 5, not the guideline's "approximately 3-4."**
   Each of the 5 (2A, 2B's prediction, 3A, 3B, Section 5's comparison)
   sits at a genuinely distinct decision point the audit in section 7
   requires be assessed somewhere; cutting one felt like removing real
   content to hit a number rather than a concision improvement. Flagging
   for course-author review rather than silently deciding it is fine.
3. **Section 8's widget scope narrowed from the old React activity.** The
   old knn-explore widget also had a binned calibration plot and
   bias/variance-proxy numeric readouts (slope-based proxies). The new
   notebook-native version ports the k-driven refit, the observed-vs-
   predicted scatter, the training-sample-resample overlay, and the error-
   curve marker, but not the calibration plot or the proxy numerics --
   judged as advanced/auxiliary content beyond what "port its current
   useful interactives" strictly requires, and cutting them kept Section 8
   from becoming a second, larger lecture. If the course author wants them
   back, they are straightforward to add to the same widget cell in
   `scripts/generate_exercise_02_notebook.py`.
4. **CI does not yet build JupyterLite automatically.** Wiring a
   `jupyter lite build` step (and a corresponding Playwright job) into
   `.github/workflows/deploy.yml` was judged to be deployment-pipeline
   work outside this WP's explicit scope (WP41 forbids merging, pushing,
   deploying, and starting WP42). All verification above was performed
   against a local combined build. The maintainer guide documents the
   exact commands a future deployment WP needs.
5. **Durable-test coverage is broad but not exhaustive against section
   12's full enumerated list.** Every item was considered; most are
   covered by an automated test (offline structural, offline executed, or
   browser). A few (light/dark combined at 390px specifically; a fully
   generic per-exercise manifest-driven Playwright harness rather than one
   file hand-written for Exercise 2) were judged lower-value for a
   single-exercise migration and are left as explicit follow-up in the
   maintainer guide rather than claimed as done.
6. **`ignore_sys_prefix` was not used to trim the JupyterLite build.**
   The build auto-discovers every labextension installed in the shared
   venv (including `jupyterlab-plotly` and a Voila preview extension that
   Exercise 2 does not use), adding a few MB. Left as-is: the size impact
   is minor relative to the whole app, and trimming risks accidentally
   excluding something a future migrated exercise needs (e.g. Plotly).

## Anything requiring course-author attention

- The ~90-second cold-start cost (see Timings) -- consider mentioning it
  to students before the first live session using this notebook.
- The 5-not-4 editable-answer-cell count (Deviation 2).
- The narrowed Section 8 widget scope (Deviation 3) -- confirm the dropped
  calibration/proxy content isn't something you specifically want kept.
- CI is not yet building or testing JupyterLite automatically (Deviation
  4) -- a future deployment WP needs to add this before Exercise 2 (or any
  further migration) can actually go live on GitHub Pages.
