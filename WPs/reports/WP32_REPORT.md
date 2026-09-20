# WP32 Report — Exercise 7: Boosting and Gradient Boosting

## 1. Starting and final state

- Local `main` before starting: `a64e3492d8796dcda67c7f59b414df5977e8b989`, exactly one
  documentation-only commit (`WP31R3: document Chapter 1 dark-mode fix and successful
  redeploy`) ahead of `origin/main` (`4f0dc06bc4c0c26f8259d4f679832b9e3eb813a4`), verified by
  `git fetch origin main` + `git log origin/main..HEAD`.
- Untracked files at start: exactly the three whitelisted ones (`WPs/WP32_...md`,
  `WPs/reports/WP16_ARCHITECT_REPORT.md`, `WPs/reports/WP21_DEPLOYMENT_REPORT.md`). No
  unexpected modified/untracked files. No pull/reset/rebase/stash performed.
- Branch created: `feature/wp32-exercise7-gradient-boosting` from local `main`.
- Checkpoint commit: `71267fd70fd0283ddb60f9c1961e65a3cca7c996` ("WP32: add specification
  (initial checkpoint)").
- Final state: implementation and this report committed locally on the same branch. Not
  merged, not pushed, no deploy, no GitHub Actions monitored, WP33 not started.

## 2. Final notebook outline and cell count

`book/chapters/chapter_07/exercise_07.ipynb` — **32 cells** (title; green run/download
admonition; "What this notebook covers"; 8 numbered sections following the spec's suggested
outline, each split into a title cell plus supporting cells; exactly 2 `<iframe>` activities;
XGBoost dropdown; summary + takeaway questions). This is under the spec's "approximately
35-45" guidance — see **Deviations** below for why. It remains substantially shorter than
Exercise 1 (75-cell portable / more canonical cells) as required.

Portable notebook: `book/downloads/chapter_07/exercise_07_portable.ipynb` — 34 cells (2 more
than canonical: banner + setup cells prepended by the generator).

## 3. Cohort and split sizes (audited and reused verbatim)

- Eligible cohort: **1004** participants, 360 cortical-thickness (`CT`) predictors, target
  `age`.
- Outer holdout split (`protocol.holdout_split`, `test_size=0.25, random_state=42,
  stratify=group`): **753** development / **251** locked test.
- Dev split (`gradient_boosting.dev_split`, identical values to `decision_tree.dev_split`:
  `test_size=0.25, random_state=7, stratify=group`, applied to the 753-row development
  partition): **564** fitting / **189** validation.
- The locked 251-row test set is read exactly once, in the notebook's section 6 pipeline and
  in `scripts/gradient_boosting_model_audit.py`'s `cv_pipeline` step; it never appears in
  either widget's data artifact (schema-enforced for the parameter explorer: no field could
  carry it).

## 4. Synthetic activity ("Build a Boosted Model")

- 24 observations, one continuous predictor `x ~ Uniform(0, 10)`.
- Formula: `y = C + A*sin(FREQ*x) + B*x + noise`, `noise ~ Normal(0, NOISE_SD)`, with
  `C=5.0, A=4.0, FREQ=0.9, B=0.6, NOISE_SD=1.2`.
- Seed `7`, fixed before generation (no seed search — unlike Exercise 6's greedy-split
  activity, no split-optimum "niceness" criterion applies here).
- Stages 0 (training-target mean) through 12, precomputed for learning rates
  `[0.1, 0.3, 0.5, 1.0]`. Stage-0 training MSE = 16.20 for all four; stage-12 training MSE:
  0.1→5.76, 0.3→2.91, 0.5→1.78, 1.0→0.89 (monotone with learning rate, as expected).
- Stumps are `max_depth=1` `DecisionTreeRegressor`s fit to the residual before each update;
  every stored `ensemblePrediction` is verified (offline, in both the export script's
  `validate()` and `tests/test_export_boosting_step_widget_data.py`) to equal
  `previous + eta * treePrediction`.
