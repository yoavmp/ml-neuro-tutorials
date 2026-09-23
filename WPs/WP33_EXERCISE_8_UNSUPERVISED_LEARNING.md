# WP33 — Exercise 8: Unsupervised Learning

## 1. Purpose

Build the complete Exercise 8 notebook for **Machine Learning for Neuroscience**.

The notebook introduces:

1. dimensionality reduction and principal component analysis (PCA);
2. clustering as an unsupervised-learning task;
3. K-means as the only worked clustering algorithm;
4. an exploratory neuroimaging research use of PCA and K-means;
5. PCA inside a supervised age-prediction pipeline.

The notebook must remain concise enough for a practice session plus self-study. It should emphasize visual reasoning, interpretation, and correct analysis structure rather than long derivations.

Do **not** introduce hierarchical clustering, dendrograms, AdaBoost, t-SNE, UMAP, DBSCAN, Gaussian-mixture models, or formal cluster-stability analysis in this exercise.

---

## 2. Starting state and branch safety

1. Begin by recording:
   - `git status --short --branch`
   - the current branch name;
   - the current `HEAD` SHA;
   - the tip SHA of `feature/wp32-exercise7-gradient-boosting`.
2. WP33 must start from the completed WP32 Exercise 7 branch, including all of its committed work.
3. Confirm that Exercise 7 exists and that Exercise 8 is still a placeholder before changing anything.
4. Preserve these two pre-existing untracked files if they are still present:
   - `WPs/reports/WP16_ARCHITECT_REPORT.md`
   - `WPs/reports/WP21_DEPLOYMENT_REPORT.md`
5. Do not reset, rebase, stash, clean, delete, or overwrite unrelated work.
6. If the starting state is materially different from the state described above, stop and report the exact discrepancy instead of guessing.
7. Create and work on:

   `feature/wp33-exercise8-unsupervised-learning`

8. Add this specification to the repository and commit it as the initial WP33 checkpoint before implementation.
9. At the end, commit the implementation and reports locally. Do **not** merge, push, deploy, or monitor GitHub Actions. Do not begin WP34.

---

## 3. Existing project conventions are requirements

Inspect the current notebooks, authoring standards, generators, widget registry, tests, and Exercise 7 implementation before editing. Follow the established architecture rather than creating a parallel system.

In particular:

- The main page title must be **Exercise 8: Unsupervised Learning**.
- Use non-Roman exercise numbering.
- Keep **What This Notebook Covers** short and student-friendly.
- Address all prose, headings, code comments, control labels, figure text, questions, and feedback directly to students.
- Use concise language suitable for non-native English speakers.
- Use the established green **Run or Download This Notebook** block, with working Colab and `.ipynb` links.
- Do not tell students to install from the repository or use `requirements.txt`.
- The portable/Colab notebook may contain a small optional package-install cell if required.
- Hide familiar data-loading and preparation inputs on the website while keeping useful outputs visible.
- Keep equivalent code visible and runnable in the portable notebook.
- Use the established blue **Think First** format.
- Avoid duplicate Think First and Reflect questions around the same activity.
- Hide website-only reproduction cells when the live activity already presents the same result. Portable notebooks must retain the runnable code and outputs.
- Ensure light mode, dark mode, narrow screens, and keyboard-accessible controls work consistently.
- Reuse the existing browser-native interactive architecture. Do not require a Python kernel in the published page.

Do not modify the Syllabus page or the Word course-overview document in this WP.

---

## 4. Data and terminology

Use the same prepared ABIDE-II table and the same 1,004 eligible participants with 360 cortical-thickness ROI features used in the existing regression/tree notebooks, unless the repository audit proves that a different canonical prepared table is required.

Reuse existing participant identifiers, feature metadata, anatomical bundle definitions, and data-loading utilities. Do not duplicate these definitions in a new independent file unless the current architecture requires a generated artifact.

Use terminology precisely:

