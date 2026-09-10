# WP10 — exact change log

Location-specific before/after entries. Notebook cells are referenced by their
stable `nbformat` cell id. It should be possible to review the substantive work
from this file without diffing raw notebook JSON.

Branch `feature/course-pages-and-eda-trim`; checkpoint `d9d3fc8` (tag
`wp10-start`); implementation commit `b5a2844`.

---

## 1. Git objects

| Item | Value |
|---|---|
| Checkpoint commit | `d9d3fc831e05c71ceaae785636ac3aeda9fd7740` — `checkpoint: before WP10` (adds `WPs/WP10_EDA_SAMPLING_AND_DISTRIBUTION_TRIM.md`, 1 file, +235) |
| Annotated tag | `wp10-start` → `d9d3fc8` (name free, no numeric suffix) |
| Implementation commit | `b5a2844` — `WP10: sampling summary + 13-column table, split sampling output, drop range checks` (18 files, +1696 / −456) |
| Report commit | `WP10 report: document sampling corrections and distribution trim` (adds the two report files only; hash in the terminal summary) |

Tags `wp01-start`…`wp09-start` and branch `feature/reusable-interactive-widgets`
untouched. No push, no merge, no force, no history rewrite.

---

## 2. `interactive/src/components/table-inspection.ts`  (WP10 §1 + §2)

### Header comment
- **Before:** "…no participant identifier — the artifact it reads
  (`abide_retention.json`) has no `SUB_ID` column."
- **After:** "…The artifact it reads (`abide_table_inspection.json`) carries
  every column of the 13-column curated table, including the two identifier
  columns `SITE_ID` and `SUB_ID`, because seeing the real rows — identifier
  column included — is the point of comparing `head()`, `tail()` and
  `sample()`."

### Imports / types
- `import { parseAbideRetentionData, type AbideRetentionData } from "../retention-data";`
  → `import { parseAbideTableInspectionData, type AbideTableInspectionData } from "../table-inspection-data";`
- `mount(args: MountArgs<TableInspectionConfig, AbideRetentionData>)`
  → `MountArgs<TableInspectionConfig, AbideTableInspectionData>`
- `WidgetComponent<TableInspectionConfig, AbideRetentionData>` +
  `parseData: parseAbideRetentionData`
  → `WidgetComponent<TableInspectionConfig, AbideTableInspectionData>` +
  `parseData: parseAbideTableInspectionData`

### Evidence summary (`render()`)
- **Before:**
  ```
  `${METHOD_LABEL[method]} shows ${view.rowCount} rows from ` +
  `${view.siteCount} acquisition ${siteWord} (${view.sites.join(", ")}); ` +
  `${view.missingCells} of ${view.totalCells} cells are missing.`
  ```
- **After:** the `(${view.sites.join(", ")})` segment is removed; a comment
  notes the site count is kept, the name list is not spelled out (visible in
  the `SITE_ID` column), and `view.sites` stays on `data-sites` for
  tests/state only.
  ```
  `${METHOD_LABEL[method]} shows ${view.rowCount} rows from ` +
  `${view.siteCount} acquisition ${siteWord}; ` +
  `${view.missingCells} of ${view.totalCells} cells are missing.`
  ```
- `table.dataset.sites = view.sites.join(",")` and all other `data-*` state
  attributes: **unchanged**. `summariseView` in `src/table-inspection.ts`:
  **unchanged** (still computes `sites` / `siteCount` / `missingCells` /
  `totalCells`).

---

## 3. NEW `interactive/src/table-inspection-data.ts`  (WP10 §2)

Component-owned Zod schema + `parseAbideTableInspectionData` for the new
artifact. Exports `IDENTIFIER_FIELDS = ["SITE_ID", "SUB_ID"] as const`.

