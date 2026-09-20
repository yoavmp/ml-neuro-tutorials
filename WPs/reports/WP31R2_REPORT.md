# WP31R2 Report — Mermaid Dependency Correction and Redeployment

## Status: PARTIAL SUCCESS (Mermaid fix verified working on CI; deployment
## blocked by a third, unrelated, pre-existing CI gap)

WP31R's second CI-environment gap (`ModuleNotFoundError: No module named
'sphinxcontrib.mermaid'` in "Build Jupyter Book", run `35469646309`) was
confirmed, fixed by pinning the missing distribution in `requirements.txt`,
verified in a fresh disposable virtual environment, merged, and pushed exactly
once. The resulting GitHub Actions run **passed "Build Jupyter Book"** — the
WP31R2 correction works. The run then failed at a **later, different, and
unrelated** step: "End-to-end test the built Chapter 1 page" (`npm run
test:e2e:book`), where one dark-mode Plotly test
(`chapter01-dark-mode.spec.ts:121`) timed out waiting for the histogram
plot's render-count attribute; the other 85 of 86 tests in that step passed.
Per WP31R2's stop conditions, this WP stops here: no second push, no fix, no
rerun. **Production is unaffected** ("Publish website" never ran).

---

## 1. Starting state and Git safety (WP31R2 §1)

* **Starting local `main` HEAD:** `7b17c5f61ea88c6f490a15c711cfe77dfed38be1`
  (short `7b17c5f`, "WP31R: document CI float-portability fix and blocked
  redeploy").
* **Starting `origin/main`** (confirmed via one `git fetch origin main`):
  `de564b3dccedfc92eb14f6460efd4ffb459d4c5e` — the WP31R release SHA, matching
  the spec's expected state exactly.
* Local `main` was exactly one documentation-only commit ahead of
  `origin/main`, containing only `WPs/reports/WP31R_REPORT.md` and
  `WPs/reports/WP31R_EXACT_CHANGELOG.md` (2 files, 423 insertions) — confirmed
  via `git show --stat` and `git diff --stat origin/main..HEAD`.
* `git status --short --branch` showed only the two whitelisted pre-existing
  untracked legacy reports plus the not-yet-committed WP31R2 specification
  itself. No unexpected modified or untracked file.
* No pull, rebase, reset, stash, or automatic divergence resolution was
  performed — none was needed.
* Branch `fix/wp31r2-mermaid-dependency` created from local `main`.
* **WP31R2 specification checkpoint commit:** `1274242` — "WP31R2: add
  specification (initial checkpoint)" — adds only
  `WPs/WP31R2_MERMAID_DEPENDENCY_AND_REDEPLOY.md` (1 file, 318 insertions).

## 2. Dependency diagnosis (WP31R2 §2)

* **Failed step and traceback, run `35469646309`** ("Build Jupyter Book"):
  ```
  Extension error:
  Could not import extension sphinxcontrib.mermaid (exception: No module named 'sphinxcontrib.mermaid')
  ...
  ModuleNotFoundError: No module named 'sphinxcontrib.mermaid'
  ```
  Every prior step in that job (through "End-to-end test the standalone
  widget app") completed successfully — confirmed via `gh run view
  35469646309 --json jobs`; no different missing import or configuration
  error precedes it.
* **`.github/workflows/deploy.yml`**: `Set up Python` pins `python-version:
  "3.11"`; `Install Python dependencies` runs exactly `pip install -r
  requirements.txt`. No other Python-dependency install step exists in the
  workflow.
* **Requirements file used by CI:** `requirements.txt` (the only
  requirements/constraints/lock file in the repository; no `constraints.txt`,
  `poetry.lock`, `Pipfile.lock`, or `pyproject.toml` pin list exists). Before
  this WP it contained: `jupyter-book==1.0.4.post1`, `jupyterlab`,
  `ipykernel`, `numpy`, `pandas`, `matplotlib`, `seaborn`, `scikit-learn` —
  **`sphinxcontrib-mermaid` was absent.**
* **`book/_config.yml`** (lines 57–62): `sphinx.extra_extensions` lists
  `sphinxcontrib.mermaid`, with an explanatory comment (WP27) that MyST hands
  the Exercise 4 nested-cross-validation `mermaid` fenced code block to the
  Sphinx directive this extension registers.
* **Local environment inspection** (`.venv`, Python 3.12.7):
  * `pip show sphinxcontrib-mermaid` → `Version: 2.1.1`, `Required-by:`
    *(empty)* — confirming it is not a transitive dependency of anything else
    installed (i.e., it was added to this `.venv` directly/out of band, not
    pulled in automatically by `jupyter-book` or any other pinned package).
  * `python -c "import importlib.metadata as m; print(m.version('sphinxcontrib-mermaid'))"`
    → `2.1.1` (consistent with `pip show`).
  * `python -c "import sphinxcontrib.mermaid; print(sphinxcontrib.mermaid.__file__)"`
    → resolves inside `.venv/lib/python3.12/site-packages/sphinxcontrib/mermaid/__init__.py`.
* **Diagnosis confirmed on all four points:**
  1. `book/_config.yml` intentionally enables `sphinxcontrib.mermaid` — yes.
  2. Local builds succeed only because the package exists in the local
     `.venv` — yes (absent from `requirements.txt`, present locally,
     `Required-by` empty).
  3. The GitHub Actions install path (`pip install -r requirements.txt`) does
     not install it — yes, confirmed by its absence from the file.
  4. No different missing import or configuration error precedes it — yes,
     every step before "Build Jupyter Book" succeeded in run `35469646309`.

## 3. The narrow pinned dependency (WP31R2 §3)

* **Compatibility check before pinning:** `sphinxcontrib-mermaid==2.1.1`
  declares `Requires-Python: >=3.10` (via
  `importlib.metadata.distribution(...).metadata.get('Requires-Python')`).
  CI's `deploy.yml` pins Python **3.11**, which satisfies `>=3.10` — the
  locally-working version is directly compatible with CI's Python version, so
  no fallback to an older/different pin was needed.
* **Change:** added one line, `sphinxcontrib-mermaid==2.1.1`, to
  `requirements.txt`, placed immediately after `jupyter-book==1.0.4.post1` —
  matching the file's existing exact-`==`-pin style (the only other pinned
  line) and grouping it with its related Sphinx/jupyter-book tooling rather
  than the unpinned data-science stack below it.
* No other line in `requirements.txt` changed. No second `pip install`
  command was added to `deploy.yml` (the project already installs a
  canonical requirements file, so none was needed). Jupyter Book, Sphinx,
  MyST, and every other package remain exactly as pinned/unpinned before.
  `sphinxcontrib.mermaid` was **not** removed from `book/_config.yml`.

## 4. Durable dependency-contract test (WP31R2 §4)

Added `tests/test_deploy_dependency_contract.py` (2 tests, both offline):

* `test_mermaid_extension_is_still_declared_and_mapped`: asserts
  `book/_config.yml`'s `sphinx.extra_extensions` still lists
  `sphinxcontrib.mermaid`, and that the extension is present in this test's
  own `EXTENSION_DISTRIBUTIONS` map (guards the guard — if Mermaid support is
  ever removed, this fails loudly rather than letting the coverage below
  silently become a no-op).
* `test_every_enabled_extension_with_a_known_distribution_is_exactly_pinned`:
  parses `.github/workflows/deploy.yml` for its `pip install -r <file>`
  command (not a hardcoded filename — stays correct if the file is renamed),
  parses that file's `name==version` lines, and for every extension in
  `book/_config.yml`'s `extra_extensions` that has a known
  extension→distribution mapping, asserts the distribution is present with
  an exact pin. The failure message names both the missing Sphinx extension
  and the PyPI distribution it requires.
* Deliberately narrow: `EXTENSION_DISTRIBUTIONS` is a small explicit
  dict (currently one entry), not a universal import-to-PyPI resolver.
* Negative-case verification (not committed, done by hand before trusting the
  test): running the parsing helper against the pre-fix requirements content
  confirmed the distribution would have been reported absent, i.e. the test
  would have failed exactly the way WP31R2 needed it to.

## 5. Fresh-environment reproduction (WP31R2 §5)

* **Python version used:** only two Python versions exist on this machine —
  system `/usr/bin/python3` (3.9.6, Apple Command Line Tools) and
  `/usr/local/bin/python3.12` (3.12.7). Neither matches CI's exact 3.11.16.
  **Deviation, as anticipated by WP31R2 §5:** 3.12.7 was used as the closest
  available version — and this was not merely the closer of the two: Python
  3.9.6 does not satisfy `sphinxcontrib-mermaid==2.1.1`'s `Requires-Python:
  >=3.10` at all, so 3.9.6 was not a usable alternative regardless of
  closeness. No new system Python was installed.
* Created a disposable venv with `python3.12 -m venv` inside a `mktemp -d`
  directory (outside the repository and outside `.venv`).
* `pip install -r requirements.txt` (the exact command `deploy.yml` runs) —
  succeeded, no network restriction encountered.
* **Installed versions** (`pip show`): `jupyter-book==1.0.4.post1`,
  `Sphinx==7.4.7` (pulled in by `jupyter-book`, unpinned in
  `requirements.txt`), `sphinxcontrib-mermaid==2.1.1` — `Sphinx`'s own
  `Required-by` field now lists `sphinxcontrib-mermaid` among its dependents,
  confirming the extension is correctly wired into this fresh environment.
* `python -c "import sphinxcontrib.mermaid; print(...__file__)"` — resolved
  inside the **fresh venv's** own `site-packages`, not the repository's
  `.venv`, proving the fix does not depend on anything already installed
  outside `requirements.txt`.
* Full offline Python test suite (`python -m unittest discover -s tests -v`)
  in the fresh venv: **707 tests, 0 failures, 0 errors, 11 skipped**
  (identical count/skips to the normal `.venv` — see §6).
* `jupyter-book build book` using the fresh venv's own binary: **succeeded,
  2 pre-existing unrelated warnings** (missing `logo.png`; `book/README.md`
  not in any toctree — both present since before this WP); `find book/_build
  -name "*.err.log"` → no execution-error reports.
* The temporary venv directory was removed afterward (`rm -rf` on the
  `mktemp -d` path).

## 6. Additional bounded local validation (WP31R2 §6) — all gates run once, all passed

| # | Gate | Command | Result |
|---|---|---|---|
| 1 | Focused dependency-contract test | `python -m unittest tests.test_deploy_dependency_contract -v` | ✅ 2/2 |
| 2 | Full offline Python test suite | `python -m unittest discover -s tests -v` | ✅ **707 tests, 0 failures, 0 errors** (705 WP31R-baseline + 2 new dependency-contract tests; same 11 pre-existing `python-docx` skips) |
| 3 | Greedy-widget export check (WP31R fix retained) | `python scripts/export_tree_greedy_widget.py --check` | ✅ self-consistent |
| 4 | Portable-notebook deterministic check, all chapters | `python scripts/build_portable_notebook.py --check --notebook all` | ✅ chapters 1–6 up to date (75/43/34/34/47/33 cells — unchanged) |
| 5 | Registered portable smoke test | `python scripts/smoke_portable_notebook.py` | ✅ chapters 1–4 execute cleanly, key values matched |
| 6 | Independent Ex5/Ex6 smoke execution (still unregistered; one-off script in a `mktemp -d` dir, removed after) | `nbclient`-based, same method as the registered script | ✅ both execute with no cell errors; identical key values to WP31/WP31R (`eligible = 1004  development = 753  outer test (excluded) = 251`, `depth= 5 ... val ROC AUC=0.567`, ridge/lasso alphas and 17-feature forward-selection curve) |
| 7 | Clean Jupyter Book build (normal `.venv`) | `jupyter-book clean book --all` then `jupyter-book build book` | ✅ succeeded, same 2 pre-existing warnings; no `.err.log` reports. (Both this gate and gate 9 below were run via a detached/`nohup` process because the calling tool's own command timeout is shorter than these builds; each was confirmed to have completed successfully by reading its log after reconnecting, with no partial state in the gitignored `book/_build/` directory.) |
| 8 | Focused built-book tests, Exercises 4/5/6 | `npx playwright test --config playwright.book.config.ts e2e-book/chapter04.spec.ts e2e-book/chapter05.spec.ts e2e-book/chapter05-visual-policy.spec.ts e2e-book/chapter06.spec.ts` | ✅ **32/32 passed** |
| 9 | Launch-button tests | `npx playwright test --config playwright.book.config.ts e2e-book/launch-buttons.spec.ts` | ✅ **20/20 passed** |
| 10 | Cross-chapter light/dark-mode tests | `npx playwright test --config playwright.book.config.ts e2e-book/wp22-cross-chapter-dark-mode.spec.ts` | ✅ **5/5 passed**, explicitly including Exercise 4, 5, and 6 |

**Frontend typecheck, frontend unit tests, and a frontend production
rebuild were not run: unnecessary.** `git status`/`git diff --stat` for this
entire WP touches only `requirements.txt`, one new file under `tests/`, and
this WP's own specification/report files — no file under `interactive/` was
changed.

No sleeps, weakened assertions, skipped tests, global retries, or repeated
build/stress loops were used anywhere in this WP. Each gate was run exactly
once.

**Coverage note for the user's attention:** none of these required gates run
`interactive/e2e-book/chapter01-dark-mode.spec.ts` in isolation — CI's "End-
to-end test the built Chapter 1 page" step runs the *entire* `e2e-book/`
suite (`npm run test:e2e:book`, 86 tests) via a single command, which is
broader than the specific per-exercise/launch-button/cross-chapter subsets
WP31R2 §6 enumerates. This gap is why the §9 failure (below) was not caught
locally before pushing; see §10.

## 7. Merge into local `main` (WP31R2 §7)

* Pre-merge local `main` reconfirmed unchanged: `7b17c5f`, clean apart from
  the two whitelisted reports.
* `git merge --no-ff fix/wp31r2-mermaid-dependency -m "Pin Mermaid dependency
  for CI book builds"` — **no conflicts.**
