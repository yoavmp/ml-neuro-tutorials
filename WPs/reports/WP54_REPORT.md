# WP54 report: course pages, Exercise 6/9 figure fixes, and release

## Success or failure -- read this first

**Success.** Every numbered requirement in WP54 is applied, the full
offline test suite (1201 tests) and the full combined Jupyter Book +
JupyterLite Playwright suite (124 tests, including one new permanent test
this WP added) both pass, the production deploy succeeded on the actual
`full` release gate, and the live site has been verified directly against
its real published HTML/notebook content.

## Starting state and branch

Began at `main` tip `5cfa89c` ("WP53: reports..."), matching WP54's own
starting point. Checkpoint branch `checkpoint/wp54-pre-work` created at
that tip before any edit; work done on
`feature/wp54-course-pages-and-notebook-fixes`. The WP spec itself is
committed as `WPs/WP54_COURSE_PAGES_NOTEBOOK_FIXES_AND_RELEASE.md`
(`6e50502`).

## Source-document verification (syllabus docx)

Read the supplied syllabus document (`סילבוס למידה חישובית תשפז.docx`,
`~/Downloads`) completely, cell-by-cell via `python-docx` (not the earlier
flattened-text transcription in the WP spec, which ran adjacent table
cells together ambiguously in a few rows). The WP spec's own course-book
link (`https://hastie.su.domains/ISLP/ISLP_website.pdf.download.html`) was
confirmed present in the docx's own hyperlink relationships.

**Discrepancies found between the WP spec's transcription and the actual
document, corrected against the document per WP54's own instruction:**

