# WP19 Report — Remove early cross-validation and parameter tuning

## Completion status

**Complete, including one corrective continuation.** All required sections
executed: inventory, Exercise 3 (KNN) and Exercise 4 (classification)
revisions, Exercise 1/2 audit, course overview DOCX update, tests, final
validation gate, local merge to `main`. Local-only; nothing pushed or
deployed; WP20 not started.

## Correction: Exercise 2's hidden cross-validation removed

The original WP19 pass treated Exercise 2's regression-compare (feature-set
comparison) activity as out of scope, on the judgment that it was a
legitimate, previously-approved (WP11) evaluation methodology rather than a
"selection" procedure -- see the superseded "Judgment call" note below. Yoav
confirmed this was wrong: the activity's hidden 5-fold `KFold` +
`cross_val_predict` procedure is itself early-course cross-validation and
had to go, regardless of whether it selects a hyperparameter. This
correction replaces it with one fixed, reproducible train/test split,
identical to Exercise 2 Section 2 / Exercise 3's own outer holdout
(`train_test_split(test_size=0.25, random_state=42, stratify=group)`).

**What changed** (`scripts/export_regression_catalog.py` and everything it
feeds):

- The catalog builder no longer imports or calls `KFold` / `cross_val_predict`
  / `cross_val_score` anywhere. It computes one shared `(idx_train, idx_test)`
  split (753 train / 251 test participants, the same split used by every
  other exercise for the `age` target) once, and reuses those exact indices
  for every bundle x measurement-subset combination -- so every comparison
  still shares the same held-out participants, just via a fixed split
  instead of aggregated out-of-fold predictions.
- `StandardScaler` and `LinearRegression` are fit once each, on the training
  participants only; R² and MSE are computed once, on the held-out test
  participants only (not recomputed per fold and aggregated).
- The identifiability threshold (`p >= 0.7 * n`) now uses the training-set
  size (753) instead of the old per-fold training size (~803); no catalog
  entry's enabled/disabled status changed as a result (verified: the same
  single entry, `all-eligible__CT+Area` at p=720, remains the only disabled
  one).
- Artifact schema bumped to `schemaVersion: 2`: `crossValidation` and
  `foldOf` are gone; `holdoutSplit` (`testSize`, `randomState`, `stratify`,
  `nTrain`, `nTest`) replaces them; top-level `observed` (full cohort, 1004
  values) is replaced by `observedTest` (251 values, the held-out
  participants only); each model's `cvR2`/`cvMSE` fields are renamed
  `testR2`/`testMSE`.
- `book/config/abide_modeling.json`: `protocol.cross_validation` (the
  `KFold(n_splits=5, ...)` block) removed outright -- nothing else in the
  manifest referenced it. `catalog.identifiability_rule` and `catalog.note`
  reworded to describe the fixed split instead of folds/cross-validation.
- Frontend (`interactive/src/regression-compare-data.ts`,
  `regression-compare.ts`, `components/regression-compare.ts`): schema,
  types, and rendered text updated to the new field names
  (`holdoutSplit`/`observedTest`/`testR2`/`testMSE`); the unused
  `ScatterPoint`/`scatterPoints` helper (which carried a per-point `fold`
  field) was deleted as dead code that no longer has meaning. UI text changed
  from "cross-validated"/"out-of-fold" to "held-out"; the cohort line now
  states training and test participant counts separately.
- `book/_static/widgets/configs/regression_compare.json`: description,
  instructions, and the selection-bias note reworded to "held-out"/"train/test
  split" language, and the selection-bias note now explicitly says this
  activity is "exploratory model comparison, not feature selection or
  optimization."
