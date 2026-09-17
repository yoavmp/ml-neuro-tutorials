# WP25 — Syllabus-aligned notebook restructure (Exercises 1–12)

## Purpose

Restructure the active book around the course's new syllabus numbering (the `תרגול`
column) while preserving the previous notebook arrangement, byte-for-byte, on a
dedicated archive branch. This is a structural move, not a content redesign: no model,
data, split, seed, feature set, or metric changes silently; any unavoidable numeric
change is measured and reported.

This WP is **local-only**: no reset/rebase/stash/merge/push/deploy/Actions monitoring,
and WP26 is not started.

---

## 0. Pre-flight (verified before writing this file)

```
git status --short --branch   -> ## edit/wp24-notebook-concision; only WP16/WP21 untracked reports
git branch --show-current      -> edit/wp24-notebook-concision
git rev-parse HEAD              -> 914841c4c6033f232d96ce33b6dbcc23eda1c766
git rev-parse origin/main       -> 4237ce7b3528526066bcda03e6e94545ca29ad14
```

Matches the expected starting state exactly (WP24 tip `914841c`, only
`WPs/reports/WP16_ARCHITECT_REPORT.md` and `WPs/reports/WP21_DEPLOYMENT_REPORT.md`
untracked). `NOTEBOOK_AUTHORING_STANDARDS.md`, `WP24`'s spec, and its report have been
read.

`archive/pre-syllabus-notebook-structure` was created pointing at `914841c` (verified
`git rev-parse` matches exactly) **before** any implementation edit, and carries no new
commits. Branch `edit/wp25-syllabus-restructure` was created from the same commit. This
file is committed alone as the checkpoint commit, before any implementation edit.

`WPs/reports/WP16_ARCHITECT_REPORT.md` and `WPs/reports/WP21_DEPLOYMENT_REPORT.md` are
left untouched throughout.

---

## 1. Repo investigation — findings that drive the plan below

### Current active structure

```
book/chapters/chapter_01/exercise_01.ipynb   "Exercise 1 — Exploratory data analysis (EDA)"  (73 cells)
book/chapters/chapter_02/exercise_02.ipynb   "Exercise 2: Regression"                          (29 cells)
book/chapters/chapter_03/exercise_03.ipynb   "Exercise 3: KNN and the Bias–Variance Tradeoff"  (31 cells)
book/chapters/chapter_04/exercise_04.ipynb   "Exercise 4: Classification with Logistic Regression" (32 cells)
```

`book/_toc.yml` lists `intro`, `syllabus`, `contents` (with the four chapters above as
sections), in that order. `book/syllabus.md` is a one-line stub (`# Syllabus`) — it is
**not** edited by this WP, only checked byte-for-byte unchanged.

### Exercise 3's existing section map (this is the pivot for §8 below)

1. Our data table (reloads the same table Exercise 2 already loaded)
2. One standard KNN regression workflow (fits one `KNeighborsRegressor` pipeline at
   `K_EXAMPLE = 20` on Exercise 2's own split/recipe; compares held-out R² against a
   freshly-refit linear-regression baseline)
3. Correct and misleading ways to evaluate a model (A/B/C resubstitution/leakage
   comparison for KNN, `knn_abc.json` widget)
4. The classic bias–variance tradeoff (conceptual, static illustration — no data
   dependency)
5. How performance changes across every k (splits Exercise 2's own `X_train`/`y_train`
   into a fitting/validation subset, computes an R²/MSE curve across every `k`)
6. Explore k yourself (`knn_explore.json` widget: k-slider, three deterministic
   alternative training samples, binned calibration)

Per the task prompt, **Sections 4–6** (the actual bias-variance material) transfer to
Exercise 2; **Sections 1–3** (data reload, the standalone KNN workflow, and the A/B/C
evaluation widget) are **not** part of the new active book and remain only on
`archive/pre-syllabus-notebook-structure`.

### Confirmed: Exercise 2 already has everything Sections 4–6 need

Exercise 3's Section 1 (data reload) and Section 2 (`FEATURES`, `X`, `y`, `groups`,
`X_train`/`X_test`/`y_train`/`y_test`) reproduce **the exact same recipe and the exact
same `random_state=42` stratified split** Exercise 2's own Section 2 already computes —
confirmed identical column list, identical `train_test_split` call signature, same
source table. So Sections 4–6, moved into Exercise 2, need **no reloaded data and no
re-split**: they reuse Exercise 2's existing `FEATURES`, `X`, `y`, `groups`, `X_train`,
`X_test`, `y_train`, `y_test` directly. This satisfies the instruction to "reuse
Exercise 2's existing data and variables wherever practical."

