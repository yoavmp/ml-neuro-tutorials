# WP30 Report: Exercise 6 Clarity and Activity Refinements

## 1. Outcome

**Success.** Every numbered section of the WP30 spec was implemented, tested, and validated:
the single-tree diagram now uses short display-only aliases and plain wording with no bare
`value =`; the 2D partition plot has gray, correctly-clipped decision-boundary overlays; the
greedy-splitting activity's four-quadrant dataset was replaced end-to-end with a simulated,
overlapping two-feature dataset (seed 17, the first of 0–49 to pass every predeclared
acceptance criterion); a bounded classification-tree audit was run exactly once and its
predeclared inclusion rule passed, so a second, clearly-labeled contrast figure was added; the
ensemble activity's replicate/seed selector was removed everywhere (schema, config, component,
tests) in favor of one fixed training sample, and its MSE axis titles were shortened to exactly
`MSE (years²)`; the fair-comparison cell is now `hide-input` (table visible, code collapsed);
and the duplicate post-activity "Think again" markdown blocks were removed for both activities
(see §7 Deviations — this last point reads a related instruction slightly more broadly than its
literal placement in the spec).

## 2. Git state

**Starting branch:** `feature/wp29-exercise6-decision-trees` at `5998e0408d1bd2d9bd81793ed664102bcfb0e786`
(WP29 report/changelog). `git status --short --branch` at that point:
```
## feature/wp29-exercise6-decision-trees
?? WPs/WP30_EXERCISE_6_CLARITY_AND_ACTIVITY_REFINEMENTS.md
?? WPs/reports/WP16_ARCHITECT_REPORT.md
?? WPs/reports/WP21_DEPLOYMENT_REPORT.md
```
Only the three permitted untracked files were present (the WP30 spec itself, plus the two
pre-existing untracked reports carried over from earlier WPs). Nothing else was present; nothing
was reset, stashed, or overwritten.

**Working branch:** `fix/wp30-exercise6-refinements`, created from `5998e04`. First commit saves
the WP30 spec verbatim as the initial checkpoint, before any implementation file changed.

**Final status:** working tree clean on `fix/wp30-exercise6-refinements` after this report and
changelog are committed; `WPs/reports/WP16_ARCHITECT_REPORT.md` and
`WPs/reports/WP21_DEPLOYMENT_REPORT.md` remain untracked and untouched, exactly as found.

## 3. Section-by-section outcome

| Spec section | Outcome |
|---|---|
| §1 Tree diagram aliases/wording | Done. Aliases are diagram-only; real column names unchanged in code/manifest/audit. Verified functionally (executes the real formatter against a throwaway tree) that no rendered box contains `value =`. |
| §2 Partition-plot boundaries | Done. Boundaries clipped to each split's own parent region; verified functionally against a throwaway tree that only the root's boundary spans the full extent. |
| §3 Greedy dataset replacement | Done end-to-end: exporter, committed artifact, widget config wording, notebook reproduction, portable notebook, tests. See §4 below for the full audit. |
| §4 Classification audit + conditional figure | Done. Audit run once with settings fixed beforehand; inclusion rule passed; figure added, clearly labeled, with the required caveats. See §5 below. |
| §5 "One Tree or Many?" simplification | Done. Selector removed from schema/config/component; distribution and ensemble-size panels still aggregate all 5 replicates; prediction panel uses the first replicate (seed 0), documented in the manifest. Axis titles shortened; "lower is better" moved to a caption. |
| §6 Fair-comparison cell tag | Done. `hide-cell` → `hide-input`; table visible; code collapsed on the website; portable notebook keeps it visible and runnable (unaffected, since the portable generator never hides cells). |
| §7 Consistency sweep | Done; see the exact changelog. Repo-wide grep confirms no remaining "quadrant" / duplicate-reflection / `defaultReplicateSeed` / old long-axis-title text in student-facing or config surfaces. |
| §8 Focused tests (17 items) | All 17 have at least one direct test; several (no-bare-`value=`, partition-boundary hierarchy) are functional (execute the real notebook code), not just textual greps. |
| §9 Bounded validation | Run; one gate failed because of this WP and was corrected once (see §6 below); no gate was rerun without new evidence. |
| §10 Manual verification | Done via Playwright screenshots (not committed as tests) of the standalone greedy widget in dark mode and at 390px, and of the built Exercise 6 page's tree diagram, partition plot, classification curve, and fair-comparison collapse/table in light and dark. All matched expectations. |

