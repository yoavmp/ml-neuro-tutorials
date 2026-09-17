# WP25 Report — Syllabus-aligned notebook restructure (Exercises 1–12)

## Status: SUCCESS

All items in `WPs/WP25_SYLLABUS_ALIGNED_NOTEBOOK_RESTRUCTURE.md` were completed. Every
validation gate passed; one gate (a Playwright title assertion) needed one diagnosis/fix/
rerun cycle, matching the WP's bounded-validation allowance exactly. No merge, push,
deploy, or GitHub Actions run occurred. WP26 was not started.

- **Starting branch/SHA:** `edit/wp24-notebook-concision` @ `914841c4c6033f232d96ce33b6dbcc23eda1c766`
  (the WP24 tip) — matched the WP's expected starting state exactly (only
  `WPs/reports/WP16_ARCHITECT_REPORT.md` and `WPs/reports/WP21_DEPLOYMENT_REPORT.md`
  untracked).
- **Archive branch:** `archive/pre-syllabus-notebook-structure` @ `914841c4c6033f232d96ce33b6dbcc23eda1c766`
  — verified identical to the WP24 tip, no new commits added.
- **WP25 branch:** `edit/wp25-syllabus-restructure`
  - Checkpoint commit (spec only): `20f421f9f122426324853c0027ddc6b19ea96474`
  - **Implementation commit: `db4eda9797232b54f06ae7baec64f51927b5afea`**

---

## 1. Exact old-to-new notebook mapping

| Old location / title | New location / title | Disposition |
|---|---|---|
| `chapter_01/exercise_01.ipynb` — "Exercise 1 — Exploratory data analysis (EDA)" | `chapter_01/exercise_01.ipynb` — "Exercise 1: Exploratory Data Analysis" | **Title-only rename** (H1 line, plus the portable-notebook generator's `_CH1_BANNER` title line); all content, sections, activities, outputs, and calculations unchanged (see §7) |
| `chapter_02/exercise_02.ipynb` — "Exercise 2: Regression" | `chapter_02/exercise_02.ipynb` — "Exercise 2: Regression and Bias-Variance Trade-Off" | **Rebuilt**: original content kept, merged with old Exercise 3 Sections 4–6 (see §2) |
| `chapter_03/exercise_03.ipynb` — "Exercise 3: KNN and the Bias–Variance Tradeoff" (Sections 1–3) | *(discarded from the active tree)* | **Archived only** — preserved on `archive/pre-syllabus-notebook-structure`; not part of the new active book |
| `chapter_03/exercise_03.ipynb` Sections 4–6 (bias-variance tradeoff, all-k curve, explore-k widget) | `chapter_02/exercise_02.ipynb` Sections 5–7 | **Transferred** into the merged Exercise 2 (see §2) |
| `chapter_04/exercise_04.ipynb` — "Exercise 4: Classification with Logistic Regression" | `chapter_03/exercise_03.ipynb` — "Exercise 3: Classification and Metrics" | **Moved wholesale**, cross-references renumbered (see §5) |
| *(did not exist)* | `chapter_04/exercise_04.md` … `chapter_12/exercise_12.md` | **Created** as minimal placeholder pages (see §6) |

---

## 2. Exact KNN sections transferred (old Exercise 3 → new Exercise 2)

Transferred verbatim, only cross-reference wording adjusted (never scientific content):

- **Old Section 4 "The classic bias–variance tradeoff"** → new **Section 5**. The
  conceptual illustration code (synthetic curves, no data dependency) is byte-identical.
  One sentence was reworded because it referenced the discarded old Section 3 (the A/B/C
  widget): "training error alone keeps falling as flexibility increases (Section 3
  showed `k = 1` reaching a perfect resubstitution score)" → "training error alone keeps
  falling as flexibility increases — pushed to its limit, a model can fit training data
  perfectly by memorising it". A forward reference "Sections 5 and 6" → "Sections 6 and
  7" (renumbered).