### Dependency actually needed: a KNN baseline fit (minimum necessary setup)

Sections 4–6 all refer back to "Section 2" for `K_EXAMPLE = 20` and a fitted KNN model
(`knn_model`, `test_r2`, `test_pred`) to compare against. That model itself lives in the
**discarded** Section 2, not Sections 4–6. Per the instruction to "reproduce only the
necessary setup inside Exercise 2, not the discarded teaching narrative": a short new
subsection is added introducing KNN regression and fitting one `KNeighborsRegressor`
pipeline at `K_EXAMPLE = 20` on Exercise 2's own `X_train`/`X_test`/`y_train`/`y_test`
(no reload, no re-split) — this is intentionally condensed relative to the discarded
Section 2 (no separate linear-regression re-comparison print, since Exercise 2 already
has that model a few cells above), producing the `knn_model`/`knn_test_r2`/`knn_test_mse`
that Sections 4–6's transferred material needs. Variables are renamed with a `knn_`
prefix (`knn_model`, `knn_pred`, `knn_test_r2`, `knn_test_mse`) so they cannot collide
with or be confused for the existing linear-regression `model`/`y_pred`/`test_r2`/
`test_mse` a few cells above.

**Numeric consequence to verify, not assume:** Exercise 3's original KNN fit used
`X_train`/`X_test` from its own re-derived split. Because that split is
computationally identical to Exercise 2's (same seed, same stratify array, same source
rows, same column order), refitting on Exercise 2's own arrays must reproduce the exact
same `held-out R² = 0.578`-class numbers Exercise 3 reported — verified numerically
during implementation (§14) rather than assumed; any mismatch is treated as a stop-and-
report condition, not silently accepted.

### Prose cross-references requiring adaptation (recorded exactly in the changelog)

Several sentences in the transferred/adjacent material name a "Section" or "Exercise"
number that shifts under the merge or the classification move. These are content-
neutral wording fixes (never a scientific-content change):

- Ex3 §4 bullet referencing "(Section 3 showed k = 1 reaching a perfect resubstitution
  score)" — Section 3 (the A/B/C widget) is discarded; reworded to state the general
  fact (training error keeps falling as flexibility increases, reaching a perfect score
  at k = 1) without pointing at a section that no longer exists in the active book.
- Ex3 §5 lead-in "the outer test set from Sections 2–3 is never touched here" —
  reworded to name the regression workflow generically ("the linear-regression and KNN
  test set above").
- Ex3 §6 and its "What this curve shows" admonition both say "the k = 20 worked-example
  value from Section 2" — Section 2 is now Linear Regression, not KNN; reworded to "the
  KNN worked example above."
- Ex3 "In summary": "the same workflow structure Exercise 2 used for linear regression"
  — now self-referential (both live in the same notebook); reworded to "the same
  workflow structure used above for linear regression."
- Ex4 (new Exercise 3): every "Exercises 2-3" / "Exercise 3" reference to the old
  regression+KNN pair is renumbered to the single merged "Exercise 2" (e.g. "Exercises
  2-3 used ABIDE's rich neuroimaging table" → "Exercise 2 used ABIDE's rich neuroimaging
  table"; "the same workflow structure Exercise 3 used for k" → "the same workflow
  structure Exercise 2 used for k"; "Exercises 2-3's comparison of correct and
  misleading evaluation methods, including resubstitution" → "Exercise 2's comparison of
  correct and misleading evaluation methods, including resubstitution", since that
  demonstration is Exercise 2's own Section 3, not the discarded KNN A/B/C widget).

None of these touch a model, dataset, split, seed, feature set, or metric — text only.

### Interactive widgets involved

- `knn_abc.json` / `interactive/src/components/knn-abc.ts` (or equivalent name) — **not
  moved**: belongs to discarded Section 3, stays only on the archive branch. Its frontend
  component, config, exported data, and any dedicated tests are removed from the active
  tree (§15) once confirmed archived.
- `knn_explore.json` / its component and exported data — **moved** conceptually to
  Exercise 2: config `title`/description updated to say "Exercise 2", iframe `src` paths
  in the merged notebook point at the same `../configs/knn_explore.json` relative path
  (chapter directory changes from `chapters/chapter_03/` to `chapters/chapter_02/`, so the
  relative `../../_static/...` prefix is unchanged, but the config's student-facing
  title/labels must say "Exercise 2" wherever they name the exercise).
- `regression_compare.json` and its component — already Exercise 2's; unaffected in
  route, only reordered to sit under the new `## Bonus` heading.
- `classification_threshold.json` and `classification_imbalance.json` and their
  components — move with the classification notebook from chapter_04 → chapter_03; every
  student-facing title/label naming "Exercise 4" is updated to "Exercise 3".
- Exact config/component/manifest/test file paths and every literal `chapter_03`/
  `chapter_04`/`exercise_03`/`exercise_04`/`Exercise 3`/`Exercise 4` occurrence are
  enumerated from a full-repo search performed during implementation and listed file-by-
  file in `WPs/reports/WP25_EXACT_CHANGELOG.md` — not guessed from memory.

### Portable notebooks and generator

`scripts/build_portable_notebook.py` maps each canonical notebook to a
`book/downloads/chapter_0N/exercise_0N_portable.ipynb` output and holds one
`_CHN_..._IFRAME_REPLACEMENT` constant per interactive activity, swapping each iframe for
a static blurb linking back to the live page. This WP:

- adds/updates the constants for Exercise 2's now-two widgets (`regression_compare`,
  `knn_explore`) at their new `chapter_02` download path;
- adds/updates the constants for Exercise 3's two widgets (`classification_threshold`,
  `classification_imbalance`) at their new `chapter_03` download path, renumbering every
  in-blurb "Exercise 4" reference to "Exercise 3";
