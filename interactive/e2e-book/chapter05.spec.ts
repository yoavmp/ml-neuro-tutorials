import { expect, test, type Frame } from "@playwright/test";

// Proof that both embedded Exercise 5 activities (WP28: "Regularization and
// Feature Selection") work on the *final built* Exercise 5 HTML page -- not
// just the standalone widget page. The regression-compare activity moved
// here from Exercise 2's Bonus section (see chapter02.spec.ts, which now
// only covers the knn-explore activity); regularization-explore is new. The
// dark-mode check for these activities lives in
// wp22-cross-chapter-dark-mode.spec.ts.

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_05/exercise_05.html";
const COMPARE_IFRAME_SELECTOR =
  'iframe[title="Interactive feature-set comparison for predicting age from brain structure"]';
const REGULARIZATION_IFRAME_SELECTOR =
  'iframe[title="Interactive Ridge/Lasso regularization exploration for predicting age from brain structure"]';

async function frameFor(page: import("@playwright/test").Page, selector: string): Promise<Frame> {
  await page.locator(selector).scrollIntoViewIfNeeded();
  const handle = await page.locator(selector).elementHandle();
  expect(handle, "iframe element present").not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, "iframe content frame present").not.toBeNull();
  return frame!;
}

test.describe("Chapter 5 built page — title and structure", () => {
  test("shows the exact title, no stale placeholder text, both activities, and a Colab button", async ({
    page,
  }) => {
    await page.goto(CHAPTER_URL);
    const h1Text = await page.locator(".bd-article h1").first().innerText();
    expect(h1Text.replace(/#\s*$/, "").trim()).toBe("Exercise 5: Regularization and Feature Selection");

    const bodyText = await page.locator(".bd-article").innerText();
    expect(bodyText).not.toMatch(/Materials for this exercise will be added before the practice session\./);
    expect(bodyText).not.toMatch(/logistic regression/i);
    expect(bodyText.toLowerCase()).not.toContain("selection frequency");
    expect(bodyText.toLowerCase()).not.toContain("are the selected features stable");

    // exactly one embedded activity of each kind
    await expect(page.locator(COMPARE_IFRAME_SELECTOR)).toHaveCount(1);
    await expect(page.locator(REGULARIZATION_IFRAME_SELECTOR)).toHaveCount(1);
    await expect(page.locator("iframe")).toHaveCount(2);

    await expect(page.locator('[data-testid="colab-launch-button"]')).toBeVisible();
  });
});

test.describe("Chapter 5 built page — embedded feature-set comparison (moved from Exercise 2)", () => {
  test("iframe loads, config+data are 200, both panels render, a control change is real", async ({
    page,
  }) => {
    const APP_MARKER = "/_static/widgets/app/";
    const responses: { url: string; status: number }[] = [];
    const activityRequests: string[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));
    page.on("request", (r) => {
      if ((r.frame()?.url() ?? "").includes(APP_MARKER)) activityRequests.push(r.url());
    });

    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, COMPARE_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/regression_compare.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/abide_regression_models.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    const panelA = frame.locator('[data-testid="regression-panel-A"]');
    const panelB = frame.locator('[data-testid="regression-panel-B"]');
    await expect(panelA).toBeVisible();
    await expect(panelB).toBeVisible();
    await expect(panelA).toHaveAttribute("data-feature-count", "78"); // frontoparietal x CT
    await expect(panelB).toHaveAttribute("data-feature-count", "46"); // occipital x CT

    const beforeR2 = await panelA.getAttribute("data-r2");
    await frame.locator('[data-testid="regression-A-bundle"]').selectOption("all-eligible");
    await expect(panelA).toHaveAttribute("data-feature-count", "360");
    expect(await panelA.getAttribute("data-r2")).not.toEqual(beforeR2);

    expect(activityRequests.length).toBeGreaterThan(0);
  });
});

test.describe("Chapter 5 built page — embedded regularization-explore activity", () => {
  test("iframe loads, config+data are 200, defaults to Ridge at its best alpha", async ({ page }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, REGULARIZATION_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/regularization_explore.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/regularization_explore.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    await expect(frame.locator('[data-testid="regularization-model-select"]')).toHaveValue("ridge");
    await expect(frame.locator('[data-testid="regularization-predictions-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );
    await expect(frame.locator('[data-testid="regularization-coefficients-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );

    const bodyText = await frame.locator("#app").innerText();
    expect(bodyText.toLowerCase()).not.toContain("test mse");
    expect(bodyText.toLowerCase()).not.toContain("held-out");
  });

  test("choosing Linear Regression disables the alpha control", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, REGULARIZATION_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await frame.locator('[data-testid="regularization-model-select"]').selectOption("linear");
    await expect(frame.locator('[data-testid="regularization-alpha-slider"]')).toBeDisabled();
  });

  test("browser refresh restores the configured default model", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    let frame = await frameFor(page, REGULARIZATION_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await frame.locator('[data-testid="regularization-model-select"]').selectOption("lasso");

    await page.reload();
    frame = await frameFor(page, REGULARIZATION_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(frame.locator('[data-testid="regularization-model-select"]')).toHaveValue("ridge");
  });
});

test.describe("Chapter 5 built page — narrow-viewport layout", () => {
  test("both activities remain usable at 390px without horizontal document scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(CHAPTER_URL);

    const compareFrame = await frameFor(page, COMPARE_IFRAME_SELECTOR);
    await expect(compareFrame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    let overflow = await compareFrame.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);

    const regFrame = await frameFor(page, REGULARIZATION_IFRAME_SELECTOR);
    await expect(regFrame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    overflow = await regFrame.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });
});
