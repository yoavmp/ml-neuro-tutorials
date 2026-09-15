# WP17 Report — Exercise 4: Classification with Logistic Regression

**SUCCESS — implemented and validated locally.**

---

## Start / end state

- Expected WP16 starting point (per WP17 §1): `a57fefc01fa63e67805afb3db64b74507b36133f`.
- Actual starting SHA, confirmed intentional by Yoav in this session: `c5aa2ca1f32a5cdf2b8547e51310f531d8622f04`
  (`main`/`origin/main` consistent), one commit ahead of the WP's documented
  reference and tagged `wp17-start`.
- `WPs/reports/WP16_ARCHITECT_REPORT.md` — acknowledged pre-existing
  untracked file, per Yoav's explicit instruction: never touched, still
  untracked.
- Branch: `feature/exercise-04-classification`, created from `wp17-start`.
- Implementation commit: `ed7d053` on the feature branch.
- Merge commit: `2da4086` (`--no-ff`) on local `main`.
- **Final local `main` SHA: `2da40863e75d158481636e88f84f4ad56b162e37`.**
- Local `main` is 3 commits ahead of `origin/main` (WP doc checkpoint,
  implementation, merge) — **not pushed**.

## Data audit results and diagnosis coding

- Source: `abide2.tsv` (pinned commit `e4eed3c4d...`, SHA-256 verified),
  1004 participants x 1446 columns, identical source Exercises 2-3 use.
- Diagnosis column: **`group`**, native to `abide2.tsv` (no join needed).
  Coding: `1.0` = autism, `2.0` = control (`cohort.group_codes` in the
  manifest). Recoded in the notebook/audit to `y = 1` (autism, positive
  class) / `y = 0` (control, negative class).
- Usable participants: **463 autism, 541 control**, 1004 total. 0 missing
  `group` values, 0 duplicate `subject` ids. Each row is one participant
  (same guarantee `load_modeling_frame()` already enforces for Exercises
  2-3).
- Feature columns: the exact same 360 bilateral cortical-thickness (`fsCT_*`)
  columns as Exercises 2-3's canonical recipe (`all-eligible x CT`), 0
  missing cells (per the reviewed manifest).
- No duplicate participant ids; no diagnosis-derived, id, age, sex, site, or
  behavioural-score column entered `X` (enforced by `assert_brain_only`,
  which also treats `group` itself as forbidden in `X`).

## Exact feature definition

```python
FEATURES = [c for c in BRAIN_COLS if c.startswith("fsCT_")]
```
360 columns, identical derivation to Exercises 2-3's Section 2 recipe cell.

## Model / split / preprocessing specification

- Positive class: autism (`group == 1`). Negative class: control.
- Split: `train_test_split(X, y, test_size=0.25, random_state=42,
  stratify=y)` — the project-standard seed, participant-level,
  stratified by the diagnosis label itself (not a covariate, since `y` is
  diagnosis here). This is **not** the same 753/251 row partition as
  Exercises 2-3 (the split target changed), though it happens to produce
  the same sizes (1004 rows, 0.25 test fraction, no missing `group`).
