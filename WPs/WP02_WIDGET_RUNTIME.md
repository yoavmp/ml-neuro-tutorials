# WP02 — Build and verify the reusable widget runtime

## Objective

Fix the notebook cell-type error that blocks reliable builds, then create a reusable, locally bundled browser runtime that can load validated activity configurations and data beneath the GitHub Pages repository subpath. Prove the runtime with a test-only Plotly smoke activity. Do not implement the ABIDE histogram or retention activity yet.

## Decisions already made

- Keep the existing Colab launch option.
- Published embedded activities will be browser-native and kernel-free.
- Bundle Plotly locally; no CDN at viewer runtime.
- Do not export participant identifiers.
- Do not remove the old `ipywidgets`, Voici, JupyterLite configuration, or `exercise_01_widgets.ipynb` yet. They may be retired only after replacements pass end-to-end tests in later WPs.
- Use the confirmed Chapter 1 path depth `../../_static/...` later; WP02 does not add the production notebook iframe.

## Tasks

### 1. Safety checkpoint

1. Read `CLAUDE_INTERACTIVE_WIDGETS.md`, this file, `WPs/README.md`, and `WPs/reports/WP01_REPORT.md` completely.
2. Confirm the branch is `feature/reusable-interactive-widgets`.
3. Before WP02 edits, inspect the working tree and create the mandatory `checkpoint: before WP02` commit plus annotated `wp02-start` tag as specified in `CLAUDE_INTERACTIVE_WIDGETS.md`.
4. Record starting HEAD, checkpoint hash, and tag for the report.

### 2. Repair the blocking notebook cell types

1. Use a small one-purpose Python script or command built with `nbformat` to open `book/chapters/chapter_01/exercise_01.ipynb`.
2. Identify the two cells reported in WP01 that contain MyST `:::{note}` admonitions but are typed as code.
3. Convert only those cells to Markdown. Preserve their source, cell IDs, and unrelated metadata. Do not broadly rewrite or clear the notebook.
4. Validate the notebook with `nbformat` and record the old/new cell types and IDs.
5. Run the relevant Jupyter Book build far enough to confirm the original `SyntaxError` is gone. If a later independent execution error appears, diagnose and report it; do not expand scope into unrelated teaching changes.

### 3. Scaffold the frontend project

Create a maintainable project broadly matching:

```text
interactive/
  package.json
  package-lock.json
  tsconfig.json
  vite.config.ts
  src/
    main.ts
    styles.css
    config.ts
    urls.ts
    components/
      types.ts
      runtime-smoke.ts
  tests/
    config.test.ts
    urls.test.ts
  e2e/
    runtime.spec.ts
    serve-static.mjs        # only if needed for nested-path testing

book/_static/widgets/
  configs/runtime_smoke.json
  data/runtime_smoke.json
  app/                      # generated Vite output, ignored by Git
```

Requirements:

1. Use TypeScript with strict checking and Vite with `base: './'`.
2. Use a current stable Node line supported by CI; declare the supported range in `package.json`. Local Node 24 may be used if dependencies support it, but plan to pin Node 22 in GitHub Actions later.
3. Pin direct dependency versions and commit `package-lock.json`.
4. Bundle Plotly.js into the production assets. Do not reference `cdn.plot.ly`, jsDelivr, unpkg, or another runtime CDN.
5. Prefer the smallest official Plotly distribution that demonstrably supports the planned histogram, bar, and heatmap needs. If uncertain or tests show missing trace types, use the full minified distribution and report the bundle-size tradeoff.
6. Output production assets to `book/_static/widgets/app/`. Keep that generated directory ignored rather than committed.
7. Do not change the GitHub Actions deployment workflow yet; that belongs to a later integration WP.

### 4. Implement a generic validated runtime