- **Old Section 5 "How performance changes across every k"** → new **Section 6**. All
  four code cells (fit/validation split, the sort-distances-once cumulative-mean trick,
  the `k = N_fit` endpoint check, the two-panel plot) are byte-identical. One markdown
  cross-reference fixed ("the outer test set from Sections 2–3 is never touched here" →
  "the outer test set used in Sections 2-4 above"); one forward reference renumbered
  ("Section 6 reuses" → "Section 7 reuses").
- **Old Section 6 "Explore k yourself"** → new **Section 7**. The iframe cell is
  byte-identical (same `../configs/knn_explore.json` relative path — same directory
  depth from `chapters/chapter_02/` as from `chapters/chapter_03/`). Two cross-references
  to "Section 5"/"Section 2" (old numbering, meaning the discarded standalone KNN
  workflow) reworded to "Section 6" and "the KNN worked example above" respectively,
  since "Section 2" now means linear regression in the merged notebook.

**Not transferred** (discarded, archived only): old Sections 1–3 — the data-reload
preamble, the standalone "One standard KNN regression workflow" (its own `K_EXAMPLE = 20`
fit, plotted, and manually re-compared against a freshly-refit linear regression), and
"Correct and misleading ways to evaluate a model" (the `knn_abc.json` honest-vs-invalid
A/B/C widget).

---

## 3. Dependencies adapted from old Exercise 3 Sections 1–3

Investigation confirmed old Exercise 3's Section 1 (data reload) and Section 2 (`FEATURES`,
`X`, `y`, `groups`, and the `train_test_split(..., random_state=42, stratify=groups)` call)
reproduced **the exact same recipe and split** Exercise 2's own Section 2 already
computes — verified identical column list, identical call signature, same source table.
So the transferred Sections 5–7 needed **no reloaded data and no re-split**; only two
genuinely new pieces of setup were required, both minimal:

