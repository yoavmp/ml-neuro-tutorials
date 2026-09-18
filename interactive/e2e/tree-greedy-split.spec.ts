import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `tree-greedy-split` activity
// ("Build a Tree Greedily"), served from book/_static/widgets/. The
// built-Jupyter-Book check lives in ../e2e-book/chapter06.spec.ts.
const QUERY = "?config=../configs/tree_greedy_split.json";

function appUrl(query = ""): string {
  return `/app/index.html${query}`;
}

test.describe("tree-greedy-split", () => {
  test("loads at the root node with no optimum revealed", async ({ page }) => {
    const failed: string[] = [];
    page.on("requestfailed", (r) => failed.push(r.url()));

    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(page.locator('[data-testid="tree-greedy-feature-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );
    await expect(page.locator('[data-testid="tree-greedy-mse-plot"]')).toHaveAttribute("data-render-count", /[1-9]/);

    const app = page.locator("#app");
    await expect(app).toHaveAttribute("data-round-id", "root");
    await expect(page.locator('[data-testid="tree-greedy-reveal-panel"]')).toBeHidden();
    await expect(page.locator('[data-testid="tree-greedy-reveal-button"]')).toBeDisabled();
    await expect(page.locator('[data-testid="tree-greedy-continue-button"]')).toBeDisabled();

    expect(failed, `unexpected network failures: ${failed.join(", ")}`).toHaveLength(0);
  });

  test("switching feature and threshold updates the score card without revealing the optimum", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const before = await page.locator('[data-testid="tree-greedy-scorecard"]').innerText();

    await page.locator('[data-testid="tree-greedy-feature-select"]').selectOption("x2");
    const afterFeature = await page.locator('[data-testid="tree-greedy-scorecard"]').innerText();
    expect(afterFeature).not.toEqual(before);

    const thresholdSelect = page.locator('[data-testid="tree-greedy-threshold-select"]');
    const optionCount = await thresholdSelect.locator("option").count();
    expect(optionCount).toBeGreaterThan(1);
    await thresholdSelect.selectOption({ index: optionCount - 1 });
    const afterThreshold = await page.locator('[data-testid="tree-greedy-scorecard"]').innerText();
    expect(afterThreshold).not.toEqual(afterFeature);

    // No pre-reveal leakage: the reveal panel (the only place this round's
    // optimal feature/threshold/MSE would appear) stays hidden and empty.
    const revealPanel = page.locator('[data-testid="tree-greedy-reveal-panel"]');
    await expect(revealPanel).toBeHidden();
    expect(await revealPanel.innerText()).toBe("");
  });

  test("lock, reveal, and continue progress through all three rounds", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    for (let round = 0; round < 3; round++) {
      await expect(page.locator("#app")).toHaveAttribute("data-round-index", String(round));

      await page.locator('[data-testid="tree-greedy-lock-button"]').click();
      await expect(page.locator('[data-testid="tree-greedy-feature-select"]')).toBeDisabled();

      await page.locator('[data-testid="tree-greedy-reveal-button"]').click();
      await expect(page.locator('[data-testid="tree-greedy-reveal-panel"]')).toBeVisible();
      const revealText = await page.locator('[data-testid="tree-greedy-reveal-panel"]').innerText();
      expect(revealText).toContain("Greedy optimum");

      await page.locator('[data-testid="tree-greedy-continue-button"]').click();
    }

    await expect(page.locator("#app")).toHaveAttribute("data-round-index", "2");
    await expect(page.locator('[data-testid="tree-greedy-continue-button"]')).toBeDisabled();
  });

  test("reset returns to the root node with no accepted splits", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await page.locator('[data-testid="tree-greedy-lock-button"]').click();
    await page.locator('[data-testid="tree-greedy-reveal-button"]').click();
    await page.locator('[data-testid="tree-greedy-continue-button"]').click();
    await expect(page.locator("#app")).toHaveAttribute("data-round-index", "1");

    await page.locator('[data-testid="tree-greedy-reset-button"]').click();
    await expect(page.locator("#app")).toHaveAttribute("data-round-index", "0");
    await expect(page.locator('[data-testid="tree-greedy-reveal-panel"]')).toBeHidden();
    await expect(page.locator('[data-testid="tree-greedy-feature-select"]')).toBeEnabled();
  });

  test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(page.locator('[data-testid="tree-greedy-feature-plot"]')).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("shows the error panel when pointed at a nonexistent config", async ({ page }) => {
    await page.goto(appUrl("?config=../configs/tree_greedy_split_missing.json"));
    await expect(page.locator('[data-testid="widget-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="widget-error-message"]')).toContainText("HTTP 404");
  });
});
