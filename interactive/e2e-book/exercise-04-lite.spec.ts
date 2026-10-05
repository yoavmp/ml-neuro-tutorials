import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

// End-to-end proof that the migrated Exercise 4 JupyterLite notebook works
// in a real browser against the actual combined jupyter-book + jupyter-lite
// build (WP45), modeled directly on exercise-03-lite.spec.ts. Requires
// `jupyter lite build --config book/lite/jupyter_lite_config.json --lite-dir
// book/lite --output-dir book/_build/html/lite` to have already run.
//
// Unlike Exercise 3, none of this notebook's two "YOUR CODE HERE" blanks
// (Section 3's cross-validation, Section 5's nested cross-validation) are
// guarded by a raise-on-missing-prerequisite cell: each one's own check
// cell degrades gracefully to "Not complete yet" instead, so "Run All
// Cells" on the UNTOUCHED template produces zero error cells at all. This
// file tests both: the untouched template's graceful no-cascade behavior,
// and a teacher-only completed path (typed in live, exactly like a student
// filling in the blanks) that reproduces the established mean
// cross-validation MSE and nested-CV result and exercises every native
// widget and checked question.

// WP49: bumped from 180_000 -- waitForKernelIdle's own up-to-600_000ms
// budget needs headroom beyond the old fixed-wait assumption this default
// was sized for (found live on CI: this file's teacher-completed test
// failed with the old fixed 140_000ms wait, even running completely
// serialized with nothing else contending).
test.setTimeout(300_000);

const NOTEBOOK_URL = "/lite/notebooks/index.html?path=exercise_04.ipynb";

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

// WP49: found live on CI -- this file's teacher-completed test failed
// with the old fixed 140_000ms wait, even running completely isolated
// (nothing else contending). `.jp-Notebook-ExecutionIndicator[data-status]`
// is JupyterLab's own semantic kernel-status attribute (unknown -> busy ->
// idle), confirmed live by watching it transition across a real Run All
// Cells -- polling for "idle" is environment-independent, unlike any
// fixed duration (see exercise-07-lite.spec.ts for the full writeup).
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
  // Playwright's keyboard.type() sends real per-key keydown events, which
  // CodeMirror 6 (JupyterLab's editor) reacts to with its own smart-indent
  // on Enter -- stacking on top of this solution's own explicit leading
  // whitespace and corrupting indented blocks (confirmed live: an
  // IndentationError on a for-loop body typed this way). insertText uses a
  // single CDP Input.insertText call instead, which CodeMirror treats as a
  // plain paste and does not re-indent.
  await page.keyboard.insertText(solution);
  await page.keyboard.press("Shift+Enter");
  await page.waitForTimeout(600);
}

