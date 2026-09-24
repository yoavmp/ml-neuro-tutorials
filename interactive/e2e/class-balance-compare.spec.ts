import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `class-balance-compare`
// activity (WP38R sec 5, Exercise 10: "Does higher accuracy mean a better
// classifier?"), served from book/_static/widgets/ at both the site root and
// the simulated GitHub Pages project subpath. This activity replaces the
// removed `imbalance-threshold` activity (deleted spec:
// imbalance-threshold.spec.ts) -- there is no threshold control anywhere
// here; the only primary control is the class-balance selector.
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/class_balance_compare.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

// Expected values recomputed once from the committed artifact
// (book/_static/widgets/data/abide_class_balance_compare.json) by
// scripts/export_class_balance_compare_data.py --refresh -- not tuned or
// curated after the fact.
const RATIO_BASELINES: Record<string, { majorityBaseline: string; prAucBaseline: string }> = {
  "50:50": { majorityBaseline: "50.0%", prAucBaseline: "0.500" },
  "60:40": { majorityBaseline: "60.0%", prAucBaseline: "0.400" },
  "70:30": { majorityBaseline: "70.0%", prAucBaseline: "0.300" },
  "80:20": { majorityBaseline: "80.0%", prAucBaseline: "0.200" },
  "90:10": { majorityBaseline: "90.0%", prAucBaseline: "0.100" },
};

