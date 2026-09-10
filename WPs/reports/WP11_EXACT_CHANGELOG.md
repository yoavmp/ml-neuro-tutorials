# WP11 — exact change log

Location-specific before/after. Notebook cells are referenced by stable
`nbformat` id. It should be possible to review the substantive work from this
file without diffing raw notebook JSON.

Branch `feature/regression-practice`; checkpoint `7b69864` (tag `wp11-start`);
implementation commit `5e785e2`.

---

## 1. Git objects

| Item | Value |
|---|---|
| Checkpoint commit | `7b6986433474d5173062dd4c6d4290c0a373acd9` — `checkpoint: before WP11` (adds `WPs/WP11_NOTEBOOK2_LINEAR_REGRESSION.md`, 1 file, +569) |
| Annotated tag | `wp11-start` → `7b69864` (tag object `8ccadfb16be461643ab9fc782be6a47b3b8ed664`; name free, no suffix) |
| Implementation commit | `5e785e2` — `WP11: Exercise II linear regression, feature-set comparison activity, modelling data pipeline` (25 files, +5230 / −244) |
| Report commit | `WP11 report: document Exercise II linear regression` (adds the two report files only) |

Tags `wp01-start`…`wp10-start` and all prior branches untouched. No push, merge,
force, rebase, revert, or history rewrite.

---

## 2. NEW `book/config/abide_modeling.json` (reviewed manifest, committed source)

`schemaVersion` 1. Blocks:

- `source` — `pinned_commit` `e4eed3c4daa7f40b0ba931182a8c7e5e691dba6b`;
  `brain_table` (`abide2.tsv`, sha256 `ad0db42f…`, sep `\t`, 1004×1446);
  `phenotype_table` (`abide2_phenotypic.csv`, sha256 `537e5411…`, latin-1,
  1114×348); `merge` (`subject` ↔ `SUB_ID`, left, keep
  `FIQ,VIQ,PIQ,SRS_TOTAL_RAW,ADOS_G_TOTAL,ADI_R_SOCIAL_TOTAL_A`).
- `atlas` — HCP-MMP1.0 (Glasser 2016, doi:10.1038/nature18933); `n_rois` 360;
  `column_pattern` `^fs(?P<measure>CT|Area|Vol|LGI)_(?P<hemi>L|R)_(?P<label>.+)_ROI$`;
  `roi_label_inventory` (181 tokens); `asymmetric_labels` `["5L","5R"]`;
  `bilateral_label_count` 179.
- `measures` — CT/Area/Vol/LGI → prefix + name + unit.
- `non_brain_columns`, `identifier_columns`, `cohort` (17 sites, group/sex/age
  summaries).
- `targets` — `FIQ` (role `main`, n 908) and `SRS_TOTAL_RAW`
  (role `lower_availability`, n 764), each with meaning / availability /
  structural note / rationale. `rejected_targets` records VIQ, PIQ,
  ADOS_G_TOTAL, ADI_R_SOCIAL_TOTAL_A, `age` with reasons.
- `leakage_guard` — `forbidden_exact` (25 names incl. every target, VIQ, PIQ,
  DX_GROUP, age, sex, site, subject, …) and `forbidden_pattern`
  `(?i)(^|_)(id|sub|subject|participant|site|age|sex|dx|iq|fiq|viq|piq|group|handed|scan|med_status)($|_)`.
- `protocol` — `holdout_split` `{test_size 0.25, random_state 42, stratify group}`;
  `cross_validation` `{KFold, n_splits 5, shuffle true, random_state 0}`;
  `preprocessing` (StandardScaler+LinearRegression pipeline, scaler on
  train/fold only); `generalisation_target`; `canonical_recipe`
  `{bundle frontoparietal, measures [CT]}`.
- `catalog` — `target FIQ`; `measurement_subsets`
  `[[CT],[Area],[Vol],[LGI],[CT,Area]]`; `bundles` (6 + `all-eligible`);
  `identifiability_rule` (`p < 0.7 * fold_train_n`, else disabled).
- `bundles` — `frontoparietal` (39), `frontal` (21), `parietal` (21),
  `temporal` (18), `occipital` (23), `sensorimotor` (20). Each: `label`,
  `literature`, explicit `rois` list of Glasser labels.
- `literature` — Jung & Haier 2007 (doi:10.1017/S0140525X07001185),
  Narr et al. 2007 (doi:10.1093/cercor/bhl125).

