# WP12 — exact change log

Location-specific before/after. Notebook cells are referenced by stable
`nbformat` id. It should be possible to review the substantive work from this
file without diffing raw notebook JSON.

Branch `feature/regression-practice`; checkpoint `3051562` (tag `wp12-start`);
implementation commit `5f559f9`.

---

## 1. Git objects

| Item | Value |
|---|---|
| Checkpoint commit | `30515629c6e4ddf2716581ed2295ec65f4b3fe65` — `checkpoint: before WP12` (adds `WPs/WP12_EXERCISE_2_CORRECTIONS_AND_MODEL_AUDIT.md`, 1 file, +333) |
| Annotated tag | `wp12-start` → `3051562` (tag object `6e5802496f41e15ce39d4df3e0f45e4fdc775176`; name free, no suffix) |
| Implementation commit | `5f559f9` — `WP12: retarget Exercise 2 to age (regression model audit), regularisation preview, navigation/wording corrections` (19 modified, 5 new; 1051 insertions, 765 deletions) |
| Report commit | adds the two report files only |

Tags `wp01-start`…`wp11-start` and all prior branches untouched. No push,
merge, force, rebase, revert, or history rewrite.

---

## 2. NEW `scripts/regression_model_audit.py` (audit source, not build output)

Reproducible modelling audit run once (`--run`, network) and re-validated
offline thereafter (`--check`). Public surface:

- `FEATURE_SPACES` — the 6 predeclared (feature-space) combinations audited:
  `all-eligible × {all 4 measures, CT, Area, Vol, LGI}`, `frontoparietal × CT`.
- `TARGETS = ["age", "FIQ"]`.
- `_evaluate(model_family, X, y)` — outer `KFold(5, shuffle=True,
  random_state=0)`; for `ridge`/`lasso`, `RidgeCV`/`LassoCV` with `cv=`
  inner `KFold(5, shuffle=True, random_state=1)` fitted on the outer-training
  rows only; returns per-fold R²/MSE/alpha/non-zero-coefficient-count plus
  aggregate mean/std. `linear` with `p >= n_train` is flagged
  `underdetermined`.
- `_locked_holdout(model_family, X, y, groups)` — the manifest's own
  `protocol.holdout_split` (`test_size=0.25, random_state=42,
  stratify=group`), evaluated exactly once.
- `run_audit()` — target facts (N/missing/range/mean/sd/brain-NaN for both
  targets) + every `(feature_space, target, model_family)` nested-CV
  candidate + 6 locked-holdout candidates for the structures the notebook
  actually shows.
- `validate(results)` / `cmd_check()` — offline re-validation: source pins
  match the manifest, both targets covered by every feature space, every
  `p >= n_train` OLS candidate is labelled `underdetermined`.
- `RIDGE_ALPHAS = np.logspace(-1, 6, 29)`, `LASSO_ALPHAS = np.logspace(-3, 2,
  26)` — documented logarithmic grids, reused verbatim in the manifest and the
  notebook.

---

## 3. NEW `scripts/regression_model_audit_result.json` (generated, `--run`)

Full audit output: `targets` (age N=1004, FIQ N=908, both with 0 missing brain
cells), 36 nested-CV `candidates` + 6 `locked-holdout-once` candidates — see
`WP12_REPORT.md` §2.4–2.5 for the rendered table. SHA-256
`6aef676e63ce83a6d9899c25036249a1664ad9ae72311aae665d1e59869e7b2a`.

---

## 4. `book/config/abide_modeling.json` (reviewed manifest)

```diff
- "targets": {
-   "FIQ": {"role": "main", ...},
-   "SRS_TOTAL_RAW": {"role": "lower_availability", ...}
- }
+ "targets": {
+   "age": {"role": "main", "label": "Age at scan", "unit": "years",
+            "source": "brain_table", "available_n": 1004, "missing_n": 0,
+            "rationale": "WP12 audit: age has reliably positive out-of-sample
+                          R2 with ordinary linear regression, unlike FIQ."},
+   "FIQ": {"role": "regularization_preview", "label": "Full-scale IQ (FIQ)",
+            "unit": "IQ points", ... unchanged facts,
+            "rationale": "kept as the compact secondary example to show
+                          ridge/lasso rescue instability, not absence of
+                          signal."}
+ }
```

