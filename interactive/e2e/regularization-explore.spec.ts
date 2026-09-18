import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `regularization-explore`
// activity ("Shrink the Coefficients"), served from book/_static/widgets/ at
// both the site root and the simulated GitHub Pages project subpath. The
// built-Jupyter-Book check lives in ../e2e-book/chapter05.spec.ts.
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/regularization_explore.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

for (const { name, prefix } of BASES) {
  test.describe(`regularization-explore @ ${name}`, () => {
    test("defaults to Ridge at its best validation alpha, and every display renders", async ({ page }) => {
      const failed: string[] = [];
      const sockets: string[] = [];
      page.on("requestfailed", (r) => failed.push(r.url()));
      page.on("websocket", (ws) => sockets.push(ws.url()));

      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      await expect(page.locator('[data-testid="regularization-model-select"]')).toHaveValue("ridge");
      await expect(page.locator('[data-testid="regularization-alpha-slider"]')).toBeEnabled();
      await expect(page.locator('[data-testid="regularization-alpha-disabled-note"]')).toBeHidden();

      const metrics = await page.locator('[data-testid="regularization-metrics"]').innerText();
      expect(metrics).toContain("Ridge");
      expect(metrics).toContain("alpha = 562");
      expect(metrics).toContain("best validation alpha = 562");
      expect(metrics).toContain("unregularized linear-regression baseline validation MSE = 76.1");

      await expect(page.locator('[data-testid="regularization-predictions-plot"]')).toHaveAttribute(
        "data-render-count",
        /[1-9]/,
      );
      await expect(page.locator('[data-testid="regularization-coefficients-plot"]')).toHaveAttribute(
        "data-render-count",
        /[1-9]/,
      );

      expect(failed, `unexpected network failures: ${failed.join(", ")}`).toHaveLength(0);
      expect(sockets, `unexpected websocket connections: ${sockets.join(", ")}`).toHaveLength(0);
    });

    test("choosing Linear Regression disables the alpha control and shows the baseline note", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      await page.locator('[data-testid="regularization-model-select"]').selectOption("linear");

      await expect(page.locator('[data-testid="regularization-alpha-slider"]')).toBeDisabled();
      await expect(page.locator('[data-testid="regularization-alpha-select"]')).toBeDisabled();
      await expect(page.locator('[data-testid="regularization-alpha-disabled-note"]')).toBeVisible();

      const metrics = await page.locator('[data-testid="regularization-metrics"]').innerText();
      expect(metrics).toContain("Linear Regression");
      expect(metrics).toContain("not applicable");
    });

    test("choosing Lasso and moving alpha lowers the nonzero-coefficient count as alpha grows", async ({
      page,
    }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const select = page.locator('[data-testid="regularization-model-select"]');
      await select.selectOption("lasso");

      const app = page.locator("#app");
      const nnzAtBest = Number(await app.getAttribute("data-nonzero-count"));
      expect(nnzAtBest).toBeGreaterThan(0);
      expect(nnzAtBest).toBeLessThan(360);

      // Move to the highest alpha on the grid (last <option>).
      const alphaSelect = page.locator('[data-testid="regularization-alpha-select"]');
      const optionCount = await alphaSelect.locator("option").count();
      await alphaSelect.selectOption({ index: optionCount - 1 });

      const nnzAtMax = Number(await app.getAttribute("data-nonzero-count"));
      expect(nnzAtMax).toBeLessThanOrEqual(nnzAtBest);
    });

    test("test-set results are never exposed while exploring alpha", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const bodyText = await page.locator("#app").innerText();
      expect(bodyText.toLowerCase()).not.toContain("test mse");
      expect(bodyText.toLowerCase()).not.toContain("test r2");
      expect(bodyText.toLowerCase()).not.toContain("held-out");
    });
  });
}
