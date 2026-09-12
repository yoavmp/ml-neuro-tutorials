# WP10 implementation report — sampling display corrections and final distribution trim

## Outcome

Status: **SUCCESS**

All four user corrections in `WPs/WP10_EDA_SAMPLING_AND_DISTRIBUTION_TRIM.md` and
every numbered check in §5 are done and green. No merge, deployment, push,
hosting change, private/public architecture change, generic-download-control
change, destructive git command, history rewrite, or generated build-output
commit occurred. No next practice notebook was started.

| Check | Before WP10 | After WP10 |
|---|---|---|
| Frontend typecheck | PASS | PASS |
| Frontend unit (`vitest`) | 177 / 177 | **187 / 187** |
| `npm audit --omit=dev` | 0 vulnerabilities | 0 vulnerabilities |
| Widget artifact `--check --artifact all` | 2 valid + canonical | **3 valid + canonical** (new `abide_table_inspection.json`) |
| Python unit (`unittest discover -s tests`) | 97 / 97 | **114 / 114** |
| Portable notebook `--check` | up to date (78 cells) | **up to date (75 cells)** |
| Portable smoke (out of repo, network) | 21 code cells, key values matched | **20 code cells, key values matched** |
| Standalone Playwright | 50 / 50 | **50 / 50** (assertions updated) |
| Clean Jupyter Book build | build succeeded, **2 warnings** | build succeeded, **2 warnings** (same two pre-existing) |
| `*.err.log` guard | empty | empty |
| Built-book Playwright | 16 / 16 | **16 / 16** (assertions updated) |
| 3× consecutive clean builds, deterministic figures | identical (5 PNGs) | **identical (5 PNGs)** |

The two build warnings are the pre-existing `logo file 'logo.png' does not exist`
and `book/README.md: document isn't included in any toctree`; both predate WP10
and are out of scope. No new warning was introduced.

## 1. Checkpoint, tag, baseline (WP10 §"Required reading and checkpoint")

- Branch confirmed: **`feature/course-pages-and-eda-trim`** (unchanged).
- Working tree at start: only the untracked WP brief
  `WPs/WP10_EDA_SAMPLING_AND_DISTRIBUTION_TRIM.md`. No build output, cache,
  `.DS_Store`, credential, token, or private data present.
- **Checkpoint commit: `d9d3fc831e05c71ceaae785636ac3aeda9fd7740`**
  (`checkpoint: before WP10`) — adds the WP brief only (1 file, +235 lines).
- **Annotated tag: `wp10-start`** → `d9d3fc8`. The name was free; **no numeric
  suffix** was needed.
- The complete WP09 baseline was run **before** any implementation change and is
  the "Before WP10" column above.
- No `git reset --hard`, `git checkout -- <path>`, `git clean`, `git rebase`,
  `git revert`, history rewrite, or force-push at any point.

## 2. User correction 1 — simplify the sampling-activity evidence summary — SUCCESS

`interactive/src/components/table-inspection.ts`: the `role="status"` evidence
line dropped the parenthesized site-name list. It now reads, for every method:

> `sample() shows 8 rows from 8 acquisition sites; 17 of 104 cells are missing.`
> `head() shows 8 rows from 1 acquisition site; 24 of 104 cells are missing.`

- Applies to `head()`, `tail()` and `sample()` (one code path).
- Retains the row count, the acquisition-**site count**, and the missing-cell
  count.
- The site-name list is not exposed anywhere student-facing: not in the summary,
  not in a tooltip/`title`, not in a redundant paragraph, and not in the
  accessible announcement (the summary's `textContent` is what a screen reader
  reads, and it no longer contains the list).
- The `SITE_ID` column is still displayed in the table, so names remain
  inspectable there.
- Internal state kept for tests only: `table.dataset.sites` (the
  `data-sites` attribute) still carries the comma-joined list; `summariseView`
  still computes `sites` / `siteCount`. Neither is visible prose. WP10 §1
  explicitly permits this.
- Tests updated: `interactive/e2e/table-inspection.spec.ts` asserts the exact
  new summary string and `not.toContain("ABIDEII-")` / `not.toMatch(/\([A-Z]/)`
  on the summary text; `interactive/e2e-book/chapter01.spec.ts` asserts
  `summaryText).not.toContain("ABIDEII-")`.

