# WP31R3 — Chapter 1 Dark-Mode Test Stability and Redeployment

## Purpose

Fix the final CI blocker preventing deployment of Exercises 4–6.

WP31R2 successfully corrected the missing Mermaid dependency: GitHub Actions run `35510061137`
passed the Jupyter Book build. The workflow then failed later because one test in
`chapter01-dark-mode.spec.ts` timed out in `waitForRendered`; 85 of the 86 built-book Playwright
tests passed. The publish step did not run, so production remains unchanged.

This WP must reproduce and diagnose that failure under realistic full-suite load, replace any
timing assumption with a state-based readiness condition while preserving all visual assertions,
run the complete built-book suite locally, and make one bounded deployment attempt.

Do not change lesson content, data, model results, or visual acceptance thresholds.

## 1. Expected starting state and Git safety

Expected remote state:

- `origin/main` at WP31R2 release commit `f12967b` (resolve and record the full SHA);
- workflow run `35510061137` failed only at the built-book Playwright step;
- the Jupyter Book build and earlier CI steps passed;
- production was not published.

Expected local state:

- local `main` at documentation commit `8e2a827`, exactly one documentation-only commit ahead of
  `origin/main`;
- that commit contains only `WP31R2_REPORT.md` and `WP31R2_EXACT_CHANGELOG.md`;
- the only permitted untracked files are:
  - `WPs/reports/WP16_ARCHITECT_REPORT.md`;
  - `WPs/reports/WP21_DEPLOYMENT_REPORT.md`;
  - this WP31R3 specification before its checkpoint commit.

Procedure:

1. Start on local `main`; record its full SHA and `git status --short --branch`.
2. Run one `git fetch origin main`; confirm the remote SHA and expected one-commit local
   divergence.
3. Stop on any unexpected state. Do not pull, reset, rebase, stash, delete, overwrite, or
   force-push.
4. Create `fix/wp31r3-chapter01-dark-mode-stability` from local `main`.
5. Save this specification as `WPs/WP31R3_CHAPTER01_DARK_MODE_STABILITY_AND_REDEPLOY.md` and commit
   it as the first checkpoint before implementation changes.
6. Leave the two legacy reports untouched and untracked.

## 2. Diagnose the exact failure

Inspect:

- the failed logs, trace, attachments, screenshots, and Playwright error context from run
  `35510061137`;
- `interactive/e2e-book/chapter01-dark-mode.spec.ts`, especially line 121 and
  `waitForRendered`;
- the relevant Chapter 1 widget component and its render-ready mechanism;
- the Playwright book configuration, worker count, timeouts, web server, and iframe-loading logic;
- state-based waiting helpers already proven elsewhere in the repository, including the hardened
  Exercise 5 geometry helper and cross-chapter dark-mode tests.

Record:

1. which Chapter 1 widget and plot timed out;
2. what exact condition `waitForRendered` awaited;
3. whether the iframe loaded, the widget initialized, and Plotly eventually rendered;
4. whether the failure indicates a product defect or a test readiness race;
5. whether the helper waits for a one-time event/counter that can be missed or delayed under
   parallel load;
6. the duration and worker/load context of the failed CI test.

Do not assume “flaky test” merely because 85 other tests passed. If evidence indicates a product
defect, correct the product narrowly and report it. If evidence is insufficient, stop rather than
masking the failure.

## 3. Reproduce before editing

Build the frontend and Jupyter Book once, then run:

1. the single failed Chapter 1 test in isolation;
2. the complete `chapter01-dark-mode.spec.ts` file;
3. that spec with the repository's normal built-book worker setting and `--repeat-each=3`;
4. the entire built-book Playwright suite once with its normal CI configuration.

The purpose is to distinguish an isolated product failure from a load-dependent readiness race.
Do not alter global retries or timeouts to obtain a passing baseline. If the full suite already
passes locally, that is useful evidence but does not eliminate the CI trace; continue with a
state-based correction if the trace shows the helper is intrinsically race-prone.

## 4. Correct the readiness logic without weakening the test

If the failure is a readiness race, update the narrowest shared or local helper so the test waits
for observable completed state rather than elapsed time or a fragile intermediate event.

The corrected wait should, as applicable:

- wait for the target iframe document and widget root to exist;
- wait for the expected Plotly graph element(s) to exist;
- verify Plotly has populated `_fullLayout` and `_fullData`;
- verify the component's rendered/data-ready marker is present and valid;
- require the graph bounding box to be non-zero;
- when geometry or theme assertions follow, wait for relevant bounding boxes/theme values to
  remain stable across consecutive animation frames;
- provide a clear diagnostic message identifying which readiness condition failed.

Preserve every substantive assertion in `chapter01-dark-mode.spec.ts`, including:

- the book-controlled dark theme reaches the iframe;
- paper/plot/card backgrounds have the expected dark palette;
- axes, gridlines, data marks, and text remain visible;
- drag layers remain transparent and do not obscure axes;
- refresh/first-paint behavior remains correct where currently tested.

Forbidden fixes:

- arbitrary `waitForTimeout`/sleep;
- merely increasing the global test or assertion timeout;
- adding retries;
- `.skip`, `.fixme`, conditional bypasses, or deleting the failing assertion;
- lowering color, geometry, visibility, or layout thresholds;
- reducing the worker count only to hide the race;
- changing production visuals solely to make the test easier.

Prefer reusing an existing proven helper if its semantics fit. Avoid duplicating subtly different
readiness implementations across specs.

## 5. Focused regression coverage

Add or update tests/helpers so they prove:

1. the wait does not resolve before the iframe/widget exists;
2. it does not resolve when Plotly exists but `_fullLayout`/`_fullData` are incomplete;
3. it resolves after the completed render state is observable;
4. it still times out with a useful condition-specific message when rendering genuinely fails;
5. all original Chapter 1 dark-mode assertions still execute;
6. no global retry, timeout, threshold, or worker setting was weakened.

Do not add a synthetic test framework solely for the helper if the same behavior can be exercised
through the real Chapter 1 page.

## 6. Required bounded local validation

After the correction, rebuild only what changed and run these gates once unless a stress count is
explicitly stated:

1. the previously failing test in isolation;
2. full `chapter01-dark-mode.spec.ts`;
3. that file at normal workers with `--repeat-each=5`;
4. the complete built-book Playwright suite at the same configuration used by CI — all 86 or more
   tests must pass;
5. cross-chapter dark-mode tests;
6. Chapter 1 built-book tests;
7. focused Exercises 4–6 built-book tests;
8. full frontend unit-test suite and typecheck if frontend source/helper code changed;
9. one production frontend build if frontend inputs changed;
10. full offline Python test suite;
11. Mermaid dependency-contract test and `import sphinxcontrib.mermaid`;
12. portable-notebook deterministic check for all chapters;
13. one clean Jupyter Book build and check for execution-error logs.

Run the complete built-book suite locally even if every focused test passes; this is the coverage
gap explicitly identified by WP31R2.

If a gate fails because of this WP, make one focused correction and rerun only that failed gate
once. Stop on an unrelated or repeated failure. Do not use sleeps, retries, weakened assertions,
or repeated open-ended stress loops.

## 7. Merge into local `main`

Only after all gates pass:

1. Switch to local `main` and reconfirm its SHA/status.
2. Merge with one non-fast-forward merge commit:

   ```bash
   git merge --no-ff fix/wp31r3-chapter01-dark-mode-stability -m "Stabilize Chapter 1 dark-mode rendering test"
   ```

3. Stop on conflict; do not resolve automatically.
4. Record the merge commit as `WP31R3_RELEASE_SHA`.
5. Prove the merged `main` tree is identical to the correction branch.
6. Confirm the diff from WP31R2's release contains only:
   - the previously local WP31R2 reports;
   - this WP31R3 specification;
   - the narrow readiness/test correction and strictly necessary related helper documentation.

Do not amend, squash, rebase, or rewrite history.

## 8. Push exactly once

After merge verification:

```bash
git push origin main
```

- Perform exactly one push.
- If it fails, stop. Do not retry, pull, rebase, or force-push.
- Verify with one read-only remote query that `origin/main` equals `WP31R3_RELEASE_SHA`.

## 9. Monitor one workflow run

1. Query once for the deployment run whose `headSha` equals `WP31R3_RELEASE_SHA`.
2. If absent, wait no more than 30 seconds and query once more.
3. If still absent, stop.
4. Run exactly one continuous:

   ```bash
   gh run watch RUN_ID --exit-status
   ```

