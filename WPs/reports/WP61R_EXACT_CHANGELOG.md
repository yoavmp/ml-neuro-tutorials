# WP61R Exact Changelog — Exercise 11 author revisions

Branch: `feature/wp61-embeddings-and-rsa` (continued). Checkpoint
`71a114d`. Implementation `3e2f6c6`. Not merged, not pushed.

## `scripts/generate_exercise_11_notebook.py` (the bulk of this WP)

- **Module docstring**: dropped the split-half mention from the content
  summary and headline-results list; added a paragraph describing what
  WP61R changed (split-half removal, the two latent-bug fixes applied
  alongside the one WP61 already had); "Outputs" section unchanged.
- **Overview** (`wp61-002-overview`): list item 1 drops
  "ventral-temporal-"; list shrinks from 6 to 5 items (the split-half item
  removed, items 5-6 renumbered to 4-5).
- **Section 1 intro** (`wp61-102-intro`): removed "chosen without
  reference to the face/house comparison... so that comparison is not
  circular"; replaced the raw-scan paragraph with the concise
  already-prepared-part wording + a direct link,
  `[haxby_rsa_patterns.manifest.json](data/haxby_rsa_patterns.manifest.json)`
  (contents-tree-relative; a first attempt using `../files/data/...`,
  reasoned from the page's literal URL, 404'd live — JupyterLab resolves
  and re-serves relative markdown links through its own contents/`/files/`
  mechanism, not the raw page URL).
- **Heatmap intro** (`wp61-104-heatmap-intro`): "Supplied: a heatmap..."
  → "Here we can see a heatmap...", trailing sentence shortened.
- **Heatmap cell** (`wp61-105-heatmap`): added
  `for i in range(1, len(CATEGORIES)): ax.axhline(i - 0.5, color="black", linewidth=0.6)`
  between the `imshow` call and the axis-label calls.
- **New cell `wp61-106-q-row-voxel`**: `show_question("q-row-voxel")`,
  moved here (was `wp61-209-q-row-voxel`, after the Section 2 RDM plot).
- **RDM blank** (`wp61-205-rdm-blank`): "Example shape only" → "Example
  format" in the hint comment.
- **RDM check cell** (`wp61-206-rdm-check`, now also renumbered from the
  removal of `wp61-209`/`210`/`212` below it to `wp61-208`): guard
  unchanged from WP61's own prior fix.
- **RDM plot cell** (now `wp61-208-plot`, was already this id): guard
  condition gains `not np.allclose(neural_rdm, 0.0) and` (consistency fix,
  same bug class as item 10, not explicitly requested but applied for
  consistency).
- **Removed cell** `wp61-209-q-row-voxel` (moved to Section 1, see above).
- **Renamed** `wp61-210-q-rdm-cell` → `wp61-209-q-rdm-cell`;
  `wp61-211-order-note` → `wp61-210-order-note` (content unchanged).
- **Removed cell** `wp61-212-q-condition-order` (the entire cell).
- **MDS cell** (`wp61-303-mds`): guard condition gains
  `not np.allclose(neural_rdm, 0.0) and`; `MDS(...)` call changed from
  `dissimilarity="precomputed", random_state=0` to
  `metric="precomputed", random_state=0, n_init=4, init="random"`.
- **MDS reflection** (`wp61-304-reflection`): removed "(There is no single
  correct answer to predict here; this is a prompt for the written-answer
  cell below.)".
- **Entire function `_section_4_split_half()` deleted** (was
  `wp61-401-header` through `wp61-407-q-split-half`: header, intro md,
  odd/even-pattern given code, instructions md, the blank
  `wp61-405-split-half-blank` tagged `wp61-activity-split-half`, its
  check cell, and `show_question("q-split-half")`).
- **`_section_5_model_comparison()` renamed to
  `_section_4_model_comparison()`**; header text "## 5." → "## 4."; every
  cell id in it renumbered `wp61-50N` → `wp61-40N`
  (402-face-example-intro, 403-face-example, 404-instructions,
  405-animacy-blank, 406-animacy-check, 407-widget-intro, 408-widget);
  model-RDM paragraph trimmed; "Section 5's two predeclared hypotheses" →
  "Section 4's"; animacy blank's "Example shape only" → "Example format".
- **Face-hypothesis example cell** (now `wp61-403-face-example`): no
  content change beyond the id renumber (the all-zero guard was already
  present from WP61).
