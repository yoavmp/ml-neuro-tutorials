# WP01 implementation report

## Outcome
Status: SUCCESS

The audit reproduced the reported failure with a precise root cause, found a second, independent root cause for why the interactive controls cannot work at all on a static GitHub Pages site, confirmed the data-loading and static-asset paths WP02 will depend on, corrected stale `.gitignore`/index state, and evaluated the proposed TypeScript/Vite/Plotly/iframe architecture against the real repository. No teaching prose, analysis results, or notebook cell IDs/metadata were altered; no replacement architecture was implemented.

## Git safety checkpoint
- Branch: `feature/reusable-interactive-widgets` (created from `main` at `24398db`)
- Starting HEAD: `24398db68db6228fd5227f4ba22d4fa42625ae45` ("Stop tracking generated Jupyter Book files")
- Checkpoint commit: `414a38af9850231f92b5b8514a8d33b61ef0deb0` ("checkpoint: before WP01")
- Checkpoint tag: `wp01-start` (annotated, points at `414a38a`)
- Retraction guidance: identify the checkpoint only; do not execute a reset/revert.

## Work completed

1. **Read the governing documents** — `CLAUDE_INTERACTIVE_WIDGETS.md`, `WPs/README.md`, `WPs/WP01_AUDIT_AND_BASELINE.md` — in full before acting.
2. **Created `feature/reusable-interactive-widgets`** from `main`, then the mandatory checkpoint commit + annotated tag, staging only legitimate pre-existing work (prior uncommitted `ipywidgets`/JupyterLite/Voici/Plotly experiments, the new `WPs/` and `CLAUDE_INTERACTIVE_WIDGETS.md` assignment files, and the standalone `exercise_01_widgets.ipynb` draft). Excluded from the checkpoint: `book/.jupyterlite.doit.db` (a `doit` build-cache database) and a newly-created stale `.ipynb_checkpoints` autosave file — both are non-authored, reproducible cache artifacts per Rule 2.
3. **Inspected the repository tree**, `.gitignore`, `requirements.txt`, `book/_config.yml`, `book/_toc.yml`, `.github/workflows/deploy.yml`, and `book/chapters/chapter_01/exercise_01.ipynb` cell-by-cell via `nbformat`/JSON (not text search-and-replace).
4. **Located every relevant mechanism**: JupyterLite/Voici config in `book/_config.yml`, `ipywidgets` usage in two notebooks, a client-side Plotly.js figure using CDN delivery, the "Open in Colab" launch button, and no iframe embedding of any kind currently wired into the page.
5. **Determined the canonical data path**: ABIDE-II phenotypic CSV fetched at runtime from a third-party GitHub mirror; curated-column list at `book/config/eda_phenotype_columns.json`, itself re-fetched over the network from this repo's own `raw.githubusercontent.com` URL by both widget notebooks.
6. **Recorded environment versions** (see table below).
7. **Ran the real build twice** (`jupyter-book build book`) and reproduced the reported failure deterministically both times.
8. **Served the build over HTTP** (`python3 -m http.server`, never `file://`) and confirmed page/asset/JupyterLite-app reachability. Browser console/network inspection was **NOT TESTED** — no Chromium/Playwright binary is available in this environment (see Problems section).
9. **Inspected `book/_build` diagnostically only** — read the execution error report and jupyter-cache state, made no edits, and it is not committed (already ignored, verified untracked after every build).
10. **Corrected `.gitignore`** and untracked 6 already-tracked generated files (5 `.DS_Store`, 1 stale notebook checkpoint) without deleting the local copies.
11. **Confirmed `book/_static` copy-through** empirically: created a throwaway probe file under `book/_static/`, rebuilt, confirmed it appeared under `_build/html/_static/`, then deleted the probe (not committed). Confirmed the exact relative depth (`../../_static/...`) used from a Chapter 1 page.
12. **Evaluated the proposed static TypeScript/Vite architecture** against the real repository (see below) — not implemented.
13. Committed audit/ignore changes as `WP01: audit interactive notebook baseline` (`c3c899c`).
14. Wrote this report.
15. Committing this report next as `WP01 report: document results`, then stopping.

