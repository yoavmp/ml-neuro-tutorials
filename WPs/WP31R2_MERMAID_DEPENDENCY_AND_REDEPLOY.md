# WP31R2 — Mermaid Dependency Correction and Redeployment

## Purpose

Correct the second CI-environment gap exposed by the Exercises 4–6 deployment and complete the
deployment.

WP31R successfully fixed the cross-platform floating-point test: the complete offline Python test
step passed in GitHub Actions run `35469646309`. That run then failed later while building the
Jupyter Book because the CI environment could not import `sphinxcontrib.mermaid`. The live site
was not published and remains on the pre-Exercises-4–6 release.

This WP must diagnose the dependency path, add the narrowly required pinned dependency to the
environment actually installed by CI, verify the book in a fresh environment, push once, monitor
one workflow run, and verify the production site.

Do not change notebook, widget, dataset, model, or lesson content.

## 1. Expected Git state and safety

Expected remote state:

- `origin/main` at WP31R release commit
  `de564b3dccedfc92eb14f6460efd4ffb459d4c5e`;
- GitHub Actions run `35469646309` failed at **Build Jupyter Book** with
  `ModuleNotFoundError: No module named 'sphinxcontrib.mermaid'`;
- production `gh-pages` was not updated.

Expected local state:

- local `main` is exactly one WP31R documentation-only commit ahead of `origin/main`;
- that local commit contains only `WPs/reports/WP31R_REPORT.md` and
  `WPs/reports/WP31R_EXACT_CHANGELOG.md`;
- the only permitted untracked files are:
  - `WPs/reports/WP16_ARCHITECT_REPORT.md`;
  - `WPs/reports/WP21_DEPLOYMENT_REPORT.md`;
  - this WP31R2 specification before its checkpoint commit.

Procedure:

1. Start on local `main` and record its actual full SHA and status.
2. Run one `git fetch origin main`; confirm `origin/main` remains exactly at the WP31R release SHA.
3. Prove local `main` differs from `origin/main` only by the expected documentation commit/files.
4. Stop on any unexpected state. Do not pull, reset, rebase, stash, delete, overwrite, or
   force-push.
5. Create branch `fix/wp31r2-mermaid-dependency` from local `main`.
6. Save this specification as `WPs/WP31R2_MERMAID_DEPENDENCY_AND_REDEPLOY.md` and commit it as the
   first checkpoint before implementation changes.
7. Leave both whitelisted legacy reports untouched and untracked.

## 2. Confirm the dependency diagnosis

Before editing files, inspect and record:

- the failed step and complete relevant traceback from workflow run `35469646309`;
- `.github/workflows/deploy.yml`, including its Python version and dependency-install commands;
- every repository requirements/constraints/lock file used by that workflow;
- `book/_config.yml`, including the exact Mermaid extension entry;
- the currently working local environment's distribution name and version using both:
  - `python -m pip show sphinxcontrib-mermaid`;
  - `python -c "import importlib.metadata as m; print(m.version('sphinxcontrib-mermaid'))"`;
- `python -c "import sphinxcontrib.mermaid; print(sphinxcontrib.mermaid.__file__)"`;
- whether the package is currently direct, transitive, or absent from the repository's pinned
  dependency definition.

Confirm that:

1. `book/_config.yml` intentionally enables `sphinxcontrib.mermaid`;
2. local builds succeed because the package exists in the local `.venv`;
3. the GitHub Actions install path does not install it;
4. no different missing import or configuration error precedes it.

If this diagnosis is false or incomplete, stop and report the evidence rather than applying the
assumed fix.

## 3. Add the narrow pinned dependency

Add the distribution `sphinxcontrib-mermaid` to the pinned dependency file that
`.github/workflows/deploy.yml` actually installs.

- Pin an exact version proven by the working local environment whenever that version supports the
  workflow's Python version.
- Confirm compatibility with CI's Python version from `deploy.yml` before pinning.
- Follow the existing requirements file's naming, ordering, comments, and pin style.
- Do not add a second ad hoc `pip install` command to the workflow if the project already installs
  a canonical requirements file.
