import { expect, test, type Page } from "@playwright/test";

// WP49: replaced every fixed 140_000/150_000ms post-"Run All Cells" wait
// in this file with a poll on JupyterLab's own semantic kernel-status
// attribute (unknown -> busy -> idle, confirmed live by watching it
// transition across a real Run All Cells) -- environment-independent,
// unlike a fixed duration. Found live (exercise-04/06/07-lite.spec.ts):
// a fixed wait that is usually enough can still leave the kernel
// genuinely busy when a test interacts right after, which can trigger a
// JupyterLite app-level reload. See exercise-07-lite.spec.ts for the full
// writeup.
async function waitForKernelIdle(page: Page, timeoutMs = 600_000) {
  await page.waitForFunction(
    () => document.querySelector(".jp-Notebook-ExecutionIndicator")?.getAttribute("data-status") === "idle",
    undefined,
    { timeout: timeoutMs, polling: 1_000 },
  );
}

// WP22 addendum: `chapter01-dark-mode.spec.ts` covers Exercise 1 (histogram,
// correlation scatter) end to end, including the full light/dark/reload
// cycle. This spec originally extended coverage to one Plotly activity from
// every other exercise that had one, against the *built* Jupyter Book over
// real HTTP (OS/browser forced to light throughout, the book's iframe
// Plotly figures snapshotted via `_fullData`/`_fullLayout`). WP41/WP42/
// WP44/WP45/WP46 migrated every exercise this file covers (2-7) to
// JupyterLite-native notebooks, whose figures are Matplotlib PNGs inside a
// separate-origin JupyterLite app with its own theme setting, not Plotly
// iframes on the book page -- so the original snapshot/color-assertion
// helpers (`gotoDark`, `activityFrame`, `snapshotPlot`, `assertDarkFigure`,
// and their supporting dark-palette constants) have no surface left to
// check anywhere in this file and were removed (WP46; the same reasoning
// WP44/WP45 already applied exercise-by-exercise below). Every test in this
// file now instead switches the JupyterLite app's own theme to dark and
// confirms a rendered figure survives, exercise by exercise. WP25 moved the
// KNN exploration activity into Exercise 2 and moved classification into
// Exercise 3; the discarded knn-abc activity's dark-mode coverage (the
// original bug screenshot) lives only on
// archive/pre-syllabus-notebook-structure.

