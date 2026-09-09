# WP07 — exact change log

Location-specific record of every substantive change in WP07, so the effect can
be identified without diffing notebook JSON.

- Canonical notebook: `book/chapters/chapter_01/exercise_01.ipynb`
  (**81 → 84 cells**: three markdown/code cells added, one question removed from
  a card, no cell deleted, every pre-existing cell id preserved).
- New portable notebook: `book/downloads/chapter_01/exercise_01_portable.ipynb`
  (**generated**, 84 cells).
- Cell positions below are the **post-WP07** 0-based index; the 12–36-hex id is
  the stable anchor.
- Regenerated `execution_count` values and figure-image hashes from a clean
  rebuild are not listed as substantive (build regenerates them from cache); the
  committed canonical notebook keeps its output-less committed state and only the
  one new code cell adds `"outputs": []` / `"execution_count": null`.

Checkpoint: `d201cecd169c23ff148294d1410f9441a8a3d33e` ("checkpoint: before WP07"),
annotated tag `wp07-start`.
Implementation commit: `1b209c89db990c6fe316d439432fa9f872cd461f`
("WP07: fix notebook UX and add portable Colab version").

---

## 1. Sidebar toggle — diagnosis and fix

### Root cause (verified by Playwright + DOM inspection on the built page)

The built Chapter 1 page renders **two** `.primary-toggle` buttons (and two
`.secondary-toggle` buttons):

| button | location | rendered | accessible name |
|---|---|---|---|
| A | `#pst-header` (site navbar) | `display:none` at every width (`sphinx-book-theme.css`: `.bd-header button.sidebar-toggle{display:none}`) | "Site navigation" |
| B | `.bd-header-article` (article header) | **visible** at every width (`sphinx-book-theme.css` `@media (min-width:768px){button.sidebar-toggle.primary-toggle{display:inline-block}}` + `.bd-header-article .btn{display:flex}`) | "Toggle primary sidebar" |

`_static/scripts/pydata-sphinx-theme.js` and `_static/scripts/sphinx-book-theme.js`
each wire their click handler with `document.querySelector(".primary-toggle")`,
which returns the **first** match in DOM order — button **A**, the hidden one.
Button **B**, the only one the reader sees, has **no** click / keyboard handler.

Observed before WP07 (`diagnose_sidebar.mjs`, viewports 1280 / 1024 / 390 px):

| viewport | click B (mouse) | Enter on B | primary sidebar state |
|---|---|---|---|
| 1280 | no change | no change | permanently visible (256 px, 4 nav links) |
| 1024 | no change | no change | permanently visible (205 px) |
| 390 | no change | no change | hidden (`visibility:hidden`, `offsetParent:null`) — **no working way to reach site nav** |

`#pst-header` itself is `height:0` on mobile, so re-showing button **A** by CSS
was not viable.

### Fix — `book/_static/sidebar-toggle-fix.js` (new, 57 lines)

Forwards activation from the visible article-header toggles to their wired hidden
counterparts:

```js
forward(".bd-header-article .primary-toggle",   "#pst-header .primary-toggle");
forward(".bd-header-article .secondary-toggle", "#pst-header .secondary-toggle");
// visible.addEventListener("click", e => { e.preventDefault(); hidden.click(); });
```

No theme internals are patched. The theme's own handlers then run unchanged:

| viewport | click B / Enter / Space | observable result |
|---|---|---|
| 1280 / 1024 | toggles `pst-sidebar-hidden` on `#pst-primary-sidebar` | sidebar slides out (`margin-left:-256px`, `visibility:hidden`, `opacity:0`); second activation restores it |
| 768 / 390 | opens `#pst-primary-sidebar-modal` (`<dialog>.showModal()`) | nav links become reachable; Escape / outside-click closes and moves them back |

Wired in `book/_config.yml` via `sphinx.config.html_js_files: [sidebar-toggle-fix.js]`.

### Regression tests — `interactive/e2e-book/sidebar-toggle.spec.ts` (new, 4 tests)

