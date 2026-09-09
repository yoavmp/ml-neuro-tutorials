# `interactive/` — reusable widget runtime

A kernel-free, CDN-free browser runtime for the interactive activities embedded
in the Jupyter Book. It loads a validated JSON **config** + **data** file and
renders an activity with a locally bundled copy of Plotly.js.

> **Status (WP04):** two production activities are live and embedded in
> Chapter 1 — `eda-histogram` (variable distributions) and `eda-retention`
> (complete-case retention by acquisition site). The developer smoke activity
> (`runtime-smoke`) remains a fixture. The obsolete `ipywidgets` / JupyterLite /
> Voici experiment (notebook cells, `exercise_01_widgets.ipynb`, and the
> `jupyterlite_sphinx` config) was removed in WP04 once the browser-native
> replacements passed; the **Open in Colab** launch button is unchanged.

## Prerequisites

- **Node** ≥ 20.19 (`< 25`). CI runs Node 22 (`.github/workflows/deploy.yml`);
  local development has also used Node 24. The supported range is declared in
  `package.json` `engines`.
- npm (ships with Node). Install exact locked versions with `npm ci`.
- For end-to-end tests only: the project-managed Chromium, installed with
  `npx playwright install chromium`. No system browser is used.
- The **built Jupyter Book** end-to-end test additionally needs a Python
  environment that can run `jupyter-book build book` (repo `requirements.txt`).

## Commands

| Command | What it does |
|---|---|
| `npm ci` | Install exact locked dependencies. |
| `npm run typecheck` | `tsc --noEmit`, strict. |
| `npm run test:unit` | Vitest unit tests (`tests/*.test.ts`): histogram maths, complete-case retention maths, config + data + URL validation. |
| `npm test` | typecheck + unit tests. |
| `npm run build` | typecheck, then `vite build` → `../book/_static/widgets/app/`. |
| `npm run serve:static` | Serve `book/_static/widgets/` over HTTP on `:4173` for manual checks. |
| `npm run serve:book` | Serve `book/_build/html` over HTTP on `:4174` (build the book first). |
| `npm run test:e2e` | Builds first (`pretest:e2e`), then runs Playwright/Chromium against the built widget files (`e2e/`). |
| `npm run test:e2e:book` | Runs Playwright against the **built Jupyter Book** Chapter 1 page (`e2e-book/`). Requires `jupyter-book build book` to have run. |

Manual preview after a build:

```bash
npm run build
npm run serve:static
# smoke fixture:
#   http://localhost:4173/app/index.html?config=../configs/runtime_smoke.json
# production histogram:
#   http://localhost:4173/app/index.html?config=../configs/eda_histogram.json
# production retention explorer:
#   http://localhost:4173/app/index.html?config=../configs/eda_retention.json
# subpath check: prefix the path with /ml-neuro-tutorials
```

Preview the real embedded page (iframe under the actual Chapter 1 route):

```bash
cd interactive && npm run build && cd ..
rm -rf book/_build && .venv/bin/jupyter-book build book
cd interactive && npm run serve:book
# open http://localhost:4174/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html
```

## The `eda-histogram` activity

| Piece | Path | Tracked? |
|---|---|---|
| Config (title, variables + labels, default, bin range, prompts) | `book/_static/widgets/configs/eda_histogram.json` | yes |
| Data artifact (one array per variable, `null` for missing) | `book/_static/widgets/data/abide_histogram.json` | yes |
| Pure binning maths (no DOM/Plotly) | `interactive/src/histogram.ts` | yes |
| Data Zod schema (no DOM/Plotly) | `interactive/src/histogram-data.ts` | yes |
| Component (selector, bin slider, Plotly bar trace) | `interactive/src/components/histogram.ts` | yes |

The component plots a Plotly **bar** trace built from `computeHistogram(...)` — the
number of bins and the counts are exactly the tested values, never delegated to a
Plotly histogram trace. Constant and all-missing variables have defined,
tested behaviour (one unit-wide bin / an explicit "no data" message).

### Authoring / changing the activity

1. Edit `configs/eda_histogram.json`. Every default is validated against its
   allowed set/range at load time (`src/config.ts`), so an out-of-range default
   bin count or an unknown `defaultVariable` fails fast with a visible error.
2. To add a variable it must also be present in the data artifact — add its name
   to `HISTOGRAM_VARIABLES` in `scripts/export_widget_data.py` and re-run the
   refresh (below).
3. `npm run typecheck && npm run test:unit && npm run build`, then
   `npm run test:e2e` and (after a book build) `npm run test:e2e:book`.

