# WP50 exact changelog

Starting SHA (local and remote `main`, in sync): `9597f8d` ("WP49: record
the final CI run that confirmed the paths-ignore fix").

Checkpoint: branch `checkpoint/wp50-pre-work`, at `9597f8d`, created before
any WP50 edit.

No feature branch: this WP's entire implementation landed as one commit,
made directly on `main` after full local verification (see "Verification"
below) — unlike several prior WPs' multi-commit, multi-push arcs, there was
no partial/intermediate state worth isolating on its own branch, and the
WP50 spec itself asks for exactly one controlled production push.

## Commit made by this WP

1. `2ec83cc` — "WP50: change-aware classifier and deploy gate for
   single-notebook edits" (8 files changed, +1714/−7):
   - **New** `scripts/classify_release_change.py` (525 lines): the
     deterministic classifier. Resolves the comparison base from
     `origin/gh-pages`'s HEAD commit message (`deploy: <sha>`), validates
     it (reachable commit object, ancestor of HEAD), diffs base..HEAD with
     rename detection, classifies every changed path (WP docs / one
     exercise's own scoped surface / shared-global / unknown), and for a
     change confined to exercise-scoped paths, diffs each touched
     exercise's five generated notebook artifacts (JupyterLite template,
     its lite-served portable copy, the downloads portable copy, the
     transition page, the reference notebook) cell-by-cell to verify
     "prose-only" (identical cell order/type, code-cell sources, cell and
     notebook metadata, outputs — only markdown-cell wording may differ).
     Produces `gate` ∈ {`skip`, `prose`, `exercise`, `full`}, the affected
     exercise IDs, a human log, and a machine JSON form; writes
     `gate=`/`exercises=`/`reason=` to `$GITHUB_OUTPUT` when asked.
   - **New** `scripts/run_selected_checks.py` (160 lines): recomputes the
     same classification and executes exactly the checks the `prose`/
     `exercise` gates call for, in two phases (`pretest`: generator
     `--check` + structural/reference unittest files; `postbuild`: route
     smoke-check + the touched exercise's own Playwright spec for the
     `exercise` gate only). No-ops for `skip`/`full` (the latter stays the
     existing broad steps in `deploy.yml` itself, run directly).
   - **New** `scripts/smoke_release_routes.py` (130 lines): the cheap,
     no-browser smoke check both fast gates use — validates a built
     exercise's transition-page route and link, its JupyterLite template,
     and its *actually served* portable download
     (`lite/files/exercise_0N_portable.ipynb`, not
     `exercise_manifest.json`'s `fallbackDownloadablePath`, which is a
     source-tree path `book/_config.yml` excludes from the build entirely
     — found and fixed during this WP's own local dry-run, see
     "Deviations" in the report).
   - **Modified** `.github/workflows/deploy.yml` (+75/−7 within the file):
     added a `classify` job (checkout, shallow `git fetch origin
     gh-pages`, run the classifier, publish its outputs) that
     `build-and-deploy` now `needs:`; `build-and-deploy` itself gains
     `if: needs.classify.outputs.gate != 'skip'` and per-step `if:`
     conditions splitting the existing steps into "always" (site-build
     prerequisites, the build itself, cheap data-artifact `--check`s),
     "full gate only" (frontend typecheck/unit/audit, the blanket
     01–08 generator-staleness loop, the full offline `unittest
     discover`, the full `npm run test:e2e:book`, the chapter_02
     kernel-execution smoke), and two new steps — "Run change-aware
     pretest checks" and "Run change-aware browser + route smoke checks"
     — gated to `prose`/`exercise`. The combined build and the final
     "Publish website" step are unchanged and still run exactly once per
     non-`skip` push.
   - **New** `.github/workflows/full-regression.yml` (146 lines):
     `workflow_dispatch`-only (no `schedule:` — the full suite is a real
     ~20–30 min local / ~1.5–2h CI run, not "inexpensive"), mirrors
     `deploy.yml`'s full-gate steps, has no publish step anywhere in the
     file.
   - **New** `tests/test_classify_release_change.py` (472 lines, 35
     tests): path-classification unit tests; notebook prose-diff unit
     tests (markdown-only, code-cell source change, MC-label-in-code-cell
     change, cell-count change, notebook-metadata change, output change);
     pure `classify()` gate-decision tests with a stubbed prose-checker
     (single exercise prose/code, two exercises both-prose and
     mixed-escalates, shared-path-wins-even-alongside-an-exercise-change,
     unknown-path, untrustworthy-base, rename-contributes-both-paths); and
     real-disposable-git-repo end-to-end tests exercising
     `classify_release()`/`resolve_base()` against actual commits —
     including the missing/corrupt/non-ancestor marker cases and the
     "prior failed push, then a fix" scenario proving the comparison
     stays anchored to the last *successful* publish (a shared-path
     change from the never-published failed push is still caught; the
     same diff taken against the merely-previous push instead would have
     missed it).
   - **New** `WPs/reports/WP50_MAINTAINER_GUIDE.md` (155 lines): where
     wording is edited and what to regenerate; the four-gate table; why
     the prose check is based on the generated notebooks, not the commit
     message; how to request a full run (automatic escalation, a touched
     shared path, or `full-regression.yml`); how to see why CI chose a
     gate; running the same checks locally; an explicit note on scope
     (shared surfaces are never finely attributed to "actually affected"
     exercises — any shared-path change takes the full gate
     unconditionally; Exercises 9–12 are not fast-pathed, unchanged from
     before this WP).
   - `WPs/WP50_CHANGE_AWARE_NOTEBOOK_RELEASE.md`: the WP spec itself,
     committed (was untracked at the start of this WP).

## Local-only fixture commit (never pushed, branch deleted)

`5755fd7` — "fixture: wording-only tweak to Exercise 1's overview
paragraph (local fast-path demo, not for push)", made on a disposable
branch `wp50-fastpath-fixture-demo` branched from `2ec83cc`, used only to
exercise the new fast path end-to-end locally (see the report's
"Verification" section 4). The branch was deleted and `main` restored to
`2ec83cc` with a clean working tree before the production push; this SHA
is recorded here for traceability only (the branch pointing to it no
longer exists, so it is unreachable and eligible for eventual git
garbage collection — expected and fine for a throwaway fixture).

## Push

`git push origin main` — `9597f8d..2ec83cc main -> main`, one push, no
force, no rewrite.

## CI run

[`37793260325`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/37793260325)
("WP50: change-aware classifier and deploy gate for single-notebook
edits"), triggered by the push above — **success**, **1h45m33s**
end to end, watched through completion via `gh run view` (not assumed
from a final notification).

| Job/step | Result | Duration |
| --- | --- | --- |
| `classify` (new) | success | 9s |
| `build-and-deploy`: install deps + course-toolbar extension build | success | ~80s |
| `build-and-deploy`: frontend typecheck/unit/audit/build (full gate) | success | ~30s |
| `build-and-deploy`: **Run change-aware pretest checks** (new) | **skipped** (gate=full) | 0s |
| `build-and-deploy`: full offline Python suite (full gate) | success | 24m39s |
| `build-and-deploy`: Install Playwright Chromium | success | 36s |
| `build-and-deploy`: standalone widget app e2e (full gate) | success | 1m22s |
| `build-and-deploy`: Jupyter Book + JupyterLite build | success | ~5s |
| `build-and-deploy`: full `npm run test:e2e:book` (full gate) | success, **0 failures** | 1h16m24s |
| `build-and-deploy`: **Run change-aware browser + route smoke checks** (new) | **skipped** (gate=full) | 0s |
| `build-and-deploy`: chapter_02 portable-notebook smoke (full gate) | success | 6s |
| `build-and-deploy`: Publish website | success | 4s |

The two new conditional steps correctly showed `skipped` (this push is
`full`-gated, by the classifier's own rule, since it changes the workflow
files themselves) — the first real confirmation that the
`needs.classify.outputs.gate` wiring works in actual GitHub Actions, not
only in local YAML parsing.

## Live-site verification

Checked the real, served site directly after confirming the publish step
succeeded and the `gh-pages` marker matches
(`git fetch origin gh-pages --depth=1 && git log -1 --format='%H %s'
origin/gh-pages` → `deploy: 2ec83cc384e4699611f8106963d7ff480f9cdf86`, this
WP's own commit):

| Check | URL | Result |
| --- | --- | --- |
| Hub still lists exactly 1–8 | `/contents.html` | HTTP 200 |
| Exercise 1 transition page | `/chapters/chapter_01/exercise_01.html` | HTTP 200, contains "Open Exercise 1" |
| Exercise 9 still unpublished | `/chapters/chapter_09/exercise_09.html` | HTTP 404 (unchanged by this WP) |
| Exercise 1 Lite template | `/lite/files/exercise_01.ipynb` | HTTP 200, `content-type: application/x-ipynb+json` |
| Exercise 1 portable download | `/lite/files/exercise_01_portable.ipynb` | HTTP 200, `content-type: application/x-ipynb+json` |

Nothing about what is published or excluded changed as a side effect of
this WP — expected, since it touches only CI classification/test
selection, not any teaching content or build-scope config.

## Numeric parity

No generator, data export, or notebook content changed in this WP at all
— every edit is to CI infrastructure (`scripts/classify_release_change.py`,
`scripts/run_selected_checks.py`, `scripts/smoke_release_routes.py`,
`.github/workflows/*`) or documentation. Numeric parity for Exercises 1–8
is therefore unchanged by construction, and was re-confirmed anyway by the
full offline suite's pass (above) and by the one local fixture edit (the
`5755fd7` wording-only demo) touching no code cell at all.

## Confirmation

`Homework_Materials/` untouched. Exercises 9–12's own source and git
history untouched. No destructive git operation at any point — one plain
commit on `main` from its already-synced tip, one plain push, no merge, no
rebase, no force-push, no branch deletion of anything but the author's own
disposable local fixture branch (`wp50-fastpath-fixture-demo`, never
pushed).
