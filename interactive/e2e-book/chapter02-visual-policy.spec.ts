import { expect, test, type Frame, type Page } from "@playwright/test";

// WP16 regression guard: the deployed Exercise 2 feature-set comparison used
// to paint its x-axis title outside the plot's own box, overlapping the
// ROI-summary <details> row below it by ~15px, and its comparison cards used
// a lavender-gray background instead of the page's own surface. This spec
// reproduces both checks against the *built* Jupyter Book at the real
// deployed content width plus a wider desktop and a narrow (390 px) layout,
// so a future regression is caught at all three.
//
// 1350 px outer viewport measures to ~742-744 px iframe width in the built
// book at the time this spec was written (sidebar visible, single content
// column) -- the width named in WP16 as the real deployed reproduction case.
const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_02/exercise_02.html";
const IFRAME_SELECTOR =
  'iframe[title="Interactive feature-set comparison for predicting age from brain structure"]';

const VIEWPORTS = [
  { name: "742px content width (real deployed reproduction case)", width: 1350, height: 900 },
  { name: "wide desktop", width: 1920, height: 1000 },
  { name: "390px narrow/mobile", width: 390, height: 900 },
];

async function activityFrame(page: Page): Promise<Frame> {
  await page.locator(IFRAME_SELECTOR).scrollIntoViewIfNeeded();
  const handle = await page.locator(IFRAME_SELECTOR).elementHandle();
  expect(handle, "iframe element present").not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, "iframe content frame present").not.toBeNull();
  return frame!;
}

// `data-widget-ready="true"` is set synchronously once `mount()` returns, but
// each panel's `draw()` -- and the `Plotly.react()` inside it that actually
// determines the plot's final rendered height -- runs unawaited ("fire and
// forget") after that. Measuring geometry right after `data-widget-ready`
// races the real Plotly render: on a fast/idle machine the race is rarely
// visible, but a loaded CI runner can measure the pre-render DOM (still at
// its CSS `min-height`, not the actual figure height), which is exactly the
// kind of false "clearance" reading this suite exists to prevent. Wait for
// both panels' own `data-render-count` (set after `Plotly.react()` resolves,
// same signal `e2e-book/chapter02.spec.ts` already asserts) before measuring
// anything.
async function waitForBothPanelsRendered(frame: Frame): Promise<void> {
  await expect(frame.locator('[data-testid="regression-A-plot"]')).toHaveAttribute(
    "data-render-count",
    /[1-9]/,
  );
  await expect(frame.locator('[data-testid="regression-B-plot"]')).toHaveAttribute(
    "data-render-count",
    /[1-9]/,
  );
}

