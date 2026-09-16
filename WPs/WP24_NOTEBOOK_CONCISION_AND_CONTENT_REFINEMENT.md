# WP24 — Notebook concision and content refinement (Exercises 1–4)

## Purpose

A bounded editorial and technical-cleanup pass across Exercises 1–4: fix duplicated
explanations, simplify "impute" jargon in Exercise 1, remove Spearman correlation from
Exercise 1 entirely, tighten Exercise 2 §5 and Exercise 4 §6 prose, mute the too-bright
yellow syntax-highlight color in dark mode, collapse redundant website-only reproduction
cells, and perform one bounded concision pass. This WP does not change any model, data,
split, seed, feature set, or metric.

This WP is **local-only**: no reset/rebase/stash/merge/push/deploy/Actions monitoring.

---

## 0. Pre-flight (already verified before writing this file)

```
git status --short --branch   -> ## main...origin/main [ahead 1]; only WP16/WP21 untracked reports
git rev-parse HEAD             -> c644933387e2117ed66b975ab7d476aef5d79802
git rev-parse origin/main      -> 4237ce7b3528526066bcda03e6e94545ca29ad14
```

Matches the expected starting state exactly. `NOTEBOOK_AUTHORING_STANDARDS.md` has been
read. Branch `edit/wp24-notebook-concision` created from this commit. This file is
committed alone as the checkpoint commit, before any implementation edit.

`WPs/reports/WP16_ARCHITECT_REPORT.md` and `WPs/reports/WP21_DEPLOYMENT_REPORT.md` are
left untouched throughout.

---

## 1. Repo investigation — findings that drive the plan below

### Exercise 1 (`book/chapters/chapter_01/exercise_01.ipynb`, 73 cells)

- "Our approach in this exercise" is cell 52 (end of §4, right before §5 starts at cell
  53). The retention activity is cells 34–36 (`### Design a complete-case dataset` →
  `### Complete-case retention explorer` iframe → `### Your decision`).
- All `imput*` occurrences: table row in cell 39; heading + prose in cell 43; variable
  names `imputation_demo`/`FIQ_imputed` and print text in cell 44; column label in cell
  45; dropdown in cell 46; prose in cell 47; variable reuse in cell 49; prose in cell 52.
- All `spearman` occurrences: opening list item 2; heading + table row in cell 67;
  worked comparison in cell 69; "Explore correlations yourself" prose in cell 70;
  synthesis-challenge step + a worked dropdown answer in cell 72. The correlation
  **widget** (`book/_static/widgets/configs/eda_correlation.json`, rendered by
  `interactive/src/components/correlation.ts`) has a live Pearson/Spearman `<select>`
  (`data-testid="correlation-method"`) backed by `spearman()`/`averageRanks()` in
  `interactive/src/correlation.ts`, a `CorrelationMethod` enum in `interactive/src/config.ts`,
  fixtures/tests in `interactive/tests/correlation.test.ts` and
  `interactive/e2e/correlation.spec.ts`, one selector interaction in
  `interactive/e2e-book/chapter01.spec.ts`, and prose in `interactive/README.md`. The
  static Pearson-only heatmap (cell 68) is unaffected — it never computed Spearman.
- Cell tags: only `hide-input`/`hide-output` exist; no `hide-cell` anywhere yet. Cell 11
  (head/tail/sample reproduction) is a legitimate first demonstration of a pandas method,
  explicitly framed by cell 10 as "here to show the code, not more result tables" and
  already `hide-output` — **left unchanged**. Cell 57 (histogram reproduction, `hide-input`)
  is explicitly introduced by cell 56 as reproducing "the same basic plot" — a genuine
  redundant-reproduction candidate for `hide-cell`.

### Exercise 2 (`book/chapters/chapter_02/exercise_02.ipynb`, 29 cells)

- The exploratory-comparison warning appears twice: once inside the notebook (cell 22,
  right after the §4 Think-first block, i.e. **after** the student has used the
  activity) and once inside the widget's own config
  (`book/_static/widgets/configs/regression_compare.json` → `selectionBiasNote`, rendered
  by `interactive/src/components/regression-compare.ts` **before/during** use). Keep the
  notebook occurrence (cell 22); remove the widget's `selectionBiasNote` (schema field in
  `interactive/src/config.ts`, JSON key, component rendering, `interactive/tests/config.test.ts`
  fixture).
