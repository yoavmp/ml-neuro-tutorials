# WP26R Exact Changelog — Fix WP25 archive-audit CI portability and redeploy

Outcome: **SUCCESS**. Full detail in `WPs/reports/WP26R_REPORT.md`. Ordered by what
actually happened; remote-affecting actions called out explicitly.

## 1. CI/test correction (local, on `fix/wp26r-archive-audit-ci`)

Branch `fix/wp26r-archive-audit-ci` created from `main` @
`294c1e242dc3823d2f67b931bcc9c3764c544cfd` (the WP26 documentation-commit tip).

Commit `5972ba1...` "Fix WP25 archive audit for CI checkouts" — **2 files changed**:

* `tests/test_wp25_content_audit.py` (81 lines changed) —
  * Removed `ARCHIVE_BRANCH` constant; renamed `WP24_TIP_SHA` →
    `PRE_SYLLABUS_ARCHIVE_COMMIT` (same value,
    `914841c4c6033f232d96ce33b6dbcc23eda1c766`).
  * Added `_commit_exists(sha)` helper (`git cat-file -e <sha>^{commit}`, offline).
  * `ArchiveBranchTests` → renamed `PreSyllabusArchiveContentTests`; its 5 methods
    consolidated to 3, all now addressing `PRE_SYLLABUS_ARCHIVE_COMMIT` by SHA:
    `test_archive_branch_exists_locally` → `test_pre_syllabus_commit_is_present_in_local_history`;
    `test_archive_branch_preserves_the_old_knn_exercise_3` →
    `test_pre_syllabus_commit_preserves_the_old_knn_exercise_3`;
    `test_archive_branch_preserves_the_old_classification_exercise_4` →
    `test_pre_syllabus_commit_preserves_the_old_classification_exercise_4`. Retired (not
    weakened-to-no-op; rationale in the report §2):
    `test_archive_branch_points_at_the_exact_wp24_tip`,
    `test_archive_branch_has_no_new_commits_beyond_the_wp24_tip` — both tested branch
    *pointer* drift, which has no offline equivalent; that check already happens at
    release time (WP26/WP26R's own `git rev-parse`/`git diff --stat` steps).
  * `SyllabusPageUnchangedTests`: its 2 methods
    (`test_syllabus_source_is_byte_for_byte_unchanged_from_the_wp24_tip`,
    `test_syllabus_page_was_not_edited_relative_to_the_archive_branch`) — identical
    assertions once both addressed the same commit — merged into 1:
    `test_syllabus_source_is_byte_for_byte_unchanged_from_the_pre_syllabus_commit`.
  * Module docstring updated to document the commit-based approach and why
    branch-pointer verification moved to deployment time.
  * Net: 443 → 440 total tests in `tests/`; 7 old archive/Syllabus methods → 4 new
    ones, all still git-based and offline.
* `.github/workflows/deploy.yml` (2 lines added) — "Check out repository" step
  (`actions/checkout@v4`) gained `with: fetch-depth: 0`.

## 2. WP26R specification commit (local, on `fix/wp26r-archive-audit-ci`)

Commit `54f3fc7...` "WP26R: add CI archive-audit correction specification" — adds
`WPs/WP26R_FIX_ARCHIVE_AUDIT_AND_REDEPLOY.md` only.

(Chronological note: the specification commit was made *before* the implementation
commit above, per WP26R's own procedure — §3 "create branch, commit spec" precedes §4
"diagnose"/§5 "implement". Listed second here only because the implementation is the
substantive CI/test correction.)

## 3. Isolated-checkout verification (no commits; local-only, fully cleaned up)

* Temporary clone created via `mktemp -d` +
  `git clone --no-local --single-branch --branch fix/wp26r-archive-audit-ci --no-tags`.
* Confirmed no local or remote-tracking `archive/pre-syllabus-notebook-structure` ref
  existed in the clone, and that `914841c4c6033f232d96ce33b6dbcc23eda1c766` still
  resolved (full single-branch history).
* `python3 -m unittest tests.test_wp25_content_audit -v` → 12/12 passed.
* Temporary directory removed with `rm -rf` immediately after (exact path only). The
  real `archive/pre-syllabus-notebook-structure` branch was never read from, fetched,
  moved, or deleted.

## 4. Merge commit (local, on `main`)

* `git switch main && git merge --no-ff fix/wp26r-archive-audit-ci -m "Merge WP26R CI
  archive-audit correction"` — no conflicts.
* Merge commit SHA (**`WP26R_RELEASE_SHA`**): `44739b30da52191d563f70d80d9d2dbcaa102ea7`
* Parents: `294c1e242dc3823d2f67b931bcc9c3764c544cfd` (prior local `main` tip, the WP26
  documentation commit) and `5972ba1...` (correction-branch tip, itself descended from
  `54f3fc7...` the WP26R spec commit).
* 3 files changed relative to prior `main`: `.github/workflows/deploy.yml`,
  `tests/test_wp25_content_audit.py`, and the new
  `WPs/WP26R_FIX_ARCHIVE_AUDIT_AND_REDEPLOY.md`.

## 5. `main` push (remote-affecting — the one authorized `main` push)

* `git push origin main`
* Result: `origin/main` moved `ba3771d8f536e369006c8f2fb5588d1ce71292a6` →
  `44739b30da52191d563f70d80d9d2dbcaa102ea7` (`WP26R_RELEASE_SHA`).
* Verified: local `main` == `origin/main` == `44739b30da52191d563f70d80d9d2dbcaa102ea7`.
* **This was the only push to `main` in WP26R.** No second push occurred; the failed
  WP26 workflow (run `35219556794`) was never rerun.

## 6. Deployment (triggered automatically by the push above; completed successfully)

* GitHub Actions run `35220942956`, workflow "Build and deploy Jupyter Book", on
  `main`, triggering SHA `44739b30da52191d563f70d80d9d2dbcaa102ea7` (=
  `WP26R_RELEASE_SHA`).
* Started 2026-09-17T12:24:39Z, completed (success) 2026-09-17T12:28:08Z (3m27s).
* **Every step passed**, including "Unit-test the Python scripts (offline)" (the
  former failure point), "Build Jupyter Book", and "Publish website".
* `gh-pages` updated to the newly built site; production verified in §9 of the report.
* Watched once via `gh run watch`; not rerun, not cancelled.

## 7. Local-only report commit (NOT pushed)

* `WPs/reports/WP26R_REPORT.md` and `WPs/reports/WP26R_EXACT_CHANGELOG.md` (this file)
  committed on local `main` only, after the single `main` push above.
* This commit is **`WP26R_DOCUMENTATION_SHA`** — recorded once made. Deliberately
  **not pushed**, so it triggers no further Actions run.
* Because this commit lands after the only `main` push in §5, these report files are
  **not present on `origin/main` or in the deployed production build** — local only.

## Summary of remote state after WP26R

* `origin/archive/pre-syllabus-notebook-structure`: `914841c4c6033f232d96ce33b6dbcc23eda1c766`
  — **unchanged** throughout WP26R
* `origin/main`: `44739b30da52191d563f70d80d9d2dbcaa102ea7` (`WP26R_RELEASE_SHA`) — CI
  green on this commit
* `origin/gh-pages` (production): updated by run `35220942956`; serving the WP25
  syllabus-aligned book (Exercises 1–12, no Exercise 13) — verified live in the report
* Local `main`: one commit ahead of `origin/main` after the documentation commit
  (`WP26R_DOCUMENTATION_SHA`), not pushed
