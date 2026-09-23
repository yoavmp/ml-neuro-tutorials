# WP34 — Revise Exercise 8 and Build Exercise 9: Advanced Models

## 1. Purpose

This work package has two connected goals:

1. revise Exercise 8 so it demonstrates PCA with a previously learned model rather than introducing principal component regression (PCR);
2. replace the Exercise 9 placeholder with **Exercise 9: Advanced Models**, introducing PCR, partial least squares (PLS), support vector machines, and kernels through concise code examples, two interactive activities, and a fair comparison on ABIDE-II age prediction.

The notebook follows a lecture covering PCR, PLS, SVMs, and kernels. It should emphasize practical distinctions, model choice, and test-level conceptual understanding rather than repeating full prediction-pipeline instruction.

---

## 2. Starting state and branch safety

1. Record:
   - `git status --short --branch`;
   - current branch;
   - current `HEAD` SHA;
   - the tip SHA of `feature/wp33-exercise8-unsupervised-learning`.
2. WP34 must start from the final committed WP33 branch tip, including the complete Exercise 8 implementation and reports.
3. Resolve and record the literal WP33 final report-commit SHA. WP33's report omitted that exact value; do not modify the WP33 report merely to fill it in.
4. Confirm before editing that:
   - Exercise 8 is a real notebook;
   - Exercise 9 is still a placeholder;
   - Exercise 8 currently contains the PCA-plus-linear-regression supervised section that this WP must replace.
5. Preserve these pre-existing untracked files if present:
   - `WPs/reports/WP16_ARCHITECT_REPORT.md`
   - `WPs/reports/WP21_DEPLOYMENT_REPORT.md`
6. Do not reset, rebase, stash, clean, delete, or overwrite unrelated work.
7. If the starting state differs materially from this description, stop and report the discrepancy.
8. Create and work on:

   `feature/wp34-exercise9-advanced-models`

9. Add this specification to the repository and commit it as the initial WP34 checkpoint before implementation.
10. Commit the implementation and reports locally. Do **not** merge, push, deploy, run or monitor GitHub Actions, or start WP35.

---

## 3. General authoring requirements

Inspect the current authoring standards, Exercises 4–8, portable-notebook generator, audit scripts, widget architecture, theme policy, and tests before editing.

Maintain all established project conventions:

- student-facing, concise, self-learning language;
- capitalized title and non-Roman numbering;
- short **What This Notebook Covers** opening;
- green **Run or Download This Notebook** block with correct Colab and `.ipynb` links;
- blue **Think First** blocks;
- no duplicate Think First/Reflect prompts;
- familiar data-loading inputs hidden on the website with useful output visible;
- long reproduction/comparison code hidden or collapsed on the website but visible and runnable in the portable notebook;
- no student-facing repository installation instructions;
- browser-native interactive activities requiring no Python kernel;
- working light mode, dark mode, narrow layouts, keyboard controls, and theme-aware Plotly output.

Do not modify the Syllabus page or Word course-overview document.

---

# Part A — Exercise 8 correction

## 4. Remove PCR from Exercise 8

Exercise 8 must remain about unsupervised learning, PCA, and K-means. PCR should first appear in Exercise 9.

In Exercise 8:

1. Remove the current Section 8 PCA-plus-`LinearRegression` example.
2. Remove all references to:
   - principal component regression;
   - PCR;
   - `LinearRegression` as the model following PCA;
   - the existing PCA-regression versus ordinary-linear-regression comparison;
   - its component-selection results and metrics.
3. Update:
   - **What This Notebook Covers**;
   - section text;
   - summary;
   - questions;
   - code comments;
   - audit output;
   - portable notebook;
   - tests;
   - any generated or cached output that depends on the removed analysis.
4. A repository-wide student-facing search must confirm that PCR is introduced first in Exercise 9, not Exercise 8.

## 5. Replace it with PCA plus KNN regression

Replace Exercise 8 Section 8 with a concise section titled approximately:

`## 8. Using PCA Before a Model We Already Know`

Use **KNN regression to predict age** from ABIDE-II cortical-thickness data.

This is the preferred model because students already know KNN and PCA directly addresses a weakness of distance-based learning in a high-dimensional space.

Required teaching points:

- KNN calculates distances between participants.
- In hundreds of dimensions, many irrelevant or noisy directions can make distances less informative.
- PCA can replace the 360 original features with a smaller set of component scores before KNN.
- Scaling and PCA must be fitted inside the validation pipeline.
- PCA remains feature extraction, not literal feature selection.
- The number of retained PCs and `k` are model parameters.
- PCA is not guaranteed to improve prediction, because high-variance directions are not chosen using age.

Use a correct pipeline equivalent to:

```python
Pipeline([
    ("scale", StandardScaler()),
    ("pca", PCA()),
    ("model", KNeighborsRegressor()),
])
```

Keep the example compact:

- reuse the established eligible age-prediction cohort and split/fold conventions;
- choose the number of PCs and `k` on development data only;
- compare PCA + KNN against KNN using the original standardized 360 features under the same evaluation structure;
- show a small results table with MSE and R-squared;
- report the result honestly, whether PCA helps or not;
- do not add another interactive activity to Exercise 8.

Hide the full tuning/evaluation machinery on the website. Keep it visible and executable in the portable notebook.

Use one Think First question:

> Why might PCA help KNN more directly than it helps a model that does not calculate distances between participants?

Update the Exercise 8 audit script so its supervised portion now verifies PCA + KNN and raw-feature KNN. Rename the audit script/result only if the current name becomes actively misleading; otherwise preserve paths and document the broadened purpose.

---

# Part B — Exercise 9: Advanced Models

## 6. Scope and learning sequence

Replace the Exercise 9 placeholder with a real notebook titled:

`# Exercise 9: Advanced Models`

The notebook must be concise. A complete prediction pipeline has already appeared several times, so show only model-specific code and important implementation details. Hide the reusable nested-comparison machinery.

Use this section order.

### Opening: What This Notebook Covers

State concisely that this is Exercise 9 of *Machine Learning for Neuroscience*. Students will:

1. compare PCR with PLS;
2. connect SVM margins and support vectors to classification and regression;
3. explore how kernels create nonlinear models;
4. compare advanced models on the same ABIDE-II age-prediction task.

### 1. Why Consider More Advanced Models?

Explain briefly:

- neuroimaging predictors are numerous and correlated;
- predictive information may be low-dimensional;
- useful relationships may be linear or nonlinear;
- different models preserve and use information differently.

Think First:

> If two models receive the same participants and features, why can they produce different predictions even when both are evaluated correctly?

### 2. Principal Component Regression

Introduce PCR here for the first time.

Show a compact pipeline:

```python
Pipeline([
    ("scale", StandardScaler()),
    ("pca", PCA(n_components=...)),
    ("model", LinearRegression()),
])
```

Important pointers only:

- PCR means linear regression using principal-component scores as predictors.
- PCA chooses directions that explain variation in `X`, without seeing age.
- The number of retained components is a model parameter.
- Scaling and PCA must be fitted inside each validation fold.
- PCR can reduce noise and collinearity but can discard a low-variance direction that predicts the target.

Link conceptually to Exercise 8's PCA section without repeating its scree/loading material.

### 3. Partial Least Squares

Introduce PLS regression as supervised component construction.

Explain:

- PCR components summarize variation in predictors;
- PLS components are constructed using the relationship between predictors and the target;
- PLS can prioritize a predictive direction that explains relatively little variance in `X`;
- because PLS sees the target, the complete PLS fit must occur inside training folds;
- the number of PLS components must be chosen using training/development data.

Show concise code using `PLSRegression`. If an outer `StandardScaler` is used, set PLS's internal scaling consistently (for example, `scale=False`) and explain this in one short comment rather than scaling twice silently.

### 4. Interactive Activity — PCR or PLS?

Create a deterministic synthetic example in which:

- one direction has high predictor variance but weak target relevance;
- another direction has lower predictor variance but stronger target relevance;
- noise prevents perfect prediction.

Required controls:

- method: PCR or PLS;
- number of components: 1 or 2;
- one compact control or preset that changes how strongly the target aligns with the lower-variance direction.

Required outputs:

1. the two-dimensional predictor cloud colored by target value;
2. the selected first component direction;
3. observed-versus-predicted validation values;
4. training and validation MSE;
5. a short statement of how the chosen component was constructed.

The training/validation split must remain fixed while controls change.

Guiding questions:

- With one component, why can PLS outperform PCR?
- Why do PCR and PLS become more similar after both original directions are retained?
- Does a component that explains more predictor variance necessarily predict age better?
- Why would fitting PLS before the split be especially problematic?

Do not expose the answer through default annotations before students interact.

