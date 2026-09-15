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
