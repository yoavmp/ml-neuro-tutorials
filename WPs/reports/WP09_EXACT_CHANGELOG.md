# WP09 — exact change log

Location-specific before/after entries. Notebook cells are referenced by their
stable `nbformat` cell id. It should be possible to review the substantive work
from this file without diffing raw notebook JSON.

Branch `feature/course-pages-and-eda-trim`; checkpoint `2c3a165` (tag
`wp09-start`); implementation commit `13ab778`.

---

## 1. Git objects

| Item | Value |
|---|---|
| Branch created from | `main` `6d8c1f67bdac2af9c131919be72fb43dcb813598` |
| Checkpoint commit | `2c3a165c7eba85c922c7df95a760aeaf9c91b232` — `checkpoint: before WP09` (adds `WPs/WP09_COURSE_PAGES_AND_EDA_TRIM.md`, 1 file, +454) |
| Annotated tag | `wp09-start` → `2c3a165` (tag object `49ab764ca9eb47243f4d0506293cb68131154401`; name free, no suffix) |
| Implementation commit | `13ab778075c300695959eb2065448b7e8778940e` — `WP09: course pages, streamlined EDA lesson, table-inspection activity` (36 files, +3076 / −1656) |
| Report commit | `WP09 report: document course pages and EDA streamlining` (adds the two report files only; hash in the terminal summary) |

Tags `wp01-start`…`wp08-start` and branch `feature/reusable-interactive-widgets`
untouched. No push, no merge, no force, no history rewrite.

---

## 2. Course-level book structure

### `book/_config.yml`
- L1 `title: Machine Learning for Neuroscientists` → `title: Machine Learning for Neuroscience`

### `book/intro.md` (the book root — Introduction page)
- **Before:** `# Introduction` + "Welcome to the tutoring materials for **Machine
  Learning for Neuroscientists**." + a generic bullet list of tutorial contents +
  a one-line note about classroom / independent study.
- **After:** full rewrite — three sections:
  - intro paragraph: practice-session materials for **Machine Learning for
    Neuroscience**; each notebook follows a short PowerPoint **on Moodle**
    (named, no URL);
  - `## Using the notebooks`: in-class *or* self-study at your own pace; some
    activities interactive with nothing to install; run and change the code;
    every notebook has a **Colab** link + a downloadable `.ipynb`;
  - `## About the questions`: questions placed *before* explanations to build
    reasoning, style close to course assessment / exam questions; some have a
    revealable guide, others are open with **no single correct answer**.
- No time budget, no Moodle URL, no "every question has an answer".

### `book/syllabus.md`
- **Before:** `To be filled - copy from our syllabus ` (no title → 7 repeated
  `toctree contains reference to document 'syllabus' that doesn't have a title`
  warnings).
- **After:** `# Syllabus` (title only). Warnings eliminated.

### `book/contents.md`
- Unchanged (`# Contents` + `{tableofcontents}`; ready for future practices).

### `book/_toc.yml`
- Unchanged — already `root: intro` with
  `chapters: [syllabus, contents → sections → chapters/chapter_01/exercise_01]`,
  which is exactly the required order.

### `book/README.md`
- L2 "tutorials for the Computational Learning for Neuroscience course Tel Aviv
  University" → "practice materials for the Machine Learning for Neuroscience
  course, Tel Aviv University". (Root `README.md` line 7 — an attribution to a
  *different* prior course — left untouched.)

---

## 3. Canonical column authority

### `book/config/eda_phenotype_columns.json`
- **Before (39):** `SITE_ID, SUB_ID, DX_GROUP, PDD_DSM_IV_TR, AGE_AT_SCAN, SEX,
  HANDEDNESS_CATEGORY, HANDEDNESS_SCORES, FIQ, VIQ, PIQ, FIQ_TEST_TYPE,
  CURRENT_MED_STATUS, EYE_STATUS_AT_SCAN, ADI_R_SOCIAL_TOTAL_A,
  ADI_R_VERBAL_TOTAL_BV, ADI_R_RRB_TOTAL_C, ADOS_MODULE, ADOS_G_TOTAL,
  ADOS_2_TOTAL, ADOS_2_SEVERITY_TOTAL, SRS_VERSION, SRS_INFORMANT, SRS_TOTAL_RAW,
  SRS_AWARENESS_RAW, SRS_COGNITION_RAW, SRS_COMMUNICATION_RAW, SRS_MOTIVATION_RAW,
  SRS_MANNERISMS_RAW, SRS_TOTAL_T, SCQ_TOTAL, RBSR_6SUBSCALE_TOTAL, MASC_TOTAL_T,
  BRIEF_BRI_T, BRIEF_MI_T, BRIEF_GEC_T, CBCL_6-18_INTERNAL_T,
  CBCL_6-18_EXTERNAL_T, CBCL_6-18_TOTAL_PROBLEM_T`