1. **A KNN baseline fit** (new Section 4, "Introducing KNN regression") — old Exercise 3's
   own Section 2 fit and plotted `K_EXAMPLE = 20` and printed a linear-regression
   re-comparison; that section itself is discarded, but Sections 5–7 all reference "the
   worked-example k = 20" and a fitted KNN model. A condensed replacement was added:
   one short KNN-concept paragraph, the `K_EXAMPLE = 20` framing (identical wording
   pattern to Exercise 2's own `C_EXAMPLE`-style framing), and one fit/plot cell reusing
   Exercise 2's **existing** `X_train`/`X_test`/`y_train`/`y_test` — no reload, no re-split,
   no re-fit of linear regression for comparison (Exercise 2 already has `test_r2` a few
   cells above; the new cell prints it directly instead of refitting). Variables use a
   `knn_` prefix (`knn_model`, `knn_pred`, `knn_test_r2`, `knn_test_mse`) so they cannot
   collide with the existing linear-regression variables.
2. **`groups_train`/`groups_test`** — the transferred Section 6 (dev-curve) needs
   `groups_train` to stratify its internal fitting/validation split
   (`train_test_split(X_train, y_train, ..., stratify=groups_train)`). Exercise 2's own
   split only unpacked `X_train, X_test, y_train, y_test`. **Adaptation:** Exercise 2's
   existing `train_test_split` call (Section 2) was extended to also unpack
   `groups_train, groups_test`, by passing `groups` as a third array into the same split
   call. This does not change `X_train`/`X_test`/`y_train`/`y_test` at all — passing an
   additional array into `train_test_split` alongside the same `random_state`/`stratify`
   only returns that array's own matching partition, it does not alter how the other
   arrays are split. **Verified numerically**: `X_train`/`y_train` before and after this
   change produce identical held-out results in both cells that depend on them (§9 below).
3. **One import added**: `from sklearn.neighbors import KNeighborsRegressor` and
   `import time` (used by the dev-curve's timing print) added to Exercise 2's single,
   already-existing imports/data-loading cell — no new loading cell created.

No discarded teaching narrative (the old Section 1–3 prose, the standalone A/B/C widget,
or its explanatory text) was reproduced.

---

## 4. Final Exercise 2 section order

1. **Our data table** (unchanged)
2. **Building one linear-regression workflow** (unchanged)
3. **Three ways to score the same model** (unchanged)
4. **Introducing KNN regression** (new — minimal setup, see §3.1)
5. **The classic bias–variance tradeoff** (transferred, old §4)
6. **How performance changes across every k** (transferred, old §5)
7. **Explore k yourself** (transferred, old §6 — `knn_explore.json` widget)
8. **Bonus** (see §5 below — not a numbered `## N.` section)
9. **In summary** / **Questions to take away** (merged, deduplicated, renumbered 1–15)

The opening "What this notebook covers" numbered list has exactly 7 items, matching the 7
numbered `## N.` sections (per `NOTEBOOK_AUTHORING_STANDARDS.md` §3), and includes the
task-required framing: *"In class, we will see how regression is performed in Python
using linear-regression tools from `scikit-learn`. At home, you will apply the same
regression ideas with k-nearest neighbours (KNN) and use it to explore the bias-variance
tradeoff."*

One title, one run/download block, one imports/data-loading sequence, one prerequisites
line, one conclusion — verified by a dedicated regression test
(`test_opening_appears_exactly_once`).

---

## 5. Final Bonus contents

`## Bonus` sits immediately after Section 7 and before "## In summary", containing:

- one short student-facing sentence: *"The two activities below extend the main lesson
  with two further, optional explorations of linear regression — they are not required
  for the core session."*
- `### Comparing feature sets` (was `## 4.` in the old Exercise 2 — the
  `regression_compare.json` widget) — content, activity, and results unchanged.
- `### What does sample size change?` (was `## 5.` in the old Exercise 2 — the
  sample-size learning-curve section) — content, `SAMPLE_SIZE_ROIS`, `sizes`, `n_rep`,
  seed, and plot unchanged.

Both were demoted from top-level numbered sections to `###` subsections under `## Bonus`
— confirmed by a dedicated regression test asserting neither old heading string
(`## 4. Comparing feature sets`, `## 5. What does sample size change?`) survives.

---

## 6. Final Exercise 3 mapping

The complete old Exercise 4 notebook (32 cells, all six of its own numbered sections
unchanged: 1–6 stay 1–6) moved verbatim to `chapter_03/exercise_03.ipynb`, renamed
"Exercise 3: Classification and Metrics". Every cross-reference to the old regression+KNN
pair was renumbered to the single merged Exercise 2:

- "This is Exercise 4 of…Exercises 2-3 used ABIDE's rich neuroimaging table…" →
  "This is Exercise 3 of…In this exercise, we will work through a classification
  pipeline using logistic regression and evaluate its predictions with classification
  metrics.…Exercise 2 used ABIDE's rich neuroimaging table…" (task-required concise
  wording added).
- "(Exercises 2-3's comparison of correct and misleading evaluation methods…)" →
  "(Exercise 2's comparison of correct and misleading evaluation methods…)" — this now
  correctly points at Exercise 2's own Section 3 resubstitution/leakage table, not the
  discarded KNN A/B/C widget.
- Every other "Exercises 2-3"/"Exercise 2-3" occurrence (Sections 1, 3, 6-dropdown, and
  the "Predictors" sentence in Section 3) → "Exercise 2".
- "the same workflow structure Exercise 3 used for `k`" (In summary) → "…Exercise 2 used
  for `k`" (KNN now lives in Exercise 2).
- Colab/raw-download URLs, `_toc.yml`, portable-notebook path, generator entry, widget
  configs, exported data, e2e specs, and every Python test path: `chapter_04`/
  `exercise_04` → `chapter_03`/`exercise_03` throughout.

No material removed by WP19/WP20/WP22/WP24 was reintroduced — the notebook's numbered
sections, hide-tags, and executed outputs are otherwise byte-identical to the pre-WP25
version (diff limited to the renumbering strings above).

---

## 7. Exercise 1 — confirmed unchanged

Per the task's explicit exception, the **only** edit made to Exercise 1 was the H1 title,
for capitalization/wording consistency with the syllabus's exact title list:

```
# Exercise 1 — Exploratory data analysis (EDA)
```
→
```
# Exercise 1: Exploratory Data Analysis
```

No section, activity, output, calculation, or portable-notebook content changed — the
notebook's portable version was regenerated only to reflect this same title-only change
in the generator's `_CH1_BANNER` constant (`git diff` on both files is limited to the
title line and the generator constant). `git diff --numstat` confirms
`book/chapters/chapter_01/exercise_01.ipynb`: 41 insertions / 41 deletions — the
symmetric line-count change expected from a JSON pretty-print of a single string field
changing, not a content edit (verified: `test_exercise_1_loading_cells_are_visible` and
the rest of `test_notebook_opening_structure.py`/`test_notebook_corrections.py` still
pass unchanged, confirming structure and tags are untouched).

