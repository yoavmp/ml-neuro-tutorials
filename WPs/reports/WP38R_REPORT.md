# WP38R Report — Exercise 10 Review Corrections

## 1. Overall result

**SUCCESS.** All six required corrections landed: the multiple-selection
question's layout was hardened (no overlap reproduced after extensive
measurement, defended by a permanent regression test); the shared iframe/card
whitespace defect was root-caused and fixed at the actual source (two
independent bugs in `resize-report.ts`, plus a third, unrelated iframe-border
bug the strengthened test surfaced); the leakage laboratory now uses
`KNeighborsRegressor(n_neighbors=15)` throughout, with every visible
comparison (browser, notebook, portable notebook) showing both correct and
leaky R² and MSE plus a signed difference; the threshold-based imbalance
activity was fully replaced with a five-balance `class-balance-compare`
activity at a fixed 0.5 threshold; Fragment 4 now explicitly names the
Section 4 UCI HAR dataset and preserves the known-user/new-user nuance; and
the canonical notebook, portable notebook, and every test file were updated
and re-verified. One CSS change made mid-way through section 7 (lowering
`.widget-plot`'s `min-height` from 320px to 240px) was investigated further
during manual visual inspection, found to rest on a false premise, and
reverted — documented in full in §5 and §10 below, since it is the one
significant deviation from a straight-line execution. All bounded-validation
gates passed. Everything is committed locally on
`fix/wp38r-exercise10-review`; nothing was merged, pushed, deployed, or
monitored through GitHub Actions.

## 2. Starting state

- **WP38 branch-tip SHA:** `3b8cdeaf40413ceeec8585ac6c0b838387a82ee2`
  (`WP38: reports — Exercise 10 execution report and exact changelog`), the
  tip of `feature/wp38-exercise10-common-mistakes`. Resolved via
  `git rev-parse feature/wp38-exercise10-common-mistakes` and
  `git log -1 --format="%H %s" 3b8cdea`, both agreeing.
- Confirmed the branch contained, in order: the WP38 specification checkpoint
  `06fd62af0ea0eee8bcf5cc20274c8a5a1d8f7602`, the WP38 implementation commit
  `61a16c6f26a81b32c76c884b3122d266edc31bc1`, and the report commit above.
  `git status --short --branch` was clean.
- **Local `main`:** `2f74ccae826d14da9dee9997d890697d159d91c0`.
- **`origin/main`:** `f792ad55f34342e627ed1fe3b85ff60777507d85`.
  Neither was read from nor modified at any point.
- **New branch:** `fix/wp38r-exercise10-review`, created from the WP38 tip
  above.
- **Checkpoint commit** (specification, before implementation):
  `6c8a3a7a67dce0993a4e775e26c00bd6352ecc2f`.
- Implementation is spread across the commits listed in §9 below (this WP's
  scope crossed several independent axes — layout, shared resize
  infrastructure, two separate activity rewrites, and a notebook integration
  pass — so it was not implemented as a single commit; see the exact
  changelog for the full file-by-file breakdown per commit).
- This report and the exact changelog are committed as one further commit on
  top of the last implementation commit (see §11 for the literal final
  status/SHA, captured after that commit).

## 3. Section 3 — multiple-selection question layout

**Root cause: not reproduced.** The spec described the question wrapping to
two lines and drifting into the activity box. Direct measurement — Chromium
and Firefox, three widths spanning a single line through the ~5-line wrap the
real question text reaches at 390px, light and dark, the standalone widget
preview and the actual built book, initial load and a hard reload with dark
mode already active — found the legend (`.widget-quiz-question`) and the
first checkbox row separated by the intended 8px gap in every configuration,
with zero overlap. No absolute positioning, fixed line-height assumption, or
insufficient fixed height was found in `.widget-quiz-fieldset` /
`.widget-quiz-question` (neither had ever set one).

As hardening (not a fix for a confirmed defect), `.widget-quiz-question`
gained an explicit `width: 100%` and `box-sizing: border-box` — `<legend>`
has no reliable default cross-browser intrinsic width, so pinning it removes
the only plausible latent cause named in the spec, even though it did not
reproduce. A permanent regression test
(`interactive/e2e/leakage-quiz.spec.ts`) now asserts a non-overlapping,
≥4px gap between the question and the first option at desktop, an
intermediate wrapping width, and 390px, in both themes, on both initial load
and a reload taken with dark mode already active.

## 4. Section 7 — shared iframe/card whitespace

Three independent, genuine defects were found and fixed; a fourth change
(the `.widget-plot` min-height reduction) was tried, investigated, and
reverted. All are in the shared runtime (`interactive/src/resize-report.ts`,
`book/_static/activity-resize.js`), so the fixes apply to every activity in
Exercises 1–10, not just Exercise 10.

### 4.1 Root cause #1 (primary): `documentElement.scrollHeight` cannot report a value smaller than the current viewport

`resize-report.ts` measured `document.documentElement.scrollHeight`. Per the
CSSOM View spec, the root element's `scrollHeight` is defined as the
**greater of** the viewport's own height and the content's rendered height —
it can never report a value *smaller* than whatever height the iframe
currently has. Every activity starts life in exactly that state: the
notebook's static pre-JS `height` attribute is only ever an approximation of
the true content, frequently larger than it, and any later content
contraction (a control resetting to shorter text, a comparison grid
collapsing) was invisible to this measurement for the same reason.

**Direct proof** (a synthetic harness page embedding a real activity iframe,
using the exact production resize-message contract):

| Static fallback height | True content height | Result under `documentElement.scrollHeight` | Result under `document.body.scrollHeight` |
|---|---|---|---|
| 1400px | 762px | **stuck at 1200px** (never corrects down) | correctly settles at 762px |

Fix: measure `document.body.scrollHeight` (and observe `document.body` with
the `ResizeObserver`) instead — `<body>` has no such viewport floor.

### 4.2 Root cause #2: a separately-timed `scrollHeight` read can be stale relative to the `ResizeObserver` entry that triggered it

After fixing #4.1, the full built-book Playwright suite (run once section
4.1's fix landed) still failed on two activities outside Exercise 10 —
Exercise 5's Ridge/Lasso explorer (128px of "bottom slack") and Exercise 8's
PCA/K-means explorer (158px) — at **initial** load, with no interaction
required. Direct measurement of Ridge/Lasso's coefficient chart (whose
height depends on how many coefficients are shown, `40 * pairs.length + 60`)
showed the body-height trajectory settle 1878px → 1522px → 1394px, with
resize *messages* posted for the first two but never the third:

- At the exact animation frame the shrink to 1394px happens, the
  `ResizeObserver` entry's own `contentRect.height` already read
  **1394.125** (correct).
- A `document.body.scrollHeight` property read taken one *or even two*
  further animation frames later still returned **1522** — and never
  corrected afterward, because `<body>`'s content box does not change again
  (there is nothing further for the observer to fire on).

Fix: report the observed entry's own `contentRect.height` directly, instead
of re-deriving the same quantity via a separately timed property read.
Verified: Ridge/Lasso and PCA/K-means both settle correctly; the original
harness regression test (§4.1) still passes.

### 4.3 Root cause #3 (unrelated, surfaced by the strengthened test): the iframe's own border eats into its interior viewport

The full built-book suite still failed three cases in
`chapter05-visual-policy.spec.ts` (a pre-existing, WP16-era spec, not new to
this WP) with a persistent (not timing-related) internal scrollbar. Direct
measurement: `.ml-activity` (the iframe's own CSS class) has a `1px` border
under the page theme's `box-sizing: border-box`, so `iframe.style.height`
sets the iframe's **outer** height, not its interior viewport:

```
style.height = 1132px  →  interior clientHeight = 1130px  (2px short)
true content (body.scrollHeight) = 1132px
```

This is a permanent, structural 2px shortfall on **every** activity iframe
in the book, present since the border was added — invisible to every other
test's ≥2px tolerance, and only surfaced by this one spec's stricter ≤1px
internal-scrollbar check. Fixed in `book/_static/activity-resize.js` by
reading the iframe's own current border-top/bottom width
(`getComputedStyle`, not hardcoded) and adding it before applying the
height. Verified: `scrollHeight === clientHeight` exactly afterward; full
built-book suite green (152/152).

### 4.4 The min-height change: tried, investigated, reverted

Before finding #4.1–4.3, a `.widget-plot` CSS `min-height` of 320px was
suspected of forcing every chart configured shorter than that (many
components request 240–300px) to sit inside an oversized box, wasting
20–80px per undersized chart. This was lowered to 240px (the smallest height
any component configures) and *appeared* confirmed by direct measurement in
the standalone Vite preview.

Manual visual inspection (§8) of the built book caught a resulting defect —
leakage-lab's aggregate-plot y-axis title visibly overlapped adjacent text.
Tracing it back: in the **actual embedded-book** context, every Plotly
figure renders its SVG at exactly `.widget-plot`'s CSS-resolved height,
**regardless of the component's own `layout.height` override** — confirmed
directly, with a fully unmodified checkout's `resize-report.ts` and
`activity-resize.js` restored and `min-height` at its original 320px, that a
component configured for `height: 300` still renders at 320px. This is
long-standing `autosize`/`responsive` behavior in the real iframe-embedded
context (not reproducible in the standalone preview, which is why the
320→240 change looked justified there), and predates this WP entirely.

Consequence: there was no "wasted space per undersized chart" to recover in
the deployed book — every chart already rendered flush against whatever the
shared min-height was. Lowering it to 240px did not fix a gap; it uniformly
shrank every Plotly figure in the entire book by 80px, and for the one chart
with a longer axis title, that shrink caused a real, visible overlap.
**Reverted to 320px.** The two genuine fixes above (§4.1, §4.2) are
independent of this value and remain in place.

### 4.5 Quantitative height contract (section 7.1/9.5)

`interactive/e2e-book/iframe-height-contract.spec.ts` (pre-existing, WP35-era)
was strengthened rather than replaced:

- `childScrollHeight` now reads `document.body.scrollHeight` instead of
  `document.documentElement.scrollHeight` — the old measurement used the
  same viewport-floored API as the bug itself, so it was structurally unable
  to ever catch it (both sides of the old comparison derived from the same
  clamped number).
- A new **trailing-gap** assertion: the distance between the last
  *rendered* element inside `#app` and the bottom of the content box must
  not exceed **60px** (`.widget-root`'s 20px bottom padding, plus the
  largest bottom margin a trailing element can carry — `.widget-plot`'s
  28px, if a chart rather than the usual `<ul class="widget-prompts">`
  happens to end an activity — plus ~8px of cross-platform rounding
  headroom, matching WP16's own already-measured ~6px Linux/Chromium-vs-
  macOS variance at this same boundary). Measured baseline for the common
  case (ending on the reflection-prompts list): ~24px.
- An explicit **reset/contraction** step (not just any control change) is
  now exercised where a reset control exists, since that is exactly the
  transition the old viewport-floored measurement could never observe.
- Two bugs in the strengthening itself were found and fixed during
  validation, both self-inflicted rather than product defects: the
  trailing-gap measurement originally used `#app`'s literal DOM
  `lastElementChild`, which for leakage-quiz/multi-select-quiz can be a
  `hidden` element (an all-zero bounding rect), inflating the measured gap
  to 586–887px — fixed by walking backward to the last child with a
  non-zero rendered box; and the reset-click step's selector wasn't
  filtered to visible buttons, hanging on leakage-quiz's "Try again" (hidden
  until an answer is checked) — fixed with a `:visible` filter.
