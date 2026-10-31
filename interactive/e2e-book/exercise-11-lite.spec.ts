import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

// End-to-end proof that Exercise 11 (Embeddings and RSA) works in a real
// browser against the actual combined jupyter-book + jupyter-lite build,
// modeled directly on exercise-09-lite.spec.ts's own patterns. WP61 is
// local-only: this route exists in the local build because the generator
// writes book/lite/files/exercise_11.ipynb directly, with NO
// book/config/exercise_manifest.json or book/_toc.yml change -- this spec
// therefore navigates straight to the lite URL rather than clicking a
// launch button from a chapter page (there is none yet).
//
// Every checked question's displayed option order is reproducibly
// shuffled per question (never "correct option first") -- every "click
// the correct option" step below selects by the option's own TEXT, never
// by position.

test.setTimeout(240_000);

const NOTEBOOK_URL = "/lite/notebooks/index.html?path=exercise_11.ipynb";

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

async function scrollToVisibleFine(
  page: Page,
  text: string,
  cellSelector = ".jp-CodeCell",
): Promise<import("@playwright/test").Locator> {
  const locator = page.locator(cellSelector, { hasText: text }).first();
  // scrollHeight is re-measured every iteration (not captured once up
  // front): a cell late in this notebook (a two-panel figure plus a
  // widget, near the very end) can still be growing the windowed panel's
  // total scrollHeight as its own image finishes rendering, so a single
  // up-front measurement can under-count the true max and end the sweep
  // short of where the target cell actually lands.
  for (let st = 0; ; st += 300) {
    const scrollHeight = await page.evaluate(
      () => document.querySelector(".jp-WindowedPanel-outer")?.scrollHeight ?? 0,
    );
    if (st > scrollHeight) break;
    await page.evaluate((v) => {
      const el = document.querySelector(".jp-WindowedPanel-outer");
      if (el) el.scrollTop = v;
    }, st);
    await page.waitForTimeout(300);
    if ((await locator.count()) > 0 && (await locator.boundingBox())) {
      return locator;
    }
  }
  throw new Error(`cell containing "${text}" never became visible while fine-scrolling`);
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
// never by position, since every question's displayed order is shuffled.
async function answerSingleChoice(page: Page, promptAnchor: string, optionText: string) {
  const q = await scrollToVisible(page, promptAnchor, ".jp-OutputArea-output");
  const label = q.locator(".widget-radio-box label", { hasText: optionText });
  await expect(label).toBeVisible({ timeout: 5_000 });
  await label.click();
  await q.locator("button", { hasText: "Check" }).click();
  await page.waitForTimeout(400);
  return q;
}

const ROW_VOXEL_PROMPT = "What does one row of the loaded table represent";
const ROW_VOXEL_CORRECT = "One row is a single category's averaged BOLD response pattern from one scanning run";
const RDM_CELL_PROMPT = "actually represent?";
const RDM_CELL_CORRECT = "How dissimilar those two categories' averaged response patterns are";
const CONDITION_ORDER_PROMPT = "what must be true about their category order?";
const CONDITION_ORDER_CORRECT = "Both RDMs must list categories in the exact same order";
const MDS_PROMPT = "What does the distance between two points on that plot represent?";
const MDS_CORRECT = "An approximation of the RDM's real dissimilarity between those two categories";
const SPLIT_HALF_PROMPT = "instead of only reporting the whole-dataset RDM?";
const SPLIT_HALF_CORRECT = "To check whether a similar representational structure appears independently";
const MULTISELECT_PROMPT = "Which statements about what that does and does not establish are true?";
const MULTISELECT_CORRECT = [
  "It is consistent with face-related information being present somewhere in this region of interest",
  "It is a descriptive correlation between two matrices, not a significance-tested or causal claim.",
  "A similar positive correlation could in principle arise from a different underlying representational code",
];
const MULTISELECT_WRONG = "It proves that specific individual voxels are dedicated exclusively to processing faces.";

const RDM_SOLUTION =
  "import numpy as np\n" +
  "n = len(CATEGORIES)\n" +
  "neural_rdm = np.zeros((n, n))\n" +
  "for i in range(n):\n" +
  "    for j in range(n):\n" +
  "        r = np.corrcoef(CATEGORY_PATTERNS[i], CATEGORY_PATTERNS[j])[0, 1]\n" +
  "        neural_rdm[i, j] = 1 - r\n" +
  "print(neural_rdm.shape)";

const SPLIT_HALF_SOLUTION =
  "n = len(CATEGORIES)\n" +
  "odd_rdm = np.zeros((n, n))\n" +
  "even_rdm = np.zeros((n, n))\n" +
  "for i in range(n):\n" +
  "    for j in range(n):\n" +
  "        odd_rdm[i, j] = 1 - np.corrcoef(ODD_CATEGORY_PATTERNS[i], ODD_CATEGORY_PATTERNS[j])[0, 1]\n" +
  "        even_rdm[i, j] = 1 - np.corrcoef(EVEN_CATEGORY_PATTERNS[i], EVEN_CATEGORY_PATTERNS[j])[0, 1]\n" +
  "split_half_r = np.corrcoef(upper_triangle(odd_rdm), upper_triangle(even_rdm))[0, 1]\n" +
  "print(split_half_r)";

const ANIMACY_SOLUTION =
  'ANIMATE = {"face", "cat"}\n' +
  'nonscrambled_categories = [c for c in CATEGORIES if c != "scrambledpix"]\n' +
  "positions = [CATEGORIES.index(c) for c in nonscrambled_categories]\n" +
  "neural_rdm_nonscrambled = neural_rdm[np.ix_(positions, positions)]\n" +
  "animacy_hypothesis_rdm = np.array([\n" +
  "    [0 if (ci in ANIMATE) == (cj in ANIMATE) else 1 for cj in nonscrambled_categories]\n" +
  "    for ci in nonscrambled_categories\n" +
  "])\n" +
  "animacy_match_r = np.corrcoef(\n" +
  "    upper_triangle(neural_rdm_nonscrambled), upper_triangle(animacy_hypothesis_rdm)\n" +
  ")[0, 1]\n" +
  "print(animacy_match_r)";

test.describe("Exercise 11 — JupyterLite notebook, untouched template", () => {
  test("Run All Cells: no error cells, data loads, both widgets render, and every blank's check cell shows guidance", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    expect(await page.locator(".jp-mod-error").count()).toBe(0);

    await scrollWindowed(page, 0.03);
    await expect(page.locator("body")).toContainText("464 ventral-temporal voxels", { timeout: 5_000 });

    for (const anchor of [
      "define neural_rdm above first",
      "define odd_rdm, even_rdm, and split_half_r above first",
      "define nonscrambled_categories, animacy_hypothesis_rdm, and animacy_match_r above first",
    ]) {
      const cell = await scrollToVisible(page, anchor);
      await expect(cell.locator(".jp-OutputArea-output").last()).toContainText("Not complete yet");
    }

    // Both native widgets render even though both corresponding blanks
    // were left untouched (the grouping widget's own match_r is NaN before
    // neural_rdm is filled in -- it still renders and prints a Group A/B
    // line, which is what is asserted here).
    await expect(page.locator("body")).toContainText("Group A = ['cat', 'face']");
    const distanceWidgetUntouched = await scrollToVisible(page, "_distance_dd = widgets.Dropdown");
    await expect(distanceWidgetUntouched.locator("img").last()).toBeVisible({ timeout: 5_000 });

    // The given face-hypothesis example depends on neural_rdm (Section 2's
    // own blank) and gracefully defers, rather than silently showing a NaN
    // correlation, when that blank is still untouched.
    const faceExampleCell = await scrollToVisible(page, "face_hypothesis_rdm = np.array(");
    await expect(faceExampleCell.locator(".jp-OutputArea-output").last()).toContainText(
      "Not complete yet: finish Section 2's neural_rdm task first.",
    );
  });

  test("stays usable at a 390px viewport, and both widgets' control labels stay fully readable", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await page.waitForTimeout(4000);

    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(2);

    await runAllCells(page);
    for (const anchor of ["_grouping_select = widgets.SelectMultiple", "_distance_dd = widgets.Dropdown"]) {
      const cell = await scrollToVisibleFine(page, anchor);
      const labels = cell.locator(".widget-controls-row .widget-label");
      const count = await labels.count();
      for (let i = 0; i < count; i++) {
        const label = labels.nth(i);
        const notClipped = await label.evaluate((el) => el.scrollWidth <= el.clientWidth + 2);
        expect(notClipped).toBe(true);
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

test.describe("Exercise 11 — JupyterLite notebook, teacher-completed path", () => {
  test("filling in all three blanks reproduces the established results, both widgets respond live, every checked question grades correctly after shuffling, and download contains the edits", async ({
    page,
  }) => {
    test.setTimeout(600_000);
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    await fillBlank(page, "neural_rdm = np.zeros((n, n))", RDM_SOLUTION);
    await runCell(page, "neural_rdm.shape != (len(CATEGORIES)");
    let check = await scrollToVisible(page, "Looks good: neural_rdm is square");
    await expect(check.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    // Re-run the MDS cell (Section 3) and the given face-hypothesis example
    // (Section 5) now that neural_rdm exists -- both deferred gracefully
    // during the initial Run All Cells (before this blank was filled) and
    // must now recover the documented real result, not stay stuck on their
    // "not complete yet" message.
    await runCell(page, "mds = MDS(n_components=2");
    await page.waitForTimeout(1_000);
    await runCell(page, "face_hypothesis_rdm = np.array(");
    const faceExampleRerun = await scrollToVisible(page, "face_hypothesis_rdm = np.array(");
    await expect(faceExampleRerun.locator(".jp-OutputArea-output").last()).toContainText("face_match_r = 0.247");

    await fillBlank(page, "odd_rdm = np.zeros((n, n))", SPLIT_HALF_SOLUTION);
    await runCell(page, 'for name, m in (("odd_rdm", odd_rdm)');
    check = await scrollToVisible(page, "Looks good: split_half_r");
    await expect(check.locator(".jp-OutputArea-output").last()).toContainText("Looks good: split_half_r = 0.485");

    await fillBlank(page, 'ANIMATE = {"face", "cat"}', ANIMACY_SOLUTION);
    await runCell(page, 'if "scrambledpix" in nonscrambled_categories:');
    check = await scrollToVisible(page, "Looks good: animacy_match_r");
    await expect(check.locator(".jp-OutputArea-output").last()).toContainText(
      "Looks good: animacy_match_r = 0.446 over 7 categories.",
    );

    // Re-run the grouping widget now that neural_rdm is complete (its own
    // cell reads neural_rdm from the global namespace when it first runs).
    const GROUPING_ANCHOR = "_grouping_select = widgets.SelectMultiple";
    await runCellReturning(page, GROUPING_ANCHOR);
    await page.waitForTimeout(1_000);
    await expect(page.locator("body")).toContainText("Group A = ['cat', 'face']   Group B =", { timeout: 5_000 });

    let groupingWidget = await scrollToVisible(page, GROUPING_ANCHOR);
    await groupingWidget.locator("select").first().selectOption(["house"]);
    await page.waitForTimeout(1_000);
    await expect(page.locator("body")).toContainText("Group A = ['house']", { timeout: 5_000 });

    // The distance-metric activity: toggling the dropdown redraws
    // instantly from precomputed variants (no refit visible to the user).
    const DISTANCE_ANCHOR = "_distance_dd = widgets.Dropdown";
    let distanceWidget = await scrollToVisible(page, DISTANCE_ANCHOR);
    await expect(distanceWidget.locator("img").last()).toBeVisible({ timeout: 5_000 });
    await distanceWidget.locator("select").selectOption({ label: "Euclidean distance" });
    await page.waitForTimeout(1_000);
    distanceWidget = await scrollToVisible(page, DISTANCE_ANCHOR);
    await expect(distanceWidget.locator("img").last()).toBeVisible({ timeout: 5_000 });

    // Every single-choice checked question: correct feedback, selected by
    // option TEXT (never position -- every question's order is shuffled).
    for (const [prompt, correct] of [
      [ROW_VOXEL_PROMPT, ROW_VOXEL_CORRECT],
      [RDM_CELL_PROMPT, RDM_CELL_CORRECT],
      [CONDITION_ORDER_PROMPT, CONDITION_ORDER_CORRECT],
      [MDS_PROMPT, MDS_CORRECT],
      [SPLIT_HALF_PROMPT, SPLIT_HALF_CORRECT],
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
    // visible answer key.
    const wrongQ = await answerSingleChoice(page, CONDITION_ORDER_PROMPT, "Nothing in particular");
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
    const downloadDir = fs.mkdtempSync(path.join(os.tmpdir(), "wp61-e2e-"));
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.click("text=Download my notebook"),
    ]);
    const savePath = path.join(downloadDir, "exercise_11.ipynb");
    await download.saveAs(savePath);
    const downloaded = fs.readFileSync(savePath, "utf8");
    expect(downloaded).not.toContain("# YOUR CODE HERE\\n# Hint: loop over every pair");
    expect(downloaded).toContain("animacy_match_r = np.corrcoef(");
  });
});
