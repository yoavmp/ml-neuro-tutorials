import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `validation-lock-test`
// activity (WP27, Exercise 4's "Choose k Before Revealing the Test Set";
// WP27R revised the candidate grid and rebuilt the figure as an aligned
// three-panel train/validation/test plot). The built-Jupyter-Book check
// lives in ../e2e-book/chapter04.spec.ts and the dark-mode check in
// ../e2e-book/wp22-cross-chapter-dark-mode.spec.ts.
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/validation_lock_test.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

// WP27R densified grid must include these; a bare "12" from the old grid
// must not remain as a tab.
const REQUIRED_KS = [8, 10, 15, 20, 25, 30, 50];

async function plotTraceCount(page: import("@playwright/test").Page): Promise<number> {
  return page.evaluate(() => {
    const el = document.querySelector('[data-testid="validation-lock-test-plot"]') as
      | (HTMLElement & { data?: unknown[] })
      | null;
    return el?.data?.length ?? -1;
  });
}

for (const { name, prefix } of BASES) {
  test.describe(`validation-lock-test @ ${name}`, () => {
    test("loads with the configured default k=25, dense candidate grid, no stale 12 tab, test result hidden", async ({
      page,
    }) => {
      const consoleErrors: string[] = [];
      const sockets: string[] = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") consoleErrors.push(msg.text());
      });
      page.on("websocket", (ws) => sockets.push(ws.url()));

      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      await expect(page.locator("#app")).toHaveAttribute("data-chosen-k", "25");
      await expect(page.locator("#app")).toHaveAttribute("data-locked", "false");
      await expect(page.locator('[data-testid="validation-lock-test-k-25"]')).toHaveAttribute(
        "aria-selected",
        "true",
      );

      for (const k of REQUIRED_KS) {
        await expect(page.locator(`[data-testid="validation-lock-test-k-${k}"]`)).toHaveCount(1);
      }
      await expect(page.locator('[data-testid="validation-lock-test-k-12"]')).toHaveCount(0);

      // the test result is not revealed before locking
      await expect(page.locator('[data-testid="validation-lock-test-reveal"]')).toBeHidden();
      await expect(page.locator('[data-testid="validation-lock-test-reset-button"]')).toBeHidden();
      await expect(page.locator('[data-testid="validation-lock-test-reset-note"]')).toBeHidden();
      await expect(page.locator('[data-testid="validation-lock-test-methodology-warning"]')).toBeHidden();
      await expect(page.locator('[data-testid="validation-lock-test-post-reveal-reflect"]')).toBeHidden();

      // only training + validation traces exist before locking -- no test
      // panel trace, so no test value has been placed in the DOM at all.
      expect(await plotTraceCount(page)).toBe(2);

      const selection = await page.locator('[data-testid="validation-lock-test-selection"]').innerText();
      expect(selection).toMatch(/Training-selected k = \d+/);
      expect(selection).toMatch(/Validation-selected k = \d+/);

      await expect(page.locator('[data-testid="validation-lock-test-plot"]')).toHaveAttribute(
        "data-render-count",
        /[1-9]/,
      );

      expect(sockets).toEqual([]);
      expect(consoleErrors, consoleErrors.join("; ")).toEqual([]);
    });

    test("choosing a different k updates the chosen-k readout before locking", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      const before = await page.locator('[data-testid="validation-lock-test-chosen"]').innerText();
      await page.locator('[data-testid="validation-lock-test-k-8"]').click();
      await expect(page.locator("#app")).toHaveAttribute("data-chosen-k", "8");
      const after = await page.locator('[data-testid="validation-lock-test-chosen"]').innerText();
      expect(after).not.toEqual(before);
      expect(after).toMatch(/Chosen k = 8/);
    });

    test("locking reveals the third test-MSE panel, the methodology warning, and post-reveal questions, and disables further k changes", async ({
      page,
    }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await page.locator('[data-testid="validation-lock-test-k-8"]').click();

      await page.locator('[data-testid="validation-lock-test-lock-button"]').click();
      await expect(page.locator("#app")).toHaveAttribute("data-locked", "true");
      await expect(page.locator('[data-testid="validation-lock-test-reveal"]')).toBeVisible();

      // the third panel's trace now exists alongside the other two
      expect(await plotTraceCount(page)).toBe(3);

      const stats = await page.locator('[data-testid="validation-lock-test-reveal-stats"]').innerText();
      expect(stats).toMatch(/Test MSE for your chosen k = 8/);
      const compare = await page.locator('[data-testid="validation-lock-test-reveal-compare"]').innerText();
      expect(compare).toMatch(/training-selected k = \d+/);
      expect(compare).toMatch(/validation-selected k = \d+/);
      expect(compare).toMatch(/tracks the validation curve/);

      const warning = await page
        .locator('[data-testid="validation-lock-test-methodology-warning"]')
        .innerText();
      expect(warning).toMatch(/teaching demonstration/i);
      expect(warning).toMatch(/must not change now/i);

      await expect(page.locator('[data-testid="validation-lock-test-post-reveal-reflect"]')).toBeVisible();
      const postReveal = await page
        .locator('[data-testid="validation-lock-test-post-reveal-reflect"]')
        .innerText();
      expect(postReveal).toMatch(/resemble/i);

      // choice is frozen: the k tabs and lock button are disabled
      await expect(page.locator('[data-testid="validation-lock-test-k-25"]')).toBeDisabled();
      await expect(page.locator('[data-testid="validation-lock-test-lock-button"]')).toBeDisabled();
      await expect(page.locator('[data-testid="validation-lock-test-reset-button"]')).toBeVisible();
      await expect(page.locator('[data-testid="validation-lock-test-reset-note"]')).toBeVisible();
      const note = await page.locator('[data-testid="validation-lock-test-reset-note"]').innerText();
      expect(note).toMatch(/not.*valid analysis/i);
      expect(note).toMatch(/revealed test curve/i);
    });

    test("reset returns to the unlocked default state, hiding the test panel again", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await page.locator('[data-testid="validation-lock-test-k-8"]').click();
      await page.locator('[data-testid="validation-lock-test-lock-button"]').click();
      await expect(page.locator("#app")).toHaveAttribute("data-locked", "true");

      await page.locator('[data-testid="validation-lock-test-reset-button"]').click();
      await expect(page.locator("#app")).toHaveAttribute("data-locked", "false");
      await expect(page.locator("#app")).toHaveAttribute("data-chosen-k", "25"); // back to config default
      await expect(page.locator('[data-testid="validation-lock-test-reveal"]')).toBeHidden();
      await expect(page.locator('[data-testid="validation-lock-test-post-reveal-reflect"]')).toBeHidden();
      await expect(page.locator('[data-testid="validation-lock-test-k-25"]')).toBeEnabled();
      expect(await plotTraceCount(page)).toBe(2);
    });

    test("shows the error panel when pointed at a nonexistent config", async ({ page }) => {
      await page.goto(appUrl(prefix, "?config=../configs/validation_lock_test_missing.json"));
      await expect(page.locator('[data-testid="widget-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="widget-error-message"]')).toContainText("HTTP 404");
    });

    test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({
      page,
    }) => {
      await page.setViewportSize({ width: 390, height: 900 });
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="validation-lock-test-plot"]')).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);
    });
  });
}
