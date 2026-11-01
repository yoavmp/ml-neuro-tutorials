# WP61 report: Exercise 11's active notebook on embeddings and RSA (local only)

## Success or failure -- read this first

**Success, local-only, as scoped.** Exercise 11 ("Embeddings and
Representational Similarity Analysis") is built as a real, active
JupyterLite-native notebook on real Haxby et al. (2001) fMRI data, with a
reproducible offline extraction script, 42 offline structural/reference-
execution tests (all green), a passing 4-test Playwright suite against the
actual combined local build (untouched-template, 390px, reset, and
teacher-completed paths), and two real bugs found and fixed by that
browser testing, not just by inspection. Exercise 11 is **not** merged,
pushed, deployed, or wired into the live release gate -- it stays
`migrationState: "legacy"` in `book/config/exercise_manifest.json`, and its
book page stays the placeholder stub, exactly as scoped.

**One deviation from the WP spec**, found mid-implementation and corrected
rather than worked around: `book/downloads/chapter_11/exercise_11_portable.ipynb`
is **not** produced this WP (see "Deviations" below) -- an existing guard
test (`tests/test_placeholder_exercises.py`) explicitly forbids a portable
download file at that exact path while Exercise 11's book page is still
the placeholder stub, and this WP respects that boundary rather than
silently breaking it.

Real Colab verification was **not performed** -- unverified, as required
to state explicitly, not assumed.

## Branch and SHAs

- Branch: `feature/wp61-embeddings-and-rsa`, off `main` at `c056b01`.
- Checkpoint: `f07c3a3` ("checkpoint: before WP61"), tag `wp61-start`.
- Implementation: `d6fd7af` ("WP61: build Exercise 11 active notebook on
  representational similarity analysis (local only)").
- This report + exact changelog: committed separately after this file.

## Gate A: the prepared Haxby RSA export

### Source and method

- Dataset: Haxby et al. (2001), subject 2 -- `nilearn.datasets.fetch_haxby`'s
  own documented default subject (`subjects=(2,)`), not switched to search
  for a stronger-looking result.
- Source: `http://data.pymvpa.org/datasets/haxby2001/subj2-2010.01.14.tar.gz`,
  fetched via `nilearn.datasets.fetch_haxby(subjects=[2], fetch_stimuli=False)`.
  Raw archive size: 291,168,628 bytes (~278 MiB, i.e. the ~300 MB the task
  described) -- confirmed from the download's own byte-count log, never
  committed to the repository.
- License: `nilearn`'s own dataset description lists this dataset's
  license as "unknown" -- no explicit grant from the original distributor.
  Documented honestly in the derived file's own manifest (below) rather
  than invented; the course export carries the same open-reuse-with-
  citation basis the source data itself carries, citing Haxby et al.
  (2001), *Science* 293(5539):2425-2430.
- Mask: `mask4_vt.nii.gz` (`nilearn`'s `mask_vt` attribute) -- the broad
  ventral-temporal mask, 464 voxels. Deliberately **not**
  `mask8_face_vt.nii.gz`/`mask8_house_vt.nii.gz`/`mask8b_*` (the
  category-selective masks), which would make the face/house comparison
  in Section 5 circular.
- Method (`scripts/export_haxby_rsa_data.py`): per run, z-score every
  retained voxel's time series (mean 0, sd 1, using only that run's own
  TRs); find contiguous same-label spans in `labels.txt` (its own `chunks`
  column gives run boundaries); for every non-"rest" span, drop its first
  2 TRs (hemodynamic-onset allowance -- the BOLD response lags stimulus
  onset by several seconds) and average the remaining TRs' z-scored
  values into that run/category's pattern.
- **Observed, not assumed:** every one of subject 2's 8 category blocks,
  in every one of 12 runs, was exactly **9 TRs** long (`blockLenObserved:
  [9]` in the manifest) -- matching Haxby et al. (2001)'s own documented
  24 s block length at this dataset's TR (`trSeconds: 2.5`). 2 TRs were
  dropped from every single block (`trsDroppedObserved: [2]`), leaving 7
  retained TRs per block, comfortably above the 3-TR minimum the script
  enforces. **No exclusions were necessary**: every retained run contained
  exactly one contiguous block per category, and both the odd-run subset
  (runs 1,3,5,7,9,11) and the even-run subset (0,2,4,6,8,10) independently
  cover all 8 categories (`oddEvenCheck.eachSubsetCoversAllCategories: true`).
- Scope: these are **category-level, run-level averaged patterns**. The
  original picture-by-picture presentation order and any response to an
  individual image are not recoverable from this export, and the
  notebook says so explicitly (Section 1).

### The derived export

- `book/lite/files/data/haxby_rsa_patterns.csv` -- **881,847 bytes** (~861
  KiB), 96 rows (12 runs x 8 categories), 466 columns (`run`, `category`,
  464 `voxel_####` columns). sha256
  `371e5b44e416b090cf487d89103b7f8f69444fc9f9385112aa61a7035ebb1f95`.
- `book/lite/files/data/haxby_rsa_patterns.manifest.json` -- citation,
  source URL, license statement, mask used (and why not the alternatives),
  every extraction choice above, observed block lengths/TR drops,
  exclusions (none), the odd/even coverage check, and the derived file's
  own checksum/dimensions. `scripts/export_haxby_rsa_data.py --check`
  re-validates all of this offline, with no network access; `--refresh`
  is the maintainer-only network mode that rebuilds it.
- Neither `nilearn` nor `nibabel` is added to `requirements-lite.txt` or
  `book/lite/overrides.json` -- both are maintainer-only, newly added to
  the root `requirements.txt` (never imported by any student-facing cell;
  confirmed by `tests/test_exercise_11_lite_notebook.py::test_no_raw_fmri_download_in_student_notebook`).

## What this WP built

`scripts/generate_exercise_11_notebook.py` (the same generator-authored,
hidden-setup-cell, `show_question()`/`Blank` architecture as Exercises
1-9/12) produces:

- `book/lite/files/exercise_11.ipynb` -- the JupyterLite template (42 cells).
- `book/lite/files/exercise_11_portable.ipynb` -- the same build, a
  portable/Colab-ready copy served alongside the template.
- `scripts/reference_notebooks/exercise_11_reference.ipynb` -- the
  teacher-filled copy (every `Blank` renders its complete solution),
  never published, used only by the offline reference-execution test.

### Content outline

1. **Load the response patterns.** Loads the prepared CSV (same-origin
   first, a public-repo fallback URL second, matching the established
   `load_abide_age_brain_table()` pattern), explains the `run`/`category`/
   `voxel_####` dimensions, and shows a given heatmap of all 8 categories'
   patterns from one run.
2. **Build the neural RDM** *(student blank)*. Students fill
   `neural_rdm[i, j] = 1 - corr(...)` for every category pair; a given
   check cell verifies shape, order (implicit, by construction),
   symmetry, finite entries, and a ~0 diagonal, with a fallback heatmap.
3. **2-D MDS embedding** *(given)*. `sklearn.manifold.MDS`, labeled
   points, explicit text that axes are arbitrary and the embedding only
   approximates the RDM's real distances.
4. **Split-half reliability** *(student blank)*. Students build
   `odd_rdm`/`even_rdm` from `ODD_CATEGORY_PATTERNS`/`EVEN_CATEGORY_PATTERNS`
   and `split_half_r` from their upper triangles.
5. **Model comparison.** A fully worked **given** example (face vs. every
   other category); a **student blank** for animate vs. inanimate that
   must exclude `scrambledpix` (with the stated conceptual reason --
   scrambled images have no animacy) before any score is inspected.
6. **Interpretation and limits.** States the real numbers (below), and
   explicitly explains why no naive p-value is reported (the upper-
   triangle pairs are not independent observations).

Two native `ipywidgets`/Matplotlib activities, matching Exercises 9/12's
"native widget" architecture (no iframe, no separate TS/Vite build):

- **(A) Distance-metric explorer** (Section 6): both the correlation- and
  Euclidean-distance RDM + MDS embedding are precomputed once, up front;
  the dropdown only switches which precomputed pair is redrawn.
- **(B) Category-grouping explorer** (Section 5): a `SelectMultiple` over
  the 7 non-scrambled categories builds a live hypothesis RDM and its
  descriptive correlation with the real neural RDM, explicitly labeled
  "exploration, not an independent test" once, near the activity.

Six checked questions (`show_question()`, hidden key, fixed-but-per-
question shuffle seed), covering exactly the required topics: what a
row/voxel is, what an RDM cell means, why condition order must match,
what a 2-D MDS embedding distorts, why split-half reliability is checked,
and (a multi-select) what a face-hypothesis match does and does not
establish. Three real coding blanks (RDM construction, split-half
RDMs + correlation, the animacy hypothesis RDM + correlation), each with
directional hints and an explicitly-labeled "example shape only" comment
-- never a working solution, commented or otherwise.

## Real, measured results (not adjusted after the fact)

Computed directly from `book/lite/files/data/haxby_rsa_patterns.csv`
(verification script run before writing a single generator line) and
reproduced exactly by both the offline reference-execution test and the
live-browser teacher-completed-path Playwright test:

- **Neural RDM** (correlation distance, 8 categories, patterns averaged
  across all 12 runs): distances range from **0.426** (bottle-shoe, most
  similar) to **1.124** (cat-scrambledpix, least similar); diagonal
  exactly 0, matrix exactly symmetric (both guaranteed by construction).
- **Split-half reliability** (odd-run RDM vs. even-run RDM, Pearson
  correlation of their matching upper triangles): **r = 0.485** -- a
  real, moderate, far-from-perfect value, reported as measured.
- **Face-vs-other-categories model match**: **r = 0.247** -- weak-
  positive, the weaker of the two hypotheses here; reported honestly
  rather than omitted or re-derived.
- **Animate-vs-inanimate model match** (scrambled excluded, 7x7 sub-RDM):
  **r = 0.446** -- moderate, the stronger hypothesis in this data,
  consistent with face/cat (the two animate categories) having one of the
  lowest pairwise distances (0.440) in the whole RDM.

No subject switching, no post-hoc method change, and no selective
reporting was used to produce these numbers -- they are what the
documented extraction method actually yields for subject 2.

## Verification

### Offline/structural (62 tests total, well under 10s)

```
.venv/bin/python scripts/generate_exercise_11_notebook.py --check   # OK
.venv/bin/python scripts/export_haxby_rsa_data.py --check           # OK, rows=96 runs=12 categories=8 voxel_cols=464
.venv/bin/python -m unittest discover -s tests -p 'test_exercise_11_*.py'      # 42 tests, OK (~4-6s)
.venv/bin/python -m unittest discover -s tests -p 'test_export_haxby_rsa_data.py'  # 10 tests, OK (~0.1s)
.venv/bin/python -m unittest tests.test_placeholder_exercises               # 6 tests, OK
.venv/bin/python -m unittest tests.test_exercise_manifest                   # 10 tests, OK (confirms untouched)
```

`test_exercise_11_reference_execution.py` executes the teacher-filled
reference notebook (ast-compile-and-exec per cell, in one shared
namespace, cwd set to `book/lite/files/` to match JupyterLite's real cwd
convention -- never `nbclient`, for the same `ipywidgets.Output()`-as-
context-manager reason WP41-WP51 documented) and asserts, among other
things, zero errors and every headline number above within a tight
(`delta=0.01`) tolerance of the direct verification.

Exercises 1-10/12's own suites were **not** run -- nothing shared was
touched (confirmed: every changed/added file this WP is new, except
`requirements.txt`, which only adds two maintainer-only packages never
imported by any student notebook or by the Pyodide/lite build).

### Local build + real browser (Chromium, Playwright)

```
rm -rf book/_build
.venv/bin/jupyter-book build book                                      # ~5.2s
.venv/bin/jupyter lite build --config book/lite/jupyter_lite_config.json \
  --lite-dir book/lite --output-dir book/_build/html/lite               # ~6.0s
```
Both succeeded; `exercise_11.ipynb`/`exercise_11_portable.ipynb` and the
Haxby CSV/manifest were copied into the Lite build automatically
(`build:contents:copy:exercise_11.ipynb`, `...:data/haxby_rsa_patterns.csv`
in the build log) -- **no `book/_toc.yml`, `book/_config.yml`, or
manifest change was needed** to make Exercise 11 reachable at its own
JupyterLite route; those files stay fully untouched, confirmed by `git
status` showing only the twelve files this WP actually added/changed.

`interactive/e2e-book/exercise-11-lite.spec.ts` (new, modeled on
`exercise-09-lite.spec.ts`), run via
`npx playwright test --config playwright.book.config.ts exercise-11-lite`
against the local build above, navigating directly to
`/lite/notebooks/index.html?path=exercise_11.ipynb` (no manifest-driven
launch button exists yet, by design): **4/4 passing** on the final run:

1. **Untouched template, Run All Cells**: zero `.jp-mod-error` cells, data
   loads (464-voxel message visible), every blank's check cell shows "Not
   complete yet", both native widgets render, the given face-hypothesis
   example gracefully defers (see "bugs found" below).
2. **390px viewport**: no horizontal page overflow; every widget control
   label (both activities) stays unclipped.
3. **Reset from course template** restores the template; **Back to course
   contents** returns to `contents.html`.
4. **Teacher-completed path** (the real test of correctness): fills all
   three blanks with real working solutions typed live into the browser,
   re-runs every dependent cell (MDS, the given face example, both
   widgets), confirms every check cell reaches "Looks good" with the
   **exact** documented numbers (`split_half_r = 0.485`,
   `animacy_match_r = 0.446 over 7 categories`, `face_match_r = 0.247`),
   operates both widgets live (grouping selection change, distance-metric
   toggle, each confirmed by a new rendered image), answers every one of
   the six checked questions correctly by **option text** (never
   position, since every question's displayed order is shuffled), answers
   one single-choice and one multi-choice question deliberately wrong and
   confirms correct "Not quite"/partial feedback with no leaked answer
   key, and downloads the completed notebook, confirming it contains the
   real solution code and not the `YOUR CODE HERE` placeholder.

### Two real bugs found by this browser testing (not by inspection)

1. **False-positive "Looks good" on an untouched blank.** The neural-RDM
   starter cell pre-initializes `neural_rdm = np.zeros((n, n))` (so the
   student can fill individual cells in a loop); the first Playwright run
   showed the check cell reporting "Looks good... distance range: 0.000
   to 0.000" on the completely untouched template, because an all-zero
   matrix trivially passes the shape/symmetry/zero-diagonal/finite
   checks. **Fixed**: the check cell's guard now also requires
   `not np.allclose(neural_rdm, 0.0)`, so an untouched blank correctly
   reports "Not complete yet."
2. **Given example silently computing `nan` instead of deferring
   gracefully.** The fix above exposed that Section 5's given
   face-hypothesis example depends on `neural_rdm` but had no guard at
   all -- on the untouched template it printed `face_match_r = nan`
   instead of a helpful message, the only cell in the notebook that
   didn't degrade gracefully. **Fixed**: wrapped in the same
   `"neural_rdm" in globals() and not np.allclose(neural_rdm, 0.0)` guard
   every other dependent cell already uses; confirmed via Playwright that
   it now shows "Not complete yet: finish Section 2's neural_rdm task
   first." on the untouched template and recovers the exact documented
   `face_match_r = 0.247` once re-run after the blank is filled.

A third, lower-stakes issue -- the 390px test's `scrollToVisibleFine`
helper (copied from `exercise-09-lite.spec.ts`) intermittently failed to
locate the last widget cell because it measured the windowed panel's
`scrollHeight` once, up front, while a late cell's own figure was still
growing that height -- was fixed by re-measuring `scrollHeight` on every
sweep iteration instead. This is a test-harness fix local to this WP's
own spec file, not a notebook bug.

### Private teacher-completed copy

Executed via `test_exercise_11_reference_execution.py` (offline, ast-exec,
zero errors, every headline number matched within tolerance -- see above)
**and** independently via the Playwright teacher-completed-path test,
which retypes the real solutions live in an actual browser kernel. Both
reach the same numbers. **Real Google Colab verification was not
performed in this WP** -- stated here explicitly, not assumed or implied.

### Local preview

```
cd interactive && node e2e-book/serve-book.mjs   # serves book/_build/html on :4174
```
<http://localhost:4174/lite/notebooks/index.html?path=exercise_11.ipynb>
(requires the two build commands above to have been run first; the server
process is not left running after this WP).

## Timing

No command in this WP ran longer than five minutes. For the record:

- Haxby subject-2 download + extraction (`export_haxby_rsa_data.py
  --refresh`, network): 291,168,628 bytes, **~2 minutes** on this
  connection (launched detached per the repo's long-command rule, PID
  recorded, polled via its own log rather than blocking the session).
- `jupyter-book build book`: ~5.2s (final run; ~5.4s on an earlier run).
- `jupyter lite build ...`: ~6.0s (final run; ~6.0s on an earlier run).
- Each full `exercise-11-lite.spec.ts` Playwright run (4 tests): ~1.2-1.3
  minutes total, dominated by the teacher-completed-path test's real
  scikit-learn/MDS fits inside Pyodide's WASM sandbox (four runs total
  across this WP's iterate-fix-rerun cycle, as each real bug above was
  found and fixed).
- All offline Python test suites: each under 10 seconds.

## Deviations from the spec, and why

1. **`book/downloads/chapter_11/exercise_11_portable.ipynb` is NOT
   produced this WP**, though the WP spec and the task's "portable,
   checked data path for a downloaded notebook" language both pointed
   toward it. Found mid-implementation: `tests/test_placeholder_exercises.py
   ::test_no_active_portable_notebook_for_any_placeholder` already asserts
   this exact path does not exist, specifically because Exercise 11 is
   still the one remaining exercise using the guarded `exercise_NN.md`
   placeholder convention (Exercise 10 moved to a differently-named,
   unguarded `placeholder.md` before its own from-scratch rebuild in
   WP58). This guard is clearly intentional -- it is what stops a "coming
   later" page from quietly gaining a real download button -- and this WP
   does not lift it. **What this WP ships instead**: a portable/Colab-
   ready copy at `book/lite/files/exercise_11_portable.ipynb` (checked by
   this WP's own structural tests, reachable from the local JupyterLite
   build's own file listing), satisfying "portable, checked" without
   tripping the guard. A future, explicitly authorized release WP both
   writes the `book/downloads/` copy and removes Exercise 11 from that
   test's `PLACEHOLDER_TITLES`, the same way WP52/WP57R/WP59 did for
   their own exercises.
2. **Spearman/rank correlation was not used for the model-RDM match
   score.** The task's phrasing ("a descriptive correlation score") did
   not mandate a specific correlation type, and no existing notebook in
   this course imports `scipy` directly (confirmed by a repo-wide grep)
   -- Pearson correlation via `np.corrcoef` on the upper-triangle vectors
   was used throughout (split-half, both model comparisons, both native
   activities) for consistency with the rest of the course's
   browser-compatible-stack discipline, and because the methodological
   point (upper-triangle comparison, non-independence caveat) does not
   depend on which correlation coefficient is used.
3. **2 TRs dropped per block (not a different number) for the
   hemodynamic-onset allowance.** Chosen before inspecting any RSA
   result, documented in the extraction script's own docstring and the
   manifest, and verified (not assumed) to leave every block with its
   minimum-retained-TR floor comfortably satisfied (7 of 9 TRs retained
   per block, uniformly, across all 96 run/category combinations).

## Known follow-up (not fixed in this WP, by design)

- Wiring Exercise 11 into `book/config/exercise_manifest.json`,
  `book/_toc.yml`, and a real download/launch button on its book page --
  deliberately deferred to a later release WP, per this WP's own scope
  boundary and the existing placeholder guard test.
- Real Google Colab acceptance of the portable notebook -- unverified,
  as stated above.

## Confirmation

Branch `feature/wp61-embeddings-and-rsa` has a clean working tree at
`d6fd7af` plus this report's own commit. No merge, push, deployment, or
WP62 performed. Stopping for the author's review.