- `scripts/build_portable_notebook.py`: the Exercise 2 portable notebook's
  iframe-replacement text ("...compares their cross-validated performance...
  and one fixed set of folds") reworded to "held-out performance... one fixed
  train/test split."
- The canonical `exercise_02.ipynb` needed **no further wording changes** --
  the earlier WP19 pass had already reworded its two passing
  "cross-validated"/"folds" mentions to neutral language ("one fixed
  evaluation procedure"), which reads correctly now that the procedure
  genuinely is a fixed split. No notebook code cell runs this activity's
  computation directly (it is iframe-only), so no notebook code changed.

**New Exercise 2 catalog metrics (fixed 75/25 holdout split, was 5-fold
out-of-fold):**

- `all-eligible__CT` (the canonical recipe, same one used throughout the
  course): held-out R² = **0.469** -- this exactly reproduces Exercise 2's
  own Section 2 worked-example number on the identical split/recipe/target,
  confirming the catalog now genuinely shares that split.
- `frontoparietal__CT` = 0.435, `occipital__CT` = 0.471 (was 0.411/higher
  under 5-fold; ordering preserved: frontoparietal still scores below
  occipital).
- 34 of 35 catalog entries remain enabled (only `all-eligible__CT+Area`,
  p=720, is disabled, same as before); 32 of those 34 are positive R² on the
  fixed split. Two of the smallest, weakest entries (`parietal__Area`,
  `parietal__LGI`, p=42 each) land marginally negative (-0.027) on this one
  split -- a genuine, expected consequence of a single held-out evaluation
  having higher variance than an aggregated 5-fold estimate over the whole
  cohort, not a bug. `tests/test_export_regression_catalog.py` was written
  to expect "almost all, not literally all" positive, with the exact
  fraction (≥90%) and the canonical/default-panel entries checked explicitly.

**Superseded: original "Judgment call" section.** The paragraph below,
from the original WP19 pass, is left in this report for history but no
longer reflects current policy -- see the correction above.

## Git state

- Starting tag: `wp19-start` at `03ac5cf` (WP18 report commit)
- Branch: `revise/remove-early-cross-validation`, created from `wp19-start`
- Checkpoint commit (WP document): `ea0b34f`
- Implementation commit: `ea7c1f7`
- Merge commit (`--no-ff` into `main`): `30caa85`
- WP19 report commit: `1012d1a`
- Correction commit (this continuation, committed directly to `main` per the
  correction instructions -- implementation + updated reports together): see
  Claude's final response for the exact SHA (not inserted here, per the "do
  not amend reports to insert their own commit's SHA" convention)
- `origin/main` unchanged throughout; nothing pushed

## Inventory of early CV / parameter-selection material found before editing

Searched canonical notebooks, portable notebooks, audit/export scripts,
`book/config/abide_modeling.json`, frontend TS, widget config JSON, and
tests. Findings:

- **Exercise 3** (`book/chapters/chapter_03/exercise_03.ipynb`): a full
  "Choosing k honestly" section running `KFold(n_splits=5, shuffle=True,
  random_state=0)` + `cross_val_score` over `CANDIDATE_KS = [1,3,5,7,10,15,
  20,30,50,100,200]`, selecting `K_SELECTED` (historically **15**, not 20)
  by `idxmax()`, plus a plot annotated "selected k", prose asserting the
  test set "played no role above", and later text calling the empirical
  Section-5 curve's argmax "validation-optimal".
- **Exercise 4** (`book/chapters/chapter_04/exercise_04.ipynb`): a full
  "Choosing C honestly" section running `GridSearchCV` +
  `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` over
  `CANDIDATE_CS = np.logspace(-4, 4, 9)` scored by ROC AUC, selecting
  `C_SELECTED` (historically **0.01**, from WP18), a CV-AUC-vs-C plot, a
  "Think first" question and answer about why the test set must stay
  outside C selection, and a final review question naming
  cross-validation.
- **`scripts/knn_model_audit.py`**: developer audit script whose entire
  purpose was 5-fold-CV k selection across three candidate feature spaces
  (this is what historically produced k=15).
- **`scripts/classification_model_audit.py`**: developer audit script
  performing `GridSearchCV`/`StratifiedKFold` C selection (this is what
  produced C=0.01 in WP18).
- **`scripts/export_knn_explore_data.py` / `export_knn_abc_data.py`**:
  read `knn_cfg["selected_k"]` from the manifest and exposed it to the
  frontend as `selectedKFromAudit`; the `knn-explore` widget's config
  defaulted to `"validation-optimal"` (the empirical curve's argmax, 17)
  and `knn-abc` defaulted to the audit-selected k (15).
- **`scripts/export_classification_threshold_data.py` /
  `export_classification_imbalance_data.py`**: read
  `classification_model_audit.select_canonical_c(frame)` (CV-selected) and
  exposed it as `selectedC` in the public artifact JSON.
- **`book/config/abide_modeling.json`**: `knn.cv_for_k_selection`,
  `knn.selected_k` (15) + rationale; `classification.cv_for_c_selection`,
  `classification.selected_C` (0.01) + rationale.
- **`course_overview/…docx`**: Exercise 3 row said "choosing k honestly via
  training-only 5-fold cross-validation"; Exercise 4 row said "choosing C
  honestly via training-only cross-validation scored by ROC AUC".
- **Exercise 1/2**: no formal CV/tuning *procedure* is taught in the
  notebook's own wording, but two passing terminology uses were found in
  Exercise 1/2's text (see below), and -- identified at the time but
  originally left in place, then corrected per Yoav's instruction (see
  "Correction" section above) -- Exercise 2's `regression-compare` feature-
  set-comparison activity genuinely ran `KFold(n_splits=5, ...)` +
  `cross_val_predict` under the hood in `scripts/export_regression_catalog.py`,
  invisible in the notebook's own text but real analysis. Exercise 1 named
  "cross-validation" in a forward-looking data-leakage sentence about later
  ML analyses; Exercise 2 used "cross-validated R²" and "one fixed set of
  folds" in Section 4's exploratory-model-comparison caveat.
- **Tests**: `tests/test_knn_model_audit.py`, `tests/test_exercise_03_notebook.py`
  asserted the CV-selection mechanism and k=15/17; `tests/test_classification_model_audit.py`,
  `tests/test_exercise_04_notebook.py` asserted GridSearchCV/C=0.01; Playwright
  e2e specs asserted default k=17/15 and AUC=0.593.

## Judgment call: Exercise 2's regression-compare activity [SUPERSEDED — see "Correction" above]

This section is the original, incorrect reasoning, kept verbatim for the
record. Yoav corrected it: the hidden CV procedure itself had to go. Do not
rely on this section for current behavior.

Exercise 2's "Comparing feature sets" activity (`export_regression_catalog.py`)
genuinely performs 5-fold `KFold` + `cross_val_predict` as its **evaluation
methodology** (honest out-of-sample R² across feature-set comparisons) — it
selects no hyperparameter (`LinearRegression` has none). WP19 explicitly
scopes Exercise 3/4 as "the expected substantive changes" and instructs
Exercise 1/2 to change "only if they contain student-facing references that
conflict with the new course sequence," without modifying "analyses,
outputs, interactives, or model results unless a direct conflict… is
present." I judged that rearchitecting this pipeline (a legitimate,
previously-approved WP11 feature) was out of WP19's scope, and instead
simplified the two passing mentions that named "cross-validation"/"folds"
by term (→ "one fixed evaluation procedure", "R²" without the
"cross-validated" adjective) without touching the underlying methodology,
code, or numbers. Flagging this for Yoav's confirmation that the
narrower interpretation is correct.

## Exercise 3 — exactly what changed

- **Removed**: the "Choosing k honestly" section (1 markdown + 3 code/markdown
  cells: candidate-k CV loop, CV-vs-k plot, "test set played no role" text);
  all `KFold`/`cross_val_score` imports and usage; the duplicate post-splice
  fit cell that referenced the now-undefined `K_SELECTED`.
- **Added**: a "A predeclared k" cell stating the WP19 policy sentence and
  `K_EXAMPLE = 20`, then one fit/evaluate cell.
- **Reworded** (no code change): "What this notebook covers" item 2; the
  dimensionality note; "A few things to hold onto"; the Section 3 "Think
  first" and follow-up text (both said "cross-validated k" → "k = 20");
  Section 5's empirical-curve print statement, plot labels, and "What this
  curve shows" admonition (renamed "validation-optimal" → "lowest
  validation error" everywhere, including the frontend widget config and
  export-script field/print names); Section 6 intro (states the widget
  opens at k = 20 and is exploration, not selection); "In summary" bullet 2;
  review-question 9 ("selected" → "used").
