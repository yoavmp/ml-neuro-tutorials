# WP54 — Course pages and two figure fixes

## Starting point and authorization

Start from the clean `main` after WP53 (report: `WPs/reports/WP53_REPORT.md`; production source SHA `4c4c09c`, subject to any later report-only commit). Create the normal pre-work checkpoint and a feature branch. This WP authorizes the changes below, regeneration of affected student/portable/reference notebooks, a production push and deployment, and live verification. Do not publish Exercises 10–12. Do not change fitted models or established numeric results to make a figure look better.

Read the supplied course-author syllabus `סילבוס למידה חישובית תשפ עם מטלות.docx` completely, including its table and embedded course-book link. This WP transcribes its content below so the work is reviewable even if the attachment is unavailable to a later Claude session. For any discrepancy between this transcription and the document, use the document and flag the discrepancy in the report.

## 1. Question-cell audit and old-copy guidance

The author confirmed the apparent old-format questions in Exercises 1 and 2 came from **older saved browser working copies**. The currently published fresh `exercise_01.ipynb` and `exercise_02.ipynb` templates were independently checked for this WP: their visible question cells already call only `show_question("...")`; the hidden setup holds the answer mapping. **Do not rewrite those correct question implementations, change the shared question helper, bump template versions solely for this report, or build a new migration feature.**

- Perform a focused source/generated-student-notebook audit of Exercises 1–9 to verify that visible question cells use `show_question(id)` and do not show `correct_index` or `correct_indices`. Keep the offline question-checking logic intact. Fix only a genuine remaining leak if found and document it.
- Add a brief instruction in the revised Introduction for someone opening an old saved browser working copy: **download the edited copy first**, then use **Reset from course template** if they want the latest exercise. State clearly that reset replaces that browser copy and that an old downloaded `.ipynb` will not update itself. Avoid global browser-storage deletion and do not promise automatic migration.
- One focused fresh-browser check of each of Exercises 1 and 2 should confirm the visible source calls and correct/incorrect feedback after WP53's deterministic answer shuffle. Do not run an elaborate returning-browser migration suite for a behavior already explained by the author's old copy. The report should explicitly say if no notebook 1/2 code change was needed.

## 2. Exercise 6 regression-tree diagram

Fix `format_tree_diagram()` in the **generator** and regenerate all required Exercise 6 outputs. The defect is functional as well as visual: the published code calls `plot_tree(...)`, then does `zip(order, artists)` where `order` is a manually traversed list of `tree_.node_id`s. That artist order does not match the manual order. The screenshot consequently shows custom values on the wrong boxes, clipped text, and default `squared_error`/`samples`/`value` labels beneath the custom labels. Increasing DPI/font size cannot fix mismapped labels.

Render each node **once** from the fitted `small_tree.tree_` using `children_left/right`, `feature`, `threshold`, `n_node_samples`, and `value` directly. Prefer a programmatic vector or high-resolution Matplotlib drawing of the actual model, with wrapped split labels, taller leaves, clear arrows/branch conditions, no original default-label layer, and no cropped text. For readability at notebook width, place the root at top and its two complete subtrees in stacked, clearly labeled `≤` and `>` panels (four leaves per panel); a similarly clear implementation is acceptable. Keep this in the executable notebook so downloaded local/Colab copies reproduce it. A screenshot-only/static replacement is insufficient.

The reference model uses `max_depth=3`, `min_samples_leaf=20`, `random_state=42`, and the existing two cortical-thickness columns and split. Its actual tree has 15 nodes and 8 leaves. On the established data: root `n=564`, age `15.2`, threshold `Left 3a thickness ≤ 1.799`; the root children have `n=95` and `n=469`. Leaves, from left to right, are `(n, predicted age) = (26,33.7), (20,24.6), (21,22.6), (28,19.3), (63,20.1), (78,14.7), (180,12.7), (148,10.0)` to display precision. These figures were obtained by executing the currently published Exercise 6 code against its own published CSV. Compare every node's displayed identity/count/value directly with `tree_`, and assert that each parent's sample count equals its two children's; do not merely test pixel dimensions.

Review the desktop and 390px browser render and exported/downloaded notebook. The author has already reviewed a correct two-panel preview in this conversation; use its layout intent without copying unverified raster text. If the exact figure must be displayed as two adjacent/stacked output figures rather than one tall figure for mobile legibility, keep the root-to-branch relationship unambiguous.

## 3. Exercise 9 PCR-versus-PLS interactive

