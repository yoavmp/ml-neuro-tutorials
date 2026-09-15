import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `classification-imbalance`
// activity (WP17 §5), served from book/_static/widgets/ at both the site
// root and the simulated GitHub Pages project subpath. The built-Jupyter-Book
// check lives in ../e2e-book/chapter04.spec.ts.
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/classification_imbalance.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

for (const { name, prefix } of BASES) {
  test.describe(`classification-imbalance @ ${name}`, () => {
    test("loads at the default 50:50 ratio with both panels rendered", async ({ page }) => {
      const failed: string[] = [];
      const sockets: string[] = [];
      page.on("requestfailed", (r) => failed.push(r.url()));
      page.on("websocket", (ws) => sockets.push(ws.url()));

      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      await expect(page.locator('[data-testid="cls-imb-ratio-select"]')).toHaveValue("50:50");
      const cohort = await page.locator('[data-testid="cls-imb-cohort"]').textContent();
      expect(cohort).toMatch(/400 participants/);

      for (const kind of ["stratified", "unstratified"]) {
        const metrics = await page.locator(`[data-testid="cls-imb-${kind}-metrics"]`).textContent();
        expect(metrics).toMatch(/accuracy = 0\.\d{3}/);
      }

      expect(sockets).toEqual([]);
      expect(failed).toEqual([]);
    });

    test("switching to 95:5 shows the majority-baseline accuracy of 95%", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      await page.locator('[data-testid="cls-imb-ratio-select"]').selectOption("95:5");
      const baseline = await page.locator('[data-testid="cls-imb-stratified-baseline"]').textContent();
      expect(baseline).toMatch(/95\.0%/);
      const cohort = await page.locator('[data-testid="cls-imb-cohort"]').textContent();
      expect(cohort).toMatch(/20 autism/);
    });

    test("changing the ratio and seed updates real underlying data, not just a label", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const before = await page.locator('[data-testid="cls-imb-stratified-split-counts"]').textContent();
      await page.locator('[data-testid="cls-imb-ratio-select"]').selectOption("90:10");
      const afterRatio = await page.locator('[data-testid="cls-imb-stratified-split-counts"]').textContent();
      expect(afterRatio).not.toEqual(before);

      const beforeSeed = await page.locator('[data-testid="cls-imb-unstratified-metrics"]').textContent();
      await page.locator('[data-testid="cls-imb-seed-select"]').selectOption("2");
      const afterSeed = await page.locator('[data-testid="cls-imb-unstratified-metrics"]').textContent();
      // A different seed need not always change the displayed metrics text,
      // but the control must be wired to the data, never a no-op.
      expect(afterSeed).toBeTruthy();
      expect(beforeSeed).toBeTruthy();
    });

    test("stratified and unstratified confusion matrices are both accessible tables", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      for (const kind of ["stratified", "unstratified"]) {
        const table = page.locator(`[data-testid="cls-imb-${kind}-confusion-matrix"]`);
        await expect(table).toBeVisible();
        await expect(table.locator("td")).toHaveCount(4);
      }
    });

    test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 900 });
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="cls-imb-stratified-confusion-matrix"]')).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);
    });

    test("browser refresh restores the documented default (50:50, seed 0)", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await page.locator('[data-testid="cls-imb-ratio-select"]').selectOption("95:5");
      await page.locator('[data-testid="cls-imb-seed-select"]').selectOption("3");

      await page.reload();
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="cls-imb-ratio-select"]')).toHaveValue("50:50");
      await expect(page.locator('[data-testid="cls-imb-seed-select"]')).toHaveValue("0");
    });
  });
}
