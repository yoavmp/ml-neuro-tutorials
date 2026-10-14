import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

// End-to-end proof that the WP57 Exercise 12 ("Common Mistakes and
// Pitfalls") JupyterLite notebook works in a real browser against the
// actual combined jupyter-book + jupyter-lite build, modeled directly on
// exercise-09-lite.spec.ts's own patterns. Every checked question's
// correct answer is reproducibly shuffled per question (never first), so
// every "click the correct option" step below selects by the option's own
// TEXT, never by position -- this is itself part of what this file is
// verifying, not an implementation detail to work around.
//
// Local-only (WP57): this notebook and its chapter page are wired into
// book/_toc.yml/_config.yml on the feature branch only (see
// WPs/reports/WP57_REPORT.md) -- this spec therefore requires a local
// `jupyter-book build book --all` + `jupyter lite build` to have been run
// first, exactly like exercise-09-lite.spec.ts already did while Exercise
// 9 was local-only.

test.setTimeout(240_000);

const NOTEBOOK_URL = "/lite/notebooks/index.html?path=exercise_12.ipynb";

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

async function runCellReturning(page: Page, anchorText: string) {
  const target = await scrollToVisible(page, anchorText);
  const editor = target.locator(".cm-content").first();
  await editor.click();
  await page.waitForTimeout(150);
  await page.keyboard.press("Shift+Enter");
  await page.waitForTimeout(2_000);
  return target;
}

// Click the single-choice radio option whose own text is `correctText` --
// never by position, since every question's displayed order is
// reproducibly shuffled per question.
async function answerSingleChoice(page: Page, promptAnchor: string, optionText: string) {
  const q = await scrollToVisible(page, promptAnchor, ".jp-OutputArea-output");
  const label = q.locator(".widget-radio-box label", { hasText: optionText });
  await expect(label).toBeVisible({ timeout: 5_000 });
  await label.click();
  await q.locator("button", { hasText: "Check" }).click();
  await page.waitForTimeout(400);
  return q;
}

const Q1_PROMPT = "What information actually crossed the train/validation boundary?";
const Q1_CORRECT = "The mean and standard deviation used to rescale every predictor";
const Q2_PROMPT = "What would you need, that you would not actually have, to run that";
const Q2_CORRECT = "The new participant's own age -- the exact value the model is supposed to predict";
const Q3_PROMPT = "Why is training MSE a poor way to choose among model settings";
const Q3_CORRECT = "Training MSE can always be driven toward zero by making the model more flexible";
const Q4_PROMPT = "what does this comparison actually show?";
const Q4_CORRECT = "A depth chosen for its training performance can genuinely generalize worse";
const Q5_PROMPT = "Based on the confusion matrix above, which of the following statements are true?";
const Q5_CORRECT = [
  "Sensitivity (recall for the positive class) is 0.0",
  "Specificity is 1.0 -- every true negative was correctly identified as negative.",
  "Precision is undefined here, because the classifier never predicted the positive class",
  "A classifier that always predicts the majority class can still report high plain accuracy",
];
const Q5_WRONG = "Because accuracy is 95%, at least one of the 5 positive cases must have been caught.";
const Q6_PROMPT = "What let it do that?";
const Q6_CORRECT = "most validation rows had another row from the SAME participant sitting in the training set";
const Q7_PROMPT = "At which point did the test set stop being an untouched, one-time evaluation";
const Q7_CORRECT = "As soon as its score was computed for more than one candidate setting";