- **After (13):** `SITE_ID, SUB_ID, DX_GROUP, AGE_AT_SCAN, SEX,
  HANDEDNESS_CATEGORY, FIQ, VIQ, PIQ, CURRENT_MED_STATUS, SRS_TOTAL_RAW,
  ADOS_G_TOTAL, ADI_R_SOCIAL_TOTAL_A`

---

## 4. Widget data pipeline

### `scripts/export_widget_data.py`
- Module docstring: "eight numeric variables" → "the seven numeric variables of
  the curated teaching table"; added a line noting the retention artifact also
  backs `eda-correlation` and `table-inspection`.
- `HISTOGRAM_VARIABLES`:
  `[AGE_AT_SCAN, FIQ, VIQ, PIQ, ADOS_G_TOTAL, ADOS_2_TOTAL, SRS_TOTAL_RAW, SCQ_TOTAL]`
  → `[AGE_AT_SCAN, FIQ, VIQ, PIQ, SRS_TOTAL_RAW, ADOS_G_TOTAL, ADI_R_SOCIAL_TOTAL_A]`
- `RETENTION_VARIABLES`:
  `[DX_GROUP, AGE_AT_SCAN, SEX, HANDEDNESS_CATEGORY, FIQ, VIQ, PIQ, ADOS_G_TOTAL,
  ADOS_2_TOTAL, SRS_TOTAL_RAW, SCQ_TOTAL, CURRENT_MED_STATUS, EYE_STATUS_AT_SCAN]`
  → `[DX_GROUP, AGE_AT_SCAN, SEX, HANDEDNESS_CATEGORY, FIQ, VIQ, PIQ,
  CURRENT_MED_STATUS, SRS_TOTAL_RAW, ADOS_G_TOTAL, ADI_R_SOCIAL_TOTAL_A]`
  (dropped `ADOS_2_TOTAL`, `SCQ_TOTAL`, `EYE_STATUS_AT_SCAN`; added
  `ADI_R_SOCIAL_TOTAL_A`). Categorical-codes comment: `EYE_STATUS_AT_SCAN 0/1/2`
  dropped.

### `book/_static/widgets/data/abide_histogram.json`  (regenerated `--refresh`)
- 8 numeric columns → **7**: `AGE_AT_SCAN, FIQ, VIQ, PIQ, SRS_TOTAL_RAW,
  ADOS_G_TOTAL, ADI_R_SOCIAL_TOTAL_A`. `rowCount` 1114. Re-validated `--check`
  (canonical).

### `book/_static/widgets/data/abide_retention.json`  (regenerated `--refresh`)
- `SITE_ID` + 13 vars → `SITE_ID` + **11**: drops `ADOS_2_TOTAL, SCQ_TOTAL,
  EYE_STATUS_AT_SCAN`; adds `ADI_R_SOCIAL_TOTAL_A`. `rowCount` 1114, `siteCount`
  19. Re-validated `--check` (canonical). Backs `eda-retention`,
  `eda-correlation`, and `table-inspection`.

---

## 5. Widget configs

### `book/_static/widgets/configs/eda_histogram.json`
- `variables`: removed `ADOS_2_TOTAL` ("ADOS-2 total"), `SCQ_TOTAL` ("SCQ total");
  added `ADI_R_SOCIAL_TOTAL_A` ("ADI-R social total"). `defaultVariable`
  `AGE_AT_SCAN`, `bins` `{5,60,1,25}` unchanged.
- reflectionPrompts[2]: "…ADOS and SCQ totals…" → "…the ADOS-G and ADI-R
  totals…".

### `book/_static/widgets/configs/eda_retention.json`
- group `behavioral` variables:
  `[ADOS_G_TOTAL, ADOS_2_TOTAL, SRS_TOTAL_RAW, SCQ_TOTAL]` →
  `[SRS_TOTAL_RAW, ADOS_G_TOTAL, ADI_R_SOCIAL_TOTAL_A]`.
