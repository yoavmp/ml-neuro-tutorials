# WP43R report: fix clean-CI dependency and finish JupyterLite deployment

## Success or failure

**Partial progress, still blocked — not deployed.** The `ipywidgets`
dependency gap WP43 identified is fixed and proven: reproduced in a
genuinely fresh Python 3.11.16 environment, fixed, re-verified in that same
fresh environment, and then **confirmed working in real CI** — the
"Unit-test the Python scripts (offline)" step, the Jupyter Book build, and
the JupyterLite build all passed on the triggered run, which they did not
in WP43. The run still failed, at the following step
("End-to-end test the combined book + JupyterLite build"), on a single
Playwright test timeout unrelated to the dependency fix. Per this WP's Gate
C, no retry and no second push were made. **The production site remains
completely unaffected**: `gh-pages` is unchanged and still serves the
pre-WP41 content.

## Branches and SHAs

- Start (local `main`, == `origin/main` after WP43's push):
  `e76c690ff39d5705f7396e240d77ec019d18a630`.
- `origin/main` at entry (verified via fetch, matched the WP's reported
  state exactly): `7d0f9d3c4a9cdaab1fba8041632c817d195ca05f`.
- `gh-pages` at entry (verified): `f6ddfc28e5102d44f94dc5dc86ba9875ad36db8a`
  (`deploy: 58ed1c6…`) — the pre-WP41 production state.
- Checkpoint refs created (local only, not pushed):
  `refs/checkpoints/wp43r-pre-work-main` (`e76c690…`),
  `refs/checkpoints/wp43r-production-pre-fix` (`f6ddfc2…`).
- Fix commit: `89c9bccab37c1ab295f16ef55251d4c90a04a0cf` — "WP43R Gate A/B:
  pin ipywidgets in requirements.txt for clean CI" (includes this WP's own
  spec file, and the previously-unpushed WP43 report commit `e76c690`,
  carried forward cleanly since ancestry was linear).
- Pushed once: `7d0f9d3..89c9bcc main -> main`.
- **`origin/main` now**: `89c9bccab37c1ab295f16ef55251d4c90a04a0cf`.
- **`gh-pages` now**: unchanged —
  `f6ddfc28e5102d44f94dc5dc86ba9875ad36db8a` (`deploy: 58ed1c6…`). The
  publish step never ran (see below).

## Gate A — preflight (summary)

Re-verified every historical observation the WP text asserted, rather than
assuming it still held: `origin/main` at `7d0f9d3`, `gh-pages` at
`f6ddfc2` (`deploy: 58ed1c6`), local `main` one commit ahead
(the unpushed WP43 report commit, content confirmed via `git show --stat`),
`Homework_Materials/` excluded via `.git/info/exclude` and untracked, no
active/queued workflow runs, most recent run the WP43 failure
(`36410198395`, failed at the Python unit-test step). All matched exactly;
no unexplained changes, no divergence, nothing to stop for.

## Dependency diagnosis

`requirements.txt` covers the Jupyter Book build and already carries the
standard Jupyter runtime stack (`jupyterlab`, `ipykernel`, `numpy`,
`pandas`, `matplotlib`, `seaborn`, `scikit-learn`) — the natural home for
`ipywidgets`, not `requirements-lite.txt` (scoped explicitly, by its own
header comment, to `jupyterlite-core`/`jupyterlite-pyodide-kernel` build
tooling). Both migrated notebooks' setup cells already guard their
`micropip.install(["ipywidgets"])` call with `if sys.platform ==
"emscripten":` — confirmed unchanged and untouched by this fix; the
JupyterLite browser install path is independent of this pip package
entirely.

## Gate B — reproduced and fixed in a genuinely fresh environment

The project's long-lived `.venv` was **not** used to validate this fix
(it already had `ipywidgets` installed from earlier development, which is
exactly what masked the gap in WP43). Instead:

1. Installed Python 3.11.16 via Homebrew (CI pins `python-version: "3.11"`;
   this machine had no 3.11 installed before this WP).
2. Created a brand-new virtualenv (`python3.11 -m venv`), installed
   **only** `pip install -r requirements.txt -r requirements-lite.txt` —
   the exact command the workflow runs.
3. **Reproduced the exact failure first**: `python -m unittest
   tests.test_exercise_01_reference_execution` raised the identical
   `ModuleNotFoundError: No module named 'ipywidgets'` in this fresh
   environment, confirming the diagnosis before touching anything.
4. Added `ipywidgets==8.1.9` to `requirements.txt` (the version already
   present in the dev `.venv`, and independently confirmed as both PyPI's
   current latest release and clean under `pip check` against this
   environment's resolved `jupyterlab==4.6.4` / `ipykernel==7.3.0` — no
   forced downgrade or conflict).
5. Re-installed in the same fresh venv; `pip check`: no broken
   requirements.
6. Full offline suite in that fresh venv: **1086 tests, 0 failures, 11
   skipped** (network-only, expected offline) — including both exercises'
   reference-execution numeric-integrity suites, run explicitly:
   `test_exercise_01_reference_execution` (6/6, including
   `test_curated_table_shape` — the 1114×13 table) and
   `test_exercise_02_reference_execution` (10/10, including the established
   linear-regression and KNN k=20 numbers).
