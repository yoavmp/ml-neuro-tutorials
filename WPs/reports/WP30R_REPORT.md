# WP30R Report: Classification-Tree Holdout Correction

## 1. Outcome

**Success.** The classification-depth audit's methodological bug — cross-validating over the
full 1,004-participant eligible cohort, which necessarily contained Exercise 3's locked
251-participant outer-test partition inside every fold — is fixed. The audit now reconstructs
Exercise 3's exact outer split, excludes those 251 participants by participant-set membership
before any cross-validation fold is formed, and never fits or scores a tree on them. WP30's
original inclusion rule was reapplied unchanged; it still passes on the corrected, smaller
(753-participant) development pool, so the classification-tree contrast figure is **retained**,
with its plotted values, annotations, and prose updated to the corrected results and explicit
development-only framing.

One implementation bug was found and fixed during this WP's own validation (not a spec
ambiguity): see §6.

## 2. Git state

**Starting branch:** `fix/wp30-exercise6-refinements` at `6b761644d6e6d4b2c5420a28424db733cdb978f8`
(WP30 report/changelog). `git status --short --branch` at that point:
```
## fix/wp30-exercise6-refinements
?? WPs/WP30R_CLASSIFICATION_HOLDOUT_CORRECTION.md
?? WPs/reports/WP16_ARCHITECT_REPORT.md
?? WPs/reports/WP21_DEPLOYMENT_REPORT.md
```
Only the three permitted untracked files were present. Nothing else was present; nothing was
reset, stashed, or overwritten.

**Working branch:** `fix/wp30r-classification-holdout`, created from `6b76164`. First commit
saves the WP30R spec verbatim as the initial checkpoint, before any implementation file changed.

**Final status:** working tree clean on `fix/wp30r-classification-holdout` after this report and
changelog are committed; `WPs/reports/WP16_ARCHITECT_REPORT.md` and
`WPs/reports/WP21_DEPLOYMENT_REPORT.md` remain untracked and untouched, exactly as found.

## 3. Reconstruction of Exercise 3's exact outer split

Exercise 3's classification cohort, target coding, and split settings
(`book/config/abide_modeling.json` → `classification`) were used verbatim, not reinvented:
`train_test_split(test_size=0.25, random_state=42, stratify=y)`, where `y` is `group` recoded
autism (code 1) → 1, control (code 2) → 0, over the full eligible cohort (`group` present, which
is all 1,004 brain-table participants — `group` has zero missing values in this table).

The reconstruction (`scripts/decision_tree_model_audit.py:_classification_dev_test_positions`,
mirrored inline in the notebook) draws the identical `train_test_split` call over
`np.arange(n_eligible)` stratified by the identical `y` array, then **sorts** the returned
positions back into the eligible cohort's original row order (train_test_split itself returns
them pre-shuffled — see §6 for why this sort is not optional) and uses `subject` (a stable,
native identifier column) to prove the reconstruction rather than trusting index arithmetic
alone.

