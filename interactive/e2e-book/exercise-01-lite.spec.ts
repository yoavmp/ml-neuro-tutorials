import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

// End-to-end proof that the migrated Exercise 1 JupyterLite notebook works in
// a real browser against the actual combined jupyter-book + jupyter-lite
// build (WP42 Gate 2). Mirrors exercise-02-lite.spec.ts's structure and its
// load-bearing notes (windowed cell list, toolbar Save over Ctrl+S, noUiSlider
// handle selector) -- see that file for the full rationale.

// WP49: bumped from 180_000 -- waitForKernelIdle's own up-to-
// 600_000ms budget needs headroom beyond the old fixed-wait
// assumption this default was sized for.
test.setTimeout(300_000);

const NOTEBOOK_URL = "/lite/notebooks/index.html?path=exercise_01.ipynb";

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

// WP49: replaced this file's old fixed 140_000ms wait with a poll on
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

test.describe("Exercise 1 — JupyterLite notebook", () => {
  test("opens, runs, and reproduces the established curated-table result", async ({
    page,
  }) => {
    const consoleErrors: string[] = [];
    page.on("pageerror", (err) => consoleErrors.push(err.message));
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });

    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    await scrollWindowed(page, 0.1);
    await expect(page.locator("body")).toContainText("Data table shape: (1114, 13)", {
      timeout: 5_000,
    });

    const errorCells = await page.locator(".jp-mod-error").count();
    expect(errorCells).toBe(0);

    const unexpected = consoleErrors.filter(
      (e) => !/THEBE_JS_URL|invalid theme mode|ERR_UNKNOWN_URL_SCHEME/i.test(e),
    );
    expect(unexpected, unexpected.join("\n")).toEqual([]);
  });

  test("the retention explorer is operable and updates the retained count", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await runAllCells(page);

    const panel = await scrollToVisible(page, "Required variables:", ".jp-OutputArea-output");
    const readout = panel.locator(".jp-OutputArea-output", { hasText: "Retained:" }).first();
    const before = await readout.textContent();
    const handednessCheckbox = panel.locator(".widget-checkbox", { hasText: "Handedness category" }).locator("input");
    await handednessCheckbox.scrollIntoViewIfNeeded();
    await handednessCheckbox.click();
    await page.waitForTimeout(1500);
    const after = await readout.textContent();
    expect(after).not.toEqual(before);
  });

  test("the histogram widget is operable and updates the figure", async ({ page }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await runAllCells(page);

    const panel = await scrollToVisible(page, "Bins:", ".jp-OutputArea-output");
    const select = panel.locator("select").first();
    const image = panel.locator("img").first();
    await select.scrollIntoViewIfNeeded();
    const before = await image.getAttribute("src");
    // ipywidgets' Dropdown renders each <option>'s visible text with
    // &nbsp; in place of spaces, so match by the underlying `value`
    // attribute (a plain space) instead of Playwright's `label` matcher.
    await select.selectOption({ value: "Full-scale IQ" });
    await page.waitForTimeout(1500);
    // The plot title ("Distribution of FIQ") is baked into the rendered PNG
    // raster, not accessible DOM text -- verify the figure actually changed
    // instead (a new image, distinct from the previous variable's plot).
    const after = await image.getAttribute("src");
    expect(after).not.toEqual(before);
  });

  test("a checked question grades correctly", async ({ page }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await runAllCells(page);

    const question = page.locator(".jp-OutputArea-output", {
      hasText: "Which of these columns should be treated as categorical",
    });
    const checkboxes = question.locator("input[type='checkbox']");
    await expect(checkboxes.first()).toBeVisible({ timeout: 5_000 });
    await checkboxes.nth(0).click(); // DX_GROUP
    await checkboxes.nth(2).click(); // SEX
    await checkboxes.nth(4).click(); // HANDEDNESS_CATEGORY
    await question.locator("button", { hasText: "Check answer" }).click();
    await page.waitForTimeout(500);
    await expect(question.locator("text=Correct.")).toBeVisible();
  });

  test("a written-answer cell's edit persists across reload and downloads with the edit present", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await runAllCells(page);

    const target = await scrollToVisible(
      page,
      "Pick one column above that is missing only at a handful of sites",
      ".jp-MarkdownCell",
    );
    await target.dblclick();
    await page.waitForTimeout(300);
    await page.keyboard.press("End");
    const uniqueToken = `wp42-answer-e2e-${Date.now()}`;
    await page.keyboard.type(`\n\n${uniqueToken}`, { delay: 5 });
    await page.keyboard.press("Shift+Enter");
    await page.waitForTimeout(500);
    await expect(target).toContainText("Pick one column above");
    await expect(target).toContainText(uniqueToken);

    await page.locator('[data-command="docmanager:save"]').first().click();
    await page.waitForTimeout(1500);

    await page.reload({ waitUntil: "load" });
    await page.waitForTimeout(5000);

    const downloadDir = fs.mkdtempSync(path.join(os.tmpdir(), "wp42-e2e-answer-"));
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.click("text=Download my notebook"),
    ]);
    const savePath = path.join(downloadDir, "exercise_01.ipynb");
    await download.saveAs(savePath);
    const downloaded = fs.readFileSync(savePath, "utf8");
    expect(downloaded).toContain(uniqueToken);
  });

  test("reset restores the template and Back returns to Contents", async ({ page }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await runAllCells(page);

    await page.click("text=Reset from course template");
    await page.waitForTimeout(800);
    await page.locator(".jp-Dialog-button", { hasText: "Reset" }).first().click();
    await page.waitForTimeout(2000);
    const restored = await (await scrollToVisible(page, "data.head()")).innerText();
    expect(restored).not.toContain("wp42-answer-e2e-");

    await scrollWindowed(page, 0);
    await page.click("text=Back to course contents");
    await page.waitForTimeout(1000);
    expect(page.url()).toContain("contents.html");
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

  test("running the data cell before setup fails with an actionable message, not a bare NameError", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await page.waitForTimeout(3000);

    const target = await scrollToVisible(page, "load_abide_phenotypes()");
    await target.click();
    await page.keyboard.press("Shift+Enter");
    await page.waitForTimeout(4000);

    const output = await target.locator(".jp-OutputArea-output").first().innerText();
    expect(output).toContain("RuntimeError");
    expect(output).toContain("Run this notebook's");
    expect(output.trim().split("\n").pop()).toContain("RuntimeError:");
  });
});
