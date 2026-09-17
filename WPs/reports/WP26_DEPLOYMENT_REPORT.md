# WP26 Deployment Report — Deploy the syllabus-aligned book

## Status: FAILURE (production unaffected; `main` merged and pushed, deploy workflow failed pre-build)

`main` was merged and pushed exactly once as authorized. The "Build and deploy Jupyter
Book" workflow run for the resulting commit failed at the **"Unit-test the Python
scripts (offline)"** step — before "Build Jupyter Book" and before "Publish website"
ever ran. **The live production site was not touched and remains on its pre-WP26
content** (verified directly against production, see §7). Per WP26 §11/§15, on a
workflow failure the correct action is: retrieve logs once, summarize, stop — no
rerun, no cancel, no speculative fix, no second push. That is exactly what was done.

---

## 1. Archive branch

* **Name:** `archive/pre-syllabus-notebook-structure`
* **SHA:** `914841c4c6033f232d96ce33b6dbcc23eda1c766` (unchanged — the WP24 tip)
* **Pushed to `origin` in this WP:** yes — `git push -u origin
  archive/pre-syllabus-notebook-structure`
* **Confirmed on origin:** yes — `git ls-remote --heads origin
  archive/pre-syllabus-notebook-structure` returned
  `914841c4c6033f232d96ce33b6dbcc23eda1c766`, matching exactly. No new commits were
  added to the archive branch by this WP.

## 2. Release branch and merge

* **Release branch:** `release/wp26-syllabus-book-deployment`, cut from
  `edit/wp25-syllabus-restructure` @ `99adbb5bcba93f64a1683128344caaaf44ef0b27`
* **WP26 specification commit:** `dcb6d603...` ("WP26: add deployment specification")
  committed on the release branch before any push
