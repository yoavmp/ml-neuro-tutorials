# WP06 implementation report — EDA notebook editorial, instructional, and visual design pass

## Outcome

Status: **SUCCESS**

The complete Chapter 1 EDA notebook (`book/chapters/chapter_01/exercise_01.ipynb`)
received a controlled final-quality pass:

- **Opening rewritten** to match the notebook that now exists — a one-paragraph
  purpose, an "About this exercise" cell (context, guided-tutorial vs self-study
  modes, ~60–75 min estimate, brief prerequisites), a "How to use this notebook"
  callout, learning objectives rewritten with observable verbs, and a section
  roadmap.
- **Eight prose corrections** (a typo, an internal contradiction in the data
  loading note, an out-of-register aside, an imprecise imputation claim, an
  explicit data-leakage warning at the imputation example, and the objectives /
  roadmap rewrites). **No verified WP05 numerical result was changed**; every
  number reused in an edited cell was recomputed against the pinned ABIDE-II CSV
  and matched.
- **A single, applied visibility policy.** Every active question is a
  consistent **"Think first"** card; every revealable answer is a
  **"Check your reasoning"** dropdown; four code cells changed tag so that core
  EDA operations (median imputation, `describe`, the IQR rule) are visible and a
  diagnosis-missingness table is no longer fully hidden.
- **A documented visual layer** — `book/_static/custom.css`, wired through
  `book/_config.yml` — that re-tints sphinx-book-theme toward the palette,
  typography, card treatment, and monospace-eyebrow cues of the sibling course
  site (asafmm.github.io/ml_for_neuro), inspected live in a real browser, with
  **no copied prose, markup, scripts, fonts, or assets and no new external
  dependency**. `interactive/src/styles.css` was re-tuned to the same tokens so
  the three embedded activities do not look pasted from another product.
- **Full CI-equivalent suite green**, including a clean notebook execution and
  Jupyter Book build with no `*.err.log`, all 143 unit / 40 standalone-browser /
  9 built-book tests, and fresh desktop + 390 px screenshots with no horizontal
  page overflow and all three activities interactive.

## Git safety checkpoint

- Branch: `feature/reusable-interactive-widgets` (confirmed; not changed).
- Starting HEAD: `044be5f` ("WP05 report: document results").
- **Checkpoint commit: `5926d447b323b2122e569e2ba6d04ef287a4b8b1`** ("checkpoint: before WP06").
- **Checkpoint tag: `wp06-start`** (annotated; points at `5926d447`).
  `wp06-start` did not already exist, so no numeric suffix was needed.
- The checkpoint captured the only two pre-existing working-tree items — the
  WP-process update to `WPs/README.md` and the new brief
  `WPs/WP06_NOTEBOOK_EDITORIAL_AND_DESIGN.md`. No build output, caches,
  `.DS_Store`, credentials, tokens, or private data were present or committed.
- Retraction guidance (identification only; no reset/revert performed here): to
  undo WP06, `git revert` the implementation commit
  `WP06: polish EDA notebook content and design` and the report commit, or reset
  to `5926d447` / tag `wp06-start`. Leave `wp01-start`…`wp05-start` intact.

## WP05 baseline (run before any WP06 change)

| Command | Result |
|---|---|
| `npm ci` | OK (Node 24 locally; `engines` `>=20.19.0 <25`, CI pins 22) |
| `npm run typecheck` | OK, 0 errors |
| `npm run test:unit` | **143 / 143** |
| `npm audit --omit=dev` | 0 vulnerabilities |
| `npm run build` | OK (only the carried-forward Vite 500 kB Plotly-chunk warning) |
| `python scripts/export_widget_data.py --check --artifact all` | both artifacts valid + canonical |
| `python -m unittest tests.test_export_widget_data` | **45 / 45** |
| `npx playwright test` (standalone `e2e/`) | **40 / 40** |
| `rm -rf book/_build && jupyter-book build book` | exit 0, **9 warnings** (all pre-existing: `syllabus` toctree title, `README` not in toctree, missing `logo.png`, cosmetic IPKernelApp TCP notice), **no `*.err.log`** |
| `npm run test:e2e:book` (built book `e2e-book/`) | **9 / 9** |

Baseline fully green; baseline desktop (1280) and narrow (390) screenshots of
the Chapter 1 page were captured before any visual change (stored as
throwaway artifacts under the scratchpad, not committed).

