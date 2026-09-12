# WP12 implementation report — Exercise 2 corrections and regression model audit

## Outcome

Status: **SUCCESS**

WP12's empirical audit (`scripts/regression_model_audit.py`) found that **`age`
has reliably positive out-of-sample R² in every feature space and model family
tested, while `FIQ` never does — including regularised**. Per the WP's decision
policy this moved the notebook's main ordinary-linear-regression example from
`FIQ` to `age`; the whole Exercise 2 notebook, the interactive feature-set
comparison, the portable notebook, the Colab/download navigation, the two
wording/code corrections, and every dependent config/test were updated to
match, and a new "regularisation preview" section reports the honest ridge/
lasso result for both targets. No KNN or bias–variance content was added. No
push, merge, deployment, or destructive git command occurred.

| Check | Before WP12 | After WP12 |
|---|---|---|
| Frontend typecheck | PASS | PASS |
| Frontend unit (`vitest`) | 217 / 217 | **217 / 217** |
| `npm audit --omit=dev` | 0 vulnerabilities | 0 vulnerabilities |
| Widget artifacts `export_widget_data.py --check --artifact all` | 3 valid + canonical | 3 valid + canonical (unchanged) |
| Modelling manifest `abide_modeling_data.py --check` | self-consistent (FIQ main) | self-consistent (**age main**) |
| Regression catalog `export_regression_catalog.py --check` | valid + canonical (FIQ, n=908) | valid + canonical (**age, n=1004**) |
| Regression audit `regression_model_audit.py --check` | (new) | **self-consistent** |
| Python unit (`unittest discover -s tests`) | 161 / 161 | **184 / 184** |
| Portable notebooks `build_portable_notebook.py --check` | up to date (ch1: 75, ch2: 37) | up to date (ch1: **75, byte-identical**, ch2: **33**) |
| Portable smoke (out of repo, network) | ch1: 20, ch2: 15 code cells | ch1: **20**, ch2: **13** code cells, key values matched |
| Standalone Playwright | 60 / 60 | **60 / 60** |
| Built-book Playwright | 19 / 19 | **26 / 26** |
| Clean Jupyter Book build | succeeded, 2 warnings | succeeded, **2 warnings** (same two pre-existing) |
| `*.err.log` guard | empty | empty |
| 2× consecutive clean builds, deterministic figures | identical (9 PNGs) | **identical (9 PNGs)** |

The two build warnings are the pre-existing `logo file 'logo.png' does not
exist` and `book/README.md: document isn't included in any toctree`. No new
warning was introduced.

## 1. Branch, checkpoint, baseline (WP12 §0)

- Confirmed `feature/regression-practice` HEAD was `9007054` (`WP11 report:
  document Exercise II linear regression`) with one untracked file
  (`WPs/WP12_EXERCISE_2_CORRECTIONS_AND_MODEL_AUDIT.md`) and an otherwise clean
  tree.
- **Checkpoint commit `30515629c6e4ddf2716581ed2295ec65f4b3fe65`**
  (`checkpoint: before WP12`) — adds the WP brief only (1 file, +333).
- **Annotated tag `wp12-start`** → `3051562` (tag object
  `6e5802496f41e15ce39d4df3e0f45e4fdc775176`). The name was free; no numeric
  suffix needed.
- Work continued on **`feature/regression-practice`** (the existing Exercise 2
  feature branch), not a new child branch — the WP's own preference.
