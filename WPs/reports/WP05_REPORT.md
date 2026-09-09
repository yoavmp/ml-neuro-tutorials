# WP05 implementation report

## Outcome

Status: **SUCCESS**

The Chapter 1 EDA notebook's distributions/correlations section is complete: a
22‑cell teaching sequence (4 static figures) covering reading a distribution,
comparing across groups, range checks and flagged values, Pearson/Spearman with
a pairwise‑complete‑N matrix, mixed‑type associations, and a synthesis
challenge — every subsection ending in an active question with a MyST‑dropdown
answer. A third browser‑native activity, `eda-correlation`, is implemented on the
WP02–WP04 runtime with pure unit‑tested correlation maths, is config‑driven and
identifier‑free, **reuses `abide_retention.json`** (no new data artifact, the
exporter is untouched), and is embedded in the notebook via `nbformat`. All
WP04 baseline commands and every new unit / standalone‑Playwright /
built‑book‑Playwright test pass; the histogram and retention activities are
unchanged and green; Jupyter Book builds with no `*.err.log`.

Every quantitative claim in the notebook prose and in the tables below was
computed directly from the pinned ABIDE‑II CSV with pandas/scipy and is a
**verified dataset fact**; sentences about what those numbers *mean* for an
analysis are flagged as **teaching interpretation**.

## Git safety checkpoint

- Branch: `feature/reusable-interactive-widgets`
- Starting HEAD: `c7cd18b` ("WP04 report: document results")
- Checkpoint commit: `444aa1495a3b4b48b7b3b3078df7be4ab120199a` ("checkpoint: before WP05")
- Checkpoint tag: `wp05-start` (annotated; points at `444aa14`)
- Retraction guidance: identify the checkpoint only; do **not** reset/revert
  here. To undo WP05, `git revert` the implementation commit
  `004a3fde204d948290498bae51a417da6c192d1c` and the report commit, or reset to
  `444aa14` / tag `wp05-start`. Leave `wp01-start`…`wp04-start` intact.

The checkpoint captured the two pre‑existing legitimate working‑tree changes
only: the WP‑process update to `WPs/README.md` and the new WP brief
`WPs/WP05_DISTRIBUTIONS_AND_CORRELATIONS.md`. No build output, caches,
`.DS_Store`, credentials, or private data were present or committed. The raw
ABIDE CSV was not committed.

## WP04 baseline (run before any WP05 change)

| Command | Result |
|---|---|
| `npm ci` | OK (100 pkgs) |
| `npm run typecheck` | OK, 0 errors |
| `npm run test:unit` | 100/100 |
| `npm audit --omit=dev` | 0 vulnerabilities |
| `npm run build` | OK (Vite 500 kB Plotly chunk warning only) |
| `python scripts/export_widget_data.py --check` | both artifacts valid + canonical |
| `python -m unittest … test_export_widget_data` | 45/45 |
| `npx playwright test` (standalone) | 26/26 |
| `rm -rf book/_build && jupyter-book build book` | exit 0, 9 warnings, no `*.err.log` |
| `npm run test:e2e:book` | 6/6 |

Baseline fully green; no regressions to understand.

## Inspected data findings

Reproducible inspection scripts (`inspect_abide.py`, `proto_cells.py`) were run
against the pinned source — `…/nh2020-curriculum/e4eed3c…/…/abide2_phenotypic.csv`,
SHA‑256 `537e541114884f63a2e736ba4d223a816dd013f701e56fb223ebe42e219e06f6`
(561,572 bytes; hash re‑verified) — restricted to the curated 39‑column subset
(1,114 rows). They were **not** committed (they became neither a shipped test
nor a helper). All widget‑relevant figures were also cross‑checked directly
against the committed `abide_retention.json` in `tests/correlation.test.ts`.

### Category codes — verified against the ABIDE‑II Data Legend

