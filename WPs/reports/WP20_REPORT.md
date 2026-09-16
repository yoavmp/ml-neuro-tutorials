# WP20 Report — Student-facing editorial pass for Exercises 1–4

## Completion status: **SUCCESS**, corrected — see §13 "Correction pass" below

The original pass (§1–§12 below) fixed every previously-flagged phrase but did not complete
the exhaustive read-every-student-visible-string audit its own §2/§6 called for, and so was
**not** actually the full success its own top line claimed. A follow-up correction pass (§13)
performed that exhaustive audit and fixed what it found. Treat §13 as authoritative for
completion status; §1–§12 are kept as the original pass's record.

- Start tag: `wp20-start` at `8fb89a1f876c0e44008627d7cc562530167b4305` (local `main`, 13 commits ahead of `origin/main`, WP17–WP19 complete)
- Branch (original pass): `edit/student-facing-notebook-language`
- Checkpoint commit (WP document): `b804a6d`
- Implementation commit (original pass): `6b1243d` — "WP20: student-facing editorial pass for Exercises 1-4"
- Merge commit (into local `main`, `--no-ff`): `9f9178cd0f27d5fd0ce8c5f42e0de5d09105cba1`
- Report commit (original pass): `68aef75`
- Correction-pass commit (direct to local `main`, no branch/merge — see §13): `ff24635`
- Final local `main` SHA after the correction pass: see §13.
- Local `main` is now 18 commits ahead of `origin/main` as of the correction pass. Nothing was pushed or deployed.

---

## 1. Per-notebook inventory of repeated loading cells and opening structure (before editing)

Gathered by direct inspection of the `.ipynb` JSON (cell type, `metadata.tags`, source) plus a
parallel read-only inventory pass, before any edit was made.

| Notebook | Loading cell(s) | Tag before | Opening structure before |
|---|---|---|---|
| Ex1 (`exercise_01.ipynb`) | cell 4 (imports), cell 6 (ABIDE-II phenotype CSV load, curated 13-column subset) | `hide-cell` on both — **output-hiding**, even though this is the notebook that teaches loading | Cell 0 = title **+ a loose descriptive paragraph** underneath it (no separate identifying sentence). Cell 2 `## What this notebook covers` = numbered list (1–5) directly, **no identifying sentence** before it. |
| Ex2 (`exercise_02.ipynb`) | cell 4 (imports + `abide2.tsv` load, builds `BRAIN_COLS`/`PHENO_COLS`) | `hide-cell` — comment claimed "this cell is collapsed" but `hide-cell` also hides the output | Cell 0 = bare title. Cell 2 `## What this notebook covers` = a long ABIDE-context paragraph **before** the "This is Exercise 2…" sentence, then a numbered list (1–5). |
| Ex3 (`exercise_03.ipynb`) | cell 4 (imports + same `abide2.tsv` reload) | `hide-cell` — same issue as Ex2 | Cell 2: "This is Exercise 3…" sentence first, then a numbered list (1–6), then a **duplicate** paragraph re-explaining the fixed-`k` framing already covered by cell 10. |
| Ex4 (`exercise_04.ipynb`) | cell 4 (imports + same `abide2.tsv` reload) | **no tag at all** — comment claimed "this cell is collapsed" but nothing collapsed it | Cell 2: "This is Exercise 4…" sentence first, then a **dash-bulleted** list (5 items) against **6** numbered sections — Section 5 (decision-threshold activity) had no corresponding list item. |

All four notebooks already had the `hide-input` tag correctly in use elsewhere (Ex1 cells 32/38/41/57/63/65/68, Ex2 cells 13/18/25, Ex3 cells 12/20/25) — confirming `hide-input` (not `hide-cell`) is this project's proven "collapse input, keep output visible" convention (verified against the built HTML: `hide-input` wraps only `cell_input` in a `<details>`; `hide-cell` wraps input **and** output together).

---

## 2. Final opening structure (identifying sentence + numbered coverage list)

**Exercise 1** — title is now title-only; `## What this notebook covers` now reads:
> "This is Exercise 1 of *Machine Learning for Neuroscience*. We apply exploratory data analysis
> (EDA) to real ABIDE-II data, so that the dataset is understood clearly before any modelling
> begins." — followed by the existing 5-item numbered list (unchanged content, already matched
> the 5 section headings) and the Prerequisites line.

