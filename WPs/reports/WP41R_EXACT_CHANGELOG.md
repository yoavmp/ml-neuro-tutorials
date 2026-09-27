# WP41R exact changelog

Branch: `feature/wp41-jupyterlite-course-platform`.
Starting SHA: `b0d75dfe4a01cb9c3eaf8bcf8f608d119363ebc2`.
Checkpoint branch (pre-correction state): `checkpoint/wp41r-pre-correction`
(same SHA).

## Commit 1 — `e97501a` "WP41R: add local-review blockers spec and chat handoff notes"

New files (untracked at WP start, committed as-is):
- `WPs/WP41R_LOCAL_REVIEW_BLOCKERS.md` — this WP's instruction file.
- `WPs/ML_NEURO_TUTORIALS_CHAT_HANDOFF_2026-09-27.md` — cross-session
  project handoff note.

## Commit 2 — `01a105f` "WP41R: fix Exercise 2 setup/NameError, reference-image size, and entry points"

### `scripts/generate_exercise_02_notebook.py`

- `TEMPLATE_VERSION`: `1` -> `2`.
- Added `PORTABLE_PATH`-adjacent constant `LITE_FILES_PORTABLE_COPY_PATH =
  REPO_ROOT / "book" / "lite" / "files" / "exercise_02_portable.ipynb"`,
  with a comment explaining why a second, byte-identical copy of the
  portable notebook is written here (same-origin publication via `jupyter
  lite build`, since `book/downloads/` is excluded from the Jupyter Book
  build).
- `md(source, cell_id)` -> `md(source, cell_id, attachments=None)`: sets
  `cell["attachments"]` when a non-empty dict is passed.
- Added `_run_first_notice()`: builds a new, non-collapsed Markdown cell
  (`id="wp41-000a-run-first"`) instructing the student to run the setup
  cell first.
- `_build_cells`: `cells = [_setup_cell(mode)]` -> `cells =
  [_run_first_notice(), _setup_cell(mode)]` (notebook now has one
  additional leading cell; every existing cell shifts index by one).
- `wp41-103-load` cell source: wrapped `data =
  load_abide_age_brain_table()` in `try/except NameError as exc: raise
  RuntimeError(<actionable message>) from exc`.
- Renamed/replaced `_reference_image_markdown()`'s implementation: added
  module-level `REFERENCE_IMAGE_FILENAME = "exercise_02_observed_vs_predicted.png"`
  and `_reference_image_attachments()` (returns
  `{REFERENCE_IMAGE_FILENAME: {"image/png": <base64>}}`);
  `_reference_image_markdown()` now returns
  `f"![Approved observed-vs-predicted result](attachment:{REFERENCE_IMAGE_FILENAME})"`
  instead of embedding the base64 payload inline.
- `_section_3()`'s call site for the reference-image cell: now passes
  `attachments=_reference_image_attachments()` to `md(...)`.
- `main()`: the student-mode write/check loop now iterates `(LITE_TEMPLATE_PATH,
  PORTABLE_PATH, LITE_FILES_PORTABLE_COPY_PATH)` instead of
  `(LITE_TEMPLATE_PATH, PORTABLE_PATH)`.
- Module docstring's "Outputs:" list updated to mention the new served
  copy.

### `scripts/generate_exercise_02_transition_page.py`

- `DOWNLOAD_URL`: `"../../downloads/chapter_02/exercise_02_portable.ipynb"`
  -> `"../../lite/files/exercise_02_portable.ipynb"`, with a comment
  explaining `book/downloads/` is not published.
