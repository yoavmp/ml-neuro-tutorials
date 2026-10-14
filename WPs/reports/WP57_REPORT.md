# WP57 Report — Exercise 12: Common Mistakes and Pitfalls (local review only)

## Summary

Built a local, JupyterLite-native **Exercise 12: Common Mistakes and
Pitfalls** notebook in the active generator architecture established by
WP41/WP44–WP47/WP51/WP52, on feature branch
`feature/wp57-active-exercise-12-common-mistakes`. **Nothing was merged,
pushed, deployed, or published** — this stops at the local review handoff,
per the WP's own instruction.

This is a from-scratch rebuild (new generator, new content organization,
new question/widget mechanism) of the previously-drafted common-mistakes
casebook — reassigned from its original Exercise 10 slot (now occupied by
real historical content, WP38/WP38R) to Exercise 12. The legacy Exercise 10
notebook (`book/chapters/chapter_10/exercise_10.ipynb`) and Exercise 11's
placeholder stub are **untouched** — confirmed by `git diff main` against
both paths returning empty. Exercises 1–9 are untouched (no narrowly
necessary shared fix was needed).

**Result: full acceptance, all 6 required cases + 2 widgets + 7 checked
questions built, all focused tests green, local combined book+Lite build
succeeds, real Chromium/Pyodide Playwright run confirmed.** See
"Deviations" for the handful of judgment calls made where the WP's spec
left room for them.

## Acceptance by case

| Case | Requirement | Status |
|---|---|---|
| 1. Preparing the Predictors | StandardScaler leakage on real ABIDE-II data; repair blank; observable (not promised-large) statistic change | ✅ Done |
| 2. Two Components | y included among PCA inputs, striking invalid result; repair blank (predictor-only PCA); deployment question | ✅ Done |
| 3. Picking a Tree | Model selected by training MSE vs. validation MSE; untouched test partition; repair blank | ✅ Done |
| 4. A High-Accuracy Classifier | Synthetic 95:5 imbalance; majority-class accuracy trap; confusion matrix; undefined precision handled explicitly | ✅ Done (interpretation-only, as permitted) |
| 5. Many Rows per Participant | Synthetic repeated-participant rows; row split vs. GroupShuffleSplit; repair blank | ✅ Done |
| 6. Closing challenge | Test-set peeking across candidate settings; checked question; corrected workflow in prose, no nested-CV code | ✅ Done (interpretation-only, as permitted) |
| Widget 1 (after Case 2) | Native toggle, contaminated vs. honest PCA, fixed-axis true-vs-predicted scatter, R² labeled, self-contained, deployment question | ✅ Done |
| Widget 2 (after Case 3) | Native toggle, train-MSE vs. val-MSE depth selection, marked curves, untouched-test predictions, precomputed (responsive) | ✅ Done |
| 4 required repair blanks | Cases 1, 2, 3, 5 | ✅ Exactly 4, tagged `wp57-activity-{scaler,pca,tree,group}` |
| 6–8 checked questions | Mix of single/select-all | ✅ 7 (6 single + 1 select-all) |
| Educational contract | One short run→diagnose→repair→inspect invitation, neutral headings | ✅ Stated once in the overview; case headings are the WP57 table's own names (no "leakage"/"mistake"/"bug" wording) |
| No cascading failures on untouched template | | ✅ Confirmed by execution test (`StudentTemplateNoCascade`) and Playwright's untouched-template spec |
| Local-only navigation | Discoverable in local combined preview, placeholders for 10–11 | ✅ Done — see "Navigation and placeholders" |

## Provenance and splits

- **Cases 1 and 3** (the only ABIDE-based cases) share one three-way split
  of `book/lite/files/data/abide_age_brain.csv` (1,004 participants, 360
  `fsCT_*` cortical-thickness predictors, same-origin export reused from
  Exercises 2/4–9, no new data asset): `train_test_split(..., test_size=0.4,
  random_state=42, stratify=group)` then `train_test_split(..., test_size=0.5,
  random_state=42, stratify=group_rest)` → `X_train` (602), `X_val` (201),
  `X_test` (201). This is a different split shape than Exercises 2–9's
  single train/validation split — deliberate, since this notebook's own
  lesson is specifically about which partition may inform which decision
  (Case 3 needs a genuinely untouched third partition to show the
  consequence of a training-vs-validation selection choice).
