# WP57 Release Report — Exercise 12 published, Exercises 10-11 titled placeholders

## Summary

Finished the outstanding WP57R corrections, then released Exercise 12
("Common Mistakes and Pitfalls") to production alongside Exercises 1–9,
with Exercises 10–11 retitled as "coming later" placeholder stubs.
Merged `feature/wp57-active-exercise-12-common-mistakes` into `main`.

**Honest correction, reported in full rather than smoothed over**: the
release took two pushes, not the intended one. The first push
(`1dcc902`) failed CI's offline unit-test step — two pre-existing,
course-wide test files I had not run locally before that push
(`tests/test_placeholder_exercises.py`, `tests/test_wp25_content_audit.py`)
still assumed Exercise 12 was an unpublished placeholder and Exercise
11's old title. The live site was **never affected**: GitHub Actions
never reaches the "Publish website" step when an earlier required step
fails, confirmed directly (that step shows as skipped on the failed run).
I fixed both test files to match the actually-intended state (not
weakened — see "Release tests," below), ran the complete offline suite
(1318 tests, not a subset) to catch anything else before trying again,
and pushed the fix as commit `d3a9f71`. That second push's CI run
succeeded in full and deployed.

- Final commit on `main`: **`d3a9f71`**
- First push attempt: `1dcc902` → CI run `38620131288` → **FAILED** (offline
  unit tests; site never touched)
- Corrective push: `d3a9f71` → CI run `38636765295` → **SUCCEEDED** (both
  jobs green, 1h54m; `Publish website` step ran)
- Live site: `https://yoavmp.github.io/ml-neuro-tutorials/` —
  **verified live, matches every expectation** (see "Live verification")

## 1. Pyodide/threadpoolctl warning (fixed and verified live)

**Operation that triggers it**: `KNeighborsRegressor(...).fit()`/`.predict()`
inside Case 1's "Does it change a prediction score?" comparison cell — the
first KNN usage anywhere in the notebook. Confirmed by scrolling directly
to that cell in a real JupyterLite session (Chromium via Playwright) and
reading its actual stderr output div:

```
/lib/python3.14/site-packages/threadpoolctl.py:1135: RuntimeWarning: JsProxy.as_object_map() is deprecated. Use as_py_json() instead.
  for filepath in LDSO.loadedLibsByName.as_object_map():
```

This is threadpoolctl's own Pyodide-detection code (its pairwise-distance
backend probes loaded BLAS/OpenMP libraries the first time any estimator
using that backend is fit; under Pyodide the probe walks a JS object
through a now-deprecated bridge method). It is upstream, not this
notebook's own code, and fires at most once per kernel session — Case 5's
later, independent `KNeighborsRegressor` calls showed no warning at all
once Case 1 had already triggered and absorbed it.

**Fix** (code-level, narrowly scoped — not a blanket `RuntimeWarning`
suppression): wrapped exactly the two `.fit()`/`.predict()` calls inside
`_case1_compare_knn` in a `warnings.catch_warnings()` context manager with
a filter matching only this message's exact text. No dependency version
bump was attempted: this session has no network access to verify whether
any newer threadpoolctl release has fixed its own Pyodide-detection code,
and forcing a version via `micropip.install` risks an untested
incompatibility with the preloaded, binary-pinned scikit-learn/numpy
stack for a purely cosmetic warning — the documented, defensible call per
the WP's own "if it cannot be fixed safely here, suppress only that
specific warning" instruction.

**Verified live** (real JupyterLite, Chromium via Playwright, before and
after the fix):
- Before: the cell's output area had two divs — a `stderr` div containing
  the warning above, and a `stdout` div with the comparison results.
- After: only the `stdout` div remains; the warning div is gone.
- Comparison results unchanged in both runs:
  ```
  full split (n_train=602, n_val=201): leaky val MSE=32.715  honest val MSE=32.390  (leaky worse by 0.324)
  n=100 (n_train=75, n_val=25): leaky val MSE=60.014  honest val MSE=60.911  (leaky better by 0.897)
  n=60 (n_train=45, n_val=15): leaky val MSE=10.334  honest val MSE=10.630  (leaky better by 0.296)
  ```
- No other console warning (threadpoolctl/JsProxy-related or otherwise)
  appeared anywhere else in the notebook in either run.

## 2. Placeholder titles