- Artifact size: 108,988 bytes raw (budget: under 150 KB — met).

## 5. ABIDE parameter-explorer activity

- Grids (fixed before any model was fit): learning rates
  `[0.01, 0.03, 0.05, 0.1, 0.2, 0.5]`, depths `[1, 2, 3]`, tree counts
  `[1, 5, 10, 20, 30, 50, 75, 100, 150, 200, 300]` — 198 (learning_rate, depth, n_trees)
  combinations from only **18** actual model fits (one `GradientBoostingRegressor` per
  (learning_rate, depth) pair at `n_estimators=300`, using `staged_predict` for every other
  displayed tree count).
- Defaults: `learning_rate=0.1, depth=2, n_trees=100` (declared in the manifest before the
  script was ever run).
- Artifact size: 777,630 bytes raw (budget: under 1.5 MB — met), 108,043 bytes gzip (budget:
  under 300 KB — met).
- At the default configuration, validation MSE falls from 64.9 (1 tree) to a minimum of 18.78
  around 100-150 trees, then rises slightly to 19.58 by 300 trees, while training MSE keeps
  falling to 0.81 — a genuine (not manufactured) underfit→best→slight-overfit curve, used
  directly for Section 5's "Choosing When to Stop" discussion and its "300 vs. 120 trees"
  question.
- **Play/Pause**: `setInterval`-driven advance through the `nTreesGrid` index at the current
  (learning_rate, depth); any control change calls `stopPlaying()` before applying the new
  value; reaching the final grid value auto-stops and restores the "Play" label; Reset stops
  playback and restores the declared defaults; `destroy()` always clears the interval.
  `prefers-reduced-motion` triples the interval rather than disabling Play. Covered by 10
  standalone Playwright tests plus 2 built-book tests (see §8).

## 6. CV-tuning pipeline, runtime, selection, and comparison

- Intended grid: `learning_rate ∈ {0.03, 0.05, 0.1}`, `n_estimators ∈ {50, 100, 200}`,
  `max_depth ∈ {1, 2, 3}` — 27 candidates.
- **Runtime audit** (predeclared rule, timed with a same-shape 600×360 synthetic proxy matrix
  before running the real audit): full 27-candidate × 5-fold grid ≈ 357s; every other
  exercise's full audit in this course runs in 10-35s, so the full grid was judged
  disproportionate. Reduced once, before any candidate was scored, to a **12-candidate**
  fixed subset (all 3 depths × 4 representative `(learning_rate, n_estimators)` pairs:
  `(0.03,50), (0.05,100), (0.1,100), (0.1,200)`) — proxy-timed at ≈153s. The actual audited
  5-fold run on real ABIDE data took **140.6s** (`cv_pipeline.cv_runtime_seconds` in the
  committed result).
- `KFold(n_splits=5, shuffle=True, random_state=13)`, folds formed only within the 753-row
  development partition. Selection: minimum mean CV MSE, ties broken by declaration order
  (none occurred). Selected: `{learning_rate: 0.1, n_estimators: 200, max_depth: 3}`, mean CV
  MSE = 27.2. Refit on all 753 development rows; locked-test MSE = **32.4**, R² = **0.653**
  (read exactly once).
- **Comparison (section 7)**, all three models evaluated on the identical outer
  development→locked-test split and the identical 360-feature recipe (single tree and Random
  Forest use Exercise 6's own `decision_tree.fair_comparison` settings, carried forward
  unchanged, not retuned):

  | Model | Locked-test MSE | Locked-test R² |
  |---|---|---|
  | Single tree | 70.1 | 0.249 |
  | Random Forest | 38.2 | 0.591 |
  | Gradient boosting | 32.4 | 0.653 |

  Gradient boosting genuinely wins here; the notebook and audit both state this is a
  consistent held-out comparison, not proof of universal superiority, and the numbers are
  recorded plainly rather than adjusted toward any expected outcome
  (`tests/test_gradient_boosting_model_audit.py::test_comparison_does_not_force_gradient_boosting_to_win`).

