# WP11 implementation report — Exercise II, linear regression

## Outcome

Status: **SUCCESS**

The complete linear-regression portion of Exercise II is implemented, executed,
and tested: a deterministic merged ABIDE-II brain+phenotype modelling table, a
new Chapter 2 notebook (`book/chapters/chapter_02/exercise_02.ipynb`), a new
browser-native feature-set comparison activity (`regression-compare`), a
pre-computed model catalog, a portable notebook, navigation, and targeted tests
across all four suites. No KNN or bias–variance section was added. No merge,
deployment, push, hosting change, private/public distribution change,
destructive git command, history rewrite, or generated build-output commit
occurred.

| Check | Before WP11 | After WP11 |
|---|---|---|
| Frontend typecheck | PASS | PASS |
| Frontend unit (`vitest`) | 187 / 187 | **217 / 217** |
| `npm audit --omit=dev` | 0 vulnerabilities | 0 vulnerabilities |
| Widget artifact `export_widget_data.py --check --artifact all` | 3 valid + canonical | 3 valid + canonical (unchanged) |
| Regression catalog `export_regression_catalog.py --check` | (new) | **valid + canonical** |
| Modelling manifest `abide_modeling_data.py --check` | (new) | **self-consistent** |
| Python unit (`unittest discover -s tests`) | 114 / 114 | **161 / 161** |
| Portable notebook `--check` | up to date (ch1: 75) | up to date (**ch1: 75, ch2: 37**) |
| Portable smoke (out of repo, network) | ch1: 20 code cells | **ch1: 20, ch2: 15 code cells**, key values matched |
| Standalone Playwright | 50 / 50 | **60 / 60** |
| Clean Jupyter Book build | succeeded, 2 warnings | succeeded, **2 warnings** (same two pre-existing) |
| `*.err.log` guard | empty | empty |
| Built-book Playwright | 16 / 16 | **19 / 19** |
| 2× consecutive clean builds, deterministic figures | identical (5 PNGs) | **identical (9 PNGs)** |

The two build warnings are the pre-existing `logo file 'logo.png' does not
exist` and `book/README.md: document isn't included in any toctree`. No new
warning was introduced.

## 1. Branch, checkpoint, baseline (WP11 §1)

- Confirmed `feature/course-pages-and-eda-trim` HEAD was `502f75a`
  (`WP10 report: …`) with a clean tree apart from the untracked WP11 brief.
- New branch **`feature/regression-practice`** created from that exact HEAD.
- **Checkpoint commit `7b6986433474d5173062dd4c6d4290c0a373acd9`**
  (`checkpoint: before WP11`) — adds `WPs/WP11_NOTEBOOK2_LINEAR_REGRESSION.md`
  only (1 file, +569).
- **Annotated tag `wp11-start`** → `7b69864` (tag object
  `8ccadfb16be461643ab9fc782be6a47b3b8ed664`). The name was free; no numeric
  suffix needed.
- The full WP10 baseline was run **before** any implementation change and is the
  "Before WP11" column above (matches the WP10 report).
- No `git reset --hard`, `git checkout -- <path>`, `git clean`, `git rebase`,
  `git revert`, history rewrite, force-push, tag/branch deletion at any point.

## 2. Data audit (WP11 §2) — SUCCESS

### The brain-feature table is confidently identified

`abide2.tsv` from the NeuroHackademy 2020 curriculum, Tal Yarkoni ML tutorial
(`tu-machine-learning-yarkoni/data/`), pinned to the **same immutable commit
Exercise I already uses**, `e4eed3c4daa7f40b0ba931182a8c7e5e691dba6b`
(verified byte-identical to the data-add commit `8a288018…`).

