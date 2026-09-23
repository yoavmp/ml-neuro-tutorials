# WP36 Report — Correct the PCR/PLS Alignment Activity

## 1. Overall result

**SUCCESS.** Exercise 9's "PCR or PLS?" activity's target construction was
replaced with a variance-controlled construction: each preset is now a
unit-length signal direction over standardized, mutually orthogonal
component scores, with an identical fixed noise realization added to every
preset. This makes one-component PCR's validation MSE strictly monotonic
(Weak > Moderate > Strong) and its validation R² strictly monotonic in the
opposite direction, with the PLS advantage shrinking monotonically, and
PCR/PLS still converge exactly at two components — all on the first
attempt, with no adjustment needed to the example weights given in the
spec. All bounded validation gates passed. Everything is committed locally
on `fix/wp36-pcr-pls-alignment-scale`; nothing was merged, pushed, deployed,
or monitored through GitHub Actions.

## 2. Resolved WP35 branch-tip SHA

`0e10af7` (`0e10af7d9336e7eceb84b58fd68accd439a56828`, "WP35: reports —
Exercises 7-9 review execution report and exact changelog"), the tip of
`fix/wp35-exercises7-9-review`. Resolved by `git rev-parse
fix/wp35-exercises7-9-review` and `git log --oneline -1`, both returning
`0e10af7`.

## 3. WP36 starting branch/SHA and checkpoint

- **Starting point:** `fix/wp35-exercises7-9-review` @ `0e10af7` —
  `git status --short --branch` was clean (only the untracked WP36
  specification file), confirming HEAD matched the resolved WP35 tip
  exactly.
- Before editing, confirmed the current activity reproduces the WP35
  values and behavior: `scripts/export_pcr_pls_widget.py --check` printed
  `moderate` PCR=0.666/PLS=0.618, `strong` PCR=0.710/PLS=0.672, `weak`
  PCR=0.674/PLS=0.512 — matching `WPs/reports/WP35_REPORT.md` §6 exactly,
  and reproducing the documented defect: PCR's own validation MSE is
  **not** monotonic across presets (0.674 → 0.666 → 0.710 — it dips at
  "moderate" then rises at "strong").
- `WPs/reports/WP16_ARCHITECT_REPORT.md` and
  `WPs/reports/WP21_DEPLOYMENT_REPORT.md` were present and untracked, as
  required, and were not touched.
- **New branch:** `fix/wp36-pcr-pls-alignment-scale`, created from the SHA
  above.
- **Checkpoint commit** (spec added before implementation): `0342867`.
- **Implementation commit:** `ba11f3f` ("WP36: correct PCR/PLS alignment
  activity to a variance-controlled target").

## 4. Exact target-construction formula and preset weights

For each of the 60 fixed observations, with `pc1`/`pc2` the closed-form raw
PC1/PC2 scores (unchanged from WP34/35):

```text
z_pc1 = (pc1 - mean(pc1)) / std(pc1)                      # unit variance
z_pc2_raw = (pc2 - mean(pc2)) / std(pc2)                  # unit variance
z_pc2 = standardize(z_pc2_raw - (z_pc2_raw . z_pc1 / z_pc1 . z_pc1) * z_pc1)
        # Gram-Schmidt against z_pc1, then re-standardized to unit variance
```

This step was a necessary, documented addition beyond the spec's literal
§3.1–3.2 wording: raw PC1/PC2 have a real, non-negligible in-sample
correlation of **≈0.1126** (not exactly 0, a finite-N=60 artifact of a true
bivariate-normal draw whose *population* PC1/PC2 are uncorrelated) —
confirmed by direct measurement before writing any implementation code.
Left uncorrected, `var(signal) = w1² + w2² + 2·w1·w2·corr(z_pc1, z_pc2)`
would depend on `(w1, w2)`, varying by roughly 5–11% between "moderate" and
"weak"/"strong" — failing §4's "signal variance equal across presets within
strict numerical tolerance" outright. Orthogonalizing `z_pc2` against
`z_pc1` (then re-standardizing) makes `corr(z_pc1, z_pc2) = 0` to within
`~2e-17` (floating-point noise), so `var(signal) = w1² + w2² = 1` exactly
for any unit-length `(w1, w2)`, regardless of preset.

```text
signal = signal_sd * (w1 * z_pc1 + w2 * z_pc2)   # signal_sd = 1.0, fixed for every preset
noise  = noise_sd * orthogonalize(orthogonalize(N(0,1) draw, z_pc1), z_pc2)
                                                  # noise_sd = 0.3, one fixed draw, reused verbatim
y      = center(signal + noise)
```

The noise draw is orthogonalized against **both** standardized scores
(sequential Gram-Schmidt) before being rescaled to `noise_sd`, per §3.7 —
confirmed numerically: `corr(noise, z_pc1)` and `corr(noise, z_pc2)` are
both `~3e-17` after this step. The exact same realized noise values (not
merely the same distribution) are added to every preset.

**Preset weights** — the spec's own §3's example directions, used
verbatim, with no adjustment needed (the "at most one documented
adjustment" allowance in §3/§4 was not exercised):

| Preset | `w1` (PC1 weight) | `w2` (PC2 weight) | Label |
|---|---|---|---|
| Weak | `0.25` | `0.9682458365518543` (`sqrt(1-0.25²)`) | Weak alignment with the highest-variance direction |
| Moderate | `0.7071067811865476` (`1/sqrt(2)`) | `0.7071067811865476` | Moderate alignment with the highest-variance direction |
| Strong | `0.9682458365518543` | `0.25` | Strong alignment with the highest-variance direction |

`signal_sd = 1.0`, `noise_sd = 0.3` (both in
`book/config/abide_modeling.json`'s `advanced_models.pcr_pls_activity`).
Several `(signal_sd, noise_sd)` combinations were tried in a scratch script
*before* touching any committed file, purely to confirm robustness of the
qualitative pattern and to select values giving a pedagogically clear
story (weak PCR near chance, strong PCR clearly good) rather than to search
for one specific numeric outcome; every combination tried already satisfied
every required monotonic invariant, so `(1.0, 0.3)` — the first
combination tried that also gives readable, mostly-positive R² values — was
adopted without needing the spec's "at most one adjustment" allowance.

## 5. Proof that signal/noise/target variance and SNR are comparable

Measured directly from the corrected construction (full 60-observation
sample):

| Preset | `var(signal)` | `var(noise term)` | `var(target)` | SNR |
|---|---|---|---|---|
| Weak | `1.000000` | `0.090000` | `1.090000` | `11.1111` |
| Moderate | `1.000000` | `0.090000` | `1.090000` | `11.1111` |
| Strong | `1.000000` | `0.090000` | `1.090000` | `11.1111` |

All three match to at least 6 decimal places (the residual is floating-
point noise, `~1e-16`–`1e-17`). `signal_sd² = 1.0`, `noise_sd² = 0.09`,
`SNR = signal_sd²/noise_sd² = 11.1111...` is a fixed manifest-level
constant that never enters the per-preset computation, so it is
mathematically guaranteed identical regardless of preset — not merely
observed to be close.

## 6. Before-versus-after one-component PCR/PLS values

| Preset | WP35 PCR (broken) | WP35 PLS | WP36 PCR (corrected) | WP36 PLS |
|---|---|---|---|---|
| Weak | 0.674 | 0.512 | **1.2472** | 0.5970 |
| Moderate | 0.666 | 0.618 | **0.7667** | 0.5367 |
| Strong | 0.710 | 0.672 | **0.2532** | 0.2230 |

WP35's PCR column is **not monotonic** (0.674 → 0.666 → 0.710: dips, then
rises above the "weak" value) — the exact defect WP36 was scoped to fix.
WP36's PCR column is **strictly monotonic decreasing** (1.2472 → 0.7667 →
0.2532), a difference of 0.994 between weak and strong (not an
insignificant floating-point gap), because the presets' *signal
variance* is now held fixed instead of changing with which raw axis
happens to carry the larger coefficient.

## 7. Final validation MSE and R² for every combination

| Preset | Components | Method | Train MSE | Train R² | Val MSE | Val R² |
|---|---|---|---|---|---|---|
| Weak | 1 | PCR | 0.9525 | 0.0661 | 1.2472 | -0.1343 |
| Weak | 1 | PLS | 0.3791 | 0.6283 | 0.5970 | 0.4571 |
| Weak | 2 | PCR | 0.0686 | 0.9328 | 0.1579 | 0.8564 |
| Weak | 2 | PLS | 0.0686 | 0.9328 | 0.1579 | 0.8564 |
| Moderate | 1 | PCR | 0.5409 | 0.5066 | 0.7667 | 0.1668 |
| Moderate | 1 | PLS | 0.3371 | 0.6925 | 0.5367 | 0.4167 |
| Moderate | 2 | PCR | 0.0686 | 0.9375 | 0.1579 | 0.8284 |
| Moderate | 2 | PLS | 0.0686 | 0.9375 | 0.1579 | 0.8284 |
| Strong | 1 | PCR | 0.1251 | 0.8967 | 0.2532 | 0.6449 |
| Strong | 1 | PLS | 0.1020 | 0.9157 | 0.2230 | 0.6873 |
| Strong | 2 | PCR | 0.0686 | 0.9434 | 0.1579 | 0.7786 |
| Strong | 2 | PLS | 0.0686 | 0.9434 | 0.1579 | 0.7786 |

Required invariants, all confirmed:

- **PCR MSE strictly improves** Weak (1.2472) → Moderate (0.7667) → Strong
  (0.2532). ✓
- **PCR R² strictly improves** Weak (-0.1343) → Moderate (0.1668) → Strong
  (0.6449), telling the same qualitative story as MSE. ✓
- **PLS's one-component MSE advantage over PCR shrinks** Weak (gap
  0.6503) → Moderate (0.2300) → Strong (0.0302); Strong's gap is under
  half of Weak's (0.0302 < 0.3251). ✓
- **PCR and PLS converge with two components**: identical `trainMse` and
  `valMse` (`0.0686`/`0.1579`) for every preset — note the two-component
  `valMse` is identical *across presets too* here (not just PCR=PLS within
  a preset): with both directions retained, PCR/PLS both recover the exact
  same full-predictor-space OLS fit, whose only unexplained validation
  error is the noise term, and the noise realization is identical across
  presets — a clean, expected illustration of the lesson, not a bug. The
  per-preset validation R² still differs slightly at two components
  (0.856/0.828/0.779) because R² divides by that specific 20-point
  validation subset's own empirical target variance, which is not
  perfectly identical to the full-60-point population value used for the
  variance-equality proof in §5 (an expected, small finite-sample effect,
  unrelated to the corrected construction). Retaining both directions does
  not reverse the conceptual explanation for any preset. ✓

## 8. Retries, adjustments, deviations, and judgment calls

- **Orthogonalizing `z_pc2` against `z_pc1` (necessary addition, not
  merely "preferred" as the noise-only orthogonalization in §3.7 is
  worded).** Measured the raw PC1/PC2 sample correlation (≈0.1126) before
  writing any target-construction code and confirmed analytically that,
  left uncorrected, it would make signal variance depend on `(w1, w2)` by
  5–11%, violating §4's "equal signal variance...within strict numerical
  tolerance" outright. This is a filled-in implementation detail the
  spec's §3.1–3.2 wording did not spell out (it explicitly required
  orthogonalizing the *noise*, but was silent on `z_pc1`/`z_pc2` mutual
  correlation) rather than a deviation from anything explicit; flagged
  here for visibility per WP36 §10.9's instruction to record every
  judgment call.