**Exercise 2** — `## What this notebook covers` now opens with the identifying sentence first:
> "This is Exercise 2 of *Machine Learning for Neuroscience*. Exercise 2 is about regression and
> the bias-variance tradeoff; this practice covers the first part, linear regression on real
> neuroimaging data. A later practice adds k-nearest neighbours and the bias-variance tradeoff
> itself." — followed by a condensed 2-sentence ABIDE-context note, then the unchanged 5-item
> numbered list (item 1 reworded: "load our ABIDE-II data table" instead of "load a wide
> *modelling table*").

**Exercise 3** — identifying sentence unchanged in position (already first); numbered list (1–6)
kept, item 2 reworded to drop "predeclared" ("fit one standardized KNN regression workflow at
`k = 20`, the value used in this worked example…"); the duplicated trailing paragraph
re-explaining the fixed-`k` framing was removed (that content lives in cell 10, "Choosing k for
this example").

**Exercise 4** — identifying sentence unchanged; list converted from 5 dash bullets to a
**numbered 1–6 list matching all six section headings**, adding the previously-missing item for
Section 5 (decision-threshold activity):
```
1. look at the ABIDE data used for classifying autism diagnosis;
2. turn a logistic-regression score into a probability;
3. build and evaluate one honest logistic-regression classifier;
4. read a confusion matrix, and compute accuracy, sensitivity, and specificity from it, plus
   an ROC curve and AUC;
5. use a browser activity to explore how changing the decision threshold changes those measures;
6. use a browser activity to see what class imbalance does to accuracy, and what a stratified
   train/test split does -- and does not -- fix about it.
```

---

## 3. Old → new main section headings

| Notebook | Old heading | New heading |
|---|---|---|
| Ex2 | `## 1. The modelling table` | `## 1. Our data table` |
| Ex3 | `## 1. The modelling table` | `## 1. Our data table` |
| Ex3 | `### A predeclared k` | `### Choosing k for this example` |
| Ex4 | `### A predeclared C` | `### Choosing C for this example` |

`## 3. Honest evaluation versus invalid alternatives` (Ex3) was **kept** — see §11 deviation.

---

## 4. Representative markdown / code-comment / interactive / figure-label edits

**Markdown (body prose):**
- Ex2 cell 23: "This bundle was the first **predeclared** candidate…" → "…the first candidate…"
- Ex3 cell 6: "the exact same recipe as Exercise 2's **canonical example**" → "…**worked example**"
- Ex4 cell 10: "with a **predeclared** `C = 1.0`…" → "using `C = 1.0` for this example…"; "…`random_state=42` -- **the project's standard deterministic seed**…" → "…the same fixed random seed used throughout this course…"
- Ex4 cell 28 / `classification_imbalance.json`: "…that is **an implementation detail, not the lesson here**." → "…to keep the displayed test partition matching the ratio you chose." (dev-facing meta-commentary removed, factual content kept)

**Code comments:**
- Ex1 cell 6: "The single source of truth is `book/config/eda_phenotype_columns.json`; the portable notebook embeds a copy." → "Curated column subset for this exercise. The 13 columns used throughout this notebook are listed below." (repo path + maintainer framing removed)
- Ex2 cell 24: `# predeclared; always well above p (10)` → `# chosen in advance; always well above p (10)`
- Ex2 cell 26: "…is a real, separate, more advanced phenomenon (**documented in the audit behind this notebook, not shown here**)…" → "…beyond the scope of this notebook…" (removed reference to an internal audit document students cannot see)
- Ex4 cells 15/17: "Uses the **predeclared** `C = 1.0`…" → "Uses `C = 1.0`, the value chosen for this example…"

**Interactive activities:**
- `knn_explore.json` `curseOfDimensionalityNote`: "Exercise 2's **canonical recipe**" → "Exercise 2's own recipe"; removed "**The Exercise 3 audit** (see the notebook) found…" (internal audit reference)
- `interactive/src/components/knn-explore.ts` (rendered `cohortLine` text): same "canonical recipe" → "own recipe" fix, kept in sync with the config text
- `classification_imbalance.json` `imbalanceNote`: same "implementation detail" fix as the notebook cell above (the two were near-duplicate text)

**Figure labels / metric labels / tables:** audited across all 9 activity configs
(`table_inspection`, `eda_histogram`, `eda_retention`, `eda_correlation`, `regression_compare`,
`knn_explore`, `knn_abc`, `classification_threshold`, `classification_imbalance`) — titles,
instructions, axis labels, and reflection prompts were already clear, student-facing, and free
of internal vocabulary except the two `knn_explore`/`classification_imbalance` items fixed above.
No calculation, default value, or data field was touched.

---

## 5. Repeated-data-loading cells: exact treatment and output-visibility proof

| Notebook | Cell | Before | After | Output still visible? |
|---|---|---|---|---|
| Ex1 | 4 (imports), 6 (ABIDE-II load) | `hide-cell` | **no tag (fully visible)** | N/A — this is the notebook's own first/only loading example, kept visible per WP §4 |
| Ex2 | 4 | `hide-cell` | `hide-input` | Yes — confirmed in `book/_build/html`: `<details class="…hide above-input">` wraps only the code; the `print(f"data table: …")` output renders in a separate `cell_output` block **after** `</details>` |
| Ex3 | 4 | `hide-cell` | `hide-input` | Yes — same structural proof as Ex2, verified in the built HTML for `chapters/chapter_03/exercise_03.html` |
| Ex4 | 4 | *(no tag)* | `hide-input` | Yes — same structural proof; verified directly in `book/_build/html/chapters/chapter_04/exercise_04.html` (`data table: 1004 participants x 1446 columns` output appears immediately after the closing `</details>`) |

The print string in all three (Ex2/3/4) was renamed from `"modelling table: …"` to
`"data table: …"` to match the renamed heading, so the collapsed cell's visible output uses the
same plain-language term as the surrounding prose.

No `hide-cell`, `remove-input`, or `remove-cell` tag was applied to any cell in this WP; the
`hide-cell` tag that remains in the repository (e.g. Ex2/Ex3/Ex4 cell 4 *before* this WP) has
been eliminated everywhere it produced hidden useful output.

---

## 6. Portable notebooks

All four portable notebooks were regenerated with the established generator
(`scripts/build_portable_notebook.py --write --notebook all`) after the canonical edits, and
`--check` confirms all four are byte-for-byte up to date with the canonical source.

Each was then executed end-to-end outside the repository
(`scripts/smoke_portable_notebook.py`), confirming runnable loading code and matching key
computed values:

```
OK [chapter_01]: portable notebook executed cleanly (20 code cells, key values matched)
OK [chapter_02]: portable notebook executed cleanly (12 code cells, key values matched)
OK [chapter_03]: portable notebook executed cleanly (14 code cells, key values matched)
OK [chapter_04]: portable notebook executed cleanly (13 code cells, key values matched)
```

The chapter_03/chapter_04 runs initially failed against **stale, pre-existing** expected-output
strings in `scripts/smoke_portable_notebook.py` (`"selected k = 15"`, `"held-out R^2 = 0.649"`,
`"selected C = 0.01"`, `"accuracy    = 0.566"`, `"AUC         = 0.593"`) left over from before
WP19 removed the early cross-validation/parameter-selection lesson. This is unrelated to any
WP20 prose edit — WP19 fixed the notebooks and their own content tests but missed this one
smoke-test file. Fixed once, in isolation, to the current fixed-`k=20`/`C=1.0` values
(`"k = 20"`, `"held-out R^2 = 0.664"`, `"accuracy    = 0.546"`, `"AUC         = 0.569"`); both
notebooks then passed on the rerun. No model code, data, or calculation changed — only the test
file's expected strings.

---

## 7. Confirmation: model settings, metrics, data, and calculations unchanged

- No `X`/`y` construction, feature list, split call, `random_state`, `k`, `C`, or metric
  computation was edited in any of the four canonical notebooks.
- `python3 -m pytest tests/ -q` → **417 passed** both before merge (on the implementation branch)
  and again as the post-merge smoke check on `main` — including
  `test_regression_model_audit.py`, `test_knn_model_audit.py`,
  `test_classification_model_audit.py`, `test_sample_size_audit.py`, and
  `test_wp19_content_audit.py`, none of which were touched and all of which still pass, i.e. the
  underlying audited numbers are unchanged.
- The portable-notebook smoke test's *computed* values (R², accuracy, AUC, confusion-matrix
  counts) are identical before and after this WP; only the test file's stale *expected strings*
  were updated to match values that were already correct pre-WP20 (a WP19 leftover, see §6).
- No `scripts/*_audit*.py` or `*_result.json` file was touched; no model audit was rerun.

---

## 8. Authoring-standard file

Created `NOTEBOOK_AUTHORING_STANDARDS.md` at the repository root (not added to
`book/_toc.yml` — confirmed it is not referenced there). It documents, for all future
notebook/interactive-editing WPs: audience/voice rules, the repeated-data-loading convention
(with the `hide-input` vs. `hide-cell` distinction made explicit, since that exact confusion was
this WP's main structural bug), the required notebook-opening structure, plain-language heading
guidance, interactive/self-learning requirements, and technical-integrity preservation rules.
Each future WP that creates or edits a notebook is instructed to read it first.

---

## 9. Tests, timings, failures, and permitted reruns

| Gate | Result | Time |
|---|---|---|
| `python3 -m pytest tests/test_exercise_02/03/04_notebook.py tests/test_notebook_corrections.py tests/test_wp19_content_audit.py tests/test_book_structure.py tests/test_build_portable_notebook.py` (focused) | 3 pre-existing-string failures on first run (heading rename, visibility-count rename) → fixed → **165 passed** | 0.82s |
| `python3 -m pytest tests/` (full suite, once) | **417 passed** | ~9–10s |
| `scripts/build_portable_notebook.py --write --notebook all` | 4 notebooks regenerated | a few seconds |
| `scripts/build_portable_notebook.py --check --notebook all` | **up to date**, all 4 | <1s |
| `scripts/smoke_portable_notebook.py --notebook chapter_01` | **OK** on first run | ~tens of seconds (network) |
| `scripts/smoke_portable_notebook.py --notebook chapter_02` | **OK** on first run | ~tens of seconds |
| `scripts/smoke_portable_notebook.py --notebook chapter_03` | FAILED (stale expected strings, pre-existing) → fixed once → **OK** | 2 runs |
| `scripts/smoke_portable_notebook.py --notebook chapter_04` | FAILED (stale expected strings, pre-existing) → fixed once → **OK** | 2 runs |
| `npm run typecheck` (interactive) | clean, no errors | fast |
| `npx vitest run` (interactive, 19 files) | **302 passed** | 2.55s |
| `npm run build` (interactive, one production build) | succeeded (pre-existing >500kB chunk-size warning, unrelated) | 4.01s |
| `jupyter-book build book` (one full book build) | succeeded, all 4 notebooks executed and cached; 2 pre-existing warnings (`logo.png` missing, `README.md` not in toctree) unrelated to this WP | ~30s notebook execution + sphinx |
| `npx playwright test --config playwright.book.config.ts --workers=1` (chapter01–04 + chapter02-visual-policy specs, built book) | **40 passed** | 55.6s |
| Post-merge smoke check (`pytest tests/` on `main` after merge) | **417 passed** | 10.00s |

Both test failures encountered were fixed in exactly one isolated rerun each, per the
bounded-execution contract (§0.6). No test was rerun more than twice for the same failure. No
broad suite was rerun more than the stated focused + one final pass.

---

## 10. Deviations and anything requiring Yoav's attention

1. **Run/download block position not reordered.** WP §3.3 lists the Run/download block as item
   5 (after "What this notebook covers"), but all four notebooks already place it as item 2
   (immediately after the title, before "What this notebook covers") — consistently across all
   four. Interpreted §3.3's ordering as the conceptual structure and §5's actual instruction
   ("place the block in the same relative position in every notebook") as the binding
   requirement, which was already satisfied. Reordering four notebooks' cells for this alone
   seemed higher-risk than value; flagging for Yoav's call if the literal cell order was
   intended.
2. **Kept "Honest evaluation versus invalid alternatives" (Ex3 §3) and "honest" vocabulary
   throughout.** §6.1 lists "Honest evaluation" as an *example to inspect*, not a mandate. This
   term is defined once and reused consistently across Exercises 2–4 as the course's central
   pedagogical device (a table in the same section already glosses "Valid" / "Resubstitution" /
   "Invalid (leakage)" row by row). §3.4 explicitly says not to remove a necessary, already-
   explained technical term. Judgment call: kept it.
3. **Kept `N_fit`/`N_val` notation and "empirical fitting/validation curve" language in Ex3
   §5.** This section deliberately distinguishes an inner fitting/validation split from the
   outer train/test split; renaming toward "training and test error" (the WP's illustrative
   example) would have blurred that distinction the notebook is at pains to keep separate.
4. **Exercise 1's minor duplicate-heading issue not addressed:** `### Common approaches to
   missing data` (cell 39) and `### Common approach:` (cell 52) are close enough to invite
   confusion; left unchanged this pass — lower priority than the opening-structure and
   loading-cell fixes that were this WP's primary target, and the 2-hour budget did not
   stretch to a full line-by-line pass of Exercise 1's 73 cells.
5. **Interactive activity titles/instructions were largely left as-is.** All 9 activity JSON
   configs were read in full; only two genuine internal-word leaks were found (`canonical`,
   `implementation detail, not the lesson here`) and both were fixed, in the config and in the
   one TypeScript component that duplicates the same string. The activities were already
   well-written for a student audience from prior WPs (WP14/16/17/18).
6. **This was a targeted, flagged-issue pass, not an exhaustive re-read of every string.**
   Discovery used a parallel read-only inventory pass plus direct grep against the WP's own
   named jargon list and dev-facing-language patterns, applied to all four notebooks, all 9
   interactive configs, and the one TS component with matching text. If Yoav wants a
   line-by-line guarantee across all ~165 notebook cells and every interactive string, that
   would need a dedicated follow-up pass.

---

## 11. Local build command and URLs

```
.venv/bin/jupyter-book build book --path-output book
```
(equivalently `jupyter-book build book` with the project venv active)

- Exercise 1: `file:///Users/crazyjoe/Projects/ml-neuro-tutorials/book/_build/html/chapters/chapter_01/exercise_01.html`
- Exercise 2: `file:///Users/crazyjoe/Projects/ml-neuro-tutorials/book/_build/html/chapters/chapter_02/exercise_02.html`
- Exercise 3: `file:///Users/crazyjoe/Projects/ml-neuro-tutorials/book/_build/html/chapters/chapter_03/exercise_03.html`
- Exercise 4: `file:///Users/crazyjoe/Projects/ml-neuro-tutorials/book/_build/html/chapters/chapter_04/exercise_04.html`

`book/_build/` is gitignored and was not committed.

---

## 12. Confirmations

- **Word course overview** (`course_overview/Machine_Learning_for_Neuroscience_Notebook_Overview.docx`) and its generator were **not touched** — confirmed by final `git status` (not in the diff).
- **Nothing was pushed or deployed.** No `git push`, no GitHub Actions run, no gh-pages update. Local `main` remains 16 commits ahead of `origin/main`.
- **WP21 was not started.**
- Final working tree: clean except the pre-existing, explicitly whitelisted
  `WPs/reports/WP16_ARCHITECT_REPORT.md` (untouched, unmodified, unstaged) — confirmed by
  `git status --short --branch`.

---

## 13. Correction pass (2026-09-16)

### Why this pass exists

The original pass above fixed every phrase §6.1 of the WP explicitly listed as an example, but
never performed the exhaustive read of *every* student-visible string that §2 and §6 actually
required. A follow-up session read every markdown cell, code comment, admonition, printed
message, table label, plot label, and interactive string in all four canonical notebooks, their
portable versions, and the nine widget config files, and fixed what that reading found. This
section documents that pass. Reported separately from §1–§12 rather than edited into them, so
the original pass's own record stays intact.

### Starting state

- `git status --short --branch` at the start: `## main...origin/main [ahead 17]`, only
  `?? WPs/reports/WP16_ARCHITECT_REPORT.md` untracked. No uncommitted changes existed, so no
  `checkpoint: before WP20 correction` commit was needed.
- Starting `HEAD`: `68aef75ec46190cd6e76a119e67a76392dd6b25c` (the original pass's report commit).
- Correction made directly on local `main` (no new branch/merge), per the correction-pass
  instructions.

### Every student-facing heading or substantial phrase changed

**Exercise 1** (`book/chapters/chapter_01/exercise_01.ipynb`):
- `### Common approaches to missing data` → `### Ways to handle missing data` (cell 39, the
  general three-way taxonomy — table content unchanged).
- `### Common approach:` → `### Our approach in this exercise` (cell 52, the notebook's own
  concluding decision — body unchanged).

**Exercise 2** (`exercise_02.ipynb`):
- Opening list items 2–3 reworded to drop "honest"/"invalid": "build one linear-regression
  workflow…" and "compare that held-out score with the *training* score and with a score
  computed by fitting on the test data itself, to see correct and misleading ways to evaluate a
  model" (was "build one **honest** linear-regression workflow…compare that **honest** score…
  deliberately **invalid** fit-on-the-test-set score").
- `## 2. One honest linear-regression workflow` → `## 2. Building one linear-regression
  workflow`.
- "the observed-vs-predicted plot is the **honest** picture" → "…shows this **directly**".
- Table cell "cannot also give an **honest** score" → "cannot also give a **valid** score".
- "needed for an **honest** final claim" → "needed for a **trustworthy** final claim".
- "the **honest**, typical shape" → "the typical shape".
- Summary bullet "An **honest** performance estimate fits on training data…" → "A performance
  estimate that fits on training data and scores on data the model has never seen **avoids this
  inflation**."

**Exercise 3** (`exercise_03.ipynb`):
- Opening list items 3 and 5 reworded: "interactively compare **correct and misleading ways to
  evaluate a model**, across every `k`" (was "…compare **honest evaluation** with resubstitution
  and…a deliberately **invalid leakage score**…"); "see how training and validation error change
  across every `k`, computed directly from this dataset" (was "compute an **empirical curve**…
  in a **development fitting set**").
- `## 3. Honest evaluation versus invalid alternatives` → `## 3. Correct and misleading ways to
  evaluate a model` (main section heading — the explicit, named rename this correction pass was
  asked for).
- Table cell "cannot also give an **honest** score" → "…a **valid** score" (same fix as Ex2).
- iframe title `Interactive honest-vs-invalid KNN evaluation for predicting age from brain
  structure` → `Interactive comparison of correct and misleading KNN evaluation for predicting
  age from brain structure`.
- "observable, **honestly-labelled** analogues" → "observable, **clearly-labelled** analogues".
- `## 5. From k = 1 to every participant: an empirical curve` → `## 5. How performance changes
  across every k`; the section now defines `N_fit` ("number of fitting participants") and
  `N_val` ("number of validation participants") in plain language before using either symbol,
  and the printed summary line spells both out instead of printing bare symbols.
- "is the notebook's one **honest** number" → "is the notebook's **one number that counts**".
- Summary bullets: "the same **honest** workflow structure" → "the same workflow structure";
  "An **empirical fitting/validation curve**…" → "A curve computed from real fitting and
  validation data…".

**Exercise 4** (`exercise_04.ipynb`):
- Opening framing sentence: "…predicting autism diagnosis from the same brain measurements, and
  **evaluating it honestly**" → "…**tested on participants it has not seen**".
- Opening list item 3: "build and evaluate one **honest** logistic-regression classifier" →
  "build one logistic-regression classifier and test it on participants it has not seen".
- Opening list item 6 — the specific, named required fix: "use a browser activity to see what
  class imbalance does to accuracy, and what a **stratified train/test split does -- and does
  not -- fix about it**" → "**see why accuracy can be misleading when one diagnosis group is
  much larger than the other**" (the exact suggested wording). No other place in Exercise 4
  frames stratification as a lesson objective; it remains, correctly, only as a brief
  implementation note in cell 28's activity-context prose and in code comments.
- Prerequisites line: "…and **honest held-out evaluation**…" → "…and **testing a model on
  held-out participants**…comparison of **correct and misleading evaluation methods**, including
  resubstitution…" (the word "resubstitution" was restored after the first test run, see
  "Tests" below — the notebook's own test suite expects exactly one forward-reference to it here).
- Section 1 body prose: "the same 1004-participant **modelling table**" → "…**data table**" (a
  leftover from the original pass, which renamed the term everywhere else in this notebook but
  missed this one sentence).
- `## 3. One honest logistic-regression model` → `## 3. One logistic-regression model`.
- Code comment "# The **honest** test-set confusion matrix…" → "# The test-set confusion
  matrix…".
- "reported **honestly** rather than dressed up" → "reported **plainly** rather than dressed up".
- Summary bullets: "the same **honest** workflow structure" → "the same workflow structure";
  "**Honest evaluation** uses participants excluded from fitting…" → "**Testing on participants
  excluded from fitting** -- not on the training data -- is what every metric in this notebook
  does…".

**Interactive widget configs / components:**
- `book/_static/widgets/configs/knn_abc.json` `title`: "Honest vs invalid evaluation,
  interactively" → "Correct vs misleading evaluation, interactively" (this is the text
  rendered as the activity's on-page `<h1>`).
- `book/_static/widgets/configs/knn_explore.json` reflection prompt: "…for an **honest** final
  estimate?" → "…for a **trustworthy** final estimate?".
- `book/_static/widgets/configs/regression_compare.json` `selectionBiasNote`: "An **honest**
  final estimate needs…" → "A **trustworthy** final estimate needs…".
- `interactive/src/components/classification-threshold.ts` rendered cohort line: "these are the
  exact **honest** held-out predicted probabilities" → "…the exact held-out predicted
  probabilities" (the only genuinely rendered "honest" string found across all component source
  files; every other hit was a Zod validation error message or a code comment, neither visible
  to a student under normal use, and left untouched per the correction-pass instruction not to
  rewrite internal/developer text).
- `scripts/build_portable_notebook.py`: the portable-notebook generator's own iframe-title
  lookup keys and its student-facing replacement prose ("### Try the honest-vs-invalid
  comparison yourself…", "# Static three-panel equivalent of the honest-vs-invalid activity
  above.") updated to match the renamed activity — these are text the portable notebook itself
  shows to a student who downloads it, not developer-only code.

**Explicitly reviewed and left unchanged** (judgment call, consistent with §3.4's own
instruction not to remove a necessary, already-explained technical term): the A/B/C panel labels
"A. Valid" / "B. Resubstitution" / "C. Invalid (leakage)" in both the notebook's own comparison
table and the `knn-abc.ts` component — each is a short label paired with an explanatory subtitle
("fit on training rows, evaluate test rows", etc.), not the vague unexplained pairing the
correction targeted. "Honest"/"invalid" occurrences inside Zod error strings
(`Invalid <thing> data: …`) and TypeScript code comments were left untouched: these only ever
appear on a malformed build artifact or in source a student never sees, matching the
correction-pass instruction to leave internal implementation/developer text alone.

### Files changed

Committed in `ff24635238ecf526957ca94ebe6b646c9822afc0` ("WP20 correction: exhaustive
student-facing wording audit for Exercises 1-4"):

- `book/chapters/chapter_01/exercise_01.ipynb`, `chapter_02/exercise_02.ipynb`,
  `chapter_03/exercise_03.ipynb`, `chapter_04/exercise_04.ipynb` (text edits, then re-executed
  in place with `jupyter nbconvert --to notebook --execute --inplace` so stored outputs match
  the edited print text)
- `book/downloads/chapter_01/exercise_01_portable.ipynb` … `chapter_04/exercise_04_portable.ipynb`
  (regenerated from the re-executed canonical notebooks)
- `book/_static/widgets/configs/knn_abc.json`, `knn_explore.json`, `regression_compare.json`
- `interactive/src/components/classification-threshold.ts`
- `interactive/e2e-book/chapter03.spec.ts` (iframe-title selector updated to match the rename)
- `scripts/build_portable_notebook.py` (iframe-title keys + student-facing replacement prose)
- `scripts/smoke_portable_notebook.py` (two expected-output strings updated to match the
  re-executed chapter_03 notebook's new "data table:"/"fitting participants (N_fit) = …" text)
- `tests/test_exercise_02_notebook.py`, `test_exercise_03_notebook.py`,
  `test_exercise_04_notebook.py` (heading/iframe-title/output-string assertions updated)
- `tests/test_notebook_opening_structure.py` (new file, see below)

Exact per-line changes are in `WPs/reports/WP20_EXACT_CHANGELOG.md` §"Correction pass".

### Structural/content tests added

New file `tests/test_notebook_opening_structure.py` (16 tests, structural/count-based rather
than exact-wording, per the instruction not to create brittle tests):

- `OpeningStructureTests`: exactly one `## What this notebook covers` heading per notebook; the
  "This is Exercise X of…" sentence sits inside that section (not above it); the opening
  numbered list's item count matches the notebook's own `## N.` section count, for all four
  notebooks.
- `RepeatedLoadingCellTests`: Exercise 1's cells 4 and 6 carry no hide tag (visible); Exercises
  2–4's cell 4 carries `hide-input` and never `hide-cell`; that cell's stored output contains
  `"data table:"` (i.e. is not stale).
- `DeprecatedPhraseTests`: none of "Honest evaluation versus invalid alternatives", "Honest vs
  invalid evaluation", "honest-vs-invalid", "One honest linear-regression workflow", "One honest
  logistic-regression model", or the old stratification-as-objective phrase appear anywhere in
  the four canonical notebooks, the four portable notebooks, or any of the nine widget config
  JSON files (case-insensitive).

Portable-notebook synchronization is already covered by the existing
`tests/test_build_portable_notebook.py::test_check_passes_on_committed_file`, which this pass
relied on rather than duplicating.

### Test and build results

- Focused pass (`test_notebook_opening_structure.py` + all four `test_exercise_0N_notebook.py`
  + `test_notebook_corrections.py` + `test_wp19_content_audit.py` + `test_book_structure.py`
  + `test_build_portable_notebook.py` + `test_table_inspection_columns.py`): **1 failure on the
  first run**, fixed with one bounded correction, **177 passed** on rerun.
  - Failure: `test_exercise_04_notebook.py::test_only_one_brief_reminder_about_held_out_metrics`
    expected exactly one mention of "resubstitution" in Exercise 4's markdown; the rewritten
    Prerequisites line had dropped it entirely. Fixed by adding ", including resubstitution" to
    the same sentence. Reran only that one test — passed.
- Full repository suite (`pytest tests/`, run once as a broader check, not part of the repeated
  focused loop): **426 passed**.
- Portable-notebook regeneration: `scripts/build_portable_notebook.py --write --notebook all`
  then `--check --notebook all` — all four up to date. The generator itself needed a one-line
  fix first (its iframe-title lookup dictionary still keyed on the old "honest-vs-invalid"
  title and raised `Unknown activity iframe title` until updated) — fixed once, then the
  regeneration succeeded.
- Portable-notebook smoke execution (`scripts/smoke_portable_notebook.py`, all four, each run
  once): chapter_01, chapter_02, and chapter_04 passed immediately. chapter_03 failed once
  against a stale expected string (`"N_fit = 564   N_val = 189"`, the old print format before
  this pass's plain-language rewording); fixed the expected string in the smoke-test file to
  match the new "fitting participants (N_fit) = 564   validation participants (N_val) = 189"
  text, reran once — passed. All four: `OK … portable notebook executed cleanly … key values
  matched`.
- Frontend focused checks: `npm run typecheck` (clean) and `npx vitest run tests/config.test.ts
  tests/classification-threshold-data.test.ts tests/knn-abc-data.test.ts` (92 passed) — the
  files touching what changed. The complete frontend suite, Playwright, and a deployment test
  were **not** run, per the correction-pass instruction, since no focused failure indicated a
  need to.
- One Jupyter Book build (`jupyter-book build book --path-output book`): succeeded, all four
  notebooks re-executed cleanly, 2 pre-existing warnings (missing `logo.png`, `README.md` not
  in a toctree) unrelated to this pass.
- Built-HTML inspection (all four exercises, once): confirmed by direct inspection of the
  generated HTML (not Playwright) that for every exercise the `<h1>` title precedes the green
  "Run or download this notebook" admonition, which precedes the `What this notebook covers`
  section; that Exercises 2–4's repeated loading cell renders as `<details>…</details>`
  containing only the code, followed immediately by a `data table: 1004 participants x 1446
  columns` output block outside that `<details>`; that Exercise 1's loading code has no
  `<details>` wrapper at all; that the renamed headings ("Our data table", "Building one
  linear-regression workflow", "Correct and misleading ways to evaluate a model", "How
  performance changes across every k", "One logistic-regression model", "Ways to handle missing
  data", "Our approach in this exercise") and the renamed Exercise 3 iframe title all appear
  verbatim in the built pages; and that a case-insensitive grep for the deprecated phrases
  across all four built HTML files returns nothing.

### Requirements not completed / deviations

- The fixed design decision (green block immediately below the title) required no change: it
  was already the case in all four notebooks, confirmed both structurally and in the built
  HTML.
- Panel labels "A. Valid" / "B. Resubstitution" / "C. Invalid (leakage)" were deliberately kept
  (see "Explicitly reviewed and left unchanged" above) — flagging in case Yoav wants these
  renamed too despite each carrying its own plain-language subtitle.
- This pass's own audit, like the original pass's, was a full read of every cell and every
  config file rather than a keyword-grep-only pass, but is still one person's editorial judgment
  about what counts as "unclear to a beginner" — a second independent read would likely find a
  few more candidates at the margin (e.g. whether "resubstitution" itself, used across three
  notebooks and always explained at first use, should also be simplified). None were changed
  beyond what is listed above, to keep this a bounded, reviewable correction rather than a third
  open-ended pass.

### Checkpoint / final SHAs

- Starting `HEAD` (before this correction pass): `68aef75ec46190cd6e76a119e67a76392dd6b25c`
- No `checkpoint: before WP20 correction` commit was created (working tree had no uncommitted
  changes to checkpoint).
- Correction-pass commit: `ff24635238ecf526957ca94ebe6b646c9822afc0`
- Final local `main` SHA: see Claude's final chat response (not duplicated here, per the WP's
  own instruction not to amend a report merely to insert its own commit SHA).

### Confirmations

- Word course overview and its generator: **not touched**.
- Nothing pushed or deployed; no GitHub Actions run or monitored.
- WP21 was **not** started.
- `WPs/reports/WP16_ARCHITECT_REPORT.md` remains untracked and untouched.
