# WP36 Exact Changelog

Every file added, modified, or removed by WP36 (correct Exercise 9's
PCR/PLS alignment activity to a variance-controlled target construction),
relative to the starting branch tip `fix/wp35-exercises7-9-review` @
`0e10af7`.

## Specification checkpoint (already committed before implementation)

- **`WPs/WP36_PCR_PLS_ALIGNMENT_SCALE_CORRECTION.md`** (added) — the WP36
  specification, committed as the initial checkpoint (`0342867`) before
  implementation.

## Manifest

- **`book/config/abide_modeling.json`** (modified) —
  `advanced_models.pcr_pls_activity`: replaced `noise_sd: 0.6` and the
  three presets' raw `beta_pc1`/`beta_pc2` coefficients with `signal_sd:
  1.0`, `noise_sd: 0.3`, and three presets keyed by unit-length
  `w1`/`w2` weights over standardized, orthogonal component scores
  (`weak`: `w1=0.25, w2=0.9682458365518543`; `moderate`:
  `w1=w2=0.7071067811865476`; `strong`: `w1=0.9682458365518543,
  w2=0.25`); rewrote the `note` field to describe the new construction and
  why it was needed. `advanced_models.abide_comparison` and
  `advanced_models.svm_activity` were not touched.

## Audit/export script

- **`scripts/export_pcr_pls_widget.py`** (modified) — replaced
  `_targets_for_preset`'s raw-coefficient construction with:
  `_standardize()`, `_orthogonalize()` (Gram-Schmidt helper),
  `_standardized_orthogonal_scores()` (produces `z_pc1`/`z_pc2`, exactly
  uncorrelated in-sample), and `_unit_noise()` (one fixed `N(0,1)` draw,
  orthogonalized against both standardized scores, rescaled to
  `noise_sd`); `SIGNAL_SD`/`NOISE_SD` module constants now read
  `signal_sd`/`noise_sd` from the manifest. `build_data()` now computes
  `trainR2`/`valR2` per catalog entry (via `sklearn.metrics.r2_score`) and
  a new top-level `fixedSignalNoiseNote` field; `presets` output renamed
  `betaPc1`/`betaPc2` → `weightPc1`/`weightPc2`; `generatingProcess` gained
  `signalSd`. `validate()` gained a unit-length preset-direction check and
  a `trainR2`/`valR2`-presence check. Module docstring rewritten to
  explain the WP36 correction and why the raw PC1/PC2 orthogonalization
  step was necessary (their real, non-negligible ~0.11 in-sample
  correlation).
- **`book/_static/widgets/data/pcr_pls_explore.json`** (modified,
  regenerated via `--refresh`) — new target values, catalog entries (with
  `trainR2`/`valR2`), `weightPc1`/`weightPc2` presets, `signalSd`, and
  `fixedSignalNoiseNote`; predictor `points`/`trainIds`/`valIds` byte-for-
  byte unchanged from WP35 (verified in
  `tests/test_export_pcr_pls_widget_data.py`). Re-validated offline
  (`--check`).

## Frontend schema and component

- **`interactive/src/pcr-pls-explore-data.ts`** (modified) — `catalogEntry`
  schema gained `trainR2`/`valR2` (`z.number().finite()`, not constrained
  non-negative since R² can be negative); top-level schema gained
  `fixedSignalNoiseNote`; `generatingProcess` gained `signalSd`; `presets`
  entries renamed `betaPc1`/`betaPc2` → `weightPc1`/`weightPc2`.
- **`interactive/src/components/pcr-pls-explore.ts`** (modified) — added a
  new always-visible `<p data-testid="pcr-pls-fixed-signal-noise-note">`
  paragraph (rendering `data.fixedSignalNoiseNote`, "Signal strength and
  noise are held constant; only the target's direction changes.");
  `drawText()`'s stats line now also reports `validation R² = X.XX`, and
  `container.dataset.valR2` is set alongside the existing MSE datasets.
  Header comment updated.
- **`interactive/src/config.ts`** (modified) — the "PCR or PLS?" config
  schema's doc comment updated to describe the new variance-controlled,
  unit-length-direction construction.

## Exercise 9 notebook and portable notebook

- **`book/chapters/chapter_09/exercise_09.ipynb`** (modified) — inserted a
  new markdown cell immediately after the "## 4. Interactive Activity --
  PCR or PLS?" heading, explaining (concisely) that all three presets
  share the same signal strength and noise level, that only the
  direction changes, and that PCR does best near PC1 while PLS helps most
  away from it; rewrote the hidden (`hide-cell`) illustrative reproduction
  cell to use the same standardized/orthogonalized/unit-length
  construction as the real activity data (previously used the old raw
  `0.3*pc1 + 0.85*pc2` coefficient form). Sections 1-3, 5-11 (including
  the ABIDE nested-CV comparison in Section 8) were not touched. Re-
  executed (default `RUN_FULL_NESTED_CV=False` path); 0 stored errors.
- **`book/downloads/chapter_09/exercise_09_portable.ipynb`** (modified,
  regenerated via `build_portable_notebook.py --write --notebook
  chapter_09`) — carries the same two changes; smoke-executed outside the
  repository tree twice (via `scripts/smoke_portable_notebook.py` and,
  independently, a direct `jupyter nbconvert --execute --inplace` on a
  `/tmp` copy), 0 errors both ways.

## Tests

- **`tests/test_export_pcr_pls_widget_data.py`** (modified) — added:
  `test_predictor_cloud_and_split_are_byte_for_byte_unchanged_from_wp35`
  (a hermetic SHA-256 hash check against the pre-WP36 committed values, no
  git dependency at test time); `test_preset_directions_are_unit_length`;
  `test_weak_and_strong_are_symmetric`;
  `test_pcr_mse_strictly_improves_weak_to_moderate_to_strong`;
  `test_pcr_r2_strictly_improves_weak_to_moderate_to_strong`;
  `test_signal_variance_equal_across_presets`;
  `test_noise_vector_and_variance_identical_across_presets`;
  `test_total_target_variance_comparable_across_presets`;
  `test_signal_to_noise_ratio_identical_across_presets`. Updated
  `test_pcr_and_pls_converge_once_both_components_are_retained` to also
  compare `valR2` and per-point `valPredictions`. `test_weak_moderate_
  strong_trend_at_one_component` and `test_presets_labelled_for_highest_
  variance_direction` (from WP35) kept and still pass unmodified.
- **`tests/test_exercise_09_notebook.py`** (modified) — added
  `test_reproduction_cell_uses_the_variance_controlled_construction` and
  `test_intro_explains_fixed_signal_and_noise_across_presets` to
  `PcrPlsSection`; all other existing tests in this 53-test file (up from
  51) needed no change (all previously used content-based lookup, not
  hardcoded cell indices).
- **`interactive/tests/pcr-pls-explore-data.test.ts`** (modified) — updated
  the shared `validData()` fixture: `presets` now uses
  `weightPc1`/`weightPc2`; catalog entries gained `trainR2`/`valR2`; top
  level gained `fixedSignalNoiseNote`; `generatingProcess` gained
  `signalSd`.
- **`interactive/e2e/pcr-pls-explore.spec.ts`** (modified) — added a
  Node-side reader of the committed `pcr_pls_explore.json` artifact
  (independent of the widget under test); added "the fixed signal/noise
  note is visible" and "validation R² is shown and matches the committed
  artifact for every preset/method/component combination" (12
  combinations, each checked against the artifact's own `valMse`/`valR2`
  rather than only checking that displayed text changed, per WP36 §7).

## Reports

- **`WPs/reports/WP36_REPORT.md`** (added) — this report.
- **`WPs/reports/WP36_EXACT_CHANGELOG.md`** (added) — this file.

## Untouched (confirmed)

- `book/syllabus.md` — not opened or modified.
- `course_overview/` (Word course-overview document) — not opened or
  modified.
- `scripts/advanced_models_audit.py`,
  `scripts/advanced_models_audit_result.json` — not opened or modified.
- `book/config/abide_modeling.json`'s `advanced_models.abide_comparison`
  and `advanced_models.svm_activity` keys — not modified.
- `book/chapters/chapter_09/exercise_09.ipynb` Sections 1-3 and 5-11
  (Support Vector Machines, Kernels, the SVM activity, the ABIDE nested-CV
  comparison, strengths/weaknesses, test-oriented questions, takeaways) —
  not opened or modified.
- `interactive/e2e-book/*.spec.ts` — no new built-book spec files were
  added; the existing `chapter09.spec.ts`, `chapter09-dark-mode.spec.ts`,
  and `iframe-height-contract.spec.ts` needed no changes and all still
  pass unmodified.
- `WPs/reports/WP16_ARCHITECT_REPORT.md`,
  `WPs/reports/WP21_DEPLOYMENT_REPORT.md` — preserved untracked, as
  required by WP36 §2.5.
