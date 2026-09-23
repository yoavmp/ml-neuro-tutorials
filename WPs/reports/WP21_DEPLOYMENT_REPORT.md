# WP21 Deployment Report

## 1. Release status
**SUCCESS**

## 2. Release SHA
`0a28301ceee3c4a3a8891158a73ac0754b4b6150`

## 3. Push result
Fast-forward push succeeded on the first and only attempt:

```
To https://github.com/yoavmp/ml-neuro-tutorials.git
   c5aa2ca..0a28301  main -> main
```

Post-push verification: `origin/main` resolves to `0a28301ceee3c4a3a8891158a73ac0754b4b6150`, matching `RELEASE_SHA`.

## 4. GitHub Actions run
- Workflow: **Build and deploy Jupyter Book**
- Run ID: **35080467526**
- Final status: **success** (`build-and-deploy` job completed in 3m36s, all steps green)
- Found immediately on the first `gh run list` check (no need for the 20-second retry).

Note: run annotation flagged that Node.js 20 is deprecated in Actions runners (informational only, not a failure) — pre-existing CI condition, not something this release task addressed.

## 5. Live URL verification

All four pages checked with cache-busting query `?cb=0a28301ceee3c4a3a8891158a73ac0754b4b6150`, all on the first pass (no stale-page retry needed):

| Exercise | URL | HTTP Status | Title present | "Run or download this notebook" | Revised phrase found | iframe present |
|---|---|---|---|---|---|---|
| 1 | [exercise_01.html](https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html) | 200 | ✅ Exercise 1 — Exploratory data analysis (EDA) | ✅ | ✅ "Ways to handle missing data" | ✅ |
| 2 | [exercise_02.html](https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_02/exercise_02.html) | 200 | ✅ Exercise 2: Regression | ✅ | ✅ "Building one linear-regression workflow" | ✅ |
| 3 | [exercise_03.html](https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_03/exercise_03.html) | 200 | ✅ Exercise 3: KNN and the Bias–Variance Tradeoff | ✅ | ✅ "Correct and misleading ways to evaluate a model" | ✅ |
| 4 | [exercise_04.html](https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html) | 200 | ✅ Exercise 4: Classification with Logistic Regression | ✅ | ✅ "One logistic-regression model" | ✅ |

## 6. Revised headings
All four revised phrases were found on their respective pages (see table above).

## 7. Final `git status --short --branch`
```
## main...origin/main
?? WPs/reports/WP16_ARCHITECT_REPORT.md
```
(Local `main` and `origin/main` are in sync; the pre-existing untracked WP16 report is the only untracked file, left untouched. This WP21 report itself is also untracked and not committed.)

## 8. Push confirmation
Exactly **one** `git push origin main` was performed. No amend, no force-push, no second push.

## 9. Process confirmation
- No workflow rerun was triggered.
- No force-push occurred.
- No second deployment was caused (this report is untracked/uncommitted, per instructions).
- No prolonged polling occurred: run was found on the first `gh run list` check; `gh run watch` ran as a single continuous bounded command (~3m36s, well under the 15-minute cap); live pages were verified once, with no stale-page retry needed.

## Live pages
- https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html
- https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_02/exercise_02.html
- https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_03/exercise_03.html
- https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html
