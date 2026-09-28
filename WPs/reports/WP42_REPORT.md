# WP42 report: Exercise 2 polish and active Exercise 1 migration

## Success or failure

**Success.** Both gates are complete, tested, and verified against a real
browser running the actual combined `jupyter-book` + `jupyter-lite` build.
Gate 1 required one focused correction cycle beyond the first pass (three
issues found by live browser testing, not assumed from source — see
"Gate 1: issues found and fixed" below); Gate 2 required one cascade-failure
fix found the same way. Nothing was merged, pushed, or deployed.

## Branches and SHAs

- Starting SHA (local `feature/wp41-jupyterlite-course-platform`):
  `e95dc516ffcaf6f8095e80dc171807a6d850a659`.
- Checkpoint branch (pre-work snapshot): `checkpoint/wp42-pre-work`, same SHA.
- Feature branch: `feature/wp42-exercise2-polish-exercise1-migration`.
- Final feature-branch SHA: see `git log -1` after this report's own commit
  (committed together with the exact changelog as this WP's closing commit).

## Pre-existing state check (WP instruction section 1)

At entry, `git status` showed one untracked file: `WPs/WP42_EXERCISE_2_POLISH_AND_ACTIVE_EXERCISE_1.md`
(the instruction file itself). No unexplained modifications to tracked
files. State was unambiguous, so a checkpoint branch was created and a
dedicated feature branch was cut from it before any edits, per the WP's own
instruction.

## Gate 1 — Exercise 2 polish

### Item 1 — Written responses

Removed the literal `YOUR ANSWER HERE` placeholder from all 5 editable
answer cells; each question is now `> **bold text**` with nothing else. Added
one notebook-wide instruction (in the "What this notebook covers" cell)
explaining how to edit and save an answer cell — verified it appears exactly
once (`tests/test_exercise_02_lite_notebook.py::test_one_notebook_wide_answer_cell_instruction`).
Verified live: double-clicking an untouched answer cell shows the bold
question with nothing to accidentally delete; editing, saving, reloading,
and downloading all preserve the edit (new Playwright test, see "Browser
verification" below).

### Item 2 — Checked-question layout

**Root cause, found live, not assumed:** at 390px, ipywidgets' own
stylesheet gives `.widget-checkbox`/`.widget-label-basic` a fixed 300px
width with `white-space: nowrap` + `text-overflow: ellipsis`, silently
truncating long option text (confirmed on "Choosing which features to use
because they correlate well with y_test."); `RadioButtons`' prior
`layout=Layout(width="max-content")` had the companion problem of sizing to
the single longest option's unwrapped width. Fixed with a small scoped
`<style>` block (`.checked-question` class) injected as a zero-height child
of each question's `VBox`, overriding the fixed width/nowrap/ellipsis with
`width: 100%` + `white-space: normal`. Verified live at 390px: the longest
option's `span` now reports `white-space: normal`, wraps to 2 lines
(`spanRectHeight: 44`), fits within the viewport (`labelRectWidth: 352`),
and `document.documentElement` reports zero horizontal overflow.

### Item 3 — Section 4 evaluation table

**First attempt (superseded):** used `pandas.DataFrame.style` +
`set_table_styles`/`set_properties` for left alignment. **Found live:** this
raised `AttributeError: The '.style' accessor requires jinja2` in the
browser kernel — jinja2 is not one of the packages `book/lite/overrides.json`
preloads — which aborted Section 4 and every cell after it on a fresh "Run
All Cells" (a real, load-bearing regression this WP's own testing caught
before shipping it). **Fix:** switched to `DataFrame.to_html()` (pandas
core, no jinja2 dependency) plus a scoped `<style>` block; needed
`!important` because JupyterLab's own dataframe stylesheet otherwise
outranks a plain matching rule (confirmed live: without `!important`, the
header row's inherited `text-align: right` from `to_html()`'s own inline
style still won). Verified live: every `<th>`/`<td>` in the rendered table
reports `text-align: left`.

### Item 4 — KNN check wording and substance

Replaced `# A graceful check: ...` with `# Run this to check your KNN
results.`. The check now compares against the established k=20 result
(R²≈0.664, MSE≈31.4) with documented tolerances (±0.05 R², ±3.0 MSE) and a
non-accusatory message for a different-but-complete result ("does not
automatically mean something is wrong ... a different valid implementation
... can shift these numbers"). Still gives a helpful, non-crashing message
for an unfinished attempt, and does not supply the solution. New tests
(`tests/test_exercise_02_reference_execution.py::KnnCheckCellBehavior`)
execute the actual check-cell source under three states — correct,
complete-but-wrong (R²=0.10, MSE=120.0), and unfinished (empty namespace) —
and assert on the exact printed message in each case.

### Item 5 — Conceptual figures

Only one cell in Exercise 2 fit "fixed conceptual illustration, not
data-dependent": Section 6's bias-variance schematic (its own comment said
so). Replaced the plotting code with a static image (rendered once, offline,
by new `scripts/render_exercise_02_bias_variance_figure.py`) embedded as a
cell **attachment** (nbformat's own mechanism, same as Activity 3B's
existing reference image — not a linked file, which would break for a
downloaded/Colab copy, and not an inline `data:` URL, which WP41R already
fixed for 3B for the same reason). All other figures in Exercise 2 are
measured/data-dependent or interactive and were left executable.

### Item 6 — Matplotlib deprecation warning

**Root-caused by live bisection, not assumed.** Four one-off test figures
were run in a live browser kernel after the full notebook had already
executed: a bare plot+legend+`tight_layout`+`show()` with no axvline, no
annotation, no secondary/twin axis; the same plus `axvline`; the same as
Section 7/8's plots (annotate with a blended transform) with
`layout="constrained"` instead of `tight_layout()`; the same with no layout
call at all. **All four warned, identically, including the maximally
minimal case.** This proves the warning is unconditional on this pinned
browser kernel (Pyodide's `matplotlib.use("pyodide")` backend + matplotlib
3.10.8) — it fires on every figure this kernel renders, regardless of
tight_layout, secondary axes, or annotations — and is not something fixable
by changing this notebook's plotting code. It is not specific to Sections 7
and 8 either: they are simply the first two cells in the *student* template
that actually call `plt.show()` at all (every earlier figure in the
notebook lives inside a still-blank "YOUR CODE HERE" activity that a fresh
"Run All Cells" never executes). **Fix:** one precise,
message-text-scoped filter in the setup cell —
`warnings.filterwarnings("ignore", message=r"The (width|height|x|y)
parameter as float was deprecated")` — never a blanket
`DeprecationWarning`/`MatplotlibDeprecationWarning` suppression. Verified
live: a full scroll-through of the executed notebook's output text shows
zero deprecation-warning lines (one unrelated, pre-existing
`threadpoolctl`/Pyodide `RuntimeWarning` remains, deliberately not
filtered, unrelated to matplotlib or this notebook's own code).

### Item 7 — Model-complexity spacing

Replaced the linear-1/k axis plus a secondary Axes k-tick row with a
**log-scaled** 1/k axis (`ax.set_xscale("log")`) and k values annotated
directly onto the primary Axes at their own complexity position (a new
shared helper, `annotate_model_complexity_axis`, used identically in
Sections 7 and 8). This was originally also expected to fix item 6's
warning; live bisection (above) showed it does not, and the two fixes are
independent. Two polish issues were found and fixed by live screenshot
inspection during this same item: the k-annotation row initially overlapped
the plot title (fixed with `ax.set_title(ax.get_title(), pad=26)` inside
the shared helper) and two numerically close k values (20 and the
validation-optimal 17) could land at the same height (fixed by alternating
the vertical offset by position). Verified live, light and dark: the axis
title stays "Model complexity", complexity increases left to right, every
tested k is legible with no overlap, and Section 8's black current-k marker
visibly lands on Section 7's curve at the same complexity for a given k
(same shared data arrays, same log scale).

### Versioning reconciliation and stale tests

`TEMPLATE_VERSION` in the generator was 2 (from WP41R) but
`book/config/exercise_manifest.json` still said 1 — a real, previously
unnoticed drift. Bumped the generator to 3 (this WP's real content changes)
and corrected the manifest to match; added
`tests/test_exercise_manifest.py::test_migrated_template_versions_match_notebook_metadata`
so this cannot silently drift again for any migrated exercise.

`iframe-height-contract.spec.ts` and `wp22-cross-chapter-dark-mode.spec.ts`
both still targeted Exercise 2's retired React/iframe KNN widget. Neither
was skipped: the iframe-contract case was removed with an explanatory
comment (there is no iframe left to check — Section 8 is a native
ipywidgets/Matplotlib figure, with its own coverage in
`exercise-02-lite.spec.ts`), and the dark-mode case was replaced with a real
test that switches JupyterLite's own theme to dark and confirms Section 8's
figure still renders with no error cells (matplotlib figures are
self-contained white-card PNGs, legible regardless of surrounding chrome —
confirmed by screenshot, see "Browser verification").

### Gate 1 proof

- Generator `--check`, structural tests, real-kernel reference execution:
  all pass (`tests/test_exercise_02_lite_notebook.py`,
  `tests/test_exercise_02_reference_execution.py`).
- One `jupyter-book build book` + one `jupyter lite build`.
- Full book Playwright suite: **149/149 passed in one clean run** (a
  separate, earlier 6-worker run had 2 unrelated flaky failures from
  parallel-load contention on this machine — both passed individually and
  in the final clean full-suite run; not a real regression).
- Manual/scripted browser verification: every question at 390px and in
  dark mode; KNN guard with a correct, a complete-but-wrong, and an
  unfinished attempt (offline, exact message assertions); Section 4 table
  alignment; Section 6 figure attachment; Section 7/8 log axis and k
  labels in light and dark; a written-answer edit surviving save, reload,
  and download.

## Gate 2 — Migrate Exercise 1: Exploratory Data Analysis

### Data

`scripts/export_abide_phenotypes_lite_data.py` derives the 13-column
curated teaching table (`book/config/eda_phenotype_columns.json`) **offline**
from the already-committed, already-approved
`book/_static/widgets/data/abide_table_inspection.json` (WP09/WP10's own
export of the same pinned source) rather than a second, independent network
fetch — guaranteeing byte-identical values to what the existing (now
retired) browser widgets already showed, with no risk of drift between two
export paths. Verified against the pre-migration notebook's own committed
outputs: 1114×13 shape; missingness counts for all 8 columns with any
missing values (e.g. `ADI_R_SOCIAL_TOTAL_A` 812, `FIQ` 99); complete-case
counts (95 for all 13 columns, 1015 for the core-variable set); FIQ median
112.0; FIQ–VIQ Pearson r≈0.833 — all bit-for-bit or matching to the
established rounding, via
`tests/test_exercise_01_reference_execution.py`, which executes the
completed reference notebook's actual cell sources.

### Activities (WP target: 4-6 code tasks, ~3-4 answers, 4-6 questions)

- 4 student code tasks: `tail()`/`sample()` (Section 2); the missingness
  table (Section 4, light hints only, no near-complete solution); dropping
  incomplete rows into a new dataframe (Section 5); filling one numerical
  feature's missing values with its median into a copy (Section 5). Each of
  the two Section 5 tasks has its own student-facing sanity-check cell
  (correct / different-but-valid / incomplete feedback, never silently
  solving it) — matching the pattern already established for Exercise 2's
  KNN check.
- 4 editable written answers: head/tail/sample ordering; the missingness
  heatmap; the retention explorer; a group-comparison confound.
- 4 checked questions: identifying categorical columns; histogram bin
  count; the FIQ–VIQ construction-vs-mechanism distinction; (Section 6).

### Interactives rebuilt notebook-native

- **Complete-case retention explorer** (Section 4): the one interactive the
  WP explicitly named for preservation. Rebuilt as an `ipywidgets`
  checkbox group (11 candidate variables, the same set as the old
  `eda_retention.json` config) driving a live retained-count readout and a
  per-site retention bar chart — verified live: ticking "Handedness
  category" changes the retained-count text.
- **Histogram** (Section 6): rebuilt with a `Dropdown` (7 variables) and a
  `BoundedIntText` for bin count ("a usable typed numeric input", per the
  spec) driving a live-refit Matplotlib histogram — verified live: changing
  the variable changes the rendered figure (confirmed via the image's own
  changed `src`, since the plot title is baked into the PNG raster, not DOM
  text).
- **head/tail/sample comparison** and **correlation explorer**: per the
  spec's own item 2/6 wording ("students then write code ... themselves"; "the
  Pearson correlation-matrix code/figure"), these are replaced by given/
  written code rather than rebuilt as separate interactives — there is no
  remaining interactive surface for either in the new notebook, matching
  the spec's own activity changes rather than an omission.

No Spearman, no outlier/range-check section, no time budget, no new
modelling lesson — enforced by
`tests/test_exercise_01_lite_notebook.py` (`test_no_spearman`,
`test_no_outlier_or_range_check_section`, `test_no_time_budget_language`)
and manually confirmed against the WP's own list.

### Prose reduction

Student-facing markdown prose (same stripping method WP41 used for
Exercise 2): **2900 words → 737 words (-75%)**, while adding the 4+4+4
active-learning elements above (old notebook read from
`archive/pre-wp41-jupyterlite-course-platform`; new notebook is
`book/lite/files/exercise_01.ipynb`).

### A cascade-failure bug found and fixed by live testing

The missingness heatmap (a **supplied** cell, not a student activity)
originally read `missing_summary` — a variable only the student's own
Section 4 blank defines. On a fresh "Run All Cells" against the
**unstarted student template** (exactly what a student's first open looks
like), this threw `NameError` at the heatmap cell and halted every
following cell, including the retention explorer, Section 5, and Section 6
entirely. Found via the same live-browser-first methodology as WP41R's own
blockers, not assumed from source. **Fixed** by having the heatmap compute
its own top-missing-columns list directly from `data`, independent of
whether the student's blank succeeded — matching the "one incomplete answer
must not cascade into unrelated failures" requirement, and the pattern
Exercise 2's Section 8 already uses (importing `KNeighborsRegressor`
itself so it does not depend on Section 5's blank). A regression test
(`test_heatmap_does_not_depend_on_the_student_missingness_blank`) now
checks the fix structurally.

### Retiring the old canonical page (maintainer guide section 10)

Followed the four-step sequence: (1) the new notebook's structural suite
and its reference notebook's numeric-integrity suite pass; (2)
`exercise-01-lite.spec.ts` passes against a real combined build; (3) the
manifest's Exercise 1 entry is `"migrated"` with Lite fields filled in; (4)
every exercise-content-audit test that read the old canonical page was
updated. Five such files needed changes, the same order of magnitude WP41
found for Exercise 2:

- `tests/test_notebook_corrections.py` — **deleted** (373 lines, entirely
  about the pre-migration notebook's exact structure; the same treatment
  WP41 gave the analogous `test_exercise_02_notebook.py`).
- `tests/test_build_portable_notebook.py` — **deleted**: this file's sole
  purpose was testing `build_portable_notebook.py`'s chapter_01-specific
  MyST-rewriting behavior (banner/setup/column-rewriting), which no longer
  runs now that chapter_01 is excluded from that pipeline's `NOTEBOOKS`
  registry (the same treatment chapter_02 already got from WP41).
- `tests/test_notebook_opening_structure.py`,
  `tests/test_think_first_shared_class.py` — chapter_01 removed from their
  hardcoded notebook dicts, mirroring the exact comment/pattern already in
  place for chapter_02.
- `tests/test_wp24_content_audit.py` — `Exercise1DecisionBlockOrder`
  retired (its "Our approach in this exercise" block no longer exists, cut
  as part of this WP's own concision pass); `Exercise1NoImputeJargon`'s
  plain-language check repointed from the transition page to the real
  lesson content (`EX1_PORTABLE`); `RedundantReproductionCellsCollapsed`'s
  Exercise-1-specific seaborn/hide-cell cases retired (no seaborn, no
  hide-cell concept in a JupyterLite notebook). `Exercise1NoSpearman` and
  `Exercise1CorrelationWidgetPearsonOnly` needed no changes (they either
  check unrelated widget-config/TS files, or pass trivially against the new
  content).
- `scripts/smoke_portable_notebook.py` — chapter_01's entry removed. Its
  `nbclient`-based real-kernel smoke test hangs indefinitely on this
  notebook's `ipywidgets.Output()`-based interactive widgets (the retention
  explorer and histogram), the exact same known issue WP41's report
  documented for Exercise 2's Section 8 — confirmed live: a bounded run of
  the existing, unmodified chapter_02 entry against this same script never
  completed within 100 seconds either. **This is a pre-existing gap, not
  introduced by this WP** — chapter_02 has had it, unnoticed, since WP41
  shipped. Flagged for the course author below; not fixed here (out of
  scope).
- `tests/test_exercise_03/06/07/08/09_notebook.py` — five files had a
  "shorter than Exercise 1" cell-count comparison that assumed Exercise 1
  was the book's longest lesson; now that it is a 2-cell transition page,
  each was changed to a fixed, already-satisfied absolute cap (≤45 cells,
  matching Exercise 3's own existing explicit range) instead.

### Gate 2 proof

- Generator `--check`, structural tests, real-kernel reference execution:
  all pass (`tests/test_exercise_01_lite_notebook.py`,
  `tests/test_exercise_01_reference_execution.py`,
  `tests/test_exercise_01_transition_page.py`).
- One `jupyter-book build book` + one `jupyter lite build` (same combined
  build Gate 1 used, rebuilt after Gate 2's own generator changes).
- Full book Playwright suite: 149/149 passed (same clean run reported under
  Gate 1 — both gates were verified together in the final pass).
- `exercise-01-lite.spec.ts` (new, 8 tests): opens/runs and reproduces
  1114×13; the retention explorer changes the retained count on a tick;
  the histogram widget changes its figure on a variable change; a checked
  question grades correctly; a written-answer edit survives save, reload,
  and download; Reset restores the template and Back returns to Contents;
  390px has zero horizontal overflow; running the data cell before setup
  gives an actionable `RuntimeError`, not a bare `NameError`.
- Manual/scripted dark-mode check: switched JupyterLite's own theme to
  dark, ran every cell, confirmed zero error cells and the final checked
  question's long option text still wraps fully and legibly (screenshot).

## Every test, build, and manual result

**Python (offline, no network)**: `python -m unittest discover -s tests` —
**1086 tests, all green, 11 skipped** (network-only, expected offline). Run
three times across this WP (after Gate 1, after Gate 2, and once more at
the end) — green every time.

**Generators**: `generate_exercise_01_notebook.py --check`,
`generate_exercise_02_notebook.py --check`,
`generate_exercise_01_transition_page.py --check`,
`export_abide_phenotypes_lite_data.py --check`,
`export_abide_lite_data.py --check` (unchanged, re-run as a courtesy) — all
report up to date/OK. `build_portable_notebook.py --check` — up to date for
every notebook still in its registry (chapters 3–10).

**Frontend**: `npm run typecheck` — clean.

**Jupyter Book build**: `jupyter-book build book` — succeeds, 0 errors (the
one pre-existing warning noted in WP41's report is unrelated to this WP).

**JupyterLite build**: `jupyter lite build ...` — succeeds twice (once
after Gate 1, once after Gate 2), coexists with the book hub.

**Playwright, built book** (`playwright.book.config.ts`, real headless
Chromium against the actual combined build, full suite): **149 passed, 0
failed**, one clean run. Includes `exercise-01-lite.spec.ts` (8/8),
`exercise-02-lite.spec.ts` (9/9, including the two new tests this WP adds:
a written-answer persistence check and the fixed Section 8 slider test),
`chapter01.spec.ts` (rewritten, 4/4), `chapter02.spec.ts` (unchanged, 4/4),
`launch-buttons.spec.ts` (18/18, including the two new "migrated, no Colab
button" cases for chapters 1 and 2), `iframe-height-contract.spec.ts`
(23/23, the remaining legacy exercises' iframes), and
`wp22-cross-chapter-dark-mode.spec.ts` (6/6, including the rewritten
Exercise 2 case).

## Deviations and decisions requiring course-author review

1. **`smoke_portable_notebook.py`'s `nbclient`-based smoke test cannot run
   against either migrated exercise's portable notebook** (Section
   "Retiring the old canonical page" above) — their `ipywidgets.Output()`
   widgets hang a real, frontend-less kernel indefinitely. This is a
   pre-existing gap for Exercise 2 since WP41 (not previously reported),
   now also true for Exercise 1 (excluded here, consistently). The safe
   alternative already exists and is used by both exercises' own
   numeric-integrity tests (direct cell-source execution, not `nbclient`);
   a future WP could either accept this permanently or invest in a
   JupyterLite-aware smoke-test replacement.
2. **The four checked questions per exercise, not "4-6," landed at exactly
   4 for Exercise 1** (vs. Exercise 2's 5) — judged sufficient for the
   content's actual decision points rather than added to hit a round
   number.
3. **Exercise 1's histogram widget only exercises Matplotlib's own figure
   object identity for its browser test** (comparing the rendered image's
   `src` before/after), since the plot title (the only human-readable
   confirmation of which variable is shown) is baked into the PNG raster,
   not DOM text — the same constraint Exercise 2's own figures have.
4. **The `abide_phenotypes.csv` export is derived from
   `abide_table_inspection.json` rather than a fresh, independent network
   fetch of the pinned upstream CSV.** This was a deliberate choice (byte-
   identical to the already-approved widget data, no risk of a second
   export path drifting from the first) but means this export's own
   `--write` mode needs that JSON artifact to exist and stay correct; it is
   not a from-scratch, network-verified pin the way `export_widget_data.py`
   and `export_abide_lite_data.py` are.

## Confirmation

Nothing was merged, pushed, or deployed. No GitHub Actions workflow was
triggered or inspected. `Homework_Materials/` was not touched. No exercise
other than Exercises 1 and 2 was migrated or modified. No other WP was
started.
