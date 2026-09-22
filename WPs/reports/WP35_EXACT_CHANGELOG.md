# WP35 Exact Changelog

Every file added, modified, or removed by WP35 (Exercises 7–9 review
corrections and reusable iframe auto-resize), relative to the starting
branch tip `feature/wp34-exercise9-advanced-models` @ `3cb1e81`.

## Specification checkpoint (already committed before implementation)

- **`WPs/WP35_EXERCISES_7_9_REVIEW_CORRECTIONS.md`** (added) — the WP35
  specification, committed as the initial checkpoint (`96a9263`) before
  implementation.

## Manifest

- **`book/config/abide_modeling.json`** (modified):
  - `advanced_models.pcr_pls_activity.presets`: `weak` and `strong` swapped
    (physical scenario, not just label) so the three presets now encode
    weak/moderate/strong alignment with the **highest**-variance direction
    (PC1) instead of the lower-variance one; all three `label` strings
    updated to match.
  - `advanced_models.abide_comparison.models.linear_svr.grid.C`: `[0.01,
    0.1, 1, 10]` → `[0.01, 0.1, 1]` (removed the nonconvergent `C=10`).
  - `advanced_models.abide_comparison.models.linear_svr.pipeline` string
    updated (`max_iter=5000` → `max_iter=20000`).
  - `advanced_models.abide_comparison.models.rbf_svr`: added
    `"fixed_epsilon": 1.0`; `pipeline` string updated to mention it.
  - Added `advanced_models.abide_comparison.linear_svr_grid_note` and
    `.rbf_svr_epsilon_note` (new manifest notes documenting both
    corrections); `linear_svr_solver_note` trimmed (its own `C=10`-specific
    non-convergence detail moved into the new `linear_svr_grid_note`).
  - Verified self-consistent by `scripts/abide_modeling_data.py --check`.

## Exercise 2 (language audit only)

- **`book/chapters/chapter_02/exercise_02.ipynb`** (modified) — "one of
  four predeclared, anatomically motivated bundles" → "one of four fixed,
  anatomically motivated bundles" (§"What does sample size change?");
  re-validated against `test_wp24_content_audit.py`'s existing word-count
  ceiling (219 vs. 220 words).
- **`book/downloads/chapter_02/exercise_02_portable.ipynb`** (modified,
  regenerated + banner-text fix from the generator change below);
  smoke-executed outside the repository tree, 0 errors, key values
  matched.

## Exercise 4 (language audit only)

- **`book/chapters/chapter_04/exercise_04.ipynb`** (modified) — "five
  predeclared random seeds" → "five fixed random seeds" (§2).
- **`book/downloads/chapter_04/exercise_04_portable.ipynb`** (modified,
  regenerated); smoke-executed, 0 errors, key values matched.

## Exercise 6 (language audit only)

- **`book/chapters/chapter_06/exercise_06.ipynb`** (modified):
  - "development partition" → "training-and-validation data" (two
    instances: a code comment in the classification-contrast cell, and the
    matching markdown discussion paragraph).
  - Classification-contrast code comment: removed the WP-number reference
    ("Bounded, conditional audit (WP30, corrected by WP30R)") and the
    internal script-path reference
    (`scripts/decision_tree_model_audit.py`) in a second nearby comment —
    both rewritten in plain language.
  - "fixed, predeclared complexity settings" → "fixed complexity settings"
    (§6).
  - "aggregate across all five audited training replicates" → "...five
    training replicates" (§5); `random_forest_max_features`'s inline
    comment: "was also audited" → "was also considered".
  - Re-executed; 0 stored errors (no computed values changed — comment/
    prose only).
- **`book/downloads/chapter_06/exercise_06_portable.ipynb`** (modified,
  regenerated); smoke-executed, 0 errors, key values matched.
