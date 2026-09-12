# WP16 — Repair Plotly axes, backgrounds, spacing, and production parity

## Objective

Execute this work package in:

`/Users/crazyjoe/Projects/ml-neuro-tutorials`

The deployed interactive plots do not currently match the clean local appearance. The defect is reproducible on the live site, especially in Exercise 2's feature-set comparison:

- the Plotly x-axis title extends below the plot container and overlaps the expandable ROI-summary row beneath it;
- measured on the deployed activity, the overlap is approximately 15 px;
- Plotly's axis drag/pan regions remain enabled even though the intended lesson interaction occurs through the activity controls;
- the comparison panels use a lavender-gray `--surface-alt` background (`#f4f4f9`) around a white plot, which looks inconsistent with the surrounding notebook;
- plots are relatively narrow inside the Jupyter Book content column, so spacing must be robust at the real deployed iframe width, not merely on the local Vite development page.

Implement one shared, project-wide Plotly presentation policy rather than patching one graph. Preserve all mathematical results and interactive lesson controls. Then build, merge, push, deploy, and visually validate the fix on GitHub Pages.

Do not start WP17. End with `WP16_REPORT.md` and `WP16_EXACT_CHANGELOG.md`.

---

## 0. Save the current state before changing anything

1. `cd /Users/crazyjoe/Projects/ml-neuro-tutorials`
2. Record:
   - `git status --short --branch`
   - `git branch --show-current`
   - `git rev-parse HEAD`
   - `git log -3 --oneline`
   - `git remote -v`
3. Confirm local `main`, `origin/main`, and the deployed revision correspond to the reported WP15 final SHA:
   - `92cf7e0152338faf07e5a5e1da6614d9f8645441`
4. The starting tree must be clean. If it is not, preserve and report unexpected changes; do not discard them.
5. Create an annotated tag `wp16-start` at the verified starting SHA. If the tag name exists, use a documented suffix.
6. Create a focused branch from that exact state, preferably:
   - `fix/interactive-plot-visuals`
7. Add this WP file under `WPs/` and commit it before implementation, e.g.:
   - `checkpoint: begin WP16 interactive plot visual repair`

Never use `git reset --hard`, `git clean`, destructive checkout, rebase of published history, force-push, or history rewriting.

---

## 1. Reproduce and inventory before editing

Inspect every production Plotly call site and every CSS rule that styles plot containers/panels. Do not assume the problem is limited to Exercise 2.

At minimum inventory:

- Exercise 1 histogram activity;
- Exercise 1 missingness/retention activity;
- Exercise 2 feature-set comparison;
- Exercise 3 honest/resubstitution/leakage comparison;
- Exercise 3 k explorer, including its prediction and bias/variance-related plots;
- any shared Plotly layout/config helper already present;
- `.widget-plot`, `.widget-compare-grid`, `.widget-compare-panel`, and any `--surface-alt` use;
- iframe dimensions declared in canonical notebooks;
- the production Vite bundle and Jupyter Book custom CSS/JS integration.

Capture baseline screenshots and DOM geometry from a **production build served locally**, at minimum at:

- the real deployed content width: iframe approximately 742 px;
- a wider desktop iframe;
- a narrow/mobile iframe around 390 px.

For Exercise 2, measure and record:

- plot container bounds;
- x-axis and y-axis title bounds;
- the following ROI-summary `<details>` bounds;
- legend bounds;
- whether any title/legend overlaps the next element or leaves its container;
- Plotly axis `fixedrange`, `dragmode`, modebar, scroll-zoom, and double-click state;
- panel, paper, and plot background colors.

Reproduce the currently observed Exercise 2 x-title/details overlap in an automated regression test before fixing it where practical. The final tests must prove the overlap is gone; screenshot-only review is insufficient.

---

## 2. Create one shared Plotly presentation policy

### 2.1 Shared helper

Create or consolidate a single reusable TypeScript helper used by all activity Plotly charts. It should supply shared defaults for layout, axes, font, background, grid lines, margins, responsiveness, and Plotly runtime configuration.

Do not duplicate the same fix across component files. Activity-specific titles, ranges, traces, and legends may override only what they genuinely need.

The helper must merge nested `xaxis`, `yaxis`, `margin`, and legend options safely. A shallow merge that silently erases shared axis defaults is not acceptable.

### 2.2 Preserve the intended interaction model

Students should interact through the activity controls—sliders, number inputs, selectors, tabs, and checkboxes—not by accidentally dragging axes.

For ordinary lesson plots:

