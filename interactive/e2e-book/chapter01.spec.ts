import { expect, test, type Frame } from "@playwright/test";

// Proof that the embedded eda-histogram activity works on the *final built
// Chapter 1 HTML page*, served beneath the simulated GitHub Pages project
// subpath — not just the standalone widget page.

const CHAPTER_URL =
  "/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html";
const IFRAME_SELECTOR = 'iframe[title="Interactive histogram of ABIDE-II variable distributions"]';

async function widgetFrame(page: import("@playwright/test").Page): Promise<Frame> {
  const handle = await page.locator(IFRAME_SELECTOR).elementHandle();
  expect(handle, "iframe element present").not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, "iframe content frame present").not.toBeNull();
  return frame!;
}

async function barPaths(frame: Frame): Promise<string> {
  return frame.evaluate(() => {
    const paths = document.querySelectorAll<SVGPathElement>(
      '[data-testid="histogram-plot"] g.trace.bars g.point path',
    );
    return Array.from(paths, (p) => p.getAttribute("d") ?? "").join("|");
  });
}

async function barCount(frame: Frame): Promise<number> {
  return frame.evaluate(
    () =>
      document.querySelectorAll('[data-testid="histogram-plot"] g.trace.bars g.point')
        .length,
  );
}

test.describe("Chapter 1 built page — embedded histogram", () => {
  test("iframe loads, config+data are 200, Plotly renders, both controls redraw", async ({
    page,
  }) => {
    // The Jupyter Book page itself pulls in MathJax / fonts / thebe from CDNs
    // (pre-existing book-theme behaviour, unrelated to WP03). Scope every
    // "no CDN / kernel / off-origin" assertion to requests that originate
    // *inside the activity iframe* by matching the requesting frame URL.
    const APP_MARKER = "/_static/widgets/app/";
    const responses: { url: string; status: number }[] = [];
    const activityRequests: string[] = [];
    const failed: string[] = [];
    const allSockets: string[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));
    page.on("request", (r) => {
      const frameUrl = r.frame()?.url() ?? "";
      if (frameUrl.includes(APP_MARKER)) activityRequests.push(r.url());
    });
    page.on("requestfailed", (r) => failed.push(r.url()));
    page.on("websocket", (ws) => allSockets.push(ws.url()));

    await page.goto(CHAPTER_URL);

    // 1. iframe present under the real Chapter 1 route
    const iframe = page.locator(IFRAME_SELECTOR);
    await expect(iframe).toHaveCount(1);
    await iframe.scrollIntoViewIfNeeded();

    const frame = await widgetFrame(page);

    // 3. Plotly renders inside the iframe
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    const plot = frame.locator('[data-testid="histogram-plot"]');
    await expect(plot.locator("svg.main-svg").first()).toBeVisible();
    await expect(plot).toHaveAttribute("data-active-variable", "AGE_AT_SCAN");
    await expect(plot).toHaveAttribute("data-active-bins", "25");
    await expect(plot).toHaveAttribute("data-bar-count", "25");

    // 2. config + data returned HTTP 200
    const configResp = responses.find((r) => r.url.endsWith("/configs/eda_histogram.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/abide_histogram.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    // 4. changing the variable changes active-variable, N/missing and geometry
    const geomBefore = await barPaths(frame);
    await frame.locator('[data-testid="histogram-variable"]').selectOption("VIQ");
    await expect(plot).toHaveAttribute("data-active-variable", "VIQ");
    await expect(plot).toHaveAttribute("data-render-count", "2");
    await expect(frame.locator('[data-testid="histogram-stats"]')).toContainText(
      "Available N: 799",
    );
    await expect(frame.locator('[data-testid="histogram-stats"]')).toContainText(
      "Missing N: 315",
    );
    await expect.poll(async () => (await barPaths(frame)) !== geomBefore).toBe(true);

    // 5. changing the bin count changes active-bins and the number of bars
    await frame.locator('[data-testid="histogram-bins"]').fill("50");
    await expect(plot).toHaveAttribute("data-active-bins", "50");
    await expect(plot).toHaveAttribute("data-bar-count", "50");
    await expect.poll(async () => await barCount(frame)).toBe(50);
    await frame.locator('[data-testid="histogram-bins"]').fill("10");
    await expect.poll(async () => await barCount(frame)).toBe(10);

    // 7. the ACTIVITY makes no CDN / kernel / JupyterLite / Voici / off-origin
    //    / failed request and opens no WebSocket. (The surrounding Jupyter Book
    //    page's own MathJax/font/thebe CDN use is pre-existing and out of scope.)
    const origin = new URL(page.url()).origin;
    expect(activityRequests.length, "activity issued requests").toBeGreaterThan(0);

    const offOrigin = activityRequests.filter(
      (u) => !u.startsWith(origin) && !u.startsWith("data:"),
    );
    expect(offOrigin, `activity off-origin: ${offOrigin.join(", ")}`).toEqual([]);

    const banned =
      /cdn\.plot\.ly|plotly-latest|jsdelivr|unpkg|cdnjs|googleapis|gstatic|\/api\/kernels|\/api\/sessions|pyodide|\/lite\/|voici|thebe|binder/i;
    const bannedHits = activityRequests.filter((u) => banned.test(u));
    expect(bannedHits, `activity banned requests: ${bannedHits.join(", ")}`).toEqual([]);

    expect(allSockets, `websockets: ${allSockets.join(", ")}`).toEqual([]);

    const activityFailed = failed.filter((u) => /_static\/widgets\//.test(u));
    expect(activityFailed, `failed activity requests: ${activityFailed.join(", ")}`).toEqual(
      [],
    );
  });

  test("browser refresh restores the configured defaults", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    await page.locator(IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    let frame = await widgetFrame(page);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await frame.locator('[data-testid="histogram-variable"]').selectOption("SCQ_TOTAL");
    await frame.locator('[data-testid="histogram-bins"]').fill("45");
    await expect(frame.locator('[data-testid="histogram-plot"]')).toHaveAttribute(
      "data-active-bins",
      "45",
    );

    await page.reload();
    await page.locator(IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    frame = await widgetFrame(page);
    const plot = frame.locator('[data-testid="histogram-plot"]');
    await expect(plot).toHaveAttribute("data-active-variable", "AGE_AT_SCAN");
    await expect(plot).toHaveAttribute("data-active-bins", "25");
  });

  test("embedded activity is usable at a narrow viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 780 });
    await page.goto(CHAPTER_URL);
    await page.locator(IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    const frame = await widgetFrame(page);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    const plot = frame.locator('[data-testid="histogram-plot"]');
    await expect(plot.locator("svg.main-svg").first()).toBeVisible();
    await frame.locator('[data-testid="histogram-variable"]').selectOption("FIQ");
    await expect(plot).toHaveAttribute("data-active-variable", "FIQ");
  });
});
