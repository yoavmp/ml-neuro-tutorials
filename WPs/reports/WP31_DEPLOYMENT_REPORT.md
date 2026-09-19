# WP31 Deployment Report — Deploy Exercises 4–6

## Status: FAILURE (production unaffected; `main` merged and pushed, deploy workflow failed pre-build)

`main` was merged and pushed exactly once as authorized. The "Build and deploy Jupyter
Book" workflow run for the resulting commit failed at the **"Unit-test the Python
scripts (offline)"** step — before "Build Jupyter Book" and before "Publish website"
ever ran. **The live production site was not touched and remains on its pre-WP31
content** (verified directly against production, see §8). Per WP31 §7/§9, on a
workflow failure the correct action is: retrieve logs once, summarize, stop — no
rerun, no cancel, no speculative fix, no second push. That is exactly what was done.

---

## 1. Starting state verification (WP31 §1, §3)

* **Starting branch:** `fix/wp30r-classification-holdout`
* **Starting feature-branch HEAD (before the WP31 checkpoint):**
  `343630792ac90d07effa083e1e5d51627cb8326e` (short `3436307`, "WP30R: restrict
  classification-depth audit to Exercise 3's development partition") — matches the
  spec's expected hint exactly.
* **`git status --short --branch` at the start:** only the two whitelisted
  pre-existing untracked reports (`WPs/reports/WP16_ARCHITECT_REPORT.md`,
  `WPs/reports/WP21_DEPLOYMENT_REPORT.md`) plus the not-yet-committed WP31
  specification itself. No unexpected modified or untracked file. Nothing reset,
  stashed, deleted, or overwritten.
* **WP31 specification commit (checkpoint):** `6f18ac6fcac4512404f8e8e9258e268b92eec974`
  (short `6f18ac6`) — "WP31: add specification (initial checkpoint)" — adds only
  `WPs/WP31_DEPLOY_EXERCISES_4_TO_6.md`, 1 file changed, 284 insertions.

### Ancestry verification (WP31 §3), after one `git fetch origin main`

| # | Check | Result |
|---|---|---|
| 1 | `origin/main` still at expected `44739b3...` | ✅ `44739b30da52191d563f70d80d9d2dbcaa102ea7` |
| 2 | Local `main` exactly one documentation commit ahead, `74c9a9a...` | ✅ `74c9a9a15091059dd591982422f2fece0e0993e8` — "WP26R: document CI archive-audit fix and successful redeploy" |
| 3 | `origin/main → main` diff is documentation-only | ✅ `git diff --stat origin/main main` → only `WPs/reports/WP26R_EXACT_CHANGELOG.md` and `WPs/reports/WP26R_REPORT.md`, 406 insertions, 0 deletions |
| 4 | `origin/main` is an ancestor of local `main` | ✅ `git merge-base --is-ancestor origin/main main` → true |
| 5 | Local `main` is an ancestor of the WP31 checkpoint | ✅ `git merge-base --is-ancestor main 6f18ac6...` → true; `git merge-base main fix/wp30r-classification-holdout` = `74c9a9a...` (local `main` itself) |
| 6 | Branch contains the complete linear WP27→WP27R→WP28→WP29→WP30→WP30R chain and reports | ✅ confirmed via `git log --oneline main..fix/wp30r-classification-holdout` (52 commits, all prefixed WP27/WP27R/WP28/WP29/WP30/WP30R, plus the WP31 checkpoint; see graph below) |
| 7 | No unrelated commit/file in `main..fix/wp30r-classification-holdout` | ✅ every commit in the range belongs to WP27–WP30R or WP31; no foreign content |

```
*   3da7d3f (HEAD -> main, origin/main) Merge Exercises 4-6 course materials
|\
| * 6f18ac6 (fix/wp30r-classification-holdout) WP31: add specification (initial checkpoint)
| * 3436307 WP30R: restrict classification-depth audit to Exercise 3's development partition
| * 500269f WP30R: add specification (initial checkpoint)
| * 6b76164 WP30: Exercise 6 clarity and activity refinements
| * 29f7c94 WP30: add specification (initial checkpoint)
| * 5998e04 WP29: add report and exact changelog
| ... (WP29, WP28, WP27R, WP27 chain, 52 commits total) ...
|/
* 74c9a9a WP26R: document CI archive-audit fix and successful redeploy
* 44739b3 Merge WP26R CI archive-audit correction
```

No pull, rebase, reset, cherry-pick, stash, or automatic divergence resolution was
performed at any point — none was needed, since every check above matched the
spec's expected state exactly.

## 2. Bounded pre-deployment validation (WP31 §4) — all gates run once, all passed

| # | Gate | Command | Result |
|---|---|---|---|
| 1a | Ex4 validation audit check | `python scripts/wp27_validation_audit.py --check` | ✅ self-consistent |
| 1b | Ex4 widget-data export check | `python scripts/export_wp27_widget_data.py --check` | ✅ all 3 artifacts up to date |
| 1c | Ex5 regularization audit check | `python scripts/regularization_model_audit.py --check` | ✅ self-consistent |
| 1d | Ex5 widget-data export check | `python scripts/export_regularization_widget.py --check` | ✅ valid and canonical |
| 1e | Ex6 decision-tree audit check | `python scripts/decision_tree_model_audit.py --check` | ✅ self-consistent; classification curve confirms `n=753`, best depth 5, val ROC AUC 0.567, margin 0.034, outer test (251) excluded |
| 1f | Ex6 ensemble widget-data export check | `python scripts/export_tree_ensemble_widget.py --check` | ✅ self-consistent |
| 1g | Ex6 greedy-split widget-data export check | `python scripts/export_tree_greedy_widget.py --check` | ✅ self-consistent |
| 2 | Portable-notebook deterministic checks, all implemented chapters | `python scripts/build_portable_notebook.py --check --notebook all` | ✅ chapters 1–6 all up to date (75/43/34/34/47/33 cells) |
| 3 | Registered portable smoke test | `python scripts/smoke_portable_notebook.py` | ✅ chapters 1–4 (only chapters currently registered) all execute cleanly with matching key values |
| 4 | Independent Ex5/Ex6 portable-notebook smoke execution (unregistered) | one-off `nbclient`-based script, copying each notebook into its own `tempfile.TemporaryDirectory()`, same method as the registered script | ✅ both execute cleanly with no cell errors; chapter_05 confirms ridge/lasso alpha curves and 17-feature stepwise selection; chapter_06 confirms `eligible = 1004  development = 753  outer test (excluded) = 251` and `depth= 5 ... val ROC AUC=0.567 <- highest validation ROC AUC` |
| 5 | Full offline Python test suite | `python -m unittest discover -s tests -v` | ✅ **691 tests, 0 failures, 0 errors** (11 pre-existing unrelated `python-docx`-not-installed skips) |
| 6 | Frontend typecheck | `npm run typecheck` (in `interactive/`) | ✅ clean, no errors |
| 7 | Frontend unit-test suite | `npm run test:unit` (in `interactive/`) | ✅ 27 files, **359 tests passed** |
| 8 | Production frontend build | `npm run build` (in `interactive/`) | ✅ built in 3.65s; pre-existing >500kB chunk-size advisory only (not an error); `git status` confirmed the build output is byte-identical to what was already committed |
| 9 | Clean Jupyter Book build | `jupyter-book clean book --all` then `jupyter-book build book` | ✅ succeeded, **2 pre-existing unrelated warnings** (missing `logo.png`; `book/README.md` not in any toctree — both present before this WP); confirmed with `find book/_build -name "*.err.log"` → no execution-error reports |
| 10 | Focused built-book tests, Exercises 4/5/6 | `npx playwright test --config playwright.book.config.ts e2e-book/chapter04.spec.ts e2e-book/chapter05.spec.ts e2e-book/chapter05-visual-policy.spec.ts e2e-book/chapter06.spec.ts` | ✅ **32/32 passed** |
| 11 | Launch-button tests | `npx playwright test --config playwright.book.config.ts e2e-book/launch-buttons.spec.ts` | ✅ **20/20 passed** (chapters 1–6, placeholder, and no-mapping cases) |
| 12 | Cross-chapter light/dark-mode tests | `npx playwright test --config playwright.book.config.ts e2e-book/wp22-cross-chapter-dark-mode.spec.ts` | ✅ **5/5 passed**, explicitly including Exercise 4 (validation-stability/lock-test/nested-cv), Exercise 5 (feature-set comparison + regularization), and Exercise 6 (one-tree-or-many) |
| 13 | Narrow-viewport checks, new activities | `npx playwright test e2e/nested-cv-explorer.spec.ts e2e/validation-lock-test.spec.ts e2e/validation-stability.spec.ts e2e/regularization-explore.spec.ts e2e/tree-greedy-split.spec.ts e2e/tree-ensemble-compare.spec.ts --grep "390 px"` | ✅ **10/10 passed** (390px, no horizontal document scroll) |
| extra | Deploy-workflow's additional offline gate not in the WP31 list: committed ABIDE data artifacts | `python scripts/export_widget_data.py --check --artifact all` | ✅ all 3 artifacts (histogram, retention, table-inspection) valid and canonical |

Notes:
* `npm audit --omit=dev` (also present in `deploy.yml`) was **not** reproduced locally:
  it is not marked `(offline)` in the workflow and genuinely queries the npm registry
  over the network, so it does not meet WP31 §4's "additional mandatory **offline**
  gate" criterion. It ran as part of the CI workflow itself and passed there (see §3).
* No sleeps, weakened assertions, skipped tests, global retries, or repeated build
  loops were used anywhere in this WP. Each gate was run exactly once. Two of the
  long-running gates (the independent Ex5/Ex6 portable-notebook smoke execution and
  the clean Jupyter Book build) were interrupted mid-run by session teardown events
  unrelated to the gate itself (the harness killed the background process, not a
  test/build failure); each was restarted cleanly from scratch exactly once after
  confirming no partial state had leaked into the tracked working tree (`book/_build/`
  is gitignored; `git status --short --branch` stayed clean throughout).

## 3. Merge into local `main` (WP31 §5)

* Pre-merge local `main`: `74c9a9a15091059dd591982422f2fece0e0993e8` (reconfirmed, one
  commit ahead of `origin/main`, clean apart from the two whitelisted reports).
* `git merge --no-ff fix/wp30r-classification-holdout -m "Merge Exercises 4-6 course
  materials"` — **no conflicts.**
* **`RELEASE_SHA`: `3da7d3f8b1ad4fe627f9581d23ef7e267a2c47ed`** (parents:
  `74c9a9a15091059dd591982422f2fece0e0993e8` and
  `6f18ac6fcac4512404f8e8e9258e268b92eec974`). 110 files changed, 43,860 insertions,
  410 deletions relative to prior `main`.
* Tree-identity proof: `git diff --stat RELEASE_SHA fix/wp30r-classification-holdout`
  → **empty** — the merged `main` tree is byte-for-byte identical to the WP31
  checkpoint branch tree (history/parentage aside).
* Post-merge `git status --short --branch`: only the two whitelisted legacy reports
  remained untracked.
* No amend, squash, rebase, or history rewrite was performed.

## 4. Push (WP31 §6) — exactly once

* `git push origin main` → `44739b3..3da7d3f  main -> main`. Succeeded on the first
  and only attempt.
* Verified with a read-only `git ls-remote origin refs/heads/main`:
  `3da7d3f8b1ad4fe627f9581d23ef7e267a2c47ed refs/heads/main` — matches `RELEASE_SHA`
  exactly.
* **No second push occurred at any point in this WP.**

## 5. GitHub Actions workflow (WP31 §7)

* **Workflow:** Build and deploy Jupyter Book
* **Discovery:** found on the **first** of the two permitted bounded queries
  (`gh run list --branch main --limit 5 --json ...`) — already `in_progress`, so the
  ~30s-wait/second-query fallback was not needed.
* **Run ID:** `35437984824`
* **Triggering SHA:** `3da7d3f8b1ad4fe627f9581d23ef7e267a2c47ed` (= `RELEASE_SHA`,
  confirmed via the run's `headSha`)
* **URL:** https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/35437984824
* **Started:** 2026-09-19T10:39:10Z; **completed:** 2026-09-19T10:40:36Z (~1m26s)
* **Watched once, continuously**, via `gh run watch 35437984824 --exit-status`, to
  completion. Not rerun, not cancelled, no second watch, no parallel polling, no
  scheduled wakeups.
* **Result: FAILURE**, at step **"Unit-test the Python scripts (offline)"**
  (`python -m unittest discover -s tests -v`). Steps after it ("Check the portable
  notebook is not stale", Playwright installs/tests, "Build Jupyter Book", "Fail on
  notebook execution errors", built-book e2e, portable-notebook smoke test, and
  **"Publish website"**) never ran.

### Failure diagnosis (one diagnosis only, as authorized; no correction attempted)

Retrieved with a single `gh run view 35437984824 --log-failed`. The full local suite
(gate 5 above, 691/691 tests, run twice across this WP: once standalone and once
inside gate 1g's `export_tree_greedy_widget.py --check`) passed cleanly, but the CI
runner (`ubuntu-latest`, Python 3.11.16) failed exactly one test that never ran under
those names/conditions on this development machine (macOS, Python 3.12.7, `.venv`):

```
FAIL: test_matches_a_fresh_recomputation
      (test_export_tree_greedy_widget_data.CommittedArtifact.test_matches_a_fresh_recomputation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../tests/test_export_tree_greedy_widget_data.py", line 36, in test_matches_a_fresh_recomputation
    self.assertEqual(
AssertionError: '{"ac[2414 chars]20928, 15.975361, 27.022026, 19.075057, 32.443[2892 chars]s."}' != '{"ac[2414 chars]209281, 15.97536, 27.022026, 19.075057, 32.443[2892 chars]s."}'
Diff is 16135 characters long. Set self.maxDiff to None to see it.
----------------------------------------------------------------------
Ran 691 tests in 8.204s
FAILED (failures=1, skipped=11)
```

**What this test does** (`tests/test_export_tree_greedy_widget_data.py`,
`CommittedArtifact.test_matches_a_fresh_recomputation`): it loads the committed
`book/_static/widgets/data/tree_greedy_split.json` artifact, calls
`export_tree_greedy_widget.build_data()` to recompute the same synthetic
16-observation dataset and greedy-split audit **fresh, in-process**, and asserts the
two `json.dumps(..., sort_keys=True)` strings are **byte-for-byte equal** — an exact
string comparison, not a numeric-tolerance one.

**Root cause (diagnosed, not fixed):** the two committed decimal values differ from
the runner's freshly recomputed values only in their last displayed digit
(`...20928` vs `...209281`; `15.975361` vs `15.97536`) — a floating-point
last-ULP-level discrepancy consistent with a platform/BLAS difference between this
development machine (macOS arm64, Python 3.12.7, Apple Accelerate-linked NumPy) and
the GitHub Actions runner (`ubuntu-latest`, Python 3.11.16, OpenBLAS-linked NumPy).
The dataset generation and greedy-split search involve floating-point sums/means
whose bit-exact result can legitimately differ by one ULP across BLAS
implementations, and `test_matches_a_fresh_recomputation` (unlike
`test_check_mode_passes` in the same file, gate 1g, which passed) asserts exact
string equality rather than a numeric tolerance. **This is the first time this test
file has ever executed inside GitHub Actions CI** — WP29/WP30/WP30R validated it only
on this development machine, exactly analogous to the WP26 archive-branch CI gap
that WP26R diagnosed and fixed the same way (see `WPs/reports/WP26_DEPLOYMENT_REPORT.md`
§4, `WPs/reports/WP26R_REPORT.md` §1). This is a **pre-existing CI-environment gap in
a WP29/WP30 test file**, not a defect in the WP27–WP30R notebook/widget content, the
WP31 merge, or the push. Fixing it (e.g. rewriting the assertion to compare parsed
floats with `assertAlmostEqual`/a small tolerance instead of exact JSON strings, or
pinning/documenting the numeric precision contract) is a test-code change to
`tests/test_export_tree_greedy_widget_data.py` — outside WP31's authorization
("deployment-only... must not redesign, edit, regenerate, or otherwise change...
test... content"; §7: "Do not change code, push again, or attempt a repair under
WP31"). No attempt was made to fix it.

## 6. Production verification (WP31 §8)

**Not performed as a full pass** — the deployment did not succeed, so per WP31 §9 no
production interaction/theme/viewport/console/Colab/download verification pass is
called for. Instead, the following read-only spot checks (one `git ls-remote` and one
cache-busted `curl`) confirm production is unaffected and still serving pre-WP31
content:

| Check | Result |
|---|---|
| `gh-pages` branch tip | `9dbe3b10ac31363aa1ef9cd8418a1b9cdd56ca12` — the "Publish website" step never ran in the failed workflow run, so this is the pre-existing tip from the last successful (WP26R) deploy |
| `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html` (cache-busted) | HTTP 200, title `Exercise 4: Cross-Validation for Classification and Regression` — the **old** WP26R-era placeholder title, **not** WP27's "Exercise 4: Validation and Cross-Validation" |

Conclusion: production is exactly as it was before this WP started. No stale-cache
concerns, no partial deployment, no broken links introduced. This is **not** a "stale
content after a successful workflow" stop condition (WP31 §9) — the workflow did not
succeed, so no production change was ever expected.

## 7. Not performed (deployment did not reach these stages)

* Exercises 1–6 live navigation/title verification (§8.1)
* Exercise 4 interaction, nested-CV diagram, Colab/download checks (§8.2)
* Exercise 5 regularization/coefficient-plot, feature-set-material, Colab/download checks (§8.3)
* Exercise 6 tree-diagram, partition-plot, greedy-tree-activity, classification-curve, "One Tree or Many?", fair-comparison-table, Colab/download checks (§8.4)
* Light/dark-mode, narrow-viewport, Plotly-drag-layer, and console-error verification on the live site (§8.5)

All of the above are unaffected only in the sense that production itself did not
change (§6); they were not independently re-verified live because the release that
would carry the new content was never published.

## 8. Deviations and items for the user's attention

1. **The GitHub Actions deployment workflow failed before building or publishing.**
   This is a pre-existing gap in `tests/test_export_tree_greedy_widget_data.py`
   (written and validated only against this development machine during WP29/WP30,
   never previously exercised in GitHub Actions CI) rather than an issue with the
   WP27–WP30R notebook/widget content itself or with this WP's merge/push mechanics.
2. **Recommendation (not actioned by this WP):** a follow-up correction WP is needed
   to make `test_matches_a_fresh_recomputation` CI-portable — e.g. compare the parsed
   numeric fields with a small tolerance (`assertAlmostEqual` / `pytest.approx`-style)
   instead of exact `json.dumps` string equality, mirroring how WP26R resolved the
   analogous archive-branch CI gap — then merge, push `main` again (a genuine second,
   corrective push, out of scope for WP31 as authorized), and re-run this
   verification.
3. `origin/main` currently sits at `RELEASE_SHA`
   (`3da7d3f8b1ad4fe627f9581d23ef7e267a2c47ed`) with a failed/red Actions run attached
   to it. It has not been reverted, reset, or force-pushed — per WP31's explicit
   prohibitions, no such corrective action was taken without authorization.
4. No notebook, widget, data, test, configuration, or workflow content was created,
   edited, or regenerated at any point in this WP (deployment-only, as required). The
   only new files are this report, its accompanying exact changelog, and the WP31
   specification itself (already merged as part of the feature branch).
5. Two long-running local gates (§2, independent Ex5/Ex6 smoke execution and the
   clean Jupyter Book build) were interrupted mid-run by unrelated session/background
   teardown events and were restarted cleanly from scratch exactly once each; no
   partial or stale build state was left in the tracked working tree at any point
   (`book/_build/` is gitignored, confirmed clean before each restart).

## 9. Final `git status --short --branch`

```
## main...origin/main
?? WPs/reports/WP16_ARCHITECT_REPORT.md
?? WPs/reports/WP21_DEPLOYMENT_REPORT.md
```

(as of immediately before this report and the changelog were committed locally; see
`WPs/reports/WP31_EXACT_CHANGELOG.md` for the exact commit added after this file, to
be recorded as `DOCUMENTATION_SHA`.)

Local `main` = `origin/main` = `3da7d3f8b1ad4fe627f9581d23ef7e267a2c47ed`
(`RELEASE_SHA`) at the time this report was written. The two whitelisted legacy
reports remain the only untracked files. WP32 was not started.
