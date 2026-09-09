# WP06 — EDA notebook editorial, instructional, and visual design pass

## Objective

Perform a controlled final-quality pass over the complete Chapter 1 EDA notebook. Correct mistakes and unclear teaching, align its opening and learning objectives with the notebook that now exists, apply a coherent hide/show/dropdown policy, and improve the appearance of the Jupyter Book and embedded activities in a way that feels visually related to Assaf's course site.

This is an editorial/design WP, not a new statistics-content WP. Preserve the verified numerical results and working behavior from WP05 unless correcting a demonstrated error.

## Fixed principles

- The notebook must remain suitable both for a tutor-led session and independent study.
- Students should see code that teaches an EDA operation; logistical or repetitive plotting code may be collapsible.
- Questions should be visible before answers. Answers/solutions should be revealable, not permanently hidden.
- Essential outputs remain visible. Large/noisy diagnostic outputs should be summarized or collapsible.
- Never place `hide-cell`, `hide-input`, or `hide-output` as literal cell text; use notebook metadata tags.
- Preserve all three functioning browser-native activities.
- Use system/local fonts and locally shipped styles. Do not add a new external font/CDN dependency.
- Visual similarity to Assaf's site means coherent course-family cues—not copying his prose, source code, logos, or proprietary assets.
- Report every substantive correction exactly.

## 1. Mandatory checkpoint and baseline

1. Read `CLAUDE_INTERACTIVE_WIDGETS.md`, `WPs/README.md`, this WP, and `WPs/reports/WP05_REPORT.md` completely.
2. Confirm branch `feature/reusable-interactive-widgets`.
3. Inspect the working tree and create the mandatory `checkpoint: before WP06` commit plus annotated `wp06-start` tag before WP changes.
4. Run the complete WP05 baseline: clean npm install, typecheck, all unit tests, production audit, Vite build, exporter tests/check, clean Jupyter Book build, `*.err.log` guard, standalone Playwright, and built-book Playwright.
5. Capture baseline screenshots of the Chapter 1 page at desktop and narrow viewport sizes before visual changes. Store screenshots as ignored test artifacts, not committed binaries.

## 2. Inspect Assaf's rendered course site

Inspect the public reference page and its rendered CSS/layout:

- <https://asafmm.github.io/ml_for_neuro/class1_part2_linear_regression.html#s12>
- Inspect nearby sections and the site landing/navigation if relevant.

Use a real browser/Playwright when possible. Capture temporary desktop and mobile screenshots and inspect computed styles rather than inferring design only from HTML source.

Record in the report:

- page/content width and whitespace rhythm;
- font family/scale and heading hierarchy;
- background, text, border, and accent colors;
- table appearance;
- code/output containers;
- question/“try it yourself” presentation;
- interactive-control styling;
- navigation/header cues;
- which cues were adopted, adapted, or deliberately not copied.

Do not copy text, scripts, logos, images, or course assets. If the site cannot be reached, report the exact blocker and base the design on available screenshots/current observations; never claim direct inspection occurred.

## 3. Full correctness and clarity audit

Review all 79 notebook cells in order, including hidden cells and generated outputs. Use `nbformat`; do not audit by rendered prose alone.

### Check teaching prose

- spelling, grammar, punctuation, heading consistency, and undefined terminology;
- statements that are too absolute, ambiguous, redundant, or inconsistent with later sections;
- distinctions between observation, interpretation, and causal/inferential claims;
- accurate descriptions of pandas, NumPy, Matplotlib, and seaborn behavior;
- consistent use of ABIDE-II, phenotype/variable/feature, observation/participant, missing/available, category/categorical;
- correct references to earlier/later sections and activities;
- whether every question can be answered from preceding material;
- whether dropdown answers explain reasoning rather than simply state a result.

### Check code and outputs

