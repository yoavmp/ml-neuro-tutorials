# WP38 Exact Changelog

Every file added, modified, or removed by WP38 (Exercise 10: Examples and
Common Mistakes), relative to the starting branch tip `main` @
`2f74ccae826d14da9dee9997d890697d159d91c0`.

## Specification checkpoint (already committed before implementation)

- **`WPs/WP38_EXERCISE_10_EXAMPLES_AND_COMMON_MISTAKES.md`** (added) — the
  WP38 specification, committed as the initial checkpoint (`06fd62af0ea0eee8bcf5cc20274c8a5a1d8f7602`)
  before implementation.

## Manifest

- **`book/config/abide_modeling.json`** (modified) — added the top-level
  `leakage_lab` key (target, predeclared sample sizes/seeds, and the three
  scenarios' bundles/feature counts/exact correct+leaky workflow strings).
  Purely additive (41 inserted lines, 0 removed); verified self-consistent
  by `scripts/abide_modeling_data.py --check`.

## UCI HAR data (new)

- **`scripts/uci_har_data.py`** (added) — shared loader/constants
  (`FEATURE_SUBSET`, `ACTIVITY_LABELS`, `load_compact_table`,
  `load_provenance`) and the one shared grouped-vs-random fold-comparison
  implementation (`fold_assignment`, `run_cv`, `compute_fold_comparison`)
  reused unchanged by both the audit script and the widget exporter.
- **`scripts/export_uci_har_data.py`** (added) — `--refresh` (network):
  downloads and SHA-256-verifies the original UCI archive (outer + inner
  zip), extracts the fixed 18-feature subset by official name, writes the
  compact table + provenance; `--check` (offline): re-validates both.
- **`book/data/uci_har/uci_har_compact.csv.gz`** (added) — the committed
  compact table: 10,299 rows, 30 participants, 6 activities, 18 official
  feature columns, 888 KB compressed.
- **`book/data/uci_har/provenance.json`** (added) — dataset title/authors,
  source URL, DOI, CC BY 4.0 license, original-archive checksums,
  extraction script/columns, and the derived file's own SHA-256.
- **`scripts/har_group_leakage_audit.py`** (added) — the mandatory
  preflight audit (WP38 §8.2): ordinary vs. participant-grouped 5-fold CV
  for KNN at k ∈ {1,3,5,11,25}, the four inclusion conditions, `--run`/`--check`.
- **`scripts/har_group_leakage_audit_result.json`** (added, generated) —
  the committed preflight result (`har_group_leakage_audit.py --run`);
  overall verdict **PASS**; re-validated offline (`--check`).
- **`scripts/export_har_fold_widget_data.py`** (added) — exports
  `book/_static/widgets/data/uci_har_fold_comparison.json` by reusing
  `uci_har_data.compute_fold_comparison` unchanged, so the browser
  activity's numbers cannot drift from the audited ones; `--refresh`/`--check`.
- **`book/_static/widgets/data/uci_har_fold_comparison.json`** (added,
  generated) — per-k, per-fold accuracy/macro-F1/confusion matrices for
  both splitting methods, plus all 30 participants' fold assignments.

## ABIDE leakage-lab data (new)

- **`scripts/export_leakage_lab_data.py`** (added) — builds the
  correct/leaky paired comparison for scaling, target-informed feature
  selection, and PCA, across 4 predeclared sample sizes × 5 predeclared
  seeds (60 entries); `--refresh` (network)/`--check` (offline).
- **`book/_static/widgets/data/abide_leakage_lab.json`** (added,
  generated) — the committed artifact (60 entries + scenario metadata).

## ABIDE imbalance-threshold data (new)

- **`scripts/export_imbalance_threshold_data.py`** (added) — reuses
  Exercise 3's exact 90:10 cohort-draw mechanism and fixed `C=1.0`
  logistic-regression recipe; fits ordinary and `class_weight="balanced"`
  on the identical training split, ships only both models' fixed test-set
  predicted probabilities, the true labels, and threshold-independent
  ROC-AUC/PR-AUC; `--refresh`/`--check`.
- **`book/_static/widgets/data/abide_imbalance_threshold.json`** (added,
  generated) — the committed artifact (100 test-set probabilities per
  model).

## Multiple-selection quiz content (new, static)

- **`book/_static/widgets/data/leakage_quiz.json`** (added) — the seven
  options (six correct, one incorrect), per-option feedback, success
  text, and nuance sentence, verbatim per WP38 §5.1.

## Frontend widget configs (new)

- **`book/_static/widgets/configs/leakage_quiz.json`**,
  **`leakage_lab.json`**, **`har_fold_compare.json`**,
  **`imbalance_threshold.json`** (all added) — one config per new activity
  type, each pointing at its data artifact above.

## Frontend widget implementation (new)

- **`interactive/src/leakage-quiz-data.ts`**, **`leakage-lab-data.ts`**,
  **`har-fold-compare-data.ts`**, **`imbalance-threshold-data.ts`** (all
  added) — Zod schemas/parsers for the four new data contracts.
- **`interactive/src/components/leakage-quiz.ts`** (added) — pure
  DOM/ARIA multi-select quiz: any-number-selectable checkboxes, exact-match
  success gating, per-option correct/incorrect/missed marks and feedback,
  "Try again", `aria-live` outcome region, no persistence.
- **`interactive/src/components/leakage-lab.ts`** (added) — operation /
  sample-size / seed controls; paired correct-vs-leaky bar chart; an
  aggregate leaky-minus-correct chart across all 5 seeds with the current
  seed highlighted; renders the scaling scenario's exact-zero gap
  faithfully (does not hide or "improve" it).
- **`interactive/src/components/har-fold-compare.ts`** (added) — ordinary
  vs. grouped / k / fold controls; a 30-tile participant/fold-assignment
  diagram (multi-color strips under ordinary splitting, single color under
  grouped); confusion-matrix heatmap and a per-fold accuracy/macro-F1 chart
  for the selected (method, k).
- **`interactive/src/components/imbalance-threshold.ts`** (added) — model
  / threshold controls; client-side confusion-matrix and metric recompute
  from the two fixed probability arrays (never refits); visual hierarchy
  emphasizing accuracy-vs-baseline and PR-AUC-vs-prevalence; hedged
  model-comparison language.
- **`interactive/src/classification-metrics.ts`** (modified, additive) —
  added `precisionFromCounts`, `recallFromCounts`, `f1FromCounts`,
  `balancedAccuracyFromCounts`, used by the new imbalance-threshold
  component; no existing function changed.
- **`interactive/src/components/registry.ts`** (modified, additive) —
  imported and registered the four new components.
- **`interactive/src/config.ts`** (modified, additive) — added the four
  new `.strict()` Zod config schemas (`multi-select-quiz`, `leakage-lab`,
  `har-fold-compare`, `imbalance-threshold`) to the discriminated union.
- **`interactive/src/styles.css`** (modified, additive) — new classes for
  the quiz, workflow panels, participant-fold grid, and metric-tile
  hierarchy; also fixed a real narrow-viewport bug shared by every widget
  with a `<select>` (missing `min-width: 0`/`max-width: 100%`, which could
  force horizontal overflow at 390px with a long option label) — re-ran
  the existing `classification-imbalance`, `retention`, and `knn-explore`
  standalone specs afterward to confirm no regression.

## Frontend tests (new)

- **`interactive/tests/leakage-quiz-data.test.ts`**,
  **`leakage-lab-data.test.ts`**, **`har-fold-compare-data.test.ts`**,
  **`imbalance-threshold-data.test.ts`** (all added) — Vitest schema/parser
  unit tests for the four new data modules.
- **`interactive/tests/config.test.ts`** (modified, additive) — added
  "accepts the shipped config" cases for the four new committed config
  files.
- **`interactive/e2e/leakage-quiz.spec.ts`**, **`leakage-lab.spec.ts`**,
  **`har-fold-compare.spec.ts`**, **`imbalance-threshold.spec.ts`** (all
  added) — standalone Playwright specs, each run at both the site-root and
  GitHub-Pages-subpath path prefixes.
- **`interactive/e2e-book/chapter10.spec.ts`** (added) — built-book proof
  that all four Exercise 10 activities load, respond to their controls,
  and fit at 390px on the real published page.
- **`interactive/e2e-book/iframe-height-contract.spec.ts`** (modified,
  additive) — appended the 4 new iframe cases to the shared, generic
  height-contract `CASES` list; updated the header comment's exercise
  range from "1-9" to "1-10".
- **`interactive/e2e-book/launch-buttons.spec.ts`** (modified) — moved
  Chapter 10 from the "placeholder, no Colab button" assertion into the
  mapped-`CHAPTERS` loop (it now has a portable notebook and button); the
  remaining placeholder-page check retargeted from Exercise 10 to Exercise
  11.

## Notebook (new)

- **`book/chapters/chapter_10/exercise_10.md`** (removed) — the WP25-era
  placeholder, replaced by the real notebook below.
- **`book/chapters/chapter_10/exercise_10.ipynb`** (added) — the canonical
  Exercise 10 notebook, 37 cells, executed in place with 0 stored errors
  (see `WP38_REPORT.md` §4 for the exact section list).
- **`book/downloads/chapter_10/exercise_10_portable.ipynb`** (added,
  generated) — via `scripts/build_portable_notebook.py --write --notebook
  chapter_10`; the UCI HAR compact table is embedded inline as base64 (no
  repository-relative dependency); smoke-executed outside the repository
  tree with 0 errors.
- **`book/_static/launch-buttons.js`** (modified) — added the
  `chapters/chapter_10/exercise_10.html` → portable-notebook mapping
  entry; updated the header comment's "placeholder Exercises 10-12" note
  to "11-12".

## Portable-notebook generator

- **`scripts/build_portable_notebook.py`** (modified) — added `import
  base64`; added `PUBLISHED_PAGE_CH10`, `_CH10_BANNER`, `_CH10_SETUP`,
  the four `_CH10_*_IFRAME_REPLACEMENT` blocks, `_embed_har_compact_table()`
  (embeds the committed compact table as an inline base64 literal for the
  portable notebook, mirroring the existing `_rewrite_data_loading`
  special-case pattern for Chapter 1), the `embed_har_compact_table` field
  on `NotebookSpec`, the code-cell branch that invokes it, and the
  `CHAPTER_10` `NotebookSpec`; registered it in `NOTEBOOKS`; updated the
  module docstring's `--notebook` choices list and the "Exercises 10-12
  are placeholder" note (now "Exercises 11-12").
- **`scripts/smoke_portable_notebook.py`** (modified, additive) — added
  the `chapter_10` entry to `SMOKE` with its expected printed-output
  strings.

## Tests updated for Exercise 10 no longer being a placeholder

- **`tests/test_placeholder_exercises.py`** (modified) — removed key `10`
  from `PLACEHOLDER_TITLES`; module docstring updated to "Exercises 11-12".
- **`tests/test_book_structure.py`** (modified) — chapter 10 moved from
  the "must exist as `.md`" loop to the "must exist as `.ipynb`" loop.
- **`tests/test_wp25_content_audit.py`** (modified) — `EXERCISE_TITLES[10]`
  updated to the WP38-directed notebook title "Exercise 10: Examples and
  Common Mistakes" (with a comment noting the syllabus/Word overview
  intentionally still show the WP25 wording, out of scope for WP38); the
  `n <= 9` cutoffs used to decide `.ipynb` vs. `.md` lookup changed to
  `n <= 10` in two places; the hardcoded portable-notebook tuple extended
  to include `10`.
