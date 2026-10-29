# WP60 Report — Swap Exercises 3 and 4 (local review only)

## Summary

Swapped Exercise 3 and Exercise 4's subjects on feature branch
`feature/wp60-swap-exercises-3-4`, branched from `main` at `65d52a5`.
**Nothing was merged, pushed, built into production, or deployed.** No
workflow ran.

- **Exercise 3** is now "Validation and Cross-Validation" (previously
  Exercise 4, built by WP45).
- **Exercise 4** is now "Classification and Metrics" (previously
  Exercise 3, built by WP44).

All lesson code, questions, answers, data, and established numerical
results are preserved unchanged — only their exercise number moved. The
two authoritative generators (`scripts/generate_exercise_03_notebook.py`,
`scripts/generate_exercise_04_notebook.py`) swapped bodies in place (file
names stay tied to their slot; content moved), and every generated
artifact was regenerated from them. Internal cell-id prefixes (`wp44-*`
for the classification lesson, `wp45-*` for the validation/CV lesson) were
**not** renamed — they are non-student-facing authorship bookkeeping tied
to content, not to slot number.

**JupyterLite saved-edit safety (the risk called out explicitly): both
exercises' live, in-browser template got a new, never-before-used
filename** — `exercise_03_v2.ipynb` and `exercise_04_v2.ipynb` — instead
of reusing the old plain `exercise_03.ipynb`/`exercise_04.ipynb`. See
section 2 below for why this is necessary and why a simple swap of the two
numbers would not have been safe.

**Result: every test file touched by the swap passes (80 structural +
31 executed-reference + 10 manifest + cross-reference audit tests, listed
in full below); the combined Jupyter Book + JupyterLite site builds
cleanly; all 12 live-browser Exercise 3/4 tests pass, including both
teacher-completed paths, which retype the real solutions live and
reproduce the exact established numbers (CV mean MSE = 33.8, nested-CV
selected k = [15, 12, 10, 18, 15]; classification accuracy = 0.546,
AUC = 0.569) against the notebooks at their new `_v2` URLs; the shared
`wp22-cross-chapter-dark-mode.spec.ts` file (Exercises 2, 3, 4, 5, 6, 7)
is green end-to-end.**

One genuine pre-existing-rule conflict was found and resolved, not
papered over: WP19's "no cross-validation terminology in Exercises 1-3"
content audit. Since Exercise 3 is now deliberately the
validation/cross-validation lesson, that audit's early, pre-CV zone is
narrowed to Exercises 1-2 (the same treatment the old Exercise 4 already
had, for the identical reason) — see section 4.

## 1. Every renamed or changed path

### Authoritative generators (content swapped, file names unchanged — tied to slot, not subject)

| File | New content |
|---|---|
| `scripts/generate_exercise_03_notebook.py` | Validation and Cross-Validation (was: Classification) |
| `scripts/generate_exercise_04_notebook.py` | Classification and Metrics (was: Validation and CV) |
| `scripts/generate_exercise_03_transition_page.py` | title/link updated in place |
| `scripts/generate_exercise_04_transition_page.py` | title/link updated in place |

### Renamed (content-tied, not slot-tied)

| Old | New |
|---|---|
| `scripts/render_exercise_04_nested_cv_diagram.py` | `scripts/render_exercise_03_nested_cv_diagram.py` |
| `book/lite/files/data/exercise_04_nested_cv_diagram.png` | `book/lite/files/data/exercise_03_nested_cv_diagram.png` |

### Generated outputs (regenerated via the swapped generators; same paths as before — chapter/slot-based)

- `book/lite/files/exercise_03_portable.ipynb`, `book/downloads/chapter_03/exercise_03_portable.ipynb`, `scripts/reference_notebooks/exercise_03_reference.ipynb` — now Validation/CV
- `book/lite/files/exercise_04_portable.ipynb`, `book/downloads/chapter_04/exercise_04_portable.ipynb`, `scripts/reference_notebooks/exercise_04_reference.ipynb` — now Classification
- `book/chapters/chapter_03/exercise_03.ipynb`, `book/chapters/chapter_04/exercise_04.ipynb` — transition pages, titles swapped

### New files (the live JupyterLite template only — see section 2)

- `book/lite/files/exercise_03_v2.ipynb` (Validation/CV; new)
- `book/lite/files/exercise_04_v2.ipynb` (Classification; new)

### Deleted (superseded by the `_v2` files above; no longer referenced anywhere live)

- `book/lite/files/exercise_03.ipynb`
- `book/lite/files/exercise_04.ipynb`

### Manifest

- `book/config/exercise_manifest.json`: exercise 3 and 4 entries' `title`, `templateNotebookPath`, `browserWorkingCopyName`, `liteUrl`, and `dataAssets` swapped/updated; `$comment` extended with a WP60 paragraph.

