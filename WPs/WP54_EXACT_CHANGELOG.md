# WP54 exact changelog

Diff base: `5cfa89c` (main tip before this WP) -> `df390e6` (pushed,
deployed). Spec commit `6e50502` -> content commit `df390e6`
(`git diff --stat 6e50502 df390e6` below).

```
 book/_toc.yml                                      |   6 +-
 book/downloads/chapter_05/exercise_05_portable.ipynb |   8 +-
 book/downloads/chapter_06/exercise_06_portable.ipynb | 127 ++++++++++++++-----
 book/downloads/chapter_09/exercise_09_portable.ipynb |  17 ++-
 book/intro.md                                      |  62 +++++++---
 book/lite/files/exercise_05.ipynb                  |   8 +-
 book/lite/files/exercise_05_portable.ipynb         |   8 +-
 book/lite/files/exercise_06.ipynb                  | 127 ++++++++++++++-----
 book/lite/files/exercise_06_portable.ipynb         | 127 ++++++++++++++-----
 book/lite/files/exercise_09.ipynb                  |  17 ++-
 book/lite/files/exercise_09_portable.ipynb         |  17 ++-
 book/references.md                                 |  32 +++++ (new)
 book/resources.md                                  |  43 +++++++ (new)
 book/syllabus.md                                   |  72 +++++++++++
 interactive/e2e-book/exercise-06-lite.spec.ts      |  72 ++++++++++-
 scripts/generate_exercise_05_notebook.py           |   8 +-
 scripts/generate_exercise_06_notebook.py           | 127 ++++++++++++++-----
 scripts/generate_exercise_09_notebook.py           |  17 ++-
 scripts/reference_notebooks/exercise_05_reference.ipynb |   8 +-
 scripts/reference_notebooks/exercise_06_reference.ipynb | 127 ++++++++++++++-----
 scripts/reference_notebooks/exercise_09_reference.ipynb |  17 ++-
 tests/test_book_structure.py                       | 137 +++++++++++++++++++--
 tests/test_exercise_06_lite_notebook.py            |  34 +++--
 tests/test_exercise_06_reference_execution.py      |  65 ++++++++++
 tests/test_exercise_09_lite_notebook.py            |  13 ++
 tests/test_exercise_09_reference_execution.py      |  52 ++++++++
 tests/test_wp25_content_audit.py                   |   7 --
 27 files changed, 1128 insertions(+), 227 deletions(-)
```

## Section 1 -- question-cell audit, old-copy guidance

- No notebook/generator code change (audit found no leak).
- `book/intro.md`: new "Opening an old downloaded copy later" subsection.

## Section 2 -- Exercise 6 regression-tree diagram

- `scripts/generate_exercise_06_notebook.py`:
  - Import line: dropped unused `plot_tree` from the `sklearn.tree` import.
  - `format_tree_diagram()`: full rewrite. Removed the `plot_tree(...)` +
    `zip(order, artists)` pairing entirely. New implementation: `node_label()`
    (per-node text straight from `tree_`), `layout()` (in-order leaf x,
    mean-of-children x for internal nodes, `y = -depth`), `draw_panel()`
    (draws one subtree's boxes/arrows into one `Axes`), then assembles a
    3-row `GridSpec` figure: root box, `<=` panel, `>` panel. `figsize=(10.5,
    10.8), dpi=150` (was `(15, 9), dpi=140` with the old broken call).
  - Regenerated: `book/lite/files/exercise_06.ipynb`,
    `book/lite/files/exercise_06_portable.ipynb`,
    `book/downloads/chapter_06/exercise_06_portable.ipynb`,
    `scripts/reference_notebooks/exercise_06_reference.ipynb`.
- `tests/test_exercise_06_lite_notebook.py`:
  `test_regression_tree_diagram_uses_a_larger_higher_resolution_figure`
  (asserted stale `figsize=(15, 9), dpi=140` text) replaced with
  `test_regression_tree_diagram_draws_every_node_directly_from_tree_`
  (asserts the new mechanism's structural markers and absence of the old
  `plot_tree(`/`zip(order, artists)`/`squared_error = ` text).
- `tests/test_exercise_06_reference_execution.py`: new
  `test_tree_diagram_renders_every_node_directly_from_tree_`.
- `interactive/e2e-book/exercise-06-lite.spec.ts`:
  - `the regression-tree diagram renders as a real, high-resolution image`:
    updated comment/rationale; `naturalWidth`/`naturalHeight` thresholds
    `>= 1800`/`>= 1000` -> `>= 1100`/`>= 1150` (measured-value-based, see
    report); added a portrait-aspect assertion (`naturalHeight >
    naturalWidth`).
  - New test: `the regression-tree diagram itself does not overflow a
    390px viewport`.

## Section 3 -- Exercise 9 PCR-versus-PLS interactive

- `scripts/generate_exercise_09_notebook.py`:
  - `axes[0].annotate("PC2 (fixed)", 1.3 * pc2_dir, xytext=(4, -10),
    textcoords="offset points", ...)` -> `axes[0].annotate("PC2 (fixed)",
    (0.98, 0.09), xycoords="axes fraction", ha="right", ...)`.
  - `axes[0].annotate("PLS direction", 1.2 * pls_dir, xytext=(-62, -12),
    textcoords="offset points", ...)` -> `axes[0].annotate("PLS direction",
    (0.98, 0.025), xycoords="axes fraction", ha="right", ...)`.
  - Arrow draw calls (`axes[0].arrow(...)`) for both PC2 and PLS are
    unchanged -- only the two labels' own anchors moved.
  - Regenerated: `book/lite/files/exercise_09.ipynb`,
    `book/lite/files/exercise_09_portable.ipynb`,
    `book/downloads/chapter_09/exercise_09_portable.ipynb`,
    `scripts/reference_notebooks/exercise_09_reference.ipynb`.
- `tests/test_exercise_09_lite_notebook.py`: new
  `test_pcr_pls_direction_label_is_fixed_below_pc2_not_tied_to_its_own_arrow`.
- `tests/test_exercise_09_reference_execution.py`: new
  `test_pcr_pls_pc2_and_pls_labels_sit_in_a_fixed_corner_never_on_an_arrow`.

## Section 4 -- Syllabus page

- `book/syllabus.md`: replaced the title-only placeholder (`# Syllabus`)
  with the full page (course information, aims/prerequisites, staff/office
  hours, course text/scope, assessment, 13-row schedule). Content sourced
  and cross-verified against the course-author's docx (see report's
  discrepancy table).
