# WP06 — exact change log

Location-specific record of every substantive change made in WP06. It lets you
identify precisely what changed without diffing notebook JSON.

- Notebook: `book/chapters/chapter_01/exercise_01.ipynb`
  (79 cells → **81 cells**: two markdown cells added to the opening; no cell
  deleted or merged; every pre-existing cell ID preserved).
- Cell numbers below are the **new** 0-based positions; the 12–36 hex cell ID is
  the stable anchor.
- Regenerated execution counts and figure-image hashes from a clean rebuild are
  **not** listed as substantive changes (see note at the end).

Categories used: `factual`, `code`, `clarity`, `terminology`, `grammar`,
`structure`, `cell type`, `metadata visibility`, `output cleanup`,
`visual formatting`, `accessibility`.

---

## 1. Notebook — corrections (prose)

| ID | Cell ID / location | Category | Before | After | Reason / evidence |
|---|---|---|---|---|---|
| C1 | cell 0 · `b483f85f-c9f3-4477-8760-a7ca434338d0` · H1 title | clarity / grammar | `# Exercise I: Exploratory Data Analysis (EDA)` (only the heading; no purpose text) | `# Exercise 1 — Exploratory data analysis (EDA)` **plus a new one-paragraph purpose statement** ("This exercise applies **exploratory data analysis (EDA)** to the phenotypic table of the Autism Brain Imaging Data Exchange II (ABIDE-II)… The aim is not a predictive model but a defensible understanding of the data before any modelling begins.") | WP §5.1: title + one-paragraph purpose. Roman "I" → "1" and sentence-case to match the numbered sections ("## 1.", "## 2." …). |
| C2 | cell 3 · `6d0ba51b-5219-4743-8c9a-e37126224d86` · "## Learning objectives" | clarity / structure | 6 bullets, title-case, imperative-noun style: "Inspect the dimensions and variables of a dataset / Distinguish categorical and numerical variables / Identify missing values and unusual observations / Visualize univariate and multivariate distributions / Detect potential confounding variables / Formulate questions for subsequent predictive analysis" | 8 bullets with observable verbs, matched to the sections that now exist: inspect rows/schema/types/summaries; convert encoded variables to categoricals; quantify missingness and reason about site/diagnosis; compare keep/drop/impute strategies **and explain why imputation parameters must be learned from training data only**; describe and compare distributions (centre, spread, skew, group differences); flag unusual values without deleting them; choose an association view matching the variable types; interpret Pearson/Spearman alongside pairwise-complete N and grouping/confounding | WP §5.6. Old list under-described the finished notebook (no categoricals objective, no leakage objective, no pairwise-N / association-view objective) and promised "predictive analysis" the notebook does not do. |
| C3 | cell 4 · `373d8862-c5df-49a8-9295-a3e4fc073d0f` · was "### Before we begin" | structure / clarity | `### Before we begin` + informal note: "When we load data or perform actions that are less relevant for the current session, we will sometimes hide code cells to make the notebook simpler. However, you can check them out and expand your knowledge!" | `### What this notebook covers` + a 5-item numbered roadmap that mirrors the actual H2 headings (Importing and data loading / Data inspection / Statistical inspection / Missing values / Distributions and feature correlations), each with a one-line scope note | WP §5.7 (compact roadmap). The old note only explained collapsible code, which is now covered — without the "expand your knowledge" phrasing — by the new "How to use this notebook" callout (A2). |
| C4 | cell 21 · `2545ca48-c2bc-4f91-8ddf-fe5f625c62c8` (SUB_ID/category explanation) | clarity / terminology | "…pandas now simply knows that they represent categories rather than quantities with **a relative distance**." and a trailing parenthetical: "(If you are not sure what the variable stands for - ask the researchers who collected the data! Or in this case - just google it!)." | "…rather than quantities with **a meaningful distance between them**." and a plain closing sentence: "When the meaning of a coded variable is unclear, consult the study's data legend or the people who collected it rather than guessing." | WP §3 (register consistency; "too absolute/ambiguous"). "a relative distance" was ambiguous; the "just google it!" aside is out of register for a university course notebook. |
| C5 | cell 26 · `5284a2b7-51c1-420e-b7e9-385b64dd70ec` · "#### Interpreting `describe()`" → Limitations, bullet 1 | grammar | "- Categorical variables (with `Dtpye = Category`) are excluded by default." | "- Categorical variables are excluded by default (their dtype is `category`, not a numeric type)." | Typo `Dtpye` → and mixed-case `Category`; reworded so the parenthetical is accurate pandas terminology. |
| C6 | cell 7 · `81d44a95-6997-4559-8018-46a5d2847419` · `{dropdown} Loading the ABIDE-II phenotypic data` | clarity / factual | Body stated **both** "The complete phenotypic table contains several hundred variables" **and**, two paragraphs later, "The complete ABIDE-II phenotypic dataset contains 348 variables"; it also introduced the 39-variable subset twice. | One statement of the full size ("The full phenotypic table has 348 variables — …") and one statement of the subset ("For this exercise we use a curated subset of 39 … variables. The meaning and coding of every variable are documented in the official [ABIDE-II Phenotypic Data Legend](…)."). Same links, same facts. | WP §3 (redundant / internally inconsistent). "several hundred" vs "348" is a self-contradiction in one dropdown. 348 and 39 both re-verified against `phenotypes.shape` on the pinned CSV (1114 × 39) and the curated column list. |
| C7 | cell 45 · `5d9c625f-bc31-4153-ac26-b520a9307a50` · "### Imputing a numerical variable" | clarity / leakage (WP §3) | Two short paragraphs: imputation replaces missing values with estimates; we replace missing `FIQ` with the median observed `FIQ`; "We will work on a copy so that the original dataframe remains unchanged." | Same, **plus** an explicit forward-pointing warning: "Here the median is computed from every observed value, which is fine for a one-off illustration. In a real modelling pipeline the median would be learned from the **training split only** and then applied to the validation and test data; computing it from the whole dataset first lets information from the held-out participants leak into preprocessing. The end of this section returns to this point." | WP §3 explicitly requires the imputation example to prevent students learning data leakage *at the point of the example*, not only in the later summary (cell 54, `5e1f6598-…`, "### Common approach:", unchanged — still carries the full training-only statement). **No code changed** — the demo still computes a global median deliberately, now labelled as such. |
| C8 | cell 49 · `be03bb35-e899-41ee-8df9-fdd997d4116a` (short note after the FIQ-imputation `describe` comparison) | factual / clarity | "We filled the values without changing the distribution a lot. What would happen if we implemented this for all variables? Try it yourself!" | "Imputing 99 of 1,114 `FIQ` values at the median leaves the mean almost unchanged and lowers the standard deviation only slightly, because the share of imputed rows is small. The effect grows with the fraction of missing data and with how far the imputed constant sits from the rest of the distribution — and, as the dropdown above notes, it always removes genuine variability and weakens relationships with other variables." | The old text (a) understated the effect and sat awkwardly beside the "Important limitation" dropdown immediately above it, and (b) ended with "Try it yourself!" pointing at an activity that does not exist. New wording is quantitatively checked: on the pinned CSV, imputing the 99 missing `FIQ` values at the median (112.0) moves the mean 111.02 → 111.11 and the sd 15.48 → 14.78 (n 1015 → 1114). |

