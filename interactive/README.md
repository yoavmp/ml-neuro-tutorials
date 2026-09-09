# `interactive/` — reusable widget runtime

A kernel-free, CDN-free browser runtime for the interactive activities embedded
in the Jupyter Book. It loads a validated JSON **config** + **data** file and
renders an activity with a locally bundled copy of Plotly.js.

> **Status (WP02):** only the developer smoke activity (`runtime-smoke`) exists.
> It proves the infrastructure end to end. The ABIDE histogram / missing-data
> retention activities are later work.

## Prerequisites

- **Node** ≥ 20.19 (`< 25`). Local development has used Node 24; CI will be
  pinned to Node 22 in a later WP. The supported range is declared in
  `package.json` `engines`.
- npm (ships with Node). Install exact locked versions with `npm ci`.
- For end-to-end tests only: the project-managed Chromium, installed with
  `npx playwright install chromium`. No system browser is used.

## Commands

| Command | What it does |
|---|---|
| `npm ci` | Install exact locked dependencies. |
| `npm run typecheck` | `tsc --noEmit`, strict. |
| `npm run test:unit` | Vitest unit tests (`tests/*.test.ts`): config + URL validation. |
| `npm test` | typecheck + unit tests. |
| `npm run build` | typecheck, then `vite build` → `../book/_static/widgets/app/`. |
| `npm run serve:static` | Serve `book/_static/widgets/` over HTTP on `:4173` for manual checks. |
| `npm run test:e2e` | Builds first (`pretest:e2e`), then runs Playwright/Chromium against the built static files. |

Manual preview after a build:

```bash
npm run build
npm run serve:static
# open http://localhost:4173/app/index.html?config=../configs/runtime_smoke.json
# subpath check: http://localhost:4173/ml-neuro-tutorials/app/index.html?config=../configs/runtime_smoke.json
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
