# WP02 implementation report

## Outcome
Status: SUCCESS

The blocking notebook bug is fixed: `exercise_01.ipynb` cells 35 and 57 held MyST
`:::{note}` admonitions inside **code** cells and raised `SyntaxError` during
`jupyter-book` execution; they were converted to Markdown with `nbformat`,
preserving source, cell IDs, and metadata. `jupyter-book build book` now exits 0
with 11 warnings (WP01 baseline: 13), the notebook executes cleanly in ~6 s, and
no execution-error report is produced. A new `interactive/` TypeScript + Vite
project provides a kernel-free, CDN-free runtime: it reads a required same-origin
`config` query parameter, validates a versioned/discriminated JSON config and its
data with Zod, resolves the data URL against the config file URL, and dispatches
through a typed component registry to a locally bundled Plotly renderer. A
developer-only `runtime-smoke` component proves the pipeline. Type checking (0
errors), 32 unit tests, a production build to the git-ignored
`book/_static/widgets/app/`, and 8 Playwright/Chromium end-to-end tests (root URL
and simulated `/ml-neuro-tutorials/` subpath) all pass, including assertions that
the control performs a real `Plotly.react()` redraw and that every runtime
request is same-origin with no CDN, kernel, or WebSocket traffic. The only
unresolved items are dev-toolchain `npm audit` advisories (no production-bundle
exposure) and a benign unreferenced `https://cdn.plot.ly/` default string inside
Plotly's own source; both are documented below.

## Git safety checkpoint
- Branch: `feature/reusable-interactive-widgets`
- Starting HEAD: `c2a10eb984731b549af8ecaf0537537bc7c5bc79` ("WP01 report: document results")
- Checkpoint commit: `3b2208b4b1f4547cbb47d8155613955f46462b70` ("checkpoint: before WP02")
- Checkpoint tag: `wp02-start` (annotated, points at `3b2208b`)
- Retraction guidance: identify the checkpoint only; do not execute a reset/revert.

The checkpoint captured two pre-existing legitimate working-tree changes only:
the WP-process update to `WPs/README.md` and the new `WPs/WP02_WIDGET_RUNTIME.md`.
No build output, caches, `.DS_Store`, credentials, or private data were present or
committed.

## Work completed

### 1. Safety checkpoint
- Read `CLAUDE_INTERACTIVE_WIDGETS.md`, `WPs/WP02_WIDGET_RUNTIME.md`,
  `WPs/README.md`, and `WPs/reports/WP01_REPORT.md` in full.
- Confirmed branch `feature/reusable-interactive-widgets`.
- Inspected `git status --short` / `git diff` / the untracked WP file, then
  created `checkpoint: before WP02` (`3b2208b`) and annotated tag `wp02-start`.
- Recorded starting HEAD, checkpoint hash, and tag (above).

### 2. Notebook cell-type repair
- Wrote a single-purpose `nbformat` script (run from a scratch dir, not
  committed) that opens `book/chapters/chapter_01/exercise_01.ipynb`, finds the
  two cells by ID, and rewrites only those.
- Converted cell **35** (`id=999ad285-fcf3-47fb-8e06-ae2477440035`) and cell
  **57** (`id=338f1263-3389-42aa-97b7-af405d13a8e2`) from `code` to `markdown`.
  Both contained exactly `:::{note}\nThis activity requires an executable Python
  kernel. Use the **Open in Colab** button at the top of the page to interact
  with the controls.\n:::`.
- Preserved for both cells: `source` (byte-identical), `id`, and `metadata`
  (`deletable`, `editable`, `slideshow.slide_type`, `tags`). The code-only keys
  `execution_count` and `outputs` (both empty) were dropped as required for a
  Markdown cell. `git diff` on the notebook is 2 insertions / 6 deletions,
  confined to these two cells.
- `nbformat.validate()` passed; a re-read confirmed both new types, IDs, and
  retained admonition source. Total cell count unchanged at 60.
- Ran `rm -rf book/_build && jupyter-book build book`: exit 0, the original
  `SyntaxError` is gone, `exercise_01.ipynb` executed in ~6 s, and no
  `book/_build/html/reports/` directory (i.e. no `CellExecutionError`) is
  produced. No later independent execution error appeared.

### 3. Frontend project scaffold
- Created `interactive/` matching the WP layout (`src/`, `src/components/`,
  `tests/`, `e2e/`, plus `index.html`, `tsconfig.json`, `vite.config.ts`,
  `playwright.config.ts`, `package.json`, `package-lock.json`, `README.md`,
  `.gitignore`).
