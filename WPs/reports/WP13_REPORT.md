# WP13 implementation report — Exercise 3: KNN and the Bias–Variance Tradeoff

## Outcome

Status: **SUCCESS**

WP13's KNN audit (`scripts/knn_model_audit.py`) found **no curse-of-dimensionality
problem** for standardized KNN regression on Exercise 2's exact canonical
`age` recipe (all-eligible bilateral cortical thickness, p=358): 5-fold
cross-validation on the training partition only selected **k=15**, and the
locked held-out test score (**R²=0.647, MSE=33.0**) beat both of the smaller
predeclared anatomical bundles tested (frontoparietal p=78: R²=0.477;
occipital p=46: R²=0.425) and beat Exercise 2's own OLS result (R²=0.475) on
the *identical* participants, split, target, and feature set. Per the WP's
decision policy this kept the canonical recipe as the standard example
(no bundle swap needed). A new notebook
(`book/chapters/chapter_03/exercise_03.ipynb`, 34 cells) implements the
standard KNN workflow, honest-vs-invalid evaluation (with an added explicit
k=1 resubstitution demonstration, since the k=15 A/B/C gap turned out small),
a labelled conceptual bias–variance graph, and a from-scratch empirical
fitting/validation curve over every integer k from 1 through 564 on a
development split of Exercise 2's training partition — verified to predict
the fitting-set mean exactly at k=N_fit, and never touching or retuning
against the locked outer test set. A new interactive "vary k" activity
lets students move k from 1 through 564 and see fitting/validation error and
an observed-vs-predicted scatter recompute live, entirely client-side, with
predictions validated bit-for-bit against a real `KNeighborsRegressor`.
Exercise 1 and Exercise 2 are unchanged and verified so. No push, merge,
deployment, or destructive git command occurred.

| Check | Before WP13 | After WP13 |
|---|---|---|
| Frontend typecheck | PASS | PASS |
| Frontend unit (`vitest`) | 217 / 217 | **237 / 237** |
| `npm audit --omit=dev` | 0 vulnerabilities | 0 vulnerabilities |
| Widget artifacts `export_widget_data.py --check --artifact all` | 3 valid + canonical | 3 valid + canonical (unchanged) |
| Modelling manifest `abide_modeling_data.py --check` | self-consistent | self-consistent (+ new `knn` block) |
| Regression audit `regression_model_audit.py --check` | self-consistent | self-consistent (unchanged) |
| Regression catalog `export_regression_catalog.py --check` | valid + canonical (age, n=1004) | valid + canonical (unchanged) |
| KNN audit `knn_model_audit.py --check` | (new) | **self-consistent** |
| KNN explore data `export_knn_explore_data.py --check` | (new) | **valid + canonical** |
| Python unit (`unittest discover -s tests`) | 184 / 184 | **241 / 241** |
| Portable notebooks `build_portable_notebook.py --check` | up to date (ch1: 75, ch2: 33) | up to date (ch1: **75, byte-identical**, ch2: **33, byte-identical**, ch3: **36, new**) |
| Portable smoke (out of repo, network) | ch1: 20, ch2: 13 code cells | ch1: **20**, ch2: **13**, ch3: **16** code cells, key values matched |
| Standalone Playwright | 60 / 60 | **74 / 74** |
| Built-book Playwright | 26 / 26 | **33 / 33** |
| Clean Jupyter Book build | succeeded, 2 warnings | succeeded, **2 warnings** (same two pre-existing) |
| `*.err.log` guard | empty | empty |
| 2× consecutive clean builds, deterministic figures | identical (9 PNGs) | **identical (13 PNGs)** |

The two build warnings are the pre-existing `logo file 'logo.png' does not
exist` and `book/README.md: document isn't included in any toctree`. No new
warning was introduced.

Before-column baseline was re-verified against the actual pre-edit tree
(4081bf5) prior to any WP13 change: Python 184/184, frontend 217/217,
standalone e2e 60/60, built-book e2e 26/26 — all matched the WP12 report's
own final numbers.

## 1. Branch, checkpoint, baseline (WP13 §0)

- Confirmed `feature/regression-practice` HEAD was `4081bf5` (`WP12 report:
  document Exercise 2 corrections and model audit`) with one untracked file
  (`WPs/WP13_EXERCISE_3_KNN_AND_BIAS_VARIANCE.md`) and an otherwise clean
  tree.
- **Checkpoint commit `863c7dfaab3bb3352a4d6400294bcfe0334bfd7c`**
  (`checkpoint: before WP13`) — adds the WP brief only (1 file, +353).
- **Annotated tag `wp13-start`** → `863c7df` (tag object
  `b4c5d2443d50c4b275cf244859800d779f1c8ecd`). The name was free; no numeric
  suffix needed.
- Work continued on **`feature/regression-practice`** (the existing Exercise
  feature branch), not a new child branch — the WP's own preference.