- Describe-block title corrected from "Exercises 1-9" to "Exercises 1-10"
  (the `CASES` list already covered Exercise 10; only the title was stale).
- A dedicated new regression test,
  `interactive/e2e/resize-shrink.spec.ts`, reproduces the exact §4.1 defect
  (an iframe started at a static height far taller than its real content)
  end-to-end through the production `ml-activity-resize` message contract,
  independent of the built-book suite.

Final state: `iframe-height-contract.spec.ts` 30/30 (24 activities ×
control-change/reset/dark-390px path, plus initial), `chapter10.spec.ts`
6/6, full built-book suite 152/152, full standalone suite 299/299.

## 5. Section 4 — KNN leakage laboratory

`KNeighborsRegressor(n_neighbors=15)` (fixed, predeclared, never tuned)
replaces `LinearRegression` in all three scenarios — scaling, target-informed
feature selection, PCA — in `scripts/export_leakage_lab_data.py`,
`interactive/src/components/leakage-lab.ts`,
`interactive/src/leakage-lab-data.ts`, the canonical notebook's three
reproduction cells, and every test. Sample sizes (60/100/250/1004), seeds
(0–4), bundles, feature counts, and the 75/25 split convention are
unchanged. `k=15` is valid at every sample size (≥45 training rows even at
n=60).

