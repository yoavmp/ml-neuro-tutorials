import { expect, test } from "@playwright/test";

// WP41 replaced Exercise 2's canonical Jupyter Book page with a short
// transition page: the real lesson now runs as a JupyterLite notebook (see
// exercise-02-lite.spec.ts). This file only checks the transition page
// itself; it must not embed the old knn-explore iframe or any analysis code
// of its own (see tests/test_exercise_02_transition_page.py for the offline
// structural equivalent).

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_02/exercise_02.html";

test.describe("Chapter 2 built page — JupyterLite transition page", () => {
  test("has no embedded iframe and links to the JupyterLite notebook", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    await expect(page.locator("iframe")).toHaveCount(0);
    const liteLink = page.locator('a[href*="lite/notebooks/index.html?path=exercise_02.ipynb"]');
    await expect(liteLink).toHaveCount(1);
  });

  test("links to the downloadable portable notebook", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    const downloadLink = page.locator(
      'a[href*="downloads/chapter_02/exercise_02_portable.ipynb"]',
    );
    await expect(downloadLink.first()).toBeVisible();
  });
});
