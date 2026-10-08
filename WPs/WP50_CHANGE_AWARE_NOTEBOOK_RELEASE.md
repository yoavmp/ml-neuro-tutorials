# WP50 — Change-aware testing and deployment for the course notebooks

## Context and goal

WP49 published Exercises 1–8 as JupyterLite notebooks. Its release gate builds the combined Jupyter Book/JupyterLite site and runs broad Python and Playwright suites on a push to `main`. That was appropriate for the initial release, but makes a small edit to one exercise take a long time both locally and in CI. WP49 §H already established the intended policy for future single-notebook work; implement that policy in the actual workflow.

The goal is for an author to change wording in one notebook, or for a developer to change one notebook's behavior, without re-running unrelated notebooks. The published site must still be generated from the canonical sources and checked before publication. Do not change the teaching content of Exercises 1–8 in this WP. Preserve Exercises 9–12 in source and keep their existing publication status.

Read `WPs/reports/WP49_REPORT.md` (especially §§G–H), `WP49_EXACT_CHANGELOG.md`, the current deploy workflow, notebook generators, manifest, and relevant tests before implementing. Treat the checked-out repo as authoritative if details differ from this brief.

## Deliverables

1. A deterministic change classifier used by CI and documented for local use. It should report the comparison base, changed paths, affected exercise IDs, classification, selected checks, and reason for escalation. Prefer a small maintainable script over complex YAML expressions.
2. A deployment workflow whose tests depend on that classification. Keep the existing combined site build and publication mechanism, but do not run every exercise's execution/browser tests for a change confined to one exercise.
3. A separate, manually runnable full regression workflow (`workflow_dispatch`); a scheduled full regression run is welcome if it is inexpensive enough and clearly separate from publication. It must never publish on its own. Preserve the on-demand legacy Exercise 9–10 smoke workflow.
4. A short maintainer guide: where wording is edited, which generated files must be refreshed, expected gates for each change, how to request a full run, and how to see why CI chose a gate.
5. `WPs/reports/WP50_REPORT.md` and `WP50_EXACT_CHANGELOG.md` with commands, durations, pass/fail results, CI run link, and any limits.

## Comparison base

Compute affected changes relative to the **source commit of the last successfully published site**, not simply the previous push to `main`: several pushes may have failed before a later fix. Verify how the existing `gh-pages` publication records its source SHA and use a robust, explicit marker going forward if necessary. For a missing, corrupt, or unreachable marker, default to the full gate. Never mark a failed or cancelled publication as the new base. Ensure the first run introducing this workflow takes the full gate because the workflow itself changed.

Handle multiple changed exercises, renames/deletions, generated assets, and a force-push/non-ancestor base conservatively. Do not silently drop any changed path. Log the decision in a concise human-readable form and a machine-readable form for job selection.

## Gate rules

| Change | Required gate before publish |
| --- | --- |
| Only `WPs/**` report files | Keep WP49's no-deployment behavior. |
| Verified prose-only change for Exercise N | Regenerate/check Exercise N's derived notebook(s); verify that the code-cell sources and execution-relevant notebook metadata are unchanged relative to the published base; run cheap structural/content checks relevant to N; build the combined site once; smoke-check the generated N notebook, transition route, and portable download. Skip kernel execution and broad browser suites. |
| Exercise N code, data use, interactive question/widget, or uncertain notebook-cell change, with no shared dependency change | Run N's relevant generator check, structural/reference tests and browser spec, plus tests for any actually affected shared component. Build once and check N's routes/download. For multiple exercise IDs, take the union. |
| Shared helper/CSS, data export, package dependency, manifest, book/JupyterLite config, workflow, Playwright shared fixture, deployment mechanism, unknown path, or untrustworthy classifier/base | Full release gate, including the existing broad Python and browser checks. |

The prose-only gate must be based on a trustworthy comparison of the **generated student-facing and portable notebooks**. Matching file names or a commit message is insufficient. Compare cell order/type and code-cell sources exactly; treat any change to code, execution metadata, embedded outputs/assets, checks, question logic, or unrecognized fields conservatively. If a string in a code cell changes (including a multiple-choice label), use at least the exercise-scoped gate. Do not add a manual “skip tests” switch that can override a full-gate classification.

Keep the normal build and publish path one-way: classification → selected tests → one combined build → targeted artifact smoke checks → publish. A failing selected check or build must stop publication. A manual full run may test all exercises but must not mutate the published site.

## Claude's local working policy

Apply the same classification before local testing. Run the smallest meaningful checks for the changed files. Do not run an older exercise's execution suite unless its own code or a shared dependency it uses changed. Build the combined site once when a release candidate is ready. For a wording-only edit, use the prose-only verification and inspect rendered wording; do not launch a 20-minute notebook execution just for reassurance.

For any long command, record its process/session ID, monitor it until exit, read its exit status and actual failure output immediately, and report a status update at least every five minutes. Do not leave a finished or crashed job idle awaiting a prompt. Set reasonable timeouts, distinguish genuine test failure from infrastructure failure, and avoid rerunning an unchanged long suite without a specific reason. Report the duration of every check over five minutes.

## Verification and release

1. Exercise the classifier with fixtures or focused tests covering: a markdown-only edit; a code-cell edit in one exercise; a changed MC label inside a code cell; two exercises changing together; shared helper/config change; unknown path; missing published-base marker; and a prior failed push followed by a fix. Prove the union of changes since the last *successful* deployment is selected.
2. Validate workflow syntax and job conditions. Run only relevant local tests for the classifier/workflow, plus the full gate required for this initial workflow change. Do not repeatedly rerun broad suites after unrelated edits to reports.
3. Make one controlled production push once local evidence is ready. Monitor the real GitHub Actions run through completion, inspect its logs, and verify the published source marker and live route. If it fails, investigate the actual failure, make a justified fix, and continue to a successful release; avoid speculative configuration toggles or blind retries.
4. Prove the **new fast path** without requiring a second production push: use a local end-to-end classifier/workflow simulation on a fixture commit or branch with a markdown-only Exercise N change. If the chosen workflow design permits a safe non-publishing Actions validation, use it. Do not change student-facing text merely to trigger another deployment.

At the end, state the actual remaining wall-clock work for a wording edit versus a code edit (measured if possible, estimated and labeled otherwise). Do not claim the fast path is production-proven if only simulated. Preserve a clean working tree; include a starting checkpoint and final commit in the report.
