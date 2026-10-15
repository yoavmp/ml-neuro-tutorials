# WP59 Exact Changelog — Exercise 10 wording fixes and release

Branch: `feature/wp58-active-exercise-10-deep-learning` (continued from
WP58). Implementation commit `d4342c8`, merged to `main` as `8fdec82`
(`c94628f..8fdec82`), pushed once.

## Modified files

- `scripts/generate_exercise_10_deep_learning_notebook.py`
  - `_title_and_overview()`: opening paragraph replaced with the exact
    required text (dropped the WebAssembly/PyPI-wheel explanation and the
    "see the note at the end of Section 1" cross-reference).
  - `_section_1()`: the cell combining the "zero missing values" note and
    the "Note on the JupyterLite limitation (Gate A)" blockquote is split
    — the blockquote is deleted entirely; the "zero missing values"
    sentence survives alone, in a cell renamed
    `wp58-106-missing-values-note` (was `wp58-106-jupyterlite-note`).
  - `_section_2()`: tensor-conversion task intro now reads "...since
    `BCEWithLogitsLoss` (our loss function) expects predictions and
    targets to have matching shapes..." (was "...since
    `BCEWithLogitsLoss` expects...").
  - `_section_3()`: model intro's architecture parenthesis shortened from
    "({HIDDEN_1} units, then {HIDDEN_2} units -- chosen, along with the
    learning rate below, by comparing a handful of configurations on the
    *validation* set only, never the test set)" to "({HIDDEN_1} units,
    then {HIDDEN_2} units)" (renders as "(128 units, then 32 units)").
