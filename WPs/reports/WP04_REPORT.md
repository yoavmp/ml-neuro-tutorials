# WP04 implementation report

## Outcome
Status: SUCCESS

The second production activity, `eda-retention`, is implemented on the WP02/WP03
browser-native runtime and embedded in the Chapter 1 EDA notebook. Students tick
candidate core variables in accessible grouped checkboxes and immediately see how
complete-case filtering changes the retained ABIDE sample **overall** and **per
acquisition site**. `scripts/export_widget_data.py` now emits a second
deterministic artifact — `book/_static/widgets/data/abide_retention.json`
(71,543 bytes, SHA-256 `6b2965650311d122a3acdcc7fc362dcb6dca4408c1a8dbd952e04beb2eb73320`,
1,114 aligned rows, `SITE_ID` + 13 curated candidate columns, missing → JSON
`null`) — from the **same** pinned source URL + SHA-256 as the histogram, with a
single deliberately narrow `SITE_ID` exception to identifier rejection.
Complete-case retention is a pure, DOM/Plotly-free module
(`interactive/src/retention.ts`) with 16 unit tests, independently cross-checked
against pandas: the shipped default core set (`DX_GROUP`, `AGE_AT_SCAN`, `SEX`,
`FIQ`) retains **1,015 / 1,114 = 91.1131 %**. The obsolete `ipywidgets`
retention interface and its "requires a kernel" note were replaced in
`exercise_01.ipynb` with a Markdown iframe via a three-cell → one-cell `nbformat`
edit; after the replacement passed standalone and built-page tests, the orphan
`exercise_01_widgets.ipynb`, the `ipywidgets` / `jupyterlite-sphinx` /
`jupyterlite-pyodide-kernel` / `voici` dependencies, and the stale
`jupyterlite_sphinx` block in `book/_config.yml` were removed. The **Open in
Colab** button is unchanged. Every WP04 §8 command passes locally.
`npm audit --omit=dev` reports 0 vulnerabilities; full-tree dev-only advisories
are carried forward per WP04 (no Vite/Vitest upgrade in this WP).

## Git safety checkpoint
- Branch: `feature/reusable-interactive-widgets`
- Starting HEAD: `a417761694b141683da41245ca17e5faab3d263d` ("WP03 report: document results")
- Checkpoint commit: `9818cc3956045912298516542d73b87e04cc68f3` ("checkpoint: before WP04")
- Checkpoint tag: `wp04-start` (annotated, tag object `52333b610bde3fc2a6c7b18097c4fe517d6706ff`, points at `9818cc3`)
- Retraction guidance: identify the checkpoint only; do not execute a reset or
  revert. To undo WP04, `git revert` the implementation commit `851b3f7` and this
  report commit, or reset to `9818cc3` / tag `wp04-start` at your discretion.
  Leave `wp01-start` / `wp02-start` / `wp03-start` intact.

The checkpoint captured the two pre-existing legitimate working-tree changes
only: the WP-process update to `WPs/README.md` and the new (untracked) WP brief
`WPs/WP04_MISSING_DATA_RETENTION.md`. No build output, caches, `.DS_Store`,
credentials, or private data were present or committed. The full ABIDE CSV was
**not** committed.

## Work completed

### 1. Mandatory checkpoint and baseline
- Read `CLAUDE_INTERACTIVE_WIDGETS.md`, `WPs/README.md`,
  `WPs/WP04_MISSING_DATA_RETENTION.md`, and `WPs/reports/WP03_REPORT.md` in full.
- Confirmed branch `feature/reusable-interactive-widgets`.
- Inspected `git status --short` / `git diff` / the untracked WP brief, then
  created `checkpoint: before WP04` (`9818cc3`) and annotated tag `wp04-start`.
- Ran the WP03 clean baseline before any WP04 change: `npm ci` (OK),
  `npm run typecheck` (0 errors), `npm run test:unit` (64/64), `npm run build`
  (OK, Vite 500 kB chunk warning only), `npm audit --omit=dev` (0),
  `npx playwright test` (16/16), `python -m unittest … test_export_widget_data`
  (19/19), `export_widget_data.py --check` (OK),
  `rm -rf book/_build && jupyter-book build book` (exit 0, "11 warnings", no
  `*.err.log`), `npm run test:e2e:book` (3/3). Baseline fully green; no
  diagnosis required.

### 2. Deterministic retention data export
- Extended `scripts/export_widget_data.py` to a two-artifact registry
  (`ARTIFACTS = {histogram, retention}`) without changing histogram behaviour:
  - `build_retention_artifact()` emits `SITE_ID` (documented strings, no
    missing) followed by the 13 approved candidate variables (documented integer
    category codes / numbers, `null` for missing; `NaN`/`Infinity` rejected at
    build and serialize time). No field was substituted — all 13 candidates and
    `SITE_ID` are present in `book/config/eda_phenotype_columns.json` and the
    pinned source.
  - Artifact carries `schemaVersion`, `activity: "eda-retention"`, pinned
    `source` (url, sha256, sourceRows 1114, sourceColumns 348), `rowCount`,
    `site` metadata (`field`, `siteCount` 19, `sites` = every distinct site with
    its total, in **first-appearance** order), per-variable
    `{name, availableN, missingN}`, and `columns`. No generation timestamp, no
    machine paths.
  - `validate_retention_artifact()` enforces the narrow exception: exactly
    `SITE_ID` is allowed as an identifier-shaped column and must be a non-empty
    string on every row; every *other* column must be a curated, non-identifier
    candidate and an aligned number-or-null array; site metadata must match the
    data (order, per-site totals, sum == rowCount); `availableN` must equal the
    real non-null count with `availableN + missingN == rowCount`. `SUB_ID`,
    `SCANNER_ID`, and arbitrary `*_ID` names remain refused by the shared token
    regex.
  - CLI: added `--artifact {histogram,retention,all}` (default `all`).
    `--refresh` / `--check` with no `--artifact` now cover **both** committed
    files (WP03 `--check` invocation unchanged in effect). `--artifact
    histogram` only touches `abide_histogram.json`; `--artifact retention` only
    touches `abide_retention.json` — a refresh of one cannot rewrite or delete
    the other (asserted by `ArtifactRegistryTests`).
  - Byte-for-byte determinism preserved (`sort_keys=True`, compact separators,
    single trailing newline). Two consecutive `--refresh --artifact retention`
    runs produced an identical SHA-256; the histogram artifact was untouched
    (`git diff` empty) across the retention refresh.
