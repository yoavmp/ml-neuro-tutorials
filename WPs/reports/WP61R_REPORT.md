# WP61R report: Exercise 11 author-requested revisions (local only)

## Success or failure -- read this first

**Success, local-only, continuing `feature/wp61-embeddings-and-rsa`.** All
15 numbered author corrections are applied, verified offline and in a real
browser, with no regressions found in Exercises 8/9 (the only other
notebooks touched, by item 14's search). The Haxby data manifest's license
is corrected to CC BY-SA 3.0 (verified against the dataset's own
distribution page), with no change to the extraction method or any
measured value. **Not merged, pushed, published, or deployed.**

One real bug was found and fixed along the way that wasn't on the
numbered list: once `neural_rdm` is actually filled in (not just left at
its untouched zero state), sklearn's `MDS` in the real Pyodide browser
kernel emits **two more** `FutureWarning`s beyond the `n_init` one the
author's screenshot showed (`init`'s default changing, and `dissimilarity`
being renamed to `metric`) -- these had been silently hidden by a blanket
`warnings.filterwarnings` WP61 added, which this WP61R removed per item 9's
explicit instruction. Rather than reinstate that suppression, both were
fixed the same way as `n_init`: explicit parameters (`init="random"`,
`metric="precomputed"` in place of the deprecated `dissimilarity=`).
Confirmed via a live Playwright run of the teacher-completed path (where
`MDS` actually executes) that all three warnings are now gone, not just
hidden.

## Branch and SHAs

- Branch: `feature/wp61-embeddings-and-rsa` (continued from WP61; no new
  branch, as instructed).
- Checkpoint: `71a114d` ("checkpoint: before WP61R"), tag `wp61r-start`.
- Implementation: `3e2f6c6` ("WP61R: author-requested revisions to
  Exercise 11, plus corrected Haxby license").
- This report + exact changelog: committed separately after this file.

## Change report, keyed to the numbered author corrections

1. **Overview wording.** "run x category x voxel response patterns" (the
   "ventral-temporal-" qualifier dropped). Verified absent anywhere in the
   notebook's markdown.
2. **Circularity sentence removed**; the VT-mask description now reads
   "a region broadly involved in visual object recognition" and stops
   there -- concise, as asked.
3. **Raw-scan paragraph replaced** with: "We load a small, already-prepared
   part of the dataset: for each of 12 scanning runs and each of 8
   categories, one response pattern across the retained VT voxels -- that
   category's recorded activity, averaged across its retained time points
   within the run," followed by the manifest link (see item 4).
4. **Manifest accessibility, per the mid-task correction.** A direct
   clickable link now appears both in the notebook (Section 1) and on
   `book/resources.md`, with no "find it in JupyterLite's data folder"
   text anywhere. Getting the notebook's own link right took one real
   iteration: a first attempt (`../files/data/...`, reasoned from the raw
   page URL) resolved, live, to a **404** at
   `.../lite/files/files/data/haxby_rsa_patterns.manifest.json` --
   JupyterLab rewrites a rendered markdown link's relative path against
   the notebook's position in its own **contents tree** (not the page's
   literal URL) and then re-wraps it through its own `/files/` serving
   prefix, so a relative path that already included `files/` got
   doubled. Fixed by linking `data/haxby_rsa_patterns.manifest.json`
   (contents-tree-relative, no `files/` prefix); re-verified live --
   resolves to `http://localhost:4174/lite/files/data/haxby_rsa_patterns.manifest.json`,
   **200**, JSON body confirmed to contain the corrected license text.
   `book/resources.md`'s link (`lite/files/data/haxby_rsa_patterns.manifest.json`,
   the established ABIDE-precedent form, page-root-relative) verified
   **200** directly. Both the Haxby source
   (`https://www.pymvpa.org/datadb/haxby2001.html`) and the course's own
   manifest are now on `book/resources.md`; the Haxby citation (entry 5)
   is on `book/references.md`. Nothing is described as already public --
   this whole branch remains local-only and unmerged.
5. **Heatmap intro**: "Here we can see a heatmap of all 8 categories'
   patterns from a single run (run 0)... No obvious structure is visible
   by eye -- the rest of this notebook finds it systematically instead,"
   two sentences shorter than the original.
6. **Thin black row boundaries** (`ax.axhline(i - 0.5, ...)`, linewidth
   0.6) between the heatmap's 8 category rows -- rendered and visually
   confirmed (saved PNG inspected): clean separators, data and labels
   both still fully legible.
7. **"Example format (not a real result):"** now used in both remaining
   blanks (RDM, animacy); "Example shape only" no longer appears anywhere
   in the notebook.
8. **`show_question("q-row-voxel")` moved** to immediately after the run-0
   heatmap (new cell `wp61-106-q-row-voxel`), before `CATEGORY_PATTERNS`
   is introduced in Section 2 -- order verified by cell-id position, not
   just visual inspection.