`abideTableInspectionDataSchema` object shape: `schemaVersion` literal 1,
`activity` literal `"table-inspection"`, `rowCount` positive int, `source`
(`url`/`sha256` passthrough), `columnOrder` (non-empty string array),
`identifierFields` (`z.tuple([z.literal("SITE_ID"), z.literal("SUB_ID")])`),
`site` (`field` literal `SITE_ID`, `siteCount`, `sites[]`), `variables[]`
(`name`/`availableN`/`missingN`), `columns` (`z.record(z.array(cellValue))`).

`superRefine` enforces: column keys == `columnOrder` exactly; every column
aligned to `rowCount`; the two identifier columns present and non-empty
strings on every row; any **other** identifier-shaped column name
(`/(^|_)(ID|IDS|UID|GUID|MRN|SUB|SUBJECT|PARTICIPANT|NAME|EMAIL|DOB)($|_)/i`)
rejected; `variables` metadata covers exactly the non-identifier columns and
its `availableN`/`missingN` agree with the data; `site.sites` is the distinct
`SITE_ID` values in first-appearance order with correct totals summing to
`rowCount`.

---

## 4. `interactive/src/config.ts`

**Unchanged.** The `table-inspection` config schema (`tableInspectionConfig`,
`tableInspectionColumnRef`, `checkSemantics` block) already accepts any number
of `columns` and only requires `siteField` to be among them, which `SITE_ID`
still is. 13 column entries validate with no schema change.

---

## 5. `scripts/export_widget_data.py`  (WP10 §2)

### Module docstring
- "Two artifacts are produced" → "Three artifacts are produced"; new bullet
  describing `abide_table_inspection.json` (activity `table-inspection`, every
  column of the 13-column curated table in authority order, the two-name
  `SITE_ID`/`SUB_ID` identifier exception confined to this artifact).