- **`tests/test_exercise_04_notebook.py`** (modified) — the "Exercises
  10-12 remain placeholders without launch buttons" test renamed/retargeted
  to "11-12".
- **`tests/test_exercise_06_notebook.py`** (modified) — the "Exercises
  10-12 still have no portable notebook" test renamed/retargeted to
  "11-12".
- **`tests/test_exercise_07_notebook.py`**, **`test_exercise_08_notebook.py`**,
  **`test_exercise_09_notebook.py`** (all modified) — each had its own
  "Exercises 10-12 have no launch button" test renamed/retargeted to
  "11-12"; comments updated accordingly.

## New Exercise 10 tests

- **`tests/test_exercise_10_notebook.py`** (added) — 18 tests: nbformat
  validity, cell-count range, title/opening structure, all 7 section
  headings in order, all 4 iframe titles/config paths, quiz option
  count/correctness, Think First blocks not duplicated, the required
  "leakage makes the evaluation invalid..." sentence appears exactly once,
  all 5 "Find the Mistake" fragments + dropdown answers, the 9-item final
  checklist, no engineering vocabulary leaking to student text, correct
  `hide-input`/`hide-cell` tag usage, UCI HAR attribution present, portable
  notebook has no repository-relative dependency.
- **`tests/test_export_leakage_lab_data.py`** (added) — 11 tests:
  `--check` passes, canonical serialization, full (scenario, size, seed)
  coverage, the scaling scenario's exact-zero gap, feature-selection's
  full-sample inflation direction, row-count consistency, no
  identifier-shaped keys, MSE non-negativity, plus 3 unit tests on the
  per-scenario helper functions.