SHA-256 `011def63db0b9c28da1a4b578f4cbcc07901af3ffa20ac799ea507cd807b0096`.

---

## 3. NEW `scripts/abide_modeling_data.py`

Deterministic loader + column taxonomy. Public API:

- `load_manifest(path=MANIFEST_PATH)` / module constant `MANIFEST`.
- `sha256_hex`, `load_modeling_frame(manifest=None)` — download both pinned
  sources, verify SHA-256, merge on `subject`/`SUB_ID`, drop the `Unnamed`
  trailing column, assert 1004 rows and no duplicate ids. **Network.**
- `class BrainColumn(name, measure, hemisphere, roi)`; `is_brain_column(name)`;
  `parse_brain_column(name)` — raises `ValueError` on a non-brain name, an
  unknown ROI, or a `5L`/`5R` in the wrong hemisphere.
- `classify_columns(columns)` → `{identifiers, phenotypes, brain_features,
  brain_parsed, measures, roi_count, hemispheres}`.
- `bundle_rois(bundle, manifest=None)` (`all-eligible` → 179 bilateral labels);
  `bundle_columns(bundle, measures, available=None, manifest=None)` — order is
  ROI → measure → hemisphere (L, R); rejects unknown measure/bundle, a
  non-bilateral label, a duplicate, or (with `available`) a missing column.
- `LEAKAGE_FORBIDDEN_EXACT`, `LEAKAGE_FORBIDDEN_RE`,
  `assert_brain_only(columns)` — every column must match the atlas pattern and a
  real ROI, and match nothing forbidden.
- `feature_matrix(frame, bundle, measures, target, manifest=None)` →
  `(X, y, columns)`; brain-only X, rows with the target present only.
- `_check_manifest(manifest)` + `cmd_check()` (offline) and `cmd_audit()`
  (network); `main()` with `--audit` / `--check`.

---

## 4. NEW `scripts/export_regression_catalog.py`

Offline generator for the browser catalog. Imports from `abide_modeling_data`.

- `build_catalog(frame, manifest=None)` — for each `catalog.bundles` ×
  `catalog.measurement_subsets`: compute `bundle_columns`; if
  `p >= 0.7 * fold_train_n` emit `{disabled: true, reason}`; else
  `cross_val_predict(Pipeline(StandardScaler, LinearRegression), X, y,
  cv=KFold(5, shuffle=True, random_state=0))`, store rounded `predicted`
  (4 dp), `cvR2` (6 dp), `cvMSE` (4 dp). Shared top-level `observed` (int) +
  `foldOf` (fold index per row). No identifiers.
- `validate_catalog(artifact, manifest=None)` — schemaVersion/activity, source
  pins vs manifest, `observed`/`foldOf` alignment + all fold indices,
  no identifier-shaped key, per-model bundle/measure refs, disabled entries
  carry a reason and no predictions, enabled entries' `cvR2`/`cvMSE` recompute
  from `predicted` (±1e-4 / ±1e-2), `featureCount` vs `bundle_columns`.
- `serialize` (sort_keys, compact, trailing newline). `cmd_refresh` (network),
  `cmd_check` (offline), `cmd_print_upstream_hash`. `main()` with
  `--refresh` / `--check` / `--print-upstream-hash`.

---

## 5. NEW `book/_static/widgets/data/abide_regression_models.json` (generated, `--refresh`)

Schema (top level): `schemaVersion` 1, `activity` `"regression-compare"`,
`source` `{pinnedCommit, brainTableSha256, phenotypeTableSha256}`, `target`
`{name FIQ, label, unit}`, `cohort` `{n 908, requirement, diagnosisNote}`,
`crossValidation` `{kind KFold, nSplits 5, shuffle true, randomState 0,
foldTrainN 726}`, `preprocessing`, `observed` (908 ints), `foldOf` (908 ints
0–4), `bundles` `{key → {label, rois[]}}`, `measures` `{key → {label, unit}}`,
`measurementSubsets` `[[…]]`, `models` `[{key, bundle, measures[], featureCount,
disabled, reason?, predicted?[908], cvR2?, cvMSE?}]`.