- `rejected_targets.age` (WP11's entry, "strongly predictable... not chosen")
  removed; `rejected_targets.SRS_TOTAL_RAW` added (demoted from `targets`,
  reasoned: no longer has a role once age is main; still fetched by the merge).
- `protocol.canonical_recipe`: `{"bundle": "frontoparietal", "measures":
  ["CT"]}` → `{"bundle": "all-eligible", "measures": ["CT"]}` (p=358), note
  rewritten (whole-cortex age effect, no small bundle to prefer, p well under
  n_train).
- NEW `protocol.regularisation_preview` block: purpose, feature space
  (`all-eligible × [CT,Area,Vol,LGI]`), both alpha grids, pointers to the audit
  script/result.
- `catalog.target`: `"FIQ"` → `"age"`.
- `catalog.identifiability_rule` / doc text: `p=720` typo corrected to the
  actual `p=716` (`all-eligible × [CT,Area]`).
- `catalog.note` extended to clarify the OLS-only restriction is about this
  activity's model family, not p-vs-n in general (the regularisation preview
  is where ridge/lasso are actually used).
- `bundles.*` and `literature.{pfit,narr}` blocks: unchanged (still document
  the original P-FIT/Narr provenance; the notebook now cites them only beside
  the FIQ analysis, per WP12 §6.2).
- NEW top-level `literature` entries are **not** added to the manifest (the
  two new age citations — Bethlehem 2022, Storsve 2014 — live in the notebook
  prose and the widget `literatureNote`; the manifest's `literature` block was
  left as the FIQ/P-FIT provenance record it always was, to avoid scope creep
  into a second schema field this WP does not need).
- SHA-256 `9fbe6bf73d4040bc809140e287a94ccc9be968b94823d9274133c3604cb7e1b1`.

---

## 5. `scripts/abide_modeling_data.py`

- `_check_manifest`: `canonical_recipe.bundle` check now special-cases
  `"all-eligible"` (previously only `catalog.bundles` did); the required-roles
  check now looks for `("main", "regularization_preview")` instead of
  `("main", "lower_availability")`.

---

## 6. `scripts/export_regression_catalog.py`

- `build_catalog`: `observed` — was `[int(round(v)) for v in y]` with a hard
  `np.allclose(y, np.round(y))` integer-valued assertion; now
  `[round(float(v), PRED_DECIMALS) for v in y]`, no integer assertion (age is
  fractional years).
- Cohort-consistency check: `np.array_equal(np.round(y_chk), np.round(y))` →
  `np.allclose(y_chk, y)` (exact float comparison, not int-rounded).
- `"target": {"label": "Full-scale IQ (FIQ)", "unit": "IQ points"}` (hardcoded)
  → `{"label": manifest["targets"][TARGET]["label"], "unit":
  manifest["targets"][TARGET]["unit"]}` (manifest-driven).
- `validate_catalog`: `"observed must be integers"` (rejects any non-`int`) →
  `"observed must be numeric (int or float) target values"` (rejects bool /
  non-numeric only).

---

## 7. `book/_static/widgets/data/abide_regression_models.json` (generated, `--refresh`)

`target.name` `"FIQ"` → `"age"`; `target.label` "Full-scale IQ (FIQ)" → "Age
at scan"; `target.unit` "IQ points" → "years"; `cohort.n` 908 → **1004**;
`crossValidation.foldTrainN` 726 → **803**. 35 models (unchanged count), 34
enabled (unchanged), `all-eligible__CT+Area` (p=716) still the one disabled
entry with the same reason text. **Every enabled `cvR2` is now positive**
(was: every one negative). Selected values: `frontoparietal__CT` (default A)
+0.411 (was −0.171); `occipital__CT` (default B) +0.433 (was −0.040);
`all-eligible__CT` +0.466 (was −1.208); `sensorimotor__CT+Area` (new overall
best) +0.507. `observed` now stores rounded floats (fractional years), not
integers. 73 485-ish → 280 539 bytes (float precision, not int). SHA-256
`0f2deec5add54725d5734476ada96aabdf5d23cccb1dfd2ee584c29ae739b50d`. Two
`--refresh` runs byte-identical (re-verified).

`abide_histogram.json`, `abide_retention.json`, `abide_table_inspection.json`:
**untouched** (`export_widget_data.py --check --artifact all` still OK for all
three).

---

## 8. `book/_static/widgets/configs/regression_compare.json`

