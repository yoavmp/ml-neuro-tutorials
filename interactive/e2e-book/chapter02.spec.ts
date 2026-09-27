import { expect, test } from "@playwright/test";

// WP41 replaced Exercise 2's canonical Jupyter Book page with a short
// transition page: the real lesson now runs as a JupyterLite notebook (see
// exercise-02-lite.spec.ts). This file only checks the transition page
// itself; it must not embed the old knn-explore iframe or any analysis code
// of its own (see tests/test_exercise_02_transition_page.py for the offline
// structural equivalent).
//
// WP41R: these checks used to use `a[href*="..."]` (substring-of-href)
// locators, which passed even though the site was broken -- the "Open
// Exercise 2" link's real href was `#../../lite/notebooks/index.html?...`
// (a same-page anchor; MyST/Sphinx had mis-resolved the Markdown link as an
// internal cross-reference, so clicking it did nothing), and the download
// "link" was not an <a> tag at all, just unlinked text; both still
// contained the target path as a substring, which `href*=` alone cannot
// tell apart from a real, working link. Assert the exact href and that a
// real click actually navigates instead.

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_02/exercise_02.html";
const LITE_HREF = "../../lite/notebooks/index.html?path=exercise_02.ipynb";
const DOWNLOAD_HREF = "../../lite/files/exercise_02_portable.ipynb";

test.describe("Chapter 2 built page — JupyterLite transition page", () => {
  test("has no embedded iframe and links to the JupyterLite notebook", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    await expect(page.locator("iframe")).toHaveCount(0);
    const liteLink = page.locator(`a[href="${LITE_HREF}"]`);
    await expect(liteLink).toHaveCount(1);
    await expect(liteLink).toHaveText("Open Exercise 2");
  });

  test("clicking Open Exercise 2 actually opens the JupyterLite notebook", async ({ page }) => {
    await page.goto(CHAPTER_URL);
    await page.click(`a[href="${LITE_HREF}"]`);
    await page.waitForURL(/lite\/notebooks\/index\.html\?path=exercise_02\.ipynb/, {
      timeout: 10_000,
    });
    expect(page.url()).toContain("lite/notebooks/index.html?path=exercise_02.ipynb");
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
    // WP41R: the generic per-page Colab button (book/_static/launch-buttons.js)
    // is deliberately not wired for this page -- its URL always points at the
    // public "main" branch on GitHub, which does not have this unpushed
    // migration, and the same URL shape breaks entirely once the repository
    // goes private. See launch-buttons.spec.ts for the other chapters, which
    // do keep this button.
    await page.goto(CHAPTER_URL);
    await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
    const bodyHtml = await page.locator(".bd-article").innerHTML();
    expect(bodyHtml).not.toContain("raw.githubusercontent.com");
    expect(bodyHtml).not.toContain("colab.research.google.com/github");
  });
});
