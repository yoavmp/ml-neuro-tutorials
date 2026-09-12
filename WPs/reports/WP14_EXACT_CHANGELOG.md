# WP14 — exact change log

Location-specific before/after. Notebook cells are referenced by stable
`nbformat` id. It should be possible to review the substantive work from this
file without diffing raw notebook JSON.

Branch `feature/regression-practice`; checkpoint `588a4c4` (tag `wp14-start`);
implementation commit `d5fbecc`.

---

## 1. Git objects

| Item | Value |
|---|---|
| Checkpoint commit | `588a4c4855bf0fd443b69a1aa69996c69469493f` — `checkpoint: before WP14` (adds `WPs/WP14_EXERCISES_2_AND_3_PEDAGOGICAL_REVISIONS.md`, 1 file, +494) |
| Annotated tag | `wp14-start` → `588a4c4` (tag object `ec0624f2fbefdd8c2f3c0f6002c8e06ab3ab34bd`; name free, no suffix) |
| Implementation commit | `d5fbecc40f34c8458d71c17d9813c67997bbd486` — `WP14: correct 360-parcel feature recipe; Exercises 2-3 pedagogical revisions` (35 modified, 9 new; 4431 insertions, 2328 deletions) |
| Report commit | adds the two report files only |

Tags `wp01-start`…`wp13-start` and all prior branches untouched. No push,
merge, force, rebase, revert, or history rewrite.

---

## 2. The 360-parcel audit and fix (WP14 §1)

### 2.1 Raw-data finding

Downloaded and hash-verified the pinned `abide2.tsv` (sha256
`ad0db42f85c77cbb8b4e023df288d34b29f1a63870a0cf1955c5b3b0d357579e`, matches
`book/config/abide_modeling.json`'s pin) and inspected the real column names
directly (not through the parser). For every one of the four measures
(`fsCT`, `fsArea`, `fsVol`, `fsLGI`), the left-hemisphere columns contain
exactly 180 distinct raw ROI labels and the right-hemisphere columns contain
exactly 180 distinct raw ROI labels; every label is shared between
hemispheres **except one**: the left column is raw-labelled `5L`
(`fs<measure>_L_5L_ROI`) and the right column is raw-labelled `5R`
(`fs<measure>_R_5R_ROI`) — never `fs<measure>_R_5L_ROI` or
`fs<measure>_L_5R_ROI`. Both columns are genuine continuous FreeSurfer
measurements (e.g. `fsCT_L_5L_ROI` and `fsCT_R_5R_ROI`: 1004/1004 non-null,
range 1.30–3.42 mm, mean ≈2.32 mm — a plausible cortical-thickness range
indistinguishable from any neighbouring parcel), not identifiers,
aggregates, or malformed fields. **Conclusion: this is one genuinely
bilateral HCP-MMP1 parcel (canonical id `"5"`) whose two hemisphere columns
simply do not share a common raw-label suffix in this particular source
table** — not two single-hemisphere ROIs, which is what WP12's manifest and
`scripts/abide_modeling_data.py` assumed. Every other measure/hemisphere
combination has exactly 180 real, shared-label parcels, so the audit
confirms **180 canonical parcels × 2 hemispheres = 360 genuine columns per
measurement family**, for all four families.

### 2.2 `book/config/abide_modeling.json` (`atlas`)

```diff
- "asymmetric_labels": ["5L", "5R"],
- "roi_label_inventory": [...181 raw labels incl. "5L", "5R"...],
- "bilateral_label_count": 179
+ "hemisphere_specific_labels": {
+   "5": {"L": "5L", "R": "5R", "note": "WP14 audit ... <full provenance note>"}
+ },
+ "roi_label_inventory": [...180 canonical ids, "5L"/"5R" replaced by "5"...],
+ "bilateral_label_count": 180
```

- `protocol.canonical_recipe.note`: `p=358` → `p=360`, wording updated to
  reference the corrected 360-parcel definition and this WP's audit.
- `catalog.identifiability_rule`: `all-eligible x [CT,Area] (p=716)` →
  `(p=720)`.
- `knn.canonical_recipe.note`: `p=358` → `p=360`.
- `knn.selected_k_rationale`: rewritten with the re-audited numbers (see §4
  below); `selected_k` unchanged at `15`.
- SHA-256 `1dacce47b2eab81460f379b58dee78641a8a1d01fa0d68a4f52d22aba708c31b`.

### 2.3 `scripts/abide_modeling_data.py`

- New module-level `HEMISPHERE_SPECIFIC_LABELS` (from
  `atlas.hemisphere_specific_labels`) and `_RAW_LABEL_LOCK` (raw label →
  `(canonical_roi, required_hemisphere)`), replacing `ASYMMETRIC_LABELS`.
- New `raw_label_for(roi, hemi, manifest=None)` — the literal column-name
  label for a canonical ROI id in one hemisphere; identity for ordinary
  ROIs, looked up for the one hemisphere-specific ROI.
- `parse_brain_column`: now resolves a raw label through `_RAW_LABEL_LOCK`
  first (validating the required hemisphere), falling back to the plain
  inventory check; `BrainColumn.roi` stays the literal raw label (`"5L"` /
  `"5R"`), preserving prior parsing semantics for ordinary ROIs.
- `classify_columns`: `roi_count` now canonicalises `"5L"`/`"5R"` to `"5"`
  before counting distinct ROIs (180 on the real data, not 181).
- `bundle_rois("all-eligible", ...)`: now returns
  `list(manifest["atlas"]["roi_label_inventory"])` directly — no exclusion
  filter (every canonical ROI is genuinely bilateral).
- `bundle_columns`: per-hemisphere column names now go through
  `raw_label_for(roi, hemi, manifest)` instead of assuming the raw label
  equals the ROI id; the `ASYMMETRIC_LABELS` early-raise branch is gone.
- `_check_manifest`: replaced the `asym`-set logic with validation of
  `hemisphere_specific_labels` (canonical id is in the inventory; exactly
  two distinct L/R raw labels) and `bilateral_label_count == len(inventory)`;
  the two "does the leak pattern wrongly reject a real column" loops now
  build column names through the same `raw_label_for` lookup instead of
  naive string interpolation.

Net effect: `amd.bundle_columns("all-eligible", ["CT"])` returns 360 column
names (was 358); `amd.ROI_INVENTORY` has 180 entries (was 181, including the
two malformed `"5L"`/`"5R"` entries).

### 2.4 `scripts/export_regression_catalog.py`

```diff
  "rois": (
-     [r for r in manifest["atlas"]["roi_label_inventory"]
-      if r not in manifest["atlas"]["asymmetric_labels"]]
+     list(manifest["atlas"]["roi_label_inventory"])
      if b == "all-eligible"
      else list(manifest["bundles"][b]["rois"])
  ),
```

### 2.5 Tests

- `tests/test_abide_modeling_data.py`: replaced
  `test_all_eligible_excludes_asymmetric_labels` with
  `test_atlas_inventory_is_exactly_180_bilateral_parcels` and
  `test_all_eligible_bundle_is_exactly_360_ct_columns`; renamed
  `test_enforces_hemisphere_of_asymmetric_labels` →
  `test_enforces_hemisphere_of_hemisphere_specific_labels` (now checks both
  `5L`→L and `5R`→R, and both mismatches raise); added
  `test_raw_label_for_hemisphere_specific_and_ordinary_rois`;
  `test_every_bundle_roi_is_a_real_bilateral_atlas_label` no longer checks
  an `asym` set (nothing is excluded any more). 23/23 pass.

---

## 3. Regenerated audits and artifacts (WP14 §1, §7.1–2)

All regenerated via each script's own `--run` / `--refresh` (network,
pinned-hash-verified sources), then `--check` (offline, canonical
byte-for-byte). No stored metric was hand-edited.