- `build_notebook()`'s body Markdown:
  - `**[Open Exercise 2]({LITE_URL})**` -> `**<a
    href="{LITE_URL}">Open Exercise 2</a>**`.
  - Removed the `[Google Colab](https://colab.research.google.com/github/.../main/...)`
    deep link and the separate `[{DOWNLOAD_URL}]({DOWNLOAD_URL})` line;
    replaced with one sentence: "If you would rather work outside the
    browser, <a href="{DOWNLOAD_URL}">download the same notebook</a> and
    open it in a local Jupyter installation, or in [Google
    Colab](https://colab.research.google.com/) using **File > Upload
    notebook**."
- Module docstring: added a paragraph explaining the raw-HTML-link and
  same-origin-download rationale.

### `book/_static/launch-buttons.js`

- Removed the `"chapters/chapter_02/exercise_02.html":
  "book/downloads/chapter_02/exercise_02_portable.ipynb"` entry from
  `PAGE_TO_PORTABLE` (replaced with a one-line comment pointing to the file
  header).
- File header comment: added a paragraph explaining why chapter_02 is
  excluded (unpushed migration; future-private-repo breakage).

### `book/_config.yml`

- Comment-only changes (no keys added or removed): updated the
  `_static/launch-buttons.js` comment ("Both Chapter 1 and Chapter 2 use
  it" -> "Chapters 1 and 3-10 use it; WP41R deliberately excludes Chapter
  2..."), and added a parenthetical to the `exclude_patterns: downloads/*`
  comment noting Chapter 2's portable notebook is served from
  `book/lite/files/` instead.

### Generated files (regenerated via `--write`, not hand-edited)

- `book/lite/files/exercise_02.ipynb` — regenerated from the generator
  changes above (new leading notice cell, guarded load cell, attachment-based
  reference image).
- `book/downloads/chapter_02/exercise_02_portable.ipynb` — same content as
  the lite template (student-mode output is written to both paths
  unchanged from before this WP).
- `book/lite/files/exercise_02_portable.ipynb` — **new file**; same content
  as the two paths above.
- `scripts/reference_notebooks/exercise_02_reference.ipynb` — regenerated
  reference-mode output (same structural changes, solution-side blanks).
- `book/chapters/chapter_02/exercise_02.ipynb` — regenerated from the
  transition-page generator changes above.

### `tests/test_exercise_02_lite_notebook.py`

- `test_title`: index `self.cells[1]` -> `self.cells[2]` (notebook now has
  the new notice cell at index 0, setup cell at index 1, title at index 2).
- `test_setup_cell_is_collapsed_and_first`: index `self.cells[0]` ->
  `self.cells[1]`.
- Added `test_run_first_notice_precedes_the_collapsed_setup_cell`: asserts
  cell 0 is Markdown, not source-hidden, and contains "Run the cell below
  first".
- Added `test_data_load_gives_an_actionable_error_if_setup_was_skipped`:
  asserts the `wp41-103-load` cell source contains `except NameError`,
  `raise RuntimeError`, and `Run this notebook's`.
- Added `test_reference_image_is_an_attachment_not_an_inline_data_uri`:
  asserts no `data:image/png;base64` substring in the reference-image
  cell's source, an `attachment:` reference present, source length under
  200 characters, exactly one attachment entry with an `image/png` payload
  over 1000 characters.

### `tests/test_exercise_02_transition_page.py`

- `test_links_to_the_jupyterlite_notebook`: now asserts the exact raw-HTML
  anchor `'<a href="../../lite/notebooks/index.html?path=exercise_02.ipynb">'`
  is present, not just the URL as a substring anywhere on the page.
- `test_links_to_the_downloadable_copy`: now asserts the exact anchor
  `'<a href="../../lite/files/exercise_02_portable.ipynb">'` is present and
  that `"downloads/chapter_02"` does not appear anywhere on the page.
- Added `test_no_raw_github_or_colab_deep_link`: asserts neither
  `colab.research.google.com/github` nor `raw.githubusercontent.com`
  appears anywhere on the page.

### `interactive/e2e-book/chapter02.spec.ts` (rewritten)

- Replaced `a[href*="..."]` substring locators with exact-href locators
  (`LITE_HREF`, `DOWNLOAD_HREF` constants).
- Added a test that actually clicks "Open Exercise 2" and asserts
  `page.url()` navigates to the JupyterLite notebook URL.
- Added a test that fetches the download href via `page.request.get(...)`
  and asserts HTTP `200`.
- Added a test asserting `[data-testid="colab-launch-button"]` has count
  `0` on this page and that `.bd-article`'s HTML contains neither
  `raw.githubusercontent.com` nor `colab.research.google.com/github`.

### `interactive/e2e-book/launch-buttons.spec.ts`

- Removed the `{ name: "Chapter 2", url: ..., portable: ... }` entry from
  the shared `CHAPTERS` array (Chapter 2 no longer uses the
  admonition-based opening these shared tests assert against).
- Updated the file's top comment to explain the Chapter 2 exclusion.
- Added a new top-level test, "Chapter 2 (migrated to JupyterLite) gets no
  top-bar Colab button", asserting
  `[data-testid="colab-launch-button"]` count `0` on
  `chapters/chapter_02/exercise_02.html`.

### `interactive/e2e-book/exercise-02-lite.spec.ts`

- `scrollToVisible(page, text)` -> `scrollToVisible(page, text, cellSelector
  = ".jp-CodeCell")`: added an optional cell-selector parameter so the
  helper can also locate Markdown cells.
- Console-error allowlist regex: added `|ERR_UNKNOWN_URL_SCHEME` (with a
  comment explaining the one-time, harmless failed fetch of the literal
  string `attachment:<filename>` that every Jupyter frontend implementing
  cell attachments produces before resolving the real image).
- Added test "running the data cell before setup fails with an actionable
  message, not a bare NameError": opens the notebook fresh (no "Run All
  Cells"), scrolls to and runs only the `load_abide_age_brain_table()`
  cell, asserts its output contains `RuntimeError` and `Run this
  notebook's`, and that the traceback's final line contains `RuntimeError:`.
- Added test "the reference image returns to rendered mode without a
  page-length encoded string": runs all cells, scrolls to the reference-image
  Markdown cell, asserts an `<img>` is visible, double-clicks into edit
  mode, asserts the CodeMirror source text is under 200 characters and
  contains `attachment:` but not `base64`, presses Shift+Enter, and
  reasserts the `<img>` is visible again.

## Not changed

- `book/lite/overrides.json` — investigated (ipywidgets preload entry) and
  left unchanged; see the Report's "root-causing note".
- `book/lite/extensions/course-toolbar/` — investigated (Back/Download/Reset
  toolbar) and found unrelated to all three blockers; unchanged.
- `book/lite/jupyter_lite_config.json` — unchanged.
- Any file under `book/chapters/chapter_0{1,3-10}/`,
  `book/downloads/chapter_0{1,3-10}/`, or their generators — unchanged.
- `Homework_Materials/` — not touched.
- `book/_build/` (build output, gitignored) — rebuilt locally for testing,
  never committed.