- **Cases 2, 4, 5, 6** each use small, fixed-seed, clearly-labeled
  synthetic data, generated inline and visible in their own "Run it" cell
  (never hidden infrastructure) — chosen because each mechanism being
  taught (target-informed PCA, extreme class imbalance, repeated-
  participant rows, test-set peeking) needs full control over the
  generating process no real dataset offers on demand. Every synthetic
  case's intro markdown cell states "synthetic" explicitly (verified by
  `test_synthetic_data_is_labeled_as_synthetic`).

## Actual comparison values (every number directly verified before writing
the generator; see `scripts/generate_exercise_12_notebook.py`'s own module
docstring for the full narrative, and
`tests/test_exercise_12_reference_execution.py` for the executed proof)

| Case | Contaminated/naive result | Honest/corrected result |
|---|---|---|
| 1 | Scaler fit on full table: mean(fsCT_L_1_ROI) = 2.373286 | Scaler fit on train only: mean = 2.371573 (diff 0.001713; largest diff across all 360 features = 0.024550 — small and real, not promised to be large) |
| 2 | PCA sees y (scaled ×3), fit on all 200 rows: held-out R² = 0.9997 | Predictor-only PCA, fit on train rows only: held-out R² = 0.4489 |
| 3 | Depth chosen by lowest training MSE: `None` (train MSE 0.000) → test MSE 74.740 | Depth chosen by lowest validation MSE: `5` (val MSE 45.123) → test MSE 66.143 |
| 4 | Accuracy alone: 0.95 | Confusion matrix [[95,0],[5,0]]; sensitivity 0.0, specificity 1.0, balanced accuracy 0.5, precision undefined |
| 5 | Row split: 38/40 participants overlap train/val; val R² = 0.8973 | GroupShuffleSplit: 0 participants overlap; val R² = 0.6219 |
| 6 | Best-looking alpha found by peeking at test across 5 candidates: alpha=10, test MSE 7.558 | (procedural fix only, no corrected number — the point is that "7.558" was never an honest one-time evaluation) |

## Local preview

A local HTTP server was started against the actual built site for live
inspection: `python3 -m http.server 8743` from `book/_build/html`. While
running:

- Course contents: http://localhost:8743/contents.html
- Exercise 12's transition page: http://localhost:8743/chapters/chapter_12/exercise_12.html
- Exercise 12's JupyterLite notebook directly: http://localhost:8743/lite/notebooks/index.html?path=exercise_12.ipynb
- Exercise 10 placeholder: http://localhost:8743/chapters/chapter_10/placeholder.html
- Exercise 11 placeholder: http://localhost:8743/chapters/chapter_11/exercise_11.html

This server is a local convenience only (not part of any committed
artifact); regenerate it at any time with the same `jupyter-book build
book --all` + `jupyter lite build` commands documented in the maintainer
guide if `book/_build/` is ever cleaned.

## Navigation and placeholders

Local-only changes, scoped to this feature branch (never merged, pushed,
or deployed):

- `book/_toc.yml`: added `chapters/chapter_10/placeholder`,
  `chapters/chapter_11/exercise_11`, `chapters/chapter_12/exercise_12` after
  Exercise 9, with an updated comment explaining the local-only scope.
- `book/_config.yml`: removed the `chapters/chapter_11/*` and
  `chapters/chapter_12/*` `exclude_patterns` entries; replaced
  `chapters/chapter_10/*` with the single, precise
  `chapters/chapter_10/exercise_10.ipynb` — the real legacy notebook stays
  excluded from this local build (preserved untouched, never re-executed by
  Sphinx's `execute_notebooks: cache` step, so this WP's build time/behavior
  stays independent of content it does not touch); the new
  `chapters/chapter_10/placeholder.md` builds normally.