test.describe("Exercise 12 — JupyterLite notebook, untouched template", () => {
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
      "define scaler_honest above first",
      "define honest_pca_r2 above first",
      "define tree_val_results and depth_by_val_mse above first",
      "define group_overlap and group_val_r2 above first",
    ]) {
      const cell = await scrollToVisible(page, anchor);
      await expect(cell.locator(".jp-OutputArea-output").last()).toContainText("Not complete yet");
    }

    // Both native widgets render and produce a live text summary even
    // though every blank above/around them was left untouched.
    await expect(page.locator("body")).toContainText("pipeline=contaminated");
    await expect(page.locator("body")).toContainText("rule=train");

    // Case 4 and Case 6's supplied (non-blank) demos always work.
    await expect(page.locator("body")).toContainText("Balanced accuracy: 0.500");
    await expect(page.locator("body")).toContainText("Best alpha found: 10");
  });

  test("stays usable at a 390px viewport, and every widget control label stays fully readable", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await page.waitForTimeout(4000);

    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(2);

    await runAllCells(page);
    for (const anchor of ["_widget2_toggle = widgets.Dropdown", "_widget3_toggle = widgets.Dropdown"]) {
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

test.describe("Exercise 12 — JupyterLite notebook, teacher-completed path", () => {
  test("filling in all four blanks reproduces the established results, both widgets respond live, every checked question grades correctly after shuffling, and download contains the edits", async ({
    page,
  }) => {
    test.setTimeout(600_000);
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    // Case 1: honest StandardScaler.
    await fillBlank(
      page,
      "scaler_honest = None",
      "scaler_honest = None\n" +
        "from sklearn.pipeline import Pipeline\n" +
        "scaler_honest = StandardScaler().fit(X_train)\n" +
        "honest_pipeline = Pipeline([('scale', StandardScaler()), ('model', LinearRegression())]).fit(X_train, y_train)\n" +
        "print(scaler_honest.mean_[0])",
    );
    await page.waitForTimeout(3_000);
    await runCell(page, "EXPECTED_MEAN_TRAIN = ");
    let check = await scrollToVisible(page, "Looks good: scaler_honest's learned mean");
    await expect(check.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    // Case 2: honest predictor-only PCA.
    await fillBlank(
      page,
      "honest_pca_r2 = None",
      "honest_pca_r2 = None\n" +
        "predictor_only_matrix = np.column_stack([x1, x2])\n" +
        "pca_honest = PCA(n_components=1, random_state=0).fit(predictor_only_matrix[case2_train_idx])\n" +
        "honest_scores_train = pca_honest.transform(predictor_only_matrix[case2_train_idx]).ravel()\n" +
        "honest_scores_val = pca_honest.transform(predictor_only_matrix[case2_val_idx]).ravel()\n" +
        "honest_model = LinearRegression().fit(honest_scores_train.reshape(-1, 1), case2_y[case2_train_idx])\n" +
        "honest_pred_val = honest_model.predict(honest_scores_val.reshape(-1, 1))\n" +
        "honest_pca_r2 = r2_score(case2_y[case2_val_idx], honest_pred_val)\n" +
        "print(honest_pca_r2)",
    );
    await page.waitForTimeout(3_000);
    await runCell(page, "EXPECTED_HONEST_R2 = ");
    check = await scrollToVisible(page, "Looks good: your honest R2 is close");
    await expect(check.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    // Re-run widget 1 now that both paths exist and confirm the toggle
    // visibly changes the live text summary.
    const WIDGET1_ANCHOR = "_widget2_toggle = widgets.Dropdown";
    await runCellReturning(page, WIDGET1_ANCHOR);
    await page.waitForTimeout(1_000);
    await expect(page.locator("body")).toContainText("pipeline=contaminated", { timeout: 5_000 });
    let widget1 = await scrollToVisible(page, WIDGET1_ANCHOR);
    await widget1.locator("select").first().selectOption({ index: 1 }, { timeout: 15_000 }); // honest
    await page.waitForTimeout(1_000);
    await expect(page.locator("body")).toContainText("pipeline=honest", { timeout: 5_000 });
    widget1 = await scrollToVisible(page, WIDGET1_ANCHOR);
    const widget1Img = widget1.locator("img").last();
    await expect(widget1Img).toBeVisible({ timeout: 5_000 });

    // Case 3: honest validation-MSE tree selection.
    await fillBlank(
      page,
      "tree_val_results = []",
      "tree_val_results = []\n" +
        "for depth in TREE_DEPTH_GRID:\n" +
        "    model = tree_fits[depth]['model']\n" +
        "    val_mse = mean_squared_error(y_val, model.predict(X_val))\n" +
        "    tree_val_results.append({'depth': depth, 'train_mse': tree_fits[depth]['train_mse'], 'val_mse': val_mse})\n" +
        "depth_by_val_mse = min(tree_val_results, key=lambda r: r['val_mse'])['depth']\n" +
        "print(depth_by_val_mse)",
    );
    await page.waitForTimeout(3_000);
    await runCell(page, "EXPECTED_VAL_MSE = ");
    check = await scrollToVisible(page, "Looks good: your validation MSE values match");
    await expect(check.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    // The consequence cell does not re-run just because the blank above it
    // changed (no notebook cascades) -- it already ran once during the
    // initial Run All Cells, while tree_val_results/depth_by_val_mse were
    // still empty, and printed "Not complete yet" then. Re-run it now that
    // the blank is complete, then check its own (now-populated) output.
    await runCell(page, "test_mse_by_train_choice = mean_squared_error");
    const consequence = await scrollToVisible(page, "chosen using a score that rewards memorization", ".jp-OutputArea-output");
    await expect(consequence).toContainText("chosen using a held-out score");

    // Re-run widget 2 and confirm the toggle visibly changes the chosen
    // depth reported in the live text summary.
    const WIDGET2_ANCHOR = "_widget3_toggle = widgets.Dropdown";
    await runCellReturning(page, WIDGET2_ANCHOR);
    await page.waitForTimeout(1_000);
    await expect(page.locator("body")).toContainText("rule=train  chosen_depth=None", { timeout: 5_000 });
    let widget2 = await scrollToVisible(page, WIDGET2_ANCHOR);
    await widget2.locator("select").first().selectOption({ index: 1 }, { timeout: 15_000 }); // validation
    await page.waitForTimeout(1_000);
    await expect(page.locator("body")).toContainText("rule=val  chosen_depth=5", { timeout: 5_000 });
    widget2 = await scrollToVisible(page, WIDGET2_ANCHOR);
    const widget2Img = widget2.locator("img").last();
    await expect(widget2Img).toBeVisible({ timeout: 5_000 });

    // Case 5: honest GroupShuffleSplit.
    await fillBlank(
      page,
      "group_overlap = None",
      "group_overlap = None\n" +
        "group_val_r2 = None\n" +
        "gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)\n" +
        "group_train_idx, group_val_idx = next(gss.split(case5_X, case5_y, groups=case5_participant_id))\n" +
        "group_overlap = len(set(case5_participant_id[group_train_idx]) & set(case5_participant_id[group_val_idx]))\n" +
        "group_model = KNeighborsRegressor(n_neighbors=1).fit(case5_X[group_train_idx], case5_y[group_train_idx])\n" +
        "group_pred = group_model.predict(case5_X[group_val_idx])\n" +
        "group_val_r2 = r2_score(case5_y[group_val_idx], group_pred)\n" +
        "print(group_overlap, group_val_r2)",
    );
    await page.waitForTimeout(3_000);
    await runCell(page, "EXPECTED_GROUP_R2 = ");
    check = await scrollToVisible(page, "Looks good: participant overlap is 0");
    await expect(check.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    // Every single-choice checked question: correct feedback, selected by
    // option TEXT (never position -- every question is shuffled).
    for (const [prompt, correct] of [
      [Q1_PROMPT, Q1_CORRECT],
      [Q2_PROMPT, Q2_CORRECT],
      [Q3_PROMPT, Q3_CORRECT],
      [Q4_PROMPT, Q4_CORRECT],
      [Q6_PROMPT, Q6_CORRECT],
      [Q7_PROMPT, Q7_CORRECT],
    ] as const) {
      const q = await answerSingleChoice(page, prompt, correct);
      await expect(q.locator("text=/^Correct/")).toBeVisible();
      expect(await q.innerText()).not.toContain("correct_index");
    }

    // The multiselect question: select exactly the four true statements.
    const mq = await scrollToVisible(page, Q5_PROMPT, ".jp-OutputArea-output");
    for (const statementText of Q5_CORRECT) {
      await mq.locator(".widget-checkbox label", { hasText: statementText }).click();
    }
    await mq.locator("button", { hasText: "Check answers" }).click();
    await page.waitForTimeout(400);
    await expect(mq.locator("text=/^Correct/")).toBeVisible();
    expect(await mq.innerText()).not.toContain("correct_indices");

    // One question, deliberately answered wrong: incorrect feedback, no
    // "Correct" text, no visible answer key.
    const wrongQ = await answerSingleChoice(page, Q1_PROMPT, "Nothing meaningful crossed the boundary");
    await expect(wrongQ.locator("text=/^Not quite/")).toBeVisible();

    // One multiselect question, deliberately partially wrong: sensible
    // partial feedback, still no visible answer key.
    const partialQ = await scrollToVisible(page, Q5_PROMPT, ".jp-OutputArea-output");
    await partialQ.locator(".widget-checkbox label", { hasText: Q5_WRONG }).click();
    await partialQ.locator("button", { hasText: "Check answers" }).click();
    await page.waitForTimeout(400);
    await expect(partialQ.locator("text=/true statements selected/")).toBeVisible();
    expect(await partialQ.innerText()).not.toContain("correct_indices");

    // Edit the written-answer cell and confirm the edit renders back and
    // is saved with the rest of the notebook.
    const WRITTEN_ANSWER_ANCHOR = "Looking back across all six cases";
    const MY_ANSWER = "My answer: I will refit preprocessing inside a Pipeline from now on.";
    const answerCell = await scrollToVisible(page, WRITTEN_ANSWER_ANCHOR, ".jp-MarkdownCell");
    await answerCell.dblclick();
    await page.waitForTimeout(300);
    const answerEditor = answerCell.locator(".cm-content").first();
    await answerEditor.click();
    const isMac = process.platform === "darwin";
    await page.keyboard.press(`${isMac ? "Meta" : "Control"}+End`);
    await page.keyboard.insertText(`\n\n${MY_ANSWER}`);
    await page.keyboard.press("Shift+Enter");
    await page.waitForTimeout(600);
    const renderedAnswer = await scrollToVisible(page, WRITTEN_ANSWER_ANCHOR, ".jp-MarkdownCell");
    await expect(renderedAnswer).toContainText(MY_ANSWER);

    // Download contains the completed work, including the written answer.
    const downloadDir = fs.mkdtempSync(path.join(os.tmpdir(), "wp57-e2e-"));
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.click("text=Download my notebook"),
    ]);
    const savePath = path.join(downloadDir, "exercise_12.ipynb");
    await download.saveAs(savePath);
    const downloaded = fs.readFileSync(savePath, "utf8");
    expect(downloaded).not.toContain("# YOUR CODE HERE\\n# Hint: fit a fresh StandardScaler");
    expect(downloaded).toContain("group_val_r2 = r2_score(case5_y[group_val_idx], group_pred)");
    expect(downloaded).toContain(MY_ANSWER);
  });
});
