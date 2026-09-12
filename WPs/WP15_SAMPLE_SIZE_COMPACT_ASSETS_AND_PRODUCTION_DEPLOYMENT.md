# WP15 — Repair the sample-size lesson, compact interactive assets, and deploy production

## Read this first

Execute this work package in the existing repository:

`/Users/crazyjoe/Projects/ml-neuro-tutorials`

Do not merely propose changes. Inspect the real repository and pinned ABIDE data, implement the work, run the tests, merge the completed feature work into `main`, push it, wait for GitHub Pages deployment, and verify the live site.

This WP has three goals:

1. Replace Exercise 2's distracting double-descent sample-size example with a clean, honest demonstration of why sample size matters. First try a small, defensible cortical-thickness feature subset. If no such subset produces the intended lesson under the rules below, retain all 360 CT features and start the plotted training sizes at approximately 350 participants.
2. Make the static interactive-data architecture sustainable for more notebooks by replacing the two multi-megabyte KNN JSON payloads with compact, validated, page-local assets.
3. Integrate all completed work into `main`, build it, push it, and verify Exercises 1–3 on the public GitHub Pages site.

Do not create WP16. At the end, create the two WP15 report files specified in §9.

---

## 0. Mandatory Git checkpoint before any edit

Before changing any source, generated asset, notebook, or configuration:

1. `cd /Users/crazyjoe/Projects/ml-neuro-tutorials`
2. Record:
   - `git status --short --branch`
   - `git branch --show-current`
   - `git log -1 --oneline`
   - `git remote -v`
3. Preserve all existing work. Do not discard, overwrite, or clean user files.
4. Add this WP file to the repository under `WPs/` if it is not already there.
5. Commit the current state with a checkpoint commit such as:
   - `checkpoint: before WP15`
6. Create an annotated tag `wp15-start`; if it already exists, use the next unambiguous suffix and document it.
7. Continue on the current feature branch unless repository inspection establishes a safer existing workflow.

Never use `git reset --hard`, `git clean`, destructive checkout, history rewriting, force-push, or tag deletion.

If the working tree contains unexpected changes that cannot safely be preserved, stop and report the exact files and reason. Do not guess.

---

## 1. Establish the real baseline

Read, at minimum:

- `WP14_REPORT.md`
- `WP14_EXACT_CHANGELOG.md`
- the canonical notebooks for Exercises 1–3
- the portable-notebook generator and generated portable notebooks
- `book/config/abide_modeling.json`
- the Exercise 2 sample-size code and any tests that assert its outputs
- `scripts/export_knn_explore_data.py`
- `scripts/export_knn_abc_data.py`
- the TypeScript data parsers/loaders and KNN components
- the Jupyter Book configuration, `_toc.yml`, and GitHub Pages workflow(s)
- `.gitignore`, especially the treatment of `book/_build`

Run and record the relevant baseline checks before editing. At minimum:

- Python unit tests
- frontend typecheck and unit tests
- generated-artifact `--check` commands
- portable-notebook freshness checks
- Jupyter Book build
- Playwright tests that cover standalone widgets and the built book
- current sizes of both KNN JSON assets and the built Exercise 3 page/assets

The WP14 baseline reports approximately:

- `abide_knn_explore.json`: 2,719,089 bytes
- `abide_knn_abc.json`: 1,850,283 bytes
- combined: 4,569,372 bytes

Confirm these numbers from the actual branch rather than assuming them.

---

## 2. Exercise 2 sample-size audit: isolate the intended lesson

### 2.1 Pedagogical requirement

The current all-360-feature OLS curve at low `n` demonstrates interpolation/double descent. That result is real, but it distracts from this exercise's intended lesson: with a fixed, modest model, estimates and held-out predictions generally become more stable as training data increases.

The revised section must not claim that more observations guarantee a better score in every finite sample. It should show the broad trend across repeated samples and explain that individual repeats can fluctuate.

