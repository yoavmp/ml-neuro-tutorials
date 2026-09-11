# WP14 implementation report — Exercises 2–3 pedagogical revisions and the 360-parcel correction

## Outcome

Status: **SUCCESS**

The mandatory pre-rewrite audit (WP14 §1) confirmed that the current 358-feature
canonical recipe undercounts the real data: the raw, hash-verified `abide2.tsv`
contains exactly **360** genuine cortical-thickness columns per hemisphere pair
(180 canonical HCP-MMP1 parcels × 2 hemispheres), for all four measurement
families. The two previously excluded columns (`fsCT_L_5L_ROI` and
`fsCT_R_5R_ROI`, and their `fsArea`/`fsVol`/`fsLGI` counterparts) are genuine,
complete, plausibly-ranged cortical measurements — not identifiers,
aggregates, or malformed fields — for one HCP-MMP1 parietal parcel (canonical
id `"5"`) whose two hemisphere columns simply do not share a common raw label
suffix in this source table. WP12/WP13's taxonomy parser mistook that
asymmetric *naming* for an asymmetric *parcel* and silently dropped both
columns. The parser (`scripts/abide_modeling_data.py`) was corrected to
recognise legitimate hemisphere-specific raw labels via a new
`atlas.hemisphere_specific_labels` manifest entry rather than disabling
validation, and every dependent audit, catalog, interactive artifact, and
portable notebook was regenerated from scratch — no stored 358-feature metric
was hand-edited or preserved.

With that fixed, every requested Exercise 2, Exercise 3, shared-styling,
interactive, and portable-notebook change from
`WPs/WP14_EXERCISES_2_AND_3_PEDAGOGICAL_REVISIONS.md` was implemented:
Exercise 2 is age-only linear regression again (the FIQ/regularisation
section is gone), teaches scaling explicitly before the pipeline shortcut,
and its sample-size demonstration now starts at n=50 and honestly reports a
genuine **double-descent** curve found in the re-audited data. Exercise 3
teaches k-selection with real, executable, training-only cross-validation
instead of an internal-script comment; its static k=15 A/B/C table and
separate k=1 demonstration are replaced by one interactive activity spanning
every valid k; and its existing k-explorer gained a synchronized numeric
input, three bootstrap training-sample tabs, and honestly-labelled
variance/bias-like proxy panels. Every "Think first" box across all three
canonical notebooks now uses one shared, distinctly blue MyST class. No push,
merge, deployment, or destructive git command occurred.

| Check | Before WP14 (WP13 final) | After WP14 |
|---|---|---|
| 360-parcel schema audit | not performed (358 assumed) | **confirmed: 360 genuine columns/measure, all 4 measures** |
| Frontend typecheck | PASS | PASS |
| Frontend unit (`vitest`) | 237 / 237 | **262 / 262** |
| `npm audit --omit=dev` | 0 vulnerabilities | 0 vulnerabilities |
| Widget artifacts `export_widget_data.py --check --artifact all` | 3 valid + canonical | 3 valid + canonical (unchanged) |
| Modelling manifest `abide_modeling_data.py --check` | self-consistent (p=358) | self-consistent (**p=360**) |
| Regression audit `regression_model_audit.py --check` | self-consistent (p=358) | self-consistent (**p=360**) |
| Regression catalog `export_regression_catalog.py --check` | valid + canonical | valid + canonical (**p=360**) |
| KNN audit `knn_model_audit.py --check` | self-consistent (p=358) | self-consistent (**p=360**, k=15 unchanged) |
| KNN explore data `export_knn_explore_data.py --check` | valid + canonical (schema v1) | valid + canonical (**schema v2**, +training samples) |
| KNN A/B/C data `export_knn_abc_data.py --check` | (new) | **valid + canonical** |
| Python unit (`unittest discover -s tests`) | 241 / 241 | **271 / 271** |
| Portable notebooks `build_portable_notebook.py --check` | up to date (ch1: 75, ch2: 33, ch3: 36) | up to date (ch1: **75, byte-identical**, ch2: **31**, ch3: **37**) |
| Portable smoke (out of repo, network) | ch1: 20, ch2: 13, ch3: 16 code cells | ch1: **20**, ch2: **12**, ch3: **16** code cells, key values matched |
| Standalone Playwright | 74 / 74 | **100 / 100** |
| Built-book Playwright | 33 / 33 | **36 / 36** |
| Clean Jupyter Book build | succeeded, 2 warnings | succeeded, **2 warnings** (same two pre-existing) |
| `*.err.log` guard | empty | empty |
| 2× consecutive clean builds, deterministic figures | identical (13 PNGs) | **identical (12 PNGs)** |

The two build warnings are the pre-existing `logo file 'logo.png' does not
exist` and `book/README.md: document isn't included in any toctree`. No new
warning was introduced. The PNG count dropped by one: Exercise 2 lost the
regularisation-preview bar chart (section deleted, no replacement figure);
Exercise 3 lost the static A/B/C 3-panel figure (replaced by an interactive
activity, no static figure) and gained the new CV-vs-k plot (one figure each
way, net zero for Exercise 3).

