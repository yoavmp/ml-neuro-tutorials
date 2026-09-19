# WP31 — Deploy Exercises 4–6

## Purpose

Deploy the accumulated, locally reviewed course-book work from WP27 through WP30R so the latest
versions can be reviewed on GitHub Pages.

This WP is deployment-only. It must not redesign, edit, regenerate, or otherwise change notebook,
widget, data, test, configuration, or build-workflow content unless the task explicitly says to
write the WP31 specification or final deployment reports.

The release should make these completed notebooks live:

- Exercise 4: **Validation and Cross-Validation**;
- Exercise 5: **Regularization and Feature Selection**;
- Exercise 6: **Decision Trees**.

Exercises 1–3 must remain intact, and Exercises 7–12 must remain placeholders.

## 1. Expected starting state

Start from `fix/wp30r-classification-holdout`, whose reported implementation/report commit is
`3436307`. Treat that abbreviated SHA as a hint only; record and use the actual full SHA.

Expected history from the previous release:

- `origin/main` was last reported at release commit `44739b3`;
- local `main` was last reported as one documentation-only commit ahead of `origin/main`, with
  abbreviated SHA `74c9a9a`;
- the WP27–WP30R branch chain should descend from that local `main`;
- the only permitted pre-existing untracked files are:
  - `WPs/reports/WP16_ARCHITECT_REPORT.md`;
  - `WPs/reports/WP21_DEPLOYMENT_REPORT.md`;
  - this WP31 specification, before its checkpoint commit.

Do not assume these statements are still true. Verify them.

## 2. Save the deployment specification first

1. Verify the current branch, full HEAD, and `git status --short --branch`.
2. Stop if any unexpected modified or untracked file exists. Do not reset, stash, delete, or
   overwrite it.
3. Save this specification as `WPs/WP31_DEPLOY_EXERCISES_4_TO_6.md` on
   `fix/wp30r-classification-holdout`.
4. Commit only this specification as a deployment checkpoint before running release gates.
5. Record that checkpoint SHA.

Do not add or alter either whitelisted legacy untracked report.

## 3. Verify local and remote ancestry before testing or merging

Run `git fetch origin main` once, then verify all of the following:

1. `origin/main` is still the expected previously deployed release (`44739b3...`).
2. Local `main` is exactly one documentation-only commit ahead of `origin/main`, corresponding to
   the reported WP26R documentation commit (`74c9a9a...`).
3. The diff from `origin/main` to local `main` contains documentation only.
4. `origin/main` is an ancestor of local `main`.
5. Local `main` is an ancestor of the current WP31 checkpoint on
   `fix/wp30r-classification-holdout`.
6. The current branch contains the complete linear WP27 → WP27R → WP28 → WP29 → WP30 → WP30R
   work and its reports.
7. No unrelated commit or file is present in `main..fix/wp30r-classification-holdout`.

Capture the relevant `git log --graph --oneline --decorate`, ancestry checks, and diff summaries
in the final report.

If `origin/main` advanced, local `main` differs from the expected documentation-only state, the
feature branch does not descend from local `main`, or any unexpected content appears: **stop**.
Do not pull, rebase, reset, cherry-pick, stash, merge, or resolve the divergence automatically.

## 4. Bounded pre-deployment validation

Run the following against the WP31 checkpoint branch before merging. Run each gate once. If a
gate fails, stop and report the failure; do not fix implementation inside this deployment WP.

1. Run all committed audit/export check modes needed by Exercises 4–6, without refreshing or
   rewriting their artifacts.
2. Run portable-notebook deterministic checks for all implemented chapters.
3. Run the repository's registered portable smoke test once.
4. Independently smoke-execute the Exercise 5 and Exercise 6 portable notebooks in fresh temporary
   directories if they are still absent from the registered smoke script. Do not modify that
   script in this WP.
