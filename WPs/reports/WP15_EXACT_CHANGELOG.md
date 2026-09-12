# WP15 — exact change log

Location-specific before/after. Branch `feature/regression-practice`;
checkpoint `3b7cf5c` (tag `wp15-start`); implementation commit `2584522`;
merge commit `6288136`.

---

## 1. Git objects

| Item | Value |
|---|---|
| Checkpoint commit | `3b7cf5c` — `checkpoint: before WP15` (adds `WPs/WP15_SAMPLE_SIZE_COMPACT_ASSETS_AND_PRODUCTION_DEPLOYMENT.md`, 1 file, +403) |
| Annotated tag | `wp15-start` → `3b7cf5c` (name free, no suffix) |
| Implementation commit | `2584522` — `WP15: compact sample-size subset for Exercise 2; binary KNN asset format` (33 files changed, 3572 insertions, 1093 deletions) |
| Merge commit | `6288136` — `Merge feature/regression-practice into main (WP09-WP15)` (`--no-ff`, fast-forward-clean, zero conflicts; local `main` and `origin/main` were identical at `6d8c1f6` before the merge) |
| Pushed to `origin/main` | `6d8c1f6..6288136` |
| First deploy workflow run | `34692844653` (`Build and deploy Jupyter Book`), conclusion `success`, `headSha=6288136` |
| `gh-pages` deploy commit | `f8be61e` — `deploy: 6288136acf24f9c3009aa7de9555814313f6aa25` |
| Report commit | adds the two WP15 report files only — SHA recorded in the terminal summary |

No `git reset --hard`, `git checkout -- <path>`, `git clean`, `git rebase`,
`git revert`, `--force`, or `--force-with-lease` at any point. `main` and
`feature/regression-practice` had zero divergence before the merge (`origin/main`
0 commits ahead of the feature branch; feature branch 20 commits ahead of
`origin/main`), so the merge was conflict-free.

---

## 2. Exercise 2 Section 5 sample-size audit (WP15 §2)

### 2.1 NEW `scripts/sample_size_audit.py`

Predeclared, training-only audit choosing a compact (≤12-column) cortical-
thickness bundle for the isolated sample-size demonstration, decoupled from
the whole-cortex `p=360` recipe's own near-`n=p` double-descent instability
(unchanged, documented in `scripts/regression_model_audit_result.json` /
`WPs/reports/WP14_REPORT.md`, and still shown by Sections 1–4's main worked
example on the full 360-feature recipe).

**Candidates predeclared** (source-of-preference order: no existing manifest
bundle has ≤12 columns, so every candidate is source 2 — a small documented
bilateral literature bundle — except the last, source 3, a deterministic
atlas-order rule):

| Candidate | ROIs | p | Rationale | Source pref. |
|---|---|---:|---|---:|
| `sensorimotor_core` | `4, 3a, 3b, 1, 2` | 10 | Primary motor (BA4) + primary somatosensory (BA 3a/3b/1/2) — the classic sensorimotor strip (Penfield & Rasmussen 1950; HCP-MMP1 areas 4/3a/3b/1/2) | 2 |
| `early_visual` | `V1, V2, V3, V4` | 8 | Early visual hierarchy (Felleman & Van Essen 1991) | 2 |
| `auditory_core_belt` | `A1, LBelt, MBelt, PBelt` | 8 | Primary auditory core + belt (Kaas & Hackett 2000) | 2 |
| `atlas_order_every_30th` | `1, 5m, EC, OFC, ProS, V4t` | 12 | Every 30th canonical ROI id in atlas order (indices 0,30,60,90,120,150), no reference to identity/age/performance | 3 |

**Protocol**: candidates are scored ONLY against a fixed inner-validation
partition (189 rows) carved from the outer-TRAINING partition (753 rows) via
a dev split identical in parameters to `knn.dev_split` (`test_size=0.25,
random_state=7, stratify=group`) — the outer locked test set (251 rows,
`protocol.holdout_split`) is never loaded as a scoring target anywhere in the
audit (`tests/test_sample_size_audit.py::CommittedResult::
test_outer_test_set_was_never_loaded_as_a_scoring_target`). Predeclared sizes
`[40, 60, 90, 130, 200, 300, 564]`, 40 repeated subsamples per size, 3 audit
seeds per size (0,1,2) to check seed-robustness before locking.

