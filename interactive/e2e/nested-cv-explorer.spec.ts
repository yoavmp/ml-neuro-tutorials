import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `nested-cv-explorer` activity
// (WP27, Exercise 4's "Look Inside Nested Cross-Validation"). The
// built-Jupyter-Book check lives in ../e2e-book/chapter04.spec.ts and the
// dark-mode check in ../e2e-book/wp22-cross-chapter-dark-mode.spec.ts.
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/nested_cv_explorer.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

for (const { name, prefix } of BASES) {
  test.describe(`nested-cv-explorer @ ${name}`, () => {
    test("loads with the configured default outer fold, correct metrics, inner plot and summary rendered", async ({
      page,
    }) => {
      const consoleErrors: string[] = [];
      const sockets: string[] = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") consoleErrors.push(msg.text());
      });
      page.on("websocket", (ws) => sockets.push(ws.url()));

      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      await expect(page.locator("#app")).toHaveAttribute("data-outer-fold", "0");
      await expect(page.locator('[data-testid="nested-cv-fold-0"]')).toHaveAttribute("aria-selected", "true");

      const foldStats = await page.locator('[data-testid="nested-cv-fold-stats"]').innerText();
      expect(foldStats).toMatch(/Outer fold 1:/);
      expect(foldStats).toMatch(/Selected k = \d+/);
      expect(foldStats).toMatch(/Outer-test MSE = [\d.]+/);
      expect(foldStats).toMatch(/outer-test R² = [\d.]+/);
      // the outer score, not the inner-CV score, is framed as the estimate
      expect(foldStats).toMatch(/outer-test score.*not the inner-CV score.*estimates future performance/);

      await expect(page.locator('[data-testid="nested-cv-inner-plot"]')).toHaveAttribute(
        "data-render-count",
        /[1-9]/,
      );

      const summary = await page.locator('[data-testid="nested-cv-summary-stats"]').innerText();
      expect(summary).toMatch(/Selected k per outer fold: [\d, ]+/);
      expect(summary).toMatch(/Mean outer-test MSE = [\d.]+/);

      await expect(page.locator('[data-testid="nested-cv-summary-table"]')).toBeVisible();

      expect(sockets).toEqual([]);
      expect(consoleErrors, consoleErrors.join("; ")).toEqual([]);
    });

    test("selecting a different outer fold updates the fold stats and redraws the inner plot", async ({
      page,
    }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const innerPlot = page.locator('[data-testid="nested-cv-inner-plot"]');
      const beforeRender = Number(await innerPlot.getAttribute("data-render-count"));
      const beforeStats = await page.locator('[data-testid="nested-cv-fold-stats"]').innerText();

      await page.locator('[data-testid="nested-cv-fold-1"]').click();
      await expect(page.locator("#app")).toHaveAttribute("data-outer-fold", "1");
      await expect(page.locator('[data-testid="nested-cv-fold-1"]')).toHaveAttribute("aria-selected", "true");
      await expect(page.locator('[data-testid="nested-cv-fold-0"]')).toHaveAttribute("aria-selected", "false");

      const afterStats = await page.locator('[data-testid="nested-cv-fold-stats"]').innerText();
      expect(afterStats).not.toEqual(beforeStats);
      expect(afterStats).toMatch(/Outer fold 2:/);

      const afterRender = Number(await innerPlot.getAttribute("data-render-count"));
      expect(afterRender).toBeGreaterThan(beforeRender);

      // the cross-fold summary itself never changes when only the selected fold changes
      const summary = await page.locator('[data-testid="nested-cv-summary-stats"]').innerText();
      expect(summary).toMatch(/Mean outer-test MSE = [\d.]+/);
    });

    test("browser refresh restores the configured default outer fold", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await page.locator('[data-testid="nested-cv-fold-3"]').click();
      await expect(page.locator("#app")).toHaveAttribute("data-outer-fold", "3");

      await page.reload();
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator("#app")).toHaveAttribute("data-outer-fold", "0");
    });

    test("shows the error panel when pointed at a nonexistent config", async ({ page }) => {
      await page.goto(appUrl(prefix, "?config=../configs/nested_cv_explorer_missing.json"));
      await expect(page.locator('[data-testid="widget-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="widget-error-message"]')).toContainText("HTTP 404");
    });

    test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({
      page,
    }) => {
      await page.setViewportSize({ width: 390, height: 900 });
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="nested-cv-inner-plot"]')).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);
    });
  });
}