- **PCA is dimensionality reduction and feature extraction.** It creates new features from combinations of the original features.
- Do not call PCA literal feature selection. It does not select a subset of original ROIs.
- K-means finds a partition that minimizes within-cluster squared distances. It does not discover a guaranteed biological truth.
- A visible group in PC1–PC2 is not automatically a clinical subtype.
- External variables such as diagnosis, sex, age, and acquisition site must not be used to create the unsupervised clusters. They may be inspected only afterward to help interpret the result.

---

## 5. Notebook scope and structure

Use the following content order. Section titles may be shortened slightly if this improves consistency with the existing book, but the teaching sequence must remain intact.

### Opening: What This Notebook Covers

State concisely that this is Exercise 8 of *Machine Learning for Neuroscience*. Students will:

1. reduce many brain measurements to a smaller set of principal components;
2. examine what those components represent;
3. group participants with K-means without using a target label;
4. use PCA correctly inside a supervised prediction pipeline.

Do not front-load algorithmic detail here.

### 1. Learning Without a Target

Briefly contrast supervised and unsupervised learning.

Explain that unsupervised methods can help researchers:

- summarize many related measurements;
- visualize participants in a lower-dimensional space;
- explore whether similar profiles form groups;
- generate hypotheses for later validation.

Include a short Think First prompt asking what information an algorithm can use when no target column is supplied.

### 2. PCA: Representing Many Features with Fewer Dimensions

Introduce, in plain language:

- principal components as new axes;
- participant scores on each component;
- feature loadings;
- explained variance;
- reconstruction loss as information discarded by dimensionality reduction.

State that PC1 captures the greatest available variance, PC2 captures the greatest remaining variance while being orthogonal to PC1, and so forth.

Do not include a matrix derivation or eigenvalue proof.

### 3. Interactive Activity — Find the Best Projection

Create a deterministic, browser-native activity using a small two-dimensional simulated dataset with a clear but imperfect correlation.

Required controls:

- a projection-angle slider covering 0–180 degrees;
- a **Show PC1** / reveal control;
- optionally one compact noise or data-shape control only if it materially improves the lesson without making the activity crowded.

Required visual feedback:

1. the original two-dimensional points;
2. the current projection axis;
3. projected/reconstructed positions or visible perpendicular residuals;
4. variance captured by the selected axis;
5. reconstruction MSE or proportion of variance lost;
6. the true PC1 direction only after students reveal it.

Guiding questions should ask students to predict:

- which direction captures the most variation;
- what happens to reconstruction error as captured variance increases;
- why the best axis does not need to match either original feature axis.

The activity must make the relation between variance captured and reconstruction error visually understandable. Do not present the answer before the reveal action.

### 4. PCA with ABIDE-II Neuroimaging Data

Load and standardize the 360 cortical-thickness features. Explain briefly why scaling belongs before PCA even though all features are cortical-thickness measures.

Present:

1. a scree plot;
2. cumulative explained variance;
3. a PC1–PC2 participant plot;
4. signed loadings for a small number of the strongest individual ROIs;
5. loading magnitude summarized across familiar anatomical groups.

For the grouped loading summary:

- reuse the same anatomical group definitions already used in earlier notebooks, such as frontal, parietal, temporal, occipital, and other existing project groups;
- calculate a clearly named magnitude statistic such as mean absolute loading within each group;
- do not sum signed values across a group, because positive and negative values can cancel;
- state that the grouped plot describes loading magnitude, while the individual-ROI plot preserves direction;
- audit that each included ROI is mapped consistently and that group labels match those used previously.

Keep the number of loading plots small. PC1 and PC2 are sufficient unless the data audit identifies a strong educational reason for one additional component.

Add concise interpretation prompts:

- Does one component describe a global cortical-thickness pattern or a more regional pattern?
- Can a component with less explained variance still be scientifically useful?
- What information is hidden when 360 dimensions are shown using only PC1 and PC2?

### 5. Clustering and K-Means

Define clustering conceptually, then introduce K-means as the only worked clustering method in this notebook.

Explain the repeating steps:

1. initialize `k` cluster centers;
2. assign each participant to the nearest center;
3. update each center to the mean of its assigned participants;
4. repeat until assignments stop changing or the stopping rule is reached.

