import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

// End-to-end proof that the migrated Exercise 5 JupyterLite notebook works
// in a real browser against the actual combined jupyter-book + jupyter-lite
// build (WP45), modeled directly on exercise-03-lite.spec.ts and
// exercise-04-lite.spec.ts. Requires `jupyter lite build --config
// book/lite/jupyter_lite_config.json --lite-dir book/lite --output-dir
// book/_build/html/lite` to have already run.
//
// None of this notebook's three "YOUR CODE HERE" blanks (Section 3's
// feature selection, Section 4's Lasso fit, Section 5's Lasso CV tuning)
// are guarded by a raise-on-missing-prerequisite cell: each one's own check
// cell (or, for the two supplied comparison cells, an `if` guard) degrades
// gracefully to "Not complete yet" instead, so "Run All Cells" on the
// UNTOUCHED template produces zero error cells at all.

test.setTimeout(180_000);

const NOTEBOOK_URL = "/lite/notebooks/index.html?path=exercise_05.ipynb";

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
  // Playwright's keyboard.type() sends real per-key keydown events, which
  // CodeMirror 6 (JupyterLab's editor) reacts to with its own smart-indent
  // on Enter -- stacking on top of this solution's own explicit leading
  // whitespace and corrupting indented blocks (confirmed live on Exercise
  // 4's nested-CV blank: an IndentationError on a for-loop body typed this
  // way). insertText uses a single CDP Input.insertText call instead,
  // which CodeMirror treats as a plain paste and does not re-indent.
  await page.keyboard.insertText(solution);
  await page.keyboard.press("Shift+Enter");
  await page.waitForTimeout(600);
}

