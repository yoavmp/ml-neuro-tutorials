# WP47 — Active Exercise 8: Unsupervised Learning

## Authority and scope

Migrate **Exercise 8: Unsupervised Learning** to the editable, downloadable JupyterLite notebook format used for Exercises 1–7. Teach PCA and K-means primarily through student code, short prompts, a native interactive activity, and checked conceptual questions. Preserve the meaningful existing data recipe and approved findings after auditing them; trim repetitive lecture prose. The course author will personally test the downloaded notebook in **real Google Colab later**. Do not claim that Claude has done a real Colab test.

Before changing code, read the current Exercise 8 notebook, all its old figures/widgets/data and relevant audits **in full**, plus `WPs/reports/WP46_REPORT.md`, `WP46_EXACT_CHANGELOG.md`, the WP41 maintainer guide, the Exercise 3–7 generator and transition-page patterns, and the current manifest/build setup. The user supplied a reference image for a two-panel PCA figure (specified precisely below). Audit the actual dataset, input features, preprocessing, split, sample counts, figures, numerical results, and widget conclusions. Inspect Git status and branch ancestry; checkpoint the actual state and work on a dedicated WP47 branch based on the latest reviewed work with Exercise 7. Preserve unrelated changes; never touch `Homework_Materials/`.

**Scope of verification:** Exercise 8 and directly changed support code only. Do **not** run full Python/browser suites or tests of earlier notebooks in this WP. The author wants one comprehensive suite later, when all notebooks are migrated and a separate deployment WP is prepared. If a shared change would require retesting Exercises 1–7, avoid that shared change or document the unresolved integration risk for the later deployment WP. No merge, push, deployment, or production change here.

## Common notebook contract

- Use an authoritative generator producing student, portable/downloadable, and private reference notebooks plus the Exercise 8 transition page; register it in the manifest and navigation consistent with the current locally migrated exercises. Keep original versions recoverable in Git. Provide a clear first-run instruction, real student code cells, editable written answers, and a download of the **current** student notebook, including edits.
- JupyterLite runs supplied and student code with no install cell. The downloaded `.ipynb` must work without checking out or accessing this potentially private course repository: use the established same-origin data path and checksummed independent public fallback as appropriate. Add a minimal conditional Colab setup cell only if needed; the author will verify real Colab later. Do not link to private course files or ask students to install from repository `requirements.txt`.
- Use **bold conceptual questions**, no `YOUR ANSWER HERE` in written-answer cells; use `# YOUR CODE HERE` for genuine student code. State each task's required variable names **on the last line of its instructions**, repeat them in the code stub, and avoid overwriting variables from earlier tasks. Supplied plots and checks must consume actual student results, never hidden reference solutions. An untouched Run All should show localized “not complete yet” guidance without cascading errors; the private teacher-completed copy should run to the end.
- The requested activity uses native `ipywidgets`/Matplotlib or similarly portable Python controls, not an iframe. Checked question options must wrap at 390px and show meaningful feedback. Keep figures readable in light/dark themes and portable in the `.ipynb`.

## Content sequence

### 1. Data and learning without a target

Give the import and ABIDE modelling-table loading code in full. Use the existing approved brain-feature set (audit whether this is the same 360 cortical-thickness `fsCT_` columns used in nearby exercises), with informative shapes and a short statement of the analysis question. Prepare participant-level age, diagnosis, sex, and scan-site fields **only for later coloring/interpretation**; never use these labels as inputs to exploratory PCA or K-means. Handle missing/non-numeric values consistently with the established data recipe and explain any exclusions. A brief “Learning Without a Target” introduction should state that PCA summarizes variation in the predictors and K-means groups points by feature similarity, not by known diagnosis.

Add two checked multiple-choice questions, placed near this introduction or when students first color the plot:

1. What can an unsupervised analysis help us explore (dimensions, patterns, possible groups), without promising recovery of diagnostic classes?
2. Retain/adapt the old question: **“With no target column supplied, what information can an unsupervised algorithm actually use to group or summarize participants?”** The correct explanation is predictor patterns/distances/variance, not hidden access to age, diagnosis, sex, or site. Distinguish coloring a completed plot for interpretation from fitting the unsupervised model on those labels.

