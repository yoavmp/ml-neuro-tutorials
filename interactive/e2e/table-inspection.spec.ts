import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `table-inspection` activity, served
// from book/_static/widgets/ at both the site root and the simulated GitHub
// Pages project subpath. The built-Jupyter-Book check lives in
// ../e2e-book/chapter01.spec.ts.
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/table_inspection.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

async function bodyText(page: import("@playwright/test").Page, testid: string): Promise<string> {
  return page.locator(`[data-testid="${testid}"]`).innerText();
}

for (const { name, prefix } of BASES) {
  test.describe(`table-inspection @ ${name}`, () => {
    test("head/tail are deterministic pandas-equivalents; sample is a fixed seeded draw", async ({
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

      const table = page.locator('[data-testid="table-inspection-table"]');
      await expect(table).toBeVisible();

      // default view = head(8): the first eight rows, all from one site. The
      // summary counts missing cells over all 13 curated columns (24; the first
      // BNI rows have no VIQ / PIQ / ADI-R social) — independently cross-checked
      // against the committed artifact in the unit tests.
      await expect(table).toHaveAttribute("data-method", "head");
      await expect(table).toHaveAttribute("data-row-count", "8");
      await expect(table).toHaveAttribute("data-site-count", "1");
      await expect(table).toHaveAttribute("data-sites", "ABIDEII-BNI_1");
      await expect(table).toHaveAttribute("data-missing-cells", "24");
      await expect(table).toHaveAttribute("data-total-cells", "104"); // 8 rows * 13 cols
      await expect(table.locator("tbody tr")).toHaveCount(8);
      const summaryLoc = page.locator('[data-testid="table-inspection-summary"]');
      await expect(summaryLoc).toContainText(
        "head() shows 8 rows from 1 acquisition site; 24 of 104 cells are missing.",
      );
      // the site-name list is NOT spelled out in the evidence summary (WP10 §1);
      // only "head()"/"tail()"/"sample()" parentheses remain
      expect(await summaryLoc.innerText()).not.toContain("ABIDEII-");
      expect(await summaryLoc.innerText()).not.toMatch(/\([A-Z]/);

      // switch to tail(8): a different single site, and more missing cells
      await page.locator('[data-testid="table-inspection-method-tail"]').check();
      await expect(table).toHaveAttribute("data-method", "tail");
      await expect(table).toHaveAttribute("data-site-count", "1");
      await expect(table).toHaveAttribute("data-sites", "ABIDEII-USM_1");
      await expect(table).toHaveAttribute("data-missing-cells", "35");

      // switch to sample(8): the fixed seed spans eight sites with far fewer
      // missing cells than tail()
      await page.locator('[data-testid="table-inspection-method-sample"]').check();
      await expect(table).toHaveAttribute("data-method", "sample");
      await expect(table).toHaveAttribute("data-seed", "7");
      await expect(table).toHaveAttribute("data-site-count", "8");
      await expect(table).toHaveAttribute("data-missing-cells", "17");
      const sitesAtSeed7 = await table.getAttribute("data-sites");

      // Reshuffle -> new seed, a different deterministic draw
      await page.locator('[data-testid="table-inspection-reshuffle"]').click();
      await expect(table).toHaveAttribute("data-seed", "8");
      await expect
        .poll(async () => await table.getAttribute("data-sites"))
        .not.toBe(sitesAtSeed7);

      // reload restores the configured defaults
      await page.reload();
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(table).toHaveAttribute("data-method", "head");
      await expect(table).toHaveAttribute("data-seed", "7");

      // offline production audit: no off-origin / CDN / kernel request, no socket
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

    test("row-count control changes rows and the evidence summary", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const table = page.locator('[data-testid="table-inspection-table"]');

      await page.locator('[data-testid="table-inspection-rows"]').fill("15");
      await expect(page.locator('[data-testid="table-inspection-rows-value"]')).toHaveText("15");
      await expect(table).toHaveAttribute("data-row-count", "15");
      await expect(table.locator("tbody tr")).toHaveCount(15);
      await expect(table).toHaveAttribute("data-total-cells", "195"); // 15 rows * 13 cols

      await page.locator('[data-testid="table-inspection-rows"]').fill("5");
      await expect(table).toHaveAttribute("data-row-count", "5");
      await expect(table.locator("tbody tr")).toHaveCount(5);
    });

    test("missing cells are marked accessibly and are not called errors", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const table = page.locator('[data-testid="table-inspection-table"]');
      await page.locator('[data-testid="table-inspection-method-tail"]').check();
      await expect(table).toHaveAttribute("data-missing-cells", "35");
      const missing = table.locator("td.widget-cell-missing");
      expect(await missing.count()).toBe(35);
      await expect(missing.first()).toContainText("missing"); // visually-hidden label
      const summary = await bodyText(page, "table-inspection-summary");
      expect(summary.toLowerCase()).not.toContain("error");
    });

    test("method selector is keyboard operable", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const table = page.locator('[data-testid="table-inspection-table"]');

      await page.locator('[data-testid="table-inspection-method-head"]').focus();
      await page.keyboard.press("ArrowDown"); // radio group -> next option (tail)
      await expect(page.locator('[data-testid="table-inspection-method-tail"]')).toBeChecked();
      await expect(table).toHaveAttribute("data-method", "tail");
      await page.keyboard.press("ArrowDown"); // -> sample
      await expect(table).toHaveAttribute("data-method", "sample");
    });

    test("is usable at a narrow (390 px) viewport and the wide 13-column table scrolls within its box", async ({
      page,
    }) => {
      await page.setViewportSize({ width: 390, height: 720 });
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const table = page.locator('[data-testid="table-inspection-table"]');
      await expect(table).toBeVisible();
      // all 13 columns are rendered even at this width
      await expect(table.locator("thead th")).toHaveCount(13);
      await page.locator('[data-testid="table-inspection-method-sample"]').check();
      await expect(table).toHaveAttribute("data-method", "sample");

      // the page itself must not scroll horizontally; the wide table lives in an
      // overflow-x container
      const docWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      expect(docWidth).toBeLessThanOrEqual(390 + 1);
      const scrollBox = await page.locator(".widget-table-scroll").boundingBox();
      expect(scrollBox?.width ?? 999).toBeLessThanOrEqual(390);
    });
  });
}
