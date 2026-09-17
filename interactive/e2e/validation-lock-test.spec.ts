import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `validation-lock-test`
// activity (WP27, Exercise 4's "Choose k Before Revealing the Test Set").
// The built-Jupyter-Book check lives in ../e2e-book/chapter04.spec.ts and the
// dark-mode check in ../e2e-book/wp22-cross-chapter-dark-mode.spec.ts.
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/validation_lock_test.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

for (const { name, prefix } of BASES) {
  test.describe(`validation-lock-test @ ${name}`, () => {
    test("loads with the configured default k, test result hidden, and both MSE curves rendered", async ({
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

      await expect(page.locator("#app")).toHaveAttribute("data-chosen-k", "20");
      await expect(page.locator("#app")).toHaveAttribute("data-locked", "false");
      await expect(page.locator('[data-testid="validation-lock-test-k-20"]')).toHaveAttribute(
        "aria-selected",
        "true",
      );

      // the test result is not revealed before locking
      await expect(page.locator('[data-testid="validation-lock-test-reveal"]')).toBeHidden();
      await expect(page.locator('[data-testid="validation-lock-test-reset-button"]')).toBeHidden();
      await expect(page.locator('[data-testid="validation-lock-test-reset-note"]')).toBeHidden();

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

    test("locking reveals the test result once and disables further k changes", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await page.locator('[data-testid="validation-lock-test-k-8"]').click();

      await page.locator('[data-testid="validation-lock-test-lock-button"]').click();
      await expect(page.locator("#app")).toHaveAttribute("data-locked", "true");
      await expect(page.locator('[data-testid="validation-lock-test-reveal"]')).toBeVisible();

      const stats = await page.locator('[data-testid="validation-lock-test-reveal-stats"]').innerText();
      expect(stats).toMatch(/Test MSE for your chosen k = 8/);
      const compare = await page.locator('[data-testid="validation-lock-test-reveal-compare"]').innerText();
      expect(compare).toMatch(/training-selected k = \d+/);
      expect(compare).toMatch(/validation-selected k = \d+/);

      // choice is frozen: the k tabs and lock button are disabled
      await expect(page.locator('[data-testid="validation-lock-test-k-20"]')).toBeDisabled();
      await expect(page.locator('[data-testid="validation-lock-test-lock-button"]')).toBeDisabled();
      await expect(page.locator('[data-testid="validation-lock-test-reset-button"]')).toBeVisible();
      await expect(page.locator('[data-testid="validation-lock-test-reset-note"]')).toBeVisible();
      const note = await page.locator('[data-testid="validation-lock-test-reset-note"]').innerText();
      expect(note).toMatch(/not.*valid analysis/i);
    });

    test("reset returns to the unlocked default state, hiding the test result again", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await page.locator('[data-testid="validation-lock-test-k-8"]').click();
      await page.locator('[data-testid="validation-lock-test-lock-button"]').click();
      await expect(page.locator("#app")).toHaveAttribute("data-locked", "true");

      await page.locator('[data-testid="validation-lock-test-reset-button"]').click();
      await expect(page.locator("#app")).toHaveAttribute("data-locked", "false");
      await expect(page.locator("#app")).toHaveAttribute("data-chosen-k", "20"); // back to config default
      await expect(page.locator('[data-testid="validation-lock-test-reveal"]')).toBeHidden();
      await expect(page.locator('[data-testid="validation-lock-test-k-20"]')).toBeEnabled();
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
