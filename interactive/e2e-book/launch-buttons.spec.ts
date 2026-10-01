import { expect, test } from "@playwright/test";

// WP12 §3: confirms the opening-admonition links AND the article-header Colab
// button, for every chapter still using the OLD admonition-based opening,
// point at that chapter's own portable notebook — never the canonical
// Jupyter Book source notebook, and never another chapter's notebook (the
// previously observed "older notebook" regression).
//
// WP41R/WP44/WP45/WP46: Chapters 1-7 are deliberately NOT in this list any
// more. WP41/WP42/WP44/WP45/WP46 replaced their openings with a different
// page structure (see chapter01.spec.ts, chapter02.spec.ts,
// chapter03.spec.ts, chapter04.spec.ts, chapter05.spec.ts,
// chapter06.spec.ts, chapter07.spec.ts), and each one's top-bar Colab
// button is intentionally suppressed (see book/_static/launch-buttons.js
// and the "gets no top-bar Colab button" tests below) rather than pointed
// at a URL that would stop working once the repository goes private.

const REPO = "yoavmp/ml-neuro-tutorials";
const CHAPTERS = [
  {
    // WP33 §6: Exercise 8 is now a complete notebook, with its own portable
    // notebook and Colab button.
    name: "Chapter 8",
    url: "/ml-neuro-tutorials/chapters/chapter_08/exercise_08.html",
    portable: "book/downloads/chapter_08/exercise_08_portable.ipynb",
  },
  {
    // WP34 §6: Exercise 9 is now a complete notebook, with its own portable
    // notebook and Colab button.
    name: "Chapter 9",
    url: "/ml-neuro-tutorials/chapters/chapter_09/exercise_09.html",
    portable: "book/downloads/chapter_09/exercise_09_portable.ipynb",
  },
  {
    // WP38 §6: Exercise 10 is now a complete notebook, with its own portable
    // notebook and Colab button.
    name: "Chapter 10",
    url: "/ml-neuro-tutorials/chapters/chapter_10/exercise_10.html",
    portable: "book/downloads/chapter_10/exercise_10_portable.ipynb",
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

// WP38 §6: Exercises 11-12 remain placeholders after WP38 (Exercise 10 is now
// a complete notebook -- see the Chapter 10 case in CHAPTERS above). This
// replaces the earlier stale assertion (WP34 §6) that Exercise 10 had no
// Colab button.
test("a placeholder exercise page (Exercise 11) gets no Colab button", async ({ page }) => {
  await page.goto("/ml-neuro-tutorials/chapters/chapter_11/exercise_11.html");
  await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
});

// WP41R blocker 3: unlike the placeholder pages above (which never had a
// portable notebook), Chapter 2 DOES have one -- this button is suppressed
// deliberately, not by omission. See the file comment at the top and
// chapter02.spec.ts for the replacement, same-origin download link.
test("Chapter 2 (migrated to JupyterLite) gets no top-bar Colab button", async ({ page }) => {
  await page.goto("/ml-neuro-tutorials/chapters/chapter_02/exercise_02.html");
  await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
});

// WP42 Gate 2: same treatment as Chapter 2 above -- Chapter 1 also has a
// portable notebook (it is the migrated JupyterLite student notebook now),
// so this is a deliberate suppression, not an unmapped-page omission.
test("Chapter 1 (migrated to JupyterLite) gets no top-bar Colab button", async ({ page }) => {
  await page.goto("/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html");
  await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
});

// WP44 Gate B: same treatment as Chapters 1-2 above -- Chapter 3 also has a
// portable notebook (it is the migrated JupyterLite student notebook now),
// so this is a deliberate suppression, not an unmapped-page omission.
test("Chapter 3 (migrated to JupyterLite) gets no top-bar Colab button", async ({ page }) => {
  await page.goto("/ml-neuro-tutorials/chapters/chapter_03/exercise_03.html");
  await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
});

// WP45: same treatment as Chapters 1-3 above -- Chapter 4 also has a
// portable notebook (it is the migrated JupyterLite student notebook now),
// so this is a deliberate suppression, not an unmapped-page omission.
test("Chapter 4 (migrated to JupyterLite) gets no top-bar Colab button", async ({ page }) => {
  await page.goto("/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html");
  await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
});

// WP45: same treatment as Chapters 1-3 above -- Chapter 5 also has a
// portable notebook (it is the migrated JupyterLite student notebook now),
// so this is a deliberate suppression, not an unmapped-page omission.
test("Chapter 5 (migrated to JupyterLite) gets no top-bar Colab button", async ({ page }) => {
  await page.goto("/ml-neuro-tutorials/chapters/chapter_05/exercise_05.html");
  await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
});

// WP46: same treatment as Chapters 1-5 above -- Chapter 6 also has a
// portable notebook (it is the migrated JupyterLite student notebook now),
// so this is a deliberate suppression, not an unmapped-page omission.
test("Chapter 6 (migrated to JupyterLite) gets no top-bar Colab button", async ({ page }) => {
  await page.goto("/ml-neuro-tutorials/chapters/chapter_06/exercise_06.html");
  await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
});

// WP46: same treatment as Chapters 1-6 above -- Chapter 7 also has a
// portable notebook (it is the migrated JupyterLite student notebook now),
// so this is a deliberate suppression, not an unmapped-page omission.
test("Chapter 7 (migrated to JupyterLite) gets no top-bar Colab button", async ({ page }) => {
  await page.goto("/ml-neuro-tutorials/chapters/chapter_07/exercise_07.html");
  await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
});
