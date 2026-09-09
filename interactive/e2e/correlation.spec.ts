import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `eda-correlation` activity, served
// from book/_static/widgets/ at both the site root and the simulated GitHub
// Pages project subpath. The built-Jupyter-Book check lives in
// ../e2e-book/chapter01.spec.ts.
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/eda_correlation.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

type PlotSnapshot = {
  traceCount: number;
  names: string[];
  totalPoints: number;
  firstXY: string;
};

async function plotSnapshot(
  page: import("@playwright/test").Page,
): Promise<PlotSnapshot> {
  return page.evaluate(() => {
    const gd = document.querySelector('[data-testid="correlation-plot"]') as unknown as {
      data?: Array<{ name?: string; x?: number[]; y?: number[] }>;
    };
    const data = gd.data ?? [];
    let total = 0;
    for (const t of data) total += t.x?.length ?? 0;
    const first = data[0];
    return {
      traceCount: data.length,
      names: data.map((t) => t.name ?? ""),
      totalPoints: total,
      firstXY: JSON.stringify([first?.x?.slice(0, 5) ?? [], first?.y?.slice(0, 5) ?? []]),
    };
  });
}

for (const { name, prefix } of BASES) {
  test.describe(`eda-correlation @ ${name}`, () => {
    test("defaults, exact coefficient/N, and X/Y-driven redraw", async ({ page }) => {
      const requests: string[] = [];
      const failed: string[] = [];
      const sockets: string[] = [];
      page.on("request", (r) => requests.push(r.url()));
      page.on("requestfailed", (r) => failed.push(r.url()));
      page.on("websocket", (ws) => sockets.push(ws.url()));

      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const plot = page.locator('[data-testid="correlation-plot"]');
      await expect(plot.locator("svg.main-svg").first()).toBeVisible();

      // defaults from configs/eda_correlation.json
      await expect(page.locator('[data-testid="correlation-x"]')).toHaveValue("FIQ");
      await expect(page.locator('[data-testid="correlation-y"]')).toHaveValue("SRS_TOTAL_RAW");
      await expect(page.locator('[data-testid="correlation-method"]')).toHaveValue("pearson");
      await expect(page.locator('[data-testid="correlation-group"]')).toHaveValue("none");

      await expect(plot).toHaveAttribute("data-active-x", "FIQ");
      await expect(plot).toHaveAttribute("data-active-y", "SRS_TOTAL_RAW");
      await expect(plot).toHaveAttribute("data-active-method", "pearson");
      await expect(plot).toHaveAttribute("data-active-group", "none");
      await expect(plot).toHaveAttribute("data-n", "778");
      await expect(plot).toHaveAttribute("data-r", "-0.2404");
      await expect(plot).toHaveAttribute("data-excluded-n", "336");
      await expect(plot).toHaveAttribute("data-same-variable", "false");
      await expect(plot).toHaveAttribute("data-render-count", "1");
      await expect(page.locator('[data-testid="correlation-stats"]')).toContainText(
        "Pearson correlation r = -0.24",
      );
      await expect(page.locator('[data-testid="correlation-stats"]')).toContainText(
        "n = 778 pairwise-complete participants (of 1,114)",
      );
      await expect(page.locator('[data-testid="correlation-missing"]')).toContainText(
        "excluded because either is missing: 336 of 1,114",
      );
      await expect(page.locator('[data-testid="correlation-groups"]')).toBeHidden();

      const before = await plotSnapshot(page);
      expect(before.traceCount).toBe(1);
      expect(before.totalPoints).toBe(778);

      // change Y -> a part–whole composite pair with far more pairwise data
      await page.locator('[data-testid="correlation-y"]').selectOption("VIQ");
      await expect(plot).toHaveAttribute("data-active-y", "VIQ");
      await expect(plot).toHaveAttribute("data-render-count", "2");
      await expect(plot).toHaveAttribute("data-n", "796");
      await expect.poll(async () => Number(await plot.getAttribute("data-r"))).toBeGreaterThan(0.8);
      const afterY = await plotSnapshot(page);
      expect(afterY.totalPoints).toBe(796);
      expect(afterY.firstXY).not.toBe(before.firstXY);

      // change X -> a small selected subset (differing pairwise N teaching point)
      await page.locator('[data-testid="correlation-x"]').selectOption("ADOS_G_TOTAL");
      await page.locator('[data-testid="correlation-y"]').selectOption("ADOS_2_TOTAL");
      await expect(plot).toHaveAttribute("data-n", "81");
      await expect(page.locator('[data-testid="correlation-stats"]')).toContainText("n = 81");

      // no failed / off-origin / CDN / kernel request, no WebSocket
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

    test("Pearson <-> Spearman changes the displayed coefficient for a pair where they differ", async ({
      page,
    }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const plot = page.locator('[data-testid="correlation-plot"]');

      // AGE_AT_SCAN ~ ADOS_G_TOTAL: Pearson -0.229, Spearman -0.332 (age is right-skewed)
      await page.locator('[data-testid="correlation-x"]').selectOption("AGE_AT_SCAN");
      await page.locator('[data-testid="correlation-y"]').selectOption("ADOS_G_TOTAL");
      await expect(plot).toHaveAttribute("data-active-method", "pearson");
      await expect(plot).toHaveAttribute("data-r", "-0.2290");
      await expect(plot).toHaveAttribute("data-n", "347");

      await page.locator('[data-testid="correlation-method"]').selectOption("spearman");
      await expect(plot).toHaveAttribute("data-active-method", "spearman");
      await expect(plot).toHaveAttribute("data-r", "-0.3321");
      await expect(plot).toHaveAttribute("data-n", "347"); // same rows, different statistic
      await expect(page.locator('[data-testid="correlation-stats"]')).toContainText(
        "Spearman correlation r = -0.33",
      );
    });

    test("grouping by diagnosis splits the scatter into per-group traces with per-group stats", async ({
      page,
    }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const plot = page.locator('[data-testid="correlation-plot"]');

      const ungrouped = await plotSnapshot(page);
      expect(ungrouped.traceCount).toBe(1);

      await page.locator('[data-testid="correlation-group"]').selectOption("diagnosis");
      await expect(plot).toHaveAttribute("data-active-group", "diagnosis");
      await expect(plot).toHaveAttribute("data-group-count", "2");

      const grouped = await plotSnapshot(page);
      expect(grouped.traceCount).toBe(2);
      expect(grouped.names).toEqual(["Autism", "Control"]);
      // points are partitioned, not duplicated
      expect(grouped.totalPoints).toBe(778);

      const groups = page.locator('[data-testid="correlation-groups"]');
      await expect(groups).toBeVisible();
      await expect(groups).toContainText("Autism: r = -0.03 (n = 372)");
      await expect(groups).toContainText("Control: r = -0.06 (n = 406)");

      // sex grouping is also available and re-partitions
      await page.locator('[data-testid="correlation-group"]').selectOption("sex");
      await expect(plot).toHaveAttribute("data-active-group", "sex");
      const bySex = await plotSnapshot(page);
      expect(bySex.names).toEqual(["Male", "Female"]);
      expect(bySex.totalPoints).toBe(778);
    });

    test("selecting the same variable on both axes is handled, not crashed", async ({
      page,
    }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const plot = page.locator('[data-testid="correlation-plot"]');

      await page.locator('[data-testid="correlation-y"]').selectOption("FIQ");
      await expect(plot).toHaveAttribute("data-same-variable", "true");
      await expect(plot).toHaveAttribute("data-n", "0");
      await expect(plot).toHaveAttribute("data-r", "null");
      await expect(page.locator('[data-testid="correlation-same-var"]')).toBeVisible();

      // recovering by picking a different Y works
      await page.locator('[data-testid="correlation-y"]').selectOption("PIQ");
      await expect(plot).toHaveAttribute("data-same-variable", "false");
      await expect.poll(async () => Number(await plot.getAttribute("data-n"))).toBeGreaterThan(0);
    });

    test("reloading restores the configured defaults", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const plot = page.locator('[data-testid="correlation-plot"]');
      await page.locator('[data-testid="correlation-x"]').selectOption("PIQ");
      await page.locator('[data-testid="correlation-method"]').selectOption("spearman");
      await page.locator('[data-testid="correlation-group"]').selectOption("sex");
      await expect(plot).toHaveAttribute("data-active-x", "PIQ");

      await page.reload();
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(plot).toHaveAttribute("data-active-x", "FIQ");
      await expect(plot).toHaveAttribute("data-active-y", "SRS_TOTAL_RAW");
      await expect(plot).toHaveAttribute("data-active-method", "pearson");
      await expect(plot).toHaveAttribute("data-active-group", "none");
    });

    test("hover template exposes only the two plotted values, no identifiers", async ({
      page,
    }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const templates = await page.evaluate(() => {
        const gd = document.querySelector('[data-testid="correlation-plot"]') as unknown as {
          data?: Array<{ hovertemplate?: string; customdata?: unknown }>;
        };
        return (gd.data ?? []).map((t) => ({
          tmpl: t.hovertemplate ?? "",
          hasCustomData: t.customdata !== undefined,
        }));
      });
      for (const t of templates) {
        expect(t.tmpl.toLowerCase()).not.toContain("sub_id");
        expect(t.tmpl.toLowerCase()).not.toMatch(/\bid\b|subject|participant/);
        expect(t.hasCustomData).toBe(false);
      }
    });

    test("is usable and keyboard-operable at a narrow (mobile) viewport", async ({
      page,
    }) => {
      await page.setViewportSize({ width: 375, height: 720 });
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const plot = page.locator('[data-testid="correlation-plot"]');
      await expect(plot.locator("svg.main-svg").first()).toBeVisible();

      const methodSelect = page.locator('[data-testid="correlation-method"]');
      await methodSelect.focus();
      await methodSelect.selectOption("spearman");
      await expect(plot).toHaveAttribute("data-active-method", "spearman");

      const box = await plot.boundingBox();
      expect(box?.width ?? 999).toBeLessThanOrEqual(375);
    });
  });
}