`description`/`instructions`: "IQ" → "age at scan". `targetLabel`:
"Full-scale IQ (FIQ)" → "Age at scan (years)". `literatureNote`: P-FIT/Narr
text → Bethlehem et al. (2022, doi:10.1038/s41586-022-04554-y) / Storsve et al.
(2014, doi:10.1523/JNEUROSCI.0391-14.2014) text, explicitly noting
`Frontoparietal`'s IQ-literature origin is reused only as a comparison bundle.
`bundles[0].label`: "Frontoparietal (P-FIT)" → "Frontoparietal" (the "(P-FIT)"
qualifier no longer applies to what this activity predicts).
`reflectionPrompts`: reworded around age/FIQ contrast (prompt 2 now asks
whether the `All eligible ROIs` direction of change matches what you'd expect
for FIQ). `defaultA`/`defaultB`, `measurementSubsets`, the 7 `bundles` list:
**unchanged**. SHA-256
`0eb58988982751336342a6d15fd9f5a223412ffc4e66b35f604fc26d69028d89`.

---

## 9. `interactive/src/regression-compare-data.ts`

- `superRefine`: removed the `data.observed.every((v) => Number.isInteger(v))`
  check and its associated issue (`"observed must be integer target
  values"`). `z.number().finite()` on the array element still rejects
  `NaN`/`Infinity`/non-numbers; nothing else in the schema changed.

## 10. `interactive/src/components/regression-compare.ts`

- `litSummary.textContent`: `"Where the frontoparietal bundle comes from"` →
  `"Where these ROI bundles come from"` (the disclosure always covered all
  seven bundles; only the heading was frontoparietal-specific).

---

## 11. `book/_static/launch-buttons.js` (NEW)

Static JS (registered in `_config.yml` `html_js_files`, loaded on every book
page): a literal `PAGE_TO_PORTABLE` map (`chapters/chapter_01/exercise_01.html`
→ `book/downloads/chapter_01/exercise_01_portable.ipynb`,
`chapters/chapter_02/exercise_02.html` → the chapter_02 equivalent). On
`DOMContentLoaded`, if the current path matches an entry, inserts an `<a
data-testid="colab-launch-button">` (rocket icon + "Colab" label, `.btn
.btn-sm`, `target="_blank"`) as the first child of
`.header-article-items__end .article-header-buttons`, linking to
`https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/blob/main/<portable path>`.
Idempotent (checks for an existing button before inserting). Pages with no map
entry (Introduction, Syllabus, Contents) get nothing.

## 12. `book/_config.yml`

```diff
+# WP12: `_static/launch-buttons.js` adds the missing per-page Colab CONTROL
+# ... (comment, see file)
 sphinx:
   config:
     html_js_files:
       - sidebar-toggle-fix.js
+      - launch-buttons.js
```

## 13. `book/_static/custom.css`

**Appended** a `/* WP12 -- per-page Colab launch button */` block:
`.header-article-items__end .dropdown-launch-button` (flex layout, spacing)
and its `.btn`/`.colab-launch-label` children. No existing rule changed.

---

## 14. `book/chapters/chapter_02/exercise_02.ipynb` (31 cells, rebuilt)

Rebuilt with nbformat (cell ids kept stable where a cell's role persisted from
WP11; `wp12-001..004` are the only new ids) and executed end-to-end (network).
17 markdown + 14 code (1 `hide-cell`, 4 `hide-input`, 9 visible).
`nbformat.validate` OK.

