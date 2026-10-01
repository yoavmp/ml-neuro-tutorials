import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

// End-to-end proof that the migrated Exercise 7 JupyterLite notebook works
// in a real browser against the actual combined jupyter-book + jupyter-lite
// build (WP46), modeled directly on exercise-06-lite.spec.ts. Requires
// `jupyter lite build --config book/lite/jupyter_lite_config.json --lite-dir
// book/lite --output-dir book/_build/html/lite` to have already run.
//
// None of this notebook's three "YOUR CODE HERE" blanks (Section 4's
// sweep, Section 6's pipeline, Section 6's grouped bar charts) is guarded
// by a raise-on-missing-prerequisite cell: each one's own check cell
// degrades gracefully to "Not complete yet" instead, so "Run All Cells" on
// the UNTOUCHED template produces zero error cells at all. The pipeline
// blank's GridSearchCV fit (12 candidates x 5 folds) is the slowest step in
// this notebook; this file budgets extra time for it accordingly.

test.setTimeout(240_000);

const NOTEBOOK_URL = "/lite/notebooks/index.html?path=exercise_07.ipynb";

async function scrollWindowed(page: Page, fraction: number) {
  await page.evaluate((f) => {
    const el = document.querySelector(".jp-WindowedPanel-outer");
    if (el) el.scrollTop = el.scrollHeight * f;
  }, fraction);
  await page.waitForTimeout(400);
}

async function scrollToVisible(
  page: Page,
  text: string,
  cellSelector = ".jp-CodeCell",
): Promise<import("@playwright/test").Locator> {
  const locator = page.locator(cellSelector, { hasText: text }).first();
  for (let f = 0; f <= 1.001; f += 0.05) {
    await scrollWindowed(page, f);
    if ((await locator.count()) > 0 && (await locator.boundingBox())) {
      return locator;
    }
  }
  throw new Error(`cell containing "${text}" never became visible while scrolling`);
}

async function runAllCells(page: Page) {
  await page.click("text=Run");
  await page.waitForTimeout(200);
  await page.locator(".lm-Menu-itemLabel", { hasText: "Run All Cells" }).first().click();
}

async function fillBlank(page: Page, anchorText: string, solution: string) {
  const target = await scrollToVisible(page, anchorText);
  const editor = target.locator(".cm-content").first();
  await editor.click();
  await page.waitForTimeout(150);
  const isMac = process.platform === "darwin";
  await page.keyboard.press(`${isMac ? "Meta" : "Control"}+A`);
  await page.keyboard.press("Backspace");
  // insertText (a single CDP Input.insertText call) avoids CodeMirror 6's
  // smart-indent-on-Enter corrupting indented blocks -- see WP44/WP45.
  await page.keyboard.insertText(solution);
  await page.keyboard.press("Shift+Enter");
  await page.waitForTimeout(600);
}

// Runs exactly one specific cell (located and focused explicitly by its
// own anchor text, exactly like fillBlank does), without touching its
// source. Used instead of runAllCells() to step forward through a
// supplied cell between two blanks without re-executing the whole
// notebook -- this notebook's Section 6 pipeline blank is a multi-minute
// GridSearchCV fit (see the teacher-completed-path test below), so a full
// "Run All Cells" after every later blank would recompute it again each
// time. A bare, unfocused Shift+Enter chain was tried first and was
// unreliable (JupyterLab's windowed/virtualized cell list does not
// reliably keep an off-screen "next" cell selected across a wait), hence
// explicitly re-locating and clicking into each target cell here.
async function runCell(page: Page, anchorText: string) {
  const target = await scrollToVisible(page, anchorText);
  const editor = target.locator(".cm-content").first();
  await editor.click();
  await page.waitForTimeout(150);
  await page.keyboard.press("Shift+Enter");
  await page.waitForTimeout(2_000);
}

