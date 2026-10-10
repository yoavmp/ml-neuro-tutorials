import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

// End-to-end proof that the migrated Exercise 3 JupyterLite notebook works
// in a real browser against the actual combined jupyter-book + jupyter-lite
// build (WP44), modeled directly on exercise-02-lite.spec.ts. Requires
// `jupyter lite build --config book/lite/jupyter_lite_config.json --lite-dir
// book/lite --output-dir book/_build/html/lite` to have already run.
//
// This notebook's model-fit cell depends on three student "YOUR CODE HERE"
// blanks (FEATURES, X/y, the train/test split) rather than fully supplied
// code. It used to raise an actionable RuntimeError when those blanks were
// unfilled, which halted "Run All Cells" partway through (WP44's original
// design). A later fix replaced that raise with the same graceful
// "Not complete yet" guard pattern every other check cell in this notebook
// already uses, so "Run All Cells" on the UNTOUCHED template now runs to
// genuine completion with zero error cells, exactly like every other
// migrated exercise -- every downstream activity that depends on the
// unfilled blanks degrades to its own "Not complete yet"/"Complete Section
// N first" message instead of cascading into a crash. This file tests both:
// the untouched template's graceful, no-cascade behavior, and a
// teacher-only completed path (typed in live, exactly like a student
// filling in the blanks) that reproduces the established accuracy/AUC and
// exercises every native widget and checked question.

test.setTimeout(180_000);

const NOTEBOOK_URL = "/lite/notebooks/index.html?path=exercise_03.ipynb";

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

// Polls JupyterLab's own semantic kernel-status attribute (unknown -> busy
// -> idle) rather than a fixed wait -- environment-independent, and now
// safe to use here too: the untouched template's guarded model-fit cell no
// longer raises (see this file's own header comment), so "Run All Cells"
// genuinely reaches "idle" instead of hanging partway through busy, the
// same pattern every other exercise-0N-lite.spec.ts already uses.
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


// Fills a blank "# YOUR CODE HERE" cell with real solution code, the way a
// student (or, for this test, a teacher building a completed copy) would:
// click into the CodeMirror editor, select all existing text, and type the
// replacement. Runs the cell with Shift+Enter afterward so its output (and
// any variables it defines) are available to later cells.
async function fillBlank(page: Page, anchorText: string, solution: string) {
  const target = await scrollToVisible(page, anchorText);
  const editor = target.locator(".cm-content").first();
  await editor.click();
  await page.waitForTimeout(150);
  const isMac = process.platform === "darwin";
  await page.keyboard.press(`${isMac ? "Meta" : "Control"}+A`);
  await page.keyboard.press("Backspace");
  await page.keyboard.type(solution, { delay: 2 });
  await page.keyboard.press("Shift+Enter");
  await page.waitForTimeout(600);
}

