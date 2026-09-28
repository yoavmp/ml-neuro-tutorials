# WP43 — Deploy JupyterLite Exercises 1 and 2

## Authority and outcome

The course author authorizes deployment of the reviewed WP41, WP41R, and WP42 work so students with the course-site link can open and use **Exercise 1** and **Exercise 2** as JupyterLite notebooks on GitHub Pages. The existing Jupyter Book hub and Exercises 3–10 must remain usable. This WP includes the necessary GitHub Actions build/test/publish wiring, safe integration, one production deployment, and verification of the live URLs. Do not begin another notebook migration or redesign teaching content.

Read the revised WP41 specification, `WPs/reports/WP41_REPORT.md`, `WPs/reports/WP41R_REPORT.md`, `WPs/reports/WP42_REPORT.md`, exact changelogs, and maintainer guide before acting. Follow repository instructions. Treat reports as historical: inspect current Git and hosting state rather than assuming their SHAs or branch positions still hold.

## Gate A — Git and production preflight

1. From the repository root, record current branch, `git status --short --branch`, recent log, local `main`, `origin/main`, the WP42 feature SHA, and the pre-WP41 production SHA. Fetch remote refs without changing the working tree. Check whether remote main advanced and whether the feature branch contains or diverges from it. Confirm a clean tree and that `Homework_Materials/` remains excluded without reading, staging, or uploading it. Preserve the exact current and production commits with local checkpoint refs before integration.
2. Inspect `.github/workflows/deploy.yml`, Pages artifact assembly, `.gitignore`, JupyterLite configuration, the exercise manifest, the transition pages, published asset paths, and how GitHub Pages' `/ml-neuro-tutorials/` project prefix is handled. Identify all build prerequisites, including the pinned JupyterLite requirements and the course-toolbar extension. Confirm source files and lockfiles are tracked, generated build output is ignored, and the workflow can create the same combined Book + Lite tree WP42 tested locally. Do not assume a local venv or built `book/_build/` is present in CI.
3. Check the status of the existing site and deploy workflow read-only. Record the current production URLs and behavior for hub, Exercise 1, Exercise 2, and at least one legacy exercise. Check that the WP42 portable copies, same-origin CSV assets, and reference attachments are part of the intended artifact. Verify that no student-facing migrated link depends on a public repository URL or local filesystem path.
4. If there are unexplained changes, nontrivial remote divergence, a missing secret/permission required by Pages, a deployment already running, or a risk of overwriting others' work, stop and report. Do not reset, stash, force-push, or resolve ambiguous history automatically.

## Gate B — Production build pipeline

Update the existing Pages workflow so that a fresh checkout, with explicitly installed pinned dependencies, builds Jupyter Book first and then JupyterLite into `book/_build/html/lite/`, and uploads **one combined** Pages artifact. Keep the hub and legacy static assets intact. Include the course-toolbar build and its exact Node dependencies if the source extension must be compiled in CI. Do not upload local caches, `Homework_Materials/`, raw unpublished data, or browser storage.

Add bounded CI checks appropriate to the deployment: generators `--check`, manifest/data checks, key Python structural and numerical tests, and real browser navigation/execution smoke checks for both migrated notebooks against the actual combined build where CI resources allow. At minimum, CI must fail if either Contents/transition link cannot open its JupyterLite working copy, either notebook cannot load its same-origin data and run supplied code, the current-work download fails, or a legacy exercise route disappears. Do not make the Pages upload run before the combined build and essential checks pass. Use existing test infrastructure and avoid a second, divergent build recipe.

Account for the one-time Pyodide package download and realistic browser timeout; do not replace a genuine startup failure with broad retries or skipped checks. Preserve existing deploy triggers and permissions unless a concrete change is required. Keep the workflow readable and document the build steps in the maintainer guide.

## Gate C — Local validation and integration

On a deployment-preparation branch, make only changes needed for the pipeline and direct deployment blockers. Run focused workflow/configuration checks and one local combined build from source; verify both hub and Lite trees exist. Serve the combined tree under both bare localhost and the Pages-style `/ml-neuro-tutorials/` prefix using the established test server. Click Contents → Exercise 1 and Contents → Exercise 2 in a clean browser context, start kernels, load same-origin data, run supplied cells, operate one native widget and checked question per notebook, edit/save/reload/download and inspect a unique edit, test Back and Reset confirmation, and open one legacy exercise. Verify the download/Colab guidance reaches the current portable notebook without assuming public Git access. Check mobile width and light/dark legibility. Numeric checks must preserve Exercise 1's 1114×13 table and Exercise 2's 1004×360 table and established R²/MSE values.

Run one bounded full Python and frontend/browser suite if necessary for the pipeline changes; diagnose a failure once, make one focused correction, and rerun the failing gate once. If still failing, stop before merge/push. Do not broaden into unrelated content changes.

Integrate the WP41/WP41R/WP42 feature history and deployment-preparation changes into local `main` only after all preflight and validation gates pass. Inspect the resulting diff and ancestry. If `origin/main` advanced, handle only a clearly conflict-free, understood integration; otherwise stop with a report rather than silently rebasing or overwriting someone else's changes. Push normal `main` once. Never force-push or push archive/checkpoint branches. Record the exact deployed commit SHA.

## Gate D — One deployment and live verification

Observe the one GitHub Actions workflow triggered by that push. A previous successful Pages run took about 18 minutes, so allow a realistic bounded window (up to about 35 minutes), using continuous monitoring or one sensible later status check rather than rapid polling or repeated reruns. If the workflow fails, capture the failing step and logs, stop, and report; do not push speculative fixes or trigger another deployment in this WP.

After success, verify the actual production URLs in a clean browser, with the deployed SHA/artifact identified:

- Course hub and Contents at `https://yoavmp.github.io/ml-neuro-tutorials/`.
- Contents → Exercise 1 transition → its JupyterLite notebook.
- Contents → Exercise 2 transition → its JupyterLite notebook.
- Direct JupyterLite working-copy URLs for both exercises, including browser kernel start, data loading, one supplied code run, one native widget and checked question.
- Personal edit saved across reload and **Download my notebook** containing that edit; Reset warning; Back to Contents. Use a distinct test browser/profile and avoid leaving test edits in the instructor's own browser copy.
- Portable downloads return current Exercise 1/2 notebook bytes, not old static templates; Colab instructions are accurate for a possibly private future repository.
- At least one unmigrated exercise remains accessible and its existing assets work.
- No unexpected console/network errors that prevent student use; check the Pages project subpath and mobile width.

Do not claim production verification merely because CI is green. If live browsing cannot be performed, clearly mark that limitation and give exact URLs and checks for the course author; do not invent observations.

## Reports and final response

Write `WPs/reports/WP43_REPORT.md` and `WPs/reports/WP43_EXACT_CHANGELOG.md` with starting and deployed SHAs, branch integration, workflow changes, exact tests/builds, workflow run URL/status, production URLs and results, deviations, and any remaining student-facing limitations (including first-load cost and unverified Colab behavior). Preserve a report locally if committing it after the production push would cause an unwanted second Pages deployment; do not make a second push solely for reports. State explicitly what was merged, pushed, and deployed.

Return a short course-author summary with the live site links and whether both exercises are usable. If a gate blocks deployment, return the concrete blocker and current Git/production state, without claiming success or starting another WP.
