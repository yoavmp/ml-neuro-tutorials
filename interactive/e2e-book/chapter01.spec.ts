import { expect, test, type Frame } from "@playwright/test";

// Proof that the embedded eda-histogram AND eda-retention activities work on the
// *final built Chapter 1 HTML page*, served beneath the simulated GitHub Pages
// project subpath — not just the standalone widget page.

const CHAPTER_URL =
  "/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html";
const IFRAME_SELECTOR = 'iframe[title="Interactive histogram of ABIDE-II variable distributions"]';
const RETENTION_IFRAME_SELECTOR =
  'iframe[title="Interactive ABIDE-II complete-case retention explorer"]';
const CORRELATION_IFRAME_SELECTOR =
  'iframe[title="Interactive ABIDE-II feature correlation explorer"]';
const TABLE_INSPECTION_IFRAME_SELECTOR =
  'iframe[title="Interactive head, tail, and sample comparison for the ABIDE-II table"]';

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
    await frame.locator('[data-testid="histogram-variable"]').selectOption("ADI_R_SOCIAL_TOTAL_A");
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

async function retentionFrame(page: import("@playwright/test").Page): Promise<Frame> {
  const handle = await page.locator(RETENTION_IFRAME_SELECTOR).elementHandle();
  expect(handle, "retention iframe element present").not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, "retention iframe content frame present").not.toBeNull();
  return frame!;
}

async function retentionBars(frame: Frame): Promise<string> {
  return frame.evaluate(() => {
    const paths = document.querySelectorAll<SVGPathElement>(
      '[data-testid="retention-plot"] g.trace.bars g.point path',
    );
    return Array.from(paths, (p) => p.getAttribute("d") ?? "").join("|");
  });
}