- `tests/test_export_widget_data.py`: +26 stdlib `unittest` cases on tiny
  in-memory CSV fixtures, no network — strings/categories preserved as codes,
  valid `0` not treated as missing, null/alignment in row order, first-
  appearance site metadata, the exact `SITE_ID` exception, rejection of
  `SUB_ID` / arbitrary `*_ID` / the site field as a variable / a non-`SITE_ID`
  site field / a missing site label, all `validate_retention_artifact` failure
  branches, deterministic round-trip, both artifact modes, and that the two
  committed files pass their own validators. Total suite 45 tests.

### 3. Retention configuration and schema
- Added `book/_static/widgets/configs/eda_retention.json`: title,
  `instructions`, `data`, `siteField: "SITE_ID"`, `siteLabel`, four `groups`
  (Demographics and diagnosis / Cognitive scores / Diagnostic and behavioral
  measures / Medication and scan conditions) each with `{name,label}` variables,
  `defaultVariables: ["DX_GROUP","AGE_AT_SCAN","SEX","FIQ"]`,
  `chart: {metric: "retained-percentage"}`, `lowRetentionWarningPct: 50`, three
  `reflectionPrompts`.
- Extended the versioned discriminated union in `interactive/src/config.ts` with
  a `.strict()` `eda-retention` member. `checkSemantics()` adds the cross-field
  checks the union cannot express: unique group keys, no duplicate variable name
  across groups, `siteField` not also a selectable variable, every
  `defaultVariables` entry present in some group, no duplicate defaults. 11 new
  config unit tests, including one that loads and validates the shipped
  `eda_retention.json`. Histogram config tests unchanged (34 config tests total).

### 4. Pure complete-case retention calculation
- Added `interactive/src/retention.ts#computeRetention(columns, siteLabels,
  selected)` — no DOM, no Plotly, no fetch.
  - Missing means JSON `null` only; a valid `0`, `false`, or a documented
    category string is present. A row is retained iff every selected column is
    non-null on that row.
  - No selection → every row retained, `noSelection: true`, and
    `message = "All participants are retained because no completeness criterion
    is currently applied."`
  - Deterministic per-site order = first appearance in `siteLabels`.
  - Throws on a duplicate selected variable, a selected name absent from
    `columns`, a column whose length ≠ `siteLabels.length`, and a missing/blank
    site label.
  - Returns overall `{total, retained, excluded, retainedPct}`, per-site
    `{site, total, retained, excluded, retainedPct}`, `selected`, `noSelection`,
    `message`.
- 16 unit tests: one variable, multiple variables, no selection, no missingness,
  all-excluded, site-specific missingness, valid `0` / category strings,
  deterministic first-appearance ordering, conservation
  (`retained + excluded == total`) overall and per site across five selections,
  all four validation throws, **and** three tests against the committed
  `abide_retention.json` asserting the pandas-cross-checked expected values
  (default 1,015; behavioral pair 119; no-selection 1,114).

### 5. Retention component
- Added `interactive/src/retention-data.ts` — the component-owned Zod schema for
  the artifact (kept DOM/Plotly-free so it is unit-testable): `schemaVersion`
  literal, `activity` literal, positive `rowCount`, `source`, `site` metadata,
  per-variable metadata, `columns` as `Record<string, (number|string|boolean|
  null)[]>`, `superRefine` cross-checking column alignment, the non-empty-string
  `SITE_ID` column, rejection of any other identifier-shaped column, variable
  metadata vs data, and first-appearance site order / totals. 10 unit tests,
  including validation of the committed artifact (rowCount 1114, siteCount 19,
  the 14 expected columns).
- Added `interactive/src/components/retention.ts` and registered it in
  `registry.ts`:
  - Validates the artifact through `parseAbideRetentionData`; a data file
    missing a configured column or the site column throws a readable error.
  - Accessible grouped checkboxes: one `<fieldset>`/`<legend>` per group, each
    variable a `<label for>` wrapping a real `<input type="checkbox">` with a
    visible `<span>` label and `data-testid="retention-var-<NAME>"`. Not a
    platform multi-select.
  - `Use suggested core set` / `Select all` / `Clear` buttons
    (`data-testid` `retention-suggested` / `-select-all` / `-clear`).
  - `data-testid="retention-selected"` lists and counts the selected variables;
    `data-testid="retention-stats"` shows
    `Retained N of TOTAL participants (P%) · X excluded`.
  - Plotly **bar** trace of retained-percentage by site (first-appearance
    order), `customdata = [retained, siteTotal]`, hovertemplate
    `%{x}<br>Retained %{customdata[0]} of %{customdata[1]} (%{y:.1f}%)` — no
    participant-level text. A dashed overall-retention line + annotation mirror
    the old Matplotlib figure.
  - Full `Plotly.react()` redraw on every checkbox `change` and every preset
    click.
  - Machine-testable state on the plot div: `data-selected`,
    `data-selected-count`, `data-total`, `data-retained-n`, `data-excluded-n`,
    `data-retained-pct` (2 dp), `data-site-count`, `data-bar-count`,
    `data-render-count`, `data-no-selection`, `data-low-retention`.
  - No selection → `data-testid="retention-message"` shows the explicit
    "no completeness criterion is currently applied" sentence and every row is
    retained.
  - `data-testid="retention-warning"` (amber cue + amber bars) appears when a
    selection retains `< lowRetentionWarningPct` (default 50 %) overall, with
    copy stating that 50 % is "a prompt to look closely, not a universal
    cutoff".
  - Rendered "Reflect" list from `reflectionPrompts` (compare core vs behavioral
    sets, identify disproportionately affected sites, explain why filtering
    changes sample composition).
  - Native form controls (keyboard-operable — tested with `Space`), responsive
    Plotly layout with `automargin`/`tickangle`, transparent paper/plot
    background and light/dark-aware axis/grid/bar colours via
    `prefers-color-scheme`.