- removes the old chapter_03 KNN-notebook entry and its `knn_abc`/standalone
  `knn_explore`-at-chapter_03 replacement constants (superseded — content now lives at
  chapter_02, or discarded with Section 3);
- does **not** add chapter_04–chapter_12 to the generator (§13: no portable notebooks for
  placeholders).

---

## 2. New notebook sequence (Exercises 1–12)

Built from the syllabus's `תרגול` column. Final-project reminders/comments in the
syllabus are excluded from every notebook and placeholder title. No Exercise 13 is
created. The Syllabus page's content is not edited; a regression test checks its source
file is byte-for-byte unchanged.

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

Title Case is used consistently across notebook title, Contents entry, sidebar entry,
browser title, portable notebook, download/Colab labels, widget titles that include the
exercise title, and metadata/manifests. Ordinary prose and sentence-style subheadings are
left alone.

---

## 3. Exercise 1 — unchanged

No content, section, activity, output, portable notebook, or calculation changes.
Confirmed unchanged in the report (diff against `archive/pre-syllabus-notebook-structure`
limited to navigation/title-capitalization, if any is even needed — Exercise 1's title
already reads "Exercise 1 — Exploratory data analysis (EDA)"; capitalization audit (§12)
covers whether the em-dash/EDA-parenthetical form needs to change to match the syllabus
title exactly, and if so that is the **only** permitted edit to this file).

---

## 4. Exercise 2 — rebuild (regression + transferred KNN bias-variance material)

Renamed to `Exercise 2: Regression and Bias-Variance Trade-Off`. One notebook, one title,
one "What this notebook covers", one run/download block, one imports/data-loading
sequence, one prerequisites statement, one conclusion, one portable-notebook
introduction — never two notebooks concatenated.

### 4.1 Final section order