- **Retained unchanged**: the honest-vs-invalid interactive (Section 3), the
  conceptual bias–variance curve (Section 4), the empirical fitting/
  validation curve and its exploratory framing (Section 5), the k-explore
  browser activity (Section 6) including training-sample variance and
  bias/variance proxies.
- **Fixed model spec**: `Pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=20))`,
  fit on 753 training participants, evaluated once on 251 test participants.
- **Recomputed held-out metrics (k = 20)**: R² = **0.664**, MSE = **31.4**
  (RMSE 5.6 years) — genuinely recomputed by re-executing the notebook, not
  copied from history (the historical CV-selected k was 15, R² = 0.649;
  20 is a different, higher-scoring point, confirmed by
  `scripts/knn_model_audit.py --run`).

## Exercise 4 — exactly what changed

- **Removed**: the "Choosing C honestly" section (markdown intro + GridSearchCV
  code + CV-AUC-vs-C plot + "smaller/larger C" and "cross-validation selects…"
  explanatory text); the "Think first" question/answer about keeping the test
  set outside C selection; the final review question about CV.
- **Added**: an "A predeclared C" cell with the WP19 policy sentence and
  `C_EXAMPLE = 1.0`; a review question about `predict_proba()` vs `predict()`
  (reusing the reasoning already present in an earlier in-notebook "Think
  first") to keep exactly three final questions.
- **Reworded** (no code change): Section 3's "Model:" sentence; the explicit-
  scaling cell's comment; the pipeline-shortcut cell's comment; Section 6's
  intro ("the C selected in Section 3" → "C = 1.0 from Section 3"); "In
  summary" bullet 2.
- **Retained unchanged**: the decision-threshold activity, the class-
  imbalance/misleading-accuracy activity, the model-vs-majority-baseline
  plot, AUC/balanced-accuracy/sensitivity/specificity reporting, the
  threshold-does-not-change-AUC lesson, the labelled TN/FP/FN/TP confusion
  matrix, the suppressed rich-estimator output.
- **Fixed model spec**: `Pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000))`,
  fit on 753 training participants, evaluated once on 251 test participants.
- **Recomputed held-out metrics (C = 1.0)**: accuracy = **0.546**, AUC =
  **0.569**, sensitivity = 0.534, specificity = 0.556, confusion matrix
  **TN=75, FP=60, FN=54, TP=62** — exactly reproduces WP19's expected values
  and WP17's original untuned-C=1.0 result (recomputed fresh via
  `scripts/classification_model_audit.py --run`, not copied).