In the synthetic-data plot, move the green **“PLS direction”** label to **below** the gray **“PC2 (fixed)”** label as the author requested. Place them in a dedicated annotation area or use measured text positioning so neither label covers points/arrows, clips at the axes, or touches the colorbar. Keep the arrows' directions and data unchanged. Check at weights 0, 0.25, 0.5, 0.9, and 1, and for both component-count choices, at desktop and narrow widths. A rendered-image/artist-bounds check should catch *internal* overlap; testing only that the page itself does not overflow missed the WP53 issue.

## 4. Populate the Syllabus page in English

Replace the current empty page with a faithful English rendering of the attached syllabus. Keep it scannable: course information, aims/prerequisites, staff/contact/office hours, course text, assessment, and a 13-row schedule with columns **Week, Date, Lecture, Practice, Homework**. Do not invent a room, due date, policy, assignment, or confirmed topic absent from the source. Include all of these facts:

- **Machine Learning for Neuroscience**, course **1501.1027**, semester A **2026–27**; Mondays **08:30–11:00**, location not provided in the document.
- Aims: core ML methods/terms; hands-on training, evaluation and interpretation of common models; uses and challenges in neuroscience. **Required** prior Python programming; probability and linear algebra **recommended**.
- Lecturer **Dr. Assaf Madar**, `asafmdr@gmail.com`; teaching assistant **Yoav Melamed**, `yoavmelamed@mail.tau.ac.il`; office hours by prior arrangement.
- Scope: EDA, linear and KNN regression, classification, tree models, regularization, clustering, dimensionality reduction, with practical work. Course text: **Gareth James, Daniela Witten, Trevor Hastie, Robert Tibshirani, Jonathan Taylor (2023), *An Introduction to Statistical Learning: with Applications in Python***. Link to the official freely available Python edition (the source document embeds `https://hastie.su.domains/ISLP/ISLP_website.pdf.download.html`; the official book hub `https://www.statlearning.com/` also links to it). The citation should lead the References page.
- Homework and final project submitted **in pairs**. Final grade: **Homework 10%**, **final project 45% (code submission and oral presentation)**, **written exam 45%**.

Use this schedule exactly, translating the source's Hebrew column labels and preserving its intentionally empty homework cells. Mark the two `?` topics as provisional, rather than presenting them as confirmed:

| Week | Date | Lecture | Practice | Homework listed in source |
|---|---|---|---|---|
| 1 | 19 Oct 2026 | Introduction, EDA, linear regression | EDA | — |
| 2 | 26 Oct 2026 | Linear regression continued, KNN regression, bias–variance trade-off | Linear regression, bias–variance trade-off | EDA and regression |
| 3 | 2 Nov 2026 | Classification metrics, logistic regression, LDA, KNN | Classification metrics, logistic regression | — |
| 4 | 9 Nov 2026 | Cross-validation; bootstrap *(tentative in source)* | Cross-validation and nested cross-validation | — |
| 5 | 16 Nov 2026 | Regularization and feature selection | Ridge, Lasso, feature selection | Logistic-regression classification; Ridge/Lasso regression |
| 6 | 23 Nov 2026 | Decision trees, bagging, Random Forest | Trees and ensembles | — |
| 7 | 30 Nov 2026 | Boosting and gradient boosting | Trees and boosting | Trees |
| 8 | 7 Dec 2026 | Unsupervised learning, PCA, clustering | PCA and clustering | — |
| 9 | 14 Dec 2026 | Advanced models: PCR, PLS, SVM, kernels | Advanced-model code and comparisons | Unsupervised learning and advanced models |
| 10 | 21 Dec 2026 | Introduction to deep learning | Common mistakes and realistic examples | — |
| 11 | 28 Dec 2026 | Embeddings and representational similarity analysis | Embeddings and RSA | Embeddings and RSA (bonus task) |
| 12 | 4 Jan 2027 | Introduction to LLMs *(tentative in source)* | Practice and exam-style questions | — |
| 13 | 11 Jan 2027 | Oral tests | Oral tests | — |

Ensure the page does not imply that the yet-unpublished Exercises 10–12 are available just because their lecture topics are scheduled. Link to the public exercise hub for currently published practice when useful.

## 5. Update Introduction for active notebooks and environment choices

Replace outdated passive/legacy notebook directions with a short student-facing explanation: supplied runnable cells, **YOUR CODE HERE** sections to complete, notebook-native interactive activities, and checked understanding questions (including multiple selection) with feedback. Explain saving/reopening and downloading one's edited work, and the difference between current browser work and a newly downloaded template. Remove the old “About the questions” section and obsolete iframe/Colab-only claims.