- execution order and dependence on variables defined earlier;
- valid APIs—especially any incorrect suggestion of `np.stats` rather than NumPy functions or `scipy.stats`;
- categorical conversion, category labels, and undocumented codes;
- missing-value calculations and denominators;
- imputation examples: explicitly prevent students from learning data leakage. Clarify that production ML imputers are fit on training data and applied to validation/test data; do not imply global pre-split imputation is valid;
- structural/non-random missingness in diagnosis-specific measures;
- `describe`, `info`, correlation, pairwise-N, IQR, and crosstab correctness;
- pandas/seaborn warnings and deprecated calls;
- plots whose legends, axes, units, or sample sizes are misleading;
- outputs that are stale, duplicated, excessive, or inconsistent with current code;
- accidental participant identifiers in displays;
- MyST directives accidentally typed in code cells;
- literal hide tags inside sources;
- invalid/duplicate cell IDs or metadata.

### Verify data-specific statements

Recompute any edited numerical statement against the pinned ABIDE source/artifacts. Do not alter a verified WP05 value without recording old value, new value, calculation, and evidence.

Treat the undocumented `EYE_STATUS_AT_SCAN == 0` rows carefully: if the variable appears in explanatory material, clearly distinguish legend-defined codes from observed undocumented values rather than silently labelling 0.

## 4. Exact correction/change log

Create `WPs/reports/WP06_EXACT_CHANGELOG.md` as changes are made. Include one row per substantive change:

| ID | Notebook location/cell ID | Category | Before | After | Reason/evidence |
|---|---|---|---|---|---|

Categories include: factual correction, code correction, clarity, terminology, grammar, structure, cell type, metadata visibility, output cleanup, visual formatting, or accessibility.

Requirements:

- Quote enough before/after text or code to make the change identifiable.
- For deletions, state exactly what was removed.
- For grouped purely mechanical edits, list every affected cell ID and define the exact transformation.
- Do not log regenerated execution counts or unavoidable notebook serialization noise as substantive changes.
- Add a summary count by category.

## 5. Rewrite the opening to match the finished notebook

Adapt the notebook's early introduction and objectives after inspecting the whole notebook. The opening should include:

1. A clear title and one-paragraph purpose.
2. Context: this exercise follows the short tutor presentation and applies EDA to ABIDE-II phenotypic data.
3. Estimated time and intended modes: guided tutorial and self-study.
4. Prerequisites stated briefly—not a software-installation essay.
5. A “How to use this notebook” callout explaining visible questions, revealable answers, collapsible code, and browser-native activities.
6. Learning objectives using observable verbs and matching the actual notebook. At minimum, students should be able to:
   - inspect rows, schema, types, and summaries;
   - convert encoded variables to meaningful categorical representations;
   - quantify and reason about missingness across variables/sites;
   - compare missing-data strategies without introducing leakage;
   - describe and compare distributions;
   - flag unusual values without automatically deleting them;
   - select association views appropriate to variable types;
   - interpret Pearson/Spearman correlations alongside pairwise N and grouping/confounding.
7. A compact section roadmap reflecting the actual headings.

Keep the opening concise. Do not promise neuroimaging-feature modelling if the notebook only covers phenotypic EDA.

## 6. Establish and apply a visibility policy

First create a cell inventory with cell ID, type, heading/first line, tags, output type/size, and proposed policy. Include the final policy and counts in the report.

Use this default policy, departing only with an explicit reason:

| Cell role | Default presentation |
|---|---|
| Title, explanation, question, interpretation | Visible Markdown |
| Imports and global display/style setup | `hide-cell` or `hide-input`, depending on whether output exists |
| Remote-data/config loading and curation logistics | Collapsible (`hide-cell` preferred), with a visible concise explanation and data/legend links |
| Core EDA operations students should learn (`head`, `info`, `describe`, missing counts, groupby, `corr`, crosstab) | Input and essential output visible |
| Long plotting boilerplate after the concept is established | `hide-input`, output visible |
| Small pedagogically important plotting code | Visible |
| Optional/advanced calculation | `hide-cell`, clearly introduced as optional |
| Student fill-in/challenge cell | Visible and editable |
| Answer/reasoning | MyST dropdown; executable solution code revealable via metadata |
| Empty, stale, duplicate, or diagnostic output | Remove or regenerate; never hide merely to conceal an error |