- `interactive/src/styles.css`: `--warn-bg`/`--warn-fg` tokens (light + dark),
  `.widget-warning`, `.widget-controls button`, responsive
  `.widget-checkbox-groups` grid, `.widget-checkbox-group`/`legend`,
  `.widget-checkbox`.

### 6. Notebook integration and legacy cleanup
- `book/chapters/chapter_01/exercise_01.ipynb` edited with `nbformat` only
  (cells located by content):
  - Removed the `:::{note}` "requires an executable Python kernel" cell and the
    two `ipywidgets` code cells (`core_selector = widgets.SelectMultiple` /
    `widgets.interactive_output`), replacing all three with **one** Markdown
    cell (id `999ad285-…` reused from the removed note cell) holding a short
    intro and an `<iframe>` with `title`, `loading="lazy"`, `width="100%"`,
    `height="900"`, `style="width:100%;border:none;"` and
    `src="../../_static/widgets/app/index.html?config=../configs/eda_retention.json"`.
  - Placed immediately after the "Design a complete-case dataset" prose that
    asks students to choose core variables (which itself follows the
    site-missingness heatmap + "Interpret the heatmap" cells). The "Your
    decision" follow-up prose is preserved directly after the iframe.
  - Removed the now-dead `import ipywidgets as widgets`,
    `from IPython.display import display, clear_output`, and the
    `google.colab … enable_custom_widget_manager()` block from the setup cell.
    Repo-wide search confirmed `widgets` / `display` / `clear_output` were used
    only in the removed cells. The setup cell keeps numpy / pandas / plt / sns /
    `sns.set_theme`.
  - Notebook now 57 cells (was 59), all ids unique, `nbformat.validate` OK. The
    WP03 histogram iframe cell (id `23475ca3-…`) and all other prose / static
    Matplotlib/Seaborn figures are untouched. Diff: 12 insertions / 161
    deletions (the deletions are the removed widget source + kernel note).
- Removed the orphan `book/chapters/chapter_01/exercise_01_widgets.ipynb`
  (`git rm`); it was never in `_toc.yml`.
- `requirements.txt`: removed `ipywidgets`, `jupyterlite-sphinx`,
  `jupyterlite-pyodide-kernel`, `voici`. Repo-wide search confirmed no remaining
  `.py` / `.ipynb` / config uses them (only the removed notebook, the edited
  cells, and `book/_config.yml`).
- `book/_config.yml`: removed the entire `sphinx:` block
  (`extra_extensions: [jupyterlite_sphinx]` + `jupyterlite_contents` +
  `jupyterlite_bind_ipynb_suffix`). WP01 established `jupyterlite_contents`
  pointed at a **non-existent** file (`chapters/chapter_01/eda_widgets.ipynb`)
  and `book/_contents/` is empty, so the `lite/` app shipped zero project
  content. Nothing in `_toc.yml` or the notebooks references `lite/`. The
  `launch_buttons.colab_url` (Open in Colab) is unchanged.
- No notebook-level stored widget state existed (`nb.metadata` had no
  `widgets` key), so none was removed.
- Build now emits **9 warnings** (was 11). The removed instances are the
  `exercise_01_widgets.ipynb` "document isn't included in any toctree" warnings.
  The remaining distinct warnings — `syllabus` toctree title, `README.md` not in
  any toctree, missing `logo.png`, and a cosmetic `IPKernelApp` "kernel over TCP
  without encryption" line during execution — are all pre-existing and unrelated
  to WP04. No `lite/` directory is built; the built Chapter 1 page no longer
  requests `require.js` or `@jupyter-widgets/html-manager`.

### 7. Build, CI, and browser tests
- `.github/workflows/deploy.yml`: the offline artifact-check step now runs
  `python scripts/export_widget_data.py --check --artifact all` (validates
  **both** committed artifacts). All other steps (typecheck, unit, `npm audit
  --omit=dev`, Vite build, standalone Playwright, `jupyter-book build`,
  `*.err.log` guard, built-page Playwright, deploy provider) are unchanged and
  automatically pick up the new unit/e2e specs.
- `interactive/e2e/retention.spec.ts` (standalone app, run at site root **and**
  `/ml-neuro-tutorials/`): default suggested core set from the config; exact
  overall retention (`data-retained-n="1015"`, `data-retained-pct="91.11"`,
  1,114 total, 19 sites); a checkbox change alters retained N and the real bar
  `d`-path geometry and bumps `data-render-count`; suggested / select-all /
  clear presets; `Select all` trips the low-retention warning; `Clear` shows
  the explicit no-criterion message with all 1,114 retained; site
  denominators/retained counts carried on `customdata` (sum to 1,114 / 1,015);
  reload restores the suggested set; hover template exposes aggregate counts
  only (no `sub_id`); no failed / off-origin / CDN / kernel request and no
  WebSocket; narrow-viewport usability with a keyboard `Space` toggle.
- `interactive/e2e-book/chapter01.spec.ts`: **histogram specs kept byte-for-byte
  unchanged**; added a "Chapter 1 built page — embedded retention explorer"
  describe with three tests against the real built `book/_build/html` Chapter 1
  route under the simulated `/ml-neuro-tutorials/` subpath — iframe present,
  `configs/eda_retention.json` + `data/abide_retention.json` both HTTP 200,
  Plotly renders in-iframe, defaults are the suggested core set with 1,015
  retained, `Select all` reduces retained N / moves bar geometry / shows the
  warning, `Clear` shows the no-criterion message, and the **activity-frame**
  requests are all same-origin with no CDN / kernel / JupyterLite / Voici /
  `html-manager` / thebe hit, no failed widget request, and no WebSocket;
  browser refresh restores the suggested set; narrow-viewport usability.
