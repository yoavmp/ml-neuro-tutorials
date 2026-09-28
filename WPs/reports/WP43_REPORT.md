# WP43 report: deploy JupyterLite Exercises 1 and 2

## Success or failure

**Blocked in Gate D, not deployed.** Gates A–C all passed, including a full
local combined build and a clean 149/149 real-browser Playwright run. The
WP41/WP41R/WP42 feature history plus this WP's own pipeline-wiring commits
were integrated into local `main` and pushed to `origin/main` once, as
instructed. The GitHub Actions run that push triggered **failed** at the
"Unit-test the Python scripts (offline)" step, before the Jupyter Book
build, the JupyterLite build, or the Pages publish step ever ran. Per the
WP's own Gate D instruction, no speculative fix was pushed and no second
deployment was triggered. **The production site is unaffected**: `gh-pages`
is unchanged and still serves the pre-WP41 content for the hub, Exercise 1,
and Exercise 2.

## Branches and SHAs

- Starting branch: `feature/wp42-exercise2-polish-exercise1-migration` at
  `383249a302e6c6b78ab92ae36e818ae2f2257e03`.
- Local `main` at entry: `24a1bd99e697acb8c0ec8355efb43bc485c6ffd2` — already
  one commit ahead of `origin/main` (an unpushed "WP39: reports" commit,
  pre-existing before this WP; not something this WP created).
