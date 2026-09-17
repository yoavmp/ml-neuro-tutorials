# WP24 Report — Notebook concision and content refinement

## Status: SUCCESS

All items in `WPs/WP24_NOTEBOOK_CONCISION_AND_CONTENT_REFINEMENT.md` were completed. Every
validation gate in §9 passed on the first attempt; no diagnosis/fix/rerun cycle was needed.
No merge, push, deploy, or GitHub Actions run occurred. WP25 was not started.

- Branch: `edit/wp24-notebook-concision`
- Checkpoint commit (spec only): `205d53f`
- **Implementation commit: `2e5eb52e74b130cc6f279c9b3063abebbb2d1abf`**
- Starting point: local `main` `c644933387e2117ed66b975ab7d476aef5d79802`, one
  documentation-only commit ahead of `origin/main` `4237ce7b3528526066bcda03e6e94545ca29ad14`
  — matched the WP's expected starting state exactly.

---

## 1. Exercise 1 — decision block move, plain language, Spearman removal

### 1.1 Decision-block move (§2.1)

"### Our approach in this exercise" moved from cell 52 (end of §4, immediately before §5)
to immediately before `### Design a complete-case dataset` (previously cell 34), i.e.
directly ahead of the `### Complete-case retention explorer` interactive activity.
Reworded from a past/summary framing to a forward-looking decision frame, and point 4
now names the retention activity explicitly ("use the retention explorer below to choose
variables for a specific analysis") so the block introduces the decision rather than
half-summarizing an activity the student hasn't reached yet. No content was duplicated by
the move — the block is fully self-contained and was not present elsewhere in the notebook.

### 1.2 "impute" → plain language (§2.2)

Every case-insensitive `imput*` occurrence in Exercise 1 was replaced. Exact sections
changed:

- Heading: **"Imputing a numerical variable"** → **"Filling in a numerical variable's
  missing values"**.
- Table row (§4, "Ways to handle missing data"): "**Impute** the missing values — simple
  (mean / median / mode), model-based (e.g. KNN), or multiple imputation" →
  "**Fill in** the missing values — a simple estimate (mean / median / mode), a
  model-based estimate (e.g. KNN), or a more advanced technique that fills in values
  multiple times to capture uncertainty."
- Local variable names (student-visible in code): `imputation_demo` → `filled_demo`,
  `FIQ_imputed` → `FIQ_filled` (three code cells).
- Print/table text: "Median FIQ used for imputation" → "Median FIQ used to fill in
  missing values"; "Number of imputed observations" → "Number of values filled in";
  "Median-imputed FIQ" column label → "FIQ with missing values filled in".
- Dropdown "Important limitation" and the following paragraph: "Median imputation
  solves…" → "Filling in with the median solves…"; "Imputing 99 of 1,114…" → "Filling in
  99 of 1,114… with the median…".
- The moved decision block itself (§1.1 above): "impute or delete" → "fill in or delete";
  "deletion or imputation" → "delete rows or fill in missing values"; "imputation
  parameters"/"imputation value" → "any values used to fill in missing data"/"a fill-in
  value."

No literal third-party Python API identifier needed renaming — the only pandas call
involved is `.fillna(...)`, which is already plain English. The notebook was
re-executed (`jupyter nbconvert --execute --inplace`) so every stored print/table output
matches the new wording; there were no execution errors.

**Reviewed and explicitly out of scope:** `scripts/export_widget_data.py:111` has an
internal code comment ("documented codes, never imputed") and
`book/config/abide_modeling.json` has one field describing Exercise 2's preprocessing
("No imputation is needed…"). Neither is Exercise 1 content, neither is student-facing
(one is a backend script comment, the other an internal config value never rendered to a
student), so both were left untouched per the WP's Exercise-1 scope.

### 1.3 Spearman removal (§2.3)

Removed from every path:

- **Canonical notebook**: opening list item 5; the `### Pearson and Spearman
  correlations` heading (renamed to `### Pearson correlation between numerical
  variables`) and its comparison table row; the `AGE_AT_SCAN` vs `ADOS_G_TOTAL` worked
  example (rewritten to a Pearson-only, skew-caution version); the "Explore correlations
  yourself" prose; the synthesis-challenge question and its worked "Check your reasoning"
  dropdown answer.
- **Portable notebook**: regenerated from the canonical notebook — no manual edits
  needed or made.
- **Widget config** (`book/_static/widgets/configs/eda_correlation.json`): removed
  `defaultMethod`; reworded `description`, `instructions`, and the last reflection
  prompt to drop the Pearson-vs-Spearman framing.
- **Frontend maths** (`interactive/src/correlation.ts`): removed `spearman()`,
  `averageRanks()`, and the `CorrelationMethod` type; `computeCorrelation`/`coefficient`
  now always compute Pearson; `CorrelationResult` no longer carries a `method` field.
- **Frontend component** (`interactive/src/components/correlation.ts`): removed the
  method `<select>` (`data-testid="correlation-method"`) entirely; the X/Y and grouping
  selects are retained; all stats text now reads "Pearson correlation …" unconditionally.
- **Schema** (`interactive/src/config.ts`): removed `defaultMethod: z.enum([...])` from
  `edaCorrelationConfig`.
- **Tests**: `interactive/tests/correlation.test.ts` (removed the `spearman`/
  `averageRanks` describe blocks and every `"spearman"`/`"pearson"` method argument —
  `computeCorrelation` calls now take no method arg); `interactive/tests/config.test.ts`
  (dropped `defaultMethod` from fixtures and the now-inapplicable "rejects an unknown
  defaultMethod" test); `interactive/e2e/correlation.spec.ts` (removed the
  Pearson↔Spearman test and every method-selector interaction, replacing the mobile-
  viewport interaction with the grouping select); `interactive/e2e-book/chapter01.spec.ts`
  (removed the method-switch step from the full built-page correlation test).
- **Generator** (`scripts/build_portable_notebook.py`): reworded the correlation
  iframe-replacement blurb to drop "switch between Pearson and Spearman."
- **Docs**: `interactive/README.md` — five separate mentions (status blurb, unit-test
  description, config/component/maths table rows, activity description, and the
  Pearson/Spearman comparison table, which now lists Pearson only).
- **Structural test**: `tests/test_notebook_corrections.py` — heading assertion updated
  to the new "### Pearson correlation between numerical variables" text.

Verified: `grep -ri "spearman"` returns zero hits across the canonical and portable
Exercise 1 notebooks, `eda_correlation.json`, `abide_retention.json` (the correlation
data artifact — it never held Spearman values; the coefficient is computed client-side),
`correlation.ts`, and `components/correlation.ts`. `tests/test_wp24_content_audit.py`
encodes all of this as regression tests (`Exercise1NoSpearman`,
`Exercise1CorrelationWidgetPearsonOnly`).

---

## 2. Exercise 2 — duplicate warning, sample-size section

### 2.1 Duplicate exploratory-comparison warning (§3.1)

The paragraph occurred twice: once inside the `regression-compare` widget's own config
(`selectionBiasNote` in `regression_compare.json`, shown while/before the student uses
the activity) and once in notebook cell 22, immediately after the §4 Think-first block
— i.e. **after** the student has used the activity. Per the WP, the later (notebook)
occurrence was kept unchanged; `selectionBiasNote` was removed from the schema
(`interactive/src/config.ts`), the JSON config, and its rendering in
`interactive/src/components/regression-compare.ts`. No test asserted on the field's
content, so no test rewrite was needed beyond dropping it from the
`validRegressionCompare` fixture in `config.test.ts`.

### 2.2 Section 5 shortened, feature-selection description corrected (§3.2)

**How the 10 features were actually chosen** (verified against
`scripts/sample_size_audit.py` and the committed `scripts/sample_size_audit_result.json`):
they were **not** ranked by correlation with age. Four bilateral, ≤12-column, literature-
motivated candidate bundles were predeclared (sensorimotor, early-visual, auditory,
"every-30th-atlas-ROI"); each was scored with a linear-regression audit using only the
training partition, against a decision rule (n/p ratio, upward trend, narrowing spread,
seed robustness, minimum final R²) fixed *before* any candidate was scored. The
sensorimotor-strip bundle (`p = 10`) was the first, in a fixed preference order, to pass
every check — never the best-scoring one.

Section 5's lead-in (cell 23) was rewritten to state this plainly in two short
paragraphs plus the training-size statement (down from ~230 words of dense methodological
prose to a concise, accurate summary — see word counts below), and now reads close to the
WP's suggested phrasing: "these 10 features were not chosen by ranking columns on their
correlation with age… this bundle was the first, in a fixed preference order, to pass
every check." One concise caution is retained: "This is a teaching demonstration with a
fixed feature set, not a final estimate of model performance." The later learning-curve
explanation (cell 26) was shortened to state that repeated resampling reduces the
influence of one unusually easy or hard training draw, dropping the longer methodological
aside about the whole-cortex recipe's own near-`n=p` behaviour to one sentence.

**Unchanged, verified by test and by re-running the cells:** `SAMPLE_SIZE_ROIS`,
`FEATURES_SS` (the same 10 `fsCT_*` columns), `sizes = [40, 60, 90, 130, 200, 300,
len(y_train_ss)]`, `n_rep = 40`, the fixed `random_state`/split reuse, and the resampling
loop and plotting code (cells 24–25) — none of these cells were touched, and
`test_fixed_feature_set_and_sizes_unchanged` asserts the exact source strings survive.

---

## 3. Exercise 4 — duplicate paragraph, duplicate prompts, new question

### 3.1 Majority-baseline paragraph (§4.1)

Duplicated between the `classification-imbalance` widget's own config (`imbalanceNote`
in `classification_imbalance.json`, shown while/before use) and notebook cell 28 (shown
after the iframe, cell 27 — the later occurrence). Kept the notebook occurrence; removed
`imbalanceNote` from the schema, JSON config, and its rendering in
`interactive/src/components/classification-imbalance.ts`.