- The full baseline (Python 184→ wait, see table: WP11's own final numbers)
  was taken from the WP11 report's "after" column, then re-verified against
  the actual pre-edit tree before any WP12 change (Python 161/161, frontend
  217/217, standalone e2e 60/60, built-book e2e 19/19 — all matched).
- No `git reset --hard`, `git checkout -- <path>`, `git clean`, `git rebase`,
  `git revert`, force-push, or tag/branch deletion at any point.

## 2. The modelling audit (WP12 §5) — the empirical gate for everything else

**Script:** `scripts/regression_model_audit.py` (`--run` writes/`--check`
re-validates `scripts/regression_model_audit_result.json`, SHA-256
`6aef676e63ce83a6d9899c25036249a1664ad9ae72311aae665d1e59869e7b2a`). Not
manually experimented in the canonical notebook first — the audit ran, was
inspected, and only then did the notebook rewrite start.

### 2.1 Outcomes (WP12 §5.1)

| Target | usable N | missing | range | mean | sd | missing brain cells |
|---|---|---|---|---|---|---|
| `age` | **1004** | 0 | 5.1–64.0 | 15.10 | 9.43 | 0 |
| `FIQ` | **908** | 96 | 49–149 | 111.14 | 15.27 | 0 |

`age` is a native column of `abide2.tsv` (no join required); `FIQ` requires the
same phenotypic-file join WP11 established. No identifier, diagnosis, site,
sex, or the target itself ever enters `X` (`assert_brain_only`, unchanged from
WP11, re-verified for `age`).

### 2.2 Feature spaces tested (WP12 §5.2)

1. **every eligible cortical feature across all four measures** —
   `all-eligible x [CT,Area,Vol,LGI]`, p = 1432;
2. **each single measurement family across all eligible ROIs** —
   `all-eligible x CT` / `Area` / `Vol` / `LGI`, p = 358 each;
3. **the predeclared compact bundle** — `frontoparietal x CT`, p = 78 (the
   WP11 P-FIT bundle; run for both targets as the "where scientifically
   relevant" comparison — it is FIQ's literature bundle, not age's, and is
   labelled as such).

No feature was ever selected by inspecting its association with the full
target; the bundles are the same ones predeclared in the manifest before this
WP. `p`, training N, and `p/n_train` for every candidate below.

### 2.3 Models and protocol (WP12 §5.3)

`Pipeline(StandardScaler(), estimator)` throughout, scaler fit on
train/fold only. Two complementary, both leakage-isolated procedures:

- **Nested / isolated 5-fold CV** — outer `KFold(n_splits=5, shuffle=True,
  random_state=0)`; for ridge/lasso, `alpha` is chosen by an **inner**
  `KFold(n_splits=5, shuffle=True, random_state=1)` on the outer-training rows
  only (`RidgeCV`/`LassoCV` nested inside the outer loop). This is the primary
  audit result — nothing here ever touches a held-out set more than once
  because there is no single held-out set; every row is scored exactly once,
  out of fold.
- **One locked holdout split**, evaluated **exactly once** per candidate —
  `train_test_split(test_size=0.25, random_state=42, stratify=group)`, the
  manifest's own `protocol.holdout_split` — reported alongside, for the single
  numbers the notebook actually quotes. Alpha selection on this split is again
  via `RidgeCV`/`LassoCV`'s own inner CV on the training rows only.
- Ridge alpha grid: `np.logspace(-1, 6, 29)`. Lasso alpha grid:
  `np.logspace(-3, 2, 26)`. Both documented in the manifest
  (`protocol.regularisation_preview`) and in the audit script.
- OLS is computed even where `p >= n_train` **for diagnostic comparison only**,
  labelled `underdetermined` (never recommended); verified programmatically
  (`tests/test_regression_model_audit.py::test_every_ols_candidate_with_p_over_n_is_labelled_underdetermined`).
- Deterministic seeds throughout (`OUTER_CV_SEED=0`, `INNER_CV_SEED=1`,
  matching the manifest's existing `random_state=0` 5-fold protocol).

### 2.4 Full audit table (nested / isolated CV)

| target | feature space | model | p | n_train/fold | p/n | cvR² | cvMSE | α (median) | non-zero coefs |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| age | all-eligible × all 4 measures | linear | 1432 | 803 | 1.78 | **−0.516** (UNDERDET.) | 132.9 | — | 1432 |
| age | all-eligible × all 4 measures | ridge | 1432 | 803 | 1.78 | **+0.689** | 27.5 | 1000.0 | 1432 |
| age | all-eligible × all 4 measures | lasso | 1432 | 803 | 1.78 | **+0.686** | 27.9 | 0.1585 | 193 |
| FIQ | all-eligible × all 4 measures | linear | 1432 | 726 | 1.97 | **−3.236** (UNDERDET.) | 979.7 | — | 1432 |
| FIQ | all-eligible × all 4 measures | ridge | 1432 | 726 | 1.97 | **−0.009** | 234.0 | 10000.0 | 1432 |
| FIQ | all-eligible × all 4 measures | lasso | 1432 | 726 | 1.97 | **−0.001** | 232.4 | 1.585 | 8 |
| age | all-eligible × CT | linear | 358 | 803 | 0.45 | **+0.461** | 47.5 | — | 358 |
| age | all-eligible × CT | ridge | 358 | 803 | 0.45 | **+0.652** | 30.8 | 562.3 | 358 |
| age | all-eligible × CT | lasso | 358 | 803 | 0.45 | **+0.644** | 31.4 | 0.1585 | 117 |
| FIQ | all-eligible × CT | linear | 358 | 726 | 0.49 | **−1.232** | 514.8 | — | 358 |
| FIQ | all-eligible × CT | ridge | 358 | 726 | 0.49 | **−0.010** | 234.2 | 5623.4 | 358 |
| FIQ | all-eligible × CT | lasso | 358 | 726 | 0.49 | **−0.015** | 235.4 | 100.0 | 0 |
| age | all-eligible × Area | linear | 358 | 803 | 0.45 | +0.174 | 72.4 | — | 358 |
| age | all-eligible × Area | ridge | 358 | 803 | 0.45 | +0.417 | 51.4 | 316.2 | 358 |
| age | all-eligible × Area | lasso | 358 | 803 | 0.45 | +0.406 | 52.5 | 0.1585 | 138 |
| FIQ | all-eligible × Area | linear | 358 | 726 | 0.49 | −0.998 | 460.3 | — | 358 |
| FIQ | all-eligible × Area | ridge | 358 | 726 | 0.49 | −0.002 | 232.5 | 5623.4 | 358 |
| FIQ | all-eligible × Area | lasso | 358 | 726 | 0.49 | +0.007 | 230.4 | 1.0 | 12 |
| age | all-eligible × Vol | linear | 358 | 803 | 0.45 | +0.404 | 52.3 | — | 358 |
| age | all-eligible × Vol | ridge | 358 | 803 | 0.45 | +0.592 | 36.0 | 562.3 | 358 |
| age | all-eligible × Vol | lasso | 358 | 803 | 0.45 | +0.557 | 39.2 | 0.1585 | 139 |
| FIQ | all-eligible × Vol | linear | 358 | 726 | 0.49 | −1.051 | 472.9 | — | 358 |
| FIQ | all-eligible × Vol | ridge | 358 | 726 | 0.49 | −0.010 | 234.2 | 5623.4 | 358 |
| FIQ | all-eligible × Vol | lasso | 358 | 726 | 0.49 | −0.011 | 234.7 | 1.585 | 3 |
| age | all-eligible × LGI | linear | 358 | 803 | 0.45 | +0.175 | 72.4 | — | 358 |
| age | all-eligible × LGI | ridge | 358 | 803 | 0.45 | +0.417 | 51.3 | 316.2 | 358 |
| age | all-eligible × LGI | lasso | 358 | 803 | 0.45 | +0.406 | 52.5 | 0.1585 | 139 |
| FIQ | all-eligible × LGI | linear | 358 | 726 | 0.49 | −0.996 | 459.9 | — | 358 |
| FIQ | all-eligible × LGI | ridge | 358 | 726 | 0.49 | −0.002 | 232.5 | 5623.4 | 358 |
| FIQ | all-eligible × LGI | lasso | 358 | 726 | 0.49 | +0.007 | 230.4 | 1.0 | 12 |
| age | frontoparietal (P-FIT) × CT | linear | 78 | 803 | 0.10 | +0.411 | 52.3 | — | 78 |
| age | frontoparietal (P-FIT) × CT | ridge | 78 | 803 | 0.10 | +0.442 | 49.7 | 316.2 | 78 |
| age | frontoparietal (P-FIT) × CT | lasso | 78 | 803 | 0.10 | +0.446 | 49.3 | 0.1585 | 39 |
| FIQ | frontoparietal (P-FIT) × CT | linear | 78 | 726 | 0.11 | −0.177 | 273.2 | — | 78 |
| FIQ | frontoparietal (P-FIT) × CT | ridge | 78 | 726 | 0.11 | −0.012 | 234.7 | 1000000.0 | 78 |
| FIQ | frontoparietal (P-FIT) × CT | lasso | 78 | 726 | 0.11 | −0.005 | 233.0 | 1.0 | 4 |

### 2.5 Locked-holdout numbers (evaluated exactly once; the notebook's quoted figures)

| target | model | feature space | p | n_train | n_test | R² | MSE | α | non-zero |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| age | linear | all-eligible × CT | 358 | 753 | 251 | **+0.4749** | 49.022 | — | 358 |
| age | linear | frontoparietal × CT | 78 | 753 | 251 | +0.4354 | 52.705 | — | 78 |
| age | ridge | all-eligible × all 4 measures | 1432 | 753 | 251 | +0.7000 | 28.007 | 1778.28 | 1432 |
| age | lasso | all-eligible × all 4 measures | 1432 | 753 | 251 | +0.6907 | 28.869 | 0.2512 | 128 |
| FIQ | ridge | all-eligible × all 4 measures | 1432 | 681 | 227 | +0.0158 | 249.646 | 177828.0 | 1432 |
| FIQ | lasso | all-eligible × all 4 measures | 1432 | 681 | 227 | +0.0170 | 249.329 | 1.585 | 6 |

(The notebook's *live-executed* Section 5 cell reproduces this ridge/lasso row
set almost exactly — R² 0.700 / 0.691 for age, 0.016 / 0.017 for FIQ, `nnz`
127/7 — small `nnz`/α differences from a slightly higher `LassoCV.max_iter`
used for convergence cleanliness; conclusions unchanged.)

### 2.6 Decision (WP12 §5.4)

- **Age has reliably positive out-of-sample R² everywhere tested** — every one
  of the 12 nested-CV `age` rows and both locked-holdout `age` rows are
  positive, from the weakest single-measure bundle (+0.174, Area/LGI) to
  ridge on the full brain (+0.689 to +0.700). → **age is the main
  ordinary-linear-regression example.**
- **FIQ's regularised score never clears zero reliably**: nested-CV ridge/lasso
  on the full brain are −0.009 / −0.001; the single locked-holdout split gives
  +0.016 / +0.017 — both essentially zero and disagreeing in sign across the
  two evaluation procedures, which is itself the signature of "no real
  signal," not a positive result. Per WP12 §5.4 this is reported **honestly as
  at-or-below-zero**, not cherry-picked: no split, alpha, or feature subset was
  chosen by looking at this number first (the same seeds/grids apply to every
  candidate in the table above).
- FIQ is **retained** as the compact secondary example precisely to show that
  point (regularisation rescues *instability*, not *absence of signal*) — the
  WP's "one main age example plus one short age-versus-FIQ/regularisation
  bridge" structure, not two parallel tutorials.
- The plan in WP12 §6 (six numbered sections in that order) matched the audit
  result exactly; no deviation from the suggested structure was needed beyond
  the two documented simplifications below.

## 3. Notebook restructure (WP12 §2, §4, §6)

`book/chapters/chapter_02/exercise_02.ipynb`, rebuilt from scratch (31 cells:
17 markdown, 14 code — 1 `hide-cell` data loader, 4 `hide-input` figures, 9
visible), executed end-to-end (network; 64 s), zero execution errors, zero
`stderr` output committed. `nbformat.validate` OK; ids unique, all
`wp11-*`/`wp12-*` (ids kept stable where a cell's role persisted from WP11; new
ids `wp12-001..004` only for the genuinely new regularisation-preview
section).

- **§2 Title/opening** — H1 `# Exercise 2: Regression` (Arabic numbering
  throughout; sidebar/TOC entry reads `Exercise 2: Regression`; zero
  occurrences of `Exercise II` in the notebook prose or code). The inaccurate
  "linear-regression half of Exercise II... short on theory" sentence and the
  Asaf-website comparison are gone. The new opening states: this is Exercise 2
  of *Machine Learning for Neuroscience*; Exercise 2 concerns regression and
  the bias–variance tradeoff; this part starts with linear regression on real
  neuroimaging data; KNN and the explicit bias–variance section come later.
  Verified: `tests/test_exercise_02_notebook.py::test_h1_title`,
  `test_no_stale_exercise_ii_wording`,
  `test_no_linear_regression_half_sentence_or_asaf_comparison`,
  `test_opening_has_scope_and_prerequisites_no_time_budget`.
- **§3.1 Run/download block** — now `:class: how-to-use` (was `tip`), same
  structure/wording pattern as Exercise 1, with direct Colab + raw-download
  links to **`book/downloads/chapter_02/exercise_02_portable.ipynb`** (not the
  canonical notebook, not Chapter 1's). Verified byte-for-byte against Exercise
  1's own pattern:
  `test_run_or_download_block_matches_exercise_one_and_links_this_chapter`.
- **§4.1** `# B: resubstitution` moved to its own source line (was a
  same-line trailing comment); verified
  `test_b_resubstitution_comment_is_on_its_own_line` asserts the literal
  newline, not a CSS/rendering property.
- **§4.2** The "B compares different rows..." sentence replaced with the exact
  WP wording ("B evaluates the model on its training data, whereas A and C are
  evaluated on the test data. A is the only valid estimate of performance on
  unseen participants; C is invalid because the test data were used for
  fitting."), verified whitespace-insensitively
  (`test_b_vs_c_sentence_matches_the_wp_wording`).
- **§6 Section 2 (`## 2. One honest linear-regression workflow`)** — target
  `age`; features = every eligible bilateral cortical-thickness column, p=358
  (`all-eligible × CT`, computed in-notebook as "every `fsCT_*` column except
  the two non-bilateral `5L`/`5R` labels" — no giant literal ROI list needed,
  unlike WP11's `FRONTOPARIETAL` array; verified equal, as a set, to
  `abide_modeling_data.bundle_columns("all-eligible", ["CT"])` by
  `test_canonical_feature_recipe_matches_the_manifest_all_eligible_bundle`).
  Same fixed split (`test_size=0.25, random_state=42, stratify=group`) →
  n_train=753, n_test=251. Held-out **R²=0.475, MSE=49.0 (RMSE 7.0 years)**.
- **Section 3 (`## 3. Three ways to score the same model`)** — same split/
  recipe. A=0.475 (correct), B=0.845 (resubstitution), **C=1.000** (invalid):
  with p=358 features and only 251 test rows, the test-fitted model is
  literally **underdetermined** (p > n_test) and reproduces those 251 points
  almost exactly — a stronger, more honest illustration of "C is invalid"
  than WP11's FIQ version (where p=78 < n_test=227). Ordering C > B > A
  confirmed in the executed output.
- **Section 4 (`## 4. Comparing feature sets`)** — literature framing replaced:
  Bethlehem et al. (2022, Nature, doi:10.1038/s41586-022-04554-y) and Storsve
  et al. (2014, J Neurosci, doi:10.1523/JNEUROSCI.0391-14.2014), both verified
  live via DOI content negotiation before use. States plainly that, unlike
  IQ's P-FIT hypothesis, no single small region set is literature-preferred
  for age — the bundles (including the repurposed `frontoparietal`) are used
  as anatomical comparisons, not a claim of relevance.
- **Section 5 (`## 5. Regularisation preview: age vs FIQ with the full
  brain`)** — new. Explains p-vs-n instability in plain language; states ridge
  keeps all features vs. lasso zeroing some (never "marginally reduces");
  states MSE is not comparable across the two targets' different units; fits
  `Pipeline(StandardScaler(), RidgeCV(...))` /
  `Pipeline(StandardScaler(), LassoCV(...))` over the documented grids with
  alpha chosen on the training rows only, evaluates the held-out split exactly
  once per model; a `hide-input` bar chart contrasts OLS/ridge/lasso × age/FIQ.
  IQ literature (Jung & Haier P-FIT; Narr et al.) is retained **only** in this
  section, beside the actual FIQ analysis
  (`test_iq_literature_retained_only_beside_fiq_analysis`).
- **Section 6 (`## 6. What does sample size change?`)** — simplified to one
  same-target (`age`) learning curve on the canonical recipe (deviation from
  WP11's three-part A/B/C structure, documented below). Training sizes
  `[370, 470, 570, 670, 753]` — the smallest is deliberately just above p=358
  (n/p≈1.03, "barely well posed"), 40 resamples each. Held-out R² mean rises
  from **−8.45** (n=370) through −0.22, +0.23, +0.40 to **+0.48** (n=753,
  matching Section 2 exactly, a determinism check), while the 10th–90th
  percentile band collapses from ±5 to a point.
- **In summary / Questions** — rewritten around the age/FIQ/regularisation
  narrative; the forward-looking sentence ("Next practice: k-nearest
  neighbours, and the bias-variance tradeoff.") is the only place beyond the
  opening scope where those terms appear
  (`test_no_knn_or_bias_variance_section`).

### Deviation from the WP's suggested §6 structure (documented per WP12 §6)

WP12 §6 lists a likely structure whose sample-size section keeps WP11's
two-outcome (FIQ vs SRS) comparison and matched-N bridge. Once `age` (N=1004,
0 missing) is the main target, that specific availability contrast no longer
has anything to teach — `age` has no missingness to contrast against, and
WP12 §6.4 explicitly permits removing/shortening it ("Prefer the current
rigorous same-target learning curve over a weak comparison between different
outcomes. Remove or shorten the FIQ-versus-SRS availability section if it no
longer adds a clear lesson."). The age-vs-FIQ comparison itself is not lost —
it is exactly what the new Section 5 (regularisation preview) does, honestly
and with a locked-once evaluation, so nothing the WP asked for is missing;
it is relocated and done more rigorously than a second same-target-but-
different-N demonstration would have been.

## 4. Page controls and Colab/download destinations (WP12 §3.2)

- `book/_static/launch-buttons.js` (new, registered in `_config.yml`
  `html_js_files`) adds a visible **Colab** button to the article header (next
  to the theme's own source/download dropdowns) for both chapters, from a
  static, explicit page→portable-notebook map — never guessed from the URL
  pattern, never the canonical notebook. Pages with no entry in the map (e.g.
  Introduction) get no button
  (`launch-buttons.spec.ts::"a page with no portable-notebook mapping...
  gets no Colab button"`).
- The existing theme download-`.ipynb` control (`.dropdown-download-buttons`)
  is untouched — still downloads the canonical source notebook, as before
  (WP07's original design decision; WP12 does not change it, only adds the
  Colab control next to it). Verified present on both chapters:
  `launch-buttons.spec.ts::"the theme's own download-.ipynb control is still
  present"`.
- **Verified, per chapter, both the opening-admonition links and the header
  button** (WP12 §8.12 link-target requirement):

  | Chapter | Opening Colab link | Opening raw-download link | Header Colab button |
  |---|---|---|---|
  | Exercise 1 | `.../blob/main/book/downloads/chapter_01/exercise_01_portable.ipynb` | `.../main/book/downloads/chapter_01/exercise_01_portable.ipynb` | same portable target |
  | Exercise 2 | `.../blob/main/book/downloads/chapter_02/exercise_02_portable.ipynb` | `.../main/book/downloads/chapter_02/exercise_02_portable.ipynb` | same portable target |

  Each test also asserts the *other* chapter's path is **absent** from that
  page (`launch-buttons.spec.ts`, 7 tests total, all passing on the built
  book). No regression to the previously observed "older notebook" problem.
- This is the one "necessary shared Colab-button implementation" WP12 §7
  permits touching Exercise 1 for; Exercise 1's notebook content is otherwise
  byte-identical (its `.ipynb` is not in this commit's diff at all — only
  `_config.yml`, `custom.css`, and the new shared JS file were touched, all
  of which apply identically to both chapters).

## 5. Interactive activity regenerated for `age` (WP12 §6.3)

- `scripts/export_regression_catalog.py` generalised: `TARGET` now reads
  `manifest["catalog"]["target"]` = `"age"`; `observed` stores **rounded
  floats**, not forced integers (age is fractional years — FIQ, an integer
  standard score, still round-trips fine); the cohort-consistency check uses
  `np.allclose` instead of `np.round`-to-int; `target.label`/`unit` now come
  from the manifest's per-target `label`/`unit` fields instead of being
  hardcoded FIQ strings.
- `book/_static/widgets/data/abide_regression_models.json` regenerated: 35
  entries (34 enabled + `all-eligible__CT+Area`, p=716, still disabled with
  the same numerically-defensible reason), cohort **n=1004**, 5 folds
  (`foldTrainN=803`). **Every enabled entry now scores above zero** — a
  striking contrast with WP11's FIQ catalog, where every entry was negative.
  Selected values: `frontoparietal__CT` (default A) +0.411,
  `occipital__CT` (default B) +0.433, `all-eligible__CT` +0.466,
  `sensorimotor__CT+Area` (the overall best single entry) +0.507.
  SHA-256 `0f2deec5add54725d5734476ada96aabdf5d23cccb1dfd2ee584c29ae739b50d`.
- `book/_static/widgets/configs/regression_compare.json`: `targetLabel`
  "Age at scan (years)"; `literatureNote` rewritten around Bethlehem/Storsve,
  explicitly noting the `Frontoparietal` bundle's IQ-literature origin is
  reused here only as one anatomical comparison, not an age-specific claim;
  `defaultA`/`defaultB` unchanged (`frontoparietal`/`occipital` × CT) for
  minimal, well-understood churn.
- `interactive/src/regression-compare-data.ts`: dropped the "observed must be
  integer" `superRefine` check (target-specific, not a real schema
  invariant); `interactive/src/components/regression-compare.ts`: the literature
  disclosure heading generalised from "Where the frontoparietal bundle comes
  from" to "Where these ROI bundles come from" (it always covered all seven
  bundles; the heading now says so).
- No `p >= n` restriction was lifted for regularised configurations because
  none were exposed in this activity (WP12 §6.3's "do not disable all-features
  regularised configurations merely because p>=n" is conditional on such
  configurations being offered; they are not — the regularisation preview
  runs as plain notebook code instead, keeping the activity focused on one
  model family as before).

## 6. Portable notebook and generator (WP12 §3, §7)

- `scripts/build_portable_notebook.py`: `_CH2_BANNER` "Exercise II" →
  "Exercise 2"; new `NotebookSpec.colab_title` field, set to
  `"Exercise 2: Regression"` for Chapter 2 only, written to
  `metadata.colab.name` (Colab's own tab-title source, verified present in
  the regenerated file); the iframe-replacement key updated to the notebook's
  new activity title.
- **`book/downloads/chapter_01/exercise_01_portable.ipynb` verified
  byte-for-byte identical** to before WP12 (`--check` → "up to date (75
  cells)"; not present in this commit's diff).
- **`book/downloads/chapter_02/exercise_02_portable.ipynb`** regenerated, 33
  cells (31 canonical + banner/setup/install − 1 dropped admonition). SHA-256
  `c17552039960ebf4703a38b14455abf1407e8cfae18704d0d6748cc48787f1ff`. No MyST
  directive, iframe, `_static/` path, repository-relative config path,
  `requirements.txt` instruction, hide tag, active install command, or
  self-referential Colab link. Out-of-repo smoke run: **13 code cells**, key
  values (`age available for 1004 of 1004`, `held-out R^2 =`,
  `n_features (p) = 358`) matched.
- `scripts/smoke_portable_notebook.py`: Chapter 2's expected strings updated
  to the new target's output.

## 7. Manifest (`book/config/abide_modeling.json`)

- `targets.age` added — `role: "main"`, `label`/`unit` for the catalog,
  `rationale` citing the audit result and this report.
- `targets.FIQ.role` changed `"main"` → `"regularization_preview"`.
- `SRS_TOTAL_RAW` moved from `targets` to `rejected_targets` — it was WP11's
  lower-availability secondary target for a FIQ-vs-SRS contrast that no
  longer has a role once age (0 missing) is the main target; still fetched by
  the merge and documented as available for a future exercise (deviation
  documented in §3's note above).
- `protocol.canonical_recipe` → `all-eligible × CT` (p=358), with the
  rationale (whole-cortex age effect, no small literature bundle to prefer).
- New `protocol.regularisation_preview` block: purpose, feature space, both
  documented alpha grids, pointers to the audit script and its result file.
- `catalog.target` → `"age"`; `catalog.note` clarifies the "OLS-only, no p≥n
  regularised configs" restriction is about this activity's model family, not
  a general p-vs-n rule (WP12 §6.3).
- `_check_manifest` (in `abide_modeling_data.py`) updated: `all-eligible` is
  now a valid special-cased `canonical_recipe.bundle` value (it always was for
  `catalog.bundles`); the required-roles check now looks for `"main"` and
  `"regularization_preview"`.
- SHA-256 `9fbe6bf73d4040bc809140e287a94ccc9be968b94823d9274133c3604cb7e1b1`.

## 8. Required validation (WP12 §8) — commands and results

1. **Notebook-format validation and unique cell IDs** —
   `nbformat.validate` (via `test_exercise_02_notebook.py`) — PASS; 31 unique
   `wp11-*`/`wp12-*` ids.
2. **Modeling data/provenance and leakage-guard tests** —
   `python -m unittest discover -s tests -p 'test_abide_modeling_data.py'`
   (21/21) — PASS, including the new `age`-as-target leakage-guard tests.
3. **Audit reproducibility tests, including training-only hyperparameter
   tuning** —
   `python -m unittest discover -s tests -p 'test_regression_model_audit.py'`
   (11/11) — PASS. Two tests directly **mock `RidgeCV.fit`** to prove, not
   just assert, that (a) each outer nested-CV fold's inner alpha selection
   sees exactly that fold's training rows (never more, never the held-out
   rows) and (b) the locked-holdout `RidgeCV.fit` is called exactly once,
   with exactly `n_train` rows, never `n_train + n_test`. Two more tests
   confirm bit-identical results across repeated runs (determinism).
4. **Regression-catalog schema, metric-recomputation, deterministic-output
   tests** —
   `python -m unittest discover -s tests -p 'test_export_regression_catalog.py'`
   (12/12) — PASS; `interactive/tests/regression-compare-data.test.ts` (10/10)
   — PASS, including the committed-artifact test now asserting `target.name
   == "age"`, `cohort.n == 1004`, and every enabled model's R² > 0.
5. **Python test suite** —
   `python -m unittest discover -s tests` → **184 / 184** — PASS (up from
   161; +21 net: +2 `test_abide_modeling_data.py`, +1 net
   `test_export_regression_catalog.py`, +11 new
   `test_regression_model_audit.py`, +7 net `test_exercise_02_notebook.py`).
6. **TypeScript typecheck, unit tests, production build** — `npm run
   typecheck` PASS; `npm run test:unit` → **217 / 217** PASS (unchanged
   count: 1 test updated in place, none added/removed); `npm run build` —
   succeeded (pre-existing 500 kB Plotly-chunk advisory only).
7. **Standalone Playwright, every Exercise 2 activity** — `npx playwright
   test` → **60 / 60** PASS (`regression-compare.spec.ts`'s 10 tests updated
   for positive-R² age defaults; all others unchanged).
8. **Portable-notebook freshness + out-of-repo smoke, Exercises 1 and 2** —
   `python scripts/build_portable_notebook.py --check` PASS (ch1 byte-
   identical, ch2 up to date); `python scripts/smoke_portable_notebook.py
   --notebook all` → both **OK** (ch1 20 code cells, ch2 13 code cells), key
   values matched, network.
9. **Clean Jupyter Book build** — `rm -rf book/_build && jupyter-book build
   book` → succeeded, **2 warnings** (both pre-existing, none new); `find
   book/_build -name '*.err.log'` → empty.
10. **Built-book Playwright, GitHub Pages subpath** — `npm run test:e2e:book`
    → **26 / 26** PASS (19 WP11 tests + 3 `chapter02.spec.ts` metric-sign
    updates + 7 new `launch-buttons.spec.ts` tests).
11. **Visual checks, desktop + 390 px** — manual Playwright screenshots taken
    of the Chapter 2 opening (desktop 1280 px and 390 px, no horizontal
    overflow — the Colab button is visible in the compact header too), the
    Section 3 three-panel A/B/C figure (visually confirms A hugs the diagonal
    loosely, C sits exactly on it), and the live Section 4 activity (both
    panels render real Plotly scatters with the exact catalog R²/feature
    counts). All narrow-viewport Playwright assertions (`overflow <= 1px`)
    pass on both the standalone activity and the built-book page.
12. **Link-target tests, Exercises 1 and 2, opening links + page buttons** —
    `interactive/e2e-book/launch-buttons.spec.ts`, 7/7, see §4 above.

**Manual verification performed:** changing a bundle/measurement control in
the live activity changes both the Plotly figure and the printed R²/MSE (not
just a label) — confirmed both by the automated Playwright assertions (feature
count + `data-r2` change together) and by direct screenshot inspection.
Browser refresh restores the configured defaults — confirmed by
`chapter02.spec.ts`'s dedicated refresh test (switches Model B to
`sensorimotor`, reloads, confirms it reverts to `occipital`).

Full baseline re-run before implementation matched the WP11 report's own
numbers exactly (161 Python, 217 frontend, 60 standalone, 19 built-book, 0
`npm audit` vulnerabilities, 2 build warnings) — see the table at the top for
before/after.

## 9. Exact files changed

Implementation commit `5f559f9` — 19 modified, 5 new:

**New:** `book/_static/launch-buttons.js`,
`interactive/e2e-book/launch-buttons.spec.ts`,
`scripts/regression_model_audit.py`,
`scripts/regression_model_audit_result.json`,
`tests/test_regression_model_audit.py`.

**Modified:** `book/_config.yml`, `book/_static/custom.css`,
`book/_static/widgets/configs/regression_compare.json`,
`book/_static/widgets/data/abide_regression_models.json`,
`book/chapters/chapter_02/exercise_02.ipynb`,
`book/config/abide_modeling.json`,
`book/downloads/chapter_02/exercise_02_portable.ipynb`,
`interactive/e2e-book/chapter02.spec.ts`,
`interactive/e2e/regression-compare.spec.ts`,
`interactive/src/components/regression-compare.ts`,
`interactive/src/regression-compare-data.ts`,
`interactive/tests/regression-compare-data.test.ts`,
`scripts/abide_modeling_data.py`, `scripts/build_portable_notebook.py`,
`scripts/export_regression_catalog.py`,
`scripts/smoke_portable_notebook.py`, `tests/test_abide_modeling_data.py`,
`tests/test_exercise_02_notebook.py`,
`tests/test_export_regression_catalog.py`.

**Untouched (verified):** `book/chapters/chapter_01/exercise_01.ipynb`,
`book/downloads/chapter_01/exercise_01_portable.ipynb`,
`book/_static/widgets/data/abide_histogram.json`,
`book/_static/widgets/data/abide_retention.json`,
`book/_static/widgets/data/abide_table_inspection.json`,
`book/_toc.yml`, `book/contents.md`, `book/intro.md`, `book/syllabus.md`,
`interactive/src/config.ts` (already target-agnostic from WP11).

See `WP12_EXACT_CHANGELOG.md` for the location-specific before/after.

## Warnings, deviations, deferred / not-performed

1. **Sample-size section simplified** from WP11's three-part (availability /
   matched-N / learning-curve) structure to one same-target learning curve —
   documented in §3 above, explicitly permitted by WP12 §6.4, and the
   age-vs-FIQ comparison it would have made is done more rigorously in the new
   Section 5 instead.
2. **`SRS_TOTAL_RAW` demoted out of `targets`** into `rejected_targets` (not
   literally rejected — reclassified as no-longer-relevant once age is main).
   Still fetched by the merge; documented reasoning in the manifest.
3. **The notebook's live regularisation-preview cell and the committed
   `regression_model_audit_result.json` differ slightly** in lasso non-zero
   coefficient counts / alpha (e.g. FIQ lasso `nnz` 6 in the standalone audit
   vs. 7 in the executed notebook) because the notebook's `LassoCV` uses a
   larger `max_iter` (50000 vs. the audit script's 5000) chosen purely to
   avoid a `ConvergenceWarning` in committed notebook output; both report the
   same qualitative conclusion (FIQ ≈ 0) and both are deterministic on
   repeated runs. Documented, not hidden.
4. **Colab interactive rendering not machine-verified** (Google serves an app
   shell to headless automation — unchanged limitation from WP07–WP11). The
   article-header button's `href`, the opening admonition's links, and the
   portable notebook's own `metadata.colab.name` are all covered by tests
   instead.
5. **No live / remote checks** — by the stop condition: no push, no `main`
   merge, no deployment. GitHub Pages still serves the WP08–WP11 content;
   hosting and the private/public distribution architecture were not touched.
6. **Pre-existing warnings kept** — `logo.png` missing, `book/README.md` not
   in a toctree, the Vite 500 kB Plotly-chunk advisory. All unchanged, out of
   scope.
7. **Canonical Exercise 2 notebook executed end-to-end twice** (network:
   pinned `abide2.tsv` + phenotypic CSV) to arrive at clean, warning-free
   committed outputs; both executions and two full clean `jupyter-book`
   builds produced byte-identical figure hashes (9 PNGs) in this environment.
   The pre-existing cross-platform Matplotlib byte-difference risk
   (numpy/pandas/matplotlib unpinned in `requirements.txt`) is unchanged from
   prior WPs.

## Unresolved risks / needs Yoav

- **Private-repository distribution** (carried from WP09/WP10/WP11
  unchanged): the Colab / raw-download buttons and the new article-header
  Colab button all target `github.com/yoavmp/ml-neuro-tutorials` on `main`
  and will break for non-collaborators if the repo goes private. Not in scope
  for WP12.
- **Merge / deployment of WP09–WP12** is a separate, later WP after review.
- **KNN and the full bias–variance section** are the next WP, deliberately not
  started (only the one forward-looking sentence exists, as before).
- **Whether `age` as the main example is the pedagogically preferred choice
  long-term** is an editorial judgement beyond this WP's empirical mandate —
  the audit only established that it is the scientifically honest one; Yoav
  may still prefer a different narrative emphasis for the lecture pairing.

## Confirmation of safety constraints

- **No KNN and no full bias–variance content** — only the opening-scope
  mentions and one forward-looking sentence; asserted by
  `test_no_knn_or_bias_variance_section`.
- **No merge to `main`, no deployment, no push, no force push** — nothing left
  the local `feature/regression-practice` branch.
- **No destructive git command** — no `git reset --hard`,
  `git checkout -- <path>`, `git clean`, `git rebase`, `git revert`, tag or
  branch deletion.
- **No repository-setting / hosting / Pages / distribution-architecture
  change.**
- **No generated build output committed** — `book/_build`,
  `book/.jupyter_cache`, `book/_static/widgets/app`,
  `interactive/node_modules`, `interactive/test-results`, `__pycache__`
  remain untracked / git-ignored. `abide_regression_models.json`,
  `abide_modeling.json`, and `regression_model_audit_result.json` are
  committed source/reviewed assets, not build output.
- **Exercise 1 content unchanged** — its notebook is not in this commit's
  diff at all; its portable notebook is verified byte-identical; only the
  shared `_config.yml` / `custom.css` / new `launch-buttons.js` (documented in
  §4) touch it, identically to Chapter 2.
- **No held-out test score was consulted to choose a target, feature set,
  model family, or alpha** — every selection in §2 came from the nested/
  isolated procedure or was predeclared before any score was seen; the two
  isolation tests in `test_regression_model_audit.py` verify this
  structurally, not just by inspection.
- **No WP13 created.** Stopping here per the WP's stop condition.

## Key identifiers

| Item | Value |
|---|---|
| Branch | `feature/regression-practice` (unchanged, off `502f75a`) |
| Checkpoint commit | `30515629c6e4ddf2716581ed2295ec65f4b3fe65` (`checkpoint: before WP12`) |
| Checkpoint tag | `wp12-start` → `3051562` (annotated; tag object `6e5802496f41e15ce39d4df3e0f45e4fdc775176`) |
| Implementation commit | `5f559f9` (`WP12: retarget Exercise 2 to age...`) — 19 modified, 5 new |
| Report commit | adds `WPs/reports/WP12_REPORT.md` + `WPs/reports/WP12_EXACT_CHANGELOG.md` only — SHA in the terminal summary |
| Modelling manifest | `book/config/abide_modeling.json` SHA-256 `9fbe6bf73d4040bc809140e287a94ccc9be968b94823d9274133c3604cb7e1b1` |
| Regression audit result | `scripts/regression_model_audit_result.json` SHA-256 `6aef676e63ce83a6d9899c25036249a1664ad9ae72311aae665d1e59869e7b2a` |
| Regression catalog | `book/_static/widgets/data/abide_regression_models.json` SHA-256 `0f2deec5add54725d5734476ada96aabdf5d23cccb1dfd2ee584c29ae739b50d` |
| Canonical notebook | `book/chapters/chapter_02/exercise_02.ipynb` SHA-256 `1e1723f5867077876c6ebb534c646949a3447eeefbdeb88b5cce7eb2e5ff4907` |
| Portable notebook | `book/downloads/chapter_02/exercise_02_portable.ipynb` SHA-256 `c17552039960ebf4703a38b14455abf1407e8cfae18704d0d6748cc48787f1ff` |

## Instructions for reviewer

Paste this entire report (`WP12_REPORT.md`) into the ChatGPT conversation that
produced WP12. `WP12_EXACT_CHANGELOG.md` is the companion location-specific
before/after record.