| Item | Value |
|---|---|
| Brain table | `abide2.tsv`, SHA-256 `ad0db42f85c77cbb8b4e023df288d34b29f1a63870a0cf1955c5b3b0d357579e`, TSV |
| ROI-id sidecar | `columns_id_360.txt`, SHA-256 `dede125bf6ffa9f059e8123469f96e4b23c2282ec7f8d3bbf54048f366726315` |
| Phenotype table | `abide2_phenotypic.csv`, SHA-256 `537e541114884f63a2e736ba4d223a816dd013f701e56fb223ebe42e219e06f6` (the same file / hash Exercise I pins) |
| Licence | CC-BY-4.0 (repo `LICENSE.md`; the tutorial folder adds no separate licence). ABIDE-II governance applies upstream. Redistribution is avoided anyway: the notebook downloads at runtime from the pinned URLs, and the browser artifact contains only aggregate metrics/coordinates, no raw features and no identifiers. |
| ABIDE generation | **ABIDE-II** (every `site` value is `ABIDEII-*`). |
| Row / participant count | **1004 rows, 1004 unique `subject` ids, 0 duplicates.** Identifier field: `subject` (integer). |
| Non-brain columns | `site, subject, age, age_resid, sex, group` — **no IQ / test-score column of any kind**. Yarkoni's own tutorial predicts `age`. |
| Brain-feature count | **1440** = 4 FreeSurfer measures × 360 ROIs. |
| Atlas / parcellation | **HCP-MMP1.0 (Glasser et al. 2016, doi:10.1038/nature18933)**, 360 parcels (180/hemisphere), `_ROI` suffix. |
| Column naming | `fs<measure>_<hemi>_<roi>_ROI`, e.g. `fsCT_L_46_ROI`. Regex `^fs(CT\|Area\|Vol\|LGI)_(L\|R)_(.+)_ROI$`. 181 distinct ROI base tokens (179 bilateral + `5L` L-only + `5R` R-only). |
| Measurement types | `fsCT` cortical thickness (mm), `fsArea` surface area (mm²), `fsVol` grey-matter volume (mm³), `fsLGI` local gyrification index (unitless). |
| Hemisphere encoding | single `L` / `R` after the measurement prefix. |
| Missingness in brain features | **zero** (0 of 1004×1440 cells). |
| Sites | 17: KKI_1 (206), GU_1 (103), OHSU_1 (92), NYU_1 (73), BNI_1 (58), SDSU_1 (55), EMC_1 (53), IP_1 (52), ONRC_2 (46), TCD_1 (41), IU_1 (39), ETH_1 (36), USM_1 (33), UCD_1 (32), UCLA_1 (32), KUL_3 (27), NYU_2 (26). |
| Diagnostic groups | `group` 1 = autism (463), 2 = control (541). `sex` 1 = male (765), 2 = female (239). `age` 5.13–64.0 yr. |
| Preprocessing already applied | FreeSurfer surface metrics summarised per HCP-MMP1 parcel; no further normalisation in `abide2.tsv`. `age_resid` is an age variable residualised on site (a Yarkoni teaching column) — **not used** as a feature or target here. |

### The modelling table is a documented join, not a substitution

`abide2.tsv` has no cognitive score, so the "phenotype-plus-regional-neuroimaging
table" the WP describes does not exist as one file. **Decision, taken with the
user before implementation:** deterministically merge `abide2.tsv` (brain +
`age`/`sex`/`group`/`site`) with `abide2_phenotypic.csv` (FIQ, VIQ, PIQ, SRS,
ADOS, ADI-R) on `subject == SUB_ID`. Both files come from the same pinned Yarkoni
directory and the same study (ABIDE-II). All 1004 brain-table participants are
present in the phenotypic file (0 unmatched). The merged modelling table is
**1004 rows**.

### Deterministic parser / manifest

- **`book/config/abide_modeling.json`** — the reviewed manifest: source pins +
  hashes, atlas metadata + the full 181-label ROI inventory, the 4 measures, the
  identifier / non-brain / target column lists, 6 anatomical ROI bundles
  (explicit Glasser label lists), the leakage guard (exact list + pattern), the
  split / CV protocol, the canonical recipe, and the catalog definition.
- **`scripts/abide_modeling_data.py`** — the only place brain-column string
  parsing lives: `parse_brain_column` (raises with an actionable message on any
  malformed name, unknown ROI, or wrong hemisphere for `5L`/`5R`),
  `classify_columns`, `bundle_columns` (bilateral, ordered, validated),
  `feature_matrix` + `assert_brain_only` (the leakage guard — every X column must
  match the atlas pattern and name a real ROI; nothing else can enter X), and
  `--audit` / `--check` CLI modes.

### Leakage guard (WP11 §2)

`assert_brain_only` refuses: the target itself, `VIQ`/`PIQ`/`FIQ`, `DX_GROUP` /
`group`, `age` / `AGE_AT_SCAN`, `sex` / `SEX`, `site` / `SITE_ID`,
`subject` / `SUB_ID`, `HANDEDNESS_CATEGORY`, `CURRENT_MED_STATUS`, and anything
matching the identifier/phenotype pattern. `tests/test_abide_modeling_data.py`
and `tests/test_export_regression_catalog.py` assert the feature set cannot
contain target or phenotype leakage; the browser data-schema test asserts the
artifact has no identifier-shaped key.

## 3. Targets (WP11 §3)

### Main target: FIQ (deviation from "just use it if available" — documented)

`FIQ` is not in the brain table; it is merged in. Among the 1004 participants
with usable brain data:

| Target | usable N | miss | range | mean | sd | structural note |
|---|---|---|---|---|---|---|
| `FIQ` | **908** | 96 | 49–149 | 111.1 | 15.3 | present at 16/17 sites; missing entirely only at EMC_1 (n=53); autism 423 / control 485 |
| `SRS_TOTAL_RAW` | **764** | 240 | 0–199 | 54.8 | 42.7 | present at 13/17 sites; both groups (autism 364 / control 400) |
| `VIQ` | 707 | — | — | — | — | IQ subscale — leakage-adjacent to FIQ |
| `PIQ` | 779 | — | — | — | — | IQ subscale — leakage-adjacent to FIQ |
| `ADOS_G_TOTAL` | 306 | — | — | — | — | ~87% autism; near-absent at several sites — **rejected** |
| `ADI_R_SOCIAL_TOTAL_A` | 285 | — | — | — | — | 0 controls; autism-only instrument — **rejected** |
| `age` | 1004 | 0 | 5.1–64 | 15.1 | 9.4 | strongly predictable (held-out R² ≈ 0.45) but whole-brain, no regional literature bundle — **not chosen** |

