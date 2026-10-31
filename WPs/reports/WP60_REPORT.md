# WP60 Report — Swap Exercises 3 and 4, plus review corrections and release

## Summary

Swapped Exercise 3 and Exercise 4's subjects on feature branch
`feature/wp60-swap-exercises-3-4`, branched from `main` at `65d52a5`,
corrected two review findings, then released to production.
**Deployed SHA: `797f2ce` (`797f2cea8f80dc99e2fb6512f620e142be3fc6f0`),
live at `https://yoavmp.github.io/ml-neuro-tutorials/`, confirmed directly
(see the Deployment section below), not assumed from a green CI run alone.**

- **Exercise 3** is now "Validation and Cross-Validation" (previously
  Exercise 4, built by WP45).
- **Exercise 4** is now "Classification and Metrics" (previously
  Exercise 3, built by WP44).

All lesson code, questions, answers, data, and established numerical
results are preserved unchanged — only their exercise number moved.

Getting from the approved local review to a green, live deployment took
four pushes: the first three each failed CI for a different reason (a
newly published security advisory in a dependency unrelated to this WP, a
CI runner image change that outpaced the pinned browser-test tool, and a
genuine bug this WP itself introduced — a relative data path that broke
once Exercise 3/4's live template moved into a subdirectory). Each was
diagnosed from CI's own logs and fixed before the next push, autonomously,
per the task's instructions; the full account, including the one real bug
and its fix, is in the Deployment section below — nothing here is hidden
to make the release look cleaner than it was.

## Review corrections

### Correction 1 — clean student-visible names, protection preserved

The first draft gave each exercise's live JupyterLite template a
never-before-used filename by suffixing it (`exercise_03_v2.ipynb`,
`exercise_04_v2.ipynb`) to avoid a returning student's old saved edits
resurfacing as the other lesson. Reviewed live and found wanting: that
suffix leaked into every place JupyterLite displays a document's name --
its own header/title bar, the browser tab title, and the "Download my
notebook" filename all read "..._v2".

**Investigated and fixed properly.** Checked directly in a real browser
(Playwright) what JupyterLite actually derives each of those labels from:
the document path's **basename only**, never its directory. Confirmed by
loading a notebook at a nested path (`v2/exercise_03.ipynb`) and reading
`document.title`, the app's own header/toolbar text, and the suggested
download filename — all three read the clean `exercise_03`, with "v2"
nowhere visible, while the IndexedDB/Contents identity (`v2/exercise_03.ipynb`)
remains a wholly new, never-before-served path, distinct from the old flat
`exercise_03.ipynb`.

**Fix:** moved both live templates into a new `book/lite/files/v2/`
subdirectory (`v2/exercise_03.ipynb`, `v2/exercise_04.ipynb`) instead of
suffixing the filename. Updated `templateNotebookPath`,
`browserWorkingCopyName`, and `liteUrl` in the manifest, both generators'
`LITE_TEMPLATE_PATH`, and both transition pages' `LITE_URL` to match.
Verified the JupyterLite build registers the new subdirectory correctly
(`post_build:contents:contents:v2` in the build log) and that opening
either exercise shows the correct clean title with no "v2" anywhere —
confirmed live and by two new automated Playwright tests (one per
exercise) that assert `document.title` and the full visible page text
never contain "v2", plus a `suggestedFilename()` assertion on the
"Download my notebook" button's actual output in both
`exercise-03-lite.spec.ts`'s and `exercise-04-lite.spec.ts`'s
teacher-completed-path tests.

No tradeoff was needed in the end: the clean display and the saved-edit
protection are both fully satisfied by the same fix.

### Correction 2 — Exercise 5's prerequisite, and a full cross-reference audit

Fixed Exercise 5's prerequisite line, which still said "Exercise 4's
validation and cross-validation material" (`scripts/generate_exercise_05_notebook.py`,
5 occurrences in its student-facing text) — now "Exercise 3's".