### 5. Support Vector Machines

Introduce only the practical ideas needed for the exercise:

- separating boundary;
- margin;
- support vectors;
- `SVC` for classification;
- `SVR` and the epsilon-insensitive tube for regression;
- scaling as a requirement for distance- and margin-based models.

Explain the main parameters in a compact table:

| Parameter | Student-facing meaning |
|---|---|
| `C` | How strongly the model penalizes errors or margin violations |
| `epsilon` | How much regression error is tolerated before a penalty is applied |
| `kernel` | The type of relationship the model can represent |
| `gamma` | How local and flexible an RBF relationship can become |

Use direct interpretations:

- smaller `C`: more regularization and greater tolerance for violations;
- larger `C`: stronger pressure to fit training observations;
- larger RBF `gamma`: more local and potentially more complex behavior.

### 6. Kernels and Nonlinear Boundaries

Explain the kernel idea conceptually without a derivation. Cover only:

- linear;
- polynomial, briefly;
- radial basis function (RBF), as the main nonlinear kernel.

State that a kernel acts like a similarity rule that lets the model represent a richer boundary without explicitly constructing every transformed feature.

### 7. Interactive Activity — Explore an SVM Boundary

Use deterministic, synthetic two-dimensional classification data because margins, support vectors, and nonlinear boundaries are easiest to see in classification.

Required controls:

- dataset: one approximately linear and one nonlinear dataset;
- kernel: linear, polynomial, or RBF;
- `C`: a small bounded grid such as `[0.1, 1, 10, 100]`;
- `gamma`: a small bounded grid such as `[0.1, 1, 10]`, enabled only when relevant;
- Reset.

Keep polynomial degree fixed and state it briefly.

Required outputs:

1. training and validation observations with distinguishable markers;
2. the decision boundary and decision regions;
3. visible support vectors from the training set;
4. training accuracy;
5. validation accuracy;
6. number of support vectors.

Guiding questions:

- Why can the linear kernel not separate the nonlinear dataset well?
- What happens when `C` becomes very large?
- What happens when RBF `gamma` becomes very large?
- Which settings create a boundary that follows individual training observations too closely?
- Why does perfect training accuracy not establish that the model is better?

Add a short bridge after the activity: `SVR` uses the same ideas for a continuous outcome such as age, replacing the classification margin with an epsilon-insensitive regression objective.

Clearly label this activity as conceptual exploration, not a final model-selection procedure.

### 8. Comparing Advanced Models on ABIDE-II

Use the same 1,004 eligible participants, 360 cortical-thickness features, and age target.

Compare:

1. standardized ordinary linear regression as a familiar reference;
2. PCR;
3. PLS regression;
4. linear SVR;
5. RBF SVR.

Use one shared, reproducible **nested cross-validation** structure for every model:

- identical outer folds for generalization estimates;
- identical inner-fold assignments wherever mathematically applicable;
- all preprocessing inside the model pipeline;
- inner selection using MSE;
- outer-fold reporting of MSE and R-squared;
- no additional test-set result selected after viewing these comparisons.

Do not reteach nested CV. Refer briefly to Exercise 4 and hide the reusable comparison machinery on the website.

Use bounded, auditable grids. Start from approximately:

- PCR components: `[5, 10, 20, 50, 100, 200]`;
- PLS components: `[2, 5, 10, 20]`;
- linear SVR `C`: `[0.01, 0.1, 1, 10]`;
- SVR `epsilon`: a small interpretable grid in age units, such as `[0.5, 1, 2]`;
- RBF SVR `C`: `[1, 10, 100]`;
- RBF `gamma`: a compact grid including `"scale"` and a few numeric values justified relative to standardized inputs.

The implementation may adjust a grid only for a documented numerical, convergence, or runtime reason. Do not adjust it to obtain a preferred winner. Record any convergence warnings and address them transparently.

Show students:

- compact estimator/pipeline definitions;
- compact parameter grids;
- a results table with mean outer-fold MSE, mean outer-fold R-squared, and fold variability;
- one concise comparison plot;
- the selected parameters/components across folds, preferably in a collapsed detail block.

Before revealing results, ask:

- Which method do you expect to perform best?
- Is the RBF model guaranteed to improve performance?
- What would it mean if several models have overlapping fold-to-fold results?

Report the observed results honestly. Do not declare a meaningful winner based on a negligible difference.

### 9. Strengths, Weaknesses, and Appropriate Uses

