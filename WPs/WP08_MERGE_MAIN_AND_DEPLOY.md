# WP08 — Merge the completed EDA work into `main` and deploy GitHub Pages

## Objective

Safely release all completed work from `feature/reusable-interactive-widgets` to
`main`, build and test the exact merged commit, push it without rewriting
history, wait for the GitHub Pages workflow, and verify that the newest notebook
and portable notebook are available online.

This is a release/deployment WP. Do not add new teaching content or refactor the
implementation.

## Required reading

Before acting, read completely:

- `CLAUDE_INTERACTIVE_WIDGETS.md`
- `WPs/README.md`
- `WPs/reports/WP07_REPORT.md`
- `WPs/reports/WP07_EXACT_CHANGELOG.md`
- this WP

## 1. Preserve the pre-release state

1. Confirm the current branch is `feature/reusable-interactive-widgets`.
2. Inspect `git status`, recent commits, all local branches, configured remotes,
   and the commits currently at local/remote `main`.
3. Never discard, overwrite, or silently omit an existing change.
4. Add this WP file if needed and create the mandatory checkpoint commit named
   `checkpoint: before WP08`.
5. Create annotated tag `wp08-start` at that checkpoint. If the name already
   exists, use the next unambiguous numeric suffix and report it.
6. Confirm WP01–WP07 implementation and report commits are ancestors of the
   feature branch HEAD.

Do not use `git reset --hard`, `git checkout -- <path>`, `git clean`, force push,
or history rewriting.

## 2. Fetch and assess divergence

1. Run `git fetch origin --prune`.
2. Report the ahead/behind relationship among:
   - `origin/main`;
   - local `main`;
   - `feature/reusable-interactive-widgets`.
3. Inspect commits present on `origin/main` but absent from the feature branch.
4. If remote `main` has unrelated new commits, preserve them. Update local
   `main` using a fast-forward-only pull and merge the feature branch into that
   updated `main`.
5. If there is a substantive merge conflict—especially in the notebook,
   generated portable notebook, workflow, or book configuration—stop before
   resolving it and describe the exact conflict in the report. Do not guess.

## 3. Merge locally

1. Switch to local `main`.
2. Bring it to `origin/main` with `git pull --ff-only origin main`.
3. Merge `feature/reusable-interactive-widgets` using an explicit non-fast-forward
   merge commit, for example:

   ```bash
   git merge --no-ff feature/reusable-interactive-widgets \
     -m "Merge interactive EDA tutoring notebook"
   ```

4. Confirm the merge contains all WP01–WP07 commits and that the working tree is
   clean.
5. Do not delete the feature branch or any `wpNN-start` tags.

## 4. Test the exact merged `main` commit before pushing

Run the complete WP07 CI-equivalent suite from `main`, using the repository's
documented working directories:

- clean npm install;
- TypeScript typecheck;
- frontend unit tests;
- production dependency audit;
- frontend production build;
- widget artifact validation;
- all Python unit tests;
- portable-notebook stale check;
- portable notebook smoke execution outside the repository;
- standalone Playwright suite;
- clean Jupyter Book build;
- `*.err.log` guard;
- built-book Playwright suite;
- two consecutive clean notebook builds and deterministic-figure comparison if
  this is still a documented WP07 release assertion.

Also inspect the resulting HTML and confirm:

- the repaired sidebar control is present and functional;
- all three interactive activities load and respond;
- the corrected opening text, histogram example, and IQR equation are present;
- the old built-in Colab launch control is absent;
- the new Colab/raw links target
  `book/downloads/chapter_01/exercise_01_portable.ipynb` on `main`.

If any required test fails, do not push `main`. Diagnose only enough to provide
an actionable report; do not expand WP08 into implementation work.

Do not commit `book/_build`, caches, `node_modules`, Playwright artifacts, or
other generated local test output.

## 5. Push `main` without rewriting history

Only after every required local release check passes:

```bash
git push origin main
```

- Never use `--force` or `--force-with-lease`.
- If rejected because remote `main` changed after the fetch, stop. Fetch and
  report the new divergence; do not improvise a second merge during the same
  release attempt.
- If authentication or branch protection blocks the push, stop and report the
  exact user action required.

Record the pushed merge commit hash and confirm `origin/main` resolves to it.

## 6. Monitor the GitHub Pages deployment

1. Identify the workflow run triggered by the pushed merge commit. Prefer the
   authenticated GitHub CLI if available; otherwise use the repository's public
   Actions/API pages.
2. Wait for the workflow and Pages deployment to finish. Poll at reasonable
   intervals and allow for ordinary GitHub Pages propagation delay.
3. If the workflow fails, record the failing job/step and relevant error. Do not
   change repository secrets, permissions, Pages settings, or branch protection
   without Yoav's explicit approval.
4. Confirm the deployed commit corresponds to the pushed `main` commit rather
   than an older queued workflow.

## 7. Verify the live release

Verify the public site, not only localhost:

- `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html`
- raw portable notebook:
  `https://raw.githubusercontent.com/yoavmp/ml-neuro-tutorials/main/book/downloads/chapter_01/exercise_01_portable.ipynb`
- Colab target:
  `https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/blob/main/book/downloads/chapter_01/exercise_01_portable.ipynb`

Required live checks:

1. The page contains unmistakable WP07 markers: the new run/download card,
   corrected exercise guidance, the 25-bin age example, and the IQR definition.
2. At desktop width the primary sidebar button visibly collapses/reopens the
   sidebar; at narrow width it opens the navigation dialog.
3. Each of the three embedded browser activities loads and a control change
   updates its visualization/state.
4. The raw portable notebook returns successfully, validates with `nbformat`,
   and is byte-identical to the committed generated notebook.
5. The Colab URL names the portable notebook on `main` and opens that notebook,
   not the canonical Jupyter Book source. If automated inspection of Colab is
   blocked by Google interstitial/authentication, report that limitation and
   verify the URL plus raw target rather than claiming a full pass.
6. No obvious mixed-content, missing-resource, console, or iframe errors appear.

Use cache-busting or confirm the deployed content/hash when necessary so a stale
browser cache is not mistaken for the new release.

## 8. Final report and report-only commit

After live verification, create:

- `WPs/reports/WP08_REPORT.md`
- `WPs/reports/WP08_EXACT_CHANGELOG.md`

The report must state:

- success/failure for merge, local tests, push, workflow, Pages deployment, and
  every live check;
- checkpoint/tag, feature HEAD, previous `origin/main`, merge commit, pushed
  `origin/main`, workflow run URL/ID, and deployed commit when available;
- exact divergence and whether any upstream changes were incorporated;
- all warnings, deviations, deferred checks, and actions requiring Yoav;
- confirmation that no force push, destructive command, settings change, or
  generated build output commit occurred;
- rollback guidance using `git revert -m 1 <merge-commit>`—identification only;
  do not perform rollback.

`WP08_EXACT_CHANGELOG.md` should primarily document git topology and deployment
state. WP08 should not have substantive source-code changes beyond inclusion of
the WP/report files.

Commit these two report files on `main` with:

```text
WP08 report: document main deployment
```

Push that report-only commit normally, wait for its workflow to finish, and
confirm the final live deployment is at the report commit or a later legitimate
`main` commit. This second deployment is expected because the repository tracks
WP reports.

If the initial merge push/deployment fails, keep the reports local and do not
push a misleading success report.

## Stop condition

Stop after WP08. Do not begin WP09, remove the generic theme download button, or
make any new notebook/design changes.

