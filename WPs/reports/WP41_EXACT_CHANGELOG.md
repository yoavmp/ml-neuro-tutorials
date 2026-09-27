# WP41 exact changelog

Start commit: `24a1bd99e697acb8c0ec8355efb43bc485c6ffd2` (local `main`, also
`archive/pre-wp41-jupyterlite-course-platform`).
Feature branch: `feature/wp41-jupyterlite-course-platform`.
Commits (in order):

1. `ce71d20` -- WP41: add revised specification (checkpoint).
2. `df95b00` -- WP41 Gate A: JupyterLite platform proof (pinned build,
   notebook toolbar).
3. `790260e` -- WP41: migrate Exercise 2 to a JupyterLite-native
   active-learning notebook.
4. This report + changelog commit (see `git log` for its SHA).

`git diff --stat archive/pre-wp41-jupyterlite-course-platform..HEAD`:
42 files changed, 15336 insertions(+), 3027 deletions(-).

## New files

Course platform:
- `.gitignore` (+6): ignore the course-toolbar extension's TypeScript build
  output and packaged labextension (generated, not source).
- `requirements-lite.txt`: pinned `jupyterlite-core==0.8.3`,
  `jupyterlite-pyodide-kernel==0.8.5`.
- `book/lite/jupyter_lite_config.json`: builds only the `notebooks` app,
  strips sourcemaps, registers the course-toolbar federated extension.
- `book/lite/overrides.json`: preloads numpy/pandas/scikit-learn/matplotlib
  with no install cell.
- `book/lite/extensions/course-toolbar/` (`package.json`,
  `package-lock.json`, `tsconfig.json`, `src/index.ts`, `style/index.css`):
  the reusable "Back to course contents" / "Download my notebook" /
  "Reset from course template" / save-status JupyterLab extension.
- `book/lite/files/gate_a_proof.ipynb`,
  `book/lite/files/data/gate_a_sample.csv`: Gate A's infrastructure-only
  proof notebook and its tiny same-origin data asset (not student content).

Exercise 2 migration:
- `book/config/exercise_manifest.json`: the Exercises 1-12 manifest.
- `scripts/export_abide_lite_data.py`: generates
  `book/lite/files/data/abide_age_brain.csv` (+
  `abide_age_brain.manifest.json` sidecar) from the established canonical
  recipe.
- `scripts/generate_exercise_02_notebook.py`: the authoritative generator
  for `book/lite/files/exercise_02.ipynb`,
  `book/downloads/chapter_02/exercise_02_portable.ipynb`, and
  `scripts/reference_notebooks/exercise_02_reference.ipynb`.
- `scripts/generate_exercise_02_transition_page.py`: generates
  `book/chapters/chapter_02/exercise_02.ipynb` (now a transition page).
- `scripts/render_exercise_02_reference_plot.py`: generates
  `book/lite/files/data/exercise_02_observed_vs_predicted.png`, embedded in
  Activity 3B.
- `interactive/e2e-book/exercise-02-lite.spec.ts`: browser platform tests.
- `tests/test_exercise_02_transition_page.py`,
  `tests/test_exercise_02_lite_notebook.py`,
  `tests/test_exercise_02_reference_execution.py`,
  `tests/test_exercise_manifest.py`,
  `tests/test_export_abide_lite_data.py`.
- `WPs/reports/WP41_MAINTAINER_GUIDE.md`.

## Modified files

- `book/_config.yml` (+6): excludes `book/lite/` from the Jupyter Book
  Sphinx source scan (it is JupyterLite source material, not book content).
- `book/chapters/chapter_02/exercise_02.ipynb` (1557 lines -> 2 cells):
  replaced with the transition page. The removed content is not lost --
  it lives on `archive/pre-wp41-jupyterlite-course-platform` and is the
  direct source the new generator's prose/code/numbers were built from.
- `book/downloads/chapter_02/exercise_02_portable.ipynb`: regenerated
  (previously produced by `scripts/build_portable_notebook.py`'s
  MyST-rewriting pipeline from the old canonical notebook; now produced by
  `scripts/generate_exercise_02_notebook.py` directly, byte-identical to
  `book/lite/files/exercise_02.ipynb`).
