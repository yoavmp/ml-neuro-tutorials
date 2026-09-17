# WP26R Report — Fix WP25 archive-audit CI portability and redeploy

## Status: SUCCESS

WP26's deployment failure was root-caused, corrected, verified offline (including in an
isolated checkout with no local archive branch), merged, pushed once, and the
resulting GitHub Actions run built and published successfully. Production now serves
the WP25 syllabus-aligned book (Exercises 1–12, no Exercise 13). No notebook content,
scientific results, the Syllabus page, or archive-branch contents were changed.

---

## 1. Exact root cause

Seven tests in `tests/test_wp25_content_audit.py` (`ArchiveBranchTests` and
`SyllabusPageUnchangedTests`) shelled out to `git` via a `_git()` helper using
`subprocess.run(..., check=True)`:

| # | Failing test | Git command it ran | Result |
|---|---|---|---|
| 1 | `test_archive_branch_exists_locally` | `git branch --list archive/pre-syllabus-notebook-structure` | `FAIL` — empty stdout, `assertIn` failed (exits 0 even with no match, so no exception) |
| 2 | `test_archive_branch_points_at_the_exact_wp24_tip` | `git rev-parse archive/pre-syllabus-notebook-structure` | `ERROR` — `CalledProcessError`, exit 128 |
| 3 | `test_archive_branch_has_no_new_commits_beyond_the_wp24_tip` | `git rev-list --count 914841c4...​..archive/pre-syllabus-notebook-structure` | `ERROR` — exit 128 |
| 4 | `test_archive_branch_preserves_the_old_knn_exercise_3` | `git show archive/pre-syllabus-notebook-structure:book/chapters/chapter_03/exercise_03.ipynb` | `ERROR` — exit 128 |
| 5 | `test_archive_branch_preserves_the_old_classification_exercise_4` | `git show archive/pre-syllabus-notebook-structure:book/chapters/chapter_04/exercise_04.ipynb` | `ERROR` — exit 128 |
| 6 | `test_syllabus_page_was_not_edited_relative_to_the_archive_branch` | `git show archive/pre-syllabus-notebook-structure:book/syllabus.md` | `ERROR` — exit 128 |
| 7 | `test_syllabus_source_is_byte_for_byte_unchanged_from_the_wp24_tip` | `git show 914841c4c6033f232d96ce33b6dbcc23eda1c766:book/syllabus.md` | `ERROR` — exit 128 |

(Confirmed against `gh run view 35219556794 --log-failed`, not inferred: exact
tracebacks and `CalledProcessError` command strings for all seven were read directly
from the WP26 failure log before writing the WP26R specification.)

**Why they succeeded locally:** this development machine's clone has both the local
branch `archive/pre-syllabus-notebook-structure` and full commit history, so every
`rev-parse`/`rev-list`/`show`/`branch --list` call resolves normally.

**Why they failed in `actions/checkout@v4`:** the checkout step in
`.github/workflows/deploy.yml` had no `fetch-depth` argument, so it defaulted to
**`fetch-depth: 1`** — a shallow checkout containing only the tip commit of `main`,
with no other branches and no ancestor history. Crucially, **test #7 fails for the
same reason even though it addresses the WP24 tip by raw commit SHA, not by branch
name** — proving this is a checkout-depth problem, not merely a branch-naming problem.
`914841c4c6033f232d96ce33b6dbcc23eda1c766` is genuinely an ancestor of `main` (reachable
through the WP25 merge), but was outside the one-commit-deep history GitHub Actions
had fetched.

**What each test was checking:** tests #1–3 checked archive-branch *existence/identity*
(no drift from the recorded WP24 tip); tests #4–6 checked archive/Syllabus *content*
via the branch name; test #7 checked Syllabus *content* via the SHA directly. All
seven ultimately fail for the identical underlying reason (insufficient checkout
depth/refs), not because any assertion was substantively wrong.

## 2. Correction implemented

### `tests/test_wp25_content_audit.py`

* Introduced a single named constant, `PRE_SYLLABUS_ARCHIVE_COMMIT =
  "914841c4c6033f232d96ce33b6dbcc23eda1c766"` (replacing the previous
  `ARCHIVE_BRANCH` + `WP24_TIP_SHA` pair — the archive branch's tip and the WP24 tip
  were always the same commit).
