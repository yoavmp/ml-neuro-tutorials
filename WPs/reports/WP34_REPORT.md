# WP34 Report — Revise Exercise 8 and Build Exercise 9: Advanced Models

## 1. Overall result

**SUCCESS.** Part A replaces Exercise 8's PCA-plus-`LinearRegression`
supervised section with PCA before KNN regression, so PCR is no longer
introduced anywhere before Exercise 9. Part B replaces the Exercise 9
placeholder with a complete "Advanced Models" notebook covering PCR, PLS,
SVMs, and kernels, with two new browser-native interactive activities
("PCR or PLS?" and "Explore an SVM Boundary") and a nested-cross-validation
comparison of five models on the same ABIDE-II age-prediction task every
other exercise uses. All bounded validation gates passed. Everything is
committed locally on `feature/wp34-exercise9-advanced-models`; nothing was
merged, pushed, deployed, or monitored through GitHub Actions.

## 2. Resolved WP33 final branch-tip SHA

`a5c6971` (`WP33: reports — Exercise 8 execution report and exact
changelog`), the tip of `feature/wp33-exercise8-unsupervised-learning`.
WP33's own report omitted this exact value (per its own text); it is
resolved here by `git rev-parse feature/wp33-exercise8-unsupervised-learning`
and `git log --oneline -1`, both of which returned `a5c6971`. The WP33
report/changelog files were **not** modified to backfill this value, per
WP34 §2.3.

## 3. WP34 starting and final branch/SHA

- **Starting point:** `feature/wp33-exercise8-unsupervised-learning` @
  `a5c6971` — confirmed identical to the resolved WP33 tip above.
- Before editing, confirmed: Exercise 8 was a real notebook
  (`book/chapters/chapter_08/exercise_08.ipynb`) whose section 8 was
  "PCA Inside a Supervised Prediction Pipeline" using
  `Pipeline(StandardScaler, PCA, LinearRegression)`; Exercise 9 was still a
  placeholder (`book/chapters/chapter_09/exercise_09.md`). Both matched
  WP34 §2.4 exactly.
- **New branch:** `feature/wp34-exercise9-advanced-models`, created from
  the SHA above.
- **Checkpoint commit** (spec added before implementation): `9daffdc`.
  *Deviation, self-corrected:* the branch and checkpoint commit were
  created slightly after the first few implementation file edits had
  already begun (no commits existed yet at that point, so no history was
  disturbed) rather than strictly before. This is noted transparently per
  WP34 §9's instruction to report every deviation; the resulting commit
  graph is identical to what it would have been had the branch been
  created first.
