import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `eda-retention` activity, served
// from book/_static/widgets/ at both the site root and the simulated GitHub
// Pages project subpath. The built-Jupyter-Book check lives in
// ../e2e-book/chapter01.spec.ts.
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/eda_retention.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

async function barGeometry(page: import("@playwright/test").Page): Promise<string> {
  return page.evaluate(() => {
    const paths = document.querySelectorAll<SVGPathElement>(
      '[data-testid="retention-plot"] g.trace.bars g.point path',
    );
    return Array.from(paths, (p) => p.getAttribute("d") ?? "").join("|");
  });
}

async function siteCustomdata(
  page: import("@playwright/test").Page,
): Promise<[number, number][]> {
  return page.evaluate(() => {
    const gd = document.querySelector('[data-testid="retention-plot"]') as unknown as {
      data?: Array<{ customdata?: [number, number][] }>;
    };
    return gd.data?.[0]?.customdata ?? [];
  });
}

for (const { name, prefix } of BASES) {
  test.describe(`eda-retention @ ${name}`, () => {
    test("defaults, exact overall retention, and checkbox-driven redraw", async ({
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

      const plot = page.locator('[data-testid="retention-plot"]');
      await expect(plot.locator("svg.main-svg").first()).toBeVisible();

      // default selection comes from configs/eda_retention.json
      for (const name of ["DX_GROUP", "AGE_AT_SCAN", "SEX", "FIQ"]) {
        await expect(page.locator(`[data-testid="retention-var-${name}"]`)).toBeChecked();
      }
      await expect(page.locator('[data-testid="retention-var-VIQ"]')).not.toBeChecked();
      await expect(plot).toHaveAttribute("data-selected-count", "4");

      // exact expected overall retention (independently cross-checked with pandas)
      await expect(plot).toHaveAttribute("data-total", "1114");
      await expect(plot).toHaveAttribute("data-retained-n", "1015");
      await expect(plot).toHaveAttribute("data-retained-pct", "91.11");
      await expect(plot).toHaveAttribute("data-site-count", "19");
      await expect(plot).toHaveAttribute("data-no-selection", "false");
      await expect(plot).toHaveAttribute("data-low-retention", "false");
      await expect(plot).toHaveAttribute("data-render-count", "1");
      await expect(page.locator('[data-testid="retention-stats"]')).toContainText(
        "Retained 1,015 of 1,114 participants (91.1%) · 99 excluded",
      );
      await expect(page.locator('[data-testid="retention-selected"]')).toContainText(
        "Selected variables (4): Diagnostic group, Age at scan, Sex, Full-scale IQ",
      );

      // site denominators / retained counts are carried on the trace for hover
      const cd = await siteCustomdata(page);
      expect(cd).toHaveLength(19);
      expect(cd.reduce((a, [, t]) => a + t, 0)).toBe(1114);
      expect(cd.reduce((a, [r]) => a + r, 0)).toBe(1015);

      // ticking another variable changes retained N and the actual bar geometry
      const geomBefore = await barGeometry(page);
      await page.locator('[data-testid="retention-var-SCQ_TOTAL"]').check();
      await expect(plot).toHaveAttribute("data-selected-count", "5");
      await expect(plot).toHaveAttribute("data-render-count", "2");
      await expect
        .poll(async () => Number(await plot.getAttribute("data-retained-n")))
        .toBeLessThan(1015);
      await expect.poll(async () => (await barGeometry(page)) !== geomBefore).toBe(true);

      // unticking it restores the default retention
      await page.locator('[data-testid="retention-var-SCQ_TOTAL"]').uncheck();
      await expect(plot).toHaveAttribute("data-retained-n", "1015");

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

    test("preset controls: suggested / select all / clear", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const plot = page.locator('[data-testid="retention-plot"]');

      // Select all -> low retention warning appears
      await page.locator('[data-testid="retention-select-all"]').click();
      await expect(plot).toHaveAttribute("data-selected-count", "13");
      await expect(plot).toHaveAttribute("data-low-retention", "true");
      await expect(page.locator('[data-testid="retention-warning"]')).toBeVisible();
      await expect(page.locator('[data-testid="retention-warning"]')).toContainText(
        "under 50%",
      );
      await expect
        .poll(async () => Number(await plot.getAttribute("data-retained-n")))
        .toBeLessThan(557);

      // Clear -> explicit "no completeness criterion" state, everyone retained
      await page.locator('[data-testid="retention-clear"]').click();
      await expect(plot).toHaveAttribute("data-selected-count", "0");
      await expect(plot).toHaveAttribute("data-no-selection", "true");
      await expect(plot).toHaveAttribute("data-retained-n", "1114");
      await expect(plot).toHaveAttribute("data-low-retention", "false");
      await expect(page.locator('[data-testid="retention-message"]')).toBeVisible();
      await expect(page.locator('[data-testid="retention-message"]')).toContainText(
        "no completeness criterion is currently applied",
      );
      await expect(page.locator('[data-testid="retention-warning"]')).toBeHidden();

      // Use suggested core set -> back to the four defaults and 1015 retained
      await page.locator('[data-testid="retention-suggested"]').click();
      await expect(plot).toHaveAttribute("data-selected-count", "4");
      await expect(plot).toHaveAttribute("data-retained-n", "1015");
      await expect(plot).toHaveAttribute("data-no-selection", "false");
      for (const name of ["DX_GROUP", "AGE_AT_SCAN", "SEX", "FIQ"]) {
        await expect(page.locator(`[data-testid="retention-var-${name}"]`)).toBeChecked();
      }
    });

    test("reloading the page restores the suggested core set", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const plot = page.locator('[data-testid="retention-plot"]');
      await page.locator('[data-testid="retention-var-ADOS_2_TOTAL"]').check();
      await page.locator('[data-testid="retention-var-DX_GROUP"]').uncheck();
      await expect(plot).not.toHaveAttribute("data-retained-n", "1015");

      await page.reload();
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(plot).toHaveAttribute("data-selected-count", "4");
      await expect(plot).toHaveAttribute("data-retained-n", "1015");
      await expect(page.locator('[data-testid="retention-var-ADOS_2_TOTAL"]')).not.toBeChecked();
    });

    test("hover template exposes aggregate site counts only", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const template = await page.evaluate(() => {
        const gd = document.querySelector('[data-testid="retention-plot"]') as unknown as {
          data?: Array<{ hovertemplate?: string }>;
        };
        return gd.data?.[0]?.hovertemplate ?? "";
      });
      expect(template).toContain("Retained %{customdata[0]} of %{customdata[1]}");
      expect(template.toLowerCase()).not.toContain("sub_id");
    });

    test("is usable and keyboard-operable at a narrow (mobile) viewport", async ({
      page,
    }) => {
      await page.setViewportSize({ width: 375, height: 720 });
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const plot = page.locator('[data-testid="retention-plot"]');
      await expect(plot.locator("svg.main-svg").first()).toBeVisible();

      // toggle a checkbox with the keyboard
      const viq = page.locator('[data-testid="retention-var-VIQ"]');
      await viq.focus();
      await page.keyboard.press("Space");
      await expect(viq).toBeChecked();
      await expect(plot).toHaveAttribute("data-selected-count", "5");

      const box = await plot.boundingBox();
      expect(box?.width ?? 999).toBeLessThanOrEqual(375);
    });
  });
}
