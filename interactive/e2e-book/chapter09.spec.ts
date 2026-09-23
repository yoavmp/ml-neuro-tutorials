import { expect, test, type Frame } from "@playwright/test";

// Proof that both embedded Exercise 9 activities (WP34: "Advanced Models")
// -- "PCR or PLS?" and "Explore an SVM Boundary" -- work on the *final
// built* Exercise 9 HTML page, not just the standalone widget page.

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_09/exercise_09.html";
const PCR_PLS_IFRAME_SELECTOR = 'iframe[title="Interactive PCR-versus-PLS activity for a small simulated two-dimensional dataset"]';
const SVM_IFRAME_SELECTOR = 'iframe[title="Interactive SVM decision-boundary explorer for two synthetic classification datasets"]';

async function frameFor(page: import("@playwright/test").Page, selector: string): Promise<Frame> {
  await page.locator(selector).scrollIntoViewIfNeeded();
  const handle = await page.locator(selector).elementHandle();
  expect(handle, "iframe element present").not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, "iframe content frame present").not.toBeNull();
  return frame!;
}

test.describe("Chapter 9 built page — title and structure", () => {
  test("shows the exact title, no stale placeholder text, both activities, no out-of-scope methods, and a Colab button", async ({
    page,
  }) => {
    await page.goto(CHAPTER_URL);
    const h1Text = await page.locator(".bd-article h1").first().innerText();
    expect(h1Text.replace(/#\s*$/, "").trim()).toBe("Exercise 9: Advanced Models");

    const bodyText = await page.locator(".bd-article").innerText();
    expect(bodyText).not.toMatch(/Materials for this exercise will be added before the practice session\./);

    await expect(page.locator(PCR_PLS_IFRAME_SELECTOR)).toHaveCount(1);
    await expect(page.locator(SVM_IFRAME_SELECTOR)).toHaveCount(1);
    await expect(page.locator("iframe")).toHaveCount(2);

    await expect(page.locator('[data-testid="colab-launch-button"]')).toBeVisible();
  });
});

test.describe("Chapter 9 built page — embedded PCR or PLS? activity", () => {
  test("iframe loads, config+data are 200, both panels render", async ({ page }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, PCR_PLS_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/pcr_pls_explore.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/pcr_pls_explore.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    for (const testId of ["pcr-pls-cloud-plot", "pcr-pls-pred-plot"]) {
      await expect(frame.locator(`[data-testid="${testId}"]`)).toHaveAttribute("data-render-count", /[1-9]/);
    }
  });

  test("changing method and preset works inside the built page", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, PCR_PLS_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await frame.locator('[data-testid="pcr-pls-method-select"]').selectOption("pls");
    await expect(frame.locator("#app")).toHaveAttribute("data-method", "pls");

    await frame.locator('[data-testid="pcr-pls-preset-select"]').selectOption("strong");
    await expect(frame.locator("#app")).toHaveAttribute("data-preset", "strong");
  });
});

test.describe("Chapter 9 built page — embedded Explore an SVM Boundary activity", () => {
  test("iframe loads, config+data are 200, defaults applied, plot renders", async ({ page }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, SVM_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/svm_explorer.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/svm_explorer.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    await expect(frame.locator("#app")).toHaveAttribute("data-dataset", "linear");
    await expect(frame.locator("#app")).toHaveAttribute("data-kernel", "linear");
    await expect(frame.locator('[data-testid="svm-explorer-plot"]')).toHaveAttribute("data-render-count", /[1-9]/);
  });

  test("changing dataset and kernel works inside the built page", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, SVM_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await frame.locator('[data-testid="svm-explorer-dataset-select"]').selectOption("nonlinear");
    await expect(frame.locator("#app")).toHaveAttribute("data-dataset", "nonlinear");

    await frame.locator('[data-testid="svm-explorer-kernel-select"]').selectOption("rbf");
    await expect(frame.locator("#app")).toHaveAttribute("data-kernel", "rbf");
    await expect(frame.locator('[data-testid="svm-explorer-gamma-select"]')).toBeEnabled();
  });

  test("browser refresh restores the configured defaults", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    let frame = await frameFor(page, SVM_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await frame.locator('[data-testid="svm-explorer-kernel-select"]').selectOption("rbf");
    await expect(frame.locator("#app")).toHaveAttribute("data-kernel", "rbf");

    await page.reload();
    frame = await frameFor(page, SVM_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(frame.locator("#app")).toHaveAttribute("data-kernel", "linear");
  });
});

test.describe("Chapter 9 built page — narrow-viewport layout", () => {
  test("both activities remain usable at 390px without horizontal document scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(CHAPTER_URL);

    const pcrPlsFrame = await frameFor(page, PCR_PLS_IFRAME_SELECTOR);
    await expect(pcrPlsFrame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    let overflow = await pcrPlsFrame.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);

    const svmFrame = await frameFor(page, SVM_IFRAME_SELECTOR);
    await expect(svmFrame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    overflow = await svmFrame.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });
});