- §5 (cell 23) is a 3-paragraph, ~230-word lead-in before the sample-size code (cells
  24–25). Per `scripts/sample_size_audit.py` (confirmed against
  `scripts/sample_size_audit_result.json`), the 10-feature sensorimotor bundle was **not**
  chosen by ranking features on correlation with age. It is one of four predeclared,
  literature-motivated candidate ROI bundles (bilateral, ≤12 columns each); each was
  scored with a training-partition-only linear-regression audit against a decision rule
  fixed in advance (n/p ratio, upward trend, narrowing spread, seed robustness, minimum
  final R²); the sensorimotor bundle was the first (in fixed preference order) to pass
  every check — never the best-scoring one. §5 and the later "What the learning curve
  shows" admonition (cell 26) will be substantially shortened while keeping this fact
  accurate. No feature/size/seed/calculation/figure changes.

### Exercise 4 (`book/chapters/chapter_04/exercise_04.ipynb`, 32 cells)

- The majority-baseline paragraph ("As class imbalance increases…") appears twice: once
  in the widget config (`book/_static/widgets/configs/classification_imbalance.json` →
  `imbalanceNote`, shown while/before using the activity) and once in notebook cell 28
  (shown after the iframe, cell 27). Keep the later, notebook occurrence; remove the
  widget's `imbalanceNote` (schema field, JSON key, component rendering).
- Two "Think first"/dropdown pairs in cell 28 nearly duplicate the widget's own
  `reflectionPrompts` (also in `classification_imbalance.json`, rendered as an in-widget
  "Reflect" list by `interactive/src/components/classification-imbalance.ts`). Per the
  instruction to prefer "the prompt attached to the interactive activity" (i.e. rendered
  inside the widget itself, answerable only after using the controls): remove cell 28's
  two Think-first/dropdown pairs from the canonical notebook, and keep/extend the
  widget's `reflectionPrompts` (add the new comparison question there, §4.3 below).
  Because the portable notebook replaces the iframe with a static blurb (no live widget,
  so no in-widget Reflect list), add an equivalent question directly into
  `_CH4_IMBALANCE_IFRAME_REPLACEMENT` in `scripts/build_portable_notebook.py` so the
  portable notebook keeps a reachable, equivalent prompt.
- No `hide-*` tags exist in this notebook except the data-loading cell (4). Cells 25
  (decision-threshold reproduction) and 29 (imbalance reproduction) are both explicitly
  introduced as reproducing the widget's own demonstration — both are `hide-cell`
  candidates.

### Cell-hiding mechanism (§7)

`book/_config.yml` sets no theme override, so Jupyter Book's default `sphinx-togglebutton`
behavior applies: `hide-input` = input collapsed/output shown, revealable; `hide-cell` =
input **and** output collapsed, still revealable (`NOTEBOOK_AUTHORING_STANDARDS.md` §2
already documents this); `remove-input`/`remove-cell` = deleted, not revealable — not used
anywhere and not to be introduced. `scripts/build_portable_notebook.py` already resets
every cell's metadata to `{}` when building the portable notebook and asserts
(`_assert_portable`) that no `HIDE_TAGS` survive — so adding `hide-cell` to canonical cells
requires **no** generator change; portable notebooks keep full visible code + output
automatically.

Candidates to convert/add `hide-cell` (all explicitly self-described as reproducing an
activity the student has already used, with no unique result):
- Exercise 1, cell 57 (histogram reproduction) — currently `hide-input`, upgrade to `hide-cell`.
- Exercise 4, cell 25 (decision-threshold reproduction) — currently untagged, add `hide-cell`.
- Exercise 4, cell 29 (class-imbalance reproduction) — currently untagged, add `hide-cell`.

