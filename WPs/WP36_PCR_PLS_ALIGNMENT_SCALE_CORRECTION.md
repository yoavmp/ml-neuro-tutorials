# WP36 — Correct the PCR/PLS Alignment Activity

## 1. Purpose

Correct Exercise 9's **PCR or PLS?** interactive activity so its Weak, Moderate, and Strong alignment presets differ only in the direction of predictive signal—not in target variance, signal strength, or noise level.

The current WP35 activity correctly shows the PLS advantage shrinking as the target aligns more strongly with PC1, but PCR's absolute validation MSE does not improve monotonically. This occurs because swapping raw PC coefficients changes the target's total variance: PC1 and PC2 have very different variances, so raw MSE is not comparable across presets.

The corrected activity must make the intended lesson visually and numerically intuitive:

- weak alignment with PC1: one-component PCR performs poorly and PLS has its clearest advantage;
- moderate alignment: PCR improves and the PCR–PLS gap becomes smaller;
- strong alignment with PC1: one-component PCR performs best and the PCR–PLS gap becomes small;
- with two components: PCR and PLS converge to the same full linear predictor-space result.

This is a focused correction. Do not redesign Exercise 9 or change the real ABIDE model comparison.

---

## 2. Starting state and branch safety

1. Record:
   - `git status --short --branch`;
   - current branch and `HEAD`;
   - the tip of `fix/wp35-exercises7-9-review`.
2. Start from the final committed WP35 branch tip, including its reports.
3. Resolve and record the literal WP35 branch-tip SHA from Git rather than relying on the report file.
4. Confirm the current activity reproduces the WP35 values and behavior before editing.
5. Preserve these pre-existing untracked files if present:
   - `WPs/reports/WP16_ARCHITECT_REPORT.md`
   - `WPs/reports/WP21_DEPLOYMENT_REPORT.md`
6. Do not reset, rebase, stash, clean, delete, or overwrite unrelated work.
7. If the starting state differs materially, stop and report the discrepancy.
8. Create:

   `fix/wp36-pcr-pls-alignment-scale`

9. Add and commit this specification as the initial checkpoint before implementation.
10. Commit implementation and reports locally. Do **not** merge, push, deploy, monitor GitHub Actions, or begin WP37.

---

## 3. Correct the synthetic target construction

Retain the existing deterministic predictor cloud, train/validation split, and general visual design.

Replace the raw coefficient-swapping target construction with a variance-controlled construction.

### Required approach

1. Express each participant on the known high-variance and low-variance axes.
2. Center each axis score and divide it by its own standard deviation, producing standardized component scores `z_pc1` and `z_pc2`.
3. Define each preset through a unit-length signal direction:

   ```text
   signal = w1 * z_pc1 + w2 * z_pc2
   w1² + w2² = 1
   ```

4. Use three fixed directions:
   - **Weak alignment with PC1:** `w1` small and `w2` large;
   - **Moderate alignment:** similar contributions from both directions;
   - **Strong alignment with PC1:** `w1` large and `w2` small.
5. Use the same overall signal multiplier for every preset.
6. Use the same deterministic noise realization and the same noise standard deviation for every preset.
7. Prefer orthogonalizing the fixed noise realization with respect to both component-score vectors before standardizing it. This prevents chance signal–noise covariance from changing total target variance across presets.
8. Keep the target centered consistently.

Reasonable example directions are:

```text
Weak:     w1 = 0.25, w2 = sqrt(1 - 0.25²)
Moderate: w1 = 1/sqrt(2), w2 = 1/sqrt(2)
Strong:   w1 = sqrt(1 - 0.25²), w2 = 0.25
```

These exact weights may be adjusted once if the finite deterministic sample fails to demonstrate the required monotonic teaching pattern. Any adjustment must:

- remain symmetric between Weak and Strong;
- preserve unit-length directions;
- preserve fixed signal variance and noise variance;
- be documented in the report;
- not involve repeated searching for aesthetically preferred results.

Do not change the predictor cloud or train/validation rows to manufacture the desired result.

---

## 4. Required quantitative behavior

Regenerate every PCR/PLS fit and require all of the following.

### Dataset invariants

- Predictor coordinates are byte-for-byte unchanged from WP35.
- Training and validation row IDs are unchanged.
- The same standardized/orthogonalized noise vector is used in every preset.
- Signal variance is equal across presets within strict numerical tolerance.
- Noise variance is identical across presets.
- Total target variance is equal across presets within a tight tolerance appropriate to the construction.
- Signal-to-noise ratio is identical across presets.

### One-component behavior

Using validation results:

- `PCR_MSE(Weak) > PCR_MSE(Moderate) > PCR_MSE(Strong)`;
- PLS has its largest MSE advantage over PCR under Weak alignment;
- the PLS advantage shrinks from Weak → Moderate → Strong;
- Strong PCR performs substantially better than Weak PCR, not merely by an insignificant floating-point difference.

Also compute validation R-squared for each combination. Require:

- `PCR_R2(Weak) < PCR_R2(Moderate) < PCR_R2(Strong)`;
- the R-squared result tells the same qualitative story as MSE.

### Two-component behavior

- PCR and PLS validation predictions converge within strict numerical tolerance for each preset;
- their validation MSE and R-squared match within tolerance;
- retaining both directions does not reverse the intended conceptual explanation.

