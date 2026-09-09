# WP03 implementation report

## Outcome
Status: SUCCESS

The first production activity, `eda-histogram`, is implemented on the WP02
browser-native runtime and embedded in the Chapter 1 EDA notebook. A new
`scripts/export_widget_data.py` deterministically exports eight identifier-free
numeric variables from the ABIDE-II phenotypic CSV — pinned by URL **and**
SHA-256 — into a committed 40,939-byte artifact
(`book/_static/widgets/data/abide_histogram.json`, 1,114 rows, missing values as
JSON `null`), with `--refresh` (network) and `--check` (offline) modes and 19
standard-library `unittest` tests that need no network. Binning is a pure,
DOM/Plotly-free module (`interactive/src/histogram.ts`) with 14 unit tests
covering ordinary/boundary/negative/decimal values, missingness,
requested-bin validation, all-missing input, constant input and count
conservation; the component plots its output as a Plotly **bar** trace so the
number of bins and the counts are exactly the tested values. The obsolete
CDN-Plotly histogram experiment (and its "requires a kernel" note) were replaced
in `exercise_01.ipynb` with a Markdown iframe via a two-cell `nbformat` edit; the
retention `ipywidgets` cells were left untouched. The deployment workflow now
builds and tests the frontend (Node 22, `npm ci`, typecheck, unit tests,
`npm audit --omit=dev`, Vite build, offline artifact check, Playwright against
the standalone app **and** the built Chapter 1 page) before `jupyter-book build`,
and fails CI on any notebook `*.err.log`. Every interactive claim below is backed
by a Playwright test against the final built `book/_build/html` Chapter 1 page,
served beneath a simulated `/ml-neuro-tutorials/` subpath. All commands in WP03
§8 pass. `npm audit --omit=dev` reports 0 vulnerabilities; full-tree `npm audit`
dev-only advisories are carried forward per WP02.

## Git safety checkpoint
- Branch: `feature/reusable-interactive-widgets`
- Starting HEAD: `f6c4b0fc18fb8cc23d2f7f1a5d5ac20a4e750c5c` ("WP02 report: document results")
- Checkpoint commit: `dfb4076631a37126c74488af52453d632af8935d` ("checkpoint: before WP03")
- Checkpoint tag: `wp03-start` (annotated, `aa5f6ca49410a36c8cb60243f144b7ba6b3de341`, points at `dfb4076`)
- Retraction guidance: identify the checkpoint only; do not execute a reset or revert. To undo WP03, `git revert` the implementation commit `4b4ab42` and this report commit, or reset to `dfb4076` / tag `wp03-start` at your discretion. Leave `wp01-start` / `wp02-start` intact.

The checkpoint captured the two pre-existing legitimate working-tree changes only:
the WP-process update to `WPs/README.md` and the new (untracked) WP brief
`WPs/WP03_ABIDE_HISTOGRAM.md`. No build output, caches, `.DS_Store`, credentials,
or private data were present or committed.

## Work completed

### 1. Mandatory checkpoint and baseline
- Read `CLAUDE_INTERACTIVE_WIDGETS.md`, `WPs/README.md`, `WPs/WP03_ABIDE_HISTOGRAM.md`, and `WPs/reports/WP02_REPORT.md` in full.
- Confirmed branch `feature/reusable-interactive-widgets`.
- Inspected `git status --short` / `git diff` / the untracked WP brief, then created `checkpoint: before WP03` (`dfb4076`) and annotated tag `wp03-start`.
- Ran the WP02 clean baseline from `interactive/` before any WP03 change: `npm ci` (OK), `npm run typecheck` (0 errors), `npm run test:unit` (32/32), `npm run build` (OK, Vite 500 kB chunk-size warning only), `npx playwright test` (8/8), `npm audit --omit=dev` (0 vulnerabilities). The WP02 baseline still passes; no diagnosis was needed.