### 2. PCA: Representing Many Features with Fewer Dimensions

Ask students to implement PCA using scikit-learn (`StandardScaler` then `PCA` is the suggested path, with suitable imports and a compact hint). Use a consistent student variable name **`X_pca`** for the transformed participant-by-component scores; also retain a distinct fitted **`pca_explore`** for `explained_variance_ratio_` and `components_`, and the training-independent standardized brain predictors as needed. Fit the exploratory PCA to **brain predictors only**. If another valid implementation differs because of scaling or PCA settings, explain rather than falsely asserting every numerical deviation is wrong. A reference/test copy completes the task; student code remains blank.

Ask students to make the **two-panel explained-variance figure** shown in the author's attached reference image. Give the image as a portable embedded reference if it is available in the local WP materials; the specification is authoritative even if the image is not copied into the repository:

- Left: scree bars for PCs **1–15**, x-axis PC number, y-axis individual **explained variance ratio** starting at zero.
- Right: cumulative explained variance for PCs **1–50**, x-axis number retained, y-axis percentage **starting at zero**, with a dashed **50%** guide and optional annotation for PC1. The provided image visually shows PC1 around 36.1% and roughly 70% cumulative by PC50; **calculate from this notebook's actual approved data and preprocessing** and never hardcode those illustrative values. Use the same fitted `pca_explore` and a sufficient number of components. Make both plots legible at notebook/mobile width. A supplied sanity check can verify component count, variance range, and correct cumulative construction, but must allow reasonable plotting styles.

Ask students to plot a scatter of **PC1 versus PC2**, colored by age with an explicitly labeled continuous colorbar where **brighter means younger** (for example a suitable reversed sequential map). Suggest trying diagnosis, acquisition site, or sex as alternative **post-fit colors**, with categorical legends and sensible handling of many site levels; these are observations, not PCA inputs. Ask one short interpretation question on what separation (or lack of separation) can and cannot establish. Do not imply that large variance or visible color gradients equal good prediction.

Ask students to inspect **loadings on PC1 and PC2** by plotting readable top positive/negative or top absolute-loading brain features for each, preserving coefficient sign and mapping abbreviated labels to the underlying feature names. Explain briefly that PCA loading signs can flip without changing the underlying solution; avoid declaring an individual ROI causal or diagnostic. Require stable, distinct output names (`pca_variance_fig`, `pca_scatter_fig`, `pca_loadings_fig` or reviewed equivalents) and keep the same `X_pca` used below.

### 3. K-means on the student's PCA result

Students run K-means using **their existing `X_pca`**. Give a predeclared, small choice of retained PCs (`N_CLUSTER_COMPONENTS`, drawn by slicing `X_pca`, not by secretly refitting a new PCA) and a manageable candidate list of cluster counts, with fixed `random_state` and explicit `n_init` for reproducibility. They compute and plot **inertia** and **silhouette** versus cluster count, correctly excluding `k=1` from silhouette. Silhouette calculation can be bounded with an honestly labeled fixed sample size/seed if full pairwise computation is too slow in Pyodide; audit and report any resulting difference from legacy scores. Supply checks of shapes, finite scores, and trends without forcing an invented single “correct” k. Add one checked question or brief reflection: inertia decreases as k increases, and silhouette may help but does not prove that clusters reflect diagnosis. Use required names such as `kmeans_results`, `kmeans_inertia_fig`, `kmeans_silhouette_fig` on the last line of the task instruction.

### 4. Interactive Activity — Explore PCA and K-Means

Port the existing activity into a native notebook control, preserving its meaningful choice of component count and/or cluster count and its established interpretations. It must operate on the same approved table and make any fitting or recomputation visible; label if it uses a fixed example or a cached projection rather than the student's `X_pca`. Prefer reusing their completed PCA output when it is needed for the learning objective, but provide helpful guidance when that student task is incomplete. Bound recomputation and verify controls actually change the plot/metrics in a live JupyterLite browser. Keep one concise question tied to the activity.

### 5. Using PCA in a Supervised Pipeline

