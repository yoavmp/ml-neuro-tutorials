# WP23 — Merge and deploy dark-mode Plotly repair

**Date:** 2026-09-16

**Starting feature-branch SHA:** `e5d6ad7fedf519636a2ae047c42de389f16a2966`
**Starting `main` SHA (expected, per task instructions):** `0a28301ceee3c4a3a8891158a73ac0754b4b6150`
**Starting `main` SHA (actual, observed):** `4f9bc7014625ed0a50df938f393b957a25c04037`
**Starting `origin/main` SHA (observed after `git fetch origin main`):** `0a28301ceee3c4a3a8891158a73ac0754b4b6150`

**Working branch:** `fix/published-dark-mode-plots`

**Status:** `RELEASE IN PROGRESS`

## Authorized actions

This WP authorizes exactly:

1. One merge of `fix/published-dark-mode-plots` into local `main` (`git merge --no-ff`, merge commit message `Merge WP22 dark-mode Plotly repair`).
2. One push of `main` to `origin` (`git push origin main`).
3. One bounded deployment watch (single continuous `gh run watch`, ~20s interval, max 15 minutes total, no background process, no scheduled wakeup, no repeated `gh run view`, no manual polling loop) of the "Build and deploy Jupyter Book" workflow run associated with the resulting release SHA.

## Explicit prohibitions

* No force-pushing (`git push --force` / `--force-with-lease`) under any circumstances.
* No repeated or rerun deployments — the GitHub Actions workflow run for the release SHA may be watched once and never manually rerun.
* No additional product/implementation changes to the WP22 dark-mode repair or any other code while performing this release. This WP is documentation, merge, push, and verification only.
* No pulling, rebasing, resetting, or stashing to resolve unexpected branch divergence automatically — any such divergence must stop the process and be reported.
* No amending of existing commits.
* No second push, for any reason (including documentation-only follow-up commits, which must remain local-only after the one deployment-triggering push).
* No editing, moving, deleting, or committing unrelated untracked files, specifically:
  * `WPs/reports/WP16_ARCHITECT_REPORT.md`
  * `WPs/reports/WP21_DEPLOYMENT_REPORT.md`

## Pre-merge discrepancy noted at authoring time

At the time this specification was written, local `main` was observed to be **one commit ahead** of the expected/authoritative SHA given in the WP23 task instructions (`0a28301...`). The extra commit is:

```
4f9bc70 WP22: document dark-mode Plotly repair work package
```

This is the same commit object (identical SHA) that also forms part of the `fix/published-dark-mode-plots` branch history — i.e. at some point this commit was made directly on `main` rather than solely on the feature branch. `origin/main`, confirmed via `git fetch origin main`, remains exactly at the expected `0a28301...` — the divergence is local-only and unpushed.

Per WP23 §2 ("Pre-merge verification"), this qualifies as "either branch differs unexpectedly," which requires halting before merge/push and reporting rather than resolving automatically (no pull/rebase/reset/stash). This specification is being committed to the feature branch only; the merge/push steps are deferred pending explicit direction on how to reconcile local `main`.
