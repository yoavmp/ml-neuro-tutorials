import { expect, test } from "@playwright/test";

// WP12 §3: confirms the opening-admonition links AND the article-header Colab
// button, for every chapter still using the OLD admonition-based opening,
// point at that chapter's own portable notebook — never the canonical
// Jupyter Book source notebook, and never another chapter's notebook (the
// previously observed "older notebook" regression).
//
// WP41R/WP44/WP45/WP46/WP47/WP52: Chapters 1-9 are deliberately NOT in this
// list any more. WP41/WP42/WP44/WP45/WP46/WP47/WP52 replaced their openings
// with a different page structure (see chapter01.spec.ts, chapter02.spec.ts,
// chapter03.spec.ts, chapter04.spec.ts, chapter05.spec.ts,
// chapter06.spec.ts, chapter07.spec.ts, chapter08.spec.ts,
// chapter09.spec.ts), and each one's top-bar Colab button is intentionally
// suppressed (see book/_static/launch-buttons.js and the "gets no top-bar
// Colab button" tests below) rather than pointed at a URL that would stop
// working once the repository goes private.
//
// WP49/WP52 excluded Exercises 10-12 from book/_toc.yml entirely, so the
// former Chapter 10 admonition-link case and the Exercise 11 placeholder
// case were removed here (not just skipped). This release
// (WPs/reports/WP57_RELEASE_REPORT.md) re-adds chapters/chapter_{10,11,12}
// to the built book -- chapter_10/placeholder.html and
// chapter_11/exercise_11.html as titled placeholder stubs with no
// portable notebook, chapter_12/exercise_12.html as a migrated exercise's
// transition page -- see the three tests at the end of this file.

test("a page with no portable-notebook mapping (Introduction) gets no Colab button", async ({
  page,
}) => {
  await page.goto("/ml-neuro-tutorials/intro.html");
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

// WP47: same treatment as Chapters 1-7 above -- Chapter 8 also has a
// portable notebook (it is the migrated JupyterLite student notebook now),
// so this is a deliberate suppression, not an unmapped-page omission.
test("Chapter 8 (migrated to JupyterLite) gets no top-bar Colab button", async ({ page }) => {
  await page.goto("/ml-neuro-tutorials/chapters/chapter_08/exercise_08.html");
  await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
});

// WP52: same treatment as Chapters 1-8 above -- Chapter 9 also has a
// portable notebook (it is the migrated JupyterLite student notebook now),
// so this is a deliberate suppression, not an unmapped-page omission.
test("Chapter 9 (migrated to JupyterLite) gets no top-bar Colab button", async ({ page }) => {
  await page.goto("/ml-neuro-tutorials/chapters/chapter_09/exercise_09.html");
  await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
});

// WP57 release: Chapter 12 also has a portable notebook (it is the
// migrated JupyterLite student notebook now), so this is a deliberate
// suppression, same treatment as Chapters 1-9 above.
test("Chapter 12 (migrated to JupyterLite) gets no top-bar Colab button", async ({ page }) => {
  await page.goto("/ml-neuro-tutorials/chapters/chapter_12/exercise_12.html");
  await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
});

// WP57 release: Exercise 11 is a titled placeholder stub with no portable
// notebook at all -- an unmapped-page omission, not a suppression, same
// as Introduction.
//
// WP59: Exercise 10's page at this same path is no longer that kind of
// stub -- it now links to a real, downloadable Colab/local-only notebook
// (see tests/test_book_structure.py and
// tests/test_exercise_10_deep_learning_notebook.py for its content) -- but
// it still gets no top-bar Colab button, because book/_static/
// launch-buttons.js's PAGE_TO_PORTABLE map deliberately omits chapter_10:
// the page's own body already carries an explicit download + Colab link,
// and this button's URL pattern would otherwise silently depend on the
// repository staying public (see that file's header comment).
test("Chapter 10 (Colab/local-only download page) gets no top-bar Colab button", async ({ page }) => {
  await page.goto("/ml-neuro-tutorials/chapters/chapter_10/placeholder.html");
  await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
});

test("Chapter 11 placeholder (titled 'coming later' stub) gets no Colab button", async ({ page }) => {
  await page.goto("/ml-neuro-tutorials/chapters/chapter_11/exercise_11.html");
  await expect(page.locator('[data-testid="colab-launch-button"]')).toHaveCount(0);
});
