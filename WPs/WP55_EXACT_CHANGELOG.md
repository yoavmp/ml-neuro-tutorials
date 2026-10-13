# WP55 exact changelog

Diff base: `5dfddcb` (main tip before WP54's own report commit; the last
commit origin/main actually had published) -> current `main` tip after
this WP (pushed, deployed). This range also carries the previously
unpushed `b2f0350` ("docs: standing rule for long-running local commands
and CI watches"), which WP55 explicitly authorized to ride along.

```
 CLAUDE_INTERACTIVE_WIDGETS.md                      |   3 +-
 WPs/WP55_SMALL_COURSE_FIXES_KERNEL_STARTUP_AND_RELEASE.md |  52 ++++++++
 WPs/reports/WP50_MAINTAINER_GUIDE.md               |  92 +++++++++++++
 book/downloads/chapter_01/exercise_01_portable.ipynb |  142 +++++++++++++++-
 book/lite/extensions/course-toolbar/src/index.ts   | 115 ++++++++++++++-
 book/lite/files/data/exercise_01_fiq_viq_reference.png | Bin 0 -> 43292 bytes (new)
 book/lite/files/exercise_01.ipynb                  |  142 +++++++++++++++-
 book/lite/files/exercise_01_portable.ipynb         |  142 +++++++++++++++-
 book/references.md                                 |    9 +-
 book/resources.md                                  |   15 +-
 book/syllabus.md                                   |   12 +-
 interactive/e2e-book/kernel-startup.spec.ts        |  141 +++++++++++++++ (new)
 scripts/generate_exercise_01_notebook.py           |  147 +++++++++++++++-
 scripts/reference_notebooks/exercise_01_reference.ipynb |  148 +++++++++++++-
 scripts/render_exercise_01_fiq_viq_reference_plot.py |   45 +++++++ (new)
 tests/test_book_structure.py                       |   21 +-
 tests/test_exercise_01_lite_notebook.py            |    1 +
 tests/test_exercise_01_reference_execution.py      |   12 ++
 18 files changed, 1200 insertions(+), 39 deletions(-)
```

(The two `WPs/`-prefixed guide files above and the WP55 spec file itself
are the carried-over `b2f0350` commit plus this WP's own spec commit --
both plain documentation, never read at runtime.)

## A. Syllabus

- `book/syllabus.md`:
  - `Mondays, 08:30-11:00 (location not provided in the source syllabus)`
    -> `Mondays, 08:30-11:00, Dan David building, room 110`.
  - Week 9 homework cell: `SVM*` -> `SVM`; removed the trailing footnote
    sentence about the source document's "sum" typo.
  - Replaced the three-sentence "two topics marked *(tentative)*..."
    schedule-intro paragraph with one line: `Practice notebooks: see
    [Contents](contents.md).` Per-row `*(tentative)*` markers (Weeks 4, 5,
    12) are untouched.

## B. Resources

- `book/resources.md`:
  - Removed the opening "A practical link directory for material actually
    used in Exercises 1-9 -- not a general collection." sentence.
  - Replaced the `NeuroHackademy abide2.tsv` bullet (which displayed the
    pinned `raw.githubusercontent.com/.../abide2.tsv` URL and described it
    as "the pinned, checksummed public copy every exercise's data loader
    falls back to") with a student-facing credit bullet linking
    `https://github.com/neurohackademy/nh2020-curriculum/tree/master/tu-machine-learning-yarkoni/data`
    and crediting Prof. Tal Yarkoni's NeuroHackademy 2020 workshop. No
    notebook loader changed -- grepped all 9 generators for the pinned raw
    URL after this edit; still present, byte-identical, in every one.
  - Replaced the "curated exports selected to the columns each exercise
    actually uses ... not the original ABIDE II release" sentence with
    "subsets built from the ABIDE II source above, using the columns each
    exercise requires." The three same-origin CSV `<a href>` links are
    unchanged.

## C. References

- `book/references.md`:
  - Citation 1: removed "This course's own text, used throughout
    Exercises 1-9; see also the Syllabus." Citation now ends at
    "Springer."
  - Citation 2: removed the "Exercises 1-9 are built on" phrase; now
    reads "The original publication for the ABIDE II dataset; see
    Resources for the dataset's own official site and the course's
    curated data exports."

## Regression fix: `tests/test_book_structure.py`

- `test_syllabus_does_not_invent_a_room_or_due_dates` ->
  `test_syllabus_states_the_real_room_and_does_not_invent_due_dates`:
  asserts the new room string is present and the old "location not
  provided" placeholder is gone (previously asserted the opposite).
- `test_syllabus_does_not_imply_exercises_10_to_12_are_published`:
  previously asserted the literal (now-removed) sentence "Only Exercises
  1-9 are published"; now asserts the new Contents link is present and no
  "Exercise 10/11/12" text appears.
- `test_resources_covers_the_required_minimum_links`: the
  `raw.githubusercontent.com/neurohackademy/nh2020-curriculum` needle
  (text no longer displayed on this page) replaced with
  `github.com/neurohackademy/nh2020-curriculum` (the new credit link).

## D. Exercise 1

- `scripts/generate_exercise_01_notebook.py`:
  - `md()`: new optional `attachments` parameter (same nbformat
    cell-attachment mechanism `generate_exercise_02_notebook.py` already
    uses for its own reference image).
  - New `FIQ_VIQ_REFERENCE_IMAGE_PATH`/`_fiq_viq_reference_image_attachments()`/
    `_fiq_viq_reference_image_markdown()` helpers (base64-embeds
    `book/lite/files/data/exercise_01_fiq_viq_reference.png`).
  - `wp42-608-group-answer`: old unsupported open question replaced with a
    short bold prompt followed, in the same cell, by a plain-text answered
    anecdote (site/measurement-confound explanation).
  - `_section_6()`: added, after the existing Pearson-r correlation matrix
    and checked question --
    - `wp42-612` header + `wp42-613` instructions (FIQ-vs-VIQ activity).
    - `wp42-614`/`wp42-615`: "approved current result" intro + the
      attachment-embedded reference image.
    - `wp42-616-fiq-viq-blank` (new `Blank`, tag
      `wp42-activity-fiq-viq-scatter`): student computes `paired`/
      `fiq_viq_r` and plots FIQ-vs-VIQ; hints are prose only, no working
      code.
    - `wp42-617-fiq-viq-check`: non-raising check cell, recomputes the
      expected r independently from `data`.
    - `wp42-618`/`wp42-619`: header + intro for the supplied scatter
      matrix.
    - `wp42-620-scatter-matrix`: supplied `pandas.plotting.scatter_matrix`
      cell over `AGE_AT_SCAN`/`FIQ`/`VIQ`/`PIQ`, complete-case count
      printed, `data` itself untouched.
  - `_build_cells()`: `_section_6()`'s cells now pass through the same
    `Blank.render(mode)` mapping every other section already uses (needed
    once section 6 gained its own `Blank`).
- New `scripts/render_exercise_01_fiq_viq_reference_plot.py`: offline,
  reads the committed `abide_phenotypes.csv`, computes the real paired
  FIQ/VIQ Pearson r (`n=796, r=0.83`), saves the reference PNG.
- Regenerated: `book/lite/files/exercise_01.ipynb`,
  `book/lite/files/exercise_01_portable.ipynb`,
  `book/downloads/chapter_01/exercise_01_portable.ipynb`,
  `scripts/reference_notebooks/exercise_01_reference.ipynb`.
- `tests/test_exercise_01_lite_notebook.py`: added
  `wp42-activity-fiq-viq-scatter` to `StructuralSynchronization`'s
  `blank_tags` set (the reference/template diff check).
- `tests/test_exercise_01_reference_execution.py`: two new tests --
  `test_fiq_viq_scatter_activity_matches_established_result` (`paired`
  has 796 rows, `fiq_viq_r` ~= 0.833) and
  `test_scatter_matrix_complete_cases_match_established_result`
  (`complete_for_matrix` has 783 rows).

## E. JupyterLite kernel startup

- `book/lite/extensions/course-toolbar/src/index.ts`:
  - New `ensureKernelStarted(app, panel)`: checks for an already-running
    kernel; if none, races `panel.sessionContext.ready` against a 30s
    timeout (to distinguish "merely still settling" from "genuinely
    stuck" without ever awaiting `ready` directly -- it can hang forever
    in the exact stuck case); if still no kernel after that, awaits
    `app.serviceManager.kernelspecs.ready` (bounded to another 30s), then
    explicitly starts the registry's `specs.default`-named kernel via
    `panel.sessionContext.changeKernel(...)`; reports a `showDialog` on a
    genuine timeout or thrown error. (A first version of this fix skipped
    the `sessionContext.ready`-race step -- caught introducing a new,
    real "`<uuid> was disposed`" console error into 2 of 9 exercises'
    browser tests, root-caused via a direct A/B test against the
    unmodified original extension, before this was ever considered done;
    see the report's Section E for the full investigation.)
  - `activate()`: `_app` parameter renamed to `app` (now used); calls
    `void ensureKernelStarted(app, panel)` alongside the existing
    `addButtons`/`addStatusReadout` calls inside the `panel.context.ready`
    handler.
  - Rebuilt the labextension bundle (`npx tsc && jupyter labextension
    build --development True .`) -- output is gitignored, regenerated by
    CI itself.
- New `interactive/e2e-book/kernel-startup.spec.ts`: 5 tests (3 fresh
  opens, 1 fresh open under the `/ml-neuro-tutorials/...` path-prefixed
  route, 1 returning-profile edit+reload), each confirming the kernel
  reaches "Python (Pyodide)" and a trivial cell executes with no error
  cell, with console/network diagnostics captured into the failure
  message.

Pushed and deployed: `main` -> `c10d714`, CI run
[`38394912271`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/38394912271)
(success, 1h50m35s), `gh-pages` marker `deploy: c10d714...`. See the
report's own Verification/Final-git-state sections for the full detail,
including a stale accidental CI run (`38394864039`) triggered by an
initial `git push` from the feature branch before `main` was fast-
forwarded, caught and cancelled before it could race the real deploy.