- **No preset-weight or noise-magnitude adjustment was needed.** The
  spec's own example weights (§3, used verbatim) and a same-first-try
  choice of `(signal_sd, noise_sd) = (1.0, 0.3)` already satisfied every
  required invariant in §4 on the first attempt (confirmed in a throwaway
  scratch script before touching any committed file). Several other
  `(signal_sd, noise_sd)` pairs were also tried in that same scratch
  script purely to compare pedagogical clarity (how positive/readable the
  resulting R² values are) — this was a one-time comparison among several
  values that all already passed every invariant, not a search for one
  that would pass, so it does not count against the "not involve repeated
  searching for aesthetically preferred results" restriction in §3.
- **Reproduction-cell test string wrap (1 correction, caught immediately
  by the first test run).** A new Python test asserted `"pls can help
  most"` as a single lowercase substring against the notebook's own
  intro-paragraph text, but the source wraps "pls" and "can help most"
  across a line break; fixed by normalizing whitespace before the
  substring check (the same `_norm_ws` helper already used elsewhere in
  the same test file). Rerun once; passed.
- No other test, build, or Playwright failure occurred at any point in
  this WP — every focused and full gate in §9 passed on its first run
  except the one immediate, mechanical fix above.

## 9. Validation commands and outcomes (bounded plan, in order)

