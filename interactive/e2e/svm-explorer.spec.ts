import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `svm-explorer` activity
// ("Explore an SVM Boundary"), served from book/_static/widgets/. The
// built-Jupyter-Book check lives in ../e2e-book/chapter09.spec.ts.
const QUERY = "?config=../configs/svm_explorer.json";

function appUrl(query = ""): string {
  return `/app/index.html${query}`;
}

test.describe("svm-explorer", () => {
  test("loads with the configured defaults and the plot rendered", async ({ page }) => {
    const failed: string[] = [];
    page.on("requestfailed", (r) => failed.push(r.url()));

    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const app = page.locator("#app");
    await expect(app).toHaveAttribute("data-dataset", "linear");
    await expect(app).toHaveAttribute("data-kernel", "linear");
    await expect(app).toHaveAttribute("data-c", "1");

    await expect(page.locator('[data-testid="svm-explorer-plot"]')).toHaveAttribute("data-render-count", /[1-9]/);
    expect(failed, `unexpected network failures: ${failed.join(", ")}`).toHaveLength(0);
  });

  test("gamma is disabled for the linear kernel and enabled otherwise", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await expect(page.locator('[data-testid="svm-explorer-gamma-select"]')).toBeDisabled();
    await expect(page.locator('[data-testid="svm-explorer-gamma-irrelevant-note"]')).toBeVisible();

    await page.locator('[data-testid="svm-explorer-kernel-select"]').selectOption("rbf");
    await expect(page.locator("#app")).toHaveAttribute("data-kernel", "rbf");
    await expect(page.locator('[data-testid="svm-explorer-gamma-select"]')).toBeEnabled();
    await expect(page.locator('[data-testid="svm-explorer-gamma-irrelevant-note"]')).toBeHidden();
  });

  test("switching to the nonlinear dataset with a linear kernel lowers validation accuracy", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const linearAcc = Number(await page.locator("#app").getAttribute("data-val-accuracy"));
    await page.locator('[data-testid="svm-explorer-dataset-select"]').selectOption("nonlinear");
    await expect(page.locator("#app")).toHaveAttribute("data-dataset", "nonlinear");
    const nonlinearAcc = Number(await page.locator("#app").getAttribute("data-val-accuracy"));

    expect(nonlinearAcc).toBeLessThan(linearAcc);
  });

  test("changing C updates the support-vector count", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const before = await page.locator("#app").getAttribute("data-n-support-vectors");
    await page.locator('[data-testid="svm-explorer-c-select"]').selectOption("0.1");
    await expect(page.locator("#app")).toHaveAttribute("data-c", "0.1");
    const after = await page.locator("#app").getAttribute("data-n-support-vectors");

    expect(after).not.toEqual(before);
  });

  test("Reset restores the configured defaults after several control changes", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await page.locator('[data-testid="svm-explorer-dataset-select"]').selectOption("nonlinear");
    await page.locator('[data-testid="svm-explorer-kernel-select"]').selectOption("rbf");
    await page.locator('[data-testid="svm-explorer-c-select"]').selectOption("100");
    await expect(page.locator("#app")).toHaveAttribute("data-kernel", "rbf");

    await page.locator('[data-testid="svm-explorer-reset-button"]').click();
    await expect(page.locator("#app")).toHaveAttribute("data-dataset", "linear");
    await expect(page.locator("#app")).toHaveAttribute("data-kernel", "linear");
    await expect(page.locator("#app")).toHaveAttribute("data-c", "1");
  });

  test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(page.locator('[data-testid="svm-explorer-plot"]')).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("shows the error panel when pointed at a nonexistent config", async ({ page }) => {
    await page.goto(appUrl("?config=../configs/svm_explorer_missing.json"));
    await expect(page.locator('[data-testid="widget-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="widget-error-message"]')).toContainText("HTTP 404");
  });
});
