import { expect, test } from "@playwright/test";

// Standalone runtime check for the production `multi-select-quiz` activity
// (WP38, Exercise 10: "Which steps must not see the test participants?"),
// served from book/_static/widgets/ at both the site root and the simulated
// GitHub Pages project subpath. The built-Jupyter-Book check is added
// separately once the notebook exists (see e2e-book/).
const BASES = [
  { name: "site root", prefix: "" },
  { name: "project subpath", prefix: "/ml-neuro-tutorials" },
];

const QUERY = "?config=../configs/leakage_quiz.json";

function appUrl(prefix: string, query = ""): string {
  return `${prefix}/app/index.html${query}`;
}

// From book/_static/widgets/data/leakage_quiz.json: six correct options, one
// incorrect ("metric-choice").
const CORRECT_IDS = ["scaling", "feature-selection", "pca", "missing-fill", "param-choice", "final-model"];

for (const { name, prefix } of BASES) {
  test.describe(`multi-select-quiz @ ${name}`, () => {
    test("loads with every option unchecked and no marks or feedback visible", async ({ page }) => {
      const failed: string[] = [];
      const sockets: string[] = [];
      const consoleErrors: string[] = [];
      page.on("requestfailed", (r) => failed.push(r.url()));
      page.on("websocket", (ws) => sockets.push(ws.url()));
      page.on("console", (msg) => {
        if (msg.type() === "error") consoleErrors.push(msg.text());
      });

      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      for (const id of [...CORRECT_IDS, "metric-choice"]) {
        await expect(page.locator(`[data-testid="quiz-checkbox-${id}"]`)).not.toBeChecked();
        await expect(page.locator(`[data-testid="quiz-feedback-${id}"]`)).toBeHidden();
        await expect(page.locator(`[data-testid="quiz-mark-${id}"]`)).toBeHidden();
      }
      await expect(page.locator('[data-testid="quiz-reset-button"]')).toBeHidden();
      await expect(page.locator('[data-testid="quiz-success"]')).toBeHidden();

      expect(sockets).toEqual([]);
      expect(failed).toEqual([]);
      expect(consoleErrors, consoleErrors.join("; ")).toEqual([]);
    });

    test("selecting exactly the six correct options and checking shows success feedback", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      for (const id of CORRECT_IDS) {
        await page.locator(`[data-testid="quiz-checkbox-${id}"]`).check();
      }
      await page.locator('[data-testid="quiz-check-button"]').click();

      await expect(page.locator('[data-testid="quiz-success"]')).toBeVisible();
      const outcome = await page.locator('[data-testid="quiz-outcome"]').innerText();
      expect(outcome).toMatch(/fully correct/i);

      for (const id of CORRECT_IDS) {
        const mark = await page.locator(`[data-testid="quiz-mark-${id}"]`).innerText();
        expect(mark).toMatch(/correct/i);
      }
      // options are locked after checking, until "Try again" is pressed
      await expect(page.locator(`[data-testid="quiz-checkbox-${CORRECT_IDS[0]}"]`)).toBeDisabled();
    });

    test("a partial/incorrect selection is visibly distinguished from a full pass", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      await page.locator('[data-testid="quiz-checkbox-scaling"]').check();
      await page.locator('[data-testid="quiz-checkbox-metric-choice"]').check();
      await page.locator('[data-testid="quiz-check-button"]').click();

      await expect(page.locator('[data-testid="quiz-success"]')).toBeHidden();
      const outcome = await page.locator('[data-testid="quiz-outcome"]').innerText();
      expect(outcome).toMatch(/not fully correct/i);

      const scalingMark = await page.locator('[data-testid="quiz-mark-scaling"]').innerText();
      expect(scalingMark).toMatch(/correct/i);
      const metricMark = await page.locator('[data-testid="quiz-mark-metric-choice"]').innerText();
      expect(metricMark).toMatch(/not correct/i);
      const missedMark = await page.locator('[data-testid="quiz-mark-pca"]').innerText();
      expect(missedMark).toMatch(/missed/i);

      // every option's own feedback text is visible once checked
      await expect(page.locator('[data-testid="quiz-feedback-scaling"]')).toBeVisible();
      await expect(page.locator('[data-testid="quiz-feedback-metric-choice"]')).toBeVisible();
    });

    test('"Try again" resets every selection, mark, and feedback back to the initial state', async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      await page.locator('[data-testid="quiz-checkbox-scaling"]').check();
      await page.locator('[data-testid="quiz-check-button"]').click();
      await expect(page.locator('[data-testid="quiz-reset-button"]')).toBeVisible();

      await page.locator('[data-testid="quiz-reset-button"]').click();

      await expect(page.locator('[data-testid="quiz-checkbox-scaling"]')).not.toBeChecked();
      await expect(page.locator('[data-testid="quiz-checkbox-scaling"]')).toBeEnabled();
      await expect(page.locator('[data-testid="quiz-mark-scaling"]')).toBeHidden();
      await expect(page.locator('[data-testid="quiz-feedback-scaling"]')).toBeHidden();
      await expect(page.locator('[data-testid="quiz-reset-button"]')).toBeHidden();
      await expect(page.locator('[data-testid="quiz-success"]')).toBeHidden();
    });

    test("refreshing the page restores the untouched initial state (no persisted answer)", async ({ page }) => {
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");

      for (const id of CORRECT_IDS) {
        await page.locator(`[data-testid="quiz-checkbox-${id}"]`).check();
      }
      await page.locator('[data-testid="quiz-check-button"]').click();
      await expect(page.locator('[data-testid="quiz-success"]')).toBeVisible();

      await page.reload();
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      await expect(page.locator('[data-testid="quiz-checkbox-scaling"]')).not.toBeChecked();
      await expect(page.locator('[data-testid="quiz-success"]')).toBeHidden();
      await expect(page.locator('[data-testid="quiz-reset-button"]')).toBeHidden();
    });

    test("is usable at a narrow (390 px) viewport without horizontal document scroll", async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 900 });
      await page.goto(appUrl(prefix, QUERY));
      await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);
    });

    // WP38R sec 3/9.1: the wrapped question must stay visually separate from
    // the answer list at every width the question itself wraps differently
    // at -- a single line at very wide desktop widths, two or more lines at
    // an intermediate width, and the ~5-line wrap the real question text
    // reaches at 390px (see WP38R_REPORT.md sec 4 for the measurements this
    // pins down: no overlap reproduced, but this test keeps it that way).
    for (const { label, width, colorScheme } of [
      { label: "desktop", width: 1280, colorScheme: "light" as const },
      { label: "intermediate wrapping width", width: 700, colorScheme: "light" as const },
      { label: "390px", width: 390, colorScheme: "dark" as const },
    ]) {
      test(`question bounding box does not overlap the first option at ${label}`, async ({ page }) => {
        await page.setViewportSize({ width, height: 900 });
        await page.emulateMedia({ colorScheme });
        await page.goto(appUrl(prefix, QUERY));
        await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
        await page.waitForTimeout(200); // let web fonts / wrapped text settle

        const question = page.locator(".widget-quiz-question");
        const firstOption = page.locator('[data-testid^="quiz-option-"]').first();
        const questionBox = await question.boundingBox();
        const firstOptionBox = await firstOption.boundingBox();
        expect(questionBox).not.toBeNull();
        expect(firstOptionBox).not.toBeNull();

        // the question must have wrapped onto at least one line and remain
        // fully above the first option's own box, with a real (non-zero)
        // gap -- not merely "not negative".
        const gap = firstOptionBox!.y - (questionBox!.y + questionBox!.height);
        expect(gap).toBeGreaterThanOrEqual(4);

        // and reload once (simulating a hard refresh with dark mode already
        // active) to cover the "initial load and reload while dark" case.
        await page.reload();
        await expect(page.locator("#app")).toHaveAttribute("data-widget-ready", "true");
        await page.waitForTimeout(200);
        const questionBox2 = await question.boundingBox();
        const firstOptionBox2 = await firstOption.boundingBox();
        const gap2 = firstOptionBox2!.y - (questionBox2!.y + questionBox2!.height);
        expect(gap2).toBeGreaterThanOrEqual(4);
      });
    }
  });
}
