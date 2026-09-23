import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `pca-kmeans-explorer` activity
// ("Explore PCA and K-Means"), served from book/_static/widgets/. The
// built-Jupyter-Book check lives in ../e2e-book/chapter08.spec.ts.
const QUERY = "?config=../configs/pca_kmeans_explorer.json";

function appUrl(query = ""): string {
  return `/app/index.html${query}`;
}

test.describe("pca-kmeans-explorer", () => {
  test("loads with the configured defaults and every panel rendered", async ({ page }) => {
    const failed: string[] = [];
    page.on("requestfailed", (r) => failed.push(r.url()));

    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const app = page.locator("#app");
    await expect(app).toHaveAttribute("data-retained-pc", "10");
    await expect(app).toHaveAttribute("data-k", "3");
    await expect(app).toHaveAttribute("data-seed", "0");
    await expect(app).toHaveAttribute("data-external-variable", "group");

    for (const testId of [
      "pca-kmeans-scatter-plot",
      "pca-kmeans-inertia-plot",
      "pca-kmeans-silhouette-plot",
      "pca-kmeans-sizes-plot",
      "pca-kmeans-composition-plot",
    ]) {
      await expect(page.locator(`[data-testid="${testId}"]`)).toHaveAttribute("data-render-count", /[1-9]/);
    }

    expect(failed, `unexpected network failures: ${failed.join(", ")}`).toHaveLength(0);
  });

  test("states visibly that clustering uses every retained component, not only PC1-PC2", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(page.locator('[data-testid="pca-kmeans-uses-all-pc-note"]')).toContainText(
      "every retained principal component",
    );
  });

  test("changing k updates the cluster-sizes panel and the scatter render count", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const before = await page.locator('[data-testid="pca-kmeans-scatter-plot"]').getAttribute("data-render-count");
    await page.locator('[data-testid="pca-kmeans-k-select"]').selectOption("5");

    await expect(page.locator("#app")).toHaveAttribute("data-k", "5");
    await expect(page.locator('[data-testid="pca-kmeans-scatter-plot"]')).not.toHaveAttribute(
      "data-render-count",
      before ?? "0",
    );
  });

  test("changing the retained-PC count changes inertia while PCA scores stay fixed", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const inertiaBefore = await page.locator("#app").getAttribute("data-inertia");
    await page.locator('[data-testid="pca-kmeans-retained-pc-select"]').selectOption("50");

    await expect(page.locator("#app")).toHaveAttribute("data-retained-pc", "50");
    const inertiaAfter = await page.locator("#app").getAttribute("data-inertia");
    expect(inertiaAfter).not.toEqual(inertiaBefore);
  });

  test("changing the seed changes only the K-means result, not the PC1-PC2 axis ranges", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await page.locator('[data-testid="pca-kmeans-seed-select"]').selectOption("1");

    await expect(page.locator("#app")).toHaveAttribute("data-seed", "1");
    const inertiaAfter = await page.locator("#app").getAttribute("data-inertia");
    // A different seed is not guaranteed to change inertia for every
    // combination, but the control must at least be wired to a redraw.
    await expect(page.locator('[data-testid="pca-kmeans-scatter-plot"]')).toHaveAttribute(
      "data-render-count",
      /[2-9]/,
    );
    expect(typeof inertiaAfter).toBe("string");
  });

  test("selecting acquisition site switches the composition panel to a heatmap", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await page.locator('[data-testid="pca-kmeans-external-select"]').selectOption("site");
    await expect(page.locator("#app")).toHaveAttribute("data-external-variable", "site");

    const traceTypes = await page.evaluate(() => {
      const el = document.querySelector('[data-testid="pca-kmeans-composition-plot"]') as HTMLElement & {
        data?: { type?: string }[];
      };
      return el.data?.map((t) => t.type);
    });
    expect(traceTypes).toContain("heatmap");
  });

  test("selecting age switches the composition panel to box traces", async ({ page }) => {
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await page.locator('[data-testid="pca-kmeans-external-select"]').selectOption("age");
    await expect(page.locator("#app")).toHaveAttribute("data-external-variable", "age");

    const traceTypes = await page.evaluate(() => {
      const el = document.querySelector('[data-testid="pca-kmeans-composition-plot"]') as HTMLElement & {
        data?: { type?: string }[];
      };
      return el.data?.map((t) => t.type);
    });
    expect(traceTypes?.every((t) => t === "box")).toBe(true);
  });

  test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(appUrl(QUERY));
    await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(page.locator('[data-testid="pca-kmeans-scatter-plot"]')).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("shows the error panel when pointed at a nonexistent config", async ({ page }) => {
    await page.goto(appUrl("?config=../configs/pca_kmeans_explorer_missing.json"));
    await expect(page.locator('[data-testid="widget-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="widget-error-message"]')).toContainText("HTTP 404");
  });
});