Briefly contrast exploratory unsupervised PCA above with PCA as a preprocessing step for **age prediction**. Supply the existing scikit-learn pipeline pattern in complete runnable code, with reviewed parameter names/settings:

```python
Pipeline([
    ("scale", StandardScaler()),
    ("pca", PCA()),
    ("model", KNeighborsRegressor()),
])
```

Use the pre-migration notebook's audited comparison of KNN with **PCA components** versus KNN using **all original brain features**, printing MSE and R² side by side on the same held-out participants and with fair, documented fixed/tuned settings. Crucially, fit **both scaling and PCA on training data only**, inside the predictive pipeline; do **not** reuse the Section 2 `pca_explore` fitted to all participants. Keep the final test set locked during any component-count or k selection. Use the observed results, including when PCA does not improve prediction. Add a checked question about why exploratory full-data PCA must not be reused to score the held-out test set. End with a short practical takeaway.

## Multiple-choice answer visibility

The current student-visible question cell shows code such as `correct_indices={0, 2, 4}`. Improve **Exercise 8's normal student view** so each question cell calls a question ID or similarly short wrapper and displays prompt/options/feedback without printing or displaying the answer key in that visible cell. Put question definitions and grading setup in a separate, **collapsed-by-default** support cell or another portable bundled implementation; verify actual initial rendering, execution, reveal/collapse behavior, and question feedback in JupyterLite. Check how the downloaded notebook presents this in Colab when the author later tests it. Do not modify the shared question system or older notebooks in this WP, because the author has explicitly deferred earlier-notebook tests.

State the security limit honestly in the report: a fully downloadable, offline, editable notebook must contain enough information to check answers locally, so a technically curious student can inspect its source or runtime and recover them. Collapsing or separating the setup improves the student experience; it is **not secure answer protection**. Do not use obfuscation or claim the indices are secret. Record a future shared migration option for Exercises 1–7 after the course-wide testing gate, without implementing it now.

## Focused verification and time discipline

Test only Exercise 8 and directly changed helpers, using the actual generated student and private completed notebooks. Verify data-loading portability from an empty directory with no repository assets, numeric/plot parity with the audited legacy notebook, student blanks and checks, no-cascade template, independent Section 5 train-only PCA, same `X_pca` flowing into K-means, output-name contract, and answer-key visibility. Build the combined Book+Lite artifact as needed to inspect Exercise 8 locally, but do **not** run old-notebook Python/browser specs or a course-wide suite. Run a small Exercise 8 Playwright smoke and a teacher-completed path in real Chromium: actual kernel, each widget/MC, mobile width, dark mode, persistence/edit/download, Reset/Back, and no unexpected error cells. Capture genuine limitations rather than weakening assertions.

For every long command: state the expected duration and a **hard timeout before starting**; keep stdout/stderr or a log and record process/exit status. Check progress at sensible short intervals (about 2–5 minutes), report a failure or stalled process promptly, and stop it once the agreed budget is exceeded. Do not leave a silent process running for hours or require the author to ask whether it has failed. Run a focused test once; after a code fix, rerun **only the affected test**. If a browser test takes roughly 15 minutes or more, investigate and reduce redundant cold starts/work before repeating it. Never rerun a costly suite merely to hope for a pass. Report every command exceeding 5 minutes, its elapsed time, outcome, and reason for any rerun.

Prepare an **uncommitted, private teacher-filled copy** of the real portable Exercise 8 notebook, the unfilled actual student download, and a short Colab checklist for the author (fresh upload, Run all, data/metrics, variance/PC/loading/clustering figures, every MC response, widget controls, edit/download). Mark **real Colab pending** until the author reports results. Do not commit teacher solutions in public student paths.

Commit `WPs/reports/WP47_REPORT.md` and `WPs/reports/WP47_EXACT_CHANGELOG.md` locally. Record actual checkpoint/final SHAs, files, old/new numerical results and deviations, focused tests/build/browser evidence, test durations, prose cuts, answer-key visibility behavior, Colab limitation, and author decisions. Return a short course-author summary and local review instructions. Do **not** merge, push, deploy, or start WP48.