- `--artifact {histogram,retention,all}` → `{histogram,retention,table-inspection,all}`;
  wording generalised ("all three artifacts", "Each named selector only ever
  touches its own file").

### New module constants
```python
TABLE_INSPECTION_IDENTIFIER_FIELDS = ("SITE_ID", "SUB_ID")
TABLE_INSPECTION_ARTIFACT_PATH = WIDGET_DATA_DIR / "abide_table_inspection.json"
```

### New helper `_identifier_label(value, field)`
Like `_site_label` but generic and used for both identifier fields: rejects
missing/blank; converts an integer-valued float to `int` before `str()` so
`SUB_ID` renders as `"29006"`, not `"29006.0"`.

### New `build_table_inspection_artifact(frame, allowed_columns, identifier_fields=TABLE_INSPECTION_IDENTIFIER_FIELDS)`
- Refuses any `identifier_fields` other than `("SITE_ID", "SUB_ID")`.
- **Derives** the displayed columns from `allowed_columns` (the curated
  authority) directly — `variable_names = [c for c in allowed_columns if c
  not in id_fields]` — so it cannot drift from the canonical list.
- Emits `SITE_ID` and `SUB_ID` via `_identifier_label` (non-empty strings);
  every other column via `column_to_json_values` (int / float / `null`),
  guarded by `_check_exportable` (non-identifier, curated, present in source).
- Returns `{schemaVersion, activity: "table-inspection", source, rowCount,
  columnOrder: list(allowed_columns), identifierFields: list(id_fields),
  site: {field, siteCount, sites}, variables: [ …11 non-identifier… ],
  columns: { …13… }}`.

### New `validate_table_inspection_artifact(artifact, allowed_columns, identifier_fields=…)`
Uses `_validate_common(…, "table-inspection")`; then checks
`identifierFields == ["SITE_ID","SUB_ID"]`, `columnOrder ==
list(allowed_columns)` exactly (order included), column keys == `columnOrder`,
the two identifier columns are non-empty strings, every other column is
non-identifier + curated + numeric/null (`_validate_numeric_column`),
`variables` metadata covers exactly the non-identifier curated columns, and
the `site` block is first-appearance order with totals summing to `rowCount`.

### `ARTIFACTS` registry
- Added `"table-inspection": ArtifactSpec("table-inspection", "table-inspection",
  TABLE_INSPECTION_ARTIFACT_PATH, build_table_inspection_artifact-lambda,
  validate_table_inspection_artifact-lambda)`.

### CLI
- `--artifact` `choices=("histogram", "retention", "all")` →
  `("histogram", "retention", "table-inspection", "all")`.

`build_artifact` / `build_retention_artifact` / `validate_artifact` /
`validate_retention_artifact` / `_summary` / `serialize` /
`HISTOGRAM_VARIABLES` / `RETENTION_VARIABLES` / `SITE_FIELD`: **unchanged**.

---

## 6. NEW `book/_static/widgets/data/abide_table_inspection.json`  (generated, `--refresh`)

- `activity` `table-inspection`, `schemaVersion` 1, `rowCount` 1114,
  `source.sha256` `537e541114884f63a2e736ba4d223a816dd013f701e56fb223ebe42e219e06f6`.
- `columnOrder` = `["SITE_ID","SUB_ID","DX_GROUP","AGE_AT_SCAN","SEX",
  "HANDEDNESS_CATEGORY","FIQ","VIQ","PIQ","CURRENT_MED_STATUS","SRS_TOTAL_RAW",
  "ADOS_G_TOTAL","ADI_R_SOCIAL_TOTAL_A"]` (identical to
  `book/config/eda_phenotype_columns.json`).
- `identifierFields` `["SITE_ID","SUB_ID"]`. `SITE_ID` 19 sites; `SUB_ID`
  1114 distinct string ids (`"29006"`…), 0 missing.
- `variables` meta for the 11 non-identifier columns (same availN/missingN as
  `abide_retention.json`: `HANDEDNESS_CATEGORY` 1091/23, `FIQ` 1015/99,
  `VIQ` 799/315, `PIQ` 872/242, `CURRENT_MED_STATUS` 991/123,
  `SRS_TOTAL_RAW` 785/329, `ADOS_G_TOTAL` 347/767,
  `ADI_R_SOCIAL_TOTAL_A` 302/812, `DX_GROUP`/`AGE_AT_SCAN`/`SEX` 1114/0).
- 73485 bytes, single trailing newline, `sort_keys` compact separators.
  Two `--refresh` runs byte-identical (`sha256 21d0e93207a5e15e5b6c893e5e54bec4b68d2f5d`).
- `--check --artifact all`: "OK … valid and canonical" for all three.

`book/_static/widgets/data/abide_histogram.json` and
`book/_static/widgets/data/abide_retention.json`: **byte-identical** to before
WP10 (`abide_retention.json` sha256 unchanged `4b46e6621d663d…`).

---

## 7. `book/_static/widgets/configs/table_inspection.json`  (WP10 §2)

| Field | Before | After |
|---|---|---|
| `description` | "…the curated ABIDE-II table…" | "…the **full 13-column** curated ABIDE-II table…" |
| `data` | `../data/abide_retention.json` | `../data/abide_table_inspection.json` |
| `columns` | 8 entries: `SITE_ID, DX_GROUP, AGE_AT_SCAN, SEX, HANDEDNESS_CATEGORY, FIQ, SRS_TOTAL_RAW, ADOS_G_TOTAL` | **13 entries** in canonical order: `SITE_ID` (Site), `SUB_ID` (Participant id), `DX_GROUP` (Diagnosis (1 = Autism, 2 = Control)), `AGE_AT_SCAN` (Age at scan (years)), `SEX` (Sex (1 = male, 2 = female)), `HANDEDNESS_CATEGORY` (Handedness (1 / 2 / 3)), `FIQ` (Full-scale IQ), `VIQ` (Verbal IQ), `PIQ` (Performance IQ), `CURRENT_MED_STATUS` (On medication (0 / 1)), `SRS_TOTAL_RAW` (SRS total (raw)), `ADOS_G_TOTAL` (ADOS-G total), `ADI_R_SOCIAL_TOTAL_A` (ADI-R social total) |
| `reflectionPrompts[0]` | "…Does the set of acquisition sites change?" | "…Does the **number** of acquisition sites change?" |

`schemaVersion`, `type`, `title`, `instructions`, `siteField`, `siteLabel`,
`methods`, `defaultMethod`, `rowCount` (`{min 5, max 15, default 8}`),
`sampleSeed` (7), `reflectionPrompts[1]`: **unchanged**.

---

## 8. Notebook `book/chapters/chapter_01/exercise_01.ipynb`  (76 → 73 cells)

### Cells removed (3: 2 markdown + 1 code) — WP10 §4

| id | was | tag |
|---|---|---|
| `58db4c1fc44e` | md `### Range checks and flagged values` — range-check intro, IQR definition `$$\mathrm{IQR} = Q_3 - Q_1$$`, the lower/upper fence equations, and the "we apply it to `AGE_AT_SCAN` … never `SUB_ID`" note | — |
| `7bf82a8cd5a9` | code — `age = phenotypes["AGE_AT_SCAN"]`; `q1,q3`; `iqr`; `lower_fence, upper_fence`; `flagged_age = phenotypes.loc[…]`; `print("IQR rule flags ages outside …")`; `print("56 of 1114 participants flagged for inspection")`; `flagged_age.sort_values(…).head(8)` table | (visible) |
| `c374c2ec5540` | md Think first "Evidence before editing a value" ("The flagged ages are roughly 33 to 64 years…") + its `{dropdown} Check your reasoning` (biologically-possible ages / sensitivity analysis / deletion cost) | — |

### Cells modified (source) — WP10 §3 + §4

| id | before → after |
|---|---|
| `373d8862-c5df-49a8-9295-a3e4fc073d0f` ("## What this notebook covers") | item 5 "…comparing across groups, **range checks**, and Pearson/Spearman correlations (with the correlation explorer)." → "…comparing across groups, and Pearson/Spearman correlations (with the correlation explorer)." |
| `7a1e5c93d203` (explanation before the Python equivalent) | **appended** a paragraph: *"The cell below is the Python code for each of these three sampling methods — run it yourself, and try changing `n` or `random_state`. It is here to show the code, not three more result tables to study: the activity above already compares what the methods return."* (rest of the cell unchanged) |
| `7a1e5c93d204` (sampling-methods code) | **source:** `# The same three views in Python. …` + `from IPython.display import display` + `display(phenotypes.head(8))` / `.tail(8)` / `.sample(8, random_state=0)` → `# Code to display each sampling method. head() and tail() are\n# deterministic; sample() draws rows at random, and passing random_state\n# makes one particular draw reproducible. Change n or random_state and\n# re-run to see what changes.\nfrom IPython.display import display\n\nn = 8\ndisplay(phenotypes.head(n))\ndisplay(phenotypes.tail(n))\ndisplay(phenotypes.sample(n, random_state=0))`.  **tags:** `["hide-input"]` → `["hide-output"]`.  **outputs:** regenerated by re-execution (3 `display_data` pandas tables; unchanged in form). |

### Cells re-executed

The whole notebook was re-executed end-to-end
(`jupyter nbconvert --to notebook --execute --inplace`, network: pinned
ABIDE-II CSV), 0 errors, so `execution_count` stays sequential (1…19) and
every committed output / `metadata.execution` timestamp is current. Numeric
results are unchanged from WP09 except that the range-check cell's output is
gone. `9b478759eff3` (Pearson 7×7), `80632a35b296` (FIQ violin, seeded
stripplot), `33d94597-…` ("Complete for all 13 variables" → 95 / 8.5 %),
`e6f7a8b9c0d1` (age histogram, `bins=25`): unchanged.

### Final counts (recounted from the file)

73 cells · 54 markdown · 19 code (9 visible, 7 `hide-input`, 2 `hide-cell`,
**1 `hide-output`**). `nbformat.validate` OK; ids unique; only tags anywhere
are `hide-input` / `hide-cell` / `hide-output`. No cell id was renamed; the 3
removed ids are gone, all others stable.

### Post-deletion section order (`## 5. Distributions and feature correlations`)

`### Explore numerical distributions` → histogram activity + `e6f7a8b9c0d1`
Python example → `### Reading a distribution` (`70fdfc764608`) →
`### Comparing a variable across groups` (`80632a35b296`) → site-composition
heatmap `283362766ec1` → Think first "Confounding and composition"
(`d9fa820679e0`) → **`### Pearson and Spearman correlations`** (`fd14e7f5d7a7`)
→ `9b478759eff3` matrix → `188d49e2ebf5` observations + Practical takeaway →
`### Explore correlations yourself` (`141d33ba05cc`) → Think first
`3efbb7fdf9a7` → Synthesis challenge `ae8f11ca42e5`. The confounding card
flows straight into the Pearson/Spearman heading; no dangling reference.

---

## 9. `scripts/build_portable_notebook.py`  (WP10 §3)

### Docstring
- The "drops Jupyter Book presentation tags/metadata (`hide-input` etc.)"
  bullet extended: "…and clears every code cell's stored output — with **one**
  deliberate, stable exception: the sampling-methods cell `7a1e5c93d204` keeps
  its three saved pandas table outputs, because the portable notebook does not
  embed the interactive head/tail/sample activity… Its outputs are sanitised
  of environment-specific execution metadata but are otherwise the
  deterministic pandas HTML/plain-text tables from the canonical notebook, and
  re-running the cell simply refreshes them."

### New constant
```python
PRESERVE_OUTPUT_IDS = frozenset({"7a1e5c93d204"})
```

### New helpers
- `_sanitise_output(out)` → `nbformat.from_dict({...})`: keeps `output_type`,
  `name`/`text` (stream), `data` (deep JSON copy of `text/html` + `text/plain`);
  drops per-output `execution_count`; `execute_result` gets
  `execution_count: None`; `metadata` blanked to `{}`.
- `_preserved_outputs(src_cell)` → `[_sanitise_output(o) for o in
  src_cell["outputs"]]`; `SystemExit` if the canonical cell has no output.

### `build_portable` — code-cell branch
- **Before:** `new["outputs"] = []` for every code cell.
- **After:** `new["outputs"] = _preserved_outputs(src_cell)` if
  `src_cell["id"] in PRESERVE_OUTPUT_IDS` else `[]`. `execution_count` still
  `None` for all.

### `_assert_portable`
- Per-cell loop: the "keeps stored outputs" `SystemExit` is now
  `if cell.get("outputs") and cell["id"] not in PRESERVE_OUTPUT_IDS`; added a
  `SystemExit` if any code cell keeps a non-`None` `execution_count`.
- New post-loop block: the `PRESERVE_OUTPUT_IDS` cell must exist, carry ≥1
  output, have no hide tag, and every output must be
  `display_data`/`execute_result`/`stream` with no `execution_count`, no
  transient `metadata`, and `SITE_ID` in the payload; and the set of
  code cells with outputs must equal `PRESERVE_OUTPUT_IDS` exactly.

`IFRAME_REPLACEMENTS` (still 4), `_rewrite_data_loading`, `_banner_cell`,
`_setup_cell`, `_setup_install_cell`, `convert_myst_directives`,
`DROP_ADMONITION_TITLES`, `serialize`: **unchanged**.

---

## 10. `book/downloads/chapter_01/exercise_01_portable.ipynb`  (regenerated, `--write`)

- **78 → 75 cells** (canonical 76 → 73; portable = 73 + 3 prepended
  banner/setup/install − 1 dropped "Run or download" admonition). 55 markdown +
  20 code.
- Cell `7a1e5c93d204`: source = the canonical WP10 source (comment invites
  changing `n`/`random_state`, `n = 8` once, three `display(...)` calls); no
  tags; `execution_count` `None`; **3 `display_data` outputs** (`text/html` +
  `text/plain` pandas tables, `metadata` `{}`, no `execution_count`).
- Every **other** code cell: `outputs == []`, `execution_count == None`, no
  tags.
- No `IQR` / range-check content anywhere. `CURATED_COLUMNS` literal (13),
  pinned CSV URL, no `../../config/`, no `requirements.txt`, no active
  `%pip`: unchanged.
- `--check`: "portable notebook is up to date (75 cells)". Repeated `--write`:
  no-op (byte-identical).

---

## 11. `scripts/smoke_portable_notebook.py`  (WP10 §4)

| Location | Before | After |
|---|---|---|
| docstring bullet | "the IQR range-check still flags 56 of 1114 ages." | "the complete-case retention example still reports all 13 variables." |
| docstring bullet | "loads as 1114 x 13 (the WP09 curated slice)" | "loads as 1114 x 13 (the curated slice)" |
| `EXPECTED_SUBSTRINGS` | `("Data table shape: (1114, 13)", "56 of 1114 participants flagged")` | `("Data table shape: (1114, 13)", "Complete for all 13 variables")` |

Out-of-repo run: "OK: portable notebook executed cleanly (20 code cells, key
values matched)" (was 21 code cells).