## The `eda-retention` activity

| Piece | Path | Tracked? |
|---|---|---|
| Config (title, grouped candidate variables + labels, defaults, prompts) | `book/_static/widgets/configs/eda_retention.json` | yes |
| Data artifact (`SITE_ID` + 13 candidate columns, `null` for missing) | `book/_static/widgets/data/abide_retention.json` | yes |
| Pure complete-case maths (no DOM/Plotly) | `interactive/src/retention.ts` | yes |
| Data Zod schema (no DOM/Plotly) | `interactive/src/retention-data.ts` | yes |
| Component (grouped checkboxes, presets, Plotly bar of retained % by site) | `interactive/src/components/retention.ts` | yes |

Students tick candidate "core" variables; a participant is retained only when
**every** ticked variable is non-`null` for them. The component shows overall
retained N / total / percentage and excluded N, a per-site bar chart (hover =
retained N / site total), an explicit "no completeness criterion is currently
applied" state when nothing is selected, and a warning cue when a selection
keeps under 50 % overall (a prompt to look closely, **not** a universal
scientific cutoff). `Use suggested core set`, `Select all`, and `Clear` presets
drive the same recompute-and-`Plotly.react()` path as the checkboxes.

### Why `SITE_ID` is in this artifact but participant identifiers never are

Grouped retention summaries are impossible without a site-grouping label, so the
retention exporter has **one** deliberately narrow exception: the exact column
name `SITE_ID` is allowed through, and only into `abide_retention.json`. It is a
coarse, non-personal acquisition-site code (19 values). `SUB_ID`, subject /
participant IDs, names, emails, dates of birth and arbitrary `*_ID` fields stay
rejected by the same token regex in both the Python builder/validator and the
client-side Zod schema. No participant row is ever exposed — the chart hover
carries site-level aggregates only.

### Default retention — regression reference

With the shipped `abide_retention.json` (1,114 rows) and the suggested core set
**`DX_GROUP`, `AGE_AT_SCAN`, `SEX`, `FIQ`**, independently cross-checked with
pandas:

| Metric | Value |
|---|---|
| Retained overall | **1,015 / 1,114 = 91.1131 %** |
| Excluded overall | 99 |
| `ABIDEII-BNI_1` | 58 / 58 (100 %) |
| `ABIDEII-EMC_1` | 0 / 54 (0 % — FIQ absent site-wide) |
| `ABIDEII-IP_1` | 25 / 56 (44.64 %) |
| `ABIDEII-USM_1` | 27 / 33 (81.82 %) |

Selecting the two behavioral totals `SCQ_TOTAL` + `ADOS_2_TOTAL` instead retains
**119 / 1,114 = 10.6822 %**; `Select all` (13 variables) retains 26 / 1,114
(2.33 %) and trips the low-retention warning. Site order is the SITE_ID column's
first appearance order.

### Refreshing the pinned ABIDE data — intentional only

`scripts/export_widget_data.py` pins the source CSV by URL **and** SHA-256, and
produces **two** artifacts from it. `--refresh` / `--check` take an optional
`--artifact {histogram,retention,all}` (default `all`); the bare WP03 forms keep
working and now cover both files. `--artifact histogram` only ever touches
`abide_histogram.json` and `--artifact retention` only ever touches
`abide_retention.json`, so refreshing one cannot rewrite or delete the other.

```bash
.venv/bin/python scripts/export_widget_data.py --check                       # offline: validate BOTH committed artifacts
.venv/bin/python scripts/export_widget_data.py --check --artifact retention   # offline: just the retention artifact
.venv/bin/python scripts/export_widget_data.py --print-upstream-hash          # network: show the current upstream SHA-256
.venv/bin/python scripts/export_widget_data.py --refresh --artifact all       # network: verify hash, rewrite both artifacts
```

`--refresh` **fails loudly** if the upstream bytes no longer match
`SOURCE_SHA256`; it never silently rewrites teaching data. To adopt a genuine
upstream change: run `--print-upstream-hash`, review the upstream diff, update
the `SOURCE_SHA256` constant in the script in the same commit, then run
`--refresh` and commit the regenerated artifact(s). Each artifact is
byte-for-byte deterministic (sorted keys, compact separators, trailing newline),
so a no-op `--refresh` produces no diff.

