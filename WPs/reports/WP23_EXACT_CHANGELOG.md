# WP23 Exact Changelog — Merge and deploy dark-mode Plotly repair

Distinguishes files by which piece of work introduced them. All paths relative to the repository root.

## A. Introduced by WP22 (implementation + its own docs), merged into `main` at `RELEASE_SHA` (`4237ce7b3528526066bcda03e6e94545ca29ad14`)

Committed on `fix/published-dark-mode-plots` prior to WP23, carried into `main` by the WP23 merge:

**Implementation:**
* `interactive/src/theme.ts` (new)
* `interactive/src/components/classification-imbalance.ts` (modified)
* `interactive/src/components/classification-threshold.ts` (modified)
* `interactive/src/components/correlation.ts` (modified)
* `interactive/src/components/histogram.ts` (modified)
* `interactive/src/components/knn-abc.ts` (modified)
* `interactive/src/components/knn-explore.ts` (modified)
* `interactive/src/components/plotly-policy.ts` (modified)
* `interactive/src/components/regression-compare.ts` (modified)
* `interactive/src/components/retention.ts` (modified)
* `interactive/src/components/runtime-smoke.ts` (modified)
* `interactive/src/main.ts` (modified)
* `interactive/src/styles.css` (modified)

**Tests:**
* `interactive/tests/theme.test.ts` (new)
* `interactive/tests/plotly-policy.test.ts` (new)
* `interactive/e2e-book/chapter01-dark-mode.spec.ts` (new)
* `interactive/e2e-book/wp22-cross-chapter-dark-mode.spec.ts` (new)

**WP22's own documentation (committed on the feature branch as part of WP22, not WP23):**
* `WPs/WP22_DARK_MODE_PLOTLY_REPAIR.md` (new, then amended by the WP22 addendum commit)
* `WPs/reports/WP22_REPORT.md` (new)
* `WPs/reports/WP22_EXACT_CHANGELOG.md` (new)
* `WPs/reports/wp22_screenshots/before-dark-book-light-widget.png` (new)
* `WPs/reports/wp22_screenshots/after-dark-book-dark-widget.png` (new)

Originating commits (all pre-date WP23):
```
4f9bc70 WP22: document dark-mode Plotly repair work package
6bce45c WP22: repair dark-mode Plotly theme sync across all interactive activities
e5d6ad7 WP22 addendum: cross-chapter built-book dark-mode verification
```

## B. The WP23 specification

* `WPs/WP23_MERGE_DEPLOY_DARK_MODE_REPAIR.md` (new)

Originating commits on `fix/published-dark-mode-plots`, both merged into `main` at `RELEASE_SHA`:
```
af3e9ea WP23: document dark-mode repair release
1d4629e WP23 correction: record verified starting state
```

The correction commit amended the same file to record the verified/corrected starting-state determination (local `main` one commit ahead of `origin/main`, confirmed as an authorized, harmless WP22 documentation checkpoint) — it did not touch WP22 implementation.

## C. Post-deployment documentation only (this commit, local-only, NOT pushed)

Committed on `main` **after** `RELEASE_SHA` was already pushed and deployed. Pushing this commit would trigger a second, out-of-scope deployment, so it is intentionally kept local-only.

* `WPs/WP23_MERGE_DEPLOY_DARK_MODE_REPAIR.md` (modified — status set to `COMPLETED`, `RELEASE_SHA` recorded, "Outcome" section added)
* `WPs/reports/WP23_REPORT.md` (new)
* `WPs/reports/WP23_EXACT_CHANGELOG.md` (new, this file)

Commit message: `WP23: document dark-mode deployment outcome`

## D. Explicitly untouched (pre-existing, unrelated to WP22/WP23)

Never added, edited, moved, deleted, or committed by WP22 or WP23:
* `WPs/reports/WP16_ARCHITECT_REPORT.md`
* `WPs/reports/WP21_DEPLOYMENT_REPORT.md`

## E. Not part of the repository (created and used only for live production verification, never committed)

* `/private/tmp/.../wp23-live/playwright.prod.config.ts` — temporary Playwright config pointing the **unmodified** WP22 spec files at `https://yoavmp.github.io` instead of the local built-book server (no environment-variable override existed in `interactive/playwright.book.config.ts` to reuse).
* `/private/tmp/.../wp23-live/console-and-operability.mjs` — temporary supplementary script for browser console/page-error capture and interactive-control operability checks against production, not covered by the reused specs.

Both files live under this session's scratchpad directory, outside the git repository, and were not committed at any point.