- Page-level network after cleanup: the Chapter 1 page still pulls MathJax from
  `cdn.jsdelivr.net/npm/mathjax@3` and ships `sphinx-book-theme`'s
  `sphinx-thebe.js` (same-origin) whose inline config names
  `unpkg.com/thebe@0.8.2` (thebe is only fetched on a "live code" click, which
  the course does not surface). Both are pre-existing `sphinx-book-theme`
  behaviour, explicitly out of WP04 scope. `require.js`,
  `@jupyter-widgets/html-manager`, and the `lite/` app are **gone**. No Google
  Fonts request is made by this page.

### 8. Documentation and completion
- `interactive/README.md`: WP04 status; a full `eda-retention` piece-by-piece
  table; a "Why `SITE_ID` is in this artifact but participant identifiers never
  are" section; a **Default retention — regression reference** table (exact
  values below); the extended `--artifact` refresh workflow; a "Page-level CDN /
  theme dependencies (out of scope)" section recording exactly what remains and
  what WP04 removed; a preview URL for the retention explorer.
- Confirmed generated output (`book/_static/widgets/app/`, `book/_build/`),
  `node_modules`, Playwright artifacts, and `__pycache__` are git-ignored and
  absent from `git status`. Working tree clean after the implementation commit.
- Committed implementation as `WP04: add ABIDE missing-data retention activity`
  (`851b3f7`); committing this report separately as
  `WP04 report: document results`, then stopping. WP05 not started, not created.

## Files changed

Implementation commit `851b3f783613b427239cc795b98f1edf3290d607`
(21 files, +2380 / −550):

| Path | Purpose |
|---|---|
| `scripts/export_widget_data.py` | two-artifact registry; `build_retention_artifact` / `validate_retention_artifact`; narrow `SITE_ID` exception; `--artifact {histogram,retention,all}` selector; histogram path unchanged. |
| `tests/test_export_widget_data.py` | +26 stdlib `unittest` cases (retention build/validate/serialize + registry). 45 total, no network. |
| `book/_static/widgets/data/abide_retention.json` | **new** — committed data artifact (1,114 rows, `SITE_ID` + 13 vars, `null` for missing). |
| `book/_static/widgets/configs/eda_retention.json` | **new** — `eda-retention` activity config (grouped candidates, defaults, prompts). |
| `interactive/src/retention.ts` | **new** — pure complete-case retention (overall + per-site, first-appearance order). |
| `interactive/src/retention-data.ts` | **new** — component-owned Zod schema for the artifact (DOM/Plotly-free). |
| `interactive/src/components/retention.ts` | **new** — the `eda-retention` component (grouped checkboxes, presets, Plotly bar, state attrs, no-selection + low-retention cues). |
| `interactive/src/components/registry.ts` | register `retentionComponent`. |
| `interactive/src/config.ts` | add the `eda-retention` schema member + `checkSemantics()` cross-field checks. |
| `interactive/src/styles.css` | warn tokens/`.widget-warning`, buttons, checkbox-group grid. |
| `interactive/tests/retention.test.ts` | **new** — 16 retention-maths unit tests incl. pandas cross-check against the committed artifact. |
| `interactive/tests/retention-data.test.ts` | **new** — 10 data-schema unit tests (incl. the committed artifact). |
| `interactive/tests/config.test.ts` | +11 `eda-retention` config tests. |
| `interactive/e2e/retention.spec.ts` | **new** — standalone-app Playwright spec (× 2 base URLs). |
| `interactive/e2e-book/chapter01.spec.ts` | +3 built-Jupyter-Book retention tests; histogram tests unchanged. |
| `interactive/README.md` | retention activity + `SITE_ID` rationale + regression reference + `--artifact` workflow + page-CDN note. |
| `book/chapters/chapter_01/exercise_01.ipynb` | replace the `ipywidgets` retention interface + kernel note with a Markdown iframe (3→1 `nbformat` edit); drop dead `ipywidgets` import from the setup cell. |
| `book/chapters/chapter_01/exercise_01_widgets.ipynb` | **removed** — orphan experiment, never in `_toc.yml`. |
| `book/_config.yml` | remove the stale `jupyterlite_sphinx` extension + `jupyterlite_contents` config; keep Colab. |
| `requirements.txt` | drop `ipywidgets`, `jupyterlite-sphinx`, `jupyterlite-pyodide-kernel`, `voici`. |
| `.github/workflows/deploy.yml` | offline-check **both** ABIDE artifacts (`--check --artifact all`). |

Checkpoint commit `9818cc3` (pre-existing work, not authored by WP04):
`WPs/README.md` (process update), `WPs/WP04_MISSING_DATA_RETENTION.md` (WP brief).

Generated / not committed (verified absent from `git status`):
`book/_static/widgets/app/`, `book/_build/`, `interactive/node_modules/`,
`interactive/test-results/`, `**/__pycache__/`.

## Retention data artifact
- Source URL/hash: `https://raw.githubusercontent.com/neurohackademy/nh2020-curriculum/e4eed3c4daa7f40b0ba931182a8c7e5e691dba6b/tu-machine-learning-yarkoni/data/abide2_phenotypic.csv`
  — SHA-256 `537e541114884f63a2e736ba4d223a816dd013f701e56fb223ebe42e219e06f6`
  (561,572 bytes; identical pin as the histogram, verified with
  `--print-upstream-hash`). Source shape 1,114 rows × 348 columns
  (`encoding="latin-1"`, header whitespace stripped).
