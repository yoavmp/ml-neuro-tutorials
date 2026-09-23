# WP33 Report — Exercise 8: Unsupervised Learning

## 1. Overall result

**SUCCESS.** Exercise 8 ("Unsupervised Learning") replaces the WP25
placeholder with a complete notebook covering PCA, K-means, an exploratory
research example, and PCA inside a supervised age-prediction pipeline, with
two new browser-native interactive activities, audit scripts, and a
multi-layer test suite. All bounded validation gates passed. Everything is
committed locally on `feature/wp33-exercise8-unsupervised-learning`; nothing
was merged, pushed, deployed, or monitored through GitHub Actions.

## 2. Starting branch and SHA

- Branch: `feature/wp32-exercise7-gradient-boosting`
- HEAD SHA: `73d802b4dbbbcc4e3085ce46ece422d45ac897c4`
- This matched the tip of `feature/wp32-exercise7-gradient-boosting` exactly
  (`git rev-parse feature/wp32-exercise7-gradient-boosting` returned the
  same SHA), satisfying WP33 §2's precondition. Exercise 7 was confirmed
  complete (`book/chapters/chapter_07/exercise_07.ipynb`, real notebook) and
  Exercise 8 was confirmed still a placeholder
  (`book/chapters/chapter_08/exercise_08.md`) before any change was made.
  The two pre-existing untracked files (`WPs/reports/WP16_ARCHITECT_REPORT.md`,
  `WPs/reports/WP21_DEPLOYMENT_REPORT.md`) were present and have been
  preserved throughout (never staged, moved, or deleted).

## 3. Final branch and SHA

- Branch: `feature/wp33-exercise8-unsupervised-learning` (created from the
  SHA above)
- Checkpoint commit (spec added before implementation): `d76437d`
- Implementation commit: `0d9bf16bba85345fd3dfa82b3b71c271783219a6`
  ("WP33: Exercise 8 — Unsupervised Learning")
- This report and the exact changelog are committed as one further commit
  on top of `0d9bf16` (see §14 for the exact final SHA, captured after that
  commit).

## 4. Exact notebook sections created

`book/chapters/chapter_08/exercise_08.ipynb`, 33 cells, in order:

- Title (`# Exercise 8: Unsupervised Learning`)
- Green "Run or download this notebook" admonition
- "What this notebook covers" (4-item list, concise, prerequisites noted)
- `## 1. Learning Without a Target` (+ Think First admonition)
- Hidden data-loading cell (`hide-input`): loads the same pinned ABIDE-II
  table Exercises 2/4/5/6/7 use, 1004 participants x 360 cortical-thickness
  features
- `## 2. PCA: Representing Many Features with Fewer Dimensions` (concept
  only; explicitly states PCA is feature extraction, not feature selection)
- `## 3. Interactive Activity -- Find the Best Projection` (+ iframe +
  hidden optional Python reproduction cell)
- `## 4. PCA with ABIDE-II Neuroimaging Data`: standardization rationale,
  hidden PCA-fit cell, scree/cumulative-variance plot, PC1-PC2 scatter,
  individual-ROI signed-loading bars (PC1/PC2, top 8 each), grouped
  mean-absolute-loading bars (frontal/parietal/temporal/occipital),
  interpretation prompts
- `## 5. Clustering and K-Means` (concept only: 4 K-means steps, the 3
  k-selection considerations, "no single objectively correct k" caveat)
- `## 6. Research Example -- Exploring Neuroanatomical Profiles`: explicit
  5-step workflow, a hidden K-means demonstration
  (retainedPc=10, k=3, seed=0, `n_init=10`), arbitrary-cluster-label caution
- `## 7. Interactive Activity -- Explore PCA and K-Means` (+ iframe; no
  separate hidden reproduction cell, since section 6's code already
  demonstrates the identical workflow on the website and in the portable
  notebook)
- `## 8. PCA Inside a Supervised Prediction Pipeline`: pipeline code shown,
  hidden split cell, hidden CV-tuning cell (component grid `[2, 5, 10, 20,
  50, 100, 200]`), visible results table, baseline comparison, leakage
  explanation, Think First question
- `## 9. What Should We Remember?` + 6 exam-style takeaway questions

Cell count (33) is below Exercise 1's cell count and above the 25-cell
floor, and the notebook is visibly less dense than Exercise 1 (confirmed by
`OpeningStructure.test_cell_count_is_reasonable_and_shorter_than_exercise_01`
and by manual review of the built page).