### 2. Deterministic ABIDE histogram data export
- Added `scripts/export_widget_data.py`:
  - Pins `SOURCE_URL` (NeuroHackademy 2020 mirror, commit `e4eed3c4…`) and `SOURCE_SHA256 = 537e5411…` (561,572 bytes). `--refresh` downloads, verifies the digest, and **fails loudly (exit 2)** without writing if the upstream bytes differ.
  - Modes: `--refresh` (network export), `--check` (offline validation + canonical-form guard), and a helper `--print-upstream-hash` (network, prints only).
  - Reads the **local** `book/config/eda_phenotype_columns.json` as the allowed-column authority (never fetched).
  - Exports one array per variable, aligned to source row order, row count preserved (1,114). Missing → JSON `null`; integer-valued observations → JSON integers; other finite values → JSON floats; `NaN`/`Infinity` rejected (`json.dumps(..., allow_nan=False)` plus an explicit finite check).
  - Artifact carries `schemaVersion`, `activity`, `source` (url, sha256, sourceRows, sourceColumns), `rowCount`, per-variable metadata (`name`, `availableN`, `missingN`), and `columns`. No generation timestamp.
  - `validate_artifact()` checks: schemaVersion, positive integer rowCount, every column key in the curated authority, no identifier-like key (regex on `ID/SUB/SITE/UID/GUID/MRN/PARTICIPANT/NAME/…` tokens), array lengths == rowCount, every value number-or-null and finite, and metadata `availableN` == actual non-null count with `availableN + missingN == rowCount`.
  - Deterministic serialization: `sort_keys=True`, compact separators, single trailing newline, no machine paths. A no-op `--refresh` produces no diff (verified by hashing three consecutive refreshes) and `--check` re-serializes and byte-compares the committed file.
- Committed `book/_static/widgets/data/abide_histogram.json` (40,939 bytes). The full source CSV was **not** committed.
- Added `tests/test_export_widget_data.py` — 19 stdlib `unittest` tests on tiny in-memory CSV fixtures, no network: helper mapping, identifier detection, header stripping, NaN/inf handling, happy-path build, rejection of a non-allowed / identifier-like / missing-in-source variable, all `validate_artifact` failure branches, deterministic sorted serialization with trailing newline, NaN-on-serialize rejection, and a build→serialize→validate round trip.

### 3. Histogram configuration and schema
- Added `book/_static/widgets/configs/eda_histogram.json`: title, `instructions`, `data`, eight `{name,label}` variables, `defaultVariable: "AGE_AT_SCAN"`, `bins: {min:5, max:60, step:1, default:25}`, `xAxisLabel`, `yAxisLabel`, three `reflectionPrompts`.
- Extended the versioned discriminated union in `interactive/src/config.ts` with a `.strict()` `eda-histogram` member. Cross-field checks the union cannot express are done in `checkSemantics()` after the Zod parse: no duplicate variable names, `defaultVariable` ∈ variables, `bins.min ≤ bins.max`, `bins.default` ∈ `[min,max]`, and `bins.default` reachable from `min` in whole `step`s. 10 new config unit tests, including one that loads and validates the shipped `eda_histogram.json`.

### 4. Pure histogram calculation
- Added `interactive/src/histogram.ts#computeHistogram(observations, requestedBins)` — no DOM, no Plotly, no fetch.
  - Throws `RangeError` if `requestedBins` is not a positive integer; `TypeError` if a non-null observation is not finite.
  - Nulls counted as `missingN`; finite values as `availableN`.
  - `kind: "empty"` (availableN 0): no bins, `min`/`max` null.
  - `kind: "constant"` (min == max): exactly one unit-wide bin `[v-0.5, v+0.5]` holding every observation — never divides by zero.
  - `kind: "normal"`: exactly `requestedBins` equal-width bins over `[min,max]`; top edge set to `max` exactly; `Math.floor((v-min)/width)` clamped so the maximum lands in the final bin.
  - Returns `binEdges`, `binCenters`, `binLabels` (`"[a, b)"`, last `"[a, b]"`), `counts` (Σ == availableN), `availableN`, `missingN`, `min`, `max`, `kind`.
- 14 unit tests cover requested bins, boundary/negative/decimal values, missingness, count conservation across bin choices, requested-bin and non-finite-input validation, empty/all-missing, and constant input.
- The component plots this via a Plotly `bar` trace (per-bin `width` array, `bargap: 0`), not a histogram trace.

