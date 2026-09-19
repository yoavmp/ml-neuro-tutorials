import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `validation-stability`
// activity (WP27, Exercise 4's "One Split or Several Folds?"). The
// built-Jupyter-Book check lives in ../e2e-book/chapter04.spec.ts and the
// dark-mode check in ../e2e-book/wp22-cross-chapter-dark-mode.spec.ts.
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/validation_stability.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

for (const { name, prefix } of BASES) {
  test.describe(`validation-stability @ ${name}`, () => {
    test("loads with deterministic defaults: N=100, seed=0, 5 folds, both plots rendered", async ({
      page,
    }) => {
      const consoleErrors: string[] = [];
      const sockets: string[] = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") consoleErrors.push(msg.text());
      });
      page.on("websocket", (ws) => sockets.push(ws.url()));

      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const container = page.locator("#app");
      await expect(container).toHaveAttribute("data-size-key", "100");
      await expect(container).toHaveAttribute("data-seed", "0");
      await expect(container).toHaveAttribute("data-folds", "5");

      await expect(page.locator('[data-testid="validation-stability-size-100"]')).toHaveAttribute(
        "aria-selected",
        "true",
      );
      await expect(page.locator('[data-testid="validation-stability-seed-0"]')).toBeChecked();
      await expect(page.locator('[data-testid="validation-stability-folds-5"]')).toBeChecked();

      await expect(page.locator('[data-testid="validation-stability-single-plot"]')).toHaveAttribute(
        "data-render-count",
        /[1-9]/,
      );
      await expect(page.locator('[data-testid="validation-stability-cv-plot"]')).toHaveAttribute(
        "data-render-count",
        /[1-9]/,
      );

      const summary = await page.locator('[data-testid="validation-stability-summary"]').innerText();
      expect(summary).toMatch(/Sample size 100, seed 0/);

      expect(sockets).toEqual([]);
      expect(consoleErrors, consoleErrors.join("; ")).toEqual([]);
    });

    test("changing sample size updates the summary, plots, and small-N note", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      // at N=100 the small-N note is hidden (not one of the audited unstable sizes)
      await expect(page.locator('[data-testid="validation-stability-small-n-note"]')).toBeHidden();

      const beforeSummary = await page.locator('[data-testid="validation-stability-summary"]').innerText();
      await page.locator('[data-testid="validation-stability-size-30"]').click();
      await expect(page.locator("#app")).toHaveAttribute("data-size-key", "30");
      const afterSummary = await page.locator('[data-testid="validation-stability-summary"]').innerText();
      expect(afterSummary).not.toEqual(beforeSummary);
      expect(afterSummary).toMatch(/Sample size 30/);

      // N=30 is one of the audited sizes with meaningful instability
      await expect(page.locator('[data-testid="validation-stability-small-n-note"]')).toBeVisible();
    });

    test("changing the seed re-partitions the same sample size (partition instability), not the sample", async ({
      page,
    }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await page.locator('[data-testid="validation-stability-size-30"]').click();

      const beforeSummary = await page.locator('[data-testid="validation-stability-summary"]').innerText();
      await page.locator('[data-testid="validation-stability-seed-2"]').check();
      await expect(page.locator("#app")).toHaveAttribute("data-seed", "2");
      const afterSummary = await page.locator('[data-testid="validation-stability-summary"]').innerText();
      expect(afterSummary).not.toEqual(beforeSummary);
      // sample size label is unchanged -- only the partition (seed) changed
      expect(afterSummary).toMatch(/Sample size 30/);
    });

    test("changing the fold count redraws the cross-validation plot with new fold statistics", async ({
      page,
    }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const cvPlot = page.locator('[data-testid="validation-stability-cv-plot"]');
      const beforeRender = Number(await cvPlot.getAttribute("data-render-count"));
      await page.locator('[data-testid="validation-stability-folds-10"]').check();
      await expect(page.locator("#app")).toHaveAttribute("data-folds", "10");
      const afterRender = Number(await cvPlot.getAttribute("data-render-count"));
      expect(afterRender).toBeGreaterThan(beforeRender);
    });

    test("N=30 with 10 folds is flagged invalid rather than silently computed", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await page.locator('[data-testid="validation-stability-size-30"]').click();
      await page.locator('[data-testid="validation-stability-folds-10"]').check();

      await expect(page.locator('[data-testid="validation-stability-cv-empty"]')).toBeVisible();
      const text = await page.locator('[data-testid="validation-stability-cv-empty"]').innerText();
      expect(text.length).toBeGreaterThan(0);
    });

    test("browser refresh restores the configured defaults", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await page.locator('[data-testid="validation-stability-size-500"]').click();
      await expect(page.locator("#app")).toHaveAttribute("data-size-key", "500");

      await page.reload();
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator("#app")).toHaveAttribute("data-size-key", "100");
    });

    test("shows the error panel when pointed at a nonexistent config", async ({ page }) => {
      await page.goto(appUrl(prefix, "?config=../configs/validation_stability_missing.json"));
      await expect(page.locator('[data-testid="widget-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="widget-error-message"]')).toContainText("HTTP 404");
    });

    test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({
      page,
    }) => {
      await page.setViewportSize({ width: 390, height: 900 });
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="validation-stability-single-plot"]')).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);
    });
  });
}