| id | kind | before (WP11) | after (WP12) |
|---|---|---|---|
| `wp11-001` | md | `# Exercise II: Regression` | `# Exercise 2: Regression` |
| `wp11-002` | md | `:class: tip`, no direct links | `:class: how-to-use`, Colab + raw links to `chapter_02/exercise_02_portable.ipynb` (matches Exercise 1's pattern exactly) |
| `wp11-003` | md | "linear-regression half of Exercise II... short on theory", Asaf comparison implied | Exercise-2/regression/bias-variance/KNN scope statement, no Asaf comparison |
| `wp11-010` | md | outcome examples: `FIQ` | outcome: `age` (native, no join); `FIQ` named as Section 5's harder target |
| `wp11-011` | code, `hide-cell` | loads brain+phenotype, merges | **unchanged** (already loads both `age` and `FIQ`) |
| `wp11-012` | code | prints FIQ availability | + prints `age available for 1004 of 1004` |
| `wp11-013` | md | Think first: name an outcome (FIQ implied) | Think first: name *the* main outcome (age) |
| `wp11-020` | md | frontoparietal×CT recipe (p=78), FIQ target, P-FIT framing | all-eligible×CT recipe (p=358), age target, whole-cortex framing |
| `wp11-021` | code | `FRONTOPARIETAL = [...39 literal labels...]` | `ASYMMETRIC_ROIS` filter over `BRAIN_COLS`, no literal ROI list (equals `bundle_columns("all-eligible",["CT"])` as a set) |
| `wp11-022` | code | `has_fiq`, `y=FIQ`, n_train=681/n_test=227 | `has_age`, `y=age`, **n_train=753/n_test=251** |
| `wp11-023` | code | held-out R²=−0.120 | held-out **R²=0.475, MSE=49.0, RMSE 7.0 years** |
| `wp11-024` | code, `hide-input` | scatter, x/y label "FIQ" | scatter, x/y label "age (years)" |
| `wp11-025` | md | 78-D hyperplane; negative-R² framing | 358-D hyperplane; positive-R² framing, "not automatically large" caveat |
| `wp11-030`–`wp11-032` | md/code | A/B/C table + panels, FIQ | same structure, age; **C R²=1.000 exactly** (p=358>n_test=251, literally underdetermined, not just optimistic) |
| `wp11-031` | code | `# B: resubstitution` same line as code | **own source line** (WP12 §4.1 fix) |
| `wp11-033` | md | "B compares different rows..." | exact WP wording: "B evaluates the model on its training data, whereas A and C..." (WP12 §4.2 fix) |
| `wp11-040` | md | P-FIT/Narr framing for FIQ | Bethlehem 2022 / Storsve 2014 framing for age; explicit "no single small region set... for age" statement |
| `wp11-041` | md | iframe title "...predicting IQ from brain structure" | iframe title "...predicting **age** from brain structure" |
| `wp11-042` | md | Think first (FIQ-flavoured) | Think first + explicit callback to Section 5's FIQ comparison |
| `wp12-001` | md, **NEW** | — | `## 5. Regularisation preview: age vs FIQ with the full brain` — p-vs-n explanation, ridge/lasso definitions, P-FIT/Narr citations (FIQ-only) |
| `wp12-002` | code, **NEW** | — | `ALL_MEASURES_FEATURES` (p=1432); `fit_and_score(target)` — OLS/RidgeCV/LassoCV over documented grids, inner CV on train only, one holdout eval; runs for both targets |
| `wp12-003` | code, `hide-input`, **NEW** | — | grouped bar chart, OLS (grey, underdetermined) vs ridge/lasso (colour) × age/FIQ |
| `wp12-004` | md, **NEW** | — | interpretation: age improves with regularisation, FIQ stays ≈0; MSE not comparable across targets |
| `wp11-050` | md | `## 5. What does sample size change?`, two-outcome intro | `## 6. What does sample size change?`, single-learning-curve intro (drops the WP11 Part A/B two-outcome + matched-N structure — WP12 §6.4 deviation, documented in the report) |
| `wp11-0515`, `wp11-052`–`wp11-057` | md/code | Part A (FIQ vs SRS availability) + Part B (matched-N) | **removed** |
| `wp11-058` | code | sizes `[120,200,320,460,600,681]`, FIQ, p=78 | sizes `[370,470,570,670,753]`, **age**, p=358 (smallest size kept ≥ p, not the old ≥1.5×p margin, and documented as "barely well posed" on purpose) |
| `wp11-059` | code, `hide-input` | learning-curve figure, FIQ title | learning-curve figure, "age learning curve... p=358" title |
| `wp11-05a` | md | "more data bought certainty, not signal" (FIQ, stays negative) | same point, age (stays positive); explicit contrast with FIQ's regularisation-can't-manufacture-signal result |
| `wp11-060` | md | 6-point summary, FIQ/negative-R² framing | 5-point summary, age/FIQ/regularisation framing |
| `wp11-061` | md | 7 questions (FIQ-flavoured) | 7 questions (age/FIQ/regularisation-flavoured; Q5/Q6 new) |

SHA-256 `1e1723f5867077876c6ebb534c646949a3447eeefbdeb88b5cce7eb2e5ff4907`.

---

## 15. `scripts/build_portable_notebook.py`

- **Added** `NotebookSpec.colab_title: str | None = None`; wired into
  `build_portable`: when set, writes `out["metadata"]["colab"] = {"name":
  spec.colab_title}`.
- `CHAPTER_02.colab_title = "Exercise 2: Regression"` (`CHAPTER_01` leaves it
  `None` — unchanged metadata, byte-identical output).
- `_CH2_BANNER`: "Exercise II: Regression - portable notebook" → "Exercise 2:
  Regression - portable notebook" (heading only; body text unchanged).
- `CHAPTER_02.iframe_replacements` key: `"Interactive feature-set comparison
  for predicting IQ from brain structure"` → `"...predicting age from brain
  structure"` (matches the canonical notebook's new iframe title).

**`book/downloads/chapter_01/exercise_01_portable.ipynb` verified
byte-identical** to its pre-WP12 state (`--check` → "up to date (75 cells)").

## 16. `book/downloads/chapter_02/exercise_02_portable.ipynb` (generated, `--write`)

33 cells (31 canonical + banner/setup/install, − 1 dropped "Run or download"
admonition). Banner heading now "Exercise 2: Regression - portable notebook".
`metadata.colab.name = "Exercise 2: Regression"` (new). Otherwise same
structure as WP11 (commented `%pip install` cell, all code cells output-free,
`execution_count` None, no MyST/iframe/hide-tag/repo-path). SHA-256
`c17552039960ebf4703a38b14455abf1407e8cfae18704d0d6748cc48787f1ff`.

## 17. `scripts/smoke_portable_notebook.py`

`SMOKE["chapter_02"]["expect"]`: `("1004 participants", "held-out R^2 =",
"n_features (p) = 78")` → `("age available for 1004 of 1004", "held-out R^2
=", "n_features (p) = 358")`. `chapter_01` entry unchanged. Out-of-repo run:
`OK [chapter_01]` (20 code cells), `OK [chapter_02]` (**13** code cells, down
from 15 — fewer code cells after dropping the WP11 Part A/B sample-size
cells and gaining the regularisation-preview cell; net −2).

---

## 18. Tests

### Python (`tests/`), `unittest` — 161 → 184

| File | Δ | Contents |
|---|---|---|
| NEW `test_regression_model_audit.py` | +11 | committed-result self-consistency, source pins, both targets × every feature space present, every `p>=n_train` OLS candidate labelled underdetermined, age reliably positive / FIQ regularised never reliably positive, documented alpha grids; **mocks `RidgeCV.fit`** to prove nested-CV inner tuning never sees more than the outer-fold's training rows and locked-holdout tuning is called exactly once with exactly `n_train` rows; determinism across repeated runs. |
| `test_abide_modeling_data.py` | +2 net | `test_targets_have_the_two_required_roles` updated to `("main", "regularization_preview")`; NEW `test_main_target_is_age`; `test_canonical_recipe_is_a_real_bundle_and_measure` special-cases `all-eligible`; `test_feature_matrix_rejects_an_unknown_target` now uses a genuinely unknown target (was `"age"`, now valid); NEW `test_feature_matrix_accepts_age_as_a_target`. |
| `test_export_regression_catalog.py` | +1 net | `test_shape_and_cohort` → target `age`, cohort.n 1004, `observed` allowed non-integer; `test_every_enabled_model_metric_recomputes_from_its_predictions` → 1004; `test_literature_bundle_does_not_win` renamed `test_every_bundle_predicts_age_above_chance` → every `cvR2 > 0`, frontoparietal still < occipital. |
| `test_exercise_02_notebook.py` | +7 net (18→25) | H1, run-or-download-block, cell-count, tag, KNN/bias-variance, six-numbered-sections(was five)-in-order, main-target-is-age, canonical-feature-recipe-matches-manifest (replaces the WP11 embedded-FRONTOPARIETAL-list test), leakage guard (age+FIQ forbidden), fixed split/pipeline, `# B: resubstitution` own-line, B-vs-C exact wording, invalid-model-object, iframe title (age), age-literature citations, IQ-literature-only-beside-FIQ, regularisation-preview alpha-grids/inner-CV, no-stale-FIQ-claims-outside-its-section, learning-curve-same-recipe, executed-outputs (age values), no-stderr. NEW: `test_no_stale_exercise_ii_wording`, `test_no_linear_regression_half_sentence_or_asaf_comparison`. |
| `test_build_portable_notebook.py` | ±0 | unchanged (25 tests); all still green against the refactored module (chapter_01 spec/output untouched). |
| `test_export_widget_data.py`, `test_notebook_corrections.py`, `test_table_inspection_columns.py`, `test_book_structure.py` | ±0 | unchanged. |

### Frontend `vitest` — 217 → 217 (1 updated, 0 added/removed)

| File | Δ | Contents |
|---|---|---|
| `tests/regression-compare-data.test.ts` | 0 (1 test body changed) | "validates the committed abide_regression_models.json artifact": target=`age`, cohort.n=1004, every enabled model `cvR2 > 0`, frontoparietal still < occipital. |

### Playwright standalone (`interactive/e2e/`) — 60 → 60 (10 tests updated in place)

`regression-compare.spec.ts`: defaults test now expects `Out-of-sample R2 =
0\.\d+` (was `-0\.\d+`) and no "worse than predicting the mean" suffix,
`data-r2 > 0`; bundle-change test now expects `afterR2 > 0.4` (was `<
-0.5` — the direction of the effect flips: more features helps age, hurt
FIQ). Disabled-combination and ROI-list tests unchanged (bundle/feature-count
facts, not target-dependent).

### Playwright built-book (`interactive/e2e-book/`) — 19 → 26

`chapter02.spec.ts`: iframe selector + metrics regex updated to
`age`/positive-R². NEW `launch-buttons.spec.ts` (7 tests): per chapter (×2) —
opening-admonition Colab+raw links target that chapter's own portable
notebook and never the other chapter's, article-header Colab button targets
the same portable notebook, the theme's download-`.ipynb` control is still
present; plus one test that a page with no portable-notebook mapping
(Introduction) gets no Colab button.

---

## 19. Commands run (no repository mutation beyond local commits)

```
git add WPs/WP12_EXERCISE_2_CORRECTIONS_AND_MODEL_AUDIT.md
git commit -m "checkpoint: before WP12"                       # 3051562
git tag -a wp12-start -m "Checkpoint before WP12 ..."
# baseline (before): python -m unittest discover -s tests ;
#   (cd interactive && npm test && npm run test:e2e && npm run test:e2e:book) ;
#   npm audit --omit=dev ; export_widget_data.py --check --artifact all ;
#   abide_modeling_data.py --check ; export_regression_catalog.py --check ;
#   build_portable_notebook.py --check ; rm -rf book/_build ; jupyter-book build book ;
#   2x clean build figure-hash compare
python scripts/regression_model_audit.py --run          # data audit (network)
python scripts/regression_model_audit.py --check
python scripts/export_regression_catalog.py --refresh   # writes abide_regression_models.json for age
python scripts/export_regression_catalog.py --check
python <scratch author_ex2_wp12.py>                      # writes exercise_02.ipynb (scratch authoring script, not committed)
(cd book/chapters/chapter_02 && jupyter nbconvert --to notebook --execute --inplace exercise_02.ipynb)
python scripts/build_portable_notebook.py --write --notebook chapter_02
python scripts/build_portable_notebook.py --check --notebook chapter_01
python scripts/smoke_portable_notebook.py --notebook chapter_02
python -m unittest discover -s tests                     # 184 / 184
(cd interactive && npm test && npx playwright test && npm run test:e2e:book)  # 217 / 60 / 26
npm audit --omit=dev                                      # 0 vulnerabilities
rm -rf book/_build ; jupyter-book build book              # 2 warnings, no *.err.log
for i in a b ; do rm -rf book/_build ; jupyter-book build book ; done   # identical 9-PNG hash set
python scripts/smoke_portable_notebook.py --notebook all  # both, out of repo
git add -A ; git reset -- WPs/reports/
git commit -m "WP12: retarget Exercise 2 to age ..."       # 5f559f9
git add WPs/reports/WP12_REPORT.md WPs/reports/WP12_EXACT_CHANGELOG.md
git commit -m "WP12 report: document Exercise 2 corrections and model audit"
```

No `git reset --hard`, `git checkout -- <path>`, `git clean`, `git rebase`,
`git revert`, `git push`, `git merge`, `--force`, or `--force-with-lease`. No
repository setting, secret, branch-protection rule, or Pages configuration
changed. No `book/_build`, `book/.jupyter_cache`, `book/_static/widgets/app`,
`interactive/node_modules`, `interactive/test-results`, `__pycache__`, or
Playwright artifact staged. `book/config/abide_modeling.json`,
`book/_static/widgets/data/abide_regression_models.json`, and
`scripts/regression_model_audit_result.json` are committed source/reviewed
assets, not build output.