## 5. Both activities and their controls

**Activity A -- `pca-projection` ("Find the Best Projection")**
- Controls: projection-angle slider (0-180 deg, step 1), "Show PC1" /
  "Hide PC1" reveal toggle, Reset
- Data: a fixed, mean-centered, synthetic 40-point 2-D cloud
  (`scripts/export_pca_projection_widget.py`; sigma_x=3.0, sigma_y=2.0,
  rho=0.75, seed=11)
- All projection math (captured variance, reconstruction MSE) is pure
  closed-form trigonometry computed live in the browser
  (`interactive/src/pca-projection-data.ts#projectAtAngle`) from the fixed
  point cloud -- no model fitting, no Python runtime in the browser
- True PC1 stays hidden until the reveal control is pressed (verified by a
  Playwright assertion and by the notebook-content test)

**Activity B -- `pca-kmeans-explorer` ("Explore PCA and K-Means")**
- Controls: retained-PC-count select (`[2, 5, 10, 20, 50]`), k select
  (`[2, 3, 4, 5, 6]`), seed select (`[0, 1, 2]`), external-characteristic
  select (diagnosis / sex / acquisition site / age)
- PCA fit once (`n_components=50`) on the real 1004-participant, standardized
  360-feature cohort; PC1/PC2 scores stored once (nested-component
  invariant, locked in by a dedicated test)
- A precomputed catalogue covers all 5 x 5 x 3 = 75 (retainedPc, k, seed)
  combinations, each with `KMeans(n_init=10, random_state=seed)`, inertia,
  silhouette (only where mathematically valid), cluster sizes, and centers
  projected to PC1-PC2
- Outputs: PC1-PC2 scatter colored by cluster + centers, inertia-across-k
  and silhouette-across-k curves, cluster-size bars, and an
  external-characteristic composition panel that switches chart type
  (normalized bars for diagnosis/sex, a normalized heatmap for acquisition
  site, box plots for age)
- A visible note states clustering uses every retained component even
  though the scatter always shows only PC1-PC2

## 6. ABIDE participant/feature counts

1004 eligible participants, 360 cortical-thickness features -- identical to
every other exercise notebook (Exercises 2, 4, 5, 6, 7), confirmed by
`scripts/pca_kmeans_audit.py` and asserted by
`tests/test_pca_kmeans_audit.py`.

## 7. PCA explained-variance and loading-summary audit results

From `scripts/pca_kmeans_audit_result.json` (`scripts/pca_kmeans_audit.py --run`):

- PC1 explained variance = 36.1%, PC2 = 5.9%
- Cumulative explained variance: PC2=42.0%, PC5=49.4%, PC10=54.3%,
  PC20=60.1%, PC50=70.2%
- PC1 loadings are 100% one sign (a global, whole-cortex pattern); PC2's
  strongest individual ROIs are temporal/medial-temporal (PHA1, EC, TGd,
  AAIC, PeEc, H, TGv) -- a genuinely regional pattern, matching the
  notebook's own interpretive prompt
- Grouped mean-absolute loading (never a signed sum):

  | group     | PC1    | PC2    |
  |-----------|--------|--------|
  | frontal   | 0.0577 | 0.0453 |
  | parietal  | 0.0594 | 0.0390 |
  | temporal  | 0.0516 | 0.0622 |
  | occipital | 0.0489 | 0.0402 |

  These match the printed notebook output exactly (both are computed from
  the identical `abide_modeling.json` bundle ROI lists, inlined into the
  notebook the same way Exercise 5 inlines its frontal bundle, and audited
  independently in `scripts/pca_kmeans_audit.py`).

## 8. K-means catalogue ranges, defaults, and artifact sizes

- `retainedPcGrid = [2, 5, 10, 20, 50]`, `kGrid = [2, 3, 4, 5, 6]`,
  `seeds = [0, 1, 2]`, `n_init = 10`
- Defaults: retainedPc=10, k=3, seed=0, external variable=diagnosis (`group`)
- `book/_static/widgets/data/pca_kmeans_explorer.json`: **962,448 bytes
  uncompressed (940.9 KiB)**, **50,481 bytes gzip -9 (49.3 KiB)** -- larger
  than most other widget artifacts in this course because it stores a
  1004-length cluster-label array for each of 75 combinations, but this is
  the minimum needed to cover the full required grid without dropping an
  educational control; gzip (which GitHub Pages applies automatically)
  reduces the network transfer to under 50 KiB.