### 3.2 Duplicate prompts, kept the one attached to the activity (§4.2)

Cell 28's two "Think first"/"Check your reasoning" pairs nearly duplicated the widget's
own `reflectionPrompts` (rendered as an in-widget "Reflect" list by
`classification-imbalance.ts`, i.e. literally attached to the interactive activity and
answerable only after using its controls). Per the WP's stated preference, the notebook's
two Think-first/dropdown pairs were removed from cell 28, which now contains only the
single majority-baseline paragraph plus one sentence pointing the student at the widget's
own Reflect questions. The widget's `reflectionPrompts` are the retained, single prompt
set.

Because the portable notebook replaces the iframe with a static blurb (no live widget, so
no in-widget Reflect list would ever reach it), an equivalent question was added directly
to `_CH4_IMBALANCE_IFRAME_REPLACEMENT` in `scripts/build_portable_notebook.py` — the
portable notebook keeps a reachable "Think about this as you try a few ratios…" prompt
that includes the same comparison question below.

### 3.3 New comparison question (§4.3)

Added as the third item of `classification_imbalance.json`'s `reflectionPrompts`
(and, for the portable path, the class-imbalance iframe-replacement blurb):

> "As imbalance increases, the model's raw accuracy rises too. Is the model actually
> performing better than at 50:50, or worse? What might you wrongly conclude if you only
> saw its accuracy, without the baseline for comparison?"