| Exercise | Old title | New title | Still "coming later"? |
|---|---|---|---|
| 10 | "Coming Later" | **"Exercise 10: Deep Learning"** | Yes — body text unchanged ("Materials for this exercise will be added before the practice session."), no runnable notebook, no launch/download button (verified: `launch-buttons.spec.ts`'s new test) |
| 11 | "Embeddings and Representational Similarity Analysis" | **"Exercise 11: Embeddings and RSA"** | Yes — same body text, no notebook, no button |

The real legacy Exercise 10 notebook (`book/chapters/chapter_10/exercise_10.ipynb`)
is byte-for-byte untouched (`tests/test_exercise_10_notebook.py`, 20/20
unmodified and passing) and remains excluded from the Sphinx build by
`book/_config.yml`'s `exclude_patterns`, preserved for later redesign.

## 3a. The CI failure and its fix (full detail)

`tests/test_placeholder_exercises.py` and `tests/test_wp25_content_audit.py`
are two pre-existing, course-wide audits I did not include in my local
"focused" test selection before the first push. Both hardcode assumptions
about Exercises 11–12 that this release deliberately changes:

- `test_placeholder_exercises.py`'s `PLACEHOLDER_TITLES` dict treated
  Exercise 12 as a plain-Markdown placeholder (no `.ipynb`, no portable
  notebook) and expected Exercise 11's old title.
- `test_wp25_content_audit.py`'s `EXERCISE_TITLES` dict and its
  `_title_of()`/final-project-reference path logic branched on `n <= 10`
  to decide whether to read a real `.ipynb` or a placeholder `.md` —
  Exercise 12 fell into the wrong branch now that it is real content.

Both files had already been updated this same way for every *previous*
exercise's placeholder → real-notebook conversion (WP27 through WP38 each
removed that exercise from `PLACEHOLDER_TITLES` and updated
`EXERCISE_TITLES`/the path branching) — I followed the exact same,
already-established pattern for Exercise 12, and updated Exercise 11's
expected title to the new, authorized wording. No check was removed or
loosened: `test_placeholder_exercises.py` now covers exactly the one
exercise (11) still using its placeholder convention; the two
`test_wp25_content_audit.py` methods that iterate 1–12 now correctly read
Exercise 12's real `.ipynb`, and its portable-notebook sweep now also
covers Exercise 12's real portable copy (previously it only checked
1–10, since 11–12 had none).

Verified before the corrective push: both files pass in isolation, and
then the **complete** offline suite (`python -m unittest discover -s
tests`, not a hand-picked subset) — 1318 tests, 11 pre-existing skips,
**zero failures or errors** — run fully detached (durable log + PID,
confirmed via `ps`) per the maintainer-guide procedure, after an earlier
attempt to run it via the harness's own background-task flag was killed
by a session restart before completion (recovered by re-launching
properly detached, not by assuming the first attempt's result).

## 3. Production release

- `book/_toc.yml`: Exercises 1–9, then `chapters/chapter_10/placeholder`,
  `chapters/chapter_11/exercise_11`, `chapters/chapter_12/exercise_12` — 12
  entries total, in order.
- `book/_config.yml`: `exclude_patterns` now excludes only the real legacy
  `chapters/chapter_10/exercise_10.ipynb` — everything else in chapters
  10–12 builds normally.
- `book/config/exercise_manifest.json`: exercise 12 moved to
  `migrationState: "migrated"` with full lite wiring (`templateNotebookPath`,
  `browserWorkingCopyName`, `liteUrl`, `templateVersion: 1`, `dataAssets`
  reusing the same-origin ABIDE export); exercises 10–11 titles updated to
  match their new placeholder pages; `migrationState` for 10–11 stays
  `"legacy"` (not migrated — titled stubs, not active content).
- `book/_static/launch-buttons.js`: removed the stale, already-dead
  `chapters/chapter_10/exercise_10.html` mapping entry (that page is never
  built); documented that Exercise 12 and both placeholders are
  intentionally unmapped.

**Release tests updated to match the intended state (not weakened)**:
- `tests/test_exercise_manifest.py::test_only_exercises_1_through_9_and_12_are_migrated`
  (renamed from `..._1_through_9_are_migrated`) now expects the migrated
  set `[1..9, 12]`.
- `tests/test_book_structure.py`'s three previously-WP57-invalidated
  assertions are rewritten, not deleted or loosened: the toc now expects
  exactly the 12-entry list above
  (`test_exercises_one_through_nine_and_twelve_are_published_in_order`);
  a new `test_exercise_10_legacy_notebook_preserved_but_not_published`
  confirms only the real legacy notebook stays out of the toc; a new
  `test_exercise_10_and_11_placeholders_are_titled_and_not_misleading`
  confirms both placeholder pages' titles and the absence of `.ipynb`
  mentions in their body text. Every other, unrelated assertion in both
  files is untouched and still passing.
- `interactive/e2e-book/launch-buttons.spec.ts`: added live-verified tests
  confirming Exercise 12 and both placeholders get no Colab button (17/17
  passing, including these 3 new ones).
- `interactive/e2e-book/warning-sweep.spec.ts`: added `12` to the
  course-wide list of published exercises this check covers (not run
  locally this session — see "Focused local checks" below — but will run
  as part of CI's full-gate browser suite).

## Actual prediction-score comparison (Case 1, directly verified, unchanged
by the warning fix)

| Size | leaky val MSE | honest val MSE | direction |
|---|---|---|---|
| full (602/201) | 32.715 | 32.390 | leaky **worse** by 0.324 |
| n=100 (75/25, seed 0) | 60.014 | 60.911 | leaky **better** by 0.897 |
| n=60 (45/15, seed 0) | 10.334 | 10.630 | leaky **better** by 0.296 |

(Case 2's values, from WP57R, are unchanged by this release: contaminated
R² = 0.8973, honest R² = 0.1209.)

## Focused local checks (per the WP's own instruction — no course-wide
re-run of Exercises 1–9)

