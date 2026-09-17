import { expect, test, type Frame } from "@playwright/test";

// Proof that all three embedded Exercise 4 activities (WP27: "Validation and
// Cross-Validation"; WP27R revised the candidate grids, the lock-test
// three-panel reveal, and the nested-CV diagram) work on the *final built*
// Exercise 4 HTML page -- not just the standalone widget page. Replaces the
// WP25-era placeholder check (Chapter 4 was a not-yet-written page then; WP27
// replaced the Markdown placeholder with a real notebook). The dark-mode
// check for these three activities lives in wp22-cross-chapter-dark-mode.spec.ts.

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html";
const STABILITY_IFRAME_SELECTOR = 'iframe[src*="config=../configs/validation_stability.json"]';
const LOCK_TEST_IFRAME_SELECTOR = 'iframe[src*="config=../configs/validation_lock_test.json"]';
const NESTED_CV_IFRAME_SELECTOR = 'iframe[src*="config=../configs/nested_cv_explorer.json"]';

async function frameFor(page: import("@playwright/test").Page, selector: string): Promise<Frame> {
  await page.locator(selector).scrollIntoViewIfNeeded();
  const handle = await page.locator(selector).elementHandle();
  expect(handle, "iframe element present").not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, "iframe content frame present").not.toBeNull();
  return frame!;
}