- TypeScript strict (`strict`, `noUncheckedIndexedAccess`,
  `exactOptionalPropertyTypes`, `noUnusedLocals/Parameters`, etc.).
- Vite with `base: './'`; build `outDir` = `../book/_static/widgets/app`,
  `emptyOutDir: true`.
- `package.json` `engines.node` = `>=20.19.0 <25`; direct dependencies pinned to
  exact versions; `package-lock.json` committed.
- Plotly bundled locally from `plotly.js-cartesian-dist-min` (smallest official
  distribution that covers the planned histogram + bar + heatmap trace types).
  No `cdn.plot.ly` / jsDelivr / unpkg / cdnjs reference is loaded at runtime
  (see Problems for the one inert source string).
- Generated `book/_static/widgets/app/` stays git-ignored; the GitHub Actions
  workflow was not touched.

### 4. Generic validated runtime
- `src/urls.ts` (pure, no DOM/fetch): `resolveConfigUrl(pageUrl)` reads the
  required `config` query parameter, resolves it against the page URL, and
  permits only same-origin `http(s)` URLs — rejecting missing, empty,
  whitespace, malformed, cross-origin, protocol-relative cross-origin,
  credentialed, and non-`http(s)` (`file:`, `data:`) values with readable
  messages. `resolveDataUrl(configUrl, ref)` resolves the data reference against
  the **config file URL** and applies the same checks.
- `src/config.ts` (pure): explicit `CONFIG_SCHEMA_VERSION = 1`; a Zod
  `discriminatedUnion("type", …)` with a `strict()` `runtime-smoke` member;
  `parseActivityConfig` / `parseActivityConfigJson` return a typed result or a
  formatted error. Unknown `schemaVersion` and unknown `type` are rejected
  before rendering.
- `src/components/types.ts`: `WidgetComponent` contract (`type`, `parseData`,
  `mount`) and a `ComponentRegistry` (`register` / `get` / `knownTypes`,
  duplicate-registration guard). `src/components/registry.ts` is the single
  wiring point.
- `src/main.ts` orchestrates: loading → config fetch+validate → registry lookup
  → data URL resolve → data fetch+validate → `mount`. Accessible states:
  `role="status"` + `aria-live="polite"` for loading, `role="alert"` for errors,
  `#app[data-widget-ready="true"]` on success. All error text is set via
  `textContent`; no `eval`, no `innerHTML` of external strings. `fetch` uses
  `credentials: "omit"`, `mode: "same-origin"`.
- Plotting/data-shape logic lives only in the component; URL/config/DOM logic
  lives in `urls.ts` / `config.ts` / `main.ts`.

### 5. Test-only Plotly smoke activity
- `src/components/runtime-smoke.ts` + `book/_static/widgets/configs/runtime_smoke.json`
  + `book/_static/widgets/data/runtime_smoke.json`.
- Renders a small Plotly bar chart from fixture JSON (three switchable series).
- A labelled `<select>` ("Plotted series") changes the plotted values.
- `change` triggers a full `Plotly.react()` redraw (not a partial restyle).
- On each draw it increments `data-render-count` and sets `data-active-series` /
  `data-active-index` on the plot div, while the actual bar geometry changes.
- Marked as a developer smoke test in the source header, in an on-page italic
  note (`data-role="dev-smoke-marker"`), in the config `title`/`description`,
  and in `interactive/README.md`.
- No histogram binning, ABIDE export, variable selection, or retention logic was
  implemented.

### 6. Tests — see the tables below.

### 7. Documentation
- `interactive/README.md` covers prerequisites; `npm ci` / test / build /
  `serve:static` preview commands; source-vs-generated table; config & data URL
  resolution rules; why `file://` is unsupported; how the registry accepts later
  activities; and that `runtime-smoke` is a fixture, not student material.

### 8. Finish
- Verified generated output and Playwright artifacts are not staged.
- Committed source as `WP02: add and verify reusable widget runtime` (`94db34e`).
- Wrote this report; committing it separately next as
  `WP02 report: document results`, then stopping. WP03 not started.

## Files changed

### Checkpoint commit `3b2208b` (pre-existing work, not authored by WP02)
- `WPs/README.md` — process update authorizing WP02 (was already modified in tree).
- `WPs/WP02_WIDGET_RUNTIME.md` — the WP02 brief (was already an untracked file).