## 2. Notebook — question / answer structure

Every active question is now a **"Think first"** card
(` ```{admonition} … :class: think-first ``` `); every revealable answer that
was labelled "Answer" / "Answer for Q4" is now **"Check your reasoning"**. This
is a structural / visual-consistency change (WP §7). **Question and answer
wording is preserved verbatim**; where a `####` heading carried topic
information it reappears as a bold lead line inside the card.

| ID | Cell ID | Category | Before (first line) | After | Notes |
|---|---|---|---|---|---|
| Q1 | `ea35b076-ed3d-4712-a5ef-97ebc7bfa9f7` | structure | `### Questions for discussion` | `Think first` card; heading dropped | sample-rows question (3 items) unchanged |
| Q2 | `e05d9a3c-cf5d-4b7b-ba0c-92aa7659d389` | structure | `#### Questions` | `Think first` card; heading dropped | `info()` question (4 items) unchanged |
| Q3 | `be0fb829-7901-4143-b08c-9234bc9c8d19` | structure | `#### Identify the variables` | `Think first` card; **"Identify the variables."** kept as bold lead line | categorical-identification question (4 items) unchanged |
| Q4 | `831d596a-31c5-45d4-967b-3d75fee0b0cd` | structure | `#### Questions` | `Think first` card; heading dropped | `describe()` question (5 items) unchanged |
| Q5 | `d7865b58-dccd-4616-b054-6607f5316e96` | structure | `#### Questions` | `Think first` card; heading dropped | missingness question (4 items) unchanged |
| Q6 | `ac946108-fbcf-4009-b04c-dc75c5c5a68e` | structure | `#### Interpret the heatmap` | `Think first` card; **"Interpret the heatmap."** kept as bold lead line | heatmap question (4 items) unchanged |
| Q7 | `3dd2ae89-0043-4e29-9261-f5865851bf5e` | structure | `#### Questions` | `Think first` card; heading dropped | complete-case question (4 items) unchanged |
| Q8 | `c9c244ce-f0a8-44fd-80c0-c35009451f3c` | structure | `#### Question` | `Think first` card; heading dropped | "Not recorded" question (1 item) unchanged; its answer is Q16 below |
| Q9 | `0658e691-6ca7-4535-ba93-929ad0be6068` | structure | `### Questions` | `Think first` card; heading dropped | histogram question (5 items) unchanged |
| Q10 | `b32176a3b7f9` | structure | `#### Question: read the summary` + inline ` ```{dropdown} Answer ``` ` | split into a `Think first` card (**"Read the summary."** lead line) **and** a ` ```{dropdown} Check your reasoning ``` ` | question (3 items) and answer text unchanged |
| Q11 | `d9fa820679e0` | structure | `#### Question: confounding and composition` + inline `Answer` dropdown | split; lead line **"Confounding and composition."**; dropdown → `Check your reasoning` | text unchanged; numbers in the answer (521 Autism / 593 Control, KKI_1 ≈ 27/73 %, KUL_3 & NYU_2 100 % Autism, ≈ 70 % of females Control) re-verified on the pinned CSV |
| Q12 | `c374c2ec5540` | structure | `#### Question: evidence before editing a value` + inline `Answer` dropdown | split; lead line **"Evidence before editing a value."**; dropdown → `Check your reasoning` | text unchanged |
| Q13 | `3efbb7fdf9a7` | structure | `#### Question: use the explorer` + inline `Answer` dropdown | split; lead line **"Use the explorer."**; dropdown → `Check your reasoning` | text unchanged; ADOS pair n ≈ 81 and FIQ×SRS overall −0.24 / within-group ≈ 0 re-verified |
| Q14 | `1e00b5ffc77d` | structure | `#### Question: choosing an association measure` + inline `Answer` dropdown | split; lead line **"Choosing an association measure."**; dropdown → `Check your reasoning` | text unchanged; ≈ 70 % / ≈ 50 % and Cramér's V ≈ 0.18 re-verified (0.184) |
| Q15 | `7dd4a474-502a-42fb-a0dc-ca2ceef9f01a` | structure | ` ```{dropdown} Answer for Q4 ``` ` (standalone) | ` ```{dropdown} Check your reasoning — heatmap Q4 ``` ` | answer text unchanged |
| Q16 | `988ff5d1-966a-4d0d-a495-3ed09b42f276` | structure | ` ```{dropdown} Answer ``` ` (standalone, answers Q8) | ` ```{dropdown} Check your reasoning ``` ` | answer text unchanged |
| Q17 | `ae8f11ca42e5` · "### Synthesis challenge" | structure | `### Synthesis challenge` H3 + 6-item task list + ` ```{dropdown} A model reasoning process (not a single "right" answer) ``` ` | 6-item task list wrapped in a ` ```{admonition} Synthesis challenge :class: challenge ``` ` card; the "model reasoning process" dropdown (a checklist, not a single answer — WP §7.5) is **unchanged** | task text unchanged |

