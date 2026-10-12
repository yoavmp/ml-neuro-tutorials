import { expect, test, type Browser, type Page } from "@playwright/test";

// WP55 item E: focused, bounded coverage for JupyterLite's own intermittent
// "No Kernel" startup race (see book/lite/extensions/course-toolbar/src/
// index.ts's ensureKernelStarted() for the root-cause writeup and fix).
//
// This does NOT re-run Exercise 1's full content suite (exercise-01-lite.
// spec.ts already does that) -- it only exercises the kernel-startup path
// itself: repeated fresh opens (a handful, not a many-hour stochastic
// suite), a "returning profile" (same browser context, reload after an
// edit), and the real GitHub-Pages-style path-prefixed route, each
// confirming a trivial cell actually executes and capturing diagnostics
// if any attempt is ever caught on "No Kernel".
test.setTimeout(90_000);

const ROOT_NOTEBOOK_URL = "/lite/notebooks/index.html?path=exercise_01.ipynb";
const SUBPATH_NOTEBOOK_URL = "/ml-neuro-tutorials/lite/notebooks/index.html?path=exercise_01.ipynb";

interface Diagnostics {
  console: string[];
  requestFailures: string[];
}

function instrument(page: Page): Diagnostics {
  const diag: Diagnostics = { console: [], requestFailures: [] };
  page.on("console", msg => {
    if (msg.type() === "error" || msg.type() === "warning") {
      diag.console.push(`[${msg.type()}] ${msg.text()}`);
    }
  });
  page.on("requestfailed", req => {
    diag.requestFailures.push(`${req.method()} ${req.url()} :: ${req.failure()?.errorText}`);
  });
  return diag;
}

async function waitForKernelIdle(page: Page, timeoutMs = 60_000) {
  await page.waitForFunction(
    () => document.querySelector(".jp-Notebook-ExecutionIndicator")?.getAttribute("data-status") === "idle",
    undefined,
    { timeout: timeoutMs, polling: 500 },
  );
}

// Confirms the kernel actually became usable (never settled on "No
// Kernel") and that a trivial cell genuinely executes -- the real,
// user-visible behavior this WP's fix targets, not just a UI label.
async function confirmKernelStartsAndRunsATrivialCell(page: Page, diag: Diagnostics, label: string) {
  const pyodideAppeared = await page
    .locator("text=Python (Pyodide)")
    .first()
    .waitFor({ state: "visible", timeout: 35_000 })
    .then(() => true)
    .catch(() => false);

  const stuckOnNoKernelOnly =
    !pyodideAppeared && (await page.locator("text=No Kernel").count()) > 0;

  if (!pyodideAppeared) {
    const detail = [
      `[${label}] kernel never showed "Python (Pyodide)" within 35s` +
        (stuckOnNoKernelOnly ? " (stuck on \"No Kernel\")" : " (still starting?)"),
      "---console/warning lines---",
      ...diag.console,
      "---failed requests---",
      ...diag.requestFailures,
    ].join("\n");
    throw new Error(detail);
  }

  const firstCell = page.locator(".jp-CodeCell").first();
  await firstCell.click();
  await page.keyboard.press("Shift+Enter");
  await waitForKernelIdle(page);

  const errorCells = await page.locator(".jp-mod-error").count();
  expect(errorCells, `[${label}] a cell errored on run:\n${diag.console.join("\n")}`).toBe(0);
}

async function freshAttempt(browser: Browser, url: string, label: string) {
  const context = await browser.newContext();
  const page = await context.newPage();
  const diag = instrument(page);
  try {
    await page.goto(url, { waitUntil: "load" });
    await confirmKernelStartsAndRunsATrivialCell(page, diag, label);
  } finally {
    await context.close();
  }
}

test.describe("Exercise 1 kernel startup", () => {
  // Bounded: a handful of fresh-context opens, not an exhaustive or
  // stochastic sweep -- enough to exercise the race repeatedly without
  // turning this into a many-hour suite.
  for (let i = 1; i <= 3; i++) {
    test(`fresh open #${i} starts the Pyodide kernel and runs a cell`, async ({ browser }) => {
      await freshAttempt(browser, ROOT_NOTEBOOK_URL, `fresh-${i}`);
    });
  }

  test("a fresh open under the real GitHub-Pages-style path-prefixed route also starts the kernel", async ({
    browser,
  }) => {
    await freshAttempt(browser, SUBPATH_NOTEBOOK_URL, "subpath");
  });

  test("a returning profile (same context) still starts the kernel after an edit and reload, with the edit retained", async ({
    browser,
  }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    const diag = instrument(page);
    try {
      await page.goto(ROOT_NOTEBOOK_URL, { waitUntil: "load" });
      await confirmKernelStartsAndRunsATrivialCell(page, diag, "returning-first-visit");

      // Edit a markdown cell and save, simulating "a returning profile
      // with an edited notebook" (WP55 item E's own phrasing).
      const target = page.locator(".jp-MarkdownCell", { hasText: "Run the cell below first" }).first();
      await target.dblclick();
      await page.waitForTimeout(200);
      await page.keyboard.press("End");
      const uniqueToken = `wp55-kernel-e2e-${Date.now()}`;
      await page.keyboard.type(`\n\n${uniqueToken}`, { delay: 5 });
      await page.keyboard.press("Shift+Enter");
      await page.waitForTimeout(300);
      await page.locator('[data-command="docmanager:save"]').first().click();
      await page.waitForTimeout(1000);

      // Reload in the SAME context/profile -- any persisted service-worker
      // or IndexedDB state from the first visit carries over, unlike a
      // fresh context.
      await page.reload({ waitUntil: "load" });
      await confirmKernelStartsAndRunsATrivialCell(page, diag, "returning-after-reload");
      await expect(page.locator("body")).toContainText(uniqueToken);
    } finally {
      await context.close();
    }
  });
});