**Main target = `FIQ`.** Rationale: highest availability of any cognitive score
after requiring brain data; it is the score the Exercise II literature framing
(P-FIT, Narr et al.) is *about*; and it produces a richer, more honest lesson
(see §5–§7). This is a deviation from the WP's "prefer FIQ if available" only in
that a join was required to obtain it — reported here and in the changelog per
the WP instruction, and pre-approved by the user, whose steer was: "join the
tables, pick a target at your judgement … good for the framing of our lesson,
and preferably have brain regions that are better predictive in literature."

**Lower-availability target = `SRS_TOTAL_RAW`** (n=764). The only continuous
behavioural score that is documented, not one-site, and present for both
diagnostic groups. The FIQ (908) vs SRS (764) contrast is **modest** and is
described as such in the notebook; ADOS_G_TOTAL and ADI_R_SOCIAL_TOTAL_A were
rejected for group/site confinement (WP11 §3 criteria). The rigorous sample-size
demonstrations (matched-N subsampling, learning curve) both run on FIQ alone.

### Literature-motivated anatomy (WP11 §3, §8) — citations verified

- **Jung RE, Haier RJ. The Parieto-Frontal Integration Theory (P-FIT) of
  intelligence: converging neuroimaging evidence. *Behav Brain Sci*.
  2007;30(2):135–154.** doi:10.1017/S0140525X07001185 (verified via DOI content
  negotiation).
- **Narr KL, Woods RP, Thompson PM, et al. Relationships between IQ and regional
  cortical gray matter thickness in healthy adults. *Cereb Cortex*.
  2007;17(9):2163–2171.** doi:10.1093/cercor/bhl125 (verified; published online
  2006-11-21, 2007 issue).

Six deterministic ROI bundles, defined **a priori** and stored in the manifest,
mapped to real Glasser labels (every label verified bilateral and present):

| Bundle | ROIs | Basis |
|---|---|---|
| `frontoparietal` | 39 | P-FIT core: DLPFC (9/46/45/44/47 subdivisions, IFJ/IFS), inferior + superior parietal (PG*, PF*, IP*, IPS1, LIP*, MIP, AIP, area 7), dorsal ACC (a32pr, p32pr, d32, 8BM, SCEF) |
| `frontal` | 21 | the prefrontal component only (DLPFC + dorsal ACC) |
| `parietal` | 21 | the parietal component only (IPL + IPS + SPL) |
| `temporal` | 18 | lateral / superior temporal — scoped comparison |
| `occipital` | 23 | primary + extrastriate visual — comparison |
| `sensorimotor` | 20 | primary + premotor / somatosensory — comparison |
| `all-eligible` | 358 | all 179 bilateral ROIs (5L/5R excluded) |

The bundle definitions are fixed in the manifest independently of any
performance number; `tests/test_abide_modeling_data.py` and
`tests/test_exercise_02_notebook.py` assert the notebook's embedded
frontoparietal list is byte-equal to the manifest.

## 4. Notebook and navigation (WP11 §4)

- **`book/chapters/chapter_02/exercise_02.ipynb`**, H1 `# Exercise II: Regression`,
  **35 cells** (21 markdown, 14 code: 9 visible, 4 `hide-input`, 1 `hide-cell`).
  Stable ids `wp11-001` … `wp11-061`. `nbformat.validate` OK; ids unique; only
  tags used are `hide-input` / `hide-cell`.
  - Opening: H1; a compact `{admonition} Run or download` (own cell, matching
    Exercise I); **What this notebook covers** (linear-regression only);
    concise **Prerequisites**. No course-Introduction repetition, no time
    budget.
  - Slight deviation: the WP prefers "roughly 35–50" canonical cells; the
    notebook is at the low end (35) because the lecture-first structure and the
    "no definition-only sections" rule leave little to add without padding.
- `book/_toc.yml`: `chapters/chapter_02/exercise_02` added after
  `chapters/chapter_01/exercise_01` under `contents`. Order preserved:
  Introduction → Syllabus → Contents → Exercise I → Exercise II (verified in the
  built HTML sidebar and prev/next chain). `book/contents.md` uses
  `{tableofcontents}` and picks the new page up automatically — no edit needed.
- Design: the existing rust/cream style, `{admonition}` "Think first" cards and
  `{dropdown}` "Check your reasoning" blocks, matching Exercise I.