---

## 8. Titles for Exercises 1–12

| # | Title |
|---|---|
| 1 | Exercise 1: Exploratory Data Analysis |
| 2 | Exercise 2: Regression and Bias-Variance Trade-Off |
| 3 | Exercise 3: Classification and Metrics |
| 4 | Exercise 4: Cross-Validation for Classification and Regression |
| 5 | Exercise 5: Regularization and Feature Selection |
| 6 | Exercise 6: Decision Trees |
| 7 | Exercise 7: Trees and Boosting |
| 8 | Exercise 8: PCA and Clustering |
| 9 | Exercise 9: Advanced Models and Model Comparison |
| 10 | Exercise 10: Common Machine Learning Mistakes |
| 11 | Exercise 11: Embeddings and Representational Similarity Analysis |
| 12 | Exercise 12: Review and Exam-Style Questions |

Verified matching across notebook H1 / Contents entry / sidebar entry (they all derive
from the same page source since neither `_toc.yml` nor any page carries a separate
`title:` override — confirmed by inspection) by `tests/test_wp25_content_audit.py` and by
a live Playwright check of the built sidebar (§13).

---

## 9. Files created for placeholder pages

```
book/chapters/chapter_04/exercise_04.md
book/chapters/chapter_05/exercise_05.md
book/chapters/chapter_06/exercise_06.md
book/chapters/chapter_07/exercise_07.md
book/chapters/chapter_08/exercise_08.md
book/chapters/chapter_09/exercise_09.md
book/chapters/chapter_10/exercise_10.md
book/chapters/chapter_11/exercise_11.md
book/chapters/chapter_12/exercise_12.md
```

Minimal Markdown (the simplest format Jupyter Book supports for a static page; the
existing `chapter_0N/exercise_0N` `_toc.yml` convention needs no special-casing for a
`.md` vs `.ipynb` target). Each file's entire content is exactly:

```markdown
# Exercise N: <exact title>

Materials for this exercise will be added before the practice session.
```

No learning objectives, dates, final-project reminders, Colab/download buttons,
interactive placeholders, empty code cells, syllabus quotations, or section outlines —
confirmed by `tests/test_placeholder_exercises.py`.

---

## 10. Confirmations

- **No final-project comment introduced**: `tests/test_wp25_content_audit.py`'s
  `NoFinalProjectReferences` class scans every Exercise 1–12 page and both active
  portable notebooks for "final project"/"final-project"/"capstone" — zero hits.
- **Syllabus page unchanged**: `book/syllabus.md` is still exactly `# Syllabus`, verified
  byte-for-byte against both the WP24 tip and the archive branch by
  `tests/test_wp25_content_audit.py::SyllabusPageUnchangedTests` (a `git show` comparison,
  not a hand-typed hash). The Syllabus page's own content was never opened for editing.
- **Exercise 1 content unchanged**: confirmed in §7 above.

---

## 11. Portable-notebook regeneration