## 1. Correctness and clarity audit — summary

All 81 cells (79 before edits) were read in order with `nbformat`, including
hidden cells and stored outputs. An independent reproduction of the notebook's
data pipeline (`pd.read_csv` of the pinned NH2020 CSV → strip column names →
select the 39 curated columns → categorical cast) was used to recompute every
quantitative statement that appears in edited or split cells.

**Verified correct, left unchanged** (representative):

- shape `1114 × 39`; `DX_GROUP` 521 Autism / 593 Control, 0 missing; `SEX`
  856 M / 258 F; the WP05 legend codings for `DX_GROUP`, `SEX`,
  `HANDEDNESS_CATEGORY`, `CURRENT_MED_STATUS`, `EYE_STATUS_AT_SCAN` (incl. the
  70 undocumented `0` rows — the notebook does not surface `EYE_STATUS`).
- `describe()` counts and the missingness ordering (MASC_TOTAL_T 80.6 % …
  EYE_STATUS 0.1 %).
- complete-case retention: 1114 → **1** (all 39) → 1015 (core 5).
- FIQ median = 112.0, 99 missing; FIQ by diagnosis n 479 / 536.
- AGE IQR fences ≈ [−3.8, 31.1], **56 of 1114** flagged; ages 5.13–64.
- site × diagnosis composition (KKI_1 ≈ 27/73 %, KUL_3 & NYU_2 100 % Autism);
  Cramér's V(SEX, DX_GROUP) = **0.184**; females ≈ 70 % Control.
- every Pearson/Spearman/pairwise-N in cell `188d49e2ebf5` (FIQ–VIQ 0.833 N 796,
  SRS_TOTAL–SRS_COMMUNICATION 0.981 N 785 with sum-of-subscales == total in
  755/757 fully-observed rows, SRS_TOTAL–SCQ 0.842 N 289, FIQ–SRS −0.240 N 778
  → ≈ 0 within group, SCQ–ADOS_G 0.056 N 71, AGE–FIQ 0.008 N 1015,
  AGE–ADOS_G −0.229 / −0.332 N 347, ADOS_G–ADOS_2 0.881 N 81).

**Corrected** (full before/after in `WP06_EXACT_CHANGELOG.md` §1):

| # | Where | What was wrong | Fix |
|---|---|---|---|
| C5 | `describe()` limitations bullet | typo `Dtpye = Category` | "their dtype is `category`, not a numeric type" |
| C6 | `{dropdown} Loading the ABIDE-II phenotypic data` | said both "several hundred variables" and "348 variables"; introduced the 39-subset twice | one statement of 348, one of the 39-subset |
| C4 | SUB_ID / category note | ambiguous "a relative distance"; out-of-register "just google it!" aside | "a meaningful distance between them"; "consult the study's data legend or the people who collected it" |
| C8 | note after FIQ-imputation compare | "without changing the distribution a lot … Try it yourself!" — understated, and pointed at a non-existent activity | precise statement of the observed effect (mean 111.02→111.11, sd 15.48→14.78) and why it is small here |
| C7 | "### Imputing a numerical variable" | leakage was only flagged 9 cells later | added a forward-pointing warning that a real pipeline fits the imputer on the training split only; **no code changed** |
| C1–C3 | title, objectives, roadmap | see §2 below | rewritten |

No stale/duplicate/empty output cell and no MyST directive typed into a code
cell was found. `nbformat.validate` passes; 81 unique cell IDs; the only tags
used are `hide-cell` and `hide-input`; no literal `hide-*` line appears in any
source.

**Deliberately not changed:** `phenotypes.sample(n=8, random_state=42)`
(cell `7af020ab-…`) still displays the `SUB_ID` column. These are public
ABIDE-II dataset identifiers, the very next question cell (`be0fb829-…`, Q3)
asks the student to classify `SUB_ID` as measurement / category / identifier,
and removing the column would blunt that teaching moment. It is an intentional
display of a public column, not an accidental identifier leak, and no export is
involved.

## 2. Introduction / objectives — before vs after

