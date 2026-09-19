# WP31R — CI Float Portability Correction and Redeployment

## Purpose

Correct the single CI-only failure from WP31 and redeploy Exercises 4–6.

WP31 merged and pushed the intended release to `origin/main` at
`3da7d3f8b1ad4fe627f9581d23ef7e267a2c47ed`, but GitHub Actions failed before building or
publishing. The reported failure was an exact serialized-JSON comparison between the committed
greedy-tree artifact and a fresh recomputation. macOS and Linux produced scientifically
equivalent floating-point values differing only in their final decimal digit.

This WP must first confirm that diagnosis, then make the narrowest robust portability correction,
run the release gates, push once, monitor one workflow, and verify the live site.

Do not redesign notebooks, widgets, datasets, models, or activities.

## 1. Expected starting state and Git safety

Expected remote state:

- `origin/main` at WP31 `RELEASE_SHA`:
  `3da7d3f8b1ad4fe627f9581d23ef7e267a2c47ed`;
- that commit has a failed GitHub Actions run `35437984824`;
- production `gh-pages` remains at its prior release because WP31 failed before publishing.

Expected local state:

- local `main` is exactly one WP31 documentation-only commit ahead of `origin/main`;
- the only permitted untracked files are:
  - `WPs/reports/WP16_ARCHITECT_REPORT.md`;
  - `WPs/reports/WP21_DEPLOYMENT_REPORT.md`;
  - this WP31R specification, before its initial commit.

Procedure:

1. Start on local `main`.
2. Record the actual full local and remote SHAs and `git status --short --branch`.
3. Run one `git fetch origin main` and confirm `origin/main` is still exactly the WP31 release
   SHA above.
4. Confirm local `main` is exactly one documentation-only commit ahead and that the commit contains
   only `WP31_DEPLOYMENT_REPORT.md` and `WP31_EXACT_CHANGELOG.md`.
5. Stop if any state differs unexpectedly. Do not pull, reset, rebase, stash, delete, overwrite,
   force-push, or resolve divergence automatically.
6. Create `fix/wp31r-ci-float-portability` from local `main`.
7. Save this specification as `WPs/WP31R_CI_FLOAT_PORTABILITY_AND_REDEPLOY.md` and commit it as the
   first checkpoint before implementation changes.
8. Leave the two whitelisted legacy reports untouched and untracked.

## 2. Confirm the failure mechanism before changing code

Inspect:

- `tests/test_export_tree_greedy_widget_data.py`;
- `scripts/export_tree_greedy_widget.py`;
- `book/_static/widgets/data/tree_greedy_split.json`;
- the failed log from GitHub Actions run `35437984824`.

Confirm and report:

1. which paths and numeric fields differed;
2. the maximum absolute numeric difference;
3. whether any dictionary key, list length/order, string, Boolean, integer, selected seed, feature,
   threshold ordering, optimal split, observation count, or round structure differed;
4. whether the discrepancy is confined to insignificant final-digit floating-point variation.

If any semantic or structural difference exists, or any numeric discrepancy is materially larger
than the reported approximately `1e-6` scale, stop. Do not hide a real artifact mismatch behind a
tolerance.

## 3. Implement a semantic artifact comparison

Replace the cross-platform-invalid byte-for-byte JSON comparison with a reusable recursive
semantic comparison.

The comparison contract must be strict:

- dictionary keys must match exactly;
- list lengths and ordering must match exactly;
- strings, Booleans, `null`, and integers must match exactly;
- numeric floating-point leaves may differ only within a documented absolute tolerance;
- use `rel_tol=0` so large values do not receive a proportionally larger allowance;
- the comparator must report the failing JSON path and both values when a mismatch occurs;
- NaN and infinity must not be silently accepted;
- changes to selected seed, optimal feature, split order, thresholds beyond tolerance, participant
  observations beyond tolerance, or activity structure must still fail.

Choose the smallest explicit tolerance justified by the CI evidence. If the report's observed
difference is confirmed, prefer an absolute tolerance around `2e-6`; do not exceed `5e-6` without
stopping for user approval.

