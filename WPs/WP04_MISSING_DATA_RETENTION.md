# WP04 — ABIDE missing-data retention activity

## Objective

Implement the second real course activity: students select candidate core variables and immediately see how complete-case filtering changes the retained ABIDE sample overall and within each acquisition site. Replace the remaining kernel-dependent retention widget in the EDA notebook, remove obsolete widget/JupyterLite/Voici experiment infrastructure only after the replacement passes, and prove the activity on the final built Jupyter Book page.

Do not perform the separate Vite/Vitest major-version security upgrade in this WP.

## Fixed teaching decisions

- Default core variables: `DX_GROUP`, `AGE_AT_SCAN`, `SEX`, `FIQ`.
- Students may choose from grouped demographic, cognitive, behavioral, and scan-condition variables.
- A participant is retained only when every selected variable is non-missing.
- With no variables selected, all rows are retained and the interface must explicitly state that no completeness criterion is being applied.
- Show retained/excluded N and retained percentage overall, plus retained/total and percentage for every site.
- `SITE_ID` is allowed only as a non-personal site-grouping label. Do not export `SUB_ID` or any participant identifier.
- Keep the Colab launch option.
- Page-wide self-hosting of MathJax/Google Fonts is out of scope; the activity itself must remain same-origin and CDN/kernel-free.

## Candidate variables

Use these fields if present in the local curated-column authority and pinned source:

### Demographics and diagnosis

- `DX_GROUP`
- `AGE_AT_SCAN`
- `SEX`
- `HANDEDNESS_CATEGORY`

### Cognitive scores

- `FIQ`
- `VIQ`
- `PIQ`

### Diagnostic and behavioral measures

- `ADOS_G_TOTAL`
- `ADOS_2_TOTAL`
- `SRS_TOTAL_RAW`
- `SCQ_TOTAL`

### Medication and scan conditions

- `CURRENT_MED_STATUS`
- `EYE_STATUS_AT_SCAN`

If a field is unavailable or unsuitable according to the official coding/legend already used by the project, do not silently substitute it. Report the issue and use the closest documented curated field only if clearly justified.

## Tasks

### 1. Mandatory checkpoint and baseline

1. Read `CLAUDE_INTERACTIVE_WIDGETS.md`, `WPs/README.md`, this WP, and `WPs/reports/WP03_REPORT.md` completely.
2. Confirm branch `feature/reusable-interactive-widgets`.
3. Inspect the working tree, then create the mandatory `checkpoint: before WP04` commit and annotated `wp04-start` tag before making WP changes.
4. Run the WP03 clean baseline: `npm ci`, typecheck, all existing unit tests, Vite build, standalone Playwright, exporter offline check, Jupyter Book build, execution-error guard, and built-book Playwright.
5. If the baseline fails, diagnose before adding the retention feature.

### 2. Extend deterministic data export

Extend `scripts/export_widget_data.py` without breaking the existing histogram refresh/check workflow.

Requirements:

1. Produce and commit `book/_static/widgets/data/abide_retention.json` from the same pinned source URL and SHA-256 used for the histogram.
2. Export 1,114 aligned rows containing `SITE_ID` plus the approved candidate variables. A columnar representation is preferred.
3. Encode missing observations as JSON `null`; preserve categorical values as documented strings/numbers rather than inventing imputed values.
4. Include schema version, activity name, pinned provenance, row count, site-field metadata, and per-variable available/missing counts. Omit timestamps and local paths.
5. Maintain strict participant-identifier rejection. Add a narrowly scoped, explicit exception allowing only `SITE_ID` for this artifact because it is required for grouped retention summaries. `SUB_ID`, subject/participant IDs, names, emails, dates of birth, and arbitrary `*_ID` fields must remain rejected.
6. Validate that `SITE_ID` has no missing values, every column length equals row count, values are supported JSON primitives or null, and all candidate variables are in the local curated-column authority.
7. Preserve byte-for-byte deterministic output and offline validation. Extend the CLI cleanly—e.g. an explicit artifact selector—while retaining or documenting backward compatibility for WP03 commands.
8. Extend the Python `unittest` suite with local fixtures for strings/categories, the exact `SITE_ID` exception, rejection of participant/arbitrary IDs, null handling, alignment, metadata counts, determinism, and both artifact modes. No unit test may require network access.
9. Verify that refresh of one artifact cannot unintentionally rewrite or delete the other.

