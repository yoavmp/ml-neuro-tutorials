import { expect, test, type Frame } from "@playwright/test";

// Proof that all four embedded Exercise 10 activities (WP38: "Examples and
// Common Mistakes") -- the multiple-selection quiz, the leakage lab, the
// UCI HAR fold-comparison, and the imbalance-threshold activity -- work on
// the *final built* Exercise 10 HTML page, not just the standalone widget
// page.

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_10/exercise_10.html";
const QUIZ_IFRAME_SELECTOR =
  'iframe[title="Interactive multiple-selection question on which preprocessing and modelling steps must not use the final test participants"]';
const LEAKAGE_LAB_IFRAME_SELECTOR =
  'iframe[title="Interactive leakage-lab comparing correct and leaky preprocessing pipelines on ABIDE-II cortical thickness and age"]';
const HAR_IFRAME_SELECTOR =
  'iframe[title="Interactive comparison of random-window and participant-grouped cross-validation on UCI HAR smartphone sensor windows"]';
const IMBALANCE_IFRAME_SELECTOR =
  'iframe[title="Interactive comparison of ordinary and class-weighted logistic regression for imbalanced autism classification"]';

async function frameFor(page: import("@playwright/test").Page, selector: string): Promise<Frame> {
  await page.locator(selector).scrollIntoViewIfNeeded();
  const handle = await page.locator(selector).elementHandle();
  expect(handle, "iframe element present").not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, "iframe content frame present").not.toBeNull();
  return frame!;
}

test.describe("Chapter 10 built page — title and structure", () => {
  test("shows the exact title, no stale placeholder text, all four activities, and a Colab button", async ({
    page,
  }) => {
    await page.goto(CHAPTER_URL);
    const h1Text = await page.locator(".bd-article h1").first().innerText();
    expect(h1Text.replace(/#\s*$/, "").trim()).toBe("Exercise 10: Examples and Common Mistakes");

    const bodyText = await page.locator(".bd-article").innerText();
    expect(bodyText).not.toMatch(/Materials for this exercise will be added before the practice session\./);

    await expect(page.locator(QUIZ_IFRAME_SELECTOR)).toHaveCount(1);
    await expect(page.locator(LEAKAGE_LAB_IFRAME_SELECTOR)).toHaveCount(1);
    await expect(page.locator(HAR_IFRAME_SELECTOR)).toHaveCount(1);
    await expect(page.locator(IMBALANCE_IFRAME_SELECTOR)).toHaveCount(1);
    await expect(page.locator("iframe")).toHaveCount(4);

    await expect(page.locator('[data-testid="colab-launch-button"]')).toBeVisible();
  });
});

test.describe("Chapter 10 built page — embedded multi-select quiz", () => {
  test("iframe loads, config+data are 200, checking with a full pass shows success", async ({ page }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, QUIZ_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/leakage_quiz.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/leakage_quiz.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    for (const id of ["scaling", "feature-selection", "pca", "missing-fill", "param-choice", "final-model"]) {
      await frame.locator(`[data-testid="quiz-checkbox-${id}"]`).check();
    }
    await frame.locator('[data-testid="quiz-check-button"]').click();
    await expect(frame.locator('[data-testid="quiz-success"]')).toBeVisible();
  });
});

test.describe("Chapter 10 built page — embedded leakage lab", () => {
  test("iframe loads, config+data are 200, both plots render", async ({ page }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, LEAKAGE_LAB_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/leakage_lab.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/abide_leakage_lab.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    await expect(frame.locator('[data-testid="leak-pair-plot"] svg.main-svg').first()).toBeVisible();
    await expect(frame.locator('[data-testid="leak-aggregate-plot"] svg.main-svg').first()).toBeVisible();

    await frame.locator('[data-testid="leak-operation-select"]').selectOption("pca");
    await expect(frame.locator("#app")).toHaveAttribute("data-current-scenario", "pca");
  });
});

test.describe("Chapter 10 built page — embedded UCI HAR fold comparison", () => {
  test("iframe loads, config+data are 200, participant grid and plots render", async ({ page }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, HAR_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/har_fold_compare.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/uci_har_fold_comparison.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    await expect(frame.locator('[data-testid="har-participant-grid"] > *')).toHaveCount(30);

    await frame.locator('[data-testid="har-method-grouped"]').click();
    await expect(frame.locator("#app")).toHaveAttribute("data-current-method", "grouped");
  });
});

test.describe("Chapter 10 built page — embedded imbalance-threshold activity", () => {
  test("iframe loads, config+data are 200, switching model updates the confusion matrix", async ({ page }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, IMBALANCE_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/imbalance_threshold.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/abide_imbalance_threshold.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    await expect(frame.locator('[data-testid="imb-accuracy"]')).toHaveText("85.0%");
    await frame.locator('[data-testid="imb-model-select"]').selectOption("classWeighted");
    await expect(frame.locator('[data-testid="imb-accuracy"]')).toHaveText("81.0%");
  });
});

test.describe("Chapter 10 built page — narrow-viewport layout", () => {
  test("all four activities remain usable at 390px without horizontal document scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(CHAPTER_URL);

    for (const selector of [
      QUIZ_IFRAME_SELECTOR,
      LEAKAGE_LAB_IFRAME_SELECTOR,
      HAR_IFRAME_SELECTOR,
      IMBALANCE_IFRAME_SELECTOR,
    ]) {
      const frame = await frameFor(page, selector);
      await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const overflow = await frame.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);
    }
  });
});
