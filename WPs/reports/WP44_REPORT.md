# WP44 report: Colab portability and active Exercise 3

## Success or failure — read this first

**Split result, exactly as the WP's own contingency anticipates.**

- **Gate B (migrate Exercise 3) succeeded.** Exercise 3 is now a
  JupyterLite-native notebook, generator-authored like Exercises 1-2,
  preserving every established number bit-for-bit, verified by direct
  reference-notebook execution *and* live in a real JupyterLite browser
  session (data load, every checked question, every native widget, the
  guarded no-cascade behavior, reset/download, a full teacher-completed
  run reproducing accuracy=0.546 and AUC=0.569 live).
- **Gate A/C's real-Colab requirement is UNVERIFIED, for all three
  exercises (1, 2, and 3), and is reported as such rather than assumed
  passed.** This coding session has no browser-automation tool and no
  authenticated Google session — there is no way to open
  colab.research.google.com, upload a `.ipynb`, and click through it, no
  matter how much local/offline/in-browser-but-not-Colab work is done
  instead. This was true before this WP started (Exercises 1-2 had never
  actually been opened in real Colab either, despite shipping to
  production) and remains true now. See "The Colab blocker" below.
- Per the WP's own instruction, this means: do not deploy, do not mark
  Exercise 3 "Colab-verified," and hand the course author a ready-to-run
  manual checklist instead of a false pass.

Nothing was merged, pushed, or deployed. `Homework_Materials/` was not
touched. Exercises 4-12 and their React widgets were not touched. The live
production site (`https://yoavmp.github.io/ml-neuro-tutorials/`, currently
serving `gh-pages@05ceb13`) is unaffected by anything in this WP.

## Branches and SHAs

- Starting point: local `main` @ `02c389d` (1 commit ahead of
  `origin/main@dcc5365`; `origin/gh-pages@05ceb13` is the live production
  deploy). `git status` was clean except the untracked WP44 spec file — no
  unexplained changes.
- Checkpoint: `refs/checkpoints/wp44-pre-work-main` and branch
  `checkpoint/wp44-pre-work`, both at `02c389d`.
- Feature branch: `feature/wp44-colab-portability-exercise-3`.
- Commits on the feature branch, in order:
  1. `ef31ab7` — checkpoint the WP spec.
  2. `2c85d1a` — Gate B: migrate Exercise 3.
  3. This report + the exact changelog (committed together as this WP's
     closing commit — see `git log -1` after that commit for its SHA).

## The Colab blocker

Stated plainly, per the WP's own explicit instruction to do so:

**This session cannot open Google Colab.** The available tools are a
sandboxed shell, a file editor, and (for the frontend) Playwright driving a
local headless Chromium against the locally-built site over
`http://localhost:4174`. None of that reaches `colab.research.google.com`,
which requires an authenticated Google session and a real, unsandboxed
browser session a human drives (or explicitly delegates). No amount of
local execution — direct cell-by-cell Python execution, `nbclient`, or a
real Playwright session against the local JupyterLite build — is the same
claim as "this ran in real Colab," and this report does not blur that line
anywhere.

**What was verified instead, and why it is still real evidence, not a
substitute:**

1. **Exact-match reference execution (offline, deterministic).** Every
   cell's source is executed directly, in order, in one namespace — the
   same technique `tests/test_exercise_02_reference_execution.py` already
   established and the maintainer guide prescribes specifically *because*
   `nbclient`/`jupyter execute` is known to hang on this course's
   `ipywidgets.Output()` pattern with no real frontend attached. This
   reproduces the audited classification result bit-for-bit (see
   "Numeric results" below) for all three exercises.
2. **A real browser, but not Colab.** `interactive/e2e-book/*.spec.ts` runs
   real headless Chromium against the actual combined
   `jupyter-book`+`jupyter-lite` build, served locally. This exercises real
   widget DOM/JS, a real Pyodide kernel, real ipywidgets comm handshakes —
   everything Colab would too, except Colab's own upload flow, its own
   installed package versions, and any Colab-specific rendering quirk.
3. **A private-repository simulation.** Each exercise's downloaded
   `.ipynb` was copied into a totally empty directory (no `book/`, no
   `data/`, nothing) and its setup+data-loading cells executed there
   directly — proving the pinned public fallback URL (never this course's
   own repository) is what actually runs and produces the expected shape,
   for all three exercises. See "Repository-independence check" below.

