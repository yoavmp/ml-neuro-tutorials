# WP65 — Exercise 7 Interactive Activity 2: precompute the boosting-parameter grid offline

## Authority and trigger

The course author asked to update Exercise 7's "Interactive Activity 2:
Explore the Boosting Parameters" so it no longer fits models live. Every
time that activity's cell ran, it fit all 18
(`EXPLORER_LR_GRID` x `EXPLORER_DEPTH_GRID`) `GradientBoostingRegressor`
models via `staged_predict`, inside the notebook's own cell, in-browser
(Pyodide/WASM) — correct but slow, and wasteful to repeat every time a
student reruns the cell or just scrolls back through "Run All Cells."

## Execution contract

1. Precalculate the full (learning rate x tree depth x tree count) grid
   offline, in a reproducible script, using this notebook's established
   data (`book/lite/files/data/abide_age_brain.csv`, same natural fsCT_*
   column order via its own sidecar manifest), its established split
   (Section 1's `wp46-104-load`: `train_test_split(..., test_size=0.25,
   random_state=42, stratify=groups)` then `train_test_split(...,
   test_size=0.25, random_state=7, stratify=groups_train)`), and its
   established model settings (`GradientBoostingRegressor(learning_rate,
   max_depth, n_estimators=max(EXPLORER_N_TREES_GRID), random_state=42)`
   fit once per (learning_rate, depth) pair, every tree-count step read
   from that one fit's `staged_predict`, exactly as the activity always
   computed it). Never read the locked outer test set.
2. Commit the small cache this script produces, and the script itself.
3. Load the cached values in the notebook's first, collapsed setup cell,
   as plain data — the setup cell must not fit any model.
4. The Activity 2 cell itself must only build controls (dropdowns, slider)
   and draw plots from the cache; rerunning it must fit no model.
5. Embed the cache in the portable notebook (and the JupyterLite template
   and the reference notebook) as a literal, the same way this notebook
   already embeds its feature-column list, so it works in Colab or a bare
   downloaded `.ipynb` with no repository file dependency at notebook-run
   time.
6. Replace Activity 2's intro markdown with this exact, concise
   student-facing wording: "These results were calculated ahead of time
   from the fitting and validation sets so the activity opens quickly. The
   locked test set was not used. Changing a control displays saved results
   rather than training a new model." Make clear that the curves shown
   reflect this notebook's *original* fitting/validation split, even if a
   student has since changed that split.
7. Author every change in `scripts/generate_exercise_07_notebook.py` (and
   the new cache-generation script), regenerated into every derived copy —
   never a hand-edit of a generated `.ipynb`. No change to Exercises 1-6 or
   8-12, or any shared/platform file, unless proven necessary.
8. Verify the plots and controls still match the current activity (same
   two-panel figure: training/validation MSE vs. tree count on a log
   x-axis, and a validation-MSE heatmap across learning rate x tree count;
   same dropdowns/slider; same metrics line). Measure the setup cell's and
   the Activity 2 cell's own run times in a real local JupyterLite build
   (not estimated), and run the focused Exercise 7 checks
   (`test_exercise_07_lite_notebook.py`,
   `test_exercise_07_reference_execution.py`,
   `test_exercise_07_transition_page.py`, the generator's own `--check`,
   plus a new test for the cache script and artifact). Do not run or wait
   on the full project-wide suite here — the required release gate
   (`.github/workflows/deploy.yml`) covers that on push.
9. Push to `main`, watch the deploy workflow to completion, and verify the
   live activity (controls, plots, and the new description text).

## Required report

Write `WPs/reports/WP65_REPORT.md` with: the cache-generation script and
its committed artifact (with a cross-check against an already-audited
number so the offline computation is verified, not merely asserted), the
notebook-generator diff, the exact timings measured for the setup cell and
the Activity 2 cell (ideally a before/after comparison against the
previous live-fit cost), the focused test/e2e results, the push/deploy run
id and conclusion, and live-page verification.
