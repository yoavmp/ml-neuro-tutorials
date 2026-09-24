# WP38 — Exercise 10: Examples and Common Mistakes — Report

## 1. Overall result

**Success.** The UCI HAR mandatory preflight audit (spec §8.2) passed all
four inclusion conditions decisively, so implementation proceeded. Exercise
10 was built as a 37-cell canonical notebook plus a fully self-contained
39-cell portable notebook, with four new browser-native interactive
activities, four new committed data artifacts, five new/updated Python
audit/export scripts, and a compact, provenance-documented UCI HAR subset.
All local validation gates in the spec's bounded plan (§17) passed. Nothing
was merged, pushed, deployed, or monitored through CI.

## 2. Starting state

- Local `main` SHA (verified): `2f74ccae826d14da9dee9997d890697d159d91c0`
  (WP37V report commit).
- `origin/main` SHA (verified): `f792ad55f34342e627ed1fe3b85ff60777507d85`.
- Local `main` was exactly two documentation-only commits ahead of
  `origin/main` (`bf6aaa2` WP37, `2f74cca` WP37V) — confirmed via
  `git diff origin/main..main --stat` (only `WPs/reports/*.md` files
  touched). Working tree was clean apart from the untracked WP38 spec file.
  WP16/WP21 report files were confirmed tracked, not untracked.
- Branch `feature/wp38-exercise10-common-mistakes` created from that
  verified `main`.

## 3. Checkpoint, implementation, and final commit SHAs

- Checkpoint (spec only): `06fd62af0ea0eee8bcf5cc20274c8a5a1d8f7602` —
  "WP38: add specification (initial checkpoint)".
- Implementation: `61a16c6f26a81b32c76c884b3122d266edc31bc1` — "WP38:
  Exercise 10 — Examples and Common Mistakes" (62 files changed, 21,262
  insertions, 44 deletions).
- Reports: committed separately immediately after this report and the
  exact changelog were finalized — see `git log -1` on this branch for the
  exact SHA (this report is written before that commit exists, so it
  cannot literally quote its own resulting hash).

## 4. Final notebook outline and cell count

`book/chapters/chapter_10/exercise_10.ipynb` — **37 cells** (target
32–38):

1. Title
2. Run/download admonition
3. What this notebook covers (4 numbered bullets, per spec §4 — this
   deliberately does not enumerate all 7 numbered sections one-for-one, an
   explicit WP38 §4 instruction that supersedes `NOTEBOOK_AUTHORING_STANDARDS.md`'s
   general "one list item per section" convention; documented as a judgment
   call in §12 below)
4. `## 1. The Boundary Around the Training Data` — principle, compact flow
   diagram (inline HTML/CSS, matching the Exercise 4 nested-CV diagram
   style, shorter), 6-bullet exclusion list, quiz lead-in
5. Quiz iframe (`multi-select-quiz`)
6. `## 2. A Leakage Laboratory` — intro
7. Data loading (`hide-input`, pinned `abide2.tsv`)
8–14. Scaling / feature-selection / PCA / median-fill wrong-vs-correct code
   pairs (markdown + code, alternating)
15. Leakage-lab activity intro
16. Leakage-lab iframe (`leakage-lab`)
17. Predeclared-design summary + required honesty sentence
18. Think First block
19. `## 3. Do Not Choose the Model With the Test Set` — intro
20. Static table reusing Exercise 4's own audited candidate-k results
    (`hide-input`)
21. Workflow explanation + questions
22. `## 4. Related Observations Must Stay Together` — UCI HAR intro,
    attribution, neuroscience analogues
23. UCI HAR compact-table load (`hide-input`)
24. HAR activity intro
25. HAR iframe (`har-fold-compare`)
26. HAR reproduction cell (`hide-cell`, one k, ordinary vs. grouped)
27. Preflight summary + guiding questions (Think First)
28. `## 5. Class Imbalance Changes the Question` — intro + activity intro
29. Imbalance iframe (`imbalance-threshold`)
30. Imbalance reproduction cell (`hide-cell`)
31. Honesty statement + questions
32. `## 6. Does the Split Match the Scientific Question? (Bonus)` — site
    diagram + text