| Piece | Before (as committed at `wp06-start`) | After |
|---|---|---|
| Title | `# Exercise I: Exploratory Data Analysis (EDA)` — heading only | `# Exercise 1 — Exploratory data analysis (EDA)` + a one-paragraph purpose (EDA on the ABIDE-II phenotypic table; goal is a defensible understanding before modelling, not a model) |
| Context / modes / time | none (an informal "### Before we begin" note about hidden cells) | new **"## About this exercise"** cell: hands-on part of Chapter 1, follows the tutor presentation; **Guided tutorial** (~60–75 min) and **Self-study** modes; prerequisites = basic Python + first acquaintance with `pandas`/`NumPy`/`matplotlib`/`seaborn`, run top-to-bottom, internet needed on first run |
| "How to use" | none | new **`{admonition} How to use this notebook`** callout: visible questions vs revealable answers, collapsed vs open code, three kernel-free browser activities |
| Learning objectives | 6 title-case bullets; missing categoricals, leakage, pairwise-N/association-view; promised "predictive analysis" | 8 observable-verb bullets covering inspect rows/schema/types/summaries; convert encoded vars to categoricals; quantify missingness + reason about site/diagnosis; compare keep/drop/impute **without leakage**; describe & compare distributions; flag unusual values without deleting; choose an association view by variable type; interpret Pearson/Spearman with pairwise N + confounding |
| Roadmap | none | **"### What this notebook covers"** — 5 numbered items mirroring the actual H2 headings |

The opening stays concise (title paragraph + three short cells) and does not
promise neuroimaging-feature modelling.

## 3. Visibility policy — final

Policy applied (WP §6 default table, departures noted):

| Cell role | Presentation |
|---|---|
| Title / explanation / question / interpretation | visible Markdown |
| Imports; remote-data load; optional advanced calc | `hide-cell` (3 cells) |
| Long plotting boilerplate after the concept is made | `hide-input`, output visible (6 cells) |
| Secondary exploratory `groupby` whose table is the evidence for an answer | `hide-input` (1 cell — was `hide-cell`) |
| Core EDA operations (`sample`, `info`, `describe`, categorical cast, `isna` counts, `groupby`, median imputation, IQR rule, `corr`, crosstab) | input + essential output visible (12 cells) |
| Answer / reasoning | `{dropdown}` (MyST, revealable) |

### Counts (22 code cells)

| Presentation | Before | After |
|---|---|---|
| visible (input + essential output) | 12 | 12 |
| `hide-input` (output visible) | 9 | 7 |
| `hide-cell` (collapsed, revealable) | 4 | 3 |
| `hide-output` | 0 | 0 |

Four tag changes (detail + IDs in `WP06_EXACT_CHANGELOG.md` §3):
`hide-cell`→`hide-input` on the missing-by-diagnosis `groupby`;
`hide-input`→visible on the median-imputation demo, the `describe().T`
distribution summary, and the IQR-flag cell. No tag was added. Every hidden cell
still reveals in built HTML via the sphinx-togglebutton "Show code cell source"
bar (10 toggles: 3 `hide-cell` + 7 `hide-input`) — verified by clicking and by
keyboard focus in Playwright. Markdown cells: 57 → 59.

### Question / answer consistency

- **14 "Think first" cards** (9 plain question cells + 5 that also carried an
  inline answer, now split). Rendered `<div class="think-first admonition">` with
  a monospace uppercase title and a typographic `?` marker.
- **7 "Check your reasoning" dropdowns** (5 from the split cells + 2 standalone
  that were labelled "Answer" / "Answer for Q4").
- The synthesis challenge task list is wrapped in a `challenge` card; its
  "model reasoning process" dropdown (a checklist, not one right answer) is
  unchanged, per WP §7.5.
