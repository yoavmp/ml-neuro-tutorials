# WP64 — Exercise 7: resilient scikit-learn load in the data-loading cell

## Authority and trigger

The course author reported an intermittent live-site failure: on
`https://yoavmp.github.io/ml-neuro-tutorials/lite/notebooks/index.html?path=exercise_07.ipynb`,
after running the collapsed setup cell, the data-loading cell sometimes
raises `ModuleNotFoundError: No module named 'sklearn'` at
`from sklearn.model_selection import ...`. The author independently opened
the live page fresh and got a clean "360 predictors" run, so this is not a
"scikit-learn missing from the build" report — it reads as intermittent,
and the author explicitly warned not to assume scikit-learn is absent from
the deployed build.

## Execution contract

1. **Reproduce before changing anything.** Do not edit the notebook, the
   generator, or any JupyterLite build config until the failure is
   actually reproduced and its mechanism is understood against the real
   deployed site (not a theory about it). Cover a cold start and a
   returning-browser/saved-notebook condition, inspect kernel startup and
   package loading, and capture real browser console/network evidence.
2. **Preserve student state.** Do not propose or use "Reset from course
   template" as the fix, and do not touch the JupyterLite contents
   IndexedDB or any build/deploy mechanism that would discard a student's
   saved notebook.
3. If the cause is established and a fix is written, it must be the
   smallest reliable change, authored in the generator
   (`scripts/generate_exercise_07_notebook.py`) and regenerated into every
   derived copy — never a hand-edit of a generated `.ipynb`. No change to
   Exercises 1–6 or 8–12, `book/lite/overrides.json`,
   `requirements-lite.txt`, or any other platform-wide file unless the
   root cause is proven to be platform-wide (it was not — see the report).
4. Run the focused Exercise 7 checks
   (`test_exercise_07_lite_notebook.py`, `test_exercise_07_reference_execution.py`,
   `test_exercise_07_transition_page.py`, the generator's own `--check`)
   and the shared kernel-startup check
   (`interactive/e2e-book/kernel-startup.spec.ts`) plus
   `interactive/e2e-book/exercise-07-lite.spec.ts`, against a real local
   combined `jupyter-book build` + `jupyter lite build`. Do not run or
   wait on the full project-wide suite here — the required release gate
   (`.github/workflows/deploy.yml`) covers that on push.
5. If the cause cannot be reproduced or explained, stop and report the
   evidence without a speculative deployment. If it can, and the fix
   passes focused checks, push to `main`, watch the deploy workflow to
   completion, and verify the fix on the **live** page under the same
   failing conditions that were reproduced locally (not just a fresh
   browser — the author already confirmed that case works).

## Required report

Write `WPs/reports/WP64_REPORT.md` with: the reproduction method and tool
(a real headless-Chromium session driven against the live page, via
Playwright), the exact mechanism established (what jupyterlite-pyodide-kernel
actually does with `book/lite/overrides.json`'s preload list, and where the
real race lives), the exact aborted-request repro and resulting traceback,
the fix diff, focused test/e2e results, the push/deploy run id and
conclusion, and live-page verification under the reproduced failing
condition. State plainly if any part of the originally reported "returning
browser with a saved notebook" angle was ruled out rather than confirmed,
and why.
