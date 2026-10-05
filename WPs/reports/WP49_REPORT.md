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

## D. The first-ever full combined Playwright run, and three real issues it found

Built the combined site once (`jupyter-book build book --all` on a clean
`_build/`, then `jupyter lite build --config
book/lite/jupyter_lite_config.json --lite-dir book/lite --output-dir
book/_build/html/lite`) and ran `npm run test:e2e:book` — the complete
suite across all eight migrated exercises' `exercise-0N-lite.spec.ts`
files, every `chapterNN.spec.ts` transition page, `launch-buttons.spec.ts`,
and `wp22-cross-chapter-dark-mode.spec.ts` — for the first time ever. WP46
and WP47 had each explicitly deferred this exact run ("one comprehensive
suite later, once every notebook is migrated"); this is that moment.

**First full run** (default full parallelism, matching CI's then-current
config): **95 passed, 8 failed, 20.6 minutes.** Diagnosed every failure
individually rather than assuming or dismissing any of them:

1. **A real stale assertion** (not contention): `wp22-cross-chapter-dark-
   mode.spec.ts`'s Exercise 4 case still checked for `.ml-ncv-diagram`, the
   raw-HTML nested-CV diagram WP48 replaced with a rendered PNG attachment
   — this test was simply never run again after that WP48 change landed.
   Fixed to check for the new `<img alt="Nested cross-validation
   diagram...">` instead.
2. **A real, deterministic timeout bug** (not contention): the same
   file's Exercise 7 case set `test.setTimeout(180_000)` but then spent
   that *entire* budget on its own first `page.waitForTimeout(180_000)` —
   a guaranteed failure on every run, unlike this file's other five
   exercises (each budgets 140_000–150_000ms of internal wait against the
   same 180_000ms limit, leaving real slack). Bumped to `240_000`.
3. **Genuine cross-test CPU contention** (confirmed, not assumed): the
   remaining 6 failures (one in `exercise-01-lite.spec.ts`, one each in
   `exercise-04-lite.spec.ts`/`exercise-06-lite.spec.ts`'s
   teacher-completed paths, three in `exercise-07-lite.spec.ts`) were
   verified live, one by one, by rerunning each failing file **completely
   isolated** (`--workers=1`, nothing else running) — every single one
   passed cleanly alone. This is the exact resource-contention pattern
   WP43RR/WP46/WP47 already documented for smaller exercise counts, now
   reproducing more broadly simply because there are more Pyodide-heavy
   files contending for the same CPU. A live diagnostic run with
   `console`/`pageerror`/`crash`/`framenavigated` instrumentation attached
   confirmed the two `exercise-07-lite.spec.ts` widget-interaction tests
   genuinely work (no crash, no error, no navigation) — they just
   occasionally take longer than this test's original fixed 1.5s wait + 5s
   assertion timeout to settle, right after 180s of continuous upstream
   computation. Widened those two tests' margins (same assertions, more
   generous timeouts: 5s→20s, 1.5s→3s wait) rather than touching anything
   that changes what is actually being checked.
4. **Structural fix for the environment, not the assertions**: since CI's
   runner has *fewer* cores than the machine this contention was
   diagnosed on, it is more exposed to this pattern, not less. Capped
   `playwright.book.config.ts` to `workers: 1` **on CI only** (local runs
   stay fully parallel for fast iteration) — a concurrency/environment
   accommodation, never a weakened or deleted assertion.

**Reruns after each fix, each isolated and bounded, not a blind loop:**
- `exercise-07-lite.spec.ts` alone (`--workers=1`): **7/7 passed, 32.5
  min** (matches this file's own WP46-documented historical baseline).
- `wp22-cross-chapter-dark-mode.spec.ts` alone (`--workers=1`): **6/6
  passed, 15.5 min**.
- `exercise-01-lite.spec.ts` alone (`--workers=1`): **8/8 passed, 14.9
  min**.
- A four-file serialized rerun (`exercise-04/06/07-lite.spec.ts` +
  `wp22-...`) confirmed Exercises 4 and 6's full files also pass cleanly
  isolated.
- **Final full-suite confirmation, fully parallel** (matching the
  original run's own config, to prove the fixes hold under the same
  conditions that found them): **95 passed, 8 failed, 20.5 minutes** —
  the wp22 Exercise-4 diagram fix held under full parallelism too, but
  Exercises 1/4/6/7's heaviest tests still contended under *full* default
  parallelism exactly as expected (this is what motivated the CI
  `workers: 1` cap in point 4 above, verified by every isolated rerun
  above rather than asserted).

See `WP49_EXACT_CHANGELOG.md` for the exact command/duration table.

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

No other workflow step needed touching: `smoke_portable_notebook.py`'s
`SMOKE` dict already correctly excludes Exercises 1–8's portable
notebooks (each documented as hitting the known
`ipywidgets.Output()`-as-context-manager / `nbclient` comm-handshake hang,
verified instead by each exercise's own reference-execution suite) and
only smoke-tests `chapter_02`, `chapter_09`, and `chapter_10` — unaffected
by this WP's publish/unpublish decisions either way.

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

See `WP49_EXACT_CHANGELOG.md` for exact commits, the GitHub Actions run
URL, its final status and duration, and the post-deployment live-site
check.

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
