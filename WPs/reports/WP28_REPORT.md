# WP28 Report: Exercise 5 — Regularization and Feature Selection

## 1. Outcome

**Success.** Exercise 5 is a complete, executed notebook covering predefined vs. data-driven
feature selection, leakage-safe correlation/`SelectKBest` selection, Ridge and Lasso regression
(including a new interactive activity), a complete nested-CV regularization pipeline, and stepwise
selection via `SequentialFeatureSelector`. "Compare Two Feature Sets" moved from Exercise 2's Bonus
into Exercise 5 Section 2 with no numerical change to its underlying catalog. All work is local on
`feature/wp28-exercise5-regularization-feature-selection`; nothing was merged, pushed, or deployed.

## 2. Git state

**Starting branch:** `fix/wp27r-validation-refinements` at `cc711b9` (WP27R report/changelog),
matching the only permitted untracked files (`WPs/reports/WP16_ARCHITECT_REPORT.md`,
`WPs/reports/WP21_DEPLOYMENT_REPORT.md`), left untouched throughout.

**Working branch:** `feature/wp28-exercise5-regularization-feature-selection`, created from `cc711b9`.

**Final HEAD:** `2470b62e2d3c031661598621de27b3cf9426c4d2`

**Final `git status --short`:**
```
?? WPs/reports/WP16_ARCHITECT_REPORT.md
?? WPs/reports/WP21_DEPLOYMENT_REPORT.md
```

12 commits on the branch before this report (specification, stale-test fix, widget implementation,
notebook, Exercise 2 edit, portable notebooks, and four rounds of test/spec updates found by running
progressively broader gates), plus this report and the exact changelog.

## 3. Stale Exercise 4 launch-button test (§3)

`interactive/e2e-book/launch-buttons.spec.ts` asserted Exercise 4 had **no** Colab button — stale
since WP27. Corrected: Chapter 4 joined the `CHAPTERS` loop (full Colab/download/admonition
coverage, like chapters 1–3); the placeholder guard was retargeted twice as the branch progressed —
first to Exercise 5 (still a placeholder before §6's conversion), finally to Exercise 6 (the next
true placeholder after Exercise 5 became a notebook). Focused run: 17/17 passed at each stage.

## 4. Material moved from Exercise 2 to Exercise 5

**Removed from Exercise 2's Bonus** (cells `wp25-010`, `wp11-041`, `wp11-042`): the "Comparing
feature sets" heading and literature prose, the `regression_compare.json` iframe, and its
think-first admonition + exploratory-comparison warning. Bonus's intro sentence changed from "The
two activities below…" to "The activity below extends the main lesson with one further, optional
exploration…". Question 13 ("Two feature sets in the Bonus activity…") was removed and the
remaining two questions renumbered 13–14.