5. Run the full offline Python test suite once.
6. Run frontend typecheck once.
7. Run the full frontend unit-test suite once.
8. Run one production frontend build.
9. Run one clean Jupyter Book build.
10. Run the focused built-book tests for Exercises 4, 5, and 6.
11. Run launch-button tests.
12. Run cross-chapter light/dark-mode tests, including Exercises 4–6.
13. Run narrow-viewport checks for the new activities.

Do not run redundant repeated stress suites. The previous WPs already ran their full standalone
and built-book Playwright suites. If the repository's actual deployment workflow contains an
additional mandatory offline gate not listed above, reproduce that gate once and document it.

Do not use arbitrary sleeps, weakened assertions, skipped tests, global retries, or repeated
build loops.

## 5. Merge into local `main`

Only after every pre-deployment gate passes:

1. Switch to local `main`.
2. Reconfirm its SHA and clean state apart from the two whitelisted untracked reports.
3. Merge `fix/wp30r-classification-holdout` with a single non-fast-forward merge commit:

   ```bash
   git merge --no-ff fix/wp30r-classification-holdout -m "Merge Exercises 4-6 course materials"
   ```

4. If any conflict occurs, stop. Do not resolve it automatically.
5. Record the merge commit as `RELEASE_SHA`.
6. Prove that the merged `main` tree is identical to the WP31 checkpoint branch tree, excluding
   Git history/parentage. If there is a content difference, stop before pushing.
7. Confirm the only untracked files remain the two whitelisted legacy reports.

Do not amend, squash, rebase, or rewrite the accumulated WP history.

## 6. Push exactly once

After the merge checks pass:

```bash
git push origin main
```

- Perform exactly one push in this WP.
- If the push is rejected or fails, stop. Do not pull, force-push, rebase, retry, or make a second
  push.
- After success, verify with a read-only remote query that `origin/main` points to `RELEASE_SHA`.

## 7. Monitor exactly one deployment workflow run

Identify the GitHub Actions deployment run triggered by `RELEASE_SHA`.

Bound the process to avoid the polling loops seen in earlier deployment work:

1. Query once for a workflow run associated with `RELEASE_SHA`.
2. If it is not visible yet, wait no more than 30 seconds and query one final time.
3. If it is still absent, stop and report that no run was discovered. Do not keep polling.
4. Once found, record the run ID and invoke one continuous:

   ```bash
   gh run watch RUN_ID --exit-status
   ```

5. Do not start a background watch, schedule wakeups, poll in parallel, or launch another watcher.
6. Do not rerun a failed or cancelled workflow.

If the workflow fails, stop. Record its failing job/step and relevant log excerpt. Do not change
code, push again, or attempt a repair under WP31.

## 8. Production verification

Perform this section only if the workflow succeeds. Verify the deployed site, not localhost, at:

`https://yoavmp.github.io/ml-neuro-tutorials/`

Use a fresh browser context or cache-busting query string so cached HTML/assets cannot masquerade
as the new release.

### 8.1 Page and navigation checks

Verify HTTP success, rendered title, sidebar order, and expected content for:

- `/chapters/chapter_01/exercise_01.html` — Exercise 1 unchanged;
- `/chapters/chapter_02/exercise_02.html` — Regression and Bias-Variance Trade-Off;
- `/chapters/chapter_03/exercise_03.html` — Classification and Metrics;
- `/chapters/chapter_04/exercise_04.html` — Validation and Cross-Validation, no longer a
  placeholder;
- `/chapters/chapter_05/exercise_05.html` — Regularization and Feature Selection, no longer a
  placeholder;
- `/chapters/chapter_06/exercise_06.html` — Decision Trees, no longer a placeholder;
- Exercises 7–12 remain placeholder pages;
- Exercise 13 remains absent;
- the Syllabus page remains unchanged.

### 8.2 Exercise 4 checks

Confirm that:

- all Exercise 4 interactive activities load under the deployed project subpath;
- controls update their plots and displayed metrics;
- the hidden-test activity shows training, validation, and locked test MSE in the intended staged
  sequence;
