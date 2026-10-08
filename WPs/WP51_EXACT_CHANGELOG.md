# WP51 exact changelog

Starting SHA (local `main`): `c5acbe3` ("WP50: reports -- real CI results,
live-site verification, and the local fast-path demo"), matching
`origin/main`.

Feature branch: `feature/wp51-active-exercise-09`, created from that tip.

Commits made by this WP, in order:
1. `e329501` -- checkpoint the WP spec on the dedicated feature branch.
2. `98b21cc` -- build Exercise 9's active JupyterLite-native notebook
   (generator, generated outputs, build-tooling deregistration, tests);
   10 files changed, +8777/-653 (see `git show --stat 98b21cc` for exact
   per-file counts).
3. This report + this changelog (committed together as this WP's closing
   commit; see `git log -1` after that commit for the final SHA).

No merge, no push, no deployment, no GitHub Actions interaction at any
point. `book/_toc.yml`, `book/_config.yml`, `book/config/
exercise_manifest.json`, and `book/_static/launch-buttons.js` are
untouched.

## Changed/added files (commit `98b21cc`)

```
A  scripts/generate_exercise_09_notebook.py
A  book/lite/files/exercise_09.ipynb
A  book/lite/files/exercise_09_portable.ipynb
M  book/downloads/chapter_09/exercise_09_portable.ipynb
A  scripts/reference_notebooks/exercise_09_reference.ipynb
M  scripts/build_portable_notebook.py
M  scripts/smoke_portable_notebook.py
A  tests/test_exercise_09_lite_notebook.py
A  tests/test_exercise_09_reference_execution.py
M  tests/test_exercise_09_notebook.py
```

- `scripts/generate_exercise_09_notebook.py` (new, ~1,790 lines): the sole
  generator for Exercise 9's four derived notebooks, modeled on
  `scripts/generate_exercise_08_notebook.py`'s exact shape (`--write`/
  `--check`, `--student`/`--reference`, the `Blank` class, the hidden
  `wp51-000-setup` cell carrying `show_question()`'s answer-key-hiding
  `_QUESTIONS` dict). See its own module docstring for every verified
  number and the reasoning behind the SVR-subset runtime decision.
- `book/lite/files/exercise_09.ipynb` (new): the JupyterLite template, 60
  cells, built from this generator in `--student` mode.
- `book/lite/files/exercise_09_portable.ipynb` (new): the served portable
  copy -- byte-identical to the JupyterLite template (verified by
  `tests/test_exercise_09_lite_notebook.py::StructuralSynchronization`).
- `book/downloads/chapter_09/exercise_09_portable.ipynb` (modified): the
  Colab/local download, now written by the new generator instead of
  `scripts/build_portable_notebook.py`'s old MyST-rewriting pipeline
  (which used to derive it from the legacy
  `book/chapters/chapter_09/exercise_09.ipynb`). Same content as the
  JupyterLite template.
- `scripts/reference_notebooks/exercise_09_reference.ipynb` (new): the
  teacher-filled copy, built in `--reference` mode -- every blank solved,
  no `YOUR CODE HERE` text remaining.
- `scripts/build_portable_notebook.py` (modified): `CHAPTER_09` removed
  from the `NOTEBOOKS` registry dict (the `CHAPTER_09` spec constant
  itself is left defined, unused, mirroring the WP47/chapter_08 and every
  earlier migration's precedent); docstring/comments updated to name
  Exercise 9 among the already-migrated chapters.
- `scripts/smoke_portable_notebook.py` (modified): the `"chapter_09"` entry
  removed from the `SMOKE` dict (its two native `ipywidgets.Output()`
  context-manager activities are expected to hang `nbclient`'s real ZMQ
  kernel, the same documented reason chapters 1, 4, 5, 6, 7, and 8 are
  already absent); module docstring and the preceding comment block
  updated accordingly, including an explicit note that
  `.github/workflows/legacy-notebook-smoke.yml`'s own `--notebook
  chapter_09` step is now stale and is a known follow-up for a later,
  explicitly authorized deployment WP, not fixed in this one.
- `tests/test_exercise_09_lite_notebook.py` (new, 33 tests): structural
  tests for the JupyterLite template -- blanks, tags, required output
  names, checked-question answer-key hiding, both native widgets, the
  nested-CV historical reference's confinement to its own `<details>`
  block, template/portable/reference synchronization. Modeled on
  `tests/test_exercise_08_lite_notebook.py`.
- `tests/test_exercise_09_reference_execution.py` (new, 18 tests):
  executes the reference notebook and the untouched student template in
  one shared namespace (not `nbclient`, for the same `ipywidgets.Output()`
  reason noted above) and checks every established number and the
  no-cascade behavior of the untouched template. Modeled on
  `tests/test_exercise_08_reference_execution.py`.
- `tests/test_exercise_09_notebook.py` (modified, 1 test rewritten): this
  file's `LaunchButtonsAndPortable` class tests
  `book/downloads/chapter_09/exercise_09_portable.ipynb`, now this WP's
  own output. `test_portable_notebook_keeps_the_nested_cv_comparison_
  visible_and_runnable` asserted exactly the old five-model live grid this
  WP was asked to remove, so it is replaced with
  `test_portable_notebook_no_longer_embeds_the_old_five_model_nested_cv_
  as_its_own_result`, asserting the opposite plus the presence of the new
  labeled historical reference. Every other test in this file (which all
  target the untouched, still-excluded-from-the-Sphinx-build
  `book/chapters/chapter_09/exercise_09.ipynb`) is unchanged and still
  green.

## Not changed

`book/chapters/chapter_09/exercise_09.ipynb` (the legacy static page,
excluded from the Sphinx `exclude_patterns` since WP49), `book/_toc.yml`,
`book/_config.yml`, `book/config/exercise_manifest.json`,
`book/_static/launch-buttons.js`, `.github/workflows/*.yml`, and every
Exercises 1-8/10-12 file.
