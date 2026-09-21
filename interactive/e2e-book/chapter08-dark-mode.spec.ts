import { expect, test, type Frame, type Page } from "@playwright/test";

// Dedicated dark-mode regression guard for Exercise 8's two new activities
// (WP33), over the *built* Jupyter Book, mirroring chapter01-dark-mode.spec.ts
// (the WP22 template this project uses for per-chapter dark-mode coverage) --
// WP32's own report flagged the lack of an equivalent spec for Exercise 7 as
// a deviation; this closes that gap for Exercise 8 rather than repeating it.
//
// Root cause this guards against (WP22): every activity used to read
// `prefers-color-scheme` on its OWN window, once, at mount time. The book's
// own light/dark toggle (pydata-sphinx-theme) never touches that media query
// -- it resolves the reader's choice onto the PARENT document's
// `data-theme`/`data-mode` instead (see `src/theme.ts`). This spec forces the
// browser's OS-level color-scheme to stay LIGHT throughout (`emulateMedia`)
// and drives the book's own toggle button, so a chart that only happens to
// look right because the OS preference matches the book's theme cannot pass
// by accident.

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_08/exercise_08.html";
const PROJECTION_SEL =
  'iframe[title="Interactive projection-angle activity for a small simulated two-dimensional dataset"]';
const KMEANS_SEL = 'iframe[title="Interactive PCA and K-means explorer for ABIDE-II participants"]';

// getComputedStyle(el).fill reports only the RGB channels for an SVG path;
// the alpha component of markerPrimary's rgba(...) is applied by the browser
// as a separate `fill-opacity`, not folded into the reported `fill` string.
const LIGHT = {
  bg: "rgb(255, 255, 255)",
  marker: "rgb(42, 111, 158)", // plotly-policy.ts markerPrimary (light), alpha via fill-opacity
  gridColor: "rgb(226, 226, 226)", // #e2e2e2
};
const DARK = {
  bg: "rgb(28, 26, 38)", // #1c1a26
  marker: "rgb(120, 170, 210)", // plotly-policy.ts markerPrimary (dark), alpha via fill-opacity
  gridColor: "rgb(58, 58, 58)", // #3a3a3a
};

async function waitForBookReady(page: Page): Promise<void> {
  await page.waitForFunction(
    () => document.documentElement.dataset.mode !== undefined && document.documentElement.dataset.mode !== "",
    undefined,
    { timeout: 15000 },
  );
}

// See chapter01-dark-mode.spec.ts for the full rationale of this two-step
// wait (native lazy-load intersection trigger, then Plotly's own render
// completion) -- reused verbatim here rather than re-deriving it.
async function waitForActivityNavigationStarted(page: Page, iframeSelector: string): Promise<void> {
  try {
    await page.waitForFunction(
      (iframeSelector: string) => {
        const iframe = document.querySelector(iframeSelector) as HTMLIFrameElement | null;
        if (!iframe) return false;
        iframe.scrollIntoView({ block: "center" });
        const url = iframe.contentDocument?.URL;
        return !!url && url !== "about:blank";
      },
      iframeSelector,
      { timeout: 10_000, polling: 250 },
    );
  } catch {
    throw new Error(`${iframeSelector}: navigation never started (contentDocument stayed at about:blank) within 10s`);
  }
}

async function waitForActivityRendered(page: Page, iframeSelector: string, testId: string): Promise<void> {
  await page.waitForFunction(
    ({ iframeSelector, testId }: { iframeSelector: string; testId: string }) => {
      const iframe = document.querySelector(iframeSelector) as HTMLIFrameElement | null;
      const doc = iframe?.contentDocument;
      if (!doc) return false;
      const el = doc.querySelector(`[data-testid="${testId}"]`) as
        | (HTMLElement & { _fullData?: unknown[]; _fullLayout?: Record<string, unknown> })
        | null;
      if (!el) return false;
      const renderCount = Number(el.dataset.renderCount ?? "0");
      if (!Number.isFinite(renderCount) || renderCount < 1) return false;
      if (!Array.isArray(el._fullData) || el._fullData.length === 0) return false;
      if (!el._fullLayout || Object.keys(el._fullLayout).length === 0) return false;
      const rect = el.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    },
    { iframeSelector, testId },
    { timeout: 20_000, polling: "raf" },
  );
}

async function activityFrame(page: Page, iframeSelector: string): Promise<Frame> {
  const handle = await page.locator(iframeSelector).elementHandle();
  expect(handle, `${iframeSelector} element present`).not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, `${iframeSelector} content frame present`).not.toBeNull();
  return frame!;
}

interface ChartSnapshot {
  bodyBg: string;
  markerFill: string;
  gridStroke: string | null;
}