**What remains to actually close this gate** is exactly steps 1-5 of the
maintainer guide's new "Colab acceptance gate" section (WP41 maintainer
guide §11) — a human (or an agent with real, authorized Colab access) needs
to literally upload the three downloaded `.ipynb` files to a real Colab
session and work through the checklist in §12. This was true for Exercises
1-2 before this WP (never done — WP41/42/43's own reports only ever
performed the offline/local-browser proxies above), and remains true for
all three after it. **Exercise 3 is not, on the strength of this WP alone,
more or less Colab-ready than Exercises 1-2 already deployed were** — this
WP closes the *documentation and process* gap (the maintainer guide didn't
even have a Colab gate before), and adds one more exercise's worth of
offline/local-browser proxy evidence, but the live-Colab step itself is
outstanding for all three.

## Gate A — Exercises 1 and 2 (local-only work; Colab unverified)

Per the blocker above, this session did every locally-possible check and
explicitly stopped short of claiming the gate itself passed.

### Repository-independence check (new for this WP)

Both Exercise 1's and Exercise 2's downloaded/portable notebooks' data
fallback already used a pinned, checksummed **third-party** URL
(`raw.githubusercontent.com/neurohackademy/nh2020-curriculum/...`, not this
course's own `yoavmp/ml-neuro-tutorials` repository) — this was true before
this WP, by construction of WP41/WP42's own `load_*_table()` helpers, but
had never been empirically exercised with zero repository files present.
This WP did that: copied each portable notebook's setup+data cells into a
freshly created, completely empty directory and ran them there.

| Exercise | Result |
|---|---|
| 1 | `data.shape == (1114, 13)` — matches the established curated table |
| 2 | `data.shape == (1004, 362)`, `len(FEATURES) == 360` |
| 3 | `df.shape == (1004, 361)` (see Gate B) |

All three succeeded with **no repository file present at all** — this is a
direct, empirical demonstration that the data path keeps working if
`yoavmp/ml-neuro-tutorials` goes private, for all three exercises, not an
inference from reading the code.

### Numeric re-verification (offline)

Re-ran `tests/test_exercise_01_reference_execution.py` and
`tests/test_exercise_02_reference_execution.py` — both green, reproducing
the numbers already established in WP41/WP42's own reports (unchanged by
this WP; included here only as confirmation nothing drifted).

### Not done, and why

Live Colab upload/run for Exercises 1 and 2 — blocked, see above. No new
local proxy checks were invented beyond what WP41/WP42 already had, except
the repository-independence check above.

## Gate B — migrate Exercise 3 (succeeded)

### Audit of the pre-migration notebook

Read in full: `book/chapters/chapter_03/exercise_03.ipynb` (pre-migration,
1094 lines / 32 cells), `scripts/classification_model_audit.py`, and its
committed result `scripts/classification_model_audit_result.json`. Recorded
baseline before touching anything:

- cohort: 1004 participants, 463 autism (`group=1`), 541 control
  (`group=2`); target recoded autism=1/control=0.
- features: the same 360 bilateral cortical-thickness (`fsCT_`) columns
  Exercise 2 uses.
- split: `train_test_split(test_size=0.25, random_state=42, stratify=y)` →
  n_train=753, n_test=251.
- model: `Pipeline(StandardScaler(), LogisticRegression(C=1.0,
  max_iter=5000))`, `C_EXAMPLE = 1.0` fixed by course design, not tuned.
- locked test result: accuracy=0.545817, AUC=0.569221,
  sensitivity=0.534483, specificity=0.555556, confusion matrix
  TN=75/FP=60/FN=54/TP=62.
- threshold activity: default threshold 0.50.
- imbalance activity: fixed cohort of 400 (control always majority);
  RATIO_TABLE 50:50 through 95:5; at 90:10 → 360 control/40 autism; at
  95:5 → 380 control/20 autism.

### Data: reused, not re-exported

`book/lite/files/data/abide_age_brain.csv` (Exercise 2's own same-origin
export) already carries the `group` column, unused by Exercise 2 itself.
Before writing a single line of the generator, this WP verified directly
(a throwaway script, not assumed) that loading this file — or the same
pinned fallback URL Exercise 2 already uses — and running the audited
recipe reproduces the locked result **bit-for-bit**:

```
accuracy=0.545816733067729   (audited: 0.545817)
auc=0.569220945083014        (audited: 0.569221)
sensitivity=0.5344827586206896  (audited: 0.534483)
specificity=0.5555555555555556  (audited: 0.555556)
cm: tn=75 fp=60 fn=54 tp=62      (audited: identical)
```

Both the same-origin path and the pinned third-party fallback URL were
independently verified to reproduce this exact result — the maintainer
guide's own "both paths must return identically ordered columns" rule,
checked, not assumed. No second, independent data export was created (same
reasoning WP42 used reusing the EDA export for Exercise 1: byte-identical
to the already-approved source, no risk of a second export path drifting
from the first).

### What changed, section by section

Built `scripts/generate_exercise_03_notebook.py` following
`scripts/generate_exercise_02_notebook.py`'s exact architecture (one
authoritative module; `Blank(student, reference, id, tags)` pairs;
`--student`/`--reference`/`--check`/`--write`).

- **Section 1 — Data and setup.** Given code loads the shared table,
  verifies `group`'s raw codes are exactly `{1, 2}` before mapping anything
  (never inferred from column order), and displays class counts with the
  explicit 0=control/1=autism convention stated in prose.
- **Section 2 — sigmoid.** The old "0.48 vs 0.52" Think-first admonition
  became a checked single-choice question with full visible option text
  and real feedback.
- **Section 3 — the model.** Three new student blanks (FEATURES selection,
  X/y construction, the train/test split), each with its own
  student-facing sanity-check cell (count/names/numeric content; row
  alignment/shape/class counts; exact split sizes) that gives a helpful
  message rather than silently completing the answer. The given model-fit
  cell (the exact snippet from the WP spec) is guarded: on the untouched
  template it raises one clear `RuntimeError` naming exactly what's
  missing, not a bare traceback.
- **Section 4 — metrics.** The descriptive TN/FP/FN/TP table and formulas
  are given; constructing the confusion matrix + accuracy/sensitivity/
  specificity, and the ROC curve + AUC, are now two more student blanks,
  each with its own tolerance-based check cell (±0.03) modeled on WP42's
  KNN-check pattern — never a hidden solution, never a false "you failed"
  on a differently-valid implementation.
- **Section 5 — decision threshold.** Rebuilt as a native `ipywidgets`
  `FloatSlider` + `BoundedFloatText`, driven by the *fixed* Section 3
  probabilities (never refits the model), guarded against Section 3 being
  incomplete.
- **Section 6 — class imbalance.** Rebuilt as a native `ipywidgets`
  `Dropdown` over the same six ratios, same fixed 400-participant cohort,
  same fixed model — guarded the same way.
- **Closing.** "In summary" plus three checked takeaway questions
  (predict_proba vs. predict, effect of lowering the threshold, why 95%
  accuracy can mislead under imbalance), replacing the old MyST
  dropdown-Q&A pattern (which does not render as intended outside
  Sphinx/MyST-NB — a JupyterLite notebook is plain CommonMark).

Totals: 5 code blanks, 3 editable written-answer cells, 5 checked
questions, 2 native widgets — comparable in scale to Exercises 1 (4+4+4)
and 2 (5+5+5).

### A cascade-failure bug found and fixed before it ever reached a browser

The first draft of the Section 3→5 "paired sample" display cell
(`y_test`/`y_pred`/`y_proba` in a small table) referenced those variables
directly, unguarded — on the untouched template (where Section 3's blanks
are still empty) this would have thrown a **second, bare** `NameError`
right after the guarded cell's intentional one, which is exactly the
cascade the WP explicitly says to avoid. Caught by writing and running a
direct cell-by-cell executor against the **student** (not reference)
build before ever opening a browser: it showed precisely one exception
across the whole untouched template. Fixed by wrapping that cell in the
same `if all(name in globals() for name in (...))` guard the check cells
already use. Re-verified: exactly one exception, at the intended cell,
top to bottom, on the unmodified template.

### Prose

Student-facing markdown: **2156 words → 1124 words (-48%)**, while adding
five student code activities, three editable answers, and five checked
questions (old notebook read from this branch's own pre-migration commit;
new notebook is `book/lite/files/exercise_03.ipynb`).

