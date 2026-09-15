import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `classification-threshold`
// activity (WP17 §4), served from book/_static/widgets/ at both the site
// root and the simulated GitHub Pages project subpath. The built-Jupyter-Book
// check lives in ../e2e-book/chapter04.spec.ts.
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/classification_threshold.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

for (const { name, prefix } of BASES) {
  test.describe(`classification-threshold @ ${name}`, () => {
    test("loads at the default 0.50 threshold with real metrics and a rendered ROC plot", async ({ page }) => {
      const failed: string[] = [];
      const sockets: string[] = [];
      page.on("requestfailed", (r) => failed.push(r.url()));
      page.on("websocket", (ws) => sockets.push(ws.url()));

      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const slider = page.locator('[data-testid="cls-threshold-slider"]');
      await expect(slider).toHaveAttribute("min", "0.05");
      await expect(slider).toHaveAttribute("max", "0.95");
      await expect(slider).toHaveValue("0.5");
      await expect(page.locator('[data-testid="cls-threshold-value"]')).toHaveText("0.50");
      await expect(page.locator('[data-testid="cls-roc-plot"]')).toHaveAttribute("data-render-count", /[1-9]/);

      const metrics = await page.locator('[data-testid="cls-metrics"]').textContent();
      expect(metrics).toMatch(/accuracy = 0\.\d{3}/);
      expect(metrics).toMatch(/AUC \(fixed, threshold-independent\) = 0\.\d{3}/);

      expect(sockets).toEqual([]);
      expect(failed).toEqual([]);
    });

    test("moving the threshold recomputes the confusion matrix, not just labels", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const beforeTp = await page.locator('[data-testid="cls-cm-tp"]').textContent();
      const beforeFn = await page.locator('[data-testid="cls-cm-fn"]').textContent();

      const slider = page.locator('[data-testid="cls-threshold-slider"]');
      await slider.fill("0.9");
      await slider.dispatchEvent("change");

      const afterTp = await page.locator('[data-testid="cls-cm-tp"]').textContent();
      const afterFn = await page.locator('[data-testid="cls-cm-fn"]').textContent();
      expect(Number(afterTp)).toBeLessThanOrEqual(Number(beforeTp));
      expect(Number(afterFn)).toBeGreaterThanOrEqual(Number(beforeFn));
    });

    test("the AUC stays fixed across every threshold change", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const extractAuc = async () => {
        const text = await page.locator('[data-testid="cls-metrics"]').textContent();
        return text?.match(/AUC \(fixed, threshold-independent\) = (\d\.\d{3})/)?.[1];
      };
      const aucAt50 = await extractAuc();
      const slider = page.locator('[data-testid="cls-threshold-slider"]');
      await slider.fill("0.15");
      await slider.dispatchEvent("change");
      const aucAt15 = await extractAuc();
      await slider.fill("0.85");
      await slider.dispatchEvent("change");
      const aucAt85 = await extractAuc();

      expect(aucAt50).toBeTruthy();
      expect(aucAt15).toBe(aucAt50);
      expect(aucAt85).toBe(aucAt50);
    });

    test("numeric input is synchronized with the slider and rejects out-of-range values", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const slider = page.locator('[data-testid="cls-threshold-slider"]');
      const number = page.locator('[data-testid="cls-threshold-number"]');
      await number.fill("0.7");
      await number.dispatchEvent("change");
      await expect(slider).toHaveValue("0.7");

      await number.fill("3");
      await number.dispatchEvent("change");
      await expect(number).toHaveValue("0.70");
    });

    test("reset control restores the 0.50 default", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const slider = page.locator('[data-testid="cls-threshold-slider"]');
      await slider.fill("0.9");
      await slider.dispatchEvent("change");
      await expect(page.locator('[data-testid="cls-threshold-value"]')).toHaveText("0.90");

      await page.locator('[data-testid="cls-threshold-reset"]').click();
      await expect(page.locator('[data-testid="cls-threshold-value"]')).toHaveText("0.50");
      await expect(slider).toHaveValue("0.5");
    });

    test("keyboard interaction moves the slider and updates the display", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const slider = page.locator('[data-testid="cls-threshold-slider"]');
      await slider.focus();
      await expect(slider).toBeFocused();
      const before = await slider.inputValue();
      await slider.press("ArrowUp");
      await expect(slider).not.toHaveValue(before);
    });

    test("the ROC diagonal is labelled 'Chance-level ranking'", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const legendText = await page.locator('[data-testid="cls-roc-plot"] .legend').textContent();
      expect(legendText).toContain("Chance-level ranking");
    });

    test("browser refresh restores the documented default (0.50)", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const slider = page.locator('[data-testid="cls-threshold-slider"]');
      await slider.fill("0.8");
      await slider.dispatchEvent("change");

      await page.reload();
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="cls-threshold-slider"]')).toHaveValue("0.5");
    });

    test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 900 });
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="cls-roc-plot"]')).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);
    });
  });
}
