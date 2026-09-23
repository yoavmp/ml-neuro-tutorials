# WP37V — Exact Changelog

WP37V is a production-status-verification-only work package. It introduced **no notebook,
widget, dataset, model, test, configuration, dependency, or workflow content**, and performed no
merge, no push, and no rerun of the workflow. It queried the already-completed workflow run once
and verified already-published production content.

## Files introduced by WP37V itself

| File | Nature |
|---|---|
| `WPs/reports/WP37V_REPORT.md` | This WP's production-status verification report, committed locally on `main` (not pushed). |
| `WPs/reports/WP37V_EXACT_CHANGELOG.md` | This file, committed alongside the report (not pushed). |

## Files modified by WP37V

| File | Nature of change |
|---|---|
| `WPs/reports/WP37_DEPLOYMENT_REPORT.md` | A dated addendum (2026-09-23) appended, and the "Overall result" line updated to point to it. The original report body is otherwise preserved unchanged as a historical record of what was known at the time WP37 stopped. |

## Non-content operations WP37V performed

- One read-only query: `gh run view 35881835065 --json status,conclusion,url,jobs`.
- Multiple read-only production checks against `https://yoavmp.github.io/ml-neuro-tutorials/`:
  `curl` HTTP-status and text-content checks (cache-busted), and Playwright browser sessions
  reusing the repository's own existing `interactive/e2e-book/*.spec.ts` files unmodified, plus
  one small temporary throwaway console-error-sweep spec — all run via a temporary Playwright
  config created only inside a `mktemp -d` directory and deleted immediately after use. Nothing
  from this temporary directory was committed; `git status --short --branch` was clean before,
  during (aside from the two report files being authored), and after.
- One local, unpushed documentation commit containing the two files listed above plus the
  `WP37_DEPLOYMENT_REPORT.md` addendum.

## What was explicitly NOT done in WP37V

- No rerun, retry, or cancellation of workflow run `35881835065` (it had already completed
  successfully by the time WP37V queried it).
- No merge, push, rebase, reset, or force-push.
- No notebook, widget, dataset, script, test, or workflow file was created, edited, or
  regenerated.
- No second query of the workflow run.
- WP38 was not started.
