# WP07 — Final notebook corrections and portable Colab/VS Code version

## Objective

Apply seven user-requested corrections to the polished EDA notebook, diagnose and fix/remove the nonfunctional primary-sidebar toggle, and provide a maintainable portable notebook for Colab or downloaded local use without weakening the browser-native Jupyter Book version.

This WP must preserve all verified analysis results and all three working browser activities.

## User-requested corrections

1. The “Toggle primary sidebar” button appears to do nothing: make it work if practical; otherwise remove it.
2. “About this exercise”: remove the time budget; do not imply every question has a revealable answer; explain that questions promote deeper understanding and may resemble exam questions.
3. “How to use this notebook”: say only that some activities are interactive and work directly in the browser without installation; explain that students who want to execute or change code can use Colab or download the notebook.
4. Fix the Colab button opening an older/different notebook and make the runnable/download experience safe for casual Colab and VS Code users.
5. Remove the irrelevant question: “Why might pandas assign the `object` data type to a column?” Remove or adapt any answer that exists only for it.
6. Near the interactive histogram, add a collapsible executable Python example that plots `AGE_AT_SCAN` using 25 bins.
7. In the range-check introduction, explicitly define `IQR = Q3 − Q1` before presenting the 1.5×IQR fences.

Also correct the WP06 reporting arithmetic during WP07 reporting: the documented tag transitions imply 25 code cells after WP06 (15 visible, 7 `hide-input`, 3 `hide-cell`), not 22 code cells/12 visible. Recount from the actual notebook rather than assuming either number.

## 1. Mandatory checkpoint and baseline

1. Read `CLAUDE_INTERACTIVE_WIDGETS.md`, `WPs/README.md`, this WP, `WPs/reports/WP06_REPORT.md`, and `WPs/reports/WP06_EXACT_CHANGELOG.md` completely.
2. Confirm branch `feature/reusable-interactive-widgets`.
3. Inspect the working tree and create the mandatory `checkpoint: before WP07` commit plus annotated `wp07-start` tag before WP changes.
4. Run the complete WP06 baseline: npm clean install, typecheck, unit tests, production audit, Vite build, exporter tests/check, clean Jupyter Book build, error-log guard, standalone Playwright, and built-book Playwright.
5. Capture the current sidebar-button behavior at desktop and 390 px before changing it.

## 2. Diagnose the primary-sidebar toggle

Use Playwright and DOM inspection on the built page. Do not hide the button merely because its effect is subtle.

1. Identify the exact button element, accessible name, target, event handler, breakpoint behavior, and sidebar state before/after activation.
2. Test mouse click, keyboard Enter/Space, desktop, tablet-like width, and 390 px.
3. Determine whether the button:
   - opens a modal/drawer only below a breakpoint;
   - targets a missing/empty sidebar;
   - is obscured by CSS or z-index;
   - has a broken theme script/ARIA target;
   - is present where the theme never intended it to be actionable.
4. Prefer restoring correct theme behavior with narrowly scoped CSS/config/markup.
5. If the primary sidebar has meaningful navigation, do not remove access to it on narrow screens.
6. If a button is genuinely redundant at a viewport where the sidebar is permanently visible, hide it only at that viewport while retaining the working mobile control.
7. If repair would require fragile theme monkey-patching, remove only the nonfunctional control and document why.
8. Add browser regression tests asserting an observable sidebar state change where the control remains visible. Do not accept “click produced no error” as proof.

## 3. Correct the opening text

Edit `book/chapters/chapter_01/exercise_01.ipynb` with `nbformat`.

### About this exercise

- Remove every time estimate/budget.
- Retain guided-tutorial and self-study modes without durations.
- State that questions are included to encourage deeper understanding and may resemble questions used in course assessment/exams.
- Do not claim every question has a revealable answer. Explain that some have a reasoning dropdown while open discussion questions intentionally may not.
- Keep the tone supportive and professional; do not imply that notebook questions are guaranteed verbatim exam questions.

Suggested semantic wording—not mandatory verbatim:

> Questions throughout the notebook are designed to move beyond running code toward explaining analytical choices. Some include a revealable reasoning guide, while others are intentionally open for discussion. The style of reasoning may resemble course assessment questions.

### How to use this notebook

Keep it concise and include only:

- work through sections in order and pause at questions before continuing;
- some activities are interactive and work directly in the browser without installing anything;
- to execute cells or change code, use the Colab option or download the portable `.ipynb` notebook;
- some answers/checklists are revealable, while open questions may not have one fixed answer.

Do not enumerate which activities are interactive.

## 4. Design a robust Colab/download path

### Important constraint to report

The current feature branch is local. Any Colab URL based on GitHub `main` will show the older `main` notebook until WP01–WP07 are merged and pushed. Do not “fix” this by permanently pointing released course material at a temporary feature branch. State clearly in the report that remote end-to-end validation becomes possible after merge/push.

### Required architecture: generated portable notebook

Create a deterministic generator, for example `scripts/build_portable_notebook.py`, that derives a committed portable notebook from the canonical source:

```text
book/downloads/chapter_01/exercise_01_portable.ipynb
```

The exact path may vary modestly if repository conventions require it; document any deviation.

The portable notebook is for both Colab and downloaded VS Code/Jupyter use. It must not become an independently hand-maintained copy.

Generator requirements:

1. Source of truth remains `book/chapters/chapter_01/exercise_01.ipynb`.
2. Provide deterministic `--write` and `--check` modes. CI must fail if the committed portable notebook is stale.
3. Preserve ordinary explanatory Markdown and runnable Python analysis cells.
4. Replace the three Jupyter-Book iframe cells with concise Markdown containing:
   - what the activity explores;
   - a normal HTTPS link to the corresponding published activity/page;
   - a note that the embedded version is available on the course website.
5. Convert or simplify MyST-only directives (`{admonition}`, `{dropdown}` and classes) into Markdown/HTML that renders intelligibly in Colab and VS Code. Prefer `<details><summary>…</summary>…</details>` only if both environments render it reliably; otherwise use visible Markdown headings. No raw MyST fences may remain.
6. Remove Jupyter Book presentation tags/metadata that have no portable meaning, while preserving cell order and code.
7. Do not include JavaScript/TypeScript build steps, Node imports, local iframe paths, `book/_static` assumptions, or generated HTML in the portable notebook.
8. Ensure the Python dependency story is casual-user friendly:
   - inventory imports actually used;
   - rely on packages preinstalled in Colab where appropriate;
   - add one short optional setup cell only for packages not normally available;
   - avoid reinstalling or downgrading NumPy/pandas/matplotlib/seaborn/scipy unnecessarily;
   - give VS Code users a concise pointer to `requirements.txt`.
9. Ensure the ABIDE data and curated-column loading paths work outside the repository. Use pinned raw HTTPS resources or embed the small curated column list in the generated notebook; do not use local relative files that Colab cannot see.
10. Preserve categorical conversion and all later analysis dependencies.
11. Do not display credentials or require authentication.
12. Give the generated notebook a short banner saying it is the portable derivative and linking to the richer course webpage.

### Colab and download controls

1. Inspect the existing sphinx-book-theme/Jupyter Book Colab button and its constructed URL.
2. Remove or disable the old built-in Colab control if it cannot target the portable path.
3. Add stable, clearly labelled controls near the notebook opening or in a safe theme-supported location:
   - **Open portable notebook in Colab** →
     `https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/blob/main/book/downloads/chapter_01/exercise_01_portable.ipynb`
   - **Download portable notebook** → a stable raw GitHub `main` URL or Jupyter Book-served downloadable source that downloads the portable `.ipynb`.
4. Keep links on `main`, not the temporary feature branch. Explain that they become current after merge/push.
5. Ensure links open the intended path and do not silently fall back to the canonical embedded notebook.
6. If GitHub raw links trigger display rather than download in some browsers, use the best stable supported link and label it accurately (“View/download” if necessary).
7. Update “How to use this notebook” to refer to these controls without over-explaining implementation details.

### Portable notebook verification

1. Validate with `nbformat` and unique cell IDs.
2. Assert no iframe, relative `_static` URL, MyST directive fence, hide tag, widget import, or Node requirement remains.
3. Execute the portable notebook from a temporary directory outside the repository root using a fresh Jupyter kernel/environment representative of normal Python/Colab packages.
4. Confirm all Python cells execute in order and important output values match the canonical notebook.
5. Test the generated direct activity links syntactically. If the feature is not yet on remote `main`, mark remote HTTP/content equality as deferred—not falsely passing.
6. Add unit tests for deterministic transformation, iframe replacement, directive conversion, portable data loading, and `--check` stale detection.
7. Update GitHub Actions to run the portable generator in `--check` mode and execute/smoke-test it without duplicating expensive setup unnecessarily.

## 5. Remove the irrelevant pandas question

Locate the exact prompt:

> Why might pandas assign the `object` data type to a column?

Remove it cleanly from its “Think first” card. Renumber/repunctuate the remaining list if needed. Remove or adapt only the corresponding answer text, if present, and preserve other questions about `info()` that remain relevant to this dataset.

Record the exact cell ID and before/after list in the changelog.

## 6. Add the collapsible Python histogram example

Immediately adjacent to the interactive histogram introduction, add a short explanation such as “The same basic plot can be created in Python.” Then add an executable code cell using the existing dataframe and plotting stack, with exactly:

- variable: `AGE_AT_SCAN`;
- bins: `25`;
- labelled x-axis in years;
- y-axis as participant count;
- concise title;
- deterministic styling consistent with the notebook.

A suitable implementation is:

```python
fig, ax = plt.subplots(figsize=(8, 4))
sns.histplot(
    data=phenotypes,
    x="AGE_AT_SCAN",
    bins=25,
    color="steelblue",
    edgecolor="white",
    ax=ax,
)
ax.set(
    title="Distribution of age at scan",
    xlabel="Age at scan (years)",
    ylabel="Number of participants",
)
plt.show()
```