## 9. Supervised PCA candidates, chosen component count, and final metrics

- Candidate grid: `[2, 5, 10, 20, 50, 100, 200]`
- `KFold(n_splits=5, shuffle=True, random_state=13)` on the outer
  development partition (n=753) only; `StandardScaler` and `PCA` fit inside
  every fold via an `sklearn.Pipeline`
- Selected: **50 components** (mean CV MSE = 32.7)
- Locked outer test (n=251), evaluated once: PCA pipeline test MSE = 29.9,
  test R² = +0.680
- Baseline (`StandardScaler` + `LinearRegression`, no PCA), same split: test
  MSE = 49.6, test R² = +0.469
- On this cohort and split, PCA substantially **improves** prediction
  (ordinary least squares on 360 highly correlated features overfits the
  753-row development partition; PCA's dimensionality reduction regularizes
  it). The notebook reports this without claiming PCA must always win, per
  spec, and the audit script would have reported the opposite result
  faithfully had that been the outcome.

## 10. Validation gates (bounded plan, run in order)

| # | Gate | Command(s) | Result |
|---|------|------------|--------|
| 1 | Focused audit-script tests | `pca_kmeans_audit.py --run` then `--check`; `export_pca_projection_widget.py --refresh`/`--check`; `export_pca_kmeans_widget.py --refresh`/`--check` | All OK; `pca_kmeans_audit.py --run` ~4.2s |
| 2 | Focused Exercise 8 notebook/content tests | `unittest discover -p 'test_exercise_08_notebook.py'` | 46 tests, 0.066s, OK (after 1 correction, see §11) |
| 3 | Portable-notebook generation + `--check` | `build_portable_notebook.py --write --notebook chapter_08` then `--check --notebook all` | 35 cells written; all 8 registered notebooks up to date |
| 4 | Portable Exercise 8 smoke execution outside repo tree | copied `exercise_08_portable.ipynb` to a fresh temp dir, `jupyter nbconvert --to notebook --execute --inplace` | 0 errors |
| 5 | Focused frontend unit tests + typecheck | `npx vitest run tests/pca-projection-data.test.ts tests/pca-kmeans-explorer.test.ts tests/pca-kmeans-explorer-data.test.ts`; `npm run typecheck` | 26/26, typecheck clean |
| 6 | One frontend production build | `npm run build` | succeeded (pre-existing >500kB chunk-size warning, unrelated to WP33) |
| 7 | Focused standalone Playwright tests | `npx playwright test e2e/pca-projection.spec.ts e2e/pca-kmeans-explorer.spec.ts` | 16/16, 6.2s |
| 8 | One Jupyter Book build | `rm -rf book/_build && jupyter-book build book` | succeeded; chapter_08 executed in 6.06s; 2 pre-existing unrelated warnings (stale `README.md` toctree notice) |
| 9 | Focused built-book Exercise 8 Playwright tests, incl. dark mode | `npx playwright test --config playwright.book.config.ts e2e-book/chapter08.spec.ts e2e-book/chapter08-dark-mode.spec.ts` | 7/7 structural; dark-mode 1/1 after 1 correction (see §11) |
| 10 | Full Python suite once | `unittest discover -s tests -p 'test_*.py'` | **872 tests, 0 failures, 11 skipped** (network-only; up from 789 in WP32) |
| 11 | Full frontend unit suite once | `npm test` | **32 files / 402 tests, all passed** (up from 376 in WP32) |
| 12 | Manual visual inspection | Playwright screenshots of the built page, light/dark/390px-narrow | Both activities render correctly, legibly, with no overflow, in all three states (see saved screenshots referenced in this session) |

Additionally, extended beyond the minimum for WP33 §10's specific
instruction to fix a known WP32 gap:

- `scripts/smoke_portable_notebook.py` registry extended to cover chapters
  5, 6, 7, and 8 (previously only 1-4). Each new entry verified
  individually (`--notebook chapter_05` ... `chapter_08`) and then as a
  full run (`smoke_portable_notebook.py`, no `--notebook` flag): **all 8
  chapters executed cleanly with matching key values.**
- Full standalone Playwright suite: **227/227** (up from 208 in WP32).
- Full built-book Playwright suite: **107/107** (up from 96 in WP32).

No gate was rerun more than once; no long-running full suite was rerun
speculatively.

## 11. Failures, retries, deviations, and judgment calls