test.describe("Exercise 7 — JupyterLite notebook, untouched template", () => {
  test("Section 1 loads the established data and Section 3's illustration prints", async ({ page }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);
    await page.waitForTimeout(180_000);

    await scrollWindowed(page, 0.05);
    await expect(page.locator("body")).toContainText("n_train (development) = 753", { timeout: 5_000 });

    const example = await scrollToVisible(page, "gb_model = GradientBoostingRegressor");
    // Checked to 2 decimals, not 3: Pyodide's WASM-compiled numpy/scikit-learn
    // can accumulate a few ULPs of floating-point drift differently from a
    // native build across 100 sequential trees, occasionally moving the 3rd
    // decimal of R^2 (confirmed live: 0.746 in-browser vs. 0.745349 natively).
    await expect(example.locator(".jp-OutputArea-output").last()).toContainText("validation R2 = 0.74");
  });

  test("no error cells anywhere on an untouched Run All Cells; all three blanks degrade to their own guidance", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);
    await page.waitForTimeout(180_000);

    expect(await page.locator(".jp-mod-error").count()).toBe(0);

    const sweepCheck = await scrollToVisible(page, "define boosting_sweep_results above first");
    await expect(sweepCheck.locator(".jp-OutputArea-output").last()).toContainText("Not complete yet");

    const pipelineCheck = await scrollToVisible(
      page,
      "define boosting_search, boosting_best_model, boosting_test_mse, and boosting_test_r2 above first",
    );
    await expect(pipelineCheck.locator(".jp-OutputArea-output").last()).toContainText("Not complete yet");

    const barCheck = await scrollToVisible(page, "define boosting_bar_fig_a and boosting_bar_fig_b above first");
    await expect(barCheck.locator(".jp-OutputArea-output").last()).toContainText("Not complete yet");
  });

  test("the Build a Boosted Model activity advances stages and the stage-0 status is shown", async ({ page }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);
    await page.waitForTimeout(180_000);

    const widget = await scrollToVisible(page, "Next Step", ".jp-CodeCell");
    await expect(page.locator("body")).toContainText("Stage 0: the model predicts the training-target mean", {
      timeout: 5_000,
    });
    await widget.locator("button", { hasText: "Next Step" }).click();
    await page.waitForTimeout(1_500);
    await expect(page.locator("body")).toContainText("Stage 1: a new shallow tree was fitted", { timeout: 5_000 });
  });

  test("the Explore the Boosting Parameters widget changes its metrics line when depth changes", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);
    await page.waitForTimeout(180_000);

    const widget = await scrollToVisible(page, "Tree depth:", ".jp-CodeCell");
    await expect(page.locator("body")).toContainText("learning rate = 0.1   depth = 2   trees = 100", {
      timeout: 5_000,
    });
    // Plain-int Dropdown options: select by fixed position, not by value
    // (WP44/45 documented ipywidgets.Dropdown value/HTML-option mismatch).
    await widget.locator("select").nth(1).selectOption({ index: 2 });
    await page.waitForTimeout(3_000);
    await expect(page.locator("body")).toContainText("depth = 3", { timeout: 10_000 });
  });

  test("stays usable at a 390px viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await page.waitForTimeout(4000);
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(2);
  });

  test("reset restores the template and Back returns to Contents", async ({ page }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await page.waitForTimeout(3000);

    await page.click("text=Reset from course template");
    await page.waitForTimeout(800);
    await page.locator(".jp-Dialog-button", { hasText: "Reset" }).first().click();
    await page.waitForTimeout(2000);

    await scrollWindowed(page, 0);
    await page.click("text=Back to course contents");
    await page.waitForTimeout(1000);
    expect(page.url()).toContain("contents.html");
  });
});