1. desktop: toggle visible; click collapses (`pst-sidebar-hidden` + off-viewport) and re-expands the sidebar.
2. desktop: keyboard Enter and Space also toggle it.
3. narrow (390 px): click opens `#pst-primary-sidebar-modal`, the "…Exploratory data analysis…" nav link is visible inside, Escape closes it.
4. loop over 1280 / 1024 / 768 / 390 px: wherever the toggle is visible, one click must change `{pst-sidebar-hidden, modalOpen}` — fails on a no-op.

All 4 pass; the full `e2e-book` suite is now **13** tests (was 9).

---

## 2. Notebook — opening text

| ID | Cell (index · id) | Before | After | Reason |
|---|---|---|---|---|
| O1 | 2 · `a1b2c30d4e5f` — "## About this exercise" | `- **Guided tutorial** — worked through together in a session. Budget about 60–75 minutes for the full notebook.` / `- **Self-study** — read from top to bottom on your own. Every question has a revealable answer, and the three interactive activities need no Python kernel.` | `- **Guided tutorial** — worked through together in a session.` / `- **Self-study** — read from top to bottom on your own. The three interactive activities need no Python kernel.` **plus** a new paragraph: *"Questions are placed throughout the notebook. They are there to move past simply running code toward explaining the analytical choices behind it, and the kind of reasoning they ask for is close to what course assessment and exam questions expect. Some questions have a **Check your reasoning** dropdown that walks through the argument; open discussion questions are deliberately left without one fixed answer."* | WP §3: remove every time estimate; stop claiming every question has a revealable answer; add the deeper-understanding / assessment-style-reasoning point without promising verbatim exam questions. |
| O2 | 3 · `b2c3d40e5f6a` — "How to use this notebook" | 3 bullets: "Questions come before answers…"; "Some code is collapsed…"; **"Three activities run in your browser.** The histogram, the complete-case retention explorer, and the correlation explorer are kernel-free…" | 4 bullets: work through sections in order and pause at each **Think first** card; "Some activities are interactive and run directly in your browser, with nothing to install."; "To execute the code cells or change the code yourself, open the notebook in Colab or download the portable `.ipynb` version using the links at the top of this notebook."; "Some answers and checklists are revealable in a **Check your reasoning** dropdown; open questions may not have one fixed answer." | WP §3: concise; do **not** enumerate which activities are interactive; add browser / no-install + Colab + portable-download guidance. |
| O3 | 1 · `c4d5e6f7a8b9` — **new** `{admonition} Run or download this notebook :class: how-to-use` | — | Card inserted immediately after the H1 title: "This page is fully readable as it is… To **run or change the Python code**, use the portable version of the notebook:" + two links (below) + "The portable notebook keeps every Python analysis cell and swaps the three embedded activities for links back to this page." | WP §4: stable, clearly-labelled controls near the notebook opening. |

New-cell id convention: 12-hex, matching WP05/WP06 (`c4d5e6f7a8b9`, `d5e6f7a8b9c0`, `e6f7a8b9c0d1`); all three verified distinct from existing ids.

---

## 3. Notebook — Colab / download controls