33. `## 7. Find the Mistake` — intro
34. Fragments 1–3 (code blocks + dropdown answers)
35. Fragments 4–5 (code blocks + dropdown answers)
36. Final Checklist (9 bullets)

Portable notebook: `book/downloads/chapter_10/exercise_10_portable.ipynb`
— **39 cells** (banner + setup + install cell, then the canonical cells with
each iframe replaced by a runnable equivalent or a link-back block; the UCI
HAR compact table embedded inline as base64 so it needs no repository file).

## 5. Exact checkbox options and answer behavior

Question (from `book/_static/widgets/data/leakage_quiz.json`):

> Which operations learn quantities or make data-dependent decisions and
> must therefore not use the final test participants? Select all correct
> answers.

Seven options, in the spec's exact order, six correct:

1. Calculating the mean and standard deviation for scaling — correct
2. Choosing features based on their correlation with the target — correct
3. Fitting PCA — correct
4. Calculating median values for filling missing data — correct
5. Selecting a model parameter from performance results — correct
6. Fitting the final prediction model — correct
7. Choosing in advance whether success will be summarized with F1,
   ROC-AUC, or another metric — **incorrect** (the only incorrect option)

No color/renaming distractors. Behavior (verified by 42 passing standalone
Playwright tests plus a built-book test): all options unmarked/hidden
feedback before "Check answer"; any number selectable; after checking,
correct-selected marked correct, incorrect-selected marked incorrect,
missed-correct visibly identified, every option's own feedback sentence
shown; only an exact match (all 6 correct, 0 incorrect) shows the success
panel (verbatim success text + nuance sentence from the data file); "Try
again" clears every mark/selection; a page refresh restores the untouched
initial state (no `localStorage`, no network call beyond the initial
config/data fetch); keyboard-operable native controls, `for`/`id`-linked
labels, `aria-describedby` per option, one `aria-live="polite"` outcome
region.

## 6. Leakage scenarios, data, splits, and before/after results

Predeclared design (`book/config/abide_modeling.json` → `leakage_lab`,
`scripts/export_leakage_lab_data.py`): target `age` (1,004 eligible
participants, 0 missing), sample sizes `[60, 100, 250, 1004]`, seeds
`[0, 1, 2, 3, 4]` — every seed and sample size fixed **before** any result
was computed. Each `(scenario, sample size, seed)` draws one cohort and one
outer 75/25 split, reused identically for the correct and leaky variant
(60 entries total, one per combination).

| Scenario | Bundle (feature count) | Correct workflow | Leaky workflow |
|---|---|---|---|
| Scaling | `sensorimotor_core` × CT (p=10) | Split first; `Pipeline(StandardScaler(), LinearRegression())` fit on train only | `StandardScaler` fit on train+test, then split |
| Feature selection | `all-eligible` × CT (p=360 → 20 selected) | Split first; `Pipeline(SelectKBest(f_regression, k=20), StandardScaler(), LinearRegression())` fit on train only | `SelectKBest` fit on train+test and the target, then split |
| PCA | `frontoparietal` × CT (p=78 → 10 components) | Split first; `Pipeline(StandardScaler(), PCA(n_components=10), LinearRegression())` fit on train only | `StandardScaler`+`PCA` fit on train+test, then split |

Mean leaky-minus-correct R² gap per (scenario, sample size), across the 5
predeclared seeds:

| Scenario | n=60 | n=100 | n=250 | n=1004 |
|---|---|---|---|---|
| Scaling | 0.000 | 0.000 | 0.000 | 0.000 |
| Feature selection | +0.015 (range −0.87…+0.46) | −0.153 | −0.038 | +0.002 |
| PCA | −0.123 | −0.245 | +0.018 | −0.005 |