---

## 4. Redundant reproduction cells hidden (§7)

Three cells were newly collapsed with `hide-cell` (input **and** output collapse by
default, revealable via the theme's built-in `<details>`/"Show code cell content" toggle
— confirmed on the built page, see §7 of validation below):

| Notebook | Cell | Why it qualifies |
|---|---|---|
| Exercise 1 | histogram-reproduction cell (`sns.histplot` of `AGE_AT_SCAN`) | Preceding markdown says outright "The same basic plot can be produced in Python" — a pure reproduction of the interactive histogram activity, with no unique result. Was `hide-input` (output visible); upgraded to `hide-cell`. |
| Exercise 4 | decision-threshold reproduction (`threshold = 0.50` cell) | Its own comment says it explores "the same tradeoff the browser activity shows." Was untagged; added `hide-cell`. |
| Exercise 4 | class-imbalance reproduction (`class_ratio = "90:10"` cell) | Its own comment says it explores "the same imbalance/misleading-accuracy demonstration the browser activity shows." Was untagged; added `hide-cell`. |

**Not hidden**, per the standards' exclusions: Exercise 1's head/tail/sample cell (first
demonstration of the methods, already `hide-output` only); Exercise 1's
`retention_comparison` cell (a fixed illustrative example, not a reproduction of the
reader's own tool selection); Exercise 2's learning-curve cells (a different question —
sample size — the iframe never shows).

`scripts/build_portable_notebook.py` already resets every cell's metadata to `{}` when
building the portable notebook and asserts (`_assert_portable`) that no `hide-*` tag
survives, so no generator change was needed — confirmed on the regenerated portable
notebooks: all three corresponding cells have `metadata.tags == []` and their code/output
are present and unchanged.

---

## 5. Dark-mode syntax color

| | Selector(s) | Old color | New color | Contrast vs. code background |
|---|---|---|---|---|
| Dark mode | `.highlight .c1` (comments), `.highlight .nb` (builtins incl. `print`), `.highlight .mi` (int literals) | `#FFD900` (theme default, not previously overridden in source) | `#c7a86b` | old: 11.84:1 against `#201e2b`; new: **7.21:1** against `#201e2b` — well above the 4.5:1 minimum, materially less saturated/bright |
| Light mode | same three classes | `#515151` (comments) / `#7F4707` (builtins, ints) | **unchanged** | `#515151` → 7.43:1, `#7F4707` → 7.00:1 against `#f7f7fb` — already muted and compliant; not touched |

All three dark-mode classes previously shared one identical bright color and now share
one identical muted color, so no existing separation between comments/builtins/ints was
lost, and separation from keywords (`#DCC6E0`), function names (`#00E0E0`), and strings
(`#ABE338`) is untouched. The override was added to `book/_static/custom.css` (the only
place this project customizes pygments; there is no `pygments_dark_style` override in
`book/_config.yml`, and the generated `pygments.css` itself is a gitignored build
artifact, so this is the correct place to fix it). Verified against the actual built page
in a real browser (Playwright, both themes): computed color of `.highlight .c1/.nb/.mi`
in dark mode is `rgb(199, 168, 107)` (`#c7a86b`) and in light mode is unchanged
(`rgb(81,81,81)` / `rgb(127,71,7)`).

---

## 6. Word counts (student-facing Markdown only, Exercises 1–4)

Documentation only — not a numerical target.

| Notebook | Before | After | Delta |
|---|---|---|---|
| Exercise 1 | 4,785 | 4,800 | +15 |
| Exercise 2 | 2,547 | 2,375 | −172 |
| Exercise 3 | 2,315 | 2,315 | 0 (out of scope, untouched) |
| Exercise 4 | 2,275 | 2,139 | −136 |

Exercise 1 grew slightly net: the Spearman/impute removals shortened text, but the moved
decision block gained a transitional sentence and the correlation worked-example rewrite
added a short caution — both intentional, and net word count is not the goal for that
exercise.

---

## 7. Tests, builds, and validation run (§9)

All gates passed on the first attempt; no reruns were needed.

1. **Portable-notebook regeneration**: `scripts/build_portable_notebook.py --write
   --notebook all` (chapters 1, 2, 4 regenerated; chapter 3 unaffected/unchanged), then
   `--check --notebook all` — all four report "up to date" (deterministic).
2. **Portable-notebook smoke execution**: `scripts/smoke_portable_notebook.py` for
   `chapter_01`, `chapter_02`, `chapter_04` — all three `OK`, executed cleanly, key
   values matched.
3. **Focused Python tests**: full `tests/` discovery (`python -m unittest discover -s
   tests -p 'test_*.py'`) — **459 passed, 11 skipped** (pre-existing network-dependent
   skips), **0 failed**. This included the new `tests/test_wp24_content_audit.py` (33
   tests) and two intentionally updated assertions in `tests/test_notebook_corrections.py`
   (the histogram cell's tag and the overall hide-tag count, both now reflecting the new
   `hide-cell`).
4. **Frontend typecheck**: `npm run typecheck` in `interactive/` — clean, no errors.
5. **Frontend unit tests**: full `npx vitest run` — **309 passed**, 21 files (touched
   files re-verified individually first: `correlation.test.ts`, `correlation-data.test.ts`,
   `config.test.ts`, `regression-compare.test.ts`, `classification-metrics.test.ts`).
6. **Frontend production build**: `npm run build` in `interactive/` — succeeded, rebuilt
   `book/_static/widgets/app/` (gitignored build artifact, needed only for local
   Playwright verification; not committed).
7. **Jupyter Book build**: `jupyter-book build book` — succeeded, 2 pre-existing warnings
   unrelated to this WP (missing `logo.png`, `README.md` not in a toctree).
8. **Built-book Playwright** (`playwright.book.config.ts`, `--workers=1`):
   `chapter01.spec.ts`, `chapter01-dark-mode.spec.ts`, `chapter02.spec.ts`,
   `chapter04.spec.ts` — **23/23 passed**.
9. **Standalone-widget Playwright**: `correlation.spec.ts`, `regression-compare.spec.ts`,
   `classification-imbalance.spec.ts` — **34/34 passed**.
10. **Manual/scripted visual verification** (Playwright driving the built book directly,
    screenshots + computed-style checks, both themes):
    - Exercise 1 missing-data section: decision block confirmed rendered immediately
      before the retention activity.
    - Exercise 1 Pearson activity: confirmed no method selector in the DOM; stats text
      reads "Pearson correlation r = …".
    - Exercise 2 §4/§5: confirmed the single exploratory-comparison warning sits right
      after the Think-first block, and the shortened §5 renders as intended.
    - Exercise 4 §6: confirmed the class-imbalance section shows only the single
      majority-baseline paragraph with no duplicate Think-first blocks.
    - A representative code block (Exercise 1's data-loading cell): dark-mode computed
      color for `.c1`/`.nb`/`.mi` is `rgb(199, 168, 107)`; light mode unchanged.
    - The Exercise 1 hide-cell reproduction cell: confirmed collapsed
      (`<details>` without `open`) by default, with both input and output inside the same
      `<details>`, labelled "Show code cell content"/"Hide code cell content", and
      confirmed clicking the summary reveals both.

No gate failed; the one-retry allowance in §9 of the WP was not needed.

---

## 8. Deviations / items for Yoav's attention

- `scripts/build_course_overview_docx.py` still names "Spearman correlations" in its
  Exercise 1 description text (used to build
  `course_overview/Machine_Learning_for_Neuroscience_Notebook_Overview.docx`). Per the
  standing WP20 policy that the approved Word overview and its generator are not touched
  without an explicit request, this line was **left unchanged** rather than edited or
  regenerated. It will describe removed content until a future WP updates it — flagging
  for a decision, not fixing unilaterally.
- `scripts/export_widget_data.py:111` and `book/config/abide_modeling.json` each contain
  one internal, non-Exercise-1, non-student-facing mention of "imput*"; reviewed and left
  untouched as out of this WP's Exercise-1-only scope (§1.2 above).

No other deviations. Every item in the WP was completed as specified.

---

## 9. Final state

```
$ git status --short --branch
## edit/wp24-notebook-concision
?? WPs/reports/WP16_ARCHITECT_REPORT.md
?? WPs/reports/WP21_DEPLOYMENT_REPORT.md
```

(as of writing this report, before the report files themselves are committed in the
following commit). Local build/inspection artifacts (`book/_build/`,
`book/_static/widgets/app/`) are gitignored and were not committed. Nothing was pushed,
deployed, or monitored via GitHub Actions. WP25 was not started.
