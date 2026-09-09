# WP07 implementation report — final notebook corrections and portable Colab/VS Code notebook

## Outcome

Status: **SUCCESS**

All seven user-requested corrections are applied, the non-functional
primary-sidebar toggle is diagnosed and **repaired** (not merely hidden), and a
deterministic, generated portable notebook now exists for Colab / VS Code /
Jupyter use without weakening the browser-native Jupyter Book version. Every
verified WP05 analysis result and all three browser activities are preserved.
The full CI-equivalent suite is green, including two byte-identical consecutive
notebook builds.

One item needs Yoav's attention and one fact is unavoidable until merge — both
are called out below.

## Git safety checkpoint

- Branch: `feature/reusable-interactive-widgets` (confirmed; not changed).
- Starting HEAD: `6c083c4` ("WP06 report: document editorial and design changes").
- Pre-existing working-tree items captured in the checkpoint: the WP-process
  update to `WPs/README.md` and the new `WPs/WP07_FINAL_CORRECTIONS_AND_PORTABLE_NOTEBOOK.md`.
  No build output, cache, `.DS_Store`, credential, token, or private data was
  present or committed.
- **Checkpoint commit: `d201cecd169c23ff148294d1410f9441a8a3d33e`** ("checkpoint: before WP07").
- **Checkpoint tag: `wp07-start`** (annotated; points at `d201cecd`). `wp07-start`
  did not already exist, so no numeric suffix was needed.
- **Implementation commit: `1b209c89db990c6fe316d439432fa9f872cd461f`**
  ("WP07: fix notebook UX and add portable Colab version").
- Report commit: "WP07 report: document final corrections" — hash in the terminal
  summary (a report cannot contain its own commit hash).
- Retraction guidance (identification only; no reset/revert performed): to undo
  WP07, `git revert` the implementation commit and the report commit, or reset to
  `d201cecd` / tag `wp07-start`. Leave `wp01-start`…`wp06-start` intact.

## WP06 baseline (run before any WP07 change)

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
| `rm -rf book/_build && jupyter-book build book` | exit 0, **9 warnings** (all pre-existing: `syllabus` toctree title ×N, `README` not in toctree, missing `logo.png`), **no `*.err.log`** |
| `npm run test:e2e:book` (built book `e2e-book/`) | **9 / 9** |
| `diagnose_sidebar.mjs` (Playwright, 1280 / 1024 / 390 px) | article-header "Toggle primary sidebar" button: **no observable effect at any viewport** (mouse or keyboard) — captured before changing it |

Baseline fully green.

## 1. The primary-sidebar toggle — exact root cause and resolution

### Root cause

The built Chapter 1 page (sphinx-book-theme 1.3.0 on pydata-sphinx-theme 0.17.1)
renders **two** `.primary-toggle` buttons:

1. `#pst-header .primary-toggle` — accessible name "Site navigation";
   **`display:none` at every width** (`sphinx-book-theme.css`:
   `.bd-header button.sidebar-toggle{display:none}`). `#pst-header` itself is
   `height:0` on narrow viewports.
2. `.bd-header-article .primary-toggle` — accessible name "Toggle primary
   sidebar"; **visible at every width**. This is the button the reader sees and
   the one the user reported.

`pydata-sphinx-theme.js` and `sphinx-book-theme.js` each bind their handler with
`document.querySelector(".primary-toggle")`, which returns the **first** DOM
match — button 1, the hidden one. Button 2 has **no click or keyboard handler at
all**. Clicking or pressing Enter/Space on it does nothing (verified: no error,
no modal, no class change, no sidebar movement) at 1280, 1024, and 390 px.

At ≥ 992 px the primary sidebar is permanently visible, so the button is also
*redundant* there. At 390 px the primary sidebar is hidden and this dead button
is the **only** control offered for the site navigation — so on mobile there was
no working way to open the nav.

### Resolution — repair, narrowly scoped, no theme monkey-patching

`book/_static/sidebar-toggle-fix.js` (new, wired through
`sphinx.config.html_js_files`) forwards activation from each visible
article-header toggle to its already-correctly-wired hidden counterpart:

```js
visible.addEventListener("click", (e) => { e.preventDefault(); hidden.click(); });
```

The theme's own logic then runs unchanged:

| viewport | activation (mouse / Enter / Space) | observable result |
|---|---|---|
| 1280 / 1024 px | toggles `pst-sidebar-hidden` on `#pst-primary-sidebar` | the persistent sidebar slides out (`margin-left:-256px`, `visibility:hidden`, `opacity:0`); activating again brings it back |
| 768 / 390 px | `#pst-primary-sidebar-modal.showModal()` | the navigation `<dialog>` opens with the real nav links inside; Escape / outside-click closes it and moves the links back |

No theme file is patched; the shim only attaches standard listeners to stable
theme DOM and delegates. The `.secondary-toggle` (on-this-page) button is wired
the same way for consistency, though WP07 only required the primary one.

### Regression tests

`interactive/e2e-book/sidebar-toggle.spec.ts` (4 tests, all green) assert an
**observable** sidebar state change — never "click produced no error":

1. desktop: the toggle is visible; click collapses the sidebar
   (`pst-sidebar-hidden` **and** it leaves the viewport) and re-expands it;
2. desktop: keyboard Enter and Space both toggle it;
3. 390 px: click opens `#pst-primary-sidebar-modal`, the
   "…Exploratory data analysis…" nav link is visible inside, Escape closes it;
4. a loop over 1280 / 1024 / 768 / 390 px: wherever the button is visible, one
   click **must** change `{pst-sidebar-hidden, modalOpen}` or the test fails.

The built-book Playwright suite is now **13** tests (was 9).

## 2. Opening text

### About this exercise (`a1b2c30d4e5f`)

- **Every time estimate removed** — "Budget about 60–75 minutes for the full
  notebook" is gone; the *Guided tutorial* / *Self-study* modes remain, without
  durations.
- The claim **"Every question has a revealable answer" is removed.** New wording:
  *"Some questions have a **Check your reasoning** dropdown that walks through the
  argument; open discussion questions are deliberately left without one fixed
  answer."*
- Assessment / deeper-understanding point added: *"They are there to move past
  simply running code toward explaining the analytical choices behind it, and the
  kind of reasoning they ask for is close to what course assessment and exam
  questions expect."* — no promise of verbatim exam questions.

### How to use this notebook (`b2c3d40e5f6a`)

Rewritten to four bullets and **no longer enumerates the interactive
activities**: work through sections in order and pause at each *Think first*
card; "Some activities are interactive and run directly in your browser, with
nothing to install."; "To execute the code cells or change the code yourself,
open the notebook in Colab or download the portable `.ipynb` version using the
links at the top of this notebook."; some answers/checklists are revealable,
open questions may not have one fixed answer.

### New "Run or download this notebook" card (`c4d5e6f7a8b9`)

Inserted immediately after the H1 title. Contains the two stable controls
(see §3).

## 3. Colab / download path

### The old control is removed

`launch_buttons.colab_url` is deleted from `book/_config.yml`. That option made
sphinx-book-theme build a "Launch → Colab" URL from `repository.branch` (`main`)
and the **canonical** path
`.../blob/main/book/chapters/chapter_01/exercise_01.ipynb` — i.e. the embedded
Jupyter Book notebook (iframes + MyST), and on `main` still the pre-WP01 version.
The built page now has no `dropdown-launch-buttons` and the only
`colab.research.google.com` URL on it is the portable link.

### The new controls (in the card at the top of the notebook)

- **Open the portable notebook in Colab** →
  `https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/blob/main/book/downloads/chapter_01/exercise_01_portable.ipynb`
- **View or download the portable `.ipynb`** →
  `https://raw.githubusercontent.com/yoavmp/ml-neuro-tutorials/main/book/downloads/chapter_01/exercise_01_portable.ipynb`
  (labelled "View or download" because raw GitHub may display rather than
  download in some browsers)

Both point at `main`, not the feature branch.

### Canonical notebook vs portable notebook

| | canonical `book/chapters/chapter_01/exercise_01.ipynb` | portable `book/downloads/chapter_01/exercise_01_portable.ipynb` |
|---|---|---|
| role | single source of truth; built by Jupyter Book into the GitHub Pages site | generated derivative for running / editing the code |
| activities | three `<iframe>` browser activities (kernel-free, on the static site) | replaced by a short Markdown pointer + HTTPS link to the published page |
| directives | MyST `{admonition}` / `{dropdown}` | `#### heading` and `<details><summary>` (render in Colab, VS Code, Jupyter) |
| hide tags | `hide-input` / `hide-cell` (togglebutton in the built HTML) | stripped — every code cell is plainly visible |
| data columns | read from `book/config/eda_phenotype_columns.json` (repo file) | the 39-name list embedded inline |
| ABIDE CSV | pinned raw GitHub URL (neurohackademy mirror) | same URL, verbatim |
| maintenance | edited by hand | **never** hand-edited — regenerated by `scripts/build_portable_notebook.py --write`; CI fails if stale |

