# WP63 Report — Exercise 4: comment cleanup and release

## Overall result: SUCCESS

All five comment edits are implemented and verified in the live notebook.
`revise/exercise-04-validation-split` (carrying WP62 and WP63) is merged
into `main`, pushed, and deployed via the repository's release workflow.
Two real test-scope gaps surfaced by CI (not false alarms) were found and
fixed along the way — see "What CI caught" below.

## Branch, merge, and push

- Merged `revise/exercise-04-validation-split` into local `main` with
  `--no-ff`: merge commit `af0cde5`.
- Pushed `main` to `origin`: `7e3a348..af0cde5`, then two follow-up fix
  commits pushed individually as CI caught gaps: `af0cde5..88144fa`, then
  `88144fa..f3fc6ed`.
- **Final pushed/deployed SHA on `main`: `f3fc6ed650688ffdb8db6ece807cfca4e68ad5fb`.**

## The five comment edits (verified present in the live notebook)

| # | Before | After |
|---|---|---|
| 1 | `# Load the approved ABIDE-II classification table: ...` | `# Load the ABIDE-II classification table: ...` |
| 2 | `# Verify the raw codes before mapping anything -- never infer a mapping from column order or alphabetical sorting.` (2 lines) | `# Verify data` |
| 3 | `# Recode the raw ABIDE-II codes to this notebook's binary target, once, here -- every later cell already sees 0 = control / 1 = autism on df["group"], never the raw 1/2 codes or a string label.` (3 lines) | `# In the original dataset, 1 = autism, 2 = control. Change the labels to 0 = control, 1 = autism before proceeding.` (mapping code itself unchanged) |
| 4 | `# A small, predetermined set of candidate C values to compare on the` / `# validation set below -- not adjusted after seeing any result.` (2 lines) | `# A small, predetermined set of candidate C values to compare.` (1 line) |
| 5 | 4-line check-cell comment explaining the `np.asarray()` ambiguous-truth-value workaround | `# Run this to check your X and y. Accepts X/y as a NumPy array, a pandas` / `# DataFrame/Series, or anything else convertible to one.` (exactly 2 lines, as specified) |

All five were confirmed word-for-word in the regenerated
`book/lite/files/v2/exercise_04.ipynb` before running any test, and again
independently by fetching the **live** deployed copy after publication
(see "Live verification" below). No author-directed implementation notes,
WP identifiers, or "as requested" language were added to any student-facing
cell — the generator's internal docstrings/comments (not student-visible)
were updated separately where they referenced the old wording.

## What CI caught (two real scope gaps, not false alarms)

Local verification before each push was the five-wording check, the
generator's own `--check`, and the three `test_exercise_04_*.py` files
(all green). CI's "full gate" — which this diff triggered because it
touches `scripts/` and `tests/` — covers substantially more than that,
and caught two genuine staleness bugs my narrower local scope missed:

1. **Run `41711669876`** (`af0cde5`) failed the Python unit-test suite
   (1427 tests, 1 failure): `tests/test_wp19_content_audit.py::test_classification_uses_fixed_c1_language`
   still hard-asserted the literal `"C_EXAMPLE = 1.0"` in the portable
   Exercise 4 notebook — a repository-wide content audit WP62 never
   touched, left over from WP19's "fixed C" policy that WP62 deliberately
   superseded for Exercise 4. Fixed by renaming/rewriting the test
   (`test_classification_selects_c_via_a_validation_set`) to assert the
   new `C_GRID` literal is present and the old `C_EXAMPLE` literal is
   absent — the same treatment this file's own comments already document
   for Exercise 3 when WP60 gave it a deliberately different subject.
   Pushed as `88144fa`.

