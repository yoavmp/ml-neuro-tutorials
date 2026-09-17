# WP26R — Fix WP25 archive-audit CI portability and redeploy

**Date:** 2026-09-17

**Starting branch/SHA:** `main` @ `294c1e242dc3823d2f67b931bcc9c3764c544cfd` (the WP26
documentation commit, one commit ahead of `origin/main`)
**Starting `origin/main` SHA:** `ba3771d8f536e369006c8f2fb5588d1ce71292a6` (`RELEASE_SHA`
from WP26 — merged and pushed, but its deploy workflow failed pre-build)
**Archive branch (unchanged throughout):** `archive/pre-syllabus-notebook-structure` @
`914841c4c6033f232d96ce33b6dbcc23eda1c766`, confirmed identical on `origin`
**Correction branch:** `fix/wp26r-archive-audit-ci`

**Status:** `IN PROGRESS` (updated in the WP26R report on completion)

## Purpose

WP26 merged and pushed the syllabus-aligned book (WP25) to `main`, but the "Build and
deploy Jupyter Book" GitHub Actions run for that push failed at the "Unit-test the
Python scripts (offline)" step, before ever building or publishing — production was
never touched. This WP fixes the root cause, verifies the fix in an environment that
reproduces the CI gap, pushes one corrective release, and verifies the resulting
production deployment. No notebook content, numerical results, or the Syllabus page
are touched.

## Root cause (confirmed against the actual WP26 failure log, not inferred)

Seven tests in `tests/test_wp25_content_audit.py` (`ArchiveBranchTests` and
`SyllabusPageUnchangedTests`) shell out to `git` via a local `_git()` helper
(`subprocess.run(["git", *args], cwd=REPO_ROOT, ..., check=True)`):

| Test | Git command | CI error |
|---|---|---|
| `test_archive_branch_exists_locally` | `git branch --list archive/pre-syllabus-notebook-structure` | assertion failure — empty output, not an exception (this is the lone `branch --list` call, which exits 0 even when nothing matches) |
| `test_archive_branch_points_at_the_exact_wp24_tip` | `git rev-parse archive/pre-syllabus-notebook-structure` | `CalledProcessError`, exit 128 |
| `test_archive_branch_has_no_new_commits_beyond_the_wp24_tip` | `git rev-list --count 914841c4...​..archive/pre-syllabus-notebook-structure` | `CalledProcessError`, exit 128 |
| `test_archive_branch_preserves_the_old_knn_exercise_3` | `git show archive/pre-syllabus-notebook-structure:book/chapters/chapter_03/exercise_03.ipynb` | `CalledProcessError`, exit 128 |
| `test_archive_branch_preserves_the_old_classification_exercise_4` | `git show archive/pre-syllabus-notebook-structure:book/chapters/chapter_04/exercise_04.ipynb` | `CalledProcessError`, exit 128 |
| `test_syllabus_page_was_not_edited_relative_to_the_archive_branch` | `git show archive/pre-syllabus-notebook-structure:book/syllabus.md` | `CalledProcessError`, exit 128 |
| `test_syllabus_source_is_byte_for_byte_unchanged_from_the_wp24_tip` | `git show 914841c4c6033f232d96ce33b6dbcc23eda1c766:book/syllabus.md` | `CalledProcessError`, exit 128 |

They pass locally because this development machine's repository has both the local
branch `archive/pre-syllabus-notebook-structure` and full commit history, so every
`rev-parse`/`rev-list`/`show` resolves.

**They are not purely a "branch name" problem.** The seventh failure
(`test_syllabus_source_is_byte_for_byte_unchanged_from_the_wp24_tip`) addresses the
WP24 tip **by commit SHA**, not by branch name, and it still failed with the same
`exit status 128`. `.github/workflows/deploy.yml`'s "Check out repository" step uses
`actions/checkout@v4` with no `fetch-depth` argument, which defaults to
**`fetch-depth: 1`** — a shallow checkout containing only the tip commit of `main`
itself and no ancestor history and no other branches or refs. In that checkout, `git
rev-parse`/`git show` cannot resolve **any** commit other than `HEAD`, whether
addressed by branch name or by raw SHA — including `914841c4c6033f232d96ce33b6dbcc23eda1c766`,
which is in fact an ancestor of `main` (reachable through the WP25 merge) but is
outside the shallow history window fetched.

So: five of the seven checks were checking archive-branch **contents** (three) or
**existence/identity** (two: `points_at_the_exact_wp24_tip`,
`has_no_new_commits_beyond_the_wp24_tip`); one checked Syllabus content against the
archive branch; one checked Syllabus content against the WP24 tip **SHA directly**.
All seven fail for the same underlying reason — insufficient checkout depth/refs in
CI — not because the tests are wrong about what they check, only about the
environment they assume.

## Correct design

