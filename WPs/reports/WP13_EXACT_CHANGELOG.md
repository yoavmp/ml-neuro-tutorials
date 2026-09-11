# WP13 — exact change log

Location-specific before/after. Notebook cells are referenced by stable
`nbformat` id. It should be possible to review the substantive work from
this file without diffing raw notebook JSON.

Branch `feature/regression-practice`; checkpoint `863c7df` (tag
`wp13-start`); implementation commit `f327e4c`.

---

## 1. Git objects

| Item | Value |
|---|---|
| Checkpoint commit | `863c7dfaab3bb3352a4d6400294bcfe0334bfd7c` — `checkpoint: before WP13` (adds `WPs/WP13_EXERCISE_3_KNN_AND_BIAS_VARIANCE.md`, 1 file, +353) |
| Annotated tag | `wp13-start` → `863c7df` (tag object `b4c5d2443d50c4b275cf244859800d779f1c8ecd`; name free, no suffix) |
| Implementation commit | `f327e4cb0b8c17de94065a83efb002e2cbb4e653` — `WP13: Exercise 3 - KNN regression and the bias-variance tradeoff` (10 modified, 17 new; 5286 insertions, 7 deletions) |
| Report commit | adds the two report files only |

Tags `wp01-start`…`wp12-start` and all prior branches untouched. No push,
merge, force, rebase, revert, or history rewrite.

---

## 2. NEW `scripts/knn_model_audit.py` (audit source, not build output)

Reproducible KNN model audit, run once (`--run`, network) and re-validated
offline thereafter (`--check`). Public surface:

- `FEATURE_SPACES` — the 3 predeclared feature-space candidates:
  `all-eligible × CT` (Exercise 2 canonical, p=358), `frontoparietal × CT`
  (p=78), `occipital × CT` (p=46).
- `TARGET = "age"`.
- `_outer_split(frame, cols)` — Exercise 2's own locked
  `train_test_split(test_size=0.25, random_state=42, stratify=group)`.
- `_k_grid(k_max)` — a representative, log-spaced set of `k` in `[1,
  k_max]`, always including small-k values and both endpoints.
- `_cv_select_k(X_train, y_train, k_max)` — `KFold(5, shuffle=True,
  random_state=0)` on the training partition only; returns the full per-k
  curve and the selected `k` (argmax mean CV R², ties toward smaller k).
- `_locked_test_eval(...)` — fits the final model once on the full training
  partition, scores the untouched test partition once.
- `_fitting_set_endpoint(...)` — the "k = every participant in the fitting
  set" diagnostic; asserts every test prediction equals the training-partition
  mean.
- `run_audit()` / `validate(results)` / `cmd_check()` — target facts +
  every `(feature_space)` candidate's full CV curve, selected k, locked test
  evaluation, and fitting-set endpoint.

---

## 3. NEW `scripts/knn_model_audit_result.json` (generated, `--run`)

Full audit output for the 3 feature-space candidates — see
`WP13_REPORT.md` §3.2 for the rendered table. SHA-256
`7281a1b446d8fe6874932d82062385ce994b84179787e6db0da8c2c01a7e50ab`.
Byte-identical (apart from `runtime_seconds`) across independent `--run`
invocations in two different Python environments.

---

## 4. `book/config/abide_modeling.json` (reviewed manifest)

```diff
+ "knn": {
+   "target": "age",
+   "canonical_recipe": {"bundle": "all-eligible", "measures": ["CT"],
+                          "note": "same as protocol.canonical_recipe..."},
+   "cv_for_k_selection": {"kind": "KFold", "n_splits": 5, "shuffle": true,
+                            "random_state": 0, ...},
+   "dev_split": {"test_size": 0.25, "random_state": 7, "stratify": "group",
+                  "note": "...N_fit=564, N_val=189..."},
+   "audit_script": "scripts/knn_model_audit.py",
+   "audit_result": "scripts/knn_model_audit_result.json",
+   "selected_k": 15,
+   "selected_k_rationale": "WP13 audit: ... k=15 ... test R2=+0.647 ...",
+   "export_data_script": "scripts/export_knn_explore_data.py",
+   "export_data_artifact": "book/_static/widgets/data/abide_knn_explore.json"
+ }
```