- Do not upgrade Jupyter Book, Sphinx, MyST, Mermaid, or unrelated packages.
- Do not remove the Mermaid extension from the book configuration; the nested-CV diagram and any
  other Mermaid content must remain supported.

If the locally installed version is not compatible with the CI Python version, choose the closest
documented compatible version and explain the evidence in the report. Do not select an unpinned
latest version merely to make CI pass.

## 4. Add a durable dependency-contract test

Add one focused offline test that prevents the same omission from recurring.

The test should:

1. parse the relevant Mermaid extension declaration from `book/_config.yml`;
2. confirm that enabling `sphinxcontrib.mermaid` requires the distribution
   `sphinxcontrib-mermaid`;
3. confirm that this distribution appears with an exact version pin in the canonical requirements
   file installed by CI;
4. provide a clear failure message naming the missing extension and dependency.

Keep the test narrow. Do not attempt to create a universal import-to-PyPI dependency resolver.

## 5. Fresh-environment reproduction

Do not rely only on the existing `.venv`, because that environment already contains the missing
package.

Create a disposable virtual environment inside a `mktemp -d` directory using the closest locally
available Python version to CI's configured version. Then:

1. install dependencies using the same requirements command as `deploy.yml`;
2. print the installed versions of Jupyter Book, Sphinx, and `sphinxcontrib-mermaid`;
3. import `sphinxcontrib.mermaid` explicitly;
4. run the full offline Python test suite;
5. build the Jupyter Book using the same build command as CI;
6. confirm no notebook execution-error logs exist;
7. remove the temporary environment afterward.

If the exact CI Python version is unavailable locally, document that deviation; the fresh
environment is still required with the closest available version. Do not install another system
Python solely for this WP.

If dependency installation cannot run because of an incidental network restriction, stop and
report it rather than falling back silently to the existing `.venv`.

## 6. Additional bounded local validation

After the fresh-environment gate passes, run the following once in the normal project environment:

1. focused dependency-contract test;
2. full offline Python test suite;
3. `python scripts/export_tree_greedy_widget.py --check` to retain coverage of WP31R's fix;
4. portable-notebook deterministic check for all chapters;
5. registered portable smoke test;
6. independent Exercise 5 and Exercise 6 portable smoke execution if they remain unregistered;
7. one clean Jupyter Book build;
8. focused built-book tests for Exercises 4–6;
9. launch-button tests;
10. cross-chapter dark-mode tests.

Frontend typecheck, frontend unit tests, and a frontend production rebuild are unnecessary if no
frontend file changes. Confirm and document that condition rather than rerunning unrelated gates.

Run each gate once. If this WP causes a failure, make one focused correction and rerun only that
failed gate once. Stop on an unrelated or repeated failure. Do not use skips, weakened assertions,
arbitrary sleeps, global retries, or repeated stress loops.

## 7. Merge into local `main`

Only after every required gate passes:

1. Switch to local `main`.
2. Reconfirm it remains at the verified starting SHA and is clean apart from the two whitelisted
   reports.
3. Merge with one non-fast-forward merge commit:

   ```bash
   git merge --no-ff fix/wp31r2-mermaid-dependency -m "Pin Mermaid dependency for CI book builds"
   ```

4. Stop on any conflict; do not resolve it automatically.
5. Record the merge commit as `WP31R2_RELEASE_SHA`.
6. Prove the merged `main` tree is identical to the correction branch tree.
7. Confirm the diff from WP31R's release contains only:
   - the previously local WP31R reports;
   - this WP31R2 specification;
   - the pinned dependency and focused dependency-contract test;
   - any strictly necessary small documentation comment.

Do not amend, squash, rebase, or rewrite history.

## 8. Push exactly once

After merge verification:

```bash
git push origin main
```

- Perform exactly one push.
- If it fails or is rejected, stop. Do not retry, pull, rebase, or force-push.
- Verify with one read-only remote query that `origin/main` equals `WP31R2_RELEASE_SHA`.

## 9. Monitor exactly one workflow run

Identify the deployment workflow triggered by `WP31R2_RELEASE_SHA`:

