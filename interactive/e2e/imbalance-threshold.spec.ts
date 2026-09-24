import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `imbalance-threshold` activity
// (WP38, Exercise 10: "High accuracy can still miss the minority class"),
// served from book/_static/widgets/ at both the site root and the simulated
// GitHub Pages project subpath. The built-Jupyter-Book check is added
// separately once the notebook exists (see e2e-book/).
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/imbalance_threshold.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

for (const { name, prefix } of BASES) {
  test.describe(`imbalance-threshold @ ${name}`, () => {
    test("loads at the default ordinary model / 0.50 threshold with the primary tiles rendered", async ({
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

      await expect(page.locator('[data-testid="imb-model-select"]')).toHaveValue("ordinary");
      await expect(page.locator('[data-testid="imb-threshold-value"]')).toHaveText("0.50");

      const cohort = await page.locator('[data-testid="imb-cohort"]').textContent();
      expect(cohort).toMatch(/400 participants/);

      await expect(page.locator('[data-testid="imb-accuracy"]')).toHaveText("85.0%");
      const baseline = await page.locator('[data-testid="imb-baseline"]').innerText();
      expect(baseline).toMatch(/90\.0%/);

      await expect(page.locator('[data-testid="imb-cm-tn"]')).toHaveText("84");
      await expect(page.locator('[data-testid="imb-cm-fp"]')).toHaveText("6");
      await expect(page.locator('[data-testid="imb-cm-fn"]')).toHaveText("9");
      await expect(page.locator('[data-testid="imb-cm-tp"]')).toHaveText("1");

      expect(sockets).toEqual([]);
      expect(failed).toEqual([]);
      expect(consoleErrors, consoleErrors.join("; ")).toEqual([]);
    });

    test("switching to the class-weighted model recomputes the confusion matrix without refitting", async ({
      page,
    }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      await page.locator('[data-testid="imb-model-select"]').selectOption("classWeighted");
      await expect(page.locator('[data-testid="imb-accuracy"]')).toHaveText("81.0%");
      await expect(page.locator('[data-testid="imb-cm-tn"]')).toHaveText("80");
      await expect(page.locator('[data-testid="imb-cm-fp"]')).toHaveText("10");

      const secondary = await page.locator('[data-testid="imb-secondary-metrics"]').innerText();
      expect(secondary).toMatch(/ROC-AUC \(fixed, threshold-independent\) = 0\.628/);

      // PR-AUC is threshold-independent and specific to the class-weighted model
      await expect(page.locator('[data-testid="imb-prauc"]')).toHaveText("0.142");
    });

    test("moving the threshold recomputes the confusion matrix in real time", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const before = await page.locator('[data-testid="imb-cm-tp"]').textContent();
      await page.locator('[data-testid="imb-threshold-number"]').fill("0.05");
      await page.locator('[data-testid="imb-threshold-number"]').dispatchEvent("change");
      await expect(page.locator('[data-testid="imb-threshold-value"]')).toHaveText("0.05");

      const after = await page.locator('[data-testid="imb-cm-tp"]').textContent();
      expect(after).not.toEqual(before);

      // PR-AUC and ROC-AUC never change with the threshold
      const praucAfter = await page.locator('[data-testid="imb-prauc"]').textContent();
      expect(praucAfter).toBe("0.143");
    });

    test("reset returns to the default model and threshold", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      await page.locator('[data-testid="imb-model-select"]').selectOption("classWeighted");
      await page.locator('[data-testid="imb-threshold-number"]').fill("0.9");
      await page.locator('[data-testid="imb-threshold-number"]').dispatchEvent("change");

      await page.locator('[data-testid="imb-reset-button"]').click();
      await expect(page.locator('[data-testid="imb-model-select"]')).toHaveValue("ordinary");
      await expect(page.locator('[data-testid="imb-threshold-value"]')).toHaveText("0.50");
      await expect(page.locator('[data-testid="imb-accuracy"]')).toHaveText("85.0%");
    });

    test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 900 });
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="imb-confusion-matrix"]')).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);
    });
  });
}