| Where | Before | After |
|---|---|---|
| `book/_config.yml` `launch_buttons:` | `launch_buttons:` / `  colab_url: "https://colab.research.google.com"` | block **removed**, replaced by a comment explaining why (the theme builds the Colab URL from `repository.branch` = `main` + the canonical path `book/chapters/chapter_01/exercise_01.ipynb`, so it opened the embedded Jupyter Book notebook, not the portable one). |
| Built Chapter 1 page | header "Launch" dropdown → **Launch on Colab** → `https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/blob/main/book/chapters/chapter_01/exercise_01.ipynb` | `dropdown-launch-buttons` is **absent**; the only `colab.research.google.com` URL on the page is the portable link in card O3. |
| Card O3 links | — | **Open the portable notebook in Colab** → `https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/blob/main/book/downloads/chapter_01/exercise_01_portable.ipynb` · **View or download the portable `.ipynb`** → `https://raw.githubusercontent.com/yoavmp/ml-neuro-tutorials/main/book/downloads/chapter_01/exercise_01_portable.ipynb` (labelled "View or download" because raw GitHub may display rather than download). |
| Theme "Download this page → .ipynb" (`btn-download-source-button` → `_sources/…exercise_01.ipynb`) | present | **left as-is.** It is honestly labelled "Download source file", is not the misleading *Colab* control WP §4.2 targets, and both tried Sphinx knobs (`html_copy_source: false`, `use_download_button: false`) either failed to remove it or left a broken link. Flagged for Yoav under "requires attention". |
| `book/_config.yml` `exclude_patterns:` | — | `exclude_patterns:` / `  - downloads/*` added so Sphinx does not treat `book/downloads/` as a source document (no "not in any toctree" warning; not copied into `_build/html`). |

---

## 4. Notebook — removed question

| ID | Cell (index · id) | Before | After |
|---|---|---|---|
| Q-DEL | 18 · `e05d9a3c-cf5d-4b7b-ba0c-92aa7659d389` — `{admonition} Think first` after `phenotypes.info()` | `Examine the output of \`phenotypes.info()\`.` / `1. How many participants and variables are present?` / `2. Which variables contain missing observations?` / `3. Are any categorical variables stored as numbers/strings?` / **`4. Why might pandas assign the \`object\` data type to a column?`** | items 1–3 unchanged, verbatim; **item 4 removed**. No renumbering needed. |

There was **no dedicated answer dropdown** for item 4 (the following cell
`3ad75c70-…` "#### Interpreting `info()`" is a strengths/limitations discussion,
not a Q&A answer, and is unchanged). No adjacent `info()` question was touched.
`grep` over every cell confirms the string
"Why might pandas assign the `object` data type" no longer appears anywhere.

---

## 5. Notebook — collapsible Python age histogram

| New cell | Index · id | Type / tag | Content |
|---|---|---|---|
| H-MD | 59 · `d5e6f7a8b9c0` | markdown | "The same basic plot can be produced in Python with the notebook's existing dataframe and plotting stack." |
| H-CODE | 60 · `e6f7a8b9c0d1` | code · **`hide-input`** | ```python\nfig, ax = plt.subplots(figsize=(8, 4))\nsns.histplot(\n    data=phenotypes,\n    x="AGE_AT_SCAN",\n    bins=25,\n    color="steelblue",\n    edgecolor="white",\n    ax=ax,\n)\nax.set(\n    title="Distribution of age at scan",\n    xlabel="Age at scan (years)",\n    ylabel="Number of participants",\n)\nplt.show()``` |

Placement: immediately after the histogram `<iframe>` cell
(`23475ca3-…`), i.e. `iframe cell → H-MD → H-CODE → {admonition} Think first`
(`0658e691-…`).

**Visibility decision: `hide-input`** (not `hide-cell`). The rendered static
histogram sits directly under the interactive one and demonstrates that both draw
the same 1,114 rows, so the output has teaching value and stays visible; only the
code folds behind "Show code cell source". Verified in the built HTML: the
toggle bar is present and the output `<img>`
(`_images/52530396…png`) renders.

The portable notebook keeps this cell as an ordinary visible, runnable code cell
(hide tag stripped); it executes and produces the histogram.

---

## 6. Notebook — IQR defined explicitly

