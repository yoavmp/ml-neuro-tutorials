```text
WPs/WP27R_EXERCISE_4_INTERACTION_AND_NESTED_CV_REFINEMENTS.md
```

Produce:

```text
WPs/reports/WP27R_REPORT.md
WPs/reports/WP27R_EXACT_CHANGELOG.md
```

## 0. Purpose

This is a **local correction** to the already-completed WP27 Exercise 4
("Validation and Cross-Validation"). WP27 was merged into
`feature/wp27-validation-cross-validation` and reported as a success, but a
post-hoc read of the shipped activity surfaced four refinements worth making
before that branch is ever proposed for `main`:

1. the "Choose k Before Revealing the Test Set" activity's candidate-`k` grid
   is too sparse around the value that actually wins on validation data;
2. that activity never shows students the *test*-MSE curve at all -- only
   two summary sentences after locking -- so the core lesson ("the
   test-error pattern tracks validation error more closely than training
   error") is asserted in prose but never shown as a picture;
3. the nested-cross-validation candidate grid jumps from 15 to 30, which
   flattened every outer fold's selection to `k = 15` and undersold the
   "different outer folds can select different values" lesson;
4. the nested-CV diagram is a generic Mermaid flowchart that does not
   actually render in the portable (Colab / Jupyter) notebook, and does not
   show the two-level, fold-by-fold structure of nested cross-validation.

This WP does **not** rebuild Exercise 4. It changes candidate grids, adds a
third plotted panel to one existing widget, replaces one diagram, and updates
the surrounding prose/tests/portable notebook to stay consistent. It does not
merge, push, deploy, monitor GitHub Actions, or begin WP28.

## 1. Starting state

Verify:

```bash
git status --short --branch
git branch --show-current
git rev-parse HEAD
git log --oneline --decorate -10
```

Expected starting branch: `feature/wp27-validation-cross-validation`, with
the documentation-placeholder correction (`WP27: fix unresolved placeholder
in final-git-state section of report`) already committed at `HEAD`.

The only permitted untracked files are:

```text
WPs/reports/WP16_ARCHITECT_REPORT.md
WPs/reports/WP21_DEPLOYMENT_REPORT.md
```

Leave them untouched. If the state differs materially, stop -- do not reset,
rebase, stash, clean, or automatically resolve divergence.

Create the branch:

```bash
git switch -c fix/wp27r-validation-refinements
```

Write and commit this specification before any implementation.

## 2. Hidden-test activity: expand the k grid

In "Choose k Before Revealing the Test Set" (`scripts/wp27_validation_audit.py`
Part B `CANDIDATE_KS`, currently
`[1, 2, 3, 5, 8, 12, 20, 30, 50, 75, 100, 150, 250, 400, 564]`), replace the
sparse region around the likely optimum with a denser one.

The final grid must include at least: `8, 10, 15, 20, 25, 30, 50`.

Preserve the useful, valid larger candidates already present after 50
(`75, 100, 150, 250, 400, 564`), and the very small candidates (`1, 2, 3, 5`)
that demonstrate the training-selected-`k` overfitting case. Drop `12`
(replaced by the denser `10`/`15` neighbours) unless a *different, clearly
defined* candidate grid elsewhere still needs it -- it does not.

Apply the same final grid consistently in: notebook prose, the Python
tuning-reproduction cell, the audit script, the exported widget data, the
widget configuration, the frontend controls/labels, the portable notebook,
and the tests. No stale reference to the old grid (in particular `12`) may
remain outside a different, clearly defined grid (the nested-CV grid, which
is handled separately in section 7).

## 3. Reveal a third test-MSE plot after locking

Rebuild the "Choose k Before Revealing the Test Set" widget
(`interactive/src/components/validation-lock-test.ts`) around one aligned
three-panel figure: training MSE vs. `k`, validation MSE vs. `k`, and test
MSE vs. `k`, sharing an aligned (log) x-axis and a comparable y-axis
presentation across all three panels.

Before locking:

* show the training panel and the validation panel (as today);
* keep the third panel visibly present but empty/locked -- a placeholder,
  not real test data;
* do not put any test-MSE value into the DOM, an accessibility string, a
  tooltip, a hover template, a `hidden` element, or any other
  student-inspectable surface before the lock button is pressed. (The
  underlying data module may hold every candidate's precomputed test score in
  memory -- it always has, for every WP27 widget -- but no test number may be
  rendered into a plot trace, a text node, or an attribute until locked.)

After "Lock Choice and Reveal Test Result" is pressed:

* freeze the selected `k` and disable the tuning controls (already true);
* redraw the figure with the third panel populated with the real test-MSE
  curve across every candidate `k`;
* keep the training and validation panels visible in the same figure;
* mark the student-chosen `k` consistently on all three panels;
* also mark/identify the training-selected and validation-selected `k`
  values on the panels or in adjoining text;
* state, next to the figure, that lower MSE is better.

Use wording such as "tracks" or "resembles" for the test/validation
relationship unless an actual correlation coefficient is computed and
clearly labelled -- none is required here, and none is added.

Add an explicit methodological warning, visible once the result is revealed,
that the complete test curve is shown only as a teaching demonstration:
in a real analysis, evaluating every candidate on the test set would use the
test set for tuning, and the choice must not change after seeing the curve.

"Reset Activity" restarts the demonstration; its note must say that
repeated resets and test inspection would be invalid in a real analysis
(already true; keep and, if needed, sharpen the wording to mention the
revealed *curve*, not only the single locked score).

## 4. Guiding and reflection questions

Keep, before the activity (the existing "Think first" block and the widget's
pre-lock reflection prompts):

* which `k` should perform best on the training set (training-selected vs.
  validation-selected);
* which value is expected to perform better on unseen test participants;
* why the training-selected `k` might fail to generalise.

Add, after the test curve is revealed (widget reflection prompts and/or
notebook prose):

* which curve the test-error curve resembles more: training or validation;
* whether the validation-selected `k` also minimized test MSE on this split;
* why a `k` that looks better on the revealed test curve must not be
  switched to;
* what would happen to the meaning of the test set if this procedure were
  repeated.

Update surrounding prose to distinguish expected generalisation, what
happened on this particular split, what the selection procedure guarantees,
and what it does not: the training-selected `k` is expected to look best on
training data because it was selected there; the validation-selected `k` is
expected to generalise better, but is not guaranteed to minimize test error
on every individual split.

## 5. Rename and collapse the Python reproduction (Section 5)

Retitle the Python reproduction that immediately follows the hidden-test
interaction (the fit/validation tuning cell and the one-time reveal cell) to:

```text
Optional: Reproduce the Tuning Activity in Python
```

Add one sentence directly below the heading:

> The interactive activity above contains the main lesson. Expand this
> optional section if you want to reproduce the analysis in Python.

On the website: collapse the code (input and any output) using the
project's existing `hide-cell` tag convention (as already used for the
Section-3 CV reproduction), with a clear indication near the heading of how
to reveal it. Do not hide the conceptual explanation paragraphs -- only the
code cells collapse.

