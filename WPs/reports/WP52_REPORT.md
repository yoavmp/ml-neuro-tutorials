# WP52 report: Exercise 9 review fixes and publication

## Success or failure -- read this first

**Success.** All 15 author review corrections are applied to Exercise 9's
generator, Exercise 9 is published to the live site alongside Exercises
1-8, the full offline test suite (1161 tests) and the full combined
Jupyter Book + JupyterLite Playwright suite (112 tests) both pass, the
production deploy succeeded, and the live site has been verified directly
(hub listing, transition page, JupyterLite route, portable download,
Chapters 10-12 still unpublished). Real Google Colab verification remains
**pending** (not performed, as the WP explicitly allows), with a private
checklist and copies prepared for the author.

## Starting state and branch

Began at `feature/wp51-active-exercise-09` tip `14fb73e`, matching the WP's
own "Authority and starting point" description exactly: WP01-WP08's
interactive-EDA work live, WP51's Exercise 9 generator built but local-only
(not wired into `book/_toc.yml`, `book/_config.yml`, the manifest, or
`launch-buttons.js`). Checkpoint branch `checkpoint/wp52-pre-work` created
at that tip before any edit.

All WP52 work landed as one commit (`2e18798`, "WP52: Exercise 9 review
fixes (all 15 items) and publication") on that feature branch, then the
branch was fast-forward-merged into local and remote `main` (`c5acbe3` ->
`2e18798`, no merge commit -- the feature branch was already a direct,
undiverged descendant of `main`) and pushed as the one production release
this WP authorizes. See `WPs/reports/WP52_EXACT_CHANGELOG.md` for the full
file list.

## The 15 review corrections -- acceptance table

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Title -> "Exercise 9: Advanced Models" | Done | Cell 2; `test_title`; confirmed live (`curl` on the deployed `exercise_09.ipynb`) |
| 2 | PCR starter cell: exact required shape, no loop/pipeline/fit/predict/score solution, even commented | Done | `PCR_COMPONENT_GRID = [2, 5, 10, 20, 50]` + `pcr_results = []` + prose hints only; `test_pcr_blank_has_exact_starter_shape`, `test_blanks_contain_no_executable_solution_even_commented` |
| 3 | PCR/PLS widget: every control label (incl. "Weight on PC1"/"Components") fully readable, no tab overlap, desktop + 390px | Done | `style={"description_width": "initial"}` + `.widget-controls-row` CSS backstop + `controls_row()` helper; verified live-browser at desktop and 390px (label `scrollWidth<=clientWidth`, no bounding-box overlap) |
| 4 | Weight-on-PC1 visibly changes target-dependent part of left plot (recolor by target, rotating signal/PLS arrows); PC1/PC2 and predictor coords may stay fixed, explained briefly; right plot has a fixed MSE y-axis across every setting; verified in a real browser | Done | Points colored by `y2`, train/val now by marker shape; "true signal" + "PLS direction" arrows rotate with `w1`; PC1/PC2/predictor coordinates annotated "(fixed)" with an explanatory paragraph; `_PCRPLS_MSE_YLIM` computed once from the global max over the whole grid; live Playwright run changes "Weight on PC1" to 0.9 and "Components" to 2 and asserts the printed summary updates each time |
| 5 | SVM/SVR question -> "mark all correct", separate C/gamma/epsilon statements, >=2 true and plausible false | Done | `make_multi_choice_question`; 3 true + 3 false statements, 2 per parameter; sensible correct/incorrect/partial feedback without revealing which items were right; hidden answer key preserved |
| 6 | Vary correct-answer position across all checked questions (incl. multiselect), reproducible per-question, stable across reruns | Done | Per-question `shuffle_seed` + `random.Random(seed).shuffle`; positions: pcr-vs-pls@2, leakage@1, c-gamma-epsilon(multi)@{1,4,5}, train-vs-val@1, exact-vs-approx@2 of 3 (none at 0); reproducibility and "not all first" verified by execution (`test_shuffle_is_reproducible_and_varies_positions_across_questions`) and live-browser clicking by option TEXT |
| 7 | Remove "A compact SVC example" section (redundant plot/code) | Done | Section removed; `make_svc_dataset` relocated into the SVM activity's own self-contained cell (still reused by that activity) |
| 8 | Fix truncated/overlapping labels in "Explore an SVM boundary", desktop + narrow; test controls after | Done | Same `controls_row()`/`description_width` fix applied to all 4 dropdowns; live-browser label-overflow check at 390px; live dataset-dropdown interaction test |
| 9 | SVR task: remove disguised solution; keep high-level prompts + small param list + shape hints; mention GridSearchCV as a comment only | Done | Blank keeps `SVR_PARAM_SETS` (the task's own object, not the solution) + subset setup (supplied) + prose hint; GridSearchCV mentioned only inside a `#`-comment, never as executable code (`test_svr_blank_mentions_gridsearchcv_as_a_comment_only`) |
| 10 | Section 5: remove kernel-application table + everything from "Lasso and logistic regression" onward; keep a short, accurate Ridge-vs-KernelRidge intro; explain exact counterpart / different parameterization, no identical-prediction claim | Done | Table and that whole tail (logistic+RBFSampler demo, optional Lasso challenge, KNN demo, trees note, and the `q-knn-trees` question that followed it) removed; new intro text states KernelRidge(rbf) is the exact counterpart of Ridge in a different parameterization and explicitly does not promise identical predictions for arbitrary parameters; see **Deviation** below for the resulting question count |
| 11 | Every blank: no commented-out complete answers; "Fill Code Here" marker itself a comment; concise hints/output names/checks kept | Done | All 4 blanks (PCR, PLS, SVR, Ridge+KernelRidge) contain zero `.fit(`/`Pipeline([`/`.predict(`/scoring-call fragments, commented or not; every `YOUR CODE HERE` line starts with `#` |
| 12 | Preserve Section 6 after the Section 5 cut, adjust dependencies/numbering | Done | No numbering break (only content *within* Section 5 removed); Section 6 unaffected structurally |
| 13 | Section 6: compare on full training data/full feature set/same validation participants; student's small-subset SVR stays pedagogical, not ranked; separate offline full-data SVR benchmark, documented and reproducible, with its own parameters/counts/seed/MSE/R2; PCR/PLS/Ridge/KernelRidge also get R2; exploratory-vs-unbiased caveat stated | Done | `scripts/compute_exercise_09_svr_benchmark.py` + committed `exercise_09_svr_benchmark.json` (SVR() library defaults, chosen before any validation score, `n_train=753`/`n_val=251`/`n_features=360`/split `test_size=0.25, random_state=42, stratify=group`, `val_mse=54.083`, `val_r2=0.421`); embedded as `SVR_BENCHMARK` with its own labeled table row; PCR/PLS schemas now require `val_r2`; student's own SVR activity printed separately, explicitly "not ranked"; exploratory-vs-final-test caveat added to the intro markdown |
| 14 | Fix Section 6 Matplotlib warning: explicit tick positions before `set_xticklabels` | Done | `ax.set_xticks(x_positions)` immediately before `set_xticklabels(...)`; verified by executing that exact cell in isolation with `warnings.catch_warnings(record=True)` -- zero Matplotlib warnings |
| 15 | Remove the collapsed historical-reference section entirely | Done | `<details>` block, "historical", and "nested" no longer appear anywhere in the notebook's markdown or code |

### Deviation to flag explicitly (item 10 vs. the verification checklist's "six questions")

Item 10's instruction to remove "the subsequent ... material and everything
after it within Section 5" removes the KNN/trees paragraph, its demo, *and*
the checked question that sat after it in cell order (`q-knn-trees`, which
asked whether KNN/trees have a `kernel=` switch -- a question about exactly
the material item 10 cuts). That leaves **5** checked questions, not the
"six" the Verification section's own bullet names. I followed item 10's
specific, detailed content-removal instruction over that bullet's bare
count -- most plausibly a figure not recomputed after the cut, since no
instruction asks to relocate or preserve that question elsewhere, and doing
so would reintroduce the KNN/trees content item 10 explicitly removes.
Every verification step below that could be scoped to "six" was run against
the actual five questions that ship instead.

## Release wiring

- `book/config/exercise_manifest.json`: Exercise 9 flipped to
  `migrationState: "migrated"` with `templateNotebookPath`,
  `browserWorkingCopyName`, `liteUrl`, `templateVersion: 1`, and its real
  `dataAssets` (`abide_age_brain.csv` + its manifest -- the only data this
  exercise's generator actually loads); `$comment` updated.
- `book/_toc.yml`: `chapters/chapter_09/exercise_09` added right after
  Exercise 8; the old WP49 comment updated to "Exercises 10-12."
- `book/_config.yml`: `chapters/chapter_09/*` removed from
  `exclude_patterns`; comment updated.
- `book/_static/launch-buttons.js`: the `chapter_09` -> portable-download
  Colab-button entry removed from `PAGE_TO_PORTABLE` (now migrated, so it
  gets the same top-bar-Colab-button suppression as Exercises 1-8); header
  comment updated to list Exercise 9's own transition-page generator.
- New `scripts/generate_exercise_09_transition_page.py` +
  `book/chapters/chapter_09/exercise_09.ipynb` rewritten by it (the old
  65KB legacy nested-CV notebook replaced by a 2-cell transition page,
  exactly mirroring Exercises 1-8's own pattern); new
  `tests/test_exercise_09_transition_page.py`.
- `.github/workflows/legacy-notebook-smoke.yml`: the stale
  `smoke_portable_notebook.py --notebook chapter_09` step removed (that
  registry entry was already retired in WP51 for the documented
  `ipywidgets.Output()`/nbclient hang, so this step would have failed
  argparse's own `choices` check); Exercise 10's own step, trigger paths,
  and title updated to say so explicitly. Confirmed this did **not**
  silently no-op: the corresponding GitHub Actions run after the push
  (`37849393325`) completed successfully running only Exercise 10's check.
- `scripts/classify_release_change.py`: all eight `(0[1-8])` per-exercise
  path regexes widened to `(0[1-9])`; `PUBLISHED_EXERCISE_NUMBERS` bumped to
  `range(1, 10)`; docstring updated. Without this, any future Exercise-9-only
  edit would fall through to the generic `^scripts/`/`^book/chapters/`
  shared patterns and force a `full` gate forever -- defeating the whole
  point of WP50's scoped gate for this exercise going forward.
- `.github/workflows/deploy.yml`: the full-gate generator-staleness loop
  widened to `01 02 03 04 05 06 07 08 09` plus a new
  `compute_exercise_09_svr_benchmark.py --check` call; two step
  names/comments updated from "Exercises 1-8" to "Exercises 1-9".
- Confirmed Exercises 10-12 remain excluded: `tests/test_book_structure.py`
  (updated for the Exercise 9 migration, see below) and a live check
  (`chapters/chapter_1{0,1,2}/...html` all return live HTTP 404).

### A second shared-test update this surfaced

`tests/test_book_structure.py` (not an Exercise-9-specific file) hardcoded
"only Exercises 1-8 are published" in three tests (`range(1, 9)`, an
explicit `assertNotIn` for `chapters/chapter_09/exercise_09`, and
`len(files) == 8`). The first full local offline-suite run (see
"Verification" below) caught all three failing after the toc/config change;
all three updated for the 1-9 boundary and renamed accordingly.

## Full-training-data SVR benchmark -- provenance

`scripts/compute_exercise_09_svr_benchmark.py` (new, committed): loads
`book/lite/files/data/abide_age_brain.csv`, makes the exact same split
every other model in this notebook uses
(`train_test_split(..., test_size=0.25, random_state=42, stratify=group)`
-> 753 train / 251 val / 360 features), fits
`Pipeline([StandardScaler(), SVR()])` with scikit-learn's own **library
defaults** (`kernel="rbf", C=1.0, gamma="scale", epsilon=0.1`) -- chosen
specifically *because* it requires no decision informed by any validation
score -- and writes the result to the committed artifact
`scripts/reference_notebooks/exercise_09_svr_benchmark.json`:

```
val_mse = 54.083, val_r2 = 0.421
```

This is honestly **worse** than Ridge (31.813/0.659), KernelRidge
(21.924/0.765), PCR's best (29.610/0.683), and PLS's best (29.658/0.682) --
not cherry-picked to win, which is the point: it demonstrates a real,
reproducible, not-tuned-against-validation number, clearly distinguished in
the notebook from both the student's own 300-row-subset SVR activity result
and the old pre-WP51 nested-CV historical summary (removed, item 15).
`tests/test_exercise_09_svr_benchmark.py` keeps this artifact honest
(`--check` must pass; split/row/feature counts; "not tuned" flag; the exact
library-default parameters; plausible, non-perfect scores).

## Numbers verified directly (same split everywhere)

| Method | Setting | Validation MSE | Validation R2 |
|---|---|---|---|
| PCR | n=2 / 5 / 10 / 20 / **50 (best)** | 51.138 / 44.488 / 34.808 / 31.943 / **29.610** | 0.452 / 0.523 / 0.627 / 0.658 / **0.683** |
| PLS | n=2 / **5 (best)** / 10 / 20 / 50 | 39.935 / **29.658** / 38.797 / 48.906 / 49.555 | 0.572 / **0.682** / 0.584 / 0.476 / 0.469 |
| SVR (300-row subset, pedagogical) | linear C1 / C10, rbf C1 / C10 / **C100 (best)** | 94.996 / 99.755 / 60.886 / 33.834 / **29.535** | -0.018 / -0.069 / 0.348 / 0.638 / **0.684** |
| Ridge (full data) | alpha=100 | 31.813 | 0.659 |
| KernelRidge (full data) | rbf, alpha=0.1, gamma=0.001 | **21.924** | **0.765** |
| SVR instructor benchmark (full data, untuned) | library defaults | 54.083 | 0.421 |

All identical to WP51's own already-verified numbers (this WP changed no
modeling code in the required PCR/PLS/SVR/Ridge/KernelRidge blanks, only
their schemas, hints, and surrounding wiring) plus the two new R2 columns
and the new full-data SVR row.

## Verification

### Local, offline

```
.venv/bin/python -m unittest \
  tests.test_exercise_09_lite_notebook tests.test_exercise_09_reference_execution \
  tests.test_exercise_09_transition_page tests.test_exercise_09_svr_benchmark \
  tests.test_exercise_manifest tests.test_classify_release_change \
  tests.test_book_structure tests.test_wp35_content_audit
```
**143 tests, ~13s, OK.**

Full repository offline suite, run once the shared release-wiring files
were touched (the WP's own instruction: "For shared release wiring, run
focused manifest/toc/route tests; let the WP50 CI gate determine whether
its full suite is required" -- and separately, because the classifier
itself was going to select `full`, I ran it locally first rather than
finding out only in CI):
```
.venv/bin/python -m unittest discover -s tests
```
**1161 tests, 1322-1384s (~22-23 min) across two runs, OK, 0 failures, 11
skipped** (pre-existing, unrelated to this WP). The *first* run (before the
two fixes below) surfaced 4 real failures -- see "Bugs found and fixed."

### Local, browser (real headless Chromium against the actual combined build)

```
rm -rf book/_build
.venv/bin/jupyter-book build book                                          # ~4.8s
.venv/bin/jupyter lite build --config book/lite/jupyter_lite_config.json \
  --lite-dir book/lite --output-dir book/_build/html/lite                  # ~6.2s
cd interactive && npx playwright test --config playwright.book.config.ts \
  exercise-09-lite.spec.ts chapter09.spec.ts launch-buttons.spec.ts
```
**18/18 passed** (final clean run, ~1.6-1.7 min), covering: both widgets
(live interaction, not just inspecting callbacks), all five checked
questions by option **text** (never position, since they're shuffled),
the multiselect question's correct/partial feedback, a 390px label-overflow
check (no clipped or overlapping control label on either widget), the
untouched template's graceful "Not complete yet" guidance on all four
blanks, reset/back navigation, and a download-contains-the-edits check.

Then the full combined-build suite, confirming no regression to Exercises
1-8 or shared fixtures:
```
npm run test:e2e:book
```
**112/112 passed, 29.8 min.** Also ran (unaffected by this WP, confirmed
clean): `npm run typecheck` (after fixing issues in my own new spec file,
see below) and `npm run test:unit` (481 tests, pre-existing, green).

### Bugs found and fixed during this WP (caught before any of this reached a student)

1. **CPU contention, not a regression.** Running the full offline Python
   suite and the Playwright browser suite concurrently on this machine
   caused transient timeouts in the browser suite (kernel-idle waits,
   scroll-into-view waits) -- the same documented pattern
   `interactive/playwright.book.config.ts`'s own comments already describe
   for CI. Resolved by not running them concurrently; the identical
   Playwright run passed cleanly alone.
2. **Author-facing-language leak**, caught by the pre-existing
   `tests/test_wp35_content_audit.py` (which audits every exercise, not
   just Exercise 9): my own `"(WP52 item N)"` explanatory comments, and a
   CSS class literal containing `"wp51"`, ended up inside the actual
   **notebook cell source** (the hidden setup cell and the PCR/PLS widget
   cell) -- not just the generator script's own comments/cell-id metadata,
   which are never shipped. Fixed: removed the WP references from that
   text, renamed the CSS class from `wp51-widget-controls` to
   `widget-controls-row` (no WP number, matching the exact convention every
   other migrated exercise's own `checked-question` class already uses).
3. **`tests/test_book_structure.py`** -- see "A second shared-test update"
   above.
4. **My own Playwright-spec authoring bugs**, found and fixed by actually
   running the spec, not guessed: (a) one assertion anchored on text that
   is pixels inside a rendered Matplotlib image
   (`ax.set_title("Full training data...")`), not real DOM text -- switched
   to a real, visible table-cell string; (b) Shift+Enter advances
   JupyterLab's active cell, which can scroll a just-run widget back out of
   the windowed notebook's rendered range before the next interaction --
   fixed by re-locating (re-scrolling into view) immediately before each
   interaction rather than reusing a locator captured earlier; (c)
   `selectOption` by option label failed for one `(label, value)`-tuple
   Dropdown -- switched to index-based selection, matching the
   already-working convention every other exercise's own spec already
   uses; (d) Section 6's own compare cell does not automatically re-run
   when an earlier blank is filled (no notebook cascades, by design, the
   same behavior every other migrated exercise's spec already documents)
   -- the test needed to explicitly re-run it before asserting on the
   updated table.

None of (1)-(4) reflect a defect a student would ever have hit; (2) and the
`test_book_structure.py` fix are the only two that touched anything besides
this WP's own new test file.

### Teacher-filled portable notebook, offline

`tests/test_exercise_09_reference_execution.py` executes
`scripts/reference_notebooks/exercise_09_reference.ipynb` (every blank
filled with the generator's own reference solution, byte-structurally
synchronized with the shipped portable/JupyterLite notebooks by
`StructuralSynchronization`) in one shared Python namespace -- the same
approach WP41/WP44-47/WP51 established, since this notebook's native
`ipywidgets.Output()` widgets hang `nbclient`'s real kernel with no
frontend attached. Zero errors; every number above reproduced; the
full-data SVR benchmark confirmed distinct from the student's own subset
result; the Section 6 comparison table confirmed to carry `val_r2` for
every row; the Section 6 compare cell re-executed in isolation under
`warnings.catch_warnings(record=True)` -- zero Matplotlib warnings.

### Colab

**Pending**, as the WP explicitly allows recording rather than blocking the
release on. Prepared, privately, not committed: a verbatim copy of the
teacher-filled reference notebook, a verbatim copy of the actual
downloadable portable notebook, and a filled-in copy of the WP41
maintainer-guide's own Colab-acceptance-checklist template (file paths
given to the user directly, not repeated here, per the same WP51
precedent). No claim of actual Colab verification is made anywhere in this
report.

## The production push

`scripts/classify_release_change.py` on the actual pushed commit:
```
GATE: full
reason: shared/unknown path(s) changed: .github/workflows/deploy.yml, 
  .github/workflows/legacy-notebook-smoke.yml, book/_config.yml, 
  book/_static/launch-buttons.js (classified "unknown" -- see note below), 
  book/_toc.yml, book/config/exercise_manifest.json, 
  interactive/e2e-book/chapter09-dark-mode.spec.ts, 
  interactive/e2e-book/launch-buttons.spec.ts, 
  interactive/playwright.book.config.ts, several shared scripts/tests (+9 more)
```
This is exactly the case the WP spec itself names ("the first release of
Exercise 9 changes shared publication wiring ... its classifier may
correctly select the full gate") -- **not** overridden, weakened, or
second-guessed.

Minor, pre-existing, out-of-scope note: `book/_static/launch-buttons.js`
was already classified `"unknown"` rather than `"shared"` before this WP
(no `_SHARED_PATTERNS` entry matches that path) -- functionally identical
outcome (`unknown` forces `full`, same as `shared`), so nothing to fix for
this release; not touched, since neither the 15 review items nor the
release-wiring section asked for it.

Pushed: `git push origin main` (fast-forward, `c5acbe3` -> `2e18798`).

### The real CI run

GitHub Actions run `37849393166` ("Build and deploy Jupyter Book"):
**success**, classify job 8s, build-and-deploy job **1h46m38s**. Per-step
durations over five minutes:

| Step | Duration |
|---|---|
| Unit-test the Python scripts (offline, full gate) | ~24m28s |
| End-to-end test the combined book + JupyterLite build (full gate) | ~1h18m27s |

Every full-gate step succeeded, including the widened
`generate_exercise_0{1..9}_notebook.py --check` /
`_transition_page.py --check` loop and the new
`compute_exercise_09_svr_benchmark.py --check`. `Publish website` (the
`peaceiris/actions-gh-pages` step) completed in 4s.

A companion workflow, `37849393325` ("Legacy notebook smoke test (Exercise
10)"), triggered by the same push (WP51's own prior edit to
`scripts/smoke_portable_notebook.py`, now merged) and **succeeded**
independently, confirming the stale `chapter_09` step's removal did not
silently break Exercise 10's own, still-relevant check.

### Live-site verification (after the deploy, by direct HTTP check against the real published site)

- `gh-pages` branch HEAD commit message: `deploy: 2e187981f0f8790ebc8ba7fb4e6eb0f0acedbeb3`
  -- matches the pushed `main` SHA exactly.
- `https://yoavmp.github.io/ml-neuro-tutorials/contents.html` links to
  `chapters/chapter_09/exercise_09.html` (the hub lists Exercise 9).
- `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_09/exercise_09.html`
  -- HTTP 200, zero `<iframe>`, contains
  `<a href="../../lite/notebooks/index.html?path=exercise_09.ipynb">Open Exercise 9</a>`
  and a working portable-download link.
- `https://yoavmp.github.io/ml-neuro-tutorials/lite/notebooks/index.html?path=exercise_09.ipynb`
  -- HTTP 200.
- `https://yoavmp.github.io/ml-neuro-tutorials/lite/files/exercise_09.ipynb`
  and `.../exercise_09_portable.ipynb` -- both HTTP 200; the deployed
  notebook's own title cell reads `# Exercise 9: Advanced Models`.
- `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_1{0,1,2}/exercise_1{0,1,2}.html`
  -- all three HTTP **404** (Chapters 10-12 remain unpublished).
- `https://yoavmp.github.io/ml-neuro-tutorials/_static/launch-buttons.js`
  -- live `PAGE_TO_PORTABLE` map contains only `chapter_10`; the two
  remaining `"chapter_09"` substrings on that page are comment text, not
  map entries.

## Deviations, summarized

1. Five checked questions, not six -- see the dedicated callout above
   (item 10's cut necessarily removes its own question).
2. `launch-buttons.js`'s pre-existing classifier gap (`"unknown"` instead of
   `"shared"`) -- noted, not fixed (out of scope, no behavior change).
3. Real Google Colab acceptance -- recorded pending, per the WP's own
   explicit allowance, not treated as a release blocker.

## Final git state

- `main` (local and `origin/main`, in sync): `2e18798`.
- `gh-pages`: `e4568cd`, marker `deploy: 2e18798...`.
- Checkpoint branch `checkpoint/wp52-pre-work` left in place at the
  pre-WP52 tip (`14fb73e`) for reference.
- Working tree clean after this report's own closing commit (see `git
  status --short`).
