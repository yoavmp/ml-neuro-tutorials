# WP31 Exact Changelog — Deploy Exercises 4–6

Outcome: **FAILURE** — `main` merged and pushed; deploy workflow failed before
building or publishing; production unaffected. See
`WPs/reports/WP31_DEPLOYMENT_REPORT.md` for full detail. Ordered by what actually
happened, remote-affecting actions called out explicitly.

## 1. WP31 specification commit (local, on `fix/wp30r-classification-holdout`)

* Branch already at `343630792ac90d07effa083e1e5d51627cb8326e` ("WP30R: restrict
  classification-depth audit to Exercise 3's development partition"), the expected
  starting tip.
* Commit `6f18ac6fcac4512404f8e8e9258e268b92eec974` "WP31: add specification (initial
  checkpoint)" — adds `WPs/WP31_DEPLOY_EXERCISES_4_TO_6.md` only. 1 file changed, 284
  insertions.

## 2. Ancestry verification (local-only, read-only remote query)

* `git fetch origin main` — the only fetch performed in this WP.
* Confirmed `origin/main` unchanged at `44739b30da52191d563f70d80d9d2dbcaa102ea7`;
  local `main` unchanged at `74c9a9a15091059dd591982422f2fece0e0993e8`, exactly one
  documentation commit ahead; full WP27–WP30R chain present and linear; no unrelated
  content. See deployment report §1 for the complete table.

## 3. Bounded pre-deployment validation (local-only, no remote effect)

* 13 gates from WP31 §4, plus 1 additional offline gate from `deploy.yml` not on that
  list (`export_widget_data.py --check --artifact all`) — all run exactly once, all
  passed. Full command list and results in deployment report §2.
* No file in the working tree was created, modified, or deleted by any gate (the
  frontend production build's output was verified byte-identical to what was already
  committed; the Jupyter Book build wrote only to the gitignored `book/_build/`).

## 4. Merge commit (local, on `main`)

* `git switch main && git merge --no-ff fix/wp30r-classification-holdout -m "Merge
  Exercises 4-6 course materials"`
* No conflicts.
* Merge commit SHA (**`RELEASE_SHA`**): `3da7d3f8b1ad4fe627f9581d23ef7e267a2c47ed`
* Parents: `74c9a9a15091059dd591982422f2fece0e0993e8` (prior local `main` tip) and
  `6f18ac6fcac4512404f8e8e9258e268b92eec974` (WP31 checkpoint branch tip).
* 110 files changed, 43,860 insertions(+), 410 deletions(-) relative to prior `main`
  (brings in the entire WP27 + WP27R + WP28 + WP29 + WP30 + WP30R + WP31-spec
  history: Exercise 4 validation/cross-validation notebook and three widgets,
  Exercise 5 regularization/feature-selection notebook and widget, Exercise 6
  decision-tree notebook and two widgets, their portable notebooks, tests, and
  reports).
* Merged `main` tree confirmed byte-for-byte identical to the checkpoint branch tree
  (`git diff --stat RELEASE_SHA fix/wp30r-classification-holdout` → empty).

## 5. `main` push (remote-affecting — the one authorized `main` push)

* `git push origin main`
* Result: `origin/main` moved `44739b30da52191d563f70d80d9d2dbcaa102ea7` →
  `3da7d3f8b1ad4fe627f9581d23ef7e267a2c47ed` (`RELEASE_SHA`).
* Verified: `git ls-remote origin refs/heads/main` →
  `3da7d3f8b1ad4fe627f9581d23ef7e267a2c47ed refs/heads/main`.
* **This was the only push to `main` in WP31.** No second push occurred.

## 6. Deployment attempt (triggered automatically by the push above; did not complete)

* GitHub Actions run `35437984824`, workflow "Build and deploy Jupyter Book", on
  `main`, triggering SHA `3da7d3f8b1ad4fe627f9581d23ef7e267a2c47ed` (= `RELEASE_SHA`).
* Discovered on the first of two permitted bounded queries (already `in_progress`);
  no second query needed.
* Started 2026-09-19T10:39:10Z, completed (failed) 2026-09-19T10:40:36Z (~1m26s).
* Watched once, continuously, via `gh run watch 35437984824 --exit-status`, to
  completion.
* **Failed** at step "Unit-test the Python scripts (offline)" —
  `test_matches_a_fresh_recomputation` in `tests/test_export_tree_greedy_widget_data.py`
  failed with a last-digit floating-point discrepancy between the committed
  `tree_greedy_split.json` artifact and a fresh in-CI recomputation (platform/BLAS
  difference between this macOS development machine and the `ubuntu-latest` runner —
  see deployment report §5 for the full diagnosis).
* Steps that **did not run**: "Check the portable notebook is not stale", Playwright
  install/e2e, "Build Jupyter Book", "Fail on notebook execution errors", built-book
  e2e, portable-notebook smoke test, **"Publish website"**.
* **No deployment to `gh-pages` occurred.** `gh-pages` remains at
  `9dbe3b10ac31363aa1ef9cd8418a1b9cdd56ca12`, its pre-WP31 tip. **The production site
  was not changed by this WP.**
* Not rerun. Not cancelled. No fix (speculative or otherwise) was pushed.

## 7. Local-only report commit (NOT pushed)

* `WPs/reports/WP31_DEPLOYMENT_REPORT.md` and `WPs/reports/WP31_EXACT_CHANGELOG.md`
  (this file) are committed on local `main` only, after the single `main` push above.
* This commit is **`DOCUMENTATION_SHA`** — recorded below once made. It is
  deliberately **not pushed**, so it triggers no further Actions run.
* Because this commit lands after the only `main` push in §5, these report files were
  **never deployed and are not present on production or on `origin/main`** — they
  exist only in the local repository.

## Summary of remote state after WP31

* `origin/main`: `3da7d3f8b1ad4fe627f9581d23ef7e267a2c47ed` (`RELEASE_SHA`) — CI red on
  this commit (deploy job failed pre-build, at the Python unit-test step)
* `origin/gh-pages` (production): `9dbe3b10ac31363aa1ef9cd8418a1b9cdd56ca12`,
  unchanged — still serving pre-WP31 (WP26R-era) content
* Local `main`: one commit ahead of `origin/main` after the documentation commit
  (`DOCUMENTATION_SHA`), not pushed
* `fix/wp30r-classification-holdout`: unchanged since the WP31 checkpoint commit
  `6f18ac6fcac4512404f8e8e9258e268b92eec974`, now fully merged into `main`