- **Implementation commit `f327e4cb0b8c17de94065a83efb002e2cbb4e653`**
  (`WP13: Exercise 3 - KNN regression and the bias-variance tradeoff`) — 27
  files changed, 5286 insertions(+), 7 deletions(-).
- No `git reset --hard`, `git checkout -- <path>`, `git clean`, `git rebase`,
  `git revert`, force-push, or tag/branch deletion at any point.

## 2. Inspection before writing (WP13 §1)

Read, in full, before making any content decision: `exercise_02.ipynb` (all
31 cells, provenance, split, pipeline, iframe/Colab/download wiring),
`scripts/build_portable_notebook.py`, `scripts/abide_modeling_data.py`,
`book/config/abide_modeling.json`, `scripts/export_regression_catalog.py`,
`interactive/src/regression-compare*.ts` and its component, the widget
`config.ts` schema/registry/`main.ts`, `book/_toc.yml`,
`book/_static/launch-buttons.js`, `book/_static/custom.css`,
`tests/test_exercise_02_notebook.py`, `tests/test_regression_model_audit.py`,
`tests/test_export_regression_catalog.py`, `tests/test_build_portable_notebook.py`,
`tests/test_book_structure.py`, and the existing Playwright specs (standalone
and built-book). Exercise 2 is used as the literal source of truth for data
provenance, the canonical feature recipe, the locked outer split, the
green run/download block, the portable-notebook derivation pattern, and the
static/offline interactive-activity architecture (one Vite SPA driven by a
`?config=` query parameter, never a page per activity).

## 3. The KNN audit (WP13 §1) — the empirical gate for the notebook's example

**Script:** `scripts/knn_model_audit.py` (`--run` writes / `--check`
re-validates `scripts/knn_model_audit_result.json`, SHA-256
`7281a1b446d8fe6874932d82062385ce994b84179787e6db0da8c2c01a7e50ab`).
Deterministic, reproducible byte-for-byte across two independent `--run`
invocations in two different Python environments during this WP (system
Python 3.12 / numpy 2.5.1 / scipy 1.18.1, and the project `.venv` / numpy
2.5.3 / scipy 1.18.1) — every field except `runtime_seconds` was identical.

### 3.1 Design (WP13 §1)

- Model: `Pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=k))`;
  scaler fit on training rows / training folds only, exactly like Exercise
  2's OLS pipeline.
- **k selection**: `KFold(n_splits=5, shuffle=True, random_state=0)` on the
  **outer-training partition only** (753 rows) — the same cross-validation
  protocol Exercise 2's manifest already documents
  (`protocol.cross_validation`). Evaluated at a representative, log-spaced
  grid of k spanning **1 through 602** (`k_grid_max_valid_in_cv`, the largest
  k valid inside that 5-fold CV — a fold's own training size, 753×4/5≈602),
  not every integer (a full even grid is a separate thing Section 4.5 of the
  notebook computes from scratch). k* = argmax mean CV R², ties toward the
  smaller k.
- **Special endpoint**: k equal to every participant in the fitting set —
  evaluated as a diagnostic never used for selection, fit once on the full
  753-row training partition with `k=753` and scored on the untouched 251-row
  test set. Structurally verified that every prediction equals the
  training-partition mean (`all_predictions_equal_training_mean: true` for
  every candidate).
- **Locked test evaluation**: exactly Exercise 2's own outer split
  (`train_test_split(test_size=0.25, random_state=42, stratify=group)`),
  touched **exactly once per candidate**, after k is already fixed by the
  training-only procedure above. Verified by
  `tests/test_knn_model_audit.py::LockedTestIsolation` (mocks
  `KNeighborsRegressor.fit` to prove the final model's `.fit()` is called
  exactly once, with exactly the 753 training rows, never the 251 test rows).
- **Feature spaces** (all predeclared before any score was seen): the exact
  Exercise 2 canonical recipe (`all-eligible × CT`, p=358) plus two
  already-reviewed smaller anatomical bundles from
  `book/config/abide_modeling.json` — `frontoparietal` (p=78, the P-FIT
  bundle) and `occipital` (p=46) — to assess the effect of dimensionality, as
  the WP asked. No feature was chosen by looking at its association with
  `age`.

### 3.2 Full audit table

| feature space | p | n_train | n_test | k_max (CV-valid) | selected k | k=1 CV R² | selected-k CV R² | selected-k CV MSE | locked test R² | locked test MSE | k=N_fit test R² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all-eligible × CT (**canonical**) | 358 | 753 | 251 | 602 | **15** | +0.452 | **+0.598** | 34.46 | **+0.647** | 33.0 | −0.0003 |
| frontoparietal × CT (P-FIT) | 78 | 753 | 251 | 602 | 82 | −0.155 | +0.362 | 54.99 | +0.477 | 48.8 | −0.0003 |
| occipital × CT (comparison) | 46 | 753 | 251 | 602 | 20 | +0.081 | +0.475 | 45.55 | +0.425 | 53.6 | −0.0003 |

Runtime: 12.49s (system Python), 9.2s (first run, `.venv`) — recorded per run
in the committed JSON's `runtime_seconds` field, not asserted as a fixed
value (machine-dependent).

### 3.3 Decision (WP13 §1)

- **No curse-of-dimensionality problem was observed.** The 358-feature
  canonical recipe scored *highest* of the three candidates on both the
  training-only CV metric (+0.598) and the locked test metric (+0.647) — the
  opposite of what a naive "more features hurts KNN" prior would predict for
  this dataset/recipe. Both smaller bundles (well inside the range where
  distance concentration is a real risk) scored lower on every metric.
- Since the canonical recipe is both the strongest candidate *and* the one
  that keeps the notebook's Exercise-2 comparison valid (same participants,
  split, target, and feature set — WP13 §4.2's explicit condition for showing
  that comparison), the canonical `all-eligible × CT` recipe was retained as
  the notebook's one standard configuration. No bundle swap was needed.