Before-column baseline was re-verified against the actual pre-edit tree
(`c6f153c`, WP13's final commit) prior to any WP14 change: Python 241/241,
frontend 237/237, standalone e2e 74/74, built-book e2e 33/33 — all matched
WP13's own final report numbers.

## 1. Branch, checkpoint, baseline (WP14 §0)

- Confirmed `feature/regression-practice` HEAD was `c6f153c` (`WP13 report:
  document Exercise 3 KNN and bias-variance tradeoff`) with one untracked
  file (`WPs/WP14_EXERCISES_2_AND_3_PEDAGOGICAL_REVISIONS.md`) and an
  otherwise clean tree.
- **Checkpoint commit `588a4c4855bf0fd443b69a1aa69996c69469493f`**
  (`checkpoint: before WP14`) — adds the WP brief only (1 file, +494).
- **Annotated tag `wp14-start`** → `588a4c4` (tag object
  `ec0624f2fbefdd8c2f3c0f6002c8e06ab3ab34bd`). The name was free; no
  conflict, no numeric suffix needed.
- Work continued on **`feature/regression-practice`** (the existing
  Exercise feature branch), not a new child branch — the WP's own
  preference, matching WP09–WP13.
- **Implementation commit `d5fbecc40f34c8458d71c17d9813c67997bbd486`**
  (`WP14: correct 360-parcel feature recipe; Exercises 2-3 pedagogical
  revisions`) — 35 files modified, 9 new; 4431 insertions(+), 2328
  deletions(-).
- No `git reset --hard`, `git checkout -- <path>`, `git clean`, `git
  rebase`, `git revert`, force-push, or tag/branch deletion at any point.

## 2. The 360-parcel audit (WP14 §1) — the mandatory gate

Per the WP's explicit instruction, this audit was performed and its result
confirmed **before** any notebook content was rewritten; had it come back
negative, the WP required stopping without touching the notebooks.

### 2.1 Method

Downloaded the pinned `abide2.tsv` directly (network, hash-verified against
`book/config/abide_modeling.json`'s pin
`ad0db42f85c77cbb8b4e023df288d34b29f1a63870a0cf1955c5b3b0d357579e` — matched)
and inspected its real column names with plain `pandas`/`re`, independent of
`scripts/abide_modeling_data.py`'s own parser. For each of the four
measurement prefixes (`fsCT`, `fsArea`, `fsVol`, `fsLGI`), computed the set
of raw ROI-label suffixes appearing in the `_L_` columns and in the `_R_`
columns.

### 2.2 Finding

For all four measures: **exactly 180** distinct raw labels in the left-
hemisphere columns and **exactly 180** in the right-hemisphere columns.
**179** labels are shared between hemispheres (an ordinary bilateral
parcel — e.g. `fsCT_L_V1_ROI` / `fsCT_R_V1_ROI`). The remaining one is
**not** shared by label: the left-hemisphere column is raw-labelled `5L`
(`fsCT_L_5L_ROI`) and the right-hemisphere column is raw-labelled `5R`
(`fsCT_R_5R_ROI`) — **never** `fsCT_R_5L_ROI` or `fsCT_L_5R_ROI`, confirmed
for all four measures. Both columns:

- are present for all 1004/1004 participants, zero missing;
- hold plausible, unremarkable continuous cortical-thickness values
  (`fsCT_L_5L_ROI`: range 1.427–3.322 mm, mean 2.316 mm, sd 0.297;
  `fsCT_R_5R_ROI`: range 1.297–3.421 mm, mean 2.328 mm, sd 0.284 — both
  squarely inside the plausible cortical-thickness range and
  indistinguishable in shape from any neighbouring parcel's column);
- match the exact `fs<measure>_<hemi>_<label>_ROI` naming pattern every
  other genuine brain column uses.

**Conclusion: this is one genuinely bilateral HCP-MMP1 parcel (canonical id
`"5"`), not two single-hemisphere-only ROIs.** It is the *only* ROI in the
entire atlas whose two hemisphere columns do not share a raw label suffix in
this particular source table (a quirk of how this specific CSV was
generated, not a defect in the underlying FreeSurfer measurements). 180
canonical parcels × 2 hemispheres = **360 genuine columns per measurement
family**, for all four families — the audit's schema claim WP14 §8 requires
is fully confirmed.

### 2.3 Why WP12/WP13 missed this

`scripts/abide_modeling_data.py`'s original `parse_brain_column` correctly
parsed both `fsCT_L_5L_ROI` and `fsCT_R_5R_ROI` as valid brain columns (the
raw labels `"5L"`/`"5R"` were already in the reviewed
`roi_label_inventory`), but treated them as **two separate,
single-hemisphere-only ROI labels** (`atlas.asymmetric_labels = ["5L",
"5R"]`) and excluded both from the `all-eligible` bundle used to build `X`.
That is a correct description of *this table's naming*, but an incorrect
inference about *the underlying anatomy*: both raw labels are the two
hemisphere halves of one bilateral parcel, and excluding them both drops a
real, informative feature pair rather than "an asymmetric ROI that cannot
form a bilateral pair" (the prior code's own comment, now removed).

### 2.4 The fix

`book/config/abide_modeling.json`'s `atlas` block replaced
`asymmetric_labels: ["5L", "5R"]` with `hemisphere_specific_labels: {"5":
{"L": "5L", "R": "5R"}}` (canonical ROI id → the raw label used in each
hemisphere's own column); `roi_label_inventory` now lists 180 canonical ids
(`"5"` in place of `"5L"`/`"5R"`) and `bilateral_label_count: 180`.
`scripts/abide_modeling_data.py` was updated to resolve raw labels through
this mapping in both directions (`raw_label_for(roi, hemi)` when building
column names; a reverse lookup when parsing them), so `parse_brain_column`
still validates the hemisphere each raw label is legitimately allowed in
(unchanged, correct behaviour), while `bundle_rois("all-eligible")` and
`bundle_columns` no longer exclude the parcel. Per the WP's explicit
instruction, **no special-case student explanation was added** — the
notebooks simply say "360 cortical parcels" with no mention of the
correction, and the taxonomy parser now recognises the legitimate name
rather than disabling validation generally (every other leakage/inventory
check is unchanged and still enforced).

Full detail: `WP14_EXACT_CHANGELOG.md` §2.

## 3. Updated Exercise 2 and KNN metrics (WP14 §1, §3.5, §4.1)

Every affected audit was rerun from scratch (network, pinned-hash-verified
sources) rather than hand-edited. None of the fixed participant splits
changed (same `random_state`s throughout); only the feature count and the
metrics computed from it did.

| Metric | Before (p=358) | After (p=360) |
|---|---:|---:|
| Exercise 2 OLS, locked held-out R² | 0.475 | **0.469152** |
| Exercise 2 OLS, locked held-out MSE | ≈49.0 | **49.5544** |
| Exercise 2 5-fold CV R² (catalog, `all-eligible__CT`) | ≈0.46 | **0.465** |
| `all-eligible × [CT,Area]` feature count / catalog status | p=716, disabled | **p=720, disabled** |
| KNN training-only 5-fold CV, selected k | 15 | **15 (unchanged)** |
| KNN training-only CV R² at selected k | 0.598 | **0.599** |
| KNN locked held-out R² at k=15 | 0.647 | **0.649168** |
| KNN locked held-out MSE at k=15 | 33.0 | **32.75** |
| KNN k=1 training-only CV R² | 0.452 | **0.4565** |
| Exercise 3 dev-split validation-optimal k | 17 | **17 (unchanged)** |
| Dev-split fitting-set mean (years) | 15.192 | **15.192373** |

The selected `k` (15) and the dev-split validation-optimal `k` (17) both
happen to be numerically unchanged by the correction; every R²/MSE value
shifted by a small but real amount. This was verified empirically, not
assumed — per WP14 §1's explicit instruction not to assume WP12/WP13 values
survive unchanged.

## 4. Exercise 2 revisions (WP14 §3)

- **§3.1 FIQ/regularisation removed entirely.** The whole "5. Regularisation
  preview: age vs FIQ with the full brain" section (4 cells) is deleted from
  both the canonical and portable notebooks. `FIQ` does not appear anywhere
  in the notebook's markdown, code, or executed output (asserted by
  `test_no_fiq_or_regularisation_content`). The data-loading cell no longer
  merges the phenotypic CSV at all — `age` is a native column of the brain
  table, so per the WP's own preference the loader was simplified to the
  single table, dropping the `phen`/`SUB_ID`/`KEEP_PHEN` machinery
  entirely (not just hiding it). `scripts/regression_model_audit.py`
  (the FIQ/regularisation audit script itself) and its result JSON remain
  as internal, dev-facing tooling — still tested, still regenerated with
  the 360-feature fix — since it is reviewed infrastructure independent of
  what any notebook shows a student, exactly as the WP allows.
- **§3.2 Research-question framing.** The opening now states plainly that
  ABIDE's own research aim is autism-related group differences and
  diagnosis, that rich shared datasets can support other scientifically
  appropriate questions honestly stated as such, and that this notebook's
  question — predicting `age`, a continuous variable, from cortical
  measurements — is one such question, not an answer to ABIDE's primary
  one. No classification method is introduced.
- **§3.3 Instructor-facing commentary removed.** The phrase "without
  turning this into a splitting lecture" is gone. A repo-wide scan (folded
  into `test_no_wp_script_or_report_references_in_student_text`) found no
  other WP/report/script/internal-decision reference in either notebook's
  markdown or code beyond the intended provenance-linked pieces.
- **§3.4 Explicit scaling, then the pipeline shortcut.** A new cell writes
  out `scaler = StandardScaler(); X_train_scaled = scaler.fit_transform(...);
  X_test_scaled = scaler.transform(...)` and fits a plain `LinearRegression`
  on the scaled arrays, printing its own R²/MSE. The following markdown cell
  explains `fit_transform` vs `transform`, states the scaler-must-never-be-
  fit-on-test-data rule, and notes explicitly that unregularised OLS with an
  intercept is scale-invariant (so the numbers will match exactly) while
  flagging that this will **not** be true for KNN, the next practice. Only
  then does the (unchanged-code) pipeline cell appear, now asserting
  `np.allclose(y_pred, explicit_pred)` before anything downstream reuses
  `model`/`y_pred`/`test_r2`/`test_mse` — one clearly defined model path,
  not two competing results.
- **§3.5 All 360 CT parcels.** Every "358 features"/"358-feature" mention
  in prose, code comments, and printed output is now "360". The special-case
  `ASYMMETRIC_ROIS` exclusion in the feature-selection cell is gone; the
  cell is now the single line `FEATURES = [c for c in BRAIN_COLS if
  c.startswith("fsCT_")]`.
- **§3.6 Low-N learning curve.** Sizes are now the WP's own predeclared
  sequence, `[50, 100, 200, 300, 400, 550, len(y_train)]` — no adjustment
  was needed for determinism or feasibility, so none is documented as a
  deviation. 40 repeated deterministic subsamples per size (unchanged
  repeat count from WP11/WP12), reporting **median** (switched from mean,
  more robust given the extreme instability found — documented in the
  notebook) plus the 10th–90th percentile spread, for both R² and MSE. The
  right-hand R² panel plots the full, unclipped range; the left-hand MSE
  panel uses a log y-scale, both with an `n_train = p` marker. See §6 below
  for what the curve actually showed.

## 5. Cross-validation candidate set and selected k (WP14 §4.3, §8)

Candidate set: `[1, 3, 5, 7, 10, 15, 20, 30, 50, 100, 200]` (11 values,
log-spaced, deliberately small — "a manageable candidate set", per the WP).
5-fold `KFold(shuffle=True, random_state=0)` on `X_train, y_train` only
(Exercise 2's own documented cross-validation protocol, reused verbatim);
`cross_val_score(..., scoring="r2")` per candidate; `K_SELECTED =
int(cv_results.loc[cv_results["mean_cv_r2"].idxmax(), "k"])`. Executed live
in the notebook, this selects **k = 15** with mean CV R² = **0.599** —
exactly reproducing `scripts/knn_model_audit.py`'s independent, wider
(log-spaced 1..602) grid search over the same fold protocol, confirmed by
`test_executable_cv_reproduces_the_committed_audit_selected_k`. The test set
is never read by this cell (`X_test`/`y_test` do not appear in its source,
asserted structurally); the notebook states explicitly that the test set's
only role, once `k` is fixed, is to estimate performance, not choose it.

## 6. Sample-size demonstration: a real double-descent curve

Running the predeclared `[50, 100, 200, 300, 400, 550, 753]` sizes on the
corrected 360-feature recipe produced a genuinely **non-monotonic** curve —
confirmed reproducible across several other seeds before being written into
the notebook, so this is reported as a real, seed-robust finding, not an
artefact of one unlucky draw:

| n_train | n/p | median held-out R² | regime |
|---:|---:|---:|---|
| 50 | 0.14 | **+0.514** | deeply underdetermined |
| 100 | 0.28 | +0.508 | deeply underdetermined |
| 200 | 0.56 | +0.299 | underdetermined |
| 300 | 0.83 | −0.742 | underdetermined, approaching threshold |
| 400 | 1.11 | **−1.945 (worst)** | just past the interpolation threshold |
| 550 | 1.53 | +0.160 | overdetermined, recovering |
| 753 | 2.09 | +0.469 | matches Section 2 exactly |

The worst point is **not** the smallest sample size — it is `n_train = 400`,
just past `n_train = p = 360`. This is the well-documented "double descent"
phenomenon (Belkin, Hsu, Ma & Mandal, 2019, PNAS,
`doi:10.1073/pnas.1903070116`), not a bug: deep in the underdetermined
region the minimum-norm solution `scikit-learn` returns behaves like an
implicitly regularised estimator and still predicts reasonably; near the
interpolation threshold that implicit regularisation is weakest and the fit
is most unstable; well past it, ordinary least squares becomes well posed
again. WP14 §3.6 required not clipping or silently omitting extreme
negative R² values and emphasising that the curve reflects both sample size
and the `n<p`→`n>p` transition — both are satisfied, and the notebook names
the phenomenon explicitly rather than describing a smooth monotonic story
that the data does not actually show.

## 7. Exercise 3 revisions (WP14 §4)

- **§4.1 Same 360-feature recipe.** Byte-identical (non-comment) feature
  cell to Exercise 2's, asserted by test; same locked 753/251 split. KNN
  audit rerun (see §3 above); every dependent metric, figure, annotation,
  activity default, portable output, and test updated from the new result,
  not assumed unchanged.
- **§4.2 Internal references removed.** The multi-line comment naming
  `scripts/knn_model_audit.py` and pointing to "the WP13 report" is gone,
  replaced by the executable CV cell itself (§5). A repo-wide scan of the
  canonical notebook's markdown and code for `scripts/`, `wp11`–`wp14`,
  "audit script", "audit_result" found none remaining
  (`test_no_wp_script_or_report_references_in_student_text`). Internal
  scripts/tests/reports keep their real paths in their own files.
- **§4.3 Executable training-only CV.** See §5 above.
- **§4.4 Section 3 replaced by one interactive.** The static k=15 A/B/C
  table+figure and the separate static k=1 demonstration
  (`invalid_test_fitted_model`, `invalid_test_fitted_model_k1`,
  `knn_demo_k1`) are gone from both notebooks. In their place: one new
  `knn-abc` interactive activity (new component/config/data/export-script
  stack, §9 below) with a slider **and** a synchronized numeric input
  spanning `k = 1..min(n_train, n_test) = 1..251` (the shared valid range,
  since panel C's own reference pool is the smaller 251-row test set).
  Moving `k` recomputes all three panels' real predictions, R², MSE, and
  plots from the precomputed neighbour-ordered target arrays — never a
  relabel. Every panel shares identical axes and a
  `"Perfect prediction (observed = predicted)"` legend entry. Default k =
  15 (the audit-selected value). The endpoint/prompt bullets from WP14
  §4.4 (k=1 makes B/C exactly perfect; A at k=1 is not; increasing k
  usually narrows the gap) are stated both inside the widget (`k1Note`
  config field) and in the notebook's own markdown immediately after the
  iframe.
- **§4.5 Numeric input for the existing explorer.** A synchronized numeric
  field (`1..N_fit`) sits beside the slider in both activities; typed
  values outside that range or non-integer are rejected and the field
  reverts to the last valid `k` rather than producing an invalid model
  silently; both directions (slider→number, number→slider) update live;
  both are keyboard-operable (Playwright-verified); refresh restores the
  configured default.
- **§4.6 Identity-line legend.** Every observed-vs-predicted scatter across
  both KNN activities (and, for consistency, Exercise 2's own OLS scatters)
  now shows a visible legend entry reading exactly
  `"Perfect prediction (observed = predicted)"` — the prior `knn-explore`
  scatter had `showlegend: false` entirely (a real bug this WP fixed, not
  just a wording change).
- **§4.7 Duplicate reflection removed.** The notebook's own Section 6 Think
  first block (`wp13-062`), which substantially repeated the widget's own
  "Reflect" prompts, is deleted; the widget's config-driven prompts were
  extended (2 new entries, covering the training-sample and calibration
  additions) to keep exactly one place carrying that content. No empty
  wrapper or stray heading remains (verified structurally).
- **§4.8 Training-sample variance.** Three deterministic training samples —
  `A` (the actual, unresampled 564-row fitting set) and `B`/`C` (independent
  bootstrap resamples, seeds 101/102, size 564, each refit with its own
  `StandardScaler`) — feed three labelled tabs
  ("Training sample A/B/C") that switch the observed-vs-predicted scatter's
  predictions while leaving the 189 validation participants themselves
  untouched (asserted structurally: `trainingSamples.A` byte-equals the
  original unresampled baseline; `B`/`C` are provably different draws).
  A **training-sample-sensitivity ("variance") proxy** — mean, across
  validation participants, of the SD of the three samples' predictions at
  the current `k` — is displayed with an explicit caveat that it is an
  empirical proxy, not the formal population variance term (ABIDE gives one
  sample, not repeated draws from the true data-generating process).
- **§4.9 Bias-like proxy.** A binned calibration panel (6 equal-width age
  bins; x = bin-mean observed age, y = bin-mean ensemble-mean prediction,
  identity line) visibly flattens toward the fitting-set mean as `k` grows.
  The quantitative proxy is the **OLS slope of the ensemble-mean prediction
  regressed on the observed value** (1 = predictions track observed age
  closely; 0 = fully flattened), shown with the WP's own required exact
  caveat wording: "an observable bias-like underfitting proxy... not formal
  bias²... ABIDE does not reveal the unknown population function... the
  observed age-level outcomes still contain irreducible variation this
  slope cannot separate out."
- **§4.10 Central k-complexity relationship.** Stated as a prominent
  paragraph at the top of Section 6, explicitly connecting both
  interactives (Section 3's honest-vs-invalid comparison and Section 6's
  explorer): larger `k` → simpler/smoother, lower variance/higher bias;
  smaller `k` → more flexible, lower bias/higher variance, greater
  overfitting risk; "lower bias" qualified as a general KNN tendency, not an
  absolute guarantee for every finite sample. The exact `k = N_fit`
  mean-prediction endpoint is tested for **every** training selection (A,
  B, and C independently), not just the original baseline.

## 8. Interactive architecture and performance (WP14 §5)

- Section 3's comparison is a **new, separate config-driven activity type**
  (`knn-abc`) rather than crowding the existing `knn-explore` component,
  giving the clearest separation between the two activities' very different
  purposes (one deliberately contains an invalid/leakage panel by design;
  the other never does). Both reuse the same pure metric helpers
  (`r2Score`, `meanSquaredError`, `sharedAxisRange`, `predictAllForK`) —
  nothing duplicated.
- Section 6's enhancement extends the existing component in place (fixed
  validation set preserved; all new computation deterministic; only
  target-neighbour age values are stored, never participant IDs, raw
  features, site, or diagnosis — enforced by both scripts' identifier-key
  scans and both TypeScript schemas' `IDENTIFIER_TOKEN` checks).
- Artifact sizes, documented: `abide_knn_explore.json` grew from 697,322 to
  **2,719,089 bytes** (three 189×564 neighbour matrices instead of one —
  the direct cost of the three training-sample tabs); the new
  `abide_knn_abc.json` is **1,850,283 bytes** (three matrices sized
  251×251/753×251/251×251, truncated to the shared `k_max=251`). Both load
  with no kernel, backend, CDN, WebSocket, or live data request (Playwright
  `requestfailed`/`websocket` listeners assert empty on every load) and
  remain usable at 390 px with zero horizontal document overflow (asserted
  numerically, `overflow <= 1px`, in both standalone and built-book specs).
- Every stored prediction was independently validated against a real
  `Pipeline(StandardScaler(), KNeighborsRegressor(k))` at representative
  k-values for every panel/sample before being written (`atol=1e-6`); an
  early draft of `export_knn_abc_data.py`'s own validation step
  fit the comparison sklearn model on **raw, unscaled** features while the
  stored neighbour matrices used **scaled** distances, producing a max
  absolute prediction difference of 40.0 years at k=1 — caught by the
  validation step itself before anything was written, fixed by wrapping the
  comparison fit in the same `Pipeline(StandardScaler(), ...)` the stored
  data actually uses. The identical bug (present from the start, since both
  scripts share the same pattern) was found and fixed in
  `export_knn_explore_data.py`'s new bootstrap-sample validation at the
  same time.

## 9. Portable notebooks and student-facing cleanliness (WP14 §6)

- Regenerated via `scripts/build_portable_notebook.py --write` for
  chapters 2 and 3; chapter 1 verified byte-identical (`--check`, not
  touched by this WP beyond the shared CSS, which portable notebooks do not
  carry).
- The generator gained an optional "iframe followup code" mechanism: for
  the new `knn-abc` iframe, the portable notebook gets a runnable
  three-panel-matplotlib equivalent with an editable `k_demo = K_SELECTED`
  variable (reusing the already-in-scope `X_train`/`X_test`/`y_train`/
  `y_test` from the earlier cells) — the WP14 §4.4 requirement, satisfied
  with real, running code rather than another static markdown pointer. The
  pre-existing `knn-explore` iframe keeps its WP13-established pointer to
  "Section 5 above" (already a full non-interactive equivalent).
- `_assert_portable`'s existing banned-substring/hide-tag/execution-count/
  install-command checks all re-ran clean for both regenerated notebooks.
- No `FIQ`/regularisation content, no student-facing `scripts/`/WP/report/
  internal-artifact reference, no repository-relative data path in either
  canonical or portable Exercise 2/3 notebook (all asserted by tests, not
  just manually reviewed).
- Out-of-repository smoke execution (network, no repo checkout): all three
  portable notebooks executed cleanly and matched every expected string —
  see the validation table above.

## 10. Shared blue Think first (WP14 §2)

One CSS class, `think-first`, already existed (introduced in WP06) but
shared its visual treatment with the rust-coloured `.challenge`/
`.how-to-use` admonitions and was used inconsistently — Exercise 1 already
tagged its blocks `:class: think-first`, while Exercises 2 and 3 used the
theme's plain `:class: note`. This WP:

- Split the CSS: `.challenge`/`.how-to-use` keep their original rust
  appearance verbatim; `.admonition.think-first` gets its own new rule
  block using new, dedicated `--ml-think-*` tokens (light and dark), a
  clearly blue border/header/background, the same `?` glyph, accessible
  contrast (AA-checked ink-on-background pairs in both themes).
- Migrated every `:class: note` "Think first" block in Exercises 2 and 3 to
  `:class: think-first` as part of each notebook's rewrite. Exercise 1
  needed no markup change — it already used the shared class, so the CSS
  split alone changes its rendered colour.
- Added `tests/test_think_first_shared_class.py`: scans all three
  canonical notebooks and asserts every "Think first" admonition uses
  `:class: think-first` (none found using any other class) and that no
  legacy `:class: note` variant remains anywhere; also asserts the CSS
  defines `.think-first` in its own selector block (not merged with
  `.challenge`/`.how-to-use`) with the new blue tokens present.
- Visually inspected (Playwright screenshots, desktop 1280 px and mobile
  390 px, both chapters) — confirmed clearly blue, legibly bordered,
  correctly spaced, and distinct from the orange "Check your reasoning"
  dropdowns and run/download banners beside them at both widths.

## 11. Exact test commands and results

```
python -m unittest discover -s tests                             # 271 / 271
(cd interactive && npm run typecheck)                             # PASS
(cd interactive && npm run test:unit)                             # 262 / 262
(cd interactive && npm run build)                                 # succeeded (pre-existing 500kB Plotly-chunk advisory only)
(cd interactive && npm audit --omit=dev)                          # 0 vulnerabilities
(cd interactive && npx playwright test)                           # 100 / 100
python scripts/build_portable_notebook.py --check --notebook all  # all 3 up to date
python scripts/smoke_portable_notebook.py --notebook all          # OK x3, network, key values matched
rm -rf book/_build && jupyter-book build book                     # succeeded, 2 pre-existing warnings, no *.err.log
(cd interactive && npm run test:e2e:book)                         # 36 / 36
# repeated jupyter-book build x2: identical 12-PNG SHA-256 set both times
```

Full before/after test-file breakdown: `WPs/reports/WP14_EXACT_CHANGELOG.md`
§15.

## 12. Warnings, deviations, deferred / not performed

1. **PNG count dropped from 13 to 12** — not a regression: Exercise 2 lost
   one figure (the deleted regularisation-preview bar chart, no
   replacement) and Exercise 3's figure count is unchanged net (lost the
   static A/B/C figure, gained the new CV-vs-k plot).
2. **`abide_knn_explore.json` grew roughly 4×** (697 KB → 2.72 MB) — the
   direct, documented cost of storing three independent 189×564 neighbour
   matrices (one per training sample) instead of one. Not reduced further
   (e.g. by shrinking decimal precision below 4 places) because the
   existing precision was already validated against real sklearn output at
   `atol=1e-6` and reducing it further risked reintroducing detectable
   prediction drift; judged an acceptable, one-time, documented size cost
   for the pedagogical value of the three-sample comparison.
3. **Bootstrap resample size chosen as 564 (= N_fit), not a smaller
   subsample** — chosen so the training-sample tabs share exactly the same
   valid `k` range (`1..N_fit`) as the original explorer, avoiding a
   second, smaller k-ceiling special case in the UI. Bootstrap-with-
   replacement was preferred over disjoint subsampling per the WP's own
   "preferably equal-sized bootstrap resamples" wording.
4. **Candidate k grid for the notebook's own CV cell (11 values) is coarser
   than the audit script's own grid (log-spaced 1..602)** — deliberately:
   the WP asked for "a manageable candidate set... not an overwhelming
   list." Verified before committing that the coarser grid's argmax still
   lands on k=15 (matching the finer-grid audit) both from the full
   `cv_curve` data and from live execution.
5. **The `export_knn_abc_data.py` / `export_knn_explore_data.py`
   scaled-vs-raw validation bug** (§8 above) was caught and fixed before
   any artifact was ever committed — recorded here for transparency, not
   because any incorrect data was ever shipped.
6. **No live/remote checks** — by the stop condition: no push, no `main`
   merge, no deployment. GitHub Pages still serves the WP08–WP13 content;
   hosting and the private/public distribution architecture were not
   touched.
7. **Colab interactive rendering not machine-verified** (unchanged
   limitation from WP07–WP13; Google serves an app shell to headless
   automation). The article-header button's `href`, the opening
   admonition's links, and the portable notebook's own `metadata.colab.name`
   are all covered by tests instead.
8. **Pre-existing warnings kept** — `logo.png` missing, `book/README.md`
   not in a toctree, the Vite 500 kB Plotly-chunk advisory. All unchanged,
   out of scope.

## Unresolved risks / needs Yoav

- **Private-repository distribution** (carried unchanged from WP09–WP13):
  the Colab / raw-download buttons and the article-header Colab button all
  target `github.com/yoavmp/ml-neuro-tutorials` on `main` and will break for
  non-collaborators if the repo goes private. Not in scope for WP14.
- **Merge / deployment of WP09–WP14** is a separate, later WP after review.
- **Classification** is the next practice, deliberately not started (only
  the existing forward-looking mentions remain, unchanged in count).
- **The double-descent finding in Exercise 2's Section 5** is a genuine,
  seed-robust empirical result, not a data-quality issue — but it is a more
  advanced statistical phenomenon than the notebook previously taught, and
  Yoav may want to review whether the explanation pitched (three regimes,
  cited to Belkin et al. 2019) is at the right level for this course's
  audience, or whether a lighter-touch treatment is preferred.
- **`abide_knn_explore.json`'s size (2.72 MB)** is larger than any other
  committed interactive artifact in this repository; acceptable for a
  static GitHub Pages site but worth a conscious sign-off given it is a
  meaningful jump from WP13's 697 KB.

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
  `git status` before every commit in this WP).
  `book/config/abide_modeling.json`,
  `book/_static/widgets/data/abide_knn_explore.json`,
  `book/_static/widgets/data/abide_knn_abc.json`,
  `scripts/knn_model_audit_result.json`, and
  `scripts/regression_model_audit_result.json` are committed
  source/reviewed assets, not build output.
- **Exercise 1 content unchanged** — its canonical notebook is not present
  in this commit's diff at all (confirmed by `git diff wp14-start..HEAD --
  book/chapters/chapter_01`, empty); its portable notebook is verified
  byte-identical; only the shared `book/_static/custom.css` touches it, and
  only by recolouring a class it already used.
- **No held-out test score was consulted to choose the feature space, k, or
  any modelling decision** — every selection came from the training-only
  cross-validation procedure or was predeclared before any score was seen;
  the notebook's own CV cell excludes `X_test`/`y_test` from its source
  (asserted structurally), and the audit script's isolation tests
  (`tests/test_knn_model_audit.py`, unchanged from WP13, still passing
  against the 360-feature data) continue to verify this by mocking
  `.fit()`, not just by inspection.
- **The outer test set is never touched by the Section 5 development curve
  or either interactive activity's underlying computation** — Section 5 and
  the `knn-explore` artifact derive entirely from the 753-row
  outer-training partition (unchanged from WP13, re-verified);
  `knn-abc`'s panel C is a **deliberately, visibly labelled invalid**
  exception to this rule by design (its entire pedagogical point), isolated
  to its own activity and never used by model selection anywhere else.
- **No WP15 created, no classification exercise begun.** Stopping here per
  the WP's own stop condition.

## Key identifiers

| Item | Value |
|---|---|
| Branch | `feature/regression-practice` (unchanged, off `c6f153c`) |
| Checkpoint commit | `588a4c4855bf0fd443b69a1aa69996c69469493f` (`checkpoint: before WP14`) |
| Checkpoint tag | `wp14-start` → `588a4c4` (annotated; tag object `ec0624f2fbefdd8c2f3c0f6002c8e06ab3ab34bd`) |
| Implementation commit | `d5fbecc40f34c8458d71c17d9813c67997bbd486` (`WP14: correct 360-parcel feature recipe; Exercises 2-3 pedagogical revisions`) — 35 modified, 9 new; 4431 insertions(+), 2328 deletions(-) |
| Report commit | adds `WPs/reports/WP14_REPORT.md` + `WPs/reports/WP14_EXACT_CHANGELOG.md` only — SHA in the terminal summary |
| Modelling manifest | `book/config/abide_modeling.json` SHA-256 `1dacce47b2eab81460f379b58dee78641a8a1d01fa0d68a4f52d22aba708c31b` |
| Regression audit result | `scripts/regression_model_audit_result.json` (regenerated in place) |
| KNN audit result | `scripts/knn_model_audit_result.json` (regenerated in place, selected k=15 unchanged) |
| KNN explore data | `book/_static/widgets/data/abide_knn_explore.json` SHA-256 `e3ceb0ff4d1e2d2dab8f3eecd1eefacf951de57efa4bbefba41a6819ad01794e` (2,719,089 bytes, schema v2) |
| KNN A/B/C data (new) | `book/_static/widgets/data/abide_knn_abc.json` SHA-256 `07dc7107c447affc54c92bb53cb51d4eba63f1ca315623411d45c9a89e84515e` (1,850,283 bytes) |
| Canonical Exercise 2 notebook | `book/chapters/chapter_02/exercise_02.ipynb` SHA-256 `8c28c9af61874ec99a82589ca8b8702796f7b9692396f29962c1662d580430f4` |
| Canonical Exercise 3 notebook | `book/chapters/chapter_03/exercise_03.ipynb` SHA-256 `4c84c35b6abb077b1a62631fe8eb6f44258b941b32f1164f694bf998434ebd73` |
| Portable Exercise 2 notebook | `book/downloads/chapter_02/exercise_02_portable.ipynb` SHA-256 `38167900e8fb45254602949a7fdc902f3c1ca0092323b15d943792109f69a8c4` |
| Portable Exercise 3 notebook | `book/downloads/chapter_03/exercise_03_portable.ipynb` SHA-256 `302ec876316c2feabd0f33f4a51d8c73cc1a6d14272c7670b70755c29dbcd8d3` |

## Instructions for reviewer

Paste this entire report (`WP14_REPORT.md`) into the ChatGPT conversation
that produced WP14. `WP14_EXACT_CHANGELOG.md` is the companion
location-specific before/after record.
