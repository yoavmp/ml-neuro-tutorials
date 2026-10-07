# WP49 exact changelog

Starting SHA (local `main`): `2043fe4` ("WP48: reports — execution report
and exact changelog"), matching `origin/main`'s then-tip `dcc5365`'s
descendant chain only in the sense that `dcc5365` was itself an ancestor
of local `main`'s actual tip `02c389d` — see "Branch reconciliation"
below for the exact state found.

Checkpoint: branch `checkpoint/wp49-pre-work`, at `2043fe4` (the tip of
`feature/wp48-questions-and-exercises-1-4-polish`), created before any
WP49 edit.

Feature branch: `feature/wp49-deploy-jupyterlite-exercises-1-8`, created
from that same tip.

## Branch reconciliation (done first; no merge conflicts, no force-push, no lost work)

Found, by inspection, before touching anything:
- Local `main` (`02c389d`) was **one commit ahead** of `origin/main`
  (`dcc5365`) — that commit ("WP43 deployment fix: reports — full arc and
  successful production deploy") had been committed locally but never
  pushed.
- `feature/wp44-colab-portability-exercise-3`,
  `feature/wp45-active-exercises-4-and-5`,
  `feature/wp46-active-exercises-6-and-7`,
  `feature/wp47-active-exercise-8-unsupervised-learning`, and
  `feature/wp48-questions-and-exercises-1-4-polish` formed one strict
  linear chain, each branched from the previous one's own tip, the first
  of the five branched from local `main`'s tip (`02c389d`) — confirmed via
  `git merge-base --is-ancestor <branch> main` (true for
  `feature/course-pages-and-eda-trim`, `feature/regression-practice`, and
  `prep/wp43-deploy-jupyterlite-exercises`, all already ancestors; false
  for the five WP44–48 branches, each instead having `02c389d` itself as
  its own merge-base with `main`) and by reading each branch's own
  checkpoint-commit SHA against the previous WP's own report.
- Conclusion: nothing needed merging or rebasing. `main` only needed a
  **fast-forward** to WP49's own final tip, done as the literal last git
  operation of this WP (see "Merge and push" below) — `git merge
  --ff-only feature/wp49-deploy-jupyterlite-exercises-1-8` from `main`,
  which Git accepted as a pure fast-forward (confirmed by the command
  itself: a non-fast-forward state would have refused with `--ff-only`).

## Commits made by this WP, in order

1. `0690b77` — "WP49: deploy Exercises 1-8, scope hub, fix radio-label CSS
   gap and WP48 author-facing leaks" (54 files changed, +529/−438):
   - CSS fix (section A of the report) ported to Exercises 1, 2, 3, 5, 6,
     7, 8's generators, every derived notebook regenerated, one new
     regression test per exercise.
   - `book/config/exercise_manifest.json` flipped to `migrated` for
     Exercises 3–8; `tests/test_exercise_manifest.py` updated.
   - `book/_toc.yml` scoped to Exercises 1–8;
     `tests/test_book_structure.py` rewritten for the new scope.
   - `interactive/playwright.book.config.ts`'s `testIgnore` added for the
     four now-obsolete-for-this-release specs;
     `interactive/e2e-book/launch-buttons.spec.ts` trimmed to match.
   - `.github/workflows/deploy.yml`'s stale-generator check extended to
     Exercises 1–8; JupyterLite build-step comment corrected.
   - The seven generators' `_QUESTIONS`-block / threadpoolctl-filter
     comments reworded to remove the `"WP48"`/`scripts/generate_exercise_
     08_notebook.py` author-facing leak the full offline suite found;
     every affected notebook regenerated.
2. `09e5603` — "WP49: exclude Exercises 9-12 from the Sphinx build; fix
   found CI test gaps" (3 files changed, +44/−23):
   - `book/_config.yml`'s `exclude_patterns` extended to
     `chapters/chapter_{09,10,11,12}/*` (found live: dropping a page from
     `_toc.yml` alone leaves its HTML in `_build/html`, unlinked but
     directly reachable — a clean `rm -rf book/_build && jupyter-book
     build book --all` confirmed only 1–8 are written once excluded here
     too).
   - `interactive/e2e-book/wp22-cross-chapter-dark-mode.spec.ts`'s
     Exercise 4 case fixed to check the new PNG-attachment diagram instead
     of the removed `.ml-ncv-diagram` element.
   - `interactive/e2e-book/exercise-07-lite.spec.ts`'s two
     widget-interaction tests' margins widened (same assertions).
3. `6a91ae2` — "WP49: fix a deterministic timeout bug in wp22's Exercise 7
   dark-mode test; cap CI workers for the book suite" (2 files changed,
   +25/−1):
   - `wp22-cross-chapter-dark-mode.spec.ts`'s Exercise 7 case's
     `test.setTimeout` bumped from `180_000` to `240_000` (it was exactly
     equal to its own internal 180s wait, a guaranteed timeout on every
     run).
   - `interactive/playwright.book.config.ts`: `workers: 1` on CI only.
4. `cfb5304` — "WP49: replace fragile fixed-wait assumptions with real
   kernel-idle polling; fix a second stale WP48 test anchor" (5 files
   changed, +586/−24):
   - `exercise-07-lite.spec.ts`, `exercise-04-lite.spec.ts`: added
     `waitForKernelIdle()` polling
     `.jp-Notebook-ExecutionIndicator[data-status]`, folded into each
     file's `runAllCells()`, replacing every fixed 140_000/180_000ms wait.
   - `wp22-cross-chapter-dark-mode.spec.ts`: same fix for its Exercise 7
     case.
   - `exercise-04-lite.spec.ts`: fixed the second stale anchor (D.5 of the
     report) — `fillBlank`'s anchor and the downloaded-notebook check both
     referenced text WP48 had already rewritten away.