- Untouched: `{dropdown} Important limitation` (a note) and
  `{dropdown} Loading the ABIDE-II phenotypic data` (progressive-disclosure
  background). The two retention-explorer task prompts ("Design a complete-case
  dataset", "Your decision") stay as visible prose section leads because they
  introduce an activity rather than pose a check-your-answer question.
- Built HTML contains **0** literal `{admonition}` / `{dropdown}` / `:class:`
  strings; all 14 cards and 10 dropdowns render as directives.

## 4. Assaf's site — design observations and adopted / not-adopted cues

Inspected live in headless Chromium (Playwright) on 2026-09-09:
<https://asafmm.github.io/ml_for_neuro/class1_part2_linear_regression.html>
(HTTP 200) plus the site landing <https://asafmm.github.io/ml_for_neuro/>
(HTTP 200). Desktop (1280) and mobile (390) screenshots were captured and
computed styles were read from the DOM (not inferred from source). `intro.html`
404s — the landing is served at the directory root; noted, not a blocker.

| Aspect | Observed on Assaf's site | Decision for this book |
|---|---|---|
| Page width / rhythm | main column ~1024 px; prose measure ~700 px; generous 96 px tail padding; warm cream gradient top-right of the hero | **adapted** — 46 rem prose measure inside the existing sphinx-book-theme column; no hero, no gradient |
| Font family / scale | IBM Plex Serif headings (h1 ~56 px, tight −1 px tracking), IBM Plex Sans body (~16.5 px, line-height ~1.62), IBM Plex Mono for eyebrows / tables / buttons / captions | **adapted, not copied** — system **serif** stack (Georgia …) for h1–h4 with −0.012em tracking; system sans body; system **mono** for table text, card titles, dropdown headers, code toggles. **No web font is fetched.** |
| Heading hierarchy | serif, weight 600, section number eyebrow ("01") in mono accent above each h2 | serif + weight 600 + tracking adopted; the mono section-number eyebrow was **not** reproduced (needs per-heading markup; fragile) |
| Colours | ink `#1b1826`, body `#5c5674`, faint `#8b85a3`, border `#d3d3e0`, rust accent `#dd5f1b` (+ `rgba(...,0.13)` soft), warm red `#b8365a`, teal `#0e7c7b`, page `#e8e9f0`, surface `#fcfcfe`, alt `#f1f1f7` | **adopted** almost verbatim as `--ml-*` tokens; body text darkened to `#423c53` and link/accent text to `#ad4a12` to clear WCAG AA on white |
| Tables | monospace, ~11–12 px, muted text, tight padding, left-aligned | **adopted** — dataframe tables now monospace + tabular-nums, subtle header, right-aligned numerics, zebra + hover |
| Code / output containers | `#fcfcfe` surface, 1 px `#d3d3e0` border, 8 px radius, ~14–17 px padding | **adopted** for `.cell_input` and the code-toggle bar (dashed border to read as revealable) |
| Question / "try it yourself" | monospace uppercase eyebrow label ("MOVE THE LINE YOURSELF"), card with 1 px border + subtle radius | **adopted** — "Think first" / "Synthesis challenge" / "How to use" cards: rust left border, monospace uppercase title, 10 px radius |
| Interactive-control styling | rust slider/thumb, 5 px-radius buttons (solid rust primary / bordered secondary), monospace labels, left-accent-border readout chips | **adopted** in `interactive/src/styles.css` — `accent-color` rust for range/checkbox/radio, 5 px buttons with rust hover, serif widget titles, alt-surface control groups |
| Navigation / header | custom left rail with mono course code eyebrow, serif course title, numbered TOC; "theme · light" pill | **not adopted** — sphinx-book-theme's own navbar/sidebar are left entirely alone (rules are scoped to `.bd-article`); only the theme's colour tokens are re-tinted so nav links pick up the rust accent |
| Prose, source code, logos, images, JS | — | **not copied.** No text, script, image, or asset from the site is present. |

## 5. CSS / config / table / iframe changes

- **`book/_static/custom.css`** — new, ~330 lines, documented. `:root` +
  `html[data-theme="light"]` + `html[data-theme="dark"]` define the `--ml-*`
  palette and re-map the theme's own `--pst-color-*` tokens (primary, link,
  accent, border, surface, text-base/muted, heading, target, inline-code) in
  both themes. Scoped rules, all under `.bd-article`: serif h1–h4 with
  `scroll-margin-top` (anchor offset under the sticky header); 46 rem prose
  measure that leaves figures / tables / iframes full width; `table.dataframe`
  monospace + tabular-nums + subtle header + zebra + hover + numeric alignment;
  `.cell_output .output { overflow-x:auto }` so wide tables scroll in place;
  `.admonition.think-first` / `.challenge` / `.how-to-use` cards; `sd-dropdown`
  header restyle; `.cell_input` + code-toggle framing; `iframe.ml-activity`
  card (1 px border, 10 px radius, white surface, `0 1px 3px` shadow, vertical
  margin); `:focus-visible` outlines; `prefers-reduced-motion` block;
  `@media print` block.
  **`!important` is used only** on the `sd-dropdown` overrides (sphinx-design
  sets those at a specificity that a scoped class cannot beat cleanly), the
  `prefers-reduced-motion` reset, and the `@media print` rules — 3 documented
  groups; nothing else in the file uses it. No selector targets navigation,
  search, or Plotly internals, and none is tied to generated cell numbers.