### 3. Retention configuration and schema

Add `book/_static/widgets/configs/eda_retention.json` and extend the discriminated configuration schema with `eda-retention`.

The config must define:

- title and concise instructions;
- data URL;
- site field and readable site label;
- candidate variables grouped under the four headings above;
- readable variable labels;
- default selected variables (`DX_GROUP`, `AGE_AT_SCAN`, `SEX`, `FIQ`);
- chart metric/default (`retained percentage`, with N/total visible);
- professional reflection prompts.

Validate uniqueness, group membership, default membership, nonempty labels, and that the site field is not also a selectable variable.

### 4. Pure complete-case retention calculation

Create a DOM/Plotly-free calculation module and comprehensive unit tests.

Inputs:

- aligned columnar values;
- site labels;
- selected variable names.

Outputs:

- total, retained, excluded, and retained percentage overall;
- per-site total, retained, excluded, and retained percentage;
- selected variables;
- a flag/message for no selection.

Rules:

1. Missing means JSON `null`. Do not treat valid `0`, `false`, or empty documented category strings as missing unless the source/export schema explicitly defines them as missing before serialization.
2. Retain a row only when all selected fields are non-null.
3. With no selection, retain every row and flag that no completeness criterion is applied.
4. Preserve a deterministic site order. Prefer first appearance or explicitly documented alphabetical order; test it.
5. Reject missing requested columns, unequal column lengths, missing site labels, and duplicate selected variables.
6. Test one variable, multiple variables, no selection, no missingness, all excluded, site-specific missingness, valid zeros/false/strings, deterministic ordering, and consistency/conservation (`retained + excluded = total`) overall and per site.
7. Independently cross-check shipped default and selected-variable results against pandas in Python or equivalent trusted calculations; report exact expected values.

### 5. Retention component

Implement and register `eda-retention`:

1. Validate the artifact with a component-owned Zod schema kept separate from Plotly/DOM code where practical.
2. Render accessible grouped checkboxes, not a difficult platform-dependent multi-select. Every checkbox must have a visible label.
3. Provide `Use suggested core set`, `Select all`, and `Clear` controls.
4. Clearly list/count selected variables.
5. Show overall retained N/total, percentage, and excluded N.
6. Render a Plotly bar chart of retained percentage by site; hover and/or annotations must show retained N / site total.
7. Recalculate and redraw with `Plotly.react()` on every selection change.
8. Store machine-testable selected-variable, retained-N, retained-percent, site-count, and render-count state attributes.
9. When nothing is selected, explicitly display: all participants are retained because no completeness criterion is currently applied.
10. Include a warning/visual cue when a selection retains less than 50% overall, without prescribing that 50% is a universal scientific cutoff.
11. Include prompts asking students to compare the suggested core set with broader behavioral sets, identify sites disproportionately affected, and explain why complete-case filtering may change sample composition.
12. Use only aggregate hover information. Do not expose participant rows or identifiers.
13. Ensure keyboard operation, narrow-screen usability, and light/dark rendering.

### 6. Notebook integration and legacy cleanup

Edit notebooks with `nbformat`, locating target cells by content rather than index alone.

1. In `book/chapters/chapter_01/exercise_01.ipynb`, replace only the remaining `ipywidgets` retention interface and its kernel-only note with concise teaching Markdown and an iframe loading:

   ```text
   ../../_static/widgets/app/index.html?config=../configs/eda_retention.json
   ```