### 5. Production histogram component
- Added `interactive/src/histogram-data.ts` — the component-owned Zod schema for the artifact (kept DOM/Plotly-free so it is unit-testable): `schemaVersion` literal, positive `rowCount`, `source`, per-variable metadata, `columns` as `Record<string, (number|null)[]>`, `superRefine` cross-checking every column length against `rowCount` and every `availableN` against the data. 7 unit tests, including validation of the committed `abide_histogram.json` (rowCount 1114, the eight expected columns).
- Added `interactive/src/components/histogram.ts` and registered it in `registry.ts`:
  - Validates the artifact through `parseAbideHistogramData`; a data file missing a configured column throws a readable error.
  - Explicitly labelled `<select>` (`data-testid="histogram-variable"`) and range `<input>` (`data-testid="histogram-bins"`) with a visible `<output>` (`data-testid="histogram-bins-value"`).
  - Shows `Available N: … · Missing N: …` (`data-testid="histogram-stats"`).
  - `Plotly.react()` full redraw on `change` of either control; the bin `<output>` also tracks `input` live.
  - Machine-testable state on the plot div: `data-active-variable`, `data-active-bins`, `data-bar-count`, `data-render-count`, `data-kind`.
  - On-page instructions + a "Reflect" list from `reflectionPrompts`.
  - Empty/all-missing → `Plotly.purge` + an explicit "No observations are available for …" message.
  - Native form controls (keyboard-accessible), responsive Plotly layout, transparent paper/plot background with light/dark-aware axis/grid/bar colours via `prefers-color-scheme`.
  - Hover template exposes a bin range and a count only — no participant-level text.

### 6. Notebook integration
- `book/chapters/chapter_01/exercise_01.ipynb` edited with `nbformat` only (script located the cells by content: the `:::{note}` "executable Python kernel" markdown cell and the `code` cell containing `go.Histogram` + `include_plotlyjs="cdn"`).
  - Deleted the kernel-only note (obsolete: the activity needs no kernel).
  - Replaced the CDN-Plotly code cell with a Markdown cell (same id `23475ca3-…`, `deletable/editable/slideshow` metadata preserved) holding a one-line intro and an `<iframe>` with `title`, `loading="lazy"`, `width="100%"`, `height="680"`, `style="width:100%;border:none;"` and `src="../../_static/widgets/app/index.html?config=../configs/eda_histogram.json"`.
  - Diff is a single hunk confined to those two cells (11 insertions / 164 deletions — the deletions are the removed Plotly source and its stored HTML output). Notebook now 59 cells, all ids unique, `nbformat.validate` OK. Retention widget cells 36/37 intact. No other Plotly/CDN reference remains in the notebook.
- `requirements.txt`: removed `plotly` (now exclusively the obsolete histogram/CDN dependency; no remaining notebook imports it — see Deviations).

### 7. GitHub Actions and build guard
- `.github/workflows/deploy.yml` — same provider (`peaceiris/actions-gh-pages@v4`), trigger (`push: main`) and `publish_dir`. Added, before `jupyter-book build book`:
  1. `actions/setup-node@v4`, Node 22, `cache: npm`, `cache-dependency-path: interactive/package-lock.json`.
  2. `npm ci` in `interactive/`.
  3. `npm run typecheck` + `npm run test:unit`.
  4. `npm audit --omit=dev` (fails on any production advisory).
  5. `npm run build` → `book/_static/widgets/app/` exists before Sphinx copies `_static`.
  6. `python scripts/export_widget_data.py --check` (offline).
  7. `npx playwright install --with-deps chromium`, then `npx playwright test` (standalone app).
  After the book build: a `*.err.log` guard (`shopt -s globstar`; prints and `exit 1` if any report exists) and `npm run test:e2e:book` (Playwright against the built Chapter 1 page). Existing `pip install -r requirements.txt` was reused, not duplicated.