### Tests (content swapped, file names unchanged — tied to slot)

- `tests/test_exercise_03_lite_notebook.py` / `tests/test_exercise_04_lite_notebook.py`
- `tests/test_exercise_03_reference_execution.py` / `tests/test_exercise_04_reference_execution.py`
- `tests/test_exercise_03_transition_page.py` / `tests/test_exercise_04_transition_page.py`

### Browser specs (content swapped, file names unchanged — tied to slot)

- `interactive/e2e-book/exercise-03-lite.spec.ts` / `interactive/e2e-book/exercise-04-lite.spec.ts`
- `interactive/e2e-book/chapter03.spec.ts` / `interactive/e2e-book/chapter04.spec.ts` (`LITE_HREF` updated to `_v2`, titles unchanged — these check generic link behavior, not subject)
- `interactive/e2e-book/wp22-cross-chapter-dark-mode.spec.ts` (shared file: the Exercise 3 and Exercise 4 blocks swapped — see section 3)

### Cross-reference text fixes in other exercises (subject-matter mentions, not slot mentions)

- `book/config/abide_modeling.json` — 5 notes (Exercise 9's nested-CV convention, Exercise 5's feature-selection note, Exercise 5's stratify note, Exercise 6's classification-tree note, Exercise 9's nested-CV note)
- `book/_config.yml` — 1 comment (which exercise's diagram needs `sphinxcontrib.mermaid` kept available)
- `scripts/decision_tree_model_audit.py`, `scripts/decision_tree_model_audit_result.json`, `tests/test_decision_tree_model_audit.py` — Exercise 6's own audit referencing classification's protocol (6 mentions)
- `scripts/wp27_validation_audit.py`, `scripts/export_wp27_widget_data.py`, `tests/test_wp27_validation_audit.py`, `tests/test_deploy_dependency_contract.py` — validation/CV's own audit and data-export scripts (6 mentions)
- `tests/test_wp24_content_audit.py` — `EX4`/`EX4_PORTABLE` path constants (WP24's own historical name for "the classification lesson") retargeted to the lesson's new location
- `tests/test_wp19_content_audit.py` and `tests/test_wp25_content_audit.py` — see section 4

## 2. JupyterLite saved-edit handling (the risk this WP called out explicitly)

**Investigation.** JupyterLite's in-browser "Contents" drive persists a
student's edits in the browser's own IndexedDB, keyed by the notebook's
`path` (the `?path=` query-string value, e.g. `exercise_03.ipynb`) — not
by its content. The committed template under `book/lite/files/` only
seeds that IndexedDB entry the *first* time a given path is opened in a
given browser; every later visit to the same URL serves whatever is
already in IndexedDB, not a fresh copy of the template (confirmed by
reading `book/lite/extensions/course-toolbar/src/index.ts`: "Reset from
course template" exists specifically because the committed template is
otherwise never re-served once a browser has its own copy).

That means a straight swap of the two numbers — keeping the plain
`exercise_03.ipynb`/`exercise_04.ipynb` paths and just changing which
lesson's generator writes to each — would **not** be safe: a student who
had already opened and edited the old Exercise 3 (Classification) would,
after this WP, open the new `exercise_03.ipynb` URL and see their *old,
stale, classification* notebook restored from IndexedDB — not the new
Validation/CV template — with no indication anything had changed. The
same collision would hit Exercise 4 in the other direction.

**Solution implemented.** Both exercises' live template/working-copy
filename — the one used for `templateNotebookPath`, `browserWorkingCopyName`,
and `liteUrl`'s `path=` parameter — moved to a **new string that has never
been served at this site before**: `exercise_03_v2.ipynb` and
`exercise_04_v2.ipynb`. A never-before-used path has no existing IndexedDB
entry to collide with, so every browser — new or returning — gets a fresh
seed from the correct, new template. The old plain-named files under
`book/lite/files/` were deleted (superseded, unreferenced); any
browser that still has an IndexedDB entry under the old path simply never
sees it surfaced again (a harmless, permanently orphaned entry, not a
silent mislabeling).

Deliberately **not** changed, because they carry no browser-storage
identity and are served fresh/statically on every request: the portable
download files (`book/downloads/chapter_0N/exercise_0N_portable.ipynb`,
`book/lite/files/exercise_0N_portable.ipynb`) and the transition pages
(`book/chapters/chapter_0N/exercise_0N.ipynb`). No change was needed in
`course-toolbar`'s own TypeScript — every one of its mechanisms (back
link, download, reset, status readout) already derives everything from
whatever `path` the URL carries, with no exercise-number-specific code at
all.

**Checked directly, live, in a real browser (not just reasoned about):**
opening both new `?path=exercise_0N_v2.ipynb` URLs from the rebuilt site,
confirming each shows the correct new lesson, and exercising "Download my
notebook" / "Reset from course template" / "Back to course contents" on
both (`exercise-03-lite.spec.ts`/`exercise-04-lite.spec.ts`'s own
"untouched template" test groups — see section 5).

## 3. Shared component changed: `wp22-cross-chapter-dark-mode.spec.ts`

This file's Exercise 3 and Exercise 4 blocks swapped along with their
content: Exercise 3's block now navigates to `exercise_03_v2.ipynb` and
checks the nested-CV diagram's visibility after a dark-theme switch (the
check the old Exercise 4 block did); Exercise 4's block now navigates to
`exercise_04_v2.ipynb` and checks a rendered figure (the check the old
Exercise 3 block did).

One pre-existing staleness, unrelated to the swap itself, was found and
fixed while doing this: the old Exercise 3 (classification) block's own
comments claimed its untouched template "deliberately halts Run All Cells
partway through via a guarded RuntimeError" and used a 140-second fixed
wait instead of polling for kernel idle. Reading the current generator
(and `exercise-03-lite.spec.ts`'s own header comment, which says this
plainly) shows that guard was already replaced with a graceful
"Not complete yet" message before this WP — the fixed-wait/tolerate-1-error
pattern was stale. The swapped-in Exercise 4 block now correctly uses
`waitForKernelIdle` and expects zero error cells, matching its own
dedicated spec's already-passing behavior. (One real bug introduced
during the swap itself, caught by actually running this file: the first
draft of the new Exercise 3 block checked for a generic code-cell figure
at 10% scroll, copied from the classification block's pattern — but the
validation/CV notebook has no code-cell-rendered figure at all, only the
diagram. Fixed to check the diagram specifically, as the content's own
original test did; now passing.)

