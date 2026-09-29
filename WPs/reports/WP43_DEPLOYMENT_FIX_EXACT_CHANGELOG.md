# WP43-series deployment fix: exact changelog

Five commits, pushed individually to `origin/main`, each triggering its own
CI run. No force-push; no other branch touched; `Homework_Materials/`
untouched throughout.

## Commit `a016d8e` — Fix recurring Exercise 2 Section 8 Playwright timeout, capture CI evidence

Files:
- `interactive/e2e-book/exercise-02-lite.spec.ts` (modified)
- `interactive/playwright.book.config.ts` (modified)
- `.github/workflows/deploy.yml` (modified)

### `exercise-02-lite.spec.ts`

All 7 occurrences of `await page.waitForTimeout(100_000);` (one per
full-notebook test) changed to `await page.waitForTimeout(140_000);`,
matching the value already used by every test in
`exercise-01-lite.spec.ts` and by `wp22-cross-chapter-dark-mode.spec.ts`'s
own Exercise-2 dark-mode check for this same notebook. Two comments
updated to explain the change and its evidence.

### `playwright.book.config.ts`

```diff
   use: {
     baseURL: `http://localhost:${PORT}`,
-    trace: "off",
+    trace: "retain-on-failure",
+    screenshot: "only-on-failure",
+    video: "retain-on-failure",
   },
```

### `.github/workflows/deploy.yml`

Added a step after "End-to-end test the combined book + JupyterLite
build":

```yaml
- name: Upload Playwright failure evidence (book suite)
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: playwright-book-failure-evidence
    path: interactive/test-results
    retention-days: 14
```

Triggered run:
[`36461757056`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/36461757056),
head SHA `a016d8e`. Result: failure (a *different* test than before --
`iframe-height-contract.spec.ts`'s Chapter 5 check -- see report for
detail). The Section 8 slider fix itself was confirmed working in this
run and every run after it.

## Commit `17b13fc` — Drop book-suite video capture: caused a new iframe-settle CI flake

Files:
- `interactive/playwright.book.config.ts` (modified)

```diff
     trace: "retain-on-failure",
     screenshot: "only-on-failure",
-    video: "retain-on-failure",
```

(Comment rewritten to document the video hypothesis and that it was tried
and reverted.)

Triggered run:
[`36474594313`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/36474594313),
head SHA `17b13fc`. Result: failure -- the identical Chapter 5 test, the
identical `1578px` reading.

## Commit `596ef9b` — Serialize book-suite CI workers: eliminate cross-test CPU contention

Files:
- `interactive/playwright.book.config.ts` (modified)

```diff
   retries: 0,
+  ...(process.env.CI ? { workers: 1 } : {}),
   reporter: [["list"]],
```

(Plus a long comment documenting the cross-worker-contention hypothesis
and its evidence.)

Triggered run:
[`36535264291`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/36535264291),
head SHA `596ef9b`. Result: failure -- the identical Chapter 5 test, the
identical `1578px` reading, now under full serialization (38.9m step
duration vs ~21m before, for no benefit).

## Commit `4d19fbb` — Drop book-suite trace capture: last remaining constant across 3 flakes

Files:
- `interactive/playwright.book.config.ts` (modified)

```diff
   retries: 0,
-  ...(process.env.CI ? { workers: 1 } : {}),
   reporter: [["list"]],
   use: {
     baseURL: `http://localhost:${PORT}`,
-    trace: "retain-on-failure",
     screenshot: "only-on-failure",
   },
```

Net effect relative to the pre-`a016d8e` baseline: `screenshot:
"only-on-failure"` is the only capture-mode change kept; `workers` is back
to its original unset (default) value.

Triggered run:
[`36546309608`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/36546309608),
head SHA `4d19fbb`. Result: failure, but a genuinely different one -- the
entire 149-test browser suite passed; the run failed one step later, at
"Execute the portable notebook outside the repository" (job
`109333438944`, step 23), 4m47s after the browser-test step finished.

## Commit `dcc5365` — Fix stale chapter_02 expected strings in smoke_portable_notebook.py

Files:
- `scripts/smoke_portable_notebook.py` (modified)

### Docstring (top of file)

Rewrote the `chapter_02` bullet in the module docstring to describe the
guarded KNN-check cell's actual current behavior and to explain why
Section 8's own "k = {k} model complexity" print is not (and structurally
cannot be) checked by this script's `_all_output_text()` extraction.

### `SMOKE["chapter_02"]`

```diff
-            "age available for 1004 of 1004",
-            "n_features = 360",
+            "1004 participants, 360 brain predictors",
+            "n_train = 753   n_test = 251",
             "held-out R^2 = 0.469",
-            "k = 20",
-            "held-out R^2 = 0.664",
-            "fitting participants (N_fit) = 564   validation participants (N_val) = 189",
-            "every validation prediction equals the fitting-set mean",
-            "n_features (p) = 10",
+            "held-out MSE = 49.6",
+            "Not complete yet: define knn_pred, knn_r2, and knn_mse above first.",
+            "fitting participants = 564   validation participants = 189",
+            "k with lowest validation error = 17",
```

Also rewrote the `chapter_02` entry's own header comment (the one
explaining why `chapter_01` is excluded from `SMOKE`), correcting its claim
that a bounded run against chapter_02 previously hung -- this session's own
CI evidence (chapter_02 completing in ~4 seconds, no hang, in run
`36546309608`) contradicts that specific claim. `chapter_01`'s own
exclusion is left in place, not re-verified.

No notebook content changed. `book/downloads/chapter_02/
exercise_02_portable.ipynb` itself was not modified -- only this script's
expectations about its output.

Triggered run:
[`36566657471`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/36566657471),
head SHA `dcc5365`. **Result: success.** Every step passed, including
`Publish website`.

## Production result

- `gh-pages` advanced: `f6ddfc28e5102d44f94dc5dc86ba9875ad36db8a` (pre-WP41
  content, unchanged since WP43's first attempt) →
  `05ceb13e4467616c72b0033e6990da8ce5d162d6`
  (`deploy: dcc53655b8e4b3eac67ba741e165ff6bbbf0cf3d`).
- This is the first successful production deploy since WP41 began
  migrating Exercises 1 and 2 to JupyterLite.
- `origin/main`: `89c9bcc` (WP43R's tip, entering this session) →
  `dcc5365` (5 commits: `a016d8e`, `17b13fc`, `596ef9b`, `4d19fbb`,
  `dcc5365`).

## Reports

`WPs/reports/WP43_DEPLOYMENT_FIX_REPORT.md` and this file are committed
locally on `main`. Per the established pattern in this repository (see
WP43R/WP43RR), they are not pushed in a separate commit solely to publish
them, to avoid triggering an unnecessary sixth deploy run; they will reach
`origin/main` whenever the next substantive change is pushed. (Unlike
WP43R/WP43RR, this session's actual deployment already succeeded and is
already live, so this is a matter of report-publishing hygiene, not
withholding a production change.)
