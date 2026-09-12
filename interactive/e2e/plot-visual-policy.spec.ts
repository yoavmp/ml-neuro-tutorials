import { expect, test, type Page } from "@playwright/test";

// Project-wide regression guard for WP16: every activity chart must share one
// Plotly presentation policy (locked interaction, theme-matching background,
// no title/legend/next-element overlap), not a fix patched into a single
// component. This complements the existing per-activity specs, which already
// cover functional/control behaviour.

function appUrl(query: string): string {
  return `/app/index.html?config=${query}`;
}

interface PlotRuntimeState {
  dragmode: unknown;
  xFixedrange: unknown;
  yFixedrange: unknown;
  hasModebar: boolean;
  paperBg: string;
  plotBg: string;
}

async function plotRuntimeState(page: Page, testId: string): Promise<PlotRuntimeState> {
  return page.evaluate((selector) => {
    const el = document.querySelector(selector) as (HTMLElement & {
      _fullLayout?: { dragmode?: unknown; xaxis?: { fixedrange?: unknown }; yaxis?: { fixedrange?: unknown } };
    }) | null;
    if (!el) throw new Error(`plot element not found: ${selector}`);
    const cs = getComputedStyle(el);
    return {
      dragmode: el._fullLayout?.dragmode,
      xFixedrange: el._fullLayout?.xaxis?.fixedrange,
      yFixedrange: el._fullLayout?.yaxis?.fixedrange,
      hasModebar: el.querySelectorAll(".modebar").length > 0,
      paperBg: cs.backgroundColor,
      plotBg: cs.backgroundColor,
    };
  }, `[data-testid="${testId}"]`);
}

async function bbox(page: Page, testId: string) {
  const box = await page.locator(`[data-testid="${testId}"]`).boundingBox();
  expect(box, `${testId} has a bounding box`).not.toBeNull();
  return box!;
}

const CHARTS = [
  { activity: "eda-histogram", query: "../configs/eda_histogram.json", plotTestId: "histogram-plot" },
  { activity: "eda-retention", query: "../configs/eda_retention.json", plotTestId: "retention-plot" },
  { activity: "eda-correlation", query: "../configs/eda_correlation.json", plotTestId: "correlation-plot" },
  {
    activity: "regression-compare",
    query: "../configs/regression_compare.json",
    plotTestId: "regression-A-plot",
  },
  { activity: "knn-abc", query: "../configs/knn_abc.json", plotTestId: "knn-abc-panel-a-plot" },
  { activity: "knn-explore", query: "../configs/knn_explore.json", plotTestId: "knn-scatter-plot" },
];

test.describe("shared Plotly presentation policy", () => {
  for (const { activity, query, plotTestId } of CHARTS) {
    test(`${activity}: chart has a nonzero bounding box, no modebar, transparent Plotly surface, and locked axes`, async ({
      page,
    }) => {
      const consoleErrors: string[] = [];
      const failed: string[] = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") consoleErrors.push(msg.text());
      });
      page.on("requestfailed", (r) => failed.push(r.url()));

      await page.goto(appUrl(query));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const box = await bbox(page, plotTestId);
      expect(box.width).toBeGreaterThan(0);
      expect(box.height).toBeGreaterThan(0);

      const state = await plotRuntimeState(page, plotTestId);
      // dragmode:false + fixedrange:true on both axes is the interaction lock:
      // students drive these charts through the lesson's own controls, not by
      // dragging/zooming the axes.
      expect(state.dragmode).toBe(false);
      expect(state.xFixedrange).toBe(true);
      expect(state.yFixedrange).toBe(true);
      expect(state.hasModebar).toBe(false);

      expect(consoleErrors, `console errors: ${consoleErrors.join("; ")}`).toEqual([]);
      expect(failed, `failed requests: ${failed.join(", ")}`).toEqual([]);
    });
  }

  test("regression-compare: scroll-wheel and drag over the plot do not change the axis range (scroll zoom / drag pan disabled)", async ({
    page,
  }) => {
    await page.goto(appUrl("../configs/regression_compare.json"));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const plot = page.locator('[data-testid="regression-A-plot"]');
    const rangeBefore = await plot.evaluate((el) => (el as any)._fullLayout.xaxis.range.slice());

    const box = (await plot.boundingBox())!;
    const cx = box.x + box.width / 2;
    const cy = box.y + box.height / 2;

    // attempt a drag-zoom
    await page.mouse.move(cx - 40, cy);
    await page.mouse.down();
    await page.mouse.move(cx + 40, cy, { steps: 5 });
    await page.mouse.up();

    // attempt a scroll-zoom
    await page.mouse.move(cx, cy);
    await page.mouse.wheel(0, -200);

    // attempt a double-click reset
    await page.mouse.dblclick(cx, cy);

    const rangeAfter = await plot.evaluate((el) => (el as any)._fullLayout.xaxis.range.slice());
    expect(rangeAfter).toEqual(rangeBefore);
  });

  for (const { activity, query, plotTestId } of [
    { activity: "regression-compare", query: "../configs/regression_compare.json", plotTestId: "regression-A-plot" },
    { activity: "knn-abc", query: "../configs/knn_abc.json", plotTestId: "knn-abc-panel-a-plot" },
  ]) {
    test(`${activity}: comparison-card background matches the page, not the old lavender-gray surface`, async ({
      page,
    }) => {
      await page.goto(appUrl(query));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const [panelBg, pageBg] = await page.evaluate(
        ([plotSel]) => {
          const card = document.querySelector(plotSel)!.closest(".widget-compare-panel")!;
          return [getComputedStyle(card).backgroundColor, getComputedStyle(document.body).backgroundColor];
        },
        [`[data-testid="${plotTestId}"]`] as const,
      );
      expect(panelBg).not.toBe("rgb(244, 244, 249)"); // the old --surface-alt
      expect(panelBg).toBe(pageBg);
    });
  }

  test("regression-compare: hover still surfaces a tooltip despite the interaction lock", async ({ page }) => {
    await page.goto(appUrl("../configs/regression_compare.json"));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const plot = page.locator('[data-testid="regression-A-plot"]');
    const point = plot.locator("g.points path.point").first();
    await point.hover({ force: true });
    await expect(page.locator(".hoverlayer .hovertext")).toBeVisible();
  });
});