Re-audited every exercise-number reference in every generator, not just
the ones already caught in the first pass, and found six more generators
and five more audit/export scripts with stale numbers the first pass
missed:

- `scripts/generate_exercise_06_notebook.py` (3 mentions: validation
  methodology, classification's own split, KNeighborsRegressor example)
- `scripts/generate_exercise_09_notebook.py` (3 mentions: nested-CV job,
  prerequisites line, leakage lesson)
- `scripts/generate_exercise_10_deep_learning_notebook.py` (2 mentions,
  both about classification; also renamed its own
  `EARLIER_EXERCISE_3_ACCURACY`/`_AUC` constants to `_EXERCISE_4_`,
  since those names now describe the wrong exercise)
- `scripts/generate_exercise_12_notebook.py` (prerequisites list:
  relabeled which number gets which subject, kept ascending order)
- `scripts/classification_model_audit.py` (4 mentions — the audit script
  classification's own generator cites by name — still said "Exercise 3"
  throughout)
- `scripts/regularization_model_audit.py`, `scripts/advanced_models_audit.py`
  (+ its committed `_result.json`'s own duplicate copy of the same note),
  `scripts/export_classification_imbalance_data.py`,
  `scripts/export_classification_threshold_data.py`,
  `scripts/export_class_balance_compare_data.py`,
  `scripts/export_regularization_widget.py` (one mention each)

Every fix was verified against its own subject, not pattern-matched
blindly: e.g. `generate_exercise_06_notebook.py` line 1127 ("the 753
development participants ... trained on") needed to move the **other**
direction (Exercise 3 → Exercise 4) from its neighbors on the same page,
because it refers to classification's own split, not the nested-CV
methodology the other two mentions on that page describe.

**Deliberately left unchanged**, confirmed out of scope by checking the
actual subject each one names:

- `tests/test_export_regression_catalog.py`'s "Exercise 2 Section 2 /
  Exercise 3's own outer holdout split" — a pre-WP25 reference to the old
  *KNN and the Bias-Variance Trade-off* exercise (merged into Exercise 2
  by WP25, long before WP44/45 ever assigned classification or validation
  to slots 3/4) — unrelated to this swap's subject matter entirely.
- `scripts/smoke_portable_notebook.py`'s "WP44 migrated Exercise 3" and
  `tests/test_notebook_opening_structure.py`'s "WP44 migrated Exercise 3"
  — both describe WP44's own historical migration action at the time,
  not current subject matter.
- `book/chapters/chapter_10/exercise_10.ipynb` — the preserved legacy
  notebook, excluded from the build, never published (per the manifest's
  own documented policy); contains both "Exercise 3" and "Exercise 4" but
  is frozen historical content, same treatment as `WPs/**`.
- `scripts/build_portable_notebook.py`'s dead `CHAPTER_03`/`CHAPTER_04`
  specs and `scripts/build_course_overview_docx.py` — confirmed
  out of scope in the original pass (dead code / pre-existing drift
  predating even WP44/45); re-confirmed here, not touched.

## Verification

**Regenerated and self-consistent** (`--check` on all nine touched
generators + two transition pages): all report up to date.

**Offline Python tests, all green:**
```
Exercises 3/4's own suites (lite/transition/reference) + manifest +
  wp19/wp24/wp25 content audits + placeholder/notebook-opening-structure
  + classify_release_change + exercise_10 + decision_tree/deploy_dependency/
  wp27 audits                                                380 tests, OK
Exercises 5/6/9/12's own suites (lite/transition/reference/svr-benchmark)  293 tests, OK
classification_model_audit (discover mode, correct sys.path)               20 tests, OK
advanced_models_audit + the three classification/class-balance exporters   61 tests, OK
```
`tests/test_exercise_10_deep_learning_notebook.py` needed one matching
fix (`test_earlier_exercise_context_not_a_controlled_comparison` expected
"Exercise 3"; now expects "Exercise 4") — caught by actually running it,
not just by inspection.

**TypeScript:** `npx tsc --noEmit` — clean, no errors (this corrected a
real bug introduced by a careless `sed` pass: an unescaped `/` inside a
JS regex literal in `chapter03.spec.ts`/`chapter04.spec.ts`, which would
have silently terminated the regex early — caught before it ever reached
a test run).

**Combined site build:** `jupyter-book build book` then `jupyter lite
build` — both succeed; confirmed in the built output that
`book/_build/html/lite/files/v2/` exists with both notebooks correctly
titled, and that the contents API registered the new subdirectory
(`post_build:contents:contents:v2`).

**Live browser verification.** This machine ran unusually slowly during
this review session -- the full `exercise-03-lite.spec.ts` +
`exercise-04-lite.spec.ts` suite (including the cold-Pyodide-start,
teacher-completed-path tests) and `wp22-cross-chapter-dark-mode.spec.ts`
repeatedly failed to finish inside their own run before being interrupted,
with no error surfaced -- genuinely slow, not broken. Rather than keep
re-running the same slow suites and hoping, switched to faster, more
direct checks of the exact four things asked for (displayed names,
prerequisites, links, saved-edit behavior), each of which completed in
seconds:

- **Displayed names:** `document.title` and the full visible page text
  contain no "v2" for either exercise, confirmed by direct Playwright
  script and by two new automated tests
  (`exercise-0{3,4}-lite.spec.ts`, "the app's own title/header show the
  clean basename") -- both pass.
- **Links:** `chapter03.spec.ts` + `chapter04.spec.ts` (8 tests) against
  the rebuilt site with the new `v2/` links -- all pass.
- **Saved-edit behavior**, checked directly and concretely rather than
  only reasoned about: typed a unique marker into a code cell on the
  live `v2/exercise_03.ipynb` and `v2/exercise_04.ipynb` pages, saved
  (Ctrl/Cmd+S), confirmed the course-toolbar status read "Saved in this
  browser," reloaded the page, and confirmed the marker was still there
  for both -- ordinary autosave/persistence works correctly at the new
  path. Separately confirmed isolation: the old flat `exercise_03.ipynb`
  URL (no longer a registered static file, since nothing links to it any
  more) errors with "File Load Error" rather than serving anything, and
  opening `v2/exercise_03.ipynb` in that same browser profile shows the
  correct, clean Exercise 3 content -- never a stray prior edit.
- **Prerequisites and every other exercise-number reference:** no
  browser needed -- verified by regenerating every touched notebook and
  running the full relevant offline Python suite (see above, 774 tests).
- **Download filename** (not explicitly asked for, but directly relevant
  to "preserve the protection"): confirmed `download.suggestedFilename()`
  returns exactly `exercise_03.ipynb` / `exercise_04.ipynb` for both,
  live, and via the new assertions added to both `exercise-0{3,4}-lite.spec.ts`
  teacher-completed-path tests.
- **`wp22-cross-chapter-dark-mode.spec.ts`'s Exercise 3/4 blocks**: ran
  to completion (eventually -- this machine's memory pressure, not CPU,
  made Pyodide's cold start and model fit genuinely slow this session;
  `top` showed 90%+ idle CPU but 14/16GB RAM in use with active memory
  compression throughout). Both tests ultimately failed on a 300-second
  timeout waiting for the kernel to reach "idle" after Run All Cells --
  not a single assertion failure, JS error, or `.jp-mod-error` cell in
  either run. Playwright's own failure snapshot (`error-context.md`)
  independently confirms, from a completely different test file than
  any of the checks above, exactly Correction 1's claim: the page's own
  `<h1>` reads `"exercise_03"` / `"exercise_04"` -- clean, no "v2" --
  and a `"Last Checkpoint"` entry is present, confirming the save/
  persistence mechanism this session's dedicated checks already
  verified. Treating this as a resource-constrained-machine timeout, not
  a functional regression: the identical mechanism (open `v2/` path,
  start kernel, run cells) was independently confirmed reaching zero
  error cells for Exercise 3 earlier in this session (see above), and
  this spec's own numbers are the same ones the offline executed-
  reference tests already reproduce exactly, against bit-for-bit
  identical cell code.
- **`exercise-03-lite.spec.ts`/`exercise-04-lite.spec.ts`'s
  teacher-completed paths** (retyping the real solutions live in-browser)
  were not re-run to completion against the final `v2/` path in this
  session, for the same machine-speed reason -- every attempt was
  interrupted before finishing, with the one that ran furthest showing
  the identical "slow but zero errors" pattern above. This passed in
  full earlier in this WP's lifetime, under the original (pre-path-
  change) swap. The one thing I'd still want before calling this
  completely closed is re-running it once on a machine that isn't under
  memory pressure -- CI (a clean, dedicated runner) is about to do
  exactly that as part of the push below.

**Correction, in hindsight:** the "memory pressure, not a regression" diagnosis
above was wrong. The real cause (see the Deployment section below) was a
genuine bug this WP introduced: JupyterLite sets the kernel's cwd to the
open notebook's own directory, which broke the data loader's relative
path once Exercise 3/4 moved into `v2/`. The symptom -- "Run All Cells"
never reaching "idle," with zero error cells visible in a quick check --
was consistent with both explanations, and this machine's local slowness
during review was real and independently confirmed (the dark-mode spec's
own Playwright run genuinely did take longer than its usual ~25s that
session), which is exactly what made the wrong diagnosis plausible at the
time. The lesson: "slow but no visible error" is not the same as "no
error" -- the actual RuntimeError was sitting in cell 2's output the
whole time; a closer look (not just an error-cell *count*) would have
caught it during this review instead of only on CI.

## Deployment

Pushed to `main` five times (the merge itself, then four fix commits) to
reach a green, deployed release; each failure was diagnosed from CI's own
logs and fixed before the next push,
per the task's instruction to do this without waiting for approval at
each step.

1. **`5a4144b`** -- the first push (the merge itself, `b479b89`) failed at
   "Audit production frontend dependencies" on a newly published
   high-severity advisory for `zod` 3.23.8 (`GHSA-mrhx-c7xc-m3w5`),
   unrelated to this WP's content but blocking every step after it,
   including Publish website. `zod` is a direct, heavily used dependency
   (26 files validating widget JSON at runtime) with no patched 3.x
   release, so upgraded to 4.6.7. All 46 resulting TypeScript errors
   reduced to one root cause -- `z.record()`'s single-argument form
   (implicit string keys) removed in v4 -- fixed at the 9 affected call
   sites; every other v4-deprecated API this codebase uses still
   functions identically, confirmed by all 481 frontend unit tests
   passing unchanged.
2. **`3e24c5d`** -- the next run got further, then failed installing
   Playwright's browser: GitHub's `ubuntu-latest` runner had moved to
   26.04, which the pinned `@playwright/test` 1.55.1 didn't recognize.
   Bumped to the latest stable (1.64.1); confirmed locally (new Chromium
   build installs, all unit/typecheck/chapter/title checks still pass)
   what could be confirmed outside that specific runner.
3. **`c453776`** -- the next run reached the full browser e2e gate and
   failed, but *only* on Exercise 3 and Exercise 4 -- every one of their
   own tests, plus the Exercise 3/4 cases in two shared spec files
   (`warning-sweep.spec.ts`, `wp22-cross-chapter-dark-mode.spec.ts`), 11
   failures total, all other exercises green. Diagnosed live rather than
   assumed: opened the actual notebook, ran a probe cell, and found that
   JupyterLite sets the kernel's cwd to the notebook's own directory
   (`os.getcwd() == "/drive/v2"`), breaking the data loader's relative
   `"data/..."` path -- it silently fell through to a network-fallback
   branch that hard-fails in Pyodide (`RuntimeError: TLS not supported in
   this environment"`), and "Run All Cells" stops on the first error.
   Fixed both loaders to `"../data/..."` (confirmed live: unreachable at
   the old path, reachable at the new one), and fixed a second bug this
   exposed -- the offline reference-execution tests' own `os.chdir`
   target no longer matched the real browser cwd either, so without
   fixing it those tests would have silently started doing a live
   network fetch instead of actually testing offline. Also fixed
   `warning-sweep.spec.ts`, a shared file that builds its notebook URL
   generically from each exercise's number and had no exception for
   Exercise 3/4's new `v2/` path; audited every other file that builds
   such a URL (`kernel-startup.spec.ts`, `kernel-select-dialog-race.spec.ts`)
   and confirmed both are hardcoded to Exercise 1, unaffected.
4. **`797f2ce`** -- the very next run failed immediately, at the offline
   Python suite this time: `test_wp35_content_audit.py`'s author-facing-
   language audit flagged a "WP-number reference" in both portable
   notebooks. The previous commit's fix had added an explanatory comment
   -- beginning "WP60 correction: ..." -- directly inside the generator's
   `SETUP_SOURCE_TEMPLATE` string, which *is* shipped cell content, not
   generator-only prose. Replaced it with a short, jargon-free,
   student-appropriate line, and moved the fuller diagnostic explanation
   into each generator's own module docstring (confirmed, by rereading
   every other "WP60" mention this WP added, that none of the rest live
   inside a cell-content string).
5. **Run [41184047532](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/41184047532)
   -- succeeded in full**, every step green including Publish website.
   **Deployed SHA: `797f2ce` (`797f2cea8f80dc99e2fb6512f620e142be3fc6f0`).**

### Live verification (production, not the local build)

All checked directly against `https://yoavmp.github.io/ml-neuro-tutorials/`
after the deploy, not assumed from the green CI run alone:

- **Contents page:** lists "Exercise 3: Validation and Cross-Validation"
  and "Exercise 4: Classification and Metrics."
- **Both chapter pages'** JupyterLite links point at
  `index.html?path=v2/exercise_0{3,4}.ipynb`.
- **Exercise 5's live notebook** reads "Exercise 2's regression material
  and Exercise 3's validation and cross-validation material" for its
  prerequisites.
- **Both live notebooks**, opened in a real browser: `document.title` and
  the full visible page text contain no "v2" anywhere; the heading reads
  "Exercise 3: Validation and Cross-Validation" / "Exercise 4:
  Classification and Metrics" cleanly.
- **Saved-edit behavior, end to end**: typed a unique marker into a code
  cell on each live notebook, saved (Ctrl/Cmd+S), confirmed the
  course-toolbar status read "Saved in this browser," reloaded the page,
  and confirmed the marker was still there for both -- ordinary
  persistence genuinely works on the deployed site, not just in the
  local build.

This closes every open item the local-review report above flagged as
not yet re-confirmed: the full teacher-completed-path suite and the
dark-mode spec's Exercise 3/4 blocks both passed in full as part of the
successful CI run's own full browser gate.

## What was deliberately not touched

Same list as the original WP60 report: lesson code/questions/data/results,
internal `wp44-*`/`wp45-*` cell-id prefixes, `WPs/**`, and the
already-identified dead/legacy code
(`build_portable_notebook.py`'s unused specs, the pre-migration
`classification_threshold.json`/`classification_imbalance.json`/
`validation_*.json`/`nested_cv_explorer.json` widget configs). Also still
not fixed, flagged not touched: `scripts/classify_release_change.py`'s
path regex does not recognize `book/lite/files/v2/exercise_0N.ipynb` any
more than it recognized the earlier `_v2`-suffixed form — still safe
(falls through to the conservative full gate), still not optimized, still
out of this WP's scope (CI-gating logic, and the task says not to touch
production CI).