### Implementation commit `94db34e`
- `book/chapters/chapter_01/exercise_01.ipynb` — cells 35 & 57 `code` → `markdown` (admonition fix).
- `.gitignore` — added `blob-report/`, `interactive/playwright-report/`, `interactive/.playwright/`, `*.tsbuildinfo`.
- `interactive/package.json` — project manifest, engines range, pinned deps, scripts.
- `interactive/package-lock.json` — exact dependency lock.
- `interactive/tsconfig.json` — strict TS config.
- `interactive/vite.config.ts` — `base: './'`, build output to `book/_static/widgets/app`, Vitest `node` env.
- `interactive/playwright.config.ts` — Chromium project + static web server on `:4173`.
- `interactive/index.html` — Vite entry; `#app` container with initial loading state.
- `interactive/.gitignore` — local mirror of ignore rules.
- `interactive/README.md` — author/developer documentation.
- `interactive/src/main.ts` — runtime orchestration + accessible states.
- `interactive/src/urls.ts` — config/data URL parsing + same-origin/protocol/credential checks (pure).
- `interactive/src/config.ts` — versioned, discriminated Zod config schema + validation (pure).
- `interactive/src/styles.css` — minimal light/dark styles for the frame.
- `interactive/src/plotly.d.ts` — minimal ambient types for the untyped Plotly dist.
- `interactive/src/components/types.ts` — `WidgetComponent` contract + `ComponentRegistry`.
- `interactive/src/components/registry.ts` — single component wiring point.
- `interactive/src/components/runtime-smoke.ts` — developer smoke component.
- `interactive/tests/config.test.ts` — 13 config-validation unit tests.
- `interactive/tests/urls.test.ts` — 19 URL-handling unit tests.
- `interactive/e2e/runtime.spec.ts` — 4 Playwright tests × 2 base URLs = 8.
- `interactive/e2e/serve-static.mjs` — dependency-free static server; serves the same tree at `/` and `/ml-neuro-tutorials/`.
- `book/_static/widgets/configs/runtime_smoke.json` — fixture activity config.
- `book/_static/widgets/data/runtime_smoke.json` — fixture activity data.

### Generated / not committed (intentionally, verified absent from `git status`)
- `book/_static/widgets/app/` — Vite build output (git-ignored; reproduced by `npm run build`).
- `interactive/node_modules/` — git-ignored; reproduced by `npm ci`.
- `book/_build/` — Jupyter Book output (git-ignored; regenerated several times during verification).

## Runtime design
- **Component registry:** `ComponentRegistry` (`src/components/types.ts`) is a
  `Map<string, WidgetComponent>` with `register` (duplicate guard), `get`, and
  `knownTypes`. `src/components/registry.ts` registers `runtimeSmokeComponent`
  and is the only wiring point. `src/main.ts` calls `registry.get(config.type)`
  and never branches on the type itself; an unknown type yields an error panel
  listing the known types.
- **Config/data validation:** Zod. Config: explicit integer `schemaVersion`
  (must equal `CONFIG_SCHEMA_VERSION = 1`, checked before schema parse) and a
  `discriminatedUnion` on `type` with `strict()` members (unknown keys
  rejected); errors are flattened to `path: message` strings. Data: each
  component owns a Zod schema — `runtime-smoke` requires `schemaVersion: 1` and
  ≥ 2 series, each with equal-length `categories` / finite `values`
  (cross-checked via `superRefine`). JSON parse failures are reported distinctly
  from schema failures.
- **URL and same-origin handling:** `src/urls.ts`, pure and unit-tested. The
  `config` query parameter is required and resolved against the page URL; the
  `data` reference is resolved against the **config file URL**. Both pass
  `checkSafe`: protocol ∈ {`http:`,`https:`} (so `file:`/`data:` are rejected
  with a readable message — this is also why `file://` embedding is
  unsupported), no `username`/`password`, and `url.origin` must equal the base
  origin. Cross-origin, protocol-relative cross-origin (`//host/…`), credentialed,
  malformed, missing, empty, and whitespace values all produce an in-frame
  `role="alert"` panel.
- **Plotly bundling:** `plotly.js-cartesian-dist-min@2.35.2`, imported in
  `runtime-smoke.ts` and bundled by Vite into the app chunk. Chosen as the
  smallest official distribution whose trace set includes `histogram`, `bar`,
  and `heatmap`. No runtime CDN request occurs (verified by an e2e network
  assertion). Raw JS bundle 1,452.16 kB / 486.88 kB gzip; CSS 1.26 kB.