## Gate C — Exercise 3 verification (local browser: passed; Colab: unverified)

### Reference-notebook execution (offline, exact)

`tests/test_exercise_03_reference_execution.py` executes the completed
reference notebook's actual cell sources (not `nbclient` — same reasoning
as Exercise 2, and confirmed independently this WP: Section 5/6's
`ipywidgets.Output()` widgets are exactly the pattern known to hang a
frontend-less kernel). Asserts, against
`scripts/classification_model_audit_result.json` directly (not
hand-copied numbers): participant/predictor counts, class counts, split
sizes, accuracy/sensitivity/specificity/AUC, the full confusion matrix,
`C_EXAMPLE`, and the imbalance widget's own 90:10 cohort math
(360 control/40 autism). Also exercises the two numeric check cells'
three behaviors (correct / complete-but-different / unfinished) directly,
mirroring WP42's `KnnCheckCellBehavior` pattern.

### Real browser, real combined build (local, not Colab)

`interactive/e2e-book/exercise-03-lite.spec.ts` (5 tests) against
`jupyter-book build book` + `jupyter lite build` served over real HTTP by
a local Chromium:

1. Kernel starts, same-origin data loads (`463 autism (group=1 -> 1), 541
   control (group=2 -> 0)`), Section 2's checked question grades correctly
   (verified selecting each option and reading the real feedback text).
2. Running the **untouched** template top to bottom: every activity check
   cell *before* the guard degrades to its own "Not complete yet" message;
   the guard cell itself raises the intended, actionable `RuntimeError`
   text, not a bare traceback. (JupyterLab's "Run All Cells" halts at the
   first uncaught exception — confirmed live — so nothing after the guard
   runs at all on the untouched template; this is the "no cascade"
   requirement satisfied by construction for everything downstream, on top
   of what item 1 above already proves for everything upstream.)
3. 390px viewport: zero meaningful horizontal overflow.
4. Reset restores the template (a fresh edit token is gone after reset);
   Back returns to Contents.
5. **Teacher-completed path, entirely live in the browser:** typed the
   reference solution into all five blanks (the same text a student would
   type), re-ran, and confirmed **live**: `n_train = 753 n_test = 251
   n_features = 360`; `Looks good: accuracy=0.546 ...`; `Looks good:
   AUC=0.569 ...`; the threshold slider changes its own printed readout
   when dragged; the imbalance dropdown recomputes correctly when switched
   from 90:10 (prints "40 autism") to 95:5 (prints "20 autism" — the exact
   expected cohort math for that ratio); **Download my notebook** produces
   a file with the placeholder gone and real solution code (naming
   `df.columns`) in its place.

Three real, live-browser bugs were found and fixed by this process (not
assumed from source): ipywidgets renders an empty, hidden "description"
`<label>` for every widget even with `description=""`, which a naive
`label` selector matches first instead of the real option labels (fixed:
scope to `.widget-radio-box label`, the same scoping the notebook's own
CSS fix already uses); a custom `feedback_correct` string starting
"Correct:" is not the shared helper's default "Correct." (fixed the test's
own expected string, not the notebook); and a cell whose output is a
matplotlib figure *then* print statements needs `.last()`, not `.first()`,
to reach the printed text (fixed the test; also simplified the imbalance
assertion to check for the ratio-specific printed number directly, which
is a stronger and more robust signal than a before/after string diff).

Full book suite, run after all of the above: **148/148 passed**, one clean
run (`npx playwright test --config playwright.book.config.ts`, default
parallel workers, no flakiness).

### Colab (unverified — see "The Colab blocker" above)

Not performed, for the reason stated at the top of this report. The
downloaded `.ipynb` at `book/downloads/chapter_03/exercise_03_portable.ipynb`
is ready for a human to run the checklist in the maintainer guide's new
§12 the moment real Colab access is available.

### The Colab acceptance gate is now documented (WPs/reports/WP41_MAINTAINER_GUIDE.md §11-12)

Added, as the WP required: an ordered 5-step gate (download → fresh Colab
session → untouched-template Run All → teacher-completed Run All →
record runtime/versions/evidence); an explicit statement of what to do
when live Colab access is unavailable (do the offline/local-browser proxy
work, state the blocker, leave a checklist, mark the gate unverified, do
not deploy); a list of the automated proxies that keep this gate honest
without being mistaken for it; and a copy-paste teacher checklist
template. Deliberately does **not** add a CI job requiring an instructor's
personal Google credentials (no supported, credential-free Colab
automation exists, and a credentialed one is a security liability out of
proportion to what it would catch beyond the proxies already documented).