- **`_section_6_interpret()` renamed to `_section_5_interpret()`**; header
  "## 6." → "## 5."; every cell id renumbered `wp61-60N` → `wp61-50N`
  (502-summary, 503-reflection, 504-q-face-implications,
  505-widget-intro, 506-widget, 507-closing).
- **Summary cell** (now `wp61-502-summary`): removed the split-half
  reliability bullet; trimmed the "why no p-value" paragraph.
- **Distance-metric widget cell** (now `wp61-506-widget`): `_MDS(...)`
  call changed identically to the Section 3 MDS call above
  (`metric="precomputed", ..., n_init=4, init="random"`).
- **Closing cell** (now `wp61-507-closing`): removed the split-half
  "Closing notes" bullet and the entire "Collapsing this notebook's
  question-checking setup... not secure answer protection..." paragraph.
- **`_QUESTIONS` dict**: removed the `"q-condition-order"` and
  `"q-split-half"` entries in full (prompt, options, `correct_index`,
  `feedback_correct`).
- **Setup-cell template** (`SETUP_SOURCE_TEMPLATE`): removed the two
  `warnings.filterwarnings(...)` calls targeting the `dissimilarity`/
  `init` deprecation messages (and their explanatory comment) — no longer
  needed once every `MDS(...)` call sets its parameters explicitly.
- **`_build_cells()`**: drops the `_section_4_split_half()` call; calls
  renamed to `_section_4_model_comparison()`/`_section_5_interpret()`.

Regenerated via `--write`: `book/lite/files/exercise_11.ipynb`,
`book/lite/files/exercise_11_portable.ipynb`,
`scripts/reference_notebooks/exercise_11_reference.ipynb` (40 cells, was
larger before the split-half removal).

## `scripts/export_haxby_rsa_data.py`