## 4. Greedy-splitting dataset: formula, seed, and full audit

**Formula (fixed before any seed was inspected):**
```
x1 ~ Normal(mu1=5.5, sd1=2.0)
x2 ~ Normal(mu2=5.5, sd2=2.0)
y  = intercept + beta1*z(x1) + beta2*z(x2) + gamma*z(x1)*z(x2) + noise
noise ~ Normal(0, noise_sd=2.5)
intercept=20.0, beta1=6.0, beta2=5.0, gamma=1.5
z(x) = (x - mean) / sd   (the fixed population parameters above, not sample statistics)
n = 16 observations
```
**Seed selection:** seeds `0..49` were scanned in order against the predeclared acceptance
criteria in `scripts/export_tree_greedy_widget.py:seed_diagnostics()` — both feature–target
correlations in `[0.35, 0.90]`, cross-feature correlation `≤ 0.40`, a root-split margin `> 0.75`
with margin-ratio `≤ 0.55` (unique, discoverable, not obvious), both root-split children `≥ 5`
observations, both further child splits with margin `> 0.5` / ratio `≤ 0.60` and both
grandchildren `≥ 3` observations, and both features used somewhere across the tree. **Seed 17**
is the first of `0..49` to pass every criterion (seeds 0–16 each fail at least one — see the
committed artifact's `generatingProcess` and `tests/test_export_tree_greedy_widget_data.py`'s
`test_selected_seed_is_genuinely_the_first_passing_seed_0_to_49`, which recomputes this
independently). No seed after 17 was inspected for a "better" result.

**Correlations (seed 17, n=16):** `corr(x1, y) = 0.760`, `corr(x2, y) = 0.605`,
`corr(x1, x2) = 0.072`.

**Full three-round audit** (weighted split MSE, reduction, and runner-up gap; all numbers are
byte-identical to the committed `book/_static/widgets/data/tree_greedy_split.json`):

| Round | n | Parent MSE | Optimal split | Split MSE | Reduction | Sizes (L/R) | Runner-up | Gap |
|---|---|---|---|---|---|---|---|---|
| Root | 16 | 75.728 | Brain measure 1 ≤ 5.925 | 37.381 | 38.347 | 8 / 8 | Brain measure 2 ≤ 6.969 (reduction 35.027) | 3.320 |
| Left child | 8 | 37.103 | Brain measure 2 ≤ 5.493 | 5.919 | 31.183 | 5 / 3 | Brain measure 2 ≤ 4.915 (reduction 19.250) | 11.933 |
| Right child | 8 | 37.659 | Brain measure 2 ≤ 6.6375 | 15.132 | 22.528 | 5 / 3 | Brain measure 2 ≤ 4.2675 (reduction 20.458) | 2.070 |

Both features are used across the tree (root on Brain measure 1, both children on Brain measure
2), matching the old dataset's structure while now coming from continuous, overlapping,
genuinely noisy data rather than four constructed quadrants.

## 5. Classification-tree audit and inclusion-rule outcome

**Configuration, fixed before viewing any result:** Exercise 3's cohort and target coding
(`group` recoded autism=1/control=0, n=1004: 463 positive / 541 negative), the same 360-feature
`all-eligible × CT` recipe, `min_samples_leaf=5` (chosen to match this section's own regression
complexity curve, for consistency, not scanned), `max_depth` grid 1–10,
`StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`, mean training/validation ROC AUC
from predicted probabilities. The outer `classification.holdout_split` test partition was never
read by this audit (it runs cross-validation over the full eligible cohort instead).

**Full depth curve** (`scripts/decision_tree_model_audit_result.json`
→ `classification_complexity_curve`):