35 models, 34 enabled + `all-eligible__CT+Area` (p 716) disabled. All 34
`cvR2 < 0`. `frontoparietal__CT` (default A) −0.171 / MSE 273.2;
`occipital__CT` (default B) −0.040 / MSE 242.6; `all-eligible__CT` −1.208.
73 485 → 287 483 bytes. SHA-256
`6ef2cb10f18b3283e9dd491be815b3984ddf8a5e7fc811f64b976d079b61853f`. Two
`--refresh` runs byte-identical.

`abide_histogram.json`, `abide_retention.json`, `abide_table_inspection.json`:
**untouched** (`export_widget_data.py --check --artifact all` still OK for all
three).

---

## 6. NEW `book/_static/widgets/configs/regression_compare.json`

`schemaVersion` 1, `type` `regression-compare`, `data`
`../data/abide_regression_models.json`. Fields: `title`, `description`,
`instructions`, `targetLabel`, `measurementSubsets`
(`[{measures:["CT"],label},{["Area"]},{["Vol"]},{["LGI"]},{["CT","Area"]}]`),
`bundles` (7: frontoparietal, frontal, parietal, temporal, occipital,
sensorimotor, all-eligible), `defaultA` `{measures:["CT"],bundle:"frontoparietal"}`,
`defaultB` `{measures:["CT"],bundle:"occipital"}`, `literatureNote`
(verified DOIs + Glasser mapping), `selectionBiasNote`, `reflectionPrompts` (3).
SHA-256 `1795ff48f69e49a95a8df71c69667a3a84bc8bda894729bd0c0c6ff4a0bc92c2`.

---

## 7. `interactive/src/config.ts`

- **Added** `regressionMeasurementSubset`, `regressionBundleRef`,
  `regressionModelChoice`, `regressionCompareConfig` (strict object:
  `type` literal `"regression-compare"`, `instructions`, `targetLabel`,
  `measurementSubsets` (≥1), `bundles` (≥2), `defaultA`, `defaultB`,
  `literatureNote`, `selectionBiasNote`, optional `reflectionPrompts`).
- `activityConfigSchema` discriminated union: **+ `regressionCompareConfig`**
  (now 6 members).
- **Added** `export type RegressionCompareConfig`.
- `checkSemantics`: **added** a `regression-compare` branch — no duplicate
  bundle keys, no duplicate measure combinations, `defaultA`/`defaultB`
  `.bundle` ∈ `bundles` and `.measures` join ∈ `measurementSubsets` joins.

---

## 8. NEW `interactive/src/regression-compare.ts`

Pure helpers: `r2Score` (not clamped — negative is valid; throws on length
mismatch / zero variance), `meanSquaredError`, `scatterPoints`,
`sharedAxisRange(values, padFrac=0.05)`, `catalogKey({bundle, measures})` →
`"<bundle>__<m>+<m>"`.

## 9. NEW `interactive/src/regression-compare-data.ts`

Zod schema + `parseRegressionCatalog`. `superRefine` enforces: no
identifier-shaped top-level key; `observed` length == `cohort.n` and all
integers; `foldOf` aligns and uses every fold index `0..nSplits-1`;
`measurementSubsets` reference known measures; unique model keys; model
`bundle`/`measures` reference the maps; disabled models carry a reason and no
predictions; enabled models' `predicted` aligns with `observed` and their
`cvR2`/`cvMSE` recompute (±1e-3 / ±1e-1) via `regression-compare.ts`; ≥1
enabled model.

## 10. NEW `interactive/src/components/regression-compare.ts`

`regressionCompareComponent` (`type "regression-compare"`,
`parseData: parseRegressionCatalog`). `mount`:
- config×data consistency check (every offered bundle/measure/catalog entry must
  exist) → throws a readable error otherwise;
- header, a `<details>` literature note (`data-testid
  regression-literature-note`), a cohort/folds line
  (`regression-cohort`), a `.widget-compare-grid` of two panels, a
  `selectionBiasNote` paragraph (`regression-selection-bias`), optional Reflect
  list;
- each panel (`regression-panel-A` / `-B`): measurement `<select>`
  (`regression-A-measures`), bundle `<select>` (`regression-A-bundle`), a
  metrics line (`regression-A-metrics`), a Plotly `.widget-plot`
  (`regression-A-plot`, `data-render-count`), a disabled message
  (`regression-A-disabled`), a `<details>` ROI list
  (`regression-A-roi-summary` / `-roi-list`);
