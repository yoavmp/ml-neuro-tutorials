# WP03 — Production ABIDE histogram activity

## Objective

Implement the first real course activity on the reusable runtime: an ABIDE-II histogram with a variable selector and exact bin-count control. Export and commit a small identifier-free static data artifact, embed the activity in the EDA notebook, integrate frontend building/testing into GitHub Actions, and prove the interaction on the final built Jupyter Book page.

Do not implement the missing-data retention activity in this WP.

## Fixed decisions

- Keep the Colab launch option.
- Use the browser-native TypeScript runtime from WP02.
- Plotly must remain locally bundled; no CDN or Python kernel at viewer runtime.
- The activity data must contain no `SUB_ID` or other participant identifier.
- Keep the old retention widget untouched until its replacement is implemented.
- Replace the obsolete histogram experiment only after the new activity passes locally.
- Do not perform a major Vite/Vitest toolchain upgrade inside this feature WP. Require `npm audit --omit=dev` to pass and carry the dev-only advisories forward for a separate maintenance WP.

## Tasks

### 1. Mandatory checkpoint and baseline

1. Read `CLAUDE_INTERACTIVE_WIDGETS.md`, `WPs/README.md`, this WP, and `WPs/reports/WP02_REPORT.md` completely.
2. Confirm branch `feature/reusable-interactive-widgets`.
3. Inspect the working tree, then create the mandatory `checkpoint: before WP03` commit and annotated `wp03-start` tag before making WP changes.
4. From `interactive/`, run the clean baseline sequence:

   ```bash
   npm ci
   npm run typecheck
   npm run test:unit
   npm run build
   npx playwright test
   ```

5. If the WP02 baseline no longer passes, diagnose it before adding the histogram and report the result.

### 2. Deterministic ABIDE histogram data export

Create `scripts/export_widget_data.py` and appropriate tests.

Requirements:

1. Treat the existing ABIDE-II phenotypic CSV identified in WP01 as the provenance source and `book/config/eda_phenotype_columns.json` as the allowed-column authority. Never fetch this repository's column config from GitHub; read the local file.
2. Pin and report the exact source URL and SHA-256 hash of the downloaded CSV bytes. If the upstream bytes differ from the pinned hash, fail loudly rather than silently producing changed teaching data.
3. Support two explicit modes:
   - a refresh/export mode that downloads/verifies the source and deterministically writes the static artifact;
   - an offline validation/check mode that validates the committed artifact without network access.
4. Commit the small output at `book/_static/widgets/data/abide_histogram.json`. Do not commit the complete source CSV unless there is a compelling documented reason and the file size/licensing are checked first.
5. Export one array per variable or another compact deterministic representation supported by the runtime. Preserve row count/alignment if it helps later activities, but export no identifiers.
6. Include only these initial variables unless the actual source/legend makes one unavailable:
   - `AGE_AT_SCAN`
   - `FIQ`
   - `VIQ`
   - `PIQ`
   - `ADOS_G_TOTAL`
   - `ADOS_2_TOTAL`
   - `SRS_TOTAL_RAW`
   - `SCQ_TOTAL`
7. If a named field differs in the curated config/source, use the documented canonical field and state the substitution in the report. Do not silently substitute.
8. Encode missing observations as JSON `null`; reject NaN/Infinity tokens. Numeric observations must be JSON numbers.
9. Include schema version, source provenance/hash, row count, and variable metadata. Omit nondeterministic generation timestamps.
10. Make output byte-for-byte deterministic: stable ordering, stable JSON formatting, trailing newline, and no machine-specific paths.
11. Validate that every exported field is in the local curated-column list, arrays match the declared row count, values are number-or-null, and no identifier-like keys are present.
12. Add Python standard-library `unittest` tests using small local fixtures. Tests must not require network access.

### 3. Histogram configuration and schema

Add `book/_static/widgets/configs/eda_histogram.json` and extend the versioned discriminated configuration schema with an `eda-histogram` activity type.

The configuration, not the component, must define:

- title and concise instructions;
- data URL;
- available variable names and readable labels;
- default variable;
- minimum, maximum, step, and default bin count;
- axis labels where needed;
- student reflection prompts.

Use a default of `AGE_AT_SCAN` and approximately 25 bins, with an allowed range suitable for teaching (for example 5–60). Validate that defaults belong to their allowed sets/ranges.

### 4. Pure histogram calculation

Create a DOM-independent calculation module with unit tests.

Requirements:

1. Accept number-or-null observations and an integer requested bin count.
2. Separate missing values and reject non-finite numeric inputs if they somehow reach the function.
3. For nonconstant data, return exactly the requested number of equal-width bins, with the maximum included in the final bin.
4. Return bin edges, centers or labels, counts, available N, missing N, minimum, and maximum.
5. Counts must sum to available N.
6. Define and document deterministic behavior for empty/all-missing and constant-valued variables. Constant data must render meaningfully and must not divide by zero.
7. Test ordinary values, boundary values, negative/decimal values, missingness, requested-bin validation, all-missing input, constant input, and count conservation.

Plot the returned bins as a Plotly **bar trace** rather than delegating bin selection to a histogram trace. This ensures that the number of bins and counts are exactly those produced by the tested calculation.

### 5. Production histogram component

Implement and register `eda-histogram`:

1. Validate the loaded ABIDE artifact with a component-owned Zod schema.
2. Render an explicitly labelled variable selector.
3. Render an explicitly labelled bin slider/input with its current value visible.
4. Show available N and missing N for the selected variable.
5. Recalculate and redraw with `Plotly.react()` whenever either control changes.
6. Update machine-testable state attributes such as active variable, active bin count, and render count.
7. Include a concise, professional student prompt: predict what changing bin count will do before moving it, then compare variables and relate differing sample sizes to missingness.
8. Provide readable empty-data and validation errors.
9. Ensure keyboard use, responsive layout, and sensible light/dark display.
10. Do not include participant-level hover text. Hover may show bin range and count only.

### 6. Notebook integration

Edit `book/chapters/chapter_01/exercise_01.ipynb` with `nbformat`.

1. Identify the existing histogram experiment by content rather than relying only on cell index.
2. Replace its obsolete Plotly/CDN or `ipywidgets` histogram material with concise Markdown instructions and an iframe loading:

   ```text
   ../../_static/widgets/app/index.html?config=../configs/eda_histogram.json
   ```

   Confirm URL resolution empirically in the built site.
3. Give the iframe an informative title, `loading="lazy"`, full width, no visible border, and sufficient fixed height. Dynamic height is optional and out of scope.
4. Preserve unrelated teaching content, retention-widget material, cell IDs where practical, and all unrelated metadata/tags.
5. Remove any histogram-only CDN dependency/import/output made obsolete by the replacement. Do not remove dependencies or cells still used elsewhere.
6. Do not add raw ABIDE logistics to the student-facing notebook.

### 7. GitHub Actions and build guard

Update the existing deployment workflow without changing its deployment provider or target branch.

Before `jupyter-book build book`, it must:

1. Set up Node 22 with npm caching based on `interactive/package-lock.json`.
2. Run `npm ci` in `interactive/`.
3. Run type checking and unit tests.
4. Run `npm audit --omit=dev` and fail if production dependencies are vulnerable.
5. Build the Vite application so `book/_static/widgets/app/` exists before Sphinx copies static assets.
6. Run the exporter in offline validation mode against the committed ABIDE artifact.
7. Install Playwright Chromium and its Linux dependencies, build the Jupyter Book, serve `book/_build/html`, and run the relevant browser tests against the built Chapter 1 page.
8. Add a robust post-build check that fails CI if any notebook execution-error report (`*.err.log`) exists, since Jupyter Book itself may return exit 0.

Avoid duplicating dependency installation already present in the workflow. Keep commands readable and pin action major versions consistent with the existing workflow unless a security/compatibility reason requires change.

### 8. End-to-end verification

Extend Playwright tests to exercise the final built page, not just the standalone app.

Verify:

1. The iframe loads under the actual Chapter 1 route.
2. The config and data return HTTP 200.
3. Plotly renders inside the iframe.
4. Changing variable modifies active-variable state, N/missing values as applicable, and actual bar geometry.
5. Changing bin count modifies active-bin state and actual bar geometry/number of bars.
6. Browser refresh restores configuration defaults.
7. No off-origin, CDN, kernel, JupyterLite, Voici, WebSocket, or failed requests occur for the activity.
8. The activity works at the simulated `/ml-neuro-tutorials/` project subpath.
9. The iframe is usable at desktop and narrow viewport sizes.

Also run and report:

```bash
cd interactive
npm ci
npm run typecheck
npm run test:unit
npm run build
npm audit --omit=dev
npx playwright test
cd ..
.venv/bin/python -m unittest discover -s tests -p 'test_export_widget_data.py'
.venv/bin/python scripts/export_widget_data.py --check
rm -rf book/_build
.venv/bin/jupyter-book build book
```

Use the repository's actual script arguments if designed slightly differently and document them.

### 9. Documentation and completion

1. Update `interactive/README.md` with the real histogram config/data and authoring workflow.
2. Document how to refresh the pinned data intentionally and how to review/update the source hash. Do not normalize an unexpected upstream change automatically.
3. Document local preview of the final book via HTTP.
4. Confirm generated output, `node_modules`, browser binaries, reports, caches, and `book/_build` are not staged.
5. Commit implementation with `WP03: add production ABIDE histogram activity`.
6. Create `WPs/reports/WP03_REPORT.md`, including exact data counts/hashes, bundle size, test outcomes, workflow changes, deviations, and unresolved risks.
7. Commit the report with `WP03 report: document results`.
8. Print the required terminal summary and stop. Do not create or begin WP04.

## Acceptance criteria

- Mandatory WP03 checkpoint commit and annotated tag exist.
- Committed ABIDE artifact is deterministic, identifier-free, validated offline, and uses `null` for missing values.
- Histogram calculations are pure, tested, conserve counts, and create exactly the requested bins for nonconstant data.
- Variable and bin controls trigger a real Plotly redraw.
- The production iframe replaces only the obsolete histogram experiment.
- Built Chapter 1 browser tests prove the actual figure changes for both controls.
- Viewer runtime makes no CDN/kernel/off-origin requests.
- GitHub Actions builds and tests the frontend before deploying the Jupyter Book.
- CI fails on notebook execution-error reports.
- Clean install, typecheck, Python/unit tests, production build, production-dependency audit, Jupyter Book build, and Playwright tests pass.
- Generated output is not committed.
- Documentation and `WPs/reports/WP03_REPORT.md` are complete.
- Working tree is clean after separate implementation and report commits.
- No retention activity or WP04 file is created.

Stop after WP03 regardless of outcome.