Use a revealable metadata tag so the Python code block is collapsed by default in the built book. Decide `hide-input` versus `hide-cell` based on whether showing a second static histogram output adds teaching value; prefer `hide-input` if the output usefully demonstrates equivalence, otherwise `hide-cell`. Record the decision.

Ensure the portable notebook keeps this Python cell runnable and visible or normally collapsible according to what the target environment supports.

## 7. Define IQR explicitly

Revise the range-check Markdown so it defines:

$$
\mathrm{IQR} = Q_3 - Q_1
$$

before stating the conventional fences:

$$
Q_1 - 1.5\,\mathrm{IQR}
\qquad\text{and}\qquad
Q_3 + 1.5\,\mathrm{IQR}.
$$

Explain briefly that `Q1` and `Q3` are the 25th and 75th percentiles. Preserve the important statement that crossing a fence flags an observation for inspection and does not prove error.

Verify MathJax/MyST rendering in the built HTML and readable fallback in the portable notebook.

## 8. Small deterministic cleanup

Seed the existing `sns.stripplot(..., jitter=0.25, ...)` example so repeated notebook builds reproduce the same point positions. Use a narrowly scoped approach that does not unexpectedly change randomness elsewhere. Rebuild twice and compare the target figure output/hash or plotted coordinates.

Do not expand this into broader figure redesign.

## 9. Tests

Run all existing tests and add targeted tests for the requested corrections.

Required assertions:

1. Sidebar button either changes an observable sidebar state at each viewport where visible, or is absent where intentionally removed.
2. No time estimate remains in “About this exercise.”
3. Opening text contains the assessment/deeper-understanding point without promising verbatim exam questions.
4. “How to use” no longer enumerates interactive activities and includes browser/no-install, Colab, and portable-download guidance.
5. The irrelevant `object`-dtype question and any orphaned answer are absent.
6. The Python age histogram cell exists, uses `AGE_AT_SCAN` and 25 bins, executes, and is revealable/collapsed as intended.
7. The IQR equations render and do not appear as raw markup.
8. Portable notebook generation is deterministic and `--check` passes.
9. Portable notebook executes outside the repository; data/config loading works.
10. The built-page Colab/download links target the portable notebook path on `main`.
11. All three browser activities still render and respond.
12. Existing unit, standalone-browser, and built-book tests remain green.
13. Clean Jupyter Book build with no `*.err.log`.
14. Two consecutive clean notebook builds reproduce the jittered figure deterministically.
15. No new off-origin dependency is introduced beyond existing pinned ABIDE/Colab/GitHub links and pre-existing theme resources.

## 10. Exact changelog and report

Create `WPs/reports/WP07_EXACT_CHANGELOG.md` with exact before/after entries for:

- sidebar diagnosis/fix or removal;
- both opening-text changes;
- Colab button/config and portable-notebook transformation;
- removed question/answer;
- histogram example cell and chosen visibility tag;
- IQR paragraph/equations;
- stripplot seeding;
- any CSS/config/workflow/test changes;
- corrected visibility counts.

Create `WPs/reports/WP07_REPORT.md` including:

- SUCCESS / PARTIAL SUCCESS / FAILURE;
- checkpoint/tag and commits;
- which items require Yoav's attention;
- exact sidebar root cause and resolution;
- canonical-vs-portable notebook explanation;
- what works in Colab and downloaded VS Code/Jupyter;
- what differs from the published book and why;
- the unavoidable fact that `main` remains older until merge/push;
- portable execution evidence;
- final cell/tag counts;
- test results;
- deviations and unresolved risks;
- recommendations only for WP08.

Then:

1. Confirm generated output/caches are ignored and uncommitted.
2. Commit implementation with `WP07: fix notebook UX and add portable Colab version`.
3. Commit both reports with `WP07 report: document final corrections`.
4. Print the required terminal summary and stop. Do not create or begin WP08.

## Acceptance criteria

- Mandatory WP07 checkpoint/tag exists.
- Sidebar toggle works observably wherever shown or is cleanly removed where redundant.
- Opening contains no time budget and accurately describes questions/answers/exam-style reasoning.
- “How to use” matches the requested concise browser/Colab/download guidance.
- Old/misleading Colab control is replaced by links to a deterministic portable notebook on `main`.
- Portable notebook is generated from the canonical notebook, validated, deterministic, and executes outside the repo without local static assets.
- Portable notebook contains runnable Python but replaces embedded activities with published links.
- Irrelevant object-dtype question is completely removed without harming adjacent questions.
- Collapsible executable Python age histogram with 25 bins is present.
- IQR, Q1, Q3, and both fences are clearly defined and render correctly.
- Stripplot jitter is deterministic across builds.
- All prior activities, unit tests, browser tests, notebook execution, and book build remain green.
- Exact changelog/report are complete and final tree is clean.
- No WP08 or unrelated infrastructure upgrade is created.

Stop after WP07 regardless of outcome.

