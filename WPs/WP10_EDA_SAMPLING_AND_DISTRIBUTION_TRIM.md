# WP10 — Sampling display corrections and final distribution trim

## Objective

Apply four focused corrections to the WP09 EDA notebook and its portable
derivative. Keep the existing course pages, 13-column ABIDE-II selection, and
four browser activities otherwise unchanged.

Do not merge to `main`, deploy, change the private/public distribution
architecture, remove the generic theme download control, or begin another
practice notebook.

## Required reading and checkpoint

Read completely:

- `CLAUDE_INTERACTIVE_WIDGETS.md`
- `WPs/README.md`
- `WPs/reports/WP09_REPORT.md`
- `WPs/reports/WP09_EXACT_CHANGELOG.md`
- this WP

Then:

1. Confirm branch `feature/course-pages-and-eda-trim` and inspect the working
   tree. Preserve every pre-existing user change.
2. Add this WP brief and create the mandatory commit
   `checkpoint: before WP10` before implementation changes.
3. Create annotated tag `wp10-start` at the checkpoint, using an unambiguous
   suffix only if necessary.
4. Run the complete WP09 baseline and record its results.

Never use destructive git commands, rewrite history, force-push, or commit
generated build output/caches.

## 1. Simplify the sampling-activity evidence summary

The visible summary currently produces text such as:

> sample() shows 11 rows from 9 acquisition sites (ABIDEII-ETH_1,
> ABIDEII-GU_1, ...); 11 of 88 cells are missing.

Keep the **number** of acquisition sites but remove the parenthesized list of
site names from the visible description. The intended form is:

> sample() shows 11 rows from 9 acquisition sites; … cells are missing.

Requirements:

- apply consistently to `head()`, `tail()`, and `sample()`;
- retain row count, acquisition-site count, and missing-cell count;
- do not expose the site-name list elsewhere in the visible summary, tooltip, or
  redundant paragraph;
- the site column remains visible in the table, so students can inspect names
  there if desired;
- update accessibility text and tests so screen readers do not receive the
  removed parenthesized list as hidden duplicate prose;
- internal site-list computation may remain if useful for tests/state, but it
  must not clutter the student-facing description.

## 2. Display all 13 curated columns in the interactive table

The WP09 table-inspection activity displays only 8 of the 13 active phenotype
columns. This makes comparison with the rest of the notebook confusing.

Update `table_inspection.json` and the component/data contract as needed so the
interactive table shows **all 13 curated columns**, in exactly the same order as
`book/config/eda_phenotype_columns.json`:

```text
SITE_ID
SUB_ID
DX_GROUP
AGE_AT_SCAN
SEX
HANDEDNESS_CATEGORY
FIQ
VIQ
PIQ
CURRENT_MED_STATUS
SRS_TOTAL_RAW
ADOS_G_TOTAL
ADI_R_SOCIAL_TOTAL_A
```

Requirements:

- derive or test the configuration against the canonical list so future drift
  is caught;
- keep horizontal scrolling contained inside the activity at desktop and narrow
  widths; do not cause page-level horizontal overflow;
- keep headers sticky/readable and missing cells accessible;
- recompute the evidence summary from all 13 displayed columns. For example, 11
  rows now means 143 inspected cells, not 88; never hard-code a missing count;
- preserve deterministic `head()`, `tail()`, `sample()`, reshuffle, row-count,
  keyboard, and responsive behavior;
- update unit, standalone Playwright, and built-book Playwright expectations.

Inspect the actual default and representative views after the change and report
the exact row/site/missing-cell summaries used by tests. Do not fabricate them.

## 3. Separate canonical-book and portable sampling output behavior

The Python-equivalent cell currently displays all three outputs directly in the
published notebook, which is duplicative after the interactive activity.

### Published Jupyter Book behavior

For the stable cell currently identified in WP09 as `7a1e5c93d204`:

- show the Python code by default;
- hide/collapse its output by default using `hide-output`;
- remove `hide-input` from this cell;
- keep the code demonstrating all three methods:
  `phenotypes.head(n)`, `phenotypes.tail(n)`, and
  `phenotypes.sample(n, random_state=...)`;
- define `n` once rather than repeating an unexplained literal where practical;
- add a concise code comment inviting students to change `n` and
  `random_state` and observe what changes;