## 3. User correction 2 — display all 13 curated columns — SUCCESS

### Final interactive column order (exactly `book/config/eda_phenotype_columns.json`)

```
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

### Data-contract change

The WP09 activity displayed 8 of 13 columns because it reused
`abide_retention.json`, which deliberately has **no `SUB_ID`** (Rule 11 /
WP09). Showing the real rows of the curated table — identifier column
included — is the point of comparing `head()/tail()/sample()`, and WP10 §2
requires all 13, so a **dedicated deterministic artifact** was added rather
than polluting the retention/correlation data:

- **`scripts/export_widget_data.py`**: new `build_table_inspection_artifact` /
  `validate_table_inspection_artifact`, a third `ArtifactSpec`
  (`ARTIFACTS["table-inspection"]`), and `--artifact table-inspection` (also
  covered by `all`). The builder **derives** the 13 displayed columns directly
  from the curated column authority, so it cannot drift. Exactly the two
  names `("SITE_ID", "SUB_ID")` — `TABLE_INSPECTION_IDENTIFIER_FIELDS` — are
  allowed through as non-empty **string** display columns
  (`_identifier_label`, which also strips the trailing `.0` from the integer
  `SUB_ID`); every other column is a curated, non-identifier number / code /
  `null` array exactly as in the retention artifact. `abide_histogram.json`
  and `abide_retention.json` are **byte-identical** to before (verified).
- **`book/_static/widgets/data/abide_table_inspection.json`** (new, generated,
  `--refresh`): `activity` `table-inspection`, `rowCount` 1114,
  `columnOrder` = the 13-name authority verbatim, `identifierFields`
  `["SITE_ID","SUB_ID"]`, `site` block (19 sites), `variables` meta for the
  11 non-identifier columns, `columns` for all 13. `--check` reports it
  valid + canonical; two `--refresh` runs are byte-identical
  (`sha256 21d0e932…`).
- **`interactive/src/table-inspection-data.ts`** (new): component-owned Zod
  schema + `parseAbideTableInspectionData`. Enforces on the client:
  `columnOrder` == column keys, every column aligned to `rowCount`, the two
  identifier columns are non-empty strings on every row, any **other**
  identifier-shaped column name is rejected, `variables` metadata covers
  exactly the non-identifier columns and agrees with the data, and
  `site.sites` is first-appearance order.
- **`interactive/src/components/table-inspection.ts`**: `parseData` and the
  mounted data type switched to the new module; the "no SUB_ID" comment
  replaced with the real contract.
- **`book/_static/widgets/configs/table_inspection.json`**: `data` →
  `../data/abide_table_inspection.json`; `columns` → the 13 entries in
  canonical order, each with a human label.

### Drift protection

- `tests/test_table_inspection_columns.py` (new): asserts the authority is the
  13-column list, `[c["name"] for c in config.columns] == authority`
  (order included), and the committed artifact's `columnOrder` == authority
  with `SITE_ID`/`SUB_ID` complete string columns.
- `interactive/tests/table-inspection.test.ts`: the "against the committed
  artifact" block now loads `abide_table_inspection.json`, uses the 13-column
  `DISPLAY`, and checks `columnOrder` / `identifierFields` / a full `SUB_ID`
  string column.

### Actual summary counts after switching to 13 columns (measured, not fabricated)

`rowCount` 8 is the configured default view.

| View | Sites | Missing / total cells |
|---|---|---|
| `head(8)` (default) | 1 (`ABIDEII-BNI_1`) | **24 / 104** |
| `tail(8)` | 1 (`ABIDEII-USM_1`) | **35 / 104** |
| `sample(8, seed 7)` | 8 | **17 / 104** |
| `head(11)` | 1 | 33 / **143** |
| `tail(11)` | 1 | 41 / **143** |
| `sample(11, seed 7)` | 10 | 22 / **143** |
| `head(15)` | 1 | 46 / **195** |
| `tail(15)` | 1 | 46 / **195** |
| `sample(15, seed 7)` | 12 | 31 / **195** |

`SITE_ID`, `SUB_ID`, `DX_GROUP`, `AGE_AT_SCAN`, `SEX` are complete, so the extra
missing cells versus WP09 come from adding `VIQ`, `PIQ`, `CURRENT_MED_STATUS`
and `ADI_R_SOCIAL_TOTAL_A` to the view. `11 rows` now inspects `11 × 13 = 143`
cells; nothing is hard-coded — the number is `rowCount × displayColumns.length`.
The seeded draw `[12, 482, 585, 680, 773, 858, 976, 1098]` and the
`head`/`tail` selections are unchanged (deterministic `mulberry32` + full
Fisher–Yates); reshuffle still advances to seed 8; row-count, keyboard and
responsive behaviour unchanged.

### Containment (measured)

Visually inspected in the built book at 1280 px and 390 px: all 13 headers
render, the table scrolls inside `.widget-table-scroll`
(`overflow-x:auto`), and `document.documentElement.scrollWidth` equals the
viewport width at both sizes — no page-level horizontal overflow. Headers stay
sticky; missing cells keep `.widget-cell-missing` + a visually-hidden
"missing" label and are never called an error. The standalone narrow-viewport
Playwright test was moved from 375 px to **390 px** and additionally asserts
`thead th` count 13; the built-book narrow test already used 390 px.

## 4. User correction 3 — separate canonical and portable sampling output — SUCCESS

### Published Jupyter Book (`book/chapters/chapter_01/exercise_01.ipynb`)

Cell `7a1e5c93d204` (source, tags, and re-executed outputs):

```python
# Code to display each sampling method. head() and tail() are
# deterministic; sample() draws rows at random, and passing random_state
# makes one particular draw reproducible. Change n or random_state and
# re-run to see what changes.
from IPython.display import display