---

## 12. Tests

### `interactive/tests/table-inspection.test.ts`
- `describe("table-inspection against the committed abide_retention.json")` →
  `describe("… abide_table_inspection.json")`; `loadArtifact` reads the new
  file and types `columnOrder` / `identifierFields`.
- `DISPLAY` 8 columns → **13** (canonical order, `SUB_ID` included).
- **Removed** test: "head(8) is one site with no missing display cells;
  tail(8) …" (`missingCells` 0 / 19 over 8 columns).
- **Added** tests: "carries every one of the 13 curated columns in canonical
  order, SUB_ID included" (`columnOrder`, `identifierFields`, full `SUB_ID`
  string column); "head(8) and tail(8) each stay inside one site; the summary
  counts all 13 columns" (`head` 1 site / `24` missing / `8*13`; `tail` 1 site
  / `35` missing / `8*13`); "sample(8, seed 7) spans 8 sites…" now `17`
  missing / `8*13`; "an 11-row view inspects 11 * 13 = 143 cells".
- Net: 23 → **25** tests.

### NEW `interactive/tests/table-inspection-data.test.ts`  (8 tests)
`IDENTIFIER_FIELDS` value; committed artifact parses (13 columns, `rowCount`
1114, 19 sites); rejects a non-allowlisted identifier-shaped column
(`SCANNER_ID`); rejects a missing `SUB_ID` column; rejects a `null` in an
identifier column; rejects `columnOrder` / column-keys disagreement; rejects
the wrong `activity`; rejects an unaligned column.

