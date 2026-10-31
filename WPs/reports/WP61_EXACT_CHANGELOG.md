# WP61 Exact Changelog — Exercise 11: Embeddings and RSA (local only)

Branch: `feature/wp61-embeddings-and-rsa`, off `main` at `c056b01`.
Checkpoint `f07c3a3` (tag `wp61-start`). Implementation commit `d6fd7af`.
Not merged, not pushed.

## New files

- `scripts/export_haxby_rsa_data.py` — maintainer-only offline extraction
  script (`--refresh` network mode, `--check` offline mode). Fetches
  subject 2's Haxby et al. (2001) data via
  `nilearn.datasets.fetch_haxby(subjects=[2], fetch_stimuli=False)`,
  masks with `mask4_vt.nii.gz` (`mask_vt`, 464 voxels), per-run z-scores
  every voxel, finds contiguous same-label spans per run from
  `labels.txt`, drops the first 2 TRs of every non-"rest" span, averages
  the rest into one category pattern per (run, category). Writes
  `book/lite/files/data/haxby_rsa_patterns.csv` and its
  `.manifest.json` sidecar.
- `book/lite/files/data/haxby_rsa_patterns.csv` — 881,847 bytes, 96 rows
  (12 runs × 8 categories), 466 columns (`run`, `category`, 464
  `voxel_####`). sha256
  `371e5b44e416b090cf487d89103b7f8f69444fc9f9385112aa61a7035ebb1f95`.
- `book/lite/files/data/haxby_rsa_patterns.manifest.json` — provenance
  (citation, source URL, license statement), mask used, every
  extraction-method choice, observed block lengths (`[9]`) and TRs
  dropped (`[2]`), exclusions (`["none: ..."]`), odd/even coverage check
  (`true`), derived-file checksum/dimensions.
