# WP09 — Course pages, streamlined EDA lesson, and interactive data inspection

## Objective

Create the course-level Introduction and Syllabus structure, rename the course,
make the portable notebook independent of repository-based installation
instructions, and shorten Exercise I into a focused first EDA practice using a
carefully verified 10–15-column ABIDE-II table. Add one reusable browser-native
data-inspection activity for comparing `head()`, `tail()`, and `sample()`.

Do not create or begin the next practice notebook. Do not merge this WP into
`main` or deploy it; release/deployment will be a separate WP after review.

## Required reading

Read completely before acting:

- `CLAUDE_INTERACTIVE_WIDGETS.md`
- `WPs/README.md`
- `WPs/reports/WP08_REPORT.md`
- `WPs/reports/WP08_EXACT_CHANGELOG.md`
- this WP

## 1. Mandatory checkpoint and branch safety

1. Confirm the current local `main` and `origin/main` relationship and inspect
   the complete working tree. Preserve any user changes.
2. Fetch `origin` and start a new branch from the current deployed `main`:
   `feature/course-pages-and-eda-trim`.
3. Add this WP brief and create the mandatory commit
   `checkpoint: before WP09` before implementation changes.
4. Create annotated tag `wp09-start` at the checkpoint. If it exists, use a
   clear numeric suffix and report it.
5. Run and record the complete WP08 baseline before implementation: frontend
   install/typecheck/unit/audit/build, artifact checks, Python tests, portable
   notebook check and smoke execution, standalone Playwright, clean Jupyter Book
   build plus error-log guard, and built-book Playwright.

Never use destructive git commands, rewrite history, force-push, or commit build
outputs/caches. Do not merge to `main` or publish this branch in WP09.

## 2. Rename the course

Use the exact course title consistently:

> Machine Learning for Neuroscience

Update Jupyter Book metadata, page titles/navigation where appropriate, the
portable-notebook banner, and any other student-facing location that still uses
an old course name. Do not put literal Markdown asterisks into YAML metadata or
HTML titles. Do not rename historical WP reports.

## 3. Create the course-level Introduction page

The **Introduction** page must appear first in the book, before Syllabus and
Contents. It is course-level material, not part of Exercise I.

Write a concise, professional page explaining:

- these are the practice-session materials for **Machine Learning for
  Neuroscience**;
- each practice notebook follows a brief PowerPoint presentation available on
  Moodle—mention Moodle but do not add a Moodle URL;
- notebooks can accompany the in-class practice or be used for self-learning at
  home, at the student's own pace;
- some activities work interactively on the published page without installing
  anything;
- students are encouraged to execute the code themselves and experiment by
  changing it;
- each notebook provides Colab and downloadable `.ipynb` controls for doing so;
- questions are deliberately placed before some explanations/results to promote
  deeper understanding and reasoning, and their style may resemble course
  assessment or exam questions;
- some questions have a revealable reasoning guide, while genuinely open
  questions may have no single answer.

Adapt the useful ideas from Exercise I's current **How to use this notebook**
block to course-level wording. Avoid repeating the same idea in multiple
sections. Do not add a time budget or imply that every question has an answer.

Use restrained design consistent with the established rust/cream course style.
Do not turn the page into marketing copy or a long technical setup guide.

## 4. Make Syllabus and Contents structurally correct

Required navigation order:

1. Introduction
2. Syllabus
3. Contents
4. Exercise I: Exploratory Data Analysis (EDA), nested appropriately beneath
   the course contents/chapter structure

Requirements:

- Update `_toc.yml` using valid Jupyter Book syntax; Introduction should be the
  book root if that is the cleanest way to guarantee the order.
- **Syllabus** should contain only the page title for now. Do not invent syllabus
  content, dates, assessment weights, or placeholder prose.
- Ensure Syllabus builds, opens, and appears in both the table of contents and
  primary sidebar.
- Keep the Contents page functional and ready to list additional practices later.
- Eliminate the existing repeated `syllabus` toctree-title warnings rather than
  suppressing them.
- Verify next/previous navigation follows the intended order.

## 5. Remove duplicated Exercise I introduction

The course Introduction now owns the general usage explanation. Streamline
`book/chapters/chapter_01/exercise_01.ipynb` accordingly:

- retain the H1 exercise title;
- retain a compact **Run or download this notebook** control because each
  notebook must provide its own Colab/download actions;