- group `scan` label "Medication and scan conditions" → "Medication status";
  variables `[CURRENT_MED_STATUS, EYE_STATUS_AT_SCAN]` → `[CURRENT_MED_STATUS]`.
- `defaultVariables` `[DX_GROUP, AGE_AT_SCAN, SEX, FIQ]` unchanged.
- Effect: "Select all" is now **11** variables (was 13); suggested-core retention
  1015 / 1114 (91.11 %) unchanged.

### `book/_static/widgets/configs/eda_correlation.json`
- `variables`: removed `ADOS_2_TOTAL`, `SCQ_TOTAL`; added `ADI_R_SOCIAL_TOTAL_A`
  → `[AGE_AT_SCAN, FIQ, VIQ, PIQ, SRS_TOTAL_RAW, ADOS_G_TOTAL,
  ADI_R_SOCIAL_TOTAL_A]`.
- `defaultX` `FIQ`, `defaultY` `SRS_TOTAL_RAW`, `defaultMethod` `pearson`,
  `groupings` (DX_GROUP / SEX) unchanged → default `r = -0.2404`, `n = 778`
  unchanged.
- reflectionPrompts[1]: "…ADOS-G total vs ADOS-2 total. Both look strong…" →
  "…ADOS-G total vs ADI-R social total. Both are positive…".

### `book/_static/widgets/configs/table_inspection.json`  (NEW)
```
type "table-inspection", data "../data/abide_retention.json",
siteField "SITE_ID", methods [head, tail, sample], defaultMethod "head",
rowCount {min 5, max 15, default 8}, sampleSeed 7,
columns: SITE_ID, DX_GROUP, AGE_AT_SCAN, SEX, HANDEDNESS_CATEGORY, FIQ,
         SRS_TOTAL_RAW, ADOS_G_TOTAL
reflectionPrompts: 2 operational nudges (distinct from the notebook Think first)
```

---

## 6. Interactive TypeScript layer (`interactive/`)

### NEW `src/table-inspection.ts`
Pure maths: `mulberry32(seed)`, `sampleRowIndices(totalRows, k, seed)` (full
Fisher–Yates, ascending, `k` clamped), `selectRowIndices(method, …)`,
`summariseView(columns, siteLabels, displayColumns, rowIndices)` →
`{rowCount, sites[], siteCount, missingCells, totalCells}`, `formatCell`,
`INSPECTION_METHODS`.

### NEW `src/components/table-inspection.ts`
`table-inspection` component: `<fieldset>` radio group, `Rows` range input,
`Reshuffle sample` button (`seed = (seed + 1) >>> 0`), accessible `<table>`
(`<caption>`, `<th scope="col">`, sticky `thead`) inside `.widget-table-scroll`
(`overflow-x:auto`), live `role="status"` evidence summary, `.widget-cell-missing`
+ visually-hidden "missing" for null cells. State on the table element:
`data-method, -row-count, -site-count, -sites, -missing-cells, -total-cells,
-seed, -render-count`. Reuses `parseAbideRetentionData` / `abide_retention.json`.

### `src/config.ts`
- Added `tableInspectionColumnRef`, `tableInspectionRowCount`,
  `tableInspectionMethod`, `tableInspectionConfig` (strict Zod, `sampleSeed`
  optional int ≥ 0, `reflectionPrompts` optional).
- `activityConfigSchema` discriminated union: `+ tableInspectionConfig`.
- Exported `TableInspectionConfig` type.
- `checkSemantics`: new `table-inspection` block — duplicate column names,
  `siteField` must be a displayed column, methods no-dup, `defaultMethod ∈
  methods`, `rowCount.min ≤ max`, `default ∈ [min,max]`, `sampleSeed` required
  when `methods` includes `sample`.

### `src/components/registry.ts`
- `+ import { tableInspectionComponent }` and `registry.register(tableInspectionComponent)`.

### `src/styles.css`
- Appended: `.widget-radio-group`, `.widget-radio`, `.widget-table-scroll`
  (`overflow-x:auto`), `.widget-table` (+ `caption`, `th`/`td` `white-space:nowrap`,
  sticky `thead th`), `.widget-cell-missing` (`position:relative` so the
  visually-hidden span cannot escape the scroll box), `.widget-visually-hidden`.