- **`book/_config.yml`** — added
  `sphinx: { config: { html_css_files: [ custom.css ] } }` (Jupyter Book 1.0.4's
  supported mechanism; `book/_static` is already on `html_static_path`).
  Verified: `book/_build/html/_static/custom.css` is emitted and
  `exercise_01.html` links it.
- **`interactive/src/styles.css`** — token palette re-tuned to the book's
  `--ml-*` values (+ `--border-strong`, `--surface-alt`, `--accent`,
  `--accent-ink`, `--accent-soft`, warm `--error-*` / `--warn-*`) with a
  matching dark block; `accent-color` for range/checkbox/radio moved from blue
  `#2a6f9e` to rust; serif widget titles/subheads; `.widget-root` padding;
  buttons (surface-alt bg, stronger border, 5 px radius, rust hover) + a shared
  `:focus-visible` outline; checkbox-group and plot radii to 8 px. **No
  TypeScript, component logic, config schema, data artifact, or exporter code
  changed.** Rebuild: `index-*.css` 2.77 kB → 3.55 kB; the JS bundle is
  byte-identical (1,484.72 kB / gzip 495.89 kB).
- **Notebook iframes** — the three activity `<iframe>`s gain
  `class="ml-activity"` and lose the inline `border: none` (so the stylesheet's
  card frame is not overridden); `title`, `src`, `loading`, `width`, `height`
  unchanged. All three still load, are HTTP 200 for config + data, and stay
  interactive on the real built Chapter 1 page (built-book Playwright).
- **Tables audited individually.** The three prose/MyST tables (missing-data
  strategies, Pearson-vs-Spearman, association-view-by-type) and the dataframe
  outputs are styled by global CSS only. No `pandas.Styler` was added: none of
  the current tables needs decimal/percentage formatting, a caption, or a
  highlighted cell beyond what the code already does (`.round(...)`), and a
  gradient would imply ranking that is not intended.

## 6. Files changed

Implementation commit `WP06: polish EDA notebook content and design`
(4 files changed vs `5926d447`):

| Path | Change |
|---|---|
| `book/chapters/chapter_01/exercise_01.ipynb` | 79 → 81 cells; opening rewrite (3 edits + 2 new cells); 8 prose corrections; 17 question/answer structure changes; 4 visibility-tag changes; 3 iframe class edits. `+243 / −98` lines, **no `execution_count` or output line changed** (build regenerates via cache). |
| `book/_static/custom.css` | **new** — the documented visual layer. |
| `book/_config.yml` | `sphinx.config.html_css_files: [custom.css]` added; trailing newline added. |
| `interactive/src/styles.css` | token palette + controls aligned with the book layer; focus outlines. |

**Not changed:** `scripts/export_widget_data.py`, both `abide_*.json` data
artifacts (SHA-256 identical), `book/_static/widgets/configs/*.json`,
`.github/workflows/deploy.yml`, `_toc.yml`, `requirements.txt`, every
`interactive/src/*.ts`, every test file, the histogram / retention / correlation
component logic.

Generated / not committed (verified absent from `git status`):
`book/_build/`, `book/_static/widgets/app/`, `interactive/node_modules/`,
`interactive/test-results/`, `**/__pycache__/`, all screenshot artifacts
(kept under the session scratchpad).

## 7. Tests