Explain how to evaluate candidate values of `k` using no more than these three considerations:

- inertia and the elbow;
- silhouette score;
- whether cluster sizes and interpretations are scientifically usable.

Make clear that there may be no single objectively correct `k`. A higher silhouette score alone does not establish a biological subtype.

Do not introduce hierarchical clustering or show a dendrogram.

### 6. Research Example — Exploring Neuroanatomical Profiles

Use K-means on retained ABIDE PCA scores as an exploratory research example.

The workflow must be explicit:

1. standardize the cortical-thickness features;
2. fit PCA without using diagnosis or another target;
3. retain a chosen number of PCs;
4. fit K-means in that retained PC space;
5. only then compare the resulting clusters with external participant characteristics.

If a published neuroimaging example is cited, use a verified primary research source and describe it briefly without implying that the present classroom analysis reproduces its scientific conclusions.

Include a visible caution that cluster labels such as 0, 1, and 2 are arbitrary. Do not call the resulting groups autism subtypes.

### 7. Interactive Activity — Explore PCA and K-Means

Build one combined activity rather than separate PCA-count and K-means activities.

Required controls:

- retained PCs: `[2, 5, 10, 20, 50]`;
- number of clusters `k`: integers 2–6;
- several deterministic initialization seeds;
- external characteristic to inspect after clustering: diagnosis, sex, acquisition site, or age.

The selected seed should affect only K-means initialization. PCA must remain fixed for a given retained-component count.

Required outputs:

1. PC1–PC2 participant scatter colored by cluster;
2. selected cluster centers projected into PC1–PC2;
3. inertia across candidate `k` values for the selected retained-PC count and seed;
4. silhouette score across candidate `k` values for the same setting;
5. cluster sizes;
6. an appropriate cluster-composition view for the selected external characteristic:
   - normalized bars for diagnosis or sex;
   - a compact heatmap or normalized composition view for acquisition site;
   - box/violin summaries for age.

State visibly that clustering uses all selected PCs even though the scatter plot shows only PC1 and PC2.

Guiding questions should include:

- Do the elbow and silhouette score suggest the same `k`?
- Does changing the seed change the result? What does that imply?
- Do clusters mostly reproduce acquisition site, diagnosis, age, or none of them?
- If clusters differ in diagnosis proportions, does that prove they are autism subtypes?
- Could structure exist in higher PCs even when PC1–PC2 looks overlapping?

Keep controls and plots readable on a normal laptop and on a narrow page. Avoid an unnecessarily large dashboard.

### 8. PCA Inside a Supervised Prediction Pipeline

Return to age prediction so students can connect this notebook to earlier regression exercises.

Use a correct scikit-learn pipeline equivalent to:

```python
Pipeline([
    ("scale", StandardScaler()),
    ("pca", PCA()),
    ("model", LinearRegression()),
])
```

Requirements:

- Reuse the established eligible cohort and locked outer train/test split used for age prediction in the earlier notebooks where possible.
- Tune only the number of retained components on training/development data.
- Candidate component counts should be a compact set such as `[2, 5, 10, 20, 50, 100, 200]`, adjusted only if a fold-size constraint requires it.
- Fit scaling and PCA inside the pipeline and therefore inside each validation fold.
- Touch the locked test set only after selecting the component count.
- Compare PCA regression with a plain linear-regression baseline using the original standardized features and the same outer split.
- Report test R-squared and MSE without implying that PCA must improve prediction.
- If PCA performs worse, retain and explain the honest result.

Explain concisely:

- PCA preserves directions with high variation in `X`, not directions chosen to predict age;
- a low-variance direction can still contain useful target information;
- fitting PCA before cross-validation leaks information about validation rows even though PCA never sees `y`.

Use a short Think First question asking whether the component count with the greatest explained variance must also give the best age prediction.

Do not add a third interactive activity here. A compact worked pipeline, validation curve, and result table are sufficient.

### 9. Main Takeaways

End with a brief summary:

- PCA creates lower-dimensional combinations of the original features.
- Loadings help interpret what components represent.
- K-means groups similar observations but does not prove natural or biological categories.
- `k` is judged using quantitative evidence and scientific usefulness, not one universal rule.
- In supervised work, preprocessing and PCA must be fitted within the validation pipeline.

Add a small set of exam-style questions. Do not repeat the interactive prompts verbatim.

---

## 6. Interactive implementation requirements

Implement the two activities using the same registry, schema, generated-data, React/TypeScript, Plotly, iframe, and theme-sync conventions as the existing activities.

### Activity A: PCA projection

- Use deterministic precomputed or lightweight browser-side numeric data.
- Do not use a browser Python runtime.
- The answer must remain hidden until the reveal control is used.
- Reset must restore the initial state.
- Projection metrics must agree numerically with an independent Python audit.

### Activity B: ABIDE PCA and K-means explorer

- Precompute the bounded configuration catalogue offline.
- Store only fields needed by the browser.
- Keep the artifact reasonably small and report its compressed and uncompressed size.
- If the full proposed catalogue is too large, first reduce redundant stored arrays or derive display values in the browser. Do not silently remove an educational control.
- Use deterministic sklearn settings and record them in the audit script.
- `KMeans` must set an explicit `n_init` and random state.
- Validate inertia, silhouette, cluster sizes, centers, and external-variable summaries against the Python source calculations.
- Do not optimize clustering against diagnosis or another external variable.

For both activities:

- use meaningful iframe titles and accessible form labels;
- keep Plotly drag layers transparent;
- maintain legible axes and margins in both themes;
- use the established exact theme palette rather than relying on inherited browser colors;
- avoid horizontal scrolling at the book's normal content width;
- show a helpful static/fallback message only if the activity genuinely cannot load;
- produce no widget-related console errors.

---

## 7. Static and portable notebook behavior

1. The built website should prioritize the live activities.
2. Code that reproduces an activity should be collapsed or fully hidden on the website when showing it would duplicate the live activity.
3. The portable notebook must include visible, executable Python equivalents for both activities.
4. Portable controls do not need to reproduce the React interface. Clear parameter variables that students can edit are sufficient.
5. The portable notebook must run from top to bottom in a clean environment after its optional package-install cell is skipped in the project environment.
6. Generated notebooks must remain generated through the established script rather than manually drifting from their source.

---

## 8. Audit scripts and reproducibility

Create or extend focused audit scripts following current repository practice.

At minimum, independently verify:

- eligible participant and feature counts;
- the 360-feature cortical-thickness set;
- standardized PCA explained-variance ratios;
- cumulative explained variance;
- strongest individual ROI loadings;
- grouped mean absolute loading calculations;
- every K-means catalogue configuration;
- cluster sizes sum to the full eligible sample;
- silhouette is computed only when mathematically valid;
- external variables were excluded from PCA and clustering inputs;
- the supervised PCA pipeline fits scaler and PCA inside validation folds;
- the locked test set was not used for selecting the component count;
- reported R-squared and MSE reproduce exactly from the committed code and data.

Do not choose component counts, `k`, or displayed examples because they make diagnosis separation look impressive. Record any educational display defaults before inspecting external-label separation, or justify them using target-free criteria only.

---

## 9. Required tests

Add focused tests that protect the educational and technical requirements above.

### Notebook/content tests

- Exercise 8 replaces the placeholder and appears in the correct TOC/sidebar position.
- Title capitalization and exercise number are correct.
- What This Notebook Covers is concise.
- No hierarchical clustering, dendrogram, t-SNE, UMAP, DBSCAN, GMM, or AdaBoost teaching section appears.
- PCA is described as feature extraction/dimensionality reduction, not literal feature selection.
- Familiar data-loading inputs are hidden on the website.
- Website reproduction cells for live activities are hidden/collapsed as intended.
- Portable equivalents remain visible and runnable.
- Colab and download links target Exercise 8.

### Numeric tests

- PCA metrics and loading summaries match the audit source.
- Grouped loading magnitudes use absolute loadings and do not use signed sums.
- K-means configs and summaries match the audit source.
- External variables are not used to generate clusters.
- Supervised results match the committed pipeline and fixed split.
- No PCA/scaling fit occurs outside the supervised validation pipeline.

