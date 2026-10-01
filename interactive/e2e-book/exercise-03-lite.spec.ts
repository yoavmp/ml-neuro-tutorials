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
// Unlike Exercise 2, this notebook's model-fit cell depends on three student
// "YOUR CODE HERE" blanks (FEATURES, X/y, the train/test split) rather than
// fully supplied code -- so "Run All Cells" on the UNTOUCHED template
// deliberately stops at one guarded, actionable RuntimeError (WP44's own
// no-cascade requirement), not a fully reproduced result. This file tests
// both: the untouched template's graceful, single-point failure, and a
// teacher-only completed path (typed in live, exactly like a student filling
// in the blanks) that reproduces the established accuracy/AUC and exercises
// every native widget and checked question.

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

async function runAllCells(page: Page) {
  await page.click("text=Run");
  await page.waitForTimeout(200);
  await page.locator(".lm-Menu-itemLabel", { hasText: "Run All Cells" }).first().click();
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
    // Cold start budget matches exercise-02-lite.spec.ts for the same
    // Pyodide + scientific-stack cold fetch.
    await page.waitForTimeout(140_000);

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
    const labels = question.locator(".widget-radio-box label");
    await expect(labels.first()).toBeVisible({ timeout: 5_000 });
    await labels.nth(1).click();
    await question.locator("button", { hasText: "Check answer" }).click();
    await page.waitForTimeout(500);
    // This question's own feedback_correct text starts "Correct:" (a colon,
    // not the shared helper's default "Correct." period) -- match the
    // actual text rather than assuming the default.
    await expect(question.locator("text=/^Correct:/")).toBeVisible();
  });

  // WP44: JupyterLab's "Run All Cells" halts at the first uncaught error
  // (confirmed live) -- it does not keep queuing later cells past a raised
  // exception the way a plain top-to-bottom script would. This means the
  // "no cascade" requirement is satisfied by construction for whatever runs
  // AFTER the guard (nothing does, so nothing can cascade); what this test
  // verifies live is the part that is not automatic: every activity BEFORE
  // the guard (which the run queue does reach) degrades to its own helpful
  // "Not complete yet" message rather than a raw NameError, and the guard
  // cell itself raises the intended, actionable RuntimeError, not a bare
  // traceback. (Offline, tests/test_exercise_03_reference_execution.py and
  // the direct cell-by-cell executor already confirm the untouched
  // template raises in exactly one place, top to bottom -- see WP44's
  // report.)
  test("activities before the guarded model-fit cell degrade gracefully, and the guard itself is actionable", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);
    await page.waitForTimeout(140_000);

    const featuresCheck = await scrollToVisible(page, "define FEATURES above first");
    await expect(featuresCheck.locator(".jp-OutputArea-output")).toContainText("Not complete yet");

    const xyCheck = await scrollToVisible(page, "define X and y above first");
    await expect(xyCheck.locator(".jp-OutputArea-output")).toContainText("Not complete yet");

    const splitCheck = await scrollToVisible(page, "define X_train, X_test, y_train, and y_test above first");
    await expect(splitCheck.locator(".jp-OutputArea-output")).toContainText("Not complete yet");

    const guarded = await scrollToVisible(page, "X_train/X_test/y_train/y_test are not defined yet");
    const guardedOutput = guarded.locator(".jp-OutputArea-output");
    await expect(guardedOutput).toContainText("RuntimeError");
    await expect(guardedOutput).toContainText("Complete the FEATURES, X/y, and train/test split activities");
    // The traceback itself (an nbformat "error" output, confirmed by the
    // RuntimeError text above) is the load-bearing proof; JupyterLab does
    // not add a "jp-mod-error" class to the outer .jp-Cell element the way
    // an earlier version of this test assumed (confirmed live).
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
    await page.waitForTimeout(140_000);

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
