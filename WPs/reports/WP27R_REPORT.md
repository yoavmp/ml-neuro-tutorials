# WP27R Report — Exercise 4 Interaction and Nested-CV Refinements

## Overall result: SUCCESS

All four refinements described in
`WPs/WP27R_EXERCISE_4_INTERACTION_AND_NESTED_CV_REFINEMENTS.md` were
implemented, re-verified against a re-run deterministic audit, and covered by
new or updated tests. Every gate in the bounded-validation list passed; none
needed the allowed one-diagnosis-and-rerun (two unrelated, quickly-fixed
issues came up during implementation itself -- see "Corrections made" below
-- but no bounded-validation *gate* failed and needed a rerun).

## Starting and final SHA

- Starting point: `8d48bca` on `feature/wp27-validation-cross-validation`
  (`WP27: fix unresolved placeholder in final-git-state section of report`).
- Specification commit: `31d5b17` (`fix/wp27r-validation-refinements`).
- Implementation commit: `83f3f3a` (`WP27R: densify k grids, reveal third
  test-MSE panel, replace nested-CV diagram`).
- Final SHA: this report's own commit, on `fix/wp27r-validation-refinements`
  -- read from `git log --oneline --decorate -5` in "Final git state" below
  rather than from this line, since a commit cannot record its own hash.

## Final hidden-test candidate grid (Part B / "Choose k Before Revealing the Test Set")

```text
[1, 2, 3, 5, 8, 10, 15, 20, 25, 30, 50, 75, 100, 150, 250, 400, 564]
```