- **k=15** was locked from the training-only CV curve and evaluated exactly
  once on the outer test set: **R²=0.647, MSE=33.0 (RMSE 5.7 years)**,
  compared with **R²=0.475, MSE=49.0** for Exercise 2's OLS on the identical
  753/251 split and 358-feature recipe. This is reported in the notebook as
  one specific comparison, not a universal KNN-vs-linear-regression claim
  (explicit wording in `wp13-028`, asserted by
  `test_no_...` — see `tests/test_exercise_03_notebook.py`).

## 4. Sample sizes (canonical, development, outer-test)

| Partition | n | Role |
|---|---:|---|
| Full usable cohort (`age` available) | 1004 | source for the outer split |
| Outer training partition | 753 | Exercise 2's own `train_test_split` training rows, reused verbatim |
| Outer test partition | 251 | locked; touched exactly once per reported model |
| Development fitting subset (`N_fit`) | 564 | further split of the 753 outer-training rows (`test_size=0.25, random_state=7, stratify=group`), used only by Section 5 (notebook) and the interactive activity |
| Development validation subset (`N_val`) | 189 | same split; never touches the outer 251-row test set |

## 5. Selected k, procedure, and final metrics (notebook Section 2)

- **k = 15**, selected by 5-fold cross-validation on the 753-row outer-training
  partition only (`scripts/knn_model_audit.py`), then locked before the
  outer test set was touched.
- **Held-out (outer test) R² = 0.647, MSE = 33.0 (RMSE 5.7 years)**, on the
  same 358-feature, 753/251-participant recipe as Exercise 2.
- **Compared with Exercise 2's OLS on the identical data: R² = 0.475.**
  Reported as one specific, non-universal comparison (see §3.3 above).

## 6. Honest evaluation versus invalid alternatives (notebook Section 3)

### 6.1 At the reported k=15 (same fixed k and recipe throughout)

| | fit on | evaluated on | R² | MSE |
|---|---|---|---:|---:|
| A. correct | training rows | test rows | **0.647** | 32.99 |
| B. training score (resubstitution) | training rows | training rows | 0.659 | 29.77 |
| C. invalid (leakage) | test rows | same test rows | 0.650 | 32.69 |

A, B, and C are **close together** at k=15 (all ≈0.65) — a fairer, less
dramatic picture than Exercise 2's OLS example (A=0.475, B=0.845, C=1.000),
because averaging over 15 neighbours limits how optimistic either
resubstitution or the invalid fit-on-test model can be. Per WP13 §4.3, since
the audit-selected k did **not** make the optimism visually dramatic, an
explicit small k=1 demonstration was added.

### 6.2 The added k=1 demonstration (explicitly labelled, not the reported model)

| | R² |
|---|---:|
| A. correct (held-out, k=1) | 0.553 |
| B. training score (resubstitution, k=1) | **1.000** |
| C. invalid (leakage, k=1) | **1.000** |

At k=1, B and C are both a **perfect 1.000** — every fitted point is its own
nearest neighbour at distance zero, so the prediction exactly reproduces the
observation, by construction, not because anything was learned. A (0.553)
is *lower* than the k=15 model's held-out score, illustrating that a
perfect training score is not evidence of good generalisation. The two
`invalid_test_fitted_model*` objects are each assigned exactly once and never
referenced from any later cell
(`tests/test_exercise_03_notebook.py::test_invalid_leakage_models_are_clearly_named_and_isolated_to_their_own_cell`).

## 7. Behaviour at k=1, the validation optimum, and k=N_fit (notebook Section 5 / interactive)

Computed once (notebook, self-contained) and independently once more
(`scripts/export_knn_explore_data.py`, the committed interactive artifact);
both agree bit-for-bit.

| k | fitting R² | fitting MSE | validation R² | validation MSE |
|---|---:|---:|---:|---:|
| 1 | **1.000** (trivial resubstitution) | 0.0 | 0.335 | 48.0 |
| 17 (**validation-optimal**) | 0.614 | 35.7 | **0.634** (best) | 26.3 |
| 564 = N_fit (**every fitting participant**) | **≈0.000** | 93.4 | −0.004 | 93.7 |

