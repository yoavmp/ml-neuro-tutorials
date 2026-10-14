# WP57 Exact Changelog — Exercise 12: Common Mistakes and Pitfalls (local review only)

Branch: `feature/wp57-active-exercise-12-common-mistakes`, created from
`main` at `5d46b26`. **No merge, push, or deployment.**

## New files

- `scripts/generate_exercise_12_notebook.py` — the single authoritative
  generator for the student template, portable notebook, served portable
  copy, and reference notebook. Six cases (Preparing the Predictors, Two
  Components, Picking a Tree, A High-Accuracy Classifier, Many Rows per
  Participant, One Last Setting to Try), two native `ipywidgets`
  activities, 7 checked questions (6 single-choice + 1 select-all), 4
  required student repair blanks (Cases 1, 2, 3, 5).
- `scripts/generate_exercise_12_transition_page.py` — generates
  `book/chapters/chapter_12/exercise_12.ipynb` (replaces the old
  `exercise_12.md` stub) linking to the Lite notebook and portable
  download, following `generate_exercise_09_transition_page.py`'s exact
  pattern.
- `book/lite/files/exercise_12.ipynb` — generated student template
  (JupyterLite).
- `book/downloads/chapter_12/exercise_12_portable.ipynb` — generated
  portable/Colab copy (identical bytes to the Lite template).
- `book/lite/files/exercise_12_portable.ipynb` — same bytes, served
  same-origin copy for the download button.
- `scripts/reference_notebooks/exercise_12_reference.ipynb` — generated,
  fully solved reference notebook (test-only, never published).
- `book/chapters/chapter_12/exercise_12.ipynb` — the new transition page
  (replaces `exercise_12.md`, removed — see "Deleted files" below).
- `book/chapters/chapter_10/placeholder.md` — new local-only "Coming
  Later" placeholder page for navigation purposes. Does **not** reference
  or migrate the real legacy `exercise_10.ipynb`, which is untouched and
  unreferenced by any toc.
- `tests/test_exercise_12_lite_notebook.py` — 38 structural/offline tests
  (headers, overview-list/section correspondence, blank/question
  inventories, no-leakage-in-hints audit, widget self-containment,
  student/portable/reference synchronization).
- `tests/test_exercise_12_reference_execution.py` — 28 executed tests
  (reference notebook's established numbers; untouched template's
  graceful, cascade-free degradation).
- `tests/test_exercise_12_transition_page.py` — 9 tests for the new
  transition page.
- `interactive/e2e-book/exercise-12-lite.spec.ts` — real Chromium/Pyodide
  Playwright spec: untouched-template Run All, 390px-viewport label
  checks, Reset/Back navigation, and the full teacher-completed path (all
  4 blanks, both widgets, all 7 questions correct + 2 deliberately-wrong
  answers, edit/download).

## Modified files

- `book/_toc.yml` — added `chapters/chapter_10/placeholder`,
  `chapters/chapter_11/exercise_11`, `chapters/chapter_12/exercise_12`
  after `chapters/chapter_09/exercise_09`; updated the surrounding comment
  to describe this WP's local-only scope. **Local-only; revert to `main`'s
  text before any release.**
- `book/_config.yml` — `exclude_patterns`: removed the
  `chapters/chapter_11/*` and `chapters/chapter_12/*` entries entirely;
  replaced `chapters/chapter_10/*` with the single, precise
  `chapters/chapter_10/exercise_10.ipynb` (keeps the real legacy notebook
  excluded/unexecuted while letting the new placeholder in the same
  directory build). **Local-only; revert to `main`'s text before any
  release.**
- `book/config/exercise_manifest.json` — entry `number: 12`: `title`
  changed from `"Placeholder"` to `"Common Mistakes and Pitfalls"`;
  `legacyStaticPagePath` changed from `"chapters/chapter_12/exercise_12.md"`
  to `"chapters/chapter_12/exercise_12.ipynb"` (the file it points at was
  renamed/replaced). `migrationState` for entries 10–12 **unchanged**
  (`"legacy"`); all lite-wiring fields for entry 12 **unchanged** (`null`).

## Renamed/replaced files

