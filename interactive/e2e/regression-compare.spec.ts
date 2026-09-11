import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `regression-compare` activity,
// served from book/_static/widgets/ at both the site root and the simulated
// GitHub Pages project subpath. The built-Jupyter-Book check lives in
// ../e2e-book/chapter02.spec.ts.
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/regression_compare.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

for (const { name, prefix } of BASES) {
  test.describe(`regression-compare @ ${name}`, () => {
    test("both panels render, defaults are the frontoparietal-vs-occipital comparison, and metrics are real", async ({
      page,
    }) => {
      const failed: string[] = [];
      const sockets: string[] = [];
      page.on("requestfailed", (r) => failed.push(r.url()));
      page.on("websocket", (ws) => sockets.push(ws.url()));

      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const panelA = page.locator('[data-testid="regression-panel-A"]');
      const panelB = page.locator('[data-testid="regression-panel-B"]');
      await expect(panelA).toBeVisible();
      await expect(panelB).toBeVisible();

      // defaults: A = frontoparietal x cortical thickness (78 features),
      //           B = occipital x cortical thickness (46 features).
      await expect(page.locator('[data-testid="regression-A-bundle"]')).toHaveValue("frontoparietal");
      await expect(page.locator('[data-testid="regression-A-measures"]')).toHaveValue("CT");
      await expect(panelA).toHaveAttribute("data-feature-count", "78");
      await expect(page.locator('[data-testid="regression-B-bundle"]')).toHaveValue("occipital");
      await expect(panelB).toHaveAttribute("data-feature-count", "46");

      // both Plotly panels drew
      await expect(page.locator('[data-testid="regression-A-plot"]')).toHaveAttribute(
        "data-render-count",
        /[1-9]/,
      );
      await expect(page.locator('[data-testid="regression-B-plot"]')).toHaveAttribute(
        "data-render-count",
        /[1-9]/,
      );

      // metrics: age IS predictable here — held-out R^2 is positive and the
      // panel exposes the exact value (no "worse than the mean" suffix).
      const aMetrics = await page.locator('[data-testid="regression-A-metrics"]').innerText();
      expect(aMetrics).toMatch(/Out-of-sample R2 = 0\.\d+/);
      expect(aMetrics).not.toContain("worse than predicting the mean");
      const aR2 = Number(await panelA.getAttribute("data-r2"));
      expect(aR2).toBeGreaterThan(0);

      // no CDN / kernel / socket
      expect(sockets).toEqual([]);
      expect(failed).toEqual([]);
    });

    test("changing the ROI bundle recomputes the plot and the metrics, not just a label", async ({
      page,
    }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const panelA = page.locator('[data-testid="regression-panel-A"]');
      const plotA = page.locator('[data-testid="regression-A-plot"]');
      const beforeR2 = await panelA.getAttribute("data-r2");
      const beforeRender = Number(await plotA.getAttribute("data-render-count"));

      await page.locator('[data-testid="regression-A-bundle"]').selectOption("all-eligible");
      await expect(panelA).toHaveAttribute("data-feature-count", "358");
      const afterR2 = await panelA.getAttribute("data-r2");
      const afterRender = Number(await plotA.getAttribute("data-render-count"));

      expect(afterR2).not.toEqual(beforeR2);
      expect(afterRender).toBeGreaterThan(beforeRender);
      // unlike FIQ, age keeps a real, positive signal with every eligible
      // cortical-thickness region — more features here is a modest improvement,
      // not a collapse.
      expect(Number(afterR2)).toBeGreaterThan(0.4);
    });

    test("an unsupported p >= n combination is disabled with a visible reason, not fitted", async ({
      page,
    }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      await page.locator('[data-testid="regression-A-bundle"]').selectOption("all-eligible");
      await page.locator('[data-testid="regression-A-measures"]').selectOption("CT+Area");

      const panelA = page.locator('[data-testid="regression-panel-A"]');
      await expect(panelA).toHaveAttribute("data-disabled", "true");
      const disabled = page.locator('[data-testid="regression-A-disabled"]');
      await expect(disabled).toBeVisible();
      await expect(disabled).toContainText("least squares is not numerically defensible");
      await expect(page.locator('[data-testid="regression-A-plot"]')).toBeHidden();
    });

    test("the ROI list is revealable and lists the bundle's parcels", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const summary = page.locator('[data-testid="regression-A-roi-summary"]');
      await expect(summary).toContainText("78 features");
      const list = page.locator('[data-testid="regression-A-roi-list"]');
      await expect(list).toContainText("IPS1");
      await expect(list).toContainText("46");
    });

    test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({
      page,
    }) => {
      await page.setViewportSize({ width: 390, height: 780 });
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="regression-panel-A"]')).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);
      // the bundle select is keyboard reachable
      await page.locator('[data-testid="regression-A-bundle"]').focus();
      await expect(page.locator('[data-testid="regression-A-bundle"]')).toBeFocused();
    });
  });
}
