# WP43-series deployment fix: closing the recurring Section 8 / CI arc

## Success or failure

**Success — deployed.** Five commits (`a016d8e`, `17b13fc`, `596ef9b`,
`4d19fbb`, `dcc5365`), five triggered CI runs, and one genuinely new bug
found one step further in once the first was fixed. The workflow run
triggered by the final commit,
[`36566657471`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/36566657471)
at head SHA `dcc5365`, **passed every step including `Publish website`.**
`gh-pages` advanced to `05ceb13e4467616c72b0033e6990da8ce5d162d6`
(`deploy: dcc53655b8e4b3eac67ba741e165ff6bbbf0cf3d`) — the first successful
production deploy since WP41 began migrating Exercises 1 and 2 to
JupyterLite. The live site now serves the migrated exercises.

This report picks up where `WPs/reports/WP43RR_REPORT.md` left off (that WP
was rerun-only, authorized to stop after one failed rerun) and covers
everything from the course author's explicit authorization to diagnose, fix,
and deploy through to completion.

## The arc, in order

### 1. `a016d8e` — the real fix, obscured by its own diagnostics

**Root cause of the original, WP43R/WP43RR-reported failure**:
`interactive/e2e-book/exercise-02-lite.spec.ts` used a fixed 100-second
cold-start wait after "Run All Cells" for all 7 of its full-notebook tests.
Two prior CI runs had failed identically at the Section 8 slider test,
never finding the widget handle within that budget. Two pieces of evidence,
found by reading the surrounding test suite rather than guessing:

- `interactive/e2e-book/exercise-01-lite.spec.ts` already used 140 seconds
  for all 6 of its tests.
- `interactive/e2e-book/wp22-cross-chapter-dark-mode.spec.ts`'s own
  Exercise-2 dark-mode check already used 140 seconds for this *exact*
  notebook, with a comment claiming (incorrectly, at the time) that
  `exercise-02-lite.spec.ts` already matched it.

Bumped all 7 waits in `exercise-02-lite.spec.ts` from 100s to 140s,
matching the value already proven elsewhere in the same suite for the same
notebook. Verified locally: all 9 tests in the file pass individually.

Also added `video`/`trace` capture to `playwright.book.config.ts` and a
CI artifact-upload step, since WP43RR had found the prior failures left no
trace, screenshot, or video to inspect. This turned out to be premature —
see below.

**CI result**: the Section 8 slider test passed for the first time. A
*different*, previously always-green test failed instead:
`iframe-height-contract.spec.ts`'s Chapter 5 Ridge/Lasso check, undershooting
its required height by 42px (`1578px` received vs `>=1620px` required).

### 2. `17b13fc` — the wrong diagnosis (video), corrected by evidence

Hypothesis: `video: "retain-on-failure"` records continuously for every
test to support that retention mode, and the added CPU load was perturbing
Chapter 5's `page.waitForFunction(..., { polling: "raf" })` settle-detection
(a 400ms wall-clock stability window, sensitive to delayed rAF callbacks).
Removed `video`, kept `trace`.

**CI result**: the *exact same* test failed with the *exact same* `1578px`
reading. Identical numbers across two independent CI runs is not random
flakiness — it meant the video theory was wrong, or at least incomplete.

### 3. `596ef9b` — the wrong diagnosis (cross-worker contention), also corrected by evidence