- the nested-CV split diagram renders correctly;
- the Colab and download links resolve to the Exercise 4 portable notebook.

### 8.3 Exercise 5 checks

Confirm that:

- the regularization activity loads and responds to Ridge/Lasso and parameter controls;
- coefficient and prediction plots update rather than only changing text;
- moved feature-set material is present in Exercise 5 and absent from its old Exercise 2 location;
- the Colab and download links resolve to the Exercise 5 portable notebook.

### 8.4 Exercise 6 checks

Confirm that:

- the tree diagram uses `Left 3a thickness` and `Right area 2 thickness`, internal `Mean age`,
  leaf `Predicted age`, and the title `Resulting Regression Tree`;
- the 2D partition plot has visible gray hierarchical boundary segments;
- the greedy-tree activity uses the overlapping 16-participant simulated dataset, hides the
  answer before Reveal, preserves earlier accepted splits, and reaches all three rounds;
- only one reflection set appears for each activity;
- the regression complexity curve remains present;
- the classification curve is present with the corrected development-only result
  (`n=753`, best depth 5, validation ROC AUC approximately 0.567) and explicitly excludes the
  251-participant outer test;
- “One Tree or Many?” has no seed/replicate selector, uses `MSE (years²)`, and its controls update
  the plots;
- the fair-comparison table is visible while its code input is collapsed;
- the Colab and download links resolve to the Exercise 6 portable notebook.

### 8.5 Theme, layout, and runtime checks

For every interactive activity in Exercises 4–6:

- verify light mode;
- switch the book itself to dark mode under a light OS preference and verify the iframe/Plotly
  theme follows correctly;
- reload at least one Exercise 6 page while dark mode is already active and confirm correct first
  paint;
- verify Plotly drag layers remain transparent and do not cover axis titles;
- verify important marks, lines, labels, and controls remain visible;
- verify a 390px viewport has no page-level horizontal overflow;
- record new console errors and distinguish them from any already-documented, unrelated Thebe or
  theme-bootstrap messages.

Prefer existing production-capable Playwright checks. If a temporary verification script is
needed, create it only inside a `mktemp -d` directory and remove that temporary directory after
use. Do not add new production code or committed tests in this deployment WP.

## 9. Stop conditions

Stop immediately and do not improvise if any of these occurs:

- unexpected Git divergence or files;
- failed pre-deployment gate;
- merge conflict;
- failed/rejected push;
- no discoverable workflow after the two bounded queries;
- failed/cancelled workflow;
- production serves stale or broken content after a successful workflow;
- an interactive activity fails to update its plot;
- a material dark-mode, narrow-layout, download, or runtime regression appears.

Do not make a second push or workflow rerun. Document the exact blocker for a separate correction
WP.

## 10. Deployment reports

After successful production verification—or immediately after any stop condition—create:

- `WPs/reports/WP31_DEPLOYMENT_REPORT.md`
- `WPs/reports/WP31_EXACT_CHANGELOG.md`

The report must include:

- starting feature-branch SHA and WP31 checkpoint SHA;
- verified starting `main` and `origin/main` SHAs;
- ancestry/diff evidence;
- every pre-deployment command and result;
- `RELEASE_SHA`;
- the single push result;
- GitHub Actions run ID, discovery attempts, duration, and conclusion;
- every live URL checked and the result;
- interaction, theme, viewport, console, Colab, and download verification;
- all deviations and anything requiring user attention;
- final `git status --short --branch`.

Commit only these two reports locally on `main` after the deployment attempt. Record that commit
as `DOCUMENTATION_SHA`. Do **not** push it, because doing so would trigger a second deployment.

The intended final successful state is:

- `origin/main` at `RELEASE_SHA`;
- local `main` exactly one documentation-only commit ahead at `DOCUMENTATION_SHA`;
- the two whitelisted legacy reports still untracked and untouched;
- no WP32 started.