Specific requirements:

- Ensure each hidden cell can actually be revealed in built HTML.
- Do not hide so much that self-learners cannot reproduce the analysis.
- Avoid consecutive hidden logistics cells with no visible explanation.
- Retain essential numeric/table outputs even when plotting code is collapsed.
- Normalize tags and remove conflicting/obsolete tags.
- Verify rendered toggle labels and keyboard operation.

## 7. Question and dropdown design

Audit every active question across the notebook, not only WP05 additions.

1. Make question prompts visually consistent and recognizable before answers.
2. Use valid MyST admonition/dropdown syntax in Markdown cells.
3. Prefer a consistent pair such as a visible “Think first” question card followed by a “Check your reasoning” dropdown.
4. Do not nest directives in a way Jupyter Book 1.0.4 cannot parse.
5. Preserve open-ended discussion where no single answer exists; label model answers as considerations/checklists.
6. Do not make introductory/data-loading background disappear merely because it is long; use a dropdown only when progressive disclosure improves reading.
7. Test that no directive renders as literal backticks/text.

## 8. Visual design system

Create a small, documented visual layer—preferably `book/_static/custom.css` or a similarly appropriate source file—and wire it through the existing Jupyter Book/Sphinx configuration using the mechanism supported by this project version.

### Design goals

- Visually related to Assaf's course through restrained palette, typography scale, spacing, card treatment, and interactive-control cues.
- Clearly still Yoav's notebook, without copied branding/assets.
- Professional scientific teaching material rather than a marketing page.
- Comfortable on desktop, laptop, narrow/mobile, and print/PDF where practical.

### Style targets

1. Define CSS custom properties for background, surface, text, muted text, accent, accent-soft, border, success/warning, and code background.
2. Use a local/system sans-serif font stack; do not fetch a web font.
3. Improve heading hierarchy, spacing, and anchor-offset behavior.
4. Set a readable main-column width and line length without squeezing wide figures/tables.
5. Style notebook tables/dataframes with:
   - readable font size and padding;
   - subtle header background;
   - zebra striping and hover/focus clarity;
   - responsive horizontal scrolling rather than page overflow;
   - numeric alignment where feasible;
   - captions/rounding through pandas Styler only when it improves interpretation.
6. Style question admonitions, dropdown answers, notes, warnings, and optional sidebars consistently but distinctly.
7. Style code input/output containers and toggle buttons so hidden content is obviously revealable.
8. Give all three interactive iframes a consistent card border, radius, background, padding/shadow treatment, and responsive width. Do not break their internal layout.
9. Align `interactive/src/styles.css` tokens and controls with the book palette so iframe content does not look pasted from another product.
10. Improve visible focus states and maintain WCAG AA contrast for normal text where practical. Do not encode diagnosis/groups by color alone.
11. Respect `prefers-reduced-motion`; avoid decorative animation.
12. Add restrained print rules so answers/code/tables do not become illegible.

Avoid:

- excessive gradients, shadows, pill-shaped everything, oversized hero sections, or decorative icons;
- global selectors that accidentally restyle navigation or Plotly internals;
- `!important` unless required to override the theme and documented;
- fragile selectors tied to generated notebook cell numbers;
- external CSS/JS dependencies.

### Tables and outputs

Audit each important table individually. Use global CSS for consistent baseline styling, then apply `pandas.Styler` only for justified formatting such as decimals, percentage display, captions, or highlighting a pedagogically important cell. Do not use gradients that imply significance or ranking without explanation.

## 9. Structural cleanup boundaries

Allowed:

- correcting headings, transitions, repeated explanations, cell types, tags, and stale outputs;
- removing a truly duplicate/dead cell after documenting it;
- removing a broken logo reference if no logo exists, with exact report entry;
- fixing TOC/title warnings directly caused by Chapter 1 presentation if low risk;
- small local helper functions when they reduce repeated display/formatting code.