- New top-level `knn` block only — every WP09–WP12 key (`targets`,
  `bundles`, `protocol`, `catalog`, `literature`, `rejected_targets`, ...)
  is **byte-for-byte unchanged**. `scripts/abide_modeling_data.py`'s
  `_check_manifest` does not reference `knn` and needed no change.
- SHA-256 `9933abde1ca621db0808cb7510cf0e011ff1fd501502fed54c407a7cac9fbef5`.

---

## 5. NEW `scripts/export_knn_explore_data.py`

Deterministic export for the interactive `knn-explore` activity. Public
surface:

- `_outer_split(frame, manifest=None)` / `_dev_split(X_train, y_train,
  g_train, manifest=None)` — both manifest-parameterised (unlike an earlier
  draft that read the module-level `MANIFEST` unconditionally; fixed before
  commit so `tests/test_export_knn_explore_data.py`'s synthetic-frame tests
  can exercise a smaller recipe without downloading real data).
- `_sorted_neighbor_targets(X_query, X_ref, y_ref)` — sort distances once,
  return the reference targets reordered nearest-first.
- `_r2_mse_curve(sorted_targets, observed)` — cumulative-mean trick, one
  pass, every k from 1 to `n_fit`.
- `_validate_against_sklearn(...)` — fits real
  `KNeighborsRegressor(k).fit(...).predict(...)` at 7 representative k
  values and asserts `np.allclose` (`atol=1e-6`) before anything is written.
- `build_artifact(frame, manifest=None)` / `validate_artifact(artifact,
  manifest=None)` — builds/validates the full artifact (see §7 below);
  structural checks include: array lengths align with `split.nFit` /
  `nValidation`, `curve.k == [1..n_fit]`, `curve.fitR2[0] ≈ 1.0`,
  `curve.fitR2[-1] ≈ 0.0`, `validationOptimalK` is the true argmax, no
  identifier-shaped top-level key.

---

## 6. NEW `book/_static/widgets/data/abide_knn_explore.json` (generated, `--refresh`)

697,322 bytes. SHA-256
`f13dbf8715368f85ad784e07fd2db8c9b534832db26139b1f70d30f953aacfec`.
Byte-identical across independent `--refresh` runs in two Python
environments. Contents summarised in `WP13_REPORT.md` §8.

`abide_regression_models.json`, `abide_histogram.json`, `abide_retention.json`,
`abide_table_inspection.json`: **untouched**.

---

## 7. NEW `book/_static/widgets/configs/knn_explore.json`