async function snapshotProjection(page: Page): Promise<ChartSnapshot> {
  await waitForActivityNavigationStarted(page, PROJECTION_SEL);
  await waitForActivityRendered(page, PROJECTION_SEL, "pca-projection-plot");
  const frame = await activityFrame(page, PROJECTION_SEL);
  return frame.evaluate(() => {
    const plot = document.querySelector('[data-testid="pca-projection-plot"]')!;
    const point = plot.querySelector("g.points path.point");
    const grid = plot.querySelector(".gridlayer path");
    return {
      bodyBg: getComputedStyle(document.body).backgroundColor,
      markerFill: point ? getComputedStyle(point).fill : "",
      gridStroke: grid ? getComputedStyle(grid).stroke : null,
    };
  });
}

async function snapshotKmeansInertia(page: Page): Promise<ChartSnapshot> {
  await waitForActivityNavigationStarted(page, KMEANS_SEL);
  await waitForActivityRendered(page, KMEANS_SEL, "pca-kmeans-inertia-plot");
  const frame = await activityFrame(page, KMEANS_SEL);
  return frame.evaluate(() => {
    const plot = document.querySelector('[data-testid="pca-kmeans-inertia-plot"]')!;
    // The 4 non-selected-k markers use theme.markerPrimary; the selected-k
    // marker uses theme.diagonalLine -- read the first (non-selected) point.
    const point = plot.querySelector("g.points path.point");
    const grid = plot.querySelector(".gridlayer path");
    return {
      bodyBg: getComputedStyle(document.body).backgroundColor,
      markerFill: point ? getComputedStyle(point).fill : "",
      gridStroke: grid ? getComputedStyle(grid).stroke : null,
    };
  });
}

test.describe("Chapter 8 built page — dark-mode Plotly theme sync (WP22 pattern)", () => {
  test.describe.configure({ timeout: 90_000 });

  test("Find the Best Projection and Explore PCA and K-Means: light -> dark -> reload-while-dark -> light", async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: "light" });
    await page.setViewportSize({ width: 1350, height: 1200 });
    await page.goto(CHAPTER_URL, { waitUntil: "commit" });
    await waitForBookReady(page);

    // --- light mode (book default: "auto", resolved against light OS) ---
    const projLight = await snapshotProjection(page);
    const kmeansLight = await snapshotKmeansInertia(page);
    expect(projLight.bodyBg, "projection light: widget card background").toBe(LIGHT.bg);
    expect(projLight.markerFill, "projection light: observed-point color").toBe(LIGHT.marker);
    expect(projLight.gridStroke, "projection light: gridline color").toBe(LIGHT.gridColor);
    expect(kmeansLight.bodyBg, "kmeans light: widget card background").toBe(LIGHT.bg);
    expect(kmeansLight.gridStroke, "kmeans light: gridline color").toBe(LIGHT.gridColor);

    // --- switch to dark using the book's own color-mode control ---
    await page.locator("button.theme-switch-button").first().click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

    const projDark = await snapshotProjection(page);
    const kmeansDark = await snapshotKmeansInertia(page);
    expect(projDark.bodyBg, "projection dark: widget card background").toBe(DARK.bg);
    expect(projDark.markerFill, "projection dark: observed-point color").toBe(DARK.marker);
    expect(projDark.gridStroke, "projection dark: gridline color").toBe(DARK.gridColor);
    expect(kmeansDark.bodyBg, "kmeans dark: widget card background").toBe(DARK.bg);
    expect(kmeansDark.gridStroke, "kmeans dark: gridline color").toBe(DARK.gridColor);

    // --- reload while dark is already selected (the exact WP22 defect) ---
    await page.reload({ waitUntil: "commit" });
    await waitForBookReady(page);
    const projReloaded = await snapshotProjection(page);
    const kmeansReloaded = await snapshotKmeansInertia(page);
    expect(projReloaded.bodyBg, "projection reload-in-dark: widget card background").toBe(DARK.bg);
    expect(projReloaded.markerFill, "projection reload-in-dark: observed-point color").toBe(DARK.marker);
    expect(kmeansReloaded.bodyBg, "kmeans reload-in-dark: widget card background").toBe(DARK.bg);

    // --- switch back to light and verify restoration ---
    await page.locator("button.theme-switch-button").first().click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

    const projRestored = await snapshotProjection(page);
    const kmeansRestored = await snapshotKmeansInertia(page);
    expect(projRestored.bodyBg, "projection restored-light: widget card background").toBe(LIGHT.bg);
    expect(projRestored.markerFill, "projection restored-light: observed-point color").toBe(LIGHT.marker);
    expect(kmeansRestored.bodyBg, "kmeans restored-light: widget card background").toBe(LIGHT.bg);
  });
});