- **k=1**: fitting R²=1.0 exactly (every fitting point is its own nearest
  neighbour); validation R²=0.335 — much worse, showing the perfect fitting
  score is a high-variance artefact, not generalisation.
- **Validation optimum, k=17**: not identical to the audit's training-only
  selected k=15 — expected, since they come from different splits of
  different data (the audit's 5-fold CV on 753 rows vs. this section's single
  564/189 fit/validation split); the notebook says so explicitly
  (`wp13-055`).
- **k=N_fit=564**: fitting R²≈0.0 exactly (the constant training-mean
  predictor scored against its own fitting data has R²=0 by construction) and
  **every validation prediction equals the fitting-set mean, 15.192 years** —
  verified structurally in the notebook
  (`assert np.allclose(pred_val_at_k_nfit, y_fit.mean())`, `wp13-053`) and
  independently in `tests/test_export_knn_explore_data.py` and
  `interactive/tests/knn-explore-data.test.ts`.

This empirical curve is exploratory: it **never retunes** the Section 2
model. The outer test set is not read anywhere in Section 5's code (verified
by `tests/test_exercise_03_notebook.py::test_dev_split_is_independent_of_the_outer_test_set`,
which asserts `X_test`/`y_test` do not appear in that section's source).

## 8. Interactive artifact structure and privacy checks

- **Config:** `book/_static/widgets/configs/knn_explore.json` (new activity
  type `knn-explore`, registered in `interactive/src/config.ts` as a
  discriminated-union member and in `interactive/src/components/registry.ts`).
  `defaultK: "validation-optimal"` resolves at mount time to whatever the
  committed data's `validationOptimalK` field says (17), rather than being
  hardcoded, so the widget and the notebook cannot silently drift apart.
- **Data:** `book/_static/widgets/data/abide_knn_explore.json` (697,322
  bytes; SHA-256 `f13dbf8715368f85ad784e07fd2db8c9b534832db26139b1f70d30f953aacfec`),
  produced by `scripts/export_knn_explore_data.py --refresh`. Contents:
  - `observedValidation` (189 age values) and `observedFitting` (564 age
    values) — target values only;
  - `neighborTargetsByProximity`: for each of the 189 validation
    participants, the 564 fitting-set **age values** (not features, not
    distances) reordered nearest-first. The browser derives the prediction
    for any chosen k as the mean of the first k entries of the relevant row —
    a genuine client-side recomputation, validated once offline (in the
    export script, before writing) against a real
    `Pipeline(StandardScaler(), KNeighborsRegressor(k))` at k ∈ {1, 5, 15,
    17, 50, 200, 564}, all matching to floating-point precision (`atol=1e-6`);
  - a precomputed `curve` (per-k fitting/validation R²/MSE for every
    k=1..564), computed via the same sort-once/cumulative-sum trick, used for
    the second (error-vs-k) plot.
  - **No participant identifiers, no raw brain features, no site/diagnosis
    column** anywhere in the artifact — enforced structurally by
    `validate_artifact`'s identifier-key scan and by
    `tests/test_export_knn_explore_data.py::test_contains_no_participant_identifier`
    and the TypeScript schema's own `IDENTIFIER_TOKEN` check
    (`interactive/src/knn-explore-data.ts`).
- **Component:** `interactive/src/components/knn-explore.ts` — a single k
  slider (`1..564`, native `<input type="range">`, keyboard-operable,
  `aria-label`ed), current k / fitting R²·MSE / validation R²·MSE text, an
  observed-vs-predicted validation scatter (Plotly), a fitting/validation
  MSE-vs-k curve with a marker at the current k (log-scaled k axis), and
  static endpoint explanations at k=1 and k=N_fit. State lives only in DOM/JS
  memory (no `localStorage`), so a browser refresh naturally restores the
  configured default — verified by
  `interactive/e2e/knn-explore.spec.ts::"browser refresh restores the
  configured default k"` and the built-book equivalent.
- **Scaling on/off comparison** (WP13 §4.6, explicitly optional): **not
  added**, to keep the activity focused and concise, per the WP's own "only
  if it remains concise" condition. Documented as a deliberate omission, not
  an oversight.

## 9. Notebook (WP13 §2–§4, §7)

`book/chapters/chapter_03/exercise_03.ipynb`, 34 cells (14 markdown, 20
code — 1 `hide-cell` data loader, 4 `hide-input` figures, 15 visible),
authored via a scratch nbformat script (not committed, per the same pattern
WP12 used) and executed end-to-end twice (system Python and the project
`.venv`; both clean, zero execution errors, zero `stderr` output, identical
printed values). `nbformat.validate` OK; every cell id is `wp13-*` and
unique. SHA-256
`7ae116f3470d7f4ee21b63035cefde32c8a48db049cf6070cd99ec31e1aa8b8a`.

