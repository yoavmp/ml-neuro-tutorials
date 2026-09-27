# WP41R — Repair Exercise 2 local-review blockers

## Authority and scope

This is a focused correction to WP41 on `feature/wp41-jupyterlite-course-platform`. The course author observed three blockers in the actual local combined build:

1. Exercise 2 reaches `data = load_abide_age_brain_table()` with `NameError: name 'load_abide_age_brain_table' is not defined`; subsequent cells fail because `data` does not exist.
2. Clicking the approved reference image exposes an enormous `data:image/png;base64,...` Markdown source that is difficult to leave or edit.
3. The Book transition page's **Open Exercise 2** link does not open JupyterLite. Its portable path appears as literal text, and the page's inherited Colab control opens the old notebook.

Fix these in the existing feature branch. Do not migrate another exercise, merge, push, deploy, start WP42, or touch `Homework_Materials/`. Preserve all approved cohorts, splits, metrics, student tasks, and the current browser working-copy contract.

## 1. Git checkpoint and diagnosis

From the repository root, record `git status --short --branch`, `git log -5 --oneline --decorate`, and the current feature SHA. Check for unexplained changes before editing; stop and report rather than resetting, stashing, or overwriting them. Create a local checkpoint commit or branch for the pre-correction state. Inspect the actual generator, generated notebook, transition-page generator, manifest, built HTML, Book theme links, and browser console/network traces. Identify the cause of each symptom; do not assume the missing helper is merely an import error.

In a clean browser profile, reproduce the student's natural path: Contents → Exercise 2 → JupyterLite → run the supplied setup and analysis cells in order. Record whether the collapsed setup cell ran, whether its asynchronous package setup completed, whether it raised an earlier exception, and why the helper was unavailable. Also test a fresh kernel, not only a kernel that has accumulated variables during development.

## 2. Make setup and data loading reliable

The notebook must give students a clear, short first-run action and an unmistakable success or actionable failure message. Keep implementation detail collapsible if useful, but do not let collapsed or asynchronous setup silently leave the helper undefined. Ensure `load_abide_age_brain_table()` is defined before its first use in a fresh kernel after following the notebook instructions. Make any prerequisite run order explicit. If a student runs the data cell before setup, give a helpful instruction rather than a raw `NameError`; avoid masking real failures or inserting hidden fallback results.

Verify imports, `ipywidgets` installation/initialization in Pyodide, same-origin CSV loading, and a fresh-kernel top-to-bottom run of supplied cells. Independently confirm the downloaded notebook still loads the checksummed fallback data in local Jupyter and Colab-compatible execution. The five student blanks may remain blank; independent later sections must not cascade into uncaught errors. Preserve numerical results: 1004 participants, 360 predictors, 753/251 train/test, linear R² 0.469 and MSE 49.55, k=20 KNN R² 0.664 and MSE 31.4, and the existing Section 7/Bonus values.

## 3. Repair the reference image cell

Replace the giant inline `data:image/png;base64,...` Markdown URL with a compact, portable notebook representation, such as a notebook attachment if it works in JupyterLite, local Jupyter, and Colab. The rendered image must remain visible and readable; entering edit mode must expose only short, manageable source text, and leaving edit mode must be straightforward. Do not put a large base64 payload into a visible code cell or move the image to a site-only path that breaks the downloaded notebook. Check round-trip rendering and exported `.ipynb` in all supported environments where practical. Add a browser regression check that clicks the image cell and confirms it can be returned to rendered mode without a page-length encoded string.

## 4. Repair every Exercise 2 entry point

Generate correct links for the local combined build and the eventual GitHub Pages project subpath from the manifest or a single route helper. Clicking **Open Exercise 2** from the built Book transition page must open the intended personal JupyterLite working copy directly. The portable notebook must be a working download link, not literal text. Contents → Exercise 2 → Open Exercise 2 must work by actual clicks in a browser, including a fresh profile and a 390px viewport. Avoid stale cached HTML when checking by rebuilding both halves of the combined site and using a fresh browser context.

Audit the inherited top-bar **Colab** action on the transition page. It must not lead to the old notebook. Point it to the new Exercise 2 notebook only if that route demonstrably works for a local build and the future public/private-repository arrangement; otherwise suppress it on this transition page and provide a clear **Download notebook for Colab** link with concise upload instructions. Do not point students at a raw GitHub URL that will fail when the repository becomes private. Check any top-bar download action for the same stale target. Keep navigation for unmigrated exercises intact.

## 5. Focused validation and report

Update generators and generated files together. Add focused tests that would have caught all three user-reported failures, including the actual built transition page and a clean-kernel first-run path; structural checks alone are insufficient. Build Jupyter Book, then JupyterLite into `book/_build/html/lite/`, serve the combined tree, and run browser tests by clicking from Contents. Inspect the reference cell interaction and verify Colab/download targets. Run focused numerical-integrity and portability checks and one bounded full suite if required by repository rules. For a failing gate, diagnose once, make one focused correction, and rerun that gate once; stop and report if still failing.

Write `WPs/reports/WP41R_REPORT.md` and `WPs/reports/WP41R_EXACT_CHANGELOG.md`. Include root causes, changed files, exact commands/results, screenshots or browser evidence, fresh-kernel first-run result, local and Pages-subpath link targets, image portability, numeric comparison, deviations, branch/SHA, and confirmation that nothing was merged, pushed, or deployed. Commit these reports locally. Return a short course-author summary with the exact local build/serve commands and URL for review. Do not start the next WP.
