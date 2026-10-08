# WP51 report: Exercise 9's active notebook on PCR/PLS, SVMs, and kernels (local only)

## Success or failure -- read this first

**Success, local-only, as scoped.** Exercise 9 was rebuilt as a
generator-authored, JupyterLite-native notebook in the style of Exercises
1-8, with a single reproducible ABIDE-II train/validation split, five
required student tasks plus one optional challenge, two native ipywidgets
activities, six checked questions, and a graceful final comparison. Every
number is verified directly, not assumed. 149 offline tests and 3 real
Playwright-browser tests (against the actual combined `jupyter-book` +
`jupyter lite` build) all pass. Exercises 1-8 are untouched; Exercises
10-12 are untouched. `book/_toc.yml`, `book/_config.yml`, `book/config/
exercise_manifest.json`, and `book/_static/launch-buttons.js` are
untouched, so this work is not live, not in the release gate, and not
discoverable from the published site. No merge, push, deployment, or WP52
happened or was attempted.

## Branch and SHAs

- Feature branch: `feature/wp51-active-exercise-09`, branched from local
  `main` at `c5acbe3` (matching `origin/main`).
- `e329501` -- checkpoint commit (the WP spec file only).
- `98b21cc` -- the generator, its four generated outputs, the two
  build-tooling deregistrations, and the three test-file changes.
- This report + changelog are committed together as this WP's closing
  commit -- see `git log -1` on `feature/wp51-active-exercise-09` after
  this commit for the final SHA.

## What this WP built

Replaced the old Exercise 9 (30 cells: heavy prose, two `<iframe>`
standalone-app embeds, and an embedded *historical* five-model nested-
cross-validation summary computed outside the notebook) with a 60-cell
generator-authored notebook, `scripts/generate_exercise_09_notebook.py`,
following `scripts/generate_exercise_08_notebook.py`'s architecture
exactly (hidden setup cell, `show_question()` answer-key hiding, the
`Blank` student/reference pair, generous tolerant sanity checks, native
`ipywidgets` activities in place of the old iframes).

### Content outline (60 cells)

1. **Run-first notice + hidden setup** -- imports, the same-origin/
   pinned-URL ABIDE loader (duplicated, not imported, per WP41 section
   4.7), the `show_question()` infrastructure and its six question
   definitions.
2. **Title and overview.**
3. **Section 1 -- Load and split.** Supplied: loads the 1,004-participant,
   360-predictor ABIDE-II table, makes **one** `train_test_split`
   (`test_size=0.25, random_state=42, stratify=group`), defines `X`, `y`,
   `X_train`, `X_val`, `y_train`, `y_val`. Reused, unmodified, by every
   later section -- no second split, no separate locked test set.
4. **Section 2 -- PCR.** Blank: fit `StandardScaler -> PCA ->
   LinearRegression` across `n_components in [2, 5, 10, 20, 50]`, collect
   `pcr_results`. Supplied tolerant check cell + supplied plot cell
   (handles an incomplete result). `show_question("q-leakage")`.
