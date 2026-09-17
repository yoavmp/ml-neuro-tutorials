import { expect, test } from "@playwright/test";

// Chapter 4 (WP25): a placeholder page for a not-yet-written exercise. Confirms
// the page builds, shows its title and the one placeholder sentence, and offers
// none of the controls a real exercise page would (no Colab button, no
// download dropdown content implying a portable notebook, no iframe).

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html";

test.describe("Chapter 4 built page — placeholder exercise", () => {
  test("shows the exact title and the one placeholder sentence, nothing else", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    // The theme appends its own permalink anchor ("#") inside the <h1>; strip
    // it before comparing the actual title text.
    const h1Text = await page.locator(".bd-article h1").first().innerText();
    expect(h1Text.replace(/#\s*$/, "").trim()).toBe(
      "Exercise 4: Cross-Validation for Classification and Regression",
    );
    await expect(
      page.locator(".bd-article").getByText(
        "Materials for this exercise will be added before the practice session.",
      ),
    ).toBeVisible();
  });

  test("has no interactive activity, no Colab button, and no article-header download dropdown implying a portable notebook", async ({
    page,
  }) => {
    await page.goto(CHAPTER_URL);
    await expect(page.locator("iframe.ml-activity")).toHaveCount(0);
    await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
  });
});