- set `xaxis.fixedrange = true` and `yaxis.fixedrange = true`;
- disable plot dragging/panning/box zoom (`dragmode = false`, or the correct Plotly equivalent established by testing);
- disable scroll zoom;
- disable double-click axis reset;
- hide the Plotly modebar;
- preserve hover tooltips and externally triggered re-rendering when lesson controls change;
- preserve keyboard accessibility of all lesson controls.

Do **not** use `staticPlot: true` if it removes useful hover information. If a particular graph truly needs native plot zoom/pan, document the exception and make the visual controls non-obstructive; do not silently apply an exception.

Verify through DOM/runtime state that axis drag handles no longer respond and the cursor does not become an axis-resize cursor over the title/tick regions.

### 2.3 Clean, consistent color treatment

Use a clean white or theme-matching surface throughout the interactive figures:

- comparison-card background must match the surrounding activity/page background instead of `#f4f4f9`;
- Plotly `paper_bgcolor` and `plot_bgcolor` must match that surface or be transparently composed without exposing a gray mismatch;
- retain a subtle border or separation between comparison panels if useful, but do not use a filled gray/lavender card merely to distinguish them;
- use one subtle, consistent grid-line color;
- maintain readable text and contrast;
- controls should remain visually distinct and accessible.

Do not globally remove `--surface-alt` if it is still useful for tables, form controls, warnings, or selected states. Scope the background correction to plot comparison panels and relevant plot wrappers.

Inspect both the Jupyter Book default light presentation and the app's supported theme behavior. Do not introduce unreadable dark-mode text or a white-on-white control state. If the iframe does not currently receive the parent theme, keep this WP focused on a polished, internally consistent light activity rather than adding an unrequested theme-communication system.

### 2.4 Axis titles, legends, and spacing

The final layout must guarantee that:

- x-axis titles remain fully visible;
- y-axis titles remain fully visible, including long titles such as predicted/observed age descriptions;
- titles never overlap a following `<details>`, caption, metric, reflection, or neighboring chart;
- legends remain inside their intended plot/card region and do not cover data or titles;
- tick labels are not clipped;
- changing a selector or `k` value does not reintroduce the overlap;
- resizing the page/sidebar does not reintroduce it.

Use Plotly `automargin` plus explicit minimum margins where necessary. Also give the plot wrapper sufficient block-flow space below the SVG; do not rely solely on an SVG title being painted outside a fixed-height container. Prefer a shared CSS spacing rule to activity-specific spacer elements.

If a plot needs a slightly larger minimum height, use a small responsive height policy. Avoid excessive empty space.

### 2.5 Responsive resizing

Ensure every chart calls Plotly's responsive resize behavior when its iframe/container width changes. Use the existing Plotly responsive mechanism or a shared `ResizeObserver` if necessary.

Keep side-by-side comparisons where they remain readable. Stack panels only at a breakpoint where two columns genuinely cease to be usable; do not make desktop comparison unnecessarily long. Test the actual approximately 742 px iframe width with the Jupyter Book sidebar open.

Do not add an internal iframe scrollbar solely as a consequence of this repair. If stacking changes content height, update the existing embedding-height mechanism safely and consistently rather than clipping content. Avoid a large blank region at wider widths.

---

## 3. Component-specific acceptance requirements

### Exercise 1

- Histogram remains responsive to variable and bin controls.
- Missingness/retention plots retain their labels and heatmap readability.
- No axis-title overlap, gray plot surround, modebar, or axis dragging.

### Exercise 2

- Both feature-set panels remain easy to compare.
- The x-axis title `Observed Age at scan` and both y-axis titles are completely visible.
- The ROI-summary disclosure begins below the plot/title with a visible gap—target at least 12 CSS px.
- No title/disclosure overlap at 742 px, wide desktop, or 390 px.
- Changing measure and ROI bundle redraws the figure without altering spacing or backgrounds.

### Exercise 3: A/B/C comparison

- All three observed-versus-predicted plots use the same clean styling and axis limits.
- The perfect-prediction legend stays visible and does not crowd the axes.
- Changing `k` updates plots and metrics exactly as before.
- `k=1` still yields the expected perfect B/C result.

### Exercise 3: k explorer

- Prediction, error-curve, training-sample, variance-proxy, and bias-like plots all use the shared styling.
- Training-sample tabs and numeric/slider k controls remain synchronized.
- Titles, calibration labels, and identity-line legends remain visible at all tested sizes.

---

## 4. Automated visual/layout regression tests

Extend the committed Playwright suites with geometry and styling assertions, not only “plot exists.” At minimum assert:

1. every relevant Plotly chart has a nonzero visible bounding box;
2. x/y titles are visible and not clipped;
3. Exercise 2's x-title bottom plus a minimum clearance is above the ROI-summary top;
4. plot/card/paper backgrounds match the approved color policy;
5. modebars are absent;
6. x/y axes are fixed and plot drag/scroll zoom is disabled while hover remains available;
7. control changes still alter traces/metrics;
8. no horizontal document overflow at the narrow viewport;
9. no internal iframe clipping or unexpected scrollbar at each canonical embedded height;
10. no failed requests or new console errors.

Test both the standalone production build and the built Jupyter Book. Use screenshots for human review at the real Jupyter Book width, but keep deterministic DOM geometry assertions as the regression guard.

Do not create fragile pixel-perfect golden images unless the project already has a stable screenshot-baseline workflow. Prefer semantic color/geometry tests.

---

## 5. Full local validation

Run the repository's actual commands discovered from the current project. At minimum:

- frontend typecheck;
- frontend unit tests;
- frontend production build;
- Python unit tests;
- every generated-data `--check` command;
- portable-notebook freshness checks;
- a clean Jupyter Book build;
- standalone Playwright suite;
- built-book Playwright suite at desktop and narrow widths;
- two consecutive clean builds to verify deterministic output;
- console/network-error scan;
- visual screenshots of each activity from the production build.

The numerical assets and notebook outputs should not need regeneration for a presentation-only change. If any generated data or notebook content changes, explain why and verify that the underlying values remain identical.

The two known Jupyter Book warnings may remain only if unchanged:

- missing `logo.png`;
- `book/README.md` not included in a toctree.

The existing Plotly/Vite chunk-size advisory may remain if unchanged. New warnings or failures are not acceptable.

---

## 6. Merge, push, deploy, and verify production

After the complete local gate passes:

1. Commit the implementation on `fix/interactive-plot-visuals`.
2. Fetch `origin` and inspect divergence.
3. Switch to `main` and update with `git pull --ff-only origin main`.
4. Merge the fix branch with an ordinary `--no-ff` merge.
5. Run a post-merge production build, clean Jupyter Book build, and representative built-book visual tests on `main`.
6. Push `main` normally. Never force-push.
7. Monitor the existing GitHub Pages workflow to terminal success.
8. Hard-refresh and test the live production pages:
   - Exercise 1 EDA;
   - Exercise 2 Regression;
   - Exercise 3 KNN and bias–variance.
9. Run the geometry/style Playwright checks against the live site, not just localhost.
10. Visually inspect production screenshots at the real iframe width.

Do not report deployment success merely because `git push` succeeded. Confirm the deployed revision corresponds to the final pushed `main` commit.

If authentication, remote divergence, merge conflicts, required-test failures, or deployment failure prevent safe completion, stop and report rather than forcing a workaround.

---

## 7. Reports

At the end create:

- `WPs/reports/WP16_REPORT.md`
- `WPs/reports/WP16_EXACT_CHANGELOG.md`

The report must include:

- success/failure;
- starting SHA/tag/branch and final implementation/merge/report/main SHAs;
- the root cause of the title overlap and gray background;
- all Plotly call sites audited;
- the shared layout/config/CSS changes;
- before/after geometry for Exercise 2, including the prior overlap and final clearance;
- before/after computed colors;
- axis dragging, hover, modebar, responsiveness, and accessibility behavior;
- desktop, 742 px, and 390 px results;
- complete test commands and pass counts;
- build warnings and whether they are pre-existing;
- deployment workflow result;
- exact live URLs and live visual/interaction checks;
- every deviation or item requiring Yoav's attention.

Commit and push the report files on `main`, wait for the resulting Pages workflow if one is triggered, and repeat a concise production smoke check. End with the final `main` SHA, clean status, live URLs, and any attention item.

Do not create WP17.

---

## 8. Non-negotiable constraints

- Do not change regression/KNN mathematics, splits, features, scores, or binary data.
- Do not remove the lesson controls or their functionality.
- Keep hover information unless a documented plot-specific reason prevents it.
- Disable accidental axis manipulation for ordinary lesson plots.
- Use one shared Plotly policy, not repeated patches.
- No title, legend, disclosure, or neighboring-element overlap.
- No mismatched gray/lavender comparison background.
- No backend, CDN, service worker, or Git LFS dependency.
- No destructive Git commands or force-push.
- Do not deploy with failing required tests.
- Do not change repository visibility.
- Do not start the next WP.