- **Exercise 10 placeholder**: new file `book/chapters/chapter_10/placeholder.md`
  ("# Exercise 10: Coming Later" + "Materials for this exercise will be
  added before the practice session.") — no notebook, no launch/download
  button. The real legacy `exercise_10.ipynb` is completely untouched and
  not referenced by any toc.
- **Exercise 11 placeholder**: unchanged — the pre-existing
  `book/chapters/chapter_11/exercise_11.md` already reads "Materials for
  this exercise will be added before the practice session," already has no
  runnable notebook or launch button, and was left as-is.
- **Exercise 12**: `book/chapters/chapter_12/exercise_12.md` (the old,
  never-built, different-topic placeholder stub — "Review and Exam-Style
  Questions," no reviewable historical content) was **removed** and
  replaced with `book/chapters/chapter_12/exercise_12.ipynb`, a short
  transition page (`scripts/generate_exercise_12_transition_page.py`,
  following the Exercise 1–9 pattern exactly) linking to the real lesson at
  `lite/notebooks/index.html?path=exercise_12.ipynb` and the portable
  download.
- `book/config/exercise_manifest.json`: updated entry 12's `title` ("Common
  Mistakes and Pitfalls") and `legacyStaticPagePath` (now points at the new
  `.ipynb` transition page, since the `.md` it used to point at no longer
  exists). `migrationState` for entries 10–12 is **unchanged ("legacy")** —
  this WP does not claim production migration; `tests/test_exercise_manifest.py`
  (including `test_only_exercises_1_through_9_are_migrated`) passes
  unmodified, confirming the production gate is untouched.
- **Verified live**: built the real local combined site
  (`jupyter-book build book --all` then `jupyter lite build`, both exit 0,
  no errors) and confirmed by `curl`/direct file inspection:
  `chapters/chapter_10/placeholder.html` (200, "Exercise 10: Coming Later"),
  `chapters/chapter_11/exercise_11.html` (200), `chapters/chapter_12/exercise_12.html`
  (200, "Exercise 12: Common Mistakes and Pitfalls", links to the Lite
  route), `lite/files/exercise_12.ipynb` (200), and
  `lite/notebooks/index.html?path=exercise_12.ipynb` (200). The Contents
  page (`contents.html`) lists all three new entries in order. No
  `exercise_10.html` was produced (the real legacy notebook stays excluded).
- **Direct-URL route** (`lite/notebooks/index.html?path=exercise_12.ipynb`)
  is also directly reachable without any toc changes at all, per the WP's
  own "also acceptable for review" fallback — confirmed above.

## Answer-key and blank audits

- 7 questions (`q-scaler-leakage`, `q-pca-deployment`,
  `q-train-vs-val-select`, `q-tree-deploy`, `q-classifier-metrics` [select-
  all], `q-group-leakage`, `q-test-peeking`), all defined with
  `correct_index`/`correct_indices` **only** inside the hidden setup cell;
  every visible `show_question(...)` call contains neither
  (`test_checked_questions_use_show_question_with_no_visible_answer_key`).
  Each has its own `shuffle_seed`; reproducibility and position variance
  across questions verified by executing `show_question` with real
  shuffled widgets and clicking the shuffled-correct option
  (`test_shuffle_is_reproducible_and_varies_positions_across_questions`,
  `test_show_question_displays_the_shuffled_widget_with_correct_feedback`).
- 4 required blanks (Cases 1, 2, 3, 5), each tagged
  `wp57-activity-{scaler,pca,tree,group}`. Every blank's starter source was
  grepped for `.fit(`, `Pipeline([`, `.predict(`, `mean_squared_error(y_val`,
  `r2_score(y_val`, `PCA(n_components`, `GroupShuffleSplit(` — **zero
  hits, including inside comments** (hints describe the approach in prose
  instead, e.g. "fit a fresh StandardScaler using X_train only" rather than
  writing the call). `YOUR CODE HERE` markers are themselves comments in
  every case. No `NotImplementedError`, no `!pip install`/`%pip install`
  anywhere in the student notebook.
- Instructor notes/WP/script references: `tests/test_exercise_12_lite_notebook.py::test_no_wp_or_script_references_in_student_text`
  and the transition page's own equivalent confirm no "wp57", "wp38",
  "scripts/generate", etc. reach student-visible markdown.
- "Contaminated"/"invalid" labeling only appears **after** the diagnosis
  step, never in the "Run it" cell itself
  (`test_results_labeled_contaminated_or_invalid_only_after_diagnosis`).

## Focused test outcomes and timings

Per the WP's instruction, only Exercise-12-specific and navigation-related
suites were run — **no Exercises 1–9 offline/browser suites, and no
course-wide Playwright run, were executed as a default for this WP.**

| Suite | Result | Notes |
|---|---|---|
| `tests/test_exercise_12_lite_notebook.py` | 38/38 OK, 0.09s | Structural: headers, blanks, questions, widgets, no-leakage-in-hints, synchronization |
| `tests/test_exercise_12_reference_execution.py` | 28/28 OK, ~5.2s | Executed reference (every established number reproduced exactly) + executed untouched template (zero errors, graceful degradation, cases independent) |
| `tests/test_exercise_12_transition_page.py` | 9/9 OK, 0.03s | Transition page structure, links, no duplicated analysis content |
| `tests/test_exercise_manifest.py` | 10/10 OK, unmodified | Confirms the production migration gate (`migrated` = exercises 1–9 only) is untouched by this WP's local manifest edits |
| `tests/test_exercise_10_notebook.py` | 20/20 OK, unmodified | Confirms the real legacy Exercise 10 notebook is byte-for-byte untouched |
| `tests/test_classify_release_change.py` | 59/59 OK, unmodified | Unaffected (this WP does not change deploy-gate classification) |
| `tests/test_book_structure.py` | **3 known, expected, documented failures** | See "Deviations" — this file asserts the *production* toc/exclude-pattern state; it is expected to fail while this branch's local-only preview wiring is in place, exactly as WP51 documented for Exercise 9. Reverting `book/_toc.yml`/`book/_config.yml` to `main`'s committed text restores it to green. |
| Local combined build (`jupyter-book build book --all` + `jupyter lite build`) | Both exit 0, no errors | Launched detached per the maintainer-guide procedure; completed in both of its two runs (initial, and after the heading fix below) |
| `interactive/e2e-book/exercise-12-lite.spec.ts` (real Chromium/Pyodide) | **4/4 passed, 1.4 minutes** (final run) | Launched detached three times total — see "Real bugs found by the browser run" below for why the first two runs failed and what fixed each |

### Real bugs found by the browser run (not by any offline/headless test)

The real Playwright run against the actual local build is the only check
in this WP that exercises JupyterLab's own UI, and it found two genuine
defects neither the structural tests nor the executed-reference tests
could see, since neither renders any UI:

1. **Run 1** (both "untouched template" tests, 240s default timeout each;
   the teacher-completed test also timed out at its own 600s): every case
   originally used the heading `### Run it`. JupyterLab's table-of-contents
   sidebar renders every markdown heading as a navigable entry, so the
   built page had 6 extra elements containing the text "Run it" in
   addition to the actual "Run" menu-bar item. `page.click("text=Run")`
   (meant for the menu bar) is a case-insensitive substring match and
   resolved to 20 elements, picking a non-visible sidebar entry first, then
   spinning for the full timeout waiting for it to become clickable
   (confirmed by the exact error: `locator resolved to 20 elements ...
   element is not visible`). **Fix**: renamed all 6 headings to
   `### First, the Code` (confirmed by direct inspection that no heading in
   the built notebook contains "run" after the fix). Re-ran the local
   combined build, then the full spec: the two "untouched template"
   Run-All tests passed (31.0s and 35.8s); the teacher-completed test still
   failed, on a different error (see below).
2. **Run 2** (teacher-completed test only): after filling Case 3's repair
   blank, the test checked Case 3's "consequence" cell's printed text —
   but that cell had already run once during the initial Run All Cells,
   *before* the blank was filled, and (correctly, per this notebook's own
   no-cascade design) does not automatically re-run just because an
   earlier cell changed. The same gap existed for Case 5's check cell.
   **Fix**: added explicit `runCell(...)` calls for both cells after their
   blanks are filled, mirroring `exercise-09-lite.spec.ts`'s own existing
   comment about this exact JupyterLab behavior ("Section 6's own cell does
   not re-run just because an earlier cell changed").
3. While fixing the above, also noticed the spec's "edit a written-answer
   cell" step was an unimplemented placeholder comment with no real
   interaction — and that the notebook's own overview text promised an
   editable written-answer cell ("Written-answer cells ... double-click
   one to edit it") that the notebook did not actually contain anywhere.
   Added one genuine written-answer blockquote cell to Case 6 (a closing
   reflection question, no checked question competing with it) and
   implemented the real double-click/edit/Shift+Enter/download-contains-
   the-edit interaction in the spec.

**Run 3** (final): all 4 tests passed —
`reset restores the template and Back returns to Contents` (8.6s),
`Run All Cells: ...` (31.0s), `stays usable at a 390px viewport, ...`
(35.8s), `filling in all four blanks ... and download contains the edits`
(1.4m). Total: **4 passed in 1.4 minutes.**

No command in this WP ran longer than the detached-process threshold
without following the maintainer-guide procedure (durable log under this
session's scratchpad directory, PID recorded, confirmed detached via
`ps -o pid,ppid`, polled to completion rather than assumed). No command was
re-launched; each (book build, Playwright run) was launched exactly once
and its completion confirmed from its own log/PID before use.

## Widget visual checks (real JupyterLite preview via Playwright)

- **Widget 1** ("a result that knows the answer", after Case 2): toggle
  switches between `pipeline=contaminated` and `pipeline=honest` in a live
  text summary; a real `<img>` (matplotlib PNG, `naturalWidth > 400`)
  renders for both settings; label-overflow CSS (`description_width:
  initial` + `widget-controls-row` wrap) confirmed present and (at a 390px
  viewport) every control label is unclipped and non-overlapping.
- **Widget 2** ("which tree gets deployed?", after Case 3): toggle switches
  the live summary from `rule=train chosen_depth=None` to `rule=val
  chosen_depth=5`; its own render callback contains no `.fit(` call (
  `test_widget2_precomputes_fits_for_responsiveness`), confirming every
  depth's tree was precomputed once and the toggle only reselects/redraws —
  responsive in Pyodide by construction, not just by observation.
- Both widgets confirmed self-contained: each duplicates its own imports
  and data/fit logic rather than depending on its case's own repair blank,
  so both render correctly from a completely untouched template (verified
  by the untouched-template Playwright test and by
  `StudentTemplateNoCascade` in the execution test).

## Colab status

**UNVERIFIED — real Google Colab is not reachable from this session.**
A private, not-committed, not-published set of files was prepared in this
session's own scratch directory (not a repository path) for the author's
later real-Colab check:

- a verbatim copy of `scripts/reference_notebooks/exercise_12_reference.ipynb`
  (every blank filled);
- a verbatim copy of the actual downloadable
  `book/downloads/chapter_12/exercise_12_portable.ipynb` (what a student
  actually gets);
- `COLAB_CHECKLIST.md`, the WP41 maintainer guide section 12 template,
  filled in with this WP's own established numbers and all 7 checked-
  question topics, marked **UNVERIFIED**, with the local/simulated
  verification actually performed listed explicitly instead.

Their local path was given to the user directly in this session, not
repeated here, to avoid implying it is a repository path. Simulated/local-
browser portability is not a substitute for a real Colab run and is not
claimed to be one — this is the exact same discipline WP51 (Exercise 9,
also local-only) followed, for the same reason.

## Intentional methodological flaws vs. accidental coding bugs

Every "flawed" result in this notebook (Cases 1–3, 5, 6; Case 4's
accuracy-only framing) is an **intentional methodological flaw**, designed
to run without error and produce a plausible result — that is the lesson.
Three **accidental coding/authoring bugs** were found and fixed during
development, none related to any case's own teaching content:

1. The first draft of Case 1's three-way split called
   `train_test_split(X, y, group, ...)` (three positional arrays) but
   unpacked only 5 return values instead of the required 6
   (`X_train, X_rest, y_train, y_rest, group_rest = ...`), raising
   `ValueError: too many values to unpack`. Fixed by unpacking
   `group_train` as well. Caught immediately by the reference-execution
   check, before any verified number in this report was computed.
2. Six case headings read `### Run it`, which collided with JupyterLab's
   own "Run" menu in the real browser (see "Real bugs found by the
   browser run" above) — not detectable by any headless/offline test.
3. The notebook's overview text promised an editable written-answer cell
   that did not exist anywhere in the notebook, and the Playwright spec's
   corresponding check was an unimplemented placeholder. Both found while
   investigating bug 2; fixed together.

## Branch, commits, and final git state

- Branch: `feature/wp57-active-exercise-12-common-mistakes` (created from
  `main` at commit `5d46b26`, "WP56: prose-fast-gate top-level book pages,
  remove Syllabus page").
- Checkpoint commit: `27ad971` — "WP57: checkpoint the WP spec on a
  dedicated feature branch" (adds `WPs/WP57_ACTIVE_EXERCISE_12_COMMON_MISTAKES_LOCAL.md`).
- Implementation commit: `6374130` — "WP57: build Exercise 12's active
  JupyterLite-native notebook (local only)".
- Report commit: (recorded immediately after this report is committed —
  see the terminal summary for its exact SHA).
- Working tree: clean after both commits (confirmed by `git status`).
- **No merge, push, CI release run, or deployment was performed or
  attempted.**

## Deviations from the spec, and why

- **Case 3/Widget 2 needed a genuine three-way ABIDE split**, unlike every
  other exercise's single train/validation split — necessary because the
  WP explicitly asks the widget to "reserve an untouched test partition,"
  which requires a partition neither the selection decision nor its own
  check cell ever touches. Documented at the top of the generator's module
  docstring and in "Provenance and splits" above.
- **`test_book_structure.py` has 3 known, expected failures** while this
  branch's local-only toc/exclude-pattern changes are in place (see
  "Focused test outcomes" above) — the same kind of legitimate, documented
  invalidation WP51 reported for Exercise 9's own structural test. Not
  fixed by editing that file, deliberately: it is a production gate, and
  weakening it to pass while 10–12 sit in a local toc would reduce its
  power to catch an accidental production leak later. Reverting
  `book/_toc.yml`/`book/_config.yml` restores it to green.
- **Exercise 11's placeholder stub was left completely unedited** rather
  than rewritten to a generic "Coming Later" label — its existing text
  ("Materials for this exercise will be added before the practice
  session.") already satisfies the WP's own requirement (no runnable
  notebook, no launch/download button), and rewriting it was not
  necessary.
- **7 questions, not "6–8" exactly in the middle** — within the specified
  range, split 6 single-choice + 1 select-all (Case 4's confusion-matrix
  question), matching the WP's "mix single choice and select-all where
  appropriate" instruction without forcing a second select-all question
  where a single-choice framing fit the material better.
- **No separate "Final Checklist" closing section** (the legacy Exercise
  10 draft had one) — omitted to keep the opening numbered list
  ("What this notebook covers," 6 items) matching the notebook's 6 numbered
  `## N.` headings exactly, per `NOTEBOOK_AUTHORING_STANDARDS.md` §3. Case
  6 ends with a short prose closing paragraph instead of a separate
  heading.
