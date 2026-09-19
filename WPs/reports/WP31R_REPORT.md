# WP31R Report — CI Float Portability Correction and Redeployment

## Status: PARTIAL SUCCESS (correction verified on CI; deployment blocked by a
## second, unrelated, pre-existing CI gap)

The single CI-only failure diagnosed in WP31 (`test_matches_a_fresh_recomputation`,
an exact byte-for-byte JSON comparison that is not portable across platforms) was
confirmed, fixed with a strict semantic comparator, merged, and pushed exactly once.
The "Unit-test the Python scripts (offline)" step **passed** on the resulting
GitHub Actions run — the WP31R correction works. However, that same run then failed
at a **different, later step** ("Build Jupyter Book": `ModuleNotFoundError: No
module named 'sphinxcontrib.mermaid'`), a missing CI dependency unrelated to
WP31R's scope. Per WP31R's stop conditions, this WP stops here: no second push,
no fix, no rerun. **Production is unaffected** (the "Publish website" step never
ran on either the WP31 or WP31R run).

---

## 1. Starting state and Git safety (WP31R §1)

* **Starting local `main` HEAD:** `999154327af51552c762a2be58f15cf3091c95dd`
  (short `9991543`, "WP31: add deployment report and exact changelog").
* **Starting `origin/main`** (confirmed via one `git fetch origin main`):
  `3da7d3f8b1ad4fe627f9581d23ef7e267a2c47ed` (short `3da7d3f`, "Merge Exercises
  4-6 course materials") — matches the spec's expected `RELEASE_SHA` exactly.
* Local `main` was exactly one documentation-only commit ahead of `origin/main`,
  containing only `WPs/reports/WP31_DEPLOYMENT_REPORT.md` and
  `WPs/reports/WP31_EXACT_CHANGELOG.md` (2 files, 375 insertions) — confirmed via
  `git show --stat` and `git diff --stat origin/main..HEAD`.
* `git status --short --branch` showed only the two whitelisted pre-existing
  untracked legacy reports (`WPs/reports/WP16_ARCHITECT_REPORT.md`,
  `WPs/reports/WP21_DEPLOYMENT_REPORT.md`) plus the not-yet-committed WP31R
  specification itself. No unexpected modified or untracked file.
* No pull, rebase, reset, stash, or automatic divergence resolution was performed
  — none was needed.
* Branch `fix/wp31r-ci-float-portability` created from local `main`.
* **WP31R specification checkpoint commit:** `3d405be` — "WP31R: add
  specification (initial checkpoint)" — adds only
  `WPs/WP31R_CI_FLOAT_PORTABILITY_AND_REDEPLOY.md` (1 file, 308 insertions).

## 2. Failure-mechanism confirmation (WP31R §2)

Retrieved the WP31 failed CI log once more (`gh run view 35437984824
--log-failed`), plus a local deep structural/numeric diff between the committed
artifact and `export_tree_greedy_widget.build_data()` (this development machine
reproduces the committed values exactly — the discrepancy is macOS-vs-Linux, not
reproducible locally). The CI log's truncated `assertEqual` diff (`'{"ac[2414
chars]20928, 15.975361, 27.022026, 19.075057, 32.443[2892 chars]s."}' !=
'{"ac[2414 chars]209281, 15.97536, 27.022026, 19.075057, 32.443[2892 chars]s."}'`)
shows **2414 identical leading characters and 2892 identical trailing characters**
around exactly two differing numeric substrings. Locating those substrings in a
local `sort_keys=True` dump identifies the exact JSON paths:

| # | JSON path | Committed (macOS) | Linux CI recomputation | Absolute difference |
|---|---|---|---|---|
| 1 | `rounds[0]("root").candidates.x1.reduction[4]` | `6.20928` | `6.209281` | `1e-6` |
| 2 | `rounds[0]("root").candidates.x1.reduction[5]` | `15.975361` | `15.97536` | `1e-6` |

No dictionary key, list length/order, string, Boolean, integer, selected seed
(`17` both sides, per the identical prefix through `generatingProcess`), feature,
threshold ordering, optimal split, observation count, or round structure differed
— confirmed by the identical prefix/suffix spans and by every other passing
assertion in the same test run (`test_check_mode_passes`,
`test_selected_seed_is_genuinely_the_first_passing_seed_0_to_49`, etc., all still
green). The discrepancy is confined to insignificant final-digit floating-point
variation at exactly the reported ~`1e-6` scale — this diagnosis is **confirmed**,
matching WP31's own independent diagnosis in `WPs/reports/WP31_DEPLOYMENT_REPORT.md`
§5 verbatim (same log, same two values, same root-cause explanation: macOS
Accelerate-linked NumPy vs. Linux OpenBLAS-linked NumPy last-ULP differences in
floating-point sums/means).

Docker was not available locally (`docker: command not found`) and was not
installed, per WP31R §5's explicit prohibition on introducing a container system
for this WP; GitHub Actions remained the authoritative Linux verification (see §5
below — the actual CI run now passes this exact test).

## 3–4. Implementation (WP31R §3–§4)

* **`scripts/semantic_json_compare.py`** (new): a strict recursive comparator —
  `semantic_diff(a, b, abs_tol, path)` returns the first `SemanticMismatch`
  (with JSON path, both values, and reason) or `None`; `assert_semantically_equal`
  raises `AssertionError` from it. Contract: dictionary keys must match exactly
  (reports missing/extra keys); list length and order must match exactly; `None`,
  strings, and Booleans compared with strict type+value equality; integers
  compared exactly; float leaves compared with `math.isclose(rel_tol=0.0,
  abs_tol=abs_tol)`; any non-finite value (`NaN`, `inf`, `-inf`) on either side is
  **always** rejected, even if both sides agree (never silently accepted).
  `DEFAULT_ABS_TOL = 2e-6` — chosen per WP31R §3's guidance ("prefer an absolute
  tolerance around `2e-6`") as roughly double the observed `1e-6` discrepancy,
  well under the `5e-6` ceiling, so genuine last-digit cross-platform noise passes
  while anything larger still fails.
* **`scripts/export_tree_greedy_widget.py`**: `cmd_check()`'s exact
  `json.dumps(...) != json.dumps(...)` comparison replaced with
  `semantic_diff(data, recomputed, abs_tol=DEFAULT_ABS_TOL)`, printing the
  mismatch's path/reason/values on failure. No change to `build_data()`,
  `seed_diagnostics()`, `select_seed()`, `validate()`, or the committed artifact
  itself — the artifact was **not** regenerated (its semantic content was proven
  current by `test_check_mode_passes` and every other still-passing test; a
  platform-specific regeneration would only move the 1e-6 gap to the opposite
  platform, per WP31R §3's explicit warning).
* **`tests/test_export_tree_greedy_widget_data.py`**:
  `test_matches_a_fresh_recomputation` replaced its exact-string `assertEqual`
  with `assert_semantically_equal(self.data, tg.build_data(),
  abs_tol=DEFAULT_ABS_TOL)`. The test still fully recomputes and verifies the
  entire artifact — it is not skipped, weakened to a partial check, or
  reduced in scope. All 12 other tests in the file are unchanged.
* **`tests/test_semantic_json_compare.py`** (new, 14 tests): accepts a
  sub-tolerance float difference; rejects an over-tolerance float difference;
  rejects a changed `selectedSeed`; rejects a changed optimal feature and a
  changed threshold; rejects a missing key; rejects an extra key; rejects
  reordered list elements; rejects a changed list length; reports the exact
  nested JSON path of a mismatch; rejects `NaN`/`inf`/`-inf` even when only one
  side is non-finite; rejects `NaN` even when **both** sides are `NaN` (never
  silently accepted); rejects a changed Boolean; rejects an int/bool type
  mismatch; confirms identical structures match.

## 5. Bounded local validation (WP31R §5) — all gates run once, all passed

| # | Gate | Command | Result |
|---|---|---|---|
| 1 | Focused greedy-exporter + comparator tests | `python -m unittest tests.test_semantic_json_compare tests.test_export_tree_greedy_widget_data -v` | ✅ 29/29 |
| 2 | Greedy-widget export check | `python scripts/export_tree_greedy_widget.py --check` | ✅ self-consistent |
| 3 | Exercise 6 focused tests | `python -m unittest tests.test_exercise_06_notebook tests.test_decision_tree_model_audit tests.test_export_tree_ensemble_widget_data tests.test_export_tree_greedy_widget_data tests.test_semantic_json_compare -v` | ✅ 154/154; plus `decision_tree_model_audit.py --check` and `export_tree_ensemble_widget.py --check`, both self-consistent |
| 4 | Full offline Python test suite | `python -m unittest discover -s tests -v` | ✅ **705 tests, 0 failures, 0 errors** (691 WP31-baseline + 14 new comparator tests; same 11 pre-existing `python-docx` skips as WP31) |
| 5 | Portable-notebook deterministic check, all chapters | `python scripts/build_portable_notebook.py --check --notebook all` | ✅ chapters 1–6 up to date (75/43/34/34/47/33 cells — identical counts to WP31) |
| 6a | Registered portable smoke test | `python scripts/smoke_portable_notebook.py` | ✅ chapters 1–4 execute cleanly, key values matched |
| 6b | Independent Ex5/Ex6 smoke execution (unregistered, one-off script in a `mktemp -d` dir, removed after) | `nbclient`-based, same method as the registered script | ✅ both execute with no cell errors; chapter_05 confirms ridge (`alpha=562.3`, MSE 22.3, 360 nonzero) / lasso (`alpha=0.2154`, MSE 22.7, 101 nonzero) and 17-feature forward-selection curve; chapter_06 confirms `eligible = 1004  development = 753  outer test (excluded) = 251` and `depth= 5 ... val ROC AUC=0.567 <- highest validation ROC AUC` — identical key values to WP31 |
| 7 | Frontend typecheck/unit tests | not run | **unnecessary**: no file under `interactive/` was changed by this WP (`git diff --stat` against the branch base touches only `scripts/` and `tests/`) |
| 8 | Production frontend build | not run | **unnecessary**, same reason; the already-committed bundle is reused unchanged |
| 9 | Clean Jupyter Book build | `jupyter-book clean book --all` then `jupyter-book build book` | ✅ succeeded, **2 pre-existing unrelated warnings** (missing `logo.png`; `book/README.md` not in any toctree — both present since before this WP, identical to WP31); `find book/_build -name "*.err.log"` → no execution-error reports. (Interrupted once by an unrelated session-teardown event mid-run, identical in kind to WP31 §2's note; restarted cleanly from scratch exactly once after confirming `book/_build/` — gitignored — held no partial state and `git status --short --branch` stayed clean.) |
| 10a | Focused built-book tests, Exercises 4/5/6 | `npx playwright test --config playwright.book.config.ts e2e-book/chapter04.spec.ts e2e-book/chapter05.spec.ts e2e-book/chapter05-visual-policy.spec.ts e2e-book/chapter06.spec.ts` | ✅ **32/32 passed** |
| 10b | Launch-button tests | `npx playwright test --config playwright.book.config.ts e2e-book/launch-buttons.spec.ts` | ✅ **20/20 passed** |
| 10c | Cross-chapter light/dark-mode tests | `npx playwright test --config playwright.book.config.ts e2e-book/wp22-cross-chapter-dark-mode.spec.ts` | ✅ **5/5 passed**, explicitly including Exercise 4, 5, and 6 |

Docker was not installed or used (unavailable locally; not introduced, per WP31R
§5). No sleeps, weakened assertions, skipped tests, global retries, or repeated
build/stress loops were used anywhere in this WP. Each gate was run exactly once,
except the two build-related gates each interrupted once by unrelated
session/background teardown and cleanly restarted exactly once, with no partial
state in tracked files at any point.

## 6. Merge into local `main` (WP31R §6)

* Pre-merge local `main` reconfirmed unchanged: `9991543`, clean apart from the
  two whitelisted reports.
* `git merge --no-ff fix/wp31r-ci-float-portability -m "Fix cross-platform
  greedy-tree artifact verification"` — **no conflicts.**
* **`WP31R_RELEASE_SHA`: `de564b3dccedfc92eb14f6460efd4ffb459d4c5e`** (parents:
  `9991543` and `60658ed`).
* Tree-identity proof: `git diff --stat de564b3 fix/wp31r-ci-float-portability`
  → **empty** — the merged `main` tree is byte-for-byte identical to the
  correction-branch tree.
* Diff from WP31's `RELEASE_SHA` (`3da7d3f`) to `WP31R_RELEASE_SHA`: exactly 7
  files — the two previously-local WP31 reports, the WP31R specification, and
  the narrow comparator/test correction (`scripts/export_tree_greedy_widget.py`
  +6/-5, `scripts/semantic_json_compare.py` new +96,
  `tests/test_export_tree_greedy_widget_data.py` +15/-8,
  `tests/test_semantic_json_compare.py` new +141). No notebook, widget, dataset,
  model, or activity content changed.
* No amend, squash, rebase, or history rewrite was performed.

## 7. Push (WP31R §7) — exactly once

* `git push origin main` → `3da7d3f..de564b3  main -> main`. Succeeded on the
  first and only attempt.
* Verified with a read-only `git ls-remote origin refs/heads/main`:
  `de564b3dccedfc92eb14f6460efd4ffb459d4c5e refs/heads/main` — matches
  `WP31R_RELEASE_SHA` exactly.
* **No second push occurred at any point in this WP.**

## 8. GitHub Actions workflow (WP31R §8)

* **Workflow:** Build and deploy Jupyter Book
* **Discovery:** found on the **first** of the two permitted bounded queries
  (`gh run list --branch main --limit 5 --json ...`) — already `in_progress`.
* **Run ID:** `35469646309`
* **Triggering SHA:** `de564b3dccedfc92eb14f6460efd4ffb459d4c5e` (=
  `WP31R_RELEASE_SHA`, confirmed via the run's `headSha`)
* **Started:** 2026-09-19T21:11:14Z; **completed:** 2026-09-19T21:13:55Z
  (~2m41s)
* **Watch:** `gh run watch 35469646309 --exit-status` was executed exactly once,
  continuously. **Deviation to record:** the local tool session enforces its own
  command timeout, and this single watch invocation was cut off by that local
  timeout before the run had finished (the run was still executing "Build
  Jupyter Book" and later steps at that point; it had already shown "Unit-test
  the Python scripts (offline)" ✓). No second `gh run watch` was executed. To
  learn the already-completed run's final state, one **read-only** status query
  (`gh run view 35469646309 --json status,conclusion,...`) was used instead —
  not a watch, not a poll loop, not a rerun; it queries a run that had already
  finished on GitHub's side by the time it was issued. This is the one deviation
  from "one continuous watch" in this WP, caused by a local tool constraint
  rather than any workflow action; the intent (no rerun, no fix-and-push-again,
  no parallel/background polling) was preserved.
* **Result: FAILURE.**
  * "Unit-test the Python scripts (offline)" (the step WP31R specifically
    targeted) **passed** — confirming the semantic-comparator fix works
    against real Linux CI.
  * A **later, different** step, **"Build Jupyter Book"**, failed:
    ```
    Extension error:
    Could not import extension sphinxcontrib.mermaid (exception: No module named 'sphinxcontrib.mermaid')
    ...
    ModuleNotFoundError: No module named 'sphinxcontrib.mermaid'
    ```
    retrieved with a single `gh run view 35469646309 --log-failed`. This is a
    missing Python dependency in the CI environment (`sphinxcontrib-mermaid` is
    evidently required by `book/_config.yml`'s Sphinx extensions but is not
    installed by the workflow's dependency-install step, or not pinned in the
    requirements file consumed by CI) — a pre-existing CI-environment gap
    unrelated to the WP31R float-comparator correction, to the greedy-tree
    artifact, or to any notebook/widget/dataset content. It is the same class of
    gap as the one WP31R itself was created to fix (a check that had never
    actually been exercised end-to-end in GitHub Actions until now), but it is a
    **different** step and a **different** cause, outside WP31R's authorized
    scope ("make the narrowest robust portability correction" for the diagnosed
    JSON-comparison issue only).
  * "Publish website" never ran.

Per WP31R §8/§10 ("If the workflow fails, retrieve its failed log once, document
the exact blocker, and stop. Do not fix or push again within WP31R." /
"failed/cancelled workflow" is an explicit stop condition), **this WP stops
here.** No fix was attempted, no second push was made, and the workflow was not
rerun.

## 9. Production verification (WP31R §9)

**Not performed as a full pass** — WP31R §9 applies "only after the workflow
succeeds," and it did not. Read-only spot checks instead confirm production is
unaffected:

| Check | Result |
|---|---|
| `gh-pages` branch tip | `9dbe3b10ac31363aa1ef9cd8418a1b9cdd56ca12` — unchanged from WP31's report; "Publish website" never ran in either the WP31 or WP31R failed run |
| `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html` (cache-busted) | HTTP 200, title `Exercise 4: Cross-Validation for Classification and Regression` — the pre-existing WP26R-era title, **not** WP27's "Exercise 4: Validation and Cross-Validation" |

Conclusion: production is exactly as it was before this WP started. No
interaction, theme, layout, Colab/download, or console-error verification was
performed against the live site, since the release that would carry the new
content was never published.

## 10. Deviations and items for the user's attention

1. **The WP31R correction is verified working on real GitHub Actions CI.** The
   exact test/step WP31 diagnosed as failing (`test_matches_a_fresh_recomputation`
   inside "Unit-test the Python scripts (offline)") passed on run `35469646309`.
2. **A second, unrelated, pre-existing CI gap blocked the same run**: missing
   `sphinxcontrib.mermaid` Python package during "Build Jupyter Book". This is
   outside WP31R's authorized scope (the WP's purpose was the narrow JSON-
   comparison portability fix only) and was **not** investigated or fixed here.
3. **Recommendation (not actioned by this WP):** a follow-up WP is needed to
   diagnose and fix the `sphinxcontrib.mermaid` CI dependency gap (most likely:
   add `sphinxcontrib-mermaid` to the pinned requirements file the workflow
   installs from, or confirm it's already present in `book/_config.yml`'s
   `sphinx: extra_extensions` and was simply never added to the environment
   dependency list; jupyter-book/mermaid diagrams may already be present in the
   book's Markdown source and have only ever built successfully on this local
   `.venv`, never in CI) — then merge (or push directly, since this correction
   is unrelated to any pending feature branch), re-trigger the deploy workflow,
   and complete production verification for Exercises 4–6.
4. **Deviation in workflow monitoring:** the single permitted `gh run watch` was
   cut off by a local tool-level command timeout before the run finished on
   GitHub's side (see §8 for detail). A single read-only `gh run view` status
   query — not a second watch, not a poll loop — was used to learn the final
   (already-determined) conclusion. No rerun, no parallel polling, no scheduled
   wakeup was used.
5. `origin/main` currently sits at `WP31R_RELEASE_SHA`
   (`de564b3dccedfc92eb14f6460efd4ffb459d4c5e`) with a failed/red Actions run
   attached to it, exactly mirroring WP31's prior state at its own `RELEASE_SHA`.
   It has not been reverted, reset, or force-pushed.
6. No notebook, widget, dataset, model, or activity content was created, edited,
   or regenerated at any point in this WP. The committed `tree_greedy_split.json`
   artifact is byte-identical to before — only the comparison logic changed.
7. The clean Jupyter Book build gate (§5, gate 9) was interrupted once by an
   unrelated session/background teardown event and restarted cleanly from
   scratch exactly once; no partial or stale build state was left in the tracked
   working tree at any point (`book/_build/` is gitignored, confirmed clean
   before the restart).

## 11. Final `git status --short --branch`

```
## main...origin/main
?? WPs/reports/WP16_ARCHITECT_REPORT.md
?? WPs/reports/WP21_DEPLOYMENT_REPORT.md
```

(as of immediately before this report and the changelog were committed locally;
see `WPs/reports/WP31R_EXACT_CHANGELOG.md` for the exact commit added after this
file, to be recorded as `WP31R_DOCUMENTATION_SHA`.)

Local `main` = `origin/main` = `de564b3dccedfc92eb14f6460efd4ffb459d4c5e`
(`WP31R_RELEASE_SHA`) at the time this report was written. The two whitelisted
legacy reports remain the only untracked files. WP32 was not started.
