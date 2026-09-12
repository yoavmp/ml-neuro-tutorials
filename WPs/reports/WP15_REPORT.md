# WP15 implementation report — sample-size repair, compact interactive assets, production deployment

## Outcome

Status: **SUCCESS**

Exercise 2's Section 5 sample-size demonstration no longer shows the
360-feature recipe's real double-descent instability by accident; it now
isolates the intended lesson ("more training data → more stable, more
accurate held-out prediction") using a small, fixed, 10-column cortical-
thickness bundle (`sensorimotor_core`: primary motor + primary
somatosensory cortex, bilateral) selected by a predeclared, training-only
audit over four candidate bundles, all of which passed the audit's decision
rule — `sensorimotor_core` was the first passing candidate in declaration
order, not the best-scoring one, and the locked outer test set was never
consulted while choosing it. The full 360-feature recipe, and the genuine
double-descent curve it produces, are unchanged in Sections 1–4's main
worked example.

Both Exercise 3 KNN interactive artifacts moved from large inline-JSON
numeric-array payloads to a small JSON manifest plus one compact,
deterministic binary file each (`scripts/binary_asset.py` /
`interactive/src/binary-asset.ts`): nearest-neighbour orderings are now
16-bit row indices into small 32-bit-float reference-target arrays instead
of the full reordered target values repeated in every row. Combined runtime
interactive-data size: 4,569,372 → 1,293,530 bytes (**−71.7%**, well past
the 50% target), every individual file under the 1 MB budget, with zero
change to the activities' mathematics, visible results, or accessibility —
proven by the full standalone and built-book Playwright suites passing
unchanged, plus a live production Playwright run.

All completed work was merged into `main` with an ordinary `--no-ff` merge
(zero conflicts — `main` had no commits `feature/regression-practice`
lacked), pushed, and deployed via the existing GitHub Actions → GitHub Pages
workflow. The triggered workflow run succeeded, `gh-pages` was updated to a
commit literally named after the deployed `main` SHA, and Exercises 1–3 were
verified on the live production site — both by direct HTTP checks and by
running the full built-book Playwright suite (36 tests: config/data 200s,
real k-driven recomputation, panel/tab/legend checks, Colab/download
targets, sidebar toggle) against `https://yoavmp.github.io` itself, not just
against a local build.

| Check | Before WP15 (WP14 final) | After WP15 |
|---|---|---|
| Python unit tests | 271 / 271 | **308 / 308** |
| Frontend unit (`vitest`) | 262 / 262 | **276 / 276** |
| `npm audit --omit=dev` | 0 vulnerabilities | 0 vulnerabilities |
| `abide_modeling_data.py --check` | self-consistent (p=360) | self-consistent (p=360, +`sensorimotor_core` bundle, +`sample_size_demo`) |
| `regression_model_audit.py --check` | self-consistent | self-consistent (unchanged) |
| `export_regression_catalog.py --check` | valid + canonical | valid + canonical (unchanged) |
| `knn_model_audit.py --check` | self-consistent (k=15) | self-consistent (k=15, unchanged) |
| `sample_size_audit.py --check` (new) | — | **self-consistent, 4/4 candidates pass, `sensorimotor_core` selected** |
| `export_knn_explore_data.py --check` | valid + canonical (schema v2, 1 JSON file) | valid + canonical (**schema v3, manifest + binary**) |
| `export_knn_abc_data.py --check` | valid + canonical (schema v1, 1 JSON file) | valid + canonical (**schema v2, manifest + binary**) |
| Combined KNN interactive-data size | 4,569,372 bytes | **1,293,530 bytes (−71.7%)** |
| Portable notebooks `--check` | up to date (ch1: 75, ch2: 31, ch3: 37) | up to date (ch1: 75, **ch2: 31 byte-changed content, same count**, ch3: 37) |
| Portable smoke (out of repo, network) | ch1: 20, ch2: 12, ch3: 16 code cells | ch1: **20**, ch2: **12**, ch3: **16**, key values matched |
| Standalone Playwright | 100 / 100 | **100 / 100** |
| Built-book Playwright | 36 / 36 | **36 / 36** |
| Clean Jupyter Book build | succeeded, 2 warnings | succeeded, **2 warnings** (same two pre-existing) |
| `*.err.log` guard | empty | empty |
| 2× consecutive clean builds, deterministic figures | identical (12 PNGs) | **identical (12 PNGs)** |
| Live-site Playwright (production, this WP only) | not run | **36 / 36 against `https://yoavmp.github.io`** |

## 1. Branch, checkpoint, baseline (WP15 §0–1)

- Confirmed `feature/regression-practice` HEAD was `2cbf350` (`WP14 report:
  document 360-parcel correction and Exercises 2-3 revisions`) with one
  untracked file (`WPs/WP15_SAMPLE_SIZE_COMPACT_ASSETS_AND_PRODUCTION_
  DEPLOYMENT.md`) and an otherwise clean tree.
- **Checkpoint commit `3b7cf5c`** (`checkpoint: before WP15`) — adds the WP
  brief only (1 file, +403).
- **Annotated tag `wp15-start`** → `3b7cf5c`. The name was free; no conflict,
  no numeric suffix needed.
- Work continued on **`feature/regression-practice`** — the existing
  Exercise feature branch, matching WP09–WP14's own established preference,
  per WP15 §0.7 ("continue on the current feature branch unless repository
  inspection establishes a safer existing workflow" — it did not).
- Baseline: the checkpoint commit's tree is byte-for-byte WP14's own final,
  reviewed tree (confirmed directly: both committed KNN JSON asset sizes —
  2,719,089 and 1,850,283 bytes — matched WP14's report exactly before any
  WP15 edit). WP14's own final report already recorded the full baseline
  gate (Python 271/271, frontend 262/262, standalone e2e 100/100 — WP14
  reports 100, not 74, reflecting WP13→WP14 growth — built-book e2e 36/36,
  2 build warnings, 12 PNGs); this WP relied on those numbers rather than
  re-running the identical full gate a second time against an unmodified
  tree, since the checkpoint commit changes nothing but adding this WP's own
  brief file. Deviation noted for transparency, per WP15 §1's instruction to
  record baseline checks: the manifest/data self-consistency checks
  (`abide_modeling_data.py --check`, direct byte-size comparison) were run
  directly against the checkpoint tree; the full test/e2e suites were not
  independently re-run before the first edit, only after.
- Implementation commit `2584522`; merge commit `6288136`. Full identifiers,
  hashes, and command list: `WPs/reports/WP15_EXACT_CHANGELOG.md`.

## 2. Exercise 2 Section 5 audit and rewrite (WP15 §2)

### 2.1 The predeclared audit

`scripts/sample_size_audit.py` predeclares four small (≤12-column, bilateral,
documented) cortical-thickness candidates *before* scoring any of them:
`sensorimotor_core` (BA4 + 3a/3b/1/2, p=10), `early_visual` (V1–V4, p=8),
`auditory_core_belt` (A1 + belt regions, p=8), and `atlas_order_every_30th`
(a deterministic every-30th-ROI rule, p=12, the lowest-preference source).
No existing manifest bundle (`frontoparietal`, `frontal`, `parietal`,
`temporal`, `occipital`, `sensorimotor`) has ≤12 columns, so none qualified
as a source-1 candidate.

Every candidate is scored using **only** the outer-training partition: an
inner dev split (identical parameters to the already-reviewed
`knn.dev_split`) carves a fixed 564-row fit pool and a fixed 189-row
validation pool out of the 753-row outer-training set; the 251-row locked
outer test set is never loaded as a scoring target anywhere in the audit
module (`tests/test_sample_size_audit.py::
test_outer_test_set_was_never_loaded_as_a_scoring_target` asserts this
structurally — the inner validation size, 189, is checked to be the KNN
dev-split size, never the 251-row outer test size).

The decision rule — smallest plotted size ≥3× p, a clear (≥0.05) R² gain
from smallest to largest predeclared size, no single-step drop >0.02,
instability narrowing to ≤35% of its starting spread, cross-seed median
disagreement ≤0.15, and a final median R² ≥0.15 — was written and its
thresholds fixed in code **before** any candidate's numbers were computed;
`evaluate_decision_rule` is a pure function of a candidate's own stored rows,
re-verified offline by `--check` recomputing it from the committed JSON and
asserting the recomputation matches what was stored (catching any accidental
edit to the committed result).

**All four candidates passed.** `sensorimotor_core` was selected because it
is the first passing candidate in source-preference-then-declaration order —
a small, well-established, single documented anatomical system (P less loaded
with cognition-literature framing than P-FIT-style DLPFC bundles, which was a
deliberate simplicity/defensibility choice among several equally-passing
options) — never because it scored highest (it did not; `auditory_core_belt`
and `atlas_order_every_30th` both had higher training-only R² at every size).
The full per-candidate audit table, including the three candidates not used,
is reproduced in `WPs/reports/WP15_EXACT_CHANGELOG.md` §2.1 and committed in
full in `scripts/sample_size_audit_result.json`.

### 2.2 Why this is not held-out-test-driven cherry-picking

- The candidate list, sizes, repeat count, seeds, and decision-rule
  thresholds were all fixed in code before any candidate's own numbers (even
  training-only ones) were computed.
- Every candidate was scored against the SAME fixed inner-validation
  partition, never the locked outer test set.
- The selection procedure sorts passing candidates by `(source_preference,
  declaration_order)` — an ordering fixed before scoring — never by which
  one's own numbers looked best; this is asserted, not merely claimed
  (`test_selected_candidate_is_sensorimotor_core` pins the actual outcome so
  any future change to the selection LOGIC that silently changed the winner
  would be caught).
- The final, real held-out figure (§2.3 below) is computed exactly once,
  after the candidate was already locked, using Exercise 2's own existing
  locked outer split — the same discipline the repository's `knn.selected_k`
  and `catalog` decisions already use elsewhere.

### 2.3 Final Section 5 implementation and numbers

Section 5 now defines its own small feature list (`SAMPLE_SIZE_ROIS =
["4","3a","3b","1","2"]`, expanded to 10 `fsCT_` columns), re-splits with the
IDENTICAL `random_state=42` stratified split Section 2 already uses (proven,
not assumed, by an in-notebook `assert np.array_equal(y_train_ss, y_train)`),
and sweeps `sizes = [40, 60, 90, 130, 200, 300, len(y_train_ss)]` (753) with
40 repeated subsamples per size, reporting median ± 10th/90th-percentile
R²/MSE — same statistical treatment as WP14's design (repeated deterministic
subsampling, robust centre + spread), applied to the new feature set and
sizes.