- on any control change: look up `catalogKey`, set `panel.dataset`
  (`modelKey`, `featureCount`, `disabled`, `r2`, `mse`); if disabled → purge +
  hide the plot, show the reason; else `Plotly.react` an observed-vs-oof-pred
  `scattergl` + a dashed diagonal on the **shared** axis range, recompute
  R²/MSE from the stored predictions for the metrics line;
- `destroy()` purges both plots.

## 11. `interactive/src/components/registry.ts`

`import { regressionCompareComponent } from "./regression-compare";` +
`registry.register(regressionCompareComponent);` (now 6 components).

## 12. `interactive/src/styles.css`

**Appended** a `/* regression-compare activity */` block: `.widget-note`
(+ `summary`, `p`), `.widget-roi-list`, `.widget-compare-grid`
(`repeat(auto-fit, minmax(300px, 1fr))`), `.widget-compare-panel`,
`.widget-compare-panel .widget-plot`. No existing rule changed.

---

## 13. NEW `book/chapters/chapter_02/exercise_02.ipynb` (35 cells)

Authored deterministically (fixed ids `wp11-001`…`wp11-061`) and executed
end-to-end (network) so committed outputs are current. 21 markdown + 14 code
(9 visible, 4 `hide-input`, 1 `hide-cell`). `nbformat.validate` OK.

| id | kind | content |
|---|---|---|
| `wp11-001` | md | H1 `# Exercise II: Regression` |
| `wp11-002` | md | `{admonition} Run or download` (own cell → dropped in portable) |
| `wp11-003` | md | `## What this notebook covers` (5-item list) + Prerequisites |
| `wp11-010` | md | `## 1. The modelling table` — row = participant; column kinds |
| `wp11-011` | code `hide-cell` | imports; pinned URLs; load `abide2.tsv` + `abide2_phenotypic.csv`; merge; `BRAIN_COLS`/`PHENO_COLS`; print `1004 x 1452` |
| `wp11-012` | code | compact preview (`head(4)` of 6 phenotype + 3 brain columns); count summary (10 phenotype, 1440 brain, 0 missing, FIQ 908/1004) |
| `wp11-013` | md | **Think first** (outcome/features/row/measures/encoding) + `Check your reasoning` |
| `wp11-020` | md | `## 2. One honest linear-regression workflow` — pre-declared frontoparietal-CT recipe, 78 features |
| `wp11-021` | code | `FRONTOPARIETAL = [...39 Glasser labels...]` (== manifest); `bundle_columns`; `FEATURES`; leakage asserts |
| `wp11-022` | code | brain-only `X`, `y=FIQ`, drop missing; `train_test_split(0.25, random_state=42, stratify=groups)` → `n_train=681 n_test=227` |
| `wp11-023` | code | `make_pipeline(StandardScaler(), LinearRegression())`; fit train; predict test; **held-out R² −0.120, MSE 284.0** |
| `wp11-024` | code `hide-input` | observed-vs-predicted scatter + diagonal, equal axes |
| `wp11-025` | md | hyperplane not drawable; negative R² valid; population = same-17-sites |
| `wp11-026` | md | **Think first** (a task the held-out score does not speak to) + `Check your reasoning` (new site/scanner) |
| `wp11-030` | md | `## 3. Three ways to score the same model` — A/B/C table + **Think first** (predict the ordering) |
| `wp11-031` | code | `train_r2` (B); `invalid_test_fitted_model` fit+score on test (C); a 3-row `scores` DataFrame; print n_train/n_test/p |
| `wp11-032` | code `hide-input` | 3 aligned observed-vs-predicted panels, shared limits |
| `wp11-033` | md | B/C are not competing models; A vs C isolates contamination; + `Check your reasoning: the ordering` (C>B>A) |
| `wp11-040` | md | `## 4. Comparing feature sets` — P-FIT / Narr, verified DOIs, Glasser mapping; "hypothesis, not a guarantee" |
| `wp11-041` | md | `<iframe title="Interactive feature-set comparison for predicting IQ from brain structure" src="../../_static/widgets/app/index.html?config=../configs/regression_compare.json" height="1180">` |
| `wp11-042` | md | **Think first** (measurement vs bundle; does P-FIT win; all-eligible) + selection-bias paragraph |
| `wp11-050` | md | `## 5. What does sample size change?` |
| `wp11-051` | md | `### A. Two outcomes with different availability` + **Think first** |
| `wp11-0515` | code | availability table (usable N, by group, sites-with-any) for FIQ vs SRS_TOTAL_RAW |
| `wp11-052` | code | `holdout_r2(target)`; **FIQ −0.120, SRS_TOTAL_RAW −0.198** |
| `wp11-053` | md | different outcomes cannot isolate sample size; MSE scales differ; use R² |
| `wp11-054` | md | `### B. Match the high-N target to the low-N target` |
| `wp11-055` | code | fixed FIQ held-out; **matched training N 573** (full 681); 300 seeded draws; mean −0.150, 5–95 pct [−0.196, −0.108]; full −0.120; SRS −0.198 |
| `wp11-056` | code `hide-input` | histogram of matched-N held-out R² with the three markers |
| `wp11-057` | md | `### C. Learning curve, same target` |
| `wp11-058` | code | sizes `[120,200,320,460,600,681]`, 40 reps; prints n/p 1.5 and mean + 10–90 pct per size |
| `wp11-059` | code `hide-input` | learning-curve figure (mean + 10–90 band, zero line) |
| `wp11-05a` | md | `{admonition}` "What the learning curve shows — and does not" |
| `wp11-060` | md | `## In summary` — 6 points; one forward-looking sentence (no KNN/bias–variance heading) |
| `wp11-061` | md | `### Questions to take away` — 7 reasoning prompts |