- `book/downloads/chapter_10/exercise_10_deep_learning_portable.ipynb`
  and `scripts/reference_notebooks/exercise_10_deep_learning_reference.ipynb`
  — regenerated via `python3 scripts/generate_exercise_10_deep_learning_notebook.py
  --write --all`. Markdown-only diff in both (verified: every changed
  hunk is inside a markdown cell's `source`; 44 cells in each, unchanged).
- `book/chapters/chapter_10/placeholder.md` — content replaced (filename
  unchanged). Old: title + "Materials for this exercise will be added
  before the practice session." New: title + the Colab/local-only runtime
  sentence + a download link
  (`https://raw.githubusercontent.com/yoavmp/ml-neuro-tutorials/main/book/downloads/chapter_10/exercise_10_deep_learning_portable.ipynb`)
  + an Open-in-Colab link
  (`https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/blob/main/book/downloads/chapter_10/exercise_10_deep_learning_portable.ipynb`)
  + a backlink to Introduction (`../../intro.md`).
- `book/config/exercise_manifest.json` — exercise 10's
  `fallbackDownloadablePath`: `downloads/chapter_10/exercise_10_portable.ipynb`
  → `downloads/chapter_10/exercise_10_deep_learning_portable.ipynb`. Updated
  the manifest's top-level `$comment` to describe the new state.
- `book/intro.md` — new "### PyTorch for Exercise 10 (optional)"
  subsection after "Working locally (optional)": states PyTorch is
  Colab/local-only and not available in-browser, links
  https://pytorch.org/get-started/locally/, gives a `pip install torch`
  example.
- `book/resources.md` — new bullet under "Python and Jupyter
  documentation": `[PyTorch documentation](https://pytorch.org/docs/stable/)`.
- `book/_config.yml` — `exclude_patterns` comment block updated (the
  `- chapters/chapter_10/exercise_10.ipynb` exclusion itself is
  unchanged) to describe Exercise 10's new published state instead of
  the old "titled 'coming later' placeholder stubs for Exercises 10-11"
  wording.
- `tests/test_exercise_10_deep_learning_notebook.py`
  - `test_colab_local_only_and_no_jupyterlite_claim`: now asserts the
    exact new opening-paragraph text (whitespace-normalized).
  - Removed `test_pyodide_version_and_evidence_named`; added
    `test_gate_a_evidence_kept_in_the_wp_report_not_the_notebook`
    (asserts "Gate A", "jupyterlite-pyodide-kernel 0.8.5", "Pyodide
    v314.0.5", "verified directly, not assumed" are all **absent** from
    the notebook, and that "zero missing values" survives).
  - Added `test_shape_explanation_names_bcewithlogitsloss_as_our_loss_function`.
  - Added `test_architecture_parenthesis_is_short` (asserts
    "(128 units, then 32 units)" present, old "chosen, along with the
    learning" clause absent).
  - `LegacyExerciseTenUntouched`: replaced
    `test_placeholder_page_still_says_coming_later` with
    `test_live_page_links_to_this_wp_notebook_not_the_legacy_one`
    (asserts no "will be added" stub text, no iframe, the new notebook's
    filename present, the legacy portable's filename and `lite/notebooks`
    absent); updated the class docstring.
- `tests/test_book_structure.py` — split
  `test_exercise_10_and_11_placeholders_are_titled_and_not_misleading`
  into `test_exercise_11_placeholder_is_titled_and_not_misleading`
  (Exercise 11 half, assertions unchanged) and
  `test_exercise_10_is_published_as_a_colab_local_download_page` (new:
  asserts the title, the Colab/local-only sentence, the new notebook
  filename, the `colab.research.google.com/github/yoavmp/
  ml-neuro-tutorials` link, and the absence of "will be added",
  `lite/notebooks`, and "Open Exercise 10").
- `interactive/e2e-book/launch-buttons.spec.ts` — comment above the
  Chapter 10 test updated (was: "titled 'coming later' stub... an
  unmapped-page omission"; now explains the page is a real Colab/
  local-only download page whose top-bar-button suppression is
  deliberate, not an unmapped-page omission); test name and assertion
  unchanged (still `toHaveCount(0)` for `colab-launch-button`).
- `interactive/playwright.book.config.ts` — comment explaining
  `chapter10.spec.ts`'s `testIgnore` entry rewritten (was: "chapter 10 no
  longer exists in the built book... would fail on a 404"; now: the old
  legacy iframe-embedded page that spec exercises is permanently
  superseded by this WP's own Colab-only page, so the spec can never pass
  again as written). `testIgnore` list itself unchanged.

## New files

- `WPs/reports/WP59_REPORT.md` (this WP's report)
- `WPs/reports/WP59_EXACT_CHANGELOG.md` (this file)

## Files explicitly NOT touched

- `book/chapters/chapter_11/exercise_11.md` (Exercise 11 placeholder)
- `book/chapters/chapter_10/exercise_10.ipynb` (preserved legacy notebook)
- `book/downloads/chapter_10/exercise_10_portable.ipynb` (legacy portable
  copy)
- `book/_toc.yml` (Exercise 10's toctree entry stays
  `chapters/chapter_10/placeholder`, unchanged)
- `book/_static/launch-buttons.js` (its `PAGE_TO_PORTABLE` map
  deliberately does not gain a `chapter_10` entry)
- `tests/test_placeholder_exercises.py`, `tests/test_wp25_content_audit.py`,
  `tests/test_exercise_manifest.py`, `tests/test_classify_release_change.py`,
  `interactive/e2e-book/chapter10.spec.ts`,
  `interactive/e2e-book/iframe-height-contract.spec.ts`,
  `interactive/e2e-book/warning-sweep.spec.ts` — all read in full and
  confirmed to need no change (see WP59_REPORT.md section 3 for why each
  one).

## Commits

- `d4342c8` — "WP59: wording cleanup + release Exercise 10 as a Colab/
  local download page" (all file changes above except this changelog and
  the report).
- `8fdec82` — "Merge feature/wp58-active-exercise-10-deep-learning:
  release Exercise 10 (Deep Learning)" (merge commit on `main`,
  `--no-ff`).
- This report + changelog: a separate commit on `main` (not part of the
  CI-triggering push, since `WPs/**` is excluded from
  `.github/workflows/deploy.yml`'s trigger paths).

## CI / deployment

- Push: `c94628f..8fdec82` to `origin/main`.
- Triggered runs: `Build and deploy Jupyter Book` (run `38724820626`,
  `full` gate, succeeded, 1h53m55s, `Publish website` step succeeded) and
  `Legacy notebook smoke test (Exercise 10)` (run `38724820644`,
  non-blocking, succeeded, 57s).
- One push was sufficient — no corrective push was needed.