### `interactive/tests/config.test.ts`
- `validTableInspection` fixture `data`: `../data/abide_retention.json` →
  `../data/abide_table_inspection.json` (string only; not filesystem-checked).
  Test count unchanged (57).

### `interactive/e2e/table-inspection.spec.ts`
- head(8): `data-missing-cells "0"` → `"24"`; **added** `data-total-cells
  "104"` and an exact summary-string assertion
  (`"head() shows 8 rows from 1 acquisition site; 24 of 104 cells are
  missing."`) plus `not.toContain("ABIDEII-")` / `not.toMatch(/\([A-Z]/)`.
- tail(8): `data-missing-cells "19"` → `"35"`.
- sample(8, seed 7): `data-missing-cells "7"` → `"17"`.
- "missing cells …" test: `data-missing-cells "19"` → `"35"`;
  `missing.count()` `19` → `35`.
- "row-count control": `data-total-cells "120"` (15×8) → `"195"` (15×13);
  comment updated.
- narrow-viewport test: `375` px → **`390`** px (title + all width asserts);
  **added** `expect(thead th).toHaveCount(13)`.
- Test count unchanged (10 per base × … = 50 total).

### `interactive/e2e-book/chapter01.spec.ts`
- table-inspection describe only: `responses.find(… "/data/abide_retention.json")`
  → `"/data/abide_table_inspection.json"`; head(8) `data-missing-cells "0"` →
  `"24"`; **added** `data-total-cells "104"` + `thead th` count 13;
  sample(8) `data-missing-cells "7"` → `"17"`; summary read once, assert
  `toContain("8 acquisition sites")` **and** `not.toContain("ABIDEII-")`.
