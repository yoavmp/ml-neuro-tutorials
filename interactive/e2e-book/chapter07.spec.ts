import { expect, test, type Frame } from "@playwright/test";

// Proof that both embedded Exercise 7 activities (WP32: "Boosting and
// Gradient Boosting") -- "Build a Boosted Model" and "Explore the Boosting
// Parameters" -- work on the *final built* Exercise 7 HTML page, not just
// the standalone widget page.

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_07/exercise_07.html";
const STEP_IFRAME_SELECTOR =
  'iframe[title="Interactive stage-by-stage gradient boosting activity on a small simulated dataset"]';
const PARAM_IFRAME_SELECTOR =
  'iframe[title="Interactive gradient-boosting parameter explorer for predicting age from brain structure"]';

async function frameFor(page: import("@playwright/test").Page, selector: string): Promise<Frame> {
  await page.locator(selector).scrollIntoViewIfNeeded();
  const handle = await page.locator(selector).elementHandle();
  expect(handle, "iframe element present").not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, "iframe content frame present").not.toBeNull();
  return frame!;
}

test.describe("Chapter 7 built page — title and structure", () => {
  test("shows the exact title, no stale placeholder text, both activities, no AdaBoost, and a Colab button", async ({
    page,
  }) => {
    await page.goto(CHAPTER_URL);
    const h1Text = await page.locator(".bd-article h1").first().innerText();
    expect(h1Text.replace(/#\s*$/, "").trim()).toBe("Exercise 7: Boosting and Gradient Boosting");

    const bodyText = await page.locator(".bd-article").innerText();
    expect(bodyText).not.toMatch(/Materials for this exercise will be added before the practice session\./);
    expect(bodyText.toLowerCase()).not.toContain("adaboost");

    await expect(page.locator(STEP_IFRAME_SELECTOR)).toHaveCount(1);
    await expect(page.locator(PARAM_IFRAME_SELECTOR)).toHaveCount(1);
    await expect(page.locator("iframe")).toHaveCount(2);

    await expect(page.locator('[data-testid="colab-launch-button"]')).toBeVisible();
  });
});

test.describe("Chapter 7 built page — embedded Build a Boosted Model activity", () => {
  test("iframe loads, config+data are 200, both plots render at stage 0", async ({ page }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, STEP_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/boosting_step_by_step.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/boosting_step_by_step.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    await expect(frame.locator('[data-testid="boosting-step-observation-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );
    await expect(frame.locator("#app")).toHaveAttribute("data-stage-index", "0");
  });

  test("Next Step advances the stage inside the built page", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, STEP_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await frame.locator('[data-testid="boosting-step-next-button"]').click();
    await expect(frame.locator("#app")).toHaveAttribute("data-stage-index", "1");
  });
});

test.describe("Chapter 7 built page — embedded Explore the Boosting Parameters activity", () => {
  test("iframe loads, config+data are 200, defaults applied, all panels render", async ({ page }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, PARAM_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/boosting_parameter_explorer.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/boosting_parameter_explorer.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    await expect(frame.locator("#app")).toHaveAttribute("data-learning-rate", "0.1");
    await expect(frame.locator("#app")).toHaveAttribute("data-depth", "2");
    await expect(frame.locator("#app")).toHaveAttribute("data-n-trees", "100");
    await expect(frame.locator('[data-testid="boosting-param-mse-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );
    await expect(frame.locator('[data-testid="boosting-param-heatmap-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );
    await expect(frame.locator('[data-testid="boosting-param-prediction-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );
  });

  test("Play advances the tree count inside the built page", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, PARAM_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await frame.locator('[data-testid="boosting-param-play-button"]').click();
    await expect(frame.locator("#app")).not.toHaveAttribute("data-n-trees", "100", { timeout: 5000 });
  });

  test("browser refresh restores the configured defaults", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    let frame = await frameFor(page, PARAM_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await frame.locator('[data-testid="boosting-param-depth-select"]').selectOption("3");

    await page.reload();
    frame = await frameFor(page, PARAM_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(frame.locator("#app")).toHaveAttribute("data-depth", "2");
  });
});

test.describe("Chapter 7 built page — narrow-viewport layout", () => {
  test("both activities remain usable at 390px without horizontal document scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(CHAPTER_URL);

    const stepFrame = await frameFor(page, STEP_IFRAME_SELECTOR);
    await expect(stepFrame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    let overflow = await stepFrame.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);

    const paramFrame = await frameFor(page, PARAM_IFRAME_SELECTOR);
    await expect(paramFrame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    overflow = await paramFrame.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });
});