- Rows and fields: 1,114 aligned rows. `columns` = `SITE_ID` (strings) + 13
  candidate variables, **no substitutions** — all present in
  `book/config/eda_phenotype_columns.json` and the source. Per-variable
  available / missing: `DX_GROUP` 1114/0, `AGE_AT_SCAN` 1114/0, `SEX` 1114/0,
  `HANDEDNESS_CATEGORY` 1091/23, `FIQ` 1015/99, `VIQ` 799/315, `PIQ` 872/242,
  `ADOS_G_TOTAL` 347/767, `ADOS_2_TOTAL` 269/845, `SRS_TOTAL_RAW` 785/329,
  `SCQ_TOTAL` 293/821, `CURRENT_MED_STATUS` 991/123, `EYE_STATUS_AT_SCAN`
  1113/1. Categorical variables are the documented integer codes (`DX_GROUP`
  1/2, `SEX` 1/2, `HANDEDNESS_CATEGORY` 1/2/3, `CURRENT_MED_STATUS` 0/1,
  `EYE_STATUS_AT_SCAN` 0/1/2) — never imputed. Valid `0` (`CURRENT_MED_STATUS`,
  `EYE_STATUS_AT_SCAN`) is preserved, not nulled.
- Site grouping treatment: `SITE_ID` (19 acquisition sites, 0 missing) is
  exported as a plain string column plus a `site` metadata block
  (`field: "SITE_ID"`, `siteCount: 19`, `sites: [{label,total}, …]` in
  first-appearance order, totals summing to 1,114). It is used only as a
  grouping label; the widget hover shows site-level aggregates, never rows.
- Missing-value representation: JSON `null` for the 13 candidate columns.
  Integer-valued observations serialize as JSON integers, other finite values as
  JSON floats. `SITE_ID` has no `null`. `NaN`/`Infinity` rejected at build and
  serialize (`allow_nan=False` + explicit finite check).
- Participant-identifier check: `SITE_ID` is the **only** identifier-shaped name
  allowed, via an explicit allowlist argument in
  `build_retention_artifact` / `validate_retention_artifact`, and only in this
  artifact. `SUB_ID`, subject/participant IDs, names, emails, DOB and arbitrary
  `*_ID` fields are still refused by the shared token regex
  `(^|_)(ID|IDS|UID|GUID|MRN|SUB|SUBJECT|SUBID|PARTICIPANT|NAME|EMAIL|DOB)($|_)`
  (Python) and an equivalent regex in the client Zod schema. Unit tests
  (`test_rejects_sub_id_as_a_selected_variable`,
  `test_rejects_arbitrary_id_field`, `test_rejects_site_field_as_a_selected_variable`,
  `test_catches_identifier_column_other_than_site`) lock this down. The raw CSV
  is not committed; the artifact contains no diagnosis-linked identifier.
- Artifact size/hash/determinism: `book/_static/widgets/data/abide_retention.json`,
  **71,543 bytes**, SHA-256
  **`6b2965650311d122a3acdcc7fc362dcb6dca4408c1a8dbd952e04beb2eb73320`**.
  Deterministic (`sort_keys=True`, `separators=(",",":")`, single trailing
  newline, no timestamp/paths): identical hash across two consecutive
  `--refresh --artifact retention` runs; `--check` re-serialises and byte-
  compares. The histogram artifact
  (`93761624b15030ebe7fed8213773fe453630d693ab060b3e642086b3fbeb3e87`, 40,939
  bytes) was **not** modified by any retention refresh.

## Retention behavior
- Candidate/default variables: 13 candidates in four config groups
  (Demographics and diagnosis: `DX_GROUP`, `AGE_AT_SCAN`, `SEX`,
  `HANDEDNESS_CATEGORY`; Cognitive scores: `FIQ`, `VIQ`, `PIQ`; Diagnostic and
  behavioral measures: `ADOS_G_TOTAL`, `ADOS_2_TOTAL`, `SRS_TOTAL_RAW`,
  `SCQ_TOTAL`; Medication and scan conditions: `CURRENT_MED_STATUS`,
  `EYE_STATUS_AT_SCAN`). Default / suggested core set:
  **`DX_GROUP`, `AGE_AT_SCAN`, `SEX`, `FIQ`**.
- Complete-case rule: a participant is retained only when **every** selected
  variable is non-`null` for them. A valid `0` / `false` / documented category
  string is present, not missing.
- No-selection behavior: every row retained; `data-no-selection="true"`;
  `retention-message` displays "All participants are retained because no
  completeness criterion is currently applied."; the low-retention warning is
  suppressed.
- Overall and site outputs: overall retained N / total / percentage (1 dp) and
  excluded N in `retention-stats`; a Plotly bar of retained-percentage per site
  (first-appearance order) with hover `Retained <retained> of <siteTotal>
  (<pct>%)` and a dashed overall-retention reference line + annotation.
- Student-facing prompts: config `instructions` plus a rendered "Reflect" list —
  compare the suggested core set with a broader behavioral selection and see how
  much the sample shrinks / which sites vanish; identify sites disproportionately
  affected (cross-referencing the missingness heatmap); explain why complete-case
  filtering changes sample **composition**, not just size.

### Exact default-selection regression reference (independently cross-checked with pandas)

Selection `{DX_GROUP, AGE_AT_SCAN, SEX, FIQ}` on the committed artifact:

| Scope | Retained / Total | % |
|---|---|---|
| **Overall** | **1015 / 1114** | **91.1131 %** (99 excluded) |
| ABIDEII-BNI_1 | 58 / 58 | 100.00 % |
| ABIDEII-EMC_1 | 0 / 54 | 0.00 % (FIQ absent site-wide) |
| ABIDEII-ETH_1 | 37 / 37 | 100.00 % |
| ABIDEII-GU_1 | 104 / 106 | 98.11 % |
| ABIDEII-IP_1 | 25 / 56 | 44.64 % |
| ABIDEII-IU_1 | 40 / 40 | 100.00 % |
| ABIDEII-KKI_1 | 210 / 211 | 99.53 % |
| ABIDEII-KUL_3 | 28 / 28 | 100.00 % |
| ABIDEII-NYU_1 | 77 / 78 | 98.72 % |
| ABIDEII-NYU_2 | 27 / 27 | 100.00 % |
| ABIDEII-OHSU_1 | 93 / 93 | 100.00 % |
| ABIDEII-OILH_2 | 59 / 59 | 100.00 % |
| ABIDEII-SDSU_1 | 57 / 58 | 98.28 % |
| ABIDEII-SU_2 | 42 / 42 | 100.00 % |
| ABIDEII-TCD_1 | 42 / 42 | 100.00 % |
| ABIDEII-UCD_1 | 32 / 32 | 100.00 % |
| ABIDEII-UCLA_1 | 30 / 32 | 93.75 % |
| ABIDEII-U_MIA_1 | 27 / 28 | 96.43 % |
| ABIDEII-USM_1 | 27 / 33 | 81.82 % |

Other cross-checked references: `{SCQ_TOTAL, ADOS_2_TOTAL}` → 119 / 1114
(10.6822 %); `Select all` (13 vars) → 26 / 1114 (2.3339 %, trips the < 50 %
warning); no selection → 1114 / 1114 (100 %, no criterion applied).

## Legacy cleanup
- **Notebook interface**: the `ipywidgets` `SelectMultiple` /
  `interactive_output` retention cells and their `:::{note}` kernel warning are
  gone from `exercise_01.ipynb`, replaced by one Markdown + iframe cell. The
  setup cell's dead `import ipywidgets as widgets` /
  `from IPython.display import display, clear_output` / Colab custom-widget-
  manager block were removed (used nowhere else, repo-wide search).
- **Orphan notebook**: `book/chapters/chapter_01/exercise_01_widgets.ipynb`
  removed (`git rm`); it was never in `_toc.yml` and only ever ran with a live
  kernel.
- **Dependencies**: `ipywidgets`, `jupyterlite-sphinx`,
  `jupyterlite-pyodide-kernel`, `voici` removed from `requirements.txt` after a
  repo-wide search confirmed no `.py` / `.ipynb` / config still uses them.
- **`book/_config.yml`**: the `sphinx:` block (`extra_extensions:
  [jupyterlite_sphinx]`, `jupyterlite_contents`, `jupyterlite_bind_ipynb_suffix`)
  removed — WP01 established it referenced a non-existent file and produced an
  empty `lite/` app. `launch_buttons.colab_url` retained.
- **Widget state**: none stored in the notebook (`nb.metadata` had no `widgets`
  key), so nothing to strip.
- **Kept**: the Open-in-Colab launch button; the WP03 histogram iframe and its
  tests; all static Matplotlib/Seaborn figures and teaching prose; existing
  JupyterLite *package* installs are simply no longer referenced.
- **Build warnings**: 11 → 9. Removed: the `exercise_01_widgets.ipynb`
  "not included in any toctree" warnings. Remaining warnings are all pre-existing
  and unrelated (syllabus toctree title, `README.md` not in toctree, missing
  `logo.png`, cosmetic `IPKernelApp` TCP-encryption notice).

## Build and deployment integration
- `npm run build` (Vite, `base:"./"`) writes the app to the git-ignored
  `book/_static/widgets/app/`; in CI this runs before `jupyter-book build book`.
  Bundle: `index-*.js` 1,472,854 bytes raw (~493 kB gzip), CSS ~2.8 kB
  (+~12 kB JS / +~0.9 kB CSS vs WP03 for the retention code). Vite's 500 kB
  chunk warning persists (Plotly), as in WP02/WP03.
- Sphinx copies `book/_static/widgets/` through verbatim — verified in
  `book/_build/html/_static/widgets/{app,configs,data}/`, including
  `abide_retention.json` and `eda_retention.json`.
- The iframe `src`
  `../../_static/widgets/app/index.html?config=../configs/eda_retention.json`
  resolves from `chapters/chapter_01/exercise_01.html`; `config` →
  `_static/widgets/configs/eda_retention.json`, its `data` →
  `_static/widgets/data/abide_retention.json`. Confirmed by HTTP 200 assertions
  in the built-page e2e at the `/ml-neuro-tutorials/` subpath.
- `jupyter-book build book`: exit 0, "build succeeded, 9 warnings", no
  `book/_build/**/*.err.log`.
- `.github/workflows/deploy.yml`: unchanged pipeline except the artifact check is
  now `--check --artifact all` (both files). The new unit and e2e specs are
  picked up automatically by the existing `test:unit` / `playwright test` /
  `test:e2e:book` steps.