for (const { name, width, height } of VIEWPORTS) {
  test.describe(`Chapter 2 built page — Exercise 2 plot geometry @ ${name}`, () => {
    test("x-axis title stays fully inside the plot's box, with a clear gap above the ROI-summary disclosure", async ({
      page,
    }) => {
      await page.setViewportSize({ width, height });
      await page.goto(CHAPTER_URL);
      const frame = await activityFrame(page);
      await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await waitForBothPanelsRendered(frame);

      const plotBox = await frame.locator('[data-testid="regression-A-plot"]').boundingBox();
      const roiSummaryBox = await frame.locator('[data-testid="regression-A-roi-summary"]').boundingBox();
      expect(plotBox, "plot A bounding box").not.toBeNull();
      expect(roiSummaryBox, "ROI summary bounding box").not.toBeNull();

      const geometry = await frame.evaluate(() => {
        const plot = document.querySelector('[data-testid="regression-A-plot"]') as HTMLElement;
        const svg = plot.querySelector("svg.main-svg");
        const xTitle = plot.querySelector(".xtitle");
        return {
          plotBottom: plot.getBoundingClientRect().bottom,
          svgBottom: svg ? svg.getBoundingClientRect().bottom : null,
          xTitleBottom: xTitle ? xTitle.getBoundingClientRect().bottom : null,
        };
      });

      // The title must never be painted outside the plot's own box (the exact
      // WP16 defect: a fixed height + fixed margin with no `automargin`).
      expect(geometry.xTitleBottom, "x-axis title bottom").not.toBeNull();
      expect(geometry.svgBottom, "plot SVG bottom").not.toBeNull();
      expect(geometry.xTitleBottom!).toBeLessThanOrEqual(geometry.svgBottom! + 0.5);

      // And the plot's rendered box must end with real clearance -- at least
      // 12 CSS px -- before the ROI-summary disclosure begins.
      const clearance = roiSummaryBox!.y - (plotBox!.y + plotBox!.height);
      expect(clearance).toBeGreaterThanOrEqual(12);
    });

    test("both panels' comparison-card background matches the page, not the old lavender-gray surface", async ({
      page,
    }) => {
      await page.setViewportSize({ width, height });
      await page.goto(CHAPTER_URL);
      const frame = await activityFrame(page);
      await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await waitForBothPanelsRendered(frame);

      const colors = await frame.evaluate(() => {
        const panelA = document.querySelector('[data-testid="regression-panel-A"]')!;
        const panelB = document.querySelector('[data-testid="regression-panel-B"]')!;
        return {
          panelA: getComputedStyle(panelA).backgroundColor,
          panelB: getComputedStyle(panelB).backgroundColor,
          page: getComputedStyle(document.body).backgroundColor,
        };
      });
      expect(colors.panelA).not.toBe("rgb(244, 244, 249)");
      expect(colors.panelB).not.toBe("rgb(244, 244, 249)");
      expect(colors.panelA).toBe(colors.page);
      expect(colors.panelB).toBe(colors.page);
    });

    test("no horizontal document overflow and no unexpected iframe clipping at this width", async ({ page }) => {
      await page.setViewportSize({ width, height });
      await page.goto(CHAPTER_URL);
      const frame = await activityFrame(page);
      await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await waitForBothPanelsRendered(frame);

      const pageOverflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(pageOverflow).toBeLessThanOrEqual(1);

      const frameOverflow = await frame.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(frameOverflow).toBeLessThanOrEqual(1);

      // book/_static/activity-resize.js keeps the iframe's own height in sync
      // with its real content height (a static HTML `height` attribute alone
      // cannot stay correct once the compare-grid collapses to one column at
      // a narrow width -- see that file for the full root cause). Give the
      // postMessage round trip a moment to land, then confirm no internal
      // scrollbar/clipping remains at this width.
      const iframeEl = await page.locator(IFRAME_SELECTOR).elementHandle();
      await expect
        .poll(
          async () =>
            iframeEl!.evaluate((el: HTMLIFrameElement) => {
              const doc = el.contentDocument!;
              return doc.documentElement.scrollHeight - doc.documentElement.clientHeight;
            }),
          { message: "iframe content height in sync with its own scrollHeight", timeout: 3000 },
        )
        .toBeLessThanOrEqual(1);
    });

    test("changing measure/ROI bundle redraws the figure without altering the spacing or background policy", async ({
      page,
    }) => {
      await page.setViewportSize({ width, height });
      await page.goto(CHAPTER_URL);
      const frame = await activityFrame(page);
      await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await waitForBothPanelsRendered(frame);

      const before = await frame.evaluate(() => {
        const panel = document.querySelector('[data-testid="regression-panel-A"]')!;
        const plot = document.querySelector('[data-testid="regression-A-plot"]') as HTMLElement;
        const roi = document.querySelector('[data-testid="regression-A-roi-summary"]') as HTMLElement;
        return {
          panelBg: getComputedStyle(panel).backgroundColor,
          clearance: roi.getBoundingClientRect().top - plot.getBoundingClientRect().bottom,
        };
      });

      // data-feature-count is set before the redraw's own Plotly.react() call
      // resolves, so wait for the render-count to actually bump too -- same
      // reasoning as waitForBothPanelsRendered above -- before measuring the
      // "after" geometry.
      const renderCountBefore = await frame
        .locator('[data-testid="regression-A-plot"]')
        .getAttribute("data-render-count");
      await frame.locator('[data-testid="regression-A-bundle"]').selectOption("all-eligible");
      await expect(frame.locator('[data-testid="regression-panel-A"]')).toHaveAttribute(
        "data-feature-count",
        "360",
      );
      await expect(async () => {
        const current = await frame
          .locator('[data-testid="regression-A-plot"]')
          .getAttribute("data-render-count");
        expect(current).not.toBe(renderCountBefore);
      }).toPass({ timeout: 3000 });

      const after = await frame.evaluate(() => {
        const panel = document.querySelector('[data-testid="regression-panel-A"]')!;
        const plot = document.querySelector('[data-testid="regression-A-plot"]') as HTMLElement;
        const roi = document.querySelector('[data-testid="regression-A-roi-summary"]') as HTMLElement;
        return {
          panelBg: getComputedStyle(panel).backgroundColor,
          clearance: roi.getBoundingClientRect().top - plot.getBoundingClientRect().bottom,
        };
      });

      expect(after.panelBg).toBe(before.panelBg);
      expect(after.clearance).toBeGreaterThanOrEqual(12);
    });
  });
}
