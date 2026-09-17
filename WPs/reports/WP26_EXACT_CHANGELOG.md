# WP26 Exact Changelog — Deploy the syllabus-aligned book

Outcome: **FAILURE** — `main` merged and pushed; deploy workflow failed before
building or publishing; production unaffected. See `WPs/reports/WP26_DEPLOYMENT_REPORT.md`
for full detail. Ordered by what actually happened, remote-affecting actions called
out explicitly.

## 1. Archive-branch push (remote-affecting)

* `git push -u origin archive/pre-syllabus-notebook-structure`
* Result: new branch `archive/pre-syllabus-notebook-structure` created on `origin` at
  `914841c4c6033f232d96ce33b6dbcc23eda1c766` — no new commits, identical to the local
  branch, which was itself unchanged from the WP24 tip.
* Verified immediately: `git ls-remote --heads origin
  archive/pre-syllabus-notebook-structure` → `914841c4c6033f232d96ce33b6dbcc23eda1c766`.

## 2. WP26 specification commit (local, on `release/wp26-syllabus-book-deployment`)

* Branch `release/wp26-syllabus-book-deployment` created from
  `edit/wp25-syllabus-restructure` @ `99adbb5bcba93f64a1683128344caaaf44ef0b27`.
* Commit `dcb6d60...` "WP26: add deployment specification" — adds
  `WPs/WP26_DEPLOY_SYLLABUS_ALIGNED_BOOK.md` only. 1 file changed, 147 insertions.

## 3. Merge commit (local, on `main`)

* `git switch main && git merge --no-ff release/wp26-syllabus-book-deployment -m
  "Merge WP25 syllabus-aligned notebook structure"`
* No conflicts.
* Merge commit SHA (**`RELEASE_SHA`**): `ba3771d8f536e369006c8f2fb5588d1ce71292a6`
* Parents: `c644933387e2117ed66b975ab7d476aef5d79802` (prior local `main` tip) and
  `dcb6d60...` (release-branch tip).
* 92 files changed, 6117 insertions(+), 6440 deletions(-) relative to prior `main`
  (brings in the entire WP24 + WP25 + WP26-spec history: notebook restructure,
  placeholder chapters 4–12, archived knn-abc widget removal, updated tests).

## 4. `main` push (remote-affecting — the one authorized `main` push)

* `git push origin main`
* Result: `origin/main` moved `4237ce7b3528526066bcda03e6e94545ca29ad14` →
  `ba3771d8f536e369006c8f2fb5588d1ce71292a6` (`RELEASE_SHA`).
* Verified: local `main` == `origin/main` == `ba3771d8f536e369006c8f2fb5588d1ce71292a6`.
* **This was the only push to `main` in WP26.** No second push occurred.

## 5. Deployment attempt (triggered automatically by the push above; did not complete)

* GitHub Actions run `35219556794`, workflow "Build and deploy Jupyter Book", on
  `main`, triggering SHA `ba3771d8f536e369006c8f2fb5588d1ce71292a6` (= `RELEASE_SHA`).
* Started 2026-09-17T12:09:43Z, completed (failed) 2026-09-17T12:11:02Z (~1m19s).
* **Failed** at step "Unit-test the Python scripts (offline)" — 7 of 443 tests in
  `tests/test_wp25_content_audit.py` failed/errored because the CI checkout does not
  have the `archive/pre-syllabus-notebook-structure` branch locally available (see
  deployment report §4 for full diagnosis).
* Steps that **did not run**: "Check the portable notebook is not stale", Playwright
  install/e2e, "Build Jupyter Book", "Fail on notebook execution errors", built-book
  e2e, portable-notebook smoke test, **"Publish website"**.
* **No deployment to `gh-pages` occurred.** `gh-pages` remains at
  `d1d670b06aa8c6544be70fa7d1d8df67f23e5831`, its pre-WP26 tip. **The production site
  was not changed by this WP.**
* Not rerun. Not cancelled. No fix (speculative or otherwise) was pushed.

## 6. Local-only report commit (NOT pushed)

* `WPs/reports/WP26_DEPLOYMENT_REPORT.md` and `WPs/reports/WP26_EXACT_CHANGELOG.md`
  (this file) are committed on local `main` only, after the single `main` push above.
* This commit is **`DOCUMENTATION_SHA`** — recorded in the deployment report once
  made. It is deliberately **not pushed**, so it triggers no further Actions run.
* Because this commit lands after the only `main` push in §4, these report files were
  **never deployed and are not present on production or on `origin/main`** — they
  exist only in the local repository.

## Summary of remote state after WP26

* `origin/archive/pre-syllabus-notebook-structure`: `914841c4c6033f232d96ce33b6dbcc23eda1c766`
* `origin/main`: `ba3771d8f536e369006c8f2fb5588d1ce71292a6` (`RELEASE_SHA`) — CI red on
  this commit (deploy job failed pre-build)
* `origin/gh-pages` (production): `d1d670b06aa8c6544be70fa7d1d8df67f23e5831`,
  unchanged — still serving pre-WP26 content
* Local `main`: one commit ahead of `origin/main` after the documentation commit
  (`DOCUMENTATION_SHA`), not pushed