In the portable notebook: keep this code visible and runnable (the portable
generator already strips `hide-*` tags for every notebook), preserve the
tuning/reveal separation, keep the reveal cell's output un-saved, and make
sure the section title in the portable notebook matches the website's
optional-section title.

## 6. Replace the nested-CV flowchart (Section 6)

Remove the current generic Mermaid flowchart. Replace it with a dedicated,
natively-authored nested-cross-validation split diagram (inline responsive
HTML/CSS, not a raster screenshot, not a copy of any external reference
image) illustrating two levels:

* **Outer cross-validation**: one column per outer fold (matching the real
  `N_OUTER = 5`), one row per outer iteration; the outer-test segment
  (muted yellow) rotates across iterations; the remaining segments are outer
  training data (muted blue).
* **Inner cross-validation**, zoomed from one outer-training set: one column
  per inner fold (matching the real `N_INNER = 5`), one row per inner
  iteration; the inner-validation segment (muted orange) rotates; the
  remaining segments are inner training data (muted green).

Mark directly on/around the diagram: "Choose k" beside the inner-validation
process, "Refit the selected k on all outer-training data" after inner CV,
and "Evaluate the tuning procedure" beside the outer-test fold, so the
conceptual chain (outer training -> inner CV chooses k -> refit -> outer
test evaluates the procedure) is visible.

Requirements: responsive on narrow screens (no clipped labels, no
below-legible fold text -- operation labels and the color legend live in
normal-sized surrounding HTML text, not shrinking SVG/graphic text); readable
in light and dark modes on the website (theme-aware colors via the existing
`custom.css` token pattern, with static fallback values so the same markup
degrades gracefully with no theme CSS at all); accessible text
accompanying the graphic; renders unmodified in both the built website and
the portable notebook (no Sphinx/MyST-only syntax). Add a concise caption:
inner-validation folds choose `k`; outer-test folds evaluate the complete
tuning procedure; outer-test folds never choose `k`.

## 7. Densify the nested-CV candidate grid