SHA-256 `5702670b5ecfb115fcf71bc1623516973f53f985dd7340d18feb9b5a592eefd9`.

---

## 14. `book/_toc.yml`

```diff
   - file: contents
     sections:
       - file: chapters/chapter_01/exercise_01
+      - file: chapters/chapter_02/exercise_02
```

`book/contents.md`, `book/intro.md`, `book/syllabus.md`, `book/_config.yml`:
**unchanged** (`exclude_patterns: downloads/*` already covers
`downloads/chapter_02/`).

---

## 15. `scripts/build_portable_notebook.py` (multi-notebook refactor)

- **Added** `@dataclass(frozen=True) NotebookSpec` (key, canonical, portable,
  published_page, banner_source, setup_source, lesson_packages,
  drop_admonition_titles, iframe_replacements, preserve_output_ids,
  rewrite_columns, require_pinned_source, extra_banned).
- **Added** `CHAPTER_01` spec (values identical to the old module constants) and
  `CHAPTER_02` spec (published page
  `…/chapters/chapter_02/exercise_02.html`; `lesson_packages`
  `"numpy pandas matplotlib scikit-learn"`; one iframe replacement keyed by
  `"Interactive feature-set comparison for predicting IQ from brain structure"`;
  `preserve_output_ids=frozenset()`; `rewrite_columns=False`).
  `NOTEBOOKS = {chapter_01, chapter_02}`.
- Back-compat aliases kept: `CANONICAL`, `PORTABLE`, `BANNER_ID`, `SETUP_ID`,
  `SETUP_INSTALL_ID`, `PUBLISHED_PAGE`, `IFRAME_REPLACEMENTS`,
  `DROP_ADMONITION_TITLES`, `PRESERVE_OUTPUT_IDS`, `LESSON_PACKAGES`,
  `HIDE_TAGS`, `convert_myst_directives`, `serialize` — all unchanged values.
- `build_portable(canonical_nb, columns, spec=CHAPTER_01)` — **signature-compatible**;
  threads `spec` through `_banner_cell` / `_setup_cell` / `_setup_install_cell`
  and the cell loop (which now uses `spec.drop_admonition_titles`,
  `spec.iframe_replacements`, `spec.rewrite_columns`,
  `spec.preserve_output_ids`).
- `_assert_portable(nb, spec=CHAPTER_01)` — the `CURATED_COLUMNS` assertions are
  guarded by `spec.rewrite_columns`; the "≥1 output only on preserve ids" and
  "pinned source URL present" checks are parametrised; everything else
  unchanged.
- `main()` — `--write` / `--check` iterate `NOTEBOOKS` (or the one named by the
  new `--notebook {chapter_01,chapter_02,all}`; default `all`). Bare
  `--check` (CI) now also checks chapter_02.

**`book/downloads/chapter_01/exercise_01_portable.ipynb` is byte-identical** to
its pre-WP11 state (verified; `--check` "up to date (75 cells)").

