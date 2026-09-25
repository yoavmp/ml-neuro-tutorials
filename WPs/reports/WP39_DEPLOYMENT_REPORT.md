# WP39 — Deployment Execution Report

## 1. Overall result

**SUCCESS.** The WP38/WP38R Exercise 10 course materials were merged into local `main`, pushed to
`origin/main` exactly once, built and published successfully by the existing GitHub Actions
workflow, and fully verified live in production at
`https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_10/exercise_10.html`. No
pre-deployment gate failed, no conflict occurred, and no genuine product/data/test defect was
found. WP40 has not been started.

---

## 2. Starting state (Section 1)

- `fix/wp38r-exercise10-review` tip (read from Git, not inferred from the report):
  `2f801ca84c01a1b084f053ec26e8d5074e8bcd1d`
- Local `main`: `2f74ccae826d14da9dee9997d890697d159d91c0` — matches expectation exactly.
- `origin/main` (after `git fetch origin main`): `f792ad55f34342e627ed1fe3b85ff60777507d85` —
  matches the previously deployed release exactly (not merely an ancestor).
- `origin/main..main` contains exactly the two expected local-only documentation commits: `bf6aaa2`
  (WP37) and `2f74ccae826d14da9dee9997d890697d159d91c0` (WP37V) — the latter *is* local `main`'s
  own tip.
- WP38R branch contains, in order: WP38 checkpoint `06fd62a`, WP38 implementation `61a16c6`, WP38
  report `3b8cdea`, WP38R checkpoint `6c8a3a7`, all documented WP38R implementation commits
  (`7378fed`, `6f2ad57`, `bb37450`, `2349458`+merge `f43b10f`, `2a1abfc`+merge `12ec3bc`, `72141da`,
  `754e1bb`, `b53dad3`, `ec51c43`, `edaad80`, `d204399`), and one final WP38R report commit
  (`2f801ca`) at the tip — all confirmed present via `git log --oneline main..fix/wp38r-exercise10-review`
  and cross-checked against every SHA referenced in `WPs/reports/WP38R_REPORT.md`.
- WP38R working tree: clean except the untracked WP39 specification (not yet committed).
- `book/syllabus.md` and the `course_overview/` Word-document sources: byte-identical between local
  `main` and the WP38R branch tip (`git diff --quiet` on both paths — empty).
- No divergence from any Section 1 expectation was found; validation proceeded.

**WP39 checkpoint** (this specification committed on `fix/wp38r-exercise10-review`):
`16e8291fe8eea049fe125ec128786f7716a0d4b7`
(tree SHA `d33bc5681607f11ae709b507bdc173883c7e95d3`).

---

## 3. Intended release diff (Section 2)

`git diff --stat main 16e8291f...` showed 72 files changed (25,909 insertions, 53 deletions),
containing only: the Exercise 10 canonical/portable notebooks, widget configs/components/data/
tests for the quiz/leakage-lab/HAR-fold-compare/class-balance-compare activities, the UCI HAR
compact data + provenance, the KNN leakage-lab and class-balance audited export artifacts, shared
`activity-resize.js`/`resize-report.ts` fixes and their tests, portable-generator/launch-button
registration for Chapter 10, WP38/WP38R/WP39 documentation, and placeholder/shared-test updates
(`test_book_structure.py`, `test_exercise_04/06/07/08/09_notebook.py`,
`test_placeholder_exercises.py`, `test_wp25_content_audit.py`) whose diffs were individually
inspected and confirmed to be nothing but "10 moves from the placeholder range (10-12) into the
complete range (1-10)" mechanical renumbering — exactly the kind of update WP39 §2 permits.

Explicitly confirmed **not** in the diff: `book/syllabus.md`, `course_overview/*`,
`scripts/build_course_overview_docx.py`, any `book/chapters/chapter_01`–`chapter_09` content file,
any `book/chapters/chapter_11`/`chapter_12` placeholder file, `.github/workflows/*`,
`requirements*.txt`/`pyproject.toml`, and `interactive/package.json`/`package-lock.json` (checked
via a single scoped `git diff --stat` against all of these paths — empty output).

---

## 4. Pre-deployment validation gates (Section 3) — commands, results, durations

All gates run once, in order, using the project's existing `.venv` and installed frontend
dependencies. **All gates passed; no failure, retry, or deviation occurred.**