Replace `NESTED_CANDIDATE_KS = [5, 15, 30, 50, 75]` with a denser grid in the
10-30 range, auditing a grid such as
`8, 10, 12, 15, 18, 20, 22, 25, 28, 30, 40, 50` and adjusting only for valid
model constraints or a clearly justified simplification (e.g. inner-CV
runtime). Apply the final grid consistently to the nested-CV code cell, the
audit script's `GridSearchCV` configuration, the generated output table, the
nested-CV widget data, the portable notebook, the surrounding prose, the
post-activity questions, and the tests.

Rerun the deterministic nested-CV audit and report the selected `k` for
every outer fold with the new grid. Do not choose seeds or delete candidate
values to manufacture variation -- report the real outcome. If folds now
select different values, show and discuss that. If every fold still selects
the same value, say so plainly ("may differ" rather than "will differ") and
do not claim variation that did not occur.

## 8. Outputs and interpretations

Because the candidate grids change: re-execute the affected canonical
notebook cells, regenerate the portable notebook, regenerate the widget
data/config exports, update the stored audit JSON and any displayed tables,
update numerical assertions in the tests, update prose describing selected
`k` values, and remove stale numbers/outputs left over from the old grids.

Do not change participants, predictors, the age target, the train /
validation / test split, the outer/inner CV seeds, the scaling procedure, or
the primary MSE metric, unless a genuine implementation error is found (none
is expected; if one is found, stop and report before proceeding).

## 9. Tests

Add or update focused Python and frontend/Playwright tests confirming (at
least): the hidden-test candidate grid includes 8, 10, 15, 20, 25, 30, 50
and no stale sparse grid (in particular a bare `12`) remains outside the
nested-CV grid; no test value is present in the DOM/accessibility tree
before locking; the third (test) panel appears only after locking and all
three panels remain together afterward; selected-`k` markers appear
consistently across all three panels; controls lock after reveal and reset
returns to the pre-reveal state; the teaching-only methodological warning is
visible after reveal; post-reveal reflection questions compare train,
validation, and test; the optional Python section carries the exact new
title and is collapsed on the website while remaining visible and runnable
in the portable notebook, whose saved test-reveal output remains absent; the
Mermaid flowchart is gone and the new split diagram shows outer train/test
and inner train/validation with "Choose k" / "Refit" / "Evaluate the tuning
procedure" all present; the nested grid is denser between 10 and 30; the
displayed selected-`k` table matches the regenerated audit; prose says "may
differ" rather than asserting variation that did not occur; no
logistic-regression material was introduced; and the Syllabus page and Word
course overview remain untouched.

## 10. Bounded validation

Run, in order, allowing one diagnosis-and-correction plus one rerun per
failed gate (stop and report, without looping, if a gate still fails after
that):

1. affected audit/export scripts;
2. focused Exercise 4 Python tests;
3. portable-notebook generation check;
4. Exercise 4 portable smoke execution;
5. frontend typecheck;
6. focused unit tests for the hidden-test and nested-CV activities;
7. one production frontend build;
8. one Jupyter Book build;
9. focused widget Playwright tests;
10. focused built-book Exercise 4 tests;
11. light/dark diagram and three-panel plot checks;
12. narrow-screen checks;
13. full Python suite once;
14. full frontend unit suite once.

## 11. Manual verification

Confirm: the denser k controls are usable; the third panel is genuinely
unavailable before locking; the three curves are easy to compare after
revelation; the methodological warning is visible and clear; the optional
Python reproduction does not interrupt notebook flow; the new nested-CV
diagram communicates the two-level structure better than the old flowchart;
selected-k values in prose match the regenerated data; light mode, dark
mode, and narrow layouts work; no unrelated notebook changed.

## 12. Reports

Create `WPs/reports/WP27R_REPORT.md` and
`WPs/reports/WP27R_EXACT_CHANGELOG.md`, covering: the final hidden-test and
nested-CV candidate grids; training-selected, validation-selected, and
(labelled as retrospective teaching information only) test-optimal `k`; the
test/validation curve comparison; selected `k` per outer fold before and
after densification and whether folds actually differed; the diagram
implementation method; which cells are hidden on the website; portable
behavior; regenerated asset sizes; tests/builds run; corrections or reruns;
deviations; and the final branch/SHA. The exact changelog lists every
modified, created, moved, or deleted file.

## 13. Completion

Commit, in order: (1) this specification, (2) the implementation, (3) the
reports. Stop with all work local on `fix/wp27r-validation-refinements`. Do
not merge, push, deploy, monitor GitHub Actions, or begin WP28.