- `origin/main` at entry (== the live pre-WP41 production SHA, confirmed via
  the `gh-pages` branch's own `deploy: <sha>` commit message):
  `58ed1c61f43f0b3c6d23c1f32212bf2d3b9c9f0b` ("Merge Exercise 10 course
  materials").
- Ancestry was fully linear and conflict-free: `origin/main` ⊂ local `main`
  ⊂ the WP41/41R/42 feature branch ⊂ this WP's deployment-preparation
  branch. No rebase, reset, or force-push was needed or used.
- Deployment-preparation branch: `prep/wp43-deploy-jupyterlite-exercises`,
  cut from the feature branch tip.
  - `b6a8ed0` — Gate B: wire JupyterLite build into the Pages deploy
    workflow.
  - `7d0f9d3c4a9cdaab1fba8041632c817d195ca05f` — Gate C: fix the
    course-toolbar build step (found live during local validation, not
    assumed). Final prep-branch SHA.
- Local checkpoint refs (not pushed): `refs/checkpoints/wp43-pre-work-main`
  (`24a1bd9…`), `refs/checkpoints/wp43-pre-work-feature` (`383249a…`),
  `refs/checkpoints/wp43-production-pre-wp41` (`58ed1c6…`).
- **Integration**: local `main` was fast-forwarded (no merge commit) to the
  prep branch tip, then pushed once: `58ed1c6..7d0f9d3 main -> main`. This
  is the one production push the WP authorizes.
- **`origin/main` now**: `7d0f9d3c4a9cdaab1fba8041632c817d195ca05f`.
- **`gh-pages` (the actually-live site) is still**:
  `f6ddfc28e5102d44f94dc5dc86ba9875ad36db8a` (`deploy: 58ed1c6…`) —
  unchanged by this WP, since the workflow failed before the publish step.

## Gate A — preflight (summary)

- Confirmed no deployment was running and the most recent prior run
  (`36027222613`, the WP39 deploy) completed successfully in 18m55s.
- GitHub Pages config: `build_type: "legacy"`, source `gh-pages` branch —
  the existing `peaceiris/actions-gh-pages` push-to-branch flow, not the
  native Pages-artifact flow. No missing secret or permission (the existing
  `GITHUB_TOKEN` with `contents: write` had already deployed successfully
  many times).
- `Homework_Materials/` is excluded via `.git/info/exclude` (a local,
  non-committed exclusion, not `.gitignore`), confirmed untracked and
  ignored; not read, staged, or uploaded.
- Baseline production behavior recorded (all via read-only HTTP checks):
  hub `200` (redirects to `intro.html`), `chapters/chapter_01/exercise_01.html`
  `200` (old static content, no JupyterLite reference), `chapters/chapter_02/exercise_02.html`
  `200` (same), `chapters/chapter_03/exercise_03.html` `200` (legacy,
  unaffected baseline), `lite/notebooks/index.html` `404` (the JupyterLite
  tree did not exist in production before this WP, as expected — WP41's own
  report flagged wiring it into CI as out of scope).

## Gate B — workflow changes

Edited `.github/workflows/deploy.yml` only (see the exact changelog for the
full diff). In order of insertion:

1. `pip install -r requirements.txt -r requirements-lite.txt` (was
   `requirements.txt` alone).
2. New step **Install and build the course-toolbar JupyterLite extension**
   (`book/lite/extensions/course-toolbar`): `npm ci`, then `npx tsc` and
   `jupyter labextension build --development True .` directly — see
   "Gate C: a real bug found and fixed" below for why not `npm run build`.
3. New step **Validate the JupyterLite exercise data exports (offline)**:
   `export_abide_lite_data.py --check`, `export_abide_phenotypes_lite_data.py
   --check`.
4. New step **Check the migrated exercise generators are not stale
   (offline)**: `--check` for both notebook generators and both transition-
   page generators.
5. New step **Build JupyterLite (Exercises 1 and 2)**: `jupyter lite build
   --config book/lite/jupyter_lite_config.json --lite-dir book/lite
   --output-dir book/_build/html/lite`, inserted after "Build Jupyter Book"
   and "Fail on notebook execution errors", before the book's end-to-end
   test step.
6. Renamed "End-to-end test the built Chapter 1 page" to "End-to-end test
   the combined book + JupyterLite build" — the command (`npm run
   test:e2e:book`) is unchanged, but it now also runs
   `exercise-01-lite.spec.ts` and `exercise-02-lite.spec.ts` (already present
   in `interactive/e2e-book/` since WP42) against a real JupyterLite build
   for the first time in CI, because that build now exists by this point in
   the job.

`publish_dir: ./book/_build/html` is unchanged — once the JupyterLite build
step runs before it, that directory is already the single combined
Book+Lite tree, satisfying "one combined Pages artifact" without a second,
divergent build recipe. Triggers and permissions were not touched.
`scripts/smoke_portable_notebook.py` needed no change: chapters 1 and 2 were
already excluded from its registry by WP42 (their `ipywidgets.Output()`
widgets hang a real, frontend-less `nbclient` kernel — a pre-existing,
documented gap, not something this WP introduced).

## Gate C — local validation

All performed from a clean `rm -rf book/_build` using the repo's pinned
`.venv`:

- `export_abide_lite_data.py --check`, `export_abide_phenotypes_lite_data.py
  --check` — both OK.
- `generate_exercise_01_notebook.py --check`, `generate_exercise_02_notebook.py
  --check`, `generate_exercise_01_transition_page.py --check`,
  `generate_exercise_02_transition_page.py --check` — all up to date.
- `python -m unittest discover -s tests` — **1086 tests, 0 failures, 11
  skipped** (network-only, expected offline). This passed locally but, as
  Gate D's failure shows, was not actually representative of a clean CI
  checkout — see "Root cause" below.
- `build_portable_notebook.py --check` — up to date for chapters 3–10.
- `jupyter-book build book` — succeeded, 2 pre-existing warnings (same ones
  WP41's report already recorded as unrelated), 0 notebook execution-error
  logs.
- `jupyter lite build --config book/lite/jupyter_lite_config.json --lite-dir
  book/lite --output-dir book/_build/html/lite` — succeeded; both trees
  (`chapters/…`, `lite/notebooks/…`) confirmed present side by side in the
  same output directory.

### A real bug found and fixed (not assumed)

The obvious CI recipe — `npm ci` then `npm run build` in
`book/lite/extensions/course-toolbar` — **fails** in a clean checkout:

```
Internal Error: course-toolbar@workspace:.: This package doesn't seem to be
present in your lockfile; run "yarn install" to update the lockfile
```

`npm run build` delegates to `jlpm run build:labextension:dev`, and
`jupyter labextension build`'s own bundled Yarn expects a Yarn-managed
dependency tree, not one `npm ci` just populated from `package-lock.json`.
Fixed by using the exact recipe the WP41 maintainer guide (section 6)
already documents: `npm ci` for dependency install, then `npx tsc` and
`jupyter labextension build --development True .` directly, bypassing
`jlpm`'s package-manager mismatch entirely. Verified locally: a clean
rebuild from a fresh `book/_build/` succeeds and produces
`course_toolbar/labextension/`.

### Real-browser validation (Playwright, real headless Chromium)

`npm run test:e2e:book` against the actual combined build, served by the
repo's own `serve-book.mjs` under **both** bare `localhost:4174/…` and the
Pages-style `localhost:4174/ml-neuro-tutorials/…` prefix from the same
running server:

**149/149 passed, 0 failed (7.9 minutes), one clean run.** This includes:

- `exercise-01-lite.spec.ts` (8/8) and `exercise-02-lite.spec.ts` (9/9):
  kernel start, same-origin data load, supplied-cell execution reproducing
  the established numeric results (Exercise 1's `(1114, 13)` table;
  Exercise 2's R²/MSE values), one native widget operable per notebook
  (the retention explorer / Section 8's k-slider), one checked question
  graded correctly per notebook, a written-answer edit surviving save →
  reload → **Download my notebook** with the edit present in the downloaded
  bytes, Reset-restores-template + Back-to-Contents (with the Reset
  confirmation dialog), and zero horizontal overflow at 390px.
- `chapter01.spec.ts` and `launch-buttons.spec.ts`: clicking "Open Exercise
  1"/"Open Exercise 2" on the transition page **served under the real
  `/ml-neuro-tutorials/` subpath** actually opens the JupyterLite working
  copy — the Pages-prefix check the WP requires.
- `wp22-cross-chapter-dark-mode.spec.ts`: dark-mode legibility, including
  Exercise 2's Section 8 figure.
- `chapter03.spec.ts`–`chapter10.spec.ts` and
  `iframe-height-contract.spec.ts`: every legacy (unmigrated) exercise's
  embedded activities and iframes still work, confirming the hub and legacy
  content are intact alongside the new JupyterLite trees.

`npm run typecheck` (interactive/): clean.

## Integration

Re-checked `origin/main` and active-run state immediately before merging
(both unchanged from Gate A's baseline). Fast-forwarded local `main` to the
prep branch tip (`7d0f9d3`) — a clean fast-forward, no merge commit, no
conflicts, 85 files changed (27,479 insertions, 9,312 deletions) relative to
the pre-WP41 `origin/main`. Pushed once: `58ed1c6..7d0f9d3 main -> main`.

## Gate D — deployment and its failure

- Triggered run:
  [`36410198395`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/36410198395),
  head SHA `7d0f9d3c4a9cdaab1fba8041632c817d195ca05f`.
- **Result: failure**, at the **"Unit-test the Python scripts (offline)"**
  step, after 1m41s — well inside the ~35-minute bounded window (it failed
  fast; the Jupyter Book build, JupyterLite build, and Pages publish steps
  never ran).

### Root cause

```
ModuleNotFoundError: No module named 'ipywidgets'
```

raised inside `tests/test_exercise_01_reference_execution.py` and
`tests/test_exercise_02_reference_execution.py`'s `setUpClass`, which
execute the reference notebooks' **actual cell source** directly (the
maintainer guide's own documented numeric-integrity-test pattern, chosen
specifically because `nbclient`/`jupyter execute` hangs on these notebooks'
`ipywidgets.Output()` cells — see maintainer guide section 8). Both
notebooks' setup cells `micropip`-install `ipywidgets` **only** when
`sys.platform == "emscripten"` (i.e., inside the real Pyodide browser
kernel), by design — so that a full local Jupyter/Colab environment, which
the maintainer guide assumes "already has it installed," does not
redundantly re-fetch it. A bare CI `pip install -r requirements.txt`
interpreter is neither the browser kernel nor a full local Jupyter
environment: it has no `ipywidgets`, the setup cell's platform guard
correctly skips installing it there too (it is not Pyodide), and the
subsequent `import ipywidgets` inside the executed cell throws.

This is a **pre-existing gap in `requirements.txt`** — `ipywidgets` was
never added there — invisible in every prior local run (including this WP's
own Gate C validation above) because the developer's `.venv` already has
`ipywidgets==8.1.9` installed from earlier WP41/42 work, masking exactly the
condition a genuinely clean checkout hits. `requirements.txt` was not
modified by this WP (Gate B's scope was the build/test wiring, not this
existing test's dependency contract), so this gap predates WP43 and was
first surfaced, not created, by wiring these tests into a clean-CI run for
the first time.

### What was not done, per the WP's explicit instruction

No fix was pushed and no second deployment was triggered. `gh-pages` is
confirmed unchanged (`f6ddfc28e5102d44f94dc5dc86ba9875ad36db8a`, still
`deploy: 58ed1c6…`); the production hub, Exercise 1, Exercise 2, and
Exercise 3 all still return their pre-WP41 content, and
`lite/notebooks/index.html` is still `404`. **The production site is
completely unaffected by this WP** — there is no partial or broken
deployment.

## Current state for the course author

- `origin/main` now contains all of WP41/WP41R/WP42/WP43's work
  (`7d0f9d3`), but **Pages has not republished from it** — anyone reading
  the GitHub repository sees the migrated Exercises 1/2, but the live site
  still serves the old static versions. This is an expected, safe
  intermediate state (main ahead of what Pages has published), not a
  deployment in progress.
- **Concrete blocker**: add `ipywidgets` to `requirements.txt` (the local
  `.venv` currently has `8.1.9`; pin to match whatever version the course
  author wants CI to install) so the offline reference-execution tests can
  `import ipywidgets` outside the browser kernel. This is the only known
  blocker — every other Gate A–C check passed, including the full
  real-browser Playwright suite against the actual combined build. Once
  fixed, re-running Gate C's `python -m unittest discover -s tests` in a
  **genuinely fresh virtualenv** (not a long-lived dev `.venv`) before the
  next push would have caught this before it reached CI.
- No other WP was started. No content beyond the deploy workflow was
  changed by this WP (the course-toolbar build-step fix is pipeline-only).

## Deviations from the WP text

1. Gate D's failure means live verification (hub/Exercise 1/Exercise
   2/direct JupyterLite URLs/download/Colab/legacy-exercise/mobile/dark-mode
   checks against production) **could not be performed** — there is nothing
   new to verify live; the production site is provably unchanged (see
   above). This is not a limitation in observation; it is the correct,
   literal state.
2. This report and the exact changelog are being written to the working
   tree and will be committed locally on `main` but **not pushed** in this
   WP, since pushing would trigger another `Build and deploy Jupyter Book`
   run — exactly the "another deployment" Gate D forbids. They will reach
   `origin/main` whenever the `ipywidgets` fix (or any other change) is
   pushed next.