| Command / check | Result | Evidence |
|---|---|---|
| `npm run typecheck` | **PASS** | `tsc --noEmit` exit 0 |
| `npm run test:unit` | **PASS** | **143 / 143** (unchanged suite; CSS-only edits) |
| `npm audit --omit=dev` | **PASS** | 0 vulnerabilities |
| `npm run build` | **PASS** | CSS 3.55 kB, JS byte-identical; only the pre-existing 500 kB Plotly-chunk warning |
| `python scripts/export_widget_data.py --check --artifact all` | **PASS** | both artifacts valid + canonical (untouched) |
| `python -m unittest tests.test_export_widget_data` | **PASS** | **45 / 45** |
| `npx playwright test` (standalone) | **PASS** | **40 / 40** |
| `rm -rf book/_build && jupyter-book build book` | **PASS** | "build succeeded, **9 warnings**" — identical pre-existing set (syllabus title, README not in toctree, `logo.png`, IPKernelApp TCP notice); **no `*.err.log`** |
| `find book/_build -name '*.err.log'` | **PASS** | empty |
| `npm run test:e2e:book` (built book) | **PASS** | **9 / 9** — all three iframes load, config+data 200, controls change the real figure/stats |
| `nbformat.validate` + unique-id + tag + literal-hide-line check | **PASS** | 81 cells, 81 unique IDs, tags ⊆ {`hide-cell`, `hide-input`}, 0 literal hide lines |
| Independent pandas recompute of every edited/​split numeric statement | **PASS** | matches the pinned CSV to the quoted precision |
| MyST render check on built HTML | **PASS** | 0 literal directive strings; 14 "Think first" + 1 "How to use" + 1 "Synthesis challenge" cards; 7 "Check your reasoning" + 3 other dropdowns render |
| Horizontal-overflow check (Playwright, 1280 px and 390 px) | **PASS** | `scrollWidth == clientWidth` at both; wide dataframe tables scroll inside `.cell_output .output` |
| Custom CSS load check | **PASS** | `_static/custom.css` emitted and linked in `exercise_01.html`; computed `--pst-color-link` = `#ad4a12` |
| Browser console / network (built page, both viewports) | **PASS** | no new errors, no failed requests; the one `Got invalid theme mode` message is present identically in the pre-change baseline (sphinx-book-theme) |

## 8. Visual and accessibility verification

Reviewed against before/after screenshots at 1280 px and 390 px (desktop +
narrow), plus dark mode and print emulation:

- **Introduction** — serif title + purpose paragraph, "About this exercise",
  the "How to use this notebook" card (rust left border, mono uppercase title,
  `i` marker).
- **Representative table** — `phenotypes.sample()` output: monospace,
  tabular-nums, right-aligned numerics, zebra, subtle header, bold index.
- **Question / dropdown** — "Think first" card (peach title band, `?` marker)
  followed by a "Check your reasoning" dropdown (mono rust header, chevron).
- **Hidden-code toggle** — "Show code cell source" now a mono, rust, dashed-border
  bar; click and keyboard-focus both reveal the input (Playwright).
- **Each static figure type** — the missingness heatmap, the FIQ violin+strip,
  the site×diagnosis and Pearson / pairwise-N heatmaps all render with readable
  labels inside the restyled page.
- **All three interactive cards** — retention, histogram, correlation: identical
  card frame (border, 10 px radius, white surface, soft shadow), serif widget
  titles, aligned mono-labelled controls, rust control accents; default readouts
  correct (e.g. correlation `r = -0.24 · n = 778`).
- **Dark mode** — the theme toggle is exposed; `html[data-theme="dark"]` swaps
  to dark surfaces with a lifted `#f0915c` accent for links, toggles, and the
  active nav item; cards, code output, and figures stay legible.
- **Print** — `@media print` replaces tinted card/dropdown backgrounds with grey
  borders, keeps dropdown summaries and any open content visible, and shrinks the
  dataframe font; nothing tested went missing.
- **Contrast** (programmatic sRGB check on the built light page): body text
  `#423c53` on `#fff` ≈ **10.5:1**; links `#ad4a12` on `#fff` ≈ **5.6:1**;
  dropdown-header text on its band ≈ **5.1:1**; "Think first" title on its band
  ≈ **4.9:1** — all ≥ WCAG AA for normal text. Group colour in the figures and
  the correlation explorer is always paired with a text label / legend, never
  colour alone. `:focus-visible` gives a 2 px rust outline on links, buttons,
  summaries, and widget controls. `prefers-reduced-motion` collapses transitions.

## 9. Deviations from instructions

1. **Section-number eyebrows not reproduced.** Assaf's site prints a mono accent
   "01" above each `h2`. Adding that to the notebook would need per-heading
   markup or fragile `::before` counters keyed to heading order; it was judged
   out of proportion to the benefit and omitted. Heading serif face, weight, and
   tracking are adopted.
2. **Body/link colours darkened from the reference.** The sibling site's body
   `#5c5674` and accent `#dd5f1b` do not clear WCAG AA as text on white; this
   book uses `#423c53` for body copy and `#ad4a12` for link/accent text, keeping
   the un-darkened `#dd5f1b` for borders and markers only. Documented in the CSS.
3. **Two new opening cells** (not an edit of existing ones) for "About this
   exercise" and "How to use this notebook", so the title cell and the
   objectives cell each keep a single clear job. IDs `a1b2c30d4e5f`,
   `b2c3d40e5f6a` (12-hex, matching the WP05 convention).