- **`tests/test_exercise_06_notebook.py`** (modified) — updated
  `test_corrected_development_only_numbers_match_the_committed_audit`'s
  expected substring from "development partition" to
  "training-and-validation data".

## Exercise 7 (Part A)

- **`book/chapters/chapter_07/exercise_07.ipynb`** (modified):
  - Section 6 intro/procedure list: "development partition" →
    "training-and-validation data" (three instances, plus one more in the
    Section 5 activity intro and one in the Section 7 comparison
    sentence).
  - Grid-size explanation markdown cell rewritten in full: no more
    "predeclared rule," target machine, audit report, or internal timing
    protocol; new concise, student-facing wording per WP35 §4.
  - CV-fitting code cell: dropped "predeclared" from its own comment;
    added per-candidate `std_cv_mse` (fold-level SD) alongside the
    existing `mean_cv_mse`.
  - Replaced the single results/print cell with three cells: a new,
    visible grouped bar-graph cell (matplotlib; x-axis by `max_depth`,
    bars colored by `learning_rate`, `n_estimators` labeled per bar,
    y-axis from 0, selected candidate starred, legend outside the axes)
    plus its own "selected settings"/"locked-test" prints; a new
    `hide-cell`-tagged cell holding the original full 12-row numeric
    table (collapsed on the website, fully visible/runnable in the
    portable notebook); the post-graph explanation paragraph now refers
    to "the graph" instead of "the table."
  - Re-executed; identical selected settings/locked-test metrics as
    before (learning_rate=0.1, n_estimators=200, max_depth=3; MSE 27.2;
    locked-test MSE 32.4, R² 0.653).
- **`book/downloads/chapter_07/exercise_07_portable.ipynb`** (modified,
  regenerated); smoke-executed outside the repository tree, 0 errors, key
  values matched.
- **`interactive/e2e-book/chapter07-dark-mode.spec.ts`** (added) —
  dedicated built-book dark-mode regression guard for both Exercise 7
  activities, following the `chapter08-dark-mode.spec.ts` template;
  additionally asserts zero console/runtime errors throughout the full
  light→dark→reload→light cycle (filtering two pre-existing, unrelated
  book-chrome noise strings not introduced by this WP).
- **`interactive/e2e/boosting-parameter-explorer.spec.ts`** (modified) —
  both `page.waitForTimeout(700)` negative-assertion waits (Pause-stops-
  advancing; no-orphan-timer-after-reload) now derive their bound from the
  widget's own committed `playIntervalMs` (read from the real config
  fixture at test time) instead of a disconnected literal, with the
  rationale documented in place per WP35 §6.3's carve-out for a genuinely
  unavoidable short wait.
- **`tests/test_exercise_07_notebook.py`** (modified) — updated
  `test_intended_27_candidate_grid_is_shown_and_reduction_explained` for
  the new wording ("27-candidate" instead of "27 candidates"); added
  `test_no_author_facing_grid_selection_paragraph_remains`; replaced
  `test_results_table_and_selected_settings_are_visible` with
  `test_selected_settings_are_visible_and_raw_table_is_collapsed` (checks
  the new split: bar-chart cell visible, raw-table cell `hide-cell`) and
  added `test_bar_graph_encodes_depth_learning_rate_trees_and_mse`.

## Exercise 8 (Part B)

- **`book/chapters/chapter_08/exercise_08.ipynb`** (modified):
  - "What this notebook covers": the central question now has its own
    bolded standalone line, "**What can we learn from brain measurements
    when no target is supplied at all?**"
  - Cumulative explained-variance plot: y-axis 0–100%, `PercentFormatter`,
    PC1's own cumulative value marked with a point + annotation; the PCA
    fit/values are unchanged. `import matplotlib.ticker as mticker` added
    to the shared imports cell.
  - "**K-means** is the only clustering method covered in this notebook."
    → "In this notebook, we use **K-means** as one practical example for
    understanding how clustering works."
  - Section 8 renamed: `## 8. Using PCA Before a Model We Already Know` →
    `## 8. Using PCA in a Supervised Pipeline` (still PCA + KNN).
  - New markdown cell (guided `k` exploration) inserted immediately after
    the "Explore PCA and K-Means" iframe: inertia/silhouette-vs-`k`,
    Age-colored `k=2`/`k=3`/larger-`k` comparison, and the required
    cautious conclusion (not a proven `k`, not autism subtypes).
  - "development partition" → "training-and-validation data" (three
    instances in the Section 8 PCA+KNN text).
  - Re-executed; PCA/K-means/KNN results and audited numbers unchanged
    (no data or metric was altered).