## 4. Cross-reference audit: the one real design tension found

`tests/test_wp19_content_audit.py` enforces "no cross-validation /
formal-tuning terminology in the rendered student-facing text of
Exercises 1-3" (the WP19 scope). Exercise 3's own new title
("Validation and Cross-Validation") trips that rule directly — the
notebook's canonical page literally says "Cross-Validation" now.

This is not a bug to paper over with wording: it is WP19's rule and this
WP's requested swap genuinely disagreeing about which exercise number is
allowed to mention cross-validation. Resolved the same way the rule
already handled the *old* Exercise 4 (which held this exact subject
before the swap and was, for that reason, never included in WP19's scope
to begin with): narrowed the audit's "early, pre-cross-validation zone"
from Exercises 1-3 to Exercises 1-2, and retargeted the one test that
checked classification-specific wording (`C_EXAMPLE = 1.0`) to follow that
content to its new home at Exercise 4. `tests/test_wp25_content_audit.py`
similarly encodes a live `EXERCISE_TITLES` dict used to verify every
exercise's *current* required title — updated for exercises 3 and 4 to
the new wording.

Deliberately left untouched, as historical record: `WPs/**`, every
`WPs/reports/*.md` and `*_EXACT_CHANGELOG.md`, and the two "pre-syllabus
archive" tests in `test_wp25_content_audit.py` that check an immutable
old commit by SHA (an entirely different, long-superseded numbering, from
before WP25). Also left untouched, as genuinely out of scope: the Word
course-overview generator (`scripts/build_course_overview_docx.py`) and
`scripts/build_portable_notebook.py`'s own `CHAPTER_03`/`CHAPTER_04`
specs — both already describe an even older course structure (predating
WP44/45's migration) and are either unreferenced dead code (the latter,
confirmed: its own `NOTEBOOKS` registry comment says the pre-migration
pipeline for Exercises 1-9 is "left in place, unused, rather than
removed") or already stale independent of this swap (the former). Fixing
either is a separate, unrelated task.

## 5. Test results

**Regenerated and self-consistent:**
```
.venv/bin/python scripts/generate_exercise_03_notebook.py --check   -> OK
.venv/bin/python scripts/generate_exercise_04_notebook.py --check   -> OK
.venv/bin/python scripts/generate_exercise_03_transition_page.py --check -> OK
.venv/bin/python scripts/generate_exercise_04_transition_page.py --check -> OK
```

**Offline Python tests (all green):**
```
test_exercise_03_lite_notebook + test_exercise_04_lite_notebook
  + test_exercise_03_transition_page + test_exercise_04_transition_page   80 tests, OK
test_exercise_03_reference_execution + test_exercise_04_reference_execution  31 tests, OK
  (executes both completed reference notebooks end to end; confirms the
  established numbers bit-for-bit: classification accuracy=0.545817,
  AUC=0.569221, sensitivity=0.534483, specificity=0.555556, confusion
  matrix TN=75/FP=60/FN=54/TP=62; validation one-split MSE=31.3768/
  R2=0.663879, 5-fold CV mean MSE=33.8121/R2=0.615255, nested-CV mean MSE
  matches scripts/wp27_validation_audit_result.json)
test_exercise_manifest                                                   10 tests, OK
test_decision_tree_model_audit + test_deploy_dependency_contract         22 tests, OK
test_wp19_content_audit + test_wp25_content_audit
  + test_placeholder_exercises + test_notebook_opening_structure
  + test_classify_release_change                                        96 tests, OK
test_wp24_content_audit                                                  29 tests, OK
```
A full repo-wide `python -m unittest discover -s tests` sanity pass was
also started as a bonus (not required — the task scope is Exercises 3-4
plus their cross-references, audited above without rerunning other
exercises' own full suites); it is long-running (12 exercises' worth of
real model fits). If it surfaces anything beyond what is already covered
above, it will need a follow-up look before release.

**TypeScript:** `npx tsc --noEmit` — clean, no errors.

**Combined site build:**
```
.venv/bin/jupyter-book build book                                        -> build succeeded, 2 warnings
  (both pre-existing and unrelated: missing book/logo.png; book/README.md
  not in any toctree)
.venv/bin/jupyter lite build --config book/lite/jupyter_lite_config.json
  --lite-dir book/lite --output-dir book/_build/html/lite                -> succeeded
```
Confirmed in the built output: `book/_build/html/lite/files/` contains
`exercise_03_v2.ipynb` (title "Exercise 3: Validation and Cross-Validation")
and `exercise_04_v2.ipynb` (title "Exercise 4: Classification and
Metrics"), the renamed diagram PNG, and no stale plain-named files.

**Live browser tests (Playwright, against the rebuilt site), all green:**
```
chapter03.spec.ts + chapter04.spec.ts                      8 tests passed
exercise-03-lite.spec.ts + exercise-04-lite.spec.ts        12 tests passed (3.6m)
  - both "untouched template" groups: correct established data/text,
    zero unexpected error cells, correct graceful degradation messages,
    390px viewport usable, Reset/Back both work
  - both "teacher-completed path" tests: typed the real solutions live
    and reproduced the established numbers (CV mean MSE=33.8, nested-CV
    selected k=[15, 12, 10, 18, 15]; classification accuracy=0.546,
    AUC=0.569), downloaded the completed notebook and confirmed the
    blank was actually filled
wp22-cross-chapter-dark-mode.spec.ts (Exercises 2,3,4,5,6,7)  6 tests passed
  (one real bug caught and fixed during this run -- see section 3)
```

## 6. What was deliberately not touched

- Lesson code, questions, written-answer prompts, data, and established
  numerical results — moved, never rewritten.
- Internal cell-id prefixes (`wp44-*`, `wp45-*`) — content-tied authorship
  bookkeeping, not student-facing, not worth the churn/risk of renaming.
- `WPs/**` (every spec and report, including this WP's own predecessors) —
  historical record, per the task's own instruction.
- Legacy/dead code already unrelated to the live pipeline:
  `scripts/build_portable_notebook.py`'s `CHAPTER_03`/`CHAPTER_04` specs,
  the pre-JupyterLite `classification_threshold.json`/
  `classification_imbalance.json`/`validation_stability.json`/
  `validation_lock_test.json`/`nested_cv_explorer.json` widget configs, and
  `scripts/export_classification_*`/`export_class_balance_compare_data.py`
  — none referenced by the current generators or notebooks.
- `scripts/classify_release_change.py` (the CI release-gate classifier):
  its path regex for `book/lite/files/exercise_(0[1-9])(?:_portable)?\.ipynb`
  does not match the new `_v2` filenames, so a future change to either
  template there would classify as "unknown" and force the conservative
  full gate rather than the faster per-exercise/prose-only gate. This is
  safe (never under-scopes a real change) but not optimized; flagged here
  rather than touched, since it is CI-gating logic outside this WP's scope
  and the task explicitly says not to run or wire production CI.

## 7. Local preview

Served from the rebuilt `book/_build/html` (Playwright's own
`node e2e-book/serve-book.mjs`, port 4174; `cd interactive && node
e2e-book/serve-book.mjs` to run it standalone):

- Exercise 3 (Validation and Cross-Validation): `http://localhost:4174/ml-neuro-tutorials/chapters/chapter_03/exercise_03.html`, or directly `http://localhost:4174/lite/notebooks/index.html?path=exercise_03_v2.ipynb`
- Exercise 4 (Classification and Metrics): `http://localhost:4174/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html`, or directly `http://localhost:4174/lite/notebooks/index.html?path=exercise_04_v2.ipynb`

## 8. Not done (by instruction)

No merge, no push, no production CI, no deploy. This stays on
`feature/wp60-swap-exercises-3-4` for local review; release is a separate,
explicit, later decision.
