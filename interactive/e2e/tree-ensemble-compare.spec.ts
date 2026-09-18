import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `tree-ensemble-compare`
// activity ("One Tree or Many?"), served from book/_static/widgets/. The
// built-Jupyter-Book check lives in ../e2e-book/chapter06.spec.ts.
const QUERY = "?config=../configs/tree_ensemble_compare.json";

function appUrl(query = ""): string {
  return `/app/index.html${query}`;
}

test.describe("tree-ensemble-compare", () => {
  test("loads with every panel rendered and no unexpected network activity", async ({ page }) => {
    const failed: string[] = [];
    const sockets: string[] = [];
    page.on("requestfailed", (r) => failed.push(r.url()));
    page.on("websocket", (ws) => sockets.push(ws.url()));

    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await expect(page.locator('[data-testid="tree-ensemble-distribution-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );
    await expect(page.locator('[data-testid="tree-ensemble-size-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );
    await expect(page.locator('[data-testid="tree-ensemble-prediction-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );

    expect(failed, `unexpected network failures: ${failed.join(", ")}`).toHaveLength(0);
    expect(sockets, `unexpected websocket connections: ${sockets.join(", ")}`).toHaveLength(0);
  });

  test("defaults to Random Forest and shows its feature-subset setting", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(page.locator('[data-testid="tree-ensemble-model-select"]')).toHaveValue("random-forest");
    const metrics = await page.locator('[data-testid="tree-ensemble-prediction-metrics"]').innerText();
    expect(metrics).toContain("Random Forest");
    expect(metrics).toContain("feature-subset size");
  });

  test("changing training replicate updates the prediction plot", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const renderCountBefore = await page
      .locator('[data-testid="tree-ensemble-prediction-plot"]')
      .getAttribute("data-render-count");
    await page.locator('[data-testid="tree-ensemble-replicate-select"]').selectOption({ index: 1 });
    await expect(async () => {
      const current = await page
        .locator('[data-testid="tree-ensemble-prediction-plot"]')
        .getAttribute("data-render-count");
      expect(current).not.toBe(renderCountBefore);
    }).toPass({ timeout: 3000 });
  });

  test("selecting the single tree disables the number-of-trees control", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await page.locator('[data-testid="tree-ensemble-model-select"]').selectOption("single-tree");
    await expect(page.locator('[data-testid="tree-ensemble-ntrees-select"]')).toBeDisabled();
    const metrics = await page.locator('[data-testid="tree-ensemble-prediction-metrics"]').innerText();
    expect(metrics).toContain("not applicable");
  });

  test("changing number of trees updates the highlighted validation MSE", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await page.locator('[data-testid="tree-ensemble-model-select"]').selectOption("bagging");

    const app = page.locator("#app");
    const mseAtDefault = await app.getAttribute("data-val-mse");
    await page.locator('[data-testid="tree-ensemble-ntrees-select"]').selectOption({ index: 0 });
    await expect(async () => {
      const current = await app.getAttribute("data-val-mse");
      expect(current).not.toBe(mseAtDefault);
    }).toPass({ timeout: 3000 });
  });

  test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(page.locator('[data-testid="tree-ensemble-distribution-plot"]')).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("shows the error panel when pointed at a nonexistent config", async ({ page }) => {
    await page.goto(appUrl("?config=../configs/tree_ensemble_compare_missing.json"));
    await expect(page.locator('[data-testid="widget-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="widget-error-message"]')).toContainText("HTTP 404");
  });
});
