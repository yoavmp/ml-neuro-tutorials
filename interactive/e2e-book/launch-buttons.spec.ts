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
  {
    // WP28 §6: Exercise 5 is now a complete notebook, with its own portable
    // notebook and Colab button.
    name: "Chapter 5",
    url: "/ml-neuro-tutorials/chapters/chapter_05/exercise_05.html",
    portable: "book/downloads/chapter_05/exercise_05_portable.ipynb",
  },
  {
    // WP29 §6: Exercise 6 is now a complete notebook, with its own portable
    // notebook and Colab button.
    name: "Chapter 6",
    url: "/ml-neuro-tutorials/chapters/chapter_06/exercise_06.html",
    portable: "book/downloads/chapter_06/exercise_06_portable.ipynb",
  },
  {
    // WP32 §6: Exercise 7 is now a complete notebook, with its own portable
    // notebook and Colab button.
    name: "Chapter 7",
    url: "/ml-neuro-tutorials/chapters/chapter_07/exercise_07.html",
    portable: "book/downloads/chapter_07/exercise_07_portable.ipynb",
  },
  {
    // WP33 §6: Exercise 8 is now a complete notebook, with its own portable
    // notebook and Colab button.
    name: "Chapter 8",
    url: "/ml-neuro-tutorials/chapters/chapter_08/exercise_08.html",
    portable: "book/downloads/chapter_08/exercise_08_portable.ipynb",
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

// WP33 §6: Exercises 9-12 remain placeholders after WP33 (Exercise 8 is now
// a complete notebook -- see the Chapter 8 case in CHAPTERS above). This
// replaces the earlier stale assertion (WP32 §6) that Exercise 8 had no
// Colab button.
test("a placeholder exercise page (Exercise 9) gets no Colab button", async ({ page }) => {
  await page.goto("/ml-neuro-tutorials/chapters/chapter_09/exercise_09.html");
  await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
});