test.describe("Exercise 3 — JupyterLite notebook, untouched template", () => {
  test("Section 1 loads the established data and Section 2's checked question grades correctly", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    await scrollWindowed(page, 0.05);
    await expect(page.locator("body")).toContainText("463 autism (group=1 -> 1), 541 control (group=2 -> 0)", {
      timeout: 5_000,
    });

    const question = await scrollToVisible(
      page,
      "Two participants receive autism probabilities",
      ".jp-OutputArea-output",
    );
    // ipywidgets renders an empty, hidden "description" <label> for every
    // widget even when description="" (confirmed live: a plain "label"
    // locator's first match is this hidden element, not a real option) --
    // the actual clickable per-option labels live specifically inside
    // ".widget-radio-box" (the same scoping the setup cell's own CSS fix
    // already targets for text-wrapping, see SETUP_SOURCE_TEMPLATE).
    // This question shuffles its displayed option order with a fixed
    // per-question seed (course-wide review item 2) -- select by the
    // option's own TEXT, never by position.
    const labels = question.locator(".widget-radio-box label");
    await expect(labels.first()).toBeVisible({ timeout: 5_000 });
    await question.locator(".widget-radio-box label", { hasText: "barely changing the model's actual evidence" }).click();
    await question.locator("button", { hasText: "Check answer" }).click();
    await page.waitForTimeout(500);
    // This question's own feedback_correct text starts "Correct:" (a colon,
    // not the shared helper's default "Correct." period) -- match the
    // actual text rather than assuming the default.
    await expect(question.locator("text=/^Correct:/")).toBeVisible();
  });

  // The model-fit cell's guard used to raise an actionable RuntimeError,
  // which halted "Run All Cells" there by construction -- nothing after it
  // could ever run, so "no cascade" held trivially. Now that the guard
  // degrades gracefully instead (see this file's header comment), this test
  // verifies the stronger claim live: EVERY activity that depends on the
  // unfilled blanks, all the way through the end of the notebook, shows its
  // own helpful "Not complete yet"/"Complete Section N first" message, zero
  // cells end up in JupyterLab's own error state, and the kernel genuinely
  // reaches "idle" (not stuck "busy" behind a silent hang). (Offline,
  // tests/test_exercise_03_reference_execution.py's direct cell-by-cell
  // executor already confirms the untouched template raises nowhere, top
  // to bottom.)
  test("every activity depending on the unfilled blanks degrades gracefully, with zero error cells end to end", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    expect(await page.locator(".jp-mod-error").count()).toBe(0);

    const featuresCheck = await scrollToVisible(page, "define FEATURES above first");
    await expect(featuresCheck.locator(".jp-OutputArea-output")).toContainText("Not complete yet");

    const xyCheck = await scrollToVisible(page, "define X and y above first");
    await expect(xyCheck.locator(".jp-OutputArea-output")).toContainText("Not complete yet");

    const splitCheck = await scrollToVisible(page, "define X_train, X_test, y_train, and y_test above first");
    await expect(splitCheck.locator(".jp-OutputArea-output")).toContainText("Not complete yet");

    // The former guard cell: no RuntimeError, no red traceback -- a plain,
    // friendly printed instruction instead, and the fit/predict code never
    // ran (so the cell has no real output beyond that one line).
    const fitCell = await scrollToVisible(page, "complete the FEATURES, X/y, and train/test split activities above first");
    const fitOutput = fitCell.locator(".jp-OutputArea-output");
    await expect(fitOutput).toContainText("Not complete yet");
    await expect(fitOutput).not.toContainText("RuntimeError");

    // Downstream of the fit cell: Section 4's confusion-matrix and ROC/AUC
    // blanks' own checks, Section 5's threshold widget, and Section 6's
    // imbalance dropdown all degrade too, rather than cascading into a
    // NameError.
    const cmCheck = await scrollToVisible(page, "complete Section 3's activities above first");
    await expect(cmCheck.locator(".jp-OutputArea-output")).toContainText("Not complete yet");

    const aucCheck = await scrollToVisible(page, "define auc above first");
    await expect(aucCheck.locator(".jp-OutputArea-output")).toContainText("Not complete yet");

    await scrollToVisible(page, "y_test and y_proba are not defined yet", ".jp-CodeCell");
    await expect(page.locator("body")).toContainText("Complete Section 3 first: y_test and y_proba are not defined yet");

    const imbalanceGuard = await scrollToVisible(page, "Section 3's X/y activity first", ".jp-CodeCell");
    await expect(imbalanceGuard).toBeVisible();
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

test.describe("Exercise 3 — JupyterLite notebook, teacher-completed path", () => {
  test("filling in every blank reproduces the established result and drives both native widgets", async ({
    page,
  }) => {
    // This test's own budget: one cold start (~140s) plus three typed
    // blanks, two re-runs with their own settle waits, and widget
    // interactions -- comfortably exceeds the file-wide 180s default.
    test.setTimeout(480_000);
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    await fillBlank(page, "# FEATURES = ...", 'FEATURES = [c for c in df.columns if c.startswith("fsCT_")]');
    await fillBlank(
      page,
      "# X = ...",
      'X = df[FEATURES].to_numpy(float)\ny = df["group"].to_numpy()',
    );
    await fillBlank(
      page,
      "# X_train, X_test, y_train, y_test = ...",
      "X_train, X_test, y_train, y_test = train_test_split(\n    X, y, test_size=0.25, random_state=42, stratify=y\n)",
    );

    // Re-run from the (now guarded-but-passing) model-fit cell onward so
    // every later cell sees the newly defined variables.
    await runAllCells(page);
    await page.waitForTimeout(30_000);

    await scrollWindowed(page, 0.35);
    await expect(page.locator("body")).toContainText("n_train = 753   n_test = 251   n_features = 360", {
      timeout: 5_000,
    });

    await fillBlank(
      page,
      "# cm = confusion_matrix(...)",
      "cm = confusion_matrix(y_test, y_pred, labels=[0, 1])\n" +
        "tn, fp, fn, tp = cm[0, 0], cm[0, 1], cm[1, 0], cm[1, 1]\n" +
        "accuracy = accuracy_score(y_test, y_pred)\n" +
        "sensitivity = tp / (tp + fn)\n" +
        "specificity = tn / (tn + fp)\n" +
        "print(f'accuracy = {accuracy:.3f}')",
    );
    await fillBlank(
      page,
      "# fpr, tpr, _ = roc_curve(...)",
      "fpr, tpr, _ = roc_curve(y_test, y_proba)\nauc = roc_auc_score(y_test, y_proba)\nprint('placeholder plot')",
    );

    await runAllCells(page);
    await page.waitForTimeout(30_000);

    // WP48 D.3 replaced the confusion-matrix numeric autocheck cell with a
    // qualitative Markdown reflection (no "Looks good: accuracy=..." print
    // left to assert on) -- the activity's own typed print above is this
    // test's replacement signal that the established accuracy reproduced.
    await scrollWindowed(page, 0.55);
    await expect(page.locator("body")).toContainText("accuracy = 0.546", { timeout: 5_000 });
    await expect(page.locator("body")).toContainText(
      "plausible outcome for this specific, difficult problem",
      { timeout: 5_000 },
    );
    await scrollWindowed(page, 0.65);
    await expect(page.locator("body")).toContainText("Looks good: AUC=0.569", { timeout: 5_000 });

    // Section 5's threshold slider now has real y_test/y_proba to work with.
    const handle = page.locator(".widget-slider .noUi-handle").first();
    for (let f = 0.55; f <= 1.001; f += 0.05) {
      await scrollWindowed(page, f);
      if ((await handle.count()) > 0 && (await handle.boundingBox())) break;
    }
    await expect(handle).toBeVisible({ timeout: 5_000 });
    const beforeThreshold = await scrollToVisible(page, "predicted autism =");
    const before = await beforeThreshold.locator(".jp-OutputArea-output").first().innerText();
    await handle.click();
    for (let i = 0; i < 10; i++) await page.keyboard.press("ArrowRight");
    await page.waitForTimeout(1000);
    const after = await beforeThreshold.locator(".jp-OutputArea-output").first().innerText();
    expect(after).not.toEqual(before);

    // Section 6's imbalance dropdown. Re-find the cell by its OWN printed
    // output text before and after the interaction, rather than reusing one
    // locator handle across the mutation: selecting a new ratio replaces
    // the cell's figure and text output (a new matplotlib figure + a
    // changed "cohort: ..." line), and the windowed cell list can remount
    // the cell's DOM node during that change -- the same lesson
    // scrollToVisible already exists for.
    // The default ratio (90:10 of 400) prints "40 autism"; selecting 95:5
    // must recompute and print "20 autism" -- a specific, unambiguous
    // signal that the widget actually refit at the new ratio, not just that
    // the <select> element's own value changed.
    await expect(page.locator("body")).toContainText("40 autism", { timeout: 5_000 });
    const dropdown = await scrollToVisible(page, "ratio:", ".jp-CodeCell");
    await dropdown.locator("select").selectOption("95:5");
    await expect(page.locator("body")).toContainText("20 autism", { timeout: 10_000 });

    // Download contains the completed work.
    const downloadDir = fs.mkdtempSync(path.join(os.tmpdir(), "wp44-e2e-"));
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.click("text=Download my notebook"),
    ]);
    const savePath = path.join(downloadDir, "exercise_03.ipynb");
    await download.saveAs(savePath);
    const downloaded = fs.readFileSync(savePath, "utf8");
    // Not an exact string match: CodeMirror's auto-closing brackets can
    // alter typed punctuation in ways that still execute correctly (already
    // proven above by the reproduced accuracy/AUC) without matching a
    // hand-typed literal byte-for-byte. What must be true is that the
    // blank's placeholder is gone and real solution code replaced it --
    // "df.columns" appears only in the completed FEATURES answer, nowhere
    // in the untouched template.
    expect(downloaded).not.toContain('"# YOUR CODE HERE\\n# FEATURES = ...\\n"');
    expect(downloaded).toContain("df.columns");
  });
});