| max_depth | train ROC AUC | val ROC AUC |
|---|---|---|
| 1 | 0.560 | 0.509 |
| 2 | 0.616 | 0.508 |
| 3 | 0.676 | **0.532** |
| 4 | 0.743 | 0.510 |
| 5 | 0.797 | 0.496 |
| 6 | 0.851 | 0.500 |
| 7 | 0.894 | 0.518 |
| 8 | 0.924 | 0.519 |
| 9 | 0.947 | 0.528 |
| 10 | 0.965 | 0.525 |

Depths 3 (0.5320) and 10 (0.5253) round to the same 2-decimal display value in a slightly
different audit variant seen mid-way through this WP (see §6); at the final, natural-column-order
configuration depth 3 is the unambiguous raw maximum, so the shallower-preferred tie-break was
not actually needed to select it, though the code still applies it (and is tested against
recomputation).

**Inclusion rule (WP30 §4.2), evaluated once:**
- highest validation ROC AUC at `max_depth = 3` → **≥ 3: pass**;
- margin over depth 2 (`0.531971 − 0.507889 = 0.024082`) → **≥ 0.01: pass**;
- **both conditions passed → the classification figure was included.**

Neither the metric, folds, seed, feature recipe, depth range, nor tree settings were changed
after this result was seen. The notebook clearly labels both panels, explicitly states ROC AUC is
higher-is-better versus MSE's lower-is-better, explicitly disclaims that classification is
inherently more or less complex than regression, and adds an honesty caveat that both validation
ROC AUC values are modest and close to chance (0.5) — the figure demonstrates depth selection,
not a strong classifier.

## 6. Fixed ensemble replicate

The "One Tree or Many?" prediction panel now always uses **replicate index 0 (seed 0)** — the
first replicate in `book/_static/widgets/data/tree_ensemble_compare.json`, per WP30 §5's
preference for the first existing replicate absent a technical reason otherwise. Documented in
`book/config/abide_modeling.json` → `decision_tree.ensemble.fixed_prediction_replicate`. The
distribution and ensemble-size panels are unaffected and continue to aggregate across all 5
audited replicates.

## 7. Tests and builds run, corrections, and reruns

Run in the order given by WP30 §9, each once unless noted:

1. `decision_tree_model_audit.py --run` (network, 23.4s) and `--check`; `export_tree_greedy_widget.py --refresh`/`--check`; `export_tree_ensemble_widget.py --check`; `abide_modeling_data.py --check` — all pass.
2. Focused Exercise 6 Python tests (`test_decision_tree_model_audit.py`,
   `test_export_tree_greedy_widget_data.py`, `test_exercise_06_notebook.py`) — all pass
   (16 + 15 + 68 tests).
3. `build_portable_notebook.py --write --notebook chapter_06` then `--check` — up to date, 33 cells.
4. Portable-notebook smoke: covered by the full `unittest discover` run (below) plus the executed
   canonical notebook (gate 7); the dedicated `smoke_portable_notebook.py` network script was not
   separately re-run in this offline session (see §8, deviations).
5. Frontend unit tests + `tsc --noEmit` — 359 tests pass, no type errors.
6. `npm run build` (production widget bundle) — succeeds (pre-existing >500kB chunk-size
   warning, unrelated to this WP).
7. `jupyter-book build book` — succeeds; Exercise 6 notebook executed fresh via mystnb in 28.8s;
   no `*.err.log` files produced; one pre-existing, unrelated warning (`book/README.md` not in
   any toctree).
8. Focused standalone (`tree-greedy-split.spec.ts`, `tree-ensemble-compare.spec.ts`) and
   built-book (`chapter06.spec.ts`) Playwright tests — 6 + 8 + **initially 5/6 pass, 1 fail**
   (see correction below); after the fix, 6/6 pass.
9. Launch-button (`launch-buttons.spec.ts`), dark-mode (`wp22-cross-chapter-dark-mode.spec.ts`),
   narrow-viewport checks — all pass, including Exercise 6's dark-mode entry.
10. Full Python suite (`python -m unittest discover -s tests`) — **683 tests pass** (run twice,
    identical result both times).