## Tests and verification
| Command/test | Result | Evidence or relevant output |
|---|---|---|
| `npm ci` (interactive) | PASS | 100 packages, clean install. |
| `npm run typecheck` | PASS | `tsc --noEmit` exit 0, no diagnostics (strict, `exactOptionalPropertyTypes`, `noUncheckedIndexedAccess`). |
| `npm run test:unit` | PASS | "Test Files 6 passed / Tests 100 passed" — `retention.test.ts` 16, `retention-data.test.ts` 10, `config.test.ts` 34, `histogram.test.ts` 14, `histogram-data.test.ts` 7, `urls.test.ts` 19. |
| `npm run build` | PASS | 19 modules; `index-*.js` 1,472.62 kB (gzip 492.68 kB), `index-*.css` 2.77 kB; Vite 500 kB chunk warning only. |
| `npm audit --omit=dev` | PASS | "found 0 vulnerabilities". |
| `npx playwright test` (standalone, `e2e/`) | PASS | "26 passed" — `retention.spec.ts` 10 (× site-root/subpath), `histogram.spec.ts` 8, `runtime.spec.ts` 8. Chromium. |
| `.venv/bin/python -m unittest discover -s tests -p 'test_export_widget_data.py'` | PASS | "Ran 45 tests … OK" (no network). |
| `.venv/bin/python scripts/export_widget_data.py --check` | PASS | both artifacts "valid and canonical"; retention sha256 `6b296565…`, histogram sha256 `93761624…`. |
| `.venv/bin/python scripts/export_widget_data.py --refresh --artifact retention` (×2) | PASS | downloaded 561,572 bytes, sha256 matches pin; wrote 71,543 bytes; identical artifact hash both runs; histogram file untouched (`git diff` empty). |
| `rm -rf book/_build && .venv/bin/jupyter-book build book` | PASS (exit 0) | "build succeeded, 9 warnings"; no `*.err.log`; widget assets present under `_build/html/_static/widgets/`. |
| `find book/_build -name '*.err.log'` | PASS | empty. |
| `npm run test:e2e:book` (built book, `e2e-book/`) | PASS | "6 passed" — 3 histogram (unchanged) + 3 retention: iframe under Chapter 1 route, config+data HTTP 200, Plotly renders, defaults 1015/1114, select-all reduces retained N + moves bars + shows warning, clear shows no-criterion message, activity requests all same-origin (no CDN/kernel/JupyterLite/Voici/html-manager/thebe), no WebSocket, refresh restores defaults, narrow viewport. |
| `nbformat.validate` after the notebook edit | PASS | 57 cells, 57 unique ids; histogram iframe cell + all other prose intact; no `ipywidgets` / `widgets.` reference remains. |
| `git status --porcelain` after implementation commit | PASS (clean) | empty; `book/_build/`, `book/_static/widgets/app/`, `node_modules`, `__pycache__` all absent. |
| Independent pandas cross-check of default + behavioral selections | PASS | values in the regression table above computed directly with `pandas` on the pinned CSV and asserted by `retention.test.ts`. |

Environment: macOS 15.7 (Darwin 24.6.0), Python 3.12.7 (`.venv`), pandas 3.0.5,
Node v24.4.1 / npm 11.4.2 (CI pins Node 22), Jupyter Book 1.0.4.post1, Playwright
Chromium 140.

## Acceptance criteria
| Criterion | PASS/FAIL/NOT TESTED | Evidence |
|---|---|---|
| Mandatory WP04 checkpoint commit and annotated tag exist | PASS | `9818cc3` "checkpoint: before WP04" / annotated `wp04-start` (`52333b6`). |
| Retention artifact deterministic, offline-validated, contains `SITE_ID` but no participant identifier | PASS | 71,543 bytes, sha256 `6b296565…`; `--check` OK; `SITE_ID` present, `SUB_ID`/`*_ID` rejected; raw CSV not committed. |
| Exact `SITE_ID` exception is narrow and tested; `SUB_ID` and arbitrary IDs remain rejected | PASS | explicit allowlist arg in build/validate; 4 dedicated unit tests + client Zod regex. |
| Complete-case calculations pure, tested, independently cross-checked | PASS | `src/retention.ts` (no DOM/Plotly), 16 unit tests incl. pandas cross-check (1015 / 119 / 1114). |
| Default selection is `DX_GROUP`, `AGE_AT_SCAN`, `SEX`, `FIQ` | PASS | `eda_retention.json` `defaultVariables`; asserted in standalone + built-page e2e. |
| Checkboxes and all three preset controls update summaries and actual Plotly geometry | PASS | `retention.spec.ts` "preset controls" + "checkbox-driven redraw"; `data-render-count` increments, bar `d`-paths change. |
| No-selection and low-retention states clear and pedagogically accurate | PASS | explicit "no completeness criterion" message; `< 50 %` warning worded as "a prompt to look closely, not a universal cutoff". |
| Retention iframe works and changes visibly on the final built Chapter 1 page | PASS | `e2e-book/chapter01.spec.ts` retention describe, `/ml-neuro-tutorials/` subpath. |
| Histogram activity and tests remain passing | PASS | histogram unit + `e2e/histogram.spec.ts` (8) + `e2e-book` histogram (3) unchanged and green. |
| Obsolete `ipywidgets`/JupyterLite/Voici files, config, dependencies removed only after replacement tests pass; Colab remains | PASS | removal committed in the same commit as the passing replacement; `launch_buttons.colab_url` intact. |
| CI validates both artifacts and runs the full frontend/book test path before deployment | PASS | `deploy.yml` `--check --artifact all` + unchanged typecheck/unit/audit/build/Playwright/book/err-guard/book-Playwright before `peaceiris/actions-gh-pages`. |
| Activity requests same-origin and kernel/CDN-free | PASS (for the activity) | standalone + built-page e2e assert 0 off-origin/CDN/kernel/WebSocket for activity-frame requests. Page-level MathJax/thebe pre-existing, out of scope. |
| Typecheck, all unit tests, prod dep audit, build, Jupyter Book, error guard, standalone/built-book Playwright pass | PASS | Tests table. |
| Documentation and WP04 report complete | PASS | `interactive/README.md` updated; this report. |
| Working tree clean after separate implementation and report commits | PASS (impl verified; report commit follows) | `git status --porcelain` empty after `851b3f7`. |
| No WP05 file created | PASS | no `WP05*` file; no retention-follow-up work started. |

## Deviations from instructions
- **Cleaned the notebook setup cell (cell id `4ddc8b70-…`).** Removing the
  retention widget and the `ipywidgets` dependency left `import ipywidgets as
  widgets`, `from IPython.display import display, clear_output`, and the
  `google.colab … enable_custom_widget_manager()` block dead (repo-wide search:
  used only in the removed cells). They were removed so the notebook still
  executes after `ipywidgets` is dropped from `requirements.txt`. This is code
  cleanup entailed by the WP, not a change to teaching prose or analysis
  results. `execution_count` on that cell reset to `null` because its source
  changed (re-executed on the next cached build). One-line revert if the
  reviewer wants the import kept.
