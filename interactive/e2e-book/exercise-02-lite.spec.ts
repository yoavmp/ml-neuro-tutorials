import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

// End-to-end proof that the migrated Exercise 2 JupyterLite notebook works
// in a real browser against the actual combined jupyter-book + jupyter-lite
// build (WP41). Requires `jupyter lite build --config
// book/lite/jupyter_lite_config.json --lite-dir book/lite --output-dir
// book/_build/html/lite` to have already run (see
// WPs/reports/WP41_MAINTAINER_GUIDE.md) -- CI does not yet build this
// automatically (that wiring is out of WP41's scope; see the "Deviations"
// section of WPs/reports/WP41_REPORT.md).
//
// Notes learned building this notebook platform, load-bearing for every
// interaction below:
//   - The notebook's cell list is virtualized ("windowed"): a cell far off
//     screen is not in the DOM at all. scrollWindowed() below must run
//     before locating any specific cell.
//   - This machine (and CI images) report a Mac-like platform to
//     JupyterLab's keybinding layer, which then expects Cmd (Meta), not
//     Ctrl, for "Accel"-bound commands (save, select-all). Use the toolbar
//     Save button and Backspace-based clearing, never Ctrl+S/Ctrl+A.
//   - ipywidgets 8's IntSlider renders via noUiSlider (a div, not a native
//     <input type=range>); its keyboard-operable handle is ".noUi-handle".
//   - Cold start (first visit, empty cache) fetches Pyodide plus the
//     scientific stack from the CDN and can take ~90s; warm reloads are
//     much faster. The waits below are sized for a cold run.

test.setTimeout(180_000);

const NOTEBOOK_URL = "/lite/notebooks/index.html?path=exercise_02.ipynb";

async function scrollWindowed(page: Page, fraction: number) {
  await page.evaluate((f) => {
    const el = document.querySelector(".jp-WindowedPanel-outer");
    if (el) el.scrollTop = el.scrollHeight * f;
  }, fraction);
  await page.waitForTimeout(400);
}