### NEW `tests/table-inspection.test.ts` — 23 tests (see report §11).

### `tests/config.test.ts` — `+11` tests: `parseActivityConfig — table-inspection`
describe block + shipped-`table_inspection.json` validation.

### `tests/retention-data.test.ts`
- Committed-artifact column-set assertion: removed `ADOS_2_TOTAL`,
  `EYE_STATUS_AT_SCAN`, `SCQ_TOTAL`; added `ADI_R_SOCIAL_TOTAL_A` (14 → 12 keys).

### `tests/retention.test.ts`
- `{SCQ_TOTAL, ADOS_2_TOTAL}: 119 / 1114 (10.6822 %)` →
  `{ADOS_G_TOTAL, ADI_R_SOCIAL_TOTAL_A}: 152 / 1114 (13.6445 %)`.

### `tests/correlation-data.test.ts`
- Column-presence loop: `ADOS_2_TOTAL`, `SCQ_TOTAL` → `ADI_R_SOCIAL_TOTAL_A`.

### `tests/correlation.test.ts`
- `ADOS-G ~ ADOS-2 total` (n 81, r 0.8815) → `ADOS-G ~ ADI-R social total`
  (n 152, r 0.17494).
- `SRS_TOTAL_RAW ~ SCQ_TOTAL` grouped by diagnosis (overall 0.842, groups
  0.543/0.413) → `SRS_TOTAL_RAW ~ ADOS_G_TOTAL` grouped by diagnosis
  (overall 0.303834, groups n [211, 8], r [0.158969, 0.8404]).

### `tests/histogram-data.test.ts`
- Committed-artifact column set: `ADOS_2_TOTAL`, `SCQ_TOTAL` removed;
  `ADI_R_SOCIAL_TOTAL_A` added (8 → 7 keys).

### NEW `e2e/table-inspection.spec.ts` — 10 tests (5 × root + subpath):
deterministic head/tail, fixed seeded sample, Reshuffle → seed 8 + changed
sites, reload restores defaults, row-count control + `data-total-cells`,
accessible missing cells (never "error"), radio keyboard (`ArrowDown`),
narrow-viewport table scroll + no horizontal document scroll, offline/no-CDN
audit.

### `e2e/retention.spec.ts`
- `retention-var-SCQ_TOTAL` → `retention-var-ADOS_G_TOTAL` (both occurrences).
- `retention-var-ADOS_2_TOTAL` → `retention-var-ADI_R_SOCIAL_TOTAL_A`.
- "Select all" `data-selected-count` `"13"` → `"11"`.

### `e2e/correlation.spec.ts`
- small-N pair: `ADOS_G_TOTAL` / `ADOS_2_TOTAL`, `data-n "81"` →
  `ADOS_G_TOTAL` / `ADI_R_SOCIAL_TOTAL_A`, `data-n "152"`; stats text `n = 81` →
  `n = 152`.

### `e2e/histogram.spec.ts`
- "refresh restores defaults" selects `SCQ_TOTAL` → `ADI_R_SOCIAL_TOTAL_A`.

### `e2e-book/chapter01.spec.ts`
- `+ TABLE_INSPECTION_IFRAME_SELECTOR` const + `tableInspectionFrame()` helper.
- `+ test.describe("Chapter 1 built page — embedded head/tail/sample activity")`
  with 3 tests (loads + method switch + audit; reload restores `head`;
  narrow-viewport row-count).
- retention section: `retention-var-SCQ_TOTAL` → `retention-var-ADOS_G_TOTAL`;
  `data-selected-count "13"` → `"11"`.
- histogram section: `selectOption("SCQ_TOTAL")` → `"ADI_R_SOCIAL_TOTAL_A"`.

---

## 7. Notebook `book/chapters/chapter_01/exercise_01.ipynb`  (84 → 76 cells)

### Cells removed (12: 8 markdown + 4 code)

