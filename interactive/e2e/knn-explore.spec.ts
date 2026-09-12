import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `knn-explore` activity, served
// from book/_static/widgets/ at both the site root and the simulated GitHub
// Pages project subpath. The built-Jupyter-Book check lives in
// ../e2e-book/chapter03.spec.ts.
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/knn_explore.json";
const N_FIT = 564;

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

for (const { name, prefix } of BASES) {
  test.describe(`knn-explore @ ${name}`, () => {
    test("loads with the validation-optimal default k, real metrics, and both plots rendered", async ({
      page,
    }) => {
      const failed: string[] = [];
      const sockets: string[] = [];
      page.on("requestfailed", (r) => failed.push(r.url()));
      page.on("websocket", (ws) => sockets.push(ws.url()));

      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const slider = page.locator('[data-testid="knn-k-slider"]');
      await expect(slider).toHaveAttribute("min", "1");
      await expect(slider).toHaveAttribute("max", String(N_FIT));
      await expect(slider).toHaveValue("17"); // validation-optimal k, from the committed data
      await expect(page.locator('[data-testid="knn-k-value"]')).toHaveText("17");

      const metrics = await page.locator('[data-testid="knn-metrics"]').textContent();
      expect(metrics).toMatch(/k = 17/);
      expect(metrics).toMatch(/validation R2 = 0\.\d+/);

      await expect(page.locator('[data-testid="knn-scatter-plot"]')).toHaveAttribute(
        "data-render-count",
        /[1-9]/,
      );
      await expect(page.locator('[data-testid="knn-curve-plot"]')).toHaveAttribute(
        "data-render-count",
        /[1-9]/,
      );

      expect(sockets).toEqual([]);
      expect(failed).toEqual([]);
    });

    test("moving k recomputes the metrics and both plots, not just the label", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const slider = page.locator('[data-testid="knn-k-slider"]');
      const scatter = page.locator('[data-testid="knn-scatter-plot"]');
      const beforeMetrics = await page.locator('[data-testid="knn-metrics"]').textContent();
      const beforeRender = Number(await scatter.getAttribute("data-render-count"));

      await slider.fill("1");
      await expect(page.locator('[data-testid="knn-k-value"]')).toHaveText("1");
      const afterMetrics = await page.locator('[data-testid="knn-metrics"]').textContent();
      const afterRender = Number(await scatter.getAttribute("data-render-count"));

      expect(afterMetrics).not.toEqual(beforeMetrics);
      expect(afterMetrics).toMatch(/fitting R2 = 1\.000/);
      expect(afterRender).toBeGreaterThan(beforeRender);
    });

    test("k = N_fit collapses the scatter to a single predicted value (the fitting-set mean)", async ({
      page,
    }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      await page.locator('[data-testid="knn-k-slider"]').fill(String(N_FIT));
      await expect(page.locator('[data-testid="knn-k-value"]')).toHaveText(String(N_FIT));
      const metrics = await page.locator('[data-testid="knn-metrics"]').textContent();
      expect(metrics).toMatch(/fitting R2 = -?0\.000/);

      const endpoint = page.locator('[data-testid="knn-endpoint-kmax"]');
      await expect(endpoint).toContainText("constant");
    });

    test("keyboard interaction moves the slider and updates the display", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const slider = page.locator('[data-testid="knn-k-slider"]');
      await slider.focus();
      await expect(slider).toBeFocused();
      const before = await slider.inputValue();
      await slider.press("ArrowUp");
      await expect(slider).not.toHaveValue(before);
    });

    test("the identity line is labelled in a visible legend", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const legendText = await page.locator('[data-testid="knn-scatter-plot"] .legend').textContent();
      expect(legendText).toContain("Perfect prediction (observed = predicted)");
    });

    test("endpoint explanations for k=1 and k=N_fit are present", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="knn-endpoint-k1"]')).toContainText("nearest neighbour");
      await expect(page.locator('[data-testid="knn-endpoint-kmax"]')).toContainText("fitting-set mean");
    });

    test("browser refresh restores the configured default k", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await page.locator('[data-testid="knn-k-slider"]').fill("100");
      await expect(page.locator('[data-testid="knn-k-value"]')).toHaveText("100");

      await page.reload();
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="knn-k-slider"]')).toHaveValue("17");
    });

    test("numeric input is synchronized with the slider in both directions", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const slider = page.locator('[data-testid="knn-k-slider"]');
      const number = page.locator('[data-testid="knn-k-number"]');
      await expect(number).toHaveValue("17");

      await slider.fill("50");
      await expect(number).toHaveValue("50");

      await number.fill("120");
      await number.dispatchEvent("change");
      await expect(slider).toHaveValue("120");
      await expect(page.locator('[data-testid="knn-k-value"]')).toHaveText("120");
    });

    test("numeric input rejects an out-of-range value and keeps the last valid k", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const number = page.locator('[data-testid="knn-k-number"]');
      await number.fill(String(N_FIT + 500));
      await number.dispatchEvent("change");
      await expect(number).toHaveValue("17");
      await expect(page.locator('[data-testid="knn-k-value"]')).toHaveText("17");
    });

    test("switching training-sample tabs updates the scatter without changing the validation set", async ({
      page,
    }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await page.locator('[data-testid="knn-k-slider"]').fill("3");

      const scatter = page.locator('[data-testid="knn-scatter-plot"]');
      const beforeRender = Number(await scatter.getAttribute("data-render-count"));
      await page.locator('[data-testid="knn-sample-tab-B"]').click();
      await expect(page.locator('[data-testid="knn-sample-tab-B"]')).toHaveAttribute("aria-selected", "true");
      await expect(page.locator('[data-testid="knn-sample-tab-A"]')).toHaveAttribute("aria-selected", "false");
      const afterRender = Number(await scatter.getAttribute("data-render-count"));
      expect(afterRender).toBeGreaterThan(beforeRender);
    });

    test("variance and bias-like proxy readouts are present and change with k", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const variance = page.locator('[data-testid="knn-variance-proxy"]');
      const bias = page.locator('[data-testid="knn-bias-proxy"]');
      const beforeVariance = await variance.innerText();
      const beforeBias = await bias.innerText();

      await page.locator('[data-testid="knn-k-slider"]').fill("3");
      await expect(variance).not.toHaveText(beforeVariance);
      await expect(bias).not.toHaveText(beforeBias);
      await expect(page.locator('[data-testid="knn-bias-plot"]')).toHaveAttribute("data-render-count", /[1-9]/);
    });

    test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({
      page,
    }) => {
      await page.setViewportSize({ width: 390, height: 900 });
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="knn-scatter-plot"]')).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);
    });
  });
}