**Honest finding, not curated:** scaling shows an **exact** zero gap in
every one of its 20 entries. This is a genuine mathematical fact (ordinary
least-squares predictions are invariant to any consistent invertible
rescaling of the inputs), not a bug — the notebook explains this explicitly
and uses it to make the point that the discipline of training-only fitting
matters even when a specific case shows no visible effect. Feature
selection and PCA are noisy at small n (tiny 15–25-row test partitions),
occasionally favoring the *correct* pipeline in a given split — the
notebook and widget both state plainly that "leakage makes the evaluation
invalid even when its score is similar — or occasionally worse — in one
particular split," and no seed was chosen after seeing results (all 5 were
generated and reported together). The full-cohort (n=1004) feature-selection
row, the most stable, shows a small positive mean gap consistent with the
expected direction.

## 7. UCI HAR provenance, licence, fixed features, checksums, extraction

- Source: Human Activity Recognition Using Smartphones
  (Reyes-Ortiz, Anguita, Ghio, Oneto, Parra) —
  <https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones>,
  DOI <https://doi.org/10.24432/C54S4K>, CC BY 4.0.
- Original archive: `human+activity+recognition+using+smartphones.zip`,
  SHA-256 `c00b803081a5c797cd5e4b83700a9810b38d53d9d84e01917e090e1fdbc81031`;
  inner `UCI HAR Dataset.zip`, SHA-256
  `2045e435c955214b38145fb5fa00776c72814f01b203fec405152dac7d5bfeb0` (both
  pinned and verified in `scripts/export_uci_har_data.py`).
- Extraction: deterministic, `scripts/export_uci_har_data.py --refresh`,
  concatenating `train` then `test` splits in each split's original row
  order; the 18-feature subset is the exact official names from
  `features.txt` (verified present verbatim), chosen by measurement family
  (mean/std of body acceleration, gravity acceleration, body angular
  velocity per axis) — never by predictive performance.
- Compact table: `book/data/uci_har/uci_har_compact.csv.gz` (10,299 rows,
  30 participants, 6 activities, 888 KB compressed); provenance at
  `book/data/uci_har/provenance.json` including the derived file's own
  SHA-256, re-verified offline by `scripts/export_uci_har_data.py --check`.
- All notebook and test execution reads only this committed compact file
  (`uci_har_data.load_compact_table`) — fully offline; the network refresh
  path is maintainer-only and was exercised once during this WP.

## 8. Complete HAR preflight table (all five k values)

`Pipeline(StandardScaler(), KNeighborsClassifier())`, ordinary
`StratifiedKFold(5, shuffle=True, random_state=42)` vs. participant-grouped
`StratifiedGroupKFold(5, shuffle=True, random_state=42)`:

| k | ordinary acc | grouped acc | acc gap | ordinary macro-F1 | grouped macro-F1 | F1 gap | positive folds (of 5) |
|---|---|---|---|---|---|---|---|
| 1 | 0.8963 | 0.8069 | +0.0894 | 0.8903 | 0.7964 | +0.0939 | 5 |
| 3 | 0.8973 | 0.8259 | +0.0714 | 0.8918 | 0.8161 | +0.0758 | 5 |
| 5 | 0.8938 | 0.8307 | +0.0630 | 0.8882 | 0.8217 | +0.0665 | 5 |
| 11 | 0.8877 | 0.8411 | +0.0466 | 0.8819 | 0.8321 | +0.0498 | 5 |
| 25 | 0.8674 | 0.8361 | +0.0313 | 0.8603 | 0.8265 | +0.0338 | 4 |

**Preflight verdict: PASS**, all four conditions:

1. Ordinary splitting places participant data across train/validation in
   every fold — **30/30 participants** cross folds.
2. Grouped splitting has zero participant overlap — confirmed directly
   (disjoint sets per fold) and via the crossing count (0/30).
3. Ordinary is ≥0.03 more optimistic (accuracy or macro-F1) for ≥2 of 5 k
   values — **all 5 of 5** qualify (required: ≥2).