## Exercises 1 and 2 — audit result

Changes were necessary (§6), and — per the correction — Exercise 2's model
results for the regression-compare activity **were** modified (recomputed
under the fixed split; see "Correction" above). Exercise 1's, and Exercise
2's own Section 2 worked-example, analyses/outputs were not modified.

- **Exercise 1**: one sentence in the missing-data section named
  "cross-validation" as a forward reference while explaining preprocessing
  leakage. Reworded to reference the train/test split generically instead,
  preserving the leakage lesson without naming the postponed method.
- **Exercise 2**: two passing mentions of "cross-validated R²"/"fixed set of
  folds" in Section 4's exploratory-model-comparison caveat and one
  questions-cell reference were reworded in the original WP19 pass, and now
  read correctly given the fixed-split correction. The regression-compare
  activity's underlying 5-fold `KFold`/`cross_val_predict` evaluation was
  removed and replaced with one fixed train/test split (see "Correction"
  above) — this is a genuine change to the activity's model results, not
  just wording. No other Exercise 1/2 content changed.

## Interactive exploration vs. parameter selection

Confirmed for both exercises: the k-explore and honest-vs-invalid (knn-abc)
widgets, and the threshold/imbalance widgets, still let students move a
control across many values and see real, recomputed metrics — but no widget
default, label, or reflection prompt calls a value "best"/"selected"/
"optimal" based on validation performance any more. `knn_explore.json`'s
`defaultK` is now the literal `20` (was `"validation-optimal"`); `knn-abc`'s
default reads a renamed `workedExampleK` field (was `selectedKFromAudit`,
15) and now resolves to 20; the classification widgets' `modelC` field
(was `selectedC`) is 1.0 throughout every ratio/seed. The one remaining
factual "lowest validation error" curve-minimum annotation (Exercise 3
Section 5/6) is explicitly framed as illustration, not a final answer.

## Threshold and imbalance activities