## 5. Section 1 — the wide modelling table (WP11 §5) — SUCCESS

`## 1. The modelling table`. Explains one row = one participant, phenotype vs
brain vs identifier columns, region+hemisphere encoding, and that this is a
modelling table, not the Exercise I EDA table. Shows: `model_df.shape`
(`1004 × 1452`), a **compact preview** (6 phenotype columns + 3 representative
brain columns, `head(4)`), and a count summary (10 phenotype columns, 1440 brain
features = 4 measures × 181 region-hemispheres, 0 missing brain cells, FIQ
available for 908/1004). No full wide dataframe is printed. One **Think first**
card (outcome / features / participant / measurement types / ROI encoding) with
a `Check your reasoning` dropdown. The data-loading cell is `hide-cell` in the
book, visible+runnable in the portable notebook, and is plain self-contained
Python (two pinned HTTPS URLs, `pandas.merge`) — no repository dependency.

## 6. Section 2 — one honest workflow (WP11 §6) — SUCCESS

`## 2. One honest linear-regression workflow`. **Pre-declared compact recipe:**
bilateral cortical thickness (`fsCT`) over the 39-region frontoparietal bundle
= **78 features** (n/p ≈ 8.7 for the training set). Chosen a priori from the
intelligence literature, explicitly *not* because it scores well (it does not —
see §8).

Steps, in readable visible cells: (1–2) build brain-only `X` and `y = FIQ`, drop
rows with no FIQ; (3) one fixed split `train_test_split(test_size=0.25,
random_state=42, stratify=group)` → **n_train = 681, n_test = 227**; (4–5)
`make_pipeline(StandardScaler(), LinearRegression())` fitted on training rows
only (no imputation — brain features have no missing values); (6–7) predict the
untouched test rows, compute held-out **R² = −0.120**, **MSE = 284.0** (RMSE
16.9 IQ points); (8, `hide-input`) observed-vs-predicted scatter with the
perfect-prediction diagonal, identical axis limits.

Clarifications given: the 78-D hyperplane is not drawable; observed-vs-predicted
is the honest picture; **negative held-out R² is valid** (worse than the
mean-prediction baseline). Population statement: the split estimates
generalisation to **new participants from the same 17 ABIDE-II sites**; a random
participant split says nothing about a new scanner/site. A dedicated **Think
first** + `Check your reasoning` on exactly that point.

## 7. Section 3 — training / held-out / leakage (WP11 §7) — SUCCESS

`## 3. Three ways to score the same model`, same fixed split, same 78-feature
recipe. A **Think first** asks students to predict the ordering first. Then a
compact three-row metrics table and (`hide-input`) three aligned
observed-vs-predicted panels with identical axis limits:

| | fit on | evaluated on | R² | MSE |
|---|---|---|---|---|
| **A. correct** | training rows | test rows | **−0.120** | 283.980 |
| **B. training score** | training rows | those same training rows | **+0.091** | 205.672 |
| **C. invalid** | **test rows** | those same test rows | **+0.277** | 183.260 |

Ordering **C > B > A**, so the only honest number is the only negative one. The
invalid model is the clearly named object `invalid_test_fitted_model`, used only
in Section 3 and never again (asserted by `tests/test_exercise_02_notebook.py`).
`n_train`, `n_test`, and feature count are printed. Safeguards in prose: B and C
are not competing models; B compares different rows while **A vs C uses the same
test rows** and isolates the contamination directly; the result is used as-is
even though the inflation is modest; a `Check your reasoning` dropdown explains
the ordering.

## 8. Section 4 — interactive feature-set comparison (WP11 §8) — SUCCESS

### The activity