| ID | Cell (index · id) | Before | After |
|---|---|---|---|
| IQR | 70 · `58db4c1fc44e` — "### Range checks and flagged values" | *"A range check marks observations that fall outside an expected interval so a human can look at them. It does **not** decide that they are errors. A standard rule flags values below `Q1 − 1.5 × IQR` or above `Q3 + 1.5 × IQR`. We apply it to `AGE_AT_SCAN` and show the flagged rows using only non-identifying fields (site, diagnosis label, age) — never `SUB_ID`."* | *"A range check marks observations that fall outside an expected interval so a human can look at them. Crossing the interval **flags a value for inspection; it does not prove the value is an error.** The usual interval is built from the quartiles. `Q1` and `Q3` are the 25th and 75th percentiles of the variable (a quarter of the values fall below `Q1`, a quarter above `Q3`), and the interquartile range is the distance between them:*<br>`$$ \mathrm{IQR} = Q_3 - Q_1 . $$`<br>*A value is flagged when it falls below the lower fence or above the upper fence:*<br>`$$ Q_1 - 1.5\,\mathrm{IQR} \qquad\text{and}\qquad Q_3 + 1.5\,\mathrm{IQR}. $$`<br>*We apply it to `AGE_AT_SCAN` and show the flagged rows using only non-identifying fields (site, diagnosis label, age) — never `SUB_ID`."* |

Rendering: the built HTML contains
`<div class="math notranslate nohighlight"> \[ \mathrm{IQR} = Q_3 - Q_1 . \]</div>`
(and the fences), i.e. MathJax display-math input, not raw `$$` text; MathJax is
loaded on the page (`dollarmath` MyST extension already enabled). In the portable
notebook the same `$$…$$` blocks render via Colab/Jupyter MathJax.

The "flags for inspection, does not prove error" point is preserved (moved into
the first paragraph and slightly strengthened).

---

## 7. Notebook — stripplot jitter seeded

| ID | Cell (index · id) | Before | After |
|---|---|---|---|
| SEED | 66 · `80632a35b296` — FIQ violin + strip (`hide-input`) | `sns.violinplot(…)` then directly `sns.stripplot(\n    data=fiq_by_diagnosis, …, jitter=0.25, ax=ax,\n)` | between the two calls: `# Seed only the stripplot jitter (seaborn draws it from np.random); restore` / `# the global RNG state afterwards so no later cell is affected.` / `_rng_state = np.random.get_state()` / `np.random.seed(0)` before `sns.stripplot(…)`, and `np.random.set_state(_rng_state)` immediately after the closing `)`. |

Scope: only `np.random`'s global state is touched, and it is saved and restored
around the one call, so nothing else in the notebook changes. No `sns.stripplot`
argument changed; `jitter=0.25` is unchanged.

Determinism evidence:

* isolated re-render of the cell three times (including once after consuming
  1,000 random draws first, once after `np.random.seed(12345)`): identical
  stripplot point-offset hash and identical PNG hash every time; the post-cell
  global RNG state differs between runs → confirms `set_state` restored the
  pre-existing stream rather than leaving it at `seed(0)`.
* two consecutive `rm -rf book/_build book/.jupyter_cache && jupyter-book build`
  runs produce a **byte-identical set of 6 figure PNGs** (before WP07 the
  violin/strip PNG changed hash on every run — WP06 report deviation 6).

---

## 8. Portable notebook generator — `scripts/build_portable_notebook.py` (new, 445 lines)

Deterministically derives `book/downloads/chapter_01/exercise_01_portable.ipynb`
from the canonical notebook + `book/config/eda_phenotype_columns.json`.

