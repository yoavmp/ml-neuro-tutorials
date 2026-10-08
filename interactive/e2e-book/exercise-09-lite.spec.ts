import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

// End-to-end proof that the WP52-corrected Exercise 9 JupyterLite notebook
// works in a real browser against the actual combined jupyter-book +
// jupyter-lite build, modeled directly on exercise-08-lite.spec.ts's own
// patterns. Exercise 9's own checked questions no longer have their
// correct answer first (WP52 item 6: reproducibly shuffled per question),
// so every "click the correct option" step below selects by the option's
// own TEXT, never by position -- this is itself part of what this file is
// verifying, not an implementation detail to work around.

test.setTimeout(240_000);

const NOTEBOOK_URL = "/lite/notebooks/index.html?path=exercise_09.ipynb";

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
  await page.keyboard.insertText(solution);
  await page.keyboard.press("Shift+Enter");
  await page.waitForTimeout(600);
}

async function runCell(page: Page, anchorText: string) {
  const target = await scrollToVisible(page, anchorText);
  const editor = target.locator(".cm-content").first();
  await editor.click();
  await page.waitForTimeout(150);
  await page.keyboard.press("Shift+Enter");
  await page.waitForTimeout(1_500);
}

// Click the single-choice radio option whose own text is `correctText` --
// never by position, since WP52 item 6 reproducibly shuffles every
// question's displayed order.
async function answerSingleChoice(page: Page, promptAnchor: string, optionText: string) {
  const q = await scrollToVisible(page, promptAnchor, ".jp-OutputArea-output");
  const label = q.locator(".widget-radio-box label", { hasText: optionText });
  await expect(label).toBeVisible({ timeout: 5_000 });
  await label.click();
  await q.locator("button", { hasText: "Check" }).click();
  await page.waitForTimeout(400);
  return q;
}

const PCR_VS_PLS_PROMPT = "Both PCR and PLS build a small number of components";
const PCR_VS_PLS_CORRECT =
  "PCR's components are chosen using X alone; PLS's components use the relationship between X and y";
const LEAKAGE_PROMPT = "Why must StandardScaler and PCA (or PLSRegression) be fit only on";
const LEAKAGE_CORRECT = "Fitting them on the full dataset lets information from the validation rows leak";
const TRAIN_VS_VAL_PROMPT = "In the SVM boundary activity, one setting reaches very high";
const TRAIN_VS_VAL_CORRECT = "A boundary that fits the training data extremely closely is not guaranteed to generalize";
const EXACT_VS_APPROX_PROMPT = "What is the relationship between ordinary Ridge regression and";
const EXACT_VS_APPROX_CORRECT = "KernelRidge(kernel='rbf') is the exact RBF-kernel counterpart of L2-regularized (Ridge) regression";
const MULTISELECT_PROMPT = "Which of the following statements about SVM/SVR parameters are true?";
const MULTISELECT_CORRECT = [
  "Larger C pushes the model to fit training points more closely",
  "For an RBF kernel, larger gamma makes the decision boundary more local and flexible.",
  "In SVR, a larger epsilon widens the band of regression error that receives no penalty at all.",
];
const MULTISELECT_WRONG = "epsilon is a classification-only parameter, used by SVC rather than SVR.";

