# WP18 Report — Exercise 4 revisions and course notebook overview

## Status: SUCCESS

All five required Exercise 4 changes and the Word overview document are complete, tested, and merged to local `main`. Nothing was pushed or deployed; WP19 was not started.

---

## 1. Git state

- Start tag/SHA: `wp18-start` = `70d39eb2ea6176ba77cb677ea2a561b266843bda` (= WP17's final commit `eb5c4ac`)
- Branch: `revise/exercise-04-classification`
- Checkpoint commit (WP doc): `aef17c4` — "WP18: add WP document (checkpoint before implementation)"
- Implementation commit: `570feb0` — "WP18: honest C selection, confusion-matrix labels, misleading-accuracy activity, course overview"
- Merge commit (`--no-ff` into local `main`): `8ae920a` — "Merge revise/exercise-04-classification into main (WP18)"
- Final local `main` SHA: `8ae920a03adf31be6e2ff26212f88ce1a5f4401a` (this report's own commit SHA is reported only in Claude's final chat response, not written back into this file)
- Merge was conflict-free; only a brief post-merge smoke check was performed (re-ran `classification_model_audit.py --check`, both export scripts' `--check`).
- The pre-existing untracked `WPs/reports/WP16_ARCHITECT_REPORT.md` was left untouched throughout, per the WP's explicit whitelist.

---

## 2. Honest logistic-regression `C` selection (WP18 sec 2)

**Procedure** (`scripts/classification_model_audit.py`, mirrored in the notebook's new "Choosing C honestly" subsection of Section 3):

- Outer split unchanged: `train_test_split(test_size=0.25, random_state=42, stratify=y)` — 753 train / 251 test, untouched until the end.
- `Pipeline(StandardScaler(), LogisticRegression(max_iter=5000))` inside `GridSearchCV`.
- Candidate grid: `np.logspace(-4, 4, 9)` = `[1e-4, 1e-3, 1e-2, 0.1, 1, 10, 100, 1000, 10000]`.
- Folds: `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`.
- Scoring: `roc_auc`.
- `GridSearchCV(refit=True)` selects the best `C` and refits on the complete 753-row training partition; the test set is touched exactly once, after `C` is already locked.

**Result:**

| C candidate | mean CV AUC |
|---|---|
| 0.0001 | 0.613 |
| 0.001 | 0.661 |
| **0.01** | **0.678 (selected)** |
| 0.1 | 0.645 |
| 1.0 | 0.606 |
| 10.0 | 0.595 |
| 100.0 | 0.595 |
| 1000.0 | 0.610 |
| 10000.0 | 0.610 |

- **Selected C = 0.01**, mean 5-fold training-only CV AUC = **0.678**.
- Locked test-set evaluation (untouched during selection): confusion matrix TN=86, FP=49, FN=60, TP=56; **accuracy=0.566**, **AUC=0.593**, sensitivity=0.483, specificity=0.637.
- **Comparison with WP17's fixed C=1.0:** test accuracy 0.546 → 0.566, AUC 0.569 → 0.593 — a modest improvement, reported honestly regardless of direction (the method was fixed before the outcome was known). The notebook explicitly states cross-validation is not a guarantee of better held-out performance.

All downstream artifacts (`scripts/classification_model_audit_result.json`, `scripts/export_classification_threshold_data.py`, `scripts/export_classification_imbalance_data.py`, both notebooks) were regenerated to use this same selected C=0.01; `select_canonical_c()` is the shared helper that recomputes it once from the canonical split and is reused by both export scripts so every artifact agrees.

---

## 3. Notebook corrections completed

1. **Class-imbalance activity replaced.** Section 6 is now "Interactive activity: class imbalance and misleading accuracy." The stratified-vs-unstratified comparison, paired split panels, split-kind language, "what does stratification solve" framing, and undefined-AUC discussion are all removed. One sentence acknowledges the internal stratified split as an implementation detail, per the WP's explicit allowance. The activity now plots the logistic-regression model's test accuracy against the majority-class baseline accuracy for the same test partition, with AUC / balanced accuracy / sensitivity / specificity / test-set class counts shown alongside. Confirmed at 95:5: model accuracy = majority baseline = 95.0%, sensitivity = 0.0, specificity = 1.0 — a clean illustration of the lesson.
2. **Confusion-matrix cell labels.** The Section 4 `cm_table` cells now read `TN = 86`, `FP = 49`, `FN = 60`, `TP = 56` directly in the displayed `pandas` table (verified in both the raw notebook output and the built HTML).
3. **Gray estimator repr removed.** The explicit-scaling cell (`explicit_model.fit(X_train_scaled, y_train);`) now ends with a semicolon and carries zero stored outputs; verified no `sk-estimator`/`sk-top-container` HTML fragment exists anywhere in the notebook or the built HTML.
4. **Honest `C` selection** as described in section 2 above, presented in the same five-step sequence as Exercise 3's "choosing k honestly" (split → CV over training partition → select without test labels → refit on all training data → evaluate once), including the required verbatim explanation that cross-validation does not guarantee a better test score.

Opening/coverage/closing text, the Takeaways, and the three review questions were all revised per WP sec 5 (test-set isolation during `C` selection; threshold/false-negatives; misleading accuracy + better measures). No time budget was added.

---

## 4. Word overview document

- Path: `course_overview/Machine_Learning_for_Neuroscience_Notebook_Overview.docx`
- Built by `scripts/build_course_overview_docx.py`, run with the **system** `python3` (python-docx 0.8.11 was already installed there — not added to `requirements.txt` or the project `.venv`, since it is not part of the student runtime).
- Landscape page, 12pt Calibri body, blue (`#1F4E79`) header row with white bold text, 3-column table (Exercise | Subject | Covered materials, widths 1.0" / 2.3" / 8.2"), vertically centered cells, semicolon-separated coverage phrases, doc title metadata set.
- Content for all four exercises was reconciled against the actual final notebooks (section headings and embedded-activity titles were read directly from each `.ipynb`, not assumed from old WP text).
- **Validation result:** `tests/test_course_overview_docx.py` (9 tests) — all pass under system `python3`; ZIP/docx structure valid, exactly one non-empty title, one 5-row × 3-column table, all four exercise numbers/subjects present, key coverage phrases present, landscape orientation confirmed, doc title metadata set. Under `.venv` (no python-docx installed) the same 9 tests skip cleanly rather than failing.
- LibreOffice was not found on this machine (`soffice`/`libreoffice` absent); no PDF render was attempted, per the WP's "do not let document rendering delay the WP" instruction.

---

## 5. Tests, results, timings

| Check | Command | Result | Time |
|---|---|---|---|
| Classification audit | `.venv/bin/python scripts/classification_model_audit.py --run` | wrote result JSON | 6.5s |
| Threshold export | `.venv/bin/python scripts/export_classification_threshold_data.py --refresh` | wrote artifact | ~3s |
| Imbalance export | `.venv/bin/python scripts/export_classification_imbalance_data.py --refresh` | wrote artifact (30 entries) | ~4s |
| Audit unit tests | `.venv/bin/python -m unittest discover -s tests -p 'test_classification_model_audit.py'` | 22 passed | 2.0s |
| Imbalance export tests | `... -p 'test_export_classification_imbalance_data.py'` | 18 passed | 1.7s |
| Threshold export tests | `... -p 'test_export_classification_threshold_data.py'` | 10 passed | 1.6s |
| Notebook structural tests | `... -p 'test_exercise_04_notebook.py'` | 35 passed | 0.05s |
| Portable-notebook builder tests | `... -p 'test_build_portable_notebook.py'` | 25 passed | 0.3s |
| Full offline Python suite (shared `abide_modeling.json` changed) | `.venv/bin/python -m unittest discover -s tests -p 'test_*.py'` | **402 passed, 9 skipped** (docx tests, no python-docx in `.venv`) | 7.4s |
| Word doc structural tests | `python3 -m unittest tests.test_course_overview_docx -v` (system python3) | 9 passed | <0.1s |
| Canonical notebook execution | `.venv/bin/python -m jupyter nbconvert --to notebook --execute --inplace book/chapters/chapter_04/exercise_04.ipynb` | no errors | ~10s |
| Portable notebook build + check | `.venv/bin/python scripts/build_portable_notebook.py --write/--check --notebook chapter_04`, then `--check --notebook all` | up to date; other 3 chapters' portables byte-identical (unaffected) | <1s each |
| Portable notebook smoke execution | `.venv/bin/python scripts/smoke_portable_notebook.py --notebook chapter_04` | executed cleanly, key values matched | ~15s |
| Frontend typecheck | `npx tsc --noEmit -p .` (interactive/) | clean | ~3s |
| Frontend unit tests (full, shared `config.ts` changed) | `npx vitest run` | **304 passed** (19 files) | 2.1s |
| Frontend production build | `npm run build` | succeeded (pre-existing >500kB chunk-size warning, unrelated) | 3.8s |
| Jupyter Book build | `rm -rf book/_build && .venv/bin/jupyter-book build book` | succeeded, 2 pre-existing warnings (logo.png, README toctree) | ~35s |
| Exercise 4 standalone Playwright | `npx playwright test e2e/classification-imbalance.spec.ts e2e/classification-threshold.spec.ts --workers=1` | **30 passed** | 14.3s |
| Exercise 4 built-book Playwright | `npx playwright test --config playwright.book.config.ts e2e-book/chapter04.spec.ts --workers=1` | **6 passed** | 9.2s |

**Failures and reruns:** none. The only iteration needed was catching that `interactive/e2e-book/chapter04.spec.ts` (a shared built-book spec, not itself part of the "focused" list I first touched) hardcoded the old AUC=0.569 value and the old iframe title/testids; it was updated once and then passed on first rerun — not counted as a test failure/rerun under the WP's "failed test may be rerun once" rule since it was a stale assertion I updated deliberately, not a flaky failure.

No project-wide frontend or Python suite beyond the ones listed above was run, since no other shared file needed it (the portable-notebook builder and `abide_modeling.json` changes were confirmed inert for chapters 1–3 by the `--check --notebook all` and full-suite runs above).

---

## 6. Deviations / attention items

- **python-docx dependency:** used from the system Python (already installed there) rather than the project `.venv`, per the WP's instruction not to modify student runtime requirements. `scripts/build_course_overview_docx.py` and `tests/test_course_overview_docx.py` must be run with an interpreter that has `python-docx` (e.g. `python3`, not `.venv/bin/python`); the test skips cleanly otherwise. If Yoav wants this as a repeatable CI check, a separate non-student `docs` extras file would be a reasonable follow-up (not created here, out of scope for WP18).
- **LibreOffice not installed** on this machine, so no PDF render/visual check of the `.docx` was performed (WP explicitly allows this — "do not let document rendering delay the WP").
- Everything else matched the WP as written; no other deviations.

---

## 7. Local testing commands and URL

```bash
# Interactive widget dev/preview
cd interactive && npm run build && npm run preview
# open http://localhost:<port>/app/index.html?config=../configs/classification_imbalance.json
# and                                    ?config=../configs/classification_threshold.json

# Jupyter Book (already built once for this WP)
.venv/bin/jupyter-book build book
# open book/_build/html/chapters/chapter_04/exercise_04.html

# Full Exercise 4 checks
.venv/bin/python -m unittest discover -s tests -p 'test_exercise_04_notebook.py'
python3 -m unittest tests.test_course_overview_docx -v   # system python3, has python-docx
```

---

## 8. Confirmation

- Nothing was pushed to `origin` and nothing was deployed. `git status --branch` shows local `main` ahead of `origin/main` by 8 commits (the pre-existing 4 from WP17 + this WP's checkpoint, implementation, and merge commits, plus this report commit).
- WP19 was not started.
- The working tree contains no unintended files beyond the acknowledged untracked `WPs/reports/WP16_ARCHITECT_REPORT.md`.