Was `[1, 2, 3, 5, 8, 12, 20, 30, 50, 75, 100, 150, 250, 400, 564]`. Added
`10, 15, 25`; dropped the stale `12` (no longer needed once `10`/`15`
bracket it); kept the very small candidates (`1, 2, 3, 5`, needed for the
training-selected-k overfitting demonstration) and every candidate above 50
unchanged. Contains all of the spec's required values: `8, 10, 15, 20, 25,
30, 50`.

## Final nested-CV candidate grid (Part C / "Look Inside Nested Cross-Validation")

```text
[8, 10, 12, 15, 18, 20, 22, 25, 28, 30, 40, 50]
```

Was `[5, 15, 30, 50, 75]`. Adopted the spec's suggested audit grid directly
(no adjustment was needed for model or runtime constraints -- `GridSearchCV`
over 12 candidates x 5 inner folds x 5 outer folds runs in well under a
second on this data). 8 of the 12 candidates fall in the required 10-30
densification range.

## Training-selected, validation-selected, and test-optimal k

From the re-run audit (`scripts/wp27_validation_audit_result.json`,
`part_b_train_val_test_tuning`):

- **Training-selected k = 1** (train MSE = 0.0, as always -- k=1 trivially
  memorizes the fitting set regardless of grid density).
- **Validation-selected k = 25** (validation MSE = 26.66; the previous grid's
  k=20 scores 27.13, close behind -- the densified grid found a slightly
  better validation candidate right next to the old one, exactly the
  "sparse around the optimum" problem the spec described).
- **Test-optimal k = 8** (test MSE = 31.07, R² = 0.667) -- **retrospective
  teaching information only**, computed and shown after the fact; it is
  never used to select anything, and the notebook/widget do not present it
  as a recommendation.

For comparison, locking the validation-selected k=25 scores test MSE = 32.58
(R² = 0.651); locking the training-selected k=1 scores test MSE = 50.19
(R² = 0.462). The validation-selected value again beats the training-selected
value on this test set, as it did before densification (this was not
re-engineered to hold -- it is the outcome of the same one predeclared
outer/development split reused from Exercise 2, per WP27's original
audit design).

## Test and validation curve comparison

Across the candidate grid, training MSE falls monotonically from 92.5 (k=564)
to 0.0 (k=1) -- it never turns around. Both validation MSE and test MSE
instead dip to an interior minimum and rise again at both ends (validation
minimum at k=25, MSE 26.66; test minimum at k=8, MSE 31.07, with k=8 through
k=30 all within about 2 MSE of each other -- a shallow bowl). The revealed
test curve's *shape* -- U-shaped, not monotonic -- resembles the validation
curve far more than the training curve. The notebook and widget both use
"tracks"/"resembles" language for this, per the spec's instruction not to
claim a computed correlation; none was computed.

## Selected k per outer fold, before and after grid densification

| | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Distinct values |
| --- | --- | --- | --- | --- | --- | --- |
| Before (`[5, 15, 30, 50, 75]`) | 15 | 15 | 15 | 15 | 15 | 1 |
| After (`[8, 10, 12, 15, 18, 20, 22, 25, 28, 30, 40, 50]`) | 15 | 12 | 10 | 18 | 15 | 4 |

**The outer folds now select different values of k.** This is the honest
outcome of the re-run deterministic audit (same outer seed 100, same inner
seed 101, same participants, same split) with only the candidate grid
changed -- no seed was chosen or candidate deleted to manufacture this
result. Mean outer-test MSE moved from 33.17 (sd 6.90) to 33.36 (sd 7.49);
mean outer-test R² from 0.621 to 0.620 -- both changes are small, as
expected, since densifying the grid mainly changes *which* nearby k each
fold picks, not the overall quality of the tuning procedure. The notebook's
interpretation text was rewritten to report this specific outcome (see
`tests/test_exercise_04_notebook.py::WP27RGridsAndActivity::test_prose_reports_the_real_outcome_without_falsifying_it`,
which is itself conditioned on the audit's own `selected_k_varies_across_folds`
flag rather than hardcoding an assumption).

## Diagram implementation method

The Mermaid `flowchart TD` in Section 6 is replaced by a native, inline
HTML/CSS diagram (class `ml-ncv-diagram`) built directly in the notebook
markdown cell -- no image, no JavaScript library, no Mermaid. It shows:

- an outer grid: 5 rows (matching the real `N_OUTER=5`) x 5 columns, one
  outer-test column (muted yellow) rotating per row, the rest outer-training
  (muted blue); the row corresponding to outer iteration 2 is outlined to
  mark which iteration's training data the inner grid zooms into;
- an inner grid of the same shape (matching `N_INNER=5`) using inner-training
  (muted green) / inner-validation (muted orange);
- three operation labels to the right: "Choose `k`" (against the inner-
  validation color), "Refit the selected `k` on all outer-training data",
  and "Evaluate the tuning procedure" (against the outer-test color);
- a color legend above the grids and a caption below stating that inner-
  validation folds choose k, outer-test folds evaluate the complete tuning
  procedure, and outer-test folds never choose k.

Every colored element sets its color via
`background-color:var(--ml-ncv-<role>, #<fallback-hex>)`. The four
`--ml-ncv-*` custom properties are defined with light defaults on `:root` and
dark overrides in the existing `html[data-theme="dark"]` block in
`custom.css`, so the website gets a theme-aware diagram automatically;
everywhere else (the portable notebook, Colab, GitHub, plain Jupyter -- none
of which load this stylesheet) the inline fallback renders the same static,
light-mode-equivalent colors, so the diagram never looks broken or
uncolored. All other styling (layout, gaps, `overflow-x:auto` for narrow
screens, font sizes) is inline as well, so it does not depend on any
external stylesheet either. The whole block is one continuous HTML block
(no blank lines), which MyST/CommonMark passes through as raw HTML on the
website exactly like the pre-existing `<iframe>` activity blocks already do,
and which `scripts/build_portable_notebook.py` copies verbatim into the
portable notebook (confirmed: `grep 'ml-ncv-diagram'
book/downloads/chapter_04/exercise_04_portable.ipynb` matches).

An `aria-label` on the wrapping element and the caption paragraph provide
the accessible-text requirement; the grids themselves are `aria-hidden`
since they are decorative relative to that text.

## Cells hidden on the website

Four code cells now carry a `hide-input`/`hide-cell` tag in
`exercise_04.ipynb` (confirmed by the built-book grep for "Hide code cell" /
"Show code cell": 4 matches each):

1. the Section-1 data-loading cell (`hide-input`, pre-existing);
2. the Section-3 fixed-k cross-validation reproduction (`hide-cell`,
   pre-existing);
3. **new**: the Section-5 fit/validation tuning-reproduction cell
   (`hide-cell`);
4. **new**: the Section-5 one-time reveal cell (`hide-cell`).

The new "### Optional: Reproduce the Tuning Activity in Python" heading and
its one-sentence blurb, and the "A few things to hold onto" interpretation
markdown cell that follows the reveal cell, are markdown cells and are never
collapsed -- markdown cells have no `hide-*` mechanism in this project, so
the conceptual explanation stays visible by construction, satisfying the
spec's "do not hide unique conceptual explanations together with the
optional code."

## Portable-notebook behavior

Regenerated via `scripts/build_portable_notebook.py --write --notebook
chapter_04` from the edited canonical notebook (no manual edits to the
portable file). Confirmed:

- all `hide-*` tags are stripped, so both Section-5 reproduction cells are
  visible and runnable (the generator's existing, unmodified behavior);
- the diagram's raw HTML survives untouched (`convert_myst_directives` only
  rewrites `{admonition}`/`{dropdown}` fences, which the diagram is not);
- the reveal cell (`STUDENT_CHOICE_K = validation_selected_k`) still has no
  saved output, consistent with every other code cell in this portable
  notebook (the project's blanket no-saved-outputs convention, as WP27's
  report already noted -- not a new exception);
- `scripts/smoke_portable_notebook.py --notebook chapter_04` executes the
  regenerated notebook end to end and its updated expected-value list
  (`validation-selected k = 25`, test MSE 32.6, nested selection
  `[15, 12, 10, 18, 15]`, mean outer-test MSE 33.4) matches exactly.

## Regenerated assets and sizes

| File | Raw bytes | Gzip bytes |
| --- | ---: | ---: |
| `book/_static/widgets/configs/validation_lock_test.json` | 1,265 | 654 |
| `book/_static/widgets/configs/nested_cv_explorer.json` (unchanged) | 937 | 541 |
| `book/_static/widgets/data/wp27_validation_lock_test.json` | 2,708 | 1,002 |
| `book/_static/widgets/data/wp27_nested_cv_explorer.json` | 2,044 | 924 |

`wp27_validation_stability.json` (Part A) is unchanged and was not
regenerated -- Part A's sample-size stability audit does not depend on
either candidate-k grid, confirmed byte-identical by
`scripts/export_wp27_widget_data.py --check`.

## Tests and builds run (spec section 10, in order)

| # | Gate | Result |
| --- | --- | --- |
| 1 | `python3 scripts/wp27_validation_audit.py --run` / `--check`, `python3 scripts/export_wp27_widget_data.py --check` | PASS |
| 2 | `python3 -m unittest tests.test_exercise_04_notebook tests.test_wp27_validation_audit` | PASS (71 tests) |
| 3 | `python3 scripts/build_portable_notebook.py --check` (all 4 notebooks) | PASS |
| 4 | `python3 scripts/smoke_portable_notebook.py --notebook chapter_04` | PASS |
| 5 | `npm run typecheck` (interactive/) | PASS |
| 6 | Focused unit tests: `validation-lock-test-data`, `nested-cv-explorer-data`, `config.test.ts` | PASS (93 tests) |
| 7 | `npm run build` (interactive/) | PASS (pre-existing >500KB chunk warning only) |
| 8 | `jupyter-book build book` | PASS (2 pre-existing, unrelated warnings: missing `logo.png`, `README.md` not in a toctree) |
| 9 | Focused Playwright: `validation-lock-test`, `nested-cv-explorer`, `validation-stability`, `plot-visual-policy` | PASS (43 tests); also ran the **full** standalone widget suite (161 tests, all pass) since `plotly-policy.ts` and `custom.css` are shared across every widget |
| 10 | Focused built-book Playwright: `chapter04.spec.ts`, `wp22-cross-chapter-dark-mode.spec.ts` | PASS (11 tests) |
| 11 | Light/dark diagram + three-panel plot checks | PASS -- new assertions: trace count 2→3 across lock, dark-mode `--ml-ncv-outer-train` resolves to the dark hex, methodology warning visible |
| 12 | Narrow-screen (390px) checks | PASS -- existing document-overflow check plus a new diagram-visibility check |
| 13 | `python3 -m unittest discover -s tests` (full suite, once) | PASS (511 tests, 11 pre-existing skips) |
| 14 | `npx vitest run` (full frontend unit suite, once) | PASS (323 tests) |

**No bounded-validation gate failed.** The spec's one-diagnosis-one-rerun
allowance was not needed for any of the 14 gates.

## Corrections made during implementation (not gate failures)

1. **Class-name leak.** The diagram's first draft used the prefix
   `wp27-ncv-*` (matching this WP's name), which tripped the pre-existing
   `test_no_wp_or_script_references_in_student_text` guard once the
   notebook was re-executed (`'wp27' unexpectedly found` in the markdown).
   Renamed to `ml-ncv-*` (matching the project's existing `--ml-*` token
   convention) in `custom.css`, the notebook, and the portable notebook.
   Caught and fixed before any gate ran, in the same editing pass.
2. **CSS placement.** A first edit to `custom.css` accidentally nested the
   light-mode `--ml-ncv-*` fallback values inside the existing
   `html[data-theme="dark"]` block instead of `:root`. Caught on review
   before running any gate; corrected by moving the light values to `:root`
   and merging the dark values into the single existing dark block (no
   duplicate `html[data-theme="dark"]` selector left behind).

Neither correction required rerunning a bounded-validation gate a second
time -- both were fixed before gates 1-14 were run in their final form.

## Deviations from spec

- Section 10 gate 9 ("focused widget Playwright tests") explicitly names a
  focused subset; this report also ran the full 161-test standalone widget
  suite as an extra precaution, because `plotly-policy.ts` (the shared axis-
  layout helper) and `custom.css` both changed and are used by every widget,
  not just the three Exercise 4 ones. All 161 passed -- no regression.
- One **pre-existing, unrelated** failure was discovered while running the
  full built-book Playwright suite beyond the spec's focused gate list:
  `interactive/e2e-book/launch-buttons.spec.ts` still asserts that Exercise
  4 "gets no Colab button" (`a placeholder exercise page (Exercise 4) gets
  no Colab button`), which has been false since WP27 gave Exercise 4 a real
  Colab button. This predates WP27R entirely (WP27's own bounded-validation
  gates never exercised `launch-buttons.spec.ts`) and is out of this WP's
  four-item scope (spec section 0). **Left unfixed and flagged for user
  attention** rather than fixed here, to avoid scope creep into WP27
  cleanup; see "Requires user attention" below.
- No deviation from the "do not change participants/predictors/target/
  splits/seeds/scaling/primary metric" constraint (spec section 8) was
  needed or made.

## Manual verification (spec section 11)

- Denser k controls: confirmed via Playwright that all 17 lock-test k-tabs
  render and wrap responsively (`.widget-tabs` is pre-existing
  `flex-wrap: wrap`), and that `k-12` is genuinely absent.
- Third panel genuinely unavailable before locking: confirmed by reading
  the live Plotly figure's own `.data` array length (2 before, 3 after) in
  both the standalone widget and the built book -- not just a visual/CSS
  hidden check.
- Three curves easy to compare: matched log x-axes (`matches: "x"`) and one
  shared y-range across all three panels, recomputed to include test values
  only after locking.
- Methodological warning: present and visible immediately once locked,
  independent of the reset button/note (a separate paragraph, not folded
  into the reset warning).
- Optional Python reproduction: collapsed by default on the built page,
  confirmed via the built-book Playwright test; does not interrupt the
  markdown flow (the interpretation prose after it stays visible).
- New nested-CV diagram: confirmed present, Mermaid confirmed absent, in
  both the built book and the portable notebook.
- Selected k values in prose match regenerated data: cross-checked by a
  dedicated test (`test_displayed_selected_k_table_matches_regenerated_audit`)
  reading `scripts/wp27_validation_audit_result.json` directly.
- Light mode, dark mode, narrow layouts: confirmed via Playwright
  (computed-style / custom-property assertions, the same methodology the
  pre-existing Exercise 1-4 dark-mode suite already uses).
- No unrelated notebook changed: confirmed by `git status --short` showing
  only the 16 files listed in the exact changelog, plus the two pre-existing
  permitted untracked reports, left untouched.

## Final git state

```text
$ git log --oneline --decorate -5
83f3f3a (HEAD -> fix/wp27r-validation-refinements) WP27R: densify k grids, reveal third test-MSE panel, replace nested-CV diagram
31d5b17 WP27R: add Exercise 4 interaction and nested-CV refinements specification
8d48bca (feature/wp27-validation-cross-validation) WP27: fix unresolved placeholder in final-git-state section of report
a699e8a WP27: built-book Playwright coverage for Exercise 4 (gate 8/10)
4cfbb45 WP27: Playwright tests for the three Exercise 4 widgets

$ git status --short --branch
## fix/wp27r-validation-refinements
?? WPs/reports/WP16_ARCHITECT_REPORT.md
?? WPs/reports/WP21_DEPLOYMENT_REPORT.md
```

(The two untracked files are pre-existing, out-of-scope reports from
unrelated prior work packages, explicitly left untouched throughout this
session.) This report and `WPs/reports/WP27R_EXACT_CHANGELOG.md` are
committed after this text is written; their commit's SHA becomes the new
`HEAD` on `fix/wp27r-validation-refinements` and should be read from a fresh
`git log`, not this line.

## Requires user attention

- `interactive/e2e-book/launch-buttons.spec.ts`'s "Exercise 4 gets no Colab
  button" test is stale (pre-dates WP27R, unrelated to this WP's scope) and
  should be fixed or removed in a future, small WP27-cleanup pass -- it does
  not affect anything WP27R touched and was not fixed here to keep this
  branch's diff scoped to the four refinements in the spec.
- All other work is complete, local, and green on
  `fix/wp27r-validation-refinements`. Nothing was merged, pushed, deployed,
  or monitored in CI, and WP28 was not started, per spec section 13.