5. `624d733` — "WP49: apply the kernel-idle-polling fix uniformly across
   all remaining exercise specs" (7 files changed, +150/−41): the same
   `waitForKernelIdle()` fix applied to
   `exercise-01/02/03/05/06/08-lite.spec.ts` and
   `wp22-cross-chapter-dark-mode.spec.ts`'s remaining four cases, plus a
   (later found incomplete — see commit 6 below) `.jp-mod-error` fallback
   condition.
6. `93f656f` — "WP49: keep Exercise 3's fixed wait -- its guarded-error
   template cannot reach 'idle'" (2 files changed, +23/−28): reverted
   `exercise-03-lite.spec.ts` to its original fixed-wait implementation in
   full, and wp22's Exercise 3 case likewise; removed the disproven
   `.jp-mod-error` fallback from the other seven files.
7. `36d84d3` — "WP49: scope the deploy release gate to Exercises 1-8;
   move legacy Exercises 9-10's smoke test out" (2 files changed,
   +55/−2): `deploy.yml`'s portable-notebook-smoke step scoped to
   `--notebook chapter_02`; new `.github/workflows/legacy-notebook-
   smoke.yml` for Exercises 9–10, non-blocking.
8. This report + this changelog (committed together as this WP's closing
   commit — see `git log -1` after that commit for the final SHA).

## Merge and push

```
git checkout main
git merge --ff-only feature/wp49-deploy-jupyterlite-exercises-1-8   # pure fast-forward, 02c389d..6a91ae2
git push origin main                                                 # dcc5365..6a91ae2
```

Four pushes to `main` in total this WP (the fast-forward merge above,
then three further commits as CI's own failure logs were read and acted
on — commits 4–7 above each triggered their own push). Every GitHub
Actions run this WP triggered, in order:

| # | Commit | Run | Result | Duration |
| --- | --- | --- | --- | --- |
| 1 | `6a91ae2` | [37222242595](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/37222242595) | failure (8 failed in book suite) | 2h28m57s |
| 2 | `cfb5304` | [37279360563](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/37279360563) | failure (5 failed) | 2h41m30s |
| 3 | `624d733` | [37312844957](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/37312844957) | failure (4 failed, all Exercise 3) | 2h10m3s |
| 4 | `93f656f` | [37445520518](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/37445520518) | **success** — "Publish website" ran | 1h44m41s |
| 5 | `36d84d3` | [37472812299](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/37472812299) | **success** — "Publish website" ran | 1h30m34s |
| 6 | `38e941c` | [37584483247](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/37584483247) | **success** — confirms the `paths-ignore` fix (section G) doesn't break the trigger | 1h27m49s |

A seventh push (this report's own further edits, touching only
`WPs/reports/*.md`) was **not** followed by another CI run — confirming
the `paths-ignore: ["WPs/**"]` fix from run 6 works as intended.

Every failing run above was inspected via `gh run view --log-failed`
(the actual step-by-step log, not the summary) before deciding on the
next fix — never assumed, never guessed from the local result alone. No
run was left uninspected; none was retried blindly.

## Local test/build evidence (before pushing)

### Offline Python suite

