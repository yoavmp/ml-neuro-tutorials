# WP43RR exact changelog

## Source/workflow changes

**None.** This WP is explicitly a rerun-only WP ("Do not push a report or
empty commit to trigger a fresh build... Do not weaken assertions, raise
timeouts blindly, change notebook code, push a fix"). No file under
version control besides the two report files below was modified. No commit
was pushed to `origin/main`.

## CI operations performed

1. `git fetch origin main gh-pages` — read-only, confirmed
   `origin/main` = `89c9bccab37c1ab295f16ef55251d4c90a04a0cf` and
   `origin/gh-pages` = `f6ddfc28e5102d44f94dc5dc86ba9875ad36db8a`, both
   matching the WP43R report exactly.
2. `gh run list --workflow=deploy.yml --status=in_progress` and
   `--status=queued` — confirmed empty (no active/queued run) before the
   rerun.
3. `gh run rerun 36414417778` — the one authorized rerun operation, issued
   at 2026-09-28T11:54:36Z. No `--failed`-only flag used; the WP text calls
   for rerunning "the whole failed workflow/job," and this workflow has a
   single job (`build-and-deploy`), so a full rerun and a failed-jobs-only
   rerun are equivalent here.
4. Monitored via spaced `gh run view 36414417778 --json status` polls
   (≥60s apart) until `status == "completed"`; no additional reruns were
   issued.
5. `gh run view 36414417778 --json ...jobs.steps` and
   `gh run view --job=108915252487 --log-failed` — read-only, to capture
   the exact failed step and log excerpt.
6. `gh api repos/yoavmp/ml-neuro-tutorials/actions/runs/36414417778/attempts/1/jobs`
   and `gh api .../jobs/108901997609/logs --allow-escape-sequences` —
   read-only, to pull attempt 1's (the original WP43R run's) own log for a
   side-by-side comparison of worker count and per-test timing against
   attempt 2 (this rerun).
7. `gh api repos/yoavmp/ml-neuro-tutorials/actions/runs/36414417778/artifacts`
   — read-only, confirmed no Playwright trace/screenshot/video artifacts
   exist for this run (the workflow has no `upload-artifact` step for
   test output).
8. `git fetch origin gh-pages` (post-rerun) and two `curl` HTTP checks
   against the live site — read-only, confirmed `gh-pages` and the
   production site are unchanged.

No `git reset`, `stash`, `checkout`, `rebase`, or `push` was performed at
any point. `Homework_Materials/` was not read, staged, or touched.

## Repository changes (this session)

- Added `WPs/reports/WP43RR_REPORT.md` (this WP's execution report).
- Added `WPs/reports/WP43RR_EXACT_CHANGELOG.md` (this file).
- Both committed locally on `main` after this content is finalized; **not
  pushed**, per the WP's explicit instruction not to push solely to
  publish reports (that would trigger a fourth `Build and deploy Jupyter
  Book` run).

## Production state before and after this WP

| | Before | After |
|---|---|---|
| `origin/main` | `89c9bcc` | `89c9bcc` (unchanged; local `main` gains report commits, not pushed) |
| `gh-pages` | `f6ddfc2` (`deploy: 58ed1c6…`) | `f6ddfc2` (`deploy: 58ed1c6…`) — unchanged |
| Live hub | `200`, pre-WP41 content | `200`, pre-WP41 content — unchanged |
| `lite/notebooks/index.html` | `404` | `404` — unchanged |

Production was not touched by this WP.