## 16. NEW `book/downloads/chapter_02/exercise_02_portable.ipynb` (generated, `--write`)

37 cells (35 canonical + `portable-banner` / `portable-setup` /
`portable-setup-install`, − 1 dropped "Run or download" admonition cell). Banner
names *Machine Learning for Neuroscience* and links the published Exercise II
page. `# %pip install numpy pandas matplotlib scikit-learn` (commented). The
`wp11-041` iframe cell → a Markdown pointer to the published page. No MyST
fence, `<iframe`, `_static/`, `../../config/`, `requirements.txt`, hide tag,
`%pip`/`!pip`, `colab.research.google.com/github`, or `ipywidgets`. All code
cells output-free, `execution_count` None. SHA-256
`2514f6ebc153de11f69f7b26e0f286ac18b6a68b8c2231581007356f3aa186a0`.

## 17. `scripts/smoke_portable_notebook.py`

- **Before:** module constants `PORTABLE`, `EXPECTED_SUBSTRINGS`; `main()` runs
  the one chapter_01 notebook.
- **After:** `SMOKE = {chapter_01: {path, expect:("Data table shape: (1114, 13)",
  "Complete for all 13 variables")}, chapter_02: {path, expect:("1004
  participants", "held-out R^2 =", "n_features (p) = 78")}}`; `_run_one(key,
  spec)`; `main(argv)` with `--notebook {chapter_01,chapter_02,all}` (default
  `all`); timeout 300 → 600. Out-of-repo run: `OK [chapter_01]` (20 code cells),
  `OK [chapter_02]` (15 code cells).

---

## 18. Tests

### Python (`tests/`), `unittest` — 114 → 161

| File | Δ | Contents |
|---|---|---|
| NEW `test_abide_modeling_data.py` | +19 | manifest `--check`; every bundle ROI is a real bilateral atlas label; forbidden list covers every target; the two required roles; canonical recipe refs; `parse_brain_column` valid / hyphenated / non-brain / unknown-ROI / asymmetric-hemisphere; `classify_columns` three kinds; `bundle_columns` order + all-eligible-excludes-5L/5R + unknown-measure/bundle + missing-column; `assert_brain_only` accepts brain / rejects targets+phenotypes; `feature_matrix` brain-only + drops missing target + unknown-target. Provides `synthetic_frame()` reused below. |
| NEW `test_export_regression_catalog.py` | +12 | committed artifact: `--check` passes, validator finds nothing, shape/cohort (n 908, 5 folds, int observed), **no identifier token**, source pins vs manifest, every enabled model's R²/MSE recompute, **literature bundle does not win** (all cvR²<0; frontoparietal_CT < occipital_CT), a high-p combination disabled with a reason, canonical serialization. Synthetic-frame build: round-trip + validate, no identifier column, tampered prediction rejected. |
| NEW `test_exercise_02_notebook.py` | +15 | valid + `wp11-` ids unique; H1 exact; opening has scope + prerequisites, no time budget, no course-intro repetition; cell count 28–50 and < Exercise I; only `hide-input`/`hide-cell` tags; **no KNN / bias–variance section heading** (≤1 forward-looking mention); five numbered sections present; embedded `FRONTOPARIETAL` == manifest; notebook code has the leakage guard; fixed stratified split + pipeline; `invalid_test_fitted_model` named + used once; iframe → `regression_compare.json` with the exact title; verified DOIs present; executed outputs present (`1004 participants`, `held-out R^2 = -0.`, `n_train = 681`, `n_features (p) = 78`, A/B/C rows); no committed execution error. |
| `test_book_structure.py` | +1 | `test_exercise_two_follows_exercise_one` — `_toc.yml` sections are exactly `[exercise_01, exercise_02]` and the ipynb exists. |
| `test_build_portable_notebook.py` | ±0 | unchanged (25 tests); all still green against the refactored module (default `spec=CHAPTER_01`). |
| `test_export_widget_data.py`, `test_notebook_corrections.py`, `test_table_inspection_columns.py` | ±0 | unchanged. |

### Frontend `vitest` — 187 → 217

