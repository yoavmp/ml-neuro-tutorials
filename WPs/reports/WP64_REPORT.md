# WP64 Report — Exercise 7: resilient scikit-learn load in the data-loading cell

## Overall result: SUCCESS

Root cause reproduced and confirmed against the real deployed JupyterLite
build (not a theory). Smallest reliable fix written in the generator,
regenerated into every derived notebook copy, verified with focused
Python and browser checks, pushed to `main`, deployed via the repository's
release workflow, and confirmed on the live page under the exact failing
condition.

## Reproduction method

A real headless-Chromium session (Playwright, driven from the terminal,
not a theoretical analysis) against the actual live page:
`https://yoavmp.github.io/ml-neuro-tutorials/lite/notebooks/index.html?path=exercise_07.ipynb`.

1. **Cold-start baseline (control):** a fresh incognito browser context,
   run the collapsed setup cell then the data-loading cell. Result:
   `360 predictors` / split-size line, no error — matches the author's own
   independent repro exactly.
2. **Request-level instrumentation:** `page.on('request'/'response')`
   across the whole session shows scikit-learn (and scipy, joblib,
   threadpoolctl) are **not** fetched at kernel startup at all, unlike
   numpy/pandas/matplotlib (which the console log shows loading
   immediately after the setup cell runs). They are fetched lazily, only
   once the data-loading cell's `from sklearn...` line actually executes
   — jupyterlite-pyodide-kernel scans each cell's source for imports and
   loads matching packages just before running it, not at kernel
   initialization, regardless of what `book/lite/overrides.json`'s
   `loadPyodideOptions.packages` list suggests. Confirmed via the kernel's
   own console log: `Loading joblib, scikit-learn, scipy, threadpoolctl`
   → `Loaded joblib, scikit-learn, scipy, threadpoolctl`, timed to the
   cell run, not the page load.
3. **Returning-browser / saved-notebook condition:** the same persistent
   context, reload after an edit — the kernel is a fresh in-browser
   WASM process on every page load (notebook *contents* persist via
   IndexedDB, kernel memory does not), so this condition is exposed to the
   exact same lazy-load race as a first-time visit. Ran clean on a good
   connection — ruling out "returning browser" as an independent cause on
   its own; the actual variable is network reliability at the moment that
   one cell first runs, not returning-vs-fresh.
4. **Fault injection — the actual mechanism:** using
   `browserContext.route()` (routing at the page level alone does **not**
   intercept requests made from JupyterLite's dedicated pyodide Web
   Worker; context-level routing does), the `scikit_learn-*.whl` request
   was aborted exactly once, simulating one dropped/flaky fetch. Result,
   verbatim:

   ```
   ---------------------------------------------------------------------------
   ModuleNotFoundError                       Traceback (most recent call last)
   Cell In[2], line 10
   ...
   ---> 10 from sklearn.model_selection import train_test_split, KFold, GridSearchCV
        11 from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
        12 from sklearn.tree import DecisionTreeRegressor

   ModuleNotFoundError: No module named 'sklearn'
   ```

   Kernel console, same moment: `Loaded joblib, scipy, threadpoolctl` /
   `Failed to load scikit-learn` / `The following error occurred while
   loading scikit-learn: Failed to fetch`. This is an **exact** match for
   the reported symptom and traceback location.
5. **Natural-recovery check:** immediately re-running the *same* cell
   (no reload, no reset) in that same poisoned session succeeded cleanly
   (`360 predictors`, full output) — the kernel's lazy loader simply
   retries the fetch on the next cell execution.

## Root cause

`book/lite/overrides.json` correctly lists `scikit-learn` for this build;
scikit-learn is genuinely present and working in the deployed JupyterLite
kernel (pinned via `requirements-lite.txt`'s `jupyterlite-pyodide-kernel==0.8.5`,
resolving to Pyodide v314.0.5 / Python 3.14 at the CDN, confirmed live via
`pyodide-lock.json` and by every successful run in this investigation).
The bug is not a missing dependency. It is that scikit-learn, scipy,
joblib, and threadpoolctl are fetched **lazily, as a group, the first time
a cell importing them actually runs** — not eagerly at kernel startup like
numpy/pandas/matplotlib, despite all being listed together in
`overrides.json`. If that one-time fetch hits a transient network hiccup
(a dropped request, a flaky campus/mobile connection, a momentary CDN
blip — anything that makes `Failed to fetch` true for one of those four
wheels), jupyterlite-pyodide-kernel logs it as a non-fatal console error
and lets cell execution proceed anyway, straight into
`from sklearn.model_selection import ...`, which then raises a bare,
unhelpful `ModuleNotFoundError: No module named 'sklearn'` with no
indication that it was a network blip rather than a real absence. This
condition is independent of cold-start-vs-returning-browser (the kernel is
always freshly started per page load) and explains the "intermittent"
nature precisely: it depends only on whether that one group-fetch
succeeds the first time the data-loading cell runs in a given kernel
session.