New activity config: `type: "knn-explore"`, `data:
"../data/abide_knn_explore.json"`, `defaultK: "validation-optimal"`,
`curseOfDimensionalityNote` / `endpointNoteK1` / `endpointNoteKMax` (the
activity's own plain-language endpoint text, referenced by the component),
3 `reflectionPrompts`.

---

## 8. `interactive/src/config.ts`

- New `knnExploreConfig` Zod schema (strict object): `instructions`,
  `curseOfDimensionalityNote`, `endpointNoteK1`, `endpointNoteKMax`,
  `defaultK: z.union([z.literal("validation-optimal"),
  z.number().int().positive()])`, optional `reflectionPrompts`.
- `activityConfigSchema` discriminated union extended with
  `knnExploreConfig`; new exported type `KnnExploreConfig`.
- No existing config member changed.

## 9. `interactive/src/components/registry.ts`

- Imports and registers `knnExploreComponent` (type `"knn-explore"`). No
  existing registration changed.

---

## 10. NEW `interactive/src/knn-explore-data.ts`

Zod schema + `parseKnnExploreData` for the artifact in §6. Validates: array
length alignment (`observedValidation`/`observedFitting`/
`neighborTargetsByProximity` rows against `split.nFit`/`nValidation`),
`curve.k` is exactly `[1..n_fit]`, `curve.fitR2[0] ≈ 1`,
`curve.fitR2[last] ≈ 0`, `validationOptimalK`/`selectedKFromAudit` within
`[1, n_fit]`, no identifier-shaped top-level key (same
`IDENTIFIER_TOKEN` pattern as `regression-compare-data.ts`).

## 11. NEW `interactive/src/knn-explore.ts`

Pure helpers, no DOM: `predictForK`, `cumulativeMeans`,
`predictAllForK`. Re-exports `r2Score` / `meanSquaredError` /
`sharedAxisRange` from `./regression-compare` (reused verbatim, not
duplicated — both are already target-agnostic generic metrics).

## 12. NEW `interactive/src/components/knn-explore.ts`

Production activity component. One k slider (`1..n_fit`, `<input
type="range">`, `data-testid="knn-k-slider"`), live-updating `<output>`
value display, a metrics line (`data-testid="knn-metrics"`), an
observed-vs-predicted validation scatter (`data-testid="knn-scatter-plot"`,
recomputed client-side from `neighborTargetsByProximity` via
`predictAllForK`), a fitting/validation MSE-vs-k curve with a marker at the
current k (`data-testid="knn-curve-plot"`, log-scaled k axis), and static
k=1 / k=N_fit endpoint text (`data-testid="knn-endpoint-k1"` /
`"knn-endpoint-kmax"`, sourced from config). `resolveDefaultK` resolves
`config.defaultK` (`"validation-optimal"` or a literal number) against the
loaded data's `validationOptimalK`.

---

## 13. `book/chapters/chapter_03/exercise_03.ipynb` (NEW, 34 cells)

Authored via a scratch nbformat script (not committed) and executed
end-to-end (network) twice, in two Python environments; identical outputs
both times. 14 markdown + 20 code (1 `hide-cell`, 4 `hide-input`, 15
visible). `nbformat.validate` OK.

| id | kind | content |
|---|---|---|
| `wp13-001` | md | `# Exercise 3: KNN and the Bias–Variance Tradeoff` |
| `wp13-002` | md | `:class: how-to-use` run/download admonition, Colab + raw links to `chapter_03/exercise_03_portable.ipynb` |
| `wp13-003` | md | scope: KNN regression + brief classification forward-pointer, 6-item outline, prerequisites, no time budget |
| `wp13-010` | md | `## 1. The modelling table` — reuse-Exercise-2 pointer |
| `wp13-011` | code, `hide-cell` | data loading — same two pinned CSVs, same merge, as Exercise 2's `wp11-011` |
| `wp13-012` | code | compact 3-row preview + `age available for 1004 of 1004` |
| `wp13-020` | md | `## 2. One standard KNN regression workflow` — recipe, split, KNN formula, scaling note, curse-of-dimensionality note, k-selection provenance |
| `wp13-021` | code | `FEATURES` — byte-identical (non-comment lines) to Exercise 2's `wp11-021` |
| `wp13-022` | code | brain-only X/y + locked split, extended to also carry `groups_train`/`groups_test` through (verified not to change the X_train/X_test/y_train/y_test split itself) |
| `wp13-023` | md | Think first: predict KNN vs. OLS |
| `wp13-024` | code | `K_SELECTED = 15`; `Pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=K_SELECTED))`; held-out R²=0.647, MSE=33.0 |
| `wp13-025` | code, `hide-input` | observed-vs-predicted scatter, identity line, equal axes |
| `wp13-026` | md | discussion bullets + "Compared with Exercise 2" lead-in |
| `wp13-027` | code | live OLS refit on the identical split/recipe for comparison (R²=0.475) |
| `wp13-028` | md | explicit non-universal-comparison caveat |
| `wp13-030` | md | `## 3. Honest evaluation versus invalid alternatives` — A/B/C table, Think first |
| `wp13-031` | code | A/B/C at k=15: `invalid_test_fitted_model` (assigned once, isolated to this cell) |
| `wp13-032` | code, `hide-input` | 3-panel A/B/C scatter |
| `wp13-033` | md | discussion (gap is small at k=15) + "sharper illustration" lead-in for k=1 |
| `wp13-034` | code | k=1 demonstration: `invalid_test_fitted_model_k1` (assigned once, isolated to this cell); A=0.553, B=1.000, C=1.000 |
| `wp13-035` | md | k=1 discussion; explicit non-reuse note |
| `wp13-040` | md | `## 4. The classic bias–variance tradeoff` — decomposition equation, small/large-k bullets |
| `wp13-041` | code, `hide-input` | conceptual bias/variance/irreducible/expected-test-error figure, title contains "CONCEPTUAL, not estimated from ABIDE data" |
| `wp13-050` | md | `## 5. From k = 1 to every participant: an empirical curve` — fit/validation split description |
| `wp13-051` | code | `X_fit, X_val, y_fit, y_val` split (`test_size=0.25, random_state=7, stratify=groups_train`); N_fit=564, N_val=189 |
| `wp13-052` | code | sort-once + cumulative-sum curve for every k=1..564; prints k=1 / validation-optimal (k=17) / k=N_fit rows |
| `wp13-053` | code | explicit `assert np.allclose(pred_val_at_k_nfit, y_fit.mean())`; prints the fitting-set mean, 15.192 years |
| `wp13-054` | code, `hide-input` | two-panel figure: fitting/validation MSE vs k (log x-axis, k=1/optimal/N_fit markers) + validation R² vs k |
| `wp13-055` | md | "What this curve shows -- and does not" admonition; states the curve is consistent with, not a direct measurement of, bias/variance; states it never retunes the Section 2 model |
| `wp13-060` | md | `## 6. Explore k yourself` — intro |
| `wp13-061` | md | `<iframe title="Interactive KNN neighbour-count exploration for predicting age from brain structure" src="../../_static/widgets/app/index.html?config=../configs/knn_explore.json" ...>` |
| `wp13-062` | md | 3 Think-first prompts |
| `wp13-070` | md | `## In summary` — 5 bullets + classification forward-pointer (2nd and last mention) |
| `wp13-071` | md | `### Questions to take away` — 7 questions |

SHA-256 `7ae116f3470d7f4ee21b63035cefde32c8a48db049cf6070cd99ec31e1aa8b8a`.

---

## 14. `scripts/build_portable_notebook.py`

- **Added** `PUBLISHED_PAGE_CH3`, `_CH3_BANNER`, `_CH3_SETUP`,
  `_CH3_IFRAME_REPLACEMENT` (points at "Section 5 above" — the notebook's
  own from-scratch matplotlib k exploration — rather than a nonexistent
  extra cell), and a new `CHAPTER_03 = NotebookSpec(...)` with
  `colab_title="Exercise 3: KNN and the Bias-Variance Tradeoff"`.
- `NOTEBOOKS` dict extended: `{CHAPTER_01, CHAPTER_02, CHAPTER_03}`.
- `CHAPTER_01`/`CHAPTER_02` specs, banners, and behaviour: **byte-for-byte
  unchanged**.

**`book/downloads/chapter_01/exercise_01_portable.ipynb`** and
**`book/downloads/chapter_02/exercise_02_portable.ipynb`** verified
byte-identical to before WP13 (`--check` → "up to date"; not present in
this commit's diff).

## 15. `book/downloads/chapter_03/exercise_03_portable.ipynb` (generated, `--write`)

36 cells (34 canonical + banner/setup/install − 1 dropped "Run or download"
admonition). `metadata.colab.name = "Exercise 3: KNN and the Bias-Variance
Tradeoff"`. No MyST/iframe/hide-tag/repo-path/active-install-command. SHA-256
`1819c36faf4dbb367cd774d134ebac350a5c11d83373221299221aa5a80b23ab`.

## 16. `scripts/smoke_portable_notebook.py`

- `SMOKE["chapter_03"]` added: expects `"age available for 1004 of 1004"`,
  `"k = 15"`, `"held-out R^2 = 0.647"`, `"N_fit = 564   N_val = 189"`, the
  k=N_fit endpoint sentence. `chapter_01`/`chapter_02` entries unchanged.
  Out-of-repo run: `OK [chapter_01]` (20), `OK [chapter_02]` (13),
  `OK [chapter_03]` (**16** code cells, new).

---

## 17. `book/_toc.yml`

```diff
       - file: chapters/chapter_01/exercise_01
       - file: chapters/chapter_02/exercise_02
+      - file: chapters/chapter_03/exercise_03
```

## 18. `book/_static/launch-buttons.js`

```diff
   var PAGE_TO_PORTABLE = {
     "chapters/chapter_01/exercise_01.html":
       "book/downloads/chapter_01/exercise_01_portable.ipynb",
     "chapters/chapter_02/exercise_02.html":
       "book/downloads/chapter_02/exercise_02_portable.ipynb",
+    "chapters/chapter_03/exercise_03.html":
+      "book/downloads/chapter_03/exercise_03_portable.ipynb",
   };
```

No other change to the file (Chapters 1–2 behaviour unchanged).

---

## 19. Tests

### Python (`tests/`), `unittest` — 184 → 241

| File | Δ | Contents |
|---|---|---|
| NEW `test_knn_model_audit.py` | +16 | committed-result self-consistency, source pins, all 3 feature spaces present, canonical recipe beats both smaller bundles and beats Exercise 2's OLS, k-grid spans `[1, k_max]`, selected-k is the argmax of the CV curve, fitting-set endpoint predicts a constant, runtime recorded; **mocks `KNeighborsRegressor.fit`** to prove CV-fold isolation and locked-test single-fit isolation; determinism across repeated runs. |
| NEW `test_export_knn_explore_data.py` | +15 | committed-artifact shape/split/endpoints, no participant identifier, serialization canonical; `BuildFromSyntheticFrame` round-trips `build_artifact`/`validate_artifact` on a synthetic frame (frontoparietal recipe substituted for the unavailable all-eligible one), confirms the k=n_fit constant-prediction property structurally, and confirms tampered curves/endpoints are rejected. |
| NEW `test_exercise_03_notebook.py` | +26 | H1, run-or-download block, opening scope/prerequisites/no-time-budget, cell count, tags, 6 numbered sections in order, classification-mentioned-only-forward, k-vs-n terminology, canonical recipe byte-matches Exercise 2's own cell, locked split matches Exercise 2, leakage guard, standard pipeline matches the audit-selected k, scaling always inside the pipeline, invalid-model isolation (regex word-boundary check, fixed after an initial substring false-positive against `invalid_test_fitted_model_k1`), k=1 demonstration values, A/B/C values, conceptual-graph labelling, bias-variance equation present, dev-split independence from the outer test set, N_fit endpoint verified in code, curve-never-retunes wording, no-direct-measurement wording, iframe target, executed-output values, no stderr/errors. |
| `test_book_structure.py` | ±0 (1 test renamed/extended) | `test_exercise_two_follows_exercise_one` → `test_exercises_two_and_three_follow_exercise_one_in_order`: TOC now asserted as `[chapter_01, chapter_02, chapter_03]`. |
| `test_abide_modeling_data.py`, `test_regression_model_audit.py`, `test_export_regression_catalog.py`, `test_exercise_02_notebook.py`, `test_build_portable_notebook.py`, `test_export_widget_data.py`, `test_notebook_corrections.py`, `test_table_inspection_columns.py` | ±0 | unchanged; all still green against the extended `abide_modeling.json` and `build_portable_notebook.py`. |

### Frontend `vitest` — 217 → 237

| File | Δ | Contents |
|---|---|---|
| NEW `knn-explore-data.test.ts` | +9 | schema accept/reject cases (misaligned arrays, bad `curve.k`, endpoint violations, identifier-shaped key) + validates the committed `abide_knn_explore.json` artifact. |
| NEW `knn-explore.test.ts` | +5 | `predictForK`, `cumulativeMeans`, `predictAllForK` pure-function tests. |
| `config.test.ts` | +6 | new `parseActivityConfig — knn-explore` describe block: valid config, numeric `defaultK`, unknown `defaultK` string rejected, non-positive numeric `defaultK` rejected, strict-schema extra-key rejection, accepts the shipped `configs/knn_explore.json`. |
| all other test files | ±0 | unchanged. |

### Playwright standalone (`interactive/e2e/`) — 60 → 74

NEW `knn-explore.spec.ts` (14 tests: 7 scenarios × {site root, project
subpath}) — default k=17 with real metrics and both plots rendered, moving k
recomputes metrics/plots (not just a label), k=N_fit collapses the scatter
to the fitting-set mean, keyboard (arrow-key) interaction, endpoint text
present, refresh restores the default, narrow-viewport (390 px) usability
with no horizontal overflow. All other spec files unchanged.

### Playwright built-book (`interactive/e2e-book/`) — 26 → 33

- NEW `chapter03.spec.ts` (4 tests): iframe + config/data 200s + both plots
  render + a real k change, k=N_fit collapse, refresh-restores-default,
  narrow-viewport usability — all against the actual built Chapter 3 HTML
  page beneath the simulated GitHub Pages subpath.
- `launch-buttons.spec.ts`: `CHAPTERS` array extended with a Chapter 3 entry
  (+3 tests via the existing per-chapter loop: opening-admonition links,
  header Colab button, theme download-`.ipynb` control present); the
  no-mapping-page test (Introduction) unchanged.
- `chapter01.spec.ts`, `chapter02.spec.ts`, `sidebar-toggle.spec.ts`:
  unchanged.

---

## 20. Commands run (no repository mutation beyond local commits)

```
git add WPs/WP13_EXERCISE_3_KNN_AND_BIAS_VARIANCE.md
git commit -m "checkpoint: before WP13"                       # 863c7df
git tag -a wp13-start -m "Checkpoint before WP13 ..."
# baseline (before): python -m unittest discover -s tests ;
#   (cd interactive && npm test && npx playwright test && npm run test:e2e:book) ;
#   npm audit --omit=dev ; jupyter-book build book             # matched WP12's own "after" numbers

python scripts/knn_model_audit.py --run                        # KNN audit (network)
python scripts/knn_model_audit.py --check
python scripts/export_knn_explore_data.py --refresh            # writes abide_knn_explore.json (network)
python scripts/export_knn_explore_data.py --check
python <scratch author_ex3_wp13.py>                            # writes exercise_03.ipynb (scratch authoring script, not committed)
(cd book/chapters/chapter_03 && python -m nbconvert --to notebook --execute --inplace exercise_03.ipynb)
python scripts/build_portable_notebook.py --write --notebook chapter_03
python scripts/build_portable_notebook.py --check --notebook chapter_01
python scripts/build_portable_notebook.py --check --notebook chapter_02
python scripts/smoke_portable_notebook.py --notebook all       # network
(cd interactive && npm run build)                               # regenerates book/_static/widgets/app
python -m unittest discover -s tests                            # 241 / 241
(cd interactive && npm run typecheck && npm run test:unit && npx playwright test && npm run test:e2e:book)
npm audit --omit=dev                                            # 0 vulnerabilities
rm -rf book/_build ; jupyter-book build book                    # 2 warnings, no *.err.log
for i in a b ; do rm -rf book/_build ; jupyter-book build book ; done   # identical 13-PNG hash set
git add -A -- ':!WPs/reports'
git commit -m "WP13: Exercise 3 - KNN regression and the bias-variance tradeoff"   # f327e4c
git add WPs/reports/WP13_REPORT.md WPs/reports/WP13_EXACT_CHANGELOG.md
git commit -m "WP13 report: document Exercise 3 KNN and bias-variance tradeoff"
```

No `git reset --hard`, `git checkout -- <path>`, `git clean`, `git rebase`,
`git revert`, `git push`, `git merge`, `--force`, or `--force-with-lease`. No
repository setting, secret, branch-protection rule, or Pages configuration
changed. No `book/_build`, `book/.jupyter_cache`, `book/_static/widgets/app`,
`interactive/node_modules`, `interactive/test-results`, `__pycache__`, or
Playwright artifact staged. `book/config/abide_modeling.json`,
`book/_static/widgets/data/abide_knn_explore.json`, and
`scripts/knn_model_audit_result.json` are committed source/reviewed assets,
not build output.