| # | Gate | Command | Result | Duration |
|---|------|---------|--------|----------|
| 1a | UCI HAR compact-data/provenance | `python scripts/export_uci_har_data.py --check` | OK: valid (rows=10299, participants=30, activities=6) | 0.86s |
| 1b | ABIDE manifest/self-consistency | `python scripts/abide_modeling_data.py --check` | OK: self-consistent | 0.11s |
| 1c–1e | HAR grouped-split / HAR widget-export / leakage-lab / class-balance export checks | covered by the focused-test gate below (§tests reload and re-validate each committed artifact's `--check` invariants) | OK | — |
| 2 | Portable-notebook staleness (all 10 chapters) | `python scripts/build_portable_notebook.py --check --notebook all` | all 10 chapters up to date | 1.72s |
| 3 | Smoke-execute Chapter 10 portable notebook outside the repo | `python scripts/smoke_portable_notebook.py --notebook chapter_10` | OK: executed cleanly (10 code cells, key values matched) | 8.50s |
| 4a | Focused Exercise 10 / exporter / audit / portable-behavior tests | `python -m unittest tests.test_exercise_10_notebook tests.test_export_leakage_lab_data tests.test_export_class_balance_compare_data tests.test_export_har_fold_widget_data tests.test_har_group_leakage_audit tests.test_uci_har_data` | 76/76 passed | 7.19s |
| 4b | Focused portable-notebook / launch / book-structure tests | `python -m unittest tests.test_build_portable_notebook tests.test_book_structure tests.test_placeholder_exercises tests.test_wp25_content_audit` | 52/52 passed | 0.68s |
| 5 | Full offline Python suite | `python -m unittest discover -s tests -p 'test_*.py'` | **1066 tests, 0 failures, 11 skipped** (pre-existing, network-only) | 13.85s |
| 6a | Frontend typecheck | `npm run typecheck` (interactive/) | clean | 4.15s |
| 6b | Frontend full unit-test suite | `npm run test:unit` (interactive/) | **38 files / 481 tests passed** | 4.11s |
| 7 | One frontend production build | `npm run build` (interactive/) | succeeded; one pre-existing >500kB chunk-size warning (unrelated) | 8.08s |
| 8 | Focused standalone Playwright: quiz, leakage-lab, HAR-fold-compare, class-balance-compare, resize-shrink | `npx playwright test e2e/leakage-quiz.spec.ts e2e/leakage-lab.spec.ts e2e/har-fold-compare.spec.ts e2e/class-balance-compare.spec.ts e2e/resize-shrink.spec.ts` | **53/53 passed** | 13.45s |
| 9a | Clean the book build dir | `jupyter-book clean book` | emptied `_build` (except `.jupyter_cache`) | 0.42s |
| 9b | One clean Jupyter Book build | `jupyter-book build book` | succeeded; 2 pre-existing, unrelated warnings (`book/README.md` not in toctree; a `[etoc]` redirect notice) | 6.49s |
| 10 | Focused built-book Playwright: Chapter 10 structure/interactions, launch buttons, iframe-height contract (dark/390px/console embedded) | `npx playwright test --config playwright.book.config.ts e2e-book/chapter10.spec.ts e2e-book/launch-buttons.spec.ts e2e-book/iframe-height-contract.spec.ts` | **62/62 passed** (includes Exercises 1–10 iframe-height contract, dark mode, 390px, and console-error assertions) | 32.46s |
| 11 | Manual local visual check: Exercise 10 at desktop/390px × light/dark | Playwright-driven screenshots of the built book (temporary, never-committed script; server started/stopped for the check only) | Confirmed: quiz question never overlaps first option; all four activities fit their content (no large empty lower region) after allowing full scroll-through settle; no plot/legend/control/feedback clipping; correct/leaky R² and MSE both visible in the leakage lab; all five class balances load with both logistic models simultaneously visible; dark mode correct at both widths | — |

Gate 10 already embeds the dark-mode, 390px, and unexpected-console-error checks called for
separately in §3 item 10 (`iframe-height-contract.spec.ts` drives each activity through a control
change, a reset/"try again" contraction, dark mode, and a 390px viewport, with console/runtime
error recording throughout) — no separate spec run was needed or added.

**One investigated-and-dismissed observation during gate 11:** an initial screenshot pass (fixed
3-second wait, no scroll) appeared to show large blank regions in the lower half of Exercise 10.
Re-measuring with `document.body.scrollHeight` and each iframe's actual rendered height (542px,
1603px, 1590px, 1981px — all real, non-trivial content) after scrolling the full page through in
500px steps to let every Plotly chart finish rendering showed no such gap; a second full-page
screenshot after that settle confirmed all four activities render completely with normal
notebook-prose spacing between sections. This was a screenshot-timing artifact of the manual check
script, not a product defect — confirmed independently by gate 10's automated `iframe-height-
contract.spec.ts`, which passed for all four Exercise 10 iframes using its own settle-detection
logic.

No gate failed. No speculative reruns, `--repeat-each`, sleeps beyond normal settle waits, seed
changes, artifact refreshes, or weakened assertions were used. No notebook re-execution or artifact
refresh occurred outside the listed checks (the smoke-execution in gate 3 runs the notebook
*outside* the repository, per spec, and does not write back into it).

---

## 5. Merge into local `main` (Section 4)

- WP39 checkpoint tree SHA reconfirmed: `d33bc5681607f11ae709b507bdc173883c7e95d3`.
- Working tree clean before merge.
- Switched to `main`; reconfirmed `main` = `2f74ccae826d14da9dee9997d890697d159d91c0` and
  `origin/main` = `f792ad55f34342e627ed1fe3b85ff60777507d85` (fresh `git fetch origin main`) —
  both unchanged from Section 1.
- `git merge --no-ff fix/wp38r-exercise10-review -m "Merge Exercise 10 course materials"` completed
  with **no conflicts** (strategy: `ort`).
- **`RELEASE_SHA` = `58ed1c61f43f0b3c6d23c1f32212bf2d3b9c9f0b`**
- Tree identity proven: `git diff RELEASE_SHA 16e8291f...` and
  `git diff-tree -r RELEASE_SHA 16e8291f...` both produced **empty output**.
- Working tree after merge: clean.

---

## 6. Push (Section 5)

- Preconditions reconfirmed immediately before push: `origin/main` still
  `f792ad55f34342e627ed1fe3b85ff60777507d85` (fresh fetch); `origin/main` confirmed an ancestor of
  `RELEASE_SHA`; working tree clean.
- `git push origin main` succeeded on the first and only attempt: `f792ad5..58ed1c6  main -> main`.
- Read-only verification: `git ls-remote origin main` → `58ed1c61f43f0b3c6d23c1f32212bf2d3b9c9f0b
  refs/heads/main` — confirms `origin/main` = `RELEASE_SHA`.
- Exactly one push was performed. No retry was needed or attempted.

---

## 7. Workflow discovery and monitoring (Section 6)

- Workflow discovery: `gh run list --commit 58ed1c61f43f0b3c6d23c1f32212bf2d3b9c9f0b --limit 5`
  found a matching run on the **first query** (no 30-second wait/second query was needed).
- **Workflow name:** "Build and deploy Jupyter Book"
- **Run ID:** `36027222613`
- **URL:** `https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/36027222613`
- Single foreground watcher started: `gh run watch 36027222613 --exit-status`.
- **Deviation (environmental, documented per WP39 §9's "genuine defect... stop and report" /
  WP37 precedent for tool-boundary interruptions):** the watcher's own process exceeded the tool
  environment's single-call limit and was moved to a background-tracked continuation of the *same*
  watcher (not a second watcher). That background-tracked process was itself later terminated by an
  environment/session boundary (a new session started with the message "done?" and a stopped-task
  notification, unrelated to the WP39-mandated 30-minute cap — the process log showed it was killed
  at ≈10 minutes elapsed, with steps 1–16 already succeeded and step 17 in progress) rather than by
  a deliberate 30-minute interruption. Following the same precedent WP37V established for exactly
  this situation, **one** single read-only status query —
  `gh run view 36027222613 --json status,conclusion,url,jobs,createdAt,updatedAt` — was issued
  (not a second watcher, not a polling loop) to determine the run's actual final state. This is the
  only query beyond the one initial watcher that was made.
- That single query showed the run had already reached `status: completed`, `conclusion: success`
  by the time it was issued.
- **All 20 steps succeeded**, including "Execute the portable notebook outside the repository"
  (completed `2026-09-24T16:43:57Z`) and "Publish website" (completed `2026-09-24T16:44:01Z`).
- **Run duration:** `2026-09-24T16:25:09Z` → `2026-09-24T16:44:04Z` ≈ **18m55s** — consistent with
  the ~18-minute baseline WP37 established for this same workflow, and well within the 30-minute
  cap. No interruption, rerun, or repair was needed.

---

## 8. Production verification (Section 7)

All checks below were run against `https://yoavmp.github.io/ml-neuro-tutorials/` with
cache-busting query strings and fresh browser contexts (Playwright, no persisted state), following
the workflow's confirmed `success` conclusion.

