# WP59 Report — Exercise 10 wording fixes and release to production

## Summary

Continued on `feature/wp58-active-exercise-10-deep-learning` (branched
from `main` at `c94628f`, where WP58 built Exercise 10's notebook locally
only). This WP (1) made four specific wording changes to the generator
and regenerated both notebooks, (2) published Exercise 10 to the live
site as a Colab/local-Jupyter-only download page, replacing the "coming
later" placeholder, and (3) fixed every stale course-wide test assumption
that referenced the old wording or placeholder state. **Pushed once,
merged to `main`, CI ran the full gate end-to-end and deployed
successfully, and the live site was verified directly** — Contents,
the Exercise 10 page, the download link, and the GitHub Contents API
endpoint Colab's loader uses.

- WP59 implementation commit: `d4342c8`
- Merge commit on `main`: `8fdec82` (`c94628f..8fdec82`)
- CI run: [38724820626](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/38724820626)
  — classify job: `full` gate (confirmed both by the classifier's own
  reasoning, reproduced locally, and by observing the full-gate-only
  steps — e.g. "Type-check and unit-test the frontend" — actually execute
  rather than skip) — **succeeded in full, 1h53m55s**, `Publish website`
  step ran and succeeded.
- Non-blocking companion workflow `Legacy notebook smoke test (Exercise
  10)` (triggered because `book/downloads/chapter_10/**` changed; smoke-
  tests the *old*, untouched legacy portable notebook, not this WP's new
  one): run [38724820644](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/38724820644),
  **succeeded**, 57s.
- No second push was needed — the first push's CI run was green.

## 1. Four wording changes (generator + both regenerated notebooks)

All four in `scripts/generate_exercise_10_deep_learning_notebook.py`,
applied to the shared cell list both the student and reference notebooks
render from, then regenerated with `--write --all`:

1. **Opening runtime paragraph** replaced with exactly the required text:
   > **This notebook runs in Google Colab or ordinary local Jupyter
   > (Python 3.11 or later) only.** It is not available through this
   > course's in-browser JupyterLite launcher. Open this notebook
   > directly in Colab or in a local Jupyter installation.

   (Dropped the old sentence naming the WebAssembly/PyPI-wheel reasoning
   and "see the note at the end of Section 1" — both only made sense
   alongside the block removed in the next item.)
2. **Removed the "Note on the JupyterLite limitation (Gate A)" blockquote**
   entirely from the shared cell list (so from both notebooks — the
   Blank/per-mode mechanism only applies to the three tagged `YOUR CODE
   HERE` cells, not this plain markdown cell; the reference notebook was
   never published either way). That cell originally combined this
   blockquote with an unrelated "zero missing values" teaching point in
   one cell; the teaching point was kept as its own cell
   (`wp58-106-missing-values-note`, renamed from
   `wp58-106-jupyterlite-note`) and the blockquote's technical evidence
   (`jupyterlite-pyodide-kernel 0.8.5`, `Pyodide v314.0.5`, the exact
   `micropip.install` failure) stays only in `WPs/reports/WP58_REPORT.md`,
   per the instruction to keep technical verification in the WP report,
   not student-facing content.
3. **Shape explanation** now names the loss function explicitly: "...since
   `BCEWithLogitsLoss` (**our loss function**) expects predictions and
   targets to have matching shapes..." (Section 2's tensor-conversion
   task intro).
