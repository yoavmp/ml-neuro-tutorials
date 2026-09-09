# WP01 — Audit and establish the baseline

## Objective

Safely capture the current project state, inspect the real implementation, reproduce the current interactive-figure problem, and provide evidence needed for ChatGPT to design WP02. Do not implement the replacement architecture in this WP.

## Tasks

1. Read `CLAUDE_INTERACTIVE_WIDGETS.md` and `WPs/README.md` completely.
2. Create the feature branch if needed, then create the mandatory pre-WP checkpoint commit and annotated tag before changing project files.
3. Inspect the repository tree, `.gitignore`, dependencies, Jupyter Book configuration, table of contents, deployment workflow, and `book/chapters/chapter_01/exercise_01.ipynb`.
4. Locate all JupyterLite, Voici, `ipywidgets`, Matplotlib-widget, Plotly/CDN, iframe, and custom JavaScript code relevant to the failed activity.
5. Determine the canonical ABIDE phenotypic input, curated-column configuration, and exact data-loading path used by the notebook.
6. Record OS, Python, Jupyter Book, Node, and npm versions. Use the existing virtual environment if valid; do not commit it.
7. Run the current relevant notebook/build commands. Attempt to reproduce the reported behavior: control/status text changes but the figure does not, and in one local attempt no figure appeared. Record the actual current behavior if it differs.
8. Serve generated HTML over HTTP, never `file://`. Inspect browser console and network errors if browser automation or developer tools are available.
9. Inspect `book/_build` only diagnostically. Never edit or commit it.
10. Add or correct ignore rules for `_build`, `.DS_Store`, `node_modules`, future Vite output, Playwright artifacts, caches, and other generated files. If generated files are already tracked, remove them from the Git index without deleting local copies and report exactly what was untracked.
11. Confirm whether `book/_static` is copied to the final HTML and determine the exact iframe-relative path from the built Chapter 1 page.
12. Evaluate the proposed static TypeScript/Vite/local-Plotly/JSON/iframe architecture against the repository. Report any necessary deviations, but do not implement it.
13. Commit audit/ignore/documentation changes with `WP01: audit interactive notebook baseline`.
14. Create `WPs/reports/WP01_REPORT.md` using the required format. Include enough evidence for another engineer to design WP02 without repeating the audit.
15. Commit the report with `WP01 report: document results`, print the required summary, and stop.

## Required evidence in the report

- Relevant repository tree and exact file paths.
- Current widget implementation and why the plot is believed to fail.
- Exact build/deployment sequence.
- Data source, selected-column configuration, and whether the build depends on network access.
- Whether `_static` assets and nested GitHub Pages paths work as expected.
- Commands executed and concise outputs/exit statuses.
- Browser console/network findings, or an explicit `NOT TESTED` explanation.
- Recommended technical scope and prerequisites for WP02.
- All deviations, warnings, and uncertainty.

## Acceptance criteria

- Mandatory checkpoint commit and annotated tag exist and are recorded.
- Baseline build command and current interactive behavior are documented.
- No user-authored source is unintentionally changed.
- Generated files are correctly ignored and not tracked.
- Planned source/build/static paths are confirmed against the repository.
- `WPs/reports/WP01_REPORT.md` explicitly reports outcome, tests, deviations, and risks.
- Audit and report are committed separately.
- Working tree is clean.
- No WP02 file or replacement implementation has been created.

Stop after WP01 even if every criterion passes.