### 8. End-to-end verification
- `interactive/e2e/histogram.spec.ts` (standalone app, run at site root and `/ml-neuro-tutorials/`): defaults from the config, bars rendered, variable change updates `data-active-variable` + N/missing + bar geometry, bin change updates `data-active-bins` + `data-bar-count` + the real number of `g.point` bars, hover template is range+count only, reload restores defaults, narrow-viewport usability, and no off-origin / CDN / kernel / failed request and no WebSocket.
- `interactive/e2e-book/chapter01.spec.ts` (built `book/_build/html`, subpath route): the iframe exists under the real Chapter 1 route; config and data both return HTTP 200; Plotly renders inside the iframe; changing the variable changes active-variable/N/geometry; changing bins changes active-bins and the bar count (50, then 10); browser refresh restores defaults; the **activity's own** requests (matched by requesting-frame URL) are all same-origin with no CDN/kernel/JupyterLite/Voici hit, no failed widget request, and no WebSocket; usable at a 390 px viewport.
- Full WP03 §8 command block run locally — see Tests table.

### 9. Documentation and completion
- `interactive/README.md`: WP03 status; `eda-histogram` piece-by-piece table; authoring workflow; **intentional-only** data-refresh procedure (`--check` / `--print-upstream-hash` / `--refresh`, and how to adopt a genuine upstream change by editing `SOURCE_SHA256` in the same commit); `serve:book` / `test:e2e:book`; and a local "preview the real embedded page over HTTP" recipe.
- Confirmed generated output (`book/_static/widgets/app/`, `book/_build/`), `node_modules`, Playwright artifacts, `__pycache__` and caches are git-ignored and absent from `git status`. Added `__pycache__/` + `*.pyc` to `.gitignore`.
- Committed implementation as `WP03: add production ABIDE histogram activity` (`4b4ab42`); committing this report separately as `WP03 report: document results`, then stopping. WP04 not started.

## Files changed

Implementation commit `4b4ab42a65e70b1437dc72486cee0c72559e8161` (24 files, +2086 / −184):

| Path | Purpose |
|---|---|
| `scripts/export_widget_data.py` | **new** — deterministic ABIDE export/validate (`--refresh` / `--check` / `--print-upstream-hash`). |
| `tests/test_export_widget_data.py` | **new** — 19 stdlib `unittest` tests, no network. |
| `book/_static/widgets/data/abide_histogram.json` | **new** — committed data artifact (1114 rows, 8 vars, `null` for missing). |
| `book/_static/widgets/configs/eda_histogram.json` | **new** — `eda-histogram` activity config. |
| `interactive/src/histogram.ts` | **new** — pure equal-width binning + edge cases. |
| `interactive/src/histogram-data.ts` | **new** — component-owned Zod schema for the artifact (DOM/Plotly-free). |
| `interactive/src/components/histogram.ts` | **new** — the `eda-histogram` component (selector, bin slider, Plotly bar trace, state attrs). |
| `interactive/src/components/registry.ts` | register `histogramComponent`. |
| `interactive/src/config.ts` | add the `eda-histogram` schema member + `checkSemantics()` default/range validation. |
| `interactive/src/styles.css` | styles for instructions, control groups, range input, stats, empty message, prompts. |
| `interactive/tests/histogram.test.ts` | **new** — 14 binning unit tests. |
| `interactive/tests/histogram-data.test.ts` | **new** — 7 data-schema unit tests (incl. the committed artifact). |
| `interactive/tests/config.test.ts` | +10 `eda-histogram` config tests. |
| `interactive/e2e/histogram.spec.ts` | **new** — standalone-app Playwright spec (× 2 base URLs). |
| `interactive/e2e-book/chapter01.spec.ts` | **new** — built-Jupyter-Book Playwright spec. |
| `interactive/e2e-book/serve-book.mjs` | **new** — dependency-free static server for `book/_build/html` (root + subpath). |
| `interactive/playwright.book.config.ts` | **new** — Playwright config for the built-book suite (port 4174). |
| `interactive/package.json` | add `serve:book`, `test:e2e:book`. |
| `interactive/tsconfig.json` | include `e2e-book` + `playwright.book.config.ts`. |
| `interactive/README.md` | histogram activity + data-refresh + book-preview docs. |
| `book/chapters/chapter_01/exercise_01.ipynb` | replace the obsolete CDN-Plotly histogram experiment + kernel note with a Markdown iframe (2-cell `nbformat` edit). |
| `.github/workflows/deploy.yml` | frontend build/test/audit + built-page e2e + `*.err.log` guard before deploy. |
| `requirements.txt` | drop now-unused `plotly`. |
| `.gitignore` | add `__pycache__/`, `*.pyc`. |