Extracted verbatim from the legend PDF
(<https://fcon_1000.projects.nitrc.org/indi/abide/ABIDEII_Data_Legend.pdf>):

| Variable | Legend coding | Counts in this sample |
|---|---|---|
| `DX_GROUP` | `1=Autism; 2=Control` | 521 / 593, 0 missing |
| `SEX` | `1=male; 2=female` | 856 / 258, 0 missing |
| `HANDEDNESS_CATEGORY` | `1=right handed; 2=left handed; 3=mixed handed` | 957 / 68 / 66, 23 missing |
| `CURRENT_MED_STATUS` | `0=no; 1=yes` | 824 / 167, 123 missing |
| `EYE_STATUS_AT_SCAN` | `1=open; 2=closed` | 842 / 201, **plus 70 rows coded `0`** (not in the legend), 1 missing |

Only `DX_GROUP` and `SEX` labels are surfaced to students (the correlation
grouping control and the group‑comparison / crosstab cells). The `EYE_STATUS`
code‑0 discrepancy is a dataset fact worth noting but is not used anywhere in
the new material.

### Numeric variables (curated set) — distribution facts

`AGE_AT_SCAN` 5.13–64, skew **+2.44**, 0 missing. `FIQ` 49–151, skew −0.35,
n 1015. `VIQ` n 799, `PIQ` n 872. `SRS_TOTAL_RAW` 0–199, mean 55.3 / median 43,
skew +0.53, n 785. `SCQ_TOTAL` n 293, `ADOS_G_TOTAL` n 347, `ADOS_2_TOTAL`
n 269. The behavioural totals therefore describe 25–35 % of the cohort each.

### Range / outlier check (`AGE_AT_SCAN`)

IQR rule `Q3 + 1.5·IQR` upper fence = **31.06 y**; **56 of 1,114** participants
flagged (ages ~31–64), concentrated at adult‑recruiting sites (e.g.
`ABIDEII-BNI_1`). *Interpretation:* biologically plausible adults, not errors —
used to teach "flagged for inspection, not automatically wrong".

### Diagnosis composition by site & sex

19 acquisition sites. `ABIDEII-KUL_3` and `ABIDEII-NYU_2` are **100 % Autism**;
`ABIDEII-KKI_1` is 26.5 % Autism / 73.5 % Control; overall 521 / 593. `SEX` and
`DX_GROUP` are **not independent**: 70.2 % of females are Control vs ~48 % of
males; **Cramér's V(SEX, DX_GROUP) = 0.184**. *Interpretation:* site and sex are
both candidate confounders for any Autism‑vs‑Control comparison.

### Verified correlation findings (Pearson `r`, Spearman `ρ`, pairwise‑complete N)

| Pair | `r` | `ρ` | N | Within‑group (`DX_GROUP` 1 / 2) | Teaching role — **interpretation** |
|---|---|---|---|---|---|
| `FIQ` – `VIQ` | 0.8330 | 0.8304 | 796 | 0.841 / 0.785 | **Part–whole composite** — FIQ is derived from VIQ+PIQ; not an independent biological result. Stable across groups. |
| `FIQ` – `PIQ` | 0.8376 | 0.8047 | 783 | 0.846 / 0.807 | second composite pair |
| `VIQ` – `PIQ` | 0.5166 | 0.4933 | 786 | 0.515 / 0.446 | genuine moderate association between two *separate* subscores (not part–whole of each other) |
| `SRS_TOTAL_RAW` – `SRS_COMMUNICATION_RAW` | 0.981 | 0.978 | 785 | — | **Arithmetic part–whole** — the subscale is summed into the total; equal to the total in 755/757 fully‑observed rows. Reporting it as a finding is circular. |
| `SRS_TOTAL_RAW` – `SCQ_TOTAL` | 0.8421 | 0.8174 | 289 | 0.543 (n 151) / 0.413 (n 138); by site OHSU 0.22 vs ~0.85 | **Group‑ and site‑sensitive** — the strong overall value is inflated by the gap *between* diagnostic groups. |
| `FIQ` – `SRS_TOTAL_RAW` | −0.2404 | −0.2358 | 778 | −0.026 (n 372) / −0.056 (n 406) | **Overall association ≈ entirely between‑group** — near zero within each group. Interactive **default pair**. |
| `ADOS_G_TOTAL` – `ADOS_2_TOTAL` | 0.8815 | 0.8615 | **81** | — | **Differing pairwise N** — high `r` on only 81 of 1,114 (participants given both ADOS versions). |
| `AGE_AT_SCAN` – `FIQ` | 0.0084 | −0.0136 | 1015 | 0.063 / −0.040 | **Weak / null** on the largest available N; stays ~0 within groups. |
| `AGE_AT_SCAN` – `ADOS_G_TOTAL` | −0.2290 | −0.3321 | 347 | — | **Pearson ≠ Spearman** — age is right‑skewed (skew +2.44), so the rank coefficient is stronger; look at the scatter. |

### Simpson's paradox / confounding

Not forced (WP §2.6). There is strong **dilution** (`FIQ`–`SRS` −0.24 → ~0
within group; `SRS`–`SCQ` 0.84 → ~0.5) but no clean overall sign‑flip. The
section teaches confounding with (a) the site × diagnosis composition heatmap
and (b) the grouped `FIQ` vs `SRS_TOTAL_RAW` view in the explorer, exactly as
the WP allows when no clean paradox exists.

## Teaching structure and notebook cells added

Continues the existing unnumbered `###` / `####` heading style of `## 5.
Distributions and feature correlations`. 22 cells inserted **after** the
histogram `### Questions` cell (id `0658e691-…`); no existing cell, id, tag or
output changed (`git diff` = **+483 / −0** on the notebook). 12‑hex ids. 4 new
static figures (WP limit 5). Estimated **30–40 min** of teaching after the
missing‑data material.

| # | Cell | Type / tag | Purpose |
|---|---|---|---|
| A1 | `### Reading a distribution` | md | shape/center/spread/skew/multimodality/floor–ceiling/implausible; bin choice changes appearance not data |
| A2 | `distribution_summary` | code `hide-input` | `describe()` + available/missing N for 5 justified variables (no 39‑column wall) |
| A3 | `#### Question: read the summary` + dropdown | md | skew from mean>median; "wrong" vs "uncertain/unrepresentative"; discrete vs continuous |
| B1 | `### Comparing a variable across groups` | md | why violin+points beats a bar of means; legend‑verified `DX_GROUP` labels on a copy |
| B2 | FIQ by diagnosis | code `hide-input` | **Fig 1** violin + jittered strip, n annotated on the axis; `observed=True` groupby summary |
| B3 | short prose | md | overlap; colours are labels not good/bad; site as a suspect confounder |
| B4 | site × diagnosis composition | code `hide-input` | **Fig 2** normalized crosstab heatmap (sites ordered by size) |
| B5 | `#### Question: confounding and composition` + dropdown | md | find the skewed sites; 100 %‑Autism sites; name a participant‑level confounder (sex) |
| C1 | `### Range checks and flagged values` | md | IQR rule flags for **inspection**, not deletion; deletion needs coding checks + sensitivity analysis |
| C2 | AGE_AT_SCAN IQR flag | code `hide-input` | fence, flagged count, `head(8)` shown via `SITE_ID` + age + diagnosis label only, `reset_index(drop=True)` — **no `SUB_ID`** |
| C3 | `#### Question: evidence before editing a value` + dropdown | md | impossible vs unusual; what to verify; effect on those sites |
| D1 | `### Pearson, Spearman, and the sample behind each number` | md | compact P vs S table (linear/outlier‑sensitive vs monotone/robust; neither causal); "each cell = a different subset" |
| D2 | Pearson matrix | code `hide-input` | **Fig 3** masked lower‑triangle heatmap on 8 justified numerics (incl. an SRS subscale for the part–whole point) |
| D3 | pairwise‑N matrix | code `hide-input` | **Fig 4** same variables, same mask, N per cell |
| D4 | discussion | md | one genuine assoc (`SRS`–`SCQ` 0.84, but see grouping); one part–whole (`SRS`–subscale 0.98; `FIQ`–`VIQ` 0.83); one small‑N cell (`SCQ`–`ADOS_G` 0.06 on N 71 vs `AGE`–`FIQ` N 1015); Pearson vs Spearman worked pair (`AGE`–`ADOS_G` −0.23 vs −0.33); explicit "no p‑value fishing" |
| D5 | `### Explore correlations yourself` + `<iframe>` | md | intro + embedded `eda-correlation`, explains why no trend line |
| D6 | `#### Question: use the explorer` + dropdown | md | FIQ–VIQ definitional; ADOS pair small n; FIQ–SRS overall vs within‑group |
| E1 | `### When a correlation matrix is the wrong tool` | md | the mixed‑type table (numeric–numeric / numeric–categorical / categorical–categorical / ordered categorical) |
| E2 | `sex_by_diagnosis` crosstab | code | counts + within‑sex row proportions |
| E3 | Cramér's V | code `hide-cell` | optional sidebar, revealable; `scipy.stats.chi2_contingency` |
| E4 | `#### Question: choosing an association measure` + dropdown | md | why `corr()` on `SEX` codes is wrong; independence check; `ADOS_MODULE` is not ordered |
| F1 | `### Synthesis challenge` + dropdown | md | 6‑step task (predict → pairwise N → P vs S → group → part–whole → two sentences) with a **model reasoning process**, not one prescribed conclusion |

All 5 dropdown answers and the model‑reasoning block render as collapsible
cards in the built book (verified: 0 literal ```` ```{dropdown} ```` strings,
dropdown cards present). `hide-input` / `hide-cell` toggles render as
"Show code cell source". `phenotypes` is never mutated for labels — diagnosis
and sex labels are built on copies with `.astype("int64").map({...})`.

## Interactive correlation design

**Activity `eda-correlation`**, registered in `components/registry.ts`, on the
existing config→data→component runtime (no runtime changes).

- **Data:** reuses `book/_static/widgets/data/abide_retention.json` — it already
  carries aligned, identifier‑free `AGE_AT_SCAN`, `FIQ`, `VIQ`, `PIQ`,
  `ADOS_G_TOTAL`, `ADOS_2_TOTAL`, `SRS_TOTAL_RAW`, `SCQ_TOTAL` plus the
  `DX_GROUP` / `SEX` codes the grouping needs. **`scripts/export_widget_data.py`
  and both committed artifacts are byte‑for‑byte unchanged.**
- **Config `configs/eda_correlation.json`:** title / description / instructions;
  8 numeric variables + labels; `defaultX = FIQ`, `defaultY = SRS_TOTAL_RAW`
  (distinct, pedagogically useful — a real moderate negative that collapses
  within groups), `defaultMethod = pearson`; `groupings` = `diagnosis`
  (`DX_GROUP`: 1→Autism, 2→Control) and `sex` (`SEX`: 1→Male, 2→Female) with
  legend‑verified mappings; 5 reflection prompts (prediction, differing‑N,
  part–whole, within‑group, association≠causation). The component always adds a
  "No grouping" option itself.
- **Config validation** (`config.ts` `checkSemantics`): ≥2 variables, unique
  names, `defaultX`/`defaultY` present and **distinct**, `defaultMethod ∈
  {pearson, spearman}`, unique grouping keys, no `"none"` key, grouping `field`
  not also a selectable variable, unique grouping value codes, non‑empty
  labels; the shipped file is loaded and validated in a unit test.
- **Pure calculations — `src/correlation.ts` (no DOM / Plotly / fetch):**
  `pairwiseComplete` (rows where both are finite; returns x/y arrays, n and an
  `{total, x, y, either}` missing breakdown); `pearson`; `averageRanks`
  (tie → mean rank); `spearman` (Pearson on average‑rank transforms);
  `computeCorrelation` (overall + optional per‑group, groups in the config
  `values` order, stable key `String(code)`); `assertAligned`. Edge cases are
  **null + a readable reason**, never a throw: `REASON_TOO_FEW` (n<3),
  `REASON_NO_VARIANCE` (constant column). The only throw is a column‑length
  mismatch (a data‑integrity bug). Non‑finite / non‑number cells are treated as
  missing, not as data.
- **Component `components/correlation.ts`:** labelled `<select>`s for X, Y,
  method, "Colour by"; scatter (`scatter` markers; Okabe–Ito group colours,
  deliberately not a good/bad ramp; opacity; **no regression line** — one line
  would misrepresent a rank correlation and a grouped view); a stats line
  (method, `r` to 2 dp, pairwise `n` of total), a missing line
  (`X missing · Y missing · excluded because either is missing: k of total`), a
  per‑group line when grouped. **Same‑variable** X=Y is handled: an explicit
  note, `data-r="null"`, `data-n="0"`, empty plot, render‑count still bumps.
  `Plotly.react()` on every change. Hover shows only the two plotted values —
  **no `customdata`, no identifier**. Native keyboard‑operable controls;
  responsive; light/dark via `prefers-color-scheme`.
- **Machine‑testable attributes** on `[data-testid="correlation-plot"]`:
  `data-active-x`, `-y`, `-method`, `-group`; `data-n`; `data-r` (4 dp or
  `"null"`); `data-excluded-n`; `data-trace-count`; `data-group-count`;
  `data-render-count`; `data-same-variable`.

### Correlation activity defaults & shipped‑data reference values

Default `FIQ` × `SRS_TOTAL_RAW`, Pearson, no grouping, on the committed
`abide_retention.json` (cross‑checked with pandas, asserted in
`tests/correlation.test.ts` and both Playwright suites):

| Selection | Pearson | Spearman | pairwise `n` (excluded) |
|---|---|---|---|
| `FIQ` × `SRS_TOTAL_RAW` **(default)** | −0.2404 | −0.2358 | 778 (336) |
| → coloured by diagnosis | Autism −0.03 (n 372) · Control −0.06 (n 406) | | |
| `FIQ` × `VIQ` | 0.8330 | 0.8304 | 796 |
| `ADOS_G_TOTAL` × `ADOS_2_TOTAL` | 0.8815 | 0.8615 | **81** of 1,114 |
| `AGE_AT_SCAN` × `FIQ` | 0.0084 | −0.0136 | 1,015 |
| `AGE_AT_SCAN` × `ADOS_G_TOTAL` | −0.2290 | −0.3321 | 347 |

### Embedding

`exercise_01.ipynb` edited with `nbformat` only. One Markdown cell with a short
intro and:

```
<iframe title="Interactive ABIDE-II feature correlation explorer"
  src="../../_static/widgets/app/index.html?config=../configs/eda_correlation.json"
  loading="lazy" width="100%" height="820" style="width: 100%; border: none;"></iframe>
```

placed in D5, after the static Pearson and pairwise‑N matrices. Histogram and
retention iframes, the Colab button, all prior prose and figures are untouched.

## Files changed

Implementation commit `004a3fde204d948290498bae51a417da6c192d1c`
(13 files, +2291 / −8):

| Path | Change |
|---|---|
| `interactive/src/correlation.ts` | **new** — pure Pearson/Spearman/pairwise‑complete/grouped maths |
| `interactive/src/correlation-data.ts` | **new** — Zod schema reusing `abide_retention.json` (alignment + identifier rejection; no `site` block) + `numericColumn` helper |
| `interactive/src/components/correlation.ts` | **new** — the `eda-correlation` component |
| `interactive/src/components/registry.ts` | register `correlationComponent` |
| `interactive/src/config.ts` | add `eda-correlation` schema member + `checkSemantics` branch |
| `book/_static/widgets/configs/eda_correlation.json` | **new** — activity config |
| `interactive/tests/correlation.test.ts` | **new** — 25 tests (maths + pandas/scipy cross‑checks + committed‑artifact checks) |
| `interactive/tests/correlation-data.test.ts` | **new** — 6 data‑schema tests |
| `interactive/tests/config.test.ts` | +12 `eda-correlation` config tests |
| `interactive/e2e/correlation.spec.ts` | **new** — standalone Playwright spec (×2 base URLs = 14 tests) |
| `interactive/e2e-book/chapter01.spec.ts` | +3 built‑book correlation tests; histogram/retention tests unchanged |
| `interactive/README.md` | `eda-correlation` section, code‑label note, regression table, preview URL, status bumped to WP05 |
| `book/chapters/chapter_01/exercise_01.ipynb` | +22 cells (distributions/correlations sequence + explorer iframe); +483 / −0 |

**Not changed:** `scripts/export_widget_data.py`, both `abide_*.json` data
artifacts (SHA‑256 identical), `.github/workflows/deploy.yml`, `requirements.txt`,
`book/_config.yml`, `_toc.yml`, the histogram/retention source and tests.

Generated / not committed (verified absent from `git status`):
`book/_static/widgets/app/`, `book/_build/`, `interactive/node_modules/`,
`interactive/test-results/`, `**/__pycache__/`.

## Tests

| Command / test | Result | Evidence |
|---|---|---|
| `npm run typecheck` | **PASS** | `tsc --noEmit` exit 0 (strict, `exactOptionalPropertyTypes`, `noUncheckedIndexedAccess`) |
| `npm run test:unit` | **PASS** | **143 passed** (was 100): `correlation.test.ts` 25, `correlation-data.test.ts` 6, `config.test.ts` 46 (+12), histogram 14, histogram‑data 7, retention 16, retention‑data 10, urls 19 |
| `npm audit --omit=dev` | **PASS** | 0 vulnerabilities |
| `npm run build` | **PASS** | 22 modules; `index-*.js` 1,484.72 kB (gzip 495.89 kB); Vite 500 kB chunk warning only (Plotly, carried from WP02) |
| `python -m unittest … test_export_widget_data` | **PASS** | 45/45, no network (exporter untouched) |
| `python scripts/export_widget_data.py --check` | **PASS** | both artifacts valid + canonical; retention sha256 `6b296565…`, histogram `93761624…` (unchanged) |
| `npx playwright test` (standalone `e2e/`) | **PASS** | **40 passed** (was 26): `correlation.spec.ts` 14, histogram 8, retention 10, runtime 8 |
| `rm -rf book/_build && jupyter-book build book` | **PASS** | exit 0, "build succeeded, 9 warnings" (all pre‑existing: syllabus toctree title, README not in toctree, missing `logo.png`, cosmetic IPKernelApp TCP notice); no `*.err.log` |
| `find book/_build -name '*.err.log'` | **PASS** | empty |
| `npm run test:e2e:book` (built book `e2e-book/`) | **PASS** | **9 passed** (was 6): 3 histogram (unchanged) + 3 retention (unchanged) + 3 correlation |
| Notebook `nbformat.validate` + unique‑id check | **PASS** | 79 cells, all ids unique, valid; +22 vs 57 |
| Independent pandas/scipy cross‑check | **PASS** | every coefficient / N in prose + `correlation.test.ts` computed directly on the pinned CSV / committed artifact |
| Visual inspection (built Chapter 1 page, Playwright screenshots) | **PASS** | 4 new figures render with readable labels + non‑empty data; flagged‑age table shows no `SUB_ID`; dropdowns render as cards; explorer default + grouped views correct (see below) |

Built‑book Playwright asserts for `eda-correlation`: iframe present under the
real Chapter 1 route; `configs/eda_correlation.json` + `data/abide_retention.json`
HTTP 200; defaults `FIQ`/`SRS_TOTAL_RAW`/pearson/none with `data-n="778"`,
`data-r="-0.2404"`; changing X/Y changes the plotted point count (778 → 796 →
81) and geometry; Pearson→Spearman on `AGE_AT_SCAN`×`ADOS_G_TOTAL` changes
`data-r` `-0.2290` → `-0.3321` on the same `n=347`; diagnosis grouping →
2 partitioned traces named `Autism`/`Control`, `data-group-count="2"`, per‑group
line `Autism: r = -0.03 (n = 372)`; sex grouping re‑partitions; same‑variable
X=Y shows the note and `data-r="null"`; refresh restores defaults; hover
templates carry no `customdata`/identifier; the activity frame issues only
same‑origin requests — no CDN / kernel / JupyterLite / Voici / widget‑manager /
WebSocket — and no failed widget request; narrow‑viewport usable.

Visual check (screenshots): the default scatter is a clean cloud with the stats
and missing lines above it; the diagnosis‑coloured view shows blue Autism points
sitting high on SRS and orange Control points low, with the readout "Within
groups — Autism: r = -0.03 (n = 372) · Control: r = -0.06 (n = 406)" — the
overall −0.24 visibly a between‑group effect. Legend sits below the plot. The
notebook's four figures (violin, site×diagnosis heatmap, masked Pearson
triangle, pairwise‑N triangle) render with readable axis labels and annotations.

## Acceptance criteria

| Criterion | Status | Evidence |
|---|---|---|
| WP05 checkpoint commit + annotated tag exist | **PASS** | `444aa14` / `wp05-start` |
| Data inspection precedes and justifies example selection | **PASS** | inspection scripts run first; verified‑findings table; every example tied to a stable interpretation |
| Notebook completes the distributions/correlations sequence without becoming an inferential‑statistics chapter | **PASS** | 22 cells, sections A–F; no hypothesis tests / p‑values / models; Cramér's V is an optional `hide-cell` sidebar |
| Static examples concise, readable, non‑identifying, explicit about missingness | **PASS** | ≤5 vars per table; 4 figures; flagged rows via `SITE_ID` + age + diagnosis label, no `SUB_ID`; every plot/stat handles `NaN`/`null` explicitly (`dropna`, `notna().sum()`, `observed=True`) |
| Correlation **and** pairwise‑N matrices both shown and discussed | **PASS** | Figs 3 & 4 on the same variables + same mask; D4 discussion reads them together |
| Pearson/Spearman, part–whole, group/site composition, outlier caution, mixed‑type associations covered accurately | **PASS** | D1/D4; `SRS`–subscale & `FIQ`–`VIQ`; Fig 2 + Cramér's V; C1–C3; E1 table + crosstab |
| Every major subsection has an active question with a self‑learning answer/checklist | **PASS** | A3, B5, C3, D6, E4, F1 — each a `####` question closing with a `{dropdown}` |
| `eda-correlation` is config‑driven, identifier‑free, accessible, uses pure tested calculations | **PASS** | `config.ts` union member + semantics; reuses identifier‑free artifact; `<label for>` on every control, keyboard‑operable, light/dark; `correlation.ts` 25 unit tests |
| Browser tests on the final built Chapter 1 page prove all explorer controls alter the real figure/statistics | **PASS** | `e2e-book/chapter01.spec.ts` correlation describe (3 tests) |
| Histogram & retention regressions remain green | **PASS** | unit + `e2e/histogram.spec.ts` + `e2e/retention.spec.ts` + both built‑book describes unchanged and passing |
| Jupyter Book executes without notebook error reports; MyST dropdowns render | **PASS** | exit 0, no `*.err.log`; 0 literal `{dropdown}` strings, dropdown cards present |
| No runtime CDN/kernel dependency introduced | **PASS** | activity‑frame network assertions; bundle is the same locally‑bundled Plotly |
| Documentation / report complete; final tree clean | **PASS** | `interactive/README.md` updated; this report; `git status` clean after the impl commit |
| No WP06 file or out‑of‑scope maintenance change | **PASS** | no `WP06*`; no Vite/Vitest bump, no Plotly code‑split, no MathJax self‑host, no toctree/logo cleanup |

## Deviations from instructions

1. **"axis/legend labels" in the config are the per‑variable `label` fields and
   the grouping `values[].label`, not static `xAxisLabel`/`yAxisLabel` keys.**
   The axes change with the X/Y selection, so a fixed axis‑label string would be
   wrong; the variable label *is* the axis title, updated on every redraw. The
   legend labels are the grouping value labels. All labels are non‑empty and
   validated.
2. **`correlation-data.ts` is a separate, looser schema** rather than reusing
   `parseAbideRetentionData`. It keeps only alignment + identifier rejection
   (drops the retention‑only `site` / per‑variable metadata requirements) so the
   correlation activity does not demand structure it never uses. Same rationale
   and same deviation shape as WP03/WP04's split data schemas.
3. **`deploy.yml` unchanged.** New unit tests are globbed by `npm run
   test:unit`, new standalone/built‑book specs by `playwright test` /
   `test:e2e:book`, and no new data artifact was added (the reused one is
   already covered by `--check --artifact all`). Sphinx copies
   `book/_static/widgets/configs/` and `data/` verbatim. Per WP §8.2 ("update
   only as needed; do not duplicate existing steps") nothing was added.
4. **Transient `pip install pdfplumber` into the git‑ignored `.venv`** to
   extract the ABIDE‑II Data Legend PDF text and verify the `DX_GROUP` / `SEX` /
   handedness / medication / eye‑status code meanings. `requirements.txt` is
   unchanged; nothing about this is committed.
5. **22 new notebook cells** — the top of the WP's "approximately 15–22" range —
   and **4** new static figures (limit 5).
6. **Node 24 locally** (`package.json` `engines` `>=20.19.0 <25`; CI pins 22).
   Full‑tree `npm audit` still reports the WP02–WP04 dev‑toolchain advisories
   (esbuild/vite/vitest); `npm audit --omit=dev` is clean. Carried forward per
   WP §8.3 (no Vite/Vitest upgrade in this WP).

## Unresolved risks

- The unit and Playwright suites assert exact coefficients (4 dp) and group
  `n`. Any change to `abide_retention.json` or the pinned source would require
  updating the reference table in `interactive/README.md` and the specs. The
  values are documented in three places to make that intentional.
- Playwright reads Plotly's public `gd.data` array (trace names, point counts)
  rather than SVG internals for the scatter — robust to a Plotly minor bump,
  and `data-render-count` / `data-n` / `data-group-count` back it up.
- Reusing `abide_retention.json` ties the explorer's variable menu to that
  file. Adding a numeric variable that is not already exported would require
  extending `RETENTION_VARIABLES` in `scripts/export_widget_data.py` and a
  deterministic re‑refresh.
- The surrounding Chapter 1 *page* still loads MathJax from
  `cdn.jsdelivr.net/npm/mathjax@3` and ships `sphinx-thebe.js` (pre‑existing
  `sphinx-book-theme` behaviour; the activity iframe itself is CDN/kernel‑free,
  asserted). Out of scope here, as in WP04.
- `jupyter-book build` still exits 0 on a notebook execution error; the CI
  `*.err.log` guard is the safety net and must be kept.
- Bundle is 1.48 MB raw / 496 kB gzip (Plotly), above Vite's 500 kB warning —
  acceptable for a lazy‑loaded iframe; code‑splitting remains an option.

## Git commits created

- Checkpoint: `444aa1495a3b4b48b7b3b3078df7be4ab120199a` ("checkpoint: before WP05")
- Checkpoint tag: `wp05-start` (annotated; points at `444aa14`)
- Implementation: `004a3fde204d948290498bae51a417da6c192d1c` ("WP05: complete distributions and feature correlations section")
- Report: "WP05 report: document results" — hash printed in the terminal summary (a report cannot contain its own hash).

## Recommendations — WP06 only (do not create or begin WP06)

- **Page‑level CDN removal** (Rule 8): self‑host MathJax and trim / self‑host the
  `sphinx-thebe` launch‑button config so the whole published Chapter 1 page, not
  only the iframes, is CDN‑free. Now the smallest remaining CDN item.
- **Consolidate the Chapter 1 EDA notebook's remaining kernel‑only demos**
  (median imputation, category fill) into the browser runtime, or explicitly
  decide they stay kernel‑only, so the whole EDA exercise works on the static
  site.
- **Toolchain security bump** (Vite ≥ 6 / Vitest ≥ 3 or then‑current) as an
  isolated WP with a full typecheck/unit/build/e2e re‑run, to clear the
  dev‑only `npm audit` advisories.
- **Plotly bundle**: code‑split behind a dynamic `import()` now that the final
  trace‑type set across the three activities is fixed (bar + scatter).
- **Shared e2e static‑server helper**: `e2e/serve-static.mjs` and
  `e2e-book/serve-book.mjs` are near‑duplicates.
- **Optional**: dynamic iframe height (all three activities use a fixed
  `height`); a short "reading a scatterplot" callout to pair with the new
  explorer.

## Instructions for reviewer

Paste this entire report into the ChatGPT conversation that produced WP05.
