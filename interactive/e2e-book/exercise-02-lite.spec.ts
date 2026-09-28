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
//     much faster. The waits below are sized for a cold run on CI, which
//     has been observed to need up to 140s in practice (not just download
//     time -- Section 8's own KNN refits + matplotlib rendering add to it).

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
    // Bumped from 100s to 140s: CI (unlike this repo's own dev machine)
    // reliably needed more than 100s to reach Section 8's widget cell in
    // two separate observed CI runs, each stalling out with the slider
    // never rendered. 140s is not a guess -- it is the value
    // exercise-01-lite.spec.ts and wp22-cross-chapter-dark-mode.spec.ts's
    // own Exercise 2 dark-mode check already use successfully for this
    // exact notebook's cold start.
    await page.waitForTimeout(140_000);

    await scrollWindowed(page, 0.2);
    await expect(page.locator("body")).toContainText("held-out R^2 = 0.469", {
      timeout: 5_000,
    });

    // no error output anywhere in the executed notebook
    const errorCells = await page.locator(".jp-mod-error").count();
    expect(errorCells).toBe(0);

    // benign, pre-existing book-page console noise is allowed; nothing new.
    // WP41R: "ERR_UNKNOWN_URL_SCHEME" is the browser's one-time failed
    // literal fetch of "attachment:<filename>" (not a real URL scheme) when
    // first rendering Section 3B's reference-image markdown cell, before
    // JupyterLab's own attachment resolver replaces the <img> src with the
    // real data URI -- this is how nbformat cell attachments always render
    // in any Jupyter frontend (verified: the image still displays
    // correctly, see "the reference image returns to rendered mode..."
    // below), not a bug introduced by using them here instead of an inline
    // data: URI.
    const unexpected = consoleErrors.filter(
      (e) => !/THEBE_JS_URL|invalid theme mode|ERR_UNKNOWN_URL_SCHEME/i.test(e),
    );
    expect(unexpected, unexpected.join("\n")).toEqual([]);
  });

  test("Section 8 slider is operable and updates the figure", async ({ page }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await runAllCells(page);
    await page.waitForTimeout(140_000);

    // Sweep for the slider by its own handle rather than a fixed scroll
    // fraction: this notebook's exact cell heights (and so which fraction
    // of the windowed list the Section 8 widget falls at) change whenever
    // earlier content changes, which is expected and not itself a bug.
    const handle = page.locator(".widget-slider .noUi-handle").first();
    for (let f = 0; f <= 1.001; f += 0.05) {
      await scrollWindowed(page, f);
      if ((await handle.count()) > 0 && (await handle.boundingBox())) break;
    }
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
    await page.waitForTimeout(140_000);

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
    await page.waitForTimeout(140_000);

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

  // WP42 Gate 1 item 1: a written-answer cell (a bold question in an
  // otherwise-plain Markdown cell, no "YOUR ANSWER HERE" placeholder) must
  // still be editable, saveable, reloadable, and included in a download --
  // the same contract already proven above for a code cell, checked here
  // for a Markdown one specifically since editing/rendering Markdown is a
  // different code path (double-click to enter source view, not a single
  // click into a CodeMirror editor already in edit mode).
  test("a written-answer cell's edit persists across reload and downloads with the edit present", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await runAllCells(page);
    await page.waitForTimeout(140_000);

    const target = await scrollToVisible(
      page,
      "How does KNN (k=20) compare",
      ".jp-MarkdownCell",
    );
    await target.dblclick();
    await page.waitForTimeout(300);
    await page.keyboard.press("End");
    const uniqueToken = `wp41-answer-e2e-${Date.now()}`;
    await page.keyboard.type(`\n\n${uniqueToken}`, { delay: 5 });
    await page.keyboard.press("Shift+Enter");
    await page.waitForTimeout(500);
    // Rendering back must still show the bold question -- editing/re-
    // rendering the cell must not have destroyed its prompt.
    await expect(target).toContainText("How does KNN (k=20) compare");
    await expect(target).toContainText(uniqueToken);

    await page.locator('[data-command="docmanager:save"]').first().click();
    await page.waitForTimeout(1500);

    await page.reload({ waitUntil: "load" });
    await page.waitForTimeout(5000);

    const downloadDir = fs.mkdtempSync(path.join(os.tmpdir(), "wp41-e2e-answer-"));
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.click("text=Download my notebook"),
    ]);
    const savePath = path.join(downloadDir, "exercise_02.ipynb");
    await download.saveAs(savePath);
    const downloaded = fs.readFileSync(savePath, "utf8");
    expect(downloaded).toContain(uniqueToken);
    expect(downloaded).toContain("How does KNN (k=20) compare");
  });

  test("reset restores the template and Back returns to Contents", async ({ page }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await runAllCells(page);
    await page.waitForTimeout(140_000);

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

  // WP41R blocker 1, reproduced live: a fresh kernel, opened normally (NOT
  // "Run All Cells"), where the data-load cell is run directly without first
  // running the collapsed setup cell above it -- the natural mistake, since
  // that cell's own input is hidden and gives no visual cue it needs to run.
  // Before the fix this surfaced as a bare `NameError:
  // name 'load_abide_age_brain_table' is not defined`; existing coverage
  // only ever exercised "Run All Cells" (which queues the setup cell first
  // by construction) and so never caught it.
  test("running the data cell before setup fails with an actionable message, not a bare NameError", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await page.waitForTimeout(3000);

    const target = await scrollToVisible(page, "load_abide_age_brain_table()");
    await target.click();
    await page.keyboard.press("Shift+Enter");
    await page.waitForTimeout(4000);

    // The RuntimeError is chained from the original NameError (`raise ... from
    // exc`), so the traceback legitimately still shows "NameError" as the
    // chain's root cause -- Python's own "The above exception was the direct
    // cause of the following exception" framing, not a bug. What must be
    // true is that the FINAL, actionable exception is the friendly
    // RuntimeError, not that "NameError" is absent from the output.
    const output = await target.locator(".jp-OutputArea-output").first().innerText();
    expect(output).toContain("RuntimeError");
    expect(output).toContain("Run this notebook's");
    expect(output.trim().split("\n").pop()).toContain("RuntimeError:");
  });

  // WP41R blocker 2: the approved reference image must round-trip through
  // edit mode without ever exposing its base64 payload as visible, editable
  // Markdown source (the pre-fix `data:image/png;base64,...` URL was tens of
  // thousands of characters on one line).
  test("the reference image returns to rendered mode without a page-length encoded string", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await runAllCells(page);
    await page.waitForTimeout(140_000);

    const target = await scrollToVisible(
      page,
      "Approved observed-vs-predicted result",
      ".jp-MarkdownCell",
    );
    await expect(target.locator("img")).toBeVisible({ timeout: 5_000 });

    await target.dblclick();
    await page.waitForTimeout(500);
    const editorText = await page.evaluate(() => {
      const active = document.querySelector(".jp-Cell.jp-mod-active .cm-content");
      return active ? active.textContent ?? "" : "";
    });
    expect(editorText.length).toBeLessThan(200);
    expect(editorText).not.toContain("base64");
    expect(editorText).toContain("attachment:");

    await page.keyboard.press("Shift+Enter");
    await page.waitForTimeout(800);
    await expect(target.locator("img")).toBeVisible({ timeout: 5_000 });
  });
});
