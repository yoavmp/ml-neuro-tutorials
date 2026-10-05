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
4. This report + this changelog (committed together as this WP's closing
   commit — see `git log -1` after that commit for the final SHA).

## Merge and push

```
git checkout main
git merge --ff-only feature/wp49-deploy-jupyterlite-exercises-1-8   # pure fast-forward, 02c389d..6a91ae2
git push origin main                                                 # dcc5365..6a91ae2
```

GitHub Actions run triggered by that push:
**https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/37222242595**

<!-- WP49-CI-RESULT-PLACEHOLDER -->

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

Runs 4–9 are the targeted, isolated reruns the task asked for ("rerun
only a failing focused check after a specific fix"); run 1 and run 9 are
the two full-suite runs this WP needed (the first to find every issue at
once, the second — under identical full-parallelism conditions — to prove
the three real fixes hold and that only genuine full-parallelism
contention remains, which the CI `workers: 1` cap then addresses).

<!-- WP49-CI-E2E-RESULT-PLACEHOLDER -->

## Live-site verification

<!-- WP49-LIVE-SITE-PLACEHOLDER -->

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