Use one concise table with no more than these four rows:

| Method | Useful when | Main limitation |
|---|---|---|
| PCR | Features are numerous and correlated | Components ignore the target |
| PLS | Predictive information may not follow the highest-variance directions | Target-aware components can overfit |
| Linear SVM/SVR | Many features and an approximately linear relationship | Scaling and parameter selection matter |
| Kernel SVM/SVR | A nonlinear relationship is plausible and the sample is not enormous | Less interpretable and increasingly expensive as the sample grows |

Conclude that model choice also depends on interpretability, sample size, computational cost, and the scientific question.

### 10. Test-Oriented Thinking Questions

Include concise questions, with revealable answers for the central concepts:

1. Why must PCA and PLS be fitted inside each validation fold?
2. When might PLS outperform PCR?
3. Why can PCR discard a direction useful for prediction?
4. What generally happens when `C` increases?
5. How can a very large RBF `gamma` lead to overfitting?
6. Why does an RBF kernel not guarantee better validation performance?
7. What makes a training observation a support vector?
8. Why must all compared models use the same outer folds?
9. If two models have similar scores, what other considerations guide the choice?
10. Why is selecting and evaluating a model on the same validation results optimistic?

Avoid repeating identical versions of these questions in earlier Reflect boxes.

### 11. Main Takeaways

Keep this to a short list:

- PCR uses PCA components without allowing the target to influence them.
- PLS constructs components using the predictor–target relationship.
- SVMs base their solution on support vectors and regularized margins.
- Kernels let SVMs represent nonlinear relationships.
- Greater flexibility can help, but it can also overfit.
- Fair model comparison requires the same nested validation procedure.

---

## 7. Interactive implementation requirements

Implement both activities through the existing config/schema/registry/TypeScript/Plotly architecture. Do not use a Python runtime in the browser.

### PCR/PLS activity

- Generate data deterministically in a focused export script.
- Precompute model fits for the bounded control grid with scikit-learn.
- Store only the data required for display and independent verification.
- Make component-direction sign deterministic for display, since component signs are mathematically arbitrary.
- Ensure train and validation rows remain fixed across control changes.
- Independently verify scores, directions, predictions, and MSE in Python tests.

### SVM/kernel activity

- Generate both datasets deterministically and keep their splits fixed.
- Precompute the bounded configuration catalogue with scikit-learn.
- Support vectors must come only from training observations.
- Store a bounded decision grid sufficient for a smooth but compact Plotly boundary.
- Disable or visually mark irrelevant controls rather than silently applying them.
- Independently verify decision-grid classes, accuracies, support-vector indices/counts, and defaults.

### Both activities

- meaningful iframe titles and accessible labels;
- keyboard-operable native controls;
- responsive layout without horizontal scrolling;
- exact light/dark theme synchronization;
- transparent Plotly drag layers;
- readable axes, titles, margins, and legends;
- no widget-related console errors;
- dedicated built-book dark-mode coverage for both activities.

Report compressed and uncompressed artifact sizes. If an artifact is large, first reduce redundant storage without removing an approved educational control.

---

## 8. Portable notebooks

1. Regenerate Exercise 8's portable notebook after its PCR-to-KNN correction.
2. Register and generate the Exercise 9 portable notebook.
3. Replace live iframes with visible, editable Python equivalents.
4. Keep hidden website comparison code visible and runnable in portable notebooks.
5. Include only the established optional package-install cell; do not reference a private repository or `requirements.txt` in student-facing text.
6. Extend the standard portable smoke registry to include Exercise 9.
7. Execute both Exercise 8 and Exercise 9 portable notebooks outside the repository tree.

---

## 9. Audit and reproducibility requirements

Create or extend focused audit scripts that independently verify:

### Exercise 8

- PCA + KNN pipeline structure;
- tuning performed on development data only;
- raw-feature KNN comparison under identical folds/split;
- reported MSE and R-squared;
- no PCR or `LinearRegression` remains in Exercise 8 student-facing material or executable analysis.

### Exercise 9

- cohort and feature counts;
- identical outer folds across every ABIDE model;
- all scaling, PCA, and PLS fitting occurs inside training folds;
- inner parameter selection excludes the outer fold;
- all parameter grids match the manifest/notebook;
- outer-fold MSE and R-squared reproduce exactly;
- summarized means and variability reproduce exactly;
- PCR and PLS component counts are valid for every inner fold;
- SVM convergence and fit status;
- all interactive catalogue calculations.