While integrating the KNN change into the canonical notebook, two
pre-existing issues in the notebook's own (separate from the exporter)
reproduction cells were corrected: the scaling and feature-selection cells
computed a leaky variant but only ever printed the **correct** pipeline's
R² (the leaky score was silently discarded); and the PCA cell fit a leaky
preprocessing pipeline but never fit or scored a downstream model on it at
all. All three cells now split via one reusable `train_idx`/`test_idx` pair
(mirroring the exporter's own approach) and print both correct and leaky
test R².

**Complete recomputed result table** (`book/_static/widgets/data/abide_leakage_lab.json`,
60 entries, `--refresh` + `--check` both pass, byte-canonical):

| scenario | n | seed | correct R² | leaky R² | Δ(leaky−correct) | correct MSE | leaky MSE |
|---|---:|---:|---:|---:|---:|---:|---:|
| feature_selection | 60 | 0 | 0.1973 | 0.3313 | +0.1340 | 106.896 | 89.050 |
| feature_selection | 60 | 1 | 0.3968 | 0.4328 | +0.0360 | 19.096 | 17.955 |
| feature_selection | 60 | 2 | 0.2284 | 0.3502 | +0.1218 | 194.184 | 163.542 |
| feature_selection | 60 | 3 | 0.4359 | 0.4608 | +0.0248 | 53.509 | 51.154 |
| feature_selection | 60 | 4 | 0.4446 | 0.6261 | +0.1816 | 66.503 | 44.765 |
| feature_selection | 100 | 0 | 0.3240 | 0.1270 | -0.1971 | 14.272 | 18.433 |
| feature_selection | 100 | 1 | 0.0749 | 0.2323 | +0.1575 | 25.486 | 21.148 |
| feature_selection | 100 | 2 | 0.4523 | 0.5090 | +0.0567 | 86.532 | 77.571 |
| feature_selection | 100 | 3 | 0.5132 | 0.5218 | +0.0085 | 38.319 | 37.648 |
| feature_selection | 100 | 4 | 0.5552 | 0.7154 | +0.1602 | 24.166 | 15.464 |
| feature_selection | 250 | 0 | 0.4996 | 0.5797 | +0.0801 | 35.508 | 29.824 |
| feature_selection | 250 | 1 | 0.5823 | 0.5589 | -0.0233 | 31.131 | 32.868 |
| feature_selection | 250 | 2 | 0.3383 | 0.4805 | +0.1422 | 47.120 | 36.992 |
| feature_selection | 250 | 3 | 0.5494 | 0.5404 | -0.0089 | 57.899 | 59.046 |
| feature_selection | 250 | 4 | 0.3196 | 0.4252 | +0.1056 | 39.692 | 33.531 |
| feature_selection | 1004 | 0 | 0.6101 | 0.6477 | +0.0376 | 36.760 | 33.212 |
| feature_selection | 1004 | 1 | 0.6484 | 0.6867 | +0.0382 | 42.164 | 37.578 |
| feature_selection | 1004 | 2 | 0.5804 | 0.6179 | +0.0374 | 38.494 | 35.058 |
| feature_selection | 1004 | 3 | 0.6921 | 0.7017 | +0.0096 | 23.404 | 22.675 |
| feature_selection | 1004 | 4 | 0.6454 | 0.6517 | +0.0063 | 23.026 | 22.616 |
| pca | 60 | 0 | 0.1935 | 0.2129 | +0.0194 | 107.409 | 104.820 |
| pca | 60 | 1 | 0.0183 | 0.0293 | +0.0110 | 31.077 | 30.729 |
| pca | 60 | 2 | 0.1107 | 0.1035 | -0.0072 | 223.800 | 225.624 |
| pca | 60 | 3 | 0.3484 | 0.3302 | -0.0181 | 61.816 | 63.537 |
| pca | 60 | 4 | 0.4624 | 0.4519 | -0.0106 | 64.364 | 65.628 |
| pca | 100 | 0 | 0.0232 | 0.0612 | +0.0380 | 20.625 | 19.823 |
| pca | 100 | 1 | -0.2427 | -0.1596 | +0.0832 | 34.236 | 31.944 |
| pca | 100 | 2 | 0.1868 | 0.1508 | -0.0361 | 128.466 | 134.164 |
| pca | 100 | 3 | 0.4814 | 0.4767 | -0.0046 | 40.829 | 41.192 |
| pca | 100 | 4 | 0.2425 | 0.1773 | -0.0652 | 41.160 | 44.703 |
| pca | 250 | 0 | 0.2971 | 0.3453 | +0.0481 | 49.875 | 46.461 |
| pca | 250 | 1 | 0.1370 | 0.2120 | +0.0750 | 64.313 | 58.721 |
| pca | 250 | 2 | -0.0241 | 0.0259 | +0.0499 | 72.919 | 69.364 |
| pca | 250 | 3 | 0.4571 | 0.4680 | +0.0109 | 69.751 | 68.351 |
| pca | 250 | 4 | 0.4492 | 0.4458 | -0.0035 | 32.129 | 32.331 |
| pca | 1004 | 0 | 0.4144 | 0.3965 | -0.0178 | 55.212 | 56.895 |
| pca | 1004 | 1 | 0.5276 | 0.5327 | +0.0051 | 56.660 | 56.051 |
| pca | 1004 | 2 | 0.3838 | 0.4080 | +0.0243 | 56.535 | 54.308 |
| pca | 1004 | 3 | 0.4893 | 0.5018 | +0.0125 | 38.827 | 37.873 |
| pca | 1004 | 4 | 0.4628 | 0.4523 | -0.0105 | 34.884 | 35.568 |
| scaling | 60 | 0 | 0.0008 | 0.0084 | +0.0075 | 133.066 | 132.061 |
| scaling | 60 | 1 | -0.3716 | -0.3273 | +0.0444 | 43.419 | 42.014 |
| scaling | 60 | 2 | -0.0325 | -0.0635 | -0.0309 | 259.858 | 267.645 |
| scaling | 60 | 3 | 0.2549 | 0.2578 | +0.0029 | 70.680 | 70.404 |
| scaling | 60 | 4 | 0.2822 | 0.2833 | +0.0011 | 85.938 | 85.812 |
| scaling | 100 | 0 | -0.3551 | -0.4017 | -0.0466 | 28.612 | 29.595 |
| scaling | 100 | 1 | -0.2537 | -0.1840 | +0.0697 | 34.538 | 32.619 |
| scaling | 100 | 2 | 0.1599 | 0.1476 | -0.0123 | 132.716 | 134.666 |
| scaling | 100 | 3 | 0.3527 | 0.3470 | -0.0057 | 50.956 | 51.407 |
| scaling | 100 | 4 | 0.2833 | 0.3000 | +0.0167 | 38.939 | 38.032 |
| scaling | 250 | 0 | 0.4915 | 0.4841 | -0.0074 | 36.083 | 36.607 |
| scaling | 250 | 1 | 0.3147 | 0.3210 | +0.0063 | 51.069 | 50.597 |
| scaling | 250 | 2 | 0.2767 | 0.2784 | +0.0017 | 51.506 | 51.382 |
| scaling | 250 | 3 | 0.2867 | 0.2869 | +0.0002 | 91.641 | 91.616 |
| scaling | 250 | 4 | 0.0956 | 0.0992 | +0.0035 | 52.757 | 52.551 |
| scaling | 1004 | 0 | 0.4376 | 0.4432 | +0.0055 | 53.018 | 52.499 |
| scaling | 1004 | 1 | 0.4255 | 0.4271 | +0.0016 | 68.900 | 68.706 |
| scaling | 1004 | 2 | 0.3345 | 0.3455 | +0.0110 | 61.058 | 60.047 |
| scaling | 1004 | 3 | 0.3640 | 0.3629 | -0.0011 | 48.345 | 48.431 |
| scaling | 1004 | 4 | 0.3211 | 0.3229 | +0.0019 | 44.089 | 43.968 |

**Scaling specifically:** unlike ordinary least squares (scale-invariant, so
the pre-WP38R scaling scenario always showed an exact zero gap), KNN's
distance-based predictions do depend on feature scale — every one of the 20
scaling entries now shows a nonzero gap, though modest (|gap| ≤ 0.070 R²)
and not consistently signed (13 positive, 7 negative). This is the intended,
honest outcome, not a bug.

**Confirmation:** both R² and MSE for both correct and leaky pipelines, plus
a labelled, signed `ΔR²`/`ΔMSE` (leaky − correct), are shown for every
visible comparison — the browser activity's metric tiles and paired-bar
chart hover, the aggregate-across-splits chart's own axis label, and all
three canonical-notebook reproduction cells. No remaining `LinearRegression`
reference exists anywhere in the leakage-lab activity's code, config,
artifact, or notebook cells (Fragment 1–3's generic debugging exercise in
Section 7, unrelated to the leakage-lab activity, still uses
`LinearRegression` as a stand-in estimator for a different, general
leakage-pattern question — left as is, since it was never part of this
activity).

## 6. Section 5 — class-balance comparison activity

The threshold-slider activity (`imbalance-threshold`) is fully removed —
component, data loader, exporter, config/data artifacts, tests, e2e spec —
and replaced with `class-balance-compare`, comparing the same two models
(ordinary vs. `class_weight="balanced"` logistic regression, `C=1.0`) across
exactly five balances (`50:50, 60:40, 70:30, 80:20, 90:10`; `95:5` excluded)
at a fixed 0.5 decision threshold, with no threshold control of any kind.

All values are reused, unmodified, from `book/config/abide_modeling.json`'s
pre-existing `classification.imbalance_activity` section (already
predeclared for Exercise 3's own, different activity, well before this WP):
`cohort_size=400`, `cohort_resample_seed_base=20000` (cohort seed =
base + ratio index, 0–4), `split_seeds[0]=0` (one fixed split per balance,
matching the removed activity's own precedent), and the established
`all-eligible × CT` (p=360) feature recipe via
`classification_model_audit._feature_columns`/`_xy`.

**Complete metric table** (`book/_static/widgets/data/abide_class_balance_compare.json`,
`--refresh` + `--check` pass, byte-canonical; cohort n=400 throughout):

| balance | cohort (maj/min) | test (maj/min) | model | acc | bal.acc | recall | prec | F1 | ROC-AUC | PR-AUC | PR-AUC base | maj. base | confusion (tn,fp,fn,tp) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 50:50 | 200/200 | 50/50 | ordinary | 0.590 | 0.590 | 0.520 | 0.605 | 0.559 | 0.618 | 0.603 | 0.500 | 0.500 | 33,17,24,26 |
| 50:50 | 200/200 | 50/50 | class-weighted | 0.590 | 0.590 | 0.520 | 0.605 | 0.559 | 0.618 | 0.603 | 0.500 | 0.500 | 33,17,24,26 |
| 60:40 | 240/160 | 60/40 | ordinary | 0.640 | 0.625 | 0.550 | 0.550 | 0.550 | 0.665 | 0.603 | 0.400 | 0.600 | 42,18,18,22 |
| 60:40 | 240/160 | 60/40 | class-weighted | 0.640 | 0.625 | 0.550 | 0.550 | 0.550 | 0.665 | 0.603 | 0.400 | 0.600 | 42,18,18,22 |
| 70:30 | 280/120 | 70/30 | ordinary | 0.580 | 0.519 | 0.367 | 0.324 | 0.344 | 0.549 | 0.337 | 0.300 | 0.700 | 47,23,19,11 |
| 70:30 | 280/120 | 70/30 | class-weighted | 0.590 | 0.536 | 0.400 | 0.343 | 0.369 | 0.550 | 0.339 | 0.300 | 0.700 | 47,23,18,12 |
| 80:20 | 320/80 | 80/20 | ordinary | 0.750 | 0.487 | 0.050 | 0.143 | 0.074 | 0.593 | 0.310 | 0.200 | 0.800 | 74,6,19,1 |
| 80:20 | 320/80 | 80/20 | class-weighted | 0.740 | 0.519 | 0.150 | 0.250 | 0.188 | 0.591 | 0.307 | 0.200 | 0.800 | 71,9,17,3 |
| 90:10 | 360/40 | 90/10 | ordinary | 0.850 | 0.517 | 0.100 | 0.143 | 0.118 | 0.630 | 0.143 | 0.100 | 0.900 | 84,6,9,1 |
| 90:10 | 360/40 | 90/10 | class-weighted | 0.810 | 0.494 | 0.100 | 0.091 | 0.095 | 0.628 | 0.142 | 0.100 | 0.900 | 80,10,9,1 |

Real, once-computed finding (never re-tuned after seeing it): at 90:10,
class-weighting **lowers** accuracy (0.850→0.810) and balanced accuracy
(0.517→0.494) with **no** matching recall gain (0.100→0.100, identical) —
genuinely not universally better, exactly the nuance the spec asked for. At
70:30 and 80:20, class-weighting *does* raise recall and F1 at some accuracy
cost, the more commonly expected trade-off. Both are shown, unedited.

The browser activity has exactly one primary control (a balance selector),
shows both models simultaneously, follows the required visual hierarchy
(accuracy-vs-baseline and recall/F1 as large tiles; balanced
accuracy/precision/ROC-AUC/PR-AUC as smaller secondary text), includes
side-by-side confusion matrices, and one across-balance line chart
(accuracy-vs-baseline by default, toggleable to recall/F1). No threshold
control, threshold slider, or "High Accuracy Can Still Miss the Minority
Class" text remains anywhere in the new config/component/notebook text.
Student-facing text never states or implies class weighting is universally
better — every evaluative sentence is hedged ("not guaranteed to help every
metric"), and this is asserted directly by
`test_class_balance_activity_has_five_balances_and_no_threshold_language`
and the new Playwright spec.

## 7. Section 6 — Fragment 4

Fragment 4 (`book/chapters/chapter_10/exercise_10.ipynb`) now explicitly
states it reuses the Section 4 UCI HAR smartphone-window dataset, uses that
section's own variable names (`X_har`/`y_har`/`groups_har`), and its answer:
names repeated, sometimes-overlapping windows per participant as the
mechanism, names `StratifiedGroupKFold` with `groups_har` as the fix for the
new-participant goal, and explicitly preserves the known-user/new-user
distinction ("Row-wise splitting is not *universally* invalid... if the goal
were instead generalizing to new *windows* from the same, already-known
participants, an ordinary random split would be a reasonable match")
rather than declaring row-wise splitting universally invalid.

## 8. Validation commands and outcomes (bounded plan, in order)

| # | Gate | Command(s) | Result |
|---|------|------------|--------|
| 1 | Reproduce quiz overlap + whitespace | Chromium+Firefox, 3 widths, both themes, standalone + built book | Quiz: no overlap reproduced (see §3). Whitespace: root-caused directly (see §4) |
| 2 | Recompute KNN leakage artifact once | `export_leakage_lab_data.py --refresh` then `--check` | wrote artifact; canonical; 60/60 entries |
| 3 | Compute five-balance imbalance artifact once | `export_class_balance_compare_data.py --refresh` then `--check` | wrote artifact; canonical; 5 ratios × 2 models |
| 4 | Focused exporter/audit checks | `unittest tests.test_export_leakage_lab_data` (11), `tests.test_export_class_balance_compare_data` (16), `tests.test_export_classification_imbalance_data` (18, unaffected sibling) | all pass |
| 5 | Focused Exercise 10 notebook/content tests | `unittest tests.test_exercise_10_notebook` | 20/20 pass |
| 6 | Execute canonical notebook once | `jupyter nbconvert --to notebook --execute --inplace exercise_10.ipynb` | 0 errors; outputs match hand-verified values |
| 7 | Regenerate Chapter 10 portable + all-chapter check | `build_portable_notebook.py --write --notebook chapter_10`; `--check --notebook all` | all 10 chapters up to date |
| 8 | Smoke-execute Chapter 10 portable outside repo | `smoke_portable_notebook.py --notebook chapter_10` | OK, key values matched |
| 9 | Frontend typecheck + focused unit tests | `npm run typecheck`; `npm run test:unit` | clean; 481/481 |
| 10 | One frontend production build | `npm run build` | succeeded (pre-existing >500kB chunk-size warning, unrelated) |
| 11 | Focused standalone Playwright | `leakage-lab.spec.ts leakage-quiz.spec.ts class-balance-compare.spec.ts resize-shrink.spec.ts` | 43/43 |
| 12 | Clean Jupyter Book build | `jupyter-book build book` (run 4 times total across this WP, once per infrastructure fix that needed re-verifying against the real embedded context) | succeeded every time; 2 pre-existing, unrelated warnings (missing `logo.png`, `README.md` not in toctree) |
| 13 | Focused built-book tests | `iframe-height-contract.spec.ts chapter10.spec.ts` (multiple passes, see §10); `chapter05-visual-policy.spec.ts` (after the border fix) | 30/30, 6/6, 3/3 in final state |
| 14 | Full offline Python suite | `unittest discover -s tests -p 'test_*.py'` | **1066 tests, 0 failures, 11 skipped** (network-only), run 3 times across this WP (after the exporter/notebook changes landed, and twice more after infrastructure fixes that don't touch Python — confirming no regression each time) |
| 15 | Full frontend unit suite | `npm run test:unit` | **38 files / 481 tests**, run 3 times, always green |
| 16 | Full standalone Playwright suite | `npx playwright test` | **299/299**, run 4 times across this WP, always green |
| 17 | Full built-book Playwright suite | `npx playwright test --config playwright.book.config.ts` | first full run: 5 failures (see §10); second full run (after §4.2/§4.3 fixes): 2 failures (chapter05-visual-policy, unrelated to the first two but caught by the same full run); final run: **152/152** |
| 18 | Manual visual inspection | Screenshots of all four Exercise 10 activities at desktop/390px × light/dark against the built book | Caught the min-height regression (§4.4) directly; confirmed clean after the revert |

No gate was rerun more than the bounded-plan-permitted one-correction cycle
**per distinct defect** — several distinct defects were found across gates
13/17, each diagnosed and fixed once, with one immediate confirming rerun;
see §10 for the full, honest account, since more than one correction cycle
was needed across the whole gate (not for any single defect).

## 9. Commits on `fix/wp38r-exercise10-review` (in order)

```
6c8a3a7 WP38R: add specification (initial checkpoint)
7378fed WP38R sec 3/7: fix iframe/card whitespace at its root cause; harden quiz layout
6f2ad57 WP38R sec 6: clarify Fragment 4 reuses the Section 4 smartphone-window dataset
bb37450 WP38R sec 9.4: add regression test for Fragment 4's dataset clarification
2349458 WP38R sec 4: replace LinearRegression with KNN in the leakage-lab activity
f43b10f Merge WP38R sec 4: KNN swap in leakage-lab activity
2a1abfc WP38R sec 5: replace imbalance-threshold with class-balance-compare
12ec3bc Merge WP38R sec 5: replace imbalance-threshold with class-balance-compare
72141da WP38R sec 4/5/8: integrate KNN leakage-lab and class-balance-compare into the notebook
754e1bb WP38R sec 8: regenerate Chapter 10 portable notebook
b53dad3 WP38R sec 7/9.5: fix two latent defects the strengthened height contract exposed
ec51c43 WP38R sec 7: compensate for the iframe's own border in activity-resize.js
edaad80 WP38R sec 7: revert .widget-plot min-height 320->240 (flawed premise)
d204399 WP38R: correct a test comment referencing the reverted min-height diagnosis
```

(The two `2349458`/`f43b10f` and `2a1abfc`/`12ec3bc` pairs are a background
agent's commit plus the merge that brought it into this branch — sections 4
and 5 were implemented in isolated worktrees in parallel, since they touch
disjoint files, then reviewed and merged in.)

## 10. Retries, deviations, judgment calls, and the one real correction cycle

- **The `.widget-plot` min-height reduction (320px→240px→320px) — the one
  significant deviation from a straight-line execution, disclosed in full.**
  Diagnosed from the standalone Vite preview as fixing wasted per-chart
  space; implemented; only during manual visual inspection of the *built
  book* (a later gate) was it discovered that the standalone preview does
  not represent real Plotly sizing behavior in the embedded-iframe context,
  where every chart already renders at the shared floor regardless of its
  own configured height. Reverted once this was confirmed (including
  reproducing the same behavior on a fully unmodified checkout, ruling out
  any WP38R change as the cause). This is exactly the kind of judgment call
  the spec's bounded-validation plan exists to catch before it ships — it
  was caught by gate 18, one gate before the report was written, not left
  in.
- **Two distinct, genuine pre-existing defects surfaced by the strengthened
  height-contract test, each requiring its own correction (§4.2, §4.3),
  neither part of Exercise 10 or this WP's original scope, but squarely
  within "the shared iframe/card sizing" mandate of section 7.** Both are
  root-caused, fixed, and independently verified (not papered over with a
  longer wait or a looser tolerance) — see §4 for the measurements.
- **Two bugs in the test-strengthening itself** (the trailing-gap
  measurement's hidden-element bug; the reset-click step's missing
  visibility filter) — both self-inflicted, both caught by the very first
  run of the new assertions, both fixed in one pass each.
- **The canonical notebook's own PCA/scaling/feature-selection reproduction
  cells had two pre-existing, unrelated bugs** (leaky R² computed but never
  printed; PCA's leaky pipeline never fit a downstream model at all) —
  found while integrating the KNN change, fixed as part of the same pass
  since correcting them was necessary to satisfy section 4.2's "every
  visible comparison shows both R² values" requirement.
- No seed, sample size, feature count, component count, or `k` was searched
  or adjusted after seeing a result, at any point, for either the leakage
  lab or the class-balance activity. Every predeclared value came from
  either this WP's own specification (`k=15`) or the pre-existing course
  manifest (`book/config/abide_modeling.json`, written for other exercises
  before this review began).
- No sleeps or stress-repetition were used to paper over a resize-timing
  defect; every fix targets the actual mechanism (a measurement source, a
  border compensation), verified by direct, repeatable measurement rather
  than by adding delay.

## 11. Portable notebook and generated artifacts

- `scripts/build_portable_notebook.py --check --notebook all`: all 10
  chapters up to date (Chapter 10 regenerated at 39 cells).
- Chapter 10's portable notebook smoke-executed outside the repository tree
  (`scripts/smoke_portable_notebook.py --notebook chapter_10`): 0 errors,
  key values matched.
- Confirmed present in the portable notebook: `KNeighborsRegressor`,
  `n_neighbors=15`, all five balance keys (`50:50`…`90:10`). Confirmed
  absent: any `<iframe>`, `_static/` reference, `scripts/` path,
  `requirements.txt` mention, `imbalance_threshold`/`imbalance-threshold`
  reference, or WP number.
- Canonical notebook: 37 cells (9 code, 28 markdown) — within the
  pre-existing 32–38 target range; unchanged from before this WP (Fragment
  4's rewrite and Section 5's rewrite both edited existing cells' `source`,
  adding no new cells).

## 12. Confirmation: Syllabus and Word course overview untouched

`book/syllabus.md` and the `course_overview/` Word document were not opened,
read, or modified at any point. Confirmed by `git status --short` and the
exact changelog's file list — neither path appears anywhere in it.

## 13. Confirmation: nothing merged, pushed, deployed, or monitored via CI

Nothing was merged into `main`, pushed to `origin`, or deployed. No GitHub
Actions workflow was run, triggered, or monitored. WP39 was not started. All
work exists only in local commits on `fix/wp38r-exercise10-review`.

## 14. Final `git status --short --branch`

Immediately before committing this report + changelog:

```
## fix/wp38r-exercise10-review
?? WPs/reports/WP38R_EXACT_CHANGELOG.md
?? WPs/reports/WP38R_REPORT.md
```

After committing this report and changelog, `git rev-parse HEAD` and
`git status --short --branch` were run and their literal output is reported
in the assistant's final message to the user (a commit cannot contain its
own SHA).