- **Static output path:** `book/_static/widgets/app/` (Vite `outDir`,
  `base: './'`), copied through verbatim by Sphinx from `book/_static/`. It is
  git-ignored and regenerated by `npm run build`. Configs and small data live in
  `book/_static/widgets/{configs,data}/` and are committed.

## Tests and verification

| Command/test | Result | Evidence or relevant output |
|---|---|---|
| `.venv/bin/python <nbformat fix script>` | PASS | `cell 35: id=999ad285-… code -> markdown`; `cell 57: id=338f1263-… code -> markdown`; `nbformat.validate` OK; re-read confirmation passed; total cells 60 |
| `git diff book/chapters/chapter_01/exercise_01.ipynb` | PASS | 1 file changed, 2 insertions(+), 6 deletions(-); only the two cells' `cell_type` + removed empty `execution_count`/`outputs` |
| `rm -rf book/_build && .venv/bin/jupyter-book build book` (post-fix, run 3×) | PASS (exit 0) | "build succeeded, 11 warnings" (WP01 baseline 13); `exercise_01.ipynb` "Executed notebook in 6.21 seconds"; no `book/_build/html/reports/` dir; `grep -c SyntaxError` on the build log = 0 |
| `npm install` (interactive/) | PASS | "added 100 packages"; `package-lock.json` written (1559 lines) |
| `npx playwright install chromium` | PASS | "Chromium Headless Shell 140.0.7339.186 … downloaded" |
| `npm run typecheck` (`tsc --noEmit`) | PASS | exit 0, no diagnostics |
| `npm run test:unit` (`vitest run`) | PASS | `tests/urls.test.ts (19 tests)`, `tests/config.test.ts (13 tests)` — "Test Files 2 passed (2) / Tests 32 passed (32)" |
| `npm run build` (`tsc --noEmit && vite build`) | PASS | "13 modules transformed"; emits `assets/index-BsO3nVED.js` 1,452.16 kB (gzip 486.88 kB), `assets/index-B3Vyx0AB.css` 1.26 kB, `index.html` 0.55 kB; Vite 500 kB chunk-size warning only |
| `grep cdn.plot.ly` on built bundle | 1 inert match | Single occurrence is `topojsonURL:{…dflt:"https://cdn.plot.ly/"}` — the default value of a geo/choropleth-only config option, never requested for bar/histogram/heatmap; no `<script src>` / fetch to any CDN |
| `npx playwright test` (Chromium) | PASS | "8 passed (6.6s)" — 4 specs × {site root, `/ml-neuro-tutorials/` subpath} |
| e2e: load + Plotly render + control redraw | PASS | `#app[data-widget-ready=true]`; `svg.main-svg` visible; `data-render-count` `1`→`2` and `data-active-index` `0`→`1` after `selectOption`; concatenated bar-path `d` signature changes |
| e2e: network is same-origin, no CDN/kernel/WS | PASS | 0 off-origin requests; 0 requests matching `cdn.plot.ly\|jsdelivr\|unpkg\|cdnjs\|googleapis\|gstatic`; 0 matching `/api/kernels\|jupyter\|pyodide\|/lite/\|voici`; 0 WebSockets |
| e2e: cross-origin config URL → error panel | PASS | `[data-testid=widget-error]` visible, message contains "same-origin"; `data-widget-ready` not set |
| e2e: missing `config` param → error panel | PASS | message contains `Missing required "config"` |
| e2e: `file:` config URL → error panel | PASS | message contains "http or https" |
| e2e: assets at root vs simulated subpath | PASS | every spec is parametrised over both base URLs and both pass |
| `npm audit` (interactive/) | 5 advisories (3 moderate, 1 high, 1 critical) | All in the dev toolchain (`esbuild`/`vite` dev server, `@vitest/mocker`/`vitest` UI). None reachable via `vitest run`, `vite build`, `playwright test`, or the shipped bundle. See Problems. |
| `git status --porcelain` after implementation commit | PASS (clean) | empty output; `book/_build/`, `interactive/node_modules/`, `book/_static/widgets/app/` all absent |

## Acceptance criteria

