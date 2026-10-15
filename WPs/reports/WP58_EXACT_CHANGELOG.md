# WP58 Exact Changelog — Exercise 10: Deep Learning (local review only)

Branch: `feature/wp58-active-exercise-10-deep-learning`, created from
`main` at `c94628f`. **No merge, push, or deployment.**

## New files

- `scripts/generate_exercise_10_deep_learning_notebook.py` — the single
  authoritative generator for the student (Colab/local) notebook and the
  private teacher-filled reference notebook; renders one shared cell list
  twice (`build_notebook("student")` / `build_notebook("reference")`), so
  the two stay structurally synchronized by construction. No JupyterLite
  template, no transition page, no manifest/toc entry — Gate A found
  PyTorch does not work in this course's pinned JupyterLite build (see
  `WPs/reports/WP58_REPORT.md`), so there is nothing for those to wire up
  to. Imports `scripts/abide_modeling_data.py` at *generation* time only
  (to compute the real, leakage-guarded 1,440-column feature list via
  `bundle_columns("all-eligible", ["CT", "Area", "Vol", "LGI"])`); the
  generated notebook's own embedded data loader is self-contained (no
  runtime dependency on `scripts/`), matching every other portable
  notebook in this course.
- `book/downloads/chapter_10/exercise_10_deep_learning_portable.ipynb` —
  generated student notebook (Colab/local only). 44 cells: title +
  overview, one hidden setup cell, six numbered sections (Setup and the
  Task; Hold-Out Design and Tensors; Build a Fully Connected Network;
  Train and Validate; Final Evaluation and Comparison; Interpretation and
  Limits), three `# YOUR CODE HERE` blanks (tensors/`DataLoader`; the
  `nn.Module`; `train_one_epoch`/`evaluate`'s forward-pass-and-loss
  lines), six `show_question(...)` hidden-key multiple-choice checks.
  Does not collide with, reference, or replace
  `book/downloads/chapter_10/exercise_10_portable.ipynb` (the existing,
  untouched legacy Exercise 10 portable notebook) — different filename,
  by design.
- `scripts/reference_notebooks/exercise_10_deep_learning_reference.ipynb`
  — generated, fully solved, private reference notebook (test/author-only,
  never published; same 44 cells, same ids, as the student notebook except
  the three blank cells carry the real solution instead of `...`
  placeholders).
- `tests/test_exercise_10_deep_learning_notebook.py` — 29 structural/
  offline tests: nbformat validity; title/overview/section structure and
  correspondence; the Colab/local-only + Gate A evidence language (exact
  Pyodide version, "verified directly, not assumed"); the single
  conditional `%pip install torch` cell; exact data counts (1,440
  features, 1,004 participants, all four feature-family names); no MyST
  directive fences; no engineering vocabulary leaking to student text;
  the three blank-tagged cells and a ten-phrase no-full-solution-leaked
  audit of their student-visible hints; all six `show_question` calls
  present with the right ids and nowhere else; `correct_index` never
  appearing outside the one hidden setup cell; the hidden setup cell being
  the first code cell; train-only-scaling and one-time-test-evaluation
  language; the three-model comparison table's columns; the Exercise-3
  context sentence's "not… a directly controlled comparison" framing; the
  Saponaro et al. (2022) citation's exact numbers (1,638 participants, 37
  sites, 221 features, AUC 0.58→0.67) and its functional-vs-structural-MRI
  distinction; no diagnostic/causal/definitive-ceiling claim; no
  repository-relative dependency in the portable notebook;
  student/reference structural synchronization (identical cell ids,
  differing only in the three intended blanks); generator-staleness
  (imports the generator module directly, no shell-out, no network); and
  that the legacy Exercise 10 notebook, its portable copy, and the live
  placeholder page remain untouched.
- `WPs/reports/WP58_REPORT.md` — this WP's full report (Gate A evidence
  and verdicts, notebook content summary, honest final numbers, focused
  test/execution verification, local preview instructions, deviations,
  and the release decisions left open for the course author).
- `WPs/reports/WP58_EXACT_CHANGELOG.md` — this file.

## Modified files

None. `book/chapters/chapter_10/` (the legacy notebook, its portable
copy's directory, and the live placeholder page), `book/_toc.yml`,
`book/_config.yml`, `book/config/exercise_manifest.json`,
`book/intro.md`, `book/resources.md`, and `book/references.md` are all
byte-identical to their state at the branch point — confirmed by `git
status --short` listing only the five new files above throughout this WP,
at every checkpoint.

## Deleted files

None.

## Checkpoint

- Checkpoint commit: `checkpoint: before WP58` (adds the attached
  `WPs/WP58_ACTIVE_EXERCISE_10_DEEP_LEARNING.md` spec to the new branch;
  the working tree was already clean of anything else).
- Tag: `wp58-start`, at the checkpoint commit.
- The checkpoint and implementation commits were each recreated once,
  via `git reset --soft` back to the branch point (no content lost; both
  commits were local and unpushed) plus `git tag -d`/`git tag`, after the
  first attempt omitted the required `Co-Authored-By` trailer. No
  `--amend`, no interactive rebase, no force-push.

## Investigation artifacts (not committed; scratchpad/local only)

- A one-off headless-Chromium Playwright script that loaded the real
  pinned Pyodide v314.0.5 build and ran `micropip.install("torch")`
  (Gate A item 1's live-attempt evidence) — run from a copy placed
  temporarily under `interactive/` (for `node_modules` resolution) and
  removed immediately after use; never committed.
- Two isolated Python 3.11 virtual environments (one with `torch`
  pre-installed, one without) used to verify Gate A item 2 and to execute
  the reference notebook end-to-end for timing — created under this
  session's scratchpad directory, including a temporary Jupyter
  kernelspec registered under the user's `~/Library/Jupyter/kernels/` for
  `nbconvert --execute` to use; both the kernelspecs and the scratch run
  directories were removed after verification completed.
- Exploratory, throwaway experiment scripts used to verify the real
  honest numbers (data counts, split sizes, a small validation-only
  hyperparameter grid for both the network and the logistic-regression
  baseline) before writing the generator — kept entirely in this
  session's scratchpad directory, never committed to the repository.

None of the above persists in the repository or on the branch; they are
recorded here only so the verification trail is reconstructable.