| Requirement (WP §4) | Implementation |
|---|---|
| source of truth stays the canonical notebook | only reads `CANONICAL` and the columns JSON; never edits them |
| `--write` / `--check`, CI fails on stale | `--check` regenerates in memory and byte-compares to the committed file; exit 1 if missing or stale |
| keep explanatory Markdown + runnable Python | pass-through, original cell id retained |
| replace the 3 iframe cells | matched by `<iframe … title="…">`; each becomes: what the activity explores + `> **Interactive version on the course website.** … <https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html>` + "This portable notebook links to it instead of embedding it." Unknown iframe title → hard error. |
| convert MyST directives, no raw fences | `{admonition} T` → `#### T` heading + body; `{dropdown} T` → `<details><summary><strong>T</strong></summary> … </details>` (renders in Colab + VS Code + Jupyter); `:class:` / other option lines dropped; multiple blocks per cell handled |
| drop presentation tags/metadata, keep order + code | every cell's `metadata` reset to `{}`; code cells get `outputs: []`, `execution_count: null` |
| no JS/TS/Node/iframe/`_static`/generated HTML | `_assert_portable()` rejects `<iframe`, `_static/`, ```` ```{ ````, `ipywidgets`, `require(`, self-referential Colab links, any hide tag, any stored output |
| dependency story | prepended `## Setup` markdown cell: numpy/pandas/matplotlib/seaborn are preinstalled on Colab; VS Code users → `pip install -r requirements.txt`; a single commented `# %pip install …` line; **no install cell runs by default** |
| ABIDE data + column loading work outside the repo | `PHENOTYPES_URL` (pinned raw GitHub, neurohackademy mirror) kept verbatim; the repo-relative `COLUMNS_URL` + `pd.read_json(COLUMNS_URL, typ="series").tolist()` replaced by an embedded `CURATED_COLUMNS = [ … 39 names … ]` list and `phenotypes = phenotypes[CURATED_COLUMNS].copy()` |
| categorical conversion + later deps preserved | `.astype("category")` cell and all analysis cells pass through unchanged |
| no credentials / auth | none present or added |
| banner linking to the course page | prepended `portable-banner` markdown cell |

Also drops the two Jupyter-Book-navigation admonitions **"Run or download this
notebook"** and **"How to use this notebook"** (the portable banner covers the
portable-relevant guidance).

Result: **84 cells** (2 prepended `portable-banner` / `portable-setup` + 84
canonical − 2 dropped admonitions). 23 code cells, 61 markdown. Unique ids
(`nbformat.validate` passes). `nbformat.writes` (sorted keys, indent 1) + a
single trailing newline → running `--write` twice is a no-op; `--check` passes.

### Verification

| WP §4 check | Result |
|---|---|
| `nbformat` valid + unique ids | pass |
| no iframe / `_static` / MyST fence / hide tag / widget import / Node require | pass (asserted in generator **and** `tests/test_build_portable_notebook.py`) |
| execute from a temp dir outside the repo root, fresh kernel | `scripts/smoke_portable_notebook.py`: copies to `mktemp -d`, runs every cell via `nbclient` with `resources.metadata.path` = the temp dir, **0 errors**, 23/23 code cells |
| important output values match canonical | `Data table shape: (1114, 39)`; FIQ median 112, mean 111.0; `describe().T` block matches; FIQ-by-diagnosis n 479 / 536 (median 108 / 115); `IQR rule flags ages outside [-3.8, 31.1] years`, `56 of 1114 participants flagged`; SEX×DX_GROUP 77/181/444/412, within-sex % 29.8/70.2 (F), 51.9/48.1 (M) |
| direct activity links | syntactically correct HTTPS to the published page; **remote HTTP/content equality is deferred** until the branch is merged/pushed to `main` (see report) — not marked passing |
| unit tests for transform / iframe / directive / data loading / `--check` staleness | `tests/test_build_portable_notebook.py`, **18 tests**, pass |
| CI runs `--check` + executes it | `deploy.yml` steps added (below) |

---

## 9. New / changed non-notebook files

