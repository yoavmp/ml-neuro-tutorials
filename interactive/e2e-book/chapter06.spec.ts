import { expect, test, type Frame } from "@playwright/test";

// Proof that both embedded Exercise 6 activities (WP29: "Decision Trees") --
// "Build a Tree Greedily" and "One Tree or Many?" -- work on the *final
// built* Exercise 6 HTML page, not just the standalone widget page.

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_06/exercise_06.html";
const GREEDY_IFRAME_SELECTOR =
  'iframe[title="Interactive greedy-splitting activity for a small synthetic regression tree"]';
const ENSEMBLE_IFRAME_SELECTOR =
  'iframe[title="Interactive comparison of a single tree, bagging, and Random Forest for predicting age from brain structure"]';

async function frameFor(page: import("@playwright/test").Page, selector: string): Promise<Frame> {
  await page.locator(selector).scrollIntoViewIfNeeded();
  const handle = await page.locator(selector).elementHandle();
  expect(handle, "iframe element present").not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, "iframe content frame present").not.toBeNull();
  return frame!;
}

test.describe("Chapter 6 built page — title and structure", () => {
  test("shows the exact title, no stale placeholder text, both activities, and a Colab button", async ({
    page,
  }) => {
    await page.goto(CHAPTER_URL);
    const h1Text = await page.locator(".bd-article h1").first().innerText();
    expect(h1Text.replace(/#\s*$/, "").trim()).toBe("Exercise 6: Decision Trees");

    const bodyText = await page.locator(".bd-article").innerText();
    expect(bodyText).not.toMatch(/Materials for this exercise will be added before the practice session\./);
    expect(bodyText.toLowerCase()).not.toContain("adaboost");
    expect(bodyText.toLowerCase()).not.toContain("gradient boosting");
    expect(bodyText.toLowerCase()).not.toContain("xgboost");
    expect(bodyText.toLowerCase()).not.toContain("classification tree");

    await expect(page.locator(GREEDY_IFRAME_SELECTOR)).toHaveCount(1);
    await expect(page.locator(ENSEMBLE_IFRAME_SELECTOR)).toHaveCount(1);
    await expect(page.locator("iframe")).toHaveCount(2);

    await expect(page.locator('[data-testid="colab-launch-button"]')).toBeVisible();
  });
});

test.describe("Chapter 6 built page — embedded Build a Tree Greedily activity", () => {
  test("iframe loads, config+data are 200, both panels render, no optimum revealed yet", async ({ page }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, GREEDY_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/tree_greedy_split.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/tree_greedy_split.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    await expect(frame.locator('[data-testid="tree-greedy-feature-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );
    await expect(frame.locator('[data-testid="tree-greedy-mse-plot"]')).toHaveAttribute("data-render-count", /[1-9]/);
    await expect(frame.locator('[data-testid="tree-greedy-reveal-panel"]')).toBeHidden();
  });

  test("lock and reveal shows the greedy optimum for the root node", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, GREEDY_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await frame.locator('[data-testid="tree-greedy-lock-button"]').click();
    await frame.locator('[data-testid="tree-greedy-reveal-button"]').click();
    const revealText = await frame.locator('[data-testid="tree-greedy-reveal-panel"]').innerText();
    expect(revealText).toContain("Greedy optimum");
    expect(revealText.toLowerCase()).toContain("x1");
  });
});

test.describe("Chapter 6 built page — embedded One Tree or Many? activity", () => {
  test("iframe loads, config+data are 200, defaults to Random Forest, all panels render", async ({ page }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, ENSEMBLE_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/tree_ensemble_compare.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/tree_ensemble_compare.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    await expect(frame.locator('[data-testid="tree-ensemble-model-select"]')).toHaveValue("random-forest");
    await expect(frame.locator('[data-testid="tree-ensemble-distribution-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );
    await expect(frame.locator('[data-testid="tree-ensemble-size-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );
    await expect(frame.locator('[data-testid="tree-ensemble-prediction-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );
  });

  test("browser refresh restores the configured default replicate and model", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    let frame = await frameFor(page, ENSEMBLE_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await frame.locator('[data-testid="tree-ensemble-model-select"]').selectOption("single-tree");

    await page.reload();
    frame = await frameFor(page, ENSEMBLE_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(frame.locator('[data-testid="tree-ensemble-model-select"]')).toHaveValue("random-forest");
  });
});

test.describe("Chapter 6 built page — narrow-viewport layout", () => {
  test("both activities remain usable at 390px without horizontal document scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(CHAPTER_URL);

    const greedyFrame = await frameFor(page, GREEDY_IFRAME_SELECTOR);
    await expect(greedyFrame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    let overflow = await greedyFrame.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);

    const ensembleFrame = await frameFor(page, ENSEMBLE_IFRAME_SELECTOR);
    await expect(ensembleFrame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    overflow = await ensembleFrame.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });
});