## Every test, build, and manual result

**Python (offline, no network):** `python -m unittest discover -s tests` —
**1090 tests, all green, 11 skipped** (network-only, expected offline). Run
twice across this WP (mid-migration and at the end) — green both times.

**Generators:** `generate_exercise_01/02/03_notebook.py --check`,
`generate_exercise_01/02/03_transition_page.py --check` — all report up to
date.

**Jupyter Book build:** `jupyter-book build book --all` (forced full
rebuild — a plain incremental build was found, live, not to recopy a
changed `_static` file, which silently left a stale `launch-buttons.js` in
the served output; `--all` fixed it) — succeeds, 1 pre-existing warning
(missing `logo.png`, unrelated to this WP, noted in WP41's report too).

**JupyterLite build:** `jupyter lite build --config
book/lite/jupyter_lite_config.json --lite-dir book/lite --output-dir
book/_build/html/lite` — succeeds, coexists with the book hub, copies
`exercise_03.ipynb`/`exercise_03_portable.ipynb` correctly.

**Playwright, built book** (`playwright.book.config.ts`, real headless
Chromium against the actual combined build): **148 passed, 0 failed**, one
clean run with default parallel workers. Includes
`exercise-03-lite.spec.ts` (5/5), the rewritten `chapter03.spec.ts` (4/4,
transition-page-only, no analysis content), `launch-buttons.spec.ts`
(Chapter 3 added to the "migrated, no Colab button" cases),
`iframe-height-contract.spec.ts` (Chapter 3's two retired iframe cases
removed), `wp22-cross-chapter-dark-mode.spec.ts` (Chapter 3's Plotly
iframe case replaced with a JupyterLite-app-theme check), and every
already-passing spec for chapters 1, 2, and 4-10 unchanged.

**Frontend:** `npx tsc --noEmit` — clean.

**Manual/live-browser verification** (see Gate C above for the full list):
untouched-template no-cascade behavior; every checked question graded
correctly; both native widgets changing their own live output; a
teacher-completed run reproducing the exact audited accuracy/AUC;
download containing real edited content; reset/back/390px.

## Deviations and decisions requiring course-author attention

1. **Real Google Colab was never verified for Exercises 1, 2, or 3** —
   the central limitation of this WP, stated as plainly as possible
   throughout. See "The Colab blocker." This is not a regression this WP
   introduced; it is a pre-existing gap this WP found, documented
   (maintainer guide §11-12), and could not close without a tool this
   session does not have.
2. **`jupyter-book build book` did not recopy a changed `_static` file on
   a plain incremental build** — live evidence found mid-WP (the
   `launch-buttons.js` suppression edit for Chapter 3 silently had no
   effect until `--all` forced a full rebuild). Not something this WP's
   scope covers fixing in the build tooling itself; flagged here in case
   a future WP hits the same silent-staleness trap.
3. **Section 3/4's numeric check cells use a ±0.03 tolerance** (accuracy/
   sensitivity/specificity/AUC), slightly looser than Exercise 2's KNN
   check's ±0.05 R²/±3.0 MSE in relative terms — judged appropriate for
   classification metrics bounded to [0, 1], not copied mechanically from
   Exercise 2's regression-scale tolerances. Worth a second opinion if the
   course author wants tighter/looser bounds.
4. **The imbalance widget's random seed (`np.random.default_rng(20000)`)
   is fixed and not exposed to students**, unlike the old iframe widget's
   `seed-select` control — a deliberate simplification (the WP's Section 6
   spec asked to preserve "the comparison across class ratios, model
   performance, and majority-class baseline," not the seed-exploration
   axis specifically); flag if the course author wants that control back.

## Confirmation

Nothing was merged, pushed, or deployed. No GitHub Actions workflow was
triggered or inspected. `Homework_Materials/` was not touched. No exercise
other than Exercise 3 was migrated or modified (Exercises 1-2 were only
read/re-verified, not edited, except the shared `launch-buttons.js` file's
own Chapter 3 suppression entry). Exercises 4-12 and their React widgets
were not touched. WP45 was not started.
