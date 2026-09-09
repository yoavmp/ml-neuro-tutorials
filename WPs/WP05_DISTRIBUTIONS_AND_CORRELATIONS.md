# WP05 — Complete distributions and feature correlations

## Objective

Complete the EDA notebook section that currently stops after the interactive histogram. Build a concise, professional teaching sequence covering univariate distributions, comparisons across groups, outliers/range checks, numeric correlations, pairwise sample size, and mixed-type associations. Add a browser-native correlation explorer using the established runtime. The result must work for a guided tutorial and independent self-learning.

The section should emphasize reasoning and interpretation rather than passive plot scrolling. Do not turn it into an inferential-statistics chapter or a catalogue of plotting commands.

## Scope and pacing

- Continue from the existing histogram; do not duplicate its introduction.
- Target roughly 30–40 minutes of teaching after the preceding missing-data material.
- Prefer approximately 15–22 focused new notebook cells and no more than five new static figure outputs, excluding the interactive explorer.
- Every major subsection needs a short prediction or interpretation question.
- Self-learning answers must be available in correctly formed MyST dropdown/admonition Markdown or appropriately tagged solution cells—not literal `hide-cell` text.
- Preserve all earlier EDA sections, both working interactive activities, and the Colab button.

## 1. Mandatory checkpoint and baseline

1. Read `CLAUDE_INTERACTIVE_WIDGETS.md`, `WPs/README.md`, this WP, and `WPs/reports/WP04_REPORT.md` completely.
2. Confirm branch `feature/reusable-interactive-widgets`.
3. Inspect the working tree and create the mandatory `checkpoint: before WP05` commit and annotated `wp05-start` tag before WP changes.
4. Run the complete WP04 baseline: clean npm install, typecheck, unit tests, Vite build, production-dependency audit, Python exporter tests/check, Jupyter Book build, error-log guard, standalone Playwright, and built-book Playwright.
5. Do not continue until regressions are understood and reported.

## 2. Inspect the real ABIDE data before authoring examples

Use the pinned ABIDE-II source and local curated-column list. Perform a reproducible exploratory inspection in a temporary script or notebook that is not committed unless it becomes a generally useful test/helper.

Inspect and report:

1. distributions, ranges, unique counts, missing N, and suspicious/extreme values for all curated numeric variables;
2. overall counts/proportions for `DX_GROUP`, `SEX`, and other categorical variables used in the section;
3. diagnosis composition by `SITE_ID`;
4. Pearson and Spearman pairwise correlations plus pairwise-complete N for plausible numeric variables;
5. correlations within diagnosis groups for candidate pairs;
6. whether any apparent overall association materially changes after stratifying by diagnosis or site;
7. redundancy/part–whole relationships, especially totals versus their subscales;
8. candidate examples whose interpretation is stable and pedagogically useful.

Selection rules:

- Do not simply choose the largest absolute correlations and present them as discoveries.
- Prefer at least one domain-intuitive relationship, one relationship illustrating differing pairwise N, and one weak or group-sensitive relationship.
- Explicitly identify mathematical part–whole correlations, such as a total score correlated with one of its component subscales; do not present these as independent biological findings.
- Do not force a Simpson's-paradox or confounding example. If no clear example exists, state that and use the site-by-diagnosis composition plot to teach why confounding should still be checked.
- Treat all selected relationships as exploratory/descriptive. Do not add uncorrected p-value fishing.
- Verify diagnosis/sex/category codes using the existing ABIDE legend/documentation before applying readable labels.

Include a compact verified-findings table in `WPs/reports/WP05_REPORT.md`: variables, statistic, pairwise N, overall value, stratified values where relevant, and teaching reason.

## 3. Notebook teaching structure

Inspect existing heading levels/numbering and continue them consistently. Use the following conceptual order, adapting titles to avoid duplicate headings.

### A. Reading distributions

Immediately after the existing interactive histogram:

1. Explain briefly what shape, center, spread, skew, multimodality, floor/ceiling effects, and implausible values can reveal.
2. Clarify that bin choice changes appearance but not observations—the lesson already demonstrated by the interactive histogram.
3. Add a concise numeric summary table for a small, justified set of variables using `describe()` plus available/missing N. Do not print a 39-column wall of output.
4. Add an active interpretation question using actual output.

### B. Comparing distributions across groups

1. Use one carefully chosen example, likely age or FIQ by diagnosis, after confirming it from the data.
2. Use a plot that shows distribution and sample size honestly—e.g. violin/box plus jitter or a compact histogram/facet. Avoid a bare bar chart of means.
3. Add a site-by-diagnosis normalized count/proportion display to expose multicenter composition. A heatmap or compact stacked proportion plot is appropriate.
4. Ask students which variables could confound a diagnosis comparison and why a balanced overall dataset can still be unbalanced within sites.
5. Avoid causal or clinical claims.

### C. Range checks and outliers