The portable notebook is **generated, not a parallel copy.** It carries a banner
identifying it as the portable derivative and linking back to the course page.

### What works where

- **Colab:** numpy / pandas / matplotlib / seaborn are preinstalled, so the
  notebook runs with nothing to install. All 23 code cells execute; the three
  activity cells are Markdown links to the course page. `<details>` dropdowns and
  `$$…$$` math render.
- **Downloaded VS Code / Jupyter:** same, plus a `## Setup` cell pointing at
  `requirements.txt` and a single commented `# %pip install …` line for the rare
  missing-package case. No install cell runs by default; nothing is
  reinstalled/downgraded.
- **Differences from the published book, and why:** no embedded activities (they
  need the built site's `_static/widgets/` app and same-origin config/data — not
  portable); MyST cards become headings / `<details>` (MyST only renders under
  Sphinx); collapsed code is shown in full (no togglebutton outside Sphinx). The
  analysis, its order, and its outputs are identical.

### The unavoidable fact

The feature branch is local. **Any GitHub-`main` URL — the two portable links
included — will resolve to the older `main` content until WP01–WP07 are merged
and pushed.** The links are deliberately kept on `main` (not the temporary
branch) so they become correct automatically after merge. Remote end-to-end
validation of the links (HTTP fetch + content equality) is therefore **deferred
to after merge/push**, and is not reported as passing here.

## 4. Portable execution evidence

`scripts/smoke_portable_notebook.py` copies the committed portable notebook into
a fresh `mktemp -d` **outside the repository root**, runs every cell with a clean
`nbclient` kernel whose working directory is that temp dir (so no repo-relative
path can accidentally resolve), and checks the outputs:

- **0 cell errors**, 23 / 23 code cells executed;
- `Data table shape: (1114, 39)`;
- `describe().T` block: AGE mean 14.9 / sd 9.2; FIQ mean 111.0 / median 112.0 /
  available 1015; SRS_TOTAL_RAW mean 55.3 / median 43 / available 785;
- FIQ by diagnosis: Autism n 479 (median 108.0), Control n 536 (median 115.0);
- `IQR rule flags ages outside [-3.8, 31.1] years` / `56 of 1114 participants
  flagged for inspection`;
- SEX × DX_GROUP: 77 / 181 / 444 / 412; within-sex % 29.8 / 70.2 (F),
  51.9 / 48.1 (M).

Every value matches the canonical notebook and the WP05/WP06 verified results.
This script also runs in CI.

## 5. Removed question

Item 4, *"Why might pandas assign the `object` data type to a column?"*, is
removed from the `info()` "Think first" card (`e05d9a3c-…`). Items 1–3 are
unchanged, verbatim, and need no renumbering. There was **no dedicated answer
dropdown** for it (the following "#### Interpreting `info()`" cell is a
strengths/limitations discussion, unchanged), so nothing was orphaned. A `grep`
over every cell confirms the prompt string appears nowhere in the notebook.

## 6. Collapsible Python age histogram

A one-line Markdown lead ("The same basic plot can be produced in Python…") plus
a `hide-input` code cell (`e6f7a8b9c0d1`) are inserted immediately after the
histogram `<iframe>` cell:

```python
fig, ax = plt.subplots(figsize=(8, 4))
sns.histplot(data=phenotypes, x="AGE_AT_SCAN", bins=25,
             color="steelblue", edgecolor="white", ax=ax)
ax.set(title="Distribution of age at scan",
       xlabel="Age at scan (years)", ylabel="Number of participants")
plt.show()
```

`AGE_AT_SCAN`, **25 bins**, x-axis in years, y-axis "Number of participants",
concise title, notebook's own `steelblue` / white styling.

**Visibility: `hide-input`, not `hide-cell`.** The rendered static histogram sits
directly under the interactive one and shows the same 1,114 ages, so the output
has teaching value and stays visible; only the code folds. Verified in the built
HTML: the "Show code cell source" toggle is present and the output image renders.
The portable notebook keeps this as an ordinary visible, runnable cell.

## 7. IQR defined explicitly

