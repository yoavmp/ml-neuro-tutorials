import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

// End-to-end proof that the migrated Exercise 6 JupyterLite notebook works
// in a real browser against the actual combined jupyter-book + jupyter-lite
// build (WP46), modeled directly on exercise-05-lite.spec.ts. Requires
// `jupyter lite build --config book/lite/jupyter_lite_config.json --lite-dir
// book/lite --output-dir book/_build/html/lite` to have already run.
//
// Neither of this notebook's two "YOUR CODE HERE" blanks (Section 3's
// depth sweep, Section 6's model comparison) is guarded by a raise-on-
// missing-prerequisite cell: each one's own check cell degrades gracefully
// to "Not complete yet" instead, so "Run All Cells" on the UNTOUCHED
// template produces zero error cells at all. This file tests both: the
// untouched template's graceful no-cascade behavior, and a teacher-only
// completed path (typed in live, exactly like a student filling in the
// blanks) that reproduces the established results and exercises the native
// widgets and checked questions.

// WP49: bumped from 180_000 -- waitForKernelIdle's own up-to-
// 600_000ms budget needs headroom beyond the old fixed-wait
// assumption this default was sized for.
test.setTimeout(300_000);

const NOTEBOOK_URL = "/lite/notebooks/index.html?path=exercise_06.ipynb";

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

// WP49: replaced this file's old fixed 150_000ms wait with a poll on
// JupyterLab's own semantic kernel-status attribute (unknown -> busy ->
// idle, confirmed live by watching it transition across a real Run All
// Cells) -- environment-independent, unlike a fixed duration. Found live
// (exercise-04/06/07-lite.spec.ts, WP49): a fixed wait that is usually
// enough can still leave the kernel genuinely busy when a test
// interacts right after, which can trigger a JupyterLite app-level
// reload. See exercise-07-lite.spec.ts for the full writeup.
async function waitForKernelIdle(page: Page, timeoutMs = 600_000) {
  await page.waitForFunction(
    () => document.querySelector(".jp-Notebook-ExecutionIndicator")?.getAttribute("data-status") === "idle",
    undefined,
    { timeout: timeoutMs, polling: 1_000 },
  );
}

