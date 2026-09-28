# WP43RR — One workflow rerun and production verification

## Authority and scope

The course author authorized deploying JupyterLite Exercises 1 and 2. WP43R fixed the clean-CI `ipywidgets` dependency, but its GitHub Actions run `36414417778` failed on one Exercise 2 Section 8 slider Playwright timeout after the Python tests and both site builds passed. The live site was not updated. This WP makes **one rerun of the existing workflow at the existing pushed SHA**, without a new code commit or push, to determine whether the isolated timeout was transient and, if the workflow succeeds, complete the already-authorized production verification.

Read `WPs/reports/WP43_REPORT.md`, `WPs/reports/WP43R_REPORT.md`, and their changelogs. Reported state to verify: `origin/main` is `89c9bccab37c1ab295f16ef55251d4c90a04a0cf`; `gh-pages` is still `f6ddfc28e5102d44f94dc5dc86ba9875ad36db8a` (`deploy: 58ed1c6…`); WP43R reports are committed only on local `main`. Do not assume those refs are unchanged without checking.

## Gate A — Read-only preflight

1. Inspect current branch, `git status --short --branch`, recent log, local and remote `main`, `gh-pages`, and the exact conclusion/log of run `36414417778`. Confirm the slider timeout is as reported and no later run or publication has already superseded it. Confirm the local report commit and any untracked changes are preserved. Do not reset, stash, stage, rebase, or push. Do not touch `Homework_Materials/`.
2. Verify there is no workflow already active and that the existing pushed SHA still contains the `ipywidgets` pin and WP43 combined-build workflow. Confirm GitHub Actions provides a rerun of this exact run/job with the same head SHA and standard publish permissions. If remote `main` or `gh-pages` advanced unexpectedly, or another deployment is in progress, stop and report rather than rerunning an obsolete commit.

## Gate B — One rerun, no source change

Rerun the **whole failed workflow/job exactly once** at SHA `89c9bcc…`, using the GitHub Actions rerun operation. Do not push a report or empty commit to trigger a fresh build. Do not skip the browser test or publish manually. Monitor this one attempt with a realistic bound of about 40 minutes (the previous run took 29 minutes), using continuous observation or sensible spaced checks; avoid rapid polling, arbitrary repeated sleeps, or repeated reruns.

If it fails, capture the exact failed step, logs, Playwright trace/screenshot/video if available, CI worker count, and timing. Specifically determine whether the same `.widget-slider .noUi-handle` visibility timeout recurred and whether the widget cell had rendered, failed, or was still executing. **Stop after this one failed rerun.** Do not weaken assertions, raise timeouts blindly, change notebook code, push a fix, or start another workflow in this WP. State that production remains unchanged only after verifying `gh-pages` and the live site.

## Gate C — Verify the live deployment if green

If the workflow succeeds, confirm the `gh-pages` deploy commit corresponds to the rerun head SHA. In a fresh browser profile, verify the real Pages project subpath:

- [https://yoavmp.github.io/ml-neuro-tutorials/](https://yoavmp.github.io/ml-neuro-tutorials/) and Contents.
- Contents → Exercise 1 transition → its JupyterLite working copy; direct Lite URL; browser kernel, same-origin 1114×13 data, supplied cell, retention or histogram widget, checked question.
- Contents → Exercise 2 transition → its JupyterLite working copy; direct Lite URL; browser kernel, same-origin 1004×360 data, linear result, Section 8 slider, checked question.
- Edit a uniquely identifiable student code or written-answer cell, save, reload, and confirm **Download my notebook** contains that exact edit. Check Reset warning and Back to Contents. Use a separate test profile so the instructor's browser work is not modified.
- Both current portable downloads (not old static notebooks) and accurate Colab download/upload instructions; one unchanged legacy exercise; 390px width and dark-mode legibility; no blocking console/network failures. Distinguish the expected one-time cold start from a broken kernel.

Do not claim the site is live solely from a green workflow or HTTP 200. If browser interaction is unavailable, say exactly what was and was not verified and provide links for the course author's check.

## Reporting

Write `WPs/reports/WP43RR_REPORT.md` and `WPs/reports/WP43RR_EXACT_CHANGELOG.md` with preflight refs, rerun attempt/run URL and head SHA, exact outcome, whether `gh-pages` advanced, live URLs and observed checks if green, or failure artifacts and production state if red. Reports may be committed locally but must not be pushed solely to publish reports, since that would trigger another deployment. Return a short course-author summary. Do not start another WP.