| File | Category | Change |
|---|---|---|
| `book/_static/sidebar-toggle-fix.js` | **new** (JS, 57 lines) | forwards the visible article-header primary/secondary toggles to the wired hidden ones; documented root cause; defensive null checks; no theme monkey-patching |
| `book/_config.yml` | config | **removed** `launch_buttons:` block (+ explanatory comment); **added** `exclude_patterns: [downloads/*]` (+ comment); **added** `sphinx.config.html_js_files: [sidebar-toggle-fix.js]`. `html_css_files: [custom.css]` unchanged. Net: `+17 / −4` lines. |
| `book/downloads/chapter_01/exercise_01_portable.ipynb` | **new** (generated, 84 cells) | committed portable derivative; regenerated by `scripts/build_portable_notebook.py --write` |
| `scripts/build_portable_notebook.py` | **new** (445 lines) | the deterministic generator (see §8) |
| `scripts/smoke_portable_notebook.py` | **new** (95 lines) | out-of-repo execution + key-value check; used by CI and locally |
| `tests/test_build_portable_notebook.py` | **new** (18 tests) | directive conversion, iframe replacement, portable data loading, determinism, `--check` staleness detection |
| `tests/test_notebook_corrections.py` | **new** (10 tests) | asserts every WP07 canonical-notebook correction (no time budget, assessment wording, concise "How to use", portable links, object-dtype question gone, histogram example cell + `hide-input`, IQR defined before fences, stripplot seeded, cell/visibility counts, valid+unique ids) |
| `.github/workflows/deploy.yml` | CI | 3 steps added: `python -m unittest discover -s tests -v` (after the artifact check); `python scripts/build_portable_notebook.py --check`; `python scripts/smoke_portable_notebook.py` (after the built-book e2e). `+9` lines. |

**Not changed:** `book/_static/custom.css`, `interactive/src/**`, `interactive/package*.json`,
`scripts/export_widget_data.py`, both `abide_*.json` artifacts, the widget
config JSON, `book/config/eda_phenotype_columns.json`, `_toc.yml`,
`requirements.txt`, every existing test file, `interactive/e2e/**`,
`interactive/e2e-book/chapter01.spec.ts`.

Generated / not committed (verified absent from `git status`):
`book/_build/`, `book/.jupyter_cache/`, `book/_static/widgets/app/`,
`interactive/node_modules/`, `**/__pycache__/`, Playwright artifacts,
scratchpad execution copies.

---

## 10. Corrected cell / visibility counts

### The WP06 arithmetic error

WP06 `WP06_EXACT_CHANGELOG.md` §3 ("Visibility counts (22 code cells)") printed:

| | visible | hide-input | hide-cell | sum |
|---|---|---|---|---|
| WP06 "Before" | 12 | 9 | 4 | **25** |
| WP06 "After" | 12 | 7 | 3 | **22** |

The "Before" row sums to **25**, not 22, so the table is internally inconsistent.
The transitions WP06 actually lists — V1 `hide-cell → hide-input`; V2, V3, V4
`hide-input → visible` — imply the true **pre-WP06** split was
**9 visible / 9 hide-input / 4 hide-cell = 22**, and applying them gives
**12 visible / 7 hide-input / 3 hide-cell = 22**. The total code-cell count was
**22 throughout WP06** — it was never 25, and "visible" was never 15. (The WP07
brief's alternative guess of "25 code cells / 15 visible" also does not hold: it
adds the inconsistent 25 total to the correct post-state breakdown.)

### Recount from the actual notebooks

**At `wp07-start`** (`book/chapters/chapter_01/exercise_01.ipynb`, verified with
`nbformat`): **81 cells = 22 code + 59 markdown + 0 raw.**
Code visibility: **12 visible / 7 `hide-input` / 3 `hide-cell` / 0 `hide-output`.**
Only `hide-input` and `hide-cell` tags appear anywhere; 81 unique ids.

**After WP07** (canonical): **84 cells = 23 code + 61 markdown.**
Code visibility: **12 visible / 8 `hide-input` / 3 `hide-cell` / 0 `hide-output`.**

| change | Δ cells |
|---|---|
| + `{admonition} Run or download this notebook` (markdown) | +1 md |
| + "The same basic plot…" one-liner (markdown) | +1 md |
| + AGE_AT_SCAN histogram example (code, `hide-input`) | +1 code, +1 hide-input |
| − item 4 from the `info()` "Think first" card | 0 (in-cell edit) |

**Portable notebook** (`book/downloads/chapter_01/exercise_01_portable.ipynb`):
**84 cells = 23 code + 61 markdown.** All hide tags stripped, so every code cell
renders normally; all `outputs` empty. 84 unique ids (`portable-banner`,
`portable-setup`, + 82 canonical ids passed through; 2 canonical admonitions
dropped).