### 2.2 No result-driven cherry-picking

Do not search hundreds of parcel combinations until one makes an attractive plot. Do not use the locked outer test set to select parcels, choose a random seed, remove inconvenient points, or decide among feature recipes.

Before calculating candidate results, write a small audit configuration listing a short set of defensible candidate subsets. Each candidate must:

- contain at most 12 genuine `fsCT_` parcel columns;
- be defined independently of participant ages and regression outcomes;
- have a reproducible anatomical or deterministic rationale;
- include both hemispheres when the anatomical rationale is bilateral;
- use only predictors, never diagnosis, site, participant ID, or another phenotype;
- avoid deriving the choice from correlations with age in the full dataset.

Good candidate sources, in order of preference:

1. a small, already reviewed anatomical bundle in the existing manifest;
2. a small bilateral set tied to a documented neuroanatomical rationale;
3. a deterministic, atlas-wide sampling rule fixed from column order/atlas structure without looking at age or performance.

Do not invent uncertain anatomical labels. Validate every proposed column against the real, hash-pinned table and the corrected 180-parcel/360-column atlas manifest.

### 2.3 Training-only comparison and decision rule

Evaluate the predeclared candidates using training data only. Use repeated, deterministic development splits or repeated cross-validation; do not inspect or score the locked outer test partition during candidate choice.

Define the decision rule in code before viewing results. A candidate is acceptable only if all of the following hold:

- `p <= 12` and the smallest plotted training size is comfortably larger than `p`;
- the median validation R² has a clear overall upward trend as `n` grows;
- instability narrows materially with larger `n`;
- there is no interpolation-threshold collapse or visually dominant reversal;
- the result is not dependent on one lucky seed;
- the final full-training model remains meaningful enough for the plot to teach prediction rather than pure noise.

Minor finite-sample non-monotonicity is acceptable; do not demand that every adjacent median increase. Report the numeric audit table for every predeclared candidate in the WP report, including candidates not selected.

### 2.4 Locked fallback

If no predeclared small subset passes that rule, do not keep searching. Use the existing honest 360-feature CT recipe and change the plotted sizes so they start around 350 participants and then increase to all available training participants. Choose a simple predeclared sequence such as `[350, 400, 500, 600, len(y_train)]`, adjusted only for the actual available `n` and with the adjustment reported.

Because `p=360`, the text must still disclose that the smallest points are near the `n≈p` transition and may be unstable. If the 350/400 points are still dominated by double descent, move the start upward only as much as necessary based on the training-only audit and report the exact decision; never crop or clip the resulting axes to hide poor values.

### 2.5 Final Exercise 2 implementation

Once the decision is locked:

- regenerate the final sample-size figure and executed output;
- use repeated deterministic training subsamples;
- report a robust centre (median is preferred) and a visible uncertainty interval;
- label the number of predictors `p` and training observations `n` clearly;
- keep the evaluation partition fixed across plotted sample sizes;
- ensure scaling is fit separately inside each training subsample and only applied to its evaluation data;
- update every dependent statement, question, caption, output, test, and portable notebook;
- remove the double-descent discussion if the revised figure no longer demonstrates it;
- do not retain stale `n=50`/`n=100` claims, values, or outputs unless a valid compact subset is selected and those sizes remain in the locked design.

The student-facing explanation should be concise. Suggested message:

> Here we deliberately hold the feature set fixed and modest so that the plot isolates the effect of training-set size. Each point summarizes repeated training samples. More data usually improves stability and generalization, although a single sample can still perform better or worse by chance.

Adapt the wording to the actual chosen design. If the 360-feature fallback is used, do not call the feature set modest.

Keep the section focused on sample size; do not introduce a new full lesson on double descent, feature selection, or regularization.

---

## 3. Compact data architecture for browser interactives

### 3.1 Why this is being done