| Suite | Result |
|---|---|
| `tests/test_exercise_12_lite_notebook.py` + `test_exercise_12_reference_execution.py` + `test_exercise_12_transition_page.py` | 92/92 OK |
| `tests/test_exercise_manifest.py` | 10/10 OK |
| `tests/test_book_structure.py` | 16/16 OK (3 rewritten, 13 unchanged) |
| `tests/test_exercise_10_notebook.py` (confirms the real legacy notebook is untouched) | 20/20 OK, unmodified |
| `tests/test_classify_release_change.py` (confirms the classifier itself still behaves correctly) | 59/59 OK, unmodified |
| Local combined build (`jupyter-book build book --all` + `jupyter lite build`), ×2 (warning fix, then release wiring) | both exit 0, no errors, each time |
| `interactive/e2e-book/exercise-12-lite.spec.ts` + `launch-buttons.spec.ts` (real Chromium/Pyodide) | **17/17 passed**, 1.5 minutes |
| `scripts/classify_release_change.py` against this exact diff | **GATE: full** — exactly as expected (shared paths touched: `book/_toc.yml`, `book/_config.yml`, `book/config/exercise_manifest.json`, shared test/script files) |
| `tests/test_placeholder_exercises.py` + `test_wp25_content_audit.py` (the two files the first push's CI failure found) | **6/6 + 11/11 OK**, fixed |
| Complete offline suite, all of `tests/` (run once the gap above was found, before the corrective push) | **1318/1318 OK, 11 skipped, 0 failures/errors** |

Exercises 1–9's own offline/browser suites were not re-run as their own
separate local pass (per the WP's instruction not to repeat checks on
unchanged notebooks) — but the complete offline suite above does include
every exercise's own offline test file, and CI's own full-gate run (which
the classifier correctly selected) exercised the complete browser suite,
including `warning-sweep.spec.ts`, for all of 1–9 and 12.

## Live verification

All checked directly against `https://yoavmp.github.io/ml-neuro-tutorials/`
after CI run `38636765295` deployed (confirmed via the `gh-pages` branch's
own marker commit, `deploy: d3a9f71...`, matching the pushed commit exactly
— not merely trusting the workflow's "success" status):

- **Contents page** links to all three new entries, in order:
  `chapters/chapter_10/placeholder.html`, `chapters/chapter_11/exercise_11.html`,
  `chapters/chapter_12/exercise_12.html`.
- **Exercise 10 placeholder title**: `<h1>Exercise 10: Deep Learning</h1>` — confirmed.
- **Exercise 11 placeholder title**: `<h1>Exercise 11: Embeddings and RSA</h1>` — confirmed.
- **Exercise 12 page**: `<h1>Exercise 12: Common Mistakes and Pitfalls</h1>`,
  linking to `../../lite/notebooks/index.html?path=exercise_12.ipynb` and
  `../../lite/files/exercise_12_portable.ipynb` — confirmed.
- **Legacy Exercise 10 notebook not exposed**: `chapters/chapter_10/exercise_10.html`
  returns **404** — confirmed.
- **Exercise 12 opens and downloads**, in a real browser (Chromium via
  Playwright, against the live URL, not the local build): loaded, ran
  every cell to completion, and **Download my notebook** produced a file
  named `exercise_12.ipynb`.
- **The warning is absent in the live Case 1 cell**: scrolled directly to
  the KNN comparison cell on the live site and read its actual output
  area — exactly one output div (`application/vnd.jupyter.stdout`), no
  `stderr` div, text matching the expected comparison results exactly:
  ```
  full split (n_train=602, n_val=201): leaky val MSE=32.715  honest val MSE=32.390  (leaky worse by 0.324)
  n=100 (n_train=75, n_val=25): leaky val MSE=60.014  honest val MSE=60.911  (leaky better by 0.897)
  n=60 (n_train=45, n_val=15): leaky val MSE=10.334  honest val MSE=10.630  (leaky better by 0.296)
  ```

## Real-Colab status

**Still UNVERIFIED.** This session has no real Google Colab access. A
teacher-filled reference copy, a student-unfilled portable copy, and a
filled `COLAB_CHECKLIST.md` (now updated with this release's final Case 1
KNN numbers and the resolved warning) were prepared in this session's own
scratch directory during WP57R, not committed, for the author's own later
real-Colab run. Nothing about this release changes that status — it is
reported honestly as still unverified, not assumed to have passed because
the local/simulated and real-browser checks above did.

## Branch and final git state

- `feature/wp57-active-exercise-12-common-mistakes`: all work merged into
  `main`; left in place (not deleted).
- `main`: `d3a9f71`, pushed to `origin/main` (two pushes total — see "The
  CI failure and its fix" above for why the second was needed).
- `origin/gh-pages`: `9fd4c1b` (`deploy: d3a9f71...`), matching.
- Working tree: clean.
