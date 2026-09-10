# WP09 implementation report — course pages, streamlined EDA lesson, and interactive data inspection

## Outcome

Status: **SUCCESS**

All fifteen numbered sections of `WPs/WP09_COURSE_PAGES_AND_EDA_TRIM.md` were
implemented on a new feature branch off the deployed `main`, and the full WP08
baseline plus every targeted test is green:

| Check | Before WP09 | After WP09 |
|---|---|---|
| Frontend typecheck | PASS | PASS |
| Frontend unit (`vitest`) | 143 / 143 | **177 / 177** |
| `npm audit --omit=dev` | 0 vulnerabilities | 0 vulnerabilities |
| Frontend production build | PASS (pre-existing 500 kB chunk note) | PASS (same note) |
| Widget artifact `--check --artifact all` | both valid + canonical | **both valid + canonical** (regenerated) |
| Python unit (`unittest discover -s tests`) | 73 / 73 | **97 / 97** |
| Portable notebook `--check` | up to date (84 cells) | **up to date (78 cells)** |
| Portable notebook smoke (out of repo) | 23 code cells, key values matched | **21 code cells, key values matched** |
| Standalone Playwright | 40 / 40 | **50 / 50** |
| Clean Jupyter Book build | build succeeded, **9 warnings** | build succeeded, **2 warnings** |
| `*.err.log` guard | empty | empty |
| Built-book Playwright | 13 / 13 | **16 / 16** |
| 3× consecutive clean builds, deterministic figures | identical (6 PNGs) | **identical (5 PNGs)** |

No merge to `main`, deployment, push, force push, destructive git command,
repository-setting change, or generated build-output commit occurred. The
generic sphinx-book-theme download control was not touched. No next practice
notebook was created.

## 1. Checkpoint and branch safety (WP09 §1)

- Start branch: `main` at `6d8c1f67bdac2af9c131919be72fb43dcb813598`
  (`WP08 report: document main deployment`); `main` == `origin/main` (verified
  before and after `git fetch origin --prune`; fetch added nothing new).
- New branch **`feature/course-pages-and-eda-trim`** created from that `main`.
- Only uncommitted item at start: untracked `WPs/WP09_COURSE_PAGES_AND_EDA_TRIM.md`
  (the WP brief). No build output, cache, `.DS_Store`, credential, token, or
  private data present.
- **Checkpoint commit: `2c3a165c7eba85c922c7df95a760aeaf9c91b232`**
  (`checkpoint: before WP09`) — adds the WP brief only (1 file, +454 lines).
- **Annotated tag: `wp09-start`** → `2c3a165` (tag object
  `49ab764ca9eb47243f4d0506293cb68131154401`). The name was free; **no numeric
  suffix** was needed.
- WP08 baseline was run in full **before** any implementation change and is
  recorded in the table above (left column).
- No `git reset --hard`, `git checkout -- <path>`, `git clean`, `git rebase`,
  `git revert`, history rewrite, or force-push at any point.

## 2. Rename the course (WP09 §2) — SUCCESS

`Machine Learning for Neuroscience` is now used consistently:

| Location | Before | After |
|---|---|---|
| `book/_config.yml` `title` | `Machine Learning for Neuroscientists` | `Machine Learning for Neuroscience` |
| `book/intro.md` heading + body | `...for Neuroscientists` | `...for Neuroscience` |
| `book/README.md` line 2 | "Computational Learning for Neuroscience course Tel Aviv University" | "Machine Learning for Neuroscience course, Tel Aviv University" |
| Portable-notebook banner | (no course name) | names **Machine Learning for Neuroscience** |

Rendered check: `book/_build/html/intro.html` `<title>` is
`Introduction — Machine Learning for Neuroscience`; the primary sidebar brand
reads `Machine Learning for Neuroscience`. No literal Markdown asterisks in YAML
or HTML titles. Historical WP reports were not renamed. Root `README.md` line 7
("adapted from …") is an **attribution to a different prior course** that happens
to share the name and was left untouched.

## 3. Introduction page (WP09 §3) — SUCCESS

`book/intro.md` is the book root and appears first (before Syllabus and
Contents). It is a concise professional page (three short sections: intro
paragraph, *Using the notebooks*, *About the questions*) covering every
requested concept:

- practice-session materials for **Machine Learning for Neuroscience**;
- each notebook follows a short PowerPoint on **Moodle** (named, **no URL**);
- for the in-class session *or* self-study at home at the student's own pace;
- some activities work interactively on the published page with nothing to
  install;