### 8.1 Page and launch behavior

- HTTP 200 at `chapters/chapter_10/exercise_10.html`.
- Title: exactly **"Exercise 10: Examples and Common Mistakes"** (confirmed via `<title>`, which
  also carries the site suffix "— Machine Learning for Neuroscience").
- No placeholder text (asserted by the reused `chapter10.spec.ts` "title and structure" test).
- Chapter 10 appears in the sidebar in the intended order: Introduction, Syllabus, Contents,
  Exercises 1–12 in strict numeric order (extracted directly from the production page's nav and
  confirmed Exercise 10 sits between 9 and 11).
- Colab/download links point to the Chapter 10 portable notebook: the article-header Colab button
  and the opening-admonition Colab+raw links both target
  `.../blob/main/book/downloads/chapter_10/exercise_10_portable.ipynb` (Colab) and
  `raw.githubusercontent.com/.../chapter_10/exercise_10_portable.ipynb` (raw) — confirmed both by
  the reused `launch-buttons.spec.ts` (62/62 passed, all 10 chapters) and directly via `curl`.
- The portable notebook URL returns HTTP 200 — confirmed against its real destination,
  `https://raw.githubusercontent.com/yoavmp/ml-neuro-tutorials/main/book/downloads/chapter_10/exercise_10_portable.ipynb`
  (the portable notebook is intentionally served from the repository, not from the GitHub Pages
  build — `book/downloads/` is outside `book/_build/html`).
