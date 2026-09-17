# WP26 — Deploy the syllabus-aligned book (WP25 release)

**Date:** 2026-09-17

**Starting branch/SHA:** `edit/wp25-syllabus-restructure` @ `99adbb5bcba93f64a1683128344caaaf44ef0b27`
**Archive branch (verified, pre-existing):** `archive/pre-syllabus-notebook-structure` @ `914841c4c6033f232d96ce33b6dbcc23eda1c766`
**Starting `origin/main` SHA:** `4237ce7b3528526066bcda03e6e94545ca29ad14`
**Working/release branch:** `release/wp26-syllabus-book-deployment` (cut from the WP25 tip above)

**Status:** `IN PROGRESS` (updated in the WP26 report on completion)

## Purpose

Deploy the already-approved WP25 syllabus-aligned notebook restructure (Exercises
1–12) to production. The user has locally reviewed and visually tested WP25 and
authorizes this WP to push the archive branch, merge WP25 into `main`, push `main`
once, let the existing "Build and deploy Jupyter Book" GitHub Actions workflow deploy
it, and verify the live site. This is a release WP: merge, push, verify, document.
No new teaching-content, notebook, widget, styling, dataset, model, or numerical-result
changes are made. The Syllabus page, the Word course-overview document, and
`scripts/build_course_overview_docx.py` are not touched. The two whitelisted untracked
legacy reports (`WPs/reports/WP16_ARCHITECT_REPORT.md`,
`WPs/reports/WP21_DEPLOYMENT_REPORT.md`) are left untouched throughout.

## Authorized actions

This WP authorizes exactly:

1. One push of `archive/pre-syllabus-notebook-structure` to `origin` (`git push -u
   origin archive/pre-syllabus-notebook-structure`), with immediate remote-SHA
   verification.
2. One merge of `release/wp26-syllabus-book-deployment` into local `main`
   (`git merge --no-ff`, message "Merge WP25 syllabus-aligned notebook structure").
3. One push of `main` to `origin` (`git push origin main`).
4. One bounded lookup of the GitHub Actions run for the release SHA (immediate lookup,
   then at most one more after a ~20s wait — no repeated polling).
5. One bounded deployment watch (single continuous `gh run watch RUN_ID --exit-status
   --interval 15`, max 15 minutes, no background process, no scheduled wakeup, no
   repeated `gh run view`, no manual polling loop).
6. One production verification pass against the live site (with at most one
   cache-busted reload per page that initially appears stale).