1. Replace every `ARCHIVE_BRANCH`-relative git command in
   `tests/test_wp25_content_audit.py` with the immutable commit constant already used
   by one of the seven tests, renamed for clarity:

   ```python
   PRE_SYLLABUS_ARCHIVE_COMMIT = "914841c4c6033f232d96ce33b6dbcc23eda1c766"
   ```

   `ArchiveBranchTests.test_archive_branch_exists_locally` and
   `test_archive_branch_points_at_the_exact_wp24_tip`/
   `test_archive_branch_has_no_new_commits_beyond_the_wp24_tip` collapse into commit-
   identity checks (`git cat-file -e <sha>^{commit}` / `git rev-parse <sha>` equality)
   — remote branch-existence stays a repository-verification concern (already covered
   live in WP26's own procedure and reports), not an offline unit test.
2. Give `.github/workflows/deploy.yml`'s checkout step `fetch-depth: 0` so the full
   history — including `914841c4c6033f232d96ce33b6dbcc23eda1c766` — is present in the
   CI checkout. This is a checkout-configuration change only; it does not fetch other
   branches over the network during the test step itself (all refs come from the one
   `actions/checkout` step, before any Python runs) and adds no network dependency to
   the test process.
3. The Python test step remains fully offline: it only ever inspects commits already
   present in the local `.git` object database after checkout, via plain `git`
   subprocess calls — no `git fetch`, no GitHub API, no credentials.
4. Tests keep checking the same intended differences between the pre-syllabus and
   post-syllabus notebook structure (old KNN Exercise 3 content, old classification
   Exercise 4 content, Syllabus page byte-identity) — only how they *locate* the
   pre-syllabus commit changes, from a branch name to the immutable SHA already
   recorded as `WP24_TIP_SHA`.

Explicitly not done: no fake local archive branch created in CI, no `git fetch` added
inside the tests, no test skipped/weakened/marked `expectedFailure`, no swallowed `git`
errors, no hardcoded archived notebook text substituted for the git-based comparison,
no dependency on the current working branch name, no GitHub credentials required.

## Scope

**Permitted changes:**
* `tests/test_wp25_content_audit.py` (commit-based archive access)
* `.github/workflows/deploy.yml` (checkout `fetch-depth: 0`)
* `WPs/WP26R_FIX_ARCHIVE_AUDIT_AND_REDEPLOY.md` and its two reports

**Not touched:** canonical notebooks, portable notebooks, interactive components,
datasets, model outputs, widget exports, Jupyter Book content, Contents/sidebar, the
Syllabus page, the Word overview file/generator, archive branch contents.

## Procedure

1. Verify starting state matches WP26R §2 exactly; stop on any unexpected divergence
   or untracked file outside the whitelist.
2. Create `fix/wp26r-archive-audit-ci` from `main`'s WP26 tip; commit this
   specification first.
3. Diagnose the seven failures precisely against the actual WP26 CI log (done above,
   before implementation).
4. Implement the correction: rewrite the seven archive-branch-relative git calls in
   `tests/test_wp25_content_audit.py` to use `PRE_SYLLABUS_ARCHIVE_COMMIT`; add
   `fetch-depth: 0` to the checkout step in `.github/workflows/deploy.yml`.
5. Run the seven formerly-failing tests directly, then the whole
   `tests/test_wp25_content_audit.py` module — confirm none skipped, none touching the
   network, all passing.
6. Verify independence from the local archive branch: build the correction commit in a
   throwaway worktree/clone created with `mktemp -d` that has full history
   (fetch-depth 0 equivalent) but **no local branch** named
   `archive/pre-syllabus-notebook-structure`; run the audit file there; require it to
   pass; remove exactly that temporary directory afterward; never touch the real
   archive branch.
7. Reproduce the exact failed CI gate command
   (`python -m unittest discover -s tests -v`) locally and confirm it passes in full,
   recording pass/skip/fail counts and timing.
8. Bounded additional checks: focused WP25 content-audit tests (done in steps 5–7),
   YAML syntax validation of the edited workflow file via the repo's available PyYAML
   installation, and one Jupyter Book build as a release sanity check. Frontend unit
   tests, Playwright, portable-notebook execution, and scientific audits are not
   rerun unless a check surfaces an unexpected regression.
9. Commit the implementation on `fix/wp26r-archive-audit-ci`
   ("Fix WP25 archive audit for CI checkouts"); record its SHA.
10. Before merging: fetch `origin`, confirm `origin/main` is still exactly
    `ba3771d8f536e369006c8f2fb5588d1ce71292a6` and local `main` still contains only the
    expected WP26 documentation commit above it; stop if `origin/main` has advanced.
11. Merge `fix/wp26r-archive-audit-ci` into local `main` with `--no-ff`
    ("Merge WP26R CI archive-audit correction"); no automatic conflict resolution.
    Record the merge commit as `WP26R_RELEASE_SHA`.
12. Push `main` to `origin` exactly once; verify local/remote `main` both equal
    `WP26R_RELEASE_SHA`.
13. Locate the new GitHub Actions run for `WP26R_RELEASE_SHA` (one immediate lookup,
    one more after ~20s if needed, no further polling); watch it once to completion
    (`gh run watch RUN_ID --exit-status --interval 15`, max 15 minutes, no reruns, no
    background/scheduled polling). On failure: fetch failed-step logs once, summarize,
    stop.
14. On success, verify the repaired workflow built the book and published GitHub
    Pages, then verify production per WP26R §17's checklist, with at most one
    cache-busted reload for any page that initially appears stale.
15. Write `WPs/reports/WP26R_REPORT.md` and `WPs/reports/WP26R_EXACT_CHANGELOG.md`
    covering root cause, exact old/new git commands, the checkout change, the
    isolated-checkout verification, the full offline-gate result, all recorded SHAs
    and run details, production verification, and confirmation that no notebook
    content or archive-branch contents changed.
16. Commit the two WP26R reports locally on `main` only (`WP26R_DOCUMENTATION_SHA`);
    do not push this commit.

## Stop conditions

Unexpected git divergence, an untracked/modified file outside the whitelist, a merge
conflict, `origin/main` having advanced beyond `ba3771d8f536e369006c8f2fb5588d1ce71292a6`
before the WP26R merge, a bounded-check failure that survives its one
diagnosis/correction/rerun cycle, a new workflow failure, or a workflow that does not
finish within 15 minutes — any of these halts the WP before the next irreversible step
and is reported rather than worked around. No notebook-content or scientific-result
change, no Syllabus-page change, no Word-overview change, no archive-branch
deletion/move, no force-push, no second `main` push, no workflow rerun, no polling
loop, no WP27.
