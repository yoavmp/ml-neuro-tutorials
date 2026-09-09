import { expect, test } from "@playwright/test";

// The static server exposes the same content at the site root and beneath a
// simulated GitHub Pages project subpath. Every runtime assertion runs against
// both so we know the relative `base: "./"` assets survive the subpath.
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const SMOKE_QUERY = "?config=../configs/runtime_smoke.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

async function barSignature(page: import("@playwright/test").Page): Promise<string> {
  // Concatenated geometry of every rendered bar path — changes iff the plotted
  // values change.
  return page.evaluate(() => {
    const paths = document.querySelectorAll<SVGPathElement>(
      ".widget-plot g.trace.bars g.point path, .widget-plot g.trace .point path",
    );
    return Array.from(paths, (p) => p.getAttribute("d") ?? "").join("|");
  });
}

for (const { name, prefix } of BASES) {
  test.describe(`runtime-smoke @ ${name}`, () => {
    test("loads, renders a Plotly graph, and the control redraws it", async ({ page }) => {
      const requests: string[] = [];
      const sockets: string[] = [];
      page.on("request", (r) => requests.push(r.url()));
      page.on("websocket", (ws) => sockets.push(ws.url()));

      await page.goto(appUrl(prefix, SMOKE_QUERY));

      // 1. page loads successfully
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-role="dev-smoke-marker"]')).toBeVisible();

      // 2. Plotly produced a graph
      const plot = page.locator('[data-testid="runtime-smoke-plot"]');
      await expect(plot.locator("svg.main-svg").first()).toBeVisible();
      await expect(plot).toHaveAttribute("data-render-count", "1");
      await expect(plot).toHaveAttribute("data-active-index", "0");

      const before = await barSignature(page);
      expect(before.length).toBeGreaterThan(0);

      // 3. the control changes BOTH the render marker and the real plot state
      await page.locator('[data-testid="series-select"]').selectOption("1");
      await expect(plot).toHaveAttribute("data-render-count", "2");
      await expect(plot).toHaveAttribute("data-active-index", "1");
      await expect
        .poll(async () => (await barSignature(page)) !== before)
        .toBe(true);

      // 5. every runtime request is same-origin; no CDN, kernel, or WebSocket
      const origin = new URL(page.url()).origin;
      const offOrigin = requests.filter((u) => !u.startsWith(origin) && !u.startsWith("data:"));
      expect(offOrigin, `off-origin requests: ${offOrigin.join(", ")}`).toEqual([]);

      const banned = /cdn\.plot\.ly|plotly-latest|jsdelivr|unpkg|cdnjs|googleapis|gstatic/i;
      expect(requests.filter((u) => banned.test(u))).toEqual([]);

      const kernelish = /\/api\/kernels|\/api\/sessions|jupyter|pyodide|\/lite\/|voici/i;
      expect(requests.filter((u) => kernelish.test(u))).toEqual([]);

      expect(sockets).toEqual([]);
    });

    test("shows the error panel for a cross-origin config URL", async ({ page }) => {
      await page.goto(
        appUrl(prefix, `?config=${encodeURIComponent("https://evil.example/c.json")}`),
      );
      const err = page.locator('[data-testid="widget-error"]');
      await expect(err).toBeVisible();
      await expect(page.locator('[data-testid="widget-error-message"]')).toContainText(
        "same-origin",
      );
      await expect(page.locator("#app")).not.toHaveAttribute("data-widget-ready", "true");
    });

    test("shows the error panel for a missing config param", async ({ page }) => {
      await page.goto(appUrl(prefix));
      await expect(page.locator('[data-testid="widget-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="widget-error-message"]')).toContainText(
        'Missing required "config"',
      );
    });

    test("shows the error panel for a malformed (unsupported-protocol) config URL", async ({
      page,
    }) => {
      await page.goto(
        appUrl(prefix, `?config=${encodeURIComponent("file:///etc/passwd")}`),
      );
      await expect(page.locator('[data-testid="widget-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="widget-error-message"]')).toContainText(
        "http or https",
      );
    });
  });
}