### Frontend/unit tests

- config/schema parsing;
- initial rendering;
- every control updates the intended outputs;
- reveal/reset behavior for Activity A;
- component-count, `k`, seed, and external-characteristic behavior for Activity B;
- plot trace and legend semantics;
- responsive layout;
- theme synchronization.

### Browser tests

- standalone activity checks in light and dark mode;
- built-book Exercise 8 checks in light and dark mode;
- reload while dark preserves correct first paint;
- Plotly paper, plot, grids, labels, data marks, and drag layers follow the established theme contract;
- no new runtime or console errors attributable to Exercise 8;
- narrow viewport remains usable;
- keyboard operation works for native controls.

Include dedicated built-book dark-mode coverage for both new Exercise 8 activities rather than relying only on the shared visual-policy test.

---

## 10. Bounded validation plan

Avoid the long verification loops that delayed earlier WPs.

Run gates in this order:

1. focused audit-script tests;
2. focused Exercise 8 notebook/content tests;
3. focused portable-notebook generation and `--check`;
4. portable Exercise 8 smoke execution outside the repository tree;
5. focused frontend unit tests and typecheck;
6. one frontend production build;
7. focused standalone Playwright tests for the two new activities;
8. one Jupyter Book build;
9. focused built-book Exercise 8 Playwright tests, including dark mode;
10. the full Python suite once;
11. the full frontend unit suite once;
12. manual visual inspection of the final built Exercise 8 page in light mode, dark mode, and a narrow viewport.

Rules:

- Do not repeatedly rerun an already-passing full suite.
- If a gate fails, identify the root cause, make one bounded correction, and rerun only that gate once.
- If it still fails, stop and report the failure instead of entering a repair loop.
- Do not use arbitrary long sleeps. Use event/state-based waits. A short, bounded animation wait is permitted only if the report explains why an event-based signal is unavailable.
- Do not run or watch GitHub Actions because this WP does not deploy.
- Do not wait for external state after the local work is complete.

Also extend the portable smoke-test registry so Exercises 5–8 are covered by the normal automated smoke command, unless inspection shows that a currently active WP already corrected this gap. Do not rewrite working smoke infrastructure unnecessarily.

---

## 11. Manual review checklist

Confirm visibly that:

- the notebook is shorter and less dense than Exercise 1;
- the introductory text is concise;
- the PCA projection activity does not reveal PC1 prematurely;
- the relation between captured variance and reconstruction error is understandable;
- the ROI and anatomical-group loading plots have readable labels;
- anatomical group names match prior notebooks;
- the clustering dashboard is not overcrowded;
- selecting different retained-PC counts, `k`, seeds, and external characteristics produces coherent changes;
- acquisition-site composition can be inspected without implying that site is a target;
- the supervised PCA section does not leak test or validation information;
- all hidden-cell behavior is correct on the website and portable notebook;
- both interactive activities look correct in published-style dark mode, not only in a local light page.

---

## 12. Reports and stopping condition

Create:

- `WPs/reports/WP33_REPORT.md`
- `WPs/reports/WP33_EXACT_CHANGELOG.md`

The report must include:

1. overall success or failure;
2. starting branch and SHA;
3. final branch and SHA;
4. exact notebook sections created;
5. both activities and their controls;
6. ABIDE participant/feature counts;
7. PCA explained-variance and loading-summary audit results;
8. K-means catalogue ranges, defaults, and artifact sizes;
9. supervised PCA candidates, chosen component count, and final metrics;
10. every validation gate with command, duration, and result;
11. any failure, retry, deviation, or judgment call;
12. confirmation that the Syllabus and Word overview were untouched;
13. confirmation that nothing was merged, pushed, deployed, or monitored through GitHub Actions;
14. final `git status --short --branch` and concise decorated log.

The exact changelog must list every added, modified, renamed, or removed file and explain its purpose.

After committing the reports, stop. Return a short summary suitable for a user who will not read the full reports, and clearly flag anything that requires a decision before a later correction or deployment WP.
