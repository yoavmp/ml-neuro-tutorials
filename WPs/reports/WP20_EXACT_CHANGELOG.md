# WP20 Exact Changelog

## Commits

1. `b804a6d81567247cfbe67f5df5ca399d58a616f2` — "WP20: add WP document (checkpoint before implementation)" (branch `edit/student-facing-notebook-language`)
   - Created: `WPs/WP20_STUDENT_FACING_EDITORIAL_PASS.md`
2. `6b1243d00685183d7c1edb60a61d96d5b95a198c` — "WP20: student-facing editorial pass for Exercises 1-4" (branch `edit/student-facing-notebook-language`)
   - See file list below.
3. `9f9178cd0f27d5fd0ce8c5f42e0de5d09105cba1` — Merge commit, `git merge --no-ff edit/student-facing-notebook-language` into local `main` (`Merge: 8fb89a1 6b1243d`)

Start tag: `wp20-start` → `8fb89a1f876c0e44008627d7cc562530167b4305`

## Files created

- `WPs/WP20_STUDENT_FACING_EDITORIAL_PASS.md` (checkpoint commit)
- `NOTEBOOK_AUTHORING_STANDARDS.md` (implementation commit)
- `WPs/reports/WP20_REPORT.md` (this pass's report commit, created after merge)
- `WPs/reports/WP20_EXACT_CHANGELOG.md` (this file, created after merge)

## Files modified (implementation commit `6b1243d`)

| File | Change |
|---|---|
| `book/chapters/chapter_01/exercise_01.ipynb` | Title cell trimmed to title-only; "What this notebook covers" gained an identifying sentence + "In this notebook, you will:" transition (list content unchanged); cells 4 and 6 (imports, ABIDE-II load) changed from `hide-cell` to no tag (fully visible); cell 6 dev-facing code comment (repo path, "single source of truth") rewritten |
| `book/chapters/chapter_02/exercise_02.ipynb` | "What this notebook covers" reordered (identifying sentence first, context condensed); `## 1. The modelling table` → `## 1. Our data table` (heading + body prose); cell 4 tag `hide-cell` → `hide-input`; loading print string `"modelling table: …"` → `"data table: …"`; cell 23 "predeclared candidate" → "candidate"; cell 24 code comment "predeclared" → "chosen in advance"; cell 26 removed "documented in the audit behind this notebook, not shown here" |
| `book/chapters/chapter_03/exercise_03.ipynb` | "What this notebook covers" list item 2 reworded (dropped "predeclared"), duplicate trailing paragraph removed; `## 1. The modelling table` → `## 1. Our data table`; cell 4 tag `hide-cell` → `hide-input`; loading print string renamed; cell 6 "canonical example" → "worked example"; `### A predeclared k` → `### Choosing k for this example` (heading + body reworded) |
| `book/chapters/chapter_04/exercise_04.ipynb` | "What this notebook covers" list converted from 5 dash bullets to a numbered 1–6 list matching all sections (added missing Section 5 item); cell 4 tag added (`hide-input`, was untagged); loading print string renamed; cell 10 "predeclared `C = 1.0`" and "the project's standard deterministic seed" reworded; `### A predeclared C` → `### Choosing C for this example`; cells 15/17 code comments reworded; cell 28 "implementation detail, not the lesson here" removed |
| `book/downloads/chapter_01/exercise_01_portable.ipynb` | Regenerated via `scripts/build_portable_notebook.py --write` from the edited canonical notebook |
| `book/downloads/chapter_02/exercise_02_portable.ipynb` | Regenerated |
| `book/downloads/chapter_03/exercise_03_portable.ipynb` | Regenerated |
| `book/downloads/chapter_04/exercise_04_portable.ipynb` | Regenerated |
| `book/_static/widgets/configs/knn_explore.json` | `curseOfDimensionalityNote`: "canonical recipe" → "own recipe"; removed "The Exercise 3 audit (see the notebook) found…" internal reference |
| `book/_static/widgets/configs/classification_imbalance.json` | `imbalanceNote`: removed "…that is an implementation detail, not the lesson here." |
| `interactive/src/components/knn-explore.ts` | Rendered `cohortLine` text: "Exercise 2's canonical recipe." → "Exercise 2's own recipe." |
| `scripts/smoke_portable_notebook.py` | Fixed two pre-existing stale expected-output string sets (chapter_03, chapter_04) left over from before WP19's removal of early cross-validation/parameter selection; docstring updated to match |
| `tests/test_exercise_02_notebook.py` | `test_five_numbered_sections_present_in_order`: heading string updated to `"## 1. Our data table"` |
| `tests/test_exercise_03_notebook.py` | `test_six_numbered_sections_present_in_order`: heading string updated to `"## 1. Our data table"` |
| `tests/test_notebook_corrections.py` | `test_cell_and_visibility_counts`: updated expected tag-visibility counts for Exercise 1 (`hide-cell` 2→0, `visible` 9→11) to reflect cells 4/6 becoming visible |

No file was renamed or deleted in this WP.

## Files explicitly not touched (in scope but unmodified after review)

- All nine interactive activity configs other than `knn_explore.json` and
  `classification_imbalance.json` (`table_inspection.json`, `eda_histogram.json`,
  `eda_retention.json`, `eda_correlation.json`, `regression_compare.json`, `knn_abc.json`,
  `classification_threshold.json`) — reviewed in full, no internal/dev-facing language or
  unexplained jargon found.
- `course_overview/Machine_Learning_for_Neuroscience_Notebook_Overview.docx` and its generator —
  explicitly out of scope per the WP.
- `WPs/reports/WP16_ARCHITECT_REPORT.md` — whitelisted pre-existing untracked file, untouched.

---

## Correction pass (2026-09-16)

The claim above ("all nine configs… reviewed in full, no… unexplained jargon found") did not
hold up: `knn_abc.json`, `knn_explore.json`, and `regression_compare.json` each still carried a
genuine "honest"/"invalid" student-facing string, found on the exhaustive re-read this
correction pass performed. See `WPs/reports/WP20_REPORT.md` §13 for the full narrative,
per-notebook wording table, and test/build results.

### Commit

`ff24635238ecf526957ca94ebe6b646c9822afc0` — "WP20 correction: exhaustive student-facing
wording audit for Exercises 1-4", committed directly to local `main` (starting `HEAD`
`68aef75ec46190cd6e76a119e67a76392dd6b25c`; no branch/merge, per the correction-pass
instructions; no checkpoint commit needed since the working tree had no uncommitted changes at
the start).