- Retention / correlation describes (their own `abide_retention.json`
  assertions): **unchanged**. Test count unchanged (16 total).

### `tests/test_notebook_corrections.py`
- `test_what_this_notebook_covers_kept_and_numpy_not_a_prerequisite`: **added**
  `self.assertNotIn("range check", covers.lower())`.
- `test_think_first_then_explanation_then_collapsed_python_equivalent` renamed
  → `test_think_first_then_explanation_then_code_to_show_each_method`;
  now asserts the explanation contains "Python code for each of these three
  sampling", the cell has `hide-output` and **not** `hide-input`, `"n = 8"`,
  `"Change n or random_state"`, and `phenotypes.head(n)` / `.tail(n)` /
  `.sample(n, random_state=0)`.
- `test_cell_and_visibility_counts`: `76 → 73` cells, `20 → 19` code,
  `{"visible": 10, "hide-input": 8, "hide-cell": 2, "hide-output": 0}` →
  `{"visible": 9, "hide-input": 7, "hide-cell": 2, "hide-output": 1}`.
- `test_iqr_range_check_still_flags_56`: **removed**.
- **Added** `test_range_check_subsection_fully_removed`: ids `58db4c1fc44e` /
  `7bf82a8cd5a9` / `c374c2ec5540` absent; the strings `Range checks and
  flagged values`, `range check`, `IQR`, `interquartile`, `lower_fence`,
  `upper_fence`, `flagged_age`, `1.5`, `56 of 1114`, `participants flagged`
  absent from md + code; histogram/Pearson cells + heading retained.