**Decision-rule thresholds** (fixed in code before any candidate was scored):
smallest size ≥3× p; median R² gain from smallest to largest size ≥0.05;
no single-step drop >0.02; instability (90th–10th pctile spread) at the
largest size ≤35% of its value at the smallest size; max disagreement across
the 3 seeds' medians ≤0.15; final median R² ≥0.15.

**Result**: all four candidates passed every check. Full per-candidate table
(training-only, `mean_r2_mean_over_seeds`):

| Candidate | n=40 | n=60 | n=90 | n=130 | n=200 | n=300 | n=564 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `sensorimotor_core` | +0.039 | +0.149 | +0.222 | +0.260 | +0.292 | +0.308 | +0.321 |
| `early_visual` | +0.083 | +0.146 | +0.228 | +0.246 | +0.265 | +0.276 | +0.285 |
| `auditory_core_belt` | +0.151 | +0.243 | +0.292 | +0.316 | +0.336 | +0.353 | +0.364 |
| `atlas_order_every_30th` | +0.104 | +0.254 | +0.335 | +0.374 | +0.402 | +0.423 | +0.434 |

**Selection**: `sensorimotor_core` — the first passing candidate in
declaration/source-preference order (source-2 bundles are preferred over the
source-3 deterministic rule; ties within source 2 broken by declaration
order, never by which candidate scored highest — the selection code
explicitly sorts by `(source_preference, declaration_index)`, not by any
R² value). Full committed audit: `scripts/sample_size_audit_result.json`
(17,188 bytes on `--run`, re-verified byte-for-byte self-consistent by
`--check`).

### 2.2 `book/config/abide_modeling.json`

- New `bundles.sensorimotor_core` (label, literature note, 5 ROIs) — a
  reviewed, minimal subset of the existing `bundles.sensorimotor` (20 ROIs),
  used only by the new `protocol.sample_size_demo` block, never by
  `protocol.canonical_recipe` or `catalog`.
- New `protocol.sample_size_demo` block: purpose, `selected_bundle:
  "sensorimotor_core"`, measures, predeclared sizes, audit script/result
  pointers, and a note summarising the selection process (candidates
  considered, decision rule, why `sensorimotor_core` was picked over the
  other three passing candidates).
- `knn.export_data_artifact` updated from the single old JSON path to the
  manifest + binary pair (§4 below).
- SHA-256 `b36039a5…` (full digest in §7 below).

### 2.3 `book/chapters/chapter_02/exercise_02.ipynb` Section 5 (rewritten)