`scripts/build_portable_notebook.py --write --notebook all` (now covering only
`chapter_01`, `chapter_02`, `chapter_03` — `chapter_04` was removed from the generator's
`NOTEBOOKS` mapping since placeholder Exercises 4–12 have no portable notebook), then
`--check --notebook all` — all three report "up to date" (deterministic, confirmed twice
across the session including after a later doc-only regeneration of `knn_explore`'s data
manifest).

- **Exercise 2's portable notebook** (46 cells) includes the transferred KNN Sections
  5–7, keeps the website-hidden reproduction/plot cells visible with their outputs (the
  generator's `_assert_portable` already strips all `hide-*` tags for every notebook, no
  generator change was needed for this), places the feature-set/sample-size material
  under `### Comparing feature sets`/`### What does sample size change?` following the
  canonical notebook's own Bonus structure, and its `regression_compare` **and** newly
  added `knn_explore` iframes both resolve to static "explore on the course website"
  blurbs linking to `chapters/chapter_02/exercise_02.html`.
- **Exercise 3's portable notebook** (34 cells) contains the moved classification
  lesson; its `colab_title` is now "Exercise 3: Classification and Metrics"; both
  `classification_threshold`/`classification_imbalance` iframe replacements were renamed
  from `_CH4_*` to `_CH3_*` constants and reworded from "Exercise 4 page" to "Exercise 3
  page", pointing at `chapters/chapter_03/exercise_03.html`.
- `book/downloads/chapter_04/` was **removed** (no portable notebook for a placeholder).
- No portable notebook still names the classification lesson "Exercise 4"; no active
  portable notebook exposes discarded old-Exercise-3 Sections 1–3 or the `knn_abc`
  widget (both verified by `grep`, by the dedicated `test_wp25_content_audit.py` checks,
  and by the full `test_notebook_opening_structure.py`/`test_wp19_content_audit.py`/
  `test_wp24_content_audit.py` suites).

---

## 12. Widget / manifest / path changes

- **`knn_explore.json`**: `description` and `curseOfDimensionalityNote` reworded from
  "Course activity for Exercise 3"/"Exercise 2's own worked example" to "Course activity
  for Exercise 2"/"the worked example above" (now a self-reference, since the widget
  lives inside Exercise 2 itself). Iframe relative path unchanged (`../configs/
  knn_explore.json` from `chapters/chapter_02/`, same directory depth as before).
- **`classification_threshold.json`** / **`classification_imbalance.json`**:
  `description` reworded "Course activity for Exercise 4" → "Course activity for
  Exercise 3"; `classification_threshold.json`'s self-reference "Exercise 4's own
  fixed…test-set predicted probabilities" → "this notebook's own fixed…" (again now a
  self-reference).
- **`interactive/src/components/knn-explore.ts`**: one runtime-visible DOM string
  rewritten — "both drawn from Exercise 2's own {N}-participant training partition…the
  same as Exercise 2's own recipe" → "both drawn from the {N}-participant training
  partition used above…the same as the recipe used above" (was a cross-reference to
  Exercise 2 from outside it; now self-referential).
- **`knn_abc` widget removed end to end** (discarded content, archived only):
  `book/_static/widgets/configs/knn_abc.json`,
  `book/_static/widgets/data/abide_knn_abc{.bin,_manifest.json}`,
  `interactive/src/components/knn-abc.ts`, `interactive/src/knn-abc-data.ts`,
  `interactive/tests/knn-abc-data.test.ts`, `interactive/e2e/knn-abc.spec.ts`,
  `scripts/export_knn_abc_data.py`, `tests/test_export_knn_abc_data.py`; deregistered
  from `interactive/src/components/registry.ts` and `interactive/src/config.ts`'s
  discriminated union; removed from `interactive/e2e/plot-visual-policy.spec.ts`'s
  shared-policy table and from `interactive/e2e-book/chapter03.spec.ts`/
  `wp22-cross-chapter-dark-mode.spec.ts`.
