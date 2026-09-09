# `interactive/` — reusable widget runtime

A kernel-free, CDN-free browser runtime for the interactive activities embedded
in the Jupyter Book. It loads a validated JSON **config** + **data** file and
renders an activity with a locally bundled copy of Plotly.js.

> **Status (WP03):** the first production activity, `eda-histogram`, is live and
> embedded in Chapter 1. The developer smoke activity (`runtime-smoke`) remains a
> fixture. The missing-data retention activity is still later work.

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
| `npm run test:unit` | Vitest unit tests (`tests/*.test.ts`): histogram maths, config + data + URL validation. |
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

### Refreshing the pinned ABIDE data — intentional only

`scripts/export_widget_data.py` pins the source CSV by URL **and** SHA-256.

```bash
.venv/bin/python scripts/export_widget_data.py --check              # offline: validate the committed artifact
.venv/bin/python scripts/export_widget_data.py --print-upstream-hash # network: show the current upstream SHA-256
.venv/bin/python scripts/export_widget_data.py --refresh             # network: verify hash, rewrite the artifact
```

`--refresh` **fails loudly** if the upstream bytes no longer match
`SOURCE_SHA256`; it never silently rewrites teaching data. To adopt a genuine
upstream change: run `--print-upstream-hash`, review the upstream diff, update
the `SOURCE_SHA256` constant in the script in the same commit, then run
`--refresh` and commit the regenerated `abide_histogram.json`. The artifact is
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

## `runtime-smoke` is a test fixture

`runtime-smoke` (component, `configs/runtime_smoke.json`, `data/runtime_smoke.json`)
is a **developer smoke test**, not student material. It renders a trivial bar
chart and a "Plotted series" selector that forces a full `Plotly.react()` redraw
and bumps a `data-render-count` attribute. Its only job is to prove the runtime,
bundling, URL handling, and browser tests work.