## 7. A correctness bug found and fixed during implementation

The first versions of `scripts/gradient_boosting_model_audit.py` and
`scripts/export_boosting_parameter_widget.py` selected the 360 cortical-thickness columns via
`abide_modeling_data.bundle_columns()`'s canonical ROI-then-hemisphere ordering, while the
notebook (matching Exercise 6's own established convention, `_natural_order_columns`) uses the
raw table's column order. Because these columns are highly correlated, tree-based
best-split tie-breaking is order-sensitive — the notebook's live execution and the audit
script's numbers silently diverged (e.g. sklearn-example validation MSE 18.3 vs. 18.2;
CV-selected `max_depth` 2 vs. 3; locked-test MSE 29.3 vs. 32.4). Caught by comparing the
executed notebook's own printed output against the audit JSON before writing tests. Fixed by
adding the identical `_natural_order_columns()` helper (matching
`decision_tree_model_audit.py`'s own, with the same documented rationale) to both scripts and
re-running `--run`/`--refresh`; the notebook's live numbers and the committed audit now match
exactly.

## 8. Files created / changed / deleted

**Created:**
- `scripts/gradient_boosting_model_audit.py`, `scripts/gradient_boosting_model_audit_result.json`
- `scripts/export_boosting_step_widget.py`, `scripts/export_boosting_parameter_widget.py`
- `book/_static/widgets/data/boosting_step_by_step.json`,
  `book/_static/widgets/data/boosting_parameter_explorer.json`
- `book/_static/widgets/configs/boosting_step_by_step.json`,
  `book/_static/widgets/configs/boosting_parameter_explorer.json`
- `interactive/src/boosting-step-by-step-data.ts`, `interactive/src/boosting-parameter-explorer-data.ts`
- `interactive/src/components/boosting-step-by-step.ts`, `interactive/src/components/boosting-parameter-explorer.ts`
- `book/chapters/chapter_07/exercise_07.ipynb`, `book/downloads/chapter_07/exercise_07_portable.ipynb`
- `interactive/tests/boosting-step-by-step-data.test.ts`, `interactive/tests/boosting-parameter-explorer-data.test.ts`
- `interactive/e2e/boosting-step-by-step.spec.ts`, `interactive/e2e/boosting-parameter-explorer.spec.ts`
- `interactive/e2e-book/chapter07.spec.ts`
- `tests/test_gradient_boosting_model_audit.py`, `tests/test_export_boosting_step_widget_data.py`,
  `tests/test_export_boosting_parameter_widget_data.py`, `tests/test_exercise_07_notebook.py`
- `WPs/reports/WP32_REPORT.md`, `WPs/reports/WP32_EXACT_CHANGELOG.md`

**Changed:**
- `book/config/abide_modeling.json` (new `gradient_boosting` manifest block)
- `book/_config.yml` (corrected stale Mermaid comment, no rendered-content change)
- `book/_static/launch-buttons.js` (registered Chapter 7; updated placeholder-range comment)
- `scripts/build_portable_notebook.py` (registered `CHAPTER_07`; updated docstring)
- `interactive/src/config.ts` (two new Zod activity schemas + union entries)
- `interactive/src/components/registry.ts` (registered both new components)
- `interactive/e2e/plot-visual-policy.spec.ts` (added 3 chart entries for the new activities)
- `interactive/e2e-book/launch-buttons.spec.ts` (added Chapter 7 to `CHAPTERS`; moved the
  "placeholder gets no Colab button" check from Exercise 7 to Exercise 8)
- `tests/test_placeholder_exercises.py`, `tests/test_exercise_06_notebook.py`,
  `tests/test_exercise_04_notebook.py`, `tests/test_book_structure.py`,
  `tests/test_wp25_content_audit.py` (removed/renumbered Exercise 7 from every
  "placeholder Exercises 7-12" assumption; retitled Exercise 7 in
  `test_wp25_content_audit.py`'s `EXERCISE_TITLES`)

**Deleted:**
- `book/chapters/chapter_07/exercise_07.md` (replaced by the `.ipynb`, via `git rm`, history
  preserved through the rename-like replace)

## 9. Every test/build command and result

| # | Command | Result |
|---|---|---|
| 1 | `python scripts/gradient_boosting_model_audit.py --run` then `--check` | ✅ self-consistent; numbers match live notebook execution |
| 2 | `python scripts/export_boosting_step_widget.py --refresh` then `--check` | ✅ self-consistent, semantic-diff matches a fresh recomputation |
| 3 | `python scripts/export_boosting_parameter_widget.py --refresh` then `--check` | ✅ self-consistent |
| 4 | `python -m unittest` (4 new WP32 test files + updated `test_placeholder_exercises`, `test_exercise_06_notebook`) | ✅ all pass (after fixing 4 test-assertion bugs of my own, listed below) |
| 5 | `python -m unittest discover -s tests -p 'test_*.py'` (full offline suite) | ✅ 789 tests, 0 failures, 11 skipped (network-only tests) |
| 6 | `python scripts/build_portable_notebook.py --write --notebook chapter_07` then `--check --notebook all` | ✅ 34 cells written; all 7 chapters up to date (75/43/34/34/47/33/34) |
| 7 | Standalone smoke-execute of `exercise_07_portable.ipynb` in a fresh temp directory (`jupyter nbconvert --execute`) | ✅ exit 0, no repo dependency |
| 8 | `jupyter nbconvert --to notebook --execute --inplace exercise_07.ipynb` | ✅ ran twice (before/after the column-order fix); zero error outputs |
| 9 | `npm run typecheck`, `npm run build` (interactive/) | ✅ clean; bundle unchanged in size class (pre-existing >500kB chunk warning, not new) |
| 10 | `npm test` (typecheck + full Vitest unit suite) | ✅ 29 files / 376 tests |
| 11 | `npx playwright test` (full standalone suite) | ✅ 208/208 passed |
| 12 | `rm -rf book/_build && jupyter-book build book/` | ✅ succeeded, 2 pre-existing unrelated warnings (missing `logo.png`, `README.md` not in toctree); Chapter 7 executed in 161.2s with zero error outputs |
| 13 | `npx playwright test --config playwright.book.config.ts` (full built-book suite, including `chapter01-dark-mode.spec.ts`) | ✅ 96/96 passed |
| 14 | Ad hoc Playwright script toggling `data-theme=dark` on the built Chapter 7 page | ✅ body background switches to the dark palette; plot container stays `rgba(0,0,0,0)` |
| 15 | Manual audits of every existing exercise's `--check` script (`decision_tree_model_audit`, `export_tree_ensemble_widget`, `export_tree_greedy_widget`, `knn_model_audit`, `regression_model_audit`, `regularization_model_audit`, `classification_model_audit`, `sample_size_audit`, `wp27_validation_audit`) | ✅ all unaffected by the manifest edit |

## 10. Failures, focused corrections, and reruns

- **Frontend typecheck** initially failed on two type errors (a `Timeout` vs. `number`
  interval-handle mismatch; an `unknown[]` Plotly trace array). Fixed by typing
  `intervalHandle` as `number | undefined` and using the ambient `PlotData[]` type; rerun
  passed.
- **Vitest unit test** (`boosting-step-by-step-data.test.ts`) failed on the real committed
  artifact: JSON spells the learning rate `1.0` as `"1.0"`, but JS's `String(1)` produces
  `"1"`, so a naive `stagesByLearningRate[String(eta)]` lookup missed it. Fixed by matching
  keys numerically (`stagesForLearningRate` helper) in both the schema's `superRefine` and the
  component; rerun passed. The standalone Playwright spec was written with the correct `"1"`
  select-option value from the start once this was understood.
- **Column-order correctness bug** — see §7 above; both audit/export scripts corrected, both
  re-run, notebook re-executed and reconciled.
- **Four of my own new Python-test assertions failed** on first run against real data/notebook
  text (an over-strict dict-equality check that didn't account for a `note` field; an
  over-broad `"test" not in keys` check that flagged the legitimate key
  `lockedTestExcluded`; two exact-substring checks broken by Markdown bold markers / a line
  wrap). All four were test-only bugs, not product bugs; fixed by loosening/normalizing the
  assertions, rerun passed.
- **One standalone Playwright test** (`boosting-parameter-explorer.spec.ts`) asserted the
  widget's body text must not contain "locked test" — but the widget's own required framing
  copy legitimately says "the locked test set remains unavailable." Fixed to check for the
  expected framing phrase instead of a blanket negative; rerun passed.
- **Three pre-existing tests genuinely broke** by definition once Chapter 7 became a real
  notebook: `tests/test_exercise_04_notebook.py`'s and
  `tests/test_exercise_06_notebook.py`'s "Exercises 7-12 remain placeholders" assertions, and
  `interactive/e2e-book/launch-buttons.spec.ts`'s "Exercise 7 gets no Colab button" test — all
  three renumbered to 8-12 / Exercise 8, plus `tests/test_book_structure.py` and
  `tests/test_wp25_content_audit.py`, which were not on the spec's explicit rerun list but
  failed the full-suite run for the same reason (hardcoded `n <= 6` / `range(7, 13)`
  assumptions); all fixed narrowly (chapter 7 added to the "real notebook" side, range
  shifted), rerun of the full suite passed.
- No other gate failed; no gate was rerun more than once except where a fix required it.

## 11. Deviations and items for user attention

- **Cell count (32) is below the spec's "approximately 35-45" guidance.** Given the strong,
  repeated emphasis elsewhere in the spec on conciseness ("substantially shorter than Exercise
  1," "avoid unnecessary theory," "practice after the lecture, not reteach the entire
  lecture"), I judged a tighter notebook the better trade-off rather than padding it to hit
  the count. Flagging for your review in case you'd prefer more granularity regardless.
- **`scripts/smoke_portable_notebook.py` was not extended** to cover Chapter 7 — it already
  hardcodes only chapters 1-4 and was never extended for chapters 5 or 6 either, so Chapter 7
  follows the same (pre-existing) gap. I instead smoke-executed the portable notebook manually
  in a fresh temp directory (§9, row 7) and it passed; this is not wired into the automated
  suite.
- **No automated dark-mode toggle test was added** for the two new activities specifically
  (`interactive/e2e-book/wp22-cross-chapter-dark-mode.spec.ts` covers a curated subset of
  existing chapters, not every activity ever added). I instead verified manually (§9, row 14)
  that the shared theme infrastructure both widgets already use (`theme.ts`,
  `plotly-policy.ts` — identical to every other activity) behaves correctly. The transparent-
  background/locked-axes policy itself *is* covered automatically, via the 3 new
  `plot-visual-policy.spec.ts` entries.
- The Play/Pause `data-testid="boosting-param-play-button"` toggles its own **text content**
  between "Play" and "Pause" (plus `aria-pressed` and `container.dataset.playing`) rather than
  keeping a fixed label with a separate state indicator — this was a design choice for
  clarity, not dictated by the spec; flagging in case a fixed label was expected.
- One Playwright test (`Pause stops advancement...`) and one (`no orphan timer...`) each use a
  short, bounded `page.waitForTimeout(700)` (a little over one configured Play interval) to
  positively confirm nothing changes/throws after pausing/reloading — permitted by WP32 §20's
  "event/state observation rather than a long real-time animation" wording, but flagging since
  it is technically a fixed wait, not pure polling.