Re-examined the failing run's own timestamps: worker A ran
`exercise-02-lite.spec.ts`'s heavy Pyodide tests continuously for ~5.5
minutes; worker B's fast `iframe-height-contract.spec.ts` tests executed
inside that exact window, including the failing Chapter 5 case. Hypothesis:
CI's 2-vCPU runner couldn't give two simultaneously-busy Chromium processes
enough CPU, starving worker B's rAF-based polling. Capped Playwright to
`workers: 1` in CI to eliminate cross-test contention entirely (accepting
roughly double the wall-clock time for that step; the workflow has no
tighter time budget than GitHub's own 360-minute job default).

**CI result**: the exact same test failed a *third* time, with the exact
same `1578px` reading — now under full serialization, where cross-test
contention is structurally impossible. This disproved the contention
theory outright.

### 4. `4d19fbb` — the actual fix

The one setting present in all three failing runs, unlike video and
worker count, was `trace: "retain-on-failure"` — which, like video, has to
record continuously (DOM snapshots, screenshots, console, network) to
support failure-retention, adding real overhead to every test regardless of
pass/fail. Removed `trace`, reverted the now-pointless `workers: 1` cap
(it never helped and only cost CI time). Kept only
`screenshot: "only-on-failure"`, which is genuinely free on a passing test
(it fires once, only on failure, no continuous recording).

**CI result**
([`36546309608`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/36546309608)):
**the entire 149-test browser suite passed**, including the Section 8
slider test and the Chapter 5 Ridge/Lasso check, for the first time in this
whole saga. The run still failed, but one step later, at "Execute the
portable notebook outside the repository" — a step no prior run had ever
reached.

### 5. `dcc5365` — a genuinely new, unrelated bug, found and fixed

`scripts/smoke_portable_notebook.py` executes each chapter's portable
notebook with a clean `nbclient` kernel and checks that a handful of
deterministic strings appear in its output. Its `chapter_02` entry expected
8 substrings; 7 of 8 did not appear. Diagnosed by reading the portable
notebook's actual cell source directly (not guessing from the truncated CI
log, which is capped at 4000 characters) and cross-checking against the
real captured CI output:

| Old expected string | What's actually true |
|---|---|
| `"age available for 1004 of 1004"` / `"n_features = 360"` | Reworded to `"1004 participants, 360 brain predictors"` |
| `"k = 20"` | Never printed as such |
| `"held-out R^2 = 0.664"` | `0.664` only exists as `EXPECTED_KNN_R2` inside the guarded KNN-check cell's *success* branch, which cannot fire in a distributed (intentionally blank) student portable notebook — it always takes the `"Not complete yet: define knn_pred, knn_r2, and knn_mse above first."` branch instead |
| `"fitting participants (N_fit) = ... (N_val) = 189"` | Reworded to the unlabeled `"fitting participants = 564   validation participants = 189"` |
| `"every validation prediction equals the fitting-set mean"` | This was multiple-choice *feedback* text that only renders on a user click — structurally unreachable by a headless `nbclient` run regardless of wording |
| `"n_features (p) = 10"` | No matching content exists anywhere in the current notebook |

Most of this drift almost certainly dates to WP42 Gate 1's "KNN check"
polish, which converted a fully-worked KNN example into a guarded,
checked student exercise cell. It went undetected because this is the
**first CI run in the entire WP41→WP43RR history to ever reach this step**
— every prior run failed earlier, at the browser-test step this same
session's first four commits fixed.

Rewrote the `chapter_02` expected-strings tuple to match the notebook's
real, already-independently-verified-correct current behavior (the OLS
`R^2 = 0.469` result is the same number asserted throughout
`exercise-02-lite.spec.ts` and every prior WP report — unchanged, not
touched). Also corrected the file's own header comment, which claimed a
prior "bounded run... against chapter_02... never completed within 100s"
due to an `ipywidgets.Output()`/nbclient hang — this run's real CI evidence
(chapter_02 completed in ~4 seconds, no hang) contradicts that specific
claim for chapter_02 (chapter_01's own separate exclusion was not
re-verified and is left in place).

No notebook content was changed anywhere in this arc. Only test
infrastructure (wait timings, capture settings, a stale test's own
expectations) was touched.

**CI result**
([`36566657471`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/36566657471)):
**every step passed, including `Publish website`.**

## Why the middle three commits look like a detour

Commits 2 and 3 (`17b13fc`, `596ef9b`) did not fix the bug, but they were
not wasted motion: each was a real, evidence-based hypothesis, tested
against real CI runs, and *disproved* by real CI evidence (an identical
numeric failure recurring is itself strong information) rather than
assumed away. Ruling out video overhead and cross-worker contention with
hard evidence is what made `trace` the last, correct remaining suspect.

## What was NOT done