**Independent identity proof** (run once, network, not part of the committed offline test
suite — see §6's deviation note): loading a fresh frame and calling Exercise 3's own
`classification_model_audit.py._xy()` / `._split()` to get its actual train/test subject sets,
then comparing them set-for-set against this WP's reconstruction:
```
Ex3 train set == WP30R dev set:  True
Ex3 test set  == WP30R test set: True
sizes: 753 753 251 251
```
The reconstructed development and outer-test partitions are **participant-for-participant
identical** to Exercise 3's own split, not merely equal in size.

## 4. Sample sizes and class counts

| Partition | n | positive (autism) | negative (control) |
|---|---|---|---|
| Eligible cohort | 1004 | 463 | 541 |
| Development (used for CV) | 753 | 347 | 406 |
| Outer test (excluded) | 251 | 116 | 135 |

`753 + 251 = 1004`; `347 + 116 = 463`; `406 + 135 = 541`. Development and outer-test participant
sets are disjoint by construction and their union equals the eligible cohort — both asserted at
runtime (raising `RuntimeError` if violated) and re-verified offline by `--check` and by
`tests/test_decision_tree_model_audit.py`. These sizes are identical to
`scripts/classification_model_audit_result.json`'s own committed `cohort` block
(`n_train=753, n_test=251, n_positive_total=463, n_negative_total=541`).

## 5. Corrected depth-by-depth audit and inclusion decision

Configuration unchanged from WP30 except the participant pool: `all-eligible × CT` (p=360, same
natural column order the notebook itself uses), `DecisionTreeClassifier`,
`min_samples_leaf=5`, `max_depth` 1–10, `StratifiedKFold(n_splits=5, shuffle=True,
random_state=42)` — now applied to the 753 development rows only.

| max_depth | train ROC AUC | val ROC AUC |
|---|---|---|
| 1 | 0.5742 | 0.5233 |
| 2 | 0.6417 | 0.5337 |
| 3 | 0.7100 | 0.5202 |
| 4 | 0.7752 | 0.5560 |
| 5 | 0.8306 | **0.5672** |
| 6 | 0.8766 | 0.5561 |
| 7 | 0.9122 | 0.5487 |
| 8 | 0.9377 | 0.5518 |
| 9 | 0.9579 | 0.5503 |
| 10 | 0.9703 | 0.5490 |

**Best depth = 5** (val ROC AUC 0.567219), **depth-2 val ROC AUC = 0.5337**, **margin =
0.033519**.

**Inclusion rule (unchanged, reapplied exactly):**
- highest validation ROC AUC at `max_depth = 5` → **≥ 3: pass**;
- margin over depth 2 (`0.033519`) → **≥ 0.01: pass**;
- **both conditions pass → the classification figure is retained.**

Neither the metric, folds, seed, feature recipe, depth range, nor tie-break rule was altered
after this result was seen; the only change from WP30 was restricting the participant pool, made
before rerunning.

## 6. Figure decision and student-facing update

**The classification figure is retained.** Its title now reads "Classification: predicting
autism diagnosis (development data only)"; the code cell prints `eligible = 1004   development =
753   outer test (excluded) = 251` before running any cross-validation; the surrounding markdown
states the corrected numbers (max_depth=5, 0.567, margin 0.034 over depth-2's 0.534), explicitly
says the comparison ran "within Exercise 3's development partition (753 of the 1004 eligible
participants)" and that "Exercise 3's own locked 251-participant outer test set is excluded
before any fold is formed and is never used to compare depths," and keeps every required caution
from WP30 (ROC AUC higher-is-better vs. MSE lower-is-better; not-inherently-more-complex;
modest/near-chance AUC values, not a strong classifier).

## 7. Provenance correction (WP30 §5)

The manifest note and the audit script's docstring previously implied that the full-cohort
version was safe because "this script never reads a stored test-index object." That is true but
irrelevant: the full 1,004-row cohort *is* the eligible cohort, which *contains* the 251 outer-test
participants regardless of whether any index file is read, so their outcomes influenced every
cross-validation fold. Both locations now state the corrected basis for safety explicitly:
participant-set exclusion, proven by asserted disjointness and union-equality, not omission of a
side-channel index.

## 8. A self-caught bug during this WP's own validation

While re-executing the corrected notebook cell, its printed depth-by-depth AUC values did not
match the corrected audit script's committed result, even though both used the identical
eligible-cohort data, identical `test_size`/`random_state`/`stratify`, and identical downstream
code. Root cause: `train_test_split` returns the requested positions in a **pre-shuffled** order,
and `StratifiedKFold(shuffle=True, random_state=42)`'s fold assignment depends on the *row order*
of the array it is given, not merely on *which* rows are present. The audit script already sorted
its reconstructed `dev_pos`/`test_pos` back into original row order before subsetting; the first
draft of the notebook cell did not. Fixed by adding the same `np.sort(...)` to the notebook cell;
re-executed once, and the notebook's printed curve then matched the script's committed result
exactly (`max_depth=5`, val AUC 0.567219, at every depth). This is now called out with an inline
comment in the notebook explaining why the sort is necessary, not incidental.

## 9. Tests and builds run, corrections, and reruns

Run in the order given by WP30R §7, each once unless noted:

1. `decision_tree_model_audit.py --run` (network, 32.4s) then `--check` — both pass; `--check`
   additionally re-verifies `development_test_disjoint`, `development_test_union_equals_eligible`,
   the eligible/development/outer-test size and class-count partitioning, and the inclusion
   rule's three booleans against a fresh recomputation of the corrected `val_auc` curve.
2. Focused `test_decision_tree_model_audit.py` (20 tests) and `test_exercise_06_notebook.py`
   (94 tests) — both pass.
3. `build_portable_notebook.py --write --notebook chapter_06` then `--check` — up to date, 33
   cells.
4. Dedicated portable-notebook smoke execution: ran the existing `scripts/smoke_portable_notebook.py`
   as-is (chapters 1–4, which is all it currently registers) — all 4 pass, confirming this WP
   introduced no regression there. Chapter 6 is not registered in that script (out of this WP's
   §6 file list, so not added); as the substantive equivalent, the chapter_06 portable notebook
   was independently smoke-executed outside the repository with the same method
   (`nbclient.NotebookClient` in a fresh temp directory) and its key printed values checked,
   including the corrected `eligible = 1004   development = 753   outer test (excluded) = 251`
   line and `depth= 5 ... val ROC AUC=0.567 <- highest validation ROC AUC` — passed cleanly (12
   code cells executed).
5. Full Python suite (`python -m unittest discover -s tests`) — **691 tests pass** (683 before
   this WP + 8 new).
6. Frontend typecheck — **not run**; no file under `interactive/` changed in this WP (confirmed
   by `git status`), so there is nothing to typecheck.
7. Production frontend build — **not run**, for the same reason (no frontend inputs changed).
8. `jupyter-book build book` — succeeds; the corrected notebook's cached execution was reused
   (content-hash matched the nbconvert run already performed); no new `*.err.log` files; the same
   one pre-existing, unrelated warning as WP30 (`book/README.md` not in any toctree).
9. Focused built-book Exercise 6 Playwright tests (`chapter06.spec.ts`) — **6/6 pass**.
10. Launch-button (`launch-buttons.spec.ts`, 20 tests) and dark-mode
    (`wp22-cross-chapter-dark-mode.spec.ts`, 5 tests) checks, run because the classification
    figure's text changed — **25/25 pass**, including Exercise 6's own dark-mode entry.

No gate failed because of this WP other than the self-caught notebook/script mismatch in §8,
which was corrected and the affected notebook cell re-executed once (not a full gate rerun, since
the mismatch was caught before any gate ran against the stale cell). No unrelated pre-existing
failures were encountered. No sleeps, lowered visual thresholds, skipped tests, or global retries
were used anywhere in this WP.

## 10. Manual verification

Inspected the built Exercise 6 page in both light and dark rendering (via Playwright screenshots,
not committed as tests):
- the regression complexity figure (Section 3's first panel) is visually unchanged;
- the classification figure is present (rule passed) and reads "Classification: predicting
  autism diagnosis (development data only)", with the `eligible = 1004   development = 753
  outer test (excluded) = 251` line printed directly above it;
- the retained curve and prose show the corrected development-only numbers (max_depth=5, 0.567,
  margin 0.034);
- no student-facing text implies locked test rows were used for depth comparison;
- both light and dark renderings remain readable (the matplotlib figure itself keeps a white
  background in dark mode, consistent with every other static figure in this course — not a
  regression introduced here);
- the portable notebook was regenerated from, and therefore matches, the canonical notebook's
  decision to retain the figure.

## 11. Deviations and items for the user's attention

1. **Network-dependent identity proof kept out of the offline test suite.** The strongest
   evidence that the reconstructed development/outer-test partitions are
   participant-for-participant identical to Exercise 3's own split (§3) requires loading a live
   frame and calling `classification_model_audit.py`'s own functions — it was run once,
   successfully, and is reported verbatim in §3, but was deliberately not added to
   `tests/test_decision_tree_model_audit.py`, since that suite's module docstring commits to
   "no network" (matching the repository's offline-CI contract for that file). The committed
   offline tests instead check: the committed result's development/outer-test sizes and class
   counts match `classification_model_audit_result.json`'s own committed cohort numbers
   (`test_classification_complexity_curve_cv_pool_is_development_only_not_the_full_cohort`), the
   partition-membership booleans and arithmetic are internally consistent
   (`test_classification_complexity_curve_proves_participant_set_exclusion`), and a fresh
   `train_test_split` replay with the same recorded sizes/seed reproduces the same partition
   sizes (`test_classification_complexity_curve_reconstruction_is_deterministic_offline`). If
   stronger, network-based CI coverage of the exact participant identity is wanted, it would need
   its own opt-in/network-marked test, which was judged out of this narrow correction's scope.
2. **The self-caught row-order bug (§8, §6 changelog)** is worth flagging even though it was
   fixed within this WP: it is a subtle, easy-to-repeat mistake (`train_test_split`'s returned
   indices are not sorted) that would have silently produced a different-but-plausible-looking
   corrected result had the notebook and audit script not been cross-checked against each other
   during validation. The fix is now an explicit, commented behavior in both files, not just a
   latent convention.

Implementation and both reports are committed locally on `fix/wp30r-classification-holdout`. Per
WP30R §9 / the task instructions, nothing was merged, pushed, deployed, or monitored on GitHub
Actions, and WP31 was not started.
