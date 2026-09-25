# WP39 — Exact Changelog

Deployment-only work package. WP39 itself changed nothing in `book/`, `interactive/`, `scripts/`,
or `tests/` — every file under those trees that reached `origin/main` in this release was already
authored and reviewed by WP38/WP38R. This changelog records exactly what WP39 *did*: the checkpoint
it added, the merge/push/deploy sequence it ran, and the two report files it produced.

---

## 1. Files added by WP39

- `WPs/WP39_DEPLOY_EXERCISE_10.md` — the WP39 specification itself, committed as the deployment
  checkpoint on `fix/wp38r-exercise10-review`.
- `WPs/reports/WP39_DEPLOYMENT_REPORT.md` — this WP's execution report (committed on `main` after
  the deployment attempt completed).
- `WPs/reports/WP39_EXACT_CHANGELOG.md` — this file.

No other file was created, edited, or deleted by WP39.

---

## 2. Commit-by-commit

### 2.1 On `fix/wp38r-exercise10-review`

| Commit | Message | Contents |
|---|---|---|
| `16e8291fe8eea049fe125ec128786f7716a0d4b7` | `WP39: add specification (deployment checkpoint)` | Adds `WPs/WP39_DEPLOY_EXERCISE_10.md` only (342 insertions, 0 deletions). Committed after all Section 1 starting-state checks passed and before any validation gate ran. |

### 2.2 On `main`

| Commit | Message | Contents |
|---|---|---|
| `58ed1c61f43f0b3c6d23c1f32212bf2d3b9c9f0b` (**`RELEASE_SHA`**) | `Merge Exercise 10 course materials` | `git merge --no-ff fix/wp38r-exercise10-review`. 72 files changed, 25,909 insertions(+), 53 deletions(-). Tree proven identical to the WP39 checkpoint tree (`d33bc5681607f11ae709b507bdc173883c7e95d3`) via empty `git diff` and empty `git diff-tree -r`. Pushed to `origin/main` as the sole push of this WP (`f792ad5..58ed1c6`). |
| *(pending, documentation-only, not pushed)* | `WP39: reports — deployment execution report and exact changelog` | Adds `WPs/reports/WP39_DEPLOYMENT_REPORT.md` and `WPs/reports/WP39_EXACT_CHANGELOG.md`. Committed locally on `main` after production verification completed. **Not pushed** — pushing it would trigger another deployment run for a documentation-only change, which WP39 §8 explicitly disallows. |

---

## 3. Merged content summary (for reference — authored by WP38/WP38R, not WP39)

The 72 files the merge commit brought into `main` (see `WPs/reports/WP38_EXACT_CHANGELOG.md` and
`WPs/reports/WP38R_EXACT_CHANGELOG.md` for their own authorship record):

- `book/chapters/chapter_10/exercise_10.ipynb` (new canonical notebook) and
  `book/chapters/chapter_10/exercise_10.md` (deleted — placeholder replaced by the notebook).
- `book/downloads/chapter_10/exercise_10_portable.ipynb` (new portable notebook, 11,003 lines).
- Widget configs/data for four Exercise 10 activities: `leakage_quiz`, `leakage_lab`,
  `har_fold_compare`, `class_balance_compare` (`book/_static/widgets/configs/*.json`,
  `book/_static/widgets/data/*.json`).
- `book/data/uci_har/uci_har_compact.csv.gz` + `provenance.json` (new UCI HAR dataset subset).
- `book/config/abide_modeling.json` (extended with the `leakage_lab` manifest entry).
- Shared infrastructure fixes: `book/_static/activity-resize.js`, `book/_static/launch-buttons.js`,
  `interactive/src/resize-report.ts` (the strengthened iframe-height contract WP38R introduced).
- New `interactive/src/` modules: `class-balance-compare-data.ts`, `classification-metrics.ts`,
  `har-fold-compare-data.ts`, `leakage-lab-data.ts`, `leakage-quiz-data.ts`, and their four
  `components/*.ts` counterparts, plus a `config.ts` update and `registry.ts` registration.
- New `interactive/tests/*.test.ts` (4 files) and `interactive/e2e/*.spec.ts` (5 files) covering
  the above.
- New `interactive/e2e-book/chapter10.spec.ts`; updated `iframe-height-contract.spec.ts` and
  `launch-buttons.spec.ts` to include Chapter 10.
- New `scripts/`: `export_class_balance_compare_data.py`, `export_har_fold_widget_data.py`,
  `export_leakage_lab_data.py`, `export_uci_har_data.py`, `har_group_leakage_audit.py` (+ its
  committed result JSON), `uci_har_data.py`, and a `smoke_portable_notebook.py` update; plus a
  `build_portable_notebook.py` update to register Chapter 10.
- New `tests/`: `test_exercise_10_notebook.py`, `test_export_class_balance_compare_data.py`,
  `test_export_har_fold_widget_data.py`, `test_export_leakage_lab_data.py`,
  `test_har_group_leakage_audit.py`, `test_uci_har_data.py`.
- Mechanical renumbering-only updates (10-12 placeholder range → 11-12) in
  `tests/test_book_structure.py`, `tests/test_exercise_04_notebook.py`,
  `tests/test_exercise_06_notebook.py`, `tests/test_exercise_07_notebook.py`,
  `tests/test_exercise_08_notebook.py`, `tests/test_exercise_09_notebook.py`,
  `tests/test_placeholder_exercises.py`, `tests/test_wp25_content_audit.py`.
- WP38/WP38R specification and report documentation under `WPs/` and `WPs/reports/`.

`book/syllabus.md` and `course_overview/*` are **not** in this list — confirmed unchanged by both
WP39 §1 (pre-merge) and WP39 §7 (post-deployment, against the previously deployed release).

---

## 4. Net repository state after WP39

- `origin/main` = `RELEASE_SHA` = `58ed1c61f43f0b3c6d23c1f32212bf2d3b9c9f0b`.
- Local `main` = `RELEASE_SHA` + one unpushed documentation-only commit (this report + this
  changelog).
- `fix/wp38r-exercise10-review` unchanged since its WP39 checkpoint (`16e8291f...`) — not deleted,
  not force-pushed, not rebased.
- No other branch, tag, or ref was created, modified, or deleted.