Checkpoint commit `dfb4076` (pre-existing work, not authored by WP03): `WPs/README.md` (process update), `WPs/WP03_ABIDE_HISTOGRAM.md` (WP brief).

Generated / not committed (verified absent from `git status`): `book/_static/widgets/app/`, `book/_build/`, `interactive/node_modules/`, `interactive/test-results/`.

## ABIDE data artifact
- Source URL and pinned source hash: `https://raw.githubusercontent.com/neurohackademy/nh2020-curriculum/e4eed3c4daa7f40b0ba931182a8c7e5e691dba6b/tu-machine-learning-yarkoni/data/abide2_phenotypic.csv` — SHA-256 `537e541114884f63a2e736ba4d223a816dd013f701e56fb223ebe42e219e06f6` (561,572 bytes). Digest confirmed stable across repeated downloads (curl ×3 + urllib).
- Source rows/columns: 1,114 rows × 348 columns (after header whitespace strip, `encoding="latin-1"`, matching the notebook's original read).
- Exported rows/variables: 1,114 rows × 8 variables. Row count and order preserved from the source.
- Exported fields (all present in `book/config/eda_phenotype_columns.json`; **no substitutions**): `AGE_AT_SCAN` (availableN 1114 / missingN 0), `FIQ` (1015 / 99), `VIQ` (799 / 315), `PIQ` (872 / 242), `ADOS_G_TOTAL` (347 / 767), `ADOS_2_TOTAL` (269 / 845), `SRS_TOTAL_RAW` (785 / 329), `SCQ_TOTAL` (293 / 821).
- Missing-value representation: JSON `null`. Integer-valued observations are JSON integers, other finite values JSON floats. `NaN`/`Infinity` are rejected at build and serialize time (`allow_nan=False` + explicit finite check).
- Identifier/privacy check: `SUB_ID`, `SITE_ID` and every other identifier-like name are refused by a token regex (`(^|_)(ID|IDS|UID|GUID|MRN|SUB|SUBJECT|SUBID|PARTICIPANT|NAME|EMAIL|DOB)($|_)`); none of the eight exported names match. The artifact contains only the eight numeric arrays plus provenance/metadata — no per-participant identifier, no site, no diagnosis. The raw CSV is not committed.
- Artifact size and deterministic hash: `book/_static/widgets/data/abide_histogram.json`, **40,939 bytes**, SHA-256 **`93761624b15030ebe7fed8213773fe453630d693ab060b3e642086b3fbeb3e87`**. Deterministic: `sort_keys=True`, `separators=(",",":")`, single trailing newline, no timestamp/paths. Verified byte-identical across three consecutive `--refresh` runs and by the `--check` re-serialization guard.

## Histogram behavior
- Variables/default: eight variables (labels in the config); default `AGE_AT_SCAN`.
- Bin range/default: range slider `min 5`, `max 60`, `step 1`, default `25`. The default and the `defaultVariable` are validated against their allowed set/range at config-load time; an out-of-range default produces a visible error panel and no render.
- Empty and constant-variable behavior: **empty / all-missing** → `kind:"empty"`, no bins, `Plotly.purge`, `data-bar-count="0"`, and an explicit "No observations are available for &lt;label&gt;." message (none of the eight shipped variables is all-missing). **Constant** (`min == max`) → `kind:"constant"`, exactly one unit-wide bin `[v−0.5, v+0.5]` containing every observation; no division by zero. Both are unit-tested.
- Student-facing text: config `instructions` ("predict what the change will do before you move it: fewer bins hide structure, more bins turn random noise into apparent peaks"), the retained notebook Markdown ("Before changing the controls, predict: …"), and a rendered "Reflect" list of three prompts (predict-then-move; compare age vs IQ vs questionnaire; relate available N to missingness).

## Build and deployment integration
- `npm run build` (Vite, `base:"./"`) writes the app to the git-ignored `book/_static/widgets/app/`; in CI this runs before `jupyter-book build book`.
- Sphinx copies `book/_static/widgets/` through verbatim — verified in `book/_build/html/_static/widgets/{app,configs,data}/`, including `abide_histogram.json` and `eda_histogram.json`.
- The iframe `src` `../../_static/widgets/app/index.html?config=../configs/eda_histogram.json` resolves correctly from `chapters/chapter_01/exercise_01.html`; `config` → `_static/widgets/configs/eda_histogram.json`, its `data` → `_static/widgets/data/abide_histogram.json`. Confirmed by HTTP 200 assertions in the built-page e2e at the `/ml-neuro-tutorials/` subpath.
- `jupyter-book build book`: exit 0, "build succeeded, 11 warnings" (same count as the WP02 baseline; the three distinct warnings — `syllabus` toctree title, `logo.png` missing, and `README.md` / `exercise_01_widgets.ipynb` "not in any toctree" — are all pre-existing and unrelated to WP03). No `book/_build/**/ *.err.log` produced.
- `.github/workflows/deploy.yml`: frontend steps + `--check` + standalone Playwright before the book build; `*.err.log` guard + built-page Playwright after it; deploy step unchanged.
- Bundle: `book/_static/widgets/app/assets/index-*.js` 1,460,844 bytes raw (~489 kB gzip), CSS ~1.9 kB. +8.5 kB JS vs WP02 for the histogram code. Vite's 500 kB chunk warning persists (Plotly), as in WP02.

## Tests and verification
| Command/test | Result | Evidence or relevant output |
|---|---|---|
| `npm ci` / `npm run typecheck` (baseline + final) | PASS | `tsc --noEmit` exit 0, no diagnostics. |
| `npm run test:unit` | PASS | `tests/histogram.test.ts` 14, `tests/config.test.ts` 24, `tests/histogram-data.test.ts` 7, `tests/urls.test.ts` 19 — "Test Files 4 passed / Tests 64 passed (64)". |
| `npm run build` | PASS | 16 modules transformed; `index-*.js` 1,460.61 kB (gzip 489.49 kB), `index-*.css` 1.90 kB; Vite 500 kB chunk warning only. |
| `npm audit --omit=dev` | PASS | "found 0 vulnerabilities" (exit 0). |
| `npx playwright test` (standalone, `e2e/`) | PASS | "16 passed" — `histogram.spec.ts` (8: × site-root/subpath) + `runtime.spec.ts` (8), Chromium. |
| `.venv/bin/python -m unittest discover -s tests -p 'test_export_widget_data.py'` | PASS | "Ran 19 tests … OK". |
| `.venv/bin/python scripts/export_widget_data.py --check` | PASS | "OK: … is valid and canonical."; artifact sha256 `93761624…`; per-variable availableN/missingN summary. |
| `.venv/bin/python scripts/export_widget_data.py --refresh` (×3, determinism) | PASS | Downloaded 561,572 bytes, sha256 matches pin; wrote 40,939 bytes; identical artifact hash all three runs. |
| `rm -rf book/_build && .venv/bin/jupyter-book build book` | PASS (exit 0) | "build succeeded, 11 warnings"; no `*.err.log`; widget assets present under `_build/html/_static/widgets/`. |
| `*.err.log` guard (workflow step, simulated locally) | PASS | `find book/_build -name '*.err.log'` → empty. |
| `npm run test:e2e:book` (built `book/_build/html`, `e2e-book/`) | PASS | "3 passed" — iframe under Chapter 1 route, config+data HTTP 200, Plotly renders in-iframe, variable + bin controls change geometry/bar count, refresh restores defaults, activity requests all same-origin, no WebSocket, narrow viewport. |
| `nbformat.validate` after the notebook edit | PASS | 59 cells, 59 unique ids; diff one hunk confined to the two target cells; retention cells 36/37 intact. |
| `git status --porcelain` after implementation commit | PASS (clean) | empty; `book/_build/`, `book/_static/widgets/app/`, `interactive/node_modules/`, `__pycache__` all absent. |

Environment: macOS 15.7 (Darwin 24.6.0), Python 3.12.7 (`.venv`), Node v24.4.1 / npm 11.4.2 (CI pins Node 22), Jupyter Book 1.0.4.post1, Playwright Chromium 140.

## Acceptance criteria
| Criterion | PASS/FAIL/NOT TESTED | Evidence |
|---|---|---|
| Mandatory WP03 checkpoint commit and annotated tag exist | PASS | `dfb4076` "checkpoint: before WP03" / annotated `wp03-start`. |
| Committed ABIDE artifact is deterministic, identifier-free, validated offline, uses `null` for missing | PASS | 40,939 bytes, sha256 `93761624…`; `--check` OK; identifier regex + curated-list validation; `null` for missing. |
| Histogram calculations are pure, tested, conserve counts, exactly the requested bins for nonconstant data | PASS | `src/histogram.ts`, 14 tests incl. count conservation over `[1,2,3,7,10,50]` bins and "exactly N bins". |
| Variable and bin controls trigger a real Plotly redraw | PASS | `Plotly.react()`; `data-render-count` increments; bar `d`-path signature and `g.point` count change — standalone + built-page e2e. |
| The production iframe replaces only the obsolete histogram experiment | PASS | 2-cell `nbformat` edit; retention `ipywidgets` cells and all other prose untouched; single confined diff hunk. |
| Built Chapter 1 browser tests prove the actual figure changes for both controls | PASS | `e2e-book/chapter01.spec.ts` against `book/_build/html` at the `/ml-neuro-tutorials/` subpath. |
| Viewer runtime makes no CDN/kernel/off-origin requests | PASS (for the activity) | Standalone e2e: 0 off-origin/CDN/kernel; built-page e2e: activity-frame requests all same-origin. The surrounding Jupyter Book page's own MathJax/font/thebe CDN use is pre-existing and out of scope — see Problems. |
| GitHub Actions builds and tests the frontend before deploying the Jupyter Book | PASS | `deploy.yml` steps 1–7 + built-page e2e before `peaceiris/actions-gh-pages`. |
| CI fails on notebook execution-error reports | PASS | `*.err.log` guard step (`shopt -s globstar`, prints + `exit 1`). |
| Clean install, typecheck, Python/unit tests, prod build, prod-dep audit, Jupyter Book build, Playwright tests pass | PASS | Tests table. |
| Generated output is not committed | PASS | `git status` clean; app/build/node_modules/pycache ignored. |
| Documentation and `WPs/reports/WP03_REPORT.md` are complete | PASS | `interactive/README.md` updated; this report. |
| Working tree clean after separate implementation and report commits | PASS (impl verified; report commit follows) | `git status --porcelain` empty after `4b4ab42`. |
| No retention activity or WP04 file created | PASS | No retention component/config/data; no `WP04*` file; retention notebook cells unchanged. |

## Deviations from instructions
- **Removed `plotly` from `requirements.txt`.** WP03 §6.5 requires removing histogram-only CDN dependencies made obsolete by the replacement. After the notebook edit, no notebook imports `plotly` (`exercise_01_widgets.ipynb` never did), so the pip dependency is now dead. Low risk: CI only runs `jupyter-book build book`. One-line revert if the reviewer wants it kept for Colab parity.
- **The artifact Zod schema lives in `interactive/src/histogram-data.ts`, imported by `components/histogram.ts`, rather than literally inside the component file.** This keeps it free of the Plotly import so it can be unit-tested in the Vitest `node` environment (WP §4: "plotting and calculations must be testable independently"). It is still owned and used only by the histogram component.
- **Added a third exporter mode `--print-upstream-hash`** (network, read-only) beyond the two required, to make an intentional hash update reviewable without writing.
- **Split Playwright into two configs.** `playwright.config.ts` (standalone app, `e2e/`) and `playwright.book.config.ts` (built book, `e2e-book/`, `npm run test:e2e:book`). `npx playwright test` covers the standalone suite only, matching the WP §8 command ordering (it runs before `jupyter-book build`); CI runs the built-book suite after the book build.
- **Built-page e2e scopes the "no CDN / off-origin" assertion to requests whose originating frame is the activity iframe.** The Jupyter Book page itself loads MathJax, Google Fonts, `sphinx-thebe`, `require.js` (cdnjs) and `@jupyter-widgets/html-manager` (jsdelivr) — pre-existing `sphinx-book-theme` / launch-button / `ipywidgets` behaviour, not introduced or removable by WP03. See Problems.
- **Added `__pycache__/` and `*.pyc` to `.gitignore`** (housekeeping; `.pyc` files were briefly staged and removed before the commit).
- **Node 24 locally**; `package.json` `engines` is `>=20.19.0 <25` and CI is pinned to Node 22 as required.

## Problems and unresolved risks
- **The surrounding Chapter 1 page is not itself CDN-free.** `book/_build/html/chapters/chapter_01/exercise_01.html` requests MathJax and MathJax fonts (jsdelivr), Google Fonts, `sphinx-thebe.js/css`, `require.js` (cdnjs) and `@jupyter-widgets/html-manager` (jsdelivr), and embeds a `requestKernel: true` thebe config. These come from `sphinx-book-theme`, the launch buttons, and the still-present `ipywidgets` retention cells — all pre-existing. The **activity iframe** makes zero CDN/kernel/off-origin requests (asserted). Making the whole page CDN-free (self-hosted MathJax, disabling thebe, replacing the `ipywidgets` retention widget) is recommended for WP04.
- **`npm audit` (full tree) still reports the WP02 dev-toolchain advisories** (esbuild/vite dev server, `@vitest/mocker`/vitest UI). None are reachable from `vitest run` / `vite build` / `playwright test` or the shipped bundle. `npm audit --omit=dev` is clean. Carried forward for an isolated toolchain-bump WP, as in WP02.
- **Bundle size** 1.46 MB raw / 489 kB gzip (cartesian Plotly), above Vite's 500 kB warning. Acceptable for a lazy-loaded iframe; code-splitting / a smaller dist is a WP04 option.
- **e2e depends on Plotly's internal SVG structure** (`g.trace.bars g.point path`). A future Plotly major could rename these; the independent `data-render-count` / `data-bar-count` attribute checks would still catch a redraw/rebin.
- **`jupyter-book build book` still exits 0 on notebook execution errors.** Mitigated in CI by the new `*.err.log` guard; local builds still need the guard run by hand.
- **`AGE_AT_SCAN` maximum is 64.0** in the source (a few adult participants). This is the data value, not a control bound — the bin slider range (5–60) is a bin *count* range and is unaffected; the histogram always spans the observed `[min,max]`.
- **The pinned source is a third-party GitHub mirror.** If that commit is ever removed, `--refresh` breaks (but `--check` and the committed artifact keep the site building). Documented in `interactive/README.md`.

## Git commits created
- Checkpoint commit: `dfb4076631a37126c74488af52453d632af8935d` ("checkpoint: before WP03")
- Checkpoint tag: `wp03-start` (annotated, `aa5f6ca49410a36c8cb60243f144b7ba6b3de341`, points at `dfb4076`)
- Implementation commit: `4b4ab42a65e70b1437dc72486cee0c72559e8161` ("WP03: add production ABIDE histogram activity")
- The report commit ("WP03 report: document results") hash is printed in the terminal summary because the report cannot contain its own future hash.

## Recommended scope for WP04
Recommendations only. Do not create or begin WP04.
- **Missing-data retention activity** as the second real component: a pure, unit-tested retention calculation + its Zod data schema + a declarative config, replacing the `ipywidgets` `SelectMultiple` / `interactive_output` cells (36–37) in `exercise_01.ipynb` with an iframe. Reuse the `export_widget_data.py` pipeline (add the needed columns; still identifier-free).
- **Once the retention widget is gone**, remove the `@jupyter-widgets/html-manager` CDN dependency, and decide the fate of `exercise_01_widgets.ipynb` (still "not included in any toctree").
- **Page-level CDN removal**: self-host MathJax, disable/trim `sphinx-thebe` and `requestKernel`, and provide a self-hosted font, so the whole published page — not only the iframe — is CDN-free per Rule 8.
- **Toolchain security bump** (Vite ≥ 6 / Vitest ≥ 3 or then-current) as an isolated WP with a full typecheck/unit/build/e2e re-run to clear the dev-only `npm audit` advisories.
- **Plotly bundle**: code-split behind a dynamic `import()` or evaluate a smaller distribution once the final trace-type set (bar/heatmap) is fixed.
- **Optional**: dynamic iframe height (out of scope here) and a shared `serve-*.mjs` helper to reduce duplication between the two e2e servers.

## Instructions for reviewer
Paste this entire report into the ChatGPT conversation that produced WP03.