Give clear choices: **open the exercise in the site's JupyterLite notebook** (no local install), or download its `.ipynb` and upload/open it in **Google Colab**. Also describe local Jupyter/VS Code as optional: **Python 3.11 is the tested/recommended local version**, plus `numpy`, `pandas`, `matplotlib`, `scikit-learn`, `ipywidgets` (and `seaborn` if actually used); JupyterLab or VS Code notebook support and `ipykernel`; initial dataset retrieval may require internet. Give a minimal installation example **in the Introduction only if useful**, not a repo-install/`requirements.txt` instruction in student-facing content. The browser runs its own bundled Pyodide Python, and Colab's runtime version is controlled by Colab: **do not claim that every environment literally runs Python 3.11**. The notebook's `kernelspec` saying `Python 3` does not establish a 3.11 version. Do not introduce package/version claims unsupported by the actual published 1–9 notebooks.

## 6. Resources then References pages

Add top-level **Resources** immediately after **Contents**, followed immediately by **References**, in `_toc.yml` and the visible site navigation. Follow the linked inspiration page's clean, short grouping, but make content specific to *this* course, with no empty placeholder sections.

**Resources** is a practical link directory for material actually shown or used in the published Exercises 1–9. Inventory their generated student notebooks, transition pages, and course text for URLs and named external resources; deduplicate, categorize (course text, datasets/data provenance, relevant Python/Jupyter documentation or useful learning tools), and give each link one line explaining its purpose. At minimum include: official **ISL with Python** book hub/free edition; official **ABIDE II** site and phenotypic legend; the pinned **NeuroHackademy `abide2.tsv`** source used by the course's data-loading fallback; the course's **published same-origin ABIDE CSV/other actual data assets** when useful, accurately distinguishing curated course exports from the original source. Check link targets and whether they are genuinely accessible; don't link to private repository internals or encourage students to install the repo. Include other genuinely relevant, linked resources from notebook 1–9, not an arbitrary long collection copied from the inspiration page.

**References** is a consistent bibliography for *citable works actually invoked by the published notebooks/syllabus*, with the course book **first**, then other works in a consistent order/style, DOI or stable primary link when available, and brief notebook/chapter pointers if helpful. Inventory every explicit author–year, DOI, paper, dataset citation, or adapted externally sourced figure across the published 1–9 notebooks and page content. At minimum include the course book, the ABIDE II dataset publication if used, and Exercise 5's **Bethlehem et al. (2022), DOI `10.1038/s41586-022-04554-y`**, and **Storsve et al. (2014), DOI `10.1523/JNEUROSCI.0391-14.2014`**. Verify bibliographic metadata at primary publishers, Crossref, or official source pages before publishing. Link existing in-notebook author–year mentions to this References page when feasible without disrupting notebook portability; a downloaded notebook should not depend on an internal site route for essential context. Treat the original research/data-provider credit correctly. Do not add unsupported citations to ordinary teaching explanations just to fill the page.

## Verification, deployment and reporting

- Regenerate and check only notebooks whose generators actually change, plus focused source/content tests for all nine visible question cells. Build Jupyter Book and JupyterLite once on the final local source. Exercise 6 and 9 browser checks must inspect the **inside of the generated figures** at the problematic states; do not substitute no-page-overflow tests for readability. Test the new syllabus table, navigation order, bibliography links, and 404s for unpublished chapters.
- Inspect the WP50 release classifier on the real diff. Shared book navigation/intro/syllabus/assets may legitimately choose `full`; honor its result. Avoid serial repeat runs of unaffected notebook reference/execution tests locally. Follow the existing one-push, diagnose-before-retry, monitor-to-completion workflow, with progress updates during long tests; do not leave CI idle awaiting user prompts.
- Once green, deploy and verify the exact `gh-pages` marker/source SHA, the five course pages (**Introduction, Syllabus, Contents, Resources, References**), Exercises 1–9, fresh Exercise 1/2 question cells, corrected Exercise 6 figure and Exercise 9 label, downloads, links, and unpublished 10–12 404s. The old-copy instruction must describe the existing manual backup/reset path accurately; do not claim automatic browser-copy migration was implemented. Do not discard a student's work for a test.
- Produce `WPs/reports/WP54_REPORT.md` and `WP54_EXACT_CHANGELOG.md`: each numbered requirement, syllabus source mapping, URL and citation inventory, question audit and confirmation that old saved copies caused the author's report, per-node tree validation, figure checks including failed/resolved states, changed files, test scope/timings, real CI gate/run/status, live verification, limitations, and final git state. Put closing reports in `WPs/**` so a report-only commit does not cause another deployment.
