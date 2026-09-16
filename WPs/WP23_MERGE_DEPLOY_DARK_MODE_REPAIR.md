# WP23 — Merge and deploy dark-mode Plotly repair

**Date:** 2026-09-16

**Starting feature-branch SHA (before the WP23 specification commit):** `e5d6ad7fedf519636a2ae047c42de389f16a2966`
**Feature-branch tip containing the WP23 specification:** `af3e9ea00102b3f46852b13e1709acf445e33d6f`
**Starting `origin/main` SHA:** `0a28301ceee3c4a3a8891158a73ac0754b4b6150`
**Starting local `main` SHA:** `4f9bc7014625ed0a50df938f393b957a25c04037`

**Working branch:** `fix/published-dark-mode-plots`

**Status:** `COMPLETED`

**Release SHA (deployed to GitHub Pages):** `4237ce7b3528526066bcda03e6e94545ca29ad14`
**Documentation SHA (local-only, not pushed):** see `WPs/reports/WP23_REPORT.md` §1 (recorded after this commit is made)

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

## Corrected starting-state determination

At authoring time, local `main` was observed to be one commit ahead of `origin/main`. Rather than an unexpected divergence, this was confirmed to be an authorized WP22 documentation checkpoint:

```
4f9bc70 WP22: document dark-mode Plotly repair work package
```

This commit was made directly on local `main` (documentation only — the 253-line WP22 specification file, no implementation code) and is also a shared ancestor of `fix/published-dark-mode-plots`, since the feature branch was cut from `main` at that point. `origin/main` remained at the earlier deployed SHA (`0a28301...`), unaffected, since the checkpoint commit was never pushed.

The corrected, authoritative starting state is:

* `origin/main`: `0a28301ceee3c4a3a8891158a73ac0754b4b6150`
* local `main`: `4f9bc7014625ed0a50df938f393b957a25c04037`
* feature branch before the WP23-spec commit: `e5d6ad7fedf519636a2ae047c42de389f16a2966`
* feature-branch tip containing the WP23 specification: `af3e9ea00102b3f46852b13e1709acf445e33d6f`

Four checks were performed before proceeding to merge, all of which passed:

1. `origin/main` (`0a28301...`) is an ancestor of local `main` — confirmed.
2. The checkpoint commit `4f9bc70...` is an ancestor of `fix/published-dark-mode-plots` — confirmed.
3. The only difference between `origin/main` and local `main` is the WP22 specification file (`WPs/WP22_DARK_MODE_PLOTLY_REPAIR.md`, 253 insertions, no other files) — confirmed.
4. The WP23 specification commit (`af3e9ea...`) contains only its intended file (`WPs/WP23_MERGE_DEPLOY_DARK_MODE_REPAIR.md`) — confirmed.

Because the checkpoint commit was already a shared ancestor of the feature branch (not a divergent, conflicting change), merging `fix/published-dark-mode-plots` into local `main` introduces no duplicate content and is safe to proceed with, per explicit authorization to proceed with option 1 (no reset of local `main`).

## Outcome

Full results — merge SHA, push confirmation, GitHub Actions run details, and live dark-mode verification against production — are recorded in `WPs/reports/WP23_REPORT.md` and `WPs/reports/WP23_EXACT_CHANGELOG.md`. Summary: merge, push, and deployment all succeeded; the live site was verified against production with a light-OS-emulated browser and all dark-mode checks passed for Exercises 1–4, including the Exercise 3 KNN A/B/C activity specifically called out in the original bug report.