| id | was | reason |
|---|---|---|
| `a1b2c30d4e5f` | md "## About this exercise" | §5 — now owned by the Introduction |
| `b2c3d40e5f6a` | md "How to use this notebook" admonition | §5 |
| `6d0ba51b-5219-4743-8c9a-e37126224d86` | md "## Learning objectives" | §5 |
| `c80dce59-8978-4314-a20b-ec0947c1f175` | md "### Inspecting a random sample" | §11 |
| `7af020ab-570e-43ce-a88a-eb51b34aa8b6` | code `phenotypes.sample(n=8, random_state=42)` (visible) | §11 |
| `3ad75c70-7fdf-406c-be12-7f2329dd0cb5` | md "#### Interpreting `info()`" | §8 |
| `5284a2b7-51c1-420e-b7e9-385b64dd70ec` | md "#### Interpreting `describe()`" | §8 |
| `c4dc9fe3ee9e` | code pairwise-N heatmap "Participants behind each correlation" (`hide-input`) | §10 / §11 |
| `e15470791c85` | md "### When a correlation matrix is the wrong tool" | §10 |
| `2c5625b060d7` | code `SEX × DX_GROUP` crosstab (visible) | §10 |
| `458219f7acdb` | code Cramér's V sidebar (`hide-cell`) | §10 |
| `1e00b5ffc77d` | md Think first "Choosing an association measure" | §10 |

### Cells added (4: 3 markdown + 1 code), inserted after `3e4d2fad-…` ("## 2. Data inspection")

| id | type | content |
|---|---|---|
| `7a1e5c93d201` | md | intro line + `<iframe title="Interactive head, tail, and sample comparison for the ABIDE-II table" src="../../_static/widgets/app/index.html?config=../configs/table_inspection.json" … class="ml-activity">` |
| `7a1e5c93d202` | md | `{admonition} Think first` — sites in head()/tail()? in sample()? missingness? which view for a first broad look + what a small sample can't promise |
| `7a1e5c93d203` | md | explanation: head()/tail() deterministic & good for ordering/schema; sample() wider spread in an ordered multi-site table; small sample not guaranteed representative; `random_state` reproduces one draw |
| `7a1e5c93d204` | code (`hide-input`) | `from IPython.display import display` + `display(phenotypes.head(8))` / `.tail(8)` / `.sample(8, random_state=0)` |

### Cells modified (source)