New reusable browser activity type **`regression-compare`**, built on the
existing TypeScript/Vite/config-driven architecture (same discriminated-union
config, component registry, Zod data schema, locally bundled Plotly, iframe
embedding). Two panels (Model A, Model B); each chooses a **measurement subset**
(cortical thickness / surface area / grey-matter volume / gyrification /
thickness+area) and an **anatomical ROI bundle** (the 6 bundles + "all eligible
ROIs"), shows the exact ROI list (revealable) and feature count, and draws
observed vs **out-of-fold** predicted FIQ with a perfect-prediction diagonal,
the cross-validated R² and MSE, and the participant count. Both panels share
identical axis limits. **No training scores are shown.**

### Static-site implementation

Offline Python (`scripts/export_regression_catalog.py`) pre-computes the finite
catalog to `book/_static/widgets/data/abide_regression_models.json`
(SHA-256 `6ef2cb10f18b3283e9dd491be815b3984ddf8a5e7fc811f64b976d079b61853f`,
287 483 bytes). Every entry uses the **same cohort** (FIQ present, n = 908) and
the **same folds** (`KFold(n_splits=5, shuffle=True, random_state=0)`), so the
`observed` target vector and the per-row `foldOf` assignment are stored **once**
at the top level and each model carries only its out-of-fold `predicted` array.
Preprocessing (`StandardScaler`) is fitted inside each fold. The artifact
contains **no participant identifier** and no raw brain feature. It validates
schema, finite values, row alignment, model keys, per-model R²/MSE recomputed
from the predictions, canonical re-serialisation, and rejects an
identifier-shaped key. Two `--refresh` runs are byte-identical. It loads with no
CDN/backend.

### Catalog contents and actual metrics

35 entries (6 bundles + all-eligible × {CT, Area, Vol, LGI, CT+Area}), **34
enabled, 1 disabled**. Fold-training n = 726; the identifiability bound is
0.7 × 726 = 508. `all-eligible__CT+Area` (p = 716) is **disabled** with the
reason "716 features vs 726 training rows per fold: ordinary least squares is not
numerically defensible here (no regularisation in this activity)". No
pseudo-inverse is silently used; no ridge is introduced.

Every FIQ model has **negative** cross-validated R² (the honest reality that
cortical morphometry barely predicts IQ in this sample). Selected values:

| entry | p | cvR² | cvMSE |
|---|---|---|---|
| `frontoparietal__CT` (defaults A) | 78 | −0.171 | 273.2 |
| `frontoparietal__CT+Area` | 156 | −0.284 | 299.4 |
| `frontal__Area` | 42 | −0.034 | 241.1 |
| `parietal__CT` | 42 | −0.065 | 248.3 |
| `occipital__CT` (defaults B) | 46 | −0.040 | 242.6 |
| `sensorimotor__CT` | 40 | −0.064 | 248.2 |
| `all-eligible__CT` | 358 | −1.208 | 514.8 |
| `all-eligible__Area` | 358 | −0.974 | 460.4 |
| `all-eligible__CT+Area` | 716 | — | DISABLED |

The **literature-motivated frontoparietal bundle does not win**: it is the
*worst* single-measure bundle for cortical thickness (−0.171, vs occipital
−0.040), because it has the most features and therefore overfits most. This is
the §8 lesson made concrete with real data, and it is asserted by
`interactive/tests/regression-compare-data.test.ts` and
`tests/test_export_regression_catalog.py`.

### Config defaults and literature framing

`book/_static/widgets/configs/regression_compare.json`: `defaultA` = `CT` ×
`frontoparietal`, `defaultB` = `CT` × `occipital` (P-FIT vs a comparison bundle,
same measure). A short `literatureNote` (verified DOIs + the Glasser mapping)
sits immediately before the activity, and a `selectionBiasNote` states that
trying many configurations is exploratory model comparison and that quoting the
best CV score as final performance is selection bias. The notebook repeats both
points in prose.

### Interaction tests (WP11 §8)

`interactive/tests/config.test.ts` (+8): schema + semantic validation, default
bundle/measure combination must be offered, duplicate-key / duplicate-subset /
two-bundle-minimum / strict-extra-key rejection, and the shipped config
validates. `interactive/tests/regression-compare.test.ts` (12): R² (incl.
negative), MSE, scatter zip, shared axis range, catalog key. 
`interactive/tests/regression-compare-data.test.ts` (10): committed artifact
parses (n=908, 5 folds, 34 enabled, every metric recomputes), rejects a
misaligned/tampered prediction, a bad cvR², a disabled model carrying
predictions, an identifier-shaped key, an unknown bundle, a foldOf not covering
all folds. `interactive/e2e/regression-compare.spec.ts` (10 = 5 × site-root +
subpath): both panels render, defaults + feature counts, negative-R² metrics
text, a **real control change** (switch bundle → feature count 78→358 and R²
changes, render count increments), the disabled `p ≥ n` combination shows its
reason and hides the plot, the ROI list is revealable, 390 px viewport with no
horizontal document scroll + keyboard-reachable select, no CDN/socket/off-origin.
`interactive/e2e-book/chapter02.spec.ts` (3): the iframe loads on the built
Exercise II page under the Pages subpath, config+data HTTP 200, both panels
render with the right feature counts, a real control change, browser-refresh
restores defaults, 390 px viewport, no CDN/kernel/socket.

## 9. Section 5 — sample size (WP11 §9) — SUCCESS

`## 5. What does sample size change?`, three parts.

**Part A — two outcomes.** Usable counts shown overall and by diagnosis group
(`wp11-0515`). Same frontoparietal-CT recipe, same held-out evaluation:
**FIQ held-out R² −0.120, SRS_TOTAL_RAW held-out R² −0.198** (both negative;
modest availability difference). A **Think first** asks whether a difference
would reflect predictability or sample size / reliability / range / diagnosis /
site / who was assessed. Prose states that comparing different outcomes cannot
isolate sample size, that raw MSE is on different scales and must not be
compared across the two, and that R² is the cross-target metric.

**Part B — matched-N.** Keep FIQ; fix one held-out set (25%, `random_state=42`);
repeatedly (300 deterministic draws, `np.random.default_rng(0)`) subsample the
FIQ training pool to the usable SRS training size and refit. **matched training
N = 573** (vs FIQ full training N = 681). Held-out R² at matched N: **mean
−0.150, 5th–95th pct [−0.196, −0.108]**; FIQ at full N −0.120; SRS at its own N
−0.198. The gap is small because 573 and 681 are close — stated honestly; Part C
is the clean demonstration. A `hide-input` histogram marks the matched-N mean,
the full-N FIQ point, and the SRS point.

**Part C — learning curve.** Same FIQ target, same recipe, one fixed held-out
set, training sizes `[120, 200, 320, 460, 600, 681]`, 40 resamples each. p = 78,
smallest size 120 → n/p = 1.5 (safely above p, per §9C):

| n_train | held-out R² mean | 10th–90th pct |
|---|---|---|
| 120 | −1.962 | [−2.661, −1.377] |
| 200 | −0.608 | [−0.771, −0.454] |
| 320 | −0.325 | [−0.460, −0.209] |
| 460 | −0.196 | [−0.245, −0.156] |
| 600 | −0.138 | [−0.162, −0.118] |
| 681 | −0.120 | [−0.120, −0.120] |

The spread collapses from ±0.6 to 0 as the training set grows; the mean rises
steeply out of the small-sample regime and then flattens **just below zero**.
The interpretation card states: more data bought *certainty*, not a signal the
features do not carry, and individual random draws still wobble. One availability
display, one matched-N distribution, one learning-curve figure, one card — not a
missing-data lecture.

## 10. Questions and synthesis (WP11 §10) — SUCCESS

"Think first" cards are placed before results in §1, §2, §3, §5A. A closing
`### Questions to take away` lists seven reasoning prompts (outcome vs features;
why same-observation scoring inflates; training vs held-out; feature-set
comparison and feature count; negative test R²; why different-target performance
does not isolate sample size; what the learning curve does and does not show).
Some have `Check your reasoning` dropdowns; the open ones do not. `## In summary`
is a six-point synthesis, not a recap. One forward-looking sentence names the
next practice; **no KNN or bias–variance heading or content** was added
(`tests/test_exercise_02_notebook.py::test_no_knn_or_bias_variance_section`).

## 11. Portable notebook and multi-notebook generator (WP11 §11) — SUCCESS

`scripts/build_portable_notebook.py` was refactored to a `NotebookSpec` registry
(`NOTEBOOKS = {chapter_01, chapter_02}`), `build_portable(canonical, columns,
spec=CHAPTER_01)` keeping its old signature and default so every existing caller
and test is unchanged. `main()` `--write` / `--check` now iterate all specs
(superset of the old behaviour); `--notebook {chapter_01,chapter_02,all}` scopes
them.

- **`book/downloads/chapter_01/exercise_01_portable.ipynb` is byte-for-byte
  identical** to before WP11 (verified; `--check` = "up to date (75 cells)"; the
  25 existing portable tests pass unchanged).
- **`book/downloads/chapter_02/exercise_02_portable.ipynb`**, 37 cells (35
  canonical + banner/setup/install − 1 dropped "Run or download" admonition).
  SHA-256 `2514f6ebc153de11f69f7b26e0f286ac18b6a68b8c2231581007356f3aa186a0`.
  Banner names **Machine Learning for Neuroscience**; commented install cell is
  `# %pip install numpy pandas matplotlib scikit-learn` (import audit — no
  `seaborn` in Exercise II); no repository / `requirements.txt` instruction; no
  local relative data/config path (the notebook already loads from pinned HTTPS
  URLs); the embedded activity becomes an HTTPS link to the published Exercise II
  page; no MyST directives, iframes, hide tags, Node requirements, credentials,
  or active install command. `--write` twice is a no-op; the out-of-repo smoke
  executes it cleanly (**15 code cells**, key values matched).
- `scripts/smoke_portable_notebook.py` extended to a per-notebook `SMOKE`
  registry with `--notebook`; both notebooks pass out of repo.
- The Chapter 2 opening references the final `main`-style portable path and the
  published Pages URL, not the feature branch. They are expected not to resolve
  remotely until a later merge/deploy WP.

Distribution warning carried forward (needs Yoav, unchanged from WP09/WP10): the
Colab / raw-download buttons target `github.com/yoavmp/ml-neuro-tutorials` on
`main`; if the repo goes private they break for non-collaborators. Hosting was
not changed in WP11.

## 12. Reproducibility and methodological tests (WP11 §12)

| # | Requirement | Where | Result |
|---|---|---|---|
| 1 | source checksum / provenance + parsed feature taxonomy | `test_abide_modeling_data.py` (`ManifestCheck`, `BrainColumnParsing`) | PASS |
| 2 | target counts + target/brain-feature separation | `test_abide_modeling_data.py`, `test_export_regression_catalog.py` | PASS |
| 3 | no target/phenotype/id/dx/site/age/sex leakage in X | `test_abide_modeling_data.py::LeakageGuard`, `regression-compare-data.test.ts` | PASS |
| 4 | deterministic / disjoint train-test indices | notebook `random_state=42` split; `test_exercise_02_notebook.py::test_fixed_stratified_split_and_pipeline` | PASS |
| 5 | preprocessing learned from training rows/folds only | Pipeline in the notebook and the catalog generator; `test_exercise_02_notebook.py` | PASS |
| 6 | R²/MSE recomputed independently from stored predictions | `regression-compare.ts` + `regression-compare-data.ts`, `test_export_regression_catalog.py::test_every_enabled_model_metric_recomputes` | PASS |
| 7 | training/test/leakage table uses intended rows + labels the invalid case | `test_exercise_02_notebook.py::test_invalid_leakage_model_is_a_clearly_named_object`, `test_executed_outputs_are_present` | PASS |
| 8 | invalid model never enters later data | `test_exercise_02_notebook.py` (asserts `invalid_test_fitted_model` appears exactly twice — defined + used once) | PASS |
| 9 | literature/anatomical bundle mapping valid + outcome-independent | `test_abide_modeling_data.py::test_every_bundle_roi_is_a_real_bilateral_atlas_label`, `test_exercise_02_notebook.py::test_embedded_frontoparietal_bundle_matches_the_manifest` | PASS |
| 10 | every catalog model uses the same cohort/folds | shared `observed` + `foldOf`; `regression-compare-data.ts` superRefine; `test_export_regression_catalog.py::test_shape_and_cohort` | PASS |
| 11 | no unsupported `p ≥ n_train` OLS configuration offered | `test_export_regression_catalog.py::test_a_high_dimensional_combination_is_disabled_with_a_reason`; `regression-compare.spec.ts` disabled test | PASS |
| 12 | matched-N + learning-curve samples deterministic and correctly nested | notebook uses one seeded `default_rng(0)`, one fixed held-out set for both; `test_exercise_02_notebook.py::test_executed_outputs_are_present` | PASS |
| 13 | browser artifact contains no participant identifier | `test_export_regression_catalog.py::test_contains_no_participant_identifier`, `regression-compare-data.test.ts` | PASS |
| 14 | observed-vs-predicted plot data align with metrics | `regression-compare.ts` (`scatterPoints`), `regression-compare-data.ts` recompute | PASS |
| 15 | navigation, portable links, generator staleness, out-of-repo execution | `test_book_structure.py::test_exercise_two_follows_exercise_one`, `build_portable_notebook.py --check`, `smoke_portable_notebook.py` | PASS |
| 16 | Exercise I + its four activities unchanged and green | Exercise I notebook and configs untouched (only `_toc.yml` gained one line); built-book Playwright ch1 16/16, standalone 50 ch1 tests unchanged; Ex I portable byte-identical | PASS |
| 17 | clean build, no `*.err.log`, no new warning, responsive 390 px | book build 2 pre-existing warnings, 0 err.log; `regression-compare.spec.ts` + `chapter02.spec.ts` 390 px | PASS |

Full WP10 baseline re-run after implementation: see the table at the top. Visual
inspection (built book, 1280 px + 390 px): the Exercise II opening, the
wide-table preview, the observed-vs-predicted and 3-panel figures, the
feature-comparison activity (two panels, controls redraw the real Plotly scatter
and the metrics, ROI list reveals, disabled combination shows its reason), the
matched-N histogram and learning-curve figure, and the portable notebook all
render correctly; no page-level horizontal overflow at 390 px.

## Warnings, deviations, deferred / not-performed

1. **The modelling table is a join** of `abide2.tsv` and `abide2_phenotypic.csv`
   (same pinned dir, same study), not a single prepared file. Pre-approved by the
   user; documented in §2–§3 and the manifest. Reproducible with
   `python scripts/abide_modeling_data.py --audit`.
2. **Main target FIQ requires the join** (it is absent from the brain table).
   Reported per WP11 §3. `age` (native, strongly predictable) was considered and
   not chosen — it has no literature-specified regional bundle, which the P-FIT
   framing needs.
3. **FIQ is barely predictable from morphometry in this sample** — every catalog
   model and the canonical recipe give a negative held-out R². This is used as
   the central teaching point (WP11 §6 negative R², §8 "literature motivates a
   hypothesis, not a result"), and the learning curve shows more data buys
   certainty, not signal. It is the honest result, not a defect.
4. **Modest FIQ (908) vs SRS (764) availability contrast** for §9A — the WP's
   ideal <100 vs ~1000 was explicitly not to be forced, and the two continuous
   scores that would give a sharper contrast (ADOS, ADI-R) are group/site
   confined and were rejected. §9B/§9C (both on FIQ) are the rigorous
   demonstrations.
5. **Notebook cell count 35** — the low end of the WP's "roughly 35–50"; the
   lecture-first, no-definition-only-sections constraints leave little to add
   without padding.
6. **New generated source artifact** `abide_regression_models.json` — a
   committed deterministic input the Vite app loads (like the other three widget
   data files), regenerable with
   `python scripts/export_regression_catalog.py --refresh`. Not build output.
7. **New committed manifest** `book/config/abide_modeling.json` — reviewed source
   of truth, offline-validatable (`abide_modeling_data.py --check`).
8. **Canonical Exercise II notebook executed end-to-end** (network: pinned
   `abide2.tsv` + phenotypic CSV) so committed outputs are current. Figure bytes
   are deterministic within this environment (2 clean builds → identical 9-PNG
   hash set); the pre-existing cross-platform Matplotlib byte-difference risk
   (numpy/pandas/matplotlib unpinned) is unchanged.
9. **Colab interactive rendering not machine-verified** (Google serves an app
   shell to headless automation — same as WP07–WP10). URL structure and the raw
   target are covered by the notebook-content tests.
10. **No live / remote checks** — by the stop condition: no push, no `main`
    merge, no deployment. GitHub Pages still serves the WP08–WP10 content;
    hosting and the private/public distribution architecture were not touched.
    The generic sphinx-book-theme download control was not touched.
11. **Pre-existing warnings kept** — `logo.png` missing, `book/README.md` not in
    a toctree; the Vite 500 kB Plotly-chunk advisory. All unchanged, out of
    scope.

## Unresolved risks / needs Yoav

- **Private-repository distribution** (carried from WP09 §6/§13, WP10): the
  Chapter 1 *and now Chapter 2* Colab / raw-download buttons target
  `github.com/yoavmp/ml-neuro-tutorials` on `main` and will break for
  non-collaborators if the repo goes private. Not in scope for WP11.
- **Merge / deployment of WP09–WP11** is a separate, later WP after review.
- **KNN and the full bias–variance section** are the next WP, deliberately not
  started.

## Confirmation of safety constraints

- **No KNN and no full bias–variance content** — only one forward-looking
  sentence; asserted by `test_exercise_02_notebook.py`.
- **No merge to `main`, no deployment, no push, no force push** — nothing left
  the local `feature/regression-practice` branch.
- **No destructive git command** — no `git reset --hard`, `git checkout -- <path>`,
  `git clean`, `git rebase`, `git revert`, tag or branch deletion.
- **No repository-setting / hosting / Pages / distribution-architecture change.**
  The generic theme download control was not removed or changed.
- **No generated build output committed** — `book/_build`, `book/.jupyter_cache`,
  `book/_static/widgets/app`, `interactive/node_modules`, `__pycache__`, and
  Playwright artifacts remain untracked / git-ignored.
  `abide_regression_models.json` and `abide_modeling.json` are source assets, not
  build output.
- **Exercise I unchanged** — its notebook, configs, activities, portable
  notebook (byte-identical), and tests are untouched; only `book/_toc.yml` gained
  one line.
- **No next practice notebook (KNN / bias–variance) created or started.**

## Key identifiers

| Item | Value |
|---|---|
| Branch | `feature/regression-practice` (off `502f75a`) |
| Checkpoint commit | `7b6986433474d5173062dd4c6d4290c0a373acd9` (`checkpoint: before WP11`) |
| Checkpoint tag | `wp11-start` → `7b69864` (annotated; tag object `8ccadfb16be461643ab9fc782be6a47b3b8ed664`; no numeric suffix needed) |
| Implementation commit | `5e785e2` (`WP11: Exercise II linear regression, feature-set comparison activity, modelling data pipeline`) — 25 files, +5230 / −244 |
| Report commit | `WP11 report: document Exercise II linear regression` — adds `WPs/reports/WP11_REPORT.md` + `WPs/reports/WP11_EXACT_CHANGELOG.md` only; hash in the terminal summary |
| Modelling manifest | `book/config/abide_modeling.json` SHA-256 `011def63db0b9c28da1a4b578f4cbcc07901af3ffa20ac799ea507cd807b0096` |
| Regression catalog | `book/_static/widgets/data/abide_regression_models.json` SHA-256 `6ef2cb10f18b3283e9dd491be815b3984ddf8a5e7fc811f64b976d079b61853f` |
| Canonical notebook | `book/chapters/chapter_02/exercise_02.ipynb` SHA-256 `5702670b5ecfb115fcf71bc1623516973f53f985dd7340d18feb9b5a592eefd9` |
| Portable notebook | `book/downloads/chapter_02/exercise_02_portable.ipynb` SHA-256 `2514f6ebc153de11f69f7b26e0f286ac18b6a68b8c2231581007356f3aa186a0` |

## Instructions for reviewer

Paste this entire report (`WP11_REPORT.md`) into the ChatGPT conversation that
produced WP11. `WP11_EXACT_CHANGELOG.md` is the companion location-specific
before/after record.