- Net: 23 → 23 tests.

### `tests/test_build_portable_notebook.py`
- `test_no_iframe_or_static_or_directive_or_hidetag`: the
  `assertEqual(cell.get("outputs"), [])` is now guarded by
  `if cell["id"] not in bpn.PRESERVE_OUTPUT_IDS`.
- **Added** `test_only_the_sampling_cell_keeps_saved_outputs`,
  `test_sampling_cell_keeps_three_sanitised_pandas_tables` (3 `display_data`
  outputs, `metadata` `{}`, no `execution_count`, `SITE_ID` + `SUB_ID` in the
  plain text, source has `n = 8` + `Change n or random_state`),
  `test_no_range_check_or_iqr_remnant`.
- Net: 22 → 25 tests.

### `tests/test_export_widget_data.py`
- New fixtures `TABLE_INSPECTION_FIXTURE_CSV` (6 rows / 3 sites,
  `SUB_ID`+`SITE_ID` string ids), `TABLE_INSPECTION_AUTHORITY`
  (`["SITE_ID","SUB_ID","DX_GROUP","AGE_AT_SCAN","FIQ"]`),
  `build_table_inspection_frame()`.
- **Added** `BuildTableInspectionArtifactTests` (6): happy-path shape /
  metadata, null+code preservation, round-trip + validate, rejects a third
  identifier field, rejects an identifier-shaped non-allowlisted variable,
  rejects a missing identifier value.
- **Added** `ValidateTableInspectionArtifactTests` (5): good passes, catches
  `columnOrder` drift, catches an identifier-shaped extra column, catches a
  `null` in an identifier column, catches the wrong `activity`.