5. Set the calling tool's timeout to at least 20 minutes before starting the watch so the local
   tool does not terminate it prematurely.
6. Do not run a background watcher, scheduled wakeup, parallel poll, second watch, or workflow
   rerun.

If the workflow fails, retrieve failed logs once, document them, and stop. Do not fix and push
again within WP31R3.

## 10. Production verification after workflow success

Use a fresh browser context and cache-busting query string against:

`https://yoavmp.github.io/ml-neuro-tutorials/`

### 10.1 Structure

Verify:

- Exercises 1–3 still load correctly;
- Exercise 4 is **Validation and Cross-Validation**;
- Exercise 5 is **Regularization and Feature Selection**;
- Exercise 6 is **Decision Trees**;
- Exercises 7–12 remain placeholders;
- Exercise 13 remains absent;
- sidebar order is correct and Syllabus remains unchanged.

### 10.2 Exercise 4

- Every activity loads under the deployed project subpath and updates text and plots.
- The hidden-test activity follows its train/validation/test sequence.
- The nested-CV diagram renders rather than showing raw Mermaid text.
- Colab and download links resolve.

### 10.3 Exercise 5

- Ridge/Lasso and parameter controls update coefficient and prediction plots.
- The moved feature-set comparison is present here and absent from Exercise 2.
- Colab and download links resolve.

### 10.4 Exercise 6

- The tree diagram uses the shortened labels, `Mean age`, `Predicted age`, and intended title.
- Gray hierarchical partition boundaries render.
- The 16-participant greedy activity hides answers before Reveal and completes all rounds.
- The classification-depth figure shows development-only `n=753`, best depth 5, validation ROC
  AUC approximately 0.567, with the 251-participant test partition excluded.
- The ensemble activity has no seed selector, uses `MSE (years²)`, and updates its plots.
- The fair-comparison table is visible while code input is collapsed.
- Colab and download links resolve.

### 10.5 Theme, runtime, and layout

- Verify Chapter 1's dark-mode behavior that caused the CI failure.
- Verify every Exercise 4–6 activity in light and book-controlled dark mode under a light OS
  preference.
- Reload Exercise 6 while dark mode is active and verify correct first paint.
- Confirm Plotly drag layers remain transparent and do not obscure axes.
- Confirm data marks, labels, and controls remain visible.
- Confirm no page-level horizontal overflow at 390px.
- Record new console errors separately from previously documented unrelated Thebe/theme-bootstrap
  messages.

Prefer existing production-capable Playwright checks. Temporary scripts must live only in a
`mktemp -d` directory and be removed afterward. Do not commit new production-test infrastructure
in this deployment correction.

## 11. Stop conditions

Stop without improvising on:

- unexpected Git state;
- evidence of a product defect outside this WP;
- failed or repeated local gate;
- merge conflict;
- failed push;
- no matching workflow after two bounded queries;
- failed/cancelled workflow;
- stale/broken production after workflow success;
- interaction, Mermaid, theme, layout, download, or runtime regression.

Do not make a second push or rerun the workflow.

## 12. Reports and final state

After successful production verification—or immediately after a stop condition—create:

- `WPs/reports/WP31R3_REPORT.md`;
- `WPs/reports/WP31R3_EXACT_CHANGELOG.md`.

The report must include:

- starting local/remote SHAs and ancestry;
- failed CI test, trace, widget, and exact readiness condition;
- reproduction matrix before and after correction;
- root cause and why the correction is state-based rather than a timeout increase;
- exact assertions preserved;
- every local gate and result, including the complete built-book suite;
- `WP31R3_RELEASE_SHA` and single push result;
- workflow run ID, discovery attempts, duration, step results, and conclusion;
- every production URL and interaction/theme/layout/link check;
- deviations and anything requiring user attention;
- final `git status --short --branch`.

Commit only these two reports locally on `main` after the deployment attempt and record that commit
as `WP31R3_DOCUMENTATION_SHA`. Do not push it.

The intended successful final state is:

- `origin/main` at `WP31R3_RELEASE_SHA` with a successful workflow;
- production updated with Exercises 4–6;
- local `main` exactly one documentation-only commit ahead at `WP31R3_DOCUMENTATION_SHA`;
- only the two whitelisted legacy reports remain untracked;
- no WP32 started.