- The course author's separate authorization to archive Exercises 3-12 and
  publish only 1 and 2 was explicitly conditioned on a failure "on the
  Chapter 5 legacy test." That failure mode was fixed by `4d19fbb` and did
  not recur in the final run — so that restructuring was correctly never
  triggered. All 12 chapters remain published, unchanged.
- No test was disabled, skipped, or weakened for Exercise 1 or Exercise 2
  at any point in this arc, per the course author's explicit instruction.
- No force-push. `Homework_Materials/` and all unrelated work were
  untouched throughout.

## Verification of the live deployment

### Confirmed via automated real-browser CI (gates every deploy)

The 149-test Playwright suite that passed on `dcc5365` includes, against
the actual combined book + JupyterLite build served over real HTTP:

- Exercise 1 and Exercise 2: kernel start, same-origin data load, supplied
  cells reproducing the established numeric results, one native
  ipywidgets/Matplotlib widget operable per notebook (Exercise 1's
  retention/histogram explorer; Exercise 2's Section 8 k-slider), one
  checked question graded correctly per notebook, a written-answer/code
  edit surviving save → reload → **Download my notebook** with the edit
  present in the downloaded bytes, Reset-restores-template + Back-to-
  Contents, zero horizontal overflow at 390px, and dark-mode legibility.
- The transition pages under the real `/ml-neuro-tutorials/` Pages
  subpath, confirming the "Open Exercise 1/2" links actually open the
  JupyterLite working copy in production-equivalent conditions.
- Every legacy (unmigrated) chapter's embedded activities, confirming the
  hub and Exercises 3-12 are intact and unaffected.

### Confirmed directly, this session, against the live production site

Static HTTP/content checks (not a live interactive browser session — see
limitations below) after the deploy:

| Check | Result |
|---|---|
| `https://yoavmp.github.io/ml-neuro-tutorials/` | `200` |
| `.../contents.html` | `200`, lists all 12 chapters unchanged |
| `.../chapters/chapter_01/exercise_01.html` | `200`, contains `href="../../lite/notebooks/index.html?path=exercise_01.ipynb"` |
| `.../chapters/chapter_02/exercise_02.html` | `200`, contains `href="../../lite/notebooks/index.html?path=exercise_02.ipynb"` |
| `.../lite/notebooks/index.html` (JupyterLite app root) | `200` |
| `.../lite/notebooks/index.html?path=exercise_01.ipynb` | `200` |
| `.../lite/notebooks/index.html?path=exercise_02.ipynb` | `200` |
| `.../lite/files/exercise_01.ipynb` (student template, same-origin download source) | `200` |
| `.../lite/files/exercise_02.ipynb` | `200` |

`origin/gh-pages` confirmed advanced:
`05ceb13e4467616c72b0033e6990da8ce5d162d6`
(`deploy: dcc53655b8e4b3eac67ba741e165ff6bbbf0cf3d`).

### Limitation, stated plainly

This session's own live-site check was static (HTTP status and HTML
content inspection), not an interactive browser session — no tool in this
session can drive a real browser to click through the site, start a
Pyodide kernel, and operate the Section 8 slider live. The interactive,
real-Chromium-browser verification of exactly that behavior happened as
part of the CI gate that blocked this deploy until it passed (see above,
149/149). If the course author wants a first-hand interactive check, the
direct links above are ready for that.

## Deployed state

- `origin/main`: `dcc53655b8e4b3eac67ba741e165ff6bbbf0cf3d`.
- `origin/gh-pages`: `05ceb13e4467616c72b0033e6990da8ce5d162d6`
  (`deploy: dcc5365`).
- Live: <https://yoavmp.github.io/ml-neuro-tutorials/>
- Exercise 1: <https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html>
- Exercise 2: <https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_02/exercise_02.html>

## Deviations from the originating WP text

This report supersedes the "stop and report" scope of `WP43RR` per the
course author's explicit follow-up authorization to diagnose, fix, and
deploy without returning after each attempt. Five push/CI cycles were run
in total this session; the course author asked for exactly this and to be
updated at the end, not after each one.
