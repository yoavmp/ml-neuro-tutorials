import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `boosting-step-by-step`
// activity ("Build a Boosted Model"), served from book/_static/widgets/. The
// built-Jupyter-Book check lives in ../e2e-book/chapter07.spec.ts.
const QUERY = "?config=../configs/boosting_step_by_step.json";

function appUrl(query = ""): string {
  return `/app/index.html${query}`;
}

test.describe("boosting-step-by-step", () => {
  test("loads at stage 0 with the default learning rate", async ({ page }) => {
    const failed: string[] = [];
    page.on("requestfailed", (r) => failed.push(r.url()));

    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(page.locator('[data-testid="boosting-step-observation-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );
    await expect(page.locator('[data-testid="boosting-step-mse-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );

    const app = page.locator("#app");
    await expect(app).toHaveAttribute("data-stage-index", "0");
    await expect(page.locator('[data-testid="boosting-step-stage-label"]')).toContainText("training-target mean");
    await expect(page.locator('[data-testid="boosting-step-prev-button"]')).toBeDisabled();

    expect(failed, `unexpected network failures: ${failed.join(", ")}`).toHaveLength(0);
  });

  test("Next Step advances the stage and updates the plots/metrics", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const before = await page.locator('[data-testid="boosting-step-stage-label"]').innerText();
    await page.locator('[data-testid="boosting-step-next-button"]').click();

    await expect(page.locator("#app")).toHaveAttribute("data-stage-index", "1");
    const after = await page.locator('[data-testid="boosting-step-stage-label"]').innerText();
    expect(after).not.toEqual(before);
    await expect(page.locator('[data-testid="boosting-step-prev-button"]')).toBeEnabled();
  });

  test("Previous Step is disabled at stage 0 and Next Step is disabled at the final stage", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const slider = page.locator('[data-testid="boosting-step-stage-slider"]');
    const max = await slider.getAttribute("max");
    await slider.fill(max!);
    await slider.dispatchEvent("change");

    await expect(page.locator("#app")).toHaveAttribute("data-stage-index", max!);
    await expect(page.locator('[data-testid="boosting-step-next-button"]')).toBeDisabled();
    await expect(page.locator('[data-testid="boosting-step-prev-button"]')).toBeEnabled();
  });

  test("changing the learning rate changes the training MSE at the same stage", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await page.locator('[data-testid="boosting-step-next-button"]').click();
    const mseBefore = await page.locator("#app").getAttribute("data-train-mse");

    await page.locator('[data-testid="boosting-step-lr-select"]').selectOption("1");
    await expect(page.locator("#app")).toHaveAttribute("data-learning-rate", "1");
    const mseAfter = await page.locator("#app").getAttribute("data-train-mse");
    expect(mseAfter).not.toEqual(mseBefore);
  });

  test("the scaled-correction toggle changes the residual plot", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await page.locator('[data-testid="boosting-step-next-button"]').click();

    const before = await page.evaluate(() => {
      const el = document.querySelector('[data-testid="boosting-step-residual-plot"]') as HTMLElement & {
        data?: { name?: string }[];
      };
      return el.data?.map((t) => t.name);
    });

    await page.locator('[data-testid="boosting-step-scaled-toggle"]').check();
    await expect(page.locator('[data-testid="boosting-step-residual-plot"]')).toHaveAttribute(
      "data-render-count",
      /[2-9]/,
    );
    const after = await page.evaluate(() => {
      const el = document.querySelector('[data-testid="boosting-step-residual-plot"]') as HTMLElement & {
        data?: { name?: string }[];
      };
      return el.data?.map((t) => t.name);
    });
    expect(after).not.toEqual(before);
  });

  test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(page.locator('[data-testid="boosting-step-observation-plot"]')).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("shows the error panel when pointed at a nonexistent config", async ({ page }) => {
    await page.goto(appUrl("?config=../configs/boosting_step_by_step_missing.json"));
    await expect(page.locator('[data-testid="widget-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="widget-error-message"]')).toContainText("HTTP 404");
  });
});