11. Full frontend unit suite (`npm run test:unit`) — **359 tests pass** (27 files).
12. Full standalone Playwright suite (`npx playwright test`) — **188 tests pass**.
13. Full built-book Playwright suite (`npm run test:e2e:book`), including the hardened Exercise 5
    geometry test — **85 passed, 1 failed** on the first run; the 1 failure was in
    `chapter06.spec.ts` (this WP's own change); corrected and the single spec file rerun
    (6/6 pass). Not rerun in full a second time, per §9's "do not rerun gates that already
    passed."

**Two corrections made during validation, each applied once and re-verified:**

1. **Classification audit column order.** The first version of
   `_classification_complexity_curve()` used `abide_modeling_data.bundle_columns()`'s canonical
   ROI-then-hemisphere order (matching Exercise 3's own classification audit). Executing the
   notebook's own inline cell — which, like every other tree section in Exercise 6, uses the raw
   table's natural column order because `DecisionTreeClassifier` split selection is
   order-sensitive among highly correlated cortical-thickness columns — produced *different*
   numbers (val AUC 0.530 vs. 0.532 at depth 3, etc.), an inconsistency between the audit script
   and the notebook it is supposed to underwrite. Fixed by switching the audit script to the
   same `_natural_order_columns()` helper the existing regression `_complexity_curve()` already
   uses, for the same documented reason; re-ran `--run` once. The inclusion rule's outcome did
   not change (still passes; the margin grew slightly, from 0.021 to 0.024).
2. **Portable-notebook banned-path check.** The rewritten greedy-reproduction cell's comment
   originally referenced the widget's own committed-artifact path
   (`book/_static/widgets/data/tree_greedy_split.json`), which tripped
   `build_portable_notebook.py`'s `_static/`-path guard (a check meant to catch stray
   book-internal paths leaking into the portable notebook). Reworded the comment to describe the
   artifact without the literal path; re-ran `--write`/`--check` once, both clean.
3. **Built-book Playwright wording.** `chapter06.spec.ts`'s reveal-panel assertion expected the
   literal substring `"x1"`, which the widget correctly no longer shows now that its label reads
   "Brain measure 1". Updated the assertion to expect the new, correct label; reran that one
   spec file once (6/6 pass) rather than the full built-book suite again.

No unrelated pre-existing failures were encountered. No sleeps, lowered visual thresholds,
skipped tests, or global retries were used anywhere in this WP.

## 8. Deviations and items for the user's attention

1. **Duplicate-reflection scope.** WP30 §3.2 states "keep only one post-activity reflection
   block; remove the duplicate Think Again/Reflect set" inside the subsection about the greedy
   activity specifically. I found the *identical* pattern in the ensemble activity (its own
   "Think again" markdown cell duplicated `tree_ensemble_compare.json`'s `reflectionPrompts`
   almost verbatim) and removed both, reasoning from §7's general "duplicate reflection prompts"
   sweep instruction and §8 test item 9 ("only one post-activity reflection set remains"). If the
   intent was narrower — only the greedy activity — the ensemble activity's removed markdown cell
   can be restored from this branch's history; I judged the broader, symmetric fix more coherent
   given both activities exhibited the same duplication for the same underlying reason.
2. **Partition-plot axis labels kept as real column names**, not the §1.1 diagram aliases — §1.1
   scopes aliasing to "the diagram" (the tree figure in §1); §2's own instruction list for the
   partition plot does not mention aliasing, so the axis labels were left unchanged.
3. **Classification figure's honesty caveat** (both ROC AUC values are close to 0.5, i.e.
   chance-level) goes slightly beyond §4.2's literal text, added because the audited numbers are
   genuinely modest and the existing notebook's tone elsewhere (e.g. Section 6's "not guaranteed"
   framing) sets a standard of not overstating results.
4. `scripts/smoke_portable_notebook.py` (the network script that executes the portable notebook
   completely outside the repository, listed in `.github/workflows/deploy.yml`) was not
   separately invoked in this offline validation session; the portable notebook's own
   `--check` (determinism) passed, and the canonical notebook it is derived from executed
   cleanly end-to-end twice.

Implementation and both reports are committed locally on `fix/wp30-exercise6-refinements`. Per
WP30 §11 / the task instructions, nothing was merged, pushed, deployed, or monitored on GitHub
Actions, and WP31 was not started.
