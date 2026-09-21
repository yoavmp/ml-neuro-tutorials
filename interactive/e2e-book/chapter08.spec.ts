import { expect, test, type Frame } from "@playwright/test";

// Proof that both embedded Exercise 8 activities (WP33: "Unsupervised
// Learning") -- "Find the Best Projection" and "Explore PCA and K-Means" --
// work on the *final built* Exercise 8 HTML page, not just the standalone
// widget page.

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_08/exercise_08.html";
const PROJECTION_IFRAME_SELECTOR =
  'iframe[title="Interactive projection-angle activity for a small simulated two-dimensional dataset"]';
const KMEANS_IFRAME_SELECTOR =
  'iframe[title="Interactive PCA and K-means explorer for ABIDE-II participants"]';

async function frameFor(page: import("@playwright/test").Page, selector: string): Promise<Frame> {
  await page.locator(selector).scrollIntoViewIfNeeded();
  const handle = await page.locator(selector).elementHandle();
  expect(handle, "iframe element present").not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, "iframe content frame present").not.toBeNull();
  return frame!;
}

test.describe("Chapter 8 built page — title and structure", () => {
  test("shows the exact title, no stale placeholder text, both activities, no out-of-scope methods, and a Colab button", async ({
    page,
  }) => {
    await page.goto(CHAPTER_URL);
    const h1Text = await page.locator(".bd-article h1").first().innerText();
    expect(h1Text.replace(/#\s*$/, "").trim()).toBe("Exercise 8: Unsupervised Learning");

    const bodyText = await page.locator(".bd-article").innerText();
    expect(bodyText).not.toMatch(/Materials for this exercise will be added before the practice session\./);
    const bodyLower = bodyText.toLowerCase();
    for (const needle of ["hierarchical clustering", "dendrogram", "t-sne", "umap", "dbscan", "gaussian mixture", "adaboost"]) {
      expect(bodyLower).not.toContain(needle);
    }

    await expect(page.locator(PROJECTION_IFRAME_SELECTOR)).toHaveCount(1);
    await expect(page.locator(KMEANS_IFRAME_SELECTOR)).toHaveCount(1);
    await expect(page.locator("iframe")).toHaveCount(2);

    await expect(page.locator('[data-testid="colab-launch-button"]')).toBeVisible();
  });
});

test.describe("Chapter 8 built page — embedded Find the Best Projection activity", () => {
  test("iframe loads, config+data are 200, the plot renders, and the true PC1 stays hidden", async ({ page }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, PROJECTION_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/pca_projection.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/pca_projection.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    await expect(frame.locator('[data-testid="pca-projection-plot"]')).toHaveAttribute("data-render-count", /[1-9]/);
    await expect(frame.locator("#app")).toHaveAttribute("data-revealed", "false");
  });

  test("moving the angle slider and revealing PC1 works inside the built page", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, PROJECTION_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const slider = frame.locator('[data-testid="pca-projection-angle-slider"]');
    await slider.fill("15");
    await slider.dispatchEvent("input");
    await expect(frame.locator("#app")).toHaveAttribute("data-angle-deg", "15.0");

    await frame.locator('[data-testid="pca-projection-reveal-button"]').click();
    await expect(frame.locator("#app")).toHaveAttribute("data-revealed", "true");
    await expect(frame.locator('[data-testid="pca-projection-reveal-text"]')).toContainText("True PC1 direction");
  });
});

test.describe("Chapter 8 built page — embedded Explore PCA and K-Means activity", () => {
  test("iframe loads, config+data are 200, defaults applied, all panels render", async ({ page }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, KMEANS_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/pca_kmeans_explorer.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/pca_kmeans_explorer.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    await expect(frame.locator("#app")).toHaveAttribute("data-retained-pc", "10");
    await expect(frame.locator("#app")).toHaveAttribute("data-k", "3");
    for (const testId of ["pca-kmeans-scatter-plot", "pca-kmeans-inertia-plot", "pca-kmeans-silhouette-plot", "pca-kmeans-sizes-plot", "pca-kmeans-composition-plot"]) {
      await expect(frame.locator(`[data-testid="${testId}"]`)).toHaveAttribute("data-render-count", /[1-9]/);
    }
  });

  test("changing k and the external characteristic works inside the built page", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, KMEANS_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await frame.locator('[data-testid="pca-kmeans-k-select"]').selectOption("5");
    await expect(frame.locator("#app")).toHaveAttribute("data-k", "5");

    await frame.locator('[data-testid="pca-kmeans-external-select"]').selectOption("age");
    await expect(frame.locator("#app")).toHaveAttribute("data-external-variable", "age");
  });

  test("browser refresh restores the configured defaults", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    let frame = await frameFor(page, KMEANS_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await frame.locator('[data-testid="pca-kmeans-retained-pc-select"]').selectOption("50");
    await expect(frame.locator("#app")).toHaveAttribute("data-retained-pc", "50");

    await page.reload();
    frame = await frameFor(page, KMEANS_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(frame.locator("#app")).toHaveAttribute("data-retained-pc", "10");
  });
});

test.describe("Chapter 8 built page — narrow-viewport layout", () => {
  test("both activities remain usable at 390px without horizontal document scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(CHAPTER_URL);

    const projFrame = await frameFor(page, PROJECTION_IFRAME_SELECTOR);
    await expect(projFrame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    let overflow = await projFrame.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);

    const kmeansFrame = await frameFor(page, KMEANS_IFRAME_SELECTOR);
    await expect(kmeansFrame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    overflow = await kmeansFrame.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });
});
