import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `leakage-lab` activity (WP38,
// Exercise 10: "What happens when the test set leaks in?"), served from
// book/_static/widgets/ at both the site root and the simulated GitHub Pages
// project subpath. The built-Jupyter-Book check is added separately once the
// notebook exists (see e2e-book/).
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/leakage_lab.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

for (const { name, prefix } of BASES) {
  test.describe(`leakage-lab @ ${name}`, () => {
    test("loads at the default feature-selection / all-eligible-participants / Split 1 combination", async ({
      page,
    }) => {
      const failed: string[] = [];
      const sockets: string[] = [];
      const consoleErrors: string[] = [];
      page.on("requestfailed", (r) => failed.push(r.url()));
      page.on("websocket", (ws) => sockets.push(ws.url()));
      page.on("console", (msg) => {
        if (msg.type() === "error") consoleErrors.push(msg.text());
      });

      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      await expect(page.locator('[data-testid="leak-operation-select"]')).toHaveValue("feature_selection");
      await expect(page.locator("#app")).toHaveAttribute("data-current-sample-size", "1004");
      await expect(page.locator("#app")).toHaveAttribute("data-current-seed", "0");

      const correctWorkflow = await page.locator('[data-testid="leak-workflow-correct"]').innerText();
      expect(correctWorkflow).toMatch(/split first/i);
      const leakyWorkflow = await page.locator('[data-testid="leak-workflow-leaky"]').innerText();
      expect(leakyWorkflow).toMatch(/SelectKBest/);

      // The estimator is KNeighborsRegressor(n_neighbors=15) in every
      // scenario (WP38R sec 4); the workflow text should describe it, not
      // the old LinearRegression.
      expect(correctWorkflow).toMatch(/KNeighborsRegressor\(n_neighbors=15\)/);

      await expect(page.locator('[data-testid="leak-pair-plot"] svg.main-svg').first()).toBeVisible();
      await expect(page.locator('[data-testid="leak-aggregate-plot"] svg.main-svg').first()).toBeVisible();

      // Paired signed-difference readouts (WP38R sec 4.2) are present with a
      // labeled direction for the default selection.
      const r2Diff = await page.locator('[data-testid="leak-r2-diff"]').innerText();
      expect(r2Diff).toMatch(/ΔR² \(leaky − correct\) = [+-]?\d/);
      const mseDiff = await page.locator('[data-testid="leak-mse-diff"]').innerText();
      expect(mseDiff).toMatch(/ΔMSE \(leaky − correct\) = [+-]?\d/);

      expect(sockets).toEqual([]);
      expect(failed).toEqual([]);
      expect(consoleErrors, consoleErrors.join("; ")).toEqual([]);
    });

    test("scaling at sample size 60, split 1 shows a real, non-hidden correct/leaky gap (KNN is scale-sensitive)", async ({
      page,
    }) => {
      // Historical note: under the old LinearRegression estimator this gap
      // was mathematically zero (OLS is scale-invariant). The estimator is
      // now KNeighborsRegressor(n_neighbors=15) (WP38R sec 4), which IS
      // scale-sensitive, so correct and leaky no longer match here -- values
      // below are read from the freshly recomputed
      // book/_static/widgets/data/abide_leakage_lab.json, not fabricated.
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      await page.locator('[data-testid="leak-operation-select"]').selectOption("scaling");
      await page.locator('[data-testid="leak-samplesize-select"]').selectOption("60");
      await page.locator('[data-testid="leak-seed-select"]').selectOption("0");

      const correctMetrics = await page.locator('[data-testid="leak-correct-metrics"]').innerText();
      const leakyMetrics = await page.locator('[data-testid="leak-leaky-metrics"]').innerText();
      expect(correctMetrics).not.toEqual(leakyMetrics);
      expect(correctMetrics).toMatch(/Test MSE = 133\.07/);
      expect(leakyMetrics).toMatch(/Test MSE = 132\.06/);

      const r2Diff = await page.locator('[data-testid="leak-r2-diff"]').innerText();
      expect(r2Diff).toMatch(/ΔR² \(leaky − correct\) = \+0\.008/);
      const mseDiff = await page.locator('[data-testid="leak-mse-diff"]').innerText();
      expect(mseDiff).toMatch(/ΔMSE \(leaky − correct\) = -1\.01/);
    });

    test("changing the sample size and split updates the underlying split statistics", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const before = await page.locator('[data-testid="leak-split-stats"]').innerText();
      await page.locator('[data-testid="leak-samplesize-select"]').selectOption("100");
      const afterSize = await page.locator('[data-testid="leak-split-stats"]').innerText();
      expect(afterSize).not.toEqual(before);
      expect(afterSize).toMatch(/n_train = 75/);

      await page.locator('[data-testid="leak-seed-select"]').selectOption("1");
      const afterSeed = await page.locator('[data-testid="leak-split-stats"]').innerText();
      expect(afterSeed).toMatch(/Split 2/);
    });

    test("reset returns to the default operation, sample size, and split", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      await page.locator('[data-testid="leak-operation-select"]').selectOption("pca");
      await page.locator('[data-testid="leak-samplesize-select"]').selectOption("60");
      await page.locator('[data-testid="leak-seed-select"]').selectOption("3");
      await expect(page.locator("#app")).toHaveAttribute("data-current-scenario", "pca");

      await page.locator('[data-testid="leak-reset-button"]').click();
      await expect(page.locator("#app")).toHaveAttribute("data-current-scenario", "feature_selection");
      await expect(page.locator("#app")).toHaveAttribute("data-current-sample-size", "1004");
      await expect(page.locator("#app")).toHaveAttribute("data-current-seed", "0");
    });

    test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 900 });
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="leak-pair-plot"]')).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);
    });
  });
}