n = 8
display(phenotypes.head(n))
display(phenotypes.tail(n))
display(phenotypes.sample(n, random_state=0))
```

- `hide-input` **removed**, `hide-output` **added** — the only cell tag change.
- `n` is defined **once**; the comment invites changing `n` and `random_state`.
- All three methods kept: `phenotypes.head(n)`, `phenotypes.tail(n)`,
  `phenotypes.sample(n, random_state=0)`.
- The preceding explanation cell `7a1e5c93d203` gained a lead-in paragraph
  framing the next cell as *"the Python code for each of these three sampling
  methods … here to show the code, not three more result tables to study: the
  activity above already compares what the methods return."*
- Verified in the clean built HTML: the cell renders as
  `class="cell tag_hide-output …"` with the `cell_input` container present
  (code visible) and a **"Show code cell output" / "Hide code cell output"**
  toggle — the three tables are collapsed until requested. No `tag_hide-input`
  on the cell.

### Portable Colab / download notebook

`scripts/build_portable_notebook.py`: the generator still strips presentation
tags and clears every code-cell output — with **one** narrow, stable
exception:

```python
PRESERVE_OUTPUT_IDS = frozenset({"7a1e5c93d204"})
```

- In the code-cell branch, a cell whose id is in `PRESERVE_OUTPUT_IDS` gets
  `new["outputs"] = _preserved_outputs(src_cell)` instead of `[]`;
  `execution_count` is still `None`.
- `_sanitise_output(out)` copies one canonical output keeping only
  `output_type` and the deterministic payload (`text/html` + `text/plain`
  pandas tables, or stream `text`), drops per-output `execution_count`, and
  blanks `metadata` (kills the `iopub.*` timestamps). Result depends only on
  the committed canonical notebook, so repeated generation is byte-identical
  (`--check` and `test_repeated_builds_are_byte_identical` pass).
- `_assert_portable` now: allows stored outputs **only** on
  `PRESERVE_OUTPUT_IDS`; requires that cell to carry ≥1 output, each
  `display_data`/`execute_result`/`stream` with `text/plain` containing
  `SITE_ID`, no `execution_count`, no transient metadata, and no hide tag;
  and asserts **no other** code cell has outputs and no code cell keeps an
  `execution_count`.
- The portable data-loading cell still embeds `CURATED_COLUMNS` literally,
  keeps the pinned ABIDE-II CSV URL, and has no `../../config/` /
  `requirements.txt` / active `%pip`. The commented install cell is unchanged.
- Result: `book/downloads/chapter_01/exercise_01_portable.ipynb`,
  **75 cells** (55 markdown + 20 code). Exactly one code cell —
  `7a1e5c93d204` — carries outputs (3 sanitised `display_data` pandas
  tables, visible by default); all 19 others are output-free. Re-running the
  cell in Colab / VS Code / Jupyter simply refreshes the tables (the smoke
  test re-executes the whole notebook cleanly).

### New portable-generator tests

`tests/test_build_portable_notebook.py`: `test_no_iframe_or_static_or_directive_or_hidetag`
now skips the preserved id for the empty-outputs assertion; added
`test_only_the_sampling_cell_keeps_saved_outputs`,
`test_sampling_cell_keeps_three_sanitised_pandas_tables` (3 outputs, `metadata`
empty, no `execution_count`, `SITE_ID`/`SUB_ID` in the plain text), and
`test_no_range_check_or_iqr_remnant`.

## 5. User correction 4 — remove the range-check subsection — SUCCESS

Removed from `book/chapters/chapter_01/exercise_01.ipynb` (via `nbformat`):

| Cell id | Was |
|---|---|
| `58db4c1fc44e` | md `### Range checks and flagged values` — intro + IQR / fence equations |
| `7bf82a8cd5a9` | code — quartiles, `lower_fence`/`upper_fence`, `flagged_age`, the printed "56 of 1114 participants flagged", the flagged-rows table |
| `c374c2ec5540` | md Think first "Evidence before editing a value" + its "Check your reasoning" dropdown (all about the flagged ages) |

