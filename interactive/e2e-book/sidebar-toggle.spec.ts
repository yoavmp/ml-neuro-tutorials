import { expect, test } from "@playwright/test";

// WP07 regression tests for the article-header sidebar toggles on the built
// Chapter 1 page. Before WP07 the visible "Toggle primary sidebar" button in
// `.bd-header-article` had no handler at all (both theme scripts bind the
// hidden `#pst-header` copy) and clicking it did nothing at every viewport.
// `book/_static/sidebar-toggle-fix.js` forwards activation to the wired hidden
// button, so the theme's own behaviour runs: at >= 992 px it collapses/expands
// the persistent primary sidebar (`.pst-sidebar-hidden`); below 992 px it opens
// the sidebar `<dialog>` modal.
//
// Every assertion below checks an OBSERVABLE sidebar state change — never just
// "the click produced no error".

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html";
const PRIMARY_TOGGLE = ".bd-header-article .primary-toggle";
const PRIMARY_SIDEBAR = "#pst-primary-sidebar";
const PRIMARY_MODAL = "#pst-primary-sidebar-modal";

test.describe("Chapter 1 built page — primary sidebar toggle", () => {
  test("desktop: the toggle is visible and collapses / expands the sidebar", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(CHAPTER_URL);

    const toggle = page.locator(PRIMARY_TOGGLE);
    await expect(toggle).toBeVisible();

    const sidebar = page.locator(PRIMARY_SIDEBAR);
    await expect(sidebar).not.toHaveClass(/pst-sidebar-hidden/);
    await expect(sidebar).toBeVisible();

    // click -> collapsed (observable: class + it leaves the viewport)
    await toggle.click();
    await expect(sidebar).toHaveClass(/pst-sidebar-hidden/);
    await expect(sidebar).not.toBeInViewport();

    // click again -> expanded
    await toggle.click();
    await expect(sidebar).not.toHaveClass(/pst-sidebar-hidden/);
    await expect(sidebar).toBeVisible();
  });

  test("desktop: keyboard Enter and Space also toggle the sidebar", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(CHAPTER_URL);

    const sidebar = page.locator(PRIMARY_SIDEBAR);
    await page.locator(PRIMARY_TOGGLE).focus();

    await page.keyboard.press("Enter");
    await expect(sidebar).toHaveClass(/pst-sidebar-hidden/);

    await page.keyboard.press("Enter");
    await expect(sidebar).not.toHaveClass(/pst-sidebar-hidden/);

    await page.keyboard.press("Space");
    await expect(sidebar).toHaveClass(/pst-sidebar-hidden/);
  });

  test("narrow viewport: the toggle opens the navigation modal", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 800 });
    await page.goto(CHAPTER_URL);

    const toggle = page.locator(PRIMARY_TOGGLE);
    await expect(toggle).toBeVisible();

    const modal = page.locator(PRIMARY_MODAL);
    await expect(modal).not.toHaveJSProperty("open", true);

    await toggle.click();
    await expect(modal).toHaveJSProperty("open", true);

    // the primary navigation is actually reachable inside the modal
    const navLinks = modal.locator("nav.bd-links a, .bd-sidebar-primary a");
    expect(await navLinks.count()).toBeGreaterThan(0);
    await expect(
      modal.getByRole("link", { name: /Exploratory data analysis/i }).first(),
    ).toBeVisible();

    // Escape closes it again
    await page.keyboard.press("Escape");
    await expect(modal).not.toHaveJSProperty("open", true);
  });

  test("the toggle is never a no-op where it is shown", async ({ page }) => {
    for (const width of [1280, 1024, 768, 390]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(CHAPTER_URL);
      const toggle = page.locator(PRIMARY_TOGGLE);
      if (!(await toggle.isVisible())) continue;

      const state = () =>
        page.evaluate(
          ({ sel, modalSel }) => {
            const s = document.querySelector(sel);
            const m = document.querySelector(modalSel) as HTMLDialogElement | null;
            return JSON.stringify({
              hidden: s?.classList.contains("pst-sidebar-hidden") ?? null,
              modalOpen: m?.open ?? null,
            });
          },
          { sel: PRIMARY_SIDEBAR, modalSel: PRIMARY_MODAL },
        );

      const before = await state();
      await toggle.click();
      await expect
        .poll(async () => (await state()) !== before, {
          message: `primary toggle changed nothing at ${width}px`,
        })
        .toBe(true);
    }
  });
});
