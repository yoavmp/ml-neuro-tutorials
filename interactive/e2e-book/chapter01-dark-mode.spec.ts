import { expect, test, type Frame, type Page } from "@playwright/test";

// WP22 regression guard, against the *built* Jupyter Book over real HTTP --
// not the standalone Vite dev page. Confirmed root cause: every activity used
// to read `prefers-color-scheme` on its OWN window, once, at mount time. The
// book's own light/dark toggle (pydata-sphinx-theme) never touches that media
// query -- it resolves the reader's choice onto the PARENT document's
// `data-theme`/`data-mode` instead (see `src/theme.ts`). This spec forces the
// browser's OS-level color-scheme to stay LIGHT throughout (`emulateMedia`)
// and drives the book's own toggle button, so any assertion that passes only
// because the OS preference happened to agree with the book's theme is not
// possible here -- exactly the mismatch the pre-WP22 code could not handle.
//
// A histogram (bar fill + gridlines) and the correlation scatter (marker
// fill) live on the same page, so both charts are covered without a second
// page load.

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html";
const HIST_SEL = 'iframe[src*="config=../configs/eda_histogram.json"]';
const CORR_SEL = 'iframe[src*="config=../configs/eda_correlation.json"]';

// Resolved hex -> rgb() the way getComputedStyle reports it, so assertions
// read as "the dark palette color", not a magic rgb() triplet.
const LIGHT = {
  bg: "rgb(255, 255, 255)",
  histBar: "rgb(42, 111, 158)", // #2a6f9e
  gridColor: "rgb(226, 226, 226)", // #e2e2e2
  corrMarker: "rgb(51, 86, 107)", // #33566b (UNGROUPED_COLOR_LIGHT)
};
const DARK = {
  bg: "rgb(28, 26, 38)", // #1c1a26
  histBar: "rgb(90, 155, 212)", // #5a9bd4
  gridColor: "rgb(58, 58, 58)", // #3a3a3a
  corrMarker: "rgb(143, 182, 204)", // #8fb6cc (UNGROUPED_COLOR_DARK)
};

// `waitUntil: "commit"` (see the two `goto`/`reload` calls below) resolves as
// soon as the response is received -- well before the book's own inline
// script (pydata-sphinx-theme's `setTheme`/`addModeListener`) has run. In
// this environment `"load"`/`"domcontentloaded"` never resolve at all (some
// external resource this sandbox cannot reach keeps the load event pending
// indefinitely), so this polls for the concrete signal that actually matters
// instead: the theme script has resolved `data-mode` from "" to a real value
// and wired up the toggle button's click handler.
async function waitForBookReady(page: Page): Promise<void> {
  await page.waitForFunction(
    () => document.documentElement.dataset.mode !== undefined && document.documentElement.dataset.mode !== "",
    undefined,
    { timeout: 15000 },
  );
}

async function activityFrame(page: Page, selector: string): Promise<Frame> {
  // Each activity iframe is `loading="lazy"` (book/_static, WP16), so it only
  // starts fetching its own document once scrolled near the viewport. Plain
  // `.scrollIntoView()` (bypassing Playwright's actionability/"stable
  // bounding box" wait) is used deliberately: `activity-resize.js` keeps
  // nudging the iframe's own `height` attribute as its content settles, which
  // can keep `scrollIntoViewIfNeeded()`'s stability check from ever
  // resolving.
  const locator = page.locator(selector);
  await locator.evaluate((el) => el.scrollIntoView({ block: "center" }));
  const handle = await locator.elementHandle();
  expect(handle, `${selector} element present`).not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, `${selector} content frame present`).not.toBeNull();
  return frame!;
}

async function waitForRendered(frame: Frame, testId: string): Promise<void> {
  await expect(frame.locator(`[data-testid="${testId}"]`)).toHaveAttribute("data-render-count", /[1-9]/);
}

interface ChartSnapshot {
  bodyBg: string;
  barOrMarkerFill: string;
  gridStroke: string | null;
  dragRectFills: string[];
  dragRectStrokes: string[];
}

async function snapshotHistogram(frame: Frame): Promise<ChartSnapshot> {
  await waitForRendered(frame, "histogram-plot");
  return frame.evaluate(() => {
    const plot = document.querySelector('[data-testid="histogram-plot"]')!;
    const bar = plot.querySelector(".bars path");
    const grid = plot.querySelector(".gridlayer path");
    const dragRects = Array.from(plot.querySelectorAll(".draglayer rect"));
    return {
      bodyBg: getComputedStyle(document.body).backgroundColor,
      barOrMarkerFill: bar ? getComputedStyle(bar).fill : "",
      gridStroke: grid ? getComputedStyle(grid).stroke : null,
      dragRectFills: dragRects.map((r) => getComputedStyle(r).fill),
      dragRectStrokes: dragRects.map((r) => getComputedStyle(r).stroke),
    };
  });
}

async function snapshotCorrelation(frame: Frame): Promise<ChartSnapshot> {
  await waitForRendered(frame, "correlation-plot");
  return frame.evaluate(() => {
    const plot = document.querySelector('[data-testid="correlation-plot"]')!;
    const point = plot.querySelector("g.points path.point");
    const grid = plot.querySelector(".gridlayer path");
    const dragRects = Array.from(plot.querySelectorAll(".draglayer rect"));
    return {
      bodyBg: getComputedStyle(document.body).backgroundColor,
      barOrMarkerFill: point ? getComputedStyle(point).fill : "",
      gridStroke: grid ? getComputedStyle(grid).stroke : null,
      dragRectFills: dragRects.map((r) => getComputedStyle(r).fill),
      dragRectStrokes: dragRects.map((r) => getComputedStyle(r).stroke),
    };
  });
}

