# WP42 exact changelog

Starting SHA (local `feature/wp41-jupyterlite-course-platform`):
`e95dc516ffcaf6f8095e80dc171807a6d850a659` ("WP41R: reports — execution
report and exact changelog").

Checkpoint branch (pre-work snapshot, same SHA): `checkpoint/wp42-pre-work`.

Feature branch: `feature/wp42-exercise2-polish-exercise1-migration`.

Commits made by this WP, in order:
1. `75ed307` — WP42 Gate 1: polish Exercise 2 (answers, layout, table, KNN
   check, figures, warnings, axis).
2. `467baee` — WP42 Gate 2: migrate Exercise 1 to a JupyterLite-native
   active-learning notebook.
3. This report + this changelog (committed together as this WP's closing
   commit; see `git log -1` after that commit for the final SHA).

No merge, no push, no deployment, no GitHub Actions interaction at any point.

## Full diffstat (checkpoint → final, before this closing commit)

```
45 files changed, 7509 insertions(+), 6611 deletions(-)
```

## Changed files, by commit

### Commit 1 — Gate 1 (Exercise 2 polish)

```
A  WPs/WP42_EXERCISE_2_POLISH_AND_ACTIVE_EXERCISE_1.md
M  book/config/exercise_manifest.json
M  book/downloads/chapter_02/exercise_02_portable.ipynb
A  book/lite/files/data/exercise_02_bias_variance_conceptual.png
M  book/lite/files/exercise_02.ipynb
M  book/lite/files/exercise_02_portable.ipynb
M  interactive/e2e-book/exercise-02-lite.spec.ts
M  interactive/e2e-book/iframe-height-contract.spec.ts
M  interactive/e2e-book/wp22-cross-chapter-dark-mode.spec.ts
M  scripts/generate_exercise_02_notebook.py
A  scripts/render_exercise_02_bias_variance_figure.py
M  scripts/reference_notebooks/exercise_02_reference.ipynb
M  tests/test_exercise_02_lite_notebook.py
M  tests/test_exercise_02_reference_execution.py
M  tests/test_exercise_manifest.py
```

### Commit 2 — Gate 2 (Exercise 1 migration)

```
M  book/_static/launch-buttons.js
M  book/chapters/chapter_01/exercise_01.ipynb
M  book/config/exercise_manifest.json
A  book/lite/files/data/abide_phenotypes.csv
A  book/lite/files/data/abide_phenotypes.manifest.json
A  book/lite/files/exercise_01.ipynb
A  book/lite/files/exercise_01_portable.ipynb
M  book/downloads/chapter_01/exercise_01_portable.ipynb
D  interactive/e2e-book/chapter01-dark-mode.spec.ts
M  interactive/e2e-book/chapter01.spec.ts
A  interactive/e2e-book/exercise-01-lite.spec.ts
M  interactive/e2e-book/iframe-height-contract.spec.ts
M  interactive/e2e-book/launch-buttons.spec.ts
M  scripts/build_portable_notebook.py
A  scripts/export_abide_phenotypes_lite_data.py
A  scripts/generate_exercise_01_notebook.py
A  scripts/generate_exercise_01_transition_page.py
A  scripts/reference_notebooks/exercise_01_reference.ipynb
M  scripts/smoke_portable_notebook.py
D  tests/test_build_portable_notebook.py
A  tests/test_exercise_01_lite_notebook.py
A  tests/test_exercise_01_reference_execution.py
A  tests/test_exercise_01_transition_page.py
M  tests/test_exercise_03_notebook.py
M  tests/test_exercise_06_notebook.py
M  tests/test_exercise_07_notebook.py
M  tests/test_exercise_08_notebook.py
M  tests/test_exercise_09_notebook.py
M  tests/test_exercise_manifest.py
D  tests/test_notebook_corrections.py
M  tests/test_notebook_opening_structure.py
M  tests/test_think_first_shared_class.py
M  tests/test_wp24_content_audit.py
```

## Data/numerical facts introduced or reconciled

- `scripts/generate_exercise_02_notebook.py`: `TEMPLATE_VERSION` bumped
  2 → 3 (real content change); `book/config/exercise_manifest.json`'s
  Exercise 2 `templateVersion` corrected 1 → 3 (was never updated when WP41R
  bumped the notebook's own metadata to 2 — a real, closed gap; see
  `tests/test_exercise_manifest.py::test_migrated_template_versions_match_notebook_metadata`,
  new in this WP, which now enforces this for every migrated exercise).
- `book/lite/files/data/exercise_02_bias_variance_conceptual.png`: new,
  rendered by `scripts/render_exercise_02_bias_variance_figure.py` from no
  data (a fixed schematic, not measured).
- `book/lite/files/data/abide_phenotypes.csv` /
  `abide_phenotypes.manifest.json`: new, 1114 rows × 13 columns, derived
  offline from the already-committed, already-approved
  `book/_static/widgets/data/abide_table_inspection.json` (no network
  fetch; see `scripts/export_abide_phenotypes_lite_data.py`).
- `book/config/exercise_manifest.json`: Exercise 1 `migrationState`
  `"legacy"` → `"migrated"`, `templateVersion` `null` → `1`, Lite fields
  filled in.

## Confirmation

Nothing was merged, pushed, or deployed. No GitHub Actions workflow was
triggered or inspected. `Homework_Materials/` was not touched. No exercise
other than Exercises 1 and 2 was migrated or modified (chapters 3–10
verified unchanged via their own passing `launch-buttons.spec.ts` and
`iframe-height-contract.spec.ts` cases).