- **`What this notebook covers`** (`373d8862-…`) item 5: "…comparing across
  groups, **range checks**, and Pearson/Spearman…" → "…comparing across
  groups, and Pearson/Spearman correlations (with the correlation explorer)."
- No other active prose, code, output, caption, transition, or activity prompt
  refers to the removed unit. Full-notebook search for `Range checks`,
  `range check`, `IQR`, `interquartile`, `lower_fence`, `upper_fence`,
  `flagged_age`, `1.5`, `56 of 1114`, `participants flagged` → **nothing**
  (asserted by `tests/test_notebook_corrections.py::test_range_check_subsection_fully_removed`).
- Section order after deletion: `## 5. Distributions and feature correlations`
  → distributions → group comparison → site-composition heatmap + its
  "Confounding and composition" Think first (`d9fa820679e0`) →
  `### Pearson and Spearman correlations` (`fd14e7f5d7a7`) → explorer →
  synthesis. The transition from the confounding card straight into the
  Pearson/Spearman heading is clean; no dangling reference.
- No imports became unused — `numpy` is still used by the seeded stripplot
  (`80632a35b296`) and the correlation mask (`9b478759eff3`); nothing was
  removed unnecessarily.
- **Portable notebook + smoke**: the portable notebook no longer contains the
  IQR unit (75 cells). `scripts/smoke_portable_notebook.py` `EXPECTED_SUBSTRINGS`
  dropped `"56 of 1114 participants flagged"` and now anchors on
  `"Data table shape: (1114, 13)"` + `"Complete for all 13 variables"`;
  docstring updated. Smoke passes out of repo (20 code cells).
- **Tests**: `test_iqr_range_check_still_flags_56` **removed** (not made
  vacuous); `test_range_check_subsection_fully_removed` added;
  `test_cell_and_visibility_counts` updated;
  `test_what_this_notebook_covers_kept_and_numpy_not_a_prerequisite` gained
  `assertNotIn("range check", covers.lower())`.
- Histogram, distribution summaries, group comparison, and the correlation
  lesson were **not** touched.

## 6. Regenerate + verify (WP10 §5) — all 13 checks