test.describe("Exercise 4 — JupyterLite notebook, untouched template", () => {
  test("Section 1 loads the established data and Section 2's one-split result prints", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    await scrollWindowed(page, 0.05);
    await expect(page.locator("body")).toContainText("1004 participants, 360 brain predictors, target = age", {
      timeout: 5_000,
    });

    const oneSplit = await scrollToVisible(page, "one_split_model = make_pipeline");
    // This cell's output area also carries a benign stderr warning output
    // ahead of the actual print (same two-outputs-per-cell shape WP44
    // documented for a matplotlib-figure-then-print cell); .last() reaches
    // the real printed text.
    await expect(oneSplit.locator(".jp-OutputArea-output").last()).toContainText("test R^2 = 0.664");
  });

  test("no error cells anywhere on an untouched Run All Cells; both blanks degrade to their own guidance", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    expect(await page.locator(".jp-mod-error").count()).toBe(0);

    const cvCheck = await scrollToVisible(page, "define cv_fold_mse and cv_mean_mse above first");
    await expect(cvCheck.locator(".jp-OutputArea-output").last()).toContainText("Not complete yet");

    const nestedCheck = await scrollToVisible(page, "complete the nested cross-validation pipeline above first");
    await expect(nestedCheck.locator(".jp-OutputArea-output").last()).toContainText("Not complete yet");
  });

  test("the One Split or Several Folds widget changes its printed summary when the controls change", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    const widget = await scrollToVisible(page, "sample size:", ".jp-CodeCell");
    await expect(page.locator("body")).toContainText("sample size = 100   seed = 0", { timeout: 5_000 });

    await widget.locator("select").first().selectOption("30");
    await expect(page.locator("body")).toContainText("sample size = 30   seed = 0", { timeout: 10_000 });
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

test.describe("Exercise 4 — JupyterLite notebook, teacher-completed path", () => {
  test("filling in both blanks reproduces the established results and drives the checked questions", async ({
    page,
  }) => {
    test.setTimeout(480_000);
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    // WP49: found live -- WP45's original "# cv_fold_mse = ..." starter
    // comment was rewritten by WP48 (section E.2) into a multi-step
    // guidance block that never contains that literal text any more;
    // this anchor had gone stale and this test had not actually been run
    // since (WP48's own report used ad-hoc scripts, not this file).
    // "Required names: cv_fold_mse" is still unique and present.
    await fillBlank(
      page,
      "Required names: cv_fold_mse",
      "cv_pipe = make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=K_EXAMPLE))\n" +
        "cv_folds = KFold(n_splits=5, shuffle=True, random_state=0)\n" +
        "cv_scores = cross_validate(cv_pipe, X, y, cv=cv_folds, scoring=('neg_mean_squared_error', 'r2'))\n" +
        "cv_fold_mse = -cv_scores['test_neg_mean_squared_error']\n" +
        "cv_mean_mse = cv_fold_mse.mean()\n" +
        "print(cv_mean_mse)",
    );

    await runAllCells(page);
    await page.waitForTimeout(20_000);

    const cvCheck = await scrollToVisible(page, "Looks good: 5 fold MSEs");
    await expect(cvCheck.locator(".jp-OutputArea-output").last()).toContainText("mean MSE = 33.8");

    // Section 4's checked question.
    const q1 = await scrollToVisible(
      page,
      "why can changing only the random seed swing the single-split test R",
      ".jp-OutputArea-output",
    );
    const q1Labels = q1.locator(".widget-radio-box label");
    await expect(q1Labels.first()).toBeVisible({ timeout: 5_000 });
    await q1Labels.first().click();
    await q1.locator("button", { hasText: "Check answer" }).click();
    await page.waitForTimeout(500);
    await expect(q1.locator("text=/^Correct:/")).toBeVisible();

    await fillBlank(
      page,
      "# 1. build a Pipeline(StandardScaler(), KNeighborsRegressor())",
      "NESTED_CANDIDATE_KS = [8, 10, 12, 15, 18, 20, 22, 25, 28, 30, 40, 50]\n" +
        "N_OUTER, N_INNER = 5, 5\n" +
        "OUTER_SEED, INNER_SEED = 100, 101\n" +
        "outer_cv = KFold(n_splits=N_OUTER, shuffle=True, random_state=OUTER_SEED)\n" +
        "inner_cv = KFold(n_splits=N_INNER, shuffle=True, random_state=INNER_SEED)\n" +
        "nested_rows = []\n" +
        "for fold_i, (train_idx, test_idx) in enumerate(outer_cv.split(X)):\n" +
        "    X_tr, X_te = X[train_idx], X[test_idx]\n" +
        "    y_tr, y_te = y[train_idx], y[test_idx]\n" +
        "    pipe = Pipeline([('scaler', StandardScaler()), ('knn', KNeighborsRegressor())])\n" +
        "    grid = GridSearchCV(pipe, param_grid={'knn__n_neighbors': NESTED_CANDIDATE_KS}, scoring='neg_mean_squared_error', cv=inner_cv)\n" +
        "    grid.fit(X_tr, y_tr)\n" +
        "    selected_k = grid.best_params_['knn__n_neighbors']\n" +
        "    pred = grid.predict(X_te)\n" +
        "    nested_rows.append({'outer_fold': fold_i + 1, 'selected_k': selected_k, 'outer_test_mse': mean_squared_error(y_te, pred), 'outer_test_r2': r2_score(y_te, pred)})\n" +
        "nested = pd.DataFrame(nested_rows)\n" +
        "nested.round(3)",
    );

    await runAllCells(page);
    await page.waitForTimeout(30_000);

    const nestedCheck = await scrollToVisible(page, "Looks good: mean outer-test MSE");
    await expect(nestedCheck.locator(".jp-OutputArea-output").last()).toContainText("[15, 12, 10, 18, 15]");

    // Download contains the completed work.
    const downloadDir = fs.mkdtempSync(path.join(os.tmpdir(), "wp45-e2e-"));
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.click("text=Download my notebook"),
    ]);
    const savePath = path.join(downloadDir, "exercise_04.ipynb");
    await download.saveAs(savePath);
    const downloaded = fs.readFileSync(savePath, "utf8");
    expect(downloaded).not.toContain('"# YOUR CODE HERE\\n# 1. create the model/pipeline');
    expect(downloaded).toContain("cv_pipe = make_pipeline");
  });
});