9. **Every `MDS(...)` call** (the given Section 3 scatter and the
   Section-5 distance-metric activity, both occurrences) now sets
   `n_init=4`, `init="random"`, and `metric="precomputed"` explicitly --
   root-cause fixes, not suppression. The two `warnings.filterwarnings`
   calls WP61 had added for the `dissimilarity`/`init` messages are
   removed outright (there is nothing left for them to catch). Verified
   with zero `FutureWarning`s in: the offline reference-execution run
   (local sklearn 1.9.0), and a real-browser Playwright run of both the
   untouched template (where `MDS` never actually executes) and, more
   importantly, the teacher-completed path (where it does, in Pyodide's
   own sklearn, python3.14 build) -- this second check is what caught the
   two extra warnings in the first place.
10. **Given MDS scatter cell** now carries the same
    `not np.allclose(neural_rdm, 0.0)` guard the check cell and the given
    face-hypothesis example already had, printing "Not complete yet:
    finish Section 2's neural_rdm task first" on an untouched blank
    instead of plotting all 8 categories collapsed onto one point.
11. **"This is a prompt for the written-answer cell below" removed** from
    the MDS reflection paragraph.
12. **Split-Half Reliability section removed in full**: its header, both
    markdown cells, the odd/even-pattern given code, the blank, the check
    cell, and `show_question("q-split-half")`, plus the separate
    `show_question("q-condition-order")` cell -- both corresponding
    `_QUESTIONS` entries deleted from the hidden setup cell. The overview
    numbered list, every `## N.` section heading, and every internal
    "Section 5"/"Section 6" cross-reference were renumbered consistently
    (model comparison is now Section 4, interpretation Section 5); cell
    ids were renumbered to match (`wp61-5xx`→`wp61-4xx`,
    `wp61-6xx`→`wp61-5xx`). The short category-order note ("two RDMs can
    only be compared cell-by-cell if both list categories in the same
    order") stays in Section 2, now with no quiz attached. Confirmed via
    a dedicated test (`test_split_half_section_is_fully_removed`) that no
    trace of `split_half_r`/`odd_rdm`/`even_rdm`/`ODD_CATEGORY_PATTERNS`/
    `EVEN_CATEGORY_PATTERNS`/"Split-Half" remains in code or markdown, and
    via the reference-execution test that none of those names exist in
    the executed namespace.
13. **Trimmed**: the Section 2 RDM-definition paragraph, the Section 4
    model-RDM paragraph, and the Section 5 summary bullets (down from
    three bullets to two once the split-half bullet was removed, plus a
    shortened p-value paragraph) -- meaning preserved throughout
    (confirmed by the unchanged measured numbers and the full green test
    suite, which exercises every one of these concepts).
14. **"Hidden question keys are not secure" paragraph removed** from
    Exercise 11's closing cell. Searched every other generator
    (`grep -rn "secure answer protection\|technically curious student can
    always recover"`) and found the same **student-facing** paragraph
    (inside an actual markdown cell, not a maintainer comment) in exactly
    two others: `generate_exercise_08_notebook.py` and
    `generate_exercise_09_notebook.py`; removed it from both, changing
    nothing else in either cell. (Exercises 01-03/05-07 carry only a
    differently-worded **Python source comment** above their own
    `_QUESTIONS = {` dict -- never rendered to a student -- correctly left
    untouched, since item 14 asked for the student-facing text
    specifically.) Diffs confirmed minimal: 6-8 line deletions per file,
    nothing else changed (`git diff --stat`).
15. **Both widgets confirmed working**: the grouping `SelectMultiple` and
    the distance-metric `Dropdown`, live in a real browser, both before
    and after the relevant blank is filled. The distance-metric activity
    is confirmed to redraw **both** plots (heatmap + MDS scatter) on
    **both** dropdown options (correlation and Euclidean), with zero MDS
    warning text in either cell's rendered output, in the actual
    teacher-completed-path Playwright run.

## License correction (outside the numbered list, as instructed)

Verified directly: PyMVPA's own dataset page
(`https://www.pymvpa.org/datadb/haxby2001.html`) states "The original
authors of Haxby et al. (2001) hold the copyright of this dataset and
made it available under the terms of the Creative Commons
Attribution-Share Alike 3.0 license." `scripts/export_haxby_rsa_data.py`'s
`DATASET_LICENSE` constant is corrected from the earlier "unknown"
statement (which had been based only on `nilearn`'s own dataset
description -- a different, non-authoritative source that doesn't itself
state a license) to CC BY-SA 3.0, with the distributor's exact quoted
statement, a note on what was wrong before and why, and an explicit
share-alike note: since CC BY-SA 3.0 requires derivative works to carry
the same license, this course's own derived export is now stated to be
itself CC BY-SA 3.0 with the same attribution requirement.

**The already-committed `book/lite/files/data/haxby_rsa_patterns.manifest.json`
was hand-aligned to the corrected constant** rather than regenerated via
`--refresh` (which would re-download the ~300 MB raw archive for a
text-only change) -- confirmed the CSV's own sha256 is byte-identical
before and after, and `--check` passes. The extraction method and every
measured value (RDM distances, `face_match_r`, `animacy_match_r`) are
unchanged, as instructed.

## Verification

### Offline (all green, each well under a minute)

```
.venv/bin/python scripts/generate_exercise_11_notebook.py --check          # OK
.venv/bin/python scripts/generate_exercise_08_notebook.py --check          # OK
.venv/bin/python scripts/generate_exercise_09_notebook.py --check          # OK
.venv/bin/python scripts/export_haxby_rsa_data.py --check                  # OK
.venv/bin/python -m unittest discover -s tests -p 'test_exercise_11_lite_notebook.py'        # 46 tests, OK
.venv/bin/python -m unittest discover -s tests -p 'test_exercise_11_reference_execution.py'  # 9 tests, OK (incl. zero-FutureWarning check)
.venv/bin/python -m unittest discover -s tests -p 'test_export_haxby_rsa_data.py'            # 10 tests, OK
.venv/bin/python -m unittest discover -s tests -p 'test_exercise_08_lite_notebook.py'        # 32 tests, OK
.venv/bin/python -m unittest discover -s tests -p 'test_exercise_08_reference_execution.py'  # 15 tests, OK
.venv/bin/python -m unittest discover -s tests -p 'test_exercise_09_lite_notebook.py'        # 49 tests, OK
.venv/bin/python -m unittest discover -s tests -p 'test_exercise_09_reference_execution.py'  # 22 tests, OK
.venv/bin/python -m unittest tests.test_book_structure                                       # 17 tests, OK (resources/references extended)
.venv/bin/python -m unittest tests.test_placeholder_exercises                                # 6 tests, OK
```

Exercises 1-3/5-7/10/12's own test suites were **not** run -- confirmed by
the item-14 search that none of them carry the student-facing paragraph,
and nothing else in this WP touches them.

Diffs for Exercises 8/9's four regenerated files each confirmed minimal
via `git diff --stat`/content inspection: exactly the one paragraph
removed, nothing else.

### Local build + real browser (Chromium, Playwright)

```
rm -rf book/_build
.venv/bin/jupyter-book build book                                      # ~5.3-5.4s (three runs during this WP)
.venv/bin/jupyter lite build --config book/lite/jupyter_lite_config.json \
  --lite-dir book/lite --output-dir book/_build/html/lite               # ~6.3-6.7s (three runs)
```

`interactive/e2e-book/exercise-11-lite.spec.ts` was substantially rewritten
for the removed split-half section, renumbered cell anchors, and new
no-MDS-warning assertions; run four times total across this WP as each
real issue was found and fixed:

1. First run (before the `metric=`/`init=` fix): 3/4 passed; the
   teacher-completed-path test caught the two extra `FutureWarning`s
   described above.
2. After the fix: **4/4 passed** (~1.1 minutes total), including the
   explicit no-MDS-warning assertions in both the untouched-template and
   teacher-completed-path tests, both MDS cells, both distance-metric
   dropdown options.

A separate, throwaway spec (written, run twice to find and confirm the
`data/...` link fix, then deleted -- never committed) verified the
in-notebook manifest link's live resolved `href` and its HTTP status
directly against the running local server.

### Local preview

Server already running from this WP's own earlier verification pass
(`node interactive/e2e-book/serve-book.mjs`, PID 50260, log
`/tmp/wp61_logs/serve_book_preview.log`) -- confirmed still serving the
final, rebuilt content (`curl` against `/resources.html` returns the
corrected "CC BY-SA 3.0" text).

<http://localhost:4174/lite/notebooks/index.html?path=exercise_11.ipynb>
<http://localhost:4174/resources.html>
<http://localhost:4174/references.html>

## Timing

No command in this WP ran longer than two minutes. Every Jupyter Book
build: ~5.3-5.4s. Every JupyterLite build: ~6.3-6.7s. Every Playwright run
of the full 4-test Exercise 11 suite: ~41s-1.3min. All offline Python
test suites: each under 15 seconds.

## Unresolved / open items

- The one "Supplied:" phrase the author's item 5 didn't explicitly name
  (Section 2's "Visualize the neural RDM" intro, a different heatmap)
  still reads "Supplied: a heatmap of `neural_rdm`..." -- left as written,
  since item 5 named one specific cell; flagging it here in case
  consistency across both heatmap intros is also wanted.
- `ANIMATE_CATEGORIES`/`SCRAMBLED_CATEGORY` module-level constants in the
  generator (defined, never referenced -- pre-existing from the original
  WP61 build, not touched by any of this WP's 15 items) remain unused
  dead code; out of this WP's scope, noted for a future cleanup pass if
  wanted.
- Real Google Colab verification: still not performed, as before --
  unverified, not assumed.

## Confirmation

Branch `feature/wp61-embeddings-and-rsa` has a clean working tree at
`3e2f6c6` plus this report's own commit. No merge, push, deployment, or
further WP performed. Stopping for the author's review.