- **Title / opening** — H1 `# Exercise 3: KNN and the Bias–Variance
  Tradeoff` (Arabic numbering). Opening states KNN regression (averaging)
  and, briefly, that KNN also does classification by voting among neighbours
  — a forward pointer only, never taught here (asserted by
  `test_classification_mentioned_only_as_forward_looking`, which checks the
  word appears in no heading and at most 3 times total in the notebook's
  markdown). No time budget.
- **§1 The modelling table** — reloads the same two pinned public CSVs
  Exercise 2 uses (self-contained; no repository dependency, no cross-notebook
  import), with a compact 3-row/6-column preview only (no re-taught EDA).
- **§2 One standard KNN regression workflow** — the *exact same* feature
  recipe cell as Exercise 2's `wp11-021` (byte-identical non-comment source,
  asserted by test) and the exact same locked split
  (`test_size=0.25, random_state=42, stratify=groups`) → n_train=753,
  n_test=251. `k=15`. Held-out **R²=0.647, MSE=33.0**. A compact, clearly
  caveated OLS comparison, computed live in this notebook (not just quoted
  from Exercise 2), reusing the identical split/recipe/target.
- **§3 Honest evaluation versus invalid alternatives** — the k=15 A/B/C
  table, plus the added, explicitly labelled k=1 demonstration described in
  §6 above.
- **§4 The classic bias–variance tradeoff** — the squared-error
  decomposition equation, small-k/large-k bullets, and a synthetic
  conceptual figure whose title literally contains "CONCEPTUAL, not
  estimated from ABIDE data" (asserted by
  `test_conceptual_graph_is_explicitly_labelled_not_estimated`).
- **§5 From k=1 to every participant: an empirical curve** — the from-scratch
  fit/validation development curve described in §7 above, with a two-panel
  figure (MSE-vs-k with k=1 / validation-optimal / k=N_fit markers, log
  k-axis; validation R²-vs-k with the optimum annotated), and an explicit
  admonition stating the curve is *consistent with*, not a *direct
  measurement of*, bias and variance.
- **§6 Explore k yourself** — the `knn-explore` iframe (same one-SPA,
  `?config=` pattern as Exercise 2's activity), with three Think-first
  prompts.
- **In summary / Questions to take away** — five-point summary; the
  classification forward-pointer appears once more here (its only other
  mention besides the opening); seven questions matching the WP's list.

## 10. Page controls, TOC, and Colab/download destinations (WP13 §2)

- `book/_toc.yml`: `chapters/chapter_03/exercise_03` added immediately after
  `chapters/chapter_02/exercise_02`. Sidebar/Contents render "Exercise 3: KNN
  and the Bias–Variance Tradeoff" (confirmed in the built-book screenshot,
  §12 below).
- `book/_static/launch-buttons.js`: `PAGE_TO_PORTABLE` extended with
  `chapters/chapter_03/exercise_03.html` →
  `book/downloads/chapter_03/exercise_03_portable.ipynb`. Verified, per
  chapter, that the opening-admonition links and the header Colab button both
  point at that chapter's own portable notebook and never another chapter's
  (`interactive/e2e-book/launch-buttons.spec.ts`, now 3 chapters × 3 tests +
  1 no-mapping test = 10 tests, all passing).
- Exercise 1 and Exercise 2's own `_config.yml` / `custom.css` /
  `launch-buttons.js` entries are untouched (only the new chapter_03 map
  entry was added); their notebooks are not in this commit's diff at all,
  and their portable notebooks were re-verified byte-identical.

## 11. Portable notebook and generator (WP13 §5)

- `scripts/build_portable_notebook.py`: new `CHAPTER_03` `NotebookSpec`
  (banner, setup text, `lesson_packages="numpy pandas matplotlib
  scikit-learn"`, iframe replacement keyed on the Exercise 3 activity's exact
  `<iframe title="...">`, `colab_title="Exercise 3: KNN and the
  Bias-Variance Tradeoff"`); `NOTEBOOKS` dict extended. The iframe-replacement
  text points at "Section 5 above" (the notebook's own from-scratch
  matplotlib k-exploration) rather than duplicating a non-existent extra
  cell, satisfying WP13 §5's "non-interactive Python/Matplotlib version of
  the k exploration where practical" requirement with the content the
  notebook already has.
