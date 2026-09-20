import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `boosting-parameter-explorer`
// activity ("Explore the Boosting Parameters"), served from
// book/_static/widgets/. The built-Jupyter-Book check lives in
// ../e2e-book/chapter07.spec.ts.
const QUERY = "?config=../configs/boosting_parameter_explorer.json";

function appUrl(query = ""): string {
  return `/app/index.html${query}`;
}

test.describe("boosting-parameter-explorer", () => {
  test("loads with the declared defaults and no locked-test data in view", async ({ page }) => {
    const failed: string[] = [];
    page.on("requestfailed", (r) => failed.push(r.url()));

    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(page.locator('[data-testid="boosting-param-mse-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );
    await expect(page.locator('[data-testid="boosting-param-heatmap-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );
    await expect(page.locator('[data-testid="boosting-param-prediction-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );

    const app = page.locator("#app");
    await expect(app).toHaveAttribute("data-learning-rate", "0.1");
    await expect(app).toHaveAttribute("data-depth", "2");
    await expect(app).toHaveAttribute("data-n-trees", "100");
    await expect(app).toHaveAttribute("data-playing", "false");
    await expect(page.locator('[data-testid="boosting-param-play-button"]')).toHaveText("Play");

    // The widget's own framing text legitimately says the test set is locked
    // (config.testSetNote) -- what must never appear is actual test-set data.
    // The data schema structurally excludes it (no field could carry it; see
    // boosting-parameter-explorer-data.ts and the "test set absent from
    // widget data" Python test), so this only re-checks the framing copy.
    const bodyText = await page.locator("#app").innerText();
    expect(bodyText).toContain("development data only");
    expect(bodyText.toLowerCase()).toContain("test set remains unavailable");

    expect(failed, `unexpected network failures: ${failed.join(", ")}`).toHaveLength(0);
  });

  test("changing a control updates the metrics and the plots", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const before = await page.locator('[data-testid="boosting-param-metrics"]').innerText();
    await page.locator('[data-testid="boosting-param-depth-select"]').selectOption("3");
    await expect(page.locator("#app")).toHaveAttribute("data-depth", "3");
    const after = await page.locator('[data-testid="boosting-param-metrics"]').innerText();
    expect(after).not.toEqual(before);
  });

  test("Play advances through the committed tree-count grid and updates state at every step", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const app = page.locator("#app");
    await expect(app).toHaveAttribute("data-n-trees", "100");

    await page.locator('[data-testid="boosting-param-play-button"]').click();
    await expect(app).toHaveAttribute("data-playing", "true");
    await expect(page.locator('[data-testid="boosting-param-play-button"]')).toHaveText("Pause");

    // Wait (via polling, not a fixed sleep) for at least one advance past the default.
    await expect(app).not.toHaveAttribute("data-n-trees", "100", { timeout: 5000 });
    const advanced = await app.getAttribute("data-n-trees");
    expect(Number(advanced)).toBeGreaterThan(100);
  });

  test("Pause stops advancement at the current point", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const app = page.locator("#app");
    await page.locator('[data-testid="boosting-param-play-button"]').click();
    await expect(app).not.toHaveAttribute("data-n-trees", "100", { timeout: 5000 });

    await page.locator('[data-testid="boosting-param-play-button"]').click();
    await expect(app).toHaveAttribute("data-playing", "false");
    const paused = await app.getAttribute("data-n-trees");

    // A short, bounded wait (well under the configured 600ms interval x 2)
    // to confirm the paused value genuinely stops changing, per WP32 §20:
    // event/state observation rather than a long real-time animation wait.
    await page.waitForTimeout(700);
    await expect(app).toHaveAttribute("data-n-trees", paused!);
  });

  test("changing any control pauses playback before applying the new value", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const app = page.locator("#app");
    await page.locator('[data-testid="boosting-param-play-button"]').click();
    await expect(app).toHaveAttribute("data-playing", "true");

    await page.locator('[data-testid="boosting-param-lr-select"]').selectOption("0.5");
    await expect(app).toHaveAttribute("data-playing", "false");
    await expect(page.locator('[data-testid="boosting-param-play-button"]')).toHaveText("Play");
  });

  test("Play stops automatically at the final tree count and restores the Play label", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const app = page.locator("#app");
    const slider = page.locator('[data-testid="boosting-param-ntrees-slider"]');
    const maxIndex = await slider.getAttribute("max");
    await slider.fill(String(Number(maxIndex) - 1));
    await slider.dispatchEvent("input");

    await page.locator('[data-testid="boosting-param-play-button"]').click();
    await expect(app).toHaveAttribute("data-n-trees", "300", { timeout: 5000 });
    await expect(app).toHaveAttribute("data-playing", "false");
    await expect(page.locator('[data-testid="boosting-param-play-button"]')).toHaveText("Play");
  });

  test("Reset stops playback and restores the declared defaults", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const app = page.locator("#app");
    await page.locator('[data-testid="boosting-param-depth-select"]').selectOption("1");
    await page.locator('[data-testid="boosting-param-play-button"]').click();
    await expect(app).toHaveAttribute("data-playing", "true");

    await page.locator('[data-testid="boosting-param-reset-button"]').click();
    await expect(app).toHaveAttribute("data-playing", "false");
    await expect(app).toHaveAttribute("data-learning-rate", "0.1");
    await expect(app).toHaveAttribute("data-depth", "2");
    await expect(app).toHaveAttribute("data-n-trees", "100");
  });

  test("no orphan timer keeps running after the page reloads mid-playback", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(String(e)));

    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await page.locator('[data-testid="boosting-param-play-button"]').click();
    await expect(page.locator("#app")).toHaveAttribute("data-playing", "true");

    await page.reload();
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(page.locator("#app")).toHaveAttribute("data-playing", "false");

    // Give any orphaned interval from the destroyed instance a chance to fire
    // and throw against a torn-down DOM before asserting none did.
    await page.waitForTimeout(700);
    expect(errors, `unexpected page errors: ${errors.join(", ")}`).toHaveLength(0);
  });

  test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(page.locator('[data-testid="boosting-param-heatmap-plot"]')).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("shows the error panel when pointed at a nonexistent config", async ({ page }) => {
    await page.goto(appUrl("?config=../configs/boosting_parameter_explorer_missing.json"));
    await expect(page.locator('[data-testid="widget-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="widget-error-message"]')).toContainText("HTTP 404");
  });
});