4. **`#### Question` headings dropped, not kept above the card.** The
   "Think first" admonition is the recognisable prompt; keeping a now-redundant
   heading above it (and a duplicate TOC entry) was judged worse than losing two
   vague "Questions" entries from the right-hand contents list. Topic-bearing
   headings ("Identify the variables", "Interpret the heatmap", the five
   `Question: …` suffixes) were preserved as bold lead lines inside the card.
5. **`deploy.yml` unchanged.** `custom.css` lives in `book/_static/`, which
   Sphinx already copies verbatim, and it is loaded by the new `_config.yml`
   entry; the workflow's `jupyter-book build book` step therefore picks it up
   with no new step. No new test file was added (the visual layer is verified by
   the existing built-book Playwright plus the screenshot review in this WP), so
   no CI wiring was needed.
6. **`sns.stripplot` jitter left unseeded.** The FIQ violin+strip figure
   (`80632a35b296`, WP05 code) calls `sns.stripplot(… jitter=0.25 …)` without a
   seed, so its PNG hash changes on every notebook execution. It is cosmetic
   (the printed group table is deterministic) and fixing it means editing WP05
   code and regenerating the output; left as a WP07 recommendation.
7. **Node 24 locally** (`engines` `>=20.19.0 <25`; CI pins 22). `npm audit
   --omit=dev` is clean; the full-tree dev-toolchain advisories are carried
   forward from WP02–WP05 (no Vite/Vitest upgrade in this WP).

## 10. Unresolved risks

- **Figure non-determinism** — the unseeded `stripplot` jitter (deviation 6).
  The CI `*.err.log` guard is unaffected; only the image bytes vary.
- **`custom.css` couples to two theme internals** — the `sd-dropdown` selectors
  and the `.admonition-title::before` icon replacement depend on
  sphinx-design / pydata-sphinx-theme markup. A major theme bump could need a
  re-check. The colour-token re-map (`--pst-color-*`) is the stable part.
- **Page-level CDN, unchanged** — the surrounding Chapter 1 *page* still loads
  MathJax from `cdn.jsdelivr.net` and ships `sphinx-thebe.js` (pre-existing
  sphinx-book-theme behaviour). The activity iframes remain CDN/kernel-free
  (asserted by the built-book Playwright). Out of scope here, as in WP04–WP05.
- **`jupyter-book build` still exits 0 on a notebook execution error**; the CI
  `*.err.log` guard remains the safety net and must be kept.
- **Bundle size** — 1.48 MB raw / 496 kB gzip (Plotly), above Vite's 500 kB
  warning; acceptable for a lazy-loaded iframe, code-splitting still an option.

## 11. Git commits created

- Checkpoint: `5926d447b323b2122e569e2ba6d04ef287a4b8b1` ("checkpoint: before WP06")
- Checkpoint tag: `wp06-start` (annotated; points at `5926d447`)
- Implementation: "WP06: polish EDA notebook content and design" — hash in the terminal summary
- Reports: "WP06 report: document editorial and design changes" — hash in the terminal summary (a report cannot contain its own commit hash)

## 12. Recommendations — WP07 only (do not create or begin WP07)

- **Seed the `stripplot` jitter** (`np.random.seed` or a fixed `rng`) so the
  Chapter 1 notebook builds byte-reproducibly, then optionally commit executed
  outputs for the eight WP05 code cells that currently ship without outputs.
- **Page-level CDN removal** (Rule 8): self-host MathJax and trim / self-host the
  `sphinx-thebe` launch-button config so the whole published Chapter 1 page —
  not only the iframes — is CDN-free.
- **Dynamic iframe height** for all three activities (currently fixed
  `height=680/820/900`), to remove inner scrollbars on narrow viewports.
- **Consolidate the remaining kernel-only demos** (median imputation, category
  fill) into the browser runtime, or explicitly decide they stay kernel-only, so
  the entire EDA exercise works on the static site.
- **Toolchain security bump** (Vite ≥ 6 / Vitest ≥ 3) as an isolated WP with a
  full typecheck/unit/build/e2e re-run.
- **A short automated visual-regression check** (Playwright screenshot compare)
  for the Chapter 1 page, if the project wants to lock the new design in CI.

## Instructions for reviewer

Paste this entire report (`WP06_REPORT.md`) into the ChatGPT conversation that
produced WP06. `WP06_EXACT_CHANGELOG.md` is the companion line-item record.
