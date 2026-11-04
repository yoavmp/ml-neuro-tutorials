# WP63 Exact Changelog

## Starting point

Local `main` at `af0cde5` (the WP62/WP63 merge commit, pushed to `origin`
in this same session).

## Commits (in order)

```
a31c3d9 WP63: add WP document (checkpoint before implementation)
5a05415 WP63: student-facing comment cleanup in Exercise 4
af0cde5 Merge revise/exercise-04-validation-split into main (WP62/WP63)
88144fa WP63: fix stale WP19 content-audit assertion for Exercise 4's new C-selection policy
f3fc6ed WP63: update Exercise 4 book e2e spec for the three-way split and validation-based C selection
```

`a31c3d9` and `5a05415` were made on `revise/exercise-04-validation-split`
and merged into `main` via `af0cde5` (`--no-ff`). `88144fa` and `f3fc6ed`
were made directly on `main`, each in response to a specific CI failure
on the preceding push (see `WP63_REPORT.md`, "What CI caught").

**Final pushed/deployed SHA: `f3fc6ed650688ffdb8db6ece807cfca4e68ad5fb`.**

## Files created

- `WPs/WP63_EXERCISE_04_COMMENT_CLEANUP_AND_RELEASE.md` — the WP
  specification, committed alone in `a31c3d9`.
- `WPs/reports/WP63_REPORT.md` — this WP's report.
- `WPs/reports/WP63_EXACT_CHANGELOG.md` — this file.

## Files modified, commit `5a05415` (the five comment edits)

```
 book/downloads/chapter_04/exercise_04_portable.ipynb |  ~15 ++----
 book/lite/files/exercise_04_portable.ipynb           |  ~15 ++----
 book/lite/files/v2/exercise_04.ipynb                 |  ~15 ++----
 scripts/generate_exercise_04_notebook.py             |  ~15 ++----
 scripts/reference_notebooks/exercise_04_reference.ipynb | ~15 ++----
 5 files changed, 30 insertions(+), 60 deletions(-)
```

All five generated/reference copies were produced exclusively by
`python3 scripts/generate_exercise_04_notebook.py --write` from the
edited generator — never hand-edited — and confirmed idempotent by a
subsequent `--check`.

### `scripts/generate_exercise_04_notebook.py` comment changes

1. `wp44-102-load`: `# Load the approved ABIDE-II classification table: ...`
   → `# Load the ABIDE-II classification table: ...`.
2. `wp44-104-labels`: two-line raw-code verification comment → `# Verify data`.
3. `wp44-104-labels`: three-line recode comment →
   `# In the original dataset, 1 = autism, 2 = control. Change the labels
   to 0 = control, 1 = autism before proceeding.` (the mapping line
   `df["group"] = df["group"].map({1: 1, 2: 0})` itself unchanged).
4. `wp44-303-imports`: dropped the second comment line
   (`# validation set below -- not adjusted after seeing any result.`);
   reworded the remaining line to
   `# A small, predetermined set of candidate C values to compare.`
5. `wp44-324-check`: shortened the four-line check-cell comment to the
   exact two lines specified.

## Files modified, commit `88144fa` (content-audit fix)

```
 tests/test_wp19_content_audit.py | 27 ++++++++++++++++-----------
 1 file changed, 16 insertions(+), 11 deletions(-)
```

`NotebookContentAudit.test_classification_uses_fixed_c1_language` renamed
to `test_classification_selects_c_via_a_validation_set`; now asserts
`"C_GRID = [0.01, 0.1, 1.0, 10.0, 100.0]"` is present and
`"C_EXAMPLE = 1.0"` is absent in `book/downloads/chapter_04/exercise_04_portable.ipynb`,
with an updated comment explaining why Exercise 4 left this audit's
"early, pre-cross-validation zone" (mirroring the existing comment pattern
for Exercise 3). `NOTEBOOK_PATHS`, `PROHIBITED_PATTERNS`, and every other
test in the file are unchanged.

## Files modified, commit `f3fc6ed` (book e2e spec fix)