The range-check intro (`58db4c1fc44e`) now, in order: states that crossing the
interval **flags a value for inspection and does not prove it is an error**;
defines `Q1` and `Q3` as the 25th and 75th percentiles; then

$$\mathrm{IQR} = Q_3 - Q_1$$

**before** presenting the fences $Q_1 - 1.5\,\mathrm{IQR}$ and
$Q_3 + 1.5\,\mathrm{IQR}$.

Rendering: the built HTML contains
`<div class="math notranslate nohighlight"> \[ \mathrm{IQR} = Q_3 - Q_1 . \]</div>`
(MathJax display-math input, not raw `$$` text); the `dollarmath` MyST extension
is already enabled and MathJax is loaded on the page. In the portable notebook
the `$$…$$` blocks render via Colab/Jupyter MathJax.

## 8. Stripplot seeding

The FIQ violin+strip cell (`80632a35b296`) now saves the global RNG state, calls
`np.random.seed(0)` immediately before `sns.stripplot(...)` (seaborn draws the
jitter from `np.random`), and restores the state right after — so no later cell
sees a changed RNG stream. No `stripplot` argument changed (`jitter=0.25` kept).

Determinism evidence:

- isolated re-render of the cell three times, including once after consuming
  1,000 random draws and once after `np.random.seed(12345)`: **identical**
  stripplot point-offset hash and identical PNG hash each time; the post-cell
  RNG state differs across runs, confirming `set_state` restored the pre-existing
  stream;
- two consecutive `rm -rf book/_build book/.jupyter_cache && jupyter-book build`
  runs produce a **byte-identical set of six figure PNGs** (before WP07 the
  violin/strip PNG changed hash on every run — WP06 deviation 6, now closed).

## 9. Corrected cell / tag counts

WP06's `WP06_EXACT_CHANGELOG.md` §3 printed a "Before" visibility row (12 / 9 / 4)
that sums to **25**, not the stated 22 — an internal inconsistency. Recounted
directly from the notebooks with `nbformat`:

| | cells | code | markdown | visible | hide-input | hide-cell |
|---|---|---|---|---|---|---|
| true pre-WP06 (implied by WP06's own transitions) | 79 | 22 | 57 | 9 | 9 | 4 |
| **at `wp07-start`** (measured) | **81** | **22** | **59** | **12** | **7** | **3** |
| **after WP07** (canonical, measured) | **84** | **23** | **61** | **12** | **8** | **3** |
| portable notebook (measured) | 84 | 23 | 61 | 23 | 0 | 0 |

The code-cell total was **22 throughout WP06** (never 25, never "15 visible").
WP07 adds one `hide-input` code cell (the histogram example) and two markdown
cells (the run/download card, the histogram one-liner). Only `hide-input` and
`hide-cell` tags appear anywhere; all cell ids are unique;
`nbformat.validate` passes on both notebooks.

## 10. Files changed

Implementation commit `1b209c89` (10 files, `+2810 / −19` vs `d201cec`):

| Path | Change |
|---|---|
| `book/chapters/chapter_01/exercise_01.ipynb` | 81 → 84 cells; opening text (2 edits + 1 new card); object-dtype question removed; `hide-input` histogram example + lead line added; IQR paragraph rewritten with two `$$` blocks; stripplot jitter seeded. `+122 / −19`; no output/`execution_count` churn on existing cells. |
| `book/_static/sidebar-toggle-fix.js` | **new** — 57-line event-forwarding shim (see §1). |
| `book/_config.yml` | remove `launch_buttons:`; add `exclude_patterns: [downloads/*]`; add `sphinx.config.html_js_files: [sidebar-toggle-fix.js]`. |
| `book/downloads/chapter_01/exercise_01_portable.ipynb` | **new** — generated portable notebook (84 cells). |
| `scripts/build_portable_notebook.py` | **new** — deterministic `--write` / `--check` generator. |
| `scripts/smoke_portable_notebook.py` | **new** — out-of-repo execution + key-value check (CI + local). |
| `tests/test_build_portable_notebook.py` | **new** — 18 tests (transform / iframe / directive / data loading / determinism / `--check` staleness). |
| `tests/test_notebook_corrections.py` | **new** — 10 tests asserting every WP07 canonical-notebook correction. |
| `.github/workflows/deploy.yml` | 3 steps added: `python -m unittest discover -s tests -v`; `build_portable_notebook.py --check`; `smoke_portable_notebook.py`. |

**Not changed:** `book/_static/custom.css`, `interactive/src/**`, `scripts/export_widget_data.py`,
both `abide_*.json` artifacts, widget config JSON, `book/config/eda_phenotype_columns.json`,
`_toc.yml`, `requirements.txt`, `interactive/package*.json`, existing test files,
`interactive/e2e/**`, `interactive/e2e-book/chapter01.spec.ts`.

Generated / not committed (verified absent from `git status`): `book/_build/`,
`book/.jupyter_cache/`, `book/_static/widgets/app/`, `interactive/node_modules/`,
`**/__pycache__/`, Playwright artifacts, scratchpad copies.

## 11. Tests

| Check | Result |
|---|---|
| `npm run typecheck` | **PASS** (0 errors) |
| `npm run test:unit` (frontend) | **143 / 143** (suite unchanged) |
| `npm audit --omit=dev` | **0 vulnerabilities** |
| `npm run build` (frontend) | **PASS** (only the pre-existing 500 kB Plotly-chunk warning; JS byte-identical, no `interactive/src` change) |
| `python scripts/export_widget_data.py --check --artifact all` | **PASS** (both artifacts valid + canonical, untouched) |
| `python -m unittest discover -s tests` | **73 / 73** (45 export + 18 portable-generator + 10 notebook-corrections) |
| `python scripts/build_portable_notebook.py --check` | **PASS** (byte-identical to the committed file; `--write` twice is a no-op) |
| `python scripts/smoke_portable_notebook.py` | **PASS** (out-of-repo execute, 0 errors, key values matched) |
| `npx playwright test` (standalone `e2e/`) | **40 / 40** |
| `rm -rf book/_build && jupyter-book build book` | **PASS** — "build succeeded, **9 warnings**" (identical pre-existing set: `syllabus` title ×N, `README` not in toctree, `logo.png`); **no `*.err.log`** |
| `find book/_build -name '*.err.log'` | empty |
| `npm run test:e2e:book` (built book) | **13 / 13** (9 activity + **4 new sidebar** regression tests) |
| Two consecutive clean notebook builds (cache cleared) | **byte-identical** set of 6 figure PNGs |
| IQR math in built HTML | renders as `\[ \mathrm{IQR} = Q_3 - Q_1 . \]` (MathJax), not raw markup |
| Old Colab launch control | absent from the built page; portable links present and point at the portable path on `main` |
| All three browser activities | still render and respond (built-book e2e) |

Against WP §9's 15 required assertions: **1** ✓ (sidebar changes observable
state / clean regression tests) · **2** ✓ (no time estimate) · **3** ✓
(assessment point, no verbatim promise) · **4** ✓ ("How to use" not enumerated;
browser/Colab/download guidance) · **5** ✓ (object-dtype question and any
orphan absent) · **6** ✓ (histogram cell: `AGE_AT_SCAN`, 25 bins, executes,
`hide-input`) · **7** ✓ (IQR equations render) · **8** ✓ (`--check` passes,
generation deterministic) · **9** ✓ (portable executes outside the repo) ·
**10** ✓ (built-page links target the portable path on `main`; remote fetch
deferred to post-merge, not falsely passed) · **11** ✓ (three activities) ·
**12** ✓ (existing unit / standalone / built-book tests green) · **13** ✓ (clean
build, no `*.err.log`) · **14** ✓ (deterministic jittered figure across two
builds) · **15** ✓ (no new off-origin dependency — the shim is a local
`_static` file; the portable notebook reuses the pinned ABIDE-II CSV; the
Colab/raw links are on pre-existing allowed hosts).

## 12. Which items require Yoav's attention

1. **Merge and push the branch, then re-check the two portable links.** Until
   WP01–WP07 land on `main`, the Colab link and the raw-`.ipynb` link resolve to
   the older `main` content. After merge, open each once to confirm Colab loads
   the portable notebook and the raw link serves the file. (Design constraint,
   not a defect — the links are intentionally on `main`.)
2. **The theme's generic "Download this page → .ipynb" button** still serves the
   canonical page source (`_sources/chapters/chapter_01/exercise_01.ipynb`). It
   is honestly labelled "Download source file" and is **not** the misleading
   *Colab* control WP §4 targets, so it was left in place: the two Sphinx knobs
   tried (`html_copy_source: false`, `use_download_button: false`) either did not
   remove it in Jupyter Book 1.0.4 or left a broken link. If you want it gone,
   the low-risk route is a small `sphinx-book-theme` template override in
   `book/_templates/`, which is a change worth its own review.