- students are encouraged to run the code and experiment by changing it;
- each notebook provides Colab and downloadable `.ipynb` controls;
- questions are deliberately placed before some explanations to promote deeper
  reasoning, and their style is close to course assessment / exam questions;
- some questions have a revealable reasoning guide; genuinely open questions
  have no single correct answer.

No time budget, no "every question has an answer" claim, no Moodle link, no long
setup guide, no marketing copy. Restrained rust/cream style (plain Markdown,
theme defaults). `tests/test_book_structure.py` asserts every one of these.

## 4. Syllabus / Contents structure (WP09 §4) — SUCCESS

- `book/_toc.yml` was already valid and in the required order
  (`root: intro`; `chapters: [syllabus, contents → sections → exercise_01]`), so
  no change was needed there.
- `book/syllabus.md` is now **title-only**: exactly `# Syllabus`. This removes
  the **7 repeated `syllabus` toctree-title warnings** at the source (not
  suppressed). No invented dates / weights / prose.
- `book/contents.md` keeps `# Contents` + `{tableofcontents}`, ready to list
  future practices.
- Rendered navigation order (sidebar and prev/next), verified in
  `book/_build/html`:
  **Introduction → Syllabus → Contents → Exercise 1** — prev/next chain checked
  page-by-page (`intro → syllabus → contents → exercise_01`). Syllabus builds,
  opens, and appears in both the table of contents and the primary sidebar.

## 5. Remove the duplicated Exercise I introduction (WP09 §5) — SUCCESS

`book/chapters/chapter_01/exercise_01.ipynb`:

| Cell (stable id) | Action |
|---|---|
| `b483f85f-…` H1 "Exercise 1 — …" | retained unchanged |
| `c4d5e6f7a8b9` "Run or download this notebook" admonition | retained, compact; "three embedded activities" → "four" |
| `a1b2c30d4e5f` "## About this exercise" | **removed** |
| `b2c3d40e5f6a` "How to use this notebook" admonition | **removed** |
| `6d0ba51b-…` "## Learning objectives" | **removed** |
| `373d8862-…` "What this notebook covers" | **retained**, edited to the shortened lesson; heading raised `###` → `##` (see §Warnings); a concise **Prerequisites** line added here, **NumPy removed** from it |

