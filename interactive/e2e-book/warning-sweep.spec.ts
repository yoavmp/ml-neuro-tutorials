import { expect, test, type Page } from "@playwright/test";

// Course-wide warning sweep (WP53): runs every published exercise's
// JupyterLite notebook once, on its untouched student template, and scans
// every cell's rendered output -- scrolled through in full, since
// JupyterLab's windowed notebook virtualizes cells out of the DOM when not
// currently in view -- for any Python warning text that reached the
// student (UserWarning/RuntimeWarning/PerformanceWarning/
// DeprecationWarning, etc.). This is deliberately broader than any single
// exercise's own spec file: it is the live-browser evidence for the WP's
// own requirement not to claim the whole course is warning-free based only
// on static/offline inspection. The untouched template (not a teacher-
// filled copy) is used because it is what every student actually opens
// first, and every native interactive activity checked here (the ones that
// do not depend on an unfilled "YOUR CODE HERE" blank) already renders and
// is operable on the untouched template.
//
// A positive match here does not by itself distinguish a brand-new
// regression from a previously-undiscovered warning -- either way, it is
// something the report must record honestly, with the exact cell and
// message, rather than silently ignored.

test.setTimeout(240_000);

const EXERCISES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 12];

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
  // The untouched template's own guarded cells may leave the kernel
  // reporting "idle" between still-rendering widget cells; a reasonably
  // generous timeout, not a fixed sleep, still drives this off the real
  // signal.
  await waitForKernelIdle(page, 180_000).catch(() => {});
}

// Collects text from every *output area* (.jp-OutputArea-output) at every
// scroll position from top to bottom of the windowed notebook, so every
// cell's output is captured in the DOM at least once. Deliberately scoped
// to rendered OUTPUT, not document.body.innerText as a whole: a cell's own
// source code is visible in its CodeMirror editor too, and this course's
// own generator source routinely explains a fix in a code comment that
// mentions the word "warning" (e.g. "# explicit tick positions before
// set_xticklabels -- avoids a Matplotlib warning") -- real prose, not an
// actual warning reaching the student, and a false positive if swept too.
async function collectAllOutputText(page: Page): Promise<string> {
  const chunks: string[] = [];
  for (let f = 0; f <= 1.001; f += 0.1) {
    await page.evaluate((frac) => {
      const el = document.querySelector(".jp-WindowedPanel-outer");
      if (el) el.scrollTop = el.scrollHeight * frac;
    }, f);
    await page.waitForTimeout(250);
    chunks.push(
      await page.evaluate(() =>
        Array.from(document.querySelectorAll(".jp-OutputArea-output"))
          .map((el) => (el as HTMLElement).innerText)
          .join("\n"),
      ),
    );
  }
  return chunks.join("\n");
}

// Known, pre-existing, non-Python, book-page-level noise this course's own
// specs already allowlist (see e.g. exercise-01-lite.spec.ts and
// exercise-02-lite.spec.ts) -- never a Python warning, and never anything
// this sweep is checking for.
const BENIGN_NON_WARNING_NOISE = /THEBE_JS_URL|invalid theme mode/i;

for (const n of EXERCISES) {
  const id = String(n).padStart(2, "0");
  test(`Exercise ${n}: no Python warning text reaches the untouched template's rendered output`, async ({
    page,
  }) => {
    await page.goto(`/lite/notebooks/index.html?path=exercise_${id}.ipynb`, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    const text = await collectAllOutputText(page);
    const warningLines = text
      .split("\n")
      .filter((line) => /warning/i.test(line) && !BENIGN_NON_WARNING_NOISE.test(line));

    expect(warningLines, `Exercise ${n} rendered warning text:\n${warningLines.join("\n")}`).toEqual([]);
  });
}