- **Test-file wording sensitivity (1 correction, `tests/test_exercise_08_notebook.py`).**
  Four substring assertions initially failed because Markdown line-wrapping
  split the target phrase across a line break (e.g. "not feature\nselection").
  Root cause identified immediately; fixed by using the existing
  `_norm_ws()` whitespace-normalizing helper (already used elsewhere in the
  same file) before the four affected assertions. Rerun once; all 46 tests
  passed. Not a notebook content defect -- a test-assertion brittleness
  issue, now fixed.
- **Dark-mode color assertion (1 correction, `interactive/e2e-book/chapter08-dark-mode.spec.ts`).**
  The initial assertion expected the CSS `rgba(...)` string
  `plotly-policy.ts`'s `markerPrimary` uses, but `getComputedStyle(el).fill`
  on an SVG path reports only the RGB channels (alpha is applied via a
  separate `fill-opacity`, not folded into `fill`). Root cause identified;
  corrected the expected values to plain `rgb(...)` with an explanatory
  comment. Rerun once; passed.
- **`export_pca_kmeans_widget.py --check` initially required network.** My
  first draft's `cmd_check()` recomputed `build_data()` (which downloads
  the ABIDE-II table) for a semantic-diff comparison, contradicting this
  repo's established convention that a network-sourced artifact's `--check`
  validates structure + canonical serialization only (never
  network-requiring recomputation) -- confirmed by inspecting
  `scripts/export_regression_catalog.py --check`, and by
  `scripts/gradient_boosting_model_audit.py --check`, which never recompute
  either. Corrected before committing (not caught by a failing gate --
  caught during implementation review against precedent).
- **No specific published neuroimaging citation in section 6.** WP33 §6
  conditionally allows citing "a verified primary research source." I chose
  not to name a specific paper, since I could not independently verify a
  specific study's exact methodology/findings from this environment and
  did not want to risk stating an unverified or misremembered citation in
  student-facing material. Section 6 instead describes the PCA-then-K-means
  research workflow generically and accurately, which fully satisfies the
  section's other requirements (explicit workflow order, arbitrary-label
  caution, no "autism subtypes" claim).
- **Fixed categorical cluster-color palette.** `interactive/src/pca-kmeans-explorer.ts`
  uses a hardcoded 6-color qualitative palette (`CLUSTER_COLORS`) rather
  than colors derived from the shared light/dark theme tokens, because
  `plotly-policy.ts` only exposes two accent colors (`markerPrimary`,
  `diagonalLine`), not a categorical palette. The chosen colors are
  mid-saturation and were confirmed legible against both the light and dark
  widget-card backgrounds by manual screenshot review (§10, gate 12).
- **Data artifact size (see §8).** The K-means catalogue is the single
  largest widget data file in the course (940.9 KiB uncompressed / 49.3 KiB
  gzip). Reducing it further would mean shrinking the required grids
  (`retainedPcGrid`, `kGrid`, `seeds`), which WP33 §6 explicitly says not to
  do ("do not silently remove an educational control"); it was kept at the
  full required grid and its size reported here rather than trimmed.

No gate failed and was left unresolved. No repair loop was entered.

## 12. Syllabus and Word course-overview confirmation

`book/syllabus.md` and the `course_overview/` Word document were not
opened, read, or modified at any point in this WP.
`git status --short --branch` (§14) confirms no changes under either path.

## 13. Merge / push / deploy / CI confirmation

Nothing was merged, pushed, or deployed. No GitHub Actions workflow was
run, triggered, or monitored. All work exists only in local commits on
`feature/wp33-exercise8-unsupervised-learning`.

## 14. Final `git status --short --branch` and decorated log

Immediately before committing this report + changelog:

```
## feature/wp33-exercise8-unsupervised-learning
?? WPs/reports/WP33_EXACT_CHANGELOG.md
?? WPs/reports/WP33_REPORT.md
```

Decorated log at the implementation commit (parent of this report commit):

```
0d9bf16 (HEAD -> feature/wp33-exercise8-unsupervised-learning) WP33: Exercise 8 — Unsupervised Learning
d76437d WP33: add specification (initial checkpoint)
73d802b (feature/wp32-exercise7-gradient-boosting) WP32: Exercise 7 — Boosting and Gradient Boosting
71267fd WP32: add specification (initial checkpoint)
a64e349 (main) WP31R3: document Chapter 1 dark-mode fix and successful redeploy
```

After this commit, `git status --short --branch` returns to a clean tree
(`## feature/wp33-exercise8-unsupervised-learning`, no other lines), and
`git log --oneline -1` reports the report commit as the new branch tip.