Not changed (deliberately): ` ```{dropdown} Important limitation ``` `
(`60259cf9-d15b-4fff-a2e8-f1740ed0bc13`, a note, not a Q&A answer) and
` ```{dropdown} Loading the ABIDE-II phenotypic data ``` ` (`81d44a95-6997-4559-8018-46a5d2847419`,
progressive-disclosure background — WP §7.6). Task prompts "### Design a
complete-case dataset" (`a7375aa6-59b3-4b2b-a02a-070f177a1610`) and "### Your decision" (`d19fa654-60f6-4db4-822d-43e57022aa52`) were
left as visible prose section leads because they introduce the retention
explorer rather than pose a check-your-answer question.

## 3. Notebook — metadata visibility (tag) changes

| ID | Cell ID | first line | Before tag | After tag | Reason |
|---|---|---|---|---|---|
| V1 | `69a9eef8-01f4-4135-937a-bac10ff445d8` | `# Can you find scores that were collected only for diagnosed participants?` (missing-by-diagnosis `groupby`) | `hide-cell` | `hide-input` | It is the evidence for the "missingness by diagnosis" answer (Q15 dropdown). Its output table should be visible for self-study; only the code collapses. |
| V2 | `b2d5e7b0-e038-4e94-aff4-35f6cd9ffa77` | `imputation_demo = phenotypes[[…]].copy()` (median-imputation demo) | `hide-input` | *(visible)* | WP §6 policy row "core EDA operations … input and essential output visible": `.median()` + `.fillna()` is an operation the student should read, not plotting boilerplate. |
| V3 | `70fdfc764608` | `# A deliberately short set…` (`describe().T` + available/missing N) | `hide-input` | *(visible)* | Same policy row — `describe` is a named core operation. |
| V4 | `7bf82a8cd5a9` | `age = phenotypes["AGE_AT_SCAN"]` (IQR fence + flagged rows) | `hide-input` | *(visible)* | Same policy row — the IQR rule is a named core operation; the cell is short and teaches the rule. |