- **`tests/test_uci_har_data.py`** (added) — 14 tests across the committed
  compact table (row/participant/activity counts, 18 feature columns, no
  missing values, repeated rows per participant), provenance (pinned
  source/DOI/license, derived-file checksum match, no target-informed
  selection), and the shared fold comparison (ordinary crosses every
  participant, grouped has zero overlap, single grouped fold per
  participant, ordinary more optimistic at k=5, 5×6×6 confusion matrices,
  determinism).
- **`tests/test_har_group_leakage_audit.py`** (added) — 9 tests: the
  committed result is current/canonical/reproducible from the committed
  data, all five k values preserved, each of the four inclusion conditions
  individually holds, overall PASS, plus 2 synthetic-data unit tests
  proving condition 4 (not one anomalous fold) and condition 3 (≥2
  qualifying k) actually discriminate.
- **`tests/test_export_har_fold_widget_data.py`** (added) — 6 tests:
  `--check` passes, canonical serialization, numbers match the audited
  preflight exactly, 30 participants with fold assignments, no
  identifier-shaped keys, deterministic rebuild.
- **`tests/test_export_imbalance_threshold_data.py`** (added) — 11 tests:
  `--check` passes, canonical serialization, 90:10/400/40 cohort, 90%
  majority baseline, 10% PR-AUC-prevalence baseline, both models share the
  same test labels, same fixed `C` for both, class-weighted model
  correctly declares `class_weight='balanced'`, ROC/PR-AUC in `[0,1]`, no
  identifier-shaped keys, deterministic cohort resampling.

## Reports

- **`WPs/reports/WP38_REPORT.md`** (added) — this WP's report.
- **`WPs/reports/WP38_EXACT_CHANGELOG.md`** (added) — this file.

## What was explicitly NOT done in WP38

- `book/syllabus.md` and
  `course_overview/Machine_Learning_for_Neuroscience_Notebook_Overview.docx`
  were not touched.
- No existing widget type, component, config, or data artifact (Exercises
  1-9) was modified — only new files were added, plus the four purely
  additive shared-infrastructure diffs listed above
  (`classification-metrics.ts`, `registry.ts`, `config.ts`, `styles.css`).
- No seed, sample size, feature subset, or model was searched, retried, or
  changed after seeing a result at any point.
- No `git push`, `git merge` into `main`, or GitHub Actions interaction of
  any kind.
- No dependency file was installed, upgraded, or modified.