- `ArtifactRegistryTests`: `test_both_modes_are_registered_and_distinct` →
  `test_all_three_artifacts_are_registered_and_distinct`
  (`{"histogram","retention","table-inspection"}`, 3 distinct filenames);
  `test_selector_scopes_to_one_artifact` gains the `table-inspection`
  selector and the 3-element `all`.
- `test_committed_artifacts_pass_their_own_validators` now auto-covers the new
  spec (iterates `ARTIFACTS.values()`).
- Net: 45 → 56 tests.

### NEW `tests/test_table_inspection_columns.py`  (3 tests)
`authority` is the 13-column list (starts `SITE_ID`, contains `SUB_ID`);
`[c["name"] for c in config["columns"]] == authority` and every column has a
label, `config["data"] == "../data/abide_table_inspection.json"`,
`config["siteField"] == "SITE_ID"`; artifact `activity` `table-inspection`,
`columnOrder == authority`, keys match, `identifierFields
["SITE_ID","SUB_ID"]`, `rowCount` 1114, `SITE_ID`/`SUB_ID` complete string
columns of length 1114.

### `tests/test_book_structure.py`
**Unchanged** (7 tests).

### Totals
Frontend unit 177 → **187**; standalone Playwright 50 → 50; built-book
Playwright 16 → 16; Python `unittest` 97 → **114**.

---

## 13. Commands run (no repository mutation beyond local commits)

```
git add WPs/WP10_EDA_SAMPLING_AND_DISTRIBUTION_TRIM.md
git commit -m "checkpoint: before WP10"                  # d9d3fc8
git tag -a wp10-start -m "Checkpoint before WP10 (sampling corrections and distribution trim)"
# baseline: python -m unittest discover -s tests ; (cd interactive && npm run test && npm run test:e2e && npm run test:e2e:book)
#           python scripts/build_portable_notebook.py --check ; python scripts/export_widget_data.py --check --artifact all
#           rm -rf book/_build ; jupyter-book build book ; python scripts/smoke_portable_notebook.py
# … implementation (nbformat edits, export_widget_data.py, table-inspection-data.ts, component, configs, generator, tests) …
jupyter nbconvert --to notebook --execute --inplace book/chapters/chapter_01/exercise_01.ipynb
python scripts/export_widget_data.py --refresh --artifact all
python scripts/export_widget_data.py --check --artifact all
python scripts/build_portable_notebook.py --write
rm -rf book/_build ; jupyter-book build book              # 2 warnings, no *.err.log
for i in 1 2 3 ; do rm -rf book/_build ; jupyter-book build book ; done   # identical 5-PNG hash set
python scripts/smoke_portable_notebook.py                 # out of repo, 20 code cells
python -m unittest discover -s tests                      # 114 / 114
(cd interactive && npm run test && npm run test:e2e && npm run test:e2e:book)   # 187 / 50 / 16
git add -A ; git reset -- WPs/reports/
git commit -m "WP10: sampling summary + 13-column table, split sampling output, drop range checks"   # b5a2844
git add WPs/reports/WP10_REPORT.md WPs/reports/WP10_EXACT_CHANGELOG.md
git commit -m "WP10 report: document sampling corrections and distribution trim"
```

No `git reset --hard`, `git checkout -- <path>`, `git clean`, `git rebase`,
`git revert`, `git push`, `git merge`, `--force`, or `--force-with-lease`. No
repository setting, secret, branch-protection rule, Pages configuration, or
distribution architecture changed. No `book/_build`, `book/.jupyter_cache`,
`book/_static/widgets/app`, `interactive/node_modules`, `__pycache__`, or
Playwright artifact staged. `book/_static/widgets/data/abide_table_inspection.json`
is a committed source data asset (loaded by the Vite app at runtime like the
other two artifacts), not build output.