7. A bounded set of pre-deployment verification gates (§ "Bounded pre-deployment
   verification" below) — each gate may have at most one diagnosis + one correction
   (deployment-configuration or generated-build-artifact fixes only) + one rerun.

## Explicit prohibitions

* No new teaching-content, notebook, widget, styling, dataset, model, or
  numerical-result changes.
* No changes to the Syllabus page, the Word course-overview document, or
  `scripts/build_course_overview_docx.py`.
* No touching `WPs/reports/WP16_ARCHITECT_REPORT.md` or
  `WPs/reports/WP21_DEPLOYMENT_REPORT.md`.
* No reset, rebase, stash, clean, or automatic resolution of unexpected divergence —
  stop and report instead.
* No force-pushing, under any circumstances.
* No second push of `main`, for any reason (documentation commits stay local-only).
* No amending of existing commits.
* No rerunning or cancelling the GitHub Actions workflow.
* No repeated/scheduled polling of the workflow run.
* No pushing a speculative fix if the workflow fails — diagnose, summarize, stop.
* No starting WP27.
* If a validation-gate failure would require changing approved notebook content or
  implementation, stop and request authorization rather than making the change.

## Procedure

1. **Verify starting state** — `git status --short --branch`, current branch, HEAD,
   `origin/main`, the archive branch SHA, and the last 10 commits. Confirm the active
   branch is `edit/wp25-syllabus-restructure`, the archive branch is at
   `914841c4c6033f232d96ce33b6dbcc23eda1c766`, WP25's spec/implementation/report
   commits and report files are present, and the only untracked files are the two
   whitelisted legacy reports. Stop before pushing if anything else is
   modified/untracked/missing/divergent.
2. **Create `release/wp26-syllabus-book-deployment`** from the WP25 tip and commit
   this specification as the first commit on it.
3. **Confirm archive integrity** — the archive branch must still point exactly at
   `914841c4c6033f232d96ce33b6dbcc23eda1c766`, must be an ancestor of the release
   branch, and gets no new commits from this WP.
4. **Bounded pre-deployment verification** (focused, not a full re-run of WP25's
   validation):
   1. Focused WP25 structural/content tests: `python -m unittest
      tests.test_wp25_content_audit tests.test_book_structure
      tests.test_placeholder_exercises tests.test_exercise_02_notebook
      tests.test_exercise_03_notebook -v`
   2. Portable-notebook deterministic checks for Exercises 2 and 3:
      `.venv/bin/python scripts/smoke_portable_notebook.py --notebook chapter_02` and
      `--notebook chapter_03`.
   3. Frontend typecheck: `npm run typecheck` (in `interactive/`).
   4. One production frontend build: `npm run build` (in `interactive/`).
   5. One Jupyter Book build: `jupyter-book build book`.
   6. One quick built-book check confirming Exercise 2 opens, Exercise 3 opens,
      Exercise 4 is the cross-validation placeholder, Exercise 12 exists, Exercises
      1–12 appear in sidebar order, and no Exercise 13 appears.
5. **Push the archive branch first**, verify the remote SHA immediately via
   `git ls-remote --heads origin archive/pre-syllabus-notebook-structure`. Stop (no
   force-push) if it differs from `914841c4c6033f232d96ce33b6dbcc23eda1c766`.
6. **Verify `main` before merging** — `git fetch origin`, then compare local `main`,
   `origin/main` (expected prior release `4237ce7b3528526066bcda03e6e94545ca29ad14`),
   and the release branch. Stop without merging if `origin/main` has advanced
   unexpectedly, local `main` contains an unrelated commit, the release branch is
   missing expected main history, or anything has diverged unexpectedly.
7. **Merge** `release/wp26-syllabus-book-deployment` into `main` with `--no-ff` and
   message "Merge WP25 syllabus-aligned notebook structure". Stop and report on any
   conflict rather than resolving automatically. Record the merge commit as
   `RELEASE_SHA`.
8. **Push `main` exactly once.** Verify local and remote `main` both equal
   `RELEASE_SHA`.
9. **Locate the deployment workflow** for `RELEASE_SHA` via `gh run list` — one
   immediate lookup, then (if needed) one more after ~20s. Record workflow name, run
   ID, triggering SHA, start time, URL.
10. **Watch the workflow once**, `gh run watch RUN_ID --exit-status --interval 15`, max
    15 minutes. On timeout: stop the watch, record status, report pending, do not
    rerun/cancel/start another run. On failure: fetch failed-step logs once,
    summarize, stop — no rerun, no speculative fix. On success: proceed to production
    verification.
11. **Verify the live production book** at
    `https://yoavmp.github.io/ml-neuro-tutorials/` against the 20-point checklist in
    the WP26 task description (Exercises 1–12 open with correct titles/placeholders,
    no Exercise 13, transferred KNN/classification widgets work, light/dark mode,
    Colab/download links, Syllabus unchanged, no final-project reminder leaking into
    notebooks, no new console errors). One cache-busted reload permitted per
    initially-stale page; no repeated refresh loop.
12. **Write the deployment reports** — `WPs/reports/WP26_DEPLOYMENT_REPORT.md` and
    `WPs/reports/WP26_EXACT_CHANGELOG.md` — covering every item listed in the WP26
    task description (status; archive branch/SHA/remote confirmation; release
    branch; pre-merge branch/SHA; `RELEASE_SHA`; `origin/main` SHA; workflow name/run
    ID/URL/duration/result; production URLs checked; per-exercise verification;
    widget/light-dark/link results; Exercise-13 and Syllabus-unchanged confirmations;
    unrelated console warnings; deviations; final `git status --short --branch`). The
    changelog must clearly separate the archive-branch push, the WP26 spec commit,
    the merge commit, the `main` push/deployment, and the local-only report commit —
    and must not claim the report files themselves were deployed, since they are
    committed after the only `main` push.
13. **Commit the two WP26 reports locally on `main` only** (`DOCUMENTATION_SHA`) — do
    not push this commit (pushing would trigger another deployment). Final intended
    state: `origin/main` at `RELEASE_SHA`; local `main` one documentation commit ahead
    at `DOCUMENTATION_SHA`; remote archive branch at the WP24 archive SHA; only the
    two whitelisted reports untracked.

## Stop conditions

Any of the following halts the WP before the next irreversible step (push/merge/
deploy) and is reported rather than worked around: unexpected git divergence, an
untracked/modified file outside the whitelist, a merge conflict, an archive-branch
remote SHA mismatch, a validation-gate failure that would require notebook-content
changes, a workflow failure, or a workflow that does not finish within 15 minutes.