1. **What this notebook covers** (rewritten to describe both the in-class
   linear-regression work and the at-home KNN/bias-variance practice, using language
   close to: *"In class, we will see how regression is performed in Python using linear
   regression tools from scikit-learn. At home, you will apply the same regression ideas
   with KNN and use it to explore the bias-variance trade-off."*)
2. **Our data table** (existing Exercise 2 §1, unchanged)
3. **Building one linear-regression workflow** (existing Exercise 2 §2, unchanged)
4. **Three ways to score the same model** (existing Exercise 2 §3, unchanged)
5. **Introducing KNN regression** (new, minimal — §1 above: one short conceptual
   paragraph, the `K_EXAMPLE = 20` framing, one fitted pipeline reusing Exercise 2's own
   `X_train`/`X_test`/`y_train`/`y_test`, one held-out R²/MSE print, one observed-vs-
   predicted plot mirroring Exercise 2's own — no re-derivation of data or split)
6. **The classic bias–variance tradeoff** (transferred Ex3 §4, conceptual illustration,
   cross-reference reworded per §1 above)
7. **How performance changes across every k** (transferred Ex3 §5, reusing Exercise 2's
   `X_train`/`y_train` for its internal fitting/validation re-split — unchanged
   computation)
8. **Explore k yourself** (transferred Ex3 §6, `knn_explore.json` widget, titles/labels
   updated to name Exercise 2)
9. **Bonus** (existing Exercise 2 §4 "Comparing feature sets" + §5 "What does sample size
   change?", moved to the end, one short sentence marking them optional/non-core)
10. **In summary** / **Questions to take away** (merged: the existing Exercise 2 summary
    plus the transferred KNN summary bullets and take-away questions, deduplicated so no
    concept or question repeats)

No cross-validation, parameter tuning, or "best k" selection is introduced anywhere in
this notebook (matches the existing WP19 removal and the explicit instruction here).

### 4.2 Bonus

```markdown
## Bonus
```
placed immediately after the KNN "Explore k yourself" section and before "In summary",
containing the existing feature-set-comparison and sample-size subsections exactly as
they are today (headings renumbered under the `## Bonus` parent), plus one short
student-facing sentence: these extend the main lesson and are not required for the core
session.

### 4.3 Interactive material moved

`knn_explore.json` (and its exported data/manifest entry) is updated so every
student-facing string names Exercise 2, not Exercise 3; the iframe in the merged notebook
points at the same relative config path from the new `chapters/chapter_02/` location.
`regression_compare.json` is unaffected in route (already Exercise 2's), only its
notebook position moves under Bonus. `knn_abc.json` and its component/tests/exported data
are **not** moved — they stay archived only, and are removed from the active tree once
confirmed superseded (§15).

---

## 5. Exercise 3 — rebuild (classification, moved wholesale from old Exercise 4)

The complete old Exercise 4 notebook moves to `book/chapters/chapter_03/exercise_03.ipynb`
(overwriting the old KNN notebook there, which is fully preserved on the archive branch)
and is renamed `Exercise 3: Classification and Metrics`. "What this notebook covers"
gains a concise line close to: *"In this exercise, we will work through a classification
pipeline using logistic regression and evaluate its predictions with classification
metrics."* All content, both interactive activities (`classification_threshold.json`,
`classification_imbalance.json`), and all metrics/plots/results are retained unchanged
except the section-cross-reference rewording in §1 above and every `chapter_04`/
`exercise_04`/"Exercise 4" occurrence renumbered to `chapter_03`/`exercise_03`/
"Exercise 3", across: notebook, Contents/sidebar/prev-next links, Colab and download
URLs, portable notebook + its generator entry, widget iframe `src` paths and configs,
exported widget data, frontend manifests/routes, tests, accessibility labels, and any
generated HTML references. No material removed by WP19/WP20/WP22/WP24 is reintroduced.

---

## 6. Exercises 4–12 — placeholder pages

`book/chapters/chapter_04/` through `chapter_12/`, one file per chapter, using the
simplest format the current Jupyter Book build supports cleanly for a static page
(Markdown, `exercise_0N.md`, following the repository's `chapter_0N/exercise_0N`
convention so `_toc.yml` entries need no special-casing). Each placeholder's entire
content:

```markdown
# Exercise N: <exact title>

Materials for this exercise will be added before the practice session.
```

No learning objectives, invented content, dates, final-project reminders, Colab/download
buttons, interactive placeholders, empty code cells, syllabus quotations, or section
outlines. Chapter_04's route now belongs to *Cross-Validation for Classification and
Regression*; the previous classification content that used to sit at chapter_04 lives
only at its new chapter_03 location and on the archive branch — chapter_04 never holds
classification content in the active tree at any point during this WP.

---

## 7. Contents, `_toc.yml`, and navigation

`book/_toc.yml`'s `contents` section is extended to list `chapters/chapter_01/exercise_01`
through `chapters/chapter_12/exercise_12` in order, `intro` and `syllabus` remaining
before `contents` exactly as today. No Exercise 13 entry. `book/syllabus.md` is not
edited; a focused test asserts its file hash/content is unchanged from the pre-WP25
commit. Any additional navigation cards/index (if the repo has one beyond `_toc.yml`
and `contents.md`) are updated the same way — confirmed during implementation by
inspecting the actual built sidebar, not assumed.

---

## 8. Capitalization audit

Title Case applied consistently to all twelve titles and their Contents/sidebar/browser-
title/portable-notebook/download-label/Colab-label/widget-title/metadata counterparts,
matching §2's table exactly, including the specific phrases called out in the task
prompt (`Regression and Bias-Variance Trade-Off`, `Classification and Metrics`,
`Cross-Validation for Classification and Regression`, `Regularization and Feature
Selection`, `Advanced Models and Model Comparison`, `Representational Similarity
Analysis`, `Exam-Style Questions`). Ordinary prose, code, and sentence-style subheadings
are left alone. Focused tests assert notebook title == Contents label == sidebar label
for every Exercise 1–12 page.

---

## 9. Portable notebooks

Regenerated via `scripts/build_portable_notebook.py --write` for chapters 1–3 only
(chapters 4–12 are placeholders with no portable notebook), then `--check` for
determinism. Exercise 2's portable notebook includes the transferred KNN material with
website-hidden reproduction code/outputs left visible, and the Bonus material clearly
marked. Exercise 3's portable notebook contains the moved classification lesson with
every "Exercise 4" reference renumbered. All Colab/download links point at the correct
new chapter path. No active portable notebook still names the classification notebook
"Exercise 4," exposes discarded Exercise 3 Sections 1–3, or runs against a website
widget.

---

## 10. Preserve functionality; remove stale copies

Model definitions, datasets, features, sample sizes, seeds, splits, metrics, saved
outputs, interactive defaults, responsive layout, light/dark behavior, Plotly theme sync,
and accessibility behavior are preserved throughout. Any numeric difference introduced by
reusing Exercise 2's arrays for the transferred KNN fit (§1 above) is measured and
reported, not silently accepted. After the archive branch is confirmed to hold the
previous versions, stale active copies — the old standalone KNN notebook content at
chapter_03 (superseded by classification), duplicate `knn_abc` assets, obsolete
chapter_04-as-classification references, old-numbering portable notebooks, unreachable
widget exports, and stale test expectations — are removed from the active tree so exactly
one authoritative version of each active exercise exists.

---

## 11. Tests

Focused regression tests are added/updated for at least the 20 items listed in the task
prompt (archive-branch SHA check; Exercise 1 unchanged; Exercise 2's title/transferred-
content/no-old-Ex3-Sections-1-3/single-opening-block/Bonus-ordering; Exercise 3's
title/content/numbering; Exercise 4-as-placeholder; Exercises 4–12 exist and build; no
Exercise 13; `_toc.yml`/Contents order; title/Contents/sidebar match; Syllabus unchanged;
no final-project reminder introduced; no duplicate active copies; portable-notebook
correctness; widget/manifest route validity). Exact new/updated test file names and
assertions are recorded in the report and changelog as implementation proceeds — not
pre-committed to a hypothetical file list here, since the existing test layout
(`tests/test_exercise_0N_notebook.py`, `tests/test_book_structure.py`,
`tests/test_notebook_corrections.py`, `interactive/tests/*.test.ts`) is the natural home
for most of them and is confirmed against the actual current test suite before editing.

---

## 12. Bounded validation

Run once, in order, with the one-retry-per-gate policy from the task prompt: focused
structural/notebook tests; portable-generator checks; smoke execution of the Exercise 2
and Exercise 3 portable notebooks; frontend typecheck; focused frontend tests for moved
widgets/manifests; one production frontend build; one Jupyter Book build; one full Python
test suite (numbering/navigation changed globally); one full frontend unit-test run
(manifests/chapter ownership changed); focused Playwright inspection of Exercise 1,
Exercise 2, Exercise 3, one middle placeholder, Exercise 12, Contents navigation, sidebar
order, previous/next links, Colab/download links for Exercises 2–3, transferred KNN
widgets, transferred classification widgets, and light/dark modes for moved interactive
figures. On a failing gate: one diagnosis/fix pass, one rerun; if still failing, stop and
report rather than loop. No GitHub Actions run.

---

## 13. Manual built-book verification

Per the task prompt's checklist in full — Exercise 1 unchanged, Exercise 2 reads as one
notebook, KNN precedes Bonus, Bonus clearly contains the feature-set/sample-size
extensions, Exercise 3 opens classification, Exercise 4 opens the cross-validation
placeholder, Exercises 5–12 open their placeholders, no Exercise 13, Contents/sidebar
agree, moved widgets load, no broken iframe path, no stale exercise number visible in
Exercise 2/3, placeholders show no nonfunctional Colab/download controls, Syllabus
unedited, no final-project comment anywhere in the new structure.

---

## 14. Documentation

`WPs/reports/WP25_REPORT.md` and `WPs/reports/WP25_EXACT_CHANGELOG.md` are produced per
the task prompt's required content lists, including the exact old-to-new mapping, exact
KNN sections transferred, dependency adaptations, final section orders, titles for
Exercises 1–12, every created/modified/moved/deleted file with a concise reason, test/
build results, any numeric changes (with numbers), and deviations.

---

## 15. Completion state

Implementation is committed, then the two reports are committed, on
`edit/wp25-syllabus-restructure`. `archive/pre-syllabus-notebook-structure` receives no
new commits. Nothing is merged, pushed, deployed, or monitored via Actions; WP26 is not
started.