2. **Run `41799270728`** (`88144fa`) got past the Python suite but failed
   the combined-book Playwright end-to-end suite: 2 of 146 book-level
   tests failed, both in `interactive/e2e-book/exercise-04-lite.spec.ts`
   — a browser test hardcoding the old 4-variable split guard text
   (`"define X_train, X_test, y_train, and y_test above first"`), the old
   one-line split solution it types in live, the old `"n_train = 753
   n_test = 251"` print, and the old `accuracy = 0.546` / `AUC=0.569`
   results. Rewrote the spec for the new six-variable guard text, the new
   two-call split solution, the new `"n_train = 564   n_val = 189
   n_test = 251"` print, the new `selected C = 0.1` print, and the new
   `accuracy = 0.534` / `AUC=0.580` results; also added a check for the
   new C-selection cell's own "not complete yet" guard, so the test's own
   "every activity degrades gracefully" claim still covers every cell
   genuinely. Before pushing this fix, it was run and verified **locally**
   against a real local `jupyter-book build` + `jupyter lite build` +
   Playwright, both at full parallelism (where one unrelated test flaked
   from CPU contention, a known, already-documented pre-existing issue in
   this suite) and serialized at `--workers=1` (CI's own setting) — all 6
   tests in the file passed cleanly. Pushed as `f3fc6ed`.

No other file or test was touched to make these pass — both fixes updated
stale *assertions* about a policy WP62 had already, deliberately, changed,
never the reverse.

## Final CI run

- **Run id 41823269119**, triggered by push of `f3fc6ed`:
  <https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/41823269119>
- Gate selected by `scripts/classify_release_change.py`: **full** (this
  diff touches `scripts/` and `tests/`, not just notebook content).
- Both jobs (`classify`, `build-and-deploy`) completed with conclusion
  **success**. Run duration: 11:43:42–13:47:15 UTC (≈2h3m), consistent
  with this repository's established full-gate timing.
- Publish step (`peaceiris/actions-gh-pages`) ran as part of the same
  successful job.

## Deployed `gh-pages` commit

```
8d72a13169170921b31482dca0d6211d5d9f58d0  deploy: f3fc6ed650688ffdb8db6ece807cfca4e68ad5fb  2026-11-04T13:47:09+00:00
```

The `gh-pages` commit message embeds the exact `main` SHA it was built
from (`f3fc6ed...`), confirmed by `git fetch origin gh-pages --depth=1`
after the run completed — this is the authoritative proof the publish
step actually ran against this change, not an earlier, stale build.

## Live verification (not inferred from CI's green status alone)

Fetched directly from the published site after the run completed:

- `GET https://yoavmp.github.io/ml-neuro-tutorials/lite/files/v2/exercise_04.ipynb` → **200**, 63,422 bytes.
- `GET https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html` → **200** (transition page, unaffected by this WP, still live).
- Parsed the fetched notebook and confirmed, in the live bytes:
  - `C_GRID = [0.01, 0.1, 1.0, 10.0, 100.0]` present; `C_EXAMPLE = 1.0` absent.
  - `# Verify data` present (comment edit 2).
  - `# A small, predetermined set of candidate C values to compare.` present (comment edit 4).
  - `In the original dataset, 1 = autism, 2 = control` present (comment edit 3).
  - `# Load the approved ABIDE-II` absent (comment edit 1 — "approved" removed).
  - The new split's student stub (`# X_trainval, X_test, y_trainval, y_test = ...` /
    `# X_train, X_val, y_train, y_val = ...`) and `selected_C` are present.

This confirms the live, publicly served notebook is the actual post-WP62/63
content, not a cached prior build.

## Tests run (this WP's own additions, beyond WP62's)

| Command | Result |
|---|---|
| `python3 scripts/generate_exercise_04_notebook.py --check` (after each edit) | OK, every time |
| `.venv/bin/python -m unittest discover -s tests -p 'test_exercise_04_lite_notebook.py'` | 36/36 passed |
| `.venv/bin/python -m unittest discover -s tests -p 'test_exercise_04_reference_execution.py'` | 17/17 passed |
| `.venv/bin/python -m unittest discover -s tests -p 'test_wp19_content_audit.py'` (new) | 14/14 passed |
| `npx playwright test --config playwright.book.config.ts exercise-04-lite.spec.ts` (full parallelism) | 4/6 passed, 2 failed — traced to local CPU contention (this suite's own documented, pre-existing issue) and a locator strict-mode bug in my own new assertion (`.jp-OutputArea-output` resolving to 2 elements on a cell with both a displayed table and a print); fixed |
| Same, `--workers=1` (CI's own setting) | **6/6 passed** |
| CI run 41711669876 (full gate) | failure — 1 Python test (see above) |
| CI run 41799270728 (full gate) | failure — 2 Playwright book tests (see above) |
| **CI run 41823269119 (full gate)** | **success** |

No test was weakened or deleted to make it pass; both fixed assertions now
check the actually-current, intentional policy.

## Scope discipline

Touched: `scripts/generate_exercise_04_notebook.py` (comments only), its
four generated notebook copies, `tests/test_wp19_content_audit.py`, and
`interactive/e2e-book/exercise-04-lite.spec.ts`. No production model/text
logic changed in this WP — only comment wording (per the five specified
edits) and the two stale test files CI identified. `book/_build/` (local
build output used for verification) was never staged or committed.

## Local preview server

The one local JupyterLite preview server started for WP62's review
(port 8890) was shut down before this WP's merge/push work began,
confirmed unreachable (`curl` returned no response). No other local
service was touched.

## Deviations from the WP

The WP anticipated only the five comment edits plus a clean merge/push/
deploy. It did not anticipate needing two additional fix-forward commits
— both were real, CI-caught staleness bugs in test files outside this
WP's originally-scoped file list (`tests/test_wp19_content_audit.py` and
`interactive/e2e-book/exercise-04-lite.spec.ts`), not scope creep into new
features. Both are documented above and were fixed, verified locally, and
re-pushed rather than reverted around.

## Confirmation

The deployed, live SHA is `f3fc6ed` (unchanged — nothing further was
rebuilt or redeployed). This report and its changelog were committed and
pushed as a separate, documentation-only commit afterward
(`WPs/reports/WP63_REPORT.md`/`WP63_EXACT_CHANGELOG.md`); because
`.github/workflows/deploy.yml` excludes `WPs/**` from its trigger path,
that push did not start a new deploy run — confirmed directly: no run
exists for that commit's SHA in `gh run list`, and the most recent run
remains `41823269119` against `f3fc6ed`. `main`'s current tip is
therefore that documentation commit, not `f3fc6ed`; read the exact SHA
from a fresh `git log` rather than this line, per this report's own
cannot-self-reference convention. Nothing else was pushed or started
beyond this WP's own scope.