// A windowed cell can textContent-match (Playwright's `hasText`) while
// still off the currently-scrolled viewport, in which case innerText()
// returns "" and boundingBox() is null. The list's total scrollHeight also
// differs between a live "Run All Cells" run (still growing as outputs
// render) and a reloaded, fully-rendered notebook, so no single fraction
// guess is reliable across both. Sweep the whole list in small steps and
// stop once the target cell is actually laid out (has a bounding box).
async function scrollToVisible(page: Page, text: string): Promise<import("@playwright/test").Locator> {
  const locator = page.locator(".jp-CodeCell", { hasText: text }).first();
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

test.describe("Exercise 2 — JupyterLite notebook", () => {
  test("opens, runs, and reproduces the established linear-regression result", async ({
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
    await page.waitForTimeout(100_000); // cold start: kernel + package fetch + full run

    await scrollWindowed(page, 0.2);
    await expect(page.locator("body")).toContainText("held-out R^2 = 0.469", {
      timeout: 5_000,
    });

    // no error output anywhere in the executed notebook
    const errorCells = await page.locator(".jp-mod-error").count();
    expect(errorCells).toBe(0);

    // benign, pre-existing book-page console noise is allowed; nothing new
    const unexpected = consoleErrors.filter(
      (e) => !/THEBE_JS_URL|invalid theme mode/i.test(e),
    );
    expect(unexpected, unexpected.join("\n")).toEqual([]);
  });

  test("Section 8 slider is operable and updates the figure", async ({ page }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await runAllCells(page);
    await page.waitForTimeout(100_000);

    await scrollWindowed(page, 0.85);
    const handle = page.locator(".widget-slider .noUi-handle").first();
    const readout = page.locator(".widget-slider .widget-readout").first();
    await expect(handle).toBeVisible({ timeout: 5_000 });
    const before = await readout.textContent();
    await handle.click();
    for (let i = 0; i < 5; i++) await page.keyboard.press("ArrowRight");
    await page.waitForTimeout(1500);
    const after = await readout.textContent();
    expect(after).not.toEqual(before);
  });

  test("a checked question grades correctly", async ({ page }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await runAllCells(page);
    await page.waitForTimeout(100_000);

    await scrollWindowed(page, 0.12);
    // Every checked question stays mounted once rendered, and more than one
    // uses "correct"/"Correct" somewhere in its own option text (Section 4's
    // "A. correct" among them) -- scope the result to Activity 2A's own
    // widget container by its unique prompt text, not by page position.
    const question = page.locator(".jp-OutputArea-output", {
      hasText: "Which uses of the test target",
    });
    const checkboxes = question.locator("input[type='checkbox']");
    await expect(checkboxes.first()).toBeVisible({ timeout: 5_000 });
    await checkboxes.nth(0).click();
    await checkboxes.nth(2).click();
    await question.locator("button", { hasText: "Check answer" }).click();
    await page.waitForTimeout(500);
    await expect(question.locator("text=Correct.")).toBeVisible();
  });

  test("an edit persists across reload and downloads with the edit present", async ({
    page,
    context,
  }) => {
    await context.grantPermissions?.([]);
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await runAllCells(page);
    await page.waitForTimeout(100_000);

    const target = await scrollToVisible(page, "knn_model = ...");
    const editor = target.locator(".cm-content").first();
    const box = await editor.boundingBox();
    if (!box) throw new Error("editor bounding box not available");
    // Click directly in the CodeMirror editor (not the cell's outer
    // wrapper -- that can land on non-editable padding and stay in command
    // mode) near its bottom-left, which both enters edit mode and places the
    // cursor on the last line reliably, regardless of the starter text's
    // exact length. Arrow-key navigation to "the end" was tried first and
    // is not reliable here: enough ArrowDown presses to safely clear one
    // cell can cross into the next cell instead of stopping at its last
    // line.
    await editor.click({ position: { x: 3, y: Math.max(2, box.height - 3) } });
    await page.waitForTimeout(300);
    await page.keyboard.press("End");
    for (let i = 0; i < 400; i++) await page.keyboard.press("Backspace");
    const uniqueToken = `wp41-e2e-${Date.now()}`;
    await page.keyboard.type(`# ${uniqueToken}\n`, { delay: 5 });
    await page.keyboard.press("Escape");
    await page.waitForTimeout(300);

    await page.locator('[data-command="docmanager:save"]').first().click();
    await page.waitForTimeout(1500);

    await page.reload({ waitUntil: "load" });
    await page.waitForTimeout(5000);
    // Confirm persistence and the download contract together via the
    // downloaded file's actual content, not by scrolling the windowed cell
    // list into view: right after a reload (unlike right after "Run All
    // Cells") the list can lay a cell out with a real, non-null
    // boundingBox() while it is still visually blank for a moment, which
    // makes DOM text-scraping flaky here even though the underlying
    // document -- verified directly via download -- already has the edit.
    const downloadDir = fs.mkdtempSync(path.join(os.tmpdir(), "wp41-e2e-"));
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.click("text=Download my notebook"),
    ]);
    const savePath = path.join(downloadDir, "exercise_02.ipynb");
    await download.saveAs(savePath);
    const downloaded = fs.readFileSync(savePath, "utf8");
    expect(downloaded).toContain(uniqueToken);
  });

  test("reset restores the template and Back returns to Contents", async ({ page }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await runAllCells(page);
    await page.waitForTimeout(100_000);

    await page.click("text=Reset from course template");
    await page.waitForTimeout(800);
    await page.locator(".jp-Dialog-button", { hasText: "Reset" }).first().click();
    await page.waitForTimeout(2000);
    const restored = await (await scrollToVisible(page, "knn_model = ...")).innerText();
    expect(restored).not.toContain("wp41-e2e-");

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
});