| Row | WP spec said | Document actually says | Syllabus page now says |
|---|---|---|---|
| Week 2 homework | "EDA and regression" | "EDA + KNN regression (try different k's, theoretical questions on how k relates to the bias-variance trade-off)" | matches document |
| Week 4 practice | "Cross-validation and nested cross-validation" | "CV vs train/test, example on classification, regression" (no mention of nested CV) | matches document |
| Week 5 homework | "Logistic-regression classification; Ridge/Lasso regression" | "Ridge/lasso regress + logreg classify with tuning in nested cv?" (the nested-CV detail, itself tentative, belongs here, not Week 4) | matches document, with "(tentative)" |
| Week 6 practice | "Trees and ensembles" | "Trees (start)" (ensembles are this week's *lecture* topic, not confirmed for practice) | matches document |
| Week 7 homework | "Trees" | "Classification using: Trees/LDA" | matches document |
| Week 9 homework | "Unsupervised learning and advanced models" | "PCA and Kernel in all previous models, Knn, ridge, sum" | matches document, with a flagged note (next row) |

One residual: the document's own Week 9 homework cell literally reads
"...Knn, ridge, **sum**" -- almost certainly a typo for "SVM" (that week's
own lecture topic is "PCR, PLS, SVM, Kernels"). Rendered as "SVM" on the
page with an explicit, visible footnote disclosing the source's literal
text and that this is an unconfirmed correction, not silently "fixed" --
not independently confirmed with the course author.

No other discrepancies found; every other fact in WP54's transcription
(course number, semester, times, staff/contact, aims, course text link,
assessment weights, "in pairs", the other 11 schedule rows) was verified
character-for-character against the document and is unchanged.

## Acceptance table

### 1. Question-cell audit and old-copy guidance

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Visible question cells across Exercises 1-9 call only `show_question(id)`, never `correct_index`/`correct_indices` | Done -- no code change needed | Scripted audit of all 9 published `exercise_0N.ipynb`: the only cells where `show_question(` and `correct_index`/`correct_indices` co-occur are each exercise's own hidden setup cell (`metadata.jupyter.source_hidden: true`), which legitimately defines the shared `show_question()` helper and the `_QUESTIONS` answer-key dict. No other cell in any of the 9 notebooks matches. Confirms the author's own diagnosis: the apparent leaks were old saved browser working copies, not a defect in the currently published templates. |
| 2 | Introduction explains downloading an old copy first, then Reset from course template | Done | New "Opening an old downloaded copy later" section in `book/intro.md`, written against the actual toolbar implementation (`book/lite/extensions/course-toolbar/src/index.ts`): names the real button label "Reset from course template", states it discards in-browser edits for that notebook and fetches the current template, and that it never touches an already-downloaded `.ipynb`. No global-browser-storage-deletion instruction, no automatic-migration claim. |
| 3 | Fresh-browser check of Exercises 1 and 2's question cells/feedback | Done, via existing coverage -- no new notebook code needed | `exercise-01-lite.spec.ts`/`exercise-02-lite.spec.ts`'s own teacher-completed-path tests (unchanged by this WP) click each checked question by its own option **text** and assert the "Correct."/feedback text renders, confirming the visible `show_question()` call and post-WP53-shuffle feedback live, in a real browser, as part of the full combined suite run below. No notebook 1/2 code change was needed or made. |

### 2. Exercise 6 regression-tree diagram

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Root cause fixed: no more `zip(order, artists)` against `plot_tree`'s own artist list | Done | Confirmed the exact bug mechanism by reading sklearn 1.9.0's own `_MPLTreeExporter.recurse()` (`.venv/lib/python3.12/site-packages/sklearn/tree/_export.py`): for each of the root's two children it emits a **second**, un-requested "True"/"False" edge-label `Annotation`, which shifts every later `zip()` pairing against a separately preorder-walked node list by one, silently mislabeling 13 of 15 nodes (2 are left with `plot_tree`'s own unedited default text). `format_tree_diagram()` no longer calls `plot_tree` at all -- it reads `children_left`/`children_right`/`feature`/`threshold`/`n_node_samples`/`value` directly off the fitted tree's own `tree_`, once per node. |
| 2 | Every node's displayed identity/count/value compared directly against `tree_` | Done | Refit the actual published model (`max_depth=3, min_samples_leaf=20, random_state=42`) against the actual published `abide_age_brain.csv`: 15 nodes, 8 leaves; root `n=564`, `age=15.2`, split `Left 3a thickness <= 1.799`; children `n=95`/`n=469`; leaves left-to-right `(26,33.7),(20,24.6),(21,22.6),(28,19.3),(63,20.1),(78,14.7),(180,12.7),(148,10.0)` -- matches WP54's own stated figures exactly. New permanent test `tests/test_exercise_06_reference_execution.py::test_tree_diagram_renders_every_node_directly_from_tree_` re-derives every node's expected label independently (not by reusing the generator's own function) and asserts it appears verbatim in the real rendered `Figure`'s `Text` artists; separately asserts every parent's `n_node_samples` equals the sum of its two children's, for all 15 nodes; asserts no node is left with `plot_tree`'s own unedited `"squared_error = "` text. |
| 3 | Readable layout: root at top, two complete subtrees in stacked, labeled `<=`/`>` panels | Done | Root box at top; `<=`/`>` panel titles state the exact branch condition and count (`<= 1.799 branch (n = 95)` / `> 1.799 branch (n = 469)`); each panel is a full 3-level subtree (its own 3 internal nodes + 4 leaves), laid out via a generic in-order-leaf-position/mean-of-children algorithm, drawn with wrapped 3-line labels, generous box padding (taller leaves), and short local arrows labeled `<=`/`>` between each parent and child. No original `plot_tree` default-label layer anywhere. ASCII `<=`/`>` used throughout (matching sklearn's own `plot_tree` convention) rather than a Unicode `≤`, keeping the generator source plain ASCII like every other exercise generator. |
| 4 | Kept in the executable notebook, not a screenshot | Done | `format_tree_diagram()` is defined and called live in the notebook's own code cell (`wp46-106-diagram`), executed by JupyterLite, the portable download, and the reference notebook alike -- confirmed identically regenerated into all four output paths. |
| 5 | Desktop and 390px browser checks on the real build | Done | `exercise-06-lite.spec.ts`: desktop test confirms real measured `naturalWidth=1250`/`naturalHeight=1311` (portrait, `height > width`, confirming the stacked-panel layout) -- thresholds set with headroom below that **measured** value (Jupyter's inline backend saves with a tight bbox, cropping empty margin, so the raw canvas-size x dpi arithmetic overstates the true raster; this was caught live, not assumed). New permanent 390px test runs the untouched template for real at a 390px viewport, confirms the displayed image width fits the viewport while the underlying raster keeps its full resolution (no blur from downscaling), and that the page itself still has zero horizontal overflow. |

### 3. Exercise 9 PCR-versus-PLS interactive

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | "PLS direction" label moved below "PC2 (fixed)" | Done | Both labels anchored at fixed `axes fraction` positions in a dedicated corner (`(0.98, 0.09)` / `(0.98, 0.025)`) -- same x, PLS strictly below PC2 -- rather than either label's own (PC2: fixed but shared with its arrow's tip; PLS: w1-rotating) data-coordinate position. |
| 2 | Neither label covers points/arrows/colorbar at any checked setting | Done | Rendered at every combination of weight in `{0, 0.25, 0.5, 0.9, 1.0}` x components in `{1, 2}` (10 renders) during development; the original anchor-at-PC2's-own-arrow-tip placement was found, live, to let the PLS/true-signal arrows (collinear with PC2 at `w1=0`) draw directly across the "PC2 (fixed)" text -- fixed by moving to the dedicated empty-margin corner instead of merely offsetting from the arrow tip. New permanent test `tests/test_exercise_09_reference_execution.py::test_pcr_pls_pc2_and_pls_labels_sit_in_a_fixed_corner_never_on_an_arrow` re-runs the actual widget across all 10 settings and asserts, via the real rendered `Annotation`/arrow-patch `get_window_extent()` bounding boxes, that neither label's box ever overlaps any of the four arrow patches. Arrow directions and underlying data are unchanged -- only the two labels' own anchor points moved. |

### 4. Syllabus page

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | English rendering of the attached syllabus, scannable sections | Done | `book/syllabus.md`: course information, aims/prerequisites, staff/contact/office hours, course text, assessment, 13-row schedule -- all sections WP54 named. |
| 2 | Every named fact included, nothing invented | Done | Course `1501.1027`, Semester A 2026-27, Mondays 08:30-11:00 (location explicitly stated as not provided), lecturer/TA names and emails, required/recommended prerequisites, course text with the embedded free-PDF link and `statlearning.com`, 10%/45%/45% grading, "in pairs" -- verified against the docx cell-by-cell (see discrepancy table above). No room, due date, policy, or confirmed-but-unconfirmed topic invented. |
| 3 | Tentative topics marked provisional | Done | Week 4 "bootstrap *(tentative)*" and Week 5's nested-CV tuning detail *(tentative)*, Week 12 "Intro to LLMs *(tentative)*" -- the document's own "?" markers, never presented as confirmed. |
| 4 | Does not imply Exercises 10-12 are published | Done | Explicit schedule-section note: "Only Exercises 1-9 are published on this site so far; a scheduled lecture topic for Weeks 10-13 does not mean that week's practice notebook is available yet," linking to Contents. |

### 5. Introduction

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Replaces legacy per-exercise-Colab-link / revealable-guide framing | Done | Old "About the questions" section removed; the now-false "revealable guide"/"genuinely open, no single correct answer" claims removed (every current question is a checked `make_single_choice_question`/multi-select question with a real `correct_index`/`correct_indices` -- confirmed by reading `generate_exercise_01_notebook.py`, no open-ended ungraded question type exists in the current platform). |
| 2 | Supplied code, YOUR CODE HERE, interactive activities, multi-select checked questions with feedback | Done | New "Using the notebooks" section states all four explicitly. |
| 3 | Saving/reopening/downloading, browser-vs-template distinction | Done | Explains autosave-in-browser, the real "Download my notebook" button (verified against `course-toolbar/src/index.ts`), and that a browser copy does not follow you to another browser/device. |
| 4 | Clear choices: in-browser JupyterLite, or download + Colab | Done | Both named explicitly, with a real link to `colab.research.google.com` (an already-established link elsewhere in this repo, e.g. `generate_exercise_01_transition_page.py`). |
| 5 | Local Jupyter/VS Code optional, accurate package list, no requirements.txt instruction | Done | Python 3.11 (verified against `.github/workflows/deploy.yml`'s own pin), `numpy`/`pandas`/`matplotlib`/`scikit-learn`/`ipywidgets` (verified against `book/lite/overrides.json`'s actual preloaded-package list; `seaborn` deliberately **excluded** -- grepped all 9 published notebooks, confirmed unused in any of them, even though the root `requirements.txt` lists it for unrelated maintainer tooling), JupyterLab/VS Code + `ipykernel`, one illustrative `pip install` line -- not a `requirements.txt`/`git clone` instruction. |
| 6 | No environment literally claims Python 3.11 | Done | Explicit: the in-browser platform runs its own bundled Pyodide Python, Colab's runtime version is Colab's own choice -- neither is claimed to be exactly 3.11 (the notebooks' own `kernelspec` only says "Python 3", verified). |

### 6. Resources then References

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Added immediately after Contents, before References, in `_toc.yml` and the visible nav | Done | `book/_toc.yml` order: syllabus, contents, resources, references. Live sidebar nav confirmed in this exact order (see Verification). |
| 2 | Resources: practical, categorized, minimum-required links, all genuinely accessible | Done | Course text (free PDF + `statlearning.com`); datasets/provenance (official ABIDE II site, its own official Phenotypic Data Legend PDF -- discovered via the ABIDE II page's own link, not guessed; the pinned NeuroHackademy `abide2.tsv`; this course's own same-origin `abide_age_brain*.csv`/`abide_phenotypes.csv` exports, explicitly distinguished as curated, not the original release); Python/Jupyter docs (NumPy, pandas, Matplotlib, scikit-learn, ipywidgets, JupyterLite, Colab). Every one of the 14 external links returned HTTP 200 when checked directly (see Verification); no link to private repository internals, no repo-install encouragement. |
| 3 | References: course book leads, consistent bibliography, verified metadata | Done | Course book first; then the ABIDE II dataset's own publication (Di Martino et al. 2017, *Scientific Data*, DOI `10.1038/sdata.2017.10` -- found and metadata-verified via Crossref's API, since the dataset is used throughout but wasn't itself explicitly author-year-cited in any notebook); Bethlehem et al. (2022) and Storsve et al. (2014), both metadata-verified via Crossref against WP54's own given DOIs. A same-origin link to the References page was also added alongside Exercise 5's own existing inline DOI citations (`scripts/generate_exercise_05_notebook.py`) -- additive only; the original DOI links remain the portable, essential citation. |

## Tests added or changed

- `tests/test_exercise_06_lite_notebook.py`: replaced the stale WP53
  `figsize=(15, 9), dpi=140` structural assertion with one that asserts
  the *mechanism* changed (`ct.children_left`/`ct.n_node_samples`/no
  `plot_tree(`/no `zip(order, artists)`/stacked-panel structure present).
- `tests/test_exercise_06_reference_execution.py`: new
  `test_tree_diagram_renders_every_node_directly_from_tree_` (node-by-node
  verification, described above).
- `tests/test_exercise_09_lite_notebook.py`: new structural assertion for
  the fixed-corner anchors.
- `tests/test_exercise_09_reference_execution.py`: new
  `test_pcr_pls_pc2_and_pls_labels_sit_in_a_fixed_corner_never_on_an_arrow`
  (10-setting live bounding-box verification, described above).
- `tests/test_book_structure.py`: the WP09-era `test_syllabus_is_title_only`
  and the old "revealable guide"/no-http Introduction assertions are
  superseded by this WP's own explicit requirements -- replaced with tests
  for the new Introduction content, the new Syllabus content/schedule/
  tentative-marking/no-invented-facts, and the new Resources/References
  content and `_toc.yml` order.
- `tests/test_wp25_content_audit.py`: removed
  `SyllabusPageUnchangedTests`, a one-time WP25-era guard proving the
  syllabus page was *not* touched during that restructure -- superseded
  now that this WP deliberately populates it. (The file's other,
  unrelated WP25 checks are untouched.)
- `interactive/e2e-book/exercise-06-lite.spec.ts`: updated the
  high-resolution-image test's thresholds/portrait check to the new
  figure; added a new 390px-specific test exercising the diagram's own
  rendered box at that width (not merely page-level no-overflow).

## Bugs found and fixed during this WP

1. **My own first-draft docstring for the fixed `format_tree_diagram()`
   literally contained the text `zip(order, artists)`** (explaining the
   bug it fixes) -- which broke my own new
   `assertNotIn("zip(order, artists)", self.code)` structural test, since
   that docstring ships as real notebook cell source. Reworded to describe
   the mechanism without the literal expression; caught by running the
   test, not assumed fixed.
2. **An overly broad `assertNotIn("squared_error", self.code)`** matched
   `mean_squared_error(` (legitimate, unrelated code elsewhere in the same
   notebook) -- narrowed to the actual `plot_tree`-default-label substring
   `"squared_error = "`.
3. **The new Exercise 6 390px test copied the desktop test's
   `await expect(page.locator("text=Python (Pyodide)")).toBeVisible(...)`
   wait**, which times out live at 390px: that toolbar kernel-status label
   is hidden by responsive CSS at narrow widths (an existing,
   unrelated characteristic of the platform, not a defect introduced by
   this WP -- confirmed by checking `exercise-09-lite.spec.ts`'s own
   already-passing 390px test, which never waits on that label and instead
   uses a fixed settle delay before driving the menu-based "Run All
   Cells"). Fixed to match that already-proven pattern.
4. **The same test's `naturalWidth`/`naturalHeight >= 1400` thresholds**
   were computed from raw `figsize x dpi` canvas arithmetic, not the
   actual saved raster -- JupyterLite's inline Matplotlib backend saves
   with a tight bounding box, cropping the figure's own empty margin.
   Measured the real value live (`naturalWidth=1250`, `naturalHeight=1311`)
   and set thresholds with headroom below that measurement instead.
5. **My Resources page's three relative `.csv` links
   (`[text](lite/files/data/....csv)`) were silently converted by Sphinx's
   MyST parser into `_downloads/<hash>/....csv` copy-and-serve links**,
   not the real same-origin `lite/files/data/...` route the exercises
   themselves use -- caught by inspecting the actual built HTML, not
   assumed from the Markdown source. Switched those three links to raw
   inline HTML `<a href="...">` tags, which Sphinx does not intercept;
   confirmed the rebuilt HTML links to the real route and the files exist
   there byte-identical to source.

None of (1)-(2) reached a published notebook (caught by the test suite
before any commit); (3)-(4) were caught by running the actual new tests
live, not assumed correct from the pattern of an existing, different-width
test; (5) was caught by inspecting the actual built HTML output, not the
Markdown source.

## Verification

### Local, offline (Python)

```
.venv/bin/python -m unittest discover -s tests
```
Two full runs during this WP (both detached via `nohup`/`disown` so they
survived the session interruptions below): the first found the one real
pre-existing stale assertion (`test_wp25_content_audit.py`'s
`SyllabusPageUnchangedTests`, described above) -- **1202 tests, 1317.9s
(~22m), 1 failure (that one, now fixed), 11 skipped**; the second, after
the fix, is the clean final run -- **1201 tests, 1375.0s (~22.9m), 0
failures, 11 skipped (pre-existing, unrelated)**.

### Local, browser (real headless Chromium against the actual combined build)

```
rm -rf book/_build
.venv/bin/jupyter-book build book
.venv/bin/jupyter lite build --config book/lite/jupyter_lite_config.json \
  --lite-dir book/lite --output-dir book/_build/html/lite
cd interactive && npm run test:e2e:book
```
Jupyter Book build: succeeded, 2 pre-existing warnings (missing
`logo.png`, `README.md` not in any toctree) -- both present before this WP,
neither new. First combined-suite run: **123/124 passed, 30.1m** -- the
one failure was `exercise-02-lite.spec.ts`'s own, unrelated slider test
(`.widget-slider .noUi-handle` not visible within 5s), which this WP never
touched; re-ran in isolation (1 worker, no resource contention from the
other 123 tests running in parallel) and it **passed cleanly in 28.8s**,
confirming a transient flake under load, not a regression. The two
Exercise 6 test fixes (bugs 3-4 above) were applied and verified
individually before a final, complete confirmation run: **124/124 passed,
30.1m** (one more test than WP53's baseline 123, exactly the new permanent
390px-diagram test this WP added).

### Real GitHub Actions CI run

`scripts/classify_release_change.py` on the actual pushed commit:
```
GATE: full
reason: shared/unknown path(s) changed: book/_toc.yml (shared: book table
  of contents); book/intro.md (shared: book hub page); book/references.md
  (unknown: no recognized classification rule matches this path);
  book/resources.md (unknown: no recognized classification rule matches
  this path); book/syllabus.md (shared: book hub page);
  tests/test_book_structure.py (shared: shared Python test);
  tests/test_wp25_content_audit.py (shared: shared Python test)
affected exercise IDs: [5, 6, 9]
```
Not overridden or second-guessed, exactly as WP54 itself anticipated
("Shared book navigation/intro/syllabus/assets may legitimately choose
`full`; honor its result").

Pushed: `git push origin main` (fast-forward, `5cfa89c` -> `df390e6`).

GitHub Actions run
[`38245266571`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/38245266571)
("Build and deploy Jupyter Book"): **success**. `classify` job 7s;
`build-and-deploy` job **1h36m44s**. Every step succeeded:

| Step | Result |
|---|---|
| Check every migrated exercise generator is not stale (offline, full gate) | passed |
| Unit-test the Python scripts (offline, full gate) | **1201 tests, 1229.4s (~20.5m), OK, 11 skipped** -- same counts as the local run |
| Check the portable notebook is not stale (offline, full gate) | passed |
| End-to-end test the standalone widget app | **299 passed, 1.2m** (unaffected by this WP) |
| Build Jupyter Book / Build JupyterLite (Exercises 1-9) | passed |
| End-to-end test the combined book + JupyterLite build (full gate) | **124 passed, 1.2h** -- identical count to the local final run |
| Execute the portable notebook outside the repository (Exercises 1-9 only, full gate) | passed |
| Publish website | succeeded |

### Live-site verification (after the deploy, by direct HTTP check against the real published site)

- `gh-pages` branch HEAD commit message: `deploy: df390e637e3e0144ced9b5aed3131f392d35b4f0`
  -- matches the pushed `main` SHA exactly.
- All of `intro.html`, `syllabus.html`, `contents.html`, `resources.html`,
  `references.html`, `chapters/chapter_0{1,5,6,9}/exercise_0{1,5,6,9}.html`,
  both Exercise 6/9 JupyterLite notebook routes, both raw `exercise_0{6,9}.ipynb`
  files, and the same-origin `lite/files/data/abide_age_brain.csv` return
  HTTP 200.
- `chapters/chapter_1{0,1,2}/exercise_1{0,1,2}.html` all return HTTP
  **404** (Exercises 10-12 remain unpublished, and the Syllabus page says
  so explicitly).
- The live sidebar navigation (parsed directly from the built
  `intro.html`) lists, in order: Introduction, Syllabus, Contents,
  Exercises 1-9, **Resources**, **References** -- exactly the order WP54
  required.
- The live `exercise_06.ipynb` and `exercise_09.ipynb` (downloaded
  directly from the published site, not the local build) contain every
  specific fix: Exercise 6 has no `plot_tree(`, no `zip(order, artists)`,
  and does use `ct.children_left`/`ct.n_node_samples`/`draw_panel(...)`;
  Exercise 9's `PC2 (fixed)`/`PLS direction` annotations use the new fixed
  `(0.98, 0.09)`/`(0.98, 0.025)` `axes fraction` anchors and no longer use
  `1.2 * pls_dir`.
- The live `syllabus.html` contains the course number, both staff emails
  (HTML-entity-encoded as `&#64;` by Sphinx's own anti-spam obfuscation --
  confirmed this renders as a normal `@` in the browser, not a defect),
  "Oral tests", "tentative", and the "Only Exercises 1-9 are published"
  guard sentence.
- The live `resources.html` links to the real same-origin
  `lite/files/data/abide_age_brain.csv` route (not a Sphinx
  `_downloads/<hash>/...` copy -- bug 5 above), the ABIDE II legend PDF,
  and `statlearning.com`.
- The live `references.html` leads with the course book citation and
  contains all three required DOIs.

All of this is live-HTTP evidence against the actual published site, not a
repeat of the local/CI browser-automation checks above.

## Process note: background-task survival across session interruptions

This WP's long-running commands (the two full offline-suite runs, the
Jupyter Book/JupyterLite builds, both combined Playwright runs, and the CI
watch) were repeatedly interrupted mid-run by unrelated session restarts
that killed the harness's own background-task tracking (and, in the first
two attempts, the underlying process itself). Switched to launching each
long command via `nohup ... < /dev/null & disown` (fully detaching it from
the harness's process tree, reparented to PID 1) and separately polling
for process exit; this survived every later interruption without losing
any in-progress run, and every long command's actual result was read back
from its own log file rather than from the harness's own (unreliable, in
this session) completion notification.

## Final git state

- `main` (local and `origin/main`, in sync): `df390e6`.
- `gh-pages`: `ba64ce2`, marker `deploy: df390e6...`.
- Checkpoint branch `checkpoint/wp54-pre-work` left in place at the
  pre-WP54 tip (`5cfa89c`) for reference.
- This report and the changelog are added in a separate, `WPs/**`-only
  closing commit (`paths-ignore` keeps it from triggering another deploy).
