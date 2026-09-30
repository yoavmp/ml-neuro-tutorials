import { expect, test } from "@playwright/test";

// WP45 replaced Exercise 4's canonical Jupyter Book page with a short
// transition page: the real lesson now runs as a JupyterLite notebook (see
// exercise-04-lite.spec.ts). This file only checks the transition page
// itself; it must not embed the old validation-stability/lock-test/
// nested-cv-explorer iframes or any analysis code of its own (see
// tests/test_exercise_04_transition_page.py for the offline structural
// equivalent). Modeled exactly on chapter03.spec.ts's own treatment of
// Exercise 3.

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html";
const LITE_HREF = "../../lite/notebooks/index.html?path=exercise_04.ipynb";
const DOWNLOAD_HREF = "../../lite/files/exercise_04_portable.ipynb";

test.describe("Chapter 4 built page — JupyterLite transition page", () => {
  test("has no embedded iframe and links to the JupyterLite notebook", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    await expect(page.locator("iframe")).toHaveCount(0);
    const liteLink = page.locator(`a[href="${LITE_HREF}"]`);
    await expect(liteLink).toHaveCount(1);
    await expect(liteLink).toHaveText("Open Exercise 4");
  });

  test("clicking Open Exercise 4 actually opens the JupyterLite notebook", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    await page.click(`a[href="${LITE_HREF}"]`);
    await page.waitForURL(/lite\/notebooks\/index\.html\?path=exercise_04\.ipynb/, {
      timeout: 10_000,
    });
    expect(page.url()).toContain("lite/notebooks/index.html?path=exercise_04.ipynb");
  });

  test("links to the downloadable portable notebook with a real, working href", async ({
    page,
  }) => {
    await page.goto(CHAPTER_URL);
    const downloadLink = page.locator(`a[href="${DOWNLOAD_HREF}"]`);
    await expect(downloadLink).toHaveCount(1);
    await expect(downloadLink).toBeVisible();

    const response = await page.request.get(
      new URL(DOWNLOAD_HREF, page.url()).toString(),
    );
    expect(response.status()).toBe(200);
  });

  test("has no top-bar Colab button and no raw-GitHub link", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
    const bodyHtml = await page.locator(".bd-article").innerHTML();
    expect(bodyHtml).not.toContain("raw.githubusercontent.com");
    expect(bodyHtml).not.toContain("colab.research.google.com/github");
  });
});
