# WP53 — Polish Exercises 3–9 and deploy

## Authority and starting point

Use the current `main` after WP52 and read `WPs/reports/WP52_REPORT.md`, `WP52_EXACT_CHANGELOG.md`, and the WP50 maintainer guide before editing. Exercise 9 is live, and Exercises 1–9 are the published JupyterLite course. This WP authorizes the fixes below, their necessary generated notebook/download changes, a single production release, and live verification. Do not migrate or publish Exercises 10–12. Preserve established data, splits, model recipes, and measured results unless a requested fix necessarily changes one; document any such difference with direct execution evidence.

The user-provided replacement image is packaged with this WP as `WP53_nested_cv_diagram.png`. Add it to the project's source assets under a descriptive name, wire the Notebook 4 generator to the asset, and confirm the built notebook displays the new image at a readable size. Use this image, rather than redrawing the old overlapping diagram. The other two user screenshots show (a) the Pyodide/threadpoolctl warning and (b) Exercise 9's PCR/PLS legend and labels colliding with the colorbar.

Work on a feature branch with a pre-work checkpoint and clean starting tree. Edit the generator/source of each notebook, not only a generated `.ipynb`. Regenerate student, portable, and reference outputs as the repository requires. Keep instructor answers out of student-facing visible cells.

## Notebook-specific corrections

### Exercise 3 — Classification and metrics

1. The data/setup cell currently appends `SEX` and `SITE` to an already highly fragmented `table`, producing pandas `PerformanceWarning` at those assignments. Construct the table in a batch (`concat`/one new DataFrame/copy as appropriate), preserving column values, names, order where relevant, row alignment, numeric matrix, and established model scores. Verify this exact cell no longer emits the warning in JupyterLite.
2. In “Fit the model,” an unfinished student activity currently raises a `RuntimeError`. Replace that expected incomplete-work path with a short, friendly printed instruction of the same substance. A completed student solution must still fit and expose the same downstream variables; unexpected programming errors must not be silently swallowed. Confirm a blank-template run has no red traceback here and a teacher-filled run works.

### Exercise 4 — Validation and cross-validation

1. In “One Split or Several Folds?” replace the low sample-size choices with a progression beginning at **150, 250**, then larger sizes. Adjust widget defaults, allowed values, explanatory copy, and any dependent tests consistently; retain the visual lesson about split variability. Change the checked question's example from “30 or 50 participants” to “150 or 250 participants.”
2. Replace the nested-CV illustration with the packaged `WP53_nested_cv_diagram.png`. Display it at useful notebook width, with no clipped or overlapping labels at normal desktop and 390px viewport widths. Keep alt text/description that explains outer assessment versus inner tuning.

### Exercise 6 — Decision trees

1. Make the regression-tree diagram genuinely readable at notebook width and when zoomed. Prefer vector/SVG or a suitably high-resolution, properly cropped rendering with larger node text; changing CSS width on the same tiny raster alone is insufficient. Check desktop and narrow layouts.
2. Replace visible **“Think first:”** with **“Think:”**.
3. In “Build a Greedy Tree,” eliminate the `No artists with labels found to put in legend` warning. Only request a legend when labeled artists exist, or give intended plotted artists explicit labels.
4. Changing between brain measure 1 and 2 must immediately update the candidate-threshold figure. Changing the numeric threshold must immediately update the threshold line in the left plot. “Lock in answer” remains the action to commit/check the student's choice, not a prerequisite for preview. Check both directions and repeated edits for stale output/state.
5. In the “A second look…” graph, replace “(development data only)” with **“train-val data only”**, and “development = 753” with **“train-val = 753”**. Keep the actual counts unchanged.
6. In “One tree or many?” show the full **“Number of trees”** widget label. Allocate enough label width in the actual JupyterLite output and a narrow viewport.

### Exercise 7 — Boosting

In “Interactive Activity 1: Build a Boosted Model,” show the entire checkbox label **“Show the newest tree's correction after scaling by the learning rate”**. Let long labels wrap or give them sufficient layout width. Check the notebook at desktop and mobile width without hiding other controls.

### Exercise 8 — Unsupervised learning

1. Remove the commented complete PCA solution from the student blank. Leave only short, non-executable direction, for example:

   ```python
   # YOUR CODE HERE
   # Xs = ...      # scaled X
   # X_pca = ...   # PCA applied to Xs
   ```

   Keep any required subsequent state/checks intact. The student must still choose how to fit/transform PCA.
2. Replace the wording “Required output name: `pca_variance_fig`” with “Your figure should be defined under the name `pca_variance_fig`.” Apply the same wording to `pca_scatter_fig` and `pca_loadings_fig`, preserving the names that later cells/tests use.
3. The K-means interactive currently emits a Pyodide `threadpoolctl` warning about deprecated `JsProxy.as_object_map()`. Diagnose which call triggers it in the browser and fix the underlying compatibility/use where practical (dependency/API choice or targeted application code). Do not hide all warnings globally or monkey-patch installed packages without a justified, tested reason. Document a narrow unavoidable upstream limitation honestly if it cannot be fixed without breaking the models; the goal is warning-free student output.

### Exercise 9 — Advanced Models