test.describe("Chapter 1 built page — embedded retention explorer", () => {
  test("iframe loads, config+data are 200, selection changes text and Plotly geometry", async ({
    page,
  }) => {
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

    const iframe = page.locator(RETENTION_IFRAME_SELECTOR);
    await expect(iframe).toHaveCount(1);
    await iframe.scrollIntoViewIfNeeded();

    const frame = await retentionFrame(page);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    const plot = frame.locator('[data-testid="retention-plot"]');
    await expect(plot.locator("svg.main-svg").first()).toBeVisible();

    // config + data returned HTTP 200
    const configResp = responses.find((r) => r.url.endsWith("/configs/eda_retention.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/abide_retention.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    // defaults: the suggested four-variable core set, exact expected retention
    await expect(plot).toHaveAttribute("data-selected-count", "4");
    await expect(plot).toHaveAttribute("data-total", "1114");
    await expect(plot).toHaveAttribute("data-retained-n", "1015");
    await expect(plot).toHaveAttribute("data-retained-pct", "91.11");
    await expect(plot).toHaveAttribute("data-site-count", "19");
    await expect(frame.locator('[data-testid="retention-stats"]')).toContainText(
      "Retained 1,015 of 1,114 participants (91.1%)",
    );

    // selection-driven change: add behavioral vars -> fewer retained, bars move,
    // low-retention warning shows
    const geomBefore = await retentionBars(frame);
    await frame.locator('[data-testid="retention-select-all"]').click();
    await expect(plot).toHaveAttribute("data-selected-count", "11");
    await expect(plot).toHaveAttribute("data-low-retention", "true");
    await expect(frame.locator('[data-testid="retention-warning"]')).toBeVisible();
    await expect
      .poll(async () => Number(await plot.getAttribute("data-retained-n")))
      .toBeLessThan(1015);
    await expect.poll(async () => (await retentionBars(frame)) !== geomBefore).toBe(true);

    // clear -> explicit no-criterion state
    await frame.locator('[data-testid="retention-clear"]').click();
    await expect(plot).toHaveAttribute("data-no-selection", "true");
    await expect(plot).toHaveAttribute("data-retained-n", "1114");
    await expect(frame.locator('[data-testid="retention-message"]')).toContainText(
      "no completeness criterion is currently applied",
    );

    // the ACTIVITY makes no CDN / kernel / JupyterLite / Voici / off-origin request
    const origin = new URL(page.url()).origin;
    expect(activityRequests.length, "activity issued requests").toBeGreaterThan(0);
    const offOrigin = activityRequests.filter(
      (u) => !u.startsWith(origin) && !u.startsWith("data:"),
    );
    expect(offOrigin, `activity off-origin: ${offOrigin.join(", ")}`).toEqual([]);
    const banned =
      /cdn\.plot\.ly|plotly-latest|jsdelivr|unpkg|cdnjs|googleapis|gstatic|\/api\/kernels|\/api\/sessions|pyodide|\/lite\/|voici|thebe|binder|widget-manager|html-manager/i;
    const bannedHits = activityRequests.filter((u) => banned.test(u));
    expect(bannedHits, `activity banned requests: ${bannedHits.join(", ")}`).toEqual([]);
    expect(allSockets, `websockets: ${allSockets.join(", ")}`).toEqual([]);
    const activityFailed = failed.filter((u) => /_static\/widgets\//.test(u));
    expect(activityFailed, `failed activity requests: ${activityFailed.join(", ")}`).toEqual([]);
  });

  test("browser refresh restores the suggested core set", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    await page.locator(RETENTION_IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    let frame = await retentionFrame(page);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await frame.locator('[data-testid="retention-var-ADOS_G_TOTAL"]').check();
    await expect(frame.locator('[data-testid="retention-plot"]')).toHaveAttribute(
      "data-selected-count",
      "5",
    );

    await page.reload();
    await page.locator(RETENTION_IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    frame = await retentionFrame(page);
    const plot = frame.locator('[data-testid="retention-plot"]');
    await expect(plot).toHaveAttribute("data-selected-count", "4");
    await expect(plot).toHaveAttribute("data-retained-n", "1015");
  });

  test("embedded retention explorer is usable at a narrow viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 780 });
    await page.goto(CHAPTER_URL);
    await page.locator(RETENTION_IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    const frame = await retentionFrame(page);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    const plot = frame.locator('[data-testid="retention-plot"]');
    await expect(plot.locator("svg.main-svg").first()).toBeVisible();
    await frame.locator('[data-testid="retention-var-VIQ"]').check();
    await expect(plot).toHaveAttribute("data-selected-count", "5");
  });
});

async function correlationFrame(page: import("@playwright/test").Page): Promise<Frame> {
  const handle = await page.locator(CORRELATION_IFRAME_SELECTOR).elementHandle();
  expect(handle, "correlation iframe element present").not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, "correlation iframe content frame present").not.toBeNull();
  return frame!;
}

async function correlationPoints(frame: Frame): Promise<{ traces: number; points: number; names: string[] }> {
  return frame.evaluate(() => {
    const gd = document.querySelector('[data-testid="correlation-plot"]') as unknown as {
      data?: Array<{ name?: string; x?: number[] }>;
    };
    const data = gd.data ?? [];
    let points = 0;
    for (const t of data) points += t.x?.length ?? 0;
    return { traces: data.length, points, names: data.map((t) => t.name ?? "") };
  });
}

test.describe("Chapter 1 built page — embedded correlation explorer", () => {
  test("iframe loads, config+data are 200, controls change the real figure and statistics", async ({
    page,
  }) => {
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

    const iframe = page.locator(CORRELATION_IFRAME_SELECTOR);
    await expect(iframe).toHaveCount(1);
    await iframe.scrollIntoViewIfNeeded();

    const frame = await correlationFrame(page);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    const plot = frame.locator('[data-testid="correlation-plot"]');
    await expect(plot.locator("svg.main-svg").first()).toBeVisible();

    const configResp = responses.find((r) => r.url.endsWith("/configs/eda_correlation.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/abide_retention.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    // defaults
    await expect(plot).toHaveAttribute("data-active-x", "FIQ");
    await expect(plot).toHaveAttribute("data-active-y", "SRS_TOTAL_RAW");
    await expect(plot).toHaveAttribute("data-active-method", "pearson");
    await expect(plot).toHaveAttribute("data-n", "778");
    await expect(plot).toHaveAttribute("data-r", "-0.2404");
    const before = await correlationPoints(frame);
    expect(before.traces).toBe(1);
    expect(before.points).toBe(778);

    // switch method -> coefficient changes for a divergent pair
    await frame.locator('[data-testid="correlation-x"]').selectOption("AGE_AT_SCAN");
    await frame.locator('[data-testid="correlation-y"]').selectOption("ADOS_G_TOTAL");
    await expect(plot).toHaveAttribute("data-r", "-0.2290");
    await frame.locator('[data-testid="correlation-method"]').selectOption("spearman");
    await expect(plot).toHaveAttribute("data-r", "-0.3321");
    await expect(plot).toHaveAttribute("data-n", "347");

    // group -> two partitioned traces + per-group stats
    await frame.locator('[data-testid="correlation-x"]').selectOption("FIQ");
    await frame.locator('[data-testid="correlation-y"]').selectOption("SRS_TOTAL_RAW");
    await frame.locator('[data-testid="correlation-method"]').selectOption("pearson");
    await frame.locator('[data-testid="correlation-group"]').selectOption("diagnosis");
    await expect(plot).toHaveAttribute("data-group-count", "2");
    const grouped = await correlationPoints(frame);
    expect(grouped.traces).toBe(2);
    expect(grouped.names).toEqual(["Autism", "Control"]);
    expect(grouped.points).toBe(778);
    await expect(frame.locator('[data-testid="correlation-groups"]')).toContainText(
      "Autism: r = -0.03 (n = 372)",
    );

    // the ACTIVITY makes no CDN / kernel / off-origin request and no WebSocket
    const origin = new URL(page.url()).origin;
    expect(activityRequests.length, "activity issued requests").toBeGreaterThan(0);
    const offOrigin = activityRequests.filter(
      (u) => !u.startsWith(origin) && !u.startsWith("data:"),
    );
    expect(offOrigin, `activity off-origin: ${offOrigin.join(", ")}`).toEqual([]);
    const banned =
      /cdn\.plot\.ly|plotly-latest|jsdelivr|unpkg|cdnjs|googleapis|gstatic|\/api\/kernels|\/api\/sessions|pyodide|\/lite\/|voici|thebe|binder|widget-manager|html-manager/i;
    const bannedHits = activityRequests.filter((u) => banned.test(u));
    expect(bannedHits, `activity banned requests: ${bannedHits.join(", ")}`).toEqual([]);
    expect(allSockets, `websockets: ${allSockets.join(", ")}`).toEqual([]);
    const activityFailed = failed.filter((u) => /_static\/widgets\//.test(u));
    expect(activityFailed, `failed activity requests: ${activityFailed.join(", ")}`).toEqual([]);
  });

  test("same-variable selection is handled and browser refresh restores defaults", async ({
    page,
  }) => {
    await page.goto(CHAPTER_URL);
    await page.locator(CORRELATION_IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    let frame = await correlationFrame(page);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    const plot = frame.locator('[data-testid="correlation-plot"]');

    await frame.locator('[data-testid="correlation-y"]').selectOption("FIQ");
    await expect(plot).toHaveAttribute("data-same-variable", "true");
    await expect(frame.locator('[data-testid="correlation-same-var"]')).toBeVisible();

    await page.reload();
    await page.locator(CORRELATION_IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    frame = await correlationFrame(page);
    const plot2 = frame.locator('[data-testid="correlation-plot"]');
    await expect(plot2).toHaveAttribute("data-active-x", "FIQ");
    await expect(plot2).toHaveAttribute("data-active-y", "SRS_TOTAL_RAW");
    await expect(plot2).toHaveAttribute("data-same-variable", "false");
  });

  test("embedded correlation explorer is usable at a narrow viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 780 });
    await page.goto(CHAPTER_URL);
    await page.locator(CORRELATION_IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    const frame = await correlationFrame(page);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    const plot = frame.locator('[data-testid="correlation-plot"]');
    await expect(plot.locator("svg.main-svg").first()).toBeVisible();
    await frame.locator('[data-testid="correlation-group"]').selectOption("sex");
    await expect(plot).toHaveAttribute("data-active-group", "sex");
  });
});

async function tableInspectionFrame(page: import("@playwright/test").Page): Promise<Frame> {
  const handle = await page.locator(TABLE_INSPECTION_IFRAME_SELECTOR).elementHandle();
  expect(handle, "table-inspection iframe element present").not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, "table-inspection iframe content frame present").not.toBeNull();
  return frame!;
}

test.describe("Chapter 1 built page — embedded head/tail/sample activity", () => {
  test("iframe loads, config+data are 200, and switching the method changes the rows and the summary", async ({
    page,
  }) => {
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

    const iframe = page.locator(TABLE_INSPECTION_IFRAME_SELECTOR);
    await expect(iframe).toHaveCount(1);
    await iframe.scrollIntoViewIfNeeded();

    const frame = await tableInspectionFrame(page);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    const table = frame.locator('[data-testid="table-inspection-table"]');
    await expect(table).toBeVisible();

    const configResp = responses.find((r) => r.url.endsWith("/configs/table_inspection.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/abide_table_inspection.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    // default view: head(8) -> one site; the summary counts missing cells over
    // all 13 curated columns (24)
    await expect(table).toHaveAttribute("data-method", "head");
    await expect(table).toHaveAttribute("data-site-count", "1");
    await expect(table).toHaveAttribute("data-sites", "ABIDEII-BNI_1");
    await expect(table).toHaveAttribute("data-missing-cells", "24");
    await expect(table).toHaveAttribute("data-total-cells", "104"); // 8 rows * 13 cols
    await expect(table.locator("thead th")).toHaveCount(13);

    // a real control change: switch to sample() -> eight sites, fewer missing
    // cells than tail(); the visible rows change
    await frame.locator('[data-testid="table-inspection-method-sample"]').check();
    await expect(table).toHaveAttribute("data-method", "sample");
    await expect(table).toHaveAttribute("data-seed", "7");
    await expect(table).toHaveAttribute("data-site-count", "8");
    await expect(table).toHaveAttribute("data-missing-cells", "17");
    const summaryText = await frame
      .locator('[data-testid="table-inspection-summary"]')
      .innerText();
    expect(summaryText).toContain("8 acquisition sites");
    // the site names are not listed in the evidence summary (WP10 §1)
    expect(summaryText).not.toContain("ABIDEII-");

    // the ACTIVITY makes no CDN / kernel / off-origin request and no WebSocket
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
    expect(activityFailed, `failed activity requests: ${activityFailed.join(", ")}`).toEqual([]);
  });

  test("browser refresh restores the configured defaults", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    await page.locator(TABLE_INSPECTION_IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    let frame = await tableInspectionFrame(page);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await frame.locator('[data-testid="table-inspection-method-tail"]').check();
    await expect(frame.locator('[data-testid="table-inspection-table"]')).toHaveAttribute(
      "data-method",
      "tail",
    );

    await page.reload();
    await page.locator(TABLE_INSPECTION_IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    frame = await tableInspectionFrame(page);
    await expect(frame.locator('[data-testid="table-inspection-table"]')).toHaveAttribute(
      "data-method",
      "head",
    );
  });

  test("embedded activity is usable at a narrow viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 780 });
    await page.goto(CHAPTER_URL);
    await page.locator(TABLE_INSPECTION_IFRAME_SELECTOR).scrollIntoViewIfNeeded();
    const frame = await tableInspectionFrame(page);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    const table = frame.locator('[data-testid="table-inspection-table"]');
    await expect(table).toBeVisible();
    await frame.locator('[data-testid="table-inspection-rows"]').fill("12");
    await expect(table).toHaveAttribute("data-row-count", "12");
  });
});
