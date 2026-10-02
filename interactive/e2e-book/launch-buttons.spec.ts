import { expect, test } from "@playwright/test";

// WP12 §3: confirms the opening-admonition links AND the article-header Colab
// button, for every chapter still using the OLD admonition-based opening,
// point at that chapter's own portable notebook — never the canonical
// Jupyter Book source notebook, and never another chapter's notebook (the
// previously observed "older notebook" regression).
//
// WP41R/WP44/WP45/WP46/WP47: Chapters 1-8 are deliberately NOT in this list
// any more. WP41/WP42/WP44/WP45/WP46/WP47 replaced their openings with a
// different page structure (see chapter01.spec.ts, chapter02.spec.ts,
// chapter03.spec.ts, chapter04.spec.ts, chapter05.spec.ts,
// chapter06.spec.ts, chapter07.spec.ts, chapter08.spec.ts), and each one's
// top-bar Colab button is intentionally suppressed (see
// book/_static/launch-buttons.js and the "gets no top-bar Colab button"
// tests below) rather than pointed at a URL that would stop working once
// the repository goes private.
//
// WP49: the former Chapter 9/Chapter 10 admonition-link cases, and the
// Exercise 11 placeholder case, are removed here (not just skipped):
// Exercises 9-12 are intentionally excluded from book/_toc.yml for this
// release, so chapters/chapter_{09,10,11,12}/*.html no longer exist in the
// built book at all. Their source is untouched for a future redesign; see
// WPs/reports/WP49_REPORT.md.

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