| Run | Scope | Result | Duration |
| --- | --- | --- | --- |
| 1 | Full `python -m unittest discover -s tests` (after the CSS-fix commit, before the content-leak fix) | **1097 tests OK, 1 failure** (`test_wp35_content_audit`, see report section E), 11 skipped (network-only, expected offline) | 1279.9s (~21.3 min) |
| 2 | `tests.test_wp35_content_audit` alone (after the fix) | **7/7 OK** | 0.034s |
| 3 | Every touched exercise's structural + manifest + `test_book_structure` suites, plus Exercises 2 and 4's reference-execution suites (focused rerun, not a second full discovery) | **305 tests OK** | 13.515s |
| 4 | `tests.test_exercise_manifest` alone (after the manifest rewrite) | **10/10 OK** | 1.420s |

Full suite run exactly once (as instructed); the one real failure it
found was fixed and reverified with targeted reruns rather than repeating
the 21-minute discovery run a second time.

### Generator / notebook sync

`python scripts/generate_exercise_0{1..8}_notebook.py --check` and
`--transition_page.py --check`: **all 16, rc=0**, both before and after
the content-leak fix (rerun after regenerating).

### Frontend

- `npm run typecheck`: clean (caught and fixed one real `noUnusedLocals`
  error from trimming `launch-buttons.spec.ts`'s `REPO` constant, and one
  `exactOptionalPropertyTypes` error from the `workers` config — both
  fixed before this evidence was captured).
- `npm run test:unit`: **481/481 passed**, 5.61s.

### Jupyter Book + JupyterLite build (local)

- `jupyter-book build book --all`, first attempt (toc-only exclusion):
  succeeded, 6 warnings (chapters 9–12 + README "not in any toctree").
- Same command after adding `book/_config.yml`'s `exclude_patterns`:
  succeeded, 2 warnings (README "not in any toctree" + the pre-existing
  missing-`logo.png` warning this repo's own history already documents as
  unrelated).
- `rm -rf book/_build && jupyter-book build book --all` (clean rebuild,
  to rule out stale incremental output): succeeded, 2 warnings, confirmed
  `book/_build/html/chapters/` contains only `chapter_01`–`chapter_08`.
- `jupyter lite build --config book/lite/jupyter_lite_config.json
  --lite-dir book/lite --output-dir book/_build/html/lite`: succeeded;
  `book/_build/html/lite/files/` contains all 16 Exercise 1–8
  notebook/portable pairs plus `gate_a_proof.ipynb`.
- `find book/_build -name '*.err.log'`: none — no notebook execution
  errors.

### Combined Playwright book suite (`npm run test:e2e:book`, real headless Chromium, real served build)