Python tests (standard-library `unittest`, no network):

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_export_widget_data.py'
```

## Source vs generated

| Path | Tracked? | Notes |
|---|---|---|
| `interactive/src`, `tests`, `e2e`, config files | yes | Hand-written source. |
| `interactive/package-lock.json` | yes | Exact dependency lock. |
| `interactive/node_modules/`, `interactive/dist/` | no (git-ignored) | Reproduced by `npm ci` / `vite`. |
| `book/_static/widgets/app/` | **no (git-ignored)** | Vite build output. Regenerate with `npm run build`. Sphinx copies it through from `book/_static/` at book-build time. |
| `book/_static/widgets/configs/*.json` | yes | Activity configs (hand-written). |
| `book/_static/widgets/data/*.json` | yes | Small exported activity data. |
| `interactive/test-results/`, `playwright-report/` | no (git-ignored) | Playwright artifacts. |

## Config and data URL resolution

The app page is loaded as:

```
.../_static/widgets/app/index.html?config=<relative-url>
```

1. `config` is **required**. It is resolved against the app page URL.
2. Only **same-origin** `http(s)` URLs are allowed. Cross-origin URLs, URLs with
   embedded credentials, non-`http(s)` protocols (including `file:`), missing and
   malformed values are all rejected with a visible in-frame error panel.
3. The config JSON must carry an explicit integer `schemaVersion` (currently `1`)
   and a discriminated `type`. It is validated with Zod before use.
4. The config's `data` field is resolved **relative to the config file's URL**,
   not the browser page, and passes the same same-origin checks.
5. The data JSON is validated by the component's own schema before rendering.

Because everything is same-origin and relative, the identical build works at the
site root and beneath the GitHub Pages project subpath
(`https://<user>.github.io/ml-neuro-tutorials/...`) — `vite.config.ts` sets
`base: './'` so no asset path is hard-coded.

## Why `file://` is unsupported

The runtime `fetch()`es the config and data files. Browsers treat `file://`
pages as opaque / null-origin, so `fetch` of a sibling file is blocked and the
same-origin check cannot pass. Always preview over HTTP (`npm run serve:static`)
and embed from the HTTP-served Jupyter Book. The protocol allow-list also
explicitly rejects `file:` with a readable error.

## How the component registry supports later activities

`src/components/types.ts` defines a `WidgetComponent` contract (`type`,
`parseData`, `mount`) and a `ComponentRegistry`. `src/components/registry.ts` is
the single wiring point. `src/main.ts` never branches on the activity type — it
looks the component up by `config.type`. Adding the histogram activity later is:

1. add a config member to the discriminated union in `src/config.ts`;
2. add `src/components/histogram.ts` exporting a `WidgetComponent`;
3. `registry.register(histogramComponent)` in `registry.ts`;
4. keep the pure binning/statistics math in its own module so it can be unit
   tested without a DOM or Plotly.

## Page-level CDN / theme dependencies (still present, out of scope here)

Each **activity iframe** is same-origin and CDN/kernel-free — asserted by the
standalone and built-book Playwright specs, which scope their "no off-origin /
CDN / kernel / WebSocket" checks to requests originating inside the app frame.

The surrounding Chapter 1 *page* still pulls **MathJax** from
`cdn.jsdelivr.net/npm/mathjax@3` (`sphinx-book-theme` / MyST default) and still
ships `sphinx-book-theme`'s launch-button `sphinx-thebe.js` (same-origin) whose
inline config names `https://unpkg.com/thebe@0.8.2/...` — thebe itself is only
fetched if a reader clicks a "live code" button, which this course does not
surface. Both are pre-existing `sphinx-book-theme` behaviour, unrelated to the
activities.

The WP04 legacy cleanup **did** remove, from this page: `require.js` (cdnjs),
`@jupyter-widgets/html-manager` (jsdelivr) and the notebook widget-manager
bootstrap (they came with the now-deleted `ipywidgets` cells), and the entire
`lite/` JupyterLite app (`jupyterlite_sphinx` config dropped from
`book/_config.yml`). No Google Fonts request is made by this page.

Self-hosting the remaining MathJax / trimming the thebe config so the whole
published page — not just the iframes — is CDN-free is deliberately **out of
scope** for this WP (see `WP04_MISSING_DATA_RETENTION.md`
§"Fixed teaching decisions").

## `runtime-smoke` is a test fixture

`runtime-smoke` (component, `configs/runtime_smoke.json`, `data/runtime_smoke.json`)
is a **developer smoke test**, not student material. It renders a trivial bar
chart and a "Plotted series" selector that forces a full `Plotly.react()` redraw
and bumps a `data-render-count` attribute. Its only job is to prove the runtime,
bundling, URL handling, and browser tests work.