| Script | Command | Key result after (before, WP13) |
|---|---|---|
| `scripts/regression_model_audit.py` | `--run` | age/linear/all-eligible×CT locked holdout: **p=360, R²=0.4692, MSE=49.55** (p=358, R²=0.475, MSE≈49.0) |
| `scripts/export_regression_catalog.py` | `--refresh` | `all-eligible__CT`: **p=360, cvR²=+0.465** (p=358, ≈+0.46); `all-eligible__CT+Area` now **p=720 DISABLED** (was p=716) |
| `scripts/knn_model_audit.py` | `--run` | canonical (all-eligible×CT): **p=360, selected k=15** (unchanged), **cvR²=+0.5995, test R²=+0.6492, test MSE=32.75** (p=358, k=15, test R²=0.647, MSE=33.0) |
| `scripts/export_knn_explore_data.py` | `--refresh` | **p=360**, N_fit=564, N_val=189 (unchanged sizes), validation-optimal k=**17** (unchanged), fitting-set mean **15.192373** |
| `scripts/export_knn_abc_data.py` (NEW) | `--refresh` | **p=360**, n_train=753, n_test=251, k_max=251, default k=15 |

Selected `k` (15) and validation-optimal `k` (17) are numerically unchanged
by the 360-parcel correction; the underlying R²/MSE values at every `k`
shifted slightly. This is reported, not assumed: WP14 §1 explicitly warned
against assuming WP12/WP13 numbers survive unchanged, and the audit was
rerun in full before any notebook content was written.

`scripts/regression_model_audit_result.json` and
`scripts/knn_model_audit_result.json` were regenerated in place (existing
files, same schema, new numbers — not new files).

---

## 4. NEW `scripts/export_knn_abc_data.py`

Deterministic export for the new Exercise 3 Section 3 "honest vs invalid"
interactive (WP14 §4.4). Public surface:

- `_outer_split(frame, manifest)` — Exercise 2's own locked
  `train_test_split(test_size=0.25, random_state=42, stratify=group)` on the
  360-feature canonical recipe; returns both train **and** test arrays
  (unlike `export_knn_explore_data.py`'s `_outer_split`, which only needs
  the training partition).
- `_sorted_neighbor_targets(X_query, X_ref, y_ref, top)` — per-query
  reference-set targets sorted nearest-first, truncated to `top` = `k_max =
  min(n_train, n_test) = 251`.
- Three independently fit/queried panels:
  - **A**: one `StandardScaler` fit on the 753 training rows; query = 251
    test rows.
  - **B**: the *same* scaler/pool as A; query = the 753 training rows
    themselves (self-inclusive resubstitution).
  - **C**: a *separate* `StandardScaler` fit on the 251 test rows only
    (deliberately invalid); query = those same 251 test rows.
- `_validate_panel_against_sklearn(...)` — fits a real
  `Pipeline(StandardScaler(), KNeighborsRegressor(k))` for representative
  `k ∈ {1,5,15,17,50,100,251}` per panel and asserts `np.allclose` (`atol=1e-6`)
  against the cumulative-sum predictions before anything is written; an
  earlier draft fit the sklearn comparison model directly on raw
  (unscaled) features and was caught and fixed by this check (max abs
  diff 40.0 at k=1 before the fix — see §9 below).