- Preprocessing: `StandardScaler` fit on training rows only (verified: the
  scaler's `fit_transform` never touches `X_test`).
- Model: `LogisticRegression(C=1.0, max_iter=5000)`, fixed C, not tuned on
  the test set, no feature/seed/model selection performed to improve the
  reported result.
- No imputation was needed (0 missing values in the 360 features or in
  `group`).

## Honest held-out results (`scripts/classification_model_audit_result.json`)

- n_train = 753, n_test = 251 (test: 116 autism, 135 control).
- Confusion matrix (rows = actual, columns = predicted; autism positive):
  TN = 75, FP = 60, FN = 54, TP = 62.
- **Accuracy = 0.546. AUC = 0.569.** Sensitivity = 0.534. Specificity = 0.556.
- Discrimination is modest, reported as such in the notebook and this
  report — not dressed up. Re-fitting the identical pipeline on the
  identical split twice produced byte-identical metrics (reproducibility
  check passed).
- The notebook states explicitly that this split estimates generalisation
  to new participants from the same 17 ABIDE-II sites, not to an unseen
  acquisition site.

## Imbalance-activity cohort size and why it was chosen

Fixed cohort size **N = 400**, drawn once per ratio (real participants,
without replacement, deterministic per-ratio seed), documented in
`book/config/abide_modeling.json` (`classification.imbalance_activity`).
Rationale: at every ratio from 50:50 through 95:5, the larger class never
exceeds the available pool (95% of 400 = 380 of 541 available control
participants); at 95:5 the minority class is 20 autism participants total
(about 15 train / 5 test after a stratified 75/25 split) — sparse enough to
make the imbalance concrete, while keeping a stratified test partition
possible. Confirmed empirically: across all 6 ratios x 5 seeds x 2 split
kinds (60 fits), the minority test count never reached zero (minimum
observed: 4, in one unstratified 95:5 draw), so the "undefined AUC"
one-class-test-partition path exists and is unit-tested
(`tests/test_export_classification_imbalance_data.py`) but does not occur
in the committed real-data artifact — documented here rather than silently
left unverified.

## Notebook and interactive content delivered

- `book/chapters/chapter_04/exercise_04.ipynb` — 30 cells, `wp17-`-prefixed
  ids, six numbered sections (data, sigmoid, one honest model, metrics, two
  interactive activities) plus Takeaways and exactly three review questions
  with revealable answers. Executed once with a real kernel (network),
  outputs committed; no execution errors.
- Activity A — **decision threshold** (`classification-threshold`): slider
  (0.05-0.95, step 0.01) + synchronized numeric input + reset-to-0.50,
  confusion matrix (HTML table), accuracy/sensitivity/specificity/%-predicted
  stats, ROC curve with a "Chance-level ranking" diagonal and the current
  threshold marked. AUC is computed once from the fixed test-set
  probabilities and never changes with the threshold (verified by a
  Playwright test). Portable-notebook equivalent: an ordinary code cell with
  an editable `threshold = 0.50` line.
- Activity B — **class imbalance / stratified split**
  (`classification-imbalance`): ratio selector (6 ratios) + seed selector (5
  predetermined seeds), side-by-side stratified vs. unstratified panels
  (train/test counts, confusion matrix, accuracy, AUC or "undefined: both
  classes are required", majority-class baseline). Portable-notebook
  equivalent: an ordinary code cell with editable `class_ratio` /
  `random_state` variables, executed with real output in both the canonical
  and portable notebooks.
- Both activities reuse WP16's shared Plotly policy (`plotly-policy.ts`,
  untouched) and the WP16 dynamic iframe-height mechanism (no new resize
  code needed).
- Portable/Colab notebook (`book/downloads/chapter_04/exercise_04_portable.ipynb`):
  generated by `scripts/build_portable_notebook.py` (extended with a new
  `CHAPTER_04` spec), passes `--check`, smoke-executed once end-to-end
  outside the repo (`scripts/smoke_portable_notebook.py`), no `<iframe>`,
  no `ipywidgets`, no private-repo access.
- Toolchain generalized from 3 to 4 notebooks in every place WP17 flagged:
  `book/_toc.yml`, `tests/test_book_structure.py`,
  `scripts/build_portable_notebook.py` (`NOTEBOOKS` dict +
  `PUBLISHED_PAGE_CH4`, plus a stale docstring fix), `scripts/smoke_portable_notebook.py`,
  `book/_static/launch-buttons.js` (`PAGE_TO_PORTABLE`), and
  `interactive/e2e-book/launch-buttons.spec.ts` (`CHAPTERS`).

## Tests run once, pass/fail counts and elapsed time

Run once each, after implementation was stable, per §9:

| Gate | Result | Time |
|---|---|---|
| `classification_model_audit.py --run` (network) | 1 run, honest result written | 8.04s (audit runtime) |
| Python full suite (`python -m unittest discover -s tests`) | **380 passed**, 0 failed | 8.9s |
| Frontend typecheck (`npm run typecheck`) | passed, 0 errors | ~3s |
| Frontend unit tests (`npm run test:unit`, Vitest) | **302 passed** (19 files) | 1.7s |
| Frontend production build (`npm run build`) | succeeded (pre-existing >500kB chunk-size warning, unrelated to WP17) | ~4s |
| Jupyter Book build (`jupyter-book build book`, clean) | succeeded, 2 pre-existing warnings (missing `logo.png`, `README.md` not in toctree) | 34.5s |
| Standalone Playwright (`npx playwright test`) | **140 passed**, 0 failed (includes 22 new classification-activity tests) | 24.2s |
| Built-book Playwright (`--workers=1`) | **57 passed**, 0 failed (includes 6 new Chapter 4 tests + 4 updated launch-button tests) | 68.3s |

**No test failed or flaked.** No rerun of any test was needed.

Additional Python tests for the new data-export scripts and the audit
itself (22 + 19 tests) are included in the 380-test full-suite count above,
not run separately as a second pass.

## Deviations from this WP

1. **Wall-clock vs. active-work timing.** The bounded-execution contract's
   "3 hours of active work" clock was interpreted as active engagement
   time, not raw wall-clock time: a large real-world gap (a new day) fell
   between this WP's pre-flight stop-and-report turn and Yoav's "Proceed
   with WP17" instruction. All substantive research and implementation work
   described here happened within roughly 2.5 hours of active tool use
   following that instruction, well inside the 3-hour bound as intended.
2. **§4's "avoid a visually dense multi-panel dashboard" for Activity A**
   was read as compatible with one confusion-matrix panel (a table, not a
   Plotly chart) + one ROC panel + compact metric-card text, per §4's own
   explicit layout guidance — the confusion matrix is rendered as an
   accessible HTML table rather than a Plotly heatmap, since no prior
   exercise renders a confusion matrix as a chart and a table is simpler,
   losslessly readable at any width, and keyboard/screen-reader friendly.
3. **AUC is computed client-side** from the fixed labels/probabilities
   (`classification-metrics.ts`'s `rocCurve`/`aucTrapezoidal`), not merely
   echoed from the Python audit's number, to keep with this project's
   "nothing is a canned label" convention (matching how `knn-abc`/
   `knn-explore` recompute real predictions client-side). The Python-side
   `aucFromAudit` value is retained in the exported artifact and
   cross-checked by a Python test for consistency, but is not what the
   widget displays.
4. No other deviations. Every explicit WP17 requirement (§1-§11) was
   implemented as written, including the exclusions in §7 (no SMOTE, no
   precision-recall curves, no leave-one-site-out, no coefficient maps,
   etc. — verified by `tests/test_exercise_04_notebook.py`'s
   `test_excluded_topics_absent`).

## Issues requiring Yoav's attention

1. **`WPs/reports/WP16_ARCHITECT_REPORT.md`** is still untracked, per your
   instruction to leave it alone. It remains exactly as it was.
2. **Discrimination is honestly modest** (accuracy 0.546, AUC 0.569) —
   expected and explicitly called out per WP17 §2's "report the result
   honestly even if discrimination is modest." No action needed unless you
   want a stronger example for teaching purposes (would require expanding
   scope beyond what WP17 authorizes, e.g. a different feature bundle or
   target).
3. Nothing else blocks moving on. WP18 was not started.

## Exact terminal commands for Yoav to build and test Exercise 4 locally

```bash
cd /Users/crazyjoe/Projects/ml-neuro-tutorials

# Python data/model audit (offline check; --run needs network)
.venv/bin/python scripts/classification_model_audit.py --check
.venv/bin/python -m unittest discover -s tests -p 'test_exercise_04_notebook.py'
.venv/bin/python -m unittest discover -s tests -p 'test_classification_model_audit.py'
.venv/bin/python -m unittest discover -s tests -p 'test_export_classification_*.py'

# Frontend
cd interactive
npm run typecheck
npm run test:unit
npm run build
npx playwright test                                   # standalone widget app
npx playwright test --config playwright.book.config.ts --workers=1   # needs a prior `jupyter-book build book`

# Jupyter Book (from repo root)
cd ..
jupyter-book build book
# open book/_build/html/chapters/chapter_04/exercise_04.html in a browser
```

## No push or deployment was performed in WP17.

No GitHub Actions workflow was started or monitored. WP18 was not started.