* **Pre-merge local `main`:** `c644933387e2117ed66b975ab7d476aef5d79802` ("WP23:
  document dark-mode deployment outcome" — already an ancestor of the release branch,
  matching the WP26 spec's expected/documented pattern; no unrelated divergence)
* **Pre-merge `origin/main`:** `4237ce7b3528526066bcda03e6e94545ca29ad14` (confirmed an
  ancestor of the release branch before merging)
* **Merge:** `git merge --no-ff release/wp26-syllabus-book-deployment` into `main`,
  message "Merge WP25 syllabus-aligned notebook structure". No conflicts.
* **RELEASE_SHA:** `ba3771d8f536e369006c8f2fb5588d1ce71292a6`

## 3. `main` push

* `git push origin main` — pushed exactly once (`4237ce7..ba3771d main -> main`).
* Post-push verification: local `main` = `origin/main` =
  `ba3771d8f536e369006c8f2fb5588d1ce71292a6`. Confirmed equal.
* No second push of `main` occurred at any point in this WP.

## 4. GitHub Actions workflow

* **Workflow name:** Build and deploy Jupyter Book
* **Run ID:** `35219556794`
* **Triggering SHA:** `ba3771d8f536e369006c8f2fb5588d1ce71292a6` (= `RELEASE_SHA`,
  confirmed via `gh run view --json headSha`)
* **Start time:** 2026-09-17T12:09:43Z
* **URL:** https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/35219556794
* **Duration:** ~1m19s (12:09:43Z → 12:11:02Z)
* **Result:** **failure**, at step "Unit-test the Python scripts (offline)"
  (`python -m unittest discover -s tests -v`). Steps after it ("Check the portable
  notebook is not stale", Playwright installs/tests, "Build Jupyter Book", "Fail on
  notebook execution errors", built-book e2e, portable-notebook smoke test, "Publish
  website") never ran.
* Located with a single `gh run list --branch main --limit 5` lookup — the run was
  already present, so the fallback ~20s-wait/second-lookup step was not needed.
* Watched once, continuously, via `gh run watch 35219556794 --exit-status --interval
  15` to completion (well under the 15-minute bound). Not rerun, not cancelled.

### Failure diagnosis (one diagnosis, as authorized; no correction attempted)

`python -m unittest discover -s tests -v` reported `FAILED (failures=1, errors=6,
skipped=11)` out of 443 tests. All 7 failing tests are in
`tests/test_wp25_content_audit.py`, classes `ArchiveBranchTests` and
`SyllabusPageUnchangedTests`:

* `test_archive_branch_exists_locally`
* `test_archive_branch_points_at_the_exact_wp24_tip`
* `test_archive_branch_has_no_new_commits_beyond_the_wp24_tip`
* `test_archive_branch_preserves_the_old_knn_exercise_3`
* `test_archive_branch_preserves_the_old_classification_exercise_4`
* `test_syllabus_page_was_not_edited_relative_to_the_archive_branch`
* `test_syllabus_source_is_byte_for_byte_unchanged_from_the_wp24_tip`

Root cause: these tests shell out to `git branch --list archive/pre-syllabus-notebook-structure`,
`git rev-parse archive/pre-syllabus-notebook-structure`, and `git show
archive/pre-syllabus-notebook-structure:<path>` — i.e. they require that branch to
exist in the **local** git checkout the test process runs against. They pass locally
(this machine has the archive branch, confirmed in §1). The GitHub Actions runner's
`actions/checkout@v4` step fetches only the pushed ref (`main`) with the workflow's
default settings; it does not fetch `archive/pre-syllabus-notebook-structure`, even
though that branch now exists on `origin` (confirmed in §1). So in the CI runner the
branch is genuinely absent from the local ref list, and every test that shells out to
it fails or errors. This is a **CI-environment gap in a WP25 test file**, not a defect
in the WP25 notebook content, the merge, or the push — WP25 was local-only and this is
the first time this test file has ever run inside GitHub Actions. Fixing it (e.g.
fetching the archive branch in the workflow, or rewriting the tests to compare against
`origin/archive/...` or a bundled ref) is a test/CI-configuration change to
`tests/test_wp25_content_audit.py` and/or `.github/workflows/deploy.yml` — outside
WP26's authorization (§11: "do not push a speculative fix"; §15: no rerun). No attempt
was made to fix it.

## 5. Production verification

**Not performed as a full pass** — the deployment did not succeed, so per WP26 §11 no
production verification pass is called for. Instead, the following spot checks confirm
production is unaffected and still serving the pre-WP26 (WP23/WP24-era) content:

| Check | Result |
|---|---|
| `gh-pages` branch tip | `d1d670b06aa8c6544be70fa7d1d8df67f23e5831` (predates this WP's push; unchanged by this run) |
| `chapters/chapter_03/exercise_03.html` title | `Exercise 3: KNN and the Bias–Variance Tradeoff` — old numbering, **not** WP25's "Exercise 3: Classification and Metrics" |
| `chapters/chapter_04/exercise_04.html` title | `Exercise 4: Classification with Logistic Regression` — old numbering, **not** WP25's cross-validation placeholder |
| `chapters/chapter_12/exercise_12.html` | HTTP 404 — chapter 12 does not exist in production yet |

Conclusion: production is exactly as it was before this WP started. No stale-cache
concerns, no partial deployment, no broken links introduced.

## 6. Not performed (deployment did not reach these stages)

* Exercises 1–12 live verification
* Transferred KNN-widget result
* Transferred classification-widget result
* Light/dark-mode result
* Colab/download-link result
* Exercise-13-absence / Syllabus-unchanged live confirmation (unaffected, since
  production wasn't touched — see §5)
* Browser console check

## 7. Deviations / unresolved issues

* The GitHub Actions deployment workflow failed before building or publishing. This is
  a **pre-existing gap** in `tests/test_wp25_content_audit.py` (written and validated
  only against a local checkout during WP25, never previously exercised in CI) rather
  than an issue with the WP25 content itself or with this WP's merge/push mechanics.
* **Recommendation (not actioned by this WP):** a follow-up WP is needed to make
  `ArchiveBranchTests`/`SyllabusPageUnchangedTests` CI-safe — e.g. have the workflow
  fetch the archive branch (`git fetch origin
  archive/pre-syllabus-notebook-structure:archive/pre-syllabus-notebook-structure`)
  before the Python unit-test step, or rewrite the tests to target
  `origin/archive/pre-syllabus-notebook-structure` — then push `main` again (a genuine
  second, corrective push, which is out of scope for WP26 as authorized).
* `main` on `origin` currently sits at `RELEASE_SHA`
  (`ba3771d8f536e369006c8f2fb5588d1ce71292a6`) with a failed/red Actions run attached
  to it. It has not been reverted, reset, or force-pushed — per WP26's explicit
  prohibitions, no such corrective action was taken without authorization.
* No notebook, widget, data, or numeric-result changes were made or attempted at any
  point.

## 8. Final `git status --short --branch`

```
## main...origin/main
?? WPs/reports/WP16_ARCHITECT_REPORT.md
?? WPs/reports/WP21_DEPLOYMENT_REPORT.md
```

(as of immediately before this report and the changelog were committed locally; see
`WPs/reports/WP26_EXACT_CHANGELOG.md` for the exact commit added after this file).

Local `main` = `origin/main` = `ba3771d8f536e369006c8f2fb5588d1ce71292a6` at the time
this report was written. The two whitelisted legacy reports remain the only untracked
files.