- Structural k=1 endpoint assertions: `sorted_b[:, 0] == y_train` and
  `sorted_c[:, 0] == y_test` exactly (`atol=1e-9`) — every query point is
  its own nearest neighbour in the self-referential panels.
- `build_artifact` / `validate_artifact` (shape, `kMax == min(nTrain,
  nTest)`, k=1 endpoints, no identifier-shaped key) / `--refresh` / `--check`.

---

## 5. NEW `book/_static/widgets/data/abide_knn_abc.json` (generated, `--refresh`)

1,850,283 bytes. SHA-256
`07dc7107c447affc54c92bb53cb51d4eba63f1ca315623411d45c9a89e84515e`.
Contents: `observedTrain` (753 ages), `observedTest` (251 ages),
`neighborTargetsA` (251×251), `neighborTargetsB` (753×251),
`neighborTargetsC` (251×251) — age values only, reordered nearest-first,
truncated to the shared `kMax=251`; no participant id, brain feature, site,
or diagnosis anywhere (enforced by `validate_artifact`'s identifier-key
scan and `interactive/src/knn-abc-data.ts`'s `IDENTIFIER_TOKEN` check).

---

## 6. `book/_static/widgets/data/abide_knn_explore.json` (regenerated, schema bump 1→2)

2,719,089 bytes (was 697,322, WP13's committed value). SHA-256
`e3ceb0ff4d1e2d2dab8f3eecd1eefacf951de57efa4bbefba41a6819ad01794e`.

- `schemaVersion: 1 → 2`.
- All existing fields (`observedValidation`, `observedFitting`,
  `neighborTargetsByProximity`, `curve.*`, `fitTargetMean`,
  `validationOptimalK`, `selectedKFromAudit`) recomputed on the 360-feature
  recipe; same shape/semantics as WP13.
- **New** `trainingSamples: {A, B, C}` (WP14 §4.8), each
  `{fitTargetMean, neighborTargetsByProximity}` (189×564):
  - `A` is byte-identical to the top-level baseline (the actual, unresampled
    564-row fitting set).
  - `B`, `C` are independent bootstrap resamples (with replacement, size
    564) of the same fitting pool, seeds 101 / 102
    (`scripts/export_knn_explore_data.py::BOOTSTRAP_SEEDS`), **each with its
    own `StandardScaler` refit on its own resampled raw rows** — a genuine
    "what if you had drawn a different training sample" refit, not a
    relabelling. Each independently validated against a real
    `Pipeline(StandardScaler(), KNeighborsRegressor(k))` at representative
    k and asserted to predict its own resampled mean at k=n_fit.

`build_artifact`/`validate_artifact` extended: `trainingSamples` must have
exactly keys `A, B, C`; every sample's `neighborTargetsByProximity` must
align with `nFit`/`nValidation`; every sample's k=n_fit endpoint (checked
via its first row) must match its own `fitTargetMean`; `trainingSamples.A`
must equal the top-level `neighborTargetsByProximity`/`fitTargetMean`
exactly.

`abide_regression_models.json`: regenerated (360-feature `all-eligible`
entries; `all-eligible__CT+Area` newly disabled at p=720).
`abide_histogram.json`, `abide_retention.json`, `abide_table_inspection.json`:
**untouched**.

---

## 7. Interactive (TypeScript) layer

### 7.1 NEW `interactive/src/knn-abc-data.ts`

Zod schema + `parseKnnAbcData` for the artifact in §5. Validates array
shapes against `split.{nTrain,nTest,kMax}`, `kMax == min(nTrain, nTest)`,
the k=1 structural endpoints (`neighborTargetsB[:,0] == observedTrain`,
`neighborTargetsC[:,0] == observedTest`), `selectedKFromAudit` range, no
identifier-shaped key (same `IDENTIFIER_TOKEN` pattern as
`regression-compare-data.ts` / `knn-explore-data.ts`).

### 7.2 NEW `interactive/src/components/knn-abc.ts`

Production activity component (WP14 §4.4/§4.6). Slider (`data-testid`
`knn-abc-k-slider`, `1..kMax`) **and** a synchronized numeric input
(`knn-abc-k-number`) — typed values are clamped/rejected if non-integer or
out of `[1, kMax]` (the number field snaps back to the last valid `k` rather
than producing an invalid model). Three panels (A/B/C), each a Plotly
observed-vs-predicted scatter (`knn-abc-panel-{a,b,c}-plot`) with a real
`R2`/`MSE` line (`knn-abc-panel-{a,b,c}-metrics`) recomputed from
`predictAllForK` on every `k` change, identical shared axis range across
all three, and a visible legend entry `"Perfect prediction (observed =
predicted)"` for the identity line (`showlegend: true` at both the layout
and trace level — WP13's original `knn-explore` scatter had
`showlegend: false`, so this is also the fix applied to it, see §7.4).

### 7.3 `interactive/src/config.ts`

- New `knnAbcConfig` Zod schema (`type: "knn-abc"`, `instructions`,
  `k1Note`, optional `reflectionPrompts`); registered in
  `activityConfigSchema`'s discriminated union; new exported type
  `KnnAbcConfig`.
- `knnExploreConfig` extended with four new required string fields:
  `trainingSampleInstructions`, `varianceProxyNote`, `biasProxyNote`,
  `kComplexityNote` (WP14 §4.8/§4.9/§4.10 caveat text, config-driven so the
  exact wording lives in one reviewed place).

### 7.4 `interactive/src/components/knn-explore.ts` (WP14 §4.5/§4.6/§4.8/§4.9/§4.10)

- **Numeric input** (`knn-k-number`) added beside the existing slider,
  bidirectionally synced (`input`/`change` listeners both directions);
  out-of-range or non-integer values are rejected and the field reverts to
  the last valid `k`.
- **Identity-line legend fix**: the observed-vs-predicted scatter's layout
  now sets `showlegend: true` (was `false`) and the diagonal trace's `name`
  is the literal `"Perfect prediction (observed = predicted)"` (was
  `"perfect prediction"`, never shown).
- **Three training-sample tabs** (`knn-sample-tab-{A,B,C}`, `role="tab"`,
  `aria-selected`) switch which of `trainingSamples.{A,B,C}` feeds the
  observed-vs-predicted scatter and its y-axis title; the validation
  participants (`data.observedValidation`) and the top MSE-vs-k curve are
  unchanged by the switch — only that scatter's predictions.
- **Variance-proxy readout** (`knn-variance-proxy`): text showing
  `varianceProxy(...)` (new pure function, §7.5) over the three samples'
  predictions at the current `k`, with `config.varianceProxyNote`'s caveat
  displayed alongside.
- **Bias-like-proxy panel** (`knn-bias-proxy` text + `knn-bias-plot`, a
  6-bin calibration scatter of ensemble-mean prediction vs observed age
  with the identity line): `calibrationSlope(...)` (new pure function)
  computed from `ensembleMeanForK(...)` at the current `k`, with
  `config.biasProxyNote`'s caveat displayed alongside.
- New `kComplexityNote` paragraph rendered near the top of the activity.
- `draw()` now also calls `drawVarianceAndBias()` on every `k` change.

### 7.5 `interactive/src/knn-explore.ts` (pure helpers)

Three new exported functions, unit-tested, no DOM:

- `varianceProxy(samplePredictions)` — mean, across query points, of the
  SD of ≥2 samples' predictions for that point; throws for fewer than two
  samples.
- `calibrationSlope(observed, ensemblePredicted)` — OLS slope of
  ensemble-mean prediction regressed on observed value (covariance /
  variance of observed; 0 if the observed variance is 0).
- `ensembleMeanForK(samples, k)` — per-query mean of `predictAllForK`
  across several sample matrices at a fixed `k`.

### 7.6 `interactive/src/components/registry.ts`

- Imports and registers `knnAbcComponent` (type `"knn-abc"`). No existing
  registration changed.

### 7.7 `interactive/src/styles.css`

- New `.widget-number-input` (the numeric k field) and `.widget-tabs` /
  `.widget-tabs button` (the training-sample pill tabs, including an
  `aria-selected="true"` highlighted state and `:focus-visible` outline)
  rule blocks. No existing rule changed.

---

## 8. `book/_static/custom.css` (WP14 §2 — shared blue Think first)

- New root tokens (light): `--ml-think-border`, `--ml-think-border-strong`,
  `--ml-think-accent`, `--ml-think-accent-ink`, `--ml-think-accent-soft`
  (blue, deliberately distinct from the existing rust `--ml-accent`family).
  New matching tokens under `html[data-theme="dark"]` (as `--ml-think-*`
  variables lifted for dark-background legibility).
- The old combined selector block
  `.admonition.think-first, .admonition.challenge, .admonition.how-to-use`
  (all three sharing the rust accent) is **split**: `.challenge` /
  `.how-to-use` keep the original rust rules verbatim (unchanged
  appearance); `.admonition.think-first` gets its own new rule block using
  the `--ml-think-*` tokens (blue border/header background/ink, same `?`
  glyph mark, same border-radius/spacing pattern).
- The shared focus-visible and print-media rules (which listed all three
  classes together) are left as-is — generic behaviour, not colour.

No canonical notebook needed a markup change for this: `exercise_01.ipynb`
already used `:class: think-first` on every Think first block (established
in WP06); the CSS split alone changes its rendered colour from rust to
blue. `exercise_02.ipynb` and `exercise_03.ipynb`'s Think first blocks
(which previously used `:class: note`, the theme's default styling) were
migrated to `:class: think-first` as part of each notebook's full rewrite
(§9/§10 below).

---

## 9. `book/chapters/chapter_02/exercise_02.ipynb` (rewritten, 31→29 cells)

Authored via a scratch nbformat script (not committed) and executed
end-to-end twice; clean, zero execution errors, zero stderr. SHA-256
`8c28c9af61874ec99a82589ca8b8702796f7b9692396f29962c1662d580430f4`.

| id | status | change |
|---|---|---|
| `wp11-001` | unchanged | H1 title |
| `wp11-002` | unchanged | run/download admonition |
| `wp11-003` | **edited** | added the ABIDE research-question framing paragraph (WP14 §3.2); outline item 5 (regularisation) removed, item 6→5 renumbered |
| `wp11-010` | **edited** | dropped the `FIQ` mention from the phenotype-columns bullet and the "FIQ reappears in Section 5" sentence |
| `wp11-011` | **edited** | data loading simplified to the single brain table only — the phenotypic-CSV merge, `KEEP_PHEN`, and `phen`/`SUB_ID` handling are gone entirely (WP14 §3.1: "prefer simplifying the loader to the single prepared brain table"); `RidgeCV`/`LassoCV` imports and `KFold`/`cross_val_predict` dropped |
| `wp11-012` | **edited** | `FIQ` dropped from `preview_cols` and the printed availability line |
| `wp11-013` | **edited** | `:class: note` → `:class: think-first`; dropdown answer no longer mentions FIQ |
| `wp11-020` | **edited** | `358 features` → `360`; rewritten to introduce "explicit steps, then pipeline shortcut"; forward-reference retargeted from the removed Section 5 to the (renumbered) sample-size section |
| `wp11-021` | **edited** | `ASYMMETRIC_ROIS` exclusion removed entirely — `FEATURES = [c for c in BRAIN_COLS if c.startswith("fsCT_")]`; now 360 features |
| `wp11-022` | **edited** | removed the "without turning this into a splitting lecture" aside (WP14 §3.3); split code itself unchanged |
| `wp14-101` | **NEW** | explicit `scaler = StandardScaler(); X_train_scaled = scaler.fit_transform(X_train); X_test_scaled = scaler.transform(X_test)` + plain `LinearRegression`, printed as `explicit_r2`/`explicit_mse` (WP14 §3.4) |
| `wp14-102` | **NEW** | markdown explaining `fit_transform`/`transform`, the "scaler must never be fitted on the test set" rule, and the OLS-with-intercept scale-invariance fact, bridging into the pipeline shortcut |
| `wp11-023` | **edited**, now the "pipeline shortcut" | `make_pipeline(StandardScaler(), LinearRegression())`, now with `assert np.allclose(y_pred, explicit_pred)` proving equivalence to `wp14-101`; this is the `model` reused by every later section |
| `wp11-024` | **edited** | identity-line legend label → `"Perfect prediction (observed = predicted)"` (WP14 §4.6, applied to Exercise 2 too for consistency) |
| `wp11-025` | **edited** | `358-dimensional` → `360-dimensional`; dropped the parenthetical FIQ contrast |
| `wp11-026` | **edited** | `:class: note` → `:class: think-first` |
| `wp11-030` | **edited** | `358-feature` → `360-feature`; `:class: note` → `:class: think-first` |
| `wp11-031` | **edited** | comment `358` → `360` |
| `wp11-032` | **edited** | identity-line legend label added to each of the 3 panels |
| `wp11-033` | **edited** | `358 features` → `360 features` |
| `wp11-040` | **edited** | dropped the "(Section 5)" IQ-theory cross-reference (Section 5 no longer exists); simplified to describe only the age literature |
| `wp11-041` | unchanged | iframe (`configs/regression_compare.json`) |
| `wp11-042` | **edited** | `:class: note` → `:class: think-first`; question 2's FIQ-by-name reference reworded to "a target with a much weaker brain-based signal than age" |
| `wp12-001`, `wp12-002`, `wp12-003`, `wp12-004` | **DELETED** | entire "5. Regularisation preview: age vs FIQ" section |
| `wp11-050` | **edited**, renumbered "## 6." → "## 5." | rewritten to introduce the predeclared low-N sizes and the `n_train ≤ p` underdetermined regime |
| `wp11-058` | **edited** | `sizes = [370, 470, 570, 670, len(y_train)]` → `[50, 100, 200, 300, 400, 550, len(y_train)]`; mean→**median** + 10th/90th percentile for both R² and MSE (more robust given the extreme instability found); explicit `n_train <= p` flag printed per row |
| `wp11-059` | **edited** | single-panel R²-only plot → **two-panel** figure (MSE, log y-scale, left; R², full unclipped range, right), `n_train = p` vertical marker on both |
| `wp11-05a` | **edited** | entirely rewritten: documents the **double-descent** shape actually found in the executed output (worst point at `n_train=400`, not the smallest `n`), cites Belkin et al. 2019 (`doi:10.1073/pnas.1903070116`), explains the three regimes |
| `wp11-060` | **edited** | FIQ/regularisation bullets removed; new bullet on the scaling-then-pipeline equivalence; sample-size bullet rewritten for the double-descent finding |
| `wp11-061` | **edited** | questions 5–6 (FIQ/regularisation) removed; new question 4 (explicit-vs-pipeline equivalence) and question 6 (double-descent) added; renumbered 1–7 |

---

## 10. `book/chapters/chapter_03/exercise_03.ipynb` (rewritten, 34→34 cells)

Authored via a scratch nbformat script (not committed) and executed
end-to-end twice; clean, zero execution errors, zero stderr. SHA-256
`4c84c35b6abb077b1a62631fe8eb6f44258b941b32f1164f694bf998434ebd73`.

| id | status | change |
|---|---|---|
| `wp13-001`…`wp13-012` | unchanged / minor | title, run/download, opening scope (outline item 2 reworded for the executable-CV step), modelling-table intro/loader/preview unchanged in substance |
| `wp13-011` | **edited** | data loading simplified exactly as Exercise 2's `wp11-011` (single brain table, no phenotype merge); `cross_val_score` added to the sklearn import line |
| `wp13-020` | **edited** | `358 features` → `360`; removed *"A deterministic audit script (`scripts/knn_model_audit.py`) selected it... See the WP13 report..."* entirely (WP14 §4.2) |
| `wp13-021` | **edited** | `ASYMMETRIC_ROIS` exclusion removed — byte-identical (non-comment) to Exercise 2's `wp11-021`; now 360 features |
| `wp13-022` | unchanged | split code (comment references `groups_train`/`groups_test` for Section 5, unchanged) |
| `wp13-023` | **edited** | `:class: note` → `:class: think-first`; `R² = 0.475` → `R² = 0.469` |
| `wp14-210` | **NEW** | markdown: "Choosing k honestly" — introduces the executable training-only CV cell |
| `wp14-211` | **NEW** | `CANDIDATE_KS = [1,3,5,7,10,15,20,30,50,100,200]`; `cross_val_score` over `KFold(n_splits=5, shuffle=True, random_state=0)` on `X_train, y_train` only; `cv_results` table; `K_SELECTED = int(cv_results.loc[cv_results["mean_cv_r2"].idxmax(), "k"])` — **arises from executable code**, reproduces the audit's `k=15` (WP14 §4.3) |
| `wp14-212` | **NEW** | `hide-input` plot of mean CV R² vs `k` (log x-axis) with the selected `k` marked |
| `wp14-213` | **NEW** | markdown: "the test set played no role above" |
| `wp13-024` | **edited** | now just `knn_model = make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=K_SELECTED))` and the fit/print — the old 4-line comment naming `scripts/knn_model_audit.py` and the WP13 report is gone; `K_SELECTED` is never a literal `15` anywhere in the notebook |
| `wp13-025` | **edited** | identity-line legend label → `"Perfect prediction (observed = predicted)"` |
| `wp13-026`–`wp13-028` | **edited** | `358` → `360`; "chosen `k`" phrasing generalised (no longer names `15` as a fact independent of the CV cell) |
| `wp13-030` | **edited** | intro and Think first rewritten for the new interactive (no more fixed-`k` "same fixed split, same `k=15`" framing); `:class: note` → `:class: think-first` |
| `wp14-220` | **NEW** (replaces `wp13-031`, `wp13-032`) | `<iframe title="Interactive honest-vs-invalid KNN evaluation for predicting age from brain structure" ... config=../configs/knn_abc.json>` |
| `wp14-221` | **NEW** (replaces `wp13-033`, `wp13-034`, `wp13-035`) | markdown: the four k=1/general-k bullets from WP14 §4.4 ("at k=1, B and C are exactly perfect...", "A at k=1 is not perfect...", "increasing k averages more...") |
| `wp13-031`, `wp13-032`, `wp13-034` | **DELETED** | the static k=15 A/B/C table+figure and the separate static k=1 demonstration (`invalid_test_fitted_model`, `invalid_test_fitted_model_k1`, `knn_demo_k1` all gone) |
| `wp13-033`, `wp13-035` | **DELETED** | their accompanying prose |
| `wp13-040`, `wp13-041` | **edited** | added the "general tendency of KNN, not a guarantee" qualifier (WP14 §4.10); forward-references retargeted to "Sections 5 and 6" (was "Section 5") |
| `wp13-050`–`wp13-054` | unchanged | the empirical fit/validation curve (Section 5) — logic, splits, and endpoint assertions untouched; recomputed values only (N_fit=564, N_val=189, k=17 optimal — same as WP13, since these are dev-split numbers, not audit numbers) |
| `wp13-055` | **edited** | dropped the literal `(17)`/`(15)` parenthetical numbers (now described generically, since both are computed live rather than quoted) |
| `wp13-060` | **edited** | new opening paragraph stating the central k-complexity relationship explicitly and connecting Section 3's and Section 6's activities (WP14 §4.10); updated to mention the numeric-entry and three-training-sample additions |
| `wp13-061` | unchanged path, **edited height** | iframe `height="1500"` → `"2700"` (more content: numeric input, tabs, variance/bias panels) |
| `wp13-062` | **DELETED** | the duplicate Think first block (WP14 §4.7) — its content substantially repeated the widget's own config-driven "Reflect" prompts, which were extended instead (see `knn_explore.json`, §11 below) |
| `wp13-070` | **edited** | bullets rewritten: CV wording ("choosing k by cross-validation on the training partition only" → "executable cross-validation"); new bullets referencing the Section 3 interactive and the Section 6 variance/bias panels |
| `wp13-071` | **edited** | questions renumbered 1–9; new questions 6–7 about the training-sample and calibration panels; old question 2 ("perfect training performance") reworded to "perfect resubstitution performance" |

---

## 11. Config JSON

### `book/_static/widgets/configs/knn_explore.json` (edited)

- `curseOfDimensionalityNote`: `358` → `360`, `1432` → `1440`.
- New required fields: `trainingSampleInstructions`, `varianceProxyNote`,
  `biasProxyNote`, `kComplexityNote` (exact WP14-mandated caveat wording,
  see §7.3).
- `reflectionPrompts`: 3 → 5 entries (two new prompts about the
  training-sample tabs and the binned calibration plot, filling the role of
  the deleted notebook Think first block, §10 `wp13-062`).

### `book/_static/widgets/configs/knn_abc.json` (NEW)

`type: "knn-abc"`, `data: "../data/abide_knn_abc.json"`, `instructions`,
`k1Note` (the four-bullet k=1 explanation from WP14 §4.4, as one config
string rendered under the slider), 3 `reflectionPrompts`.

---

## 12. `scripts/build_portable_notebook.py`

- `NotebookSpec` gains two optional fields: `iframe_followup_code: dict[str,
  str]` and `iframe_followup_ids: dict[str, str]` — a runnable code cell
  inserted immediately after an iframe's markdown replacement, keyed by the
  iframe's `title` (WP14 §4.4: "replace the iframe with runnable Python
  code using a clearly editable `k_demo` variable and a three-panel static
  output").
- `build_portable`'s cell loop: after appending an iframe's markdown
  replacement, if `iframe_title in spec.iframe_followup_code`, appends a new
  code cell (fresh `outputs=[]`, `execution_count=None`) built from that
  source.
- `CHAPTER_03.iframe_replacements` gains a second entry, for the new
  `knn-abc` iframe title, plus `iframe_followup_code` /
  `iframe_followup_ids={"...": "portable-knn-abc-demo"}`: the followup cell
  defines `k_demo = K_SELECTED`, fits real
  `make_pipeline(StandardScaler(), KNeighborsRegressor(k))` models for A/B/C
  against the already-in-scope `X_train`/`X_test`/`y_train`/`y_test`, and
  renders the same 3-panel matplotlib figure as the interactive activity.
- `CHAPTER_01`, `CHAPTER_02` specs and behaviour: **byte-for-byte
  unchanged** (verified: `--check --notebook chapter_01` → up to date,
  75 cells, no diff in this commit).

---

## 13. Portable notebooks (regenerated, `--write`)

- **`book/downloads/chapter_02/exercise_02_portable.ipynb`**: 33 → **31**
  cells (dropped the regularisation-preview cells, added the two
  explicit-scaling cells; net −2). SHA-256
  `38167900e8fb45254602949a7fdc902f3c1ca0092323b15d943792109f69a8c4`.
- **`book/downloads/chapter_03/exercise_03_portable.ipynb`**: 36 → **37**
  cells (−2 static-ABC cells and their prose, +3 CV cells, +1 iframe-markdown
  cell already counted in the base 34→34 canonical change, +1 new
  `portable-knn-abc-demo` followup code cell). SHA-256
  `302ec876316c2feabd0f33f4a51d8c73cc1a6d14272c7670b70755c29dbcd8d3`.
- **`book/downloads/chapter_01/exercise_01_portable.ipynb`**: verified
  byte-identical (`--check` → "up to date", 75 cells; not present in this
  commit's diff).
- `_assert_portable` re-ran for both regenerated notebooks: no MyST
  directive, iframe, `_static/` path, repo-relative config path,
  `requirements.txt` instruction, hide tag, active install command, or
  self-referential Colab link.

---

## 14. `scripts/smoke_portable_notebook.py`

- `SMOKE["chapter_02"].expect`: `"n_features (p) = 358"` →
  `"n_features (p) = 360"`.
- `SMOKE["chapter_03"].expect`: added `"selected k = 15"`; `"held-out R^2 =
  0.647"` → `"held-out R^2 = 0.649"`.
- Out-of-repo run: `OK [chapter_01]` (20 code cells, unchanged), `OK
  [chapter_02]` (**12** code cells, was 13), `OK [chapter_03]` (**16** code
  cells, was 16 — same count, different cells).

---

## 15. Tests

### Python (`tests/`), `unittest` — 241 → 271

| File | Δ | Contents |
|---|---|---|
| NEW `test_export_knn_abc_data.py` | +13 | committed-artifact shape/split/k=1-endpoints/no-identifier/canonical-serialization; `BuildFromSyntheticFrame` round-trips `build_artifact`/`validate_artifact` on a synthetic frame; tampered-shape and tampered-k1-endpoint rejection. |
| NEW `test_think_first_shared_class.py` | +3 | scans all three canonical notebooks: every "Think first" admonition uses `:class: think-first`; no legacy `:class: note` "Think first" block remains anywhere; the shared CSS class is defined with its own (not `.challenge`/`.how-to-use`-shared) selector block and blue tokens. |
| `test_abide_modeling_data.py` | +2 net (2 removed, 4 added) | see §2.5. |
| `test_exercise_02_notebook.py` | rewritten | 27 tests: FIQ/regularisation absence, 5 (not 6) numbered sections, 360-feature recipe verification against `amd.bundle_columns`, explicit-scaling-precedes-pipeline structural check, IQ-literature-citation absence outside a (now-nonexistent) FIQ section, low-N/double-descent learning-curve assertions, shared blue Think-first class, no student-facing `scripts/`/`WPnn` references. |
| `test_exercise_03_notebook.py` | rewritten | 31 tests: executable-CV-not-hardcoded check, CV reproduces the committed audit's `k=15`, no `invalid_test_fitted_model`/`knn_demo_k1` remain, Section 3 interactive iframe + k=1 endpoint text present, no duplicate reflection block, k-complexity relationship stated prominently, shared blue Think-first class, no student-facing internal references. |
| `test_export_knn_explore_data.py` | +7 net | schema-version-2 check; three-training-samples shape + independent k=n_fit endpoint re-verification per sample; sample A matches baseline; B/C are genuinely different draws; **independent Python re-implementation of the variance-proxy and calibration-slope formulas**, cross-checked against the committed artifact at k∈{1, selected-k, n_fit} (mirrors the exact TypeScript formulas in `interactive/src/knn-explore.ts`, WP14 §7.13). |
| `test_knn_model_audit.py` | ±0 (values only) | `p == 358` → `p == 360` (2 occurrences; comments updated). |
| `test_build_portable_notebook.py`, `test_book_structure.py`, `test_export_regression_catalog.py`, `test_regression_model_audit.py`, `test_notebook_corrections.py`, `test_table_inspection_columns.py`, `test_export_widget_data.py` | ±0 | unchanged; all still green against the extended manifest/generator. |

### Frontend `vitest` — 237 → 262

| File | Δ | Contents |
|---|---|---|
| NEW `knn-abc-data.test.ts` | +10 | schema accept/reject cases (`kMax` mismatch, wrong row/column counts, k=1-endpoint violations for B and C, identifier-shaped key, out-of-range `selectedKFromAudit`) + validates the committed `abide_knn_abc.json`. |
| `knn-explore-data.test.ts` | +5 net | `schemaVersion` literal `1`→`2`; fixture gains `trainingSamples`; new accept/reject cases for a missing sample, a malformed sample row, and `trainingSamples.A` not matching the top-level baseline; committed-artifact assertions extended to check `trainingSamples`. |
| `knn-explore.test.ts` | +9 | `varianceProxy` (zero when identical, matches a hand-computed SD, throws under 2 samples), `calibrationSlope` (1 for a pure shift, 0 for a constant, throws on mismatched/empty input), `ensembleMeanForK` (averages across samples at a fixed k). |
| `config.test.ts` | +11 | new `parseActivityConfig — knn-abc` describe block (valid config, optional `reflectionPrompts`, strict-schema rejection, missing-`k1Note` rejection, accepts the shipped `configs/knn_abc.json`); `validKnnExplore` fixture extended with the four new required fields. |
| all other test files | ±0 | unchanged. |

### Playwright standalone (`interactive/e2e/`) — 74 → 100

- NEW `knn-abc.spec.ts` (16 tests: 8 scenarios × {site root, project
  subpath}) — default k=15 with real per-panel metrics, k=1 makes B/C
  exactly perfect while A is not, moving k recomputes all three panels,
  numeric-input sync + out-of-range rejection, keyboard interaction, the
  k=1 explanatory note, the identity-line legend, narrow-viewport (390 px)
  usability.
- `knn-explore.spec.ts`: +12 tests (×2 bases: numeric-input sync,
  numeric-input out-of-range rejection, training-sample-tab switching
  re-renders the scatter, variance/bias-proxy readouts change with `k`, the
  identity-line legend).
- `regression-compare.spec.ts`: 1 value fixed (`data-feature-count` `"358"`
  → `"360"`, the pre-existing "all eligible" bundle test — a real behaviour
  change from the 360-parcel fix propagating through the shared catalog,
  not a WP14-authored test).
- All other spec files unchanged.

### Playwright built-book (`interactive/e2e-book/`) — 33 → 36

- `chapter03.spec.ts`: +3 tests, a new `describe` block for the embedded
  `knn-abc` iframe on the built Exercise 3 page (config+data 200s and all
  three panels render at the default k; k=1 makes B/C exactly perfect;
  narrow-viewport usability). The existing `knn-explore` iframe `describe`
  block is unchanged (same testids, still passes against the regenerated
  data).
- `chapter02.spec.ts`: 1 value fixed (`data-feature-count` `"358"` →
  `"360"`, same pre-existing test as above, built-book variant).
- `chapter01.spec.ts`, `launch-buttons.spec.ts`, `sidebar-toggle.spec.ts`:
  unchanged.

---

## 16. Commands run (no repository mutation beyond local commits)

```
git add WPs/WP14_EXERCISES_2_AND_3_PEDAGOGICAL_REVISIONS.md
git commit -m "checkpoint: before WP14"                        # 588a4c4
git tag -a wp14-start -m "Checkpoint before WP14 ..."

python scripts/abide_modeling_data.py --check                  # manifest self-consistency after the atlas fix

python scripts/regression_model_audit.py --run                 # network; recomputes with p=360
python scripts/regression_model_audit.py --check
python scripts/export_regression_catalog.py --refresh          # network
python scripts/export_regression_catalog.py --check
python scripts/knn_model_audit.py --run                        # network
python scripts/knn_model_audit.py --check
python scripts/export_knn_explore_data.py --refresh            # network; writes abide_knn_explore.json (schema v2)
python scripts/export_knn_explore_data.py --check
python scripts/export_knn_abc_data.py --refresh                # network; writes abide_knn_abc.json (new)
python scripts/export_knn_abc_data.py --check

python <scratch author_ex02_wp14.py>                            # writes exercise_02.ipynb (scratch authoring script, not committed)
(cd book/chapters/chapter_02 && python -m nbconvert --to notebook --execute --inplace exercise_02.ipynb)
python <scratch author_ex03_wp14.py>                            # writes exercise_03.ipynb (scratch authoring script, not committed)
(cd book/chapters/chapter_03 && python -m nbconvert --to notebook --execute --inplace exercise_03.ipynb)

python -m unittest discover -s tests                            # 271 / 271

(cd interactive && npm run typecheck)
(cd interactive && npm run test:unit)                           # 262 / 262
(cd interactive && npm run build)                                # regenerates book/_static/widgets/app
(cd interactive && npm audit --omit=dev)                        # 0 vulnerabilities
(cd interactive && npx playwright test)                          # 100 / 100

python scripts/build_portable_notebook.py --write --notebook chapter_02
python scripts/build_portable_notebook.py --write --notebook chapter_03
python scripts/build_portable_notebook.py --check --notebook chapter_01
python scripts/build_portable_notebook.py --check --notebook all
python scripts/smoke_portable_notebook.py --notebook all        # network

rm -rf book/_build ; jupyter-book build book                    # 2 warnings (pre-existing), no *.err.log
for i in a b ; do rm -rf book/_build ; jupyter-book build book ; done   # identical 12-PNG hash set
(cd interactive && npm run test:e2e:book)                        # 36 / 36

git add -A -- ':!WPs/reports'
git commit -m "WP14: correct 360-parcel feature recipe; Exercises 2-3 pedagogical revisions"   # d5fbecc
git add WPs/reports/WP14_REPORT.md WPs/reports/WP14_EXACT_CHANGELOG.md
git commit -m "WP14 report: ..."
```

No `git reset --hard`, `git checkout -- <path>`, `git clean`, `git rebase`,
`git revert`, `git push`, `git merge`, `--force`, or `--force-with-lease`. No
repository setting, secret, branch-protection rule, or Pages configuration
changed. No `book/_build`, `book/.jupyter_cache`, `book/_static/widgets/app`,
`interactive/node_modules`, `interactive/test-results`, `__pycache__`, or
Playwright artifact staged. `book/config/abide_modeling.json`,
`book/_static/widgets/data/abide_knn_explore.json`,
`book/_static/widgets/data/abide_knn_abc.json`,
`scripts/regression_model_audit_result.json`, and
`scripts/knn_model_audit_result.json` are committed source/reviewed assets,
not build output.