- remove **About this exercise**;
- remove **How to use this notebook**;
- remove other generic course-introduction material that now duplicates the
  Introduction page;
- remove **Learning objectives** entirely;
- retain **What this notebook covers**, editing it to match the shortened lesson;
- keep prerequisites concise and remove NumPy as a stated prerequisite because
  it is not a major focus of this exercise.

Do not remove local context that is genuinely needed to understand ABIDE-II or
the analysis that follows.

## 6. Make the portable notebook self-contained for package setup

The repository may become private after production. Remove student-facing setup
text such as:

> Running locally in VS Code / Jupyter: use the project's pinned versions,
> `pip install -r requirements.txt` from the repository, or install the four
> packages into your environment.

Requirements:

1. Neither the canonical nor generated portable notebook should instruct
   students to obtain requirements or setup information from the repository.
2. Add a short, optional package-installation **code cell** to the portable
   notebook for the packages actually imported by the lesson. It must be safe
   for Colab, VS Code, and Jupyter users.
3. Do not automatically reinstall/downgrade packages on every run. Prefer a
   clearly labelled cell whose installation command is commented out and which
   students uncomment/run only if imports fail, for example:

   ```python
   # If an import below fails, uncomment and run this line once:
   # %pip install numpy pandas matplotlib seaborn
   ```

   Adjust the package list only after inventorying the actual imports. Do not
   add packages merely because they are used by build/test tooling.
4. Do not mention a private/local repository path in the portable notebook.
5. Keep the portable notebook a deterministic generated derivative; do not
   hand-maintain it.
6. Preserve the already verified Colab and portable-download controls. The
   user manually confirmed that the current Colab title/path is correct.
7. Ensure all notebook data/config dependencies needed at runtime remain
   publicly reachable and independent of a local clone. Report any future
   private-repository limitation discovered for the buttons or hosted file
   rather than silently breaking it.

## 7. Reduce the ABIDE phenotypic table to 10–15 columns

Before editing, inspect the actual ABIDE-II data programmatically. Select **10 to
15 columns total** that provide a manageable first EDA table and satisfy all of
the following:

- participant identifier;
- site/scanner or equivalent acquisition-group identifier;
- diagnosis;
- core demographics, including age and sex;
- at least one additional categorical variable;
- multiple useful numeric variables;
- several variables with substantial missingness so the missing-data lesson
  remains meaningful;
- enough complete/partly complete numeric variables for illustrative
  distributions and correlations.

A candidate set to evaluate—not a mandatory list—is:

```text
SITE_ID, SUB_ID, DX_GROUP, AGE_AT_SCAN, SEX, HANDEDNESS_CATEGORY,
FIQ, VIQ, PIQ, CURRENT_MED_STATUS, EYE_STATUS_AT_SCAN,
ADI_R_SOCIAL_TOTAL_A, ADOS_G_TOTAL, SRS_TOTAL_RAW
```

Choose the final set based on observed dtype, availability, missingness, site
coverage, and teaching value. Avoid redundant questionnaire subscales. Keep the
final table between 10 and 15 columns; 12–14 is preferred if it satisfies the
lesson. Do not include a variable merely to reach a target count.

Update the canonical column configuration in one place and regenerate every
derived artifact from it. In the report, provide an exact compact table with the
final column name, teaching role, intended dtype, and overall missing percentage.

Then audit **every** downstream dependency and make it consistent with the new
table:

- data loading and printed shape;
- categorical conversions and labels;
- sample/head/tail displays;
- `info()` and `describe()` examples;
- missingness summaries and heatmaps;
- complete-case/core-variable comparisons;
- distributions, group comparisons, range checks, and correlations;
- all four browser activities after §11 is implemented;
- widget data/config artifacts;
- portable generator and smoke-test expected values;
- narrative claims, questions, answers, captions, table text, and tests.

No stale reference to a removed phenotype may remain in executable code,
displayed output, activity controls/defaults, prose that describes the active
table, or assertions. Links to the full official phenotype legend may of course
remain.

Do not fabricate values. Recalculate all examples from the revised table and
report every changed numeric result used in the lesson.

## 8. Shorten statistical inspection

Keep concise introductions to `DataFrame.info()` and `DataFrame.describe()` but
remove the separate sections/cells titled **Interpreting `info()`** and
**Interpreting `describe()`**.

Fold no more than one or two essential points into each earlier method
description:

- `info()` is useful for shape, dtypes, and non-null counts, but not
  distributions;
- `describe()` summarizes distributions of numeric variables but can hide
  group structure and requires attention to missing observations.

Keep wording suitable for first-time EDA students. Remove redundant output or
questions if their teaching purpose disappears after the trim.

## 9. Reduce the missing-data approaches table

Replace the approximately ten-row **Common approaches to missing data** table
with at most three clear approaches:

1. remove incomplete observations or variables;
2. impute missing values—all simple, model-based, and multiple-imputation
   variants summarized in this single row, with only the main benefit/caution;
3. keep missingness explicit or use an analysis/model that handles it, when
   scientifically and technically appropriate.

Use compact columns such as approach / when useful / main caution. Do not turn
subtypes of imputation into additional rows. Retain the essential principle that
the missingness mechanism and analysis goal determine the choice.

Update the surrounding ABIDE application to match the revised columns and avoid
implying that one strategy is universally best.

## 10. Trim the correlation section

- Remove the entire **When a correlation matrix is the wrong tool** section.
- Remove the **Participants behind each correlation** code and graph, plus text
  that exists only to introduce/interpret that display.
- Remove minor/repetitive correlation impressions.
- Retain only a few main data-supported observations from the revised numeric
  variables, stated briefly and without discussing participant counts.
- Do not imply causality or present correlations distorted by diagnostic scoring
  conventions as general population relationships.
- Keep the main correlation matrix/explorer only if it remains useful with the
  reduced table; update its variables, defaults, labels, explanatory text, and
  tests.
- Recompute all stated coefficients from the revised data and ensure the prose
  agrees with the displayed results.

This section should finish with a short practical takeaway, not a long advanced
methodological detour.

## 11. Add an interactive `head()` / `tail()` / `sample()` activity

At the beginning of **2. Data inspection**, replace the existing presentation
of a single random sample and the advance claim that `head()`/`tail()` are
inferior with a browser-native activity that lets students compare the methods
themselves.

### Student experience

Create a fourth activity using the reusable TypeScript/Vite/config-driven
architecture established in WP01–WP07. It must:

- work directly in the GitHub Pages iframe with no Python kernel;
- provide a clear selector for `head()`, `tail()`, and `sample()`;
- display an accessible table of rows from the revised phenotype subset;
- make missing values visually clear without suggesting they are errors;
- expose the site/scanner column so ordering/site concentration is visible;
- use an equal row count for fair comparison, with a modest control if useful;
- make `sample()` deterministic for the initial view and offer a deliberate
  resample/seed control if implemented;
- show a compact evidence summary such as sites represented and missing cells,
  so students can compare views rather than only stare at rows;
- be responsive and keyboard accessible and use the established visual style;
- use only the minimum public ABIDE fields required by the activity and introduce
  no new CDN/runtime dependency.

Prefer a new generic/configurable activity type such as `table-inspection`
rather than notebook-specific hard-coded DOM. Keep it reusable for future
notebooks.

### Pedagogical sequence

Do not tell students the conclusion before they explore. Use this order:

1. a short neutral prompt explaining that pandas offers several ways to inspect
   rows;
2. the interactive comparison;
3. a **Think first** card asking what each view reveals, how many sites appear,
   what happens to missingness patterns, and which view is more useful for a
   first broad look;
4. a concise explanation: `head()` and `tail()` are deterministic and useful for
   checking ordering/schema; a random sample can expose broader variety in an
   ordered multi-site table, but a small sample is not guaranteed to represent
   the full dataset;
5. a short collapsed Python equivalent using
   `phenotypes.head(n)`, `phenotypes.tail(n)`, and
   `phenotypes.sample(n, random_state=...)`.

Verify the actual data supports the intended observation. If head/tail do not
each concentrate on a site or do not exhibit the described pattern, report the
observed behavior and write the lesson around the evidence rather than forcing
the expected conclusion.

Update the remainder of **2. Data inspection** so its questions and explanations
refer to this activity and do not duplicate it.

### Activity tests

Add unit and Playwright coverage for:

- config/schema validation and unknown activity handling;
- exact pandas-equivalent row selection for head/tail and deterministic sample;
- resampling behavior, if present;
- correct site/missing-cell summaries;
- selector keyboard/accessibility behavior;
- responsive table rendering;
- iframe integration in the clean built book;
- a real control change visibly changing rows and summary state;
- artifact canonicality/offline production audit.

