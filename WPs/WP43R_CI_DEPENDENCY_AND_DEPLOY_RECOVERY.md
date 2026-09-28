# WP43R — Fix clean-CI dependency and finish JupyterLite deployment

## Authority and goal

The course author already authorized deployment of JupyterLite Exercises 1 and 2 in WP43. WP43 pushed `main` once, but the triggered GitHub Actions run failed before publication because its clean Python environment lacked `ipywidgets`. This focused recovery continues that authorized deployment. Do not change lesson content or migrate another exercise. Do not treat the pushed GitHub source as proof of a live site.

Read `WPs/reports/WP43_REPORT.md`, `WPs/reports/WP43_EXACT_CHANGELOG.md`, the WP42 report, and the WP41 maintainer guide. Current reported state (verify it): `origin/main` at `7d0f9d3c4a9cdaab1fba8041632c817d195ca05f`, live `gh-pages` still at `f6ddfc28e5102d44f94dc5dc86ba9875ad36db8a` (`deploy: 58ed1c6…`); WP43 reports were committed on local `main` after the push and remain unpushed. Failed workflow: `https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/36410198395`, at the offline Python unit-test step with `ModuleNotFoundError: No module named 'ipywidgets'`. These are historical observations, not assumptions about the machine now.

## Gate A — Safe state and dependency diagnosis

Record current branch, `git status --short --branch`, recent log, local and remote `main`, `gh-pages`, and active workflow runs. Fetch remote refs read-only. Confirm exactly what the local unpublished report commit contains and preserve it. Confirm `Homework_Materials/` remains excluded without reading, staging, or uploading it. Preserve checkpoint refs for both the current local `main` and current production state. Stop on unexplained changes, nontrivial divergence, or another deployment in progress; do not reset, stash, force-push, or overwrite unrelated work.

Inspect `requirements.txt`, `requirements-lite.txt`, CI Python version, the two reference-execution tests, and the notebook setup cells. Add the missing standard-Jupyter runtime dependency to the appropriate pinned requirements file used by clean CI and local Jupyter; `ipywidgets==8.1.9` was observed in the developer venv, but verify compatibility with the repository's pinned stack rather than assuming that exact version is mandatory. Keep JupyterLite's browser-specific `micropip` behavior intact. Do not add a student-facing installation step or `pip install -r requirements.txt` to the notebooks.

## Gate B — Reproduce in a genuinely clean environment

Create an isolated fresh environment matching the workflow's Python version and install only the exact requirements the workflow installs. Do not use the long-lived project `.venv` to claim this gate passed. Run the full offline Python suite; verify both Exercise 1 and Exercise 2 reference notebooks import `ipywidgets` and execute their numeric-integrity tests. If another genuine missing dependency appears, add only the required pinned dependency, diagnose once, and rerun this gate once. If still failing, stop before a push and report. Check dependency resolution and the existing generated notebook/manifest checks.

Validate the actual workflow configuration and locally build the combined Book + Lite site as needed to ensure no changed dependency breaks the JupyterLite step. Preserve Exercise 1's 1114×13 and Exercise 2's 1004×360 data and established results. WP43 already passed 149/149 browser tests against the combined build; rerun focused browser checks only if this correction affects browser packaging, and do not repeatedly spend minutes on an unchanged full suite. Verify the course-toolbar build remains present in the fresh workflow path. Include the previously unpushed WP43 report commit in the normal next push if Git ancestry is clean.

## Gate C — One controlled recovery push and workflow

After Gates A–B pass, commit the dependency fix locally with a clear message. Inspect the exact diff and ancestry against `origin/main`. Push `main` normally once; never force-push. Observe the single triggered workflow with a realistic bound of about 35 minutes (the prior successful workflow took about 19 minutes). Avoid rapid polling and do not rerun a failed workflow or push an additional speculative fix in this WP. If the workflow fails at another step, capture the exact log and stop with production state unchanged or clearly described.

If the workflow succeeds, confirm the `gh-pages` deployment commit corresponds to the new `main` SHA. Verify the live site in a clean browser under `https://yoavmp.github.io/ml-neuro-tutorials/`: Contents → Exercise 1 and Exercise 2 transition pages → JupyterLite working copies; direct Lite URLs; kernel startup and same-origin data; one supplied-code result, native widget, and checked question in each notebook; edit/save/reload/download-current-work, Reset warning, Back to Contents; current portable downloads and private-repository-safe Colab upload instructions; at least one unchanged legacy exercise; the project subpath and a mobile-width view. Use a separate clean profile so instructor browser work is untouched. Note the one-time cold load and any genuine browser/network error. Do not claim live verification from CI alone.

## Reports and stop

Write `WPs/reports/WP43R_REPORT.md` and `WPs/reports/WP43R_EXACT_CHANGELOG.md` with start/final SHAs, exact dependency change and clean-environment proof, test/build results, workflow run URL/status, `gh-pages` SHA, live links and observed behavior, deviations, and whether anything was pushed/deployed. Avoid a separate report-only push that would trigger another deployment; reports may remain committed locally for a later authorized update. Return a short course-author summary with live links if successful, or the exact blocker and current production state if not. Do not start another WP.