| # | Requirement | Result |
|---|---|---|
| 1 | visible sampling summary has the site **count** but no parenthesized site list | **PASS** (component + standalone/built-book Playwright) |
| 2 | interactive table displays the exact 13-column canonical list in order | **PASS** (`test_table_inspection_columns.py`; config, artifact `columnOrder`, and `thead th` count 13 all checked) |
| 3 | summary totals / missing counts reflect 13 columns at every row-count setting | **PASS** (`totalCells = rows × 13`; head/tail/sample at n = 8/11/15 measured above; unit + Playwright) |
| 4 | activity usable and contained at 390 px and desktop | **PASS** (visual check + Playwright: 13 headers render, table scrolls in its box, no page horizontal overflow at 390 px and 1280 px) |
| 5 | canonical sampling cell is visible code + `hide-output`, not `hide-input`, output collapsed in built HTML | **PASS** (cell metadata + built HTML toggle verified) |
| 6 | portable version shows code + deterministic saved outputs for that cell | **PASS** (3 sanitised `display_data` tables; only that cell; byte-identical regeneration) |
| 7 | portable setup repo-independent, optional install line safe/commented | **PASS** (unchanged; `test_build_portable_notebook.py` green) |
| 8 | complete range-check unit and all dependencies absent | **PASS** (`test_range_check_subsection_fully_removed`; portable + smoke) |
| 9 | all four browser activities still render and respond | **PASS** (built-book Playwright 16/16; standalone 50/50) |
| 10 | sidebar + Introduction/Syllabus/Contents navigation still green | **PASS** (sidebar-toggle 4/4; nav unchanged — not touched) |
| 11 | clean Jupyter Book build: no `*.err.log`, no new warning | **PASS** (2 warnings, both pre-existing) |
| 12 | notebook IDs unique, retained cell IDs stable | **PASS** (73 canonical / 75 portable, `nbformat.validate` OK, ids unique; only ids removed, none renamed) |
| 13 | generator `--check`, out-of-repo portable smoke, repeated-build determinism | **PASS** (`--check` up to date; smoke 20 cells out of repo; 3× clean builds → identical 5-PNG hash set; `export_widget_data --refresh` ×2 byte-identical) |

### Final counts recounted from the actual files

| | Canonical notebook | Portable notebook |
|---|---|---|
| Total cells | **73** (was 76) | **75** (was 78) |
| Markdown | 54 | 55 |
| Code | **19** (was 20) | 20 |
| Code — visible | 9 | 20 |
| Code — `hide-input` | 7 | 0 |
| Code — `hide-cell` | 2 | 0 |
| Code — `hide-output` | **1** (was 0) | 0 |
| Code cells with stored outputs | (executed notebook) | **1** (`7a1e5c93d204` only) |

Only tags anywhere in the canonical notebook: `hide-input`, `hide-cell`,
`hide-output`. `nbformat.validate` passes for both; all ids unique.

### Test-count deltas

| Suite | Before | After | Change |
|---|---|---|---|
| Frontend unit (`vitest`) | 177 | **187** | + `table-inspection-data.test.ts` (8); `table-inspection.test.ts` 23 → 25 |
| Standalone Playwright | 50 | 50 | assertions updated (missing-cell counts, 390 px, summary has no site list) |
| Built-book Playwright | 16 | 16 | assertions updated (`abide_table_inspection.json`, missing-cell counts, no site list) |
| Python (`unittest`) | 97 | **114** | `test_export_widget_data.py` 45 → 56 (+11); new `test_table_inspection_columns.py` (3); `test_build_portable_notebook.py` 22 → 25 (+3); `test_notebook_corrections.py` 23 → 23 (−`test_iqr…`, +`test_range_check…`) |

## Exact portable-generator exception used for saved sampling outputs

`PRESERVE_OUTPUT_IDS = frozenset({"7a1e5c93d204"})`. In `build_portable`,
code cells whose id is in that set are emitted with
`new["outputs"] = _preserved_outputs(src_cell)` (a list of
`_sanitise_output(o)` = `nbformat.from_dict` of `{output_type, [name], [text],
[data deep-copy], metadata={}}`, plus `execution_count: None` for
`execute_result`); every other code cell keeps `new["outputs"] = []`. All code
cells keep `execution_count = None`. `_assert_portable` enforces that exactly
this id has outputs, that its outputs are sanitised `display_data` pandas
tables (no `execution_count`, empty `metadata`, `SITE_ID` present), that it
carries no hide tag, and that repeated builds are byte-identical.