Local ABIDE-II context needed to understand the analysis (the "Loading the
ABIDE-II phenotypic data" dropdown, the site/diagnosis explanations) was kept.

## 6 & 13. Portable notebook self-contained for setup + private-repo readiness — SUCCESS

`scripts/build_portable_notebook.py`:

1. The canonical notebook's data-loading cell (`bd37a40a-…`) no longer fetches
   the column list from `raw.githubusercontent.com/.../main/…`. It now reads the
   local single source of truth,
   `json.loads(Path("../../config/eda_phenotype_columns.json").read_text())`,
   which the Jupyter Book build resolves in-repo. **Neither notebook instructs
   students to obtain requirements or config from the repository.**
2. The portable generator embeds that list as a literal `CURATED_COLUMNS = [...]`
   and drops the now-unused `json` / `pathlib` imports.
3. The portable **Setup** markdown cell was rewritten with **no** `requirements.txt`
   / repository wording, and a new **code cell** `portable-setup-install` was
   added:
   ```python
   # If an import below fails, uncomment and run this line once, then
   # restart the kernel. Safe on Colab, VS Code and Jupyter.
   # %pip install numpy pandas matplotlib seaborn
   ```
   The install line is **commented out** — never run automatically. The package
   list was taken from the notebook's actual `import` lines (numpy, pandas,
   matplotlib, seaborn; `json` / `pathlib` / `IPython` are always available;
   `scipy` is gone with the removed Cramér's V cell). Build/test tooling is
   excluded.
4. No private/local repository path appears in the portable notebook.
5. The portable notebook stays a deterministic generated derivative
   (`--check` passes; `test_repeated_builds_are_byte_identical` passes).
6. The verified Colab / raw-download controls are preserved verbatim on `main`.
7. Runtime data dependency: the pinned ABIDE-II CSV in the third-party public
   repo `neurohackademy/nh2020-curriculum` (immutable commit), unaffected by
   this repo's visibility.

`_assert_portable` was hardened to reject `../../config/`, `requirements.txt`,
`CURATED_COLUMNS = json.loads`, and any active `%pip`/`!pip` line, and to require
the commented install cell.

**Private-repository implication (needs Yoav):** the Colab / raw-download
buttons still target `github.com/yoavmp/ml-neuro-tutorials` on `main`. If that
repository becomes private, `colab.research.google.com/github/yoavmp/…` and
`raw.githubusercontent.com/yoavmp/…/main/…` will stop working for students who
are not collaborators — Google/GitHub cannot read a private repo on the
student's behalf. This is **not** changed here. Recommended future stable
distribution (Yoav's call): publish the portable `.ipynb` as a GitHub **Release
asset** or on a small dedicated **public** repo, or serve it from the Pages site
itself and point the Colab button at that public URL. The column config is no
longer a private-repo risk (local read + embed).

## 7. Reduce the ABIDE phenotypic table to 13 columns (WP09 §7) — SUCCESS

The actual ABIDE-II CSV (1114 rows × 348 columns, SHA-256
`537e541114884f63a2e736ba4d223a816dd013f701e56fb223ebe42e219e06f6`) was inspected
programmatically before selection (dtype, availability, missingness, site
coverage). The candidate SRS/ADOS subscale totals were rejected to avoid
redundant questionnaire subscales; `EYE_STATUS_AT_SCAN` (0.1 % missing) was
dropped as low teaching value; `ADI_R_SOCIAL_TOTAL_A` was added for a second
high-missingness numeric instrument.

### Final 13-column table

`book/config/eda_phenotype_columns.json` (the single source of truth):

| # | Column | Teaching role | Intended dtype | Overall missing % |
|---|---|---|---|---|
| 1 | `SITE_ID` | acquisition-site / scanner group identifier | `category` (from `str`) | 0.0 |
| 2 | `SUB_ID` | participant identifier | `string` | 0.0 |
| 3 | `DX_GROUP` | diagnosis group (1 = Autism, 2 = Control) | `category` (from `int`) | 0.0 |
| 4 | `AGE_AT_SCAN` | core demographic — age, continuous numeric | `float64` | 0.0 |
| 5 | `SEX` | core demographic — sex (1 = male, 2 = female) | `category` (from `int`) | 0.0 |
| 6 | `HANDEDNESS_CATEGORY` | additional categorical (1/2/3), light missingness | `category` (from `float`) | 2.1 |
| 7 | `FIQ` | numeric cognitive score, mostly complete | `float64` | 8.9 |
| 8 | `VIQ` | numeric cognitive score, moderate missingness | `float64` | 28.3 |
| 9 | `PIQ` | numeric cognitive score, moderate missingness | `float64` | 21.7 |
| 10 | `CURRENT_MED_STATUS` | additional categorical (0/1), moderate missingness | `category` (from `float`) | 11.0 |
| 11 | `SRS_TOTAL_RAW` | numeric symptom-scale total, moderate missingness | `float64` | 29.5 |
| 12 | `ADOS_G_TOTAL` | numeric autism-assessment total, high missingness | `float64` | 68.9 |
| 13 | `ADI_R_SOCIAL_TOTAL_A` | numeric autism-interview total, high missingness | `float64` | 72.9 |

Satisfies every §7 constraint: participant id, site id, diagnosis, age + sex,
two extra categoricals, five useful numerics, six variables with substantial
missingness (11 %–73 %), and four complete / mostly-complete numerics for
distributions and correlations. 13 columns (12–14 preferred).

### Every downstream dependency updated

- `scripts/export_widget_data.py`: `HISTOGRAM_VARIABLES` (7 numeric of the new
  table) and `RETENTION_VARIABLES` (11 non-identifier columns; `SITE_ID` re-added
  as the grouping label) rewritten; docstring updated.
- `book/_static/widgets/data/abide_histogram.json`,
  `book/_static/widgets/data/abide_retention.json`: regenerated with
  `--refresh --artifact all` and re-validated `--check` (canonical, deterministic).
- `book/_static/widgets/configs/eda_histogram.json`,
  `eda_retention.json`, `eda_correlation.json`: variable / group lists, default
  selections, and reflection prompts brought in line with the new columns.
- New `book/_static/widgets/configs/table_inspection.json` (§11).
- Notebook: data-loading + printed shape, categorical conversion list, `info()` /
  `describe()` examples, missingness summary + heatmap + by-diagnosis table,
  complete-case comparison, distribution summary set, correlation variable block,
  every Think first / Check-your-reasoning card, table text, and captions.
- All four browser activities (§11 implemented).
- Portable generator + smoke expected value.
- Frontend unit + Playwright + Python tests.

Search for every removed phenotype name (`ADOS_2_TOTAL`, `SCQ_TOTAL`,
`EYE_STATUS_AT_SCAN`, `SRS_COMMUNICATION_RAW`, `PDD_DSM_IV_TR`, `ADOS_MODULE`,
`FIQ_TEST_TYPE`, `SRS_VERSION`/`SRS_INFORMANT`, `HANDEDNESS_SCORES`, the CBCL /
BRIEF / MASC / RBSR / Vineland families, …) in executable code, displayed output,
activity controls/defaults, and active-table prose returns **nothing** — enforced
by `tests/test_notebook_corrections.py::test_no_stale_removed_phenotype_in_code_or_active_prose`.
The link to the full official ABIDE-II Data Legend remains, as allowed.

### Recomputed numeric results used in the lesson

All examples were recomputed from the revised 13-column table; the notebook was
re-executed end-to-end (0 errors) so committed outputs match.

| Result | Old (39-col) | New (13-col) |
|---|---|---|
| Printed data-table shape | `(1114, 39)` | `(1114, 13)` |
| `missing_summary` rows with missingness | ~30 | **8** (`ADI_R_SOCIAL_TOTAL_A` 72.9, `ADOS_G_TOTAL` 68.9, `SRS_TOTAL_RAW` 29.5, `VIQ` 28.3, `PIQ` 21.7, `CURRENT_MED_STATUS` 11.0, `FIQ` 8.9, `HANDEDNESS_CATEGORY` 2.1) |
| `describe().T` numeric rows | ~18 | **7** (`AGE_AT_SCAN`, `FIQ`, `VIQ`, `PIQ`, `SRS_TOTAL_RAW`, `ADOS_G_TOTAL`, `ADI_R_SOCIAL_TOTAL_A`); statistics for retained variables unchanged |
| `missing_by_diagnosis` (autism / control %) | 15 rows | 8 rows; e.g. `ADI_R_SOCIAL_TOTAL_A` 42.0 / 100.0, `ADOS_G_TOTAL` 42.2 / 92.2 |
| `retention_comparison` "complete for all N" | all 39 → **1** (0.1 %) | all 13 → **95** (8.5 %) |
| `retention_comparison` core `{SITE_ID,DX_GROUP,AGE_AT_SCAN,SEX,FIQ}` | 1015 (91.1 %) | 1015 (91.1 %) — unchanged |
| FIQ median imputation | 112.0, 99 imputed | 112.0, 99 imputed — unchanged |
| `CURRENT_MED_STATUS` fill counts | 824 / 167 / 123 | 824 / 167 / 123 — unchanged |
| IQR range check on `AGE_AT_SCAN` | fences `[-3.8, 31.1]`, **56 / 1114** flagged | fences `[-3.8, 31.1]`, **56 / 1114** flagged — unchanged; prose "roughly 31–64" → "roughly 33 to 64" (min flagged age 32.6) |
| FIQ-by-diagnosis printout | Autism 479 / 108.0 / 106.6 · Control 536 / 115.0 / 114.9 | same (FIQ column unchanged); title "FIQ recorded for 1,015 of 1,114" kept |
| Distribution summary set | `[AGE_AT_SCAN, FIQ, SRS_TOTAL_RAW, SCQ_TOTAL, ADOS_G_TOTAL]` | `[AGE_AT_SCAN, FIQ, SRS_TOTAL_RAW, ADOS_G_TOTAL, ADI_R_SOCIAL_TOTAL_A]` |
| Correlation variable block | 8 vars incl. `SRS_COMMUNICATION_RAW`, `SCQ_TOTAL` | 7 vars: `AGE_AT_SCAN, FIQ, VIQ, PIQ, SRS_TOTAL_RAW, ADOS_G_TOTAL, ADI_R_SOCIAL_TOTAL_A` |
| Pearson matrix key cells | — | `FIQ~VIQ` 0.83, `FIQ~PIQ` 0.84, `VIQ~PIQ` 0.52, `SRS~ADOS_G` 0.30, `SRS~ADI_R` 0.31, `AGE~ADOS_G` −0.23 (Spearman −0.33), `FIQ~SRS` −0.24 |
| Removed statistics | pairwise-N matrix; `SEX × DX_GROUP` crosstab; Cramér's V ≈ 0.18 | removed |
| Synthesis-challenge model answer (`VIQ`/`PIQ`) | n ≈ 786, Pearson ≈ 0.52, Spearman ≈ 0.49 | still accurate (n 786, r 0.517, ρ 0.493) — unchanged |

## 8. Shorten statistical inspection (WP09 §8) — SUCCESS

- `#### Interpreting \`info()\`` (`3ad75c70-…`) and `#### Interpreting \`describe()\``
  (`5284a2b7-…`) sections **removed**.
- One caveat folded into `### Dataset structure with \`info()\`` (`4116a60a-…`):
  *"…useful for … shape, … data types, … non-null counts … but it says nothing
  about the distribution of the values inside a column."*
- One caveat folded into `### Numerical summaries with \`describe()\``
  (`0adaedf8-…`): *"…a single row of numbers can hide differences between groups
  or sites, and the `count` column is the reminder that each statistic is
  computed only from the observations that are actually present."*
- Wording kept first-time-EDA friendly; no orphaned questions
  (the adjacent Think first cards still stand on their own).

## 9. Reduce the missing-data approaches table (WP09 §9) — SUCCESS

`### Common approaches to missing data` (`a6028127-…`): the ~10-row table is now
**3 body rows**:

| Approach | When it is useful | Main caution |
|---|---|---|
| **Remove** incomplete rows or a whole variable | little data lost, missingness plausibly unrelated to the question | shrinks the sample; can bias it |
| **Impute** — simple (mean/median/mode), model-based (e.g. KNN), or multiple imputation | a complete table is required and other variables inform the gaps | understates uncertainty; distorts relationships; parameters from training data only |
| **Keep missingness explicit** — indicator, "not recorded" category, or a method that accepts missing data | the fact a value is missing may itself be informative | the model may learn the data-collection procedure, not biology |

All imputation subtypes are one row. The closing sentence keeps the essential
principle and adds "no one strategy is always best"; the surrounding ABIDE
application (`### Common approach:`, `5e1f6598-…`) already matched and was left.

## 10. Trim the correlation section (WP09 §10) — SUCCESS

Removed:

- `### When a correlation matrix is the wrong tool` (`e15470791c85`);
- the *Participants behind each correlation* pairwise-N code + graph (`c4dc9fe3ee9e`)
  and the four-bullet "Read the two matrices together" interpretation;
- the `SEX × DX_GROUP` crosstab code (`2c5625b060d7`), the Cramér's V sidebar
  (`458219f7acdb`), and their Think first card (`1e00b5ffc77d`).

Retained and updated:

- `### Pearson and Spearman correlations` (`fd14e7f5d7a7`) — kept the compact
  Pearson-vs-Spearman comparison table; dropped the "sample behind each number"
  framing.
- The Pearson lower-triangle heatmap (`9b478759eff3`) — now the 7 curated numeric
  variables; figure size trimmed.
- A short 3-bullet observation list + **Practical takeaway** (`188d49e2ebf5`),
  stated briefly, no participant-count discussion, no causal language, and the
  `SRS_TOTAL_RAW`/`SRS_COMMUNICATION_RAW` part-whole example replaced with the
  genuine `FIQ`–`VIQ`/`PIQ` definitional case. All coefficients recomputed and
  in agreement with the displayed matrix.
- The correlation explorer (`eda_correlation.json`) kept — variable list, the
  "ADOS-G vs ADI-R" prompt, and the Think first pair updated.

## 11. `head()` / `tail()` / `sample()` activity (WP09 §11) — SUCCESS

### New reusable activity type `table-inspection`

Built on the WP01–WP07 TypeScript/Vite/config-driven architecture, **not**
notebook-specific DOM:

- `interactive/src/table-inspection.ts` — pure, unit-tested maths:
  `mulberry32` PRNG, `sampleRowIndices` (full Fisher–Yates, returned
  ascending), `selectRowIndices(method, …)`, `summariseView` (distinct sites in
  first-appearance order, missing cells over the displayed columns),
  `formatCell`.
- `interactive/src/components/table-inspection.ts` — a `<fieldset>` radio group
  (`head()` / `tail()` / `sample()`), a `Rows` range input, a `Reshuffle sample`
  button (advances the seed), an accessible `<table>` (`<caption>`, `<th scope>`,
  sticky header) inside an `overflow-x` scroll box, and a live evidence summary
  (`role="status"`). Missing cells get `.widget-cell-missing` and a
  visually-hidden "missing" label — clearly *missing*, never *error*. Reuses
  `parseAbideRetentionData` + `abide_retention.json` (no `SUB_ID`, no new
  CDN/runtime dependency).
- `interactive/src/config.ts` — a `table-inspection` member of the discriminated
  union with a strict Zod schema + cross-field checks (site field must be a
  displayed column, methods no-dup, `defaultMethod ∈ methods`,
  `rowCount.min ≤ default ≤ max`, `sampleSeed` required when `sample` is offered).
- Registered in `interactive/src/components/registry.ts`; styles in
  `interactive/src/styles.css`.

### Config and default selection

`book/_static/widgets/configs/table_inspection.json`: `methods` head/tail/sample,
`defaultMethod` **head**, `rowCount` `{min 5, max 15, default 8}`, `sampleSeed`
**7**, 8 display columns
(`SITE_ID, DX_GROUP, AGE_AT_SCAN, SEX, HANDEDNESS_CATEGORY, FIQ, SRS_TOTAL_RAW,
ADOS_G_TOTAL`).

### Data actually supports the intended observation (verified)

The ABIDE-II table is sorted by site (19 runs = 19 sites), so:

| View (n = 8) | Acquisition sites | Missing display cells |
|---|---|---|
| `head(8)` (default) | **1** — `ABIDEII-BNI_1` | **0 / 64** |
| `tail(8)` | **1** — `ABIDEII-USM_1` | **19 / 64** |
| `sample(8, seed 7)` | **8** — BNI/KKI/KUL_3/NYU_2/OHSU/SDSU/TCD/USM | **7 / 64** |

`head()`/`tail()` each concentrate on one site; the deterministic sample spreads
across many. The lesson is written around this observed behaviour. The exact
seed-7 draw (`rows [12, 482, 585, 680, 773, 858, 976, 1098]`) was cross-checked
with an independent Python re-implementation of `mulberry32` + Fisher–Yates over
the real 1114-row table (`table-inspection.test.ts`).

### Pedagogical sequence in the notebook (start of "2. Data inspection")

The single random-sample cell (`7af020ab-…`, `phenotypes.sample(n=8,
random_state=42)`) and its "### Inspecting a random sample" heading (`c80dce59-…`)
were removed, along with the advance claim that `head()`/`tail()` "may not
represent the entire dataset" / a random sample gives a "broader first
impression". New order:

1. `3e4d2fad-…` — neutral prompt: pandas offers `head()`, `tail()`, `sample()`,
   custom selection; *which gives the best first impression?*
2. `7a1e5c93d201` — the `table-inspection` iframe
   (`title="Interactive head, tail, and sample comparison for the ABIDE-II table"`).
3. `7a1e5c93d202` — **Think first**: how many sites in `head()`/`tail()`? in
   `sample()`? what happens to missingness? which view for a first broad look,
   and what can a small sample still not promise?
4. `7a1e5c93d203` — concise explanation: `head()`/`tail()` deterministic &
   good for ordering/schema; a random sample exposes wider variety in an ordered
   multi-site table; a small sample is not guaranteed representative;
   `random_state` just makes one draw reproducible.
5. `7a1e5c93d204` — collapsed (`hide-input`) Python equivalent:
   `phenotypes.head(8)`, `phenotypes.tail(8)`,
   `phenotypes.sample(8, random_state=0)`.

The retained Think first (`ea35b076-…`) at the end of the section was reworded to
refer to "the views above" and does not duplicate the new card.

### Activity tests

- **Unit** (`interactive/tests/table-inspection.test.ts`, 23 tests): mulberry32
  determinism / range, exact head/tail selection + clamping, deterministic
  sample + the exact seed-7 draw, a different seed → a different draw, unknown
  method throws, `summariseView` site/missing-cell counts, head-vs-tail site
  concentration, and cross-checks against the committed `abide_retention.json`
  (`head(8)`→1 site/0 missing, `tail(8)`→1 site/19 missing,
  `sample(8, seed 7)`→8 sites/7 missing).
- **Config** (`interactive/tests/config.test.ts`, +11 tests): schema + semantic
  validation, unknown-method / bad-`defaultMethod` / missing-`sampleSeed` /
  site-field-not-a-column / duplicate-column / out-of-range-`rowCount.default` /
  empty-`methods` / strict-extra-key rejection, and the shipped
  `table_inspection.json` validates.
- **Standalone Playwright** (`interactive/e2e/table-inspection.spec.ts`, 10 tests
  = 5 × site-root + project-subpath): head/tail deterministic pandas-equivalents,
  fixed seeded sample, Reshuffle → seed 8 and a changed site set, reload restores
  defaults, row-count control changes rows + `data-total-cells`, missing cells
  marked accessibly and never called an error, radio group keyboard-operable
  (`ArrowDown`), narrow-viewport table scrolls within its box while the document
  does not scroll horizontally, and a no-CDN/kernel/off-origin/socket audit.
- **Built-book Playwright** (`interactive/e2e-book/chapter01.spec.ts`, +3 tests):
  the iframe loads on the real Chapter 1 HTML under the Pages subpath,
  config + data are HTTP 200, `head(8)` defaults (`data-sites` `ABIDEII-BNI_1`,
  0 missing), switching to `sample()` gives 8 sites / 7 missing and changes the
  rows, reload restores `head`, narrow-viewport row-count change, and a
  no-CDN/kernel/socket audit.

## 12. Design and visibility pass (WP09 §12) — SUCCESS

Conservative pass only (no redesign):

- revealable **Check your reasoning** dropdowns kept where they add value
  (skew / small-N / definitional-correlation / range-check reasoning); no answer
  added to open questions;
- loading / figure code stays `hide-input` / `hide-cell`; short instructive code
  (`categorical_columns`, `retention_comparison`, `imputation_demo`, the Python
  `head/tail/sample`) stays visible;
- empty headings, orphan answers, duplicated intros, and awkward
  post-deletion transitions removed; the leading `### What this notebook covers`
  was raised to `##` (it followed the deleted `## Learning objectives`).

**Counts recounted from the final notebook:**

| | Value |
|---|---|
| Total cells | **76** (was 84) |
| Markdown cells | 56 |
| Code cells | **20** (was 23) |
| — visible | **10** |
| — `hide-input` | **8** |
| — `hide-cell` | **2** |
| — `hide-output` | **0** |

All retained cells keep their stable ids; the 4 new cells use fixed unique ids
`7a1e5c93d201`–`7a1e5c93d204`. `nbformat.validate` passes; ids are unique; the
only tags anywhere are `hide-input` / `hide-cell`.

## 14. Required verification (WP09 §14)

| # | Requirement | Result |
|---|---|---|
| 1 | course title exactly *Machine Learning for Neuroscience* in config + rendered nav/title | **PASS** (`_config.yml`; `intro.html` `<title>` and sidebar brand) |
| 2 | sidebar + prev/next order Introduction → Syllabus → Contents → Exercise I | **PASS** (prev/next chain checked page-by-page) |
| 3 | Syllabus title-only, builds, opens, no title/toctree warning | **PASS** (`# Syllabus`; the 7 warnings are gone) |
| 4 | Introduction has every requested concept, no Moodle link, no time estimate, no answer guarantee | **PASS** (`test_book_structure.py`) |
| 5 | Exercise I: no About/How-to/Learning-objectives duplicates; keeps *What this notebook covers* + compact Colab/download control | **PASS** (`test_notebook_corrections.py`) |
| 6 | NumPy absent from stated prerequisites | **PASS** |
| 7 | final table 10–15 configured columns; all code/prose/artifacts use it | **PASS** (13 columns) |
| 8 | no stale removed-variable reference | **PASS** (`test_no_stale_removed_phenotype_in_code_or_active_prose`) |
| 9 | `info()`/`describe()` interpretation sections absent; caveats concise + earlier | **PASS** |
| 10 | missing-data approaches table ≤ 3 body rows | **PASS** (3) |
| 11 | requested correlation material removed; remaining claims match recalculated values | **PASS** |
| 12 | new inspection activity works and teaches from observed data | **PASS** (built-book + standalone Playwright; lesson written around the observed head/tail/sample behaviour) |
| 13 | all four browser activities render + respond in the built book | **PASS** (built-book Playwright 16/16) |
| 14 | portable notebook deterministic, self-contained for setup, executes outside the repo | **PASS** (`--check`; smoke, 21 code cells, out of repo) |
| 15 | clean Jupyter Book build: no `*.err.log`, no newly introduced warning | **PASS** (2 warnings, both pre-existing: `logo.png` missing, `book/README.md` not in a toctree; the 7 `syllabus` warnings eliminated) |
| 16 | existing functionality + repaired sidebar remain green | **PASS** (sidebar-toggle regression 4/4; all prior activity tests updated + green) |

### Visual inspection (desktop 1280 px + narrow 390 px)

Screenshots were captured to the session scratchpad (not committed — the repo has
no documented screenshot location):

- **Introduction** — clean three-section page, restrained rust/cream, sidebar
  `Introduction / Syllabus / Contents`, "Next → Syllabus".
- **Syllabus** — single `# Syllabus` heading, prev "Introduction" / next
  "Contents".
- **Contents** — heading + generated table of contents listing Exercise 1.
- **Exercise I opening** — H1, "Run or download this notebook" card,
  "What this notebook covers" (`##`) with the NumPy-free prerequisites line.
- **New inspection activity** — Method radio group, Rows slider (8),
  Reshuffle button, evidence line ("head() shows 8 rows from 1 acquisition site
  (ABIDEII-BNI_1); 0 of 64 cells are missing." / "sample() … 8 acquisition sites
  … 7 of 64 cells are missing."), accessible table with `phenotypes.head()` /
  `phenotypes.sample() — 8 rows, seed 7` caption; usable at 390 px with the table
  scrolling inside its own box and the page not scrolling horizontally.
- **Missing-data table** — 3 body rows.
- **Shortened correlation ending** — Pearson matrix, 3-bullet observations, a
  one-paragraph Practical takeaway, then the explorer and the synthesis
  challenge; no "wrong tool" detour.

## Warnings, deviations, deferred / not-performed checks

1. **New heading level** — raising `### What this notebook covers` to `##` was
   necessary because the preceding `## Learning objectives` was deleted; leaving
   `###` produced a new "Non-consecutive header level increase; H1 to H3"
   warning. With the change, the clean build has **only the 2 pre-existing
   warnings**.
2. **Pre-existing build warnings kept** — `logo.png` missing and
   `book/README.md` not in any toctree. Both predate WP09 and are out of scope.
3. **Pre-existing Vite chunk note** — the ~1.5 MB Plotly bundle still trips
   Vite's 500 kB advisory. Unchanged behaviour.
4. **Colab interactive rendering not machine-verified** — Google serves an app
   shell / auth wall to headless automation (same as WP07/WP08). URL structure
   and the raw target are verified by the notebook-content tests.
5. **No live / remote checks** — by the stop condition: no push, no `main`
   merge, no deployment. The GitHub Pages site is unchanged and still serves the
   WP08 content.
6. **`git pull --ff-only`** was not needed — local `main` already equalled
   `origin/main` and `git fetch` brought no new commits.
7. Cross-platform Matplotlib figure bytes may differ between this macOS run and
   Linux CI (numpy/pandas/matplotlib unpinned, flagged since WP07). Figures are
   byte-deterministic *within* an environment (3 consecutive clean builds →
   identical hash set).

## Unresolved risks / needs Yoav

- **Private-repository distribution** (see §6/§13): the Colab / raw-download
  buttons target `github.com/yoavmp/ml-neuro-tutorials` on `main`; they will
  break for non-collaborators if the repo goes private. A future public
  distribution method (Release asset / dedicated public repo / Pages-hosted
  `.ipynb`) is recommended but **not** implemented, and hosting scope was not
  changed.
- Release / deployment of WP09 is a separate, later WP after review.

## Confirmation of safety constraints

- **No merge to `main`, no deployment, no push** (nothing left the local
  `feature/course-pages-and-eda-trim` branch).
- **No force push**, **no `--force-with-lease`**.
- **No destructive git command** — no `git reset --hard`, `git checkout -- <path>`,
  `git clean`, `git rebase`, `git revert`, tag deletion, or branch deletion.
- **No repository-setting change** — no secret, Actions permission, branch
  protection, or Pages configuration touched.
- **No generated build output committed** — `book/_build`, `book/.jupyter_cache`,
  `book/_static/widgets/app`, `interactive/node_modules`, `__pycache__`, and
  Playwright artifacts remain untracked / git-ignored (verified against the
  staged file list).
- **The generic theme download control was not removed.**
- **No next practice notebook was created or started.**

## Key identifiers

| Item | Value |
|---|---|
| Branch | `feature/course-pages-and-eda-trim` (off `main` `6d8c1f6`) |
| Checkpoint commit | `2c3a165c7eba85c922c7df95a760aeaf9c91b232` (`checkpoint: before WP09`) |
| Checkpoint tag | `wp09-start` → `2c3a165` (annotated; tag object `49ab764ca9eb47243f4d0506293cb68131154401`; no suffix needed) |
| Implementation commit | `13ab778075c300695959eb2065448b7e8778940e` (`WP09: course pages, streamlined EDA lesson, table-inspection activity`) |
| Report commit | `WP09 report: document course pages and EDA streamlining` — adds `WPs/reports/WP09_REPORT.md` + `WPs/reports/WP09_EXACT_CHANGELOG.md` only. Its hash is recorded in the session terminal summary (a report cannot contain its own hash). |

## Instructions for reviewer

Paste this entire report (`WP09_REPORT.md`) into the ChatGPT conversation that
produced WP09. `WP09_EXACT_CHANGELOG.md` is the companion location-specific
before/after record.