1. Demonstrate a transparent range/IQR flag on one variable, clearly calling observations “flagged for inspection,” not automatically erroneous.
2. Show the actual flagged rows only through non-identifying fields and relevant measurements; do not display `SUB_ID`.
3. Explain that deletion requires domain knowledge, coding verification, and sensitivity analysis.
4. Ask students what evidence they would need before correcting or removing a value.

### D. Numeric correlations and pairwise N

1. Explain Pearson versus Spearman in a compact comparison:
   - Pearson: linear association and sensitivity to extreme values;
   - Spearman: rank-based monotonic association and robustness to scale/outliers;
   - neither establishes causality.
2. Calculate a focused correlation matrix from a justified numeric subset, not every possible column.
3. Alongside it, calculate the pairwise-complete N matrix using the same variables.
4. Plot correlation and N together or sequentially so students see that cells in one correlation matrix may describe different participant subsets.
5. Use a triangular mask where helpful and keep labels readable.
6. Discuss at least one verified correlation, one part–whole/redundancy example, and one example where missingness changes N substantially.
7. Do not use significance stars or uncorrected correlation p-values.

### E. Mixed variable types

Add a short professional guide explaining that “correlation matrix” is not the universal association tool:

| Variable types | Suitable first EDA view |
|---|---|
| Numeric–numeric | Scatterplot; Pearson/Spearman |
| Numeric–categorical | Grouped distributions and summaries |
| Categorical–categorical | Contingency table; proportions; optionally Cramér's V |
| Ordered categorical | Ordered counts; rank-based method only when coding/order is defensible |

Use one small `pd.crosstab` example relevant to site, diagnosis, or sex. Cramér's V may be shown as an optional sidebar, but do not let it dominate the section.

### F. Synthesis challenge

End with a short student task:

1. choose a plausible feature pair;
2. predict direction/form before plotting;
3. check missing/pairwise N;
4. compare Pearson and Spearman;
5. check diagnosis or another justified grouping;
6. write two conclusions: what the plot supports and what it cannot establish.

Provide a dropdown checklist/model reasoning process, not a single prescribed scientific conclusion.

## 4. Static notebook code quality

1. Reuse the existing imports/dataframe and established coding style.
2. Use explicit variable lists with readable names and brief comments.
3. Keep outputs compact and deterministic.
4. Use `observed=True` where appropriate with pandas categorical groupings to avoid warnings/unobserved combinations.
5. Handle missing values explicitly for every plot/statistic.
6. Do not mutate the main `phenotypes` dataframe merely for plotting labels; use copies/mappings.
7. Ensure categorical order and labels reflect the ABIDE legend.
8. Set figure sizes, labels, titles, and accessible color choices consistently. Do not use diagnosis colors that imply “good/bad.”
9. Avoid deprecated seaborn/pandas calls and suppress no meaningful warnings.
10. Any solution code cell must use notebook metadata tags correctly and be revealable in the Jupyter Book.

## 5. Browser-native correlation explorer

Implement and register a new `eda-correlation` activity using the existing runtime.

### Reuse data where possible

Prefer reusing `book/_static/widgets/data/abide_retention.json`, which already contains aligned identifier-free values for `SITE_ID`, diagnosis, sex, age, IQ, ADOS, SRS, and SCQ fields. Create a new data artifact only if the inspected teaching examples require fields absent from it; justify any duplication and extend the deterministic exporter/tests if needed.

### Configuration

Add `book/_static/widgets/configs/eda_correlation.json`. Configuration must define:

- title and instructions;
- data URL;
- selectable numeric variables and readable labels;
- distinct default X and Y variables selected from actual pedagogically useful data;
- selectable method: Pearson or Spearman;
- grouping choices: none, diagnosis, and sex, with verified value-to-label mappings;
- axis/legend labels and reflection prompts.

Validate unique variables, valid defaults, distinct default axes, valid group fields/mappings, and nonempty labels.

### Pure calculations

Implement DOM/Plotly-free, unit-tested functions for:

1. pairwise-complete extraction from two numeric columns;
2. Pearson correlation;
3. Spearman correlation with correct average ranks for ties;
4. overall and optional group-specific N/correlation;
5. null result plus readable reason for N too small or zero variance;
6. deterministic group ordering;
7. conservation and alignment validation.

Test known correlations, tied ranks, nulls, constants, small N, invalid/nonfinite inputs, grouped results, and agreement with trusted Python/pandas/scipy calculations on fixtures and selected shipped-data cases.

### Interface and plot