4. **Architecture parenthesis** shortened from "(128 units, then 32 units
   -- chosen, along with the learning rate below, by comparing a handful
   of configurations on the *validation* set only, never the test set)"
   to exactly "(128 units, then 32 units)" (Section 3's model intro). The
   dropped validation-only-tuning detail is not lost pedagogically — it
   is still covered by Section 5's intro paragraph and the
   `q-test-set-choices` checked question.

**Verified these are markdown-only changes** (`git diff` on both
regenerated `.ipynb` files inspected directly — every changed hunk is
inside a `"cell_type": "markdown"` cell's `source`; zero code cells
changed, cell count unchanged at 44 in each notebook). Re-executed the
regenerated `scripts/reference_notebooks/exercise_10_deep_learning_reference.ipynb`
end-to-end (`jupyter nbconvert --to notebook --execute`) in a **fresh**
Python 3.11.16 virtualenv (`python3.11 -m venv`, `numpy<2`, `torch==2.2.2`
CPU wheel — same recipe WP58 used) created specifically for this check:
**zero errors**, wall time 59.4s (includes venv-cold kernel startup), and
the comparison table's numbers are **identical** to WP58's originally
reported ones (expected, since no code changed):

| Model | Accuracy | Balanced acc. | Sensitivity | Specificity | ROC AUC |
|---|---|---|---|---|---|
| Dummy (majority class) | 0.537 | 0.500 | 0.000 | 1.000 | 0.500 |
| Logistic regression (C=0.003) | 0.552 | 0.547 | 0.473 | 0.620 | 0.601 |
| Neural network | 0.577 | 0.562 | 0.366 | 0.759 | 0.615 |

## 2. Publishing Exercise 10

**Page**: kept the existing file path
`book/chapters/chapter_10/placeholder.md` (minimal diff, and renaming it
risked colliding with the preserved `exercise_10.ipynb` legacy notebook's
own stem in the same directory — the existing `_config.yml` exclude
pattern already relies on `placeholder` and `exercise_10` being different
stems). Replaced its content: title unchanged ("Exercise 10: Deep
Learning"), the same Colab/local-only runtime sentence as the notebook's
own opening, a download link, and an Colab link — no JupyterLite button,
no iframe, no claim that PyTorch runs in this site's in-browser kernel.

**Download/Colab link mechanism**: `book/downloads/` is excluded from the
Jupyter Book build (`book/_config.yml`'s own `exclude_patterns` and
comment: "not published under `_build/html`") and there is no
`html_extra_path` copying it in — confirmed by reading the actual current
config rather than trusting an older, now-stale comment in
`scripts/generate_exercise_02_transition_page.py` that describes a
different, no-longer-true mechanism. I considered instead placing a
plain-static copy under `book/lite/files/` (which *is* served
same-origin), but rejected it: `jupyter lite build` exposes everything
under that directory in the in-browser file browser too, so a student
opening the generic JupyterLite launcher would see this notebook sitting
next to the real browser-executable ones and could try to run it there —
exactly the "import torch" failure Gate A found, and exactly what "no
JupyterLite launch button, no implying PyTorch runs in browser" rules
out. Instead both links use the same `https://colab.research.google.com/
github/<repo>/blob/<branch>/<path>` / raw-GitHub pattern
`book/_static/launch-buttons.js` already uses for other chapters' Colab
buttons — confirmed the GitHub repository is public
(`gh repo view --json visibility` → `PUBLIC`) before relying on this,
since both URLs need the repository to stay public to keep working (the
same disclosed tradeoff `_config.yml`'s own comments already describe for
that existing mechanism).

**Manifest**: updated `book/config/exercise_manifest.json`'s entry 10
`fallbackDownloadablePath` from the old legacy `exercise_10_portable.ipynb`
to this WP's own `exercise_10_deep_learning_portable.ipynb` (the file
actually linked from the published page); `migrationState` stays
`"legacy"` (correct — no JupyterLite wiring, by design) and
`legacyStaticPagePath` stays pointed at the untouched legacy notebook.
Updated the manifest's own top-level `$comment` and `book/_config.yml`'s
exclude-pattern comment block for accuracy (both were shared-surface
files already forcing the full gate regardless).

**Exercise 11**: not touched at all (confirmed `git diff` shows no
changes under `chapters/chapter_11/`). **Legacy Exercise 10**: not
touched (`book/chapters/chapter_10/exercise_10.ipynb` and
`book/downloads/chapter_10/exercise_10_portable.ipynb` both unchanged,
confirmed by `git diff` and by the existing `LegacyExerciseTenUntouched`
test class, which still passes).

**Introduction / Resources**: added a "PyTorch for Exercise 10 (optional)"
subsection to `book/intro.md` (states PyTorch is Colab/local-only, not in
this site's in-browser notebooks, links to
[PyTorch's own installation instructions](https://pytorch.org/get-started/locally/),
gives a plain `pip install torch` example) and one bullet to
`book/resources.md`'s existing "Python and Jupyter documentation" section
linking [PyTorch's documentation](https://pytorch.org/docs/stable/) —
matching the page's existing per-library bullet style, kept separate from
the scholarly citations on `references.md`. Checked both pages still pass
every existing `tests/test_book_structure.py` assertion, including the
negative ones (no `requirements.txt`, no `git clone`, no private-repo URL
on `resources.md`).

## 3. Stale course-wide test/comment assumptions found and fixed

Searched explicitly (not just the one file I expected to touch) with
`grep -rl` across `tests/`, `scripts/`, and `interactive/e2e*` for
`chapter_10`/`Exercise 10`/`exercise_10`:

- `tests/test_exercise_10_deep_learning_notebook.py` — removed/replaced
  the Gate-A-evidence assertions (`test_pyodide_version_and_evidence_named`)
  with a new test asserting that evidence is **absent** from the notebook
  (stays in the WP report only); updated the opening-paragraph assertion
  to the new exact wording; added tests for the new shape-explanation and
  architecture-parenthesis wording; replaced the placeholder-page test
  (`test_placeholder_page_still_says_coming_later`, which would have
  stayed misleadingly named — and have kept passing by accident, since it
  never actually asserted "coming later" text — even after this release)
  with one that asserts the live page correctly links this WP's own
  notebook and not the legacy one.
- `tests/test_book_structure.py` — split the combined
  `test_exercise_10_and_11_placeholders_are_titled_and_not_misleading`
  test: Exercise 11's half is unchanged (renamed only); Exercise 10's half
  is replaced with assertions that it is no longer a stub and correctly
  links the download/Colab URLs.
- `tests/test_placeholder_exercises.py`, `tests/test_wp25_content_audit.py`
  — read both in full; **no change needed**. The former's
  `PLACEHOLDER_TITLES` dict already covered only Exercise 11 (Exercise
  10's placeholder has lived in a differently-named file,
  `chapters/chapter_10/placeholder.md`, since WP49, and was always out of
  this file's scope — its own docstring says so). The latter's
  `EXERCISE_TITLES[10]` and final-project-reference checks both read from
  `chapters/chapter_10/exercise_10.ipynb` — the untouched legacy
  notebook — never from the page this WP changed.
- `tests/test_exercise_manifest.py`, `tests/test_classify_release_change.py`
  — read in full; **no change needed**. The manifest schema tests are
  satisfied by the `fallbackDownloadablePath` update alone (legacy entries
  still correctly have no lite wiring); the classifier tests describe
  Exercise 10 as "legacy/unpublished" meaning "no JupyterLite wiring,"
  which remains true and is unrelated to whether its book page has real
  content.
- `interactive/e2e-book/chapter10.spec.ts` — **confirmed already excluded**
  from the Playwright run (`playwright.book.config.ts`'s `testIgnore`);
  it tests the old legacy iframe-embedded page, which this release does
  not restore. Left excluded (not deleted, per that file's own stated
  intent to keep it as a historical record), but the `playwright.book.
  config.ts` comment explaining *why* was stale ("chapter 10 no longer
  exists in the built book" — false again, now that chapter 10 has a real
  page) and is corrected.
- `interactive/e2e-book/launch-buttons.spec.ts` — the assertion itself
  (`chapter_10/placeholder.html` gets no top-bar Colab button) is **still
  true** after this release, because `launch-buttons.js`'s
  `PAGE_TO_PORTABLE` map deliberately does not include `chapter_10` (its
  own page body already carries the explicit links). Only the test's
  *comment* ("titled 'coming later' stub") was stale; corrected.
- `interactive/e2e-book/iframe-height-contract.spec.ts` — reviewed; its
  exclusion rationale ("nothing to check until Exercise 10+ migrates")
  remains accurate, since this release does not add any iframe to Exercise
  10's page. No change.
- `interactive/e2e-book/warning-sweep.spec.ts` — reviewed; its `EXERCISES`
  list (`[1,2,3,4,5,6,7,8,9,12]`) is scoped to JupyterLite-executed
  exercises only and correctly excludes 10/11 already. No change.

## Verification

**Local, before pushing:**

- Full offline suite: `python3 -m unittest discover -s tests` — **1350
  tests, 0 failures, 0 errors** (up from WP57's reported 1318; +32 net
  from this WP's new/split tests). Took ~22.5 minutes wall time on this
  machine — reported here since it is well over 5 minutes.
- `jupyter-book build book` — succeeds; only the two pre-existing,
  unrelated warnings (`logo.png` missing, `README.md` not in any
  toctree — both present before this WP, confirmed by `git log` on each
  file).
- Inspected the actual built `book/_build/html/chapters/chapter_10/
  placeholder.html` directly: exact `<h1>Exercise 10: Deep Learning</h1>`;
  `has iframe: False`; `has colab-launch-button testid: False`; both the
  raw-GitHub download link and the `colab.research.google.com/github/...`
  link present with the correct repo/branch/path; the `../../intro.html`
  backlink resolved with no Sphinx "unresolved reference" warning.
- `python3 scripts/classify_release_change.py --format json` —
  confirmed `"gate": "full"` locally, for the exact reason expected
  (several touched paths classify as `"shared"`: `book/downloads/`,
  the new generator script, the new reference notebook, the new test
  file — each forces `full` on its own).
- `python3 scripts/smoke_release_routes.py --build-dir book/_build/html
  --pages intro,resources` — both pages' own same-repository links clean.

**After pushing — live, not assumed:**

- `gh run view 38724820626` — `classify` job succeeded; `build-and-deploy`
  job's full-gate-only steps (e.g. "Type-check and unit-test the
  frontend") show `completed/success`, not skipped, confirming the `full`
  gate actually ran, not just was selected; `Publish website` step
  `completed/success`.
- `curl` directly against `https://yoavmp.github.io/ml-neuro-tutorials/`:
  - `contents.html` contains `href="chapters/chapter_10/placeholder.html"`.
  - `chapters/chapter_10/placeholder.html`: `<h1>Exercise 10: Deep
    Learning</h1>`; zero occurrences of "Materials for this exercise will
    be added"; the exact raw-GitHub download `href` and the exact
    `colab.research.google.com/github/...` `href`; zero `<iframe>`; zero
    `colab-launch-button` test ids.
  - `intro.html` contains the "PyTorch for Exercise 10 (optional)"
    section, its `pytorch.org/get-started/locally/` link, and its
    `pip install torch` code block (confirmed by reading the rendered
    HTML directly, since Pygments splits that line across `<span>`
    elements that defeat a naive substring search).
  - `resources.html` contains `href="https://pytorch.org/docs/stable/"`.
- **Download link, fetched live**: `curl -I` on
  `https://raw.githubusercontent.com/yoavmp/ml-neuro-tutorials/main/book/
  downloads/chapter_10/exercise_10_deep_learning_portable.ipynb` →
  `HTTP/2 200`. Fetched the body and parsed it as JSON: valid nbformat 4.5,
  44 cells, first cell's source is exactly `# Exercise 10: Deep Learning`.
- **Colab link's underlying endpoint, fetched live** (Colab's own
  `/github/` loader resolves through GitHub's Contents API, not the raw
  CDN — checked the actual mechanism, not just the raw file): `curl -I` on
  `https://api.github.com/repos/yoavmp/ml-neuro-tutorials/contents/book/
  downloads/chapter_10/exercise_10_deep_learning_portable.ipynb?ref=main`
  → `HTTP/2 200`, `content-length: 109168`. **This confirms the link's
  target is live and fetchable by the mechanism Colab actually uses — it
  does not confirm Colab's own UI renders/runs it.**
- Non-blocking `Legacy notebook smoke test (Exercise 10)` workflow run
  [38724820644](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/38724820644)
  (triggered by the `book/downloads/chapter_10/**` path match):
  succeeded, 57s — it smoke-executes the *old* legacy portable notebook
  (unaffected by this WP), not this WP's new one; recorded here only to
  confirm it did not regress.

**Explicitly NOT verified — reported as unverified, not claimed:**

- **Real Google Colab execution.** No browser/Colab session was opened.
  "Colab link works" here means: the exact URL Colab's loader would fetch
  returns `200` with valid notebook JSON at the exact path the link
  points to — not that Colab's own UI was opened and the notebook was run
  there. This matches every other active exercise in this course (see
  `book/config/exercise_manifest.json`'s own `$comment`).
- **Real JupyterLite-build verification of the "no browser PyTorch" claim**
  was not re-run this WP — it is WP58's own already-recorded evidence
  (Pyodide lockfile + live headless-Chromium `micropip.install` attempt,
  `WPs/reports/WP58_REPORT.md`), unchanged by this WP's purely
  markdown-level edits.

## Deviations

1. Kept `book/chapters/chapter_10/placeholder.md`'s **filename** unchanged
   rather than renaming it to something that no longer says "placeholder"
   — a judgment call favoring minimal diff and avoiding any stem collision
   with the preserved `exercise_10.ipynb` in the same directory (not asked
   for either way; flagged here since the filename no longer accurately
   describes the page's content).
2. Did not add Exercise 10's new portable notebook to any CI execution
   smoke test (the non-blocking `legacy-notebook-smoke.yml` workflow still
   only covers the *old* legacy notebook). This WP's own local re-execution
   (above) covers the same ground once; wiring continuous CI coverage for
   it was judged out of scope for a wording-and-release WP and is noted
   here as a candidate follow-up, not performed.

## Status

Clean on `main` at `8fdec82` after CI succeeded and the site deployed.
This report and `WPs/reports/WP59_EXACT_CHANGELOG.md` are committed
separately (`WPs/**` is excluded from the deploy workflow's trigger paths,
so that commit does not re-run CI).