1. Query once for the matching run.
2. If absent, wait at most 30 seconds and query once more.
3. If still absent, stop and report.
4. Verify the run's `headSha`.
5. Execute one continuous:

   ```bash
   gh run watch RUN_ID --exit-status
   ```

6. Configure the calling tool's timeout long enough for the complete workflow before starting the
   watch. Do not use a background watcher, scheduled wakeup, parallel polling, or second watch.
7. Do not rerun a failed workflow.

If the workflow fails, retrieve the failed log once, document it, and stop. Do not fix or push
again within WP31R2.

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
- sidebar order is correct;
- Syllabus remains unchanged.

### 10.2 Exercise 4

- All activities load under the project subpath and update both text and plots.
- The hidden-test activity follows its train/validation/test sequence.
- The nested-CV diagram renders rather than appearing as raw Mermaid text.
- Colab and download links resolve correctly.

### 10.3 Exercise 5

- Ridge/Lasso and parameter controls update coefficient and prediction plots.
- The moved feature-set comparison is present here and absent from Exercise 2.
- Colab and download links resolve correctly.

### 10.4 Exercise 6

- The regression tree has the shortened feature names, `Mean age`, `Predicted age`, and the
  intended title.
- Gray hierarchical partition boundaries are visible.
- The noisy 16-participant greedy activity hides answers before Reveal and completes all rounds.
- The classification-depth figure reports development-only `n=753`, best depth 5, validation ROC
  AUC approximately 0.567, with the 251-participant outer test excluded.
- The ensemble activity has no seed selector, uses `MSE (years²)`, and updates its plots.
- The fair-comparison table is visible while code input is collapsed.
- Colab and download links resolve correctly.

### 10.5 Themes, runtime, and layout

- Verify every Exercise 4–6 activity in light mode and book-controlled dark mode under a light OS
  preference.
- Reload Exercise 6 while dark mode is active and verify correct first paint.
- Confirm Plotly drag layers remain transparent and do not obscure axis titles.
- Confirm data marks, labels, and controls remain visible.
- Confirm no page-level horizontal overflow at 390px.
- Record new console errors separately from previously documented unrelated Thebe/theme-bootstrap
  messages.

Prefer existing production-capable Playwright checks. Any temporary verification script must be
created only inside `mktemp -d` and removed afterward. Do not commit production-test changes in
this deployment WP.

## 11. Stop conditions

Stop without improvising if any of these occurs:

- unexpected Git state or ancestry;
- diagnosis does not match the missing dependency;
- incompatible or unresolvable dependency version;
- failed/repeated local gate;
- merge conflict;
- failed push;
- no matching workflow after two bounded queries;
- failed/cancelled workflow;
- stale or broken production after a successful workflow;
- interaction, Mermaid rendering, theme, layout, download, or runtime regression.

Do not make a second push or rerun the workflow.

## 12. Reports and final state

After successful live verification—or immediately after a stop condition—create:

- `WPs/reports/WP31R2_REPORT.md`;
- `WPs/reports/WP31R2_EXACT_CHANGELOG.md`.

The report must include:

- starting local/remote SHAs and ancestry;
- CI traceback and confirmed dependency path;
- local working version and selected pin;
- exact requirements/workflow relationship;
- fresh-environment Python/package versions, commands, and results;
- every bounded local gate and result;
- `WP31R2_RELEASE_SHA` and the single push result;
- workflow run ID, discovery attempts, duration, step results, and conclusion;
- every production URL and interaction/theme/layout/link check;
- deviations and anything requiring user attention;
- final `git status --short --branch`.

Commit only the two reports locally on `main` after the deployment attempt and record that commit
as `WP31R2_DOCUMENTATION_SHA`. Do not push it, because that would trigger a second deployment.

The intended successful final state is:

- `origin/main` at `WP31R2_RELEASE_SHA` with a successful deployment workflow;
- production updated with Exercises 4–6;
- local `main` exactly one documentation-only commit ahead at `WP31R2_DOCUMENTATION_SHA`;
- only the two whitelisted legacy reports remain untracked;
- no WP32 started.