**Added to Exercise 5 Section 2** ("Compare Predefined Feature Sets"): the same prose (reframed —
"Prior knowledge can define a feature set before model fitting…"), the same iframe (config/data
files unchanged, `regression_compare.json` / `abide_regression_models.json`), the same think-first
box, and the same exploratory-comparison warning (reworded to "exploratory comparison" per the WP28
brief, from "exploratory model comparison"). A new transition paragraph ("The frontal
cortical-thickness set may predict age reasonably well — but are all of these features useful for
prediction?…") leads into Section 3.

**No numerical change.** The catalog (`abide_regression_models.json`), its exporter
(`scripts/export_regression_catalog.py`), and the widget's own component/config files were not
touched — only the notebook cells that embed the iframe and the frontend files' header comments
(`regression-compare.ts`, `regression-compare-data.ts`, `components/regression-compare.ts` —
comment-only, "Exercise II" → "Exercise 5").

## 5. Final Exercise 2 Bonus structure

```
## Bonus
"The activity below extends the main lesson with one further, optional
exploration of linear regression -- it is not required for the core session."
  ### What does sample size change?
  [unchanged: sensorimotor-bundle learning-curve code, plot, and admonition]
```

Exercise 2 is now 41 cells (was 44); its portable notebook is 43 cells (was 46). `exercise_02.html`
embeds exactly one iframe (`knn_explore.json`).

## 6. Final Exercise 5 outline

```
# Exercise 5: Regularization and Feature Selection
[run/download admonition -> book/downloads/chapter_05/exercise_05_portable.ipynb]
## What this notebook covers            (8-item numbered list, matches the 8 sections below)
## 1. Why Select Features?              (predefined vs. data-driven, leakage explanation; data load)
## 2. Compare Predefined Feature Sets   (moved regression-compare activity, reframed)
## 3. Select Features Using the Data    (training-only correlation ranking; SelectKBest in CV)
## 4. Ridge and Lasso Regression        (formulas, comparison table, concrete alpha=1/0.1 example)
## 5. Explore Regularization            ("Shrink the Coefficients" activity + optional Python reproduction)
## 6. A Complete Regularized Regression Pipeline  (nested CV: Linear vs Ridge vs Lasso, full cohort)
## 7. Other Feature-Selection Methods   (3-row table; SequentialFeatureSelector forward-selection demo)
## 8. How Do We Choose a Feature-Selection Method?  (single open-question admonition + <=4 bullets)
## In summary
### Questions to take away              (11 questions)
```

45 cells total (14 code, 31 markdown), two `<iframe>` activities, no stability/selection-frequency
material anywhere, no duplicate methods table.

## 7. Actual correlation-selection results (Section 3)

Computed on the 753-row outer-training partition only (251-row test set never read):

- correlation range across all 360 `fsCT_*` features: **[-0.563, +0.087]** — almost every feature
  correlates negatively with age (consistent with the widespread-cortical-thinning literature cited
  in Section 2), with no strongly positive end;
- most negative: `fsCT_L_5mv_ROI` (r=-0.563), `fsCT_L_DVT_ROI` (r=-0.557), `fsCT_R_V2_ROI` (r=-0.544),
  `fsCT_L_MBelt_ROI` (r=-0.538), `fsCT_R_23c_ROI` (r=-0.532);
- near zero: `fsCT_L_TGd_ROI` (r=-0.001) through `fsCT_L_PeEc_ROI` (r=-0.006).

**`SelectKBest` inside 5-fold `GridSearchCV`** (`KFold(5, shuffle=True, random_state=0)`), candidate
`k ∈ {5, 10, 20, 40, 80, 160, 360}`: cross-validation MSE improves from 49.1 (k=5) to a minimum of
**40.8 at k=80**, then worsens to 63.2 at k=360 (every feature) — selecting more features does not
always help.

## 8. Alpha grids and selected values

Manifest (`book/config/abide_modeling.json` → `regularization`): `ridge_alpha_grid =
np.logspace(-1, 5, 25)`, `lasso_alpha_grid = np.logspace(-3, 1, 25)` — audited empirically
(`scripts/regularization_model_audit.py`) on the same p=360 recipe Exercises 2/4 use, distinct from
the earlier p=1432 `regularization_preview` grids (WP12), which this exercise does not reuse.

**Dev-split curve** (n_fit=564, n_val=189, identical to `knn.dev_split`): unregularized linear
regression **overfits sharply** — validation R²=**-0.058** (worse than predicting the mean) despite
n_fit > p, because the 360 cortical-thickness columns are highly redundant. Ridge's best validation
alpha ≈ **562**, validation MSE ≈ **22.3** (all 360 coefficients nonzero). Lasso's best validation
alpha ≈ **0.215**, validation MSE ≈ **22.7**, **~100–102 nonzero coefficients** (run-to-run variation
of ±1 from BLAS-thread nondeterminism near the zero-threshold, not a bug).

**Outer nested-CV comparison** (Section 6; `KFold(5, shuffle=True, random_state=100)` outer,
`KFold(5, shuffle=True, random_state=101)` inner, full 1004-participant cohort, `np.logspace(-1,5,25)`
/ `np.logspace(-3,1,25)` grids, matching the manifest exactly): Linear mean MSE≈49.1 (R²≈0.427);
**Ridge mean MSE≈31.5 (R²≈0.645)**, alpha ∈ {316.2, 562.3} across the 5 outer folds (never at a grid
boundary); **Lasso mean MSE≈32.4 (R²≈0.636)**, alpha ∈ {0.147, 0.215}, **median ~91–118 nonzero
coefficients**. Both regularized models substantially outperform unregularized linear regression;
neither selected alpha sits at a grid boundary, so no grid expansion was needed.

*Deviation from the WP28 spec draft:* the spec's §4 mentioned reusing the already-audited p=1432
`regularization_preview` numbers from WP12. On review this was the wrong data (that grid targets a
literally underdetermined p>n case on `all-eligible × all-measures`); Exercise 5 instead computes
fresh Ridge/Lasso results on the same p=360 `all-eligible × CT` recipe Exercises 2 and 4 already
use, which is both more consistent with those notebooks and produces a cleaner "even n>p can overfit
with correlated predictors" story than the literal-underdetermined case would have.

## 9. Stepwise selection (Section 7)

Candidate set: 42 bilateral prefrontal cortical-thickness features (`frontal` bundle, 21 ROIs).
`SequentialFeatureSelector(direction="forward", n_features_to_select=17)` (verified to select the
identical 17-feature set as the manual step-by-step greedy curve) selects: `fsCT_L_a9-46v_ROI`,
`fsCT_R_a9-46v_ROI`, `fsCT_R_p9-46v_ROI`, `fsCT_L_9a_ROI`, `fsCT_R_9p_ROI`, `fsCT_L_8C_ROI`,
`fsCT_L_8Av_ROI`, `fsCT_L_8Ad_ROI`, `fsCT_L_IFJa_ROI`, `fsCT_L_IFJp_ROI`, `fsCT_R_IFSa_ROI`,
`fsCT_R_IFSp_ROI`, `fsCT_R_p47r_ROI`, `fsCT_L_a47r_ROI`, `fsCT_L_p32pr_ROI`, `fsCT_R_p32pr_ROI`,
`fsCT_R_8BM_ROI`. The full forward-selection curve (5-fold CV MSE) falls from 65.5 (1 feature) to a
minimum of **56.4 at 17 features**, then rises again to 59.6 at all 42 — the same "more features can
hurt" pattern as Section 3, on an independent feature set.

## 10. "Shrink the Coefficients" widget

Component: `interactive/src/components/regularization-explore.ts`. Controls: model select
(Linear/Ridge/Lasso), log-scale alpha range slider paired with an exact-value `<select>` (new
control pattern — no prior log-scale slider existed in this codebase; built on `knn-explore.ts`'s
slider+numeric-input wiring). Displays: observed-vs-predicted validation scatter with diagonal,
a sorted bar chart of the 14 tracked coefficients (union of Ridge's and Lasso's own top-12
largest-magnitude coefficients at their respective best alphas), and a performance line (train MSE,
validation MSE, selected alpha, best validation alpha, unregularized baseline, nonzero count,
coefficient norm). Linear Regression disables the alpha slider/select and shows a baseline note. No
test-set numbers appear anywhere in the widget (verified by e2e assertion). All 25×2 (model, alpha)
configurations are precomputed offline; no client-side model fitting.

**Asset sizes:** `regularization_explore.json` — **83,462 bytes raw / 32,577 bytes gzip**.

## 11. Portable notebooks

`book/downloads/chapter_05/exercise_05_portable.ipynb` (47 cells: banner, setup, install cell, then
the canonical 45 cells minus 2 `<iframe>` cells plus the 2 markdown pointer replacements — all 14
code cells preserved, including the `hide-cell`-tagged nested-CV and alpha-curve-reproduction cells,
fully visible here). `book/downloads/chapter_02/exercise_02_portable.ipynb` regenerated (43 cells,
down from 46) with the moved activity's pointer cell removed. Both smoke-executed top to bottom via
`nbconvert --execute` with zero errors (Exercise 2: ~17s; Exercise 5: ~108s, dominated by the nested-CV
and forward-selection cells).

## 12. Tests and builds (§25–26)

| Gate | Result |
|---|---|
| Focused launch-button test (14→17 tests as chapters were added) | PASS |
| `regularization_model_audit.py --check`, `export_regularization_widget.py --check`, `build_portable_notebook.py --check --notebook all` | PASS |
| Focused `test_exercise_02_notebook.py` (38 tests) | PASS |
| Focused `test_exercise_05_notebook.py` (40 tests) | PASS |
| Portable generation (`--write` + `--check`) | PASS |
| Exercise 2 + Exercise 5 portable smoke execution (`nbconvert --execute`) | PASS, 0 errors |
| Frontend typecheck (`tsc --noEmit`) | PASS |
| Focused `regularization-explore` unit tests (15) + e2e (12) | PASS |
| Focused moved-widget tests (`regression-compare*`, standalone e2e) | PASS |
| Production frontend build (`npm run build`) | PASS (1.59MB/521KB gzip bundle; pre-existing chunk-size warning, unrelated to WP28) |
| Jupyter Book build (clean, `rm -rf book/_build` + rebuild) | PASS, 1 warning (pre-existing `logo.png` missing) |
| Focused widget Playwright tests (`regularization-explore.spec.ts`, `plot-visual-policy.spec.ts`) | PASS |
| Focused built-book Exercise 2 + Exercise 5 tests (`chapter02.spec.ts`, `chapter05.spec.ts`, `chapter05-visual-policy.spec.ts`) | PASS |
| Light/dark (`wp22-cross-chapter-dark-mode.spec.ts`) + narrow-viewport checks | PASS |
| Full Python suite (`unittest discover -s tests`) | PASS, 551 tests, 11 pre-existing network-skips |
| Full frontend unit suite (`vitest run`) | PASS, 342 tests / 25 files |
| Full standalone Playwright suite | PASS, 174 tests |
| Full built-book launch-button spec | PASS, 17 tests (run per §3 and again at final state) |

**Corrections and reruns during the process:**

1. **Alpha-grid inconsistency (self-diagnosed).** The first draft of Section 6's nested-CV cell used
   a coarser `np.logspace(-1,5,13)`/`np.logspace(-3,1,13)` grid than the manifest's documented
   25-point grids; corrected before the first commit, notebook regenerated and re-executed.
2. **Frontend widget test failures (2).** `formatAlpha(100)` stripped trailing zeros from an integer
   (`"100"` → `"1"`) and a `parseRegularizationExploreData` test fixture had a length mismatch;
   both fixed in the same session, before any commit.
3. **Stale built app bundle.** The first standalone Playwright run against the new widget failed
   entirely (`data-widget-ready` never set) because `book/_static/widgets/app/` is a gitignored,
   prebuilt bundle that `npm run build` had not yet regenerated; fixed by running the build.
4. **Structural test bugs in `test_exercise_05_notebook.py` (5, self-diagnosed on first run).**
   An over-broad forbidden-table-row check matched Section 4's own Ridge/Lasso table; a phrase
   assertion didn't match the actual (more precise) wording used; two assertions broke on markdown
   line-wrap boundaries; one assertion flagged a legitimate code *comment* naming `X_test` as if it
   were a real read. All five fixed with more precise or whitespace-tolerant assertions.
5. **Stale `_static/launch-buttons.js` in the built book.** A normal `jupyter-book build` did not
   recopy the edited static file (sphinx's staleness check); required `rm -rf book/_build` + full
   rebuild. Found by the full built-book launch-button run.
6. **`chapter02-visual-policy.spec.ts` (found only by running the *full* built-book suite, not the
   targeted Exercise 2/5 specs).** This entire file's 12 tests exclusively exercised the
   regression-compare activity's plot geometry on Exercise 2's page; since that activity moved,
   the file moved with it (renamed `chapter05-visual-policy.spec.ts`, retargeted).
7. **Six repo-wide Python test files (found only by running the *full* `unittest discover`, not the
   two notebooks' own test files).** `test_book_structure.py`, `test_exercise_04_notebook.py`,
   `test_placeholder_exercises.py`, `test_wp24_content_audit.py`, and `test_wp25_content_audit.py`
   all carried hardcoded "Exercise 5 is a placeholder" or "chapters 1–4 are notebooks" assumptions
   predating WP28; all five updated (see the exact changelog for specifics), plus two new parity
   assertions added to `test_exercise_05_notebook.py`.
8. **Flaky geometry assertion under heavy parallel load (documented, not "fixed").** Running the
   *full* built-book Playwright suite with its default 6 workers intermittently fails one
   `chapter05-visual-policy.spec.ts` viewport variant's `clearance >= 12`px assertion (a different
   variant each time — "wide desktop" once, "742px content width" once). The same test passes
   reliably (3/3 repeats) when run in isolation or with `--workers=2` in a less loaded moment. This
   is the identical assertion, on identical widget code, that existed as `chapter02-visual-policy.spec.ts`
   before WP28 — a pre-existing timing sensitivity in this one geometry spec under system load, not a
   defect WP28 introduced. Per §26's "one diagnosis and correction; one rerun" allowance, this was
   diagnosed (confirmed environmental, not functional) and is reported rather than chased further.

No other gate required more than one attempt.

## 13. Deviations from the spec

- Reused Exercise 4's `knn.dev_split` fitting/validation split for the alpha-tuning sections
  (`regularization.dev_split` in the manifest is literally identical) rather than defining a new
  split, for exact participant-level consistency with Exercise 4.
- Section 6's alpha grids use 13→25 points (see correction #1 above) to match the manifest exactly.
- The regularization-audit numbers reused in §4 of the spec draft (p=1432 `regularization_preview`)
  were replaced with a fresh p=360 audit — see §8 above.
- `test_wp24_content_audit.py`'s `Exercise2SingleExploratoryWarning` class was renamed
  `Exercise5SingleExploratoryWarning` rather than deleted, since the underlying behavior it checks
  (the warning appears exactly once, after the activity) still needs a home — moved, not dropped.

## 14. Manual verification (§27)

Confirmed directly against the built book (`book/_build/html`) and the standalone widget app:
Exercise 2 has no feature-set-comparison material and remains coherent with its single-item Bonus;
Exercise 5 reads as one lesson through 8 sections; the moved activity renders and functions
identically from its new location; the correlation/`SelectKBest` leakage boundary is visible in the
code (test set never read before Section 6); Ridge/Lasso are described correctly per the standards
table; the alpha slider+select pair is usable and readable at both light and dark themes and at
390px; no stability section, table duplication, or third widget exists; the methods table has
exactly three rows; the stepwise section is code-and-a-static-figure, not a widget; the final
section is one open-question box with four bullets; Exercise 5's Colab/download links resolve to
`exercise_05_portable.ipynb`; Exercises 6–12 remain unchanged placeholder pages with no launch
button.

## 15. Final Git status

```
Branch: feature/wp28-exercise5-regularization-feature-selection
Status: only WPs/reports/WP16_ARCHITECT_REPORT.md and WP21_DEPLOYMENT_REPORT.md untracked
        (pre-existing, untouched)
```

Implementation HEAD before this report and the exact changelog:
`2470b62e2d3c031661598621de27b3cf9426c4d2`. This report and
`WPs/reports/WP28_EXACT_CHANGELOG.md` are committed after it, as the branch's final commit(s).

No merge, push, deploy, or GitHub Actions run was performed. WP29 was not started.