test.describe("Exercise 9 — JupyterLite notebook, untouched template", () => {
  test("Run All Cells: no error cells, data loads, both widgets render, and every blank's check cell shows guidance", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    expect(await page.locator(".jp-mod-error").count()).toBe(0);

    await scrollWindowed(page, 0.05);
    await expect(page.locator("body")).toContainText("360 cortical-thickness predictors", { timeout: 5_000 });

    for (const anchor of [
      "define pcr_results above first",
      "define pls_results above first",
      "define svr_results above first",
      "define ridge_result, kernel_ridge_result above first",
    ]) {
      const cell = await scrollToVisible(page, anchor);
      await expect(cell.locator(".jp-OutputArea-output").last()).toContainText("Not complete yet");
    }

    // Both native widgets render and produce a live summary line even
    // though every blank above/around them was left untouched.
    await expect(page.locator("body")).toContainText("weight on PC1=0.25");
    await expect(page.locator("body")).toContainText("dataset=nonlinear");

    // Section 6's instructor SVR benchmark always shows, regardless of
    // which blanks are complete (WP52 item 13).
    await expect(page.locator("body")).toContainText("SVR (instructor reference, full training data)");
  });

  test("stays usable at a 390px viewport, and every widget control label stays fully readable", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await page.waitForTimeout(4000);

    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(2);

    // WP52 items 3/8: scroll to each widget and confirm every control
    // label is neither clipped within its own box nor overlapping the
    // control next to it.
    for (const anchor of ["_pcrpls_w1_dd = widgets.Dropdown", "_svm_dataset_dd = widgets.Dropdown"]) {
      await runAllCells(page).catch(() => {}); // no-op if already idle; ensures widgets have rendered
      const cell = await scrollToVisible(page, anchor);
      const labels = cell.locator(".widget-controls-row .widget-label");
      const count = await labels.count();
      expect(count).toBeGreaterThan(0);
      const boxes: { left: number; right: number; top: number; bottom: number }[] = [];
      for (let i = 0; i < count; i++) {
        const label = labels.nth(i);
        const notClipped = await label.evaluate((el) => el.scrollWidth <= el.clientWidth + 2);
        expect(notClipped).toBe(true);
        const box = await label.boundingBox();
        if (box) boxes.push({ left: box.x, right: box.x + box.width, top: box.y, bottom: box.y + box.height });
      }
      // No two labels' bounding boxes overlap each other.
      for (let i = 0; i < boxes.length; i++) {
        for (let j = i + 1; j < boxes.length; j++) {
          const a = boxes[i]!;
          const b = boxes[j]!;
          const overlapsX = a.left < b.right && b.left < a.right;
          const overlapsY = a.top < b.bottom && b.top < a.bottom;
          expect(overlapsX && overlapsY).toBe(false);
        }
      }
    }
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

test.describe("Exercise 9 — JupyterLite notebook, teacher-completed path", () => {
  test("filling in all four blanks reproduces the established results, both widgets respond live, every checked question grades correctly after shuffling, and download contains the edits", async ({
    page,
  }) => {
    test.setTimeout(600_000);
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    await fillBlank(
      page,
      "PCR_COMPONENT_GRID = [2, 5, 10, 20, 50]",
      "PCR_COMPONENT_GRID = [2, 5, 10, 20, 50]\n" +
        "pcr_results = []\n" +
        "from sklearn.preprocessing import StandardScaler\n" +
        "from sklearn.decomposition import PCA\n" +
        "from sklearn.linear_model import LinearRegression\n" +
        "from sklearn.pipeline import Pipeline\n" +
        "from sklearn.metrics import mean_squared_error, r2_score\n" +
        "for n in PCR_COMPONENT_GRID:\n" +
        "    pipe = Pipeline([('scale', StandardScaler()), ('pca', PCA(n_components=n, random_state=0)), ('model', LinearRegression())])\n" +
        "    pipe.fit(X_train, y_train)\n" +
        "    pred = pipe.predict(X_val)\n" +
        "    pcr_results.append({'n_components': n, 'val_mse': float(mean_squared_error(y_val, pred)), 'val_r2': float(r2_score(y_val, pred))})\n" +
        "print(pcr_results)",
    );
    await page.waitForTimeout(3_000);
    await runCell(page, "EXPECTED_PCR_MSE = ");
    let check = await scrollToVisible(page, "Looks good: your PCR validation MSE/R2");
    await expect(check.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    await fillBlank(
      page,
      "PLS_COMPONENT_GRID = [2, 5, 10, 20, 50]",
      "PLS_COMPONENT_GRID = [2, 5, 10, 20, 50]\n" +
        "pls_results = []\n" +
        "from sklearn.cross_decomposition import PLSRegression\n" +
        "for n in PLS_COMPONENT_GRID:\n" +
        "    pipe = Pipeline([('scale', StandardScaler()), ('model', PLSRegression(n_components=n, scale=False))])\n" +
        "    pipe.fit(X_train, y_train)\n" +
        "    pred = pipe.predict(X_val).ravel()\n" +
        "    pls_results.append({'n_components': n, 'val_mse': float(mean_squared_error(y_val, pred)), 'val_r2': float(r2_score(y_val, pred))})\n" +
        "print(pls_results)",
    );
    await page.waitForTimeout(3_000);
    await runCell(page, "EXPECTED_PLS_MSE = ");
    check = await scrollToVisible(page, "Looks good: your PLS validation MSE/R2");
    await expect(check.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    // Re-run the PCR/PLS widget now that both blanks are complete, then
    // confirm changing BOTH controls visibly updates the live summary and
    // that the label fix (item 3) still produces full-text, non-overlapping
    // labels at desktop width.
    const PCRPLS_ANCHOR = "_pcrpls_w1_dd = widgets.Dropdown";
    await runCellReturning(page, PCRPLS_ANCHOR);
    await page.waitForTimeout(1_000);
    await expect(page.locator("body")).toContainText("weight on PC1=0.25  components=1", { timeout: 5_000 });
    // Shift+Enter advances JupyterLab's active cell and can scroll the
    // widget back out of the windowed notebook's rendered range -- re-find
    // it (scrolling back into view if needed) immediately before each
    // interaction, rather than reusing a locator across time/scroll changes.
    let widgetCell = await scrollToVisible(page, PCRPLS_ANCHOR);
    await widgetCell.locator("select").nth(0).selectOption({ label: "0.9" }, { timeout: 15_000 });
    await page.waitForTimeout(1_000);
    await expect(page.locator("body")).toContainText("weight on PC1=0.90", { timeout: 5_000 });
    widgetCell = await scrollToVisible(page, PCRPLS_ANCHOR);
    await widgetCell.locator("select").nth(1).selectOption({ index: 1 }, { timeout: 15_000 }); // Components -> 2
    await page.waitForTimeout(1_000);
    await expect(page.locator("body")).toContainText("components=2", { timeout: 5_000 });

    await fillBlank(
      page,
      "_svr_subset_rng = np.random.RandomState(0)",
      "from sklearn.svm import SVR\n" +
        "from sklearn.metrics import r2_score\n" +
        "SVR_PARAM_SETS = [\n" +
        "    {'kernel': 'linear', 'C': 1, 'gamma': None, 'epsilon': 1},\n" +
        "    {'kernel': 'linear', 'C': 10, 'gamma': None, 'epsilon': 1},\n" +
        "    {'kernel': 'rbf', 'C': 1, 'gamma': 'scale', 'epsilon': 1},\n" +
        "    {'kernel': 'rbf', 'C': 10, 'gamma': 'scale', 'epsilon': 1},\n" +
        "    {'kernel': 'rbf', 'C': 100, 'gamma': 'scale', 'epsilon': 1},\n" +
        "]\n" +
        "_svr_subset_rng = np.random.RandomState(0)\n" +
        "_svr_subset_idx = _svr_subset_rng.choice(len(X_train), size=300, replace=False)\n" +
        "X_train_svr_subset = X_train[_svr_subset_idx]\n" +
        "y_train_svr_subset = y_train[_svr_subset_idx]\n" +
        "svr_results = []\n" +
        "for params in SVR_PARAM_SETS:\n" +
        "    svr_kwargs = {k: v for k, v in params.items() if v is not None}\n" +
        "    pipe = Pipeline([('scale', StandardScaler()), ('svr', SVR(**svr_kwargs))])\n" +
        "    pipe.fit(X_train_svr_subset, y_train_svr_subset)\n" +
        "    pred = pipe.predict(X_val)\n" +
        "    svr_results.append({**params, 'val_mse': float(mean_squared_error(y_val, pred)), 'val_r2': float(r2_score(y_val, pred))})\n" +
        "print(svr_results)",
    );
    await page.waitForTimeout(3_000);
    await runCell(page, "EXPECTED_SVR_BEST_KERNEL = ");
    check = await scrollToVisible(page, "Looks good: best config");
    await expect(check.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    await fillBlank(
      page,
      'from sklearn.kernel_ridge import KernelRidge',
      "from sklearn.linear_model import Ridge\n" +
        "from sklearn.kernel_ridge import KernelRidge\n" +
        "ridge_pipe = Pipeline([('scale', StandardScaler()), ('model', Ridge(alpha=100))]).fit(X_train, y_train)\n" +
        "ridge_pred = ridge_pipe.predict(X_val)\n" +
        "ridge_result = {'val_mse': float(mean_squared_error(y_val, ridge_pred)), 'val_r2': float(r2_score(y_val, ridge_pred))}\n" +
        "kernel_ridge_pipe = Pipeline([('scale', StandardScaler()), ('model', KernelRidge(kernel='rbf', alpha=0.1, gamma=0.001))]).fit(X_train, y_train)\n" +
        "kernel_ridge_pred = kernel_ridge_pipe.predict(X_val)\n" +
        "kernel_ridge_result = {'val_mse': float(mean_squared_error(y_val, kernel_ridge_pred)), 'val_r2': float(r2_score(y_val, kernel_ridge_pred))}\n" +
        "print(ridge_result, kernel_ridge_result)",
    );
    await page.waitForTimeout(3_000);
    await runCell(page, "EXPECTED_RIDGE_MSE = ");
    check = await scrollToVisible(page, "Looks good: Ridge val_mse");
    await expect(check.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    // Re-run the SVM widget and confirm changing the dataset dropdown
    // visibly updates the live summary line.
    const SVM_ANCHOR = "_svm_dataset_dd = widgets.Dropdown";
    await runCellReturning(page, SVM_ANCHOR);
    await page.waitForTimeout(1_000);
    const svmWidget = await scrollToVisible(page, SVM_ANCHOR);
    await svmWidget.locator("select").nth(0).selectOption({ index: 0 }, { timeout: 15_000 }); // "Linearly separable blobs"
    await page.waitForTimeout(1_000);
    await expect(page.locator("body")).toContainText("dataset=linear", { timeout: 5_000 });

    // Section 6's own cell does not re-run just because an earlier cell
    // changed (no notebook cascades) -- re-run it now that every blank is
    // complete, so its table picks up all four results.
    await runCell(page, "SVR_BENCHMARK = ");
    await page.waitForTimeout(1_000);

    // The full-training-data table now includes every blank's result,
    // PLUS the separate, labeled instructor SVR benchmark row -- never
    // the student's own subset result ranked alongside them.
    const compareCell = await scrollToVisible(page, "KernelRidge (RBF, full training data)", ".jp-OutputArea-output");
    await expect(compareCell).toContainText("KernelRidge (RBF, full training data)");
    await expect(compareCell).toContainText("SVR (instructor reference, full training data)");
    await expect(page.locator("body")).toContainText("Your own SVR activity (Section 4, 300-row training subset)");

    // Every checked question: correct feedback, selected by option TEXT
    // (never position -- WP52 item 6 shuffles every question).
    for (const [prompt, correct] of [
      [PCR_VS_PLS_PROMPT, PCR_VS_PLS_CORRECT],
      [LEAKAGE_PROMPT, LEAKAGE_CORRECT],
      [TRAIN_VS_VAL_PROMPT, TRAIN_VS_VAL_CORRECT],
      [EXACT_VS_APPROX_PROMPT, EXACT_VS_APPROX_CORRECT],
    ] as const) {
      const q = await answerSingleChoice(page, prompt, correct);
      await expect(q.locator("text=/^Correct/")).toBeVisible();
      expect(await q.innerText()).not.toContain("correct_index");
    }

    // The multiselect question: select exactly the three true statements.
    const mq = await scrollToVisible(page, MULTISELECT_PROMPT, ".jp-OutputArea-output");
    for (const statementText of MULTISELECT_CORRECT) {
      await mq.locator(".widget-checkbox label", { hasText: statementText }).click();
    }
    await mq.locator("button", { hasText: "Check answers" }).click();
    await page.waitForTimeout(400);
    await expect(mq.locator("text=/^Correct/")).toBeVisible();
    expect(await mq.innerText()).not.toContain("correct_indices");

    // One question, deliberately answered wrong: incorrect feedback, no
    // "Correct" text, no visible answer key.
    const wrongQ = await answerSingleChoice(page, LEAKAGE_PROMPT, "It doesn't actually matter");
    await expect(wrongQ.locator("text=/^Not quite/")).toBeVisible();

    // One multiselect question, deliberately partially wrong: sensible
    // partial feedback, still no visible answer key.
    const partialQ = await scrollToVisible(page, MULTISELECT_PROMPT, ".jp-OutputArea-output");
    await partialQ.locator(".widget-checkbox label", { hasText: MULTISELECT_WRONG }).click();
    await partialQ.locator("button", { hasText: "Check answers" }).click();
    await page.waitForTimeout(400);
    await expect(partialQ.locator("text=/true statements selected/")).toBeVisible();
    expect(await partialQ.innerText()).not.toContain("correct_indices");

    // Download contains the completed work.
    const downloadDir = fs.mkdtempSync(path.join(os.tmpdir(), "wp52-e2e-"));
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.click("text=Download my notebook"),
    ]);
    const savePath = path.join(downloadDir, "exercise_09.ipynb");
    await download.saveAs(savePath);
    const downloaded = fs.readFileSync(savePath, "utf8");
    expect(downloaded).not.toContain("# YOUR CODE HERE\\n# Hint: reuse the pipeline shape");
    expect(downloaded).toContain("kernel_ridge_result = {");
  });
});

async function runCellReturning(page: Page, anchorText: string) {
  const target = await scrollToVisible(page, anchorText);
  const editor = target.locator(".cm-content").first();
  await editor.click();
  await page.waitForTimeout(150);
  await page.keyboard.press("Shift+Enter");
  await page.waitForTimeout(2_000);
  return target;
}