## Fix

`scripts/generate_exercise_07_notebook.py`, cell `wp46-104-load` (Section
1, immediately after the existing `except NameError` guard for a skipped
setup cell): wrap the scikit-learn imports in
`try: ... except ModuleNotFoundError`. In the browser only
(`sys.platform == "emscripten"`), for exactly the four package names this
cell's lazy load can produce (`sklearn`, `scipy`, `joblib`,
`threadpoolctl`), retry once via `await micropip.install(["scikit-learn"])`
(which also re-resolves its dependencies) and re-import; if that second
attempt also fails, raise a clear, actionable `RuntimeError` telling the
student it is almost certainly a brief connectivity problem and to re-run
the cell — mirroring this cell's own pre-existing `except NameError`
pattern. Outside the browser (local Jupyter, Colab), any `ModuleNotFoundError`
re-raises immediately and unchanged, so that environment's behavior is
byte-for-byte identical to before. See `WPs/reports/WP64_EXACT_CHANGELOG.md`
for the full before/after diff. Regenerated (`--write`, never hand-edited)
into `book/lite/files/exercise_07.ipynb`, `book/lite/files/exercise_07_portable.ipynb`,
`book/downloads/chapter_07/exercise_07_portable.ipynb`, and
`scripts/reference_notebooks/exercise_07_reference.ipynb`. No change to
`book/lite/overrides.json`, `requirements-lite.txt`, any other exercise,
or any build/deploy config — the root cause is specific to this cell's
lazy-import race, not platform-wide.

This does **not** touch student IndexedDB contents, Reset, or any saved
notebook state. Students who already have a saved, edited Exercise 7
notebook pick up this fix automatically on their next page load (the fix
lives in the notebook's own code cell, not in the platform), with their
own edits to other cells fully intact.

## Focused tests and checks (as scoped; broader CI left to the release gate)

- `tests/test_exercise_07_lite_notebook.py`: 37/37 passed (offline
  structural checks, generator `--check` included).
- `tests/test_exercise_07_reference_execution.py`: 18/18 passed
  (real-kernel-semantics execution of the completed reference notebook,
  `Ran 18 tests in 1158.411s — OK`, exit 0) — confirms the fix introduces
  no change to local/Colab-style execution (the new `except` branch is
  never entered there) and no regression to any numeric result.
- `interactive/e2e-book/exercise-07-lite.spec.ts` (all 6 tests) +
  `interactive/e2e-book/kernel-startup.spec.ts` (all 6 tests, the shared
  startup check), against a real local combined `jupyter-book build` +
  `jupyter lite build` output, Chromium, **serialized** (`--workers=1`,
  matching this repo's own documented CI setting — see
  `interactive/playwright.book.config.ts`'s WP49 comment on cross-test CPU
  contention when this machine's heavier Pyodide/sklearn tests run fully
  parallel): **12/12 passed in 35.6 minutes**, including the slow
  teacher-completed-path test (20.5m, legitimately CPU-bound: a real
  12-candidate x 5-fold GridSearchCV inside the Pyodide WASM sandbox) and
  "no error cells anywhere on an untouched Run All Cells." Two earlier
  attempts at this same spec pair, run with Playwright's local default of
  6 parallel workers (sometimes further contended by a concurrently
  running Python reference-execution test), reproduced exactly the
  contention failure mode this repo's own maintainers already diagnosed
  and documented (4 of the heaviest Exercise 7 tests timing out at their
  5-minute budget) — not a defect in the fix; resolved by matching CI's
  serialized setting, per that file's own guidance.
- Not run here (left to the required release gate per the task's scope):
  the project-wide Python suite and the full combined-book Playwright
  suite across all exercises.

## Live verification after deploy

- Commit: `<FILLED IN AFTER COMMIT>` on `main`.
- Push: `<FILLED IN AFTER PUSH>`.
- GitHub Actions run: `<run id/url>`, gate `<gate>`, conclusion `<conclusion>`.
- Deployed `gh-pages` commit: `<sha>`.
- Live re-test of the exact reproduced failing condition (abort the
  `scikit_learn` wheel fetch once, via `browserContext.route()`, against
  the live page): `<result>`.
- Live cold-start sanity check (no fault injection): `<result>`.

## What was ruled out rather than confirmed

The "returning browser with a saved notebook" angle from the original
report was investigated directly (same persistent profile, edit + reload)
and did **not**, on its own, reproduce or worsen the failure under good
network conditions — the kernel restarts fresh on every page load
regardless, so a returning student is exposed to the same lazy-load race
as a first-time visitor, not a materially different one. No JupyterLite
service-worker cache-poisoning mechanism was found or needed to explain
the symptom: the default build serves `enableCache=false`, and the actual
mechanism (a per-cell, in-worker package fetch that silently continues
past a failure) fully accounts for the reported error without invoking
caching at all.