- `book/chapters/chapter_12/exercise_12.md` → **removed** (old,
  never-built, different-topic placeholder stub — "Review and Exam-Style
  Questions" — with no reviewable historical content of its own). Replaced
  in the same logical slot by `book/chapters/chapter_12/exercise_12.ipynb`
  (new transition page; see "New files"). Git's own diff detected a rename
  pairing against the new, unrelated `chapters/chapter_10/placeholder.md`
  purely by text-similarity heuristic — both are short "Coming
  later"-style stubs of similar length; this is a cosmetic artifact of
  `git status`'s similarity detector, not an actual content relationship
  between the two files.

## Unmodified (verified)

- `book/chapters/chapter_10/exercise_10.ipynb` — byte-for-byte untouched
  (`git diff main` against this path is empty); preserved as a reviewable
  historical source per the WP's own instruction.
- `book/chapters/chapter_11/exercise_11.md` — untouched; its existing
  placeholder wording already satisfied the WP's "Coming later" / no-
  launch-button requirement.
- Exercises 1–9 (notebooks, generators, tests, transition pages) — no
  changes; no narrowly necessary shared fix was needed.
- `book/_static/launch-buttons.js` — not touched; Exercise 12 follows the
  same transition-page-only pattern as Exercises 1–9 (no Colab button
  mapping needed), and chapter 10's pre-existing (already-stale, already-
  unreachable before this WP) mapping entry is unaffected.

## Bug found and fixed during development (accidental, not a teaching case)

- First draft of `scripts/generate_exercise_12_notebook.py`'s Case 1/3
  shared three-way split called
  `train_test_split(X, y, group, test_size=..., random_state=..., stratify=group)`
  (3 positional arrays → 6 return values) but unpacked only 5 names
  (`X_train, X_rest, y_train, y_rest, group_rest = ...`), raising
  `ValueError: too many values to unpack (expected 5)` the first time the
  reference notebook was executed. Fixed by adding the missing
  `group_train` name to the unpacking. Caught before any number in the
  report was finalized.
- Three blank hints (`wp57-activity-scaler`, `wp57-activity-pca`,
  `wp57-activity-group`) initially contained literal executable-looking
  substrings inside their own comments (e.g. `StandardScaler().fit(X_train)`,
  `PCA(n_components=1)`, `GroupShuffleSplit(n_splits=1, ...)`) — harmless
  to a student, but inconsistent with Exercise 9's own, stricter
  convention of never writing an exact forbidden-looking call fragment
  even in a comment. Rewritten as prose-only hints before this WP's own
  structural test (`test_blanks_contain_no_executable_solution_even_commented`)
  was written, so the test and the fix shipped together, not found by a
  later failing run.
- Both native widgets' render functions initially only drew a matplotlib
  title inside the figure image (not real DOM text), which a Playwright
  test cannot assert on via `toContainText`. Added one `print(...)` status
  line per widget (`pipeline={path} held-out R2={r2}` /
  `rule={rule} chosen_depth={depth} test_mse={mse}`), matching
  `generate_exercise_09_notebook.py`'s own established convention for the
  same reason, before the Playwright spec was written against it.
- **Real bug found only by the actual browser run, not by any offline
  test**: every case originally used the heading `### Run it`. JupyterLab's
  table-of-contents sidebar renders every markdown heading as a navigable
  entry, so the page ended up with 6 extra elements whose own text also
  contains "Run it" — and Playwright's `page.click("text=Run")` (meant for
  the "Run" menu bar item) is a case-insensitive substring match that
  picked one of these non-visible sidebar entries first, then spun for the
  full 600s timeout waiting for it to become clickable. Confirmed by the
  exact error (`locator resolved to 20 elements... element is not
  visible`) in the first real Playwright run. Fixed by renaming all 6
  headings to `### First, the Code` (no heading in the notebook contains
  "run" after the fix, confirmed by a direct grep of every rendered
  heading). This could not have been caught by the headless/offline
  execution tests, which render no UI at all — exactly why the WP requires
  a real Chromium/Pyodide run.

## Tests added/run (see WP57_REPORT.md for exact counts/timings)

- `tests/test_exercise_12_lite_notebook.py` (new, 38 tests)
- `tests/test_exercise_12_reference_execution.py` (new, 28 tests)
- `tests/test_exercise_12_transition_page.py` (new, 9 tests)
- `tests/test_exercise_manifest.py` (existing, unmodified, re-run to
  confirm the production migration gate is untouched)
- `tests/test_exercise_10_notebook.py` (existing, unmodified, re-run to
  confirm the real legacy notebook is untouched)
- `tests/test_classify_release_change.py` (existing, unmodified, re-run —
  unaffected)
- `tests/test_book_structure.py` (existing, unmodified — 3 known/expected
  failures while this branch's local toc wiring is in place; see
  WP57_REPORT.md "Deviations")
- `interactive/e2e-book/exercise-12-lite.spec.ts` (new) — real
  Chromium/Pyodide run against the local combined build; see
  WP57_REPORT.md for the exact result.

## Explicitly not run (per the WP's own instruction)

- Exercises 1–9's offline/browser test suites.
- Course-wide Playwright (`npm run test:e2e:book` without a file filter).