The present two KNN JSON files total about 4.57 MB. Four times that is about 18.3 MB, which is not a GitHub Pages capacity problem, but repeated large JSON arrays increase parsing time, page transfer, and Git history. They also exceed GitHub's current recommended 1 MB maximum for a single repository object, even though they are far below its enforced 100 MB file limit.

Implement a reusable compact format now, without changing the activities' mathematics, visible results, accessibility, or offline/static-hosting model.

### 3.2 Required design

Replace the two large, numeric-array JSON payloads with:

- a small versioned JSON manifest per activity; and
- one or more deterministic binary payload files read with `fetch(...).arrayBuffer()` and typed arrays.

Preferred representation:

- store nearest-neighbour row indices as unsigned 16-bit integers when the validated maximum index is below 65,536;
- store the corresponding target arrays once per reference/training sample as little-endian 32-bit floats, unless comparison proves 64-bit precision is required to reproduce all displayed metrics at the existing rounding precision;
- eliminate the duplicate Exercise 3 explorer baseline matrix if `trainingSamples.A` is identical to the top-level baseline;
- keep shapes, byte offsets, dtypes, endianness, schema version, and SHA-256 digests in the JSON manifest;
- retain no participant identifiers, sites, diagnoses, or raw 360-feature rows in browser assets.

If a different representation is demonstrably smaller, simpler to validate, and equally robust, it is allowed, but document the deviation and evidence in the report.

Do not depend on a server, database, CDN, Git LFS pointer, service worker, notebook kernel, or runtime Python. The built GitHub Pages site must remain a static site. Do not require browser support for transparently serving precompressed `.gz` files.

### 3.3 Reusable loader

Create one shared, tested TypeScript binary loader rather than activity-specific byte parsing. It must:

- validate schema version before loading;
- validate path safety and expected byte length;
- validate array bounds, shapes, dtype, and endianness;
- verify a digest where practical in both tests and production; if production digest verification has a material compatibility/performance cost, enforce it during export/build and explain the decision;
- fail with a clear, student-friendly activity error rather than a blank plot;
- work when hosted under the repository subpath `/ml-neuro-tutorials/`;
- avoid duplicate network fetches of the same file on one page;
- preserve current keyboard and screen-reader behaviour.

### 3.4 Exporters and canonical checks

Update the Python exporters so `--refresh` writes the manifest and binary files deterministically and `--check` validates that committed files are canonical byte-for-byte.

The validators must reconstruct the logical arrays and retain all existing semantic checks, including:

- shapes and valid `k` ranges;
- exact/appropriately tolerant k=1 self-neighbour endpoints for invalid panels B and C;
- the Exercise 3 `k=N_fit` mean-prediction endpoint;
- equality of training sample A with the baseline semantics;
- agreement with representative scikit-learn KNN predictions;
- no identifier-shaped manifest key or prohibited payload;
- no raw imaging matrix in the public asset.

Do not hand-edit generated manifests or binary files.

### 3.5 Size budget

Add an automated size-budget test. Target:

- at least a 50% reduction from the combined 4,569,372-byte JSON baseline;
- no individual committed runtime-data object above 1,000,000 bytes if the chosen layout can reasonably achieve that;
- page-local loading: Exercise 2 must not fetch Exercise 3 assets, and each activity should fetch only what it needs.

If the 50% target cannot be achieved without reducing correctness, browser compatibility, or maintainability, keep the correct implementation and document measured sizes and the reason. Do not reduce numeric precision silently.

Delete obsolete large JSON assets only after every source reference and test has migrated. Confirm they are absent from the final built site. Do not rewrite Git history to remove their old versions.

### 3.6 Preserve portable notebooks

Colab/downloaded notebooks must continue to run without the browser binary assets. Their non-interactive fallback code and outputs remain the source of truth for portable use. Do not add JavaScript/binary-loader requirements to the portable notebook.

---

## 4. Notebook and site consistency checks

After the Exercise 2 and asset changes:

- regenerate both affected canonical notebook outputs rather than editing output JSON by hand;
- regenerate Exercises 2 and 3 portable notebooks;
- ensure Exercise 1 remains unchanged unless a shared infrastructure change truly requires it;
- confirm the blue `Think first` design remains consistent across all exercises;
- verify the green `Run or download this notebook` block and Colab/download links on Exercises 1–3;
- confirm no student-facing text references WPs, reports, internal scripts, or audit files;
- confirm all pages work from a clean browser session under a repository subpath;
- confirm no browser console errors, failed requests, uncaught exceptions, or blank plots.

---

## 5. Full local validation gate before merge

Run the repository's real commands discovered from its documentation/workflows. At minimum, complete:

1. every changed Python exporter in refresh mode;
2. every artifact exporter in check/canonical mode;
3. Python unit tests;
4. frontend formatting/linting if configured;
5. frontend typecheck;
6. frontend unit tests;
7. production interactive build;
8. portable-notebook freshness checks;
9. portable smoke execution outside the repository environment, following the existing harness;
10. a clean Jupyter Book build;
11. standalone and built-book Playwright suites;
12. two consecutive clean builds with deterministic generated figures/assets;
13. a scan for stale `358`, obsolete JSON filenames, Exercise 2 FIQ/regularization text, and student-facing internal references;
14. a scan of the final built tree for obsolete multi-megabyte KNN JSON files.

Record exact commands, versions, pass counts, warnings, generated sizes, and hashes. Existing known warnings may remain only if unchanged and explicitly identified. New warnings or skipped tests are failures unless a concrete external blocker is documented.

Do not merge or push if this gate fails.

---

## 6. Production integration: inspect first, then merge safely

The user has explicitly authorized merging completed work to `main`, pushing, building, and deploying the latest notebooks.

Before mutation:

1. Confirm the local remote named `origin` points to the intended repository: `yoavmp/ml-neuro-tutorials`.
2. Run `git fetch origin --prune`.
3. Inspect the commit graph and divergence among the current feature branch, local `main`, and `origin/main`.
4. Inspect the existing GitHub Pages source/workflow. Follow the repository's established deployment mechanism; do not invent a second Pages workflow.

Safe merge sequence, adapted only if repository inspection requires it:

1. Commit the completed WP15 implementation on the feature branch.
2. Ensure the feature branch is clean and the implementation commit passes §5.
3. Switch to `main`.
4. Update from `origin/main` with `git pull --ff-only origin main`.
5. Merge the feature branch into `main` with an ordinary merge commit (`--no-ff` is acceptable and preferred for this WP history).
6. Run a short post-merge smoke gate on `main` before pushing: artifact checks, frontend production build, clean Jupyter Book build, and representative Playwright checks.

If `main` has unexpected divergence, merge conflicts, protected-branch requirements, or remote commits that materially change the work, stop and report. Do not force, rebase published history, or resolve substantive conflicts by guessing.

---

## 7. Build and publish using the repository's established Pages path

Determine whether GitHub Pages is deployed by GitHub Actions, a dedicated Pages branch, or committed build output.

- If an existing GitHub Actions workflow builds and deploys from `main`, push source to `main` and let that workflow build. Do not commit `book/_build` merely to duplicate the workflow.
- If the established project intentionally publishes committed build output or a dedicated branch, follow that exact mechanism after validating it locally.
- Do not change hosting provider, repository visibility, Pages audience, or custom domain.

Push `main` normally. Never force-push.

Use `gh` if already authenticated/configured to monitor the exact workflow run triggered by the push. Otherwise use a safe, read-only GitHub endpoint/browser check. Wait until deployment is terminal; do not report success merely because the push succeeded.

If deployment fails, inspect its logs, make only in-scope fixes, rerun the full relevant checks, commit, push normally, and monitor the new run. Report every additional fix.

---

## 8. Live-site acceptance tests

