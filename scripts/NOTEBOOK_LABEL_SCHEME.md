# Notebook cell labels

Every student-facing exercise notebook generator (`scripts/generate_exercise_{01..12}_notebook.py`,
including `generate_exercise_10_deep_learning_notebook.py`) prepends one of
seven one-line Markdown labels immediately above each code cell that fits
one of the categories below. A label is plain Markdown text — a colored
square/diamond emoji plus bold text — never CSS, HTML, or JupyterLite-only
cell styling, so it renders identically in JupyterLite, a downloaded local
notebook, and Colab.

| Label | Format | Use for |
|---|---|---|
| 🟦 RUN FIRST | `🟦 **RUN FIRST** · [short description]` | Setup, data loading, or supplied code whose variables a later cell genuinely reads (confirm by grep, not assumption) |
| 🟧 YOUR CODE | `🟧 **YOUR CODE** · [short description]` | Every `blank(...)` student activity |
| 🟩 CHECK | `🟩 **CHECK** · Run after completing your code` | Every self-check cell validating a blank, with pass/fail framing |
| 🟪 EXPLORE | `🟪 **EXPLORE** · [short description]` | Every interactive widget cell (`.observe(...)` + live redraw) |
| 🟨 QUESTION | `🟨 **QUESTION** · Choose an answer and check it` | Every `show_question(...)` cell |
| 🟫 ILLUSTRATE | `🟫 **ILLUSTRATE** · [short description]` | A supplied, non-interactive, non-assessment code cell producing a matplotlib/graphical figure the student runs and looks at — figures only, never a table or printed text |
| 🔷 INSPECT | `🔷 **INSPECT** · [short description]` | Supplied code producing a table, printed result, or text output to examine — must not imply the cell sets up later work (that's RUN FIRST) or checks correctness (that's CHECK) |

CHECK and QUESTION always use the exact fixed text above (no bracketed
description); the other five take a short, cell-specific description.

## Placement rule

The label is the first line of the Markdown cell immediately above the
target code cell, followed by one blank line, then that cell's existing
content unchanged. If a Markdown cell doesn't already sit immediately
above the target (two code cells are adjacent, or the nearest Markdown
cell is shared by multiple following cells, e.g. a section summary before
several questions), insert a new one-line label-only Markdown cell instead
of repurposing unrelated prose — never prepend a label onto content that
isn't specifically about the cell it precedes.

A code cell gets **exactly one** label, or none if it fits no category
(e.g. a bare `data.head()` with no later use *and* no figure predates
INSPECT's introduction in a few spots that were later relabeled; a plain
section header; a free-text reflection blockquote).

## Verification

Each generator's own `--write`/`--check` modes keep the generated
`book/lite/files/`, `book/downloads/chapter_*/`, and
`scripts/reference_notebooks/` copies synchronized with this source. There
is no separate pytest suite asserting label placement; verification is
done ad hoc per change with a small script that walks each generated
notebook's cells and confirms every labeled code cell's immediate
predecessor is the matching label Markdown cell, with no double-stacked or
orphaned labels, and that every `blank()` activity cell carries exactly
YOUR CODE.