Confirmed still working: 18 standalone Playwright specs
(`classification-threshold.spec.ts`, `classification-imbalance.spec.ts`)
and 6 built-book specs (`chapter04.spec.ts`) all pass — threshold changes
recompute the confusion matrix while AUC (now 0.569) stays fixed; the
imbalance activity's majority-baseline comparison and per-ratio/seed
metrics render correctly with the fixed C = 1.0 model throughout.

## Overview DOCX

- Exercise 3 row now reads "…worked model uses a preselected k = 20, fixed
  by course design…" (no CV claim).
- Exercise 4 row now reads "…worked model uses a fixed C = 1.0, fixed by
  course design…" (no CV/tuning claim).
- Layout fix for the WP18 defect: every table row (header + 4 data rows)
  now carries `w:cantSplit`; paragraph spacing tightened (title/intro
  `space_after` reduced, cell paragraphs set to 0pt-before/4pt-after).
  Body text stays at 12pt (not reduced).
- Structural validation: `python3 -m unittest tests.test_course_overview_docx -v`
  (system Python 3.12 with python-docx 0.8.11) — **11/11 pass**, including
  two new WP19 assertions (`test_no_early_cross_validation_or_tuning_claim`,
  `test_rows_are_marked_cant_split`).
- **Visual-render status: unavailable.** No `soffice`/`libreoffice`/
  `docx2pdf`/`unoconv` is installed on this machine, and the WP explicitly
  forbids installing LibreOffice to avoid delaying the WP. Only structural
  (python-docx + zip) validation was performed. **Please return the file
  for external visual inspection** to confirm the one-page landscape
  layout looks right — this is the one WP19 requirement I could not
  self-verify.

## Tests — commands, results, timings

All run from the repo root unless noted.