## 12. Design and visibility pass

After content changes, make a conservative pass over cell visibility and
dropdowns:

- retain revealable reasoning where it adds learning value;
- do not add an answer to every question;
- keep logistical/loading code hidden or collapsed;
- keep short, instructive code accessible;
- remove empty headings, orphan answers, duplicated introductions, and awkward
  transitions created by deletions;
- do not perform a broad visual redesign.

Recount cells and visibility tags from the actual final notebook and report the
numbers. Preserve unique stable cell IDs for retained cells; give new cells
stable unique IDs.

## 13. Portable notebook and private-repository readiness

Regenerate the portable notebook from the canonical source and confirm:

- no repository installation instruction or local relative runtime dependency;
- optional installation code cell is present and safe;
- all retained Python cells execute sequentially outside the repository;
- the reduced columns are embedded/generated correctly;
- the new browser activity becomes a normal HTTPS link back to the published
  page rather than an iframe;
- no MyST-only directive, hide tag, iframe, Node requirement, or generated output
  remains;
- all four activity replacements are recognized explicitly; unknown iframe
  titles still fail generation;
- the portable notebook remains deterministic and `--check` passes.

Do not claim that a private GitHub repository is directly accessible to every
Colab user. If the current Colab or raw-download URL would cease to work for
students once the source repository is private, document the exact constraint
and recommend a future stable distribution method; do not change hosting scope
without Yoav's authorization.

## 14. Required verification

Run the complete baseline again plus targeted tests for every change. At minimum
verify:

1. course title is exactly **Machine Learning for Neuroscience** in config and
   rendered navigation/title locations;
2. sidebar and prev/next order is Introduction → Syllabus → Contents → Exercise I;
3. Syllabus is title-only, builds, opens, and emits no title/toctree warning;
4. Introduction contains every requested concept, no Moodle link, no time
   estimate, and no guarantee that all questions have answers;
5. Exercise I no longer contains About/How-to/Learning objectives duplicates,
   but retains What this notebook covers and compact Colab/download controls;
6. NumPy is absent from stated prerequisites;
7. final table has 10–15 configured columns and all code/prose/artifacts use it;
8. no stale removed-variable reference remains;
9. `info()`/`describe()` interpretation sections are absent and essential caveats
   appear concisely earlier;
10. missing-data approaches table has no more than three body rows;
11. all requested correlation material is removed and remaining claims match
   recalculated values;
12. the new inspection activity works and teaches from observed data rather than
   a hard-coded conclusion;
13. all four browser activities render and respond in the built book;
14. portable notebook is deterministic, self-contained for setup, and executes
   outside the repository;
15. clean Jupyter Book build has no `*.err.log` and no newly introduced warning;
16. existing functionality and repaired sidebar remain green.

Visually inspect the Introduction, Syllabus, Contents, Exercise I opening, new
inspection activity, missing-data table, and shortened correlation ending at
desktop and narrow widths. Capture evidence in the report; do not commit
screenshots unless the repository already has a documented place for them.

## 15. Exact changelog and completion report

Create:

- `WPs/reports/WP09_REPORT.md`
- `WPs/reports/WP09_EXACT_CHANGELOG.md`

The report must include:

- success/failure for every numbered user request and every required test;
- checkpoint commit/tag, implementation commit, report commit, and branch;
- exact final column list with dtype/role/missing percentage;
- all changed numerical results and default activity selections;
- exact pages/cells/sections added, removed, retained, or merged;
- final notebook cell and visibility counts;
- test counts, build warnings, live/remote checks that were intentionally not
  performed, deviations, unresolved risks, and anything requiring Yoav;
- the private-repository implication for Colab/download distribution;
- confirmation that no merge to `main`, deployment, force push, destructive
  command, repository-setting change, or generated build-output commit occurred.

`WP09_EXACT_CHANGELOG.md` must provide location-specific before/after entries,
including stable notebook cell IDs and activity/config/artifact paths. It should
be possible to review the substantive work without diffing raw notebook JSON.

Commit implementation separately, then commit the two reports with:

```text
WP09 report: document course pages and EDA streamlining
```

## Stop condition

Stop after WP09 reports are committed on
`feature/course-pages-and-eda-trim`. Do not merge, push to `main`, deploy, remove
the generic theme download control, or start the next practice notebook.