1. Labelled X-variable, Y-variable, method, and grouping controls.
2. Prevent or clearly handle selecting the same variable on both axes.
3. Scatterplot of pairwise-complete observations, colored only when a grouping is selected.
4. Show overall method, coefficient, and N prominently; show group-specific coefficient/N when grouped.
5. Show missing/excluded N relevant to the selected pair.
6. Do not show participant identifiers in hover data.
7. Do not add a regression line unless its meaning is explicitly correct for the selected method. Omitting trend lines is acceptable and preferred over misleading lines.
8. Redraw with `Plotly.react()` after every meaningful control change.
9. Maintain machine-testable active-X/Y/method/group/render-count/N attributes.
10. Include concise prompts about direction, form, outliers, group structure, missingness, and the difference between association and causation.
11. Provide accessible controls, keyboard operation, responsive layout, and light/dark compatibility.

## 6. Embed the correlation explorer

Edit `book/chapters/chapter_01/exercise_01.ipynb` with `nbformat` only.

1. Place a concise introduction and iframe in the numeric-correlation subsection after students have seen the static correlation and N matrices.
2. Use the confirmed source pattern:

   ```text
   ../../_static/widgets/app/index.html?config=../configs/eda_correlation.json
   ```

3. Use an informative iframe title, lazy loading, full width, no visible border, and sufficient height.
4. Preserve all previous content, histogram/retention iframes, cell IDs where practical, metadata, and tags.
5. Do not expose implementation logistics in the student-facing notebook.

## 7. Testing and verification

Extend existing suites without weakening prior assertions.

### Unit/data tests

- configuration validation and semantic constraints;
- data schema and required configured fields;
- Pearson/Spearman including ties and edge cases;
- grouped/pairwise-complete calculations;
- selected results cross-checked against trusted Python calculations;
- all existing histogram, retention, exporter, URL, and runtime tests remain green.

### Browser tests

Standalone and built-book Playwright tests must verify:

- default X/Y/method/group and expected N/coefficient within appropriate tolerance;
- changing X or Y changes actual scatter geometry and N where expected;
- changing Pearson↔Spearman changes displayed method/coefficient for a pair where they differ;
- diagnosis/sex grouping changes traces/colors and displays group-specific N/statistics;
- same-variable handling;
- refresh restores defaults;
- no participant identifiers in hover;
- activity-frame requests are same-origin with no CDN/kernel/JupyterLite/Voici/widget-manager/WebSocket traffic;
- narrow viewport usability;
- both earlier production activities still work on the built page.

### Notebook/build checks

1. Validate the notebook with `nbformat` and verify unique cell IDs.
2. Execute a clean Jupyter Book build.
3. Fail/report if any `*.err.log` exists.
4. Inspect all new static figures for readable labels, nonempty data, and reasonable dimensions. If visual browser screenshots are available, inspect them rather than relying only on object existence.
5. Confirm all new answer dropdowns render as dropdowns rather than literal MyST text.
6. Run the full CI-equivalent command sequence documented in `interactive/README.md`.

## 8. Documentation and cleanup boundaries

1. Update `interactive/README.md` for `eda-correlation`, its config, calculations, tests, and preview URL.
2. Update the GitHub workflow only as needed so new tests/config/data are automatically covered. Do not duplicate existing steps.
3. Do not perform the Vite/Vitest major upgrade, Plotly code-splitting, MathJax self-hosting, logo/toctree cleanup, or unrelated notebook restructuring in this WP.
4. Do not add inferential tests or machine-learning models.
5. Confirm generated outputs/caches are ignored and uncommitted.

## 9. Report and stop

The report must include:

- exact inspected examples and why each was chosen;
- static plots/tables added and their teaching purpose;
- exact Pearson/Spearman values and pairwise N used in prose;
- whether a meaningful group/site-sensitive association was found;
- correlation activity defaults and shipped-data reference values;
- notebook cell count/headings added and estimated teaching time;
- all test counts/results;
- screenshots or explicit visual-inspection status;
- deviations and unresolved risks.

Then:

1. Commit with `WP05: complete distributions and feature correlations section`.
2. Create `WPs/reports/WP05_REPORT.md`.
3. Commit the report with `WP05 report: document results`.
4. Print the required summary and stop. Do not create or begin WP06.

## Acceptance criteria

- WP05 checkpoint commit and annotated tag exist.
- Data inspection precedes and justifies example selection.
- Notebook completes the distributions/correlations sequence without becoming an inferential-statistics chapter.
- Static examples are concise, readable, non-identifying, and explicitly handle missingness.
- Correlation and pairwise-N matrices are both shown and discussed.
- Pearson/Spearman, part–whole correlation, group/site composition, outlier caution, and mixed-type associations are covered accurately.
- Every major subsection includes an active question with a self-learning answer/checklist.
- `eda-correlation` is config-driven, identifier-free, accessible, and uses pure tested calculations.
- Browser tests against the final built Chapter 1 page prove all explorer controls alter the real figure/statistics.
- Histogram and retention regressions remain green.
- Jupyter Book executes without notebook error reports, and MyST dropdowns render correctly.
- No runtime CDN/kernel dependency is introduced.
- Documentation/report are complete and the final working tree is clean.
- No WP06 file or out-of-scope maintenance change is created.

Stop after WP05 regardless of outcome.