- **Implementation commit:** `c2575e0bb165a6fa77c4464c9674b1d163aeae5b`
  ("WP34: Part A — Exercise 8 PCA+KNN correction; Part B — Exercise 9
  Advanced Models").
- This report and the exact changelog are committed as one further commit
  on top of `c2575e0` (see §12 for the exact final SHA, captured after
  that commit).

## 4. Part A — exact Exercise 8 changes and new KNN results

`book/chapters/chapter_08/exercise_08.ipynb` section 8 was replaced in
place (cells 25–31, same count and position, title and content rewritten):

- **Title:** `## 8. PCA Inside a Supervised Prediction Pipeline` →
  `## 8. Using PCA Before a Model We Already Know`.
- **Model:** `Pipeline(StandardScaler, PCA, LinearRegression)` →
  `Pipeline(StandardScaler, PCA, KNeighborsRegressor)`, compared against
  standardized KNN on the original 360 features under the identical
  `KFold(n_splits=5, shuffle=True, random_state=13)` folds and
  `train_test_split(test_size=0.25, random_state=42, stratify=groups)`
  outer split (`protocol.holdout_split`, unchanged).
- **Grid:** jointly selected `n_components` from `[5, 10, 20, 50, 100]` and
  `k` from `[5, 10, 20, 40]` (20 combinations x 5 inner folds) by minimum
  mean CV MSE; the raw-feature KNN baseline selects `k` from the identical
  `k_grid` under the identical folds.
- **One Think First question** (verbatim, per spec): *"Why might PCA help
  KNN more directly than it helps a model that does not calculate
  distances between participants?"*
- **Imports:** `sklearn.linear_model.LinearRegression` replaced by
  `sklearn.neighbors.KNeighborsRegressor` in the shared data-loading cell.
- **Repository-wide search confirmed:** neither "PCR", "principal
  component regression", nor "LinearRegression" appears anywhere in
  Exercise 8 (new `test_pcr_is_not_introduced_here` assertion); the
  earlier PCA-regression-vs-OLS comparison and its results/metrics are
  fully removed.
- **Audited results** (`scripts/pca_kmeans_audit.py --run`,
  `scripts/pca_kmeans_audit_result.json`): selected **n_components=20,
  k=10** (mean CV MSE = 24.8); locked-test **PCA(20)+KNN(k=10)**: MSE =
  **21.0**, R² = **+0.775**; **raw-feature KNN (k=5)**: MSE = **32.0**,
  R² = **+0.657**. On this cohort and split, **PCA substantially improves
  KNN** — the notebook reports this without implying PCA must always help
  distance-based models, consistent with the section's own teaching point
  that PCA keeps variance-defined directions, not target-informed ones.
- Portable notebook regenerated (`exercise_08_portable.ipynb`, 35 cells,
  unchanged count) and smoke-executed outside the repository tree with 0
  errors, matching the new printed values.

## 5. Part B — Exercise 9 section list and cell count

`book/chapters/chapter_09/exercise_09.ipynb`, **27 cells**, in order:

- Title (`# Exercise 9: Advanced Models`)
- Green "Run or download this notebook" admonition
- "What this notebook covers" (4-item list, matching WP34 §6 verbatim)
- `## 1. Why Consider More Advanced Models?` (+ Think First)
- `## 2. Principal Component Regression` (PCR introduced here for the
  first time in the course; illustrative, non-executed pipeline fence)
- `## 3. Partial Least Squares` (supervised component construction;
  illustrative pipeline fence using `scale=False` with a one-line comment)
- `## 4. Interactive Activity — PCR or PLS?` (+ iframe + hidden
  illustrative Python reproduction + guiding questions)
- `## 5. Support Vector Machines` (margin/support-vector concepts +
  parameter table, verbatim from WP34 §5's four-row table)
- `## 6. Kernels and Nonlinear Boundaries` (linear/polynomial/RBF)
- `## 7. Interactive Activity — Explore an SVM Boundary` (+ iframe +
  hidden illustrative Python reproduction + guiding questions + SVR bridge
  sentence)
- `## 8. Comparing Advanced Models on ABIDE-II`: pre-questions, hidden data
  loading, hidden nested-CV comparison machinery, visible results
  table+plot, collapsed selected-hyperparameters dropdown, honest
  discussion
- `## 9. Strengths, Weaknesses, and Appropriate Uses` (4-row table,
  verbatim from spec)
- `## 10. Test-Oriented Thinking Questions` (10 numbered questions; 5 have
  a `{dropdown}` revealable answer for the central concepts)
- `## 11. Main Takeaways`

Cell count (27) is below Exercise 1's cell count and above the 20-cell
floor used for this check; the notebook is visibly less dense than
Exercise 1 and does not repeat a full prediction-pipeline tutorial (the
only `pd.read_csv` and only nested-CV/nested nested loop in the notebook
is in section 8; sections 2–7 show only illustrative, non-executed or
small self-contained code).

## 6. Interactive controls, defaults, and artifact sizes

**Activity A — `pcr-pls-explore` ("PCR or PLS?")**
- Controls: method select (PCR/PLS, default PCR), number-of-components
  select (1/2, default 1), preset select (Weak/Moderate/Strong alignment
  with the lower-variance direction, default Moderate)
- Data: a fixed, deterministic synthetic 60-point 2-D predictor cloud
  (`scripts/export_pcr_pls_widget.py`; ρ=0.7, seed=21) with a fixed 40/20
  train/validation split; PC1 explains 85% of predictor variance, PC2 15%
  (closed-form, since ρ is fixed and marginal variances are equal). Only
  the target (and therefore the precomputed PCR/PLS fits) changes across
  presets; the predictor cloud and the split never do.
- All 2 (methods) × 2 (component counts) × 3 (presets) = 12 combinations
  precomputed with scikit-learn (`Pipeline(StandardScaler, PCA,
  LinearRegression)` for PCR; `Pipeline(StandardScaler,
  PLSRegression(scale=False))` for PLS); confirmed PCR's direction never
  depends on the preset (target-blind) while PLS's does, and PCR/PLS
  converge exactly at 2 components (full predictor-space regression) —
  both independently verified in `tests/test_export_pcr_pls_widget_data.py`.
- Outputs: predictor cloud colored by target value (continuous colorscale,
  train circles / validation diamonds), the selected first component as an
  overlaid line, observed-vs-predicted validation scatter with a diagonal
  reference, training/validation MSE, and a one-sentence construction note
  that differs by method.
- `book/_static/widgets/data/pcr_pls_explore.json`: **17,803 bytes (17.4
  KiB) uncompressed, 3,435 bytes (3.4 KiB) gzip -9**.

**Activity B — `svm-explorer` ("Explore an SVM Boundary")**
- Controls: dataset select (Approximately linear / Nonlinear, default
  linear), kernel select (linear/poly/RBF, default linear), `C` select
  (`[0.1, 1, 10, 100]`, default 1), `gamma` select (`[0.1, 1, 10]`, default
  1, **disabled** — not merely ignored — with a visible note whenever the
  linear kernel is selected)
- Data: two fixed, deterministic synthetic 80-point 2-D classification
  datasets (`scripts/export_svm_explorer_widget.py`; seed=33) — Gaussian
  blobs (linear) and a noisy inner-blob/outer-ring shape with 4 deliberate
  near-boundary label flips (nonlinear) — each with its own fixed 60/20
  train/validation split.
- All (dataset × kernel × C × gamma-where-relevant) = 28 combinations per
  dataset (56 total) precomputed with `Pipeline(StandardScaler,
  SVC(...))`; support vectors are always training-row ids; the decision
  grid is a fixed 60×60 mesh stored as compact `"0"/"1"` digit-string rows
  (not nested number arrays) to avoid the JSON pretty-printer's
  one-line-per-number blow-up.
- Outputs: training/validation points with distinguishable
  circle/diamond markers per class, filled decision regions, open-circle
  support-vector markers, training accuracy, validation accuracy, and
  support-vector count.
- `book/_static/widgets/data/svm_explorer.json`: **329,189 bytes (321.5
  KiB) uncompressed, 9,824 bytes (9.6 KiB) gzip -9**. (Well under WP33's
  940.9 KiB precedent; an earlier draft that stored the decision grid as
  nested number arrays was 3,511.1 KiB uncompressed — reduced without
  cutting the grid, per WP34 §7's "reduce redundant storage" instruction;
  see §9 for the numerical/runtime deviations behind this activity too.)

## 7. ABIDE comparison grids, fold structure, model results, and selected parameters

Same 1,004 eligible participants, 360 cortical-thickness features, and
`age` target as every other exercise (no missing ages in this cohort).
**Outer:** `KFold(n_splits=5, shuffle=True, random_state=100)` — identical
outer folds for every model, matching Exercise 4's own nested-CV
convention. **Inner:** `KFold(n_splits=5, shuffle=True, random_state=101)`,
computed once per outer fold and reused across every model's candidate
grid within that fold. Inner selection always uses mean inner-fold MSE;
each model is refit once on the full outer-training fold at its selected
hyperparameter(s) and evaluated exactly once on the outer-test fold.

| Model | Grid | Selected (every outer fold) | Mean outer-test MSE (SD) | Mean outer-test R² |
|---|---|---|---|---|
| Standardized OLS (reference) | none | — | 49.14 (6.31) | +0.427 |
| PCR | `n_components ∈ [5,10,20,50,100,200]` | 50 | 31.74 (7.04) | +0.638 |
| PLS | `n_components ∈ [2,5,10,20]` | 5 | 32.42 (7.71) | +0.632 |
| Linear SVR | `C ∈ [0.01,0.1,1,10]`, `epsilon ∈ [0.5,1,2]` | `C=0.1, epsilon=2` | 40.28 (12.44) | +0.552 |
| RBF SVR | `C ∈ [1,10,100]`, `gamma ∈ ["scale",0.001,0.01]` | `C=100, gamma="scale"` | 20.15 (5.77) | +0.774 |

On this cohort and split, **RBF SVR wins clearly**; **PCR and PLS perform
almost identically** (a concrete instance of the notebook's own "what would
overlapping fold-to-fold results mean?" guiding question); linear SVR beats
plain OLS but trails both dimensionality-reduction methods; OLS on the full
360 correlated features is weakest, consistent with Exercise 8's own
supervised-pipeline finding. Reported honestly as the observed result for
this cohort and split, not a general ranking. Full per-fold candidate
scores and selections are committed in
`scripts/advanced_models_audit_result.json` and independently re-derivable
from the portable notebook's own `fold_results` table.

## 8. Validation commands, durations, and outcomes (bounded plan, in order)

| # | Gate | Command(s) | Result |
|---|------|------------|--------|
| 1 | Focused Ex8 correction audit/tests | `pca_kmeans_audit.py --run`/`--check`; `unittest -p test_exercise_08_notebook.py`; `unittest -p test_pca_kmeans_audit.py` | OK; audit ~7s; 50 + 14 tests, all pass |
| 2 | Focused Ex9 model audit/tests | `advanced_models_audit.py --run`/`--check`; `unittest -p test_advanced_models_audit.py` | OK; audit **216.2s** (see §9 for the runtime fix that made this feasible — an earlier attempt exceeded 20 minutes and was killed); 13 tests pass |
| 3 | Focused widget export checks + Python tests | `export_pcr_pls_widget.py --refresh`/`--check`; `export_svm_explorer_widget.py --refresh`/`--check`; `unittest -p test_export_pcr_pls_widget_data.py` (13 tests); `unittest -p test_export_svm_explorer_widget_data.py` (11 tests) | All OK; PCR/PLS export instant; SVM export ~15–34s |
| 4 | Regenerate portable notebooks + `--check` | `build_portable_notebook.py --write --notebook chapter_08` / `chapter_09`; `--check --notebook all` | 35-cell and 29-cell notebooks written; all 9 registered notebooks up to date |
| 5 | Portable smoke execution, Ex8 + Ex9, outside the repository | copied both portable notebooks to a scratch dir; `jupyter nbconvert --to notebook --execute --inplace`; `smoke_portable_notebook.py --notebook chapter_08` / `chapter_09` | 0 errors both; smoke key-value checks OK; Ex9 execution ~3.7 min (nested-CV cell) |
| 6 | Focused frontend unit tests + typecheck | `npx vitest run tests/pcr-pls-explore-data.test.ts tests/svm-explorer-data.test.ts` (24 tests); `npm run typecheck` | All pass; typecheck clean |
| 7 | One frontend production build | `npm run build` | Succeeded (pre-existing >500 kB chunk-size warning, unrelated) |
| 8 | Focused standalone Playwright for the two new activities | `npx playwright test e2e/pcr-pls-explore.spec.ts e2e/svm-explorer.spec.ts e2e/plot-visual-policy.spec.ts` | 13/13 + 20/20 (after 1 narrow-viewport fix, see §9) |
| 9 | One Jupyter Book build | `jupyter-book build book` (clean, then one incremental rebuild after a text-only widget-config fix) | Succeeded, 2 warnings (both pre-existing: missing `logo.png`, `README.md` not in any toctree); Ex9 execution ~3.6–3.7 min; incremental rebuild after the config fix reused the jupyter-cache and took ~6s |
| 10 | Focused built-book Ex8/Ex9 tests incl. dark mode | `playwright test --config playwright.book.config.ts e2e-book/chapter08.spec.ts e2e-book/chapter08-dark-mode.spec.ts e2e-book/chapter09.spec.ts e2e-book/chapter09-dark-mode.spec.ts e2e-book/launch-buttons.spec.ts` | 45/45 (first pass), then 16/16 re-confirmed against the clean rebuild |
| 11 | Full Python suite once | `unittest discover -s tests -p 'test_*.py'` | **959 tests, 0 failures, 11 skipped** (network-only; up from 872 in WP33) |
| 12 | Full frontend unit suite once | `npm test` (typecheck + `vitest run`) | **34 files / 426 tests, all passed** (up from 402 in WP33) |
| 13 | Full standalone + built-book Playwright once | `npx playwright test`; `npx playwright test --config playwright.book.config.ts` | **242/242** standalone (up from 227); **118/118** built-book (up from 107) |
| 14 | Manual visual inspection | Playwright screenshots, light/dark/390 px-narrow, chapter pages and both new widgets individually | Confirmed correct in all states (see §9 for one fix this step caught) |

No gate was rerun more than the bounded-plan-permitted one correction
cycle; no long-running full suite was rerun speculatively (the Jupyter Book
build's second, ~6-second run reused the jupyter-cache rather than
re-executing any notebook, since only a static widget-config JSON file —
not a notebook — had changed).

## 9. Failures, retries, deviations, and judgment calls

- **`SVR(kernel="linear")` → `LinearSVR` substitution (documented
  runtime fix, made before viewing any outer-fold result).** The first
  `advanced_models_audit.py --run` attempt was killed twice across two
  session boundaries after 15–20+ minutes without completing. Direct
  timing on one real outer-training fold (n=803, p=360) showed
  `SVR(kernel="linear", C=10)` alone takes **65 seconds for a single fit**;
  the nested-CV grid needs roughly 800 such fits, an infeasible runtime.
  `LinearSVR` (liblinear coordinate descent) solves the identical
  epsilon-insensitive linear objective — scikit-learn's own documented
  recommendation for this n/p regime — and every fit completes in under 2
  seconds (`max_iter=5000`). This is recorded in
  `book/config/abide_modeling.json`
  (`advanced_models.abide_comparison.linear_svr_solver_note`) and in code
  comments in both `scripts/advanced_models_audit.py` and the notebook.
  With this fix, the full audit completed in 216.2 seconds. **Flagged for
  attention:** this is an implementation-level solver substitution, not a
  change to the taught concept (the parameter table and prose still teach
  `SVR`'s `C`/`epsilon`/`kernel`/`gamma` generically); it was made purely
  for runtime feasibility, before any comparison result was seen.
- **`LinearSVR` non-convergence at large `C` (recorded, not silently
  discarded).** At `C=10` (the grid's largest linear-SVR value),
  `LinearSVR` does not fully converge within `max_iter=5000` on real
  ABIDE data — confirmed this is intrinsic conditioning, not merely an
  iteration-budget artifact, by rerunning at `max_iter=100000` (still
  non-convergent, 22s). 128 `ConvergenceWarning`s were captured (all from
  `linear_svr`) and recorded in `advanced_models_audit_result.json`'s
  `convergence_warnings` list rather than discarded; the notebook's own
  discussion cell states this honestly and notes it did not prevent a
  stable hyperparameter selection across outer folds. The notebook's own
  code suppresses printing 100+ raw warning lines (via
  `warnings.filterwarnings`) so the stored output stays readable; the
  underlying warnings are still captured and reported in prose.
- **Narrow-viewport (390 px) overflow, `pcr-pls-explore` (1 correction).**
  A native `<select>` sizes its closed box to its widest *option* text,
  which cannot wrap; the preset select's options initially repeated the
  full preset description (already shown in the control's own label),
  overflowing at 390 px by 33 px. Fixed by shortening the option text to
  "Weak"/"Moderate"/"Strong" while keeping the full description in the
  label. Root cause identified immediately from a DOM-width debug script;
  rerun once; passed.
- **Duplicate "conceptual exploration" sentence, `svm-explorer` (1
  correction, caught only by manual screenshot review, §10 step 14).** The
  widget's own hardcoded conceptual-exploration note (component-level, per
  WP34 §7's requirement that this activity be clearly labeled) duplicated
  a near-identical sentence already present in the widget config's
  `instructions` text. Removed the sentence from
  `book/_static/widgets/configs/svm_explorer.json`, keeping exactly one
  occurrence, consistent with the repeated-warning rule in
  `NOTEBOOK_AUTHORING_STANDARDS.md` §7 applied to the widget's own UI.
  Verified with a fresh screenshot after an incremental Jupyter Book
  rebuild (which reused the jupyter-cache, ~6s, no re-execution needed).
- **Stale `exercise_09.md` placeholder left on disk (1 correction).** The
  old placeholder was not deleted when `exercise_09.ipynb` was created,
  causing Sphinx to log "multiple files found for the document" (resolved
  in favor of the `.ipynb`, so the *content* built correctly throughout,
  but the ambiguity itself was undesirable to leave in the repository).
  `git rm`'d before the final commit, matching WP33's own precedent of
  removing the prior placeholder outright.
- **`EXERCISE_TITLES[9]` / required-phrase correction in
  `tests/test_wp25_content_audit.py` (judgment call, flagged for
  attention).** WP34 §6 explicitly specifies the title
  `# Exercise 9: Advanced Models`. The pre-existing test file recorded a
  longer title, `"Exercise 9: Advanced Models and Model Comparison"`
  (inherited from the original WP25-era placeholder text, not from
  `book/syllabus.md`, which currently contains only a bare `# Syllabus`
  heading and no exercise titles). Updated `EXERCISE_TITLES[9]` and the
  corresponding `test_titles_use_title_case_for_the_named_phrases` required
  phrase to match WP34's explicit instruction, following the same pattern
  WP33 used when it corrected `EXERCISE_TITLES[8]` from a stale title to
  its own required one. **This is a title choice worth double-checking**
  before deployment, since it shortens the exercise's previously-recorded
  full name.
- **Session-boundary interruptions (process, not a defect).** Two
  long-running background computations (the Exercise 9 nested-CV audit,
  initially, and its later notebook/Jupyter-Book-build echoes) were killed
  when their hosting session ended between turns, before the
  `SVR`→`LinearSVR` fix. Each was restarted from the same deterministic
  code with no data loss, since nothing had been committed mid-computation;
  no repository state was left inconsistent.

No gate failed and was left unresolved. No repair loop was entered beyond
the single-correction-then-rerun pattern the bounded plan allows.

## 10. Confirmation: Syllabus and Word course-overview untouched

`book/syllabus.md` and the `course_overview/` Word document were not
opened, read, or modified at any point in this WP.
`git status --short` (§14) confirms no changes under either path.

## 11. Confirmation: nothing merged, pushed, deployed, or monitored via CI

Nothing was merged, pushed, or deployed. No GitHub Actions workflow was
run, triggered, or monitored. All work exists only in local commits on
`feature/wp34-exercise9-advanced-models`.

## 12. Final `git status --short --branch` and decorated log

Immediately before committing this report + changelog:

```
## feature/wp34-exercise9-advanced-models
?? WPs/reports/WP34_EXACT_CHANGELOG.md
?? WPs/reports/WP34_REPORT.md
```

Decorated log at the implementation commit (parent of this report commit):

```
c2575e0 (HEAD -> feature/wp34-exercise9-advanced-models) WP34: Part A — Exercise 8 PCA+KNN correction; Part B — Exercise 9 Advanced Models
9daffdc WP34: add specification (initial checkpoint)
a5c6971 (feature/wp33-exercise8-unsupervised-learning) WP33: reports — Exercise 8 execution report and exact changelog
0d9bf16 WP33: Exercise 8 — Unsupervised Learning
d76437d WP33: add specification (initial checkpoint)
```

After this commit, `git status --short --branch` returns to a clean tree
(`## feature/wp34-exercise9-advanced-models`, no other lines), and
`git log --oneline -1` reports the report commit as the new branch tip.