- `scripts/generate_exercise_11_notebook.py` — the notebook generator
  (`--write`/`--check`, `--student`/`--reference`/`--all`), following
  `generate_exercise_09_notebook.py`'s exact architecture: `md()`/`code()`/
  `Blank`/`blank()` helpers, a hidden `wp61-000-setup` cell carrying
  `load_haxby_rsa_table()`, `category_patterns_from()`, `upper_triangle()`,
  the question-widget builders, `_QUESTIONS`/`show_question()`, and the
  `controls_row()`/CSS helpers (all duplicated, not imported, per the
  established per-generator self-containment convention). Six sections
  (load → neural RDM → MDS → split-half → model comparison → interpret),
  two native `ipywidgets` activities, 6 checked questions, 3 `Blank`
  tasks. Outputs `book/lite/files/exercise_11.ipynb`,
  `book/lite/files/exercise_11_portable.ipynb`, and
  `scripts/reference_notebooks/exercise_11_reference.ipynb`. Does
  **not** write `book/downloads/chapter_11/exercise_11_portable.ipynb`
  (see report's "Deviations" section).
- `book/lite/files/exercise_11.ipynb` — generated student notebook, 42
  cells.
- `book/lite/files/exercise_11_portable.ipynb` — byte-identical to the
  above (same generated text), the portable/Colab-ready served copy.
- `scripts/reference_notebooks/exercise_11_reference.ipynb` — generated
  teacher-filled notebook (every `Blank` renders its `reference_source`);
  never published.
- `tests/test_export_haxby_rsa_data.py` — 10 offline tests: `--check`
  passes; CSV shape (96×466, 12 runs, 8 categories, 464 voxel columns);
  every run has every category exactly once; no missing/non-finite
  values; mask is the broad VT mask (not category-selective); odd/even
  coverage recorded true; subject/source pinned; derived-file checksum
  matches; categories are the documented eight; no exclusions were
  necessary.
- `tests/test_exercise_11_lite_notebook.py` — 42 total with the
  reference-execution file below (this file alone: structural tests
  modeled on `test_exercise_09_lite_notebook.py` — title, run-first
  notice, hidden/collapsed setup cell, actionable `NameError` message,
  reasonable cell count, no stored error outputs, exactly 3
  `YOUR CODE HERE` blanks with the required tags, no commented-out
  solution fragments, required output names appear in each task's
  instructions, exactly 6 checked questions with hidden keys/shuffle
  seeds in the hidden setup cell only, multiselect/full-width CSS present,
  no iframe/legacy-widget-config reference, both native widgets present
  (distance-metric precomputed before use, grouping widget excludes
  `scrambledpix` and is labeled exploratory), widget label-overflow fix
  present, no raw-fMRI import in the student notebook
  (`fetch_haxby`/`nilearn`/`nibabel` absent), "category-level" caveat
  stated, "no p-value is reported" stated, editable answer cells exist,
  no `YOUR ANSWER HERE` placeholder, no WP/script references in student
  text, `book/downloads/chapter_11/exercise_11_portable.ipynb` confirmed
  absent, template/served-copy/reference stay structurally synchronized,
  reference has no `YOUR CODE HERE` placeholders, generator `--check`
  passes.
- `tests/test_exercise_11_reference_execution.py` — executes the
  reference notebook (ast-compile-and-exec per cell, one shared
  namespace, cwd set to `book/lite/files/`); asserts zero errors, data
  shape, `neural_rdm` square/symmetric/zero-diagonal/finite, its distance
  range (0.4255–1.1236, `delta=0.01`), `split_half_r≈0.4854`,
  `face_match_r≈0.2467`, `animacy_match_r≈0.4459` over 7 categories, and
  that every question's shuffle seed is distinct and reproducible.
- `interactive/e2e-book/exercise-11-lite.spec.ts` — Playwright spec
  modeled on `exercise-09-lite.spec.ts`, navigating directly to
  `/lite/notebooks/index.html?path=exercise_11.ipynb` (no manifest launch
  button exists). 4 tests: untouched-template Run-All-Cells (no error
  cells, data loads, both blanks'/check cells show "Not complete yet",
  both widgets render, the given face-hypothesis example gracefully
  defers), 390px viewport (no overflow, both widgets' labels unclipped —
  uses a locally modified `scrollToVisibleFine` that re-measures
  `scrollHeight` every sweep iteration instead of once up front), reset +
  back-to-contents, and the teacher-completed path (fills all 3 blanks
  with real solutions, confirms every documented number exactly, operates
  both widgets live, answers all 6 questions by option text including one
  deliberate wrong answer per question type, downloads and verifies the
  completed `.ipynb`).

## Modified files

- `requirements.txt` — appended, after the existing `scikit-learn` line:
  ```
  # Maintainer-only, offline-extraction-script dependencies (WP61 Gate A,
  # scripts/export_haxby_rsa_data.py --refresh). Never added to
  # requirements-lite.txt or book/lite/overrides.json: neither has a
  # prebuilt Pyodide wheel, and no student notebook imports either package --
  # the browser kernel only ever loads the small, already-derived CSV export.
  nilearn
  nibabel
  ```
  `requirements-lite.txt` and `book/lite/overrides.json` are both
  untouched.

## Explicitly NOT touched this WP

`book/_toc.yml`, `book/_config.yml`, `book/config/exercise_manifest.json`,
`book/chapters/chapter_11/exercise_11.md` (the placeholder stub),
`book/downloads/chapter_11/` (deliberately left absent — see the report's
"Deviations" section), any file for Exercises 1–10 or 12, and any shared
`interactive/src/*` infrastructure.

## Mid-WP corrections (found by actually running the notebook in a browser)

1. `scripts/generate_exercise_11_notebook.py`, the neural-RDM check cell
   (`wp61-206-rdm-check`): guard changed from `if "neural_rdm" in
   globals():` to `if "neural_rdm" in globals() and not
   np.allclose(neural_rdm, 0.0):` — the untouched starter pre-initializes
   `neural_rdm` to an all-zero matrix (so the student can fill individual
   cells), which was trivially passing the shape/symmetry/diagonal/finite
   checks and printing a false "Looks good".
2. Same file, the face-hypothesis example cell (`wp61-503-face-example`):
   wrapped the entire body in the same `"neural_rdm" in globals() and not
   np.allclose(neural_rdm, 0.0)` guard (previously unguarded, the only
   `neural_rdm`-dependent cell in the notebook without one) — it was
   silently printing `face_match_r = nan` on the untouched template
   instead of the "Not complete yet" message every other dependent cell
   already gives.
3. `requirements.txt`, module docstring's "Outputs" section, and the
   `PORTABLE_PATH`/write-loop in `generate_exercise_11_notebook.py` —
   removed `book/downloads/chapter_11/exercise_11_portable.ipynb` from
   the generator's write targets entirely (originally written, then
   deleted) after discovering
   `tests/test_placeholder_exercises.py::test_no_active_portable_notebook_for_any_placeholder`
   forbids that exact path while Exercise 11 is still the placeholder.
   `tests/test_exercise_11_lite_notebook.py`'s `StructuralSynchronization`
   class was updated to match: `PORTABLE_PATH`/`test_lite_and_portable_are_identical`
   removed, replaced with `test_no_active_downloads_portable_notebook_yet`.
4. `interactive/e2e-book/exercise-11-lite.spec.ts`'s `scrollToVisibleFine`
   helper — changed to re-measure `.jp-WindowedPanel-outer`'s
   `scrollHeight` on every sweep iteration (was measured once, up front),
   fixing an intermittent failure to locate a cell late in this notebook
   whose own figure was still growing the panel's rendered height.