test.describe("Exercise 7 — JupyterLite notebook, teacher-completed path", () => {
  test("filling in all three blanks reproduces the established results and drives a checked question", async ({
    page,
  }) => {
    test.setTimeout(1_800_000);
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);
    await page.waitForTimeout(180_000);

    await fillBlank(
      page,
      "# boosting_sweep_results = []",
      "boosting_sweep_results = []\n" +
        "for n in N_TREES_VALUES:\n" +
        "    m = GradientBoostingRegressor(learning_rate=0.1, max_depth=2, n_estimators=n, random_state=42)\n" +
        "    m.fit(X_fit, y_fit)\n" +
        "    pred = m.predict(X_val)\n" +
        "    boosting_sweep_results.append({'n_estimators': n, 'val_mse': mean_squared_error(y_val, pred)})\n" +
        "boosting_sweep_fig, ax = plt.subplots()\n" +
        "ax.plot([r['n_estimators'] for r in boosting_sweep_results], [r['val_mse'] for r in boosting_sweep_results], marker='o')\n" +
        "plt.show()",
    );

    // fillBlank()'s own Shift+Enter only queues the sweep cell's execution
    // (7 GradientBoostingRegressor fits, up to 300 trees) -- confirmed
    // live that its default settle wait is nowhere near enough: the cell
    // was still showing "[*]" (running) seconds later, so the check cell
    // below ran immediately behind it with nothing yet in `globals()`.
    await page.waitForTimeout(60_000);
    // Only the newly-filled cell + its own check cell need to run here --
    // NOT a full runAllCells(), which would also re-run every cell above
    // (harmless on its own, but see the pipeline blank below, where a full
    // re-run would repeat a multi-minute computation for no reason).
    await runCell(page, "EXPECTED_SWEEP_MIN_VAL_MSE = 18.73");

    const sweepCheck = await scrollToVisible(page, "Looks good: minimum validation MSE across the sweep");
    await expect(sweepCheck.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    await fillBlank(
      page,
      "# param_grid = [",
      "param_grid = [\n" +
        "    {'learning_rate': [lr], 'n_estimators': [n], 'max_depth': max_depth_grid}\n" +
        "    for lr, n in lr_n_estimators_pairs\n" +
        "]\n" +
        "cv = KFold(n_splits=5, shuffle=True, random_state=13)\n" +
        "boosting_search = GridSearchCV(GradientBoostingRegressor(random_state=42), param_grid, scoring='neg_mean_squared_error', cv=cv)\n" +
        "boosting_search.fit(X_train, y_train)\n" +
        "boosting_best_model = boosting_search.best_estimator_\n" +
        "boosting_test_pred = boosting_best_model.predict(X_test)\n" +
        "boosting_test_mse = mean_squared_error(y_test, boosting_test_pred)\n" +
        "boosting_test_r2 = r2_score(y_test, boosting_test_pred)\n" +
        "print(boosting_test_mse, boosting_test_r2)",
    );

    // fillBlank()'s own Shift+Enter already started the GridSearchCV fit
    // (12-candidate reduced grid, 5 folds each, up to 200 trees per
    // candidate) -- the heaviest single computation in this notebook.
    // scripts/gradient_boosting_model_audit.py's own committed timing
    // audit (book/config/abide_modeling.json's
    // gradient_boosting.cv_pipeline.runtime_audit) measured this exact
    // reduced grid at ~153s on a native machine; confirmed live that
    // Pyodide's WASM-compiled scikit-learn (no native BLAS, tree-building
    // is not BLAS-vectorized to begin with) takes considerably longer than
    // that on top, hence the long wait budget here. Deliberately NOT a
    // full runAllCells(): that would restart this same multi-minute fit
    // from scratch on every later blank in this test, instead of running
    // forward from where the kernel already is.
    await page.waitForTimeout(900_000);
    // Step forward through the check cell and the supplied
    // boosting_cv_results builder cell -- not a full re-run. (The
    // results-intro markdown cell between them needs no execution: a
    // notebook's markdown cells render from their stored source
    // automatically, with no "run" step required.)
    await runCell(page, "EXPECTED_CV_BEST_MEAN_MSE = 27.4236");
    await runCell(page, 'boosting_cv_results = pd.DataFrame(boosting_search.cv_results_["params"])');

    const pipelineCheck = await scrollToVisible(page, "Looks good: selected {'learning_rate'");
    await expect(pipelineCheck.locator(".jp-OutputArea-output").last()).toContainText("locked-test MSE");

    await fillBlank(
      page,
      "# slice_a = boosting_cv_results",
      "slice_a = boosting_cv_results[boosting_cv_results['max_depth'] == 2].sort_values(['learning_rate', 'n_estimators'])\n" +
        "labels_a = [f'lr={row.learning_rate}\\ndepth2' for row in slice_a.itertuples()]\n" +
        "boosting_bar_fig_a, ax = plt.subplots()\n" +
        "ax.bar(labels_a, slice_a['mean_cv_mse'])\n" +
        "plt.show()\n" +
        "slice_b = boosting_cv_results[boosting_cv_results['learning_rate'] == 0.1].sort_values(['n_estimators', 'max_depth'])\n" +
        "labels_b = [f'n={row.n_estimators}\\nd={row.max_depth}' for row in slice_b.itertuples()]\n" +
        "boosting_bar_fig_b, ax = plt.subplots()\n" +
        "ax.bar(labels_b, slice_b['mean_cv_mse'])\n" +
        "plt.show()",
    );

    // Cheap (filtering/plotting an already-computed DataFrame, no model
    // fitting), but give it a short settle buffer before checking anyway.
    await page.waitForTimeout(10_000);
    // Only this blank's own check cell needs to run.
    await runCell(page, "define boosting_bar_fig_a and boosting_bar_fig_b above first");

    const barCheck = await scrollToVisible(page, "Looks good: plot A compares");
    await expect(barCheck.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    const q1 = await scrollToVisible(
      page,
      "Does a new tree in gradient boosting predict the target directly",
      ".jp-OutputArea-output",
    );
    const q1Labels = q1.locator(".widget-radio-box label");
    await expect(q1Labels.first()).toBeVisible({ timeout: 5_000 });
    await q1Labels.first().click();
    await q1.locator("button", { hasText: "Check answer" }).click();
    await page.waitForTimeout(500);
    await expect(q1.locator("text=/^Correct:/")).toBeVisible();

    // Download contains the completed work.
    const downloadDir = fs.mkdtempSync(path.join(os.tmpdir(), "wp46-e2e-"));
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.click("text=Download my notebook"),
    ]);
    const savePath = path.join(downloadDir, "exercise_07.ipynb");
    await download.saveAs(savePath);
    const downloaded = fs.readFileSync(savePath, "utf8");
    expect(downloaded).not.toContain("# YOUR CODE HERE\\n# boosting_sweep_results");
    expect(downloaded).toContain("boosting_search = GridSearchCV(");
  });
});