| id | before → after |
|---|---|
| `c4d5e6f7a8b9` | "swaps the **three** embedded activities" → "**four**" |
| `373d8862-…` | heading `### What this notebook covers` → `## What this notebook covers`; item 2 now "comparing `head()`, `tail()`, and `sample()`…"; item 5 "…range checks, and Pearson/Spearman correlations (with the correlation explorer)"; **added** a concise `**Prerequisites:**` line — `pandas`, `matplotlib`, `seaborn` only (**NumPy removed**), "run the cells in order", "first run needs internet access" |
| `bd37a40a-…` (data load, `hide-cell`) | removed `import pandas as pd`; `# Use a pre-selected subset…\nCOLUMNS_URL = "https://raw.githubusercontent.com/yoavmp/…/main/book/config/eda_phenotype_columns.json"` and `phenotypes = phenotypes[pd.read_json(COLUMNS_URL, typ="series").tolist()].copy()` → `import json` + `from pathlib import Path` + `CURATED_COLUMNS = json.loads(Path("../../config/eda_phenotype_columns.json").read_text())` + `phenotypes = phenotypes[CURATED_COLUMNS].copy()`. Printed shape unchanged in form → **`(1114, 13)`** |
| `81d44a95-…` (dropdown) | "a curated subset of 39 demographic, diagnostic, cognitive, and behavioral variables" → "a deliberately small curated slice: 13 columns covering identifiers, core demographics, diagnosis, a few cognitive scores, and a couple of autism-assessment totals" |
| `3e4d2fad-…` ("## 2. Data inspection") | removed the `head()`/`tail()` "may not represent the entire dataset" / "A random sample can provide a broader first impression" advance claim; now a neutral 4-item list of `head()`/`tail()`/`sample()`/custom + "Which … gives the most useful first impression? The activity below lets you compare them …" |
| `ea35b076-…` (Think first) | "Examine the **sampled rows**…" → "Look at the rows and the column names **in the views above**…"; Q3 "variables or **subjects**" → "variables or **participants**" |
| `4116a60a-…` ("### Dataset structure with `info()`") | closing line rewritten to fold in the §8 caveat ("…shape, … data types, … non-null counts … but it says nothing about the distribution …") |
| `5af7a0f6-…` ("### Identifying hidden categorical variables") | examples updated: `SITE_ID` as `str` (was `SITE_ID` and `FIQ_TEST_TYPE` as `object`); `HANDEDNESS_CATEGORY` and `CURRENT_MED_STATUS` as floats (was `ADOS_MODULE` and `CURRENT_MED_STATUS`) |
| `be0fb829-…` (Think first) | Q4 "Is `ADOS_MODULE` an ordered severity scale …" → "`HANDEDNESS_CATEGORY` is coded `1`, `2`, `3`. Is that an ordered scale or three unordered groups? How would you check?" |
| `64a0bf6b-…` (code, visible) | `categorical_columns` `[SITE_ID, DX_GROUP, PDD_DSM_IV_TR, SEX, HANDEDNESS_CATEGORY, FIQ_TEST_TYPE, CURRENT_MED_STATUS, EYE_STATUS_AT_SCAN, ADOS_MODULE, SRS_VERSION, SRS_INFORMANT]` → `[SITE_ID, DX_GROUP, SEX, HANDEDNESS_CATEGORY, CURRENT_MED_STATUS]`; `SUB_ID` → `string` kept |
| `2545ca48-…` | ADOS_MODULE ordered-scale example → `HANDEDNESS_CATEGORY` right/left/mixed `1/2/3` "three groups, not an increasing scale" |
| `0adaedf8-…` ("### Numerical summaries with `describe()`") | "…easier to read when the dataset contains many columns." shortened; **added** §8 caveat paragraph ("…can hide differences between groups or sites, and the `count` column is the reminder …") |
| `a6028127-…` ("### Common approaches to missing data") | ~10-row table → **3 body rows** (Remove / Impute [all variants in one row] / Keep missingness explicit), columns approach / when useful / main caution; closing "…no one strategy is always best." |
| `1b016f0b-…` ("#### Removing incomplete observations") | "contains 39 variables…" / "complete data for all **39** variables" → "This curated table has **13** variables, and two of them — the ADOS-G and ADI-R totals — were collected for only part of the sample." / "all **13** variables" |
| `33d94597-…` (code, `hide-input`) | dataset label `"Complete for all 39 variables"` → `"Complete for all 13 variables"`; output row → **95 / 8.5 %** (was 1 / 0.1 %) |
| `70fdfc764608` (code, visible) | `summary_variables` `[AGE_AT_SCAN, FIQ, SRS_TOTAL_RAW, SCQ_TOTAL, ADOS_G_TOTAL]` → `[AGE_AT_SCAN, FIQ, SRS_TOTAL_RAW, ADOS_G_TOTAL, ADI_R_SOCIAL_TOTAL_A]`; comment updated |
| `b32176a3b7f9` (Think first + dropdown) | Q2 & dropdown items 2–3: `SCQ_TOTAL and ADOS_G_TOTAL` → `ADOS_G_TOTAL and ADI_R_SOCIAL_TOTAL_A`; "If the SCQ was collected…" → "If the ADOS-G or ADI-R was collected…" |
| `c374c2ec5540` (Think first + dropdown) | "flagged ages are roughly **31–64** years" → "roughly **33 to 64** years" |
| `fd14e7f5d7a7` ("### Pearson, Spearman, and the sample behind each number") | title → "### Pearson and Spearman correlations"; dropped the "each cell can be computed from a different subset … pairwise-complete sample-size matrix" paragraph; kept the Pearson↔Spearman comparison table; new closing line notes missing values differ between variables |
| `9b478759eff3` (code, `hide-input`) | `correlation_variables` `[AGE_AT_SCAN, FIQ, VIQ, PIQ, SRS_TOTAL_RAW, SRS_COMMUNICATION_RAW, SCQ_TOTAL, ADOS_G_TOTAL]` → `[AGE_AT_SCAN, FIQ, VIQ, PIQ, SRS_TOTAL_RAW, ADOS_G_TOTAL, ADI_R_SOCIAL_TOTAL_A]`; comment simplified; `figsize` `(7.5, 6)` → `(7, 5.5)` |
| `188d49e2ebf5` ("Read the two matrices together") | 4 long bullets + p-value note → 3 short data-supported observations (`FIQ~VIQ/PIQ ≈ 0.83` definitional, `VIQ~PIQ ≈ 0.52`; social measures `≈ 0.30` on few participants; `AGE~ADOS_G` Pearson −0.23 / Spearman −0.33) + kept the "no p-values" note + a one-paragraph **Practical takeaway** |
| `3efbb7fdf9a7` (Think first + dropdown) | Q2 & dropdown item 2: "X = `ADOS-G total`, Y = `ADOS-2 total`" / "`n` is about 81 … ADOS-G and ADOS-2 are different versions" → "X = `ADOS-G total`, Y = `ADI-R social total`" / "`n` is about 152 … different instruments (a direct observation schedule and a parent interview)" |

