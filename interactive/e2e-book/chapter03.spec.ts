import { expect, test, type Frame } from "@playwright/test";

// Proof that the embedded knn-explore activity works on the *final built
// Exercise 3 HTML page*, served beneath the simulated GitHub Pages project
// subpath -- not just the standalone widget page.

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_03/exercise_03.html";
const IFRAME_SELECTOR =
  'iframe[title="Interactive KNN neighbour-count exploration for predicting age from brain structure"]';
const N_FIT = 564;

async function activityFrame(page: import("@playwright/test").Page): Promise<Frame> {
  const handle = await page.locator(IFRAME_SELECTOR).elementHandle();
  expect(handle, "iframe element present").not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, "iframe content frame present").not.toBeNull();
  return frame!;
}

test.describe("Chapter 3 built page — embedded KNN k-exploration", () => {
  test("iframe loads, config+data are 200, both plots render, a real k change is real", async ({
    page,
  }) => {
    const APP_MARKER = "/_static/widgets/app/";
    const responses: { url: string; status: number }[] = [];
    const activityRequests: string[] = [];
    const failed: string[] = [];
    const sockets: string[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));
    page.on("request", (r) => {
      if ((r.frame()?.url() ?? "").includes(APP_MARKER)) activityRequests.push(r.url());
    });
    page.on("requestfailed", (r) => failed.push(r.url()));
    page.on("websocket", (ws) => sockets.push(ws.url()));

    await page.goto(CHAPTER_URL);
    const iframe = page.locator(IFRAME_SELECTOR);
    await expect(iframe).toHaveCount(1);
    await iframe.scrollIntoViewIfNeeded();

    const frame = await activityFrame(page);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/knn_explore.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/abide_knn_explore.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    const slider = frame.locator('[data-testid="knn-k-slider"]');
    await expect(slider).toHaveValue("17"); // validation-optimal default
    await expect(frame.locator('[data-testid="knn-scatter-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );
    await expect(frame.locator('[data-testid="knn-curve-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );

    const metrics = await frame.locator('[data-testid="knn-metrics"]').innerText();
    expect(metrics).toMatch(/k = 17/);

    // a real control change: k=1 -> perfect fitting R2, different metrics text
    const beforeMetrics = metrics;
    await slider.fill("1");
    await expect(frame.locator('[data-testid="knn-k-value"]')).toHaveText("1");
    const afterMetrics = await frame.locator('[data-testid="knn-metrics"]').innerText();
    expect(afterMetrics).not.toEqual(beforeMetrics);
    expect(afterMetrics).toMatch(/fitting R2 = 1\.000/);

    // no CDN / kernel / socket / off-origin from the activity
    const origin = new URL(page.url()).origin;
    expect(activityRequests.length).toBeGreaterThan(0);
    const offOrigin = activityRequests.filter(
      (u) => !u.startsWith(origin) && !u.startsWith("data:"),
    );
    expect(offOrigin, `off-origin: ${offOrigin.join(", ")}`).toEqual([]);
    const banned =
      /cdn\.plot\.ly|jsdelivr|unpkg|cdnjs|googleapis|gstatic|\/api\/kernels|pyodide|\/lite\/|voici|thebe|binder/i;
    expect(activityRequests.filter((u) => banned.test(u))).toEqual([]);
    expect(sockets).toEqual([]);
    expect(failed.filter((u) => /_static\/widgets\//.test(u))).toEqual([]);
  });

  test("k = N_fit collapses the scatter plot to the fitting-set mean", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    await page.locator(IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    const frame = await activityFrame(page);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await frame.locator('[data-testid="knn-k-slider"]').fill(String(N_FIT));
    await expect(frame.locator('[data-testid="knn-k-value"]')).toHaveText(String(N_FIT));
    const metrics = await frame.locator('[data-testid="knn-metrics"]').innerText();
    expect(metrics).toMatch(/fitting R2 = -?0\.000/);
  });

  test("browser refresh restores the configured default k", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    await page.locator(IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    let frame = await activityFrame(page);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await frame.locator('[data-testid="knn-k-slider"]').fill("100");
    await expect(frame.locator('[data-testid="knn-k-value"]')).toHaveText("100");

    await page.reload();
    await page.locator(IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    frame = await activityFrame(page);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(frame.locator('[data-testid="knn-k-slider"]')).toHaveValue("17");
  });

  test("embedded activity is usable at a narrow viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(CHAPTER_URL);
    await page.locator(IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    const frame = await activityFrame(page);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(frame.locator('[data-testid="knn-scatter-plot"]')).toBeVisible();
    const overflow = await frame.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });
});