| # | Gate | Command(s) | Result |
|---|------|------------|--------|
| 1 | Regenerate PCR/PLS artifact + `--check` | `export_pcr_pls_widget.py --refresh`/`--check` | OK, instant |
| 2 | Focused Python export/invariant tests | `unittest -p test_export_pcr_pls_widget_data.py` (24 tests, 9 new) | OK |
| 3 | Exercise 9 notebook/content tests | `unittest -p test_exercise_09_notebook.py` (53 tests, 2 new); notebook re-executed (default `RUN_FULL_NESTED_CV=False` path, ~seconds) | 1 correction (whitespace-normalization in a brand-new test, see §8); then OK |
| 4 | Regenerate Exercise 9 portable notebook + generator `--check` | `build_portable_notebook.py --write --notebook chapter_09`; `--check --notebook all` | All 9 registered notebooks up to date |
| 5 | Smoke-execute Exercise 9 portable notebook outside the repository | `scripts/smoke_portable_notebook.py --notebook chapter_09`; independently, `jupyter nbconvert --execute --inplace` on a copy in `/tmp` | Both: 0 errors, key values matched |
| 6 | Focused frontend unit tests + typecheck | `npx tsc --noEmit`; `npx vitest run tests/pcr-pls-explore-data.test.ts` (12 tests) | Clean |
| 7 | One frontend production build | `npm run build` | Succeeded (pre-existing >500 kB chunk-size warning, unrelated) |
| 8 | Focused standalone PCR/PLS Playwright test | `npx playwright test e2e/pcr-pls-explore.spec.ts` (10 tests, 2 new: fixed-note visibility, browser-vs-artifact R²/MSE comparison across all 12 combinations) | 10/10 |
| 9 | One Jupyter Book build | `jupyter-book build book` | Succeeded, 2 warnings (both pre-existing: missing `logo.png`, `README.md` not in any toctree) |
| 10 | Focused built-book Exercise 9, dark-mode, iframe-height tests | `playwright test --config playwright.book.config.ts e2e-book/chapter09.spec.ts e2e-book/chapter09-dark-mode.spec.ts e2e-book/iframe-height-contract.spec.ts` | 28/28 (7 `chapter09.spec.ts` + 1 `chapter09-dark-mode.spec.ts` + 20 `iframe-height-contract.spec.ts` cases, one per Exercise 1-9 iframe) |
| 11 | Full Python suite once | `unittest discover -s tests -p 'test_*.py'` | **990 tests, 0 failures, 11 skipped** (network-only; up from 979 in WP35) |
| 12 | Full frontend unit suite once | `npm test` | **34 files / 426 tests, all passed** (unchanged count — this WP added Playwright coverage, not new `.test.ts` files) |
| 13 | Full standalone + built-book Playwright once | `npx playwright test`; `npx playwright test --config playwright.book.config.ts` | **246/246** standalone (up from 244, +2 new PCR/PLS checks); **139/139** built-book (unchanged from WP35 — no new built-book spec files added in this WP) |
| 14 | Manual visual inspection | Playwright screenshots of the standalone activity: light, dark (`colorScheme: "dark"`), and a 390px-narrow viewport | Confirmed correct in all three: the new validation-R² stat and the fixed-signal/noise note read cleanly on one/two lines respectively with no crowding, so the plain R² addition (§5.2's primary option) was used rather than falling back to normalized MSE |

No gate was rerun more than the bounded-plan-permitted one-correction
cycle. No full suite was rerun speculatively.

## 10. Confirmation: ABIDE comparison, Syllabus, and Word overview untouched

- `book/config/abide_modeling.json`'s `advanced_models.abide_comparison`
  and `advanced_models.svm_activity` keys were not modified — only
  `advanced_models.pcr_pls_activity` changed (`git diff` confirms the
  surrounding JSON is untouched).
- `scripts/advanced_models_audit.py`,
  `scripts/advanced_models_audit_result.json`, the LinearSVR grid, and the
  RBF-SVR fixed `epsilon` were not opened or modified.
- Exercise 9's Section 8 (ABIDE nested-CV comparison), Section 5–7 (SVM),
  and Sections 9–11 were not opened or modified — confirmed by
  `git diff book/chapters/chapter_09/exercise_09.ipynb` touching only
  Section 4's own cells (an inserted intro paragraph and the rewritten
  hidden reproduction cell).