- Exercises 1–9 remain reachable: all nine return HTTP 200.
- Exercises 11–12 remain placeholders: titles confirmed exactly
  "Exercise 11: Embeddings and Representational Similarity Analysis" and
  "Exercise 12: Review and Exam-Style Questions"; `launch-buttons.spec.ts` confirms Exercise 11
  gets no Colab button.
- Exercise 13 absent: HTTP 404, as expected.
- Syllabus remains unchanged: HTTP 200, and `book/syllabus.md`'s source is byte-identical to the
  previously deployed release (`git diff` against `f792ad5:book/syllabus.md` — empty).

### 8.2 Required Exercise 10 content

Confirmed present on the live page: the training-data-boundary principle ("The Boundary Around the
Training Data" section heading); the seven-option multiple-selection quiz with exactly six correct
answers (verified directly from the served `leakage_quiz.json` artifact: `len(options)==7`,
`sum(correct)==6`); the KNN leakage laboratory with fixed `k=15` (verified in the rendered page
text); paired correct/leaky R² and MSE (confirmed both by `chapter10.spec.ts`'s leakage-lab
assertion and by direct visual inspection during gate 11, which also captured the pipeline text
"Correct test R2: 0.576 / Leaky test R2: 0.573" for the scaling scenario); the UCI HAR
random-window-versus-participant-grouped activity ("Random Windows or New Participants?");
Fragment 4's explicit UCI HAR/new-participant framing (the "New Participants" heading/prose
appearing multiple times in context); the final debugging checklist ("Final Checklist" heading
present).

Confirmed **absent**: the removed "High Accuracy Can Still Miss the Minority Class"
threshold-comparison activity (zero matches); a stale threshold-slider control (the one "decision
threshold" text match on the page is the *new* class-balance-compare activity's own description —
"Both models below use identical, training-only preprocessing and a fixed decision threshold of
0.5" — not a slider; `chapter10.spec.ts` additionally asserts "no threshold control" directly on
the rendered widget).

### 8.3 Interactive behavior

All four Exercise 10 activities verified against production via the reused
`e2e-book/chapter10.spec.ts` and `e2e-book/iframe-height-contract.spec.ts` (62/62 passed):

