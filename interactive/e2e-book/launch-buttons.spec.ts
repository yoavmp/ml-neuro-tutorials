import { expect, test } from "@playwright/test";

// WP12 §3: confirms the opening-admonition links AND the article-header Colab
// button, for BOTH chapters, point at that chapter's own portable notebook —
// never the canonical Jupyter Book source notebook, and never the other
// chapter's notebook (the previously observed "older notebook" regression).

const REPO = "yoavmp/ml-neuro-tutorials";
const CHAPTERS = [
  {
    name: "Chapter 1",
    url: "/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html",
    portable: "book/downloads/chapter_01/exercise_01_portable.ipynb",
  },
  {
    name: "Chapter 2",
    url: "/ml-neuro-tutorials/chapters/chapter_02/exercise_02.html",
    portable: "book/downloads/chapter_02/exercise_02_portable.ipynb",
  },
  {
    name: "Chapter 3",
    url: "/ml-neuro-tutorials/chapters/chapter_03/exercise_03.html",
    portable: "book/downloads/chapter_03/exercise_03_portable.ipynb",
  },
  {
    // WP28 §3: Exercise 4 is no longer a placeholder (WP27) -- it has its own
    // portable notebook and Colab button like chapters 1-3, so it belongs in
    // this loop rather than under the "placeholder gets no button" checks
    // below, where a stale assertion previously claimed the opposite.
    name: "Chapter 4",
    url: "/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html",
    portable: "book/downloads/chapter_04/exercise_04_portable.ipynb",
  },
];

for (const { name, url, portable } of CHAPTERS) {
  test.describe(`${name} — Colab / download destinations`, () => {
    test("opening admonition links to this chapter's own portable notebook (Colab + raw)", async ({
      page,
    }) => {
      await page.goto(url);
      const colabHref = `https://colab.research.google.com/github/${REPO}/blob/main/${portable}`;
      const rawHref = `https://raw.githubusercontent.com/${REPO}/main/${portable}`;

      // Scope to the opening admonition's own links: the article-header Colab
      // button (tested separately below) targets the same URL, so an
      // unscoped page-wide locator would double-count it.
      const admonition = page.locator(".bd-article .admonition.how-to-use");
      const colabLink = admonition.locator(`a[href="${colabHref}"]`);
      const rawLink = admonition.locator(`a[href="${rawHref}"]`);
      await expect(colabLink).toHaveCount(1);
      await expect(rawLink).toHaveCount(1);

      // never the OTHER chapter's, and never a canonical/source path
      for (const other of CHAPTERS) {
        if (other.portable === portable) continue;
        await expect(page.locator(`a[href*="${other.portable}"]`)).toHaveCount(0);
      }
    });

    test("article-header Colab button targets this chapter's portable notebook", async ({
      page,
    }) => {
      await page.goto(url);
      const button = page.locator('[data-testid="colab-launch-button"]');
      await expect(button).toBeVisible();
      await expect(button).toHaveAttribute(
        "href",
        `https://colab.research.google.com/github/${REPO}/blob/main/${portable}`,
      );
      await expect(button).toHaveAttribute("target", "_blank");
    });

    test("the theme's own download-.ipynb control is still present", async ({ page }) => {
      await page.goto(url);
      const download = page.locator(".dropdown-download-buttons");
      await expect(download).toHaveCount(1);
    });
  });
}

test("a page with no portable-notebook mapping (Introduction) gets no Colab button", async ({
  page,
}) => {
  await page.goto("/ml-neuro-tutorials/intro.html");
  await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
});

// WP28 §3: Exercises 5-12 are still placeholders at this point (before
// Exercise 5 is implemented later in WP28). This replaces the stale
// assertion that Exercise 4 (now implemented, see the CHAPTERS loop above)
// had no Colab button.
test("a placeholder exercise page (Exercise 5, before WP28 implementation) gets no Colab button", async ({
  page,
}) => {
  await page.goto("/ml-neuro-tutorials/chapters/chapter_05/exercise_05.html");
  await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
});