| Cell | Change |
|---|---|
| `wp11-050` | Rewritten: explains the small, fixed `sensorimotor_core` subset (10 columns) used only for this section, why (isolate sample size from the 360-feature recipe's own near-n=p instability), how it was chosen (predeclared, training-only audit, never the locked test set), and the new predeclared sizes. |
| `wp11-058` | Rewritten: builds `SAMPLE_SIZE_ROIS`/`FEATURES_SS` (10 columns, both hemispheres), re-splits with the SAME `random_state=42` stratified split as Section 2 (asserted `np.array_equal(y_train_ss, y_train)`), then the resample sweep at `sizes = [40, 60, 90, 130, 200, 300, len(y_train_ss)]`, printing median ± 10th/90th-percentile R²/MSE per size — no more `UNDERDETERMINED` flag (no size ever approaches `p=10`). |
| `wp11-059` | Rewritten: same two-panel MSE/R² figure, without the `n_train = p` vertical marker (not relevant at this scale) and title now says "sensorimotor cortical thickness, p = 10". |
| `wp11-05a` | Rewritten: explains the clean upward trend + narrowing spread, explicitly notes this is not a per-draw guarantee, and explicitly contrasts with Section 2's separate, unchanged, whole-cortex behaviour rather than re-deriving the double-descent explanation here. |
| `wp11-060` | "In summary" sample-size bullet rewritten for the new finding (no more `n_train <= p` / double-descent bullet). |
| `wp11-061` | Questions 6–7 rewritten to match the new curve (no longer "where is the worst point", now "name evidence the trend is real"; sizes in Q7 updated from 550/753/50-100 to 300/753/40). |

Sections 1–4 (the 360-feature recipe, the honest/training/invalid
three-way comparison, and the feature-set-comparison activity) are
byte-for-byte untouched except cell ids already listed above.

Re-executed end-to-end via `nbconvert --execute --inplace`; zero errors,
zero stderr (`tests/test_exercise_02_notebook.py::
test_no_execution_errors_or_stderr_committed`). SHA-256 `244b85eb…`.

**Executed Section 5 output** (final numbers used in the notebook and this
report):

| n_train | n/p | median held-out R² | 10–90 pct | median MSE |
|---:|---:|---:|---|---:|
| 40 | 4.00 | +0.188 | [−0.040, +0.300] | 75.8 |
| 60 | 6.00 | +0.265 | [+0.156, +0.348] | 68.6 |
| 90 | 9.00 | +0.356 | [+0.244, +0.395] | 60.1 |
| 130 | 13.00 | +0.370 | [+0.317, +0.405] | 58.8 |
| 200 | 20.00 | +0.373 | [+0.349, +0.402] | 58.5 |
| 300 | 30.00 | +0.395 | [+0.363, +0.413] | 56.5 |
| 753 (full) | 75.30 | +0.407 | [+0.407, +0.407] | 55.4 |

(This is the real outer test partition, consulted only AFTER the candidate
was already locked by the training-only audit above — the training-only
numbers for `sensorimotor_core` in §2.1 and these outer-test numbers agree in
shape: clean upward trend, narrowing spread, no collapse.)

### 2.4 `book/downloads/chapter_02/exercise_02_portable.ipynb`

Regenerated via `scripts/build_portable_notebook.py --write --notebook
chapter_02`; cell count unchanged at 31 (no structural cell added/removed,
only Section 5's existing cells' content changed). SHA-256 `def3a276…`.

### 2.5 `scripts/smoke_portable_notebook.py`

`SMOKE["chapter_02"].expect`: `"n_features (p) = 360"` (the OLD Section-5
line, no longer printed) replaced with `"n_features = 360"` (Section 2's own
line, unchanged) + `"n_features (p) = 10"` (the new Section-5 line).

### 2.6 Tests

- `tests/test_sample_size_audit.py` (NEW, 15 tests): committed-audit
  self-consistency, every candidate ≤12 real bilateral `fsCT_` columns, the
  outer test set structurally never loaded, the decision rule is a pure,
  independently-re-derivable function of each candidate's stored rows, and
  `sensorimotor_core` is the actual recorded selection.
- `tests/test_exercise_02_notebook.py`: replaced
  `test_learning_curve_starts_at_low_n_and_spans_underdetermined_region` with
  5 new tests (`test_sample_size_section_uses_a_small_predeclared_subset_
  not_the_360_recipe`, `test_sample_size_subset_reuses_the_same_participant_
  split_as_section_2`, `test_no_stale_double_descent_or_underdetermined_
  claims`, `test_sample_size_curve_shows_a_clear_upward_trend_with_
  narrowing_spread`, plus the existing `test_executed_outputs_are_present_
  and_teach_the_point` updated for the new `"n_features (p) = 10"` string).

---

## 3. Compact binary interactive-data format (WP15 §3)

### 3.1 NEW `scripts/binary_asset.py`

Shared deterministic binary-payload packer/decoder: `BinaryAssetBuilder.add(
name, dtype, array)` (dtype `float32` or `uint16`, values cast little-endian,
4-byte-aligned between sections; `uint16` sections assert every value is in
`[0, 65535]`); `.build()` returns the concatenated blob + a `sections` dict
(dtype/shape/byteOffset/byteLength per section); `decode_section(blob,
section)` is the read-back mirror, used by both export scripts' own
validators to reconstruct the OLD schema's logical nested arrays from the
NEW binary + manifest, so every existing semantic check (shapes, k=1/k=N_fit
endpoints, sklearn agreement, no-identifier scan) still runs against the
same logical values as before, sourced differently.

`tests/test_binary_asset.py` (NEW, 9 tests): round-trip, alignment,
uint16-overflow/negative rejection, duplicate/unsupported-dtype rejection,
explicit little-endian byte order, 2-D shape preservation, determinism
across repeated builds.

### 3.2 NEW `interactive/src/binary-asset.ts`

Shared TypeScript loader/decoder, the browser mirror of §3.1:
`binaryManifestBaseSchema` (zod: `schemaVersion`, `activity`, `binary.{path,
byteLength,sha256}`, `sections` record) + `loadBinaryAsset(manifestJson,
manifestSchema, manifestUrl)`. Validates, in order: manifest schema; no
identifier-shaped top-level manifest key or section name; binary path safety
via the EXISTING `resolveDataUrl` (same-origin, http/https only, reused
rather than reimplemented) resolved against the manifest's own URL; fetches
the binary via `fetch(...).arrayBuffer()`, caching in-flight/resolved
fetches by URL (`_clearBufferCacheForTests` for tests only) so one page never
fetches the same binary twice; byte-length match; SHA-256 digest match via
`crypto.subtle.digest` when available (secure-context browsers — every
target here, since GitHub Pages is HTTPS and local dev is a secure-context
`localhost`), else a console-free skip (§3.4 below); per-section bounds/
alignment/shape validation; little-endian typed-array decode with an
explicit `DataView`-based fallback for the (today, nonexistent) big-endian
case. Returns a clear, student-friendly error string on any failure rather
than throwing.

`interactive/tests/binary-asset.test.ts` (NEW, 15 tests) +
`interactive/tests/binary-fixture.ts` (NEW, shared test helper: packs typed
sections into a blob the same way the Python encoder does, mocks `fetch` to
serve it).

### 3.3 `interactive/src/components/types.ts` / `main.ts`

- `WidgetComponent.parseData` signature widened: `(raw: unknown, dataUrl:
  URL) => DataResult<TData> | Promise<DataResult<TData>>` — `dataUrl` is the
  already-resolved, same-origin data URL, so a binary-backed activity's
  parser can resolve its sibling `.bin` file against it. Existing
  synchronous, single-argument component implementations remain valid
  (TypeScript function-type assignability allows fewer parameters and a
  non-`Promise` return); none of the other 6 component files needed any
  change.
- `main.ts`: `component.parseData(dataJson)` → `await
  component.parseData(dataJson, dataUrlResult.url)`. One line.

### 3.4 `scripts/export_knn_explore_data.py` (schema v2 → v3)

Same computation as before (`_sorted_neighbor_index` now returns row
INDICES via `np.argsort`, not reordered target values), same validation
(`_validate_against_sklearn`, structural k=1/k=n_fit endpoints), plus a NEW
`_verify_float32_precision` step: reconstructs the curve from the
float32(targets) + uint16(index) round-trip and asserts it matches the
float64 computation within `2×10⁻⁴` (documented as double-rounding headroom,
not a hidden precision loss — both sides are independently rounded to the
same 4-decimal display precision the old schema used) BEFORE anything is
written; passed on the real data with a comfortable margin (this is a
production/export-time check, not a per-load runtime cost — WP15 §3.3's
"if production digest verification has a material cost, enforce it at
export/build" applies the same reasoning here to float precision).

Binary sections written: `observedValidation` (f32×189), `observedFitting`
(f32×564, also A's own reference pool), `fitTargetsB`/`fitTargetsC`
(f32×564 each, B/C's own bootstrap-resampled pools), `neighborIndexA/B/C`
(u16×189×564 each), `curveFitR2/FitMSE/ValR2/ValMSE` (f32×564 each). No
separate "baseline" storage for A — its index matrix IS the top-level
baseline matrix (schema v2's `trainingSamples.A == top-level` duplicate is
structurally impossible in v3, not merely de-duplicated after the fact).

Output: `book/_static/widgets/data/abide_knn_explore_manifest.json` (2,212
bytes) + `abide_knn_explore.bin` (656,124 bytes). Old
`abide_knn_explore.json` (2,719,089 bytes) deleted.

### 3.5 `scripts/export_knn_abc_data.py` (schema v1 → v2)

Same three panels (A valid, B resubstitution, C invalid-leakage), same
`_validate_panel_against_sklearn`/k=1 structural checks, plus the same
`_verify_float32_precision` proof. Panels A and B share one reference pool
(`observedTrain`, the 753 training targets) — only their query sets differ —
so it is stored once; panel C's pool is `observedTest` (251).

Binary sections: `observedTrain` (f32×753), `observedTest` (f32×251),
`neighborIndexA` (u16×251×251, into `observedTrain`), `neighborIndexB`
(u16×753×251, into `observedTrain`), `neighborIndexC` (u16×251×251, into
`observedTest`).

Output: `book/_static/widgets/data/abide_knn_abc_manifest.json` (1,162
bytes) + `abide_knn_abc.bin` (634,032 bytes). Old `abide_knn_abc.json`
(1,850,283 bytes) deleted.

### 3.6 `interactive/src/knn-explore-data.ts` / `knn-abc-data.ts` (rewritten)

Both keep their EXACT prior exported logical TypeScript interface
(`KnnExploreData`/`KnnAbcData`, same field names/shapes/semantics) so the
downstream rendering components (`components/knn-explore.ts`,
`components/knn-abc.ts`) needed **zero** changes — only the two `*-data.ts`
modules' data SOURCE changed. `parseKnnExploreData`/`parseKnnAbcData` are now
`async (raw, dataUrl) => Promise<DataResult<...>>`: call the shared
`loadBinaryAsset`, reconstruct every logical nested array via one indexed
lookup pass (`toRows`, bounds-checked — an out-of-range index throws a clear,
localised error rather than silently reading `undefined`), then re-run the
same structural/endpoint validations the old schema's zod `superRefine` used
to run inline.

### 3.7 Config JSON

`book/_static/widgets/configs/knn_explore.json` / `knn_abc.json`: `"data"`
field repointed from the old single JSON path to the new `*_manifest.json`
path. No other field changed (verified via `git diff`, a 1-line diff per
file).

### 3.8 `book/config/abide_modeling.json`

`knn.export_data_artifact`: updated from the single old JSON path to
`"book/_static/widgets/data/abide_knn_explore_manifest.json +
book/_static/widgets/data/abide_knn_explore.bin"`.

### 3.9 Size budget (WP15 §3.5)

| Asset | Before (schema v1/v2, WP14) | After (schema v2/v3, WP15) |
|---|---:|---:|
| KNN explore (manifest+binary vs. old single JSON) | 2,719,089 B | 2,212 + 656,124 = 658,336 B |
| KNN A/B/C (manifest+binary vs. old single JSON) | 1,850,283 B | 1,162 + 634,032 = 635,194 B |
| **Combined total** | **4,569,372 B** | **1,293,530 B** |
| **Reduction** | — | **−71.69%** (target: ≥50%) |

Every individual committed runtime-data object is under the 1,000,000-byte
budget (largest is `abide_knn_explore.bin` at 656,124 bytes). Confirmed
absent from the final built tree: `find book/_build/html/_static/widgets/data
-iname 'abide_knn_*.json'` → empty (only the two `*_manifest.json` files, not
the old flat-array names, exist there).

### 3.10 Tests (Python + TypeScript)

- `tests/test_export_knn_explore_data.py` (rewritten for schema v3, 25
  tests): committed manifest+binary self-consistency, size-budget assertion,
  no-obsolete-JSON assertion, structural endpoints via
  `_reconstruct_logical`, synthetic-frame build/validate round trip,
  tampered-shape/endpoint/digest/out-of-range-index rejection.
- `tests/test_export_knn_abc_data.py` (rewritten for schema v2, 18 tests):
  same pattern.
- `interactive/tests/knn-explore-data.test.ts` (rewritten, 11 tests) /
  `knn-abc-data.test.ts` (rewritten, 10 tests): hand-built manifest+binary
  fixtures (via the new shared `tests/binary-fixture.ts`), reconstruction
  correctness, identifier-key rejection, digest/byte-length mismatch
  rejection, out-of-range-index rejection, and validation of the real
  committed manifest+binary pair (mocking only the network `fetch`, reading
  the actual files from disk).
- `interactive/tests/config.test.ts`: `data` field fixtures updated to the
  new manifest filenames (schema-shape test only, not file-existence
  dependent — passed unchanged either way, updated for clarity).
- `interactive/e2e-book/chapter03.spec.ts`: both `describe` blocks now check
  for `configResp`/`manifestResp`/`binaryResp` all HTTP 200 AND assert no
  request for the old `abide_knn_explore.json`/`abide_knn_abc.json` path
  occurred at all.

---

## 4. Commands run (chronological, abbreviated — see WP15_REPORT.md §11 for
the full gate)

```
git add WPs/WP15_SAMPLE_SIZE_COMPACT_ASSETS_AND_PRODUCTION_DEPLOYMENT.md
git commit -m "checkpoint: before WP15"                        # 3b7cf5c
git tag -a wp15-start -m "WP15 start checkpoint"

python scripts/sample_size_audit.py --run                      # network
python scripts/sample_size_audit.py --check

# Exercise 2 Section 5 rewritten via a scratch nbformat script (not committed)
(cd book/chapters/chapter_02 && python -m nbconvert --to notebook --execute --inplace exercise_02.ipynb)
python scripts/build_portable_notebook.py --write --notebook chapter_02

python scripts/export_knn_explore_data.py --refresh             # network
python scripts/export_knn_explore_data.py --check
python scripts/export_knn_abc_data.py --refresh                 # network
python scripts/export_knn_abc_data.py --check

python -m unittest discover -s tests                            # 308 / 308
(cd interactive && npm run typecheck)
(cd interactive && npm run test:unit)                           # 276 / 276
(cd interactive && npm audit --omit=dev)                        # 0 vulnerabilities
(cd interactive && npm run build)
(cd interactive && npx playwright test)                         # 100 / 100
python scripts/build_portable_notebook.py --check --notebook all
python scripts/smoke_portable_notebook.py --notebook all        # network

rm -rf book/_build ; jupyter-book build book                    # 2 pre-existing warnings, no *.err.log
(cd interactive && npm run test:e2e:book)                       # 36 / 36
for i in a b ; do rm -rf book/_build ; jupyter-book build book ; done  # identical 12-PNG SHA-256 set

git add -A -- ':!WPs/reports'
git commit -m "WP15: compact sample-size subset for Exercise 2; binary KNN asset format"  # 2584522

git checkout main
git pull --ff-only origin main                                  # already up to date
git merge --no-ff feature/regression-practice                   # 6288136, zero conflicts
# post-merge smoke: python unittest, artifact --check x7, frontend build, jupyter-book build, representative e2e-book
git push origin main                                             # 6d8c1f6..6288136

gh run watch 34692844653 --exit-status                          # success

# live acceptance (production baseURL, e2e-book specs reused with a
# temporary local-only Playwright config, removed after use)
curl -o /dev/null -w '%{http_code}' <13 URLs>                    # 200 x11, 404 x2 (obsolete JSON, expected)
npx playwright test --config <temp prod config> e2e-book/*.spec.ts  # 36 / 36 against production
```

No `git reset --hard`, `git checkout -- <path>`, `git clean`, `git rebase`,
`git revert`, force-push, or tag/branch deletion at any point. No
`book/_build`, `book/.jupyter_cache`, `book/_static/widgets/app`,
`interactive/node_modules`, `interactive/test-results`, `__pycache__`, or
Playwright artifact staged.