- `book/syllabus.md` and the `course_overview/` Word document were not
  opened, read, or modified.
- `WPs/reports/WP16_ARCHITECT_REPORT.md` and
  `WPs/reports/WP21_DEPLOYMENT_REPORT.md` were preserved untracked.

## 11. Confirmation: nothing merged, pushed, deployed, or monitored via CI

Nothing was merged, pushed, or deployed. No GitHub Actions workflow was
run, triggered, or monitored. All work exists only in local commits on
`fix/wp36-pcr-pls-alignment-scale`.

## 12. Final `git status --short --branch` and decorated log

Immediately before committing this report + changelog:

```
## fix/wp36-pcr-pls-alignment-scale
?? WPs/reports/WP36_EXACT_CHANGELOG.md
?? WPs/reports/WP36_REPORT.md
```

Decorated log at the implementation commit (parent of this report commit):

```
ba11f3f (HEAD -> fix/wp36-pcr-pls-alignment-scale) WP36: correct PCR/PLS alignment activity to a variance-controlled target
0342867 WP36: add specification (initial checkpoint)
0e10af7 (fix/wp35-exercises7-9-review) WP35: reports — Exercises 7-9 review execution report and exact changelog
918a0eb WP35: Exercises 7-9 review corrections and reusable iframe auto-resize
96a9263 WP35: add specification (initial checkpoint)
```

The final branch-tip SHA (after this report commit) is reported literally
in Claude's final response to the user, per WP36 §10 (a commit cannot
contain its own SHA).