7. Generator/data/portable-notebook `--check` gates: all up to date, same
   fresh venv.
8. Rebuilt from scratch in the same fresh venv, to rule out any
   dependency-change side effect on the JupyterLite step: the
   course-toolbar extension (`npx tsc` + `jupyter labextension build`),
   `jupyter-book build book` (0 execution-error logs), and `jupyter lite
   build … --output-dir book/_build/html/lite`. All three succeeded
   unchanged; both trees (`chapters/…`, `lite/notebooks/…`) confirmed
   present in the same combined output directory.
9. Did **not** re-run WP43's already-clean 149-test Playwright suite
   locally — this change is a server-side pip dependency with no effect on
   JupyterLite's browser-side `micropip` install path, per the WP's own
   instruction to skip an unchanged full browser suite when a correction
   doesn't touch browser packaging.

## Gate C — the one controlled recovery push and its result

Re-checked `origin/main` and active-run state immediately before pushing
(both unchanged). Committed the fix (`89c9bcc`), pushed once:
`7d0f9d3..89c9bcc main -> main`.

Triggered run:
[`36414417778`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/36414417778),
head SHA `89c9bccab37c1ab295f16ef55251d4c90a04a0cf`. Watched without rapid
polling (30-second interval checks). **Result: failure**, job duration
29m2s — inside the ~35-minute bound.

### What passed (the dependency fix is proven)

Every step through **"Build JupyterLite (Exercises 1 and 2)"** succeeded,
including the two that failed the underlying dependency check in WP43:

- ✓ Install and build the course-toolbar JupyterLite extension
- ✓ **Unit-test the Python scripts (offline)** — the step that failed in
  WP43 with `ModuleNotFoundError: No module named 'ipywidgets'` now passes.
- ✓ Build Jupyter Book
- ✓ Fail on notebook execution errors (0 error logs)
- ✓ Build JupyterLite (Exercises 1 and 2)

### What failed

**"End-to-end test the combined book + JupyterLite build"**: **148 of 149
Playwright tests passed**; 1 failed:

```
[chromium] › e2e-book/exercise-02-lite.spec.ts:110:3 ›
  Exercise 2 — JupyterLite notebook › Section 8 slider is operable and
  updates the figure

Error: expect(locator).toBeVisible() failed
Locator:  locator('.widget-slider .noUi-handle').first()
Expected: visible
Received: <element(s) not found>
Timeout:  5000ms
  at interactive/e2e-book/exercise-02-lite.spec.ts:125:26
```

This is a single-test timeout waiting for a slider handle to render, in a
notebook and spec file **this WP did not modify at all** (WP43R's only
change was `requirements.txt`). It has the same signature as flakiness
WP42's own report already documented under this exact suite's 6-worker
parallel-load contention on CI-class hardware ("a separate, earlier
6-worker run had 2 unrelated flaky failures from parallel-load contention
… both passed individually and in the final clean full-suite run; not a
real regression"). This WP's own Gate C local validation used the same
unmodified spec file and passed 149/149 on WP43's prior run. This is
plausible, not confirmed, flakiness — no retry was performed to confirm it,
per this WP's explicit instruction not to rerun the failed workflow or push
an additional fix.

### Production state after this run

- `gh-pages`: **unchanged**, still `f6ddfc28e5102d44f94dc5dc86ba9875ad36db8a`
  (`deploy: 58ed1c6…`) — the "Publish website" step never ran (it sits
  after the failed step in the job).
- Live checks: hub `200` (unchanged pre-WP41 content),
  `lite/notebooks/index.html` still `404`.
- **No partial or broken deployment. Production is exactly as it was
  before this WP.**

## What was not done, per the WP's explicit instruction

No workflow rerun, no second push, no speculative fix for the Playwright
timeout. Live-site verification (Contents → Exercise 1/2, direct Lite URLs,
kernel start, widgets, download, Colab instructions, legacy exercise,
mobile width) was **not performed**, because nothing new reached
production — there is nothing to verify live yet.

## Current state and concrete next step for the course author

- `origin/main` is now `89c9bcc` (all of WP41/41R/42/43/43R). Pages has
  **still not republished** — the live site is untouched.
- The dependency blocker from WP43 is resolved and proven in both a fresh
  local environment and real CI.
- The remaining blocker is a single Playwright test
  (`exercise-02-lite.spec.ts:110`, "Section 8 slider is operable and
  updates the figure") that timed out once under CI's 6-worker parallel
  load, on content unchanged by this WP and previously green. The
  recommended next step is a fresh workflow run (not a code change) to
  determine whether this reproduces — if it does not, this was CI-resource
  contention exactly as WP42 previously observed; if it reproduces
  consistently, it needs its own focused investigation. That decision
  and any rerun are for the next authorized WP, not this one.

## Deviations from the WP text

None of substance. `WPs/reports/WP43R_REPORT.md` and
`WPs/reports/WP43R_EXACT_CHANGELOG.md` are committed locally on `main`
after the push above but are **not pushed** in this WP, to avoid
triggering a third `Build and deploy Jupyter Book` run.