test.describe("Chapter 4 built page — title and structure", () => {
  test("shows the exact title and no stale placeholder text", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    const h1Text = await page.locator(".bd-article h1").first().innerText();
    expect(h1Text.replace(/#\s*$/, "").trim()).toBe("Exercise 4: Validation and Cross-Validation");

    const bodyText = await page.locator(".bd-article").innerText();
    expect(bodyText).not.toMatch(/Materials for this exercise will be added before the practice session\./);
    expect(bodyText).not.toMatch(/logistic regression/i);

    // exactly one embedded activity of each kind (combined activity not duplicated)
    await expect(page.locator(STABILITY_IFRAME_SELECTOR)).toHaveCount(1);
    await expect(page.locator(LOCK_TEST_IFRAME_SELECTOR)).toHaveCount(1);
    await expect(page.locator(NESTED_CV_IFRAME_SELECTOR)).toHaveCount(1);

    // a Colab launch button now exists (Exercise 4 is no longer a placeholder)
    await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(1);

    // WP27R: the old generic Mermaid flowchart is gone; the native
    // nested-cross-validation split diagram is present with its required
    // operation labels.
    expect(bodyText).not.toMatch(/flowchart TD/);
    await expect(page.locator(".ml-ncv-diagram")).toHaveCount(1);
    await expect(page.locator(".ml-ncv-diagram")).toContainText("Outer cross-validation");
    await expect(page.locator(".ml-ncv-diagram")).toContainText("Inner cross-validation");
    await expect(page.locator(".ml-ncv-diagram")).toContainText("Choose");
    await expect(page.locator(".ml-ncv-diagram")).toContainText("Refit the selected");
    await expect(page.locator(".ml-ncv-diagram")).toContainText("Evaluate the tuning procedure");

    // WP27R: the optional Python reproduction of Section 5 is collapsed by
    // default on the website (project's standard hide-cell toggle).
    await expect(page.locator(".bd-article h3", { hasText: "Optional: Reproduce the Tuning Activity in Python" })).toHaveCount(1);
    await expect(page.getByText("Show code cell content").first()).toBeVisible();
  });
});

test.describe("Chapter 4 built page — embedded validation-stability activity", () => {
  test("iframe loads, config+data are 200, both plots render at the configured defaults", async ({ page }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, STABILITY_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/validation_stability.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/wp27_validation_stability.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    await expect(frame.locator("#app")).toHaveAttribute("data-size-key", "100");
    await expect(frame.locator("#app")).toHaveAttribute("data-seed", "0");
    await expect(frame.locator("#app")).toHaveAttribute("data-folds", "5");

    await expect(frame.locator('[data-testid="validation-stability-single-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );
    await expect(frame.locator('[data-testid="validation-stability-cv-plot"]')).toHaveAttribute(
      "data-render-count",
      /[1-9]/,
    );

    // test results are visible immediately here (this activity has no lock/reveal gate)
    const summary = await frame.locator('[data-testid="validation-stability-summary"]').innerText();
    expect(summary).toMatch(/Sample size 100, seed 0/);
  });

  test("choosing a small sample size shows the small-N note and redraws both plots", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, STABILITY_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    await expect(frame.locator('[data-testid="validation-stability-small-n-note"]')).toBeHidden();

    await frame.locator('[data-testid="validation-stability-size-30"]').click();
    await expect(frame.locator("#app")).toHaveAttribute("data-size-key", "30");
    await expect(frame.locator('[data-testid="validation-stability-small-n-note"]')).toBeVisible();
    const summary = await frame.locator('[data-testid="validation-stability-summary"]').innerText();
    expect(summary).toMatch(/Sample size 30/);
  });
});

test.describe("Chapter 4 built page — embedded validation-lock-test activity", () => {
  test("iframe loads, config+data are 200, test result is hidden before locking", async ({ page }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, LOCK_TEST_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/validation_lock_test.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/wp27_validation_lock_test.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    await expect(frame.locator("#app")).toHaveAttribute("data-chosen-k", "25");
    await expect(frame.locator("#app")).toHaveAttribute("data-locked", "false");
    await expect(frame.locator('[data-testid="validation-lock-test-reveal"]')).toBeHidden();
    await expect(frame.locator('[data-testid="validation-lock-test-k-12"]')).toHaveCount(0);
    for (const k of [8, 10, 15, 20, 25, 30, 50]) {
      await expect(frame.locator(`[data-testid="validation-lock-test-k-${k}"]`)).toHaveCount(1);
    }

    const selection = await frame.locator('[data-testid="validation-lock-test-selection"]').innerText();
    expect(selection).toMatch(/Training-selected k = \d+/);
    expect(selection).toMatch(/Validation-selected k = \d+/);

    // no test trace exists in the plot before locking
    const traceCount = await frame.evaluate(() => {
      const el = document.querySelector('[data-testid="validation-lock-test-plot"]') as
        | (HTMLElement & { data?: unknown[] })
        | null;
      return el?.data?.length ?? -1;
    });
    expect(traceCount).toBe(2);
  });

  test("locking reveals the third test-MSE panel and the methodology warning, and disables further k changes", async ({
    page,
  }) => {
    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, LOCK_TEST_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    await frame.locator('[data-testid="validation-lock-test-lock-button"]').click();
    await expect(frame.locator("#app")).toHaveAttribute("data-locked", "true");
    await expect(frame.locator('[data-testid="validation-lock-test-reveal"]')).toBeVisible();
    await expect(frame.locator('[data-testid="validation-lock-test-lock-button"]')).toBeDisabled();
    await expect(frame.locator('[data-testid="validation-lock-test-reset-button"]')).toBeVisible();

    const traceCount = await frame.evaluate(() => {
      const el = document.querySelector('[data-testid="validation-lock-test-plot"]') as
        | (HTMLElement & { data?: unknown[] })
        | null;
      return el?.data?.length ?? -1;
    });
    expect(traceCount).toBe(3);

    const warning = await frame
      .locator('[data-testid="validation-lock-test-methodology-warning"]')
      .innerText();
    expect(warning).toMatch(/teaching demonstration/i);

    await expect(frame.locator('[data-testid="validation-lock-test-post-reveal-reflect"]')).toBeVisible();
  });
});

test.describe("Chapter 4 built page — embedded nested-cv-explorer activity", () => {
  test("iframe loads, config+data are 200, the default outer fold and summary table render", async ({ page }) => {
    const responses: { url: string; status: number }[] = [];
    page.on("response", (r) => responses.push({ url: r.url(), status: r.status() }));

    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, NESTED_CV_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const configResp = responses.find((r) => r.url.endsWith("/configs/nested_cv_explorer.json"));
    const dataResp = responses.find((r) => r.url.endsWith("/data/wp27_nested_cv_explorer.json"));
    expect(configResp?.status, "config HTTP status").toBe(200);
    expect(dataResp?.status, "data HTTP status").toBe(200);

    await expect(frame.locator("#app")).toHaveAttribute("data-outer-fold", "0");
    await expect(frame.locator('[data-testid="nested-cv-inner-plot"]')).toHaveAttribute("data-render-count", /[1-9]/);
    await expect(frame.locator('[data-testid="nested-cv-summary-table"]')).toBeVisible();
  });

  test("selecting a different outer fold updates the fold stats", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    const frame = await frameFor(page, NESTED_CV_IFRAME_SELECTOR);
    await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

    const before = await frame.locator('[data-testid="nested-cv-fold-stats"]').innerText();
    await frame.locator('[data-testid="nested-cv-fold-1"]').click();
    await expect(frame.locator("#app")).toHaveAttribute("data-outer-fold", "1");
    const after = await frame.locator('[data-testid="nested-cv-fold-stats"]').innerText();
    expect(after).not.toEqual(before);
  });
});

test.describe("Chapter 4 built page — narrow-viewport layout", () => {
  test("all three activities remain usable at 390px without horizontal document scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(CHAPTER_URL);

    for (const selector of [STABILITY_IFRAME_SELECTOR, LOCK_TEST_IFRAME_SELECTOR, NESTED_CV_IFRAME_SELECTOR]) {
      const frame = await frameFor(page, selector);
      await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");
    }

    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);

    // WP27R: the native nested-CV diagram scrolls horizontally within its
    // own box (like the project's wide dataframe tables) rather than
    // clipping labels or forcing the page itself to scroll.
    const diagram = page.locator(".ml-ncv-diagram");
    await diagram.scrollIntoViewIfNeeded();
    await expect(diagram).toBeVisible();
  });
});