### Cells re-executed (outputs regenerated from the 13-column table, 0 errors)

`bd37a40a-…` (shape), `64a2cd66-…` (`info()` → 13 columns), `909cb415-…`
(dtypes → 5 categoricals + `SUB_ID` string), `5bef8a25-…` (`describe().T` → 7
numeric rows), `675bc826-…` (`missing_summary` → 8 rows), `b7fb371d-…`
(missingness heatmap → 8 rows), `69a9eef8-…` (missing-by-diagnosis → 8 rows),
`33d94597-…` (retention 1114 / 95 / 1015), `b2d5e7b0-…` (median FIQ 112.0, 99
imputed), `8b45099c-…` (imputed-FIQ describe), `2fa6ee38-…` (824 / 167 / 123),
`e6f7a8b9c0d1` (age histogram), `70fdfc764608` (distribution summary),
`80632a35b296` (FIQ violin: Autism 479 / 108.0 / 106.6, Control 536 / 115.0 /
114.9), `283362766ec1` (site×diagnosis heatmap), `7bf82a8cd5a9` (IQR: 56 / 1114
flagged), `9b478759eff3` (Pearson matrix, 7×7).

### Final counts

76 cells · 56 markdown · 20 code (10 visible, 8 `hide-input`, 2 `hide-cell`, 0
`hide-output`). `nbformat.validate` OK; ids unique; only `hide-*` tags anywhere.

---

## 8. Portable-notebook generator

### `scripts/build_portable_notebook.py`
- Docstring: "three browser activities" → "four"; note that the canonical
  notebook reads the column list from `book/config/`; mention the optional
  commented `%pip install` cell.
- `IFRAME_REPLACEMENTS`: **+** key `"Interactive head, tail, and sample
  comparison for the ABIDE-II table"` → a Markdown pointer paragraph +
  course-page link (now 4 entries).
- **+** `SETUP_INSTALL_ID = "portable-setup-install"`,
  `LESSON_PACKAGES = "numpy pandas matplotlib seaborn"`.
- `_rewrite_data_loading()`: now strips `import json` / `from pathlib import Path`
  and replaces the `CURATED_COLUMNS = json.loads(Path("../../config/…").read_text())`
  block (regex, `DOTALL`) with the literal `CURATED_COLUMNS = [ … ]`; leading
  blank line trimmed. (Old form keyed on `COLUMNS_URL` / `pd.read_json`.)
- `_banner_cell()`: names "**Machine Learning for Neuroscience**"; "three
  activities" → "four" (×2).
- `_setup_cell()`: removed the `requirements.txt` / "from the repository"
  wording; now "run the next cell once … then restart the kernel", plus the
  internet-access note.
- **+** `_setup_install_cell()`: a code cell with a commented
  `# %pip install numpy pandas matplotlib seaborn` (never active).
- `build_portable()`: `cells = [_banner_cell, _setup_cell, _setup_install_cell]`
  (was 2); code-cell rewrite trigger `"COLUMNS_URL" in source` →
  `"eda_phenotype_columns.json" in source`.
- `_assert_portable()` banned set: **+** `"../../config/"`, `"requirements.txt"`;
  **+** rejects `CURATED_COLUMNS = json.loads`, a missing install cell, a
  changed/absent commented `%pip` line, and any active `%pip`/`!pip` line.

### `book/downloads/chapter_01/exercise_01_portable.ipynb`  (regenerated `--write`)
- 84 → **78** cells (canonical 76 − 1 dropped "Run or download" admonition + 3
  prepended banner/setup/install). Data-load cell has the embedded
  `CURATED_COLUMNS` literal (13) and the pinned ABIDE-II CSV URL; no
  `../../config/`, no `requirements.txt`, no active install command. `--check`
  passes; deterministic (`test_repeated_builds_are_byte_identical`).