- `book/downloads/chapter_01/exercise_01_portable.ipynb` and
  `book/downloads/chapter_02/exercise_02_portable.ipynb` verified
  **byte-for-byte identical** to before WP13 (`--check` → "up to date"; not
  present in this commit's diff).
- **`book/downloads/chapter_03/exercise_03_portable.ipynb`** generated, 36
  cells (34 canonical + banner/setup/install − 1 dropped "Run or download"
  admonition). SHA-256
  `1819c36faf4dbb367cd774d134ebac350a5c11d83373221299221aa5a80b23ab`. No MyST
  directive, iframe, `_static/` path, repository-relative config path,
  `requirements.txt` instruction, hide tag, active install command, or
  self-referential Colab link (all asserted by `_assert_portable`, which
  ran during generation). Out-of-repo smoke run: **16 code cells**; key
  values (`age available for 1004 of 1004`, `k = 15`, `held-out R^2 =
  0.647`, `N_fit = 564   N_val = 189`, the k=N_fit endpoint sentence) all
  matched.
- `scripts/smoke_portable_notebook.py`: `chapter_03` entry added with those
  expected strings; `chapter_01`/`chapter_02` entries unchanged.

## 12. Required validation (WP13 §7) — commands and results

1. **Notebook validation, unique cell ids, current outputs, no stale
   Exercise 2/FIQ wording** — `nbformat.validate` (via
   `tests/test_exercise_03_notebook.py`) — PASS; 34 unique `wp13-*` ids; no
   execution errors or stderr in any committed output.
2. **Data provenance, split identity with Exercise 2, feature leakage
   guards** — asserted in `test_exercise_03_notebook.py`
   (`test_canonical_feature_recipe_matches_exercise_2_and_the_manifest`,
   `test_locked_split_matches_exercise_2`,
   `test_notebook_code_has_the_leakage_guard`) — PASS.
3. **Audit reproducibility and training-only k-selection tests** —
   `python -m unittest discover -s tests -p 'test_knn_model_audit.py'`
   (16/16) — PASS. Two tests directly **mock `KNeighborsRegressor.fit`** to
   prove, not just assert, that (a) every CV fold's k-selection fit sees
   exactly that fold's own training rows (never the full training partition,
   never the outer test rows), and (b) the locked test evaluation's final
   `.fit()` is called exactly once, with exactly the 753 training rows.
4. **Exact endpoint tests** (k=1; k=N_fit equals fitting-target mean) —
   `test_export_knn_explore_data.py::test_endpoint_k1_is_perfect_resubstitution`,
   `test_endpoint_k_equals_n_fit_is_the_constant_mean_predictor`,
   `test_k_equals_n_fit_predicts_a_single_constant_for_every_validation_row`
   — PASS; also asserted inside the notebook itself (`wp13-053`) and in the
   TypeScript schema (`interactive/tests/knn-explore-data.test.ts`).
5. **Independent R²/MSE recomputation for all stored interactive
   predictions** — `export_knn_explore_data.py`'s own `validate_artifact`
   recomputes the k=1 / k=N_fit endpoints structurally from the stored
   arrays on every `--check`; `interactive/tests/knn-explore-data.test.ts`
   does the same client-side-schema recomputation for the committed
   artifact.
6. **Representative fast predictions checked against scikit-learn** — the
   export script's `_validate_against_sklearn` fits real
   `KNeighborsRegressor` models at k ∈ {1, 5, 15, 17, 50, 200, 564} and
   compares to the cumulative-sum predictions (`atol=1e-6`) before the
   artifact is ever written; re-verified in
   `tests/test_export_knn_explore_data.py`.
7. **Python test suite** — `.venv/bin/python -m unittest discover -s tests`
   → **241 / 241** — PASS (up from 184; +57: +16
   `test_knn_model_audit.py`, +15 `test_export_knn_explore_data.py`, +26
   `test_exercise_03_notebook.py`, and `test_book_structure.py`'s TOC test
   updated in place for the 3-chapter order).
8. **TypeScript typecheck, unit tests, production build** —
   `npm run typecheck` PASS; `npm run test:unit` → **237 / 237** PASS (up
   from 217: +9 `knn-explore-data.test.ts`, +5 `knn-explore.test.ts`, +6 new
   `config.test.ts` cases for the `knn-explore` config type); `npm run
   build` — succeeded (pre-existing 500 kB Plotly-chunk advisory only,
   unchanged).
9. **Standalone Playwright, every activity including the new one** —
   `npx playwright test` → **74 / 74** PASS (60 unchanged + 14 new
   `knn-explore.spec.ts`, both at the site root and the simulated project
   subpath).
10. **Portable-notebook freshness + out-of-repo smoke, all three chapters**
    — `python scripts/build_portable_notebook.py --check` PASS (ch1/ch2
    byte-identical, ch3 up to date); `python scripts/smoke_portable_notebook.py
    --notebook all` → all three **OK** (20 / 13 / 16 code cells), key values
    matched, network.
11. **Clean Jupyter Book build** — `rm -rf book/_build && jupyter-book build
    book` (`.venv`) → succeeded, **2 warnings** (both pre-existing, none
    new); `find book/_build -name '*.err.log'` → empty.
12. **Built-book Playwright, GitHub Pages subpath** — `npm run
    test:e2e:book` → **33 / 33** PASS (26 unchanged + 4 new
    `chapter03.spec.ts` + 3 new `launch-buttons.spec.ts` Chapter-3 cases).