No tag was **added**. `hide-cell` remains on: imports (`4ddc8b70-fd5d-40b5-bd93-7fbb43aea810`),
remote-data load (`bd37a40a-40a1-4ab3-9398-f539a2b61fca`), optional Cramér's V sidebar (`458219f7acdb`).
`hide-input` remains on the four plotting-boilerplate cells (missingness heatmap
`b7fb371d-8127-4b93-9d23-ad8c09e99d75`, retention comparison `33d94597-727c-4b58-a365-9ac1ecb4f365`, violin `80632a35b296`,
site×diagnosis heatmap `283362766ec1`, Pearson heatmap `9b478759eff3`,
pairwise-N heatmap `c4dc9fe3ee9e`) — six cells.

### Visibility counts (22 code cells)

| Presentation | Before | After |
|---|---|---|
| Visible (input + output) | 12 | **12** |
| `hide-input` (output visible) | 9 | **7** |
| `hide-cell` (collapsed) | 4 | **3** |
| `hide-output` | 0 | 0 |

(Net: V2/V3/V4 moved `hide-input`→visible, V1 moved `hide-cell`→`hide-input`, so
visible stays 12 by coincidence — three cells opened, one that was fully
collapsed is now half-open.)

## 4. Notebook — new cells

| New cell ID | Position | Category | Content |
|---|---|---|---|
| `a1b2c30d4e5f` | cell 1 (after title) | structure | `## About this exercise` — context (hands-on part of Chapter 1, follows the tutor presentation), the two intended modes (**Guided tutorial**, budget ~60–75 min; **Self-study**), and brief prerequisites (basic Python + first acquaintance with `pandas`/`NumPy`/`matplotlib`/`seaborn`; run cells top-to-bottom; internet needed on first run). WP §5.2–5.4. |
| `b2c3d40e5f6a` | cell 2 | structure | ` ```{admonition} How to use this notebook :class: how-to-use ``` ` — visible questions vs revealable answers, collapsed vs open code, three kernel-free browser activities. WP §5.5. |

## 5. Notebook — iframe framing (visual formatting)

| ID | Cell IDs | Category | Before | After |
|---|---|---|---|---|
| F1 | `999ad285-fcf3-47fb-8e06-ae2477440035` (retention), `23475ca3-3adb-41b9-9918-6e75b953a2fd` (histogram), `141d33ba05cc` (correlation) | visual formatting | `<iframe … style="width: 100%; border: none;">` | `<iframe … class="ml-activity" style="width: 100%;">` — the inline `border: none` is dropped so `book/_static/custom.css` can give all three the same card frame (1 px border, 10 px radius, white surface, subtle shadow, vertical margin). `title`, `src`, `loading="lazy"`, `width`, `height` unchanged. |

---

## 6. New / changed non-notebook files