```
 interactive/e2e-book/exercise-04-lite.spec.ts | 64 ++++++++++++++++++++-------
 1 file changed, 48 insertions(+), 16 deletions(-)
```

In `interactive/e2e-book/exercise-04-lite.spec.ts`:

- Header comment: "the train/test split" → "the train/validation/test split".
- `"every activity ... degrades gracefully"` test: updated the split
  check's anchor text to the new six-variable guard message; added a new
  assertion for the new C-selection cell's own "not complete yet" guard;
  updated the final-fit guard's anchor text to the new seven-name-guard
  message; updated the imbalance-widget guard's anchor text to its new
  wording (`"Section 3's X/y and C-selection activities first"`).
- `"filling in every blank ..."` test: the split blank's typed solution
  changed from the single `train_test_split` call to the two sequential
  calls producing train/validation/test; the post-split assertion changed
  from a fixed-fraction `scrollWindowed` + whole-body text check (brittle
  against the notebook's new, longer cell count) to a `scrollToVisible`-
  anchored check for the new `"n_train = 564   n_val = 189   n_test =
  251   n_features = 360"` text; added a new assertion for the
  C-search cell's own `"selected C = 0.1"` print (using `.last()` on its
  output-area locator, since that cell has two output blocks — the
  displayed validation table and the print); the two old fixed-fraction
  accuracy/AUC checks (`"accuracy = 0.546"`, `"Looks good: AUC=0.569"`)
  replaced with `scrollToVisible`-anchored checks for the new
  `"accuracy = 0.534"` / `"Looks good: AUC=0.580"` results.

## Files explicitly not touched

Every file outside the five Exercise-4-generator-owned copies,
`tests/test_wp19_content_audit.py`, and
`interactive/e2e-book/exercise-04-lite.spec.ts` — confirmed by
`git diff --stat af0cde5..f3fc6ed` (2 files) plus the WP62 scope-discipline
list (still honored: `scripts/classification_model_audit.py` and its
JSON, the threshold/imbalance export scripts, and
`book/chapters/chapter_04/exercise_04.ipynb` remain untouched).

## Release

- Merge: `af0cde5` (`revise/exercise-04-validation-split` → `main`,
  `--no-ff`), pushed as `7e3a348..af0cde5`.
- Fix-forward pushes: `af0cde5..88144fa`, then `88144fa..f3fc6ed`.
- GitHub Actions runs (branch `main`, workflow "Build and deploy Jupyter
  Book"):
  - `41711669876` (`af0cde5`) — **failure** (Python content-audit test).
  - `41799270728` (`88144fa`) — **failure** (2 Playwright book tests).
  - `41823269119` (`f3fc6ed`) — **success**, full gate, ≈2h3m
    (2026-11-04T11:43:42Z–13:47:15Z).
- Published via `peaceiris/actions-gh-pages@v4` to the `gh-pages` branch.
- Deployed `gh-pages` commit:
  `8d72a13169170921b31482dca0d6211d5d9f58d0` — `"deploy:
  f3fc6ed650688ffdb8db6ece807cfca4e68ad5fb"`, 2026-11-04T13:47:09Z.
- Live verification: `GET` on the published
  `lite/files/v2/exercise_04.ipynb` and
  `chapters/chapter_04/exercise_04.html` both returned 200; the fetched
  notebook's bytes were parsed and confirmed to contain the new `C_GRID`,
  the new comment wordings, and the new split stub, and to lack the old
  `C_EXAMPLE = 1.0` and "approved ABIDE-II" text.

## Final state

```
f3fc6ed (HEAD -> main, origin/main) WP63: update Exercise 4 book e2e spec for the three-way split and validation-based C selection
88144fa WP63: fix stale WP19 content-audit assertion for Exercise 4's new C-selection policy
af0cde5 Merge revise/exercise-04-validation-split into main (WP62/WP63)
5a05415 WP63: student-facing comment cleanup in Exercise 4
a31c3d9 WP63: add WP document (checkpoint before implementation)
```

`main` and `origin/main` are both at `f3fc6ed`, deployed and live.