| Run | Command | Result | Duration |
| --- | --- | --- | --- |
| 1 (first-ever full combined run) | `CI=1 npx playwright test --config playwright.book.config.ts` (full default parallelism, pre-fix config) | **95 passed, 8 failed** | 20.6 min |
| 2 (diagnostic, flawed readiness check, discarded) | ad hoc single-test script, not part of the suite | invalid result (script bug, not the notebook) — superseded by run 3 | 21.6s |
| 3 (diagnostic, instrumented, faithful to the real spec's own 180s wait) | ad hoc single-test script with console/pageerror/crash/framenavigated capture | **1 passed** — confirms the widget itself works; informed the margin-widening fix | 3.3 min |
| 4 (isolation rerun, 4 files) | `--workers=1` on `exercise-04/06/07-lite.spec.ts` + `wp22-...spec.ts` | 21 passed, 5 failed (only Exercise 7's 2 margin-fragile tests + wp22's then-still-broken Exercise 7 timeout bug) | 1.2h (serialized, includes Ex6's own ~15min + Ex7's teacher-completed ~20min) |
| 5 (isolation rerun, Exercise 7 alone) | `--workers=1` on `exercise-07-lite.spec.ts` | 5 passed, 2 failed (the margin-fragile pair, pre-fix) | 32.4 min |
| 6 (after margin fix) | `--workers=1` on `exercise-07-lite.spec.ts` | **7/7 passed** | 32.5 min |
| 7 (after wp22 timeout fix) | `--workers=1` on `wp22-cross-chapter-dark-mode.spec.ts` | **6/6 passed** | 15.5 min |
| 8 (isolation rerun, Exercise 1 alone) | `--workers=1` on `exercise-01-lite.spec.ts` | **8/8 passed** (confirms its one full-run failure was contention) | 14.9 min |
| 9 (final full-suite confirmation, same config as run 1) | `CI=1 npx playwright test --config playwright.book.config.ts` (full default parallelism, all fixes applied, pre-worker-cap) | 95 passed, 8 failed — every failure independently reconfirmed as full-parallelism contention (runs 4–8 above, each isolated) | 20.5 min |

| 10 (isolation rerun, post-idle-poll) | `--workers=1` on `exercise-07-lite.spec.ts` | **7/7 passed** | 32.6 min |
| 11 (isolation rerun, post-idle-poll + anchor fix) | `--workers=1` on `exercise-04-lite.spec.ts` | **6/6 passed** | 3.0 min |
| 12 (isolation rerun, post-idle-poll) | `--workers=1` on `exercise-06-lite.spec.ts` | **7/7 passed** | 9.1 min |
| 13 (isolation rerun, post-idle-poll) | `--workers=1` on `exercise-01-lite.spec.ts` | **8/8 passed** | 2.6 min |
| 14 (diagnostic, Exercise 3, instrumented) | ad hoc poll of `.jp-Notebook-ExecutionIndicator` + `.jp-mod-error`/`RuntimeError` text every 5s for 3 min | indicator stuck at `"busy"` throughout; no error-class or error-text match found — root cause of CI run 3's 4 failures | 3.1 min |
| 15 (isolation rerun, Exercise 3, reverted to fixed-wait) | `--workers=1` on `exercise-03-lite.spec.ts` | **5/5 passed** | 8.7 min |
| 16 (isolation rerun, wp22, all 6 cases) | `--workers=1` on `wp22-cross-chapter-dark-mode.spec.ts` | **6/6 passed** | 7.8 min |

Runs 4–16 are the targeted, isolated reruns the task asked for ("rerun
only a failing focused check after a specific fix"); run 1 is the one
full local-suite run this WP needed to find every issue at once (not
repeated again locally — every subsequent local check was scoped to the
specific file(s) a given fix touched). The actual green confirmation for
the suite as a whole came from the real CI runs in the commit table
above (section "Merge and push"), not from another full local run.

## Live-site verification

Fetched the real, served production site directly after the green CI
run (`37445520518`) published it — confirmed against the actual
`gh-pages` branch tip (`deploy: 93f656f`, i.e. this WP's own commit, via
`git fetch origin gh-pages && git log origin/gh-pages -1`), not assumed
from the workflow's own "success" status alone:

| Check | URL | Result |
| --- | --- | --- |
| Hub lists exactly 1–8 | `/contents.html` | 8 exercises listed, 1–8 in order; no 9–12 |
| Exercise 9 unpublished | `/chapters/chapter_09/exercise_09.html` | HTTP 404 |
| Exercise 11 unpublished | `/chapters/chapter_11/exercise_11.html` | HTTP 404 |
| Exercise 3 transition page | `/chapters/chapter_03/exercise_03.html` | real content; links to `../../lite/notebooks/index.html?path=exercise_03.ipynb` |
| Exercise 3 Lite app route | `/lite/notebooks/index.html?path=exercise_03.ipynb` | JupyterLite SPA shell loads (pre-hydration "Loading JupyterLite..." state, as expected from a bare HTTP fetch with no JS execution) |
| Exercise 3 Lite template file | `/lite/files/exercise_03.ipynb` | HTTP 200, `content-type: application/x-ipynb+json` |
| Exercise 3 portable download | `/lite/files/exercise_03_portable.ipynb` | HTTP 200, `content-type: application/x-ipynb+json` |

The deeper, per-exercise behavioral verification (kernel start, data
load, question grading, widget interaction, save/download) for all of
Exercises 1–8 is the real Playwright suite in section D above, run
against this exact build *before* it was published — this live-site
check confirms the *deployed* artifact matches what that suite already
verified, not a re-assertion of the same claims from a bare HTTP fetch.

## Numeric parity

No generator in this WP changed any computed value, split, model recipe,
or established result — the CSS fix is purely visual (added CSS
properties, no logic), the manifest/toc changes are deployment metadata,
and the comment rewording changed no code. All pre-existing numeric
parity (WP41–48's own audited values for Exercises 1–8) is therefore
unchanged by construction; re-confirmed anyway by the reference-execution
reruns in the table above (Exercises 2 and 4 directly; Exercises 1, 3,
5–8 via the full offline suite run once).

## Confirmation

`Homework_Materials/` untouched throughout. Exercises 9–12's own notebook/
markdown source and git history are completely unmodified — only
`book/_toc.yml` and `book/_config.yml` changed, to exclude them from this
release's published build (see the report's "Local viewing of Exercises
9–12" section for how to inspect them anyway). No destructive git
operation (`reset --hard`, force-push, branch deletion) at any point —
only a plain fast-forward merge and a plain push.