### `scripts/smoke_portable_notebook.py`
- Docstring "loads as 1114 x 39" → "1114 x 13 (the WP09 curated slice)".
- `EXPECTED_SUBSTRINGS`: `"Data table shape: (1114, 39)"` →
  `"Data table shape: (1114, 13)"` (`"56 of 1114 participants flagged"` kept).
- Result: 21 code cells executed cleanly out of repo, key values matched.

---

## 9. Python tests

### `tests/test_notebook_corrections.py`  (WP07 → WP09 rewrite)
Replaced the WP07 assertions with a WP09 `NotebookStreamlining` suite (23 tests):
About/How-to/Learning-objectives removed; H1 + compact Colab/download control +
`What this notebook covers` retained; NumPy not a stated prerequisite; the
13-column config; notebook reads the config from one place; `(1114, 13)` shape
output; **no stale removed phenotype** (30-name blocklist) in code or
active-table prose; categorical-conversion list is exactly the 5 curated
categoricals; `Interpreting info()/describe()` sections absent + caveats folded
in; missing-data table ≤ 3 body rows; complete-case prose/code say 13 not 39;
correlation detours removed (`pairwise_n`, `cramers_v`, "wrong tool", crosstab,
"Choosing an association measure"); correlation matrix uses the 7 curated
numerics; section ends with a Practical takeaway; table-inspection activity block
in the right place with the right iframe title/src; no advance claim that
head/tail are inferior; Think first → explanation → collapsed Python equivalent;
cell/visibility counts (76 / 20 / 10-8-2-0); valid + unique ids, only `hide-*`
tags; seeded stripplot preserved; histogram example preserved; IQR still flags
56.

### NEW `tests/test_book_structure.py` (7 tests)
Course title exact / no markdown / no old name; `_toc.yml` `root: intro` and the
Introduction → Syllabus → Contents → Exercise I order; `syllabus.md` is exactly
`# Syllabus`; Introduction covers every requested concept; Introduction has no
`http`, no time budget, no answer guarantee; Contents keeps `{tableofcontents}`.

### `tests/test_build_portable_notebook.py`
- `test_banner_and_setup_prepended`: cells[0]=banner, [1]=setup, [2]=install;
  banner names the course; dropped the `requirements.txt` assertion.
- **+** `test_setup_has_no_repo_instruction_and_a_commented_install_cell`.
- `test_iframe_cells_replaced_with_published_links`: `len(IFRAME_REPLACEMENTS)`
  == 4; `count(PUBLISHED_PAGE)` == `1 + 4`.
- `test_portable_data_loading_is_offline_safe`: **+** `"CURATED_COLUMNS = json.loads"`,
  `"../../config/"`, `"requirements.txt"` all absent.
- **+** `test_all_four_activities_are_recognised_explicitly`,
  `test_unknown_iframe_title_still_fails_generation`,
  `test_no_active_pip_install_anywhere`.

### Totals
Frontend unit 143 → **177**; standalone Playwright 40 → **50**; built-book
Playwright 13 → **16**; Python unittest 73 → **97**.

---

## 10. Commands run (no repository mutation beyond local commits)

```
git fetch origin --prune
git switch -c feature/course-pages-and-eda-trim
git add WPs/WP09_COURSE_PAGES_AND_EDA_TRIM.md
git commit -m "checkpoint: before WP09"                 # 2c3a165
git tag -a wp09-start -m "Checkpoint before WP09 (course pages and EDA trim)"
# … implementation …
python scripts/export_widget_data.py --refresh --artifact all
python scripts/build_portable_notebook.py --write
# full baseline + targeted verification (see report)
git add -A ; git reset -- WPs/reports/
git commit -m "WP09: course pages, streamlined EDA lesson, table-inspection activity"   # 13ab778
git add WPs/reports/WP09_REPORT.md WPs/reports/WP09_EXACT_CHANGELOG.md
git commit -m "WP09 report: document course pages and EDA streamlining"
```

No `git reset --hard`, `git checkout -- <path>`, `git clean`, `git rebase`,
`git revert`, `git push`, `git merge`, `--force`, or `--force-with-lease`. No
repository setting, secret, branch-protection rule, or Pages configuration
changed. No `book/_build`, `book/.jupyter_cache`, `book/_static/widgets/app`,
`interactive/node_modules`, `__pycache__`, or Playwright artifact staged.
