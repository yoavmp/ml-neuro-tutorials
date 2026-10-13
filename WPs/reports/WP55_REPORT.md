# WP55 report: course-page edits, Exercise 1 correlations, kernel startup, and release

## Success or failure -- read this first

**Success.** Every numbered WP55 requirement (A-E) is applied and
verified. Item E (the intermittent JupyterLite "No Kernel" startup race)
started from a source-confirmed mechanism (live-browser diagnostics
against the deployed site -- 8 real attempts -- did not themselves catch
the stuck state, but reading the actual shipped `@jupyterlab/apputils`
`SessionContext` source located a real, confirmed race), and the first
implementation of its fix introduced its own real, *reproduced* defect --
caught by this repo's own full combined browser suite, root-caused via a
live A/B test against the completely unmodified extension, fixed, and the
fix itself reverified by the same method (3x repeated, isolated,
zero-failure). Both the original "No Kernel" race and this fix's own
regression are now addressed with evidence, not assumption, at every step.
The locally-committed, previously-unpushed persistent-job-policy commit is
preserved and rides along with this release exactly as WP55 authorized.

## Starting state and branch

Began at local `main` tip `b2f0350` ("docs: standing rule for long-running
local commands and CI watches") -- `main` was 1 commit ahead of
`origin/main` at that point (`5dfddcb` -> `b2f0350`), and that commit is
the one WP55 explicitly says to preserve and let ride along. Checkpoint
branch `checkpoint/wp55-pre-work` created at that exact tip before any
WP55 edit (per the repo's own pre-work-checkpoint convention, matching
`checkpoint/wp54-pre-work` etc.); work done on
`feature/wp55-small-fixes-kernel-and-release`. The WP spec itself was
moved from the repository root into `WPs/` (the convention every other WP
spec uses) and committed as
`WPs/WP55_SMALL_COURSE_FIXES_KERNEL_STARTUP_AND_RELEASE.md`.

## Acceptance table

### A. Syllabus: three concise copy changes

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Room set to Dan David building, room 110; old placeholder removed | Done | `book/syllabus.md`: `Mondays, 08:30-11:00, Dan David building, room 110`. |
| 2 | Week 9 homework renders `SVM` with no asterisk; "sum" footnote removed | Done | Row now reads `...KNN, Ridge, SVM`; the old footnote sentence is gone. |
| 3 | Intro disclaimer replaced with a neutral Contents link; no false publish claim | Done | `## Schedule` now opens with `Practice notebooks: see [Contents](contents.md).` Individual `*(tentative)*` markers on Weeks 4, 5, and 12 are untouched. |

### B. Resources: direct, student-facing descriptions

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Opening "practical link directory..." sentence removed, no replacement | Done | Page now opens directly with "For citable works, see [References](references.md)." |
| 2 | NeuroHackademy entry replaced with student-facing credit + exact destination | Done | `[NeuroHackademy 2020 machine-learning tutorial data](https://github.com/neurohackademy/nh2020-curriculum/tree/master/tu-machine-learning-yarkoni/data)` crediting [Prof. Tal Yarkoni](https://talyarkoni.org/)'s workshop at [NeuroHackademy](https://neurohackademy.org/) 2020. The pinned `raw.githubusercontent.com` URL every notebook loader actually falls back to is untouched in every generator -- this is a resource-page *display* change only, confirmed by grepping all 9 generators for that URL after the edit (still present, unchanged). |
| 3 | "curated exports..." paragraph replaced with the exact required sentence | Done | "subsets built from the ABIDE II source above, using the columns each exercise requires." The three same-origin CSV links are unchanged. |

### C. References: remove two bits of commentary

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | "This course's own text, used throughout..." sentence removed | Done | Citation 1 now ends at "Springer." |
| 2 | "Exercises 1-9 are built on" phrasing removed from citation 2 | Done | Now reads "The original publication for the ABIDE II dataset; see [Resources]...". Bibliography, all three DOIs, and citation order are unchanged. |

**Regression caught and fixed before any CI run:** three `tests/test_book_structure.py` assertions encoded the *pre-WP55* wording as required facts (`"location not provided"`, the literal `"Only Exercises 1-9 are published"` sentence, and the pinned `raw.githubusercontent.com` display URL). All three are intentionally gone after A/B above. Rewrote each to assert the new, intended content instead (new room string present and the old placeholder gone; the new Contents link present and no "Exercise 10/11/12" text; the new `github.com/neurohackademy/nh2020-curriculum` credit link present) -- caught by actually running the full suite once (see Verification), not by inspection alone.

### D. Exercise 1: an explained FIQ comparison and two correlation plots

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | FIQ-by-diagnosis question turned into a short, answered anecdote | Done | Bold prompt kept short; a plain-text answer follows directly below in the same cell (site/measurement-confound explanation, framed as a possibility, not a demonstrated cause -- matches the WP's own suggested example). **Not** implemented as a `<details>`/`<summary>` reveal -- see Deviations below for why. |
| 2 | New FIQ-vs-VIQ scatter activity: paired dropna, same-observations Pearson r, labeled axes/title | Done | New blank (`wp42-616-fiq-viq-blank`, tag `wp42-activity-fiq-viq-scatter`): student builds `paired = data[["FIQ","VIQ"]].dropna()`, computes `fiq_viq_r = paired["FIQ"].corr(paired["VIQ"])`, plots FIQ (x) vs VIQ (y) with both axes labeled and a title containing `n` and Pearson r. Hints are prose, not working code (see Deviations). A non-raising check cell recomputes the expected r independently from `data` and compares within tolerance; reports "not complete yet" rather than erroring when the blank is unfinished. |
| 3 | Portable reference image, real course data, both renderers | Done | `scripts/render_exercise_01_fiq_viq_reference_plot.py` computes the real value (`n=796, r=0.83`) from the committed `abide_phenotypes.csv`, offline, and saves `book/lite/files/data/exercise_01_fiq_viq_reference.png`. Embedded as a cell **attachment** (base64 inside the `.ipynb` JSON, same nbformat mechanism as Exercise 2's Activity 3B reference image) -- not a linked file, so it travels with a downloaded/Colab copy. Placed right before the blank ("For reference, here is the approved current result:"), matching the course's own established reference-image placement convention. |
| 4 | Ready-to-run 4-variable scatter matrix (AGE_AT_SCAN, FIQ, VIQ, PIQ) | Done | Supplied cell (`wp42-620-scatter-matrix`) uses `pandas.plotting.scatter_matrix` (no Seaborn), prints the complete-case sample size before plotting (`783 of 1114`), uses a separate `complete_for_matrix` dataframe so `data` itself is never modified, and runs independently of the student's blank above. |

**A fourth item inside D.2 the author explicitly flagged mid-session:**
the first draft of the student blank's hint comments gave the *exact*
working `paired = ...` / `fiq_viq_r = ...` lines verbatim -- a complete
solution for the correlation half of the task, not a hint. Rewritten to
prose hints only (mentioning `.dropna()` and `.corr()` by name, giving no
copy-pasteable line) before this was ever committed.

### E. Intermittent JupyterLite "No Kernel" picker

**Root cause, confirmed by reading the actual shipped library source (not
assumed):** `node_modules/@jupyterlab/apputils/lib/sessioncontext.js`'s
`SessionContext.startKernel()` reads `this.specsManager.specs`
*synchronously*, without awaiting `specsManager.ready` first, as soon as a
notebook's document context becomes ready. The Pyodide kernel's own
kernelspec is registered by a separate, lazily-loaded federated extension
chunk. If that chunk hasn't registered yet at the exact moment
`startKernel()` runs, `specs` is still `null`, no kernel name can be
picked, the function returns "needs selection" -- and **nothing ever
retries**: there is no listener on `specsManager.specsChanged` wired to
this path, so the session context's own `ready` promise never resolves
and the notebook is left on "No Kernel" permanently. A full reload only
"fixes" this because the browser's cache makes the second load's
federated-extension fetch fast enough to win the race -- not a real fix,
a favorable rerun, exactly matching the author's own description.

This compounds with a second, separate, **permanent** (non-racy)
mismatch, confirmed directly: every exercise notebook's own saved
kernelspec metadata asks for kernel name `"python3"`, but this
deployment's actual registered Pyodide kernel is named `"python"` (`book/
lite`'s built `jupyter-lite.json` -> `"defaultKernelName": "python"`).
Live-browser evidence against the deployed site: **8/8** attempts (6
fresh contexts, the site's launch-button route, a returning profile)
logged JupyterLab's own name-mismatch fallback notice in the browser
console on every single load -- though that fallback alone did not
produce a stuck "No Kernel" in any of those 8 runs; it recovered via the
language-based fallback every time. The live diagnostics are therefore
best read as: the permanent mismatch is real and fires on every load, but
8 attempts were not enough to also catch the separate, genuinely
intermittent registry race live.

**Fix implemented** in `book/lite/extensions/course-toolbar/src/index.ts`
(the one small extension this repo already ships and controls --
`@jupyterlab/apputils`/`@jupyterlab/services` themselves are third-party,
pip-installed, and out of this repo's control): a new
`ensureKernelStarted()`, called for every opened notebook right after the
existing `panel.context.ready` toolbar setup. If a kernel is already
running, it does nothing (the normal case). If not, it races
`sessionContext.ready` against a bounded timeout (30s) -- not to use the
result, but to distinguish "the automatic attempt is merely still
settling" from "it is genuinely stuck" without the indefinite hang
awaiting `ready` directly would risk in the stuck case (see below). Only
if still no kernel after that full window does it proceed: wait, bounded
again, for `app.serviceManager.kernelspecs.ready`, then explicitly start
the kernel by the registry's own `specs.default` name via
`sessionContext.changeKernel(...)`. If the registry never becomes ready
or `changeKernel` itself throws, a `showDialog` reports it plainly
instead of leaving an unexplained "No Kernel" or waiting indefinitely.
Not a sleep, not a page reload, not a cache purge.

**A real regression was caught and fixed before this ever reached a
commit the author would see as "done":** the first working version of
this fix checked only `session?.kernel` and, if absent, went straight to
its own recovery attempt -- reasoning (correctly) that `sessionContext.
ready` itself must never be awaited directly, since in the exact stuck
case being fixed that promise never resolves at all (confirmed by reading
`SessionContext.initialize()`: `_ready.resolve()` is only called when
`needsSelection` is `false`). That version passed its own new test file
and the first full combined-suite run looked clean at a glance -- but 3
of 129 tests failed with a previously-unseen console error,
`"<uuid> was disposed"`, in `exercise-01-lite.spec.ts` and
`exercise-02-lite.spec.ts`'s own strict zero-unexpected-console-errors
assertions (exercise-03's failure was an unrelated plain timeout). Rather
than wave this off as "probably CPU contention under 6-way parallelism"
(plausible, but not established), a direct A/B test resolved it
conclusively: the **exact same** `exercise-01-lite.spec.ts`, run serially
(`--workers=1`, zero contention) 3 times in a row against the
**completely original, unmodified** pre-WP55 `course-toolbar` extension,
passed **24/24 clean** -- proving the error was not pre-existing. The
same serial, 3x-repeated run against the first fix version reproduced the
identical `"<uuid> was disposed"` error even with zero contention,
confirming the fix itself was the proximate cause: reading
`SessionContext._changeKernel`'s source further, a session-start request
*can* be outstanding for a real amount of time before `session?.kernel`
becomes set -- so the first fix's bare `session?.kernel` check could
start a *second*, redundant kernel while JupyterLab's own automatic
attempt was merely still in flight (not stuck), racing its own
request-preemption logic (`_pendingSessionRequest`) for no reason and
leaking a disposed-object console error as a side effect of the resulting
(harmless, but real) double-start-and-cleanup. The `sessionContext.ready`
-vs-bounded-timeout race above is the actual fix for this: it waits long
enough for a merely-slow legitimate attempt to finish on its own, and
only engages its own recovery path once that full window has passed with
still no kernel. Re-verified: the same 3x-serial-repeat check against
**exercises 1, 2, and 3** together (66 test executions) passed **66/66
clean**, and the full combined 9-exercise suite was re-run once more in
full (see Verification) with zero recurrence.

**New permanent coverage:** `interactive/e2e-book/kernel-startup.spec.ts`
-- 3 fresh-context opens, 1 fresh open under the real GitHub-Pages-style
path-prefixed route (`/ml-neuro-tutorials/...`, previously never exercised
by any existing kernel-related test -- every prior kernel test used the
site-root route only), and 1 "returning profile" (same browser context,
edit + save + reload). Each confirms the kernel actually reaches "Python
(Pyodide)" (not just that the label appears) by running a trivial cell and
asserting no error cell, and captures console/network diagnostics into the
failure message if any attempt is ever caught on "No Kernel". All 5 pass
locally against the rebuilt combined site (see Verification).

**Honest limitation:** the *original* "No Kernel" race itself (as opposed
to this fix's own, separately-caught-and-fixed regression) is a confirmed
mechanism and a defensible, source-verified fix, not a reproduced-then-
fixed bug -- no live diagnostic, before or after this deploy (13 real
browser attempts across the pre-deploy investigation and the final
post-deploy verification, see Verification below), ever caught a notebook
stuck on "No Kernel" itself. If the author still sees "No Kernel" after
this deploy, the next useful evidence would be the exact browser console
output at the moment it happens (this fix's own dialog, or the absence of
the usual fallback console line, would be diagnostic).

## Deviations from the WP spec (both decided before committing, not after)

1. **D.1's reveal mechanism:** the WP asked for a `<details>`/`<summary>`
   collapsible reveal "if that actually renders and toggles in both
   JupyterLite and a downloaded notebook opened in Colab," with an
   explicit fallback to a plain display "if either renderer does not
   support it reliably." This environment has no real Google Colab
   browser access to verify the toggle live there (the WP itself
   anticipated this: "prepare the compact teacher-filled copy/checklist if
   real Colab access is unavailable" -- but that clause is about a
   teacher-filled *notebook* copy, not a way to verify unrelated HTML/JS
   rendering behavior in Colab's own UI). Rather than claim a Colab
   browser test that was never run, this used the WP's own explicit safe
   fallback: a plain answer displayed directly below the question,
   verified to render identically everywhere nbformat markdown renders.
2. **D.2's hint comments:** flagged directly by the author mid-session
   (see Acceptance table D above) -- fixed before commit, not left as a
   finding.
3. **E's fix location:** the WP named "JupyterLite configuration/
   extension/open flow" as the fix's intended location; implemented in
   this repo's own `course-toolbar` extension specifically because it is
   the one piece of the JupyterLite app shell this repo actually owns and
   can patch -- `@jupyterlab/apputils`'s `SessionContext` itself (where the
   actual race lives) is third-party and pip-installed.

## Verification

### Local, offline (Python)

```
.venv/bin/python -m unittest discover -s tests
```
Two full runs (both launched detached via `nohup ... & disown`, per the
repo's own persistent-job policy -- see Process note below): the first,
run before the `tests/test_book_structure.py` fix above, found exactly the
3 now-fixed stale assertions -- **1203 tests, 1412.0s (~23.5m), 3
failures, 11 skipped**; the second, after the fix, is the clean final run
-- **1203 tests, 1353.7s (~22.6m), 0 failures, 11 skipped (pre-existing,
unrelated to this WP)**.

### Local, frontend (full gate)

```
cd interactive
npm run typecheck   # clean
npm run test:unit   # 481 tests passed (38 files), 3.52s
npm audit --omit=dev   # 0 vulnerabilities
npm run build        # unchanged output (book/_static/widgets/app not touched by this WP)
npx playwright test  # standalone widget app suite: 299 passed, 50.4s
```

### Local, browser (real headless Chromium against the actual combined build)

```
rm -rf book/_build
.venv/bin/jupyter-book build book
.venv/bin/jupyter lite build --config book/lite/jupyter_lite_config.json \
  --lite-dir book/lite --output-dir book/_build/html/lite
cd interactive && npm run test:e2e:book
```
Built three times -- not repeats for wording adjustments, but each to
incorporate a real subsequent code change: (1) after A-D, before item E;
(2) after E's first `ensureKernelStarted()` implementation; (3) after
that implementation's own fix (see Section E's regression writeup above).
Every Jupyter Book build succeeded with the same 2 pre-existing warnings
(missing `logo.png`, `README.md` not in any toctree) as WP54's own
baseline -- neither new.

`exercise-01-lite.spec.ts` (8 tests, includes the new FIQ/VIQ activity):
**8/8 passed, 1.1m**.
`kernel-startup.spec.ts` (new, 5 tests): **5/5 passed, 43.2s** (isolated;
see Section E for the full 3x-repeated, zero-contention verification of
this file together with exercises 1-3, 66/66 clean).

Full combined suite (`npm run test:e2e:book`, every chapter + exercise
spec, full local parallelism) against the final, fixed build: **119
passed, 10 failed, 28.2m**. Zero `"was disposed"` errors (the regression
this WP's own fix targeted). All 10 failures were `waitForKernelIdle`
timeouts (9) or a 90s test-timeout during an unusually slow run (1, this
WP's own `kernel-startup.spec.ts` returning-profile test) concentrated
overwhelmingly on Exercise 7 (5 of 10, plus the cross-chapter dark-mode
test that also targets Exercise 7) and each exercise's own heaviest
"teacher-completed, fill in every blank" test (Exercises 5, 6, 8) --
exactly the CPU-contention pattern WP54's own report already documented
for full local parallel runs on this machine ("every one in Exercises
1/4/6/7's heaviest tests... passed cleanly once rerun serialized"), and
exactly why `playwright.book.config.ts` already caps CI itself to a
single worker for this file while leaving local runs fully parallel for
speed. Re-ran all 6 affected spec files together, serialized (`--workers=1`,
zero contention): **37/37 passed, 1.0h** -- every test that failed under
full parallelism passed cleanly in isolation, including this WP's own
`kernel-startup.spec.ts` (5/5, all under 30s each) and Exercise 7's own
slowest test (19.8m where it previously hit the identical `600000ms`
timeout under contention). Zero `"was disposed"` errors across all 37.
Confirms the 10 full-parallel failures were the already-documented local
CPU-contention class (WP54), not a regression.

### Real GitHub Actions CI run

`scripts/classify_release_change.py` on the actual committed diff:
```
GATE: full
reason: shared/unknown path(s) changed: CLAUDE_INTERACTIVE_WIDGETS.md
  (unknown); book/lite/extensions/course-toolbar/src/index.ts (shared:
  JupyterLite course-toolbar extension); book/lite/files/data/
  exercise_01_fiq_viq_reference.png (shared: shared exported data asset);
  book/references.md (unknown); book/resources.md (unknown);
  book/syllabus.md (shared: book hub page); interactive/e2e-book/
  kernel-startup.spec.ts (shared: shared book browser-test fixture/spec);
  scripts/render_exercise_01_fiq_viq_reference_plot.py (shared: shared
  script); tests/test_book_structure.py (shared: shared Python test)
affected exercise IDs: [1]
```
Not overridden -- the `course-toolbar` change alone would have forced
`full` regardless of everything else, and the classifier's decision was
used as-is.

**A real mistake caught before it could do damage:** `git push origin main`
was first run while still on the `feature/wp55-small-fixes-kernel-and-
release` branch, which pushed local `main` -- unchanged since before this
WP, still at `b2f0350` -- rather than the WP55 work (a feature-branch
workflow this repo hadn't used mid-WP before; the fast-forward step was
missed on the first attempt). This triggered a real, unwanted CI run
(`38394864039`) for that stale state. Caught immediately from `gh run
list`'s own output (two runs in progress, the older one's message
obviously not WP55's own); `main` was fast-forwarded to the real tip
(`c10d714`) and pushed properly (`b2f0350..c10d714`, triggering the real
run `38394912271`), and the stale run was cancelled
(`gh run cancel 38394864039`) before it could reach anywhere near its own
"Publish website" step (cancelled at 1m25s, confirmed via `gh run view`
showing both jobs' actual state -- a `full`-gate run takes 1.5-2h, so
cancelling this early closed a real risk: had it instead run to
completion and published *after* the real run, the live site would have
been silently reverted to pre-WP55 content). No blind retry: this was
corrected once, deliberately, based on actual `gh run list` evidence.

Real CI run: [`38394912271`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/38394912271)
("Build and deploy Jupyter Book"): **success**. `classify` job 8s;
`build-and-deploy` job **1h50m35s**. Every step succeeded, including
**Publish website**:

| Step | Result |
|---|---|
| Type-check and unit-test the frontend | passed (481 tests, 38 files) |
| Audit production frontend dependencies | passed (0 vulnerabilities) |
| Check every migrated exercise generator is not stale (offline, full gate) | passed |
| Unit-test the Python scripts (offline, full gate) | **1203 tests, 1203.2s (~20m), OK, 11 skipped** -- matches the local final run's counts |
| Check the portable notebook is not stale (offline, full gate) | passed |
| End-to-end test the standalone widget app | **299 passed, 1.3m** |
| Build Jupyter Book / Build JupyterLite (Exercises 1-9) | passed |
| End-to-end test the combined book + JupyterLite build (full gate) | **129 passed, 1.3h, 0 failed, 0 `"was disposed"` errors** -- CI's own book-suite config already caps this step to a single worker (`playwright.book.config.ts`: `...(process.env.CI ? { workers: 1 } : {})`), exactly the serialized condition the local reruns above used to separate the real fix from CPU-contention noise -- confirming on CI's own infrastructure, not just locally, that the fix holds and nothing in this WP regressed any of the other 8 exercises |
| Execute the portable notebook outside the repository (Exercises 1-9 only, full gate) | passed |
| Publish website | succeeded |

### Live-site verification

- `gh-pages` branch HEAD commit message: `deploy:
  c10d71444246f2b2d353dfee73387ee90fcf7535` -- matches the pushed `main`
  SHA exactly.
- Direct HTTP checks against the real published site
  (`https://yoavmp.github.io/ml-neuro-tutorials/`): `syllabus.html`,
  `resources.html`, `references.html`, `contents.html`,
  `chapters/chapter_01/exercise_01.html`,
  `lite/files/exercise_01.ipynb`, and
  `lite/files/data/exercise_01_fiq_viq_reference.png` all return HTTP 200
  (one transient 503 on `syllabus.html`'s first request resolved to 200
  on an immediate retry -- a momentary CDN blip, not a real gap).
  `chapters/chapter_1{0,1,2}/exercise_1{0,1,2}.html` all return HTTP
  **404** (Exercises 10-12 remain unpublished).
- Live `syllabus.html` contains "Dan David building, room 110" and zero
  occurrences of "location not provided"/"Only Exercises 1-9 are
  published". Live `resources.html` contains "NeuroHackademy 2020
  machine-learning tutorial data" (the new credit link). Live
  `references.html` contains zero occurrences of "used throughout
  Exercises 1-9"/"Exercises 1-9 are built on".
- The live `exercise_01.ipynb` (downloaded directly from the published
  site, not the local build) contains `fiq_viq_r`, `scatter_matrix`, and
  the `wp42-activity-fiq-viq-scatter` tag -- all 61 cells present.
- The live `jupyter-lite.json`'s `course-toolbar` federated-extension
  entry points at `remoteEntry.c47a16ea64b1480d0de6.js` -- the exact
  bundle hash produced by this WP's final (fixed) `jupyter labextension
  build`, confirming the deployed extension is the fixed version, not the
  original or the first (regressed) fix attempt.
- **Real browser verification against the live, deployed site** (not a
  repeat of the local/CI browser-automation checks above): 5 fresh
  headless-Chromium contexts opened the live Exercise 1 notebook
  (`https://yoavmp.github.io/ml-neuro-tutorials/lite/notebooks/index.html?path=exercise_01.ipynb`)
  independently. **5/5** reached "Python (Pyodide)" (never stuck on "No
  Kernel"), each executed its first cell successfully, and **zero**
  `"was disposed"` console errors occurred. This is bounded, repeated
  evidence of the fix working on the actual production deployment, not a
  claim that the original intermittent race is "solved" from one
  successful launch -- see Section E's own honest-limitation note on the
  live diagnostics' scope.

## Process note: long-running commands (following the newly committed policy)

| Command | Launch | Duration | Notes |
|---|---|---|---|
| Combined book/lite build #1 (pre-kernel-fix, A-D) | detached (`nohup`/`disown`, PID 57726) | a few minutes | succeeded, exit 0 |
| Live-site kernel diagnostic (throwaway script, since deleted) | detached (PID 57955) | ~3.5m | 8/8 attempts; evidence folded into Section E above |
| Offline suite, run 1 (pre-test-fix) | detached (PID 57985) | 1412.0s (~23.5m) | 3 failures (now fixed) |
| Combined book/lite build #2 (first kernel-fix version) | detached (PID 58626) | a few minutes | succeeded, exit 0 |
| Offline suite, run 2 (final, clean) | detached (PID 66060) | 1353.7s (~22.6m) | 0 failures |
| Full combined book e2e suite, run 1 (`npm run test:e2e:book`, first kernel-fix version) | detached (PID 66985) | 33.1m | 126 passed, 3 failed -- all `"<id> was disposed"` console errors; root-caused below |
| Isolated rerun, exercises 1-3 (first kernel-fix version, `--workers=1`) | detached (PID 75953) | ~15m | 2 failed (1 `"was disposed"`, 1 unrelated timeout) -- confirmed reproducible even with zero contention |
| Baseline A/B check: exercise-01-lite.spec.ts x3, **completely unmodified** pre-WP55 extension | detached (PID 78288) | 7.2m | 24/24 clean, 0 `"was disposed"` -- proved the error was not pre-existing |
| Fix-verification: exercises 1-3 x3 repeats, **revised** kernel-fix | detached (PID 78633) | 35.5m | 66/66 clean, 0 `"was disposed"` -- proved the revision fixed it |
| Combined book/lite build #3 (revised kernel-fix, final) | detached (PID 76160) | a few minutes | succeeded, exit 0 |
| Full combined book e2e suite, run 2 (final, full local parallelism) | detached (PID 79893) | 28.2m | 119 passed, 10 failed, 0 `"was disposed"` -- all 10 were `waitForKernelIdle` timeouts/one slow-test-timeout, concentrated on Exercise 7 (5/10) and each exercise's own heaviest test |
| Rerun of the 6 affected spec files, serialized (`--workers=1`) | detached (PID 81399) | 1.0h | 37/37 clean, 0 `"was disposed"` -- confirmed CPU contention under full parallelism, not a regression |

Every command above exceeding five minutes was launched fully detached
from the harness's own process tree (`nohup <cmd> > <log> 2>&1 < /dev/null
& disown`), confirmed reparented to PID 1, with its PID and log path
recorded in-session as it launched; progress was read back from each log's
actual content rather than assumed. No command was re-launched without
first confirming the previous attempt was not still running or had not
already finished. This WP's session was interrupted by repeated restarts
of the harness itself (not merely its background-task tracking) during
several of the longest runs above; each time, the actual process (PID) and
log were checked directly before concluding anything about the command's
status, exactly as the policy requires -- in every case the detached
process was still genuinely running (or had already finished) rather than
silently dead, so nothing was ever blindly re-launched.

## Final git state

- `main` (local and `origin/main`, in sync): `c10d714`.
- `gh-pages`: `be384f1`, marker `deploy: c10d714...`.
- Checkpoint branch `checkpoint/wp55-pre-work` left in place at the
  pre-WP55 tip (`b2f0350`) for reference.
- `feature/wp55-small-fixes-kernel-and-release` left in place, fully
  merged into `main` (fast-forward, no divergence).
- This report and the changelog are added in a separate, `WPs/**`-only
  closing commit (`paths-ignore` keeps it from triggering another
  deploy).