async function runAllCells(page: Page) {
  await page.click("text=Run");
  await page.waitForTimeout(200);
  await page.locator(".lm-Menu-itemLabel", { hasText: "Run All Cells" }).first().click();
  await waitForKernelIdle(page);
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

test.describe("Exercise 6 — JupyterLite notebook, untouched template", () => {
  test("Section 1 loads the established data and fits the small tree", async ({ page }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    await scrollWindowed(page, 0.05);
    await expect(page.locator("body")).toContainText("n_fit = 564", { timeout: 5_000 });

    const smallTree = await scrollToVisible(page, "SMALL_TREE_FEATURES = ");
    await expect(smallTree.locator(".jp-OutputArea-output").last()).toContainText("leaves = 8");
  });

  test("no error cells anywhere on an untouched Run All Cells; both blanks degrade to their own guidance", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    expect(await page.locator(".jp-mod-error").count()).toBe(0);

    const depthCheck = await scrollToVisible(page, "define tree_depth_train_mse and tree_depth_val_mse above first");
    await expect(depthCheck.locator(".jp-OutputArea-output").last()).toContainText("Not complete yet");

    const comparisonCheck = await scrollToVisible(page, "define tree_cv_fold_results above first");
    await expect(comparisonCheck.locator(".jp-OutputArea-output").last()).toContainText("Not complete yet");
  });

  test("the Build a Tree Greedily activity locks and reveals the root split", async ({ page }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    const widget = await scrollToVisible(page, "Lock My Answer", ".jp-CodeCell");
    await widget.locator("button", { hasText: "Lock My Answer" }).click();
    await page.waitForTimeout(400);
    const revealBtn = widget.locator("button", { hasText: "Reveal Best Split" });
    await expect(revealBtn).toBeEnabled({ timeout: 5_000 });
    await revealBtn.click();
    await page.waitForTimeout(400);
    await expect(page.locator("body")).toContainText("Greedy optimum", { timeout: 5_000 });
  });

  test("the One Tree or Many? widget changes its summary table when the number of trees changes", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    const widget = await scrollToVisible(page, "Number of trees:", ".jp-CodeCell");
    // This widget's plots/print run inside an ipywidgets.Output() context,
    // whose content is not part of the notebook cell's own
    // .jp-OutputArea-output tree (it lives in the widget's own
    // comm-synced view) -- checked against the full page body instead,
    // exactly like exercise-04-lite.spec.ts's "sample size:" widget.
    await expect(page.locator("body")).toContainText("number of trees = 50", { timeout: 5_000 });
    // Plain-int Dropdown options: select by fixed position, not by value
    // (WP44/45 documented ipywidgets.Dropdown value/HTML-option mismatch).
    await widget.locator("select").first().selectOption({ index: 0 });
    await expect(page.locator("body")).toContainText("number of trees = 1 ", { timeout: 10_000 });
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

test.describe("Exercise 6 — JupyterLite notebook, teacher-completed path", () => {
  test("filling in both blanks reproduces the established results and drives the checked questions", async ({
    page,
  }) => {
    test.setTimeout(480_000);
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    await fillBlank(
      page,
      "# tree_depth_train_mse = []",
      "tree_depth_train_mse = []\n" +
        "tree_depth_val_mse = []\n" +
        "for d in MAX_DEPTHS:\n" +
        "    t = DecisionTreeRegressor(max_depth=d, min_samples_leaf=5, random_state=42)\n" +
        "    t.fit(X_fit, y_fit)\n" +
        "    tree_depth_train_mse.append(mean_squared_error(y_fit, t.predict(X_fit)))\n" +
        "    tree_depth_val_mse.append(mean_squared_error(y_val, t.predict(X_val)))\n" +
        "tree_depth_fig, ax = plt.subplots()\n" +
        "ax.plot(MAX_DEPTHS, tree_depth_train_mse, marker='o', label='training MSE')\n" +
        "ax.plot(MAX_DEPTHS, tree_depth_val_mse, marker='o', label='validation MSE')\n" +
        "ax.legend()\n" +
        "plt.show()",
    );

    await runAllCells(page);
    await page.waitForTimeout(30_000);

    const depthCheck = await scrollToVisible(page, "Looks good: best depth by validation MSE");
    await expect(depthCheck.locator(".jp-OutputArea-output").last()).toContainText("best depth by validation MSE = 2");

    const q1 = await scrollToVisible(page, "Which depth should we select before predicting the test set?", ".jp-OutputArea-output");
    const q1Labels = q1.locator(".widget-radio-box label");
    await expect(q1Labels.first()).toBeVisible({ timeout: 5_000 });
    await q1Labels.first().click();
    await q1.locator("button", { hasText: "Check answer" }).click();
    await page.waitForTimeout(500);
    await expect(q1.locator("text=/^Correct:/")).toBeVisible();

    await fillBlank(
      page,
      "# cv = KFold(n_splits=5, shuffle=True, random_state=100)",
      "cv = KFold(n_splits=5, shuffle=True, random_state=100)\n" +
        "tree_settings = dict(max_depth=6, min_samples_leaf=5, random_state=42)\n" +
        "models = {\n" +
        "    'Single tree': DecisionTreeRegressor(**tree_settings),\n" +
        "    'Bagging': BaggingRegressor(DecisionTreeRegressor(**tree_settings), n_estimators=50, random_state=42),\n" +
        "    'Random Forest': RandomForestRegressor(n_estimators=50, max_features=19, **tree_settings),\n" +
        "}\n" +
        "tree_cv_fold_results = {name: {'mse': [], 'r2': []} for name in models}\n" +
        "for train_idx, val_idx in cv.split(X):\n" +
        "    X_tr, X_va = X[train_idx], X[val_idx]\n" +
        "    y_tr, y_va = y[train_idx], y[val_idx]\n" +
        "    for name, model in models.items():\n" +
        "        model.fit(X_tr, y_tr)\n" +
        "        pred = model.predict(X_va)\n" +
        "        tree_cv_fold_results[name]['mse'].append(mean_squared_error(y_va, pred))\n" +
        "        tree_cv_fold_results[name]['r2'].append(r2_score(y_va, pred))",
    );

    await runAllCells(page);
    // The comparison loop fits Single tree/Bagging/Random Forest (bagging
    // and Random Forest at n_estimators=50) across 5 folds on the full
    // 1004x360 cohort -- noticeably heavier than the depth-sweep blank
    // above, hence the longer wait budget here.
    await page.waitForTimeout(90_000);

    const comparisonCheck = await scrollToVisible(page, "Looks good: single tree mean MSE");
    await expect(comparisonCheck.locator(".jp-OutputArea-output").last()).toContainText("both ensembles score lower");

    // Download contains the completed work.
    const downloadDir = fs.mkdtempSync(path.join(os.tmpdir(), "wp46-e2e-"));
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.click("text=Download my notebook"),
    ]);
    const savePath = path.join(downloadDir, "exercise_06.ipynb");
    await download.saveAs(savePath);
    const downloaded = fs.readFileSync(savePath, "utf8");
    expect(downloaded).not.toContain("# YOUR CODE HERE\\n# tree_depth_train_mse");
    expect(downloaded).toContain("tree_cv_fold_results = {name:");
  });
});