## 13. Deviations from instructions

1. **`html_js_files` used for the sidebar fix.** WP §2.4 prefers "CSS/config/
   markup"; a CSS-only repair was not possible (the working handler is bound to a
   permanently-hidden button, and `#pst-header` is `height:0` on mobile). The
   shim is 57 lines, attaches only standard listeners to stable theme DOM, patches
   no theme internals, and delegates to the theme's own behaviour — the least
   fragile option, and not the "theme monkey-patching" §2.7 warns against.
2. **`.secondary-toggle` also forwarded.** WP07 only required the primary toggle;
   the secondary ("on this page") button had the identical dead-handler bug, so
   the same one-line forward was applied for consistency. Covered indirectly by
   the "never a no-op" test only for the primary button.
3. **Portable path is `book/downloads/chapter_01/exercise_01_portable.ipynb`** —
   exactly the path the WP suggested; `exclude_patterns: [downloads/*]` was added
   so Sphinx does not treat it as a book page (it would otherwise emit a new
   "not in any toctree" warning).
4. **Two navigation admonitions dropped from the portable notebook.** The
   generator omits "Run or download this notebook" and "How to use this notebook"
   (both are Jupyter-Book-page navigation); the prepended portable banner + setup
   cells cover the portable-relevant guidance.
5. **CI now also runs the Python `unittest` suite** (`discover -s tests`). It was
   not previously wired into `deploy.yml`; adding it was the natural place to run
   the new generator tests and it also picks up `test_export_widget_data`.
6. **Node 24 locally** (`engines` `>=20.19.0 <25`; CI pins 22). `npm audit
   --omit=dev` is clean; no Vite/Vitest change in this WP.

## 14. Unresolved risks

- **Remote link validation is deferred** until merge/push (§3, §12.1). The link
  *strings* are correct; their *targets* are only current on `main` after merge.
- **`sidebar-toggle-fix.js` depends on two stable theme selectors** —
  `.bd-header-article .primary-toggle` and `#pst-header .primary-toggle`. A major
  sphinx-book-theme / pydata-sphinx-theme upgrade that renames or reorders those
  would need a re-check; the shim fails safe (does nothing) if either selector
  stops matching. The regression tests would catch a regression.
- **Portable notebook depends on Colab keeping numpy/pandas/matplotlib/seaborn
  preinstalled.** If Colab drops one, the user hits a clear `ImportError` and the
  commented `# %pip install …` line in the setup cell is the fix; the smoke test
  would not catch a Colab-only change.
- **`pandas` / `numpy` are unpinned in `requirements.txt`.** The notebook and the
  portable notebook execute against whatever the environment resolves (locally
  pandas 3.0.5 / numpy 2.5.3; CI installs latest on Python 3.11). A future major
  pandas release could change behaviour; out of scope for WP07.
- **Page-level CDN, unchanged** — the Chapter 1 *page* still loads MathJax from a
  CDN (pre-existing sphinx-book-theme behaviour). The activity iframes and the
  new shim are CDN-free. Out of scope, as in WP04–WP06.
- **`jupyter-book build` still exits 0 on a notebook execution error**; the CI
  `*.err.log` guard remains the safety net and must be kept.

## 15. Recommendations — WP08 only (do not create or begin WP08)

- **After merge:** open the two portable links once and confirm; then the
  "remote HTTP/content equality" check in the portable-notebook verification can
  move from *deferred* to *passing*.
- **Remove the "Download source file" button** cleanly via a
  `book/_templates/` override if the canonical `.ipynb` should not be offered at
  all (§12.2).
- **Add the portable notebook to a visible "Downloads" location** in the book
  (e.g. a short appendix page) so it is discoverable without reading the Chapter 1
  opening.
- **Self-host MathJax / trim `sphinx-thebe`** so the whole published page — not
  only the iframes and the shim — is CDN-free (carried from WP06).
- **Pin `numpy` / `pandas` / `matplotlib` / `seaborn`** in `requirements.txt` and
  mirror the pins in the portable setup cell, so canonical and portable
  execution are reproducible over time.
- **Dynamic iframe height** for the three activities (carried from WP06).

## Instructions for reviewer

Paste this entire report (`WP07_REPORT.md`) into the ChatGPT conversation that
produced WP07. `WP07_EXACT_CHANGELOG.md` is the companion line-item record.