- **`book/_static/launch-buttons.js`**: `PAGE_TO_PORTABLE` no longer maps
  `chapters/chapter_04/exercise_04.html` (placeholder, no portable notebook).
- **`book/_toc.yml`**: extended with `chapters/chapter_05/exercise_05` through
  `chapters/chapter_12/exercise_12`.
- **`book/config/abide_modeling.json`**, **`scripts/knn_model_audit.py`**,
  **`scripts/classification_model_audit.py`**, **`scripts/export_regression_catalog.py`**,
  **`scripts/export_knn_explore_data.py`**, **`scripts/export_classification_threshold_
  data.py`**, **`scripts/export_classification_imbalance_data.py`**,
  **`book/_static/activity-resize.js`**: docstring/comment/note-field "Exercise 3"/
  "Exercise 4" cross-references updated to "Exercise 2"/"Exercise 3" for accuracy (none
  are student-facing; all are internal documentation). `scripts/sample_size_audit_result.
  json` and `book/_static/widgets/data/abide_knn_explore_manifest.json` were
  **regenerated** (via `sample_size_audit.py --run` and `export_knn_explore_data.py
  --refresh`) purely to pick up the corrected `abide_modeling.json` note text — confirmed
  via `git diff` that only that one string changed in each file, and the KNN manifest's
  binary payload SHA-256 (`4ded3bba…`) is unchanged, confirming zero numeric drift.

---

## 13. Tests and builds run, with results

Bounded validation, in order, one retry per failing gate:

1. **Focused structural/notebook tests** — `tests/test_exercise_02_notebook.py` (39,
   rewritten), `tests/test_exercise_03_notebook.py` (36, rewritten),
   `tests/test_placeholder_exercises.py` (6, new), `tests/test_wp25_content_audit.py`
   (15, new), `tests/test_book_structure.py` (9, updated),
   `tests/test_notebook_opening_structure.py` (9, updated),
   `tests/test_wp19_content_audit.py` (updated paths/indices),
   `tests/test_wp24_content_audit.py` (updated paths/heading) — **all pass**.
2. **Portable-generator checks** — `--write`/`--check --notebook all` — up to date,
   deterministic (§11).
3. **Smoke execution, Exercise 2 portable** — `OK [chapter_02]: portable notebook
   executed cleanly (19 code cells, key values matched)`.
4. **Smoke execution, Exercise 3 portable** — `OK [chapter_03]: portable notebook
   executed cleanly (13 code cells, key values matched)`.
5. **Frontend typecheck** (`npm run typecheck`) — clean.
6. **Focused frontend tests** — `interactive/tests/config.test.ts` (70, knn-abc fixture
   removed), `knn-explore.test.ts`/`knn-explore-data.test.ts` (unaffected, still pass) —
   all pass.
7. **One production frontend build** (`npm run build`) — succeeded (pre-existing chunk-
   size warning only, unrelated).
8. **One Jupyter Book build** (`jupyter-book build book`) — succeeded, 2 pre-existing
   warnings (`logo.png` missing, `README.md` not in a toctree) — same baseline as WP24,
   nothing new.
9. **One full Python test suite** (`python -m unittest discover -s tests -p 'test_*.py'`)
   — **443 passed, 11 skipped** (pre-existing network-dependent skips), **0 failed**.
10. **One full frontend unit-test run** (`npx vitest run`) — **294 passed**, 20 files
    (down from 21 — `knn-abc-data.test.ts` removed).