- `scripts/build_portable_notebook.py` (-101/+~20 net): removed the
  `chapter_02` `NotebookSpec` and its `_CH2_*` banner/setup/iframe-
  replacement constants and the now-unused `PUBLISHED_PAGE_CH2` constant;
  updated its module docstring's notebook-key list and Exercises-11-12 note.
- `interactive/e2e-book/chapter02.spec.ts`: replaced entirely (the old
  spec tested the retired knn-explore iframe embed; the new one tests the
  transition page's link and absence of any embedded iframe/analysis code).
- Five cross-notebook tests updated because they read Exercise 2's old
  implementation details as part of a repo-wide check:
  - `tests/test_notebook_opening_structure.py`: removed `chapter_02` from
    the `CANONICAL`/`PORTABLE`/`EXERCISE_NUMBERS` maps and the two loops
    that asserted its old cell-4 hide-input/output convention (now scoped
    to `chapter_03` only).
  - `tests/test_think_first_shared_class.py`: removed `chapter_02` from
    the notebooks scanned for the shared `think-first` MyST admonition
    class (the transition page has no MyST admonitions).
  - `tests/test_wp19_content_audit.py`: the fixed-k=20 language check now
    reads the completed reference notebook
    (`KNeighborsRegressor(n_neighbors=20)`) instead of a `K_EXAMPLE = 20`
    constant in the old canonical/portable notebooks, since that step is
    now a student "YOUR CODE HERE" activity.
  - `tests/test_wp24_content_audit.py`: `Exercise2SampleSizeSectionAccurate`
    now reads `book/lite/files/exercise_02.ipynb`'s `## Bonus` section
    instead of the old canonical page's `### What does sample size
    change?` subsection; the generator's Bonus intro was extended to keep
    covering the same required points ("not chosen by ranking", "teaching
    demonstration").
  - `tests/test_wp25_content_audit.py`:
    `test_only_one_active_copy_of_the_transferred_knn_material` now checks
    the reference notebook for exactly one
    `KNeighborsRegressor(n_neighbors=20)` fit and asserts the transition
    page contains no `KNeighborsRegressor` reference at all, replacing the
    old `K_EXAMPLE = 20`-cell-count check against the (now retired)
    canonical notebook.
  - `tests/test_exercise_03_notebook.py`,
    `tests/test_exercise_04_notebook.py`: their cross-checks against
    Exercise 2's internal `FEATURES`-derivation source line and `PIN`
    constant were replaced with checks against the actual 360-column
    recipe (via the new data-export sidecar manifest) and the pinned
    commit SHA respectively, so they no longer depend on Exercise 2's
    internal implementation.

## Removed files

- `tests/test_exercise_02_notebook.py` (442 lines): validated the old
  canonical notebook's exact content (cell IDs, section headings, specific
  wording, embedded iframe). Superseded by
  `tests/test_exercise_02_transition_page.py` and
  `tests/test_exercise_02_lite_notebook.py` /
  `tests/test_exercise_02_reference_execution.py`.

## Data/content moved, not deleted

- Exercise 2's pre-WP41 lesson prose, code, and structure: preserved
  verbatim on `archive/pre-wp41-jupyterlite-course-platform` (and in this
  branch's own history before commit `790260e`).
- Exercise 2's interactive activity code (`interactive/src/knn-explore*.ts`,
  `book/_static/widgets/configs/knn_explore.json`,
  `book/_static/widgets/data/abide_knn_explore*`): left untouched on disk.
  WP41 does not remove the old widget/React-style implementation (per its
  own scope rule); it is simply no longer embedded by Exercise 2's new
  canonical page. It remains available for reference and is still built by
  `interactive/`'s existing pipeline.

## Not changed

- `book/_toc.yml`: unchanged. The Contents page's `{tableofcontents}`
  listing reads each exercise's title directly from its page, so no TOC
  edit was needed for the transition page to keep showing "Exercise 2:
  Regression and Bias-Variance Trade-Off" in place.
- Exercises 1, 3-12 and their portable notebooks/widget configs: untouched
  except for the five test-file updates above, all of which check the
  *unmigrated* exercises' actual content unchanged and only adjust how
  they cross-reference Exercise 2.
- `.github/workflows/deploy.yml`: not touched. Wiring a JupyterLite build
  step into CI is explicitly out of this WP's scope (see "Deviations" in
  `WP41_REPORT.md`).