1. `source .venv/bin/activate && python3 -m unittest discover -s tests -p 'test_knn_model_audit.py' -v` — 13/13 pass, 1.6s
2. `python3 -m unittest discover -s tests -p 'test_classification_model_audit.py' -v` — 20/20 pass, 1.3s
3. `python3 -m unittest discover -s tests -p 'test_export_knn_explore_data.py'/'test_export_knn_abc_data.py'/'test_export_classification_threshold_data.py'/'test_export_classification_imbalance_data.py'` — 25, 18, 10, 18 pass respectively
4. `python3 -m unittest discover -s tests -p 'test_exercise_03_notebook.py' -v` — 31/31 pass
5. `python3 -m unittest discover -s tests -p 'test_exercise_04_notebook.py' -v` — 34/34 pass
6. `python3 -m unittest discover -s tests -p 'test_wp19_content_audit.py' -v` (new) — 7/7 pass
7. `python3 -m unittest discover -s tests -p 'test_*.py'` (full suite, run once pre-merge and once post-merge) — **405/405 pass, 11 skipped** (docx tests, no `docx` in `.venv`), ~6.8s each run
8. `python3 scripts/knn_model_audit.py --run` / `python3 scripts/classification_model_audit.py --run` — regenerated committed JSON, matches notebook output exactly
9. `python3 scripts/export_knn_explore_data.py --refresh` / `export_knn_abc_data.py --refresh` / `export_classification_threshold_data.py --refresh` / `export_classification_imbalance_data.py --refresh` — all regenerated and self-validated
10. `python3 scripts/build_portable_notebook.py --write --notebook all` then `python3 -m unittest discover -s tests -p 'test_build_portable_notebook.py' -v` — 25/25 pass
11. `python3 scripts/smoke_portable_notebook.py --notebook chapter_03` / `--notebook chapter_04` — both execute clean, metrics match canonical notebooks exactly
12. `python3 -m unittest tests.test_course_overview_docx -v` (system python3) — 11/11 pass
13. Frontend: `cd interactive && npx tsc --noEmit` — clean; `npx vitest run` — **304/304 pass** (19 files)
14. `cd interactive && npm run build` — succeeds (one pre-existing chunk-size warning, unrelated to WP19)
15. `cd . && source .venv/bin/activate && jupyter-book build book` — succeeds, 2 warnings (one pre-existing `README.md not in toctree`, unrelated)
16. `cd interactive && npx playwright test knn-explore.spec.ts knn-abc.spec.ts classification-threshold.spec.ts classification-imbalance.spec.ts --workers=1` — **70/70 pass**
17. `cd interactive && npx playwright test --config playwright.book.config.ts chapter03.spec.ts chapter04.spec.ts --workers=1` — first run: **3 failures** (stale hardcoded expectations: `chapter03.spec.ts` line 65 still expected `k = 17`; `chapter04.spec.ts` lines 46/65 still expected `AUC = 0.593` from WP18's C=0.01). Fixed in one pass (updated the three literals to `k = 20` / `AUC = 0.569`) and reran the same two spec files once — **13/13 pass**. This is the one permitted isolated rerun; no second fix was needed.

### Correction continuation — focused re-run only (per the correction's explicit scope)

18. `python3 -m unittest discover -s tests -p 'test_export_regression_catalog.py' -v` — first run: **1 failure** (`test_every_bundle_predicts_age_above_chance` assumed universal positivity, which the old aggregated 5-fold estimate happened to have but the new single-split estimate legitimately does not for 2 of 34 enabled entries). Rewrote the assertion to require ≥90% positive plus explicit checks on the canonical/default entries (this is the one permitted rerun for this failure) — **17/17 pass** after.
19. `python3 -m unittest discover -s tests -p 'test_exercise_02_notebook.py' -v` — 30/30 pass, unchanged (this notebook has no inline code for the iframe-only regression-compare activity).
20. `python3 -m unittest discover -s tests -p 'test_build_portable_notebook.py' -v` (after regenerating the chapter_02 portable notebook) — 25/25 pass.
21. `python3 -m unittest discover -s tests -p 'test_wp19_content_audit.py' -v` (updated: added `regression_compare.json` to the widget-config scan, added a generated-data-artifact scan, added an Exercise-2-exporter implementation check that the *code* — not the module docstring's historical explanation — contains no `KFold`/`cross_val_predict`) — **14/14 pass**.
22. Frontend: `cd interactive && npx tsc --noEmit` — clean; `npx vitest run regression-compare` — **20/20 pass** (2 files).
23. `cd interactive && npm run build` — succeeds (same pre-existing chunk-size warning).
24. `source .venv/bin/activate && jupyter-book build book` — succeeds, same 2 pre-existing warnings; Exercise 2's own notebook cache was reused (unchanged code), only its regenerated widget config/data copied.

No unrelated full suites were repeated for this correction, per its explicit scope.

## Deviations and items for Yoav's attention

1. **Judgment call on Exercise 2 — corrected.** The original pass left the
   regression-compare activity's hidden `KFold`/`cross_val_predict`
   evaluation in place; Yoav confirmed this was wrong and it has now been
   replaced with a fixed train/test split (see "Correction" above). No
   further action needed on this item.
2. **DOCX visual rendering unavailable** — please open the file locally to
   confirm the one-page landscape layout. (Unchanged by this correction —
   the DOCX was not touched.)
3. Historical WP13/WP14/WP17/WP18 documents and reports were left untouched
   (not rewritten) per §2.
4. The WP16 architect report remained untracked and untouched throughout,
   including through this correction.

## Local build commands and URLs (Exercises 3 and 4)

- Frontend dev/build: `cd interactive && npm run build` (writes to
  `book/_static/widgets/app/`); `npm run preview` to serve it locally.
- Jupyter Book: `source .venv/bin/activate && jupyter-book build book`;
  open `book/_build/html/chapters/chapter_03/exercise_03.html` and
  `book/_build/html/chapters/chapter_04/exercise_04.html` in a browser, or
  `cd interactive && npm run serve:book` (serves `book/_build/html` at
  `http://localhost:4174`) for the URLs the Playwright book specs use:
  `/ml-neuro-tutorials/chapters/chapter_03/exercise_03.html` and
  `/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html`.
- Standalone widgets: `cd interactive && npm run serve:static` serves
  `book/_static/widgets` at `http://localhost:4173` — e.g.
  `/app/index.html?config=../configs/knn_explore.json`.

## Nothing pushed or deployed; WP20 not started

Confirmed: no `git push`, no GitHub Actions triggered, no deploy workflow
invoked. `origin/main` remains at `c5aa2ca`, unchanged throughout this WP.
No WP20 file or work was created or begun.
