# WP22: Dark-Mode Plotly Repair

- **Date:** 2026-09-16
- **Starting commit SHA:** `0a28301ceee3c4a3a8891158a73ac0754b4b6150`
- **Intended working branch:** `fix/published-dark-mode-plots`
- **Status:** COMPLETED
- **Scope note:** This WP is local-only. It does not authorize pushing to any
  remote or deploying (no GitHub Actions trigger, no gh-pages publish). All
  work stays on the local working branch until a human explicitly requests
  otherwise in a future WP.

---

## Original instruction (verbatim)

Implement WP22: repair all interactive Plotly figures in Jupyter Book dark mode.

The published light-mode figures are correct. In dark mode, some deployed figures show light-gray plot backgrounds, black or invisible data marks, and thick gray rectangles around the axes. Local light-mode rendering is not sufficient verification.

This is a focused local implementation WP. Do not push or deploy.

### 1. Git safety

1. Run `git status --short --branch`, `git branch --show-current`, and `git rev-parse HEAD`.
2. Expected starting point:

   * branch: `main`
   * `HEAD`: `0a28301ceee3c4a3a8891158a73ac0754b4b6150`
   * local `main` synchronized with `origin/main`
3. Preserve all existing untracked reports, including:

   * `WPs/reports/WP16_ARCHITECT_REPORT.md`
   * `WPs/reports/WP21_DEPLOYMENT_REPORT.md`, if present
4. Do not add, modify, delete, move, or commit those untracked reports.
5. If tracked changes exist, create a checkpoint commit before proceeding. Otherwise, record the starting SHA.
6. Create and work on:
   `fix/published-dark-mode-plots`

### 2. Reproduce the actual failure

Before editing, inspect the current theme and Plotly implementation.

Reproduce the problem using the built Jupyter Book served over HTTP—not only the standalone Vite development page.

Test these situations:

1. Load a notebook in light mode.
2. Switch to dark mode using the Jupyter Book color-mode control.
3. Reload the notebook while dark mode is already selected.
4. Switch dark → light → dark again.
5. Inspect a histogram and an observed-versus-predicted scatterplot.

The important distinction is:

* The parent Jupyter Book stores its active theme on its root element, including attributes such as `data-theme` and/or `data-mode`.
* The interactive app runs inside a same-origin iframe.
* Browser `prefers-color-scheme` is not necessarily the same as the theme selected in Jupyter Book.
* Plotly must redraw when the selected Jupyter Book theme changes.

Document the confirmed cause in the WP22 report. Do not assume that Dark Reader or another extension is responsible unless the local reproduction proves it.

### 3. Implement one centralized theme mechanism

Create or improve one shared theme hook/provider for the interactive application. Do not implement separate theme-detection code in every chart.

The mechanism must:

1. When embedded, read the active theme from the parent Jupyter Book document.
2. Observe the parent document for subsequent `data-theme`, `data-mode`, or equivalent changes.
3. Update React state whenever the parent theme changes.
4. Cause every Plotly figure to redraw using the new theme.
5. Work when the page initially loads in dark mode.
6. Work when the user switches themes after the chart has rendered.
7. Fall back safely to `prefers-color-scheme` when the interactive app is opened directly or cannot access its parent.
8. Remove observers and media-query listeners during cleanup.
9. Use `try/catch` around parent-document access so direct or cross-origin use does not break.

A same-origin parent observer is acceptable. A parent-to-iframe `postMessage` mechanism is also acceptable if it is cleaner and fully tested. Do not rely only on `prefers-color-scheme`.

### 4. Give Plotly explicit light and dark palettes

Create one shared Plotly theme/layout helper used by every gridded interactive figure.

Explicitly define, for both themes:

* plot background;
* paper/margin background;
* font and axis-label color;
* gridline color;
* axis-line and tick color;
* legend background/text;
* annotation text;
* trace, marker, line, and histogram colors where components currently rely on browser or Plotly defaults;
* reference-line colors.

Do not leave essential colors as browser defaults.

Dark mode should have:

* a genuinely dark plot and paper background consistent with the widget card;
* visible, contrasting data marks;
* subdued but readable gridlines;
* readable labels and legends.

Light mode must remain visually equivalent to the current correct design.

Changing the theme must not change any data, metrics, selected values, or model results.

### 5. Eliminate the visible axis-drag rectangles

The gray bands and corner rectangles must never be visible.

Inspect Plotly's drag layer and determine which measures are necessary. Prefer a combination of:

* explicitly transparent `.draglayer` rectangles, scoped only inside Plotly figures;
* `stroke: none`;
* `fixedrange: true` for axes where manual axis dragging is not part of the lesson;
* `displayModeBar: false`;
* `scrollZoom: false`;
* disabling double-click axis resets or free panning when they serve no teaching purpose.

Hover information and updates made through the activity's own controls must continue to work.

Do not add a global `svg rect` rule. It could damage histogram bars, heatmap cells, legends, or other SVG graphics.

Do not apply `forced-color-adjust: none` to the entire application. That could harm accessibility in operating-system high-contrast modes. If it is genuinely needed, scope it narrowly to the Plotly visualization or drag layer and explain why in the report.

Do not add a Dark Reader lock unless Dark Reader is independently confirmed as the cause. This WP concerns the built-in Jupyter Book dark mode.

### 6. Apply the fix to every relevant activity

Inventory every interactive component that renders a Plotly or similarly gridded figure.

At minimum, inspect:

* EDA histogram;
* EDA correlation explorer;
* regression feature comparison;
* KNN A/B/C evaluation;
* KNN exploration and bias–variance figures;
* classification threshold activity;
* classification imbalance activity;
* any additional Plotly figure found during the inventory.

Use the shared theme implementation everywhere. Do not make isolated fixes only for the two screenshots.

Tables and non-plot activities should retain their current appearance.

### 7. Automated regression tests

Add focused tests that verify behavior rather than merely searching for CSS strings.

#### Unit/component tests

Test that the shared theme mechanism:

* reads an already-active parent dark theme;
* responds when the parent theme changes;
* falls back to the browser preference when no parent theme is available;
* cleans up its observers/listeners;
* supplies distinct explicit light and dark Plotly layouts.

#### Built-book browser tests

Serve the built Jupyter Book and test representative notebook pages through their actual iframes.

For at least one histogram and one scatterplot:

1. Verify light-mode rendering.
2. switch to dark mode;
3. verify that the iframe and Plotly layout become dark;
4. verify that the plot and paper backgrounds match the intended palette;
5. verify that data marks remain visible and retain their intended color;
6. verify that gridlines remain readable;
7. verify that Plotly drag-layer rectangles remain transparent;
8. reload while dark mode is active and repeat the critical assertions;
9. switch back to light mode and verify restoration.

If inexpensive, apply the computed-style assertions to every Plotly activity. Do not create fragile full-page pixel snapshots as the sole test. Small diagnostic screenshots may supplement computed-style and DOM assertions.

The test must fail against the pre-WP22 implementation if the theme-propagation race or mismatch is reproducible.

### 8. Bounded verification

Run only:

1. focused frontend unit/component tests related to theme and plots;
2. frontend typecheck;
3. one production interactive build;
4. one Jupyter Book build;
5. the focused built-book dark-mode browser tests.

Do not run the entire repository, frontend, or Playwright suite unless a focused failure proves it necessary.

For each failing gate:

* make at most one bounded correction;
* rerun only the failed focused gate once;
* if it still fails, stop and report partial success.

Do not push, deploy, monitor GitHub Actions, or repeatedly rebuild.

### 9. Preserve content and calculations

Do not change:

* notebook teaching content;
* datasets;
* participant splits;
* model parameters;
* metrics;
* interaction defaults;
* existing student questions;
* portable notebook calculations.

Only iframe integration or titles may change if technically necessary for the theme fix.

### 10. Commit and reports

Commit the implementation locally on the repair branch.

Create:

* `WPs/reports/WP22_REPORT.md`
* `WPs/reports/WP22_EXACT_CHANGELOG.md`

The report must include:

1. exact confirmed root cause;
2. why light mode worked while published dark mode failed;
3. every affected plotting component;
4. centralized theme mechanism implemented;
5. treatment of Plotly drag layers;
6. light-mode and dark-mode verification results;
7. reload-in-dark-mode result;
8. test/build commands and outcomes;
9. screenshots or computed-style evidence from before and after, if available;
10. implementation commit SHA;
11. confirmation that nothing was pushed or deployed;
12. any remaining browser-specific uncertainty.

Do not mark the WP successful merely because the standalone Vite page looks correct. Success requires the built Jupyter Book, actual iframe embedding, theme switching, and initial dark-mode reload to pass.

Finish with a short recap for Yoav. Do not start WP23.

---

## Post-implementation links

- Report: [`reports/WP22_REPORT.md`](reports/WP22_REPORT.md)
- Exact changelog: [`reports/WP22_EXACT_CHANGELOG.md`](reports/WP22_EXACT_CHANGELOG.md)
