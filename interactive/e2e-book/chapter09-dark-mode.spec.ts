import { expect, test, type Frame, type Page } from "@playwright/test";

// Dedicated dark-mode regression guard for Exercise 9's two new activities
// (WP34), over the *built* Jupyter Book, mirroring chapter08-dark-mode.spec.ts
// (itself following the chapter01-dark-mode.spec.ts / WP22 template this
// project uses for per-chapter dark-mode coverage).
//
// See chapter08-dark-mode.spec.ts for the full rationale: the browser's
// OS-level color-scheme is forced to stay LIGHT throughout (`emulateMedia`),
// and the book's own toggle button drives the actual theme change, so a
// chart that only happens to look right because the OS preference matches
// the book's theme cannot pass by accident.

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_09/exercise_09.html";
const PCR_PLS_SEL = 'iframe[title="Interactive PCR-versus-PLS activity for a small simulated two-dimensional dataset"]';
const SVM_SEL = 'iframe[title="Interactive SVM decision-boundary explorer for two synthetic classification datasets"]';

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

async function snapshotPcrPlsCloud(page: Page): Promise<ChartSnapshot> {
  await waitForActivityNavigationStarted(page, PCR_PLS_SEL);
  await waitForActivityRendered(page, PCR_PLS_SEL, "pcr-pls-pred-plot");
  const frame = await activityFrame(page, PCR_PLS_SEL);
  return frame.evaluate(() => {
    const plot = document.querySelector('[data-testid="pcr-pls-pred-plot"]')!;
    const point = plot.querySelector("g.points path.point");
    const grid = plot.querySelector(".gridlayer path");
    return {
      bodyBg: getComputedStyle(document.body).backgroundColor,
      markerFill: point ? getComputedStyle(point).fill : "",
      gridStroke: grid ? getComputedStyle(grid).stroke : null,
    };
  });
}

async function snapshotSvmPlot(page: Page): Promise<{ bodyBg: string; gridStroke: string | null }> {
  await waitForActivityNavigationStarted(page, SVM_SEL);
  await waitForActivityRendered(page, SVM_SEL, "svm-explorer-plot");
  const frame = await activityFrame(page, SVM_SEL);
  return frame.evaluate(() => {
    const plot = document.querySelector('[data-testid="svm-explorer-plot"]')!;
    const grid = plot.querySelector(".gridlayer path");
    return {
      bodyBg: getComputedStyle(document.body).backgroundColor,
      gridStroke: grid ? getComputedStyle(grid).stroke : null,
    };
  });
}

test.describe("Chapter 9 built page — dark-mode Plotly theme sync (WP22 pattern)", () => {
  test.describe.configure({ timeout: 90_000 });

  test("PCR or PLS? and Explore an SVM Boundary: light -> dark -> reload-while-dark -> light", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "light" });
    await page.setViewportSize({ width: 1350, height: 1300 });
    await page.goto(CHAPTER_URL, { waitUntil: "commit" });
    await waitForBookReady(page);

    // --- light mode (book default: "auto", resolved against light OS) ---
    const pcrPlsLight = await snapshotPcrPlsCloud(page);
    const svmLight = await snapshotSvmPlot(page);
    expect(pcrPlsLight.bodyBg, "pcr-pls light: widget card background").toBe(LIGHT.bg);
    expect(pcrPlsLight.markerFill, "pcr-pls light: observed-point color").toBe(LIGHT.marker);
    expect(pcrPlsLight.gridStroke, "pcr-pls light: gridline color").toBe(LIGHT.gridColor);
    expect(svmLight.bodyBg, "svm light: widget card background").toBe(LIGHT.bg);
    expect(svmLight.gridStroke, "svm light: gridline color").toBe(LIGHT.gridColor);

    // --- switch to dark using the book's own color-mode control ---
    await page.locator("button.theme-switch-button").first().click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

    const pcrPlsDark = await snapshotPcrPlsCloud(page);
    const svmDark = await snapshotSvmPlot(page);
    expect(pcrPlsDark.bodyBg, "pcr-pls dark: widget card background").toBe(DARK.bg);
    expect(pcrPlsDark.markerFill, "pcr-pls dark: observed-point color").toBe(DARK.marker);
    expect(pcrPlsDark.gridStroke, "pcr-pls dark: gridline color").toBe(DARK.gridColor);
    expect(svmDark.bodyBg, "svm dark: widget card background").toBe(DARK.bg);
    expect(svmDark.gridStroke, "svm dark: gridline color").toBe(DARK.gridColor);

    // --- reload while dark is already selected (the exact WP22 defect) ---
    await page.reload({ waitUntil: "commit" });
    await waitForBookReady(page);
    const pcrPlsReloaded = await snapshotPcrPlsCloud(page);
    const svmReloaded = await snapshotSvmPlot(page);
    expect(pcrPlsReloaded.bodyBg, "pcr-pls reload-in-dark: widget card background").toBe(DARK.bg);
    expect(pcrPlsReloaded.markerFill, "pcr-pls reload-in-dark: observed-point color").toBe(DARK.marker);
    expect(svmReloaded.bodyBg, "svm reload-in-dark: widget card background").toBe(DARK.bg);

    // --- switch back to light and verify restoration ---
    await page.locator("button.theme-switch-button").first().click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

    const pcrPlsRestored = await snapshotPcrPlsCloud(page);
    const svmRestored = await snapshotSvmPlot(page);
    expect(pcrPlsRestored.bodyBg, "pcr-pls restored-light: widget card background").toBe(LIGHT.bg);
    expect(pcrPlsRestored.markerFill, "pcr-pls restored-light: observed-point color").toBe(LIGHT.marker);
    expect(svmRestored.bodyBg, "svm restored-light: widget card background").toBe(LIGHT.bg);
  });
});