* **`WP31R2_RELEASE_SHA`: `f12967beaed9a4e16b4930e2881e28435478d388`**
  (parents: `7b17c5f` and `1187c01`).
* Tree-identity proof: `git diff --stat f12967b fix/wp31r2-mermaid-dependency`
  → **empty** — the merged `main` tree is byte-for-byte identical to the
  correction-branch tree.
* Diff from WP31R's `RELEASE_SHA` (`de564b3`) to `WP31R2_RELEASE_SHA`:
  exactly 5 files — the two previously-local WP31R reports, the WP31R2
  specification, `requirements.txt` (+1 line), and
  `tests/test_deploy_dependency_contract.py` (new, 104 lines). No notebook,
  widget, dataset, model, or activity content changed.
* No amend, squash, rebase, or history rewrite was performed.

## 8. Push (WP31R2 §8) — exactly once

* `git push origin main` → `de564b3..f12967b  main -> main`. Succeeded on
  the first and only attempt.
* Verified with a read-only `git ls-remote origin refs/heads/main`:
  `f12967beaed9a4e16b4930e2881e28435478d388 refs/heads/main` — matches
  `WP31R2_RELEASE_SHA` exactly.
* **No second push occurred at any point in this WP.**

## 9. GitHub Actions workflow (WP31R2 §9)