- **`book/downloads/chapter_08/exercise_08_portable.ipynb`** (modified,
  regenerated); smoke-executed outside the repository tree, 0 errors, key
  values matched.
- **`interactive/src/components/pca-kmeans-explorer.ts`** (modified) —
  the "Participants in PC1-PC2 space, colored by cluster" scatter plot's
  legend moved outside the axes (vertical, right side, `x: 1.02`) with a
  150px reserved right margin, replacing the shared horizontal-top default
  that could crowd the plot at the largest configured `k` (6).
- **`tests/test_exercise_08_notebook.py`** (modified) — `SECTION_TITLES`
  and five section-8-scoped tests updated for the rename; the PCA+KNN
  teaching-points assertion updated for "training-and-validation data".

## Exercise 9 (Part C)

- **`book/chapters/chapter_09/exercise_09.ipynb`** (modified):
  - Section 8 restructured: new `RUN_FULL_NESTED_CV = False` flag cell
    (visible); the machinery cell (still `hide-input`) now defines
    `RBF_SVR_EPSILON = 1.0`, a corrected `LINEAR_SVR_C_GRID = [0.01, 0.1,
    1]`, `max_iter=20000`, a literal `EMBEDDED_SUMMARY` (from the
    regenerated audit), and gates the entire original computation behind
    `if RUN_FULL_NESTED_CV: ... else: summary =
    pd.DataFrame(EMBEDDED_SUMMARY).set_index("model")`; a new markdown
    note states the optional full run takes a few minutes.
  - "Selected hyperparameters per outer fold" dropdown: now points to
    `RUN_FULL_NESTED_CV = True` instead of an always-present
    `fold_results` table, and states the corrected `C` grid and the fixed
    RBF `epsilon`.
  - Discussion paragraph: RBF SVR's reported mean MSE updated (20.2 →
    20.4, reflecting the corrected epsilon); the closing paragraph
    discussing `LinearSVR`'s non-convergence removed entirely (0 warnings
    remain).
  - Re-executed (default path, `RUN_FULL_NESTED_CV=False`): ~8 seconds,
    identical printed summary to the regenerated audit. A separate scratch
    copy with the flag flipped to `True` was executed independently
    (~117 seconds, 0 errors, identical printed numbers) and discarded —
    not part of this diff.
- **`book/downloads/chapter_09/exercise_09_portable.ipynb`** (modified,
  regenerated); smoke-executed outside the repository tree (default,
  fast path), 0 errors, key values matched.
- **`interactive/src/components/pcr-pls-explore.ts`** (modified) — the
  alignment control's label: "Target's alignment with the lower-variance
  direction:" → "Target alignment with the highest-variance direction:";
  header comment updated.
- **`interactive/src/config.ts`** (modified) — the "PCR or PLS?" config
  schema's doc comment updated for the new alignment-preset framing.
- **`book/_static/widgets/configs/pcr_pls_explore.json`** (modified) —
  `description`/`instructions` reworded for "highest-variance direction".
- **`book/_static/widgets/data/pcr_pls_explore.json`** (modified,
  regenerated via `scripts/export_pcr_pls_widget.py --refresh`) — the
  `weak`/`strong` presets' `betaPc1`/`betaPc2`/`label` swapped; predictor
  cloud, split, and noise realization unchanged; re-validated by
  `--check`.