| File | Δ | Contents |
|---|---|---|
| `tests/config.test.ts` | +8 | `describe("parseActivityConfig — regression-compare")`: valid fixture; rejects defaultA.bundle not in bundles / defaultB.measures not offered / duplicate bundle keys / duplicate measure combinations / <2 bundles / extra key; the shipped `regression_compare.json` validates. |
| NEW `tests/regression-compare.test.ts` | +12 | `r2Score` (1.0 / 0.0 / negative / worked example / throws), `meanSquaredError`, `scatterPoints`, `sharedAxisRange` (padding, non-collapsing), `catalogKey`. |
| NEW `tests/regression-compare-data.test.ts` | +10 | synthetic catalog accepted; wrong activity; observed ≠ cohort.n; foldOf missing a fold; stored cvR2 disagrees; misaligned predicted; disabled model with predictions; identifier-shaped key; unknown bundle; **committed `abide_regression_models.json`** parses (n 908, 5 folds, >20 enabled, every metric recomputes, frontoparietal_CT < occipital_CT < 0). |

### Playwright standalone (`interactive/e2e/`) — 50 → 60

NEW `regression-compare.spec.ts` (5 tests × site-root + subpath): both panels
render + defaults (frontoparietal-CT p 78, occipital-CT p 46) + negative-R²
metrics text + no socket/failed; changing the bundle recomputes plot + metrics
(`data-r2` changes, render count increments, p 78 → 358); an unsupported
`p ≥ n` combination shows its reason and hides the plot; the ROI list reveals
(`IPS1`, `46`); 390 px with no horizontal document scroll + keyboard-reachable
select.

### Playwright built-book (`interactive/e2e-book/`) — 16 → 19

NEW `chapter02.spec.ts` (3): iframe loads on the built Exercise II page under the
project subpath, config + data HTTP 200, both panels render with the right
feature counts, a real control change (`all-eligible` → p 358, `data-r2`
changes), no CDN/kernel/socket/off-origin; browser refresh restores defaults
(`occipital`); 390 px viewport, no horizontal overflow.

---

## 19. Commands run (no repository mutation beyond local commits)

```
git checkout -b feature/regression-practice
git add WPs/WP11_NOTEBOOK2_LINEAR_REGRESSION.md
git commit -m "checkpoint: before WP11"                      # 7b69864
git tag -a wp11-start -m "Checkpoint before WP11 (Exercise II linear regression)"
# baseline (before): python -m unittest discover -s tests ;
#   (cd interactive && npm test && npm run test:e2e && npm run test:e2e:book) ;
#   npm audit --omit=dev ; export_widget_data.py --check --artifact all ;
#   build_portable_notebook.py --check ; rm -rf book/_build ; jupyter-book build book ;
#   smoke_portable_notebook.py ; 2x clean build figure-hash compare
python scripts/abide_modeling_data.py --audit          # data audit
python scripts/abide_modeling_data.py --check
python scripts/export_regression_catalog.py --refresh  # writes abide_regression_models.json
python scripts/export_regression_catalog.py --check
python .../author_ex2.py                               # writes exercise_02.ipynb (scratch authoring script)
(cd book/chapters/chapter_02 && jupyter nbconvert --to notebook --execute --inplace exercise_02.ipynb)
python scripts/build_portable_notebook.py --write      # ch1 no-op, ch2 written
python scripts/smoke_portable_notebook.py              # both, out of repo
python -m unittest discover -s tests                   # 161 / 161
(cd interactive && npm test && npm run test:e2e && npm run test:e2e:book)   # 217 / 60 / 19
rm -rf book/_build ; jupyter-book build book           # 2 warnings, no *.err.log
for i in a b ; do rm -rf book/_build ; jupyter-book build book ; done   # identical 9-PNG hash set
git add -A ; git reset -- WPs/reports/
git commit -m "WP11: Exercise II linear regression, feature-set comparison activity, modelling data pipeline"
git add WPs/reports/WP11_REPORT.md WPs/reports/WP11_EXACT_CHANGELOG.md
git commit -m "WP11 report: document Exercise II linear regression"
```

No `git reset --hard`, `git checkout -- <path>`, `git clean`, `git rebase`,
`git revert`, `git push`, `git merge`, `--force`, or `--force-with-lease`. No
repository setting, secret, branch-protection rule, or Pages configuration
changed. No `book/_build`, `book/.jupyter_cache`, `book/_static/widgets/app`,
`interactive/node_modules`, `__pycache__`, or Playwright artifact staged.
`book/config/abide_modeling.json` and
`book/_static/widgets/data/abide_regression_models.json` are committed source
assets, not build output.