5. **Section 3 -- PLS.** Partly-completed-pipeline-style blank (hint
   comments, same shape as PCR): `pls_results`. Supplied check + a
   combined PCR/PLS plot. `show_question("q-pcr-vs-pls")`. Then the native
   **"PCR or PLS?"** activity: a small synthetic, standardized,
   mutually-orthogonal 2-D dataset (Gram-Schmidt-constructed, same
   technique the old iframe's own committed data used) with dropdowns for
   the predictive signal's weight on PC1 and the retained-component count
   -- both PCR and PLS refit live, plotted side by side with the PC1/PC2
   arrows.
6. **Section 4 -- SVM and SVR.** Parameter table (`C`/`epsilon`/`kernel`/
   `gamma`/`degree`, classification-only/regression-only distinctions).
   `show_question("q-c-gamma-epsilon")`. A supplied compact SVC
   boundary/margin/support-vector demo on a small synthetic 2-D dataset
   (`make_svc_dataset`, reused three more times later in the notebook).
   The native **"Explore an SVM Boundary"** activity: dataset/kernel/`C`/
   `gamma` dropdowns, train vs. validation points visually distinct
   (circle vs. triangle marker), support vectors circled.
   `show_question("q-train-vs-val")`. Blank: scaled linear/RBF `SVR`
   pipelines on a documented, fixed 300-row subset of the training
   partition, collecting `svr_results` -- subset discipline documented
   explicitly (see "Numbers verified" below).
7. **Section 5 -- Kernels beyond SVM.** A small RBF-similarity-vs-distance
   illustration. A compact table of how Ridge, Lasso/LogisticRegression,
   KNN, and trees/forests each relate (or don't) to the kernel trick.
   Blank: `Ridge(alpha=100)` vs. `KernelRidge(kernel="rbf", alpha=0.1,
   gamma=0.001)`, collecting `ridge_result`/`kernel_ridge_result`.
   `show_question("q-exact-vs-approx")`. A supplied brief
   `RBFSampler`+`LogisticRegression` example (on the same synthetic
   classification data, since age is continuous). An **optional**
   `RBFSampler`+`Lasso` challenge blank (not graded the same way --
   explicitly marked optional), on the real ABIDE predictors, showing
   where sparsity moves after the feature map. A supplied KNN
   Gaussian-distance-weighting snippet. A conceptual (no-code) paragraph
   on trees/forests. `show_question("q-knn-trees")`.
8. **Section 6 -- Compare and reflect.** Supplied: assembles every
   completed result into one table/bar-chart, missing results reported by
   name, never a traceback. Two bold-blockquote reflection prompts. A
   bulleted "what should we remember" summary. A collapsed, labeled,
   non-graded `<details>` historical reference to the old five-model
   nested-CV summary -- explicitly not this notebook's own result, and
   not used to grade anything here.

Total: **5 required student blanks** (PCR, PLS, SVR, Ridge+KernelRidge
combined) **+ 1 optional challenge** (RBFSampler+Lasso) = 6 `YOUR CODE
HERE` cells, within the spec's "approximately 5-7." **6 checked
questions**, one per requested topic (PCR vs. PLS, leakage, `C`/`gamma`/
`epsilon`, train vs. validation, exact vs. approximate kernels, KNN/trees
native kernels).

## Numbers verified before writing a single generator line

All computed directly against `book/lite/files/data/abide_age_brain.csv`
(the same 1,004-participant, 360-predictor table every other exercise
uses), using the exact split every later cell reuses
(`train_test_split(..., test_size=0.25, random_state=42, stratify=group)`
-> 753 train / 251 validation rows):

| Method | Setting | Validation MSE | Validation R2 |
|---|---|---|---|
| PCR | n_components=2/5/10/20/50 | 51.138 / 44.488 / 34.808 / 31.943 / 29.610 | -- |
| PLS | same grid | 39.935 / **29.658** / 38.797 / 48.906 / 49.555 | -- |
| SVR (300-row subset) | linear, C=1 | 94.996 | -0.018 |
| SVR (300-row subset) | linear, C=10 | 99.755 | -0.069 |
| SVR (300-row subset) | rbf, C=1 | 60.886 | 0.348 |
| SVR (300-row subset) | rbf, C=10 | 33.834 | 0.638 |
| SVR (300-row subset) | **rbf, C=100 (best)** | **29.535** | **0.684** |
| Ridge | alpha=100 | 31.813 | 0.659 |
| KernelRidge | rbf, alpha=0.1, gamma=0.001 | **21.924** | **0.765** |

PLS's 5-component best (29.658) is a genuine near-tie with PCR's own best
at 10x more components (29.610 at n=50) -- a real finding, not cherry-
picked, and exactly the kind of evidence Section 6's "why can't a single
split crown a universal winner" reflection prompt points at. KernelRidge
clearly beats plain Ridge here. The optional-challenge Lasso numbers (163/
360 nonzero features at MSE 29.877 plain vs. 15/200 nonzero transformed
features at MSE 58.515 after `RBFSampler`) are reported honestly, *worse*
performance included -- the cell's own point is where sparsity now
applies, not a performance claim.

**A real runtime-budget decision, documented in the generator's own module
docstring and the SVR task's own instructions:** `SVR(kernel="linear")` on
the full 753x360 training partition took 4-93 seconds per fit locally
(worse at higher `C`) -- unacceptable for a single-threaded, no-GPU Pyodide
kernel in the browser. Every SVR number in this notebook is a fixed,
documented 300-row random subset's own result (`SVR_SUBSET_N=300,
SVR_SUBSET_SEED=0`), and the student-facing instructions say so explicitly
("these are subset scores, not full-dataset scores").

Synthetic-data numbers (`make_svc_dataset`, seed=33, n=140, 98 train/42
val): "nonlinear" + `kernel="linear"`, C=1 -> train acc 0.541, val acc
0.548, every one of the 98 training points becomes a support vector (a
clean illustration of a linear boundary failing on a genuinely nonlinear
problem). Same data, `kernel="rbf"`, C=1 (this notebook's own compact demo
and the activity's own default) -> train acc 0.949, val acc 0.952, 35
support vectors. `RBFSampler`(gamma=0.5, n_components=50) +
`LogisticRegression` on the same data: plain logistic validation accuracy
0.476 (worse than chance on this split) vs. 0.952 after the feature map.

## Verification and stop conditions

### Offline/structural (149 tests, ~11s)

```
.venv/bin/python -m unittest \
  tests.test_exercise_09_notebook \
  tests.test_exercise_09_lite_notebook \
  tests.test_exercise_09_reference_execution \
  tests.test_exercise_manifest \
  tests.test_classify_release_change
```
Result: **OK, 149 tests in 10.967s.** (`test_exercise_09_lite_notebook.py`:
33 tests, structural, no kernel. `test_exercise_09_reference_execution.py`:
18 tests, executes the reference and the untouched student template in one
shared namespace -- no network, no `nbclient` (its own `ipywidgets.
Output()` context managers are the same documented nbclient-hang pattern
Exercises 1, 4, 5, 6, 7, and 8 already work around). `test_exercise_09_
notebook.py`: 53 tests, the untouched legacy-page suite, one test rewritten
for the one assertion this WP's own scope intentionally invalidates (see
the exact changelog). `test_exercise_manifest.py` and `test_classify_
release_change.py`: unchanged, confirmed still green since this WP never
touches the manifest or the classifier.

**Explicitly not run, per the WP's own scope**: Exercises 1-8's own
execution/browser suites, and the whole project's offline suite -- no
shared Python helper, CSS rule, or data export was touched (`build_
portable_notebook.py`/`smoke_portable_notebook.py` lost a dict entry each;
neither script's logic changed), so there is no mechanism by which this
WP could have broken any of their already-passing suites.

### Local build + real browser (Chromium, Playwright)

```
rm -rf book/_build
.venv/bin/jupyter-book build book                                    # 16s
.venv/bin/jupyter lite build --config book/lite/jupyter_lite_config.json \
  --lite-dir book/lite --output-dir book/_build/html/lite             # 7s
```
Both succeeded; `exercise_09.ipynb`/`exercise_09_portable.ipynb` were
copied into the Lite build automatically (`build:contents:copy:
exercise_09.ipynb` in the build log) -- **no `book/_toc.yml`, `book/
_config.yml`, or manifest change was needed at all** to make Exercise 9
reachable at its own JupyterLite route; those files stay fully untouched.

A throwaway Playwright spec (written, run, then deleted -- never
committed, matching the WP's "keep it local" instruction) drove a real
headless Chromium against this exact build, modeled directly on
`exercise-08-lite.spec.ts`'s own patterns:

| Check | Result | Duration |
|---|---|---|
| Untouched template: Run All Cells -> zero `.jp-mod-error` cells, data loads, all four required blanks' check cells show "Not complete yet", both supplied demos and the comparison table's graceful-missing message all present | **PASS** | 29.9s |
| 390px viewport: no horizontal page overflow; a checked-question radio label's own bounding box fits within 390px | **PASS** | 27.3s |
| Teacher-completed path: all five blanks filled with the reference solutions reproduce the table above exactly; the PCR/PLS widget's dropdown change updates its figure and summary line live; the SVM widget's dataset dropdown change updates its boundary/accuracy live; all six checked questions give "Correct" feedback on the right answer and "Not quite" (no visible `correct_index`) on a deliberately wrong one; **Download my notebook** produces a file containing the filled-in work | **PASS** | 1.1m |

Total real-browser verification: 3/3 passed, ~2 minutes.

### Local preview

A static server for the real combined build (`interactive/e2e-book/
serve-book.mjs`, the same server the Playwright suite uses) is running in
the background for the author's own review:

```
http://localhost:4174/lite/notebooks/index.html?path=exercise_09.ipynb
```

(`http://localhost:4174/` is the book root; Exercise 9 has no book page of
its own in this build, by design -- `book/_config.yml`'s `exclude_patterns`
still excludes `chapters/chapter_09/*`, unchanged.) To restart it later:
`cd interactive && PORT=4174 node e2e-book/serve-book.mjs` (after rebuilding
`book/_build` with the two commands above, if it was removed).

### Colab checklist and private copies

Per the WP's instruction, a private, **not committed, not published** set
of files was prepared in this session's own scratch directory (not any
git-tracked path) for the author's later real-Colab check:
- a verbatim copy of `scripts/reference_notebooks/exercise_09_reference.
  ipynb` (every blank filled);
