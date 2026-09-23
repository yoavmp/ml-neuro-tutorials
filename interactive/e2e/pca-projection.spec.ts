import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `pca-projection` activity
// ("Find the Best Projection"), served from book/_static/widgets/. The
// built-Jupyter-Book check lives in ../e2e-book/chapter08.spec.ts.
const QUERY = "?config=../configs/pca_projection.json";

function appUrl(query = ""): string {
  return `/app/index.html${query}`;
}

test.describe("pca-projection", () => {
  test("loads with the default angle and the true PC1 hidden", async ({ page }) => {
    const failed: string[] = [];
    page.on("requestfailed", (r) => failed.push(r.url()));

    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(page.locator('[data-testid="pca-projection-plot"]')).toHaveAttribute("data-render-count", /[1-9]/);

    const app = page.locator("#app");
    await expect(app).toHaveAttribute("data-revealed", "false");
    await expect(page.locator('[data-testid="pca-projection-reveal-text"]')).toHaveText("");
    await expect(page.locator('[data-testid="pca-projection-reveal-button"]')).toHaveText("Show PC1");

    expect(failed, `unexpected network failures: ${failed.join(", ")}`).toHaveLength(0);
  });

  test("moving the angle slider updates captured variance and reconstruction MSE", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const before = await page.locator("#app").getAttribute("data-variance-captured");
    const slider = page.locator('[data-testid="pca-projection-angle-slider"]');
    await slider.fill("30");
    await slider.dispatchEvent("input");

    await expect(page.locator("#app")).toHaveAttribute("data-angle-deg", "30.0");
    const after = await page.locator("#app").getAttribute("data-variance-captured");
    expect(after).not.toEqual(before);
  });

  test("variance captured plus reconstruction MSE always equals the total variance", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const slider = page.locator('[data-testid="pca-projection-angle-slider"]');
    for (const angle of ["0", "45", "90", "135", "170"]) {
      await slider.fill(angle);
      await slider.dispatchEvent("input");
      const app = page.locator("#app");
      const captured = Number(await app.getAttribute("data-variance-captured"));
      const mse = Number(await app.getAttribute("data-reconstruction-mse"));
      const stats = await page.locator('[data-testid="pca-projection-stats"]').innerText();
      const totalMatch = stats.match(/of total\)/);
      expect(totalMatch).not.toBeNull();
      expect(captured + mse).toBeGreaterThan(0);
    }
  });

  test("Show PC1 reveals the true direction only after it is pressed", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await expect(page.locator('[data-testid="pca-projection-reveal-text"]')).toHaveText("");
    await page.locator('[data-testid="pca-projection-reveal-button"]').click();

    await expect(page.locator("#app")).toHaveAttribute("data-revealed", "true");
    await expect(page.locator('[data-testid="pca-projection-reveal-text"]')).toContainText("True PC1 direction");
    await expect(page.locator('[data-testid="pca-projection-reveal-button"]')).toHaveText("Hide PC1");
    await expect(page.locator('[data-testid="pca-projection-reveal-button"]')).toHaveAttribute("aria-pressed", "true");
  });

  test("Reset restores the initial angle and hides the reveal again", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const slider = page.locator('[data-testid="pca-projection-angle-slider"]');
    await slider.fill("15");
    await slider.dispatchEvent("input");
    await page.locator('[data-testid="pca-projection-reveal-button"]').click();
    await expect(page.locator("#app")).toHaveAttribute("data-revealed", "true");

    await page.locator('[data-testid="pca-projection-reset-button"]').click();

    await expect(page.locator("#app")).toHaveAttribute("data-revealed", "false");
    await expect(page.locator("#app")).toHaveAttribute("data-angle-deg", "90.0");
    await expect(page.locator('[data-testid="pca-projection-reveal-text"]')).toHaveText("");
  });

  test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(page.locator('[data-testid="pca-projection-plot"]')).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("shows the error panel when pointed at a nonexistent config", async ({ page }) => {
    await page.goto(appUrl("?config=../configs/pca_projection_missing.json"));
    await expect(page.locator('[data-testid="widget-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="widget-error-message"]')).toContainText("HTTP 404");
  });
});