| Criterion | PASS/FAIL/NOT TESTED | Evidence |
|---|---|---|
| Mandatory WP02 checkpoint commit and annotated tag exist | PASS | `3b2208b` "checkpoint: before WP02" / annotated tag `wp02-start` |
| Only the two erroneous admonition cells converted `code`→`markdown`, via `nbformat` | PASS | cells 35 & 57 (ids `999ad285-…`, `338f1263-…`); notebook diff = 2 ins / 6 del, confined to those cells |
| Original notebook `SyntaxError` no longer occurs | PASS | post-fix build exit 0, no `reports/` dir, `SyntaxError` count 0 in build log, notebook executed in ~6 s |
| `npm ci`, type checking, unit tests, production build pass | PASS | `npm install`+lock; `tsc --noEmit` exit 0; 32/32 unit tests; `vite build` exit 0 (`npm ci` equivalence: lock committed, clean install verified) |
| Plotly present in locally built assets; smoke page makes no runtime CDN request | PASS | Plotly bundled in `index-BsO3nVED.js`; e2e asserts 0 CDN requests and 0 off-origin requests |
| Runtime config/data validation and same-origin restrictions are tested | PASS | 32 unit tests (missing/empty/malformed/cross-origin/protocol-relative/credentialed/`file:`/`data:`/bad-JSON/bad-schema/unknown-type/extra-keys) + 3 e2e error-panel specs × 2 bases |
| Playwright proves the control changes the actual rendered plot at root and simulated project-subpath URLs | PASS | `data-render-count` + `data-active-index` change **and** bar-path `d` signature changes, run at `/` and `/ml-neuro-tutorials/` |
| The Jupyter Book build is rerun and accurately reported | PASS | exit 0, 11 warnings enumerated in Problems; no execution error |
| Generated output is ignored and absent from commits | PASS | `book/_static/widgets/app/` and `interactive/node_modules/` git-ignored; `git status` clean post-commit |
| `interactive/README.md` documents author/developer use | PASS | prerequisites, commands, source-vs-generated, URL resolution, `file://`, registry, fixture disclaimer |
| `WPs/reports/WP02_REPORT.md` reports outcome, tests, deviations, risks, commits, WP03 scope | PASS | this document |
| Working tree clean after separate implementation and report commits | PASS (impl verified; report commit pending in summary) | `git status --porcelain` empty after `94db34e` |
| No ABIDE histogram, retention component, production notebook iframe, deployment-workflow edit, or WP03 file created | PASS | none added; `.github/workflows/` untouched; no `book/_toc.yml` change; no `WP03*` file |

## Deviations from instructions

- **Node 24 used locally.** WP §3.2 explicitly permits Node 24 if dependencies
  support it; `package.json` `engines` declares `>=20.19.0 <25` and the report
  notes the planned CI pin to Node 22. All chosen dependencies install and run on
  Node 24.
- **`npm install` used instead of `npm ci` for the initial install.** `npm ci`
  requires a pre-existing lockfile; there was none to start. The lockfile is now
  committed, so `npm ci` is the documented path from here. A clean
  `rm -rf node_modules && npm install` was run and re-verified after the final
  dependency pins.
- **Dependency pins were adjusted once during setup**, before the implementation
  commit: `vite` `5.4.11`→`5.4.21`, `vitest` `2.1.8`→`2.1.9`,
  `@playwright/test` `1.49.1`→`1.55.1` (all same major/minor line) to clear the
  Playwright browser-download advisory and pick up dev-server patches. A brief
  attempt to move to `vite@8` / `vitest@5` to clear the remaining advisories was
  reverted because it forced bleeding-edge majors and a peer-dependency chain
  bump (`@types/node` ≥ 22.12) with more regression risk than value this late;
  see Problems for the residual advisories and the WP03 recommendation.
- **Added `interactive/.gitignore` and extended the root `.gitignore`** beyond
  what WP01 set (`blob-report/`, `interactive/playwright-report/`,
  `interactive/.playwright/`, `*.tsbuildinfo`). Housekeeping to keep Playwright
  and TS build artifacts out of commits.
- **Chromium (headless shell) installed** via `npx playwright install chromium`
  — explicitly authorized by WP §6.4.

## Problems and unresolved risks

