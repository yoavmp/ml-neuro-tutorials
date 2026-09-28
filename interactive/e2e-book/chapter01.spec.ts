import { expect, test } from "@playwright/test";

// WP42 Gate 2 replaced Exercise 1's canonical Jupyter Book page with a short
// transition page: the real lesson now runs as a JupyterLite notebook (see
// exercise-01-lite.spec.ts). This file only checks the transition page
// itself; it must not embed any of the old four iframes (head/tail/sample
// comparison, complete-case retention explorer, histogram, correlation
// explorer -- all four rebuilt notebook-native inside the JupyterLite
// notebook) or any analysis code of its own (see
// tests/test_exercise_01_transition_page.py for the offline structural
// equivalent). This file replaces the pre-WP42 version of itself, which
// covered those four iframes directly; see
// interactive/e2e-book/exercise-01-lite.spec.ts for their replacement
// coverage, and archive/pre-wp41-jupyterlite-course-platform for the retired
// iframe-based content.
//
// Mirrors chapter02.spec.ts exactly (see that file's own comment on why
// exact-href + real-click assertions matter here, not a substring locator).

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html";
const LITE_HREF = "../../lite/notebooks/index.html?path=exercise_01.ipynb";
const DOWNLOAD_HREF = "../../lite/files/exercise_01_portable.ipynb";

test.describe("Chapter 1 built page — JupyterLite transition page", () => {
  test("has no embedded iframe and links to the JupyterLite notebook", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    await expect(page.locator("iframe")).toHaveCount(0);
    const liteLink = page.locator(`a[href="${LITE_HREF}"]`);
    await expect(liteLink).toHaveCount(1);
    await expect(liteLink).toHaveText("Open Exercise 1");
  });

  test("clicking Open Exercise 1 actually opens the JupyterLite notebook", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    await page.click(`a[href="${LITE_HREF}"]`);
    await page.waitForURL(/lite\/notebooks\/index\.html\?path=exercise_01\.ipynb/, {
      timeout: 10_000,
    });
    expect(page.url()).toContain("lite/notebooks/index.html?path=exercise_01.ipynb");
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