2. Place the activity immediately after the site-missingness heatmap/explanation where students are asked to choose core variables.
3. Preserve unrelated code/prose, the working histogram iframe, cell IDs where practical, tags, and metadata.
4. After the new retention activity passes standalone and built-page tests:
   - remove the orphan experimental `book/chapters/chapter_01/exercise_01_widgets.ipynb`;
   - remove `ipywidgets`, `jupyterlite-sphinx`, `jupyterlite-pyodide-kernel`, `voici`, and related dependencies only if repository-wide search confirms they are no longer used;
   - remove the stale `jupyterlite_sphinx`/Voici/JupyterLite configuration from `book/_config.yml` only if no remaining feature depends on it;
   - remove notebook-level stored widget state only if no widget view remains;
   - keep the Colab launch button/configuration;
   - do not remove ordinary static Matplotlib/Seaborn notebook figures.
5. Build and confirm that the previous orphan-notebook and widget-manager warnings/requests are removed or explain precisely why any remain.

### 7. Build, CI, and browser tests

Extend—not duplicate—the WP03 workflow and tests.

1. CI must offline-check both committed ABIDE artifacts.
2. Existing typecheck, unit, production audit, Vite build, notebook error guard, and Playwright steps must remain.
3. Standalone browser tests must verify:
   - default selected variables;
   - exact expected overall retention;
   - checkbox changes alter retained N and actual bar geometry;
   - suggested/select-all/clear controls;
   - no-selection behavior;
   - site denominators/retained counts;
   - low-retention warning;
   - refresh restores defaults;
   - no failed, off-origin, CDN, kernel, or WebSocket request;
   - narrow viewport usability.
4. Built-book browser tests must enter the retention iframe on the real Chapter 1 page and verify actual selection-driven text and Plotly geometry changes under the simulated `/ml-neuro-tutorials/` subpath.
5. Keep the existing histogram tests passing unchanged.
6. Inspect page-level network traffic after legacy cleanup. Distinguish activity traffic from unrelated theme resources. Confirm no JupyterLite/Voici/widget-manager/kernel request remains due to the removed experiment.

### 8. Verification commands

Run and report at minimum:

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
find book/_build -name '*.err.log' -print
cd interactive
npm run test:e2e:book
```

Adapt the exporter command only if the new explicit artifact interface requires it, and document all exact invocations.

### 9. Documentation and completion

1. Update `interactive/README.md` with the retention component, config, artifact, testing, and authoring workflow.
2. Explain why `SITE_ID` is included while participant identifiers are forbidden.
3. Document exact default retention results as a regression reference.
4. Record any remaining page-level CDN/theme dependencies without expanding scope into self-hosting them.
5. Confirm generated output and caches are absent from staged changes.
6. Commit implementation with `WP04: add ABIDE missing-data retention activity`.
7. Create and commit `WPs/reports/WP04_REPORT.md` with `WP04 report: document results`.
8. Print the required terminal summary and stop. Do not create or begin WP05.

## Acceptance criteria

- Mandatory WP04 checkpoint commit and annotated tag exist.
- Retention artifact is deterministic, offline-validated, and contains `SITE_ID` but no participant identifier.
- Exact `SITE_ID` exception is narrow and tested; `SUB_ID` and arbitrary IDs remain rejected.
- Complete-case calculations are pure, tested, and independently cross-checked.
- Default selection is `DX_GROUP`, `AGE_AT_SCAN`, `SEX`, `FIQ`.
- Checkboxes and all three preset controls update summaries and actual Plotly geometry.
- No-selection and low-retention states are clear and pedagogically accurate.
- Retention iframe works and changes visibly on the final built Chapter 1 page.
- Histogram activity and tests remain passing.
- Obsolete `ipywidgets`/JupyterLite/Voici experiment files, configuration, and dependencies are removed only after replacement tests pass; Colab remains.
- CI validates both artifacts and runs the full frontend/book test path before deployment.
- Activity requests are same-origin and kernel/CDN-free.
- Typecheck, all unit tests, production dependency audit, build, Jupyter Book, error guard, and standalone/built-book Playwright pass.
- Documentation and WP04 report are complete.
- Working tree is clean after separate implementation and report commits.
- No WP05 file is created.

Stop after WP04 regardless of outcome.