11. **Focused Playwright inspection**:
    - Book-level (`playwright.book.config.ts`, `--workers=1`): `chapter01.spec.ts`
      (12), `chapter02.spec.ts` (7, now including the transferred KNN block),
      `chapter03.spec.ts` (11, now the classification content moved from chapter04),
      `chapter04.spec.ts` (2, new placeholder spec) — **one initial failure**: the theme's
      own permalink anchor (`#`) inside the `<h1>` broke an exact-text-match assertion in
      the new placeholder spec; fixed in one pass (strip the anchor before comparing) and
      reran — passed. `chapter01-dark-mode.spec.ts` (2), `chapter02-visual-policy.spec.ts`
      (12), `launch-buttons.spec.ts` (11, chapter_04 mapping removed, two placeholder-page
      checks added), `sidebar-toggle.spec.ts` (4), `wp22-cross-chapter-dark-mode.spec.ts`
      (2, KNN dark-mode check folded into the Exercise 2 test, classification renamed to
      Exercise 3) — **all pass** (73 total across these runs).
    - Widget-level (`playwright.config.ts`): `regression-compare.spec.ts` (10),
      `classification-imbalance.spec.ts` (12), `classification-threshold.spec.ts` (18),
      `knn-explore.spec.ts` (24), `plot-visual-policy.spec.ts` (8, knn-abc entries
      removed) — **72 passed**.
    - Manual verification: sidebar/nav order confirmed live via a scripted Playwright
      check — `Introduction, Syllabus, Contents, Exercise 1…Exercise 12` in exact order,
      no Exercise 13; a middle placeholder (`chapter_08`) opens with the correct title
      and placeholder sentence; `chapter_12` opens with its correct title; the built HTML
      confirms no `knn_abc` reference anywhere in Exercise 2/3; the only "Exercise N"
      strings appearing outside each page's own content are the theme's own
      previous/next navigation footer links (expected, not stale content).

No GitHub Actions run.

---

## 14. Numerical output changes

**None.** Every metric the transferred/moved material reports is bit-for-bit identical to
its pre-WP25 value, verified by direct re-execution:

- Linear regression held-out R² = **0.469** (Exercise 2, unchanged).
- KNN (k=20) held-out R² = **0.664** (now in Exercise 2 — matches the value the old,
  now-archived Exercise 3 reported for the identical fit, confirming the split-reuse
  adaptation in §3 introduced no drift).
- Dev-curve: N_fit=564, N_val=189, fitting-set mean=15.192373 (unchanged).
- Classification (Exercise 3, moved from Exercise 4): accuracy=0.546, AUC=0.569,
  imbalance cohort 400 participants (360 control/40 autism) — all unchanged.
- `abide_knn_explore_manifest.json`'s regenerated binary payload SHA-256 is unchanged
  from before regeneration, confirming the doc-only manifest-note fix in §12 touched no
  numbers.

---

## 15. Deviations and unresolved issues

- **`scripts/build_course_overview_docx.py`** and `course_overview/Machine_Learning_
  for_Neuroscience_Notebook_Overview.docx` still describe the pre-WP25 exercise
  numbering (Exercise 3 = KNN, Exercise 4 = classification, no Exercises 5–12) — **left
  untouched**, per the explicit task instruction in §5 ("Do not update the Word
  course-overview document or its generator in this WP"). This is now materially more
  stale than the WP24 flag (a full renumbering, not one wording line) — flagging for a
  future WP's attention, not fixing unilaterally. `tests/test_course_overview_docx.py`
  was left as-is and still passes (it only tests the generator's own pre-WP25 behavior).
- One Playwright title-assertion failure (theme permalink anchor) was diagnosed and
  fixed within the WP's one-retry allowance — see §13 item 11. No unresolved failures.
- No other deviations. Every item in the WP was completed as specified.

---

## 16. Final state

```
$ git status --short --branch
## edit/wp25-syllabus-restructure
?? WPs/reports/WP16_ARCHITECT_REPORT.md
?? WPs/reports/WP21_DEPLOYMENT_REPORT.md
```

(as of writing this report, before the two WP25 report files themselves are committed in
the following commit). Local build/inspection artifacts (`book/_build/`,
`book/_static/widgets/app/`, `interactive/test-results/`) are gitignored and were not
committed. `archive/pre-syllabus-notebook-structure` carries no new commits. Nothing was
merged, pushed, deployed, or monitored via GitHub Actions. WP26 was not started.
