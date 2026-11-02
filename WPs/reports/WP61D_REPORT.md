# WP61D Report — Exercise 11 (Embeddings and RSA) release to production

## Success or failure — read this first

**Success.** Exercise 11, built by WP61 and revised by WP61R, is now
published to production exactly as approved: the same notebook content
and measured results (RDM distances, `face_match_r = 0.247`,
`animacy_match_r = 0.446`), with no changes beyond the release wiring
(manifest, Contents navigation, portable download, placeholder-guard
tests) this WP added. **Pushed once, merged to `main`, CI ran the full
gate end-to-end and deployed successfully, and the live site has been
verified directly** — Contents, the Exercise 11 page, its JupyterLite
launch, its portable download, the CSV/manifest data links, Resources/
References, and that Exercises 10 and 12 still behave as before.

## Branch, commits, CI, deploy

- Continued on `feature/wp61-embeddings-and-rsa` from WP61R's last commit
  (`1502602`).
- WP61D implementation commit: `f7d2f6f` ("WP61D: release Exercise 11
  (Embeddings and RSA) to production").
- Merge commit on `main`: `5213265` (`c056b01..5213265`, `--no-ff`,
  fast-forward-able — `main` was a direct ancestor of the feature branch,
  so the merge was clean with no conflicts).
- Pushed once: `git push origin main` (`c056b01..5213265`). No second
  push was needed — the first push's CI run was green.
- CI run: [41316133201](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/41316133201)
  — classify job: `full` gate (expected: this release touches several
  shared paths — `book/_toc.yml`, `book/config/exercise_manifest.json`,
  `interactive/e2e-book/launch-buttons.spec.ts`,
  `interactive/e2e-book/warning-sweep.spec.ts` — which the classifier
  (`scripts/classify_release_change.py`) treats as shared/unknown and
  escalates to `full` regardless of its own `PUBLISHED_EXERCISE_NUMBERS`
  range, which still only covers 1-9 and was intentionally left
  unchanged, matching the same gap already present for Exercise 12 since
  WP57) — **succeeded in full**, 2h16m57s (14:25:38–16:42:35 UTC), every
  step from "Check out repository" through "Publish website" green,
  including the full `npm run test:e2e:book` Playwright run against the
  combined book + JupyterLite build.
- Deployed SHA: `5213265` — confirmed via the `gh-pages` branch's own
  deploy marker commit `c399170` ("deploy:
  5213265c745f7fbdf3d37e96b75e9fced63713c7").

## What WP61D changed (release wiring only — no notebook-content change)

- `book/config/exercise_manifest.json`: Exercise 11 moves to
  `migrationState=migrated`, with full lite wiring
  (`templateNotebookPath`, `browserWorkingCopyName`, `liteUrl`,
  `templateVersion=1`, `dataAssets` for `haxby_rsa_patterns.csv`/
  `.manifest.json`) and `fallbackDownloadablePath` pointing at the new
  `downloads/chapter_11/exercise_11_portable.ipynb`.
- `scripts/generate_exercise_11_notebook.py`: added `PORTABLE_PATH`
  (`book/downloads/chapter_11/exercise_11_portable.ipynb`) to the
  student-mode write loop, alongside the already-shipped lite template
  and served portable copy — all three byte-identical, same as every
  other migrated exercise.
- `scripts/generate_exercise_11_transition_page.py` (new): replaces the
  old titled "coming later" placeholder stub
  `book/chapters/chapter_11/exercise_11.md` with a short transition page
  at `book/chapters/chapter_11/exercise_11.ipynb`, linking to the
  JupyterLite notebook and its downloadable copy — modeled directly on
  `scripts/generate_exercise_09_transition_page.py` and
  `scripts/generate_exercise_12_transition_page.py`.
- `book/_toc.yml` / `book/_config.yml` / `book/_static/launch-buttons.js`:
  comments updated to describe Exercise 11 as published, not pending; no
  functional change was needed (the toc entry, `exclude_patterns`, and
  the already-empty `PAGE_TO_PORTABLE` map already covered this shape
  correctly).
- Placeholder-guard and course-wide tests updated to match, each
  following its own file's established precedent for a prior exercise's
  release (WP52/WP57R/WP59):
  `tests/test_placeholder_exercises.py` (`PLACEHOLDER_TITLES` is now
  empty — Exercise 11 was the last placeholder in this file's
  convention), `tests/test_book_structure.py` (replaces the Exercise 11
  placeholder assertion with one confirming it is published),
  `tests/test_exercise_manifest.py` (migrated set is now
  `[1..9, 11, 12]`), `tests/test_wp25_content_audit.py` (Exercise 11's
  title now read from its `.ipynb` like every other exercise),
  `tests/test_exercise_11_lite_notebook.py` (replaces the "no downloads
  copy yet" guard with an identity check against the new, real portable
  download), new `tests/test_exercise_11_transition_page.py` (mirrors
  the other exercises' own transition-page test files),
  `interactive/e2e-book/launch-buttons.spec.ts` (Chapter 11's placeholder
  test replaced with a "migrated, no Colab button" test),
  `interactive/e2e-book/warning-sweep.spec.ts` (adds 11 to the
  course-wide published-exercises list).

## Verification

### Local, before pushing

- Full offline suite: `python -m unittest discover -s tests` — **1424
  tests, 11 pre-existing skips, 0 failures** (~24 min; the suite is
  genuinely this size, not stuck — re-confirmed by a second run after a
  late fix, below).
- `scripts/generate_exercise_11_notebook.py --check`,
  `scripts/generate_exercise_11_transition_page.py --check`,
  `scripts/export_haxby_rsa_data.py --check` — all OK.
- `jupyter-book build book` and `jupyter lite build` — both clean, same
  two pre-existing warnings as every prior release (missing `logo.png`,
  `README.md` not in any toctree).
- Real-browser Playwright run of `exercise-11-lite.spec.ts` +
  `launch-buttons.spec.ts` against the built book (served locally via
  `interactive/e2e-book/serve-book.mjs`): **17/17 passed**, including
  both Exercise 11 lite-notebook tests (untouched template and
  teacher-completed path) and the new "Chapter 11 migrated, no Colab
  button" test.
- Local-server checks before pushing: Exercise 11's page, its
  JupyterLite route, both `exercise_11*.ipynb` files, the CSV, and the
  manifest JSON all resolved **200**; the manifest JSON's license field
  showed the corrected CC BY-SA 3.0 text; `resources.html`'s manifest
  link resolved **200**. The portable notebook's data-loading fallback
  URL (`https://raw.githubusercontent.com/.../main/book/lite/files/data/haxby_rsa_patterns.csv`)
  was confirmed to point at the exact path this push would publish —
  correctly **404** at that point, since it was not yet on `main`.
- One mid-process correction, caught before committing: the new
  transition-page generator's cell ids were first written as
  `wp62-transition-title`/`wp62-transition-body` (an initial WP-number
  guess) before this WP was relabeled `WP61D` per author direction;
  fixed to `wp61d-transition-title`/`wp61d-transition-body`, the
  notebook regenerated, and the full local verification pass (offline
  118-test focused suite, book + lite rebuild, 17-test Playwright run)
  repeated and reconfirmed green before pushing.

### Live, after deploy (`https://yoavmp.github.io/ml-neuro-tutorials`)

All checked directly against the deployed site, not assumed from CI logs:

| Route | Result |
|---|---|
| `/index.html`, `/contents.html` | 200; Contents lists "Exercise 11: Embeddings and RSA" linking to `chapters/chapter_11/exercise_11.html` |
| `/chapters/chapter_11/exercise_11.html` | 200; title "Exercise 11: Embeddings and RSA"; links to `lite/notebooks/index.html?path=exercise_11.ipynb` and `lite/files/exercise_11_portable.ipynb` |
| `/lite/notebooks/index.html` (JupyterLite launcher) | 200 |
| `/lite/api/contents/all.json` | lists both `exercise_11.ipynb` and `exercise_11_portable.ipynb` |
| `/lite/files/exercise_11.ipynb` | 200; valid notebook, nbformat 4, 40 cells, first cell matches the approved content |
| `/lite/files/exercise_11_portable.ipynb` | 200 |
| `/lite/files/data/haxby_rsa_patterns.csv` | 200 |
| `/lite/files/data/haxby_rsa_patterns.manifest.json` | 200 |
| `https://raw.githubusercontent.com/yoavmp/ml-neuro-tutorials/main/book/lite/files/data/haxby_rsa_patterns.csv` (the portable notebook's fallback URL) | 200, now that it is actually on `main` |
| `/resources.html` | 200; links the Haxby source (`pymvpa.org/datadb/haxby2001.html`) and the course manifest (`haxby_rsa_patterns.manifest.json`) |
| `/references.html` | 200 |
| `/chapters/chapter_10/placeholder.html` | 200; still titled "Exercise 10: Deep Learning", unchanged by this release |
| `/chapters/chapter_12/exercise_12.html` | 200; still titled "Exercise 12: Common Mistakes and Pitfalls", links to "Open Exercise 12", unchanged by this release |

No real Google Colab verification was performed in this WP — same
caveat as every prior release (WP49/WP52/WP57/WP59): the download link
and the raw-GitHub fallback URL are confirmed reachable and correct, but
actually opening the notebook in Colab and running it there is **not
done and should be treated as pending**, not assumed.

## Deviations from the plan

None of substance. The release followed the established WP51→WP52,
WP57→WP57, WP58→WP59 pattern exactly, reusing each file's own prior
precedent rather than inventing a new shape. The only correction made
along the way was the WP-number relabeling of the new transition page's
cell ids (`wp62-` → `wp61d-`, see above), caught and fixed before the
first push — not a deviation visible in the shipped result.

## Confirmation

`main` is at `5213265`, deployed and live. Exercise 11 is published
alongside Exercises 1–9/12; Exercise 10 remains a titled Colab/local-only
download page, unchanged. No further action pending except the
author's own real-Colab check, noted above as not performed here.