Use the same comparison contract in:

1. `test_matches_a_fresh_recomputation`; and
2. the exporter's `--check` path if that path also relies on exact serialized floating-point
   equality or could fail for the same cross-platform reason.

Do not merely skip, delete, xfail, or weaken the recomputation test. It must continue to verify
the complete artifact semantically.

Do not regenerate the committed artifact merely to match the current platform unless the
diagnostic step proves its semantic content is actually stale. A platform-specific regenerated
artifact would reproduce the same problem in the opposite environment.

## 4. Add focused regression tests

Add tests proving that the semantic comparator:

1. accepts otherwise identical nested data with a float difference smaller than the chosen
   tolerance;
2. rejects a float difference larger than the tolerance;
3. rejects a changed selected seed;
4. rejects a changed optimal feature or split threshold beyond tolerance;
5. rejects a missing/extra dictionary key;
6. rejects changed list order or length;
7. reports the relevant nested JSON path;
8. rejects non-finite numeric values;
9. still confirms the committed artifact matches a fresh recomputation locally;
10. leaves all existing greedy-dataset acceptance, no-answer-leakage, and three-round audit tests
    intact.

Do not reduce existing coverage to make CI pass.

## 5. Bounded local validation

Run each gate once after the correction. If a gate fails because of this correction, make one
focused fix and rerun only that failed gate once. Stop on unrelated or repeated failure.

1. Focused greedy-exporter tests.
2. `python scripts/export_tree_greedy_widget.py --check`.
3. All Exercise 6 focused Python tests.
4. Full offline Python test suite.
5. Portable-notebook deterministic check for all chapters.
6. Registered portable smoke test plus independent Exercise 5/6 smoke execution, following WP31's
   proven procedure.
7. Frontend typecheck and unit tests only if frontend files changed; otherwise document that they
   were unnecessary.
8. One production frontend build only if frontend inputs changed; otherwise reuse the committed
   bundle and document why.
9. One clean Jupyter Book build.
10. Focused built-book tests for Exercises 4–6, launch buttons, and cross-chapter dark mode.

If Docker or another already-configured Linux runtime is available, run the focused exporter test
once there as additional evidence. Do not install or introduce a container system solely for this
WP. GitHub Actions remains the authoritative Linux verification.

No arbitrary sleeps, skips, lowered assertions, global retries, or repeated stress loops.

## 6. Merge the correction into local `main`

Only after all required local gates pass:

1. Switch to local `main`.
2. Reconfirm it is unchanged from the verified starting state and is clean apart from the two
   whitelisted reports.
3. Merge `fix/wp31r-ci-float-portability` with one non-fast-forward merge commit:

   ```bash
   git merge --no-ff fix/wp31r-ci-float-portability -m "Fix cross-platform greedy-tree artifact verification"
   ```

4. Stop on any conflict; do not resolve it automatically.
5. Record the merge commit as `WP31R_RELEASE_SHA`.
6. Prove the merged `main` tree is identical to the correction-branch tree.
7. Confirm the diff from WP31's release contains only:
   - the previously local WP31 reports;
   - the WP31R specification;
   - the narrow comparator/test correction and any strictly necessary related documentation.

Do not amend, squash, rebase, or rewrite history.

## 7. Push exactly once

After all merge checks pass:

```bash
git push origin main
```

- Perform exactly one push.
- If rejected or unsuccessful, stop. Do not pull, retry, rebase, or force-push.
- After success, use a read-only remote query to verify `origin/main` equals
  `WP31R_RELEASE_SHA`.

## 8. Monitor exactly one workflow run

Identify the deployment workflow triggered by `WP31R_RELEASE_SHA`:

1. Query once.
2. If no matching run appears, wait at most 30 seconds and query once more.
3. If still absent, stop and report.
4. Once found, verify its `headSha`, record the run ID, and execute exactly one continuous:

   ```bash
   gh run watch RUN_ID --exit-status
   ```

5. Do not use a background watcher, scheduled wakeup, parallel polling, second watch, or workflow
   rerun.