- `tests/test_book_structure.py`: `Pages.test_syllabus_is_title_only`
  replaced with `test_syllabus_covers_the_required_facts`,
  `test_syllabus_has_a_13_row_schedule_with_required_columns`,
  `test_syllabus_marks_tentative_topics_as_provisional_not_confirmed`,
  `test_syllabus_does_not_invent_a_room_or_due_dates`,
  `test_syllabus_does_not_imply_exercises_10_to_12_are_published`.
- `tests/test_wp25_content_audit.py`: removed
  `SyllabusPageUnchangedTests.test_syllabus_source_is_byte_for_byte_unchanged_from_the_pre_syllabus_commit`
  (its entire purpose -- proving WP25 left the placeholder untouched -- is
  superseded by this WP deliberately populating the page). No other test
  in that file touched.

## Section 5 -- Introduction

- `book/intro.md`: full rewrite of the "Using the notebooks" section and
  the old "About the questions" section (removed); new "Opening an old
  downloaded copy later" and "Working locally (optional)" sections.
- `tests/test_book_structure.py`: `Pages.test_introduction_covers_the_required_concepts`
  and `test_introduction_has_no_moodle_url_no_time_budget_no_answer_guarantee`
  (renamed `..._no_guaranteed_3_11`) rewritten for the new required content
  and new negative-claim guards.

## Section 6 -- Resources then References

- `book/resources.md` (new): Course text, Datasets and data provenance,
  Python and Jupyter documentation sections.
- `book/references.md` (new): numbered bibliography, course book first,
  then Di Martino et al. (2017) / Bethlehem et al. (2022) / Storsve et al.
  (2014).
- `book/_toc.yml`: added `- file: resources` and `- file: references` as
  new top-level chapters immediately after `contents`.
- `scripts/generate_exercise_05_notebook.py`: Section 2's existing
  Bethlehem/Storsve citation markdown cell -- added a same-origin link to
  the new References page alongside the existing, unchanged DOI links.
  Regenerated: `book/lite/files/exercise_05.ipynb`,
  `book/lite/files/exercise_05_portable.ipynb`,
  `book/downloads/chapter_05/exercise_05_portable.ipynb`,
  `scripts/reference_notebooks/exercise_05_reference.ipynb`.
- `tests/test_book_structure.py`:
  `Toc.test_order_is_intro_syllabus_contents_then_exercise_nested` renamed
  `test_order_is_intro_syllabus_contents_resources_references`, extended
  for the two new chapters; new `test_resources_covers_the_required_minimum_links`,
  `test_resources_does_not_link_private_repo_internals`,
  `test_references_leads_with_the_course_book_and_covers_the_minimum`.

## Release

- `scripts/classify_release_change.py`: `GATE: full` (shared
  `book/_toc.yml`/`book/intro.md`/`book/syllabus.md`, unknown
  `book/references.md`/`book/resources.md`, shared
  `tests/test_book_structure.py`/`tests/test_wp25_content_audit.py`).
  Honored, not overridden.
- Merged `feature/wp54-course-pages-and-notebook-fixes` into `main`
  (fast-forward, `5cfa89c` -> `df390e6`); pushed.
- CI run [`38245266571`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/38245266571):
  success, `build-and-deploy` 1h36m44s.
- `gh-pages` updated to `ba64ce2`, marker `deploy: df390e6...`.