## Warnings, deviations, deferred / not-performed

1. **New third data artifact** — `abide_table_inspection.json` is a genuinely
   new committed generated input (not build output; it is a source asset the
   Vite app loads, exactly like `abide_histogram.json` /
   `abide_retention.json`). It is deterministic and regenerable with
   `python scripts/export_widget_data.py --refresh --artifact table-inspection`.
2. **`SUB_ID` now appears in one browser artifact.** WP01 Rule 11 says "avoid
   participant identifiers unless required"; WP10 §2 requires the full
   13-column list, which includes `SUB_ID`. It is confined to
   `abide_table_inspection.json`, emitted as the study-assigned integer id as a
   string, with an explicit two-name allowlist; `abide_histogram.json` and
   `abide_retention.json` remain `SUB_ID`-free and byte-identical.
3. **Canonical notebook re-executed end-to-end** (network: pinned ABIDE-II CSV)
   so committed `execution_count` / `metadata.execution` timestamps and outputs
   are current — the same practice as WP09. Figure bytes are deterministic
   within this environment (3× clean builds → identical 5-PNG hash set);
   cross-platform Matplotlib byte differences vs Linux CI remain a pre-existing,
   flagged risk (numpy/pandas/matplotlib unpinned).
4. **Pre-existing build warnings kept** — `logo.png` missing and
   `book/README.md` not in a toctree. Unchanged, out of scope.
5. **Pre-existing Vite 500 kB chunk note** — the Plotly bundle still trips
   Vite's advisory. Unchanged.
6. **Colab interactive rendering not machine-verified** — Google serves an app
   shell to headless automation (same as WP07–WP09); URL structure and the raw
   target are covered by the notebook-content tests.
7. **No live / remote checks** — by the stop condition: no push, no `main`
   merge, no deployment. The GitHub Pages site still serves the WP08/WP09
   content; hosting and the private/public distribution architecture were not
   touched. The generic sphinx-book-theme download control was not touched.

## Unresolved risks / needs Yoav

- **Private-repository distribution** (carried from WP09 §6/§13, unchanged
  here): the Chapter 1 Colab / raw-download buttons still target
  `github.com/yoavmp/ml-neuro-tutorials` on `main` and will break for
  non-collaborators if the repo goes private. Not in scope for WP10.
- Release / deployment of WP09 + WP10 is a separate, later WP after review.

## Confirmation of safety constraints

- **No merge to `main`, no deployment, no push, no force push** — nothing left
  the local `feature/course-pages-and-eda-trim` branch.
- **No destructive git command** — no `git reset --hard`, `git checkout -- <path>`,
  `git clean`, `git rebase`, `git revert`, tag or branch deletion.
- **No repository-setting / hosting / Pages / distribution-architecture change.**
- **The generic theme download control was not removed or changed.**
- **No generated build output committed** — `book/_build`,
  `book/.jupyter_cache`, `book/_static/widgets/app`,
  `interactive/node_modules`, `__pycache__`, and Playwright artifacts remain
  untracked / git-ignored (verified against the staged file list).
  `abide_table_inspection.json` is a source data asset, not build output.
- **No next practice notebook was created or started.**

## Key identifiers

| Item | Value |
|---|---|
| Branch | `feature/course-pages-and-eda-trim` |
| Checkpoint commit | `d9d3fc831e05c71ceaae785636ac3aeda9fd7740` (`checkpoint: before WP10`) |
| Checkpoint tag | `wp10-start` → `d9d3fc8` (annotated; no numeric suffix needed) |
| Implementation commit | `b5a2844` (`WP10: sampling summary + 13-column table, split sampling output, drop range checks`) — 18 files, +1696 / −456 |
| Report commit | `WP10 report: document sampling corrections and distribution trim` — adds `WPs/reports/WP10_REPORT.md` + `WPs/reports/WP10_EXACT_CHANGELOG.md` only; hash in the terminal summary |

## Instructions for reviewer

Paste this entire report (`WP10_REPORT.md`) into the ChatGPT conversation that
produced WP10. `WP10_EXACT_CHANGELOG.md` is the companion location-specific
before/after record.