13. **Visual checks, desktop + 390 px** — Playwright screenshots of the
    Chapter 3 activity taken at 1280 px and 390 px: sidebar entry reads
    "Exercise 3: KNN and the Bias–Variance Tradeoff", Colab header button
    present, k-slider/metrics/scatter/curve all render correctly, no
    horizontal overflow at 390 px (`overflow <= 1px`, asserted by the
    narrow-viewport tests in both `knn-explore.spec.ts` and
    `chapter03.spec.ts`).
14. **Exercises 1 and 2 remain functional** — their own Playwright specs
    (standalone and built-book) are unchanged and still pass in full; their
    portable notebooks are verified byte-identical; their canonical
    notebooks are not present in this commit's diff.

**Manual verification performed:** moving the k slider in the live activity
changes the scatter plot, the curve-plot marker, and every displayed metric
together (not just a label) — confirmed both by the automated Playwright
assertions (metrics-text change + render-count increment together) and by
direct screenshot inspection at k=17 (default), k=1, and k=564. Browser
refresh restores the configured default k=17 — confirmed by the dedicated
refresh tests in both the standalone and built-book specs.

Two independent clean `jupyter-book build` runs (this WP) produced
byte-identical figure hashes across all **13** committed PNGs (9 from
Exercises 1–2, unchanged, + 4 new from Exercise 3).

## 13. Exact files changed

Implementation commit `f327e4c` — 27 files changed (10 modified, 17 new).
See `WP13_EXACT_CHANGELOG.md` for the location-specific before/after.

**Untouched (verified byte-identical or absent from the diff):**
`book/chapters/chapter_01/exercise_01.ipynb`,
`book/chapters/chapter_02/exercise_02.ipynb`,
`book/downloads/chapter_01/exercise_01_portable.ipynb`,
`book/downloads/chapter_02/exercise_02_portable.ipynb`,
`book/_static/widgets/data/abide_regression_models.json`,
`book/_static/widgets/data/abide_histogram.json`,
`book/_static/widgets/data/abide_retention.json`,
`book/_static/widgets/data/abide_table_inspection.json`,
`book/_static/widgets/configs/regression_compare.json`,
`scripts/regression_model_audit.py`,
`scripts/regression_model_audit_result.json`,
`scripts/export_regression_catalog.py`, `scripts/abide_modeling_data.py`,
`interactive/src/regression-compare.ts`,
`interactive/src/regression-compare-data.ts`,
`interactive/src/components/regression-compare.ts`, `book/contents.md`,
`book/intro.md`, `book/syllabus.md`, `book/_config.yml`,
`book/_static/custom.css`.

## Warnings, deviations, deferred / not-performed

