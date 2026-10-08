# WP50 report: change-aware testing and deployment for the course notebooks

## Scope and starting state

Starting SHA (local and remote `main`, already in sync): `9597f8d` ("WP49:
record the final CI run that confirmed the paths-ignore fix").

Checkpoint branch: `checkpoint/wp50-pre-work`, at that same tip, created
before any WP50 edit.

No feature branch was created: the whole implementation landed as one
commit, made directly on `main` after full local verification (see
"Verification" below) and before the single production push the spec
asks for. See `WPs/reports/WP50_EXACT_CHANGELOG.md` for the exact commit
and its full file list.

No change to Exercises 1–8's teaching content anywhere in this WP.
Exercises 9–12 remain exactly as WP49 left them: legacy source, preserved,
unpublished, and — a deliberate scope decision, not an oversight — **not**
fast-pathed by the new classifier (see "Deviations" below).

## What was read first

`WPs/reports/WP49_REPORT.md` in full, especially §G (the deploy-workflow
fixes WP49 itself made) and §H (the testing policy this WP implements);
`WPs/reports/WP49_EXACT_CHANGELOG.md`; the live `.github/workflows/
deploy.yml` and `.github/workflows/legacy-notebook-smoke.yml`; every
`scripts/generate_exercise_0N_{notebook,transition_page}.py`; `scripts/
build_portable_notebook.py` and `scripts/smoke_portable_notebook.py`;
`book/config/exercise_manifest.json` and `tests/test_exercise_manifest.py`;
`book/_config.yml`/`book/_toc.yml`; `interactive/playwright.book.config.ts`
and the `interactive/e2e-book/` and `interactive/src/` trees; and the
`gh-pages` branch's own commit history (`git log origin/gh-pages`), to
confirm how `peaceiris/actions-gh-pages` actually records its source SHA
before designing anything around it.

## A. The comparison base: reusing `gh-pages`'s own marker, not inventing a new one

`git log origin/gh-pages` shows every one of its commits is already
`deploy: <40-hex-sha>` — `peaceiris/actions-gh-pages`'s own default commit
message, written only by the "Publish website" step, which is the last
step in `deploy.yml` and runs with no `continue-on-error`/`if: always()`.
That means:

- a failed or cancelled run never touches `gh-pages` at all, so it can
  never become the new base, by construction, with no extra bookkeeping
  needed;
- the marker already carries the exact source SHA as a full, unambiguous
  40-hex string — no need for a new file, tag, or release asset.

`scripts/classify_release_change.py`'s `resolve_base()` reads
`origin/gh-pages`'s HEAD commit message, requires it to match
`deploy: <40-hex-sha>` exactly, requires that SHA to be a reachable commit
object in the checkout, and requires it to be an ancestor of the current
head — any failure at any of those three steps (missing ref, corrupt
message, unreachable object, or non-ancestor/force-push) is reported as
**untrustworthy**, which forces the full gate. No new infrastructure was
added to gh-pages publishing itself; this is the "use a robust, explicit
marker going forward if necessary" clause resolved as "it already is
one."

## B. The classifier (deliverable 1)

`scripts/classify_release_change.py` (525 lines, one file, stdlib only —
`argparse`/`json`/`re`/`subprocess`/`dataclasses`/`pathlib`, no pip
dependency, so the CI `classify` job doesn't even need `pip install`).
Computes, in order: the comparison base and its trust; `git diff
--name-status -M base head`, with a rename contributing **both** its old
and new path to classification (no changed path is ever silently
dropped, including a rename into an unrecognized name); each path's class
(`wp_docs`, one exercise's own scoped surface — 1–8 only, by an explicit
allowlist of path patterns, not a keyword guess; `shared`; or `unknown`);
and, only when every non-doc path is exercise-scoped, a prose-only
verification per touched exercise.

**Prose-only verification compares the actual generated notebooks**, per
the spec's explicit requirement — not the generator source, not a commit
message. For each touched exercise, it diffs five committed artifacts
between base and head (the JupyterLite template, its lite-served portable
copy, the downloads portable copy, the transition page, the reference
notebook): cell count and type sequence must match; every code cell's
`source` must be byte-identical; every cell's `id`/`metadata` and every
code cell's `outputs`/`execution_count` must be unchanged; the
notebook-level `metadata` (kernelspec, `wp41.templateVersion`, etc.) must
be unchanged. Only markdown-cell `source` may differ. A changed string
inside a code cell — the spec's own named example, a multiple-choice
label — fails this and escalates, exactly as required.

Output: a human-readable report (base + trust + reason; every changed
path with its class; the prose verdict per touched exercise; the final
gate and reason) and the identical information as JSON, plus
`--github-output` support for `gate=`/`exercises=`/`reason=`. Both forms
are produced by the same run — no separate "CI mode" and "local mode"
logic to drift apart.

## C. The deployment workflow (deliverable 2)

`.github/workflows/deploy.yml` gained a `classify` job (checkout,
`git fetch origin gh-pages --depth=1 || true`, run the classifier) that
`build-and-deploy` depends on and reads `needs.classify.outputs.gate`
from. `build-and-deploy` itself:

- Only runs at all when `gate != 'skip'` (job-level `if:`).
- Always runs: checkout, Python/Node setup, dependency installs, the
  course-toolbar JupyterLite-extension build (needed by every gate that
  builds the site at all), the two cheap offline data-artifact `--check`
  steps, the Jupyter Book build, the execution-error check, and the
  JupyterLite build. **The combined build and publish mechanism are
  unchanged** — same commands, same order, same `peaceiris/actions-
  gh-pages` publish step, run exactly once per non-`skip` push, per the
  spec's explicit "keep this one-way" requirement.
- Only for `gate == 'full'`: frontend typecheck/unit/audit, building the
  standalone widget app, the blanket 01–08 generator-staleness loop, the
  full offline `python -m unittest discover`, the portable-notebook
  staleness check, the standalone widget app's own Playwright run, the
  full `npm run test:e2e:book`, and the chapter_02 real-kernel portable
  smoke. This is the entire pre-WP50 pipeline, untouched, still gated the
  same way it always ran — just now conditional instead of unconditional.
- Only for `gate in (prose, exercise)`: two new steps calling
  `scripts/run_selected_checks.py --phase pretest` (before the build) and
  `--phase postbuild` (after it) — see deliverable discussion below.
  `exercise` additionally gets `Install Playwright Chromium` (shared with
  `full`).
- `Upload Playwright failure evidence` now only fires for gates that
  could actually have produced Playwright output (`full`/`exercise`).

No manual "skip tests" switch exists anywhere in the file — the spec
explicitly forbids one, and the only way to reach a narrower gate than
`full` is for the classifier to actually verify it.

## D. The full-regression and legacy-smoke workflows (deliverable 3)

`.github/workflows/full-regression.yml` (new): `workflow_dispatch` only,
mirrors `deploy.yml`'s full-gate steps end to end, **has no publish step
anywhere in the file** — not merely skipped by a condition, structurally
absent, so nothing it does can ever change the live site. No `schedule:`
trigger: the full suite is a genuine ~20–30 minute local / ~1.5–2 hour CI
run (WP49 §D), not the spec's "inexpensive enough" bar for an automatic
recurring run; `workflow_dispatch` keeps it available on demand instead,
which is what the spec calls the acceptable fallback when a schedule
isn't warranted.

`.github/workflows/legacy-notebook-smoke.yml` (Exercises 9–10,
`workflow_dispatch` + its own narrow path trigger): **untouched** — it
already satisfied "preserve the on-demand legacy Exercise 9–10 smoke
workflow" exactly as WP49 left it.

## E. The targeted smoke check, and a real bug it caught early

`scripts/smoke_release_routes.py` checks, per exercise, against an
already-built `book/_build/html`: the transition route exists and
contains the right "Open Exercise N" link and `liteUrl` reference; the
JupyterLite template is valid non-empty notebook JSON; the portable
download is valid non-empty notebook JSON.

**Found during this WP's own local dry-run, before any push**: the first
version read the portable-download path from `exercise_manifest.json`'s
`fallbackDownloadablePath` (`downloads/chapter_0N/...`) — which is wrong.
`book/_config.yml`'s own `exclude_patterns` lists `downloads/*`
specifically so Sphinx never treats it as a source doc, which also means
it is **never copied into `book/_build/html` at all**. The actual served
download link, confirmed against the transition page generator's own
`DOWNLOAD_URL` constant and against WP49's own live-site verification
(which checked `lite/files/exercise_03_portable.ipynb`, not a
`downloads/` URL), is `lite/files/exercise_0N_portable.ipynb`. Running the
script against a real local build caught this immediately (every
exercise's "portable download" check failed with a `downloads/` path
that was simply never written); fixed to check the real served path
before any CI run ever saw it. `fallbackDownloadablePath` remains exactly
what its own name says — the repo-relative source path the generator
writes to — and is used only for that, nowhere near the smoke check.

## F. The classifier's own test suite (deliverable 5 prerequisite; spec §Verification 1)

`tests/test_classify_release_change.py`, 35 tests, three layers:

1. **Path classification** (no git): generator scripts, lite
   template/portable copies, downloads, test files, and browser specs for
   Exercises 1–8 classify as that exercise; a mismatched chapter/exercise
   number in a download path, a cross-cutting spec
   (`wp22-cross-chapter-dark-mode.spec.ts`), and a brand-new unrecognized
   path all classify as shared/unknown, never silently as "exercise."
2. **Notebook prose-diff** (no git, synthetic notebook dicts): markdown-
   only wording change passes; a code-cell source change, an MC-label
   change *inside a code cell*, a cell-count change, a notebook-metadata
   change, and a code-cell output change each escalate.
3. **Pure gate decisions** (`classify()` with a stubbed prose-checker) and
   **real end-to-end** (`classify_release()`/`resolve_base()` against a
   real, disposable temp git repository — not the project repo) covering
   every scenario the spec names explicitly: a markdown-only edit; a
   code-cell edit; a changed MC label inside a code cell; two exercises
   changing together (both prose stays `prose`; one prose + one code
   escalates the whole push to `exercise`, union of both exercise IDs); a
   shared config/helper change (forces `full` even alongside an
   otherwise-qualifying exercise change); an unknown path; a missing
   gh-pages marker; a corrupt marker; a non-ancestor marker (simulated
   force-push via an orphan commit); and **a prior failed push followed by
   a fix** — built so that diffing against the last *successful* publish
   correctly still catches a shared-path change the failed push
   introduced and the fix commit never touched, while the same comparison
   taken against the merely-previous push (the wrong base) would have
   missed it and wrongly fast-pathed the release. All 35 pass.

## G. The maintainer guide (deliverable 4)

`WPs/reports/WP50_MAINTAINER_GUIDE.md`. Covers: where wording actually
lives (the generator `.py` files, not the canonical-looking `.ipynb`
under `book/chapters/`) and the exact `--write` commands to regenerate
every derived file after editing it; the four-gate table with what each
one runs; why the prose check trusts the generated notebooks and not a
commit message or file-name pattern; three ways to get a full run
(automatic escalation, touching any shared path on purpose, or
`full-regression.yml`) plus the preserved legacy Exercise 9–10 smoke
workflow; how to read why CI picked a gate (the `classify` job's own
outputs and step log); the exact local commands
(`run_selected_checks.py --phase pretest`/`--phase postbuild`) and what
each needs; and an explicit "note on scope" section stating two
deliberate simplifications so a future reader doesn't mistake them for
bugs: shared-surface changes are never finely attributed to their "actual"
blast radius (any shared path takes the full gate, unconditionally), and
Exercises 9–12 are not fast-pathed (optimizing their gate was out of
scope here).

## Verification

### 1. Classifier fixtures (spec's explicit list)

All eight named scenarios — see section F above — are covered by real,
passing tests. `markdown-only edit`, `code-cell edit`, `MC-label-in-code-
cell`, `two exercises together`, `shared helper/config change`, `unknown
path`, `missing published-base marker`, and `prior failed push followed
by a fix` each have a dedicated test; the last one explicitly proves the
union-since-last-success property by contrasting the correct base against
the wrong one in the same test.

```
.venv/bin/python -m unittest discover -s tests -p 'test_classify_release_change.py'
# Ran 35 tests in 6.5s — OK
```

### 2. Workflow syntax, job conditions, and the full local gate

`actionlint` was not available in this offline environment; syntax was
validated with `yaml.safe_load` against all three workflow files
(`deploy.yml`, `full-regression.yml`, `legacy-notebook-smoke.yml` —
unchanged, included as a control), and every `needs.classify.outputs.gate`
condition was traced by hand against the job graph. Per the spec's own
instruction ("a local pass does not substitute for watching the actual
GitHub Actions run"), the authoritative syntax/condition check is the real
CI run itself (section below).

This WP touches `.github/workflows/deploy.yml`,
`.github/workflows/full-regression.yml`, and three new `scripts/*.py`
files — a shared/workflow surface by its own classifier's rules — so the
policy it implements requires the **full gate locally**, once, before the
production push:

| Check | Result | Duration |
| --- | --- | --- |
| `python -m unittest discover -s tests -v` (full offline suite, 1133 tests) | OK, 11 skipped | **1357.9s (~22.6 min)** |
| `rm -rf book/_build && jupyter-book build book --all` | success, 2 pre-existing warnings (same baseline as WP49) | ~3 min |
| `jupyter lite build ...` (Exercises 1–8) | success | ~1 min |
| `scripts/smoke_release_routes.py` for all 8 exercises against the clean build | all 8 OK | <1s |
| `npm run test:e2e:book` (full suite, default parallelism) | **102/103 passed** | **30.6 min** |
| Isolated rerun of the one failing file (`exercise-06-lite.spec.ts`, `--workers=1`) | **7/7 passed** | 8.1 min |

The one full-suite failure (`exercise-06-lite.spec.ts`: "the Build a Tree
Greedily activity locks and reveals the root split") reproduced exactly
the cross-test CPU-contention pattern WP49 §D.1 already documented for
this same default-parallelism configuration — WP50 touches zero exercise
or widget code, so there is no plausible mechanism by which it could have
introduced a new Exercise-6 regression, and the isolated rerun (7/7,
including that exact test) confirms it. Not rerun a third time: per the
local working policy, there is no specific reason to distrust the
isolated result, and repeating an already-explained flake "just in case"
is exactly the cost-without-risk-reduction pattern WP49 §H warns against.

Every one of these checks exceeded five minutes except the smoke check;
each is reported above with its actual measured duration, not an
estimate.

### 3. One controlled production push

`git push origin main` (`9597f8d..2ec83cc`) — see "Deployment, CI, and
live-site verification" below for the real run, watched through
completion, and the live-site checks taken afterward.

### 4. The new fast path, proven locally without a second production push

On a disposable branch (`wp50-fastpath-fixture-demo`, created from the
pushed commit `2ec83cc`, never pushed, deleted immediately after):
changed one sentence inside `scripts/generate_exercise_01_notebook.py`'s
overview markdown ("a checked question **with** immediate feedback" →
"**for** immediate feedback" — purely cosmetic, zero code/logic change),
ran `--write` for both of Exercise 1's generators, committed
(`5755fd7`).

```
$ .venv/bin/python scripts/classify_release_change.py --base-ref 2ec83cc... --head-ref HEAD
...
affected exercise IDs: [1]
GATE: prose
reason: every touched exercise's generated notebooks differ only in markdown wording
```

```
$ time .venv/bin/python scripts/run_selected_checks.py --phase pretest --base-ref 2ec83cc... --head-ref HEAD
... generator --check (x2), test_exercise_01_lite_notebook.py (31 tests), test_exercise_01_transition_page.py (8 tests)
pretest phase: 4/4 checks passed in 5.5s
```

Rebuilt (incrementally — `jupyter-book build book`: 3.0s; `jupyter lite
build`: 4.6s, both reusing the unaffected pages' cache) and ran the
postbuild phase:

```
$ time .venv/bin/python scripts/run_selected_checks.py --phase postbuild --base-ref 2ec83cc... --head-ref HEAD
+ smoke_release_routes.py --exercises 1
OK: exercise 1 route, JupyterLite template, and portable download all smoke-check clean
postbuild phase: 1/1 checks passed in 0.1s
```

No kernel execution, no Playwright, no browser at all — confirmed by
reading the commands actually run above, not merely by the gate label.
Independently confirmed (via direct JSON inspection) that the new wording
really is present in both the regenerated source notebook and the rebuilt
served output, so this is a genuine fast-path run against real new
content, not a no-op. The branch was then deleted and `main` restored to
a clean working tree before the production push — this demonstration
never touched, and is not part of, the pushed history (see
`WP50_EXACT_CHANGELOG.md`'s note on the `5755fd7` SHA).

**This is a simulation, not production proof of the fast path** — stated
explicitly, as the spec requires: the real CI `classify` job has not yet
been exercised on a `prose`- or `exercise`-gated push (this WP's own
introducing push is unavoidably `full`, by its own rule, since it changes
the workflow files themselves). The local classifier and
`run_selected_checks.py` are the exact same code CI runs, invoked the
same way, which is the strongest evidence available without manufacturing
a second, unnecessary content change purely to trigger another
deployment — which the spec explicitly forbids doing.

## Deployment, CI, and live-site verification

**CI run**: [`37793260325`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/37793260325)
— **success**, start to finish in **1h45m33s** (`2026-10-08T14:32:09Z` →
`2026-10-08T16:17:42Z`), watched through completion via `gh run view`
(status polled every 5 minutes; step-level detail pulled whenever a status
update was due), not merely assumed green from a final notification.

**The new `classify` job worked exactly as designed, on the very first
real run**:

- `classify`: success in 9s. This WP's own commit touches
  `.github/workflows/deploy.yml`, `.github/workflows/full-regression.yml`,
  and three new `scripts/*.py` files — all `shared` by the classifier's
  own rules — so it correctly produced `gate=full`, satisfying the spec's
  "ensure the first run introducing this workflow takes the full gate"
  requirement without that rule needing to be special-cased anywhere.
- `build-and-deploy`'s two new conditional steps both show
  **`completed/skipped`** in the real run — `Run change-aware pretest
  checks (prose/exercise gate only)` and `Run change-aware browser + route
  smoke checks (prose/exercise gate only)` — confirming the `if:` wiring
  against `needs.classify.outputs.gate` actually works in GitHub Actions,
  not just in the local `yaml.safe_load` check.
- Every pre-existing full-gate step ran and passed, unchanged: frontend
  typecheck/unit/audit/build, both offline data-artifact checks, the
  01–08 generator-staleness loop, the full offline Python suite
  (**24m39s**, `14:34:20`→`14:58:59`), the portable-notebook staleness
  check, the standalone widget app's Playwright run, the Jupyter Book
  build, the execution-error check, the JupyterLite build, the full
  `npm run test:e2e:book` (**1h16m24s**, `15:01:04`→`16:17:28`, **zero
  failures** — CI's own `workers: 1` cap avoids exactly the cross-test
  contention that caused this WP's one local flake), the chapter_02
  portable-notebook kernel smoke, and finally **Publish website**
  (success, 4s).

**Live-site verification**, done against the real served site, after
confirming the publish step succeeded (not assumed from the workflow's own
"success" status):

```
$ git fetch origin gh-pages --depth=1 && git log -1 --format='%H %s' origin/gh-pages
4cf07c1... deploy: 2ec83cc384e4699611f8106963d7ff480f9cdf86
```

— the `gh-pages` marker matches this WP's own pushed commit exactly.

```
contents.html:                              200
chapters/chapter_01/exercise_01.html:       200, contains "Open Exercise 1"
chapters/chapter_09/exercise_09.html:       404  (legacy exclusion still in effect)
lite/files/exercise_01.ipynb:               200  application/x-ipynb+json
lite/files/exercise_01_portable.ipynb:      200  application/x-ipynb+json
```

Site is live and correct; nothing about Exercises 1–8's publication or
Exercises 9–12's exclusion changed as a side effect of this WP, as
required.

## Deviations and pending items

- **`fallbackDownloadablePath` vs. the real served download URL** (section
  E): not a deviation from the spec, but worth flagging as the kind of
  thing a future WP should not re-assume — the manifest field describes
  where the generator *writes* the portable notebook in the repository,
  not where the published site *serves* it from.
- **Shared-surface changes are not finely attributed.** The spec's
  `exercise` row says "plus tests for any actually affected shared
  component" — this WP's classifier instead always escalates any
  shared-path change straight to `full`, never attempting to compute a
  shared surface's precise blast radius. Simpler, more maintainable, and
  strictly more conservative; documented as a deliberate design choice in
  the maintainer guide (§7), not a gap.
- **Exercises 9–12 are not fast-pathed.** Their source changes still take
  the full gate, exactly as before this WP (they already triggered the
  full `deploy.yml` with no path filter, since WP49 only excluded them
  from the *published build*, not from the workflow's trigger). Optimizing
  their gate was never in this WP's scope ("preserve... their existing
  publication status").
- **The new fast path is simulated, not yet production-proven** — see
  Verification §4 above; this is stated as a limitation, not papered over.
- `actionlint` was unavailable offline; workflow correctness rests on
  `yaml.safe_load` + manual job-condition tracing + the real CI run below,
  not a dedicated linter.
- Working tree is clean at the end of this WP; the only artifacts left
  behind are the two new report files themselves and the checkpoint
  branch `checkpoint/wp50-pre-work` (unpushed, local only, matching every
  prior WP's own convention).

## Remaining wall-clock work, wording edit vs. code edit

**Baseline (unchanged, `full` gate)**: ~1h45m end to end in CI (measured,
this WP's own introducing run), ~20–30 min + ~5 min build locally with
default Playwright parallelism (measured, section Verification §2).

**A wording-only edit to one exercise (`prose` gate)** — **measured
locally** (Verification §4): `classify` is near-instant;
`run_selected_checks.py --phase pretest` **5.5s**; incremental
`jupyter-book build book` **3.0s**; incremental `jupyter lite build`
**4.6s**; `run_selected_checks.py --phase postbuild` **0.1s**. Total
measured local compute: **~13 seconds**, down from the ~20–30 minute full
local gate. For CI specifically, this gate has not yet been exercised in
production (this WP's own push was unavoidably `full`, by its own rule —
see §4's explicit caveat); extrapolating from this run's own measured
fixed overhead (checkout + Python/Node setup + `npm ci` + the
course-toolbar extension build, measured at **79s** before any
content-dependent step even starts) plus the ~13s of actual checks and
build and the ~5s publish step, a `prose`-gated CI run is **estimated at
roughly 1.5–2 minutes**, versus ~1h45m today — labeled an estimate because
it is extrapolated from this run's real per-step timings, not itself
measured on a `prose`-gated CI run.

**A real code/content edit to one exercise (`exercise` gate)** — not
separately measured end-to-end this WP (constructing a throwaway code-level
fixture and running its real Playwright spec would cost real minutes for a
number already well-characterized by WP49 §D.4's own per-exercise
measurements); **estimated** from this run's measured fixed overhead
(79s) + the `exercise` gate's own small additions (generator `--check` +
structural + reference-execution tests, each low single-digit seconds per
WP49's own numbers; `Install Playwright Chromium`, measured at **36s** in
this very run) + **that one exercise's own** `exercise-0N-lite.spec.ts` +
`chapterNN.spec.ts` run time, which WP49 §D.4 already measured in isolation
per exercise and ranges from **~2.6 minutes** (Exercise 1) to **~32.6
minutes** (Exercise 7) + the ~5s build and ~5s publish steps. So: roughly
**4–35 minutes total, depending on which exercise**, versus ~1h45m today —
also an estimate, for the reason above, though built from real measured
components rather than guessed from scratch.

Both gates are real, large reductions from the unconditional full gate;
neither claim is asserted as CI-production-proven beyond what Verification
§3–4 and the section above actually show.
