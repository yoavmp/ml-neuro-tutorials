# Syllabus

**Machine Learning for Neuroscience** &middot; Course **1501.1027** &middot;
Semester A, 2026-27
Mondays, 08:30-11:00 (location not provided in the source syllabus)

## Aims and prerequisites

- Core methods and terminology in machine learning
- Hands-on training, evaluation, and interpretation of common models
- Uses and challenges of machine learning in neuroscience

Prior Python programming experience is **required**. A background in
probability and linear algebra is **recommended**.

## Staff and office hours

| Role | Name | Contact |
|---|---|---|
| Lecturer | Dr. Assaf Madar | `asafmdr@gmail.com` |
| Teaching assistant | Yoav Melamed | `yoavmelamed@mail.tau.ac.il` |

Office hours: by prior arrangement.

## Course text and scope

The course covers core machine-learning topics starting from exploratory
data analysis, through classification and regression with linear models and
KNN, tree-based models, and regularization methods. The course also covers
clustering and dimensionality reduction. Hands-on practical work is
emphasized throughout.

Course text (freely available):
Gareth James, Daniela Witten, Trevor Hastie, Robert Tibshirani, and Jonathan
Taylor (2023). *[An Introduction to Statistical Learning: with Applications
in Python](https://hastie.su.domains/ISLP/ISLP_website.pdf.download.html)*.
See also the book's official hub, [statlearning.com](https://www.statlearning.com/).

## Assessment

| Component | Weight |
|---|---|
| Homework | 10% |
| Final project (code submission and oral presentation) | 45% |
| Written exam | 45% |

Homework and the final project are submitted **in pairs**.

## Schedule

The two topics marked *(tentative)* below are provisional in the source
syllabus, not confirmed. Only Exercises 1-9 are published on this site so
far; a scheduled lecture topic for Weeks 10-13 does not mean that week's
practice notebook is available yet -- see [Contents](contents.md) for the
currently published exercises.

| Week | Date | Lecture | Practice | Homework |
|---|---|---|---|---|
| 1 | 19 Oct 2026 | Intro, EDA, linear regression | EDA | &mdash; |
| 2 | 26 Oct 2026 | Linear regression continued, KNN regression, bias-variance trade-off | Linear regression, bias-variance trade-off (using a KNN interactive example) | EDA + KNN regression (try different *k*'s; theoretical questions on how *k* relates to the bias-variance trade-off) |
| 3 | 2 Nov 2026 | Classification metrics, logistic regression, LDA, KNN | Classification metrics, logistic regression | &mdash; |
| 4 | 9 Nov 2026 | Cross-validation; bootstrap *(tentative)* | CV vs. train/test, with a classification and a regression example | &mdash; |
| 5 | 16 Nov 2026 | Regularization and feature selection | Regularization (Ridge, Lasso), feature selection | Ridge/Lasso regression + logistic-regression classification, with tuning in nested CV *(tentative)* |
| 6 | 23 Nov 2026 | Decision trees, bagging, Random Forest | Trees (start) | &mdash; |
| 7 | 30 Nov 2026 | Boosting, gradient boosting | Trees, boosting | Classification using trees/LDA |
| 8 | 7 Dec 2026 | Unsupervised learning, PCA, clustering | PCA, clustering | &mdash; |
| 9 | 14 Dec 2026 | Advanced models: PCR, PLS, SVM, kernels | Advanced models, code and comparisons | PCA and kernels applied to previous models: KNN, Ridge, SVM* |
| 10 | 21 Dec 2026 | Introduction to deep learning | Common mistakes, realistic examples | &mdash; |
| 11 | 28 Dec 2026 | Embeddings, representational similarity analysis | Embeddings, RSA | Embeddings and RSA (bonus task) |
| 12 | 4 Jan 2027 | Introduction to LLMs *(tentative)* | Practice, exam-style questions | &mdash; |
| 13 | 11 Jan 2027 | Oral tests | Oral tests | &mdash; |

\* The source syllabus lists this row's last homework item as "sum"; rendered here as "SVM" to match this week's own advanced-models topic (PCR, PLS, SVM, kernels) -- flagged as a likely source typo, not independently confirmed with the course author.