1. **Environment note (not a deviation, documented for reproducibility):**
   this machine's system Python initially had numpy 2.5.1 / scipy 1.14.1,
   an incompatible pairing that produced a benign `UserWarning` on every
   `import sklearn` — which would have shown up as committed notebook
   stderr. Upgraded `scipy` to 1.18.1 (matching the project's own `.venv`)
   to fix the root cause rather than suppressing the symptom; re-verified
   every numeric result was unchanged before and after (byte-identical audit
   JSON, byte-identical `abide_knn_explore.json`, identical notebook
   printed values) in both environments. No repository file depends on this;
   it is a one-time local environment fix.
2. **Scaling on/off comparison not added to the interactive activity** —
   WP13 §4.6 marks this explicitly optional ("only if it remains concise");
   omitted to keep the activity focused, per §8 above.
3. **The k=1 special demonstration was needed and added** — WP13 §4.3
   anticipated this exact situation ("If the audit-selected k does not make
   the optimism visually clear, add a small, explicitly labeled k=1
   demonstration") and it applied here: at k=15 the A/B/C gap is modest
   (0.647/0.659/0.650). Added per the WP's own instructions, not a deviation.
4. **Colab interactive rendering not machine-verified** (Google serves an
   app shell to headless automation — unchanged limitation from WP07–WP12).
   The article-header button's `href`, the opening admonition's links, and
   the portable notebook's own `metadata.colab.name` are all covered by
   tests instead.
5. **No live / remote checks** — by the stop condition: no push, no `main`
   merge, no deployment. GitHub Pages still serves the WP08–WP12 content;
   hosting and the private/public distribution architecture were not
   touched.
6. **Pre-existing warnings kept** — `logo.png` missing, `book/README.md` not
   in a toctree, the Vite 500 kB Plotly-chunk advisory. All unchanged, out
   of scope.
7. **Canonical Exercise 3 notebook executed end-to-end twice** (network:
   pinned `abide2.tsv` + phenotypic CSV; same two files Exercise 2 already
   uses) to arrive at clean, warning-free committed outputs; both
   executions and two full clean `jupyter-book` builds produced
   byte-identical figure hashes (13 PNGs) in this environment. The
   pre-existing cross-platform Matplotlib byte-difference risk
   (numpy/pandas/matplotlib unpinned in `requirements.txt`) is unchanged
   from prior WPs.
8. **The empirical development curve's validation-optimal k (17) is not the
   same as the audit's training-only selected k (15)** — expected and
   explained in the notebook itself (§7 above); not treated as a bug or
   reconciled by retuning either number.

## Unresolved risks / needs Yoav

- **Private-repository distribution** (carried from WP09–WP12 unchanged):
  the Colab / raw-download buttons and the article-header Colab button all
  target `github.com/yoavmp/ml-neuro-tutorials` on `main` and will break for
  non-collaborators if the repo goes private. Not in scope for WP13.
- **Merge / deployment of WP09–WP13** is a separate, later WP after review.
- **Classification** is the next practice, deliberately not started (only
  the two forward-looking mentions exist, as before).
- **Whether the k=1 vs. validation-optimal-k vs. audit-selected-k
  three-way distinction is pedagogically clear enough as written** is an
  editorial judgement beyond this WP's empirical mandate — the audit and the
  development curve are both honestly reported and internally consistent;
  Yoav may still prefer additional scaffolding around why the three numbers
  differ.

## Confirmation of safety constraints

- **No merge to `main`, no deployment, no push, no force push** — nothing
  left the local `feature/regression-practice` branch.
- **No destructive git command** — no `git reset --hard`,
  `git checkout -- <path>`, `git clean`, `git rebase`, `git revert`, tag or
  branch deletion.
- **No repository-setting / hosting / Pages / distribution-architecture
  change.**
- **No generated build output committed** — `book/_build`,
  `book/.jupyter_cache`, `book/_static/widgets/app`,
  `interactive/node_modules`, `interactive/test-results`, `__pycache__`
  remain untracked / git-ignored (confirmed via `git check-ignore -v` and
  `git status` before this commit).
  `book/config/abide_modeling.json`, `book/_static/widgets/data/abide_knn_explore.json`,
  and `scripts/knn_model_audit_result.json` are committed source/reviewed
  assets, not build output.
- **Exercise 1 and Exercise 2 content unchanged** — neither canonical
  notebook is in this commit's diff at all; both portable notebooks are
  verified byte-identical; only the shared `book/_toc.yml` and
  `book/_static/launch-buttons.js` (documented in §10) touch them, and only
  additively (a new TOC entry, a new map key).
- **No held-out test score was consulted to choose the feature space, k, or
  the standard configuration** — every selection came from the
  training-only 5-fold CV procedure or was predeclared before any score was
  seen; `tests/test_knn_model_audit.py`'s two isolation tests verify this
  structurally, not just by inspection.
- **The outer test set is never touched by the all-k development curve or
  the interactive activity** — both derive entirely from the 753-row
  outer-training partition; verified structurally
  (`test_dev_split_is_independent_of_the_outer_test_set`).
- **No WP14 created, no classification exercise begun.** Stopping here per
  the WP's stop condition.

## Key identifiers

| Item | Value |
|---|---|
| Branch | `feature/regression-practice` (unchanged, off `4081bf5`) |
| Checkpoint commit | `863c7dfaab3bb3352a4d6400294bcfe0334bfd7c` (`checkpoint: before WP13`) |
| Checkpoint tag | `wp13-start` → `863c7df` (annotated; tag object `b4c5d2443d50c4b275cf244859800d779f1c8ecd`) |
| Implementation commit | `f327e4cb0b8c17de94065a83efb002e2cbb4e653` (`WP13: Exercise 3 - KNN regression and the bias-variance tradeoff`) — 27 files, 5286 insertions(+), 7 deletions(-) |
| Report commit | adds `WPs/reports/WP13_REPORT.md` + `WPs/reports/WP13_EXACT_CHANGELOG.md` only — SHA in the terminal summary |
| Modelling manifest | `book/config/abide_modeling.json` SHA-256 `9933abde1ca621db0808cb7510cf0e011ff1fd501502fed54c407a7cac9fbef5` |
| KNN audit result | `scripts/knn_model_audit_result.json` SHA-256 `7281a1b446d8fe6874932d82062385ce994b84179787e6db0da8c2c01a7e50ab` |
| KNN explore data | `book/_static/widgets/data/abide_knn_explore.json` SHA-256 `f13dbf8715368f85ad784e07fd2db8c9b534832db26139b1f70d30f953aacfec` |
| Canonical notebook | `book/chapters/chapter_03/exercise_03.ipynb` SHA-256 `7ae116f3470d7f4ee21b63035cefde32c8a48db049cf6070cd99ec31e1aa8b8a` |
| Portable notebook | `book/downloads/chapter_03/exercise_03_portable.ipynb` SHA-256 `1819c36faf4dbb367cd774d134ebac350a5c11d83373221299221aa5a80b23ab` |

## Instructions for reviewer

Paste this entire report (`WP13_REPORT.md`) into the ChatGPT conversation
that produced WP13. `WP13_EXACT_CHANGELOG.md` is the companion
location-specific before/after record.