test.describe("Chapter 1 built page — dark-mode Plotly theme sync (WP22)", () => {
  // Each test drives 2 iframes through 3-4 theme states plus a full page
  // reload; the default 30s budget is tuned for lighter single-state specs.
  test.describe.configure({ timeout: 90_000 });

  test("histogram and correlation scatter: light → dark → reload-while-dark → light, every critical surface matches the intended palette", async ({
    page,
  }) => {
    // The browser's OS-level preference stays LIGHT for the entire test. If
    // any assertion below only passed because the OS preference happened to
    // agree with the book's chosen theme, this pins it so it can't.
    await page.emulateMedia({ colorScheme: "light" });
    await page.setViewportSize({ width: 1350, height: 1000 });
    await page.goto(CHAPTER_URL, { waitUntil: "commit" });
    await waitForBookReady(page);

    // --- 1. light mode (book default: "auto", resolved against light OS) ---
    let hist = await activityFrame(page, HIST_SEL);
    let corr = await activityFrame(page, CORR_SEL);
    const histLight = await snapshotHistogram(hist);
    const corrLight = await snapshotCorrelation(corr);
    expect(histLight.bodyBg, "histogram light: widget card background").toBe(LIGHT.bg);
    expect(histLight.barOrMarkerFill, "histogram light: bar color").toBe(LIGHT.histBar);
    expect(histLight.gridStroke, "histogram light: gridline color").toBe(LIGHT.gridColor);
    expect(corrLight.bodyBg, "correlation light: widget card background").toBe(LIGHT.bg);
    expect(corrLight.barOrMarkerFill, "correlation light: marker color").toBe(LIGHT.corrMarker);

    // --- 2/3. switch to dark using the book's own color-mode control ---
    await page.locator("button.theme-switch-button").first().click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

    hist = await activityFrame(page, HIST_SEL);
    corr = await activityFrame(page, CORR_SEL);
    const histDark = await snapshotHistogram(hist);
    const corrDark = await snapshotCorrelation(corr);
    expect(histDark.bodyBg, "histogram dark: widget card background").toBe(DARK.bg);
    expect(histDark.barOrMarkerFill, "histogram dark: bar color").toBe(DARK.histBar);
    expect(histDark.gridStroke, "histogram dark: gridline color").toBe(DARK.gridColor);
    for (const fill of histDark.dragRectFills) {
      expect(["rgba(0, 0, 0, 0)", "transparent"]).toContain(fill);
    }
    for (const stroke of histDark.dragRectStrokes) {
      expect(["none", "rgba(0, 0, 0, 0)"]).toContain(stroke);
    }
    expect(corrDark.bodyBg, "correlation dark: widget card background").toBe(DARK.bg);
    expect(corrDark.barOrMarkerFill, "correlation dark: marker color").toBe(DARK.corrMarker);

    // --- 4. reload while dark is already selected (the exact WP22 defect:
    // theme used to be read once at mount, so a *cold* dark-mode load with a
    // light OS preference rendered the light palette). Mode persists via the
    // book's own localStorage. ---
    await page.reload({ waitUntil: "commit" });
    await waitForBookReady(page);
    hist = await activityFrame(page, HIST_SEL);
    corr = await activityFrame(page, CORR_SEL);
    const histReloaded = await snapshotHistogram(hist);
    const corrReloaded = await snapshotCorrelation(corr);
    expect(histReloaded.bodyBg, "histogram reload-in-dark: widget card background").toBe(DARK.bg);
    expect(histReloaded.barOrMarkerFill, "histogram reload-in-dark: bar color").toBe(DARK.histBar);
    expect(corrReloaded.bodyBg, "correlation reload-in-dark: widget card background").toBe(DARK.bg);
    expect(corrReloaded.barOrMarkerFill, "correlation reload-in-dark: marker color").toBe(DARK.corrMarker);

    // --- 5. switch back to light and verify restoration ---
    await page.locator("button.theme-switch-button").first().click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

    hist = await activityFrame(page, HIST_SEL);
    corr = await activityFrame(page, CORR_SEL);
    const histRestored = await snapshotHistogram(hist);
    const corrRestored = await snapshotCorrelation(corr);
    expect(histRestored.bodyBg, "histogram restored-light: widget card background").toBe(LIGHT.bg);
    expect(histRestored.barOrMarkerFill, "histogram restored-light: bar color").toBe(LIGHT.histBar);
    expect(corrRestored.bodyBg, "correlation restored-light: widget card background").toBe(LIGHT.bg);
    expect(corrRestored.barOrMarkerFill, "correlation restored-light: marker color").toBe(LIGHT.corrMarker);
  });

  test("dark → light → dark again keeps redrawing correctly each time", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "light" });
    await page.setViewportSize({ width: 1350, height: 1000 });
    await page.goto(CHAPTER_URL, { waitUntil: "commit" });
    await waitForBookReady(page);
    const toggle = page.locator("button.theme-switch-button").first();

    await toggle.click(); // auto -> dark
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    let hist = await activityFrame(page, HIST_SEL);
    expect((await snapshotHistogram(hist)).barOrMarkerFill).toBe(DARK.histBar);

    await toggle.click(); // dark -> light
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
    hist = await activityFrame(page, HIST_SEL);
    expect((await snapshotHistogram(hist)).barOrMarkerFill).toBe(LIGHT.histBar);

    await toggle.click(); // light -> auto (resolves to light against light OS emulation)
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

    await toggle.click(); // auto -> dark
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    hist = await activityFrame(page, HIST_SEL);
    expect((await snapshotHistogram(hist)).barOrMarkerFill).toBe(DARK.histBar);
  });
});