### Files created

- `tests/test_notebook_opening_structure.py`

### Files modified

| File | Change |
|---|---|
| `book/chapters/chapter_01/exercise_01.ipynb` | Cell 39 heading `### Common approaches to missing data` → `### Ways to handle missing data`; cell 52 heading `### Common approach:` → `### Our approach in this exercise`. Re-executed in place (no output text changed, but kept in sync with the other three). |
| `book/chapters/chapter_02/exercise_02.ipynb` | Opening list items 2–3 reworded (drop "honest"/"invalid"); `## 2. One honest linear-regression workflow` → `## 2. Building one linear-regression workflow`; five more "honest"/"invalid" phrases reworded in body prose, a table cell, and the summary (see WP20_REPORT.md §13 for each). Re-executed in place — the stored output for cell 4 was stale ("modelling table:" instead of "data table:") from before the original pass's print-string rename; now refreshed. |
| `book/chapters/chapter_03/exercise_03.ipynb` | Opening list items 3 and 5 reworded; `## 3. Honest evaluation versus invalid alternatives` → `## 3. Correct and misleading ways to evaluate a model`; iframe title renamed; `## 5. From k = 1 to every participant: an empirical curve` → `## 5. How performance changes across every k`, with `N_fit`/`N_val` now defined in plain language before use; printed summary line reworded from bare symbols to plain language; four more "honest"/"empirical curve" phrases reworded. Re-executed in place — cell 4's stored output was stale ("modelling table:") and cell 22's print text changed. |
| `book/chapters/chapter_04/exercise_04.ipynb` | Opening framing sentence, list items 3 and 6 (item 6 is the specific required stratification-framing fix), and the Prerequisites line reworded; Section 1 body "modelling table" → "data table" (a leftover the original pass missed); `## 3. One honest logistic-regression model` → `## 3. One logistic-regression model`; a code comment and two summary bullets reworded. Re-executed in place (no output *values* changed, only comment/prose text, but kept in sync). |
| `book/downloads/chapter_01/exercise_01_portable.ipynb` … `chapter_04/exercise_04_portable.ipynb` | Regenerated via `scripts/build_portable_notebook.py --write` from the re-executed canonical notebooks. |
| `book/_static/widgets/configs/knn_abc.json` | `title`: "Honest vs invalid evaluation, interactively" → "Correct vs misleading evaluation, interactively". |
| `book/_static/widgets/configs/knn_explore.json` | One reflection prompt: "an honest final estimate" → "a trustworthy final estimate". |
| `book/_static/widgets/configs/regression_compare.json` | `selectionBiasNote`: "An honest final estimate…" → "A trustworthy final estimate…". |
| `interactive/src/components/classification-threshold.ts` | Rendered cohort-line text: dropped "honest" before "held-out predicted probabilities". |
| `interactive/e2e-book/chapter03.spec.ts` | `ABC_IFRAME_SELECTOR` updated to the renamed iframe title. |
| `scripts/build_portable_notebook.py` | Iframe-title dictionary keys (3 occurrences) and two student-facing portable-notebook prose strings ("Try the honest-vs-invalid comparison…", the matching code comment) updated to match the Exercise 3 rename. |
| `scripts/smoke_portable_notebook.py` | Two expected-output strings updated: chapter_03's `N_fit = 564   N_val = 189` → `fitting participants (N_fit) = 564   validation participants (N_val) = 189`. |
| `tests/test_exercise_02_notebook.py` | Heading string updated to `"## 2. Building one linear-regression workflow"`. |
| `tests/test_exercise_03_notebook.py` | Two heading strings updated; iframe-title assertion updated; `N_fit`/`N_val` output-string assertion updated. |
| `tests/test_exercise_04_notebook.py` | Heading string updated to `"## 3. One logistic-regression model"`. |

No file was renamed or deleted in this correction pass.

### Files explicitly reviewed and left unchanged

- `A. Valid` / `B. Resubstitution` / `C. Invalid (leakage)` panel labels in the Exercise 2/3
  comparison tables and in `interactive/src/components/knn-abc.ts` — each carries its own
  plain-language subtitle; judged not to be the vague "invalid alternatives" pairing the
  correction targeted (see WP20_REPORT.md §13 for the reasoning).
- `book/_static/widgets/configs/classification_threshold.json`'s `description` field (contains
  "honest" but is never rendered by any component — confirmed by `grep`) and all `Invalid <x>
  data: …` Zod validation-error strings across `interactive/src/*.ts` — these are internal
  build/config validation messages a student never sees under normal use, not the material this
  correction pass's audit scope covers.
- `interactive/tests/config.test.ts`'s `validKnnAbc` fixture (`title: "Honest vs invalid
  evaluation, interactively"`) — an arbitrary schema-validation test fixture, not asserted
  against real production content.