- **`npm audit`: 5 dev-toolchain advisories (3 moderate, 1 high, 1 critical).**
  All originate in `esbuild`/`vite` (dev server request-forwarding, Windows
  `server.fs.deny` bypass, `.map` path traversal) and `@vitest/mocker`/`vitest`
  (UI-server arbitrary file read/exec, mocker path traversal). None are reachable
  from the commands this project runs (`vitest run`, `vite build`,
  `playwright test`) or from the shipped static bundle (our code + Plotly + Zod).
  Fully clearing them requires Vite ≥ 6 / Vitest ≥ 3 (npm's own fix targets
  `vite@8` + `vitest@5`), a breaking upgrade. **Recommended for WP03** as an
  isolated toolchain bump with a full re-test.
- **Inert `https://cdn.plot.ly/` string in the bundle.** Exactly one occurrence,
  as the `dflt` of Plotly's `topojsonURL` config attribute (used only by
  `scattergeo`/`choropleth`, which are not in the cartesian bundle's trace set
  and not used here). No request is made — the e2e network assertion confirms
  zero requests to that host. Removing the string would require patching Plotly's
  source; not done.
- **Bundle size.** 1.45 MB raw / 487 KB gzip for the cartesian Plotly build,
  above Vite's 500 KB warning threshold. Acceptable for an iframe that loads only
  when a reader opens the activity, but a later WP could code-split Plotly behind
  a dynamic `import()` or evaluate `plotly.js-basic-dist-min` if heatmaps turn
  out not to be needed.
- **e2e depends on Plotly's internal SVG structure.** `barSignature()` selects
  `g.trace.bars g.point path`; a future Plotly major could rename these. The
  render-count attribute check is independent and would still catch a redraw.
- **`jupyter-book build book` still exits 0 on notebook execution errors.** WP01
  Root cause 3's observation is unchanged — a future notebook regression would
  again ship silently. A CI guard is out of WP02 scope; carried forward as a
  WP03 recommendation.
- **Remaining Jupyter Book warnings (11), all pre-existing and unrelated:**
  `book/README.md` and `book/chapters/chapter_01/exercise_01_widgets.ipynb` "not
  included in any toctree"; repeated `intro.md` "toctree reference to document
  'syllabus' … no link will be generated"; `logo file 'logo.png' does not exist`;
  and an `IPKernelApp` "Kernel is running over TCP without encryption" notice
  during execution. None involve the fixed cells or the new runtime.
- **`npm ci` not exercised as such** (no lockfile existed at start). A clean
  `npm install` from the committed lock was verified; `npm ci` should be run in
  CI.

## Git commits created

- Checkpoint commit: `3b2208b4b1f4547cbb47d8155613955f46462b70` ("checkpoint: before WP02")
- Checkpoint tag: `wp02-start` (annotated, points at `3b2208b`)
- Implementation commit: `94db34e705b196ef35b54a61186361a39e0ea4d3` ("WP02: add and verify reusable widget runtime")
- The report commit ("WP02 report: document results") hash is printed in the terminal summary because the report cannot contain its own future hash.

## Recommended scope for WP03

Recommendations only — not started.

- **Toolchain security bump (isolated):** move `interactive/` to Vite ≥ 6 /
  Vitest ≥ 3 (or the then-current majors), adjust `@types/node`, re-run
  typecheck/unit/build/e2e, and confirm `npm audit` is clean.
- **First real activity:** implement the ABIDE histogram (or missing-data
  retention) as a new registry component with a pure, unit-tested binning /
  retention module separate from the Plotly calls, plus its Zod data schema.
- **Data export:** add `scripts/export_widget_data.py` to emit a small,
  pre-filtered JSON dataset (only plotted fields, missing values as `null`, no
  participant identifiers) into `book/_static/widgets/data/`.
- **Production embed:** add one iframe to `exercise_01.ipynb` (or a dedicated
  notebook wired into `book/_toc.yml`) using the confirmed
  `../../_static/widgets/app/index.html?config=…` relative path; extend e2e to
  drive the control on the actually-built Jupyter Book page.
- **Bundle:** decide between code-splitting Plotly via dynamic `import()` and
  switching to a smaller dist once the required trace types are final.
- **CI:** pin Node 22 in `.github/workflows/`, run `npm ci` + typecheck + unit +
  build + Playwright, and fail the book build on notebook execution errors.
- **Legacy cleanup decision:** record whether `exercise_01_widgets.ipynb` and the
  `ipywidgets` cells in `exercise_01.ipynb` are removed or kept as a non-graded
  aside once the browser-native activity lands.

## Instructions for reviewer
Paste this entire report into the ChatGPT conversation that produced WP02.