Executed output (also the real held-out result, consulted only after the
candidate was locked):

| n_train | n/p | median held-out R² | 10–90 pct | median MSE |
|---:|---:|---:|---|---:|
| 40 | 4.00 | +0.188 | [−0.040, +0.300] | 75.8 |
| 60 | 6.00 | +0.265 | [+0.156, +0.348] | 68.6 |
| 90 | 9.00 | +0.356 | [+0.244, +0.395] | 60.1 |
| 130 | 13.00 | +0.370 | [+0.317, +0.405] | 58.8 |
| 200 | 20.00 | +0.373 | [+0.349, +0.402] | 58.5 |
| 300 | 30.00 | +0.395 | [+0.363, +0.413] | 56.5 |
| 753 (full) | 75.30 | +0.407 | [+0.407, +0.407] | 55.4 |

A clean, monotone-in-the-median upward trend with steadily narrowing spread,
and no interpolation-threshold collapse at any size (every plotted `n_train`
is ≥4× `p=10`) — the intended lesson, undistorted by the 360-feature
recipe's own separate near-`n=p` behaviour. No values were clipped, hidden,
or cherry-picked from a wider run.

The explanatory text (`wp11-050`, `wp11-05a`) states plainly that this is a
*modest*, deliberately small feature set used *only* for this isolated
demonstration (Sections 1–4 keep the full 360-feature recipe throughout, per
WP15's own non-negotiable constraint), names the general selection process
(a short predeclared list, scored training-only, against a rule fixed in
advance) without naming the script or WP file (matching the existing
"no student-facing internal reference" rule, re-verified by
`test_no_wp_script_or_report_references_in_student_text`), and explicitly
warns that the rising median does not guarantee every individual repeat
improves — matching the WP's suggested framing, adapted to the actual locked
design.

Double-descent language, the old `UNDERDETERMINED` flag, and the old
`sizes = [50, 100, 200, 300, 400, 550, len(y_train)]` are all gone from
Section 5 (`test_no_stale_double_descent_or_underdetermined_claims`); they
remain true and unchanged for Sections 1–4's own 360-feature recipe, which
this WP did not touch.

## 3. Compact interactive-data architecture (WP15 §3)

### 3.1 Design actually implemented

Exactly the WP's preferred representation: a small versioned JSON manifest
per activity (`schemaVersion`, `activity`, `source`, `target`,
`featureRecipe`, `split`, small scalars, `binary.{path,byteLength,sha256}`,
`sections` — per-section `dtype`/`shape`/`byteOffset`/`byteLength`) plus one
deterministic binary file, read with `fetch(...).arrayBuffer()` and typed
arrays. Nearest-neighbour row indices are `uint16` (every validated maximum
index here is 563 or 752, both far under 65,536 — `BinaryAssetBuilder.add`
asserts this and raises a clear error if it were ever violated); reference-
pool target arrays are little-endian `float32`, proven — not assumed —
sufficient by an export-time round-trip check comparing the float32-sourced
curve against the float64 computation at the existing 4-decimal display
precision (WP15 §3.2's escape hatch: "unless comparison proves 64-bit
precision is required"; it was not).

The Exercise 3 explorer's duplicate baseline matrix (schema v2's
`trainingSamples.A` byte-identical to the top-level `neighborTargetsByProximity`)
is eliminated structurally, not merely de-duplicated after computing both:
schema v3 has exactly one `neighborIndexA` section, and the browser loader
uses it for both the top-level view and the "Training sample A" tab.

No server, database, CDN, Git LFS, service worker, notebook kernel, or
runtime Python is required — the built site is still fully static (verified
by the built-book Playwright suite passing against `book/_build/html`
served by a plain static file server, and again against the real production
GitHub Pages site). No `.gz` precompression is used or required.

### 3.2 Reusable loader

One shared, tested TypeScript module, `interactive/src/binary-asset.ts`
(`loadBinaryAsset`), used identically by both `knn-explore-data.ts` and
`knn-abc-data.ts` — not activity-specific byte parsing duplicated twice. It:
validates `schemaVersion` and every manifest field via zod before doing
anything else; validates the binary path is safe (same-origin, http/https,
resolved against the manifest's own URL) by reusing the EXISTING, already
security-reviewed `resolveDataUrl` helper rather than reimplementing path
safety; validates byte length and, where `crypto.subtle` is available (every
target browser here, since GitHub Pages is HTTPS and local dev serves from a
secure-context `localhost`), a SHA-256 digest; validates every section's
bounds, 4-byte alignment, dtype, and byte-length/shape consistency; decodes
little-endian regardless of host byte order; caches in-flight/resolved
fetches by URL so one page never fetches the same binary twice; and returns
a clear, student-friendly `DataResult` error rather than throwing or
producing a blank plot. `interactive/tests/binary-asset.test.ts` (15 tests)
exercises every one of those failure modes directly, independent of any real
KNN data.

Digest verification is also enforced at export time (§3.1) rather than only
at runtime — belt and braces, and explicitly the reasoning WP15 §3.3 invites
("if production digest verification has a material compatibility/
performance cost, enforce it during export/build") applied here to the
float32-precision question specifically, while the (cheap, ~650 KB,
SubtleCrypto-native) runtime digest check is kept as well since it has no
material cost on any actual target platform.

### 3.3 Exporters and canonical checks

`scripts/export_knn_explore_data.py` (schema v2→v3) and
`scripts/export_knn_abc_data.py` (schema v1→v2) both gained: the same
`--refresh`/`--check` modes as before; a shared binary-packing dependency
(`scripts/binary_asset.py`, new, 9 of its own unit tests); and a
`_reconstruct_logical` helper that decodes the binary back into the OLD
schema's logical nested arrays so every pre-existing semantic check — shapes,
valid k ranges, exact k=1 self-neighbour endpoints for B/C, the k=N_fit
mean-prediction endpoint, `trainingSamples.A` equality (now structural, see
§3.1), agreement with representative scikit-learn KNN predictions, no
identifier-shaped key, no raw imaging matrix — still runs, now against
binary-sourced data. No generated manifest or binary file was ever hand-
edited; both scripts' `--check` mode re-validates the committed files
byte-for-byte canonical (`serialize_manifest(committed) == on-disk text`, and
the binary's own SHA-256 re-derived and compared).

### 3.4 Size budget

| Asset | Before | After | Reduction |
|---|---:|---:|---:|
| `abide_knn_explore.*` | 2,719,089 B (1 JSON) | 658,336 B (2,212 manifest + 656,124 binary) | −75.8% |
| `abide_knn_abc.*` | 1,850,283 B (1 JSON) | 635,194 B (1,162 manifest + 634,032 binary) | −65.7% |
| **Combined** | **4,569,372 B** | **1,293,530 B** | **−71.7%** |

Target was ≥50%; achieved 71.7%. Every individual committed runtime-data
object is under the 1,000,000-byte budget (largest single file:
`abide_knn_explore.bin`, 656,124 bytes). Page-local loading is unchanged and
verified: Exercise 2's own activity (`regression_compare.json` /
`abide_regression_models.json`) is untouched and unrelated to either KNN
binary; the built-book Playwright suite's chapter02/chapter03 specs each
assert their own iframe's network requests, and `chapter03.spec.ts` now
explicitly asserts NO request for the obsolete
`abide_knn_explore.json`/`abide_knn_abc.json` paths occurs at all. Both old
JSON files were deleted only after every reference (config JSON, export
script, TypeScript loader, manifest field, tests) had migrated, confirmed
absent from `book/_build/html/_static/widgets/data/` after a clean rebuild,
and confirmed to 404 on the live production site (§8 below). No Git history
rewrite was performed to remove their old committed versions.

### 3.5 Portable notebooks

Unaffected: neither `exercise_02_portable.ipynb` nor `exercise_03_portable.ipynb`
references the browser binary loader, `fetch`, or JavaScript in any way — the
portable notebooks' non-interactive Python fallback code and outputs were
already, and remain, the source of truth for offline/Colab use. Chapter 2's
portable notebook only changed because Section 5's own Python content
changed (§2 above); chapter 3's portable notebook is untouched (`--check`
reports it up to date, unchanged cell count).

## 4. Notebook and site consistency (WP15 §4)

- Both affected canonical notebooks (`exercise_02.ipynb`) were regenerated
  by re-executing via `nbconvert`, never by hand-editing output JSON.
  `exercise_03.ipynb` needed no content change (only its underlying data
  format changed, invisibly to the notebook's own markdown/code).
- Exercise 2's portable notebook regenerated via `build_portable_notebook.py
  --write`; Exercise 3's portable notebook confirmed unchanged
  (`--check` reports "up to date").
- Exercise 1 is untouched (not present in this WP's diff at all).
- The shared blue "Think first" CSS class and design is untouched (no CSS
  file in this WP's diff).
- The green "Run or download this notebook" block and Colab/`.ipynb`
  download links on all three exercises: re-verified by the built-book
  Playwright `launch-buttons.spec.ts` suite, including against the live
  production site (§8).
- No student-facing text references WPs, reports, internal scripts, or audit
  files (re-scanned directly against notebook source cells only, excluding
  base64 image output blobs which trivially contain arbitrary substrings by
  chance — confirmed zero real hits).
- Clean-browser-session / repository-subpath behaviour: every standalone
  Playwright spec runs its "site root" case AND a "project subpath" case;
  both passed (100/100).
- No console errors, failed requests, or blank plots: asserted by the
  Playwright suites' own `requestfailed`/`console`/render-count checks, and
  independently re-verified against the live production site with an ad hoc
  console/network listener (one pre-existing, unrelated console warning
  found — see §8).

## 5. Full local validation gate (WP15 §5)

All 14 required checks were run and passed; exact commands and results are
in `WPs/reports/WP15_EXACT_CHANGELOG.md` §4. Summary: Python unit tests
308/308; frontend typecheck clean; frontend unit tests 276/276; `npm audit
--omit=dev` 0 vulnerabilities; production interactive build succeeded (same
pre-existing 500 kB Plotly-chunk advisory as every prior WP, no new
warning); portable-notebook freshness clean for all 3 chapters; portable
smoke execution (network, outside the repository) OK for all 3 chapters;
clean `jupyter-book build` succeeded with the same 2 pre-existing warnings
(`logo.png` missing, `book/README.md` not in a toctree) and no new one;
standalone Playwright 100/100; built-book Playwright 36/36; two consecutive
clean builds produced an identical 12-PNG SHA-256 set; a targeted scan found
no stale `358`, no obsolete JSON filenames, no Exercise 2 FIQ/regularisation
text, and no student-facing internal reference; the final built tree
contains no multi-megabyte (or any) `abide_knn_*.json` file. No frontend
lint script is configured in this repository (`npm run lint` does not
exist), so that sub-item of §5.4 is not applicable.

## 6. Production integration (WP15 §6)

- `origin` confirmed pointing at `yoavmp/ml-neuro-tutorials`.
- `git fetch origin --prune` run before any mutation.
- Local `main` and `origin/main` were identical (`6d8c1f6`) before the
  merge; the feature branch was 20 commits ahead of `origin/main` and
  `origin/main` had 0 commits the feature branch lacked — zero divergence,
  zero risk of conflict, confirmed before merging (not assumed).
- Existing GitHub Actions workflow (`.github/workflows/deploy.yml`) inspected
  and followed exactly as-is: it already runs the full test/build/e2e gate
  and publishes `book/_build/html` to the `gh-pages` branch via
  `peaceiris/actions-gh-pages@v4` on every push to `main`. No second Pages
  workflow was created; `book/_build` was never committed to `main`.
- Sequence followed: implementation commit on the feature branch (§1) → §5
  gate passed on that commit → switch to `main` → `git pull --ff-only
  origin main` (already up to date) → `git merge --no-ff
  feature/regression-practice` (merge commit `6288136`, zero conflicts) →
  a short post-merge smoke gate ON `main` itself (Python unit tests 308/308;
  all 7 artifact `--check` commands; frontend typecheck + production build;
  a clean `jupyter-book build`; a representative 10-test built-book
  Playwright run covering chapters 2 and 3) → `git push origin main`
  (`6d8c1f6..6288136`, ordinary push, never forced).

## 7. Build and publish (WP15 §7)

Pushed `main` normally; the existing GitHub Actions workflow
(`Build and deploy Jupyter Book`) triggered automatically. `gh` was already
authenticated (`yoavmp`, `repo`+`workflow` scopes) and was used to watch the
exact triggered run to its terminal state:

- **Run `34692844653`**, triggered by the push, `headSha=6288136`, every
  step green (frontend typecheck/unit/build/audit, both artifact checks, the
  full standalone Playwright suite, the Jupyter Book build, the
  notebook-execution-error guard, the built-book Chapter-1 Playwright check,
  the out-of-repository portable-notebook smoke execution, and the
  `peaceiris/actions-gh-pages@v4` publish step), **conclusion: `success`**,
  total runtime 3m4s.
- `gh-pages` branch updated to commit `f8be61e`, whose own commit message —
  written by the deploy action itself — is literally `deploy:
  6288136acf24f9c3009aa7de9555814313f6aa25`, i.e. the exact merge-commit SHA
  just pushed to `main`. This is independent confirmation (not merely an
  assumption) that the live site reflects this WP's final `main` commit.
- No deployment failure occurred, so no in-scope fix / rerun / second
  monitoring cycle was needed.

## 8. Live-site acceptance (WP15 §8)

Base URL: `https://yoavmp.github.io/ml-neuro-tutorials/`.

**Direct HTTP checks** (13 URLs): Introduction, Syllabus, Contents,
Exercise 1/2/3 pages, both new manifest files, both new binary files — all
200; both OLD `abide_knn_explore.json`/`abide_knn_abc.json` paths — both
404, confirming the obsolete large assets are genuinely gone from
production, not merely from the local build.

**Interactivity, not just HTTP 200**: the entire built-book Playwright suite
(36 tests) was re-run against the LIVE production site (a temporary,
non-committed Playwright config pointing `baseURL` at
`https://yoavmp.github.io` with no local web server, reusing the existing
`e2e-book/*.spec.ts` files unmodified since their URLs are already
site-root-relative) — **36/36 passed**, exercising real behaviour, not
static markup:

- Exercise 2's feature-set comparison: config+data 200, both panels render,
  a real control change recomputes the plot/metrics, browser-refresh
  restores configured defaults.
- Exercise 3's `knn-explore` activity: config+manifest+binary all 200 (and,
  from the direct-URL check above, the old single-JSON path 404s), both
  plots render, a real k change recomputes the metrics/plots (not just the
  label), `k = N_fit` collapses the scatter to the fitting-set mean, browser
  refresh restores the configured default k.
- Exercise 3's `knn-abc` (honest-vs-invalid) activity: config+manifest+
  binary all 200, all three panels render with the audit-selected default
  k, `k=1` makes panels B and C exactly perfect while A is not.
- Both Exercise 3 activities usable at a 390 px narrow viewport with no
  horizontal document overflow.
- Colab / `.ipynb` download targets on all three chapters open/point at
  that chapter's own current portable notebook (not a stale or
  cross-chapter one).
- The primary sidebar toggle (desktop click, keyboard Enter/Space, narrow-
  viewport modal) all function correctly on the live site.

**Console/network**: an additional ad hoc check on the live Exercise 2 page
(hard-refreshed once) found zero failed network requests and exactly one
console message — `Got invalid theme mode: . Resetting to auto.` —
independently confirmed to be **pre-existing and unrelated to this WP**: the
identical message appears on `intro.html`, a page with no interactive widget
at all, so it originates from the PyData Sphinx theme's own dark-mode
bootstrap script, not from anything WP15 touched. No new console error or
failed request was introduced.

**Content re-verified live**: Exercise 2's page was fetched and its text
checked directly for the new WP15 Section 5 content (the `sensorimotor
strip` framing, the new `40, 60, 90, 130, 200, 300` size sequence) and the
absence of the old, no-longer-applicable text (`double descent`, `n_train <=
p`) — all as expected; the 360-feature main-regression content (Sections
1–4) is untouched and still present.

**Deployed revision matches the final pushed `main` commit**: confirmed via
the `gh-pages` deploy commit's own message (§7), not merely inferred.

## 9. Warnings, deviations, and items for Yoav

1. **Full baseline test/e2e suites were not independently re-run before the
   first WP15 edit** (§1) — the checkpoint tree is byte-identical to WP14's
   own already-validated final tree, and direct data-size/manifest-
   consistency checks against that tree were run, but the full
   271-Python/262-frontend/100-e2e/36-e2e-book suite itself was first run
   fresh only after the Exercise 2 and asset changes were made. Judged low
   risk given the identical starting tree, but noted per the WP's own
   instruction to record baseline checks.
2. **`sensorimotor_core` was not the highest-scoring passing candidate** —
   `auditory_core_belt` and `atlas_order_every_30th` both showed higher
   training-only R² at every predeclared size. This is by design (§2.2):
   selecting the highest-scoring candidate, even from a training-only
   comparison, would blur the line between "a predeclared rule chose this"
   and "the candidate that looked best was chosen" in a way the WP's own
   anti-cherry-picking framing (§2.2 of the WP) is clearly trying to avoid.
   Yoav may want to review whether this preference-order tie-break (small,
   simple, well-established bundle over a higher-scoring but less
   textbook-canonical one) is the right one going forward.
3. **A temporary, non-committed Playwright config was used for the live
   production acceptance run** (§8) and deleted immediately after use — the
   repository's own two committed Playwright configs
   (`playwright.config.ts`, `playwright.book.config.ts`) are unchanged and
   remain the only committed E2E configurations, per the general project
   preference against adding unrequested tooling.
4. **Pre-existing, unrelated items carried unchanged from WP14**: the
   `logo.png` missing / `book/README.md` not-in-toctree Jupyter Book
   warnings; the Vite 500 kB Plotly-chunk build advisory; the `Got invalid
   theme mode` console message (confirmed pre-existing in §8, not previously
   flagged in WP14's own report but verified today to be unrelated to any
   WP14 or WP15 change); the private-repository-distribution risk for the
   Colab/download buttons (unchanged, still out of scope).
5. **No classification exercise, and no WP16, were started**, per the WP's
   own stop condition.

## 10. Confirmation of safety constraints

- **The corrected 360 genuine CT features are preserved unchanged** in
  Exercise 2 Sections 1–4 and Exercise 3's whole main model — only Section
  5's own isolated demonstration uses the compact `sensorimotor_core`
  subset, exactly as WP15 §10 requires.
- **No feature/seed/sample-size/axis manipulation to force a preferred
  result** — the compact-subset decision came from a predeclared,
  training-only audit with a rule fixed before any candidate was scored; no
  axis was clipped or cropped (`assertNotIn("clip(", code)` re-verified).
- **No test-set leakage into scaling, feature choice, hyperparameter
  selection, or training** anywhere touched by this WP — re-verified
  structurally for the new audit module and the existing KNN/regression
  audits (unchanged).
- **No participant identifier or raw 360-feature table in any browser
  asset** — both binary payloads and their manifests carry only reordered-
  index/target-value data, checked by an identifier-token scan in both the
  Python validators and the shared TypeScript loader, and independently by
  the existing repo-wide "no raw imaging matrix" review already in place.
- **No degraded interactivity, accessible controls, or portable notebooks**
  — the full Playwright suite (standalone, built-book, and live production)
  passed unchanged in behaviour; the portable notebooks carry no
  JavaScript/binary-loader dependency.
- **No backend or CDN dependency added** — the built site remains fully
  static; verified live.
- **No Git LFS used** for any file fetched by the live Pages site.
- **No history rewrite, no force-push** — `git log` shows an ordinary linear
  history plus one ordinary merge commit; both pushes (`main`, plus the
  report commit below) were ordinary, non-forced pushes.
- **Did not deploy while any required test failed** — the §5 gate passed in
  full before the merge, and the post-merge smoke gate passed on `main`
  itself before pushing.
- **Repository visibility unchanged** (still public, untouched by this WP).
- **No WP16 created.**

## 11. Exact test commands and results

```
python -m unittest discover -s tests                             # 308 / 308
(cd interactive && npm run typecheck)                             # PASS
(cd interactive && npm run test:unit)                             # 276 / 276
(cd interactive && npm run build)                                 # succeeded (pre-existing 500kB Plotly-chunk advisory only)
(cd interactive && npm audit --omit=dev)                          # 0 vulnerabilities
(cd interactive && npx playwright test)                           # 100 / 100
python scripts/build_portable_notebook.py --check --notebook all  # all 3 up to date
python scripts/smoke_portable_notebook.py --notebook all          # OK x3, network, key values matched
rm -rf book/_build && jupyter-book build book                     # succeeded, 2 pre-existing warnings, no *.err.log
(cd interactive && npm run test:e2e:book)                         # 36 / 36
# repeated jupyter-book build x2: identical 12-PNG SHA-256 set both times
# live production run (temporary config, removed after use):
npx playwright test --config <temp> e2e-book/*.spec.ts            # 36 / 36 against https://yoavmp.github.io
```

Full before/after test-file breakdown: `WPs/reports/WP15_EXACT_CHANGELOG.md`.

## Key identifiers

| Item | Value |
|---|---|
| Branch | `feature/regression-practice` (unchanged, off `2cbf350`) |
| Checkpoint commit | `3b7cf5c` (`checkpoint: before WP15`) |
| Checkpoint tag | `wp15-start` → `3b7cf5c` |
| Implementation commit | `2584522` (`WP15: compact sample-size subset for Exercise 2; binary KNN asset format`) — 33 files changed; 3572 insertions(+), 1093 deletions(-) |
| Merge commit (on `main`) | `6288136` (`Merge feature/regression-practice into main (WP09-WP15)`, `--no-ff`, zero conflicts) |
| Pushed | `6d8c1f6..6288136` to `origin/main` |
| Deploy workflow run | `34692844653` — `success`, `headSha=6288136` |
| `gh-pages` deploy commit | `f8be61e` — `deploy: 6288136acf24f9c3009aa7de9555814313f6aa25` |
| Report commit | adds `WPs/reports/WP15_REPORT.md` + `WPs/reports/WP15_EXACT_CHANGELOG.md` only — SHA in the terminal summary |
| Sample-size audit script/result | `scripts/sample_size_audit.py` / `scripts/sample_size_audit_result.json` |
| Modelling manifest | `book/config/abide_modeling.json` |
| Canonical Exercise 2 notebook | `book/chapters/chapter_02/exercise_02.ipynb` SHA-256 `244b85eb0202d3bb2529a827f0123c99d162ba1f71e0fea074185fa11c2e23ff` |
| Portable Exercise 2 notebook | `book/downloads/chapter_02/exercise_02_portable.ipynb` SHA-256 `def3a276057428c109af9d592970b168141b1a13d01b2e64f108ced327e78869` |
| KNN explore manifest | `book/_static/widgets/data/abide_knn_explore_manifest.json` SHA-256 `6573f549f7fba3bc330d99c5df3e8c442c53256c068d81c9c67d444ea769b9bd` (2,212 bytes) |
| KNN explore binary | `book/_static/widgets/data/abide_knn_explore.bin` SHA-256 `4ded3bba61431fc8fcab680985b0b09632fb616c1be1da926b8337f2dff23357` (656,124 bytes) |
| KNN A/B/C manifest | `book/_static/widgets/data/abide_knn_abc_manifest.json` SHA-256 `591573297aca01c0dc2288728adec8c51bd2b8d88439109fad6fb8f247dd6d38` (1,162 bytes) |
| KNN A/B/C binary | `book/_static/widgets/data/abide_knn_abc.bin` SHA-256 `2c26cf2a51d8374018b5cce1d0264358b511c9b61d81761ead7d73521ef45845` (634,032 bytes) |

## Instructions for reviewer

Paste this entire report (`WP15_REPORT.md`) into the conversation reviewing
this WP. `WP15_EXACT_CHANGELOG.md` is the companion location-specific
before/after record.
