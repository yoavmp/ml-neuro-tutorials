import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `eda-histogram` activity, served
// from book/_static/widgets/ at both the site root and the simulated GitHub
// Pages project subpath. The built-Jupyter-Book check lives in
// ../e2e-book/chapter01.spec.ts.
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/eda_histogram.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

async function barGeometry(page: import("@playwright/test").Page): Promise<string> {
  return page.evaluate(() => {
    const paths = document.querySelectorAll<SVGPathElement>(
      '[data-testid="histogram-plot"] g.trace.bars g.point path',
    );
    return Array.from(paths, (p) => p.getAttribute("d") ?? "").join("|");
  });
}

async function barCount(page: import("@playwright/test").Page): Promise<number> {
  return page.evaluate(
    () =>
      document.querySelectorAll(
        '[data-testid="histogram-plot"] g.trace.bars g.point',
      ).length,
  );
}

for (const { name, prefix } of BASES) {
  test.describe(`eda-histogram @ ${name}`, () => {
    test("loads defaults, renders bars, and both controls redraw the figure", async ({
      page,
    }) => {
      const requests: string[] = [];
      const failed: string[] = [];
      const sockets: string[] = [];
      page.on("request", (r) => requests.push(r.url()));
      page.on("requestfailed", (r) => failed.push(r.url()));
      page.on("websocket", (ws) => sockets.push(ws.url()));

      await page.goto(appUrl(prefix, QUERY));

      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const plot = page.locator('[data-testid="histogram-plot"]');
      await expect(plot.locator("svg.main-svg").first()).toBeVisible();

      // defaults come from configs/eda_histogram.json
      await expect(plot).toHaveAttribute("data-active-variable", "AGE_AT_SCAN");
      await expect(plot).toHaveAttribute("data-active-bins", "25");
      await expect(plot).toHaveAttribute("data-bar-count", "25");
      await expect(page.locator('[data-testid="histogram-bins-value"]')).toHaveText("25");
      await expect(page.locator('[data-testid="histogram-stats"]')).toContainText(
        "Available N: 1,114",
      );
      await expect(page.locator('[data-testid="histogram-stats"]')).toContainText(
        "Missing N: 0",
      );
      await expect(plot).toHaveAttribute("data-render-count", "1");

      // 1) changing the variable changes active-variable, N/missing and geometry
      const geomBefore = await barGeometry(page);
      await page.locator('[data-testid="histogram-variable"]').selectOption("VIQ");
      await expect(plot).toHaveAttribute("data-active-variable", "VIQ");
      await expect(plot).toHaveAttribute("data-render-count", "2");
      await expect(page.locator('[data-testid="histogram-stats"]')).toContainText(
        "Available N: 799",
      );
      await expect(page.locator('[data-testid="histogram-stats"]')).toContainText(
        "Missing N: 315",
      );
      await expect.poll(async () => (await barGeometry(page)) !== geomBefore).toBe(true);

      // 2) changing the bin count changes active-bins AND the number of bars
      await page.locator('[data-testid="histogram-bins"]').fill("50");
      await expect(plot).toHaveAttribute("data-active-bins", "50");
      await expect(plot).toHaveAttribute("data-bar-count", "50");
      await expect(page.locator('[data-testid="histogram-bins-value"]')).toHaveText("50");
      await expect.poll(async () => await barCount(page)).toBe(50);

      await page.locator('[data-testid="histogram-bins"]').fill("8");
      await expect(plot).toHaveAttribute("data-bar-count", "8");
      await expect.poll(async () => await barCount(page)).toBe(8);

      // 3) no CDN / kernel / off-origin / failed requests, no WebSocket
      const origin = new URL(page.url()).origin;
      const offOrigin = requests.filter(
        (u) => !u.startsWith(origin) && !u.startsWith("data:"),
      );
      expect(offOrigin, `off-origin: ${offOrigin.join(", ")}`).toEqual([]);
      const banned =
        /cdn\.plot\.ly|plotly-latest|jsdelivr|unpkg|cdnjs|googleapis|gstatic|\/api\/kernels|jupyter|pyodide|\/lite\/|voici/i;
      expect(requests.filter((u) => banned.test(u))).toEqual([]);
      expect(failed, `failed: ${failed.join(", ")}`).toEqual([]);
      expect(sockets).toEqual([]);
    });

    test("hover text exposes a bin range and count only (no participant detail)", async ({
      page,
    }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const template = await page.evaluate(() => {
        const gd = document.querySelector('[data-testid="histogram-plot"]') as unknown as {
          data?: Array<{ hovertemplate?: string }>;
        };
        return gd.data?.[0]?.hovertemplate ?? "";
      });
      expect(template).toContain("Bin %{customdata}");
      expect(template).toContain("Count %{y}");
      expect(template.toLowerCase()).not.toContain("sub_id");
    });

    test("refreshing the page restores the configured defaults", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await page.locator('[data-testid="histogram-variable"]').selectOption("ADI_R_SOCIAL_TOTAL_A");
      await page.locator('[data-testid="histogram-bins"]').fill("40");
      await expect(page.locator('[data-testid="histogram-plot"]')).toHaveAttribute(
        "data-active-bins",
        "40",
      );

      await page.reload();
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const plot = page.locator('[data-testid="histogram-plot"]');
      await expect(plot).toHaveAttribute("data-active-variable", "AGE_AT_SCAN");
      await expect(plot).toHaveAttribute("data-active-bins", "25");
      await expect(page.locator('[data-testid="histogram-bins-value"]')).toHaveText("25");
    });

    test("is usable at a narrow (mobile) viewport", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 720 });
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const plot = page.locator('[data-testid="histogram-plot"]');
      await expect(plot.locator("svg.main-svg").first()).toBeVisible();
      // control still reachable and functional
      await page.locator('[data-testid="histogram-variable"]').selectOption("FIQ");
      await expect(plot).toHaveAttribute("data-active-variable", "FIQ");
      const box = await plot.boundingBox();
      expect(box?.width ?? 0).toBeLessThanOrEqual(375);
    });
  });
}
