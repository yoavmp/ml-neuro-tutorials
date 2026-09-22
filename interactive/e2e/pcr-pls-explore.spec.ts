import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `pcr-pls-explore` activity
// ("PCR or PLS?"), served from book/_static/widgets/. The built-Jupyter-Book
// check lives in ../e2e-book/chapter09.spec.ts.
const QUERY = "?config=../configs/pcr_pls_explore.json";

function appUrl(query = ""): string {
  return `/app/index.html${query}`;
}

test.describe("pcr-pls-explore", () => {
  test("loads with the configured defaults and both panels rendered", async ({ page }) => {
    const failed: string[] = [];
    page.on("requestfailed", (r) => failed.push(r.url()));

    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const app = page.locator("#app");
    await expect(app).toHaveAttribute("data-method", "pcr");
    await expect(app).toHaveAttribute("data-n-components", "1");
    await expect(app).toHaveAttribute("data-preset", "moderate");

    for (const testId of ["pcr-pls-cloud-plot", "pcr-pls-pred-plot"]) {
      await expect(page.locator(`[data-testid="${testId}"]`)).toHaveAttribute("data-render-count", /[1-9]/);
    }

    expect(failed, `unexpected network failures: ${failed.join(", ")}`).toHaveLength(0);
  });

  test("switching from PCR to PLS changes the reported validation MSE", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await page.locator('[data-testid="pcr-pls-preset-select"]').selectOption("strong");
    await expect(page.locator("#app")).toHaveAttribute("data-preset", "strong");
    const pcrValMse = await page.locator("#app").getAttribute("data-val-mse");

    await page.locator('[data-testid="pcr-pls-method-select"]').selectOption("pls");
    await expect(page.locator("#app")).toHaveAttribute("data-method", "pls");
    const plsValMse = await page.locator("#app").getAttribute("data-val-mse");

    expect(plsValMse).not.toEqual(pcrValMse);
  });

  test("PCR and PLS converge once both components are retained", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await page.locator('[data-testid="pcr-pls-preset-select"]').selectOption("strong");
    await page.locator('[data-testid="pcr-pls-ncomponents-select"]').selectOption("2");
    await page.locator('[data-testid="pcr-pls-method-select"]').selectOption("pcr");
    const pcrValMse = await page.locator("#app").getAttribute("data-val-mse");

    await page.locator('[data-testid="pcr-pls-method-select"]').selectOption("pls");
    const plsValMse = await page.locator("#app").getAttribute("data-val-mse");

    expect(plsValMse).toEqual(pcrValMse);
  });

  test("the predictor cloud's own point positions stay fixed across every control change", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const readCloudX = () =>
      page.evaluate(() => {
        const el = document.querySelector('[data-testid="pcr-pls-cloud-plot"]') as HTMLElement & { data?: { x?: number[] }[] };
        return el.data?.[0]?.x ?? null;
      });

    const before = await readCloudX();
    await page.locator('[data-testid="pcr-pls-preset-select"]').selectOption("strong");
    await expect(page.locator('[data-testid="pcr-pls-cloud-plot"]')).toHaveAttribute("data-render-count", /[2-9]/);
    const after = await readCloudX();

    expect(after).toEqual(before);
  });

  test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(page.locator('[data-testid="pcr-pls-cloud-plot"]')).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("shows the error panel when pointed at a nonexistent config", async ({ page }) => {
    await page.goto(appUrl("?config=../configs/pcr_pls_explore_missing.json"));
    await expect(page.locator('[data-testid="widget-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="widget-error-message"]')).toContainText("HTTP 404");
  });
});