test.describe("Exercise 5 — JupyterLite notebook, untouched template", () => {
  test("Section 1 loads the established data and Section 2's predefined-comparison widget renders", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);
    await page.waitForTimeout(140_000);

    await scrollWindowed(page, 0.03);
    await expect(page.locator("body")).toContainText("360 predictors, e.g.", { timeout: 5_000 });

    const widget = await scrollToVisible(page, "Model A:", ".jp-CodeCell");
    await expect(widget.locator(".jp-OutputArea-output img, .jp-OutputArea-output canvas").first()).toBeVisible({
      timeout: 5_000,
    });
  });

  test("no error cells anywhere on an untouched Run All Cells; every blank degrades to its own guidance", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);
    await page.waitForTimeout(140_000);

    expect(await page.locator(".jp-mod-error").count()).toBe(0);

    const selectCheck = await scrollToVisible(
      page,
      "define selected_features, selected_model, and selected_test_mse above first",
    );
    await expect(selectCheck.locator(".jp-OutputArea-output").last()).toContainText("Not complete yet");

    const lassoCheck = await scrollToVisible(page, "define lasso_model, lasso_pred, and lasso_mse above first");
    await expect(lassoCheck.locator(".jp-OutputArea-output").last()).toContainText("Not complete yet");

    const lassoCvCheck = await scrollToVisible(
      page,
      "define lasso_cv_alpha, lasso_cv_pred, and lasso_cv_test_mse above first",
    );
    await expect(lassoCvCheck.locator(".jp-OutputArea-output").last()).toContainText("Not complete yet");
  });

  test("changing the predefined comparison bundles updates the printed R^2 table", async ({ page }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);
    await page.waitForTimeout(140_000);

    const widget = await scrollToVisible(page, "Model A:", ".jp-CodeCell");
    const before = await widget.locator(".jp-OutputArea-output").first().innerText();
    const selects = widget.locator("select");
    // ipywidgets renders a Dropdown built from (label, value) tuples with
    // the HTML <option>'s own value attribute set to an internal index, not
    // the semantic bundle key, and matching by {label:...} was also found
    // (live) not to satisfy Playwright's actionability check on this
    // widget's <select> -- select by fixed position instead: BUNDLE_ORDER
    // in the generator is [frontoparietal, frontal, parietal, temporal,
    // occipital, sensorimotor, all-eligible], so index 6 is "All eligible
    // ROIs" (confirmed against the same live snapshot).
    await selects.first().selectOption({ index: 6 });
    await page.waitForTimeout(1500);
    const after = await widget.locator(".jp-OutputArea-output").first().innerText();
    expect(after).not.toEqual(before);
    expect(after).toContain("360");
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

test.describe("Exercise 5 — JupyterLite notebook, teacher-completed path", () => {
  test("filling in every blank reproduces the established results and drives the checked questions", async ({
    page,
  }) => {
    test.setTimeout(600_000);
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);
    await page.waitForTimeout(140_000);

    await fillBlank(
      page,
      "# selector = SelectKBest",
      "K_SELECT = 80\n" +
        "selector = SelectKBest(score_func=f_regression, k=K_SELECT).fit(X_train, y_train)\n" +
        "selected_idx = selector.get_support(indices=True)\n" +
        "selected_features = [FEATURES[i] for i in selected_idx]\n" +
        "selected_model = make_pipeline(StandardScaler(), LinearRegression())\n" +
        "selected_model.fit(X_train[:, selected_idx], y_train)\n" +
        "selected_pred = selected_model.predict(X_test[:, selected_idx])\n" +
        "selected_test_mse = mean_squared_error(y_test, selected_pred)\n" +
        "print(selected_test_mse)",
    );

    await runAllCells(page);
    await page.waitForTimeout(20_000);
    const selectCheck = await scrollToVisible(page, "features selected, held-out MSE");
    await expect(selectCheck.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    await fillBlank(
      page,
      "# LASSO_ALPHA = ...",
      "LASSO_ALPHA = 0.1\n" +
        "lasso_model = make_pipeline(StandardScaler(), Lasso(alpha=LASSO_ALPHA, max_iter=20000))\n" +
        "lasso_model.fit(X_train, y_train)\n" +
        "lasso_pred = lasso_model.predict(X_test)\n" +
        "lasso_mse = mean_squared_error(y_test, lasso_pred)\n" +
        "lasso_nonzero = int(np.sum(np.abs(lasso_model.named_steps['lasso'].coef_) > 1e-10))\n" +
        "print(lasso_mse, lasso_nonzero)",
    );

    await runAllCells(page);
    await page.waitForTimeout(20_000);
    const lassoCheck = await scrollToVisible(page, "coefficients are nonzero.");
    await expect(lassoCheck.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    // Section 3's checked question.
    const q1 = await scrollToVisible(page, "Why must SelectKBest be fit on X_train/y_train only", ".jp-OutputArea-output");
    const q1Labels = q1.locator(".widget-radio-box label");
    await expect(q1Labels.first()).toBeVisible({ timeout: 5_000 });
    await q1Labels.first().click();
    await q1.locator("button", { hasText: "Check answer" }).click();
    await page.waitForTimeout(500);
    await expect(q1.locator("text=Correct")).toBeVisible();

    await fillBlank(
      page,
      "# 1. build a Pipeline(StandardScaler(), Lasso",
      "lasso_cv_pipe = Pipeline([('scaler', StandardScaler()), ('lasso', Lasso(max_iter=20000, tol=1e-3))])\n" +
        "lasso_cv_search_cv = KFold(n_splits=5, shuffle=True, random_state=0)\n" +
        "lasso_cv_model = GridSearchCV(lasso_cv_pipe, {'lasso__alpha': LASSO_ALPHAS}, scoring='neg_mean_squared_error', cv=lasso_cv_search_cv)\n" +
        "lasso_cv_model.fit(X_train, y_train)\n" +
        "lasso_cv_alpha = lasso_cv_model.best_params_['lasso__alpha']\n" +
        "lasso_cv_pred = lasso_cv_model.predict(X_test)\n" +
        "lasso_cv_test_mse = mean_squared_error(y_test, lasso_cv_pred)\n" +
        "print(lasso_cv_alpha, lasso_cv_test_mse)",
    );

    await runAllCells(page);
    await page.waitForTimeout(30_000);
    await scrollToVisible(page, "selected alpha =");
    await expect(page.locator("body")).toContainText("Looks good: selected alpha", { timeout: 5_000 });
    await expect(page.locator("body")).toContainText("coefficients are nonzero (tolerance", { timeout: 5_000 });

    // Download contains the completed work.
    const downloadDir = fs.mkdtempSync(path.join(os.tmpdir(), "wp45-e2e-"));
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.click("text=Download my notebook"),
    ]);
    const savePath = path.join(downloadDir, "exercise_05.ipynb");
    await download.saveAs(savePath);
    const downloaded = fs.readFileSync(savePath, "utf8");
    expect(downloaded).not.toContain('"# YOUR CODE HERE\\n# selector = SelectKBest');
    expect(downloaded).toContain("lasso_cv_pipe");
  });
});