- `DATASET_LICENSE` constant rewritten: from the "unknown" statement
  (based only on `nilearn`'s own dataset description) to CC BY-SA 3.0,
  quoting pymvpa.org's own license statement verbatim, noting the
  correction and its reason, and adding a share-alike note for the
  derived export. No other change — extraction logic and every numeric
  constant untouched.

## `book/lite/files/data/haxby_rsa_patterns.manifest.json`

- `dataset.license` field hand-aligned to the new `DATASET_LICENSE` text
  (not regenerated via `--refresh`, to avoid re-downloading the ~300 MB
  raw archive for a text-only change). `derivedFile.sha256` and every
  other field unchanged; confirmed the referenced CSV's own sha256 is
  unchanged and `--check` passes.

## `book/resources.md`

- Added, under "Datasets and data provenance", after the ABIDE course-export
  bullet: a bullet for the Haxby et al. (2001) PyMVPA distribution page
  (with its CC BY-SA 3.0 license noted) and a bullet for this course's own
  `haxby_rsa_patterns.manifest.json`, linked the same way the existing
  ABIDE CSV exports are (`<a href="lite/files/data/...">`).

## `book/references.md`

- Added entry 5: Haxby et al. (2001), *Science* 293(5539):2425-2430, DOI
  link, "Cited in Exercise 11... see Resources for the dataset's own
  distribution page and the course's curated export" — same shape as
  entry 2 (ABIDE II).

## `tests/test_book_structure.py`

- `test_resources_covers_the_required_minimum_links`: added
  `pymvpa.org/datadb/haxby2001.html`,
  `lite/files/data/haxby_rsa_patterns.manifest.json`, and
  `cc by-sa 3.0` to the required-substrings list.
- `test_references_leads_with_the_course_book_and_covers_the_minimum`:
  added `haxby` and `10.1126/science.1063736` to the required-substrings
  list.

## `tests/test_exercise_11_lite_notebook.py`

- `BLANK_TAGS`: removed `"wp61-activity-split-half"`.
- `SINGLE_CHOICE_QUESTION_IDS`: removed `"q-condition-order"`,
  `"q-split-half"`.
- `test_your_code_here_tasks_exist`: expected blank count 3 → 2.
- New `test_example_format_wording_not_example_shape`.
- `test_blanks_contain_no_executable_solution_even_commented`: removed the
  `wp61-activity-split-half` forbidden-fragment entry.
- `test_required_output_names_appear_in_instructions`: removed the
  split-half-instructions assertion block; animacy-instructions id
  `wp61-504-instructions` → `wp61-404-instructions`.
- New `test_split_half_section_is_fully_removed`,
  `test_q_row_voxel_moved_before_category_patterns`.
- `test_checked_questions_use_show_question_with_no_visible_answer_key`:
  expected checked-question count 6 → 4.
- `test_distance_metric_activity_is_notebook_native_and_precomputed`: id
  `wp61-606-widget` → `wp61-506-widget`.
- `test_grouping_activity_is_notebook_native_and_labeled_exploratory` /
  `test_grouping_activity_excludes_scrambled_category`: ids
  `wp61-508-widget` → `wp61-408-widget`, `wp61-507-widget-intro` →
  `wp61-407-widget-intro`.
- New: `test_mds_warnings_fixed_via_explicit_parameters_not_suppression`,
  `test_mds_scatter_cell_guards_against_unfilled_neural_rdm`,
  `test_rdm_plot_cell_also_guards_against_unfilled_neural_rdm`,
  `test_mds_reflection_no_longer_mentions_the_written_answer_prompt`,
  `test_overview_wording_and_no_ventral_temporal_voxel_phrase`,
  `test_manifest_is_linked_directly_from_section_1`,
  `test_heatmap_intro_wording`, `test_heatmap_has_row_boundary_lines`,
  `test_no_secure_answer_protection_paragraph`.

## `tests/test_exercise_11_reference_execution.py`

- Removed `test_split_half_reliability_matches_direct_verification`;
  added `test_split_half_section_removed_no_leftover_names` and
  `test_no_mds_future_warning_anywhere` (re-executes the notebook with
  `warnings.catch_warnings(record=True)` and asserts no `n_init`-mentioning
  warning fired).
- `test_question_shuffle_is_reproducible_and_varies_by_question`: question
  id list drops `"q-condition-order"`, `"q-split-half"`.

## `interactive/e2e-book/exercise-11-lite.spec.ts`

- Removed `SPLIT_HALF_PROMPT`/`SPLIT_HALF_CORRECT`/`SPLIT_HALF_SOLUTION`,
  `CONDITION_ORDER_PROMPT`/`CONDITION_ORDER_CORRECT`.
- Added `MDS_WRONG` constant and `MDS_WARNING_NEEDLES` +
  `assertCellOutputHasNoMdsWarning()` helper.
- Untouched-template "Run All Cells" test: removed the
  `odd_rdm, even_rdm, split_half_r` "Not complete yet" check from the
  anchor loop; added two `assertCellOutputHasNoMdsWarning` calls (the
  given MDS cell and the distance-metric widget cell).
- Teacher-completed-path test: removed the entire split-half
  fill-blank/check block; added `assertCellOutputHasNoMdsWarning` calls
  after the Section 3 MDS re-run and after selecting each distance-metric
  dropdown option (now exercises both options, previously only one); the
  three-item single-choice loop drops `CONDITION_ORDER_PROMPT`, keeps
  `ROW_VOXEL`/`RDM_CELL`/`MDS`; the "deliberately wrong" single-choice
  check switched from `CONDITION_ORDER_PROMPT` to `MDS_PROMPT` (answered
  with `MDS_WRONG`), since the condition-order question no longer exists.

## Exercises 8 and 9 (item 14's search)

- `scripts/generate_exercise_08_notebook.py`: removed the "Collapsing
  this notebook's question-checking setup... not secure answer
  protection..." paragraph from cell `wp47-602-summary`. Nothing else in
  the cell or file changed.
- `scripts/generate_exercise_09_notebook.py`: removed the identical
  paragraph from cell `wp51-605-summary`. Nothing else changed.
- Regenerated via `--write`: `book/lite/files/exercise_08.ipynb`,
  `book/lite/files/exercise_08_portable.ipynb`,
  `book/downloads/chapter_08/exercise_08_portable.ipynb`,
  `scripts/reference_notebooks/exercise_08_reference.ipynb`;
  `book/lite/files/exercise_09.ipynb`,
  `book/lite/files/exercise_09_portable.ipynb`,
  `book/downloads/chapter_09/exercise_09_portable.ipynb`,
  `scripts/reference_notebooks/exercise_09_reference.ipynb`. Each diff
  confirmed to be exactly the one paragraph's removal (`git diff --stat`:
  6 deletions for Exercise 8's three identical copies + reference, 8
  lines changed for Exercise 9's — portable/lite differ by one blank-line
  context line).

## Explicitly NOT touched this WP

`book/_toc.yml`, `book/_config.yml`, `book/config/exercise_manifest.json`,
`book/chapters/chapter_11/exercise_11.md`, `book/downloads/chapter_11/`
(still absent, per WP61's own placeholder-guard finding), Exercises
1-3/5-7/10/12 and their generators/tests (confirmed, by the item-14
search, to carry nothing matching the removed paragraph), and any shared
`interactive/src/*` infrastructure.