* **Workflow:** Build and deploy Jupyter Book
* **Discovery:** found on the **first** of the two permitted bounded queries
  (`gh run list --branch main --limit 5 --json ...`) — already `in_progress`.
* **Run ID:** `35510061137`
* **Triggering SHA:** `f12967beaed9a4e16b4930e2881e28435478d388` (=
  `WP31R2_RELEASE_SHA`, confirmed via the run's `headSha`)
* **Started:** 2026-09-20T12:14:40Z; **completed:** 2026-09-20T12:20:37Z
  (~5m57s)
* **Watch:** learning from WP31R's deviation (its single `gh run watch` was
  cut off by the calling tool's own command timeout before the run finished),
  this WP started `gh run watch 35510061137 --exit-status` **detached**
  (`nohup ... &; disown`) so it would run to completion independent of any
  local tool timeout, then waited on that single detached process. This
  satisfies WP31R2 §9.6's instruction to configure a sufficiently long
  timeout: exactly one continuous watch invocation ran end-to-end with no
  cutoff this time, no second watch, no parallel polling of the run itself,
  and no workflow rerun.
* **Result: FAILURE.**
  * **"Build Jupyter Book" passed** — confirming the `sphinxcontrib-mermaid`
    pin fix works against real Linux CI. (Every step up through "Fail on
    notebook execution errors" also passed.)
  * A **later, different, unrelated** step, **"End-to-end test the built
    Chapter 1 page"** (`npm run test:e2e:book`, running the full
    `interactive/e2e-book/` Playwright suite, 86 tests), failed on exactly
    one test:
    ```
    1) [chromium] › e2e-book/chapter01-dark-mode.spec.ts:121:3 › Chapter 1 built page
       — dark-mode Plotly theme sync (WP22) › histogram and correlation scatter:
       light → dark → reload-while-dark → light, every critical surface matches
       the intended palette

       Error: expect(locator).toHaveAttribute(expected) failed
       Locator: locator('[data-testid="histogram-plot"]')
       Expected pattern: /[1-9]/
       Received: <element(s) not found>
       Timeout: 5000ms
         at waitForRendered (chapter01-dark-mode.spec.ts:71:60)
         at snapshotHistogram (chapter01-dark-mode.spec.ts:83:9)
         at chapter01-dark-mode.spec.ts:171:32

    85 passed (1.2m)
    ```
    retrieved with a single `gh run view 35510061137 --log-failed`. This is
    a pre-existing dark-mode/rendering-timing test in a part of Chapter 1's
    WP22 dark-mode verification that WP31R2 did not touch, edit, or exercise
    (no CSS, JS, or Plotly-theme code changed in this WP; the diff is
    `requirements.txt` and one new offline test file only). It is a
    **different class of gap** than either of WP31R2's authorized targets
    (the float-comparison test and the Mermaid dependency) — outside
    WP31R2's scope ("Correct the second CI-environment gap... Do not change
    notebook, widget, dataset, model, or lesson content").
  * "Execute the portable notebook outside the repository" and "Publish
    website" were **skipped** (not run) as a consequence.

Per WP31R2 §9/§11 ("If the workflow fails, retrieve the failed log once,
document it, and stop. Do not fix or push again within WP31R2." /
"failed/cancelled workflow" is an explicit stop condition), **this WP stops
here.** No fix was attempted, no second push was made, and the workflow was
not rerun.

## 10. Production verification (WP31R2 §10)

**Not performed as a full pass** — WP31R2 §10 applies only after the
workflow succeeds, and it did not. Read-only spot checks instead confirm
production is unaffected:

| Check | Result |
|---|---|
| Workflow steps 18–19 ("Execute the portable notebook outside the repository", "Publish website") | both `skipped` — confirmed via `gh run view --json jobs` |
| `gh-pages` branch tip | `9dbe3b10ac31363aa1ef9cd8418a1b9cdd56ca12` — unchanged from WP31R's and WP31's reports |
| `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html` (cache-busted) | HTTP 200, title `Exercise 4: Cross-Validation for Classification and Regression` — the pre-existing WP26R-era title, **not** WP27's "Exercise 4: Validation and Cross-Validation" |

Conclusion: production is exactly as it was before this WP started. No
interaction, theme, layout, Colab/download, or console-error verification was
performed against the live site, since the release that would carry the new
content was never published.

## 11. Deviations and items for the user's attention

1. **The WP31R2 Mermaid fix is verified working on real GitHub Actions CI.**
   "Build Jupyter Book" — the exact step that failed in run `35469646309` —
   passed in run `35510061137`.
2. **A third, unrelated, pre-existing CI gap blocked the same run**: a single
   flaky/timing-sensitive dark-mode Playwright test,
   `chapter01-dark-mode.spec.ts:121` (histogram render-count wait timing out
   after a light→dark→reload-while-dark→light sequence), inside the broader
   "End-to-end test the built Chapter 1 page" step. 85 of the 86 tests in
   that step passed. This is outside WP31R2's authorized scope and was
   **not** investigated further or fixed here, per the explicit "document
   and stop" instruction.
3. **Coverage gap identified (see §6 note):** WP31R2's bounded local gates,
   like WP31R's before it, never exercised
   `interactive/e2e-book/chapter01-dark-mode.spec.ts` specifically — only
   the Exercise 4–6, launch-button, and cross-chapter-dark-mode subsets were
   required and run. CI's single "End-to-end test the built Chapter 1 page"
   step is the full `e2e-book/` suite (86 tests) and is measurably broader
   than what any WP31-series local gate list has exercised so far. A
   follow-up correction WP should either (a) diagnose whether this specific
   test is flaky (re-run it locally/in isolation several times to check for
   nondeterminism in the dark-mode reload/redraw timing) or a genuine
   regression, and fix accordingly, and/or (b) add the full
   `chapter01*.spec.ts` set to the routine bounded local gate list so this
   class of gap is caught before pushing next time.
4. **Recommendation (not actioned by this WP):** a follow-up WP (e.g.
   WP31R3) should reproduce `chapter01-dark-mode.spec.ts:121` against the
   locally built book (`npx playwright test --config playwright.book.config.ts
   e2e-book/chapter01-dark-mode.spec.ts`, ideally run more than once to check
   for flakiness), diagnose whether it is a genuine WP22 dark-mode regression
   or a CI-only timing/resource issue (the local `.venv` build has passed
   every prior gate cleanly), fix if needed, then merge, push, re-trigger the
   deploy workflow, and complete production verification for Exercises 4–6.
5. **Deviation, anticipated by the WP itself:** the fresh-environment
   reproduction (§5) used Python 3.12.7, not CI's exact 3.11.16 — the only
   two Python versions available locally are 3.9.6 (incompatible with the
   new pin's `Requires-Python: >=3.10`) and 3.12.7. No new system Python was
   installed to work around this.
6. `origin/main` currently sits at `WP31R2_RELEASE_SHA`
   (`f12967beaed9a4e16b4930e2881e28435478d388`) with a failed/red Actions run
   attached to it, exactly mirroring WP31R's and WP31's prior states at
   their own release SHAs. It has not been reverted, reset, or force-pushed.
7. No notebook, widget, dataset, model, or activity content was created,
   edited, or regenerated at any point in this WP. `sphinxcontrib.mermaid`
   remains enabled in `book/_config.yml`; the nested-CV diagram and any other
   Mermaid content remain supported.

## 12. Final `git status --short --branch`

```
## main...origin/main
?? WPs/reports/WP16_ARCHITECT_REPORT.md
?? WPs/reports/WP21_DEPLOYMENT_REPORT.md
```

(as of immediately before this report and the changelog were committed
locally; see `WPs/reports/WP31R2_EXACT_CHANGELOG.md` for the exact commit
added after this file, to be recorded as `WP31R2_DOCUMENTATION_SHA`.)

Local `main` = `origin/main` = `f12967beaed9a4e16b4930e2881e28435478d388`
(`WP31R2_RELEASE_SHA`) at the time this report was written. The two
whitelisted legacy reports remain the only untracked files. WP32 was not
started.
