import { expect, test, type Frame } from "@playwright/test";

// Proof that both embedded Exercise 4 activities work on the *final built
// Exercise 4 HTML page*, served beneath the simulated GitHub Pages project
// subpath -- not just the standalone widget page.

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html";
const THRESHOLD_IFRAME_SELECTOR =
  'iframe[title="Interactive decision-threshold exploration for classifying autism vs. control from brain structure"]';
const IMBALANCE_IFRAME_SELECTOR =
  'iframe[title="Interactive class-imbalance exploration for classifying autism vs. control from brain structure"]';

async function frameFor(page: import("@playwright/test").Page, selector: string): Promise<Frame> {
  const handle = await page.locator(selector).elementHandle();
  expect(handle, "iframe element present").not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, "iframe content frame present").not.toBeNull();
  return frame!;
}

test.describe("Chapter 4 built page — embedded decision-threshold activity", () => {
  test("iframe loads, config+data are 200, ROC plot renders at the default threshold", async ({
    page,
  }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const iframe = page.locator(THRESHOLD_IFRAME_SELECTOR);
    await expect(iframe).toHaveCount(1);
    await iframe.scrollIntoViewIfNeeded();

    const frame = await frameFor(page, THRESHOLD_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/classification_threshold.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/abide_classification_threshold.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    await expect(frame.locator('[data-testid="cls-threshold-slider"]')).toHaveValue("0.5");
    await expect(frame.locator('[data-testid="cls-roc-plot"]')).toHaveAttribute("data-render-count", /[1-9]/);

    const metrics = await frame.locator('[data-testid="cls-metrics"]').innerText();
    expect(metrics).toMatch(/threshold = 0\.50/);
    expect(metrics).toMatch(/AUC \(fixed, threshold-independent\) = 0\.593/);
  });

  test("moving the threshold changes the confusion matrix and metrics, but never the AUC", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    await page.locator(THRESHOLD_IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    const frame = await frameFor(page, THRESHOLD_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const beforeMetrics = await frame.locator('[data-testid="cls-metrics"]').innerText();
    const beforeTp = await frame.locator('[data-testid="cls-cm-tp"]').innerText();

    await frame.locator('[data-testid="cls-threshold-slider"]').fill("0.9");
    await frame.locator('[data-testid="cls-threshold-slider"]').dispatchEvent("change");

    const afterMetrics = await frame.locator('[data-testid="cls-metrics"]').innerText();
    const afterTp = await frame.locator('[data-testid="cls-cm-tp"]').innerText();
    expect(afterMetrics).not.toEqual(beforeMetrics);
    expect(afterTp).not.toEqual(beforeTp);
    expect(afterMetrics).toMatch(/AUC \(fixed, threshold-independent\) = 0\.593/);

    // reset control restores the default
    await frame.locator('[data-testid="cls-threshold-reset"]').click();
    await expect(frame.locator('[data-testid="cls-threshold-value"]')).toHaveText("0.50");
  });

  test("embedded threshold activity is usable at a narrow viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(CHAPTER_URL);
    await page.locator(THRESHOLD_IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    const frame = await frameFor(page, THRESHOLD_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(frame.locator('[data-testid="cls-roc-plot"]')).toBeVisible();
    const overflow = await frame.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });
});

test.describe("Chapter 4 built page — embedded class-imbalance activity", () => {
  test("iframe loads, config+data are 200, the accuracy-comparison chart renders at 95:5", async ({ page }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const iframe = page.locator(IMBALANCE_IFRAME_SELECTOR);
    await expect(iframe).toHaveCount(1);
    await iframe.scrollIntoViewIfNeeded();

    const frame = await frameFor(page, IMBALANCE_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/classification_imbalance.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/abide_classification_imbalance.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    await frame.locator('[data-testid="cls-imb-ratio-select"]').selectOption("95:5");
    const cohort = await frame.locator('[data-testid="cls-imb-cohort"]').innerText();
    expect(cohort).toMatch(/400 participants/);
    expect(cohort).toMatch(/20 autism/);

    await expect(frame.locator('[data-testid="cls-imb-plot"]')).toHaveAttribute("data-baseline-accuracy", "0.9500");
  });

  test("changing the ratio and seed selects real precomputed data, not just labels", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    await page.locator(IMBALANCE_IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    const frame = await frameFor(page, IMBALANCE_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const before = await frame.locator('[data-testid="cls-imb-counts"]').innerText();
    await frame.locator('[data-testid="cls-imb-ratio-select"]').selectOption("95:5");
    const afterRatio = await frame.locator('[data-testid="cls-imb-counts"]').innerText();
    expect(afterRatio).not.toEqual(before);

    await frame.locator('[data-testid="cls-imb-seed-select"]').selectOption("1");
    const afterSeed = await frame.locator('[data-testid="cls-imb-metrics"]').innerText();
    expect(afterSeed.length).toBeGreaterThan(0);
  });

  test("embedded imbalance activity is usable at a narrow viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(CHAPTER_URL);
    await page.locator(IMBALANCE_IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    const frame = await frameFor(page, IMBALANCE_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(frame.locator('[data-testid="cls-imb-plot"]')).toBeVisible();
    const overflow = await frame.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });
});