- a verbatim copy of the actual downloadable `book/downloads/chapter_09/
  exercise_09_portable.ipynb` (what a student actually gets), for
  side-by-side comparison;
- `COLAB_CHECKLIST.md`, the WP41 maintainer guide section 12 template,
  filled in with this WP's own established numbers and all six
  checked-question topics, marked **UNVERIFIED (real Colab not reachable
  from this session)**, with a summary of what has actually been verified
  locally/in-browser instead.

Their local path was given to the user directly in chat, not repeated
here, to avoid implying it is a repository path. Simulated/local-browser
portability is not a substitute for a real Colab run and is not claimed to
be one.

## Deviations from the spec, and why

- **5 required blanks, not split further to reach 6.** The spec asks for
  "approximately 5-7"; Ridge and KernelRidge were kept as one combined
  blank (the spec itself frames them as one coupled comparison: "Students
  compare it with ordinary Ridge... saving kernel_ridge_result and
  ridge_result"). Counting the optional Lasso/RBFSampler challenge, there
  are 6 `YOUR CODE HERE` cells total, within range.
- **The old legacy static page (`book/chapters/chapter_09/exercise_09.
  ipynb`) was left untouched**, not rewritten into a short "transition
  page" the way Exercises 1-8's own `chapters/chapter_0N/exercise_0N.
  ipynb` became after their migrations. That page has been excluded from
  the Sphinx build entirely since WP49 (`exclude_patterns`), so it is
  already unreachable from the built site regardless of its content; a
  transition page only makes sense once Exercise 9 is actually
  re-included in `book/_toc.yml`/`exclude_patterns` -- a decision this WP
  was explicitly told to leave to a later deployment WP. Its own
  structural test (`tests/test_exercise_09_notebook.py`) is therefore
  still exercising real, currently-accurate content, with one exception
  (see the changelog) where this WP's own change legitimately invalidated
  one assertion.
- **No new Exercise-9-specific Playwright spec was committed.** The spec's
  own browser-verification checklist was satisfied with a throwaway,
  deleted-after-use script instead of a permanent `exercise-09-lite.spec.
  ts`, specifically so this WP adds nothing `npm run test:e2e:book` would
  ever pick up -- consistent with "do not add Exercise 9 to the live
  release gate." Writing and committing that permanent spec is natural
  follow-up work for the deployment WP that actually wires Exercise 9 in.

## Known follow-up (not fixed in this WP, by design)

`.github/workflows/legacy-notebook-smoke.yml` still has a step running
`python scripts/smoke_portable_notebook.py --notebook chapter_09`, which
will now fail (`chapter_09` is no longer a registered `--notebook` choice,
since this WP removed it from that script's `SMOKE` dict for the same
`ipywidgets.Output()`/`nbclient` reason Exercises 1/4/5/6/7/8 are already
absent there). This workflow only runs on `workflow_dispatch` or a push to
`main` touching specific paths -- it cannot run from this local, unpushed
branch, so it has no effect here. Fixing it requires a release-wiring
decision (drop the chapter_09 step entirely? route it to the new reference-
execution test instead?) that belongs with whichever WP actually
authorizes Exercise 9's deployment, not this one.

## Confirmation

- Branch `feature/wp51-active-exercise-09`, clean working tree after this
  commit (`git status --short` empty).
- No merge, no push, no deployment, no WP52, no GitHub Actions
  interaction at any point in this session.
- Stopping here for the course author's review, per the WP's own
  instruction.