- **Removed the `jupyterlite_sphinx` config from `book/_config.yml` and the
  four packages from `requirements.txt`.** `CLAUDE_INTERACTIVE_WIDGETS.md` Rule 8
  says JupyterLite "may remain"; WP04 §6.4 authorizes removal "only if
  repository-wide search confirms they are no longer used". WP01 established the
  config pointed at a non-existent file (`chapters/chapter_01/eda_widgets.ipynb`)
  and shipped an empty `lite/` app, and repo-wide search found no other use, so I
  removed it. This drops the `lite/` build from the site. Reversible by
  restoring the `sphinx:` block and the four pins.
- **Reused the removed kernel-note cell's id (`999ad285-…`) for the new iframe
  Markdown cell** (a 3-cells-into-1 collapse), matching the WP03 precedent of
  reusing an id when swapping a cell's type. The two removed `ipywidgets`
  code-cell ids (`8e512021-…`, `c8a80b86-…`) are retired.
- **The artifact Zod schema lives in `interactive/src/retention-data.ts`,
  imported by `components/retention.ts`**, rather than literally inside the
  component file — same rationale and same deviation as WP03's
  `histogram-data.ts` (keeps it Plotly-free and unit-testable). It is still
  owned and used only by the retention component.
- **Added an `--artifact {histogram,retention,all}` selector** to
  `export_widget_data.py` — explicitly invited by WP04 §2.7 ("Extend the CLI
  cleanly — e.g. an explicit artifact selector"). Bare `--check` / `--refresh`
  default to `all`, so the WP03 command strings are unchanged in effect.
- **Fixed a stray NUL byte** accidentally introduced into
  `interactive/src/retention-data.ts` during authoring (an order-comparison
  `.join(" ")` separator became `.join("")`); caught before commit by
  git's binary-file detection. Functionally identical; typecheck + all
  retention-data unit tests pass.
- **Node 24 locally**; `package.json` `engines` is `>=20.19.0 <25` and CI is
  pinned to Node 22 as required.
- **`npm audit` (full tree) still reports the WP02/WP03 dev-toolchain
  advisories** (esbuild/vite dev server, `@vitest/mocker`/vitest). None are
  reachable from `vitest run` / `vite build` / `playwright test` or the shipped
  bundle. `npm audit --omit=dev` is clean. Carried forward per WP04's explicit
  "Do not perform the separate Vite/Vitest major-version security upgrade in
  this WP".

## Problems and unresolved risks
- **The surrounding Chapter 1 page is still not CDN-free.** It requests MathJax
  from `cdn.jsdelivr.net/npm/mathjax@3` and ships `sphinx-book-theme`'s
  `sphinx-thebe.js` whose inline config references `unpkg.com/thebe@0.8.2`
  (thebe is fetched only on a "live code" click, which the course does not
  expose). Both are pre-existing `sphinx-book-theme` behaviour and explicitly
  out of WP04 scope ("Page-wide self-hosting of MathJax/Google Fonts is out of
  scope"). The **activity iframe itself** makes zero CDN/kernel/off-origin
  requests (asserted). WP04 cleanup did remove `require.js`,
  `@jupyter-widgets/html-manager`, and the `lite/` app from the page.
- **`npm audit` (full tree) dev-only advisories** persist (esbuild/vite/vitest).
  Deferred to an isolated toolchain-bump WP, as instructed.
- **Bundle size** 1.47 MB raw / 493 kB gzip (Plotly cartesian dist), above
  Vite's 500 kB warning. Acceptable for a lazy-loaded iframe; code-splitting
  Plotly behind a dynamic `import()` remains an option.
- **e2e depends on Plotly's internal SVG structure** (`g.trace.bars g.point
  path`). A future Plotly major could rename these; the independent
  `data-render-count` / `data-retained-n` / `data-bar-count` attribute checks
  would still catch a redraw.
- **The pinned source is a third-party GitHub mirror.** If that commit is ever
  removed, `--refresh` breaks, but `--check` and the committed artifacts keep
  the site building. Documented in `interactive/README.md`.
- **`jupyter-book build book` still exits 0 on notebook execution errors.**
  Mitigated in CI by the WP03 `*.err.log` guard; local builds still need that
  check run by hand.
- **`jupyterlab` remains in `requirements.txt`.** It is not needed for
  `jupyter-book build` but is harmless and was outside the WP's removal list, so
  it was left in place.

## Git commits created
- Checkpoint commit: `9818cc3956045912298516542d73b87e04cc68f3` ("checkpoint: before WP04")
- Checkpoint tag: `wp04-start` (annotated, tag object `52333b610bde3fc2a6c7b18097c4fe517d6706ff`, points at `9818cc3`)
- Implementation commit: `851b3f783613b427239cc795b98f1edf3290d607` ("WP04: add ABIDE missing-data retention activity")
- The report commit ("WP04 report: document results") hash is printed in the
  terminal summary because the report cannot contain its own future hash.

## Recommended scope for WP05
Recommendations only. Do not create or begin WP05.
- **Page-level CDN removal** (Rule 8): self-host MathJax and either self-host or
  disable the `sphinx-thebe` launch-button config so the whole published
  Chapter 1 page — not only the iframes — is CDN-free. Now that `ipywidgets` /
  JupyterLite are gone this is a smaller, well-scoped change.
- **Toolchain security bump** (Vite ≥ 6 / Vitest ≥ 3 or then-current) as an
  isolated WP with a full typecheck/unit/build/e2e re-run to clear the dev-only
  `npm audit` advisories.
- **Plotly bundle**: code-split behind a dynamic `import()` or evaluate a
  smaller distribution once the final trace-type set (bar) is fixed for both
  activities.
- **Shared e2e server helper**: `e2e/serve-static.mjs` and
  `e2e-book/serve-book.mjs` are near-duplicates; a shared module would reduce
  drift.
- **Optional**: dynamic iframe height (both activities use a fixed `height`);
  decide whether `jupyterlab` should also leave `requirements.txt`.
- **Consider** a third activity or consolidating the Chapter 1 EDA notebook's
  remaining kernel-only demos (median imputation, category fill) if they should
  also work on the static site.

## Instructions for reviewer
Paste this entire report into the ChatGPT conversation that produced WP04.