test.describe("Cross-chapter dark-mode Plotly verification (WP22 addendum)", () => {
  test.describe.configure({ timeout: 60_000 });

  // WP41 migrated Exercise 2 to a JupyterLite-native notebook: its built
  // page (chapters/chapter_02/exercise_02.html) is now a 2-cell transition
  // page with no embedded iframe or Plotly figure at all (confirmed:
  // chapter02.spec.ts asserts iframe count is 0 there), so the book's own
  // dark-mode toggle and this file's Plotly `_fullData`/`_fullLayout`
  // color-snapshot technique have no surface left to check on that page.
  // Exercise 2's own figures (matplotlib, not Plotly) live inside the
  // JupyterLite app instead, a separate origin/app with its OWN theme
  // setting unrelated to the book's theme-switch-button -- this replacement
  // test checks THAT surface: switching the notebook's own JupyterLab theme
  // to dark must not error, and Section 8's live figure (the one explicitly
  // required to "keep figures legible in light/dark modes") must still be
  // present and rendered. Matplotlib figures here are static, white-card
  // PNGs -- legible by construction regardless of the surrounding app
  // theme, unlike the dark-palette-remapped Plotly figures other exercises
  // still use, which is why this test's shape necessarily differs from the
  // others in this file rather than reusing snapshotPlot/assertDarkFigure.
  test("Exercise 2 — JupyterLite notebook: Section 8 figure survives switching to the app's own dark theme", async ({
    page,
  }) => {
    // Overrides this file's 60s describe-level timeout: a cold JupyterLite
    // start (Pyodide + the scientific stack) can take up to ~140s, the same
    // budget exercise-02-lite.spec.ts uses for this same notebook.
    test.setTimeout(300_000);
    await page.goto("/lite/notebooks/index.html?path=exercise_02.ipynb", { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await page.click("text=Run");
    await page.waitForTimeout(200);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Run All Cells" }).first().click();
    await waitForKernelIdle(page);

    await page.click("text=Settings");
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Theme" }).first().click();
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "JupyterLab Dark" }).first().click();
    await page.waitForTimeout(1000);

    expect(await page.locator(".jp-mod-error").count()).toBe(0);

    const el = await page.evaluate(() => {
      const panel = document.querySelector(".jp-WindowedPanel-outer");
      if (panel) panel.scrollTop = panel.scrollHeight * 0.78;
      return true;
    });
    expect(el).toBe(true);
    await page.waitForTimeout(600);
    const figureVisible = await page.locator(".jp-OutputArea-output img, .jp-OutputArea-output canvas").count();
    expect(figureVisible).toBeGreaterThan(0);
  });

  // WP45 migrated Exercise 5 to a JupyterLite-native notebook: its built
  // page (chapters/chapter_05/exercise_05.html) is now a 2-cell transition
  // page with no embedded iframe or Plotly figure at all (confirmed:
  // chapter05.spec.ts asserts iframe count is 0 there), so this file's
  // Plotly `_fullData`/`_fullLayout` color-snapshot technique has no
  // surface left to check on that page -- the same reasoning WP44 already
  // applied to Exercise 3 below. This replacement checks the JupyterLite
  // app's own theme instead: switching to dark must not error, and a
  // rendered Matplotlib figure (a static, white-card PNG, legible
  // regardless of surrounding app theme) must still be present.
  test("Exercise 5 — JupyterLite notebook: a rendered figure survives switching to the app's own dark theme", async ({
    page,
  }) => {
    test.setTimeout(300_000);
    await page.goto("/lite/notebooks/index.html?path=exercise_05.ipynb", { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await page.click("text=Run");
    await page.waitForTimeout(200);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Run All Cells" }).first().click();
    await waitForKernelIdle(page);

    await page.click("text=Settings");
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Theme" }).first().click();
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "JupyterLab Dark" }).first().click();
    await page.waitForTimeout(1000);

    // The untouched template's blank "YOUR CODE HERE" activities degrade to
    // their own "Not complete yet" print messages (no exception raised, by
    // design -- see exercise-05-lite.spec.ts), so no error cell is expected
    // here at all.
    expect(await page.locator(".jp-mod-error").count()).toBe(0);

    const el = await page.evaluate(() => {
      const panel = document.querySelector(".jp-WindowedPanel-outer");
      if (panel) panel.scrollTop = panel.scrollHeight * 0.1;
      return true;
    });
    expect(el).toBe(true);
    await page.waitForTimeout(600);
    const figureVisible = await page.locator(".jp-OutputArea-output img, .jp-OutputArea-output canvas").count();
    expect(figureVisible).toBeGreaterThan(0);
  });

  // WP46 migrated Exercise 6 to a JupyterLite-native notebook: its built
  // page (chapters/chapter_06/exercise_06.html) is now a 2-cell transition
  // page with no embedded iframe or Plotly figure at all (confirmed:
  // chapter06.spec.ts asserts iframe count is 0 there), so this file's
  // Plotly `_fullData`/`_fullLayout` color-snapshot technique has no
  // surface left to check on that page -- the same reasoning WP44/WP45
  // already applied to Exercises 3-5. This replacement checks the
  // JupyterLite app's own theme instead: switching to dark must not error,
  // and a rendered Matplotlib figure (a static, white-card PNG, legible
  // regardless of surrounding app theme) must still be present.
  test("Exercise 6 — JupyterLite notebook: a rendered figure survives switching to the app's own dark theme", async ({
    page,
  }) => {
    test.setTimeout(300_000);
    await page.goto("/lite/notebooks/index.html?path=exercise_06.ipynb", { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await page.click("text=Run");
    await page.waitForTimeout(200);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Run All Cells" }).first().click();
    await waitForKernelIdle(page);

    await page.click("text=Settings");
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Theme" }).first().click();
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "JupyterLab Dark" }).first().click();
    await page.waitForTimeout(1000);

    // The untouched template's blank "YOUR CODE HERE" activities degrade to
    // their own "Not complete yet" print messages (no exception raised, by
    // design -- see exercise-06-lite.spec.ts), so no error cell is expected
    // here at all.
    expect(await page.locator(".jp-mod-error").count()).toBe(0);

    const el = await page.evaluate(() => {
      const panel = document.querySelector(".jp-WindowedPanel-outer");
      if (panel) panel.scrollTop = panel.scrollHeight * 0.1;
      return true;
    });
    expect(el).toBe(true);
    await page.waitForTimeout(600);
    const figureVisible = await page.locator(".jp-OutputArea-output img, .jp-OutputArea-output canvas").count();
    expect(figureVisible).toBeGreaterThan(0);
  });

  // WP46 migrated Exercise 7 to a JupyterLite-native notebook: its built
  // page (chapters/chapter_07/exercise_07.html) is now a 2-cell transition
  // page with no embedded iframe or Plotly figure at all (confirmed:
  // chapter07.spec.ts asserts iframe count is 0 there); chapter07-dark-
  // mode.spec.ts (the old iframe-Plotly-color regression guard) is deleted
  // for the same reason. This replacement mirrors Exercise 6's above.
  test("Exercise 7 — JupyterLite notebook: a rendered figure survives switching to the app's own dark theme", async ({
    page,
  }) => {
    // WP49: this test's own internal wait below used to be a fixed
    // 180_000ms that exactly equalled its test.setTimeout, leaving zero
    // time for every step after it -- a guaranteed timeout on every run.
    // Replaced the fixed wait with a poll on JupyterLab's own semantic
    // kernel-status attribute (unknown -> busy -> idle, confirmed live by
    // watching it transition across a real Run All Cells), which is
    // environment-independent rather than a guessed duration -- see
    // exercise-07-lite.spec.ts's own `waitForKernelIdle` for the full
    // writeup. `test.setTimeout` widened accordingly.
    test.setTimeout(300_000);
    await page.goto("/lite/notebooks/index.html?path=exercise_07.ipynb", { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await page.click("text=Run");
    await page.waitForTimeout(200);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Run All Cells" }).first().click();
    await page.waitForFunction(
      () => document.querySelector(".jp-Notebook-ExecutionIndicator")?.getAttribute("data-status") === "idle",
      undefined,
      { timeout: 240_000, polling: 1_000 },
    );

    await page.click("text=Settings");
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Theme" }).first().click();
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "JupyterLab Dark" }).first().click();
    await page.waitForTimeout(1000);

    // The untouched template's blank "YOUR CODE HERE" activities degrade to
    // their own "Not complete yet" print messages (no exception raised, by
    // design -- see exercise-07-lite.spec.ts), so no error cell is expected
    // here at all.
    expect(await page.locator(".jp-mod-error").count()).toBe(0);

    const el = await page.evaluate(() => {
      const panel = document.querySelector(".jp-WindowedPanel-outer");
      if (panel) panel.scrollTop = panel.scrollHeight * 0.1;
      return true;
    });
    expect(el).toBe(true);
    await page.waitForTimeout(600);
    const figureVisible = await page.locator(".jp-OutputArea-output img, .jp-OutputArea-output canvas").count();
    expect(figureVisible).toBeGreaterThan(0);
  });

  // WP44 migrated Exercise 3 to a JupyterLite-native notebook: its built
  // page (chapters/chapter_03/exercise_03.html) is now a 2-cell transition
  // page with no embedded iframe or Plotly figure at all (confirmed:
  // chapter03.spec.ts asserts iframe count is 0 there), so this file's
  // Plotly `_fullData`/`_fullLayout` color-snapshot technique has no
  // surface left to check on that page -- the same reasoning already
  // applied to Exercise 2 above. This replacement checks the JupyterLite
  // app's own theme instead: switching to dark must not error, and a
  // rendered Matplotlib figure (a static, white-card PNG, legible
  // regardless of surrounding app theme, unlike the dark-palette-remapped
  // Plotly figures other exercises still use) must still be present.
  test("Exercise 3 — JupyterLite notebook: a rendered figure survives switching to the app's own dark theme", async ({
    page,
  }) => {
    test.setTimeout(300_000);
    await page.goto("/lite/notebooks/index.html?path=exercise_03.ipynb", { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await page.click("text=Run");
    await page.waitForTimeout(200);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Run All Cells" }).first().click();
    await waitForKernelIdle(page);

    await page.click("text=Settings");
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Theme" }).first().click();
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "JupyterLab Dark" }).first().click();
    await page.waitForTimeout(1000);

    // The untouched template's own guarded model-fit RuntimeError (Section
    // 3, by design -- see exercise-03-lite.spec.ts) is the one expected
    // error cell here; anything beyond that would be a real regression.
    expect(await page.locator(".jp-mod-error").count()).toBeLessThanOrEqual(1);

    const el = await page.evaluate(() => {
      const panel = document.querySelector(".jp-WindowedPanel-outer");
      if (panel) panel.scrollTop = panel.scrollHeight * 0.1;
      return true;
    });
    expect(el).toBe(true);
    await page.waitForTimeout(600);
    const figureVisible = await page.locator(".jp-OutputArea-output img, .jp-OutputArea-output canvas").count();
    expect(figureVisible).toBeGreaterThan(0);
  });

  // WP45 migrated Exercise 4 to a JupyterLite-native notebook: its built
  // page (chapters/chapter_04/exercise_04.html) is now a 2-cell transition
  // page with no embedded iframe or Plotly figure at all (confirmed:
  // chapter04.spec.ts asserts iframe count is 0 there), so this file's
  // Plotly `_fullData`/`_fullLayout` color-snapshot technique has no
  // surface left to check on that page -- the same reasoning WP44 already
  // applied to Exercise 3 below. This replacement checks the JupyterLite
  // app's own theme instead, and additionally confirms the nested-
  // cross-validation diagram still renders after switching themes. WP48
  // replaced the original raw-HTML diagram (whose `--ml-ncv-*` custom
  // properties this test used to check) with a rendered PNG embedded as a
  // notebook attachment (see scripts/render_exercise_04_nested_cv_diagram.py)
  // -- a plain raster image with its own opaque white background, legible
  // in both themes by construction, with nothing left to toggle.
  test("Exercise 4 — JupyterLite notebook: a rendered figure and the nested-CV diagram survive switching to the app's own dark theme", async ({
    page,
  }) => {
    test.setTimeout(300_000);
    await page.goto("/lite/notebooks/index.html?path=exercise_04.ipynb", { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await page.click("text=Run");
    await page.waitForTimeout(200);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Run All Cells" }).first().click();
    await waitForKernelIdle(page);

    await page.click("text=Settings");
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Theme" }).first().click();
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "JupyterLab Dark" }).first().click();
    await page.waitForTimeout(1000);

    // The untouched template's blank "YOUR CODE HERE" activities degrade to
    // their own "Not complete yet" print messages (no exception raised, by
    // design -- see exercise-04-lite.spec.ts), so no error cell is expected
    // here at all.
    expect(await page.locator(".jp-mod-error").count()).toBe(0);

    const el = await page.evaluate(() => {
      const panel = document.querySelector(".jp-WindowedPanel-outer");
      if (panel) panel.scrollTop = panel.scrollHeight * 0.4;
      return true;
    });
    expect(el).toBe(true);
    await page.waitForTimeout(600);

    // The diagram is a plain <img> (markdown attachment), not HTML/CSS that
    // could fail to adapt to JupyterLab's dark theme the way the old
    // version did -- what this test confirms is that the image still
    // renders, visibly, with no error, after switching themes.
    const diagram = page.locator('img[alt^="Nested cross-validation diagram"]');
    await expect(diagram).toBeVisible();
  });
});
