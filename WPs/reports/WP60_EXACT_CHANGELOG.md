# WP60 exact changelog

Starting SHA (local `main`): `65d52a5` ("WP59 report: Exercise 10 wording
fixes, release, and live verification"), matching `origin/main`.

Feature branch: `feature/wp60-swap-exercises-3-4`, branched from that SHA.

Commits made by this WP, in order:
1. `6d6f2c8` — swap Exercise 3 and Exercise 4's subjects.
2. `c7aae28` — review corrections: clean student-visible display (the
   `v2/` subdirectory fix), Exercise 5's prerequisite, and a full
   cross-reference audit across six more generators and five more
   audit/export scripts.
3. `4b2797b` — report update: `wp22-cross-chapter-dark-mode.spec.ts`
   evidence (clean titles confirmed from a third, independent test file;
   the local machine's slowness during review, not a regression).
4. Merge commit `b479b89` on `main` — fast-forward-clean merge of the
   feature branch (no conflicts).
5. `5a4144b` — upgrade `zod` 3.23.8 → 4.6.7 (unblocks the first CI
   failure: a newly published security advisory, unrelated to this WP).
6. `3e24c5d` — upgrade `@playwright/test` 1.55.1 → 1.64.1 (unblocks the
   second CI failure: GitHub's runner image moved to Ubuntu 26.04).
7. `c453776` — fix Exercise 3/4's data-loading relative path, and the
   offline test harness's matching `os.chdir` target, and
   `warning-sweep.spec.ts`'s stale flat-path URL construction (unblocks
   the third CI failure: the one real bug this WP introduced).
8. `797f2ce` — fix an author-facing WP-number reference that leaked into
   both portable notebooks' cell content as part of commit 7's own fix
   (unblocks the fourth CI failure).
9. This report + this changelog (committed together as this WP's closing
   commit; see `git log -1` after that commit for the final SHA).

**Pushed to `main` five times (the merge itself, then commits 5–8, each
directly after the previous push's CI failure); CI run
[41184047532](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/41184047532)
on commit 8 (`797f2ce`) succeeded in full, including "Publish website."
Deployed SHA: `797f2ce` (`797f2cea8f80dc99e2fb6512f620e142be3fc6f0`).**

## Changed/added/deleted files, commit 1 (`6d6f2c8`)

```
A  WPs/reports/WP60_REPORT.md
M  book/_config.yml
M  book/chapters/chapter_03/exercise_03.ipynb
M  book/chapters/chapter_04/exercise_04.ipynb
M  book/config/abide_modeling.json
M  book/config/exercise_manifest.json
M  book/downloads/chapter_03/exercise_03_portable.ipynb
M  book/downloads/chapter_04/exercise_04_portable.ipynb
R  book/lite/files/data/exercise_04_nested_cv_diagram.png -> book/lite/files/data/exercise_03_nested_cv_diagram.png
M  book/lite/files/exercise_03_portable.ipynb
R  book/lite/files/exercise_04.ipynb -> book/lite/files/exercise_03_v2.ipynb
M  book/lite/files/exercise_04_portable.ipynb
R  book/lite/files/exercise_03.ipynb -> book/lite/files/exercise_04_v2.ipynb
M  interactive/e2e-book/chapter03.spec.ts
M  interactive/e2e-book/chapter04.spec.ts
M  interactive/e2e-book/exercise-03-lite.spec.ts
M  interactive/e2e-book/exercise-04-lite.spec.ts
M  interactive/e2e-book/wp22-cross-chapter-dark-mode.spec.ts
M  scripts/decision_tree_model_audit.py
M  scripts/decision_tree_model_audit_result.json
M  scripts/export_wp27_widget_data.py
M  scripts/generate_exercise_03_notebook.py
M  scripts/generate_exercise_03_transition_page.py
M  scripts/generate_exercise_04_notebook.py
M  scripts/generate_exercise_04_transition_page.py
M  scripts/reference_notebooks/exercise_03_reference.ipynb
M  scripts/reference_notebooks/exercise_04_reference.ipynb
R  scripts/render_exercise_04_nested_cv_diagram.py -> scripts/render_exercise_03_nested_cv_diagram.py
M  scripts/wp27_validation_audit.py
M  tests/test_decision_tree_model_audit.py
M  tests/test_deploy_dependency_contract.py
M  tests/test_exercise_03_lite_notebook.py
M  tests/test_exercise_03_reference_execution.py
M  tests/test_exercise_03_transition_page.py
M  tests/test_exercise_04_lite_notebook.py
M  tests/test_exercise_04_reference_execution.py
M  tests/test_exercise_04_transition_page.py
M  tests/test_wp19_content_audit.py
M  tests/test_wp24_content_audit.py
M  tests/test_wp25_content_audit.py
M  tests/test_wp27_validation_audit.py
```

## Changed/added/deleted files, commit 2 (`c7aae28`)

```
M  WPs/reports/WP60_REPORT.md
M  book/chapters/chapter_03/exercise_03.ipynb
M  book/chapters/chapter_04/exercise_04.ipynb
M  book/config/exercise_manifest.json
M  book/downloads/chapter_05/exercise_05_portable.ipynb
M  book/downloads/chapter_06/exercise_06_portable.ipynb
M  book/downloads/chapter_09/exercise_09_portable.ipynb
M  book/downloads/chapter_10/exercise_10_deep_learning_portable.ipynb
M  book/downloads/chapter_12/exercise_12_portable.ipynb
M  book/lite/files/exercise_05.ipynb
M  book/lite/files/exercise_05_portable.ipynb
M  book/lite/files/exercise_06.ipynb
M  book/lite/files/exercise_06_portable.ipynb
M  book/lite/files/exercise_09.ipynb
M  book/lite/files/exercise_09_portable.ipynb
M  book/lite/files/exercise_12.ipynb
M  book/lite/files/exercise_12_portable.ipynb
R  book/lite/files/exercise_03_v2.ipynb -> book/lite/files/v2/exercise_03.ipynb
R  book/lite/files/exercise_04_v2.ipynb -> book/lite/files/v2/exercise_04.ipynb
M  interactive/e2e-book/chapter03.spec.ts
M  interactive/e2e-book/chapter04.spec.ts
M  interactive/e2e-book/exercise-03-lite.spec.ts
M  interactive/e2e-book/exercise-04-lite.spec.ts
M  interactive/e2e-book/wp22-cross-chapter-dark-mode.spec.ts
M  scripts/advanced_models_audit.py
M  scripts/advanced_models_audit_result.json
M  scripts/classification_model_audit.py
M  scripts/export_class_balance_compare_data.py
M  scripts/export_classification_imbalance_data.py
M  scripts/export_classification_threshold_data.py
M  scripts/export_regularization_widget.py
M  scripts/generate_exercise_03_notebook.py
M  scripts/generate_exercise_03_transition_page.py
M  scripts/generate_exercise_04_notebook.py
M  scripts/generate_exercise_04_transition_page.py
M  scripts/generate_exercise_05_notebook.py
M  scripts/generate_exercise_06_notebook.py
M  scripts/generate_exercise_09_notebook.py
M  scripts/generate_exercise_10_deep_learning_notebook.py
M  scripts/generate_exercise_12_notebook.py
M  scripts/reference_notebooks/exercise_05_reference.ipynb
M  scripts/reference_notebooks/exercise_06_reference.ipynb
M  scripts/reference_notebooks/exercise_09_reference.ipynb
M  scripts/reference_notebooks/exercise_10_deep_learning_reference.ipynb
M  scripts/reference_notebooks/exercise_12_reference.ipynb
M  scripts/regularization_model_audit.py
M  tests/test_exercise_03_lite_notebook.py
M  tests/test_exercise_03_transition_page.py
M  tests/test_exercise_04_lite_notebook.py
M  tests/test_exercise_04_transition_page.py
M  tests/test_exercise_10_deep_learning_notebook.py
M  tests/test_wp24_content_audit.py
```

## Changed/added/deleted files, commit 3 (`4b2797b`)

```
M  WPs/reports/WP60_REPORT.md
```

## Changed/added/deleted files, commit 5 (`5a4144b`, first post-merge push)

```
M  interactive/package-lock.json
M  interactive/package.json
M  interactive/src/binary-asset.ts
M  interactive/src/correlation-data.ts
M  interactive/src/har-fold-compare-data.ts
M  interactive/src/histogram-data.ts
M  interactive/src/nested-cv-explorer-data.ts
M  interactive/src/regression-compare-data.ts
M  interactive/src/retention-data.ts
M  interactive/src/table-inspection-data.ts
M  interactive/src/validation-stability-data.ts
```

## Changed/added/deleted files, commit 6 (`3e24c5d`)

```
M  interactive/package-lock.json
M  interactive/package.json
```

## Changed/added/deleted files, commit 7 (`c453776`)

```
M  book/downloads/chapter_03/exercise_03_portable.ipynb
M  book/downloads/chapter_04/exercise_04_portable.ipynb
M  book/lite/files/exercise_03_portable.ipynb
M  book/lite/files/exercise_04_portable.ipynb
M  book/lite/files/v2/exercise_03.ipynb
M  book/lite/files/v2/exercise_04.ipynb
M  interactive/e2e-book/warning-sweep.spec.ts
M  scripts/generate_exercise_03_notebook.py
M  scripts/generate_exercise_04_notebook.py
M  scripts/reference_notebooks/exercise_03_reference.ipynb
M  scripts/reference_notebooks/exercise_04_reference.ipynb
M  tests/test_exercise_03_reference_execution.py
M  tests/test_exercise_04_reference_execution.py
```

## Changed/added/deleted files, commit 8 (`797f2ce`, deployed SHA)

```
M  book/downloads/chapter_03/exercise_03_portable.ipynb
M  book/downloads/chapter_04/exercise_04_portable.ipynb
M  book/lite/files/exercise_03_portable.ipynb
M  book/lite/files/exercise_04_portable.ipynb
M  book/lite/files/v2/exercise_03.ipynb
M  book/lite/files/v2/exercise_04.ipynb
M  scripts/generate_exercise_03_notebook.py
M  scripts/generate_exercise_04_notebook.py
M  scripts/reference_notebooks/exercise_03_reference.ipynb
M  scripts/reference_notebooks/exercise_04_reference.ipynb
```

## CI runs against this WP's commits on `main`

Five runs total, confirmed from `gh run list` directly (not reconstructed
from memory): the merge itself got its own run before any fix commit
existed.

| Push | Head SHA | Run | Result | Failing step |
|---|---|---|---|---|
| 0 (merge) | `b479b89` | [41057263393](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/41057263393) | failure | Audit production frontend dependencies (zod advisory) |
| 1 | `5a4144b` | [41063647241](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/41063647241) | failure | Install Playwright Chromium (ubuntu26.04-x64) |
| 2 | `3e24c5d` | [41076485535](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/41076485535) | failure | End-to-end test the combined book + JupyterLite build — every Exercise 3/4 test, only those |
| 3 | `c453776` | [41114418441](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/41114418441) | failure | Unit-test the Python scripts (`test_wp35_content_audit`) |
| 4 | `797f2ce` | [41184047532](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/41184047532) | **success** | — (Publish website ran) |

A companion, non-blocking workflow ("Legacy notebook smoke test (Exercise
10)") also ran against `b479b89` (triggered because
`book/downloads/chapter_10/**` changed in commit 2's regeneration pass)
and succeeded — unrelated to this WP's own gate.
