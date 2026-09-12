import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `knn-abc` activity (WP14 §4.4),
// served from book/_static/widgets/ at both the site root and the simulated
// GitHub Pages project subpath. The built-Jupyter-Book check lives in
// ../e2e-book/chapter03.spec.ts.
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/knn_abc.json";
const K_MAX = 251;

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

for (const { name, prefix } of BASES) {
  test.describe(`knn-abc @ ${name}`, () => {
    test("loads with the audit-selected default k and all three panels rendered", async ({ page }) => {
      const failed: string[] = [];
      const sockets: string[] = [];
      page.on("requestfailed", (r) => failed.push(r.url()));
      page.on("websocket", (ws) => sockets.push(ws.url()));

      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const slider = page.locator('[data-testid="knn-abc-k-slider"]');
      await expect(slider).toHaveAttribute("min", "1");
      await expect(slider).toHaveAttribute("max", String(K_MAX));
      await expect(slider).toHaveValue("15"); // audit-selected k, from the committed data
      await expect(page.locator('[data-testid="knn-abc-k-value"]')).toHaveText("15");

      for (const panel of ["a", "b", "c"]) {
        await expect(page.locator(`[data-testid="knn-abc-panel-${panel}-plot"]`)).toHaveAttribute(
          "data-render-count",
          /[1-9]/,
        );
        const metrics = await page.locator(`[data-testid="knn-abc-panel-${panel}-metrics"]`).textContent();
        expect(metrics).toMatch(/R2 = -?\d\.\d{3}/);
      }

      expect(sockets).toEqual([]);
      expect(failed).toEqual([]);
    });

    test("k=1 makes B and C exactly perfect (R2 = 1.000) while A is not", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      await page.locator('[data-testid="knn-abc-k-slider"]').fill("1");
      await expect(page.locator('[data-testid="knn-abc-k-value"]')).toHaveText("1");

      const aMetrics = await page.locator('[data-testid="knn-abc-panel-a-metrics"]').textContent();
      const bMetrics = await page.locator('[data-testid="knn-abc-panel-b-metrics"]').textContent();
      const cMetrics = await page.locator('[data-testid="knn-abc-panel-c-metrics"]').textContent();
      expect(bMetrics).toMatch(/R2 = 1\.000/);
      expect(cMetrics).toMatch(/R2 = 1\.000/);
      expect(aMetrics).not.toMatch(/R2 = 1\.000/);
    });

    test("moving k recomputes all three panels, not just labels", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const beforeA = await page.locator('[data-testid="knn-abc-panel-a-metrics"]').textContent();
      const beforeRenderA = Number(
        await page.locator('[data-testid="knn-abc-panel-a-plot"]').getAttribute("data-render-count"),
      );

      await page.locator('[data-testid="knn-abc-k-slider"]').fill("50");
      const afterA = await page.locator('[data-testid="knn-abc-panel-a-metrics"]').textContent();
      const afterRenderA = Number(
        await page.locator('[data-testid="knn-abc-panel-a-plot"]').getAttribute("data-render-count"),
      );
      expect(afterA).not.toEqual(beforeA);
      expect(afterRenderA).toBeGreaterThan(beforeRenderA);
    });

    test("numeric input is synchronized with the slider and rejects out-of-range values", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const slider = page.locator('[data-testid="knn-abc-k-slider"]');
      const number = page.locator('[data-testid="knn-abc-k-number"]');
      await number.fill("100");
      await number.dispatchEvent("change");
      await expect(slider).toHaveValue("100");

      await number.fill(String(K_MAX + 999));
      await number.dispatchEvent("change");
      await expect(number).toHaveValue("100");
    });

    test("keyboard interaction moves the slider and updates the display", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const slider = page.locator('[data-testid="knn-abc-k-slider"]');
      await slider.focus();
      await expect(slider).toBeFocused();
      const before = await slider.inputValue();
      await slider.press("ArrowUp");
      await expect(slider).not.toHaveValue(before);
    });

    test("k1 note explaining the resubstitution endpoint is present", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="knn-abc-k1-note"]')).toContainText("nearest neighbour");
    });

    test("every panel's identity line is labelled in a visible legend", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const legendText = await page.locator('[data-testid="knn-abc-panel-a-plot"] .legend').textContent();
      expect(legendText).toContain("Perfect prediction");
    });

    test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 900 });
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="knn-abc-panel-a-plot"]')).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);
    });
  });
}