Not allowed in WP06:

- new statistical topics or new interactive activities;
- changing the ABIDE artifact contents/source/hash without a factual need;
- Vite/Vitest major upgrades or Plotly code-splitting;
- replacing Jupyter Book with another framework;
- copying Assaf's content/assets;
- broad site redesign of unrelated chapters;
- pushing or merging the branch.

## 10. Testing and visual verification

Run the complete existing CI-equivalent suite and add targeted tests where useful.

Required checks:

1. `nbformat.validate`, unique cell IDs, valid tags, and no literal hide-tag lines.
2. Clean notebook execution and Jupyter Book build; no `*.err.log`.
3. No stale outputs: key displayed values match recomputation.
4. MyST questions/dropdowns/admonitions render as intended; none appear as literal directive syntax.
5. Hidden/collapsible inputs/cells have working visible toggles.
6. Custom CSS loads successfully in the built Chapter 1 page.
7. No horizontal page overflow at desktop and 390 px viewport; wide tables scroll within their container.
8. All three iframes load and remain interactive.
9. Existing 143+ unit tests, 40+ standalone browser tests, and 9+ built-book tests remain green.
10. Browser console has no new errors and no failed new asset requests.
11. Compare before/after screenshots at desktop and narrow viewport. Inspect the introduction, one representative table, one question/dropdown, hidden-code toggle, each static figure type, and all three interactive cards.
12. Inspect dark mode if the theme exposes it, and print preview or print CSS sufficiently to ensure content is not lost.
13. Run a basic automated contrast check if practical; manually inspect any unsupported custom states.

Do not commit screenshot/test-output binaries unless a pre-existing visual-regression convention requires them.

## 11. Reports and completion

Create:

### `WPs/reports/WP06_EXACT_CHANGELOG.md`

- Exact before/after correction table.
- Exact cell type/tag/visibility changes.
- Exact deleted/merged cells.
- Summary counts by change category.

### `WPs/reports/WP06_REPORT.md`

Include:

- SUCCESS / PARTIAL SUCCESS / FAILURE;
- checkpoint/tag and implementation commit;
- short correctness-audit summary;
- introduction/objectives before-versus-after summary;
- visibility policy and counts of visible/`hide-input`/`hide-cell`/`hide-output` cells;
- Assaf-site design observations and adopted/non-adopted cues;
- CSS/config/table/iframe changes;
- exact files changed;
- test commands/counts/results;
- visual/accessibility verification;
- deviations and unresolved risks;
- recommendations only for WP07.

Then:

1. Confirm generated output/caches are ignored and uncommitted.
2. Commit implementation with `WP06: polish EDA notebook content and design`.
3. Commit both reports with `WP06 report: document editorial and design changes`.
4. Print the required terminal summary and stop. Do not create or begin WP07.

## Acceptance criteria

- Mandatory WP06 checkpoint/tag exists.
- Every substantive correction and visibility/type change is recorded exactly.
- No verified numerical result changes without recomputation and documentation.
- Introduction, objectives, roadmap, timing, prerequisites, and usage instructions accurately match the completed notebook.
- A consistent, justified visibility policy is applied without hiding core learning code.
- All active questions and answers render consistently and remain usable for self-study.
- Custom styling measurably improves headings, tables, cards, code toggles, iframes, responsiveness, and focus states.
- Design decisions are informed by a documented inspection of Assaf's rendered site, or the access failure is honestly reported.
- No copied content/assets or new external dependency is introduced.
- Notebook execution, full Jupyter Book build, all prior unit/browser tests, and new visual/structure assertions pass.
- Desktop/narrow screenshots are reviewed; tables do not cause page overflow.
- Three interactive activities remain functional.
- Reports are complete and working tree is clean after separate commits.
- No WP07 or out-of-scope infrastructure upgrade is created.

Stop after WP06 regardless of outcome.