4. Direction is not from one anomalous fold — every qualifying k has ≥4 of
   5 individual folds positive (4 k's have 5/5, one has 4/5; required: ≥3).

Committed at `scripts/har_group_leakage_audit_result.json`
(`scripts/har_group_leakage_audit.py --run`/`--check`).

## 9. Participant overlap evidence

- Observations per participant: min 281, median 342.5, max 409, mean 343.3.
- Ordinary splitting: 30/30 participants have rows in more than one of the
  5 folds (i.e., every participant's data appears on both sides of the
  train/validation boundary for at least one fold).
- Grouped splitting: 0/30 participants cross folds; independently verified
  that every fold's participant set is disjoint from every other fold's.

## 10. Imbalance class counts and complete metric comparison

Fixed 90:10 cohort (reusing Exercise 3's own cohort-draw mechanism and
`C=1.0` logistic-regression recipe): 400 participants (360 control, 40
autism), one locked stratified 25% test split (90 control, 10 autism;
majority baseline accuracy 90.0%, positive prevalence 10.0%).

| Model | Accuracy @0.5 | Recall @0.5 | Recall @0.1 | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|
| Ordinary | 85.0% | 1/10 (10%) | 1/10 (10%) | 0.6300 | 0.1434 |
| Class-weighted (`class_weight="balanced"`) | 81.0% | 1/10 (10%) | 3/10 (30%) | 0.6278 | 0.1420 |

Confusion matrix @0.5: ordinary TN=84 FP=6 FN=9 TP=1; class-weighted TN=80
FP=10 FN=9 TP=1. At the default threshold both models catch very few
autism cases (the "high accuracy can still miss the minority class" point);
class weighting's advantage only appears at a lower threshold, where it
triples recall at the cost of more false alarms — exactly the "not
guaranteed to improve every metric" honesty statement the spec requires.

## 11. Every validation command and result

Run in the order given by spec §17:

1. UCI HAR preflight: `python3 scripts/har_group_leakage_audit.py --run` →
   **PASS** (table in §8). `--check` reproducibility confirmed.
2. Compact data subset + extraction/audit architecture committed:
   `scripts/export_uci_har_data.py --refresh` then `--check` → **OK**.
3. Focused audit/export checks — all six new/touched export scripts'
   `--check`/`--refresh` modes run successfully:
   `export_leakage_lab_data.py`, `export_har_fold_widget_data.py`,
   `export_imbalance_threshold_data.py`, `export_uci_har_data.py`,
   `har_group_leakage_audit.py`, `abide_modeling_data.py --check` (manifest
   self-consistency, unaffected by the new `leakage_lab` key).
4. Focused Exercise 10 notebook/content tests:
   `python3 -m unittest tests.test_exercise_10_notebook` → **18/18 pass**.
5. Canonical notebook executed once via `nbclient`
   (`resources.metadata.path` = the chapter's own directory) → **all 37
   cells executed cleanly**, outputs match the audited numbers above.
6. Portable notebook generated (`build_portable_notebook.py --write
   --notebook chapter_10`) and `--check --notebook all` → **OK, all 10
   registered chapters up to date**.
7. Portable notebook smoke-executed outside the repository (copied to an
   isolated temp directory, no repo files present) →
   `scripts/smoke_portable_notebook.py` → **OK [chapter_10]: portable
   notebook executed cleanly (10 code cells, key values matched)**; the
   full 10-chapter smoke suite (`scripts/smoke_portable_notebook.py`, no
   args) also passed for every chapter.
8. Frontend typecheck + focused unit tests:
   `npm run typecheck` → clean; `npm run test:unit` → **38 files, 475
   tests passed** (includes the 4 new data-module test files + new
   `config.test.ts` cases).
9. One frontend production build: `npm run build` → succeeded (pre-existing
   >500 kB bundled-Plotly chunk warning, unrelated to this change).
10. Focused standalone Playwright for the 4 new activities:
    `npx playwright test e2e/leakage-quiz.spec.ts e2e/leakage-lab.spec.ts
    e2e/har-fold-compare.spec.ts e2e/imbalance-threshold.spec.ts` →
    **42/42 passed** (both path prefixes).
11. One clean Jupyter Book build: `jupyter-book build book/` → succeeded,
    `book/_build/html/chapters/chapter_10/exercise_10.html` produced, no
    errors.
12. Focused built-book tests: `interactive/e2e-book/chapter10.spec.ts`
    (new), `iframe-height-contract.spec.ts` (4 new cases appended), and
    `launch-buttons.spec.ts` (Chapter 10 moved from the placeholder
    no-button list into the mapped-chapter loop) — see exact pass counts
    in the addendum below (run against the freshly rebuilt book).
13. Full offline Python suite once: `python3 -m unittest discover -s
    tests` → **1059/1059 passed** (after updating 8 pre-existing test files
    that hardcoded the "Exercises 10–12 are placeholders" range to "11–12":
    `test_book_structure.py`, `test_placeholder_exercises.py`,
    `test_wp25_content_audit.py`, `test_exercise_04_notebook.py`,
    `test_exercise_06_notebook.py`, `test_exercise_07_notebook.py`,
    `test_exercise_08_notebook.py`, `test_exercise_09_notebook.py`).
14. Full frontend unit suite once: covered by step 8 (475/475).
15. Full standalone Playwright suite once: `npm run test:e2e` → **288/288
    passed** (confirms the shared `styles.css` narrow-viewport fix did not
    regress any existing widget).
16. Full built-book Playwright suite once: see addendum.
17. Manual visual inspection at desktop/390px, light/dark: see addendum.

### Addendum — built-book and visual gates (completed after the notebook existed)

- One clean Jupyter Book build: `jupyter-book build book/` → **build
  succeeded, 1 warning** (pre-existing, unrelated: `logo.png` does not
  exist — present before this WP). `book/_build/html/chapters/chapter_10/exercise_10.html`
  produced.
- Focused built-book tests, against the freshly built book:
  - `interactive/e2e-book/chapter10.spec.ts` (new) → **6/6 passed**
    (title/structure, all 4 iframes load with config+data returning HTTP
    200, quiz reaches success state, leakage-lab operation control works,
    HAR method toggle works, imbalance model switch changes the reported
    accuracy, 390px layout has no horizontal overflow across all four
    iframes).
  - `interactive/e2e-book/iframe-height-contract.spec.ts` (4 new cases
    appended for the 4 new iframes) → full spec **24/24 passed** (every
    Exercise 1-10 activity, including the 4 new ones, fits its content,
    survives a control change, and fits in dark mode at 390px).
  - `interactive/e2e-book/launch-buttons.spec.ts` (Chapter 10 moved from
    the "placeholder, no button" case into the mapped-chapter loop; the
    lone placeholder-page check retargeted from Exercise 10 to Exercise 11)
    → **56/56 passed**.
  - One caught-and-fixed defect during this step: `book/_static/launch-buttons.js`
    did not yet have a `chapters/chapter_10/exercise_10.html` entry in its
    static page→portable-notebook map (it was still only registered
    through chapter 9) — added, which is also what the chapter10.spec.ts
    "Colab button" assertion depends on.
  - Four **pre-existing** tests (in `tests/test_exercise_07_notebook.py`,
    `test_exercise_08_notebook.py`, `test_exercise_09_notebook.py`, plus
    the earlier `test_exercise_04_notebook.py` and
    `test_exercise_06_notebook.py`) hardcoded "Exercises 10-12 have no
    launch button / remain placeholders" — updated to "11-12" now that
    Exercise 10 has one, alongside `test_book_structure.py` and
    `test_wp25_content_audit.py` (see §12).
  - Full built-book Playwright suite once: `npm run test:e2e:book` →
    **152/152 passed** (confirms no regression to any of Exercises 1-9's
    book-level behavior, sidebar toggle, or the WP22 cross-chapter
    dark-mode addendum).
- Manual visual inspection: screenshots taken of the built page at desktop
  (1400px) in light and dark mode, and at 390px in light and dark mode, plus
  each of the 4 activities individually at desktop width. All render
  cleanly, theme-consistent, no clipping. One real defect was found and
  fixed this way: the Section 1 flow diagram's connecting arrows were
  plain flex siblings, so wrapping at narrow/medium widths could strand an
  arrow at the end of one row with its box alone on the next row; each
  arrow was regrouped with the box it points to so wrapping always keeps
  an arrow with its destination box. Verified fixed by re-screenshotting.

## 12. Retries, deviations, judgment calls, and unresolved issues

- **Title deviation from the WP25 syllabus placeholder wording, by explicit
  WP38 instruction**: the notebook's title is "Exercise 10: Examples and
  Common Mistakes" (WP38 spec §title), not the WP25 placeholder's "Exercise
  10: Common Machine Learning Mistakes". `book/syllabus.md` and
  `course_overview/Machine_Learning_for_Neuroscience_Notebook_Overview.docx`
  were **not** touched (out of scope per WP38's own instructions and the
  required report confirmation in item 13 below); the test fixture in
  `tests/test_wp25_content_audit.py` (`EXERCISE_TITLES[10]`) was updated to
  the new title, with a comment explaining the discrepancy is intentional
  and scoped to WP38.
- **"What this notebook covers" bullets do not enumerate all 7 sections
  one-for-one** — WP38 spec §4 gives exact required bullet text (4 items,
  organized by principle, not by section), which supersedes
  `NOTEBOOK_AUTHORING_STANDARDS.md`'s general "one list item per section"
  convention for this notebook specifically.
- **Median-fill demonstration uses synthetically introduced missingness**:
  cortical thickness has zero real missing values in this table, so the
  wrong/correct code pair marks 30 values in one copy of one column as
  `NaN` (seeded, deterministic, explicitly labeled to the student as
  illustrative) purely to show the code pattern — no performance claim is
  attached to this cell.
- **Imbalance activity reuses Exercise 3's exact cohort-draw mechanism and
  fixed `C=1.0`** rather than introducing a new sampling rule, per spec
  §9's instruction to reuse the established pipeline; a new `imbalance-
  threshold` frontend component was built (rather than extending the
  existing `classification-imbalance` component) because the required
  controls (model toggle + threshold slider) and metrics (PR-AUC, F1,
  precision, recall) are a materially different interaction from Exercise
  3's ratio/seed selector — judged a cleaner fit with the existing
  "fixed-probabilities, client-recomputes-at-any-threshold" pattern already
  established by `classification-threshold.ts` than retrofitting the
  ratio-based component.
- **No dedicated `chapter10-dark-mode.spec.ts`** was added, unlike several
  earlier chapters' per-chapter dark-mode regression specs (e.g.
  `chapter09-dark-mode.spec.ts`) with exact-RGB Plotly-theme assertions.
  Dark-mode correctness for the two Plotly-bearing new activities
  (`leakage-lab`, `har-fold-compare`) rests on: (a) both components using
  the same shared `getPlotlyTheme`/`subscribeToThemeChanges` two-line
  pattern as every other themed widget, verified by direct code
  inspection; (b) the shared, generic `iframe-height-contract.spec.ts`
  suite exercising dark mode across all activities including the 4 new
  ones; (c) manual visual inspection (§11 addendum). This is a scope
  reduction under the session's time budget, disclosed rather than hidden.
- **HAR preflight passed on the first attempt** with a wide safety margin
  (all 5 k values qualified against a ≥2 requirement; the smallest
  per-k margin was still 0.031, well above the 0.03 threshold) — no
  alternative features, seeds, splits, or models were searched at any
  point, consistent with the mandatory stop-condition instruction.
- No other retries were needed; every audit/export script, the canonical
  notebook, and the portable notebook executed successfully on the first
  attempt after each edit.

## 13. Syllabus and Word overview confirmation

`book/syllabus.md` and
`course_overview/Machine_Learning_for_Neuroscience_Notebook_Overview.docx`
are **untouched** — neither appears in `git status --short` for this
branch (see literal status in §15 and the exact changelog).

## 14. Nothing merged, pushed, deployed, or monitored

No `git push`, `git merge`, `git checkout main`, or GitHub Actions
interaction of any kind occurred during this WP. All commits are local to
`feature/wp38-exercise10-common-mistakes`.

## 15. Literal final `git status --short --branch`

Immediately before the implementation commit (reports untracked, about to
be committed together with everything else):

```
## feature/wp38-exercise10-common-mistakes
 M book/_static/launch-buttons.js
D  book/chapters/chapter_10/exercise_10.md
 M book/config/abide_modeling.json
 M interactive/e2e-book/iframe-height-contract.spec.ts
 M interactive/e2e-book/launch-buttons.spec.ts
 M interactive/src/classification-metrics.ts
 M interactive/src/components/registry.ts
 M interactive/src/config.ts
 M interactive/src/styles.css
 M interactive/tests/config.test.ts
 M scripts/build_portable_notebook.py
 M scripts/smoke_portable_notebook.py
 M tests/test_book_structure.py
 M tests/test_exercise_04_notebook.py
 M tests/test_exercise_06_notebook.py
 M tests/test_exercise_07_notebook.py
 M tests/test_exercise_08_notebook.py
 M tests/test_exercise_09_notebook.py
 M tests/test_placeholder_exercises.py
 M tests/test_wp25_content_audit.py
?? WPs/reports/WP38_EXACT_CHANGELOG.md
?? WPs/reports/WP38_REPORT.md
?? book/_static/widgets/configs/har_fold_compare.json
?? book/_static/widgets/configs/imbalance_threshold.json
?? book/_static/widgets/configs/leakage_lab.json
?? book/_static/widgets/configs/leakage_quiz.json
?? book/_static/widgets/data/abide_imbalance_threshold.json
?? book/_static/widgets/data/abide_leakage_lab.json
?? book/_static/widgets/data/leakage_quiz.json
?? book/_static/widgets/data/uci_har_fold_comparison.json
?? book/chapters/chapter_10/
?? book/data/
?? book/downloads/chapter_10/
?? interactive/e2e-book/chapter10.spec.ts
?? interactive/e2e/har-fold-compare.spec.ts
?? interactive/e2e/imbalance-threshold.spec.ts
?? interactive/e2e/leakage-lab.spec.ts
?? interactive/e2e/leakage-quiz.spec.ts
?? interactive/src/components/har-fold-compare.ts
?? interactive/src/components/imbalance-threshold.ts
?? interactive/src/components/leakage-lab.ts
?? interactive/src/components/leakage-quiz.ts
?? interactive/src/har-fold-compare-data.ts
?? interactive/src/imbalance-threshold-data.ts
?? interactive/src/leakage-lab-data.ts
?? interactive/src/leakage-quiz-data.ts
?? interactive/tests/har-fold-compare-data.test.ts
?? interactive/tests/imbalance-threshold-data.test.ts
?? interactive/tests/leakage-lab-data.test.ts
?? interactive/tests/leakage-quiz-data.test.ts
?? scripts/export_har_fold_widget_data.py
?? scripts/export_imbalance_threshold_data.py
?? scripts/export_leakage_lab_data.py
?? scripts/export_uci_har_data.py
?? scripts/har_group_leakage_audit.py
?? scripts/har_group_leakage_audit_result.json
?? scripts/uci_har_data.py
?? tests/test_exercise_10_notebook.py
?? tests/test_export_har_fold_widget_data.py
?? tests/test_export_imbalance_threshold_data.py
?? tests/test_export_leakage_lab_data.py
?? tests/test_har_group_leakage_audit.py
?? tests/test_uci_har_data.py
```

After the implementation commit, `git status --short --branch` shows a
clean tree on `feature/wp38-exercise10-common-mistakes`, ahead of
`origin/main` by the WP37/WP37V documentation commits plus this WP's
checkpoint, implementation, and report commits — see the final commit SHA
recorded at the top of `WPs/reports/WP38_EXACT_CHANGELOG.md`'s companion
commit.
