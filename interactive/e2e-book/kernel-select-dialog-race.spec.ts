import { expect, test, type Page } from "@playwright/test";

// WP55R: kernel-startup.spec.ts (WP55) already confirms the kernel reaches
// "Python (Pyodide)" and a cell runs -- it does not, by itself, prove that
// no *blocking modal* ever sat in front of the notebook on the way there.
// The course author reported exactly that: a native "Select Kernel" dialog
// that could not be used or closed, with Python sometimes starting behind
// it regardless. See book/lite/extensions/course-toolbar/src/index.ts's
// interceptAutomaticKernelSelectDialog() for the full root-cause and fix
// writeup, and WPs/reports/WP55R_REPORT.md for the live investigation that
// found it.
//
// Reproducing the dialog's own real trigger (Context._populate()'s
// unawaited sessionContext.initialize() call) turned out to be
// unreachable in this app's actual bootstrap: this JupyterLite "notebooks"
// app does not open or populate any document until every federated
// extension -- including the Pyodide kernel's own kernelspec registration
// -- has finished loading, confirmed by repeated Playwright network-delay
// fault injection against that extension specifically (6s-20s+ delays, all
// of which still rendered a fully working notebook with no dialog). What
// *is* independently, deterministically reproducible is the dialog's own
// lifecycle once open: this suite drives the exact same, unmodified
// SessionContextDialogs.selectKernel() JupyterLab itself uses -- via a
// test-only hook course-toolbar exposes on `window` for exactly this
// purpose -- against a session kept genuinely kernel-less by delaying the
// Pyodide kernel's own CDN assets (pyodide.mjs/pyodide.asm.wasm/etc, not
// the kernelspec extension), which does not block the rest of the app from
// rendering. This proves the guard's actual mechanism: a Select Kernel
// dialog that opens while no kernel has started yet gets dismissed quickly
// and does not block the notebook, while Python still starts normally in
// the background and a cell still runs.
test.setTimeout(60_000);

const NOTEBOOK_URL = "/lite/notebooks/index.html?path=exercise_01.ipynb";
const PYODIDE_CDN_DELAY_MS = 9_000;

async function delayPyodideCdnAssets(page: Page): Promise<void> {
  await page.route("https://cdn.jsdelivr.net/pyodide/**", async route => {
    await new Promise(resolve => setTimeout(resolve, PYODIDE_CDN_DELAY_MS));
    await route.continue();
  });
}

async function openTestDialogOnceReady(page: Page): Promise<void> {
  // The hook no-ops (returns false) until tracker.currentWidget exists;
  // retry briefly rather than a single fixed-delay guess.
  await expect
    .poll(
      () =>
        page.evaluate(() =>
          (
            window as unknown as {
              __courseToolbarOpenSelectKernelDialogForTest?: () => Promise<boolean>;
            }
          ).__courseToolbarOpenSelectKernelDialogForTest?.()
        ),
      { timeout: 10_000, intervals: [200] }
    )
    .toBe(true);
}

async function waitForKernelIdle(page: Page, timeoutMs = 30_000) {
  await page.waitForFunction(
    () => document.querySelector(".jp-Notebook-ExecutionIndicator")?.getAttribute("data-status") === "idle",
    undefined,
    { timeout: timeoutMs, polling: 500 },
  );
}

test.describe("Exercise 1 Select-Kernel dialog lifecycle", () => {
  test("a Select Kernel dialog opened while the kernel has not started yet does not stay open, and Python still starts", async ({
    page,
  }) => {
    await delayPyodideCdnAssets(page);
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });

    await openTestDialogOnceReady(page);

    // The guard dismisses it quickly (well inside one second in local
    // testing); this bound is generous, not tuned to that exact timing.
    await expect(page.locator(".jp-Dialog:has-text('Select Kernel')")).toHaveCount(0, { timeout: 5_000 });

    // Confirm it did not silently resolve to "No Kernel" either --
    // Python genuinely starts, including through the still-ongoing CDN
    // delay above, and a trivial cell actually executes.
    await expect(page.locator("text=Python (Pyodide)").first()).toBeVisible({ timeout: 20_000 });
    await page.locator(".jp-CodeCell").first().click();
    await page.keyboard.press("Shift+Enter");
    await waitForKernelIdle(page);
    await expect(page.locator(".jp-mod-error")).toHaveCount(0);
  });

  test("the normal fast path (no delay) never shows a Select Kernel dialog at all", async ({ page }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)").first()).toBeVisible({ timeout: 20_000 });
    await expect(page.locator(".jp-Dialog:has-text('Select Kernel')")).toHaveCount(0);
  });
});