for (const { name, prefix } of BASES) {
  test.describe(`class-balance-compare @ ${name}`, () => {
    test("loads at the default 50:50 balance with both models shown and no threshold control", async ({
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

      await expect(page.locator('[data-testid="cbc-ratio-select"]')).toHaveValue("50:50");

      const cohort = await page.locator('[data-testid="cbc-cohort"]').textContent();
      expect(cohort).toMatch(/400 participants/);
      expect(cohort).toMatch(/200 control/);
      expect(cohort).toMatch(/200 autism/);

      // Both models rendered simultaneously, not behind a model-select toggle.
      await expect(page.locator('[data-testid="cbc-accuracy-ordinary"]')).toHaveText("59.0%");
      await expect(page.locator('[data-testid="cbc-accuracy-weighted"]')).toHaveText("59.0%");
      await expect(page.locator('[data-testid="cbc-recall-ordinary"]')).toHaveText("Recall = 0.520");
      await expect(page.locator('[data-testid="cbc-recall-weighted"]')).toHaveText("Recall = 0.520");
      await expect(page.locator('[data-testid="cbc-f1-ordinary"]')).toHaveText("F1 = 0.559");

      await expect(page.locator('[data-testid="cbc-confusion-matrix-ordinary"]')).toBeVisible();
      await expect(page.locator('[data-testid="cbc-confusion-matrix-weighted"]')).toBeVisible();

      await expect(page.locator('[data-testid="cbc-plot"] svg.main-svg').first()).toBeVisible();

      // No threshold control of any kind, and no residue of the removed
      // "High Accuracy Can Still Miss the Minority Class" threshold-slider
      // activity anywhere in the DOM.
      await expect(page.locator('input[type="range"]')).toHaveCount(0);
      const bodyText = (await page.locator("#app").innerText()).toLowerCase();
      expect(bodyText).not.toContain("threshold slider");
      expect(bodyText).not.toContain("classification threshold");
      expect(bodyText).not.toContain("high accuracy can still miss");
      for (const testid of [
        "imb-threshold-slider",
        "imb-threshold-number",
        "imb-threshold-value",
        "imb-model-select",
      ]) {
        await expect(page.locator(`[data-testid="${testid}"]`)).toHaveCount(0);
      }

      expect(sockets).toEqual([]);
      expect(failed).toEqual([]);
      expect(consoleErrors, consoleErrors.join("; ")).toEqual([]);
    });

    test("switching to 90:10 updates metrics, confusion matrices, and the chart for both models", async ({
      page,
    }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const beforeRenderCount = await page.locator('[data-testid="cbc-plot"]').getAttribute("data-render-count");

      await page.locator('[data-testid="cbc-ratio-select"]').selectOption("90:10");

      const cohort = await page.locator('[data-testid="cbc-cohort"]').textContent();
      expect(cohort).toMatch(/360 control/);
      expect(cohort).toMatch(/40 autism/);

      await expect(page.locator('[data-testid="cbc-accuracy-ordinary"]')).toHaveText("85.0%");
      await expect(page.locator('[data-testid="cbc-accuracy-weighted"]')).toHaveText("81.0%");
      await expect(page.locator('[data-testid="cbc-recall-ordinary"]')).toHaveText("Recall = 0.100");
      await expect(page.locator('[data-testid="cbc-recall-weighted"]')).toHaveText("Recall = 0.100");
      await expect(page.locator('[data-testid="cbc-f1-ordinary"]')).toHaveText("F1 = 0.118");
      await expect(page.locator('[data-testid="cbc-f1-weighted"]')).toHaveText("F1 = 0.095");

      const cmOrdinary = page.locator('[data-testid="cbc-confusion-matrix-ordinary"]');
      await expect(cmOrdinary.locator('[data-cell="tn"]')).toHaveText("84");
      await expect(cmOrdinary.locator('[data-cell="fp"]')).toHaveText("6");
      await expect(cmOrdinary.locator('[data-cell="fn"]')).toHaveText("9");
      await expect(cmOrdinary.locator('[data-cell="tp"]')).toHaveText("1");

      const cmWeighted = page.locator('[data-testid="cbc-confusion-matrix-weighted"]');
      await expect(cmWeighted.locator('[data-cell="tn"]')).toHaveText("80");
      await expect(cmWeighted.locator('[data-cell="fp"]')).toHaveText("10");
      await expect(cmWeighted.locator('[data-cell="fn"]')).toHaveText("9");
      await expect(cmWeighted.locator('[data-cell="tp"]')).toHaveText("1");

      const afterRenderCount = await page.locator('[data-testid="cbc-plot"]').getAttribute("data-render-count");
      expect(Number(afterRenderCount)).toBeGreaterThan(Number(beforeRenderCount));
    });

    test("switching the chart metric toggles the plotted series without changing the tiles", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const accuracyBefore = await page.locator('[data-testid="cbc-accuracy-ordinary"]').textContent();
      await page.locator('[data-testid="cbc-chart-metric-select"]').selectOption("recall-f1");
      await expect(page.locator("#app")).toHaveAttribute("data-current-chart-metric", "recall-f1");
      const accuracyAfter = await page.locator('[data-testid="cbc-accuracy-ordinary"]').textContent();
      expect(accuracyAfter).toEqual(accuracyBefore);
      await expect(page.locator('[data-testid="cbc-plot"] svg.main-svg').first()).toBeVisible();
    });

    test("majority-class baseline and PR-AUC baseline match the artifact at every balance", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      for (const [ratio, expected] of Object.entries(RATIO_BASELINES)) {
        await page.locator('[data-testid="cbc-ratio-select"]').selectOption(ratio);
        const baseline = await page.locator('[data-testid="cbc-baseline"]').textContent();
        expect(baseline, `ratio ${ratio}`).toContain(expected.majorityBaseline);

        const secondary = await page.locator('[data-testid="cbc-secondary-ordinary"]').textContent();
        expect(secondary, `ratio ${ratio}`).toContain(`baseline = ${expected.prAucBaseline}`);
      }
    });

    test("class weighting is never described as universally better", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const bodyText = (await page.locator("#app").innerText()).toLowerCase();
      expect(bodyText).not.toContain("always better");
      expect(bodyText).not.toContain("strictly better");
      expect(bodyText).not.toContain("universally better");
      expect(bodyText).toContain("not guaranteed to help every metric");
    });

    test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 900 });
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="cbc-plot"]')).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);
    });

    test("browser refresh restores the documented default (50:50)", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await page.locator('[data-testid="cbc-ratio-select"]').selectOption("90:10");

      await page.reload();
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="cbc-ratio-select"]')).toHaveValue("50:50");
    });
  });
}