1. **Multiple-selection quiz** — iframe/config/data load (HTTP 200), full-pass selection shows
   success, "Try again" reset restores default state (exercised by
   `iframe-height-contract.spec.ts`'s reset step), no overlap between the wrapped question and the
   first option (confirmed both by the reused desktop/intermediate/390px overlap assertions and by
   manual gate-11 screenshots).
2. **KNN leakage laboratory** — iframe/config/data load, both plots render, sample-size/seed/
   scenario controls update metrics, k=15 fixed, correct/leaky R²/MSE both visible, reset restores
   the default operation/sample-size/split.
3. **Random windows vs. new participants (UCI HAR)** — iframe/config/data load, participant grid
   and both plots render, method/k/fold controls update accuracy/macro-F1, reset restores defaults.
4. **Class-balance comparison** — iframe/config/data load, no threshold control present, switching
   among all five balances updates metrics/confusion matrices/chart for both models simultaneously,
   majority-class and PR-AUC baselines update correctly and match the committed artifact, ordinary
   and class-weighted results are shown side by side.

For every activity: no clipping, no large empty lower region, the iframe grows and shrinks with
content, no page-level horizontal overflow at 390px, light mode correct, book-toggle dark mode
correct, and — checked with a small temporary (never-committed) production-only script — reload
while dark gives the correct first paint (`data-theme="dark"` and the dark body background were
already present at navigation commit, before `networkidle`). No unexpected console/runtime errors
were observed in any of these checks; the single console message seen throughout (`SyntaxError:
'THEBE_JS_URL' has already been declared`) is the same pre-existing, unrelated Thebe/theme-bootstrap
noise `iframe-height-contract.spec.ts` already whitelists.

### 8.4 Shared resize regression

`iframe-height-contract.spec.ts` was run against production for **all registered Exercises 1–10
activities** (24 iframes total across 10 chapters), not only Exercise 10 — **24/24 passed**, each
covering: fits-content-after-settle, survives a control change, survives a reset/"try again"
contraction where one exists, and still fits in dark mode at 390px, with both the
clipping/undershoot assertion and the excessive-trailing-space assertion checked on every
measurement.

No model fitting, artifact regeneration, or repository writes occurred during production
verification. The temporary Playwright config used to point the repository's own specs at
production was created only inside a `mktemp -d` directory (with a symlink to
`interactive/node_modules` for module resolution) and was deleted immediately after use, along with
the local static-server process used for the manual visual check and all scratch screenshots —
`git status --short --branch` was clean throughout and confirmed clean afterward.

---

## 9. Deviations, warnings, and unresolved issues

1. The foreground GitHub Actions watcher was interrupted by an environment/session boundary before
   the workflow's conclusion was observed within that same tool call (see §7). This was **not** the
   WP39-mandated 30-minute stop condition (only ≈10 minutes had elapsed and the run itself
   completed in ≈19 minutes) — it was resolved with exactly one additional read-only status query,
   following the WP37/WP37V precedent already established in this repository's history for the same
   situation. No second watcher, polling loop, or scheduled wake-up was used.
2. An initial (uncorrected) manual-screenshot pass during gate 11 appeared to show large blank
   regions; this was a screenshot-timing artifact (iframes not yet settled), resolved by scrolling
   the page through before capturing, and independently contradicted by the automated
   `iframe-height-contract.spec.ts` pass. See §4 for detail. Not a product defect.
3. A first attempt to check the "portable notebook URL returns HTTP 200" item guessed an incorrect
   GitHub-Pages-relative path and got HTTP 404; this was a checking-script mistake, not a site
   defect — the page's actual Colab/raw links (confirmed by inspecting the served HTML) both
   resolve correctly, and the real raw-notebook URL returns HTTP 200. See §8.1.
4. No other retry, deviation, warning, or unresolved issue occurred. No pre-deployment gate was
   rerun. No implementation, notebook, widget, data, dependency, or workflow file was modified by
   WP39.

---

## 10. Confirmations

- **No implementation content was changed by WP39.** The only files WP39 itself added are this
  report, `WPs/reports/WP39_EXACT_CHANGELOG.md`, and (as the deployment checkpoint, carried into
  the release tree unchanged) `WPs/WP39_DEPLOY_EXERCISE_10.md` itself.
- **Syllabus and Word course overview remained unchanged** throughout WP39: confirmed unchanged
  between local `main` and the WP38R branch tip before the merge (§3), and confirmed byte-identical
  to the previously deployed release after production verification (§8.1). `course_overview/` is
  not part of the GitHub Pages build and was independently confirmed unchanged in the repository
  diff.
- Literal final `git status --short --branch`, captured immediately before the documentation
  commit (i.e. with these two report files already written to disk but not yet staged/committed):

  ```text
  ## main...origin/main
  ?? WPs/reports/WP39_DEPLOYMENT_REPORT.md
  ?? WPs/reports/WP39_EXACT_CHANGELOG.md
  ```

  (Local `main` and `origin/main` in sync at `RELEASE_SHA` =
  `58ed1c61f43f0b3c6d23c1f32212bf2d3b9c9f0b`; the only untracked files are the two report files
  this commit is about to add. Immediately after the deployment attempt completed — before these
  reports were written — the tree was fully clean, as shown in §6/§8.)

- The documentation commit SHA is reported in the final chat response after the commit exists, per
  WP39 §8 item 13.

**Expected successful final state, achieved:**
- `origin/main` points to `RELEASE_SHA` (`58ed1c61f43f0b3c6d23c1f32212bf2d3b9c9f0b`).
- Local `main` is one documentation-only commit ahead of `origin/main` (this report + the exact
  changelog).
- Working tree clean.
- Exercise 10 is live and fully verified.
- WP40 has not started.