If the workflow fails, retrieve its failed log once, document the exact blocker, and stop. Do not
fix or push again within WP31R.

## 9. Verify the live production site

Perform this section only after the workflow succeeds. Use a fresh browser context and a
cache-busting query string against:

`https://yoavmp.github.io/ml-neuro-tutorials/`

### 9.1 Structure and pages

Verify:

- Exercises 1–3 still load with their expected titles and content;
- Exercise 4 is **Validation and Cross-Validation**, not a placeholder;
- Exercise 5 is **Regularization and Feature Selection**, not a placeholder;
- Exercise 6 is **Decision Trees**, not a placeholder;
- Exercises 7–12 remain placeholders;
- Exercise 13 remains absent;
- sidebar order is correct and the Syllabus page is unchanged.

### 9.2 Interactions

Exercise 4:

- every activity loads under the project subpath and updates both text and plots;
- the hidden-test activity follows the staged train/validation/test sequence;
- the nested-CV split diagram renders.

Exercise 5:

- Ridge/Lasso and parameter controls update coefficient and prediction plots;
- the moved feature-set comparison is present here and absent from Exercise 2.

Exercise 6:

- the clearer regression-tree labels/title and gray partition boundaries render;
- the noisy 16-participant greedy activity hides answers before Reveal and completes three rounds;
- the classification-depth figure shows development-only `n=753`, best depth 5, validation ROC
  AUC approximately 0.567, and excludes the 251-participant outer test;
- the ensemble activity has no seed selector, uses `MSE (years²)`, and updates plots;
- the fair-comparison table is visible while its code input is collapsed.

### 9.3 Links, themes, and layouts

- Exercise 4–6 Colab and download links resolve to their correct portable notebooks.
- Verify all Exercise 4–6 activities in light mode and in book-controlled dark mode under a light
  OS preference.
- Reload Exercise 6 while dark mode is already active and verify correct first paint.
- Confirm Plotly drag layers are transparent and do not obscure axes.
- Confirm important marks and text remain visible.
- Confirm no page-level horizontal overflow at a 390px viewport.
- Record new console errors separately from any already-known unrelated Thebe/theme-bootstrap
  messages.

Prefer existing production-capable Playwright checks. Any one-off verification script must live
only in a `mktemp -d` directory and be removed afterward. Do not commit new production tests in
this deployment correction.

## 10. Stop conditions

Stop without improvising on:

- unexpected Git state or ancestry;
- a semantic mismatch larger than the justified tolerance;
- structural artifact differences;
- failed/repeated local gate;
- merge conflict;
- failed push;
- missing workflow after two bounded queries;
- failed/cancelled workflow;
- stale or broken production after a successful workflow;
- interaction, dark-mode, layout, download, or runtime regression.

Do not make a second push or rerun the workflow.

## 11. Reports and final state

After production verification—or immediately after a stop condition—create:

- `WPs/reports/WP31R_REPORT.md`;
- `WPs/reports/WP31R_EXACT_CHANGELOG.md`.

The report must include:

- starting local/remote SHAs and ancestry;
- evidence confirming or rejecting the floating-point diagnosis;
- every differing JSON path and maximum absolute difference;
- the selected comparison tolerance and justification;
- exact implementation and focused regression tests;
- every local gate and result;
- `WP31R_RELEASE_SHA` and single push result;
- workflow run ID, discovery attempts, duration, and conclusion;
- every production URL and interaction/theme/layout/link check;
- deviations and anything requiring user attention;
- final `git status --short --branch`.

Commit only these two reports locally on `main` after the deployment attempt and record that commit
as `WP31R_DOCUMENTATION_SHA`. Do not push it, because that would trigger another deployment.

The intended successful final state is:

- `origin/main` at `WP31R_RELEASE_SHA` with a successful deployment workflow;
- production updated to the Exercises 4–6 release;
- local `main` exactly one documentation-only commit ahead at `WP31R_DOCUMENTATION_SHA`;
- only the two whitelisted legacy reports remain untracked;
- no WP32 started.