- **`scripts/export_pcr_pls_widget.py`** (modified) — module docstring
  updated for the new preset framing.
- **`scripts/advanced_models_audit.py`** (modified) — `RBF_SVR_EPSILON`
  constant (read from the manifest's `fixed_epsilon`) now passed
  explicitly to every RBF `SVR` fit; `LINEAR_SVR_MAX_ITER` constant (20000,
  documented) replaces the previous inline `max_iter=5000`; `validate()`
  gained three checks (grid excludes `C=10`; `rbf_svr.fixed_params.epsilon`
  matches the manifest; no `linear_svr` convergence warnings remain);
  `_print_summary()` prints each model's `fixed_params` when present.
- **`scripts/advanced_models_audit_result.json`** (modified, regenerated
  via `--run`) — new grids/epsilon; **zero** convergence warnings (down
  from 128 in WP34's committed result); RBF SVR's mean outer-test MSE
  20.15 → 20.38 (R² 0.771626); every other model's numbers unchanged
  (LinearSVR `C=10` was never selected by any outer fold, so its removal
  does not change LinearSVR's own reported numbers). Re-validated offline
  (`--check`).
- **`tests/test_advanced_models_audit.py`** (modified) — updated the
  `linear_svr` grid assertion; added
  `test_linear_svr_grid_excludes_the_nonconvergent_c_equals_10`,
  `test_no_convergence_warnings_remain`,
  `test_rbf_svr_epsilon_is_explicit_and_not_sklearns_implicit_default`,
  `test_rbf_svr_pipeline_actually_sets_epsilon`.
- **`tests/test_export_pcr_pls_widget_data.py`** (modified) — added
  `test_weak_moderate_strong_trend_at_one_component` (the required
  monotonic-gap invariant) and
  `test_presets_labelled_for_highest_variance_direction`.
- **`interactive/e2e/pcr-pls-explore.spec.ts`** (modified) — added
  "the alignment control is labelled for the highest-variance direction"
  and "PLS's advantage over PCR at one component shrinks from weak to
  strong alignment with PC1".
- **`scripts/smoke_portable_notebook.py`** (modified) — `chapter_09`'s
  expected-output string updated from the stale WP34 value ("RBF SVR
  mean MSE = 20.2 mean R2 = +0.774") to the regenerated audit's actual
  value ("...20.4...+0.772"); caught by running the smoke check itself
  (see WP35_REPORT.md §10).
- **`tests/test_exercise_09_notebook.py`** (modified) — updated the grid/
  epsilon assertions and the "Selected hyperparameters" dropdown check;
  replaced `test_discussion_is_honest_and_mentions_convergence_warnings`
  with `test_discussion_is_honest_and_no_longer_mentions_unresolved_warnings`;
  added `test_linear_svr_grid_excludes_c_equals_10`,
  `test_run_full_nested_cv_flag_defaults_false_and_gates_the_expensive_code`,
  `test_embedded_summary_matches_the_audit`,
  `test_note_explains_the_optional_full_run_takes_minutes`,
  `test_no_notebook_or_repository_dependency_for_default_embedded_results`.

## Portable-notebook generator

- **`scripts/build_portable_notebook.py`** (modified) — every chapter's
  opening-banner text ("...generated from the canonical course notebook by
  `scripts/build_portable_notebook.py`.") rewritten to "...generated from
  the full interactive course notebook." (9 occurrences, one regex pass);
  a second internal-script-path/vocabulary reference inside Exercise 1's
  portable-only curated-column rewrite comment also reworded. All 9
  registered notebooks regenerated as a result (1, 3, 5's content is
  otherwise unchanged; 2, 4, 6, 7, 8, 9 also carry their own content
  changes above).
- **`book/downloads/chapter_01/exercise_01_portable.ipynb`**,
  **`.../chapter_03/exercise_03_portable.ipynb`**,
  **`.../chapter_05/exercise_05_portable.ipynb`** (modified, regenerated;
  banner-text only — no other change).

## Part D — reusable interactive-height correction

- **`interactive/src/resize-report.ts`** (modified) — `ResizeObserver`
  callbacks are now coalesced with `requestAnimationFrame` (at most one
  resize message posted per rendered frame) and a height change under 2px
  is treated as noise rather than reported, closing WP35 §17.5's
  debounce/oscillation-tolerance requirement (previously every observer
  callback posted immediately with only an exact-equality de-dupe check).
- **`book/_static/activity-resize.js`** (modified) — added the matching
  2px write-side tolerance (skips an iframe-height write that would change
  the on-screen height by less than 2px), as defense in depth alongside
  the child-side fix above.
- **`interactive/e2e-book/iframe-height-contract.spec.ts`** (added) — a
  single reusable spec enumerating all 20 interactive iframes across
  Exercises 1–9; for each, checks (after a wall-clock-stability settle):
  iframe height reaches the child's required height (within 4px); bottom
  slack ≤ 32px; no internal scrollbar from clipping; the contract still
  holds after changing the widget's first `<select>` (where one exists);
  the contract still holds at dark mode + 390px; zero resize-message/
  runtime errors (filtering the same two pre-existing, unrelated
  book-chrome noise strings as the Exercise 7 dark-mode spec).
- **`NOTEBOOK_AUTHORING_STANDARDS.md`** (modified) — new §8, "Interactive
  iframe height (WP35)": documents the shared, automatic mechanism (no
  per-widget wiring needed), clarifies the HTML `height` attribute is only
  a rough pre-JS fallback, and directs future activities to register in
  `iframe-height-contract.spec.ts`'s `CASES` list rather than writing a
  new one-off height test. Renumbered the old §8 ("Before you start a
  notebook-editing WP") to §9.

## Cross-book language audit

- **`tests/test_wp35_content_audit.py`** (added) — repository-wide
  student-facing language audit across every canonical notebook, portable
  notebook, and widget-config JSON for Exercises 1–9: (1) a forbidden-
  phrase/WP-number-reference/internal-script-path scanner with an
  explicit (currently empty) allowlist mechanism for future legitimate
  exceptions; (2) a dedicated "development partition" absence check across
  the same scope plus widget data artifacts.
- **`book/_static/widgets/configs/tree_ensemble_compare.json`** (modified)
  — `instructions`: "all five audited training replicates" → "all five
  training replicates".
- **`book/_static/widgets/configs/validation_stability.json`** (modified)
  — `description`: "a predeclared set of" → "a fixed set of".
- **`tests/test_wp24_content_audit.py`** — **not modified**; its existing
  `test_section_5_is_concise` word-count ceiling (220 words) already
  covered the Exercise 2 wording fix above once an equally-short
  replacement phrase was chosen (see WP35_REPORT.md §10).

## Reports

- **`WPs/reports/WP35_REPORT.md`** (added) — this report.
- **`WPs/reports/WP35_EXACT_CHANGELOG.md`** (added) — this file.

## Untouched (confirmed)

- `book/syllabus.md` — not opened or modified.
- `course_overview/` (Word course-overview document) — not opened or
  modified.
- `book/_toc.yml` — not modified.
- `book/_static/launch-buttons.js`, `book/_static/custom.css` — not
  modified (no CSS was found responsible for artificial iframe bottom
  space; see WP35_REPORT.md §7).
- Exercises 1, 3, 5's *canonical* notebooks — not modified (only their
  portable notebooks regenerated, banner-text only, from the generator
  fix above).
- `WPs/reports/WP16_ARCHITECT_REPORT.md`,
  `WPs/reports/WP21_DEPLOYMENT_REPORT.md` — preserved untracked, as
  required by WP35 §2.5.