- ensure the prose introduces this as **code to display each sampling method**,
  not as three additional results students must study after the interactive.

The clean built HTML must visibly show the code and keep the three table outputs
collapsed until the student requests them. Verify the actual toggle behavior,
not only the cell metadata.

### Portable Colab/download notebook behavior

The portable notebook does not embed the sampling activity. For this specific
cell, it should therefore contain:

- the code, visible;
- the comment encouraging changes to `n` and `random_state`;
- the three saved table outputs, visible by default when the portable notebook
  first opens;
- normal behavior when students rerun the cell in Colab, VS Code, or Jupyter.

Modify the deterministic portable generator rather than hand-editing the
portable notebook. The generator currently strips presentation metadata and
clears outputs; introduce the narrowest stable exception for this known cell.
Sanitize irrelevant execution metadata while preserving deterministic,
portable pandas table outputs. Add tests proving:

- this cell alone retains the intended saved outputs;
- no unrelated code-cell output is accidentally retained;
- no Jupyter Book hide tag remains in the portable notebook;
- repeated generation is byte-identical;
- portable smoke execution still passes outside the repository.

If preserving canonical saved outputs introduces unstable HTML identifiers or
environment-specific bytes, normalize the output deterministically or generate
a portable-safe representation. Do not weaken the stale-file check.

## 4. Remove the entire range-check subsection

Remove **Range checks and flagged values** because the distributions section is
still too long. Remove the complete teaching unit, not only its heading:

- the range-check introduction;
- the IQR definition and fence equations;
- code that calculates or displays flagged ages;
- related Think first / answer or reasoning material;
- captions, transitions, synthesis text, and output references that exist only
  for this example.

Update all affected material:

- **What this notebook covers** must no longer promise range checks;
- the portable notebook and its smoke expected values must not refer to the 56
  flagged participants or IQR fences;
- remove obsolete IQR/range assertions from tests rather than changing them into
  vacuous checks;
- remove any now-unused imports or variables only if genuinely unused;
- repair section transitions and heading order after deletion;
- ensure no active prose, code, output, or activity prompt refers to this removed
  subsection.

Do not remove the histogram, distribution summaries, group comparison, or main
correlation lesson unless necessary to repair a direct dangling reference.

## 5. Regenerate and verify all derivatives

Regenerate the portable notebook and any affected widget configuration/artifact.
Run the complete WP09 suite plus targeted tests for these corrections:

1. visible sampling summary includes site count but no parenthesized site list;
2. interactive table displays the exact 13-column canonical list in order;
3. summary totals/missing counts reflect 13 columns at every row-count setting;
4. activity remains usable and contained at 390 px and desktop widths;
5. canonical sampling-equivalent cell is visible code + `hide-output`, not
   `hide-input`, and output is collapsed in built HTML;
6. portable version shows code plus deterministic saved outputs for that cell;
7. portable setup remains repository-independent and its optional install line
   remains safe/commented;
8. complete range-check teaching unit and all dependencies are absent;
9. all four browser activities still render and respond;
10. repaired sidebar and Introduction/Syllabus/Contents navigation remain green;
11. clean Jupyter Book build has no `*.err.log` and no new warning;
12. all notebook IDs remain unique and all retained cell IDs remain stable;
13. generator `--check`, out-of-repo portable smoke, and repeated-build
    determinism pass.

Visually inspect the modified activity and surrounding notebook sequence at
desktop and 390 px. Recount final notebook cells and visibility tags from the
actual files.

## 6. Report and stop

Create:

- `WPs/reports/WP10_REPORT.md`
- `WPs/reports/WP10_EXACT_CHANGELOG.md`

Report:

- success/failure for each user correction and every required check;
- checkpoint/tag, implementation commit, report commit, and branch;
- exact final interactive column order;
- actual default/example summary counts after switching to 13 columns;
- exact notebook cells removed/modified and final visibility/cell counts;
- exact portable-generator exception used for saved sampling outputs;
- test counts, warnings, deviations, unresolved risks, and anything requiring
  Yoav;
- confirmation that no merge, deployment, push, hosting change, generic-download
  change, destructive command, or generated build-output commit occurred.

Commit implementation separately, then commit the reports with:

```text
WP10 report: document sampling corrections and distribution trim
```

Stop after the report commit on `feature/course-pages-and-eda-trim`. Do not
start another WP or practice notebook.