Do not use outer-fold results to revise grids or defaults in favor of a preferred model. Defaults for synthetic activities must be pedagogically chosen independently of ABIDE model rankings.

---

## 10. Required tests

Add focused tests for:

### Exercise 8 correction

- PCR absent from Exercise 8;
- PCA + KNN section present;
- correct leakage-safe pipeline;
- audited metrics match stored output;
- portable notebook updated and executable.

### Exercise 9 notebook

- placeholder replaced with `.ipynb`;
- correct title, opening, green block, links, and sidebar position;
- required sections and concise scope;
- PCR first introduced here;
- PLS, SVC/SVR, `C`, `epsilon`, kernels, and `gamma` described accurately;
- no duplicate question blocks;
- familiar data loading hidden;
- long comparison machinery hidden on website and visible in portable form;
- ABIDE results match the audit;
- Syllabus and Word overview remain unchanged.

### Interactive unit/browser tests

- config/schema validation;
- default state;
- every control updates the intended output;
- irrelevant gamma control state;
- reset behavior;
- PCR/PLS fixed split and method differences;
- SVM decision boundary and support-vector display;
- light/dark/reload-in-dark behavior;
- narrow viewport;
- keyboard controls;
- no new runtime errors.

Update placeholder expectations so Exercises 10–12 remain placeholders and Exercise 9 is treated as a real notebook with a portable version and launch button.

---

## 11. Bounded validation plan

Use the following order:

1. focused Exercise 8 correction audit/tests;
2. focused Exercise 9 model audit/tests;
3. focused widget export checks and Python tests;
4. regenerate portable notebooks and run generator `--check`;
5. portable smoke execution for Exercises 8 and 9 outside the repository;
6. focused frontend unit tests and typecheck;
7. one frontend production build;
8. focused standalone Playwright tests for the two new activities;
9. one Jupyter Book build;
10. focused built-book Exercise 8 and Exercise 9 tests, including dedicated Exercise 9 dark-mode coverage;
11. full Python suite once;
12. full frontend unit suite once;
13. full standalone and built-book Playwright suites once if the focused gates pass;
14. manual inspection of Exercises 8 and 9 in light, dark, and narrow views.

Bounded-execution rules:

- Do not rerun a passing full suite.
- On failure, determine the root cause, make one bounded correction, and rerun only the failed gate once.
- If the rerun still fails, stop and report rather than entering a repair loop.
- Do not use long arbitrary sleeps; prefer event/state-based waits.
- Do not run, watch, or poll GitHub Actions.
- Do not merge, push, or deploy.

---

## 12. Manual review checklist

Confirm visibly that:

- Exercise 8 no longer introduces PCR;
- its PCA + KNN section is concise and clearly connected to high-dimensional distances;
- Exercise 9 is not a repeated prediction-pipeline tutorial;
- PCR and PLS are visually and conceptually distinguishable;
- the PCR/PLS activity does not reveal its conclusion before interaction;
- support vectors are clearly marked;
- SVM boundaries remain readable in dark mode;
- `C` and `gamma` visibly change appropriate models;
- the ABIDE comparison does not overstate small score differences;
- code/output hiding is appropriate on the website;
- portable notebooks preserve all runnable teaching code;
- Colab and download links target the correct notebook versions.

---

## 13. Reports and stop condition

Create:

- `WPs/reports/WP34_REPORT.md`
- `WPs/reports/WP34_EXACT_CHANGELOG.md`

The report must include:

1. overall success or failure;
2. resolved WP33 final branch-tip SHA;
3. WP34 starting and final branch/SHA;
4. exact Exercise 8 changes and new KNN results;
5. Exercise 9 section list and cell count;
6. interactive controls, defaults, and artifact sizes;
7. ABIDE comparison grids, fold structure, model results, and selected parameters;
8. validation commands, durations, and outcomes;
9. every failure, retry, deviation, warning, or judgment call;
10. any result or design choice requiring the user's attention;
11. confirmation that Syllabus and Word overview were untouched;
12. confirmation that nothing was merged, pushed, deployed, or monitored through GitHub Actions;
13. final `git status --short --branch` and exact decorated log.

The exact changelog must list every added, modified, renamed, and removed file and explain its purpose.

After committing both reports, stop. Return a concise summary for the user, flagging only decisions or problems that require attention before inspection or deployment. Do not start WP35.
