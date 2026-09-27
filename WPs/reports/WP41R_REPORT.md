# WP41R report: repair Exercise 2 local-review blockers

## Success or failure

**Success.** All three blockers the course author observed in the actual
local combined build were reproduced live in a real headless browser first
(not assumed from reading source), root-caused, fixed, and re-verified live
after the fix. Nothing was merged, pushed, or deployed.

## Branches and SHAs

- Branch: `feature/wp41-jupyterlite-course-platform` (unchanged; no new
  branch created, per WP41R's authority).
- Starting SHA (this WP's entry point): `b0d75dfe4a01cb9c3eaf8bcf8f608d119363ebc2`
  ("WP41: reports — execution report and exact changelog").
- Local checkpoint: branch `checkpoint/wp41r-pre-correction` at the starting
  SHA, created before any edits (section 1's "local checkpoint... for the
  pre-correction state").
- Commits made by this WP, in order:
  1. `e97501a` — WP41R: add local-review blockers spec and chat handoff notes.
  2. `01a105f` — WP41R: fix Exercise 2 setup/NameError, reference-image size,
     and entry points.
  3. This report + the exact changelog (committed together as this WP's
     closing commit; see `git log -1` after that commit for the final SHA).
- No merge, no push, no deployment, no GitHub Actions interaction at any
  point.

## Pre-existing state check (section 1)

`git status --short --branch` at the start showed only two untracked files
(`WPs/ML_NEURO_TUTORIALS_CHAT_HANDOFF_2026-09-27.md`,
`WPs/WP41R_LOCAL_REVIEW_BLOCKERS.md` — the instruction file itself and a
cross-session handoff note the user had placed in the repository). No
unexplained modifications to tracked files. Both were committed as this
WP's first commit rather than reset or ignored.

## Diagnosis method (section 1)

Rather than reasoning from source alone, every blocker was reproduced with a
real Chromium browser (Playwright, headless) against the actual combined
build (`jupyter-book build book` then `jupyter lite build --config
book/lite/jupyter_lite_config.json --lite-dir book/lite --output-dir
book/_build/html/lite`, served locally), matching the student path
Contents -> Exercise 2 -> JupyterLite -> run cells. Each fix was then
re-verified the same way, live, after rebuilding.

## Blocker 1 — `NameError: load_abide_age_brain_table`

**Reproduction.** The repository's own `exercise-02-lite.spec.ts` uses the
notebook toolbar's "Run All Cells", which queues every cell's execution
through the kernel strictly in source order — including the collapsed setup
cell — so it never hit the bug and all 6 of its tests passed both before and
after this fix. The actual failure mode is different: in a fresh kernel, the
setup cell (`wp41-000-setup`) is collapsed (`jupyter.source_hidden`) *and*
was, before this fix, the very first thing in the notebook with no
explanatory text anywhere above it. A reviewer or student who scrolls to a
visible cell and runs just that one — the natural way to spot-check a
specific result, and exactly how the course author described finding this —
never executes it. Reproduced directly: opened the notebook fresh, scrolled
to the `data = load_abide_age_brain_table()` cell, ran only that cell, and
got the exact reported traceback (`NameError: name
'load_abide_age_brain_table' is not defined`).

**Root cause.** Missing first-run guidance plus a collapsed, unlabeled first
cell, not an import or packaging problem. An initial hypothesis — that
`book/lite/overrides.json` listing `"ipywidgets"` in
`loadPyodideOptions.packages` (a list otherwise reserved for packages with
prebuilt Pyodide wheels; the setup cell's own comment says ipywidgets has
none) could make the later `await micropip.install(["ipywidgets"])` call
raise and abort the cell before reaching the function definition — was
investigated and ruled out: across every browser run in this WP (`Run All
Cells`, isolated single-cell runs, before and after every other change),
the setup cell completed successfully every time with no ipywidgets-related
error anywhere in the console or cell output. `overrides.json` was left
unchanged.

**Fix.**
- Added an always-visible Markdown cell immediately before the collapsed
  setup cell: "**Run the cell below first.** ... it still has to run once,
  before anything else in this notebook, or later cells will fail with
  `NameError`." (never collapsed, so it cannot be missed the way the setup
  cell itself can be).
- Wrapped `data = load_abide_age_brain_table()` in `try/except NameError`,
  re-raising as `RuntimeError` with a specific, actionable instruction
  ("Run this notebook's first code cell (collapsed, at the very top,
  under 'Run the cell below first') before this one, then run this cell
  again."). This is a real failure with a clear message, not a swallowed
  exception or a fabricated fallback `data` — Python's own exception
  chaining (`raise ... from exc`) still shows the original `NameError` as
  the chain's stated cause, but the notebook's own, final, highlighted
  error is the actionable `RuntimeError`.
- Confirmed the 5 "YOUR CODE HERE" activities and the notebook's other
  independent-section safety net (`wp41-506-check`, already present before
  this WP, guarding Section 5's KNN blank) are unaffected: neither depends
  on the setup/data-load fix, and no other given-code cell in the notebook
  references a variable that only a still-blank student activity would
  define — verified by grep across the whole generator, not assumed.

**Verification.** Live browser: opened fresh, ran only the data cell without
setup -> got the actionable `RuntimeError`, not a bare `NameError`. Live
browser: "Run All Cells" from a cold kernel -> full run, `held-out R^2 =
0.469` visible, zero error cells (unchanged from before this WP; this path
was never broken). New Playwright test
`running the data cell before setup fails with an actionable message, not a
bare NameError` codifies the reproduction. New offline unittest
`test_data_load_gives_an_actionable_error_if_setup_was_skipped` and
`test_run_first_notice_precedes_the_collapsed_setup_cell` codify the fix
structurally.

## Blocker 2 — Reference image exposes a page-length base64 string

**Reproduction.** Built and served the site, opened the notebook, scrolled
to Section 3B's reference image, entered edit mode: the visible Markdown
source was the entire `![...](data:image/png;base64,<~54,000 characters on
one line>)`.

**Root cause.** The generator inlined the PNG as a `data:` URL directly in
the cell's Markdown *source*, which is what a student sees (and has to
scroll past/risk corrupting) on entering or leaving edit mode. This is
distinct from where the bytes live for *rendering* — nbformat has always had
a dedicated place for that, cell **attachments**, which this notebook did
not use.

**Fix.** Replaced the inline `data:` URL with a standard nbformat cell
attachment: the cell's Markdown source is now
`![Approved observed-vs-predicted result](attachment:exercise_02_observed_vs_predicted.png)`
(90 characters), and the actual PNG bytes live in the cell's
`attachments` field, resolved by the renderer at display time. This is
core nbformat behavior, not a JupyterLite-only trick, so it renders
identically in every environment the notebook targets.

**Verification.**
- **JupyterLite** (live browser): image renders (`<img>` with a resolved
  `data:image/png;base64,...` src, confirming the renderer substitutes it
  at display time); double-clicking into the cell shows exactly the
  90-character source above, nothing longer; `Shift+Enter` returns it to
  rendered mode with the image intact. New Playwright test *"the reference
  image returns to rendered mode without a page-length encoded string"*
  codifies this exact round trip.
- **Local Jupyter** (via `nbconvert.HTMLExporter`, the same rendering stack
  `jupyter nbconvert`/classic Jupyter use): rendered the portable notebook
  to HTML and confirmed the attachment resolves to an embedded `<img
  src="data:image/png;base64,...">` with zero unresolved `attachment:`
  references in the output.
- **Colab**: not independently testable from this environment (no network
  access to colab.research.google.com). Colab's own markdown-image-paste
  feature is implemented via this same standard nbformat `attachments`
  mechanism, so this is expected to render there unchanged; flagging this
  as the one leg of blocker 2 not verified first-hand, per the "where
  practical" qualifier in the WP.
- One expected, harmless side effect: the browser makes one failed network
  request for the literal string `attachment:<filename>` (not a real URL
  scheme) before JupyterLab's attachment resolver replaces the `<img> src`
  — this is how nbformat attachments render in any Jupyter frontend
  implementing the convention, occurs once, and does not affect the final
  rendered image (confirmed above). Documented in
  `exercise-02-lite.spec.ts` and added to that file's benign-console-noise
  allowlist rather than silently ignored.
- New offline unittest
  `test_reference_image_is_an_attachment_not_an_inline_data_uri` asserts no
  `data:image/png;base64` substring anywhere in the cell source, an
  `attachment:` reference instead, source length under 200 characters, and
  a real attachment payload present.

## Blocker 3 — Every Exercise 2 entry point was broken

**Reproduction.** Built and served the site, opened
`chapters/chapter_02/exercise_02.html` in a live browser and inspected the
actual DOM (not just the generator source):
- "Open Exercise 2" rendered as
  `<a class="reference internal" href="#../../lite/notebooks/index.html?path=exercise_02.ipynb">`
  — clicking it left `page.url()` unchanged except for the appended
  fragment; it never navigated anywhere.
- The download line rendered as
  `<span class="xref myst">../../downloads/chapter_02/exercise_02_portable.ipynb</span>`
  — not an `<a>` element at all, so it was never clickable; this also
  would have 404'd regardless, since `book/downloads/` is excluded from the
  Jupyter Book build and was never copied into `_build/html/`.
- The generic per-page Colab button (`_static/launch-buttons.js`) resolved
  to `https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/blob/main/book/downloads/chapter_02/exercise_02_portable.ipynb`
  — a URL that only ever fetches from the *public* `main` branch on GitHub,
  which still has the pre-WP41 Exercise 2 (this migration is unpushed, per
  WP41's own constraints), so the button opened the old notebook exactly as
  reported.

**Root cause, entry points 1-2.** MyST/Sphinx treats a relative Markdown
link that is not a scheme-qualified external URL (`https://...`) as a
candidate cross-reference to another document in the same Sphinx project.
Since neither `../../lite/notebooks/index.html?path=...` nor
`../../downloads/chapter_02/...` is a real Sphinx document, that resolution
fails — for the first it fell back to a same-page `#...` anchor (a no-op
click), for the second it fell back to unlinked literal text. This is a
Sphinx/MyST-specific behavior that only affects same-site relative links
built with plain Markdown `[text](url)` syntax; it does not affect the
`https://...` absolute URLs the older chapters (1, 3-10) already use for
their own Colab/raw-GitHub links, which is why only Exercise 2's new,
same-origin-style links were affected.

**Root cause, entry point 3 (Colab button).** Structural, not a code bug:
`launch-buttons.js`'s URL pattern (`github.com/<repo>/blob/<branch>/<path>`)
can only ever reflect the *public, pushed* state of the named branch. Per
WP41R section 4's own framing, this route cannot "demonstrably work for a
local build" (Colab cannot reach an uncommitted/unpushed local file at all)
"and the future public/private-repository arrangement" (the same URL
pattern stops working entirely once the repository goes private, for every
chapter, not just this one).

**Fix.**
- `scripts/generate_exercise_02_transition_page.py`: both links now use raw
  inline HTML (`<a href="...">...</a>`) inside the Markdown cell.
  CommonMark/MyST pass raw inline HTML through untouched, so it is never
  misread as a cross-reference and renders as an ordinary working `<a>` tag
  — confirmed in the rebuilt HTML (`<a
  href="../../lite/notebooks/index.html?path=exercise_02.ipynb">Open
  Exercise 2</a>` and `<a
  href="../../lite/files/exercise_02_portable.ipynb">download the same
  notebook</a>`).
- The download target changed from `../../downloads/chapter_02/...` (never
  published) to `../../lite/files/exercise_02_portable.ipynb`. The portable
  notebook's exact, byte-identical content is now also written to
  `book/lite/files/exercise_02_portable.ipynb` by
  `generate_exercise_02_notebook.py` (a third, deliberately identical copy
  of the same generated content — the canonical committed copy stays
  `book/downloads/chapter_02/exercise_02_portable.ipynb`, consistent with
  every other chapter). `jupyter lite build` already copies
  `book/lite/files/` verbatim into `_build/html/lite/files/`, so this file
  is published same-origin with zero Sphinx build-config risk to any other
  page, and works regardless of the repository's future visibility, same as
  the JupyterLite app's own data files already do.
- The inline "Google Colab" reference in the transition page's own body
  text was also changed, for the same reason: it previously deep-linked
  `colab.research.google.com/github/.../main/...` (the same
  private-repo-unsafe pattern as the suppressed button); it now links to
  plain `https://colab.research.google.com/` with instructions to use
  **File > Upload notebook** after downloading — accurate regardless of
  repository visibility or push state, and satisfies the WP's "otherwise
  suppress it... and provide a clear Download notebook for Colab link with
  concise upload instructions" branch.
- `book/_static/launch-buttons.js`: removed the
  `"chapters/chapter_02/exercise_02.html"` entry from `PAGE_TO_PORTABLE`, so
  the top-bar Colab button no longer appears on this page at all (unmapped
  pages already got no button, by design — this uses that existing
  mechanism rather than adding new logic). Chapters 1 and 3-10 are
  unaffected.
- Checked the theme's own separate "download source" dropdown (unrelated to
  `launch-buttons.js`): it correctly points at
  `_sources/chapters/chapter_02/exercise_02.ipynb` — the current transition
  page's own source, not stale content. No fix needed there.

**Verification.** Live browser, rebuilt combined site: clicking "Open
Exercise 2" now navigates `page.url()` to the actual JupyterLite notebook
URL; `GET .../lite/files/exercise_02_portable.ipynb` returns `200`; the
download link is a real, visible `<a>`; `[data-testid="colab-launch-button"]`
count is `0` on this page; `.bd-article` innerHTML contains neither
`raw.githubusercontent.com` nor `colab.research.google.com/github` anywhere
on this page. Rewrote `interactive/e2e-book/chapter02.spec.ts` to assert
exact hrefs and an actual click-through navigation (see "why the old tests
did not catch this," below) and added a dedicated Colab-button-absent case
to `interactive/e2e-book/launch-buttons.spec.ts`; removed Chapter 2 from
that file's shared admonition-based assertion loop, since Exercise 2 no
longer uses that page structure. New offline unittest
`test_no_raw_github_or_colab_deep_link` and a stricter
`test_links_to_the_jupyterlite_notebook` /
`test_links_to_the_downloadable_copy` (asserting the exact `<a href="...">`
form, not a URL substring) in `tests/test_exercise_02_transition_page.py`.

## Why the existing regression tests did not catch any of this

Concrete, checked evidence, not a general claim: on the *pre-fix* build,
`interactive/e2e-book/chapter02.spec.ts`'s two tests both passed. Test 1
used `a[href*="lite/notebooks/index.html?path=exercise_02.ipynb"]`
(substring-of-href) — this matched the broken `href="#../../lite/..."`
too, since the broken href still *contains* that substring after the
leading `#`. Test 2 used
`a[href*="downloads/chapter_02/exercise_02_portable.ipynb"]` — the actual
download element was an unlinked `<span>`, not an `<a>`, so this locator
should have matched nothing; it passed anyway because the *Colab button*'s
href also contains that same substring, so the test was unknowingly
asserting on the wrong element. Both rewritten tests now assert the exact
`href` attribute and, for the JupyterLite link, an actual click-driven
navigation. `exercise-02-lite.spec.ts`'s existing 6 tests all used "Run All
Cells", which queues the setup cell first by construction and so never
exercised the skip-setup path; a new test exercises that path directly.
This matches the WP's instruction that "structural checks alone are
insufficient."

## Numerical integrity (unchanged)

Verified via a real-kernel (`nbclient`) execution of
`scripts/reference_notebooks/exercise_02_reference.ipynb` and the live
browser "Run All Cells" run:

| Quantity | Value |
|---|---|
| Participants | 1004 |
| Brain predictors | 360 |
| Train / test split | 753 / 251 |
| Linear regression, held-out R^2 | 0.469 |
| Linear regression, held-out MSE | 49.55 |
| KNN (k=20), held-out R^2 | 0.664 |
| KNN (k=20), held-out MSE | 31.4 |

All unchanged from before this WP. Section 7/Bonus values (sample-size and
feature-set comparisons) were exercised by the same reference-notebook run
(`tests/test_exercise_02_reference_execution.py`, all 7 cases pass) and are
unaffected — this WP touched none of that code.

## Hub / template / working-copy / storage / download / portable mapping (updated)

Only the routing for Exercise 2's *portable/Colab* copy changed:

- **Template** (unchanged): `book/lite/files/exercise_02.ipynb`, served at
  `<site>/lite/files/exercise_02.ipynb`.
- **Portable/Colab copy**: canonical committed copy remains
  `book/downloads/chapter_02/exercise_02_portable.ipynb` (consistent with
  chapters 1, 3-10); a byte-identical second copy is now also written to
  `book/lite/files/exercise_02_portable.ipynb`, which is what actually gets
  published (`book/downloads/` is not). The transition page links to the
  published copy.
- Everything else (working copy via IndexedDB, autosave status, Download
  button exporting live state, Reset fetching the static template, Back to
  Contents) is unchanged from the original WP41 report and was not touched
  by this WP.

## Local build and test commands used

```
source .venv/bin/activate
jupyter-book build book
jupyter lite build --config book/lite/jupyter_lite_config.json \
  --lite-dir book/lite --output-dir book/_build/html/lite

# offline / structural / numerical-integrity
.venv/bin/python -m unittest discover -s tests            # 1083 tests, OK (11 skipped)

# real-kernel execution
.venv/bin/python -m unittest tests.test_exercise_02_reference_execution -v

# browser (from interactive/)
cd interactive
npx playwright test --config playwright.book.config.ts    # full book e2e suite, 155 passed
npm run typecheck
npm run test:unit                                          # 481 tests, all passed
```

Serve URL used for all browser checks:
`http://localhost:4174/chapters/chapter_02/exercise_02.html` and
`http://localhost:4174/lite/notebooks/index.html?path=exercise_02.ipynb`
(via `interactive/e2e-book/serve-book.mjs`, which also serves everything
under `/ml-neuro-tutorials/...` to exercise the future GitHub Pages project
subpath).

## Test results

- `tests/` (repository-wide, `unittest discover`): **1083 passed**, 11
  skipped, 0 failed.
- `tests/test_exercise_02_reference_execution.py` (real-kernel execution):
  **7/7 passed**; numbers match the table above.
- `interactive` book e2e suite (`playwright.book.config.ts`, full run):
  **155 passed**, 0 failed for anything this WP touched. Two pre-existing
  failures unrelated to this WP were discovered incidentally (see
  Deviations) and left unmodified, per scope.
- `interactive/e2e-book/exercise-02-lite.spec.ts` alone: **8/8 passed**
  (the original 6, plus the 2 new regression tests this WP adds).
- `interactive` typecheck: clean. `interactive` vitest unit suite: **481/481
  passed**.

## Deviations and judgment calls

- **Two pre-existing, unrelated failing tests were discovered while running
  the full book e2e suite** (not part of any bounded gate this WP defined;
  found only because a full-suite pass was run as a courtesy check):
  `iframe-height-contract.spec.ts` and
  `wp22-cross-chapter-dark-mode.spec.ts` each still reference Exercise 2's
  *old* React/iframe KNN-exploration widget
  (`iframe[title="Interactive KNN neighbour-count exploration..."]` /
  `config=../configs/knn_explore.json`), which the original WP41 migration
  already removed from `chapters/chapter_02/exercise_02.html` (confirmed:
  `chapter02.spec.ts` itself asserts `iframe` count is `0` on this page).
  This is pre-existing WP41 test debt, unrelated to any of the three
  blockers in scope for WP41R, and updating/retiring those two test files
  was judged out of scope ("do not migrate another exercise," and these
  tests do not concern Exercise 2's JupyterLite migration or entry points).
  Left unmodified; flagged here for the course author's awareness.
- **`TEMPLATE_VERSION` bumped from 1 to 2** in
  `generate_exercise_02_notebook.py`'s embedded notebook metadata
  (`nb.metadata.wp41.templateVersion`). Purely informational (nothing reads
  it at runtime — "Reset from course template" always fetches whatever is
  currently at `lite/files/<path>`, unconditionally); bumped so the
  metadata itself reflects that this is not the original Gate-A-era
  content.
- **The portable notebook now exists in two on-disk locations with
  identical content** (`book/downloads/chapter_02/...` and
  `book/lite/files/exercise_02_portable.ipynb`), both written by the same
  generator from the same source. Judged preferable to either restructuring
  the canonical path (bigger, riskier change, inconsistent with every other
  chapter) or adding a new Sphinx `html_extra_path` entry (verified via
  Sphinx's own `copy_asset` source that it would have dropped the
  `downloads/` prefix from the served path, requiring either a URL change
  anyway or a symlink workaround — both judged messier than one extra,
  clearly-commented, generator-written file).
- **Colab verification for the reference-image fix is source-based, not
  live-tested** (no network access to colab.research.google.com from this
  environment). Noted explicitly in the Blocker 2 section above rather than
  silently assumed.

## Confirmation

Nothing was merged, pushed, or deployed. No GitHub Actions workflow was
triggered or inspected. `Homework_Materials/` was not touched. No exercise
other than Exercise 2 was migrated or modified (chapters 1, 3-10 verified
unchanged via their own passing `launch-buttons.spec.ts` cases). WP42 was
not started.