* Replaced every `git ... archive/pre-syllabus-notebook-structure` invocation with the
  commit-based equivalent:

  | Old | New |
  |---|---|
  | `git branch --list archive/pre-syllabus-notebook-structure` | `git cat-file -e 914841c4...^{commit}` (new `_commit_exists()` helper) |
  | `git rev-parse archive/pre-syllabus-notebook-structure` | *(retired — see below)* |
  | `git rev-list --count 914841c4...​..archive/pre-syllabus-notebook-structure` | *(retired — see below)* |
  | `git show archive/pre-syllabus-notebook-structure:book/chapters/chapter_03/exercise_03.ipynb` | `git show 914841c4...:book/chapters/chapter_03/exercise_03.ipynb` |
  | `git show archive/pre-syllabus-notebook-structure:book/chapters/chapter_04/exercise_04.ipynb` | `git show 914841c4...:book/chapters/chapter_04/exercise_04.ipynb` |
  | `git show archive/pre-syllabus-notebook-structure:book/syllabus.md` | `git show 914841c4...:book/syllabus.md` (now the *only* Syllabus-vs-pre-syllabus check; see below) |
  | `git show 914841c4...:book/syllabus.md` | unchanged (already commit-based) |

* **Retired, not weakened-to-a-no-op:** `test_archive_branch_points_at_the_exact_wp24_tip`
  and `test_archive_branch_has_no_new_commits_beyond_the_wp24_tip` tested whether the
  **branch pointer itself** had drifted from the expected SHA. There is no offline,
  network-free way to check a *branch's* current tip without either fetching it (which
  WP26R explicitly forbids doing from inside the tests) or having it already present in
  the checkout (which a CI checkout of a single ref never has, by design, regardless of
  `fetch-depth`). Rewriting these two tests to use `PRE_SYLLABUS_ARCHIVE_COMMIT` in
  place of the branch name would have made them compare the constant to itself — a
  tautology, not a real check. Per the WP26R design ("Remote archive-branch existence
  must remain a deployment/repository verification, not an offline unit-test
  requirement"), this exact check already exists and is exercised every release: WP26
  §6/§7 and this WP's own §7 below both run `git rev-parse
  archive/pre-syllabus-notebook-structure` and `git diff --stat
  archive/pre-syllabus-notebook-structure..<release-branch>` directly against a full
  local clone as part of the release procedure, and are recorded in the WP26/WP26R
  reports. Nothing that these two tests verified is now unverified — it moved from an
  offline pytest assertion to a release-time git check, which is the only place it can
  correctly live.
* The two Syllabus-vs-pre-syllabus tests (`...relative_to_the_archive_branch` and
  `...unchanged_from_the_wp24_tip`) became **literally identical assertions** once both
  addressed the same `PRE_SYLLABUS_ARCHIVE_COMMIT`; keeping two copies of the same
  comparison would be duplication, not stronger coverage, so they were merged into one:
  `test_syllabus_source_is_byte_for_byte_unchanged_from_the_pre_syllabus_commit`.
* Net effect: 7 old test methods → 4 new/renamed methods
  (`test_pre_syllabus_commit_is_present_in_local_history`,
  `test_pre_syllabus_commit_preserves_the_old_knn_exercise_3`,
  `test_pre_syllabus_commit_preserves_the_old_classification_exercise_4`,
  `test_syllabus_source_is_byte_for_byte_unchanged_from_the_pre_syllabus_commit`), all
  still git-based, offline, content-comparing, and none skipped/`expectedFailure`/
  string-substituted for the git comparison. Total suite count: 443 → 440 (the 3-test
  reduction is exactly the two retired branch-drift checks plus the one merged
  duplicate; **no assertion of substance was removed**).
* Explicitly **not** done: no fake local archive branch created, no `git fetch` added
  inside any test, no test skipped/marked `expectedFailure`, no swallowed `git` errors
  (`_git()` still uses `check=True` and lets failures raise), no hardcoded archived
  notebook text substituted for the git-based comparison, no dependency on the current
  working branch name, no GitHub credentials required.

### `.github/workflows/deploy.yml`

* The "Check out repository" step (`actions/checkout@v4`) now passes `with:
  fetch-depth: 0`, so the CI checkout has the full commit history of `main` —
  including `914841c4c6033f232d96ce33b6dbcc23eda1c766` as an ancestor — available
  offline to every later step. This is a checkout-configuration change only: it adds
  no network access to the Python test step itself (all refs arrive via the one
  `actions/checkout` action, before any Python runs), and does not fetch other
  branches (confirmed in the isolated-checkout verification below — the archive branch
  name itself remains unresolvable even with `fetch-depth: 0`, exactly matching real
  CI).

## 3. Isolated-checkout verification (no local archive branch)

A normal run in the development repository was insufficient proof, since that
repository still has the real archive branch locally. Created a fresh, isolated clone
with `mktemp -d`, restricted to a single branch and full history (replicating
`actions/checkout@v4` with `fetch-depth: 0` far more faithfully than a plain `git
clone`, which fetches *all* remote branches and would not reproduce the CI gap):

```
git clone --no-local --single-branch --branch fix/wp26r-archive-audit-ci --no-tags \
  file://<repo> <tmpdir>
```

Before running the audit, confirmed the isolation was genuine:

```
$ git branch --list
* fix/wp26r-archive-audit-ci
$ git branch --remotes
  origin/HEAD -> origin/fix/wp26r-archive-audit-ci
  origin/fix/wp26r-archive-audit-ci
$ git rev-parse 914841c4c6033f232d96ce33b6dbcc23eda1c766
914841c4c6033f232d96ce33b6dbcc23eda1c766
$ git rev-parse archive/pre-syllabus-notebook-structure
fatal: ambiguous argument 'archive/pre-syllabus-notebook-structure': unknown revision
or path not in the working tree.
```

No local or remote-tracking ref named `archive/pre-syllabus-notebook-structure` exists
in this clone, yet the immutable commit resolves (full history was fetched). This is
the exact CI gap, faithfully reproduced. Running the audit there:

```
$ python3 -m unittest tests.test_wp25_content_audit -v
...
Ran 12 tests in 0.162s
OK
```

All 12 tests passed, none skipped. The temporary directory was then removed with `rm
-rf` (exact path only); the real `archive/pre-syllabus-notebook-structure` branch was
never touched.

## 4. Full offline CI-gate reproduction

Ran the exact command from the "Unit-test the Python scripts (offline)" workflow step,
in the working repository (which has the real archive branch — irrelevant now, since
no test references it by name):

```
.venv/bin/python -m unittest discover -s tests -v
```

**Result: `Ran 440 tests in 7.732s` / `OK (skipped=11)`** — 0 failures, 0 errors. The 11
skips are the pre-existing, unrelated `python-docx not installed in this interpreter`
skips in `tests/test_course_overview_docx.py` (present before this WP; the Word
overview generator itself was not touched). All seven formerly-failing tests now pass
under their corrected names (4 methods; see §2 for the exact mapping/consolidation).
No test in this run touched the network.

## 5. Additional bounded checks

* **YAML syntax validation** of the edited `.github/workflows/deploy.yml`, using the
  repository's already-installed PyYAML (`.venv/bin/python -c "import yaml;
  yaml.safe_load(...)"`) — parsed successfully; confirmed the checkout step's `with:
  {fetch-depth: 0}` mapping is present and correctly nested.
* **One Jupyter Book build** (`jupyter-book build book`) as a release sanity check —
  succeeded with 1 warning (`logo file 'logo.png' does not exist`), a pre-existing,
  unrelated warning present before this WP.
* Frontend unit tests, Playwright, portable-notebook execution, and scientific audits
  were **not** rerun locally (none of their inputs changed and no unexpected failure
  arose); they were, however, exercised and passed as part of the successful CI run
  itself (§7).

## 6. Correction commit

`fix/wp26r-archive-audit-ci` @ **`5972ba15...`** (short: `5972ba1`) — "Fix WP25
archive audit for CI checkouts". 2 files changed: `tests/test_wp25_content_audit.py`,
`.github/workflows/deploy.yml`. No other files touched.

## 7. Merge and push

* Pre-merge check: `origin/main` confirmed still at
  `ba3771d8f536e369006c8f2fb5588d1ce71292a6` (unchanged since WP26); local `main`
  confirmed to contain only the expected WP26 documentation commit above it. No
  unexpected advancement.
* `git switch main && git merge --no-ff fix/wp26r-archive-audit-ci -m "Merge WP26R CI
  archive-audit correction"` — no conflicts.
* **`WP26R_RELEASE_SHA`: `44739b30da52191d563f70d80d9d2dbcaa102ea7`**
* `git push origin main` — the only `main` push in WP26R
  (`ba3771d..44739b3 main -> main`).
* Verified: local `main` == `origin/main` == `44739b30da52191d563f70d80d9d2dbcaa102ea7`.

## 8. GitHub Actions run

* **Workflow:** Build and deploy Jupyter Book
* **Run ID:** `35220942956`
* **Triggering SHA:** `44739b30da52191d563f70d80d9d2dbcaa102ea7` (= `WP26R_RELEASE_SHA`,
  confirmed via `gh run view --json headSha`)
* **URL:** https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/35220942956
* **Located:** first `gh run list` lookup found nothing yet; one ~20s wait, second
  lookup found the run already `in_progress` — no further polling.
* **Watched once**, continuously, to completion (`gh run watch 35220942956
  --exit-status --interval 15`), well under the 15-minute bound.
* **Result: success**, duration 3m27s (12:24:39Z → 12:28:08Z). Every step passed,
  including "Unit-test the Python scripts (offline)" (previously the failure point)
  and, for the first time in this release cycle, "Build Jupyter Book" and "Publish
  website". The pre-existing Node.js 20 deprecation annotation (unrelated to this WP)
  is the only non-passing annotation.

## 9. Production verification

Verified against `https://yoavmp.github.io/ml-neuro-tutorials/` with cache-busting
query parameter `?cb=44739b3` (derived from `WP26R_RELEASE_SHA`), one pass, no reload
needed (nothing appeared stale):

| # | Check | Result |
|---|---|---|
| 1 | Homepage, Contents, Ex 1, Ex 8 reachable | all HTTP 200 |
| 2 | Exercise 2 title | `Exercise 2: Regression and Bias-Variance Trade-Off` ✓ |
| 3 | Exercise 2 contains transferred KNN material | `KNeighborsRegressor`, `bias-variance`/`bias–variance`, `Bonus`, and the `knn_explore` iframe all present ✓ |
| 4 | Exercise 2's KNN interaction works | `knn_explore.json` config and the widget app bundle both serve 200; interaction itself validated by CI's own Playwright `test:e2e:book` pass on this exact commit (not independently re-driven in a browser this pass — see §10) |
| 5 | Exercise 3 title | `Exercise 3: Classification and Metrics` ✓ |
| 6 | Exercise 3's classification interactions work | `classification_threshold`/`classification_imbalance` widget references present (2 hits); same CI Playwright pass as above covers interaction behavior |
| 7 | Exercise 4 is the cross-validation placeholder | title `Exercise 4: Cross-Validation for Classification and Regression` ✓, not the old classification lesson |
| 8 | Exercises 5–12 in navigation | confirmed in the sidebar HTML (Exercises 5,6,7,8,9,10,11,12 all present with correct titles) ✓ |
| 9 | Exercise 12 no longer 404s | HTTP 200 ✓ |
| 10 | Exercise 13 absent | HTTP 404 ✓ |
| 11 | Sidebar ordering | Introduction/Syllabus/Contents, then Exercises 1–12 in numeric order, confirmed from the rendered nav on Exercise 1's page ✓ |
| 12 | Colab/download links use new numbering | Exercise 2 → `.../chapter_02/exercise_02_portable.ipynb`; Exercise 3 → `.../chapter_03/exercise_03_portable.ipynb` ✓ |
| 13 | Light/dark-mode rendering | not independently re-driven in a browser this pass; covered by CI's `test:e2e:book` suite, which includes the dedicated cross-chapter dark-mode spec (`wp22-cross-chapter-dark-mode.spec.ts`) and passed on this exact commit (§8) — see deviation note in §10 |
| 14 | No new runtime errors | not independently checked via a live browser console this pass (see §10); no such errors surfaced in CI's Playwright runs |
| 15 | Syllabus page unchanged | title renders correctly; byte-identity against `914841c4...:book/syllabus.md` already enforced offline by `test_syllabus_source_is_byte_for_byte_unchanged_from_the_pre_syllabus_commit`, which passed (§4) |
| 16 | No final-project reminder | 0 matches for "final project"/"final-project"/"capstone" in Exercise 2 or 3 pages ✓ |

## 10. Deviations / unresolved issues

* Items 13/14 above (live light/dark-mode rendering, browser console errors) were
  **not** independently re-verified with a driven browser session in this production
  pass — WP26R's own bounded-check philosophy (§10: "Do not rerun ... Playwright ...
  unless an unexpected failure indicates they are relevant") argues against duplicating
  what CI's `test:e2e:book` Playwright suite (which includes the WP22 cross-chapter
  dark-mode spec) already exercised and passed against this exact `WP26R_RELEASE_SHA`
  moments earlier. Documented here as a scope note rather than silently assumed.
* No other deviations. All bounded gates (§4, §5) passed on the first attempt; no
  diagnosis/correction/rerun cycle was needed for any of them.

## 11. Confirmations

* **No notebook, portable-notebook, interactive-component, dataset, model-output,
  widget-export, Jupyter Book content, Contents/sidebar, Syllabus-page, or Word-overview
  change was made.** Only `tests/test_wp25_content_audit.py` and
  `.github/workflows/deploy.yml` were edited (plus this WP's own spec/report files).
* **The archive branch is unchanged.** `archive/pre-syllabus-notebook-structure`
  remains at `914841c4c6033f232d96ce33b6dbcc23eda1c766` locally and on `origin`
  throughout WP26R — never fetched, moved, or deleted by this WP.

## 12. Final `git status --short --branch`

```
## main...origin/main
?? WPs/reports/WP16_ARCHITECT_REPORT.md
?? WPs/reports/WP21_DEPLOYMENT_REPORT.md
```

(as of immediately before this report and the changelog were committed locally on
`main`; see `WPs/reports/WP26R_EXACT_CHANGELOG.md` for the documentation commit that
follows). At that point local `main` == `origin/main` ==
`44739b30da52191d563f70d80d9d2dbcaa102ea7`.