1. In the PCR-versus-PLS interactive, the legend and labels/annotations near the right side overlap the colorbar. Reserve enough margin and move the legend and other right-side elements to the right or outside the data axes so **PC1 fixed, PLS direction, true signal**, and the color scale are all visible at desktop width. Check a narrow viewport and interaction after changing the control.
2. Change “This activity uses entirely synthetic data -- not ABIDE -- clearly labeled above” to “This activity uses entirely synthetic data -- not ABIDE.”
3. In the SVR student task replace the wording “not run here, since Pyodide has no GPU/multiple threads and” with **“we skip that here for computational reasons.”** Edit the full sentence for natural grammar; do not make an unsupported blanket claim about Pyodide.

## Course-wide checks and corrections (published Exercises 1–9)

1. Review every visible “YOUR CODE HERE” cell in generated **student** notebooks. A hint or partial scaffold is fine, including some provided lines for a hard exercise. If a commented block gives a complete executable answer to its own task, remove the solution or pare it back to partial guidance. Keep reference/teacher copies correct, and retain expected variable names and useful graceful checks. Report which cells were actually changed; do not rewrite good hints just to satisfy the audit.
2. Review all checked multiple-choice and multiple-select questions. Assign a **fixed, varied ordering once per question when generating the notebook**, rather than reshuffling on each display or click. Preserve each answer's identity, feedback, hidden key, and correctness, including multi-select. Do not permute a question whose options have meaningful ordered labels or depend on sequence (e.g. deliberately labeled A/B/C steps). Ensure the correct choice is not systematically in the first position across the course. Use deterministic per-question seeds or explicit permutations, not one shared runtime shuffle; tests should verify stable display order and actual feedback. A student should not see correct indices in an ordinary visible code cell.
3. Review the native interactive activities in Exercises 1–9 for the red/pink warnings seen on real JupyterLite. Run each activity once and change representative controls, capturing the browser kernel output, including stderr/warnings. Fix sources using recommended supported APIs or proper widget layout rather than suppressing whole warning classes. At minimum cover the specific Exercise 6 legend and Exercise 8 threadpoolctl warning above, plus any warnings you actually encounter. Record widget, message, cause, and fix (or a documented upstream limitation) in the report. Do not claim the whole course is warning-free based solely on static inspection.

## Verification and time discipline

Follow WP50's classifier and actual changed-file scope. Because this WP deliberately touches several notebooks and may touch shared question/widget code, expect a `full` release classification if that is what the classifier returns; do not change the classifier or mislabel the diff just to obtain a fast gate. Scope local work intelligently:

- First run generator/structural checks for edited notebooks and a narrow teacher-filled execution check for changed code and established metrics. Run the new answer-order and student-hint checks on Exercises 1–9. Check blank and filled paths where a graceful guard changes.
- Build Jupyter Book + JupyterLite **once** from the final source, then use the same build for one browser sweep of the affected notebooks and all published interactive activities. Check controls, warning output, responsive layouts, and changed figures/text. Exercise 9's model section can use a focused browser test rather than repeatedly rerunning expensive SVR benchmarking. Add/adjust focused automated tests only for behavior that changed.
- Do not repeatedly run full Python/Playwright suites locally to chase unrelated failures. If the classifier or workflow selects the full CI gate, allow that single authoritative CI run. After any concrete failure, inspect its artifact/log, fix that cause, and rerun the smallest useful local reproducer before a further push. One additional deploy run may be needed for a verified correction; do not make speculative CI pushes.
- Monitor every long-running command and GitHub Actions run to completion without waiting for the course author to prod you. Record the process/session ID, poll on a sensible interval, inspect exit status and failed logs immediately, and send concise progress updates roughly every 10–15 minutes during long gates. A quiet terminal is not proof of success. Do not leave a background test unexamined for hours. Report duration once per substantive run, not repeated redundant timings.

Verify generated notebook contents, teacher-filled execution, and the compiled JupyterLite routes. Check no regressions to the known reference metrics when only presentation changes were intended. Check the downloaded `.ipynb` remains self-contained/Colab-portable to the extent automated verification can prove; explicitly distinguish this from a real Colab run, which the course author may do later.

## Release and acceptance

When local checks are green, commit, merge/fast-forward to `main` as appropriate, push **once**, and follow the actual CI classification. If CI fails, diagnose and fix it rather than stopping at the first failure or repeatedly guessing. After a successful publish, confirm the `gh-pages` deploy marker matches the pushed source SHA. On the live site, confirm Exercises 1–9 open, the specific corrected notebook routes/downloads return 200 and contain the changes, the replacement image loads, and Chapters 10–12 remain unpublished. Check representative visible fixes live in Exercise 3/4/6/7/8/9; note that automated browser checks against the built app are distinct from live interactive checks if the latter are not feasible.

Write `WPs/reports/WP53_REPORT.md` and `WP53_EXACT_CHANGELOG.md` with a checklist for every numbered request, the question permutations/answer validation method, warning sweep results, tests and timings, real CI run and gate classification, live links/status, any unresolved issue, and the exact git state. Keep reports behind `WPs/**` so report-only commits do not trigger another deploy. Do not report deployed until the production workflow and live marker prove it.