Not converted (unique or teaching value, per the standards' exclusions):
- Exercise 1 cell 11 (head/tail/sample) — first demonstration of the methods; already hides only output.
- Exercise 1 cell 41 (`retention_comparison`) — a fixed illustrative example, not a reproduction of the reader's own tool choice.
- Exercise 2 cells 24–25 (learning curve) — a different question (sample size) the iframe does not show.

### Syntax-highlighting yellow (§5)

`book/_static/custom.css` carries no pygments token-class overrides today; the yellow
comes from the theme's default dark pygments style (`pygments.css`, a gitignored build
artifact) applying `#FFD900` to `.highlight .c1` (comment), `.nb` (builtin, incl. `print`),
and `.mi` (integer literal) under `html[data-theme="dark"]`. Light mode already uses
`#7F4707` for `.nb`/`.mi` and `#515151` for `.c1` — muted, not bright, and already ≥7:1
contrast against the light code background (`#f7f7fb`) — **no light-mode change needed**.
Measured: dark existing `#FFD900` vs. dark code background `#201e2b` = 11.84:1 (technically
compliant but perceptually harsh); candidate `#c7a86b` vs. the same background = 7.21:1
(muted, still comfortably ≥4.5:1). Fix: add three dark-mode-only overrides to
`book/_static/custom.css` for `.highlight .c1`, `.nb`, `.mi` at `#c7a86b`, right after the
existing `.cell_input div.highlight` rule. All three currently share one color already
(no existing separation to preserve among them); other token classes (keywords, function
names, strings) are untouched.

---

## 2. Exercise 1 edits

1. Move cell 52 ("Our approach in this exercise") to sit immediately before cell 34
   ("Design a complete-case dataset"), i.e. before the retention activity. Reword from a
   past/summary framing ("we will not immediately…") to a forward-looking decision frame
   that explicitly introduces the upcoming activity, and replace "impute"/"imputation"
   with plain language. Point 4 ("select variables according to the specific analysis")
   is rephrased to name the retention activity directly, removing the awkward forward
   reference this move would otherwise create.
2. Replace all Exercise 1 `imput*` occurrences (cells 39, 43 heading+prose, 44 code
   vars/prints, 45 column label, 46, 47, 49, and the moved block) with plain wording:
   "fill in missing values" / "filling in missing values" / "values filled in from other
   observations". Rename the section heading "Imputing a numerical variable" →
   "Filling in a numerical variable's missing values". Rename local variables
   `imputation_demo` → `filled_demo`, `FIQ_imputed` → `FIQ_filled`. No literal third-party
   API identifier (e.g. `.fillna`) needs renaming or explanation — `fillna` is already
   plain English.
3. Remove Spearman entirely from Exercise 1: notebook prose/heading/table/dropdown
   (cells 2, 67, 69, 70, 72); the widget's method selector, `spearman()`/`averageRanks()`
   maths, and `CorrelationMethod` type (`interactive/src/correlation.ts`,
   `interactive/src/components/correlation.ts`, `interactive/src/config.ts`); the config
   data (`book/_static/widgets/configs/eda_correlation.json`); the portable-notebook
   iframe-replacement text (`scripts/build_portable_notebook.py`); the unit/e2e tests
   (`interactive/tests/correlation.test.ts`, `interactive/e2e/correlation.spec.ts`,
   `interactive/e2e-book/chapter01.spec.ts`); `interactive/README.md`; and the Python
   structural test (`tests/test_notebook_corrections.py`). Rename the heading "Pearson and
   Spearman correlations" → "Pearson correlation between numerical variables". The widget
   keeps its variable/grouping selectors and states "Pearson correlation" in its label.
   `scripts/build_course_overview_docx.py` also names "Spearman correlations" in its
   Word-overview text; per the standing WP20 policy that the approved Word overview and
   its generator are not to be touched without a specific request, this one line is
   **left as a flagged, out-of-scope deviation** in the report rather than edited here.

---

## 3. Exercise 2 edits

1. Remove `selectionBiasNote` (schema, JSON, component rendering, test fixture) from the
   `regression-compare` widget; keep notebook cell 22's paragraph as the sole occurrence.
2. Shorten §5 (cell 23) to a short lead-in naming the accurate selection process (see §1
   above) plus one concise caution that the fixed feature set is a teaching demonstration,
   not a final estimate. Shorten cell 26 ("What the learning curve shows") to a concise
   statement that repeated resampling reduces the influence of one easy/hard draw. No
   change to `FEATURES_SS`, `SAMPLE_SIZE_ROIS`, sizes, seeds, the resampling loop, or the
   plot code (cells 24–25 untouched except cell 25's `hide-input` tag, unchanged).

---

## 4. Exercise 4 edits

1. Remove `imbalanceNote` (schema, JSON, component rendering) from the
   `classification-imbalance` widget; keep notebook cell 28's paragraph as the sole
   occurrence.
2. Remove cell 28's two "Think first"/dropdown pairs (duplicated by the widget's own
   Reflect list); keep the widget's `reflectionPrompts` as the single retained prompt
   set. Add an equivalent, reachable question to
   `_CH4_IMBALANCE_IFRAME_REPLACEMENT` in `scripts/build_portable_notebook.py` for the
   portable notebook, which has no live widget.