If the first variance-controlled construction fails any invariant, diagnose whether the problem is implementation, finite-sample noise, or model behavior. Make at most one documented adjustment to direction spacing or noise magnitude. If it still fails, stop and report instead of entering a search loop.

---

## 5. Update the interactive display

Keep the existing controls:

- method: PCR or PLS;
- components: 1 or 2;
- target alignment with the highest-variance direction: Weak, Moderate, Strong.

Update the activity so students can compare presets meaningfully.

Required display changes:

1. Continue showing training MSE and validation MSE.
2. Add validation R-squared as a compact additional metric, unless careful visual inspection demonstrates that it makes the stats area unacceptably crowded. If space is genuinely inadequate, use normalized validation MSE instead and document the decision.
3. Add a brief note near the preset control or statistics:

   > Signal strength and noise are held constant; only the target's direction changes.

4. Update construction notes so they describe standardized component directions rather than raw coefficients whose meaning depends on component variance.
5. Ensure the Weak/Moderate/Strong labels remain understandable without mathematical notation in the main interface.
6. Keep the existing fixed predictor cloud, train/validation marker distinction, component-direction line, and observed-versus-predicted plot.
7. Preserve responsive iframe height behavior after adding the metric/note.

Do not add another activity or lengthen the notebook substantially.

---

## 6. Update Exercise 9 text and runnable reproduction

Update only text directly related to the activity.

Explain concisely:

- all three presets have the same signal strength and noise level;
- only the orientation of target-relevant information changes;
- this makes performance differences comparable across presets;
- PCR performs best when the predictive direction aligns with PC1;
- PLS can help when predictive information lies away from the highest-variance direction.

Review the guiding questions and revealed answers so they match the corrected results.

Update:

- canonical notebook;
- hidden website reproduction code;
- portable notebook reproduction code;
- widget description and instructions;
- generated widget artifact;
- stored notebook output if affected.

Do not change the ABIDE nested-CV results, LinearSVR grid, RBF-SVR settings, or other Exercise 9 sections.

---

## 7. Audit and tests

Update the export/audit path and add focused tests for:

1. unchanged predictor coordinates;
2. unchanged train/validation split;
3. unit-length preset directions;
4. equal signal variance;
5. identical noise vector and variance;
6. comparable total target variance;
7. identical signal-to-noise ratio;
8. PCR MSE strictly improves Weak → Moderate → Strong;
9. PCR validation R-squared strictly improves Weak → Moderate → Strong;
10. PLS's one-component advantage shrinks Weak → Moderate → Strong;
11. PCR and PLS converge with two components;
12. frontend schema includes any new R-squared fields;
13. live widget metrics and plots update correctly;
14. note about fixed signal/noise is visible;
15. light mode, dark mode, narrow view, reload, and iframe-height contract remain correct.

Tests must compare the actual values shown in the browser with the committed Python-generated artifact rather than checking only that text changes.

---

## 8. Portable notebook behavior

Regenerate Exercise 9's portable notebook.

Requirements:

- the reproduction code uses the same variance-controlled construction;
- it remains visible and editable;
- it executes without repository access;
- Exercise 9 smoke execution passes;
- the optional full ABIDE nested-CV flag remains `False` by default and is otherwise untouched.

---

## 9. Bounded validation plan

Run only the validation relevant to this focused correction:

1. regenerate the PCR/PLS artifact and run its `--check`;
2. focused Python export/invariant tests;
3. Exercise 9 notebook/content tests;
4. regenerate Exercise 9 portable notebook and run generator `--check`;
5. smoke-execute Exercise 9 portable notebook outside the repository;
6. focused frontend unit tests and typecheck;
7. one frontend production build;
8. focused standalone PCR/PLS Playwright test;
9. one Jupyter Book build;
10. focused built-book Exercise 9, dark-mode, and iframe-height tests;
11. full Python suite once;
12. full frontend unit suite once;
13. full standalone and built-book Playwright suites once;
14. manual visual inspection of the activity in light, dark, and narrow views.

Rules:

- Do not rerun a passing full suite.
- On failure, diagnose the cause, make one bounded correction, and rerun only the failed focused gate once.
- If the required quantitative teaching pattern still fails after the one permitted construction adjustment, stop and report.
- Do not run, watch, or poll GitHub Actions.
- Do not merge, push, or deploy.

---

## 10. Reports and stopping condition

Create:

- `WPs/reports/WP36_REPORT.md`
- `WPs/reports/WP36_EXACT_CHANGELOG.md`

The report must include:

1. overall success or failure;
2. resolved WP35 branch-tip SHA;
3. WP36 starting branch/SHA;
4. implementation commit SHA;
5. exact target-construction formula and preset weights;
6. proof that signal/noise/target variance and SNR are comparable;
7. before-versus-after one-component PCR/PLS MSE values;
8. final validation MSE and R-squared for every preset/method/component combination;
9. every retry, adjustment, deviation, or judgment call;
10. validation commands and outcomes;
11. confirmation that the ABIDE comparison, Syllabus, and Word overview were untouched;
12. confirmation that nothing was merged, pushed, deployed, or monitored through GitHub Actions.

As in WP35, do not claim that a report contains its own final commit SHA. After committing the reports, run `git rev-parse HEAD` and include the literal final branch-tip SHA and final `git status --short --branch` in Claude's final response.

After committing the reports, stop. Do not begin deployment or WP37.
