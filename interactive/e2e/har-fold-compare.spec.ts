import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `har-fold-compare` activity
// (WP38, Exercise 10: "Random windows or new participants?"), served from
// book/_static/widgets/ at both the site root and the simulated GitHub Pages
// project subpath. The built-Jupyter-Book check is added separately once the
// notebook exists (see e2e-book/).
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/har_fold_compare.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

for (const { name, prefix } of BASES) {
  test.describe(`har-fold-compare @ ${name}`, () => {
    test("loads at the default ordinary / k=5 / Fold 1 combination with both plots rendered", async ({ page }) => {
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

      await expect(page.locator('[data-testid="har-method-ordinary"]')).toHaveAttribute("aria-selected", "true");
      await expect(page.locator('[data-testid="har-k-5"]')).toHaveAttribute("aria-selected", "true");
      await expect(page.locator('[data-testid="har-fold-0"]')).toHaveAttribute("aria-selected", "true");

      await expect(page.locator('[data-testid="har-participant-grid"] > *')).toHaveCount(30);

      await expect(page.locator('[data-testid="har-confusion-plot"] svg.main-svg').first()).toBeVisible();
      await expect(page.locator('[data-testid="har-summary-plot"] svg.main-svg').first()).toBeVisible();

      const overlap = await page.locator('[data-testid="har-overlap-caption"]').innerText();
      expect(overlap).toMatch(/overlap/i);

      expect(sockets).toEqual([]);
      expect(failed).toEqual([]);
      expect(consoleErrors, consoleErrors.join("; ")).toEqual([]);
    });

    test("participant-grouped splitting always reports zero participants split across a fold; ordinary does not", async ({
      page,
    }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const ordinaryStat = await page.locator('[data-testid="har-split-stat"]').innerText();
      expect(ordinaryStat).toMatch(/: 30 of 30\./);

      await page.locator('[data-testid="har-method-grouped"]').click();
      await expect(page.locator("#app")).toHaveAttribute("data-current-method", "grouped");
      const groupedStat = await page.locator('[data-testid="har-split-stat"]').innerText();
      expect(groupedStat).toMatch(/: 0 of 30\./);
    });

    test("choosing a different k and fold updates the reported accuracy/macro-F1", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const before = await page.locator('[data-testid="har-fold-metrics"]').innerText();
      await page.locator('[data-testid="har-k-25"]').click();
      await expect(page.locator("#app")).toHaveAttribute("data-current-k", "25");
      const afterK = await page.locator('[data-testid="har-fold-metrics"]').innerText();
      expect(afterK).not.toEqual(before);
      expect(afterK).toMatch(/k = 25/);

      await page.locator('[data-testid="har-fold-2"]').click();
      await expect(page.locator("#app")).toHaveAttribute("data-current-fold", "2");
      const afterFold = await page.locator('[data-testid="har-fold-metrics"]').innerText();
      expect(afterFold).toMatch(/Fold 3/);
    });

    test("reset returns to the default method, k, and fold", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      await page.locator('[data-testid="har-method-grouped"]').click();
      await page.locator('[data-testid="har-k-25"]').click();
      await page.locator('[data-testid="har-fold-3"]').click();

      await page.locator('[data-testid="har-reset-button"]').click();
      await expect(page.locator("#app")).toHaveAttribute("data-current-method", "ordinary");
      await expect(page.locator("#app")).toHaveAttribute("data-current-k", "5");
      await expect(page.locator("#app")).toHaveAttribute("data-current-fold", "0");
    });

    test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 900 });
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="har-confusion-plot"]')).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);
    });
  });
}
