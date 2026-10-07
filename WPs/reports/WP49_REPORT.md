# WP49 report: deploy the JupyterLite versions of Exercises 1–8

## Scope and starting state

Starting SHA (local `main`): `2043fe4` ("WP48: reports — execution report
and exact changelog"), the tip of
`feature/wp48-questions-and-exercises-1-4-polish`.

Checkpoint branch: `checkpoint/wp49-pre-work`, at that same tip (created
before any WP49 edit was made).

Feature branch: `feature/wp49-deploy-jupyterlite-exercises-1-8`, created
from that same tip.

**Branch reconciliation, done first, without losing or force-pushing
anything:**

- Local `main` was at `02c389d` ("WP43 deployment fix..."), one commit
  *ahead* of `origin/main` (`dcc5365`) — that single commit had never been
  pushed.
- `feature/wp44-colab-portability-exercise-3` through
  `feature/wp48-questions-and-exercises-1-4-polish` were five branches in a
  strict linear chain, each created from the previous one's tip, starting
  from local `main`'s own tip (`02c389d`) — confirmed via `git merge-base
  --is-ancestor` and inspecting each branch's merge-base with `main`
  before touching anything. None of them had ever been merged back into
  `main`; none of this work had reached GitHub.
- This meant reconciliation required no merge and no conflict resolution:
  `main` only needed a fast-forward to WP49's own tip, done as the very
  last step (see "Merge and push" below) — never a destructive rewrite of
  any branch.

No `Homework_Materials/` changes anywhere in this WP.

## What WP48 had already built, and what was still missing for a real release

WP44–47 had already migrated Exercises 3–8 to JupyterLite-native
notebooks and built their book pages (a thin "Open Exercise N" transition
page, exactly like Exercises 1–2), but deliberately left
`book/config/exercise_manifest.json`'s `migrationState` at `"legacy"` for
3–8, pending the author's own real-Colab acceptance gate
(`WP41_MAINTAINER_GUIDE.md` §11). WP48 then migrated all seven
(`show_question` answer-key concealment) and fixed Exercises 1–4's
itemized issues, including Exercise 4's radio-label CSS overlap — but
explicitly scoped that one fix to Exercise 4 only, flagging (not fixing)
the identical gap in Exercises 1, 2, 3, 5, 6, 7, 8. Nothing had been
merged, pushed, or deployed, and the combined Jupyter Book + JupyterLite
Playwright suite had never been run across all eight exercises at once —
WP46 and WP47 each explicitly deferred that ("one comprehensive suite
later, once every notebook is migrated").

WP49's job: finish that — flip the manifest, scope the public hub to
Exercises 1–8, port the CSS fix everywhere, run the comprehensive gate for
real, fix whatever it found, and publish.

## A. Radio-label CSS fix ported to Exercises 1, 2, 3, 5, 6, 7, 8

Added the identical `height: auto !important; padding: 3px 0; line-height:
1.3;` properties WP48 added only to Exercise 4's `.checked-question
.widget-radio-box label` rule (Exercise 1 uses the equivalent
`.wrap-labels` class) to the same duplicated CSS block in the other seven
generators. Regenerated every derived notebook (`--write`) and confirmed
`--check` reports all eight back in sync. Added
`test_question_radio_labels_do_not_clip_wrapped_rows` (mirroring WP48's
own Exercise-4 test) to each of the other seven
`tests/test_exercise_0N_lite_notebook.py` files.

Live-browser confirmation: both desktop and 390px narrow-viewport checks
passed for every exercise's question widgets as part of the full combined
Playwright run (section D below) — no visual overlap observed anywhere.

## B. Exercise manifest: Exercises 3–8 flipped to `migrationState: "migrated"`

This is the actual deployment decision this WP exists to make. The
author's own authorization is explicit: *"I authorize this deployment
with real-Colab acceptance of the revised notebooks still pending."*
Flipped `migrationState` to `"migrated"` for Exercises 3–8 and filled in
each entry's `templateNotebookPath`, `browserWorkingCopyName`, `liteUrl`,
`templateVersion` (all `1`, read from each notebook's own
`metadata.wp41.templateVersion`), and `dataAssets` (the actual CSV/JSON/
PNG files each notebook's generator loads). Rewrote the manifest's own
`$comment` to state plainly that `migrationState: "migrated"` here
reflects what is actually published, not a claim that the Colab gate has
passed. Updated `tests/test_exercise_manifest.py`'s
`test_only_exercises_1_and_2_are_migrated` →
`test_only_exercises_1_through_8_are_migrated`, asserting migrated =
`[1..8]`. All ten manifest tests pass.

## C. Public hub scoped to Exercises 1–8; Exercises 9–12 preserved, not published

1. `book/_toc.yml`: removed `chapters/chapter_{09,10,11,12}/exercise_*`
   from the toctree.
2. **Found live, not assumed**: a first attempt (toc-only) still left
   `chapter_09/exercise_09.html` etc. reachable in `book/_build/html` —
   `jupyter-book`'s incremental build does not delete orphaned output
   directories when a page is only dropped from the toctree, it just stops
   updating them. Fixed properly by adding
   `chapters/chapter_{09,10,11,12}/*` to `book/_config.yml`'s
   `exclude_patterns` (the same mechanism already used for
   `downloads/*`/`lite/*`), which drops them from Sphinx's source set
   entirely. Verified with a **clean** rebuild (`rm -rf book/_build &&
   jupyter-book build book --all`): only `chapters/chapter_0{1..8}` exist
   in the output; build succeeded with 2 pre-existing warnings (down from
   6).
3. Exercises 9–12's own source (`book/chapters/chapter_09..12/*`,
   `book/downloads/chapter_09..10/*`) and git history are completely
   untouched — only excluded from the published build. See "Local viewing
   of Exercises 9–12" below for how to inspect them.
4. `tests/test_book_structure.py`: replaced
   `test_exercises_one_through_twelve_follow_in_order`/
   `test_no_exercise_13_in_toc` (which asserted all 12 in the toc) with
   `test_exercises_one_through_eight_follow_in_order` (asserts the
   published order) and a new
   `test_exercises_nine_through_twelve_source_preserved_but_not_published`
   (asserts 9–12 are **absent** from the toc **and** their source files
   **exist on disk** — a direct, enforced guarantee of "preserved, not
   deleted").
5. `interactive/playwright.book.config.ts`: added `testIgnore` for
   `chapter09.spec.ts`, `chapter09-dark-mode.spec.ts`, `chapter10.spec.ts`,
   and `iframe-height-contract.spec.ts` — each exists only to exercise
   pages that no longer exist in the build (would fail on a 404, not a
   regression). Excluded, not deleted: their source stays for whenever
   Exercises 9–12 are migrated and republished.
6. `interactive/e2e-book/launch-buttons.spec.ts`: removed its Chapter
   9/10 admonition-link test cases and its Chapter-11-placeholder case
   (same reason — those pages no longer exist); fixed the resulting
   unused-`REPO`-constant TypeScript error.

This is a genuine descope decision, not a weakened test: the iframe tests
for Exercises 9–10 are "unrelated" to this release in the precise sense
the task named — they test a legacy experience this WP is deliberately
choosing not to publish, not a regression in anything Exercises 1–8 do.

## D. The first-ever full combined Playwright run, and what it took to turn genuinely green

Built the combined site once (`jupyter-book build book --all` on a clean
`_build/`, then `jupyter lite build --config
book/lite/jupyter_lite_config.json --lite-dir book/lite --output-dir
book/_build/html/lite`) and ran `npm run test:e2e:book` — the complete
suite across all eight migrated exercises' `exercise-0N-lite.spec.ts`
files, every `chapterNN.spec.ts` transition page, `launch-buttons.spec.ts`,
and `wp22-cross-chapter-dark-mode.spec.ts` — for the first time ever. WP46
and WP47 had each explicitly deferred this exact run ("one comprehensive
suite later, once every notebook is migrated"); this is that moment.

### D.1 Local run 1 (default full parallelism): 95 passed, 8 failed, 20.6 min

Diagnosed every failure individually:

1. **A real stale assertion** (not contention): `wp22-cross-chapter-dark-
   mode.spec.ts`'s Exercise 4 case still checked for `.ml-ncv-diagram`, the
   raw-HTML nested-CV diagram WP48 replaced with a rendered PNG attachment
   — this test was simply never run again after that WP48 change landed.
   Fixed to check for the new `<img alt="Nested cross-validation
   diagram...">` instead.
2. **A real, deterministic timeout bug**: the same file's Exercise 7 case
   set `test.setTimeout(180_000)` but then spent that *entire* budget on
   its own first `page.waitForTimeout(180_000)` — a guaranteed failure on
   every run. Bumped to `240_000`.
3. **Apparent cross-test contention**: the remaining 6 failures (Exercise
   1, Exercises 4/6's teacher-completed paths, three in Exercise 7) each
   passed when their file was rerun completely isolated (`--workers=1`).
   Capped CI (only) to `workers: 1` and widened Exercise 7's two
   widget-interaction tests' margins (1.5s→3s wait, 5s→20s assertion
   timeout) based on a diagnostic showing the widgets genuinely work, just
   occasionally slower than those margins allowed.

A local full-suite rerun under the *same* full-parallelism config then
reconfirmed the wp22 fix but still showed the same 6 "contention"
failures — consistent with the hypothesis, not yet proof the CI-only
worker cap would be enough.

### D.2 First real CI run (`workers: 1`, serialized): 98/103 passed, 1.9h, then 102/103, then 99/103

This is the part the task explicitly warned against assuming: **a local
pass is not a CI pass.** Three real pushes to `main`, three real GitHub
Actions runs, each inspected via `gh run view --log-failed` rather than
guessed at:

- **Run 1** (`37279360563`, 1.9h): 5 failed — Exercise 4's teacher-
  completed test and all four of Exercise 7's dependent tests, even
  though the exact same margin fix had just passed standalone locally.
  Root cause, found by adding `console`/`pageerror`/`crash`/
  `framenavigated` instrumentation and a real completion signal (see
  D.3): the fixed waits (`page.waitForTimeout(140_000)`/`180_000`)
  are **not reliably sufficient at all**, locally or on CI, independent
  of contention — a margin tweak was treating the symptom, not the
  cause.
- **Run 2** (`37312844957`, 2.1h): 4 failed, all now in **Exercise 6**
  (a file the margin fix never touched) — the identical symptom in a
  *different* exercise, proving the problem was never exercise-specific.
- **Run 3** (`37445520518`): **green in full**, 1h44m, including
  "Publish website." This is the run that actually shipped.

### D.3 The real fix: poll JupyterLab's own kernel-status attribute instead of guessing a duration

Replaced every fixed `page.waitForTimeout(140_000..180_000)` immediately
after clicking "Run All Cells" (across all eight `exercise-0N-
lite.spec.ts` files and five of `wp22-cross-chapter-dark-mode.spec.ts`'s
six cases) with a poll on
`.jp-Notebook-ExecutionIndicator[data-status]` — JupyterLab's own
semantic kernel-status attribute (`unknown` → `busy` → `idle`), confirmed
live by watching it transition across a real "Run All Cells" with a
instrumented diagnostic script. This is environment-independent: it
waits exactly as long as the kernel is actually busy, on any machine,
under any load, rather than assuming a duration that happened to be
measured once. It is also faster in the common case — e.g.
`exercise-01-lite.spec.ts` dropped from 14.9 min to 2.6 min,
`exercise-06-lite.spec.ts` from ~15.2 min to 9.1 min, once the poll could
exit as soon as the kernel was actually done instead of always burning
the old fixed budget.

**One real exception, found by the same instrumented-diagnostic method,
not guessed:** Exercise 3's untouched template is the only one of the
eight whose Section 3 deliberately raises inside a guarded cell (WP44, by
design — the X/y/split activity is intentionally left blank for the
student). JupyterLab's "Run All Cells" halts its run queue at that first
uncaught error rather than scheduling the remaining cells, and a 3-minute
instrumented poll confirmed `.jp-Notebook-ExecutionIndicator` genuinely
gets stuck at `"busy"` afterward — it never reaches `"idle"`. An attempt
to treat a `.jp-mod-error` class appearing as an alternate completion
signal did not work either (the same diagnostic confirmed that class is
never added here; a comment already in the file from an earlier
investigation said so). Kept `exercise-03-lite.spec.ts` and wp22's
Exercise 3 case on their original, already-proven-correct fixed-wait
implementation in full, rather than force a mechanism onto the one
notebook it structurally does not fit. Removed the dead `.jp-mod-error`
fallback condition from the other seven files too, where it was harmless
but based on a disproven premise.

### D.4 Every isolated/standalone verification run, in order

| File | Config | Result | Duration |
| --- | --- | --- | --- |
| `exercise-07-lite.spec.ts` | `--workers=1`, pre-idle-poll (margin fix only) | 7/7 passed | 32.5 min |
| `exercise-04/06/07-lite + wp22` (4 files together) | `--workers=1`, pre-idle-poll | 21 passed, 5 failed (margin-fragile Ex7 pair + wp22 Ex7 timeout bug) | 1.2h |
| `exercise-01-lite.spec.ts` | `--workers=1`, pre-idle-poll | 8/8 passed | 14.9 min |
| `exercise-07-lite.spec.ts` | `--workers=1`, idle-poll | 7/7 passed | 32.6 min |
| `exercise-04-lite.spec.ts` | `--workers=1`, idle-poll (after fixing a second stale anchor, D.5) | 6/6 passed | 3.0 min |
| `exercise-06-lite.spec.ts` | `--workers=1`, idle-poll | 7/7 passed | 9.1 min |
| `exercise-01-lite.spec.ts` | `--workers=1`, idle-poll | 8/8 passed | 2.6 min |
| `exercise-03-lite.spec.ts` | `--workers=1`, reverted to fixed-wait | 5/5 passed | 8.7 min |
| `wp22-cross-chapter-dark-mode.spec.ts` (all 6 cases) | `--workers=1`, idle-poll + Ex3 fixed-wait | 6/6 passed | 7.8 min |

### D.5 A second real stale-anchor bug, found while diagnosing Exercise 4

`exercise-04-lite.spec.ts`'s teacher-completed test's `fillBlank` call
anchored on the literal text `"# cv_fold_mse = ..."` — WP48 (section E.2)
had rewritten that blank's starter comment into a multi-step guidance
block that never contains that string any more, and the test's own
downloaded-notebook check asserted the old placeholder's *absence* (a
vacuous check once that text stopped existing at all). WP48's own report
states it used ad-hoc scripts instead of this committed spec, so this had
never been caught. Fixed the anchor to the still-unique
`"Required names: cv_fold_mse"` and the stale-placeholder check to match
the real current text.

### D.6 Final CI run: green

`https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/37445520518` —
**success**, 1h44m41s, every step including "Publish website." See
`WP49_EXACT_CHANGELOG.md` for the complete step list and the live-site
check that followed it.

## E. A real author-facing content leak, found by the full offline Python suite

Ran `python -m unittest discover -s tests` once (the full 1098-test
offline suite, no network) after porting the CSS fix: **1 failure**,
`test_wp35_content_audit.AuthorFacingLanguageAudit.test_no_author_facing_phrases_in_portable_notebooks`.

WP48's `show_question` migration (Part A) and its threadpoolctl-warning
filter (Exercises 2 and 4) each left a comment inside the hidden setup
cell referencing `"WP48"` and/or `scripts/generate_exercise_08_notebook.py`
by path — this comment travels into the **downloaded/portable student
notebook** for Exercises 1, 2, 3, 4, 5, 6, 7 (confirmed: the setup cell's
source is identical across the JupyterLite template and the portable
copy). This is exactly the kind of author/operator-facing leak WP35's own
audit exists to catch, and it had never been caught because WP48's own
verification never ran this specific test file (its own report lists
`test_wp19/24/25_content_audit` but not `test_wp35_content_audit`).

Reworded all seven comments in plain, student-safe language — no WP
numbers, no internal script paths, same technical content otherwise (zero
behavior change). Regenerated every affected notebook, reran the content
audit (**7/7 pass**) plus a focused 305-test rerun covering every touched
exercise's structural/manifest/numeric suites (**OK, 13.5s**) rather than
repeating the full 21-minute discovery run a second time for a change this
narrow.

## F. Exercise 3's demographics/label loading and portable download — verified, no bug found

Specifically checked, as the task asked: `load_demographics_table()`'s
pinned-fallback path (used when the same-origin sidecar file is absent,
i.e. the portable/Colab case) against the actual regenerated
`book/downloads/chapter_03/exercise_03_portable.ipynb` — confirmed it
falls back to the same pinned, repository-independent third-party URL
`load_abide_classification_table()` already uses, keeping both tables
row-aligned under both paths. All 15
`tests.test_exercise_03_reference_execution` tests (including the 6
`XYCheckCellBehavior` cases) and all 31
`tests.test_exercise_03_lite_notebook` structural tests pass unchanged.
This was WP48's own D.4/D.5 work; WP49 found it correct as shipped, not in
need of a fix.

## G. Deploy workflow updated to reflect what is actually published

`.github/workflows/deploy.yml`:
- "Check the migrated exercise generators are not stale" previously only
  ran `generate_exercise_0{1,2}_{notebook,transition_page}.py --check`.
  Extended to all eight (`01`–`08`).
- The JupyterLite build step's stale comment ("Build JupyterLite
  (Exercises 1 and 2)") corrected to "Build JupyterLite (Exercises 1-8)"
  — the actual `jupyter lite build` command was already unrestricted
  (bundles everything under `book/lite/files`), so this was a documentation
  fix, not a behavior change.

One more step did need touching, found after the deployment itself had
already gone green: `deploy.yml`'s "Execute the portable notebook outside
the repository" step ran `smoke_portable_notebook.py` with no `--notebook`
flag, defaulting to `"all"` — which includes Exercises 9–10's portable
notebooks, legacy content this release deliberately excludes from
`book/_toc.yml`/`book/_config.yml`. A transient failure in either of
those two (unrelated to anything in the published Exercises 1–8 site)
would have blocked this deployment for a reason that has nothing to do
with what is actually being shipped. Scoped that step to
`--notebook chapter_02` — the only Exercise-1–8 notebook this script can
currently smoke-test at all (every other migrated exercise's portable
copy is deliberately excluded from `SMOKE` for the documented
`ipywidgets.Output()`/`nbclient` hang, unrelated to this change) — and
added a new, separate `.github/workflows/legacy-notebook-smoke.yml` that
still runs Exercises 9 and 10's own smoke tests, on demand
(`workflow_dispatch`) or when `smoke_portable_notebook.py` or either
chapter's downloads change, without gating the Exercises 1–8 release.
Verified by a fifth push/CI run (see `WP49_EXACT_CHANGELOG.md`),
successful end to end -- the real final deployment.

One more, found immediately afterward: the sixth push (this report's own
closing commit, touching only `WPs/reports/*.md`) triggered `deploy.yml`
again — it has no path filter, so *any* push to `main` costs the full
~1.5–2h rebuild/redeploy, even a documentation-only one that cannot
change the published site at all. Canceled that run (confirmed safe:
`WPs/` is never read by any script or test at runtime, only referenced
in comments) and added `paths-ignore: ["WPs/**"]` to the trigger — every
WP's own closing report-and-changelog commit going forward no longer
costs a redundant full deploy cycle. This change itself (to
`deploy.yml`, not under `WPs/`) still triggered one final, real CI run
to confirm the trigger change itself works — see
`WP49_EXACT_CHANGELOG.md`.

## H. Testing policy for future single-notebook WPs

Established here, for WP50 and beyond, directly from what this WP's own
multi-hour, multi-run CI cycle cost to discover (D.1–D.3 above): **a
full offline-suite-plus-full-browser-suite rerun is the exception, not
the default, for a change scoped to one notebook.**

- **Test the new/changed notebook and any shared component it touches** —
  that notebook's own `test_exercise_0N_lite_notebook.py` (structural),
  `test_exercise_0N_reference_execution.py` (numeric), and
  `exercise-0N-lite.spec.ts` (live browser) — plus any shared helper,
  CSS block, or generator utility the change actually edited, across
  every exercise that shares it.
- **Do not re-run an older exercise's own structural/reference/browser
  suite** unless the change touched that exercise's generator, a shared
  dependency it imports, or a shared test helper/fixture it uses. A
  change scoped to Exercise N's own file has no mechanism by which it
  could break Exercise M's own already-passing suite; re-running M's
  suite "just in case" is cost without a corresponding risk reduction.
- **Build the combined site once** (`jupyter-book build book --all` on a
  clean `_build/`, then the `jupyter lite build` step) — not once per
  iteration of a fix, and not skipped entirely; the local build is the
  cheap, fast proxy for whether the real CI build will even start.
- **Smoke-test the new notebook's deployed route and its download**
  specifically — its `lite/notebooks/index.html?path=...`, its portable
  `.ipynb` download link, its transition page — against the real local
  build; this is what actually changed, so this is what must be checked
  live, every time.
- **Run an older notebook's own full execution suite only when its code,
  or a shared dependency it uses, changed** — e.g. a shared data-export
  script, a shared question-widget helper, a shared CSS block
  duplicated across every exercise (this WP's own section A is exactly
  that case, and did correctly warrant checking every exercise it
  touched).
- **The full offline `python -m unittest discover` and the full
  `npm run test:e2e:book`** remain the right gate for a WP that itself
  touches a genuinely shared surface (a manifest schema, a shared CSS
  rule, the toc/build config, a shared Playwright helper) — which is
  exactly this WP's own case, not the common case for a future
  single-notebook content WP.
- **A CI run is not optional for anything that changes what the release
  gate itself checks** (a workflow file, a shared config) — D.1–D.3 and
  G above are the concrete demonstration of why a local pass does not
  substitute for watching the actual GitHub Actions run to completion
  and reading its real failure log.

## Local viewing of Exercises 9–12

Their notebooks and book pages still exist in the repository (untouched);
only the public, deployed site omits them. To view them locally:

1. Temporarily remove the `chapters/chapter_09/*` through
   `chapters/chapter_12/*` lines from `book/_config.yml`'s
   `exclude_patterns`, and re-add their four `- file: chapters/chapter_0N/
   exercise_0N` entries to `book/_toc.yml`'s `contents` section (or just
   `git show <pre-WP49-SHA>:book/_toc.yml` / `:book/_config.yml` for the
   exact prior text).
2. `jupyter-book build book --all` — this builds a **local-only** copy
   with all 12 chapters; do not commit this change or push it.
3. Open `book/_build/html/chapters/chapter_09/exercise_09.html` (etc.)
   directly, or serve the directory
   (`python -m http.server --directory book/_build/html`) and browse to
   it.
4. Exercises 9 and 10's portable/Colab notebooks remain directly
   inspectable without any book build at all:
   `book/downloads/chapter_09/exercise_09_portable.ipynb` and
   `book/downloads/chapter_10/exercise_10_portable.ipynb` — open in any
   local Jupyter or upload to Colab as-is.
5. Exercises 11–12 are unchanged one-line placeholder pages
   (`book/chapters/chapter_11/exercise_11.md`,
   `.../chapter_12/exercise_12.md`) — plain text files, no build needed to
   read them.

## Deployment, CI, and live-site verification

**Live site**: `https://yoavmp.github.io/ml-neuro-tutorials/` — deployed
by the green CI run `37445520518`
(`https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/37445520518`),
confirmed by fetching the actual `gh-pages` branch
(`deploy: 93f656f`, matching this WP's own commit) rather than assuming
the workflow's own "success" status implied it.

Checked the real, served site directly (not a simulation) after
publication:
- `contents.html` lists exactly Exercises 1–8, in order; no trace of
  Exercises 9–12.
- `chapters/chapter_09/exercise_09.html` → HTTP 404 (confirms the Sphinx
  `exclude_patterns` fix actually took effect in production, not just
  locally).
- `chapters/chapter_11/exercise_11.html` → HTTP 404 (same, for the
  placeholder pages).
- `chapters/chapter_03/exercise_03.html` → real content, links to
  `../../lite/notebooks/index.html?path=exercise_03.ipynb` as expected.
- `lite/notebooks/index.html?path=exercise_03.ipynb` → loads the real
  JupyterLite SPA shell ("Loading JupyterLite...", the expected
  pre-hydration state for a URL fetch with no JS execution); full
  kernel-start/data-load/question-grading/widget-interaction/save-
  download behavior for every one of Exercises 1–8 was already verified
  against this exact build by the real Playwright suite (section D)
  before this deployment went out, not re-asserted here from a bare
  HTTP fetch.
- `lite/files/exercise_03.ipynb` and `lite/files/exercise_03_portable.ipynb`
  → both HTTP 200, `content-type: application/x-ipynb+json`.

A fifth push (the workflow-gate split in section G) deployed again on
top of this, also green end to end (1h30m34s); re-confirmed live
afterward (`gh-pages` tip `deploy: 36d84d3`, matching that commit;
`contents.html` still lists exactly 1-8; `chapters/chapter_09/
exercise_09.html` still 404s). See `WP49_EXACT_CHANGELOG.md` for that
run's own URL and the full run table.

## Deviations and pending items

- **Real Google Colab acceptance remains unverified** for Exercises 3–8,
  exactly as it was before this WP (WP41 maintainer guide §11) — this WP
  does not and cannot claim it. Deployed anyway on the author's own
  explicit, written authorization in this WP's own instructions ("I
  authorize this deployment with real-Colab acceptance of the revised
  notebooks still pending"). The author's own Colab check before WP48
  covered Exercises 1–3; it has not been repeated against WP48/WP49's
  changes to those three, and the author stated no further manual checks
  are possible this weekend.
- Every browser-based claim in this report is a real Playwright run
  against the real, served, combined build (never a described/simulated
  run) — Colab itself was never claimed to have been opened by this WP,
  consistent with the maintainer guide's own distinction between the two.
- `interactive/e2e-book/iframe-height-contract.spec.ts`,
  `chapter09.spec.ts`, `chapter09-dark-mode.spec.ts`, and
  `chapter10.spec.ts` are excluded from the book suite's `testIgnore`, not
  deleted — ready to be re-enabled (and, for the iframe-height-contract
  CASES array, trimmed back to only 11–12 or rewritten entirely) whenever
  Exercises 9–12 are next migrated and republished.
- This WP took five real GitHub Actions runs in total (D.2, plus the
  workflow-gate split's own run in section G) -- four 1.75-2.75 hour
  runs to get the book-suite gate green, then one more 1.5 hour run to
  confirm the gate-scoping fix. The multi-run cost was because the
  fixed-wait fragility in D.3 could not be fully diagnosed from local
  runs alone — CI's own failure logs, read directly via `gh run view
  --log-failed` each time, were what actually distinguished "contention"
  from "the wait itself is wrong" from "this one notebook cannot use this
  mechanism at all." Recorded in full in section D rather than
  compressed into a single "fixed it" line, since the false leads
  (margin-widening, the `.jp-mod-error` fallback) are exactly the kind of
  reasoning a future WP hitting a similar flake should be able to rule
  out quickly by reading this report first.