After deployment reports success, test the production site itself, not only localhost. The expected base URL is:

`https://yoavmp.github.io/ml-neuro-tutorials/`

Resolve the exact paths from the built site and verify at least:

- Introduction
- Syllabus
- Contents
- Exercise 1 EDA
- Exercise 2 Regression
- Exercise 3 KNN and bias–variance tradeoff

For Exercise 2:

- confirm the final sample-size section, values, and figure are the WP15 version;
- confirm no stale double-descent prose remains unless the fallback result genuinely requires a brief caveat;
- confirm all 360-feature main-regression content still works.

For Exercise 3:

- exercise the A/B/C k control at `k=1`, the selected/default k, and another typed k;
- confirm all plots and R²/MSE text change;
- exercise the training-sample tabs and bias/variance proxy panels;
- verify the identity-line legend;
- verify no obsolete large JSON request occurs.

Across all pages:

- confirm navigation/sidebar links;
- confirm the Colab target opens the correct portable notebook path;
- confirm the `.ipynb` download target returns the current portable notebook;
- inspect network failures and browser console errors;
- hard-refresh once to rule out stale cached HTML/assets;
- confirm the visible deployed revision corresponds to the final pushed `main` commit.

Use automated Playwright production checks where possible, supplemented by direct HTTP status/asset validation. Do not claim interactivity success from HTTP 200 alone.

---

## 9. Final reports, report commit, and final deployment

Only after implementation, merge, first deployment, and live acceptance testing, create:

- `WP15_REPORT.md`
- `WP15_EXACT_CHANGELOG.md`

The report must include:

1. success/failure status;
2. checkpoint commit/tag, implementation commit, merge commit, report commit reference, and final pushed `main` SHA;
3. baseline and final test commands/counts;
4. the complete predeclared small-feature audit table, selection rule, selected feature names/rationale, or the documented 360-feature fallback;
5. final sample sizes and numeric R²/MSE summaries used in Exercise 2;
6. why the result is not held-out-test-driven cherry-picking;
7. old and new byte sizes for every migrated interactive asset, total percentage reduction, and whether every file meets the size budget;
8. binary schema/version/dtype/endianness and validation strategy;
9. exact notebook, script, config, frontend, test, workflow, and generated-file changes;
10. portable-notebook validation results;
11. Jupyter Book warnings, if any;
12. exact GitHub Actions/Pages workflow run URL or identifier and terminal status;
13. exact live URLs tested and the interactions exercised;
14. browser console/network status;
15. any deviations, compromises, failures, or items requiring the user's attention.

Commit the two reports on `main` and push that report-only commit normally. Because this may trigger another Pages run, wait for that final run to succeed and repeat a concise production smoke check. It is acceptable for the report to identify the final report-commit SHA as “recorded in the terminal summary” if embedding its own hash would create a self-reference problem.

End with a short terminal summary containing:

- final `main` SHA;
- clean/dirty status;
- deployment status and workflow run;
- live Exercise 1, 2, and 3 URLs;
- final interactive asset total;
- any user-attention item.

Do not start another WP.

---

## 10. Non-negotiable constraints

- Preserve the corrected 360 genuine CT features in the main Exercise 2 and Exercise 3 models.
- A compact subset may be used only for Exercise 2's isolated sample-size demonstration and must be selected under §2's rules.
- Do not manipulate features, seeds, sample sizes, or axes merely to “prove” a preferred result.
- Do not leak test data into scaling, feature choice, hyperparameter selection, or training.
- Do not expose participant identifiers or the raw 360-feature table in browser assets.
- Do not degrade the existing interactivity, accessible controls, or portable notebooks.
- Do not add a backend or CDN dependency.
- Do not use Git LFS for files fetched by the live Pages site.
- Do not rewrite history or force-push.
- Do not deploy if required tests fail.
- Do not make the repository private in this WP.
- Do not create the next WP.