1. Read a required `config` query parameter from the iframe/application URL.
2. Resolve the config URL against the application page URL.
3. Permit only same-origin HTTP(S) URLs. Reject cross-origin URLs, credentials in URLs, unsupported protocols, malformed paths, and missing parameters with a readable in-frame error.
4. Load and validate JSON configuration. Use explicit schema versioning and a discriminated activity type. A small runtime validation dependency such as Zod is acceptable if pinned and justified.
5. Resolve each data URL relative to the loaded config file URL, not accidentally relative to the browser page.
6. Validate loaded data before rendering.
7. Dispatch via a typed component registry rather than `if` chains scattered through the code.
8. Provide accessible loading, success, and error states. Never use `eval`, executable JSON, or untrusted HTML insertion.
9. Keep plotting/calculation logic separate from configuration/URL/DOM logic so future components can be unit-tested.

### 5. Add a test-only Plotly smoke activity

Create a `runtime-smoke` component and fixture config/data whose sole purpose is proving the infrastructure. It should:

1. Render a small Plotly chart from fixture JSON.
2. Include a clearly labelled button or select control that changes the plotted values.
3. Redraw the graph with `Plotly.react()` or an equivalent full redraw.
4. Update a machine-testable render/version attribute while also changing the actual Plotly SVG/canvas state.
5. Be clearly marked as a developer smoke test, not course content.

Do not implement histogram binning, ABIDE data export, variable selection, or missing-data retention in WP02.

### 6. Tests

Add and run:

1. TypeScript type checking.
2. Unit tests for config validation and URL handling, including rejection of cross-origin, credentialed, unsupported-protocol, missing, and malformed cases.
3. A production Vite build.
4. Playwright with Chromium. Installing the project-managed Chromium binary is authorized. Do not assume a system browser.
5. End-to-end tests that serve the built static files over HTTP and verify:
   - the smoke page loads successfully;
   - Plotly produces a graph;
   - using the control changes both the render/version marker and the actual plot SVG/canvas state;
   - malformed or cross-origin config URLs show the error panel;
   - all viewer-runtime requests are same-origin and no CDN/kernel/WebSocket request occurs;
   - assets work at a root URL and at a simulated `/ml-neuro-tutorials/` project subpath.
6. Re-run `jupyter-book build book` after the notebook cell fix. Record exit status and warnings. Confirm specifically that the original admonition `SyntaxError` is absent.

If Playwright/Chromium installation is blocked by the environment, report `NOT TESTED` with the exact blocker; do not substitute text-only HTML inspection and call it equivalent.

### 7. Documentation

Add a concise `interactive/README.md` covering:

- prerequisites;
- install, test, build, and local HTTP preview commands;
- source versus generated files;
- config and data URL resolution;
- why `file://` is unsupported;
- how the component registry will support later activities;
- the fact that `runtime-smoke` is a test fixture, not student material.

### 8. Finish and stop

1. Confirm generated output and test artifacts are not staged.
2. Commit source changes with `WP02: add and verify reusable widget runtime`.
3. Generate `WPs/reports/WP02_REPORT.md` using the required template, including dependency versions and bundle size.
4. Commit the report separately with `WP02 report: document results`.
5. Print the required terminal summary and stop. Do not create or begin WP03.

## Acceptance criteria

- The mandatory WP02 checkpoint commit and annotated tag exist.
- Only the two erroneous admonition cells are converted from code to Markdown, using `nbformat`.
- The original notebook `SyntaxError` no longer occurs.
- `npm ci`, type checking, unit tests, and production build pass.
- Plotly is present in locally built assets and the smoke page makes no runtime CDN request.
- Runtime configuration/data validation and same-origin restrictions are tested.
- Playwright proves that the control changes the actual rendered plot at both root and simulated project-subpath URLs.
- The Jupyter Book build is rerun and accurately reported.
- Generated output is ignored and absent from commits.
- `interactive/README.md` documents author/developer use.
- `WPs/reports/WP02_REPORT.md` reports outcome, tests, deviations, risks, commits, and recommended WP03 scope.
- Working tree is clean after separate implementation and report commits.
- No ABIDE histogram, retention component, production notebook iframe, deployment-workflow edit, or WP03 file is created.

Stop after WP02 regardless of outcome.