## Files changed

**Checkpoint commit `414a38a`** (captured pre-existing uncommitted work, not authored by this WP):
- `.gitignore` — pre-existing staged addition of `.DS_Store`
- `book/_config.yml` — pre-existing addition of `jupyterlite_sphinx` config
- `book/chapters/chapter_01/exercise_01.ipynb` — pre-existing addition of `ipywidgets`/Plotly cells
- `book/chapters/chapter_01/.ipynb_checkpoints/exercise_01-checkpoint.ipynb` — stale autosave mirror of the above (later untracked)
- `requirements.txt` — pre-existing addition of `ipywidgets`, `jupyterlite-sphinx`, `jupyterlite-pyodide-kernel`, `voici`, `plotly`
- `CLAUDE_INTERACTIVE_WIDGETS.md`, `WPs/README.md`, `WPs/WP01_AUDIT_AND_BASELINE.md` — new assignment/process files
- `book/chapters/chapter_01/exercise_01_widgets.ipynb` — new standalone widget draft notebook

**Audit commit `c3c899c`** (this WP's own changes):
- `.gitignore` — added `.ipynb_checkpoints/`, `.jupyterlite.doit.db`, `.jupyter_cache/`, `node_modules/`, anticipated Vite output paths, and Playwright artifact directories
- `.DS_Store`, `.github/.DS_Store`, `.github/workflows/.DS_Store`, `book/chapters/.DS_Store`, `book/chapters/chapter_01/.DS_Store` — untracked (removed from index only; files remain on disk)
- `book/chapters/chapter_01/.ipynb_checkpoints/exercise_01-checkpoint.ipynb` — untracked (removed from index only; file remains on disk, byte-identical to `exercise_01.ipynb`)

**Not committed (intentionally excluded, still present on disk):**
- `book/.jupyterlite.doit.db` — `doit` build-cache database, untracked, newly ignored
- `book/chapters/chapter_01/.ipynb_checkpoints/exercise_01_widgets-checkpoint.ipynb` — Jupyter autosave cache, untracked, newly ignored
- `book/_build/` — full diagnostic build output (regenerated twice during this audit), already ignored, verified absent from `git status` after every build

## Tests and verification

| Command/test | Result | Evidence or relevant output |
|---|---|---|
| `sw_vers` / `uname -a` | OK | macOS 15.7.9 (Darwin 24.6.0), x86_64 |
| `python3 --version` / `.venv/bin/python --version` | OK | Python 3.12.7 (both system and venv) |
| `node --version` / `npm --version` | OK | Node v24.4.1, npm 11.4.2 |
| `.venv/bin/jupyter-book --version` | OK | Jupyter Book 1.0.4.post1, MyST-NB 1.4.0, Sphinx Book Theme 1.3.0 |
| `.venv/bin/pip list` (relevant packages) | OK | `ipywidgets==8.1.9`, `jupyterlite-sphinx==0.23.0`, `jupyterlite-pyodide-kernel==0.8.5`, `voici==0.2.0`, `voila==0.5.13`, `plotly==7.0.0`, `widgetsnbextension==4.0.16` — matches `requirements.txt` pins |
| `rm -rf book/_build && .venv/bin/jupyter-book build book` (run twice) | Exit 0, but with a `CellExecutionError` warning | Build reports "build succeeded, 13 warnings" — the notebook execution failure is **non-fatal to the overall build**, so CI would publish the broken page without failing |
| Inspect `book/_build/html/reports/chapters/chapter_01/exercise_01.err.log` | Reproduced | `SyntaxError: invalid syntax` at a `:::{note}` MyST admonition placed inside a **code** cell (see Root cause 1 below) |
| `grep` for `application/vnd.jupyter.widget-view+json` in built `exercise_01.html` | 0 matches | The `ipywidgets` `interactive_output` cell never executes (see Root cause 1) and produces no widget view in the static page |
| `grep` for the same marker in built `exercise_01_widgets.html` | 2 matches | This standalone notebook executes cleanly and does embed widget state — but is orphaned from `_toc.yml` ("document isn't included in any toctree") and its interactivity still requires a live kernel, which the static site does not provide |
| Inspect stored `outputs` of the Plotly cell (index 58) in the source `.ipynb` | 1 pre-existing `display_data` output (`execution_count: 44`) | The Plotly chart visible in the current build is a **stale, previously-captured snapshot**, not a fresh, verified execution — the notebook aborts (see Root cause 1) before this cell would re-run |
| `curl` to `raw.githubusercontent.com/.../abide2_phenotypic.csv` | HTTP 200 | Confirms the build has a live network dependency, currently reachable from this environment |
| `book/_build/html` served via `python3 -m http.server 8743` | 200 / 200 / 200 | Chapter page, a `_static` asset, and the JupyterLite `lite/index.html` app all resolve correctly over real HTTP |
| Browser console/network inspection of the served page | **NOT TESTED** | No Chromium or Playwright binary is installed in this environment (`which chromium/google-chrome` → not found; `import playwright` → `ModuleNotFoundError`) |
| Probe file under `book/_static/widgets_probe/probe.txt`, rebuild, check `_build/html/_static/widgets_probe/probe.txt` | Copied through correctly, then deleted (not committed) | Confirms Sphinx's standard `_static` copy-through works for this project with no extra configuration |
| `grep` relative `_static` paths used from `chapters/chapter_01/exercise_01.html` | `../../_static/...` throughout | Confirms the exact relative iframe depth WP02's embed will need from a Chapter 1 page |
| Search `book/_build/html/lite` for project notebooks | Only default `jupyter-lite.ipynb` placeholders per app; no course content | `book/_contents` (the directory passed as `--contents`) is empty, and `book/_config.yml`'s `jupyterlite_contents: ["chapters/chapter_01/eda_widgets.ipynb"]` references a file that **does not exist** anywhere in the repo (only `exercise_01_widgets.ipynb` exists) |

## Acceptance criteria

| Criterion | PASS/FAIL/NOT TESTED | Evidence |
|---|---|---|
| Mandatory checkpoint commit and annotated tag exist and are recorded | PASS | `414a38a` / `wp01-start` |
| Baseline build command and current interactive behavior are documented | PASS | `jupyter-book build book`; two independent root causes documented below |
| No user-authored source is unintentionally changed | PASS | Only `.gitignore` and index state (untracking) were changed by this WP; notebook prose/cells untouched |
| Generated files are correctly ignored and not tracked | PASS | 6 files untracked from index; `.gitignore` extended; verified clean `git status` after 3 rebuilds |
| Planned source/build/static paths are confirmed against the repository | PASS | `book/_static` copy-through and `../../_static/...` relative depth empirically confirmed |
| `WPs/reports/WP01_REPORT.md` explicitly reports outcome, tests, deviations, and risks | PASS | This document |
| Audit and report are committed separately | PASS | `c3c899c` (audit) will precede a separate report commit |
| Working tree is clean | PASS (verified before writing this report) | `git status --short` empty except this untracked report file, prior to its own commit |
| No WP02 file or replacement implementation has been created | PASS | No `interactive/`, no Vite scaffold, no new widget config/data files created |

## Root cause findings (primary evidence for WP02)

**Root cause 1 — build-breaking bug, CONFIRMED by reproduction:** `exercise_01.ipynb` cells at index 35 and 57 contain the MyST admonition markup `:::{note} ... :::` typed directly into **code** cells instead of markdown cells. When Jupyter Book executes the notebook (`execute_notebooks: cache`), the first such cell (index 35) raises `SyntaxError: invalid syntax` and aborts all further execution of that notebook — including both interactive-widget sections that follow (the `ipywidgets` `SelectMultiple`/`interactive_output` cells at 36–37, and the Plotly histogram at 58). Jupyter Book's overall build still exits 0 ("build succeeded, 13 warnings"), so this failure is silent in CI and the broken page would be published as-is. This is a straightforward, unrelated-to-architecture bug that should be fixed (moved to markdown cells) independently of any widget-replacement work.

**Root cause 2 — architectural, explains the reported "control updates, figure does not":** The `ipywidgets`-based interactivity (`widgets.interactive_output`, `.observe()`) requires a live Python kernel to run the Python callback that redraws the Matplotlib figure. A statically-exported GitHub Pages site has no kernel. Native `ipywidgets` DOM controls (a dropdown's own visible selection, a slider's displayed value) can still appear to respond because they are just HTML form elements, but the callback that recomputes and redraws the plot can never reach a kernel over the Jupyter comm protocol, so the figure never updates. This matches the reported symptom precisely and independently motivates moving to browser-native JS (as the Plotly `updatemenus`/`sliders` cell already does, client-side, via `restyle`/`update` methods with no kernel required) rather than `ipywidgets` callbacks. Confirmed as an architectural fact from how `ipywidgets`/Jupyter comms work and from the evidence that the `interactive_output` cell has never produced a rendered widget-state output; the live-kernel round-trip itself was **NOT TESTED** end-to-end in a browser (no browser automation available).

**Root cause 3 — dead JupyterLite configuration:** `book/_config.yml`'s `jupyterlite_contents: ["chapters/chapter_01/eda_widgets.ipynb"]` points at a file that does not exist (only `exercise_01_widgets.ipynb` exists, under a different name). `book/_contents/` — the directory jupyterlite-sphinx is told to pull content from — is empty. As a result the built `lite/` JupyterLite app ships zero project notebooks; it is a fully functional but content-less Jupyter environment. This is unrelated to Root causes 1–2 but confirms JupyterLite is not currently a working delivery path for this activity either way.

**Data/network dependency:** Both the main notebook and the standalone widgets draft fetch the ABIDE-II phenotypic CSV and the curated-column JSON over the network at execution time (`raw.githubusercontent.com`), including the widget notebooks re-fetching the column list from this repository's own `main` branch. This confirms Rule 8/architecture requirement: any browser-native replacement must ship its own small exported JSON data file (per `scripts/export_widget_data.py` in the intended layout) rather than depend on live CSV fetches or pyodide-kernel network access at viewer runtime.

## Architecture evaluation (confirm/amend, not implement)

The proposed TypeScript/Vite/local-Plotly.js/JSON/iframe architecture in `CLAUDE_INTERACTIVE_WIDGETS.md` is **confirmed as viable and well-matched** to this repository, with the following concrete findings to carry into WP02:

- `book/_static/` copy-through works with zero extra Sphinx configuration — confirmed empirically. `book/_static/widgets/app/` (Vite output) and `book/_static/widgets/{configs,data}/` will be copied automatically.
- From any Chapter 1 page, static assets are reached via `../../_static/...` — confirmed from the live build. An iframe embed should use this same two-level-up relative path so it survives the GitHub Pages repository subpath (`https://yoavmp.github.io/ml-neuro-tutorials/...`), matching Rule/requirement "assets must work beneath the GitHub Pages repository subpath."
- The existing Plotly cell (index 58) already demonstrates the *right* interaction model (client-side `updatemenus`/`sliders` driving `restyle`/`update`, no kernel) but currently loads Plotly.js from `cdn.plot.ly` — this must become a locally bundled dependency in the Vite app per Rule 8 ("without a CDN").
- The curated-column JSON at `book/config/eda_phenotype_columns.json` is a suitable seed for a `scripts/export_widget_data.py`-produced static data file; it should be re-exported as a small, pre-filtered dataset (only the fields actually plotted) rather than reused as-is, and missing values must be exported as JSON `null` per Rule 11.
- `book/chapters/chapter_01/exercise_01_widgets.ipynb` and the `ipywidgets` cells inside `exercise_01.ipynb` are exploratory dead ends for the GitHub Pages target (Root cause 2) and are candidates for removal/replacement in WP02, but no such removal was performed in this WP.
- No deviation from the proposed layout is required based on this audit; `book/_toc.yml` currently only lists `chapters/chapter_01/exercise_01`, so any new iframe-hosting notebook or page must be added there explicitly, and `exercise_01_widgets.ipynb` should either be wired into the toctree or removed to resolve the current "not included in any toctree" build warning.

## Deviations from instructions

- Ran `jupyter-book build book` twice (once via a `tee`d command whose exit-code capture failed under this shell, once cleanly) to get a reliable exit code. Both runs reproduced identical results; no repository files were affected by the retry.
- Created a temporary probe file under `book/_static/widgets_probe/probe.txt` to empirically verify static-asset copy-through (Task 11). It was deleted immediately after verification and was never committed or left in the working tree.
- Browser console/network inspection (Task 8, second half) could not be performed as no Chromium or Playwright binary is available in this environment; this is reported as NOT TESTED per instructions rather than asserted as untested-but-assumed-fine.

## Problems and unresolved risks

- **No browser automation available**: console/network-tab evidence for the reported bug is indirect (build logs, HTML output inspection, HTTP status checks) rather than a direct browser trace. If WP02 needs true browser-console verification, a Chromium/Playwright install will be required first.
- **CI does not fail on this bug**: `jupyter-book build book` exits 0 despite the `CellExecutionError`, meaning the current GitHub Actions workflow (`.github/workflows/deploy.yml`) will happily publish the broken chapter page. This is a latent risk independent of the widget-replacement work.
- **Stale committed output**: the Plotly histogram currently visible on the deployed site is a previously-captured static snapshot (`execution_count: 44`) rather than a result of a passing, current execution — the underlying code path has not actually been exercised successfully in this repository state.
- **Self-referential network fetch**: the widget notebooks fetch their own column-config JSON from `raw.githubusercontent.com/yoavmp/ml-neuro-tutorials/main/...` — i.e., from this very repository's default branch. This is fragile (breaks for anyone working on a branch/fork, and adds a real-world network dependency to something that should be a local, static import) and should not carry over into the replacement architecture.
- **`.ipynb_checkpoints` autosave drift**: a byte-identical stale checkpoint file for `exercise_01.ipynb` was already tracked in git before this WP; the equivalent checkpoint for the new widget notebook was not (now both are ignored going forward, so this should not recur).

## Git commits created

- Checkpoint commit: `414a38af9850231f92b5b8514a8d33b61ef0deb0` ("checkpoint: before WP01")
- Checkpoint tag: `wp01-start` (annotated, points at `414a38a`)
- Implementation/audit commit: `c3c899c3f361d8e6017cc2be6dd9a0da28f410ea` ("WP01: audit interactive notebook baseline")
- The report commit is printed in the terminal summary because the report cannot contain its own future hash.

## Recommended scope for the next WP

- Fix Root cause 1 first and independently (convert the two `:::{note}` code cells to markdown cells) — this is a trivial, high-value fix that unblocks any further diagnosis of the widget cells, regardless of which replacement architecture is chosen.
- Scaffold the `interactive/` Vite/TypeScript project per the intended layout, with Plotly.js as a local dependency (not CDN), and a pure/testable calculation layer separate from the Plotly rendering calls.
- Write `scripts/export_widget_data.py` to export a small, curated static JSON dataset (subset of `book/config/eda_phenotype_columns.json`'s fields, missing values as `null`, no participant identifiers beyond what's already non-identifying) into `book/_static/widgets/data/`.
- Wire one iframe embed into `exercise_01.ipynb` (or a dedicated replacement notebook added to `book/_toc.yml`) using the confirmed `../../_static/widgets/app/...` relative path, targeting the retention/missingness or histogram activity as the first end-to-end proof of concept.
- Decide and record whether `exercise_01_widgets.ipynb` and the `ipywidgets` cells in `exercise_01.ipynb` are removed or left as a non-graded aside once the browser-native replacement lands, since they cannot function as intended on the static site (Root cause 2).
- Add a CI check that fails the build on notebook execution errors (or at minimum surfaces them more visibly) so a regression like Root cause 1 cannot silently ship again — out of scope for the widget work itself but a low-cost, high-value adjacent fix.

## Instructions for reviewer
Paste this entire report into the ChatGPT conversation that produced WP01.