| File | Category | Change |
|---|---|---|
| `book/_static/custom.css` | **new** (visual formatting + accessibility) | Documented course visual layer, ~330 lines. `:root` / `html[data-theme="light"]` / `html[data-theme="dark"]` define an `--ml-*` palette (ink `#1b1826`, body `#423c53`, muted `#5c5674`, border `#d9d9e3`, rust accent `#dd5f1b`, AA-safe rust ink `#ad4a12`, page `#eceef4`, surface `#fff`, alt surface `#f4f4f9`, success `#0e7c7b`, warning `#b8365a`) and re-map the theme's own `--pst-color-*` tokens (primary / link / accent / border / surface / text / target / inline-code) in both light and dark. Scoped rules (all under `.bd-article`): serif headings (Georgia system stack) with `scroll-margin-top`; readable prose measure (46 rem) that does not constrain figures/tables/iframes; `table.dataframe` → monospace, tabular-nums, right-aligned numerics, subtle header, zebra + hover; `.cell_output .output` → `overflow-x:auto`; `.admonition.think-first` / `.challenge` / `.how-to-use` cards (rust left border, monospace uppercase title, typographic `?` / flag / info marker replacing the theme icon); `details.sd-dropdown` header (monospace, rust); `.cell_input` + "Show code cell source" toggle framing; `iframe.ml-activity` card; `:focus-visible` outlines; `prefers-reduced-motion` block; `@media print` block (grey borders instead of tints, reveal open dropdown content, smaller dataframe font). `!important` used only on: `details.sd-dropdown` overrides (theme uses inline-level specificity), the reduced-motion block, and the print block — each noted in `WP06_REPORT.md`. |
| `book/_config.yml` | code (config) | Added `sphinx: { config: { html_css_files: [ custom.css ] } }` after the `parse:` block, to load `book/_static/custom.css` into every page through the mechanism supported by Jupyter Book 1.0.4. Nothing else in the file changed. |
| `interactive/src/styles.css` | visual formatting + accessibility | Token palette re-tuned to match the book layer's `--ml-*` values: `--fg` `#1b1826`, `--muted` `#5c5674`, `--border` `#d9d9e3`, new `--border-strong` `#c4c4d4` / `--surface-alt` `#f4f4f9` / `--accent` `#dd5f1b` / `--accent-ink` `#ad4a12` / `--accent-soft`, warm-tinted `--error-*` / `--warn-*`; matching dark-mode block. `input[type=range]` / `input[type=checkbox]` / `input[type=radio]` `accent-color` changed from the old blue `#2a6f9e` to `var(--accent)`. `.widget-title` and `.widget-subhead` now use the Georgia serif stack with tight tracking. `.widget-root` padding `16px` → `18px 20px 20px`. Buttons: `background` `var(--bg)`→`var(--surface-alt)`, `border` `var(--border)`→`var(--border-strong)`, radius `4px`→`5px`, hover now tints rust. Added a shared `:focus-visible` outline rule for buttons/selects/inputs/checkboxes. `.widget-checkbox-group` radius `6px`→`8px` + `--surface-alt` background. `.widget-plot` radius `6px`→`8px`. No TypeScript, no component logic, no config schema changed. Rebuilt: `book/_static/widgets/app/assets/index-*.css` 2.77 kB → 3.55 kB; JS bundle byte-identical. |

---

## 7. Summary counts by category

| Category | Count | Items |
|---|---|---|
| factual | 3 | C6, C8, and the re-verification embedded in Q11/Q13/Q14 (no number changed) |
| clarity | 6 | C1, C2, C3, C4, C6, C7 (+ C8) |
| grammar | 2 | C1 (title), C5 |
| terminology | 2 | C4, C5 |
| structure | 21 | C1, C2, C3, Q1–Q17, + 2 new opening cells |
| cell type | 0 | (no markdown↔code conversions) |
| metadata visibility | 4 | V1, V2, V3, V4 |
| output cleanup | 0 | (no stale/duplicate output removed; none found) |
| visual formatting | 5 | F1 (×3 iframes), `custom.css`, `interactive/src/styles.css` |
| accessibility | 3 | AA-safe link/toggle colour in `custom.css`, `:focus-visible` outlines (book + widget), `prefers-reduced-motion` + print rules |
| config | 2 | `book/_config.yml`, `sphinx.config.html_css_files` |

**Deleted or merged cells: none.**
**Verified WP05 numerical values changed: none** — C8 states observed effects
(mean 111.02→111.11, sd 15.48→14.78) that are new descriptive text, not a
revision of a prior figure; every number reused in the split answer cells was
recomputed against the pinned ABIDE-II CSV and matched.

### Serialization noise not logged as substantive

A clean `jupyter-book build` re-executes the notebook (cache invalidated by the
edits) and regenerates execution counts and the five figure PNGs. Four of the
five image hashes are reproduced exactly; the violin+strip figure
(`80632a35b296`) changes hash on every run because `sns.stripplot(… jitter=0.25 …)`
is called without a seed — a pre-existing WP05 non-determinism, cosmetic only
(the printed group table above it is deterministic). Flagged as a WP07
recommendation; not altered here.