3. Add the polished comparison question to the widget's `reflectionPrompts` (third item):
   asks whether the model is actually better or worse than at 50:50, and what a reader
   might wrongly conclude from accuracy alone.

---

## 5. Dark-mode syntax color (see §1 findings)

Add to `book/_static/custom.css`, scoped `html[data-theme="dark"]`, for
`.highlight .c1`, `.highlight .nb`, `.highlight .mi`: `color: #c7a86b`. No light-mode
change (already compliant, not bright). Verify against one built-page screenshot per
mode after the Jupyter Book build (§9).

---

## 6. General concision pass

Bounded pass over Exercise 1–4 markdown and interactive instructions/config text:
shorten duplicated explanations, repeated browser-instruction phrasing, and long
cautions expressible in one sentence, per the WP prompt's priority list. Preserve
definitions, conceptual questions, interpretation guidance, and methodological cautions.
No new theory, CV, tuning, analyses, or learning objectives. Record before/after
student-facing Markdown word counts per notebook in the report.

---

## 7. Hide redundant reproduction cells

Add `hide-cell` to Exercise 1 cell 57 (upgrade from `hide-input`) and Exercise 4 cells 25
and 29 (currently untagged). No portable-generation change needed (confirmed in §1); the
portable notebooks already receive full visible code+output for these cells regardless
of website tags. Verify on the built book that each collapses fully by default with a
working reveal control, and that the corresponding portable notebook cell stays visible.

---

## 8. Durable authoring rules

Append a short new subsection to `NOTEBOOK_AUTHORING_STANDARDS.md` (not exercise-specific)
covering: prefer plain language over jargon when unnecessary; avoid repeating the same
warning/explanation around one activity; keep interactive instructions brief and
action-oriented; website notebooks may `hide-cell` a redundant Python reproduction of an
interactive figure; portable notebooks must keep such reproductions visible and runnable;
internal implementation notes must never reach student-facing material.

---

## 9. Regeneration and validation (bounded — one retry per gate, then stop and report)

1. `scripts/build_portable_notebook.py --write` (all four notebooks), then `--check` to
   confirm determinism.
2. `scripts/smoke_portable_notebook.py` for chapters 1, 2, 4 (execution smoke test).
3. Focused pytest: `tests/test_notebook_corrections.py`, `tests/test_build_portable_notebook.py`,
   `tests/test_sample_size_audit.py`, `tests/test_notebook_opening_structure.py`, plus any
   new/updated focused tests for this WP.
4. Focused vitest: `interactive/tests/correlation.test.ts`, `interactive/tests/correlation-data.test.ts`,
   `interactive/tests/config.test.ts`, `interactive/tests/regression-compare.test.ts`,
   `interactive/tests/classification-metrics.test.ts` (if touched).
5. `npm run typecheck` (interactive/) if TS changed.
6. One frontend production build (`npm run build` in `interactive/`) since component/config code changed.
7. One Jupyter Book build.
8. Focused Playwright against the built book (`interactive/e2e-book`, `--workers=1`) for
   chapter01/chapter02/chapter04 specs, plus one light+one dark screenshot/inspection each
   of: Ex1 missing-data section (moved decision block + retention activity), Ex1 Pearson
   activity, Ex2 feature comparison + sample-size section, Ex4 imbalance activity, a
   representative code block (comment + `print`), and one collapsed reproduction cell's
   reveal behavior.
9. Focused `interactive/e2e` Playwright specs for `correlation.spec.ts`,
   `regression-compare.spec.ts`, `classification-imbalance.spec.ts`.

Do not run the full suite unless a focused failure requires it. One diagnosis/fix pass
and one rerun per failing gate; stop and report if still failing.

---

## 10. Reports

Create `WPs/reports/WP24_REPORT.md` and `WPs/reports/WP24_EXACT_CHANGELOG.md` per the
required content list in the task prompt. Commit implementation + reports locally on
`edit/wp24-notebook-concision`. Do not merge, push, deploy, or start WP25.
