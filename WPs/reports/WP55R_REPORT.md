# WP55R report: stop the JupyterLite "Select Kernel" dialog from blocking students

## Success or failure -- read this first

**Success, with an important correction to the WP's own working theory.**
The reported symptom -- a native "Select Kernel" dialog that cannot be used
or closed, with Python sometimes starting behind it regardless -- is now
fixed, with live, repeated, deterministic reproduction of both the pre-fix
failure and the post-fix recovery (Section "Live reproduction" below), not
an untested patch. The WP's own leading hypothesis (a race in
`SessionContext.startKernel()` reading `specsManager.specs` before it is
ready, inherited from WP55's own root-cause writeup for the *different*,
already-fixed "No Kernel" race) turned out, after extensive live fault
injection, to be **unreachable in this specific app's actual bootstrap
sequence** -- this JupyterLite "notebooks" app does not open or populate
any document until every federated extension, including the Pyodide
kernel's own kernelspec registration, has finished loading. The dialog is
real, reproducible, and now fixed; the exact trigger WP55R asked to
confirm is not the one that fires it live in this deployment. Both of
those findings are reported precisely, with the evidence for each, in
"Investigation" below -- this is exactly the kind of correction the WP
asked for ("do not claim success merely because the kernel eventually
starts behind the popup"; "state precisely which mechanism was proved and
which remains an inference").

Exercise 10 / WP56 was not implemented, merged, pushed, or published as
part of this work, as the WP required -- no WP56-related branch, commit, or
file exists anywhere in this repository.

## Starting state and branches

Began at the actual clean `main` tip after WP55 (including its later
report-only commit): `4449f8d` ("WP55: reports -- acceptance table,
kernel-race root cause and fix regression, real CI results, and live-site
verification"), matching `origin/main` exactly. Checkpoint branch
`checkpoint/wp55r-pre-work` created at that tip; work done on
`feature/wp55r-kernel-dialog-fix`.

## Investigation

### The screenshot

The attached work order (`WPs/WP55R_AUTOSTART_PYTHON_KERNEL_NO_STUCK_PICKER.md`)
describes, rather than attaches as a separate image file, the reported
state: a native "Select Kernel" dialog, "No Kernel" shown as the current
kernel, and a menu containing "Start python Kernel", "Use No Kernel",
"No Kernel", and "Start Kernel". No actual screenshot file matching the
stated capture time (13 October 2026, ~18:20) exists anywhere on this
machine (checked via `mdfind` and a direct filesystem search across the
home directory for images from that window) -- the description in the work
order itself is the only available evidence of the author's exact
browser state, so the build-timing question the WP raised ("its
relationship to WP55's actual publish time has not been established")
could not be settled from the file itself. What *could* be settled, and
was: the exact button labels and layout described
("Start python Kernel"/"Use No Kernel"/"No Kernel"/"Start Kernel", title
"Select Kernel") match `@jupyterlab/apputils`'s own
`SessionContextDialogs.selectKernel()` dialog precisely (confirmed by
reading its source, `node_modules/@jupyterlab/apputils/lib/sessioncontext.js`
lines ~907-990, and by reproducing the identical dialog live -- see
below) -- this is unambiguously *that* dialog, not a different or stale
one.

### Root cause this WP's own fix targets (confirmed by source reading)

Reading `@jupyterlab/docregistry/lib/context.js`'s `Context._populate()`:

```js
async _populate() {
    this._isReady = true;
    this._populatedPromise.resolve(void 0);
    await this._maybeCheckpoint(false);
    if (this.isDisposed) return;
    this.sessionContext.kernelPreference = { ...name, language };
    // Note: we don't wait on the session to initialize
    // so that the user can be shown the content before
    // any kernel has started.
    void this.sessionContext.initialize().then(shouldSelect => {
        if (shouldSelect) {
            void this._dialogs.selectKernel(this.sessionContext);
        }
    });
}
```

This is a **second, independent** trigger for the blocking dialog, entirely
outside WP55's own `ensureKernelStarted()` -- it is not awaited by
`_populate()`, and `panel.context.ready` (the promise WP55's own
`ensureKernelStarted()` is chained off) resolves from
`_populatedPromise`, which settles **before** this line even runs. A
post-open recovery that only starts Python in the background, as WP55's
own fix does, cannot make an already-open copy of this exact dialog go
away -- precisely the failure mode the WP warned against.

`sessionContext.initialize()` resolves `shouldSelect = true` (opening the
dialog) via `SessionContext.startKernel()`:

```js
async startKernel() {
    ...
    const name = Private.getDefaultKernel({ specs: this.specsManager.specs, ... });
    if (options) { await this._changeKernel(options); return false; }
    return true; // "needs selection"
}
// Private.getDefaultKernel:
function getDefaultKernel({ specs, preference }) {
    if (!specs || canStart === false) { return null; }
    ...
}
```

`specsManager.specs` is read **synchronously**, with no await on
`specsManager.ready` first. If the Pyodide kernel's own federated
extension has not yet registered its kernelspec at that exact instant,
`specs` is `null`, `getDefaultKernel()` returns `null` unconditionally,
and `startKernel()` returns `true` -- "needs selection" -- opening the
dialog immediately, well before WP55's own 30-second recovery window
could ever run.

### Why this did not reproduce live (and what did)

The WP explicitly asked for deterministic fault injection "for example
delay kernel-spec registration/extension loading" if the exact state could
not be reproduced on the current build, and to "state precisely which
mechanism was proved and which remains an inference." Both were done, with
a genuinely surprising result.

**Attempt 1 -- delay the kernelspec extension's own load (the theorized
trigger):** Playwright `page.route()` delaying every request under
`**/pyodide-kernel-extension/static/**` (the federated extension's
`remoteEntry.*.js` and every sub-chunk it lazily imports), at delays of
6s, 7s, 7.5s, 8s, 8.5s, 9s, 9.5s, 10s, 10.5s, 11s, 12s, 15s, and 20s,
each against a fresh browser context opening Exercise 1, with a generous
total observation window (delay + 30s): **in every single case, the page
still rendered correctly and no Select Kernel dialog ever appeared.** An
early read of this (at 15s/20s delays, with a too-short observation window
of delay+8s) looked like a different hang entirely -- a fully blank page --
but extending the wait fully resolved it: the whole app simply does not
render *anything*, including the kernel-name toolbar item, until every
federated extension (this one included) has finished loading. This means
`Context._populate()`'s own call into `sessionContext.initialize()` --
and therefore the specs-null race above -- structurally cannot run before
`specsManager.specs` is already populated in this specific JupyterLite
"notebooks" app: document population is gated behind the same bootstrap
step that also loads the kernelspec. **This is proved, not inferred**,
by the thirteen delay values above, every one rendering correctly with no
dialog.

**Attempt 2 -- prove the dialog's own lifecycle directly:** Since the
*trigger* could not be reproduced, this instead reproduces the dialog
itself, using JupyterLab's own, completely unmodified
`SessionContextDialogs.selectKernel()` against a real panel's real
`sessionContext`, called via a test-only hook
(`window.__courseToolbarOpenSelectKernelDialogForTest`,
`course-toolbar/src/index.ts`) -- while the session is kept genuinely
kernel-less by delaying the Pyodide kernel's own **CDN assets**
(`pyodide.mjs`/`pyodide.asm.wasm`/`pyodide-lock.json` from
`cdn.jsdelivr.net`), which do *not* block the rest of the app from
rendering (confirmed: the kernelspec itself registers fine, the toolbar
renders, only the kernel's own process is still booting). This produces
the exact, real dialog -- title "Select Kernel", current selection
"No Kernel" -- deterministically, repeatedly. **This is the one directly,
repeatedly reproduced, live.**

**Honest summary of what is proved vs. inferred:** the specs-null race as
the *automatic* trigger for this dialog is a real, confirmed code path in
`@jupyterlab/apputils`/`@jupyterlab/docregistry` (third-party, pip/npm
managed, out of this repo's control) that could fire in a JupyterLab
deployment generally, but is **not reachable in this app's own bootstrap
today** (proved negative, 13 delay values). The dialog's own behavior once
open -- and this fix's effect on it -- **is** proved positive, live,
repeatedly (Section "Live reproduction" below). The fix is shipped anyway
(see "Why fix something unreachable today" below).

### A second real finding: the kernelspec name mismatch is not the cause either

WP55's own report already noted every exercise notebook's kernelspec
metadata asks for `"python3"` while the registered kernel is `"python"`,
and that this is benign (resolved via a language-based fallback,
confirmed via `Private.getDefaultKernel()`'s own matching code -- an exact
name match fails, a single language match succeeds, logging
`console.warn('No exact match found for python, using kernel python...')`).
This WP re-confirmed the same thing live, on every single page load,
fixed build included -- it fires every time and never alone produces the
dialog. No kernelspec metadata was changed (would have needed to touch
every exercise's generated notebook and its downloaded/Colab-facing
portable copy for no benefit -- the WP's own instruction not to "ship an
unnecessary speculative patch").

### Why fix something unreachable today

Even though the specs-null race could not be triggered live in this app's
*current* bootstrap, the underlying library code that would open the
dialog that way is real, third-party, and not something this repo
controls the version or future behavior of -- a future `jupyterlab`/
`jupyterlite-core` bump, or any change to how this app sequences document
opening relative to extension loading, could reopen exactly this window.
The fix (below) defends against the dialog itself, not against one
specific timing path to it, at essentially no cost (verified harmless in
every normal case; see Verification). This matches the WP's own
instruction to defend at the dialog's own lifecycle, not only the
kernel-start timing.

### The service-worker / stale-shell hypothesis

The WP separately asked to investigate whether a cached old shell/service
worker could mix release versions. This build registers its service
worker with `enableCache=false`
(`Registering new JupyterLite ServiceWorker .../service-worker.js?enableCache=false`,
confirmed live in every browser run this WP performed), and student
content lives in a **separate** browser storage than the service worker's
own cache: `indexedDB.databases()` reports
`'JupyterLite Storage - /lite/'` (the student's notebook edits) alongside
`caches.keys()` reporting only `'precache'` (the service worker's own
app-shell cache) -- two different storage mechanisms, confirmed live. This
means the safe recovery path the WP asked for, if the author ever
suspects a stale cached shell, is real and precise: **unregister the
service worker or clear only the browser's Cache Storage for this site
(DevTools -> Application -> Service Workers -> Unregister, or
Application -> Storage -> Cache Storage -> delete `precache`) and
reload** -- this does not touch IndexedDB and cannot lose a student's
saved work, unlike "clear all site data," which the WP explicitly said
not to ask for. This was not pursued further as *the* explanation for the
screenshot (no live reproduction was attempted or needed, since the
dialog's blocking behavior is independently fixed regardless of which
release-mixing scenario, if any, originally opened it) but is recorded
here as the safe, disclosed author-facing answer the WP asked for either
way.

## Fix implemented

In `book/lite/extensions/course-toolbar/src/index.ts`:

- **`interceptAutomaticKernelSelectDialog(panel)`** (new): watches the
  static `Dialog.tracker` (a JupyterLab singleton, shared via this
  extension's own `package.json` `sharedPackages`) for any dialog added
  while *armed*. For the first one seen, once its header text (read from
  `.jp-Dialog-header`, the exact class `Dialog`'s own renderer uses --
  `dialog.title.label` is never set and is useless for this, see below)
  reads "Select Kernel", it calls the dialog's own public `reject()` --
  the same effect as the user clicking Cancel, which
  `SessionContextDialogs.selectKernel()`'s own code treats as a safe
  no-op (`if (!result.button.accept) return;`, never reaching the branch
  that could shut down a session). The guard arms itself the moment a
  notebook panel is added to the tracker (not deferred behind
  `panel.context.ready`) and disarms itself the first time the kernel's
  own `statusChanged` reports anything other than
  `starting`/`unknown`/`restarting`/`autorestarting`, with a 60-second
  hard ceiling as a safety net. This means an explicit, later
  "Change Kernel" request from the user is always left completely
  untouched -- the guard is only ever live during the notebook's own
  initial startup window.
- `ensureKernelStarted()`/`ensureKernelStartedInner()` (WP55's own
  bounded-recovery logic) are **unchanged** -- this WP adds dialog
  dismissal as an independent concern, not a replacement.
- A test-only hook, `window.__courseToolbarOpenSelectKernelDialogForTest`
  (not wired to any command, menu, keybinding, or palette entry), lets
  `kernel-select-dialog-race.spec.ts` trigger the real, unmodified
  `SessionContextDialogs.selectKernel()` deterministically, for the reason
  in "Why this did not reproduce live" above.

### Three real mistakes caught only by live testing, not by inspection

Each of these looked correct on paper and was wrong in practice --
exactly the trap the WP's own "do not claim success merely because the
kernel eventually starts behind the popup" warning was about:

1. **`dialog.title.label` is always `''`.** `Dialog` never sets the
   Lumino `Widget.title` property (that is for things like dock-panel
   tabs); a first version matched on it and, because of that, never
   intercepted a single dialog -- confirmed live, the same reproduction
   below still showed a fully blocked dialog with this version. Fixed by
   reading the rendered `.jp-Dialog-header` text instead.
2. **The guard's armed lifetime cannot be tied to
   `ensureKernelStartedInner()`'s own early return.**
   `panel.sessionContext.session?.kernel` -- and therefore
   `panel.sessionContext.ready` -- becomes truthy as soon as a
   `KernelConnection` *object* exists, which can be well before the
   underlying kernel process (a multi-megabyte Pyodide WASM download) has
   actually finished starting. A version that disconnected the guard in
   `ensureKernelStarted`'s own `finally` tore it down seconds before a
   dialog opened during a still-ongoing download in a live reproduction
   that delayed the Pyodide kernel's CDN assets -- reproducing the exact
   "fix starts Python in the background but an earlier dialog stays open"
   failure the WP warned about. Fixed by tying the guard's lifetime to a
   real post-startup kernel status instead.
3. **The dismissal decision cannot re-check `session?.kernel` either**,
   for the same underlying reason: a version that added "never touch a
   dialog once a kernel exists" as an extra safety check left a real
   dialog open in a live reproduction (clicking the real kernel-name
   toolbar button while it still read "No Kernel") because a
   `KernelConnection` object already existed, mid-handshake, by the time
   the check ran. The `armed` flag (point 2) is already the single
   correct signal for "are we still in the startup window" -- removed the
   redundant, wrong check.
4. (A smaller, related timing issue) **`dialog.ready` does not guarantee
   the header's own React render has painted.** `Dialog`'s `ready`
   promise only waits on its *body* widget's render, not its separately
   rendered header -- reading `.jp-Dialog-header`'s text immediately
   after `ready` (even after two queued animation frames) sometimes read
   back empty, live, even though the same node unambiguously held
   "Select Kernel" moments later. Fixed with `waitForHeaderText()`, which
   polls once per animation frame (paced to the browser's own paint
   cycle, bounded by a 2-second ceiling) rather than guessing a fixed
   delay.

## Live reproduction (pre-fix vs. post-fix)

Both runs: a fresh headless-Chromium context, Exercise 1 opened via
`/lite/notebooks/index.html?path=exercise_01.ipynb`, Pyodide's own CDN
assets delayed 9 seconds (keeping the session genuinely kernel-less for
that window), the test-only hook used to open the real, unmodified
`SessionContextDialogs.selectKernel()` dialog, then polled for the
dialog's presence and whether a trivial cell can actually be run.

**Pre-fix** (the exact `main`-tip `index.ts` from before this WP, with
only the test hook grafted on so it could be driven the same way):
dialog opens (confirmed: header "Select Kernel", "No Kernel" as current
selection) and **stays open for the full observation window** --
`sawDialog=true, goneAt=null` (never dismissed) -- while Python
nonetheless starts successfully in the background
(`final pyodide visible: true`), and a cell click **fails**:
`<dialog aria-modal="true" ...> intercepts pointer events` -- the exact
reported symptom, reproduced deterministically.

**Post-fix** (this WP's `index.ts`): dialog opens and is gone again
within the same poll cycle it was first observed in (one run:
`sawDialog=false` -- dismissed before the first 200ms poll even caught
it visible; another: `sawDialog=true, goneAt t+2262` -- open for ~340ms),
**zero** dialogs remain afterward, Python starts, and the cell runs with
**zero** error cells. Repeated 3x in a row, clean every time.

## Focused browser test (committed)

`interactive/e2e-book/kernel-select-dialog-race.spec.ts` (2 tests, both
new):

1. "a Select Kernel dialog opened while the kernel has not started yet
   does not stay open, and Python still starts" -- the exact live
   reproduction above, as a permanent regression test: asserts the
   dialog reaches zero count within 5 seconds of opening, then confirms
   Python actually starts and a trivial cell actually runs with no error
   cells (not just that the toolbar label changes).
2. "the normal fast path (no delay) never shows a Select Kernel dialog at
   all" -- confirms the guard has no effect on the ordinary case.

Both pass locally, 3x repeated with zero flakes, and as part of the real
CI run (full gate -- see "Real CI run" below).

## Verification

### Local, offline (Python)

```
.venv/bin/python -m unittest discover -s tests
```
Launched detached (`nohup ... & disown`, PID 31251, per the repo's own
persistent-job policy -- the harness restarted mid-run twice during this
WP's own session; both times the actual process was confirmed still
running from its real PID before concluding anything, never re-launched).
**1203 tests, 1789.5s (~29.8m), OK, 11 skipped** (pre-existing, unrelated
to this WP) -- matches WP55's own prior baseline exactly.

### Local, frontend (full gate)

```
cd interactive
npm run typecheck   # clean
npm run test:unit   # 481 tests passed (38 files)
npm audit --omit=dev   # 0 vulnerabilities
npm run build        # unchanged output (book/_static/widgets/app not touched)
npx playwright test  # standalone widget app suite: 299 passed, 1.1m
```

### Local, browser (real headless Chromium against the actual combined build)

```
.venv/bin/jupyter-book build book
.venv/bin/jupyter lite build --config book/lite/jupyter_lite_config.json \
  --lite-dir book/lite --output-dir book/_build/html/lite
cd interactive && npm run test:e2e:book
```

Labextension rebuilt (`npx tsc && jupyter labextension build --development
True .`) and the site's `lite` layer rebuilt after every source revision
during development (eleven total rebuilds across the investigation and
the three real bugs above); only the final, fixed source is what was
built for the runs below and what shipped.

`kernel-select-dialog-race.spec.ts` (new): **2/2 passed**, repeated 3x in
a row with `--workers=1`, zero flakes.
`kernel-startup.spec.ts` (WP55's own, unmodified): **5/5 passed** --
confirms no regression of the already-fixed race.
`exercise-01-lite.spec.ts`: **8/8 passed**, including the
download/reset-template toolbar tests -- confirms the new guard does not
interfere with this extension's other toolbar behavior.

Full combined suite (`npm run test:e2e:book`, every chapter + exercise
spec, full local parallelism): **127 passed, 4 failed, 32.8m**. All 4
failures were in `exercise-07-lite.spec.ts` (`waitForKernelIdle`/
`boundingBox` timeouts) -- the exact local CPU-contention pattern WP54's
and WP55's own reports already documented for full-parallelism runs on
this machine. **Zero** `"was disposed"` console errors anywhere (the
regression class WP55's own fix had to catch and fix). Re-ran
`exercise-07-lite.spec.ts` alone, serialized (`--workers=1`, zero
contention): **7/7 passed, 32.9m** -- every test that failed under full
parallelism passed cleanly in isolation, confirming CPU contention, not a
regression.

### Change-aware release classifier

```
.venv/bin/python scripts/classify_release_change.py
```
```
GATE: full
reason: shared/unknown path(s) changed: book/lite/extensions/course-toolbar/src/index.ts
  (shared: JupyterLite course-toolbar extension (shared by every exercise));
  interactive/e2e-book/kernel-select-dialog-race.spec.ts (shared: shared book
  browser-test fixture/spec)
```
Not overridden -- the `course-toolbar` change alone forces `full`
regardless of everything else, used as-is, matching the full local
verification above.

### Real CI run

**A real mistake avoided, by applying WP55's own documented lesson:**
before pushing, `main` was explicitly fast-forwarded to the feature
branch's tip (`git checkout main && git merge --ff-only
feature/wp55r-kernel-dialog-fix`), then verified
(`git branch --show-current` == `main`, `git rev-parse HEAD` ==
`git rev-parse main` == `c907d9d`) before `git push origin main:main` --
the exact sequence WP55's own report flagged as the fix for the mistake
it made (pushing while still on the feature branch, which pushed a stale
`main`). This push triggered exactly **one** CI run, confirmed via
`gh run list` immediately after -- no stale/duplicate run to cancel this
time.

Real CI run:
[`38467268169`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/38467268169)
("Build and deploy Jupyter Book"): **success**. `classify` job 8s;
`build-and-deploy` job **2h6m51s**. Every step succeeded, including
**Publish website**:

| Step | Result |
|---|---|
| Install and build the course-toolbar JupyterLite extension | passed |
| Type-check and unit-test the frontend | passed |
| Audit production frontend dependencies | passed |
| Check every migrated exercise generator is not stale (offline, full gate) | passed |
| Unit-test the Python scripts (offline, full gate) | **1203 tests, 1769.3s (~29.5m), OK** -- matches the local final run's counts exactly |
| Check the portable notebook is not stale (offline, full gate) | passed |
| End-to-end test the standalone widget app | **299 passed, 1.7m** |
| Build Jupyter Book / Build JupyterLite (Exercises 1-9) | passed |
| End-to-end test the combined book + JupyterLite build (full gate) | **131 passed, 1.6h, 0 failed** -- CI's own single-worker config (`playwright.book.config.ts`: `...(process.env.CI ? { workers: 1 } : {})`) avoids the local full-parallelism CPU contention entirely, so this ran clean without needing a serialized rerun the way the local full-parallel pass did |
| Execute the portable notebook outside the repository (Exercises 1-9 only, full gate) | **OK [chapter_02]: portable notebook executed cleanly (22 code cells, key values matched)** |
| Publish website | succeeded |

Zero `FAILED`/`was disposed` strings anywhere in the full job log
(checked directly, not just the summary lines).

### Live-site verification

- `gh-pages` branch HEAD commit message: `deploy:
  c907d9dc874f9e5824dbee08dbd4b9a18cfeeab9` -- matches the pushed `main`
  SHA exactly.
- Direct HTTP checks against the real published site
  (`https://yoavmp.github.io/ml-neuro-tutorials/`): `syllabus.html`,
  `contents.html`, `chapters/chapter_01/exercise_01.html`,
  `lite/files/exercise_01.ipynb`, and `lite/jupyter-lite.json` all return
  HTTP 200. `chapters/chapter_1{0,1,2}/exercise_1{0,1,2}.html` all return
  HTTP **404** (Exercises 10-12 remain unpublished -- Exercise 10/WP56
  untouched, as required).
- The live `jupyter-lite.json`'s `course-toolbar` federated-extension
  entry points at `remoteEntry.a758aa06ad5da921d205.js` -- the exact
  bundle hash produced by this WP's own final local build (confirmed
  identical, not just "a" rebuild), confirming the deployed extension is
  the actual fixed version verified throughout this report, not a
  different CI-side rebuild.
- **Real browser verification against the live, deployed site** (not a
  repeat of the local/CI browser-automation checks above): 5 fresh
  headless-Chromium contexts opened the live Exercise 1 notebook
  (`https://yoavmp.github.io/ml-neuro-tutorials/lite/notebooks/index.html?path=exercise_01.ipynb`)
  independently. **5/5** reached "Python (Pyodide)" and executed their
  first cell successfully with zero error cells. One of the five logged a
  transient `503`/`ChunkLoadError` on a federated chunk fetch that
  self-recovered within the same load (matching the kind of momentary CDN
  blip WP55's own live verification also saw once, on a different asset)
  -- not a regression, and every other check in that same run (kernel
  start, cell execution) still succeeded.
- **Live reproduction of the fix itself, against production**: the same
  test-only hook used throughout this report
  (`window.__courseToolbarOpenSelectKernelDialogForTest`, confirmed
  present and reachable on the live site -- it ships as part of the
  deployed extension bundle) was used to open the real
  `SessionContextDialogs.selectKernel()` dialog against the live site
  while Pyodide's own CDN assets were deliberately delayed 9 seconds
  (keeping the session genuinely kernel-less). Result:
  `hookOpenedDialog=true, dismissedWithin5s=true, finalDialogCount=0,
  pyodideVisible=true` -- the dialog opened and was gone again within 5
  seconds, and Python still started successfully, **on the actual
  production deployment**, not a local rebuild. This is the strongest
  evidence available that the fix verified throughout this report is the
  fix now live for students.

## Process note: long-running commands (persistent-job policy)

| Command | Launch | Duration | Notes |
|---|---|---|---|
| Combined book/lite build (final, fixed source) | detached, foreground-confirmed | a few minutes | succeeded, exit 0 |
| Standalone widget app e2e (`npx playwright test`) | detached (`nohup`/`disown`, PID 31545) | 1.1m | 299/299 passed |
| Offline Python suite | detached (PID 31251) | 1789.5s (~29.8m) | 1203 tests, OK, 11 skipped; survived two harness session restarts mid-run, confirmed still genuinely running from its real PID/log both times, never re-launched |
| Full combined book e2e suite (`npm run test:e2e:book`, full parallel) | detached (PID 31986) | 32.8m | 127 passed, 4 failed (Exercise 7, CPU contention); survived one harness session restart, confirmed from PID/log |
| Serialized rerun, `exercise-07-lite.spec.ts` alone | detached (PID 33664) | 32.9m | 7/7 passed, zero contention; survived one harness session restart |
| Portable notebook smoke (`smoke_portable_notebook.py --notebook chapter_02`) | backgrounded by the harness | ~1 min | `OK [chapter_02]: portable notebook executed cleanly` |

Every command above exceeding a couple of minutes was launched fully
detached from the harness's own process tree, with its PID and log path
recorded, and recovered after each of several harness/session restarts by
checking the real process (`ps -p <PID>`) and the log's actual content --
never assumed finished, failed, or re-launched blindly.

## Final git state

- `main` (local and `origin/main`, in sync): `c907d9d`.
- `gh-pages`: `1b9e44e`, marker `deploy: c907d9d...`.
- Checkpoint branch `checkpoint/wp55r-pre-work` left in place at the
  pre-WP55R tip (`4449f8d`) for reference.
- `feature/wp55r-kernel-dialog-fix` left in place, fully merged into
  `main` (fast-forward, no divergence).
- This report and the changelog are added in a separate, `WPs/**`-only
  closing commit (`paths-ignore` keeps it from triggering another
  deploy).

## Deviations from the WP

None substantive. The WP's own suggested fix locations ("ensure the
default-kernel choice happens early enough... or actively resolve/cancel
an already-open initial dialog") are both partially present: the guard
actively resolves/cancels, and arms as early as this extension's own code
can run (synchronously on `tracker.widgetAdded`, not deferred). The
WP's suggested "disable `@jupyterlab/apputils-extension`'s own session-
dialogs plugin via `disabledExtensions`" alternative was investigated and
explicitly not used -- reading the installed `jupyterlite_core` package's
own `federated_extensions` addon (`patch_jupyterlite_json`) confirms this
version never propagates a labextension's own `package.json`
`disabledExtensions` field into the built `jupyter-lite.json`, so that
route would need a separate build-time patch script, not just a source
change, for no behavioral benefit over the dialog-API approach actually
used.
